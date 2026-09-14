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

- NONE
- Mined command argument/switch candidate. Promote only after validation against parser behavior or curated command docs.
- NOTE
- NOTHING

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
- COMMIT is write-ahead journaled: it durably records a redo log plus a COMMIT marker before applying buffered changes to the DBF, and aborts the commit if that durable sync fails. Committed journals are replayed on crash recovery at open. THE BACK HALF IS ALSO SYNCED: the table's contents are forced to stable media BEFORE the redo log is deleted, because writeCurrent reaches only the OS page cache and a log removed ahead of the platter would leave a power cut with neither copy. If that sync fails the log is KEPT and the area is marked stale;
- replay is idempotent, so a surviving log costs one repeat and a deleted one costs the transaction.
- BOTH SYNCS ARE GATED ON TABLE BUFFER PERSISTENT. Under the default RamOnly there is no journal at all, so COMMIT is NOT durable by default and never has been -- said plainly here because the paragraph above describes a protocol a reader could otherwise assume is always running.
- Atomicity and durability are partial (ACID beta-1), not a full transaction.
- A registered BEFORE trigger is asked, at commit entry, whether each buffered record may be written, and may refuse. A refusal aborts the WHOLE area transaction -- one COMMIT marker covers the area, so one record cannot be refused while the rest commit durably. Nothing is journaled, the buffer is retained for correction and retry, and the refusal is reported at ERROR severity so STOP_ON_ERROR governs it.
- No BEFORE trigger registered means no cost and no behaviour change.

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
- Included HELP rows: `61`
- HELP reference run: `MANRUN-20260914T034553Z-26B1376D`
- Disposition run: `MANRUN-20260914T034657Z-783CD9C3`
- Authority: `candidate_only`; `publication_authority_claimed=0`
