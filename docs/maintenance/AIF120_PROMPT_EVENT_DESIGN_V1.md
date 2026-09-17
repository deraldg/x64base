---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260917-COWORK-003
  recorded_at_utc: 2026-09-17T01:39:00Z
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
    baseline_commit: df5dcf062
  authorization:
    requested_by: maintainer (member.derald), in-session 2026-09-16 -- "do it
      now dinner is not ready", on being offered the prompt event's shape.
    scope: >
      Answers R147 section 5 item 1 -- the prompt event's spelling, and whether
      it carries text, a message id, or both. A PROPOSAL, not a ruling and not
      an implementation. NO CODE WAS WRITTEN.
  report:
    path: docs/maintenance/AIF120_PROMPT_EVENT_DESIGN_V1.md
    kind: design
---

# The prompt event -- a hook that returns a decision, and a fourth answer that is not No

Lane: AIF-120 (application-ui-dsl). Owner: `member.derald`.
Author: `member.ai.claude.cowork`. Status: **review-needed**.
Implements R147 section 5 item 1. **Proposes; decides nothing.**

> ## PARTLY SUPERSEDED THE SAME DAY -- READ THIS FIRST
>
> **`AIF120_COMMIT_PRECONDITION_WORKED_EXAMPLE_V1.md` (2026-09-16) corrects
> section 1 of this document. Section 4's driver table and section 5's ERASE
> observation still stand; the PLACEMENT does not.**
>
> This document puts `ask()` in the ENGINE as a hook the drivers install into.
> **That is backwards.** The owner then ruled the shape as CONTROL FLOW, and the
> measurement that followed -- every one of the nine prompt sites is a GUARD, so
> nothing is ever mid-work when it asks -- moves the asking to the SHELL:
>
> - the command **DECLARES** what it requires;
> - the **DISPATCHER** checks before dispatch and owns the asking;
> - `ASK` / `REPLY` operate where the command stream is already owned, so nothing
>   reads stdin mid-command and the defect class is ABSENT rather than framed.
>
> The engine therefore never learns what a console is, which this document
> assumed it would have to.
>
> **Also revised there:** `REPLY` carries a TOKEN rather than a bool -- for the
> COMMIT precondition a VERB, because `COMMIT` and `ROLLBACK` are both registered
> and today's y/N prompt cannot reach the second; and R145's fixed-versus-editable
> property already covers an ENTRY prompt, which section 7 item 1 here left open.
>
> **WHY THIS BLOCK EXISTS RATHER THAN AN EDIT.** The 2026-09-16 closeout's whole
> complaint was that this lane routes a reader to a stale answer with no
> instrument in between, and it counted three stale authorities in two days. A
> superseded design left unmarked is the fourth, authored the same afternoon by
> the session that wrote the complaint down. R77 section 3 carries a status block
> for the same reason.

---

## 1. The shape is ADOPTED, not invented, and the tree already has it twice

AIF-120's contract section 7 rules that PROPS are adopted rather than invented.
The same discipline applies to mechanisms, and this house already carries two
hook families that answer the two halves of the question:

| existing | signature | what it is |
|---|---|---|
| `xbase::cursor_hook` | `void (*)(DbArea&, const char* reason, void*)` | the engine TELLS a driver |
| `xbase::trigger_hooks::BeforeWriteFn` | **`bool (*)(DbArea&, ...)`** | the engine ASKS and OBEYS |

**`BeforeWriteFn` is the precedent, not `cursor_hook`.** A prompt is not a
notification; it is a question whose answer changes what the engine does next,
which is exactly what `set_before_callback` / `allow_record_write` already do
for the trigger veto. The proposal is that family with a different payload.

    namespace dottalk::ask {

    enum class Answer { Yes, No, Unanswerable };

    struct Question {
        helpdata::MessageId id;      // for a driver that can render
        const char*         text;    // already-rendered fallback
        const char*         scope;   // "USE", "CLOSE", "WORKSPACE OPEN", ...
        Answer              fallback;// what an unanswered question means
    };

    using AskFn = Answer (*)(const Question&, void* user) noexcept;

    void   set_callback(AskFn fn, void* user) noexcept;
    Answer ask(const Question& q) noexcept;   // Unanswerable when no hook is set

    } // namespace dottalk::ask

---

## 2. BOTH the id and the text, and the reason is measured

R147 section 5 asked: text, message id, or both. **Both**, and not as a hedge.

- **The id, because the answer already exists.** `helpdata_messages.cpp` carries
  **1,331 message ids** in **en-US (1,334 rows), plus es, it, fr and de at 329
  rows each**. A driver rendering a dialog should localise through that table,
  not print an en-US string the engine chose.
- **The text, because not every driver can render**, and the console must keep
  printing exactly what it prints today. A rendered string in the payload makes
  the console handler a one-liner and keeps this change behaviour-neutral where
  nothing is being fixed.

**AND THE FIRST PIECE OF WORK IS THAT NO PROMPT HAS AN ID.** Measured at
`df5dcf062`: every prompt in the tree is a literal. `dirty_prompt.cpp:59` builds
`"TABLE: uncommitted changes detected (...). COMMIT changes? (y/N) "` inline;
`cmd_rebuild.cpp:132` and `cmd_reindex.cpp:164` build theirs with an
`ostringstream`. Only the CANCELLATIONS carry ids -- `MessageId::CloseCanceledText`,
`MessageId::ShellQuitCanceled`. **The half a user reads in their own language is
the half that was never given an id**, and minting those, with five locales
each, is step one and is mechanical.

