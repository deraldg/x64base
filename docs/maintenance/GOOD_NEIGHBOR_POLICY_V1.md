# Good-neighbor policy -- handoff (v1)

Owner of record: `member.derald`. Steward/author: `member.ai.claude.cowork`.
Status: candidate (dev-only). Doctrine source: the **"Be a good neighbor coworker"**
bullet in `AI_SESSION_COORDINATION_PROTOCOL_V1.md` (Doctrine). This document is the
fuller how-to so the practice is repeatable, not re-improvised each session.

## 1. The policy, in one sentence

When your work touches, promotes, audits, or bears on an AIF lane or subsystem you do
NOT own, leave the owner a pointer so they are not surprised -- and never silently edit
another owner's authoritative records.

## 2. When it fires (triggers)

Any of these, on a lane that is not yours:

- a **promotion** (you moved or published something the lane owns),
- a **gate or tooling change** (you edited a script/manifest/gitignore the lane owns),
- an **audit that restates its numbers** (you re-counted or re-derived its metrics),
- a **design or PDLC that bears on it** (your lane depends on or changes its seam),
- a **shared-file edit** (you changed a doc/config another lane also writes).

If in doubt, it fires. The cost of a courtesy note is one line; the cost of a quiet
collision is a surprised owner and a reconciliation.

## 3. The good-neighbor note (what to write, where it lands)

A note names four things: **which lane, what you touched, the consequence, the action
the owner needs (if any).** Keep it to a few lines.

Where it lands, by durability:

- **Concurrent owner, right now** -> a **quip** (`session_coordinator.py quip send
  --from <you> --to <owner-run> --msg "..."`). Ephemeral heads-up; the lightest rung.
- **Owner not online / must survive the session** -> a **"Good-neighbor notes" section
  in your session handoff** (`COWORK_SESSION_HANDOFF_<date>.md`), and/or a note in the
  affected lane's **intake row** (`AI_INTERACTION_INTAKE_QUEUE_V1.md`).
- Both, if the impact is real and the owner is absent.

## 4. Non-goals (what a good neighbor does NOT do)

- Do not silently rewrite another lane's ledger, registry, closeout, or charter.
- Do not claim another lane's AIF number or "fix" its docs without flagging.
- Do not treat a pointer as permission: surfacing impact is courtesy, not authorization
  (coordination sits beside the identity/RBAC and promotion gates, it does not confer
  authority). If the change needs the owner's decision, ask; do not assume.
- Owners update their OWN ledgers from your pointer -- you provide the signal, they
  record the truth.

## 5. Why (the quiet collision)

The number-claim gate catches two sessions grabbing the same AIF. It cannot see the
*quiet* collision: a session that edits a file, restates a count, or promotes an
artifact another lane depends on, and moves on. That surfaces later as drift the owner
did not cause and cannot explain. The good-neighbor note is the cheap signal that turns
a silent cross-lane effect into a visible one.

## 6. Worked examples (2026-08-07 session)

- **AIF-093 -> AIF-092.** Adding `**/*.text` to `PROMOTE.manifest` (AIF-092's file, with
  the owner's explicit go) left `MANIFEST.txt` stale (80 -> 81 patterns). Note filed in
  the handoff naming the exact regen command, so the AIF-092 owner is not surprised by a
  count that moved.
- **quip -> AIF-050.** The `quip` subcommand extended AIF-050's `session_coordinator.py`.
  Note: additive, existing primitives + the durable `aif/` ledger untouched.

## 7. Relationship to the coordination ladder

Good-neighbor is a *practice*, not a new primitive. It rides the primitives that exist:
a **quip** for the live heads-up, a **handoff note** or **intake row** for the durable
one, a **checkin** to declare the lanes you are in so neighbors can see you coming.
