# Close ARAS

## Purpose

Dissolve the ARAS MIS back into a Single-Instance System after
the final PR has been merged. Assumes aras-sync was completed
prior to the PR merge.

## Compliance Responsibility

MIS dissolution — no surfaces remain after completion. No
compliance is applicable or meaningful.

**Does not accept responsibility for:**
- Level 1 on the surviving branch: the surviving branch's central
  artifact compliance carries forward from its last session-event PASS;
  CLOSE does not modify its exclusive scope or restricted paths

## Procedure

All steps write progress to the ARAS.md Protocol Lock step log
per the record-before-act principle: write `in-progress` before
acting, update to `complete` after. ARAS.md exists and is
writable through steps 1–5. Step 6 deletes ARAS.md as the
absolute final action.

### 1. Remove IM surface directories

Record step 1 `in-progress` in ARAS.md step log.

Delete each `[branch]-surface/` directory from `.claude/.aras/`.
After this step, only ARAS.md and DOCUMENTATION_STANDARDS.md
remain in `.claude/.aras/`.

Record step 1 complete in ARAS.md step log.

### 2. Remove IM documentation standards

Record step 2 `in-progress` in ARAS.md step log.

Delete `.claude/.aras/DOCUMENTATION_STANDARDS.md`. After this
step, only ARAS.md remains in `.claude/.aras/`.

Record step 2 complete in ARAS.md step log.

### 3. Backup

Run the backup procedure per `.claude/references/backup-procedure.md`.
If backup fails, report to managing developer and halt.

### 4. Remove directory junctions

Record step 4 `in-progress` in ARAS.md step log.

**SAFETY: Directory junctions MUST be removed before worktrees.**
On Windows, `git worktree remove` follows directory junctions and
deletes the target directory's contents. If `.claude/` or
`node_modules` is junctioned from a secondary worktree to the
main worktree, removing the worktree first will destroy the main
worktree's `.claude/` or `node_modules` directory.

For each non-main worktree that still exists:

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

Record step 4 complete in ARAS.md step log.

### 5. Remove worktree(s)

Record step 5 `in-progress` in ARAS.md step log.

Present a final confirmation before removal:

```
[aras-close: close-aras Step 5 — Remove worktrees]

About to remove worktree(s):
- [worktree path] ([branch])

Directory junctions verified removed in Step 4.
Respond with: proceed / halt
```

If confirmed, `git worktree remove ../[branch-name]` for each
non-main worktree that still exists.

Record step 5 complete in ARAS.md step log.

### 6. Verify clean state and dissolve

Verify all ARAS artifacts except ARAS.md itself are absent:

- No surface directories in `.claude/.aras/`
- No `.claude/` or `node_modules` directory junctions at former
  worktree paths
- No `DOCUMENTATION_STANDARDS.md` in `.claude/.aras/`

Then delete ARAS.md. Then delete the empty `.claude/.aras/`
directory. These are the absolute final actions — nothing is
recorded after this because ARAS.md no longer exists.
