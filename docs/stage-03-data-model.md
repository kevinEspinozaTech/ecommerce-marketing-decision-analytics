# Stage 03 — Data Model & Power BI

**Stage 3 Status: IN PROGRESS** — the frozen snapshot (2026-10-07) was exported and verified, and the Power BI star schema, DAX measures, category decision model and a four-page dashboard have been built on top of it and validated against independent recomputations. Remaining before closing the stage: Kevin's review and approval, and the open items listed under Stage Validation.

## Stage Objective

Build the Power BI data model (star schema at `order_item` grain) and the dashboard that supports the project's category decision, on top of a **frozen, verified snapshot** of TheLook eCommerce rather than live query results.

**[BUSINESS RULE / DECISION]** Data-source strategy ("option C"): a frozen CSV snapshot of `bigquery-public-data.thelook_ecommerce` is the data source for the Power BI model. A separate live BigQuery connection may be built for practice only, never as the source of reported figures. Reason: TheLook is synthetic and dynamic (Stages 1–2), so live queries return different numbers on different days; a frozen snapshot makes every figure in the model reproducible and checkable against a documented reference.

## Technical Context

- **Dataset:** `bigquery-public-data.thelook_ecommerce` (synthetic, dynamic — carried forward from Stages 1–2).
- **Access:** Python (`google-cloud-bigquery`) with Google Application Default Credentials (`gcloud auth application-default login`), running queries in the project's BigQuery Sandbox project. No credentials are stored in the repository; the billing project ID is passed on the command line and not written to any versioned file.
- **New repository artifacts:**
  - `sql/05_snapshot_export.sql` — export queries (one per table).
  - `sql/06_snapshot_reference.sql` — reference KPIs at the snapshot instant.
  - `scripts/export_snapshot.py` — runs the export, the reference query, and all verifications; writes the manifest.
  - `data/raw/` — snapshot CSV files (not versioned) and evidence files (versioned): `manifest_2026-10-07.json` and `category_ranking_reference_2026-10-07.csv`.
- **Power BI (outside the repository):** `Proyecto01_actualizado.pbix` is the working report. It embeds the snapshot data, so it is **never** versioned. A Power BI template (`.pbit`, model and pages without data) was also saved locally; it stays local and is not versioned for now. The four dashboard page screenshots are stored under `powerbi/`.
- **Data source of the model:** the four snapshot CSVs (`order_items`, `inventory_items`, `products`, `users`) — never a live BigQuery connection (option C).
- `sql/01`–`sql/04` and the Stage 2 methodology were **not** modified.

## Snapshot 2026-10-07

### Snapshot instant and method

**[OBSERVED FACT]**

| Item | Value (UTC) |
|---|---|
| Snapshot instant **T** | `2026-10-07 13:27:26` |
| Export run start | `2026-10-07 13:27:36` |
| Export run end | `2026-10-07 13:29:05` |
| Consistency method | BigQuery time travel (`FOR SYSTEM_TIME AS OF T`) on every table |

**[OBSERVED FACT]** Before the export, `FOR SYSTEM_TIME AS OF` was tested and worked on all four source tables (`order_items`, `inventory_items`, `products`, `users`). The fallback plan (one script run with recorded start/end times plus cross-file orphan checks) was therefore not needed; the orphan checks were still run as an additional control.

**[OBSERVED FACT]** BigQuery storage metadata showed all four tables last modified on 2026-10-07 between 03:35:03 and 03:35:20 UTC — before T. `order_items` held 181,070 rows, fewer than the ≈181,703 observed on 2026-09-14 (Stage 1).

**[ANALYTICAL ASSUMPTION]** A falling row count suggests the dataset is periodically **regenerated** rather than only appended to. This is an inference from two observations, not a documented property of TheLook.

**[ANALYTICAL ASSUMPTION]** Time travel on this dataset was used within what was assumed to be BigQuery's default 7-day window (i.e. T is reachable until about 2026-10-14). The dataset's actual configured window was not independently verified.

### Files, rows, and sizes

**[OBSERVED FACT]** Row counts in each CSV match the reference query exactly.

| File | Rows | Reference rows | Size | Duplicate `id` |
|---|---|---|---|---|
| `order_items_2026-10-07.csv` | 181,070 | 181,070 | 16.59 MB | 0 |
| `inventory_items_2026-10-07.csv` | 488,895 | 488,895 | 14.33 MB | 0 |
| `products_2026-10-07.csv` | 29,120 | 29,120 | 2.64 MB | 0 |
| `users_2026-10-07.csv` | 100,000 | 100,000 | 4.49 MB | 0 |

SHA-256 checksums for each file are recorded in `data/raw/manifest_2026-10-07.json` and were independently re-computed with `sha256sum` (matching).

**Format:** UTF-8 CSV, comma separator, header row, decimal point (`.`), timestamps as `YYYY-MM-DD HH:MM:SS` in UTC without offset, rows ordered by `id`. Nulls are empty cells.

### Columns included and excluded

**[BUSINESS RULE / DECISION]** The extracts are **faithful and unjoined**: each CSV mirrors one source table. Joins (e.g. `order_items` → `inventory_items.cost`) are deliberately left to Power Query, so the raw layer stays a plain copy of the source.

