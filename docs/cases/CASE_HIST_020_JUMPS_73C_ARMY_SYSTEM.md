---
id: HIST-020
title: JUMPS / 73C Army System
type: historical_case
era: 1983-1985
level: student
lab: LAB_CASE_JUMPS_73C
domains: [batch-processing, structured-data, forms, finance, mainframe, workflow]
status: first_wave_review_candidate
review_status: needs_fact_review
evidence_class: lived_history_plus_reconstruction
runtime_visibility: hidden_until_reviewed
manual_visibility: draft_outline
source_docs: [Army_73C.docx, JUMPS in 1983 ran on IBM mainframes.docx]
media_assets: [MEDIA_CASE_JUMPS_BOARD_V1]
---

## SUMMARY

This case turns the 73C Army finance workflow into a teaching module about structured data, forms, validation, batch processing, rejects, correction loops, and human-in-the-middle systems. The core scenario is the PCS arrival workflow where entitlements and travel settlement feed into the same JUMPS batch cycle.

## PROBLEM

A soldier arrival created multiple structured obligations: update entitlements, process travel, encode records, assemble a batch, wait for mainframe results, read outputs, correct rejects, and run again. The challenge was not just clerical entry; it was structured reasoning under strict formats and delayed feedback.

## WORKFLOW

Start with DA Form 3685 and DD Form 1351-2 as schemas. Then walk the integrated pipeline: finance inprocessing, entitlement update, travel voucher, punch-card encoding, batch assembly, JUMPS run, LES/travel settlement/rejects, correction, and rerun. LabTalk can later simulate this with commands such as 3685.UPDATE, 1351.NEW, CARD.OUT, CARD.VERIFY, BATCH.ASSEMBLE, BATCH.RUN, OUTPUT.GET, REJECTS.LIST, and REJECTS.FIX.

## MODEL

The model is a batch system with typed records, fixed-field forms, validation rules, rate/date computation, delayed output, and human correction loops. This should be framed as a precursor to ETL, business-rule engines, validation pipelines, and batch-oriented enterprise processing. Hardware/language claims that are not independently confirmed must remain marked as reconstruction or inference.

## TAKEAWAY

The 73C case is one of the strongest bridges between lived workflow and database literacy. It shows that structured data is not abstract: it controls money, travel, exceptions, and real human outcomes.
