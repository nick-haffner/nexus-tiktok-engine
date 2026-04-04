# Level 3: Audience & Growth Analysis — Idealized Specification

Generated 2026-04-02.

> **Scope:** This spec is idealized — it assumes access to the full dataset defined in `tmp/idealized_ttm_design/ideal-dataset-spec.md`. Current-scope queries (with stubs for unavailable data) will be appended after approval.

---

## Stated Goals

1. **Determine whether content is building an audience or just generating impressions.** This is the highest-level strategic fork for a growth-phase account. Views without follower conversion produce reach without an asset. Level 3 surfaces whether the account is accumulating a return audience or producing disposable content.

2. **Identify which content types drive follower acquisition.** Not all views are equal for growth. Level 3 breaks down follower conversion by content dimension (framework, city, content_type) to reveal what drives follows vs. what drives views-only. This directly informs the "optimize for views vs. optimize for followers" trade-off.

3. **Assess engagement quality, not just quantity.** A post with high views and low engagement reached a broad audience that didn't resonate. A post with low views and high engagement reached a narrow audience that did. Level 3 maps each post on the views-vs-engagement grid to reveal the account's content quality profile.

4. **Track the return audience signal.** FYP% measures what percentage of views come from the algorithmic feed vs. profile, search, and following. At sub-1K followers, 96-99% FYP is expected. As the account grows, this should decline — meaning people are returning, searching, or following. If FYP% stays at 99% at 5K followers, the content isn't building loyalty.

5. **Provide the audience context that Level 6 uses to resolve content strategy conflicts.** When Level 2 says "Framework X gets the most views" but Level 3 shows "Framework X has the lowest follower conversion," Level 6 needs Level 3's data to resolve the contradiction with the right priority.

---

## Inputs

| Input | Source | Purpose |
|---|---|---|
| `readings` table | `store/data/analytics/analytics.db` | Performance metrics with `new_followers`, `fyp_percent` |
| `posts` table | `store/data/analytics/analytics.db` | Content dimensions for grouping |
| `account` table | `store/data/analytics/analytics.db` | Follower/likes trajectory over time |
| Level 1 structured output | `analyze/outputs/level-1-performance-YYYY-MM-DD.json` | Pre-computed per-post rates, aggregate baselines (optional — can query directly) |
| **Analysis period** | Parameter (default: all-time) | Same rationale as Level 2 — maximizes sample |

---

## Outputs

### Structured Data Layer

**Section 1: Follower Acquisition Efficiency**

Follower conversion broken down by content dimension. Uses the same grouping infrastructure as Level 2 but with follower-centric metrics as the primary sort.

| Field | Type | Description |
|---|---|---|
| `dimension` | string | Content variable (framework, city, content_type, etc.) |
| `groups` | array | One per dimension value |

Each group:

| Field | Type | Description |
|---|---|---|
| `value` | string | Dimension value |
| `post_count` | int | Posts in group |
| `mean_follower_conversion` | float | Followers per 1K views (primary metric) |
| `median_follower_conversion` | float | Median followers per 1K views |
| `total_new_followers` | int | Sum of new followers |
| `mean_views` | float | Average views (context) |
| `mean_save_rate` | float | Average save rate (secondary signal) |
| `notable` | string or null | Flag if this group stands out |

Dimensions analyzed: `framework`, `angle`, `content_type`, `city`, `slide_count` (bucketed).

**Section 2: Engagement Quality Grid**

Maps each post on two axes: reach (views) and resonance (engagement rate). Classifies each post into a quadrant:

| Quadrant | Views | Engagement | Interpretation |
|---|---|---|---|
| **Star** | Above median | Above median | Broad reach + strong resonance |
| **Niche Hit** | Below median | Above median | Narrow but loyal — audience-building content |
| **Viral Shallow** | Above median | Below median | Broad reach, weak resonance — impressions without connection |
| **Underperformer** | Below median | Below median | Neither reach nor resonance |

Output:

| Field | Type | Description |
|---|---|---|
| `quadrant_counts` | object | `{star: N, niche_hit: N, viral_shallow: N, underperformer: N}` |
| `quadrant_posts` | object | Each quadrant maps to an array of post summaries (slug, views, engagement_rate, follower_conversion) |
| `profile_skew` | string | Which quadrant dominates — indicates the account's content personality |
| `recommendation_signal` | string | Plain-language note: "Account skews Viral Shallow — content reaches people but doesn't convert. Prioritize Niche Hit patterns for audience growth." |

**Section 3: Save Rate as Growth Indicator**

Save rate is the strongest intent signal on TikTok — "I want to come back to this." Level 3 assesses whether save rate correlates with follower growth.

| Field | Type | Description |
|---|---|---|
| `save_rate_follower_correlation` | string | `positive`, `negative`, `none`, or `insufficient_data` |
| `high_save_posts` | array | Posts with save rate > 2x median — these are the audience-building content |
| `high_save_dimensions` | object | Which dimensions (framework, city, etc.) appear most in high-save posts |
| `data_citation` | string | The specific numbers backing the finding |

**Section 4: Return Audience Trend**

Tracks FYP% over time to detect whether the account is building a return audience.

