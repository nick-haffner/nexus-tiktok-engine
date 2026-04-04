# Level 4: Cadence & Timing Optimization — Idealized Specification

Generated 2026-04-02.

> **Scope:** This spec is idealized — it assumes access to the full dataset defined in `tmp/idealized_ttm_design/ideal-dataset-spec.md`. Current-scope queries (with stubs for unavailable data) will be appended after approval.

---

## Stated Goals

1. **Determine optimal posting frequency.** Is there a diminishing return from posting too often? Is there a performance drop-off from gaps? Level 4 correlates posting cadence with per-post performance to find the sweet spot. Industry standard: most TikTok agencies recommend 3-5 posts/week for growth-phase accounts, but the only real answer is the account's own data.

2. **Identify day-of-week and time-of-day patterns.** Some days and times yield better initial distribution than others. Level 4 groups posts by posting day and posting hour to surface any patterns. For informational content, Tuesday-Thursday typically outperforms weekends — but this varies by niche and must be verified empirically.

3. **Assess the relationship between posting gaps and initial velocity.** Does a 3-day gap before a post correlate with higher 48h velocity? TikTok's algorithm may favor consistent cadence or may reward strategic pauses. Level 4 tests this with the `days_since_previous_post` dimension.

4. **Provide the scheduling data that Level 6 converts into content calendar rules.** Level 4 doesn't set the posting schedule — it provides the evidence. Level 6 synthesizes Level 4's timing data with Level 2's content strategy to produce a calendar that considers both *what* and *when*.

---

## Inputs

| Input | Source | Purpose |
|---|---|---|
| `posts` table | `store/data/analytics/analytics.db` | `posted_date`, `posted_time` for timing analysis |
| `readings` table | `store/data/analytics/analytics.db` | Performance metrics, particularly 48h velocity readings |
| Level 1 structured output | `analyze/outputs/level-1-performance-YYYY-MM-DD.json` | Pre-computed per-post rates (optional) |
| **Analysis period** | Parameter (default: all-time) | Maximizes sample |

---

## Outputs

### Structured Data Layer

**Section 1: Posting Frequency Analysis**

| Field | Type | Description |
|---|---|---|
| `frequency_periods` | array | Rolling windows showing posts-per-period and corresponding performance |

Each period:

| Field | Type | Description |
|---|---|---|
| `window_start` | date | Start of the rolling window |
| `window_end` | date | End of the rolling window |
| `posts_count` | int | Posts published in this window |
| `mean_views` | float | Average views for posts in this window |
| `mean_engagement_rate` | float | Average engagement rate |
| `mean_save_rate` | float | Average save rate |

Plus summary:

| Field | Type | Description |
|---|---|---|
| `overall_posts_per_week` | float | Average posting frequency across the full period |
| `frequency_performance_correlation` | string | `positive` (more posts = better per-post performance), `negative` (diminishing returns), `none`, or `insufficient_data` |
| `data_citation` | string | The specific numbers backing the finding |

**Section 2: Day-of-Week Performance**

Same grouping structure as Level 2's dimension comparisons, grouped by `posted_day_of_week`:

| Field | Type | Description |
|---|---|---|
| `day` | string | Monday-Sunday |
| `post_count` | int | Posts published on this day |
| `mean_views` | float | Average views |
| `median_views` | float | Median views |
| `mean_engagement_rate` | float | |
| `mean_save_rate` | float | |
| `notable` | string or null | Flag if this day stands out |

**Section 3: Time-of-Day Performance**

Grouped by `posted_time` bucketed into periods:

| Bucket | Hours | Description |
|---|---|---|
| morning | 06:00-11:59 | Pre-work / commute |
| midday | 12:00-16:59 | Lunch / afternoon |
| evening | 17:00-20:59 | Post-work / prime time |
| night | 21:00-05:59 | Late night |

Each bucket:

| Field | Type | Description |
|---|---|---|
| `bucket` | string | morning, midday, evening, night |
| `post_count` | int | |
| `mean_views` | float | |
| `mean_engagement_rate` | float | |
| `notable` | string or null | |

**Stubbed** until `posted_time` is captured (Tier 2).

**Section 4: Gap Analysis**

Correlates `days_since_previous_post` with the post's performance.

| Field | Type | Description |
|---|---|---|
| `gap_performance` | array | One entry per post, with `{slug, gap_days, views, engagement_rate, save_rate}` |
| `gap_buckets` | array | Bucketed aggregation: 0-1 days, 2-3 days, 4-7 days, 8+ days |

