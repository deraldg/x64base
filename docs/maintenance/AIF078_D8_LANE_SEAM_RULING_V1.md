---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260822-COWORK-113
  recorded_at_utc: 2026-08-22T22:20:00Z
  agent:
    provider: Anthropic
    product: Claude (Cowork)
    model: claude-opus-5
    access_mode: local_write
  session:
    id: not_exposed
    chat_reference: GUI API
    run_id: COWORK-20260822-001
  project:
    id: project.x64base.runtime
    root: D:/code/ccode
  git:
    branch: development
    baseline_commit: eef1cf5ea
  authorization:
    requested_by: maintainer (member.derald), in-session 2026-08-22 -- "1 is your
      so you resolve it", then "now that you know better do better". Authorises
      this ruling. Authorises NO code.
  review:
    first_draft: rejected by independent review, same session. Four blocking
      findings. See sec 10.
  report:
    path: docs/maintenance/AIF078_D8_LANE_SEAM_RULING_V1.md
    kind: ruling
---

# AIF-078 -- D8: the seam is PERSISTENCE vs RUNTIME, and the live relation graph is runtime

Status: **ruling, review-needed.** Author does not self-approve.
Owner: member.derald. Author: member.ai.claude.cowork, run `COWORK-20260822-001`.
Date: 2026-08-22. Baseline `eef1cf5ea`. Claim: AIF-078 (held by this member).

**This document authorises no build.** It answers Q-R2 of
`WORKSPACE_RUNTIME_RECONCILIATION_AIF070_AIF078_V1.md` and scopes ownership so
that **D9** can rule on the relation key. It does not start I1.2.

**D8 in AIF-078's own D-series**, continuing D1-D7 in
`AIF078_MULTI_WORKSPACE_STAGED_PLAN_V1.md:148-182`. D7 is the steward's
`SET RECURSION ON | OFF` decision at `:182`; an earlier draft of this ruling
took that number and is withdrawn (sec 10).

## 1. The question

Doc 1 (`AIPR-20260801-003`, review-needed, never signed off) left six open
questions. **Q-R2** was the only one it called a genuine overlap:

> **The single genuine overlap is the runtime registry.** Both lanes need one
> object that knows which workspaces exist and which areas belong to which.
> Proposed: **AIF-078 builds it, AIF-070 consumes it.**

The steward handed the question to this lane. This is the answer.

## 2. The ruling

> **D8.** The AIF-070 / AIF-078 seam is **persistence vs runtime**, not Doc 1's
> *"what a workspace IS"* vs *"how workspaces are ADDRESSED and GROUPED."*
>
> - **AIF-070 owns PERSISTENCE.** The catalog (`WORKSPACES.dbf`, catalog v2)
>   holds durable identity: `WS_ID`, `WS_NAME`, and a saved posture's `AREA`
>   lines as the child list at rest. DTSHEMA versioning, scoped `WORKSPACE SAVE`,
>   memo-resident hydration, vdisk, per-area `kind`.
> - **AIF-078 owns RUNTIME.** Which workspaces are open now, which areas belong
>   to which, the session-local handle and its allocation, the current-handle
>   notion, name resolution among open objects, and ambiguity reporting.
> - **Q-R2 CLOSED: the runtime registry is AIF-078's.** AIF-070 consumes it.

**D8.1 -- the live relation store is runtime, and this ruling is the one the
plan deferred to.** `AIF078_MULTI_WORKSPACE_STAGED_PLAN_V1.md:279-281` places
workspace-scoped relations out of scope with the words *"Own ruling, own work."*
**D8/D9 are that ruling.** This is not a claim on unassigned territory -- the
lane scoped the object and named a successor; this is the successor.

**D8.2 -- the seam cuts through the relation subsystem at SERIALIZATION, and it
has one straddler that must be assigned rather than assumed away.** The live
store (`relations_store()`, `src/cli/set_relations.cpp:60`) is runtime.
**A persisted relation format already exists and this ruling does not touch
it:** DTSHEMA postures carry `RELATION <parent> <child> ON <key>` lines, written
at `src/gui/core/session.cpp:2093-2100` and read at `:545-559`. A second
interchange form, `RelationSpec` (`src/cli/set_relations.hpp:123-135`), carries
names only. **AIF-078 will not invent a third**, and will not version either.

