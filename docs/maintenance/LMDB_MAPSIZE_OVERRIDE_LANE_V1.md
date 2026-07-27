# LMDB Mapsize Override -- BUILDLMDB Size Ladder Not Honoured v1

> **RESOLVED 2026-07-27.** Fix applied and verified. `mdb_env_set_mapsize(env_, 0)`
> replaces the hardcoded 1 GiB at both attach sites, so the environment adopts the
> size `BUILDLMDB` persisted instead of having one asserted over it.
>
> **Controlled comparison -- same table, same commands, only the binary differs:**
>
> ```
> SYSARGS pre-fix    33,554,432 -> 1,073,741,824
> SYSARGS post-fix   33,554,432 ->    33,554,432    delta 0
> ```
>
> `BUILDLMDB TINY` now produces a 32 MiB environment that is still 32 MiB after an
> index attach. **This is the first time the size ladder has been observed to hold
> through use since it was written.** 32x storage reduction for this table.
>
> Proof: `proof.lmdb.mapsize_ladder_honoured_after_fix`, transcript in
> `labtalk/proofs/runs/`. Still owed: the rebuild sizing rule
> (`mapsize_explicit`), deliberately kept out of this change so the fix could earn
> its own verdict.

Date: 2026-07-26
Status: **source-defined defect; size distribution measured; direct runtime proof OWED**
AI Friendly route: **AIF-065**
Run: `COWORK-20260726-001`   Member: `member.ai.claude.cowork`   Owner: `member.derald`
Mutation: documentation only. No source, HELP, DBF, index or runtime-state change.

## Finding

`BUILDLMDB` documents and implements a six-step size ladder plus an explicit
`MAPSIZE` spec. The value it selects is applied when the environment is
**written**, and then discarded the next time that environment is **opened for
reading**, because two other call sites hardcode 1 GiB.

The result is that the entire ladder is currently **cosmetic**. `BUILDLMDB TINY`
parses 32 MiB, prints 32 MiB, writes a 32 MiB env -- and the file becomes 1 GiB
on first attach.

| Role | Site | Mapsize | Honours the ladder |
| --- | --- | --- | --- |
| writer | `src/cli/cmd_buildlmdb.cpp:110,138-150,647-676` | `LMDB_DEFAULT_MAPSIZE` = 128 MiB, or preset, or `MAPSIZE <n>` | **yes** |
| reader / attach | `src/xindex/cdx_backend.cpp:189` | hardcoded `1 GiB` | no |
| reader / attach | `src/xindex/lmdb_backend.cpp:80` | hardcoded `1 GiB` | no |
| message catalog | `src/help/message_catalog.cpp:175,1043` | `MESSAGE_LMDB_MAPSIZE` = 128 MiB | n/a -- own env, self-consistent |

This is a **write/read disagreement**, the same defect shape as
`DOTSCRIPT_COMMENT_PREFIX_EXECUTION_PATH_DRIFT_V1`: two paths over one artifact,
each internally correct, disagreeing about a documented contract.

## The documented contract

`src/cli/cmd_buildlmdb.cpp` lines 51-58, inside the `@dottalk.usage v1` block:

```text
BUILDLMDB TINY          32 MiB
BUILDLMDB SMALL         64 MiB
BUILDLMDB MEDIUM       128 MiB     (= LMDB_DEFAULT_MAPSIZE, the no-argument default)
BUILDLMDB LARGE        256 MiB
BUILDLMDB XL           512 MiB
BUILDLMDB HUGE           1 GiB
BUILDLMDB MAPSIZE <size> YES        <n>[K|M|G], floor 8 MiB
BUILDLMDB CLEAN MAPSIZE <size> YES
```

The contract is accurate about intent and the parser is correct: `preset_mapsize()`
and `parse_mapsize_spec()` both work, the floor is enforced, and the chosen value
is reported through `format_mapsize_bytes()`. Nothing about the documentation is
wrong. The code downstream of it does not comply.

Note also `cmd_buildlmdb.cpp:676`:

```cpp
(void)mapsize_explicit; // available if you later want to report preset/default distinction
```

The writer already knows whether the size was chosen or defaulted, and discards
that knowledge. That is the natural place to warn when a chosen size is about to
be overridden.

## Measured evidence

Taken 2026-07-26 from `dottalkpp\data\lmdb`. `stat` byte sizes, not `du`, because
the question is allocation and sparseness would confuse it.

