# The Psychology of Systems Implementation

**Status: PLACEHOLDER -- NOT DRAFTED.** This file reserves the topic and records
the seed. It contains an outline and a materials list, and **no argument has been
made yet**. Nothing here is quotable, citable, or ready for review.

Owner: Derald Grimwood (member.derald). Placeholder opened 2026-08-16 at the
owner's request; scaffolded by Claude / Cowork (member.ai.claude.cowork).
The thesis is the owner's to state and has not been stated.

Why the status line is that emphatic: this project spent 2026-08-16 finding an
empty `include/devref.hpp` that declared `status: supported` and was named in the
Tier 1 seed as a working reference authority -- documented as real for months
because nothing distinguished "empty" from "fine". A placeholder that does not
announce itself becomes exactly that. See
`labtalk/registries/proofs.d/proof.tooling.catalog_state_blindness.yaml`.

## The seed

Systems implementation fails and succeeds for human reasons at least as often as
technical ones. The engineering literature is thorough on architecture and thin
on why a correct system is rejected, why a wrong one is defended, and why a
maintainer's own judgement degrades in predictable directions under load.

## Candidate questions, not yet answers

These are prompts for the owner, deliberately phrased as open questions. None is
a claim.

- **Why is a green check believed?** A passing test is emotionally different from
  a passing test that has been seen to fail. What does it cost to hold that
  distinction, and why do practitioners stop paying it?
- **Why is absence read as health?** A missing warning, an empty catalog, a quiet
  build. Silence gets scored as success because success is what silence resembles.
- **Why is frustration misread as failure?** Slow, painful progress can sit on a
  steep learning curve. What makes the practitioner conclude the opposite?
- **Why is a documented option not an honoured one?** Writing a rule down feels
  like enforcing it. It is not the same act.
- **What does a guard teach the person it blocks?** A guard that refuses a safe
  operation trains the operator to disable it, and the bypass generalises to
  every check behind the same hook.
- **Whose resistance is it?** Adoption failure is usually described as the users'
  psychology. How much of it is the implementer's?
- **What changes when a coworker is an agent?** Trust, verification appetite, and
  the felt cost of checking all move. In which directions?

## Material already in this tree

The unusual asset here is that the project has been recording its own failures in
machine-readable form for months. This paper would not need new fieldwork so much
as a reading of what is already written down.

- `labtalk/registries/lessons.d/` -- 16 lessons, of which the `career.*` set is
  almost entirely psychological rather than technical:
  `a_script_never_run_is_not_evidence`, `a_wrong_answer_that_looks_right`,
  `a_documented_option_is_not_an_honoured_option`,
  `a_gitignored_path_is_invisible_to_your_sweep`, `the_tree_already_has_it`.
- `labtalk/registries/proofs.d/` -- proof fragments that record the moment a
  belief was corrected, several of which name the author of the fix as the
  author of the defect.
- `docs/maintenance/SESSION_CLOSEOUT_*.md` -- dated closeouts carrying an errors
  section by convention. A longitudinal record of how a single practitioner got
  things wrong, written at the time rather than in recollection.
- `WHITE_PAPER_JULY14_REGIME_CHANGE_V1.md` -- measured throughput data.
- `WHITE_PAPER_AI_ACCELERATION_PLANNING_V1.md` -- section 3.2, "Frustration is
  not failure", is arguably the first paragraph of this paper and may belong here
  instead.

## Proposed shape, to be confirmed or discarded

1. Abstract
2. The problem: implementation as a human process
3. Belief and evidence -- why a green check is trusted
4. Silence as false comfort
5. The implementer's own psychology, including frustration and sunk cost
6. Resistance, adoption, and whose it actually is
7. Human-agent teams: what changes when a coworker is not a person
8. What the record shows -- reading this project's own lessons and closeouts
9. Practices that survive contact with human nature
10. Limits: one practitioner, one project, no control group

## Honest limits, to be stated in the paper itself

A single maintainer on a single project is a case study, not evidence about
software engineering generally. Whatever this paper concludes, it should say
plainly that it is one person's record examined carefully -- which is worth
something precisely because the record was kept at the time and not
reconstructed afterwards.

## Publication

If drafted and approved, publication rides the website matrix and the full-stack
flush pipeline, as with the other papers in this directory. Until then this file
is a reservation and nothing more.
