# Manualgen Product Preservation v0

Status: preserved

Generated: 2026-07-04

## Preserved Product Documents

| Artifact | SHA-256 |
| --- | --- |
| `D:/code/ccode/labtalk/products/manualgen_product_board_v0.html` | `985C42D00F7B6E5B327AE0CBC654F90CE9E31BDF08E82F2FF20419987E6C8154` |
| `D:/code/ccode/labtalk/products/manualgen_product_map_v0.md` | `E531980BF73ECF6976EBF4066523B74EBC92E093C0C8FE86B0C560255419D619` |

## Hardening Evidence

| Artifact | SHA-256 |
| --- | --- |
| `D:/code/ccode/tools/manualgen/README.md` | `D500D855EF81DC203CF11FD5A8C789D39EED5E84595E6B23CEAF7FA43097EA8A` |
| `D:/code/ccode/docs/manuals/developer/manualgen/reports/mdo_226_validate_summary_v1.csv` | `68054ED88B9689C5FE7A91D5AAA39CE07B5E20BA9B58E598A825DF1631F38B14` |
| `D:/code/ccode/docs/manuals/developer/manualgen/reports/mdo_226_build_dry_run_summary_v1.csv` | `9821EE9813F0C6FA49BF46B2533796FB178DA28B414DB357F463C67FFB912FED` |

## Observed Product State

- Repo-local vcpkg interpreter: `D:/code/ccode/build/vcpkg_installed/x64-windows/tools/python3/python.exe`
- vcpkg Python version: `3.12.9`
- `manualgen validate`: `validation_fail_rows=0`, `validation_review_rows=0`, `boundary_fail_rows=0`
- `manualgen build-dry-run`: `validation_fail_rows=0`, `boundary_fail_rows=0`, `dry_run_hash_matches_current_combined=0`
- MAN* catalog status remains `DRIFT` with `drift_failures=8`

## Hardening Changes Started

- Corrected `tools/manualgen/README.md` command list by removing stale `doctor` command and adding the real command surface.
- Pointed README and product board to repo-local vcpkg Python 3.12.9.
- Reclassified the validation failure as an interpreter-selection issue rather than a manualgen product defect.

## Next Hardening Gate

Classify the MAN* catalog drift rows. Current evidence suggests expected table
counts pass, while the CLI additionally reports duplicate extra-table rows.
