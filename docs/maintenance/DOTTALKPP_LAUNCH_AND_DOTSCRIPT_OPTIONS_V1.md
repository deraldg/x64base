---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260826-COWORK-010
  recorded_at_utc: 2026-08-26T22:20:00Z
  agent:
    provider: Anthropic
    product: Claude (Cowork)
    model: claude-opus-5
    access_mode: local_write
  session:
    id: COWORK-20260826-002
    chat_reference: not_exposed
  project:
    id: project.x64base.runtime
    root: D:/code/ccode
  git:
    branch: development
    baseline_commit: 372c5834f
  authorization:
    requested_by: maintainer (member.derald), in-session, "validate this is all true and make sure it is in the ai portal and easily found"
    scope: >
      Validate a hosted-session write-up of dottalkpp launch options and the
      DOTSCRIPT in-shell runner against source, then land it where recall can
      route to it. Source read only; no behaviour changed.
  report:
    path: docs/maintenance/DOTTALKPP_LAUNCH_AND_DOTSCRIPT_OPTIONS_V1.md
    kind: validated-reference
---

# dottalkpp launch options and DOTSCRIPT -- validated reference

Status: validated against source, review-needed. Owner: member.derald.
Author: member.ai.claude.cowork. Run: COWORK-20260826-002. Baseline: `372c5834f`.

Origin: a hosted-session write-up, checked line by line against the tree rather
than accepted. Every claim about launch, exit codes, resolution, comments,
nesting and error handling **held**. Two corrections, both about `OUT`:

1. It gets the transcript form MORE right than the `@dottalk.usage` block does
   (section 5) -- the form ships and that block omits it.
2. Its description of what `OUT` captures repeats the source's own wrong claim
   (section 3). `OUT` is not a proof capture. `SET ALTERNATE` is.

**How correction 2 was missed, and it is worth naming.** The first draft of this
file validated the note against the source contract and passed it, because the
contract says what the note said. The contract is known-wrong and has been since
2026-07-31 (AIF-081). Reading the implementation's own comment is not
verification when the defect IS the comment -- the measured behaviour is the
authority, and it lived one `recall.py capture_proof` away the whole time.

Evidence tier: **source-evidenced**. Read from `src/cli/main.cpp` and
`src/cli/cmd_dotscript.cpp` at `372c5834f`. NOT runtime-proven -- no exit code in
this file was observed from a process. Anyone who runs them should upgrade the
tier and say so.

## 0. Two things that are not the same

    dottalkpp --script <file>     an ARGV option. Redirects stdin. Not DOTSCRIPT.
    DOTSCRIPT <file>              an IN-SHELL command with its own resolver.

Confusing them is the point of this document. `--script` has no resolver, no
TRACE, no transcript, and no comment handling of its own -- it points `std::cin`
at a file and runs the ordinary interactive shell, which is why prompts still
print.

## 1. Which files exist

| Claim | Verdict |
| --- | --- |
| The runner is `src/cli/cmd_dotscript.cpp`, command `DOTSCRIPT` | TRUE |
| `cmd_dotscriptpp.cpp` is not on public `development` | TRUE |
| ...and the caveat "if the private tree has one" | RESOLVED: **it does not.** `find src -name 'cmd_dotscript*'` returns exactly one file |
| File headers name paths that do not exist | TRUE, both |

The stale headers, verbatim:

    src/cli/cmd_dotscript.cpp:10   // src/commands/cmd_dotscript.cpp
    src/cli/main.cpp:11            // File: src/main.cpp

Neither `src/commands/` nor `src/main.cpp` exists. The real paths are under
`src/cli/`. Cosmetic, but it is the kind of thing an agent greps for and fails
to find, so it is recorded rather than fixed silently.

## 2. Process -- `src/cli/main.cpp`

`main()` does `dottalk::init_utf8()` (before any console output, deliberately),
then `run_with_optional_script(argc, argv)`, which ends in `run_shell()`.

