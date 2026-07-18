---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260718-006
  recorded_at_utc: 2026-07-18T02:32:55Z
  agent:
    provider: OpenAI
    product: Codex
    model: not_exposed
    access_mode: local_write
  session:
    id: not_exposed
    chat_reference: not_exposed
  project:
    id: project.x64base.runtime
    root: D:/code/ccode
  git:
    branch: homegrown-cnx-20251112-branch
    baseline_commit: 1ce8f45d79d4a5d80ef7d006c784e54420bd4541
  authorization:
    requested_by: maintainer
    scope: add historical Pinocchio engine benchmarks and machine identity to the active documentation flush
  report:
    path: docs/maintenance/SESSION_CLOSEOUT_PINOCCHIO_HISTORICAL_BASELINE_2026-07-18.md
    kind: session_closeout
---

# Session Closeout — Pinocchio historical engine baseline

Date: 2026-07-18.  
Owning lifecycle: DotTalk++ SDLC.  
SDLC lane: engine performance evidence within the full-stack documentation flush.  
Truth state: historical runtime evidence normalized and validator-proven.  
Publication state: local documentation only.

## Outcome

Pinocchio now has a human-readable historical benchmark subsection, an
eight-row machine-readable ledger, a current-machine profile, automatic machine
capture in the runner, and a fail-closed validator. The first baseline records
the ordered-navigation engine repair without pretending that current workstation
details were captured by the historical runs.

## Initial before/after baseline

| Dataset / operation | Before | After | Improvement |
| --- | ---: | ---: | ---: |
| ENROLL 5,501,358 — `TOP SID` paired run | 66.09 s | 0.0013 s | 50,838.46x |
| ENROLL 5,501,358 — `BOTTOM SID` | 66.51 s | 0.0010 s | 66,510.00x |
| ENROLL 5,501,358 — first `SKIP` | 65.9 s | 0.0015 s | 43,933.33x |
| ENROLL 5,501,358 — `SKIP 1000000` | 87.1 s | 0.021 s | 4,147.62x |
| ENROLL 5,501,358 — `SKIP -1000000000` to top | 529 s | 0.11 s | 4,809.09x |
| ENROLL 5,501,358 — `TOP SID` cross-session | 72.169 s | 0.0013 s | 55,514.62x |
| STUDENTS 1,000,000 — `TOP SID` | 19.478 s | 0.001–0.002 s | 9,739.00–19,478.00x |
| STUDENTS 1,000,000 — `TOP LNAME` | 23.231 s | 0.001–0.002 s | 11,615.50–23,231.00x |

The retained correctness canaries remained green in the source closeouts:
record 1 is `50000000 Taylor Quinn`, LNAME order begins at `Anderson`, descending
order reverses the endpoints, and the recorded `SKIP` boundaries land correctly.

## Machine variable

The July 15 and July 18 benchmark artifacts did not record machine identity.
Every historical ledger row therefore says `machine_type=UNRECORDED` and
`machine_binding=UNRECORDED_IN_SOURCE`.

The current observed workstation profile is retained for future runs only:

- machine type: `Alienware m16 R2`;
- CPU: `Intel(R) Core(TM) Ultra 9 185H`;
- logical processors: `22`;
- memory: `63.5 GiB`;
- OS: `Microsoft Windows 11 Pro 10.0.26200`;
- historical binding: `UNVERIFIED`.

`run_pinocchio.ps1` now accepts `-MachineType <label>` and writes
`data/tmp/pinocchio/machine_profile.json` for each future run. CIM is preferred;
Windows environment data is the fallback.

## Evidence grading

- Phase 1 raw timer transcript:
  `dottalkpp/data/tmp/pinocchio/measure_timed`, SHA-256
  `383FEC725E8ABA9D2F33A55CCEC78CB003B2BBDBD6DF7AD6E30B10AFD05A24A2`.
- Phase 1 closeout:
  `SESSION_CLOSEOUT_PINOCCHIO_PHASE1_2026-07-15.md`, SHA-256
  `5BEF0AA08E80A6C1EDB1619D455039C1F3F5FEB44498DFAE1B3CF4BE658C1CCD`.
- Navigation before/after closeout:
  `SESSION_CLOSEOUT_PINOCCHIO_NAV_PERFORMANCE_2026-07-18.md`, SHA-256
  `9E47A7C5FDA22EC8C379A64C2E9E35C89E91D77C35B156827F11BAEBC65AB6D7`.
- The raw July 18 after transcript was not located in the repository scan. The
  ledger preserves this as `RAW_AFTER_TRANSCRIPT_NOT_LOCATED`; the closeout is
  not relabeled as a raw transcript.

No new multi-million-row benchmark was executed for this documentation pass.
The recorded before/after values are the retained historical runtime results.

## Changed

- Added `Historical engine benchmarks` to
  `docs/maintenance/PINOCCHIO_STRESS_TEST_PLAN_V1.md`.
- Added `docs/maintenance/PINOCCHIO_HISTORICAL_ENGINE_BENCHMARKS_V1.csv`.
- Added `docs/maintenance/PINOCCHIO_MACHINE_PROFILE_CURRENT_V1.json`.
- Added machine-profile capture and `-MachineType` to
  `dottalkpp/scripts/pinocchio/run_pinocchio.ps1` and its README.
- Added `tools/fullstack_docs/validate_pinocchio_benchmarks.py` and focused
  regression tests.

## Verification

- Benchmark validator: `PASS`, 8 rows, 0 findings.
- Current profile: `Alienware m16 R2`; required profile fields populated;
  historical binding `UNVERIFIED`.
- Full-stack documentation tests: 13 passed.
- PowerShell parser: `PASS`, 0 errors for `run_pinocchio.ps1`.
- No protected DBF/CDX/LMDB data, accepted manual pointer, website, commit, push,
  or publication target was changed.

## Next gate

Resume the selective-merge contextual review. The next Pinocchio performance
run should retain both raw build/measure transcripts and the generated machine
profile, then append new benchmark rows rather than replacing this baseline.
