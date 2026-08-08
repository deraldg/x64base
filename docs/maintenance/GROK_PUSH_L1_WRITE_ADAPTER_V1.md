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
