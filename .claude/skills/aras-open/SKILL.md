# aras-open

## Trigger

Managing developer requests a new parallel workstream.

## Arguments

Optional arguments passed when invoking the skill:

- **count** (optional integer): Number of new subsystems to provision. If provided, Step 2 generates exactly this many subsystem sections in pending-origin.md instead of copying the two-section default template.
- **branch-prefix** (optional string): If provided alongside count, pre-populates each new subsystem section's branch name field as `[branch-prefix]-[N]` and instance identifier as the final path segment plus index. Example: `/aras-open 3 nhaffner/subsystem` generates branch names `nhaffner/subsystem-1`, `nhaffner/subsystem-2`, `nhaffner/subsystem-3` with identifiers `subsystem-1`, `subsystem-2`, `subsystem-3`.

If no arguments are provided, Step 2 proceeds with the default two-section template unchanged.

## Resume Handling

If ARAS.md exists with Protocol Lock = ARAS-OPEN:

1. Read the step log from ARAS.md Protocol Lock
2. Output: "[aras-open: RESUMING from after Step N]"
3. For steps 5–10 in the step log:
   - `complete` in log → skip
   - `in-progress` in log → verify (check filesystem), then execute or mark complete
   - absent from log → execute from this step
4. If all logged steps are complete, proceed from Step 11

## Compliance Responsibility

**First open:** ARAS-OPEN creates the MIS and authors all initial surfaces.
All surfaces are produced by this protocol; ARAS-OPEN accepts responsibility
for their initial well-formedness and mutual consistency.

**Subsequent open:** ARAS-OPEN accepts responsibility for new subsystems it
creates and the scope impact of adding them. Existing surfaces maintained
compliance through session-event compliance — ARAS-OPEN cannot accept
responsibility for violations it did not introduce.

**Accepts responsibility for:**
- All new surfaces are well-formed (verified at Step 12: L2, all surfaces)
- New subsystems' scope declarations do not conflict with existing surfaces (verified at Step 12: L3)
- ARAS.md correctly reflects all new subsystems

**Does not accept responsibility for:**
- Pre-existing compliance state of existing surfaces
- Pre-existing cross-surface inconsistencies between existing surfaces

## Protocol

### 1. Assess current state

Check `.claude/.aras/ARAS.md` for Protocol Lock state:

- If ARAS.md exists with Lock = ARAS-OPEN → resume path (see Resume Handling)
- If ARAS.md exists with Lock = [other] → hard stop:

```
[aras-open: BLOCKED]

An ARAS protocol is already in progress: [protocol name] ([path], step [N] [status]).
Complete or resolve the in-progress protocol before invoking
a new one.
```

- If ARAS.md exists with Lock = None → MIS active (subsequent open).
  Run `git branch --show-current`. If current branch ≠ Source Branch
  from ARAS.md, hard stop:

```
[aras-open: BLOCKED — Wrong worktree]

aras-open must be run from the main worktree ([source branch]).
Switch to the main worktree and re-invoke.
```

- If ARAS.md absent → SIS (first open). Proceed.

### 2. Origination

Create `.claude/.aras/` if it does not exist.

Check whether `.claude/.aras/pending-origin.md` already exists
(left behind by a previous halted invocation). If it does:

```
[aras-open: Step 2 — Existing origination detected]

A pending-origin.md from a previous invocation exists.

Respond with: reuse / discard
```

- `reuse`: Skip origination, proceed to Step 3 with the
  existing file.
- `discard`: Overwrite with a fresh template and proceed
  with normal origination below.

If no existing file, or if `discard`:

Build the pending-origin.md content:

- **If `count` argument provided:** Generate exactly `count` subsystem sections
  using the section template from `references/pending-origin-template.md`.
  Number sections sequentially starting from 1. Label existing subsystems
  "(Existing Branch)" and new subsystems "(New Branch)" based on whether a
  surface directory already exists for them.
  - **If `branch-prefix` also provided:** Pre-populate each new subsystem
    section's branch name field as `[branch-prefix]-[N]` and instance
    identifier as `[final-path-segment]-[N]` (derived from the last `/`-
    separated component of the prefix). Leave all other fields blank for the
    MD to complete.
  - **If no `branch-prefix`:** Generate the correct number of sections with
    all fields blank.
- **If no `count` argument:** Copy `references/pending-origin-template.md`
  as-is (two sections).

If subsequent open: pre-populate existing subsystem sections with
current branch names and scope from their ARA.md files regardless of
whether `count` was provided.

