# Stage 04 — Garment Types for Advertising

**Stage 4 Status: IN PROGRESS** — the product-level reference ranking exists and serves as independent validation evidence (2026-10-15). The Python reference for the garment-type ranking is complete (2026-10-16). The next step is the Power BI implementation of the garment-type ranking.

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

## Garment-Type Classification (v1)

**[ANALYTICAL ASSUMPTION]** TheLook has no product-type field, so the garment type is derived from the product name with the ordered keyword rules below (from `RULES` and `EXCLUSION_PHRASES` in `scripts/product_type_classification.py`).

| Order | Step | Product type | Keywords / phrases |
|---|---|---|---|
| 0 | Exclusion phrases (removed before matching) | — | `button down`, `turn down`, `fleece lined` |
| 1 | R1 | Vests | `vest`, `gilet`, `waistcoat`, `windvest` |
| 2 | R2 | Parkas & Down | `parka`, `down`, `puffer`, `puffy` |
| 3 | R3 | Coats | `trench`, `trenchcoat`, `peacoat`, `pea coat`, `overcoat`, `topcoat`, `raincoat`, `carcoat`, `car coat`, `duster` |
| 4 | R4 | Jackets | `jacket`, `jac`, `bomber`, `windbreaker`, `anorak`, `blazer`, `softshell`, `soft shell`, `shell`, `windshirt`, `blouson` |
| 5 | R5 | Coats | `coat` |
| 6 | R6 | Fleece & Hoodies | `fleece`, `hoodie`, `hoody`, `sweatshirt`, `sweater` |
| — | No match | Other | — |

How the matching works:

- The name is lowercased and every non-alphanumeric character becomes a space (so "Fleece-Lined" becomes "fleece lined"); repeated spaces are collapsed.
- The exclusion phrases are removed, because they contain a keyword but describe a detail, not the garment (e.g., a "button down" collar is not down filling).
- Keywords match whole words only.
- The rules are checked in order and the first match wins.
- The main garment noun wins: fleece and hoodie words apply only when no vest, parka/down, coat or jacket word is present in the name (e.g., a jacket with a fleece hood stays Jackets).

Review results:

- **[OBSERVED FACT]** The category has 1,420 products; 1,111 of them have sales in the closed months.
- **[OBSERVED FACT]** Products per type (all products / with sales):

| Product type | Products | With sales |
|---|---|---|
| Vests | 98 | 78 |
| Parkas & Down | 147 | 121 |
| Coats | 295 | 233 |
| Jackets | 752 | 580 |
| Fleece & Hoodies | 53 | 42 |
| Other | 75 | 57 |
| **Total** | **1,420** | **1,111** |

- **[OBSERVED FACT]** The draft's second rule order (main garment noun before fleece/hoodie words) moved 63 products, mostly fleece-trimmed or hooded jackets and coats that the first order had read as sweatshirts.
- **[OBSERVED FACT]** A review of 10 random names per type (fixed seed) found no misclassified name in those samples, and the full list of names classified as Other was reviewed. The remaining names were not reviewed one by one.
- **[OBSERVED FACT]** Only 1 of the 1,420 products has a name that contradicts its department field: a pair of pants, classified as Other.

## Garment-Type Ranking (Python reference)

Computed by `scripts/type_ranking_reference.py` from the snapshot CSVs, with the same four criteria, three scenarios and robustness measures as the category model. Gross profit in the dataset's currency units.

| Final rank | Product type | Products with sales | Items | Gross profit | Gross margin % | Return rate % | Avg rank | Rank variation |
|---|---|---|---|---|---|---|---|---|
| 1 | Jackets | 580 | 1,150 | 92,177.39 | 55.79% | 27.46% | 1.00 | 0 |
| 2 | Parkas & Down | 121 | 211 | 23,503.14 | 55.11% | 25.17% | 2.33 | 1 |
| 3 | Vests | 78 | 157 | 8,775.76 | 56.05% | 30.53% | 3.00 | 2 |
| 4 | Coats | 233 | 437 | 35,220.29 | 55.21% | 28.73% | 3.67 | 1 |
| 5 | Fleece & Hoodies | 42 | 84 | 4,076.30 | 55.17% | 26.32% | 5.00 | 0 |
| — | Other (not ranked) | 57 | 120 | 10,977.47 | 56.75% | 20.00% | — | — |

Descriptive figures (not ranking criteria):

| Product type | Share of category gross profit | Gross profit per product with sales | Share of items men / women |
|---|---|---|---|
| Jackets | 52.75% | 158.93 | 69.22% / 30.78% |
| Parkas & Down | 13.45% | 194.24 | 43.60% / 56.40% |
| Vests | 5.02% | 112.51 | 80.89% / 19.11% |
| Coats | 20.16% | 151.16 | 54.23% / 45.77% |
| Fleece & Hoodies | 2.33% | 97.05 | 69.05% / 30.95% |

Control checks passed: 2,159 items, 174,730.35 gross profit and 1,111 products with sales; the sum of all types, including Other, equals the category totals.

## Findings at Garment-Type Level

