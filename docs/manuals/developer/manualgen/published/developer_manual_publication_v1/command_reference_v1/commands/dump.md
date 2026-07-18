<!-- CANDIDATE ONLY: report-only command-reference page; no publication authority. -->
# DUMP

- Catalog/topic: `DOT` / `DUMP`
- Status: `supported`
- Implemented/supported: `T` / `T`
- Primary/confidence: `DOTREF` / `CATALOG`

## Summary

Debug: print a structured dump of an internal value/state.

- Dump every record from the current work area in legacy pipe-delimited form.

## Status

- implemented=yes; supported=yes

## Syntax

- DUMP

## Usage

- DUMP
- DUMP USAGE

## Note

- DUMP requires an open table except for DUMP USAGE.
- DUMP operates only on the current work area.
- DUMP does not resolve paths and does not open files.
- Deleted records are prefixed with an asterisk marker.
- DUMP iterates by record number and reads each record.
- DUMP is read-only for table data but moves the current cursor during output.

## Provenance

- Topic key: `DOT|DUMP`
- Included HELP rows: `12`
- HELP reference run: `MANRUN-20260717T222026Z-28C704E0`
- Disposition run: `MANRUN-20260717T230554Z-DB3F2DC8`
- Authority: `candidate_only`; `publication_authority_claimed=0`
