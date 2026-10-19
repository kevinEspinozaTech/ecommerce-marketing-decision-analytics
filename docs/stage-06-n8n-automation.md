# Stage 06 — n8n Ad Image Automation (v1 demo)

**Stage 6 Status: Complete (dry-run v1; real Gemini generation deferred) (2026-10-19)** — the v1 demo workflow is built, exported and sanitized (`n8n/stage-06-ad-image-v1-demo.json`) and was verified end to end in dry-run mode (2026-10-19). Approved and closed by the project owner on 2026-10-19.

## Purpose and Scope

Turn a Stage 5 creative brief into an ad image candidate with an n8n workflow, with a mandatory human review before anything is saved.

The v1 demo flow:

1. Manual trigger.
2. Validate the brief.
3. Build the image prompt from `config/creative_rules.json`.
4. Image step (Gemini node, disabled in v1: dry run).
5. Human review.
6. Save the image and its metadata (only if approved).

- **[BUSINESS RULE / DECISION]** Out of scope: video, multi-format batches, publishing or scheduling, and any paid API call.

**[DATASET LIMITATION]** TheLook is synthetic and has no product images. The demo image is not a TheLook product.

## Decisions Made

Kevin's decisions, 2026-10-19:

- **[BUSINESS RULE / DECISION]** n8n runs self-hosted (n8n Community) on Kevin's PC.
- **[BUSINESS RULE / DECISION]** The Gemini API is the v1 image provider, isolated in **one** node so the provider can be swapped.
- **[BUSINESS RULE / DECISION]** The demo reference image is the author's own logo-free jacket photo. Outputs are labeled "illustrative: not a TheLook product".
- **[BUSINESS RULE / DECISION]** The full structure is built, but **no paid API call** is made now: the Gemini node is configured, has no credential and is deactivated ("dry run").
- **[BUSINESS RULE / DECISION]** Paying for and creating the API key is deferred until real use.
- **[BUSINESS RULE / DECISION]** Option C (cutout + composite) is a documented future improvement, not part of v1.
- **[BUSINESS RULE / DECISION]** Human review is mandatory.

## Environment

- **[OBSERVED FACT]** n8n 2.43.8, installed globally with npm (Node v24.22.0, npm 11.19.1).
- **[OBSERVED FACT]** In Windows PowerShell, the `.cmd` wrappers (`npm.cmd`, `n8n.cmd`) are used, because `.ps1` scripts are blocked.
- **[OBSERVED FACT]** n8n data lives outside the repository.
- **[OBSERVED FACT]** File nodes are restricted by `N8N_RESTRICT_FILE_ACCESS_TO`: a semicolon-separated list with the n8n files folder and the repository `config` folder. It must be set again in every PowerShell session before starting n8n.
- **[OBSERVED FACT]** n8n warns that non-Docker deployments will be deprecated in future versions.

## Workflow Architecture

The workflow is `n8n/stage-06-ad-image-v1-demo.json`: 20 nodes, 19 connections. The table follows the execution order from the workflow's connections; the two dead-end branches are listed after the IF node that leads to them.

| # | Node | Type | Purpose |
|---|---|---|---|
| 1 | When clicking "Execute workflow" | `manualTrigger` | Starts the workflow manually. |
| 2 | Brief | `set` | Holds the brief as raw JSON (paste `config/brief_example.json` here). |
| 3 | Validate brief | `code` | Checks the brief and adds `validation.valid` and `validation.errors`. |
| 4 | Brief valid? | `if` | True → Read creative rules; false → Stop and Error. |
| 5 | Stop and Error | `stopAndError` | Stops the run with "Brief validation failed: " and the list of errors. |
| 6 | Read creative rules | `readWriteFile` | Reads `<REPO_DIR>\config\creative_rules.json`. |
| 7 | Parse creative rules | `extractFromFile` | Parses the file as JSON into the `rules` key. |
| 8 | Build prompt | `code` | Builds the prompt from the brief and the rules. |
| 9 | Read reference image | `readWriteFile` | Reads `<N8N_FILES_DIR>\demo_reference_jacket.jpg` into the binary property `reference_image`. |
| 10 | Generate ad image (Gemini) | `googleGemini` | Image → Edit Image with model `gemini-nano-banana-2.1`, the prompt and `reference_image`; output to `generated_image`. **Disabled** and without a credential (dry run). |
| 11 | Mark generation status | `code` | Records whether an image was generated or the run was a dry run, and builds the metadata. |
| 12 | review from url | `set` | Stores the review form URL (`$execution.resumeFormUrl`) as `review_form_url`. |
| 13 | Human review | `wait` | Waits for the review form (see "Human-in-the-Loop Design"). |
| 14 | Apply review decision | `code` | Writes the decision, comment and timestamp into the metadata. |
| 15 | Approved? | `if` | True → Prepare output files; false → Rejected - nothing saved. |
| 16 | Rejected - nothing saved | `noOp` | End of the reject branch; nothing is written. |
| 17 | Prepare output files | `code` | Builds the output file names. |
| 18 | Save image | `readWriteFile` | Writes the image to `<N8N_FILES_DIR>/outputs/`. |
| 19 | Build metadata file | `code` | Turns the metadata into a JSON file (binary `metadata_file`). |
| 20 | Save metadata | `readWriteFile` | Writes the metadata JSON to `<N8N_FILES_DIR>/outputs/`. |

