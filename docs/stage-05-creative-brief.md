# Stage 05 — Creative Brief

**Stage 5 Status: COMPLETE (2026-10-17, extended 2026-10-17)** — the brief specification, the creative rules (`config/creative_rules.json`) and one example brief (`config/brief_example.json`) are done (2026-10-17).

## Stage Objective

Define the creative brief that connects the Stage 4 result (garment type **Jackets**) to the Stage 6 n8n automation. The brief states what the automation receives and which rules it must follow.

**[BUSINESS RULE / DECISION]** Stage 5 is a specification only: no code, no image generation, no publication and no performance measurement.

## Technical Context

- **Input:** the Stage 4 output — see `docs/stage-04-star-products.md`.
  - **[OBSERVED FACT]** Winning garment type: Jackets, first in all three scenarios.
  - **[OBSERVED FACT]** Department label: predominantly men's (69.22% of items sold are men's, 30.78% women's).
  - **[OBSERVED FACT]** Example products: `data/raw/type_ranking_examples_2026-10-07.csv`.
- **Output:** **[BUSINESS RULE / DECISION]** a brief per ad, consumed by the Stage 6 n8n automation.
- **Configuration files:**
  - `config/creative_rules.json` — seasons, department model, formats, restrictions, creative approaches, default approach by format, color harmony, AIDA note and sources.
  - `config/brief_example.json` — one example brief in demo mode.

**[DATASET LIMITATION]** TheLook is synthetic. All figures describe this dataset only, never a real company.

**[DATASET LIMITATION]** `dim_product` has no color column and no product images. Garment color must come from a reference image or, in demo mode without a usable image, from manual input.

## Decisions Made

Kevin's decisions, 2026-10-17:

- **[BUSINESS RULE / DECISION]** Stage 5 is a specification only. Code, image generation, publication and performance measurement are out of scope.
- **[BUSINESS RULE / DECISION]** The brief has two modes: production and demo (see "Brief Specification").
- **[BUSINESS RULE / DECISION]** In production mode, a reference image of the real product is required, and the automation must not alter or invent the product.
- **[BUSINESS RULE / DECISION]** Department (Men/Women) is a descriptive label; only the model differs between departments.
- **[BUSINESS RULE / DECISION]** Every generated output requires human review (`human_review_required` = true).
- **[ANALYTICAL ASSUMPTION]** Every creative choice (season mood, scene, lighting, model, formats) is an assumption, not a claim that it performs better.

Kevin's decisions, 2026-10-17 (extension: creative approaches layer):

- **[BUSINESS RULE / DECISION]** Four creative approaches (studio hero, lifestyle context, detail close-up, flat lay), grounded in documented practice (see "Creative Approaches" and "References").
- **[BUSINESS RULE / DECISION]** Persuasion principles (Cialdini) were considered and excluded, because they require claims that the restrictions forbid. The exception is "liking", which can be shown through the model and the scene. The source for this was not verified in this stage.
- **[BUSINESS RULE / DECISION]** Color psychology is excluded; color guidance is limited to design harmony.

## Brief Specification

### Modes

- **production**
  - **[BUSINESS RULE / DECISION]** A reference image of the real product is **required**.
  - **[BUSINESS RULE / DECISION]** The ad is built around the real product. The automation must not alter or invent the product: shape, color, details and logo stay as in the reference image.
- **demo**
  - **[DATASET LIMITATION]** TheLook has no product images.
  - **[BUSINESS RULE / DECISION]** The demo uses an image the project owner has the right to use. The image is selected and its license verified in Stage 6.
  - **[BUSINESS RULE / DECISION]** The output is labeled illustrative: "not a TheLook product".
  - **[BUSINESS RULE / DECISION]** No brand names or logos in generated text or imagery.

### Fields

