# ARAS Handbook

**Role:** Quick reference for the ARAS skill suite. Covers skill inventory, MIS lifecycle, session entry sequence, compliance quick reference, subsystem creation criteria, actor allocation models, and branch opening philosophy.
**Content:** Operational reference — what each skill does, when it runs compliance, how branches and actors relate, and how to structure parallel work.
**Constraints:**

- This is a quick reference, not a specification. Authoritative protocol details live in each skill's SKILL.md and reference files.
- Do not replicate compliance level definitions here — see `aras-compliance/` for authoritative level files.
- Update when skills are added, removed, or renamed.

---

## Skill Inventory

| Skill | Trigger | Purpose | Compliance |
|---|---|---|---|
| `/aras-open` | Open new subsystem(s) | Provision worktree, surface directory, and ARA.md for one or more new branches | L2 (all surfaces) + L3 at Step 12 |
| `/aras-close` | Close a subsystem after PR merge, or dissolve MIS | Remove surface, directory junctions, and worktree (close-branch); or dissolve all surfaces and ARAS.md (close-aras) | None |
| `/aras-sync` | Synchronized Integration Event | Merge all subsystem branches into main; distribute integrated code back to each subsystem | None |
| `/aras-reallocate` | Reallocate task or scope on a subsystem branch | Update ARA.md Current Task (task-only) or scope declarations (scope change) | None (task-only); L2(1–4) + L3 (scope change) |
| `/aras-audit` | Manual compliance audit requested | Full L1 + L2 + L3 sweep across the MIS; or IM-only (L2 + L3) | L1 + L2 + L3 (full); L2 + L3 (IM-only) |

---

## MIS Lifecycle Sequence

```
SIS (no ARAS)
    │
    ▼  /aras-open (first open)
    │  Creates: ARAS.md, DOCUMENTATION_STANDARDS.md, first surface directory
    │  Provisions: worktree, .claude/ junction, node_modules junction(s)
    │  Writes: MIS Configuration section in ARAS.md
    │  Compliance: L2 (all surfaces) + L3 at Step 12
    │
    ▼  Active MIS
    │  Session-event compliance at each cpm-start / cpm-resume
    │  (L1 + L2(1–4) on current branch; 8-hour recency gate)
    │
    ├──▶  /aras-open (subsequent): add more subsystems → L2 + L3 at Step 12
    │
    ├──▶  /aras-sync: periodic integration → no compliance
    │
    ├──▶  /aras-reallocate (task-only): update task → no compliance
    │     /aras-reallocate (scope change): update scope → L2(1–4) + L3
    │
    ├──▶  /aras-close (close-branch): remove one subsystem → no compliance
    │     MIS continues with remaining subsystems
    │
    ▼  /aras-close (close-aras): dissolve MIS → no compliance
       Removes: all surface directories, DOCUMENTATION_STANDARDS.md,
                directory junctions, worktrees, ARAS.md, .aras/
SIS restored
```

---

## Session Entry Sequence

Applies at every `cpm-start` and `cpm-resume` on a subsystem branch.

1. **Detect ARAS** — check for `.claude/.aras/ARAS.md`. If absent, skip all ARAS steps.
2. **Protocol Lock check** — if Lock ≠ None, hard stop. Non-protocol work is blocked until the protocol completes.
3. **Identify current subsystem** — match current branch against ARAS.md Active Subsystems. If not found, report and halt (wrong branch).
4. **Pending Merge check** — if subsystem status is Pending Merge (any variant), surface informational notice. Not a blocker.
5. **In-progress compliance check** — if surface-state.md records an in-progress compliance event, resume it. Skip to pass after completion.
6. **Recency gate** — if any PASS exists within the MIS within the last 8 hours, skip compliance checks and proceed directly to pass.
7. **Run compliance** — L1 + L2(1–4) on current branch only.
8. **On pass** — output `[ARAS Compliance: PASS]`, continue with session skill.
9. **On fail** — hard stop. No work proceeds until compliance is restored.

---

## Compliance Quick Reference

| Level | Name | What it checks | Scope | When it runs |
|---|---|---|---|---|
| **L1** | Central Artifact Consistency | Branch work vs ARA.md declarations: exclusive scope integrity, restricted path acknowledgment, shared scope intents for modified files | Current branch only | session-event; aras-audit (full) |
| **L2** | Surface Assertions | Per-file schema assertions on surface files. Steps 1–4: ARA.md, surface-state.md, shared-scope-intents.md per surface. Steps 5–6: ARAS.md and DOCUMENTATION_STANDARDS.md (module-wide, all-surfaces scope only) | Per-surface (Steps 1–4) or all surfaces (Steps 5–6) | session-event Steps 1–4; aras-open Step 12 (all); aras-reallocate scope change (Steps 1–4); aras-audit |
| **L3** | Cross-Surface Consistency | Exclusive scope mutual exclusion (no overlap), shared scope symmetry (all participants agree), restricted path consistency across all surfaces, ARAS.md registry accuracy | Always all surfaces | aras-open Step 12; aras-reallocate scope change; aras-audit |

