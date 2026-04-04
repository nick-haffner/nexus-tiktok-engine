# Context Persistence Model: Schema

**Purpose:** Complete definition of all CPM entities and their realizations in the codebase. Serves as the authoritative reference for CPM-audit and as the managing developer's complete system reference.

**Last Updated:** 2026-02-08

---

## 1. Governance Documents

### 1.1 CLAUDE.md

```yaml
location: "CLAUDE.md"
level: repository_root
authority: principle
governs: all_cpm_components
edit_conditions:
  - "Modifications to information integrity principles"
  - "Modifications to the context persistence system"
required_structure:
  header:
    - Role
    - Content
    - Constraints
  sections:
    - name: Principles
      required_subsections:
        - "1: Visibility Over Completeness"
        - "2: Intentional Persistence"
        - "3: Scoped, Contradiction-Free Handoffs"
    - name: Implications
    - name: Operational Entry Point
      references: "ENTRY_POINT.md"
prohibited_content:
  - behavioral_directives
  - project_context
  - documentation_standards
```

CLAUDE.md is the highest authority in the CPM. It contains information integrity principles that govern how all documentation layers manage context lifecycle and how independent governance systems interact over shared artifacts. The operational entry point section is a structural necessity of the principle system — it declares where actors enter the CPM without prescribing behavior beyond routing.

### 1.2 ENTRY_POINT.md

```yaml
location: "ENTRY_POINT.md"
level: repository_root
authority: operational
governed_by: cpm_structural_authority
purpose: route_actors_into_cpm
required_structure:
  header:
    - Role
    - Content
    - Constraints
  sections:
    - name: "Before Any Task"
      routes_to: governance_loading
    - name: "Task Routing"
      task_types:
        - type: development
          routes_to: "docs/dev_process/DEV_PROCESS.md"
        - type: documentation
          routes_to: governance_loaded_via_path_reading
        - type: maintenance
          routes_to: governance_loaded_via_path_reading
prohibited_content:
  - governance_definitions
  - documentation_standards
  - process_stages
```

ENTRY_POINT.md is the universal starting point for all work. It prescribes governance loading via the path-reading rule and routes actors to the appropriate procedural framework. It must remain thin — routing only, no governance content.

### 1.3 README.md

```yaml
location: "README.md"
level: repository_root
authority: navigational
purpose: orient_actors_to_entry_point
required_references:
  - "ENTRY_POINT.md"
  - "CLAUDE.md"
  - "docs/DOCUMENTATION_STANDARDS.md"
prohibited_content:
  - governance_definitions
  - process_stages
  - documentation_standards
```

README.md is navigational. Its first actionable direction must point to ENTRY_POINT.md. It provides a top-level repository structure overview but does not restate governance, process, or standards content.

---

## 2. Documentation Standards

### 2.1 Base Documentation Standards

```yaml
location: "docs/DOCUMENTATION_STANDARDS.md"
level: docs_root
authority: structural
scope: entire_repository
governs:
  - documentation_layer_model
  - file_header_requirements
  - quality_principles
  - path_reading_rule
  - development_process_documentation_requirements
  - extra_model_entity_definitions
  - anti_patterns
  - enforcement_rules
required_structure:
  header:
    - Role
    - Content
    - Constraints
  sections:
    - Required File Header
    - Documentation Layers
    - Quality Principles
    - Domain-Specific Standards
    - Development Process Documentation
    - Extra-Model Entities
    - Anti-Patterns
    - Enforcement
relationships:
  governed_by: "CLAUDE.md"
  extended_by: domain_specific_documentation_standards
  referenced_by:
    - all_documentation_files
    - all_cpm_skills
```

This is the single source of truth for documentation organization. All domain-specific standards extend it via the path-reading rule. It defines the layer model, quality principles, governance discovery, and the structural requirements the CPM places on development processes.

### 2.2 Project Documentation Standards

```yaml
location: "docs/tmp/DOCUMENTATION_STANDARDS.md"
level: project_layer_root
authority: structural
scope: "docs/tmp/"
extends: "docs/DOCUMENTATION_STANDARDS.md"
constraint: must_not_contradict_base_standards
required_structure:
  header:
    - Role
    - Content
    - Constraints
  sections:
    - Per-Epic Structure
    - Cornerstone Document
    - Content Expectations
    - Repo Documentation Standards
cornerstone_required_sections:
  - Executive Summary
  - Strategic Decisions
  - Acceptance Criteria
  - Progress Tracking
  - Session Continuity
  - Migration Candidates
content_categories:
  - project_metadata_and_operational_state
  - project_specific_procedures
  - staging_content
  - disposable_reference
```

