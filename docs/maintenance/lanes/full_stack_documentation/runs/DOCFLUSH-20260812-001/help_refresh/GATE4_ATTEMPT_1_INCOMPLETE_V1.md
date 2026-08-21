# Gate 4 attempt 1 -- INCOMPLETE, half-applied. Do not treat as a refresh.

    Run       : DOCFLUSH-20260812-001 (flush v5)
    Attempt   : 1, 2026-08-21 ~17:05 UTC (10:05 local)
    Operator  : member.derald, host PowerShell
    Recorded  : COWORK-20260821-002, from the pasted console output plus direct
                measurement of the store afterwards
    Verdict   : **GATE 4 NOT PASSED.** LEGACY applied; the current HELP DATA
                build wrote nothing. The store is now internally inconsistent.

---

## 1. What actually happened, measured

**Step 4 FAILED and the run continued past it.**

    Get-Process dottalk_bbsd | Stop-Process -Force
    Stop-Process: Cannot stop process "dottalk_bbsd (24112)" because of the
    following error: Access is denied.

The verification line that follows printed PID 24112 again. The shell was not
elevated. `dottalk_bbsd` held the store through steps 5 and 6.

**Step 5 applied. Step 6 did not.** File mtimes under `dottalkpp/data/help`
immediately afterwards:

    CMD_ARGS.dbf        2026-08-21 17:05   <- written
    COMMANDS.dbf        2026-08-21 17:05   <- written
    cmd_args.dbt        2026-08-21 17:05   <- written
    commands.dbt        2026-08-21 17:05   <- written
    HELP_LINE.dbf       2026-08-15 19:49   <- UNTOUCHED
    HELP_ARTIFACTS.dbf  2026-08-15 19:49   <- UNTOUCHED
    HELP_TOPIC.dbf      2026-08-15 19:49   <- UNTOUCHED
    HELP_SECTION.dbf    2026-08-15 19:49   <- UNTOUCHED

`find dottalkpp/data -newermt '2026-08-21 16:30'` returns those four files and
nothing else, so the write was not misdirected to another root -- it did not
happen.

**Read back from the tables themselves**, not from the console:

    COMMANDS.dbf   465 live rows    (LEGACY reported 465)   AGREES
    CMD_ARGS.dbf  2383 live rows    (LEGACY reported 2383)  AGREES
    HELP_LINE.dbf 28,827 lines / 528 topics
                  DOTREF 992  EDREF 786  FOXREF 665  USAGE_CONTRACT 14,914

Every v2 figure is identical to the pre-attempt baseline in
`../runtime_baseline/GATE2_ADDENDUM_V1.md` section 2. Nothing moved.

**Gate 4 assertion 3 FAILS outright:**

    TOPICKEY *|SMTP    0 rows in the v2 store
    TOPICKEY *|APPGUI  0 rows in the v2 store

The two commands this refresh exists to publish are absent from HELP DATA.

## 2. The state the store is in now, stated plainly

    COMMANDS / CMD_ARGS   rebuilt 2026-08-21 from the current binary
    HELP_LINE / ARTIFACTS / TOPIC / SECTION   nine days old (2026-08-15)

That is a **half-applied mutation**, and it is worse than either end state,
because the LEGACY tables and the v2 tables no longer describe the same
catalog. The v5 envelope opened this run to repair exactly one ungated store
move; this attempt has produced a second, narrower inconsistency on top of it.

It is recoverable and low-risk: nothing is lost, the backup
`dottalkpp/data/help.bak-20260821-100525` was taken BEFORE any write (step 3 ran
before step 4 failed), and a successful step 6 rewrites the v2 side anyway.

## 3. Why step 6 wrote nothing -- candidate, not conclusion

The daemon holding the store is the obvious candidate and the one this package
took a step to prevent. It is NOT proven here: the pasted console output ends
before step 6's own messages, so the engine's error, if it printed one, was not
captured. Attempt 2 must keep the whole transcript.

Two things in the captured output are worth carrying either way:

- `Switches mined from: ./src` and **no** `Usage contracts mined directly:`
  line. In `cmdhelp.cpp:2362` the `./src` string is the literal printed when
  `roots` is EMPTY, and the contracts line is suppressed when zero files were
  mined. Both are consistent with this block belonging to `CMDHELP BUILD LEGACY`
  (which takes no roots) rather than to step 6.
- LEGACY's own report is trustworthy here: it claimed 465/2383 and the tables
  hold 465/2383. That is the counter-vs-reality check the house's recurring
  defect pattern demands, and on this one it passed.

## 4. A CORRECTION to this package's own Gate 4 assertion 1

Assertion 1 said: *"`ABOUT` reports a build stamp LATER than `358c14a8a`."*
**That assertion is unsound and is withdrawn.** The banner reported:

    dottalk++ v0.6 (2026-08-20, 68dcd671 dirty)  (Aug 21 2026 08:05:12)

