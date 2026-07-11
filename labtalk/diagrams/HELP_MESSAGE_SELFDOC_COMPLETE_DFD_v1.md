# HELP / Message / Metadata / SelfDoc / MDO Complete DFD v1

Status: **source-derived consolidated draft**
Scope: DotTalk++ and x64base documentation, messaging, proof, manual, diagram,
and website-publication systems.

This pack consolidates the existing partial SelfDoc/MDO diagrams without
replacing them. It adds the runtime message-provider path, HELP DATA v2 stores,
canonical metadata stores, proof registry, public artifact stores, and the
simplex/duplex publication gates.

## Diagram Levels

1. `help_message_selfdoc_context_dfd_v1.mmd` - context boundary and external entities.
2. `help_message_selfdoc_level1_dfd_v1.mmd` - complete end-to-end system flow.
3. `help_message_selfdoc_level2_runtime_dfd_v1.mmd` - source, message, HELP DATA, metadata, and CMDHELPCHK detail.
4. `help_message_selfdoc_level2_promotion_dfd_v1.mmd` - SelfDoc, proof, MDO, manualgen, diagram, and publication detail.

## Core Authority Doctrine

```text
Runtime proves.
Source defines.
HELP explains.
Metadata organizes.
CMDHELPCHK validates.
SelfDoc preserves provenance.
MDO curates.
Manualgen inventories, validates, and packages draft views.
Manuals, diagrams, and websites publish reviewed derivatives.
```

## Critical Separation

- `helpdata_messages.*` is the compiled bootstrap and failure-safe fallback.
- `SYSTEM_MESSAGES` and `SYSTEM_MESSAGE_TEXT` are the active locale-aware
  runtime message workspace when present.
- HELP DATA topic/section/line/artifact tables are the organized explanation
  store, not runtime implementation authority.
- `SYSCMD`, `SYSSUBCMD`, `SYSFUNC`, `SYSARGS`, and `SYSMSG` are normalized
  metadata and crosswalk stores.
- SelfDoc probes are report-only by default.
- MDO/manualgen outputs do not mutate source, HELP, metadata, CMDHELPCHK, or
  runtime data without a separate authorization gate.
- Website-to-manual technical intake is blocked by default. Separately
  maintained public-only media, contact, branding, and navigation artifacts are
  the reviewed exception.

## Source Basis

- `docs/HELP_METADATA_SELFDOC_WORKFLOW_v1.md`
- `dottalkpp/docs/authority/help_message_reference_authority_model_v1.md`
- `dottalkpp/docs/messaging/RUNTIME_MESSAGE_CATALOG_SEED_WORKFLOW_v1.md`
- `src/help/message_catalog.cpp`
- `src/help/helpdata_messages.*`
- `src/help/helpdata_model.*`
- `src/help/helpdata_source_miner.*`
- `selfdoc/tool_manifest.yaml`
- `selfdoc/pipeline_manifest.yaml`
- `tools/manualgen/README.md`
- `labtalk/registries/proofs.yaml`
- `labtalk/diagrams/SELFDOC_MDO_DATAFLOW_MAP_v0.md`

## Honesty Boundary

This pack describes both working and target-state flows. It does not claim that
all generators or all metadata tables are complete. Current report-only,
candidate, reviewed-import, runtime-observed, and published states remain
separate in the diagrams.
