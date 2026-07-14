# DotTalk++ Extension Exit Contract v1

Status: draft.

Kind: runtime | usage | safety | document-control

Evidence class: Source-defined first wave for registry protection and manifest
document control; Design-intended for runtime exits and external execution

Owner area: extension layer, CLI dispatcher, contract lane, SelfDoc

Related:

- `src/ext/ext_policy.hpp`
- `src/ext/cmd/cmd_student_hello.cpp`
- `src/ext/cmd/cmd_student_echo.cpp`
- `src/ext/fn/fn_student_text_autoreg.cpp`
- `src/cli/shell_api.cpp`
- `src/cli/shell.cpp`
- `src/cli/command_registry.cpp`
- `dottalkpp/user/exits/README.md`

## Purpose

DotTalk++ needs an ABAP-style extension model: the core owns stable named exit
points, while students and local users own code or artifacts outside the core
upgrade path.

The system must support C++ first, because that is the current source and
usage-contract mining lane. It must also allow non-C++ work to be stored,
reviewed, curated, and later executed through a narrow contract without
pretending that DotTalk++ can currently mine every language.

## Core Rule

Core commands and built-in functions are protected. Student and local extension
work enters through a named extension lane, a reviewed manifest, and stable exit
points. Non-C++ artifacts are document-controlled and curated first; they are
not mined for source truth until tooling for that language exists.

## Hardening Decision

We should harden this concept, but in phases.

The first hardened step is not dynamic execution. The first hardened step is a
stable boundary:

- reserved built-in command names cannot be overwritten by student code
- extension names use a custom namespace such as `Z_`, `Y_`, or `STU_`
- C++ student commands keep `@dottalk.usage` contracts where they define command
  behavior
- non-C++ artifacts are inventoried in a manifest and treated as curated
  document-control inputs

Only after that boundary is source-defined should runtime exits be enabled.

## Scope

In scope:

- C++ self-registering student commands and functions already under `src/ext`
- future protected exit points around command execution and shell lifecycle
- manifest-controlled process exits for Python, PowerShell, batch, JavaScript,
  or other languages
- document control for non-C++ extension artifacts
- future `EXITS` command documentation and usage contract

Out of scope for v1:

- mining non-C++ files for command usage or function semantics
- loading unreviewed scripts automatically
- allowing extensions to overwrite built-in command names
- exposing internal C++ classes as an unstable plugin ABI
- treating HELP/manual prose as implementation authority

## Extension Points

The first exit points should be small and stable:

| Exit point | Timing | May cancel command | Notes |
| --- | --- | --- | --- |
| `startup.after` | after core command/function registration and init | no | observe or register extension metadata |
| `shutdown.before` | before normal shutdown/autosave detach | no | cleanup only |
| `command.before` | after command parse, before handler execution | later phase | audit first, cancellation only after policy hardening |
| `command.after` | after handler returns | no | audit, teaching feedback, metrics |
| `command.error` | after handler error | no | report/log only |
| `command.unknown` | after unknown command resolution fails | later phase | can provide teaching hint or future fallback |
| `timer.after` | after timed command measurement | no | reuses existing timer information |

The safest first runtime behavior is observe-only. Command cancellation and
command replacement are useful, but they should require a separate hardening
gate because they change core behavior.

## Runtime Hook Location

The canonical command path today is:

1. shell/front-end input
2. `shell_execute_line`
3. macro and variable handling
4. `CommandRegistry::run` / `try_run`
5. registered handler

The exit manager should sit at this boundary:

- command identity and raw line are available
- shell, script, and UI callers converge
- timer and polling can stay outside or report into the same event stream
- registry protection remains centralized

## Manifest Shape

The controlled manifest should live under `dottalkpp/user/exits/exits.json`.

Example:

```json
{
  "api": 1,
  "status": "draft",
  "entries": [
    {
      "id": "Z_AUDIT_COMMAND",
      "point": "command.after",
      "kind": "process",
      "language": "python",
      "entry": "src/z_audit_command.py",
      "enabled": false,
      "timeout_ms": 500,
      "owner": "student-or-class",
      "state": "curated",
      "usage_contract": "manifest",
      "evidence": "manual-review"
    }
  ]
}
```

Required fields:

