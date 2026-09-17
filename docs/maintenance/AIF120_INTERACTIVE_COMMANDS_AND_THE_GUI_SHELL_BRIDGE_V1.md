---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260917-COWORK-001
  recorded_at_utc: 2026-09-17T00:57:42Z
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
    baseline_commit: 17f5dedaa
  authorization:
    requested_by: maintainer (member.derald), in-session 2026-09-16 -- "some
      commands don't run and some have a significant delay if launched from the
      command line in appgui", with a pasted Workbench transcript, then
      "document the findings".
    scope: >
      Reads the GUI shell bridge and every src/cli translation unit that touches
      std::cin, against a transcript the maintainer captured. No code, ruling,
      fixture or CMake file was changed. Names three fix shapes and chooses
      none: src/gui and src/cli are both engine and want an explicit go.
  report:
    path: docs/maintenance/AIF120_INTERACTIVE_COMMANDS_AND_THE_GUI_SHELL_BRIDGE_V1.md
    kind: finding
---

# An interactive command in the Workbench eats the sentinel that ends it, and then eats the conversation

Lane: AIF-120 (application-ui-dsl). Owner: `member.derald`.
Author: `member.ai.claude.cowork`. Status: **review-needed**.
Evidence class: **measured**, read-only, at `17f5dedaa`.
Measured during the maintainer's 2026-09-16 working day; the envelope's UTC
stamp falls on the 17th because he is at UTC-7.

**Two symptoms, one defect.** The maintainer reported them as two: *"some
commands don't run and some have a significant delay."* They are the same
mechanism seen from either end.

---

## 1. The mechanism

`src/gui/core/gui_shell_runtime.cpp`, `PersistentProcessShellRuntime::run()`.
The Workbench does not spawn a process per command; it keeps one
`dottalkpp.exe` alive and talks to it over a pipe. To know when a command has
finished it appends a sentinel (`:168`):

    <the user's command>\n
    ECHO __DOTTALK_GUI_DONE_<n>__\n

and then waits for that marker to appear on stdout (`:179`):

    output_changed_.wait_for(lock, std::chrono::seconds(60), ...)

**The delay is not variable. It is sixty seconds, by construction**, and it is
the timeout rather than the work.

**SMARTBROWSER prints its first page and calls `std::getline(std::cin)` at
`-- More --`.** The next line in the pipe is the marker. The pager reads it as
a PAGER COMMAND. `ECHO __DOTTALK_GUI_DONE_7__` is not `Q`, not `TOP`, not
`OPEN CHILD`, so the pager prints its hint line and loops.

The marker is therefore never echoed. The GUI waits the full minute and reports

    warning: [gui.command.cli_failed] ... exit=-1
    Timed out waiting for the persistent DotTalk++ shell command marker.

**And the pager is still running.** The next command the user types is written
into the same pipe and the pager eats that too. From the maintainer's
transcript, verbatim:

    > SQLVER
    ... (hint: OPEN CHILD/BACK/SHOW BREADCRUMBS/SHOW CHILDREN/...)

`SQLVER` never ran. It was answered by a pager. **That is the whole of "some
commands don't run"**, and every command after it costs another sixty seconds
and feeds the same loop. The session does not recover; the Workbench has to be
restarted.

---

## 2. Six commands read stdin. One declares it.

Measured over `src/cli/*.cpp` for `getline(std::cin` / `std::cin >>` /
`std::cin.get`:

| file | command | declares `interactive_prompt: yes` | `noargs:` |
|---|---|---|---|
| `app_smart_browser.cpp` | SMARTBROWSER | **yes** | `interactive` |
| `app_simple_browser.cpp` | SIMPLEBROWSER | no | `launch` |
| `cmd_browser.cpp` | BROWSER | no | `interactive` |
| `cmd_rebuild.cpp` | REBUILD | no | `mutate` |
| `cmd_reindex.cpp` | REINDEX | no | `mutate` |
| `dirty_prompt.cpp` | (shared y/N helper) | n/a | n/a |
| `browse/browse_io.cpp`, `browse/browse_session.cpp`, `console_utils.cpp`, `reader.cpp` | (helpers) | n/a | n/a |

**THE HOUSE ALREADY WRITES THIS DOWN AND NOTHING READS IT.**
`app_smart_browser.cpp` carries, in its `@dottalk.usage v1` block:

    noargs: interactive
    risk:
      interactive_prompt: yes

That is machine-readable, it sits on the command, and the one caller that most
needs it -- the GUI shell bridge -- never asks. The contract is not missing a
field. It has the field, one command sets it, and no consumer consults it.

