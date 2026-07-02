# Repo Hygiene Relocation Checklist Summary - 2026-06-30

Status: report-only checklist summary.
Checklist: `docs/maintenance/repo_hygiene_relocation_checklist_2026-06-30.csv`

## Scope

This pass classified root-level entries under `D:\code\ccode`.

No files were moved, deleted, overwritten, or staged.

## Counts

| Classification | Count |
| --- | ---: |
| keep | 66 |
| move candidate | 71 |
| review before action | 164 |

Risk split:

| Classification / Risk | Count |
| --- | ---: |
| keep / low | 66 |
| move / low | 42 |
| move / medium | 29 |
| review / high | 30 |
| review / medium | 134 |

## Low-Risk Move Candidates

These are mostly generated output or accidental root litter:

- `build*` directories
- `.venv`, `.vs`, `.vscode`
- `__pycache__`
- `vcpkg_installed`
- `dist`, `bin`, `results`, `TMP`
- root CMake/build output: `CMakeCache.txt`, `build.ninja`,
  `cmake_install.cmake`, `CTestTestfile.cmake`, `DartConfiguration.tcl`
- accidental root files: `--runtime-root`, `-Filter`, `-Pattern`, `=`,
  `Unknown`
- screenshots named `Screenshot 2026-*.jpg`
- `tmpsql_regression.sqlite`

Recommended destination:

```text
C:\dottalkpp-generated
C:\dottalkpp-scratch\accidental-root-litter
C:\dottalkpp-archive\screenshots
```

## Medium-Risk Move Candidates

These should move only after a quick look because they can contain useful
history or package material:

- `_drops`
- `_incoming`
- `.mdo_backups`
- `backups`
- `memo_backup`
- `AI_logs`
- `chatgpt prgs`
- `data.save`
- `save`
- `Side Projects`
- root-level `*.zip` archives

Recommended destination:

```text
C:\dottalkpp-archive
C:\dottalkpp-archive\zip-packages
```

## Review-First Items

The checklist marks many entries as review-first because they may contain source,
docs, case material, scripts, or reusable artifacts. Do not bulk-move these.

Important review-first examples:

- `D:\code\ccode\x64base`
- `Bible`
- `books`
- `designs`
- `FoxApp`, `FoxAppShell_mtv`, `fox`, `foxcli`
- `mcc`
- `memo_sidecar_v1`
- `palette`
- `py`, `pycrud`, `python_misc`
- `sqlite-gui`
- root-level scripts, text notes, CSVs, patches, and assets

## x64base Guardrail

Do not move or overwrite `D:\code\ccode\x64base`.

Derald confirmed that the `D:` copy is the recent staged GitHub version and
`C:\x64base` is a backup. The backup may be overwritten/refreshed from the
`D:` copy if Derald explicitly asks for that. The `D:` copy is clean and ahead
of the backup:

```text
D:\code\ccode\x64base HEAD: f2a9cc94c147f53922f880ec7835d03b3412b8f0
C:\x64base              HEAD: 22db1c95a400ad30992721a532590ea131e4c52e
```

Do not make `C:\x64base` the active home unless Derald explicitly changes that
decision.

Do not overwrite `C:\x64base` unless Derald explicitly asks for a backup
refresh from `D:\code\ccode\x64base`.

## Recommended Next Action

If moving files is approved later, start with only the low-risk move candidates.
Use a timestamped destination folder and re-run `git status --short` after the
move.

Do not delete anything in the next pass.
