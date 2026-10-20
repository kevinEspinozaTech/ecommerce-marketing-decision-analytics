# Stage 07 — Portfolio Finalization

**Stage 7 Status: COMPLETE (2026-10-20)** — the repository audit, the README front page, the n8n workflow captures, the conclusion, the reuse guide, the MIT license, the final review and the polish are done, and the project owner approved the closure.

## Purpose and Scope

Finish the first portfolio project so that a first-time visitor can understand it quickly and a technical reader can check it:

- the README as a layered front page: a two-minute layer on top, technical detail below;
- a concluding narrative (short in the README, longer here);
- an honest guide to adapting the method to another business.

- **[BUSINESS RULE / DECISION]** Out of scope: new analysis, new automation, Gemini execution, a separate case study, LinkedIn or CV material, GIFs and publishing the dashboard.

## Decisions Made

Kevin's decisions, 2026-10-20:

- **[BUSINESS RULE / DECISION]** The README is the front page for both recruiters and technical interviewers.
- **[BUSINESS RULE / DECISION]** The dashboard is shown with screenshots only (`powerbi/`); the Power BI file stays outside the repository.
- **[BUSINESS RULE / DECISION]** The n8n workflow is shown with two canvas captures (`n8n/stage-06-workflow-canvas-1.png`, `n8n/stage-06-workflow-canvas-2.png`).
- **[BUSINESS RULE / DECISION]** First-person, sober voice.
- **[BUSINESS RULE / DECISION]** The conclusion is short in the README; the longer retrospective is in this document.
- **[BUSINESS RULE / DECISION]** Outdated README sections get text-only cleanups; nothing is deleted or renamed.
- **[BUSINESS RULE / DECISION]** License: MIT, LICENSE file added (2026-10-20). The TheLook dataset and data derived from it are not covered by it.
- **[BUSINESS RULE / DECISION]** The reuse claim is worded as "reusable as a method, not as a configurable product", after a read-only audit of where the weights, mappings and rules live.

## Audit Findings

A read-only audit of the repository from a first-time visitor's point of view was run on 2026-10-19, before the README changes of 2026-10-20.

| Finding | What was done |
|---|---|
| **[OBSERVED FACT]** The README did not state the result: the category appeared only in brackets in a table row, and the winning garment type (Jackets) and key figures were absent. | Added a front page with a figures table (each figure linked to its stage doc and labeled synthetic). |
| **[OBSERVED FACT]** The README framed the repository as an n8n learning repo ("core tool of this repository"; empty `workflows/` and `templates/` described as holding workflows). | Technologies rewritten to the real stack; `workflows/` and `templates/` described as empty placeholders, pointing to `n8n/`. |
| **[OBSERVED FACT]** The automation claim exceeded the evidence: the README said the project "ends with automatically generated campaign content", but Stage 6 is a dry run. | Sentence reworded; an "Honest Limits" section and the dry-run caption on the canvas images were added. |
| **[OBSERVED FACT]** No LICENSE file. | MIT License added (`LICENSE`), with a README "License" section. |
| **[OBSERVED FACT]** Leftovers: a SQL Server mention in the Security section, "(complete)" markers only on some stage files, section names in "Development Approach" that did not match the docs, no image of the n8n workflow. | Text corrected in the README; two canvas captures added. |
| **[OBSERVED FACT]** Other leftovers: `.env.example` holds a YouTube key placeholder unrelated to this project; the Stage 4 doc keeps the file name `stage-04-star-products.md`. | Not changed in this step. |

## Retrospective

*In short: I started with a question a business could act on, tested whether my answer held up, and built the automation only as far as the evidence justified.*

**The question.** The case was a fictional e-commerce company whose sales were not growing as expected and whose marketing budget was limited. That makes "what sells most?" the wrong question: spending everywhere was not an option, and a wrong choice would waste a scarce budget. I wanted an answer that did not depend on a single metric. *Sources: stage-01:13.*

**Evidence before ranking.** I checked the data before trusting it: referential integrity, status and date consistency. Then I fixed the rules that every later number depends on: COGS from `inventory_items.cost`, and revenue recognized on the delivery date for Complete sales. I also documented that the financial and return metrics use different cohorts, because Cancelled items have no delivery date. Gross profit, margin, volume and return rate sit on different scales, so I normalized them with Min-Max, ranked the categories under three weighting scenarios and required a candidate to stay near the top in all of them. *Sources: stage-02:99, 133, 311, 364, 397, 430.*

**The result, and the approach that failed.** Outerwear & Coats ranked first in all three scenarios, with average rank 1.00 and rank variation 0 (synthetic data). The natural next step was to rank individual products inside it, and that did not work well: samples were small and 156 of the 273 eligible products had a 0% return rate, so that criterion barely discriminated. I changed the question to garment types instead of forcing the product ranking. *Sources: stage-03:154, stage-04:42, 442.*

