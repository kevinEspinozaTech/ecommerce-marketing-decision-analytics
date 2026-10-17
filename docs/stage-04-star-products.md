# Stage 04 — Garment Types for Advertising

**Stage 4 Status: IN PROGRESS** — the product-level reference ranking exists and serves as independent validation evidence (2026-10-15). The Python reference for the garment-type ranking is complete (2026-10-16). The Power BI implementation (classification in Power Query, DAX measures, dashboard page "5 · Garment types") is complete and validated against the Python reference (2026-10-16). The stage is pending final review and closure.

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

## Power BI Implementation

### Power Query: `product_type` in `dim_product`

The Power BI file itself is kept outside the repository. Two custom columns were added to `dim_product` after the existing steps: a helper column `name_clean`, then `product_type`. The rules are the same ordered rules as `scripts/product_type_classification.py` (see "Garment-Type Classification (v1)").

`name_clean`:

```m
let
    lower = Text.Lower([Product_name] ?? ""),
    allowed = "abcdefghijklmnopqrstuvwxyz0123456789",
    chars = List.Transform(Text.ToList(lower), each if Text.Contains(allowed, _) then _ else " "),
    words = List.Select(Text.Split(Text.Combine(chars), " "), each _ <> "")
in
    " " & Text.Combine(words, " ") & " "
```

`product_type`:

```m
let
    p = Text.Replace(Text.Replace(Text.Replace([name_clean], " button down ", " "), " turn down ", " "), " fleece lined ", " "),
    has = (kw as list) as logical => List.AnyTrue(List.Transform(kw, each Text.Contains(p, " " & _ & " ")))
in
    if [category] <> "Outerwear & Coats" then "Not in scope"
    else if has({"vest","gilet","waistcoat","windvest"}) then "Vests"
    else if has({"parka","down","puffer","puffy"}) then "Parkas & Down"
    else if has({"trench","trenchcoat","peacoat","pea coat","overcoat","topcoat","raincoat","carcoat","car coat","duster"}) then "Coats"
    else if has({"jacket","jac","bomber","windbreaker","anorak","blazer","softshell","soft shell","shell","windshirt","blouson"}) then "Jackets"
    else if has({"coat"}) then "Coats"
    else if has({"fleece","hoodie","hoody","sweatshirt","sweater"}) then "Fleece & Hoodies"
    else "Other"
```

- `product_type` was set to data type Text.
- The helper column `name_clean` was removed after the check.
- A temporary filter on `category`, used for the check, was removed.
- Products outside Outerwear & Coats get "Not in scope".

### DAX measures by garment type

The measures live in the `fact_order_items` table, like the Stage 3 measures.

```dax
Type Is Ranked =
VAR T = SELECTEDVALUE ( dim_product[product_type] )
RETURN
    IF ( NOT ISBLANK ( T ) && NOT ( T IN { "Other", "Not in scope" } ), 1 )
```

```dax
Type Score Gross Profit =
VAR Types =
    FILTER ( ALL ( dim_product[product_type] ), NOT ( dim_product[product_type] IN { "Other", "Not in scope" } ) )
VAR Cur  = [Gross Profit (Closed Months)]
VAR MinV = MINX ( Types, [Gross Profit (Closed Months)] )
VAR MaxV = MAXX ( Types, [Gross Profit (Closed Months)] )
RETURN
    IF ( [Type Is Ranked] = 1, DIVIDE ( Cur - MinV, MaxV - MinV ) * 100 )
```

```dax
Type Score Gross Margin =
VAR Types =
    FILTER ( ALL ( dim_product[product_type] ), NOT ( dim_product[product_type] IN { "Other", "Not in scope" } ) )
VAR Cur  = [Gross Margin % (Closed Months)]
VAR MinV = MINX ( Types, [Gross Margin % (Closed Months)] )
VAR MaxV = MAXX ( Types, [Gross Margin % (Closed Months)] )
RETURN
    IF ( [Type Is Ranked] = 1, DIVIDE ( Cur - MinV, MaxV - MinV ) * 100 )
```

```dax
Type Score Sales Volume =
VAR Types =
    FILTER ( ALL ( dim_product[product_type] ), NOT ( dim_product[product_type] IN { "Other", "Not in scope" } ) )
VAR Cur  = [Complete Items (Closed Months)]
VAR MinV = MINX ( Types, [Complete Items (Closed Months)] )
VAR MaxV = MAXX ( Types, [Complete Items (Closed Months)] )
RETURN
    IF ( [Type Is Ranked] = 1, DIVIDE ( Cur - MinV, MaxV - MinV ) * 100 )
```

```dax
Type Score Return Rate =
VAR Types =
    FILTER ( ALL ( dim_product[product_type] ), NOT ( dim_product[product_type] IN { "Other", "Not in scope" } ) )
VAR Cur  = [Return Rate %]
VAR MinV = MINX ( Types, [Return Rate %] )
VAR MaxV = MAXX ( Types, [Return Rate %] )
RETURN
    IF ( [Type Is Ranked] = 1, DIVIDE ( MaxV - Cur, MaxV - MinV ) * 100 )
```

