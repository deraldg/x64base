# manualgen Blackbox cookbook v1

## Data in
manual sections, appendices, media anchors, manifests, review queues

## Blackbox process
assemble, normalize, validate, publish, catalog, smoke

## Information out
published manuals, MAN* catalog, MANUAL runtime view

## Controls
- Start report-only unless a separate apply gate is explicitly authorized.
- Name inputs, outputs, backups, rollback, smoke tests, and next gate before mutation.
- Runtime scripts remain under dottalkpp/data/scripts; maintenance scripts live here.
- Source code remains outside this lane unless a separate source-mutation package is authorized.

## Next planned step
manualgen cookbook integration with maintenance root
