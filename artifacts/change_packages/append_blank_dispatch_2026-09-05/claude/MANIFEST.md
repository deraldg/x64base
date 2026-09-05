---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260905-CLAUDE-001
  recorded_at_utc: 2026-09-05T13:21:35Z
  agent:
    provider: Anthropic
    product: Claude (Cowork)
    model: claude-opus-5
    access_mode: local_write
  session:
    id: session_01XMzP8acDeeY3kCxDyQ7FHV
    chat_reference: cowork-task:session_01XMzP8acDeeY3kCxDyQ7FHV
  project:
    id: project.x64base.runtime
    root: D:/code/ccode
  git:
    branch: development
    baseline_commit: 4aac03540529f66ba8c682a4c9bdfdc6491cbd5d
  authorization:
    requested_by: member.derald
    scope: >-
      Package the APPEND BLANK dispatch repair for review. No mutation of
      src/cli in the working tree; the proposal is the deliverable.
  report:
    path: artifacts/change_packages/append_blank_dispatch_2026-09-05/claude/MANIFEST.md
    kind: change_package
---

# APPEND BLANK dispatch -- change package

## STATUS: APPLIED TO THE WORKING TREE, ON AN EXPLICIT GO.

Superseded state, left standing because it was true when written: this began as a
proposal and said "NOTHING IN `src/cli` HAS BEEN MODIFIED." On 2026-09-05 the
maintainer ruled "take it over and make append blank work for us", which is the
explicit go `src/cli/**` requires. The patch is applied; the three sha256 values
below are the BASELINE they were applied to, not the current file state.

## MERGED WITH A SECOND, INDEPENDENT REVIEW

Grok reviewed the public snapshot (`github.com/deraldg/x64base` at `main`, which
is `C:\x64base` HEAD `9470a50d9`, 2026-08-21) and returned its report while this
package was being written. **Same diagnosis, arrived at independently.** Three
things came out of the comparison and all three are in the code:

1. **Grok named the user, and that framing is better than mine.** "Students type
   `APPEND BLANK`." The two-word form is the FoxPro spelling; this is a
   compatibility defect, not only a routing defect.
2. **Grok's criticism of this package's seam was correct as stated** -- "
   `cmd_APPEND_BLANK` only helps if the dispatcher sends the two-word form
   there" -- and it forced a measurement instead of an argument. Result below.
   The seam holds; the criticism is why it is now known to hold rather than
   assumed to.
3. **Grok specified a behaviour this package was missing and it has been
   adopted**: extra words after `BLANK` must print usage. Measured:
   `dottalk_append_blank_core` takes its `istringstream` UNNAMED and reads
   nothing, so `APPEND BLANK GARBAGE` would have appended and dropped GARBAGE
   silently -- the same silently-swallowed-token defect the whole repair is
   about. Hunk 4 is Grok's, and is attributed in the source.

**Where the two proposals differ, and why this seam was kept.** Grok proposed
teaching `cmd_APPEND` to accept `BLANK`. Measured, not argued:

```
preprocess_for_dispatch is called from exactly two places --
  shell_api.cpp:295  shell_dispatch()        <- the interactive prompt
  shell_api.cpp:319  shell_execute_line()    <- DOTSCRIPT

and cmd_dotscript.cpp:615 is what DOTSCRIPT runs each line through, while
run_regression_script() executes a .dts spec by calling cmd_DOTSCRIPT.
```

So **every path a human or a spec can take reaches the preprocessor**: the
prompt, DOTSCRIPT, and every `.dts` regression spec. The only way to reach
`cmd_APPEND` without it is a direct C++ call, and there is exactly one --
`cmd_browsetui.cpp:746`, which **Grok's fix would not have repaired either**,
because that call site hands the stream over at position ZERO, so `cmd_APPEND`'s
first token is `APPEND` and never `BLANK`. Neither proposal fixed F5 by itself.
It needs its own hunk, which is hunk 3.

