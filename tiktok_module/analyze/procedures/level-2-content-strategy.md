# Level 2: Content Strategy Analysis

Decomposes performance by the content variables the team controls — framework, angle, format, hook style, slide count, city, content topics, and sound. Produces comparison tables, a content mix audit, correlation highlights, and a classification gap report.

**Idealized spec:** `tmp/idealized_ttm_design/level-2-content-strategy-spec.md`

## When to Run

- **Bi-weekly or monthly** as part of the standard analyze cadence.
- **On demand** when evaluating whether to change content strategy.

## Inputs

| Input | Location | Required |
|---|---|---|
| Analytics database | `store/data/analytics/analytics.db` | Yes |
| Level 1 output (optional) | `analyze/outputs/level-1-performance-YYYY-MM-DD.json` | No — can query directly |
| Frameworks catalog | `store/data/strategy/frameworks.md` | For label consistency |
| Analysis period | Parameter (default: all-time) | Yes |

## Outputs

| Output | Location | Format |
|---|---|---|
| Structured report data | `analyze/outputs/level-2-content-strategy-YYYY-MM-DD.json` | JSON |
| Rendered report | `analyze/outputs/level-2-content-strategy-YYYY-MM-DD.md` | Markdown |

## Procedure

### Step 1 — Load Data

Load the master dataset using the shared base query:

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

Compute per-post derived fields: `engagement_rate`, `save_rate`, `follower_conversion`.

### Step 2 — Build Dimension Comparisons

For each content dimension, run the shared `compare_dimension` function:

| Dimension | Source | Bucketing | Current Coverage |
|---|---|---|---|
| `framework` | `n.framework` | None | 7/45 (16%) |
| `angle` | `n.angle` | None | 7/45 (16%) |
| `format` | `n.format` | None | 4/45 (9%) |
| `hook_style` | `n.hook_style` | None | **0/45 (stub)** |
| `content_type` | `p.content_type` | None | 45/45 (100%) |
| `slide_count` | `p.slide_count` | 1-5, 6-8, 9+ | 45/45 (100%) |
| `city` | `n.city` | None | 29/45 (64%) |
| `content_topics` | `n.content_topics` | Exploded | **0/45 (stub)** |
| `sound_type` | `p.sound_type` | None | **0/45 (stub)** |

For each group within a dimension, compute:
- `post_count`, `mean_views`, `median_views`, `mean_engagement_rate`, `mean_save_rate`
- `mean_follower_conversion` (supporting metric), `mean_watched_full_percent`
- `total_views`, `trajectory` (improving/declining/stable), `last_used`, `notable` flag

Posts with null values for a dimension are excluded from that dimension's comparison but counted in the classification gap report.

Dimensions with 0% coverage (`hook_style`, `content_topics`, `sound_type`) produce empty comparison objects.

### Step 3 — Build Content Mix Audit

Query the 10 most recent posts:

```sql
SELECT p.post_id, p.posted_date, p.content_type, p.slide_count,
       n.framework, n.angle, n.format, n.city
FROM posts p
LEFT JOIN nexus_post_metadata n ON p.post_id = n.post_id
ORDER BY p.posted_date DESC
LIMIT 10;
```

Compute percentage distribution across each key dimension. Include null/unclassified as an explicit category.

### Step 4 — Build Correlation Highlights

Run targeted cross-cuts from the master dataset:
- Framework x city
- Hook style x framework (when data available)
- Slide count x content_type
- Content topics x save_rate (when data available)

For each cross-cut:
1. Filter to posts that have both dimensions populated.
2. Compare the metric across groups.
3. Only surface findings where the difference is >50% and the smaller group has n >= 3.
4. Assign confidence: `high` (n >= 10), `moderate` (n 5-9), `low` (n < 5).

### Step 5 — Build Classification Gap Report

For each classification field (`framework`, `angle`, `format`, `hook_text`, `hook_style`, `city`, `cta_text`, `content_topics`):
- Count posts with non-null values.
- If coverage < 70% for a dimension, flag the impact on that dimension's comparison reliability.
- List unclassified posts with which fields are missing.

