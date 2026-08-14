# DotTalkPP DBF Path Policy

## Purpose

This document assigns a provisional path policy to DBF-bearing areas under:

- `D:\code\ccode\dottalkpp`

The goal is to distinguish:

- primary subsystem tables
- engine/runtime fixtures
- duplicate or legacy copies
- sandbox/process outputs
- backup/archive material
- generated derivative artifacts

This is a planning document, not an instruction to delete files automatically.

## Policy Labels

- `primary`
  The preferred authoritative home for a subsystem-owned DBF family.

- `fixture`
  Canonical runtime or engine specimen data used for compatibility, smoke tests, or demonstrations.

- `duplicate`
  A non-primary copy of a DBF family that appears to mirror a primary location or older layout.

- `sandbox`
  Mutable, experimental, probe, or local process data not intended as the authoritative store.

- `backup`
  Historical preservation content, promotion snapshots, or rollback material.

- `generated`
  Derived output from a build, mining, export, or projection process. May be useful, but should not be confused with the authoritative source.

## Path Policy

| Path | Policy | Notes |
| --- | --- | --- |
| `data/metadata/` | `primary` | Authoritative metadata/runtime catalog surface: `SYSCMD`, `SYSARGS`, `SYSFUNC`, `SYSHELP`, `SYSMSG`, `SYSSUBCMD`, `SYSFLDDIC`, `SYSENTVAR`. |
| `data/messaging/` | `primary` | Authoritative messaging catalog surface: `SYSTEM_MESSAGES`, `SYSTEM_MESSAGE_TEXT`. |
| `data/locale/` | `primary` | Authoritative locale-spine surface: `SYSTEM_LOCALES`, `SYSTEM_LOCALE_FALLBACK`. |
| `data/help/` | `primary` | Preferred active help/catalog DBF family: `COMMANDS`, `CMD_ARGS`, `HELP_TOPIC`, `HELP_SECTION`, `HELP_LINE`, `HELP_ARTIFACTS`, and locale overlays. |
| `data/manuals/` | `primary` | Manualgen/mangen state and publication tables: `MANRUN`, `MANSECTION`, `MANANCHOR`, etc. |
| `data/datadict/` | `primary` | Preferred datadict catalog home: `DDSOURCE`, `DDRUN`, `DDOBJECT`, `DDATTR`, `DDEDGE`, `DDEVID`, `DDARTIF`, etc. |
| `data/comments/` | `primary` | Preferred selfdoc/source-comment catalog home: `SRCFILE`, `SRCLINE`, `SRCUSAGE`, `SRCBLOCK`, `MEMO_LINES`, etc. |
| `data/dbf/` | `fixture` | Root engine/runtime fixture area. Contains base specimen tables and compatibility data. Do not treat as temp. |
| `data/dbf/x32/` | `fixture` | Canonical 32-bit/legacy compatibility specimen set. |
| `data/dbf/x64/` | `fixture` | Canonical x64 specimen set for runtime and format validation. |
| `data/dbf/memo/` | `fixture` | Memo compatibility fixtures in root memo grouping. |
| `data/dbf/x64/memo/` | `fixture` | Preferred x64 memo fixture family, including memo subtype coverage. |
| `data/dbf/help/` | `duplicate` | Likely older or alternate help DBF layout relative to `data/help/`. Keep for comparison until help policy is finalized. |
| `etc/system/` | `duplicate` | Operational or scenario-specific copies of `commands.dbf` and `cmd_args.dbf`, not preferred canonical home. |
| `etc/use/` | `duplicate` | Same as `etc/system/`; likely command lifecycle copy. |
| `etc/zap/` | `duplicate` | Same as `etc/system/`; likely command lifecycle copy. |
| `data/help/V32_help/` | `duplicate` | Legacy or versioned help-family snapshot, not preferred active location. |
| `data/help/FULL/` | `generated` | Derived help artifact variant, likely built for a specific projection or report. |
| `data/help/MINEALL/` | `generated` | Derived/mined help artifact variant, not authoritative source. |
| `data/datadict/datadict/` | `duplicate` | Nested mirror of datadict family; not preferred if `data/datadict/` is authoritative. |
| `data/datadict/datadict_sandbox/` | `sandbox` | Explicit sandbox datadict run area. |
| `data/datadict/datadict_canonical_rebuild_v0/` | `generated` | Rebuild output useful for audit and comparison, but not the default authoritative store. |
| `data/datadict/datadict_promotion_backups/` | `backup` | Historical promotion snapshots. |
| `data/datadict/datadict_create_probe/` | `sandbox` | Probe/test creation surface rather than production catalog home. |
| `data/dbf/sandbox/` | `sandbox` | Explicit mutable specimen and test-copy area. |
| `data/backup/dbf/` | `backup` | Historical preserved DBF copies. |
| `junk/` | `sandbox` | Ad hoc experiments and non-canonical specimens. |
| `docs/_backups/` | `backup` | Historical documentation/runtime snapshots, not active subsystem state. |