| Field | Description | Source |
|---|---|---|
| `mode` | `production` or `demo` | Manual input |
| `garment_type` | Garment type from Stage 4 (e.g., Jackets) | Stage 4 output |
| `department` | Men or Women; descriptive label only | Product data |
| `product_reference_internal` | Product id and name; internal use only, never in ad text | `data/raw/type_ranking_examples_2026-10-07.csv` |
| `reference_image` | Image of the product (required in production mode) | Production: real product image; demo: selected in Stage 6 |
| `garment_color` | Color of the garment | Taken from the image; manual input only in demo mode without a usable image |
| `season` | `spring`, `summer`, `autumn` or `winter` | Manual input |
| `style_direction` | Mood, scene, lighting and model | `config/creative_rules.json` (seasons, department_model) |
| `format` | Output size | `config/creative_rules.json` (formats) |
| `restrictions` | Rules the output must respect | `config/creative_rules.json` (restrictions) |
| `human_review_required` | Always `true` | Business rule |
| `creative_approach` | Optional: `studio_hero`, `lifestyle_context`, `detail_closeup` or `flat_lay`; if null, the default for the format is used | `config/creative_rules.json` (creative_approaches, default_approach_by_format) |
| `color_harmony` | Optional: `complementary` or `analogous`; if null, the default (`analogous`) is used | `config/creative_rules.json` (color_harmony) |

## Creative Approaches

Added 2026-10-17 (extension). The values live in `config/creative_rules.json`.

**[ANALYTICAL ASSUMPTION]** The four approaches are grounded in documented design practice (see "References"). They are not evidence of performance, and no approach is claimed to perform better than another.

| Approach | AIDA role | Lighting | Composition | Suitable formats |
|---|---|---|---|---|
| `studio_hero` | attention | large diffused soft light, key light close to the camera axis, gentle fill, no hard overhead light | garment centered or on a third line, front or three-quarter view, minimal props | `square_post`, `portrait_post`, `landscape_post` |
| `lifestyle_context` | desire | natural soft light; avoid harsh overhead sun; choose the light direction that flatters garment and model | model in the seasonal scene from the seasons section; rule of thirds as a guide; keep clean negative space for text in wide formats | `portrait_post`, `story_vertical`, `landscape_post`, `cover_banner` |
| `detail_closeup` | interest | soft low-contrast diffused light that keeps fine detail | tight crop on texture, collar, closure or stitching; no model required | `avatar`, `square_post` |
| `flat_lay` | interest | large diffused light, same angles repositioned for a surface | top-down view, garment spread out, consistent spacing, minimal relevant props | `square_post`, `portrait_post` |

- **[ANALYTICAL ASSUMPTION]** `flat_lay` has weaker support (a commercial blog plus comments): manual selection only, never a default.

**[ANALYTICAL ASSUMPTION]** Default approach by format (used when `creative_approach` is null):

| Format | Default approach |
|---|---|
| `square_post` | `studio_hero` |
| `portrait_post` | `lifestyle_context` |
| `story_vertical` | `lifestyle_context` |
| `landscape_post` | `lifestyle_context` |
| `cover_banner` | `lifestyle_context` |
| `avatar` | `detail_closeup` |

- **[ANALYTICAL ASSUMPTION]** Color harmony: allowed values `complementary` and `analogous`; default `analogous`. Choose the background and scene palette relative to the garment color: complementary for contrast, analogous for cohesion. This is design harmony only; no psychological claims are made about colors.
- **[ANALYTICAL ASSUMPTION]** AIDA (attention, interest, desire, action) is used only to label each approach's role. The action stage is out of scope, because price and calls to action are not part of the image. The mapping is a project assumption.
- **[BUSINESS RULE / DECISION]** In production mode, lighting and color guidance applies to the scene around the product; the product itself is never retouched or altered.

## Rules

The rules live in `config/creative_rules.json`.

- **[ANALYTICAL ASSUMPTION]** Seasons: a short mood, scene and lighting description for each season; generic, with no brand names.
- **[BUSINESS RULE / DECISION]** Department: the department is a descriptive label. Scene and styling stay identical across departments; only the model differs. Stereotypes are avoided.
- **[ANALYTICAL ASSUMPTION]** Department model wording: Men → adult male model; Women → adult female model.
- **[ANALYTICAL ASSUMPTION]** Formats: project-defined working sizes, not official platform specifications.

| Format | Aspect ratio | Size (px) |
|---|---|---|
| `square_post` | 1:1 | 1080×1080 |
| `portrait_post` | 4:5 | 1080×1350 |
| `story_vertical` | 9:16 | 1080×1920 |
| `landscape_post` | 16:9 | 1920×1080 |
| `cover_banner` | 3:1 | 1500×500 |
| `avatar` | 1:1 | 400×400 (product close-up) |

