# DotTalk++ Messaging and Locale Runtime Surface Crosswalk v1

Date: 2026-07-08

## Purpose

Record the current live runtime surfaces for messaging and locale handling so
manual promotion work can describe what already exists without collapsing it
back into a future-only metadata story.

## Runtime command surface

### MSGMGR

Source:
`src/cli/cmd_msgmgr.cpp`

Role:
- command house for runtime messaging-manager surfaces
- report/check entrypoint for active messaging-catalog status
- controlled seeding surface for reviewed runtime message rows

Current shape:
- `MSGMGR`
- `MSGMGR USAGE`
- `MSGMGR STATUS`
- `MSGMGR CHECK`
- `MSGMGR SEED PRIORITYA CHECK|APPLY`
- `MSGMGR SEED PRIORITYB CHECK|APPLY`
- `MSGMGR SEED PRIORITYC CHECK|APPLY`

Important boundary:
- `STATUS` and `CHECK` are read/report surfaces
- reviewed `SEED ... APPLY` mutates the runtime messaging catalog tables
- this command explicitly does not mutate HELP DATA, CMDHELPCHK, manualgen,
  Data Dictionary, SelfDoc, or source-derived catalogs

Related surfaces named by the command:
- `SET MESSAGE CATALOG CHECK`
- `SET MESSAGE CATALOG GET`
- `SET LANGUAGE`
- `SET MESSAGE EMIT`

## Runtime data/catalog surface

### Active messaging catalog

Observed runtime data root:
`dottalkpp/data/messaging`

Observed current tables/files:
- `SYSTEM_MESSAGES.dbf`
- `SYSTEM_MESSAGE_TEXT.dbf`
- `SYSTEM_MESSAGE_TEXT.dtx`
- supporting seed/demo csv such as `gui_messages.csv`

Observed provider source:
`src/help/message_catalog.cpp`

Meaning:
- `SYSTEM_MESSAGES` and `SYSTEM_MESSAGE_TEXT` are not only archival names
- they are active runtime catalog/provider inputs today
- the provider resolves localized message text from DBF/memo-backed data

## Locale spine surface

Observed locale data root:
`dottalkpp/data/locale`

Observed current tables:
- `SYSTEM_LOCALES.dbf`
- `SYSTEM_LOCALE_FALLBACK.dbf`

Observed provider source:
`src/help/locale_spine_catalog.cpp`

Observed runtime roots expected by the provider:
- `dottalkpp/data/locale`
- `dottalkpp/data/indexes/locale`
- `dottalkpp/data/lmdb/locale`

Meaning:
- locale handling is no longer only a prose ambition
- a shared locale spine exists structurally
- current fallback behavior is rooted in the locale-spine provider and
  currently falls back through `en-US`

## Important doctrine split

Use this split consistently:

- `SYSMSG` remains the compact metadata feeder and planning surface for message
  identity, severity, ownership, and publication alignment
- `SYSTEM_MESSAGES` / `SYSTEM_MESSAGE_TEXT` are active runtime catalog tables
  and should be described as such when the manual is talking about current
  runtime behavior
- the locale spine is a structural/runtime lane through `SYSTEM_LOCALES` and
  `SYSTEM_LOCALE_FALLBACK`, not just a future website/manual idea

## Manual promotion implication

The manual should stop using wording that implies messaging is only future
catalog doctrine.

Safer current wording:

- typed message metadata still matures through `SYSMSG`
- live runtime message rendering already uses the active messaging catalog
- locale selection and fallback now have a real runtime spine, even if broader
  multilingual shell coverage is still incomplete

## Boundary

Report only.

No source, HELP, META, catalog, or publication mutation is performed by this
crosswalk artifact.
