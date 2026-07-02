# metadata maintenance lane

Runtime surface: `DO METADATA`; `WORKSPACE`; `CATALOGCANARY`

Current role: system metadata storage/workspace lane plus separate collector, checker, and help-consumer boundaries.

This lane belongs to the DotTalk++ maintenance / Blackbox system. It is for external maintenance doctrine and workflow notes, not runtime DotTalk scripts.

Current workflow doctrine:
- [METADATA_FAMILY_SYSTEM_GUIDE_v1.md](D:/code/ccode/docs/maintenance/lanes/metadata/METADATA_FAMILY_SYSTEM_GUIDE_v1.md)
- [METADATA_HELP_MESSAGE_MANUAL_PROMOTION_MODEL_v1.md](D:/code/ccode/docs/maintenance/lanes/metadata/METADATA_HELP_MESSAGE_MANUAL_PROMOTION_MODEL_v1.md)
- [DIAGRAM_METADATA_PROMOTION_GUIDE_v1.md](D:/code/ccode/docs/maintenance/lanes/metadata/DIAGRAM_METADATA_PROMOTION_GUIDE_v1.md)
- [DIAGRAM_METADATA_JOIN_COLUMN_INVENTORY_v1.md](D:/code/ccode/docs/maintenance/lanes/metadata/DIAGRAM_METADATA_JOIN_COLUMN_INVENTORY_v1.md)
- [DIAGRAM_METADATA_V2_HEADER_CANDIDATE_v1.md](D:/code/ccode/docs/maintenance/lanes/metadata/DIAGRAM_METADATA_V2_HEADER_CANDIDATE_v1.md)
- [DIAGRAM_METADATA_V2_PROOF_SAMPLE_v1.md](D:/code/ccode/docs/maintenance/lanes/metadata/DIAGRAM_METADATA_V2_PROOF_SAMPLE_v1.md)
- [DIAGRAM_METADATA_V2_RESTAGE_CANDIDATE_v1.md](D:/code/ccode/docs/maintenance/lanes/metadata/DIAGRAM_METADATA_V2_RESTAGE_CANDIDATE_v1.md)
- [DIAGRAM_METADATA_V2_HELP_ENRICHMENT_BOUNDARY_v1.md](D:/code/ccode/docs/maintenance/lanes/metadata/DIAGRAM_METADATA_V2_HELP_ENRICHMENT_BOUNDARY_v1.md)
- [DIAGRAM_METADATA_V2_ENRICHMENT_WORKLIST_v1.md](D:/code/ccode/docs/maintenance/lanes/metadata/DIAGRAM_METADATA_V2_ENRICHMENT_WORKLIST_v1.md)
- [DIAGRAM_METADATA_V2_COMMAND_ENRICHMENT_SAMPLE_v1.md](D:/code/ccode/docs/maintenance/lanes/metadata/DIAGRAM_METADATA_V2_COMMAND_ENRICHMENT_SAMPLE_v1.md)
- [DIAGRAM_METADATA_V2_MESSAGE_ENRICHMENT_BOUNDARY_v1.md](D:/code/ccode/docs/maintenance/lanes/metadata/DIAGRAM_METADATA_V2_MESSAGE_ENRICHMENT_BOUNDARY_v1.md)
- [DIAGRAM_METADATA_V2_MANUAL_ATTACHMENT_BOUNDARY_v1.md](D:/code/ccode/docs/maintenance/lanes/metadata/DIAGRAM_METADATA_V2_MANUAL_ATTACHMENT_BOUNDARY_v1.md)

Current lane truth:
- the live runtime metadata lane is the `SYS*` DBF catalog under `dottalkpp/data/metadata`
- `DO METADATA` is the canonical lane selector
- `metadata.dtschema`, `metadata_rel.dtschema`, and `metadata_noindex.dtschema` are the live workspace surfaces
- `metacollect` is a separate read-only collector lane, not the live metadata authority
- `HELP`, `CMDHELP`, and `CMDHELPCHK` consume or compare metadata, but they do not own metadata storage
- metadata is also intended to trickle upward into top-level diagram/render consumers such as Mermaid and draw.io

Current next gate:
- normalize scattered metadata doctrine, generated reports, and runtime scripts into a cleaner metadata-first maintenance workflow