| Table | Included | Excluded and why |
|---|---|---|
| `order_items` | All 11 columns: `id`, `order_id`, `user_id`, `product_id`, `inventory_item_id`, `status`, `created_at`, `shipped_at`, `delivered_at`, `returned_at`, `sale_price` | — |
| `inventory_items` | `id`, `product_id`, `cost` | `created_at`, `sold_at`, and the denormalized `product_*` columns: only the COGS source (`cost`) and its keys are needed; product attributes come from `products`. |
| `products` | `id`, `category`, `name`, `brand`, `retail_price`, `department` | `cost` (catalog cost — **not** the COGS source; Stage 2 selected `inventory_items.cost`, and keeping both invites mixing them up), `sku`, `distribution_center_id` (not needed for the category decision). |
| `users` | `id`, `age`, `gender`, `country`, `traffic_source`, `created_at` | **Personal data:** `first_name`, `last_name`, `email`, `street_address`, `postal_code`, `city`, `state`, `latitude`, `longitude`, `user_geom`. |
| `orders` | not exported | `num_of_item` and `user_id` consistency were already validated in Stage 2; order counts are derivable from `order_items.order_id`. |

**[BUSINESS RULE / DECISION]** Personal data is excluded **at the source**, not filtered later. Even though TheLook is synthetic, the project applies the data-minimization principle from Stage 1: keep only what supports the business question. The kept customer fields support segmentation (age, gender, country), acquisition-channel analysis (`traffic_source`), and customer tenure (`created_at`). `state` and `city` were excluded as more granular than the decision requires; `user_geom` (a GEOGRAPHY column found during the schema check, not anticipated in the proposal) was excluded together with latitude/longitude as precise location data.

**[OBSERVED FACT]** Column names were confirmed against `INFORMATION_SCHEMA.COLUMNS` before writing the export queries, not assumed.

### Validations

**[OBSERVED FACT]** All validations below passed on the exported files. They are recorded in the manifest.

- **Headers:** each CSV header matches the approved column list exactly (checked with pandas and independently with `head -1`). `users` contains none of the 10 excluded personal-data columns.
- **Timestamp format:** 0 non-empty timestamp values deviate from `YYYY-MM-DD HH:MM:SS`.
- **Literal null text:** 0 cells contain `None`, `NaT`, `nan`, `NaN`, or `<NA>` in any file — every null is a truly empty cell.
- **Nulls by column:**

  | Column | Nulls | Consistency |
  |---|---|---|
  | `order_items.shipped_at` | 63,778 | = Cancelled (27,558) + Processing (36,220) |
  | `order_items.delivered_at` | 118,220 | = all items not Complete or Returned |
  | `order_items.returned_at` | 163,195 | = all items not Returned |
  | `products.name` | 2 | see Products below |
  | `products.brand` | 24 | — |
  | all other columns | 0 | — |

  The status × empty-date cross-check matched the Stage 2 status/date rules with **zero exceptions**.
- **Duplicates:** 0 duplicate `id` values in any file.
- **Orphans between files:** 0 for each of `order_items.user_id` → `users.id`, `order_items.product_id` → `products.id`, `order_items.inventory_item_id` → `inventory_items.id`, `inventory_items.product_id` → `products.id`.
- **Pandas double check:** the reference KPIs were re-computed from the CSV files with pandas and compared with `sql/06` (tolerance 0.01). All 13 metrics matched with a difference of **0**:

  | Metric | Reference = pandas |
  |---|---|
  | complete_items | 44,975 |
  | future_complete_items | 1,207 |
  | Recognized Revenue | 2,669,599.03 |
  | Recognized COGS | 1,284,340.25 |
  | Gross Profit | 1,385,258.79 |
  | Gross Margin % | 51.89 |
  | Pending order value | 5,432,791.03 |
  | Return-associated value | 1,071,349.32 |
  | Cancelled value | 1,634,399.09 |

  (plus the four row counts above).

**[BUSINESS RULE / DECISION]** `sql/06` reuses `sql/02` Section 6 **unchanged** (Complete only, COGS from `inventory_items.cost`, same INNER JOIN and rounding). The only differences are the read instant (T via time travel) and added columns: row counts, `complete_items`, and `future_complete_items` — the latter with the same definition as `sql/03` Section 1, but anchored to `DATE(T)` instead of `CURRENT_DATE()` so it is reproducible.

**[DATASET LIMITATION]** These figures describe the 2026-10-07 snapshot only. They are not expected to match, and are not reconciled with, the Stage 2 baseline (e.g. Recognized Revenue ≈ 2,654,969.61 on 2026-09-15). Each snapshot is preserved as a distinct dated observation.

### Manifest

`data/raw/manifest_2026-10-07.json` (versioned) is the evidence record for this snapshot: T, run start/end, time-travel test results, per-file columns/rows/size/SHA-256/null counts/duplicate ids/header check/literal-null check, orphan checks, the reference query output, the pandas double check, and library versions. It contains no credentials, no project ID, and no row-level data.

## Category Ranking Reference at T

