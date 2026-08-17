---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260817-COWORK-003
  recorded_at_utc: 2026-08-17T23:10:00Z
  agent:
    provider: Anthropic
    product: Claude (Cowork)
    model: claude-opus-5
    access_mode: local_write
  session:
    id: not_exposed
    chat_reference: not_exposed
  project:
    id: project.x64base.runtime
    root: D:/code/ccode
  git:
    branch: development
    baseline_commit: a148b2ee7
  authorization:
    requested_by: maintainer (member.derald), in-session, "write this up as a proposal for this lane and file it"
    scope: >
      AIF-119 M2. Proposes binding the index surface into pydottalk, splits the
      work into a correctness half and a feature half, and records three engine
      seams found while scoping it. Proposal only; nothing implemented.
  report:
    path: docs/maintenance/AIF119_M2_INDEX_BINDING_PROPOSAL_V1.md
    kind: proposal
---

# AIF-119 M2 -- binding the index surface into pydottalk

Status: proposal, review-needed. Owner: member.derald.
Author: member.ai.claude.cowork. Date: 2026-08-17.
Lane: **AIF-119** (`pydottalk-co-sourced-product`).
Charter: `AIF_119_PYDOTTALK_CO_SOURCED_PRODUCT_LANE_V1.md`, milestone **M2**.
Related: OI-005 (execution route), OI-007 (re-measure index modes).

## The question the maintainer asked first

**Do we need indexing to work for pydottalk? Does it help? Is it useful?**

Answered honestly, the request splits in two, and only one half is needed now.

**Read side -- seek, ordered iteration -- NOT needed yet.** The tables pydottalk
touches are 8 to 51 rows (portal SYS* as listed by the maintenance console). A
scan is instant at that size. Nobody has asked for `seek` from Python: the AI
portal records zero index evidence across four `launcher_pydottalk` proof runs,
and the only registered pydottalk proof is APPEND BLANK. Building a query
surface now would be building for a hypothetical.

**Write side -- index maintenance -- NEEDED, and it is a correctness guard
rather than a feature.** Measured 2026-08-17:

- `dottalkpp/data/metadata/portal/` holds 5 DBFs and **4 CDX files beside them**:
  `SYSPROOF.cdx`, `SYSRUN.cdx`, `SYSRUNLANE.cdx`, `SYSTASK.cdx`.
- Those are exactly the tables the maintenance console lists, and the console
  writes through the binding (`tools/dbf/crud.py:513` imports pydottalk;
  `tools/dbf/maint_server.py:359` "EXECUTE via pydottalk").
- The binding's write path is `module.cpp:298` calling `DbArea::set()` -- the raw
  record-buffer poke. It takes no record lock, runs no index maintenance, and
  fires no trigger.

**It has not fired yet, and that is luck plus one good default.** Every DBF in
that directory and its CDX share an mtime of `08-04 20:14`, so nothing has been
written since the indexes were built. What has held the line is the console's
own posture: writes are preview-only unless `-EnableWrite` is passed, behind the
token boundary landed in `6a931ab3d`. **This is therefore the cheapest possible
moment to fix it: before the first write, not after the first divergence.**

## What is already in place

Nothing needs adding to the build. Measured on the LEGACY preset:

- `xbase.lib` (15 sources) already carries `ramfs`, `index_hooks`,
  `trigger_hooks`, `xbase_locks`, `cursor_hook`.
- `xindex.lib` (21 sources plus `src/cnx/cnx_document.cpp` and
  `src/cnx/cnx_file.cpp`) already carries `attach`, `index_manager`,
  `cnx_backend`, `key_codec`, `index_tag`, `simple_index`,
  `simple_index_build_and_save`, the B+ tree and the CDX backends. Only
  `lmdb_backend.cpp` is filtered out.
- `xindex::ensure_manager(area)` installs the xbase index hooks once
  (`std::call_once`) and registers an `IndexManager` per area. From that point
  `DbArea::replaceFieldStored` maintains the index automatically, because
  `index_hooks::capture` / `apply_replace` route through `manager_if_attached`.
- `DbArea::close()` already calls `index_hooks::detach`, so teardown is handled.

The module simply never references any of it, so the linker discards the whole
archive. See `proof.build.index_mode_changes_nothing_shipped`.

## Proposed scope, in two phases

### Phase A -- the correctness half (small, do first)