| Field | Meaning |
| --- | --- |
| `id` | stable custom id, normally `Z_*`, `Y_*`, or `STU_*` |
| `point` | one of the registered exit points |
| `kind` | `cpp-static`, `cpp-dll`, or `process` |
| `entry` | source, binary, or command path relative to `dottalkpp/user/exits` |
| `enabled` | default false for any executable artifact |
| `timeout_ms` | required for process exits |
| `owner` | class, student, maintainer, or local owner |
| `state` | intake, curated, tested, disabled, enabled-local, retired, rejected |
| `usage_contract` | `source`, `manifest`, `curated-doc`, or `none` |
| `evidence` | current proof class or review note |

## Process Exit Contract

For non-C++ languages, DotTalk++ should avoid language-specific embedding at
first. Use a process boundary:

- stdin receives UTF-8 JSON context
- stdout returns UTF-8 JSON result
- stderr is captured as diagnostic evidence
- a timeout kills the process
- failure disables or reports the exit without crashing DotTalk++

Command context example:

```json
{
  "api": 1,
  "point": "command.after",
  "command": "LIST",
  "raw_line": "LIST 10",
  "args": "10",
  "status": "ok",
  "elapsed_ms": 2.5,
  "area": {
    "open": true,
    "name": "students",
    "recno": 12
  }
}
```

Result example:

```json
{
  "action": "continue",
  "message": "audit recorded"
}
```

Allowed v1 actions:

| Action | Meaning |
| --- | --- |
| `continue` | no behavior change |
| `log` | append message to extension log |
| `warn` | display a warning and continue |

Deferred actions:

| Action | Reason deferred |
| --- | --- |
| `cancel` | changes command behavior |
| `replace-command` | changes command behavior and needs loop/recursion guard |
| `mutate-context` | needs a stable data access API |

## C++ Contract

C++ remains the first mined extension language.

Current C++ extension files may self-register commands and functions, but the
hardened rule should be:

- built-ins are registered only by the central shell/bootstrap path
- extension commands register through extension APIs or guarded registry calls
- extension command names must not collide with built-ins
- public command behavior must include `@dottalk.usage v1`
- source behavior and runtime `USAGE` output must agree
- metacollect may harvest these source contracts

Future DLL/shared-library support should use a small C ABI instead of exposing
internal C++ classes:

```cpp
extern "C" int dottalk_extension_init(DtHostApi* host);
```

The ABI must pass stable scalar data or JSON-shaped payloads. It should not pass
`DbArea`, `XBaseEngine`, C++ standard-library containers, or internal ownership
types across module boundaries in v1.

## Non-C++ Document-Control Contract

Non-C++ files are valid extension artifacts, but they are not source-mined in v1.

Examples:

- `.py`
- `.ps1`
- `.bat`
- `.cmd`
- `.js`
- `.ts`
- `.sql`
- `.dts`
- language-specific notebooks or teaching fragments

Process:

1. Intake into `dottalkpp/user/exits/inbox`.
2. Assign a manifest row with owner, id, language, state, and intended exit
   point.
3. Review for teaching purpose, safety, path behavior, and command-line
   invocation.
4. Move reviewed artifacts to `dottalkpp/user/exits/src`, `bin`, or `curated`.
5. Keep executable entries disabled until an explicit runtime enable step exists.
6. Record runtime proof separately when execution is later supported.

Authority rule:

- the manifest describes the artifact
- curated docs explain the artifact
- runtime proof proves the artifact
- the raw non-C++ code is stored evidence, not mined authority, until a language
  miner exists

## Current `EXITS` Usage Contract

The first runtime command is intentionally read-only. It gives the class a
visible document-control surface without enabling dynamic code loading,
external process execution, or manifest mutation.

```cpp
// @dottalk.usage v1
// owner: DOT|EXITS
// command: EXITS
// category: extension-control
// status: document-control-readonly
// noargs: list-summary
// effect: report
// mutates: none
// usage-access: EXITS USAGE; EXITS HELP; EXITS ?
// summary:
//   Inspect and validate the reviewed DotTalk++ extension-exit manifest.
//
// usage:
//   EXITS
//   EXITS USAGE
//   EXITS LIST
//   EXITS SHOW <id>
//   EXITS VALIDATE
//   EXITS WHERE
//
// examples:
//   EXITS LIST
//   EXITS SHOW Z_AUDIT_COMMAND
//   EXITS VALIDATE
//   EXITS WHERE
//
// notes:
//   This phase is read-only document control.
//   EXITS does not load DLLs, execute processes, enable exits, or disable exits.
//   Non-C++ extension artifacts are manifest-controlled and not source-mined in v1.
//
// risk:
//   mutates_manifest: no
//   executes_external_process: no
//
```

