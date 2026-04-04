# Provision Worktree

## Purpose

Shared procedure for creating and provisioning a new ARAS subsystem
worktree. Used by both open-aras and open-branch.

## Procedure

### 1. Create worktree and branch

```
git worktree add ../[new-branch-name] -b [new-branch-name] [source-branch]
git push -u origin [new-branch-name]
```

### 2. Link .claude/

Create a directory junction so the new worktree shares the main
worktree's `.claude/` directory:

```
powershell -Command "New-Item -ItemType Junction -Path '[new-branch-absolute-path]\.claude' -Value '[main-worktree-absolute-path]\.claude'"
```

Use PowerShell `New-Item -ItemType Junction` — not `cmd mklink /D`,
which creates a symbolic link requiring elevation. PowerShell junctions
do not require elevated privileges or Developer Mode and handle spaces
in paths reliably from Git Bash.

Verify link: confirm `.claude/.aras/ARAS.md` is readable from the new
worktree path. If verification fails, report to managing developer and
halt.

### 3. Provision runtime files

**Environment files:** Copy `.env*` files from the main worktree,
preserving directory structure.

**Node dependencies:** Symlink `node_modules` from the main worktree
rather than running an install:

```
powershell -Command "New-Item -ItemType Junction -Path '[new-branch-absolute-path]\[subdir]\node_modules' -Value '[main-worktree-absolute-path]\[subdir]\node_modules'"
```

Repeat for each directory that contains a `package.json`. The new
worktree inherits the main worktree's installed packages at zero cost.

**Dependency constraint:** Because `node_modules` is shared via
junction, dependency changes (installs, updates, removals) must be
made on the main branch and distributed to all subsystems via
`/aras-sync`. Subsystem branches treat `node_modules` as read-only.
Include this constraint in the open report so the managing developer
is aware.

**Python dependencies:** Identify the main worktree's venv path (e.g.,
`[main-worktree]/python/.venv` or wherever the project venv lives).
No provisioning action required — the new worktree runs backend
commands by activating the main worktree's venv directly. Record the
venv path for the `## MIS Configuration` section written in the
calling protocol's ARAS.md update step.

**Build artifacts:** Do not copy. These regenerate on first build
(e.g., `.next/`, `cdk.out/`, `build/`, `__pycache__/`).

### 4. Create surface files

In the interactions module, create `[new-branch]-surface/`:

- `ARA.md` — instance identifier, branch assignment, subsystem
  interaction declarations, exclusive scope, shared scope, restricted
  paths (from origination entry; shared scope must match all named
  participating surfaces)
- `surface-state.md` — instance identifier, branch assignment,
  current state: Active, last compliance event: None
- `origin.md` — timestamped origination entry
- `shared-scope-intents.md` — instance identifier and branch
  assignment header; no entries until first shared scope modification
