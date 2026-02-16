# THREAD RESET PROTOCOL v1

Purpose:
Generate a clean, structured, performance-optimized conversation starter for a new ChatGPT thread.

---

Paste the following into the slowing thread:

We are ending this thread due to performance degradation.

Your task is to generate a clean, structured “NEW CHAT START PROMPT”.

This new chat prompt must:

1. Preserve architectural decisions.
2. Preserve environment variable structure.
3. Preserve authentication model.
4. Preserve database decisions.
5. Preserve deployment assumptions.
6. Identify the exact current blocking issue.
7. Clearly define what is working.
8. Clearly define what is broken.
9. Explicitly state non-goals (what we are NOT changing).
10. Avoid all unnecessary history or conversational recap.

Output EXACTLY two sections:

SECTION 1 — Project Snapshot  
- Architecture  
- Deployment  
- Environment variables  
- Auth model  
- Database  
- What works  
- What is broken  
- Current blocker  

SECTION 2 — New Chat Start Prompt (copy/paste ready)

The New Chat Start Prompt must:
- Contain only necessary context
- Be strict and direct
- Allow optional clarification questions
- Prevent architectural drift
- Focus only on solving the blocker

Do not include commentary outside those two sections.
Be precise.
