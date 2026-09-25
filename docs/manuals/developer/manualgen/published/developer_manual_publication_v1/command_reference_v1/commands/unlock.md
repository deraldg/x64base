<!-- CANDIDATE ONLY: report-only command-reference page; no publication authority. -->
# UNLOCK

- Catalog/topic: `DOT` / `UNLOCK`
- Status: `supported`
- Implemented/supported: `T` / `T`
- Primary/confidence: `DOTREF` / `CATALOG`

## Summary

Release the current record lock, a specified record lock, or the table lock.

## Status

- implemented=yes; supported=yes

## Syntax

- UNLOCK [ALL]

## Usage

- UNLOCK USAGE
- UNLOCK
- UNLOCK &lt;recno&gt;
- UNLOCK ALL
- UNLOCK TABLE

## Example

- UNLOCK
- UNLOCK 10
- UNLOCK ALL
- UNLOCK TABLE

## Note

- UNLOCK USAGE returns before open-table checks.
- UNLOCK with no arguments unlocks the current record.
- UNLOCK ALL and UNLOCK TABLE release the table lock.

## Related

- LOCK
- RLOCK
- FLOCK

## Provenance

- Topic key: `DOT|UNLOCK`
- Included HELP rows: `19`
- HELP reference run: `MANRUN-20260924T230323Z-76AD9EBC`
- Disposition run: `MANRUN-20260925T002350Z-BF0876DF`
- Authority: `candidate_only`; `publication_authority_claimed=0`