```dax
Type Score Balanced =
0.25 * [Type Score Gross Profit] + 0.25 * [Type Score Gross Margin]
+ 0.25 * [Type Score Sales Volume] + 0.25 * [Type Score Return Rate]
```

```dax
Type Score Profitability =
0.30 * [Type Score Gross Profit] + 0.30 * [Type Score Gross Margin]
+ 0.20 * [Type Score Sales Volume] + 0.20 * [Type Score Return Rate]
```

```dax
Type Score Growth Controlled Risk =
0.20 * [Type Score Gross Profit] + 0.30 * [Type Score Gross Margin]
+ 0.20 * [Type Score Sales Volume] + 0.30 * [Type Score Return Rate]
```

```dax
Type Rank Balanced =
VAR Types =
    FILTER ( ALL ( dim_product[product_type] ), NOT ( dim_product[product_type] IN { "Other", "Not in scope" } ) )
RETURN
    IF ( [Type Is Ranked] = 1, RANKX ( Types, [Type Score Balanced], , DESC, Skip ) )
```

```dax
Type Rank Profitability =
VAR Types =
    FILTER ( ALL ( dim_product[product_type] ), NOT ( dim_product[product_type] IN { "Other", "Not in scope" } ) )
RETURN
    IF ( [Type Is Ranked] = 1, RANKX ( Types, [Type Score Profitability], , DESC, Skip ) )
```

```dax
Type Rank Growth Controlled Risk =
VAR Types =
    FILTER ( ALL ( dim_product[product_type] ), NOT ( dim_product[product_type] IN { "Other", "Not in scope" } ) )
RETURN
    IF ( [Type Is Ranked] = 1, RANKX ( Types, [Type Score Growth Controlled Risk], , DESC, Skip ) )
```

```dax
Type Average Rank =
DIVIDE ( [Type Rank Balanced] + [Type Rank Profitability] + [Type Rank Growth Controlled Risk], 3 )
```

```dax
Type Rank Variation =
VAR R1 = [Type Rank Balanced]
VAR R2 = [Type Rank Profitability]
VAR R3 = [Type Rank Growth Controlled Risk]
RETURN
    MAX ( MAX ( R1, R2 ), R3 ) - MIN ( MIN ( R1, R2 ), R3 )
```

```dax
Top Type =
VAR Types =
    FILTER ( ALL ( dim_product[product_type] ), NOT ( dim_product[product_type] IN { "Other", "Not in scope" } ) )
VAR TopTable =
    TOPN ( 1, Types, [Type Average Rank], ASC, [Gross Profit (Closed Months)], DESC )
RETURN
    MAXX ( TopTable, dim_product[product_type] )
```

```dax
Type Bar Color =
IF ( SELECTEDVALUE ( dim_product[product_type] ) = [Top Type], "#9A7B4F", "#94A3B8" )
```

Notes:

- The measures reuse the Stage 3 base measures: `Gross Profit (Closed Months)`, `Gross Margin % (Closed Months)`, `Complete Items (Closed Months)` and `Return Rate %`.
- The Min-Max range is taken only over the five ranked types.
- `Robustness Class` was not replicated: with five types, the condition "Average Rank ≤ 10" would always be true.
- `RANKX` uses `Skip` (no tie-break), while the Python reference uses an ordinal tie-break. No tie occurred.

### Dashboard page "5 · Garment types"

The page was created by duplicating page 4, so the layout matches the Stage 3 pages. It contains:

- a `Top Type` card;
- a table with garment type, average rank, rank variation, items, gross profit, margin and return rate, sorted by average rank;
- a bar chart of the Balanced score, with the winner highlighted through `Type Bar Color`;
- a 100% stacked bar of items by department;
- a note about "Other".

A page-level filter keeps only the five ranked types.

## Stage 4 Output (input for Stages 5 and 6)

- **Winning garment type:** Jackets, first in all three scenarios.
- **Department label:** predominantly men's (69.22% of items sold are men's, 30.78% women's).
- **Example products** (from `data/raw/type_ranking_examples_2026-10-07.csv`):

| Product id | Name | Brand | Department | Items | Gross profit | Product final rank |
|---|---|---|---|---|---|---|
| 24196 | Mens Brown Sheepskin Flying Jacket 'Air force' Aviator Leather coat #S5 | Unicorn London | Men | 5 | 1,192.95 | 1 |
| 24170 | Barbour Bedale Wax Cotton Jacket Olive | Barbour | Men | 5 | 1,137.00 | 3 |
| 24283 | The North Face Nuptse 2 Jacket - Noah Green/TNF Black | The North Face | Men | 3 | 1,598.31 | 4 |
| 8436 | Calvin Klein Jeans Women's Liquid Metal Moto Jacket | Calvin Klein Jeans | Women | 5 | 446.26 | 6 |
| 23791 | Polo Ralph Lauren Men Lightweight Jacket | Ralph Lauren | Men | 7 | 483.00 | 8 |

The example products for the other four ranked types are in the same CSV.