**Every `data.mdb` in the tree holds one of exactly two sizes -- and they are
precisely the two constants in the source:**

```text
live envs (excluding backups\):
     71  files at   134,217,728 bytes   = 128 MiB   (LMDB_DEFAULT_MAPSIZE)
     41  files at 1,073,741,824 bytes   =   1 GiB   (the hardcoded backend value)

COMMENTS archived envs:
     48  at 128 MiB       32  at 1 GiB
```

No intermediate value occurs anywhere. Per lane, the split tracks how the lane is
used rather than anything it requested:

```text
x64            128MiB:  0   1GiB: 13      COMMENTS       128MiB: 0   1GiB:  8
pinocchio      128MiB:  0   1GiB:  2      datadict       128MiB: 7   1GiB: 11
help           128MiB:  9   1GiB:  0      manuals        128MiB: 8   1GiB:  0
memo           128MiB:  3   1GiB:  0      locale         128MiB: 2   1GiB:  0
sandbox        128MiB: 26   1GiB:  2      metadata       128MiB: 8   1GiB:  1
```

Lanes attached and traversed through the CDX backend are uniformly 1 GiB. Lanes
that are built and then read through other paths -- `help`, `manuals`, `memo`,
`locale` -- are uniformly 128 MiB. Nothing in the tree asked for 1 GiB.

Whole tree: **99 GB**, of which roughly 50 GB is archived (see below) and the
live remainder is inflated 8x wherever an index has ever been attached.

## Mechanism -- inferred, NOT yet proven

LMDB sizes `data.mdb` to the environment mapsize; on Windows the file is
allocated rather than sparse. The proposed mechanism is:

1. `BUILDLMDB` creates the env and calls `mdb_env_set_mapsize(env, chosen)`.
   File becomes `chosen` bytes. The transcript confirms this half directly --
   the 2026-07-26 COMMENTS reload printed
   `BUILDLMDB: mapsize 134,217,728 bytes (128 MiB)` eight times.
2. The table is later opened and its index attached through `cdx_backend` /
   `lmdb_backend`, which call `mdb_env_set_mapsize(env_, 1 GiB)`.
3. The file grows to 1 GiB and stays there.

All eight COMMENTS envs are 1 GiB, and the readback validation immediately after
that reload ran `WORKSPACE OPEN`, which attached all eight indexes.

**This is circumstantial.** The evidence is: two constants in the source, exactly
two sizes on disk matching them, and a per-lane split that correlates with attach
behaviour. That is strong, and it is not a transcript.

Per `lesson.career.a_script_never_run_is_not_evidence`, the mechanism is recorded
here as **inferred** and must not be promoted to "proven" until this runs:

```text
USE <small table>
SELECT <area>
BUILDLMDB CLEAN TINY YES
    -> stat data.mdb    expect 33,554,432
USE <same table>            && force an attach
SELECT <area>
SET ORDER TO <tag>
    -> stat data.mdb    expect 33,554,432 if the mechanism is wrong
                        expect 1,073,741,824 if it is right
```

Two `stat` calls decide it. Until they are run and the transcript preserved, this
document describes a defect whose *effect* is measured and whose *cause* is
argued.

## Second, independent problem in the same subsystem

`BUILDLMDB CLEAN YES` does not delete the previous envdir -- it **archives** it to
`<lmdb-lane>\backups\<TABLE>.cdx.d_<yyyymmdd_hhmmss>`, with no retention limit.
This is documented behaviour (`archives_existing_environment: CLEAN or FORCE` in
the risk block), so it is not a defect in itself. The absence of any retention
policy is.

```text
lmdb\COMMENTS\backups     39 GB    80 archives, oldest 2026-06-25
lmdb\sandbox\backups     4.2 GB
lmdb\messaging\backups   3.4 GB
lmdb\pinocchio\backups   3.1 GB
```

Roughly 50 GB of regenerable index, accumulated silently over a month. Combined
with the mapsize override each archive is 8x the size it should be, so the two
problems multiply.

