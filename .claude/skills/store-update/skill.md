---
name: store-update
description: "Run the daily store update cycle or a targeted update for specific content. Discovers new posts, captures content, derives data, and captures readings."
---

# Store Update

Keeps the database current. Two modes: daily cycle (routine) and targeted (user-specified scope).

## Input

```
/store-update           # daily cycle — full pipeline for all new/due content
/store-update for       # targeted — ask user what to update, run scoped pipeline
/store-update debug     # daily cycle with approval gates
```

## Prerequisites

1. Chrome open with authenticated TikTok Studio session.
2. Claude Code launched with `--chrome`.

Read `tiktok_module/store/docs/tiktok-studio-extraction.md` before executing any browser-based collection.

## Daily Cycle

Runs all four store procedures in sequence, scoped to new/changed posts since the last run. Expects 0-3 new posts and 1-10 readings. Should complete in under 5 minutes with no human involvement in normal mode.

### Step 1 — Discover

Read and execute `tiktok_module/store/procedures/discover-posts/discover.md`.

1. Run `collect_post_ids.py` to check for posts published since the last discovery run.
2. If new posts found: register and enrich via `discover.py` + `collect_post.py`.
3. If no new posts: report "0 new posts" and proceed.

### Step 2 — Capture Content

Read and execute `tiktok_module/store/procedures/capture-content/capture-content.md`.

1. Run `capture_content.py --triage-only` to check for carousels without slides.
2. If new carousels found: download slides.
3. If none: report "nothing to download" and proceed.

### Step 3 — Derive Data

Read and execute `tiktok_module/store/procedures/derive-data/derive.md`.

1. Run `derive_data.py --triage-only` to check for posts needing derivation.
2. If posts need derivation: transcribe, summarize, classify. **Vision steps (transcribe + visual summary) must use Opus** (`model="opus"` on agents). See `VISION_MODEL` in `derive_data.py`.
3. If none: report "nothing to derive" and proceed.

### Step 4 — Capture Reading

Read and execute `tiktok_module/store/procedures/capture-reading/capture-reading.md`.

1. Run `triage.py` to identify posts due for readings.
2. Collect readings for all due posts.
3. Capture daily account checkpoint.

### Output (Normal Mode)

```
Store Update — 2026-04-04

  Discover: 0 new posts
  Capture Content: nothing to download
  Derive: nothing to derive
  Capture Reading: 3 readings captured, account checkpoint captured

  Done. (47 seconds)
```

### Debug Mode

Same flow with approval gates after each step. The user can approve, reject, or disable debug for the remainder.

## Targeted Mode

```
/store-update for
```

Runs the same four-step pipeline as the daily cycle, but scoped to content the user specifies. The user describes what they want to update in natural language, and Claude resolves the scope, runs the appropriate steps, and skips steps that don't apply.

### Step 1 — Ask the user what to update.

Ask: "What would you like to update?"

The user responds with natural language. The request determines which pipeline steps run and on what scope. Examples:

| User says | What it means | Steps that run |
|---|---|---|
| "I just posted a new carousel" | New post not yet in DB | Discover → Capture Content → Derive → Capture Reading |
| "The post I published yesterday" | Existing post, wants fresh reading | Capture Reading only (for that post) |
| "All Dallas posts" | Multiple existing posts, wants fresh readings | Capture Reading only (for all Dallas posts) |
| "The last 5 posts" | Recent posts, wants fresh readings | Capture Reading only (for 5 most recent) |
| "The account" | Account-level data only | Capture Reading (account checkpoint only) |
| "Post 7621390157509365023" | Specific post by ID | Capture Reading only (for that post) |
| "The austin carousel — I want to see how it's doing" | Specific post, wants fresh reading | Capture Reading only (for that post) |
| "I posted two new videos today" | Multiple new posts not yet in DB | Discover → Capture Reading |
| "Everything from March" | Batch of existing posts | Capture Reading only (for all March posts) |
| "That carousel I posted last week, it doesn't have slide images yet" | Existing post missing content | Capture Content → Derive (for that post) |

### Step 2 — Resolve to specific posts.

Query the database to translate the user's description into specific posts:

```sql
-- Resolution examples:
-- "yesterday" →
SELECT p.post_id, n.slug, p.posted_date
FROM posts p JOIN nexus_post_metadata n ON p.post_id = n.post_id
WHERE p.posted_date = date('now', '-1 day')

-- "Dallas posts" →
SELECT ... WHERE n.city = 'Dallas'

-- "last 5" →
SELECT ... ORDER BY p.posted_date DESC LIMIT 5

-- "the austin carousel" →
SELECT ... WHERE n.slug LIKE '%austin%' AND p.content_type = 'carousel'
```

For "I just posted" requests where the post isn't in the DB yet: run discover first to register it, then resolve.

### Step 3 — Confirm with the user.

Present the resolved scope and which steps will run:

