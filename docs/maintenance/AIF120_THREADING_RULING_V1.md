---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260818-COWORK-009
  recorded_at_utc: 2026-08-18T15:20:07Z
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
    baseline_commit: 6d52c6d6f
  authorization:
    requested_by: maintainer (member.derald), in-session, "I just created a new AIF for gui work.
      I want to assign this task to this chat session" -> then selected "Threading ruling (gate 9)"
      from an offered next-move list.
    scope: >
      Proof gate 9 of the Application UI DSL lane (AIF-120): the threading ruling.
      Also records a correction to the charter's premise and one tracking defect
      found while measuring. Does NOT restate the charter or the SCX baseline.
  report:
    path: docs/maintenance/AIF120_THREADING_RULING_V1.md
    kind: ruling
---

# AIF-120 -- R11, the threading ruling (proof gate 9)

Status: **ruling, review-needed.** Owner: member.derald.
Author: member.ai.claude.cowork, run `COWORK-20260818-001`. Date: 2026-08-18.
Lane: `application-ui-dsl`. Charter: `docs/maintenance/APPLICATION_UI_DSL_LANE_V1.md`.

The charter names this "the last precondition before syntax work" and says
silence fails. This document takes the position.

---

## 0. The correction that comes first

**The charter's premise for this gate was wrong, and measurement says so.**

The charter states, twice, that nothing has touched threading: *"Nothing in a
form or menu definition speaks to it, and no measurement so far has touched
it."* True of the specimens. **Not true of the tree.**

Measured 2026-08-18 at `6d52c6d6f`:

| what exists | where | size |
| --- | --- | --- |
| A backend-agnostic GUI core with an explicit worker/UI boundary | `src/gui/core/` + `include/gui/core/` | 230,498 bytes, 21 files, all tracked |
| A **written threading and RAII contract** | `docs/ui/GUI_THREADING_RAII_CONTRACT_V1.md` | 141 lines, **untracked** -- see section 4 |
| A working wx frontend built on that core | `src/gui/wx/` | 95,136 bytes, 4 files, all tracked |
| A test that exercises the async boundary | `src/gui/core/gui_test_async_session.cpp` | 10,896 bytes |

`include/gui/core/async_session.hpp` carries a `@dottalk.contract v1` block that
names the rule in one line -- *"UI adapters submit work and consume events;
worker code must not touch toolkit widgets directly"* -- and points at the doc.

The charter missed this because it searched for the objects it had: `DEFINE
WINDOW`, `DEFINE MENU`, and the `foxtalk_*` TV headers. A GUI core that speaks
`submit_*` / `GuiEvent` and never says `DEFINE` anything is invisible to that
query. This is the house trap **"a search shaped by the object you have cannot
find an object with a different schema"** landing on the charter's own author.

**Consequence for this ruling: gate 9 is an ADOPTION, not an invention** -- the
same shape as R8, where the menu DSL already existed as text and the correct move
was to adopt it. The work here is not deciding the rule. It is (a) confirming the
existing rule is the right one for platforms we do not own, and (b) deciding what
of it the **design table** must carry, since the charter's own test is that a
generator can see only the table.

---

## 1. What the existing contract already settles

From `docs/ui/GUI_THREADING_RAII_CONTRACT_V1.md`, confirmed against the code:

- **The UI thread owns every widget.** *"No worker thread may directly touch
  wxWidgets controls, Tkinter widgets, or TUI screen objects. Workers produce
  values; UI threads render values."*
- **One workspace has one mutation lane.** `AsyncSession` holds exactly one
  `std::thread` (`grep -c 'std::thread' src/gui/core/async_session.cpp` -> 1), so
  serialization is structural, not a convention someone has to remember.
- **Results cross the boundary as immutable values**, not handles.
  `GuiEvent` carries nine kinds, every payload a `shared_ptr<const T>`.
- **Work is identified and cancellable.** `TaskId` on every submit; five
  `TaskState` values -- `queued, running, completed, cancelled, failed`;
  `cancel_pending()`; and the contract requires the app tolerate
  out-of-order completion via task ids.
- **Lifetime is RAII.** The destructor stops the queue and joins the worker.
  *"No detached worker thread that can outlive its session or event sink."*