This filled the disk on 2026-07-26 and aborted a SRC* catalog reload mid-backup.
The reload driver was itself at fault for copying `lmdb\` at all -- LMDB envs are
derived data that `BUILDLMDB CLEAN YES` rebuilds in seconds -- and worse, its
recursive copy included `backups\`, so each reload would have duplicated an
ever-growing archive pile. Fixed in
`tools\fullstack_docs\reload_src_comments.ps1`: source data only (22 MB), with a
hard abort if the backup ever exceeds 500 MB. Interim pruner:
`tools\fullstack_docs\prune_lmdb_archives.ps1`.

## Proposed correction -- NOT yet applied

**Do not change the constant in the two backends. Delete the calls.**

LMDB records the map size in the environment's meta page. When
`mdb_env_set_mapsize()` is never called, `mdb_env_open()` adopts the size
persisted in the file. Removing the two reader-side calls therefore makes both
backends inherit whatever `BUILDLMDB` chose, and the ladder starts working with
no new plumbing and no new setting.

```cpp
// src/xindex/cdx_backend.cpp:189   -- remove
(void)mdb_env_set_mapsize(env_, 1024ull * 1024ull * 1024ull); // 1 GiB
// src/xindex/lmdb_backend.cpp:80   -- remove
(void)mdb_env_set_mapsize(env_, 1024ULL * 1024ULL * 1024ULL); // 1 GiB
```

Both discard their return value with `(void)`, so a failure at either site is
invisible today. Whatever replaces them should check `rc`.

That LMDB adopts the meta-page size is stated here as the *basis* for the
proposed fix and **must be confirmed against the linked LMDB version's
`mdb_env_open` before the change is made** -- if the adoption rule differs, the
correct fix is to persist the chosen size in the CDX container and have the
backends read it, which is a larger change.

Sequencing: the correction needs a rebuild plus a `BUILDLMDB CLEAN` pass over
every lane before existing envs shrink. It should be its own slice, verified by
the same two `stat` calls, and must not be folded into an unrelated reload.

## Why this matters beyond disk

The x64base-vs-SQLite benchmark lane is chartered but unrun. **Any storage
comparison taken today would be meaningless**: index footprint is currently
determined by whether a table has ever been attached, not by anything the schema,
the data or the operator chose. A 30,124-row table and a 9-row table both occupy
1,073,741,824 bytes. Recorded against the benchmark row in
`docs/ai-friendly/HISTORICAL_DATABASE_MIGRATION_EMPIRICAL_PROGRESS_LANE_V1.md`.

## CORRECTION 2026-07-27: the proposed fix was WRONG. Do not delete the calls.

The correction proposed earlier in this document -- delete both
`mdb_env_set_mapsize` calls so LMDB adopts the meta-page size -- **would have
made things worse.** Checking the vendored header before implementing
(`build/vcpkg_installed/x64-windows/include/lmdb.h`, `mdb_env_set_mapsize`)
settles it:

> "The size should be a multiple of the OS page size. **The default is 10485760
> bytes.**"
>
> "The new size takes effect immediately for the current process but will not be
> persisted to any others until a write transaction has been committed by the
> current process. Also, **only mapsize increases are persisted** into the
> environment."
>
> "This function **may be called with a size of zero to adopt the new size.**"
>
> "Any attempt to set a size smaller than the space already consumed by the
> environment **will be silently changed to the current size of the used space.**"

Deleting the calls does not fall back to the persisted size. It falls back to
LMDB's **10 MiB default**, which is smaller than every environment in this tree
and would produce `MDB_MAP_FULL` on contact -- an 8x storage overcharge traded
for immediate failure.

### The correct fix

```c
mdb_env_set_mapsize(env_, 0);   // adopt the size persisted in the meta page
```

Zero is the documented "adopt" argument. It is one character different from the
deletion this document recommended for a day, and the difference is between
honouring `BUILDLMDB`'s ladder and breaking every index in the repository.

**`cdx_backend.cpp:189` is the primary site** -- CDX builds the index CONTAINERS
(member.derald), so that path is what almost every environment goes through.
`lmdb_backend.cpp:80` takes the same change.

### The unit of waste is the CONTAINER, not the table or the tag

Worth stating precisely, because it changes the arithmetic. A `.cdx` container
holds MANY tags, and one LMDB environment backs the whole container:

```
SYSSUBCMD.cdx          one container, 8 tags
  SUB_ID  PARENT  SUB_NAME  QUAL_NAME  DISP_STYL  VIS_TIER  REG_RING  SRC_AUTH