- **[OBSERVED FACT]** Jackets rank first in all three scenarios (rank variation 0); Parkas & Down are second.
- **[OBSERVED FACT]** Jackets account for 52.75% of the category's gross profit and 752 of its 1,420 products (53%).
- **[OBSERVED FACT]** Parkas & Down have the highest gross profit per product with sales among the ranked types (194.24 vs 158.93 for Jackets).
- **[OBSERVED FACT]** Jackets are about 69% men's and 31% women's by items sold; department is shown as a descriptive label only.
- **[OBSERVED FACT]** Gross margin differs by less than one percentage point across the ranked types (55.11% to 56.05%).
- **[OBSERVED FACT]** Ranks 3 and 4 (Vests and Coats) are nearly tied under the Balanced scenario (scores 28.0456 vs 28.0722); ranks 1 and 2 are not sensitive.
- **[ANALYTICAL ASSUMPTION]** Interpretation: Jackets win largely because they are the most numerous type, since two of the four criteria (gross profit and sales volume) are totals; and Min-Max scaling stretches the tiny margin differences over the full 0–100 range.
- **[DATASET LIMITATION]** Classification is by name: a down-filled jacket whose name does not include a word such as "down" is classified as Jackets. "Other" holds 75 products (57 with sales) that have no garment word or are not outerwear (e.g., scrub tops, pants).

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

- **[BUSINESS RULE / DECISION]** For the garment-type ranking, the minimum-items threshold and the tie-break rule are now defined: there is no minimum-items threshold for garment types, because their samples are large (items per type are shown); the tie-break is the higher gross profit, then the type name. No tie occurred.
- **[BUSINESS RULE / DECISION]** Stage 4 ranks garment types (e.g., jackets, coats, parkas) using the same four criteria and the same three scenarios as the category model. Top products are shown as examples for the ad, not as the ranking unit.
- **[ANALYTICAL ASSUMPTION]** TheLook has no product-type field. Product type is derived from the product name with keyword rules and manually reviewed; the rules and the review result are documented in the "Garment-Type Classification (v1)" section. Keyword rules can misclassify products, which is why the manual review is required.
- **[BUSINESS RULE / DECISION]** Department (men's/women's) is shown as a descriptive label only. There is no analysis of whether advertising performs differently by department.
- **[BUSINESS RULE / DECISION]** Out of scope: marketing impact, publication and performance measurement. The Stage 4 output is the garment type, its department label and 3 to 5 example products, which is the input for Stages 5 and 6.
- **[BUSINESS RULE / DECISION]** Option A accepted (2026-10-16): five ranked garment types, ranked directly, with no sub-splitting of Jackets. The size effect (Jackets are the most numerous type) is documented as a limitation. Sub-splitting Jackets is possible future work.
- **[BUSINESS RULE / DECISION]** Classification rules v1 are frozen. "Other" is a mixed residual group and is not eligible for the ranking.
- **[BUSINESS RULE / DECISION]** Example products per type are the top 5 products of that type in the product-level reference (products with at least 3 items), in product final-rank order.
- **[BUSINESS RULE / DECISION]** Scope reminder: the project goal is to find the best category and the best garment types and products inside it; what happens to them in marketing is outside the project.
- **[BUSINESS RULE / DECISION]** The garment-type return rate is pooled: returned items / (complete + returned items) over all products of the type, the same definition as in the category model.

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

Garment-type classification and ranking evidence (commit `0758f1c`):

- `scripts/product_type_classification.py` — garment-type classification rules v1 (ordered keyword rules on the product name) and the review output (read-only on the snapshot).
- `scripts/type_ranking_reference.py` — independent Python reference for the garment-type ranking, computed from the snapshot CSVs (read-only).
- `data/raw/product_type_review_2026-10-07.csv` — every product in the category with its garment type and the rule that matched.
- `data/raw/type_ranking_reference_2026-10-07.csv` — garment types ordered by final rank, with metrics, descriptive figures, scores and ranks (Other included, not ranked).
- `data/raw/type_ranking_examples_2026-10-07.csv` — the top 5 example products per ranked garment type.

## Stage Validation

*(to be filled as the stage advances)*

## Stage Log

- **Method definition (2026-10-15):** defined the Stage 4 method — four criteria per product, the Stage 3 weighting scenarios and robustness measures, contribution and price tier as descriptive figures, a minimum of 3 items with 2 and 4 as sensitivity checks, and a Power BI ranking validated by an independent Python reference. Recomputed the product-level sample sizes for Outerwear & Coats from the snapshot CSVs.
- **Reframing (2026-10-16):** moved the Stage 4 ranking unit from products to garment types, because the product-level reference showed very small samples, a weak return-rate criterion and a top 5 that is fragile to the minimum-items threshold. Products are kept as ad examples; department is a descriptive label; marketing impact is out of scope. The Stage 4 output is the input for the Stage 5–6 ad generation.
- **Garment-type classification and Python reference (2026-10-16):** drafted keyword rules on the product name, reordered them so the main garment noun wins over fleece/hoodie words (63 products moved), reviewed the result manually and froze the rules as v1. Built the independent Python reference for the garment-type ranking: Jackets first in all three scenarios, Parkas & Down second; control checks passed. Accepted Option A (five types, no sub-splitting of Jackets). The Power BI implementation is the next step.

**Stage 4 Status: IN PROGRESS**
