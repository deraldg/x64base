# Diagram Metadata Lane

Page evidence  
Topic ID: DIAG.METADATA_PROMOTION  
Primary evidence: Design-intended  
Supporting evidence: Metadata-staged  
Review status: GREEN_TENTATIVE  
Safety boundary: REPORT_ONLY / NO_MUTATION  
Owner lane: SelfDoc  
Manual: Developer Manual  
Status: DRAFT  

## Purpose

The Diagram Metadata Lane is the proposed next SelfDoc layer for making diagrams provable, regenerable, classified, and auditable.

The goal is not merely to create attractive architecture diagrams. The goal is to let SelfDoc remember what entities exist, what relationships are proven, what relationships are deferred, what artifacts were generated, what run produced them, and what evidence supports each edge.

This page describes the v1 report-only design. It does not claim that diagram metadata DBFs have already been created or loaded.

## Safety Boundary

Diagram Metadata DBF Promotion v1 is report-only.

Allowed: stage CSVs, schema notes, expected-readback notes, ledgers, and gate reports.

Not allowed: source rewrites, HELP mutation, CMDHELPCHK mutation, catalog apply, existing metadata mutation, runtime data mutation, or DBF loading.

## Proposed v1 Metadata Tables

- DIAGRUN -- one row per diagram generation or check run.
- DIAGENTITY -- one row per diagram node/entity/table/subsystem/artifact.
- DIAGREL -- one row per diagram relationship or edge.
- DIAGART -- one row per generated artifact/report/output.

These are staged design targets until DBF creation, load, and readback are explicitly authorized and proven.

## Edge Styles

- SOLID: runtime-proven or report-proven relationship.
- DASHED: deferred relationship.
- DOTTED: tentative, rejected, unknown, or review-only relationship.

## Current Proven Spine

FILEID is the reliable v1 join spine.

Candidate solid edges:

- SRCFILE -> SRCBLOCK ON FILEID
- SRCFILE -> SRCLINE ON FILEID
- SRCFILE -> SRCUSAGE ON FILEID
- SRCFILE -> SRCCLASS ON FILEID
- SRCUSAGE -> SRCCLASS ON COMMAND

## MEMO_LINES Role

MEMO_LINES remains the v1 import-safe long-text staging strategy. It is separate from native memo. Native memo is not blocking diagram metadata promotion.

Publication state: Draft / Metadata-staged / Design-intended / GREEN_TENTATIVE.
