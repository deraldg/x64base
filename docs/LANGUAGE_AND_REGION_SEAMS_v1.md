# LANGUAGE_AND_REGION_SEAMS_v1

Status: DRAFT
Project root: `D:\code\ccode`

## Purpose

This document defines how language and region support should fit into the
DotTalk++ / x64base family.

It does not require full multilingual runtime coverage today. It defines the
seams that must exist now so the system can grow without schema backtracking.

This policy applies across:

- runtime shell messaging
- metadata lanes
- HELP lanes
- SelfDoc and manual promotion
- diagram promotion

## Core rule

Canonical identity must be stable and locale-neutral.

Localized text must be layered on top of canonical identity, not embedded into
it.

In practice:

- IDs stay stable
- display text may vary by locale
- region may affect selection and presentation
- English can remain the default seed while the schema supports more

## Current doctrine

Language support is a system-wide seam, not just a messaging feature.

That means:

1. runtime messages may localize
2. help content may localize
3. metadata rows must carry locale/region seams
4. manuals may be promoted in multiple languages
5. diagrams should attach locale-specific labels without changing entity IDs

## Required canonical fields

The minimum cross-family seam fields are:

- `DEF_LOCALE`
- `REGION_ID`

Current default values:

- `DEF_LOCALE = en-US`
- `REGION_ID = GLOBAL`

These fields should be treated as baseline canonical seam fields, not optional
afterthoughts.

## What must stay locale-neutral

The following should remain canonical and stable across languages:

- command IDs
- function IDs
- argument IDs
- message IDs
- topic IDs
- section IDs
- diagram/entity IDs
- runtime/internal symbols

Examples:

- `CMD_ID`
- `FUNC_ID`
- `ARG_ID`
- `MSG_ID`
- `TOPIC_ID`

The localized layer should change wording, not identity.

## Runtime shell messaging

### Current state

The current shell already has a real language seam in the message layer.

Evidence:

- [message_catalog.hpp](D:/code/ccode/src/cli/message_catalog.hpp)
- [message_catalog.cpp](D:/code/ccode/src/cli/message_catalog.cpp)

Current characteristics:

- message codes are canonical
- text can be resolved by locale
- current built-in examples exist for:
  - `en-US`
  - `it`
  - `es`
  - `fr`
  - `de`
- unresolved lookups fall back to English

Current rule:

- new user-facing shell text should prefer message-aware routing when practical
- hard-coded `cout` may remain temporarily, but should be treated as migration
  debt for user-facing surfaces

### What belongs in the message layer

Good candidates:

- unknown command
- missing argument
- invalid syntax
- not found
- no active index
- no active table
- parser diagnostics
- navigation/search warnings
- relation warnings
- import/export user-facing errors

### What may remain outside initially

- deep developer-only diagnostics
- source comments
- experimental/beta-only emission surfaces

## Locale spine

There is already a scaffolded locale spine lane.

Evidence:

- [locale_spine_catalog.hpp](D:/code/ccode/src/help/locale_spine_catalog.hpp)
- [locale_spine_catalog.cpp](D:/code/ccode/src/help/locale_spine_catalog.cpp)

Current documented shape:

- DBF root: `dottalkpp/data/locale`
- indexes root: `dottalkpp/data/indexes/locale`
- LMDB root: `dottalkpp/data/lmdb/locale`
- fallback chain supports:
  - requested locale
  - `en-US`
  - `GLOBAL`

Current policy:

- locale spine stays shared infrastructure
- lane-specific localized text may attach to it
- locale fallback should remain explicit and deterministic

## Metadata lane requirements

### Current state

`metacollect` already emits locale and region seam fields in canonical export
artifacts.

Evidence:

- [metacollect.hpp](D:/code/ccode/include/dt/meta/metacollect.hpp)
- [metacollect.cpp](D:/code/ccode/src/meta/metacollect.cpp)
- [SYSFUNC_IMPORT_v1.csv](D:/code/ccode/dottalkpp/data/scripts/metadata/SYSFUNC_IMPORT_v1.csv)
- [SYSARGS_IMPORT_v1.csv](D:/code/ccode/dottalkpp/data/scripts/metadata/SYSARGS_IMPORT_v1.csv)

Current behavior includes:

- `DEF_LOCALE`
- `REGION_ID`
- default canonical export seeded with `en-US` / `GLOBAL`

### Policy

All new canonical metadata families that feed user-facing publication should
carry locale/region seams if localized text is plausible later.

This applies to:

- `SYSCMD`
- `SYSFUNC`
- `SYSARGS`
- `SYSHELP`
- `SYSMSG`
- related future catalog families

### Important distinction

Metadata does not need to store every localized phrase immediately.

It does need:

- canonical IDs
- locale seam fields
- region seam fields
- a place where localized display text can attach later

## Message metadata

### Current state

The message lane has two kinds of evidence:

1. compact metadata feeder direction through `SYSMSG`
2. longer-form message catalog evidence through `SYSTEM_MESSAGES`

Current documented caution:

- `SYSMSG` and `SYSTEM_MESSAGES` must not be casually collapsed without a
  crosswalk

### Policy

Use this distinction:

- `SYSMSG`
  - canonical compact metadata feeder for message identity and typed message
    organization
