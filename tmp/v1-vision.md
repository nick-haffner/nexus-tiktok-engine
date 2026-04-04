# V1 Vision — Expected End State & Use Cases

Generated 2026-04-03.

---

## Engine Functions

The engine is organized into four functions, each in its own directory under `tiktok_module/`:

| Function | Directory | Responsibility |
|---|---|---|
| **Store** | `store/` | Collect, capture, and classify TikTok data |
| **Analyze** | `analyze/` | Produce performance reports, insights, and strategic recommendations |
| **Generate** | `generate/` | Create TikTok content |
| **Integrate** | *(planned)* | Connect analysis outputs to strategy updates to generation instructions |

## End State

1. **Autonomous collection** — A scheduled procedure maintains all relevant data in a local database. The user doesn't think about data collection; it happens.

2. **Autonomous analysis** — Scheduled analysis procedures run against the collected data, producing performance reports, content strategy insights, audience growth assessments, cadence findings, and conversion funnel analysis.

3. **Autonomous strategy iteration** — Based on analysis outputs and user inputs, strategy files are updated automatically. These updates flow into content generation procedures and instructions, closing the feedback loop.

4. **Content generation assistance** — Explicit content generation instructions enable partial automation. Autonomous post ideation with generation assistance reduces the user's cognitive load and time-to-post.

5. **Full-context AI agent** — An AI agent with 100% context of the social media account, its data, its strategy, and its content history. The agent can advise, analyze, create, and execute across all engine functions.

## Use Cases

### Autonomous cycle
Follow the engine's instructions for a fully autonomous loop: collect → analyze → iterate strategy → generate content → post → repeat. The user's role is approval and posting.

### Unit use
Use individual capabilities independently:
- Capture all relevant analytics
- Run analytics reports
- Run strategy iterations
- Use content generation procedures

### Agent-assisted use
Use the AI agent to combine or extend any unit:
- Advise on strategy using data
- Advise on strategy using analysis
- Input data into reports
- Input analyses into reports
- Make changes to strategy and generation
- Create content and/or advise on content
- Schedule tasks/reminders based on generation instructions
- Explore data and find insights
- Any creative combination of the above

## Handbook Structure

The engine outputs **instructions**, not **information**.

### High-level engine handbook
- Describes available functionality (menu, not manual)
- Includes autonomous mode entry point
- Includes a brief procedure directory with user-facing descriptions
- Mentions AI agent capabilities with examples to inspire creativity
- Does not explain how the system works internally

### Autonomous mode instructions
- Generated for every part of the engine
- A user can blindly follow these and the engine will:
  - Store all intended data
  - Analyze on an intended cadence
  - Iterate strategic decisions based on analyses on an intended cadence
  - Conduct content generation based on a cadence prescribed by strategy
- Instructions are actions and expected results, not context or rationale

### Instruction readiness by function

| Function | Ready for instruction generation | Notes |
|---|---|---|
| Store | Yes | All 4 procedures implemented, skills defined, E2E tested |
| Analyze | Partially | L1-L5 implemented, synthesis phase not built, no scheduling |
| Strategy | No | Strategy files exist but no iteration procedure |
| Generate | Partially | Produce-carousel procedure exists but doesn't consume strategy outputs |

## Key Decisions

- **Instructions not information.** Users follow steps, not read documentation.
- **Autonomous by default, manual by choice.** The engine runs itself; the user participates where they want to.
- **The AI agent is the interface.** Users don't need to understand the file structure, database, or scripts. They tell Claude what they want.
- **Debug mode for oversight.** Approval gates are off by default, enabled with `debug` flag for users who want to review each step.
- **Two-file instruction model.** The handbook is the coordinator (entry point, procedure directory, agent examples). Per-function instruction files are standalone documents the user follows blindly. Stable instructions are written files. Unstable instructions are regenerated per-run.
- **Store instructions are stable.** Store architecture is finalized. Instructions don't need regeneration.
- **Store-repair is a provider/developer tool, not an autonomous mode instruction.** Users in autonomous mode run `/store-update` daily. Repair is for debugging by the provider.
- **Velocity readings matter for growth.** Marketing best practice captures early-velocity data (6-12h post-publication) to enable fast creative reaction. Daily runs alone miss the velocity window. Instructions prescribe post-publication velocity captures.
- **Permission approval guidance.** Instructions tell users to approve all Claude permission requests during store operations. Permission fatigue is the primary friction point for non-technical users.
