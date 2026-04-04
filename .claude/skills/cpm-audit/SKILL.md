---
name: cpm-audit
description: "Full compliance assessment of the repository against the Context Persistence Model schema. Reads the CPM schema, audits all entities, and produces a structured compliance report. Invoked by 'CPM-audit', 'audit CPM', or /CPM-audit. Makes no changes without explicit managing developer approval."
---

# CPM-audit

## Overview

Full repository compliance assessment against the Context Persistence Model. Reads the CPM schema from this skill's reference folder, audits every CPM entity in the repository against its defined compliance checks, and produces a structured report. This skill is audit-only — no remediation is performed without explicit managing developer approval.

## When to Activate

- Managing developer invokes "CPM-audit" or "audit CPM"
- Managing developer suspects structural drift or compliance issues
- Periodically as part of CPM maintenance

## Reference

- **Schema location:** `.claude/skills/CPM-audit/references/CPM-schema.md`

---

## Audit Protocol

### Step 1: Load Schema

Read `.claude/skills/CPM-audit/references/CPM-schema.md` in its entirety. This is the authoritative definition of what the CPM consists of and what each entity must satisfy.

### Step 2: Audit Governance Documents

For each governance document defined in Schema Section 1:

**CLAUDE.md**

- Exists at repository root
- Contains Role/Content/Constraints header
- Contains all four named principles
- Contains Implications section
- Contains Operational Entry Point section referencing ENTRY_POINT.md
- Contains no behavioral directives, project context, or documentation standards

**ENTRY_POINT.md**

- Exists at repository root
- Contains Role/Content/Constraints header
- Contains "Before Any Task" section prescribing path-reading rule
- Contains "Task Routing" section with development, documentation, and maintenance types
- Development tasks route to `docs/dev_process/DEV_PROCESS.md`
- Contains no governance definitions or process stages

**README.md**

- Exists at repository root
- First actionable direction points to ENTRY_POINT.md
- Contains no governance, process, or standards content restated

### Step 3: Audit Documentation Standards

**Base standards** (`docs/DOCUMENTATION_STANDARDS.md`)

- Exists at docs root
- Contains Role/Content/Constraints header
- Contains all required sections per schema Section 2.1
- Layer table lists three layers with correct names, locations, and lifecycles
- Path-reading rule references both DOCUMENTATION_STANDARDS.md and dev process files
- Interactions file template present under Development Process Documentation
- Extra-Model Entities section present with Live Code and Agent Configuration
- Anti-patterns table present
- Enforcement section present

**Project standards** (`docs/tmp/DOCUMENTATION_STANDARDS.md`)

- Exists at project layer root
- Contains Role/Content/Constraints header
- Does not contradict base standards
- Cornerstone required sections include all six: Executive Summary, Strategic Decisions, Acceptance Criteria, Progress Tracking, Session Continuity, Migration Candidates
- Content expectations list four categories

**Domain-specific standards**

- For each DOCUMENTATION_STANDARDS.md found along any path under docs/:
  - Contains Role/Content/Constraints header
  - Does not contradict ancestor standards
  - Scoped to its own level

### Step 4: Audit Documentation Layers

**Permanent layer** (`docs/` excluding `docs/tmp/`)

- All documentation files have Role/Content/Constraints headers
- No files reference previous states of the codebase
- No project-specific or session-specific content present
- Flag any content that appears to belong in a different layer

**Project layer** (`docs/tmp/`)

- Each subdirectory has a cornerstone document
- Each cornerstone contains all six required sections
- Migration Candidates section present and maintained in each cornerstone
- Flag any authoritative/stable content that should be in permanent docs
- Flag any session-specific content that belongs in session context

**Session layer** (`.claude/session-context/`)

- Each file follows naming convention `session-context-[session-id].md`
- Files are small and scoped
- Flag any content that should be in permanent or project documentation
- Flag any evidence of appending rather than full rewriting

### Step 5: Audit Path-Reading Rule Compliance

For each domain that has governance files:

- Trace the path from repository root to the domain
- Read all DOCUMENTATION_STANDARDS.md and dev process files along the path
- Verify no file contradicts an ancestor
- Verify extend-not-contradict relationship holds at every level

### Step 6: Audit File Headers

For every documentation file in the repository:

- Role/Content/Constraints header present
- Fields appear in correct order
- Constraints are specific to the file (not generic)
- File does not restate its layer classification

### Step 7: Audit Development Processes

**Base development process** (`docs/dev_process/DEV_PROCESS.md`)

- Exists at defined location
- Contains Role/Content/Constraints header
- All five stages defined (Educate, Ideate, Design, Implement, Document)
- Stage 1 includes governance loading via path-reading rule
- Scaling section present
- Hierarchical Fulfillment section present
- Does not prescribe documentation structure

**Domain-specific processes**

- For each domain dev process found:
  - Contains Role/Content/Constraints header
  - Header declares procedural authority and dual-authority relationship
  - Extends base stages without contradicting them

**Interactions files**

- For each dev process found, a co-located interactions file exists
- Each interactions file has Role/Content/Constraints header
- Header declares CPM ownership
- Constraints include cross-authority maintenance obligation
- Each boundary point has all five required fields: Trigger, Documentation Affected, Target Layer, Target Location, CPM Requirements
- Boundary points reflect current dev process stages (no stale or missing entries)

### Step 8: Audit Extra-Model Boundaries

- No documentation-layer files present in `.claude/` outside of `session-context/`
- No project or permanent documentation stored in agent configuration
- Interactions files exist where dev processes exist

### Step 9: Audit CPM Skills

For each skill defined in Schema Section 9:

- Skill file exists at defined location
- Skill content aligns with schema-defined protocol, triggers, arguments, and anti-patterns
- No skill restates governance content that should be deferred to documentation

### Step 10: Output Compliance Report

Format the report as:

```markdown
## CPM Compliance Report

**Audit Date:** [date]
**Schema Version:** [last updated from schema]

### Summary

- **Total entities audited:** [count]
- **Compliant:** [count]
- **Findings:** [count]

### Findings by Section

#### Governance Documents

- [finding or "Compliant"]

#### Documentation Standards

- [finding or "Compliant"]

#### Documentation Layers

- [finding or "Compliant"]

#### Path-Reading Rule Compliance

- [finding or "Compliant"]

#### File Headers

- [finding or "Compliant"]

#### Development Processes

- [finding or "Compliant"]

#### Extra-Model Boundaries

- [finding or "Compliant"]

#### CPM Skills

- [finding or "Compliant"]

### Recommendations

- [prioritized list of remediation actions, if any]

---

Awaiting managing developer direction before any remediation.
```

### Step 11: Await Direction

Do not take any remediation action. Present the compliance report and wait for the managing developer to direct specific fixes, approve a remediation plan, or dismiss findings.

---

## Anti-Patterns

### Critical

- **Don't** make any changes during an audit — this is a read-only assessment
- **Don't** skip schema sections — every section must be audited
- **Don't** infer compliance where evidence is ambiguous — surface the ambiguity as a finding

### Additional

- **Don't** audit files outside the CPM's scope (live code, agent configuration other than skills)
- **Don't** restate schema definitions in the report — reference schema sections by number
- **Don't** prioritize remediation recommendations without managing developer input on priority