```
Found 6 Dallas posts:
  2026-04-01-dallas-locals-are-furious-we     (posted 2026-04-01, last reading: 2h ago)
  2026-03-23-dallas-days-done-right           (posted 2026-03-23, last reading: 48h ago)
  2026-03-18-pov-you-are-in-dallas            (posted 2026-03-18, last reading: none)
  2026-03-16-coffee-spots-in-dallas-you       (posted 2026-03-16, last reading: 7d ago)
  2026-01-21-tourist-dallas-vs-local-dallas   (posted 2026-01-21, last reading: 30d ago)
  2026-01-18-if-you-know-these-dallas         (posted 2026-01-18, last reading: none)

Steps: Capture Reading (6 posts + account checkpoint)

Proceed?
```

The user confirms, adjusts ("skip the January ones"), or cancels.

### Step 4 — Execute the scoped pipeline.

Run only the steps identified in Step 2, only for the confirmed posts.

**If discover is needed** (new post): Follow the discover procedure for just that post — register, enrich from API (description, hashtags, sound_name, posted_time, duration).

**If capture content is needed** (new carousel without slides): Follow the capture content procedure for just that carousel — collect image URLs, download slides.

**If derive is needed** (post with slides but no derived data): Follow the derive procedure for just that post — transcribe, summarize, classify.

**If capture reading is needed** (most common): For each post in scope:
1. Run `collect_post.py` to fetch all metrics via API.
2. Write the reading to the database via `ingest.py` or direct insert.
3. If the user requested the account: capture account checkpoint via `collect_account.py`.

### Step 5 — Report.

```
Store Update — Targeted (6 Dallas posts)

  Capture Reading:
    2026-04-01-dallas-locals-are-furious-we     views=1,234   eng=4.2%  save=1.8%  (at 52h)
    2026-03-23-dallas-days-done-right           views=183     eng=1.6%  save=0.6%  (at 264h)
    2026-03-18-pov-you-are-in-dallas            views=687     eng=5.8%  save=1.5%  (at 384h)
    2026-03-16-coffee-spots-in-dallas-you       views=2,783   eng=4.9%  save=2.8%  (at 432h)
    2026-01-21-tourist-dallas-vs-local-dallas   views=54,434  eng=3.0%  save=2.4%  (at 1,800h)
    2026-01-18-if-you-know-these-dallas         views=165     eng=4.9%  save=1.2%  (at 1,872h)
  Account checkpoint: 443 followers, 13,000 likes

  Done. (12 seconds)
```

Or for a new post:

```
Store Update — Targeted (1 new post)

  Discover: 1 new post registered (2026-04-04-dallas-hidden-gems-you)
    Enriched: description, hashtags, sound_name, posted_time
  Capture Content: 8 slides downloaded
  Derive: framework=local_vs_tourist, layout=split, cta=engage, topics=food,nightlife,views
  Capture Reading: 1 reading captured (views=0, at 1h)
  Account checkpoint: 445 followers, 13,150 likes

  Done. (2m 14s)
```

## Expected Timing

| Step | Daily (typical) | Targeted |
|---|---|---|
| Discover | 0-30 seconds (usually 0 new posts) | 5-15 seconds per new post |
| Capture Content | 0-5 minutes (usually nothing to download) | 30-60 seconds per carousel |
| Derive | 0-2 minutes (usually nothing to derive) | 15-30 seconds per post |
| Capture Reading | 1-3 minutes (always has work) | 3-5 seconds per post |
| **Total (daily)** | **Under 5 minutes** | |
| **Total (targeted, reading only)** | | **Under 15 seconds** |

## Without Chrome

If Chrome is unavailable:
- **Steps 1-2 skipped** — no new posts can be discovered, no content downloaded.
- **Step 3 runs** if there are posts needing derivation (no Chrome required).
- **Step 4** prints the triage and pending-capture CSV for manual collection. The user fills the CSV from TikTok Studio by hand, then runs `python store/scripts/ingest.py --all`.

## Error Handling

On any error: stop, diagnose, report to the user with the specific post that failed and why.

```
Store Update — 2026-04-04

  Discover: 0 new posts
  Capture Content: nothing to download
  Derive: nothing to derive
  Capture Reading: ERROR — TikTok session expired during collection
    Diagnosis: collect_post.py returned auth error for post 7621390157509365023
    Action: Log in to TikTok Studio and re-run /store-update
    Progress: 2/4 readings captured before failure (ingested and saved)

  Incomplete. Re-run to capture remaining readings.
```

## What This Doesn't Do

- **Analyze.** Store-update collects data. Analysis is a separate operation on a different cadence (weekly/monthly, not daily).
- **Strategy iteration.** Data collection doesn't trigger strategy changes. That's the synthesis phase.
- **Content generation.** Store-update doesn't create posts. That's `/produce-carousel`.

## Relationship to Other Skills

- `/store-backfill` — One-time full population. Store-update is the ongoing maintenance. Both run the same four procedures; the difference is scope and scale.
- `/store-repair` — Diagnoses and fixes data issues. Store-update adds new data; repair fixes existing data.
- Analysis skills (future) — Store-update feeds the data that analysis consumes. Run store-update daily, run analysis weekly/monthly.
