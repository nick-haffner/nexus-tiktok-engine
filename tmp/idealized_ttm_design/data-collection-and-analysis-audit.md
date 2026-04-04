# Data Collection & Analysis Audit

Generated 2026-04-02. Guides the remaining work on the analyze function and data collection evolution.

> **Staleness note (2026-04-03):** The "Current Data Collection" and "Current Data Snapshot" sections below describe the pre-backfill state (45 posts, 1 checkpoint, v1 schema). The database has since been migrated to v3 and stripped for a clean backfill. The "Ideal State" and "Ideal Analysis" sections remain valid as design references. For current schema, see `store/docs/analytics-schema.md`. For current data state, see `tmp/idealized_ttm_design/ideal-dataset-spec.md`.

---

## Current Data Collection: What We Have

### Post Metadata (45 posts)
| Data Point | Source | Completeness |
|---|---|---|
| post_id, posted_date | Registration | 100% |
| description, hashtags | TikTok API enrichment | 100% |
| content_type, aweme_type, sound_name, slide_count | TikTok API enrichment | 100% |
| slug, city, hook_text, framework, angle | Repo directory + README.md parsing | Partial (~27 of 45) |
| Slide images, visual summaries | API download + AI generation | Partial |
| copy.md, README.md | Engine-produced posts only | ~15-20 posts |

### Performance Readings (45 readings across 45 posts)
| Metric | Velocity | Snapshot | Notes |
|---|---|---|---|
| views, likes, comments, shares, bookmarks | Yes | Yes | Core 5, always captured |
| new_followers | No | Yes | Snapshot only |
| avg_watch_time_seconds | No | Yes | Snapshot only |
| watched_full_percent | No | Yes | Snapshot only |
| fyp_percent | No | Yes | Snapshot only |

Snapshot windows: 48h, 7d, 30d (conditional). Currently 42 snapshots, 3 velocity reads.

### Account State (1 checkpoint)
- Followers: 443
- Total likes: 13,000
- As of: 2026-04-01

### Computed at Query Time (Not Stored)
- Engagement rate: `(likes + comments + shares) / views`
- Save rate: `bookmarks / views`
- Followers per 1K views: `new_followers * 1000 / views`

---

## Ideal State: What the Engine Should Capture

### Tier 1 — Derivable from existing data with no new collection

| Data Point | Source | Value |
|---|---|---|
| **Posting day of week** | `posted_date` | Cadence and timing analysis |
| **Posting hour** | Not captured — need to add to collection | Timing optimization |
| **Caption length** (chars, words) | `description` field | Correlation with performance |
| **Hashtag count** | `hashtags` field | Optimal hashtag volume |
| **Days since previous post** | `posted_date` sequence | Cadence impact on reach |
| **Framework/angle for all posts** | Many posts lack this — 18 of 45 have no framework | Cross-post strategic comparison |
| **Engagement rate, save rate, follower conversion** | Computed from existing columns | Should be surfaced in analysis, not stored |

### Tier 2 — Capturable with minor collection changes

| Data Point | Source | Change Required |
|---|---|---|
| **Post time (hour)** | TikTok Studio detail page | Add to Phase 2 collect or discover enrichment |
| **Sound type classification** | `sound_name` + manual tag | Trending vs. original vs. licensed — tag during production or enrichment |
| **CTA text used** | `copy.md` or `description` | Parse from caption or store during production |
| **Content topic tags** | `description` + `copy.md` | Food, nightlife, views, outdoors, etc. — tag during production |

### Tier 3 — Requires new collection infrastructure

| Data Point | Source | Value | Feasibility |
|---|---|---|---|
| **Follower growth between checkpoints** | Account table, more frequent checkpoints | Growth velocity, content-to-growth correlation | Easy — increase checkpoint cadence to daily or per-capture |
| **Traffic source breakdown beyond FYP%** | TikTok Studio analytics tab | Search, profile, following, other — matters as account grows | Medium — requires expanding Phase 2 collect |
| **Comment content/sentiment** | TikTok API or Studio | Audience intent signals, content resonance | Medium — new collection step |
| **Profile visits per post** | TikTok Studio post detail | Conversion funnel: view → profile → follow | Medium — add to snapshot collection |
| **Video/carousel completion by slide** | TikTok Studio (if available) | Identifies where viewers drop off | Hard — TikTok may not expose per-slide data |
| **Competitor benchmarks** | Manual research or scraping | Context for "what good looks like" | Hard — not automatable |

