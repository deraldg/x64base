# help maintenance lane

Runtime surface: HELP; DOTHELP; CMDHELP

Current role: HELP DATA builder/report layer plus separate DOTREF/router proof surfaces.

This lane belongs to the DotTalk++ maintenance / Blackbox system. It is for external maintenance cookbooks and scripts, not runtime DotTalk scripts.

Current workflow doctrine:
- [HELP_DOCUMENT_FAMILY_SYSTEM_GUIDE_v1.md](D:/code/ccode/docs/maintenance/lanes/help/HELP_DOCUMENT_FAMILY_SYSTEM_GUIDE_v1.md)
- [HELP_LOCALE_WORKFLOW_v1.md](D:/code/ccode/docs/maintenance/lanes/help/HELP_LOCALE_WORKFLOW_v1.md)
- [COMMENTS_HELP_PROOF_WORKFLOW_v1.md](D:/code/ccode/docs/maintenance/COMMENTS_HELP_PROOF_WORKFLOW_v1.md)
- [HELP_CMDHELP_DOTREF_PIPELINE_NOTES_v1.md](D:/code/ccode/docs/maintenance/lanes/help/HELP_CMDHELP_DOTREF_PIPELINE_NOTES_v1.md)
- [HELP_FAMILY_STATUS_MANIFEST_v1.md](D:/code/ccode/docs/maintenance/lanes/help/HELP_FAMILY_STATUS_MANIFEST_v1.md)

Current lane truth:
- `HELP`, `CMDHELP`, `DOTHELP`, and `FOXHELP` have current source/comments/runtime proof.
- the curated parent `CMDHELPCHK ARTIFACTS` pass is now green after the SET-family HELP DATA canonicalization repair.
- `DDICT` and `MANUAL` are now closed through the same current same-pass checkpoint pattern.
- `BBOX` and `MAINT` are fully closed through `CMDHELPCHK`.
- `CMDHELP HELP` remains a documented self-usage special case, not the parent topic-proof surface for `HELP`.

Current next gate:
- reconcile stale planning notes that still describe already-closed `DDICT`, `MANUAL`, or parent help-family work as future work
- hold normal `CMDHELP` on canonical/source English while preparing a separate locale-preview consumer
