"""
Frozen snapshot export of bigquery-public-data.thelook_ecommerce (Project 01, Stage 3).

Exports faithful, unjoined extracts to data/raw/ as CSV, runs the reference
query (sql/06) at the same snapshot instant, and writes a manifest with
row counts, SHA-256 checksums and a pandas double-check of the reference KPIs.

Authentication uses Google Application Default Credentials
(`gcloud auth application-default login`). This script never reads, prints
or stores credentials. The billing project ID is passed with --project and
is not written to the manifest.

Usage:
    python scripts/export_snapshot.py --project <SANDBOX_PROJECT_ID> check
    python scripts/export_snapshot.py --project <SANDBOX_PROJECT_ID> schema
    python scripts/export_snapshot.py --project <SANDBOX_PROJECT_ID> test-time-travel
    python scripts/export_snapshot.py --project <SANDBOX_PROJECT_ID> measure
    python scripts/export_snapshot.py --project <SANDBOX_PROJECT_ID> export
    python scripts/export_snapshot.py verify --manifest data/raw/manifest_YYYY-MM-DD.json
"""

import argparse
import hashlib
import json
import platform
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = REPO_ROOT / "data" / "raw"
EXPORT_SQL = REPO_ROOT / "sql" / "05_snapshot_export.sql"
REFERENCE_SQL = REPO_ROOT / "sql" / "06_snapshot_reference.sql"

DATASET = "bigquery-public-data.thelook_ecommerce"
LOCATION = "US"
TABLES = ["order_items", "inventory_items", "products", "users"]
TIME_TRAVEL_CLAUSE = "FOR SYSTEM_TIME AS OF @snapshot_ts"
TOLERANCE = 0.01

# Exact CSV headers approved for Stage 3 (order matters).
APPROVED_COLUMNS = {
    "order_items": ["id", "order_id", "user_id", "product_id", "inventory_item_id", "status",
                    "created_at", "shipped_at", "delivered_at", "returned_at", "sale_price"],
    "inventory_items": ["id", "product_id", "cost"],
    "products": ["id", "category", "name", "brand", "retail_price", "department"],
    "users": ["id", "age", "gender", "country", "traffic_source", "created_at"],
}
# Text that would mean a null was written as a literal instead of an empty cell.
LITERAL_NULL_TOKENS = ["None", "NaT", "nan", "NaN", "<NA>", "NULL", "null"]


# -----------------------------------------------------------------------------
# BigQuery helpers
# -----------------------------------------------------------------------------

def get_client(project):
    from google.cloud import bigquery

    if not project:
        sys.exit("ERROR: --project <SANDBOX_PROJECT_ID> is required for this command.")
    return bigquery.Client(project=project, location=LOCATION)


def job_config(snapshot_ts=None, dry_run=False):
    from google.cloud import bigquery

    params = []
    if snapshot_ts is not None:
        params.append(bigquery.ScalarQueryParameter("snapshot_ts", "TIMESTAMP", snapshot_ts))
    return bigquery.QueryJobConfig(
        query_parameters=params, dry_run=dry_run, use_query_cache=False
    )


def run_query(client, sql, snapshot_ts=None):
    return client.query(sql, job_config=job_config(snapshot_ts)).to_dataframe(
        create_bqstorage_client=False
    )


def load_export_queries(time_travel):
    """Split sql/05 into one query per table, using '-- @export: <table>' markers."""
    text = EXPORT_SQL.read_text(encoding="utf-8")
    parts = re.split(r"^-- @export:\s*(\w+)\s*$", text, flags=re.MULTILINE)
    queries = {}
    for name, body in zip(parts[1::2], parts[2::2]):
        sql = body.strip().rstrip(";")
        queries[name] = sql if time_travel else sql.replace(TIME_TRAVEL_CLAUSE, "")
    missing = [t for t in TABLES if t not in queries]
    if missing:
        sys.exit(f"ERROR: sql/05 is missing export blocks for: {missing}")
    return queries


def load_reference_query(time_travel):
    sql = REFERENCE_SQL.read_text(encoding="utf-8").strip().rstrip(";")
    return sql if time_travel else sql.replace(TIME_TRAVEL_CLAUSE, "")


# -----------------------------------------------------------------------------
# Commands that query BigQuery
# -----------------------------------------------------------------------------

def cmd_check(client, _args):
    client.query("SELECT 1").result()
    print("[OBSERVED FACT] Authenticated query against BigQuery succeeded.")


def cmd_schema(client, _args):
    tables = ", ".join(f"'{t}'" for t in TABLES + ["orders"])
    sql = f"""
        SELECT table_name, ordinal_position, column_name, data_type, is_nullable
        FROM `{DATASET}.INFORMATION_SCHEMA.COLUMNS`
        WHERE table_name IN ({tables})
        ORDER BY table_name, ordinal_position
    """
    print(run_query(client, sql).to_string(index=False))


