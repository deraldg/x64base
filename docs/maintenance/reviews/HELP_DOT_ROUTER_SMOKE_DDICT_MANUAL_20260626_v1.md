# HELP /DOT Router Smoke DDICT MANUAL 20260626 v1

Status: report-only router smoke artifact
Date: 2026-06-26
Runtime: `D:\code\ccode\dottalkpp\bin\dottalkpp.exe`
Working data root: `D:\code\ccode\dottalkpp\data`

## Purpose

Record the current runtime truth for the previously-reported `MANUAL` / `DDICT` `DOTHELP` and `HELP /DOT` router surfaces.

## Commands run

```text
DOTHELP DDICT
HELP /DOT DDICT
DOTHELP MANUAL
HELP /DOT MANUAL
QUIT
```

## Observed result

All four commands rendered the expected canonical DOTREF entry.

Observed summary:

- `DOTHELP DDICT`: green
- `HELP /DOT DDICT`: green
- `DOTHELP MANUAL`: green
- `HELP /DOT MANUAL`: green

## Rendered topics

`DDICT` rendered:

- syntax:
  - `DDICT [HELP|STATUS|TABLES|OBJECTS|FIELDS <table>|TAGS <table>|REL <object>|EVIDENCE <object>]`
- summary:
  - `Inspect the active Data Dictionary catalog from inside DotTalk++.`

`MANUAL` rendered:

- syntax:
  - `MANUAL [USAGE|CATALOG STATUS|CATALOG TABLES|CATALOG COUNTS|CATALOG RESOLVE <token>|SECTIONS|MEDIA|REVIEW]`
- summary:
  - `Inspect the accepted MAN* manualgen catalog from inside DotTalk++.`

## Conclusion

The previously recorded `HELP /DOT` red state for `DDICT` and `MANUAL` was historical, not current.

Current repo runtime truth:

- comments lane: green
- CMDHELP lane: green from prior operator evidence
- DOTREF presence: green
- `DOTHELP` / `HELP /DOT`: green in current runtime smoke

## Next gate

1. update per-command continuity reports so they stop naming router proof as the first active red layer
2. use this smoke pattern on the next help-family targets instead of carrying forward historical router assumptions
