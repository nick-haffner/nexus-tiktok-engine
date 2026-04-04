---
name: store-repair
description: "Diagnose and repair data issues in the store. Audits for gaps, inconsistencies, and stale data. Applies fixes with user approval."
---

# Store Repair

Inspects the database and filesystem for data issues, reports them, and applies fixes with user approval. Covers everything from missing metadata to retroactive reclassification.

## Before Starting

Read the following to understand the available toolkit:

1. **Database schema:** `tiktok_module/store/docs/analytics-schema.md` — all tables, columns, data types, what each field means
2. **Procedures:** `tiktok_module/handbook.md` — the four store procedures and what each writes
3. **Authoritative process decisions:** `tiktok_module/analyze/ANALYSIS-PROCESS.md` — gap taxonomy (structural vs addressable), data classification (permanent vs transient)

### Available Repair Tools

**Scripts for re-collecting data (require Chrome):**

| Script | What it does | When to use |
|---|---|---|
| `store/scripts/collect_post.py` | Fetch all metrics + enrichment (description, hashtags, sound_name, posted_time, duration) for one post via API | Missing or stale description, hashtags, sound_name, posted_time, duration_seconds |
| `store/scripts/collect_post_ids.py` | Collect all post IDs from TikTok Studio | Missing posts, sync issues |
| `store/scripts/collect_content.py` | Download carousel slide images for one post | Missing slide images |
| `store/scripts/collect_account.py` | Capture account checkpoint (followers, likes) | Stale or missing account data |

**Scripts for re-deriving data (no Chrome needed):**

| Script / Function | What it does | When to use |
|---|---|---|
| `store/scripts/derive_data.py` | Orchestrate all derivation for a batch of posts | Bulk re-derivation |
| `derive_units.py: classify_framework(visual_summary, slide_texts, catalog)` | Classify framework from content | Wrong or missing framework |
| `derive_units.py: classify_slide_layout(visual_summary, slide_texts, catalog)` | Classify slide layout from content | Wrong or missing slide_layout |
| `derive_units.py: classify_cta(visual_summary, slide_texts)` | Classify CTA presence and type | Wrong or missing CTA fields |
| `derive_units.py: extract_content_topics(visual_summary, slide_texts, description)` | Extract topic tags from all content sources | Missing or incomplete topics |
| `derive_units.py: extract_city(description, slide_texts, visual_summary, hashtags)` | Extract city from all content sources (weighted scoring) | Missing or wrong city |
| `derive_units.py: format_transcription(slide_texts)` | Validate slide text transcription | Re-transcription quality check |
| `derive_units.py: format_visual_summary(summary_text)` | Validate visual summary | Re-generation quality check |

**Scripts for database operations:**

| Script | What it does | When to use |
|---|---|---|
| `store/scripts/discover.py` | Register posts, idempotent null-fill updates | Missing post records, incomplete metadata |
| `store/scripts/discover.py: enrich_from_api()` | Write enrichment data to DB (description, hashtags, posted_time) | After collect_post fetches new data |
| `store/scripts/ingest.py` | Write readings to DB from CSV | Re-ingesting corrected readings |
| `store/scripts/generate_artifacts.py` | Generate caption.md and README.md from DB fields | Missing filesystem artifacts |

**Classification definitions:**

| File | What it contains | When to reference |
|---|---|---|
| `store/data/strategy/frameworks.md` | Framework and slide_layout definitions with visual signatures | Reclassification, adding new framework types |

### Key Rules

- **Null-fill is safe.** Writing to a NULL field follows the standard idempotent pattern — no approval needed.
- **Overwriting requires approval.** Changing an existing non-NULL value must show before/after and get explicit user approval.
- **Classification returns NULL when ambiguous.** Never force a classification. NULL is preferable to wrong.
- **Vision AI steps** (transcribe_slide_texts, generate_visual_summary) are executed by Claude reading slide images at procedure runtime, not by a Python function.

## Input

```
/store-repair              # full audit — scan everything, report gaps, propose fixes
/store-repair for          # targeted — user describes what to fix
```

## Full Audit

Scans every data layer and reports issues grouped by severity.

### Audit Checks

**1. Schema integrity**
- Foreign key violations (posts without nexus_post_metadata rows, carousel_details without posts)
- Orphaned filesystem directories (post directories with no matching DB record)
- DB records with no filesystem directory

**2. Metadata completeness**
- Posts missing description, hashtags, posted_time, sound_name
- Nexus metadata missing city, framework, slide_layout
- Carousel details missing slide_texts, visual_summary, has_cta, cta_type, cta_text
- Video details missing duration_seconds
- Posts with content_topics NULL

**3. Content completeness**
- Carousels with no slide images on filesystem
- Carousels where slide count in DB doesn't match files on filesystem
- Posts with no caption.md
- Posts with no README.md

