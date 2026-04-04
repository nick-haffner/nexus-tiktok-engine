# Known Issues — Analytics Capture

## Duplicate readings on manifest loss

If the manifest is deleted or corrupted after collection but before ingestion, re-running triage + collect + ingest would create new readings at new timestamps for the same posts. The readings table uses `(post_id, captured_at)` as the primary key, so two readings of the same post at different times both insert successfully. This produces duplicate observations of the same snapshot window.

**Mitigation:** The manifest guards against this in normal operation — triage refuses to overwrite an in-progress manifest (exit code 2). Duplicate readings only occur if the manifest is manually deleted. If this happens, the extra readings are analytically harmless (each is a valid point-in-time measurement) but inflate the reading count.

**Prevention:** Do not delete the manifest during an active capture cycle. If the manifest is corrupted, inspect the CSV to determine which batches were already ingested before re-triaging.

## Caption and hashtag mutability

The `description` and `hashtags` fields in the `posts` table are populated once during discovery and never re-fetched. If a user edits their TikTok caption after posting, the database retains the original version. This is accepted — caption edits are rare. If this becomes a concern, the discover procedure can be modified to refresh these fields on re-run, but this would require changing the current "never overwrite non-null" idempotency rule for these specific columns.

## Pre-v2 timestamp format

Readings captured before the v2 migration (2026-04-01) store `captured_at` without a UTC offset suffix (e.g., `2026-04-01T07:16:04`). Post-v2 readings include `+00:00` (e.g., `2026-04-03T18:27:51+00:00`). Both are UTC. Both sort correctly as ISO 8601 strings. Analysis scripts handle both formats. No action required unless strict timezone parsing is introduced.

## Backfill reading timing

Posts caught by the backfill branch of triage (any age, zero readings) receive their first reading at whatever age they happen to be when triage runs. The `hours_since_post` field records the actual age at capture, so analysis can distinguish early-captured from late-captured readings.

## Legacy reading type labels

Readings captured before 2026-04-04 may have type values from the previous snapshot window system: `early`, `48h`, `7d`, `30d`, `snapshot`, `velocity`. These are valid readings. The cadence redesign (2026-04-04) replaced these with `daily`, `weekly`, `mature`, `backfill`, and `reading`. Analysis queries should handle both sets of labels.
