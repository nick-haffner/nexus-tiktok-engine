# Procedures Handbook

The engine is organized into four **functions**, each in its own directory:

| Function | Directory | Purpose |
|---|---|---|
| **Store** | `store/` | Collect, capture, and classify TikTok data |
| **Analyze** | `analyze/` | Produce performance reports, insights, and strategic recommendations |
| **Generate** | `generate/` | Create TikTok content (carousels, captions, hashtags) |
| **Integrate** | *(planned)* | Connect analysis to strategy to generation — closing the feedback loop |

## Getting Started

**First-time setup:**

1. Install Claude Code and the Chrome extension.
2. Open Chrome and log into TikTok Studio (`tiktokstudio.com`).
3. Run `claude --chrome` from the `nexus-tiktok-engine/` directory.
4. Type `/store-backfill` to populate the engine with your existing TikTok data.
5. Follow the prompts. Takes 15-60 minutes. You can take breaks — progress is saved.

After setup, follow the instructions in `store/AUTONOMOUS.md` for daily operations.

**For all operations:** Chrome must be open with TikTok Studio logged in. Claude Code must be launched with `--chrome`. When Claude asks permission to run scripts or access the browser, approve all requests.

## Autonomous Mode

Run the engine with minimal involvement. Follow the per-function instructions below — they tell you exactly what to do, when to do it, and what to expect.

### Store

Follow `store/AUTONOMOUS.md` for daily operations. Covers:
- Daily data capture (once per day, under 3 minutes)
- Post-publication velocity capture (within 6-12 hours of posting)
- Troubleshooting

## Tools

Tell Claude what you want. It runs the right components.

### Store

| What you want | Tell Claude | Technical components |
|---|---|---|
| Set up the engine for the first time | `/store-backfill` | `collect_post_ids.py`, `discover.py`, `collect_post.py`, `collect_content.py`, `capture_content.py`, `derive_data.py`, `triage.py`, `ingest.py`, `collect_account.py` |
| Daily data capture | `/store-update` | `collect_post_ids.py`, `discover.py`, `capture_content.py`, `derive_data.py`, `triage.py`, `collect_post.py`, `ingest.py`, `collect_account.py` |
| Capture data for specific content | `/store-update for` — then describe what you want | `collect_post.py`, `ingest.py`, `discover.py`, `collect_content.py`, `derive_data.py` (scoped) |
| Check data health | `/store-repair` | DB queries, filesystem scan |
| Fix a specific data issue | `/store-repair for` — then describe what to fix | `derive_units.py` classifiers, `collect_post.py`, `discover.py`, `generate_artifacts.py` |
| Get a fresh reading for a post | "Get me a reading for [post]" | `collect_post.py`, `ingest.py` |
| See which posts need readings | "What posts are due for readings?" | `triage.py` |
| Check what posts exist on TikTok | "How many posts are on the account?" | `collect_post_ids.py` |
| Regenerate a visual summary | "Regenerate the visual summary for [post]" | `derive_data.py` (vision AI) |
| Reclassify frameworks | "Reclassify all frameworks" or `/store-repair for` | `derive_units.classify_framework` |
| Download slides for a carousel | "Download slides for [post]" | `collect_content.py` |
| Capture an account checkpoint | "What's the current follower count?" | `collect_account.py` |
| Generate missing captions/READMEs | "Generate missing captions" | `generate_artifacts.py` |

## AI Agents

Claude has full context of your TikTok account — every post, every metric, every classification, every strategy decision, and every piece of content. Ask it anything.

**Data & performance:**
- "How are my Dallas posts performing compared to Seattle?"
- "What's my best-performing framework?"
- "Show me my engagement trend over the last 3 months"
- "Which posts have the highest save rate?"

**Strategy & decisions:**
- "Should I post more Local vs Tourist or Worth It content?"
- "Which cities should I focus on next?"
- "Am I posting often enough?"
- "What's working and what isn't?"

**Content & creation:**
- "Help me plan a carousel for Nashville"
- "Write hooks for a Phoenix Worth It post"
- "What topics get the most saves?"
- "What does my best-performing post look like?"

**Account & operations:**
- "How many followers did I gain this month?"
- "What data am I missing?"
- "When was the last time analytics were captured?"
- "Compare my account now vs a month ago"

**Combine anything:**
- "Look at my top 5 posts, read their slides, and tell me what they have in common"
- "Based on my performance data, draft a content plan for next week"
- "Find my worst-performing posts and suggest what to change"
