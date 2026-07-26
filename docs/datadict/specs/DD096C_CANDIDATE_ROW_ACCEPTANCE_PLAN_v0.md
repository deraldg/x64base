# DD096C Candidate Row Acceptance / Remap Plan v0

Created UTC: `2026-05-28T22:53:02+00:00`

## Purpose

DD096C creates a candidate-only acceptance/remap plan from DD096A candidates and DD096B read-only deduplication.

## Boundary

DD096C is candidate-acceptance-planning/report-only. It does not edit C++ source, edit build files, edit command registration, mutate active catalog DBFs, append/replace/delete/pack/zap DBFs, create/rebuild CDX/LMDB, mutate HELP/META/CMDHELPCHK, regenerate catalog content, or repair manual rows.
