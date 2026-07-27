# A Documented Option Is Not an Honoured Option v0

Status: draft
Audience: developer, maintainer, technical writer, ai_partner
Registry ID: `lesson.career.a_documented_option_is_not_an_honoured_option`
Lane doc: [LMDB mapsize override](../../../docs/maintenance/LMDB_MAPSIZE_OVERRIDE_LANE_V1.md) (AIF-065)
Observed: 2026-07-26 (run `COWORK-20260726-001`)
Proof state: **source_defined** — the effect is measured, the cause is argued

## Career Lesson

Its companion, `lesson.career.a_script_never_run_is_not_evidence`, says a claim
is evidence only when a transcript exists. That lesson is about artifacts nobody
executed.

This one is about artifacts that *are* executed, every day, successfully — and
still do not do what they say.

```text
a documented option is a claim about behaviour,
and claims need evidence like any other
```

Accepting a flag is not honouring it. Echoing it back is not honouring it.
Exiting 0 is not honouring it. An option is honoured only when something
**observably differs** between it set and unset — and until someone has measured
both, it is an unverified claim wearing the costume of a feature.

## The Case

`BUILDLMDB` builds the LMDB index backend for a table. Its `@dottalk.usage`
contract documents a six-step size ladder and an explicit override:

```text
TINY 32M · SMALL 64M · MEDIUM 128M (default) · LARGE 256M · XL 512M · HUGE 1G
MAPSIZE <n>[K|M|G] YES          floor 8 MiB
```

Everything about that works. The presets parse. The floor is enforced. The
chosen value is formatted and printed back to the operator. The environment is
created at exactly that size. The documentation is accurate; the parser is
correct; the writer complies with both.

Then two other files undo it:

```cpp
src/xindex/cdx_backend.cpp:189   (void)mdb_env_set_mapsize(env_, 1024ull*1024ull*1024ull); // 1 GiB
src/xindex/lmdb_backend.cpp:80   (void)mdb_env_set_mapsize(env_, 1024ULL*1024ULL*1024ULL); // 1 GiB
```

`BUILDLMDB` is the **writer**. Those are the **attach** paths. The environment
grows to 1 GiB the first time its index is opened for use, regardless of what was
requested. `BUILDLMDB TINY` asks for 32 MiB, prints 32 MiB, produces 32 MiB — and
yields a 1 GiB file the moment anyone uses the index.

The entire ladder is cosmetic, and has been since it was written.

## Why It Stayed Invisible

Every piece is correct **in isolation**:

| Read this alone | Conclusion |
| --- | --- |
| the usage contract | a size ladder exists |
| `cmd_buildlmdb.cpp` | it is parsed, floored, applied, reported |
| the reload transcript | `mapsize 134,217,728 bytes (128 MiB)` — confirmed |
| `cdx_backend.cpp` | opens an env with a sensible 1 GiB map |

Nothing is stale. Nothing is a typo. No test fails. No error is printed. Every
file is defensible on its own terms, and reading any one of them leaves the
impression of a working feature.

The defect lives only in the **relationship between two paths over one artifact**
— the same shape as `DOTSCRIPT_COMMENT_PREFIX_EXECUTION_PATH_DRIFT_V1`, where
`DOTSCRIPT <file>` and `--script <file>` disagreed about comment prefixes and both
returned exit code 0. Single-file review cannot see either. That is a structural
limit of reading, not a lapse of attention.

## How It Was Actually Found

A disk filled during an unrelated catalog reload.

Not an audit. Not a test. Not review. The system ran out of room mid-backup, and
the investigation into *why* walked back through the index tree.

The confirming check took one command — `stat` every `data.mdb`, count distinct
sizes — and named both offending constants before either file was opened:

```text
71 live files at   134,217,728 bytes   (128 MiB)
41 live files at 1,073,741,824 bytes   (  1 GiB)
 0 files at anything else
```

Two values. Two constants in the source. Nothing in between.

**Bimodality in a measurement that ought to be continuous is a signature of two
writers disagreeing.** Index sizes should vary with row count, key width and
fill. Finding exactly two distinct values across 112 environments meant nothing
was choosing a size based on data — two hardcoded numbers were fighting, and the
distribution said which files to open.

That is a transferable move. When a measurement clusters where it should spread,
stop reading and start counting.

## The Cost

- ~8× storage inflation wherever an index has ever been attached
- a 99 GB `lmdb\` tree; ~50 GB of it superseded archives, each 8× oversized
- a benchmark axis that cannot be used at all: a 30,124-row table and a 9-row
  table both occupy 1,073,741,824 bytes, so any x64base-vs-SQLite storage
  comparison would measure attach history rather than the database

The third is the expensive one. A storage number published from this tree would
have been wrong, defensible-looking, and very hard to retract.

## What This Lesson Does Not Yet Have

The **effect** is measured. The **cause** is inferred — from two constants in the
source, two sizes on disk matching them, and a per-lane split that correlates with
attach behaviour. That is strong circumstantial evidence and it is not a
transcript, so by the companion lesson's own rule this document stays at
`source_defined`.

Settling it takes two `stat` calls:

```text
BUILDLMDB CLEAN TINY YES     -> stat data.mdb    expect 33,554,432
force an index attach        -> stat data.mdb    33,554,432 = mechanism wrong
                                                 1,073,741,824 = mechanism right
```

Recording the gap is part of the lesson. The temptation to write "proven" because
the argument is good is exactly the failure both lessons are about.

## The Gap It Exposes in Our Own Tooling

`stack_audit_v1` compares documentation against tables. The census compares
source against contracts. **Neither compares a documented option against its
observable effect.**

Which means every option in every `@dottalk.usage` block in the repository is
currently an unverified claim. Most are probably fine. `BUILDLMDB`'s size ladder
was probably fine too, right up until someone measured it.

A finding class for this — pick an option, state what must observably differ, run
both — would be the natural next guard.

## Next Gate

Run the two-`stat` proof, preserve the transcript, register it in `proofs.yaml`,
promote this lesson to `runtime_observed`, and only then apply the correction in
AIF-065.
