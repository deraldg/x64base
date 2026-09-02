<!-- CANDIDATE ONLY: report-only command-reference page; no publication authority. -->
# DOTSCRIPT

- Catalog/topic: `DOT` / `DOTSCRIPT`
- Status: `supported`
- Implemented/supported: `T` / `T`
- Primary/confidence: `DOTREF` / `CATALOG`

## Summary

Run a DotTalk++ script file, resolving bare names through script/test search locations, supporting @file notation, TRACE mode, and one-level subscript nesting.

## Status

- implemented=yes; supported=yes

## Syntax

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
- DOTSCRIPT &lt;file.dts&gt;
- DOTSCRIPT TRACE ON|OFF
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
- Bare script names try the typed name, .dts extension, scripts/, and tests/ candidates.
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
- Included HELP rows: `65`
- HELP reference run: `MANRUN-20260902T151703Z-1CA7DB89`
- Disposition run: `MANRUN-20260902T151704Z-6F39AFBC`
- Authority: `candidate_only`; `publication_authority_claimed=0`
