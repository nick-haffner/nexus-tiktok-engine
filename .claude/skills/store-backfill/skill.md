---
name: store-backfill
description: "Backfill the store with all data from an existing TikTok account. Runs discover, capture content, derive data, and capture reading in sequence. Designed for long-running sessions with human breaks."
---

# Store Backfill

Populates the store with all available data from an existing TikTok account. Runs the four store procedures in sequence, with progress tracking via the database.

## Input

```
/store-backfill [debug]
```

**`debug`** — enables per-batch approval gates. Each batch prints a summary and waits for manager input before proceeding. The manager can:
- **Approve** — proceed to the next batch
- **Reject** — Claude re-examines the batch, diagnoses issues
- **Disable debug** — turn off approval gates for the remainder of the current procedure (gates re-enable when the next procedure starts)
- **Enable debug** — turn approval gates back on mid-procedure

Without `debug`, all batches proceed automatically. The procedure still prints batch summaries and stops on errors.

**Debug mode can be changed at any time** during the procedure. The manager can say "disable debug" after reviewing a few clean batches, or "enable debug" when entering a new procedure phase. The default for each procedure is whatever the initial flag was, but the manager overrides at will.

## Prerequisites

1. Chrome open with an authenticated TikTok Studio session.
2. Claude Code launched with `--chrome`.
3. Empty or partially populated database (idempotent — safe to re-run).

## Context Management

This procedure may run for 30-60+ minutes on a large account. To manage context:
- Each phase produces compact batch summaries. Do not accumulate verbose results.
- Between phases, summarize the completed phase in 2-3 sentences and discard batch-level detail.
- If context is approaching limits, the user can invoke `/cpm-pause` at any between-batch or between-phase checkpoint.
- The database holds all state. After `/cpm-resume`, re-run `/store-backfill` — it inspects the database and resumes from the first incomplete phase.

## Procedure

### Phase 1 — Discover Posts

Read and execute `tiktok_module/store/procedures/discover-posts/discover.md`.

1. Run `collect_post_ids.py` to get all post IDs from TikTok Studio.
2. Run `discover.py` with the resulting CSV to register all posts.
3. For each batch of 5: run `collect_post.py` for API enrichment, apply via `enrich_from_api`.
4. Approval gate per batch (debug mode) or auto-proceed (normal mode).
5. Report: "Phase 1 complete. X posts registered, Y enriched, Z already existed."

**Break between Phase 1 and Phase 2:** Yes — pause and report. Capture content requires a fresh session for image URL collection. The manager confirms the session is active before proceeding.

### Phase 2 — Capture Content

**Before starting Phase 2:** Read `tiktok_module/store/docs/tiktok-studio-extraction.md` — specifically the "Carousel slide image extraction" and "Chrome bridge workaround" sections. These document the proven methods for collecting image URLs through the Chrome extension, including the base64 chunking pattern and the `__extractChunk` helper function.

Read and execute `tiktok_module/store/procedures/capture-content/capture-content.md`.

1. Collect all carousel image URLs in one `/api/post/item_list/` pagination pass. Store on `window.__carouselUrls`.
2. Install `window.__extractChunk` for efficient per-carousel URL extraction.
3. For each carousel: extract URLs via base64 chunks (2 per JS call), download via Python urllib.
4. Approval gate per batch (debug mode) or auto-proceed (normal mode).
5. Report: "Phase 2 complete. X carousels downloaded (Y total slides). Z videos skipped."

**Break between Phase 2 and Phase 3:** Optional — derive data does not require Chrome. Can proceed immediately.

### Phase 3 — Derive Data

Read and execute `tiktok_module/store/procedures/derive-data/derive.md`.

1. Run `derive_data.py --triage-only` to count posts needing derivation.
2. For each batch of 5: transcribe, summarize, classify, extract topics. **Vision steps (transcribe + visual summary) must use Opus** (`model="opus"` on agents). See `VISION_MODEL` in `derive_data.py`.
3. Approval gate per batch (debug mode) or auto-proceed (normal mode).
4. Report: "Phase 3 complete. X derived. Y left NULL for manual review."

**Break between Phase 3 and Phase 4:** Optional — capture reading is independent. Can proceed immediately, but the manager may want to review the manual review list from Phase 3 first.

### Phase 4 — Capture Reading

Read and execute `tiktok_module/store/procedures/capture-reading/capture-reading.md`.

1. Run `triage.py` to identify posts due for readings.
2. For each batch of 5: collect metrics via `collect_post.py`, fill CSV, ingest.
3. Capture account checkpoint.
4. Approval gate per batch (debug mode) or auto-proceed (normal mode).
5. Report: "Phase 4 complete. X readings captured. Account: N followers."

### Completion

```
Store Backfill Complete.

  Posts registered: X (Y carousels, Z videos)
  Slides downloaded: N total across M carousels
  Derived data: P classified, Q left NULL for manual review
  Readings captured: R (S snapshot, T velocity)
  Account: U followers, V total likes

  Suggested manual review:
    [list of posts with NULL classifications]
```

## Break Recommendation

**Always break between Phase 1 and Phase 2.** Phase 1 (discover) is API-heavy and may exhaust the TikTok session. Phase 2 needs fresh signed URLs. Confirming session health before image downloads prevents wasted work.

**Phase 2 → 3 and Phase 3 → 4 can proceed without breaks** unless the context window is large or the manager wants to review Phase 3's manual review list before capturing readings.

## If Interrupted

Re-run `/store-backfill`. Each phase inspects the database:
- Phase 1: skips registered posts, enriches null fields only.
- Phase 2: skips posts with existing slides.
- Phase 3: skips posts with populated derived fields.
- Phase 4: triage surfaces only posts without readings.

No manual state management needed.

## Error Handling

On any unexpected error:
1. Stop the current batch.
2. Diagnose (session expired? rate limited? data issue?).
3. Report to the manager with the post that failed and why.
4. Do not continue. The database is consistent up to the last committed batch.
