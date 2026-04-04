# Level 1: Performance Reporting

Produces a structured performance report covering account health, post performance, growth trajectory, and anomaly detection. This is the foundation for Level 2 (Content Strategy Analysis) and Level 6 (Strategic Synthesis).

**Idealized spec:** `tmp/idealized_ttm_design/level-1-performance-reporting-spec.md`

## When to Run

- **Weekly** as part of the standard analyze cadence.
- **On demand** when the manager wants a performance check outside the regular cadence.

## Inputs

| Input | Location | Required |
|---|---|---|
| Analytics database | `store/data/analytics/analytics.db` | Yes |
| Reporting period | Parameter (default: trailing 7 days) | Yes |

The database contains six tables: `posts` (universal metadata), `nexus_post_metadata` (company-specific), `carousel_details`, `video_details`, `readings` (performance snapshots), and `account` (follower/likes checkpoints). All connections must set `PRAGMA foreign_keys=ON`.

## Outputs

| Output | Location | Format |
|---|---|---|
| Structured report data | `analyze/outputs/level-1-performance-YYYY-MM-DD.json` | JSON |
| Data report | `analyze/outputs/level-1-performance-YYYY-MM-DD.md` | Markdown |
| Insight brief | `analyze/outputs/level-1-insights-YYYY-MM-DD.md` | Markdown |

All three are produced on every run. The JSON is the canonical data consumed by Levels 2-6. The data report is the human-readable rendering of tables and flags. The insight brief is natural language interpretation of the data for manager review — it tells you what the numbers mean, not just what they are.

## Procedure

### Step 1 — Determine Reporting Period

Accept a reporting period parameter or default to trailing 7 days from today.

Compute:
- `period_start` and `period_end` — the current reporting window
- `comparison_start` and `comparison_end` — the equivalent-length window immediately prior
- All-time bounds — no date filter

Report to console: "Reporting period: {period_start} to {period_end}. Comparison: {comparison_start} to {comparison_end}."

### Step 2 — Query Aggregate Metrics

Run `analyze/scripts/level_1_report.py --step aggregates` or execute the following queries manually:

**Posts published** in each period:
```sql
SELECT COUNT(*) as post_count
FROM posts
WHERE posted_date >= :period_start AND posted_date < :period_end;
```

**Views and engagement** for posts published in each period:
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

**Median views** per post (computed in Python — SQLite has no native MEDIAN):
```sql
SELECT r.views
FROM readings r
JOIN posts p ON r.post_id = p.post_id
WHERE p.posted_date >= :period_start AND p.posted_date < :period_end
ORDER BY r.views;
```

Run each query three times: current period, comparison period, all-time (no date filter).

Compute in Python:
- `engagement_rate = (total_likes + total_comments + total_shares) / total_views * 100`
- `save_rate = total_bookmarks / total_views * 100`
- Period-over-period deltas (absolute and percentage)

Guard against division by zero when total_views is 0 or null.

**Stubbed fields** (null until data becomes available):
- `mean_profile_visits` — requires `profile_visits` in readings (Tier 3)
- `mean_non_fyp_rate` — derivable from `fyp_percent` where available; null for posts without snapshot data

### Step 3 — Query Account Growth

```sql
SELECT captured_date, followers, total_likes
FROM account
WHERE captured_date <= :period_end
ORDER BY captured_date DESC
LIMIT 2;
```

If 2 rows returned: compute deltas and growth rates between them.
If 1 row: report current values, comparison values are null.
If 0 rows: entire account growth section is null.

Compute:
- `followers_per_post = follower_delta / posts_published_current`
- `followers_per_1k_views = total_new_followers / total_views * 1000`

Guard against division by zero.

**Stubbed fields:**
- `growth_curve` — empty array (requires daily checkpoints; currently periodic)
- `profile_visit_total` — null (Tier 3)

### Step 4 — Build Per-Post Table

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

