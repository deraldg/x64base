---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260917-COWORK-002
  recorded_at_utc: 2026-09-17T01:19:13Z
  agent:
    provider: Anthropic
    product: Claude (Cowork)
    model: claude-opus-5
    access_mode: local_write
  session:
    id: not_exposed
    chat_reference: not_exposed
    run_id: COWORK-20260916-001
  project:
    id: project.x64base.gui
    root: D:/code/ccode/gui
  git:
    branch: development
    baseline_commit: 32a1273e9
  authorization:
    requested_by: maintainer (member.derald), in-session 2026-09-16, on being
      shown OI-041's split -- "yes they can ask questions - we will support
      modal", then "dialog is to be desired".
    scope: >
      Rules what happens when the engine needs input and the driver is a GUI.
      Settles OI-041's by-circumstance half outright and states the direction
      for the by-construction half. NO CODE WAS WRITTEN.
  report:
    path: docs/maintenance/AIF120_DIALOG_OVER_REFUSAL_V1.md
    kind: ruling
---

# R147 -- when the engine needs a human, ASK. Refusal is the fallback, not the design.

Lane: AIF-120 (application-ui-dsl). Ruled by: `member.derald`.
Author: `member.ai.claude.cowork`.
Status: **review-needed** -- the author does not self-approve.

---

## 1. The ruling

Owner, 2026-09-16, on OI-041: ***"yes they can ask questions - we will support
modal"***, then ***"dialog is to be desired"***.

**A command that needs input from a person is not a command a GUI must refuse.
It is a command the GUI ANSWERS, by asking. Refusal is what a driver does while
the dialog does not exist yet -- an interim state that must say it is interim,
never a design choice presented as one.**

**AUTHOR'S READING, STATED SO IT CAN BE CORRECTED RATHER THAN INHERITED.** The
second instruction is four words and it arrived directly after this author asked
whether the by-construction half should REFUSE or get a WINDOW. It is read here
as answering that: prefer the dialog in both halves. Section 3 is therefore a
DIRECTION with a named open question, not a settled mechanism, and the
by-circumstance half in section 2 is the part that is fully ruled.

---

## 2. By circumstance: the prompt becomes a host dialog

REBUILD, REINDEX and the shared dirty-buffer confirm ask a question only when a
condition holds -- `cmd_rebuild.cpp:178` `ensure_clean_or_commit()` returns early
three times and reaches its prompt only when `dottalk::table::is_dirty(area0)`.

**These are answered, not refused.** The engine asks; the Workbench renders a
modal; the answer goes back.

**THIS IS R144'S ROUTE, POINTED ONE LAYER DOWN.** R144 (2026-09-16) ruled that a
system picker is a CAPABILITY with `DISPATCH = host` rather than a container, and
that modality is a PROPERTY. A y/N confirm is the smallest host dialog there is.
Nothing new is being invented; an existing route is being pointed at the engine's
own prompts instead of at authored forms.

### 2a. This dissolves an objection this author raised against itself

Earlier the same day this author argued that `interactive_prompt: yes` is
useless as a contract field because REBUILD only prompts when dirty -- a MAY,
not a WILL -- so a bridge refusing everything that declares it would refuse
REBUILD on every clean table.

**That objection was aimed at REFUSAL and does not survive this ruling.** A
driver that ANSWERS never needs to know in advance whether a prompt will come;
it needs to know what to do when one arrives. **A MAY is entirely adequate for
capability negotiation.** The declaration backfill named in OI-041 goes from
*cheap but wrong* to *cheap and correct*, and it becomes an OUTPUT of this
ruling rather than a prerequisite.

---

## 3. By construction: a window, not a modal -- and refusal is INTERIM

SMARTBROWSER, BROWSER and SIMPLEBROWSER are not one question. They are a loop
with state: a page, a command, another page. **A modal per page turn is not the
dialog this ruling desires**; it is a prompt wearing a window.

