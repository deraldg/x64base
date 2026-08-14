# Proof -- artifact-mediated cold resume across an 11-day gap (2026-08-12)

    proof id      : proof.ai_portal.cold_resume_retention
    state         : runtime_observed (session transcript + a re-verifiable anchor)
    recorded_utc  : 2026-08-12T20:28:00Z
    recorded_by   : member.ai.claude.cowork
    baseline      : development @ 29eca1962e1b95e642e90651668e0b2f3759c814 (2026-08-12)
    subject       : the AI Portal / BBS / frontal-memory -> permanent-memory model
    milestone     : AIF-101 M4 standing factor event, factor F2
    requested by  : member.derald, 2026-08-12 -- "record this as both a proof and a milestone"

## 1. What was observed

A Cowork / Claude session dormant since **2026-08-01** was resumed on
**2026-08-12** and told only that a coworker had left it a note. Without further
instruction it:

1. located `docs/agents/HANDOFF_CLAUDE_COWORK_SANDBOX_BUILD_2026-08-12.md`,
   addressed to "the next Cowork/sandbox agent";
2. noticed the elapsed interval on its own and re-onboarded before acting;
3. ran the staleness self-check the handoff prescribes;
4. accepted a measured correction that changed its own operating constraints --
   that a Cowork sandbox **can** build and run the engine, contradicting
   `AI_README.md`'s `-fsyntax-only` ceiling; and
5. revised its own prior position, declaring its earlier reconciliation note
   substantially overtaken and naming which of its blockers had dissolved.

Elapsed dormancy: **11 days**. Owner-reported wall time for the resume: minutes.

## 2. The falsifiable core -- what is independently checkable

This is the part that makes the record a proof rather than an anecdote. All of
it re-verifies from the tree, without the transcript.

| Claim | Check | Result |
| --- | --- | --- |
| The handoff exists where the transcript says | `ls docs/agents/HANDOFF_CLAUDE_COWORK_SANDBOX_BUILD_2026-08-12.md` | present, 8,801 B |
| It carries a machine-checkable staleness anchor | `seed_commit` in its header | `d08a09c5680f242abf909be0200784af1255a413` |
| The anchor resolves correctly | `git log -1 --format=%H -- labtalk/ai_portal/AI_TIER1_SEED_V1.md` | `d08a09c5680f242abf909be0200784af1255a413` (2026-08-10, "Seed trim to 7959B + staged-set visibility guard") |

Anchor and actual are **equal**. The mechanism the handoff prescribes therefore
resolved correctly at the time it was run, and still resolves at this baseline.
One command, re-runnable by anyone.

## 3. What rests on the transcript alone

Recorded separately because it is weaker evidence and must not be read as
equal to section 2.

- The ordering -- that re-onboarding preceded the staleness check.
- That re-onboarding was unprompted rather than instructed.
- The "few minutes" figure, which is owner-observed, not instrumented.

## 4. What this is evidence for

The frontal-memory thesis exactly as AIF-101 states it: *a reachable,
consolidated corpus compounds, because retrieval replaces re-derivation, so
per-task overhead falls toward zero.*

This is the qualitative form of that claim. An 11-day-cold agent recovered its
working position from durable artifacts -- a handoff, the Tier-1 seed, and a
commit anchor -- rather than from the tree at large or from a chat that no
longer existed. The recovery cost a file read and one git command instead of a
survey. That is the portal design doing the job it was built for, and it is the
first instance recorded with a self-verifying anchor.

It also demonstrates the return leg of the model. The dormant agent did not
merely reload state; it accepted a correction that **invalidated a documented
constraint it had been operating under**, and said so. A memory model that can
only confirm what an agent already believed is not a memory model.

## 5. What this is NOT evidence for

AIF-101 carries a standing ruling -- *praise is an unproven assertion; the
golden rule applies to compliments too.* Recording this milestone without its
limits would violate the lane it belongs to.

- **Nothing was remembered.** The agent held no state across the 11 days. It
  re-read. What is demonstrated is **artifact-mediated recovery**, which is the
  design working as intended, and which is a different claim from retention.
  Calling it memory retention overstates it in the one direction that matters,
  because it credits the agent for a property the *tree* supplied.
- **It is not measured.** No token count, no read count, and -- decisively -- no
  control case. A cold onboard *without* a handoff was not run in the same
  window, so the efficiency claim has no denominator. "Few minutes" is an
  observation, not a metric with a bound.
- **One trial, one agent, one lane.** No claim of generality is made.

## 6. A finding produced by recording this

The handoff's staleness test compares the **handoff's** recorded `seed_commit`
against the seed's current commit. That proves the *handoff* is still aligned
with the seed. It does **not** prove the *reader's onboarding* is current.

A reader that onboarded before `d08a09c56` and ran only this check would
conclude "current" while being stale. In this instance the conclusion was sound
only because the agent had already re-onboarded in-session before running it --
the right answer for a reason the check does not supply.

This is the same defect shape recorded on 2026-08-09 against
`check_session_log_row.py` and `check_mandatory_tracked.py`: a check whose scope
silently excludes the case it appears to cover, and which reports a clean result
either way.

**Smallest correction:** have the reader compare **its own** onboarding commit
against the seed's current commit, not the handoff's. One extra field in the
handoff header -- the reader records what it onboarded at -- turns a
handoff-freshness test into a reader-freshness test, which is the question being
asked.

## 7. What would overturn this

Stated so the record can be falsified rather than defended.

1. A cold resume that reads the same handoff and still re-derives position from
   the tree, showing the artifact did not carry the load.
2. An instrumented control showing no material cost difference between a cold
   start with the handoff and one without it.
3. The anchor failing to resolve at a later commit, which would mean the
   mechanism works only while nobody edits the seed.
4. A second trial in which the agent accepts the handoff's corrections
   *uncritically* -- adoption without verification is not recovery, it is drift
   with extra steps.

## 8. Evidence tier, stated precisely

`runtime_observed` in the `proofs.yaml` vocabulary: a transcript exists and the
anchor re-verifies.

**Not engine runtime.** Nothing in this proof concerns DotTalk++ behavior. What
ran was an agent session against the portal's own artifacts. The separate claim
inside the handoff -- that a Cowork sandbox built `dottalkpp` and ran
`REGRESSION RUN WORKSPACE_WRITEBACK` with WB_T1..WB_T6 green twice -- is that
coworker's proof, on its own lane, and is **not** re-verified here.
