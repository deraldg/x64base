# HELP Locale Workflow v1

Status: active workflow note
Scope: HELP DATA locale companion tables, CMDHELP locale preview direction, and source-authority fallback rules

## Purpose

This note defines the current locale workflow for the HELP family so maintainers can extend documentation language support without breaking source continuity.

It is intentionally narrower than full runtime multilingual shell reporting.

## Current operating model

The HELP family now has two distinct row classes:

1. canonical source-authority rows
2. locale companion rows

Canonical rows remain the authoritative English/source contract. Locale companion rows are attached translations or regionalized variants that must not silently replace the canonical layer until a later consumer explicitly asks for them.

## Canonical HELP tables

These remain the primary HELP DATA catalog:

- `HELP_TOPIC`
- `HELP_SECTION`
- `HELP_LINE`
- `HELP_ARTIFACTS`

These rows are the default `CMDHELP` read path and the current authority for normal operator-facing help.

## Locale companion HELP tables

These carry localized or region-specific overlays:

- `HELP_TOPIC_LOCALE`
- `HELP_SECTION_LOCALE`
- `HELP_LINE_LOCALE`
- `HELP_ARTIFACT_LOCALE`

These tables exist to extend the canonical catalog, not to replace it.

## Identity and fallback contract

The current readback/integration rule is:

1. resolve the canonical topic first
2. match locale companion rows by canonical identity plus `LOCALE_ID`
3. treat canonical/source English as the fallback authority

Practical rule:

- if a locale row is missing, draft, or not yet accepted, the system should continue to show canonical HELP text

## Current CMDHELP rule

Default behavior remains:

```text
CMDHELP <topic>
```

This must continue to return canonical/source HELP output.

Planned preview direction remains:

```text
CMDHELP <topic> PREVIEW LOCALE <locale>
```

or shorter:

```text
CMDHELP <topic> LOCALE <locale>
```

That preview path is the safe place to prove localized HELP rows before any later decision about default locale-driven display.

## SET LANGUAGE relationship

`SET LANGUAGE` is allowed to become the implicit locale selector later, but that is a later consumer decision.

Current policy:

- command keywords remain English
- canonical HELP remains source-authority English
- locale-aware HELP is previewable or attachable without changing command grammar

## Comments-evidence boundary

Source comment evidence remains English-focused by design.

That means:

- source headers
- usage contracts
- comments evidence tables

remain the canonical upstream feed for HELP continuity.

Locale work starts after canonical HELP identity exists. We do not translate the source evidence layer itself.

## Manual and metadata relationship

The HELP locale workflow is meant to fit the broader language/region spine now being established in metadata and manual/catalog lanes.

Shared policy:

- `LOCALE_ID` is the language key
- `REGION_ID` is the regional/cultural key
- source authority remains explicit
- translated layers remain companions, not replacements

This keeps HELP, manual/document catalogs, and future metadata promotion compatible with the same locale model.

## Maintenance sequence

When locale-aware HELP work is needed, use this order:

1. confirm canonical source contract and comments evidence
2. confirm canonical HELP DATA rows
3. populate or inspect locale companion rows
4. validate fallback behavior
5. only then wire or test locale preview consumers

Do not start by patching locale rows to hide missing canonical HELP rows.

## What is in force now

- HELP locale sidecar tables are real and should be preserved
- canonical/source HELP remains the default user-facing help path
- locale preview is the preferred future integration shape
- comments/source evidence stays English-only
- broader multilingual shell reporting can continue later without blocking HELP catalog preparation now

## Next gate

The next natural implementation gate is a controlled `CMDHELP` locale preview consumer that reads sidecar rows by `LOCALE_ID` while preserving canonical fallback.
