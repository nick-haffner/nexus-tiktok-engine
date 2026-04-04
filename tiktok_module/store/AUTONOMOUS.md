# Store Instructions

Follow these instructions to keep your TikTok data current.

---

## Requirements

- **Chrome** open with TikTok Studio logged in (`tiktokstudio.com`)
- **Claude Code** launched with `claude --chrome` from the `nexus-tiktok-engine/` directory
- When Claude asks permission to run scripts, execute JavaScript, or access files: **approve all requests.** These are the engine's normal operations.

## Daily Routine

Run `/store-update` once per day, ideally in the morning.

Takes 30 seconds to 3 minutes. No action needed unless an error appears.

**What you'll see on a normal day:**
```
Store Update — 2026-04-04

  Discover: 0 new posts
  Capture Content: nothing to download
  Derive: nothing to derive
  Capture Reading: 3 readings captured, account checkpoint captured

  Done. (47 seconds)
```

**What you'll see after publishing a new post:**
```
Store Update — 2026-04-04

  Discover: 1 new post registered (2026-04-04-dallas-hidden-gems-you)
    Enriched: description, hashtags, sound_name, posted_time
  Capture Content: 1 carousel, 8 slides downloaded
  Derive: 1 post — framework: local_vs_tourist, layout: split, cta: engage
  Capture Reading: 4 readings captured, account checkpoint captured

  Done. (2m 34s)
```

## After Publishing a Post

Run `/store-update for` within 6-12 hours of posting.

Tell Claude: "I just posted a new carousel" (or video, or describe what you posted).

This captures early velocity data — how the algorithm is distributing your post in its first hours. Early velocity signals whether a post is getting algorithmic push or being suppressed.

**Why this matters:** The first 6-24 hours determine how TikTok distributes your post. A velocity reading lets you and the analysis engine compare early performance across posts. Posts showing strong early velocity may warrant engagement boosting (responding to comments, sharing to stories). Posts showing weak velocity early are unlikely to recover — the next post's strategy should adjust.

If you can't run it within 12 hours, the daily run captures it the next morning. The velocity window is missed but the post is still fully processed.

## If Something Goes Wrong

- **"TikTok session expired"** — log back into TikTok Studio in Chrome, then re-run the command.
- **"Chrome not connected"** — restart Claude with `claude --chrome`.
- **Any other error** — re-run the command. Always safe, never corrupts data.
