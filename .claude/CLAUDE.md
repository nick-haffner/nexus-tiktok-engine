# CPM Root Context Chain

## MIS-ARAS Patch

> **Known architectural gap:** The correct sequence is ARAS SCC entering the CPM SCC from outside. The current implementation inverts this — ARAS pre-traversal is triggered from within the CPM root CLAUDE.md. This patch exists because the ARAS system context chain has not yet been formalized as an independent SCC with its own entry point.

Before proceeding with concern chain traversal, check for ARAS governance:

1. Check if `.claude/.aras/ARAS.md` exists.
2. If **absent** — no ARAS is active. Proceed to CPM Instantiation RCC below.
3. If **present** — load ARAS governance:
   - Read `.claude/.aras/ARAS.md`.
   - Identify the current branch (`git branch --show-current`) and load the corresponding `ARA.md` for the current subsystem.
   - Check Protocol Lock state. If Protocol Lock is not None, hard stop — non-protocol work is blocked until the protocol completes.
   - If Protocol Lock is None, run session event compliance per `.claude/references/aras-compliance/session-event.md`.
   - If compliance fails, hard stop per session-event.md.
   - If compliance passes, load the current branch's ARA.md scope into context and proceed.

## CPM Instantiation RCC

At every session boundary — whether a fresh session start or post-compaction recovery — run the session loading procedure before any other work:

**Invoke `/cpm-resume`** with the appropriate arguments:
- Fresh session (no prior context): `/cpm-resume` (no arguments)
- Fresh session with actor identity: `/cpm-resume [session-id]`
- Post-compaction recovery: `/cpm-resume [session-id]`

No actor may begin work without first completing the session loading procedure and receiving explicit managing developer approval.
