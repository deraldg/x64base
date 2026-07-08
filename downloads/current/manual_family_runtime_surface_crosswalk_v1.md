# DotTalk++ Manual Family Runtime Surface Crosswalk v1

Date: 2026-07-08

## Purpose

Record the current read-only runtime inspection surfaces that already exist for
the documentation family, so manual promotion work uses live command behavior
instead of inventing a parallel manual-only story.

## Surfaces

### MANUAL

Source:
`src/cli/cmd_manual.cpp`

Role:
- read-only inspector over the accepted `MAN*` manualgen catalog
- reports manual catalog status, expected tables, counts, resolver behavior,
  and focused manual table inspection

Current shape:
- `MANUAL`
- `MANUAL STATUS`
- `MANUAL TABLES`
- `MANUAL COUNTS`
- `MANUAL RESOLVE <token>`
- `MANUAL SECTIONS`
- `MANUAL MEDIA`
- `MANUAL REVIEW`

Meaning:
- `MANUAL` is not the manual generator
- `MANUAL` is the runtime visibility surface over accepted manual catalog state
- manual publication lanes should coordinate with this command rather than
  restating MAN* catalog structure from prose alone

### DDICT

Source:
`src/cli/cmd_ddict.cpp`

Role:
- read-only Data Dictionary inspector for the active catalog metadata
- bridges legacy `DD*` names and authoritative x64
  `DATA_DICTIONARY_*` identities

Current shape:
- `DDICT`
- `DDICT STATUS`
- `DDICT TABLES`
- `DDICT FIELDS <table-or-alias>`
- `DDICT TAGS <table-or-alias>`
- `DDICT REL <object> [IN|OUT|BOTH]`
- `DDICT EVIDENCE <object>`
- `DDICT OBJECTS [TYPE <type>] [PROFILE <profile>]`

Meaning:
- Data Dictionary prose in manuals should coordinate with the runtime catalog
  inspector
- the manual should distinguish catalog tags from physical CDX/LMDB artifacts
  because the command already does

### BBOX

Source:
`src/cli/cmd_bbox.cpp`

Role:
- educational model/teaching surface
- explains the documentation and maintenance family as blackbox systems:
  data in, process, information out

Current topics:
- `BBOX MODEL`
- `BBOX LANES`
- `BBOX COMMENTS`
- `BBOX HELP`
- `BBOX MANUALGEN`
- `BBOX DATADICT`
- `BBOX MESSAGING`
- `BBOX MAINT`
- `BBOX CONTRACTS`

Meaning:
- BBOX is the teaching vocabulary surface for these lanes
- prose that explains the documentation family conceptually should align with
  BBOX rather than drift into a separate educational model

### MAINT

Source:
`src/cli/cmd_maint.cpp`

Role:
- read-only maintenance/control-surface inspector
- reports lane purpose, cookbook/docs roots, GUI lane, AI Friendly lane, and
  contract-lane status

Current shape:
- `MAINT STATUS`
- `MAINT LANES`
- `MAINT COOKBOOK`
- `MAINT BOUNDARY`
- `MAINT BBOX`
- `MAINT DOCS`
- `MAINT GUI`
- `MAINT AI ...`
- `MAINT CONTRACTS ...`

Meaning:
- MAINT is the manager/visibility side
- BBOX is the conceptual teaching side
- the manual should keep that distinction instead of collapsing them into one

## Coordination rule

Use this split consistently:

- `MANUAL` inspects the accepted manual catalog
- `DDICT` inspects the accepted Data Dictionary catalog
- `BBOX` teaches the conceptual blackbox model of the lanes
- `MAINT` reports the maintenance/control surface around those lanes

## Manual promotion implication

The combined developer draft is stronger than the current reader artifact in
overall doctrine, but it was under-explicit about these runtime surfaces.

Before promoting more draft prose into the primary reader artifact:

1. preserve the current doctrine that manuals and websites derive from the same
   reviewed evidence spine
2. add explicit runtime-surface crosswalk prose for `MANUAL`, `DDICT`, `BBOX`,
   and `MAINT`
3. avoid describing lane ownership in a way that contradicts the commands above

## Boundary

Report only.

No source, HELP, META, catalog, or publication mutation is performed by this
crosswalk artifact.