### Step 6 — Assess Data Coverage

Same pattern as Level 1: report stubbed columns, Nexus metadata coverage, and account checkpoint count.

### Step 7 — Assemble Structured Output

```json
{
  "report_type": "level_2_content_strategy",
  "generated_at": "ISO datetime",
  "analysis_period": "all-time",
  "dimension_comparisons": [ ... ],
  "content_mix": { ... },
  "correlation_highlights": [ ... ],
  "classification_gap": { ... },
  "missing_data": { ... }
}
```

Write to `analyze/outputs/level-2-content-strategy-YYYY-MM-DD.json`.

### Step 8 — Render

Markdown report with:
- One table per dimension comparison, sorted by primary metric (mean_views)
- Content mix as percentage table
- Correlation highlights as bulleted findings with confidence tags
- Classification gap summary
- Data coverage section

Write to `analyze/outputs/level-2-content-strategy-YYYY-MM-DD.md`.

Report to console: "Level 2 report generated: analyze/outputs/level-2-content-strategy-YYYY-MM-DD.md"

### Step 9 — Generate Insight Brief

Read the JSON output from Step 7. Produce a 300-500 word natural language interpretation in two phases.

**Phase 1 — Dimension Review** (data-only):

**Content Strategy Assessment** (2-3 sentences): Lead with the highest-confidence, highest-leverage finding.

**Framework Signal** (2-3 sentences): Interpret framework comparison honestly — name the direction but flag confidence limitations.

**City Patterns** (3-5 sentences): Identify saturation signals, underperformers, bright spots. Cross-reference with content mix.

**Slide Count / Format** (2-3 sentences): Interpret structural findings with sample size caveats.

**What Can't Be Assessed** (2-3 sentences): Name stubbed dimensions and the questions that remain unanswerable.

**Phase 2 — Outlier Investigation** (targeted content access):

Identify the top 3 and bottom 3 performers by views. For each that has content artifacts (`store/data/posts/{slug}/copy.md`, `visual-summary.md`, `caption.md`), read the content and describe:
- What the hook said and how it was framed
- What content topics the slides covered
- Any structural differences from other posts
- A hypothesis about what drove the outlier performance

If a flagged post lacks content artifacts, note this as an addressable gap.

Read market research files (`store/data/market-research/`) to calibrate dimension findings where relevant.

**Cross-Level Analytical Questions** (3-5 bullets): Investigative prompts for other levels.

**Questions Requiring Human Assessment** (2-4 bullets): Each tagged `[structural]` or `[addressable]` per the gap taxonomy.

Write to `analyze/outputs/level-2-insights-YYYY-MM-DD.md`.

Report to console: "Level 2 insight brief generated: analyze/outputs/level-2-insights-YYYY-MM-DD.md"

---

## Outputs Summary

| Output | Location | Purpose |
|---|---|---|
| Structured data (JSON) | `analyze/outputs/level-2-content-strategy-YYYY-MM-DD.json` | Canonical data consumed by synthesis phase |
| Data report (Markdown) | `analyze/outputs/level-2-content-strategy-YYYY-MM-DD.md` | Human-readable comparison tables |
| Insight brief (Markdown) | `analyze/outputs/level-2-insights-YYYY-MM-DD.md` | Dimension analysis + outlier investigation with content |

---

## Important Constraints

- **No recommendations in data outputs.** The JSON and data report present comparisons and flags.
- **Insight brief interprets but does not recommend.** "Dallas shows a declining trajectory" is an insight. "Stop posting in Dallas" is a recommendation for the synthesis phase.
- **Phase 2 content access is targeted.** Only top/bottom performers identified by the data. Content explains outliers — it does not define dimensions.
- **Confidence tagging on every group.** Groups with n < 3 are flagged as `low` confidence.
- **Exclude, don't guess.** Posts without a dimension value are excluded, not inferred.
- **See `analyze/ANALYSIS-PROCESS.md`** for gap taxonomy, run modes, and insight brief standards.
