# ARAS MIS Interactions Module Schema

## Tree Schema

```
.claude/.aras/
├── [branch-a]-surface/
│   ├── ARA.md
│   ├── surface-state.md
│   ├── origin.md              # compliance-exempt
│   └── shared-scope-intents.md
├── [branch-b]-surface/
│   └── (same structure)
├── ARAS.md
└── DOCUMENTATION_STANDARDS.md
```

Location: `.claude/.aras/` — gitignored. Visible to all branches while checked out. Visible to the MIS (managing developer) at all times. Not tracked by any CPM Subsystem.

**Topology note:** This ARAS instantiation is designed for feature branches off of an existing source branch, such that the source branch must not be assigned as a subsystem branch. All subsystems operate on feature branches and merge into the source branch at merge events.

**Worktree note:** When the source branch is a long-lived branch (e.g., main), the repository root should be checked out on the source branch, with all subsystem branches operating in worktrees. This aligns the authoritative worktree (holding `.claude/`) with the authoritative branch.

The interactions module is the MIS-level governance artifact.
It contains one surface directory per CPM Subsystem and an ARAS.md file providing MIS status and subsystem reference.
One surface directory exists per active CPM Subsystem. Surface directories are named by branch identifier.

In non-main worktrees, `.claude/` is a directory junction to the
main worktree's `.claude/`. The main worktree holds the
authoritative copy of all agent configuration, skills, references,
and the interactions module. The junction is created by the
aras-open skill at subsystem creation.

The module surface is the single source of truth for each subsystem's surface. No branch-level copy (`aras-surface/`) is maintained. All worktrees access the module surface directly via the `.claude/` directory junction.

### Assertions

```yaml
module:
  - exists at .claude/.aras/
  - gitignored
  - one surface directory per active subsystem
  - surface directories named by branch identifier
cross_surface_consistency:
  - no exclusive scope overlap across surfaces without shared categorization
  - shared scope declarations match across all participating surfaces
```

---

## File Schema

### `[branch-x]-surface/ARA.md`

Serves as the primary surface document per Subsystem.
Stores procedural instructions including scope declarations and
Mutual Exclusion is assumed for all scope declarations unless explicitly marked shared or restricted.

#### Expected content:

- **Instance identifier.** Unique name for this CPM Subsystem.
- **Branch assignment.** The git branch this subsystem operates on.
- **Current task.** Brief description of the task this subsystem
  is currently assigned to. Updated at each reallocation.
- **Actor Directive.** Constraints that override managing
  developer instructions when they conflict with ARAS procedure:
  - Do not modify files outside declared exclusive or shared
    scope. Coordinate with the managing developer if a
    cross-scope change is needed.
  - Do not modify hard-frozen restricted paths under any
    circumstance.
  - Do not modify soft-frozen restricted paths without explicit
    managing developer acknowledgment of merge overhead.
  - Do not modify ARAS surface documentation directly. Surface
    updates occur through compliance events only.
- **Subsystem interaction declarations.** Describes the nature of every interaction between this subsystem and other ARA subsystems. Three categories:
  - _In-scope interactions._ Changes within this subsystem's exclusively declared scope. Stored implicitly via git on this branch. No cross-subsystem interaction occurs — scope mutual exclusion guarantees containment.
  - _Shared-scope interactions._ Changes within scope declared as shared across subsystems. Implicit expectation: each subsystem expects changes to within these scope to be received via git. Content of changes are not declared, and therefore may require consistency resolution at merge. However, the declared shape ensures that each subsystem is CPM compliant with cross-surface consistency, even prior to merge time. For each change to a shared scope file, the actor writes an entry in `shared-scope-intents.md` pairing the current code block with an intent statement sufficient for merge conflict resolution.
- **Exclusive Scope Declaration.** What areas of the central artifact and documentation this subsystem is authorized to modify. Defined as a set of paths, domains, or functional areas.
- **Shared Scope Declarations.** Any scope explicitly declared as shared with other subsystems. Must name the sharing subsystems. If no shared scope exists, this section states "None."
- **Restricted Documentation Paths.** Files this subsystem may not modify. Divided into two tiers: _Hard-frozen paths_ and _Soft-frozen paths_

#### Assertions