- **[BUSINESS RULE / DECISION]** Restrictions:
  - All modes:
    - no real identifiable people;
    - no price or discount claims;
    - no performance claims;
    - human review is required before any output is considered valid.
  - Demo mode:
    - no brand names or logos in generated text or imagery;
    - label the output as illustrative: not a TheLook product;
    - the reference image must be one the project owner has the right to use; its license is verified in Stage 6.
  - Production mode:
    - a reference image of the real product is required;
    - the product is never altered or invented: shape, color, details and logo stay as in the reference image;
    - in production mode, lighting and color guidance applies to the scene around the product; the product itself is never retouched or altered.

## Limitations

- **[DATASET LIMITATION]** `dim_product` has no color column and no product images.
- **[DATASET LIMITATION]** The demo image is not a TheLook product, so demo outputs are illustrative only.
- **[ANALYTICAL ASSUMPTION]** The creative rules are not tested; no claim is made that any season, scene, model or format performs better.
- **[BUSINESS RULE / DECISION]** Publication and performance measurement are outside the project.
- **[ANALYTICAL ASSUMPTION]** The creative-approach sources are practitioner advice, design education, a commercial blog, a literature review and a secondary history, not experiments.
- **[ANALYTICAL ASSUMPTION]** No claim is made that any creative approach performs better than another.
- **[ANALYTICAL ASSUMPTION]** `flat_lay` has the weakest support: a commercial vendor blog plus comments on a practitioner article.
- **[ANALYTICAL ASSUMPTION]** AIDA is attributed to Lewis (1898) mainly through Strong's 1925 book; Lewis never presented a fixed formula or used the acronym.
- **[BUSINESS RULE / DECISION]** The project does not measure results, so none of these assumptions is tested.

## References

Added 2026-10-17 (extension). Copied from `sources` in `config/creative_rules.json`.

| Id | Source | Evidence type | Caveat |
|---|---|---|---|
| `lewis_aida` | Wikipedia, "E. St. Elmo Lewis". https://en.wikipedia.org/wiki/E._St._Elmo_Lewis | secondary history | AIDA is attributed to Lewis (1898) mainly through Strong's 1925 book; Lewis never presented a fixed formula or used the acronym. |
| `adler_canon` | Lindsay Adler, "Photography Essentials for Fashion Bloggers Part 1: Lighting and Exposure Fundamentals", Canon U.S.A., 2019-03-21. https://www.usa.canon.com/learning/training-articles/training-articles-list/photography-essentials-for-fashion-bloggers-part-1-lighting-and-exposure-fundamentals | practitioner advice | Natural light only. |
| `house_fstoppers` | Peter House, "How to Light Clothing Like a Product Photographer", Fstoppers, 2014-04-14 (modified 2021-05-06). https://fstoppers.com/commercial/how-light-clothing-product-photographer-9524 | practitioner advice | Does not cover ghost mannequin; flat lay appears only in comments. |
| `dutile_dps` | Matt Dutile, "3 Ways to Improve Your Images With Composition", Digital Photography School, 2013-08-15 (modified 2020-12-01). https://digital-photography-school.com/3-ways-to-improve-your-images-with-composition/ | practitioner advice | No studies or data; the rule of thirds is not a hard rule. |
| `adobe_color_wheel` | Adobe Express, "The color wheel explained and how colors work together", 2026-05-28. https://www.adobe.com/ara/express/learn/blog/color-wheel-explained | design education | Its wording on triadic and split-complementary is inconsistent, so only complementary and analogous are used. |
| `squareshot_ecommerce` | Squareshot, "E-commerce photography tips to boost your online sales". https://www.squareshot.com/post/e-commerce-photography-tips-to-boost-your-online-sales | commercial vendor blog | No data behind its claims; weakest source, used only for catalog conventions. |
| `singh_2006` | S. Singh, "Impact of color on marketing", Management Decision 44(6), 2006. https://www.emeraldinsight.com/doi/abs/10.1108/00251740610673332 | literature review | Reports inconsistencies and controversies in color psychology; used only to justify excluding color psychology. |

## Work Completed

2026-10-17:

- Defined the two-mode brief (production and demo).
- Defined the brief fields.
- Wrote `config/creative_rules.json`: seasons, department model, six formats and restrictions.
- Wrote `config/brief_example.json`: demo mode, Jackets, Men, autumn, with the product read from the Stage 4 examples CSV.
- Ran consistency checks between the doc and the config files and fixed the gaps they found.

