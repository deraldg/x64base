# LabTalk Case Catalog Review v2

Safety: REPORT_ONLY / NO SOURCE-EVIDENCE MUTATION.

## Summary

- case_files: 15
- runtime_loadable_failures: 0
- registry_alignment_warn_or_fail: 0
- media_reference_warn_or_fail: 0
- first_wave_review_candidate: 5
- stub_registered: 5
- runtime_lab_candidate: 5
- gate: REVIEW_V2_STRUCTURE_GREEN_MEDIA_DRIFT_CLOSED_CATALOG_PROOF_CAPTURED_BEHAVIORAL_PROOF_OPEN

## Changes Since v1

The catalog no longer has active media-reference drift. Historical stub cases now reference media IDs that exist in `MEDIA_ASSET_REGISTRY_v0.csv`. Engineering runtime-lab cases no longer claim placeholder media IDs; they now point to runtime proof packets instead.

The FoxPro crosswalk source filename is aligned to the observed source spelling: `FoxPro -> DotTalkpp crosswalk (1).docx`.

The five strongest historical cases are now marked `first_wave_review_candidate`:

- HIST-000 The Data Trail Overview
- HIST-020 JUMPS / 73C Army System
- HIST-030 Unisys / CODASYL at ALCOA
- HIST-040 xBase as a Major Platform
- HIST-090 DotTalk++ / LabTalk and the AI Future

These are not publication-ready. They remain `hidden_until_reviewed`.

## New Control Artifacts

- `LABTALK_SOURCE_TO_CASE_INVENTORY_V1.md`
- `LABTALK_OVERLAY_BOUNDARY_V1.md`
- `LABTALK_ENG_RUNTIME_PROOF_PLAN_V1.md`
- `runtime_proofs/ENG-010_RUNTIME_PROOF.md`
- `runtime_proofs/ENG-020_RUNTIME_PROOF.md`
- `runtime_proofs/ENG-030_RUNTIME_PROOF.md`
- `runtime_proofs/ENG-040_RUNTIME_PROOF.md`
- `runtime_proofs/ENG-050_RUNTIME_PROOF.md`

The five ENG proof packets include catalog-read proof from `CASE SHOW ENG-010` through `CASE SHOW ENG-050` against `D:\code\ccode\build\src\Release\dottalkpp.exe` on 2026-06-28. Behavioral fixture proof remains open.

## Open Gates

The current structure is green, but publication gates remain open:

- first-wave historical cases still need source/factual/media review closure
- ENG cases still need behavioral fixture proof beyond catalog rendering
- all cases remain hidden until reviewed

## Boundary

LabTalk remains an optional education overlay. No source DOCX, storyboard deck, case media, or student-facing case prose is required for the x64base engine boundary.
