<!-- CANDIDATE ONLY: report-only command-reference page; no publication authority. -->
# SCX

- Catalog/topic: `DOT` / `SCX`
- Status: `supported`
- Implemented/supported: `T` / `T`
- Primary/confidence: `DOTREF` / `CATALOG`

## Summary

Student/local SCX index-file lab command for creating, tagging, building, listing, and inspecting SCX index files.

## Status

- implemented=yes; supported=yes

## Syntax

- SCX [USAGE|CREATE &lt;file&gt;|ADDTAG &lt;file&gt; &lt;name&gt; FIELD &lt;n&gt; [DESC]|BUILD &lt;file&gt;|TAGS &lt;file&gt;|INFO &lt;file&gt;]

## Usage

- SCX USAGE
- SCX CREATE &lt;file&gt;
- SCX ADDTAG &lt;file&gt; &lt;name&gt; FIELD &lt;n&gt;
- SCX ADDTAG &lt;file&gt; &lt;name&gt; FIELD &lt;n&gt; DESC
- SCX BUILD &lt;file&gt;
- SCX TAGS &lt;file&gt;
- SCX INFO &lt;file&gt;

## Note

- SCX with no arguments prints usage.
- CREATE writes a new SCX container/file.
- ADDTAG mutates SCX tag metadata.
- BUILD builds SCX contents from the current area.
- TAGS and INFO inspect SCX metadata.
- SCX is separate from the ordinary command-surface CNX/CDX/LMDB abstractions.

## Related

- IDX
- INDEX
- REINDEX

## Provenance

- Topic key: `DOT|SCX`
- Included HELP rows: `19`
- HELP reference run: `MANRUN-20260914T034553Z-26B1376D`
- Disposition run: `MANRUN-20260914T034657Z-783CD9C3`
- Authority: `candidate_only`; `publication_authority_claimed=0`
