# Phase 1 — Triage

> **Superseded.** This document is retained as reference for the triage query logic and snapshot windows. The active procedure is [`capture-reading.md`](capture-reading.md), which unifies triage, collection, and ingestion with manifest-based batch tracking.

Queries the database, determines which posts need readings, and produces a pre-filled CSV for the collector plus a plain-text summary.

## Inputs

- `analytics/analytics.db` (current database state)

## Outputs

1. `procedures/capture-reading/pending-capture.csv` — one row per post needing a reading, metadata pre-filled, metric columns blank
2. `procedures/capture-reading/triage-summary.txt` — what needs to be collected, account checkpoint status
3. Console output (same content as triage-summary.txt)

## Procedure

### Step 1 — Run the triage script

```
python scripts/triage.py
```

The script queries the database, writes the CSV, and prints the summary. If no posts are due, the CSV is written with headers only and the summary reports nothing to capture.

### Step 2 — Proceed or stop

If the triage identified posts due, proceed to Phase 2 (`procedures/capture-reading/phase-2-collect.md`). If nothing is due, the procedure is complete.

---

## Script Reference: `scripts/triage.py`

The following documents what the script does internally. No action is required — this is context only.

### Query

Runs the triage query against the database. For each post published within the last 30 days, determines whether it needs a snapshot, velocity read, or nothing based on its age and existing readings. Also checks whether an account checkpoint is due (7+ days since last entry).

### Snapshot Windows

| Window | Hours since post | Rationale                                                                    |
| ------ | ---------------- | ---------------------------------------------------------------------------- |
| 48h    | 44–52            | First formal snapshot. Algorithm has made its initial distribution decision. |
| 7d     | 164–196          | Canonical performance reading. 90–95% of lifetime views have arrived.        |
| 30d    | 672–840          | Only if 7d snapshot views > 10K. Captures second-wave distribution.          |

### CSV Generation

Writes one row per triaged post. Pre-fills `post_id`, `slug`, `posted_date`, `hours_old`, and `type`. Leaves all 9 metric columns blank for the collector to fill.

Column structure:

```
post_id, slug, posted_date, hours_old, type, views, likes, comments, shares, bookmarks, new_followers, avg_watch_time_seconds, watched_full_percent, fyp_percent
```

### Summary

Prints the number of posts due, each post's slug with age and required columns, and account checkpoint status.
