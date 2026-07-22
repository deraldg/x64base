# Current Target

Status: active.
Updated: 2026-07-22.
Supersedes: the completed staging-restoration/publication target recorded below.

## Development Focus Update — 2026-07-21/22 (runtime DEF family, build vectors, identity/RBAC)

Cowork development (dev-only unless noted):

- **Runtime DEF family shipped** (x8x16x32x64 lane): `EXAMPLE` built-in + `DEFCMD`/`UNDEFCMD`
  and `DEFFN`/`UNDEFFN` on a new live `fn_custom` expression-function registry — mint
  session-only commands/functions at runtime, no rebuild; build-proven; `DEF_FAMILY` regression;
  DEFTYPE parked. Fox `IMAGE DEFAULT`/`WEB DEFAULT/RETRO` also shipped. Committed + pushed to origin.
- **AI dev-tools security doctrine + dormant permission gate** (`ai_devtools_policy.hpp`, permits by
  default; owner-activatable) + the binding "ask for limited permission" protocol published to `AI_PORTAL.md`.
- **BUILD_VECTORS (AIF-044)** engine M1-M5: a generated `build_vectors.{hpp,json}` capacity authority;
  `MAX_FIELDS`/`MAX_AREA`/`MAX_ROWS`/x64 names + record ceilings now derive from one place (GATE #1
  areas=512; the inert `DOTTALK_MAX_AREA` drift closed); runtime `BUILDVECTORS` + `prompt_char`. Green;
  committed + pushed.
- **`project.x64base.identity` (AIF-045) opened full-blast** — the identity/RBAC/authorization layer the
  AI Portal needs. External plan evaluated + endorsed; M0 Contract v1 + M1a domain entities + M1b
  permission resolver, both g++-proven standalone. M2 (x64base schema) in progress. Not yet in the MSVC build.

See the dashboard Session Log + lane docs (`RUNTIME_DEF_FAMILY_LANE_V1.md`,
`AI_DEV_TOOLS_SECURITY_DOCTRINE_V1.md`, `BUILD_VECTORS_LANE_V1.md`, `IDENTITY_RBAC_MANAGEMENT_LANE_V1.md`,
`IDENTITY_RBAC_CONTRACT_V1.md`).

## Development Focus Update — 2026-07-20 (DotScript arrays live + DTV Phase-0)

Latest active work — the arrays + DTV milestone was **promoted + pushed** to `C:\x64base`
→ `github.com/deraldg/x64base` `main` `7f7b7c75` (28 files). The broader maintainer-gated
promotion objective below remains open (other in-flight lanes still dev-only):

- **DotScript arrays are live** (AIF-038): `{…}` literals, scoped `$name` memory
  variables (`dottalk::dotscript::VarStore`), one-based `$a[n]` subscripts (nested/
  chained), stored by real reference; MSVC-green + REPL-proven.
- **Canonical DotTalk Value (DTV) Phase-0 COMPLETE (8/8):** `dottalk::value::Value` is
  the maintainer-signed canonical two-tier value; ChatGPT's amended (unsigned-RECNO64)
  foundation is integrated as an isolated `dottalk_value` lib (real `MemoRef`), MSVC-green.
  Next is the standalone wire + comparison + adapter construction, then the tuple lane.
- **Doc-only live portal:** website Agent Sync page (`/docs/labtalk/agent-sync`) keeps
  outside AIs current between snapshots; refreshed each closeout (AIF-006).

See `docs/maintenance/SESSION_CLOSEOUT_DTV_FOUNDATION_INTEGRATED_2026-07-20.md`.

## Development Focus Update — 2026-07-20

The maintainer-gated promotion objective below is still unchanged and open — no
branch, commit, or push; `C:\x64base`/GitHub untouched.

Active work 2026-07-20 systematized the **documentation architecture** on the
simplex/duplex spine, all dev-only (engine tree) with website changes staged in
`D:\dev\x64base-site` behind the same push gate:

- **Website content classification manifest (AIF-033, WEBSITE-ASSEMBLY M1).** All
  108 website pages classified on a direction × class grid into
  `tools/fullstack_docs/website_content_manifest.yaml` (generated 6 / derived 23 /
  maintained 54 / reported 6 / static 19). It shares its `class`+`direction`
  vocabulary with the manual manifest, so the manual and website sit on one spine.
- **Doc/SDLC model pin (AIF-034).** Pinned (not built): the model refined to a graph
  with three source-of-record origins — implementation, the AI-Portal (source +
  governor), and the manual’s authored branch — plus reviewed duplex manual↔website.
  Trigger: a doc/SDLC model change drives a flowchart/diagram-update pass.
- **Manual assemblage (AIF-035, MANUAL-ASSEMBLY M1-M5).** A 22-part bill of materials
  drives a manifest-driven assembler (`tools/manualgen/assemble_manual.py`) that
  builds the developer manual (spine + authored branch + generated front/back
  matter) — 8 generators real (63 functions harvested, 183 command pages + 12
  diagrams bound, generated TOC/glossary/index + a **colophon that records how the
  manual assembled itself**), 22/22 parts, 13,782 lines. A per-class drift gate
  (`tools/manualgen/check_manual_drift.py`) FAILs the build on generated-region
  drift (proven PASS→corrupt-FAIL→PASS). MD+PDF+HTML exports are staged to the site
  under always-latest permalinks (`/downloads/current/developer-manual-latest.*`)
  with two educational pages. The assembler writes to `generated/`; acceptance stays
  gated (the accepted manual remains the reviewed baseline). M6 (retire the ~20-step
  hand-stitch) is the open next step. Development lesson:
  `docs/maintenance/MANUAL_ASSEMBLY_HISTORIFY_OLD_TO_NEW_V1.md`.

Closeout `docs/maintenance/SESSION_CLOSEOUT_MANUAL_ASSEMBLY_2026-07-20.md`
(AIPR-20260720-001); Session Log + lane state in
`docs/ai-friendly/AI_FRIENDLY_DASHBOARD_V1.md`; intake rows AIF-033/034/035. None of
this changes the authority chain or the promotion gate below.

Later the same day, two more dev-only lanes landed **build-green** (MSVC Release):
**AIF-036 `stop_on_error[severity]`** — a `STOP_ON_ERROR` command + `SET ERRORSTOP`
alias + `DOTTALK_ERRORSTOP` env that abort a running script on a new error at/above
an OFF/WARNING/ERROR threshold, keyed on the messaging-recorded error severity; and
**AIF-037 "Representative by Design"** — a teaching-grade codex principle (source
teaches, so source must be representative) + the Rule of Three, whose first
application consolidated six drifting comment/line-lexing helpers into one
unit-proven `src/cli/dotscript_lexing` module and added the canonical comment set
(`*`/`&&`/`REM` + tolerated `#`/`//`). Closeout
`docs/maintenance/SESSION_CLOSEOUT_DOTSCRIPT_ERRORSTOP_LEXING_2026-07-20.md`
(AIPR-20260720-002). Also reviewed an external DotScript-array spec (advisory). None
of this changes the authority chain or the promotion gate below.

Two **PLANNED design lanes** were then opened (docs-only, no source written):
**AIF-038 DotScript arrays** — design authority + machine catalog stored
(`DOTSCRIPT_ARRAYS_SPEC_V1.md`, `DotScript_Arrays_Catalog_v1.json`,
`DOTSCRIPT_ARRAYS_LANE_V1.md`); arrays remain **absent in the engine** and the lane
requires a Phase-0 runtime reconciliation before any Phase-1 code. **AIF-039 PDLC
(Programming Development Life Cycle) student/working model** — the terminology/framing
note (`PDLC_STUDENT_WORKING_MODEL_LANE_V1.md`), tying the incoming Tuple-System
field-type extension in as its worked exemplar. Both are PLANNED, dev-only, not
promoted; neither changes the authority chain or the promotion gate.

## Development Focus Update — 2026-07-19

The maintainer-gated promotion objective below (reconcile public corrections into
development, then push reviewed staging) is unchanged and still open — no branch,
commit, or push has been made, and `C:\x64base`/GitHub are untouched.