| Launch | Behaviour | Source |
| --- | --- | --- |
| `dottalkpp` | interactive stdin; `argc < 2`, straight to `run_shell()` | `main.cpp:218-221` |
| `dottalkpp --help` / `-h` / `/?` | usage on **stderr**, `return 0` | `main.cpp:186-190` |
| `dottalkpp --script <file>` | opens the file, `cin.rdbuf(script.rdbuf())`, then the same shell | `main.cpp:192-213` |
| `dottalkpp < file.dts` | OS redirect; never reaches argv parsing | not parsed |
| anything else as `argv[1]` | `Error: unknown option:` + usage, `return 2` | `main.cpp:214-218` |

Exit codes, all read from source:

| Condition | Exit |
| --- | --- |
| `--script` with no path (`argc < 3`) | 2 |
| `--script <file>` that cannot be opened | 2 |
| unknown `argv[1]` | 2 |
| `--help` / `-h` / `/?` | 0 |
| uncaught exception (both `catch` arms) | 1 |

`argv[3]` and beyond are never read. There is no mechanism to pass arguments to
a script this way.

The redirect is guarded: `CinRedirectGuard` restores `std::cin` in its
destructor, so the shell is not left pointing at a closed file.

## 3. In-shell -- `DOTSCRIPT`

Forms, from the file's own contract blocks:

    DOTSCRIPT USAGE
    DOTSCRIPT <file>
    DOTSCRIPT @<file>
    DOTSCRIPT TRACE
    DOTSCRIPT TRACE ON|OFF
    DOTSCRIPT TRACE <file>            -- one run only, global state unchanged
    DOTSCRIPT TRACE ON|OFF <file>
    DOTSCRIPT <file> OUT|OUTPUT <transcript> [APPEND]

Resolution of a bare name, in order (`cmd_dotscript.cpp:292-304`):

    1. the typed name
    2. <typed>.dts            (if no extension)
    3. scripts/<typed>(.dts)  (if no parent path)
    4. tests/<typed>(.dts)    (if no parent path)

`@file` notation is accepted and unquoted before resolution.

Comments and blanks: a line is skipped when, after trimming, it begins with
`*`, `//`, `&&` or `;`. The predicate delegates to
`dottalk::lexing::is_comment_or_blank` (`cmd_dotscript.cpp:159-161`) -- one
shared authority, not a private copy, which is the right shape.

`;` continuation is handled by `read_script_command` from `script_reader.hpp`,
**the same reader the interactive shell uses**, so a continued command behaves
identically in both (`cmd_dotscript.cpp:551-553`).

Nesting: `g_dotscript_depth` is `thread_local`; at `>= 2` the run refuses with
`DOTSCRIPT: nesting limit reached (max 1 subscript).` (`:490-492`). Main plus one
subscript, as documented.

Error handling per line (`:560-578`):

- comment/blank -> skipped
- unknown command -> reported as `<file>:<n>: Unknown command: <line>`, and the
  file **continues**
- after every line, `xbase::error::errorstop_tripped(err_gen0)` is checked; if
  the line tripped the `STOP_ON_ERROR` threshold the run stops and says so,
  naming the level

So an unknown command does not by itself end the run. Only a `STOP_ON_ERROR`
trip does.

Transcript: `OUT`/`OUTPUT` writes to a file while leaving console output
visible. Default truncates; `APPEND` appends (`:401-403`, parsing at
`:226-275`).

**DO NOT USE IT TO CAPTURE PROOF, AND DO NOT BELIEVE ITS OWN CONTRACT LINE.**
The source says it "captures full command output emitted through `std::cout`".
That is true and misleading: the engine's user-facing output goes through
`cli::cmdout`, NOT bare `std::cout`, and `OUT` drops all of it. Measured
2026-07-31, same script and same binary: **`DOTSCRIPT OUT` 42 lines,
`SET ALTERNATE` 89.** `SET ALTERNATE` is a strict superset.

    capture proof with:   SET ALTERNATE TO <file>  /  SET ALTERNATE ON
    never with:           DOTSCRIPT <file> OUT <transcript>

