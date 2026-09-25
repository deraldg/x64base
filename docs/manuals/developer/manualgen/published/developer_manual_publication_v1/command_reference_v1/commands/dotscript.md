<!-- CANDIDATE ONLY: report-only command-reference page; no publication authority. -->
# DOTSCRIPT

- Catalog/topic: `DOT` / `DOTSCRIPT`
- Status: `supported`
- Implemented/supported: `T` / `T`
- Primary/confidence: `DOTREF` / `CATALOG`

## Summary

Run a DotTalk++ script file, resolving bare names through SCRIPTS, supporting @file notation, TRACE mode, and one-level subscript nesting.

## Status

- implemented=yes; supported=yes

## Syntax

- DOTSCRIPT &lt;file.dts&gt;
- DOTSCRIPT USAGE
- DOTSCRIPT &lt;file&gt;
- DOTSCRIPT @&lt;file&gt;
- DOTSCRIPT TRACE
- DOTSCRIPT TRACE ON|OFF
- DOTSCRIPT TRACE &lt;file&gt;
- DOTSCRIPT TRACE @&lt;file&gt;
- DOTSCRIPT TRACE ON|OFF &lt;file&gt;
- DOTSCRIPT TRACE ON|OFF @&lt;file&gt;

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
- behavior: OUT/OUTPUT captures full command output emitted through std::cout while preserving console visibility.
- behavior: APPEND appends to an existing transcript; default OUT/OUTPUT truncates/rewrites the transcript.
- behavior: transcript capture does not make script commands safe; side effects still depend on script contents.
- boundary: transcript capture itself does not mutate DBF/CDX/LMDB, MAN*/MANSTAR, reader pointers, HELP, or CMDHELPCHK.

## Note

- DOTSCRIPT with no arguments shows usage.
- DOTSCRIPT reads an external script file and executes each nonblank, noncomment line through the shell command executor.
- Script comments/blank lines are ignored when they begin with *, //, &amp;&amp;, or ; after trimming.
- Bare names use SCRIPTS only; a missing extension means .dts.
- Qualified relative paths use DATA; subscripts use their caller's directory.
- Absolute paths are exact. Missing files never trigger a directory search.
- @file notation is accepted and unquoted before path resolution.
- TRACE without a file reports the current trace state and usage.
- TRACE ON/OFF changes global DOTSCRIPT trace state.
- TRACE &lt;file&gt; runs a single script with trace enabled without changing global trace state.
- Nesting is limited to main script plus one subscript.
- DOTSCRIPT itself delegates side effects to the commands inside the script; it is not read-only.
- TEST is intentionally not refactored in this patch; TEST may become a later consumer of shell_transcript.
- provenance: MDO-377G v1.1 shell transcript service source patch with usage-contract update.

## Related

- TEST
- CMDHELP
- WORKSPACE
- CREATE
- USE

## Provenance

- Topic key: `DOT|DOTSCRIPT`
- Included HELP rows: `57`
- HELP reference run: `MANRUN-20260924T230323Z-76AD9EBC`
- Disposition run: `MANRUN-20260925T002350Z-BF0876DF`
- Authority: `candidate_only`; `publication_authority_claimed=0`
