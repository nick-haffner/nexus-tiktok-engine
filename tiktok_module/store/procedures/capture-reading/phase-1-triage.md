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

### Reading Cadence

Readings are taken daily, with frequency determined by post age. This replaces the previous narrow snapshot windows (48h/7d/30d), which were too tight to reliably hit on a once-daily cycle.

| Post age | Cadence | Type label | Rationale |
|----------|---------|------------|-----------|
| 0–3 days (0–72h) | Every 6h | `daily` | Algorithm is actively testing. Growth curve is steepest — captures acceleration, plateaus, and distribution pushes. |
| 3–7 days (72–168h) | Every 12h | `daily` | Distribution settling. Daily check-in sufficient to track trajectory. |
| 7–30 days (168–720h) | Every 7 days | `weekly` | Monitoring for second-wave distribution. Most posts have received 90–95% of lifetime views by day 7. |
| 30 days (720h) | Once | `mature` | Lifetime baseline capstone. Establishes final performance for comparison against earlier readings. |
| 30+ days | On-demand only | `reading` | Only collected when explicitly requested via `/store-update for`. |

A post's first reading is typically captured at 6–12h via `/store-update for` (targeted mode) immediately after publishing. The daily cycle then picks it up on its next run.

Posts registered after their active window (e.g., via backfill) receive a `backfill` reading on first triage. Posts older than 30 days that have never received a reading at or after the 720h mark are triaged as `mature`.

### CSV Generation

Writes one row per triaged post. Pre-fills `post_id`, `slug`, `posted_date`, `hours_old`, and `type`. Leaves all 9 metric columns blank for the collector to fill.

Column structure:

```
post_id, slug, posted_date, hours_old, type, views, likes, comments, shares, bookmarks, new_followers, avg_watch_time_seconds, watched_full_percent, fyp_percent
```

### Summary

Prints the number of posts due, each post's slug with age and required columns, and account checkpoint status.