### Compliance Matrix

| Protocol | Event | Compliance | Rationale |
|---|---|---|---|
| session-event | Session open | L1 + L2(1–4), current branch; 8-hr recency gate | Per-surface freshness at point of use |
| aras-sync | Post-merge | None | Code sync; no scope declarations modified |
| aras-reallocate | Task only | None | No structural change |
| aras-reallocate | Scope change | L2(1–4) + L3 | Updated ARA.md well-formedness + cross-surface conflict check |
| aras-open Step 7 | Provisioning verification | None | Filesystem verification only; full compliance runs at Step 12 |
| aras-open Step 12 | After all provisioning | L2 (all surfaces) + L3 | Module-wide file well-formedness + full cross-surface sweep |
| aras-close | close-branch or close-aras | None | Close procedure owns structural cleanup; /aras-audit is the fallback |

---

## Branch Opening and Actor Allocation

### Branch opening is arbitrary

Opening a branch creates a container: a worktree, a surface directory, and an ARA.md that declares what the branch is doing. The branch name and the task it holds are independent. Nothing about opening a branch determines which actor works on it, which strategy governs task assignment, or how long it stays active. All of that is a managing developer decision made after the branch exists.

The practical consequence: **the decision to open branches can be decoupled from the decision about how to use them.** You can open branches to match compute capacity, then allocate tasks and actors to those branches dynamically via reallocation. Branch naming can reflect the resource slot rather than the task.

### Actor model

ARAS compliance operates per-branch, not per-actor. The protocol tracks the branch; it has no concept of which actor is present on it. This means:

- **Multiple actors on one branch are supported.** The compliance model is unchanged — session-event compliance runs at entry regardless of which actor enters. The 8-hour recency gate applies: if one actor just passed compliance on this branch, the next actor entering within the window skips the check.
- **Multi-actor on one branch is rare and intentional.** When suitable, it is assumed the MD has scoped the task cleanly enough that two actors can work in well-defined sections simultaneously without git conflict. The MD owns actor coordination — ARAS does not model it.
- **Actor identity is not tracked by ARAS.** If you name actors by session ID for a given session's assignment, that naming is an operational convenience, not a persistent ARAS construct. From ARAS's perspective, the next session entering the same branch is the same actor.

### Workstream division strategies

How the MD chooses to divide work across branches is a management decision, not an ARAS constraint. Three coherent approaches:

**Task-based:** Each branch is opened for a specific task and closed when that task's PR merges. Branch lifecycle = task lifecycle. Appropriate when tasks are long-running with stable, clearly bounded scope.

**Scope-based (architectural):** Branches mirror durable architectural divisions (frontend, backend, infra). Tasks rotate through branches via reallocation. Branches are long-lived. Appropriate when parallel actors work across stable architectural domains for sustained periods. The simplified reallocation in the current protocol design makes this approach meaningfully viable.

**Workstream-based:** Branches represent coherent sequences of related tasks sharing a product purpose, not a single task or a permanent architectural area. Tasks rotate within the workstream. Branches live as long as the workstream. A middle ground between task-based and scope-based — appropriate when parallelism maps to product workstreams rather than code architecture.

**Compute-pool (resource-based):** Branches are opened to match available compute capacity. Branch names reflect the resource slot (e.g., worktree-1, worktree-2, worktree-3) rather than the task. Workstream division is determined by the MD at task assignment time and adjusted via reallocation as work progresses. This model makes the arbitrary nature of branch opening explicit, and matches well with AI actors whose identity is session-scoped, not persistent.

### When to open branches

Open branches when you have work that benefits from parallel execution and enough workstreams to occupy them productively. The ceiling is set by the project's parallel workstream capacity — how many genuinely independent streams of work exist at a given time — not by compute availability alone. Opening more branches than the project can saturate adds surface maintenance and compliance overhead without coordination benefit.

The right number of branches is: as many as the project's parallel workstream structure can sustain, up to compute capacity. When a workstream completes, reallocate the branch to the next one rather than closing and re-opening.

---

## Subsystem Creation Criteria

### When to open branches / a MIS

Open a MIS (via `/aras-open`) when:

1. **Parallelism is real** — multiple workstreams exist that can genuinely execute simultaneously
2. **Exclusive scope is achievable** — workstreams can be scoped such that their changes are largely non-overlapping (shared scope intents handle incidental overlap)
3. **Overhead is justified** — Protocol Lock contention, compliance at open, surface maintenance, and junction management are worth the coordination benefit

### When NOT to open a MIS

- Single actor working sequentially — ARAS adds coordination overhead with no coordination benefit
- All work is in one domain with no parallel capacity — standalone CPM handles this cleanly
- The project is bounded and short enough that open + close overhead exceeds the parallelism benefit

### Rule of thumb

> Branches are cheap to open. The overhead is surface maintenance and compliance, not the worktree itself. Open as many branches as the project can saturate, allocate compute to fill them, and reallocate as tasks complete.
