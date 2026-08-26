# v6 Phase 5 -- the collector is fresh, and reflecting on source found AIF-131 five more times

    Run    : DOCFLUSH-20260825-001, member.ai.claude.cowork for member.derald
    Phase  : 5, metadata candidates (Gate 5). Candidate-only; nothing imported.
    Status : review-needed. **CORRECTED 2026-08-26 -- see section 0.** The
             first version of this document called the metacollect RUN
             "owner-blocked". It was not blocked. It has now been RUN, in the
             sandbox, and section 7 carries the results.

## 0. CORRECTION -- I called it blocked without trying it

The first version of this document said the metacollect run was OWNER-BLOCKED
because metacollect is a Windows exe. That reason is true and the conclusion did
not follow. `DOCFLUSH_V6_GATE.md` method note 3 says it in as many words:

> An item is "blocked" only when someone has tried it and been stopped. Two of
> five blockers in the 2026-08-24 triage had been answerable for three passes
> and never attempted. Before carrying one forward, write down the command that
> would settle it; if it can be written, the item is QUEUED, not blocked.

I wrote the command down -- section 2 -- and then filed the item as blocked
anyway. `AIF-130` / `FINDING_SANDBOX_COMPILES_AND_DOTREF_AB.md` had already
settled the general question in this lane's favour: **the sandbox compiles.**
The same document records its author introducing a fifth false claim while
correcting four; this is the same lane making the same shape of error one day
later, and it is mine.

What it actually took, measured: the `dt_meta` target in `CMakeLists.txt:771` is
fully enumerated -- 11 translation units plus `metacollect_main.cpp`, two include
directories, `cxx_std_17`. No CMake needed. g++ 11.4 on the sandbox, `-O0`,
`-j4`, **built in under forty seconds**, and the binary ran the full source scan
in one call. The cost of "blocked" was one Makefile.

**The lesson generalises past this item.** "It is a Windows exe" is a fact about
a FILE, not about a QUESTION. The question was "what does metacollect emit from
this tree", and the tree is portable C++ that the repository's own CI already
builds on Ubuntu.

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

**Prediction, written BEFORE the run** (the resume-state rule: a run you cannot
predict is "run it and see"). Section 7 scores it. `build_syscmd_seed_rows` starts from
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
    Candidate emit        DONE  -- section 7. Three CSVs written, exit 0.
    Source-vs-live compare DONE -- section 7.3
    Source reflection     DONE, and it produced section 3

Phase 5's candidate CSVs now exist. **Gate 5 binding them by SHA is the owner's,
and is the only part of Phase 5 that was ever actually his** -- a candidate emit
is not an authorization.

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

---

# 7. THE RUN -- added 2026-08-26 after section 0's correction

## 7.1 How it was built and run

    CMakeLists.txt:771  dt_meta  -- 11 TUs, enumerated, cxx_std_17
    CMakeLists.txt:832  metacollect -- src/tools/metacollect_main.cpp

    g++ 11.4 (Ubuntu 22.04), -std=c++17 -O0, -I include -I src/cli/expr, -j4
    12 objects + link                                    < 40 seconds
    binary in /tmp, NOT in the repo; no CMakeCache, no build artifact written

    metacollect --source-root <repo>/src --include-dev-commands \
                --sysargs-include-keywords --syscmd/sysfunc/sysargs-import-out ...
    exit 0
      METACOLLECT syscmd export:   229 row(s)
      METACOLLECT sysfunc export:   75 row(s)
      METACOLLECT sysargs export: 1066 row(s)

Outputs are in this directory and are gitignored by `.gitignore:342`
(`docs/maintenance/lanes/**/runs/**/*.csv`), which is the contract the
METACOLLECT runbook already states: candidates stay out of the tree.

## 7.2 The prediction, scored

    predicted   SYSCMD "close to the 2026-08-05 baseline of 226; 245 distinct
                registration tokens is an UPPER bound, since SYSCMD folds
                aliases. A result far from ~226 means the fold changed."
    actual      229          -- +3 on the baseline, 16 under the upper bound

    baseline    SYSFUNC  74           actual  75    (+1)
    baseline    SYSARGS 959           actual 1066   (+107)

The SYSCMD prediction held. **The SYSARGS move is +11% and is NOT explained
here** -- `--sysargs-include-keywords` was passed on both runs, so the widening
flag is not the difference. Recorded as a measurement with an open cause rather
than rounded off; it is the kind of gap that becomes folklore if it is left
unnamed.

## 7.3 Source vs live metadata

    metacollect --compare --metadata-root dottalkpp/data/metadata
    exit 0, 192 issue(s), all severity WARN

      189  METADATA_ONLY  command    live SYSCMD row with no source-catalog fact
        3  SOURCE_ONLY    command    SET FILTER, SET INDEX, SET ORDER
                                     (src/cli/command_catalog.cpp)
        2  ...            function

    live SYSCMD 212 rows; candidate emit 229 rows

