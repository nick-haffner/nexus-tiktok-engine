# Phase 3 — Ingest

> **Superseded.** This document is retained as reference for the ingestion and validation logic. The active procedure is [`capture-reading.md`](capture-reading.md), which uses `ingest.py` (manifest-driven) instead of `ingest_csv.py` (deleted).

Reads the filled CSV, validates, inserts readings into the database, handles account checkpoints, and cleans up.

## Inputs

- `procedures/capture-reading/pending-capture.csv` (from Phase 2, metric columns filled)
- `procedures/capture-reading/account-checkpoint.txt` (from Phase 2, if account checkpoint was due)
- `procedures/capture-reading/triage-summary.txt` (from Phase 1, cleaned up by this phase)

## Outputs

- Readings inserted into `analytics/analytics.db`
- Account checkpoint inserted if due
- Console report of results

## Procedure

### Step 1 — Run the ingestion script

```
python scripts/ingest_csv.py
```

The script handles all validation, insertion, account checkpoint ingestion, reporting, and cleanup. If the script exits with code 0, Phase 3 is complete. If it exits with a non-zero code, report the error output to the manager.

---

## Script Reference: `scripts/ingest_csv.py`

The following documents what the script does internally. No action is required — this is context only.

### Read CSV

Parses `procedures/capture-reading/pending-capture.csv`. Each row represents one reading to insert.

### Validate

For each row:
- Confirms `post_id` exists in the `posts` table. Rejects and reports if not found.
- Confirms no duplicate reading exists for this `post_id` at the computed `captured_at` timestamp. Skips and reports if duplicate.
- Checks views are non-decreasing compared to the most recent reading for this post. Warns but still inserts if violated.
- If `type` is `snapshot`, confirms all 9 metric columns are populated. Warns if any are missing.

### Insert Readings

For each validated row, inserts into the `readings` table. Uses the current datetime as `captured_at`. Computes `hours_since_post` from `posted_date` to now. Blank metric columns are inserted as NULL.

### Account Checkpoint

Queries the `account` table. If 7+ days since the last entry (or no entries exist), reads `procedures/capture-reading/account-checkpoint.txt` (two lines: follower count, total likes). Inserts into the `account` table and deletes the file. If the file is missing and a checkpoint is due, warns. If not due, skips silently.

### Report

Prints a summary: rows ingested (velocity and snapshot counts), warnings, errors, account checkpoint status.

### Clean Up

Deletes `procedures/capture-reading/pending-capture.csv` and `procedures/capture-reading/triage-summary.txt`.
