# Analytics Database Schema (v3)

**Location:** `store/data/analytics/analytics.db` (SQLite)
**Interface:** Python `sqlite3` module
**Migrated:** v2 (2026-04-02), v3 (2026-04-03)

## Architecture

The schema separates universal TikTok data from company-specific metadata and distinguishes content subtypes.

```
posts (universal)
├── nexus_post_metadata (company-specific, joined on post_id)
├── carousel_details (subtype with content analysis fields, joined on post_id)
├── video_details (subtype stub, joined on post_id)
readings (universal, transient)
account (universal, transient)
```

## Data Classification

**Permanent data** — static post metadata and content analysis. One row per post, updated in place. Tables: `posts`, `nexus_post_metadata`, `carousel_details`, `video_details`.

**Transient data** — point-in-time measurements. One row per observation, never updated. Tables: `readings`, `account`.

## Tables

### `posts` — Universal TikTok Data

Any TikTok account would have these fields.

```sql
CREATE TABLE posts (
    post_id        TEXT PRIMARY KEY,
    posted_date    TEXT NOT NULL,      -- ISO 8601 (YYYY-MM-DD)
    posted_time    TEXT,               -- HH:MM+00:00 (stub — collected via API create_time)
    description    TEXT,               -- Full caption text
    hashtags       TEXT,               -- Comma-separated, # stripped
    content_type   TEXT,               -- "carousel", "video", or "photo"
    aweme_type     INTEGER,            -- TikTok's raw content type code
    sound_name     TEXT,               -- Audio track name
    sound_type     TEXT,               -- "trending", "original", "licensed" (stub)
    slide_count    INTEGER,            -- Number of slides (carousels) or 1 (videos)
    content_path   TEXT,               -- Relative path to post content directory
    content_topics TEXT                -- Comma-separated topic tags (stub)
);
```

### `nexus_post_metadata` — Company-Specific Data

Nexus content formula fields. Minimal model — only fields with clear analytical value and a path to population.

```sql
CREATE TABLE nexus_post_metadata (
    post_id      TEXT PRIMARY KEY REFERENCES posts(post_id),
    slug         TEXT UNIQUE,       -- e.g. "nashville-2026-03-30"
    city         TEXT,              -- Target city
    framework    TEXT,              -- "local_vs_tourist", "worth_it", "the_24_hour_test", etc.
    slide_layout TEXT               -- "combined", "split", "single_point", or other (free text)
);
```

`slide_layout` is free text with documented conventions, not an exhaustive enum. New layout types are expected as content strategy evolves. Classification requires judgment.

### `carousel_details` — Content Subtype with Analysis Fields

One row per carousel post. Contains content analysis data specific to carousels.

```sql
CREATE TABLE carousel_details (
    post_id        TEXT PRIMARY KEY REFERENCES posts(post_id),
    slide_texts    TEXT,        -- JSON array of per-slide text content
    visual_summary TEXT,        -- AI description of visual style, layout, progression
    has_cta        INTEGER,     -- 0 or 1 (does a slide carry a CTA)
    cta_type       TEXT,        -- "waitlist", "website", "follow", "engage", or other
    cta_text       TEXT         -- The actual CTA string from the CTA slide
);
```

`slide_texts` format: `["Slide 1 text here", "Slide 2 text here", ...]`. Parsed from `copy.md` slide headings or transcribed from slide images.

### `video_details` — Content Subtype

Stub table for video-specific data.

```sql
CREATE TABLE video_details (
    post_id          TEXT PRIMARY KEY REFERENCES posts(post_id),
    duration_seconds REAL             -- Collected via API (video_info.video.duration)
);
```

### `readings` — Point-in-Time Performance

Transient data. New row per observation, never updated.

```sql
CREATE TABLE readings (
    post_id                TEXT NOT NULL REFERENCES posts(post_id),
    captured_at            TEXT NOT NULL,   -- ISO 8601 with UTC offset (+00:00)
    hours_since_post       INTEGER NOT NULL,
    type                   TEXT NOT NULL,   -- Cadence label: 'daily', 'weekly', 'mature', 'backfill', or 'reading' (on-demand). Legacy: '48h', '7d', '30d', 'early'.
    views                  INTEGER NOT NULL,
    likes                  INTEGER NOT NULL,
    comments               INTEGER NOT NULL,
    shares                 INTEGER NOT NULL,
    bookmarks              INTEGER NOT NULL,
    new_followers          INTEGER,         -- Snapshot only
    avg_watch_time_seconds REAL,            -- Snapshot only
    watched_full_percent   REAL,            -- Snapshot only
    fyp_percent            REAL,            -- Snapshot only
    profile_visits         INTEGER,         -- Stub (page-level metric, not in API)
    search_percent         REAL,            -- Collected via API traffic sources
    profile_percent        REAL,            -- Collected via API traffic sources
    following_percent      REAL,            -- Collected via API traffic sources
    other_percent          REAL,            -- Collected via API traffic sources
    PRIMARY KEY (post_id, captured_at)
);
```

### `account` — Account-Level State

