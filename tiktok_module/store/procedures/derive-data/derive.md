# Derive Data — Content Classification & Analysis

Reads captured content (slide images, captions) and populates derived database fields through vision AI and classification. Does not access TikTok or require Chrome. Works entirely from the filesystem and database.

## Scope

Classifies and analyzes content that has already been captured. All derivation uses slide images as the primary source, supplemented by captions where available.

Derives, in order:
1. **slide_texts** — per-slide text transcribed from images
2. **visual_summary** — description of visual style, layout, progression
3. **framework** — structural pattern classification (requires visual_summary + slide_texts)
4. **slide_layout** — slide arrangement classification (requires visual_summary + slide_texts)
5. **CTA** — call-to-action presence and classification (requires visual_summary + slide_texts)
6. **content_topics** — topic tags (requires visual_summary + slide_texts + caption)

Steps 3-6 depend on steps 1-2. If transcription or visual summary fails for a post, classification is skipped for that post.

## Prerequisites

- Posts registered in DB with slide images on filesystem (capture content completed).
- Framework and slide layout definitions in `store/data/strategy/frameworks.md`.
- No Chrome required.

## Model Requirement

Steps 1-2 (slide text transcription and visual summary generation) are vision-dependent and **must use Opus**. When the orchestrating procedure launches agents for these steps, it must specify `model="opus"`. The `VISION_MODEL` constant in `derive_data.py` codifies this.

Steps 3-6 (framework, slide_layout, CTA, content_topics) are deterministic Python classifiers and are model-independent.

## Classification Principles

- **NULL on ambiguity.** A wrong classification is worse than a missing one. Classify with confidence or leave NULL.
- **Visual summary is the primary signal** for framework and slide_layout. Slide texts confirm.
- **Framework and slide_layout definitions** are in `store/data/strategy/frameworks.md` with visual signatures. New patterns not in the catalog → NULL.
- **Posts left NULL** surface in the batch summary as "Suggested manual review" with a description of what was ambiguous.

## Procedure

### Step 1 — Triage

```
python store/scripts/derive_data.py --triage-only
```

Scans all carousel posts. For each, checks which derived fields are NULL and whether slide images exist. Reports processable posts, posts needing capture content first, and posts already fully derived.

If zero posts are processable, stop.

### Steps 2-7 — Derive (Batch by Batch)

```
python store/scripts/derive_data.py
```

Processes posts in batches of 5. For each post in the batch, runs all derivation steps in order:

1. **Transcribe slide_texts** — vision AI reads each slide image, extracts text overlays
2. **Generate visual_summary** — vision AI describes visual style, layout, colors, progression
3. **Classify framework** — reads visual_summary + slide_texts + frameworks.md catalog
4. **Classify slide_layout** — reads visual_summary + slide_texts + layouts catalog
5. **Classify CTA** — reads visual_summary + slide_texts for CTA presence anywhere in the carousel
6. **Extract content_topics** — reads visual_summary + slide_texts + caption for topic tags

### Step 8 — Batch Summary

After each batch:

```
--- Batch 1 Complete (5 posts) ---
  seattle-2025-12-26       texts: 10 slides  summary: done  framework: local_vs_tourist  layout: split     cta: engage  topics: coffee,markets,views,food,nightlife
  phoenix-2025-12-09       texts: 6 slides   summary: done  framework: local_vs_tourist  layout: combined  cta: engage  topics: hikes,nightlife,food
  ...

Suggested manual review:
  7576799139019771167: framework ambiguous — single slide, no recognizable pattern
```

**Approval gate (debug mode only):** In debug mode, wait for manager approval before committing DB writes and proceeding. Manager can approve, reject (re-examine flagged posts), or disable debug mode for the remainder of this procedure. In normal mode, commit and proceed automatically.

### Step 9 — Report

After all batches:

```
Derive Data complete.
  slide_texts: 27 transcribed
  visual_summary: 27 generated
  framework: 24 classified (3 left NULL)
  slide_layout: 25 classified (2 left NULL)
  CTA: 27 classified (22 with CTA, 5 without)
  content_topics: 27 extracted

Suggested manual review:
  7576799139019771167: framework NULL — single slide, no pattern
  7580170140919106846: framework NULL — ambiguous contrast structure
```

## Idempotency

All writes: update only if the field is currently NULL. Never overwrite existing classifications. Re-running processes only posts with remaining NULL fields.

## Error Handling

- **Vision AI can't read a slide:** Write partial slide_texts with readable slides, empty string for failed ones. Flag in batch summary.
- **Ambiguous classification:** Leave NULL. Surface in "Suggested manual review."
- **No slide images:** Skip post. Report as needing capture content.
- **Unexpected error:** Stop batch, diagnose, report to manager.

## Scripts

| Script | Purpose |
|---|---|
| `store/scripts/derive_data.py` | Triage + batch orchestration + DB writes. Contains unit function stubs for all 6 derivation steps. |

Unit functions within `derive_data.py`:
- `transcribe_slide_texts(slide_image_paths)` → JSON array
- `generate_visual_summary(slide_image_paths)` → string
- `classify_framework(visual_summary, slide_texts, catalog)` → string or NULL
- `classify_slide_layout(visual_summary, slide_texts, catalog)` → string or NULL
- `classify_cta(visual_summary, slide_texts)` → dict or NULL
- `extract_content_topics(visual_summary, slide_texts, description)` → string or NULL

## Downstream

After derive data completes, the analyze procedures (L1-L5) run with:
- Complete slide_texts in carousel_details (Level 2 outlier investigation, Level 5 CTA analysis)
- Visual summaries (Level 2 outlier investigation, Level 3 flagged post investigation)
- Framework and slide_layout classifications (Level 2 dimension comparisons)
- CTA data (Level 5 conversion funnel)
- Content topics (Level 2 dimension comparisons)
