---
id: ENG-040
title: Metadata and Data Dictionary
type: engine_case
era: 1980s-present
level: student
lab: LAB_CASE_METADATA_DICTIONARY
domains: [metadata, catalog, help, commands, functions, data-dictionary]
status: runtime_lab_candidate
review_status: needs_runtime_proof_attachment
evidence_class: source_doc_plus_project_status
runtime_visibility: hidden_until_reviewed
manual_visibility: draft_outline
source_docs: [Case Studies Core Track.docx]
media_assets: []
runtime_proof: [runtime_proofs/ENG-040_RUNTIME_PROOF.md]
---

## SUMMARY

This runtime case explains the project pivot from hardcoded documentation toward catalog-backed metadata.

## PROBLEM

Commands, functions, help text, usage contracts, source comments, and system messages can drift unless they are cataloged and validated. Sidecars are fragile if they cannot be regenerated or checked.

## WORKFLOW

Use HELP and catalog/report commands to show how command/function metadata can be harvested, compared, validated, and eventually repaired. Keep the lab report-only until mutation is explicitly authorized.

## MODEL

The model is metadata-backed documentation: source defines, runtime proves, HELP explains, metadata organizes, CMDHELPCHK validates, and SelfDoc preserves provenance.

## TAKEAWAY

A serious teaching system needs a data dictionary for its own behavior, not only for user tables.
