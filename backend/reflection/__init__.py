"""Post-event reflection package. Reads our predictions + actual outcomes,
computes deterministic scoring, then runs three Opus passes to turn recurring
prediction errors into a per-agent lessons corpus that injects into future
specialist prompts.

See docs/superpowers/specs/2026-05-11-post-event-reflection-design.md.
"""
