# DotTalk++ Database Safety Contract v1

Status: draft blocking contract.

Related:

- `VALUE_LOCALE_COLLATION_CONTRACT_V1.md`
- `../gui/GUI_RUNTIME_FACADE_PLAN_V1.md`
- `../gui/GUI_THREADING_EVENT_MODEL_V1.md`
- `../gui/WINDOWED_APP_CONTRACT_V1.md`

## Purpose

DotTalk++ should become a good database program, not just a program that can
open DBF files. A good database tool protects data, explains risk, detects
damage, and makes mutating operations explicit.

This contract defines the minimum safety expectations before windowed editing,
index rebuilds, imports, pack operations, and multi-threaded workflows grow.

## Core Rule

Every mutating operation needs a boundary.

```text
preflight
  -> begin operation
  -> apply changes
  -> verify result
  -> finalize
  -> report structured status
```

If an operation cannot provide rollback, it must say so before it starts and
should create a backup or recovery artifact when practical.

## Default Modes

| Mode | Rule |
| --- | --- |
| Inspect/read-only | Default for new GUI table opens |
| Edit session | Explicit user action, visible dirty state |
| Maintenance | Explicit operation mode for pack, repair, reindex, migration |
| Import/export | Explicit source/target, parse locale, encoding, and conflict policy |
| Compatibility command | Allowed, but should report whether it mutates data |

The first windowed GUI should remain read-only until edit safety is designed and
tested.

## Required Integrity Checks

The database layer should have service-level checks for:

- DBF header length and record length consistency,
- field descriptor validity,
- record count vs file length,
- deleted record marker validity,
- field width/decimal sanity,
- memo file existence and block size,
- memo pointer validity,
- index/tag file existence,
- index expression parseability,
- index/table freshness,
- encoding/code page ambiguity,
- file lock or sharing conflict,
- unexpected truncation.

Each check should return structured status with stable codes, not only English
text.

## Operation Boundaries

### Open Table

Preflight:

- resolve path,
- check file existence and permissions,
- read header,
- detect dialect/encoding,
- detect related memo/index files,
- declare read/write mode.

Result:

- stable area ID,
- table value context,
- warnings,
- safe snapshot availability.

### Edit Record

Preflight:

- confirm edit mode,
- capture original record image,
- validate field values,
- check locks,
- check index update requirements.

Result:

- dirty state or committed state,
- changed fields,
- validation messages,
- index refresh status.

### Append Record

Preflight:

- schema validation,
- default/null policy,
- file lock strategy,
- memo allocation strategy.

Result:

- new record identity,
- changed indexes,
- rollback/recovery note if not transactional.

### Delete or Recall

Preflight:

- confirm selected record identity,
- confirm deleted marker behavior,
- update index/filter expectations.

Result:

- deleted/active state,
- visible filter effects,
- dirty/committed status.

### Pack

Pack is destructive.

Required:

- explicit maintenance mode,
- close or isolate active editors,
- backup or copy-on-write destination,
- memo/index rebuild plan,
- record count before/after,
- validation after completion.

### Reindex

Required:

- table value context,
- index collation identity,
- expression validation,
- temp output path,
- atomic replacement where possible,
- verification before activation.

### Import

Required:

- source encoding,
- parse locale,
- schema mapping,
- conflict policy,
- validation report,
- preview before mutating destination where practical.

### Export

Required:

- output encoding,
- display or storage value policy,
- locale policy for formatted exports,
- overwrite policy,
- row count and checksum/hash where practical.

## Concurrency and Threading

The runtime must define ownership before allowing parallel work.

Initial conservative rule:

- one mutable runtime session owns each `DbArea`,
- GUI widgets never own runtime objects,
- worker tasks operate through session services,
- immutable snapshots cross thread boundaries,
- only one mutating task may run per table/session,
- read-only concurrency is allowed only after the involved table, memo, and index
  access paths are proven safe.

This is compatible with the current GUI-core `AsyncSession` approach.

## Locking Policy

DotTalk++ should distinguish:

- process-local session ownership,
- OS file sharing/locking,
- DBF record locks,
- memo file locks,
- index rebuild locks,
- user-visible edit locks.

The GUI must not imply a record is safely editable until the relevant locks and
write mode are known.

## Crash and Recovery Policy

For mutating operations, prefer:

- temp files in the same directory or same volume,
- write/flush/verify before replacement,
- atomic rename where the platform supports it,
- backup before destructive operations,
- operation journal for multi-file changes where practical,
- recovery scan on startup or explicit maintenance command.

Multi-file operations are especially sensitive:

- DBF plus memo,
- DBF plus CDX/NDX,
- metadata DBF plus sidecar indexes,
- import target plus report/log.

## Index Safety

Indexes are not just files. They are derived data with identity.

Every index/tag should eventually report:

- source table path/identity,
- source table modification marker,
- key expression,
- filter expression,
- collation identity,
- encoding/value policy,
- build tool/version,
- record count at build,
- stale/valid/unknown state.

A stale or incompatible index must not be used silently for seek/navigation.

## Memo Safety

Memo fields need their own checks:

- pointer bounds,
- block size,
- orphaned blocks,
- reused/free block behavior,
- memo encoding,
- binary vs text memo distinction,
- update ordering relative to DBF record writes.

Windowed preview can show memo summaries before full memo editing exists.

## Error and Status Contract

Database services should return:

- severity,
- stable code,
- short text,
- detailed text,
- affected path/table/area,
- operation ID or task ID,
- recovery suggestion when known,
- whether the operation mutated anything.

The UI may render this as a status bar message, dialog, or log row, but it must
not parse English text to decide behavior.

## Required Maintenance Tools

Before serious write workflows, DotTalk++ should provide service-level tools for:

- validate table,
- validate memo,
- validate indexes,
- rebuild indexes,
- backup table family,
- pack with backup,
- repair known-safe damage classes,
- encoding/collation report,
- export validation report.

The CLI/TUI/GUI lanes can present these differently, but the service contract
should be shared.

## Windowed GUI Implications

The windowed GUI should make safety visible:

- read-only vs edit mode,
- dirty state,
- active locks,
- stale index warnings,
- unknown encoding warnings,
- task progress and cancellation,
- validation/repair reports,
- destructive operation confirmation with concrete affected files.

No edit controls should be enabled just because the grid can display values.

## Acceptance Criteria

The database safety contract is minimally honored when:

- opening a table reports encoding/dialect/index/memo warnings,
- opening multiple areas does not share mutable table objects across widgets,
- read-only snapshots are immutable,
- stale or unknown index state is visible,
- mutating operations have explicit preflight and status,
- destructive operations require backup/recovery policy,
- tests cover corrupt headers, bad memo pointers, stale indexes, and lock errors.

## Deferred But Expected

- Full transaction manager.
- Multi-user record locking UI.
- Point-in-time recovery.
- Audit log for every edit.
- Online index rebuild for active writers.
- Conflict resolution for concurrent editors.

These can wait, but the current code should not make them impossible.
