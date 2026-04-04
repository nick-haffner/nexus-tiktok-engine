# Level 5: Conversion Funnel Analysis

Analyzes caption strategy, hashtag effectiveness, CTA impact, and the content-to-follower conversion funnel to inform how the team balances editorial content with business outcomes.

**Idealized spec:** `tmp/idealized_ttm_design/level-5-conversion-funnel-spec.md`

## When to Run

- **Monthly** as part of the standard analyze cadence.
- **On demand** when evaluating CTA strategy or caption approach.

## Inputs

| Input | Location | Required |
|---|---|---|
| Analytics database | `store/data/analytics/analytics.db` | Yes |
| Level 1 output (optional) | `analyze/outputs/level-1-performance-YYYY-MM-DD.json` | No — can query directly |
| Analysis period | Parameter (default: all-time) | Yes |

## Outputs

| Output | Location | Format |
|---|---|---|
| Structured report data | `analyze/outputs/level-5-conversion-funnel-YYYY-MM-DD.json` | JSON |
| Rendered report | `analyze/outputs/level-5-conversion-funnel-YYYY-MM-DD.md` | Markdown |

## Procedure

### Step 1 — Load Data

Load the master dataset using the shared base query (same as Level 2). Compute per-post derived fields.

### Step 2 — Derive Caption Metrics

For each post, compute from existing fields:
- `caption_length_words = len(description.split())` (where description is not null)
- `hashtag_count = len(hashtags.split(','))` (where hashtags is not null)

Parse `description` for CTA presence using keyword matching:

```python
CTA_PATTERNS = {
    'waitlist': ['waitlist', 'wait list', 'sign up', 'join'],
    'website': ['nexus-concierge.com', 'nexusconcierge.com'],
    'follow': ['follow us', 'follow for', 'give us a follow'],
    'engage': ['save this', 'share this', 'comment', 'bookmark'],
}
PRODUCT_KEYWORDS = ['nexus', 'concierge', 'local friend', 'local recs']
```

Classify each post: `has_cta`, `cta_type`, `has_product_mention`.

**Note:** This is heuristic parsing. When `cta_text` is captured during production (Tier 2), the heuristic is replaced.

### Step 3 — Build Caption Length Analysis

Use the shared `compare_dimension` function with `caption_length_words`, bucketed:
- short (<50 words)
- medium (50-150 words)
- long (150+ words)

Primary metric: `mean_comment_rate` (comments / views * 100) — comments are the engagement type most affected by caption quality.

Secondary: `mean_engagement_rate`, `mean_save_rate`, `mean_follower_conversion`.

Full coverage: 45/45 posts have `description`.

### Step 4 — Build Hashtag Strategy Analysis

Use the shared `compare_dimension` function with `hashtag_count`, bucketed:
- minimal (0-2)
- standard (3-5)
- heavy (6+)

Same metrics as Step 3. Coverage: 44/45 posts have `hashtags`.

### Step 5 — Build CTA & Product Mention Analysis

Group posts by:
1. `has_cta` (yes/no) — compare metrics between posts with and without any CTA
2. `cta_type` — compare metrics across CTA types (waitlist, website, follow, engage, none)
3. `has_product_mention` (yes/no) — compare metrics between posts that mention the product and those that don't

For each grouping, compute: `post_count`, `mean_engagement_rate`, `mean_save_rate`, `mean_follower_conversion`.

Generate a plain-language finding summarizing the result.

**Stubbed:** `profile_visits` per post (Tier 3) — would complete the CTA-to-conversion picture.

### Step 6 — Build Content Funnel

Compute aggregate funnel stages from the full dataset:

| Stage | Metric | Computation |
|---|---|---|
| View | total_views | Sum across all posts |
| Engage | engagement_rate | (likes + comments + shares) / views * 100 |
| Save | save_rate | bookmarks / views * 100 |
| Follow | follower_conversion | new_followers / views * 1000 |
| Profile visit | profile_visit_rate | **Stubbed** (Tier 3) |

Compute stage-to-stage dropoff ratios. Identify the bottleneck (largest relative dropoff).

Break out by `content_type` (carousel vs video) to reveal whether content format affects funnel shape.

**Current limitation:** Funnel jumps from save to follow without profile visit data.

### Step 7 — Build CTA Evolution Timeline

