# Level 2: Content Strategy Analysis — Idealized Specification

Generated 2026-04-02. Proposal for the Level 2 analyze procedure.

> **Scope:** This spec is idealized — it assumes access to the full dataset defined in `tmp/idealized_ttm_design/ideal-dataset-spec.md`. Current-scope queries (with stubs for unavailable data) will be appended after approval. The procedure document written from this spec will implement the current-scope queries while preserving the idealized output structure so that new data sources slot in without redesign.

---

## Stated Goals

1. **Identify which content dimensions drive performance.** Level 2 decomposes performance by the variables the content team controls: framework, angle, format, hook style, slide count, city, content topics, and sound. Each dimension gets its own comparison table so the team can see exactly where performance concentrates. This is the core of the bi-weekly content strategy meeting in an agency environment.

2. **Surface the highest-leverage creative variables.** Not all dimensions matter equally. Hook style determines initial distribution (48h velocity). Framework determines positioning and audience resonance (7d engagement, save rate). Slide count determines completion. Level 2 must present these in priority order so the team focuses on what moves the needle most.

3. **Detect saturation and diminishing returns.** Repeated use of the same city, framework, or angle can fatigue the audience. Level 2 must track sequential performance within a dimension — not just averages, but trajectories. A framework that averaged well historically but declined across the last 3 uses is a different signal than one that's consistently strong.

4. **Audit the content mix.** What percentage of recent posts used each framework, angle, format, and city? Over-indexing on one approach risks audience fatigue and leaves other approaches untested. Industry standard: agencies maintain 3-5 content pillars and rebalance based on performance.

5. **Provide the comparison data that Level 6 converts into decisions.** Level 2 does not make recommendations — it produces the evidence. Level 6 synthesizes Level 2's comparison tables with Level 1's health check to produce actionable strategy changes. Level 2's discipline is: present the data, flag what's notable, don't editorialize.

---

## Inputs

| Input | Source | Purpose |
|---|---|---|
| `readings` table | `store/data/analytics/analytics.db` | Performance metrics per post |
| `posts` table | `store/data/analytics/analytics.db` | Content dimensions (framework, angle, city, hook_text, slide_count, content_type, etc.) |
| `account` table | `store/data/analytics/analytics.db` | Follower data for conversion analysis |
| Level 1 structured output | `analyze/outputs/level-1-performance-YYYY-MM-DD.json` | Per-post table with computed rates, anomaly flags, aggregate baselines |
| `frameworks.md` | `store/data/strategy/frameworks.md` | Current catalog of frameworks, angles, formats — used to label and group |
| Content artifacts | `store/data/posts/{slug}/copy.md`, `README.md` | Hook text, format, additional metadata not in DB |
| **Analysis period** | Parameter (default: all-time) | Unlike Level 1's trailing window, Level 2 benefits from the largest possible sample. Default to all-time with optional period filter. |

**Dependency on Level 1:** Level 2 can run independently by querying the DB directly, but it benefits from Level 1's pre-computed per-post table (engagement rates, outlier flags, etc.). When a recent Level 1 output exists, Level 2 should consume it rather than recompute.

---

## Outputs

### Structured Data Layer

A structured intermediate representation (JSON/dict) containing all comparison tables, mix audits, and notable findings. Same pattern as Level 1: renderers consume this structure.

The structured output contains the following sections:

**Section 1: Dimension Comparisons**

An array of comparison objects, one per content dimension analyzed. Each comparison contains:

| Field | Type | Description |
|---|---|---|
| `dimension` | string | The content variable being compared (e.g., "framework", "hook_style") |
| `groups` | array | One entry per distinct value within the dimension |

Each group within a comparison:

| Field | Type | Description |
|---|---|---|
| `value` | string | The dimension value (e.g., "local_vs_tourist", "curiosity") |
| `post_count` | int | Number of posts in this group |
| `mean_views` | float | Average views |
| `median_views` | float | Median views |
| `mean_engagement_rate` | float | Average engagement rate (%) |
| `mean_save_rate` | float | Average save rate (%) |
| `mean_follower_conversion` | float | Average followers per 1K views |
| `mean_watched_full_percent` | float or null | Average completion rate (snapshot posts only) |
| `mean_profile_visits` | float or null | Average profile visits per post (Tier 3) |
| `total_views` | int | Sum of views across group |
| `trajectory` | string or null | `improving`, `declining`, `stable`, or null if < 3 posts — based on sequential view performance within the group |
| `last_used` | date | Most recent post date in this group |
| `notable` | string or null | Human-readable flag if this group stands out (e.g., "highest save rate", "declining trajectory") |

