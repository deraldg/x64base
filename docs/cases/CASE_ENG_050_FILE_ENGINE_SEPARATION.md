---
id: ENG-050
title: File-Based DB to Engine-Based DB
type: engine_case
era: 1980s-present
level: student
lab: LAB_CASE_FILE_ENGINE_SEPARATION
domains: [dbf, xdbf, cdx, lmdb, storage-abstraction]
status: runtime_lab_candidate
review_status: needs_runtime_proof_attachment
evidence_class: source_doc_plus_project_status
runtime_visibility: hidden_until_reviewed
manual_visibility: draft_outline
source_docs: [Case Studies Core Track.docx]
media_assets: []
runtime_proof: [runtime_proofs/ENG-050_RUNTIME_PROOF.md]
---

## SUMMARY

This runtime case explains how database systems separate table storage, indexing, execution, and projection.

## PROBLEM

Flat files are understandable but do not fully explain modern database behavior. Students need to see how file format, index abstraction, and backend engine responsibilities differ.

## WORKFLOW

Run STATUS and AREA, inspect open work areas and paths, then compare DBF/XDBF table data, CDX logical index containers, and backend index environment paths. Use this case carefully so backend details teach architecture rather than confuse beginners.

## MODEL

The model separates raw table storage from logical indexing and physical backend implementation. DbArea owns records and mutation; CDX owns user-facing logical tags; LMDB remains physical backend; projection commands render views of the same underlying data.

## TAKEAWAY

Modern databases separate storage, indexing, execution, and projection. DotTalk++ makes that separation visible enough to teach.
