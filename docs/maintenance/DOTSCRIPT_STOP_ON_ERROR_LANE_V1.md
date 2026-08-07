# DOTSCRIPT-STOP-ON-ERROR -- stop_on_error[severity] flag (lane v1)

Status: **implemented (dev), build+prove pending** (2026-07-20). Not promoted.
Owning lifecycle: DotTalk++ SDLC - script runtime + messaging/error spine.
Relationship: finishes the planned **SET ERRORSTOP** hook (AIF-018/AIF-021) as a
severity threshold; the foundation under the DotScript-array spec's ASSERT/error
hole.

## What the maintainer asked for

> "dotscript needs a flag, either as a command or an environmental variable, the
> command is stop_on_error[severity]" ... "errors should derive from messaging."

## Why it fits the existing engine

The plumbing was already ~80% present:

- `emit_error(MessageId, code)` (`command_output.cpp`) renders localized text from
  the message catalog **and** records a canonical HRESULT-style code carrying a
  **severity** (`success/warning/error`, `xbase_error_codes.hpp`) via
  `set_last_error`. Its comment names "(future) SET ERRORSTOP" as the consumer.
- `command_output.hpp:32` documents ERRORSTOP as the planned observer.
- The error state is thread-local (`xbase_error_context.hpp`), header-only.

So "errors derive from messaging" is honored structurally: the threshold is
compared against the severity carried by the messaging-recorded error code, never
an ad-hoc flag. Any command whose failure flows through `emit_error`/`set_last_error`
participates automatically.

## Design

A session threshold `errorstop in {OFF, WARNING, ERROR}` (default **OFF** =
legacy behavior). A running DotScript aborts when a **new** last-error at or above
the threshold is recorded on a line. "New" is detected with an **error generation
counter** (bumped by `set_last_error`) so the sticky thread-local last-error can't
false-trip a later line.

Surface (all three, as chosen):

- **Command:** `STOP_ON_ERROR [OFF|WARNING|ERROR]` (native, `dotref`). No arg
  reports the current threshold; `USAGE` prints help.
- **SET alias:** `SET ERRORSTOP [TO] OFF|WARNING|ERROR` (compatibility form, via
  the existing SET router).
- **Environment default:** `DOTTALK_ERRORSTOP=OFF|WARNING|ERROR` (also accepts
  NONE/WARN/FATAL and numeric 0/1/2), seeded once at first access; the command/SET
  override it at runtime.

## Files changed (dev, D:\code\ccode)

| Area | File | Note |
| --- | --- | --- |
| State + policy | `include/xbase_error_context.hpp` | `errorstop_level`, generation counter, `set/get_errorstop`, `errorstop_tripped`, `parse_errorstop_level`, env seed; `set_last_error` now bumps the generation |
| Command (NEW) | `src/cli/cmd_stop_on_error.cpp` | `STOP_ON_ERROR` handler + `@dottalk.usage` block |
| Registration | `src/cli/shell_commands.hpp`, `src/cli/shell_commands.cpp` | declare + `registry().add("STOP_ON_ERROR", ...)` |
| SET alias | `src/cli/cmd_set.cpp` | `SET ERRORSTOP [TO] <sev>` branch |
| Abort hook (script) | `src/cli/init_script_runner.cpp` | `run_script_file`: capture generation, trip check after each line, break |
| Abort hook (DOTSCRIPT) | `src/cli/cmd_dotscript.cpp` | same in the DOTSCRIPT loop |
| Native reference | `include/dotref.hpp` | STOP_ON_ERROR entry |
| Regression proof | `dottalkpp/data/scripts/errorstop/stop_on_error_regression.dts` | self-contained |

REGRESSION (the compiled-spec runner) iterates built-in specs, not a line loop, so
it needs no hook; scripts it drives through the two loops above are covered.

## Proof (to run on the maintainer's MSVC build)

`DOTSCRIPT dottalkpp/data/scripts/errorstop/stop_on_error_regression.dts`
(or `--script`). Expected:

- `STOP_ON_ERROR-REGRESSION-BEGIN` prints.
- Phase 1 (OFF): the invalid-severity error is recorded but **does not** abort ->
  `PASS-1-OFF-CONTINUED-PAST-ERROR` prints.
- Phase 2 (ERROR): the invalid-severity error **aborts** the run -> a
  `stopped (STOP_ON_ERROR ERROR)` line prints and **neither** `FAIL-2` **nor**
  `FAIL-3` print.

## Honesty / open items

- **Not built here.** This sandbox has no MSVC; the code is complete but the
  build + regression run is the maintainer's step (as with every engine change
  this session). Highest first-build attention: the two loop edits and the SET
  router branch.
- **Messaging follow-up.** To avoid breaking the validated, locale-complete
  message catalog blind, the STOP_ON_ERROR/SET ERRORSTOP *status* lines use
  `print_info` rather than new localized `MessageId`s. The **severity decision**
  already derives from messaging (the recorded error code). A fast-follow should
  add dedicated localized `MessageId`s (STOP_ON_ERROR set/status/invalid, the
  script "stopped" notice, an ERROR_STATUS threshold line) and run CMDHELPCHK.
- **Scope.** Threshold is thread-local (matches the existing thread-local
  last-error); interactive shell is unaffected (only the script loops abort).
- **Follow-on:** an `ERROR_STATUS` line reporting the current threshold (deferred
  with the messaging follow-up).

## Provenance pointers

- Error/severity: `include/xbase_error_codes.hpp`, `include/xbase_error_context.hpp`.
- Messaging path: `src/cli/command_output.{hpp,cpp}` (`emit_error`).
- Related gate: SET ERRORSTOP (AIF-018/AIF-021 messaging normalization).
- Consumer context: the DotScript-array spec review
  (`.../outputs/DOTSCRIPT_ARRAYS_SPEC_REVIEW_2026-07-20.md`, finding H3).
