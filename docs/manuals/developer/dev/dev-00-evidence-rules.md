# DEV-00 Evidence Rules

```yaml
page_id: DEV-00
title: Evidence Rules
status: DRAFT_PATCHED
last_verified: 2026-07-07
evidence_classes: [HELP, METADATA, SOURCE, PROVEN, CANARY, PLANNED]
```

## Purpose

The Developer Manual is a controlled publication layer over SelfDoc evidence,
source verification, runtime proof, and manual review.

## Governing doctrine

```text
HELP explains broadly.
META organizes semantically.
CMDHELPCHK validates reflected structure.
Source verifies ownership.
Runtime proves behavior.
SelfDoc preserves provenance.
The Master Document Organizer assembles the manuals.
The website is an attached publication lane, not an authority by default.
```

## Practical pipeline

```text
HELP/META/CMDHELPCHK evidence first
source verification second
runtime proof final for behavior
manual prose last
website prose is harvested only where it is explicitly outside the documented inventory
```

## Evidence precedence

1. Runtime proof for exact behavior.
2. HELP `USAGE_CONTRACT` rows, `CONFID=AUTHORITATIVE`.
3. HELP `CURATED_DOC` rows, `CONFID=CURATED`.
4. HELP `REGISTRY` rows, `CONFID=REFLECTED`, for status only.
5. CMDHELPCHK reflection reports.
6. META active semantic seed rows.
7. Source implementation/prototype inventory.
8. SOURCE_MINER inferred rows, review required.
9. Historical documents.
10. Website prose and presentation copy, unless explicitly elevated by review.

Important nuance: META is not lower quality than HELP; it is currently narrower
in the observed seed.

## Manual and website source policy

The manual and the website should draw from the same project evidence spine:

- source/runtime contracts
- HELP
- metadata
- CMDHELPCHK
- SelfDoc provenance
- reviewed canaries

The manual does not treat the website as an authority just because the website
happens to be newer or more polished.

Working rule:

- if a fact belongs to documented runtime/source inventory, harvest it from the
  project lanes directly
- if a website section is presentation-only and explicitly outside the
  documented inventory, that prose may be harvested into the manual after review
- do not copy implementation facts from the website back into the manual when
  the project lanes already own those facts

## Review statuses

`ACCEPT`, `PUBLIC_READY`, `DEVELOPER_ONLY`, `INTERNAL`, `SCAFFOLD`, `REVIEW`, `CONFLICT`, `GAP`, `CANARY`, `BLOCKED`, `HISTORICAL`, `SUPERSEDED`.

## Standing canary rules

- HELP breadth is not behavior proof.
- META absence is not project absence.
- SOURCE_MINER inference is not public documentation.
- Runtime proof is path-specific.
- Canaries remain visible until closed with evidence.

## Working rule

```text
Read HELP broadly.
Read META semantically.
Validate with CMDHELPCHK.
Verify with source.
Prove with runtime.
Assemble with manuals.
Publish to website as an attached view.
```
