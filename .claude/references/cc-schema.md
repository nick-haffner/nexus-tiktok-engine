# Context Chain Schema

**Role:** Prescriptive specification of the CPM System Context Chain for the Nexus TikTok Engine CPM Instance. Defines the CCS structure, all CCS-visible files, expected CCS content per file, and assertions for mechanical compliance verification. Referenced by cpm-audit for CCS compliance checks.
**Content:** Axioms, valid declared inputs, root loading path with PSI assertion, CCS-visible file tree, and subsystem-organized file schemas (entry points, RCC declaration, additional procedures). Organized by declared subsystem; per-file sections include description, expected CCS content, and YAML assertions.
**Constraints:**

- Specifies CCS content only — loading state content (content loaded by the CCS like behavioral directives, project documentation, governance for other systems) is out of scope even when it co-resides in CCS-visible files.
- Assertions are mechanically verifiable. Prose-level compliance is verified by cpm-audit alongside YAML assertions.
- **Known incompleteness:** This schema specifies a structurally complete context chain that achieves PSI. No context model subsystem is declared. Loading state content (CPM governance, documentation standards, documentation maintenance procedures) is not yet loaded by the chain. Context model integration is required for CPM defense.

---

## Inheritance Axiom

Every node below a declared CCS subsystem node inherits all CCS properties from its nearest declared ancestor. Any repository node not listed in this schema is CCS compliant by virtue of this inheritance — it need not be explicitly documented here.

## Visibility Axiom

A node becomes visible to the CCS — and therefore appears in this schema — when it contains CCS content: an entry point, an RCC declaration, or an additional procedure that serves the context-loading aim. Visibility is determined by content, not location.

---

## Valid Declared Inputs

The following inputs are the complete and closed set of factors that legitimately determine what the context chain loads and which steps execute. No other factor — including time, actor count, session history, invocation method, or task content — may alter which steps execute or their sequence.

### Working Domain

The actor's working directory within the repository. Determines which CLAUDE.md files the RCC traverses and which subsystem entry points are encountered. Always present — an actor is always somewhere.

### Session-ID (optional)

When present, identifies a session context file for recovery and enables actor identity resolution. When absent, indicates a fresh session with no prior context to recover. Determines whether session context loading and actor identity resolution steps execute or are structurally omitted.

### Active Project Reference (optional)

When present, identifies which project cornerstone document(s) to load. When absent, no project context is loaded. Determines whether the project context loading step executes or is structurally omitted.

### Closure

These three inputs are exhaustive. Any proposed addition to this set constitutes a schema change requiring formal justification that the new input is necessary for the CCS's context-loading aim and that its omission conditions preserve PSI.

---

## Root Loading Path

The single ordered sequence against which all actual loading paths are verified. All actual paths for all valid input combinations are ordered subsequences of this sequence. No step is reordered, no step is inserted, no step not in this sequence is added. Steps are either executed or structurally omitted per their declared omission conditions.

### Step 1 — RCC Traversal

**Loads:** All CLAUDE.md files on the actor's path from repository root to working domain.
**Participating files:** All CLAUDE.md files declared in the Tree Schema.
**Omission:** Never omitted.
**Variation:** Working domain determines which CLAUDE.md files are on the path. This is selection within the step (which files the RCC encounters), not omission of the step itself.

### Step 2 — ARAS Pre-Traversal

**Loads:** ARAS governance (.claude/.aras/ARAS.md and current branch ARA.md).
**Participating files:** Extra-schema. ARAS files are governed by ARAS's own system; they are loaded here per a known-gap patch.
**Omission:** Omitted when .claude/.aras/ARAS.md does not exist.
**Note:** This step's placement inside the CPM SCC is a known architectural gap. The correct sequence is ARAS SCC entering the CPM SCC from outside; the current implementation inverts this.

### Step 3 — Session Loading Procedure Invocation

**Loads:** Initiates the session loading procedure, which orchestrates the remainder of the root path.
**Participating file:** .claude/skills/cpm-resume/SKILL.md.
**Omission:** Never omitted. The root CLAUDE.md directs actors into this procedure at all session boundaries.

### Step 4 — Subsystem Additional Procedures

**Loads:** Additional procedures registered by subsystem entry points encountered in Step 1. This includes documentation governance files, domain concern chain files, and any other additional procedure files declared by subsystems.
**Participating files:** All additional procedure files declared in the Tree Schema by their respective subsystems.
**Omission:** Omitted when no declared subsystems along the working path register additional procedures.

### Step 5 — Project Context