SYSSUBCMD.cdx.d        ONE environment  ->  1,073,741,824 bytes after attach
```

So the 1 GiB is asserted once per container, not once per tag -- eight tags did
not cost eight gigabytes. Equally, it is not per table in general: it is per
container, and the container is the thing `CDX CREATE` makes.

That is why the count that matters is the number of containers, and why the
figure quoted in this lane is ~112 environments rather than a count of tables or
of tags.

### The library already agrees with the rebuild rule

The sizing rule decided below was reached independently, and the header shows it
matches LMDB's own semantics:

| rule as decided | LMDB behaviour |
|---|---|
| larger size grows the env | "only mapsize increases are persisted" |
| smaller size is refused | "silently changed to the current size of the used space" |
| no size reuses the current | `mdb_env_set_mapsize(env, 0)` adopts it |

LMDB will not let you shrink below what is used; the rule adds the missing half,
which is not shrinking below what was *declared*. The mechanism to implement all
three already exists in the API.

### Why this matters far beyond disk: vdisk

> "great catch -- it would have killed us in vdisk sessions" (member.derald)

The vdisk lane runs LMDB environments in RAM (`xbase::ramfs`, the
LMDB-in-RAM/symlink route). On disk a 1 GiB mapsize for a 31-row table is waste.
**In RAM it is fatal.** The live tree holds 112 environments; at the asserted
1 GiB each that is ~112 GiB of address space and, on a RAM-backed mount, real
memory. A vdisk session would have died on contact with no obvious cause, and
the diagnosis -- an attach-path constant overriding a documented size ladder --
is not one anybody would reach for while debugging an out-of-memory.

The defect was found on a full disk and proven on a 31-row table. Its worst
consequence was waiting in a lane that had not been exercised yet.

### Headroom hid it, and would have stopped hiding it at the worst moment

> "I've been lucky during testing because I have 64gb ram" (member.derald)

That is the whole reason this survived. 64 GB is generous enough that nothing in
ordinary CLI use ever pressed against the waste -- and it is NOT enough for the
lane that was next:

```
112 containers x 1 GiB   = ~112 GiB    exceeds 64 GB   -- vdisk dies
112 containers x 32 MiB  =  ~3.5 GiB   comfortable     -- vdisk viable
```

So the luck was not going to run out gradually. It would have run out the first
time someone mounted the LMDB tree in RAM, all at once, in a session where the
obvious suspect is **the new code**. The defect is four months old and lives in
an attach path nobody was editing; the vdisk lane would have been three days old
and under active development. Every instinct would have pointed at the wrong
file.

**The general shape: abundant resources do not prevent resource defects, they
postpone them -- and they postpone them until a new consumer arrives, which is
precisely when the blame lands somewhere else.** A machine sized for comfort is
a machine that cannot feel this class of problem, so the measurement has to come
from somewhere other than "does it still work here".

That is also the argument for the storage benchmark axis being unblocked rather
than merely nice: it is the instrument that would have caught this without
anyone's disk filling or anyone's RAM running out.

## THE LMDB ENVIRONMENT IS DERIVED. DO NOT BACK IT UP. (member.derald)

> "we don't need to back up the .mdb lmdb files, instead we back up the cdx
> container. The containers are small and by design we can rebuild the lmdb
> files, so why back them up in the first place."

Measured 2026-07-27:

```
SYSCMD        .cdx        776 bytes      data.mdb  1,073,741,824 bytes
SYSSUBCMD     .cdx      3,656 bytes      data.mdb  1,073,741,824 bytes
SYSFUNC       .cdx      3,656 bytes      data.mdb  1,073,741,824 bytes

ALL 93 .cdx containers   0.1 MB
ALL LMDB                 73 GB
```

**Roughly 730,000 to 1.** The declaration layer -- every tag, every container,
the entire statement of what the indexes ARE -- fits in a tenth of a megabyte.
The other 73 GB is regenerated from it plus the DBF by `BUILDLMDB`.

### The dependency, stated plainly

```
DBF (data)  +  .cdx (declares the tags)   --BUILDLMDB-->   LMDB env (derived)
   SOURCE           SOURCE                                  REGENERABLE