- `SYSTEM_MESSAGES`
  - longer-form message catalog data and runtime/catalog evidence

Localized text belongs to message content rows, keyed by canonical identity and
locale.

## HELP lane requirements

### Policy

The HELP lane needs two different language behaviors:

1. canonical/source HELP
2. locale preview or localized HELP overlays

Canonical/source HELP remains the default truth-preserving user-facing help.

Localized HELP should be layered as:

- explicit preview
- explicit localized row selection
- fallback to canonical/source HELP where localized rows are missing

### Current evidence

`CMDHELP` already carries explicit locale-preview language in its contract and
implementation notes.

Examples:

- `CMDHELP <topic> PREVIEW LOCALE <locale>`
- `CMDHELP <topic> LOCALE <locale>`

Current policy:

- plain `CMDHELP` remains canonical/source HELP
- locale preview remains explicit-only unless separately authorized for broader
  runtime behavior

## Manual promotion requirements

Manuals should be promotable in multiple languages, but they do not need full
live multilingual generation today.

Required seams now:

- canonical section IDs
- canonical topic and artifact references
- locale-aware publication plan

Policy:

- manuals may attach translated prose later
- manuals should cite canonical metadata/help identities now
- manual section structure should not depend on English wording as identity

## Diagram promotion requirements

Diagrams must separate identity from label.

Policy:

- node IDs, edge IDs, and entity IDs remain canonical
- visible labels may vary by locale
- diagram generation should prefer metadata-backed IDs and localized label maps

Good example:

- canonical entity: `SYSFUNC`
- localized label:
  - English: `System Functions`
  - Spanish: `Funciones del sistema`

The entity does not change; only the label does.

## Source comments

Source comments may remain English-only.

Reason:

- they are part of source maintenance and developer collection
- they are not the primary end-user localization surface

Policy:

- do not block source comment collection waiting for multilingual support
- do preserve canonical structure so comments can matriculate upward into
  metadata/help/manual layers later

## Fallback policy

Current family-wide fallback policy should be:

1. requested locale if available
2. canonical English default (`en-US`)
3. global/general fallback (`GLOBAL`) where applicable

This fallback rule should stay consistent across:

- message lookups
- help preview
- metadata export defaults
- future manual/diagram labeling

## Migration rule for hard-coded output

Not every `cout` must be replaced at once.

Use this triage:

### Replace first

- repeated user-facing errors
- repeated warnings
- command usage/invalid-form responses
- searchable/status-like shell messages

### Replace later

- deep dev diagnostics
- one-off temporary probes
- transient experiment lanes

### Preserve as English-only for now

- source comments
- internal repair notes
- experimental non-user-facing traces

## Operator guidance

When adding or changing a user-facing command surface:

1. keep canonical IDs stable
2. route repeated shell text through the message layer if practical
3. ensure metadata can carry `DEF_LOCALE` and `REGION_ID`
4. keep HELP canonical by default
5. use explicit locale preview or explicit locale routing for non-default text

When creating a new metadata family:

1. decide the canonical identity fields
2. add locale/region seam fields if the family may feed user-facing docs
3. seed English if that is all that exists today
4. do not fake multilingual content just to fill the seam

## Current proof surfaces

Current useful evidence includes:

- [message_catalog.hpp](D:/code/ccode/src/cli/message_catalog.hpp)
- [message_catalog.cpp](D:/code/ccode/src/cli/message_catalog.cpp)
- [locale_spine_catalog.hpp](D:/code/ccode/src/help/locale_spine_catalog.hpp)
- [locale_spine_catalog.cpp](D:/code/ccode/src/help/locale_spine_catalog.cpp)
- messaging smoke scripts under [docs/messaging/scripts](D:/code/ccode/docs/messaging/scripts)
- metadata export artifacts under [dottalkpp/data/scripts/metadata](D:/code/ccode/dottalkpp/data/scripts/metadata)

Examples of current messaging smoke coverage:

- `MESSAGE_CATALOG_PHASE22G_SET_LANGUAGE_ACTIVE_LOOKUP_SMOKE.dts`
- `MESSAGE_CATALOG_PHASE22H_SET_LANGUAGE_ACTIVE_EMISSION_SMOKE.dts`
- `MESSAGE_CATALOG_PHASE22M_SET_LANGUAGE_ROUTING_SMOKE.dts`
- `MESSAGE_CATALOG_PHASE22Q_UNSUPPORTED_LOCALE_ROUTING_SMOKE.dts`

## Rules to avoid future backtracking

1. Never use localized display text as the only identifier.
2. Never require English wording to reconstruct canonical structure.
3. Never let localized manuals or diagrams drift away from canonical IDs.
4. Never treat sparse multilingual seeding as a reason to remove locale fields.
5. Never collapse `SYSMSG` and `SYSTEM_MESSAGES` without an explicit crosswalk.

## Summary

Language and region support is not a side feature. It is a seam that must exist
across the whole family.

Current practical rule:

```text
canonical IDs remain stable
  + locale and region fields travel with metadata
  + shell/help/manual/diagram text may localize on top
```

English may remain the default seed for now.

The schema and workflow must still be ready for multilingual growth now, so the
system does not have to be rebuilt later just to add language support.
