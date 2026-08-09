# Grok push: Lane 1 write adapter (Frontal_Mem M2) -- relayable brief

**Status:** open handoff (review-needed). Owner: member.derald. Date 2026-08-08. Coordinating
agent: Claude (Cowork), run COWORK-20260807-005. Assignee coworker: **Grok**. This is the
self-contained brief to relay to Grok; the full spec is
`docs/maintenance/LANE_L1_WRITE_ADAPTER_ASSIGNMENT_GROK_V1.md`. Registered as recall node
`doc.grok_push` (reached via `trigger.persistent_memory`).

## Context

Repo `ccode`, branch `development`. **`git pull` first** -- the tools and spec are already
committed (`ac623ce46`, `d5120fe40`). You are the coworker on the engine-bound half; Claude
built and tested the engine-free half.

## Read first (use the search map, do not scan the tree)

- `docs/maintenance/LANE_L1_WRITE_ADAPTER_ASSIGNMENT_GROK_V1.md` -- your full spec.
- `tools/memory/README.md`, `tools/memory/consolidate.py`, `tools/memory/promote.py` -- the built half.
- `docs/maintenance/DESIGN_bbs_pseudochat_two_lanes.md`, `PLAN_pseudochat_lane.md` (Frontal_Mem folder) -- design + M2.
- `labtalk/ai_portal/PORTAL_SEARCH_MAP_V1.md` -- go straight to targets (BBS grammar is `src/cli/cmd_bbs.cpp` -> `do_post`).

## The split (by capability boundary -- the sandbox cannot run the engine)

- DONE (Claude, engine-free, tested 17/17): the triage value function (`consolidate.py`) and the
  attributed-post renderer (`promote.py`, emits `BBS POST` records + `.dts`).
- YOURS (engine-bound): the durable write and the store/UX seams.

## Your deliverables

1. **Run and verify the attributed write.** Take `promote.py`'s `.dts`, write via `./datarun.ps1`
   as a logged-in member. Verify each post has a real `author_id` (NEVER 0) and the source-lane
   marker; anon POST is denied (AIF-075). Trust the measurement, not the success message.
2. **First-class post `kind`.** Add a source-lane `kind` field in the store (`bbs_store.cpp` /
   `post_new`) so the marker is a real field, not a subject prefix.
3. **Hybrid confirm UX.** Interactive `PSEUDO PROMOTE ... CONFIRM` or a `board.governance`
   approval (reuses the SYSGRANT loop, auditable). Name your choice.
4. **(Optional)** the C++ `PSEUDO` command surface (Lane 2 M1) that buffers turns and consumes
   the same records.

## Contract (the seam)

`promote.py render --manifest <confirmed.json>` emits `posts[]` and a `.dts`. Consume them
verbatim. If a post is wrong, fix the working-set / value-function inputs upstream, not the
rendered post.

## Acceptance (repo idiom = datarun script + assertions)

Proposal requires owner confirm; on confirm the post exists with real `author_id` (not 0) + the
source marker; on decline nothing is written; a duplicate turn makes no duplicate post; a
contradicting turn is flagged (`[reconsolidate vs ...]` already emitted).

## Coordination rules (non-negotiable)

Claim a **fresh AIF** (`session_coordinator.py claim-aif`) -- do NOT reuse AIF-052; register the
lane with the work. Attributed writes only (`current_member()`, never author 0). Scoped per-path
commits, `git status --short` between add and commit, pre-push gate. ASCII only, no em-dashes,
`&&` is the comment marker (BBS bodies comment-free). Use `./datarun.ps1`, not the raw exe; stop
the `DotTalkBBSD` task before rebuilding the daemon (it locks the exe).

## First move

`git pull`, then **accept the lane and pick up this project's frontal memory** --
`python3 labtalk/ai_portal/recall.py trigger.persistent_memory` returns the Frontal_Mem working
set (this push, the consolidation tool, the root pointer). Run general onboarding
(`trigger.onboard`) before or after that pickup, whichever is cheaper for you. Then read the
spec, `claim-aif`, run `promote.py`'s `.dts` against the store, and verify attribution.

## Round 1 review -- ACCEPTED WITH CORRECTIONS (2026-08-08)

Grok accepted the lane and returned a review-needed package `AIPR-20260808-GROK-001` (read-only,
no tree mutation, verification procedure included). It was ground-truthed against source; the
exchange is recorded in `proof.grok_lane1_coworker_kind_collision`. **Three corrections were
issued back to Grok and MUST land before the diff is applied:**

1. **KIND value collides -- use 5, not 3.** `include/bbs/bbs_schema.hpp` already enumerates
   `KIND: 0=post 1=reply 2=agent_prompt 3=agent_reply 4=system`. Grok's proposed
   `KIND=3=consolidated_from_chat` would reclassify every existing `agent_reply` and corrupt
   recall. The next free value is **5**: `KIND=5 = consolidated_from_chat`.
2. **Do not overload `RUNID` for the lane.** Schema defines `RUNID` as an `ai_runs` ref, not a
   free-text tag. Add a dedicated `SYSPOST` field (`SRCLANE`) for the source lane, or link a real
   `ai_runs` row. Keep `RUNID` for its defined purpose.
3. **Do not hard-code `AIF-089`.** Lane numbers are allocated atomically by `claim-aif` (O_EXCL);
   089 is a suspicious lone gap below the 092-097 band. The maintainer runs `claim-aif` and stamps
   the assigned number into the package -- leave it `AIF-<assigned>`.

**Accepted as-is:** `promote.py` records/`.dts` consumed verbatim (judgment not re-opened);
attribution `current_member()` only, author never 0 (AIF-075); confirm-UX = `board.governance` /
SYSGRANT loop (interactive `PSEUDO PROMOTE ... CONFIRM` deferred to Lane 2).

**NEXT ACTION (owner):** send the corrections to Grok; when it re-issues the KIND/`SRCLANE` diff,
run its verification procedure against a real `promote.py` `.dts`. That closes the engine-bound
write half.