1. Bind **`DbArea::replaceFieldStored`** as the Python write path and stop using
   raw `set()` for field writes. This alone brings record locking, index
   maintenance and data triggers to every Python write.
2. Expose **`xindex::ensure_manager`** so a caller can attach an index manager
   to an open area, and expose `maintainsIncrementally()` so a caller can ask
   the policy question BEFORE writing rather than discovering it after.
3. Surface the **tri-state** (see below). Non-negotiable, for reasons in the
   hazards section.
4. Keep raw `set()` available but rename it to say what it is, so nobody reaches
   for it by accident.

Phase A is expected to make `lean-none` FAIL TO LINK, which is the desired
signal: it is the first moment the three index modes stop being interchangeable.
OI-007 should be re-measured and closed at that point.

### Phase B -- the query half (larger, only if wanted)

`index_seek(key)` and `index_range(low, high)` over `IndexManager::seek` /
`scan`, returning a Python iterator of `(key, recno)`; optionally `seek()` on
the area as a navigating wrapper. Defer until something actually needs it.

## API decisions, and why

**Naming: `index_seek`, not `seek`.** `IndexManager::seek(Key)` returns a
`unique_ptr<Cursor>` and does NOT move the area. The house already has both
verbs and distinguishes them in its own usage contracts:

| command | `effect:` | `mutates:` |
| --- | --- | --- |
| `SEEK` | navigate | cursor |
| `INDEXSEEK` | seek | **cursor-temporary**, "restoring the caller's cursor" |
| `FIND` | locate | cursor |
| `LOCATE` | locate | cursor locate-state continue-state |

The C++ method is semantically **INDEXSEEK**. Naming it `seek` in Python would
invite a DotScript reader to expect the area to move, read the wrong record, and
get no diagnostic. `find` and `locate` stay out of scope: one is text search,
the other an expression scan, and neither goes through `IndexManager`.

**Shapes bind cleanly.** `IndexKey` is `vector<variant<string,double>>`, so a
compound key is `["WHITE", 3.0]` with no custom caster. `Cursor` is
`first/next/last/prev(Key&, RecNo&) -> bool`, which becomes a Python iterator of
pairs rather than four exposed methods.

**The tri-state on writes.** `replaceFieldStored` returns:

- `false` -- the write did not land
- `true`, `err` empty -- written and index maintained
- `true`, `err` NON-EMPTY -- **written, index NOT maintained**

The third state must reach Python. In the CLI, dropping `err` is survivable
because `cli/table_state` can record it -- `mark_stale_field(area0, field1)`,
dirty and stale flags, the batch/reindex fallback the project used before CNX
could maintain per-record keys. **The binding cannot reach any of that**: that
layer is keyed by `int area0`, a shell work-area slot, and Python has DbArea
objects rather than work areas. `replaceFieldStored`'s own comment says "Stale-
index reporting itself belongs above DbArea" -- and for the binding there is no
above. So `err` is the ONLY surviving carrier, and a binding that swallows it
drops the caller from the realtime model into the batch model without telling
them they are now in it. Proposal: raise on `false`; on `true` with non-empty
`err`, raise a distinct exception naming the field, so "index now stale, reindex
this table" cannot be mistaken for success.

**Pydottalk has no COMMIT/ROLLBACK, and should not pretend to.** Same reason:
buffering is layer 3, keyed by work-area slot. Writes are immediate and direct.
Worth documenting, because anyone who knows DotTalk will assume otherwise.

## Three engine seams found while scoping this

Recorded because they are cheap to state now and expensive to rediscover.

**1. `DbArea` is movable and the index registry is keyed by its address.**
`src/xbase/dbarea_move_ops.cpp` exists solely to define
`DbArea(DbArea&&) = default` and move assignment. `src/xindex/attach.cpp` keys
`unordered_map<const xbase::DbArea*, unique_ptr<IndexManager>>`. A moved DbArea
keeps its data and **silently loses its index manager**: `manager_if_attached`
returns nullptr for the new address, `capture_hook` returns `{}`, and
`apply_replace_hook` returns `true` because `(!before && !after)`. The write
succeeds, `err` stays empty, and the index quietly stops tracking. Unreachable
from the CLI, where work areas own their areas and do not move them. **Very
reachable from a binding.** Mitigation: bind `DbArea` with a stable holder and
no exposed move, or key `ensure_manager` on something that survives a move.
This is the one soft edge in an otherwise clean separation and it should be
decided deliberately.

