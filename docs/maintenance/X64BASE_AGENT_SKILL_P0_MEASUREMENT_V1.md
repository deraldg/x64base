---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260806-004
  recorded_at_utc: 2026-08-07T04:40:00Z
  agent:
    provider: Anthropic
    product: Claude (Cowork)
    model: claude-opus-5
    access_mode: local_write
  session:
    id: not_exposed
    chat_reference: claude-cowork:not_exposed
  project:
    id: project.ai_friendly
    root: D:/code/ccode
  git:
    branch: development
    baseline_commit: 9dbdd69ec
  authorization:
    requested_by: maintainer
    scope: >
      Owner directed "p0 first" on AIF-090. This is the P0 measurement and the
      evidence for the G0 go/no-go. The G0 ruling itself is the owner's; no
      self-approval by the author.
  report:
    path: docs/maintenance/X64BASE_AGENT_SKILL_P0_MEASUREMENT_V1.md
    kind: measurement_report
---

# AIF-090 P0 -- Prove the Bottleneck: measurement and G0 evidence

    lane        : AIF-090, docs/maintenance/X64BASE_AGENT_SKILL_PDLC_LANE_V1.md
    date        : 2026-08-06
    method      : two outside-runner cold probes plus static reachability
                  measurement; every probe figure re-derived independently
    verdict     : **NO-GO recommended on the lane as chartered.** Owner ruling
                  required; the author does not rule his own gate.

---

## 1. What P0 had to establish

The charter's premise: cold agents do not reliably reach Tier 1, so a
description-triggered skill is needed to make the front door fire. G0 says that
if cold agents already reach Tier 1 reliably, the lane is packaging polish and
should defer.

`AI_PORTAL.md` "Build It to Prove It" required the method: *"Prefer an outside
runner. The author of an instrument is its worst tester, for the same reason a
warm assessor cannot test a cold entry path."* The session that chartered this
lane was warm. So the measurement was delegated to two cold agents that had not
seen this conversation.

## 2. Design

| Arm | Priming | N |
| --- | --- | --- |
| Control | Realistic task in the repo. No mention of the portal, the seed, or `recall.py`. | 1 |
| Treatment | Same task, preceded by a ~1.5 KB skill stub: probe environment, load Tier 0 + Tier 1, route by trigger via `recall.py`, stop at the five questions. | 1 |

Both were told to run **no** git and to make **no** edit; git behaviour was
captured as stated intent. Both were asked to report their own read order
untidied and to mark each of the seed's five questions ANSWERED-FROM-`<file>` or
COULD-NOT-ANSWER.

## 3. Result: the premise is falsified

**Both arms reached Tier 1 and answered all five questions.** The control was not
told the seed existed; it found it because the auto-injected `CLAUDE.md` points
at it, read it sixth, and stopped there. Its own words: *"I felt ready to act
after step 6 ... That file alone answered four of the five stopping questions and
told me exactly which pointer to follow for the fifth."*

**Neither arm read less than the other.** Both totalled roughly 48 KB. Isolating
orientation from task work, and excluding the treatment probe's unprompted audit
of `recall.py`'s own source (11,786 B, which it read to confirm the tool never
shells out to git before running it under a no-git constraint):

| | Control | Treatment |
| --- | --- | --- |
| Deliberate orientation reading | ~30 KB | ~23 KB |
| Total including listings and task work | ~48 KB | ~48 KB |
| Five questions answered | 5/5 | 5/5 |
| Reached Tier 1 | yes | yes |

A ~23 percent orientation reduction at N=1 per arm, heavily confounded, is not
the 5x the resolver advertises and is not a bottleneck.

## 4. Four defects the probes exposed

These are the findings that survive the NO-GO, and they are worth more than the
lane was.

### D1. `recall.py` is unreachable from every document on the entry path

Measured per file (`grep -c 'recall\.py'`): `CLAUDE.md` 0, `AGENTS.md` 0,
`.github/copilot-instructions.md` 0, `AI_README.md` 0,
`AI_TIER1_SEED_V1.md` 0, `AI_PORTAL.md` 0, `CURRENT_TARGET.md` 0,
`TIER0_STATE.md` 0, `labtalk/ai_portal/README.md` 0.

It is cited by nine documents, none of them on the mandatory start path: the
assimilation book (explicitly depth-on-demand), the dashboard, the intake queue,
the bootstrap card, the AIF-082 lane and its closeout, and two files authored
today.

**The control probe confirms the consequence.** It hunted for orientation tooling,
found `session_coordinator.py`, `prepush_gate.py`, `repository_role_guard.py`,
`generate_tier0_state.py`, `check_house_style.py` and `ascii_normalize.py` -- and
reported: *"I did not find a single 'run this to onboard' entry-point script."*
The one tool built to solve the entry-path problem was the one tool it missed.

This is AIF-082's own binding constraint applied to AIF-082's own deliverable: a
memory that cannot be reached is, functionally, a memory that does not exist.

### D2. The headline metric is anchored to a corpus that no longer gates anyone

`recall.py:40` hardcodes `ENTRY_PATH_BASELINE = 127704`, measured 2026-07-31.
Every working set is printed as a percentage of it.

But the entry path **in force today** is Tier 0 plus Tier 1:

```
labtalk/ai_portal/TIER0_STATE.md         1,919 B
labtalk/ai_portal/AI_TIER1_SEED_V1.md    8,990 B
                                        --------
actual entry path                       10,909 B
```