def test_time_travel(client):
    results = {}
    for table in TABLES:
        sql = (
            f"SELECT COUNT(*) AS n FROM `{DATASET}.{table}` "
            "FOR SYSTEM_TIME AS OF TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 MINUTE)"
        )
        try:
            n = int(run_query(client, sql)["n"].iloc[0])
            results[table] = {"ok": True, "rows": n}
        except Exception as exc:  # report the BigQuery error message, nothing else
            results[table] = {"ok": False, "error": str(exc).splitlines()[0][:300]}
    return results


def cmd_test_time_travel(client, _args):
    for table, res in test_time_travel(client).items():
        print(table, json.dumps(res))


def cmd_measure(client, _args):
    tables = ", ".join(f"'{t}'" for t in TABLES)
    sql = f"""
        SELECT table_id, row_count, size_bytes,
               ROUND(size_bytes / 1024 / 1024, 2) AS size_mb,
               FORMAT_TIMESTAMP('%Y-%m-%d %H:%M:%S', TIMESTAMP_MILLIS(last_modified_time)) AS last_modified_utc
        FROM `{DATASET}.__TABLES__`
        WHERE table_id IN ({tables})
        ORDER BY table_id
    """
    print("[OBSERVED FACT] BigQuery storage metadata:")
    print(run_query(client, sql).to_string(index=False))
    if not EXPORT_SQL.exists():
        print(f"\nDry-run skipped: {EXPORT_SQL.relative_to(REPO_ROOT)} does not exist yet.")
        return
    print("\n[OBSERVED FACT] Dry-run bytes processed per export query (no data read):")
    ts = datetime.now(timezone.utc).replace(microsecond=0) - timedelta(seconds=10)
    queries = dict(load_export_queries(time_travel=True), reference=load_reference_query(time_travel=True))
    for name, q in queries.items():
        job = client.query(q, job_config=job_config(ts, dry_run=True))
        print(f"  {name:16s} {job.total_bytes_processed / 1024 / 1024:10.2f} MB")


def cmd_export(client, args):
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    label = args.label or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    targets = [RAW_DIR / f"{t}_{label}.csv" for t in TABLES] + [RAW_DIR / f"manifest_{label}.json"]
    existing = [p.name for p in targets if p.exists()]
    if existing and not args.overwrite:
        sys.exit(f"ERROR: refusing to overwrite existing files {existing}. Use --overwrite explicitly.")

    tt = test_time_travel(client)
    time_travel = all(r["ok"] for r in tt.values())
    run_start = datetime.now(timezone.utc).replace(microsecond=0)
    # T is fixed a few seconds in the past so it is always a valid time-travel point.
    snapshot_ts = run_start - timedelta(seconds=10) if time_travel else None
    print(f"time_travel={time_travel}  T={snapshot_ts}  label={label}")

    files = {}
    for name, q in load_export_queries(time_travel).items():
        df = run_query(client, q, snapshot_ts)
        path = RAW_DIR / f"{name}_{label}.csv"
        df.to_csv(path, index=False, encoding="utf-8", lineterminator="\n")
        files[name] = {"file": path.name, "columns": list(df.columns)}
        print(f"  exported {name}: {len(df):,} rows")

    # Without time travel, @snapshot_ts only anchors future_complete_items to the run start.
    ref = run_query(client, load_reference_query(time_travel), snapshot_ts or run_start).iloc[0]
    run_end = datetime.now(timezone.utc).replace(microsecond=0)

    manifest = {
        "dataset": DATASET,
        "snapshot_label": label,
        "consistency_method": "time_travel" if time_travel else "single_run_no_time_travel",
        "snapshot_ts_utc": snapshot_ts.strftime("%Y-%m-%d %H:%M:%S") if snapshot_ts else None,
        "run_start_utc": run_start.strftime("%Y-%m-%d %H:%M:%S"),
        "run_end_utc": run_end.strftime("%Y-%m-%d %H:%M:%S"),
        "time_travel_test": tt,
        "files": files,
        "reference_query": {k: to_jsonable(v) for k, v in ref.items()},
        "environment": {
            "python": platform.python_version(),
            "pandas": pd.__version__,
            "google-cloud-bigquery": __import__("google.cloud.bigquery").cloud.bigquery.__version__,
        },
    }
    manifest_path = RAW_DIR / f"manifest_{label}.json"
    finish_manifest(manifest, manifest_path)


# -----------------------------------------------------------------------------
# Local verification (no BigQuery access needed)
# -----------------------------------------------------------------------------

