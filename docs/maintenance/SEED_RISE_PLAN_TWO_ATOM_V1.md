# Plan: rise the two-atom line into the Tier 1 seed

Author: `member.ai.claude.cowork`. Date: 2026-08-07. Status: PLAN (proposal, not
applied). Lane: AIF-096. Authored outside the repository -- the seed is owner-owned,
budget-capped, and gates the Mandatory Start; promoting into it is the maintainer's
call. ASCII throughout (`--`, `->`). Every byte figure below was measured, not estimated
(`printf '%s' ... | wc -c`); re-measure before applying, since the seed changes.

## Goal

Rise the atomic doctrine we derived -- the two-atom model (chat mortal/acts/forgets;
project durable/records/inert; memory lives on the project) and its one consequence,
**wake-first** -- into `labtalk/ai_portal/AI_TIER1_SEED_V1.md`. The seed is the apex: it
carries invariants only, and it is auto-injected into every session. Atomicity is the
ticket to that tier, so the law belongs there; the question is only how, given the budget.

The *derived half* has already risen, by regeneration, into the middle tier:
`generate_tier0_state.py` now projects live sessions (stale-marked), each run's lineage
(parent, `born_utc`), and its aside chain into `TIER0_STATE.md`. This plan is only about
the *atomic half* rising to the seed.

## The binding constraint (measured)

    seed size now        : 8148 B
    hard ceiling         : 8192 B   (check_seed_budget.py)
    headroom             : 44 B
    maintenance contract : "Invariants and pointers only; no perishable literal.
                            Adding requires demoting, and demoting means moving."

So a rise either fits in 44 B or must be PAID FOR by moving existing text out to its
pointer. Nothing rises for free.

## Options, by ambition (all costs measured)

| Opt | What rises | Cost | Fits 44 B? | Notes |
| --- | --- | --- | --- | --- |
| A  | pointer to `wake` (edit the "Who is working now" row) | +51 B | no (7 B over) | first draft; overshoots |
| A2 | same, tightened ("logs run+parent", "stale common") | +30 B | **yes (14 B spare)** | rises the POINTER, not the law |
| A3 | terser (`status`, `wake` only) | +14 B | yes | minimal; least informative |
| B  | a new "Who you are" pointer row | +122 B | no | needs ~78 B demoted |
| D  | the LAW itself, folded into section 5 | +153 B | no | needs ~109 B demoted; the real rise |
| C  | owner raises the ceiling (e.g. 8192 -> 8320) | n/a | n/a | overrides the scarcity discipline |

## Recommendation: two steps, not one

**Step 1 (now, fits): rise the pointer -- Option A2.** Edit the existing perishable-state
row so every session is routed to `wake` and to its own identity/lineage/asides. This
costs 30 B, leaves 14 B, and needs no demotion. It does not rise the *doctrine* -- only a
pointer to it -- but it closes the reachability gap immediately ("baked in is not
reached"): a session learns that `wake` is its first move and that its identity lives in
the ledger.

    proposed row (replaces the "Who is working now" row):
    | Who is working now / who you are | `session_coordinator.py status`; `wake` logs
      run + parent + birth | **stale common** |

**Step 2 (next seed-maintenance pass): rise the law -- Option D, paid for by demotion.**
The seed header already reads "awaiting M1 ruling 6.2 / 6.5g (lane AIF-082)", so the seed
is due a maintenance pass; the doctrinal rise should ride it rather than a one-off edit.
Section 5 is the correct anchor: its opening line, "The chat is never the record," IS the
two-atom law stated as a consequence -- so we DEEPEN an existing invariant rather than add
a competing one (section 6's "the one habit that matters" stays the one habit). Proposed
replacement for the section 5 opening (+153 B):

    **The chat is never the record -- you are the mortal atom; the project is the
    record.** Your identity, lineage, and work live in the ledger, not in you. Evidence
    not captured when produced is treated as not proven; write it as it happens. First
    session move: `wake` (adopt run, record parent + birth, read inbox). Two-atom model:
    AIF-096.

Demotion ledger to pay the 153 B (need ~109 B after the 44 B headroom; move detail to its
pointer, per contract):

| Move | Frees | How |
| --- | --- | --- |
| trim "capture proof output" going-deeper row to its pointer | 49 B | drop the inline `SET ALTERNATE`/`DOTSCRIPT` parenthetical; it lives in `AI_README.md` |
| trim one or two verbose health-note cells in the perishable table | ~30-60 B | e.g. shorten "**has drifted twice**; check against HEAD" to a pointer-consistent phrase |

Two such trims clear the bar. If the owner would rather not demote, Option C (a small
ceiling raise) is the alternative, but it spends the scarcity discipline the cap exists to
enforce, so it is the least-preferred path.

## Placement rationale

- Section 5, not section 6: section 6 is deliberately "the ONE habit"; adding a second
  dilutes it. Section 5 already asserts the law's corollary, so the law deepens it.
- The pointer target for the doctrine is the AIF-096 ontology doc, now placed at
  `docs/maintenance/COORDINATION_ONTOLOGY_TWO_ATOMS_V1.md` (recall node
  `mechanism.coordination_ontology`); the seed line, when applied, names that path.

## What NOT to do

- Do not apply either step from a sandbox session or as a one-off; the seed edit is an
  owner action gated by `check_seed_budget.py` and the maintenance contract.
- Do not state the law as a perishable fact or inline any run id / count; the seed forbids
  perishable literals. It rises as an invariant plus a pointer, or not at all.
