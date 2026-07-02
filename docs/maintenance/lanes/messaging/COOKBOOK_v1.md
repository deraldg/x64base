# messaging Blackbox cookbook v1

## Data in
message IDs, language rows, source output strings, placeholders

## Blackbox process
extract, catalog, localize, validate placeholders, phase source replacements

## Information out
typed/localized runtime messages and MSG* candidates

## Controls
- Start report-only unless a separate apply gate is explicitly authorized.
- Name inputs, outputs, backups, rollback, smoke tests, and next gate before mutation.
- Runtime scripts remain under dottalkpp/data/scripts; maintenance scripts live here.
- Source code remains outside this lane unless a separate source-mutation package is authorized.

## Next planned step
messaging source extraction/readiness review
