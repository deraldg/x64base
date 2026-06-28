# DotTalk++ Manual Diagram Asset Registry v1

Status: simple visual asset registry  
Audience: reader manual maintainer, human developer, AI development agent  
Source root: `D:\code\ccode`

These SVG diagrams are manual anchors. They are intentionally simple, source-controlled visual aids that can be embedded in the reader manual, developer manual, data dictionary manual, or presentations.

Companion CSV:

- `docs/manuals/assets/diagrams/manual_diagram_asset_registry_v1.csv`

## Assets

| Asset ID | File | Manual anchor | Purpose |
|---|---|---|---|
| `DIAG-ARCH-LAYERS` | `dottalkpp_architecture_layers_v1.svg` | `ANCHOR-X64BASE-README` | Four-layer working model. |
| `DIAG-EVIDENCE-PIPELINE` | `evidence_to_manual_pipeline_v1.svg` | `ANCHOR-MANUAL-DIAGRAMS` | Evidence-to-manual promotion path. |
| `DIAG-TRINITY-HEADERS` | `trinity_headers_v1.svg` | `ANCHOR-X64-TRINITY` | Trinity header dependency and roles. |
| `DIAG-X64-SELF-DESCRIBING` | `x64_self_describing_dbf_v1.svg` | `ANCHOR-X64-VECTOR-NAMES` | In-file X64M self-description. |
| `DIAG-COMMAND-HARVEST` | `command_reference_harvest_v1.svg` | `ANCHOR-COMMAND-USAGE-HARVEST` | Source usage contracts into guide entries. |
| `DIAG-WORKAREAS-CURSOR` | `workareas_cursor_control_v1.svg` | `ANCHOR-CURSOR-WORKAREAS` | Current area and current record model. |
| `DIAG-LOCKING-LIFECYCLE` | `locking_lifecycle_v1.svg` | `ANCHOR-LOCKING` | Lock, mutate, unlock lifecycle. |
| `DIAG-BUFFER-COMMIT-ROLLBACK` | `table_buffer_commit_rollback_v1.svg` | `ANCHOR-TABLE-BUFFER`; `ANCHOR-COMMIT-ROLLBACK` | Buffered mutation closure. |
| `DIAG-INDEX-ORDER` | `index_order_cdx_lmdb_v1.svg` | `ANCHOR-X64-INDEXING` | Logical order versus backend storage. |
| `DIAG-MEMO-DTX` | `memo_dtx_sidecar_v1.svg` | `ANCHOR-X64-MEMOS` | DBF memo object ID to DTX payload. |
| `DIAG-MANUAL-FAMILY` | `manual_family_v1.svg` | `ANCHOR-MANUAL-DIAGRAMS` | Full manual family shape. |
| `DIAG-MATURITY-MODEL` | `maturity_model_v1.svg` | `ANCHOR-MANUAL-DIAGRAMS` | M0-M6 manual maturity ladder. |
| `DIAG-PROOF-LOOP` | `readback_proof_loop_v1.svg` | `ANCHOR-RUNTIME-PROOFS` | Run, capture, readback, promote loop. |

## Use Rule

Each diagram should be treated like prose: it needs an anchor, a purpose, and a maturity state. Do not use a diagram to imply a feature is runtime-proven unless the related manual section has proof.
