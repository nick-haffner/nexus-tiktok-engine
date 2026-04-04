# Compliance Event Protocols

## Purpose

Shared protocol scaffolding for all ARAS compliance events.
Each event (session, open, merge, close, audit) references
this file for status headers, progress tracking, and user
check-ins. Each event specifies which levels to run.

## Status Header Convention

Every output during a compliance event must be prefixed with:

```
[ARAS Compliance: Level N — Description (context)]
```

Where context identifies the triggering event:

```
[ARAS Compliance: Level 3 — Cross-Surface (cpm-aras-merge)]
[ARAS Compliance: Level 1 — Central Artifact (cpm-audit)]
```

## Progress Tracking

After each level completes, write progress to the appropriate
location:

**Per-surface level (1):** Write to the current branch's
surface-state.md.

**Module-wide levels (2, 3):** Write to `.claude/.aras/ARAS.md`. This is the explicit write target for module-wide compliance progress.

Progress includes:

- Compliance event type (session, open, merge, close, audit)
- Levels completed and their results (pass/fail)
- Levels remaining
- Timestamp

This ensures that if a compaction event occurs mid-compliance,
per-surface progress is recoverable from surface-state.md and
module-wide progress is recoverable from ARAS.md.

## Level Execution

For each level the calling event specifies:

1. Output status header
2. Run the level procedure per its reference file
3. Collect results (pass/fail with details)
4. Write progress where applicable
5. If pass: proceed to next level
6. If fail: enter user check-in

## User Check-In on Failure

When a level fails, present findings to the managing developer:

```
[ARAS Compliance: Level N — FAILED (context)]

Findings:
[list of violations from the level's on-failure output]

Levels remaining: [list]

Respond with: continue / halt
Do not direct other tasks until this compliance event
completes or is halted.
```

- **Continue:** Proceed to the next level. Failures are
  recorded but do not block subsequent checks.
- **Halt:** Stop the compliance event. All progress is saved
  to surface-state.md. The calling event determines the
  consequence (hard stop, report, etc.).

## Completion

When all specified levels have been run:

1. Output summary:

```
[ARAS Compliance: COMPLETE (context)]

Level 1: [pass/fail/skipped]
Level 2: [pass/fail/skipped]
Level 3: [pass/fail/skipped]

Overall: [COMPLIANT / NONCOMPLIANT]
```

2. Clear compliance event progress from surface-state.md
3. Update last compliance event timestamp and result in
   surface-state.md and in ARAS.md Active Subsystems table
4. Return overall result to the calling event

## Level Reference

| Level | File       | Checks                                         |
| ----- | ---------- | ---------------------------------------------- |
| 1     | level-1.md | Central artifact state vs surface declarations |
| 2     | level-2.md | Per-file schema assertions                     |
| 3     | level-3.md | Cross-surface consistency                      |
