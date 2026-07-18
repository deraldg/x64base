<!-- CANDIDATE ONLY: report-only command-reference page; no publication authority. -->
# LOOP

- Catalog/topic: `DOT` / `LOOP`
- Status: `supported`
- Implemented/supported: `T` / `T`
- Primary/confidence: `DOTREF` / `CATALOG`

## Summary

Begin a LOOP block (scripting).

- Start buffering commands for later replay by ENDLOOP, with optional quiet mode and numeric repetition labels.

## Status

- implemented=yes; supported=yes

## Syntax

- LOOP FOR &lt;n&gt; TIMES

## Usage

- LOOP
- LOOP USAGE
- LOOP QUIET
- LOOP &lt;n&gt;
- LOOP &lt;n&gt; TIMES
- LOOP FOR &lt;n&gt;
- LOOP FOR &lt;n&gt; TIMES
- LOOP FOR &lt;label&gt;
- LOOP OVERRIDE &lt;label&gt;

## Note

- LOOP with no arguments starts command buffering and replays once at ENDLOOP.
- LOOP &lt;n&gt;, LOOP &lt;n&gt; TIMES, and LOOP FOR &lt;n&gt; replay buffered commands n times.
- LOOP QUIET suppresses buffering and ENDLOOP status messages.
- LOOP FOR &lt;label&gt; stores a nonnumeric label and currently replays once.
- ENDLOOP executes buffered commands through the pluggable shell executor.
- The loop implementation skips buffered ENDLOOP lines during replay.
- Iteration count is clamped to the hard maximum when necessary.
- LOOP mutates script execution state and may indirectly mutate anything its buffered commands mutate.

## Provenance

- Topic key: `DOT|LOOP`
- Included HELP rows: `21`
- HELP reference run: `MANRUN-20260717T222026Z-28C704E0`
- Disposition run: `MANRUN-20260717T230554Z-DB3F2DC8`
- Authority: `candidate_only`; `publication_authority_claimed=0`
