# Manualgen Structural Reconciliation Contract v1

Status: active for the post-disposition manual section comparison.

## Purpose

Map every approved section-factory topic onto the governed Developer Manual
topology without confusing an evidence refresh with authority to replace prose,
promote a supporting workspace, or change the primary reader pointer.

## Baseline topology

The manual currently has three related structural views:

- the primary reader body has 24 common-core sections;
- the media revision has 25 sections: the common core plus the
  media/storyboard teaching layer;
- the controlled runtime/MAN-CLI comparison body has 25 sections: the common
  core plus Runtime Operation, Invocation, and Automation.

Their union contains 26 governed section surfaces. The three accepted review
appendices are inventoried separately because appendix presence is evidence of
prior curation, not normal-section placement.

## Mapping order

Each approved topic is assigned by the first applicable rule:

1. partial HELP topics enter only the candidate partial-HELP appendix;
2. the explicit 13-topic structural review policy applies its evidence-backed
   target and rationale;
3. FOX topics stay inside the legacy/compatibility boundary;
4. ED, EDU, and EXT topics enter education/demo curation;
5. UI topics enter command-surface curation;
6. exact existing section command assignments are retained;
7. named family rules propose a section with medium confidence;
8. existing review-appendix topics return to explicit recuration;
9. remaining topics enter a visible command-reference review fallback.

No rule authorizes section replacement. Every mapping retains its basis,
confidence, prior section assignments, and prior appendix assignments.

## Current proof

Run `MANRUN-20260717T233746Z-BD33A215` reports:

- primary sections: 24;
- media-revision sections: 25;
- controlled-runtime sections: 25;
- union section surfaces: 26;
- primary review appendices: 3;
- approved topics mapped: 462/462;
- topics named in existing section command lists: 284;
- topics also named in existing review appendices: 52;
- explicit structural review dispositions: 13/13;
- remaining review-confidence topics: 0;
- remaining unplaced fallbacks: 0;
- duplicate topic keys: 0;
- missing structural targets: 0;
- status: `PASS`.

## Outputs

The run emits:

- a 26-row structural baseline ledger;
- a 462-row topic structural mapping;
- a per-section delta ledger;
- a human-readable structural delta proposal;
- a hash-bearing reconciliation manifest.

## Boundary

All outputs are candidate-only. The run does not mutate section sources,
combined manuals, accepted MAN catalogs, the canonical harvest, runtime HELP or
metadata, the primary reader pointer, websites, or external publication.

Per-section packet generation is completed under
`MANUALGEN_SECTION_DELTA_DRAFT_CONTRACT_V1.md`. That packetization gate now
passes, and `MANUALGEN_PROSE_REVIEW_BATCH_CONTRACT_V1.md` governs risk-ordered
human prose review beginning with the three smallest packets.
Selective merge, wholesale replacement, and publication remain separately
gated.
