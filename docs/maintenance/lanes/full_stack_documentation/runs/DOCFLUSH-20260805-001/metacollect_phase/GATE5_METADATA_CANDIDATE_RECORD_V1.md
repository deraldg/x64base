# Gate 5 metadata candidate record v1

Run: `DOCFLUSH-20260805-001`
Gate: 5, refresh organizing/provenance layers (full-stack doc flush v4)
Recorded: 2026-08-05
Decision: `PASS_CANDIDATE_ONLY` (no live metadata import; import remains a separate reviewed gate)

## What ran

`metacollect` (standalone external tool; `@dottalk.external` contract in
`src/tools/metacollect_main.cpp`; runbook `../../METACOLLECT_RUNBOOK_V1.md`)
re-reflected `D:\code\ccode\src` after the v4 source changes and emitted seed
candidates. `--include-dev-commands` was set so the dev/diagnostic commands added
this flush (BBS, NET, CANARY, CMDREL, FORMULA, EDIT, EVALDIFF, BUILDVECTORS) are
represented; `--sysargs-include-keywords` widened SYSARGS.

- Exe: `build\Release\metacollect.exe`
- Engine version at build: `v0.6 2026-08-05 b2699ee9 dirty`
- Command: `metacollect --source-root ...\src --include-dev-commands
  --sysargs-include-keywords --syscmd-import-out ... --sysfunc-import-out ...
  --sysargs-import-out ... > metacollect_facts_v1.csv`

## Bound evidence (candidate CSVs in this dir)

| File | Rows | SHA-256 (prefix) |
| --- | --- | --- |
| `SYSCMD_IMPORT_candidate_v1.csv` | 226 | `5c3302eb3c96c387` |
| `SYSFUNC_IMPORT_candidate_v1.csv` | 74 | `dd4b211cfeaef0ef` |
| `SYSARGS_IMPORT_candidate_v1.csv` | 959 | `1d1372324ac8058b` |
| `metacollect_facts_v1.csv` | 1045 | `97b81673a7ec75b4` |

`metacollect_stderr_v1.txt` records the three export row counts (226 / 74 / 959).

## Gate 5 acceptance

- Candidate and live data are visibly distinct: outputs live under this run's
  `metacollect_phase/` and were NOT imported into live metadata DBFs. PASS.
- No external helper is presented as authority: metacollect's `@dottalk.external`
  contract states it is read-only and candidate-only; these CSVs are review
  candidates, not a system of record. PASS.
- The run record accounts for every generated report: four CSVs + the stderr log,
  all listed above. PASS.

## Not done this pass (optional / deferred)

- Source-vs-live `--compare` drift report was NOT run (optional; needs
  `--metadata-root`). Can be run later per the runbook.
- Live metadata import is intentionally NOT performed; it is a separate reviewed
  gate outside this push.

## Disposition

Phase 5 is candidate-complete for this push. The seed candidates are staged for a
future reviewed metadata-import gate; nothing downstream (HELP, catalog, runtime)
was changed.
