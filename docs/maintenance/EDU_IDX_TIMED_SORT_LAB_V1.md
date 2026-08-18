---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260817-COWORK-004
  recorded_at_utc: 2026-08-17T23:55:00Z
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
    baseline_commit: 0420ea764
  authorization:
    requested_by: maintainer (member.derald), in-session, "IDX is an educational index ... it supports selected, timed index sorts" / "worth documenting"
    scope: >
      Records what the EDU IDX lab is, its two-level timing, why it is
      deliberately isolated from every persistent index family, and why it must
      not be bound into pydottalk. Runtime-observed: the maintainer ran the
      STD-vs-BUBBLE comparison on STUDENTS (200 rows) and the captured output
      is included, which also surfaced a duplicated header in IDX LIST.
  report:
    path: docs/maintenance/EDU_IDX_TIMED_SORT_LAB_V1.md
    kind: design_note
---

# EDU IDX -- the timed sort lab

Status: design note, review-needed. Owner: member.derald.
Author: member.ai.claude.cowork. Date: 2026-08-17.
Source: `src/cli/cmd_idx.cpp`, `include/cli/edu_idx.hpp`.
Evidence class: **runtime-observed**, 2026-08-17, `dottalk++ v0.6 (2aad9b37 dirty)`,
`STUDENTS` (v32, 200 records) via `datarun.ps1`. Captured run below.

## What it is

`IDX` is a **memory-only educational index lab**, `category: education`, for
teaching sorting and index concepts without writing persistent files. Its own
header states the boundary twice:

> "IDX is the EDU IDX command surface: a memory-only educational index lab.
> It is intentionally orthogonal to persistent index families."

> "IDX does not write `.inx` files and does not participate in `SET ORDER`,
> `REINDEX`, `WORKSPACE` restore, `IndexManager`, or `IIndexBackend`."

## IDX is one of a family, and the family does not enumerate

`src/edu/` holds **20 sources**: `edu_ascii_table`, `edu_bibletalk`,
`edu_boolean`, `edu_boyce_codd`, `edu_case`, `edu_christmas`, `edu_cobol`,
`edu_dewey_decimal`, `edu_edit`, `edu_erp`, `edu_evaluate`, `edu_formula`,
`edu_hanukkah`, `edu_idx`, `edu_missing_shims`, `edu_normalize`, `edu_six`,
`edu_snx`, `edu_text`. IDX is a member, not a one-off, and the `edu_` prefix is
a real convention rather than an accident.

**But the teaching surface cannot be enumerated from its own metadata.**
Measured 2026-08-17: only THREE commands declare `category: education` --
`cmd_idx.cpp`, `cmd_codasyl.cpp`, `cmd_bbox.cpp`. Meanwhile `README.md`
advertises "ASCII, SHELLO, RETRO, IDX, COBOL, CODASYL, NORMALIZE" as education
commands, and of those: `RETRO` declares `category: display`, and `ASCII`,
`SHELLO`, `COBOL` and `NORMALIZE` have no `cmd_<name>.cpp` at all -- they are
implemented under `src/edu/` and registered elsewhere.

So a harvest over `@dottalk.usage` answering "what is the teaching surface?"
returns 3 of roughly 20, and returns it without any sign that it is a fraction.
Three is a plausible number, which is exactly why the shortfall is invisible.
Only ONE `edu_` header (`include/cli/edu_idx.hpp`) and ONE namespace
(`dottalk::edu_idx`) exist, so IDX is also the only member with a declared API
of its own -- which is why it was documentable in an evening and the others were
not.

NOT proposed here: a 20-file metadata pass. It needs a ruling first, because
`RETRO` being `display` may be deliberate, and "education" may mean something
narrower than "lives in src/edu". Flagged so the next person to query that field
knows what it does and does not cover.

## IDX is not INX

These are separate things and the names invite exactly one mistake.

| | what it is | persists | participates in SET ORDER |
| --- | --- | --- | --- |
| **INX** | a single-tag on-disk index FORMAT (`orderstate::isInx` sits beside `isCnx`, `isCdx`, `isIsx`, `isCsx`, `isSix`, `isSnx`) | yes | yes |
| **IDX** | this teaching lab, in memory | **no** | **no** |

`cmd_idx.cpp`'s own `notes:` says it: "Use `INDEX` for persistent index files."

## Command surface

```text
IDX ON <field|#n> TAG <name> [SORT <algo>|<algo>] [ASC|DESC]
IDX LIST
IDX DROP <tag>
IDX DROP ALL
IDX USAGE
```

Algorithms currently **STD and BUBBLE**, parsed by
`dottalk::edu_idx::parse_sort_algo`. The documented examples are the lesson in
three lines:

```text
IDX ON LNAME TAG lname_std
IDX ON LNAME TAG lname_bubble  BUBBLE
IDX ON LNAME TAG lname_bubble2 SORT BUBBLE DESC
```

Same field, same table, different algorithm, different tag -- then `IDX LIST`
and read the times side by side.

## The captured run

```text
./datarun.ps1 -CommandLines 'USE dbf\og\STUDENTS','IDX ON LNAME TAG lname_std',
              'IDX ON LNAME TAG lname_bub BUBBLE','IDX LIST'

. Opened STUDENTS (v32) : Record count 200
  Valid Index/Indices   : CNX, INX

. Memory index created: lname_std        . Memory index created: lname_bub
    sort       : STD                         sort       : BUBBLE
    records    : 200 indexed / 200 scanned   records    : 200 indexed / 200 scanned
    build      : 9 ms                        build      : 11 ms
    sort       : 72 us                       sort       : 302 us
    compares   : 2293                        compares   : 19575
    swaps      : 0                           swaps      : 9346
```

