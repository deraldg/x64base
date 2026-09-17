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
Scopes R147. **Proposes; decides nothing.**

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

    REPLY COMMIT      run COMMIT, then re-dispatch the pending command
    REPLY ROLLBACK    run ROLLBACK, then re-dispatch the pending command
    REPLY CANCEL      drop the pending command

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

**STATED PLAINLY BECAUSE DESIGNING AHEAD OF A REAL CASE IS HOW VOCABULARIES
BLOAT: there are ZERO entry-prompts in the tree today.** Every prompt measured
for R147 is y/N -- two direct parsers and one shared helper reached from nine
sites. So this section is about **not precluding** an entry prompt, not about
building one. The fixed/editable property is what a second precondition would
DECLARE; it is not work this worked example does.

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
- **What an ENTRY prompt would validate against.** Section 3b keeps the grammar
  open for one; nothing in the tree asks for a value today, so there is no
  measured case to design the validation from, and guessing one would be the
  vocabulary bloat that section warns about.

## 7. How to verify

    grep -n '"COMMIT"\|"ROLLBACK"' include/dotref.hpp        # 207, 1130
    grep -c 'ROLLBACK' src/cli/dirty_prompt.cpp              # 0
    sed -n '44,57p'  src/cli/dirty_prompt.cpp                # commit-or-cancel
    grep -n 'maybe_prompt' src/cli/*.cpp                     # nine sites, all guards
