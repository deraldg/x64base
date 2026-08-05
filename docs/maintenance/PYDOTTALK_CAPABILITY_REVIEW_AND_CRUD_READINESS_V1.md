# pydottalk capability review and CRUD readiness (AIF-086)

Owner: member.derald. Status: review-needed (authored by steward, not yet ratified).
Lane: AIF-086 (tracking-state dogfood). Companion: TRACKING_STATE_DOGFOOD_LANE_V1.md.

## Why this exists

The plan is a Python CRUD over pydottalk for the SYS* tables (identity, bbs, portal
ruling + tracking). Before writing a single write path, the maintainer asked two
questions and one directive:

  1. Does pydottalk need record locking, triggers, etc.?
  2. Confirm the advanced features (do not assume them).
  3. pydottalk needs a full review -- its updates are consistent but not timely.

This review answers all three by grounding the binding against the engine's own
documented basic API, so the CRUD is designed to live inside CONFIRMED limits.

## Method (grounded sources, not memory)

  - Engine command surface: the website command catalog, source-derived from
    `src/cli/shell_commands.cpp` and `@dottalk.usage` blocks. Snapshot: 236
    registered command keys, 215 parsed usage contracts
    (content/docs/dottalk/command-catalog.mdx on x64base-site).
  - Engine function surface: 63 core expression functions + 2 student examples
    (content/docs/dottalk/function-catalog.mdx).
  - pydottalk binding surface: enumerated directly from
    `bindings/pydottalk/src/module.cpp` (the pybind `DbArea` class_ defs).
  - Engine command presence cross-checked in `src/cli/cmd_*.cpp`.

## The engine HAS a full data/lifecycle/concurrency vocabulary

From the command catalog, the engine's basic API already covers every layer a CRUD
needs:

  - Create rows: APPEND, APPEND_BLANK, INSERT.
  - Read: LIST, DISPLAY, DUMP, SMARTLIST, LOCATE, SEEK, SCAN, COUNT.
  - Update: REPLACE, MULTIREP, CALCWRITE, UPDATE.
  - Delete lifecycle: DELETE, RECALL, UNDELETE, PACK, TURBOPACK, ZAP, SQLERASE.
  - Concurrency: LOCK (record/table), UNLOCK.
  - Transactional buffering: COMMIT, ROLLBACK, TABLE_BUFFER.
  - Constraints: RULE, VALIDATE.
  - Relations/joins: REL, RELATIONS, SET RELATION.

## What pydottalk ACTUALLY binds

The entire mutable surface of the `DbArea` binding is:

  - lifecycle: open, close, isOpen.
  - navigation: gotoRec, top, bottom, skip.
  - read: readCurrent, get, get_field, get_memo_text, read_record,
    scan_records(skip_deleted=True), fields, fieldCount, recno, recCount,
    bof, eof, recLength.
  - write: appendBlank, set, set_field, writeCurrent.
  - delete: deleteCurrent (sets the classic xBase deleted tombstone), isDeleted.
  - introspection: filename, logicalName, memoKind, versionByte, tableFlags.

## The gap that matters (capability | engine | pydottalk | CRUD impact)

  - Record/table locking | LOCK / UNLOCK | NOT BOUND | writes are uncoordinated;
    safe only as a single writer. No cooperative lock is taken.
  - Undelete | RECALL / UNDELETE | NOT BOUND | a tombstone set via deleteCurrent
    CANNOT be cleared through pydottalk. Purge is irreversible here.
  - Physical reclaim | PACK / TURBOPACK / ZAP | NOT BOUND | deleteCurrent only
    marks deleted; the file is not compacted. Reclamation is an engine step.
  - Transaction | COMMIT / ROLLBACK / TABLE_BUFFER | NOT BOUND | writeCurrent
    persists immediately; there is no rollback. Multi-row ops are not atomic.
  - Constraints | RULE / VALIDATE | NOT BOUND | no engine-side validation; the
    CRUD must validate field names, types, and enum codes in Python before write.
  - Relations/joins | REL / SET RELATION | NOT BOUND | joins (e.g. resolve
    MEMBERKEY -> SYSMEMBER) happen in Python at read time. Already anticipated by
    the key-FK decision in tracking_schema.hpp.
  - Triggers | (none in engine) | (nothing to bind) | there is no DB-trigger
    mechanism. Derived-state upkeep is the writer's job or a derive-on-read report,
    never a trigger.

## Why the gap exists: the build boundary (the "one file that disconnects them")

pydottalk is INDEPENDENT of the dottalkpp executable. It shares engine SOURCE, it
does not link the CLI. The boundary is drawn in one file --
`bindings/pydottalk/CMakeLists.txt` -- which compiles only:

  - `bindings/pydottalk/src/module.cpp` (the pybind glue), plus three shared
    support TUs: `src/cli/order_state.cpp`, `src/common/path_resolver.cpp`,
    `src/common/path_state.cpp`;
  - and LINKS the core libs `xbase` (+ `memo`, optional `xindex`).

