# AIF-090 P0 cold-probe package -- outside-runner evidence

    From:   member.ai.claude.cowork  (run COWORK-20260806-001, lane AIF-090)
    To:     the record
    Date:   2026-08-06
    Status: primary observation, committed after the fact -- read section 3 first
    Lane:   docs/maintenance/X64BASE_AGENT_SKILL_PLDC_LANE_V1.md
    Report: docs/maintenance/X64BASE_AGENT_SKILL_P0_MEASUREMENT_V1.md

## 1. Why this package exists

The G0 NO-GO on AIF-090 -- the decision to kill a chartered programme before
building it -- rests on two cold-agent probe runs. Until this commit, those runs
existed only in a chat transcript, and what was in the tree was a
**re-derivation** of the figures they reported.

A re-derivation is not the observation. `AI_ASSIMILATION_BOOK_V1.md`'s authority
order puts a primary record above a reconstruction, and AIF-082's founding lesson
is a handoff that was never put in the tree. Committing these closes the weakest
link in the day's evidence.

The maintainer asked the right question -- "what is my evidence of a deliverable"
-- and this was the honest answer's soft spot.

## 2. Contents

| File | What it is |
| --- | --- |
| `PROBE_A_CONTROL.md` | Control arm. Realistic task, no mention of the portal, the seed, or `recall.py`. |
| `PROBE_B_TREATMENT.md` | Treatment arm. Same task, preceded by a ~1.5 KB skill stub. |
| `PROBE_C_NO_TREE.md` | No-tree arm, added later the same day. Outside agency, public GitHub only. **Contaminated -- read its section 1.** Its structural findings survive the contamination; its behavioural ones do not. |

A fourth arm (no tree, WITH a bundle) was designed and **deliberately not run**.
The harness auto-injects `CLAUDE.md` into every subagent, so both arms would
have carried the bundle's contents by injection and the comparison could not
have meant anything. Publishing that number would have been an instance of the
defect class this lane exists to close.

## 3. Provenance, stated plainly

**These are REPRODUCED from the orchestrating session's context, not captured to
disk by an automated harness.** That is a weaker provenance than a teed
transcript and the reader should treat it as such.

What supports them:

- Both probes ran as `general-purpose` subagents of the orchestrating Cowork
  session on 2026-08-06, with agent ids `a30b8c275396a93ce` (control) and
  `ab16ef3b50b2168f4` (treatment).
- **Every quantitative claim either probe made was independently re-derived from
  the tree** before it was recorded anywhere, using the commands quoted in
  `X64BASE_AGENT_SKILL_P0_MEASUREMENT_V1.md` section 4. The treatment probe
  additionally re-derived the 27,384 B working set itself, node by node, and
  matched to the byte.
- The two probes were run independently and did not see each other's output.

What does not support them: nobody but the orchestrating agent saw the runs
happen. If a future session needs stronger evidence, the probes are cheap to
repeat and the design is in section 2 of the measurement report.

## 4. Normalization notice

Both files were ASCII-normalized before commit -- `check_house_style.py` blocks
non-ASCII in added lines, and every line of a new file is an added line. The
substitutions are the house set (`--`, `->`) and no figure, filename, exit code
or quoted sentence was altered. Where a probe's own wording is quoted in the
lane documents, it is quoted verbatim from these files.

## 5. What the probes established

- Both arms reached Tier 1 and answered the seed's five questions. The control
  was never told the seed existed.
- Both read roughly 48 KB. The skill stub produced no material saving.
- The control hunted for orientation tooling, found six other tools, and missed
  `recall.py` -- which was, at that moment, cited by zero entry-path documents.
- The treatment arm found the defect that mattered most: the resolver's headline
  percentage was measured against a frozen constant, and against the entry path
  actually in force the working set was 2.5x LARGER, not 21 percent smaller.

That last finding is why this package is worth committing. It was produced by an
agent that had not seen the argument it demolished.
