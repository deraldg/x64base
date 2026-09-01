# Workspaces and MiniDBs

```yaml
page_id: USER-WS-01
title: Workspaces and MiniDBs
audience: knows xBase, new to DotTalk++
status: DRAFT
last_verified: 2026-09-01
```

## Who this is for

You already know `USE`, `SELECT`, `SET ORDER`, `REPLACE`, and what a work area
is. Nothing here re-teaches those. This covers the two things DotTalk++ adds
that have no xBase equivalent, and it is organised around the mistakes people
actually make rather than around the verb list.

`HELP` and `CMDHELP` own syntax -- what a command accepts, spelled exactly.
Read them for that. Read this for what the commands MEAN together, where they
surprise you, and how to get out of it.

## What changed in this revision (2026-09-01)

If you read the 2026-08-29 draft, four things are different and one of them is
a correction rather than an addition.

1. **`WORKSPACE OPEN` is additive, and this page said otherwise.** The old text
   called it "replacement-style". It has not behaved that way since
   2026-08-26. See Part 1. If you wrote scripts that close defensively before
   every open, they still work -- they are just carrying a precaution they no
   longer need.
2. **Nesting is durable.** `NEW ... UNDER` now records containment in the
   catalog, so a parent-child relationship survives the process. Part 2 has the
   model, the refusal you will meet, and a worked session near the end.
3. **Adding a field to an indexed table stops the index opening**, loudly and
   recoverably. Part 6.
4. **Catalog writes reach the disk before the prompt returns.** You will never
   see this working; it is documented so you know what to expect after a crash.

---

## Part 1 -- Workspaces

### The model in one paragraph

A workspace is a NAMED GROUP OF WORK AREAS. You are always in one. It is called
`DEFAULT`, you did not create it, and it cannot be destroyed. `WORKSPACE NEW
<name>` makes another; `WORKSPACE SWITCH <name>` changes which one is current.
Areas do not move between workspaces, and there is no verb to move one.

### The rule that explains most surprises

> **An area joins whichever workspace is CURRENT when the area is OPENED.**

The model is SWITCH-then-open, never open-then-assign. Read that twice, because
almost every confusing session comes from doing it in the other order.

The trap, and it is a quiet one:

```
    USE STUDENTS               && STUDENTS opens here, in DEFAULT
    WORKSPACE NEW PAYROLL
    WORKSPACE SWITCH PAYROLL
    USE STUDENTS               && "already open in current area 0"
```

That second `USE` is a **no-op for membership**. It prints that the table is
already open and returns; the area keeps the workspace it already had.
`PAYROLL` now holds ZERO areas while looking, at a glance, like it holds
STUDENTS. A scoped `WORKSPACE SAVE` at that point writes an EMPTY posture --
and it warns you, but only in console text.

Correct order:

```
    WORKSPACE NEW PAYROLL
    WORKSPACE SWITCH PAYROLL
    USE STUDENTS               && opens HERE, so it joins PAYROLL
```

If a table is already open somewhere and you want it in the workspace you are
standing in, CLOSE it first and open it again -- or open a SECOND handle on
purpose with `USE <table> AGAIN`, which is what that verb is for.

### Two ways in, and the difference is GRANULARITY

This page said until 2026-09-01 that `OPEN` is replacement-style and resets
area membership. **That was wrong, and it had been wrong since 2026-08-26.**
The correction is worth stating plainly because the old rule made people
defensively close things they did not need to close.

- `WORKSPACE OPEN <dir>` opens a DIRECTORY of tables.
- `WORKSPACE ADD <file.dbf>` opens ONE table.
- `WORKSPACE LOAD <name>` opens a saved POSTURE.

**All three are ADDITIVE. None of them closes anything.** They differ in how
much they open at once, not in whether they destroy your session. If you want
replacement, COMPOSE it and say so:

```
    WORKSPACE CLOSE ALL
    WORKSPACE OPEN <dir>
```

The runtime carries the same correction in `WORKSPACE USAGE`, dated. If you
read an older script that closes before every open, it is not wrong -- it is
just carrying a precaution it no longer needs.

`WORKSPACE OPEN <dir>` scans a directory and names the workspace after the
directory LEAF. `WORKSPACE OPEN <dir> AS <name>` overrides that name, which you
need when two directories share a leaf. Note that `AS` is also a MINTING form
-- see Part 2, because it writes a durable row exactly like `NEW` does.