def to_jsonable(v):
    if pd.isna(v):
        return None
    if hasattr(v, "item"):
        return v.item()
    return v


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def pandas_kpis(oi, ii, products, users, snapshot_date):
    """Re-implements the reference KPIs from the CSV files (sql/02 section 6 rules)."""
    m = oi.merge(ii[["id", "cost"]], left_on="inventory_item_id", right_on="id",
                 how="inner", suffixes=("", "_inv"))
    complete = m[m["status"] == "Complete"]
    revenue = complete["sale_price"].sum()
    cogs = complete["cost"].sum()
    delivered_day = pd.to_datetime(complete["delivered_at"]).dt.normalize()
    return {
        "rows_order_items": len(oi),
        "rows_inventory_items": len(ii),
        "rows_products": len(products),
        "rows_users": len(users),
        "complete_items": int(len(complete)),
        "future_complete_items": int((delivered_day > pd.Timestamp(snapshot_date)).sum()),
        "recognized_revenue": round(revenue, 2),
        "recognized_cogs": round(cogs, 2),
        "gross_profit": round((complete["sale_price"] - complete["cost"]).sum(), 2),
        "gross_margin_pct": round((revenue - cogs) / revenue * 100, 2) if revenue else None,
        "pending_order_value": round(m.loc[m["status"].isin(["Processing", "Shipped"]), "sale_price"].sum(), 2),
        "return_associated_value": round(m.loc[m["status"] == "Returned", "sale_price"].sum(), 2),
        "cancelled_value": round(m.loc[m["status"] == "Cancelled", "sale_price"].sum(), 2),
    }


def finish_manifest(manifest, manifest_path):
    """Adds sizes, checksums, integrity checks and the pandas double-check, then writes the manifest."""
    dfs = {}
    for name, info in manifest["files"].items():
        path = RAW_DIR / info["file"]
        # Only truly empty cells count as null (not words like "NA" that could be real values).
        dfs[name] = pd.read_csv(path, low_memory=False, keep_default_na=False, na_values=[""])
        info["rows"] = len(dfs[name])
        info["bytes"] = path.stat().st_size
        info["size_mb"] = round(path.stat().st_size / 1024 / 1024, 2)
        info["sha256"] = sha256(path)
        info["duplicate_ids"] = int(dfs[name]["id"].duplicated().sum())
        info["null_counts"] = {c: int(n) for c, n in dfs[name].isna().sum().items()}
        info["header_matches_approved"] = list(dfs[name].columns) == APPROVED_COLUMNS[name]
        # Re-read as raw text (no NA parsing) to catch nulls written as literal words.
        raw = pd.read_csv(path, dtype=str, keep_default_na=False)
        info["literal_null_tokens"] = {
            c: int(raw[c].isin(LITERAL_NULL_TOKENS).sum()) for c in raw.columns
            if raw[c].isin(LITERAL_NULL_TOKENS).any()
        }

    oi, ii, pr, us = (dfs[t] for t in TABLES)
    manifest["orphan_checks"] = {
        "order_items.product_id not in products.id": int((~oi["product_id"].isin(pr["id"])).sum()),
        "order_items.inventory_item_id not in inventory_items.id": int((~oi["inventory_item_id"].isin(ii["id"])).sum()),
        "order_items.user_id not in users.id": int((~oi["user_id"].isin(us["id"])).sum()),
        "inventory_items.product_id not in products.id": int((~ii["product_id"].isin(pr["id"])).sum())
            if "product_id" in ii.columns else "column not exported",
    }

    anchor = manifest["snapshot_ts_utc"] or manifest["run_start_utc"]
    snapshot_date = datetime.strptime(anchor, "%Y-%m-%d %H:%M:%S").date()
    local = pandas_kpis(oi, ii, pr, us, snapshot_date)
    ref = manifest["reference_query"]
    comparison = {}
    for k, v in local.items():
        r = ref.get(k)
        diff = None if r is None or v is None else round(abs(float(v) - float(r)), 6)
        comparison[k] = {"reference": r, "pandas": v, "abs_diff": diff,
                         "ok": diff is not None and diff <= TOLERANCE}
    manifest["pandas_double_check"] = {"tolerance": TOLERANCE, "all_ok": all(c["ok"] for c in comparison.values()),
                                       "metrics": comparison}

    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nManifest written: {manifest_path.relative_to(REPO_ROOT)}")
    print(json.dumps({k: manifest[k] for k in ("orphan_checks", "pandas_double_check")}, indent=2))


def cmd_verify(args):
    manifest_path = Path(args.manifest)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    finish_manifest(manifest, manifest_path)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--project", help="BigQuery Sandbox project ID used to run (and bill) the queries")
    p.add_argument("--label", help="Date label for file names (default: UTC date of the run)")
    p.add_argument("--manifest", help="Manifest path (verify only)")
    p.add_argument("--overwrite", action="store_true", help="Allow export to replace existing files in data/raw/")
    p.add_argument("command", choices=["check", "schema", "test-time-travel", "measure", "export", "verify"])
    args = p.parse_args()

    if args.command == "verify":
        return cmd_verify(args)
    client = get_client(args.project)
    {"check": cmd_check, "schema": cmd_schema, "test-time-travel": cmd_test_time_travel,
     "measure": cmd_measure, "export": cmd_export}[args.command](client, args)


if __name__ == "__main__":
    main()