**Dimensions analyzed (ideal state):**

| Dimension | Grouped By | Decision It Informs |
|---|---|---|
| `framework` | `nexus_post_metadata.framework` | Which structural approach to use (Local vs Tourist, Worth It, etc.) |
| `angle` | `nexus_post_metadata.angle` | Scope/lens selection (broad guide, deep-dive, list) |
| `format` | `nexus_post_metadata.format` | Layout choice (combined, split, single-point) |
| `hook_style` | `nexus_post_metadata.hook_style` | How to frame the opening slide |
| `content_type` | `posts.content_type` | Carousel vs. video performance |
| `slide_count` | `posts.slide_count` (bucketed: 1-5, 6-8, 9+) | Optimal carousel length |
| `city` | `nexus_post_metadata.city` | City selection and saturation detection |
| `content_topics` | `nexus_post_metadata.content_topics` (exploded — one post may have multiple) | Topic prioritization (food, nightlife, views, etc.) |
| `sound_type` | `posts.sound_type` | Sound strategy (trending vs. original vs. licensed) |

**Section 2: Content Mix Audit**

Shows the distribution of recent posts across key dimensions.

| Field | Type | Description |
|---|---|---|
| `period` | string | The period assessed (e.g., "last 30 days" or "last 10 posts") |
| `dimensions` | object | One key per dimension, value is an array of `{value, count, percentage}` |

Example:
```json
{
  "framework": [
    {"value": "local_vs_tourist", "count": 4, "percentage": 40},
    {"value": "worth_it", "count": 2, "percentage": 20},
    {"value": null, "count": 4, "percentage": 40}
  ]
}
```

The mix audit explicitly reports null/unclassified counts so the classification gap is visible.

**Section 3: Correlation Highlights**

Cross-dimensional findings that emerge from combining dimensions. Not a full correlation matrix — a targeted set of high-value cross-cuts:

| Field | Type | Description |
|---|---|---|
| `finding` | string | Plain-language description of the cross-dimensional pattern |
| `dimensions` | array of string | Which dimensions are involved |
| `metric` | string | Which metric the finding is about |
| `data_citation` | string | The specific numbers backing the finding |
| `confidence` | string | `high` (n >= 10), `moderate` (n 5-9), `low` (n < 5) |

Examples of ideal-state cross-cuts:
- Framework × city: "Local vs Tourist performs 3x better in Dallas than in LA"
- Hook style × framework: "Curiosity hooks on Worth It posts outperform contrast hooks on the same framework"
- Slide count × content_type: "6-slide carousels have 2x the save rate of 9-slide"
- Content topics × save rate: "Posts featuring food have 1.8x the save rate of nightlife posts"
- Caption length × engagement: "Long captions (150+ words) correlate with 40% higher comment rate"

**Section 4: Classification Gap Report**

| Field | Type | Description |
|---|---|---|
| `total_posts` | int | Total posts in the database |
| `classified_posts` | int | Posts with framework, angle, and format populated |
| `unclassified_posts` | int | Posts missing one or more classification fields |
| `unclassified_list` | array | Post IDs/slugs with which fields are missing |
| `impact` | string | How the gap affects analysis reliability (e.g., "40% of posts are unclassified — framework comparison has moderate confidence at best") |

This section makes the classification gap a first-class output rather than a hidden caveat. The manager can then decide to run a backfill or accept the reduced confidence.

### Rendering Layer

Same pattern as Level 1. Default Markdown renderer, structured data stored alongside. Both consumed by Level 6.

| Output | Location | Format |
|---|---|---|
| Structured report data | `analyze/outputs/level-2-content-strategy-YYYY-MM-DD.json` | JSON |
| Rendered report | `analyze/outputs/level-2-content-strategy-YYYY-MM-DD.md` | Markdown |

---

## Procedure Overview

**Step 1 — Load data**

Connect to the database. If a recent Level 1 output exists (same reporting cycle), load it and use its per-post table as the base dataset. Otherwise, query the database directly and compute per-post rates inline.

Load the current `frameworks.md` to map known framework/angle/format values and ensure group labels are consistent.

**Step 2 — Classify and tag**

