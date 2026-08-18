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
      not be bound into pydottalk. Source-evidenced; not run this session.
  report:
    path: docs/maintenance/EDU_IDX_TIMED_SORT_LAB_V1.md
    kind: design_note
---

# EDU IDX -- the timed sort lab

Status: design note, review-needed. Owner: member.derald.
Author: member.ai.claude.cowork. Date: 2026-08-17.
Source: `src/cli/cmd_idx.cpp`, `include/cli/edu_idx.hpp`.
Evidence class: **source-evidenced**. The lab was read, not run, this session.

## What it is

`IDX` is a **memory-only educational index lab**, `category: education`, for
teaching sorting and index concepts without writing persistent files. Its own
header states the boundary twice:

> "IDX is the EDU IDX command surface: a memory-only educational index lab.
> It is intentionally orthogonal to persistent index families."

> "IDX does not write `.inx` files and does not participate in `SET ORDER`,
> `REINDEX`, `WORKSPACE` restore, `IndexManager`, or `IIndexBackend`."

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

- **Not run this session.** Everything above is read from source. A runtime
  proof capturing an actual STD-vs-BUBBLE comparison on a known table would
  make this runtime-evidenced and would be a good teaching artifact in its own
  right.
- **Two algorithms today.** `SortAlgo` and `parse_sort_algo` are the extension
  point; adding insertion, selection or shell sort is where the lesson gets
  richer, and the two-level timing already supports it with no further work.
- **Not on the website.** The public docs describe the persistent families; the
  teaching lab is undocumented there. See OI-012, which asks that INX and IDX be
  kept distinct when that page is corrected.