The straddler is `WorkspaceRelationInfo` (`include/gui/core/model.hpp:160-171`),
which is simultaneously the parse target of a saved posture and the live GUI
model row (`model.hpp:180`). **It is assigned to AIF-078 for its runtime
identity only** -- see D9 -- and its persisted spelling stays with whoever owns
DTSHEMA. Assigning it is the honest move; an unassigned straddler is the defect
Doc 1's seam had.

**D8.3 -- `declare()` is the nominated consumption seam and it is not yet fit
for it.** `include/xbase/workspace_membership.hpp:306-310` is
`table()[h].name = nm; return true;`. It sets a name. It does not set a parent,
does not guard an existing entry, and does not advance the allocator, and it has
**zero callers** -- as do `destroy` and the reparent verb. Nominating it as the
seam is a statement of intent, and the gap is recorded rather than described as
built.

## 3. Why this seam and not Doc 1's

1. **Doc 1's cut cannot be applied as a test.** Handle allocation is
   simultaneously *what a workspace is* and *how it is addressed*. Doc 1 felt
   this and carved the registry out as "the single genuine overlap." An overlap
   in a boundary is a boundary that does not cut.
2. **Doc 1 sec 4's model lost to events.** Its groups model (*"Groups are
   membership, not containment ... a set/graph model, not a tree"*) was
   superseded by the later maintainer ruling quoted at
   `workspace_membership.hpp:70-74` -- *"multiple workspaces is just a workspace
   of workspaces of areas"* -- which restores a parent pointer. What shipped has
   parents, `would_cycle()` (`:183`) and `kMaxWorkspaceDepth = 32` (`:116`).
   **Doc 1 sec 4 should be marked superseded by events.** Note the consequence:
   Doc 1 line 133 proposed a *group* registry; what exists is a *tree* registry.
   The object matches the proposal in role, not in shape.
3. **The code already states a better seam.** `workspace_membership.hpp:20-25`:
   the catalog is *"the persistence authority ... None of that answers 'which
   areas are open in which workspace RIGHT NOW', and a workspace can be open
   having never been saved. That is session state, and this is where it lives."*
   D8 promotes that sentence to a ruling.

**Honest limit, and it is the same test D8 applies to Doc 1.** This seam has one
straddler (D8.2) and one policy flag that sits on the wrong side of it:
`recursion_enabled_ref()` (`workspace_membership.hpp:104-106`) is a
process-global mutable setting living inside the runtime-membership object, set
from `SET RECURSION` (`src/cli/cmd_set.cpp:1428`). It is session settings, not
membership. **The claim is that this seam cuts BETTER, not that it cuts
perfectly.** Two named straddlers beats one unnamed overlap; it is not zero.

## 4. What has actually moved, measured -- correcting this ruling's own first draft

Doc 1 sec 5 (`:139-147`) lists seven process-global objects. An earlier draft
claimed six had moved. **That was false.** Re-measured:

| Doc 1 item | State 2026-08-22 |
|---|---|
| the single engine | `src/cli/shell.cpp:527` `XBaseEngine eng;` unchanged. Doc 1 said it stays one engine -- **not a defect** |
| the slot array | `include/xbase.hpp:562` still `std::array<..., MAX_AREA>`; a parallel owner map now exists alongside. **Partial** |
| work-area facade | `src/cli/workareas.hpp:169` `global()` -- zero `workspace` references in the file. **Not moved** |
| per-area state | `src/cli/table_state.cpp:79-82` `static std::array<AreaState, MAX_AREA>` -- zero `workspace` references. **Not moved** |
| **the relation graph** | **Not moved.** D9's subject |
| name resolution | `src/cli/workarea_util.cpp:49-60` walks every slot with **no handle filter**. Doc 1 required *"must gain scope and must report ambiguity."* It gained the ambiguity ledger (`:94-133`); **it did not gain scope.** Half |
| last-loaded workspace | `src/cli/cmd_workspace.cpp:264-265` still one `static std::string`. **Not moved** |