Grok's closing question -- "say whether it failed on an empty table, RAM/memo
table, index, or memo field" -- is answered: **a freshly created empty VFP
table**, and the table had nothing to do with it. The failure is entirely in
dispatch and reproduces on any open table.

Verified at package time, BEFORE the patch was applied:

```
git ls-files -m src/cli/shell_api_extras.cpp src/cli/cmd_browsetui.cpp \
                src/cli/cmd_append_blank.cpp
  -> empty (all clean)

on-disk sha256
  65fab194fd6d2715f6bfb9fbaa2aea687004271de23b4ab94edbd175c156574d  shell_api_extras.cpp
  6bac62dc1d97677d1206ffdd28f4d844b6ee793776948afa30642365d481284f  cmd_browsetui.cpp
  e94132c0572cab5df644dd34b98ecb872125c792fb5aabf67274740ef19f74b4  cmd_append_blank.cpp
```

## FOUR HONEST DISCLOSURES, UP FRONT

1. **NOTHING HAS BEEN COMPILED YET.** The patch is in the tree; no build has
   run against it. Every correctness claim below is from reading source, and is
   labelled as such. `ctest`/`REGRESSION ALL` are the next gate.
2. **THE F5 CLAIM IS INSPECTION, NOT MEASUREMENT.** The BROWSE TUI was never
   run. See TEST_PLAN.md.
3. **THIS PACKAGE SITS OUTSIDE BOTH AUDITED LANDING ZONES.** The path was named
   by the maintainer. `labtalk/registries/ai_report_audit.yaml` scans
   `docs/maintenance/SESSION_CLOSEOUT_*.md` and
   `docs/maintenance/external_ai_intake/**/*.md`; `artifacts/change_packages/`
   matches neither, so **`audit_trail.py` will not see this envelope and will not
   validate it.** The envelope is written to contract shape anyway; it is
   unvalidated, and saying so is the point. If the steward wants it enforced, the
   canonical zone is
   `docs/maintenance/external_ai_intake/append-blank-dispatch_2026-09-05/`.
4. **`EXTERNAL_AI_CHANGE_PACKAGE_V1.md` IS NOT QUITE THIS CONTRACT.** It governs
   *outside* AI reviewing the *public snapshot* and returning a proposal. This
   session works inside `D:\code\ccode` with local write. The layout and the
   honesty rules are followed because they are the right ones; the framing
   ("could not read the repository", "public baseline older than development")
   does not apply and is not claimed.

## Objective

Make `APPEND BLANK` do what every document in the tree says it does, and repair
the one caller that already depended on it.

## Baseline

Repository: `D:\code\ccode` (authoritative development tree)
Branch: `development`
Baseline commit: `4aac03540529f66ba8c682a4c9bdfdc6491cbd5d`

**The baseline is HEAD, and HEAD is one commit behind this session's other
work.** The AIF-091 M2 CREATE commit was handed to the steward and has not
landed as of package time. It touches none of these three files, so the patch is
independent of whether it lands; but a reviewer comparing SHAs should know.

## Owning lifecycle and lane

- Subsystem: `cli`
- SDLC lane: `cli` (per `labtalk/registries/projects.yaml`,
  `project.x64base.runtime`)
- Truth state: **defect confirmed by measurement** (a runtime transcript, twice)
- Proof state: **repair UNPROVEN** -- not compiled, not run
- Risk class: **low-medium**. Adds one rewrite rule to a preprocessor that
  already holds two, and changes one TUI key handler that does not currently
  work.
- Next gate: build, then the runtime check in TEST_PLAN.md, then
  `REGRESSION ALL`.

## The defect

`src/cli/shell_commands.cpp:242` registers exactly one name:

```cpp
registry().add("APPEND_BLANK", ...);   // underscore, and it is the only spelling
```

