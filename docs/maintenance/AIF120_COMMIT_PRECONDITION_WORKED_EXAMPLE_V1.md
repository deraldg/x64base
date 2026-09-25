---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260917-COWORK-004
  recorded_at_utc: 2026-09-17T01:54:54Z
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
    baseline_commit: 08fa0234c
  authorization:
    requested_by: maintainer (member.derald), in-session 2026-09-16 -- on the
      ASK/REPLY question: "control flow", then "our standard is gold", then
      "commit is the perfect example for all three gui/tui types".
    scope: >
      Scopes R147's mechanism to ONE precondition proven across THREE drivers,
      and supersedes the author's own AIF120_PROMPT_EVENT_DESIGN_V1 on where the
      asking belongs. A PROPOSAL. NO CODE WAS WRITTEN.
  report:
    path: docs/maintenance/AIF120_COMMIT_PRECONDITION_WORKED_EXAMPLE_V1.md
    kind: design
---

# COMMIT as the worked example -- the prompt is a precondition in the wrong place, and the dialog's buttons are verbs that already exist

Lane: AIF-120 (application-ui-dsl). Owner: `member.derald`.
Author: `member.ai.claude.cowork`. Status: **review-needed**.
Scopes R147. Proposed 2026-09-17; **three of its four open questions were RULED
2026-09-25 and the fourth was deliberately deferred -- see section 0-R, placed
first because a reader must not act on sections 3 and 3b without it.**

---

## 0-R. RULINGS, 2026-09-25 (owner `member.derald`)

**(1) TWO KINDS, NOT THREE.** The ASK is `choice` (fixed, R145 `Style = 2`) or
`entry` (editable, `Style = 0`). A confirm is a CHOICE OVER TWO TOKENS, not a
third kind -- R145 already supplies the only distinction that carries weight, and
a separate `confirm` would invent a category the vocabulary does not need. This
retires the author's own earlier three-kind proposal.

**(2) FOUR BUTTONS ON THE DIRTY PRECONDITION, not three:** `COMMIT`,
`ROLLBACK`, `PROCEED`, `CANCEL`. The fourth is the one section 3's table missed:
**PROCEED WITHOUT COMMITTING, leaving the buffer dirty**, which is a DIFFERENT
END STATE from ROLLBACK's discard. It is not a new semantic --
`dirty_prompt.cpp:124` takes exactly this path when `g_suppress_prompts` is set,
so the engine already implements it and only the unattended caller can reach it.
**THE UNATTENDED DEFAULT IS THEREFORE `PROCEED` AND UNATTENDED BEHAVIOUR DOES
NOT CHANGE** -- the dialog exposes an outcome the engine has, rather than adding
one.

**(3) THE CONSOLE GOES THROUGH THE PROTOCOL TOO.** Owner: *"as much as possible
code is unified."* No console fast path. A driver returns a TOKEN, so keystroke
parsing exists in exactly ONE place -- a single console renderer mapping keys to
tokens -- replacing the three implementations measured in OI-041
(`dirty_prompt.cpp:43`, `cmd_rebuild.cpp:136`, `cmd_reindex.cpp:166`), which
today disagree: `yellow` consents to an index rebuild, and a leading space
consents to a commit.

**(4) TRANSPORT IS DEFERRED, DELIBERATELY AND ON THE RECORD.** Whether the ASK
crosses as a reserved line on stdout or on a separate channel is NOT decided.
It can wait: the kinds, the payload fields, the four tokens and the single parser
are all transport-independent, and the wire format is an adapter behind them.
**THE HAZARD IS THAT A DEFERRED DECISION GETS MADE BY ACCIDENT** -- by whoever
writes the first line of code -- and is then read back as ruled. So it is
recorded here as OPEN, and the first implementation must name the transport it
chose as PROVISIONAL, in the code and in its commit message, until this is ruled.

---

## 1. Why gold does not cost platinum here, and it is one measurement

**EVERY ONE OF THE NINE PROMPT SITES IS A GUARD.** Measured at `08fa0234c`:
argument parsing, then the prompt, then the work.

| site | position |
|---|---|
| `shell_commands.cpp:108,117` (`USE`, `CLOSE`) | first statement in the lambda |
| `cmd_close.cpp:243,249,259` | before any close |
| `cmd_workspace.cpp:6055,6191,6407` | immediately before the open, bare `return` behind |
| `shell.cpp:716` (`QUIT`) | guards the `break` |
| `cmd_rebuild.cpp:222` | after parsing, before the rebuild |
| `cmd_reindex.cpp:435` | same shape |

