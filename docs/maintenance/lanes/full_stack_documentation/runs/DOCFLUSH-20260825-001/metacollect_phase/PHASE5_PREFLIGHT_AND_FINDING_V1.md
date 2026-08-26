# v6 Phase 5 -- the collector is fresh, and reflecting on source found AIF-131 five more times

    Run    : DOCFLUSH-20260825-001, member.ai.claude.cowork for member.derald
    Phase  : 5, metadata candidates (Gate 5). Candidate-only; nothing imported.
    Status : review-needed. The `metacollect` RUN is owner-blocked (Windows exe).
             The finding below did not need it and is source-derived.

## 1. "Step 1 is really compile all of the programs first"

The owner's structural note on 2026-08-25 was that the fullstack push does not
begin with a harvest, it begins with a BUILD -- of everything the push will run.
Gate 0 already encodes that for `dottalkpp.exe` (`exe newer than catalogs`).
**Phase 5 runs a DIFFERENT program, and nothing was checking it.**

    build/Release/metacollect.exe        2026-08-25 12:59
      src/tools/metacollect_main.cpp     2026-08-05 20:56
      src/meta/metacollect.cpp           2026-07-26 01:31
      include/dt/meta/metacollect.hpp    2026-07-26 01:31
    DOTTALK_BUILD_METACOLLECT:BOOL=ON    (build/CMakeCache.txt)

The collector is newer than all three of its sources, so it is fresh and the run
below is safe to take. **That check should be a Gate 0 line, not a paragraph
here** -- it is `exe newer than catalogs` applied to the second program in the
stack, and it is the owner's insight stated as a gate. Filed for v7.

`metacollect` reads `src/` at RUNTIME, so today's `90e5dce0b` needs no rebuild of
the collector -- only of `dottalkpp.exe`, which happened at 01:00.

## 2. The run, for the owner (Windows exe; not runnable from the sandbox)

```powershell
$mc  = 'D:\code\ccode\build\Release\metacollect.exe'
$out = 'D:\code\ccode\docs\maintenance\lanes\full_stack_documentation\runs\DOCFLUSH-20260825-001\metacollect_phase'
& $mc --source-root D:\code\ccode\src --include-dev-commands --sysargs-include-keywords `
      --syscmd-import-out  "$out\SYSCMD_IMPORT_candidate_v1.csv" `
      --sysfunc-import-out "$out\SYSFUNC_IMPORT_candidate_v1.csv" `
      --sysargs-import-out "$out\SYSARGS_IMPORT_candidate_v1.csv" `
      > "$out\metacollect_facts_v1.csv" 2> "$out\metacollect_stderr_v1.txt"
Get-Content "$out\metacollect_stderr_v1.txt"
```

**Prediction to check it against** (the resume-state rule: a run you cannot
predict is "run it and see"). `build_syscmd_seed_rows` starts from
`collect_static_registry_commands`, which is a regex over `src/**/*.cpp` --
reproducible without the exe. Re-derived on the current tree:

    .cpp files scanned            578
    registration SITES            253
    DISTINCT tokens               245
    tokens registered twice         8

SYSCMD rows are deduplicated by CANONICAL name after alias and compact folding,
so **245 is the upper bound, not the prediction.** The 2026-08-05 baseline was
226 with 461 registry commands; the tree now holds 462. A result far from ~226
means the fold changed, not that the tree grew.

The eight double registrations, named rather than counted -- this is the
`--print the distinct matched strings` rule, and the reason it exists is that
"253 registrations" and "245 commands" are both true and neither is the number
anyone wants:

    CASE             src/cli/shell_commands.cpp:611   src/edu/edu_case.cpp:202
    CODASYL          src/cli/cmd_codasyl.cpp:863      src/cli/shell_commands.cpp:608
    DELETE           src/cli/cmd_delete.cpp:478       src/cli/shell_commands.cpp:243
    ERASE            src/cli/cmd_erase.cpp:424        src/cli/shell_commands.cpp:366
    EXAMPLE          src/cli/shell_commands.cpp:505   src/cli/shell_commands.cpp:614
    EXPORTFUNCTIONS  src/cli/cmd_export_functions.cpp:337  src/cli/shell_commands.cpp:549
    RECALL           src/cli/cmd_recall.cpp:452       src/cli/shell_commands.cpp:244
    SQLHELP          src/cli/cmd_sql_help.cpp:209     src/cli/shell_commands.cpp:453

## 3. THE FINDING -- AIF-131 fixed one instance of a class that has five

`90e5dce0b` landed this morning on the reasoning that **`shell_dispatch` keys on
the FIRST TOKEN only**, so a registry key containing a space can never be
reached. Verified again here, on both executors:

    shell_api.cpp:296-306   tok >> cmd;  U = up(cmd);  registry().run(area, U, tok)
    shell_api.cpp:343-375   tok >> cmdToken; U = up(cmdToken); registry().run(...)
                            else -> MessageId::UnknownCommand {"command", cmdToken}

`preprocess_for_dispatch` is the only rewrite ahead of the lookup and it handles
exactly two forms (`SET RELATIONS ...` -> `REL ...`, `RELATIONS ...` -> `REL ...`).
Nothing joins two tokens into a key.

