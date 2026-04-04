# Analytics Design Rationale

Decisions made during the analytics system design (2026-03-31) and the reasoning behind them.

## Why SQLite, Not Markdown Files

The original schema design (`analytics-recs-report.md`) proposed markdown files with YAML frontmatter — one snapshot file per post per capture date, plus a summary file per post.

SQLite was chosen instead because the primary consumer of analytics data is Claude, and the core value of analytics is cross-post comparison. Answering "which framework has the highest save rate?" in markdown requires reading N files, extracting YAML, and computing in-context — burning tokens and inviting errors. In SQL, it's one query.

Markdown's advantages (human-readable, git-diffable) were judged less important than query capability. The manager can ask Claude to report any metric in conversational form.

## Why No Generated Markdown Views

A hybrid approach (SQLite as source of truth, auto-generated markdown view files for human reading) was proposed and rejected in favor of pure SQLite. This keeps the system at one file with no sync concerns.

## What Was Excluded From the Schema

### Per-post demographics (age, gender, location)

The demographic profile was nearly identical across all 3 measured posts at design time (25-34 primary, ~55% male, ~96% US). Storing 6+ columns per snapshot that are the same row after row was judged not worth the complexity. If the profile shifts meaningfully, it will surface in account-level observation first. Adding columns later is non-breaking.

### Traffic source breakdown beyond FYP

Profile traffic, search traffic, DM traffic, and following traffic were all under 2% individually across all measured posts. Only `fyp_percent` is stored. The others are noise at this account's stage (sub-1K followers, 96-99% FYP distribution). If FYP ever drops significantly, the breakdown can be added.

### Caption text and hashtags

**Originally excluded** — captions lived in `copy.md` in each post's directory, and duplicating them in the database was judged a sync problem.

**Reversed (2026-04-01):** `description` and `hashtags` columns were added to the `posts` table. The reason: most posts (42 of 45 at the time) were discovered posts with no repo directory or `copy.md` at all. The caption is the only text content available for these posts, and it's the richest source for content classification (city, topic, style). Hashtags are stored separately (comma-separated, `#` stripped) to enable cross-post filtering without text parsing at query time. Both are populated automatically from the TikTok API during the discover procedure's enrichment step — no sync problem because the API is the source of truth, not a local file.

For engine-produced posts, `copy.md` still exists as the authoritative slide-by-slide copy. The `description` column stores the published caption (which may differ from copy.md). This is not duplication — they serve different purposes.

### Notes and performance tier classifications

Free-form text and subjective labels ("breakout", "average") belong in strategy documents where they have narrative context, not in database columns. The assistant should compute relative performance at query time against current baselines, not read stale labels.

### Engagement rate and save rate

Derived from stored columns. Storing them would violate single-source-of-truth. Computed at query time via `(likes+comments+shares)*100.0/views` and `bookmarks*100.0/views`.

## v2 Schema Migration (2026-04-02)

### Why Separate Universal and Company-Specific Data

The v1 schema stored everything in a flat `posts` table — universal TikTok fields alongside Nexus-specific columns (slug, city, framework, angle, hook_text). This worked for a single-company prototype but violated the generalization goal: another company using this engine would need to modify the `posts` table to add their own metadata columns, creating a fork.

The v2 migration splits the table:
- `posts` contains only universal TikTok data (post_id, posted_date, description, content_type, etc.)
- `nexus_post_metadata` contains Nexus-specific fields (slug, city, framework, angle, format, etc.), joined on post_id

Generalizing to another company means creating their own metadata table (e.g., `company_x_post_metadata`) without touching `posts` or `readings`.

### Why Subtype Tables

Carousels and videos have structurally different properties (slide count vs. duration, per-slide data vs. video completion). The v1 schema handled this with nullable columns in a single table. v2 adds `carousel_details` and `video_details` as subtype tables, each with a foreign key to `posts`.

These are stubs currently — `carousel_details` has only `post_id`, and `video_details` adds `duration_seconds` (not yet collected). The tables exist so that future per-slide or per-video data has a defined home without further schema changes.

