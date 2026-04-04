# Ideal Dataset Specification

Generated 2026-04-02. Updated 2026-04-03 for v3 schema and backfill progress.

Defines the complete dataset the engine should capture in its ideal end state. All analyze procedure specs should be written against this dataset. Current-scope implementations reference this spec and stub any data not yet available.

---

## Implemented Schema (v2)

The following tables exist in `store/data/analytics/analytics.db` as of the v2 migration.

### `posts` — Universal TikTok Data

Any TikTok account would have these fields.

| Column | Type | Status | Tier |
|---|---|---|---|
| `post_id` | TEXT PK | Populated | — |
| `posted_date` | TEXT NOT NULL | Populated | — |
| `posted_time` | TEXT | **Stub (NULL)** | 2 — add to Phase 2 collect or discover enrichment |
| `description` | TEXT | Populated | — |
| `hashtags` | TEXT | Populated (44/45) | — |
| `content_type` | TEXT | Populated | — |
| `aweme_type` | INTEGER | Populated | — |
| `sound_name` | TEXT | **All NULL** | — (data exists in TikTok, not yet collected) |
| `sound_type` | TEXT | **Stub (NULL)** | 2 — tag during production or enrichment |
| `slide_count` | INTEGER | Populated | — |
| `content_path` | TEXT | Populated | — |
| `content_topics` | TEXT | **Stub (NULL)** | 2 — tag during production or classify from description |

### `nexus_post_metadata` — Company-Specific Data (v3 minimal)

Nexus content formula fields. Reduced to 5 columns in v3 — only fields with clear analytical value and a collection path.

| Column | Type | Status | Tier |
|---|---|---|---|
| `post_id` | TEXT PK FK→posts | Populated (45/45 rows) | — |
| `slug` | TEXT UNIQUE | Populated | — |
| `city` | TEXT | Partial (29/45) | — |
| `framework` | TEXT | Partial (7/45) | 1 — backfill needed |
| `slide_layout` | TEXT | Sparse (4/45) | 2 — classify during production (free text, not enum) |

Removed in v3: `hook_text` (content data, covered by carousel slide_texts), `hook_style` (unfunded classification), `angle` (redundant with framework), `format` (renamed to slide_layout), `cta_text` (moved to carousel_details), `content_topics` (moved to posts as universal).

### `carousel_details` — Content Subtype with Analysis Fields (v3)

| Column | Type | Status | Tier |
|---|---|---|---|
| `post_id` | TEXT PK FK→posts | Populated (27 rows) | — |
| `slide_texts` | TEXT | **Stub (NULL)** | 2 — JSON array, parsed from copy.md or transcribed from images |
| `visual_summary` | TEXT | **Stub (NULL)** | 2 — AI-generated from slide images |
| `has_cta` | INTEGER | **Stub (NULL)** | 2 — classify during production or from copy.md |
| `cta_type` | TEXT | **Stub (NULL)** | 2 — classify during production or from copy.md |
| `cta_text` | TEXT | **Stub (NULL)** | 2 — extract from copy.md or caption |

### `video_details` — Content Subtype

| Column | Type | Status | Tier |
|---|---|---|---|
| `post_id` | TEXT PK FK→posts | Populated (18 rows) | — |
| `duration_seconds` | REAL | **Stub (NULL)** | 2 — available from TikTok API |

### `readings` — Performance Metrics

| Column | Type | Status | Tier |
|---|---|---|---|
| `post_id` | TEXT FK→posts | Populated | — |
| `captured_at` | TEXT | Populated | — |
| `hours_since_post` | INTEGER | Populated | — |
| `type` | TEXT | Populated | — |
| `views` | INTEGER | Populated | — |
| `likes` | INTEGER | Populated | — |
| `comments` | INTEGER | Populated | — |
| `shares` | INTEGER | Populated | — |
| `bookmarks` | INTEGER | Populated | — |
| `new_followers` | INTEGER | Populated (snapshot only) | — |
| `avg_watch_time_seconds` | REAL | Populated (snapshot only) | — |
| `watched_full_percent` | REAL | Populated (snapshot only) | — |
| `fyp_percent` | REAL | Populated (snapshot only) | — |
| `profile_visits` | INTEGER | **Stub (NULL)** | 3 — add to snapshot collection |
| `search_percent` | REAL | **Stub (NULL)** | 3 — requires expanding Phase 2 collect |
| `profile_percent` | REAL | **Stub (NULL)** | 3 — requires expanding Phase 2 collect |
| `following_percent` | REAL | **Stub (NULL)** | 3 — requires expanding Phase 2 collect |
| `other_percent` | REAL | **Stub (NULL)** | 3 — requires expanding Phase 2 collect |

### `account` — Account Checkpoints

| Column | Type | Status | Tier |
|---|---|---|---|
| `captured_date` | TEXT PK | Populated (1 row) | — |
| `followers` | INTEGER | Populated | — |
| `total_likes` | INTEGER | Populated | — |

Ideal cadence: daily checkpoints (currently periodic, roughly weekly).

---

## Computed Metrics (Not Stored — Derived at Query Time)