## Subsystem Ownership

### Metadata

- Policy home: `data/metadata/`
- Tables: `SYSCMD`, `SYSARGS`, `SYSFUNC`, `SYSHELP`, `SYSMSG`, `SYSSUBCMD`, `SYSFLDDIC`, `SYSENTVAR`
- Role: runtime catalog, command surface, metadata reflection, cmdhelp input

### Messaging

- Policy home: `data/messaging/`
- Tables: `SYSTEM_MESSAGES`, `SYSTEM_MESSAGE_TEXT`
- Role: message catalog and localized message text

### Locale

- Policy home: `data/locale/`
- Tables: `SYSTEM_LOCALES`, `SYSTEM_LOCALE_FALLBACK`
- Role: locale registry and fallback routing

### Help / CmdHelp

- Policy home: `data/help/`
- Core tables: `COMMANDS`, `CMD_ARGS`, `HELP_TOPIC`, `HELP_SECTION`, `HELP_LINE`, `HELP_ARTIFACTS`
- Locale overlays: `HELP_TOPIC_LOCALE`, `HELP_SECTION_LOCALE`, `HELP_LINE_LOCALE`, `HELP_ARTIFACT_LOCALE`
- Warning: `data/dbf/help/` and `etc/*/commands.dbf` should not be treated as the default active home without proof

### ManualGen / Mangen

- Policy home: `data/manuals/`
- Tables: `MANRUN`, `MANSECTION`, `MANREVIEW`, `MANPUB`, `MANMEDIA`, `MANHASH`, `MANAPPX`, `MANANCHOR`
- Role: manual generation and publication pipeline state

### DataDict / DDict

- Policy home: `data/datadict/`
- Core tables: `DDSOURCE`, `DDRUN`, `DDREVIEW`, `DDPROFILE`, `DDOBJECT`, `DDGATE`, `DDEVID`, `DDEDGE`, `DDBASE`, `DDATTR`, `DDARTIF`
- Expanded mirrors: `DATA_DICTIONARY_*`
- Warning: `datadict_sandbox`, `canonical_rebuild_v0`, and promotion backups are not default active homes

### Comments / SelfDoc

- Policy home: `data/comments/`
- Tables: `SRCFILE`, `SRCLINE`, `SRCUSAGE`, `SRCBLOCK`, `SRCCLASS`, `SRCDISP`, `SRCALIAS`, `MEMO_LINES`
- Role: source-comment and self-documentation evidence catalogs

### Engine / Runtime Fixtures

- Policy homes:
  - `data/dbf/`
  - `data/dbf/x32/`
  - `data/dbf/x64/`
  - `data/dbf/memo/`
  - `data/dbf/x64/memo/`
- Role: compatibility fixtures, smoke-test specimens, DBF/memo behavior validation
- Warning: these are not trash, but they are not subsystem metadata catalogs either

## Staging Guidance

For later GitHub staging and repo cleanup:

- treat `primary` paths as subsystem-owned candidates to preserve and organize
- treat `fixture` paths as engine/runtime assets requiring a separate fixture policy
- treat `duplicate` paths as compare-and-consolidate candidates
- treat `sandbox` paths as non-authoritative and eligible for relocation or exclusion
- treat `backup` paths as archival only
- treat `generated` paths as outputs that should not silently become source-of-truth

## Immediate Implication

The biggest unresolved policy question is not metadata-family ownership.

That part is already fairly legible.

The biggest unresolved question is fixture governance for:

- `data/dbf/`
- `data/dbf/x32/`
- `data/dbf/x64/`
- `data/dbf/memo/`
- `data/dbf/x64/memo/`

Those areas need a separate engine-fixture plan before aggressive staging cleanup.
