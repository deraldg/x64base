<!-- CANDIDATE ONLY: report-only command-reference page; no publication authority. -->
# DOTSCRIPT

- Catalog/topic: `DOT` / `DOTSCRIPT`
- Status: `supported`
- Implemented/supported: `T` / `T`
- Primary/confidence: `DOTREF` / `CATALOG`

## Summary

Run a DotTalk script file (test harness / automation).<br><br>        Example:<br>            DOTSCRIPT run_all_sql_tests.dts

- Run a DotTalk++ script file, resolving bare names through script/test search locations, supporting @file notation, TRACE mode, and one-level subscript nesting.
- Run a DotTalk script file (test harness / automation).
- Example:
- DOTSCRIPT run_all_sql_tests.dts

## Status

- implemented=yes; supported=yes

## Syntax

- DOTSCRIPT &lt;file.dts&gt;

## Usage

- DOTSCRIPT USAGE
- DOTSCRIPT &lt;file&gt;
- DOTSCRIPT @&lt;file&gt;
- DOTSCRIPT TRACE
- DOTSCRIPT TRACE ON
- DOTSCRIPT TRACE OFF
- DOTSCRIPT TRACE &lt;file&gt;
- DOTSCRIPT TRACE @&lt;file&gt;
- DOTSCRIPT TRACE ON &lt;file&gt;
- DOTSCRIPT TRACE OFF &lt;file&gt;
- DOTSCRIPT TRACE ON @&lt;file&gt;
- DOTSCRIPT TRACE OFF @&lt;file&gt;
- DOTSCRIPT &lt;file&gt; OUT &lt;transcript-file&gt;
- DOTSCRIPT &lt;file&gt; OUTPUT &lt;transcript-file&gt;
- DOTSCRIPT TRACE &lt;file&gt; OUT &lt;transcript-file&gt;
- DOTSCRIPT &lt;file&gt; OUT &lt;transcript-file&gt; APPEND

## Note

- DOTSCRIPT with no arguments shows usage.
- DOTSCRIPT reads an external script file and executes each nonblank,
- noncomment line through the shell command executor.
- Script comments/blank lines are ignored when they begin with *, //, &amp;&amp;, or ; after trimming.
- Bare script names try the typed name, .dts extension, scripts/, and tests/ candidates.
- @file notation is accepted and unquoted before path resolution.
- TRACE without a file reports the current trace state and usage.
- TRACE ON/OFF changes global DOTSCRIPT trace state.
- TRACE &lt;file&gt; runs a single script with trace enabled without changing global trace state.
- Nesting is limited to main script plus one subscript.
- DOTSCRIPT itself delegates side effects to the commands inside the script; it is not read-only.
- TEST is intentionally not refactored in this patch; TEST may become a later consumer of shell_transcript.

## Provenance

- Topic key: `DOT|DOTSCRIPT`
- Included HELP rows: `34`
- HELP reference run: `MANRUN-20260717T222026Z-28C704E0`
- Disposition run: `MANRUN-20260717T230554Z-DB3F2DC8`
- Authority: `candidate_only`; `publication_authority_claimed=0`
