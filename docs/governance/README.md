# Governance Notes

This directory holds durable rules that constrain future work across the
runtime, documentation, GUI, and campus layers.

Start here:

- `REPO_BOUNDARIES_RUNTIME_GUI_LABTALK_v1.md`
- `anti_drift_best_practices.md`
- `..\DOC_AUTHORITY_INDEX.json`

Current emphasis:

- `x64base` remains the authority for engine/runtime truth
- Arctic GUI/TUI work stays with the runtime/engine tree
- LabTalk is a consumer layer for portal, labs, proofs, assignments, and campus overlays
- `DotTalk++` remains a runtime/manual identity without forcing a premature source split

Report-only authority verification currently runs through:

- `tools/docs_drift_check.ps1`
