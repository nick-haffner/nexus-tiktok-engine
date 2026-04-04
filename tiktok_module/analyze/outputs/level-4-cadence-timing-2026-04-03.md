# Level 4 Cadence & Timing Optimization

**Analysis period:** all-time  
**Generated:** 2026-04-03T19:36:58.887581+00:00

## Posting Frequency

Overall: **1.6 posts/week** | Frequency-performance correlation: **negative**
*21 weekly periods analyzed, 45 total posts*

## Day-of-Week Performance

### posted_day_of_week

| Value | Posts | Mean Views | Median Views | Eng% | Save% | Follower/1K | Trajectory | Notable |
|---|---|---|---|---|---|---|---|---|
| Friday | 6 (moderate) | 15564.0 | 482.5 | 5.3% | 1.0% | 0.0 | improving | highest mean views |
| Wednesday | 8 (moderate) | 10950.8 | 484.5 | 6.6% | 0.8% | 0.2 | improving |  |
| Tuesday | 10 (high) | 7306.0 | 821.5 | 2.8% | 0.6% | 0.0 | declining | declining trajectory |
| Thursday | 10 (high) | 2978.6 | 353.0 | 4.5% | 0.6% | 0.0 | improving |  |
| Saturday | 3 (low) | 2108.7 | 1507 | 4.7% | 1.0% | 0.0 | stable | highest save rate |
| Monday | 5 (moderate) | 2043.4 | 893 | 4.3% | 1.0% | 0.0 | improving |  |
| Sunday | 3 (low) | 265.0 | 188 | 3.6% | 0.5% | 0.0 | stable | lowest mean views |

## Time-of-Day Performance

*Fully stubbed. `posted_time` is not captured (Tier 2).*

## Gap Analysis

### days_since_previous_post

| Value | Posts | Mean Views | Median Views | Eng% | Save% | Follower/1K | Trajectory | Notable |
|---|---|---|---|---|---|---|---|---|
| 2-3 days | 14 (high) | 15686.1 | 762.0 | 3.8% | 1.1% | 0.0 | declining | highest mean views |
| 8+ days | 7 (moderate) | 5194.7 | 2783 | 4.5% | 1.3% | 0.0 | improving | highest save rate |
| 0-1 days | 16 (high) | 2613.2 | 384.0 | 5.7% | 0.4% | 0.1 | improving |  |
| 4-7 days | 7 (moderate) | 438.6 | 207 | 3.0% | 0.3% | 0.0 | improving | lowest mean views |

*1 post(s) excluded (null value for this dimension).*

**Optimal gap:** 2-3 days (mean views: 15686.1, confidence: high)

## Posting Consistency

Gap standard deviation: **7.3** days | Pattern: **bursty**
Signal: Consistent posting cadence correlates with higher views.

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