```

A `.cdx` is a declaration shell; the keys live in LMDB and are rebuilt on every
`BUILDLMDB`. So the environment holds no information not derivable from two
things that together weigh almost nothing.

**Backing up a derived artifact is not caution, it is a category error.** It
costs storage proportional to the derived size while protecting nothing that the
source does not already protect -- and it competes for the very disk the
regeneration needs.

### This was learned the hard way, twice, in one day

1. A reload driver copied `lmdb/COMMENTS` recursively "to be safe" -- 47 GB of
   regenerable data -- and filled the disk mid-run. Fixed to back up source data
   only, with a hard abort above 500 MB. Recorded then as: *"back up everything
   to be safe is a reflex, and it is wrong when the thing copied is rebuilt by
   the very next step."*
2. `BUILDLMDB CLEAN` does the same thing structurally: it archives the
   superseded ENVIRONMENT. 25 archived environments exist today, holding nothing
   that could not be regenerated in seconds from a 3 KB container.

### Follow-on fix (own lane): CLEAN should not archive the environment

`BUILDLMDB CLEAN` currently archives the env with no retention limit, which is
what compounded the mapsize defect into a disk-filling event. Given the ratio
above, the correct behaviour is one of:

- **archive nothing** -- the env is regenerable by definition, and `CLEAN` is
  followed immediately by a rebuild
- **archive the `.cdx` only** -- 3 KB, preserves the declaration if the rebuild
  is destructive to it, costs nothing

Either makes the 25 existing archives straightforwardly DELETABLE rather than
subject to a retention policy. `prune_lmdb_archives.ps1 -Keep N` was the right
tool for a world where the archives were worth keeping; the measurement says
that world does not exist.

### Consequence for the reclaim below

The reclaim's operational trap -- that rebuilding 63 containers first writes
63 GiB of fresh archives -- **disappears entirely** once `CLEAN` stops archiving
environments. The batching and prune-between-batches discipline is a workaround
for a behaviour that should not exist.

## Provenance of the finding -- recorded because attribution is a lane concern here

Set down deliberately, per `AGENCY_MODEL_V1.md`, which observes that git stamps
one name where the truth often had several.

| step | who |
|---|---|
| disk filled during a SRC* reload (a copy-based backup of regenerable LMDB) | member.ai.claude.cowork, own error |
| directed attention to the size options -- *"check the usage contract in buildlmdb for TINY GIANT CUSTOM etc"* | member.derald |
| found that the ladder is parsed, echoed, written, and then overridden on attach | member.ai.claude.cowork |
| proved it, three tables, pre- and post-fix | member.ai.claude.cowork |
| corrected the fix from deletion to `set_mapsize(0)`, corrected the unit to containers, identified the vdisk consequence, and reduced archiving from a policy to nothing | member.derald |

**The maintainer believed the sizing had already been fixed.** That is the part
worth recording, and it is a stronger result than finding an unknown defect: the
documentation process did not fill a gap in what was known, it **contradicted
something believed to be settled**. A held belief is harder to dislodge than an
absence, because nothing prompts you to re-check it.

Note also that the direction and the discovery are separate acts. Being told
where to look is not the same as finding, and finding is not the same as being
right about the remedy -- the first proposed fix here was wrong and was caught by
reading the header. All three steps had different authors, which is precisely the
pattern the agency model exists to record.

## Archiving is attached to the wrong command entirely (member.derald)

> "why archive the cdx when changing sizes -- the only reason to archive is if
> modifying the cdx structure itself."

Correct, and checking it produces a clean inversion. `BUILDLMDB`'s own risk block
already states the relationship:

```
reads_cdx_container:     yes      <- the declaration, read only
writes_lmdb_environment: yes      <- the derived artifact
```

`BUILDLMDB` never modifies the container. It reads the declaration and rebuilds
the derived environment from it. **A size change alters nothing declarative**, so
there is nothing whose prior state could be worth keeping. Archiving during
`BUILDLMDB` is protecting the wrong artifact at a moment when no protected thing
is at risk.

Meanwhile:

| command | changes | archives today |
|---|---|---|
| `BUILDLMDB` | the derived environment (up to 1 GiB) | **yes** (now opt-in) |
| `CDX CREATE` | the container structure (~3 KB) | **no** |
| `CDX ADDTAG` | the container structure (~3 KB) | **no** |

Archiving exists exactly where it protects nothing, and is absent exactly where
it would be cheap and meaningful.

### The principle

**Archive the thing that CHANGES, at the command that CHANGES it -- not the
thing that is large.** Size is not a reason to keep a copy; irrecoverability is.
A 1 GiB environment regenerated by the very command that replaced it is worth
nothing; a 3 KB declaration being restructured is worth a snapshot, because a
mistaken `ADDTAG` or a re-`CREATE` discards tag definitions that no other file
holds.

### Consequences

1. `ARCHIVE`/`KEEP` on `BUILDLMDB` is **not a safety feature** and should not be
   documented as one. It is a debugging convenience for a deliberate before/after
   comparison of index CONTENT. Recorded as such rather than removed, so nobody
   reaches for it expecting protection.
2. **Owed, and the real gap:** `CDX CREATE` and `CDX ADDTAG` should snapshot the
   prior `.cdx` before restructuring it. At ~3 KB this costs nothing measurable
   and protects the only artifact in the subsystem that is not regenerable.
   Wants its own lane -- it is a change to a different command, with its own
   verification.
3. The 25 archived environments remain deletable. They were never protecting a
   declaration.

## Reclaim: the fix stops the bleeding, it does not heal the wound

Measured immediately after the fix landed, 2026-07-27:

```
dottalkpp/data/LMDB          73 GB
  63 envs @ 1,073,741,824    ~63 GiB    87% of the tree
  75 envs @   134,217,728     ~9.4 GiB
   2 envs @    33,554,432      today's rebuilt SYSARGS
