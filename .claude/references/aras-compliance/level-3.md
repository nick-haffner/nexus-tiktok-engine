# Level 3: Cross-Surface Consistency

## Purpose

Verify that surfaces are consistent with each other across the
interactions module. This check answers: do the subsystems'
declarations agree where they must agree?

## Scope Parameter

- **All surfaces:** Always runs across all active surfaces.
  Cannot be scoped to a single branch — cross-surface
  consistency is inherently multi-surface.

## Procedure

### 1. Load all surface ARA.md files

Read every `.claude/.aras/[branch]-surface/ARA.md` for all
active subsystems listed in ARAS.md.

### 2. Verify exclusive scope mutual exclusion

For each pair of surfaces:

- No path or domain appears in both surfaces' exclusive scope
  declarations unless explicitly categorized as shared

### 3. Verify shared scope consistency

For each shared scope declaration on any surface:

- Every named participating subsystem's surface declares the
  same shared scope
- Shared scope boundaries match across all participating
  surfaces

### 4. Verify restricted path consistency

For each surface:

- Hard-frozen paths are identical across all surfaces
- Soft-frozen paths are identical across all surfaces

### 5. Verify ARAS.md reflects actual state

- Every surface directory in `.claude/.aras/` has a
  corresponding entry in ARAS.md active subsystems
- Every entry in ARAS.md active subsystems has a corresponding
  surface directory
- No orphaned surfaces or phantom entries

## On Failure

Report each inconsistency with:

- The surfaces involved
- The assertion that failed
- What each surface declares vs what was expected

Return pass/fail to the orchestrator.