**Loads:** Project cornerstone document(s) identified by the active project reference.
**Participating files:** Extra-schema. Project documents are loading state content, not CCS-visible.
**Omission:** Omitted when no active project reference is provided.

### Step 6 — Session Context

**Loads:** Session context file for the provided session-id.
**Participating files:** Extra-schema. Session context files are loading state content.
**Omission:** Omitted when no session-id is provided.

### Step 7 — Actor Identity Resolution

**Loads:** Resolves actor identity from session-id against the Active Actors table in .claude/CLAUDE.md.
**Participating files:** .claude/CLAUDE.md (Active Actors table is loading state content co-residing in a CCS-visible file).
**Omission:** Omitted when no session-id is provided.

### PSI Assertion

All actual loading paths for all valid input combinations are ordered subsequences of Steps 1-7. The session loading procedure (.claude/skills/cpm-resume/SKILL.md) implements Steps 3-7; Steps 1-2 are executed by the RCC and root CLAUDE.md directives before the procedure is invoked. The procedure's internal step sequence must match Steps 3-7 in order, with only the declared omissions applied.

---

## Tree Schema

```
.                                             # Entry point + RCC: Claude Code native CLAUDE.md traversal (extra-repository)
├── .claude/
│   ├── CLAUDE.md                             # Root CPM context chain [CCS-visible]
│   └── skills/
│       └── cpm-resume/
│           └── SKILL.md                      # Session loading procedure [CCS-visible]
├── docs/
│   ├── CLAUDE.md                             # Documentation subsystem entry point [CCS-visible] (to be created)
│   ├── frontend/
│   │   ├── CLAUDE.md                         # Doc frontend subsystem entry point [CCS-visible] (to be created)
│   │   └── DOCUMENTATION_STANDARDS.md        # Frontend doc loading procedures [CCS-visible]
│   └── infrastructure/
│       └── CLAUDE.md                         # Doc infrastructure subsystem entry point [CCS-visible] (to be created)
├── nextjs/
│   ├── CLAUDE.md                             # Artifact frontend subsystem entry point [CCS-visible] (to be created)
│   └── DOCUMENTATION_CONTEXT.md             # Artifact frontend context loading procedures [CCS-visible] (to be created)
└── infrastructure/
    └── CLAUDE.md                             # Artifact infrastructure subsystem entry point [CCS-visible] (to be created)
```

### Instance-Wide Piggyback Assumption

In this instantiation, all subsystems piggyback on the Claude Code native CLAUDE.md traversal RCC unless explicitly declared otherwise. A subsystem registers its CCS participation by adding a named section to its CLAUDE.md file and all CLAUDE.md files of levels under the working subsystem. Sections need only exist — they are not required to contain content.

### Entry Point and RCC Compliance Exemption

Because the entry point and RCC of the root-level Context Chain system are enforced by Claude's native functionality and actor instruction (both extra-repo), the entry point (directive to read root-level CLAUDE.md) and the RCC (directive to read every CLAUDE.md at every level of the actor's working path) is compliance-exempt.

### Tree-Level Assertions

```yaml
tree:
  - .claude/CLAUDE.md exists
  - .claude/skills/cpm-resume/SKILL.md exists
  - docs/CLAUDE.md exists
  - docs/frontend/CLAUDE.md exists
  - docs/frontend/DOCUMENTATION_STANDARDS.md exists
  - docs/infrastructure/CLAUDE.md exists
  - nextjs/CLAUDE.md exists
  - nextjs/DOCUMENTATION_CONTEXT.md exists
  - infrastructure/CLAUDE.md exists
```

---

## Root Subsystem: `.claude/`

**Aim:** Enter all actors into the CPM System and initiate context chain loading. Achieve PSI for the context chain.
**Entry point + RCC:** Claude Code's native CLAUDE.md loading (extra-repository, tool-enforced) — in this instantiation, entry point and RCC are unified.
**Additional procedures:** `cpm-resume/SKILL.md`.
**Root Loading Path authority:** The root path for this instantiation is declared in the Root Loading Path section above. The session loading procedure (.claude/skills/cpm-resume/SKILL.md) implements Steps 3-7; Steps 1-2 are executed by the RCC before the procedure is invoked.

---

### `.claude/CLAUDE.md`

Root CPM context chain. The first CLAUDE.md file encountered by the RCC traversal for any actor in any working domain. Contains information integrity principles (loading state content) alongside CCS-specific content. This schema specifies the CCS-relevant content only.

#### Expected CCS Content

**[MIS-ARAS Patch]** section:

