# cmdhelpchk Blackbox cookbook v1

## Data in
runtime registry, HELP DATA, usage contracts, command-local usage, comments evidence, curated catalogs

## Blackbox process
validate coverage, classify gaps, produce review queues

## Information out
coverage reports and repair queues

## Current role
- validation/checkpoint layer
- compare evidence and collection layers without assuming router proof is already green
- support closure notes that identify the first red layer

## Suggested report-only procedure

1. Read runtime registry expectations.
2. Read source usage-contract expectations.
3. Read comments evidence expectations where relevant.
4. Read current HELP DATA artifact presence.
5. Record whether `CMDHELP` is green for the target.
6. Record whether `DOTHELP` / `HELP /DOT` are green for the target.
7. Classify mismatches by layer instead of treating all help failures as one class.

## Classification rule

- A command visible in `CMDHELP` but red in `HELP /DOT` is not a HELP DATA failure by default.
- First classify that mismatch as router/catalog/binary-layer red until proven otherwise.

## Controls
- Start report-only unless a separate apply gate is explicitly authorized.
- Name inputs, outputs, backups, rollback, smoke tests, and next gate before mutation.
- Runtime scripts remain under dottalkpp/data/scripts; maintenance scripts live here.
- Source code remains outside this lane unless a separate source-mutation package is authorized.

## Next planned step
CMDHELPCHK v2 crosswalk alignment
