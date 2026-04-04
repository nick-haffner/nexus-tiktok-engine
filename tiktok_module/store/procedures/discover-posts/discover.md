# Discover — Post Registration & API Enrichment

Identifies TikTok posts not in the database, registers them, and enriches them with API metadata. Idempotent — safe to run repeatedly on the same input.

**Scope:** Registration and API enrichment only. Content download (slide images) is handled by the Capture Content procedure. Derived classification (framework, visual summaries) is handled by the Derive procedure.

## When to Run

- First-time setup (backfill all existing posts)
- After publishing a post outside the normal generate pipeline
- When the database may be out of sync with TikTok
- Periodically to enrich posts with API metadata (sound_name, posted_time, duration)

This is an on-demand procedure, not part of the daily capture.

## Prerequisites

1. **Chrome** open with an authenticated TikTok Studio session (for post ID collection and API enrichment).
2. **Claude Code** launched with `--chrome` flag (if running via Claude-in-Chrome).

**Verification:** The first API call during enrichment (Step 4) serves as session verification. If it fails with an auth error, stop and report.

## Error Handling

Same pattern as Capture Reading. Every step checks for errors and stops on failure:

1. **Identify the error.** Read the error message or unexpected output.
2. **Diagnose the cause.** Prerequisite failure, data issue, or script bug.
3. **Report to the manager.** State what failed, the diagnosis, and whether it's recoverable.
4. **Do not continue past the error.** The database is idempotent — re-running after a fix is safe.

## Idempotency

- **New posts:** INSERT into `posts`, `nexus_post_metadata`, and the appropriate subtype table.
- **Existing posts:** UPDATE only fields that are currently NULL. Non-null fields are never overwritten.
- **Re-running with the same input:** All posts report "unchanged." No data corruption.

This means partial runs are safe. If discover crashes at post 50 of 100, the next run re-processes all 100: 50 report "unchanged," 50 get registered. No resume handling needed.

## Procedure

### Step 1 — Check the Cutoff

```
python store/scripts/discover.py --check
```

Reports the cutoff date from the last discovery run. Only posts published after this date need to be checked. If no previous run exists, include all posts.

### Step 2 — Collect Post IDs from TikTok

Run `collect_post_ids.py` to get the collection JavaScript:

```
python store/scripts/collect_post_ids.py
```

Execute the JavaScript on any `tiktok.com` page (TikTok Studio or public profile — session cookies required). The JS automatically:

1. Gets the account's `secUid` from the TikTok Studio user API
2. Paginates through `/api/post/item_list/` to collect all posts
3. Returns JSON with post IDs, dates (from `createTime`), descriptions, and content types

Parse the result and save as JSON (preferred — carries full metadata including descriptions and hashtags):

```
python store/scripts/collect_post_ids.py --parse '<json_result>' --output-json store/procedures/discover-posts/input.json
```

Or as CSV (legacy — minimal metadata, descriptions not included):

```
python store/scripts/collect_post_ids.py --parse '<json_result>' --output store/procedures/discover-posts/input.csv
```

Review the output. Confirm the post count matches what TikTok Studio shows. If any posts are missing or have invalid IDs, note them.

If no posts exist after the cutoff date, there is nothing to discover. Stop here.

### Step 3 — Register Posts

Run discover with the input file (JSON or CSV):

```
python store/scripts/discover.py store/procedures/discover-posts/input.json
```

The script processes posts in batches of 5:
- For each post, searches the repo for a matching directory (by date) and extracts metadata from README.md and copy.md if found.
- Registers new posts or updates null fields on existing posts.
- Prints per-post status: `[REG]` (new), `[UPD]` (null fields filled), `[ - ]` (unchanged).
- Commits after each batch.
- Stops on any database error with a diagnosis.

**Approval gate (debug mode only):** After each batch, print a summary and wait for manager approval before proceeding. In normal mode, batches proceed automatically. See the `/store-backfill` skill for debug flag usage.

Review the discovery report. Note how many posts have incomplete metadata — these are candidates for API enrichment.

### Step 4 — Enrich from TikTok API

For each post that has null fields (particularly description, hashtags, content_type, sound_name), run `collect_post` to fetch API data:

```
python store/scripts/collect_post.py <post_id>
```

Execute the generated JavaScript on any TikTok Studio page. Parse the result:

```
python store/scripts/collect_post.py <post_id> --parse '<json_result>'
```

The result contains both transient metrics (ignore for discover) and enrichment fields:
- `sound_name` — audio track name
- `duration_seconds` — video duration (videos only)
- `posted_time` — derived from `create_time` (HH:MM+00:00)

These are written to the database via `enrich_from_api` in the discover script. The orchestrating procedure (Claude) calls `collect_post` for each post and applies the enrichment.

**Batch this step.** Process 5 posts at a time. After each batch:
- Print a summary of what was enriched.
- If any API call fails (auth error, rate limit, missing data), stop and diagnose.

For the full enrichment of API-available fields (description, hashtags, content_type, aweme_type, slide_count), use the discover procedure's Step 4 from the TikTok API as documented in `store/docs/tiktok-studio-extraction.md`. This requires running JavaScript that calls `/aweme/v2/data/insight/` with `insigh_type: "video_info"`.

### Step 5 — Verify and Clean Up

Review the final state:
- How many posts are registered?
- How many have complete metadata vs. null fields?
- Are there any posts in TikTok Studio not captured in the input CSV?

Delete the input CSV after successful completion:

```
rm store/procedures/discover-posts/input.csv
```

The cutoff date in `last-run.txt` was updated by the discover script. Future runs will only need to include posts published after this date.

```
Discover complete. X posts registered, Y updated, Z unchanged.
```

---

## Without Chrome (Manual Collection)

If Chrome access is unavailable:

1. **Step 1** (check cutoff) — works without Chrome.
2. **Step 2** (collect post IDs) — must be done manually. Open TikTok Studio in a browser, read post IDs and dates from the Content tab, write `input.csv` by hand.
3. **Step 3** (register) — works without Chrome.
4. **Step 4** (API enrichment) — cannot be done without Chrome. Posts are registered with incomplete metadata. Enrichment can be run later when Chrome access is available.

---

## Scripts Reference

| Script | Purpose | Requires Chrome |
|---|---|---|
| `store/scripts/collect_post_ids.py` | Generate JS to collect post IDs from Studio Content tab | Yes (JS execution) |
| `store/scripts/discover.py` | Register posts, update null fields, batch by batch | No |
| `store/scripts/collect_post.py` | Fetch API data for enrichment (shared with capture reading) | Yes (JS execution) |

## Downstream Procedures

After discover completes, the following procedures can run on the registered posts:

| Procedure | What it does | Depends on |
|---|---|---|
| **Capture Reading** | Collect transient performance metrics | Posts registered in DB |
| **Capture Content** | Download slide images, extract slide text | Posts registered, content_type known |
| **Derive** | Classify framework, slide_layout, CTA, visual summaries, content_topics | Content captured, slide text available |