`shell_dispatch()` reads the first whitespace token as the verb
(`std::istringstream tok(line); tok >> cmd;`) and hands the command the stream
**positioned after that token**. So `APPEND BLANK` dispatches to `cmd_APPEND`
with `BLANK` as its first argument. `BLANK` is not a count, not `RAW`, not
`MANY`, so `cmd_APPEND` falls through to `print_append_usage()` and returns
having appended nothing.

**The failure mode is a silent no-op that prints something helpful-looking** --
loud enough to read as output, quiet enough not to read as an error. Downstream,
every `REPLACE` answers `REPLACE: no current record` and the table is left empty.

Measured twice, on two different days, by two different consumers:

- the WSLADDER regression fixture, where it produced two RED arms against a verb
  that had behaved perfectly (recorded in that spec's entry in
  `src/cli/cmd_regression.cpp`) -- and which would have been a FALSE GREEN
  instead if the unwritten field had happened to compare equal;
- 2026-09-05, populating the AIF-091 M2 acceptance fixture, from a handover
  written by an author who had read the WSLADDER warning.

## Why the warning did not prevent the repeat

`src/cli/cmd_append_blank.cpp`'s own `@dottalk.usage` block says:

```
//   APPEND BLANK is the friendly command spelling when routed by the dispatcher.
```

**The conditional clause is doing quiet work: the condition is false.** A reader
who checks the usage block before typing the command gets a wrong answer from the
most authoritative-looking place available. A warning filed somewhere true does
not outrank a falsehood filed somewhere obvious. That is why hunk 3 exists, and
why it is not optional cleanup.

## Changed files

