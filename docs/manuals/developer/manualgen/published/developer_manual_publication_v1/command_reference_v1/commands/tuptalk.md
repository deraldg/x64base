<!-- CANDIDATE ONLY: report-only command-reference page; no publication authority. -->
# TUPTALK

- Catalog/topic: `DOT` / `TUPTALK`
- Status: `supported`
- Implemented/supported: `T` / `T`
- Primary/confidence: `DOTREF` / `CATALOG`

## Summary

DotTalk++ tuple/logical-row command.

- Tuple-based normalization test harness and live DBF capture tool for building, normalizing, dumping, exporting, and pushing tuple entries.

## Status

- implemented=yes; supported=yes

## Syntax

- TUPTALK

## Usage

- TUPTALK
- TUPTALK USAGE
- TUPTALK RESET
- TUPTALK ADD &lt;type&gt; &lt;len&gt; &lt;raw&gt;
- TUPTALK ADD &lt;type&gt; &lt;len&gt; &lt;dec&gt; &lt;raw&gt;
- TUPTALK LIST
- TUPTALK NORMALIZE
- TUPTALK DUMP
- TUPTALK EXPORT CSV
- TUPTALK EXPORT TSV
- TUPTALK EXPORT CSV &lt;path&gt;
- TUPTALK EXPORT TSV &lt;path&gt;
- TUPTALK PUSH &lt;field&gt;
- TUPTALK PUSH ALL
- TUPTALK PUSH ALL FILTER &lt;mask&gt;
- TUPTALK PUSH FILTER &lt;mask&gt;
- TUPTALK PUSH ROW

## Example

- TUPTALK PUSH LASTNAME
- TUPTALK PUSH 3
- TUPTALK PUSH ALL
- TUPTALK PUSH ALL FILTER CND
- TUPTALK PUSH ROW

## Note

- TUPTALK with no arguments shows usage/help and buffer status.
- TT is wired as a shell alias for TUPTALK.
- ADD creates a test entry from raw text and schema type metadata.
- NORMALIZE fills normalized values using value_normalize.
- PUSH captures fields or rows from the current DBF record.
- EXPORT writes CSV or TSV when a path is supplied or uses default behavior.
- TUPTALK mutates its process-local scratch buffer and may write export files.

## Provenance

- Topic key: `DOT|TUPTALK`
- Included HELP rows: `33`
- HELP reference run: `MANRUN-20260717T222026Z-28C704E0`
- Disposition run: `MANRUN-20260717T230554Z-DB3F2DC8`
- Authority: `candidate_only`; `publication_authority_claimed=0`
