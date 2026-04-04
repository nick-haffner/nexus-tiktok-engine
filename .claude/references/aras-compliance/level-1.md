# Level 1: Central Artifact Consistency

## Purpose

Verify that the branch's actual content state is consistent
with what the surface's ARA.md declares. This check answers:
is the CPM Subsystem's central artifact reflecting what the
surface says it should be?

## Scope Parameter

- **Single branch:** Check one branch against its surface.
- **All surfaces:** Check every active branch against its surface.

## Procedure

### 0. Compliance cache check

Before running steps 1–4, check whether the last Level 1 result for
this branch is still current:

1. Read `.claude/.aras/[branch]-surface/surface-state.md`. Extract
   the last compliance event result and timestamp T.
2. If the last result is FAIL → proceed to Step 1 (cache invalid).
3. If the last result is PASS at timestamp T → run:
   `git log [branch] --since="[T]" --oneline`
4. If the git log returns no commits → return PASS without running
   Steps 1–4. Level 1 compliance carries forward.
5. If the git log returns commits → proceed to Step 1.

This cache is valid because Level 1 violations can only be introduced
by commits to the branch (restricted path modifications, shared scope
changes without intent entries, or cross-branch exclusive scope writes
which are themselves protocol violations). No commits since the last
PASS means no violation can have been introduced.

### 1. Read the branch's ARA.md

Load `.claude/.aras/[branch]-surface/ARA.md`.
Extract exclusive scope, shared scope, and restricted paths.

### 2. Verify exclusive scope

For each path or domain declared as exclusive scope:

- The path exists in the branch's working tree
- Changes to files within this scope since MIS instantiation (or since the last origination entry) were made by this branch only

### 3. Verify restricted paths

For each hard-frozen path:

- The file is unmodified compared to the source branch at MIS instantiation

For each soft-frozen path:

- The file is unmodified compared to the source branch at MIS instantiation
- OR a D(X) modification entry exists in ARAS.md acknowledging the change

### 4. Verify shared scope

For each path or domain declared as shared scope:

- The path exists in the branch's working tree
- The ARA.md acknowledges that content conflicts may exist and will be resolved at merge

For each file within shared scope that has been modified on this branch since MIS instantiation (or since the last origination entry):

- An entry exists in `shared-scope-intents.md` for that file

## On Failure

Report each violation with:

- The file path
- The declared scope category (exclusive, shared, restricted,
  out-of-scope)
- What was expected vs what was found

Return pass/fail to the orchestrator.
