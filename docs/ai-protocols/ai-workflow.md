# AI-Assisted Development Workflow

Purpose:
Use ChatGPT for planning/review and Copilot for scoped implementation.

---

## Standard Loop

1. Ask ChatGPT for plan or diagnosis.
2. Say: “Use COPILOT_PROTOCOL v1.”
3. Paste Copilot prompt into Copilot Chat.
4. Copilot implements and returns diff.
5. Paste diff back into ChatGPT for review.
6. Commit after validation.

---

## When Threads Slow Down

Use:
- thread-reset-v1.md
- thread-reset-surgical.md
- thread-reset-quick.md
- thread-reset-single-blocker.md

---

## Stability Lock

Use project-freeze-mode.md when preventing scope creep.