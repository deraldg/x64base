# MDO-381E Manual Family Runtime Surface Alignment Milestone Packet

Status: `MANUAL_FAMILY_RUNTIME_SURFACE_ALIGNMENT_MILESTONE_GREEN_REPORT_ONLY`

## Purpose

Capture the current milestone where the developer-manual publication lanes,
working draft, and runtime documentation-family command surfaces are aligned
enough to continue promotion work without inventing a parallel manual-only
story.

## Milestone conclusion

The documentation family now has a stable role split that is visible in both
manual structure and runtime command surfaces:

- `MANUAL` inspects accepted manual-catalog state
- `DDICT` inspects accepted Data Dictionary catalog state
- `BBOX` teaches the blackbox model of the documentation/maintenance lanes
- `MAINT` reports the maintenance/control-surface view of those lanes

This split is now reflected in:

- the current primary reader artifact
- the combined working draft
- the publication-lane index and lane-local READMEs
- a dedicated runtime-surface crosswalk report

## Baseline

- Primary reader artifact:
  `docs/manuals/developer/manualgen/published/developer_manual_publication_v1/developer_manual_publication_v1.md`
- Primary reader pointer:
  `docs/manuals/developer/manualgen/accepted_artifacts/ACTIVE_PRIMARY_READER_ARTIFACT.txt`
- Working draft bundle:
  `docs/manuals/developer/DEVELOPER_MANUAL_DRAFT_COMBINED.md`
- Publication lane index:
  `docs/manuals/developer/manualgen/published/README.md`

## Normalization completed in this milestone

### Lane identity cleanup

Publication lanes were reclassified so they no longer read like competing
manuals:

- primary reader artifact remains `developer_manual_publication_v1`
- controlled promotion candidate remains
  `developer_manual_publication_v1_python_rebuild_candidate_v1`
- media/manual-mutation/manual-CLI lanes are now explicitly documented as
  supporting publication workspaces

### Runtime-surface crosswalk added

Crosswalk artifact:

`docs/manuals/developer/manualgen/reports/manual_family_runtime_surface_crosswalk_v1.md`

This artifact records the current live surfaces and their roles:

- `src/cli/cmd_manual.cpp`
- `src/cli/cmd_ddict.cpp`
- `src/cli/cmd_bbox.cpp`
- `src/cli/cmd_maint.cpp`

### Working draft strengthened

The combined draft now explicitly states that the documentation family has live
runtime inspection/teaching surfaces and names their roles directly.

### Primary reader corrected conservatively

The current primary reader artifact now includes a conservative subsection
stating that the documentation family is not only report-driven; it also has
runtime inspection and teaching surfaces.

## Why this is a milestone

Before this pass, the draft doctrine was ahead of the primary reader, and the
runtime documentation-family commands existed without being clearly reflected in
the reader/publication structure.

After this pass:

- the tree tells a human what to read first
- the draft no longer treats these lanes as report-only abstractions
- the primary reader no longer omits the live command surfaces
- future promotion work has an explicit backbone instead of a drifting prose
  model

## Boundaries honored

- no reader-pointer promotion
- no accepted-manifest replacement
- no MAN* DBF/catalog mutation
- no HELP, META, CMDHELPCHK, or runtime data mutation
- no source changes outside documentation-family prose/crosswalk alignment

## Recommended next gate

`HOLD_OR_AUTHORIZE_MESSAGING_AND_LOCALIZATION_DOCUMENTATION_PROMOTION_PASS`

Reason:

The next content lane most likely to benefit from the same treatment is the
messages/localization family, because the current draft already carries stronger
doctrine than the primary reader and that lane now has real runtime/system
surfaces that should be reflected consistently.
