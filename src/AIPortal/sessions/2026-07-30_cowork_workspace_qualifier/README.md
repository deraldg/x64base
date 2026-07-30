# Session package -- Workspace qualifier / multi-workspace addressing (AIF-078)

**Session:** `2026-07-30_cowork_workspace_qualifier`
**Run:** `WORKSPACE-QUALIFIER-20260730` · **Member:** `member.ai.claude.cowork` · **Owner:** `member.derald`
**Baseline:** `349227c18e2f8781df0f576804bf962ff44797a3` on `development`
**Lane:** `AIF-078` -- `coordination/aif/AIF-078.claim`

---

## Read this first

**The authority for this lane is `docs/maintenance/WORKSPACE_QUALIFIER_NAMESPACE_DEPTH_LANE_V1.md`.**
The package in this folder is the **reference design only**, and is **superseded in part**.

## Contents

| File | Kind | Status |
|---|---|---|
| `AI_CHANGE_PACKAGE_MULTI_WORKSPACE_ADDRESSING_V1_20260730.md` | design proposal | `review-needed` -- **superseded in part** |
| `README.md` | curation index | this file |

**No patch, no source change, no test artifact.** This session produced analysis and a lane charter; the engine was not touched. `git status` at close showed no modification under `src/` or `include/` attributable to this run.

## Why the package is superseded in part

It was written before the investigation reached `docs/maintenance/SQLSEL_PLDC_LANE_V1.md:112`, which shows AIF-074 phase **P4.1** already owns table-reference qualification (*"Adds table ALIASES (`FROM STUDENTS S`) and QUALIFIED column names (`S.LNAME`), which every later slice needs"*).

That reframes the whole question. The package proposes a **standalone multi-workspace feature lane**; the lane charter concludes the live decision is far narrower -- the **namespace depth of a qualifier AIF-074 is about to author anyway** -- and recommends buying the option rather than the feature.

**What remains useful:** §4.1 (the `WorkspaceRegistry` slot-partition sketch) and §4.2 (the `@` sigil grammar) stand as the reference design **if and when** multi-workspace is built. §2's contract table is source-evidenced and independently useful -- it is the most complete written inventory of the engine's name-resolution chokepoints.

**What is withdrawn:** §9 Q8 asked whether the 512 slots should be rationed per workspace. `MAX_AREA` is a settable build vector (`config/build_vectors.cmake:14`, AIF-044; `:8-12` states 512 is a compatibility default). There is no budget to ration. Maintainer caught it; see the lane doc §9.

## Related artifacts

Landed in `809128e2b` (this package's commit):

- `docs/maintenance/WORKSPACE_QUALIFIER_NAMESPACE_DEPTH_LANE_V1.md` -- lane charter, `AIPR-20260730-001`
- `docs/maintenance/COST_BENEFIT_GATE_DOCTRINE_V1.md` -- doctrine, `AIPR-20260730-002`
- `docs/maintenance/SESSION_CLOSEOUT_WORKSPACE_QUALIFIER_NAMESPACE_DEPTH_2026-07-30.md` -- audited closeout, `AIPR-20260730-003`
- `coordination/aif/AIF-078.claim` -- lane claim

Landed separately:

- `docs/ai-friendly/AI_INTERACTION_INTAKE_QUEUE_V1.md` -- AIF-078 row. Held out of `809128e2b` because the working-tree file also carried the uncommitted AIF-075/076/077 rows, and fusing four lanes' rows into one lane's slice is what `AI_SESSION_COORDINATION_PROTOCOL_V1.md` forbids. Landed in the follow-up commit that lands all four.

*(Corrected after `809128e2b`: this section previously listed the intake row as "committed elsewhere in this changeset," which it was not. A note that was true when written and false at commit time -- the AIF-061 lesson, that a comment is part of the change.)*