Active development since 2026-07-16 has been in the Pinocchio scale/durability
lane (AIF-017 / AIF-023), all in `D:\code\ccode` on the existing branch and all
dev-only (not promoted):

- **Scale-verb hardening (Phase 1.3).** The scale sweep's remaining O(n) verbs
  are fixed and hash-bound proven: `SEEK` keyed range-seek (57s → ms), `DELETE`/
  `RECALL` bulk write-transaction batching under an active order (65.4s → 37.8s),
  `AGGS ALL` single-pass multi-aggregate (~4×), plus the earlier nav `TOP`/`SKIP`
  LMDB-cursor fix. Companion `SET FILTER`/aggregate `FOR` string-literal fix.
- **Table-buffer durability WAL (AIF-023).** `COMMIT`/`ROLLBACK` are now
  crash-recoverable via a durable `.tbj` redo log (three teed-transcript phases:
  durable writer, recovery-on-open, buffered `DELETE`). Enabled only under
  `TABLE BUFFER PERSISTENT`; default RamOnly behavior unchanged; the
  multiple-retained-edits-per-field capability is preserved (added
  `TABLE BUFFER HISTORY ON|OFF`). Scoped durability gain, not a full-ACID claim;
  DBF-`fsync` and CDX/LMDB reconciliation remain open hardening.
- **Field-type codec architecture (AIF-030, 2026-07-19).** The field layer is now
  a codec registry, not fixed-width text: `I`/`B`/`Y`/`T` store real VFP binary,
  and a worked custom type (`X`=pronoun) plugs in through a single
  `register_field_type` call with zero switch edits (M4b — the registry feeds the
  CREATE/validation chain; five hardcoded gates were deleted). VFP interop is
  proven both directions by an independent spec-based reader/writer. M1–M5 proven
  (`dottalkpp_field_codec_test` green + live shakedowns + third-party VFP
  read/write). Retired AIF-017 (`I` truncation) + AIF-028 (date coercion); found +
  fixed AIF-031 (numeric formatting locale-grouping + precision loss). Dev-only,
  uncommitted. Closeout `SESSION_CLOSEOUT_FIELDTYPE_CODEC_2026-07-19.md`
  (AIPR-20260719-007).
- **RECNO64 end-to-end 64-bit record addressing (AIF-027, 2026-07-19).** The
  remaining 32-bit record-number runtime paths are widened to 64-bit —
  positioning (`gotoRec64`), GO/GOTO/RECNO, ordered nav (`logical_nav` +
  `go_endpoint`/`skip_relative`), the table-buffer change key + COMMIT
  aggregation, record locks, the index-hook `apply_replace` chain, and the CDX
  keyed-seek decoders (M1-M3 + M4-1/2/3) — build-green + warning-clean +
  regression-clean (CURSOR x32/CNX, INDEX_X64 v64/CDX, `table_buffer.dts` x64). A
  keep-32-bit legacy-backend capability report (M4-4) is build-pending. The
  `recno()`/`recLength()` de-saturation + INT32/UINT32 boundary proofs (M4-5) — the
  only decisive proof of addressing past 2.1 B — are a separate focused project.
  Closeout `SESSION_CLOSEOUT_RECNO64_M1_M4_2026-07-19.md` (AIPR-20260719-006).

Closeouts and Session Log rows are recorded in
`docs/ai-friendly/AI_FRIENDLY_DASHBOARD_V1.md`; the durability lane is intake row
AIF-023. None of this changes the authority chain or the promotion gate below;
it is queued behind the same maintainer-reviewed staging commit/push.

## Current Objective — Reconcile Public Corrections Into Development

Public AI Portal consistency work was completed through:

- `100169433b583e5f51eafdeea130607d71942376` — public-state reconciliation;
- `a0cf52654c4f8e834e969e3c2524fd397d627a95` — canonical AI startup path;
- `fa7c04dcea07a2f0b5a027fba7bc953651cd83df` — public consistency closeout.

Those corrections were made against the public GitHub snapshot. This local
session is reconciling them into the authoritative development tree without
overwriting newer development facts, then projecting the reviewed result back
through disposable staging.

