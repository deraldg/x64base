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

- PSHELL [USAGE|&lt;command...&gt;]
- PSHELL                     -&gt; this grouped list
- PSHELL PYTHON              -&gt; only Python commands
- PSHELL PY-VENV-CREATE      -&gt; show details
- PSHELL CLEAN*              -&gt; search cleaning commands
- HELP PS LIST-CATEGORIES    -&gt; show category names
- HELP PS &lt;term&gt;             -&gt; same as PSHELL &lt;term&gt;

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
- Included HELP rows: `32`
- HELP reference run: `MANRUN-20260924T230323Z-76AD9EBC`
- Disposition run: `MANRUN-20260925T002350Z-BF0876DF`
- Authority: `candidate_only`; `publication_authority_claimed=0`
