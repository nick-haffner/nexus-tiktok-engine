# Analysis Process — Authoritative Decisions

This document records the binding design decisions for the analyze function. All procedures, scripts, and insight briefs must adhere to these decisions. Changes require explicit manager approval.

---

## Core Architecture

The analyze function consists of two phases:

1. **Analytical phase (Levels 1-5):** Each level examines data through a specific lens and produces findings. Levels are data-driven. They report what the data says, including what it cannot say. They do not make strategic recommendations.

2. **Synthesis phase:** A distinct operation that consumes analytical outputs and produces strategic recommendations. This is deliberative, not analytical. It reads findings, weighs them against each other and against the full context (including strategy and market research), and proposes decisions for manager approval.

The analytical phase is the analyst's presentation. The synthesis phase is the account lead closing the meeting. These are structurally different operations and should not be treated as peers.

---

## Run Modes

The procedure supports two run modes. Both produce the same output structure. The difference is whether gaps are resolved or accepted.

**With human review:** The procedure pauses at each level's insight brief. The manager reads the analysis, reviews the "Questions Requiring Human Assessment" section, and provides answers. These answers are incorporated into the level's output before proceeding. The synthesis phase receives enriched outputs.

**Without human review:** The procedure runs to completion. Gaps are surfaced at each level but not resolved. The "Questions Requiring Human Assessment" section is included in the output as unanswered. The synthesis phase adjusts confidence on any recommendation that depends on an unresolved gap, and notes which recommendations would benefit from human input.

Neither mode is degraded. Both produce well-defined, honest output. The first is more complete; the second is faster and still actionable.

---

## Analytical Approach

The engine performs structured qualitative analysis where it can and explicitly outsources creative judgment where it can't. Each insight brief ends with specific, informed questions for the manager — not generic "what do you think?" prompts, but precise questions that name what the engine found, what it couldn't resolve, and what human judgment is needed for.

The engine's role is **best-practice marketer preparation**: it does everything a marketer would do before the meeting and presents meeting-ready analysis with the agenda items requiring human judgment clearly marked. The manager completes the last 20% that requires taste, audience intuition, and strategic context.

This means:
- The engine provides partially completed analysis with precise questions, not raw data with open-ended prompts.
- Questions in the "Requiring Human Assessment" section must be informed by the analysis — they name specific posts, specific patterns, and specific creative dimensions.
- Recommendations from the synthesis phase are flagged as "data-supported" or "requires manager confirmation on creative assessment."

---

## Data Access Rules by Level

### Data Reports and JSON Outputs (All Levels)
- **Database only.** Deterministic, reproducible. No content artifacts, no market research, no strategy.

### Insight Briefs

| Level | Database | Market Research | Post Content | Strategy |
|---|---|---|---|---|
| L1 Performance | Yes | Yes (benchmarks) | No | No |
| L2 Content Strategy | Yes | Yes (benchmarks) | Yes (targeted — outlier posts only) | No |
| L3 Audience & Growth | Yes | Yes (growth benchmarks) | Yes (targeted — flagged posts only) | No |
| L4 Cadence & Timing | Yes | Minimal (cadence norms) | No | No |
| L5 Conversion Funnel | Yes | Yes (caption/hashtag benchmarks) | Yes (full — captions and CTAs for all posts) | No |
| Synthesis | Yes | Yes (all) | Yes (all) | Yes (all) |

### Content Access Rules
- **Targeted access (L2, L3):** Content is read only for posts identified as outliers or anomalies by the data analysis. The data determines which posts to investigate. Content explains why findings exist — it does not define the dimensions of analysis.
- **Full access (L5):** Level 5's stated goal is to evaluate caption and CTA effectiveness. Not reading the content would be incomplete analysis. All captions (description field + caption.md where available) and copy.md are accessible.
- **No access (L1, L4):** These levels answer numerical and temporal questions where content has no bearing.

### Strategy Blindness
Levels 1-5 do not read strategy files. This is deliberate. The analytical phase must be capable of producing findings that contradict current strategy. If strategy is present during analysis, there is gravitational pull toward confirming existing decisions. Strategy enters at the synthesis phase, where it is a named input that can be examined and challenged — not an ambient bias.

---

## Market Research Hydration

Market research files (`store/data/market-research/`) provide external context that calibrates findings without biasing them. They answer "is this number good?" not "does this align with our strategy?"

Usage rules:
- Cite specific benchmarks with source (e.g., "3% engagement is typical for travel carousels per carousel-visual-style.md").
- Do not use market research to filter or suppress findings.
- If a finding contradicts market research guidance, surface the contradiction — don't resolve it.

---

## Metadata as Analytical Lens

