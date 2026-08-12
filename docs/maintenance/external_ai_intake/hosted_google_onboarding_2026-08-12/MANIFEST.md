# Hosted onboarding through Google, with no GitHub -- outside-runner evidence

    From:   ChatGPT (hosted web session, maintainer-operated)
    Filed:  member.ai.claude.cowork  (run AIPR-20260812-002, lane AIF-090)
    To:     the record
    Date:   2026-08-12
    Status: primary observation, transcribed from a maintainer-supplied PDF
    Lane:   docs/maintenance/X64BASE_AGENT_SKILL_PDLC_LANE_V1.md (AIF-090)
    Prior:  docs/maintenance/external_ai_intake/aif090_cold_probes_2026-08-06/

## 1. Why this package exists

`PROBE_C_NO_TREE.md` (2026-08-06) recorded that the NO-TREE arm of the AIF-090
cold probes **could not be measured**: the harness auto-injected
`D:\code\ccode\CLAUDE.md` into every subagent, so an agent claiming to work from
public sources only was in fact carrying pre-loaded answers. A fourth arm was
designed and deliberately not run for the same reason.

**This is that arm, in the wild, uncontaminated.** A real hosted ChatGPT session,
no local checkout, no harness, no injected `CLAUDE.md` -- and, notably, no
GitHub either. It reached a correct and correctly-scoped onboarding through
Google alone.

It is one run, maintainer-operated, and it was not designed as an experiment.
Treat it as a strong existence proof and a weak measurement.

## 2. Contents

| File | What it is |
| --- | --- |
| `TRANSCRIPT.md` | The session's own report, verbatim. Text extracted from the maintainer-supplied PDF `ChatGPT - BETA_Work.pdf`; normalized to ASCII per house convention, otherwise unaltered. |

## 3. Provenance, stated plainly -- SORTED BY TIER

**This is a maintainer-supplied PDF export of a hosted chat, transcribed by
Cowork.** It is not a teed capture and not a harness artifact. The original PDF
is a single page, 67943 bytes, extracted with `pypdf`.

**Corrected 2026-08-12, on maintainer challenge ("that was your claim").** The
first draft of this package repeated the session's self-report as established
fact and then reasoned on top of it. That is chat-tier output asserting
registration-tier fact -- the defect class this project already records against
the Copilot SAP fabrication, committed here by the filer. The claims are now
separated by tier and the reader should not let them blur again.

| Tier | Claim | Standing |
| --- | --- | --- |
| **Owner-attested** | A hosted web session onboarded through Google with no GitHub. | The maintainer states it directly. Highest tier available here. |
| **Verified by the filer** | The invariants the session recited match `AI_TIER1_SEED_V1.md` and `AI_PORTAL.md` as committed. | Checked against the tree at filing. |
| **Verified by the filer** | The baseline the session reported (`db04678b dirty`) lagged `development` HEAD (`b3f648288`) by several commits. | Checked against git log. |
| **CHAT-TIER, UNVERIFIED** | That it read "an August 6 cold-onboarding report". | The agent describing its own inputs. Nobody has confirmed such a document is in the channel. Could be confabulated, mis-titled, or a conflation. |
| **CHAT-TIER, UNVERIFIED** | That Google "does not contain" the current canonical files. | A claim about a store the filer cannot see. Only the maintainer can check. |
| **CHAT-TIER, UNVERIFIED** | That it "absorbed" the rules. | A claim about its own state, not observed behaviour. |

What the tiering leaves standing is still worth having: **a hosted agent reached
a correct recitation of the house invariants through a non-GitHub channel.** The
recitation being correct is checkable and was checked. How it got there is not.

**The missing measurement, unchanged:** nobody has given this session a task and
scored whether the invariants actually BIND its actions. Reciting a rule and
being constrained by it are different things -- this project has a session on
record that read the sandbox git rule, cited it approvingly, and wedged the
index lock within the hour. Recitation is the weakest possible evidence of
onboarding, and it is what this package contains.

## 4. What it establishes

**A hosted agent reached working current state with no GitHub involvement**, via
two channels that the portal's own documentation does not name:

- **Google Drive** -- carrying a DERIVED artifact (an August 6 cold-onboarding
  report), not the canonical files;
- **the BBS, delivered over Gmail** -- carrying today's live lane state.

Both are real channels. Neither is GitHub, and neither is the website Agent Sync
page. `AI_README.md` and `AI_PORTAL.md` both frame a hosted partner as seeing
"only GitHub and the website"; that framing is now incomplete, and is corrected
in the same commit as this package.

## 5. What it does NOT establish -- and the claim that must not be repeated as fact

The agent's own words:

