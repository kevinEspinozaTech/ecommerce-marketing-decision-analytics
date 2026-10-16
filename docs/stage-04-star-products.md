# Stage 04 — Star Products

**Stage 4 Status: IN PROGRESS** — the method for ranking products inside the winning category has been defined (2026-10-15). The product ranking has not yet been built.

## Stage Objective

Identify the **star products** inside the winning category from Stage 3, **Outerwear & Coats**: the products that drive the category's result.

**[BUSINESS RULE / DECISION]** Advertising in Stage 5 will focus on the top 3 to 5 products; the top 5 are analyzed in this stage.

## Technical Context

- **Data source:** the same frozen snapshot as Stage 3 (T = `2026-10-07 13:27:26` UTC), from the snapshot CSVs in `data/raw/` — see `docs/stage-03-data-model.md`.
- **Financial cohort (Closed Months):** the same rules as Stage 3 — status `Complete`, delivered before 2026-10-01.
- **Operational cohort:** the same rules as Stage 3, used for the return rate — items **created** before 2026-10-01 with a final status (`Complete`, `Returned` or `Cancelled`).
- **Category:** Outerwear & Coats, the category recommended by the Stage 3 decision model.

**[DATASET LIMITATION]** TheLook is synthetic. All figures describe this dataset only, never a real company.

## Product-Level Sample Size

**[DATASET LIMITATION]** Recomputed from the snapshot CSVs on 2026-10-15, for Outerwear & Coats in the closed months:

| Measure | Value |
|---|---|
| Products with sales | 1,111 |
| Items sold (total) | 2,159 |
| Products that sold a single item | 470 |
| Maximum items sold by one product | 8 |
| Products with at least 3 items | 273 |
| Items covered by those 273 products | 953 |
| Share of the category's gross profit covered by those 273 products | 44.7% |
| Sensitivity check — minimum of 2 items: products / items / share of gross profit | 641 / 1,689 / 77.7% |
| Sensitivity check — minimum of 4 items: products / items / share of gross profit | 86 / 392 / 15.9% |

Product-level rates such as return rate rest on very small samples and must be read with caution.

## Work Completed

*(to be filled as the stage advances)*

## Decisions Made

Kevin's decisions, 2026-10-15:

- **[BUSINESS RULE / DECISION]** The same four criteria as the Stage 3 category model, applied per product: gross profit, gross margin %, sales volume and return rate (inverted, because lower is better).
- **[BUSINESS RULE / DECISION]** The same three weighting scenarios as Stage 3, and the same robustness measures (average rank and rank variation).
- **[BUSINESS RULE / DECISION]** Each product's contribution to the category's gross profit is reported as a descriptive figure, not as a fifth criterion, because it ranks identically to gross profit.
- **[BUSINESS RULE / DECISION]** Price tier is descriptive only; it is not a ranking criterion.
- **[ANALYTICAL ASSUMPTION]** A product must have at least 3 items in the closed months to be ranked. Minimums of 2 and 4 items are tested as sensitivity checks.
- **[BUSINESS RULE / DECISION]** An independent Python reference is computed from the snapshot CSVs and used to validate the Power BI (DAX) ranking, as in Stage 3.
- **[BUSINESS RULE / DECISION]** Tie-break rule (2026-10-15): when two products have the same scenario score, or the same average rank, the one with the higher gross profit ranks first; if still tied, the lower product id ranks first. Ranks are ordinal, so no rank is repeated.

## Concepts Learned

*(to be filled as the stage advances)*

## Problems Encountered

*(to be filled as the stage advances)*

## Solutions

*(to be filled as the stage advances)*

## PL-300 Connection

*(to be filled as the stage advances)*

## Skills Demonstrated

*(to be filled as the stage advances)*

## Portfolio Evidence

- `scripts/product_ranking_reference.py` — independent Python reference for the product ranking, computed from the snapshot CSVs (read-only).
- `data/raw/product_ranking_reference_2026-10-07.csv` — eligible products ordered by final rank, with their metrics, scores and ranks.
- `data/raw/product_ranking_sensitivity_2026-10-07.csv` — the top 5 at each minimum-volume setting used in the sensitivity check.

## Stage Validation

*(to be filled as the stage advances)*

## Stage Log

- **Method definition (2026-10-15):** defined the Stage 4 method — four criteria per product, the Stage 3 weighting scenarios and robustness measures, contribution and price tier as descriptive figures, a minimum of 3 items with 2 and 4 as sensitivity checks, and a Power BI ranking validated by an independent Python reference. Recomputed the product-level sample sizes for Outerwear & Coats from the snapshot CSVs.

**Stage 4 Status: IN PROGRESS**
