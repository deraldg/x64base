# datadict Blackbox cookbook v1

## Data in
DD* rows, x64 DATA_DICTIONARY_* artifacts, manifests, evidence

## Blackbox process
stage, import, validate, CDX/LMDB, runtime smoke

## Information out
DDICT status/tables/objects/fields/tags/rel/evidence

## Controls
- Start report-only unless a separate apply gate is explicitly authorized.
- Name inputs, outputs, backups, rollback, smoke tests, and next gate before mutation.
- Runtime scripts remain under dottalkpp/data/scripts; maintenance scripts live here.
- Source code remains outside this lane unless a separate source-mutation package is authorized.

## Next planned step
data dictionary system manifest stationing
