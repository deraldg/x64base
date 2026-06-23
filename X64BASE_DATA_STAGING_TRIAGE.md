# X64BASE Data Staging Triage

## Scope

This triage covers the remaining review buckets under
`x64base/dottalkpp/data`:

- `dbf/x32`
- `dbf/x64`
- `scripts`
- `workspaces`

This pass is staging guidance only. No restores or deletions are performed
here.

## Summary

Recommended default:

- `keep` canonical sample fixtures and curated regression assets
- `delete` obvious save copies, session state, duplicated scratch workspaces,
  and obsolete packaging clutter
- `review` anything that looks canonical but needs one more conscious fixture
  decision before GitHub staging

## dbf/x32

Tracked deletions: 5

Files:

- `HIERNODE.dbf`
- `README.txt`
- `STUDENTS.DBF`
- `STUD_MAJ.DBF`
- `students_x32_idxtest.dbf`

Recommendation:

- `keep/review`: `HIERNODE.dbf`, `STUDENTS.DBF`, `STUD_MAJ.DBF`
- `review`: `README.txt`
- `delete`: `students_x32_idxtest.dbf`

Rationale:

- The main x32 fixtures look like canonical compatibility/sample data.
- The `idxtest` file reads as a derived or narrow-purpose test copy, not a
  primary fixture.

## dbf/x64

Tracked deletions: 58

### Keep or restore as canonical fixtures

- `BUILDING.DBF`
- `CLASSES.DBF`
- `COURSES.DBF`
- `DEPT.DBF`
- `ENROLL.DBF`
- `MAJORS.DBF`
- `ROOMS.DBF`
- `STUDENTS.DBF`
- `STUD_MAJ.DBF`
- `TASSIGN.DBF`
- `TEACHERS.DBF`
- `TERMS.DBF`
- `community_college_x64_schema.txt`

These look like the canonical x64 community-college fixture family and should
not be dropped casually from a model repo.

### Move out of `dbf/x64`

- `X64SAMPLE.dbf`
- `X64SAMPLE.dtx`
- `X64_ALL_TYPES.dbf`
- `X64_ALL_TYPES.dtx`
- `HIERNODE.DBF`

Rationale:

- These are valid fixtures, but they no longer belong in the runtime-school
  lane.
- `X64SAMPLE*` and `X64_ALL_TYPES*` are better classified as development or
  engine sample fixtures.
- `HIERNODE.DBF` belongs with Dewey/indexing development fixtures rather than
  the school lane.

### Delete

- `fred.dbf`
- everything under `dbf/x64/save/`

Rationale:

- `fred.dbf` is not a kept fixture.
- `save/` is clearly duplicate snapshot state, not canonical fixture content.

## Revised DBF taxonomy

The newer cleanup introduces a better data taxonomy than the older scattered
memo paths.

### Keep: `dbf/dev`

Observed development/sample lane:

- `dbf/dev/HIERNODE.DBF`
- `dbf/dev/X64SAMPLE.dbf`
- `dbf/dev/X64SAMPLE.dtx`
- `dbf/dev/X64_ALL_TYPES.dbf`
- `dbf/dev/X64_ALL_TYPES.dtx`
- `dbf/dev/x32/HIERNODE.dbf`

Rationale:

- `HIERNODE.DBF` is part of the Dewey optimization/indexing development
  system and belongs in a dedicated development-fixture lane.
- `X64SAMPLE*` and `X64_ALL_TYPES*` are development/sample fixtures and fit
  the same lane better than `dbf/x64`.
- `dbf/dev/x32/HIERNODE.dbf` is the x32 companion development fixture.

### Keep: `dbf/memo`

Canonical memo fixture family:

- `MEMO_FOX26.*`
- `MEMO_MAINT.*`
- `MEMO_MSDOS.*`
- `MEMO_SIZE_X64.*`
- `MEMO_VFP.*`
- `MEMO_X64.*`

Observed path:

- `dottalkpp/data/dbf/memo`

Rationale:

- This is a clearer canonical home for memo-format fixtures than mixing them
  into the root `dbf/` lane.

### Keep: `dbf/x64/memo_sample`

Canonical x64 memo sample family:

- `MEMO_FOX26.*`
- `MEMO_MSDOS.*`
- `MEMO_VFP.*`
- `MEMO_X64.*`

Observed path:

- `dottalkpp/data/dbf/x64/memo_sample`

Rationale:

- This cleanly separates x64 memo sample fixtures from the broader x64 fixture
  family and from save/sandbox copies.

### Delete as replaced legacy paths

Treat these tracked deletions as replaced by the new taxonomy, not as losses:

- root `dbf/MEMO_*`
- root `dbf/X64_SAMPLE_ALLFIELDS.dtx`
- `dbf/x64/MEMO_*`
- `dbf/x64/memo/MEMO_*`

Rationale:

- The memo families now have clearer canonical homes under `dbf/memo` and
  `dbf/x64/memo_sample`.
- Old scattered memo locations should not all be restored if the new layout is
  accepted.

Current observed replacement mapping after rescan:

- old `dbf/MEMO_FOX26.*` -> new `dbf/memo/MEMO_FOX26.*`
- old `dbf/MEMO_MSDOS.*` -> new `dbf/memo/MEMO_MSDOS.*`
- old `dbf/MEMO_VFP.*` -> new `dbf/memo/MEMO_VFP.*`
- old `dbf/MEMO_X64.*` -> new `dbf/memo/MEMO_X64.*`
- old `dbf/x64/MEMO_FOX26.*` -> new `dbf/x64/memo_sample/MEMO_FOX26.*`
- old `dbf/x64/MEMO_MSDOS.*` -> new `dbf/x64/memo_sample/MEMO_MSDOS.*`
- old `dbf/x64/MEMO_VFP.*` -> new `dbf/x64/memo_sample/MEMO_VFP.*`
- old `dbf/x64/MEMO_X64.*` -> new `dbf/x64/memo_sample/MEMO_X64.*`
- old `dbf/x64/memo/MEMO_MAINT.*` -> new `dbf/memo/MEMO_MAINT.*`
- old `dbf/x64/memo/MEMO_SIZE_X64.*` -> new `dbf/memo/MEMO_SIZE_X64.*`

These replacements are strong enough to treat the old paths as superseded.

### Delete as ad hoc clutter

- `dbf/students_x64.dbf`
- `dbf/x64/fred.dbf`
- `dbf/x32/students_x32_idxtest.dbf`
- `dbf/sandbox/**`
- `dbf/x64/save/**`

Rationale:

- These read as one-off copies, ad hoc probes, or obsolete scratch fixtures
  rather than canonical project data.

### Review

- `dbf/x64/contraints.ini`
- `dbf/X64_SAMPLE_ALLFIELDS.dtx`

Rationale:

- `contraints.ini` is now present as an untracked file in `dbf/x64`, but its
  contents are legitimate field/rule constraints used as metadata rules for
  field ranges and related validation on a per-directory
  (workspace/schema) basis.
- `X64_SAMPLE_ALLFIELDS.dtx` was deleted from the old root `dbf` lane and no
  matching `X64_SAMPLE_ALLFIELDS.dbf` is present in the current taxonomy.

Decision after rescan:

- `dbf/x64/contraints.ini` -> `keep`
- `dbf/x32/contraints.ini` -> `keep`
- `dbf/X64_SAMPLE_ALLFIELDS.dtx` -> `delete`

## scripts

Tracked deletions: 80

Top-level folders present in the cleaner copy:

- `canaries`
- `cases`
- `main`
- `manual`
- `sub`
- `suites`

Recommendation by group:

Terminology note:

- `.dts` means DotScript
- DotScript is the text-based line-interpreter script format for DotTalk++
- `.dts` files should be treated as intentional script artifacts by default,
  not as disposable text clutter

### Keep

- `canaries/**`
- `cases/**`
- `main/**`
- `suites/**`
- `sub/**`
- `dottalkpp_non_destructive_smoke.dts`

Rationale:

- These look like curated regression, smoke, harness, and nested-script test
  assets. For a model repo, this is useful project evidence, not clutter.

### Review

- `README.txt`
- any files under `manual/` once populated

Rationale:

- `README.txt` may be worth rewriting or relocating, but is not harmful.
- `manual/` is structurally valid, but should be judged once it contains
  deliberate content.

### Delete

- none by default in this pass

Interpretation:

- The earlier deletions of `scripts/**` were probably too aggressive for a
  model repo.

## workspaces

Tracked deletions: 17

On-disk curated-looking files still present:

- `college.dtschemas`
- `default.erz`
- `help.dtschemas`
- `mcc_wsl.dtschemas`
- `mcc_x64.dtschema`
- `mcc.dtschema`
- `mcc.dtschemas`
- `mcc.erz`
- `x64.dtschemas`
- `x64mcc.dtschema`

Deleted set:

- `bigtest.dtschemas`
- `idx_smoke.dtschema`
- `mcc2.dtschemas`
- `mcc_sandbox.dtschema`
- `mcc_x64.dtschema.txt`
- `mcc_x64_output.txt`
- `mem64_test.dtschemas`
- `mem64_vars_test.dtschemas`
- `rel_idx_smoke.dtschema`
- `rel_smoke.dtschema`
- `sample.dtschemas`
- `session.dtschema`
- `tags.dtschemas`
- `test.dtschemas`
- `test1.dtschema`
- `workspace_dtshema2_smoke.dtshema`
- `workspace_rel_smoke.dtshema`

Recommendation:

### Keep

- `bigtest.dtschemas`
- `idx_smoke.dtschema`
- `help.dtschemas`
- `mcc2.dtschemas`
- `mcc_sandbox.dtschema`
- `mcc.dtschema`
- `mcc.dtschemas`
- `mcc_x64.dtschema`
- `mem64_test.dtschemas`
- `mem64_vars_test.dtschemas`
- `rel_idx_smoke.dtschema`
- `rel_smoke.dtschema`
- `sample.dtschemas`
- `session.dtschema`
- `tags.dtschemas`
- `test.dtschemas`
- `test1.dtschema`
- `workspace_dtshema2_smoke.dtshema`
- `workspace_rel_smoke.dtshema`
- `x64.dtschemas`
- `x64mcc.dtschema`
- `college.dtschemas`