### Tier 4 — External data for context

| Data Point | Source | Value |
|---|---|---|
| **Trending sounds in niche** | TikTok Creative Center, manual | Sound selection optimization |
| **Category/niche benchmarks** | Industry reports, competitor observation | "Is 3% engagement good for travel content?" |
| **Platform algorithm changes** | TikTok announcements, creator community | Explains sudden performance shifts |
| **Seasonal travel demand** | Search trends, travel industry data | Content timing optimization |

---

## Ideal Analysis: What a Marketing Team Would Run Against This Data

An industry-aligned TikTok marketing operation at this stage (sub-1K followers, ~45 posts, growth phase) would perform these analyses on a regular cadence. Organized by the questions they answer, not by technique.

### 1. Performance Reporting — "How are we doing?"

**Cadence:** Weekly

- **Aggregate dashboard**: Total views, likes, comments, shares, bookmarks, followers — trailing 7d, 30d, all-time. Week-over-week and month-over-month deltas.
- **Account growth trajectory**: Follower growth rate, total likes growth rate. Are we accelerating or decelerating?
- **Per-post performance table**: Every post from the reporting period ranked by views, engagement rate, save rate, follower conversion. Highlights top and bottom performers.
- **Views distribution**: Median vs. mean views. At sub-1K followers, a single viral post skews the mean. Median is the real baseline.

*Industry standard: Every social media team from solo creators to agencies runs a weekly performance roll-up. The sophistication varies, but the core metrics are universal.*

### 2. Content Strategy Analysis — "What's working and what isn't?"

**Cadence:** Bi-weekly or monthly

- **Framework performance comparison**: Average and median views, engagement rate, save rate, and follower conversion by framework (Local vs Tourist, Worth It, 24-Hour Test, etc.). With 45 posts, sample sizes are small but directional.
- **Angle performance comparison**: Broad city guide vs. deep-dive vs. curated list. Same metrics.
- **Format performance comparison**: Combined vs. split vs. single-point.
- **Hook style analysis**: Group hooks by type (curiosity, contrast, bold claim, list) and compare 48h velocity. The hook determines initial distribution — this is the highest-leverage creative variable.
- **Slide count correlation**: Does 6 slides outperform 9? Save rate and watched_full_percent are the key signals here.
- **City/geography analysis**: Which cities drive the most views? Is there a home-market advantage (Dallas)? Are some cities saturated?
- **Content mix audit**: What percentage of recent posts used each framework? Are we over-indexing on one approach? Diversity prevents audience fatigue.

*Industry standard: Agencies call this "content pillar analysis" — breaking content into strategic categories and measuring each one's contribution. Best practice is to maintain 3-5 content pillars and rebalance based on performance.*

### 3. Audience & Growth Analysis — "Who's responding and how fast are we growing?"

**Cadence:** Monthly

- **Follower acquisition efficiency**: New followers per post, per 1K views. Which content types drive follows vs. just views?
- **Engagement quality segmentation**: High views + low engagement = broad but shallow reach. Low views + high engagement = niche but loyal. Map each post on this grid.
- **Save rate as lead indicator**: Saves signal "I want to come back to this" — the strongest intent signal on TikTok. High save rate posts should inform future strategy even if view counts are modest.
- **FYP% trend**: At 96-99% FYP currently, this is expected for a growth-phase account. But tracking the trend matters — as the account grows, profile and search traffic should increase. If FYP% stays at 99% at 5K followers, the content isn't building a return audience.

*Industry standard: Growth-phase accounts focus on follower acquisition efficiency and engagement quality over raw view counts. Agencies use engagement-to-view ratios as the primary quality signal.*

### 4. Cadence & Timing Optimization — "When and how often should we post?"

**Cadence:** Monthly