For each row, compute in Python:
- `age_days = (period_end - posted_date).days`
- `posted_day_of_week = posted_date.strftime('%A')`
- `engagement_rate = (likes + comments + shares) / views * 100`
- `save_rate = bookmarks / views * 100`
- `non_fyp_percent = 100 - fyp_percent` (where fyp_percent is not null)
- `is_new = posted_date >= period_start`

**Outlier detection** — compute trailing all-time median:
```sql
SELECT r.views
FROM readings r
ORDER BY r.views;
```

Flag each post:
- `outlier: "high"` if views > 2x trailing median
- `outlier: "low"` if views < 0.5x trailing median
- `outlier: null` otherwise

**Stubbed fields per row:**
- `posted_time` — null (Tier 2)
- `profile_visits` — null (Tier 3)

### Step 5 — Detect Anomalies

Run each check and collect results into a typed flags array.

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
Flag type: `overdue_reading`, severity: `warning`.

**5b. Account checkpoint overdue:**
```sql
SELECT MAX(captured_date) as last_checkpoint
FROM account;
```
If `last_checkpoint` is more than 7 days before `period_end`: flag type `overdue_checkpoint`, severity `warning`.

**5c. Metric divergence** (high views, low engagement):
From the per-post table, flag any post where `views > trailing_median` AND `engagement_rate < 0.5 * trailing_mean_engagement_rate`.
Flag type: `metric_divergence`, severity: `info`.

**5d. Data integrity — views decrease between readings:**
```sql
SELECT r1.post_id, n.slug, r1.views as earlier_views, r2.views as later_views
FROM readings r1
JOIN readings r2 ON r1.post_id = r2.post_id AND r1.captured_at < r2.captured_at
LEFT JOIN nexus_post_metadata n ON r1.post_id = n.post_id
WHERE r2.views < r1.views;
```
Flag type: `data_integrity`, severity: `critical`.

**5e. Cadence gaps:**
```sql
SELECT posted_date,
       CAST(julianday(posted_date) - julianday(LAG(posted_date) OVER (ORDER BY posted_date)) AS INTEGER) as gap_days
FROM posts
ORDER BY posted_date DESC
LIMIT 10;
```
Flag any gap exceeding 7 days. Flag type: `cadence_gap`, severity: `info`.

**Stubbed anomaly types:**
- `audience_shift` — not evaluated until traffic source breakdown is available (Tier 3).

### Step 5b — Assess Data Coverage

Query `nexus_post_metadata` to determine classification coverage for each field (framework, angle, format, city, hook_text, hook_style, cta_text, content_topics). List all columns in `posts` and `readings` that are stubbed (all NULL). Report account checkpoint count. This section appears in the output as "Data Coverage" so the consumer knows what data is missing and how it affects analysis reliability.

### Step 6 — Generate Executive Summary

Based on the aggregate deltas and anomaly flags, produce:

- `health_status`: one of `strong`, `steady`, `declining`, `insufficient_data`
- `summary_text`: 2-3 sentence plain-language verdict

Logic:
- `strong` — median views up >10% WoW AND no critical flags
- `steady` — median views within +/-10% WoW AND no critical flags
- `declining` — median views down >10% WoW OR critical flags present
- `insufficient_data` — fewer than 2 posts with readings in the current period

The summary text should reference specific numbers: "Median views up 25% WoW (X → Y). 3 posts published, 1 flagged as outlier high. Follower growth: +Z."

### Step 7 — Assemble Structured Output

Compile all sections into a single JSON object:

```json
{
  "report_type": "level_1_performance",
  "generated_at": "ISO datetime",
  "period": { ... },
  "executive_summary": { "health_status": "...", "summary_text": "..." },
  "aggregate_metrics": { ... },
  "account_growth": { ... },
  "per_post_table": [ ... ],
  "anomalies": [ ... ],
  "missing_data": { ... }
}
```

This is the canonical output of Level 1. Write to `analyze/outputs/level-1-performance-YYYY-MM-DD.json`.