**NOT ONE ASKS AFTER DOING WORK.** That is the entire cost question. A prompt
raised mid-write would need continuations -- resumable commands, saved state,
the platinum bill. None of these has anything to resume, because none of them
has started.

---

## 2. So the prompt is a PRECONDITION, and it is in the wrong place

Nine command bodies each carry an imperative `maybe_prompt_*` call because there
was nowhere declarative to put a precondition. **That is why they are all
guards: they are preconditions wearing procedure.**

The gold shape says so out loud:

- the command **DECLARES** what it requires -- a clean buffer;
- the **DISPATCHER** checks preconditions before dispatch, and owns the asking;
- `ASK` / `REPLY` operate at **SHELL LEVEL**, where the command stream is already
  owned by the command reader.

**Nothing reads stdin mid-command, because no command is running yet.** That is
the difference between framing the defect and deleting it: no stolen line, no
eaten sentinel, no wedged pager, no sixty-second timeout. Not fixed -- absent.

And the driver-specific behaviour collapses from **nine scattered decisions into
one place that already knows which driver it is.**

### 2a. This corrects the author's own prior design

`AIF120_PROMPT_EVENT_DESIGN_V1.md` put `ask()` in the engine as a hook the
drivers install into. **That is backwards.** The shell owns asking; the engine
owns declaring. The engine never learns what a console is -- which was the
expensive-sounding half of R147's option (3), and it turns out not to be
required at all.

---

## 3. THE DIALOG'S BUTTONS ARE VERBS THAT ALREADY EXIST, AND THE BINARY PROMPT CANNOT REACH ONE OF THEM

Measured at `08fa0234c`:

| button | verb | status |
|---|---|---|
| Commit | `COMMIT` | registered (`dotref.hpp:207`), and **already invoked from inside the prompt** (`dirty_prompt.cpp:78`) |
| Discard | `ROLLBACK` | registered (`dotref.hpp:1130`) -- and **`dirty_prompt.cpp` mentions it ZERO times** |
| Proceed | (none) | **ADDED BY RULING (2), 2026-09-25.** Proceed WITHOUT committing; the buffer stays dirty. `dirty_prompt.cpp:124` already returns exactly this outcome under `g_suppress_prompts`, so it is the engine's own third answer and today only an unattended caller can choose it |
| Cancel | (none) | drop the pending intent |

**`parse_yes_default_no()` gives commit-or-cancel. There is no way to say
discard.** A user carrying changes they do not want has no answer to the
question: they must cancel, type `ROLLBACK`, and then retype the command they
originally wanted. **The verb exists. The prompt cannot reach it.**

**SO COMMIT IS NOT MERELY A GOOD TEST CASE. IT IS THE CASE WHERE A DIALOG
EXPRESSES SOMETHING THE CONSOLE PROMPT STRUCTURALLY CANNOT**, and that is a
stronger argument for R147's *"dialog is to be desired"* than convenience: the
y/N prompt is **LOSSY relative to the engine's own vocabulary.**

### 3a. Therefore REPLY carries a TOKEN, and for COMMIT that token is a VERB

    REPLY <id> COMMIT     run COMMIT, then re-dispatch the pending command
    REPLY <id> ROLLBACK   discard the buffered changes, then re-dispatch
    REPLY <id> PROCEED    re-dispatch WITHOUT committing; the buffer stays dirty
    REPLY <id> CANCEL     drop the pending command

**THE `<id>` IS NOT DECORATION.** It correlates the reply to the ask, so a late
or duplicated answer cannot resolve a question it was not asked. The machinery
for this already exists in the other direction: `gui_shell_runtime.cpp:157`
numbers its completion marker `__DOTTALK_GUI_DONE_<n>__` for the same reason.

**For this precondition, REPLY introduces no new semantics: it is a SEQUENCER
over commands that already exist.** The pending intent is one slot holding a
command line, and re-dispatching a line is the one thing a shell is already good
at.

### 3b. BUT A PROMPT IS NOT ALWAYS A CHOICE. IT MAY REQUEST AN ENTRY -- and this lane ruled that distinction three days ago

