# Session package -- House index maintenance + VDISK routing boundary

**Session:** `2026-07-30_cowork_house_index_vdisk`
**Run:** `DECLARED-CAPABILITY-VALIDATOR-20260730` - **Member:** `member.ai.claude.cowork` - **Owner:** `member.derald`
**Baseline:** `b702b5a5d1cc629c48411af9e93ff879b198e73f` on `development`
**Lanes touched:** `AIF-079` (new, claimed) - `AIF-043` (existing, new milestone V6) - `XIDX-TXN-02` (existing, M0 amended)

---

## Read this first

**No engine source was changed.** This session produced analysis, one lane charter, and one milestone declaration. Everything is `review-needed`. Nothing was committed or staged.

The two documents in this folder are the **evidence record**. The two documents in `docs/maintenance/` are the **actionable lane authority**. If they ever disagree, the lane docs win and this folder is the audit trail of how they were derived.

## Contents

| File | Kind | Status |
|---|---|---|
| `LANE_XIDX_TXN_02_M0_RECONCILIATION_V1_20260730.md` | findings, amends an existing M0 | `review-needed` |
| `AIF_043_VDISK_VIRTUAL_STORE_BOUNDARY_FINDINGS_V1_20260730.md` | findings | `review-needed` |
| `INDEX_MUTATION_SEAM_TRACE_V1_20260730.md` | findings, routed to existing lanes | `review-needed` |
| `TRIAGE_EXECUTION_PLAN_V1_20260730.md` | cross-lane execution plan, triage order | `review-needed` |
| `SITTING1_CHANGE_MANIFEST_V1_20260730.md` | **change manifest -- source WAS modified** | `review-needed` |
| `README.md` | curation index | this file |

> **This session stopped being doc-only.** Sitting 1 of the triage plan (items E, C1, A) was implemented under explicit maintainer authorization: five files under `src/`, unstaged and uncommitted, syntax-checked only. See the change manifest for the new `replaceFieldStored` contract, three behavior changes a reviewer must agree to, and the build commands that reach the next gate.

**Start with the triage plan** if you are picking this session up to do work rather than to review findings. It orders every item from all three investigations so that stopping after any sitting leaves the highest-value work already banked.

## Related artifacts landed outside this folder

- `docs/maintenance/DECLARED_CAPABILITY_VALIDATOR_LANE_V1.md` -- `AIF-079` lane charter
- `docs/maintenance/AIF_043_V6_ROUTING_BOUNDARY_HARDENING_V1_20260730.md` -- `AIF-043` milestone V6
- `coordination/aif/AIF-079.claim` -- lane claim, allocated atomically via `session_coordinator.py claim-aif`

**Held out deliberately:** the `docs/ai-friendly/AI_INTERACTION_INTAKE_QUEUE_V1.md` row for `AIF-079`. The working-tree copy of that file may carry other sessions' uncommitted rows, and fusing several lanes' rows into one lane's slice is what `AI_SESSION_COORDINATION_PROTOCOL_V1.md` forbids. The row is drafted in section 4 below for whoever lands the next intake batch.

## How this session went

Two investigations, in order, both read-only:

1. **House index maintenance.** Question posed: *"the algorithm we used to update LMDB index keys/tags should work with the house index too."* Answer: yes, and more strongly than the premise assumes. There is no LMDB-specific algorithm. `IndexManager::apply_replace_snapshot` is already backend-neutral and already fires for CNX today, landing on stubs that discard the keys and set a flag nobody reads. Also found: this is already lane `XIDX-TXN-02`, M0 met 2026-07-21, M1-ready, never built. Five blockers the 07-21 M0 did not surface are recorded as N1-N5.

2. **VDISK / virtual store.** Question posed: investigate vdisk and virtual database / house index support. The existing positioning note is accurate on every limitation it claims; the gap is that it does not say whether those limitations are **enforced**. In five places they are not. Recorded as R1-R6.

The pattern that connects them -- seven instances of capability declared at the interface and absent at the leaf -- is what became `AIF-079`.

