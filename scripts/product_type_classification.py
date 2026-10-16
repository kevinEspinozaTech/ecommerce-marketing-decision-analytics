"""
Draft garment-type classification for one category (Project 01, Stage 4).

TheLook has no product-type field, so the garment type is derived from the
product name with an ordered list of keyword rules: the first rule that matches
wins, and unmatched products are "Other". This is a DRAFT for manual review;
the final rules will be re-implemented in Power Query as a conditional column,
so the matching is deliberately simple:

  1. lowercase the name and replace every non-alphanumeric character with a
     space (so "Fleece-Lined" becomes "fleece lined" and "Arc'teryx" becomes
     "arc teryx"), then collapse repeated spaces;
  2. remove the exclusion phrases (e.g. "button down"), which contain a
     keyword but do not describe the garment;
  3. a keyword matches only as a whole word: " keyword " must appear inside
     " cleaned name " (spaces added at both ends).

Read-only on the snapshot: it reads products (and order_items / inventory_items
only to count products with sales in the closed months) and writes one derived
CSV file (no personal data):
    data/raw/product_type_review_<snapshot>.csv

Usage:
    python scripts/product_type_classification.py
    python scripts/product_type_classification.py --seed 42 --sample 10
"""

import argparse
import re
import sys
from pathlib import Path

import pandas as pd

from product_ranking_reference import (DEFAULT_CATEGORY, DEFAULT_CUTOFF, DEFAULT_SNAPSHOT,
                                       RAW_DIR, REPO_ROOT, financial_metrics, load_snapshot)

DEFAULT_SEED = 42
DEFAULT_SAMPLE = 10
OTHER = "Other"

# Phrases removed from the cleaned name before matching. They contain a keyword
# but describe a detail, not the garment.
EXCLUSION_PHRASES = [
    "button down",   # collar / closure detail, not down filling
    "turn down",     # "turn down collar", not down filling
    "fleece lined",  # a lined jacket, not a fleece garment
]

# Ordered rules: the FIRST rule that matches wins. (rule id, product type, keywords)
# The main garment noun wins: a name such as "Jacket with Detachable Fleece Hood"
# or "Pea Coat with Hoody" stays Jackets / Coats. Fleece & Hoodies is therefore
# checked last and applies only when no vest, parka/down, coat or jacket word is
# present in the name.
RULES = [
    # R1 - Vests first: "Down Vest", "Fleece Vest" and "Vest Jacket" are vests.
    ("R1", "Vests", ["vest", "gilet", "waistcoat", "windvest"]),
    # R2 - Insulated garments before jackets and coats: "Down Jacket", "Parka Coat".
    ("R2", "Parkas & Down", ["parka", "down", "puffer", "puffy"]),
    # R3 - Specific coat words before jackets: "Trench Coat Jacket" is a coat.
    ("R3", "Coats", ["trench", "trenchcoat", "peacoat", "pea coat", "overcoat",
                     "topcoat", "raincoat", "carcoat", "car coat", "duster"]),
    # R4 - Jackets, including jacket-like styles that never say "jacket".
    ("R4", "Jackets", ["jacket", "jac", "bomber", "windbreaker", "anorak", "blazer",
                       "softshell", "soft shell", "shell", "windshirt", "blouson"]),
    # R5 - Generic "coat" after jackets: "X Jacket Coat" was already caught by R4.
    ("R5", "Coats", ["coat"]),
    # R6 - Fleece and hoodies only when no main garment noun matched above.
    ("R6", "Fleece & Hoodies", ["fleece", "hoodie", "hoody", "sweatshirt", "sweater"]),
]

# Previous rule order (Fleece & Hoodies before Coats and Jackets), kept only to
# print the before/after comparison in the review output.
PREVIOUS_RULES = [RULES[0], RULES[1], ("R3", "Fleece & Hoodies", RULES[5][2]),
                  ("R4", "Coats", RULES[2][2]), ("R5", "Jackets", RULES[3][2]),
                  ("R6", "Coats", RULES[4][2])]

# "Other" is the residual group: names that match no rule. It is a mix (including
# non-outerwear items) and is NOT eligible to be recommended in the ranking.
TYPE_ORDER = ["Vests", "Parkas & Down", "Coats", "Jackets", "Fleece & Hoodies", OTHER]


# -----------------------------------------------------------------------------
# Classification
# -----------------------------------------------------------------------------

def normalize(name):
    """Lowercase, non-alphanumeric to spaces, padded with one space at each end."""
    return " " + re.sub(r"[^a-z0-9]+", " ", str(name).lower()).strip() + " "


def clean_name(name):
    padded = normalize(name)
    for phrase in EXCLUSION_PHRASES:
        padded = padded.replace(f" {phrase} ", " ")
    return padded