Owner, raising it against this design: *"a prompt might be more than binary, it
may request an entry"*. Correct, and the vocabulary for it already exists rather
than needing inventing.

**R145 (2026-09-16) ruled exactly this distinction one layer up:** a FIXED set
is not an EDITABLE one, it is a PROPERTY, and it is adopted from VFP's
ComboBox `Style` rather than invented. A prompt is a form with one field, and
the question *"choice or entry"* is that field's `Style`:

| answer kind | R145 spelling | what the dialog renders | what REPLY carries |
|---|---|---|---|
| choice among N | fixed (`Style = 2`) | buttons or a fixed list | one of the offered tokens -- for COMMIT, a VERB |
| free entry | editable (`Style = 0`) | a text field | a VALUE |

And **R144 supplies the rest of the frame**: modality is a PROPERTY, a host
dialog is a CAPABILITY with `DISPATCH = host`. So an ASK is a modal one-field
form whose field is fixed or editable. **Nothing new enters the vocabulary.**

**THE GRAMMAR MUST NOT PRECLUDE IT, AND THAT COSTS NOTHING TODAY.** `REPLY
COMMIT` and `REPLY "students.dbf"` are the same grammar -- a token -- and the
ASK declares which kind it expects, so validation belongs to the asker rather
than to REPLY.

**CORRECTED 2026-09-25 -- THIS PARAGRAPH SAID THERE WERE NONE, AND THERE ARE
FIVE.** As written it read: *"designing ahead of a real case is how vocabularies
bloat: there are ZERO entry-prompts in the tree today"*, and concluded that this
section was only about NOT PRECLUDING an entry prompt rather than serving one.
That was wrong, and HOW it was wrong is worth more than the count.

**THE EARLIER SWEEP SCOPED ITSELF TO THE PRECONDITION PATHS AND THEN CLAIMED THE
TREE.** It measured `maybe_prompt_*` plus the two rebuild/reindex confirms, and
reported *"every prompt measured for R147 is y/N"* -- true of that population.
The sentence above promoted it to a statement about the whole tree. **A
MEASUREMENT WHOSE SCOPE WAS NARROWER THAN ITS CLAIM**, which is the defect this
lane names most often, occurring in a document that teaches the rule.

**MEASURED 2026-09-25 at `4d47bc43c`:** every `std::getline(std::cin, ...)` and
`std::cin >>` under `src/` and `include/` -- **15 reads in 9 files**, one of them
(`reader.cpp:16`) the REPL loop and not a prompt. Three shapes: **3 confirms**,
**5 FREE ENTRIES**, **6 command loops**. The entries, with their own prompt text:

    app_simple_browser.cpp:857   "Enter value for <field> [<type>] (current=<v>): "
    app_simple_browser.cpp:1022  "Field name or #? "
    app_simple_browser.cpp:1047  "Enter value: "
    cmd_browser.cpp:190          "Field name: "
    cmd_browser.cpp:199          "New value: "

So entry prompts are not hypothetical, and under ruling (1) **serving them is in
scope rather than merely not precluding them.** `:857` is the binding case: it
already prints the FIELD NAME, the FIELD TYPE and the CURRENT VALUE, so an
`entry` ask carries those three as fields and a modal can render the prompt
faithfully. **That is ADOPTED from what the code already prints, not invented**
-- section 7 of the design-table contract, applied to this protocol.

---

## 4. Why COMMIT proves all three drivers and not just one

The three surfaces are a complete cross-section of the ways a driver can relate
to the engine, and this one precondition exercises each differently:

| driver | relation to the engine | what asking looks like | what it proves |
|---|---|---|---|
| console CLI | in-process, owns the terminal | today's `(y/N)` line | **behaviour unchanged** where nothing is broken |
| TV (TUI) | in-process, terminal owned by TVision | a TVision dialog | the in-process dialog path, no serialisation -- fixes R147 5a.3's visible-but-unanswerable state |
| Workbench | **out of process, over a pipe** | a wx modal, answer returned as `REPLY <verb>` | the only path needing a wire format |

If one precondition works across in-process/no-dialog, in-process/dialog and
out-of-process/serialised, **the mechanism is proven and a second precondition
is a declaration rather than architecture.**

---

## 5. What is owed

