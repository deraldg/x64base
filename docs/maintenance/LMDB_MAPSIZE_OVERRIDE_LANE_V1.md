# LMDB Mapsize Override -- BUILDLMDB Size Ladder Not Honoured v1

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

### Specimen ledger after the proof

```
SYSSUBCMD   1,073,741,824   SPENT -- this proof
SYSFUNC       134,217,728   spare, 69 rows, never attached
SYSARGS       134,217,728   spare, 249 rows, never attached
SYSCMD      1,073,741,824   pre-existing attached control
```

Two spares remain for verifying the FIX -- a `TINY` request must produce and
keep a 32 MiB file across an attach.

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
