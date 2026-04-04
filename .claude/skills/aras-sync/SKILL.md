# aras-sync (Synchronized Integration Event)

## Trigger

Managing developer requests a Synchronized Integration Event —
merges all ARAS subsystem branches into the source branch and
distributes the result back to all branches, producing a fully
synchronized MIS state.

Invoked by: /aras-sync, "aras sync", "aras sie",
"synchronized integration event", "run SIE"

## Arguments

`ordered` (optional) — if present, prompt MD to specify merge
order before proceeding. If omitted, merge alphabetically by
branch name.

## Status Header Convention

Every output during this protocol must be prefixed with:

```
[aras-sie: Step N — Description]
```

Every prompt to the managing developer must end with:

```
Respond with: [valid options]
To pause this protocol, respond "pause".
Do not direct other tasks until this protocol completes or is paused.
```

## Protocol

### 1. Identify subsystems

Read `.claude/.aras/ARAS.md`. If Protocol Lock ≠ None, hard stop:

```
[aras-sie: BLOCKED]

An ARAS protocol is already in progress: [protocol name] ([path], step [N] [status]).
Complete or resolve the in-progress protocol before running
a Synchronized Integration Event.
```

Run `git branch --show-current`. If current branch ≠ Source Branch from ARAS.md, hard stop:

```
[aras-sie: BLOCKED — Wrong worktree]

aras-sync must be run from the main worktree ([source branch]).
Switch to the main worktree and re-invoke.
```

Identify all active subsystems and their branches.

Discover worktree paths by running:

```
git worktree list --porcelain
```

Match each subsystem branch to its worktree path from the output.

### 1b. Check for uncommitted changes

For each worktree (main + all subsystem worktrees), run:

```
git -C [worktree-path] status --porcelain --untracked-files=all
```

If all worktrees are clean, skip to the next step.

If any worktree has uncommitted changes, report per worktree:

```
[aras-sie: Step 1b — Uncommitted changes detected]

The following worktrees have uncommitted changes:
- [branch] ([worktree-path]): [N] modified, [N] new

An SIE synchronizes committed state only. Uncommitted changes
will not be included in the merge and may conflict with the
fast-forward distribution in Step 3.

Respond with: proceed / commit and proceed / halt
To pause this protocol, respond "pause".
Do not direct other tasks until this protocol completes or is paused.
```

- **proceed:** Continue without committing. MD accepts that
  uncommitted changes are excluded from the SIE.
- **commit and proceed:** For each worktree with uncommitted
  changes, stage all changes (modified and new) and commit:
  ```
  git -C [worktree-path] add -A
  git -C [worktree-path] commit -m "Pre-SIE commit: [branch] [ISO8601 timestamp]"
  ```
  `.gitignore` governs what is excluded from staging.
  ```
  [aras-sie: Step 1b — Committed]

  Committed on:
  - [branch]: [short summary of files]
  ```
  Then proceed to the next step.
- **halt:** Stop so the MD can handle uncommitted changes
  manually before re-invoking.

If `ordered` argument present:

```
[aras-sie: Step 1 — Specify merge order]

Active subsystems: [list of branches]
Specify merge order (branch names, comma-separated):

Respond with: [ordered list]
To pause this protocol, respond "pause".
Do not direct other tasks until this protocol completes or is paused.
```

Otherwise: proceed in alphabetical order by branch name.

### 2. Merge all branches → main

Operating from the main worktree. For each branch in order:

```
git merge [branch] --no-ff -m "SIE: [branch] → main [ISO8601 timestamp]"
```

If the merge completes without conflicts: proceed to the next branch.

If conflicts are detected (git reports conflict markers):

1. Run `git diff --name-only --diff-filter=U` to identify
   conflicting files.

2. For each conflicting file, search the active entries (entries
   above the `## Archived` section, or all entries if no archive
   section exists) of every surface's `shared-scope-intents.md`
   for entries matching that file path.

3. Output intent-informed conflict analysis:

```
[aras-sie: Step 2 — Conflict resolving [branch]]

Conflicting files:
- [file path]

Intent context:
  [branch A]: [intent statement for this file, or "No intent recorded"]
  [branch B]: [intent statement for this file, or "No intent recorded"]

Recommendation: [analysis based on intents — which change should
take precedence, how to combine them, or flag if intents contradict]

The VS Code Merge Editor is now active. Resolve all conflicts
using the above context, then stage the resolved files.

Respond with: resolved
To pause this protocol, respond "pause".
Do not direct other tasks until this protocol completes or is paused.
```

4. On `resolved`:
   ```
   git add -A
   git commit -m "SIE: [branch] → main [ISO8601 timestamp]"
   ```

After all branches merged: `git push origin main`.

### 3. Merge main → all branches

For each subsystem branch, using its worktree path:

```
git -C [worktree-path] merge main --ff-only
```

If `--ff-only` fails on any branch: hard stop — unexpected
non-fast-forward state. Inspect git log manually before retrying.

After all branches updated, batch push:

```
git push origin [branch-1] [branch-2] [branch-3] ...
```

### 4. Archive shared scope intents

For each subsystem branch, read its surface's
`.claude/.aras/[branch]-surface/shared-scope-intents.md`.

If the file has active entries (content above the `## Archived`
section, or any entries if no archive section exists yet):

- Move all active entries under a new dated archive subsection.
  If an `## Archived` section already exists, prepend the new
  subsection immediately after the `## Archived` header (most
  recent first). If no `## Archived` section exists, append it.

  ```markdown
  ## Archived

  ### SIE [ISO8601 timestamp]

  [entries that were active at this SIE]
  ```

- Clear the active area: retain only the instance identifier and
  branch assignment header lines at the top of the file.

If the file has no active entries: skip.

### 5. Update ARAS.md

ARAS.md is a `.claude/` file covered by `.gitignore`. Update it
on disk only — do not stage or commit it. Never use `git add -f`
on gitignored files.

Add or update the `Last SIE` field in the Status section:

```
**Last SIE:** [ISO8601 timestamp]
```

### 6. Report

```
[aras-sie: COMPLETE]

Merge order: [branch list in order used]
Conflicts resolved: [list of files and source branches, or None]
Shared scope intents archived: [list of branches with entries archived, or None]
Last SIE recorded: [timestamp]
MIS state: [N] active subsystems, all synchronized with main
```

## Resume Handling

SIE has no resume path. If interrupted mid-run, inspect git state
manually (git log, git status, git worktree list) and re-invoke
/aras-sync. The protocol is designed to complete in a single
synchronous run.

## Anti-Patterns

- **Don't** use `git add -f` on gitignored files — `.claude/`
  is gitignored by design. If `git add` fails on a `.claude/`
  file, that's `.gitignore` working correctly. Update on disk
  only; never force-track gitignored files.
