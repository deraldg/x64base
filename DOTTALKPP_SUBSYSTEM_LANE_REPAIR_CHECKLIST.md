# DotTalkPP Subsystem Lane Repair Checklist

## Purpose

This checklist captures the current repair work needed after promoting structural DBF families from:

- `dottalkpp/data/dbf/...`

up into:

- `dottalkpp/data/<subsystem>/`

The focus is narrow:

- DBF location
- matching CDX location
- matching LMDB location
- matching `.dts` path wiring
- obvious stray or cross-subsystem contamination

## Status Labels

- `OK`
  Looks coherent enough for now.

- `FIX PATH`
  `.dts` script points to the wrong place.

- `MISSING CDX`
  DBFs exist but equivalent `.cdx` files are missing or incomplete.

- `MISSING LMDB`
  DBFs/CDX exist but LMDB lane is missing or incomplete.

- `STRAY`
  Foreign files appear in the subsystem lane.

- `UNWIRED`
  Promoted DBF family exists but has no obvious `.dts` lane.

## Checklist

| Subsystem | DBF lane | CDX lane | LMDB lane | DTS lane | Status | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| `messaging` | `data/messaging/` | `data/indexes/messaging/` | `data/lmdb/messaging/` | [messaging.dts](D:/code/ccode/dottalkpp/data/messaging.dts) | `OK` | `SYSTEM_MESSAGES` and `SYSTEM_MESSAGE_TEXT` are fully matched. |
| `locale` | `data/locale/` | `data/indexes/locale/` | `data/lmdb/locale/` | none found under `data/*.dts` | `UNWIRED` | Physical lanes are coherent, but no dedicated data-root `.dts` lane was found. |
| `manuals` | `data/manuals/` | `data/indexes/manuals/` | `data/lmdb/manuals/` | [manuals.dts](D:/code/ccode/dottalkpp/data/manuals.dts) | `FIX PATH`, `STRAY` | Script still points to docs-side absolute path instead of promoted runtime lane. `lmdb/manuals/` contains stray `MAJORS.cdx.d`. |
| `metadata` | `data/metadata/` | `data/indexes/metadata/` | `data/lmdb/metadata/` | [metadata.dts](D:/code/ccode/dottalkpp/data/metadata.dts) | `MISSING CDX`, `MISSING LMDB` | DBF family has 8 tables, but active lane looks complete only for `SYSCMD`. Need to confirm whether full metadata family should be indexed. |
| `metadata_x64` | no separate DBF lane found | `data/indexes/x64/metadata/` | `data/lmdb/x64/metadata/` | [metadata_x64.dts](D:/code/ccode/dottalkpp/data/metadata_x64.dts) | `FIX PATH`, `STRAY` | Script points DBF to `metadata` but indexes/LMDB to x64 metadata lane. LMDB lane contains many non-metadata engine tables. |
| `help/cmdhelp` | `data/help/` | `data/indexes/help/` | `data/lmdb/help/` | [cmdhelp.dts](D:/code/ccode/dottalkpp/data/cmdhelp.dts), [selfhelp.dts](D:/code/ccode/dottalkpp/data/selfhelp.dts) | `MISSING CDX`, `STRAY` | `COMMANDS.cdx` exists, but `CMD_ARGS`, `HELP_TOPIC`, `HELP_SECTION`, `HELP_LINE`, `HELP_ARTIFACTS` CDXs are missing. `indexes/help/` has stray `PEOPLE.cdx` and `TINY.cdx`. |
| `datadict` | `data/datadict/` | `data/indexes/datadict/` | `data/lmdb/datadict/` | [ddbase.dts](D:/code/ccode/dottalkpp/data/ddbase.dts) | `STRAY` | Core family is mostly coherent. `lmdb/datadict/` contains stray `MANANCHOR.cdx.d`. |
| `comments` | `data/comments/` | none | none | none found under `data/*.dts` | `UNWIRED`, `MISSING CDX`, `MISSING LMDB` | Promoted DBF family exists, but no index lane, no LMDB lane, and no data-root script lane were found. |

## Repair Actions

### 1. Manuals

- Update [manuals.dts](D:/code/ccode/dottalkpp/data/manuals.dts) to use:
  - `SET PATH DBF TO MANUALS`
  - `SET PATH INDEXES TO INDEXES\MANUALS`
  - `SET PATH LMDB TO LMDB\MANUALS`
- Remove or relocate stray `MAJORS.cdx.d` from `data/lmdb/manuals/`

### 2. Metadata

- Decide whether all `data/metadata/*.dbf` tables should have corresponding CDX/LMDB companions
- If yes, create or restore matching CDX/LMDB lanes for:
  - `SYSARGS`
  - `SYSENTVAR`
  - `SYSFLDDIC`
  - `SYSFUNC`
  - `SYSHELP`
  - `SYSMSG`
  - `SYSSUBCMD`
- If no, document that only `SYSCMD` is expected to be indexed

### 3. Metadata X64

- Decide whether `metadata_x64.dts` should:
  - point DBF to a real `data/metadata_x64/` lane, or
  - be retired in favor of `metadata.dts`
- Remove non-metadata LMDB dirs from `data/lmdb/x64/metadata/`

### 4. Help / CmdHelp

- Decide whether the promoted canonical help lane is `data/help/`
- If yes, add or restore CDX files for:
  - `CMD_ARGS`
  - `HELP_TOPIC`
  - `HELP_SECTION`
  - `HELP_LINE`
  - `HELP_ARTIFACTS`
- Remove or relocate stray `PEOPLE.cdx` and `TINY.cdx` from `data/indexes/help/`
- Verify that `cmdhelp.dts` and `selfhelp.dts` should continue to target `data/help/`

### 5. Locale

- Add a dedicated `locale.dts` if locale lanes are meant to be opened or validated directly from runtime scripts

### 6. DataDict

- Remove or relocate stray `MANANCHOR.cdx.d` from `data/lmdb/datadict/`
- Confirm whether uppercase/lowercase CDX filename variation is intentional or accidental

### 7. Comments

- Decide whether `data/comments/` is:
  - developer-only storage, or
  - a real runtime/query lane
- If it is a real lane, add:
  - `data/indexes/comments/`
  - `data/lmdb/comments/`
  - a dedicated `.dts` lane

## Priority Order

1. `manuals`
2. `help/cmdhelp`
3. `metadata`
4. `metadata_x64`
5. `datadict`
6. `locale`
7. `comments`

## Immediate Conclusion

The promotion was partly successful.

The promoted folders are real and meaningful, but only `messaging` is currently fully married across:

- DBF
- CDX
- LMDB
- `.dts`

The rest need either path correction, missing companions, or subsystem-lane cleanup.
