<!-- CANDIDATE ONLY: report-only command-reference page; no publication authority. -->
# PSHELL

- Catalog/topic: `DOT` / `PSHELL`
- Status: `supported`
- Implemented/supported: `T` / `T`
- Primary/confidence: `DOTREF` / `CATALOG`

## Summary

PowerShell reference catalog presentation helper used by the PSHELL command.

- Display the PowerShell/PSHELL helper reference and search the curated PowerShell one-liner catalog.

## Status

- implemented=yes; supported=yes

## Syntax

- PSHELL
- PSHELL USAGE
- PSHELL LIST-CATEGORIES
- PSHELL &lt;category&gt;
- PSHELL &lt;term&gt;
- PSHELL [USAGE|&lt;command...&gt;]
- PSHELL                     → this grouped list
- PSHELL PYTHON              → only Python commands
- PSHELL PY-VENV-CREATE      → show details
- PSHELL CLEAN*              → search cleaning commands
- HELP PS LIST-CATEGORIES    → show category names
- HELP PS &lt;term&gt;             → same as PSHELL &lt;term&gt;

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

## Related

- HELP
- SQLHELP
- PS

## Provenance

- Topic key: `DOT|PSHELL`
- Included HELP rows: `37`
- HELP reference run: `MANRUN-20260902T151703Z-1CA7DB89`
- Disposition run: `MANRUN-20260902T151704Z-6F39AFBC`
- Authority: `candidate_only`; `publication_authority_claimed=0`
