# SelfDoc Runtime Surface Realignment Audit 20260626 v1

Status: review artifact
Scope: `BBOX`, `MAINT`, `MANUAL`, `DDICT`, adjacent help-family overlap

## Purpose

Record the current overlap, sequence, and user-surface logic across the first-wave SelfDoc runtime commands, then capture the smallest safe realignment applied in this pass.

## Surfaces Examined

- [cmd_bbox.cpp](D:/code/ccode/src/cli/cmd_bbox.cpp:1)
- [cmd_maint.cpp](D:/code/ccode/src/cli/cmd_maint.cpp:1)
- [cmd_manual.cpp](D:/code/ccode/src/cli/cmd_manual.cpp:1)
- [cmd_ddict.cpp](D:/code/ccode/src/cli/cmd_ddict.cpp:1)
- [dotref.hpp](D:/code/ccode/include/dotref.hpp:412)
- [MAINTENANCE_LANE_MANIFEST_v1.md](D:/code/ccode/docs/maintenance/MAINTENANCE_LANE_MANIFEST_v1.md:1)
- [BLACKBOX_LANES_v1.md](D:/code/ccode/docs/maintenance/BLACKBOX_LANES_v1.md:1)
- [SELF_DOC_SUBSYSTEM_MATRIX_v1.md](D:/code/ccode/docs/maintenance/SELF_DOC_SUBSYSTEM_MATRIX_v1.md:1)

## Boundary Model

Current command family is logically defensible when read in this order:

1. `BBOX`
   Teaches the model: data in, processing, information out.
2. `MAINT`
   Teaches the governance layer: lanes, cookbooks, boundaries, gates.
3. `MANUAL`
   Inspects one concrete publication/catalog lane.
4. `DDICT`
   Inspects one concrete metadata/catalog lane.
5. `HELP` / `CMDHELP` / `CMDHELPCHK`
   Prove public help visibility, build/export logic, and validation integrity.

This order was already mostly present in doctrine, but the command UX was not fully aligned with it.

## Overlap Findings

### `BBOX` vs `MAINT`

- `BBOX` is educational and lane-oriented.
- `MAINT` is governance and boundary-oriented.
- This boundary is correct in both code and docs.
- Runtime text already says:
  - `BBOX explains the model.`
  - `MAINT explains the maintenance process, gates, cookbooks, and boundaries.`

Main overlap risk:

- both commands can list lanes, so users may confuse model-teaching with process-governance
- that is acceptable if the no-args behavior stays distinct

### `MANUAL` vs `DDICT`

- both are read-only catalog inspectors
- both report status, structural counts, and resolver behavior
- both belong under the `MAINT` governance umbrella, not the `BBOX` teaching role

Main UX mismatch found:

- `MANUAL` already behaves like a status-first inspector on bare invocation
- `DDICT` previously dropped to usage text on bare invocation
- that made the two concrete inspectors feel inconsistent even though they serve the same operator posture

### Help-Family Overlap

- `HELP`, `DOTHELP`, and `CMDHELP` are related but not identical proof surfaces
- `MANUAL` and `DDICT` should stay concrete lane inspectors, not become alternate help routers
- the current split remains correct

## Realignment Applied In This Pass

### 1. `DDICT` no-args behavior

Changed bare `DDICT` to report `STATUS` instead of usage text.

Reason:

- this makes `DDICT` behave like `MANUAL` and `MAINT`: bare invocation gives the operator current state first
- usage remains available through `DDICT HELP`, `DDICT USAGE`, and `DDICT ?`

### 2. `MANUAL` short-form aliases

Added direct aliases:

- `MANUAL STATUS`
- `MANUAL TABLES`
- `MANUAL COUNTS`
- `MANUAL RESOLVE <token>`
- `MANUAL CATALOG` now resolves to status

Reason:

- the existing `CATALOG <verb>` namespace is structurally valid but awkward for operators
- short aliases preserve doctrine while making the runtime surface easier to remember

### 3. Public syntax alignment

Updated native public reference text in [dotref.hpp](D:/code/ccode/include/dotref.hpp:412) so it matches the runtime realignment:

- `DDICT` now documents bare invocation and status-first posture
- `MANUAL` now documents short-form aliases alongside the existing `CATALOG` forms

## What Was Not Changed

- `BBOX` remains model-first on bare invocation and prints both model and lanes
- `MAINT` remains status-first on bare invocation
- `MANUAL` remains read-only and self-contained
- `DDICT` bridge logic and owner-resolution behavior were not changed
- help-family build/check architecture was not merged into these lane inspectors

## Recommended Operator Sequence

For a new operator or reviewer:

1. `BBOX`
2. `MAINT`
3. `MAINT LANES`
4. `MANUAL STATUS`
5. `DDICT STATUS`
6. `CMDHELP <surface>`
7. `CMDHELPCHK`

That sequence preserves concept -> governance -> concrete subsystem -> help proof.

## Next Logical Realignment

The next safe step is not to merge these commands, but to improve cross-navigation:

- `MAINT` should eventually accept direct lane topics such as `COMMENTS`, `HELP`, `CMDHELPCHK`, `MANUAL`, `DDICT`, and `MESSAGING`
- `BBOX` should eventually expose `CMDHELPCHK` as a first-class teaching lane topic, because the doctrine already treats it that way

Those should be done with message-catalog-backed text so the messaging lane stays authoritative.
