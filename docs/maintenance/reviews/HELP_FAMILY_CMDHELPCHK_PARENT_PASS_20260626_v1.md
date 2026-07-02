# HELP Family CMDHELPCHK Parent Pass 20260626 v1

Status: report-only maintenance validation artifact
Scope: `HELP`, `CMDHELP`, `DOTHELP`, `FOXHELP`
Runtime root: `D:\code\ccode\dottalkpp`

## Purpose

Record the first curated `CMDHELPCHK` pass for the parent help-family surfaces after the comments-lane `IMPORT` repair.

This pass was intended to reduce the remaining “checkpoint deferred” area in the help-family lane.

## Commands run

```text
CMDHELPCHK
CMDHELPCHK ARTIFACTS . 5
CMDHELP HELP
CMDHELP DOTHELP
CMDHELP FOXHELP
QUIT
```

Executed from:

- `D:\code\ccode\dottalkpp\data`
- binary: `D:\code\ccode\dottalkpp\bin\dottalkpp.exe`

## Observed results

### 1. Reflection validation

`CMDHELPCHK` noargs completed and ended with:

- `Structural Checks`
- `OK no structural issues found`

Interpretation:

- the reflected parent help-family command structure is currently coherent enough for this checkpoint
- no fresh structural break was observed in:
  - `HELP`
  - `CMDHELPCHK`
  - `SET` subcommand family reflection
  - reflected function inventory

### 2. HELP DATA v2 artifact validation

`CMDHELPCHK ARTIFACTS . 5` opened:

- `D:\code\ccode\dottalkpp\data\help\help_artifacts.dbf`

Key findings:

- artifact rows: `5,507`
- source-miner rows: `91`
- blank text rows: `16`
- reported orphan `CMDKEY` rows: `5,495`
- reported compact DOT SET-family artifact rows: `46`

The actionable error from this pass is:

- compact SET-family artifact `CMDKEY` rows still use forms such as:
  - `DOT|SETCASE`
  - `DOT|SETCNX`
  - `DOT|SETFILTER`
  - `DOT|SETINDEX`
  - `DOT|SETNEAR`
  - `DOT|SETORDER`
  - `DOT|SETPATH`

Expected canonical keys are:

- `DOT|SET CASE`
- `DOT|SET CNX`
- `DOT|SET FILTER`
- `DOT|SET INDEX`
- `DOT|SET NEAR`
- `DOT|SET ORDER`
- `DOT|SET PATH`

Interpretation:

- this is a real lane defect in HELP DATA v2 artifact key normalization
- it is not a comments-lane/import defect
- it is also not a parent help-family router defect

### 3. CMDHELP topic visibility

`CMDHELP DOTHELP` was green and rendered the expected `DOT|DOTHELP` topic.

`CMDHELP FOXHELP` was green and matched both:

- `DOT|FOXHELP`
- `FOX|FOXHELP`

Interpretation:

- `DOTHELP` is visible through current `CMDHELP`
- `FOXHELP` remains a dual-catalog continuity fact and is visible through current `CMDHELP`

### 4. `CMDHELP HELP` special behavior

`CMDHELP HELP` did **not** render a `HELP` topic page.

It rendered `CMDHELP` usage text instead.

That behavior matches the current implementation in [cmdhelp.cpp](D:/code/ccode/src/cli/cmdhelp.cpp:1748), where `HELP` is treated as a usage request token for the `CMDHELP` surface itself.

Interpretation:

- this is currently a surface rule, not necessarily a defect
- it means `CMDHELP HELP` cannot currently be used as the parent-surface topic proof for `HELP`
- `HELP` parent proof should continue to rely on:
  - `HELP`
  - `HELP HELP`
  - `HELP /DOT HELP`
  - comments-lane proof
  - router/catalog proof

## Follow-up repair and rerun

After the first pass, the HELP DATA bridge was repaired so SET-family registry/catalog/doc rows canonicalize to spaced command identities such as:

- `SET ORDER`
- `SET INDEX`
- `SET PATH`

Validation rerun commands:

```text
CMDHELP BUILD
CMDHELPCHK ARTIFACTS . 5
CMDHELP DOTHELP
CMDHELP FOXHELP
QUIT
```

Executed from:

- `D:\code\ccode\dottalkpp\data`
- binary: `D:\code\ccode\build\src\Release\dottalkpp.exe`

Observed rerun results:

- `compact DOT SET-family command keys : 0`
- `compact DOT SET-family artifact rows: 0`
- `SET-family alias/variant rows       : 0`
- `CMDHELP DOTHELP` remained green
- `CMDHELP FOXHELP` remained green

Interpretation:

- the parent help-family SET canonicalization defect is repaired
- the curated parent `CMDHELPCHK ARTIFACTS` gate is now green for this issue
- the remaining parent-surface special case is still `CMDHELP HELP`, which intentionally routes to `CMDHELP` usage under the current implementation

## Continuity findings

Current truth from this pass:

- `CMDHELPCHK` reflection mode is green
- `CMDHELP DOTHELP` is green
- `CMDHELP FOXHELP` is green
- `CMDHELP HELP` is reserved by current command behavior as a usage alias path
- HELP DATA v2 SET-family artifact canonicalization is now green after the follow-up repair

This means the remaining parent help-family checkpoint work is now narrower than before:

1. decide whether `CMDHELP HELP` should remain a self-usage alias or gain an explicit topic escape path
2. carry the same curated `CMDHELPCHK` pattern into `DDICT` and `MANUAL`
3. reconcile stale notes that still describe already-repaired SET-family artifact work as open

## Recommended next gate

1. Preserve the current `CMDHELP HELP` behavior as a documented surface rule unless and until a deliberate behavior-change package is authorized.
2. Do not reopen comments/import or SET-family artifact work unless staged/live evidence diverges again.
3. Promote `DDICT` and `MANUAL` from deferred checkpoint state by running the same curated `CMDHELPCHK` validation pattern on their current green comments/runtime surfaces.