Extends base standards for the project layer. Defines per-epic structure, cornerstone requirements, and content expectations. Quality principles are applied directionally rather than definitively for project documentation.

### 2.3 Domain-Specific Documentation Standards

```yaml
location_pattern: "DOCUMENTATION_STANDARDS.md at any level under docs/"
authority: structural
scope: own_level_and_descendants
extends: ancestor_documentation_standards
constraint: must_not_contradict_ancestors
discovery: path_reading_rule
required_structure:
  header:
    - Role
    - Content
    - Constraints
```

Any domain may define additional documentation standards by placing a `DOCUMENTATION_STANDARDS.md` file at the appropriate level. The path-reading rule discovers these automatically. Each file extends ancestor standards without contradicting them.

---

## 3. Documentation Layers

### 3.1 Permanent Layer

```yaml
name: Permanent
location: "docs/ (excluding docs/tmp/)"
lifecycle: permanent
function: authoritative_description_of_central_artifact_current_state
maintained_by: managing_developer
quality_rigor: full_adherence
constraints:
  - must_not_reference_previous_states
  - only_layer_referenced_across_projects_and_long_time_horizons
content_types:
  - architecture
  - functionality_references
  - troubleshooting_guidance
  - gaps_and_issues
  - development_process_documentation
  - cpm_interactions_files
includes_procedural_authority_files: true
```

The authoritative layer. Includes files whose primary authority is procedural (dev processes) — these are subject to CPM structural governance but their content is governed by their own procedural authority, as described in DOCUMENTATION_STANDARDS.md under Development Process Documentation.

### 3.2 Project Layer

```yaml
name: Project
location: "docs/tmp/ (organized by epic)"
lifecycle: temporary
function: project_memory
maintained_by: managing_developer
quality_rigor: where_practical
directory_structure:
  pattern: "docs/tmp/[epic-name]/"
  required_files:
    - "[epic-name].md (cornerstone)"
  additional_files: as_needed
lifecycle_events:
  on_completion:
    - resolve_all_migration_candidates
    - migrate_or_dismiss_each_candidate
    - remove_epic_directory
constraints:
  - does_not_survive_project_completion
  - content_either_migrates_to_permanent_or_is_removed
```

Project memory layer. The Migration Candidates section in each cornerstone document tracks content approaching permanent-worthy status throughout the project. No epic directory may be removed until all migration candidates are resolved.

### 3.3 Session Layer

```yaml
name: Session
location: ".claude/session-context/"
lifecycle: volatile
function: single_handoff_context
file_naming: "session-context-[session-id].md"
write_protocol: full_rewrite_only
maintained_by: claude_via_cpm_pause
quality_rigor: sufficient_for_continuation
constraints:
  - never_appended
  - must_remain_small_and_scoped
  - sole_documentation_type_without_complete_managing_developer_intent
  - full_rewrite_forces_contradiction_reconciliation_at_write_time
```

Volatile layer. Each session receives a dedicated file. Full rewrites at each compaction event implement Principle 3 directly — contradictions are reconciled at write time rather than accumulated.

---

## 4. Path-Reading Rule

```yaml
definition_location: "docs/DOCUMENTATION_STANDARDS.md"
section: Domain-Specific Standards
trigger: before_editing_any_file
scope: repository_root_to_working_directory
files_discovered:
  - type: "DOCUMENTATION_STANDARDS.md"
    authority: structural
  - type: development_process_root_files
    authority: procedural
  - type: interactions_files
    authority: structural_boundary_declaration
hierarchy: extend_not_contradict
conflict_behavior: hard_stop_until_resolved
```

The path-reading rule is the CPM's primary mechanism for both governance discovery and contradiction prevention. It loads all applicable governance — structural and procedural — before work begins. Its scope was extended from documentation standards only to include development process files, reflecting the CPM's broadened purpose: ensuring all governing context relevant to a task is discoverable and loadable.

---

## 5. Required File Header

