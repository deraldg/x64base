# DotTalk++ Messaging and Locale Command Surface Crosswalk v1

Date: 2026-07-08

## Purpose

Document the operator-facing command surfaces for messaging and locale control,
so manual prose can describe the real shell entrypoints instead of jumping
directly from doctrine to provider internals.

## Primary shell entrypoint

### SET

Source:
`src/cli/cmd_set.cpp`

Messaging/locale subcommands currently surfaced through `SET`:
- `SET LANGUAGE`
- `SET LANGUAGE TO <locale|DEFAULT>`
- `SET LOCALE`
- `SET LOCALE TO <locale|DEFAULT>`
- `SET LANGUAGE CHECK`
- `SET LANGUAGE REPORT`
- `SET LOCALE CHECK`
- `SET LOCALE REPORT`
- `SET MESSAGE CATALOG CHECK`
- `SET MESSAGE CATALOG STATUS`
- `SET MESSAGE PROOF ON|OFF|CHECK`
- `SET MESSAGE EMIT <symbol> [LOCALE <locale>] [ARG <name> <value>]`

Observed semantics:
- `SET LANGUAGE` / `SET LOCALE` mutate the active session message locale
- successful locale changes route through the active message provider when the
  runtime DBF catalog is loaded
- unsupported locale diagnostics also attempt active-provider routing before
  falling back to compiled message text
- `SET MESSAGE CATALOG CHECK|STATUS` is the operator-facing provider check
  surface
- `SET MESSAGE PROOF` is a diagnostics/proof gate for message-routing evidence
- `SET MESSAGE EMIT` is a direct shell test surface for message symbol emission

## Command-house surface

### MSGMGR

Source:
`src/cli/cmd_msgmgr.cpp`

Role:
- manager/report/check/seed house for the runtime catalog itself

Meaningful split:
- `SET ...` is the everyday shell/operator surface
- `MSGMGR` is the manager/seed/report surface around the same catalog lane

## Provider/data boundary

Operator commands above ultimately coordinate with:
- provider: `src/help/message_catalog.cpp`
- locale provider: `src/help/locale_spine_catalog.cpp`
- runtime data:
  - `dottalkpp/data/messaging/SYSTEM_MESSAGES.dbf`
  - `dottalkpp/data/messaging/SYSTEM_MESSAGE_TEXT.dbf`
  - `dottalkpp/data/locale/SYSTEM_LOCALES.dbf`
  - `dottalkpp/data/locale/SYSTEM_LOCALE_FALLBACK.dbf`

## Manual implication

Safe manual wording:

- shell users normally encounter messaging/locale through `SET`
- maintainers and seed/review flows encounter the lane through `MSGMGR`
- both surfaces sit above the same provider/data spine

## Boundary

Report only.