live envs 115   archived envs 25
```

Sixty-three files hold 87% of the tree, and they are 1 GiB **only because they
were once attached**. The fix prevents new inflation; it cannot shrink an
environment that already exists. Reclaiming requires rebuilding each container.

### The compounding that actually filled the disk

member.derald: *"it's also been consuming large amounts of disk space, especially
with the backups."* That is the second defect in this subsystem multiplying the
first:

- every attached env is 1 GiB rather than its declared size
- `BUILDLMDB CLEAN` archives each superseded env with **no retention limit**
- so every rebuild banks *another* 1 GiB copy

Neither alone would have filled a disk. Together, each maintenance operation on
an over-sized environment permanently deposits an over-sized archive. **The fix
therefore improves the archive growth rate by the same factor as the live size**
-- future `CLEAN` operations bank a 32 MiB archive where they used to bank 1 GiB.

### The operational trap is GONE -- and the version above was wrong twice

An earlier draft of this section warned that rebuilding all 63 one-gig containers
would "first write ~63 GiB of fresh archives" and prescribed batching with prunes
between. **Both halves were wrong, and they were wrong in opposite directions.**

`archive_envdir_to_backups` uses `fs::rename` -- a MOVE, not a copy. Archiving
never spiked disk usage; it ACCUMULATED it. The disk-filling incident that opened
this lane was a copy-based backup script, an entirely different mechanism that I
had conflated with this one. Both retain regenerable data; only one doubles it.

And as of 2026-07-27 `BUILDLMDB CLEAN` **discards** the superseded environment by
default (`ARCHIVE`/`KEEP` opts in), so there are no archives to accumulate or
prune. The reclaim is therefore a single pass:

1. rebuild each over-sized container at an appropriate rung
2. delete the 25 pre-existing archives -- regenerable, no retention policy needed

Projected end state is roughly 63 x 128 MiB in place of 63 x 1 GiB, about 55 GiB
recovered, and more where a smaller rung suits -- most of these catalogs are
small enough for `TINY` or `SMALL`.

`prune_lmdb_archives.ps1 -Keep N` was the right tool for a world in which the
archives were worth keeping. The 730,000:1 measurement says that world does not
exist, and the tool is now vestigial rather than load-bearing.

### Why this is worth doing now rather than later

Every container left at 1 GiB is one that will bank a 1 GiB archive the next time
anything rebuilds it. The debt compounds on maintenance, not on use.

## Rebuild sizing rule -- DECIDED 2026-07-27 (member.derald)

> "if we rebuild, the command should default to the current size unless a larger
> size is declared (probably for more room)."

This is a second, separable correction from the override deletion, and it should
land with it because together they make the ladder mean something.

### The rule

| invocation | behaviour |
|---|---|
| rebuild, **no size given** | reuse the env's CURRENT mapsize -- do not fall back to a compiled default |
| rebuild, **larger size given** | grow to the requested size |
| rebuild, **smaller size given** | refuse, or require an explicit force token; shrinking risks `MDB_MAP_FULL` and silent data loss on an env that already holds more |

Rationale: a rebuild is a maintenance operation on an EXISTING environment. It
should preserve the operator's earlier sizing decision by default and change it
only when told. Today a bare rebuild silently reasserts a compiled constant,
which means the size an operator chose survives exactly until the next routine
rebuild -- a decision with no memory.

### The flag already exists and is discarded

`src/cli/cmd_buildlmdb.cpp:676`:

```cpp
(void)mapsize_explicit; // available if you later want to report preset/default distinction
```

`mapsize_explicit` -- precisely the "did the operator name a size?" predicate the
rule needs -- is already computed, then thrown away with a comment anticipating
the use it was never put to. `chosen_mapsize` is initialised from
`LMDB_DEFAULT_MAPSIZE` (line 624) regardless.

So implementing the rule is not new machinery. It is:

1. when `!mapsize_explicit`, read the existing env's current mapsize (LMDB meta
   page, via `mdb_env_info`) and use it instead of `LMDB_DEFAULT_MAPSIZE`
2. when explicit and larger, use the request
3. when explicit and smaller, refuse with a message naming both sizes
4. delete the `(void)` and report which branch was taken, which is what the
   comment wanted in the first place

**This is the third instance in one run of the same shape**: a mechanism built,
left unwired, and the gap invisible because nothing compares the two halves.
`SOURCE_HASH` written and never read (AIF-066); `X64M` displacement declared and
never checked (`dbfread`); `mapsize_explicit` computed and never used. Worth
naming as a class: *a value produced for a decision that is never made.*

## PROVEN 2026-07-27 -- mechanism observed, lane promoted to `runtime_observed`

The inference in "Mechanism -- inferred, NOT yet proven" is now observed. One
index attach, on a never-attached environment `BUILDLMDB` had written at 128 MiB:

```
BEFORE: 134,217,728                    (128 MiB, as BUILDLMDB wrote it)

  . SETPATH: DBF     = ...\data\metadata
  . SETPATH: INDEXES = ...\data\INDEXES\metadata
  . SETPATH: LMDB    = ...\data\LMDB\metadata
  . Opened SYSSUBCMD (v64) : Record count 31
    Valid Index/Indices   : CDX
    Auto-attached order: SYSSUBCMD.cdx (tag: SUB_ID)
  . SET ORDER: CDX TAG 'SUB_ID' (ASC)
  . Found at 31.