```yaml
definition_location: "docs/DOCUMENTATION_STANDARDS.md"
section: Required File Header
applies_to: every_documentation_file
required_fields:
  - field: Role
    order: 1
    purpose: "How the file relates to the larger documentation model"
  - field: Content
    order: 2
    purpose: "What the file contains (scope summary)"
  - field: Constraints
    order: 3
    purpose: "Boundaries predictive of likely drift, scope creep, or misuse"
optional_metadata: permitted_after_required_fields
constraints:
  - fields_must_appear_in_defined_order
  - constraints_must_be_specific_to_the_file
  - files_must_not_restate_layer_classification
```

The header pattern makes each file's scope visible at the point of editing. Constraints are predictive — they address the most probable ways the specific file could drift from its intended purpose, not generic documentation rules.

---

## 6. Quality Principles

```yaml
definition_location: "docs/DOCUMENTATION_STANDARDS.md"
section: Quality Principles
applies_to: all_documentation_regardless_of_layer
principles:
  - name: Completeness
    requirement: "Nothing silently missing within scope"
  - name: Abstraction
    requirement: "Human-legible overviews before implementation detail"
  - name: Visibility
    requirement: "Rationale captured — WHY not just WHAT"
  - name: Actionability
    requirement: "Enables the reader to act"
scaling:
  permanent: full_adherence
  project: where_practical
  session: sufficient_for_continuation
verification: four_item_checklist_before_finalizing_any_change
```

Quality principles are properties of documentation, not properties of the system. They describe what good documentation looks like independent of the layer model or structural governance. Rigor scales with layer lifecycle.

---

## 7. Development Process

### 7.1 Base Development Process

```yaml
location: "docs/dev_process/DEV_PROCESS.md"
authority: procedural
scope: all_development_tasks
governed_by_structurally: "docs/DOCUMENTATION_STANDARDS.md"
structural_procedural_distinction: "Described in docs/DOCUMENTATION_STANDARDS.md under Development Process Documentation"
stages:
  - number: 1
    name: Educate
    includes: governance_loading_via_path_reading_rule
  - number: 2
    name: Ideate
  - number: 3
    name: Design
  - number: 4
    name: Implement
  - number: 5
    name: Document
    includes: documentation_standards_compliance_pass
additional_sections:
  - Scaling
  - Hierarchical Fulfillment
constraints:
  - domain_processes_extend_but_cannot_contradict
  - does_not_prescribe_documentation_structure
```

The base development process is the procedural entry point for all development tasks (routed from ENTRY_POINT.md). It applies to every development task with rigor proportional to scope. Domain-specific processes extend it with domain-scoped stages and deliverables.

### 7.2 Domain-Specific Development Processes

```yaml
location_pattern: "Domain documentation directories"
authority: procedural
extends: "docs/dev_process/DEV_PROCESS.md"
constraint: must_not_contradict_base_stages
discovery: path_reading_rule
required_structure:
  header:
    - Role
    - Content
    - Constraints
  role_must_declare:
    - procedural_authority
    - relationship_to_cpm_structural_governance
known_instances:
  - domain: frontend
    location: "docs/frontend/DEV_PROCESS/DEV_PROCESS.md"
    extensions:
      - "Stage 0: Review Frontend Principles"
      - "Vision directories (Stage 2)"
      - "Rules and constraints directories (Stage 3)"
      - "Vision summary and system rules extraction (Stage 5)"
```

Domain processes extend the base with domain-specific stages, substeps, and deliverables. Each must declare procedural authority and its relationship to CPM structural governance in its header.

### 7.3 Interactions Files

```yaml
authority: structural
ownership: cpm
co_located_with: associated_dev_process
discovery: path_reading_rule
purpose: cpm_boundary_declaration_at_dev_process_touchpoints
required_structure:
  header:
    - Role
    - Content
    - Constraints
  constraints_must_include: cross_authority_maintenance_obligation
  sections:
    - name: Boundary Points
      per_boundary_point:
        - field: Trigger
        - field: Documentation Affected
        - field: Target Layer
        - field: Target Location
        - field: CPM Requirements
known_instances:
  - name: Base
    location: "docs/dev_process/INTERACTIONS.md"
    boundary_points:
      - "Documentation Standards Compliance Pass (Stage 5)"
  - name: Frontend
    location: "docs/frontend/DEV_PROCESS/INTERACTIONS.md"
    boundary_points:
      - "Vision Documentation Created (Stage 2)"
      - "Rules and Constraints Documentation Created (Stage 3)"
      - "Vision Summary Updated (Stage 5)"
      - "System Rules and Constraints Extracted (Stage 5)"
      - "General Documentation Updates (Stage 5)"
```

