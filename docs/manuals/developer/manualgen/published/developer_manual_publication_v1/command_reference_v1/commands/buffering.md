<!-- CANDIDATE ONLY: report-only command-reference page; no publication authority. -->
# BUFFERING

- Catalog/topic: `ED` / `BUFFERING`
- Status: `supported`
- Implemented/supported: `F` / `T`
- Primary/confidence: `EDREF` / `CATALOG`

## Summary

Buffering means changes are staged before permanent commit.<br><br>Commands<br>    TABLE ON<br>    REPLACE ...<br>    COMMIT<br>    ROLLBACK   (planned/deferred in some contexts)<br><br>Observed model<br>    With TABLE ON:

- Buffering means changes are staged before permanent commit.
- Commands
- TABLE ON
- REPLACE ...
- COMMIT
- ROLLBACK   (planned/deferred in some contexts)
- Observed model
- With TABLE ON:
- TUPLE may show buffered values immediately
- LIST may still show persisted/indexed values until COMMIT
- Educational point
- Buffering separates:
- working state
- persisted state
- This is a classic database concept and an important teaching tool.

## Status

- implemented=no; supported=yes

## Syntax

- TABLE BUFFERING

## Provenance

- Topic key: `ED|BUFFERING`
- Included HELP rows: `17`
- HELP reference run: `MANRUN-20260717T222026Z-28C704E0`
- Disposition run: `MANRUN-20260717T230554Z-DB3F2DC8`
- Authority: `candidate_only`; `publication_authority_claimed=0`