### Closing is scoped now

Bare `WORKSPACE CLOSE` closes **your** workspace's members. `WORKSPACE CLOSE
ALL` closes everything everywhere and is the only form that also reconciles
areas nobody registered. With one workspace open the two are identical; with
two open, the difference is whether you just closed a colleague's work.

`SET RECURSION ON|OFF` -- a `SET` verb, not a `WORKSPACE` one -- decides
whether a close DESCENDS into nested workspaces. `OFF` does not forbid nesting;
it makes nested workspaces parallel rather than swept together, and a skipped
child is always reported rather than silently left open.

### One file, two workspaces

This is the case a global registry cannot represent, and DotTalk++ supports it.
A bare `USE` is REFUSED for a file that already has a work area; `USE <table>
AGAIN` is the explicit way to ask for a second handle. Closing one workspace
must not release the other's handle.

When a name resolves to more than one open area you will see the ambiguity
ledger fire:

```
    NAME: 'STUDENTS' is open in 2 areas (ws 1 area 1, ws 1 area 3);
    resolved to area 1. Qualify the name -- first-wins is a migration step.
```

That is the ledger WORKING, not an error. But treat it as a warning about your
own script: first-wins is a migration step, not a promise. Qualify the name.

### Where things actually are

- `WORKSPACE` (bare) lists current open work areas.
- `WORKSPACE ALL` lists all area slots, including closed ones.
- `WORKSPACE REGISTRY` reports RUNTIME membership -- which areas belong to
  which workspace right now, plus current handle, recursion, parent and depth.

`REGISTRY` is not the catalog. `REGISTRY` answers *what is open*; the catalog
answers *what has been saved*. Confusing the two is the second most common
mistake after the ordering rule above.

---

## Part 2 -- Identity, and the residue you leave behind

### `NEW` writes to disk, and this surprises everyone

`WORKSPACE NEW` is DURABLE, not runtime-only. It either ADOPTS the durable
identity its name already means, or writes a birth row to mint a fresh one. So
a workspace can be referred to from outside this process without ever being
SAVED. `WORKSPACE OPEN <dir> AS <name>` mints the same way.

Practically: **every `NEW` you type at the prompt writes a row to the
production catalog.** A regression spec is bracketed into a scratch catalog;
nothing brackets a person.

Watch for the word `ADOPTED` in the output. It means the name already had a
live row and you have inherited that identity rather than starting fresh --
usually because a previous session did not clean up.

### Retire and remove are different verbs

| verb | what it does | rows |
|---|---|---|
| `WORKSPACE DESTROY <name>` | RETIRES the identity: supersedes the live row so the name has no live row | all rows stay and stay readable |
| `WORKSPACE DELETE <name>` | flags rows deleted AND superseded | rows stay on disk permanently, hidden under `SET DELETED ON` |
| `WORKSPACE PURGE <name>` | retained ALIAS of DELETE | -- |

A destroyed workspace leaves a RECORD, not a hole. After `DESTROY`, a later
`NEW` of that name mints a FRESH id instead of adopting the old one. What stops
an adoption is SUPERSEDED, not the delete flag.

`PURGE` is misnamed and kept only for compatibility. In xBase the pair is
exact: DELETE flags and the row is ignored, PACK removes it. This verb is on
the flag side, so "purge" belongs to the other one. Prefer `DELETE` in anything
new.

**There is deliberately no `WORKSPACE PACK.`** Allocation is `max(WS_ID)+1`
derived from surviving rows, so deleted rows MUST keep being counted. Pack this
catalog and the next `NEW` would inherit a deleted workspace's identity.

### `UNDER` declares a parent, and the catalog remembers it

`WORKSPACE NEW <name> UNDER <parent>` nests one workspace inside another, and
since 2026-09-01 that containment is DURABLE: the catalog row records the
parent's identity and the child's depth, so nesting survives the process
instead of living only in this session's registry.

Two things follow that you will meet at the prompt.

**The catalog records the parent's DURABLE id, not the handle you typed.**
`REGISTRY` shows `parent 2` because 2 is a slot in this process's table; the
catalog stores `276`, the parent's real identity. They are different numbers
for the same parent and both are correct. A handle does not survive a restart;
the durable id is the thing that does.

**A parent that has no durable identity is REFUSED, not silently flattened.**

```
    . WORKSPACE NEW DURX UNDER DEFAULT
    WORKSPACE NEW: refused -- the parent workspace has no durable identity yet,
      so its containment cannot be recorded.
      A parent must be durable before a child can name it. Nothing was created.
