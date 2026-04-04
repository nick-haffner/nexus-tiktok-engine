# Level 5 Conversion Funnel Analysis

**Analysis period:** all-time  
**Generated:** 2026-04-03T19:36:59.005592+00:00

## Caption Length

### caption_length_words

| Value | Posts | Mean Views | Median Views | Eng% | Save% | Follower/1K | Trajectory | Notable |
|---|---|---|---|---|---|---|---|---|
| short (<50) | 33 (high) | 7656.1 | 323 | 5.3% | 0.8% | 0.0 | declining | highest mean views |
| medium (50-150) | 9 (moderate) | 4523.6 | 778 | 2.5% | 0.5% | 0.2 | improving |  |
| long (150+) | 3 (low) | 2603.0 | 865 | 2.6% | 0.7% | -- | stable | lowest mean views |

**Optimal for comments:** short (<50) (mean comment rate: 0.3%, confidence: high)

## Hashtag Strategy

### hashtag_count

| Value | Posts | Mean Views | Median Views | Eng% | Save% | Follower/1K | Trajectory | Notable |
|---|---|---|---|---|---|---|---|---|
| heavy (6+) | 20 (high) | 9656.2 | 369.0 | 4.9% | 0.7% | 0.1 | improving | highest mean views |
| standard (3-5) | 24 (high) | 4494.4 | 706.0 | 4.4% | 0.8% | 0.0 | declining | highest save rate |
| minimal (0-2) | 1 (low) | 183.0 | 183 | 1.6% | 0.6% | 0.0 | -- | lowest mean views |

**Optimal range:** heavy (6+) (mean views: 9656.2, confidence: high)

## CTA & Product Mention Impact

**Finding:** Posts with CTAs have 3.9x higher save rate than posts without.

| Group | Posts | Eng% | Save% | Follower/1K |
|---|---|---|---|---|
| With CTA | 16 | 3.4% | 1.4% | 0.0 |
| Without CTA | 29 | 5.2% | 0.4% | 0.1 |

**By CTA type:**

| Type | Posts | Eng% | Save% | Follower/1K |
|---|---|---|---|---|
| engage | 10 | 3.0% | 1.4% | 0.0 |
| follow | 2 | 5.2% | 2.4% | 0.0 |
| none | 29 | 5.2% | 0.4% | 0.1 |
| waitlist | 2 | 2.7% | 0.9% | -- |
| website | 2 | 4.4% | 1.0% | 0.0 |

**Product mention:**
- With mention: 16 posts, eng 5.0%, save 0.4%
- Without mention: 29 posts, eng 4.3%, save 0.9%

## Content Funnel

| Stage | Value |
|---|---|
| View | 301174 |
| Engage | 4.89% |
| Save | 2.86% |
| Follow | 0.21 per 1K views |
| Profile Visit | -- (stub) |

**Largest dropoff: Save -> Follow (ratio: 0.007)**

**By content type:**

| Type | Posts | Eng% | Save% | Follower/1K |
|---|---|---|---|---|
| carousel | 27 | 4.87% | 2.91% | 0.2 |
| video | 18 | 5.78% | 0.27% | -- |

## CTA Evolution Timeline

**Shift detected:** CTA usage went from 22.7% to 47.8%.
Save rate: 0.7% -> 0.8%

## Data Coverage

**Classification coverage:**

| Field | Populated | Coverage |
|---|---|---|
| framework | 7/45 | 16% |
| slide_layout | 4/45 | 9% |
| city | 29/45 | 64% |

**Stubbed columns (not yet collected):**

- `posts.posted_time` (Tier 2) -- Posting time of day
- `posts.sound_type` (Tier 2) -- Sound classification (trending/original/licensed)
- `readings.profile_visits` (Tier 3) -- Profile visits per post
- `readings.search_percent` (Tier 3) -- Traffic source: search
- `readings.profile_percent` (Tier 3) -- Traffic source: profile
- `readings.following_percent` (Tier 3) -- Traffic source: following
- `readings.other_percent` (Tier 3) -- Traffic source: other

**Addressable gaps:**

- **Competitive context** (L1, L2, Synthesis): Add competitor tracking via manual research or third-party tools
- **Classification metadata** (L2, L3): Backfill existing posts or capture during generate procedure (38/45 lack framework)
- **Content artifacts** (L2, L3, L5): Automate capture during generate and discover procedures (~37/45 lack copy.md)
- **posted_time** (L4): Add to Phase 2 collect or discover enrichment
- **Follower attribution** (L3): Capture fresh readings going forward to determine if backfill data is artifactual
- **Profile visits** (L5): Expand Phase 2 collect to capture profile_visits per post
- **Traffic source breakdown** (L3): Expand Phase 2 collect (only fyp_percent currently captured)
- **CTA heuristic accuracy** (L5): Populate carousel_details.cta_type and cta_text during generate procedure (currently keyword-matched from description)
- **sound_name / sound_type** (L2): Collect sound_name during enrichment, tag sound_type during production

**Structural gaps (accepted by procedure):**

- **Creative judgment** (L2, L3, L5, Synthesis): Assessing hook appeal, caption authenticity, visual energy. Engine performs structured analysis and surfaces questions for human judgment.

Account checkpoints: 1
