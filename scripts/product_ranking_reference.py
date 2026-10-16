"""
Independent reference for the Stage 4 product ranking (Project 01, Stage 4).

Ranks the products inside one category (default: Outerwear & Coats) from the
frozen snapshot CSVs in data/raw/, using the Stage 3 decision logic applied per
product: four criteria (gross profit, gross margin %, volume, return rate
inverted), min-max scores across the eligible products, three weighting
scenarios, average rank and rank variation. The output is used to validate the
Power BI ranking; it is not a source for the dashboard.

Read-only on the snapshot: it reads products, order_items and inventory_items
and writes two derived CSV files (no personal data):
    data/raw/product_ranking_reference_<snapshot>.csv
    data/raw/product_ranking_sensitivity_<snapshot>.csv

Usage:
    python scripts/product_ranking_reference.py
    python scripts/product_ranking_reference.py --min-items 3 --cutoff 2026-10-01
"""

import argparse
import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = REPO_ROOT / "data" / "raw"

DEFAULT_SNAPSHOT = "2026-10-07"
DEFAULT_CATEGORY = "Outerwear & Coats"
DEFAULT_CUTOFF = "2026-10-01"
DEFAULT_MIN_ITEMS = 3
SENSITIVITY_MINIMUMS = [2, 3, 4]
TOP_N = 5
TOLERANCE = 0.01

# Control values from the Stage 3 dashboard (validated against the snapshot).
# They only apply to the default snapshot, category and cutoff.
EXPECTED_ITEMS = 2159
EXPECTED_GROSS_PROFIT = 174730.35
EXPECTED_PRODUCTS_WITH_SALES = 1111
EXPECTED_ELIGIBLE_AT_MIN3 = 273

FINAL_STATUSES = ["Complete", "Returned", "Cancelled"]

# Weights in the order gross profit / gross margin / volume / return rate.
SCENARIOS = {
    "balanced": (25, 25, 25, 25),
    "profitability": (30, 30, 20, 20),
    "growth_risk": (20, 30, 20, 30),
}

# Scores are rounded before ranking so floating-point noise cannot break a tie.
SCORE_RANK_DECIMALS = 9


# -----------------------------------------------------------------------------
# Loading
# -----------------------------------------------------------------------------

def load_snapshot(raw_dir, snapshot):
    products = pd.read_csv(raw_dir / f"products_{snapshot}.csv",
                           usecols=["id", "category", "name", "brand"])
    order_items = pd.read_csv(raw_dir / f"order_items_{snapshot}.csv",
                              usecols=["id", "product_id", "inventory_item_id", "status",
                                       "created_at", "delivered_at", "sale_price"],
                              parse_dates=["created_at", "delivered_at"])
    inventory = pd.read_csv(raw_dir / f"inventory_items_{snapshot}.csv",
                            usecols=["id", "cost"])
    return products, order_items, inventory


# -----------------------------------------------------------------------------
# Per-product metrics
# -----------------------------------------------------------------------------

def financial_metrics(order_items, inventory, product_ids, cutoff):
    """Closed Months cohort: Complete and delivered before the cutoff."""
    fin = order_items[(order_items["status"] == "Complete")
                      & (order_items["delivered_at"] < cutoff)
                      & (order_items["product_id"].isin(product_ids))]
    fin = fin.merge(inventory.rename(columns={"id": "inventory_item_id"}),
                    on="inventory_item_id", how="left")
    if fin["cost"].isna().any():
        sys.exit("ERROR: some order items have no matching inventory_items.cost.")
    metrics = fin.groupby("product_id").agg(items=("id", "size"),
                                            revenue=("sale_price", "sum"),
                                            cogs=("cost", "sum"))
    metrics["gross_profit"] = metrics["revenue"] - metrics["cogs"]
    metrics["gross_margin_pct"] = 100 * metrics["gross_profit"] / metrics["revenue"]
    return metrics


def operational_metrics(order_items, product_ids, cutoff):
    """Operational cohort: created before the cutoff with a final status."""
    ops = order_items[(order_items["created_at"] < cutoff)
                      & (order_items["status"].isin(FINAL_STATUSES))
                      & (order_items["product_id"].isin(product_ids))]
    counts = ops.pivot_table(index="product_id", columns="status", values="id",
                             aggfunc="size", fill_value=0)
    counts = counts.reindex(columns=FINAL_STATUSES, fill_value=0)
    result = pd.DataFrame(index=counts.index)
    result["ops_base"] = counts["Complete"] + counts["Returned"]
    result["return_rate_pct"] = 100 * counts["Returned"] / result["ops_base"]
    return result