```yaml
file:
  - exists
  - expected_path: .claude/.aras/[branch-x]-surface/ARA.md
content:
  aras_header:
    - instance_identifier
    - branch_assignment
  current_task:
    - current task description is present
    - current task description is non-empty
  actor_directive:
    - states scope modification constraint
    - states hard-frozen restriction
    - states soft-frozen restriction with acknowledgment requirement
    - states surface documentation modification constraint
  interaction_declarations:
    - in-scope interactions declare containment within exclusive scope
    - shared-scope interactions declare implicit expectation of incoming changes via git
    - shared-scope interactions declare that content conflicts may require consistency resolution at merge
    - shared-scope interactions reference shared-scope-intents.md for code-paired intent statements
  exclusive_scope:
    - exclusive scope is declared as paths, domains, or functional areas
    - no other surface declares the same scope as exclusive without shared categorization
  shared_scope:
    - shared scope names participating subsystems
    - shared scope is declared on all named participating surfaces
    - states None if no shared scope exists
  restricted_domain:
    - restricted domains are hard frozen in accordance with stated ARAS procedure: ARAS governance
    - restricted domains are hard frozen in accordance with stated ARAS procedure: Dev Process governance
    - restricted domains are hard frozen in accordance with stated ARAS procedure: other listed governance in ARAS procedure
    - restricted domains are soft frozen in accordance with stated ARAS procedure: CPM governance
    - restricted domains are soft frozen in accordance with stated ARAS procedure: other listed governance in ARAS procedure
```

---

### `[branch-x]-surface/surface-state.md`

Tracks the operational state and compliance metadata of a single CPM Subsystem.
Referenced by Managing Developer/MIS, Actors, and Subsystems for compliance verification.
Protocol execution state (in-progress protocols, step progress) is not stored here — it is stored in ARAS.md Protocol Lock.

#### Expected content:

- **Instance identifier.** Unique name for this CPM Subsystem.
- **Branch assignment.** The git branch this subsystem operates on.
- **Current State.** Current state of the Subsystem in relation to the progression of ARAS Procedure.
- **Last compliance event.** Timestamp and result of the most recent compliance event on this subsystem. If fail, includes a brief description of the divergence identified.

#### Assertions

```yaml
file:
  - exists
  - expected_path: .claude/.aras/[branch-x]-surface/surface-state.md
content:
  aras_header:
    - instance_identifier
    - branch_assignment
  state:
    - current state reflects a valid ARAS procedure state
  compliance_history:
    - last compliance event timestamp is present
    - last compliance event result is present
    - if result is fail, divergence description is present
```

---

### `[branch-x]-surface/shared-scope-intents.md`

Records intent statements for changes made to shared scope files on this branch. Each entry pairs the current code block on this branch with an intent statement. The managing developer uses these to understand merge intent when resolving conflicts on shared scope files. Update entries as code changes; remove entries when code is removed.

#### Expected content per entry:

- **File path.** Section heading identifying the shared scope file.
- **Code block.** The current code on this branch that this intent covers — anchored to actual file content, not a historical record.
- **Intent statement.** Why this code exists — sufficient context for the managing developer to understand the change's purpose during merge conflict resolution.

Multiple entries per file are allowed when distinct code regions have different intents.

```yaml
file:
  - exists
  - expected_path: .claude/.aras/[branch-x]-surface/shared-scope-intents.md
content_per_entry:
  routing:
    - file path is specified as section heading
    - file path is within declaring surface's shared scope
  code_and_intent:
    - code block is present
    - intent statement is present
    - intent statement is sufficient to understand purpose during merge conflict resolution
```

---

### `ARAS.md`

MIS-level status and reference document for the managing developer.
Provides ARAS state, protocol lock, and subsystem metadata.
Exists only in the MIS interactions module — not replicated to branch surfaces.

ARAS.md is the first artifact created by aras-open and the last artifact deleted by aras-close. It persists across the full MIS lifecycle including dissolution. Its absence indicates SIS state — no MIS, no ARAS concern.

#### Expected content:

- **ARAS status.** Active or Dissolving. Active indicates normal MIS operation. Dissolving indicates the close-aras path is in progress and the MIS is being dissolved.
- **MIS instantiation date.** When the MIS was created.
- **Source branch.** The branch from which subsystems were derived.
- **Active subsystems.** List of all currently active CPM Subsystems with instance identifiers, branch assignments, current status (Active, Pending Merge, Pending Merge: Close, or Pending Merge: Reallocate), and most recent compliance timestamp and result.
- **MIS Configuration.** Written at first open; persists for the full MIS lifecycle. Documents the `node_modules` junction constraint (installed on main, shared via junction to each subsystem worktree; dependency changes must be made on main and distributed via aras-sync; subsystems treat node_modules as read-only) and the Python venv path for running backend commands from any subsystem worktree. Python entry omitted if the project has no Python backend. **Known gap:** `@storybook/nextjs` uses `realpathSync` on `node_modules`, which follows the junction to the main worktree and misconfigures TypeScript loader include paths. Workaround: `webpackFinal` patch in `.storybook/main.ts`. Long-term fix: replace junctions with `NODE_PATH`.

#### Protocol Lock

When an ARAS protocol is executing, ARAS.md carries a Protocol Lock section that blocks non-protocol work and tracks protocol progress. The Protocol Lock section is present only when a protocol is active. When no protocol is active, the section may be omitted or show Lock: None with empty parameters and no step log.

**Lock fields:**