**What the final answer is, and what it is not.** Jackets ranked first in all three scenarios: 1,150 items, 92,177.39 gross profit (dataset currency units), 55.79% margin and a 27.46% return rate. I recorded the caveats next to the result: margins differ by less than one percentage point across types, Jackets win largely because they are the most numerous type (an assumption), and about 69% of the items sold are labeled men's, which I use only as a descriptive label. I present Jackets as the most defensible bet in this dataset, not as a guaranteed winner. *Sources: stage-04:94, 118, 119, 121.*

**From decision to action.** The creative brief turns the decision into inputs an automation can use, and every creative choice in it is labeled an assumption, not a performance claim. The n8n workflow validates the brief, builds the prompt from `config/creative_rules.json`, waits for a person to approve or reject, and saves only approved output. Human review is mandatory. I made no paid API call: the Gemini node is configured but deactivated, so the workflow runs as a dry run. *Sources: stage-05; stage-06:32.*

**Problems and what they taught me.** TheLook's product dimension has no color column and no images, so the brief takes color from a reference image and the demo needed a photo I have the right to use. That is a data limit I designed around. The other two problems were about defaults and unhappy paths: the review dropdown defaulted to "Approve", which would have allowed an accidental approval, so I cleared it; and a file-path expression was not evaluated when a backslash came directly before `{{`, and forward slashes fixed it, although I could not confirm the cause in the documentation. I now test the unhappy path and the defaults, not only the happy path. *Sources: stage-05:24, stage-06:127, 128.*

**What I would do differently, and next.** I would put the scoring weights and thresholds in one parameter table from the start, instead of typing them into each query and measure, and add a staging layer so the SQL does not depend on TheLook names. Both are under "Future Improvements", and the reuse table shows exactly where. The real test of the method is to run it on a second dataset; with real data I would also enable generation behind a spend cap and measure how the approved ads perform.

## Adapting This to Another Business

The method is **reusable as a method, not as a configurable product**: the creative layer is driven by configuration, but the data mapping, scoring weights and classification rules are written into the SQL, Python, DAX and Power Query. The table lists where.

