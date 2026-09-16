---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260916-COWORK-206
  recorded_at_utc: 2026-09-16T03:10:00Z
  agent:
    provider: Anthropic
    product: Claude (Cowork)
    model: claude-opus-5
    access_mode: local_read_only
  session:
    id: not_exposed
    chat_reference: not_exposed
    run_id: COWORK-20260916-001
  project:
    id: project.x64base.gui
    root: D:/code/ccode/gui
  git:
    branch: development
    baseline_commit: 1817c636c
  authorization:
    requested_by: maintainer (member.derald), in-session 2026-09-16 -- "we were
      working on our appgui, we stopped because we realized we needed to finish
      most of the engine improvements for workspaces, and nested workspaces and
      minidb and nested minidb and memos", then "all of the blockers need
      reevaluation", then "yes" to writing this document.
    scope: >
      Re-measures every blocker the 2026-08-20 closeout carries, against the
      tree at 1817c636c. Supersedes that document as the lane's answer to "what
      is currently false". No code, ruling or fixture was changed to produce
      this; every line is a reading.
  report:
    path: docs/maintenance/SESSION_CLOSEOUT_APPLICATION_UI_DSL_LANE_2026-09-16.md
    kind: session_closeout
---

# Session closeout -- AIF-120 (application-ui-dsl), 2026-09-16

**This supersedes `SESSION_CLOSEOUT_APPLICATION_UI_DSL_LANE_2026-08-20.md` as
the lane's "what is currently false" document.** That one remains the record of
what R70-R83 did. It is no longer a reliable statement of what is blocked.

Status: **review-needed.** Evidence class: **measured**, read-only, at
`1817c636c`. Owner: member.derald. Author: member.ai.claude.cowork.

---

## 0. Why this document exists

The lane seed says, of the authority chain:

> **Read the closeout first.** It is the only one of these that tells you what
> is currently false.

The closeout it points at was written 2026-08-20. Twenty-seven days later, **two
of its blockers are closed, one has improved, and the one it ranks FIRST --
calling it "the oldest open item in the lane by several rulings" -- was closed
four days after it was written.**

Nothing went wrong. Work landed and the document that indexes what is blocked
was not the document that landed it. But the effect is that the lane's own
onboarding instruction routes a new reader to a stale answer, with no
instrument in between.

The 2026-08-20 closeout carries a section titled *"A closeout committed
mid-session is a perishable literal."* It was right, and it under-scoped itself:
a closeout committed at the END of a session is perishable too, just more
slowly.

---

## 1. Re-measurement

| blocker | claimed 2026-08-20 | measured 2026-09-16 | verdict |
|---|---|---|---|
| **MSVC / wx** | "Nothing in R70 through R81 has been built outside gcc 13 / wx 3.2.4 / Linux ... the oldest open item in the lane by several rulings" | `dottalkpp/bin/dottalk_wb.exe` **1,443,840 B, 2026-08-24**; `dottalk_wb_next.exe` 1,426,944 B, 2026-08-23; `build/src/gui/wx/dottalk_wb.vcxproj` 2026-08-23 (Visual Studio 17 2022) | **CLOSED** -- four days after the claim |
| **Gate 7, published lane page** | "still reads 'Planned, not implemented', proposes a `CREATE WINDOW` / `DEFINE BUTTON` command syntax" | page rewritten 2026-09-03: *"Alpha -- chartered and in progress. AIF-120 is no longer a planned lane waiting to start."* The `CREATE WINDOW` row now correctly scopes the TEXT layer as planned | **CLOSED** |
| **R82.4 dtschema asymmetry** | `mcc_x64.dtschema` declares `tag=none` for thirteen areas while `mcc_x32.dtschema` declares real tags | x64: **13** `tag=none`, **0** real, mtime **2026-08-12**. x32: **0** `tag=none`, **12** real, mtime 2026-07-15 | **OPEN, untouched** |
| **Paging** | "`next_page` is called once; the R74 fills also run once and nothing recomputes them when the cursor moves ... the largest piece of unfinished runtime behaviour" | `src/cli/app_smart_browser.cpp:316` calls `next_page` INSIDE a `for(;;)`, so the page does advance. But `schema` (SchemaResolver::resolve) and `sidecar` (SidecarLoader::load_json_sidecar) are resolved ONCE, above the loop | **OPEN** -- and the claim is now line-located: the loop is fine, the fills above it are the defect |
| **R81.1 dashboard unreachable paths** | 24 (23 widows on disk + 1 GITIGNORED) | 268 cited, 250 tracked, **18 not tracked**, of which **1 ignored** -- still `DOCFLUSH-20260722-001/FULLSTACK_DOCUMENTATION_FLUSH_FILE_MANIFEST_V1.csv`, the same R42.1 case | **IMPROVED 24 -> 18, NOT closed** |
| **R70.7 stale citation** | "a stale `R70` citation at `db_tuple_stream.hpp:71` that means R69" | `src/cli/db_tuple_stream.hpp:71` still reads `// PURE 64 (owner ruling, R70).` Note the closeout's path was wrong -- the file is under `src/cli/`, not the repo root | **UNCHANGED** |

---

## 2. Three blockers I could NOT measure, and why

Recorded as unmeasured rather than guessed. Each failed for the same reason,
which is the lane's own first-listed failure mode.

