<!-- CANDIDATE ONLY: report-only command-reference page; no publication authority. -->
# DIR

- Catalog/topic: `DOT` / `DIR`
- Status: `supported`
- Implemented/supported: `T` / `T`
- Primary/confidence: `DOTREF` / `CATALOG`

## Summary

List directory or file entries through the DotTalk++ shell surface.

- List a directory or show a single file entry through DotTalk++ path resolution.

## Status

- implemented=yes; supported=yes

## Syntax

- DIR [&lt;mask&gt;|&lt;path&gt;]

## Usage

- DIR
- DIR USAGE
- DIR &lt;path&gt;
- DIR &lt;slot&gt;

## Note

- DIR with no arguments lists the configured DBF path.
- DIR &lt;path&gt; lists a directory or prints a single file entry.
- Slot-style paths resolve through the common path resolver.
- DIR is read-only and does not mutate table data or filesystem contents.

## Provenance

- Topic key: `DOT|DIR`
- Included HELP rows: `12`
- HELP reference run: `MANRUN-20260717T222026Z-28C704E0`
- Disposition run: `MANRUN-20260717T230554Z-DB3F2DC8`
- Authority: `candidate_only`; `publication_authority_claimed=0`
