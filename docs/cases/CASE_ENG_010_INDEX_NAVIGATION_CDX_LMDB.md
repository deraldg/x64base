---
id: ENG-010
title: Indexed Navigation: CDX / LMDB
type: engine_case
era: 1985-present
level: student
lab: LAB_CASE_INDEX_NAVIGATION
domains: [xbase, indexes, cdx, lmdb, logical-order]
status: runtime_lab_candidate
review_status: needs_runtime_proof_attachment
evidence_class: source_doc_plus_project_status
runtime_visibility: hidden_until_reviewed
manual_visibility: draft_outline
source_docs: [Case Studies Core Track.docx]
media_assets: []
runtime_proof: [runtime_proofs/ENG-010_RUNTIME_PROOF.md]
---

## SUMMARY

This runtime case demonstrates that logical order is not the same thing as physical record order. It uses FoxPro-style index navigation, CDX tags, and the LMDB-backed index environment as the teaching bridge.

## PROBLEM

Sequential scans are easy to understand but slow and limited. Students need to see why indexes are navigation structures, not only lookup accelerators.

## WORKFLOW

Run USE STUDENTS, SET INDEX TO STUDENTS, SET ORDER TO TAG LNAME, SMARTLIST, TOP, and SKIP. Observe the difference between physical recno and logical order.

## MODEL

The model is record storage plus an order/index layer. CDX is the user-facing logical container. LMDB is backend implementation detail. DotTalk++ should expose the order concept without leaking backend terminology into ordinary teaching prose.

## TAKEAWAY

Indexes are navigation systems. SQL often hides this behind ORDER BY and optimizer choices; DotTalk++ can show it directly.
