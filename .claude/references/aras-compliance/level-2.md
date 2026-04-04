# Level 2: Surface Assertions

## Purpose

Verify that each surface's files pass their per-file YAML
assertion blocks from the IM schema. This check answers: does
each surface file contain what the schema says it must contain?

## Scope Parameter

- **Single branch:** Steps 1–4 only. Check one branch's surface files. Module-wide steps 5–6 do not run.
- **All surfaces:** All steps. Check every active surface's files, then run module-wide steps 5–6 once.

## Procedure

### 1. Load schema

Read `.claude/references/aras-im-schema.md`. Extract per-file
assertion blocks.

### 2. Run ARA.md assertions

Against the module surface `.claude/.aras/[branch]-surface/ARA.md`:

- File assertions (exists, expected path)
- Content assertions: aras_header, interaction_declarations,
  exclusive_scope, shared_scope, restricted_domain

### 3. Run surface-state.md assertions

Against the module surface `.claude/.aras/[branch]-surface/surface-state.md`:

- File assertions (exists, expected path)
- Content assertions: aras_header, state, compliance_history

### 4. Run shared-scope-intents.md assertions

Against `.claude/.aras/[branch]-surface/shared-scope-intents.md`:

- File assertions (exists, expected path)
- Content assertions per entry: routing (file path specified,
  file path within surface's shared scope), code_and_intent
  (code block present, intent statement present)

### 5. Run ARAS.md assertions (all surfaces scope only; once)

Against `.claude/.aras/ARAS.md`:

- File assertions (exists, expected path, not on any branch)
- Content assertions: aras_status, mis_metadata, active_subsystems
- Protocol Lock assertions (evaluated in prose per aras-im-schema.md):
  lock field is None, ARAS-OPEN, ARAS-MERGE, or ARAS-CLOSE;
  if lock is not None: acquired timestamp is present, invoked-from
  branch is present, path is a valid protocol path, and step log
  contains at least one entry

### 6. Run DOCUMENTATION_STANDARDS.md assertions (all surfaces scope only; once)

Against `.claude/.aras/DOCUMENTATION_STANDARDS.md`:

- File assertions (exists, expected path, not on any branch)
- Content assertions: mis_compliance, surface_replication,
  cross_surface_consistency, instantiation_dissolution,
  artifact_lifecycle

## On Failure

Report each assertion failure with:

- The file path
- The assertion group
- The specific assertion that failed
- What was expected vs what was found

Return pass/fail to the orchestrator.
