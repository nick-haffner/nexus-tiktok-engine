# propose-skills

## Overview

Analyze accumulated repetitive instructions and conversation history to identify behavioral patterns that qualify as reusable skills. Reads the structured instruction log persisted by cpm-pause, clusters related patterns across sessions, cross-references against existing skills, and generates proposed skill packages for managing developer review. This skill is proposal-only — no skills are created or activated without explicit managing developer approval.

## When to Activate

- Managing developer says "propose skills", "find skills in my history", "extract skills", "skill audit", "review conversations for skills"
- Managing developer wants to identify recurring patterns that could be formalized
- After a significant number of new sessions have accumulated instruction entries

## References

- **Primary input:** `.claude/skills/propose-skills/references/repetitive-instructions/` (directory of per-session JSONL files)
- **Conversation transcripts:** `~/.claude/projects/` (JSONL session transcripts, optional deeper analysis)
- **Existing skills:** `.claude/skills/` (cross-reference to avoid duplication)

---

## Protocol

### Step 1: Load Instruction Log

Read all `*.jsonl` files from `.claude/skills/propose-skills/references/repetitive-instructions/`. Each file is named `[session-id].jsonl` and contains entries for that session. Parse each line as a JSON object with fields: `session_id`, `timestamp`, `project`, `instructions[]`.

Count total entries and unique sessions represented. Note the date range covered.

### Step 2: Cluster Related Instructions

Group instructions by semantic similarity across sessions. Look for:

- **Identical or near-identical instructions** appearing in multiple sessions
- **Thematic clusters** — instructions that address the same concern from different angles
- **Behavioral corrections** — instructions that correct a specific Claude behavior pattern
- **Process preferences** — instructions that define how the managing developer expects work to proceed

For each cluster, note:
- The core pattern (what behavior is being requested)
- Frequency (how many sessions mention it)
- Consistency (whether instructions contradict across sessions — later entries take precedence)
- Scope (project-specific vs. universal)

### Step 3: Cross-Reference Existing Skills

Read the SKILL.md file for each existing skill in `.claude/skills/`. For each instruction cluster identified in Step 2:

- If an existing skill already addresses the pattern → mark as "already captured"
- If an existing skill partially addresses it → mark as "enhancement candidate" with the target skill identified
- If no existing skill covers the pattern → mark as "new skill candidate"

### Step 4: Optionally Analyze Conversation Transcripts

If the managing developer requests deeper analysis, or if the instruction log alone is insufficient to form clear proposals:

- Read JSONL session transcripts from `~/.claude/projects/`
- Identify recurring workflows, multi-step procedures, or domain knowledge that appear across conversations but were not captured as repetitive instructions
- Add these as additional candidates

Skip this step if the instruction log provides sufficient signal. Inform the managing developer before reading transcripts, as they may be large.

### Step 5: Generate Skill Proposals

For each "new skill candidate" and "enhancement candidate" from Step 3, produce a structured proposal:

```markdown
### Proposed Skill: [name]

**Type:** New skill / Enhancement to [existing skill]
**Pattern:** [1-2 sentence description of the behavioral pattern]
**Evidence:** [N] sessions, date range [first]–[last]
**Representative instructions:**
- [instruction 1 — verbatim from log]
- [instruction 2 — verbatim from log]

**Proposed trigger:** [when this skill would activate]
**Proposed behavior:** [what the skill would do]
**Scope:** Project-specific / Universal
```

### Step 6: Output Proposals Report

Format the output as:

```markdown
## Skill Proposals

**Analysis Date:** [date]
**Instruction entries analyzed:** [count]
**Sessions covered:** [count] ([date range])
**Existing skills reviewed:** [count]

### Summary

- **Already captured:** [count] patterns
- **Enhancement candidates:** [count] patterns
- **New skill candidates:** [count] patterns

### Already Captured (No Action Needed)

- [pattern] → covered by [skill name]

### Enhancement Candidates

[Structured proposals per Step 5]

### New Skill Candidates

[Structured proposals per Step 5]

---

Awaiting managing developer direction. No skills will be created or modified without explicit approval.
```

### Step 7: Await Direction

Do not create or modify any skill files. Present the proposals report and wait for the managing developer to:

- Approve specific proposals for implementation
- Request modifications to proposals
- Dismiss proposals
- Request deeper analysis via Step 4

---

## Anti-Patterns

### Critical

- **Don't** create or modify skill files during analysis — this is a proposal-only skill
- **Don't** auto-activate proposed skills — all proposals require explicit managing developer approval
- **Don't** read conversation transcripts without informing the managing developer — transcripts may be large and consume significant context

### Additional

- **Don't** propose skills for patterns that appear in only one session — single-session patterns may be situational, not recurring
- **Don't** ignore contradictions between sessions — later instructions supersede earlier ones
- **Don't** propose skills that duplicate existing skill functionality — enhance existing skills instead
- **Don't** include sensitive data from instructions in the proposals report
