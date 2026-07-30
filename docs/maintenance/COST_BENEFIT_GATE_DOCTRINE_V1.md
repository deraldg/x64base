---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260730-002
  recorded_at_utc: 2026-07-30T22:24:18Z
  agent:
    provider: Anthropic
    product: Claude (Cowork)
    model: not_exposed
    access_mode: local_write
  session:
    id: not_exposed
    chat_reference: not_exposed
  project:
    id: project.ai_friendly
    root: D:/code/ccode
  git:
    branch: development
    baseline_commit: 349227c18e2f8781df0f576804bf962ff44797a3
  authorization:
    requested_by: maintainer
    scope: >
      Maintainer ruling 2026-07-30 -- "cost / benefit is now a life lesson in
      our design." Capture the cost/benefit discipline as doctrine, derived from
      the AIF-078 analysis rather than imported as generic guidance.
  report:
    path: docs/maintenance/COST_BENEFIT_GATE_DOCTRINE_V1.md
    kind: doctrine
---

# Cost/Benefit Gate Doctrine V1

**Status:** `review-needed` (proposed doctrine)
**Owner:** `member.derald` · **Steward:** `member.ai.claude.cowork`
**Origin:** maintainer ruling 2026-07-30 -- *"cost / benefit is now a life lesson in our design."*
**Derived from:** `AIF-078` (`docs/maintenance/WORKSPACE_QUALIFIER_NAMESPACE_DEPTH_LANE_V1.md`). Every rule below is a mistake made or a finding earned in that analysis, not imported advice.
**Companion to:** the evidence-tier taxonomy -- *"Conventions suggest. Registration declares. Metadata records. Runtime proves. Validators enforce."*
**Sibling doctrine:** `docs/maintenance/SCOPE_CALIBRATED_LIFECYCLE_DOCTRINE_V1.md`

---

## The cadence

> **Estimates suggest. Probes measure. Surfaces count. Timing multiplies. Reversal decides.**

---

## The five rules

### 1. Cost lives in invariants, not objects.

The request was *"add a low cost object above the table alias."* The object turned out to be a 1 KB array. The cost was in three resolvers that silently assumed table names were globally unique -- an invariant nobody had written down, held in place by `cli::find_open_area_by_name_ci` returning the first match with no ambiguity signal.

**Before pricing a change, name the invariant it weakens.** If it weakens none, it is probably cheap. If it weakens one that is undocumented and load-bearing, the object's size is irrelevant.

### 2. Verify the constraint is real before designing around it.

An earlier draft treated `MAX_AREA = 512` as a budget to be rationed and asked whether workspaces should get reserved slot ranges. `config/build_vectors.cmake:8-12` says plainly that 512 is a compatibility default chosen to preserve compiled behavior -- a settable AIF-044 vector with no upper bound at all.

Designing around a constraint that is not real produces complexity that is. **Read the constant's definition, not just its value.**

### 3. Timing multiplies. Price the same change at both ends of the schedule.

The workspace qualifier costs roughly three surfaces if decided before AIF-074's P4.1 authors the qualifier grammar, and roughly ten surfaces **plus the re-running of every closed SQLite-oracle gate** if decided after P4.7.

Identical change. Order-of-magnitude difference. **A cost/benefit with no date on it is not a cost/benefit.** State when, or the number is meaningless.

### 4. Count surfaces, not lines.

Lines of code is the wrong denominator. The right one is: *how many independent places must agree for this to be correct?* Nineteen copy-pasted linear scans of the slot array are individually trivial and collectively the reason a cap raise is not free.

**A change that touches one surface deeply is cheaper than one that touches ten surfaces shallowly.**

### 5. Price the reversal separately from the build.

Most of the multi-workspace proposal was additive and defaulted to a no-op, so reverting was free. Exactly one piece -- rejecting `A.B.C` instead of silently yielding an empty value -- was irreversible, because corpus scripts depend on the current behavior.

**The irreversible fraction deserves its own gate and its own decision, regardless of how small it is.** Bundling it inside a feature lane hides the breakage.

---

## Two derived habits

### Buy the option, not the feature.

When a capability is not yet justified but its *cheapest moment* is now, the correct purchase is usually the option: reserve the grammar seat, add the scope parameter, default the new level to the old behavior. Do not build the runtime.

This separates *"we might want multiple workspaces"* (unjustified, expensive) from *"do not foreclose multiple workspaces"* (nearly free, expiring). **Only the second is on the clock.**

### A prerequisite that pays for itself is not a cost.

Storing the slot index inside `DbArea` collapses nineteen scans to O(1) and removes a per-row cost from relation traversal **that exists today at 512 slots**. It is also a prerequisite for raising the cap and for any workspace partition.

Such items are scored at **zero** against the feature and landed on their own merits. Attributing them to the feature makes the feature look expensive and delays a fix that was already owed. **Score shared prerequisites separately, or the ledger lies.**

---

## Gate requirement

No lane opens, and no phase in an open lane starts, without a cost/benefit record answering all six:

| # | Question | Fails if |
|---|---|---|
| 1 | **What invariant does this weaken?** | Answer is "none" and the change touches a resolver, a namespace, or a uniqueness assumption |
| 2 | **What is the measured cost?** | Any size, memory, or hot-path figure is estimated rather than probed |
| 3 | **How many surfaces must agree?** | Counted in lines instead of call sites |
| 4 | **What does this cost if deferred one phase? Three? Until lane close?** | No date given |
| 5 | **What fraction is irreversible, and what breaks on revert?** | "Fully reversible" asserted without naming the dependent behavior |
| 6 | **Which prerequisites pay for themselves alone?** | Shared prerequisites scored against this feature |

Rows 2 and 4 are the ones most often skipped and most often decisive.

---

## Evidence tier of a cost estimate

Cost figures inherit the same hierarchy as everything else:

1. **Runtime-evidenced** -- measured on the target toolchain (a compiled `sizeof` probe, a timed run, a real RSS reading).
2. **Source-evidenced** -- derived from declarations actually read (a struct's members, a loop's bound).
3. **Planned** -- taken from a charter's own statement of intent.
4. **Chat/AI output** -- an estimate, however careful.

In the AIF-078 analysis, `sizeof(DbArea)` was estimated at 800 B to 1 KB from member declarations, then measured at **1088 B**. The estimate was close, and the probe took under a minute.

**Estimate when you must, probe when you can, and label which one you did.** An unlabeled cost figure is chat-tier by default -- and a cost/benefit built on chat-tier numbers is a preference with arithmetic attached.

Note the residual honesty bound in AIF-078 itself: the probe ran under g++/libstdc++, and the shipping toolchain is MSVC. The numbers are runtime-evidenced *for the wrong compiler*, which is why AIF-078 carries gate G0. **Measured on the wrong target is still not measured.**

---

## Anti-pattern

The failure this doctrine exists to prevent is not *underestimating* cost. It is **pricing the wrong thing** -- answering "how big is the object?" when the question was "what stops being true?"

The tell: a proposal whose cost section is a table of sizes and whose risk section is empty.

---

## Relationship to existing doctrine

This sits beside, not above, the evidence-tier taxonomy. Evidence tiers govern **whether a claim is true**; this governs **whether a true claim is worth acting on, and when**. A proposal can be fully source-evidenced and still be a bad purchase because it was priced at the wrong point in the schedule.

`SCOPE_CALIBRATED_LIFECYCLE_DOCTRINE_V1.md` governs how much process a change of a given size deserves. This governs whether the change should happen at all, and when. Scope calibration answers *how*; cost/benefit answers *whether* and *when*.
