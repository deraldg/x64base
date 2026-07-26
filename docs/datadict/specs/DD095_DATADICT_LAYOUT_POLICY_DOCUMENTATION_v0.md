# DD095 Data Dictionary Layout Policy Documentation v0

Created UTC: `2026-05-28T22:09:42+00:00`

## Purpose

DD095 documents the accepted Data Dictionary layout and anti-collision rule after DD093C and DD094.

## Boundary

DD095 is layout-policy-documentation/report-only unless `--write-policy` is explicitly supplied. Even with `--write-policy`, it writes only the policy document and does not edit C++ source, build files, command registration, active catalog DBFs, CDX/LMDB artifacts, HELP/META/CMDHELPCHK, generated catalog content, or manual rows.