2026-10-17 (extension: creative approaches layer):

- Added four creative approaches, default approach by format, color harmony, an AIDA note and seven sources to `config/creative_rules.json`.
- Added `creative_approach` and `color_harmony` to `config/brief_example.json`.
- Added the "Creative Approaches" and "References" sections to this doc.

## Concepts Learned

- **The brief as a contract** between the analysis and the automation.
- **Configuration-driven rules:** keeping rules in a configuration file instead of hard-coding them in the workflow.
- **Demo mode vs production mode:** separating an illustrative demo from work on the real product.
- **Evidence tags for creative decisions:** separating business rules from creative assumptions.
- **Checking a document against its configuration files.**

## Problems Encountered

1. `dim_product` has no color column and TheLook has no product images.
2. Product names contain real brand names.
3. The same rule had two different evidence tags in the doc and the JSON.
4. Two doc rules were missing from the JSON, and the Restrictions list in the doc had drifted from the JSON.

## Solutions

1. Color comes from the reference image, with manual input only in demo mode; documented as [DATASET LIMITATION].
2. Demo mode forbids brand names and logos; the product name is kept as an internal reference only.
3. The rule was unified as [BUSINESS RULE / DECISION]; [ANALYTICAL ASSUMPTION] is kept only for creative values.
4. Both rules were added to the JSON, and the Restrictions list in the doc now mirrors it item by item.

## PL-300 Connection

- Stage 5 is a specification with no Power BI, DAX or Power Query work, so it has no direct PL-300 content.

## Skills Demonstrated

- Requirements and specification writing.
- Configuration-driven design.
- Risk awareness: product fidelity and trademarks.
- Recognizing dataset limitations.
- Documentation consistency checks.

## Portfolio Evidence

- `docs/stage-05-creative-brief.md` — the Stage 5 brief specification and stage log.
- `config/creative_rules.json` — seasons, department model, formats, restrictions, creative approaches, default approach by format, color harmony, AIDA note and sources.
- `config/brief_example.json` — one example brief in demo mode.

## Stage Validation

- **[OBSERVED FACT]** Every field in the Fields table exists in `config/brief_example.json`.
- **[OBSERVED FACT]** The formats table matches `config/creative_rules.json`: names, aspect ratios, widths and heights.
- **[OBSERVED FACT]** The production and demo mode rules and the Restrictions list match the restrictions in `config/creative_rules.json` item by item.
- **[OBSERVED FACT]** The doc states, tagged [DATASET LIMITATION], that `dim_product` has no color column and no product images.
- **[OBSERVED FACT]** The evidence tags were reviewed; the department rule carries the same tag in the doc and the JSON.
- **[OBSERVED FACT]** Both JSON files load without errors.
- **[OBSERVED FACT]** None of the three files is ignored by git (`git check-ignore -v`).

Extension checks (2026-10-17):

- **[OBSERVED FACT]** Both JSON files load without errors after the extension.
- **[OBSERVED FACT]** Every `suitable_formats` value exists in `formats`.
- **[OBSERVED FACT]** `default_approach_by_format` covers all six formats, each default is allowed by that approach's `suitable_formats`, and `flat_lay` is never a default.
- **[OBSERVED FACT]** Every `source_ids` value exists in `sources`, and every source is used at least once.
- **[OBSERVED FACT]** The example brief's values are allowed: `studio_hero` exists and allows `square_post`; `analogous` is an allowed color harmony.

## Stage Log

- **Brief specification (2026-10-17):** defined the Stage 5 scope (specification only), the two modes (production and demo), the brief fields and the creative rules. Created `config/creative_rules.json` and an example brief in demo mode (`config/brief_example.json`: Jackets, Men, autumn, `square_post`).
- **Closure (2026-10-17):** Stage 5 approved and closed by the project owner.
- **Extension: creative approaches layer (2026-10-17):** added four creative approaches (studio hero, lifestyle context, detail close-up, flat lay), the default approach by format, the color harmony rule, the AIDA note and seven sources to `config/creative_rules.json`; added `creative_approach` and `color_harmony` to the example brief; documented them here as analytical assumptions, not evidence of performance.

**Stage 5 Status: COMPLETE (2026-10-17, extended 2026-10-17)**