def first_match(padded, rules):
    """(type, matched rule) of the first rule with a whole-word keyword match."""
    for rule_id, product_type, keywords in rules:
        for kw in keywords:
            if f" {kw} " in padded:
                return product_type, f"{rule_id}: {kw}"
    return OTHER, "none"


def classify(cat, rules=RULES):
    rows = []
    for _, r in cat.iterrows():
        padded = clean_name(r["name"]) if pd.notna(r["name"]) else " "
        product_type, matched_rule = first_match(padded, rules)
        rows.append({"product_id": r["product_id"], "product_name": r["product_name"],
                     "brand": r["brand"], "department": r["department"],
                     "product_type": product_type, "matched_rule": matched_rule})
    return pd.DataFrame(rows)


# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--snapshot", default=DEFAULT_SNAPSHOT, help="snapshot date in file names")
    parser.add_argument("--category", default=DEFAULT_CATEGORY)
    parser.add_argument("--cutoff", default=DEFAULT_CUTOFF, help="Closed Months cut-off (exclusive)")
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED, help="seed for the review samples")
    parser.add_argument("--sample", type=int, default=DEFAULT_SAMPLE, help="sample size per type")
    parser.add_argument("--raw-dir", type=Path, default=RAW_DIR)
    args = parser.parse_args()

    products = pd.read_csv(args.raw_dir / f"products_{args.snapshot}.csv",
                           usecols=["id", "category", "name", "brand", "department"])
    cat = products[products["category"] == args.category].copy()
    if cat.empty:
        sys.exit(f"ERROR: no products in category {args.category!r}.")
    cat["product_name"] = cat["name"].where(
        cat["name"].notna() & (cat["name"].astype(str).str.strip() != ""),
        "(unnamed) – id " + cat["id"].astype(str))
    cat = cat.rename(columns={"id": "product_id"})

    result = classify(cat)
    result["previous_type"] = classify(cat, PREVIOUS_RULES)["product_type"].values
    result["_type_order"] = result["product_type"].map(TYPE_ORDER.index)
    result = result.sort_values(["_type_order", "product_name", "product_id"])

    # Products with sales in the closed months (same cohort as the reference script).
    _, order_items, inventory = load_snapshot(args.raw_dir, args.snapshot)
    sold_ids = set(financial_metrics(order_items, inventory, cat["product_id"],
                                     pd.Timestamp(args.cutoff)).index)
    result["_has_sales"] = result["product_id"].isin(sold_ids)

    out_cols = ["product_id", "product_name", "brand", "department", "product_type",
                "matched_rule"]
    out_path = args.raw_dir / f"product_type_review_{args.snapshot}.csv"
    result[out_cols].to_csv(out_path, index=False, encoding="utf-8")

    # a. Counts per type, previous rule order (before) vs new rule order (after).
    print(f"a. Products per type - {args.category} (before = previous order, after = new)")

    def counts(type_col):
        return (result.groupby(type_col)
                .agg(products=("product_id", "size"), with_sales=("_has_sales", "sum"))
                .reindex(TYPE_ORDER, fill_value=0))

    summary = pd.concat({"before": counts("previous_type"), "after": counts("product_type")},
                        axis=1)
    summary.loc["Total"] = summary.sum()
    print(summary.to_string())

    # b. Products whose type changed between the two rule orders.
    changed = result[result["previous_type"] != result["product_type"]]
    print(f"\nb. Products whose type changed ({len(changed)}): old -> new")
    for _, r in changed.iterrows():
        print(f"  {r['previous_type']} -> {r['product_type']}:  {r['product_name']}")

    # c. All names classified as Other.
    other = result[result["product_type"] == OTHER]
    print(f"\nc. Names classified as {OTHER} ({len(other)})")
    for name in other["product_name"]:
        print(f"  {name}")

    # d. Random names per type.
    print(f"\nd. Random names per type (seed {args.seed}, up to {args.sample} each)")
    for product_type in TYPE_ORDER:
        group = result[result["product_type"] == product_type]
        if group.empty:
            continue
        print(f"  {product_type} ({len(group)})")
        for name in group.sample(n=min(args.sample, len(group)),
                                 random_state=args.seed)["product_name"]:
            print(f"    {name}")

    # e. Department check: gender word in the name vs the department field.
    padded = result["product_name"].map(normalize)
    says_women = padded.str.contains(" women | womens ", regex=True)
    says_men = padded.str.contains(" men | mens ", regex=True) & ~says_women
    women_in_men = result[says_women & (result["department"] == "Men")]
    men_in_women = result[says_men & (result["department"] == "Women")]
    print("\ne. Department check")
    print(f"  name says women, department Men: {len(women_in_men)}")
    print(f"  name says men (not women), department Women: {len(men_in_women)}")
    for _, r in pd.concat([women_in_men, men_in_women]).head(20).iterrows():
        print(f"    {r['department']:<5}  {r['product_name']}")


if __name__ == "__main__":
    main()
