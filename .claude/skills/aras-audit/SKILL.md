# aras-audit

## Trigger

Managing developer requests an ARAS compliance audit.

## Protocol

### 1. Assess current state

Check `.claude/.aras/ARAS.md` for Protocol Lock state:

- If ARAS.md absent → hard stop (no MIS to audit)
- If ARAS.md exists with Lock != None → hard stop:

```
[aras-audit: BLOCKED]

An ARAS protocol is already in progress: [protocol name] ([path], step [N] [status]).
Complete or resolve the in-progress protocol before invoking
an audit.
```

- If ARAS.md exists with Lock = None → proceed

Confirm ARAS.md status is Active.

### 2. Determine audit scope

Ask the managing developer:

"Have all active subsystems passed a /cpm-audit in their
current state?"

- Yes → full audit (levels 1, 2, 3)
- No → IM-only audit (levels 3, 4)

### 3. Execute

Run compliance event per `.claude/references/aras-compliance/compliance-event-protocols.md`
with context `aras-audit`.

If full audit: levels 1, 2, 3.
If IM-only audit: levels 3, 4.

Scope: all surfaces.

### 4. Report

Output audit results to managing developer:

```
[aras-audit: COMPLETE]

Audit type: [full / IM-only]
Level 1: [pass/fail/skipped]
Level 2: [pass/fail]
Level 3: [pass/fail]

Overall: [COMPLIANT / NONCOMPLIANT]
```

If any level failed, include findings summary from the
compliance event protocols output.
