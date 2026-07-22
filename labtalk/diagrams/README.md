# LabTalk Diagrams

Local diagram shelf for LabTalk and DotTalk++ documentation artifacts.

## LabTalk Campus and SDLC

- `LABTALK_VISUALS_v0.md` - campus, proof path, learning chain, and boundary model
- `LABTALK_SDLC_DIAGRAMS_v0.md` - SDLC/PLDC, real/dev/plugged/planned state maps, case-study lifecycle, and tool lifecycle

DotTalk++ runtime SDLC diagrams are maintained under:

- `D:/code/ccode/docs/maintenance/diagrams/DOTTALKPP_SDLC_DIAGRAMS_v0.md`
- `DOTTALKPP_SHELL_DISPATCH_AND_LOOP_CAPTURE_V1.md` - source-evidenced
  interactive dispatch, canonical execution, active buffering, and captured
  loop replay

## SelfDoc and Contract Lane Flow

- `selfdoc_contract_lane_v1.drawio` - diagrams.net source generated from `tools/diagram/diagram_seed_selfdoc_lane_v1.meta`
- `selfdoc_contract_lane_v1.mmd` - Mermaid flowchart for markdown and website publication
- `SELFDOC_MDO_DATAFLOW_MAP_v0.md` - index for the SelfDoc / MDO dataflow diagram pack
- `selfdoc_mdo_authority_dataflow_v0.mmd` - family-level authority and evidence flow
- `selfdoc_probe_pipeline_dataflow_v0.mmd` - SelfDoc read-only probe pipeline
- `selfdoc_metacollect_metadata_dataflow_v0.mmd` - `metacollect` metadata candidate pipeline
- `mdo_manualgen_publication_dataflow_v0.mmd` - MDO/manualgen draft and promotion pipeline
- `mdo_guarded_help_cmdhelpchk_dataflow_v0.mmd` - guarded HELP/CMDHELPCHK apply gate flow

The diagram captures the current SelfDoc/LANE model:

- intake from chat decisions, `USAGE` blocks, `@dottalk.contract`, HELP/CMDHELP, and metadata imports,
- contract registration, cross-linking, proof promotion, and drift checking,
- SelfDoc `metacollect` and `metadata_collection_v0` report-only pipeline,
- non-mutation and evidence-honesty guards,
- local LabTalk availability before website matriculation.
