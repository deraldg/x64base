# E2 Guarded HELP Refresh Preflight V1

Status: AUTHORIZED / NOT YET APPLIED

Run: `DOCFLUSH-20260825-001-E2-001`

## Measured reason

The integrated documentation preflight reports that the current executable is
newer than the canonical HELP store. Store structure is currently clean, but
freshness is not proven until the store is rebuilt by that executable and the
reflection/readback checks pass.

## Bound scope

- Plan SHA-256:
  `253FE9191A871A61D2B02009C4D67D4D12D25451A738BB6C69294C9426CDDCE2`
- Runtime executable SHA-256:
  `6F76DA3F315A1E5416B608894CB80967F0552B634357BFFC679BD8F5B488082F`
- Command script SHA-256:
  `374AAF10F5088C93F774EB9B07206A3B4BB38E7403D55BE65F38F9E1464DDF61`
- Apply control SHA-256:
  `646C44D60F5DAA2B072FB9E91CA615AC335A60069A069E945F9F93D4242374B8`
- Protected before-set: 39 recursively inventoried files.
- Command order: legacy build, current build, runtime reflection/readback.

The authorization is limited to this exact plan. It does not authorize source,
COMMENTS, manual, website, publication-staging, or push work.

## Fail-closed behavior

The apply control refuses mismatched hashes, an open `dottalkpp.exe`, an
existing backup target, missing transcript markers, runtime failure, semantic
HELP-store failure, or a store that remains older than the executable. Any
failure after backup restores the complete recursive before-set.

## Good Neighbor

- **WHAT CHANGED:** added the guarded E2 plan, exact authorization, command
  script, apply/rollback control, and focused fault-injection tests.
- **WHOSE AREA:** AIF-068 full-stack documentation and protected HELP state,
  intersecting the AIF-132 Portal current-run pointer.
- **AUTHORIZATION:** maintainer instruction to continue after E2 was reported as
  the first open entry, bound to the exact plan hash and 39-file before-set.
- **VERIFY OR UNDO:** run the focused unit test and validate the plan hashes.
  Before apply, delete only this package and control to undo. After apply, use
  the guarded rollback subcommand against the execution record and retained
  backup.

## Attempt 1 correction

Attempt 1 completed the runtime command sequence, then the evidence writer
rejected a repository-relative transcript path. The guard rolled the complete
39-file store back with zero hash mismatches. The only control change resolves
user-supplied paths from the declared repository root; a focused regression
test covers relative output paths. Attempt 1 transcript and failed execution
record remain retained as evidence.