| Metric | Formula | Description |
|---|---|---|
| `engagement_rate` | (likes + comments + shares) / views * 100 | Content quality signal |
| `save_rate` | bookmarks / views * 100 | Intent signal — strongest on TikTok |
| `follower_conversion` | new_followers / views * 1000 | Followers per 1K views |
| `total_play_time` | views * avg_watch_time_seconds | Aggregate attention captured |
| `non_fyp_rate` | 100 - fyp_percent | Return/search/profile audience |
| `posted_day_of_week` | derived from posted_date | Tier 1, always derivable |
| `caption_length_chars` | len(description) | Tier 1, always derivable |
| `caption_length_words` | word count of description | Tier 1, always derivable |
| `hashtag_count` | count of items in hashtags | Tier 1, always derivable |
| `days_since_previous_post` | posted_date sequence | Tier 1, always derivable |

---

## Content Artifacts (Filesystem, Not DB)

| Artifact | Location | Status |
|---|---|---|
| Slide images | `store/data/posts/{slug}/slides/` | Partial |
| Raw images | `store/data/posts/{slug}/raw-images/` | Engine-produced posts only |
| Visual summary | `store/data/posts/{slug}/visual-summary.md` | Partial |
| Copy | `store/data/posts/{slug}/copy.md` | Engine-produced posts only |
| README | `store/data/posts/{slug}/README.md` | Engine-produced posts only |
| Caption | `store/data/posts/{slug}/caption.md` | Some posts |

---

## Unpredictable Schema (Documented, Not Implemented)

These data structures are desired in the ideal state but their schemas are not yet clear enough to implement as tables.

### Per-Slide Completion Data

**Purpose:** Identify where viewers drop off in carousels. Per-slide view-through rates would reveal which slides lose attention.

**Blocked by:** TikTok may not expose per-slide completion data through Studio or API. Schema depends on what data format TikTok provides.

**Possible table:**
```
slide_metrics (
    post_id TEXT FK→posts,
    slide_position INTEGER,
    view_count INTEGER,
    view_through_rate REAL,
    PRIMARY KEY (post_id, slide_position)
)
```

### Comment / Engagement Quality Data

**Purpose:** Audience intent signals, sentiment analysis, question detection.

**Blocked by:** Collection method undecided (API scraping vs. Studio extraction vs. manual). Volume and storage implications unclear. Sentiment analysis method not chosen.

**Possible tables:**
```
comments (
    comment_id TEXT PRIMARY KEY,
    post_id TEXT FK→posts,
    text TEXT,
    created_at TEXT,
    likes INTEGER
)

comment_analysis (
    post_id TEXT PK FK→posts,
    positive_count INTEGER,
    negative_count INTEGER,
    question_count INTEGER,
    sentiment_score REAL
)
```

### Competitor / Benchmark Data

**Purpose:** Context for "what good looks like" — relative performance against similar accounts.

**Blocked by:** No automated collection method. Manual observation doesn't produce structured data. Schema depends on what's observable.

**Not designed.** Will revisit when a collection method is identified.

---

## Acquisition Tier Definitions

| Tier | Definition | Examples |
|---|---|---|
| **Tier 1** | Derivable from existing data with no new collection. | `posted_day_of_week`, `caption_length_words`, `hashtag_count` |
| **Tier 2** | Capturable with minor collection changes. | `posted_time`, `sound_type`, `slide_layout`, `cta_type/text`, `duration_seconds`, `slide_texts`, `visual_summary`, `content_topics` |
| **Tier 3** | Requires new collection infrastructure. | `profile_visits`, comment data, per-slide completion |
| **Tier 4** | External data for context. Not from the TikTok account. | Competitor benchmarks, trending sounds, seasonal demand |

## Classification Gaps

7 of 45 posts have `framework` populated. 4 have `slide_layout`. 29 have `city`. Full classification of framework and slide_layout requires manual tagging or AI-assisted classification from content artifacts (copy.md, description, slide images).

Carousel content fields (slide_texts, visual_summary, has_cta, cta_type, cta_text) are all NULL. Population requires reading copy.md (where available) or transcribing/analyzing slide images.

## Current Data Snapshot

> **Note:** This snapshot is updated periodically during development. The database was stripped and rebuilt from scratch on 2026-04-03 for E2E backfill testing. Numbers below reflect the backfill in progress.

**As of 2026-04-03 (backfill in progress):**

- **Posts:** 47 (28 carousels, 19 videos). Date range: 2025-09-16 to 2026-04-01.
- **Readings:** 0 (backfill Phase 4 not yet run).
- **Account checkpoints:** 0 (backfill Phase 4 not yet run).
- **Nexus metadata:** 47/47 with slug (description-based), city coverage TBD after backfill.
- **Carousel details:** 28 rows. Slide downloads in progress (Phase 2). Content fields NULL pending derive (Phase 3).
- **Enrichment:** posted_time 47/47, sound_name 47/47, duration_seconds 19/19 videos, description partially populated (enrichment in progress).

**Pre-backfill reference data** preserved at `tmp/backfill-reference/` (45 posts, 45 readings, 1 checkpoint from 2026-04-01).