**[OBSERVED FACT]** `sql/04` Section 8 (Scenario Ranking and Robustness Analysis) was executed at instant T **without modifying `sql/04`**: a temporary copy outside the repository added `FOR SYSTEM_TIME AS OF TIMESTAMP('2026-10-07 13:27:26 UTC')` to each of its 5 table references (all 5 patched). Execution: 2026-10-07 13:46:13 UTC; `CURRENT_DATE()` (UTC) was 2026-10-07 — the same date as T, so `sql/04`'s "before the current month" cut-off (< 2026-10-01) is the same as it would be at T. Output: 26 rows (= 26 categories in `products`), saved as `data/raw/category_ranking_reference_2026-10-07.csv` (versioned — per-category aggregates only, no personal data).

| Category | rank_balanced | rank_profitability | rank_growth_controlled_risk | average_rank | rank_variation | Classification |
|---|---|---|---|---|---|---|
| Outerwear & Coats | 1 | 1 | 1 | 1.00 | 0 | Robust Candidate |
| Active | 3 | 2 | 2 | 2.33 | 1 | Robust Candidate |
| Jeans | 2 | 3 | 6 | 3.67 | 4 | Sensitive / Lower Priority |
| Sweaters | 4 | 4 | 4 | 4.00 | 0 | Robust Candidate |
| Suits & Sport Coats | 5 | 5 | 3 | 4.33 | 2 | Robust Candidate |
| Accessories | 6 | 6 | 5 | 5.67 | 1 | Robust Candidate |
| Sleep & Lounge | 7 | 7 | 7 | 7.00 | 0 | Robust Candidate |
| Intimates | 8 | 10 | 8 | 8.67 | 2 | Robust Candidate |
| Swim | 9 | 8 | 10 | 9.00 | 2 | Robust Candidate |
| Blazers & Jackets | 12 | 9 | 9 | 10.00 | 3 | Robust Candidate |
| Shorts | 10 | 12 | 15 | 12.33 | 5 | Sensitive / Lower Priority |
| Fashion Hoodies & Sweatshirts | 11 | 11 | 17 | 13.00 | 6 | Sensitive / Lower Priority |
| Underwear | 13 | 16 | 12 | 13.67 | 4 | Sensitive / Lower Priority |
| Dresses | 15 | 13 | 14 | 14.00 | 2 | Sensitive / Lower Priority |
| Maternity | 17 | 15 | 11 | 14.33 | 6 | Sensitive / Lower Priority |
| Socks & Hosiery | 18 | 17 | 13 | 16.00 | 5 | Sensitive / Lower Priority |
| Pants | 16 | 14 | 18 | 16.00 | 4 | Sensitive / Lower Priority |
| Tops & Tees | 14 | 19 | 19 | 17.33 | 5 | Sensitive / Lower Priority |
| Skirts | 19 | 18 | 16 | 17.67 | 3 | Sensitive / Lower Priority |
| Plus | 20 | 20 | 21 | 20.33 | 1 | Sensitive / Lower Priority |
| Pants & Capris | 21 | 21 | 22 | 21.33 | 1 | Sensitive / Lower Priority |
| Clothing Sets | 22 | 23 | 20 | 21.67 | 3 | Sensitive / Lower Priority |
| Jumpsuits & Rompers | 23 | 22 | 23 | 22.67 | 1 | Sensitive / Lower Priority |
| Socks | 24 | 24 | 25 | 24.33 | 1 | Sensitive / Lower Priority |
| Leggings | 25 | 25 | 24 | 24.67 | 1 | Sensitive / Lower Priority |
| Suits | 26 | 26 | 26 | 26.00 | 0 | Sensitive / Lower Priority |

**[OBSERVED FACT]** Outerwear & Coats is ranked **#1 in all three scenarios** (average_rank 1.00, rank_variation 0) — the same position it held in the 2026-09-21 snapshot and in the second Stage 2 checkpoint.

### Shortlist comparison vs. 2026-09-21 (Stage 2, third checkpoint)

**[OBSERVED FACT]** Robust Candidates: 9 at T, 9 on 2026-09-21.

| Change | Categories |
|---|---|
| **Kept (6)** | Outerwear & Coats, Active, Sweaters, Accessories, Sleep & Lounge, Swim |
| **Dropped (3)** | Jeans (avg 3.67 but variation 4 > 3), Pants (avg 16.00), Shorts (avg 12.33, variation 5) |
| **Added (3)** | Suits & Sport Coats, Intimates, Blazers & Jackets |

**[OBSERVED FACT]** Blazers & Jackets qualifies exactly on both thresholds (average_rank = 10.00, rank_variation = 3). Jeans has the third-best average rank but is excluded by the variation condition alone.

**[ANALYTICAL ASSUMPTION]** Categories that recur across snapshots (Outerwear & Coats, Active, Sweaters, Accessories, Swim appear in the second checkpoint, the 2026-09-21 snapshot, and this one) are more defensible candidates than those that enter or leave between snapshots. Borderline cases (Blazers & Jackets, Jeans) show that the classification is sensitive to the threshold rule, which is an analytical decision, not a property of the data (Stage 2, limitation 12).

**[DATASET LIMITATION]** As in Stage 2, a Robust Candidate classification is not by itself a recommendation for marketing investment; ad spend, CAC, ROAS, CLV and real return costs remain absent from the dataset.

## Reconciliation Finding: Ranking Scope vs. Financial Baseline

**[OBSERVED FACT]** Verified from the local CSV files (pandas) and the ranking reference file:

| Scope | Complete items | Gross Profit |
|---|---|---|
| Category ranking (`sql/04`): Complete, delivered **before the current month** (< 2026-10-01) | 42,921 | 1,323,637.99 |
| + delivered 2026-10-01 to 2026-10-07 | 847 | 24,862.36 |
| + delivered after 2026-10-07 (future-dated) | 1,207 | 36,758.44 |
| **= Financial baseline (`sql/06` / `sql/02` §6): all Complete** | **44,975** | **1,385,258.79** |

The sum of the ranking file's `sales_volume` and `gross_profit` over 26 categories equals the historical scope exactly. The difference of 2,054 items = 1,207 future deliveries + 847 deliveries in the current (incomplete) month.

**[OBSERVED FACT]** The two scopes are both correct; they answer different questions. `sql/02` §6 measures everything recognized under the Stage 2 rules (including future-dated deliveries generated by the dataset); `sql/04` measures closed historical months only.

**[BUSINESS RULE / DECISION]** The Power BI model exposes the two scopes explicitly with **two families of DAX measures** instead of one ambiguous "Gross Profit":

1. **Baseline** (no suffix: `Complete Items`, `Recognized Revenue`, `Recognized COGS`, `Gross Profit`, `Gross Margin %`) — all Complete items; matches `sql/02` §6 and `sql/06`.
2. **Closed Months** (suffix `(Closed Months)`) — Complete items delivered **before 2026-10-01**; matches `sql/04`. The cut-off is a dedicated measure, `Closed Months Cutoff = DATE(2026, 10, 1)`, i.e. the first day of the snapshot month.

The Closed Months family is the basis of the category decision (dashboard pages 2–4); the Baseline family appears on the Validation page (page 1), where it is checked against the snapshot reference.

**[ANALYTICAL ASSUMPTION]** The cut-off is a fixed date tied to this snapshot, not a dynamic "first day of the current month". That is intentional for a frozen snapshot (reproducible figures), but a future snapshot would require updating `Closed Months Cutoff`.

**[DATASET LIMITATION]** 1,207 Complete items have delivery dates after the snapshot date. They are generated by the dataset (Stage 2, limitation 5) and must not be presented as real historical deliveries.

## Products: Identification and Unnamed Products

**[OBSERVED FACT]** From `products_2026-10-07.csv`:
- 29,120 rows and 29,120 distinct `id` values — **`id` is unique**.
- 27,309 distinct non-empty product names.
- **1,567 names are shared by more than one `id`** (3,376 products in total). Ids per duplicated name: 2 ids → 1,360 names; 3 → 183; 4 → 16; 5 → 7; 8 → 1.
- 1,095 of those duplicated names span more than one category, and 11 span more than one brand.
- **2 products have an empty name:** id **12586** (Intimates, Josie by Natori) and id **24455** (Outerwear & Coats, Tru-Spec).
- They are referenced by **13** `order_items` rows: 12586 → 7 (1 Complete, 4 Processing, 2 Shipped); 24455 → 6 (3 Complete, 2 Shipped, 1 Cancelled).

**[BUSINESS RULE / DECISION]** `products.id` is the only key for `dim_product`. Product name is a descriptive attribute and must never be used as a key or as the sole grouping field — grouping by name would merge different products, in many cases across categories.

**[BUSINESS RULE / DECISION]** The 2 unnamed products are **kept** (4 of their items are Complete and carry recognized revenue). In Power Query, their missing name is to be replaced with a visible label of the form `(unnamed) – id <id>`, so they remain identifiable and are not silently dropped or blank in visuals.

**[DATASET LIMITATION]** 24 products have an empty `brand`. No labeling rule has been decided for them yet.

## Power BI Data Model

**[OBSERVED FACT]** The model is a star schema at `order_item` grain built from the snapshot CSVs. The Data pane lists four tables:

| Table | Role | Notes |
|---|---|---|
| `fact_order_items` | Fact (one row per order item) | Holds the measures. The inventory cost used for COGS (`inventory_items.cost`, the Stage 2 COGS source) is available here, so the model has no separate inventory table. |
| `dim_product` | Dimension | Key: `products.id` (Stage 3 product-key decision). Category is the grouping attribute of the decision model. |
| `dim_customer` | Dimension | Built from `users` (personal data already excluded at source). Renamed from `dim_customers` for naming consistency. |
| `dim_date` | Date dimension | Calculated with DAX and **marked as the date table**. |

**[BUSINESS RULE / DECISION]** Relationships are **one-to-many, single direction**, from each dimension to the fact table. The relationship on the order **creation** date is **inactive**; measures that need it activate it explicitly with `USERELATIONSHIP`. Revenue is recognized at the delivery date (Stage 2 rule), so the delivery-date relationship is the one used by default.

**[DATASET LIMITATION]** The snapshot contains dates after the cut-off (`created_at` up to 2026-10-11 and `delivered_at` up to 2026-10-14 in the loaded data) because TheLook generates future-dated rows (Stage 2, limitation 5). The Closed Months cut-off is what keeps those rows out of the category decision.

## Measures and Cohorts

**[BUSINESS RULE / DECISION]** Two cohorts, carried over from Stage 2 and implemented as DAX measures:

