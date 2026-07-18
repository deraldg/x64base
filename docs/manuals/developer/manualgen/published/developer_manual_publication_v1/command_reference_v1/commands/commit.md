<!-- CANDIDATE ONLY: report-only command-reference page; no publication authority. -->
# COMMIT

- Catalog/topic: `DOT` / `COMMIT`
- Status: `supported`
- Implemented/supported: `T` / `T`
- Primary/confidence: `DOTREF` / `CATALOG`

## Summary

Commit buffered TABLE updates to disk.<br><br>        Notes (current shakedown observations):<br>            - Clears TABLE stale state on success.<br>            - May currently trigger full INX rebuild work as

- Apply staged table-buffered changes
- Apply buffered TABLE changes to the current area or all open buffered areas, locking records at commit time and reporting persistence-stage failures.
- Commit buffered TABLE updates to disk.
- Notes (current shakedown observations):
- - Clears TABLE stale state on success.
- - May currently trigger full INX rebuild work as part of the commit path (performance issue).

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
- COMMIT is a best-effort buffer apply operation, not an atomic transaction.
- risk:
- writes_dbf_records: yes when buffered changes exist
- writes_memo: when buffered memo changes exist
- record_locking: yes at commit time
- clears_table_buffer_changes: on successful commit
- partial_commit_possible: yes
- cdx_lmdb_rebuild: no

## Warning

- COMMIT is a mutation boundary; keep help wording conservative until runtime behavior is verified

## Related

- TABLE
- REPLACE
- CALCWRITE
- ROLLBACK

## Provenance

- Topic key: `DOT|COMMIT`
- Included HELP rows: `49`
- HELP reference run: `MANRUN-20260717T222026Z-28C704E0`
- Disposition run: `MANRUN-20260717T230554Z-DB3F2DC8`
- Authority: `candidate_only`; `publication_authority_claimed=0`
