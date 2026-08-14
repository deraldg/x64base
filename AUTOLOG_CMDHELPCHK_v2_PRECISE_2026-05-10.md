# AUTOLOG - 2026-05-10 - CMDHELPCHK v2 precise source audit

## Subsystem

HELP / command metadata / external audit tooling.

## Files produced

- `tools/help/cmdhelpchk_v2_scan.py`
- `docs/generated/reports/cmdhelpchk_v2_report.md`
- `docs/generated/reports/cmdhelpchk_v2_report.csv`
- `README_CMDHELPCHK_v2_PRECISE.md`

## Intent

Replace the first broad scanner pass with a more precise source-aware scanner that avoids false positives from unrelated text mentions.

## Change

- Added command-specific source file mapping for the ten seed commands.
- Added exact registry proof from `src/cli/shell_commands.cpp`.
- Added exact handler proof from command-local source files.
- Added command-local `@dottalk.usage v1` detection.
- Added command-local usage output detection.
- Added optional `--tree-file` support for source-only audit situations.
- Added `TREE_PRESENT_UNREAD` status to distinguish path listing from readable file content.

## Behavior preserved

- Scanner remains external and read-only except for generated reports.
- No DBF/DBT/CDX/LMDB row parsing.
- No runtime command integration.
- No mutation of docs/source/data/workspaces.

## Tests run

```bash
python3 tools/help/cmdhelpchk_v2_scan.py \
  --repo /mnt/data/dottalk_src/ccode_homegrown_20260510-110751 \
  --tree-file /mnt/data/dottalkpp_tree.txt \
  --out-dir /mnt/data/cmdhelpchk_v2_precise_report
```

Result: completed successfully, generated Markdown and CSV reports with 163 evidence rows.

## Findings

- All ten seed commands have confirmed source-level registry and handler evidence.
- The first-pass false positives were corrected: broad mentions no longer satisfy source usage/usage-output checks.
- Confirmed current source gaps for command-local usage metadata/output: `HELP`, `CMDHELPCHK`, and `LIST`.
- `CMDHELPCHK` already exists as a runtime command, so v2 should not be framed as a wholly new command replacement.
- `SET INDEX` and `SET ORDER` are source-confirmed routed SET-family forms plus standalone compatibility handlers.

## Risks

- Metadata/doc/data/log verification remains limited because only a tree listing, not file contents, was available for those layers.
- Row-level DBF verification still requires an x64base-aware reader or a safe runtime export.

## Next recommended action

Drop the precise scanner into the real dev tree and run it there. Then provide or expose actual metadata/data/help/docs/log contents if row-level and doc-level verification are required.