**Five multiword registrations remain.** They are not one finding; they are two,
and the difference is the whole point:

### 3a. Three that are DEAD AND UNSERVED -- the exact pre-fix `BUILD VECTORS` state

    src/cli/shell_commands.cpp:562   registry().add("ERROR CLEAR",  ...)
    src/cli/shell_commands.cpp:563   registry().add("ERROR STATUS", ...)
    src/cli/shell_commands.cpp:564   registry().add("ERROR TEST",   ...)

**There is no `registry().add("ERROR", ...)` anywhere in the tree.** No parent
reads the next token, and `preprocess_for_dispatch` does not rewrite `ERROR`.
Typing `ERROR CLEAR` looks up key `ERROR`, misses, and reports
`Unknown command: ERROR` -- character for character what `BUILD VECTORS`
answered before this morning.

The three underscore spellings at `:556-558` (`ERROR_CLEAR`, `ERROR_STATUS`,
`ERROR_TEST`) are single tokens and DO work. So the capability is reachable; the
spelling the help publishes is not.

**And the store publishes them as working.** `dottalkpp/data/help/COMMANDS.dbf`,
rebuilt 01:11 tonight:

    386 DOT ERROR CLEAR    implemented=yes  supported=yes
    387 DOT ERROR STATUS   implemented=yes  supported=yes
    388 DOT ERROR TEST     implemented=yes  supported=yes
    389 DOT ERROR_CLEAR    implemented=yes  supported=yes
    390 DOT ERROR_STATUS   implemented=yes  supported=yes
    391 DOT ERROR_TEST     implemented=yes  supported=yes

Three of those six rows are false in the same way, for the same reason, as the
two rows `90e5dce0b` corrected this morning. `IMPLEMENT` is answering "is there
a registration", while every reader takes it to mean "can this be typed".

### 3b. Two that are DEAD BUT SERVED -- inert duplicates, not defects

    src/cli/shell_commands.cpp:276   registry().add("SET UNIQUE",   ...)
    src/cli/shell_commands.cpp:331   registry().add("SET RELATION", ...)

Here the parent EXISTS -- `registry().add("SET", ...)` at `:275` -- and `cmd_SET`
reads its own next token and handles both (`cmd_set.cpp:1848` `UNIQUE`,
`cmd_set.cpp:1969` `RELATION`). That is precisely the mechanism the `90e5dce0b`
comment names when it says "SET works because SET itself is registered". So
these two spellings WORK; the multiword keys are simply unreachable duplicates of
a path that already functions.

They still cost something: they occupy registry slots, they emit SYSCMD and
store rows for keys that can never be typed, and they read to the next
maintainer as the pattern to copy -- which is how `ERROR CLEAR` and
`BUILD VECTORS` came to exist.

## 4. What is NOT claimed here

- **Not runtime-proven.** No `ERROR CLEAR` was typed at a prompt in this pass.
  The claim is source-evidenced, from the dispatcher and the registration sites
  named above. `BUILD VECTORS` WAS proven at runtime before `90e5dce0b` landed
  (`Unknown command: BUILD`), and the mechanism is identical, but a proven
  sibling is not a proof. The one-line settlement, for the owner:

      . ERROR STATUS
      expect: Unknown command: ERROR

  Written down so this item is QUEUED, not blocked.
- **No prescription is made.** Whether ERROR gets a router like BUILD, whether
  the three multiword registrations are deleted in favour of the underscore
  spellings, and whether the two SET duplicates are removed are three separate
  rulings for the owner of that area. Recording the defect is this lane's job.

## 5. Phase 5 status

    Collector freshness   PASS  (exe 2026-08-25 12:59 > newest source 2026-08-05 20:56)
    Candidate emit        OWNER-BLOCKED -- Windows exe, section 2 has the block
    Source reflection     DONE, and it produced section 3

Phase 5 does not close until the three candidate CSVs exist and Gate 5 binds
them by SHA. Section 3 does not depend on that and should not wait for it.

## Good Neighbor

    What changed  : one new document and one new directory in this run. No
                    source, no data, no store, no rebuild, no import.
    Whose area    : lane full_stack_documentation, run DOCFLUSH-20260825-001.
                    Section 3 concerns src/cli/shell_commands.cpp, which is
                    AIF-131's area -- reported, not edited.
    Authorization : the owner's standing instruction to run v6 to the end, and
                    the 2026-08-25 note that compiling every program is step 1.
    Verify        : section 1's four timestamps from `ls -la`.
                    section 2's counts: regex
                      (?:registry\s*\(\s*\)\s*\.\s*add|register_(?:extension_)?command)\s*\(\s*"([^"]+)"
                    over src/**/*.cpp with comments masked -- the same one at
                    src/meta/metacollect.cpp:806.
                    section 3: grep -n 'add("ERROR' src/cli/shell_commands.cpp
                      expect ERROR_CLEAR/STATUS/TEST at 556-558 and
                      ERROR CLEAR/STATUS/TEST at 562-564, and no add("ERROR",.
    Undo          : delete this document and the directory. Nothing cites them.
