---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260926-COWORK-212
  recorded_at_utc: 2026-09-26T04:10:00Z
  agent:
    provider: Anthropic
    product: Claude (Cowork)
    model: claude-opus-5
    access_mode: local_write
  session:
    id: not_exposed
    chat_reference: not_exposed
    run_id: COWORK-20260925-001
  project:
    id: project.x64base.runtime
    root: D:/code/ccode
  git:
    branch: development
    baseline_commit: bc7bf6bdd
  authorization:
    requested_by: maintainer (member.derald), in-session 2026-09-25 -- "do s3 and
      s4, then we can talk about transport - check how the cli version uses main
      and appgui/workspace gui".
    scope: >
      RECONNAISSANCE ONLY. Reports what the three drivers do today and what each
      transport shape would cost each of them. It does NOT rule; owner ruling (4)
      of 2026-09-25 deferred transport and this document does not reopen it.
      NO CODE WAS WRITTEN FOR THIS REPORT.
  report:
    path: docs/maintenance/AIF120_THREE_DRIVERS_AND_ONE_PIPE_V1.md
    kind: measurement
---

# Three drivers, one pipe, and a sentinel the engine has never emitted

Lane: AIF-120 (application-ui-dsl). Owner: `member.derald`.
Author: `member.ai.claude.cowork`. Status: **review-needed**.
Measured at `bc7bf6bdd`, after S3 (`2a8f191e9`) and S4 (`a73a6f4d4`) landed.

Scopes R147 section 5's third owed item -- the transport -- by measuring the
ground it would have to travel over. **It proposes no wire format and asks for no
ruling.** Ruling (4) deferred transport deliberately; the hazard named there was
that a deferred decision gets made by accident by the first line of code, and the
answer to that is to know the ground before anyone writes the line.

---

## 0. The one-sentence result

**The CLI and the GUI share no channel at all, the bridge's only structured token
is one the bridge writes itself, and the third driver has no pipe to frame
anything on -- so the transport question is really a question about where the
ASK handler seam sits, not about a wire format.**

---

## 1. `main.cpp` does not know the GUI exists

`src/cli/main.cpp` is 252 lines. Swept for `appgui`, `app_gui`, `workbench`,
`gui`: **zero matches.** It accepts exactly two arguments:

```
--help | -h | /?      print usage, return 0
--script <file>       open the file, swap std::cin's rdbuf to it, run_shell()
```

Anything else is an error. There is no flag for "a driver is on the other end of
this pipe", no unattended switch, no mode. `run_shell()` is the whole product.

**`--script` is a streambuf swap, not an interpreter** (`CinRedirectGuard`, defined
`main.cpp:50`, used at `main.cpp:213`). It replaces `std::cin`'s buffer and leaves the process's
own stdin handle untouched. That detail has already cost something: `cli::ask`'s
`console_available()` asks `_isatty(_fileno(stdin))` -- the C handle -- while
`ask()` reads `std::cin`. Under `--script` from a console the two disagree, and
the prompt still eats the next line of the script. Proven with a pty repro on
2026-09-25; recorded here because any transport that wants to know *who is
listening* cannot learn it from `isatty` alone.

## 2. `APPGUI` launches and forgets

`src/cli/app_gui.cpp` is 321 lines and its whole mechanism is three:

```
app_gui.cpp:212-219   launch_detached(exe)
                      Windows: std::system("start \"\" \"<exe>\"")
                      POSIX:   std::system("\"<exe>\" &")
```

No handle is retained, no pipe is created, no exit code is read. The command
prints `APPGUI: launching <path>` and returns. **The CLI never speaks to the GUI
and has no way to.** Whatever channel an ASK uses, `APPGUI` is not it and does
not need to change.

## 3. The bridge, in full

`src/gui/core/gui_shell_runtime.cpp` (510 lines) holds two runtimes.

**`ScriptShellRuntime`** -- `persistent()` false, delegates to
`run_runtime_cli_command` (`gui_cli_bridge.cpp:266`). This is what **every
non-Windows build gets**; the file's own comment records that five helpers above
the `#ifdef` were reported unused on every Linux build, so the persistent path
reads like the extra and is in fact the exception.

**`PersistentProcessShellRuntime`** -- `#ifdef _WIN32` only. One long-lived
`dottalkpp.exe`:

```
:251/:261  CreatePipe x2 (stdout, stdin), inherit flags cleared on our ends
:279-281   STARTF_USESTDHANDLES; hStdOutput AND hStdError both = stdout_write
:287       CreateProcessW, CREATE_NO_WINDOW, cwd = exe's parent
:317       reader_ = std::thread(read_loop)
:321       sleep_for(500ms) then output_.clear()  -- drain the banner
:157       marker = "__DOTTALK_GUI_DONE_" + id + "__"
:168       payload = context_seed + command + "\n" + "ECHO " + marker + "\n"
:170       WriteFile(stdin_write_, payload)
:179       output_changed_.wait_for(lock, seconds(60), marker found || exited)
:186       erase at marker_pos, ok = true
:197       else ok = false, exit_code = -1, "Timed out waiting for ... marker"
```

