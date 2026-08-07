# AI Run Traceability & Attribution -- Contract v1 (AIF-050 M0)

**Contract id:** `AI_RUN_TRACEABILITY_CONTRACT_V1` - **Status:** candidate (dev-only; not promoted)
- **Filed:** 2026-07-22
- **Owner / authority:** Derald Grimwood (maintainer).
- **Assigned member (steward / author):** `member.ai.claude.cowork` (Cowork / Claude, Anthropic).
- **Lane:** AIF-050 (`AI_RUN_TRACEABILITY_LANE_V1.md`), M0 deliverable.

This contract fixes the vocabulary and the entities the lane builds on, so later milestones
(registry, envelope v2, `@dottalk.file`, the "last agent" pointer) all speak the same terms.

## The problem, in one measurement

A source census of `D:\code\ccode` (`src/` + `include/`, `.cpp`/`.hpp`/`.h`) on 2026-07-22:

| set | count | share |
|---|---:|---:|
| total source files | 1032 | 100% |
| carrying `@dottalk.usage` (commands, harvestable today) | 231 | 22% |
| carrying neither usage nor a file contract (**invisible to the harvest**) | 801 | 78% |

Today's SelfDoc harvest sees roughly one file in five. And for the 22% it does see, it records the
command's *behavior*, never *who authored a change, in which run, or why*. The `@dottalk.file`
universal contract (M2) closes the first gap; this contract fixes the vocabulary for the second.

## The five roles (kept distinct)

Git collapses all of these onto the committer. This contract keeps them separate; each is recorded
once, where it is load-bearing, never as ceremony.

| role | who | recorded where |
|---|---|---|
| **owner / authority** | the maintainer (Derald) -- final say, authorization, sole committer/pusher | project/lane header; not repeated per change |
| **committer** | whoever ran `git commit` (in this project, always the owner) | git (`%an`) -- *not* the record of authorship |
| **author / contributor** | the party that did the work -- human or an identity-catalog **member** (`member.ai.claude.cowork`) | RUN registry + envelope `authored_by` |
| **planner** | the party whose design the work derived from, when it differs from the author (an external AI may plan what a local AI implements) | envelope `planned_by` |
| **attestor** | who vouches for a fact the run could not self-record (e.g. a `chat_handle` the platform stamped `not_exposed`) | `handle_binding: MAINTAINER_ATTESTED` |

**Rule:** *owner != author; committer != contributor.* The owner's name is load-bearing for
authorization, ownership, and commit -- and nowhere else. Stamping it across the record is a
distraction from the truth of who did the work.

## Entities

### RUN
A single working session of a member on a lane.

```
run_id:         AIPR-YYYYMMDD-NNN     # stable, unique; matches the report-audit report_id
member:         member.ai.claude.cowork
product:        Cowork                # provider/product level (Anthropic/Cowork)
project:        project.x64base.<name>
lane:           AIF-NNN
chat_handle:    <resolvable session pointer | null>
handle_binding: SELF_REPORTED | MAINTAINER_ATTESTED | NOT_RESOLVABLE
continues_run:  <prior run_id | null> # runs chain so a lane's history is walkable
started:        <date>
last_closeout:  docs/maintenance/SESSION_CLOSEOUT_*.md
status:         active | closed
```

### CHANGE (provenance row -- the maintained source the `@dottalk.file` pointer resolves to)
One row per unit-of-work touch; lives in the provenance catalog (M2), never embedded in source.

```
unit:        DOT|AREA | file:src/cli/cmd_area.cpp   # the join key
run_id:      AIPR-YYYYMMDD-NNN
authored_by: member.ai.claude.cowork               # true author
planned_by:  member.ai.chatgpt | null              # design origin when different
owner:       member.derald                         # recorded once
committer:   member.derald                         # git reality
date:        <date>
change_ref:  <closeout sec.> | <commit sha>           # the reasoning (pointer, not copied)
summary:     <one line>
```

### Handle bindings
- `SELF_REPORTED` -- the agent supplied a resolvable handle.
- `MAINTAINER_ATTESTED` -- the platform stamped the id `not_exposed`; the owner attests the handle.
  Precedent in-tree: the Pinocchio machine profile is `MAINTAINER_ATTESTED`.
- `NOT_RESOLVABLE` -- no handle exists; the closeout is the only recovery path (which is by design --
  the closeout, not the chat, is the system of record).

## Invariants

1. **Author is first-class.** Every unit of AI work resolves to a `member` + `run_id` without
   reading git.
2. **Owner is recorded once.** The maintainer's name appears where it authorizes/owns/commits, not as
   blanket attribution.
3. **Plan != implementation.** When they differ, both are recorded (`authored_by` / `planned_by`).
4. **The closeout is the record; the chat handle is convenience.** A `NOT_RESOLVABLE` handle loses
   no knowledge -- the closeout still transfers it fully.
5. **The census is complete or its exceptions are listed.** Every source file is either in the
   `@dottalk.file` census or explicitly exempt.
6. **AIF-number assignment is single-writer.** A unique id cannot be allocated by many agents
   appending to a shared file concurrently -- proven live during this lane's drafting, where four
   parallel Cowork sessions collided on AIF-047 -> 048 -> 050 in one sitting. Either the maintainer is
   the sole assigner, or the RUN registry provides an atomic "claim next-free." A free-for-all intake
   queue is a race by construction and must not be the allocator.

## Cross-references

- Lane: `AI_RUN_TRACEABILITY_LANE_V1.md` (AIF-050).
- Extends: AIF-020 report-audit envelope, AIF-045 identity (member != run), AIF-042 contract harvester.
- Registry (M1): `labtalk/registries/ai_runs.yaml`.
