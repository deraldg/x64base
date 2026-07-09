# MDO-382E Messaging and Locale Runtime Surface Alignment Packet

Status: `GREEN_REPORT_ONLY`

Date: 2026-07-08

## Objective

Align the developer manual with the current runtime reality that messaging and
locale handling already have live command/provider/data surfaces.

## What was aligned

- documented `MSGMGR` as the active runtime messaging-manager command house
- documented the active runtime catalog split:
  - metadata feeder: `SYSMSG`
  - runtime provider data: `SYSTEM_MESSAGES` / `SYSTEM_MESSAGE_TEXT`
- documented the locale spine split:
  - runtime locale tables: `SYSTEM_LOCALES` / `SYSTEM_LOCALE_FALLBACK`
  - provider: `src/help/locale_spine_catalog.cpp`
- patched both the current primary reader artifact and the current combined
  draft so they stop implying this lane is only future doctrine

## Supporting report

See:
`docs/manuals/developer/manualgen/reports/messaging_locale_runtime_surface_crosswalk_v1.md`

## Promotion meaning

This packet does not claim multilingual shell reporting is complete.

It does claim the documentation family can now safely say:

- the runtime has a real messaging catalog/provider lane
- the runtime has a real locale-spine lane
- `SYSMSG` remains important, but it is not the whole current story

## Next gate

`AUTHORIZE_COMMAND_SURFACE_HARVEST_FOR_SET_LANGUAGE_SET_MESSAGE_AND_RELATED_RUNTIME_DOCS`