**It reports operation counts, not just time** -- `compares` and `swaps` -- which
is the half that survives a fast machine. At n=200, BUBBLE's 19,575 compares sit
almost exactly on n^2/2 (20,000) while STD's 2,293 shows the n log n shape. A
student can check the complexity class by arithmetic instead of taking it on
faith, and the counts are deterministic where timings are not.

`swaps: 0` for STD is worth a question in class: the standard sort moves rather
than exchanging pairs, so "swaps" is not a universal unit of work. That is a
better lesson than a clean number.

## The part worth keeping: timing is TWO-LEVEL

`cmd_idx.cpp` reports two separate elapsed figures from one build:

- `result.build.elapsed_us` -- the whole build
- `result.build.sort.elapsed_us` -- **the sort alone**

`BuildStats` carries an `AlgoStats sort` member for exactly this. The teaching
value is in the gap between the two numbers: swapping BUBBLE for STD changes the
sort figure sharply and the build figure much less, which is how a student
discovers that reading the records, extracting keys and materialising entries
cost something independent of the algorithm. A single total would teach the
opposite lesson -- that the algorithm is everything.

`elapsed_text(uint64_t us)` prints microseconds under 1000 and milliseconds
above, so small tables stay legible instead of collapsing to "0 ms".

`IDX LIST` tabulates tag, expression, algorithm, direction and build time, so
several experiments are comparable in one view.

## Data model (`include/cli/edu_idx.hpp`)

```text
SortAlgo, SortDirection          enums
Entry { key, ... }               one sorted entry
AlgoStats { name, ... }          per-algorithm statistics
BuildStats { ... , sort }        whole-build stats, containing the sort's own
MemoryIndex { tag, expr, entries, ... }
IndexSummary { tag, expr, sort_algo, direction, ... }
BuildRequest / BuildResult { ok, replaced, message, tag }
```

`BuildResult::replaced` is worth noting: rebuilding an existing tag reports that
it replaced rather than silently overwriting, so a student repeating an
experiment sees that it happened.

## Why memory-only, and why that is the design rather than a limitation

The lab exists to be run repeatedly with different algorithms and thrown away.
Persisting it would mean rebuild semantics, staleness, container formats and
`SET ORDER` participation -- all of which are the subject of OTHER lanes and
none of which teach anything about sorting. Keeping it out of `IndexManager` and
`IIndexBackend` means an experiment cannot corrupt a real index, and a student
cannot accidentally leave a table ordered by a bubble sort.

## It must NOT be bound into pydottalk

Recorded here because the question will come up while AIF-119 M2 is open.

The lab's entire output is a **timing measurement**. Reaching it through a
Python binding would put a pybind11 call boundary, argument conversion and
interpreter overhead between the caller and the number, so the figure would
measure the binding rather than the sort -- and it would do so silently, because
the number would still look plausible. IDX is the one index family where a
binding actively destroys the feature's purpose.

If timed sorts are ever wanted from Python, the honest route is to run the CLI
(`dottalkpp` LEAN) and read its reported figures, per the stopping rule in
`AIF119_M2_INDEX_BINDING_PROPOSAL_V1.md`.

## Open / not covered

- **DEFECT, found by running it: `IDX LIST` prints its header twice.**
  `src/cli/cmd_idx.cpp:240` prints `MessageId::IdxListHeaderLineText` from the
  message catalog, then `:241-248` prints a HARDCODED `std::cout` header with
  the same six columns. Both fire, so the output carries two identical header
  rows. One must go, and the catalog is the house direction -- the hardcoded
  block also bypasses the message/locale spine entirely, so it would not
  localise even if the rest did. Cosmetic in effect, but it is a teaching
  artifact, and a duplicated header is the first thing a student sees.

- **The build dominates, and that is the lesson.** Measured: build 9 ms and
  11 ms against sorts of 72 us and 302 us. The algorithm under study is under
  3 percent of the work at this size. Choosing a bigger table changes that
  ratio, which is itself the next exercise -- `dbf/pinocchio/STUDENTS.dbf` is
  109 MB (roughly 900,000 rows), where BUBBLE is on the order of 10^11
  comparisons and is meant to be started and abandoned rather than finished.

- **Four flavors of the same data exist** in `dottalkpp/data/dbf/ladder/`
  (`students_fox26`, `students_vfp`, `students_x64`, `students_x64vec`, ~22 KB
  each). Running one tag across all four should hold the sort figure roughly
  constant while the build figure varies, separating "how the bytes are laid
  out" from "how you order them". Not yet run.

- **Two algorithms today.** `SortAlgo` and `parse_sort_algo` are the extension
  point; insertion, selection or shell sort would enrich the lesson, and the
  two-level timing plus operation counts already support them with no further
  work.

- **Not on the website.** The public docs describe the persistent families; the
  teaching lab is undocumented there. See OI-012, which asks that INX and IDX be
  kept distinct when that page is corrected.
- **Two algorithms today.** `SortAlgo` and `parse_sort_algo` are the extension
  point; adding insertion, selection or shell sort is where the lesson gets
  richer, and the two-level timing already supports it with no further work.
- **Not on the website.** The public docs describe the persistent families; the
  teaching lab is undocumented there. See OI-012, which asks that INX and IDX be
  kept distinct when that page is corrected.