**STDERR IS MERGED INTO THE SAME PIPE** (`:281`). There is one stream, not two.
Any framing scheme shares it with diagnostics.

**Context seeding** (`context_seed_payload`, `:330`) injects `SETPATH DATA`, `USE ... NOINDEX`,
`SET INDEX TO`, `SET ORDER TO`, `ASCEND`/`DESCEND` and `GOTO` ahead of the user's
command, suppressed for a verb list (`should_seed_active_table`, `:89`).
So the pipe already carries synthesised commands the user never typed.

The consumer is `src/gui/core/session.cpp` -- four `shell_runtime->run(...)` call
sites (`:1380`, `:1731`, `:3308`, `:3339`), plus `write_cli_result` (`:1271`) and
`mirror_cli_result_to_gui` (`:2756`).

## 4. THE MEASUREMENT THAT MATTERS: the engine has never emitted the sentinel

Swept `src/`, `include/` and `gui/` for `__DOTTALK_`:

```
src/gui/core/gui_shell_runtime.cpp:157    <- ONE occurrence. The construction.
```

String literals beginning `"__DOTTALK` under `src/cli/`: **zero.**

So the protocol that exists today is not the engine reporting to a driver. **The
bridge writes the token, hands it to the engine as an ordinary `ECHO` argument,
and recognises its own echo coming back.** The engine has no idea the token means
anything. The namespace `__DOTTALK_*` is, as of `bc7bf6bdd`, entirely unclaimed
by the product.

Two consequences, and they point opposite ways.

**In favour of stdout framing:** the namespace is free, so a new frame cannot
collide with existing output. Nothing prints it today.

**Against:** the same freedom means nothing *validates* it either. `ECHO
__DOTTALK_GUI_DONE_1__` typed at the Workbench prompt is indistinguishable from
the bridge's own marker -- a user can end a command early today. An ASK frame on
the same channel widens that from a nuisance to a reply-forging surface. NOT
measured: whether a forged marker actually desynchronises the id counter, or
merely truncates one command's output.

## 5. The third driver has no pipe at all

`src/tv` runs commands **in-process**: `foxtalk_shell_bridge.cpp:101` calls
`shell_execute_line(area, resolvedLine)` directly. No child, no pipe, no
sentinel, no timeout.

`foxtalk_redirect.cpp:86` (`RedirectController::install`) installs `FoxtalkCoutRedirectBuf` over
`std::cout` and `std::cerr` -- **and not over `std::cin`** -- plus
`startCStdCapture()` on Windows for the C streams.

**So a prompt in the TUI is visible and unanswerable**: the text reaches the
output window, and the `getline` underneath it reads a console stdin that
TVision's event loop owns.

## 6. What each shape costs, per driver

| | persistent bridge | `src/tv` | console |
|---|---|---|---|
| **A. stdout framing** | natural -- already scrapes one token on this pipe | **needs its own implementation**: "stdout" here is a custom `streambuf`, not a pipe, so the frame must be parsed inside `FoxtalkCoutRedirectBuf` | must strip or suppress frames, so the engine must know who is listening -- which nothing in the tree can currently express |
| **B. handler seam (engine calls an installed answerer)** | still needs a serialization, because it is the only cross-process driver | **free** -- in-process, the handler is a function | **already built**: `ask_console.cpp` is that handler, as of `2a8f191e9` |
| **C. second channel (extra handle / named pipe)** | one more handle on `CreateProcessW` | no help -- still needs A or B | no help |

**A is a wire format pretending to be an architecture.** It answers the question
for one driver and leaves the other two to reimplement the decision. **B puts the
decision in one place and leaves only the cross-process driver needing bytes on a
wire** -- and that driver is exactly the one that already has a pipe.

This is not a recommendation on the wire format. It is the observation that
**S3 already built the seam**: every confirm in the tree now enters through
`cli::ask::ask()`. A handler indirection there is one level of pointer away, and
whatever bytes the bridge eventually sends are a detail *below* it rather than a
decision *above* it.

## 7. Named, not claimed

- **The 60-second timeout must be held open while a modal is up.** R147 said so;
  nothing implements it. `wait_for` at `:179` is unconditional.
- **The 500 ms banner drain (`:321`) clears `output_` wholesale.** An ASK emitted
  during startup would be discarded. Not measured whether one can be.
- **The one-shot path has nobody to ask.** `ScriptShellRuntime` starts a process
  per command; a prompt there has no session to answer it, and that path is what
  every non-Windows build uses.
- **The reader thread is not the GUI thread.** `read_loop` (`:405`) notifies a
  condition variable; a wx modal must be raised on the UI thread. Whatever the
  transport, the hand-off between those two threads is real work nobody has
  costed.
- **`console_available()` cannot tell a pipe from a redirected script.**
  Section 1. If the transport ever keys on "is anyone there", this is the
  instrument it would use, and it is wrong in one case today.

## 8. What this does NOT do

It does not rule. Ruling (4) stands: transport is deferred, and the first
implementation names its transport PROVISIONAL in the code and in its commit
message until the owner rules. Nothing here has been written into the engine.