Interactions files are CPM-owned boundary declarations co-located with the dev process they describe. Their placement alongside the dev process reflects the shared boundary between structural and procedural authority; their header declares CPM ownership. The cross-authority maintenance obligation requires review when the associated dev process modifies documentation-producing stages.

---

## 8. Extra-Model Entities

### 8.1 Live Code

```yaml
definition_location: "docs/DOCUMENTATION_STANDARDS.md"
section: "Extra-Model Entities > Live Code"
relationship_to_cpm: extra_model
includes:
  - application_code
  - infrastructure_code
  - configuration_files
  - all_non_documentation_artifacts
boundary_mechanism: dev_process_interactions_files
cpm_does_not_govern:
  - code_location
  - code_structure
  - code_quality_standards
```

The CPM does not govern code. Boundary interactions between code and documentation are defined by development processes and declared by interactions files. The guarantee that code changes are informed by documentation is a development process concern, not a CPM concern.

### 8.2 Agent Configuration

```yaml
definition_location: "docs/DOCUMENTATION_STANDARDS.md"
section: "Extra-Model Entities > Agent Configuration"
location: ".claude/ (excluding .claude/session-context/)"
relationship_to_cpm: extra_model
contents:
  - skills
  - settings
  - cli_configuration
  - skill_references
exceptions:
  - entity: session_context
    location: ".claude/session-context/"
    participates_in: session_layer
  - entity: "CLAUDE.md"
    location: repository_root
    contains: information_integrity_principles
```

Agent configuration governs how Claude operates but does not describe the project. Session context and CLAUDE.md are the two exceptions — session context participates in the session layer, and CLAUDE.md contains the principles governing the entire model.

---

## 9. CPM Skills (Persistence Procedures)

### 9.1 CPM-start

```yaml
location: ".claude/skills/CPM-start/SKILL.md"
purpose: fresh_session_initialization
trigger:
  - new_session_with_no_prior_context
  - user_says: ["enter context", "start session"]
arguments:
  - name: domain
    required: false
protocol:
  - step: 1
    action: "Read ENTRY_POINT.md and follow its instructions"
  - step: 2
    action: "Output context summary (governance loaded, task type, domain)"
  - step: 3
    action: "Await managing developer acknowledgment"
output_sections:
  - Governance Loaded (structural, procedural, interactions)
  - Task Type (development / documentation / maintenance)
  - Domain (path or "not yet identified")
anti_patterns:
  critical:
    - "Skip ENTRY_POINT.md"
    - "Begin task execution before governance loaded and task confirmed"
  additional:
    - "Use for post-compaction recovery (use CPM-resume)"
    - "Load session context files (fresh session)"
    - "Restate governance content in summary"
```

### 9.2 CPM-pause

```yaml
location: ".claude/skills/CPM-pause/SKILL.md"
purpose: pre_compaction_context_persistence
trigger:
  - context_window_above_80_percent
  - user_requests_compaction
  - user_says: ["persist context", "prepare for compaction"]
arguments:
  - name: session-id
    required: false
    behavior_if_omitted: generate_new_session_id
protocol:
  - step: 1
    action: "Read documentation in order"
    reading_order:
      - "CLAUDE.md"
      - "docs/DOCUMENTATION_STANDARDS.md"
      - "Path-reading chain (if working domain known)"
      - "Project cornerstone document(s)"
      - "Session context file for session-id"
  - step: 2
    action: "Update documentation across layers"
    layers:
      permanent:
        condition: "Only if finalized and authoritative"
      project:
        condition: "Only if active epic exists"
        skip_if: no_active_epic
      session:
        protocol: full_rewrite_never_append
  - step: 3
    action: "Capture repetitive instructions"
    output: in_response_and_jsonl_append
    persist_to: ".claude/skills/propose-skills/references/repetitive-instructions.jsonl"
  - step: 4
    action: "Output pre-compact response"
    post_compaction_prompt: "CPM-resume [session-id]"
anti_patterns:
  critical:
    - "Include post-compaction recovery steps (handled by CPM-resume)"
    - "Overwrite repetitive-instructions.jsonl (append only)"
    - "Append to session context (full rewrite only)"
  additional:
    - "Create new files when updating existing ones suffices"
    - "Include speculative or unconfirmed content"
    - "Include sensitive data in post-compaction prompt"
    - "Restate documentation layer definitions"
```

### 9.3 CPM-resume

