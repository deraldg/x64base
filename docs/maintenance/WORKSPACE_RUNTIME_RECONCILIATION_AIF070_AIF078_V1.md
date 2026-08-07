---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260801-003
  recorded_at_utc: 2026-08-01T00:00:00Z
  agent:
    provider: Anthropic
    product: Claude (Cowork)
    model: not_exposed
    access_mode: local_write
  session:
    id: not_exposed
    chat_reference: not_exposed
  project:
    id: project.x64base.runtime
    root: D:/code/ccode
  git:
    branch: development
    baseline_commit: 97068924c
  authorization:
    requested_by: maintainer
    scope: >
      Owner ruling 2026-08-01: the mission is multiple workspaces as a working
      runtime capability with a workspace manager, modelled as GROUPS (named,
      possibly overlapping sets), and AIF-070 is to be RECONCILED BEFORE any
      build. This note is that reconciliation.
  report:
    path: docs/maintenance/WORKSPACE_RUNTIME_RECONCILIATION_AIF070_AIF078_V1.md
    kind: scope_note
---

# Workspace Runtime -- AIF-070 / AIF-078 Reconciliation V1

    status      : review-needed -- reconciliation scope note, NO build authorised by this document
    lanes       : AIF-070 (workspace.virtual_and_memo_resident, member.ai.grok.xai)
                  AIF-078 (workspace-qualifier-namespace-depth, member.ai.claude.cowork)
    owner       : member.derald
    created_utc : 2026-08-01T00:00:00Z

---

## 0. Why this exists

Owner ruling, 2026-08-01, three parts:

1. **The mission is multiple workspaces as a working runtime capability, with a workspace manager.** Not SQLsel.
2. **The structure is GROUPS** -- named sets of workspaces, possibly overlapping -- not a containment hierarchy.
3. **Reconcile AIF-070 before building.**

Ruling 1 **reverses AIF-078's own recommendation.** That lane concluded *"buy the option, not the feature -- multi-workspace addressing as a runtime capability is not yet justified; there is no demand case."* The owner is the demand case. Recorded as a ruling rather than left as a silent contradiction between what the charter recommends and what is being built.

Ruling 2 **supersedes AIF-078 sec 5b.** That section analysed recursion and containment and recommended widening `DataAddress::workspace_` to a path. Groups are a different structure. See sec 4.

---

## 1. Blocker: the AIF-070 design is not in the tree

`docs/maintenance/external_ai_intake/virtual_workspaces_memo_resident_2026-07-28/` contains three files: `MANIFEST.md`, `ASSESSMENT_LOCAL_WORKBENCH.md`, `SUMMARY_FOR_MAINTAINER.md`.

The package's own contents table (`SUMMARY_FOR_MAINTAINER.md:21-28`) lists four more artifacts that **are not present**:

| Declared | State |
|---|---|
| `proposed/labtalk/registries/intake/AIF-055_virtual_workspaces_memo_resident.md` | absent |
| `proposed/labtalk/registries/topics/proposed_ai_work_topics_entry.yaml` | absent |
| `proposed/docs/design/WHITEOBAPER_POINTER_Virtual_Workspaces.md` | absent |
| `Virtual_Workspaces_and_Memo_Resident_Databases_Whitepaper.docx` | **absent -- this is the actual design** |

The local assessment recorded this at intake time ("whitepaper `.docx` not yet delivered locally") and it has not changed since.

**Consequence, stated plainly: a full reconciliation cannot be completed from the tree.** What follows reconciles against the *summarised* design in the MANIFEST, which is real evidence but is an abstract, not a specification. Anything in the whitepaper that contradicts sec 3 below will win, and this note must then be revised.

This is the same shape as the AIF-074 plan-of-record gap (`SQLSEL_PDLC_LANE_V1.md:8` cites a plan absent from the tree) and as AIF-062. **Owed: obtain the whitepaper, or accept that AIF-070's design authority is the MANIFEST abstract and nothing more.**

---

## 2. What AIF-070 actually specifies (source: MANIFEST, evidence tier: design-intended)

- **Concurrent, named workspaces** with first-class ownership of areas, replacing the manual area-partitioning technique the maintainer already uses by hand.
- **Per-area `kind`** carried in an extended DTSHEMA, illustrated as **v4**.
- **Scoped `WORKSPACE SAVE`** by named workspace.
- **New `WORKSPACE OPEN` forms:** `/INTO NEXT n`, `/AREAS`, and a warning on the classic close-all.
- **Memo-resident hydration:** memo bytes -> DTSHEMA (+ data) -> virtual areas / vdisk. The teaching case is a per-student private mini-database living in a memo.

**Hard constraints** (carried from the 2026-07-27/28 maintainer conversation, `SUMMARY_FOR_MAINTAINER.md:15-19`):

1. Memos stay **payload-agnostic** -- no privileged workspace-memo type that limits other payloads.
2. Classic destructive `WORKSPACE OPEN` **remains available**, with a warning, for existing scripts.
3. No collision with the AI-BBS agent-server lane.

**Non-goals:** no rewrite of the `DbArea` or memo store core; no claim of production readiness.

**Risks AIF-070 named, one of which this lane independently measured:**

> "Residual process-global state that has not yet been moved under Workspace ownership"

AIF-078 measured exactly that and can now enumerate it -- see sec 5. Two lanes reaching the same finding independently is the strongest signal in this reconciliation that the seam below is the right one.

**GROUPS DO NOT APPEAR IN AIF-070.** Zero occurrences of group / set-of / collection across all three files. The group model is the maintainer's, introduced 2026-08-01, and is new work owned by AIF-078.

---

## 3. Proposed seam