Reserved post-hardening commands:

- `EXITS ENABLE <id>`
- `EXITS DISABLE <id>`
- `EXITS TEST <id>`

Those commands must not be added until manifest parsing, explicit state changes,
timeouts, structured logs, reserved-name protection, and canary proof are in
place.

## Required Behavior

- Built-in command registration must remain protected.
- Student commands and exits must use custom names.
- Unknown or disabled exits must not affect command execution.
- Exit failure must not crash the shell.
- Process exits must have timeouts.
- External process execution must remain opt-in.
- Extension logs must preserve enough context to debug without leaking raw table
  data by default.
- Non-C++ artifacts must have manifest rows before they can be tested.

## Forbidden Behavior

- No silent overwrite of built-in command names.
- No auto-execution of files from `inbox`.
- No automatic trust of non-C++ source comments as usage contracts.
- No generated HELP/manual page may claim runtime support before canaries prove
  it.
- No dynamic extension may receive unrestricted internal engine pointers in v1.

## Hardening Phases

| Phase | Evidence target | Work |
| --- | --- | --- |
| 0 | Design-intended | contract doc, source policy annotation, user/exits README |
| 1 | Source-defined | guarded command registry, reserved-name checks, manifest parser |
| 2 | Runtime-proven | observe-only exit manager with startup/command.after/timer.after canaries |
| 3 | Runtime-proven + safety | process runner with JSON stdin/stdout, timeout, logs, disabled by default |
| 4 | Source-defined ABI | optional C ABI for DLL/shared-library extensions |
| 5 | Metadata-staged | `SYSEXIT` or equivalent metadata table |
| 6 | HELP-documented | `EXITS` command and CMDHELPCHK alignment |
| 7 | Publication-ready | manualgen/SelfDoc page cites source, manifest, and runtime proof |

## Evidence

Current proof:

- source: `src/ext/ext_policy.hpp` declares the student extension boundary
- source: `include/cli/command_registry.hpp` and `src/cli/command_registry.cpp`
  track command origins and prevent protected core commands from being
  overwritten by extension registration
- source: `src/cli/extension_manifest.*` parses and validates
  `dottalkpp/user/exits/exits.json`
- source: `src/cli/cmd_exits.cpp` exposes read-only `EXITS` manifest inspection
- source examples: `src/ext/cmd/cmd_student_hello.cpp`,
  `src/ext/cmd/cmd_student_echo.cpp`, `src/ext/fn/fn_student_text_autoreg.cpp`
- runtime: existing student commands/functions compile through the current
  source glob when included in the build
- docs: this contract, `dottalkpp/user/exits/README.md`, and
  `dottalkpp/user/exits/exits.json`

Current evidence class:

- Source-defined first wave for registry protection and manifest document
  control
- Design-intended for runtime exits, process execution, DLL loading,
  cancellation, and replacement

## Drift Risks

- Student examples self-register before registry protection is hardened.
- Non-C++ artifacts may accumulate without manifest rows.
- Generated docs may imply execution support before the runtime exists.
- Process exits may become a security hole if enabled before timeout and path
  controls are in place.
- Command cancellation may create confusing behavior if enabled before audit-only
  behavior is proven.

## Review Triggers

Review this contract when:

- adding `ExitManager` or equivalent runtime code
- changing `CommandRegistry::add` or `register_command`
- adding a dynamic loader or external process runner
- adding `EXITS`, `EXTENSIONS`, or similar CLI commands
- adding non-C++ student extension samples
- teaching material asks students to run extension code
- metacollect starts mining a non-C++ language

## Deferred

- `SYSEXIT` table schema
- signed or checksummed extension packages
- per-class sandbox policies
- richer data access API for extensions
- cancellation/replacement actions
- language-specific miners
