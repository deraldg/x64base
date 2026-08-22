---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260822-COWORK-101
  recorded_at_utc: 2026-08-22T00:59:38Z
  agent:
    provider: Anthropic
    product: Claude (Cowork)
    model: claude-opus-5
    access_mode: local_write
  session:
    id: not_exposed
    chat_reference: not_exposed
    run_id: COWORK-20260818-001
  project:
    id: project.x64base.runtime
    root: D:/code/ccode
  git:
    branch: development
    baseline_commit: 8aca9ef1b
  authorization:
    requested_by: maintainer (member.derald), in-session, 2026-08-22 -- "price it,
      i'm willing to pay". This document is the price. It authorises no build.
  report:
    path: docs/maintenance/AIF120_I1_PRICE_V1.md
    kind: scope_note
---

# AIF-120 -- R111: what design I1 costs, measured

Status: **scope note, review-needed. NO BUILD AUTHORISED BY THIS DOCUMENT.**
Owner: member.derald. Author: member.ai.claude.cowork, run `COWORK-20260818-001`.
Date: 2026-08-22. Baseline `8aca9ef1b`.

**I1** (from `docs/maintenance/WORKSPACE_MANAGER_AND_GROUPS_DESIGN_V1.md`): *an
area belongs to exactly one workspace, and `DbArea` carries the workspace handle
and the slot index.* Everything else in AIF-078 queues behind it, because until
an area knows who owns it, ownership has to live in side tables -- and the side
tables are where the collisions are.

The headline: **the wide-header part is cheap and the rewiring is not.** They are
usually quoted as one number. They should not be.

---

## 1. The recompile -- measured, not estimated

From the ninja dependency log, which records the full transitive include set gcc
reported via `-MD`. This is the real recompile set, not a count of `#include`
lines. Parser: `tmp/ninjadeps.py` (scratch).

| build | objects | depend on `include/xbase.hpp` | |
|---|---|---|---|
| `build-wsl-gui-core` (2026-08-21) | 549 | **337** | 61.4% |
| `build-wsl-lean` (2026-08-19) | 505 | **325** | 64.4% |

For contrast, in the same log: `include/reference/data_address.hpp` -- the type
R110 just ruled on -- reaches **2** objects. `src/cli/workareas.hpp` reaches 25.
`xbase.hpp` is in a different class of header from anything else in this lane.

**Per-TU cost.** Seven representative TUs compiled at the build's real flags
(`-O3 -DNDEBUG -std=c++20`), g++ 11.4.0, on the 2-core device VM:

| TU | seconds |
|---|---|
| `src/cli/set_relations.cpp` | 1.98 |
| `src/cli/workareas.cpp` | 3.39 |
| `src/cli/workarea_util.cpp` | 3.68 |
| `src/xbase/dbarea.cpp` | 4.88 |
| `src/xbase/dbf_file.cpp` | 5.44 |
| `src/cli/table_state.cpp` | 7.65 |
| `src/cli/cmd_workspace.cpp` | 9.93 |

Mean 5.28 s, median 4.88 s.

**337 x 5.28 s = ~1780 s = ~30 minutes of single-threaded compile**, plus link.
Divide by your `-j`: at `-j8` about 4 minutes, at `-j16` about 2. That is the
whole mechanical cost, and it is paid **once per edit to the header**, not once.
Budget it per iteration, not per project.

**Not measured:** MSVC per-TU cost, and the Windows build's object count. Only
**3** tracked `.cpp` live under `src/gui/wx/`, so the Windows-only delta in files
is small; the per-file cost on MSVC is unknown and is the one number in this
document I am guessing at, so I am not putting a figure on it.

## 2. The header widening itself -- measured, and it is nearly free

A probe copy of `include/xbase.hpp` with the two members added
(`tmp/i1probe/xbase.hpp`, `std::uint64_t _ws_handle`, `std::int32_t _ws_slot`):

| | before | after |
|---|---|---|
| `sizeof(xbase::DbArea)` | 1088 B | **1104 B** (+16, measured) |

`MAX_AREA` is **512** and `XBaseEngine` eagerly constructs all of them
(`include/xbase.hpp:494`, `src/xbase/dbf_file.cpp:409-411`), so the cost is
**512 x 16 = 8 KB per engine**. There is exactly one engine in the tree
(`src/cli/shell.cpp:527`). Eight kilobytes, once.

And it compiles as-is. Three representative TUs built at `-O3` against the
widened header with **zero call-site changes**:

    src/xbase/dbarea.cpp        compiles clean
    src/cli/table_state.cpp     compiles clean
    src/cli/workarea_util.cpp   compiles clean

**So step 0 is: two lines, 30 minutes of compile, 8 KB, no behaviour change, and
nothing uses the new members.** It buys nothing on its own. It is the enabling
edit, and it is trivially revertible.

## 3. The rewiring -- where the money actually is

Union of live files mentioning any side-table symbol: **49** (52 counting three
AIPortal session artifacts, which are not live code). **37 of the 49 are in
`src/cli`.** In descending sharpness:

| side table | where | reach | why I1 touches it |
|---|---|---|---|
| **the relation graph** | `src/cli/set_relations.cpp:60` -- `unordered_map<string, vector<Relation>>` keyed on the **bare uppercased parent name**, no owner field | map is **file-static** (1 file); header included by **28** | **The sharpest item.** Two workspaces holding `STUDENTS` collide silently. Key must become (workspace, name). |
| **name resolution** | `src/cli/workarea_util.cpp:29-51` `find_open_area_by_name_ci` -- linear scan, **first match wins, no ambiguity signal** | **32** hits in **10** files | Must gain scope, and must be able to *report* ambiguity rather than silently pick. |
| **the work-area facade** | `src/cli/workareas.hpp:169` `global()` -- a function-local static `WorkAreaSet` | **99** hits in **26** files | Largest by hit count, shallowest by difficulty: mostly mechanical re-pointing. |
| **per-area state** | `src/cli/table_state.cpp:79` `std::array<AreaState, MAX_AREA>` | **36** hits in **10** files | Follows slot ownership once slots are owned. |
| **slot access** | `get_area_0based` | **17** hits in **1** file | Contained. |
| **last-loaded workspace** | `src/cli/cmd_workspace.cpp:261-264`, one function-local `static std::string`; 2 use sites (`:1887`, `:3562`) | 3 | Becomes per-workspace. Trivial. |

**The relation graph is the whole risk.** It is also the item with the best
shape: the map is file-static, so the *data structure* change is confined to one
`.cpp`. The exposure is whether the public signatures in `set_relations.hpp`
have to change, which would ripple to 28 includers.

**Live behaviour that must not move:** 208 relations across the corpus, 28 of
them independently-named composite endpoints (AIF-078, `b3c713ae4`), and **10
`.dts` regression scripts** exercise `SET RELATION`. Depth-1 behaviour must be
byte-identical after I1 -- that is the acceptance test, and it exists already.

## 4. Recommended sequence -- four increments, each abandonable

Priced separately because they fail differently. **Each is a separate ruling and
a separate commit.**

| # | what | compile | edit surface | risk |
|---|---|---|---|---|
| **I1.0** | add the two members, populate nowhere | 337 TUs, ~30 min | **2 lines** | none measured -- proven above |
| **I1.1** | populate them at open/close; assert the invariant in a test | 337 TUs | area open path, `schema_close_all`, one test | low -- writes only, nothing reads yet |
| **I1.2** | re-key the relation graph on (workspace, name) | 337 TUs + 28 includers if signatures move | 1 `.cpp` internals, maybe `set_relations.hpp` | **the real risk.** 208 live relations, 10 `.dts` scripts as the oracle |
| **I1.3** | scope name resolution, add an ambiguity signal | 337 TUs | 10 files, 32 sites | medium -- changes what happens on a name collision, which is a **user-visible** behaviour change and needs its own ruling |

I1.0 and I1.1 together are perhaps a session. I1.2 is a session on its own and
should not share a commit with anything. I1.3 changes behaviour a user can see
and wants your ruling before it is written, not after.

**Do not do all four in one pass.** If I1.2 goes wrong, a single commit
containing I1.0-I1.3 cannot be bisected -- and the failure mode is silent (a
relation resolving against the wrong workspace's table), which is precisely the
class of bug the 30-minute rebuild will not surface and the `.dts` scripts will.

## 5. What this does not price

- MSVC/Windows per-TU cost, and therefore the Windows rebuild figure (sec 1).
- Anything in `src/gui/wx/**`: no wxWidgets in either sandbox, so I cannot
  compile it at all, and the first Windows build after I1 will likely want a
  fix. Budget for one.
- The **group registry** itself. I1 is the precondition; groups are separate and
  have no prior art in the tree (reconciliation sec 4).
- Q-R2 -- whether AIF-078 builds the registry and AIF-070 consumes it. Still
  unanswered, and I1 assumes it.

## 6. Evidence tier

**Source-evidenced:** sec 1 (deps logs + timed compiles, re-runnable), sec 2
(measured `sizeof`, real `-O3` compiles), sec 3 (every count from `git grep`
over `src` and `include`; every file:line re-verified at `8aca9ef1b`).

**One correction made in the course of that re-verification:** the reconciliation
doc's sec 5 table cites `cmd_workspace.cpp:172-175` for the last-loaded-workspace
static. At this baseline those lines are a comment about writeback backups; the
static is at `:261-264`. The reconciliation's line number is stale, not wrong in
substance -- the static exists and is a single global. Worth fixing there when
that document is next touched.

**Chat/AI output:** sec 4, sec 5. No production code was written under this note.

## 7. Good Neighbor note

- **What changed.** One new file, `docs/maintenance/AIF120_I1_PRICE_V1.md`. **No
  source file was edited.** The header widening was measured on a *copy* under
  `tmp/i1probe/` (gitignored scratch); `include/xbase.hpp` is untouched.
- **Whose area.** I1 is **AIF-078**'s design (`member.ai.claude.cowork` -- this
  member) and lands in **engine** code (`src/cli/**`, `src/xbase/**`), which is
  not this lane's to change without an explicit go. This note asks for that go;
  it does not assume it.
- **What authorization.** Steward, in session, 2026-08-22: "price it, i'm willing
  to pay". Pricing only. The author does not self-approve; ships `review-needed`.
- **How to verify.** Recompile set:
  `python3 tmp/ninjadeps.py build-wsl-gui-core/.ninja_deps include/xbase.hpp`.
  Per-TU cost: compile any listed TU with the flags in sec 1. `sizeof`: the probe
  header is at `tmp/i1probe/xbase.hpp`, diff it against `include/xbase.hpp` to
  see the exact two lines. Counts: `git grep -c <symbol> -- src include`.
- **How to undo.** Delete this one file. Nothing else was touched.