Write the resulting content to `.claude/.aras/pending-origin.md`.
Open `.claude/.aras/pending-origin.md` in `$EDITOR`.
Wait for the managing developer to complete and save.

### 3. Parse, validate, and determine open type

Read completed `pending-origin.md`. Validate that all required
fields are populated for every subsystem section. If any required
field is empty, report to managing developer and halt.

Extract for each new subsystem: branch name, instance identifier,
exclusive scope, shared scope, and restricted paths.

Determine open type by checking `.claude/.aras/` for existing
`[branch]-surface/` directories:
- No surface directories exist → **first open**
- One or more surface directories exist → **subsequent open**

### 4. Acquire lock

Write Protocol Lock: ARAS-OPEN, Acquired: [ISO8601 timestamp],
Invoked From: [current branch], and empty step log to ARAS.md.

If first open (ARAS.md absent): create ARAS.md now with Status: Active,
MIS Instantiation Date: [timestamp], Source Branch: [current branch],
empty Active Subsystems table, and the Protocol Lock section.

### 5. Assess scope impact

Record step 5 `in-progress` in ARAS.md step log.

**No-op if first open (no existing surfaces).**

Read all existing surfaces' ARA.md files. Determine whether any new
subsystem's scope requires changes to existing subsystems:

- Does any existing subsystem's exclusive scope need to narrow?
- Does shared scope need to be added or modified?
- Do restricted paths need updating?

If existing scopes change, this is a D(X) modification — all existing
surfaces are invalidated and must be verified at their next session event.

Record step 5 complete in ARAS.md step log.

### 6. Provision each new subsystem

Record step 6 `in-progress` in ARAS.md step log.

Follow `references/provision-worktree.md` in full for each new subsystem.
Repeat for every new subsystem declared in origination.

Record step 6 complete in ARAS.md step log.

### 7. Verify new subsystems

Record step 7 `in-progress` in ARAS.md step log.

Confirm provisioning succeeded for each new subsystem:

- Worktree path exists and is accessible
- `.claude/` junction resolves (`.claude/.aras/ARAS.md` is readable from
  the new worktree path)
- Surface directory exists with all four required files (ARA.md,
  surface-state.md, origin.md, shared-scope-intents.md)

If any check fails, report to managing developer and halt.

Record step 7 complete in ARAS.md step log.

### 8. Update existing surfaces

Record step 8 `in-progress` in ARAS.md step log.

**No-op if first open or if no scope changes identified in Step 5.**

For any existing subsystem whose scope was narrowed or shared scope was added:

- Update their `ARA.md` files in the interactions module
- Append timestamped origination entry to their `origin.md`

Record step 8 complete in ARAS.md step log.

### 9. Update ARAS.md

Record step 9 `in-progress` in ARAS.md step log.

Add all new subsystems to the Active Subsystems table: instance identifiers,
branch assignments, status (Active), and compliance dates (initial: None).

**First open only:** Add `## MIS Configuration` section using the venv path
confirmed during Step 6 provisioning:

```markdown
## MIS Configuration

**Node dependencies:** `node_modules` in each subsystem worktree is
a junction pointing to the main worktree. Dependency changes (install,
update, remove) must be made on main and distributed via /aras-sync.
Subsystem branches treat `node_modules` as read-only.

**Python dependencies:** Run backend commands using the main worktree's
venv. Activate `[main-worktree-venv-path]` before running `manage.py`
or other Python commands from any subsystem worktree. Dependency changes
must be made on main and distributed via /aras-sync.
```

Replace `[main-worktree-venv-path]` with the actual path identified during
Step 6 provisioning. If the project has no Python backend, omit the Python
dependencies entry.

Record step 9 complete in ARAS.md step log.

### 10. Open workspaces

Open each new worktree in a new VS Code window. Clear the `CLAUDECODE`
environment variable to prevent the new window from inheriting the current
session's extension state:

```
powershell -Command "$env:CLAUDECODE = $null; code '[new-branch-absolute-path]'"
```

This spawns a child process with a cleaned environment. The parent shell
(and current Claude Code session) is unaffected — environment changes in
child processes do not propagate upward.

### 11. Clean up

Remove `.claude/.aras/pending-origin.md`.

### 12. Verify

Run compliance event per `.claude/references/aras-compliance/compliance-event-protocols.md`
with context `aras-open`.

Levels: 2, 3.
Scope: all surfaces.

### 13. Report

Release Protocol Lock: clear the Protocol Lock section from ARAS.md (set Lock to None, remove Parameters and Step Log). ARAS.md persists with Status: Active.

Output to managing developer:

- MIS state (newly created or extended)
- Active subsystems with scope summaries
- Compliance status
