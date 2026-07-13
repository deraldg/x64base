# SelfDoc / MDO Dataflow Map v0

Status: draft diagram pack

These diagrams summarize the active SelfDoc and Master Document Organizer
system as observed from the current policy, manifest, MDO packet, and LabTalk
materials.

## Diagrams

- `selfdoc_mdo_authority_dataflow_v0.mmd` - family-level authority and dataflow.
- `selfdoc_probe_pipeline_dataflow_v0.mmd` - SelfDoc inventory/probe flow and non-mutation gates.
- `selfdoc_metacollect_metadata_dataflow_v0.mmd` - `metacollect` and metadata candidate flow.
- `mdo_manualgen_publication_dataflow_v0.mmd` - MDO/manualgen work-order publication flow.
- `mdo_guarded_help_cmdhelpchk_dataflow_v0.mmd` - guarded HELP/CMDHELPCHK apply-gate flow.

## Reading Notes

The common doctrine is:

```text
Runtime proves.
Source defines.
HELP explains.
Metadata organizes.
CMDHELPCHK validates.
SelfDoc preserves provenance.
MDO/manualgen promotes reviewed views.
```

SelfDoc and MDO are deliberately conservative. Most lanes are report-only until
an explicit review gate authorizes mutation. Diagrams and manuals are promoted
views; they do not replace runtime, source, HELP, metadata, or CMDHELPCHK.

## Source Basis

- `docs/HELP_METADATA_SELFDOC_WORKFLOW_v1.md`
- `docs/governance/02_selfdoc_and_mdo_roles.md`
- `selfdoc/tool_manifest.yaml`
- `selfdoc/pipeline_manifest.yaml`
- `selfdoc/SELFDOC_INVENTORY_PROBE_PLAN_v0.md`
- `selfdoc/SELFDOC_EXTERNAL_TOOL_INTAKE_POLICY_v0.md`
- `docs/manuals/developer/manualgen/README.md`
- `docs/manuals/developer/manualgen/review_packets/MDO-334_MAINT_LANE_CLOSURE_NEXT_DECISION_PACKET.md`
- `docs/manuals/developer/manualgen/review_packets/MDO-335_GUARDED_HELP_CMDHELPCHK_APPLY_PLAN_PACKET.md`
- `docs/manuals/developer/manualgen/review_packets/MDO-336_GUARDED_HELP_CMDHELPCHK_APPLY_EXECUTION_PACKET.md`
