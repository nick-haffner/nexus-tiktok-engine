# How Each Analysis Level Converts to Strategic Decisions

Generated 2026-04-02. Maps each analysis level to the concrete strategic decisions it produces in a standard marketing department/agency environment.

---

## Level 1: Performance Reporting → Operational health and volume decisions

| Analysis Output | Decision Type | Example Action |
|---|---|---|
| Week-over-week view trend declining | **Alert / investigate** | "Views dropped 40% WoW — check if posting cadence changed or if a platform shift occurred" |
| Follower growth stalling despite steady views | **Strategic pivot** | "Content is reaching people but not converting to follows — review CTA approach and profile optimization" |
| Median views per post rising | **Validate current direction** | "Current strategy is working — maintain framework mix and posting cadence" |
| One post significantly outperforms | **Amplify signal** | "Seattle 12/26 hit 91K views — analyze what was different and replicate the variables" |

*In an agency:* This is the first 5 minutes of the weekly meeting. The account manager presents the dashboard, flags anomalies, and sets the tone: "good week" or "we need to talk about why this dropped." No creative decisions are made here — it's a health check that determines whether the rest of the meeting is "optimize" or "course correct."

---

## Level 2: Content Strategy Analysis → Creative selection and prioritization

| Analysis Output | Decision Type | Example Action |
|---|---|---|
| Local vs Tourist averages 2.5x more views than Worth It | **Framework prioritization** | "Default to Local vs Tourist for the next 4 posts. Use Worth It only for cities where contrast data is weak." → Update `frameworks.md` with performance annotations |
| Curiosity hooks ("spots that are actually worth it") outperform contrast hooks ("Local vs Tourist in X") on 48h velocity | **Hook style directive** | "Lead with curiosity framing in Phase 1. Test contrast hooks only when the city has strong name recognition." → Update `brand-voice.md` or `performance-insights.md` with hook guidance |
| Combined format (tourist + local on same slide) has higher save rate than split | **Format directive** | "Default to combined format. Split only when slide text is too dense for a single image." → Update `frameworks.md` |
| 6-slide carousels outperform 9-slide on watched_full_percent | **Slide count constraint** | "Cap body slides at 4 (6 total with hook + CTA). Only exceed for deep-dive angles with manager approval." → Update `brand-rules.md` text density or add to `performance-insights.md` |
| Dallas posts are saturated — declining views per successive post | **City rotation** | "Pause Dallas for 3 weeks. Prioritize untapped cities (Nashville, Miami, Portland)." → Update `content-pipeline.md` |
| Posts with food-focused categories outperform nightlife | **Topic prioritization** | "Lead with food categories in body slides. Nightlife as supporting, not anchor." → Note in `performance-insights.md` |

*In an agency:* This is the core of the bi-weekly content strategy meeting. The strategist presents comparison tables, the creative team debates what the numbers mean, and the account lead makes the call. The output is a set of creative briefs or guidelines that constrain the next production cycle. The key discipline: decisions must be tied to data points, not opinions. "I feel like Worth It is better" doesn't survive a table showing it underperforms 2.5:1.

---

## Level 3: Audience & Growth Analysis → Audience-fit and engagement quality decisions

| Analysis Output | Decision Type | Example Action |
|---|---|---|
| High-view posts have low follower conversion; low-view posts convert better | **Audience targeting shift** | "Broad reach content isn't building our audience. Shift toward niche, high-intent content (deep-dives, specific recommendations) even at the cost of views." |
| Save rate correlates more strongly with follower growth than view count | **KPI reframing** | "Optimize for save rate, not views. Phase 0 ideation should prioritize 'save-worthy' utility (actionable tips, specific recs) over 'scroll-stopping' spectacle." |
| FYP% not declining as account grows | **Return audience problem** | "Content is disposable — people see it once and don't come back. Consider series-based content or recurring formats that build anticipation." |

