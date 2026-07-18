<!-- CANDIDATE ONLY: report-only command-reference page; no publication authority. -->
# LIST

- Catalog/topic: `DOT` / `LIST`
- Status: `supported`
- Implemented/supported: `T` / `T`
- Primary/confidence: `DOTREF` / `CATALOG`

## Summary

List records from the current table using DotTalk++ command semantics.

- List records from the current work area
- Display rows from the current work area using classic LIST-style output, honoring active order/index state and optional filtering modes.

## Status

- implemented=yes; supported=yes

## Syntax

- LIST
- LIST ALL
- LIST DELETED
- LIST FIELDS &lt;fieldlist&gt;
- LIST FOR &lt;expr&gt;
- LIST WHILE &lt;expr&gt;
- LIST NEXT &lt;n&gt;
- LIST REST
- LIST [ALL] [FIELDS &lt;list&gt;] [FOR &lt;expr&gt;]

## Usage

- LIST
- LIST USAGE
- LIST TOP
- LIST BOTTOM
- LIST ALL
- LIST &lt;limit&gt;
- LIST DELETED
- LIST FOR &lt;predicate&gt;
- LIST TOP &lt;limit&gt;
- LIST BOTTOM &lt;limit&gt;

## Example

- LIST
- LIST FIELDS LNAME,FNAME
- LIST FOR GPA &gt;= 3.5
- LIST NEXT 10

## Note

- Developer inspection command; SMARTLIST is the preferred order-aware listing path
- Should preserve the current cursor unless a handler explicitly documents movement
- Filtering is expression/predicate-aware where wired
- LIST requires an open table except for LIST USAGE.
- LIST with no arguments displays from the current cursor position.
- LIST ALL starts at the top and removes the default output limit.
- TOP and BOTTOM move to an endpoint before listing.
- DELETED selects deleted records using physical traversal.
- FOR applies an expression predicate after normalization.
- Active order/index state is honored when possible; LIST falls back to physical order with a note.
- LIST is read-only for table data and restores cursor position best-effort.

## Provenance

- Topic key: `DOT|LIST`
- Included HELP rows: `38`
- HELP reference run: `MANRUN-20260717T222026Z-28C704E0`
- Disposition run: `MANRUN-20260717T230554Z-DB3F2DC8`
- Authority: `candidate_only`; `publication_authority_claimed=0`