```text
D:\code\ccode -> C:\x64base -> github.com/deraldg/x64base
```

The reconciliation must:

1. preserve the newer Pinocchio and Messaging rows already using AIF-017 and
   AIF-018;
2. move the public manual-drift record to the next free identifier, AIF-019;
3. preserve the published cold-clone evidence and canonical startup path;
4. rebuild `C:\x64base` from public `main` plus the corrected manifest overlay;
5. stop for reviewed staging commit/push after proving the diff is clean.

Current stage: steps 1 through 4 are complete. The corrected portal set is
projected into `C:\x64base`, its AIF identifiers and authority markers pass, the
prohibited-artifact scan is empty, and development/staging hashes match. The
remaining gate is the maintainer-reviewed staging commit/push; the candidate
also includes the manifest-approved Pinocchio plan, scripts, proof closeout, and
contract-intake additions.

Primary handoffs:

```text
docs/maintenance/SESSION_CLOSEOUT_AI_PORTAL_PUBLIC_CONSISTENCY_2026-07-15.md
docs/maintenance/SESSION_CLOSEOUT_AI_PORTAL_DEVELOPMENT_RECONCILIATION_2026-07-15.md
```

Do not reverse the authority chain by treating the GitHub versions as newer
truth merely because they were published later.

## Previous Objective Resolution — 2026-07-15

The staging-restoration and first-publication objective recorded below is
complete. The public state at completion was
`b9d480215c036178ba99b5109a8a2489ee89b215`; later documentation-only
reconciliation advanced `main` through the commits listed above.

The cold-clone fixes were published in:

- `46e021594bee25fd40fe9b79e318c691e1a714a0` — self-contained clone journey,
  location-honest launch/databuild scripts, and proof records;
- `b9d480215c036178ba99b5109a8a2489ee89b215` — valid DotScript `&&` comment
  syntax in the printed `DO X64` example.

The remaining sections are preserved as the state and reasoning that existed
when this previous target was active on 2026-07-14.

## Authority Restatement

```text
D:\code\ccode              authoritative development source and runtime truth
C:\x64base                 clean staging repository -> github.com/deraldg/x64base
github.com/deraldg/x64base public snapshot
```

`C:\x64base` is the **clean staging repository**, maintainer-declared
2026-07-14. It is not a backup. Earlier text in this file called it a backup;
that was wrong and has been removed. The authoritative statement lives in
`AI_PORTAL.md` under "What `C:\x64base` Is — and Is Not".

## Task

Restore `C:\x64base` to a clean staging state, so that what is published to
`github.com/deraldg/x64base` is exactly the reviewed, relevant subset of
`D:\code\ccode`.

## Staging State — RESOLVED 2026-07-14

`C:\x64base` is now clean and on `main`.

| Check | State |
| --- | --- |
| Remote | `https://github.com/deraldg/x64base.git` |
| Checked-out branch | **`main`**, tracking `origin/main` |
| HEAD | `a625ea1d` — *Merge pull request #6 from deraldg/codex/labtalk-dottalk-sdlc-planning* |
| Position vs `origin/main` | even |

### What the earlier confusion was

The staging repo had been sitting on `codex/labtalk-dottalk-sdlc-planning` with
a two-day-old remote cache. That branch's 11 commits **had already been merged**
as PR #6, and GitHub had auto-deleted the branch on merge. Local `origin/*` refs
still showed it, because nobody had fetched.

Lesson, recorded so it is not relearned: **`origin/*` refs are a cache, not the
remote.** Working-copy and remote-tracking state do not prove GitHub state. Check
`.git/FETCH_HEAD` age, or run `git ls-remote`, before reasoning about what is
published.

### Safety nets left in place

- `git stash` `stash@{0}` — the 101 tracked modifications that were in the
  staging working tree before the reset. All 13 modified C++/header files were
  verified byte-identical to `D:\code\ccode`, so nothing original was lost.
- `$HOME\x64base_uncommitted_2026-07-14.patch` — same content as a patch file.
- `rescue-codex-sdlc` — local branch pinned to the pre-merge branch tip.