**R82.1 -- the three path printers.** Claimed 13 / 18 / 37 slots against a
50-slot enum. Measured: `cmd_setpath.cpp` `dump()` (line 94) emits **20**
distinct slots; `cmd_init.cpp` names **12**; `path_state.cpp` `describe()`
(line 563) returned **0** to my extractor, which means my brace-matching failed,
not that the printer vanished. Separately `slot_name()` now carries **52** case
labels, so the enum has grown past the 50 the ruling counted. **Every number
moved and none of them is comparable.** The ruling's own counting method is what
this needs.

**BETA citations.** Claimed 26 across nine documents. I found 17 files under a
scope I chose myself (`docs/maintenance/AIF120_*` plus `gui/uidef/`). That is a
different question with a different answer, not a correction.

**Tk crash on `N5_ordinal_spec.DBF`.** Not tested. The `.DBF`/`.FPT` fixtures
are build products, untracked by design, and must be regenerated by
`gui/uidef/author_cases.py` before the crash can be reproduced.

> *"A search shaped by the object you have cannot find an object with a
> different schema ... Every flat grep over-reports. Group by the schema before
> concluding."* -- AIF120 lane seed, failure modes

That is exactly what happened to me three times in this pass. The seed predicted
it a month ago. Recording it here so the count of times this lane has hit it
stays honest.

---

## 3. The engine side the lane was waiting on

The maintainer's recollection was that the lane stopped for engine work on
workspaces, nested workspaces, minidb, nested minidb and memos. The closeout's
"Owed" table supports that when read by ASSIGNEE rather than by item: R70.6/.7/.8,
R73.7, R73.8 and R82.1 route to **engine lane**; R82.4 to **workspace owner**;
R82.2 to **workspace-manager lane**.

What has since landed:

- **WORKDESK**, 2026-09-10. `cli::workdesk::Desk` -- read-only, owns nothing, a
  JOIN of workspaces and areas. Documented in
  `docs/maintenance/WORKSPACE_WORKAREA_WORKDESK_STRUCTURE_MAP_V1.md`, which also
  documents `WorkArea`/`WorkAreaSet` for the first time. This is the "one
  session's whole picture" primitive a generated frontend needs, and it did not
  exist when the lane parked.
- **Nested workspaces, implemented rather than sketched.**
  `include/xbase/workspace_membership.hpp` carries `parent`, `parent_of()`,
  child enumeration, **cycle detection that walks up the parent chain**, and
  depth counting. The governing sentence is quoted in the header: *"Multiple
  workspaces is just a workspace of workspaces of areas."*
- **The memo -> minidb descent is already designed and headered UNDER THIS
  LANE.** `include/gui/core/gui_workspace_format.hpp` declares
  `format_minidb_container_text`, commented *AIF-120*: read-only descent into a
  MINIDB container, *"what is inside a memo field, rendered without hydrating a
  single byte ... clicking a memo costs a parse and nothing else."* The plan is
  `docs/maintenance/AIF120_MINIDB_BROWSER_PLAN_V1.md`.

`APPGUI` is a live verb (`include/dotref.hpp:582`, alias `GUI` at :584),
launching `dottalk_wb` as a separate process or reporting by name why it cannot.

---

## 4. What is actually next

1. **R82.4**, before anything bakes it in. Thirteen areas declared `tag=none` in
   the x64 workspace file against twelve real tags in its x32 twin, unchanged
   since 2026-08-12. The 2026-08-20 closeout already said *"worth deciding
   BEFORE the v3 save bakes it in"* and the v3 save has not happened.
2. **Paging**, now narrowed. The `for(;;)` loop advances correctly; `schema` and
   `sidecar` above it do not. R72's `cursor_hook::set_callback` is the signal,
   and `gui/uidef/wx_host.cpp:91` already installs one.
3. **`WORKSPACE SAVE mcc_x64 V3`** and the section-10 refusal flip -- still one
   cut, still all 22 fixtures at once.
4. **R82.1 and the BETA count**, re-measured by their own rulings' methods.
5. **The R81.1 remainder** -- 18 paths, one of which can never be staged.

---

## 5. What this document does not do

- **It changes nothing.** No code, ruling, fixture or CMake file was touched.
  Every row above is a reading of the tree at `1817c636c`. The envelope declares
  `access_mode: local_read_only`, which is the registered mode for that posture.

  *Correction, recorded rather than quietly fixed:* the first version of this
  document declared `access_mode: read_only_measure`, a value I invented to be
  descriptive. The report audit refused it -- `unregistered access mode` -- and
  the registered set was already written in the tree as
  `local_write | local_read_only | hosted_proposal | external_patch |
  human_operated_tool | automation`. The lane record ALSO already contains an
  earlier agent doing the same thing to the same field: *"The scribe invented
  `access_mode: local` by truncating `local_write`"*, which cost eight documents
  a correction pass. A vocabulary with a checker is not a suggestion, and
  inventing a clearer-sounding value is how the previous one got in.
- **It does not re-approve anything.** The author does not self-approve; this
  ships `review-needed` like every ruling in the lane.
- **It does not close R82.1, BETA or Tk.** Section 2 says why, and an unmeasured
  blocker left open is correct where a guessed number would not be.
- **It does not fix the perishability.** A closeout still goes stale silently.
  Whether that wants a mechanism -- a freshness contract on the newest closeout,
  the way the site tree has one on its pages -- is an owner decision, and it is
  the same shape as the problem `check-site-freshness` exists to solve one
  repository over.