- ARAS pre-traversal loading directive: instructs actors to load `.claude/.aras/ARAS.md` and current branch `ARA.md` before proceeding with concern chain traversal (Root Loading Path, Step 2)
- ARAS pre-traversal section is annotated as a known gap (correct sequence is ARAS SCC before CPM SCC; current implementation inverts this)

**[CPM Instantiation RCC]** section:

**Task routing:**

- Directs actor to run cpm-resume at all session boundaries — fresh session and post-compaction recovery alike (Root Loading Path, Step 3)

#### Assertions

```yaml
file:
  - exists
  - expected_path: .claude/CLAUDE.md
content:
  cpm_instantiation_rcc:
    - section present
    - contains ARAS pre-traversal loading directive (Root Loading Path, Step 2)
    - ARAS pre-traversal annotated as known gap
  task_routing:
    - present
    - directs actor to run cpm-resume at session boundaries (Root Loading Path, Step 3)
```

---

### `.claude/skills/cpm-resume/SKILL.md`

Session loading procedure. Serves as the single session entry skill for both fresh sessions and post-compaction recovery. Session-id argument is optional: omitted for fresh session start, provided for post-compaction recovery. Implements the Root Loading Path declared in this schema — the procedure's step sequence matches Steps 3-7, with only the declared omission conditions applied.

#### Expected CCS Content

- Accepts optional session-id argument
- Single procedure handling both fresh session and post-compaction recovery
- Internal step sequence matches Root Loading Path Steps 3-7 in order:
  - Step 3: Subsystem Additional Procedures (omitted when no subsystems register procedures)
  - Step 4: Project Context (omitted when no active project reference)
  - Step 5: Session Context (omitted when no session-id)
  - Step 6: Actor Identity Resolution (omitted when no session-id)
- Omission conditions reference declared valid inputs only
- Outputs structured summary of loaded state
- Awaits managing developer approval before any work begins

#### Assertions

```yaml
file:
  - exists
  - expected_path: .claude/skills/cpm-resume/SKILL.md
content:
  session_loading:
    - accepts optional session-id argument
    - serves fresh session entry when session-id omitted
    - serves post-compaction recovery when session-id provided
    - implements the Root Loading Path declared in [Root Loading Path section]
    - step sequence matches Root Loading Path Steps 3-7
    - omission conditions match declared omission conditions for each step
    - step sequence is identical (omissions allowed) regardless of input (PSI)
```

---

## Subsystem: `docs/`

**Aim:** Load documentation governance for all actors entering the docs/ domain.
**Entry point:** `docs/CLAUDE.md`.
**RCC:** inherited.
**Additional procedures:** none declared (pending governance audit).

---

### `docs/CLAUDE.md`

Documentation subsystem entry point. Loaded by the RCC traversal for any actor working within `docs/`.

_(To be created as part of governance reorganization.)_

#### Expected CCS Content

**[CPM Instantiation RCC]** section:

- _(Empty)_

**[Documentation Subsystem Entry]** section:

- Directs actor to read `docs/DOCUMENTATION_STANDARDS.md`

#### Assertions

```yaml
file:
  - exists
  - expected_path: docs/CLAUDE.md
content:
  cpm_instantiation_rcc:
    - section present
  documentation_subsystem_entry:
    - section present
    - directs actor to read docs/DOCUMENTATION_STANDARDS.md
```

---

## Subsystem: `docs/frontend/`

**Aim:** Surface frontend documentation loading directives for actors entering the docs/frontend/ domain.
**Entry point:** `docs/frontend/CLAUDE.md`.
**RCC:** inherited.
**Additional procedures:** `docs/frontend/DOCUMENTATION_STANDARDS.md` (CCS-visible loading procedures).

---

### `docs/frontend/CLAUDE.md`

Frontend documentation subsystem entry point. Boundary node carrying named sections for each simultaneously active governance layer.

_(To be created as part of governance reorganization.)_

#### Expected CCS Content

**[CPM Instantiation RCC]** section:

- _(Empty)_

**[CPM Subsystem Entry]** section:

- _(Empty)_

**[Frontend Domain Entry]** section:

- Directs actor to read `docs/frontend/DOCUMENTATION_STANDARDS.md`

#### Assertions

```yaml
file:
  - exists
  - expected_path: docs/frontend/CLAUDE.md
content:
  cpm_instantiation_rcc:
    - section present
  cpm_subsystem_entry:
    - section present
  frontend_domain_entry:
    - section present
    - directs actor to read docs/frontend/DOCUMENTATION_STANDARDS.md
```

---

### `docs/frontend/DOCUMENTATION_STANDARDS.md`

