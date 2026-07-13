# Manualgen Product Map v0

Status: product board companion

Open the product board:

```text
D:/code/ccode/labtalk/products/manualgen_product_board_v0.html
```

Preservation record:

```text
D:/code/ccode/labtalk/products/manualgen_product_preservation_v0.md
```

## What The Product Is

Manualgen is no longer just a script lane. It currently has these product
surfaces:

- active primary reader manual
- accepted primary reader pointer
- accepted/candidate manifests
- accepted MAN* catalog
- accepted MAN CLI docs
- MANSTAR native reference lane
- runlogs and smoke transcripts
- work-order and review-packet history

## Current Observed State

- `manualgen version`: `0.4.3-mdo234`
- compatible repo-local vcpkg Python observed: `3.12.9`
- active reader file exists
- active reader observed lines: `3733`
- active reader observed H1 headings: `25` including the title
- inventory: `sections=25 media=18 appendices=12 manifests=4`
- validate with vcpkg Python 3.12.9: `validation_fail_rows=0`, `boundary_fail_rows=0`
- build dry run with vcpkg Python 3.12.9: `validation_fail_rows=0`, `dry_run_hash_matches_current_combined=0`
- MAN* catalog status: `DRIFT`, `drift_failures=8`

## Sublanes

1. HELP / metadata harvest
2. Command reference assembly
3. Skeleton / TOC / section factory
4. Pippet section workflow
5. Publication / reader lane
6. Runtime proof lane
7. MAN* catalog lane
8. MANSTAR reference lane
9. Tooling / Python engine lane

## Product Hardening Gate

Repair or classify:

- MAN* duplicate extra-table drift
- dry-run hash mismatch
- active reader pointer metadata line-count/hash mismatch
