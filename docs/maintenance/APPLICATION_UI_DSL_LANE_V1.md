---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260817-COWORK-006
  recorded_at_utc: 2026-08-18T01:10:00Z
  agent:
    provider: Anthropic
    product: Claude (Cowork)
    model: claude-opus-5
    access_mode: local_write
  session:
    id: not_exposed
    chat_reference: not_exposed
  project:
    id: project.x64base.runtime
    root: D:/code/ccode
  git:
    branch: development
    baseline_commit: a5105491f
  authorization:
    requested_by: maintainer (member.derald), in-session, "the old foxpro window menu syntax might be a good candidate for a common gui interface ... then we need a lane and an aif"
    scope: >
      Charters the Application UI DSL as a real lane, replacing a published page
      that called itself a lane while having no claim, charter or intake row.
      Proposes FoxPro window/menu syntax as the source vocabulary and maps it
      against Turbo Vision and the Win32 app frame.
  report:
    path: docs/maintenance/APPLICATION_UI_DSL_LANE_V1.md
    kind: lane_charter
---

# Application UI DSL -- lane charter

**Status:** charter, review-needed. Owner: member.derald.
Steward: member.ai.claude.cowork. Date: 2026-08-17.
**AIF-120**, claimed 2026-08-18T03:15:29Z, run `COWORK-20260817-001`,
member `member.ai.claude.cowork`, lane `application-ui-dsl`.
Claim: `coordination/aif/AIF-120.claim`.

then record the number here, add the intake row, and delete this block.
Published seed: `x64base.com/docs/dev/application-ui-dsl-lane/`
(`content/docs/dev/application-ui-dsl-lane.mdx` in the site repo).

## Why this is a lane now

A page has been published calling this a lane for some time. Measured
2026-08-17: **zero** intake rows, **zero** charters, **no** claim file. The
public README says "The planned Application UI DSL lane is tracked here", and
nothing was tracking it. In this project "lane" means a claimed number, a
charter, an intake row and coordination; the word was doing work it had not
earned. This charter closes that gap.

## What already exists, and it is more than the page suggests

The published seed reads as though this starts from nothing. It does not.

- **FoxTalk is a working Turbo Vision application layer**, fourteen headers:
  `include/tv/foxtalk_app`, `_menu`, `_layout`, `_status`, `_message_line`,
  `_command_window`, `_output_window`, `_log_view`, `_cmd_input`, `_ids`,
  `_pro_menu_ids`, `_redirect`, `_shell_bridge`, `_util`, plus
  `include/palette/foxtalk_palette.hpp`.
- **`include/foxref.hpp` is a 553-line FoxPro reference catalogue**, already
  crosswalking FoxPro vocabulary to DotTalk commands.
- `include/foxpro_go.hpp`, `include/foxpro_header.hpp`, and a `fox_palette`
  build target exist.
- Targets named by the seed already exist or are chartered: Arctic TUI, the
  wxWidgets lane, the web surfaces.

**And the language does not exist at all.** `DEFINE WINDOW`, `DEFINE MENU`,
`DEFINE POPUP`, `DEFINE BAR` and `ON SELECTION` appear NOWHERE in `src/`,
`include/` or `docs/`. `include/tv/foxtalk_menu.hpp` exposes exactly one
function -- `TMenuBar* buildMenuBar(TRect bounds)` -- so menus are hardcoded C++.

**So the lane is not "build a GUI". It is "give the GUI that exists a
language."** That is a much smaller and much better-defined problem, and it is
the single most important correction this charter makes to the published page.

## Why FoxPro syntax is the right source vocabulary

Not nostalgia. Three structural reasons:

1. **It is name-based, not handle-based.** `DEFINE WINDOW cust ...` then
   `ACTIVATE WINDOW cust`. The script never holds an object, a pointer or a
   handle, so nothing about the target's object model leaks into the language.
   Turbo Vision would leak an ownership tree; Win32 would leak `HWND`s; wx would
   leak sizers. FoxPro leaks nothing.
2. **It is statement-oriented and flat**, which is what DotScript already is. No
   new evaluation model, no nesting rules, no lifetime semantics to invent.
