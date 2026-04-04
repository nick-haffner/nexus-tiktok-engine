---
name: cpm-pause
description: "Prepare for context window compaction by updating documentation, capturing repetitive instructions, and generating a post-compaction prompt. Accepts optional session-id and context-percentage arguments. Use when context window is filling (>80%), user mentions compaction, or asks to 'persist context'. Invoked by 'prepare for compaction', 'persist context', 'cpm-pause [session-id] [N%]', or /cpm-pause."
---

# Persist Context

## Overview

Prepare for Claude Code conversation compaction for session $ARGUMENTS by persisting critical context into the documentation layer model defined in `docs/DOCUMENTATION_STANDARDS.md`. This skill handles pre-compaction only. Post-compaction recovery is handled by the recontextualize skill.

## When to Activate

- User mentions context window is filling up (>80%)
- User requests preparation for `/compact` command
- User says "persist context" or "prepare for compaction"

## Arguments

Raw arguments: $ARGUMENTS

Parse arguments by splitting on whitespace. Any argument matching `\d+%` is the **context-percentage**. Any other argument is the **session-id override**. Both are optional and may appear in either order.

- **session-id** (optional): Override for session identifier. If provided, use this value. If omitted, resolve via the session ID resolution rule below.
- **context-percentage** (optional): Current context window usage as a percentage (e.g., `95%`). If omitted, assume <95% (full protocol).

### Session ID Resolution

Resolve the session-id using the first matching rule:

1. **Argument override** — If a session-id argument was provided, use it.
2. **Resume ID** — If `/cpm-resume [session-id]` was invoked earlier in this conversation, reuse that session-id.
3. **Generate** — Generate a new session-id and create a new session context file.

### Context Percentage Rule

If context-percentage is **≥95%**: skip governance re-reads (Step 1), backup (Step 4), and repetitive instructions (Step 5). Governance was already loaded at session entry by cpm-resume or cpm-start — re-reading is validation, not discovery. At ≥95%, that validation isn't worth the risk of running out of room before the session context write completes. Proceed directly to Step 2 (ARAS State Capture) and Step 3 (Update Documentation), writing session context from conversation state, then skip to Step 6 (Output).

---

## Pre-Compaction Protocol

### Step 1: Read Documentation in Order

**Skip this step if context-percentage ≥95%.** Governance was already loaded at session entry. Proceed directly to Step 2.

Read the following files in strict order. Do not skip any file that exists. If a file does not exist, note its absence.

1. **`CLAUDE.md`** — Information integrity principles. These govern all subsequent reading and action.
2. **`docs/DOCUMENTATION_STANDARDS.md`** — Documentation layer model, quality principles, and structural rules. This defines how all other documentation is organized.
3. **Path-reading chain** — If the current work involves a specific domain, read any `DOCUMENTATION_STANDARDS.md` files and development process root files along the path from repository root to the working directory.
4. **Project cornerstone document(s)** — As referenced in the current project. These provide current project state, strategic decisions, and session continuity instructions.
5. **Session context file** — Search for `session-context-[session-id].md` in `.claude/session-context/` (root) and all subdirectories (case-insensitive). Read the file matching the resolved session-id, if it exists.

### Step 2: ARAS State Capture (no compliance)

Check for `.claude/.aras/ARAS.md`. No compliance checks are performed during cpm-pause under any condition.

If ARAS.md is absent → no ARAS, continue to Step 3.

If ARAS.md is present:

- If Protocol Lock != None → note lock state (protocol name, path, step, parameters) for session context capture. Continue to Step 3.
- If Protocol Lock = None → note MIS active for session context capture. Continue to Step 3.

### Step 3: Update Documentation

Update documentation with current session state. Reference `docs/DOCUMENTATION_STANDARDS.md` for layer definitions and the verification checklist. Only update what has changed. Do not create new files unless necessary.

**Session context**: Fully rewrite — never append. Capture anything relevant to the current session that should survive a single handoff but does not belong in permanent or project documentation. This includes session-specific behavioral preferences, temporary configurations, and in-flight context that hasn't been placed in a project doc yet. Keep it small and scoped.

Session context file location depends on actor identity:

- **Actor identified** (session was started or resumed with an actor from the Active Actors table in `.claude/CLAUDE.md`, matched case-insensitively): Write to the actor's context directory as listed in the table (e.g., `.claude/session-context/jarvis/session-context-[session-id].md`). If an existing session context file for this session-id was found in a different location during Step 1, write to the actor directory — the actor directory is authoritative.
- **No actor identified**: Write to `.claude/session-context/session-context-[session-id].md` (root).

**ARAS state** (if active): Include in the session context file alongside other session-specific context:

- Instance identifier and branch assignment
- Exclusive scope and shared scope
- Protocol Lock state if any (from ARAS.md Protocol Lock section)
- Number of active subsystems and their general scope

**Permanent documentation** (`docs/` excluding `docs/tmp/`): Update only if decisions or architectural changes made this session are finalized and authoritative. Permanent docs describe the codebase as-is — do not include in-progress or speculative content.