1. **Where the precondition is declared.** The `@dottalk.usage` block is the
   house's declaration surface and already carries fourteen fields -- but it is
   documentation the engine does not read at runtime, so this would be **the
   first field with teeth**. That is a real change in what that block IS, and it
   is an owner decision, not a placement detail.
2. **Whether `REPLY` is user-typed.** Gold argues yes: registry row, contract,
   HELP, and a `.dts` can script both halves and assert -- which answers the
   grading problem R146 had to work around. It also means a human can type
   `REPLY COMMIT` with nothing pending, which needs a defined answer.
3. **Whether DISCARD joins the prompt at the console too**, or only where a
   dialog can show three options. Section 3 says the console prompt is lossy;
   fixing that is a separate behaviour change from fixing the drivers.
4. **The pending-intent slot** -- one per session, or per workspace? `WORKSPACE
   SWITCH` exists, and a pending `USE` deferred in one workspace should probably
   not complete in another.
5. **`cmd_ask.cpp` / `cmd_reply.cpp` in `src/cli`** -- confirmed reachable:
   `dottalk_wb` links `dottalk_gui_core` and wx and has NO engine, so it never
   asks; `dottalkpp.exe` links `dottalk_tvui`, so TV is inside the CLI binary.
   **Only one process ever asks.** The author's earlier `include/xbase/`
   recommendation was wrong and is withdrawn.

## 6. Not measured

- Whether any OTHER precondition in the tree has this shape. ERASE's `CONFIRM`
  token solves the same problem differently and is NOT a prompt; whether it
  should become a declared precondition too is out of scope here.
- What `ROLLBACK` does to a workspace-wide dirty set, as against one area.
  `maybe_prompt_all` exists; a discard-all has not been read.
- Whether the TVision dialog is this lane's work or its own.
- **What an ENTRY prompt would validate against.** ~~nothing in the tree asks
  for a value today, so there is no measured case to design the validation
  from~~ -- **CORRECTED 2026-09-25: five do, and section 3b lists them.** The
  validation question is still open, but it is no longer unmeasurable: the cases
  are a DBF field name, a field ordinal, and a typed field value whose type the
  prompt already prints. Designing from those is adoption; designing from none
  would have been the bloat.
- **The transport.** Deferred by ruling (4). Named here so it is not mistaken
  for settled.
- **`g_suppress_prompts` is a process-global that is never cleared**, set true
  after any successful QUIT-like prompt (`:130`, `:146`, `:167`), while the GUI
  bridge keeps ONE `dottalkpp.exe` alive across every command. Whether that path
  is reachable without the process exiting has NOT been traced. Named, not
  claimed.

## 7. How to verify

    grep -n '"COMMIT"\|"ROLLBACK"' include/dotref.hpp        # 207, 1130
    grep -c 'ROLLBACK' src/cli/dirty_prompt.cpp              # 0
    sed -n '44,57p'  src/cli/dirty_prompt.cpp                # commit-or-cancel
    grep -n 'maybe_prompt' src/cli/*.cpp                     # nine sites, all guards

    # the 2026-09-25 correction to section 3b -- the whole prompt population
    git grep -n 'getline(std::cin\|std::cin >>' -- 'src/**' 'include/**'
    sed -n '855,858p'   src/cli/app_simple_browser.cpp       # name, type, current
    sed -n '123,131p'   src/cli/dirty_prompt.cpp             # the third outcome

## 8. Corrections to this document

Recorded rather than edited away.

- **2026-09-25, section 3b.** Its central factual claim -- *"there are ZERO
  entry-prompts in the tree today"* -- was false when written and is corrected in
  place, with the original sentence quoted so the change is visible. Five entry
  prompts exist. The cause was a scope error, not a counting error: a sweep of
  the precondition paths was reported as a fact about the tree. Found while
  answering R147's own unmeasured question (3), *whether any prompt asks
  something that is not y/N*. Full working:
  `OI-041` in `coordination/OPEN_ITEMS.md`.
- **2026-09-25, section 6.** The matching bullet, which reasoned from the same
  false premise, is struck and replaced.
- **2026-09-25, sections 0-R, 3 and 3a.** Owner rulings: two kinds; four buttons;
  the console goes through the protocol; transport deferred. Section 3's button
  table gained `Proceed`, and section 3a's REPLY list gained that token and a
  correlation id.
- **Unchanged deliberately:** the `ai_report_audit` envelope at the head, which
  records what was reported on 2026-09-17 and is not a live claim about today.