**One of seven moved cleanly; two moved in part; four are untouched.** The
relation graph is not a lone straggler -- it is the sharpest of five. That is a
weaker position than the first draft claimed and a more accurate one, and it
changes the sequencing argument: D9 is not the last item, it is the first of
several, and the others need owners too.

## 5. What this ruling deliberately does NOT do

**It does not reconcile with AIF-070, because AIF-070 cannot presently be
reconciled with.** Measured:

- `coordination/aif/AIF-070.claim` is **five lines** -- aif, run_id, member
  (`member.ai.grok.xai`), lane (`workspace.virtual_and_memo_resident`),
  claimed_utc. `.claim` files carry no scope and no status **by design**;
  `AIF-078.claim` is the identical shape. AIF-070 is not under-documented
  relative to its peers here.
- `grep -rn "AIF-070" coordination/` returns **exactly one line in the whole
  tree** -- the claim naming itself. **No intake row**, three weeks after Doc 1
  recorded it as owed. The declared-but-absent intake artifact is filed under
  **AIF-055** (`Doc 1:64`), so searching for "AIF-070" misses it even if
  delivered.
- The whitepaper is **absent**. The only extant description of AIF-070's scope
  is Doc 1 sec 2, **written by this lane from a MANIFEST abstract**, self-tiered
  *"design-intended, and abstract only."*

**A boundary cannot be negotiated with an absent counterparty.** What D8 does
instead is bound THIS lane, so AIF-070's steward can object to a specific list
rather than to a vacuum. Every item in D8's persistence column is a standoff.

**Still owed, and it is the maintainer's** (Doc 1:73): obtain the whitepaper, or
rule that the MANIFEST abstract is AIF-070's design authority of record. Plus
the intake row and the AIF-055/AIF-070 number mismatch.

**Reversibility.** Doc 1:71 already established the precedence -- *"Anything in
the whitepaper that contradicts sec 3 below will win"* -- and D8 adopts it
unchanged. D8 assigns ownership, not structure; reversing it costs a document.

## 6. Registry consumers -- the blast radius of D8, measured

An earlier draft named one file. Live consumers of `xbase::workspace`:

    src/cli/cmd_workspace.cpp   create :3937, set_current_handle :3961,
                                close/registry :1355-1528, resolution :3728-3731,
                                diagnostics :3839-3854
    src/cli/cmd_set.cpp         SET RECURSION -- recursion_enabled() :1409-1427,
                                set_recursion_enabled :1428
    src/cli/cmd_use.cpp         AIF-121 USE ... IN FREE -- current_handle()/
                                members() :442-456, name_of :824, wsHandle :1069-1076
    src/cli/workarea_util.cpp   ambiguity ledger records wsHandle() :117

**The verbs are `WORKSPACE NEW` and `WORKSPACE SWITCH`** (`cmd_workspace.cpp:3891`,
`:3949`; registered `src/cli/shell_commands.cpp:404`). There is no
`WORKSPACE CREATE` -- an earlier draft of this ruling told the reader to type
one, and it falls through to *"Unknown subcommand."*

## 7. Consequences for the staged plan

Amendments are folded into `AIF078_MULTI_WORKSPACE_STAGED_PLAN_V1.md` under a
dated section rather than restated here. In summary: stage 2's choke-point half
shipped and its catalog-handoff and relation-handle halves did not; stage 4's
two-workspace precondition is **met and mutation-tested**
(`dottalkpp/data/scripts/workspace_multi_regression.dts`, four workspaces,
eleven markers, 2026-08-22) though that script is **not registered** in
`kRegressionSpecs`; the four `A.B.C` splitters are in no stage; and
`set_relations.cpp:171-178` `slot_of_area_ptr` is a **leftover duplicate** of
`cli::slot_of_area` (`src/cli/workarea_util.cpp:174-180`, AIF-120 I1.1) sitting
three lines below that refactor's own `using` import. It is not merely slower:
I1.1's note records that the shared version *"answers correctly for a closed
area too -- the old scan did not"*, so the duplicate is also **behaviourally
wrong for a closed area**, returning -1 where the shared one returns the slot.

