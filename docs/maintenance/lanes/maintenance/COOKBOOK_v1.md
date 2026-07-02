# maintenance Blackbox cookbook v1

## Data in
cookbooks, scripts, lane manifests, gates

## Blackbox process
list, plan, check, launch guarded procedures later

## Information out
maintenance status, cookbook index, launch sequence catalog

## Controls
- Start report-only unless a separate apply gate is explicitly authorized.
- Name inputs, outputs, backups, rollback, smoke tests, and next gate before mutation.
- Runtime scripts remain under dottalkpp/data/scripts; maintenance scripts live here.
- Source code remains outside this lane unless a separate source-mutation package is authorized.

## Next planned step
MAINT command design plan
