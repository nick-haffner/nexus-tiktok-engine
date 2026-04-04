# Capture Content — Slide Image Download

Downloads carousel slide images from TikTok to the filesystem. Raw content acquisition only — no text extraction, no classification, no derivation.

## Scope

This procedure gets the raw visual content onto the filesystem. The derive data procedure reads it later to extract text, classify CTA, generate visual summaries, etc.

- Downloads carousel slide images via TikTok API
- Stores in `store/data/posts/{slug}/slides/Slide N.{ext}`
- No database writes (filesystem is the output)
- Videos are listed in triage output but not processed in v1

## Prerequisites

1. Posts registered in DB with `content_type` and `slug` populated (discover posts completed).
2. Chrome with authenticated TikTok session (for API image downloads — signed URLs require active session).

## Error Handling

Same break-and-diagnose pattern as other store procedures. Stop on unexpected errors. Specific to this procedure:

- **Image URL expired:** Stop batch, report. Re-run to get fresh URLs.
- **Partial download:** Files are left in place. Next run checks slide count against existing files.
- **No slug:** Post is listed in triage as "cannot download." Slug must be assigned (via discover enrichment or manually) before content can be captured.

## Procedure

### Step 1 — Triage

```
python store/scripts/capture_content.py --triage-only
```

Scans all posts. For each carousel, checks if `store/data/posts/{slug}/slides/` exists and has files. Reports:

- Carousels needing content (missing or empty slides directory)
- Carousels with content (already downloaded)
- Videos (skipped — listed for visibility)
- Carousels without slug (cannot download)

If zero carousels need content, the procedure is complete.

### Step 2 — Download (Batch by Batch)

```
python store/scripts/capture_content.py
```

Processes carousels in batches of 5. For each carousel in the batch:

1. Create `store/data/posts/{slug}/slides/` if it doesn't exist.
2. Call the content retrieval unit process with the post_id.
3. Download each slide image to `Slide 1.{ext}`, `Slide 2.{ext}`, etc.
4. Verify downloaded count.

After each batch, print a summary:

```
--- Batch 1 Complete (5/5 carousels) ---
  seattle-2025-12-26       10 slides downloaded
  phoenix-2025-12-09       6 slides downloaded
  ...
```

**Approval gate (debug mode only):** In debug mode, wait for manager approval before proceeding. Manager can approve, reject, or disable debug mode for the remainder of this procedure. In normal mode, proceed automatically.

### Step 3 — Report

```
Capture Content complete.
  Carousels downloaded: X (Y total slides)
  Carousels already had content: Z
  Videos skipped: W
```

## Idempotency

- Skip download if `slides/` directory already has files.
- Re-running processes only carousels with empty or missing slides directories.
- Safe to run repeatedly.

## Without Chrome

Cannot run without Chrome. Image URLs require an authenticated TikTok session. If Chrome is unavailable, slide images must be downloaded manually from TikTok.

## Scripts

| Script | Purpose | Status |
|---|---|---|
| `store/scripts/capture_content.py` | Triage (filesystem scan) + batch orchestration | Implemented (triage works; download placeholder pending unit process) |
| Content retrieval unit process | Fetch image URLs from API, download images | Pending — under investigation by terminal instance |

## Downstream

After capture content completes, the derive data procedure can:
- Read slide images to generate visual summaries
- Transcribe slide text from images (for posts without copy.md)
- Classify CTA from the final slide