### Step 8 — Render

Pass the structured output to the Markdown renderer. The renderer produces a human-readable report with:

- Executive summary as a header block
- Aggregate metrics as a comparison table
- Account growth as a summary table
- Per-post table as a sortable Markdown table (outliers marked with indicators)
- Anomalies as a bulleted list grouped by severity

Write to `analyze/outputs/level-1-performance-YYYY-MM-DD.md`.

Report to console: "Level 1 report generated: analyze/outputs/level-1-performance-YYYY-MM-DD.md"

### Step 9 — Generate Insight Brief

Read the JSON output from Step 7. For each section of the insight brief, analyze the corresponding data and produce natural language interpretation. Target length: 300-500 words.

**Section 1 — Health Interpretation** (2-3 sentences): Interpret the health status in context. Not just the label — why, what's sustaining it, what's threatening it. Reference specific deltas. Determine whether the team is in "optimize" or "course correct" mode.

**Section 2 — Volume vs. Quality** (2-3 sentences): Compare `posts_published.delta` against `mean_engagement_rate.delta_pp` and `mean_save_rate.delta_pp`. If volume rose and rates fell, name the dilution signal. If rates held, name the efficiency.

**Section 3 — Growth Signal** (2-3 sentences): Interpret account growth and follower acquisition efficiency. Compare followers-per-1K-views against the growth-phase benchmark (1-3 per 1K is typical for sub-1K accounts). Note checkpoint gaps.

**Section 4 — Outlier Analysis** (3-5 sentences): For each outlier-high post, identify what dimensions (city, framework, age, content type) should be investigated. For outlier-low posts, assess whether there's a pattern or noise. Name specific posts and specific questions.

**Section 5 — Anomaly Interpretation** (1-2 sentences per anomaly type): Interpret each flagged anomaly in strategic context. Not just what happened — what it might mean and which level should investigate.

Read market research files (`store/data/market-research/`) to calibrate findings where relevant (e.g., benchmark engagement rates, industry cadence norms).

**Section 6 — Cross-Level Analytical Questions** (3-5 bullets): Investigative prompts directed at other analytical levels. These are consumed by the synthesis phase.

**Section 7 — Questions Requiring Human Assessment** (2-4 bullets): Questions requiring human judgment. Each tagged `[structural]` or `[addressable]` per the gap taxonomy in `analyze/ANALYSIS-PROCESS.md`.

Write to `analyze/outputs/level-1-insights-YYYY-MM-DD.md`.

Report to console: "Level 1 insight brief generated: analyze/outputs/level-1-insights-YYYY-MM-DD.md"

---

## Outputs Summary

| Output | Location | Purpose |
|---|---|---|
| Structured data (JSON) | `analyze/outputs/level-1-performance-YYYY-MM-DD.json` | Canonical data consumed by all downstream levels and future dashboards |
| Data report (Markdown) | `analyze/outputs/level-1-performance-YYYY-MM-DD.md` | Human-readable tables and flags |
| Insight brief (Markdown) | `analyze/outputs/level-1-insights-YYYY-MM-DD.md` | Natural language interpretation with market research calibration |

---

## Important Constraints

- **No strategic recommendations in data outputs.** The JSON and Markdown data report present facts and flags.
- **Insight brief interprets but does not recommend.** It raises questions and names signals. "This looks like a dilution pattern" is an insight. "Stop posting so frequently" is a recommendation for the synthesis phase.
- **Market research calibrates, does not bias.** Benchmarks contextualize findings. They do not filter or suppress them.
- **Graceful degradation.** If the reporting period contains zero posts, zero readings, or zero account checkpoints, the report still generates with null sections and `health_status: "insufficient_data"`.
- **Deterministic data, interpreted insights.** Steps 1-8 produce identical output given the same database state. Step 9 involves natural language reasoning.
- **See `analyze/ANALYSIS-PROCESS.md`** for gap taxonomy, run modes, and insight brief standards.