The metadata schema defines the dimensions through which we analyze posts. This is a deliberate choice, not a natural truth. Risks and mitigations:

1. **Every analysis level reports which dimensions it analyzed and which it couldn't.** The data coverage section is standard across all levels.
2. **The metadata schema is documented as a deliberate choice.** See `tmp/idealized_ttm_design/ideal-dataset-spec.md`. Additions should be evaluated for analytical value.
3. **Insight briefs must name what they can't see.** If a finding is based on 7 of 45 posts, say so. If a dimension has 0% coverage, say what questions remain unanswerable.
4. **The synthesis phase explicitly asks: "What might we be missing because of how we categorize?"** This is a standing item, not an occasional check.

---

## Gap Taxonomy

All gaps are classified into two categories:

**Structural gaps** — cannot be resolved by process or data changes within the engine. They require external capabilities the engine cannot replicate. These are accepted by the procedure and permanently surfaced.

**Addressable gaps** — can be resolved by data collection changes, metadata backfill, content artifact capture, or process improvements. These are surfaced with a resolution path so the reviewer knows that fixing them is feasible.

### Structural Gaps

| Gap | Affects | Description |
|---|---|---|
| **Creative judgment** | L2, L3, L5, Synthesis | Assessing whether a hook "feels" compelling, whether a caption reads as authentic vs. forced, whether a visual has energy. The engine performs structured analysis (classify hook type, compare CTA phrasing) and surfaces precise questions for human judgment. |

### Addressable Gaps

| Gap | Affects | Resolution Path |
|---|---|---|
| **Competitive context** | L1, L2, Synthesis | Add competitor tracking via manual research, third-party tools, or periodic competitive audits. |
| **Classification metadata** | L2, L3 | Run derive procedure to classify framework and slide_layout. 38/45 posts lack framework, 41 lack slide_layout. |
| **Carousel content** | L2, L3, L5 | Run capture content procedure to download slides and extract text. Then derive procedure to populate visual_summary, has_cta, cta_type, cta_text. |
| **posted_time** | L4 | Run discover enrichment (collect_post extracts from API create_time). Needs enrichment run against TikTok. |
| **Follower attribution** | L3 | Capture fresh readings via capture reading procedure. Backfilled snapshots may not capture historical follower data. |
| **Profile visits** | L5 | Page-level metric, not in collect_post API. Requires page navigation or different API endpoint. |
| **CTA classification** | L5 | Run derive procedure to classify from slide text/copy.md. Currently keyword-matched from description in L5 analysis. |
| **sound_name / sound_type** | L2 | sound_name: run discover enrichment. sound_type: requires manual classification (no automated source). |

### Gap Surfacing Standard

Gaps are surfaced in two places per level, without redundancy:

**Data Coverage section (data report, all levels):** Reports addressable data gaps — field coverage, stubbed columns, resolution paths. This is the "what data is missing" section. Produced by the Python script.

**Insight brief (analytical and human assessment questions):** Reports the analytical impact of gaps — what questions couldn't be answered, what findings are limited by missing data, and what human judgment is needed for structural gaps. This is the "what analysis is incomplete" section. Produced by Claude.

The data report surfaces the gap existence. The insight brief surfaces the gap impact. No overlap — one says "framework is 16% populated," the other says "framework comparison has low confidence because 84% of posts are unclassified."

---

## Output Artifact Standard

Every analytical level produces three artifacts:

| Artifact | Producer | Purpose |
|---|---|---|
| Structured data (JSON) | Python script | Canonical data for downstream consumption and future dashboards |
| Data report (Markdown) | Python script | Human-readable tables and flags |
| Insight brief (Markdown) | Claude analysis | Natural language interpretation with market research calibration, targeted content investigation (where permitted), and explicit human assessment questions |

The synthesis phase produces:
- Synthesis report (recommendations with data citations)
- Strategy diffs (proposed changes to strategy files, requiring approval)
- Synthesis insight brief (overall strategic direction, biggest bets, biggest risks, open questions)

---

## Insight Brief Standards

All insight briefs must:
- Be 300-500 words (excluding the question sections).
- Lead with the highest-leverage finding.
- Cite specific numbers, not generalizations.
- Respect confidence levels — do not overstate findings from small samples.
- Name confounds rather than claiming causation.

All insight briefs end with two distinct sections:

**Cross-Level Analytical Questions:** Directed at other analytical levels or the synthesis phase. Investigative prompts the engine can answer. Consumed internally.

**Questions Requiring Human Assessment:** Directed at the manager. Each question is tagged:
- `[structural]` — requires human creative judgment or external context that the engine cannot provide. Permanent until the gap type changes.
- `[addressable]` — could be resolved by a specific data or process change. The manager may answer now or note that fixing the underlying issue would eliminate the question.