| Cohort | Definition | Used for |
|---|---|---|
| **Financial cohort (Closed Months)** | Status `Complete`, delivered before 2026-10-01 | Gross Profit, Gross Margin %, Sales Volume, the category ranking |
| **Operational cohort** | Items **created** before 2026-10-01 with a final status (`Complete`, `Returned` or `Cancelled`) | Return Rate and Cancellation Rate |

- `Return Rate % = Returned / (Complete + Returned)`
- `Cancellation Rate % = Cancelled / (Complete + Returned + Cancelled)`
- Revenue is recognized only for `Complete` items at the delivery date; COGS comes from `inventory_items.cost`; shipping and return costs are not available (Stage 2).

**[DATASET LIMITATION]** The two cohorts differ (a Complete item can be created before 2026-10-01 and delivered after it), so the Return Rate comes from a different population than Gross Profit. This is the "Cohort Difference" limitation already documented in Stage 2 and is stated on dashboard page 1.

Measure groups in `fact_order_items`:

| Group | Measures |
|---|---|
| Baseline | `Complete Items`, `Recognized Revenue`, `Recognized COGS`, `Gross Profit`, `Gross Margin %` |
| Closed Months | `Closed Months Cutoff`, `Complete Items (Closed Months)`, `Recognized Revenue (Closed Months)`, `Recognized COGS (Closed Months)`, `Gross Profit (Closed Months)`, `Gross Margin % (Closed Months)` |
| Operational cohort | `Complete Items (Ops Cohort)`, `Returned Items (Ops Cohort)`, `Cancelled Items (Ops Cohort)`, `Return Rate %`, `Cancellation Rate %` |
| Scores (0–100) | `Score Gross Profit`, `Score Gross Margin`, `Score Sales Volume`, `Score Return Rate`, `Score Balanced`, `Score Profitability`, `Score Growth Controlled Risk` |
| Ranks | `Rank Balanced`, `Rank Profitability`, `Rank Growth Controlled Risk`, `Average Rank`, `Rank Variation`, `Robustness Class` |
| Dashboard | `Top Category`, `Gross Profit (Top Category)`, `Gross Margin % (Top Category)`, `Sales Volume (Top Category)`, `Return Rate % (Top Category)`, `Bar Color`, `Row Font Color` |

Dashboard measures (the winner is computed, not typed in):

```dax
Top Category =
VAR TopTable =
    TOPN (
        1,
        ALL ( dim_product[category] ),
        [Average Rank], ASC,
        [Gross Profit (Closed Months)], DESC
    )
RETURN
    MAXX ( TopTable, dim_product[category] )

Gross Profit (Top Category) =
VAR Cat = [Top Category]
RETURN
    CALCULATE ( [Gross Profit (Closed Months)], dim_product[category] = Cat )

Bar Color =
IF ( SELECTEDVALUE ( dim_product[category] ) = [Top Category], "#9A7B4F", "#94A3B8" )

Row Font Color =
VAR Cat = SELECTEDVALUE ( dim_product[category] )
RETURN
    SWITCH (
        TRUE (),
        Cat = [Top Category], "#9A7B4F",
        [Robustness Class] = "Sensitive / Lower Priority", "#6B7280",
        "#1F2937"
    )
```

**[BUSINESS RULE / DECISION]** The recommended category is the one with the lowest `Average Rank`; ties are broken by the highest `Gross Profit (Closed Months)`. The other `(Top Category)` measures follow the same pattern as `Gross Profit (Top Category)`, each wrapping its base measure in `CALCULATE` with the category fixed through a variable (a boolean filter predicate cannot reference a measure directly).

## Category Decision Model in Power BI

**[BUSINESS RULE / DECISION]** The Stage 2 model is reimplemented in DAX and evaluated per category:

- **Criteria:** Gross Profit (higher is better), Gross Margin % (higher), Sales Volume (higher), Return Rate % (lower is better, so its score is inverted).
- **Scoring:** Min–Max normalization to 0–100 across the 26 categories (min and max taken over all categories with `ALL` on the category column).
- **Scenarios** (weights in the order Gross Profit / Gross Margin / Sales Volume / Return Rate):

  | Scenario | Weights |
  |---|---|
  | Balanced | 25 / 25 / 25 / 25 |
  | Profitability | 30 / 30 / 20 / 20 |
  | Growth + Controlled Risk | 20 / 30 / 20 / 30 |

- **Robustness:** `Average Rank` = mean of the three scenario ranks; `Rank Variation` = best-to-worst rank gap. A category is a **Robust Candidate** when `Average Rank ≤ 10` **and** `Rank Variation ≤ 3`; otherwise it is classified **Sensitive / Lower Priority**.

**[OBSERVED FACT]** Result in Power BI: **Outerwear & Coats** is ranked #1 in all three scenarios (Average Rank 1.00, Rank Variation 0). Closed Months figures for the category: Gross Profit $174,730.35, Gross Margin 55.64%, Sales Volume 2,159 items, Return Rate 27.32%. Nine categories are Robust Candidates; the same nine as in `category_ranking_reference_2026-10-07.csv`. Jeans (Average Rank 3.67, Rank Variation 4) and Shorts (12.33 / 5) are examples of Sensitive categories; Blazers & Jackets (10.00 / 3) qualifies exactly on both thresholds.

