# CPM Resume

## Overview

Single session loading procedure for both fresh session start and post-compaction recovery. Implements Root Loading Path Steps 3-7 as declared in the CPM SCC Schema. Steps 1-2 (RCC traversal and ARAS pre-traversal) execute before this procedure is invoked — they are handled by Claude Code's native CLAUDE.md traversal and the MIS-ARAS Patch in `.claude/CLAUDE.md`.

This procedure's step sequence is identical regardless of which arguments are provided. Steps are either executed or structurally omitted based on declared inputs only.

## When to Activate

- At every session boundary, as directed by the CPM Instantiation RCC in `.claude/CLAUDE.md`
- Fresh session: invoked without session-id
- Post-compaction recovery: invoked with session-id (provided by cpm-pause output)
- User says "cpm resume", "cpm start", "enter context", or "start session"

## Arguments

- **session-id** (optional): First argument. When omitted, indicates fresh session — Steps 5 and 6 are structurally omitted. When provided, enables session context loading and actor identity resolution.

Active project reference may be resolved from session context content (when session-id is provided) or provided by the managing developer. Resolution method is an implementation detail.

---

## Session Loading Procedure

### Step 3 — Subsystem Additional Procedures

Load any additional procedures registered by subsystem entry points encountered during the RCC traversal (Step 1, which executed before this procedure was invoked).

If subsystem CLAUDE.md files along the actor's working path registered additional procedures (e.g., `DOCUMENTATION_STANDARDS.md`, `DOCUMENTATION_CONTEXT.md`, or other CCS-visible procedure files), load them now in the order they were encountered during traversal.

- **Omission condition:** Omitted when no declared subsystems along the working path register additional procedures.
- **Current state:** If the actor's working domain traverses subsystem entry points that declare additional procedures, those procedures are loaded at this step. If no subsystem entry points were encountered or none register additional procedures, this step is a no-op.

### Step 4 — Project Context

Load project cornerstone document(s) identified by the active project reference.

- If an active project reference is available (from session context, managing developer instruction, or other declared source), read the referenced cornerstone document(s).
- The cornerstone provides: project name, current phase, strategic decisions, and session continuity instructions.
- **Omission condition:** Omitted when no active project reference is provided.

### Step 5 — Session Context

Load session context file for the provided session-id. Search for `session-context-[session-id].md` in `.claude/session-context/` (root) and all subdirectories.

- If found, load the session context and note its location (root or subdirectory path) for use in Step 6.
- If not found in any location, surface the absence as a gap in the context summary — session recovery cannot proceed without session context.
- **Omission condition:** Omitted when no session-id is provided (fresh session).

### Step 6 — Actor Identity Resolution

Resolve actor identity from session-id against the Active Actors table in `.claude/CLAUDE.md`.

1. Read the Active Actors table in `.claude/CLAUDE.md`.
2. Match the session-id against the Nickname column (case-insensitive).
3. If **matched**: note the Actor name, Nickname, and MD Alias for inclusion in the context summary.
4. If **not matched**: register a new actor.
   a. Read `.claude/references/actor-names.md` and search for the session-id as a name or nickname (case-insensitive).
   b. If found: append a row using the full name, nickname, derived context directory, and MD Alias default (from `-> MD:` field if present, otherwise empty): `| [Name] | [Nickname] | .claude/session-context/[nickname]/ | [MD Alias or empty] |`.
   c. If not found: append a row using the session-id verbatim: `| [session-id] | [session-id] | .claude/session-context/[session-id]/ | |`.
   d. Create the actor's context directory on disk (`mkdir -p .claude/session-context/[nickname]/`).
   e. Note the new registration for inclusion in the context summary.

- **Omission condition:** Omitted when no session-id is provided (fresh session).

---

## Output

After all steps have executed (or been structurally omitted), present a context summary:

```markdown
## Context Summary

**Session ID**: [session-id, or "None (fresh session)"]

### Governance Loaded

- **RCC traversal (Step 1)**: [list CLAUDE.md files loaded by native traversal]
- **ARAS (Step 2)**: [ARAS state — active/inactive, subsystem, compliance status, protocol lock, or "No ARAS"]
- **Subsystem procedures (Step 3)**: [list additional procedure files loaded, or "No subsystem procedures registered" / "No subsystems on working path"]
- **Structural**: [list DOCUMENTATION_STANDARDS.md or other governance files loaded]
- **Procedural**: [list dev process files loaded, or "No dev process files found"]

### Project Context (Step 4)

- **Project**: [name/description from cornerstone, or "No active project reference"]
- **Current Phase**: [phase and status, or "N/A"]

### Session Context (Step 5)

- [session context summary, or "Omitted — no session-id provided" / "Session context file not found for [session-id]"]

### Work in Progress

- [current task or what was in progress at compaction, from session context]
- [or: "N/A — fresh session"]

### Actor Identity (Step 6)

- **You are**: [Actor Name] ([Nickname]). Respond to this name.
- **You call the managing developer**: [MD Alias from Active Actors table, or "MD" if none set]. Use this name naturally throughout the conversation — when addressing them directly, acknowledging a request, or at natural conversational beats. Not on every response; avoid mechanical repetition.
- **Peers**: [list other actors from Active Actors table]
- **Peer context**: Read `.claude/session-context/[peer-nickname]/` to learn about a peer's work.
- [or: "Omitted — no session-id provided"]

### ARAS (if active)

- **Subsystem**: [instance identifier] on [branch]
- **Exclusive scope**: [scope summary]
- **Shared scope**: [scope summary or None]
- **Restricted paths**: [hard-frozen and soft-frozen summaries]
- **Active subsystems**: [count and names]
- **Compliance**: PASS
- **Protocol Lock**: [lock name and step, or None]
- **Outgoing deferrals**: [count]
- **Incoming deferrals**: [count]

### Steps Executed

| Step | Root Path | Status | Reason |
|------|-----------|--------|--------|
| 3 | Subsystem Additional Procedures | [Executed / Omitted] | [reason] |
| 4 | Project Context | [Executed / Omitted] | [reason] |
| 5 | Session Context | [Executed / Omitted] | [reason] |
| 6 | Actor Identity Resolution | [Executed / Omitted] | [reason] |

---

Awaiting approval to proceed.
[If actor identity and MD Alias are set, end with a line addressing the MD by their alias, e.g., "Awaiting your call, Boss." or "Ready when you are, Sir."]
```

## Await Approval

**Do not take any action** until the managing developer explicitly approves.

Recognized approval signals: "Approved", "Proceed", "Continue", "Yes".

If the managing developer provides corrections, additional context, or redirects to a different task:
1. Incorporate the new information.
2. Re-output the context summary with changes reflected.
3. Await approval again.

Do not proceed on partial approval. If the developer approves some items but corrects others, re-summarize the full context with corrections incorporated.

---

## Anti-Patterns

### Critical

- **Don't** take any action before explicit approval — no file edits, no code changes, no exploratory reads beyond the defined step sequence
- **Don't** assume context not present in the referenced files — if something seems missing, surface the gap visibly rather than inferring
- **Don't** skip steps in the sequence — the order is designed to load governance before content
- **Don't** branch into separate paths for fresh vs. recovery — this is a single sequence with permitted omissions
- **Don't** proceed with task work if ARAS detected a protocol lock or compliance failure in Step 2 (before this procedure)

### Additional

- **Don't** re-read governance files already loaded by the RCC traversal (Step 1) — if CLAUDE.md content is already in context, those references are no-ops
- **Don't** read session context files for other session-ids — each session is scoped to its own context
- **Don't** restate governance content in the context summary — list what was loaded, not what it contains
- **Don't** carry forward session context assumptions if the session context file does not exist — treat its absence as a clean session
- **Don't** work outside declared scope — if ARAS is active, all work must fall within the current subsystem's exclusive or shared scope
- **Don't** treat procedural governance as subordinate to structural governance or vice versa — both apply within their respective authority domains
