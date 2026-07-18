# Tables, Records, and Data Model



Pippets used:
- PIP-004 Reviewed Candidate Pippet
- PIP-003 Evidence Review Pippet
- PIP-011 Source Reference Inventory Pippet

Evidence lineage:
- MDO-120 original draft
- MDO-128 source-lane repaired draft
- MDO-133 field-note drift repaired v4 draft
- MDO-134 evidence review gate

Repair reason:
- MDO-121 detected evidence/prose drift in the first Tables, Records, and Data Model draft.
- MDO-128 recovers or rebuilds the repair plan, then generates the source-lane repaired draft.

Evidence class:
- Repaired draft assembled from MDO-120 draft intent, MDO-121 evidence gate where available, source-lane crosswalk or recovered repair plan, and registry v4.
- Runtime behavior remains the source of truth.
- This draft does not mutate HELP, META, CMDHELPCHK, catalogs, source files, or production SelfDoc metadata.

## Purpose of this section

This section explains the table, record, field, schema, memo, and record-view vocabulary that later manual sections depend on. It follows the Getting Started and Workspaces sections: the reader should already know how the system starts, how areas frame context, and why the manual carries evidence boundaries.

The repaired draft is deliberately conservative. It does not assume every linked evidence page is the same kind of source. Some pages support current DotTalk command prose, some are educational concepts, some are compatibility references, and some need additional review before being described as runtime behavior.

## Source-lane rule for this section

A DOTREF/current evidence item may support command-facing prose after evidence review. An EDREF concept item explains vocabulary or teaching structure. A FOXREF compatibility item must be gated before being described as current runtime behavior. SQL or shell reference lanes should be routed to bridge or appendix material.

This rule prevents concept pages such as TABLE_RECORD_FIELD from being documented as if they were ordinary runtime commands, and prevents compatibility-only material from being promoted as current DotTalk behavior without proof.

## Tables, records, and fields

The core data model starts with tables, records, and fields. TABLE supports table-level vocabulary. RECORD and RECNO support record identity and record-position vocabulary. FIELDS and FIELDMGR support field-level vocabulary and field-management evidence.

TABLE_RECORD_FIELD is concept evidence for the relationship among tables, records, and fields. It should explain the model, not be presented as a user command unless a separate runtime command page proves that behavior.

## Schema and DDL

SCHEMA and DDL belong together in this section because they describe structure. SCHEMA supports table-structure vocabulary. DDL supports definition-level or schema-language vocabulary. This draft keeps DDL wording structural and avoids claiming specific DDL behavior until command evidence and runtime examples are reviewed.

## Record views and memo fields

RECORDVIEW supports record-oriented presentation or view vocabulary. MEMO supports memo-field discussion. Memo behavior is a sensitive storage and persistence topic, so final prose should distinguish visible memo fields from backend memo storage and should not overclaim persistence details without runtime evidence.

## Work areas as context, not the main topic

WORKAREA may appear in the evidence set, but the main explanation of work areas belongs in the already promoted Workspaces section. Here, WORKAREA should be used only to remind the reader that table and record commands operate in a current area/session context.

## Compatibility and bridge material

Compatibility evidence appears in this section and must be handled cautiously:

- DBAREAS: appears as compatibility evidence. Do not promote it as current DotTalk behavior without runtime proof.

Compatibility evidence can support historical or compatibility notes, but it should not be promoted as current DotTalk behavior without runtime proof.

## Command and concept map

- DBAREA [DOT_COMMAND_EVIDENCE / DOTREF]: is current/DotTalk reference evidence and may support command prose after evidence review.
- DBAREAS [COMPATIBILITY_EVIDENCE / FOXREF]: appears as compatibility evidence. Do not promote it as current DotTalk behavior without runtime proof.
- DDL [DOT_COMMAND_EVIDENCE / DOTREF]: describes schema-definition language or definition-level behavior. Treat it as structural doctrine, not a simple record command.
- FIELDMGR [DOT_COMMAND_EVIDENCE / DOTREF]: belongs to field-management evidence. Use it to discuss how field metadata and field-level operations are organized, not as ordinary user prose without review.
- FIELDS [DOT_COMMAND_EVIDENCE / DOTREF]: supports field-list and field-description discussion.
- MEMO [DOT_COMMAND_EVIDENCE / DOTREF]: supports memo/large-object field discussion. Keep memo storage details conservative unless command evidence or runtime transcripts prove more.
- RECNO [DOT_COMMAND_EVIDENCE / DOTREF]: supports record-position vocabulary.
- RECORD [DOT_COMMAND_EVIDENCE / DOTREF]: supports current-record or record-identity vocabulary.
- RECORDVIEW [DOT_COMMAND_EVIDENCE / DOTREF]: supports record-oriented presentation or viewing vocabulary.
- SCHEMA [DOT_COMMAND_EVIDENCE / DOTREF]: supports table-structure and schema vocabulary.
- TABLE [DOT_COMMAND_EVIDENCE / DOTREF]: supports table-level vocabulary.
- TABLE_RECORD_FIELD [CONCEPT_EVIDENCE / EDREF_CONCEPT]: is concept evidence for the relationship among tables, records, and fields. Do not treat it as a runtime command unless separately proven.
- WORKAREA [CONCEPT_EVIDENCE / EDREF_CONCEPT]: is concept or workspace-adjacent evidence. Mention only as context and keep detailed work-area behavior in the Workspaces section.

## What this section should not do yet

- Do not document unrelated commands from the first draft that are not in the linked evidence set.
- Do not treat EDREF concept pages as ordinary runtime commands.
- Do not treat FOXREF compatibility entries as current DotTalk behavior without runtime evidence.
- Do not add examples for mutating or destructive behavior until syntax and runtime transcripts are sampled.
- Do not move detailed workspace/session behavior out of the Workspaces section.

## Review notes before candidate generation

- Rerun PIP-003 evidence review on this repaired draft.
- Confirm the drift rows from MDO-121 are cleared or intentionally explained.
- Confirm the command/concept split is acceptable.
- Confirm MEMO wording does not overclaim backend persistence.
- Confirm DDL wording stays structural until examples are proven.

## Boundary

- repaired prose draft only
- no reviewed candidate generated
- no final prose promotion
- no generated command page deletion
- no HELP mutation
- no META mutation
- no CMDHELPCHK mutation
- no catalog apply
- no source edits
- no production SelfDoc metadata promotion