It does NOT compile or link the `src/cli/cmd_*.cpp` command layer. That is the
decoupling the maintainer described: two consumers of the same core, not one
depending on the other.

Consequence for a catch-up: the missing verbs are NOT uniform in cost.

  - deleteCurrent is already a core `DbArea` method (bound). RECALL (clear the
    deleted flag) is very likely a sibling core primitive -- a candidate CHEAP
    `.def()` add, no CLI dependency.
  - LOCK/UNLOCK live in the core `xbase::locks` layer (per CLAUDE.md, the engine
    has cross-process cooperative locking). Bindable, but needs new `.def()`s and
    possibly linking the locks TU -- MODERATE.
  - PACK/TURBOPACK and COMMIT/ROLLBACK/TABLE_BUFFER are implemented in the CLI
    command layer (`cmd_pack.cpp`, `cmd_commit.cpp`) on top of core. Exposing them
    without dragging the shell in means REIMPLEMENTING the primitive against core
    -- HEAVY, and it would erode the very decoupling this CMakeLists protects.

So "make pydottalk timely" is really: cheaply add RECALL, reasonably add
LOCK/UNLOCK, and think hard before PACK/COMMIT (those may belong to the engine
DotScript surface, not the binding).

## Consequences for the CRUD (design inside the confirmed surface)

  1. Soft-close (the default delete) is pure field writes -- fully supported and
     reversible. Bi-temporal tables stamp VTHRU + bump ROWVER; status-enum tables
     set the terminal code (+ a close epoch where the schema has one). This is the
     safe, dogfood-aligned default.
  2. --purge maps to deleteCurrent (the tombstone). It is honest to call this a
     mark, not a physical delete: the row stays in the file, hidden from
     scan_records(skip_deleted=True). It is IRREVERSIBLE via pydottalk (no RECALL)
     and does NOT reclaim space (no PACK). Both true undelete and compaction are
     engine CLI steps (RECALL, PACK) -- a maintainer handoff.
  3. No locking => the CRUD is single-writer only. The portal (metadata/portal)
     and identity (metadata/identity) tables have no other live writer, so
     maintainer-run CRUD is safe there. The bbs tables (metadata/bbs) ARE written
     by dottalk_bbsd; the CRUD must refuse or loudly guard bbs writes unless the
     daemon is confirmed stopped (Stop-ScheduledTask 'DotTalkBBSD').
  4. No COMMIT/ROLLBACK => operate one row at a time; report partial progress
     rather than promising atomic batches.
  5. Validation is Python-side: reject unknown fields, enforce N/C/L widths and the
     documented enum ladders before writeCurrent.

## The open decision the findings reopen

"Python over pydottalk" was chosen before we confirmed the binding has no locking,
no recall, no pack, and no commit. For concurrency-sensitive or destructive writes,
the safer surface is the ENGINE's own DotScript (LOCK ... REPLACE/DELETE/RECALL ...
COMMIT / PACK), run via datarun.ps1, because it takes real locks and can undelete
and compact. Two coherent postures:

  - A. pydottalk-direct, scoped safe: CRUD writes only portal + identity as a
    single writer; soft-close default; --purge tombstone with a loud
    irreversibility warning; bbs writes refused while bbsd may run. Simple, runs on
    the maintainer box today.
  - B. hybrid: pydottalk for reads and portal/identity soft edits; emit engine
    DotScript for anything that needs a lock, an undelete, or a pack (all bbs
    writes, all --purge). Safer for the shared store; a bit more machinery.

Either way, the standing recommendation is to file a binding-catch-up item so
pydottalk exposes LOCK/UNLOCK, RECALL, PACK, and COMMIT/ROLLBACK -- the review
confirms the binding, not the engine, is what lags.

## Repairs / findings (runtime-observed)

- **R-APPEND-BLANK (catalog-vs-runtime drift).** The command catalog / HELP document
  `APPEND BLANK` (command `APPEND_BLANK`, syntax "APPEND BLANK") as runtime syntax,
  but the runtime `APPEND` parser REJECTS the `BLANK` token -- it prints usage and
  does NOT append. The silent hazard: a caller that issued `APPEND BLANK` then runs
  `REPLACE`s, which land on the CURRENT (last) record instead of a new one -- a quiet
  clobber, not an error. Bare `APPEND` correctly appends one blank row (proven:
  `mem_proof.dts`, and a RAM dry run on build 64a0136d, 2026-08-04). The pydottalk
  binding `append_blank()` works at the C++ level, so this is a REPL-surface drift
  only. Repair options: (a) make the `APPEND` parser accept `BLANK` as a no-op alias
  for bare `APPEND`; or (b) correct the command catalog/HELP so `APPEND BLANK` is not
  documented as runtime syntax. Caught by the CRUD `--emit --ram` dry run, which is
  exactly what it is for. crud.py emits bare `APPEND`.

## Status / next

Findings confirmed and grounded. Awaiting the A-vs-B posture call before the CRUD
write paths are authored. Reads and the soft-close path are identical under both.
