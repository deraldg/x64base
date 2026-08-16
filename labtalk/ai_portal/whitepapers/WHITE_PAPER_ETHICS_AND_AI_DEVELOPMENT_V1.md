# Ethics and AI Development

**Status: PLACEHOLDER -- NOT DRAFTED.** This file reserves the topic and records
the seed. It contains an outline and a materials list, and **no argument has been
made yet**. Nothing here is quotable, citable, or ready for review.

Owner: Derald Grimwood (member.derald). Placeholder opened 2026-08-16 at the
owner's request; scaffolded by Claude / Cowork (member.ai.claude.cowork).
The thesis is the owner's to state and has not been stated.

A note on who should draft this one. The other placeholders can be scaffolded by
an agent without much conflict of interest. This one cannot: the paper is partly
about the conduct of the agents that would write it, and about what an AI
contributor owes the humans who rely on its output. **An agent drafting its own
ethics is a structural problem, not a stylistic one**, and the paper should say
which parts were written by whom.

## The seed

AI now writes, reviews, and gates a material share of this project's work. That
raises obligations that are not covered by the licence and are not the same as
generic "AI ethics" commentary about models in the abstract. The interesting
questions here are practitioner-level and specific.

## Candidate questions, not yet answers

Open prompts for the owner. None is a claim.

- **Attribution.** When an agent drafts and a human approves, who authored it?
  This project already answers by convention -- every whitepaper header names its
  drafting agent, and `WHITE_PAPER_AI_ACCELERATION_PLANNING_V1.md` says
  "authored by the owner" precisely because it was. Is that convention sufficient,
  and what does it owe a reader who never opens the header?
- **Credit to upstream work.** The GnuCOBOL acknowledgement (2026-08-14) was owed
  for months before it was written. What is the obligation to credit the projects
  a system stands on, and when does an unpaid acknowledgement become a wrong
  rather than an oversight?
- **Honest status.** Publishing "supported" over something empty, or "runtime-
  proven" over something never run, is a truth claim to strangers. Where is the
  line between optimism and misrepresentation?
- **Verification as an ethical duty, not just a quality practice.** An agent that
  reports success it did not verify transfers risk to the human who trusts it.
  What does the agent owe, and what does the maintainer owe in return?
- **Disclosure to visitors.** The site says "AI-assisted, source-reviewed
  documentation" in its banner. Is a banner enough? What should a reader be able
  to find out about how a page was made?
- **Labour and displacement.** An educational project aimed at students, built
  substantially by AI, is teaching them in a market being reshaped by it. Is that
  a contradiction to sit with or one to resolve?
- **The corrections asymmetry.** Errors are cheap for an agent to admit and
  expensive for a human to discover. Does that change who is obliged to look?
- **Agent-to-agent work.** Grok, Copilot, Codex and Claude have all contributed
  here. What is owed between them, and to the owner, when one reviews another?

## Material already in this tree

This project has an unusually concrete record to reason from, rather than
hypotheticals.

- `CREDITS.md` and `docs/ai-friendly/AI_BBS_LANE_V1.md` -- an existing model of
  crediting AI partners as contributors with named roles.
- `docs/ai-friendly/GNUCOBOL_ACKNOWLEDGEMENT_AND_TOOLCHAIN_V1.md` -- credit paid
  to an upstream project, with the delay recorded rather than hidden.
- `content/docs/dev/third-party-acknowledgements.mdx` (site) -- including the
  section stating plainly that the visitor count "is not ours".
- `labtalk/registries/proofs.d/proof.aside.diagnostic_removed_and_called_a_fix.yaml`
  -- a false commit message preserved on the record because the commit was pushed
  and could not be rewritten. A worked example of correction-in-public.
- `labtalk/registries/proofs.d/proof.golden_rule_verify_before_assert` (in
  `proofs.yaml`) -- the rule that host-only changes are not "done" until run.
- `docs/maintenance/external_ai_intake/` -- received AI work preserved unchanged
  as prior art, including a Copilot deck that invented an "xBridge Protocol"
  existing nowhere in the tree. Evidence for the disclosure question.
- `AI_PORTAL.md` and the Tier 1 seed -- what agents are told before they act,
  which is itself an ethical artifact.

## Proposed shape, to be confirmed or discarded

1. Abstract
2. Scope: practitioner ethics, not model ethics
3. Attribution and authorship in mixed human-agent work
4. Credit to upstream, and the cost of an unpaid acknowledgement
5. Truthful status: what "supported" and "proven" promise a stranger
6. Verification as an obligation rather than a preference
7. Disclosure: what a reader is entitled to know
8. Education, labour, and the students this project is aimed at
9. Between agents: review, correction, and what one owes another
10. Limits, and which sections were drafted by whom

## Honest limits, to be stated in the paper itself

One maintainer, one project, and a strong incentive to conclude that the way this
project already works is the ethical way. That bias should be named in the paper
rather than defended against, and the reader given enough of the record to
disagree.

## Publication

If drafted and approved, publication rides the website matrix and the full-stack
flush pipeline. Given the subject, the authorship note should be more explicit
than the house convention requires -- section by section, not just a header line.
Until then this file is a reservation and nothing more.