- **Posting frequency impact**: Plot posts per week against average views per post. Is there a diminishing return from posting too frequently? Is there a drop-off from gaps?
- **Day-of-week analysis**: Average views by posting day (requires post time data — currently missing).
- **Time-of-day analysis**: Same (requires posting hour — currently missing).
- **Gap analysis**: Does a 3-day gap before a post correlate with higher initial velocity? TikTok's algorithm may favor accounts that post at a regular cadence vs. bursts.

*Industry standard: Most TikTok agencies recommend 3-5 posts/week for growth-phase accounts. The specific timing matters less than consistency, but Tuesday-Thursday tends to outperform weekends for informational content. Testing is the only real answer.*

### 5. Conversion Funnel Analysis — "Is content driving business outcomes?"

**Cadence:** Monthly

- **CTA effectiveness**: Compare engagement and save rates on posts with different CTA approaches. Does mentioning the waitlist in the caption drive more profile visits?
- **Caption strategy**: Does caption length correlate with save rate or comments? Do posts with specific product mentions ("join Nexus") perform differently than pure editorial?
- **Profile visit → follow conversion**: Requires profile visit data (Tier 3). At this stage, the primary funnel is: FYP impression → view → engage/save → profile visit → follow → (eventually) convert.

*Industry standard: For pre-launch products, the funnel is content → follower → email/waitlist. Agencies track "cost per follower" even for organic content by measuring effort-to-output ratios.*

### 6. Strategic Synthesis — "What should we change?"

**Cadence:** Monthly (operates on the outputs of Levels 1-5, not raw data)

Level 6 is not an analysis of raw data. It never queries the database directly. Its inputs are the outputs of Levels 1-5. It performs four functions:

1. **Coherence check**: Levels 1-5 can produce contradictory signals (e.g., Level 2 says "Local vs Tourist is our best framework" while Level 3 shows those posts have the lowest follower conversion). Level 6 detects these conflicts and resolves them using an explicit priority hierarchy appropriate to the account's current stage and goals.
2. **Synthesis**: Collapses per-level findings into a unified set of account-wide strategic recommendations. The output is not "here's what each level says" — it's "here's what we're doing, informed by all of them."
3. **Contradiction scan**: Checks the synthesized recommendations against the full dataset for patterns the individual levels may have missed (e.g., a "double down on Dallas" recommendation contradicted by a declining-views trajectory across the last 4 Dallas posts — a sequential pattern that Level 2's averages wouldn't surface).
4. **Codification**: Writes the final recommendations as updates to strategy files (`performance-insights.md`, `frameworks.md`, `content-pipeline.md`, and potentially `brand-voice.md`). This is what closes the loop — without it, Level 6 is advice; with it, Level 6 is a state change that the generate function reads on its next run.

The output categories:

- **Double down**: Frameworks/angles/formats/cities with above-median performance across multiple metrics.
- **Deprioritize**: Approaches that consistently underperform. Not "never do again," but reduce frequency.
- **Test**: Hypotheses generated from the data. "Hook style X drives 2x 48h velocity — test it on 3 more posts." "City Y had unusually high save rates — try a deep-dive angle."
- **Content calendar**: Next period's planned posts informed by the above, balancing proven winners with strategic experiments.

*Industry standard: Agencies call this the "insight → action" bridge. The analysis is worthless without a decision. Best practice is to end every review with 3-5 specific action items, each tied to a data point.*

---

## Summary: Gaps Between Current and Ideal

| Dimension | Current | Ideal | Gap |
|---|---|---|---|
| **Metrics captured** | 9 per snapshot | 9 + posting time, profile visits, traffic sources | Missing timing and funnel data |
| **Reading frequency** | 1-2 per post (48h, 7d) | 48h, 7d, + daily account checkpoints | Low temporal resolution on account growth |
| **Post metadata** | 18 of 45 posts have framework/angle | All posts tagged | Classification gap on older/discovered posts |
| **Analysis performed** | None | 6 analysis categories on regular cadence | The entire analyze function is missing |
| **Strategy output** | Empty templates | Populated insights driving content decisions | No feedback loop exists |
| **Competitive context** | None | Niche benchmarks for calibration | No external reference points |

The most impactful gap isn't data collection — it's analysis. The engine already captures enough to run meaningful framework, hook, and format comparisons. The bottleneck is that no procedure reads the data and produces conclusions.
