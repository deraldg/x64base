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
**AIF: NOT YET CLAIMED.** Claim with

```text
python tools/coordination/session_coordinator.py claim-aif --member member.ai.claude.cowork --run COWORK-20260817-001 --lane application-ui-dsl
```

(One line. PowerShell continuation is a backtick, not `^`; the caret form fails
with "not recognized as a name of a cmdlet" and leaves the claim unmade.)

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
8. **A coordinate-model ruling, recorded before syntax is fixed** (see above)
9. **A second backend spiked, not shipped** -- enough of one non-TUI target to
   prove the vocabulary is not secretly Turbo Vision in disguise. Without this,
   gate 3 passing means nothing about portability.

## Housekeeping this lane inherits

- The public README says the lane is "tracked here" and points at the seed page.
  Until the claim exists that sentence points at nothing; it should read
  "described here", or be updated once the number is claimed.
- `edu_eco` is in the identical state -- an idea, published-adjacent, not
  chartered. Worth ruling on both at once.
