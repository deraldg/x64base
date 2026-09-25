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
- A BUFFERED INSERT IS ASSIGNED ITS RECORD NUMBER HERE, NOT WHEN IT WAS
- STAGED (owner ruling 2026-09-19, OI-043). The number a staged insert carries is a BUFFER KEY: it orders the changes and joins a statement to its own uncommitted rows. COMMIT always APPENDS an insert and the record number it lands on is minted at that moment, so a recno read back inside the transaction may differ from the one the row ends up with. Nothing may treat a pre-commit recno as an address.
- THE OLD BEHAVIOUR WAS NOT A WEAKER PROMISE BUT A WRONG ONE. An insert whose staged number was still in range was written OVER whatever record already held it, so a table that grew between the INSERT and the COMMIT lost a live row with no message. A DBF record's identity is its physical position, so a reservation held across a window is a promise about a gap, and a gap cannot exist in the file.
- UPDATE and DELETE are unaffected: they name records that already exist.
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
- Included HELP rows: `75`
- HELP reference run: `MANRUN-20260924T230323Z-76AD9EBC`
- Disposition run: `MANRUN-20260925T002350Z-BF0876DF`
- Authority: `candidate_only`; `publication_authority_claimed=0`
