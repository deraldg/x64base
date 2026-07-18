# Manualgen Topic Curation Contract v1

Status: active for candidate-only manual review packets.

## Purpose

Partition a provenance-bound HELP/META reference into smaller human-review
shelves without hand-editing the combined developer manual, replacing the
canonical harvest, or implying publication approval.

## Inputs

The curation run inherits the explicit `--publication-workspace` and
`--harvest-workspace` selectors. All 14 harvest files must pass the Manualgen
HELP/META Harvest Input Contract before curation begins.

`HELP_HELP_TOPIC.csv` owns the 631 topic identities. `HELP_HELP_LINE.csv` owns
the 12,784 rendered evidence lines. Curation changes neither file.

## Deterministic shelves

| Shelf | Rule | Default disposition |
| --- | --- | --- |
| `01_dot_supported_commands` | DOT and status `supported` | include command-reference candidate |
| `02_dot_command_review` | other DOT status | review before section curation |
| `03_fox_supported_commands` | FOX and status `supported` | include compatibility-reference candidate |
| `04_fox_command_review` | other FOX status | review before section curation |
| `05_education_concepts` | ED catalog | include education-appendix candidate |
| `06_supplemental_public_candidates` | EDU, EXT, or UI catalog | review public supplement |
| `07_developer_internal_topics` | DEV or INTERNAL catalog | exclude from public manual by default |
| `08_system_message_catalog` | SYSTEM topics and global SHARED_MSG lines | separate system-message appendix |
| `09_source_message_facts` | unscoped SOURCE_MINER message facts | separate source-fact appendix |

Anything outside these rules enters `99_unclassified` and fails the run.

## Required artifacts

Each run writes:

- one row per topic in `manual_topic_curation_ledger.csv`;
- one row per HELP line in `manual_line_curation_ledger.csv`;
- one human-view Markdown packet per populated shelf;
- a manifest containing input harvest hashes, packet hashes, counts, and
  publication boundary state.

## Acceptance checks

A curation candidate passes only when:

- all 631 topics occur exactly once in the topic ledger;
- all 12,784 lines occur exactly once in the line ledger;
- duplicate topic keys and line IDs are zero;
- unclassified topics and lines are zero;
- publication authority claimed is zero;
- canonical harvest replacement is zero.

## Current result

`MANRUN-20260717T225704Z-573F2F89` passes all checks across nine packets.
Supported public candidate shelves contain 238 DOT topics, 172 FOX topics, and
29 education concepts. The explicit review queue contains 22 DOT topics, four
FOX topics, and 23 supplemental topics. Five developer/internal topics are
excluded from public inclusion by default. System messages and source facts
remain separate appendices.

## Next authority gate

Human review may disposition the 49 review topics and select topic families for
section-factory candidates. It may not move accepted pointers, replace the
canonical harvest, merge generated packets into the combined manual, or
publish externally without separate authorization and comparison proof.
