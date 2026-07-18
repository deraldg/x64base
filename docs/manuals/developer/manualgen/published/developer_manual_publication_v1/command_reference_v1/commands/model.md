<!-- CANDIDATE ONLY: report-only command-reference page; no publication authority. -->
# MODEL

- Catalog/topic: `ED` / `MODEL`
- Status: `supported`
- Implemented/supported: `F` / `T`
- Primary/confidence: `EDREF` / `CATALOG`

## Summary

How to think about DotTalk++<br><br>DotTalk++ is best understood as four layers working together:<br><br>1. Command Layer<br>    The CLI accepts commands such as:<br>        USE<br>        SELECT<br>        LIST<br>        SET

- How to think about DotTalk++
- DotTalk++ is best understood as four layers working together:
- 1. Command Layer
- The CLI accepts commands such as:
- USE
- SELECT
- LIST
- SET ORDER
- SET RELATION
- REL ENUM
- 2. Data Layer
- The engine works with:
- tables
- records
- fields
- indexes
- relations
- 3. Logic Layer
- DotScript and command execution provide:
- sequential flow
- decision flow
- looping flow
- expression evaluation
- 4. View / Projection Layer
- Results are shown through:
- DISPLAY
- TUPLE
- SMARTLIST
- browser commands
- A practical mental model
- Table       = stored rows
- Record      = one row
- Field       = one column value in a row
- Index       = alternate ordered path through rows
- Relation    = parent-child path between tables
- Tuple       = projected logical row, possibly across multiple tables

## Status

- implemented=no; supported=yes

## Syntax

- SYSTEM MODEL

## Provenance

- Topic key: `ED|MODEL`
- Included HELP rows: `38`
- HELP reference run: `MANRUN-20260717T222026Z-28C704E0`
- Disposition run: `MANRUN-20260717T230554Z-DB3F2DC8`
- Authority: `candidate_only`; `publication_authority_claimed=0`
