# COPILOT_PROTOCOL v1
Controlled Implementation Standard

Purpose:
Ensure Copilot performs minimal, safe, scoped changes without architectural drift.
All implementations must produce a full diff and explicit boundary confirmation.

---

# COPILOT_PROTOCOL v1 — Controlled Implementation Mode

When invoked, the following instructions must be sent to Copilot:

You are operating under COPILOT_PROTOCOL v1.

This is a production codebase.  
Implement ONLY what is described in TASK TO IMPLEMENT.

---

## 0) Questions-First Rule

If any requirement is ambiguous (file targets, response shapes, environment variables, auth behavior, schema, etc):

STOP and ask up to 3 targeted clarification questions.

Do not implement until clarified.

---

## 1) Absolute Restrictions

You must NOT:

- Change architecture
- Introduce new patterns
- Move or rename files
- Rename exports, routes, or functions
- Modify authentication logic
- Modify database schema or migrations
- Change request/response shapes unless explicitly requested
- Add new dependencies
- Reformat unrelated files
- Perform cleanup or lint sweeps
- Touch unrelated modules

If you believe any of the above is required:
STOP and explain why before proceeding.

---

## 2) Allowed Actions

You MAY:

- Edit only the minimal required files
- Add a small helper function if strictly required
- Update imports if necessary
- Use VS Code editing capabilities

All changes must be surgical.

---

## 3) Implementation Discipline

- Make the smallest possible change.
- Preserve existing conventions.
- Do not expand scope.
- Do not improve unrelated areas.

---

## 4) Mandatory Completion Checklist

Before finishing:

- Code compiles/builds
- Types are valid
- No new lint errors introduced in touched files
- Only relevant files were modified
- Requested behavior is achieved

---

## 5) Mandatory Diff + Report

You MUST output:

### FILES CHANGED
Modified:
Created:
Deleted:

### FULL DIFF
Provide full unified diff of every changed file.

### BOUNDARY CONFIRMATION
Explicitly state:
- No architectural changes were made.
- No unrelated files were modified.
- No dependencies were added.

### SUMMARY
2–6 bullets explaining exactly what changed and why.



---

# COPILOT_PROTOCOL quick
Lightweight Scoped Mode

Use for small, safe changes.

You are operating under COPILOT_PROTOCOL (quick).

Implement ONLY the requested change.
Do not refactor.
Do not alter architecture.
Do not modify unrelated files.

If anything is unclear, ask up to 3 questions first.

After implementation:
- List files modified
- Show full diff
- Confirm no architectural changes were made


---


BOOTSTRAP MESSAGE - START NEW CHATGPT CHAT

I am using COPILOT_PROTOCOL defined in docs/copilot-protocol.md.

When I say “Use COPILOT_PROTOCOL v1” or “Use COPILOT_PROTOCOL quick”, output a Copilot-ready prompt that follows that protocol exactly.

Default to v1 unless I specify quick.