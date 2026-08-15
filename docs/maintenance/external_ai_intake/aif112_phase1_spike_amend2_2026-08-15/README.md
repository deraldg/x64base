# AIF-112 Phase-1 Spike -- Amendment Package 2

**Package:** AIPR-20260815-GROK-005
**Date:** 2026-08-15
**Kind:** steward ruling + re-issued notes (no C++ source mutation)
**Amends:** AIPR-20260815-GROK-004
**Responds to:** AIPR-20260815-COWORK-002

## One-sentence change

The I5 lock-release defect is demoted from Phase-1 gate to opportunistic evidence
routed to a separate engine lane; attribution matches the WORKSPACES string stamp
rather than a foreign key; and the exercise outline is re-ordered to lead with the
reuse audit instead.

## What changed and why

COWORK-002 mounted `src/` and `include/` read-only and found that every lock
acquisition in the tree falls into one of two classes. **Class A** releases within
the same operation -- `bbs_store` and `cmd_workspace` via RAII destructors, plus
the paired acquire/release sites in `append_support` and the six single-write
commands. **Class B** holds across operations, and consists of `cmd_lock.cpp`
alone, which contains no `unlock` call at all.

The inventory ledger is Class A. It takes a table FLOCK around a check-and-append
and releases it in the same scope, because a check-out is a row rather than a held
lock. I5 therefore cannot leak it, and the defect belongs to a different lane.

This reverses the priority COWORK-001 set, on the scribe's own initiative and by
the scribe's own correction. D1 and D3 are untouched.

## Superseding map

| File | Status | Authored by |
|------|--------|-------------|
| `notes/EXERCISE_OUTLINE.md` | **supersedes** GROK-004 | steward, verbatim |
| `notes/EVIDENCE_TEMPLATE.md` | **supersedes** GROK-004 | scribe-applied delta (steward sec. 5) |
| `notes/LEDGER_SCHEMA_SKETCH.md` | **supersedes** GROK-004 | scribe-applied delta (steward sec. 2, 3) |
| `notes/SPIKE_GOAL_AND_PROOF_BAR.md` | unchanged | use the GROK-003 copy |
| `notes/PROVISIONAL_DECISIONS_NEXT_GATE.md` | unchanged | use the GROK-003 copy |

GROK-003 and GROK-004 are preserved byte-intact.

**Read the MANIFEST section "Scribe-applied deltas" before trusting the two
delta files.** It itemizes every change and the quoted ruling authorizing it. The
steward ruled in prose on those two files without re-issuing them; the scribe
carried the rulings out and is on the record for having done so.

## What the maintainer / runner does

1. Rule on the eight open items in `MANIFEST.md`. Items 1 and 2 (D1/D3) still gate
   the ledger steps.
2. Run `notes/EXERCISE_OUTLINE.md` in the order given -- **reuse audit first**,
   not the I5 probe.
3. Fill `notes/EVIDENCE_TEMPLATE.md`. The EXPAT reclaim result is mandatory; the
   I5 result is optional.
4. Return the evidence. Split of labour agreed: the steward scores it against the
   proof bar, the scribe verifies the claims against the tree.

## Hard stops

- No C++ `src/**` changes in this spike. The engine recovery work
  (`release_held`, `force_unlock_table`, `force_unlock_record`) is a **separate
  lane and a separate authorization**.
- No side-channel sqlite3 process. SQLite is the oracle only.
- The ledger is private runtime state and is **not committed to Git**.
- No claim of PARTIAL/SUPPORTED on a public command family until HELP, contracts,
  and cold-clone proof exist in a later package.

## Two things this package does not settle

**Attribution is a recommendation, not a lock.** The steward recommends the string
stamp for Phase-1 and explicitly leaves normalization to the owner. If the owner
wants `N(20)` FK to `SYSMEMBER`, the sketch changes before the run, not after.

**`USER` is `status: experimental`.** Attribution and permission gating bind to the
identity stack via `cmd_user.cpp`, which is experimental, while `BBS` and `NET` are
supported. AIF-112 would be binding a would-be supported feature to an experimental
surface. Raised in COWORK-002 section 7; not yet ruled on.

## Delivery note

The steward is `access_mode: remote` and cannot read this tree. The AI-BBS cannot
carry the briefing either -- `dottalk_bbsd` binds `127.0.0.1` only,
`host.network.egress` is owner-only and runtime-proven refused, and `SYSPOST.BODY`
is `C(240)`. Per the Outside-AI Delivery Rule, a hosted partner is served through
the maintainer. Transmission artifact:
`docs/maintenance/AIF112_STEWARD_HANDOFF_2_FOR_TRANSMISSION_V1.md`.
