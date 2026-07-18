<!-- CANDIDATE ONLY: report-only command-reference page; no publication authority. -->
# IDX

- Catalog/topic: `DOT` / `IDX`
- Status: `supported`
- Implemented/supported: `T` / `T`
- Primary/confidence: `DOTREF` / `CATALOG`

## Summary

Memory-only educational index lab for teaching sort and index concepts without writing persistent index files.

- Memory-only educational index lab for teaching sorting and index concepts without writing persistent INX/CNX/CDX files.

## Status

- implemented=yes; supported=yes

## Syntax

- IDX [USAGE|LIST|DROP &lt;tag&gt;|DROP ALL|ON &lt;field|#n&gt; TAG &lt;name&gt; [SORT &lt;algo&gt;|&lt;algo&gt;] [ASC|DESC]]

## Usage

- IDX
- IDX USAGE
- IDX ON &lt;field|#n&gt; TAG &lt;name&gt;
- IDX ON &lt;field|#n&gt; TAG &lt;name&gt; SORT &lt;algo&gt;
- IDX ON &lt;field|#n&gt; TAG &lt;name&gt; &lt;algo&gt;
- IDX ON &lt;field|#n&gt; TAG &lt;name&gt; ASC
- IDX ON &lt;field|#n&gt; TAG &lt;name&gt; DESC
- IDX LIST
- IDX DROP &lt;tag&gt;
- IDX DROP ALL

## Example

- IDX ON LNAME TAG lname_std
- IDX ON LNAME TAG lname_bubble BUBBLE
- IDX ON LNAME TAG lname_bubble2 SORT BUBBLE DESC

## Note

- IDX with no arguments prints help/usage.
- IDX is memory-only and does not write .inx files.
- IDX does not participate in SET ORDER, REINDEX, WORKSPACE restore, IndexManager, or IIndexBackend.
- Use INDEX for persistent index files.
- SORT algorithms currently include STD and BUBBLE.

## Provenance

- Topic key: `DOT|IDX`
- Included HELP rows: `22`
- HELP reference run: `MANRUN-20260717T222026Z-28C704E0`
- Disposition run: `MANRUN-20260717T230554Z-DB3F2DC8`
- Authority: `candidate_only`; `publication_authority_claimed=0`
