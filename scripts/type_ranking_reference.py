"""
Independent reference for the Stage 4 garment-type ranking (Project 01, Stage 4).

Classifies every product of one category (default: Outerwear & Coats) into a
garment type with the frozen rules of product_type_classification.py (v1) and
ranks the types with the Stage 3 decision logic: four criteria (gross profit,
gross margin %, volume, return rate inverted), min-max scores across the ranked
types, three weighting scenarios, average rank and rank variation. "Other" is a
mixed residual group: its metrics are reported but it is not ranked. The output
is used to validate the Power BI ranking; it is not a source for the dashboard.

Read-only on the snapshot: it reads products, order_items, inventory_items and
the product-level reference, and writes two derived CSV files (no personal data):
    data/raw/type_ranking_reference_<snapshot>.csv
    data/raw/type_ranking_examples_<snapshot>.csv

Usage:
    python scripts/type_ranking_reference.py
"""

import argparse
import sys
from pathlib import Path

import pandas as pd

from product_ranking_reference import (DEFAULT_CATEGORY, DEFAULT_CUTOFF, DEFAULT_SNAPSHOT,
                                       EXPECTED_GROSS_PROFIT, EXPECTED_ITEMS,
                                       EXPECTED_PRODUCTS_WITH_SALES, RAW_DIR, REPO_ROOT,
                                       SCENARIOS, SCORE_RANK_DECIMALS, TOLERANCE,
                                       financial_metrics, load_snapshot, minmax_score,
                                       operational_metrics)
from product_type_classification import OTHER, TYPE_ORDER, classify

EXAMPLES_PER_TYPE = 5
DEPARTMENTS = ["Men", "Women"]


# -----------------------------------------------------------------------------
# Per-type metrics
# -----------------------------------------------------------------------------

def type_metrics(cat, order_items, inventory, cutoff):
    """Per-type aggregates; financial sums are additive over the products."""
    product_type = cat.set_index("product_id")["product_type"]

    fin = financial_metrics(order_items, inventory, cat["product_id"], cutoff)
    fin = fin.join(cat.set_index("product_id")[["product_type", "department"]])
    metrics = fin.groupby("product_type").agg(products_with_sales=("items", "size"),
                                              items=("items", "sum"),
                                              revenue=("revenue", "sum"),
                                              cogs=("cogs", "sum"))
    metrics.insert(0, "products", cat.groupby("product_type").size())
    metrics = metrics.reindex(TYPE_ORDER).fillna(0)
    metrics["gross_profit"] = metrics["revenue"] - metrics["cogs"]
    metrics["gross_margin_pct"] = 100 * metrics["gross_profit"] / metrics["revenue"]

    # Return rate over the type's pooled operational counts (not an average of
    # product rates): the same function, with product_id replaced by the type.
    ops_items = order_items[order_items["product_id"].isin(product_type.index)].copy()
    ops_items["product_id"] = ops_items["product_id"].map(product_type)
    metrics = metrics.join(operational_metrics(ops_items, TYPE_ORDER, cutoff))

    metrics["gp_share_pct"] = 100 * metrics["gross_profit"] / metrics["gross_profit"].sum()
    metrics["gp_per_product_with_sales"] = (metrics["gross_profit"]
                                            / metrics["products_with_sales"])
    dept_items = fin.pivot_table(index="product_type", columns="department", values="items",
                                 aggfunc="sum", fill_value=0)
    for dept in DEPARTMENTS:
        col = dept_items[dept] if dept in dept_items else 0
        metrics[f"items_share_{dept.lower()}_pct"] = 100 * col / metrics["items"]
    metrics.index.name = "product_type"
    return metrics, fin


# -----------------------------------------------------------------------------
# Scoring and ranking
# -----------------------------------------------------------------------------

def ordinal_rank(df, key_col, ascending):
    """1..n with no repeated ranks; ties broken by higher gross profit, then type name."""
    ordered = df.reset_index().sort_values([key_col, "gross_profit", "product_type"],
                                           ascending=[ascending, False, True])
    return pd.Series(range(1, len(ordered) + 1), index=ordered["product_type"].values)


