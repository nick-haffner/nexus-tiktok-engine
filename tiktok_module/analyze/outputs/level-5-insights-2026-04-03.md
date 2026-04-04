# Level 5 Insight Brief

**Period:** All-time (45 posts) | **Generated:** 2026-04-03

---

## CTA Impact

Posts with CTAs have **3.9x higher save rate** (1.4% vs 0.36%). This is the strongest conversion signal. However, the causation is ambiguous: CTA-containing posts are disproportionately recent carousels, while no-CTA posts are early videos. The CTA effect and the carousel effect are confounded. Among CTA types, "engage" (save this, share this) appears most often (n=10) with a 1.38% save rate. "Follow" shows the highest rate (2.37%) but at n=2 — noise. Engagement rate is *lower* on CTA posts (3.4% vs 5.17%), suggesting CTAs encourage saves at the cost of active interaction.

## Caption Quality Assessment

Reading the actual captions of top performers reveals a consistent pattern: **short, punchy hook sentence + "save this for your trip" CTA + city-specific hashtags.** Seattle (91K, 4.48% save rate): "Tourist spots are popular for a reason — but this is how locals actually do it. Save this for your trip." Phoenix (63K, 3.02%): "Phoenix isn't just malls and Camelback — Here's how locals upgrade the classic tourist spots. Save this for your next trip." Both use the "save this" framing naturally within the opening sentence rather than as a bolted-on CTA. The CTA feels like advice, not a directive.

Per carousel-branding-and-conversion.md, native-feeling CTAs convert 2-3x better than polished ones. The top performers exemplify this — the "save this for your trip" phrasing is functional (it tells you *why* to save) rather than promotional.

Dallas (54K, 2.42%) uses a slightly different pattern: emoji contrast framing followed by "Save this before your trip." Still effective but more directive and less organic than the Seattle/Phoenix approach.

## Product Mentions

Posts mentioning Nexus/concierge show **lower save rates** (0.36% vs 0.94%). However, the heuristic classifier is unreliable here — "nexus" appears in early-era posts as incidental mentions, not structured product CTAs. The recent posts with intentional product positioning (Nashville's "waitlist" CTA, LA's "follow" CTA) are too few to compare. This finding should be discounted until cta_text is captured during production.

## The Funnel

Aggregate: 4.89% engagement → 2.86% save → 0.21 followers/1K views. The **Save → Follow bottleneck** is severe (ratio: 0.007). Many viewers save posts but almost none follow. Without profile visit data, we can't see the middle step. Carousels drive nearly all saves (2.91% vs 0.27% for video).

## CTA Evolution

CTA usage shifted from 22.7% to 47.8% between the first and second halves of post history, with save rates rising from 0.66% to 0.80%. The shift coincides with the transition to carousels and improved content quality — isolating the CTA effect is not possible at current volume.

## Cross-Level Analytical Questions

- Does the CTA-save correlation hold when restricted to carousels only? (reanalysis with content_type control)
- What's happening between Save and Follow? (Tier 3 data gap — profile visits)
- Does the "save this for your trip" phrasing specifically drive saves, or is it the overall caption quality? (requires more data points)

## Questions Requiring Human Assessment

- `[structural]` The top performers use "save this for your trip" as organic advice rather than a directive CTA. Is this replicable as a formula, or does it risk becoming formulaic? Assessing caption authenticity requires human judgment.
- `[addressable]` The product mention classifier misattributes early posts. Manual review of the 16 classified posts would clarify, or capturing cta_text during production would replace the heuristic entirely.
- `[addressable]` Profile visit data would reveal the Save→Follow bottleneck's cause. Is it that savers don't visit the profile, or that they visit but don't follow? Expanding Phase 2 collect would answer this.
- `[structural]` Should captions stay short (current top performers average <50 words) and let slides carry the content, or would longer captions with embedded tips drive more comments? The data suggests short works, but the sample may reflect a confound with content maturation rather than a caption-length effect.