**[ANALYTICAL ASSUMPTION]** The weights and the two thresholds (10 and 3) are analytical choices from Stage 2, not properties of the data. The Rank Variation chart on dashboard page 4 makes this visible by plotting the threshold.

**[BUSINESS RULE / DECISION]** Scope of this stage: the model chooses the winning **category**. Identifying the top products **inside** that category (same decision logic plus each product's contribution to the category's gross profit, with price tier used only descriptively) belongs to the next stage.

## Dashboard (Power BI, 4 pages)

**[OBSERVED FACT]** All text is in English, consistent with the repository. Canvas: 16:9, 1920 × 1080.

| Page | Title | Content |
|---|---|---|
| 1 | Model validation · Power BI vs TheLook snapshot (2026-10-07) | 15 KPI cards in three rows (A Baseline, B Closed months, C Operational cohort), a short validation note per row, a Recognized Revenue by Year chart and a "How to read this page" box. |
| 2 | Executive summary · Which category should we invest in first? | Hero card with the recommended category (computed by `Top Category`), four KPI cards for that category, a Bottom-10-by-Average-Rank bar chart with the winner highlighted, and a "Why Outerwear & Coats?" explanation. |
| 3 | Category decision · How the 26 categories compare | A 26-row table: Gross Profit, Gross Margin %, Complete Items, Return Rate %, the three scenario ranks, Average Rank, Rank Variation and Robustness Class, sorted by Average Rank, plus a "How the ranking works" box. The Total row is switched **off** because summing or averaging ranks is meaningless. |
| 4 | Robustness & limitations · How far can we trust this result? | Rank Variation of the top 10 categories (Top N filter by Average Rank) with a constant line at the threshold (3), a "Dataset limitations" box and a "Bottom line" box. |

**[BUSINESS RULE / DECISION]** Design rules applied to all pages: off-white page background; white cards; one accent colour (bronze `#9A7B4F`) reserved for the winning category and the authorship mark; neutral slate for all other bars; secondary grey for de-emphasized rows; direct data labels instead of axes where possible; a `K | E` signature and a footnote on every page stating that the data is synthetic and that margin excludes shipping and return costs.

**[BUSINESS RULE / DECISION]** On page 1 the chart is set to **not** filter the KPI cards (Edit interactions → None), so the validation figures always show the totals.

**[DATASET LIMITATION]** The dashboard footnote and page 4 repeat the dataset limitations: synthetic data; the source is regenerated daily (so the analysis uses a frozen snapshot); future-dated rows exist; margin is gross profit only (no shipping or return costs); and min–max scores are relative to the 26 categories, not absolute performance.

## Validation of the Power BI Model

**[OBSERVED FACT]** On 2026-10-15 every figure shown on the dashboard was compared with an independent recomputation from the snapshot CSVs (pandas): `order_items` joined to `inventory_items.cost` and `products.category`. No difference was found.

| Check | Power BI | Independent recomputation |
|---|---|---|
| Baseline — Complete items | 44,975 | 44,975 |
| Baseline — Recognized Revenue | $2,669,599.03 | $2,669,599.03 |
| Baseline — Recognized COGS | $1,284,340.25 | $1,284,340.25 |
| Baseline — Gross Profit | $1,385,258.79 | $1,385,258.79 (= manifest/`sql/06` reference) |
| Baseline — Gross Margin % | 51.89% | 51.89% |
| Closed Months — Complete items | 42,921 | 42,921 |
| Closed Months — Recognized Revenue | $2,549,840.51 | $2,549,840.51 |
| Closed Months — Recognized COGS | $1,226,202.53 | $1,226,202.53 |
| Closed Months — Gross Profit | $1,323,637.99 | $1,323,637.99 |
| Closed Months — Gross Margin % | 51.91% | 51.91% |
| Ops cohort — Complete / Returned / Cancelled | 43,160 / 17,196 / 26,418 | 43,160 / 17,196 / 26,418 |
| Return Rate % / Cancellation Rate % | 28.49% / 30.44% | 28.49% / 30.44% |

**[OBSERVED FACT]** Rounding note: Closed Months revenue minus COGS computed on the two rounded figures gives 1,323,637.98, while the unrounded gross profit is 1,323,637.987, which rounds to the 1,323,637.99 shown. Both are correct; the difference is cent rounding only.

**[OBSERVED FACT]** Category table (page 3): all 26 rows were compared with `category_ranking_reference_2026-10-07.csv` on Gross Profit, Gross Margin %, Sales Volume, Return Rate %, the three scenario ranks, Average Rank, Rank Variation and Robustness Class — **0 mismatches** over 26 categories and 10 fields. Method: the dashboard values were read from the rendered table and compared programmatically with the reference file. Gross Profit, Gross Margin %, Sales Volume and Return Rate % per category were also recomputed from the CSVs and match the reference. The 26 categories sum to 42,921 items and $1,323,637.99 of gross profit, equal to the Closed Months totals.

**[DATASET LIMITATION]** These checks prove that the model reproduces the Stage 2 / snapshot logic exactly. They do not prove that the category is the best marketing investment: ad spend, CAC, ROAS, CLV and real return costs remain absent from the dataset (see Stage 2).

## Decisions Made