```

This is the answer to "why can I not nest under DEFAULT?" -- and note the
refusal says nothing about DEFAULT. It is a general rule: a container that
cannot be NAMED cannot be RECORDED. DEFAULT simply happens to be the one
workspace with no catalog row, because you never declared it. Everything you
create with `NEW` is durable from birth and can be a parent immediately.

"Nothing was created" is literal. No catalog row is written and no runtime
handle is left behind; `REGISTRY` afterwards shows exactly what it showed
before.

### Four kinds of "name", and which ones survive a restart

Most confusion in this part of the system is one question wearing four hats:
*what exactly am I holding when I hold a workspace?* The answer is that there
are four different identities in play, they have different lifetimes, and
mixing them up is what produces a script that works today and reads nonsense
tomorrow.

| what you hold | where the truth lives | survives a restart? |
|---|---|---|
| **session handle** (`handle 2`) | this process's table | NO |
| **durable id** (`WS_ID 276`) | the catalog chain | YES -- it IS the persistence |
| **derivable id** (depth, membership) | computed from something else | not stored, recomputed |
| **composition** (a name plus a path, say) | its parts | only as long as its LEAST durable part |

Two practical consequences.

**Never write a handle into anything that outlives the process.** A handle is a
slot number. Next run, slot 2 is somebody else's workspace, and a script that
says `WORKSPACE SWITCH 2` will cheerfully switch to the wrong thing rather than
fail. Address workspaces by NAME. The engine does the same thing internally:
when `UNDER` records a parent it converts the handle you typed into the
parent's durable id before writing it down, which is why the two numbers differ
in the output.

**A composition inherits durability; it never confers it.** If you build a
label out of a workspace name and something transient, the label is only as
durable as the transient half. This is the reasoning behind the `UNDER`
refusal: a child's containment is a composition of "me" and "my parent", so it
cannot be more durable than the parent, and a parent with no durable identity
would produce a containment record that means nothing on the next run.

### The catalog is written to disk before the prompt comes back

`WORKSPACE NEW` does not just intend to write a row -- as of 2026-09-01 the
write is pushed all the way to the physical disk before the command returns,
with the memo sidecar synced before the table so the two can never disagree
about which one is newer.

Before this, the engine asked the operating system to write and the OS was free
to hold it in cache. A power loss between `NEW` and the next flush could leave
a catalog that had lost its most recent rows -- and worse, could leave the
sidecar and the table disagreeing.

You will not see this. That is the point. It is recorded here so that if you
ever compare a catalog against a backup after a hard crash, you know the answer
is supposed to be "the rows are there," and a missing row is a bug worth
reporting rather than an expected cost of pulling the plug.

### `DESTROY` refuses three things, and never cascades

1. `DEFAULT` -- an area belongs to exactly one workspace and there is no null
   one, so `DEFAULT` must outlive every other workspace.
2. A workspace still HOLDING AREAS -- close them first.
3. A workspace with NESTED CHILDREN -- destroy the child first.

Because it never cascades, `DESTROY` can never be the thing that silently
orphaned an open area.

### The trap you will hit on your second day

You minted a workspace yesterday and did not retire it. Today:

```
    . WORKSPACE DESTROY PAYROLL
    WORKSPACE DESTROY: no such workspace: PAYROLL
```

The name is live in the CATALOG and absent from THIS session. `DESTROY`
resolves through the runtime registry, so it only knows the second. Re-adopt
it first:

```
    WORKSPACE NEW PAYROLL        && reports ADOPTED, same WS_ID, no new row
    WORKSPACE DESTROY PAYROLL    && now it can be retired
```

`WORKSPACE DELETE` reaches a catalog-only head without adoption, because it
refuses only names DECLARED IN THIS SESSION. It is the heavier instrument;
prefer adopt-then-`DESTROY` for ordinary residue so the history stays readable.

### Look before you leave

```
    do l1census      && read-only: rows, superseded, and LIVE HEADS by name
    do l1verify      && the scratch-root arm
    do l1cleanup     && retires names, and it WRITES -- read it before running
