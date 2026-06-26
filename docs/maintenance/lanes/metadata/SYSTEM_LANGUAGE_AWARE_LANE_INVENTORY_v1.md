# System Language-Aware Lane Inventory v1

Status: active continuity inventory  
Scope: HELP, messaging, locale spine, metadata, manual/publication, comments, and command-family consumers such as `CMDHELP`, `DDICT`, `BBOX`, and `MAINT`

## Purpose

Capture where language/locale support is already structural, where it is still
policy-only, and which command families should consume localized text rather
than owning separate translation tables.

This is the practical inventory for the next GitHub snapshot.

## Bottom line

The current system is not language-blind anymore, but the support is uneven.

- locale spine: structurally real
- messaging: structurally real
- HELP locale sidecars: structurally real
- metadata family: policy is real, active row design is still incomplete
- manual/publication family: policy is real, active row design is still incomplete
- comments/source evidence: should remain English/source-authority for now

## Shared contract already in force

Authoritative policy remains:

- [SYSTEM_LANGUAGE_REGION_SCHEMA_POLICY_v1.md](/D:/code/ccode/docs/maintenance/lanes/metadata/SYSTEM_LANGUAGE_REGION_SCHEMA_POLICY_v1.md)
- [HELP_LOCALE_WORKFLOW_v1.md](/D:/code/ccode/docs/maintenance/lanes/help/HELP_LOCALE_WORKFLOW_v1.md)
- [METADATA_HELP_MESSAGE_MANUAL_PROMOTION_MODEL_v1.md](/D:/code/ccode/docs/maintenance/lanes/metadata/METADATA_HELP_MESSAGE_MANUAL_PROMOTION_MODEL_v1.md)

Shared rule:

- canonical identities remain stable and English-first
- localized human text attaches through companion rows keyed by `LOCALE_ID`
- `REGION_ID` is recognized structurally now even if culture formatting policy remains deferred

## Lane inventory

### 1. Locale spine

Active structural artifact:

- [locale_spine.dtschema](/D:/code/ccode/dottalkpp/data/schemas/locale/locale_spine.dtschema)

Current posture:

- `SYSTEM_LOCALES` is the stable locale registry
- `SYSTEM_LOCALE_FALLBACK` is the explicit fallback chain
- this lane is already in the correct architectural position

Assessment:

- structurally language-aware now
- no redesign needed before the next snapshot

### 2. Messaging

Active structural artifact:

- [message_catalog.dtschema](/D:/code/ccode/dottalkpp/data/schemas/messaging/message_catalog.dtschema)

Current posture:

- locale-bearing message text rows are already modeled
- runtime `SET LANGUAGE` / `SET LOCALE` seams already exist
- command surfaces are being migrated from hard-coded `cout` toward message-aware reporting

Assessment:

- structurally language-aware now
- still needs denser seeding and broader command adoption

### 3. HELP family

Active workspace artifact:

- [help.dtschemas](/D:/code/ccode/dottalkpp/data/workspaces/help.dtschemas)

Current canonical tables:

- `HELP_TOPIC`
- `HELP_SECTION`
- `HELP_LINE`
- `HELP_ARTIFACTS`

Current locale sidecars:

- `HELP_TOPIC_LOCALE`
- `HELP_SECTION_LOCALE`
- `HELP_LINE_LOCALE`
- `HELP_ARTIFACT_LOCALE`

Current consumer state:

- `CMDHELP <topic> LOCALE <locale>` is now an explicit preview surface only
- canonical `CMDHELP <topic>` remains the enforced default
- missing or blocked locale rows fall back to canonical HELP text

Current watchpoint:

- the active `HELP_LINE_LOCALE` memo payload lane is damaged in runtime data
- runtime proof showed `150` memo refs and `150` missing refs
- that is a data-seeding/runtime-content defect, not a schema defect

Assessment:

- structurally language-aware now
- needs locale-sidecar rebuild/reseed, not schema repair

### 4. Metadata family

Active lane doctrine:

