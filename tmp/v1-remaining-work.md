# V1 Remaining Work

Generated 2026-04-03. Unified tracker for all remaining work across engine functions.

---

## Store

### Completed
- [x] Database v3 schema (6 tables, universal/company-specific separation)
- [x] Discover posts procedure + scripts (collect_post_ids, discover, collect_post enrichment)
- [x] Capture reading procedure + scripts (triage, collect_post, collect_account, ingest, manifest system)
- [x] Capture content procedure + scripts (capture_content, collect_content)
- [x] Derive data procedure + scripts (derive_data with 6 unit functions)
- [x] Idempotency across all permanent data writes
- [x] Error handling with break-and-diagnose pattern
- [x] Batch chunking with debug-mode approval gates
- [x] `/store-backfill` skill (E2E tested, in progress)
- [x] `/store-update` and `/store-repair` skill stubs
- [x] Documentation: schema, design rationale, extraction methods, known issues, ANALYSIS-PROCESS.md

### Remaining
- [ ] Remove velocity/snapshot reading classification (after backfill completes)
- [ ] Implement `/store-update` skill content (daily cycle: discover → capture content → derive → capture reading)
- [ ] Add on-demand read mode to `/store-update` (accept post_id argument)
- [ ] Implement `/store-repair` skill content (integrity checks, orphan detection, gap reporting)
- [ ] Complete backfill E2E test and resolve any issues discovered
- [ ] Write store autonomous instructions (for engine handbook)

## Analyze

### Completed
- [x] Level 1 — Performance Reporting (script, procedure, insight brief)
- [x] Level 2 — Content Strategy Analysis (script, procedure, insight brief with Phase 2 outlier investigation)
- [x] Level 3 — Audience & Growth Analysis (script, procedure, insight brief with targeted content access)
- [x] Level 4 — Cadence & Timing Optimization (script, procedure, insight brief)
- [x] Level 5 — Conversion Funnel Analysis (script, procedure, insight brief with full content access)
- [x] Shared query infrastructure (shared.py)
- [x] ANALYSIS-PROCESS.md (authoritative decisions, gap taxonomy, run modes, content access rules)
- [x] Market research hydration in insight briefs
- [x] Debug-mode approval gates (aligned across all levels)

### Remaining
- [ ] Synthesis phase — write idealized spec, procedure, implement
  - [ ] Four functions: coherence check, synthesis, contradiction scan, codification
  - [ ] Priority hierarchy for resolving contradictions
  - [ ] Strategy diffs as proposals (not automatic writes)
  - [ ] Fixed number of strategy surface area items with implement/test/watch/discard classification
  - [ ] Codification procedure (separate from synthesis — writes approved changes to strategy files)
- [ ] Manager checkpoint integration (where in L1-5 → synthesis chain the manager participates)
- [ ] Update analyze scripts for v3 schema changes (nexus_post_metadata now 5 columns, carousel_details has content fields)
- [ ] Re-run analysis after backfill completes (fresh data)
- [ ] Write analyze autonomous instructions (for engine handbook)

## Integrate (function — planned)

Connects analysis outputs to strategy updates to generation instructions. Closes the feedback loop.

### Completed
- [x] Strategy files exist (brand-voice.md, frameworks.md, performance-insights.md, content-pipeline.md)
- [x] Frameworks.md updated with visual signatures for classification
- [x] Strategy files consumed by generate procedure (Phase 0 ideation reads frameworks, pipeline, insights)

### Remaining
- [ ] Define strategy file schemas (sections, update rules, history tracking)
- [ ] Define how frameworks.md accepts performance annotations from synthesis
- [ ] Define how content-pipeline.md accepts planned posts from synthesis
- [ ] Determine if brand-voice.md needs a writable section or stays manually curated
- [ ] Design strategy iteration procedure (synthesis output → strategy file updates → generate procedure changes)
- [ ] Full cycle test: store → analyze → synthesis → strategy update → generate reads updated files
- [ ] Confirm the feedback loop closes end-to-end
- [ ] Write integrate autonomous instructions (for engine handbook)

## Generate (function)

### Completed
- [x] Produce-carousel procedure (Phase 0-4)
- [x] `/produce-carousel` skill
- [x] Brand rules (rendering specs)
- [x] Brand assets and product context (at repo root)

### Remaining
- [ ] Update produce-carousel to consume performance-insights.md and annotated frameworks.md
- [ ] Update Phase 0 ideation to reference content-pipeline.md for planned concepts
- [ ] Verify generate reads from correct strategy file paths (post-restructure)
- [ ] Design content cadence based on strategy outputs (how often to post, what framework/city to use)
- [ ] Write generate autonomous instructions (for engine handbook)

## Handbooks & Instructions

### Completed
- [x] Engine handbook structure (handbook.md: Getting Started, Autonomous Mode, Tools, AI Agents)
- [x] Store autonomous instructions (store/AUTONOMOUS.md)
- [x] Store tools section in handbook

### Remaining
- [ ] Write analyze autonomous instructions
- [ ] Write integrate autonomous instructions
- [ ] Write generate autonomous instructions
- [ ] Rewrite AI Agents section after all functions are complete
- [ ] Resolve any infra-run idempotency issues in analyze (multiple readings per post)
