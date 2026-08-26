---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260826-COWORK-001
  recorded_at_utc: 2026-08-26T22:49:54Z
  agent:
    provider: Anthropic
    product: Cowork
    model: not_exposed
    member: member.ai.claude.cowork
    access_mode: local_write
  attribution:
    authored_by: member.ai.claude.cowork
    planned_by: null
    owner: member.derald
    committer: member.derald
  session:
    id: COWORK-20260826-001
    run_id: COWORK-20260826-001
    chat_reference: not_exposed
    chat_handle: ""
    handle_binding: NOT_RESOLVABLE
    continues_run: COWORK-20260825-001
  project:
    id: project.x64base.runtime
    root: D:/code/ccode
  git:
    branch: development
    baseline_commit: 372c5834ff0ad5252af6a55399f6254d653a9bf7
  authorization:
    requested_by: member.derald
    scope: >
      Rule the additive-LOAD question, then build it. Four grammar answers
      given before implementation: leaf naming with AS override, re-entry
      adds only what is new, SAVE ... ALL, CLI before GUI.
  report:
    path: docs/maintenance/SESSION_CLOSEOUT_R128_ADDITIVE_WORKSPACES_2026-08-26.md
    kind: session_closeout
primary_topics:
  - workspace
  - multi_workspace
  - regression
---

# Session Closeout -- R128, additive OPEN and scoped SAVE (AIF-078)

    Date              : 2026-08-26
    Owning lifecycle  : DotTalk++ SDLC
    SDLC lane         : review
    Truth state       : mixed -- source-evidenced for the defects, runtime-proven
                        for the two behaviours ADDOPEN asserts
    Proof state       : build + transcript, on the authoring toolchain only.
                        NOT registered: there is no proof.* record.

**SCHEMA NOTE, and it is a finding rather than a preference.** This envelope is
`ai-report-audit-v1`. `AI_PORTAL.md` says new closeouts SHOULD use
`ai-report-audit-v2`; `AI_REPORT_AUDIT_V2_SPEC.md` carries a 2026-07-29
correction (AIF-074) saying the live validator REJECTS v2 and to author v1 with
v2 fields added additively. Measured rather than chosen:
`labtalk/registries/ai_report_audit.yaml:4` pins `schema: ai-report-audit-v1`.
The registry is the enforcement authority, so the spec's correction is current
and the `AI_PORTAL.md` sentence is the drifted one. The v2 attribution and
session fields are present additively, as the spec instructs.

## One-line summary

An owner ruling made WORKSPACE OPEN and LOAD additive and SAVE and CLOSE scoped
to one workspace; it was ruled, implemented on both surfaces, measured against a
baseline binary built from the same tree, and landed in three commits.

## Changed (development, D:\code\ccode)

| Area | Files | Note |
| --- | --- | --- |
| ruling | `docs/maintenance/R128_ADDITIVE_LOAD_AND_SCOPED_CLOSE_SAVE_RULING_V1.md`, one `R_RULING_REGISTER_V1.md` row | R128 from `next_r.py`, collision gate PASS |
| CLI | `src/cli/cmd_workspace.cpp` | scope computed once, consulted four times; OPEN asks the allocator instead of assuming slots 0..N-1 |
| engine header | `include/xbase/workspace_naming.hpp` (new) | directory-to-name rule, header-only, both targets already link `xbase` |
| GUI | `src/gui/core/session.cpp` | three close-all sites; the GUI can now be IN a workspace |
| spec | `dottalkpp/data/scripts/workspace_additive_open.dts` (new), `src/cli/cmd_regression.cpp` | ADDOPEN, explicit-run, array 56 -> 57 |
| fixture | `src/tests/test_gui_area_membership.cpp` | reads the joined handle off the model; G2 added; one dead arm removed |

Commits: `7f7f1b252` (ruling), `d7ca31d6b` (CLI + header + spec),
`6c3809eed` (GUI + fixture). Every blob at HEAD was hashed against the copies
that were actually compiled and run; all six match.

## What was proven, and on what

    baseline vs R128    two binaries from the same tree, LEAN/INDEX_MODE=NONE.
                        ADDOPEN: baseline T1/T2/T4/T5 .F., R128 all eight .T.
    default suite       REGRESSION ALL, 55 markers, BYTE-IDENTICAL to baseline.
                        31 .T. / 24 .F. -- the reds are the authoring
                        container's missing fixtures, identically red on both
                        binaries. Not a green suite and not claimed as one.
    maintainer profile  rebuilt under DEVELOPMENT/LMDB (the pro-md axes) and
                        re-ran ADDOPEN: eight green. A second platform
                        confirmation, NOT a second A/B.
    GUI                 dottalk_gui_core builds clean; five tests pass
                        (gui_area_membership, gui_match_count,
                        workspace_membership, relation_merge, area_alloc).

Not reached: no host toolchain run, and the Qt application was never launched.
Everything is g++ 13.3 on Linux. A sandbox green is not a green on MSVC.

## Three defects the machine found and reading did not

1. **Removing the close-all alone would have been WORSE than the defect.**
   `schema_open_directory` walked slots 0,1,2..N-1 and CLOSED whatever sat in
   each -- safe only because the caller had just closed everything. Made
   additive over an unchanged loop it stomps the low slots, which is where
   another workspace's areas live.