All three are redundant now that the merge story is understood. Drop them when
you are satisfied.

There is also an **older, pre-existing `stash@{1}`** — *"local staged gui and
source work before github sync"*, from `upgrade/selfdoc-usage-contract`. It
predates this work and was not touched. Review before discarding.

## Expected Fix

1. Stop the litter at the source: `.gitignore` in `D:\code\ccode` now excludes
   `*.bak_*` and `*.before_mdo_*` sidecar patterns, so they are never promoted.
2. Confirm the promotion filter honours those patterns before the next sync.
3. Verify publication completeness with `git ls-files`, not a green build.
   `src/CMakeLists.txt` uses `file(GLOB_RECURSE ...)`, so an untracked `.cpp`
   in staging compiles locally while remaining absent from GitHub.

## Next — the first clean PR

Staging is on `main` and clean. The work below lands as one reviewable PR
against a current baseline.

**Done in `D:\code\ccode`, uncommitted:**

1. `.gitignore` — sidecar patterns (`*.bak_*`, `*.before_mdo_*`, `*.save`) and
   the LMDB exclusion (`/dottalkpp/data/lmdb/`, `**/*.cdx.d/`). 53 GB measured.
2. Sidecar purge — 148 files, 15.1 MB removed. Manifest in
   `docs/maintenance/SIDECAR_PURGE_20260714-094942.txt`.
3. AI portal authority corrections + the AIF-006 closeout gate.
4. Index-expression contract drift repaired across 13 files. See
   `docs/contracts/reports/CONTRACT_DRIFT_INDEX_EXPRESSION_2026-07-14.md`.
5. MCC fixture rebuild lane — `dottalkpp/data/scripts/mcc/`.

**Not yet run:**

6. `dottalkpp/scripts/mcc/extract_mcc_og.ps1` — unpack the canonical archive.
7. The three flavor scripts under `DOTSCRIPT TRACE`. They are
   `CANDIDATE / REVIEW_BEFORE_EXECUTION` and have never been executed. A zero
   exit code is not proof; review the transcripts.
8. `tools/staging/promote_data_fixtures.ps1` — dev -> staging, LMDB blocked by
   a hard deny-list gate that throws rather than let a `*.cdx.d` through.
9. Branch, commit, push, PR.

## Deliberately Out Of Scope

- **Development-tree hygiene beyond sidecars.** Root-level scratch `.txt` files,
  `src/gui.zip`, `src/$envVCPKG_ROOT = ...txt`. A separate lane. Do not let it
  creep into the fixture PR.
- **`stash@{1}` in `C:\x64base`** — pre-existing parked work from
  `upgrade/selfdoc-usage-contract`. Not this task's business.

## Do Not Touch

- Do not clean, reset, or broadly stage the `D:\code\ccode` working tree.
  A dirty development tree is normal and is not a release risk signal.
- Do not make original changes in `C:\x64base`. Promote from `D:\code\ccode`.
- Do not mutate DBF data, HELP tables, metadata catalogs, generated catalogs,
  publication outputs, runtime fixtures, backups, or archives unless the
  current task explicitly authorizes it.
- Do not create, switch, or rename branches without explicit instruction.

## Proof Needed

- `git status --short` in each root before and after any promotion pass.
- A `git ls-files` check that every source required by the CMake glob is
  tracked.
- A relocation checklist before any file moves.

## History

The previous target (2026-06-29) described two clean x64base repo copies, named
`D:\code\ccode\x64base` as the recent staged GitHub version, and treated
`C:\x64base` as its backup.

That target is closed as stale on two counts, both verified 2026-07-14:

- `D:\code\ccode\x64base` **does not exist** on disk.
- `C:\x64base` is the staging repository, not a backup, and is checked out on
  `codex/labtalk-dottalk-sdlc-planning` — not the
  `upgrade/selfdoc-usage-contract` branch that target recorded.

An onboarding document drifting this far out of date is the failure mode the
closeout-updates-startup gate is meant to prevent. That gate is queued as
`AIF-006` in `docs/ai-friendly/AI_INTERACTION_INTAKE_QUEUE_V1.md`.
