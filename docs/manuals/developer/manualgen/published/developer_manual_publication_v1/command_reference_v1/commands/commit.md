<!-- CANDIDATE ONLY: report-only command-reference page; no publication authority. -->
# COMMIT

- Catalog/topic: `DOT` / `COMMIT`
- Status: `supported`
- Implemented/supported: `T` / `T`
- Primary/confidence: `DOTREF` / `CATALOG`

## Summary

Apply buffered TABLE changes to the current area or all open buffered areas, locking records at commit time and reporting persistence-stage failures.

## Status

- implemented=yes; supported=yes

## Syntax

- COMMIT
- COMMIT ALL
- COMMIT USAGE
- COMMIT MANUAL
- COMMIT INTERACTIVE
- COMMIT AUTO
- COMMIT ALL MANUAL
- COMMIT ALL INTERACTIVE
- COMMIT ALL AUTO

## Usage

- COMMIT USAGE
- COMMIT
- COMMIT ALL
- COMMIT MANUAL
- COMMIT INTERACTIVE
- COMMIT AUTO
- COMMIT ALL MANUAL
- COMMIT ALL INTERACTIVE
- COMMIT ALL AUTO

## Argument

- NOTE
- Mined command argument/switch candidate. Promote only after validation against parser behavior or curated command docs.

## Example

- COMMIT
- COMMIT ALL

## Note

- Applies buffered table changes and clears stale state on success
- Index maintenance should flow through the index subsystem rather than direct backend parsing
- COMMIT with no arguments applies buffered changes for the current area.
- COMMIT ALL applies buffered changes for all open buffered areas.
- TABLE ON buffers changes; COMMIT applies them with record locking.
- MANUAL, INTERACTIVE, and AUTO are accepted for compatibility.
- COMMIT does not rebuild CDX or LMDB containers.
- Legacy INX/IDX and CNX rebuild behavior remains only for legacy index families.
- COMMIT is a data mutation command when buffers contain changes.
- COMMIT is write-ahead journaled: it durably records a redo log plus a COMMIT marker before applying buffered changes to the DBF, and aborts the commit if that durable sync fails. Committed journals are replayed on crash recovery at open. Atomicity and durability are partial (ACID beta-1), not a full transaction.

## Warning

- COMMIT is a mutation boundary; keep help wording conservative until runtime behavior is verified

## Related

- TABLE
- REPLACE
- CALCWRITE
- ROLLBACK
- REINDEX
- REBUILD

## Provenance

- Topic key: `DOT|COMMIT`
- Included HELP rows: `49`
- HELP reference run: `MANRUN-20260902T151703Z-1CA7DB89`
- Disposition run: `MANRUN-20260902T151704Z-6F39AFBC`
- Authority: `candidate_only`; `publication_authority_claimed=0`