Order posts chronologically with CTA classifications. Detect strategy shifts: if early posts have no CTA and later posts do (or vice versa), compare before/after performance.

Output: timeline array of `{posted_date, slug, cta_type, save_rate, follower_conversion}` plus optional phase comparison.

### Step 8 — Assess Data Coverage

Report stubbed fields (`cta_text`, `profile_visits`), heuristic parsing limitations, Nexus metadata coverage.

### Step 9 — Assemble Structured Output

```json
{
  "report_type": "level_5_conversion_funnel",
  "generated_at": "ISO datetime",
  "analysis_period": "all-time",
  "caption_length": { ... },
  "hashtag_strategy": { ... },
  "cta_analysis": { ... },
  "content_funnel": { ... },
  "cta_timeline": { ... },
  "missing_data": { ... }
}
```

Write to `analyze/outputs/level-5-conversion-funnel-YYYY-MM-DD.json`.

### Step 10 — Render

Markdown report with:
- Caption length comparison table
- Hashtag strategy comparison table
- CTA impact summary with findings
- Funnel visualization (text-based stage diagram with dropoff percentages)
- CTA timeline (chronological table)
- Data coverage section

Write to `analyze/outputs/level-5-conversion-funnel-YYYY-MM-DD.md`.

Report to console: "Level 5 report generated: analyze/outputs/level-5-conversion-funnel-YYYY-MM-DD.md"

### Step 11 — Generate Insight Brief

Read the JSON output from Step 9. Produce a 300-500 word natural language interpretation with full content access.

**CTA Impact** (3-5 sentences): Lead with the CTA-save correlation. Name the confound with content type. Interpret across CTA types. Note the engagement-save trade-off if present.

**Caption Quality Assessment** (full content access): Read `description` field holistically and `caption.md` / `copy.md` where available for all posts. Move beyond keyword classification to assess:
- CTA phrasing quality — not just presence, but whether the CTA is compelling, organic, or forced
- Caption structure and readability
- Relationship between slide copy and caption copy
- Whether product mentions feel native or inserted

**Product Mentions** (2-3 sentences): Interpret with awareness of classifier limitations. Cross-reference heuristic classification against actual content read.

**Caption and Hashtag Patterns** (2-3 sentences): Interpret with confound caveats.

**The Funnel** (2-3 sentences): Name the bottleneck. Note what Tier 3 data would reveal.

**CTA Evolution** (2-3 sentences): Interpret timeline. Name what can and cannot be attributed to the strategy shift.

Read market research files (`store/data/market-research/`) for caption length benchmarks, hashtag best practices, and CTA research.

**Cross-Level Analytical Questions** (3-5 bullets): Investigative prompts for other levels.

**Questions Requiring Human Assessment** (2-4 bullets): Each tagged `[structural]` or `[addressable]`. CTA quality judgments are `[structural]`. Data collection gaps are `[addressable]`.

Write to `analyze/outputs/level-5-insights-YYYY-MM-DD.md`.

Report to console: "Level 5 insight brief generated: analyze/outputs/level-5-insights-YYYY-MM-DD.md"

---

## Outputs Summary

| Output | Location | Purpose |
|---|---|---|
| Structured data (JSON) | `analyze/outputs/level-5-conversion-funnel-YYYY-MM-DD.json` | Canonical data consumed by synthesis phase |
| Data report (Markdown) | `analyze/outputs/level-5-conversion-funnel-YYYY-MM-DD.md` | Human-readable funnel and comparison tables |
| Insight brief (Markdown) | `analyze/outputs/level-5-insights-YYYY-MM-DD.md` | Conversion analysis with full content access |

---

## Important Constraints

- **Full content access in insight brief.** Level 5's goal requires evaluating captions and CTAs. The data report uses heuristic classification; the insight brief supplements with qualitative assessment.
- **Caption parsing is heuristic in the data report.** The insight brief must name classifier limitations and cross-reference against actual content.
- **The funnel is incomplete.** Profile visits (Tier 3) would fill the Save→Follow gap.
- **Confounds must be named.** CTA presence, content type, and account maturation are intertwined.
- **No recommendations.** Level 5 presents conversion data. The synthesis phase decides CTA and caption strategy.
- **See `analyze/ANALYSIS-PROCESS.md`** for gap taxonomy, run modes, and insight brief standards.