The two lanes are complementary, not duplicative, and they divide cleanly:

| | AIF-070 | AIF-078 |
|---|---|---|
| Owns | **What a workspace IS** | **How workspaces are ADDRESSED and GROUPED** |
| Scope | named container, first-class area ownership, per-area `kind`, DTSHEMA v4 persistence, scoped SAVE, memo-resident hydration, vdisk | runtime manager, group membership, name resolution and its scope, ambiguity reporting, the qualifier that reaches a workspace |
| Steward | `member.ai.grok.xai` | `member.ai.claude.cowork` |
| Evidence today | design-intended, abstract only (sec 1) | source-evidenced survey + measured cap + one landed type change |

**The single genuine overlap is the runtime registry.** Both lanes need one object that knows which workspaces exist and which areas belong to which. Proposed: **AIF-078 builds it, AIF-070 consumes it.** Rationale is not precedence but readiness -- AIF-078 has the measured survey of what must move (sec 5), and AIF-070's own design is not in the tree to build from.

**Convergent-design note.** Both lanes independently proposed **DTSHEMA v4**: AIF-070 for a per-area `kind`, AIF-078 for a per-area `ws=` owner field. Neither knew of the other. One version bump should carry both fields; two lanes bumping the same format separately is a defect waiting to happen. **Whoever writes the format first writes both fields.**

---

## 4. What the GROUPS ruling changes in AIF-078

Groups are **membership**, not containment. A workspace belongs to zero or more named groups; groups may overlap; the all-workspaces pointer is the universal group. This is a set/graph model, not a tree.

Consequences:

- **sec 5b is superseded as the model.** Its recursion analysis, cycle guard, depth cap, and ancestor-walk question (Q8) all belong to containment. They are not wrong; they are answers to a question no longer being asked. Retained as recorded analysis; **removed from the build path.**
- **Q7's `WorkspacePath` is now over-built, and this should be said rather than quietly kept.** The widening of `DataAddress::workspace_` to a path (landed, proven, `proof.aif078.workspace_path_preserves_depth1`) was justified by nesting. Under groups an address names exactly **one** workspace; membership lives in the manager, not in the address. A path of length <= 1 is a workspace identity with extra ceremony.
  - It is harmless: depth defaults to 1, behavior is proven identical, and the smoke test pins it.
  - It is not free: it is a public type carrying a shape the design no longer implies.
  - **Recommendation: keep it, and re-justify it honestly** -- as headroom for AIF-070's memo-resident case, which *is* structurally nested (a workspace inside a memo inside a row inside a workspace) even though the addressing model is groups. That is a real justification, not a rescue of a sunk cost. **If AIF-070's whitepaper does not need nesting either, revert it.**
- **The group registry is new design**, owned by AIF-078, with no prior art in the tree.

---

## 5. What must move under workspace ownership (measured, AIF-078)

AIF-070 named "residual process-global state" as a risk. Enumerated:

| Global | Location | Under groups |
|---|---|---|
| the single engine | `src/cli/shell.cpp:527` `XBaseEngine eng;` -- only instantiation in the tree | stays one engine; the manager partitions its slots |
| the slot array | `include/xbase.hpp:494` `std::array<unique_ptr<DbArea>, MAX_AREA>`, eagerly constructed at `src/xbase/dbf_file.cpp:409-411` | needs a slot -> workspace owner map |
| work-area facade | `src/cli/workareas.hpp:169` `workareas::global()` | scope-aware or manager-mediated |
| per-area state | `src/cli/table_state.cpp:79-82` `std::array<AreaState, MAX_AREA>` | follows slot ownership |
| **the relation graph** | `src/cli/set_relations.cpp:47-63` -- one `unordered_map` keyed by **bare uppercased parent name**, no owner field | **the sharpest item.** Two workspaces holding `STUDENTS` collide silently on this key |
| name resolution | `src/cli/workarea_util.cpp:29-51` `find_open_area_by_name_ci` -- linear scan, **first match wins, no ambiguity signal** | must gain scope and must report ambiguity |
| last-loaded workspace | `src/cli/cmd_workspace.cpp:172-175` single `static std::string` | per-workspace |

`DbArea` itself carries **no** alias member, **no** slot member and **no** owner back-pointer (`include/xbase.hpp:139-468`), which is why every one of these is a side table today.

---

## 6. Open questions for the owner

- **Q-R1.** Is the AIF-070 whitepaper obtainable? If not, does the MANIFEST abstract become AIF-070's design authority of record? Sec 1 is blocked on this and the block is real.
- **Q-R2.** Accept the sec 3 seam -- AIF-078 builds the registry, AIF-070 consumes it? This is the only genuine overlap.
- **Q-R3.** Does a group have any semantics beyond addressing -- can a group be SAVED, or does it only select? Save-a-group is a persistence feature and belongs with AIF-070's DTSHEMA work, not with addressing.
- **Q-R4.** Can a workspace belong to zero groups (free-floating), or is there always an implicit universal group? Affects whether membership is optional or total.
- **Q-R5.** Keep or revert Q7's `WorkspacePath` (sec 4)? Recommend keep-and-re-justify, revert if AIF-070 needs no nesting.
- **Q-R6.** Who writes DTSHEMA v4, given both lanes need it and one bump should carry both fields?

---

## 7. Evidence tier

**Source-evidenced:** sec 1 (file presence), sec 5 (every row verified at file:line against `D:\code\ccode`).

**Design-intended, and abstract only:** sec 2 -- read from the AIF-070 MANIFEST, whose specification is absent from the tree.

**Chat/AI output:** sec 3, sec 4, sec 6. No code written under this note. **This document authorises no build.**
