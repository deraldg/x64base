# DD096Z-D2R Candidate CDX/Tag Prerequisite Diagnostic v0

Created UTC: `2026-05-29T14:57:59+00:00`

## Purpose

DD096Z-D2R diagnoses the DD096Z-D2 candidate-only `BUILDLMDB` failures.

It does not retry LMDB blindly. It proves whether candidate CDX/tags exist and stages one-table tag syntax probes before any rebuild retry.

## Boundary

Diagnostic/planning only. No active catalog replacement. No active DBF writes. No active CDX/LMDB rebuild. No source edits. No build edits. No workspace mutation. No HELP/CMDHELPCHK mutation. No manual mutation.