This is exactly the charter's option (a) -- handlers on the UI thread with
explicit hand-off -- already implemented, already documented, already carrying a
completion path. It also matches the common denominator the charter derived
independently for Win32, wx, Qt, Tk and the browser: **the UI has an owning
thread, and work done elsewhere must be marshalled back to it.**

Two independent derivations reaching the same rule is the strongest evidence this
lane has for it.

---

## 2. R11 -- the ruling

**R11. The DSL adopts the existing UI-thread rule, and the design table carries
it as an explicit per-handler dispatch attribute with a defined default. A
handler that does not declare its dispatch is UI-thread; a handler that declares
`worker` must name its completion path. Silence in the table is impossible by
construction, not by convention.**

Four parts. Each is a property of the **table**, per the charter's amendment (b):
*"anything the DSL expresses that the table does not carry is a portability
leak."*

### R11.1 -- The UI-thread rule is the language's rule, not the backend's

Every handler the DSL names (`ON SELECTION BAR`, `ON PAD`, `VALID`, `WHEN`, and
their successors) runs on the platform's UI-owning thread. A generated frontend
may implement that thread however its toolkit does; it may not choose to run a
handler somewhere else.

Portable because every candidate platform in the charter's own table has such a
thread, including the two that have only one.

### R11.2 -- `DISPATCH` is a table column with a non-null default

| value | meaning | what a generator emits |
| --- | --- | --- |
| `ui` (default) | runs to completion on the UI thread; must not block | direct call from the event handler |
| `worker` | runs off the UI thread; must not touch any UI object | the toolkit's own worker mechanism |

The default is `ui`, chosen deliberately: a handler wrongly run on the UI thread
freezes and is discovered in the first minute of use, while a handler wrongly run
off it corrupts widget state intermittently and is discovered much later, on
someone else's platform. **Fail toward the loud failure.** This is R2's lesson
applied to time rather than to space -- R2 refused a silently-assumed coordinate
unit; R11.2 refuses a silently-assumed thread.

### R11.3 -- `worker` requires a named completion handler, and completion is `ui`

A row with `DISPATCH = worker` must carry `ON_COMPLETE` naming a handler that
runs under R11.1. This is what makes the rule implementable on a platform with no
modal loop at all: the browser cannot run `execView`, but every platform in the
table can run *"do this elsewhere, then run that on the UI thread."*

The completion handler receives a task identity and a terminal state. The core
already emits both, so the table field is a description of shipped behaviour:

- identity: `TaskId`
- terminal states: `completed`, `cancelled`, `failed`
- non-terminal: `queued`, `running`

**Completion order is not guaranteed.** The existing contract already requires
tolerating it, so the DSL states it rather than discovering it per backend.

### R11.4 -- Mutating work is serialized per workspace; lifetime is by container

Two portability rules that are cheap here and expensive later:

- **Serialization.** Commands that move the record pointer or change area,
  order, filter, relation, lock or buffer state are serialized against one
  workspace. Concurrency in a generated frontend is concurrency against a DBF
  cursor. The house rule *"a write may be buffered; navigation discards it"*
  becomes a data-loss bug the moment two handlers navigate at once.
- **Lifetime.** Closing or destroying a container cancels the pending work its
  handlers submitted. Nothing queued may outlive the window that queued it.
  This rides on the ownership rule the charter already keeps as free portability,
  and is the portable half of the core's RAII join.

---

## 3. What R11 deliberately does NOT do

- **It does not add async vocabulary to the command surface.** Measured: `SYSCMD`
  carries 212 rows and **zero** concurrency commands -- the only match against
  `THREAD|ASYNC|BACKGROUND|WAIT|SLEEP|TIMER|QUEUE|POST|SPAWN|NOWAIT|YIELD|IDLE`
  is `STOP_ON_ERROR`, which is error handling. R11 is a property of a handler
  row in a design table, not a new statement a script author writes. Adding
  `DISPATCH` costs one column; adding a threading statement to the language
  would cost a concurrency model DotTalk++ does not have.