Rationale:

- `.dtschema` and `.dtschemas` are workspace files, not disposable session
  byproducts. A workspace stores tables, indexes, and relations, so these
  should default to `keep` unless a specific file is known obsolete.

### Review

- `mcc_wsl.dtschemas`

Rationale:

- `mcc_wsl` may be environment-specific.

### Keep

- `default.erz`
- `mcc.erz`

Rationale:

- `.erz` files are Ersatz browser fixtures and belong with curated workspace
  examples rather than runtime/session trash.

### Delete

- `mcc_x64.dtschema.txt`
- `mcc_x64_output.txt`

Rationale:

- These are plain text derivative/output artifacts, not workspace files.

## Staging recommendation

Safest next GitHub-facing shape for `x64base`:

1. keep all active source changes
2. keep deletion of `dbf/x64/save/**`, `dbf/sandbox/**`, and user workspaces
3. restore `data/scripts/**` unless a specific script is known obsolete
4. restore canonical `dbf/x32` and `dbf/x64` fixture families
5. restore `data/workspaces/*.dtschema*` by default
6. continue deleting workspace text outputs rather than workspace definitions

This should collapse a large part of the remaining noise without throwing away
fixtures that make the repo usable as a model baseline.

## Current residue after restore pass

After restoring the canonical fixture and workspace families, the remaining
`dottalkpp/data` status in `x64base` is mostly concentrated in these buckets:

### Intentional deletes

- `dbf/sandbox/**`
- `dbf/x64/save/**`
- `dbf/x32/students_x32_idxtest.dbf`
- `dbf/students_x64.dbf`
- `dbf/x64/fred.dbf`
- legacy memo files at old scattered paths now superseded by:
  - `dbf/memo/**`
  - `dbf/x64/memo_sample/**`
- `workspaces/mcc_x64.dtschema.txt`
- `workspaces/mcc_x64_output.txt`

These still read as sandbox/save/output/ad hoc clutter rather than canonical
repo assets.

### Generated HELP catalog churn

- `help/cmd_args.dbf`
- `help/cmd_args.dbt`
- `help/commands.dbf`
- `help/commands.dbt`

These look like generated or regenerated help artifacts, but the current delta
is not random local noise.

Observed evidence from the current files versus `HEAD`:

- `commands.dbf` rows: `408 -> 402`
- `cmd_args.dbf` rows: `2068 -> 2059`
- both `.dbt` memo stores grew substantially

Command-key differences show a coherent semantic shift:

- removed function-like entries such as `ABS`, `ACOS`, `ASIN`, `ATAN`,
  `BETWEEN`, `DATEADD`, `DATEDIFF`, `DATETIME`, `DTOS`, `EMPTY`, `EXP`,
  `FLOOR`, `GOMONTH`
- added command surfaces such as `AUTODBF`, `BIBLETALK`, `ERP`,
  `ERROR CLEAR`, `ERROR STATUS`, `ERROR TEST`, `IDX`, `MCC`, `SCX`, `SIX`,
  `SQLHELP`, `TUPEXPORT`, `TUPVALIDATE`, `WHERECACHE`

Interpretation:

- this looks like a real HELP catalog rebuild or surface refresh
- it is consistent with a command catalog becoming more command-focused and
  less mixed with function inventory

Recommended policy:

- keep these changes if the repo intends `commands.dbf` / `cmd_args.dbf` to
  reflect the current command surface
- reset them only if the model repo should avoid checked-in regenerated HELP
  catalogs entirely

### Untracked but plausible keep candidates

- `data/cmdhelp.dts`
- `data/dbf/dev/**`
- `data/dbf/memo/**`
- `data/dbf/x64/memo_sample/**`
- `data/dbf/LabTalk_DotTalkpp_Systems_Storyboard_Deck.pptx` moved out to docs
- `data/metadata.dts`
- `data/metadata_x64.dts`
- `data/pydottalk_shakedown.dts`
- `data/vfp.dts`

The storyboard deck should now be treated as documentation, not a DBF fixture:

- `docs/LabTalk_DotTalkpp_Systems_Storyboard_Deck.pptx`
- `docs/LabTalk_DotTalkpp_Systems_Storyboard_Deck_NOTES.md`

Script/definition vocabulary for this repo:

- `.dts` -> DotScript runtime/test/control script
- `.dtschema` / `.dtschemas` -> workspace definition
- `.erz` -> Ersatz browser artifact

Current classification:

- `cmdhelp.dts` -> keep as lane/bootstrap DotScript
- `metadata.dts` -> keep as lane/bootstrap DotScript
- `metadata_x64.dts` -> keep as lane/bootstrap DotScript
- `vfp.dts` -> keep as lane/bootstrap DotScript
- `pydottalk_shakedown.dts` -> keep as a real DotScript smoke/regression asset
  for `pydottalk`, which is built from `dottalkpp`

These do not read like trash. They look like lane or test scripts and should
be reviewed for promotion, not discarded blindly.
