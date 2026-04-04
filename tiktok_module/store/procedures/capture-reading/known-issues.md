# Known Issues — Analytics Capture

## Duplicate readings on manifest loss

If the manifest is deleted or corrupted after collection but before ingestion, re-running triage + collect + ingest would create new readings at new timestamps for the same posts. The readings table uses `(post_id, captured_at)` as the primary key, so two readings of the same post at different times both insert successfully. This produces duplicate observations of the same snapshot window.

**Mitigation:** The manifest guards against this in normal operation — triage refuses to overwrite an in-progress manifest (exit code 2). Duplicate readings only occur if the manifest is manually deleted. If this happens, the extra readings are analytically harmless (each is a valid point-in-time measurement) but inflate the reading count.

**Prevention:** Do not delete the manifest during an active capture cycle. If the manifest is corrupted, inspect the CSV to determine which batches were already ingested before re-triaging.

## Caption and hashtag mutability

The `description` and `hashtags` fields in the `posts` table are populated once during discovery and never re-fetched. If a user edits their TikTok caption after posting, the database retains the original version. This is accepted — caption edits are rare. If this becomes a concern, the discover procedure can be modified to refresh these fields on re-run, but this would require changing the current "never overwrite non-null" idempotency rule for these specific columns.

## Pre-v2 timestamp format

Readings captured before the v2 migration (2026-04-01) store `captured_at` without a UTC offset suffix (e.g., `2026-04-01T07:16:04`). Post-v2 readings include `+00:00` (e.g., `2026-04-03T18:27:51+00:00`). Both are UTC. Both sort correctly as ISO 8601 strings. Analysis scripts handle both formats. No action required unless strict timezone parsing is introduced.

## Backfill snapshot timing

Posts caught by the backfill branch of triage (older than 52 hours, zero readings) receive their snapshot at whatever age they happen to be when triage runs. A "48h snapshot" taken at 200 hours is less precisely timed than one taken at 48 hours, but the metrics are still valid. The `hours_since_post` field records the actual age at capture, so analysis can distinguish precisely-timed from late-captured snapshots.