def rank_types(metrics):
    ranked = metrics.drop(index=OTHER).copy()
    if ranked["return_rate_pct"].isna().any():
        sys.exit("ERROR: a ranked type has no operational-cohort base.")

    criteria = pd.DataFrame({
        "gp": minmax_score(ranked["gross_profit"], label="gross profit"),
        "gm": minmax_score(ranked["gross_margin_pct"], label="gross margin %"),
        "vol": minmax_score(ranked["items"], label="volume"),
        "rr": minmax_score(ranked["return_rate_pct"], invert=True, label="return rate"),
    })
    for name, weights in SCENARIOS.items():
        score = (criteria[["gp", "gm", "vol", "rr"]] * weights).sum(axis=1) / 100
        ranked[f"score_{name}"] = score
        ranked[f"_rank_key_{name}"] = score.round(SCORE_RANK_DECIMALS)
        ranked[f"rank_{name}"] = ordinal_rank(ranked, f"_rank_key_{name}", False)

    rank_cols = [f"rank_{name}" for name in SCENARIOS]
    ranked["avg_rank"] = ranked[rank_cols].mean(axis=1)
    ranked["rank_variation"] = ranked[rank_cols].max(axis=1) - ranked[rank_cols].min(axis=1)
    ranked["_avg_key"] = ranked["avg_rank"].round(SCORE_RANK_DECIMALS)
    ranked["final_rank"] = ordinal_rank(ranked, "_avg_key", True)
    ranked = ranked.drop(columns=[c for c in ranked.columns if c.startswith("_")])
    return ranked.sort_values("final_rank")


# -----------------------------------------------------------------------------
# Controls
# -----------------------------------------------------------------------------

def run_controls(metrics, fin, apply_expected):
    total_items = int(fin["items"].sum())
    total_gp = float(fin["gross_profit"].sum())
    with_sales = len(fin)
    print("Control checks")
    print(f"  closed-month items        : {total_items:,}")
    print(f"  closed-month gross profit : {total_gp:,.2f}")
    print(f"  products with sales       : {with_sales:,}")

    failures = []
    for col, total in [("items", total_items), ("gross_profit", total_gp),
                       ("products_with_sales", with_sales),
                       ("revenue", float(fin["revenue"].sum())),
                       ("cogs", float(fin["cogs"].sum()))]:
        type_sum = float(metrics[col].sum())
        ok = abs(type_sum - total) <= TOLERANCE
        print(f"  sum of types (incl. {OTHER}) = category total, {col}: "
              f"{type_sum:,.2f} vs {total:,.2f}: {'PASS' if ok else 'FAIL'}")
        if not ok:
            failures.append(f"type sum of {col}")

    if apply_expected:
        if total_items != EXPECTED_ITEMS:
            failures.append(f"items {total_items:,} != {EXPECTED_ITEMS:,}")
        if abs(total_gp - EXPECTED_GROSS_PROFIT) > TOLERANCE:
            failures.append(f"gross profit {total_gp:,.2f} != {EXPECTED_GROSS_PROFIT:,.2f}")
        if with_sales != EXPECTED_PRODUCTS_WITH_SALES:
            failures.append(f"products with sales {with_sales:,} != "
                            f"{EXPECTED_PRODUCTS_WITH_SALES:,}")
        if not failures:
            print(f"  items / gross profit / products with sales match the expected "
                  f"{EXPECTED_ITEMS:,} / {EXPECTED_GROSS_PROFIT:,.2f} / "
                  f"{EXPECTED_PRODUCTS_WITH_SALES:,}: PASS")
    else:
        print("  (non-default parameters: expected values not applied)")
    if failures:
        sys.exit("ERROR: control check failed: " + "; ".join(failures))


# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--snapshot", default=DEFAULT_SNAPSHOT, help="snapshot date in file names")
    parser.add_argument("--category", default=DEFAULT_CATEGORY)
    parser.add_argument("--cutoff", default=DEFAULT_CUTOFF, help="Closed Months cut-off (exclusive)")
    parser.add_argument("--raw-dir", type=Path, default=RAW_DIR)
    args = parser.parse_args()

    cutoff = pd.Timestamp(args.cutoff)
    _, order_items, inventory = load_snapshot(args.raw_dir, args.snapshot)
    products = pd.read_csv(args.raw_dir / f"products_{args.snapshot}.csv",
                           usecols=["id", "category", "name", "brand", "department"])
    cat = products[products["category"] == args.category].copy()
    if cat.empty:
        sys.exit(f"ERROR: no products in category {args.category!r}.")
    cat["product_name"] = cat["name"].where(
        cat["name"].notna() & (cat["name"].astype(str).str.strip() != ""),
        "(unnamed) – id " + cat["id"].astype(str))
    cat = cat.rename(columns={"id": "product_id"})
    cat = classify(cat)

    metrics, fin = type_metrics(cat, order_items, inventory, cutoff)
    ranked = rank_types(metrics)

    # Reference file: ranked types by final_rank, then Other marked not_ranked.
    other = metrics.loc[[OTHER]].copy()
    table = pd.concat([ranked, other]).reset_index()
    table["ranking_status"] = ["ranked"] * len(ranked) + ["not_ranked"]
    columns = ["final_rank", "product_type", "ranking_status", "products", "products_with_sales",
               "items", "revenue", "cogs", "gross_profit", "gross_margin_pct",
               "return_rate_pct", "ops_base", "gp_share_pct", "gp_per_product_with_sales",
               "items_share_men_pct", "items_share_women_pct", "score_balanced",
               "score_profitability", "score_growth_risk", "rank_balanced",
               "rank_profitability", "rank_growth_risk", "avg_rank", "rank_variation"]
    reference = table[columns].copy()
    for col in ["revenue", "cogs", "gross_profit", "gross_margin_pct", "return_rate_pct",
                "gp_share_pct", "gp_per_product_with_sales", "items_share_men_pct",
                "items_share_women_pct", "avg_rank"]:
        reference[col] = reference[col].round(2)
    for col in ["score_balanced", "score_profitability", "score_growth_risk"]:
        reference[col] = reference[col].round(4)
    for col in ["final_rank", "products", "products_with_sales", "items", "ops_base",
                "rank_balanced", "rank_profitability", "rank_growth_risk", "rank_variation"]:
        reference[col] = reference[col].astype("Int64")
    ref_path = args.raw_dir / f"type_ranking_reference_{args.snapshot}.csv"
    reference.to_csv(ref_path, index=False, encoding="utf-8")

    # Examples file: top products per ranked type from the product-level reference.
    product_ref = pd.read_csv(args.raw_dir / f"product_ranking_reference_{args.snapshot}.csv",
                              usecols=["final_rank", "product_id", "items", "gross_profit"])
    product_ref = product_ref.merge(cat, on="product_id", how="left")
    if product_ref["product_type"].isna().any():
        sys.exit("ERROR: the product-level reference has products outside the category.")
    product_ref = product_ref.sort_values("final_rank")
    rows, short_types = [], []
    for product_type in ranked.index:
        top = product_ref[product_ref["product_type"] == product_type].head(EXAMPLES_PER_TYPE)
        if len(top) < EXAMPLES_PER_TYPE:
            short_types.append((product_type, len(top)))
        for order, (_, r) in enumerate(top.iterrows(), start=1):
            rows.append({"product_type": product_type, "example_order": order,
                         "product_id": int(r["product_id"]), "product_name": r["product_name"],
                         "brand": r["brand"], "department": r["department"],
                         "items": int(r["items"]), "gross_profit": round(r["gross_profit"], 2),
                         "product_final_rank": int(r["final_rank"])})
    examples = pd.DataFrame(rows)
    ex_path = args.raw_dir / f"type_ranking_examples_{args.snapshot}.csv"
    examples.to_csv(ex_path, index=False, encoding="utf-8")

    # Console summary.
    with pd.option_context("display.width", 250, "display.max_columns", None,
                           "display.max_colwidth", 60):
        print(f"Garment-type ranking ({args.category}, delivered before {args.cutoff})")
        print(reference[["final_rank", "product_type", "ranking_status", "products",
                         "products_with_sales", "items", "gross_profit", "gross_margin_pct",
                         "return_rate_pct", "gp_share_pct", "gp_per_product_with_sales",
                         "items_share_men_pct", "items_share_women_pct"]].to_string(index=False))
        print()
        print(reference[["final_rank", "product_type", "score_balanced", "score_profitability",
                         "score_growth_risk", "rank_balanced", "rank_profitability",
                         "rank_growth_risk", "avg_rank", "rank_variation"]].to_string(index=False))

        print(f"\nExample products per type (top {EXAMPLES_PER_TYPE} from the product-level "
              f"reference, by product final rank)")
        for product_type in ranked.index:
            group = examples[examples["product_type"] == product_type]
            print(f"  {product_type}")
            print(group.drop(columns="product_type").to_string(index=False))
        for product_type, n in short_types:
            print(f"  NOTE: {product_type} has only {n} eligible product(s) in the "
                  f"product-level reference (fewer than {EXAMPLES_PER_TYPE}).")
        print()

    apply_expected = (args.snapshot, args.category, args.cutoff) == (
        DEFAULT_SNAPSHOT, DEFAULT_CATEGORY, DEFAULT_CUTOFF)
    run_controls(metrics, fin, apply_expected)

    for path in (ref_path, ex_path):
        print(f"Wrote {path.relative_to(REPO_ROOT) if path.is_relative_to(REPO_ROOT) else path}")


if __name__ == "__main__":
    main()
