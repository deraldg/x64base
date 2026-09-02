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

- UNLOCK USAGE
- UNLOCK
- UNLOCK &lt;recno&gt;
- UNLOCK ALL
- UNLOCK TABLE
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
- Included HELP rows: `24`
- HELP reference run: `MANRUN-20260902T151703Z-1CA7DB89`
- Disposition run: `MANRUN-20260902T151704Z-6F39AFBC`
- Authority: `candidate_only`; `publication_authority_claimed=0`
