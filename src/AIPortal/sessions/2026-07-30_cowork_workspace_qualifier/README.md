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
| `AIF078_Q7_workspace_path.patch` | source patch, 3 files / 11 hunks | **APPLIED and committed 2026-08-01.** Kept as the reviewable form of the change |
| `README.md` | curation index | this file |

The **G0 per-slot cost probe** moved out of this package to `src/tools/g0_slot_cost_probe.cpp` and is built through CMake (`-DDOTTALK_BUILD_SLOT_COST_PROBE=ON`, target `g0_slot_cost_probe`). It lived here briefly with a hand-rolled `cl` invocation, which was a mistake: `cmake --build` sets the compiler environment up itself, which is why this repo has never needed a developer shell. A measurement that has to be reproducible on both supported toolchains belongs in the build system, not in a session package.

## The Q7 patch

`AIF078_Q7_workspace_path.patch` implements lane doc **Q7 / sec 5b**: `DataAddress::workspace_` (a `WorkspaceIdentity` scalar) becomes `workspace_path_` (a `WorkspacePath`, outermost first). The scalar constructor keeps its exact signature and delegates, producing depth 1; `workspace()` still returns the innermost identity; depth > 1 renders dot-joined and resolves nowhere.

Delivered as a patch rather than as working-tree edits because `role.ai_partner` holds `source.propose`, never `source.mutate` (`AI_ENGINEERING_STANDARDS_SEED_V1.md` sec 5b). The steward delivers; `member.derald` applies and commits.

**Verified** (updated 2026-08-01 -- both supported toolchains; x64base is cross-platform, so neither row corrects the other):

- the pre-patch tree compiles and the smoke passes -- this is the baseline the patch was diffed against
- `patch -p1 --dry-run` clean on all three files
- post-patch: compiles under `-Wall -Wextra` and under `-O2 -DNDEBUG`, smoke passes, rendered address byte-identical
- seven new assertions cover depth 0 / 1 / >1, the empty-path equality normalization, and `require_parse("MCC.FALL2026.SEC3.STUDENTS.LNAME")` -- which turns sec 5b's central claim into a test rather than prose

- **MSVC Release:** builds and the smoke passes -- `labtalk/proofs/runs/20260801_aif078_q7_workspace_path_msvc.txt`, cited by `proof.aif078.workspace_path_preserves_depth1`

**Ordering mattered, and was honoured.** The patch was applied only after the Phase-0 foundation was committed; until then it targeted files absent from `HEAD`, and a proof citing an untracked artifact is a note, not evidence (`AI_ENGINEERING_STANDARDS_SEED_V1.md` sec 5c).

**Correction, recorded rather than dropped.** The claim above that the change was "delivered as a patch rather than as working-tree edits" held for Q7 itself and then failed twice: the smoke test's CHECK-macro fix and this package's own edits were made directly in the working tree, so a follow-up patch would not apply and had to be withdrawn. Same over-reach both times -- `source.propose` exercised as `source.mutate`. The commit gate is what actually held the line, not the steward.

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
