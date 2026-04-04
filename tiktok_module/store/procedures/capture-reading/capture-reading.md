# Analytics Capture Procedure

Unified procedure for triaging, collecting, and ingesting TikTok analytics. Runs triage, collects metrics batch-by-batch with manager approval gates, and ingests into the database — all in one execution.

## Prerequisites

Before starting, verify:

1. **Chrome** is open with an authenticated TikTok Studio session (`www.tiktok.com/tiktokstudio`). If not authenticated, log in before proceeding.
2. **Claude Code** was launched with `--chrome` flag (if running via Claude-in-Chrome).
3. **Chrome extension** is connected and responding (if running via Claude-in-Chrome).

**Verification step:** At the start of execution, attempt a single API call against any known post_id to confirm the TikTok Studio session is active. If it fails with an auth error, stop and report: "TikTok Studio session is not authenticated. Log in at www.tiktok.com/tiktokstudio and restart."

## Error Handling

This procedure stops on any unexpected error. When an error occurs:

1. **Identify the error.** Read the error message, traceback, or unexpected output.
2. **Diagnose the cause.** Determine whether it is:
   - A **prerequisite failure** (session expired, Chrome not connected, DB not found)
   - A **data issue** (post deleted, malformed response, unexpected metric format)
   - A **script bug** (crash, unhandled edge case)
3. **Report to the manager.** State what failed, the diagnosis, and whether the error is recoverable (retry) or blocking (requires investigation).
4. **Do not continue past the error.** Partial data is acceptable (the manifest tracks progress). Corrupted data is not.

## Procedure

### Step 1 — Triage

Run the triage script:

```
python store/scripts/triage.py
```

This queries the database, determines which posts need readings, and produces:
- `store/procedures/capture-reading/manifest.json` — tracks batch state
- `store/procedures/capture-reading/pending-capture.csv` — human-readable metric collection sheet

Review the console output. It reports:
- How many posts are due and their batch assignments
- Whether an account checkpoint is due
- Which posts need readings and their triage window type (velocity or snapshot)

If zero posts are due and no account checkpoint is due, the procedure is complete. Stop here.

**Error: "Existing manifest found."** A previous capture cycle was not completed. Either:
- Resume the previous cycle (see Resume Handling below)
- Delete the manifest and CSV to start fresh: `rm store/procedures/capture-reading/manifest.json store/procedures/capture-reading/pending-capture.csv`

### Step 2 — Verify Session

Before collecting any metrics, verify the TikTok Studio session by running `collect_post` for the first post in the manifest:

```
python store/scripts/collect_post.py <first_post_id>
```

Execute the generated JavaScript on a TikTok Studio page. If the response contains metric data, the session is valid. If it returns an auth error or empty response, stop and report the prerequisite failure.

### Step 3 — Collect Metrics (Batch by Batch)

For each batch in the manifest:

**3a. Collect each post in the batch.**

For each post in the current batch, run `collect_post`:

```
python store/scripts/collect_post.py <post_id> --reading-type <snapshot|velocity>
```

Execute the generated JavaScript on TikTok Studio. Parse the result:

```
python store/scripts/collect_post.py <post_id> --reading-type <type> --parse '<json_result>'
```

Write the parsed metrics to the corresponding row in `pending-capture.csv`. The CSV columns are:

```
batch, post_id, slug, posted_date, hours_old, type,
views, likes, comments, shares, bookmarks,
new_followers, avg_watch_time_seconds, watched_full_percent,
fyp_percent, profile_visits,
search_percent, profile_percent, following_percent, other_percent
```

All readings capture all metrics regardless of type. The API returns all fields in a single call — the velocity/snapshot distinction controls *when* to capture (triage windows), not *what* to capture.

**3b. Validate the batch.**

After collecting all posts in the batch, review the metrics:
- Are view counts reasonable (non-zero for posts older than a few hours)?
- Are all metric columns populated?
- Do any values look anomalous (e.g., views lower than a previous reading)?

**3c. Present batch summary.**

Print a summary of the batch to the manager:

```
--- Batch N Complete (X/X posts) ---
  slug-1          snapshot  views=XXXXX  eng=X.X%  save=X.X%
  slug-2          velocity  views=XXXXX
  ...
```

**3d. Approval gate (debug mode only).**

In debug mode: wait for manager approval before ingesting and proceeding. Manager can approve, reject (re-collect specific posts), or disable debug mode for the remainder of this procedure.

In normal mode: proceed to ingest automatically after printing the summary.

**3e. Ingest the batch.**

```
python store/scripts/ingest.py --batch N
```

Review the ingestion report. If warnings or errors appear, diagnose and report to the manager before continuing.

### Step 4 — Account Checkpoint (if due)

If the manifest indicates an account checkpoint is due:

1. Run `collect_account`:

```
python store/scripts/collect_account.py
```

2. Navigate to TikTok Studio overview. Read the follower count and total likes.

3. Parse the result:

```
python store/scripts/collect_account.py --parse '{"followers": NNN, "total_likes": NNN}'
```

4. Update the manifest with the account data. The ingest script will write it to the database on the next ingest run, or run:

```
python store/scripts/ingest.py --all
```

### Step 5 — Verify Completion

After all batches are ingested and the account checkpoint (if due) is captured:

- The manifest and CSV should be automatically cleaned up by the ingest script.
- If they remain, verify that all batches show status "ingested" in the manifest.
- Report the total number of readings ingested and any warnings.

```
Capture complete. X readings ingested (Y snapshot, Z velocity). No errors.
```

---

## Resume Handling

If the procedure was interrupted (Chrome crash, session timeout, manual stop):

1. Check for an existing manifest: `store/procedures/capture-reading/manifest.json`
2. Read the manifest to determine the state:
   - Which batches are pending, collected, or ingested?
   - Is the account checkpoint captured?
3. Resume from the first incomplete step:
   - If a batch has unfilled CSV rows, resume collection for those posts.
   - If a batch has filled CSV rows but status is not "ingested", run ingest for that batch.
   - If all batches are ingested but account checkpoint is not captured, resume at Step 4.

The manifest is the single source of truth for procedure state. The CSV is the data artifact. Both must be consistent.

---

## Without Chrome (Manual Collection)

If Chrome access is unavailable:

1. Run triage (Step 1) — works without Chrome.
2. **Skip Step 2** (session verification).
3. Collect metrics manually:
   - Open TikTok Studio in a browser.
   - For each post in the CSV, navigate to its analytics page.
   - Read the metrics and fill them into the CSV by hand.
   - Fill all metric columns for every reading.
4. Run ingest (Step 3e) — works without Chrome.

The CSV is designed to be human-fillable for exactly this scenario.

---

## Scripts Reference

| Script | Purpose | Requires Chrome |
|---|---|---|
| `store/scripts/triage.py` | Query DB, produce manifest + CSV | No |
| `store/scripts/collect_post.py` | Generate JS for one post's metrics, parse result | Yes (JS execution) |
| `store/scripts/collect_account.py` | Format account checkpoint data | Yes (page navigation) |
| `store/scripts/ingest.py` | Read CSV, validate, insert into DB | No |