For each post in the dataset, ensure all dimension fields are populated where possible:
- Derive `posted_day_of_week` from `posted_date`
- Derive `caption_length_words` from `description`
- Derive `hashtag_count` from `hashtags`
- Derive `days_since_previous_post` from the `posted_date` sequence
- Read `format` from `README.md` if not in DB (content artifact fallback)
- Read `hook_style` if available; otherwise leave null

Record which posts lack classification for each dimension. This feeds Section 4.

**Step 3 — Build dimension comparisons**

For each dimension in the analysis set:
1. Group posts by the dimension value. Posts with null values for the dimension are excluded from that comparison (but counted in the classification gap report).
2. For each group, compute: post count, mean/median views, mean engagement rate, mean save rate, mean follower conversion, mean watched_full_percent, total views.
3. Compute trajectory: order the group's posts by `posted_date` and assess whether views are improving, declining, or stable across the last 3+ posts. Use a simple directional test (are the most recent posts above or below the group mean?).
4. Flag notable groups: highest/lowest on each metric, any group with `trajectory: "declining"`, any group with post_count < 3 (insufficient data).

**Step 4 — Build content mix audit**

Take the most recent N posts (default: last 10, or last 30 days, whichever is larger) and compute the percentage distribution across each key dimension. Include null/unclassified as an explicit category.

**Step 5 — Build correlation highlights**

Run the targeted cross-cuts defined in Section 3. For each:
1. Filter to posts that have both dimensions populated.
2. Compare the metric across the cross-cut groups.
3. Only surface findings where the difference is >50% and the smaller group has n >= 3.
4. Assign confidence based on sample size.

**Step 6 — Build classification gap report**

Count posts with null values for each classification field. List the unclassified posts. Compute the impact statement (what percentage of posts are excluded from which comparisons).

**Step 7 — Assemble structured output**

Compile all sections into a single JSON object:

```json
{
  "report_type": "level_2_content_strategy",
  "generated_at": "ISO datetime",
  "analysis_period": "all-time or specified",
  "dimension_comparisons": [ ... ],
  "content_mix": { ... },
  "correlation_highlights": [ ... ],
  "classification_gap": { ... }
}
```

Write to `analyze/outputs/level-2-content-strategy-YYYY-MM-DD.json`.

**Step 8 — Render**

Pass the structured output to the Markdown renderer. The renderer produces:
- Dimension comparison tables (one per dimension, sorted by the primary metric)
- Content mix as percentage bars or tables
- Correlation highlights as a bulleted findings list with confidence tags
- Classification gap as a summary with a list of unclassified posts

Write to `analyze/outputs/level-2-content-strategy-YYYY-MM-DD.md`.

---

## Handling the Classification Gap

18 of 45 posts currently lack `framework`, `angle`, and other Nexus-specific metadata. Level 2 handles this as follows:

1. **Exclude, don't guess.** Posts without a dimension value are excluded from that dimension's comparison. Guessing or inferring would compromise the analysis.
2. **Report the exclusion.** The classification gap report (Section 4) makes the exclusion visible. The manager sees exactly how many posts are missing and how it affects confidence.
3. **Use available dimensions.** Even unclassified posts have `content_type`, `slide_count`, `city` (sometimes), `posted_date`, `caption_length`, and `hashtag_count`. These dimensions can be analyzed across the full 45-post set.
4. **Recommend backfill.** If the gap exceeds 30% of posts for a high-priority dimension (framework, angle, hook_style), the classification gap report should flag this as a blocking issue for reliable analysis.

---

## Relationship to Levels 3, 4, and 5

Levels 3 (Audience & Growth), 4 (Cadence & Timing), and 5 (Conversion Funnel) are implemented as separate procedures with their own specs, scripts, and outputs. They answer distinct strategic questions and produce distinct inputs for Level 6's coherence check.

Level 2's dimension set is scoped to **content strategy variables** — the creative decisions the team controls when producing content: framework, angle, format, hook style, slide count, city, content topics, and sound. Dimensions that belong to other levels:
- `posting_day`, `posting_time`, `days_since_previous_post` → Level 4
- `caption_length`, `hashtag_count`, `cta_text` → Level 5
- `follower_conversion` as a primary metric (not supporting) → Level 3

Level 2 includes `mean_follower_conversion` as a supporting metric in its comparison tables (useful context), but the primary analysis of audience growth patterns lives in Level 3.

All four procedures (2-5) share common query infrastructure where mechanics overlap (grouping, aggregation, median computation). Each functions independently but benefits from Level 1's pre-computed per-post table when available.

