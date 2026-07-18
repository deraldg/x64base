<!-- MDO-116: promoted from reviewed candidate into manual draft workspace v3. -->
<!-- Decision: MDO-115 ACCEPT_FOR_PROMOTION; gate READY_FOR_HUMAN_PROMOTION_REVIEW. -->
<!-- Pipeline ledger: generated/pipeline_docs_v1/MANUALGEN_PIPELINE_LEDGER_v1.md remains supporting draft evidence. -->

# HELP, Metadata, and SelfDoc

<!-- HISTORICAL STATUS: PROMOTED_TO_MANUAL_DRAFT / REVIEW_REQUIRED -->
Status: REVIEWED_FOR_PUBLICATION

Evidence class:
- Reviewed prose candidate assembled from MDO-112 draft prose and MDO-113 evidence review.
- Runtime behavior remains the source of truth.
- This candidate is not final manual prose.
- This candidate does not mutate HELP, META, CMDHELPCHK, catalogs, source files, or production SelfDoc metadata.

Promotion gate:
- READY_FOR_HUMAN_PROMOTION_REVIEW

## Overview

This section explains the evidence system behind the Developer Manual. DotTalk++ documentation is not meant to be a free-written description detached from the running program. It is assembled from runtime behavior, source contracts, HELP output, metadata rows, validation reports, command-reference pages, review gates, and human decisions.

The working doctrine is: runtime proves, source defines, HELP explains, metadata organizes, CMDHELPCHK validates, SelfDoc preserves provenance, and manualgen assembles human-facing manuals from evidence.

## Why this matters

The manual is part of the system, not just an after-the-fact book. Each generated section should have a trail showing where its claims came from, what was checked, what was deferred, and what was not mutated.

This keeps the manuals aligned with the project instead of letting them drift into a separate version of reality.

## HELP explains the command surface

HELP is the user-facing explanation layer. It exposes command syntax, usage, examples, notes, and related material. The manual can draw from HELP, but it should not silently replace HELP or invent behavior beyond the command evidence.

CMDHELP belongs to the command-help maintenance path. CMDHELPCHK belongs to the validation path. In this manual lane, CMDHELPCHK is especially important because it helps check whether generated HELP and artifact rows are structured well enough to be used downstream.

A successful HELP or CMDHELPCHK-related step is evidence. It is not, by itself, final publication.

## Metadata organizes evidence

Metadata gives the project structured rows that can be inspected, compared, exported, reconciled, and reviewed. It helps organize command facts, field facts, HELP facts, and documentation facts.

METADATA and TABLEMETA belong in this section as command surfaces for metadata-related inspection or reporting. The manual should keep their claims conservative until each command page and runtime behavior are reviewed.

The important distinction is that metadata organizes evidence. Metadata alone does not prove runtime behavior.

## SelfDoc preserves provenance

SelfDoc is the provenance-preserving role in this documentation system. It keeps source comments, usage contracts, HELP artifacts, metadata rows, generated pages, reports, canaries, manual drafts, and save points connected to the evidence trail.

This is why the MDO process repeatedly records boundaries. Those boundaries state whether a step generated draft evidence, reviewed a gate, promoted a draft workspace, or mutated nothing. They are not decoration. They are the safety rails that keep documentation work reversible and auditable.

## Manualgen assembles, reviews, and gates

Manualgen is the assembly lane. It starts from harvested HELP and metadata evidence, builds command-reference material, organizes that material into a TOC and skeleton, drafts prose, reviews evidence, creates reviewed candidates, records human decisions, and promotes accepted sections into versioned manual draft workspaces.

The current proven manualgen path is documented in the Manualgen Pipeline Ledger. The pipeline includes harvest, reconcile, assemble, normalize, structure, draft, review, candidate, decision, promote, and record phases.

The ledger itself is a project artifact. It should be updated when a repeatable phase, repair pattern, or promotion gate is proven.

## Command map

- CMDARGCHK: supports command argument checking or review in the documentation/validation lane.
- CMDHELP: supports command-help generation, maintenance, or inspection.
- CMDHELPCHK: validates HELP and command-help artifact consistency.
- METADATA: exposes metadata-related inspection or reporting surfaces.
- TABLEMETA: exposes table-metadata inspection or reporting surfaces.

## Workflow map

- Harvest: collect HELP and META inputs without mutating them.
- Reconcile: compare harvested rows and create review queues.
- Assemble: generate command-reference draft pages.
- Normalize: handle aliases, collisions, symbol commands, and deferred families.
- Structure: build TOC and skeleton files.
- Draft: write section prose from evidence.
- Review: check command pages and generate a promotion gate.
- Candidate: tighten prose without final promotion.
- Decision: capture human acceptance, revision, hold, or rejection.
- Promote: copy accepted prose into a versioned manual draft workspace.
- Record: update save points and pipeline ledgers.

## Review notes before promotion

- Confirm all five command pages before promotion.
- Keep HELP, metadata, CMDHELPCHK, SelfDoc, and manualgen roles distinct.
- Do not imply that metadata alone proves behavior.
- Do not imply that reviewed candidate status is final publication.
- Keep the pipeline ledger as draft evidence until it is reviewed and accepted.
- Preserve known canaries and deferred issues, including SET-family canonicalization and LOAD scoping.

## Boundary

- promoted to manual draft workspace, still review required
- not final published manual prose
- no generated command page deletion
- no HELP mutation
- no META mutation
- no CMDHELPCHK mutation
- no catalog apply
- no production SelfDoc metadata promotion
