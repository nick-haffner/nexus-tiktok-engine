# Level 4: Cadence & Timing Optimization

Analyzes posting frequency, day-of-week patterns, time-of-day patterns, gap impact, and posting consistency to inform content calendar decisions.

**Idealized spec:** `tmp/idealized_ttm_design/level-4-cadence-timing-spec.md`

## When to Run

- **Monthly** as part of the standard analyze cadence.
- **On demand** when revisiting the posting schedule.

## Inputs

| Input | Location | Required |
|---|---|---|
| Analytics database | `store/data/analytics/analytics.db` | Yes |
| Level 1 output (optional) | `analyze/outputs/level-1-performance-YYYY-MM-DD.json` | No — can query directly |
| Analysis period | Parameter (default: all-time) | Yes |

## Outputs

| Output | Location | Format |
|---|---|---|
| Structured report data | `analyze/outputs/level-4-cadence-timing-YYYY-MM-DD.json` | JSON |
| Rendered report | `analyze/outputs/level-4-cadence-timing-YYYY-MM-DD.md` | Markdown |

## Procedure

### Step 1 — Load Data

Load the master dataset using the shared base query (same as Level 2). Compute per-post derived fields.

### Step 2 — Compute Posting Gaps

Order all posts by `posted_date`. For each post, compute `days_since_previous_post`. Derive `posted_day_of_week` from `posted_date`.

### Step 3 — Build Posting Frequency Analysis

Group posts into rolling 7-day windows. For each window, compute:
- `posts_count` — posts published in the window
- `mean_views`, `mean_engagement_rate`, `mean_save_rate` — for posts in the window

Compute overall `posts_per_week` average. Assess frequency-performance correlation: do higher-frequency weeks produce better or worse per-post performance?

### Step 4 — Build Day-of-Week Comparison

Use the shared `compare_dimension` function with `posted_day_of_week` (Monday-Sunday).

Full coverage: all 45 posts have `posted_date`.

Each group: `post_count`, `mean_views`, `median_views`, `mean_engagement_rate`, `mean_save_rate`, `notable` flag.

**Small sample caveat:** 45 posts across 7 days means some days will have n < 5. Confidence tagging applies.

### Step 5 — Build Time-of-Day Comparison

**Fully stubbed.** `posted_time` is NULL for all posts (Tier 2). Output section returns empty groups with the bucket structure preserved (morning, midday, evening, night).

### Step 6 — Build Gap Analysis

Use the shared `compare_dimension` function with `days_since_previous_post`, bucketed:
- 0-1 days (back-to-back)
- 2-3 days
- 4-7 days
- 8+ days

Each bucket: `post_count`, `mean_views`, `mean_engagement_rate`, `mean_save_rate`, `notable` flag.

Determine `optimal_gap_signal`: which bucket performs best, with confidence level.

### Step 7 — Build Consistency Analysis

From the posting gap values:
- `gap_stddev` — standard deviation of `days_since_previous_post`
- `posting_pattern` — "consistent" (stddev < 2), "bursty" (stddev > 5), "irregular" (between)
- `consistency_performance_signal` — compare mean views in consistent stretches vs bursty stretches (null if insufficient data to segment)

### Step 8 — Assess Data Coverage

Report stubbed fields (`posted_time`), overall data completeness.

### Step 9 — Assemble Structured Output

```json
{
  "report_type": "level_4_cadence_timing",
  "generated_at": "ISO datetime",
  "analysis_period": "all-time",
  "posting_frequency": { ... },
  "day_of_week": [ ... ],
  "time_of_day": [ ... ],
  "gap_analysis": { ... },
  "consistency": { ... },
  "missing_data": { ... }
}
```

Write to `analyze/outputs/level-4-cadence-timing-YYYY-MM-DD.json`.

### Step 10 — Render

Markdown report with:
- Frequency analysis summary with correlation finding
- Day-of-week comparison table
- Time-of-day section (stubbed note)
- Gap analysis comparison table with optimal signal
- Consistency classification and signal
- Data coverage section

Write to `analyze/outputs/level-4-cadence-timing-YYYY-MM-DD.md`.

Report to console: "Level 4 report generated: analyze/outputs/level-4-cadence-timing-YYYY-MM-DD.md"

### Step 11 — Generate Insight Brief

Read the JSON output from Step 9. Produce a 300-500 word natural language interpretation focused on cadence and timing implications. Target sections:

**Cadence Assessment** (2-3 sentences): Interpret the overall posting frequency against industry benchmarks. Assess the frequency-performance correlation honestly — distinguish between causal relationships and confounded signals (e.g., account maturation).

**Gap Signal** (3-4 sentences): Interpret the gap analysis. Which bucket performs best and at what confidence? What rhythm does this suggest? Compare against the frequency finding.

**Day-of-Week Patterns** (2-3 sentences): Interpret day comparisons with appropriate caveats for sample size. Identify which days show consistent strength vs. which are driven by outliers.

**Posting Pattern** (2-3 sentences): Interpret the consistency analysis. Is the account consistent, bursty, or irregular? Does regularity correlate with performance?

**Cross-Level Analytical Questions** (3-5 bullets): Investigative prompts for other levels.

**Questions Requiring Human Assessment** (2-4 bullets): Each tagged `[structural]` or `[addressable]`. Operational questions (e.g., "is the bursty pattern caused by production bottlenecks?") are tagged `[structural]` as they require human context.

Write to `analyze/outputs/level-4-insights-YYYY-MM-DD.md`.

Report to console: "Level 4 insight brief generated: analyze/outputs/level-4-insights-YYYY-MM-DD.md"

---

## Outputs Summary

| Output | Location | Purpose |
|---|---|---|
| Structured data (JSON) | `analyze/outputs/level-4-cadence-timing-YYYY-MM-DD.json` | Canonical data consumed by synthesis phase |
| Data report (Markdown) | `analyze/outputs/level-4-cadence-timing-YYYY-MM-DD.md` | Human-readable timing tables |
| Insight brief (Markdown) | `analyze/outputs/level-4-insights-YYYY-MM-DD.md` | Natural language interpretation of cadence signals |

---

## Important Constraints

- **Level 4 answers "when," not "what."** Content dimensions are Level 2's domain.
- **Time-of-day is fully stubbed.** Returns null until `posted_time` is captured.
- **Small samples per day.** Confidence tagging essential.
- **Distinguish correlation from causation.** Name confounds (e.g., posting frequency vs. account maturation).
- **No recommendations.** Level 4 provides timing evidence. The synthesis phase builds the calendar.
- **See `analyze/ANALYSIS-PROCESS.md`** for gap taxonomy, run modes, and insight brief standards.