```

A LIVE HEAD is a name still holding a live row, which the next `NEW` of that
name will adopt. Some are intentional and should stay: `mcc_x64`, `mcc_v3`,
`sess_cursor`, `mcc_db`, `mcc_minidb_memo` (real saved workspaces) and `x64`,
`x32` (directory identities, where adoption IS the feature). Anything else live
is probably yours.

**Retire what you declared before you leave. Children first.**

### A workspace name cannot be reclaimed within a session

`CLOSE ALL` releases every area, and afterwards the registry STILL lists every
workspace at members 0. There is no DROP or REMOVE for the runtime handle. So a
script that declares workspaces is idempotent per PROCESS, not per session --
run it once, or restart rather than trusting a second pass.

---

## Part 3 -- Saving: a posture is not a database

Three things can be saved, and the difference is the PAYLOAD.

| form | line one | what it carries |
|---|---|---|
| `WORKSPACE SAVE <file>` | `DTSHEMA 2` | the DEFINITION -- AREA, RELATION, KEY. Relative paths, no cursor. **Portable, and the one to commit.** |
| `WORKSPACE SAVE <file> V3` | `DTSHEMA 3` | the SESSION -- adds FLAVOR / DBFROOT / IDXROOT / LMDBROOT and CURSOR / CURRENT. Machine-specific BY NATURE. |
| `WORKSPACE SAVE <name> MEMO MINIDB` | `MINIDB 1` | a CONTAINER whose payload IS the database. The table bytes ride along. |

`MEMO` means the artifact is stored as a row in the workspace catalog instead of
as a file. `WORKSPACE CATALOG` lists those rows read-only, and the `FMT` column
is exactly the table above -- it is the cheapest way to check what you actually
saved.

Two things worth internalising:

- **A posture is not byte-stable and is not meant to be.** It records an
  INSTANCE, so each save carries its own stamp. Byte-identity belongs to
  MINIDB, which carries table bytes.
- **MINIDB implies V3.** The embedded posture has to be self-locating to
  survive being re-pointed at RAM.

Saving a name again SUPERSEDES rather than overwrites, so the catalog keeps its
own history and superseded rows retain their bytes.

---

## Part 4 -- MiniDBs

A MiniDB is a whole small database carried inside a catalog row. It exists so a
working set can be moved, hydrated into RAM, worked on, and returned to disk.

### Hydrating one

```
    WORKSPACE LOAD mydb MEMO            && REFUSED, by design
    VDISK MOUNT                         && or: DO mem
    WORKSPACE LOAD mydb MEMO RAM        && hydrates, zero disk reads
```

The plain form refuses on purpose: a MINIDB's tables have no disk home, and
standing up empty areas over missing files is the silent-success failure this
codebase hunts. The refusal names the fix.

A hydrated table is WRITABLE. That is the point -- you work on it in RAM.

### Getting it back to disk

```
    WORKSPACE WRITEBACK mydb TO DBF/outdir WITH INDEXES CONFIRM
```

- `<name>` is REQUIRED, despite some older help spelling it `[<name>]`.
- Enumeration comes from the POSTURE's `AREA` lines, never the session's attach
  order.
- A shortfall ABORTS having written nothing -- empty directories included.
- `CONFIRM` is required to replace existing files; replaced files are kept as
  `<name>.__wbak`.
- `TO <root>` resolves like any path token: absolute stays absolute, separators
  mean DATA-root-relative, a bare name sits in the DBF slot.

**`WITH INDEXES` copies index container BYTES only.** LMDB is not carried --
lmdb is for disks -- so the destination needs `BUILDLMDB` before `SET ORDER` on
a tag will work there. This catches people out; the bytes arrive and the order
does not.

### Reading it back honestly

If you want to prove a writeback worked, read the tables AFTER unmounting the
RAM disk. Reading while it is still mounted proves the mount, not the return
leg.

---

## Part 5 -- Loading, and what a load will not do to you

**`LOAD` closes nothing at all**, and it refuses a shortfall. Declared members
are resolved and probed before anything is opened, so a load that cannot
complete leaves your current session exactly as it found it. A load that CAN
complete also leaves it standing -- the saved tables are added alongside what
you already had, into the workspace you are standing in.

```
    WORKSPACE LOAD: ABORTED -- the posture declares 2 table(s); 1 cannot be found:
      ? D:\...\MISSING.dbf
    Nothing was closed and nothing was loaded; the current workspace is untouched.