### Why Traffic Source Breakdown Was Added

The v1 rationale excluded traffic sources beyond FYP% because profile, search, following, and DM traffic were all under 2% individually. This was correct for a sub-500 follower account.

v2 adds `search_percent`, `profile_percent`, `following_percent`, and `other_percent` as stub columns in `readings`. They are all NULL currently. The reversal is forward-looking: as the account grows past 1K followers, non-FYP traffic should increase. The columns exist so that data collection can be expanded without a schema migration. Analysis procedures (Level 3) already reference these fields with graceful null handling.

### Data Classification: Permanent vs. Transient

A key architectural decision in v2 is the explicit classification of all data:

**Permanent data** (posts, nexus_post_metadata, subtypes) represents facts about the post that are set at publication time and don't change. One row per post. Updates are in-place and only fill null fields — they never overwrite existing values.

**Transient data** (readings, account) represents point-in-time observations. Every capture produces a new row. Rows are never updated or deleted.

This classification determines idempotency behavior and eliminates the duplicate detection ambiguity documented in `known-issues.md`. See analytics-schema.md for the full idempotency rules.

### Why UTC With Explicit Offset

Pre-v2 readings stored `captured_at` as `YYYY-MM-DDTHH:MM:SS` without a timezone suffix. The values were UTC but this wasn't explicit. If the system clock were set to a non-UTC timezone, new readings could be inconsistent with old ones.

v2 standardizes: all new `captured_at` values include `+00:00`. All Python datetime operations use `datetime.now(timezone.utc)`. SQLite's `julianday('now')` is inherently UTC. Pre-v2 readings retain their suffix-less format — they are still UTC and sort correctly as ISO 8601 strings.

### Why the Manifest System

The v1 capture procedure used a single `pending-capture.csv` as both the collection artifact and the state tracker. If the procedure failed mid-collection, the CSV was in an ambiguous state (some rows filled, some not) with no record of progress.

v2 introduces a `manifest.json` that tracks per-post and per-batch status separately from the metric data. The CSV remains the human-readable collection sheet. The manifest tracks whether each batch is pending, collected, or ingested. This enables:
- Batch-by-batch collection with approval gates between batches
- Safe partial completion (manifest records where the procedure stopped)
- Manifest guard preventing triage from overwriting an in-progress cycle

### Idempotency Model

The capture procedure is designed around two idempotency principles:

1. **Permanent data: insert or fill nulls.** The discover script can be run repeatedly with the same input. New posts are inserted. Existing posts have their null fields updated with incoming non-null values. Non-null fields are never overwritten. This enables incremental enrichment across multiple runs.

2. **Transient data: insert always.** Every reading is a new row at a new timestamp. Two readings of the same post at different times are both valid — they capture different points in the post's lifecycle. The triage system prevents redundant readings by not surfacing posts that already have readings in their current snapshot window.

## v3 Schema Changes (2026-04-03)

### Data Minimalism Principle

The v3 migration applies a principle: don't add schema for data with no collection path and no analytical consumer. Several v2 columns had 0% coverage, no procedure to populate them, and no analysis that consumed them. Carrying them added schema complexity without analytical return.

### Why hook_text and hook_style Were Removed

`hook_text` stored the exact text of the opening slide. This is content data — it belongs in `carousel_details.slide_texts` (as the first element of the JSON array). Storing it separately in nexus metadata meant maintaining two copies of the same string.

`hook_style` (curiosity, contrast, bold_claim, list, question) had 0% coverage, no classification procedure, and no analytical consumer. The categories are Nexus's analytical taxonomy, but without a way to populate them, the column was dead weight. If hook style analysis becomes a priority, it can be re-added with a concrete classification procedure.

### Why angle Was Removed

`angle` (broad_city_guide, category_deep_dive, worth_it_list) was designed to be orthogonal to `framework` — framework × angle = concept. In practice, they were correlated 1:1: Worth It framework always used worth_it_list angle, everything else was broad_city_guide. At current data, angle added no analytical discrimination beyond what framework already provided.

### Why format Was Renamed to slide_layout