3. **It is already half-catalogued here** in `foxref.hpp`, and the TUI it would
   drive is already dressed as FoxPro.

## The mapping matrix

Design analysis, not measurement: the Turbo Vision and Win32 columns are from
the general shape of those APIs and must be checked against the actual TV
version vendored here before any of it is committed to.

| FoxPro source form | Turbo Vision | Win32 app frame |
| --- | --- | --- |
| `DEFINE WINDOW n FROM r,c TO r,c TITLE t` | `TWindow(TRect, title, num)` | `CreateWindowEx` |
| `ACTIVATE WINDOW n` | `deskTop->insert` / `execView` (modal) | `ShowWindow` / `DialogBox` |
| `DEACTIVATE` / `HIDE WINDOW n` | `hide()` / `destroy` | `ShowWindow(SW_HIDE)` / `DestroyWindow` |
| `MOVE` / `SIZE` / `ZOOM WINDOW` | `locate()` / `zoom()` | `SetWindowPos` |
| `DEFINE MENU BAR` | `TMenuBar` | `HMENU` + `SetMenu` |
| `DEFINE PAD p OF bar PROMPT t` | `TSubMenu` | `AppendMenu(MF_POPUP)` |
| `DEFINE POPUP p` | `TMenuBox` / `TSubMenu` | `CreatePopupMenu` |
| `DEFINE BAR n OF p PROMPT t` | `TMenuItem(prompt, cmd, key)` | `AppendMenu(id)` |
| `ON SELECTION BAR/PAD DO proc` | `evCommand` + `cmXxx` in `handleEvent` | `WM_COMMAND` id dispatch |
| `@ r,c SAY text` | `TStaticText` / `TLabel` | `STATIC` control |
| `@ r,c GET var` | `TInputLine` | `EDIT` control |
| `... VALID expr` | `TValidator` | validation on `EN_KILLFOCUS` |
| `... WHEN expr` | view enable/disable | `EnableWindow` |
| `DEFINE BUTTON` / `GET ... FUNCTION '*'` | `TButton` | `BUTTON` control |
| `READ` / `READ CYCLE` | `execView` modal loop | `DialogBox` modal loop |
| `BROWSE` | `TListViewer` and friends | `SysListView32` |

The correspondence is close enough on all three columns that a single source
form is realistic. **The disagreements are the lane, and there are three.**

## AMENDMENT 2026-08-18: the target is platforms we do NOT own

Maintainer correction, and it changes what "good" means for this lane:

> "We want to make room for and accommodate OTHER gui platforms -- not our own.
> As long as you have a good basis, AI can easily handle new frontends."

So the success test is NOT "it works on FoxTalk". It is: **could someone
implement this vocabulary on a platform nobody here has seen, working from the
specification alone?** That reframes Turbo Vision from "the backend" to "one
implementer, and the least representative of the set".

**Turbo Vision is the wrong thing to design against.** It is a character-cell,
single-threaded, cooperative, synchronous event loop. Real GUIs differ from it
in ways that are invisible until a second backend exists, which is exactly when
a vocabulary is most expensive to change.

**What every candidate platform genuinely shares** -- Turbo Vision, Win32, wx,
Qt, Tk, and the browser -- is a short list, and it is the real basis:

- a top-level window or frame, with a title and a close
- a menu bar carrying popups and items, with accelerators
- dialogs, modal and modeless
- controls: label, text input, button, checkbox, radio group, list, scrollbar
- keyboard focus with an order, and mouse input
- some command or event dispatch from a control back to script
- ownership: destroying a container destroys its children

That list is portable. Everything below is where the platforms stop agreeing.

### The axis Turbo Vision cannot teach: threading

This was missing from the charter entirely and it is the most likely thing to
sink a vocabulary designed TUI-first.

| platform | UI thread rule | marshal from another thread |
| --- | --- | --- |
| Turbo Vision | single-threaded, no rule needed | n/a |
| Win32 | window handles have thread affinity | `PostMessage` |
| wxWidgets | GUI calls on the main thread | `CallAfter` / `wxQueueEvent` |
| Qt | widgets on the GUI thread | queued signal/slot connections |
| Tk | not thread-safe at all | `after()` onto the main loop |
| browser | single JS thread | workers + `postMessage` |

