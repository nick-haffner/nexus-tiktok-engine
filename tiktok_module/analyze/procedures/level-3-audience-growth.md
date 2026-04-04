# Level 3: Audience & Growth Analysis

Determines whether content is building an audience or just generating impressions. Breaks down follower acquisition by content dimension, maps the engagement quality profile, tracks save rate as a growth indicator, and monitors the return audience signal.

**Idealized spec:** `tmp/idealized_ttm_design/level-3-audience-growth-spec.md`

## When to Run

- **Monthly** as part of the standard analyze cadence.
- **On demand** when evaluating whether the content strategy is building an audience.

## Inputs

| Input | Location | Required |
|---|---|---|
| Analytics database | `store/data/analytics/analytics.db` | Yes |
| Level 1 output (optional) | `analyze/outputs/level-1-performance-YYYY-MM-DD.json` | No — can query directly |
| Analysis period | Parameter (default: all-time) | Yes |

## Outputs

| Output | Location | Format |
|---|---|---|
| Structured report data | `analyze/outputs/level-3-audience-growth-YYYY-MM-DD.json` | JSON |
| Rendered report | `analyze/outputs/level-3-audience-growth-YYYY-MM-DD.md` | Markdown |

## Procedure

### Step 1 — Load Data

Load the master dataset using the shared base query (same as Level 2). Compute per-post derived fields: `engagement_rate`, `save_rate`, `follower_conversion`.

### Step 2 — Build Follower Acquisition Tables

For each content dimension (`framework`, `angle`, `content_type`, `city`, `slide_count`), run the shared `compare_dimension` function with `mean_follower_conversion` as the primary sort metric.

Each group reports: `post_count`, `mean_follower_conversion`, `median_follower_conversion`, `total_new_followers`, `mean_views` (context), `mean_save_rate` (secondary signal), `notable` flag.

**Current limitation:** `new_followers` is only on snapshot readings (42/45). Velocity readings (3) are excluded from follower calculations.

### Step 3 — Build Engagement Quality Grid

Compute all-time medians:
- `median_views` across all posts
- `median_engagement_rate` across all posts

Classify each post into a quadrant:

| Quadrant | Views | Engagement | Interpretation |
|---|---|---|---|
| Star | >= median | >= median | Broad reach + strong resonance |
| Niche Hit | < median | >= median | Narrow but loyal — audience-building |
| Viral Shallow | >= median | < median | Broad reach, weak resonance |
| Underperformer | < median | < median | Neither reach nor resonance |

Compute quadrant counts, list posts per quadrant, determine profile skew (which quadrant dominates).

Full coverage: all 45 posts have views and engagement data.

### Step 4 — Analyze Save Rate as Growth Indicator

Identify high-save posts: save_rate > 2x median save_rate.

For high-save posts, check which dimensions (`framework`, `city`, `content_type`) appear most frequently. Assess correlation between save_rate and follower_conversion across posts that have both metrics.

### Step 5 — Track Return Audience Trend

```sql
SELECT p.posted_date, r.fyp_percent
FROM readings r
JOIN posts p ON r.post_id = p.post_id
WHERE r.fyp_percent IS NOT NULL
ORDER BY p.posted_date;
```

Compute trend direction across the time series (simple: are recent posts' FYP% lower or higher than earlier posts'?).

**Stubbed:** `traffic_source_breakdown` (search, profile, following, other percentages) — all NULL until Tier 3 data available.

### Step 6 — Analyze Account Growth Trajectory

```sql
SELECT captured_date, followers, total_likes
FROM account
ORDER BY captured_date;
```

Compute growth rate between consecutive checkpoints. Assess trend: `accelerating`, `steady`, `decelerating`, or `insufficient_data`.

Compute followers-per-post trend (rolling). Project milestones (500, 1K, 5K followers) if sufficient data.

**Current limitation:** 1 checkpoint. All trend fields return `insufficient_data`.

### Step 7 — Assess Data Coverage

Same pattern as Level 1: Nexus metadata coverage, stubbed columns, account checkpoint count.

### Step 8 — Assemble Structured Output

```json
{
  "report_type": "level_3_audience_growth",
  "generated_at": "ISO datetime",
  "analysis_period": "all-time",
  "follower_acquisition": [ ... ],
  "engagement_quality_grid": { ... },
  "save_rate_analysis": { ... },
  "return_audience_trend": { ... },
  "account_growth_trajectory": { ... },
  "missing_data": { ... }
}
```

Write to `analyze/outputs/level-3-audience-growth-YYYY-MM-DD.json`.

### Step 9 — Render

Markdown report with:
- Follower acquisition tables (one per dimension, sorted by follower conversion)
- Engagement quality grid as a 2x2 text table with post counts and names
- Save rate findings
- FYP% trend summary
- Account growth summary
- Data coverage section

Write to `analyze/outputs/level-3-audience-growth-YYYY-MM-DD.md`.

Report to console: "Level 3 report generated: analyze/outputs/level-3-audience-growth-YYYY-MM-DD.md"

### Step 10 — Generate Insight Brief

Read the JSON output from Step 8. Produce a 300-500 word natural language interpretation focused on audience and growth implications.

**Audience Health** (3-5 sentences): Interpret the engagement quality grid. What's the account's content personality? Is it consistent or scattered?

**Follower Conversion** (2-3 sentences): Interpret follower acquisition data. Flag data quality issues honestly.

**Save Rate as Growth Proxy** (2-3 sentences): Which content dimensions concentrate in high-save posts? Align with or contradict Level 2?

**Return Audience Trend** (3-4 sentences): Interpret FYP% trajectory. Flag the small-denominator caveat on early posts.

**Flagged Post Investigation** (targeted content access): For posts in the Viral Shallow and Niche Hit quadrants that have content artifacts, read `copy.md`, `visual-summary.md`, and `caption.md`. Describe what differentiates Niche Hit content (high engagement, low views) from Viral Shallow content (high views, low engagement) at the creative level. Note when flagged posts lack content artifacts (addressable gap).

Read market research files (`store/data/market-research/`) to calibrate growth benchmarks where relevant.

**Cross-Level Analytical Questions** (3-5 bullets): Investigative prompts for other levels.

**Questions Requiring Human Assessment** (2-4 bullets): Each tagged `[structural]` or `[addressable]`.

Write to `analyze/outputs/level-3-insights-YYYY-MM-DD.md`.

Report to console: "Level 3 insight brief generated: analyze/outputs/level-3-insights-YYYY-MM-DD.md"

---

## Outputs Summary

| Output | Location | Purpose |
|---|---|---|
| Structured data (JSON) | `analyze/outputs/level-3-audience-growth-YYYY-MM-DD.json` | Canonical data consumed by synthesis phase |
| Data report (Markdown) | `analyze/outputs/level-3-audience-growth-YYYY-MM-DD.md` | Human-readable tables and grid |
| Insight brief (Markdown) | `analyze/outputs/level-3-insights-YYYY-MM-DD.md` | Audience analysis with targeted content investigation |

---

## Important Constraints

- **Follower conversion is the primary metric, not views.** Defining distinction from Level 2.
- **The engagement quality grid is the signature output.**
- **Content access is targeted.** Only posts flagged by the engagement grid. Content explains quadrant placement — it does not define the grid.
- **Flag data quality issues.** If follower data is sparse or unreliable, say so.
- **Graceful degradation.** With 1 account checkpoint, growth trajectory returns `insufficient_data`.
- **See `analyze/ANALYSIS-PROCESS.md`** for gap taxonomy, run modes, and insight brief standards.
