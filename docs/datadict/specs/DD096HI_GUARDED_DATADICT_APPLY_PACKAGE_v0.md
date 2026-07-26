# DD096H/DD096I Guarded Data Dictionary Apply Package v0

Created UTC: `2026-05-29T00:05:52+00:00`

## Purpose

DD096H records explicit authorization and DD096I creates the guarded DotTalk++ apply script and PowerShell runner for the Data Dictionary schema-promotion staged rows.

## Boundary

The package generator does not write active DBFs. Active mutation happens only when the generated runner invokes `datarun` against the generated `.dts` apply script. The runner creates backups first. HELP/CMDHELPCHK remains out of scope.
