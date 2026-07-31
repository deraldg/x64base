---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260730-004
  recorded_at_utc: 2026-07-30T23:40:53Z
  agent:
    provider: Anthropic
    product: Claude (Cowork)
    model: not_exposed
    access_mode: local_write
  session:
    id: not_exposed
    chat_reference: not_exposed
  project:
    id: project.x64base.runtime
    root: D:/code/ccode
  git:
    branch: development
    baseline_commit: b702b5a5d1cc629c48411af9e93ff879b198e73f
  authorization:
    requested_by: maintainer
    scope: >
      Investigate whether the LMDB index key/tag update algorithm applies to the
      house CNX/V32 and CDX-native indexes (report-only, "investigate without
      coding"). Then investigate vdisk and virtual database / house index
      support. Owner then directed: open an AIF lane in the AI Portal, split so
      the routing findings fold into AIF-043 and the validator gets its own
      number, claim the number and write the lane docs into the repo. Owner then
      directed: onboard at the AI Portal.
  report:
    path: docs/maintenance/SESSION_CLOSEOUT_HOUSE_INDEX_VDISK_AND_CAPABILITY_VALIDATOR_2026-07-30.md
    kind: session_closeout
---

# Session Closeout -- House index maintenance, VDISK routing boundary, and the declared-capability validator (AIF-079)

Date: 2026-07-30.
Run: `DECLARED-CAPABILITY-VALIDATOR-20260730`. Owner: `member.derald`. Steward: `member.ai.claude.cowork`.
Baseline: `b702b5a5d1cc629c48411af9e93ff879b198e73f` on `development`.
Owning lifecycle: DotTalk++ SDLC (investigation) plus maintenance SDLC (lane authoring).
SDLC lane: intake / design. Truth state: source-defined. Proof state: report.

## One-line summary

Two read-only source investigations (house index incremental maintenance; vdisk routing boundary) produced one new lane `AIF-079`, one new milestone `AIF-043 V6`, and an amendment to `XIDX-TXN-02` M0 -- and a process finding: the portal onboarding was performed at the end of the session rather than the start.

## Scope calibration (declared retroactively -- see the process finding)

```text
operating_mode: maintenance
change_class: C0 (documentation only; no behavioral change)
build_target: documentation_only
product_profile: not_applicable
index_profile: not_applicable
scope_reason: Investigation and lane authoring. No engine source touched, no
  build run, no runtime executed. The findings concern xbase/xindex/cnx/cli/memo
  but the deliverable is documentation.
affected_authorities: AIF-043 lane docs, XIDX-TXN-02 lane doc, AI Portal
  coordination ledger, docs/maintenance lane set.
minimum_gate_set: source-read verification with file:line anchors; independent
  second verification pass; house style conformance; scoped-slice discipline.
deferred_gates_and_residual_risk: No build, no runtime, no .dts. Every claim is
  source-evidenced only. Nothing in this session has earned a runtime tier, and
  the lane docs say so on their face.
```

## 1. What was asked, in three parts

1. **House index.** *"House CNX/V32 and fallback for CDX/LMDB when LMDB is not used. Currently the index is loaded from disk and sorted in ram. After processing with this index, it must be rebuilt because it does no tag mutation with data mutations. It occurred to me that the algorithm we used to update LMDB index keys/tags should work with the house index too. Investigate without coding."*
2. **VDISK.** *"Investigate vdisk and our virtual database/house index support."*
3. **Lane.** *"Agreed, make an aif-nn in a new lane in the ai portal"*, then *"or do we fold it into aif-043"* -- resolved by maintainer ruling (below).
4. **Onboard.** *"Onboard yourself at the ai-portal."*

## 2. What was found

### House index (amends `XIDX-TXN-02` M0)

The premise understates the case. **There is no LMDB-specific algorithm to port.** `IndexManager::apply_replace_snapshot` (`src/xindex/index_manager.cpp:547-576`) is already backend-neutral -- erase every before-key, insert every after-key, per tag -- fed by the `xbase::index_hooks` before/after seam, which fires for CNX today. It lands on stubs: `CnxBackend::upsert/erase` and `CdxNativeBackend::upsert/erase` are `(void)key; (void)rec; stale_ = true;`.

The work is therefore not an algorithm port. It is implementing two virtual functions plus the storage and persistence beneath them.

Lane `XIDX-TXN-02` already exists, M0 met 2026-07-21, marked M1-ready, never built. Five blockers the 07-21 M0 did not surface, recorded as N1-N5: `InxPayload` is immutable by construction; `pos_by_recno_` is a dense persisted position table whose incremental maintenance is O(n) *and* `InxPayload::writeToStream` is itself a stub so the persistence gap is two layers deep; the payload comparators have no recno tiebreaker so `erase` cannot target the right duplicate; multi-tag capture is gated on a `CdxBackend` concrete-class cast that excludes CNX, CDX-native **and** `LmdbBackend`; and `wasStale()` has zero consumers repo-wide while `CNX_HDRF_DIRTY` is never tested.

### VDISK (becomes `AIF-043` milestone V6)

`AIF_043_RAM_DBF_POSITIONING_AND_LIMITATIONS_V1_20260722.md` is accurate on every limitation it claims. The gap is that it does not say whether those limitations are **enforced**. Seven layers route through `is_virtual()`; four do not (memo, legacy `.inx`, LMDB, the `.tbj` journal). Since a path under the RAM root looks virtual, each unrouted writer produces real files inside it without complaint.

Sharpest finding (R2): `VDISK UNMOUNT` calls `ramfs::clear()` unconditionally, dropping the file map **and the root list**, with no check for open areas. Nothing crashes -- the area's `shared_ptr` keeps the buffer alive so reads and writes keep succeeding against an orphaned buffer `VDISK STATUS` cannot see, while `is_virtual()` now returns false for the same path so locks begin writing real `.lock` files, `openCdx` demands an LMDB env, and `cdx_file` opens a disk stream.

### The cross-cutting pattern (becomes `AIF-079`)

Seven instances of **capability declared at the interface, absent at the leaf**, across `xindex`, `cnx`, `cli`, `memo`. Each is individually defensible as a placeholder; collectively they are a gap in the evidence taxonomy -- the declaration reads `source-evidenced` because the symbol exists, while the behavior is only `planned`. Existing validators check documentation shape; none checks capability reality.

### Maintainer ruling: split by nature

Asked whether to open one lane or fold into `AIF-043`. Ruling: **R1-R6 are defects in `AIF-043`'s own scope -> milestone V6, no new number. The validator is cross-cutting, validator-tier, and its proof artifact is a scanner plus a report rather than a `.dts` -> new lane `AIF-079`.**

## 3. Changed (development, `D:\code\ccode`)

| Area | Files | Note |
| --- | --- | --- |
| Coordination | `coordination/aif/AIF-079.claim` | Claimed via `session_coordinator.py claim-aif` (atomic `O_EXCL`) |
| Coordination | `coordination/active_sessions/DECLARED-CAPABILITY-VALIDATOR-20260730.yaml` | Session check-in, lanes `AIF-079,AIF-043` |
| Lane doc | `docs/maintenance/DECLARED_CAPABILITY_VALIDATOR_LANE_V1.md` | New `AIF-079` charter; D1-D5 detectors, seven seed instances, M0-M3 gates |
| Lane doc | `docs/maintenance/AIF_043_V6_ROUTING_BOUNDARY_HARDENING_V1_20260730.md` | New `AIF-043` milestone V6; R1-R6, V6.0-V6.2 gates |
| Session package | `src/AIPortal/sessions/2026-07-30_cowork_house_index_vdisk/README.md` | Curation index |
| Session package | `.../LANE_XIDX_TXN_02_M0_RECONCILIATION_V1_20260730.md` | Findings, amends an existing M0 |
| Session package | `.../AIF_043_VDISK_VIRTUAL_STORE_BOUNDARY_FINDINGS_V1_20260730.md` | Findings |
| This closeout | `docs/maintenance/SESSION_CLOSEOUT_HOUSE_INDEX_VDISK_AND_CAPABILITY_VALIDATOR_2026-07-30.md` | |

**No engine source was changed.** Nothing staged, nothing committed. `git diff --cached --name-only` is empty.

## 4. Verified (proof performed this session)

- **Source reads with file:line anchors.** Every claim in both findings documents and both lane docs carries an anchor; the anchor tables are section 7 of each findings doc.
- **Two independent verification passes.** Twelve claims (house index) and ten claims (vdisk) were re-checked by a separate read of the source before filing. The passes corrected three things: the `.tbj` journal path is absolute, not cwd-relative as first assumed (a narrow lazy-open fallback does produce a cwd-relative `area<N>.tbj`); `LmdbBackend` also fails the `CdxBackend` cast, so the in-code comment "CDX/LMDB: one tag DB per field-backed tag" is wrong and `SET INDEXTXN` never engages for it; and `InxPayload::writeToStream` is a stub, so the 2INX writer lives in `cmd_index.cpp` / `cmd_reindex.cpp` rather than in the class.
- **Collision gate.** `python tools/coordination/aif_collision_gate.py` -> `PASS`. It reports `AIF-079` under the advisory "claim with no intake row"; that is expected and deliberate (section 6).
- **House style.** All five authored files sweep clean for em-dashes, en-dashes, smart quotes, and Unicode arrows.
- **Tree state.** `git status --porcelain` confirms the four new paths are untracked and nothing is staged.

**Explicitly NOT verified:** no build was run, no runtime was started, no `.dts` was executed, no benchmark was taken. Every claim is source-read only. A zero exit code was not treated as proof because no code was executed to exit.

## 5. Process finding -- onboarding happened last, not first (recorded as scar tissue)

The AI Portal Mandatory Start was performed **at the end of this session**, on maintainer instruction, after two investigations and four authored documents. It should have been first.

What made it survivable rather than damaging:

- The first two turns were genuinely report-only ("investigate without coding"), so the mutation guard was satisfied by the shape of the request rather than by having read the rule.
- Mutation began only after explicit authorization ("agreed, make an aif-nn").
- The claim protocol in `CLAUDE.md` was followed (`claim-aif`, no `git add -A`, nothing staged, dirty tree preserved).

What was actually missed, and cost something:

- **House convention.** `CLAUDE.md` states no em-dashes; use `--` / `->`. The first two findings drafts used em-dashes throughout. Caught and fixed at filing time, but the maintainer read the wrong versions in chat first.
- **Scope calibration and the SDLC task fields** were never declared up front. They are declared retroactively above, which is weaker evidence than declaring them before planning.
- **The AIF-006 closeout obligation** was not known while the work was happening, so this closeout is partly a reconstruction -- exactly what "Document As You Work" (AIF-024) says not to do. The material facts survived because the chat carried them, but the portal is explicit that the chat is never the record.

The relevant portal rule is already written for a neighbouring case: *"a session record is a resume aid, not an entry point."* This session is the adjacent failure -- **no entry point was consulted at all**, because the work arrived as a direct technical question rather than as a hand-off. A technical question is not an exemption from initiation either. Recorded here so the lane has its own evidence rather than standing on assertion.

### 5a. Second process finding -- treating MSVC as the necessary gate on a cross-platform engine

Maintainer-flagged, 2026-07-30, after a green WSL build.

Throughout sitting 1 I described the proof gate as "MSVC Release build + `REGRESSION ALL`, host-side" and positioned myself as blocked on it. That framing is wrong, and it cost real capability:

- The engine is **cross-platform by design**. `build-wsl`, `vcpkg-wsl.json`, `wsl_build_dottalkpp.sh`, guarded `.exe` code and a `wsl` configure preset all exist. That preset sets `DOTTALK_INDEX_MODE: LMDB` and the WSL manifest pulls `lmdb`, so the **item A benchmark was provable on Linux the whole time**. I discovered that two turns after asserting the opposite.
- The practical consequence: I produced Windows-shaped handoffs (`cmake --build build --config Release`, `datarun.ps1`) as the primary deliverable, when what was actually useful was Linux-runnable artifacts. The maintainer had to ask for a short WSL build script rather than being handed one.

**What is NOT the correction.** "The agent could have built it itself" does not hold here: the Cowork sandbox has no `cmake`, no `ninja`, none of the `lmdb`/`sqlite3`/`nlohmann`/`sodium` headers, and no privilege to install them. Verified, not assumed. The ceiling in-sandbox is per-translation-unit `g++ -fsyntax-only`.

**The correction that does hold:** on a cross-platform engine, an agent should treat the platform the maintainer can actually run *fastest* as the primary gate, and produce artifacts for it by default. Here that is WSL/Linux for iteration, with MSVC Release reserved as the release gate. The onboarding material names `BUILDING.md`, `CMakePresets.json` and the WSL scripts, but nothing tells a new agent **which build is the fast feedback loop** -- so an agent defaults to the Windows product path and under-serves the maintainer.

Candidate onboarding fix, for review: a line in `AI_README.md` step 2 or the local-access checklist naming the fast in-loop build per platform, so an agent does not have to infer it from preset files after the fact.

## 6. AI-facing docs updated (AIF-006 gate)

| Doc | State |
| --- | --- |
| `docs/agents/CURRENT_TARGET.md` | **Not updated -- correctly.** The active objective (Phase 7 manual web-ascent, `AIF-072`) is unchanged by this session. |
| `AI_README.md` | Not updated. No branch, remote, or authority pointer changed. |
| `docs/ai-friendly/AI_FRIENDLY_DASHBOARD_V1.md` | **Session Log row drafted, deliberately held** -- see below. |
| `docs/ai-friendly/AI_INTERACTION_INTAKE_QUEUE_V1.md` | **`AIF-079` row owed, deliberately held.** Drafted in the session README section 4. Held because the working-tree copy may carry other sessions' uncommitted rows, and fusing several lanes' rows into one lane's slice is what `AI_SESSION_COORDINATION_PROTOCOL_V1.md` forbids. Same precedent as `AIF-078`. |
| `D:\dev\x64base-site` agent-sync page | Not applicable. No outside-AI-visible lane state, Phase-0 decision, or doctrine changed. Two new planned lanes with zero runtime evidence do not meet that bar. |

**Why the two queue/log rows are held rather than written.** `git status` shows `AI_FRIENDLY_DASHBOARD_V1.md` already carrying an unrelated session's uncommitted edit (Current Lane State rows for `AIF-063`/`068`/`069`, dated 2026-07-27). Appending a Session Log row to that file now would mean any commit staging it fuses two lanes' work -- the exact pattern `AI_SESSION_COORDINATION_PROTOCOL_V1.md` forbids and the Pre-Push Gate's "sliced by lane, not blobbed" rule prohibits. The intake queue carries the same hazard. Both rows are therefore **drafted here and in the session README**, to be landed by whoever next batches those shared ledgers. This is the AIF-006 "explicitly declined with a stated reason" path, not an omission; precedent is the `AIF-078` session, which held its intake row for the identical reason.

Drafted Session Log row:

```
| 2026-07-30 | Cowork -- house index maintenance + VDISK routing boundary + declared-capability validator (AIF-079) | **Two read-only source investigations; one new lane, one new milestone, one M0 amendment. No engine source changed.** (1) House index: found there is no LMDB-specific key/tag algorithm to port -- `IndexManager::apply_replace_snapshot` is already backend-neutral and already fires for CNX, landing on stubs (`CnxBackend`/`CdxNativeBackend` `upsert`/`erase` = `stale_ = true`). Lane `XIDX-TXN-02` already existed (M0 met 2026-07-21, M1-ready, never built); recorded five blockers its M0 missed (N1-N5), including that `InxPayload` is immutable by construction, `pos_by_recno_` is a dense persisted position table, the payload comparators have no recno tiebreaker so `erase` cannot target the right duplicate, multi-tag capture is gated on a concrete-class cast that also excludes `LmdbBackend`, and `wasStale()` has zero consumers. (2) VDISK: seven I/O layers route through `is_virtual()`, four do not (memo, legacy `.inx`, LMDB, `.tbj` journal), so unrouted writers produce real files inside the RAM root; sharpest is `VDISK UNMOUNT`, which drops the root list with no open-area check, leaving a live area writing to an orphaned buffer while `is_virtual()` flips false underneath it. Folded into `AIF-043` as milestone **V6** (R1-R6). (3) The cross-cutting pattern -- seven instances of capability declared at the interface and absent at the leaf -- became new lane **AIF-079**, claimed via `claim-aif`. Maintainer ruling: split by nature (defects fold into their lane; the validator gets its own number). Process finding recorded: portal onboarding was performed at the end of the session rather than the start, and the first two drafts violated the no-em-dash house convention. Dev-only, untracked, unstaged, not committed. | `docs/maintenance/SESSION_CLOSEOUT_HOUSE_INDEX_VDISK_AND_CAPABILITY_VALIDATOR_2026-07-30.md` |
```

## 7. Published

**Not promoted. Not published.** Stage reached: **Dev (`D:\code\ccode`) only** -- files authored, untracked, unstaged, uncommitted. `C:\x64base` untouched. GitHub untouched. No branch operation performed.

## 8. Still open -- for the next session

1. **Intake queue row for `AIF-079`** -- drafted (session README section 4), held for slice hygiene. Land with the next intake batch.
2. **Dashboard Session Log row** -- drafted (section 6 above), held because the dashboard already carries an unrelated session's uncommitted edit. Land with the next dashboard batch.
3. **`AIF-079` M0 sub-question** -- suppression granularity: does `status: planned` on a file-level `@dottalk.file` block suppress every symbol in that file, or is symbol-level annotation required? File-level is cheaper and probably too coarse. This decides how noisy the tool is.
4. **`AIF-043` V6.0 R1 decision** -- route memo through ramfs, or refuse memo fields on virtual tables. Refusal is the smaller honest answer; routing is the complete one.
5. **`XIDX-TXN-02` sequencing ruling.** The reconciliation argues for inverting the lane order: prove incremental key maintenance **in RAM first** (`CdxNativeBackend`, where there is no fsync, no torn write, no atomic-rename question, and no `save()` requirement), then port to disk with the durability machinery. That contradicts the 07-21 M1 plan, which starts with `save()`. Needs a ruling before the lane is scheduled.
6. **AIPR allocator.** `AI_RUN_TRACEABILITY_CONTRACT_V1.md` specifies `AIPR-YYYYMMDD-NNN`, but no allocator comparable to `claim-aif` was found. `AIPR-20260730-004` was assigned here by scanning `docs/maintenance` for the highest used id today (001-003, all from the `AIF-078` session). Confirm or correct.
7. **Stale session entry.** `coordination/active_sessions/AIPR-20260729-001.yaml` shows `[STALE]` (330+ min). Left untouched -- not this session's business.

## 9. Provenance pointers

- `src/AIPortal/sessions/2026-07-30_cowork_house_index_vdisk/README.md` -- curation index for this session
- `docs/maintenance/DECLARED_CAPABILITY_VALIDATOR_LANE_V1.md` -- `AIF-079`
- `docs/maintenance/AIF_043_V6_ROUTING_BOUNDARY_HARDENING_V1_20260730.md` -- `AIF-043` V6
- `src/AIPortal/sessions/2026-07-21_claude_recno64_indextxn_onboarding/LANE_CNX_TXN_MUTATIONS_V1_20260721.md` -- `XIDX-TXN-02` lane, amended by this session
- `src/AIPortal/sessions/2026-07-21_claude_recno64_indextxn_onboarding/LANE_XIDX_TXN_02_M0_FINDINGS_V1_20260721.md` -- the M0 this session amends
- `src/AIPortal/sessions/2026-07-21_claude_recno64_indextxn_onboarding/AIF_043_RAM_DBF_POSITIONING_AND_LIMITATIONS_V1_20260722.md` -- the positioning note this session complements
- `src/AIPortal/sessions/2026-07-21_claude_recno64_indextxn_onboarding/VFS_INMEMORY_MILESTONE_PLAN_V1_20260721.md` -- source of the V1-V5 milestone numbering that V6 continues
- `coordination/aif/AIF-079.claim` -- lane claim
