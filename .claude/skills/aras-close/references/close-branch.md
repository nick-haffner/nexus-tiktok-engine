# Close Branch

## Purpose

Remove a single CPM Subsystem from an active ARAS MIS after
its PR has been merged. The MIS continues with remaining
subsystems. Called by aras-close after Protocol Lock acquisition.

## Compliance Responsibility

The procedure owns structural cleanup. Step 1 is explicitly
responsible for removing all shared scope declarations on remaining
surfaces that reference the closing branch — unconditionally, before
any scope redistribution. If Step 1 executes correctly, no L3
violation persists after closure. Compliance is not run — residual
inconsistency indicates procedural failure, detectable via
/aras-audit.

**Does not accept responsibility for:**
- Pre-existing compliance state of remaining surfaces
- Pre-existing cross-surface inconsistencies introduced before
  this protocol

## Procedure

All steps write progress to the ARAS.md Protocol Lock step log
per the record-before-act principle: write `in-progress` before
acting, update to `complete` after.

### 1. Update remaining surfaces

Record step 1 `in-progress` in ARAS.md step log.

For each remaining subsystem's ARA.md:

**Shared scope cleanup (unconditional):** Remove any shared scope
declarations that name the closing branch. If a shared scope entry
lists the closing branch as a participant, remove it entirely or
update it to reflect only the continuing participants.

**Scope redistribution (if applicable):** If the closing subsystem's
exclusive scope is being absorbed by remaining subsystems, update
their ARA.md with the expanded scope and append a timestamped
origination entry to their origin.md.

Record step 1 complete in ARAS.md step log.

### 2. Remove closed surface directory

Record step 2 `in-progress` in ARAS.md step log.

Delete `.claude/.aras/[closing-branch]-surface/`.

Record step 2 complete in ARAS.md step log.

### 3. Remove subsystem from ARAS.md

Record step 3 `in-progress` in ARAS.md step log.

Remove the closed subsystem from the Active Subsystems table in ARAS.md.

Record step 3 complete in ARAS.md step log.

### 4. Backup

Run the backup procedure per `.claude/references/backup-procedure.md`.
If backup fails, report to managing developer and halt.

### 5. Remove directory junctions

Record step 5 `in-progress` in ARAS.md step log.

**SAFETY: Directory junctions MUST be removed before worktrees.**
On Windows, `git worktree remove` follows directory junctions and
deletes the target directory's contents. If `.claude/` or
`node_modules` is junctioned from this worktree to the main
worktree, removing the worktree first will destroy the main
worktree's `.claude/` or `node_modules` directory.

1. Remove `node_modules` junctions — one per directory that
   contained a `package.json` during provisioning:
   - `cmd //c "rmdir [worktree-absolute-path]\\[subdir]\\node_modules"`
   - On Windows, `rmdir` on a junction removes the junction
     itself without affecting the target directory
   - Repeat for each subdirectory that had a `node_modules`
     junction created during aras-open provisioning
2. Remove the `.claude/` junction:
   - `cmd //c "rmdir [worktree-absolute-path]\\.claude"`
3. Verify both are gone: confirm neither
   `[worktree-path]/[subdir]/node_modules/` nor
   `[worktree-path]/.claude/` resolves. If either still
   resolves, hard stop — do not proceed to worktree removal.

Record step 5 complete in ARAS.md step log.

### 6. Remove worktree

Record step 6 `in-progress` in ARAS.md step log.

```
[aras-close: close-branch Step 6 — Remove worktree]

About to remove worktree:
- [worktree path] ([branch])

Directory junction verified removed in Step 5.
Respond with: proceed / halt
```

If confirmed, `git worktree remove ../[branch-name]`.

Record step 6 complete in ARAS.md step log.

### 7. Verify

Confirm close-branch actions are structurally complete:

- Closed surface directory no longer exists in `.claude/.aras/`
- ARAS.md Active Subsystems table no longer lists the closed subsystem
- No remaining surface's ARA.md declares shared scope referencing
  the closed branch