AFTER : 1,073,741,824                  (1 GiB)
```

Transcript: `labtalk/proofs/runs/20260727_aif065_mapsize_attach.txt` (committed;
`.gitignore:56` negation `!labtalk/proofs/**` keeps proof artifacts trackable per
AIF-062).

**Exactly 8x, on a 31-row table, from one attach.** The bimodal distribution
reported under "Measured evidence" is explained: every environment holds either
the size `BUILDLMDB` wrote or the 1 GiB the attach path asserts, and which one
depends solely on whether an index has ever been opened.

### Correction to the predicted trigger

The protocol below anticipated that `SET ORDER` or `SEEK` would cause the
attach. The transcript shows otherwise:

```
. Opened SYSSUBCMD ...
  Auto-attached order: SYSSUBCMD.cdx (tag: SUB_ID)      <- attach happens HERE
```

**The attach occurs at `USE`,** as an auto-attach, when the index is findable.
`SET ORDER` merely selects a tag on an environment already opened and already
resized. This matters for anyone reproducing it: the trigger is not an index
*operation*, it is the index being *locatable* when the table opens.

That also explains the two failed probes below. The first had a relative tee
path that aborted the pipeline; the second reached the shell but set only
`SETPATH DBF`, so the CDX was not findable, no auto-attach occurred, and the
env stayed at 128 MiB. Both produced an identical, plausible, meaningless
`134217728 -> 134217728`.

### Replicated on a second table, 2026-07-27

`SYSFUNC` (69 rows) run through `tools/proofs/run_proof.ps1`:

```
env   134,217,728 -> 1,073,741,824   delta 939,524,096
markers all present -- the subject ran
verdict OBSERVED
```

Two tables, two row counts, identical outcome. The attach path asserts 1 GiB
regardless of what `BUILDLMDB` wrote, and regardless of how much data exists.
Transcript: `labtalk/proofs/runs/20260727_aif065_mapsize_tiny_survives_attach.txt`.

This was also the first use of the proof runner, and it is the **pre-fix
control**: the identical command with `-ExpectNoChange` becomes the regression
once `mdb_env_set_mapsize(env_, 0)` is applied.

### Specimen ledger

```
SYSSUBCMD   1,073,741,824   SPENT -- first proof
SYSFUNC     1,073,741,824   SPENT -- replication + pre-fix control
SYSARGS       134,217,728   LAST SPARE, 249 rows, never attached
SYSCMD      1,073,741,824   pre-existing attached control
```

**One spare left.** Reserve `SYSARGS` for the post-fix verification, where a
`TINY` request must produce a 32 MiB file that STAYS 32 MiB across an attach.
If it is spent early, making another control means a full `CREATE -> CDX ->
IMPORT -> BUILDLMDB` cycle on a fresh table.

### Method note that earned its place

Two consecutive probes returned `134217728 -> 134217728` for two unrelated
reasons, neither of them the mechanism. **A null probe and a negative result are
indistinguishable from the outside.** A proof protocol must therefore state what
SUCCESS LOOKS LIKE IN THE TRANSCRIPT, not merely what to measure -- here,
`Auto-attached order:` and `Found at N.`. The two `stat` calls were never the
hard part; knowing whether the thing under test ran was.

## Runtime proof protocol -- the specimen is PERISHABLE

The lane is blocked at `source_defined` because nobody has watched a single
environment change size. Two `stat` calls settle it, and today's seeding created
clean controls:

```
SYSSUBCMD   134,217,728   written 2026-07-27 07:31   31 rows   NEVER ATTACHED
SYSFUNC     134,217,728   written 2026-07-27 04:47   69 rows   never attached
SYSARGS     134,217,728   written 2026-07-27 04:54  249 rows   never attached
SYSCMD    1,073,741,824   written 2026-07-17        203 rows   attached
```

`SYSCMD` is the opposite arm: comparable row count, 8x the size, differing only
in attach history.

```powershell
$e = "D:\code\ccode\dottalkpp\data\LMDB\metadata\SYSSUBCMD.cdx.d\data.mdb"
(Get-Item $e).Length          # expect 134217728
./datarun.ps1 -CommandLines 'SETPATH DBF metadata','USE SYSSUBCMD',`
                            'SET ORDER TO SUB_ID','SEEK "SUB_SET_WRAP"'
(Get-Item $e).Length          # 1073741824 confirms the mechanism
```

**Design caveat that matters.** A plain `USE` does NOT trigger it. This morning's
seed ran `USE SYSSUBCMD; COUNT; STRUCT; LIST` after `BUILDLMDB` and the env is
still 128 MiB. The attach path needs a real index operation -- `SET ORDER`,
`SEEK`, a tag-based read. If the sizes match after the probe, suspect the PROBE
before concluding the mechanism is absent: a diagnostic that does not cover the
path under investigation returns silence indistinguishable from a negative
result (see the `SET DEVDIAG` null result, AIF-067).

**Perishability.** Any index attach on any of the three consumes that specimen.
`SYSFUNC` and `SYSARGS` are spares. Once all three are attached, re-creating a
control means a full `BUILDLMDB` cycle on a fresh table.

### On success

Promote AIF-065 to `runtime_observed`, cite the two sizes and the transcript in
`proofs.yaml`, then apply the correction and re-run the same protocol to show a
`TINY` request producing a 32 MiB file -- which is the ladder working for the
first time.

## Method note

This was found because a disk filled, not because anything was audited. The
usage contract had been correct and complete the whole time; nobody had compared
it against the bytes on disk. The check that exposed it -- `stat` every
`data.mdb` and count distinct sizes -- takes one command, and the bimodal result
named the two offending constants before either was read.

`stack_audit_v1` compares documentation against tables. It has no check that
compares a documented *option* against its *observable effect*. That gap is
worth a finding class of its own.

## Files

```text
src/cli/cmd_buildlmdb.cpp            writer; the ladder, honoured
src/xindex/cdx_backend.cpp:189       reader; hardcoded 1 GiB override
src/xindex/lmdb_backend.cpp:80       reader; hardcoded 1 GiB override
src/help/message_catalog.cpp:175     separate env, self-consistent, not implicated
tools/fullstack_docs/reload_src_comments.ps1     no longer copies lmdb\
tools/fullstack_docs/prune_lmdb_archives.ps1     interim archive reclaim
```
