# Runtime Message Catalog Seed Workflow v1

Status: canonical working draft  
Scope: runtime messaging lane only  
Working root: `D:\code\ccode\dottalkpp`

## Purpose

This workflow defines the reviewed path for promoting the compiled message
registry into the active runtime messaging workspace.

It covers:

- `SYSTEM_MESSAGES`
- `SYSTEM_MESSAGE_TEXT`
- generated CSV snapshots
- reviewed import scripts

It does not replace:

- `SYSMSG` metadata identity work
- HELP/CMDHELPCHK generation
- manualgen/selfdoc publication

## Inputs

Source authority:

- `D:\code\ccode\src\help\helpdata_messages.cpp`
- `D:\code\ccode\src\help\helpdata_messages.hpp`
- `D:\code\ccode\src\help\message_catalog.cpp`

Schema authority:

- `D:\code\ccode\dottalkpp\data\schemas\messaging\message_catalog.dtschema`

## Generator

Generator script:

- `D:\code\ccode\dottalkpp\tools\help\generate_runtime_message_catalog_seed_v1.py`

Generated outputs:

- `D:\code\ccode\dottalkpp\data\scripts\messaging\SYSTEM_MESSAGES_IMPORT_v1.csv`
- `D:\code\ccode\dottalkpp\data\scripts\messaging\SYSTEM_MESSAGE_TEXT_IMPORT_v1.csv`

Generator rules:

1. Read the compiled `MessageDef` registry from `all_messages()`.
2. Read localized `MessageTextDef` rows from `all_message_texts()`.
3. Preserve already-seeded numeric `MSGID` values declared in
   `message_catalog.cpp`.
4. Allocate new numeric `MSGID` values after the current seeded maximum.
5. Emit explicit locale rows for the localized source texts already present in
   source.
6. Ensure every message has an `en-US` runtime text row, using the compiled
   fallback text if needed.

## Import lane

Reviewed import scripts:

- `D:\code\ccode\dottalkpp\data\scripts\messaging\RUNTIME_MESSAGE_CATALOG_RESET_v1.RUN_REVIEWED.dts`
- `D:\code\ccode\dottalkpp\data\scripts\messaging\RUNTIME_MESSAGE_CATALOG_IMPORT_v1.RUN_REVIEWED.dts`
- `D:\code\ccode\dottalkpp\data\scripts\messaging\RUNTIME_MESSAGE_CATALOG_IMPORT_v1.verify.dts`
- `D:\code\ccode\dottalkpp\data\scripts\messaging\RUNTIME_MESSAGE_CATALOG_RESET_RELOAD_v1.RUN_REVIEWED.dts`

Legacy compatibility wrappers:

- `D:\code\ccode\dottalkpp\data\scripts\messaging_priority_a_seed_apply_v1.dts`
- `D:\code\ccode\dottalkpp\data\scripts\messaging_priority_a_seed_verify_v1.dts`

Usage doctrine:

- This is a reviewed snapshot reload path.
- It is not intended as an append-on-top-of-anything workflow.
- Use it after the active messaging workspace has been reviewed/reset for the
  incoming snapshot.

Reset doctrine:

- `RUNTIME_MESSAGE_CATALOG_RESET_v1.RUN_REVIEWED.dts` is the destructive step.
- It recreates the active runtime messaging DBF tables and the reviewed
  field-addressable CDX containers.
- It then rebuilds the LMDB environments from those containers.
- Expression-tag parity for `MSG_LOCALE` / `SYMBOLLOC` remains an explicit
  follow-up lane.

## Runtime sequence

1. Generate the CSV snapshots.
2. Reset the active messaging workspace with:
   - `DO messaging\RUNTIME_MESSAGE_CATALOG_RESET_v1.RUN_REVIEWED.dts`
3. Import `SYSTEM_MESSAGES`.
4. Import `SYSTEM_MESSAGE_TEXT`.
5. Rebuild LMDB from the reviewed `SYSTEM_MESSAGES.cdx` and
   `SYSTEM_MESSAGE_TEXT.cdx` containers.
6. Verify the locale-aware runtime load with:
   - `SET MESSAGE CATALOG CHECK`
   - `SET MESSAGE EMIT ...`
   - `SET LANGUAGE TO <locale>`

One-shot reviewed driver:

- `DO messaging\RUNTIME_MESSAGE_CATALOG_RESET_RELOAD_v1.RUN_REVIEWED.dts`

Legacy wrapper rule:

- Older `messaging_priority_a_seed_*` entry points no longer append a partial
  handcrafted subset.
- They are compatibility names only and now route into the reviewed full-catalog
  reset/reload or verification path.

## Authority split

The lanes remain separate on purpose:

- `SYSTEM_MESSAGES` / `SYSTEM_MESSAGE_TEXT`
  Runtime load lane used by `message_catalog.cpp`.

- `SYSMSG`
  Metadata identity/crosswalk lane for help/selfdoc/manual/meta promotion.

- `helpdata_messages.*`
  Compiled fallback lane for bootstrap and failure-safe runtime text.

## Locale posture

Current runtime message locales observed in compiled source:

- `en-US`
- `de`
- `es`
- `fr`
- `it`

The workflow seeds those locales now. Additional languages can be added later
by extending `all_message_texts()` first, then regenerating the runtime CSV
snapshots.
