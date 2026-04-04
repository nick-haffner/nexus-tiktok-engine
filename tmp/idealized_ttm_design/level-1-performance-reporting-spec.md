# Level 1: Performance Reporting — Idealized Specification

Generated 2026-04-02. Approved proposal for the Level 1 analyze procedure.

> **Scope:** This spec is idealized — it assumes access to the full dataset defined in `tmp/idealized_ttm_design/ideal-dataset-spec.md`. Current-scope queries (with stubs for unavailable data) are appended at the end. The procedure document written from this spec will implement the current-scope queries while preserving the idealized output structure so that new data sources slot in without redesign.

---

## Stated Goals

1. **Establish account health at a glance.** The primary consumer of this report is the manager (or marketing team) who needs to know in under 60 seconds whether the account is on track, improving, or declining. This mirrors the "first 5 minutes of the weekly meeting" role described in the conversion doc.

2. **Surface anomalies — both positive and negative.** Outlier posts (significantly above or below baseline) require attention. A breakout post should be analyzed for replicable variables. An underperformer should be flagged before a pattern forms. Industry standard: agencies flag any post that deviates more than 2x from the trailing median in either direction.

3. **Track trajectory, not just snapshots.** A single week's numbers are meaningless without trend context. The report must show period-over-period deltas so the reader can distinguish "bad week in a good trend" from "bad week confirming a decline." This is the difference between noise and signal.

4. **Provide the baseline that Level 2 and Level 6 build on.** Level 1 doesn't make content strategy decisions — it produces the performance context those decisions require. If Level 1 surfaces a decline, Level 2 investigates what's causing it. If Level 1 shows growth, Level 6 codifies what's working.

5. **Track account growth as a first-class metric alongside content performance.** Follower count, total likes, and growth rates are account-level health indicators independent of any single post. Industry standard: growth-phase accounts (sub-10K) track follower acquisition rate as the primary success metric, not aggregate views.

---

## Inputs

| Input | Source | Purpose |
|---|---|---|
| `readings` table | `store/data/analytics/analytics.db` | All performance metrics per post per snapshot window |
| `posts` table | `store/data/analytics/analytics.db` | Post metadata (posted_date, content_type, city, slide_count, framework, angle) for context on per-post rows |
| `account` table | `store/data/analytics/analytics.db` | Follower and total likes checkpoints for growth tracking |
| **Reporting period** | Parameter (default: trailing 7 days) | Defines "this period" for the report. Also determines the comparison period (the equivalent-length window immediately prior) |

**Important distinction:** The reporting period defines two scopes:

- **Posts published this period** — new content performance (how did this week's posts do?)
- **Readings captured this period** — measurement updates on older posts (did the Seattle post's 7d snapshot come in?)

Both matter. A week with no new posts still produces a report if readings arrived for existing posts or if account checkpoints were captured.

---

## Outputs

### Structured Data Layer

The procedure produces a structured intermediate representation (JSON or Python dict) containing all computed metrics, tables, and flags. This is the single source of truth for the report. All renderers (Markdown, HTML dashboard, or future formats) consume this structure — they never query the database directly.

The structured output contains five sections:

**Section 1: Executive Summary**
- `health_status`: enum (`strong`, `steady`, `declining`, `insufficient_data`)
- `summary_text`: string (2-3 sentence plain-language verdict)
- `period_start`, `period_end`: ISO dates

**Section 2: Aggregate Metrics Dashboard**

Key-value pairs with period comparison:

| Field | Type | Description |
|---|---|---|
| `posts_published` | `{current, previous, delta}` | Count of posts published in each period |
| `total_views` | `{current, previous, delta_pct}` | Sum of views for period posts |
| `median_views` | `{current, previous, delta_pct}` | Median views per post |
| `mean_engagement_rate` | `{current, previous, delta_pp}` | (likes + comments + shares) / views |
| `mean_save_rate` | `{current, previous, delta_pp}` | bookmarks / views |
| `total_new_followers` | `{current, previous, delta}` | Sum from snapshot readings |
| `mean_profile_visits` | `{current, previous, delta}` | Average profile visits per post |
| `mean_non_fyp_rate` | `{current, previous, delta_pp}` | Average non-FYP traffic percentage (return/search/profile audience) |
| `all_time` | object | All-time values for each metric above |

*Why median and mean:* At sub-1K followers with occasional viral posts, mean views are skewed. Median is the true baseline. Both are reported; the executive summary references median.

*Why engagement rate and save rate but not raw likes/comments/shares:* Raw counts scale with views. Rates normalize for reach and reveal content quality independent of distribution. Industry standard: agencies report rates for quality assessment and raw counts only for reach/scale assessment.

**Section 3: Account Growth**

| Field | Type | Description |
|---|---|---|
| `followers` | `{current, previous, delta, growth_rate_pct}` | From account table checkpoints |
| `total_likes` | `{current, previous, delta, growth_rate_pct}` | From account table checkpoints |
| `followers_per_post` | float | Followers gained / posts published this period |
| `followers_per_1k_views` | float | Across this period's snapshot readings |
| `growth_curve` | array | Daily follower counts within the period (from daily checkpoints) |
| `profile_visit_total` | `{current, previous, delta}` | Sum of profile visits across period posts |

*Industry standard: growth-phase accounts track "cost per follower" even for organic — expressed as effort (posts) per follower gained. This determines whether the content strategy is building an audience or just generating impressions. Daily growth curves reveal whether growth is post-driven (spikes on post days) or organic (steady baseline), informing cadence decisions.*

**Section 4: Per-Post Performance Table**

Array of objects, one per reading captured this period, sorted by views descending:

| Field | Type | Description |
|---|---|---|
| `post_id` | string | TikTok post ID |
| `slug` | string or null | Human-readable identifier |
| `published` | ISO date | posted_date |
| `posted_time` | time or null | Publication time (HH:MM) |
| `posted_day_of_week` | string | Monday-Sunday |
| `age_days` | int | Days since published |
| `views` | int | |
| `engagement_rate` | float | % |
| `save_rate` | float | % |
| `new_followers` | int or null | Snapshot only |
| `profile_visits` | int or null | Profile visits from this post |
| `fyp_percent` | float or null | % of views from FYP |
| `non_fyp_percent` | float or null | % from search, profile, following, other |
| `reading_type` | string | `snapshot` or `velocity` |
| `is_new` | bool | Published this period |
| `outlier` | enum or null | `high` (>2x median), `low` (<0.5x median), or null |

*Industry standard: the per-post table is the core artifact. Agencies use it to identify which specific posts to discuss. Without it, the meeting devolves into generalities.*

**Section 5: Anomalies & Flags**

Array of typed flag objects:

| Field | Type | Description |
|---|---|---|
| `type` | enum | `overdue_reading`, `overdue_checkpoint`, `metric_divergence`, `data_integrity`, `cadence_gap`, `audience_shift` |
| `severity` | enum | `info`, `warning`, `critical` |
| `message` | string | Human-readable description |
| `post_id` | string or null | Relevant post, if applicable |

Flag types include:
- `overdue_reading` — post past its snapshot window with no reading
- `overdue_checkpoint` — account checkpoint overdue (>7 days)
- `metric_divergence` — high views but low engagement, or inverse (algorithmic push without resonance)
- `data_integrity` — views decreased between readings
- `cadence_gap` — posting gap exceeds threshold
- `audience_shift` — significant change in non-FYP traffic percentage (indicates growing or shrinking return audience)

*Industry standard: agencies call this the "watch list." It's not actionable yet — it's a prompt for discussion or deeper investigation in Level 2.*

### Rendering Layer

A separate step consumes the structured output and produces the human-readable report. The default renderer outputs Markdown. Future renderers (HTML dashboard, PDF) consume the same structure.

The Markdown report is stored in `analyze/outputs/` with a datestamped filename (e.g., `level-1-performance-2026-04-02.md`). The structured data is stored alongside it (e.g., `level-1-performance-2026-04-02.json`). Both are available as inputs for Level 2 and Level 6.

---

## Procedure Overview

**Step 1 — Determine reporting period**

Accept a reporting period parameter or default to trailing 7 days from today. Compute the comparison period (equivalent-length window immediately prior). Compute all-time bounds.

**Step 2 — Query aggregate metrics**

Run the dashboard queries against `readings` and `posts` tables for both the current and comparison periods. Compute engagement rate, save rate, and follower acquisition metrics. Compute medians and means.

**Step 3 — Query account growth**

Pull the most recent and previous account checkpoints from the `account` table. Compute deltas and growth rates. Flag if checkpoint is overdue.

**Step 4 — Build per-post table**

Query all readings captured in the current period, joined with post metadata. Compute per-post rates. Sort by views. Flag outliers against the trailing median (computed from all-time data, not just this period, to avoid small-sample distortion).

**Step 5 — Detect anomalies**

Run anomaly checks: overdue readings, overdue checkpoints, metric divergences, data integrity issues, cadence gaps. Collect into the flags list.

**Step 6 — Generate executive summary**

Based on the aggregate deltas and anomaly flags, produce the health status enum and 2-3 sentence summary text. This is generated last because it synthesizes all prior sections.

**Step 7 — Assemble structured output**

Compile all sections into the structured intermediate representation (JSON/dict). This is the canonical output of Level 1.

**Step 8 — Render**

Pass the structured output to the default renderer (Markdown). Store both the structured data and the rendered report in `analyze/outputs/`.

---

## Current-Scope Query Definitions

These queries implement the idealized spec above against the v2 database schema (post-migration). Fields from the idealized output that are not yet available are stubbed as null. Company-specific metadata is in `nexus_post_metadata`, joined via LEFT JOIN so posts without metadata are included with NULL values.

All queries reference the actual schema in `store/data/analytics/analytics.db`. See `tmp/schema-v3-overview.md` for the full schema diagram. All connections must set `PRAGMA foreign_keys=ON`.

**Stubs for unavailable data:**
- `posted_time` → null (not captured; add to collection when available)
- `profile_visits` → null (not captured; requires expanding Phase 2 collect)
- `search_percent`, `profile_percent`, `following_percent`, `other_percent` → null (not captured; only `fyp_percent` available)
- `growth_curve` → empty array (requires daily account checkpoints; only periodic checkpoints exist)
- `mean_profile_visits`, `profile_visit_total` → null
- `audience_shift` anomaly type → not evaluated until traffic source data is available
- `comment_sentiment`, `slide_completion_by_position` → null (Tier 3; not relevant to Level 1 but noted for completeness)
- `posted_day_of_week` → derived in Python from `posted_date` (Tier 1; available now)
- `non_fyp_percent` → derived in Python from `fyp_percent` where available, null otherwise

**Note on data sparsity:** As of 2026-04-01, all 45 readings were captured on a single day and there is 1 account checkpoint. Queries must handle periods with zero posts, zero readings, or zero account checkpoints gracefully — returning nulls or empty sets, not errors.

### Step 1 — Reporting Period Computation

No query. Pure date arithmetic:
- `period_end` = today (or parameter)
- `period_start` = `period_end` - period length (default 7 days)
- `comparison_end` = `period_start`
- `comparison_start` = `comparison_end` - period length

### Step 2 — Aggregate Metrics

**2a. Posts published in period:**
```sql
SELECT COUNT(*) as post_count
FROM posts
WHERE posted_date >= :period_start AND posted_date < :period_end;
```
Run twice: once for current period, once for comparison period. Run once with no date filter for all-time.

**2b. Views and engagement for posts published in period:**
```sql
SELECT
    SUM(r.views) as total_views,
    AVG(r.views) as mean_views,
    SUM(r.likes) as total_likes,
    SUM(r.comments) as total_comments,
    SUM(r.shares) as total_shares,
    SUM(r.bookmarks) as total_bookmarks,
    SUM(r.new_followers) as total_new_followers
FROM readings r
JOIN posts p ON r.post_id = p.post_id
WHERE p.posted_date >= :period_start AND p.posted_date < :period_end;
```
Run twice for current and comparison periods. Run once for all-time.

**2c. Median views per post (period posts):**
```sql
SELECT r.views
FROM readings r
JOIN posts p ON r.post_id = p.post_id
WHERE p.posted_date >= :period_start AND p.posted_date < :period_end
ORDER BY r.views;
```
Median computed in Python from the sorted result set (SQLite has no native MEDIAN). If zero rows, median is null.

**2d. Engagement rate and save rate (computed in Python, not SQL):**
```
engagement_rate = (total_likes + total_comments + total_shares) / total_views * 100
save_rate = total_bookmarks / total_views * 100
```
Guard against division by zero when total_views is 0 or null.

### Step 3 — Account Growth

**3a. Account checkpoints in/near period:**
```sql
SELECT captured_date, followers, total_likes
FROM account
WHERE captured_date <= :period_end
ORDER BY captured_date DESC
LIMIT 2;
```
Returns the most recent checkpoint and (if it exists) the previous one. If only 1 row exists, comparison values are null. If 0 rows, the entire account growth section is null.

**3b. Follower acquisition efficiency (computed in Python):**
```
followers_per_post = (current_followers - previous_followers) / posts_published_current
followers_per_1k_views = total_new_followers / total_views * 1000
```
Both guard against division by zero.

### Step 4 — Per-Post Table

**4a. All readings captured in the current period:**
```sql
SELECT
    r.post_id,
    n.slug,
    p.posted_date,
    r.captured_at,
    r.hours_since_post,
    r.type,
    r.views,
    r.likes,
    r.comments,
    r.shares,
    r.bookmarks,
    r.new_followers,
    r.avg_watch_time_seconds,
    r.watched_full_percent,
    r.fyp_percent,
    n.city,
    n.framework,
    p.content_type,
    p.slide_count
FROM readings r
JOIN posts p ON r.post_id = p.post_id
LEFT JOIN nexus_post_metadata n ON r.post_id = n.post_id
WHERE r.captured_at >= :period_start AND r.captured_at < :period_end
ORDER BY r.views DESC;
```
Per-post engagement_rate, save_rate, is_new, and age_days computed in Python.

**4b. Trailing median for outlier detection:**
```sql
SELECT r.views
FROM readings r
ORDER BY r.views;
```
All-time median, not period-scoped. A post is flagged `outlier_high` if views > 2x this median, `outlier_low` if views < 0.5x this median.

### Step 5 — Anomaly Detection

**5a. Posts overdue for readings:**
```sql
SELECT p.post_id, n.slug, p.posted_date,
       CAST((julianday('now') - julianday(p.posted_date)) * 24 AS INTEGER) as hours_old
FROM posts p
LEFT JOIN nexus_post_metadata n ON p.post_id = n.post_id
WHERE NOT EXISTS (
    SELECT 1 FROM readings r WHERE r.post_id = p.post_id
)
AND julianday('now') - julianday(p.posted_date) > 2.0;
```
Any post older than 48 hours with zero readings is flagged.

**5b. Account checkpoint overdue:**
```sql
SELECT MAX(captured_date) as last_checkpoint
FROM account;
```
If `last_checkpoint` is more than 7 days before `period_end`, flag as overdue.

**5c. Metric divergence (high views, low engagement):**
Computed in Python from the per-post table. Flag any post where views > trailing median AND engagement_rate < 0.5 * trailing mean engagement rate.

**5d. Views decrease between readings (data integrity):**
```sql
SELECT r1.post_id, n.slug, r1.views as earlier_views, r2.views as later_views
FROM readings r1
JOIN readings r2 ON r1.post_id = r2.post_id AND r1.captured_at < r2.captured_at
LEFT JOIN nexus_post_metadata n ON r1.post_id = n.post_id
WHERE r2.views < r1.views;
```

**5e. Cadence gaps:**
```sql
SELECT posted_date,
       CAST(julianday(posted_date) - julianday(LAG(posted_date) OVER (ORDER BY posted_date)) AS INTEGER) as gap_days
FROM posts
ORDER BY posted_date DESC
LIMIT 10;
```
Flag any gap exceeding a threshold (e.g., 7 days). The threshold may be configurable.

---

## Alignment Notes

- **Structured data before rendering**: The procedure separates query/computation logic (Steps 1-7) from presentation (Step 8). Swapping or adding renderers (HTML dashboard, PDF) means adding a renderer, not modifying the procedure.
- **Output storage in `analyze/outputs/`**: Reports are analysis artifacts, not data. They don't belong in `store/data/` because they're derived, not collected. They live in `analyze/` because they're produced by and consumed within the analyze function.
- **No strategic recommendations in Level 1**: This is intentional. Level 1 reports facts and flags anomalies. It does not say "post more" or "change frameworks." That discipline keeps Level 1 fast, reliable, and unopinionated — the foundation the opinionated levels build on.
