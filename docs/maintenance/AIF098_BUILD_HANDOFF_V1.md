# AIF-098 build handoff -- Lane 1 write adapter (consolidated-from-chat post kind)

`RECURSED BACK <- frame 0 (Grok Lane 1)`: scope + review + ground-check are complete; this hands
the engine-bound half to the **next build** (a host-capable session -- the sandbox and Grok both
sit behind the capability fence and cannot build/run). See `RECURSION_MARKERS_V1.md`.

**Status:** apply-ready. AIF-098 claimed + tracked (`coordination/aif/AIF-098.claim`), intake row
filed, R2 patches ground-checked PASS. Owner `member.derald`; steward `member.ai.claude.cowork`;
coworker Grok (authored the engine-bound half). Run: `COWORK-20260808-001`.

## Already done -- do NOT redo

- Engine-free half built + tested (Claude): `tools/memory/consolidate.py` (triage value fn),
  `tools/memory/promote.py` (attributed `BBS POST` + `.dts` renderer).
- Grok R2 package authored, AIF-098 claimed and stamped into it.
- Ground-check PASS against live `development` source -- see the `GROUND-CHECK: PASS` section of
  `READY_TO_APPLY_PATCHES.md` (all four patches faithful; `KIND=0` preserved for normal posts;
  marker parse verified against `promote.py`).

## Step 1 -- apply the four patches (verbatim from `READY_TO_APPLY_PATCHES.md`)

1. `include/bbs/bbs_schema.hpp` -- add `C("SRCLANE", w::KEY)` to `syspost()`; update the KIND
   comment (5=consolidated_from_chat).
2. `include/bbs/bbs_store.hpp` -- `Post` struct `+= src_lane`; `post_new` decl `+= (int post_kind
   = 0, const std::string& src_lane = "")` (defaults keep every call site source-compatible).
3. `src/bbs/bbs_store.cpp` -- `post_new`: `KIND` write becomes `s_int(post_kind)`, add
   `w.set("SRCLANE", src_lane)`; leave `RUNID` empty. `reply_to` unchanged.
4. `src/cli/cmd_bbs.cpp` -- `do_post`: detect `[consolidated:<lane>]` -> `post_kind=5` + `src_lane`,
   pass both to `post_new`.

## Step 2 -- GATE CATCH (mandatory; read before the proof)

The BBS store has **no column-add path** -- `ensure_bbs_tables` tops up missing *rows* (boards),
not missing *fields*. So on an existing `SYSPOST.DBF` (old schema), `w.set("SRCLANE", ...)` writes
to a column that is not there.

- **Proof:** run against a **fresh / re-seeded `SYSPOST`** (the new schema carries `SRCLANE`), the
  way the `INDEX_X64` smokes build throwaway tables. Do NOT run the proof against the old live store.
- **Production** (a store with real posts): a non-destructive `SRCLANE` migration is a **follow-up
  milestone** of AIF-098. Never force a destructive re-seed.

## Step 3 -- build

- Stop the daemon first (it locks the exe -> LNK1104): `Stop-ScheduledTask -TaskName 'DotTalkBBSD'`.
- `cmake --build build --target dottalkpp dottalk_bbsd --config Release`
- Restart `DotTalkBBSD` when done.

## Step 4 -- verify (Grok's `notes/VERIFICATION_PROCEDURE.md` `.dts`, via `./datarun.ps1` as a logged-in member)

On the fresh store, assert:
- `AUTHORID != 0` (attributed; anon POST denied -- AIF-075)
- `KIND == 5` for a consolidated post; `KIND == 0` unchanged for a normal post
- `SRCLANE` holds the lane token; `RUNID` empty

**Paste the `datarun` output back to Claude (Cowork) to adjudicate the four assertions** -- do not
self-certify the proof (golden rule: assert only what was run and read).

## Step 5 -- close

- Add a regression locking `KIND==5` + `SRCLANE` for a `promote.py` `.dts` (self-bootstrapping
  throwaway `SYSPOST` in SANDBOX; register in `src/cli/cmd_regression.cpp` alongside `BBS_LANE`).
- Scoped per-path commit; `git status --short` between add and commit; prepush gate.
- Register the lane under its parent project; keep the AIF-098 intake row as the record.
- Follow-up milestone: the non-destructive `SRCLANE` migration for existing stores.

## Pointers

`READY_TO_APPLY_PATCHES.md` (patches + ground-check verdict + gate catch) -- primary.
`GROK_PUSH_L1_WRITE_ADAPTER_V1.md`, `LANE_L1_WRITE_ADAPTER_ASSIGNMENT_GROK_V1.md` (assignment).
`proof.grok_lane1_coworker_kind_collision` (the team-model + KIND=3 catch).
AIF-098 intake row in `docs/ai-friendly/AI_INTERACTION_INTAKE_QUEUE_V1.md`.
