# Phase 2 — Collect

> **Superseded.** This document is retained as reference for the collection workflow. The active procedure is [`capture-reading.md`](capture-reading.md), which unifies triage, collection, and ingestion with manifest-based batch tracking and unit processes (`collect_post.py`, `collect_account.py`).

Data collection from TikTok Studio. Read metrics and write them to `pending-capture.csv`.

## Inputs

- `procedures/capture-reading/pending-capture.csv` (from Phase 1, metadata pre-filled, metrics blank)
- `procedures/capture-reading/triage-summary.txt` (from Phase 1, indicates account checkpoint status)

## Outputs

- `procedures/capture-reading/pending-capture.csv` (same file, metric columns filled)
- `procedures/capture-reading/account-checkpoint.txt` (if account checkpoint is due)

## Procedure

### Step 1 — Access TikTok Studio

Access the TikTok Studio Content tab at `www.tiktok.com/tiktokstudio/content`. Authenticate if prompted.

### Step 2 — Collect metrics

For each row in `pending-capture.csv`: collect all metrics for the post via the API (`collect_post.py`) or by navigating to the post's analytics page. All readings capture all metrics regardless of cadence tier — the `type` field (`daily`, `weekly`, `backfill`, `reading`) records *when* the reading was triggered, not *what* to collect. Write all metric values to the corresponding columns in `pending-capture.csv`.

### Step 4 — Account Checkpoint

If `procedures/capture-reading/triage-summary.txt` indicates an account checkpoint is due, read the current follower count and total likes from TikTok Studio's overview. Write them to `procedures/capture-reading/account-checkpoint.txt` as two lines:

```
480
13200
```

Line 1: follower count. Line 2: total likes. The Phase 3 ingestion script reads this file automatically.

### Step 5 — Proceed to Phase 3

Proceed to Phase 3 (`procedures/capture-reading/phase-3-ingest.md`).