- **It does not touch `.SCX` or `.MNX`.** Neither format has a dispatch concept,
  so an importer supplies the default under R11.2 and records that it did --
  the same discipline R2 requires for an absent scale mode.
- **It does not settle the coordinate fork (gate 8).** Independent axis.
- **It does not rule on `SKIP FOR` expression evaluation** (R9's open edge).
  Those expressions run wherever their handler runs, which R11.1 makes
  well-defined, but what a portable target does with host-language expressions
  is R9's problem, not this one.

---

## 4. Defect found while measuring -- `docs/ui/` is untracked

Not part of the ruling. Recorded because it was found on the way and it is the
exact failure mode the house names.

```
git --no-optional-locks ls-files docs/ui   ->  0 files
git --no-optional-locks check-ignore docs/ui/*.md  ->  not ignored (all four)
```

Four active architecture documents are present in the working tree and in no
commit:

- `docs/ui/GUI_THREADING_RAII_CONTRACT_V1.md`
- `docs/ui/CORE_UI_PRINCIPLES_V1.md`
- `docs/ui/UI_LANE_TRADEOFFS_V1.md`
- `docs/ui/TUI_ALIGNMENT_PLAN_V1.md`

`include/gui/core/async_session.hpp` **is** tracked, and its contract block cites
`docs: docs/ui/GUI_THREADING_RAII_CONTRACT_V1.md`. A tracked file pointing at an
untracked one is a **widow** by the house definition. Anyone cloning this repo
gets the GUI core and none of the rules governing it -- and this ruling would
inherit the same widow, since it cites those documents as its evidence.

**Context, so this is not read as a bigger claim than it is.** Untracked
documents are not unique to `docs/ui`: 36 of the 335 `.md` files directly under
`docs/maintenance` are also untracked, including this lane's own
`AIF120_LANE_STATUS_AND_FIXTURES_V1.md` and `AIF120_VFP_SCX_EMPIRICAL_BASELINE_V1.md`.
Nothing under `docs/` is `.gitignore`d for these paths -- it is a staging
backlog, not a policy. What makes `docs/ui` the one worth naming here is the
ratio and the citation: four of four untracked, and one of them named by path
inside tracked source. That combination is what turns a backlog item into a
widow.

They are the maintainer's files, not this lane's, so this is a report and not an
action. Recommended commands in section 6.

---

## 5. Proof and disproof

**Evidence tier: source-evidenced.** Every claim above is read from files at
`6d52c6d6f`. Nothing here is runtime-proven; the engine was not built or run in
this session, per house rule 3.

R11 is refuted by any of:

1. a candidate platform with no UI-owning thread (would break R11.1);
2. a designer format that carries a real dispatch concept R11.2 cannot express;
3. a `worker` handler that cannot reach the UI thread on some target -- the
   charter's browser column is the one to check first;
4. a workspace where R11.4's serialization measurably costs more than the cursor
   corruption it prevents.

The cheapest live check is gate 11's second backend: implement `DISPATCH` on Tk,
whose threading rule (*"not thread-safe at all"*, `after()` onto the main loop)
is the least like wx of any target already in the tree.

---

## 6. Handoff to the maintainer -- PowerShell, run in `D:\code\ccode`

Explicit paths only; no `git add -A`. Review before staging -- the author does
not self-approve.

```powershell
# 1. This ruling, plus the charter and status edits it comes with.
git add docs/maintenance/AIF120_THREADING_RULING_V1.md
git add docs/maintenance/APPLICATION_UI_DSL_LANE_V1.md
git add docs/maintenance/AIF120_LANE_STATUS_AND_FIXTURES_V1.md
git status --short -uall
git commit -m "AIF-120: R11 threading ruling (gate 9), adopted from the shipped GUI core contract"
```

```powershell
# 2. SEPARATE commit -- the widow in section 4. Maintainer's files, maintainer's call.
git add docs/ui/GUI_THREADING_RAII_CONTRACT_V1.md docs/ui/CORE_UI_PRINCIPLES_V1.md
git add docs/ui/UI_LANE_TRADEOFFS_V1.md docs/ui/TUI_ALIGNMENT_PLAN_V1.md
git status --short -uall
git commit -m "docs/ui: track the four active UI architecture documents (widow fix)"
```
