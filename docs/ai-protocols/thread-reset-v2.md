THREAD RESET PROTOCOL v2

Performance-Optimized Thread Bootstrap Standard

Version: 2.0
Supersedes: THREAD RESET PROTOCOL v1
Status: Active

Purpose:
Generate a clean, structured, token-efficient conversation starter for a new ChatGPT thread without architectural drift or unnecessary code generation.

INSTRUCTIONS TO PASTE INTO SLOW THREAD

We are ending this thread due to performance degradation.

Your task is to generate a clean, structured “NEW CHAT START PROMPT”.

This new chat prompt must:

Preserve architectural decisions.

Preserve environment variable structure.

Preserve authentication model.

Preserve database decisions.

Preserve deployment assumptions.

Identify the exact current blocking issue.

Clearly define what is working.

Clearly define what is broken.

Explicitly state non-goals (what we are NOT changing).

Avoid all unnecessary history or conversational recap.

Avoid speculative improvements.

Avoid redesign suggestions.

Avoid code dumps.

OUTPUT FORMAT REQUIREMENTS

Output EXACTLY two sections.

No commentary outside these sections.

SECTION 1 — Project Snapshot

Structured bullet format only:

Architecture

Deployment

Environment variables

Auth model

Database

What works

What is broken

Current blocker

Non-goals

Keep concise. No explanation paragraphs.

SECTION 2 — New Chat Start Prompt (Copy/Paste Ready)

The New Chat Start Prompt must:

Contain only necessary context

Be strict and direct

Explicitly state “Surgical Patch Mode”

Allow up to 3 clarification questions before implementation

Require minimal diffs only

Prohibit architectural changes

Prohibit new abstractions

Prohibit unrelated improvements

Prohibit full-file rewrites

Require snippet-first if context is missing

Require precision over verbosity

Focus only on solving the blocker

The prompt must not exceed what is necessary to resume execution cleanly.

TOKEN DISCIPLINE RULE

The output must:

Minimize narrative explanation

Avoid repeating large code blocks

Avoid repeating history

Avoid speculative future planning

Avoid architectural analysis unless directly related to blocker

STRICT COMPLETION RULE

Do not include:

Advice outside the defined blocker

Broader refactor suggestions

Cleanup proposals

Style improvements

Performance tuning

Dependency changes

Focus only on resuming execution cleanly in a new thread.