- Frozen snapshot as the Power BI data source; live BigQuery only for practice (option C).
- Time travel to a single instant T for all tables; script refuses to overwrite existing snapshot files without `--overwrite`.
- Faithful, unjoined extracts; joins happen in Power Query.
- Column selection and personal-data exclusion as documented above; `orders` not exported.
- CSV snapshots not versioned (unverified redistribution licensing, size); manifests and category ranking references versioned as evidence (`data/raw/*.csv` ignored, with an exception for `category_ranking_reference_*.csv`).
- `sql/06` reuses `sql/02` §6 logic unchanged; `future_complete_items` anchored to `DATE(T)`.
- `products.id` as the product key; unnamed products labeled, not removed.
- Two named measure families (Baseline vs. Closed Months) with a fixed cut-off `DATE(2026, 10, 1)`; Closed Months is the basis of the category decision.
- Star schema with four tables (`fact_order_items`, `dim_product`, `dim_customer`, `dim_date`); one-to-many single-direction relationships; inactive creation-date relationship activated with `USERELATIONSHIP`; `dim_date` built in DAX and marked as the date table.
- The Stage 2 decision model is implemented in DAX (scores, three scenarios, ranks, robustness class); the reference CSV is used only to validate it, never as a source for the dashboard.
- Winner = lowest Average Rank, ties broken by highest Closed Months gross profit; the winner is computed by a measure, not typed.
- Dashboard text in English; four pages on a 1920 × 1080 canvas; one accent colour reserved for the winner; `K | E` authorship mark and a data-limitation footnote on every page.
- Table Total row switched off on page 3; page 1 chart does not cross-filter the KPI cards.
- `.pbix` stays outside the repository because it embeds the data.
- Dashboard page screenshots versioned under `powerbi/`; the `.pbit` template is not versioned for now.
- *Pending:* naming consistency (`dim_customer` singular vs. other table names; `Product_name` casing).

## Concepts Learned

- **BigQuery time travel** (`FOR SYSTEM_TIME AS OF`) as a way to read several tables at one consistent instant.
- **Snapshot reproducibility:** fixing the instant, recording checksums, and re-computing reference KPIs from the exported files (a double check) to prove the files are faithful.
- **Data minimization at the source** versus filtering later.
- **Natural key vs. descriptive attribute:** a product name is not an identifier.
- **Measure scope:** the same KPI name (Gross Profit) can legitimately have two scopes; the model should name them explicitly instead of hiding the difference.
- **Star schema in Power BI:** fact vs. dimension tables, one-to-many single-direction relationships, a marked date table, and an inactive relationship activated per measure with `USERELATIONSHIP`.
- **Filter context and context transition:** `CALCULATE` with a category held in a variable, `ALL` on a column to compute min/max across all categories, and why a boolean filter predicate cannot reference a measure.
- **Ranking in DAX:** `RANKX`, `TOPN` + `MAXX` to pick a winner with a tie-break, `SWITCH ( TRUE (), … )` for multi-case logic.
- **Min–Max normalization** and weighted scenarios implemented as measures.
- **Conditional formatting by field value** (a measure returning a colour code) and why it is applied per column.
- **Report design:** canvas size, Edit interactions (Filter / Highlight / None), the Analytics pane (constant line), Top N visual filters, Align / Distribute, and Power BI templates (`.pbit`).

## Problems Encountered

- No local BigQuery access at the start (no `gcloud`, no credentials).
- Windows Smart App Control blocked a pandas DLL on its first load.
- The authenticated session reported no "quota project".
- The first proposal could not verify column names without database access.
- The ranking's Gross Profit did not match the snapshot baseline.
- Timestamp columns carried a time component, which does not match a Date table at day grain.
- The layout was first planned on a 1280 × 720 grid, but the canvas is 1920 × 1080.
- A boolean filter inside `CALCULATE` cannot call a measure (needed for the "Top Category" measures).
- The dashboard was first written in Spanish, while the repository is in English.
- Several formatting side-effects: a Top N filter lost after changing a chart's fields; a header click that silently changed the table sort; a Total row that showed meaningless "1 / 1 / 1 / Robust Candidate"; card labels truncated at fixed width; a constant-line label whose font size cannot be changed.

## Solutions

- Installed Google Cloud CLI; the user ran `gcloud auth application-default login` personally; the script uses Application Default Credentials and never reads or prints them.
- The Smart App Control block was transient (first-load reputation check); a retry loaded pandas normally. No security setting was changed.
- The quota-project warning was harmless because every query passes the project explicitly.
- Columns were verified against `INFORMATION_SCHEMA.COLUMNS` before writing `sql/05`.
- The Gross Profit gap was fully reconciled (847 current-month + 1,207 future-dated deliveries) — see Reconciliation Finding.
- Date handling: day-grain dates for the relationship to `dim_date`.
- Grid recalculated for 1920 × 1080 (60 px margins, 1,800 px usable width); card size and position set numerically and aligned with Align / Distribute.
- Winner and its KPIs computed with `VAR` + `CALCULATE` instead of a predicate on a measure.
- All dashboard text moved to English before building the remaining pages.
- Top N filter re-applied; table re-sorted by Average Rank; Total row switched off; card label size reduced; the threshold explained in the chart subtitle instead of the constant-line label.

## PL-300 Connection