| Field | Type | Description |
|---|---|---|
| `fyp_percent_trend` | array | Time-series of `{posted_date, fyp_percent}` for posts with snapshot data, sorted chronologically |
| `trend_direction` | string | `declining` (good — more return traffic), `stable`, `increasing` (bad — more algorithmic dependency), or `insufficient_data` |
| `current_mean_fyp` | float | Mean FYP% across the most recent N posts |
| `traffic_source_breakdown` | object or null | `{fyp, search, profile, following, other}` percentages — **stubbed** until Tier 3 data available |

**Section 5: Account Growth Trajectory**

Extends Level 1's account growth section with trend analysis.

| Field | Type | Description |
|---|---|---|
| `checkpoints` | array | All account checkpoints chronologically |
| `growth_rate_trend` | string | `accelerating`, `steady`, `decelerating`, `insufficient_data` |
| `followers_per_post_trend` | array | Rolling followers-gained-per-post over time |
| `projected_milestones` | object or null | At current rate, estimated dates for 500, 1K, 5K followers (null if insufficient data) |

### Rendering Layer

| Output | Location | Format |
|---|---|---|
| Structured report data | `analyze/outputs/level-3-audience-growth-YYYY-MM-DD.json` | JSON |
| Rendered report | `analyze/outputs/level-3-audience-growth-YYYY-MM-DD.md` | Markdown |

---

## Procedure Overview

**Step 1 — Load data.** Connect to DB. Load Level 1 output if available, otherwise query directly and compute per-post rates.

**Step 2 — Build follower acquisition tables.** Group posts by each content dimension. Compute follower conversion as the primary metric. Flag notable groups.

**Step 3 — Build engagement quality grid.** Compute all-time median views and median engagement rate. Classify each post into a quadrant. Compute quadrant counts and profile skew.

**Step 4 — Analyze save rate as growth indicator.** Identify high-save posts (> 2x median save rate). Check which dimensions they cluster in. Assess correlation between save rate and follower conversion.

**Step 5 — Track return audience trend.** Extract FYP% time-series from snapshot readings. Assess directional trend. Stub traffic source breakdown until Tier 3 data available.

**Step 6 — Analyze account growth trajectory.** Pull all account checkpoints. Compute growth rate between consecutive checkpoints. Assess acceleration/deceleration. Project milestones if sufficient data.

**Step 7 — Assemble structured output.** Compile all sections into JSON. Write to `analyze/outputs/`.

**Step 8 — Render.** Markdown report with quadrant visualization (text-based), acquisition tables, and trend summaries.

---

## Alignment Notes

- **Follower conversion is the primary metric, not views.** This is the defining distinction between Level 2 and Level 3. Level 2 sorts by views and engagement. Level 3 sorts by follower conversion and save rate.
- **The engagement quality grid is the signature output.** It answers "what kind of content are we making?" in a way no single metric can. A team that sees 70% of posts in the Viral Shallow quadrant knows they have a conversion problem, regardless of what the view counts say.
- **No recommendations.** Same as Level 2 — Level 3 presents audience data and flags patterns. Level 6 makes the call.

---

## Current-Scope Query Definitions

Uses the shared base query and `compare_dimension` function from `analyze/scripts/shared.py`. See Level 2 spec for shared infrastructure details.

### Section 1 — Follower Acquisition

Uses `compare_dimension` with the same dimensions as Level 2, but sorted by `mean_follower_conversion` instead of `mean_views`. No additional SQL.

**Current limitation:** `new_followers` is only populated on snapshot readings (42/45). Velocity readings (3/45) have null — these posts are excluded from follower conversion calculations.

### Section 2 — Engagement Quality Grid

Computed in Python from the master dataset:
```python
median_views = median(all_views)
median_engagement = median(all_engagement_rates)

for post in posts:
    if post.views >= median_views and post.engagement_rate >= median_engagement:
        quadrant = "star"
    elif post.views < median_views and post.engagement_rate >= median_engagement:
        quadrant = "niche_hit"
    elif post.views >= median_views and post.engagement_rate < median_engagement:
        quadrant = "viral_shallow"
    else:
        quadrant = "underperformer"
```

No additional SQL. All 45 posts have views and engagement data — full coverage.

### Section 3 — Save Rate as Growth Indicator

Computed in Python. Identify posts with save_rate > 2x median. Check which dimensions they cluster in. Assess correlation between save_rate and follower_conversion across posts that have both metrics.

No additional SQL.

### Section 4 — Return Audience Trend

```sql
SELECT p.posted_date, r.fyp_percent
FROM readings r
JOIN posts p ON r.post_id = p.post_id
WHERE r.fyp_percent IS NOT NULL
ORDER BY p.posted_date;
```

Trend direction computed in Python (simple linear direction across the time series).

**Stubs:**
- `traffic_source_breakdown` → null (Tier 3: search_percent, profile_percent, following_percent, other_percent all NULL)

### Section 5 — Account Growth Trajectory

```sql
SELECT captured_date, followers, total_likes
FROM account
ORDER BY captured_date;
```

**Current limitation:** 1 checkpoint. Growth rate trend, followers-per-post trend, and projected milestones all return `insufficient_data` until multiple checkpoints exist.