**Be careful what 189 means.** The compare's source side is the SOURCE CATALOG
(`command_catalog.cpp`), a different extractor from the seed emit's REGISTRY
scan. 189 is not "189 commands vanished"; it is "189 of 212 live SYSCMD rows
have no counterpart in the source-catalog extraction." Whether that is drift, or
two extractors with legitimately different populations, is one measurement away
and is not settled here. `SYSMSG.dbf` has zero rows and warned.

The three SOURCE_ONLY rows are `SET FILTER`, `SET INDEX`, `SET ORDER` --
**multiword again, in a third catalog.** Section 3's defect class now has
sightings in the registry, the HELP store, and the source catalog.

## 7.4 What the candidate says about section 3 -- and it CORRECTS half of it

The three dead `ERROR` registrations **do not appear in SYSCMD at all**:

    grep -c "ERROR CLEAR|ERROR STATUS|ERROR TEST"  SYSCMD_IMPORT_candidate_v1.csv
    0

    "CMD_ERROR_CLEAR","ERROR_CLEAR","command","public","cmd_ERROR_CLEAR",true
    "CMD_ERROR_STATUS","ERROR_STATUS",...
    "CMD_ERROR_TEST","ERROR_TEST",...

`compact_command_name` (`metacollect.cpp`) strips space, underscore AND hyphen,
so `ERROR CLEAR` and `ERROR_CLEAR` compact to the same key and the fold picks
the underscore spelling as canonical. The dead registration is absorbed into the
live one and disappears.

The two SET rows survive, because there is no underscore twin to fold into --
they are the ONLY multiword `CAN_NAME`s in all 229 rows:

    "CMD_SET_RELATION","SET RELATION","command","public","cmd_SET_RELATIONS",true
    "CMD_SET_UNIQUE","SET UNIQUE","command","public","cmd_SET_UNIQUE",true

**So the same source produces two catalogs that disagree about the same three
commands.** SYSCMD says the spaced ERROR spellings are not separate commands.
`COMMANDS.dbf` publishes all three as `implemented=yes; supported=yes`. One of
those is right and it is not the one the operator reads.

That is R5 -- two answers to one question -- and it means section 3's claim needs
splitting. The DEFECT is real and unchanged: `ERROR CLEAR` cannot be typed. What
is corrected is its VISIBILITY: SYSCMD does not carry it, so a reader checking
the metadata catalog would find nothing wrong. **The fold is not a fix; it is
concealment that happens to point the right way.**

## 7.5 THE FINDING THIS RUN WAS WORTH -- `dispatch_reachable` cannot answer

The facts CSV has eighteen columns. One of them is named `dispatch_reachable` --
the exact question AIF-131 turned on, and the exact question section 3 had to
answer by reading the dispatcher by hand.

    1,083 fact rows emitted.  dispatch_reachable = false on ALL 1,083.
    ABOUT false. LIST false. COUNT false. APPEND false.

It is not measuring reachability. Derived from source rather than inferred from
the distribution:

    metacollect.cpp:1329, inside add_metadata_row_fact() -- the ONLY assignment:
      fact.dispatch_reachable = value_bool_any(row, {"DISP_REACH","DISPATCH","HAS_HDLR"});

Two consequences, and together they close the field off completely:

1. It is assigned **only for facts read out of a metadata DBF row.** Every
   source-derived fact -- `source-registry`, `source-catalog`, everything this
   run emitted -- never touches that line and keeps the struct default, `false`.
2. The only table that could supply it does not have the column:

       SYSCMD.dbf fields: CMD_ID, CAN_NAME, TYPE, VIS, HANDLER, ACTIVE

   No `DISP_REACH`, no `DISPATCH`, no `HAS_HDLR`. So the metadata path cannot
   produce `true` either.

**`dispatch_reachable` is false for everything, in every invocation this
repository can currently produce, and it is emitted anyway.** A consumer reading
the facts CSV cannot tell "not reachable" from "not computed" -- the column
answers a question it was never wired to ask.

This is the fifth sighting tonight of one family: a proxy that cannot answer the
question put to it. The others were `IMPLEMENT` (registration read as
reachability), a manual sha256 (newline read as content), and the banner's two
halves. **This one is the sharpest, because the field is NAMED after the right
question.** Had it worked, it would have printed AIF-131 as a row.

Not prescribed here. Whether `dispatch_reachable` gets computed for source facts
(the dispatcher rule is one line: a registry key containing a space can never
match), gets a `DISP_REACH` column in SYSCMD, or gets removed as a field that
misleads, is a ruling for the area that owns metacollect.

