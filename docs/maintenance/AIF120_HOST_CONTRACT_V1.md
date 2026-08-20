---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260820-COWORK-081
  recorded_at_utc: 2026-08-20T04:10:00Z
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
    id: project.x64base.gui
    root: D:/code/ccode/gui
  git:
    branch: development
    baseline_commit: d67a5ec25
  authorization:
    requested_by: maintainer (member.derald), in-session -- "examine main/shell.cpp
      and see if it could give you the roots of what you need for the gui frontend
      over the engine", then "yes" to making it a ruling. Followed by four
      corrections in flight: the commands are cataloged; aliases are in
      shell_commands.cpp; shortcuts in *resolver; and the main shell loads them.
    scope: >
      Read the host contract out of src/cli/shell.cpp and src/tv/foxtalk_app.cpp
      and write it down; relocate R70.5's per-document relation emission into that
      lifecycle; add gui/uidef/wx_host.cpp. Reads src/, writes only gui/ and docs/.
  report:
    path: docs/maintenance/AIF120_HOST_CONTRACT_V1.md
    kind: ruling
---

# AIF-120 -- R72: the host contract was already written, inside a function whose other two thirds are a terminal loop

**Status: review-needed.** The author does not self-approve.

## 0. The one-paragraph version

The maintainer pointed at `src/cli/shell.cpp` and asked whether `run_shell()` gives
the roots of a GUI frontend over the engine. It gives more than roots: **it is the
host contract, complete, in order, with a symmetric teardown.** A GUI does not need
a host designed -- it needs `run_shell()` with the middle third removed. Reading it
also convicted R70 of re-deriving initialization the house already performs, and
turned what I had called a missing mechanism into an existing one I had not looked
for. `gui/uidef/wx_host.cpp` is that host; the render below came out of it.

**Evidence tier: runtime-proven.** The generated window builds against the real
host, links 46 house translation units, opens the shipped x64 tables, installs the
engine's cursor hook, attaches the document's relations, fills the grid, and
unwinds in reverse.

## 1. `run_shell()` is three parts, and a GUI replaces one

| lines | part | who owns it |
|---|---|---|
| 506-550 | **host setup** | a GUI must do this |
| 551-769 | the REPL over `std::cin` | **wxWidgets replaces this** |
| 770-789 | **teardown**, exactly reversed | a GUI must do this |

Setup, in `shell.cpp`'s own order:

```cpp
XBaseEngine eng;  eng.selectArea(0);  g_shell_engine = &eng;   // 527-529
xbase::cursor_hook::set_callback(&on_cursor_changed, &eng);    // 531
relations_api::attach_engine(&eng);                            // 532
relations_api::set_autorefresh(true);                          // 533
register_shell_commands(eng, /*include_ui_cmds=*/true);         // 535
dottalk::ensure_builtin_commands_registered();                 // 536
shell_eval_register_for_loops();  loop_set_executor(...);       // 537-538
cmd_INIT(cur, empty);                                          // 543
relations_boot::autoload();                                    // 548
```

Teardown, at 777-783: `relations_boot::autosave()`, then
`cursor_hook::set_callback(nullptr, nullptr)`, then
`relations_api::attach_engine(nullptr)`, then `g_shell_engine = nullptr`. Reverse
order, every acquisition released. **That symmetry is the part R70 did not have at
all.**

The terminal-specific parts are three lines and they identify themselves: the
`isatty` test, `colors::applyTheme`, and the startup banner. Everything else is
host, not console.

## 2. This is an adoption, not an invention -- and I should have found it first

`src/tv/` already hosts this engine from a non-CLI frontend:

```cpp
// src/tv/foxtalk_app.cpp:469, src/tv/cmd_foxpro.cpp:568
if (auto* eng = shell_engine()) register_shell_commands(*eng, /*include_ui_cmds=*/false);
```

Turbo Vision reaches the engine through the same `shell_engine()` seam and passes
**`include_ui_cmds=false`**, because a frontend with its own UI does not want the
shell's UI launchers. R11 in this lane was already an adoption discovered after
being declared absent, for the same reason: **the house rule is look for prior art,
and a seam is invisible to a search shaped like a feature.** I searched for a host
and found none because I was looking for something called a host.