after a step-2 rebuild that ran at ~10:00 and relinked the exe. The stamp is
`__DATE__`/`__TIME__` baked into a translation unit that did not recompile, so
it records when that FILE was last built, not when the EXE was linked. A stamp
that does not move when the binary does cannot witness freshness. This is the
same defect Gate 2 section 6 filed as cosmetic (two stamps eleven minutes
apart); it is not cosmetic, it is load-bearing, and this package leaned on it.

**Replacement assertion 1, content rather than stamp:** `DOTHELP` must render
`SMTP` with the prose from `include/dotref.hpp`. On this attempt it DID --

    395  DOT  SMTP  yes  yes  Mail helper surface: probe the configured server
                             or send a message body, where enabled by local
                             policy. Credentials come from the environment and
                             are never read or printed by the command.

-- which is the dotref text verbatim. So the running exe DOES carry the dotref
change, and the reason is measurable: `358c14a8a` (2026-08-18) is an ancestor of
`68dcd6710` (2026-08-20), confirmed by `git merge-base --is-ancestor`. The
binary is 10 commits behind HEAD but not behind the input this refresh needs.

This is the v6-hints section 2 argument arriving with a receipt: the store and
the binary cannot say what built them, so a run has to reason its way to
freshness, and this package reasoned its way to the wrong instrument.

## 5. New finding -- the uncurated-command class has GROWN from five to nine

v6 hints section 4 recorded five expression functions publishing as unsupported
DOT commands. The LEGACY output on this attempt shows **nine**:

    457  DOT  GUI            yes  no
    458  DOT  APPGUI         yes  no
    459  DOT  UDATE          yes  no
    460  DOT  UDATETIME      yes  no
    461  DOT  BUILD INFO     yes  no
    462  DOT  BUILD VECTORS  yes  no
    463  DOT  FILE           yes  no
    464  DOT  UTIME          yes  no
    465  DOT  UNOW           yes  no

all carrying the same placeholder: *"is a registered DotTalk++ command; curated
DOTREF support status and help summary are pending."*

**`APPGUI` is the instructive one.** It has a NEW, correct `@dottalk.usage v1`
contract (`src/cli/app_gui.cpp:31`, `command: APPGUI`) and it still publishes as
`supported=no` with placeholder prose -- because a contract is not a dotref
entry, and only dotref supplies the curated summary. So the class grows every
time a command is added with a contract but no dotref row, which is the ordinary
path. `GUI`, `BUILD INFO` and `BUILD VECTORS` arrived the same way.

That reframes the three candidate rulings in v6 hints section 4: this is not a
five-item expression-function anomaly to be filtered, it is the DEFAULT outcome
for any new command, and the count only goes up. Recorded for the owner; not
this run's to rule on.

## 6. What attempt 2 must do differently

1. **Run the whole sequence in an ELEVATED PowerShell.** Nothing else changes.
2. Do not proceed past step 4 until the verification line prints NOTHING. The
   package said to check; the check fired correctly and was walked past. That is
   the same shape as the promotion sequence that walked past a failed `git rm`
   on 2026-08-21, caught only by a later sanity step.
3. Capture the FULL transcript of steps 5 and 6, including step 6's own
   messages. This attempt's diagnosis is incomplete only because the output
   stops.
4. Re-run BOTH builds. LEGACY is idempotent and re-running it restores the pair
   to agreement with whatever step 6 then writes.

## Good Neighbor note

    WHAT CHANGED   : dottalkpp/data/help/{COMMANDS,CMD_ARGS}.dbf and their .dbt
                     sidecars, written 2026-08-21 17:05 by CMDHELP BUILD LEGACY.
                     The four v2 HELP DATA tables are UNCHANGED. This document
                     is new; no source, no git.
    WHOSE AREA     : the HELP lane's store, operated by member.derald under the
                     Gate 3 authorization in HELP_REFRESH_PACKAGE_V1.md.
    AUTHORIZATION  : Gate 3, granted 2026-08-21. The mutation performed is
                     INSIDE that authorization; it is incomplete, not
                     unauthorized.
    VERIFY OR UNDO : backup taken before any write --
                     dottalkpp\data\help.bak-20260821-100525
                     Undo = restore that directory over dottalkpp\data\help with
                     the daemon stopped. Preferred remedy is FORWARD: re-run
                     both builds elevated, which supersedes both halves.

---

# Attempt 2 -- 2026-08-21 17:12 UTC. Same outcome, different cause. PROVEN.

Elevated this time. Step 4 printed nothing on both checks: the daemon was
genuinely dead. Store afterwards:

    CMD_ARGS.dbf / COMMANDS.dbf + .dbt   2026-08-21 17:12   written
    HELP_LINE / ARTIFACTS / TOPIC / SECTION  2026-08-15 19:49   UNTOUCHED

Identical to attempt 1. **The daemon-lock hypothesis for step 6 is FALSIFIED.**
Attempt 1 section 3 offered it as the leading candidate; it was wrong, and the
only reason it looked right was that a real lock existed elsewhere in the run.

## A1. Step 6 DID NOT RUN. Read from the source, not the console.