## 7.6 Good Neighbor for section 7

    What changed  : this document; four candidate CSVs in this directory, all
                    gitignored by .gitignore:342. Nothing else. The metacollect
                    binary was built to /tmp and is not in the repo. --compare
                    reads metadata and writes none.
    Whose area    : lane full_stack_documentation. Section 7.5 concerns
                    src/meta/metacollect.cpp -- reported, not edited.
    Authorization : the owner's question, 2026-08-26 -- "did you not run
                    metacollect as part of the push?" The answer was no, and
                    the reason given for not running it was wrong.
    Verify        : rebuild is 12 g++ calls from the TU list at CMakeLists.txt:771.
                    7.5: grep -n dispatch_reachable src/meta/metacollect.cpp
                      expect exactly one assignment, at 1329, inside
                      add_metadata_row_fact; and SYSCMD.dbf's six field names.
    Undo          : delete the CSVs and this section. Nothing cites them yet.

---

# 8. The contract that governs these candidates was never tracked -- and it exonerates the fold

## 8.1 A live contract, on disk and outside history since 2026-07-17

Staging the section 7 work put `METACOLLECT_RUNBOOK_V1.md` into a change set,
which made `cited-paths` check it, which surfaced:

    WIDOW  docs/maintenance/lanes/full_stack_documentation/
           METACOLLECT_SYSCMD_CANDIDATE_CONTRACT_V1.md -- on disk, NOT tracked
           cited by METACOLLECT_RUNBOOK_V1.md

**It is not ignored.** `git check-ignore` returns nothing; it was simply never
staged. 3,271 bytes, dated 2026-07-17, headed *"Status: active source-defined
candidate contract"* -- and it is the document that defines the exact artifact
Phase 5 emitted six hours ago. **Gate 5 binds these candidates by SHA against a
contract that is not in history.** Untracked for over a month, and only visible
because an unrelated edit dragged its citer into a change set.

Staged in this commit. The gate's own instruction is "stage the file, or stop
citing it", and a contract governing a live artifact is not a citation to drop.

## 8.2 Checked against it before staging it

A contract is worth tracking only if the thing it governs obeys it. Every clause
that is cheaply testable, tested against the section 7 output:

    "repeated runs over unchanged source must be byte-identical"
      second emission, all three candidates:   BYTE-IDENTICAL
      (the contract's own proof of determinism, and it is the strongest clause
       in the document -- it makes a re-run a CHECK rather than a replacement)
    "rows sort by CAN_NAME"                    True, 229 rows
    unique ids / unique canonical names        True / True
    "TYPE=syntax-command reserved ... other
     rows use TYPE=command"                    {command, syntax-command}
    "default rows VIS=public; included
     developer rows VIS=developer"             {public, developer}
    field order CMD_ID,CAN_NAME,TYPE,VIS,
     HANDLER,ACTIVE                            exact

## 8.3 CORRECTION to section 7.4 -- the fold is the CONTRACT, not concealment

Section 7.4 called the disappearance of the three spaced `ERROR` registrations
from SYSCMD "concealment that happens to point the right way". **That reads as a
criticism of metacollect and it is wrong.** The contract's rule 4:

> A unique compact match may map a registry token such as `SETORDER` to the
> source-contract canonical name `SET ORDER`.

The question is whether `ERROR_CLEAR` is a source-contract canonical name or
merely another registry token -- because rule 3 says two exact registered names
stay separate. Checked:

    src/cli/cmd_error_clear.cpp:15    // command: ERROR_CLEAR
    src/cli/cmd_error_status.cpp:15   // command: ERROR_STATUS
    src/cli/cmd_error_test.cpp:15     // command: ERROR_TEST

They are declared canonical in source contracts. So the registry token
`ERROR CLEAR` maps to the source-contract canonical `ERROR_CLEAR` by unique
compact match -- **rule 4 exactly, working as written.** metacollect is
obeying its contract, and the underscore spelling is canonical because the
SOURCE says so, not because a normalisation happened to swallow a defect.

What survives from 7.4, restated correctly: the two catalogs still disagree,
and the defect is still real, but neither belongs to metacollect. `COMMANDS.dbf`
publishes `ERROR CLEAR` as `implemented=yes` because the REGISTRY has a row for
it; SYSCMD does not carry it because the CONTRACT says the canonical name is
`ERROR_CLEAR`. **The two catalogs are each right about their own authority.**
The single thing that is wrong is upstream of both: `shell_commands.cpp:562-564`
registers three spaced keys that no dispatcher can reach.

That is worth stating plainly because it changes who the finding is FOR. It is
not a metacollect bug and not a SYSCMD bug. It is three lines in
`shell_commands.cpp`, and everything downstream is faithfully reporting them.

## 8.4 Good Neighbor for section 8

    What changed  : this section; METACOLLECT_SYSCMD_CANDIDATE_CONTRACT_V1.md
                    STAGED (content untouched, first time in history); one
                    unescaped pipe escaped in AIF-130's intake row.
    Whose area    : lane full_stack_documentation.
    Authorization : the owner's commit of 848273a77 raised both advisories; this
                    answers them rather than carrying them.
    Verify        : run the emit twice and `cmp` the three candidates.
                    grep -n "command: ERROR" src/cli/cmd_error_*.cpp
    Undo          : `git rm --cached` the contract restores the widow.