```

`PARTIAL` opts back into permissive behaviour explicitly, and restores what it
can. Use it deliberately, not reflexively.

**Indexes are NOT part of the probe.** They are derived and rebuildable, and the
choice travels in the posture, so a missing index does not refuse a load.

### After a load, address tables BY NAME

> **A posture's AREA numbers are KEYS, not addresses.**

A table saved from `AREA 8` will land wherever a slot is free -- typically
`0..N-1`. The load says so when it happens:

```
    WORKSPACE LOAD: 1 table(s) landed at an engine slot other than the number
    recorded in the posture. The posture's AREA numbers are KEYS, not addresses;
    use WORKSPACE REGISTRY to see where they are.
```

So write `SELECT STUDENTS`, not `SELECT 8`. This matters more than it sounds:
a marker or a report over a CLOSED area does not error -- it returns a verdict
whose polarity depends on the operator you used -- so slot-addressed checks can
read GREEN over nothing at all.

---

## Part 6 -- Orders inside a workspace

Full treatment is in the developer manual chapter on indexing; this is only
what bites you in a workspace context.

- The order you have set TRAVELS IN THE POSTURE -- the `AREA` line carries the
  tag -- so it survives a save/load round trip. If you lose it, the walk
  silently goes physical, which looks like data in the wrong order rather than
  like an error.
- Default index policy is flavor-aware: true x64/v128 uses CDX (LMDB), classic
  VFP/v32 uses CNX.
- CDX and CNX are index MANAGERS, not just containers:
  `CREATE`, `ADDTAG <name>`, `DROPTAG <name>`, `INFO`, `TAGS`.
- **A tag name IS a field name.** `ADDTAG` requires an open table and refuses a
  name that is not one of its fields.
- Building differs by family: CDX builds with `BUILDLMDB` (`BUILDLMDB CLEAN
  YES` to rebuild an existing one); CNX builds with `REBUILD`. `REINDEX`
  dispatches to whichever your table's flavor implies.
- **Adding a field to an indexed table stops the index opening.** A CDX
  carries a fingerprint of the table it was built against -- kind, version,
  record length, field count and a field-layout hash -- and `openCdx` REFUSES
  on a mismatch. `FIELDMGR APPEND` changes the record length and the field
  count, so afterwards `SET ORDER` fails with a `metadata mismatch` naming both
  sides. Your DATA is intact; only the index refuses. Rebuild it
  (`BUILDLMDB CLEAN YES` for CDX, `REBUILD` for CNX) and the order comes back.
  This is deliberate: a stale index that ANSWERS is worse than one that
  refuses, because nothing tells you the answer changed.
- **Under RAM there is no disk for `.mdb` files**, so CDX falls back to sorted
  in-RAM indexes and does not use LMDB. This is why writeback's contract says
  the destination needs `BUILDLMDB`.

### What the index refusal actually looks like

Worth seeing once, because the message is long and the important half is at the
end of it.

```
    . SET ORDER TAG CLBL
    SET ORDER: CDX TAG 'CLBL' (ASC)

    . FIELDMGR APPEND FMNEW N(4)
    FIELDMGR APPEND: field appended successfully [WARNING: attached index is
      now STALE and will refuse to open until rebuilt -- the table's reclen and
      field count no longer match the container's fingerprint]

    . SET ORDER TAG CLBL
    SET ORDER: openCdx: metadata mismatch
      [table reclen=21, fields=3, hash=9862171499522484533] vs
      [cdx   reclen=17, fields=2, hash=10505654778912424209]
```

Read the two bracketed groups as before-and-after. The table now has 3 fields
and a 21-byte record; the index was built against 2 fields and 17 bytes. That
is the whole diagnosis.

Two follow-on points that are easy to get wrong:

**The warning only fires if the index is ATTACHED.** If you never issued
`SET ORDER` in this session, the append proceeds with no warning at all -- and
invalidates the on-disk container exactly the same way. You find out later, at
the next `SET ORDER`, which is loud but not where you were looking. So after
any `FIELDMGR APPEND`, rebuild the table's indexes whether or not you were
warned.

**A refusal that names identical numbers means something different.** If the
record length and field count MATCH and only the hash differs, the message adds
a clause saying the record shape is unchanged and the field LAYOUT is not --
a rename, a same-width type change, or a reordering. Same remedy, rebuild; but
it tells you the table's columns moved rather than grew.

---

## A first session, end to end

```
    WORKSPACE NEW TRAINING
    WORKSPACE SWITCH TRAINING     && switch BEFORE opening
    SELECT 0
    USE STUDENTS
    SET ORDER TO LNAME

    WORKSPACE REGISTRY            && confirm TRAINING actually holds the area

    WORKSPACE SAVE train01 MEMO V3
    WORKSPACE CATALOG             && check FMT says what you expected

    WORKSPACE CLOSE
    WORKSPACE LOAD train01 MEMO
    SELECT STUDENTS               && BY NAME, not by slot
    TOP

    WORKSPACE CLOSE
    WORKSPACE SWITCH DEFAULT
    WORKSPACE DESTROY TRAINING    && retire what you declared
```

`WORKSPACE REGISTRY` after the open is not ceremony. It is the one cheap check
that catches the ordering mistake in Part 1 before it costs you an empty
posture.

---

## A nested session, end to end

The first session above uses one workspace. This one builds a parent and a
child, proves the containment landed in the catalog rather than only in this
process, and takes it all down again in the right order.

```
    WORKSPACE NEW COLLEGE
    WORKSPACE NEW REGISTRAR UNDER COLLEGE
```

Read the two replies carefully, because they are not saying the same thing:

```
    WORKSPACE NEW: handle 2  name COLLEGE    parent 0  depth 0  WS_ID 276
    WORKSPACE NEW: handle 3  name REGISTRAR  parent 2  depth 1  WS_ID 277
```

`COLLEGE` reports `parent 0`, which is a DECLARATION that it has no container
-- not a gap, and not "unknown". `REGISTRAR` reports `parent 2`, the session
handle, and `depth 1`. What went into the catalog for `REGISTRAR` is
`PARENT_ID 276` -- `COLLEGE`'s durable id, not its handle. Same parent, two
numbers, two lifetimes.

Now fill the child and confirm membership before trusting it:

```
    WORKSPACE SWITCH REGISTRAR
    SELECT 0
    USE STUDENTS
    SET ORDER TO LNAME

    WORKSPACE REGISTRY
```

```
    WORKSPACE REGISTRY (runtime membership)
      current handle : 3
      recursion      : ON
      workspaces     : 3
      handle 1  name DEFAULT    parent 0  depth 0  members 0  WS_ID (none yet)
      handle 2  name COLLEGE    parent 0  depth 0  members 0  WS_ID 276
      handle 3  name REGISTRAR  parent 2  depth 1  members 1  WS_ID 277
```

Three things in that block are worth pointing at.

`DEFAULT` shows `WS_ID (none yet)`. It has no catalog row because you never
declared it, which is exactly why nothing can nest under it.

`COLLEGE` shows `members 0`. A parent does not gain its children's areas.
Containment is about workspaces, not about work areas -- `COLLEGE` contains
`REGISTRAR`, and `REGISTRAR` contains the area.

`recursion : ON` decides what a close will do next.

Taking it down, and the ORDER is not optional:

```
    WORKSPACE CLOSE               && closes REGISTRAR's members only
    WORKSPACE SWITCH DEFAULT
    WORKSPACE DESTROY REGISTRAR   && child first
    WORKSPACE DESTROY COLLEGE     && now the parent is childless
```

Reverse those last two and the second is refused:

```
    WORKSPACE DESTROY: refused -- COLLEGE still has nested children.
```

That refusal is doing you a favour. A cascading destroy would retire identities
you never named, and the rows it left behind would describe a tree that no
longer exists.

### What the catalog looks like afterwards

Both rows are still there and still readable -- `DESTROY` supersedes, it does
not delete. So the record of the nesting outlives the nesting:

```
    276  COLLEGE     PARENT_ID='0'    TREE_DEPTH='0'   SUPERSEDED='1'
    277  REGISTRAR   PARENT_ID='276'  TREE_DEPTH='1'   SUPERSEDED='1'
```

A `PARENT_ID` of `0` means one thing and one thing only: **no container was
declared**. It does not mean "unknown", it does not mean "DEFAULT", and it does
not mean "not filled in yet". If you are reading rows written before
2026-09-01 you may find the column BLANK -- that is genuinely "this row predates
the feature", and blank and `0` are deliberately different so the two cannot be
confused.

`TREE_DEPTH` is the distance from the root: `0` for a workspace with no
declared parent, `1` for a child, and so on. It is computed from the parent
chain at the moment the row is written, so it cannot drift away from
`PARENT_ID` later.

---

## Traps, collected

| symptom | cause | fix |
|---|---|---|
| Workspace holds 0 areas, save writes an empty posture | table was opened before the SWITCH; `USE` on an already-open table does not change membership | CLOSE and re-open inside the workspace, or `USE <table> AGAIN` |
| `no such workspace` on a name you know exists | it is a catalog-only live head from a previous process; DESTROY reads the runtime registry | `WORKSPACE NEW <name>` (adopts), then `DESTROY` |
| `NEW` says ADOPTED when you expected a fresh one | the name still had a live row | retire it first, or accept the inherited identity |
| Rows in the wrong order after a load | the tag did not survive, or was never set | check the posture's AREA line; re-`SET ORDER` |
| `SET ORDER` fails after a writeback | `WITH INDEXES` copied bytes, not LMDB | run `BUILDLMDB` at the destination |
| Plain `LOAD` refuses your MiniDB | by design -- its tables have no disk home | `VDISK MOUNT` then `LOAD ... MEMO RAM` |
| A check reads green over nothing | slot-addressed after a load; the area is closed | address BY NAME |
| Catalog fills with rows you did not save | every `NEW` and every `OPEN ... AS` mints | `do l1census`, then adopt-and-destroy |
| `NEW ... UNDER DEFAULT` refused | DEFAULT has no catalog row, so it cannot be named as a container | nest under a workspace you declared; every `NEW` is durable from birth |
| `SET ORDER` fails right after `FIELDMGR APPEND` | the added field changed the record length, so the index fingerprint no longer matches | rebuild the index; the data is untouched |
| You closed everything before an `OPEN` out of habit | `OPEN`/`ADD`/`LOAD` have been additive since 2026-08-26 | only close when you actually mean to replace |

---

## Where to look next

**Look a verb up before you reason about it.**
`docs/manuals/command_reference/command_reference_guide_v1.csv` is generated
FROM THE HANDLERS and carries a row per command with usage, notes, examples and
related verbs. It is the first stop, not the last. It does age, and the
staleness test is mechanical: the row names its `source_path`, so compare that
handler's modification date to the guide's. Handler OLDER than the guide, trust
the row. Handler NEWER, take the row as a strong hint and confirm that one
claim in the source. Read it with a CSV reader, not by eye -- fields span
lines.

- `dottalkpp/data/scripts/workspace_multi_demo.dts` -- a narrated tour that
  asserts nothing. Read it first; run it second.
- `dottalkpp/data/scripts/workspace_multi_regression.dts` -- the gate. Read it
  when you want to know what is actually guaranteed.
- `dottalkpp/data/scripts/workspace_minidb_multi_shakedown.dts` -- the seam
  between workspaces and MiniDBs, exercised end to end.
- `dottalkpp/data/scripts/workspace_purge_regression.dts` -- the identity
  ladder: what each retire/remove verb refuses, and why.
- `docs/maintenance/RAM_MINIDB_MEMO_WORKSPACE_OPERATIONS_V1.md` -- the operator
  manual for the RAM/memo lane.
- `docs/maintenance/MEMO_RESIDENT_MINIDB_V1.md` -- mechanism and design.
- `dottalkpp/data/scripts/fieldmgr_append_live_cdx_probe.dts` -- the index
  invalidation in Part 6, measured rather than described: it builds a table,
  builds a tag, reads the keyed order, appends a field, and reads it again.
- `docs/manuals/developer/dev/dev-12-relations-workspaces-and-tuple-traversal.md`
- `docs/manuals/developer/dev/dev-09-indexing-inx-cnx-cdx-lmdb.md`

`HELP` and `CMDHELP` remain the authority on syntax. Where this page and the
generated help disagree, the generated help is right about WHAT the command
accepts and this page is right about WHY -- and one of them needs fixing, so
say so.
