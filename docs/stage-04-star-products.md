# Stage 04 — Garment Types for Advertising

**Stage 4 Status: IN PROGRESS** — the product-level reference ranking exists and serves as independent validation evidence (2026-10-15). The next step is the garment-type ranking (reframed 2026-10-16).

## Stage Objective

Identify the best **garment types** (e.g., jackets, coats, parkas) inside the winning category from Stage 3, **Outerwear & Coats**, to receive the advertising budget. For each selected garment type, the stage lists 3 to 5 example products for the ad and states clearly whether it is a men's or women's garment.

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

## Findings at Product Level

From the product-level reference ranking (minimum of 3 items, 273 eligible products):

- **[OBSERVED FACT]** The top 5 products represent about 3.4% of the category's gross profit.
- **[ANALYTICAL ASSUMPTION]** Interpretation: no single product drives the category; it appears to win through breadth rather than a few star products.
- **[OBSERVED FACT]** 156 of the 273 eligible products have a 0% return rate, so the return-rate criterion barely discriminates at product level.
- **[OBSERVED FACT]** The product top 5 is fragile to the minimum-items threshold: a minimum of 2 items keeps 4 of the 5, and a minimum of 4 items keeps 3 of the 5; the #1 product is stable.
- **[DATASET LIMITATION]** Product-level samples are very small (470 of 1,111 products sold a single item), which is why the final ranking moves to garment types.

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

Kevin's decisions, 2026-10-16 (reframing). The 2026-10-15 decisions on the minimum of 3 items (with 2 and 4 as sensitivity checks) and on the tie-break (gross profit, then lower product id) were defined for the product-level reference and remain valid only for that reference.

- **[BUSINESS RULE / DECISION]** For the garment-type ranking, the minimum-items threshold and the tie-break rule are still to be defined when the ranking is built, because garment types have much larger samples than individual products.
- **[BUSINESS RULE / DECISION]** Stage 4 ranks garment types (e.g., jackets, coats, parkas) using the same four criteria and the same three scenarios as the category model. Top products are shown as examples for the ad, not as the ranking unit.
- **[ANALYTICAL ASSUMPTION]** TheLook has no product-type field. Product type is derived from the product name with documented keyword rules and manually reviewed; the rules and the review result will be documented when built. Keyword rules can misclassify products, which is why the manual review is required.
- **[BUSINESS RULE / DECISION]** Department (men's/women's) is shown as a descriptive label only. There is no analysis of whether advertising performs differently by department.
- **[BUSINESS RULE / DECISION]** Out of scope: marketing impact, publication and performance measurement. The Stage 4 output is the garment type, its department label and 3 to 5 example products, which is the input for Stages 5 and 6.

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

The files below are the independent product-level validation evidence. The final Stage 4 ranking is at garment-type level.

- `scripts/product_ranking_reference.py` — independent Python reference for the product ranking, computed from the snapshot CSVs (read-only).
- `data/raw/product_ranking_reference_2026-10-07.csv` — eligible products ordered by final rank, with their metrics, scores and ranks.
- `data/raw/product_ranking_sensitivity_2026-10-07.csv` — the top 5 at each minimum-volume setting used in the sensitivity check.

## Stage Validation

*(to be filled as the stage advances)*

## Stage Log

- **Method definition (2026-10-15):** defined the Stage 4 method — four criteria per product, the Stage 3 weighting scenarios and robustness measures, contribution and price tier as descriptive figures, a minimum of 3 items with 2 and 4 as sensitivity checks, and a Power BI ranking validated by an independent Python reference. Recomputed the product-level sample sizes for Outerwear & Coats from the snapshot CSVs.
- **Reframing (2026-10-16):** moved the Stage 4 ranking unit from products to garment types, because the product-level reference showed very small samples, a weak return-rate criterion and a top 5 that is fragile to the minimum-items threshold. Products are kept as ad examples; department is a descriptive label; marketing impact is out of scope. The Stage 4 output is the input for the Stage 5–6 ad generation.

**Stage 4 Status: IN PROGRESS**