# -----------------------------------------------------------------------------
# Scoring and ranking
# -----------------------------------------------------------------------------

def minmax_score(values, invert=False, label=""):
    lo, hi = values.min(), values.max()
    if hi == lo:
        print(f"WARNING: max equals min for {label}; its score is 0 for every product.")
        return pd.Series(0.0, index=values.index)
    scaled = (values - lo) / (hi - lo)
    return 100 * ((1 - scaled) if invert else scaled)


def ordinal_rank(df, sort_cols, ascending):
    """1..n with no repeated ranks; ties broken by higher gross profit, then lower id."""
    ordered = df.sort_values(sort_cols + ["gross_profit", "product_id"],
                             ascending=ascending + [False, True])
    return pd.Series(range(1, len(ordered) + 1), index=ordered.index)


def rank_products(metrics, min_items):
    eligible = metrics[metrics["items"] >= min_items].copy()
    if eligible.empty:
        sys.exit(f"ERROR: no products with at least {min_items} items.")
    if eligible["return_rate_pct"].isna().any():
        sys.exit("ERROR: an eligible product has no operational-cohort base.")

    criteria = pd.DataFrame({
        "gp": minmax_score(eligible["gross_profit"], label="gross profit"),
        "gm": minmax_score(eligible["gross_margin_pct"], label="gross margin %"),
        "vol": minmax_score(eligible["items"], label="volume"),
        "rr": minmax_score(eligible["return_rate_pct"], invert=True, label="return rate"),
    })
    for name, weights in SCENARIOS.items():
        score = (criteria[["gp", "gm", "vol", "rr"]] * weights).sum(axis=1) / 100
        eligible[f"score_{name}"] = score
        eligible[f"_rank_key_{name}"] = score.round(SCORE_RANK_DECIMALS)
        eligible[f"rank_{name}"] = ordinal_rank(eligible, [f"_rank_key_{name}"], [False])

    rank_cols = [f"rank_{name}" for name in SCENARIOS]
    eligible["avg_rank"] = eligible[rank_cols].mean(axis=1)
    eligible["rank_variation"] = eligible[rank_cols].max(axis=1) - eligible[rank_cols].min(axis=1)
    eligible["_avg_key"] = eligible["avg_rank"].round(SCORE_RANK_DECIMALS)
    eligible["final_rank"] = ordinal_rank(eligible, ["_avg_key"], [True])
    eligible = eligible.drop(columns=[c for c in eligible.columns if c.startswith("_")])
    return eligible.sort_values("final_rank")


# -----------------------------------------------------------------------------
# Controls
# -----------------------------------------------------------------------------

def run_controls(metrics, eligible_counts, apply_expected):
    total_items = int(metrics["items"].sum())
    total_gp = float(metrics["gross_profit"].sum())
    print("Control checks")
    print(f"  closed-month items        : {total_items:,}")
    print(f"  closed-month gross profit : {total_gp:,.2f}")
    print(f"  products with sales       : {len(metrics):,}")
    for m, n in eligible_counts.items():
        print(f"  eligible at minimum {m}    : {n:,}")

    if not apply_expected:
        print("  (non-default parameters: expected values not applied)")
        return
    failures = []
    if total_items != EXPECTED_ITEMS:
        failures.append(f"items {total_items:,} != {EXPECTED_ITEMS:,}")
    if abs(total_gp - EXPECTED_GROSS_PROFIT) > TOLERANCE:
        failures.append(f"gross profit {total_gp:,.2f} != {EXPECTED_GROSS_PROFIT:,.2f}")
    if failures:
        sys.exit("ERROR: control check failed: " + "; ".join(failures))
    print(f"  items and gross profit match the Stage 3 dashboard "
          f"({EXPECTED_ITEMS:,} / {EXPECTED_GROSS_PROFIT:,.2f}): PASS")
    print(f"  products with sales expected {EXPECTED_PRODUCTS_WITH_SALES:,}: "
          f"{'PASS' if len(metrics) == EXPECTED_PRODUCTS_WITH_SALES else 'DIFFERENT'}")
    if 3 in eligible_counts:
        print(f"  eligible at minimum 3 expected {EXPECTED_ELIGIBLE_AT_MIN3:,}: "
              f"{'PASS' if eligible_counts[3] == EXPECTED_ELIGIBLE_AT_MIN3 else 'DIFFERENT'}")


# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--snapshot", default=DEFAULT_SNAPSHOT, help="snapshot date in file names")
    parser.add_argument("--category", default=DEFAULT_CATEGORY)
    parser.add_argument("--cutoff", default=DEFAULT_CUTOFF, help="Closed Months cut-off (exclusive)")
    parser.add_argument("--min-items", type=int, default=DEFAULT_MIN_ITEMS)
    parser.add_argument("--raw-dir", type=Path, default=RAW_DIR)
    args = parser.parse_args()

    cutoff = pd.Timestamp(args.cutoff)
    products, order_items, inventory = load_snapshot(args.raw_dir, args.snapshot)

    cat = products[products["category"] == args.category].copy()
    if cat.empty:
        sys.exit(f"ERROR: no products in category {args.category!r}.")
    cat["product_name"] = cat["name"].where(
        cat["name"].notna() & (cat["name"].astype(str).str.strip() != ""),
        "(unnamed) – id " + cat["id"].astype(str))
    cat = cat.rename(columns={"id": "product_id"}).set_index("product_id")

    metrics = financial_metrics(order_items, inventory, cat.index, cutoff)
    metrics = metrics.join(operational_metrics(order_items, cat.index, cutoff), how="left")
    metrics = metrics.join(cat[["product_name", "brand"]], how="left")
    category_gp = metrics["gross_profit"].sum()
    metrics["contribution_pct"] = 100 * metrics["gross_profit"] / category_gp
    metrics = metrics.reset_index()

    minimums = sorted(set(SENSITIVITY_MINIMUMS) | {args.min_items})
    rankings = {m: rank_products(metrics, m) for m in minimums}
    apply_expected = (args.snapshot, args.category, args.cutoff) == (
        DEFAULT_SNAPSHOT, DEFAULT_CATEGORY, DEFAULT_CUTOFF)
    run_controls(metrics, {m: len(r) for m, r in rankings.items()}, apply_expected)

    # Reference file: eligible products at the chosen minimum, ordered by final_rank.
    main_rank = rankings[args.min_items]
    columns = ["final_rank", "product_id", "product_name", "brand", "items", "revenue", "cogs",
               "gross_profit", "gross_margin_pct", "return_rate_pct", "ops_base",
               "contribution_pct", "score_balanced", "score_profitability", "score_growth_risk",
               "rank_balanced", "rank_profitability", "rank_growth_risk", "avg_rank",
               "rank_variation"]
    reference = main_rank[columns].copy()
    for col in ["revenue", "cogs", "gross_profit", "gross_margin_pct", "return_rate_pct",
                "contribution_pct", "avg_rank"]:
        reference[col] = reference[col].round(2)
    for col in ["score_balanced", "score_profitability", "score_growth_risk"]:
        reference[col] = reference[col].round(4)
    ref_path = args.raw_dir / f"product_ranking_reference_{args.snapshot}.csv"
    reference.to_csv(ref_path, index=False, encoding="utf-8")

    # Sensitivity file: top 5 at each minimum, flagged against the top 5 at minimum 3.
    top5_min3 = set(rankings[3].head(TOP_N)["product_id"])
    rows = []
    for m in SENSITIVITY_MINIMUMS:
        top = rankings[m].head(TOP_N)
        for _, r in top.iterrows():
            rows.append({"min_items": m, "final_rank": int(r["final_rank"]),
                         "product_id": int(r["product_id"]),
                         "avg_rank": round(r["avg_rank"], 2),
                         "in_top5_at_min3": "true" if r["product_id"] in top5_min3 else "false"})
    sens_path = args.raw_dir / f"product_ranking_sensitivity_{args.snapshot}.csv"
    pd.DataFrame(rows).to_csv(sens_path, index=False, encoding="utf-8")

    # Console summary.
    print(f"\nTop 10 at minimum {args.min_items} ({args.category}, delivered before {args.cutoff})")
    show = reference.head(10)[["final_rank", "product_id", "product_name", "brand", "items",
                               "gross_profit", "gross_margin_pct", "return_rate_pct",
                               "contribution_pct", "rank_balanced", "rank_profitability",
                               "rank_growth_risk", "avg_rank", "rank_variation"]]
    with pd.option_context("display.width", 250, "display.max_columns", None,
                           "display.max_colwidth", 40):
        print(show.to_string(index=False))

    print(f"\nSensitivity: overlap with the top {TOP_N} at minimum 3")
    for m in SENSITIVITY_MINIMUMS:
        overlap = len(top5_min3 & set(rankings[m].head(TOP_N)["product_id"]))
        print(f"  minimum {m}: {overlap} of {TOP_N}")

    print(f"\nWrote {ref_path.relative_to(REPO_ROOT) if ref_path.is_relative_to(REPO_ROOT) else ref_path}")
    print(f"Wrote {sens_path.relative_to(REPO_ROOT) if sens_path.is_relative_to(REPO_ROOT) else sens_path}")


if __name__ == "__main__":
    main()