Note: in the exported node list, "Human review" appears before "review from url"; the connections run "review from url" first.

### Code nodes

- **Validate brief** — the brief is invalid if any rule fails:
  - `mode` is `demo` or `production`;
  - required fields exist and are not empty: `garment_type`, `department`, `season`, `style_direction`, `format`, `restrictions`;
  - `department` is `Men` or `Women`;
  - `format` has a name and a positive width and height;
  - `human_review_required` is `true`;
  - `restrictions` is a non-empty list;
  - in demo mode, a restriction contains the "illustrative" label.
- **Build prompt**:
  - looks up the season, department model, format, creative approach (from the brief, or the default for the format), color harmony (from the brief, or the default) and the mode restrictions in `creative_rules.json`, and throws an error on any unknown value;
  - adds a warning (without stopping) if the approach is not listed as suitable for the format;
  - splits the restrictions with a regex: visual restrictions go into the prompt; process-only restrictions (human review, the label, the license, "is required") stay in the metadata;
  - outputs the prompt, approach, color harmony, format, rules version, label restriction, both restriction lists and the warnings.
- **Mark generation status**:
  - sets `generation_status` to `generated` if a `generated_image` exists, otherwise `dry_run`;
  - in a dry run, records the note "DRY RUN: no image generation call was made. The image is the reference photo, not a generated ad." and passes the reference photo on as `review_image`;
  - throws an error if neither image is present.
- **Apply review decision** — accepts only `Approve` or `Reject`; sets `approved` and writes `human_review_decision`, `human_review_comment` and `human_reviewed_at`.
- **Prepare output files** — builds the base name and the image and metadata file names, and adds them to the metadata.
- **Build metadata file** — writes the metadata as indented JSON into a binary file.

## Human-in-the-Loop Design

- **[BUSINESS RULE / DECISION]** The Wait node resumes On Form Submitted.
- The form has:
  - a required Dropdown `decision` with the options Reject and Approve, and an empty default, so approval is never accidental;
  - an optional `Comment`.
- The decision, comment and timestamp are written into the metadata.
- Only Approve reaches the save nodes. Reject ends at "Rejected - nothing saved", with nothing saved.
- The form description asks the reviewer to view the image in the previous node (Mark generation status → Binary → `review_image`) and to approve only if the image matches the brief and shows no logos, brand names, real identifiable people, price or performance claims, and the product is not altered or invented.

## Outputs

- Files go to `<N8N_FILES_DIR>/outputs`.
- File base name: `ad_<format>_<season>_<DRYRUN|GENERATED>_<timestamp>`.
- The image and the JSON metadata share the same base name.
- The metadata keeps the label, `demo_note`, prompt, `rules_version`, warnings, the human review fields and the output file names.
- **[BUSINESS RULE / DECISION]** Outputs are **not** committed to the repository.

## Verification Performed

All checks were run manually by the author in dry-run mode on 2026-10-19.

