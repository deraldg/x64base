<!-- CANDIDATE ONLY: report-only command-reference page; no publication authority. -->
# DIR

- Catalog/topic: `DOT` / `DIR`
- Status: `supported`
- Implemented/supported: `T` / `T`
- Primary/confidence: `DOTREF` / `CATALOG`

## Summary

List a directory or show a single file entry through DotTalk++ path resolution.

## Status

- implemented=yes; supported=yes

## Syntax

- DIR
- DIR USAGE
- DIR &lt;path&gt;
- DIR &lt;slot&gt;
- DIR &lt;slot&gt;:&lt;path&gt;
- DIR &lt;pattern&gt;
- DIR &lt;dir&gt;/&lt;pattern&gt;
- DIR [&lt;mask&gt;|&lt;path&gt;]
- DIR &lt;pattern&gt;          e.g. DIR *.dbf   (wildcards * and ?)
- DIR &lt;dir&gt;/&lt;pattern&gt;    e.g. DIR DBF/STUD*.*

## Usage

- DIR
- DIR USAGE
- DIR &lt;path&gt;
- DIR &lt;slot&gt;
- DIR &lt;slot&gt;:&lt;path&gt;
- DIR &lt;pattern&gt;
- DIR &lt;dir&gt;/&lt;pattern&gt;

## Note

- DIR with no arguments lists the configured DBF path.
- DIR &lt;path&gt; lists a directory or prints a single file entry.
- Slot-style paths resolve through the common path resolver.
- A trailing wildcard component (containing * or ?) filters the listing by filename, case-insensitively: DIR *.dbf, DIR DBF/STUD*.*, DIR INDEXES/*.cnx.
- DIR is read-only and does not mutate table data or filesystem contents.

## Related

- SETPATH
- SHOWINI

## Provenance

- Topic key: `DOT|DIR`
- Included HELP rows: `28`
- HELP reference run: `MANRUN-20260902T151703Z-1CA7DB89`
- Disposition run: `MANRUN-20260902T151704Z-6F39AFBC`
- Authority: `candidate_only`; `publication_authority_claimed=0`
