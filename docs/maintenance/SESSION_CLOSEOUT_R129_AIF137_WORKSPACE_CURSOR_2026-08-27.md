---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260827-COWORK-001
  recorded_at_utc: 2026-08-27T11:20:00Z
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
    id: COWORK-20260827-001
    run_id: COWORK-20260827-001
    chat_reference: not_exposed
    chat_handle: ""
    handle_binding: NOT_RESOLVABLE
    continues_run: COWORK-20260826-001
  project:
    id: project.x64base.runtime
    root: D:/code/ccode
  git:
    branch: development
    baseline_commit: 21830b9a5558e7d8e05c5db6a3b753287a006217
  authorization:
    requested_by: member.derald
    scope: >
      Design the workspace cursor, draft it as a ruling, reconcile with the
      owner-accepted Grok precepts, run the R112 ambiguity ledger, and claim
      an AIF number for what the run found. Documents only -- no src/**.
  report:
    path: docs/maintenance/SESSION_CLOSEOUT_R129_AIF137_WORKSPACE_CURSOR_2026-08-27.md
    kind: session_closeout
primary_topics:
  - workspace
  - multi_workspace
  - name_resolution
  - relations
  - workspace_cursor
---

# Session Closeout -- R129 (workspace cursor) and AIF-137 (relation parent), 2026-08-27

    Date              : 2026-08-27
    Owning lifecycle  : DotTalk++ SDLC
    SDLC lane         : review
    Truth state       : mixed -- source-evidenced for the cursor model,
                        RUNTIME-PROVEN for AIF-137 and for the SELECT crossing
    Proof state       : one interactive CLI transcript, authoring toolchain
                        only. NOT registered: there is no proof.* record.
    Mutation          : documents only. NO src/**, NO build, NO data fixture
                        edits. Two superseded rows added to WORKSPACES.dbf as
                        a measured side effect of the run (sec 5).

**SCHEMA NOTE.** This envelope is `ai-report-audit-v1`, measured rather than
chosen: `labtalk/registries/ai_report_audit.yaml:4` pins v1, and
`AI_REPORT_AUDIT_V2_SPEC.md` carries the 2026-07-29 correction (AIF-074) that
the live validator REJECTS v2 and to author v1 with v2 fields added
additively. `AI_PORTAL.md` still says v2; the registry is the enforcement
authority, so `AI_PORTAL.md` is the drifted sentence. Unchanged from the
2026-08-26 closeout, restated because a note nobody repeats becomes a
rediscovery.

## One-line summary

A design conversation about workspace addressing became a ruling draft, was
reconciled against an owner-accepted external precepts packet, and then a live
run of an instrument built in August 2026 found a workspace-blind resolver in
the relation refresh path -- which had been predicted in writing on 2026-08-23
and never measured until now.

## What was produced

    docs/maintenance/R129_WORKSPACE_CURSOR_RULING_V1.md
    docs/maintenance/AIF137_FINDING_RELATION_PARENT_IS_WORKSPACE_BLIND_V1.md
    docs/maintenance/AIF138_FINDING_AREA_CURSOR_CANNOT_SAY_NOTHING_V1.md
    docs/maintenance/SESSION_CLOSEOUT_R129_AIF137_WORKSPACE_CURSOR_2026-08-27.md
    coordination/aif/AIF-137.claim                (written by the allocator)
    coordination/aif/AIF-138.claim                (written by the allocator)

R129 was allocated by `tools\coordination\next_r.py` (union of the declared
register and 126 tree citations; highest taken R128). AIF-137 was allocated by
`session_coordinator.py claim-aif` with NO number passed, so `O_EXCL` chose.
**Neither number was picked by hand, and the AIF claim file was verified
present after the tool printed success** -- a `CLAIMED AIF-nnn` line that left
no claim file was reported on 2026-08-26, so the check is now part of the
procedure rather than an assumption.

## The measurement

RUNTIME-PROVEN. Interactive CLI, `.\datarun.ps1`, read-only on the tables.
Two directories sharing eight basenames: `dottalkpp\data\dbf\x64` and
`...\dbf\x32`.

**THE BINARY WAS IDENTIFIED BEHAVIOURALLY.** It reports
`v0.6 (2026-08-24, c39d966c dirty)` -- a date BEFORE R128 landed, so the
version string cannot identify it. The evidence is in the transcript: the
second `WORKSPACE OPEN` placed 13 tables at slots 13..25 with the first
workspace's 13 still standing at 0..12.

Three findings, in the order they arrived:

1. **The R112 ambiguity ledger fired on the second OPEN, before any table
   name was typed** -- `BUILDING` resolved from workspace 3 to workspace 2's
   area 0, tagged `REL refresh parent`.
2. **`REL LIST` showed an EMPTY store.** No relation existed. The parent was
   inferred from the work area and the inferred parent was foreign. This is
   AIF-137.
3. **`SELECT students` from inside WSX32 selected WSX64's table** (area 8)
   while WSX32's own sat at area 21, and said nothing about it.

And a fourth, about the instrument itself: **the ledger did not record the
SELECT.** `cmd_select.cpp` runs its own scan and does not call the recording
resolver, so R112 sec 6a's "measured zero" gate is currently blind to one of
its own crossing paths. Its count is a floor.

## What was ruled, and by whom

- **Part 1 of R129 by the owner**, before the measurement: there is a
  workspace cursor and it is a peer of the area and row cursors.
- **R129 sec 6.1, 6.1a and 6.2 by the owner**, AFTER the measurement and after
  the external answers: *"I think all in 6.x are valid, especially allowing an
  empty workspace, there will be times we want to open and add to it. You have
  to have a place to start."* / *"6.2 is valid"* -- with the risk accepted
  explicitly: *"If it turns [out] wrong we will find out quickly."* **The
  ordering matters: the first cut of 6.2 proposed a blanket refusal and would
  have been ruled wrong. The transcript showed the case was a LOCAL name being
  ignored, not a boundary policy being absent.**
- **P6 (unqualified names) by the owner** in the Grok precepts packet
  `AIPR-20260827-GROK-001`, owner-accepted 2026-08-27. R129 CITES it and does
  not restate it; the section that duplicated it was struck.
- **Nothing else.** No code is authorized and no fix is designed for either
  finding.

## What the author got wrong, and where it is recorded

Four corrections, all in R129 sec 10:

1. The first cut did not cite R112 at all and wrote as though cross-workspace
   ambiguity were unconsidered. It was ruled 2026-08-22 and instrumented.
   Found by reading the external packet.
2. "Three resolvers" was an undercount; `find_open_area_by_name_ci` with 36
   call sites is a fourth and the instrumented one.
3. `SELECT` REFUSE across a boundary was wrong -- P6 already answers it, the
   local name wins, and refusal belongs only where the name is absent here and
   present elsewhere. The error was reasoning about the crossing when the
   question was resolution.
4. A criticism of the external packet's directory layout was withdrawn: the
   layout is an established convention six packets deep, and the check that
   "found" it missing looked in a tree the packets do not live in. **R75.**

A fifth, in the finding: the fix framing was "add a workspace filter", and the
root cause is sharper -- `infer_parent_from_workarea()` HOLDS the `DbArea*`
and returns its name, then the caller searches the process to find the area
back and finds a different one. **The round trip loses identity.** Named by
the external reviewer, confirmed in source here.

## Residue, stated

The run minted WS_ID 208 and 209 under D10.1 and retired both by supersession
(D10.3). Two superseded rows remain in `WORKSPACES.dbf` as history; names are
free; handles 2 and 3 are not reused. Precept P3 proposes ending that mint.

## What is open

- **AIF-138** -- "what does the area cursor point at inside an EMPTY
  workspace" turned out not to be a workspace question. `Engine::_current`
  cannot express "nothing selected", and slot 0 means area 0, the startup
  position (`shell.cpp:528`) AND "no engine" (`workareas.hpp:120`). Separated
  out of R129 and claimed. **The author answered R129 sec 6.1a wrongly TWICE
  -- first a closed slot, then an invariant stated over `wsHandle()` alone
  that accepts a MISSED MEMBERSHIP STAMP as a legal position -- and the owner
  caught both, in two words each.** Recorded in R129 sec 10 item 7: the method
  error was verifying whether CLOSE produced a safe READING instead of whether
  the cursor could SAY "nothing", when R6 is a rule about representation.
- **AIF-138's REPRESENTATION** -- ruling 6.1a made the empty-workspace
  position legal and deliberately did NOT choose how the cursor says it
  (sentinel, `optional`, or a `hasCurrent()` predicate). Choosing a
  representation before counting the `currentArea()` readers is what produced
  the two withdrawn answers, so the count comes first.
- **6.2 consequence (a), watch it in use** -- in an EMPTY workspace arm 1 can
  never apply, so every name refuses or misses. Correct under the ruling, and
  the owner accepted the risk knowing it would show up fast. If it reads badly
  in practice, 6.1a is the section to reopen.
- **AIF-137** -- no fix authorized. The split of 36 call sites into scoped /
  given-handle / explicit-cross is named, not designed.
- **The R112 instrument** -- tag `cmd_select` before anyone treats the count
  as a measurement, and decide whether the target is a zero or a refusal
  counter.
- **The CLI LOAD half of R128** -- `schema_close_all()` at
  `cmd_workspace.cpp:2405`, open since 2026-08-26.

## Verify or undo

- Verify AIF-137 by re-running the sequence in its sec 2 against any
  R128-or-later binary. It fired on the first attempt with no tuning.
- Undo: delete the three documents and release AIF-137 with
  `session_coordinator.py release-aif`. Nothing else was changed.