*In an agency:* This is the monthly strategy review, often involving the client. The question is "are we building an asset (an audience) or just generating impressions?" Growth-phase accounts that chase views without follower conversion eventually plateau. The decision here is whether to shift the content strategy toward audience-building (niche, specific, high-intent) vs. reach-building (broad, viral, high-volume). This is the highest-level strategic fork.

---

## Level 4: Cadence & Timing Optimization → Content calendar and scheduling decisions

| Analysis Output | Decision Type | Example Action |
|---|---|---|
| 3-day posting gaps correlate with higher next-post velocity | **Cadence rule** | "Post every 3 days, not daily. Quality over volume." → Update `content-pipeline.md` cadence guidance |
| Tuesday-Thursday posts outperform weekend posts | **Scheduling rule** | "Schedule all posts for Tuesday-Thursday. Weekend posts only for time-sensitive content (holidays, events)." |
| Posting frequency above 5/week shows diminishing returns | **Volume cap** | "Cap at 4 posts/week. Reallocate time from production to engagement (commenting, responding)." |

*In an agency:* This is the content calendar meeting. The media planner presents timing data, the team agrees on a cadence, and the calendar is built. In practice, most agencies settle on a cadence early and only revisit it quarterly unless the data shows a clear problem. It's low-frequency, low-drama decision-making — but getting it wrong (posting too much or too little) silently erodes performance.

---

## Level 5: Conversion Funnel Analysis → CTA, caption, and product mention decisions

| Analysis Output | Decision Type | Example Action |
|---|---|---|
| Posts mentioning "waitlist" in caption have 15% higher save rate | **CTA directive** | "Include waitlist CTA in every caption. Phase 4 ChatGPT prompt must include it." → Update Phase 4 procedure |
| Longer captions (150+ words) correlate with higher comment rates | **Caption length rule** | "Minimum 150 words in caption. Include 2-3 bonus tips not on the slides." → Update Phase 4 procedure |
| Posts with product context ("we're building a local friend app") don't hurt engagement | **Product mention green light** | "Safe to include soft product mentions in captions. Don't avoid it — but keep it to 1 sentence max." → Update `brand-voice.md` |
| No measurable difference between CTA variants | **Simplify** | "Standardize on one CTA. Stop A/B testing captions — the variance is noise at this sample size." |

*In an agency:* This is the conversion optimization meeting, often separate from content strategy. The performance marketer presents funnel data, the copywriter adjusts caption templates, and the strategist decides how aggressive to be with product mentions. For pre-launch products, the tension is always "editorial purity vs. conversion pressure." The data resolves it: if product mentions don't hurt engagement, you're leaving conversions on the table by being too editorial.

---

## Level 6: Strategic Synthesis → Concrete strategy updates and experiment design

| Analysis Output | Decision Type | Example Action |
|---|---|---|
| Synthesis of Levels 1-5 | **Double down** | "Local vs Tourist + combined format + curiosity hooks is our proven formula. 60% of next month's posts should use this combination." |
| Underperformers identified | **Deprioritize** | "Single-point format underperforms on save rate. Pause unless testing a specific hypothesis." |
| Hypothesis from Level 2 data | **Experiment design** | "Hypothesis: category deep-dive angle will outperform broad city guide on save rate. Test: produce 3 deep-dives over the next 2 weeks, measure against broad guide baseline." |
| All of the above | **Strategy file updates** | Write findings to `performance-insights.md`. Annotate `frameworks.md` with performance data. Update `content-pipeline.md` with next month's planned posts. |

*In an agency:* This is how the meeting ends. The account lead summarizes: "Here are 3-5 things we're changing, here's why, and here's how we'll measure whether it worked." The output is a written brief — not a conversation. It goes into a strategy doc that the creative team references for the next production cycle. The discipline is: every recommendation has a data citation, a clear action, and a measurement plan. "Try more food content" is not a recommendation. "Increase food-category slides from 30% to 50% of body slides based on 2.1x higher save rate, measure over 8 posts" is.