## 3. R70.5 relocated -- the correction this ruling exists for

R70.5's fix was right about the defect and wrong about the address. The generated
frontend emitted, per document, into widget-construction code:

```cpp
relations_api::attach_engine(shell_engine());
relations_api::add_relation("STUDENTS", "ENROLL", {"SID"});
relations_api::set_current_parent_name("STUDENTS");
relations_api::set_autorefresh(true);
```

Three of those four lines are `shell.cpp:532-534` verbatim. **The generator was
re-implementing the host's own initialization**, once per document, inside
`OnInit`, with no ordering guarantee relative to the engine and no teardown.

The split R72 makes:

- **The document owns WHAT.** `uidef_wx.py --stream` now emits one pair of free functions -- `uidef_attach_source(xbase::XBaseEngine&)` carrying that document's `SOURCE` graph, and `uidef_detach_source()` clearing the streams first because they hold cursor state.
- **The host owns WHEN.** `wx_host.cpp` calls attach after the areas are open; `wxApp::OnExit` calls detach. The generated file *declares* the seam and the host *defines* it -- the same shape `--dispatch` has used since R38 with `uidef_register` / `uidef_after_init`.

`OnInit` is now one line: `uidef_attach_source(*shell_engine());`

## 4. What I called a missing mechanism, and was not

In answering "how close are we", I wrote that "nothing connects grid selection to
the current record, so `detail`, `summary` and `statusbar` do not follow the user."
That is false, and `shell.cpp:339` is why:

```cpp
static void on_cursor_changed(xbase::DbArea& moved, const char*, void* user) noexcept {
    ...
    relations_api::refresh_if_enabled();
}
```

`xbase::cursor_hook::set_callback` is an **engine-level cursor-changed signal**, and
the shell already uses it to keep the relation set current. A GUI grid installs the
same callback and repaints its sibling frames from it. Selection-follows-record is
not a mechanism to design; it is a callback to register. `wx_host.cpp` registers it.

Recorded as a defect in my own reasoning rather than a discovery: I asserted an
absence from the shape of my own question, which is the trap the house skill names
as *"a search shaped by the object you have cannot find an object with a different
schema."*

## 5. The command surface -- cataloged, aliased, resolved, and expensive

Four maintainer corrections in flight, each of which changes the answer.

**The commands are cataloged, and a GUI presents rather than owns.**
`include/gui/core/gui_command_catalog.hpp` already carries a written
`@dottalk.contract` whose authority clause settles it:

> GUI command catalog entries may label, prefill, or invoke DotTalk++ commands, but
> they must not redefine command syntax or behavior. [...] If a GUI action differs
> from runtime command truth, runtime/help truth wins and the catalog must be
> corrected.

**Aliases are in `shell_commands.cpp`, and the main shell loads them.** Registered
inside `register_shell_commands()` (314, 517, 549). A frontend that wants them
calls that function; it does not restate a name anywhere.

**Shortcuts are a different mechanism.** `cli::ShortcutResolver` /
`shell_shortcuts::resolve`, applied by `expand_shortcut_lead()` at `shell.cpp:682`
to the **leading token only**, before dispatch -- `H` -> `HELP`, `?` -> `FORMULA`,
`BT` -> `BROWSETUI`, `!` -> `BANG`. So a frontend dispatching command text owes,
in this order: trim, `expand_shortcut_lead`, then dispatch into the registry
`register_shell_commands` populated. An alias is a second registered name; a
shortcut rewrites the line first. Conflating them gives a catalog with duplicates
and a `?` that does nothing.

**Measured cost of the command surface**, closure computed from `nm`:

| host | house translation units |
|---|---|
| grid only (this ruling's host) | **46** |
| host + `register_shell_commands` | **318** |
| cost of the command surface | **+272** |

That is R61's boundary with a number on it. A grid needs 46; a command line needs
318. **This ruling's host deliberately does not register commands** -- not because
commands are unwanted, but because a frontend should pay for the surface it uses,
and the number says the two are worth being separate targets.

## 6. Proof

- **Compiled:** all 18 fixtures, with and without `--stream`, clean as objects under `-Wall -Wextra`.
- **Unchanged:** 18/18 byte-identical without `--stream` to the pre-R70 baseline. See correction 53.
- **Linked:** the generated file + `wx_host.cpp` + 46 house translation units.
- **Ran:** `uidef_host: 2 area(s) open, cursor hook installed, SOURCE relations attached`, then the window below.

Three rows, engine-named columns, `status_line()` in the status bar -- the same
answer `DOTSCRIPT aif120/r70_stream.dts` gives, now through a host that unwinds
what it acquired. Capture:
`docs/maintenance/evidence/AIF120_R72_host_render.png`.

### Correction 53 -- the invariant caught a cosmetic change

Adding the `OnExit` override split `return true; } };` across two lines for **every**
document, including those with no stream. Byte-identical-without-`--stream` is the
whole argument that `--stream` is additive, so a formatting change breaks it as
surely as a behavioural one. The split now happens only where there is an override
to put between the braces. The invariant is a real gate precisely because it fails
on changes that look harmless.

## 7. Reported, not fixed

**R72.1 -- `dt_cli_outbuf` is unreachable.** `shell.cpp:158` defines it in an
anonymous-scope `namespace dt_cli_outbuf` **inside the .cpp**, so the non-tty output
buffering the shell installs at 521 cannot be used by any other host. A GUI is
non-interactive by the `isatty` test, so it is exactly the caller that wants it, and
it is the one caller that cannot have it. `cli::OutputRouter` is the shared
alternative and is what a GUI should use; recorded so the asymmetry is deliberate
rather than discovered again.

**R70.6, now unavoidable in stream mode.** `uidef_attach_source` takes
`xbase::XBaseEngine&`, so every stream-mode file includes `xbase.hpp`, which carries
three `-Wsign-conversion` warnings at 477/481/485. Measured: 4 warnings on a
stream-mode translation unit, **0 of them in generated code.** Clean under
`-Wall -Wextra`.

## 8. Open

- **`relations_boot::autoload()` is not called by this host.** The shell calls it at 548 and `autosave()` at teardown. Whether a generated frontend should participate in the persisted relation set, or stay confined to its document's `SOURCE`, is an owner decision -- it is the difference between a frontend that reads a document and one that inherits session state.
- **`cmd_INIT` is not called.** The shell runs it at 543. Unclear what a GUI owes it.
- **Text dispatch is unbuilt.** Section 5 says what it costs and in what order; nothing here does it.
- **MSVC.** Still nothing in R70, R71 or R72 built outside gcc 13 / wx 3.2.4 / Linux.

## 9. Good Neighbor

| | |
|---|---|
| What changed | new `gui/uidef/wx_host.cpp`; `gui/uidef/uidef_wx.py` emits a lifecycle pair instead of four inline calls; new ruling; one evidence image; ledger rows |
| Whose area | AIF-120 / `project.x64base.gui`. `src/` was **read only** -- no engine, shell, tv or gui-core file is touched |
| Authorization | maintainer, in-session: "examine main/shell.cpp ...", then "yes" |
| How to verify | `python gui/uidef/uidef_wx.py <doc> out.cpp --stream`; compile per section 6; `R70_DBF=<dbf/x64> UIDEF_TABLES=STUDENTS,ENROLL ./app` |
| How to undo | `git revert`. The no-`--stream` output is byte-identical before and after, so a revert cannot disturb any existing generated file |
| Risk | low. One new file nothing links yet, and a generator change proven additive on 18 fixtures |

## 10. Handoff -- PowerShell, run in `D:\code\ccode`

```powershell
git status -uall

git add gui/uidef/wx_host.cpp
git add gui/uidef/uidef_wx.py
git add docs/maintenance/AIF120_HOST_CONTRACT_V1.md
git add docs/maintenance/evidence/AIF120_R72_host_render.png
git add docs/maintenance/AIF120_LANE_STATUS_AND_FIXTURES_V1.md

git status -uall

git commit -m "AIF-120: R72 -- the host contract read out of run_shell(); R70.5's relation setup relocated from generated code into the host lifecycle, and the cursor hook that already answers selection-follows-record"
```