- **[OBSERVED FACT]** Brief validation returned `valid = true` with 0 errors. A negative test with an invalid brief was stopped by "Stop and Error".
- **[OBSERVED FACT]** The rules file was read and parsed.
- **[OBSERVED FACT]** The prompt was built: `studio_hero`, plain neutral background, adult male model, 4 visual restrictions in the prompt, no warnings.
- **[OBSERVED FACT]** The reference photo was read.
- **[OBSERVED FACT]** The Approve path saved:
  - a `.jpg` (2,176,390 bytes; the reference photo, named `DRYRUN`);
  - a `.json` (1,997 bytes) with `generation_status` "dry_run", `human_review_decision` "Approve", the comment and the timestamp.
- **[OBSERVED FACT]** The Reject path ended at "Rejected - nothing saved", and no new files appeared.

Issues found and fixed:

1. The Dropdown default was "Approve" → it was cleared.
2. The file path expression was not evaluated when a backslash came directly before `{{` → forward slashes are used in expression paths. The cause was not confirmed in the documentation; the fix was confirmed by the preview and by the saved file names.

## Known Limitations

- **[OBSERVED FACT]** The Gemini call has **not** been executed: there is no credential and the node is disabled. The following are therefore not tested:
  - the output field mapping (`generated_image`);
  - whether the model ID is valid;
  - the request size limit for the ~2.18 MB reference photo;
  - the size of the returned image.
- **[OBSERVED FACT]** The Gemini node exposes no aspect-ratio option.
- **[BUSINESS RULE / DECISION]** There is no resize/crop step to the brief format; this is left as a documented limitation. The Edit Image node would need GraphicsMagick on Windows.
- **[OBSERVED FACT]** The Wait form cannot display the image; the reviewer views it in the previous node's Binary output.
- **[ANALYTICAL ASSUMPTION]** Restrictions are split into visual and process-only with a regex, which depends on the wording of the rules.
- **[OBSERVED FACT]** The model name is hard-coded in "Mark generation status".
- **[OBSERVED FACT]** The metadata field `label` holds the restriction sentence, not a clean label.
- **[OBSERVED FACT]** n8n shows a deprecation notice for non-Docker deployments.
- **[DATASET LIMITATION]** In demo mode, the product in the image is not a TheLook product.
- **[DATASET LIMITATION]** TheLook product names contain real brand text; they are for internal use only and never in ad text.

## How to Import and Run

1. Import `n8n/stage-06-ad-image-v1-demo.json` into n8n.
2. Replace `<REPO_DIR>` and `<N8N_FILES_DIR>` in the Read/Write file nodes.
3. Put a logo-free reference photo named `demo_reference_jacket.jpg` in the n8n files folder (not included in the repository).
4. Create the `outputs` folder.
5. Set `N8N_RESTRICT_FILE_ACCESS_TO`.
6. Paste a brief (`config/brief_example.json`) into the Brief node.

The exported JSON was sanitized: local paths were replaced by placeholders, the instance identifier was removed, and it contains no credentials.

## Checklist Before Enabling Gemini (future, not done)

- [ ] Create the API key and the credential only inside n8n.
- [ ] Set a low spend cap.
- [ ] Re-check model names and prices.
- [ ] Test the image size limit and the output mapping.
- [ ] Add a resize/crop step.
- [ ] Read the model name from configuration.

## Skills Demonstrated

- n8n workflow design.
- JavaScript in Code nodes.
- Configuration-driven prompt building.
- Human-in-the-loop design.
- Safe handling of secrets.
- Honest documentation of limits.

## PL-300 Connection

- This stage complements, but does not replace, Power Query and DAX practice.

## Portfolio Evidence

- `n8n/stage-06-ad-image-v1-demo.json` — sanitized export of the v1 demo workflow.
- `docs/stage-06-n8n-automation.md` — this document.

## Stage Log

- **v1 demo workflow (2026-10-19):** built the workflow (20 nodes) with the Gemini node disabled (dry run), verified the Approve, Reject and invalid-brief paths manually, fixed the Dropdown default and the expression-path issue, and exported a sanitized copy to `n8n/`.
- **Closure (2026-10-19):** Stage 6 approved and closed by the project owner as Complete (dry-run v1; real Gemini generation deferred). Delivered: the 20-node workflow verified in dry-run mode, the human review step, the Approve and Reject paths, the sanitized export and this documentation. Deferred: Gemini execution, the resize/crop step, and the API key and billing.

**Stage 6 Status: Complete (dry-run v1; real Gemini generation deferred) (2026-10-19)**