The column stores a slide layout strategy (combined, split, single_point) but the name "format" reads as "file format" or "data format." Renamed to `slide_layout` for clarity.

`slide_layout` is free text with documented conventions, not a CHECK constraint. New layout types are expected as content strategy evolves. Classification of layout is a judgment call — it requires looking at the slides and determining how content is arranged.

### Why CTA Moved to carousel_details

CTA presence, type, and text are carousel-specific design decisions. A carousel CTA is a deliberate slide in the deck. A video CTA is a caption sentence. The meaning differs by content type. Since we're designing for carousels, CTA data lives in `carousel_details` where it's structurally appropriate.

### Why content_topics Moved to posts

Topic tags (food, nightlife, views, outdoors) describe what a post is about. This is universal — any TikTok account's posts have topics. The specific taxonomy may differ by niche, but the concept of tagging posts by topic is not company-specific. Moved from `nexus_post_metadata` to `posts` as a universal stub.

### Carousel Content Analysis Fields

v3 adds `slide_texts`, `visual_summary`, `has_cta`, `cta_type`, and `cta_text` to `carousel_details`. These are content analysis fields populated by reading the post's content artifacts (copy.md, slide images) or by the generate procedure during production. They enable Level 2 outlier investigation and Level 5 CTA analysis without re-reading content artifacts on every analysis run.

## Four-Procedure Model (2026-04-03)

### Why Discover Was Narrowed

The original discover procedure handled five responsibilities: register posts, enrich from API, download slide images, generate visual summaries, and update the cutoff. This made it fragile at scale — a 100-post backfill required API calls, hundreds of image downloads, and AI-generated summaries all in one session. A failure in image download meant the entire procedure needed re-running.

The v3 redesign splits discover's responsibilities across four procedures based on data type:

1. **Discover** — register posts + enrich from API. Writes permanent captured data to `posts`, `nexus_post_metadata`, subtype tables. Idempotent. Scope: everything that comes from the TikTok API or repo directory parsing.

2. **Capture Reading** — collect transient metrics. Writes to `readings`, `account`. Already existed as the daily analytics capture procedure. Renamed for clarity.

3. **Capture Content** — download slide images, extract slide text. Writes to `carousel_details.slide_texts` and slide images on filesystem. New procedure. Scope: everything that requires downloading or reading the actual content of a post.

4. **Derive** — classify and analyze content. Writes to `carousel_details` (visual_summary, has_cta, cta_type, cta_text), `nexus_post_metadata` (framework, slide_layout), `posts` (content_topics). New procedure. Scope: everything that requires judgment or classification from content that's already captured.

### Why This Split

The split follows the data classification: permanent captured, transient, and permanent derived. Each procedure writes one type. This means:

- Each procedure can fail independently without blocking the others.
- Each procedure can be run at different cadences (discover on-demand, capture reading daily, capture content after discover, derive after capture content).
- Each procedure has clear prerequisites: capture reading requires discover (posts must exist). Capture content requires discover (content_type must be known). Derive requires capture content (slide text must be available).

### Shared Unit Processes

`collect_post.py` is shared between discover and capture reading. The same API call returns both transient metrics (consumed by capture reading) and permanent metadata (consumed by discover via `enrich_from_api`). This avoids duplicate API calls — the orchestrating procedure (Claude) calls collect_post once and routes the fields to the appropriate consumer.

## Known Edge Cases

### Caption/hashtag mutability

`description` and `hashtags` in the `posts` table are treated as permanent but are technically editable on TikTok. A user can edit their caption after posting. The current procedure writes these once during discovery and never re-fetches them. If a caption is edited on TikTok, the database retains the original version. This is accepted — caption edits are rare and the analytical impact is minimal.

## Prior Art

`analytics-recs-report.md` contains the original schema design that informed this implementation. It covers the reasoning for which metrics matter at the "content generation engine" level. The file remains in the repo as a design artifact but is not operationally referenced — the database is the implementation.

`analytics-report-03-30.md` is the first manual analytics report (3 posts, captured March 30, 2026). Its data has not been backfilled into the database. It remains as a historical document.
