<!-- CANDIDATE ONLY: report-only command-reference page; no publication authority. -->
# ENDLOOP

- Catalog/topic: `DOT` / `ENDLOOP`
- Status: `supported`
- Implemented/supported: `T` / `T`
- Primary/confidence: `DOTREF` / `CATALOG`

## Summary

End a LOOP block (scripting).

- End the active LOOP block and replay buffered commands through the shell executor.

## Status

- implemented=yes; supported=yes

## Syntax

- ENDLOOP

## Usage

- ENDLOOP
- ENDLOOP USAGE

## Note

- ENDLOOP with no arguments executes the active LOOP buffer.
- ENDLOOP requires an active LOOP block except for ENDLOOP USAGE.
- ENDLOOP clears active loop state before replay.
- ENDLOOP replays buffered commands through the registered loop executor.
- ENDLOOP reports when no LOOP is active.
- ENDLOOP may indirectly mutate data, session state, or files depending on buffered commands.

## Provenance

- Topic key: `DOT|ENDLOOP`
- Included HELP rows: `12`
- HELP reference run: `MANRUN-20260717T222026Z-28C704E0`
- Disposition run: `MANRUN-20260717T230554Z-DB3F2DC8`
- Authority: `candidate_only`; `publication_authority_claimed=0`