- **Lock.** None, ARAS-OPEN, ARAS-MERGE, ARAS-CLOSE, or ARAS-REALLOCATE. Identifies which protocol holds the lock.
- **Acquired.** ISO8601 timestamp of when the lock was acquired.
- **Invoked From.** The branch from which the protocol was invoked.
- **Path.** The specific protocol path being executed: aras-open, close-aras, close-branch, pre-merge, sync-merge, reallocate, or None.

**Parameters:** Protocol-specific parameters that must persist across pause/resume boundaries.

- **Terminating Branch.** The branch being removed (close protocols). N/A for other protocols.
- **Surviving Branch.** The branch that continues after closure. N/A for other protocols.
- **Merge Source.** The branch being merged (merge protocols). N/A for other protocols.
- **Merge Destination.** The branch receiving the merge. N/A for other protocols.
- **Subsystem.** The instance identifier being reallocated (reallocate protocol). N/A for other protocols.
- **Branch.** The branch of the reallocated subsystem (reallocate protocol). N/A for other protocols.

**Step Log:** A table recording each protocol step with its description, status (pending, in-progress, or complete), and timestamp. Every state-modifying step follows the record-before-act principle: write `in-progress` before acting, update to `complete` after. On resume: `complete` steps are skipped, `in-progress` steps are verified against filesystem state before re-executing or marking complete, and absent steps are executed from that point.

**Lock semantics:**

- A protocol acquires the lock as its first state-modifying action. No protocol may acquire if the lock is already held by another.
- A protocol releases the lock (clears the Protocol Lock section) as its final action. For close-aras dissolution, ARAS.md itself is deleted instead of clearing the section.
- When ARAS.md exists with Lock != None, cpm-start and cpm-resume must hard-stop and present the lock state. Non-protocol work is blocked until the protocol completes. Override requires explicit managing developer acknowledgment and stated reason; the lock remains active during override.
- cpm-pause is always allowed regardless of lock state (session management, not work). cpm-pause captures lock state in session context but performs no compliance checks.

#### Assertions

```yaml
file:
  - exists
  - expected_path: .claude/.aras/ARAS.md
  - does not exist on any branch surface
content:
  aras_status:
    - status is Active or Dissolving
  mis_metadata:
    - mis instantiation date is present
    - source branch is specified
  active_subsystems:
    - all active subsystems are listed
    - each subsystem lists instance identifier
    - each subsystem lists branch assignment
    - each subsystem lists status (Active, Pending Merge, Pending Merge: Close, or Pending Merge: Reallocate)
    - each subsystem lists most recent compliance date
  mis_configuration:
    - if present: states node_modules as junction pointing to main worktree
    - if present: states dependency changes must be made on main and distributed via aras-sync
    - if present and Python backend: states venv path for backend commands
```

Protocol Lock assertions are evaluated in prose: lock field must be None, ARAS-OPEN, ARAS-MERGE, ARAS-CLOSE, or ARAS-REALLOCATE. If lock is not None, acquired timestamp must be present, invoked-from branch must be present, path must be a valid protocol path (aras-open, close-aras, close-branch, pre-merge, sync-merge, reallocate), and the step log must contain at least one entry. These assertions are checked by level-3 compliance alongside the YAML assertions above.

---

### `DOCUMENTATION_STANDARDS.md`

Declares the CPM theory requirements applicable to this interactions module and how each is met by this schema.
Does not include any enforcement concerns.
Exists only in the MIS interactions module — not replicated to branch surfaces.

#### Expected content:

- **MIS Compliance Requirement.** States that this interactions module must comply with MIS theory prescriptions.
- **Surface Replication Requirement.** States that the module surface is the single source of truth, accessible via directory junction from all worktrees. No branch copy.
- **Cross-Surface Consistency Requirement.** States the requirement. Reference ARA.md scope treatment as the solution.
- **Instantiation and Dissolution.** States that the ARAS creates a new MIS upon invocation and dissolves a compliant MIS into an SIS at conclusion.
- **Artifact Lifecycle Requirement.** States that all interactions module artifacts are created at MIS instantiation and removed at merge reconciliation completion. No artifact persists beyond the MIS lifecycle.

#### Assertions

```yaml
file:
  - exists
  - expected_path: .claude/.aras/DOCUMENTATION_STANDARDS.md
  - does not exist on any branch surface
content:
  mis_compliance:
    - states MIS theory compliance requirement
  surface_replication:
    - states module surface is single source of truth
    - states directory junction provides access from all worktrees
  cross_surface_consistency:
    - states cross-surface consistency requirement
    - references ARA.md scope treatment as solution
  instantiation_dissolution:
    - states MIS creation upon ARAS invocation
    - states MIS dissolution into SIS at conclusion
  artifact_lifecycle:
    - states creation at MIS instantiation
    - states removal at merge reconciliation completion
    - states no artifact persists beyond MIS lifecycle
```