`build_legacy_helpdata` (`src/cli/cmdhelp.cpp:2372`) emits exactly three things,
in this order:

    1. CmdHelpLegacyBuildWritten   "CMDHELP LEGACY wrote: N command rows, M arg
                                    rows -> <dir>"
    2. CmdHelpSwitchesMinedFrom    "Switches mined from: <roots.front()>"
    3. print_commands_report()     the "Commands (registry U foxref U dotref U
                                    edref)" table

That is the ENTIRE captured output, in that order, on both attempts.

`build_current_helpdata` (`:2348`) emits a DIFFERENT set --
`CmdHelpCurrentBuildWritten` ("CMDHELP current build written to <dir>"),
`CmdHelpArtifactsMinedFrom`, optionally `CmdHelpUsageContractsMined`, then
`print_current_help_report`. **None of those four strings appears anywhere in
either transcript.** Step 6 emitted nothing, so it never entered the function.

## A2. `Switches mined from: ./src` belongs to LEGACY and means nothing is wrong

`:2519` -- `if (roots.empty()) roots.push_back("./src")`. For
`CMDHELP BUILD LEGACY` (two words) `outdir_arg` defaults to `"."` and `roots`
is empty, so the literal `./src` is what LEGACY prints. It is the DEFAULT, not
a dropped argument.

Attempt 1 section 3 read this line as possible evidence of a parse failure in
step 6. It is not evidence of anything about step 6. **Withdrawn.** Traced
through the parser at `:2505-2536`, the intended command parses correctly:

    CMDHELP BUILD . D:\code\ccode\src
      words     = [BUILD, ".", "D:\code\ccode\src"]
      mode      = "." -- neither V2 nor LEGACY, so pos stays 1
      outdir_arg= "."           -> resolve_help_dir_arg -> the HELP slot
      roots     = ["D:\code\ccode\src"]

and would print `Switches mined from: D:\code\ccode\src`. It printed `./src`.

## A3. The exe under test was STALE on BOTH attempts, and datarun said so

Attempt 2's rebuild was real -- CMake re-ran, every translation unit recompiled,
`version metadata : v0.6 2026-08-21 cac02a8b dirty=1`, exe written 10:12:21.
Then:

    WARNING: datarun: could NOT copy the freshly-built exe into the runtime bin
             -- the copy being run is STALE (127.1 min older than the build you
             just made).
    WARNING:   reason : The process cannot access the file
             'D:\code\ccode\dottalkpp\bin\dottalkpp.exe' because it is being
             used by another process.
    WARNING:   built  : ...build\src\Release\dottalkpp.exe  (10:12:21)
    WARNING:   running: ...dottalkpp\bin\dottalkpp.exe      (08:05:12)

Confirmed on disk: `dottalkpp/bin/dottalkpp.exe` 15:05 UTC,
`build/src/Release/dottalkpp.exe` 17:12 UTC, both 8,024,064 bytes. The banner
duly reported the old `68dcd671`.

**Something other than `dottalk_bbsd` holds `dottalkpp\bin\dottalkpp.exe`** --
almost certainly a `dottalkpp` CLI left open. Until it is closed, every run
tests the 08:05 binary no matter how many times the engine is rebuilt.

This is the guard working exactly as `CLAUDE.md` describes it, and it is the
third instance today of the resume state's own note: *a running exe holds its
own file.*

## A4. What this costs the run, honestly

Nothing has been proven about the current HELP build path. It has not executed
once. The store's four v2 tables have not been written since 2026-08-15 and are
still the honest baseline. The LEGACY pair has now been rebuilt twice by an
08:05 binary, which is 10 commits behind HEAD but ahead of the dotref input, so
the 465/2383 result is sound even though the sequence around it was not.

## A5. Next experiment -- small, isolated, captured

Two variables were confounded on both attempts: a stale exe, and a second
command that never ran. Separate them.

    1. Find and close whatever holds the runtime exe:
         Get-Process dottalkpp -ErrorAction SilentlyContinue |
           Select-Object Id, Path, StartTime
       Close it (or Stop-Process -Force), then confirm datarun stages the new
       exe -- the WARNING block must be ABSENT and ABOUT must report cac02a8b.

    2. Run step 6 ALONE, captured to a file rather than the console:
         ./datarun.ps1 -CommandLines 'CMDHELP BUILD . D:\code\ccode\src' |
           Tee-Object '<run>\help_refresh\step6_alone.txt'

       If it works alone, the defect is in running two builds in one
       `-CommandLines` array and belongs to datarun or the script reader.
       If it fails alone, its error is finally in a file instead of scrolled
       off a console.

**Do not run the two-command form again until this is settled.** It has now
produced the same silent non-result twice, and repeating it a third time adds
no information.

## A6. Method note against this session's own record

Attempt 1's diagnosis named the daemon as the leading candidate and hedged
correctly ("candidate, not conclusion"), but it also treated a console string
as evidence about a function that had not run. The parser settled both
questions in two reads and was available the whole time. **Read the code that
prints the string before reasoning about what the string means** -- the same
lesson v5's Gate 2 recorded when a grep of the built store produced a
confident wrong answer, now repeated one lane over.