Each bucket:

| Field | Type | Description |
|---|---|---|
| `bucket` | string | Gap range |
| `post_count` | int | |
| `mean_views` | float | |
| `mean_engagement_rate` | float | |
| `notable` | string or null | |

| Field | Type | Description |
|---|---|---|
| `optimal_gap_signal` | string | Which bucket performs best, with confidence level |
| `data_citation` | string | Backing numbers |

**Section 5: Consistency Analysis**

Measures whether the account posts at a regular rhythm or in bursts, and whether regularity correlates with performance.

| Field | Type | Description |
|---|---|---|
| `gap_stddev` | float | Standard deviation of posting gaps — low = consistent, high = bursty |
| `posting_pattern` | string | `consistent`, `bursty`, `irregular` |
| `consistency_performance_signal` | string or null | Whether consistent stretches outperform bursty stretches |

### Rendering Layer

| Output | Location | Format |
|---|---|---|
| Structured report data | `analyze/outputs/level-4-cadence-timing-YYYY-MM-DD.json` | JSON |
| Rendered report | `analyze/outputs/level-4-cadence-timing-YYYY-MM-DD.md` | Markdown |

---

## Procedure Overview

**Step 1 — Load data.** Connect to DB. Load Level 1 output if available.

**Step 2 — Compute posting gaps.** Order all posts by `posted_date`. Compute `days_since_previous_post` for each. Derive `posted_day_of_week`.

**Step 3 — Build frequency analysis.** Compute rolling weekly post counts. Correlate posting frequency with per-post performance in each window.

**Step 4 — Build day-of-week comparison.** Group posts by day. Compute per-group metrics.

**Step 5 — Build time-of-day comparison.** If `posted_time` is available, bucket and compare. Otherwise, stub the section.

**Step 6 — Build gap analysis.** Bucket `days_since_previous_post` and compare performance across buckets.

**Step 7 — Build consistency analysis.** Compute gap standard deviation. Classify the posting pattern. Test whether consistent stretches outperform bursty ones.

**Step 8 — Assemble structured output.** Compile all sections into JSON.

**Step 9 — Render.** Markdown report.

---

## Alignment Notes

- **Level 4 answers "when," not "what."** It does not analyze content dimensions (that's Level 2). It analyzes temporal dimensions: day, time, frequency, gap, consistency.
- **Small sample caveat.** With 45 posts spread across 7 days of the week, some days will have n < 5. Confidence tagging is essential.
- **Time-of-day is fully stubbed.** `posted_time` is not captured (Tier 2). The section exists in the output structure but returns null until data is available.
- **No recommendations.** Level 4 provides timing evidence. Level 6 builds the calendar.

---

## Current-Scope Query Definitions

Uses the shared base query from `analyze/scripts/shared.py`. See Level 2 spec for shared infrastructure details.

### Section 1 — Posting Frequency

Computed in Python from the master dataset. Posts ordered by `posted_date`, then grouped into rolling 7-day windows. Per-window: count posts, compute mean views/engagement/save rate for those posts.

No additional SQL beyond the shared base query.

### Section 2 — Day-of-Week

Uses `compare_dimension` with `posted_day_of_week` (derived from `posted_date` in Python).

Full coverage: all 45 posts have `posted_date`.

### Section 3 — Time-of-Day

**Fully stubbed.** `posted_time` is NULL for all posts (Tier 2). Output section returns empty groups. Structure preserved for when data becomes available.

### Section 4 — Gap Analysis

Posting gaps computed in Python:
```python
posts_sorted = sorted(posts, key=lambda p: p['posted_date'])
for i, post in enumerate(posts_sorted):
    if i == 0:
        post['days_since_previous'] = None
    else:
        delta = (parse(post['posted_date']) - parse(posts_sorted[i-1]['posted_date'])).days
        post['days_since_previous'] = delta
```

Uses `compare_dimension` with bucketing: 0-1 days, 2-3 days, 4-7 days, 8+ days.

Full coverage: all 45 posts have `posted_date`.

### Section 5 — Consistency Analysis

Computed in Python from the gap values:
- `gap_stddev` = standard deviation of all `days_since_previous` values
- `posting_pattern` = "consistent" if stddev < 2, "bursty" if stddev > 5, "irregular" otherwise
- Consistency-performance signal: compare mean views in low-stddev stretches vs high-stddev stretches (requires sufficient data)

No additional SQL.