## 8. Evidence tier

**Measured:** sec 4 (all seven rows re-checked at `file:line`), sec 5 (claim
contents, the one-line `grep`, whitepaper absent), sec 6 (every consumer and
both verbs), sec 7 (script contents, registry absence, the duplicate and I1.1's
note), sec 2's D8.2 file cites, D8.3's body and zero callers.
**Source-evidenced:** sec 3 item 3, D8.2's straddler reading.
**Chat/AI output:** sec 2's choice of seam, sec 3 items 1-2, sec 3's honest
limit.
**Not measured:** nothing is asserted in this ruling that was not either read
from the tree or quoted from a document.

## 9. What would falsify D8

- The AIF-070 whitepaper arriving with a different cut. Doc 1:71 governs.
- A third straddler being found that the persistence/runtime test cannot place.
  Two are named in sec 3; a third would mean the seam is not better than Doc 1's,
  only differently shaped.
- `declare()` being taken by AIF-070 in a form that does not carry the catalog's
  `WS_ID`. Then the consumption seam is somewhere else and D8.3 is wrong.

## 10. First draft, rejected -- recorded rather than quietly replaced

An earlier draft (`AIPR-20260822-COWORK-113`, same id, superseded content) was
sent back by independent review with four blocking findings. The draft is
retained under `docs/maintenance/_to_delete/` pending the steward's disposal.

1. **It took D7**, which is the steward's `SET RECURSION` decision at
   `AIF078_MULTI_WORKSPACE_STAGED_PLAN_V1.md:182` -- in a document whose closing
   section lectured the house about ruling-number collisions. Renumbered to D8.
2. **It claimed six of seven globals had moved.** One had. Sec 4 is the
   correction.
3. **It claimed the relation graph was "assigned to no lane in any document."**
   The lane's own plan assigns it at `:279-281` with *"Own ruling, own work."*
   D8.1 is the correction.
4. **It claimed no persisted relation format existed.** Two do. D8.2 is the
   correction.

**Root cause, and it is the finding worth keeping.** The author reasoned from a
copy of the staged plan held in a project doc store, not from
`docs/maintenance/AIF078_MULTI_WORKSPACE_STAGED_PLAN_V1.md`. The copy predated
D7, stage 7 and the corrected stage 2. **The copy was treated as an authority
when it was a cache.** This is the third instance in one session of the same
shape -- a summary trusted over its source -- and it is exactly what
`AIF120_WORKSPACE_NAME_SHADOWING_REPORT_V1.md:139-140` states: *"Reading a file
by path answers 'what does this file say', never 'is this the file that
loads.'"*

**Standing consequence, proposed:** a ruling may cite a project-doc copy for
narrative, never for a fact about the tree. Facts get read from the tree at
authoring time.

## 11. Good Neighbor note

- **What changed.** This document; two rejected drafts moved to
  `docs/maintenance/_to_delete/` (this session cannot delete on the mount).
  No code, no build, no test.
- **Whose area.** AIF-078's boundary, and an assignment of
  `WorkspaceRelationInfo`'s runtime identity that touches the GUI lane.
  AIF-070's steward (`member.ai.grok.xai`) may object; sec 5 names the standoff
  list to make objecting cheap.
- **What authorization.** The steward, in-session 2026-08-22: *"1 is your so you
  resolve it"*, then *"now that you know better do better."*
- **How to verify.** `sed -n '148,190p' docs/maintenance/AIF078_MULTI_WORKSPACE_STAGED_PLAN_V1.md`;
  `sed -n '306,311p' include/xbase/workspace_membership.hpp`;
  `sed -n '2093,2100p;545,559p' src/gui/core/session.cpp`;
  `sed -n '164,182p' src/cli/workarea_util.cpp`;
  `cat coordination/aif/AIF-070.claim`.
- **How to undo.** Delete this file and restore the two drafts from
  `_to_delete/`. Nothing depends on it.