Transient data. One checkpoint per day.

```sql
CREATE TABLE account (
    captured_date TEXT PRIMARY KEY,
    followers     INTEGER NOT NULL,
    total_likes   INTEGER NOT NULL
);
```

## Idempotency

### Permanent data (posts, nexus_post_metadata, carousel_details, video_details)

**Rule: insert if new, update null fields if existing. Never overwrite non-null values.**

The discover script implements this via `register_post` and `enrich_from_api`. Safe to run repeatedly — subsequent runs report "unchanged" when no null fields can be filled.

### Transient data (readings, account)

**Rule: insert always. Every observation is a new row.**

The triage system prevents redundant readings by not surfacing posts that already have a recent reading within their cadence tier (6h for hyper-early, 12h for daily, 7 days for weekly, once for mature). Account checkpoints use `captured_date` as PK — one per day, duplicates caught by IntegrityError.

## Timestamps

All stored timestamps use UTC with explicit offset:
- `captured_at`: `YYYY-MM-DDTHH:MM:SS+00:00`
- `captured_date`: `YYYY-MM-DD` (UTC)
- `posted_date`: `YYYY-MM-DD` (UTC)
- `posted_time`: `HH:MM+00:00` (derived from API `create_time` unix timestamp)

Pre-v2 readings lack the `+00:00` suffix but are still UTC.

## Computed Metrics

Not stored. Compute at query time:

| Metric | Formula |
|---|---|
| Engagement rate | `(likes + comments + shares) * 100.0 / views` |
| Save rate | `bookmarks * 100.0 / views` |
| Followers per 1K views | `new_followers * 1000.0 / views` |
| Non-FYP rate | `100 - fyp_percent` |

## Generalizability

| Component | Generalizable? | Notes |
|---|---|---|
| `posts` table | Yes | Universal TikTok fields |
| `nexus_post_metadata` | No | Nexus content formula. Replace for other accounts. |
| `carousel_details` | Mostly | CTA and visual fields apply to any carousel account. `slide_texts` format is universal. |
| `video_details` | Yes | Duration is universal |
| `readings` table | Yes | Schema-agnostic to content type |
| `account` table | Yes | Any TikTok account |

## Data Population — Procedure Responsibilities

Each field in the database is owned by one of four store procedures:

| Procedure | Data Type | Tables Written | Scope |
|---|---|---|---|
| **Discover Posts** | Permanent (captured) | `posts`, `nexus_post_metadata`, subtype rows, enrichment fields (sound_name, posted_time, duration) | Register posts + enrich from API |
| **Capture Content** | Permanent (captured) | `carousel_details.slide_texts`, slide images on filesystem | Download slide images, extract slide text |
| **Derive Data** | Permanent (derived) | `carousel_details` (visual_summary, has_cta, cta_type, cta_text), `nexus_post_metadata` (framework, slide_layout), `posts` (content_topics) | Classify and analyze content |
| **Capture Reading** | Transient | `readings`, `account` | Collect point-in-time performance metrics |

The first three procedures handle permanent data — facts about the post that don't change. Discover posts and capture content capture data directly from TikTok. Derive data produces classifications and analysis from already-captured content.

Capture reading is the only procedure that handles transient data — point-in-time measurements that produce a new row on every run.

After all four procedures have run for a post, every non-stub field is populated.

## Reading Cadence

All readings capture all metrics. The `type` field records which cadence tier triggered the capture — this controls *when* to read, not *what* to read.

| Type | Post age | Cadence | Purpose |
|---|---|---|---|
| `daily` | 0–3 days (0–72h) | Every 6h | Algorithm actively testing. Growth curve steepest. |
| `daily` | 3–7 days (72–168h) | Every 12h | Distribution settling. Daily check-in. |
| `weekly` | 7–30 days (168–720h) | Every 7 days | Monitors for second-wave distribution. |
| `mature` | 30 days (720h) | Once | Lifetime baseline capstone. |
| `backfill` | Any age ≤30d, no prior readings | Once | Catch-up for posts registered after their active window passed. |
| `reading` | Any (on-demand) | User-triggered | Requested via `/store-update for`. |

Legacy type values (`early`, `48h`, `7d`, `30d`) may exist in readings captured before 2026-04-04. These are valid readings — the type label changed but the data is the same.

A post's first reading is typically captured at 6–12h via `/store-update for` immediately after publishing. The daily triage cycle then picks it up on its next run.

## Connection Requirements

```python
conn = sqlite3.connect("store/data/analytics/analytics.db")
conn.execute("PRAGMA foreign_keys=ON")
```

## Content on Filesystem

```
store/data/posts/{slug}/
  slides/              # Slide images or cover thumbnail (capture content)
  raw-images/          # Source images (engine-produced only, generate procedure)
  copy.md              # Slide copy (engine-produced only, generate procedure)
  README.md            # Production metadata (generate_artifacts.py or generate procedure)
  caption.md           # Posted caption (generate_artifacts.py from description field)
  visual-summary.md    # AI visual description (derive procedure)
```