The direction is a real browser surface -- the Workbench already carries a
Browse tab -- and that is a lane of work rather than a patch.

**UNTIL IT EXISTS, THE BRIDGE STILL FACES ONE OF THESE TODAY**, and OI-041
measured what happens when it does: the pager eats the completion sentinel,
loops, and then eats every command after it until the Workbench is restarted.
So the interim behaviour is refuse-and-name, **labelled in the code and in the
message as interim**, per R22.4 -- an item whose capability is absent must not
render as an ordinary live item -- and R143(b), which requires a KNOWN capability
a target cannot honour to refuse and NAME rather than silently drop.

**NOT RULED: whether the browser window is AIF-120's work or its own lane**, and
whether it is the Browse tab grown up or a new surface.

---

## 4. The mechanism, and the tempting wrong version

**THE ENGINE EMITS A STRUCTURED PROMPT EVENT. THE BRIDGE DOES NOT SCRAPE
STDOUT.**

The cheap version is to watch the stream for `(y/N)` and pop a modal. That is a
hand-maintained pattern sitting beside the thing it describes, which is the
shape this lane keeps retiring -- `collect_set_subcommands()`, the 64-name
literal `cmdhelp.cpp` used to carry, the website manifest's hand-kept totals. It
would also break the first time a prompt is reworded, in a locale that is not
en-US, or in `helpdata_messages.cpp`, which already carries the same text in
it/es/fr/de.

**THE SYMMETRY IS ALREADY THERE AND IS MOST OF THE ARGUMENT.** Measured
2026-09-16 at `32a1273e9`: `src/gui/core/gui_shell_runtime.cpp` parses **exactly
one** structured thing in the stream -- `__DOTTALK_GUI_DONE_<n>__` (`:157`),
which the bridge INJECTS ITSELF via `ECHO` (`:168`) and then waits for (`:180`).
It reads nothing the engine originates. A prompt marker is **the first outbound
event**, using machinery that already exists, running the other direction.

### 4a. It takes the sixty-second timeout with it

`gui_shell_runtime.cpp:179` waits `seconds(60)` for the completion marker, and
today **a wedged pager and a slow honest command are indistinguishable to the
bridge** -- both are silence. A structured prompt gives it a THIRD state,
*waiting on a human*, so the clock stops while a modal is open instead of
expiring into `exit=-1`. The delay symptom in OI-041 is not fixed separately; it
falls out of doing this properly.

---

## 5. What is owed, in order

1. **The prompt event** -- its spelling, and whether it carries the question
   text, a message id, or both. `helpdata_messages.cpp` argues for an id, since
   the GUI should not be rendering en-US strings the engine already localises.
2. **The bridge side** -- recognise it, raise the modal, write the answer back,
   and hold the timeout while it is open.
3. **The declaration backfill** -- five commands, contract-only, now an output
   of section 2a rather than a prerequisite.
4. **`g_suppress_prompts`** -- R131 recorded it is set only on the QUIT path and
   DOTSCRIPT never touches it. **It is not superseded by this ruling.** A GUI
   can raise a dialog; a `.dts` running unattended cannot, and still needs the
   documented default. Two drivers, two answers, one prompt event.
5. **The interim refusal** for section 3, labelled interim.

## 6. Not measured

- **`src/tv`.** Never opened. If it drives the engine through the same shape
  there are THREE drivers with one absence between them, which changes what
  this costs.
- **Whether a modal can be raised from the bridge's worker thread** as it is
  currently structured, or whether the answer has to cross to the UI thread.
- **Whether any prompt in the tree asks something that is not y/N.** Only the
  two parsers in OI-041 were read.

## 7. How to verify

    sed -n '150,200p' src/gui/core/gui_shell_runtime.cpp   # one marker, injected
    sed -n '178,196p' src/cli/cmd_rebuild.cpp              # the prompt is conditional
    sed -n '44,57p'   src/cli/dirty_prompt.cpp             # default No