**2. `cursor_hook::notify` is called by nothing.** Its header says "Called by
DbArea movement/edit methods"; the only occurrence in the tree is its own
definition. `src/cli/shell.cpp:531` registers a callback that can never fire and
clears it at `:778`. `dbarea.cpp`'s layer-boundary note says the notifications
were deliberately removed, so the removal looks intentional and the header
comment is what was left behind. Not urgent; it is a hook that cannot fire with
a comment asserting it does, which will cost someone an afternoon if a future
observer is wired to it.

**3. There is no `is_stale()` on `IndexManager`.** The `stale_` flag lives
inside `cnx_backend`. So the per-write tri-state really is the only signal
available, which is why item 3 of Phase A is non-negotiable rather than a
preference.

## Test plan

All of it runs in a Linux sandbox with no Windows host and leaves nothing on
disk, because the CNX work already supports RAM-resident containers
(AIF-043 V4d: "a path under a mounted ramfs root is served from RAM"), and
`ramfs` is in `xbase.lib`:

1. mount a ramfs root; create a small table in it
2. `CNX CREATE` + `ADDTAG` for one sorted tag
3. `ensure_manager` + `openCnx` + `setTag`
4. assert `maintainsIncrementally()` is true for this backend
5. write through `replace_field`; assert the record moved in index order
6. mutation arm: force the maintenance failure path and assert the tri-state
   raises rather than returning quietly
7. assert `lean-none` fails to link once Phase A lands

Deliberately RAM-only for the first cut: a disk CNX is correct for the session
but "reverts to its last rebuilt order afterwards" until persist-once-at-close
lands, so a disk test would fail for a documented reason unrelated to the
binding.

## What is NOT proposed

- No LMDB. It is a build concern only for this lane; CNX and CDX share the
  backend seam, so proving CNX is the useful step and LMDB follows cheaply.
- No `.inx` / `.idx` change. That lane is not this lane's to touch, per
  `cnx_backend.cpp`: "Their formats and their code are not this lane's to change."
- No COMMIT/ROLLBACK emulation in Python.
- No claim that Phase B is wanted. It is scoped so the decision can be made
  later on evidence rather than now on enthusiasm.

## Effort and sequencing

Phase A is the small half and carries the correctness value. Phase B is the
larger half and carries none until a caller needs it. Estimated a couple of days
for A including the ramfs harness and the mutation arm; B is open-ended and
should be re-scoped when something asks for it.

**Sequencing note:** OI-005 (command-shell execution route) can moot Phase B
entirely. If the ruling there is subprocess `dottalkpp.exe --script`, then
indexed QUERY work belongs to the CLI, which already does it correctly, and the
binding needs only Phase A. Decide OI-005 before starting B.

## The stopping rule (maintainer, 2026-08-17)

**"If it gets that complicated, just use dottalkpp LEAN."**

This is the governing constraint on Phase B and it is recorded as a rule rather
than an opinion, because the failure mode it prevents is the one this lane was
chartered for: a binding that grows until it is a second implementation of the
command surface.

The lean CLI is not hypothetical. `DOTTALK_PRODUCT=LEAN` is a real composition
in `CMakeLists.txt:158-180`, and `windows-lean-table` and `windows-lean-lmdb`
are existing presets. A LEAN build is the engine plus education essentials with
LabTalk, maintenance, external and dev components off. It already has SEEK,
INDEXSEEK, SET ORDER, REINDEX, the buffering layer, COMMIT/ROLLBACK, and the
work-area model -- correct, tested, and maintained by the DotTalk++ SDLC rather
than by this lane.

So the test for any Phase B increment is: **does binding this into Python beat
running the lean CLI against the same data?** For a query surface the honest
answer is usually no. The binding's advantage is in-process access to records
and fields with no serialization boundary; that advantage is real for CRUD and
evaporates for anything that wants the command vocabulary. Phase A is on the
right side of that line -- record locking and index maintenance MUST be
in-process, because they attach to the same DbArea the caller is writing
through. Phase B is on the wrong side unless something specific proves
otherwise.

Stated as a rule for whoever picks this up: **if a Phase B increment starts
requiring work-area state, order state, buffering, or command parsing, stop and
shell out to LEAN instead.** Each of those is a signal that the work has crossed
back over the boundary AIF-119 exists to hold.