The working set `recall.py commit_or_push` returns is 27,384 B. That is **2.51x
LARGER than the path it claims to replace**, printed as "21% of the 127704 B
entry path this replaces".

The bound at `recall.py:289` -- `if total >= ENTRY_PATH_BASELINE` -- exists
specifically so the metric can fail, and was added after the resolver reported a
217,471 B working set beneath the words *read these, not the corpus*. Anchored to
the stale constant, **it can never fire.** Same defect shape, same file, second
occurrence.

`AI_TIER1_SEED_V1.md`'s maintenance contract forbids exactly this: *"No
perishable literal. If an agent can cheaply measure it, say 'measure it'."* The
resolver's headline figure breaks the rule the seed it serves is built on.

The 27,384 B figure itself is **correct** and was verified twice independently --
by me and by the treatment probe, each re-extracting all six nodes from disk:
4,599 + 606 + 1,201 + 3,659 + 8,727 + 8,592 = 27,384 exactly. The historic 6x
whole-file bug is genuinely fixed. It is the denominator that is wrong.

### D3. The graph returns pointers whose targets are not in it

`commit_or_push` returns `AI_PORTAL.md [## Pre-Push Gate]`, whose prose says
*"Order, severities, triggers, exit codes and known defects:
`docs/maintenance/PREPUSH_GATE_REFERENCE_V1.md`"*.

That target is **not in the graph** (`grep -c` = 0). Neither is
`docs/maintenance/AI_SESSION_COORDINATION_PROTOCOL_V1.md`, which `CLAUDE.md`
calls the authoritative doctrine for commit coordination. The treatment probe had
to follow prose into the corpus -- the exact linear reading the resolver exists
to eliminate.

Meanwhile the two tier-2 leaves the resolver *did* return account for 17,319 B,
63 percent of the working set, and the probe judged them the least useful nodes
for the task. The graph over-links generic authority and under-links task
mechanism.

### D4. The Tier 1 seed is over its own hard ceiling, unenforced

`AI_TIER1_SEED_V1.md:7` declares `budget: 8192 B hard ceiling`. Actual size:
**8,990 B. Over by 798.**

No gate enforces it. The only `8192` occurrences in `tools/` are incidental read
buffers (`active_catalog_promotion_execute.py:122`,
`stack_audit_v1.py:195`). Nothing references the seed by name for size.

`AI_PORTAL.md` holds this ceiling up as its exemplar of a good bound: *"A bounded
metric is a gate; the Tier-1 seed's 8,192-byte ceiling caught its author three
times in one sitting."* It caught its author because its author was watching. It
is not a gate, and it has drifted.

## 5. Honest limitations

- **N=1 per arm, both Claude, both in the same harness.** Not a population.
- **The control was not truly unprimed.** `CLAUDE.md` is auto-injected and
  already points at the seed, which is *why* the control succeeded. The genuinely
  unprimed case -- a hosted agent with no tree and no auto-injected shim -- was
  **not tested**, and remains the one place the skill's original argument may
  still hold.
- **Vendor asymmetry was measured statically, not by probe.** `CLAUDE.md` and
  `AGENTS.md` both point at the seed; `.github/copilot-instructions.md` does not
  (and carries unrelated Azure boilerplate). Only `CLAUDE.md` was observed to be
  auto-injected here.
- **Git behaviour is stated intent, not action.** Both arms were forbidden from
  running git for safety, so "would they wedge the repo" was not observed. Both
  correctly identified the lock hazard and the lock-free read-only forms.
- **The treatment probe deviated from the stub** by reading `recall.py`'s source
  before running it. Justified, but it means the arms are not cleanly comparable.

## 6. Recommendation to the owner

**NO-GO on AIF-090 as chartered.** The lane's premise -- that cold agents do not
reach Tier 1 -- did not survive contact with two cold agents. Building a
projector, a bundle, and a vendor-shim collapse on top of that premise would be
spending against a bottleneck that is not there.

**Recommended conversion: a small repair lane** addressing D1-D4, in cost order:

1. **D2 first.** Replace the hardcoded denominator with a measured one, so the
   bound at `:289` can fire. This is a few lines and it turns a metric that
   cannot fail into a gate that can. Until it is fixed, every figure the resolver
   prints is unsafe to quote.
2. **D4.** Add a ceiling check for the seed. The rule already exists; only the
   gate is missing. Cheap, and it is the repo's own exemplar.
3. **D1.** One line in the seed's trigger index pointing at `recall.py`. If the
   seed is at its ceiling, this is precisely the "demote out" the contract
   describes.
4. **D3.** Add the missing `requires` edges; consider whether tier-2 leaves
   belong in a depth-1 result.

**What survives of the original lane, and should be re-argued separately, not
assumed:** the distributable no-tree bundle (R3's orthogonal design is sound and
untested by this measurement), and the vendor-shim asymmetry, which is real and
which P0 measured but did not probe.

## 7. Provenance

- Lane: `docs/maintenance/X64BASE_AGENT_SKILL_PDLC_LANE_V1.md`
- Method rule: `AI_PORTAL.md`, "Build It to Prove It -- Why Review Does Not Find
  These (AIF-082)" and "Prove the Bottleneck First"
- Probe transcripts: not committed; the reported figures were re-derived from the
  tree independently and those derivations are reproducible with the commands
  quoted inline above.
