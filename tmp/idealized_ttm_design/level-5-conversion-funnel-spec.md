# Level 5: Conversion Funnel Analysis — Idealized Specification

Generated 2026-04-02.

> **Scope:** This spec is idealized — it assumes access to the full dataset defined in `tmp/idealized_ttm_design/ideal-dataset-spec.md`. Current-scope queries (with stubs for unavailable data) will be appended after approval.

---

## Stated Goals

1. **Determine whether caption and CTA strategy affects engagement and conversion.** The caption is the primary conversion driver in TikTok carousels — slides stay editorial, and the caption does the selling. Level 5 assesses whether caption characteristics (length, CTA presence, product mentions, hashtag strategy) correlate with engagement, saves, and follower conversion.

2. **Identify the optimal caption formula.** What caption length drives the most comments? Does mentioning the waitlist help or hurt engagement? How many hashtags are optimal? Level 5 produces the data that informs Phase 4 (Title, Caption & Hashtags) of the generate procedure.

3. **Assess the view → engage → save → follow → convert funnel.** At each stage, some audience drops off. Level 5 measures the conversion ratios between stages to identify where the funnel leaks. At current scale, the full funnel (through to website/waitlist) isn't measurable — but the content-side funnel (view → engage → save → follow) is.

4. **Track CTA effectiveness over time.** As the product evolves (pre-launch → post-launch), CTA strategy changes. Level 5 provides the baseline to measure whether CTA changes improve or degrade conversion.

5. **Provide the conversion data that Level 6 uses to balance editorial purity with business outcomes.** The tension between "content that performs well on TikTok" and "content that drives business results" is the defining strategic tension for branded accounts. Level 5 gives Level 6 the data to resolve it.

---

## Inputs

| Input | Source | Purpose |
|---|---|---|
| `posts` table | `store/data/analytics/analytics.db` | `description` (caption text), `hashtags` for caption analysis |
| `readings` table | `store/data/analytics/analytics.db` | Engagement, save, follower metrics for funnel analysis |
| `account` table | `store/data/analytics/analytics.db` | Follower trajectory for funnel endpoint |
| Content artifacts | `store/data/posts/{slug}/caption.md` | Structured caption data where available |
| Level 1 structured output | `analyze/outputs/level-1-performance-YYYY-MM-DD.json` | Pre-computed per-post rates (optional) |
| **Analysis period** | Parameter (default: all-time) | Maximizes sample |

---

## Outputs

### Structured Data Layer

**Section 1: Caption Length Analysis**

Groups posts by caption word count (derived from `description`).

| Bucket | Words | Description |
|---|---|---|
| short | <50 | Minimal caption — relies on slides |
| medium | 50-150 | Standard caption with context |
| long | 150+ | Extended caption with tips, story, CTA |

Each bucket:

| Field | Type | Description |
|---|---|---|
| `bucket` | string | short, medium, long |
| `post_count` | int | |
| `mean_views` | float | |
| `mean_engagement_rate` | float | |
| `mean_save_rate` | float | |
| `mean_comment_rate` | float | comments / views * 100 (comments are the engagement type most affected by caption quality) |
| `mean_follower_conversion` | float | |
| `notable` | string or null | |

| Field | Type | Description |
|---|---|---|
| `optimal_length_signal` | string | Which bucket performs best on the primary metric (comment rate), with confidence |
| `data_citation` | string | Backing numbers |

**Section 2: Hashtag Strategy Analysis**

Groups posts by hashtag count (derived from `hashtags`).

| Bucket | Count | Description |
|---|---|---|
| minimal | 0-2 | Minimal hashtags |
| standard | 3-5 | Industry-recommended range (TikTok Creator Portal) |
| heavy | 6+ | Aggressive hashtagging |

Each bucket: same metrics as Section 1.

| Field | Type | Description |
|---|---|---|
| `optimal_hashtag_signal` | string | Which range performs best, with confidence |
| `data_citation` | string | Backing numbers |

**Section 3: CTA & Product Mention Analysis**

Classifies posts by CTA presence and type. Derived from `description` (caption text).

| Field | Type | Description |
|---|---|---|
| `cta_classifications` | array | One per post: `{post_id, slug, has_cta, cta_type, has_product_mention}` |

CTA types:
- `waitlist` — mentions waitlist, sign up, join
- `website` — mentions nexus-concierge.com or URL
- `follow` — asks for follow
- `engage` — asks for save, share, comment
- `none` — no CTA detected

Grouped comparison:

| Field | Type | Description |
|---|---|---|
| `cta_presence` | object | `{with_cta: {count, mean_engagement_rate, mean_save_rate, mean_follower_conversion}, without_cta: {same}}` |
| `cta_type_comparison` | array | One per CTA type with same metrics |
| `product_mention_impact` | object | `{with_mention: {count, mean_engagement_rate, ...}, without_mention: {same}}` |
| `finding` | string | Plain-language summary: "Posts with CTAs have X% higher save rate" or "No measurable difference" |

**Stubbed fields:**
- `cta_text` from DB (Tier 2) — currently derived by parsing `description`
- `profile_visits` per post (Tier 3) — would complete the view → profile → follow funnel

**Section 4: Content Funnel Metrics**

Measures conversion ratios between funnel stages across the full dataset.

| Field | Type | Description |
|---|---|---|
| `funnel_stages` | array | Ordered stages with aggregate rates |

Stages:

| Stage | Metric | Computation |
|---|---|---|
| View | total_views | Sum across all posts |
| Engage | engagement_rate | (likes + comments + shares) / views |
| Save | save_rate | bookmarks / views |
| Follow | follower_conversion | new_followers / views * 1000 |
| Profile visit | profile_visit_rate | profile_visits / views (Tier 3 — **stubbed**) |

