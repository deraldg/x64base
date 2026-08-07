---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260806-005
  recorded_at_utc: 2026-08-07T04:55:00Z
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
      Owner directed "p0 first" on AIF-090, then "document everything" and
      "take a pause to catch up your housekeeping". This closeout covers the P0
      measurement and the AIF-006 updates it made necessary.
  report:
    path: docs/maintenance/SESSION_CLOSEOUT_X64BASE_AGENT_SKILL_P0_2026-08-06.md
    kind: session_closeout
---

# Session Closeout -- AIF-090 P0 prove-the-bottleneck, G0 no-go (AIF-090)

Date: 2026-08-06.
Owning lifecycle: PLDC.
SDLC lane: intake.
Truth state: mixed (runtime-observed probes; static measurement re-derived).
Proof state: report + git-verified.

Supersedes the P0 status claims in
`SESSION_CLOSEOUT_X64BASE_AGENT_SKILL_LANE_OPEN_2026-08-06.md`, which was
written earlier the same day and says P0 is unmeasured. That closeout is a dated
record and was left intact; the living documents were corrected instead.

## One-line summary

Ran P0 with two cold outside runners, falsified the lane's own premise,
recommended G0 NO-GO on the lane I had chartered four hours earlier, and
surfaced four defects that are worth more than the lane was.

## Changed (development, D:\code\ccode)

| Area | Files | Note |
| --- | --- | --- |
| Evidence | `docs/maintenance/X64BASE_AGENT_SKILL_P0_MEASUREMENT_V1.md` | new; the P0 report and G0 evidence (`bc08afd1d`) |
| Lane | `docs/maintenance/X64BASE_AGENT_SKILL_PLDC_LANE_V1.md` | status line, P0 row, new section 9 recording D1-D4 (`bc08afd1d`) |
| Continuity | `docs/agents/HANDOFF_CLAUDE_COWORK_AGENT_SKILL_2026-08-06.md` | section 1 superseded in place -- it said "do not start at P1, P0 unmeasured"; P0 is done and said no |
| Registry | `docs/ai-friendly/AI_INTERACTION_INTAKE_QUEUE_V1.md` | AIF-090 row status and P0 result |
| Registry | `docs/ai-friendly/AI_FRIENDLY_DASHBOARD_V1.md` | prior row corrected, new Session Log row |
| Closeout | this file | new |

## Verified (proof performed this session)

**Method was dictated by doctrine, not chosen.** `AI_PORTAL.md` "Build It to
Prove It": *"Prefer an outside runner. The author of an instrument is its worst
tester, for the same reason a warm assessor cannot test a cold entry path."* The
session that chartered the lane was warm, so P0 was delegated to two cold agents
with no access to the chartering conversation.

- **Control arm** (no mention of portal, seed, or `recall.py`): reached the seed
  sixth, stopped there, answered 5/5. Reported *"I did not find a single 'run
  this to onboard' entry-point script"* -- it found six other tools and missed
  `recall.py`.
- **Treatment arm** (~1.5 KB skill stub): ran `recall.py commit_or_push`,
  answered 5/5, and independently re-derived the 27,384 B working set node by
  node, matching to the byte.
- **Neither read less.** ~48 KB each.

**Every probe figure was re-derived independently from the tree before being
recorded.** `wc -c` on the whole files; `awk` heading-to-heading extraction for
the four `AI_PORTAL.md` sections: 4,599 + 606 + 1,201 + 3,659 + 8,727 + 8,592 =
27,384 exactly. Tier 0 + Tier 1 = 1,919 + 8,990 = 10,909. Ratio 2.51x confirmed
by calculation, not assertion. Seed size 8,990 vs declared ceiling 8,192.
`grep -c` = 0 for `recall.py` across all nine entry-path files, and 0 for both
missing graph nodes.

**A false negative was caught before it was published.** An early recursive grep
reported zero mentions of `recall.py` tree-wide. The control case -- the same
grep for a string known to be present -- also returned zero, proving the method
broken rather than the finding true. Re-measured with a bounded method:
`recall.py` is cited by nine documents, none on the entry path. The corrected
claim is narrower and survives.

**Not verified:** no engine build, no runtime execution. N=1 per arm, both
Claude, both in the same harness. Git behaviour was captured as stated intent,
not action, because both probes were forbidden git for safety. The genuinely
unprimed case -- hosted agent, no tree, no injected shim -- was NOT tested, and
both probes received `CLAUDE.md` automatically, which is why the control
succeeded. Probe transcripts were not committed; the figures they reported were
re-derived from the tree with commands quoted in the measurement report.

## AI-facing docs updated (AIF-006 gate)

All four living surfaces that carried the now-false "P0 unmeasured" claim:
charter, handoff, intake row, dashboard. `CURRENT_TARGET.md` deliberately
unchanged -- AIF-090 is not the controlling target and the 2026-07-31 "no single
controlling lane" ruling stands. `TIER0_STATE.md` regenerates on commit.

## Published

`bc08afd1d` on `development`. Earlier commits this session: `6a9ce0ea5`,
`9dce6eb37`, `d4ad1b2ee`, `e9d2033d3`, `9dbdd69ec`, pushed through
`b482028db..9dbdd69ec`. Not promoted to `C:\x64base`. Not published to the
website.

## Handoff left (AIF-082 gate)

`docs/agents/HANDOFF_CLAUDE_COWORK_AGENT_SKILL_2026-08-06.md`, section 1
superseded in place on the same day it was written, because a handoff that tells
the next agent to run a gate that has already run is worse than no handoff.

## Still open -- for the next session

1. **G0 is a recommendation, not a ruling.** No self-approval by the author. The
   owner decides whether AIF-090 converts to a repair lane or closes.
2. **D2 is the only defect that makes a live artifact unsafe to quote.** Until
   `ENTRY_PATH_BASELINE` is measured rather than hardcoded, every percentage
   `recall.py` prints understates the working set against the path actually in
   force, and the bound that exists so the metric can fail cannot fire.
3. **D4 is the cheapest.** The seed's 8,192 B ceiling rule already exists; only
   the gate is missing, and the seed is 798 B over today.
4. **D1 costs one line** in the seed's trigger index -- but the seed is over its
   ceiling, so adding requires demoting something out, which is exactly the
   contract's own procedure.
5. **D3** needs `requires` edges for `PREPUSH_GATE_REFERENCE_V1.md` and
   `AI_SESSION_COORDINATION_PROTOCOL_V1.md`, and a look at whether tier-2 leaves
   belong in a depth-1 result -- they were 63 percent of the working set and the
   least useful part of it.
6. **The untested case:** hosted agent, no tree, no auto-injected shim. If the
   owner still wants a distributable bundle, that measurement is the honest
   prerequisite.
7. Carried forward unchanged from the earlier closeout: 21 untracked `.md` at
   `docs/maintenance` root, the 7 chat-spill `.txt`, the `yes`/`no` vs
   `true`/`false` editorial call, and the `AI_TIER1_SEED_V1.md:51`
   `git diff --cached` correction.

## Provenance pointers

- Measurement: `docs/maintenance/X64BASE_AGENT_SKILL_P0_MEASUREMENT_V1.md`
- Lane: `docs/maintenance/X64BASE_AGENT_SKILL_PLDC_LANE_V1.md` section 9
- Method rule: `AI_PORTAL.md`, "Build It to Prove It" and "Prove the Bottleneck
  First"
- Prior closeout superseded on P0 status:
  `docs/maintenance/SESSION_CLOSEOUT_X64BASE_AGENT_SKILL_LANE_OPEN_2026-08-06.md`