3. **Index mutation seam trace.** Maintainer question: trace how `REPLACE` handles an indexed field update on a CDX/LMDB x64 table, given that `REPLACE` and `CALC`/`CALCWRITE` share a mutator factory. Answer: the immediate path works, via `DbArea::replaceFieldStored` and the `index_hooks` seam. Five secondary findings (A-E) were routed to lanes that already exist rather than opening a new one. The one with a measurable payoff and the smallest diff is **A**: `apply_replace_snapshot` never calls the `old_key == new_key` short-circuit, so a one-field `REPLACE` on an N-tag table issues 2N LMDB transactions when 2 would do.

### Why the split (maintainer decision, 2026-07-30)

Asked whether to open one new lane or fold into `AIF-043`. Ruling: **split by nature.**

- R1-R6 are defects in `AIF-043`'s own scope -> folded in as milestone **V6**, no new number.
- The validator is cross-cutting (`xindex`, `cnx`, `cli`, `memo`), validator-tier rather than runtime-tier, and its proof artifact is a scanner plus a report rather than a `.dts` -> **new lane `AIF-079`**.

`XIDX-TXN-02` was not renumbered; the reconciliation note amends its existing M0.

## Label collision note

The VDISK findings were originally labelled V1-V6. `AIF-043`'s own milestone plan already uses V1-V5 (`VFS_INMEMORY_MILESTONE_PLAN_V1_20260721.md`), so the findings were relabelled **R1-R6** before filing. The new milestone is **V6**. Read `V` as milestone, `R` as routing finding.

## Evidence discipline

Every claim in both documents carries a `file:line` anchor and was re-verified by a second independent source pass before filing. That pass corrected two things worth recording:

- The `.tbj` journal path is **absolute** (derived from `DbArea::filename()`), not cwd-relative as first assumed. A narrow lazy-open fallback does produce a cwd-relative `area<N>.tbj`.
- The multi-tag capture gate excludes `LmdbBackend` as well as the two house backends, because `LmdbBackend` derives from `IIndexBackend` rather than `CdxBackend`. The in-code comment saying "CDX/LMDB" is wrong.

Tier: **`source-evidenced`**. No build, no runtime, no proof script executed. Nothing in this session has earned a runtime tier.

## 4. Drafted intake queue row (not landed)

```
| AIF-079 | Declared-but-unreferenced capability validator, Cowork 2026-07-30 | validator_candidate, drift_or_risk | `docs/maintenance` | `docs/maintenance/DECLARED_CAPABILITY_VALIDATOR_LANE_V1.md`; `coordination/aif/AIF-079.claim` | draft | Detects capability declared at the interface and absent at the leaf. Seven source-verified seed instances across xindex/cnx/cli/memo form the known-answer set (wasStale, CNX_HDRF_DIRTY, OnFull::Spill/Fail, CnxDocument::save, InxPayload::writeToStream, set_persistence_mode, make_x64_memo_store). Five detector classes D1-D5. Suppression proposed via the existing `@dottalk.contract status:` field rather than a bespoke allowlist. First validator to test the "Runtime proves" rung rather than "Metadata records". Report-only at M1; ratcheted gate at M3. Instances are owned by XIDX-TXN-02 and AIF-043 and must not be fixed by this lane -- they are its proof set. |
```

## 5. Open items for the maintainer

1. **AIPR report ids not assigned.** `AI_RUN_TRACEABILITY_CONTRACT_V1.md` specifies `AIPR-YYYYMMDD-NNN` for reports, but I could not find an allocator for it comparable to `claim-aif`. The three new documents carry the run id instead. Assign AIPR ids on review, or confirm the run id is sufficient for doc-only sessions.
2. **`AIF-079` section 6 suppression granularity** -- file-level `status: planned` versus symbol-level annotation. Flagged as the open M0 sub-question; it decides how noisy the tool is.
3. **`AIF-043` V6.0 R1 decision** -- route memo through ramfs, or refuse memo fields on virtual tables. Refusal is the smaller honest answer; routing is the complete one.
4. **`XIDX-TXN-02` sequencing.** The reconciliation note argues for inverting the lane order: prove incremental key maintenance in RAM first (where there is no fsync, no torn write, and no Windows atomic-rename question), then port to disk. That contradicts the 07-21 M1 plan, which starts with `save()`. Needs a ruling before the lane is scheduled.
