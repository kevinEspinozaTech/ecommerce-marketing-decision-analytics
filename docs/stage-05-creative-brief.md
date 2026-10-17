# Stage 05 — Creative Brief

**Stage 5 Status: IN PROGRESS** — the brief specification, the creative rules (`config/creative_rules.json`) and one example brief (`config/brief_example.json`) are drafted (2026-10-17).

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
  - `config/creative_rules.json` — seasons, department model, formats and restrictions.
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
    - the product is never altered or invented: shape, color, details and logo stay as in the reference image.

## Limitations

- **[DATASET LIMITATION]** `dim_product` has no color column and no product images.
- **[DATASET LIMITATION]** The demo image is not a TheLook product, so demo outputs are illustrative only.
- **[ANALYTICAL ASSUMPTION]** The creative rules are not tested; no claim is made that any season, scene, model or format performs better.
- **[BUSINESS RULE / DECISION]** Publication and performance measurement are outside the project.

## Work Completed

To be completed at stage closure.

## Concepts Learned

To be completed at stage closure.

## Problems Encountered

To be completed at stage closure.

## Solutions

To be completed at stage closure.

## PL-300 Connection

To be completed at stage closure.

## Skills Demonstrated

To be completed at stage closure.

## Portfolio Evidence

To be completed at stage closure.

## Stage Validation

To be completed at stage closure.

## Stage Log

- **Brief specification (2026-10-17):** defined the Stage 5 scope (specification only), the two modes (production and demo), the brief fields and the creative rules. Created `config/creative_rules.json` and an example brief in demo mode (`config/brief_example.json`: Jackets, Men, autumn, `square_post`).

**Stage 5 Status: IN PROGRESS**
