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

## Provenance

- Topic key: `DOT|SCX`
- Included HELP rows: `16`
- HELP reference run: `MANRUN-20260717T222026Z-28C704E0`
- Disposition run: `MANRUN-20260717T230554Z-DB3F2DC8`
- Authority: `candidate_only`; `publication_authority_claimed=0`