CCS-visible due to loading procedures it contains. Directs actors to attribute-specific content within `docs/frontend/system/` via the task-based discovery table.

#### Expected CCS Content

_(To be specified during context model integration.)_

#### Assertions

```yaml
file:
  - exists
  - expected_path: docs/frontend/DOCUMENTATION_STANDARDS.md
content:
  loading_procedures:
    - present (content to be specified during context model integration)
```

---

## Subsystem: `docs/infrastructure/`

**Aim:** Surface infrastructure documentation loading directives for actors entering the docs/infrastructure/ domain.
**Entry point:** `docs/infrastructure/CLAUDE.md`.
**RCC:** inherited.
**Additional procedures:** none declared (pending governance audit).

---

### `docs/infrastructure/CLAUDE.md`

Infrastructure documentation subsystem entry point. Boundary node; same three-layer section structure as `docs/frontend/CLAUDE.md` adapted to the infrastructure domain.

_(To be created as part of governance reorganization.)_

#### Expected CCS Content

**[CPM Instantiation RCC]** section:

- _(Empty)_

**[CPM Subsystem Entry]** section:

- _(Empty)_

**[Infrastructure Domain Entry]** section:

- Directs actor to read `docs/infrastructure/DOCUMENTATION_STANDARDS.md`

#### Assertions

```yaml
file:
  - exists
  - expected_path: docs/infrastructure/CLAUDE.md
content:
  cpm_instantiation_rcc:
    - section present
  cpm_subsystem_entry:
    - section present
  infrastructure_domain_entry:
    - section present
    - directs actor to read docs/infrastructure/DOCUMENTATION_STANDARDS.md
```

---

## Subsystem: `nextjs/`

**Aim:** Surface context loading directives for actors working in the Next.js artifact.
**Entry point:** `nextjs/CLAUDE.md`.
**RCC:** inherited.
**Additional procedures:** `nextjs/DOCUMENTATION_CONTEXT.md` (CCS-visible, to be created).

---

### `nextjs/CLAUDE.md`

Artifact frontend subsystem entry point. Boundary node carrying named sections for each simultaneously active governance layer.

_(To be created as part of governance reorganization.)_

#### Expected CCS Content

**[CPM Instantiation RCC]** section:

- _(Empty)_

**[CPM Subsystem Entry]** section:

- _(Empty)_

**[Artifact Frontend Domain Entry]** section:

- Directs actor to read `nextjs/DOCUMENTATION_CONTEXT.md`

#### Assertions

```yaml
file:
  - exists
  - expected_path: nextjs/CLAUDE.md
content:
  cpm_instantiation_rcc:
    - section present
  cpm_subsystem_entry:
    - section present
  artifact_frontend_domain_entry:
    - section present
    - directs actor to read nextjs/DOCUMENTATION_CONTEXT.md
```

---

### `nextjs/DOCUMENTATION_CONTEXT.md`

CCS-visible context loading procedure file for actors working in the Next.js artifact. Defines how an artifact-domain actor loads context — a fundamentally different procedure from the documentation loading procedure defined in `docs/frontend/DOCUMENTATION_STANDARDS.md`.

_(To be created as part of governance reorganization.)_

#### Expected CCS Content

_(To be specified during context model integration.)_

#### Assertions

```yaml
file:
  - exists
  - expected_path: nextjs/DOCUMENTATION_CONTEXT.md
content:
  context_loading_procedures:
    - present (content to be specified during context model integration)
```

---

## Subsystem: `infrastructure/`

**Aim:** Surface context loading directives for actors working in the infrastructure artifact.
**Entry point:** `infrastructure/CLAUDE.md`.
**RCC:** inherited.
**Additional procedures:** none declared (pending governance audit).

---

### `infrastructure/CLAUDE.md`

Artifact infrastructure subsystem entry point. Boundary node; same three-layer section structure as `nextjs/CLAUDE.md` adapted to the infrastructure artifact domain.

_(To be created as part of governance reorganization.)_

#### Expected CCS Content

**[CPM Instantiation RCC]** section:

- _(Empty)_

**[CPM Subsystem Entry]** section:

- _(Empty)_

**[Artifact Infrastructure Domain Entry]** section:

- Directs actor to read `docs/infrastructure/DOCUMENTATION_STANDARDS.md`

#### Assertions

```yaml
file:
  - exists
  - expected_path: infrastructure/CLAUDE.md
content:
  cpm_instantiation_rcc:
    - section present
  cpm_subsystem_entry:
    - section present
  artifact_infrastructure_domain_entry:
    - section present
    - directs actor to read docs/infrastructure/DOCUMENTATION_STANDARDS.md
```
