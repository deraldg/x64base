# System Language and Region Schema Policy v1

Status: active schema policy
Scope: shared locale spine, metadata, HELP, manuals, publication, future dictionary/selfdoc consumers

## Purpose

This note sets the schema rule for language and region awareness across the
DotTalk++ family before more HELP/manual work continues.

The goal is narrow:

- keep English as the canonical source language for now
- make locale and region recognition explicit in schemas now
- avoid a later backtrack where HELP/manual/metadata need structural repair

This is not a full translation package.

## Core rule

Use one shared locale contract across the system.

- stable identities are not translated
- rendered human text is localized
- locale fallback is explicit and testable
- region/culture is recognized structurally now, even if formatting policy is deferred

## Shared spine

The shared locale spine remains:

- `SYSTEM_LOCALES`
- `SYSTEM_LOCALE_FALLBACK`

All consumers should recognize locale through `LOCALE_ID`.

## Field naming policy

### Canonical identity rows

Use these when a table owns stable identity or source-language authority:

- `DEFAULT_LOC` or `DEFAULT_LOCALE`: default display/source locale, normally `en-US`
- `SOURCE_LOC` or `SOURCE_LOCALE`: source-language authority locale, normally `en-US`
- `REGION_ID`: optional regional scope or later culture key

Canonical identity rows may still carry English source text.

### Localized companion rows

Use these when a table stores localized human-facing text or localized artifact labels:

- `LOCALE_ID`
- `SOURCE_LOCALE`
- `REGION_ID`
- `TEXT_DIR`
- `SOURCE_HASH`
- `LOCAL_HASH` or `LOCALIZED_HASH`
- `TRANSL_STATUS`
- `REVIEW_STATUS`
- `FALLBACK_ALLOWED`

These rows attach to stable canonical identities. They do not replace them.

## Family rules

### Messaging

Messaging is already the first real runtime consumer.

- `SYSTEM_MESSAGES` owns stable message identity
- `SYSTEM_MESSAGE_TEXT` owns localized text
- canonical/source locale remains English-first

### HELP

HELP should keep canonical identity rows and locale companion rows.

- canonical: `HELP_TOPIC`, `HELP_SECTION`, `HELP_LINE`, `HELP_ARTIFACTS`
- localized companions: `*_LOCALE`

Locale-aware HELP rows must key by canonical identity plus `LOCALE_ID`.

### Metadata

Metadata remains broader than HELP and should recognize language explicitly.

- stable command/function/message identities stay canonical and English-first
- metadata help/message text surfaces should declare default/source locale now
- text-bearing metadata rows should be structurally ready for locale-aware promotion

Metadata is not the runtime translation engine, but it must not be language-blind.

### Manual / publication

Manualgen should follow the canonical-plus-companion pattern.

- canonical: `MANSECTION`, `MANPUB`, related stable publication/media identities
- localized companions: `MANSECTION_TXT`, `MANPUB_TXT`, later similar companions where justified

This keeps publication identity stable while allowing translated editions later.

### Comments / source evidence

Source comments remain English/source-authority evidence.

- comments do not need full translation support now
- comments may carry source-locale markers later if useful
- comments should not become the translated publication surface

## English-first rule

For this phase:

- English remains the authoritative source language
- new locale-aware fields may default to `en-US`
- translation rows may be seeded later
- schema readiness comes before broad content mutation

## Region posture

`REGION_ID` is recognized now as a structural field.

This does not authorize a full culture/formatting subsystem yet.

Near term, `REGION_ID` means:

- a declared scope key for future culture rules
- a way to distinguish language from regional variation
- a way to avoid future schema churn

## Practical consequence

Before HELP/manual expansion continues:

1. metadata schemas should declare locale/region awareness
2. manual/publication schemas should declare locale/region awareness
3. existing HELP locale companion doctrine remains valid
4. translation seeding can remain deferred

## Bottom line

The whole system should recognize language and region structurally now.

English remains canonical for this phase, but locale/region blindness should not
remain in metadata, HELP-adjacent text lanes, or manual/publication schemas.
