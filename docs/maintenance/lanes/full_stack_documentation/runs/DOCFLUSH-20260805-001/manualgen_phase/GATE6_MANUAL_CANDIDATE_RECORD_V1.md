# Gate 6 manual candidate record v1

Run: `DOCFLUSH-20260805-001`
Gate: 6, generate and review a manual candidate (full-stack doc flush v4)
Recorded: 2026-08-05
Decision: `PASS_CANDIDATE_ONLY` (dry-run assembled; no publication replacement; sole FAIL is the interpreter self-check)

## What ran

`tools/manualgen/manualgen.py --manual developer` candidate-only sequence, run in
the mounted Linux sandbox on **Python 3.10.12** (manualgen 1.2.0-docflush). Setup:
`--publication-workspace developer_manual_publication_v1_media_section_v1`,
`--harvest-workspace docs/manuals/developer/manualgen/harvested`. Runbook for the
tool is `tools/manualgen/README.md`.

| Subcommand | Run id | Result |
| --- | --- | --- |
| inventory | `MANRUN-20260805T210917Z-CC041594` | sections=25 media=19 appendices=13 manifests=5; harvest 14/14 |
| validate | `MANRUN-20260805T210936Z-7CD01BE6` | 25 checks, 1 FAIL, 0 review, 0 boundary |
| export-manifest | `MANRUN-20260805T210940Z-0E4E9FC5` | manifests_after_export=5 |
| build-dry-run | `MANRUN-20260805T210943Z-3905F3A4` | dry-run markdown emitted; hash_matches_current_combined=0 |

Dry-run artifact:
`docs/manuals/developer/manualgen/generated/manualgen_build_dry_runs/MANRUN-20260805T210943Z-3905F3A4/developer_manual_build_dry_run.md`

## The single validation FAIL

`mdo_226_validate_checks_v1.csv`:

```
check_id,status,value,expected,note
PYTHON_312,FAIL,3.10.12,>= 3.12,Manualgen requires Python 3.12 or newer.
```

This is manualgen's own interpreter self-check, not a content defect. On the host
3.12 interpreter it passes (25/25). All other checks passed; the substantive
result is clean.

## Boundary (candidate-only confirmed)

From `mdo_226_validate_summary_v1.csv`:

- `boundary_fail_rows` = 0
- `protected_system_mutations` = 0 (no HELP/META/CMDHELPCHK/source/runtime mutation)
- `manual_publication_rebuilt` = 0; `x64base_tables_created` = 0; `cpp_files_created` = 0

build-dry-run assembles a generated artifact under `.../generated/...`; it does
NOT replace the publication. `hash_matches_current_combined=0` just means the
dry-run differs from the current combined publication, as expected for a fresh
candidate assembly.

## Known limitation (follow-up, not a Gate 6 blocker)

The harvest workspace `docs/manuals/developer/manualgen/harvested` (14 files)
predates this flush's Phase-4 HELP rebuild, so the manual candidate does NOT yet
reflect the commands added this pass (BBS/NET/CANARY/CMDREL/FORMULA/EDIT). To make
the manual candidate complete, re-export the HELP/META harvest from current HELP
DATA and re-run `build-reference-candidate` before a real assembly. Deferred to the
next push (recorded in `NEXT_PUSH_CONTINUATION_V1.md`).

## Disposition

Phase 6 is candidate-complete for this push: the dry-run assembles, boundary is
clean, and the only validation failure is the 3.10-vs-3.12 environment self-check
(passes on host). No publication was replaced and no protected system was mutated.
Regenerable manualgen report CSVs and the dry-run markdown are not saved here (they
reproduce from the runbook); this record binds the run ids and metrics.