**The common denominator is not "no threads". It is: the UI has an owning
thread, and work done anywhere else must be marshalled back to it.** Every real
platform states this; only Turbo Vision is silent, because it has no other
thread to be wrong about.

So the DSL must take a position. Either (a) handlers are declared to run on the
UI thread and anything slow must be handed off explicitly, or (b) there is a
background/async construct with a defined completion path. **Saying nothing is
the one unacceptable answer**, because each backend will then invent its own,
and a script stops being portable the first time it does something slow.

### Other places Turbo Vision would mislead

- **Modality.** TV `execView` and Win32 `DialogBox` are nested loops; the
  browser has no modal loop at all, only callbacks. `READ` is not universal.
- **Layout and resize.** TV is fixed character cells with no reflow. Real GUIs
  resize, scale for DPI, and lay out by font metrics. TV cannot teach any of it.
- **Ownership** is the one that generalises cleanly: parent destroys child holds
  on TV, Win32, Qt and Tk alike. Keep it; it is free portability.

### What this changes in this charter

1. Turbo Vision is demoted from "the proven backend" to "the first implementer".
2. **A real GUI must inform the design, not validate it afterwards.** wx and Tk
   both already have launchers and proof runs in this repository
   (`labtalk/aops/run-wx.ps1`, `tk.run.ps1`, and runs under
   `labtalk/proofs/runs/`), so a second reference costs discovery, not
   construction.
3. Threading becomes a required ruling alongside coordinates.
4. The specification must be written so an implementer with none of this code
   can build a frontend from it. If the spec only makes sense while reading
   `foxtalk_*`, the lane has failed its own test.

## AMENDMENT 2026-08-18 (b): the DSL is also an INTERCHANGE FORMAT

Maintainer, same session:

> "But supporting the foxpro 2.6a graphics language we can also export the
> graphic requirements to external gui generators."

This is the strongest argument in the lane and it deserves to be the frame.

**FoxPro 2.6a did not hand-write screens. It generated them.** Its design tools
produced files that a generator then turned into procedural code:

| designer | design file | generated |
| --- | --- | --- |
| Screen Builder | `.SCX` / `.SCT` | `.SPR` screen program |
| Menu Builder | `.MNX` / `.MNT` | `.MPR` menu program |
| Report Writer | `.FRX` / `.FRT` | `.FRG` |
| Project Manager | `.PJX` / `.PJT` | -- |

**And those design files are DBF tables.** `.SCX`, `.MNX` and `.FRX` are
DBF-format files with a memo sidecar; in FoxPro you could `USE` a `.SCX` and
browse the screen definition as rows. (Recalled, not measured -- the project
references none of `SCX/MNX/FRX/SPR/MPR` anywhere today, so this is prior art
from outside the tree and should be verified against a real 2.6a artifact before
it is built on.)

That matters here more than it would anywhere else: **this project is a DBF
engine.** A UI definition stored as a DBF table with a memo sidecar is not an
odd choice, it is the native one -- readable by `USE`, browsable by `BROWSE`,
indexable, diffable through the same tooling as every other table, and carried
by the same memo and workspace machinery already built.

So the architecture is three layers, not one:

```text
DSL text            what a human writes        DEFINE WINDOW / DEFINE MENU
   |
   v
design table        the interchange format     a DBF + memo, SCX-shaped
   |
   +--> runtime interpreter   (FoxTalk/TV reads the table directly)
   +--> generator -> Win32
   +--> generator -> wx / Qt / Tk
   +--> generator -> web
```

**The generators are consumers of a table, not of the parser.** That is what
"export the graphic requirements to external GUI generators" buys, and it
resolves the portability worry above by construction: a new frontend never needs
the DSL, the parser, or any of this C++ -- it needs to read one documented
table. Which is also precisely the artifact you would hand an AI and say "write
me a Qt frontend for this."