| Layer | What to adapt | Where (file:line) | How | Type |
|---|---|---|---|---|
| Data source | Dataset path `bigquery-public-data.thelook_ecommerce.<table>` | Every `FROM`/`JOIN` in `sql/` (e.g. `sql/04_category_performance_analysis.sql:116, 118, 121`; 88 occurrences across `sql/01`–`06`) | Replace with your own dataset, or a staging view | Edit code |
| Data mapping | Tables and columns used: `order_items` (`id`, `order_id`, `user_id`, `product_id`, `inventory_item_id`, `status`, `created_at`, `shipped_at`, `delivered_at`, `returned_at`, `sale_price`); `inventory_items` (`id`, `product_id`, `cost`); `products` (`id`, `category`, `name`, `brand`, `retail_price`, `department`); `orders` (`num_of_item`, in `sql/01` only); `users` (`id`, `age`, `gender`, `country`, `traffic_source`, `created_at`) | `sql/05_snapshot_export.sql:60–120`; `sql/01_data_quality_validation.sql:54, 108, 129–131` | Map your data to the same entities: order items with status, price and dates; unit cost; products with category | Edit code |
| Snapshot export | Export and verification script | `scripts/export_snapshot.py:35–36` (reads `sql/05` and `sql/06`) | Point it at your project and adjusted queries | Edit code |
| Status vocabulary | Item-level statuses `'Complete'`, `'Returned'`, `'Cancelled'`; no separate returns table | `sql/04:124, 155, 157, 159, 183`; `scripts/product_ranking_reference.py:45` | Map your order and return statuses to these outcomes | Edit code |
| Cost and revenue rules | COGS from `inventory_items.cost` joined by `inventory_item_id`; revenue recognized on `delivered_at` | `sql/04:121–122, 126` | Replace with your cost source and recognition date | Edit code |
| Cut-off date | SQL: current month (`DATE_TRUNC(CURRENT_DATE(), MONTH)`); Python default `2026-10-01`; DAX fixed `DATE(2026, 10, 1)` | `sql/04:126, 182`; `scripts/product_ranking_reference.py:32`; `docs/stage-03-data-model.md:190, 363` | Set to your own closed period | Edit code (Python: `--cutoff` argument) |
| Scoring weights and scenarios | **[ANALYTICAL ASSUMPTION]** Weights 25/25/25/25, 30/30/20/20, 20/30/20/30 | `sql/04:630–633, 802–823, 957–978` (28 typed-in weight values in 7 blocks); `scripts/product_ranking_reference.py:48–52` (`SCENARIOS`); DAX: `docs/stage-03-data-model.md:296–302`, `docs/stage-04-star-products.md:220–235` | Change in every place, consistently | Edit code |
| Robustness thresholds | **[ANALYTICAL ASSUMPTION]** `average_rank <= 10` and `rank_variation <= 3` | `sql/04:1038–1039`; DAX: `docs/stage-03-data-model.md:304, 308` | Adjust to the number of categories you rank | Edit code |
| Category scope | Category comes from the data in SQL, but "Outerwear & Coats" is typed in elsewhere | `scripts/product_ranking_reference.py:31` (`DEFAULT_CATEGORY`, overridable with `--category`, `:198`); Power Query filter `docs/stage-04-star-products.md:149` | Pass your category, edit the Power Query filter | Python: argument; Power Query: edit code |
| Garment-type rules | Ordered keyword rules written for clothing | `scripts/product_type_classification.py:44–48` (`EXCLUSION_PHRASES`), `:55–70` (`RULES`); Power Query: `docs/stage-04-star-products.md:146–156` | Write new rules for your product types, in both places | Edit code |
| Departments | "Men" / "Women" | `scripts/type_ranking_reference.py:36`; n8n "Validate brief" Code node, line 19; `config/creative_rules.json:28` (`department_model`) | Edit the code lists; edit the config entry | Edit code + configuration |
| Creative rules | Seasons, formats, approaches, restrictions, color harmony | `config/creative_rules.json:5` (`seasons`), `:28`, `:33` (`formats`), `:42` (`restrictions`), `:126` (`creative_approaches`), `:175` (`color_harmony`) | Edit values; the workflow reads the file at run time | Configuration |
| Brief | Example brief | `config/brief_example.json`; the workflow's "Brief" node holds the brief as pasted JSON (`n8n/stage-06-ad-image-v1-demo.json:18`), not loaded from the file | Paste your brief into the "Brief" node | Configuration (manual paste) |
| n8n vocabulary | Hard-coded in Code nodes: modes `['demo','production']` ("Validate brief" L5); `'illustrative'` (L39); `brief.mode + '_mode'` ("Build prompt" L21); process-only regex (L32); approach names (L37–38); `'complementary'` (L54); `'Approve'`/`'Reject'` ("Apply review decision" L6, L15); default extension `'jpg'` and `'ad_'` prefix ("Prepare output files" L10, L12) | `n8n/stage-06-ad-image-v1-demo.json` (line numbers inside each node's code) | Edit the Code nodes if your vocabulary differs | Edit code |
| Image provider | Single node "Generate ad image (Gemini)" | `n8n/stage-06-ad-image-v1-demo.json:176`; output field `generated_image` at `:166` | Replace the node; the replacement must write the `generated_image` binary field ("Mark generation status" L4); also edit `provider` and `model` strings ("Mark generation status" L15–16) and the prompt wording in "Build prompt" | Edit code |
| Power BI | Model shape is generic (`fact_order_items`, `dim_product`, `dim_customer`, `dim_date`), but it is loaded from the TheLook CSVs, keeps TheLook column names and has a fixed Closed Months cut-off | `docs/stage-03-data-model.md:21, 208, 220–223, 190, 363` | Reload from your data, remap columns, update the cut-off measure | Edit model |

### Minimum steps to try it on another business

1. Map your data to the same entities (order items with status, price and dates; unit cost; products with category) and replace the dataset path in `sql/`.
2. Map your statuses to Complete / Returned / Cancelled and set your cost source and revenue recognition date.
3. Run the validation queries (`sql/01`–`03`) and fix any data issue before ranking.
4. Decide your scenario weights and robustness thresholds, and change them consistently in `sql/04`, `SCENARIOS` and the DAX measures.
5. Rank the categories (`sql/04`), then write classification rules for the product types inside the winning category.
6. Edit `config/creative_rules.json` (departments, seasons, formats, restrictions) and paste a brief into the n8n "Brief" node.
7. Run the workflow in dry-run mode first and test the Reject and invalid-brief paths before enabling any provider.

## Future Improvements (not done)

- **[BUSINESS RULE / DECISION]** None of the following has been done:
  - centralize the scoring weights and thresholds in one configuration file or parameter table;
  - introduce a data-mapping layer (a staging view) so the SQL does not depend on TheLook names;
  - read the image provider and model name from configuration;
  - load the brief from `config/brief_example.json` instead of pasting it into the "Brief" node;
  - run the method on a second dataset.

## Pending

- No pending items, except one post-publish check: after pushing, view the Mermaid chart and the two n8n images on GitHub.

## Stage Log

- **Portfolio finalization, first pass (2026-10-20):** ran a read-only first-visitor audit of the repository; rebuilt the top of the README as a front page (figures table, flow diagram, skills table, honest limits) and cleaned outdated README text; added two n8n canvas captures; ran a read-only reusability audit; added the conclusion to the README and wrote this document with the reuse table.
- **License (2026-10-20):** added the MIT License (`LICENSE`, "Copyright (c) 2026 Kevin Espinoza") and a "License" section in the README stating that the TheLook dataset and derived data are not covered by it.
- **Closure (2026-10-20):** the final read-only repository review found no blockers. Polish applied: American spelling in this document and the exact Stage 6 row title in the README. Optional items deliberately left unchanged: the `.env.example` placeholder, the Stage 4 file name and the empty `docs/.gitkeep`. Closure approved by the project owner.

**Stage 7 Status: COMPLETE (2026-10-20)**