## Work Completed

2026-10-15:

- Defined the Stage 4 method.
- Built the independent product-level Python reference and its sensitivity check.

2026-10-16:

- Reframed the stage to garment types.
- Drafted, reviewed and froze the keyword classification rules v1.
- Built the garment-type Python reference with example products.
- Implemented `product_type` in Power Query.
- Created the 16 garment-type DAX measures.
- Validated Power BI against the Python reference.
- Built the dashboard page "5 · Garment types".
- Wrote the Stage 4 output: Jackets, predominantly men's, with five example products.

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

- **Ordered keyword rules as a custom column in M:** `Text.Lower`, `Text.Replace`, `List.AnyTrue` and a local function.
- **Explicit data types:** a column of type Any blocks the column distribution view.
- **DAX:** `FILTER` over `ALL`, the `MINX`/`MAXX` iterators and context transition.
- **`RANKX`** for ranking garment types.
- **Guard-measure pattern:** `Type Is Ranked` returns blank for types that must not be scored or ranked.
- **Conditional formatting by field value** (`Type Bar Color`).

## Problems Encountered

1. The first keyword draft read "Button Down" as down filling.
2. Jackets with a fleece hood or hoodie words in the name were classified as sweatshirts.
3. The first Power Query custom column returned 100% errors.
4. The Value distribution view did not compute for the new column.
5. Risk of altering the closed Stage 3 work.

## Solutions

1. Exclusion phrases (`button down`, `turn down`, `fleece lined`) are removed before matching.
2. The rules were reordered so the main garment noun wins; 63 products moved, and the rules were frozen as v1.
3. The product name column is named `Product_name` (capital P); the field name was corrected.
4. The column had data type Any; it was set to Text.
5. The Power BI file was saved under a new name before editing, and page 5 was created by duplicating page 4, so the Stage 3 pages stay unchanged.

## PL-300 Connection

- These steps are practice for transforming data and creating DAX calculations; the custom M column goes a bit beyond the exam's conditional column.

## Skills Demonstrated

- Independent validation of a Power BI model with a Python (pandas) reference.
- Power Query M custom columns and data types.
- DAX iterators, `RANKX` and guard measures.
- Rule-based classification with documented, reviewable rules.
- Data storytelling in a dashboard page.
- Evidence-based documentation with explicit assumptions and limitations.
- Git workflow with stage-numbered commits.

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

Power BI evidence:

- `powerbi/05-garment-types.png` — screenshot of the dashboard page "5 · Garment types" (2255×1293, the same size as the other four pages in `powerbi/`).
- The Power BI file itself is kept outside the repository.

## Stage Validation

The Power BI garment-type ranking was validated against the Python reference by comparing the Power BI table with `data/raw/type_ranking_reference_2026-10-07.csv`.

- **[OBSERVED FACT]** Product counts per type in Power Query match: Vests 98, Parkas & Down 147, Coats 295, Jackets 752, Fleece & Hoodies 53, Other 75 (total 1,420). `dim_product` has 29,120 products.
- **[OBSERVED FACT]** Items, gross profit, margin and return rate match for the six types.
- **[OBSERVED FACT]** The three scenario scores, the three ranks, average rank and rank variation match for the five ranked types.
- **[OBSERVED FACT]** `Top Type` = Jackets.
- **[OBSERVED FACT]** Across the six types, items (2,159) and gross profit (174,730.35) equal the category totals. "Not in scope" holds the other categories (40,762 items).
- The comparison was done by eye, with the scores shown at two decimals in Power BI and four in the CSV.

## Stage Log

- **Method definition (2026-10-15):** defined the Stage 4 method — four criteria per product, the Stage 3 weighting scenarios and robustness measures, contribution and price tier as descriptive figures, a minimum of 3 items with 2 and 4 as sensitivity checks, and a Power BI ranking validated by an independent Python reference. Recomputed the product-level sample sizes for Outerwear & Coats from the snapshot CSVs.
- **Reframing (2026-10-16):** moved the Stage 4 ranking unit from products to garment types, because the product-level reference showed very small samples, a weak return-rate criterion and a top 5 that is fragile to the minimum-items threshold. Products are kept as ad examples; department is a descriptive label; marketing impact is out of scope. The Stage 4 output is the input for the Stage 5–6 ad generation.
- **Garment-type classification and Python reference (2026-10-16):** drafted keyword rules on the product name, reordered them so the main garment noun wins over fleece/hoodie words (63 products moved), reviewed the result manually and froze the rules as v1. Built the independent Python reference for the garment-type ranking: Jackets first in all three scenarios, Parkas & Down second; control checks passed. Accepted Option A (five types, no sub-splitting of Jackets). The Power BI implementation is the next step.
- **Power BI implementation (2026-10-16):** implemented `product_type` in Power Query, created the 16 garment-type DAX measures, validated Power BI against the Python reference (all matched), built the dashboard page "5 · Garment types" and wrote the Stage 4 output (Jackets, predominantly men's, five example products).

**Stage 4 Status: IN PROGRESS**
