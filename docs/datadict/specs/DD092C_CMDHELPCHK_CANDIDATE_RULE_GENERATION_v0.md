# DD092C CMDHELPCHK Candidate Rule Generation v0

Created UTC: `2026-05-28T22:00:27+00:00`

## Purpose

DD092C generates review-only candidate CMDHELPCHK rules and HELP candidate rows for DDICT after DD092B readiness.

## Boundary

DD092C is candidate-generation/report-only. It does not edit C++ source, edit build files, edit command registration, mutate active catalog DBFs, append/replace/delete/pack/zap DBFs, create/rebuild CDX/LMDB, mutate HELP/META/CMDHELPCHK, regenerate catalog content, or repair manual rows.