- [METADATA_FAMILY_SYSTEM_GUIDE_v1.md](/D:/code/ccode/docs/maintenance/lanes/metadata/METADATA_FAMILY_SYSTEM_GUIDE_v1.md)
- [METADATA_HELP_MESSAGE_MANUAL_PROMOTION_MODEL_v1.md](/D:/code/ccode/docs/maintenance/lanes/metadata/METADATA_HELP_MESSAGE_MANUAL_PROMOTION_MODEL_v1.md)

Active script evidence:

- [SYSCMD_NATIVE_CREATE_IMPORT_v1.RUN_REVIEWED.dts](/D:/code/ccode/dottalkpp/data/scripts/metadata/SYSCMD_NATIVE_CREATE_IMPORT_v1.RUN_REVIEWED.dts)
- [SYSCMD_READBACK_v1.dts](/D:/code/ccode/dottalkpp/data/scripts/metadata/SYSCMD_READBACK_v1.dts)

Current posture:

- metadata command/function/help identity lanes are real
- locale/region policy is explicitly documented
- current script surfaces do not yet show promoted locale-bearing metadata companions

Assessment:

- policy-ready
- not fully schema-promoted for locale-aware text yet

Needed next rule:

- canonical metadata identity tables may carry `DEFAULT_LOCALE` and `SOURCE_LOCALE`
- future metadata text-bearing companions should carry:
  - `LOCALE_ID`
  - `SOURCE_LOCALE`
  - `REGION_ID`
  - `SOURCE_HASH`
  - `LOCALIZED_HASH`
  - `TRANSL_STATUS`
  - `REVIEW_STATUS`
  - `FALLBACK_ALLOWED`

### 5. Manual / publication family

Current evidence:

- manual lane doctrine exists
- live script inventory is still thin in the staged tree
- the only current manual script under `dottalkpp/data/scripts/manual` is a demo browser script, not the publication schema owner

Current posture:

- manual/publication identity is conceptually correct
- locale-aware publication companions are policy-defined
- active promoted manual locale tables are not yet visible as live schema artifacts in this tree

Assessment:

- policy-ready
- not yet structurally promoted in the staged data/scripts tree

### 6. Comments / source evidence family

Active script home:

- [README.md](/D:/code/ccode/dottalkpp/data/scripts/comments/README.md)
- [SOURCE_COMMENT_SCHEMA_CREATE.dts](/D:/code/ccode/dottalkpp/data/scripts/comments/SOURCE_COMMENT_SCHEMA_CREATE.dts)

Current posture:

- comments preserve source evidence
- headers/contracts/comments are the English/source-authority lane
- the current schema intentionally does not carry localization companions

Assessment:

- should stay English-first for now
- optional later addition: `SOURCE_LOCALE` marker only
- should not become a translated publication surface

## Command-family consumer rule

`CMDHELP`, `DDICT`, `BBOX`, `MAINT`, and similar command families should be
treated as language consumers, not translation-table owners.

That means:

- their command help belongs in canonical HELP plus HELP locale sidecars
- their runtime user-facing status/warning/error text should migrate through messaging
- their stable command identities remain canonical and English-first in metadata/help evidence

They do **not** each need a private locale table family.

## What is already safe to say in the next snapshot

1. The system already has a real shared locale spine.
2. Messaging is the first real runtime language consumer.
3. HELP already uses the correct canonical-plus-locale-companion model.
4. Metadata and manual lanes have the correct doctrine, but their locale-aware table promotion is still incomplete.
5. Comments are intentionally English/source-authority and should remain that way for now.

## Recommended next steps

1. Keep replacing hard-coded command text with message-aware seams.
2. Rebuild or reseed the broken HELP locale memo sidecar payloads.
3. Promote locale-aware metadata text companions before broad manualgen expansion.
4. Promote manual/publication locale companions only after metadata/help joins stay stable.
5. Keep `DDICT`, `BBOX`, `MAINT`, and related command families as consumers of HELP plus messaging, not independent localization silos.
