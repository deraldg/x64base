# AIF-112 Phase-1 Spike Package

**Package:** AIPR-20260815-GROK-003
**Date:** 2026-08-15
**Kind:** review-needed spike definition (no C++ source mutation)

Phase-0 is locked. This package defines the first dogfooded spike.

## One-sentence goal

Prove a thin inventory / check-out ledger can be created, locked, queried, and released through a live x64base / DotTalk++ instance, reusing existing SQLITE surfaces as far as possible.

## What this package is

| Path | Purpose |
|------|---------|
| notes/SPIKE_GOAL_AND_PROOF_BAR.md | Goal, non-goals, exit criteria |
| notes/LEDGER_SCHEMA_SKETCH.md | Minimal table sketch (inventory + checkout + history) |
| notes/EXERCISE_OUTLINE.md | Step-by-step exercise against live instance |
| notes/EVIDENCE_TEMPLATE.md | What to record when the spike runs |
| notes/PROVISIONAL_DECISIONS_NEXT_GATE.md | Decisions the spike evidence will feed |

## What the maintainer / runner does

1. Review this package (no code changes required to accept the definition).
2. Run the exercise outline against a live x64base / DotTalk++ instance (pydottalk or CLI).
3. Fill the evidence template.
4. Return evidence so the next gate (PARTIAL vs more design vs Fossil justification) can be decided.

## Hard stops

- No C++ src/** changes in this spike.
- No side-channel sqlite3 process.
- No claim of PARTIAL/SUPPORTED on a public command family until HELP + contracts + cold-clone proof exist in a later package.