| file | hunks | what |
|---|---|---|
| `src/cli/shell_api_extras.cpp` | 1 | route `APPEND BLANK` -> `APPEND_BLANK` |
| `src/cli/cmd_browsetui.cpp` | 2 | F5 calls the right function with a correctly positioned stream |
| `src/cli/cmd_append_blank.cpp` | 2 | usage block states the mechanism instead of asserting a false conditional; **and an unrecognized trailing word is refused rather than ignored (Grok's arm)** |

Added files: none. Deleted files: none. Binaries: none.

## Why the fix is in `preprocess_for_dispatch`

`cli::preprocess_for_dispatch` already exists to rewrite multi-word command
spellings into registered single-token verbs, and already carries two rules
(`SET RELATIONS` -> `REL`, `RELATIONS` -> `REL`). `starts_with_tokens_ci()` is
already written, already case-insensitive, already boundary-correct, and already
preserves the argument tail. **This is the seam built for this job.**

The alternative -- teaching `cmd_APPEND` to recognise `BLANK` -- was rejected: it
would give the verb two implementations reachable by two names, and the next
person to change append semantics would have to find both. Rewriting the LINE
keeps one implementation (`cmd_APPEND_BLANK` -> `dottalk_append_blank_core`).

Traced by hand, not assumed:

- `APPEND BLANK` -> `"APPEND_BLANK "` -> `cmd_APPEND_BLANK` -> usage check sees
  `APPEND_BLANK`, which is not `USAGE`/`HELP`/`?` -> `dottalk_append_blank_core`.
- `APPEND BLANK USAGE` -> `"APPEND_BLANK USAGE"` -> the usage check strips the
  `APPEND_BLANK ` prefix -> `USAGE` -> usage printed. **The rewrite does not
  swallow the usage form.**
- `APPEND`, `APPEND 5`, `APPEND RAW`, `APPEND MANY 3`: `starts_with_tokens_ci`
  requires the literal second token `BLANK`, so none of them match and none of
  them change.

## The second, independent defect: F5

```cpp
// src/cli/cmd_browsetui.cpp:746, before
std::istringstream s("APPEND BLANK");
cmd_APPEND(area, s);
```

This call **bypasses the dispatcher**, so the stream sits at position zero and
`cmd_APPEND`'s first token is `APPEND` -- not a count, not `RAW`, not `MANY`.
Same fall-through, same silent no-op. **The route added in hunk 1 does not fix
this**, which is why hunk 2 is a separate repair and not a consequence of the
first.

**Stated as inspection. The TUI was not run.** Nothing tests F5; a green suite is
not evidence about it either way.

Noted for the reviewer and deliberately NOT changed: `case Key::F4` twelve lines
above uses the identical idiom with `cmd_DELETE` and works -- but only because
`cmd_DELETE` ignores positional arguments. **The idiom is unsafe, not correct**,
and a comment saying so is included at the F5 site. Auditing every direct
`cmd_*` call in the TUI for the same latent bug is out of scope here and is
recommended in NOTES.md.

## Mutation and compatibility effects

- No on-disk format change. No DBF, index, memo, catalog or schema change.
- No new command, no removed command, no changed command semantics. `APPEND` and
  `APPEND_BLANK` behave exactly as before for every input they already accepted.
- **Behaviour change, and it is the intended one:** `APPEND BLANK` stops printing
  usage and starts appending a record. Any script or fixture that has been
  silently appending nothing will begin appending. That is a correction, but it
  is a change in observable behaviour and a reviewer should treat it as one --
  a spec that passed while writing nothing may now write something.
- `APPEND_BLANK` is classified `mutates: table-data index memo record-pointer`.
  Reaching it from a spelling that previously no-opped means the mutation
  classification now applies where it previously did not fire.

## Contracts and annotations read

- `labtalk/ai_portal/EXTERNAL_AI_CHANGE_PACKAGE_V1.md`
- `labtalk/ai_portal/AI_REPORT_AUDIT_CONTRACT_V1.md`
- `labtalk/registries/ai_report_audit.yaml`, `labtalk/registries/projects.yaml`
- `@dottalk.usage` blocks in `cmd_append.cpp`, `cmd_append_blank.cpp`,
  `cmd_delete.cpp`, `cmd_close.cpp`
- the WSLADDER spec entry in `src/cli/cmd_regression.cpp`
- `src/cli/shell_api.cpp` (`shell_dispatch`, `shell_execute_line`),
  `src/cli/shell_commands.cpp`, `include/cli/append_support.hpp`

## Files intentionally excluded

- `src/cli/cmd_append.cpp` -- correct as written once the route exists.
- `src/cli/shell_commands.cpp` -- the registry is not the right seam; a
  two-word key cannot be looked up by a single-token verb read.
- Every other direct `cmd_*` call in `cmd_browsetui.cpp` -- same latent hazard,
  separate audit, recommended in NOTES.md rather than done here.
- A regression spec -- specs live in `src/cli/cmd_regression.cpp`, which is a
  larger surface than this repair, and no `src/tests` target links the CLI layer
  so a C++ unit test at this seam is not cheap. Specified in TEST_PLAN.md and
  explicitly NOT written.
- `tmp/cp_work/` -- the scratch copies the patch was generated from. Not part of
  the package.

## Unresolved questions for the steward

1. **Location.** `artifacts/change_packages/` is new; it exists nowhere else in
   the tree and matches no audited glob. Keep it, or move to
   `docs/maintenance/external_ai_intake/append-blank-dispatch_2026-09-05/` where
   `audit_trail.py --emit-index` will find it?
2. **`AIPR-20260905-CLAUDE-001`** is self-assigned. No claim tool exists for AIPR
   ids (unlike AIF and R); uniqueness was checked by hand against
   `labtalk/registries/ai_report_index.yaml` -- nine ids, none dated 20260905.
   If AIPR ids are the steward's act like OI numbers, this one needs reissuing.
3. **Does `APPEND BLANK` beginning to work require a WSLADDER re-run?** That
   fixture was rewritten to use bare `APPEND` after the first incident. It should
   be unaffected, but it is the one place in the tree known to have been bitten.
