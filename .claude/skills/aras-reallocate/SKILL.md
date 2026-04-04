# aras-reallocate

## Trigger

Managing developer assigns a new task to an active subsystem
whose previous task has been integrated. The branch, worktree,
and surface infrastructure are retained.

Invoked by: /aras-reallocate, "aras reallocate", "reallocate [instance]"

## Status Header Convention

Every output during this protocol must be prefixed with:

```
[aras-reallocate: Step N — Description]
```

Every prompt to the managing developer must end with:

```
Respond with: [valid options]
To pause this protocol, respond "pause".
Do not direct other tasks until this protocol completes or is paused.
```

## Protocol

### 1. Identify target

Read `.claude/.aras/ARAS.md`. If Protocol Lock ≠ None, hard stop:

```
[aras-reallocate: BLOCKED]

An ARAS protocol is already in progress: [protocol name] ([path], step [N] [status]).
Complete or resolve the in-progress protocol before invoking
a new one.
```

If ARAS.md absent, hard stop (no MIS to reallocate).

Run `git branch --show-current`. Match the current branch against
ARAS.md active subsystems. If the current branch is not an active
subsystem branch, hard stop:

```
[aras-reallocate: BLOCKED — Not on a subsystem branch]

Current branch: [branch]
This protocol must be run from an active ARAS subsystem branch.
Switch to the target subsystem branch and re-invoke.
```

Read the subsystem's ARA.md to load current task and scope into
context.

### 2. Verify branch is current with main

1. `git fetch origin`
2. `git rev-list --count [target-branch]..origin/main`

If the count is greater than zero, hard stop:

```
[aras-reallocate: Step 2 — Branch behind main]

The target branch [branch] is [N] commit(s) behind
origin/main. Run /aras-sync to synchronize, then
re-invoke /aras-reallocate.
```

### 3. Collect and enhance task

Prompt the managing developer:

```
[aras-reallocate: Step 3 — New task]

Current task: [current task from ARA.md]
Current exclusive scope: [scope summary]

Provide the new task description. Include any scope changes
(paths to add or remove from exclusive scope, shared scope
additions or removals) as part of your instructions.

Respond with: [task description and any scope changes]
To pause this protocol, respond "pause".
Do not direct other tasks until this protocol completes or is paused.
```

After receiving the MD's input, review the existing ARA.md —
task context, exclusive scope, shared scope, restricted paths —
and identify any additions worth proposing: implied scope paths
not explicitly mentioned, shared scope declarations that may be
affected, or clarifications to the task statement based on
current scope context.

Present the proposed update with any suggestions for MD
confirmation:

```
[aras-reallocate: Step 3 — Confirm update]

Proposed task: [new task description]
Proposed scope changes: [additions/removals, or None]

Suggested additions:
- [suggestion with rationale]
(or: None)

Respond with: confirmed / [corrections]
To pause this protocol, respond "pause".
Do not direct other tasks until this protocol completes or is paused.
```

If the MD provides corrections, incorporate and re-output the
confirmation prompt.

### 4. Apply

Update the subsystem's ARA.md:

- `## Current Task` section: replace with confirmed task
  description. If the section does not exist, add it after
  Branch Assignment.
- Exclusive scope, shared scope: apply any confirmed changes.

Append reallocation entry to origin.md:

- Timestamp (ISO8601)
- Previous task
- New task
- Previous exclusive scope
- New exclusive scope (if changed)
- Previous shared scope
- New shared scope (if changed)

### 5. Compliance and report

If scope changed: run compliance per
`.claude/references/aras-compliance/compliance-event-protocols.md`
with context `aras-reallocate`.

Levels: 2, 3.
Scope: updated surface + cross-surface.

If task-only (no scope change): skip compliance.

Output:

```
[aras-reallocate: COMPLETE]

Subsystem: [instance] on [branch]
Previous task: [summary]
New task: [summary]
Scope changes: [summary, or None]
Compliance: [PASS / SKIPPED (task-only update)]
```

## Compliance Responsibility

This protocol owns the compliance guarantees it introduces:
scope changes on the reallocated surface (Level 2) and
cross-surface consistency after scope adjustment (Level 3).
Level 1 cache handles unchanged surfaces automatically.
No compliance is run for task-only updates — task descriptions
are not structural artifacts.