- **Prepare the data:** documented a reproducible data source; selected columns at the source; defined null-handling rules (labeling unnamed products); noted that the CSVs use a decimal point, so an import under a regional setting with a decimal comma needs an explicit en-US locale. The model's figures reconcile with the independent recomputation to the cent, so no numeric import problem was observed.
- **Model the data:** designed a star schema at `order_item` grain with `products.id` as the product key and a separate Date table (`dim_date`); the multiple dates on the fact table (`created_at`, `delivered_at`) were handled with an active/inactive relationship design.
- **DAX:** the baseline vs. historical cut-off measures are a direct example of filter-context-dependent measure design.
- **Model the data (built):** star schema, marked date table, relationship cardinality and direction, an inactive relationship with `USERELATIONSHIP`.
- **DAX (built):** `CALCULATE`, `ALL`, `VAR`, `TOPN`, `MAXX`, `RANKX`, `SELECTEDVALUE`, `SWITCH ( TRUE (), … )`, context transition, iterators.
- **Visualize and analyze (built):** card (new), clustered bar, table with conditional formatting, Top N filter, Analytics-pane constant line, Edit interactions, canvas settings, Align / Distribute.
- **Deploy and maintain:** `.pbit` template; the `.pbix` is kept out of version control because it embeds data.

## Skills Demonstrated

- BigQuery: `INFORMATION_SCHEMA`, `__TABLES__` metadata, dry runs, query parameters, time travel.
- Python: reproducible export script with safety checks (no overwrite, header validation, literal-null detection, checksums) and a pandas double check.
- Data governance: personal-data minimization, credential hygiene, licensing-aware versioning decisions.
- Analytical rigor: reconciling two legitimately different KPI scopes to the exact item and cent.
- Power BI: data modeling, DAX measure design, a decision model implemented as measures, dashboard design and storytelling.
- Validation: independent recomputation of every dashboard figure from the source files, to the cent and to the row.
- Communication: a dashboard that states its methodology, its limitations and its conclusion on the page itself.

## Portfolio Evidence

- `sql/05_snapshot_export.sql`, `sql/06_snapshot_reference.sql`, `scripts/export_snapshot.py`.
- `data/raw/manifest_2026-10-07.json` — snapshot evidence record.
- `data/raw/category_ranking_reference_2026-10-07.csv` — `sql/04` Section 8 output at T.
- Power BI report `Proyecto01_actualizado.pbix` (outside the repository) — four pages: Validation, Executive summary, Category decision, Robustness & limitations.
- Validation of the Power BI figures against the snapshot (see **Validation of the Power BI Model**).
- Dashboard page screenshots:
  - `powerbi/01-model-validation.png` — validation of the Power BI figures against the snapshot reference.
  - `powerbi/02-executive-summary.png` — executive summary with the recommended category.
  - `powerbi/03-category-decision.png` — category decision table comparing the 26 categories.
  - `powerbi/04-robustness-limitations.png` — robustness of the ranking and dataset limitations.

## Stage Validation

**Validated so far:** the Power BI model reproduces the snapshot reference and the Stage 2 category ranking exactly (see **Validation of the Power BI Model**).

**Remaining before Stage 3 can be closed (Kevin's decision):**
- Review and approval of the four-page dashboard.
- Resolve the naming-consistency item (`dim_customer`, `Product_name` casing).
- Decide whether the 24 products with an empty `brand` need a labeling rule (open since the snapshot work).

## Stage Log

- **Snapshot preparation — proposal (2026-10-07):** reviewed repository state; confirmed no local BigQuery access; proposed tables/columns, personal-data exclusions, product-identification check, reference query, file naming/format/location, versioning approach, and risks. No files created at this step.
- **Snapshot preparation — execution (2026-10-07):** installed Google Cloud CLI and the BigQuery Python client; authenticated via Application Default Credentials; verified schemas; tested time travel (working on all 4 tables); measured table sizes and dry-run bytes (~43.6 MB processed); wrote `sql/05`, `sql/06`, and `scripts/export_snapshot.py`; exported the snapshot at T = 2026-10-07 13:27:26 UTC; all validations and the pandas double check passed. `.gitignore` updated (`data/raw/*.csv` ignored, manifests versioned) and `README.md` updated to reflect `data/` and `scripts/`.
- **Reference results at T (2026-10-07):** ran `sql/04` Section 8 at T through a temporary, unversioned copy (`sql/04` unchanged); saved the 26-category ranking reference; compared the Robust Candidate shortlist with 2026-09-21; analyzed product-name uniqueness and unnamed products from the local CSVs; reconciled the ranking's scope with the financial baseline; added a `.gitignore` exception so category ranking references are versioned.
- **Power BI model, measures and dashboard (through 2026-10-15):** built the star schema and date table from the snapshot CSVs; implemented the Baseline and Closed Months measure families, the operational-cohort rates and the Stage 2 category decision model in DAX; built a four-page dashboard in English on a 1920 × 1080 canvas (validation, executive summary, category decision, robustness and limitations); removed the temporary test measures; saved a `.pbit` template locally. Recomputed every dashboard figure independently from the snapshot CSVs: no differences, including 0 mismatches over the 26-category table.
- **Dashboard screenshots (2026-10-15):** exported the dashboard to PDF and converted it to 4 PNG images under `powerbi/` (one per page); the PDF itself is not versioned.

**Stage 3 Status: IN PROGRESS**