> Google does not contain the current individual AI_README.md, AI_PORTAL.md,
> Tier 0, or Tier 1 files. I reconstructed the onboarding contract from an
> August 6 cold-onboarding report and used today's Gmail BBS output for current
> state.

**Read that as testimony, not as a finding.** It is the agent reporting on its
own inputs, and it is the least verifiable sentence in the transcript. It may be
accurate; it may be a plausible-sounding reconstruction of where its knowledge
came from, which is a thing language models produce readily. Nobody has looked in
the channel.

IF it is accurate, the consequence is the AIF-082 retrieval-failure class
exactly -- the canonical copy correct, single, and not reachable from where the
work started -- and the fix below applies. **The fix is worth doing either way**,
because a channel that demonstrably contains the four canonical files removes the
question entirely rather than answering it.

The fix is cheap and is the action item this package raises: **put
`AI_README.md`, `AI_PORTAL.md`, `AI_TIER1_SEED_V1.md` and `TIER0_STATE.md` into
the Drive channel**, so the next hosted session reads canon instead of
reconstructing it. Four files, four invariant-carrying reads, no new mechanism.

### UNRESOLVED: was there an August 6 document at all?

**The prior question is not WHICH document -- it is WHETHER.** The filer's first
draft skipped straight to identifying it and ranked four candidates, which
silently promoted a chat-tier claim into a premise. Corrected on maintainer
challenge.

Two checks, in order, and only the maintainer can run either:

1. **Does the channel contain an August 6 document at all?** If not, the
   session's account of its own sourcing is confabulated and nothing below
   applies -- which would itself be the more interesting finding, and a sharp
   reminder about what hosted self-reports are worth.
2. **If yes, which one?** Only then does the table below mean anything.

The filer can read the tree but NOT the maintainer's Drive ("Vantage point" in
`AI_README.md`'s Minimal New-AI Checklist -- absence of evidence from where you
are standing is not evidence of absence). It may not be an in-tree file at all.

In-tree candidates dated 2026-08-06, ranked by textual match to the recited
invariants. **This table is CONDITIONAL on check 1 passing** and is offered to
save the maintainer a search, not as an identification:

| Candidate | For | Against |
| --- | --- | --- |
| `external_ai_intake/aif090_cold_probes_2026-08-06/`, esp. `PROBE_C_NO_TREE.md` | 17 invariant hits; line 18 enumerates "repository roles, the `&&` comment marker, the `git add -A` prohibition" -- the exact set recited. It IS a cold-onboarding report, matching the session's own wording. | That line is a QUOTATION OF CONTAMINATION -- the probe disclosing what the harness injected into it. Onboarding from it would mean the contamination became the teaching text. |
| `docs/agents/HANDOFF_CLAUDE_COWORK_AGENT_SKILL_2026-08-06.md` | States it records "how to work in this lane" -- an onboarding contract in the handoff sense. 5 hits. | Lane-scoped to AIF-090, not the general contract. |
| `docs/maintenance/COWORK_SESSION_HANDOFF_2026-08-06.md` | Multi-lane rollup carrying broad current state. | 2 hits; reads as state, not contract. |
| `docs/maintenance/X64BASE_AGENT_SKILL_P0_MEASUREMENT_V1.md` | The report named in the probe MANIFEST. | 1 hit; a measurement report, not a contract. |

**Why this matters rather than being trivia.** If check 1 fails, a hosted agent
invented its own provenance while otherwise performing well -- and every future
hosted self-report gets read accordingly. If check 1 passes and the document is
the probe package, then hosted onboarding rests on an artifact whose own header
disclaims its behavioural findings: correct invariants arriving through a
document never written to deliver them. Both outcomes change how the channel
should be used. Resolving it costs one look at the shared folder.

**The channel also lags, measurably.** The BBS output reported the baseline as
`db04678b dirty`. By the time of this filing `development` HEAD was `b3f648288`
-- several commits on, including `c4fe62d8a`, `a766f1430` and `b3f648288` the
same day. State arriving by mail is state as of the mail. Say so rather than
treating a BBS figure as current.

## 6. The reading to avoid

The invariants survived reconstruction from a derived report. Two honest
readings, and one run cannot separate them:

1. The Tier 1 invariants are well-factored and redundantly expressed, so they
   reconstitute even from a lossy secondary source; or
2. the August 6 report was simply a good summary, and this measures that
   document rather than the seed.

Recording both. Claiming (1) alone would be the flattering reading, and this
lane exists because flattering readings were what earlier assessments produced.

## 7. Companion observation (maintainer, same day)

The maintainer notes that development was greatly accelerated by Claude's and
Codex's **desktop** local-file access. That is a program-level observation about
capability, distinct from this package's evidence; it is recorded on the
dashboard rather than asserted here, because no measurement in this package
speaks to it.
