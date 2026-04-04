# Session Event Compliance

## Purpose

Define the ARAS compliance checks that run at session entry events when an MIS is active. This procedure is invoked by CPM session skills (cpm-start, cpm-resume) when they detect an active ARAS.

## Compliance Responsibility

Session-event compliance is scoped to the current branch's own surface.
A branch can only affect its own surface files and its own central
artifact — it cannot unilaterally cause cross-surface inconsistency,
which requires a protocol event to modify scope declarations across
surfaces.

**Accepts responsibility for:**
- Level 1: The branch's central artifact is consistent with its ARA.md
- Level 2 Steps 1–4: The branch's own surface files are well-formed

**Does not accept responsibility for:**
- Cross-surface consistency (Level 3): Maintained by protocol events
  (open, merge, close) when scope declarations change
- MIS-level file well-formedness (Level 2 Steps 5–6): ARAS.md and
  DOCUMENTATION_STANDARDS.md are not the branch's surface; their
  integrity is maintained by protocol events
- Other branches' compliance: Each branch is responsible for its own
  session-event compliance

## Detection

Check for `.claude/.aras/ARAS.md`. If absent, skip — no ARAS compliance is needed.

If present with Protocol Lock != None, the calling skill handles the lock (session-event compliance is not invoked during locked protocols). Return without running compliance.

If present with Protocol Lock = None, proceed with compliance.

## Trigger

Session entry events on any branch:

- Session start (cpm-start)
- Session resume (cpm-resume)

Session pause (cpm-pause) does not trigger compliance. The next
session entry event catches any violations introduced during the
session. This avoids redundant checks when context is near-full
and ensures compliance runs with a fresh context window.

## Procedure

### 1. Identify current subsystem

Determine which branch is currently checked out. Match it against ARAS.md active subsystems list. If the current branch is not an active subsystem, report and halt — the actor may be on the wrong branch.

### 1b. Pending Merge status check

After identifying the current subsystem, check its status in
the ARAS.md Active Subsystems table.

If the subsystem's status is Active, skip this step.

If the subsystem's status contains "Pending Merge" (any variant):

```
[ARAS: Pending Merge detected (session-event [type] on [branch])]

Subsystem [instance] on [branch] has status: [status].
A merge protocol has completed for this subsystem. Before
proceeding with other work:

1. Confirm the PR merge has been completed in GitHub.
2. Pull merged content: git pull origin [source branch]

[Include the appropriate guidance based on status:]
- Pending Merge: Close → "Then run /aras-close to remove this branch."
- Pending Merge: Reallocate → "Then run /cpm-aras-reallocate to assign a new task."
- Pending Merge → "Status indicates an interrupted sync merge
  protocol. Verify merge protocol completed successfully."

Respond with: confirmed / not yet / override — [reason]
```

- confirmed: User confirms merge is done and branch is current.
  Continue to Step 2.
- not yet: Informational acknowledgment. Continue to Step 2.
  The follow-up protocol remains pending.
- override: Override with stated reason. Continue to Step 2.

This check is informational — it does not block session entry.
It ensures the managing developer is aware of pending ARAS
follow-up actions when entering a session on an affected branch.

### 2. Check for in-progress compliance event

Read the current branch's surface-state.md for in-progress
compliance event progress (written by compliance-event-protocols.md
during mid-compliance compaction).

If an in-progress compliance event is found:

- Resume it: complete remaining levels with the original context
  and scope recorded in surface-state.md
- Do not run a separate session-event compliance — the resumed
  event subsumes it
- After completion, proceed to Step 5 (On pass)

If no in-progress compliance event is found, continue to Step 3.

### 3. Recency gate

**Threshold:** 8 hours.

Read the ARAS.md Active Subsystems table. If any subsystem's last
compliance event result was PASS and the elapsed time since that
event is less than the threshold, skip compliance checks:

```
[ARAS Compliance: SKIPPED (session-event [type] on [branch])]

Last compliance: [timestamp] — PASS ([context])
Recency threshold: [threshold]
Elapsed: [elapsed time]

Compliance checks skipped. A recent PASS exists within the MIS.
```

Proceed directly to Step 5 (On pass).

If the last compliance event was NONCOMPLIANT, or if the elapsed
time exceeds the threshold, or if the managing developer explicitly
requests full compliance, continue to Step 4.

This gate applies only to session entry events (start, resume).
ARAS protocol compliance (open, merge, close) and audit compliance
always run full checks regardless of recency.

### 4. Run compliance checks

Run compliance event per `.claude/references/aras-compliance/compliance-event-protocols.md` with context `session-event ([event type] on [branch])`.

Levels: 1, 3 (Steps 1–4 only).
Scope: current branch only.

Level 2 module-wide steps (5–6) check MIS-level files and are not run at session-event — those are ARAS's responsibility at protocol events. Level 3 (cross-surface consistency) is not the branch's responsibility; cross-surface guarantees are maintained at open, merge, and close events.

### 5. On failure

Hard stop. No work proceeds until compliance is restored.

Output:

```
[ARAS Compliance: FAILED (session-event [type] on [branch])]

[findings from compliance event protocols]

This subsystem is noncompliant. Resolve before proceeding with any work.
```

### 6. On pass

Output:

```
[ARAS Compliance: PASS (session-event [type] on [branch])]
```

Continue with the session skill's normal protocol.

## Integration Note

This procedure is designed to be invoked from within CPM session
entry skills (cpm-start, cpm-resume). Each skill adds a single
conditional step:

1. Check for active ARAS
2. If active, follow this procedure
3. If pass, continue with normal protocol
4. If fail, hard stop

cpm-pause does not invoke this procedure.