---

## 3. Two severities, and the second is much milder than it looks

They must not be described as one hazard.

**(a) INTERACTIVE LOOPS -- SMARTBROWSER, BROWSER, SIMPLEBROWSER.** The marker is
consumed, not recognised, and the loop continues. **The shell never returns and
the session is poisoned.** This is section 1.

**(b) PROMPTING COMMANDS -- REBUILD, REINDEX, and the dirty-buffer confirm.**
The marker is consumed AS THE ANSWER, and then the command finishes. Read the
two parsers rather than assuming:

- `dirty_prompt.cpp` `parse_yes_default_no()`: empty answer returns false;
  anything not `y`/`yes` returns false. **Default No.**
- `cmd_rebuild.cpp:140`: `return c == 'Y'` on the first character, with empty
  taking the default.

**The marker begins with `E`, so it always answers NO.** The command refuses,
completes, and the shell recovers. The cost is sixty seconds and a silent
refusal the user reads as a hang -- not a spurious mutation.

**The narrow real hazard in (b)** is a command beginning with `Y` typed while a
prompt is pending: it answers Yes to a mutating confirm. That is a small window
and it is named here rather than left to be discovered.

---

## 4. This is R146's grading problem wearing a worse face

R146 (2026-09-16) recorded, from
`dottalkpp/data/scripts/buffer_visibility_probe_v3_smartbrowser.dts`, that under
a script SMARTBROWSER *"paints the FIRST PAGE BEFORE reading input, and a failed
`std::getline(std::cin)` returns Quit -- so under a script it renders one page
and exits."* That is why no `.dts` can reach `OPEN CHILD`, and why R146's fix
had to be graded by a ctest.

**The two drivers fail in opposite directions from the same absence.**

| driver | stdin | `getline` | result |
|---|---|---|---|
| `.dts` | at EOF | **fails** | pager quits; one page; silent under-report |
| GUI bridge | open pipe, never closed | **succeeds** | pager consumes the driver's own traffic |

Script mode loses information. GUI mode loses the session. **Neither driver can
ask "does this command need a console?", and neither command can answer.** The
suppression machinery for the prompt half already exists and is unused: R131
recorded that `g_suppress_prompts` (`dirty_prompt.cpp:27`) is set only on the
QUIT path and DOTSCRIPT never touches it.

---

## 5. Three fix shapes. This document chooses none.

Ordered cheapest first. All three touch `src/gui` or `src/cli`, which are engine
and want an explicit go -- the posture R128, R131 and R135 each state of
themselves.

**(1) The bridge refuses what it cannot drive.** Before writing to the pipe,
read the command's `interactive_prompt` and answer *"SMARTBROWSER needs a
console; run it in the CLI"* instead of hanging. One place, no engine change,
no new vocabulary. **Its limit is section 2: it covers the commands that
DECLARE, which today is one of six.**

**(2) Backfill the declaration on the other five.** Contract-only, no behaviour
change, and it is what makes (1) worth having. Note this is the house rule
already in force -- the contract is the whole block -- applied to a field that
exists and is unset.

**(3) The engine knows it has no console, and an interactive command refuses up
front.** The real fix and the largest. It would also have made a `.dts` say
*"SMARTBROWSER needs a console"* rather than silently painting one page and
letting the suite report PASS -- the defect INDEX_X64 v2 was corrected for on
2026-09-13.

**(1) and (2) are complementary and (3) supersedes both.** Doing (1) alone
would advertise a guard that misses five of six commands, which is its own
AIF-079 shape -- a declared capability narrower than it reads.

## 6. Not measured

- **Whether the 60-second wait is right for anything.** It was read, not judged.
  A long-running non-interactive command and a wedged pager are indistinguishable
  to the bridge today.
- **Whether the bridge can recover a poisoned shell** without a restart -- for
  example by sending `Q`, or by restarting the child on timeout. Neither was
  tried.
- **The TV (`src/tv`) surface**, which was not examined at all and may drive the
  engine the same way.

## 7. How to verify

    sed -n '160,200p' src/gui/core/gui_shell_runtime.cpp
    git grep -ln 'getline(std::cin\|std::cin >>\|std::cin.get' -- 'src/cli/*.cpp'
    git grep -l 'interactive_prompt: yes' -- 'src/cli/*.cpp'   # one file
    sed -n '44,57p' src/cli/dirty_prompt.cpp                   # default No
    sed -n '132,142p' src/cli/cmd_rebuild.cpp                  # c == 'Y'
