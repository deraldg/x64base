<!-- CANDIDATE ONLY: report-only command-reference page; no publication authority. -->
# PSHELL

- Catalog/topic: `DOT` / `PSHELL`
- Status: `supported`
- Implemented/supported: `T` / `T`
- Primary/confidence: `DOTREF` / `CATALOG`

## Summary

Invoke or document the PowerShell/platform-shell helper surface where enabled by the runtime policy.

- PowerShell reference catalog presentation helper used by the PSHELL command.
- Display the PowerShell/PSHELL helper reference and search the curated PowerShell one-liner catalog.

## Status

- implemented=yes; supported=yes

## Syntax

- PSHELL [USAGE|&lt;command...&gt;]

## Usage

- User-visible PSHELL usage is owned by cmd_pshell_help.cpp.
- This file provides show_pshell_help(...) and catalog formatting support.
- PSHELL
- PSHELL USAGE
- PSHELL LIST-CATEGORIES
- PSHELL &lt;category&gt;
- PSHELL &lt;term&gt;

## Example

- PSHELL
- PSHELL PYTHON
- PSHELL PY-VENV-CREATE
- PSHELL CLEAN

## Note

- PSHELL is read-only reference output; it does not execute PowerShell.
- Keep command dispatch/usage gating in cmd_pshell_help.cpp.
- PSHELL with no arguments displays the grouped PSHELL reference.
- PSHELL USAGE prints command usage without searching the catalog.
- PSHELL is read-only and does not execute PowerShell commands.

## Provenance

- Topic key: `DOT|PSHELL`
- Included HELP rows: `21`
- HELP reference run: `MANRUN-20260717T222026Z-28C704E0`
- Disposition run: `MANRUN-20260717T230554Z-DB3F2DC8`
- Authority: `candidate_only`; `publication_authority_claimed=0`
