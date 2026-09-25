<!-- CANDIDATE ONLY: report-only command-reference page; no publication authority. -->
# BUFFERING

- Catalog/topic: `ED` / `BUFFERING`
- Status: `supported`
- Implemented/supported: `F` / `T`
- Primary/confidence: `EDREF` / `CATALOG`

## Summary

Buffering means changes are staged before permanent commit.

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
- HELP reference run: `MANRUN-20260924T230323Z-76AD9EBC`
- Disposition run: `MANRUN-20260925T002350Z-BF0876DF`
- Authority: `candidate_only`; `publication_authority_claimed=0`
