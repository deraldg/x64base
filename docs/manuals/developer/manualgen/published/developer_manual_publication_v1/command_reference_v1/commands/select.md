<!-- CANDIDATE ONLY: report-only command-reference page; no publication authority. -->
# SELECT

- Catalog/topic: `DOT` / `SELECT`
- Status: `supported`
- Implemented/supported: `T` / `T`
- Primary/confidence: `DOTREF` / `CATALOG`

## Summary

Select the active DotTalk++ work area by number or logical name.

- Select the current work area by numeric slot or by work-area/table name.

## Status

- implemented=yes; supported=yes

## Syntax

- SELECT &lt;area-or-alias&gt;

## Usage

- SELECT USAGE
- SELECT &lt;n&gt;
- SELECT &lt;name&gt;
- SELECT &lt;table.dbf&gt;

## Note

- SELECT with no arguments prints usage with the current valid slot range.
- SELECT USAGE prints usage and does not change the current area.
- Numeric selection uses the current workarea slot count.
- Name selection matches workarea labels and open DBF base names case-insensitively.
- SELECT mutates current-area/session state but does not mutate table data.

## Provenance

- Topic key: `DOT|SELECT`
- Included HELP rows: `13`
- HELP reference run: `MANRUN-20260717T222026Z-28C704E0`
- Disposition run: `MANRUN-20260717T230554Z-DB3F2DC8`
- Authority: `candidate_only`; `publication_authority_claimed=0`
