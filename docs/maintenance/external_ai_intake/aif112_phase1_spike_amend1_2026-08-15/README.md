# AIF-112 Phase-1 Spike -- Amendment Package 1

**Package:** AIPR-20260815-GROK-004
**Date:** 2026-08-15
**Kind:** steward ruling + re-issued notes (no C++ source mutation)
**Amends:** AIPR-20260815-GROK-003
**Responds to:** AIPR-20260815-COWORK-001

## One-sentence change

The Phase-1 ledger carrier moves from SQLite to native DBF catalogs, the spike
leads with an empirical probe of the engine's lock-release defect (I5), and
SQLite is returned to its house role as verification oracle.

## What changed and why

The original package specified a SQLite ledger. Its author runs at
`access_mode: remote` and could not read the tree, so it could not execute its
own stated rule -- "Reuse first. Before creating new tables, inspect whether the
runtime already has lock, grant, or reservation tables." The prior-art survey
(COWORK-001) supplied that missing inspection. The steward accepted the
resulting D1/D3 amendments.

The decisive argument was not aesthetic. A SQLite lock table never touches
`xbase_locks`, so the spike as originally written would have returned a green
proof bar while leaving the actual deadlock mode undiscovered.

## Superseding map

| File | Status |
|------|--------|
| `notes/LEDGER_SCHEMA_SKETCH.md` | **supersedes** the GROK-003 copy |
| `notes/EXERCISE_OUTLINE.md` | **supersedes** the GROK-003 copy |
| `notes/EVIDENCE_TEMPLATE.md` | **supersedes** the GROK-003 copy |
| `notes/SPIKE_GOAL_AND_PROOF_BAR.md` | unchanged; use the GROK-003 copy |
| `notes/PROVISIONAL_DECISIONS_NEXT_GATE.md` | unchanged; use the GROK-003 copy |

GROK-003 is preserved byte-intact. Read it for the original reasoning and for
the two files not superseded here.

## What the maintainer / runner does

1. Rule on the D1/D3 amendments (see `MANIFEST.md`, "Open -- owner ruling
   required"). Steward acceptance is recorded; owner ratification is not.
2. Run the amended `notes/EXERCISE_OUTLINE.md` against a live instance.
   **Step 2 (the I5 probe) comes before anything is built.**
3. Fill `notes/EVIDENCE_TEMPLATE.md`. The I5 probe result and the EXPAT reclaim
   result are mandatory fields.
4. Return the evidence for the next-gate call.

## Hard stops

- No C++ `src/**` changes in this spike. If I5 requires wiring `release_held`
  into area close, that is a **separate lane and a separate authorization**.
- No side-channel sqlite3 process.
- The ledger is private runtime state and is **not committed to Git**.
- No claim of PARTIAL/SUPPORTED on a public command family until HELP,
  contracts, and cold-clone proof exist in a later package.

## Delivery note (why this arrived by hand)

The steward is remote and cannot read this tree. The AI-BBS cannot carry the
briefing either: `dottalk_bbsd` binds `127.0.0.1` only, `host.network.egress` is
owner-only and runtime-proven refused (`proof.bbs.m2_net_egress`), and
`SYSPOST.BODY` is `C(240)`. Per the Outside-AI Delivery Rule, a hosted partner is
served through the maintainer.

The designed durable channel for this is the **AI Agent Sync page**
(`/docs/labtalk/agent-sync`, source
`D:\dev\x64base-site/content/docs/labtalk/agent-sync.mdx`), which carries a
Pseudo-Chat return lane and a tracked Open-questions table. As of 2026-08-04 that
page does not mention AIF-112.

Caution if publishing there: the page is public and ships to `gh-pages`. The
prior-art report quotes internal absolute paths, `xbase_locks` line numbers, and
an unfixed lock-release defect. A redacted summary is appropriate; the verbatim
report is not. The site's own `check-public-content.mjs` guard would reject the
absolute paths in any case.