---

## 3. `Unanswerable` is the point, and it is NOT `No`

Today nothing can tell *"the user said no"* from *"there was nobody to ask."*
Both arrive as `false`, at all nine `maybe_prompt_*` sites, and that is why a
`.dts` silently cancels a `USE` and looks like it made a decision.

**Making the third state a value costs nothing and changes nothing.** Every
caller today cancels on false; `Unanswerable` also cancels, by way of
`Question::fallback`, which is `No` at every site currently in the tree.

> **This proposal does not change what happens unattended. It changes whether
> anyone can tell why it happened.**

That is also R131's `g_suppress_prompts` generalised. R147 section 5 item 4
ruled that suppression is not superseded, because a `.dts` still needs the
documented default. `Unanswerable` IS that default, expressed as a value instead
of a global flag set on one code path.

---

## 4. Three installers, one interface

| driver | installs | result |
|---|---|---|
| console CLI | today's `cout` + `getline` handler | **behaviour unchanged** |
| TV (TUI) | a TVision dialog handler, in-process | fixes the visible-but-unanswerable state measured in R147 5a.3 |
| `dottalkpp.exe` **as the GUI's subprocess** | a SERIALISING handler | writes the question out, reads the answer back |
| DOTSCRIPT / unattended | **nothing** | `ask()` returns `Unanswerable`, caller takes the fallback |

**Only the third one needs a wire format**, and that is the whole reason the
event beats scraping: two of the three drivers are in-process and never
serialise anything.

    stdout:  __DOTTALK_ASK_<n>__ <scope> <message-id> <rendered text>
    stdin:   __DOTTALK_ANSWER_<n>__ YES | NO

The `<n>` is the same monotonic id the bridge already mints for its completion
marker (`gui_shell_runtime.cpp:157`), so correlation is free.

### 4a. It closes the sixty seconds without a second mechanism

`gui_shell_runtime.cpp:179` waits `seconds(60)` and today cannot distinguish a
wedged pager from a slow honest command, because both are silence. Seeing
`__DOTTALK_ASK_` gives the bridge a **third state -- waiting on a human** -- so
the clock stops while the modal is open. R147 section 4a predicted this; the
wire format is where it actually lands.

---

## 5. ERASE already solved this a different way, and that is worth a decision per site

`MessageId::EraseReRunConfirmText` -- *"Re-run with CONFIRM to perform
deletion."* **ERASE does not ask. It requires an explicit token on the command
line**, and that works in every driver, needs no event, no dialog and no
serialisation.

So the tree has TWO idioms for *are you sure*, and only one of them has the
problem this design is fixing. **Part of the nine-site surface may be better
served by ERASE's idiom than by a dialog**, and that is a judgement per site
rather than a rule:

- *Are you sure you want to destroy this?* -- the ERASE shape fits. The user can
  restate their intent.
- *You have unsaved work; commit it first?* -- the ERASE shape does NOT fit. The
  question is not about the command the user typed; it is about state they may
  not know they are carrying, and answering it by re-typing something is asking
  them to guess.

The nine `maybe_prompt_*` sites are all the second kind. **Recorded so the
choice is made rather than defaulted.**

---

## 6. It is gradeable without a console, which R146 had to learn the hard way

The R146 lesson was that an interactive surface cannot be graded by a `.dts`,
so the testable unit has to be extracted. **This design is testable by
construction**: install a fake `AskFn` that returns a scripted answer and assert
the engine obeys it; install none and assert `Unanswerable`; assert the fallback
is honoured. No table, no console, no pipe -- a ctest beside
`dottalkpp_area_bound_view_test`.

**And the arm that matters is the one that must go red:** a handler returning
`No` must leave the buffer intact and the command cancelled, and a handler
returning `Yes` must commit. A hook nobody can prove the engine OBEYS is the
`g_suppress_prompts` shape again -- a mechanism that exists and does nothing.

---

## 7. Open, and none of it is settled here

1. **Is `Yes`/`No` enough?** Every prompt found is y/N, but *commit / discard /
   cancel* is a plausible third answer for the dirty-buffer case and the enum
   would have to grow. **Not proposed** -- it is a behaviour change, not a
   plumbing one.
2. **Where `ask` lives.** `dirty_prompt.cpp` is `src/cli`, but TV and the GUI
   core both need it and neither links the CLI. `trigger_hooks` sits in
   `src/xbase` for exactly that reason, and R128's precedent (header-only in
   `include/xbase/` so both targets reach it without linking the CLI) is the
   obvious answer.
3. **Whether the wire format is text or something framed.** Text is greppable,
   which this house values; it is also breakable by a prompt containing a
   newline.
4. **Timeout on the GUI side while a modal is open** -- indefinite, or bounded?
   A modal nobody answers should not wedge the shell forever either.
5. **Whether `src/tv` raising a dialog is in this lane or its own.**

## 8. How to verify the claims above

    grep -n 'BeforeWriteFn' include/xbase/trigger_hooks.hpp        # bool-returning hook
    grep -c '^\s*[A-Z][A-Za-z0-9_]*,' src/help/helpdata_messages.hpp   # 1331 ids
    sed -n '57,62p' src/cli/dirty_prompt.cpp                       # literal, no id
    sed -n '150,200p' src/gui/core/gui_shell_runtime.cpp           # the marker id
