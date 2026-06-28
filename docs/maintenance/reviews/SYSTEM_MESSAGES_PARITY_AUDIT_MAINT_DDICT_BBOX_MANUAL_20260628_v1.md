# SYSTEM_MESSAGES Parity Audit

Date: 2026-06-28
Scope: `MAINT`, `DDICT`, `BBOX`, `HELP`, `CMDHELP`, `MANUAL`, `manualgen`
Intent: confirm that continuing the shared `SYSTEM_MESSAGES` / `SYSMSG` lane does not silently clobber lane-owned Help, Manual, Data Dictionary, or manual-generation systems.

## Conclusion

Green.

At the current boundary, continuing `SYSTEM_MESSAGES` work is safe for these command and documentation families as long as the work remains limited to:

- source-backed message catalog rows
- runtime message import/reset/verify scripts
- locale/schema/catalog wiring

and does **not** mutate:

- `dottalkpp/data/help/*`
- `dottalkpp/data/manuals/*`
- `dottalkpp/data/datadict/*`
- accepted manualgen catalogs under `docs/manuals/...`
- `CMDHELPCHK` expectations by surprise

## Native command surfaces reviewed

- `src/cli/cmd_maint.cpp`
- `src/cli/cmd_ddict.cpp`
- `src/cli/cmd_bbox.cpp`
- `src/cli/cmd_help.cpp`
- `src/cli/cmdhelp.cpp`
- `src/cli/cmd_manual.cpp`

Note:

- There is no native `MANGEN` command under `src/cli`.
- The manual generation lane is represented by `MANUAL`, `MANSTAR`, and the `manualgen` documentation/catalog workflow.
- `HELP` is not a lane-owned emitter only; it consumes shared `GLOBAL` and `MESSAGING` message rows in addition to `HELP` command rows.

## Lane-owned physical roots reviewed

### Data Dictionary

- `dottalkpp/data/datadict`

Observed physical catalog roots include both legacy `DD*` names and x64 `DATA_DICTIONARY_*` names.

### Help

- `dottalkpp/data/help`

Observed current Help tables include:

- `HELP_TOPIC`
- `HELP_SECTION`
- `HELP_LINE`
- `HELP_ARTIFACTS`
- locale companions
- `COMMANDS`
- `CMD_ARGS`

### Manual / manualgen

- `dottalkpp/data/manuals`
- `docs/manuals/developer/manualgen`
- `tools/manualgen`

Observed current MAN* tables include:

- `MANRUN`
- `MANSECTION`
- `MANMEDIA`
- `MANANCHOR`
- `MANHASH`
- `MANREVIEW`
- `MANPUB`
- `MANAPPX`

Observed current manualgen roots include:

- accepted catalogs / docs / manifests
- reports / review packets / runlog
- Python 3.12 `manualgen` toolchain under `tools/manualgen`
- read/report-only workflow notes and published manual artifacts

### Metadata feeder roots

- `dottalkpp/data/metadata`
- `dottalkpp/data/scripts/metadata`

## Shared seam identified

The overlap is **not** in the lane-owned DBFs above.

The shared seam is:

- `dottalkpp/data/scripts/metadata/SYSMSG_IMPORT_v1.csv`

That feeder already carries command-family rows for:

- `BBOX_*`
- `MAINT_*`
- `DDICT_*`
- `HELP_*`
- `CMDHELP_*`
- `MANUAL_*`

Therefore:

- those commands already participate in the shared message feeder
- `HELP` also consumes shared `GLOBAL_*` and `MESSAGE_*` rows
- but their Help/Manual/Data Dictionary/manualgen assets remain separate systems

## Source-to-SYSMSG parity result

The following exact parity audit was performed:

- extract `MessageId::...` usage from each native command source
- compare those enum names against `ENUM_NAME` in `SYSMSG_IMPORT_v1.csv`
- verify `OWNER`
- verify `FACILITY`

### Result summary

#### BBOX

- source message ids used: `10`
- missing from `SYSMSG_IMPORT_v1.csv`: `none`
- owner mismatches: `none`
- facility mismatches: `none`

#### DDICT

- source message ids used: `66`
- missing from `SYSMSG_IMPORT_v1.csv`: `none`
- owner mismatches: `none`
- facility mismatches: `none`

#### MAINT

- source message ids used: `7`
- missing from `SYSMSG_IMPORT_v1.csv`: `none`
- owner mismatches: `none`
- facility mismatches: `none`

#### MANUAL

- source message ids used: `38`
- missing from `SYSMSG_IMPORT_v1.csv`: `none`
- owner mismatches: `none`
- facility mismatches: `none`

#### HELP

- source message ids used: `17`
- missing from `SYSMSG_IMPORT_v1.csv`: `none`
- owner mismatches: `11`
- facility mismatches: `11`

Interpretation:

- these are expected and not feeder defects
- `HELP` intentionally consumes shared `GLOBAL_*` headings and the shared `MessageRoutingProofLine`
- therefore `HELP` is a mixed consumer, not a lane-exclusive owner

#### CMDHELP

- source message ids used: `38`
- missing from `SYSMSG_IMPORT_v1.csv`: `none`
- owner/facility mismatch audit: not enforced here because `CMDHELP` spans harvested/reference-oriented surfaces
- practical result: all currently referenced `MessageId` symbols are present in the feeder

#### manualgen

- native `MessageId::...` parity does not apply directly
- `tools/manualgen/README.md` declares the Python engine boundary as read/report-only
- current contract states it does not mutate publication, x64base tables, HELP, META, CMDHELPCHK, source, or runtime data
- docs under `docs/manuals/developer/manualgen` reference `SYSMSG` / `SYSTEM_MESSAGES` conceptually, but are not themselves message-catalog mutation targets

## Interpretation

This means the current message feeder already matches the native source surfaces for these command families.

So:

- continuing the shared messaging lane will not invent parallel message ownership for these commands
- continuing the shared messaging lane will not require touching their lane-owned DBFs
- continuing the shared messaging lane will not require touching manualgen catalogs or Python engine artifacts
- the correct authority chain stays:

1. native source behavior
2. `helpdata_messages.*`
3. `SYSMSG_IMPORT_v1.csv` feeder snapshot
4. runtime `SYSTEM_MESSAGES` / `SYSTEM_MESSAGE_TEXT`

## Boundary rule going forward

When working the messaging lane, treat these command families as:

- source-authoritative for wording and behavior
- feeder-backed in `SYSMSG_IMPORT_v1.csv`
- runtime-materialized in `SYSTEM_MESSAGES`

Do **not** treat the following as messaging-owned mutation targets:

- Help DBFs
- Manual DBFs
- Data Dictionary DBFs
- accepted manualgen catalogs
- published manual artifacts
- `tools/manualgen/*`
- `docs/manuals/developer/manualgen/*`

## Recommended next step

Resume the messaging lane at the shared feeder/runtime boundary only:

- `SYSMSG_IMPORT_v1.csv`
- runtime message reset/import/verify scripts
- locale/schema/catalog mechanics

Leave `MAINT`, `DDICT`, `BBOX`, `MANUAL`, Help, and manualgen physical catalogs untouched unless a lane-specific authorization is opened.
