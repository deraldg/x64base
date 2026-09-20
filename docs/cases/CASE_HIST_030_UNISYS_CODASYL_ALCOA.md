---
id: HIST-030
title: Unisys / CODASYL at ALCOA
type: historical_case
era: 1970s-1980s
level: student
lab: LAB_CASE_CODASYL_SETS_RINGS
domains: [codasyl, network-database, sets, rings, industrial-data, relations]
status: first_wave_review_candidate
review_status: needs_source_review
evidence_class: lived_history_plus_source_docs
runtime_visibility: hidden_until_reviewed
manual_visibility: draft_outline
source_docs: [unisys.docx]
media_assets: [MEDIA_CASE_CODASYL_ALCOA_V1]
---

## SUMMARY

This case explains the network database model through the remembered Unisys / CODASYL vocabulary of sets and rings, then connects that older navigational mindset to DotTalk++ REL and REL ENUM.

## PROBLEM

Before SQL-style declarative querying became dominant, many systems required programmers to know the path through data. Relationships were not merely logical; they could also be access paths that had to be traversed procedurally.

## WORKFLOW

Teach SET as an owner/member relationship and RING as the physical chain of related members. Then show how a COBOL-style program might find an owner and walk members one by one. Finally compare the idea with DotTalk++ relation traversal, where REL defines the relationship and REL ENUM can enumerate related tuples without exposing physical pointer rings.

## MODEL

The conceptual model is navigational access. Old systems walked paths. Relational systems describe desired results. DotTalk++ can teach both: it can preserve the idea of relationship traversal while making the relationship inspectable and explainable.

## TAKEAWAY

This case gives students a vocabulary for why SQL was a major shift and why relation traversal still matters. It also prevents REL ENUM from looking like a random DotTalk++ feature; it becomes part of a historical lineage.