Authority: `AI_README.md`, Runtime Start Points. The defect is **AIF-081,
unfixed** -- the DOTSCRIPT help text still claims otherwise.

There is no `PARAMETERS` clause and no argument passing. The only trailing
tokens the parser accepts are `TRACE`, `OUT`/`OUTPUT` and `APPEND`. Stated as an
absence, which is weaker evidence than a presence: it is what the parser reads,
not a proof that nothing else is reachable.

## 4. Combining them

    dottalkpp --script driver.dts

where `driver.dts` contains `DOTSCRIPT workspace_multi_regression`, and ends:

    WORKSPACE CLOSE ALL
    QUIT

`WORKSPACE CLOSE ALL` at session end is the right temporary bound while
multi-workspace work is in flight (owner, 2026-08-26). Bare `CLOSE` is scoped to
the current workspace since AIF-078 stage 3; `CLOSE ALL` is the everywhere form
and the only one that also reconciles unregistered areas.

Note the interaction with a limit that is real and not a defect in your script:
a workspace NAME cannot be reclaimed within a session, so a `.dts` that declares
workspaces is idempotent per PROCESS, not per session. `datarun.ps1` starts a
fresh process each run, which is why it does not bite there.

## 5. THE FINDING -- a file can carry SEVERAL usage blocks, and readers took one

**Corrected 2026-08-26.** The first draft of this section said the OUT form
lived in a different vocabulary (`@dottalk.contract`) from the one CMDHELP
mines. That was wrong, and the maintainer pasting the file is what exposed it.

`cmd_dotscript.cpp` carries **two `@dottalk.usage v1` blocks**:

    :13    category: script       status: supported     -- 12 forms, no OUT
    :390   category: transcript   status: supplemental  -- the OUT/APPEND forms

The second is nested inside a `@dottalk.contract DOTSCRIPT TRANSCRIPT v1`
wrapper, which is what made it look like a different vocabulary. It is not. It
is a second, properly-formed usage contract with its own `command:`, `category:`
and a `status:` value -- `supplemental` -- that appears nowhere else.

**The defect is in the READERS, not the file.** `tools/selfdoc/audit_contracts.py`
bounded exactly one block and stopped. Measured across the tree: **20+ command
files carry two or more usage blocks** (`cmd_aggs.cpp` has five, one each for
SUM/AVG/MIN/MAX), and **18 command declarations sat in non-first blocks,
entirely unchecked** -- among them `TRANSACTION` in `cmd_transaction.cpp` block
2, which is genuinely absent from dotref.

Fixed the same day: `usage_blocks()` (plural) now reads every block, and the
dotref check iterates all of them. The helper-status check still reads the FIRST
block deliberately -- a file's exemption belongs to its primary contract, not to
a supplemental one. Post-fix the unregistered count stayed at 1, which is the
right outcome: the other 17 were registered all along, so the fix surfaced truth
rather than manufacturing findings.

This is the fourth bug of the same family in that one function, and the
instructive part is that the three previous fixes each narrowed the window
without asking whether the window should be singular at all.

Lane: **AIF-129, `contract-subblock-vocabularies-uncontrolled`** -- the name
fits better than it did before. `status: supplemental` is exactly an
uncontrolled subblock vocabulary.

### 5a. The runtime usage text has the same gap, differently

`print_usage()` (`:349-362`) lists nine syntax forms and **none of them shows
OUT**. It then says, in Notes:

    - OUT/OUTPUT tees full command output to a transcript file.

So a user running `DOTSCRIPT USAGE` learns the capability exists but is never
shown how to type it -- and the sentence they are shown is the AIF-081 claim
that section 3 records as false. Both belong in the same fix.

## 6. What is NOT claimed here

- No exit code was observed from a running process. All of section 2 is read
  from source.
- The absence of a `PARAMETERS` feature is argued from what the parser accepts.
- Behaviour under `dottalkpp < file.dts` is inferred from the absence of argv
  handling, which is sound but is still an inference.
