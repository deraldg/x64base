# Tier 1 seed -- maintenance contract

    status      : demoted out of AI_TIER1_SEED_V1.md, 2026-08-06 (AIF-090 D4)
    owns        : labtalk/ai_portal/AI_TIER1_SEED_V1.md
    gate        : tools/staging/check_seed_budget.py
    lane        : docs/maintenance/X64BASE_AGENT_SKILL_PLDC_LANE_V1.md

This is the governance for the Tier 1 seed. It was demoted out of the seed
itself because it is instruction for the seed's MAINTAINER, not an invariant an
acting agent needs in order to be safe -- and because the seed was 798 B over
the very ceiling this contract declares. Demoting it is the procedure this
contract prescribes, applied to itself.

The text below is MOVED, not restated. The seed carries a pointer here.

---

## The contract

Always-read surfaces amplify whatever they contain, correct or stale, with no
retrieval friction to slow a bad fact down. **Delivery is not accuracy.**

- **Two admissible content classes only:** *invariants* (change only by
  deliberate decision, break work if wrong) and *pointers* to generated or gated
  artifacts.
- **No perishable literal.** No versions, counts, dates, lane states, or
  measurements. If an agent can cheaply measure it, say "measure it".
- **8 KB hard ceiling.** Adding requires removing or demoting to the trigger
  index -- and demoting means *moving*, not restating. Without the ceiling this
  becomes the corpus it was extracted from.
- **A rule that gains a hard-failing gate demotes out.** The gate is the memory.
- Vendor shims (`CLAUDE.md`, `AGENTS.md`) **point here**, never restate. Two
  shims that restate will diverge, and have.

Rationale: a cold session measured the entry path at roughly 128 KB, then found
the fix for its own worst mistake in a handoff never put in the tree. Content
quality was never the problem; rules arrived when they were not actionable and
were absent when they were. Lane:
`docs/maintenance/ONBOARDING_COST_AND_ACCEPTANCE_LANE_V1.md` (AIF-082).

## The ceiling is now a gate, not a habit

`tools/staging/check_seed_budget.py` reads the budget FROM the seed's own header
and fails when the file exceeds it. Before that gate existed the ceiling was
enforced by whoever happened to be watching, and `AI_PORTAL.md` cites it as the
project's exemplar of a bounded metric:

> "A bounded metric is a gate; the Tier-1 seed's 8,192-byte ceiling caught its
> author three times in one sitting, which an unbounded byte count would not
> have done once."

It caught its author because its author was watching. Measured 2026-08-06 by a
cold outside runner, months of unwatched edits later: 8,990 B. Over by 798, and
nothing had noticed. That is the contract's own fourth bullet arriving as
evidence -- a rule without a hard-failing gate is a wish, and this one held no
better than any other.

The gate hardcodes no number. It parses the `budget` line from the document, so
the rule travels with the document that owns it and any future budgeted document
is covered without a code change.

## What may go back INTO the seed

Only an invariant or a pointer, and only if something else comes out. The
ceiling is the forcing function; the trigger index is where displaced material
goes. If you find yourself wanting to add a paragraph of explanation, that
paragraph belongs behind a pointer and the seed gets one line naming when to
follow it.
