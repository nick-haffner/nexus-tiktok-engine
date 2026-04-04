# Session Context: ttm-engine-build-01

## Session Summary

Massive multi-day session building the TikTok Module (TTM) engine from the ground up. Built all four engine functions (store, analyze, generate, integrate) with store being fully complete and analyze partially complete.

## Current State

### Store Function — COMPLETE
- All 4 store procedures implemented and E2E tested: discover-posts, capture-content, derive-data, capture-reading
- Database v3 schema (6 tables: posts, nexus_post_metadata, carousel_details, video_details, readings, account)
- All unit processes built and tested: collect_post_ids, collect_post, collect_account, collect_content, derive units (6 classifiers + city extraction)
- Skills: `/store-backfill` (tested), `/store-update` (daily + targeted "for" mode), `/store-repair` (audit + targeted fix)
- Autonomous instructions written: `store/AUTONOMOUS.md`
- Backfill E2E completed by terminal instance: 43 posts, 24 carousels with slides, 43 readings, 1 account checkpoint
- Reading classification removed (velocity/snapshot replaced with window labels: 48h, 7d, 30d, backfill, early, reading)
- City extraction implemented with weighted multi-source scoring
- Slug format: YYYY-MM-DD-descriptor with duplicate handling
- Description/hashtags collected via collect_post API enrichment (not item_list — Chrome bridge truncation issue)

### Analyze Function — PARTIALLY COMPLETE
- Levels 1-5 implemented with scripts, procedures, insight briefs
- Shared query infrastructure (shared.py)
- ANALYSIS-PROCESS.md with authoritative decisions (gap taxonomy, run modes, content access rules, insight brief standards)
- Market research hydration, debug-mode approval gates
- **NOT DONE:** Synthesis phase (the bridge between analysis and strategy), manager checkpoint integration, re-running analysis against fresh backfill data

### Integrate Function — NOT STARTED
- Strategy files exist but no iteration procedure
- No strategy file schemas defined
- No feedback loop closure

### Generate Function — PARTIALLY COMPLETE
- Produce-carousel procedure exists but doesn't consume strategy outputs
- Needs update to read from performance-insights.md and annotated frameworks.md

### Handbook — IN PROGRESS
- Structure defined: Getting Started, Autonomous Mode, Tools, AI Agents
- Store sections complete (autonomous pointer, tools table, AI agent examples)
- Tools table uses user-facing format: "What you want | Tell Claude | Technical components"
- AI Agents section drafted with cross-function examples
- **PENDING:** Analyze, integrate, generate sections not yet written
- **PENDING:** Tools table proposed but NOT YET APPROVED for implementation — only store section is implemented. The tools table was implemented prematurely and user corrected this pattern.

## Key Design Decisions Made This Session

All stored in `tmp/v1-vision.md` Key Decisions section and in `analyze/ANALYSIS-PROCESS.md`:

- Engine has 4 functions: Store, Analyze, Generate, Integrate (each in own directory)
- Two-file instruction model: handbook (coordinator) + per-function AUTONOMOUS.md (stable instructions)
- Store-repair is provider/developer tool, not autonomous mode
- Velocity readings captured post-publication per marketing best practice
- Permission approval guidance in user instructions
- Instructions not information — users follow steps, not read docs
- Debug mode for oversight (approval gates off by default)
- Analysis levels 1-5 are analytical; synthesis is deliberative (different operation type)
- Strategy blindness in L1-L5; strategy enters at synthesis only
- Insight briefs end with Cross-Level Questions + Questions Requiring Human Assessment (tagged structural/addressable)
- Data classified as permanent (captured + derived) vs transient
- Idempotency: permanent data insert-or-fill-nulls, transient data insert-always
- All timestamps UTC with +00:00 offset

## Critical User Behavioral Preferences

- **NEVER implement before proposal is approved.** User repeatedly corrected this. Always propose first, wait for explicit approval, then implement.
- **Proposals should be surfaced as text output, not written to files.** The user reviews proposals in the conversation, not in file diffs.
- **Store authoritative decisions in tmp documentation.** Novel design decisions get stored in v1-vision.md or v1-remaining-work.md.
- When user says "repropose" — provide the full revised proposal, don't just describe changes.

## Key Reference Files

- `tmp/v1-vision.md` — End state, use cases, function table, key decisions
- `tmp/v1-remaining-work.md` — Unified remaining work tracker across all functions
- `tmp/idealized_ttm_design/` — Idealized specs for all 5 analysis levels, ideal dataset spec
- `tiktok_module/handbook.md` — Engine handbook (Getting Started, Autonomous Mode, Tools, AI Agents)
- `tiktok_module/store/AUTONOMOUS.md` — Store autonomous instructions for users
- `tiktok_module/analyze/ANALYSIS-PROCESS.md` — Authoritative analysis decisions
- `tiktok_module/store/docs/analytics-schema.md` — Database v3 schema
- `tiktok_module/store/docs/analytics-design-rationale.md` — All schema design decisions
- `tiktok_module/store/docs/tiktok-studio-extraction.md` — Browser extraction methods and workarounds
- `tmp/schema-v3-overview.md` — Visual schema diagram

## Next Actions

1. **Immediate:** Continue building the handbook — analyze, integrate, generate sections still needed, but blocked on those functions being incomplete
2. **Next workstream:** Analyze function — re-run analysis against fresh backfill data, then design and implement the synthesis phase
3. **After synthesis:** Integrate function — connect synthesis outputs to strategy file updates to generate procedure changes
4. **After integrate:** Generate function updates — consume strategy outputs, design content cadence
5. **Final:** Full cycle E2E test (store → analyze → synthesis → strategy → generate)
