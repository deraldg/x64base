---
id: ENG-020
title: SEEK vs SCAN
type: engine_case
era: 1985-present
level: student
lab: LAB_CASE_SEEK_VS_SCAN
domains: [seek, scan, predicate, index, execution-plan]
status: runtime_lab_candidate
review_status: needs_runtime_proof_attachment
evidence_class: source_doc_plus_project_status
runtime_visibility: hidden_until_reviewed
manual_visibility: draft_outline
source_docs: [Case Studies Core Track.docx]
media_assets: []
runtime_proof: [runtime_proofs/ENG-020_RUNTIME_PROOF.md]
---

## SUMMARY

This runtime case contrasts point lookup through an active order with sequential predicate evaluation.

## PROBLEM

Finding a record is not one operation internally. A system may seek through an index, scan records, or combine strategies. Students should learn to distinguish exact keyed lookup from predicate search.

## WORKFLOW

Run SET ORDER TO TAG LNAME, then SEEK a known key with tracing. Compare with a scan or predicate-style query. Observe key comparison, early termination, and fallback behavior.

## MODEL

The model is access-path selection. Old xBase exposes SEEK and SCAN/LOCATE directly; modern SQL describes similar choices as index seek and index scan inside an execution plan.

## TAKEAWAY

All databases still make this decision. DotTalk++ can make the decision visible.