It also gives the lane a much better v1 boundary. **The table schema is the
deliverable.** A text DSL that only ever fed FoxTalk would be a private
convenience; a documented design table with one interpreter and one generator is
a contract other people can build against.

Consequences for the gates below: the coordinate ruling and the threading ruling
are properties of the TABLE, not of the syntax, and must be decided there.
Anything a generator cannot see in the table cannot be generated, so anything
the DSL expresses that the table does not carry is a portability leak.

## The three real problems

**1. Coordinates. This is the fork that decides everything else.**
`@ row, col` is character-cell geometry. Turbo Vision is also character-cell, so
FoxPro maps onto it almost perfectly -- which is exactly the trap, because the
easiest target will make the language TUI-shaped and every GUI target after it
will fight the coordinate model. Three options, and one must be chosen BEFORE
any syntax is fixed:

  - keep cells and scale for GUI targets (cheapest, permanently TUI-flavoured)
  - abstract units with cells as one backend (portable, more design up front)
  - declare layout intent rather than position, with cells derived (most
    portable, furthest from FoxPro, and the most work)

**2. `READ` is a modal cycle over pending `GET`s.** It maps naturally to
`execView` and to `DialogBox`, and it does not map to a web surface or to any
event-driven frame without inventing something. Either the DSL is modal-only in
v1 and says so, or `READ` becomes sugar over an explicit event model.

**3. FoxPro has no layout manager.** Absolute placement is fine for TUI and
acceptable for Win32; wx and web both expect layout. This is the same fork as
(1) seen from the other end, which is why (1) is a precondition and not a detail.

## Scope

**In scope:** the DSL surface, its parser, its command registry entries, and one
proven backend (Turbo Vision via the existing FoxTalk layer). The vocabulary
crosswalk against `foxref.hpp`.

**Not in scope:** building new GUI surfaces. wxWidgets, Arctic and web are
existing or separately chartered lanes and this one emits INTO them. If the lane
starts building widgets it has crossed its boundary.

**Stopping rule, on the AIF-119 model:** if a construct cannot be expressed
without exposing the target's object model to the script, it does not belong in
v1. The whole argument for FoxPro syntax is that it hides that model.

## Proof gates

Adopted from the published seed, which had already written them, plus two:

1. Syntax contract and examples
2. Command registry entries
3. TUI proof for menu, window, dialog, button, and event handler
4. HELP/CMDHELP coverage
5. SelfDoc metadata coverage
6. Manualgen section
7. Website comparison update
8. **A coordinate-model ruling, recorded before the table schema is fixed**
9. **A threading ruling** -- handlers on the UI thread with explicit hand-off,
   or a background construct with a defined completion path. Silence fails.
10. **The design table documented as a standalone contract** -- schema, fields,
    memo layout -- readable by someone with none of this source. This is the
    deliverable; the DSL text is a convenience over it.
11. **A second backend spiked from the TABLE, not the parser** -- enough of wx
    or Tk to prove a generator needs nothing but the documented schema. Both
    already have launchers and proof runs here, so this is discovery rather
    than construction. Without it, gate 3 passing says nothing about
    portability.

## The retro piece

Maintainer's note, and it is a real deliverable rather than a garnish: the
FoxPro 2.6a design-file story is **good retro content**, and `/retro` already
exists as a site surface.

The angle writes itself and is true: in 1994 a screen designer stored its work
as a database table, because the tool was built by database people who reached
for the thing they had. Thirty years later a DBF engine wants a portable UI
description, and the same answer is still the right one -- for the same reason.
`.SCX` was a `.DBF`. You could `USE` your user interface.

It doubles as recruitment for the lane: the piece explains the architecture to a
reader who would never open a charter, and the artifact it describes is the one
we want other people generating frontends from.

## Housekeeping this lane inherits

- The public README says the lane is "tracked here" and points at the seed page.
  Until the claim exists that sentence points at nothing; it should read
  "described here", or be updated once the number is claimed.
- `edu_eco` is in the identical state -- an idea, published-adjacent, not
  chartered. Worth ruling on both at once.