**Project documentation** (`docs/tmp/[epic-name]/`): Update only if the current work is associated with an active epic. Update the cornerstone document with current project state: phase status, progress tracking, strategic decisions finalized this session, and session continuity instructions. Update or create additional project files only if content needs to survive beyond a single handoff but is not yet authoritative. If no epic is active, skip project documentation entirely.

#### Documentation Update Checklist

| Context Type                            | Destination                         | Example                                                    |
| --------------------------------------- | ----------------------------------- | ---------------------------------------------------------- |
| Finalized architectural decisions       | Permanent docs                      | Updated routing.md with new route structure                |
| Finalized behavioral or system rules    | Permanent docs                      | Added validation rule to system-rules.md                   |
| Gaps or issues discovered               | Permanent docs (GAPS_AND_ISSUES.md) | "Auth token refresh not implemented"                       |
| Phase/task completion status            | Project cornerstone                 | "Phase 1.1: Complete"                                      |
| In-progress work state                  | Project cornerstone                 | "Reviewing concern 4 of 8"                                 |
| Strategic decisions with rationale      | Project cornerstone                 | "Chose SQS over SNS because..."                            |
| Deferred items                          | Project cornerstone or project file | "DB migration deferred to Phase 2"                         |
| Project-specific procedures             | Project file                        | Iteration protocol for this epic                           |
| Session-specific behavioral preferences | Session context                     | "Use verbose output for this session"                      |
| Temporary configurations or modes       | Session context                     | "Testing against staging environment"                      |
| In-flight context not yet placed        | Session context                     | "Exploring two approaches to auth, undecided"              |
| Next action                             | Post-compaction prompt              | "Continue with concern 5"                                  |
| ARAS subsystem state                    | Session context                     | "On branch-a, exclusive scope: /api, 2 outgoing deferrals" |

After updates, verify against the quality principles verification checklist in
`docs/DOCUMENTATION_STANDARDS.md`.

### Step 4: Backup

**Skip this step if context-percentage ≥95%.**

IF:

- the most recent backup (per `.claude/references/backup-procedure.md`) was created on a different calendar day than today (local time)

OR

- any edits have been made to .claude persistent or .aras persistent files this session (excluding session context, repetitive instructions, settings and local settings). This does NOT include timestamps for .aras files.

THEN:

run the backup procedure per `.claude/references/backup-procedure.md`. If backup fails, report to managing developer and halt.

ELSE:
Proceed to Step 5 without backup.

### Step 5: Capture Repetitive Instructions

**Skip this step if context-percentage ≥95%.**

Identify instructions from this session that:

- Were stated multiple times
- Used "always", "never", "make sure to", "remember to" language
- Corrected Claude's behavior (implicit instructions)

**SKIP** if no such instructions are identified.

**Output in response** (for user visibility):

```
### Repetitive Instructions Observed This Session:
- [instruction 1]
- [instruction 2]
```

**Persist to file** for propose-skills consumption:

- File: `.claude/skills/propose-skills/references/repetitive-instructions/[session-id].jsonl`
- Format: `{"session_id": "<id>", "timestamp": "<ISO8601>", "project": "<path>", "instructions": ["...", "..."]}`
- Overwrite the session's file (each session owns its file; all instructions for the session are captured at each compaction)

### Step 6: Output Pre-Compact Response

Format the response as:

## Ready for Compaction

**Session ID: [session-id]**

Documentation updated:

- [list of files updated with brief description of changes]
- [or: "No active epic — project documentation skipped."]

[If context-percentage ≥95%:]
- Backup: SKIPPED (≥95% context)
- Repetitive instructions: SKIPPED (≥95% context)

### Repetitive Instructions Observed This Session:

- [instruction 1]
- [instruction 2]
  (Also persisted to .claude/skills/propose-skills/references/repetitive-instructions/[session-id].jsonl)

[If no repetitive instructions were captured (either skipped or none identified), omit this section entirely.]

### Post-Compaction Prompt (copy after /compact):

───────────────────────────────────────
/cpm-resume [session-id]
───────────────────────────────────────

Run `/compact` now.

---

## Anti-Patterns

### Critical

- **Don't** include post-compaction recovery steps in this skill's output — that is handled by the cpm-resume skill
- **Don't** modify other sessions' repetitive instruction files — each session owns only its own file
- **Don't** append to session context — fully rewrite it every time
- **Don't** update ARAS surface documentation during cpm-pause — surface updates happen through compliance events, not documentation persistence
- **Don't** re-read governance files when context-percentage ≥95% — they were loaded at session entry and re-reading risks exhausting the context window before the session context write completes
- **Don't** run backup or repetitive instructions when context-percentage ≥95% — session context persistence is the priority

### Additional

- **Don't** create new documentation files when updating existing ones suffices
- **Don't** include speculative or unconfirmed content in any layer
- **Don't** include sensitive data (API keys, passwords) in the post-compaction prompt
- **Don't** restate documentation layer definitions — reference `docs/DOCUMENTATION_STANDARDS.md`