2. **The re-entry guard had the AIF-118 shape.** The first cut decided re-entry
   on the NAME alone, which answers the same for "the same directory again" and
   "a different directory whose leaf collides". Measured live: with SALES open
   from `dbf/SALES`, `WORKSPACE OPEN other/SALES` walked into the first
   workspace and opened a foreign table into it.
3. **`label` is provenance, not a name.** The GUI mirror took the posture label
   as a workspace name; its three call sites pass a whole `schema_path.string()`,
   `"memo:" + name` and `"minidb:" + name`.
   `dottalkpp_gui_area_membership_test` went RED with its own G1 guard still
   green -- both tables opened, membership did not grow -- which is the
   signature of a placement fault rather than an open fault.

Two more caught by guards rather than by review: an edit that added a third
ADDOPEN fixture put its `SET PATH` before the second table's `CREATE`, so
WAOT2 was built in the wrong directory and G1 went red on BOTH binaries; and
WAO_T5 read GREEN on both binaries in its first cut, because under the
replacing OPEN there is never a second populated workspace to save from --
**the additive defect was masking the save defect.** T5 now builds its
workspaces with NEW and ADD, which R128 does not touch.

## A side effect the diff does not show

A workspace is born durable, so the first `WORKSPACE OPEN <dir>` for a given
directory name appends a BIRTH row to `WORKSPACES.dbf`. The most common
invocation there is -- bare `WORKSPACE OPEN DBF` -- now has a persistent effect
a read-shaped verb did not have before. Measured rather than feared: three
consecutive runs produce ONE row, not three; the later ones adopt. Amplified
rather than introduced: `WS_NAME` is the catalog key, so two unrelated trees
whose DBF leaf matches share one durable chain -- always true of hand-chosen
names, now ordinary because names come from directories.

## Reported to other areas, not fixed here

- **`tools/staging/check_sandbox_git_guard.py`**: `return 2` sits OUTSIDE its
  own if/else, so a zero-byte stale lock and a live commit's lock return the
  same code, and `prepush_gate` renders both as "a stale .git/index.lock is
  present". It only bites `git commit -- <pathspec>`, which takes the lock
  before the hook runs. AIF-082's lane. **Caused by advice in this session**:
  the pathspec form was recommended to keep `TIER0_STATE.md` out of a commit --
  which was itself wrong, because `tier0-refresh` regenerates and includes that
  file BY DESIGN, as both commits printed.
- **`labtalk/registries/ai_report_index.yaml` is behind**: zero entries for
  `AIPR-20260826`, though three Codex closeouts carry those ids today.
  `AI_README.md` tells agents to resolve reports through that index rather than
  grepping, so a stale index quietly defeats the instruction.
  `audit_trail.py --emit-index` regenerates it.
- **`quip read --ack` cannot ack across a mounted tree** -- `--ack` deletes the
  quip file and the mount forbids unlink; `acked 0 of 4`. This is the SAME
  defect the 2026-08-19 Session Log row already reported for
  `session_coordinator.py unlock`. A second instance, not a new finding.
- **`CLAIMED AIF-043` left no trace**: no claim file, no intake row, while
  `next_aif.py` reports 134. Unresolved; raised to the owner.

- **This lane cites `claude/*.md` as repo paths and they are not.** `claude/`
  does not exist in this tree and is not ignored -- those are claude.ai Project
  docs, so a reader with a clone cannot follow them. It predates this session
  (`AIF078_MULTI_WORKSPACE_STAGED_PLAN_V1.md:578`) and the committed R128 ruling
  repeats it at `:17`. **The cited-paths gate passes them silently**, which is
  R75's lesson in a new place: a gate sees the shape it was built to see, and
  its silence about a class of thing is not evidence the class is clean. Named
  for retargeting rather than rewritten in a landed commit.

## Closeout updates startup (AIF-006)

- `docs/agents/CURRENT_TARGET.md` -- **no change**. It declares no controlling
  lane and deliberately carries no lane state.
- `AI_README.md` -- **no change**. Branch and authority pointers unmoved.
- `docs/ai-friendly/AI_FRIENDLY_DASHBOARD_V1.md` -- **Session Log row added.**
- `docs/ai-friendly/AI_INTERACTION_INTAKE_QUEUE_V1.md` -- **no change**. R128 is
  a ruling in an existing lane; no new intake row.
- `agent-sync.mdx` on the website -- **explicitly declined.** Publication ascent
  is a separate authorization domain and was not granted. Codex published an
  Alpha treatment of this lane on 2026-08-26 and posted it to the board; that
  page is upstream of nothing here.

## Still open

1. **The proof record.** `proof_state` is `runtime_observed` and registered
   nowhere. A `SYSPROOF` write is governed CRUD and nobody authorised one.
2. **Index attachment is not exercised.** The rewritten OPEN loop still calls
   `find_index_for_open_area` and `attach_workspace_index` untouched, but the
   ADDOPEN fixtures carry no index, so a green under LMDB proves the build and
   the areas, not the attachment. Unchanged BY INSPECTION is not unchanged by
   measurement. Closing it needs an indexed fixture.
3. **No fixture for the GUI additive property.** An arm asserting it was written
   and DELETED rather than kept: it ran after the Session was destroyed, where
   both sides are zero under every implementation, so it could not go red.
4. **Not ruled**: what a second OPEN of an already-open directory reconciles;
   whether a per-workspace close also DESTROYs; relations still cleared
   globally on a scoped CLI close; the UI shape.

R128 ships **review-needed**. The author does not self-approve.
