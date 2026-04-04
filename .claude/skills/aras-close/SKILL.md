# aras-close

## Trigger

Managing developer has completed a PR merge in GitHub for a
parallel workstream branch. aras-sync should have been run
prior to the PR merge to ensure the branch's work is present
on main.

## Resume Handling

If ARAS.md exists with Protocol Lock = ARAS-CLOSE:

1. Read the step log, Parameters (Terminating Branch, Surviving
   Branch), and Path from ARAS.md Protocol Lock
2. Run `git branch --show-current`. If current branch ≠ Source
   Branch from ARAS.md, hard stop:

   ```
   [aras-close: BLOCKED — Wrong worktree]

   aras-close must be run from the main worktree ([source branch]).
   Switch to the main worktree and re-invoke.
   ```

3. Output: "[aras-close: RESUMING [path] from after Step N]"
4. For each step in the step log:
   - `complete` → skip
   - `in-progress` → verify (check filesystem), then execute or
     mark complete
   - absent → execute from this step
5. Continue through remaining steps

## Compliance Responsibility

**close-branch (MIS continues):** The procedure owns structural
cleanup. Step 2 of close-branch.md ("Update remaining surfaces")
is explicitly responsible for removing all shared scope declarations
on remaining surfaces that reference the closing branch. If this
step executes correctly, no L3 violation persists after closure.
Compliance is not run — residual inconsistency indicates procedural
failure, detectable via /aras-audit.

**close-aras (MIS dissolves):** The MIS is fully dissolved; no
surfaces remain. No compliance is applicable or meaningful.

**Does not accept responsibility for:**
- Pre-existing compliance state of remaining surfaces
- Pre-existing cross-surface inconsistencies introduced before
  this protocol

## Protocol

### 1. Assess current state

Check `.claude/.aras/ARAS.md` for Protocol Lock state:

- If ARAS.md exists with Lock = ARAS-CLOSE → resume path (see Resume Handling)
- If ARAS.md exists with Lock = [other] → hard stop:

```
[aras-close: BLOCKED]

An ARAS protocol is already in progress: [protocol name] ([path], step [N] [status]).
Complete or resolve the in-progress protocol before invoking
a new one.
```

- If ARAS.md exists with Lock = None → proceed
- If ARAS.md absent → hard stop (no MIS to close)

Run `git branch --show-current`. If current branch ≠ Source Branch
from ARAS.md, hard stop:

```
[aras-close: BLOCKED — Wrong worktree]

aras-close must be run from the main worktree ([source branch]).
Switch to the main worktree and re-invoke.
```

Read ARAS.md. Identify active subsystems.

### 2. Identify and confirm closure target

Ask the managing developer which subsystem is being closed.
Validate the response against ARAS.md active subsystems.

```
[aras-close: Step 2 — Confirm closure target]

[Instance] on [branch] is the closure target.
This branch and its worktree will be removed.

Confirm the PR merge has been completed in GitHub and this
subsystem should be closed.

Respond with: confirmed / halt
```

If the managing developer responds "halt", stop the protocol.

### 3. Verify branch is current with main

Check that the target branch's work is present on main:

1. `git fetch origin`
2. `git rev-list --count origin/main..[target-branch]`

If the count is greater than zero, commits on the target branch
are not yet on main. Recommend running /aras-sync before closing.

This is a recommendation — the managing developer may proceed if
they confirm the gap is intentional.

### 4. Determine MIS outcome and acquire lock

Count active subsystems remaining after removing the closing one.

Acquire Protocol Lock in ARAS.md (steps 1–3 are read-only checks —
the lock is acquired here as the first state-modifying action):

- Lock: ARAS-CLOSE
- Acquired: [ISO8601 timestamp]
- Invoked From: [current branch]
- Parameters: Terminating Branch = [closing branch], Surviving Branch = [remaining branch(es)]
- Path: close-branch (more than one remaining) or close-aras (one remaining)
- Initial step log

Route:
- More than one remaining → follow `references/close-branch.md`
- One remaining → follow `references/close-aras.md`

### 5. Report

**close-branch path:** Release Protocol Lock: set Lock to None,
remove Parameters and Step Log. ARAS.md persists — the MIS continues
with remaining subsystems.

Output:
- MIS state (subsystem removed, MIS active)
- Remaining subsystems with scope summaries

**close-aras path:** ARAS.md was deleted during dissolution — no
lock release required.

Output:
- MIS dissolved — SIS restored
- Confirmation of clean state