| Field | Type | Description |
|---|---|---|
| `stage_dropoffs` | array | Conversion rate between each consecutive stage |
| `funnel_bottleneck` | string | Which stage has the largest relative dropoff — "The biggest leak is between Save and Follow: X% of savers don't follow" |
| `funnel_by_content_type` | object | Same funnel broken out by `content_type` (carousel vs video) — reveals whether content format affects funnel shape |

**Section 5: CTA Evolution Tracking**

Tracks how CTA strategy has changed over time and whether changes correlate with conversion shifts.

| Field | Type | Description |
|---|---|---|
| `cta_timeline` | array | Chronological list of `{posted_date, slug, cta_type, save_rate, follower_conversion}` |
| `phase_comparison` | object or null | If a clear CTA strategy shift is detectable (e.g., started including waitlist mentions after a certain date), compare before/after performance |

### Rendering Layer

| Output | Location | Format |
|---|---|---|
| Structured report data | `analyze/outputs/level-5-conversion-funnel-YYYY-MM-DD.json` | JSON |
| Rendered report | `analyze/outputs/level-5-conversion-funnel-YYYY-MM-DD.md` | Markdown |

---

## Procedure Overview

**Step 1 — Load data.** Connect to DB. Load Level 1 output if available. Parse `description` field for caption analysis.

**Step 2 — Derive caption metrics.** For each post, compute `caption_length_words` and `hashtag_count` from existing fields. Parse `description` for CTA presence and type using keyword matching (waitlist, nexus-concierge.com, sign up, follow, save, share). Classify product mentions.

**Step 3 — Build caption length analysis.** Bucket posts by word count. Compute per-bucket metrics with comment rate as primary.

**Step 4 — Build hashtag strategy analysis.** Bucket posts by hashtag count. Compute per-bucket metrics.

**Step 5 — Build CTA & product mention analysis.** Group posts by CTA presence, CTA type, and product mention presence. Compare metrics across groups.

**Step 6 — Build content funnel.** Compute aggregate funnel stages and conversion ratios. Break out by content type. Identify the bottleneck.

**Step 7 — Build CTA evolution timeline.** Order posts chronologically with CTA classifications. Detect strategy shifts and compare before/after if applicable.

**Step 8 — Assemble structured output.** Compile all sections into JSON.

**Step 9 — Render.** Markdown report with funnel visualization (text-based), comparison tables, and timeline.

---

## Alignment Notes

- **Caption parsing is heuristic, not perfect.** CTA detection via keyword matching will have false positives and negatives. This is acceptable at current scale — the classifications can be manually reviewed and corrected. When `cta_text` is captured during production (Tier 2), the heuristic is replaced.
- **The funnel is incomplete without Tier 3 data.** Profile visits and traffic source breakdown would close the gap between "save" and "follow." Currently the funnel jumps from save rate to follower conversion without knowing what happens in between.
- **Level 5 is the most data-constrained level.** Many of its ideal inputs (cta_text, profile_visits, traffic sources) are Tier 2-3. The current-scope implementation will be thinner than Levels 2-4. This is expected — Level 5 grows as data collection improves.
- **No recommendations.** Level 5 presents conversion data. Level 6 decides how aggressive to be with CTAs and product mentions.

---

## Current-Scope Query Definitions

Uses the shared base query from `analyze/scripts/shared.py`. See Level 2 spec for shared infrastructure details.

### Section 1 — Caption Length

Derived in Python: `caption_length_words = len(description.split())` for each post. Uses `compare_dimension` with bucketing: short (<50 words), medium (50-150), long (150+).

Full coverage: 45/45 posts have `description`.

### Section 2 — Hashtag Strategy

Derived in Python: `hashtag_count = len(hashtags.split(','))` where hashtags is not null. Uses `compare_dimension` with bucketing: minimal (0-2), standard (3-5), heavy (6+).

Coverage: 44/45 posts have `hashtags`.

### Section 3 — CTA & Product Mention

CTA classification derived by keyword matching against `description`:

```python
CTA_PATTERNS = {
    'waitlist': ['waitlist', 'wait list', 'sign up', 'join'],
    'website': ['nexus-concierge.com', 'nexusconcierge.com'],
    'follow': ['follow us', 'follow for', 'give us a follow'],
    'engage': ['save this', 'share this', 'comment', 'bookmark'],
}

PRODUCT_KEYWORDS = ['nexus', 'concierge', 'local friend', 'local recs']
```

Grouped comparison computed in Python. No additional SQL.

**Stubs:**
- `cta_text` from DB (Tier 2) → null; heuristic parsing of `description` used instead
- `profile_visits` (Tier 3) → null; funnel stage between save and follow is incomplete

### Section 4 — Content Funnel

Aggregate funnel computed from the master dataset:

```python
total_views = sum(views)
engagement_rate = sum(likes + comments + shares) / total_views
save_rate = sum(bookmarks) / total_views
follower_conversion = sum(new_followers) / total_views * 1000  # per 1K views
# profile_visit_rate → null (Tier 3 stub)
```

Broken out by `content_type` (carousel vs video) using the same computation per group.

Bottleneck detection: identify which stage-to-stage conversion has the largest relative dropoff.

**Current limitation:** funnel jumps from save_rate to follower_conversion without profile_visit data in between.

### Section 5 — CTA Evolution Timeline

Computed in Python. Posts ordered chronologically with CTA classifications appended. Phase comparison: if a detectable shift exists (e.g., first N posts have no CTA, later posts do), compare mean save_rate and follower_conversion before/after the shift.

No additional SQL.