---

## Alignment Notes

- **All-time default, not trailing window.** Unlike Level 1's weekly window, Level 2 benefits from the largest possible sample. With 45 posts, every data point matters. Period filtering is available but not the default.
- **No recommendations.** Level 2 presents comparisons and flags what's notable. It does not say "use Local vs Tourist" or "stop posting in Dallas." That's Level 6's job.
- **Confidence tagging.** Every comparison group and correlation highlight carries a confidence signal based on sample size. This prevents the team from over-indexing on a finding backed by 2 posts.
- **Structured output before rendering.** Same as Level 1 — query/computation is separated from presentation. The JSON output is the canonical artifact.

---

## Current-Scope Query Definitions

These queries implement the idealized spec above against the v2 database schema. Company-specific metadata is in `nexus_post_metadata`, joined via LEFT JOIN. See `tmp/schema-v3-overview.md` for the full schema.

### Shared Base Query

All Levels 2-5 use the same master dataset query. This is implemented once in a shared module (`analyze/scripts/shared.py`) and consumed by each level's script.

```sql
SELECT
    p.post_id, p.posted_date, p.content_type, p.slide_count,
    p.description, p.hashtags, p.sound_name, p.sound_type, p.posted_time,
    n.slug, n.city, n.framework, n.angle, n.format,
    n.hook_text, n.hook_style, n.cta_text, n.content_topics,
    r.captured_at, r.hours_since_post, r.type as reading_type,
    r.views, r.likes, r.comments, r.shares, r.bookmarks,
    r.new_followers, r.avg_watch_time_seconds,
    r.watched_full_percent, r.fyp_percent, r.profile_visits
FROM readings r
JOIN posts p ON r.post_id = p.post_id
LEFT JOIN nexus_post_metadata n ON r.post_id = n.post_id;
```

Per-post computed fields (Python, same as Level 1):
- `engagement_rate`, `save_rate`, `follower_conversion`, `non_fyp_percent`
- `posted_day_of_week`, `caption_length_words`, `hashtag_count`, `days_since_previous_post`
- `age_days`

### Shared Dimension Comparison Function

A generic function that takes the master dataset, a dimension name, and optional bucketing rules, and returns a comparison object:

```python
def compare_dimension(posts, dimension, buckets=None):
    # Group posts by dimension value (skip nulls)
    # For each group: compute post_count, mean/median views,
    #   mean engagement_rate, mean save_rate, mean follower_conversion,
    #   mean watched_full_percent, total_views
    # Compute trajectory (sequential view performance, last 3+ posts)
    # Flag notable groups (highest/lowest, declining, insufficient data)
    # Return comparison object per spec
```

This function is used by Level 2 (9 dimensions), Level 3 (follower-centric sort), Level 4 (timing dimensions), and Level 5 (caption dimensions).

### Level 2 Specific Queries

No additional SQL beyond the shared base query. All Level 2 work is grouping and aggregation in Python.

**Dimensions and their sources:**

| Dimension | Source Column | Bucketing | Current Coverage |
|---|---|---|---|
| `framework` | `n.framework` | None (categorical) | 7/45 (16%) |
| `angle` | `n.angle` | None | 7/45 (16%) |
| `format` | `n.format` | None | 4/45 (9%) |
| `hook_style` | `n.hook_style` | None | **0/45 (stub)** |
| `content_type` | `p.content_type` | None | 45/45 (100%) |
| `slide_count` | `p.slide_count` | Buckets: 1-5, 6-8, 9+ | 45/45 (100%) |
| `city` | `n.city` | None | 29/45 (64%) |
| `content_topics` | `n.content_topics` | Exploded (multi-value) | **0/45 (stub)** |
| `sound_type` | `p.sound_type` | None | **0/45 (stub)** |

**Content mix query** — last 10 posts by posted_date:
```sql
SELECT p.post_id, p.posted_date, p.content_type, p.slide_count,
       n.framework, n.angle, n.format, n.city
FROM posts p
LEFT JOIN nexus_post_metadata n ON p.post_id = n.post_id
ORDER BY p.posted_date DESC
LIMIT 10;
```

**Correlation highlights** — computed in Python by cross-cutting two dimensions from the master dataset. No additional SQL.

**Stubs:**
- `hook_style`, `content_topics`, `sound_type` dimensions produce empty comparison objects (no data). Output structure preserved.
- `mean_profile_visits` in comparison groups → null
