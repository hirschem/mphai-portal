# MPH AI Portal — Shipping Constraint

This is a single-client internal tool.

We optimize for:
- Stable auth
- Stable OCR
- Stable proposal generation
- Stable PDF export
- Stable save/edit persistence

We do NOT optimize for:
- Multi-tenant SaaS patterns
- Over-hardening
- Theoretical scalability
- Abstract architecture
- Future platform expansion

Guiding Constraint:
"If a change does not directly improve login stability, OCR stability, PDF export stability, or save/edit persistence — it does not go in."

This becomes your architectural north star.

When you drift, you re-read this file.