```yaml
location: ".claude/skills/CPM-resume/SKILL.md"
purpose: post_compaction_context_recovery
trigger:
  - post_compaction_prompt_provided
  - user_says: ["recontextualize", "resume"]
arguments:
  - name: session-id
    required: true
protocol:
  - step: 1
    action: "Read governance and context in order"
    reading_order:
      - "CLAUDE.md"
      - "docs/DOCUMENTATION_STANDARDS.md"
      - "Path-reading chain (DOCUMENTATION_STANDARDS.md + dev process files)"
      - "Interactions files (if dev process files found)"
      - "Project cornerstone document(s)"
      - "Session context file for session-id"
  - step: 2
    action: "Output context summary"
    output_sections:
      - Project State
      - Work in Progress
      - Key Decisions Active This Project
      - Governance Loaded (structural, procedural, interactions)
      - Session Context Carried Forward
      - Files Read
  - step: 3
    action: "Await explicit managing developer approval"
    approval_signals: ["Approved", "Proceed", "Continue", "Yes"]
    on_correction: re_summarize_and_reawait
gate: no_action_before_explicit_approval
anti_patterns:
  critical:
    - "Take action before approval"
    - "Assume context not in referenced files"
    - "Skip files in reading order"
    - "Read session context for other session-ids"
  additional:
    - "Read unreferenced files outside path-reading chain"
    - "Carry forward assumptions if session context missing"
    - "Restate documentation layer definitions in summary"
    - "Treat procedural governance as subordinate to structural or vice versa"
```

### 9.4 CPM-audit

```yaml
location: ".claude/skills/CPM-audit/SKILL.md"
purpose: full_cpm_compliance_assessment
trigger: managing_developer_invocation
arguments: none
scope: entire_repository
reference: "CPM-schema.md (this file)"
output: structured_compliance_report
protocol:
  - step: 1
    action: "Read this schema"
  - step: 2
    action: "Audit all entities against schema compliance checks"
  - step: 3
    action: "Output compliance report with findings per section"
  - step: 4
    action: "Await managing developer direction before remediation"
gate: audit_only_no_changes_without_approval
```

CPM-audit reads this schema and audits every entity in the repository against its compliance checks. It produces a structured report and takes no remediation action without explicit managing developer approval.

---

## 10. Anti-Patterns

```yaml
definition_location: "docs/DOCUMENTATION_STANDARDS.md"
section: Anti-Patterns
defined_anti_patterns:
  - pattern: "Editing without reading the path-reading chain"
    problem: "Contradictions introduced that the rule is designed to prevent"
  - pattern: "Missing or inaccurate file headers"
    problem: "Misleads editors about the file's role, scope, or boundaries"
  - pattern: "Restating content as more than a reference within documentation standards"
    problem: "Creates a second source of truth that can drift from authoritative location"
skill_enforced_anti_patterns:
  - pattern: "Appending to session context"
    enforced_by: CPM-pause
  - pattern: "Taking action before approval after compaction"
    enforced_by: CPM-resume
  - pattern: "Overwriting repetitive-instructions.jsonl"
    enforced_by: CPM-pause
  - pattern: "Loading session context in fresh session"
    enforced_by: CPM-start
  - pattern: "Including speculative content in any layer"
    enforced_by: CPM-pause
```

---

## 11. Enforcement Mechanisms

```yaml
definition_location: "docs/DOCUMENTATION_STANDARDS.md"
section: Enforcement
current_mechanisms:
  structural:
    - name: self_review
      mechanism: "Quality principles verification checklist"
    - name: path_reading_rule
      mechanism: "Compliance expected before any edit"
    - name: claude_md_lock
      mechanism: "Edit conditions in both CLAUDE.md and DOCUMENTATION_STANDARDS.md"
  skill_based:
    - name: CPM-start
      enforces: "ENTRY_POINT.md as universal entry"
    - name: CPM-pause
      enforces: "Documentation layer placement and full-rewrite constraint"
    - name: CPM-resume
      enforces: "Deterministic reading order and approval gate"
    - name: CPM-audit
      enforces: "Full schema compliance"
  procedural:
    - name: development_process
      enforces: "Governance loading at Stage 1 (Educate)"
    - name: entry_point
      enforces: "All tasks routed through governance loading"
future_mechanisms:
  - pr_review_for_documentation_completeness
  - automated_header_validation
  - path_reading_chain_validation_tooling
  - stale_project_documentation_detection
  - onboarding_feedback_loops
```