**4. Classification quality**
- Posts where framework is NULL but slide_texts exist (classifiable but not classified)
- Posts where slide_layout is NULL but visual_summary exists (classifiable but not classified)
- Posts where city is NULL but description contains a recognizable city name
- Posts where content_topics is NULL but slide_texts or description exist

**5. Data freshness**
- Posts with no readings
- Posts with only old readings (last reading > 30 days ago for active posts)
- Account checkpoint age (days since last checkpoint)
- Discover cutoff age (days since last discovery run)

**6. Consistency**
- Slug doesn't match description (stale slug from before description was available)
- content_path doesn't match slug
- Framework classification conflicts with slide_texts content (e.g., classified as worth_it but slides contain contrast markers)

### Audit Output

```
Store Audit — 2026-04-04

Schema Integrity: OK
Metadata Completeness: 15 issues
Content Completeness: 4 issues
Classification Quality: 17 actionable
Data Freshness: OK
Consistency: 0 issues

Summary: 36 total issues (17 actionable, 15 expected, 4 known limitations)
```

Each category expands with per-field counts and specific post lists.

### Proposed Fixes

After the audit, propose fixes with the specific tool to use:

```
Proposed Fixes:

  [AUTO] Reclassify framework for 17 carousels
         Tool: derive_units.classify_framework(visual_summary, slide_texts, frameworks.md)
         Rule: null-fill only (won't overwrite existing classifications)
         Estimated: 17 posts, ~30 seconds

  [AUTO] Derive city for 2 posts from slide_texts
         Tool: derive_units.extract_city(description, slide_texts, visual_summary, hashtags)
         Rule: null-fill only
         Estimated: 2 posts, instant

  [MANUAL] Download 4 private CDN carousels
           Requires: manual download from TikTok Studio browser
           Tool after download: derive_data.py to process new slides

  [SKIP] 15 posts without city — non-city-specific content, expected NULL
  [SKIP] 19 videos without content_topics — deferred to v2

Apply automatic fixes? [Y/n]
```

### Prevention Suggestions

After fixes are applied (or after audit if no fixes needed), report prevention suggestions for any issues that indicate a process gap:

```
Prevention Suggestions:

  - 1 post missing description: ensure /store-update runs API enrichment
    after discover. The enrichment step (collect_post.py) fetches description
    from /aweme/v2/data/insight/. If it was skipped, re-run:
    /store-update for [post slug]

  - 17 posts with classifiable but unclassified framework: ensure Phase 3
    (derive data) runs after capture content. If derive was skipped or
    interrupted, re-run: /store-repair for "reclassify frameworks"

  - 4 carousels with private CDN: these require manual download. When
    publishing new posts, ensure visibility is set to "Public" so the
    CDN URLs are accessible for automated download.
```

## Targeted Mode

```
/store-repair for
```

**Step 1 — Ask what to repair.**

Ask: "What would you like to repair or check?"

| User says | Action | Tool |
|---|---|---|
| "Check if any frameworks are wrong" | Re-run classify_framework, compare against existing | `derive_units.classify_framework` |
| "We added a new framework type — reclassify everything" | Re-run on ALL carousels, overwrite | `derive_units.classify_framework` (with override) |
| "Visual summaries seem thin — regenerate them" | Claude re-reads slide images, regenerates | Vision AI + `derive_units.format_visual_summary` |
| "Re-derive all cities" | Re-run on all posts, overwrite | `derive_units.extract_city` (with override) |
| "Some posts are missing descriptions" | Query NULLs, re-enrich from API | `collect_post.py` + `discover.enrich_from_api` |
| "The schema is about to change — what would be affected?" | Query field coverage, report impact | DB queries only |
| "Check data health" | Run full audit | Same as `/store-repair` |
| "Fix the posts without slide images" | List, offer re-download or manual | `collect_content.py` or manual |
| "This post's CTA classification looks wrong" | Show current, re-classify, confirm | `derive_units.classify_cta` (with override) |
| "Slide text transcription missed some text" | Claude re-reads the slides, compares | Vision AI + `derive_units.validate_transcription` |

**Step 2 — Scope the repair.** Query DB, count affected posts, present plan with specific tools.

**Step 3 — Execute.** Apply fixes per the override rules (null-fill auto, overwrite with approval).

**Step 4 — Report + Prevention.** Show results and suggest how to prevent recurrence.

## Override Rules

- **Null-fill:** Apply without per-post confirmation. Same as derive.
- **Overwrite:** Confirm explicitly. Show before/after for first 3 posts. Apply to rest after approval.
- **Bulk reclassification:** When the user explicitly requests reclassification of already-classified posts (e.g., after taxonomy change), this is an intentional override. Confirm once for the batch, not per-post.

## What This Doesn't Do

- **Collect new data from TikTok.** That's `/store-update`. Exception: re-enrichment requests that explicitly ask to re-fetch from the API.
- **Run analysis.** That's the analyze function.
- **Change the schema.** Schema migrations are developer operations. But repair can report impact of proposed changes.
