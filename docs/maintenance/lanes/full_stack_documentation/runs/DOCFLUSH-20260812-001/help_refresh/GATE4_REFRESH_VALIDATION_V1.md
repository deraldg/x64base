# Gate 4 -- HELP refresh validation (flush v5)

    Run       : DOCFLUSH-20260812-001
    Recorded  : 2026-08-21, session COWORK-20260821-002
    Operator  : member.derald, host PowerShell (elevated)
    Build     : attempt 3, 17:23 UTC. `CMDHELP BUILD . D:\code\ccode\src` ALONE.
    Runtime   : dottalk++ v0.6 (2026-08-21, cac02a8b dirty), build Aug 21 10:12:21
    Evidence  : help_refresh/step6_alone.txt, plus direct reads of the store
                with tools/fullstack_docs/dbfread.py
    Verdict   : **The refresh APPLIED.** Gate 4 assertions 1, 3, 5a and 6 PASS.
                Assertion 5b was MALFORMED and its corrected form FAILS (see 4).
                Assertions 2, 4, 7 and 8 are NOT YET RUN -- they need the
                post-refresh capture.

---

## 1. The build applied

    CMDHELP wrote current HELP DATA -> D:\code\ccode\dottalkpp\data\help
    Artifacts mined from: D:\code\ccode\src
    Usage contracts mined directly: 3499 row(s) from 207 file(s)

No `WARNING: datarun: could NOT copy` block, and the banner reports
`cac02a8b` built `Aug 21 2026 10:12:21` -- the freshly built exe staged for the
first time in this run. All four v2 tables carry mtime 2026-08-21 17:23.

## 2. What moved, read from the tables

| SOURCE | baseline (08-15) | now | delta |
| --- | --- | --- | --- |
| USAGE_CONTRACT | 14,914 | 15,089 | +175 |
| SOURCE_MINER | 7,503 | 7,560 | +57 |
| SHARED_MSG | 2,637 | 2,637 | 0 |
| DOTREF | 992 | 1,005 | +13 |
| CURATED_DOC | 868 | 868 | 0 |
| EDREF | 786 | 786 | **0 -- see section 4** |
| FOXREF | 665 | 665 | 0 |
| REGISTRY | 462 | 465 | +3 |
| **live lines** | **28,827** | **29,075** | **+248** |
| topics | 528 | 531 | +3 |

`FOXREF` flat at 665 is the PASS this package predicted: `foxref.hpp` did not
change since the store was built, so a move there would have meant something
else did. It did not move.

## 3. Assertion 3 PASSES -- the two new commands are published

    TOPICKEY *|SMTP     143 rows   SOURCE: DOTREF, REGISTRY, SOURCE_MINER, USAGE_CONTRACT
    TOPICKEY *|APPGUI    68 rows   SOURCE: DOTREF, REGISTRY, USAGE_CONTRACT

Both were ZERO before this build. This is the outcome the refresh existed to
produce.

## 4. FINDING -- the edref one-line titles do not reach the store, and my
## assertion was measuring the wrong thing

**First, the assertion was malformed.** Package section 8 said *"`EDREF` != 786;
a FLAT EDREF means the edref work did not reach the store."* That is a HELP_LINE
ROW COUNT being used to test a CONTENT change. `aac6b8bdf` added a `title` field
whose destination is `HELP_TOPIC.TITLE`, not a new HELP_LINE row, so EDREF
staying at 786 was never going to prove anything either way. Same error class as
withdrawn assertion 1: a proxy that cannot move when the thing it stands for
does. **Withdrawn.**

**The corrected check, run directly against `HELP_TOPIC.dbf`, FAILS:**

    ED topics                        29
    TITLE merely echoes TOPIC        29 of 29

    COMMIT     TITLE='COMMIT'
    INDEX      TITLE='INDEX'
    SCAN       TITLE='SCAN'
    ...

That is exactly the condition `aac6b8bdf` was written to remove, measured on a
store built minutes earlier from HEAD by a current binary.

**Mechanism, source-evidenced:**

- `include/edref.hpp:68` declares `const char* title = ""`, populated 29/29.
- `src/help/helpdata_export_dbf.cpp:362` is the ONLY writer of `row.title`:
  `row.title = !artifact.command.empty() ? artifact.command : key;`
- `helpdata_export_dbf.cpp` contains **no reference to edref at all** -- three
  occurrences of "title" in the whole file, all in that one code path.

So the field is authored, guarded, and never read by the exporter. The
edref.hpp comment at `:59` even QUOTES the exporter line that needed changing,
which means the author identified the target and the target was not changed.

**Why nothing caught it.** `edrefcheck_v1.py` guards "presence, length, and
topic-echo" in `edref.hpp` -- the SOURCE. It goes green while the published
surface is untouched. This is the house's named defect pattern exactly: a
declared capability with no implementation on the consuming side, and a gate
that checks CONSISTENCY rather than CORRESPONDENCE WITH DATA. It is also v6
hints 5c restated: *a report is not proven by compiling; it is proven by
pointing it at rows.*

Not fixed here. `helpdata_export_dbf.cpp` is the HELP lane's, and the fix is one
line plus a decision about precedence between `artifact.command` and an edref
title. Filed for the owner.

## 5. Q1's "unexplained 2" -- the harvest OVER-counts, it does not under-cover

The counter says **207 files**. Measured at HEAD:

    .cpp under src containing "@dottalk.usage v1"     209  (filesystem)
    same, tracked (git grep)                          209  (no untracked ones)
    of those, carrying NO contract block at all         4

The four are `src/cli/helpdata_cmdhelp_bridge.cpp`, `src/help/helpdata_messages.cpp`,
`src/help/helpdata_source_miner.cpp` and `src/meta/metacollect.cpp` -- the
implementation of the harvest itself, plus the message table that stores the
marker as a string literal. They mention the marker; they do not declare
contracts. Genuine contract files: **205**.

So the counter (207) sits between the real contracts (205) and the marker
mentions (209): the miner is counting at least two files that merely CONTAIN
the literal. **This inverts the envelope's Q1 hypothesis.** Q1 feared a silent
coverage gap -- that `src/edu` and others were unmined. The addendum already
showed the harvest is tree-shaped; this shows the residual discrepancy runs the
OTHER WAY. Nothing is missing; two things are being double-counted.

Evidence tier: **source-evidenced.** Which two of the four the miner counts is
not determined here and would need an instrumented run. Recorded as the open
remainder rather than asserted.

## 6. A one-row disagreement worth naming, not chasing

The engine reports `topics : 530`; counting distinct `TOPICKEY` in
`HELP_LINE.dbf` gives 531. The same +1 held at Gate 2 (engine 527, count 528),
so it is a stable definitional difference between the two instruments, not
drift. Named so a later reader does not read it as a defect. Nobody should
"fix" either number until someone decides which question each is answering.

## 7. Still owed before Gate 4 closes

Assertions 2, 4, 7 and 8 need the post-refresh capture that has not run:

    $run = 'D:\code\ccode\docs\maintenance\lanes\full_stack_documentation\runs\DOCFLUSH-20260812-001\help_refresh'
    ./datarun.ps1 -CommandLines (Get-Content "$run\fullstack_post_refresh_runtime_v1.dts") |
      Tee-Object "$run\fullstack_post_refresh_runtime_v1.txt"
    Set-Location D:\code\ccode

It gives CMDHELPCHK structural status (2), `DOTHELP` rendering SMTP (4), the
diff against the Phase 2 baseline (7), and the mojibake read (8).

**One change to how it is run, learned the hard way:** that script is a single
`-CommandLines` array of many lines and it ENDS IN `QUIT`. The two-command form
`'CMDHELP BUILD LEGACY','CMDHELP BUILD . <root>'` silently executed only its
first element, twice (see GATE4_ATTEMPT_1_INCOMPLETE_V1.md, A1). Whether that is
a datarun defect or a script-reader one is UNDIAGNOSED and is now an open item
of this run. If the post-refresh capture returns a transcript that stops early,
suspect the same thing rather than the engine.

## 8. LEGACY and the current build are now consistent again

`COMMANDS` 465 / `CMD_ARGS` 2383 were rebuilt at 17:12 by the 08:05 binary; the
v2 tables at 17:23 by the 10:12 binary. Both binaries are ancestors-inclusive of
every input this refresh reconciles (`358c14a8a` is an ancestor of `68dcd6710`),
so the halves agree on content even though they were written eleven minutes and
one binary apart. The half-applied state recorded in attempt 1 is RESOLVED.

Worth stating plainly anyway: two tables in one store written by two different
binaries is not a condition anything in this system can detect after the fact,
because HELP DATA carries no provenance. v6 hints section 2 asked for the stamp;
this run has now produced three separate occasions where it would have answered
a question in one read.

## Good Neighbor note

    WHAT CHANGED   : dottalkpp/data/help -- all four v2 tables rebuilt
                     2026-08-21 17:23 (+248 lines, +3 topics, SMTP and APPGUI
                     published). COMMANDS/CMD_ARGS rebuilt 17:12. This document
                     is new. No source, no git, no promotion.
    WHOSE AREA     : the HELP lane's store. Section 4's finding lands on
                     src/help/helpdata_export_dbf.cpp -- HELP lane, NOT touched.
                     edrefcheck_v1.py's coverage gap is the same lane's.
    AUTHORIZATION  : Gate 3, granted by member.derald 2026-08-21, for exactly
                     this build. No further authorization is claimed or implied.
    VERIFY OR UNDO : backups dottalkpp\data\help.bak-20260821-100525 and
                     -101225, both taken before any write. Undo = restore either
                     over dottalkpp\data\help with the daemon stopped.
                     Re-verify = the section 7 capture.

---

## 9. Addendum -- why the two-command form ran only its first line

Traced 2026-08-21 after the fact. **The launcher is exonerated.**
`launch-common.ps1:258-268` takes the `-CommandLines` array, writes EVERY
element to a temp `.dts` with `WriteAllLines`, and passes it as `--script`. Both
lines reached the engine.

**`--script` is not a script interpreter. It is stdin redirection.**
`src/cli/main.cpp:195-213`: the `--script` branch opens the file and does
`cin_guard.redirect(std::cin, script.rdbuf())`, then calls `run_shell()`. The
lines are fed to the ORDINARY INTERACTIVE SHELL through `std::cin`, read at
`src/cli/shell.cpp:596` by `read_script_command(std::cin, line)`.

Two consequences, both load-bearing and neither obvious from the flag's name:

1. **`cmd_dotscript.cpp`'s machinery does not apply.** Its `stop_on_error`
   trip-check and the `DOTSCRIPT: <file>:<line>: stopped (STOP_ON_ERROR ...)`
   message live at `cmd_dotscript.cpp:573-581` and belong to `DOTSCRIPT`, a
   different entry point. Nothing on the `--script` path prints that, which is
   why the two attempts ended with no diagnostic of any kind. A silent stop was
   the only possible outcome.
2. **Any command performing a nested `std::cin` read consumes the FOLLOWING
   SCRIPT LINES**, because they are the same stream. The codebase already knows
   this hazard by name -- `src/cli/cmd_buildlmdb.cpp:23` states as a property:
   *"BUILDLMDB is shell-safe: no nested std::cin prompt reads."* There are 18
   nested `std::getline(std::cin, ...)` sites under `src/cli`, mostly in the
   browsers and in `cmd_rebuild.cpp:136` / `cmd_reindex.cpp:166`.

**Which read swallowed line 2 is NOT determined.** `press_any_key_blocking()`
(`console_utils.cpp:27`) was the obvious suspect and is ruled out: it has zero
callers, and on `_WIN32` it uses `_getch()` against the console rather than
`std::cin`. Recorded as open rather than guessed at -- this run has already
spent two attempts on a confidently-wrong mechanism.

### Consequence for the section 7 capture -- read before running it

`fullstack_post_refresh_runtime_v1.dts` is ~30 command lines on the same
`--script` path. If any command in it performs a nested stdin read, the capture
will truncate SILENTLY at that line, with no error, exactly as the two-command
build did. Its first block is inherited byte-for-byte from the Phase 2 baseline
script, which ran clean on 2026-08-12, so the inherited half is
runtime-evidenced as safe. **The v5 ADDITIONS at the end are not** -- they have
never run.

Cheap protection, and the reason the additions were placed last: if the
transcript ends early, everything above the cut is still valid evidence.
**Verify the transcript ends with `DOCFLUSH-V5-POSTREFRESH-END` before
accepting any of it**, and treat a missing END marker as truncation rather than
as a clean run. That marker exists for exactly this and was written into the
script before the failure mode was understood.

---

## 10. Post-refresh capture -- COMPLETE. Gate 4 disposition.

    Transcript : help_refresh/fullstack_post_refresh_runtime_v1.txt
                 4,674 lines, 139,030 bytes, 2026-08-21 17:55
    Integrity  : ends with DOCFLUSH-V5-POSTREFRESH-END. NOT truncated.
    Runtime    : dottalk++ v0.6 (2026-08-21, cac02a8b dirty), build 10:12:21

The twin-script design held: the shared first block sits at identical line
numbers in both transcripts (counters at 197/198, SOURCE table at 219-225), so
the two diff positionally rather than by luck.

| # | assertion | result |
| --- | --- | --- |
| 1 | `DOTHELP` renders `SMTP` from `dotref.hpp` (replaces the withdrawn build-stamp check) | **PASS** -- transcript 2357-2358, syntax string verbatim |
| 2 | `CMDHELPCHK` structural status | **PASS** -- "OK no structural issues found" |
| 3 | `SMTP` and `APPGUI` resolve on both `HELP` and `CMDHELP` | **3 of 4. `HELP APPGUI` FAILS -- see 10a** |
| 4 | `DOTHELP` SMTP (same instrument as 1) | **PASS** |
| 5a | `FOXREF` == 665 | **PASS** -- flat, as predicted |
| 5b | `EDREF` moved | **assertion malformed, withdrawn (section 4). Corrected form FAILS.** |
| 6 | lines/topics >= 28,827 / 528 | **PASS** -- 29,075 / 530 |
| 7 | diff against the Phase 2 baseline | **DONE** -- 219 changed lines in the shared block, all attributable to the refresh |
| 8 | no mojibake | **PASS** -- 0 non-ASCII bytes in 139 KB |

**GATE 4 PASSES.** The refresh is correct and complete. The two failures are
findings ABOUT the system, not defects IN this build: 5b was my measurement
error, and 3 is a pre-existing surface gap this build merely made visible.

### 10a. FINDING -- `HELP APPGUI` says "No help found" while the store holds 68 rows for it

    . No help found for: APPGUI
      Did you mean: AVG, APPEND?
    . CMDHELP APPGUI
    DOT|APPGUI
    ==========
    SUMMARY
    -------
    Launch the windowed wxWidgets GUI as a separate process, or report by name
    why it cannot be launched.
    APPGUI is a registered DotTalk++ command; curated DOTREF support status and
    help summary are pending.

Both lines are in the store. The FIRST is the real prose, harvested from the
`@dottalk.usage v1` contract in `src/cli/app_gui.cpp`. The SECOND is the dotref
placeholder. They are stacked in one SUMMARY, and the placeholder is what drives
`supported=no` and the summary in the command table.

So for an uncurated command the three surfaces v6 hints section 3 identified do
not merely DISAGREE -- **one of them returns nothing at all.** `CMDHELP <verb>`
reads HELP DATA and answers. `HELP <verb>` reads the compiled dotref catalog and
cannot find a command that has no dotref entry, so it offers a spelling
suggestion instead. The operator-facing surface is the one that fails.

`SMTP` does not show this because it HAS a dotref entry. The two commands are a
matched pair from the same build, differing only in that one was curated, which
makes this as clean a demonstration as the lane is likely to get.

**Consequence for the uncurated class, now nine strong** (GUI, APPGUI, BUILD
INFO, BUILD VECTORS, FILE, UDATE, UDATETIME, UNOW, UTIME): each is invisible to
`HELP`, and each has good contract prose sitting in the store underneath a
placeholder that says its help is "pending". The prose is not pending. It is
written, harvested, and published -- and then labelled as absent.

This is evidence for ruling (b) in v6 hints section 4, and it widens the
question: the placeholder is not merely noise in a catalog listing, it is
suppressing a `HELP` answer that the store could already give. Owner's ruling.

### 10b. CLOSED by measurement -- the ABOUT thousands separators

Gate 2 section 6 filed three ABOUT observations. One is fixed:

    pre  (08-12)   Compiler : MSVC 1,944   C++ Std : 202,002   OS : Windows 6.1.7,600
    post (08-21)   Compiler : MSVC 1944    C++ Std : 202002    OS : Windows 6.1.7600

Recorded so the lane stops carrying it. Not this run's work -- it landed
somewhere in the nine days.

**The dual build stamp PERSISTS** and is now sharper: banner `10:12:21`, ABOUT
page 2 `Build Date : Aug 21 2026 10:11:51`. Thirty seconds, not eleven minutes,
but still two capture points reported as one fact -- which is precisely what
made it unusable as a freshness test (section 4 / withdrawn assertion 1).

### 10c. Not settled here

`FN_COVERAGE` does not appear in this transcript, so the `FILE` 75/74 warn is
still unverified by a run. `FILE` is present in the Function Inventory
(transcript 884, `function_catalog / partial / fn_string.cpp`), and the tracked
`SYSFUNC_IMPORT_v1.csv` carries `FN_FILE`, but the coverage check itself was not
exercised. Add `FN_COVERAGE` to the next capture rather than inferring it.

## 11. Where v5 stands

Gates 0, 2, 3 and 4 are closed. Remaining before the run can close:

1. **Phase 5/6 re-harvest** that v4 owed -- the manualgen harvest predates the
   rebuild, and the store has now moved twice more.
2. **The website matrix CLOSING gate** in `D:\dev\x64base-site`
   (`content/docs/dev/website-documentation-matrix.mdx`). The envelope makes it
   a closing condition: v5 cannot close on a stale matrix. Four pages are
   already known to need reconciliation (proven-capabilities, /schemas,
   ecosystem-feature-comparison, and a dated announcement).
3. The unruled items: the nine uncurated commands (now with 10a's evidence),
   foxref and `FILE()` (Q2), `risk:` blocks (Q3), and the three-descriptions
   drift -- to which 10a adds that one description is missing entirely.

Steward paused here by instruction before the website step.

---

## 12. v6 hints section 4 is SETTLED -- the filter is not failing, the roster drifted

Asked by the steward 2026-08-21: *is APPGUI absent the usage contract?*

**No. APPGUI has a full contract** -- `src/cli/app_gui.cpp:31-70`:
`command: APPGUI`, `aliases: GUI`, **`status: supported`**, `mutates: none`,
summary, usage, examples, six notes and a four-key `risk:` block. It is one of
the better-documented commands in the tree. What it lacks is a **dotref entry**:
`"APPGUI"` and `"GUI"` are both absent from `include/dotref.hpp`.

### 12a. The synthesizer hardcodes `supported = false` and never reads the contract

`src/cli/cmdhelp.cpp:786-806`. For every registry command with no FOX, DOT or ED
catalog entry:

    if (!seen_any) {
        if (is_expression_function_name(key)) continue;
        CommandInfo ci;
        ci.implemented = true;
        ci.supported   = false;              // <- :803, unconditional
        ci.verbose     = generated_pending_summary(key);
        out.push_back(std::move(ci));
    }

`ci.supported = false` is a literal. The `@dottalk.usage` contract is not
consulted at this point, so **APPGUI publishes `supported=no` while its own
contract declares `status: supported`.** The published surface contradicts the
authority it was harvested from, in the same store, in the same build.

That is a sharper defect than "the summary is a placeholder". A placeholder is
visibly a placeholder; `supported=no` reads as a determination.

### 12b. Why five functions publish as unsupported commands -- the mechanism

v6 hints section 4 recorded FILE / UDATE / UDATETIME / UNOW / UTIME publishing as
uncurated DOT commands, noted that `is_expression_function_name()` exists
"specifically to prevent this", and concluded *"and it is not catching them"*.

**It is not failing. They are not in it.** `cmdhelp.cpp:192-203` is a
hand-maintained `static const std::unordered_set<std::string>` of **64 literal
names**. Measured against the live Function Inventory in this run's transcript
(72 rows from `function_catalog`):

    in the inventory, NOT in the roster (11):
      FILE PADC PADL PADR PROPER STRCAT STUFF UDATE UDATETIME UNOW UTIME

    in the roster, NOT in the inventory (3):
      CONCAT REPLICATE SPACE

Drift in **both** directions, which is the signature of a hand-kept list rather
than a derived one.

Only five of the eleven actually surface as unsupported commands, and the
difference explains itself: `PADC`, `PADL`, `PADR`, `PROPER`, `STUFF` and
`STRCAT` all HAVE foxref or dotref entries (`FOX|PADC`, `FOX|PADL`, `FOX|PADR`,
`FOX|PROPER`, `FOX|STUFF`, `DOT|STRCAT` are all in this run's topic list), so
`seen_any` is true and they never reach the synthesizer. The five that surface
are exactly those that are in the inventory, absent from the roster, AND absent
from all three catalogs.

**This is `no perishable literals` in the engine rather than in a document.**
The authoritative set is `function_catalog`, it is in the same process, and the
roster restates it by hand. `FILE` was added 2026-08-12 and the roster was not
updated; the five were on their way in regardless of whether anyone noticed.

### 12c. What this does to the three candidate rulings

v6 hints section 4 offered (a) curate them in dotref as dual command+function,
(b) fix the filter, (c) accept that scalar invocation gives every catalog
function a command surface.

Ruling (b) now has a precise, one-line meaning it did not have before: **derive
`is_expression_function_name` from `function_catalog` instead of restating it**,
and the drift cannot recur. That is a smaller change than the hints assumed, and
it is orthogonal to (a) and (c) -- it fixes the roster whichever way the
command/function boundary question is settled.

The APPGUI half is separate and does NOT go away under any of the three: APPGUI
is a genuine command, not an expression function, so no filter should suppress
it. Its two problems stand on their own:

1. `ci.supported = false` overriding a contract that says `supported`
   (`cmdhelp.cpp:803`);
2. `HELP APPGUI` returning "No help found" because `HELP <verb>` reads the
   compiled dotref catalog (section 10a).

Both are HELP-lane rulings. Neither is touched here. Recorded with the mechanism
named so that whoever rules does not have to re-derive it.

### 12d. Evidence tier

**Source-evidenced plus runtime-corroborated.** The code paths are read at
`file:line`; the roster-vs-inventory comparison is computed against THIS RUN's
live transcript rather than against a remembered list; the APPGUI contract and
its absence from dotref are read from the tree at `cac02a8b5`. Not claimed:
that changing `:803` or the roster produces the intended output -- neither has
been altered or built.

---

## 13. dotref.hpp is NOT a stub, and the nine decompose into THREE mechanisms

Steward's recollection 2026-08-21: *"we were transitioning dotref.hpp to a
system because it was too large, I think dotref.hpp may be just a stub."*

**Measured: it is not a stub.** `include/dotref.hpp` at `cac02a8b5` is
62,167 bytes, 1,270 lines, mtime 2026-08-18. `dotref::catalog()` is a live
`std::vector<Item>` and this run's `DOTHELP` renders from it. It contributed
1,005 rows to the store.

**The transition is real but unfinished, and both halves are `candidate`:**

- `tools/fullstack_docs/dotref_autogen.py` -- AIF-067 **milestone 1, report-only
  by design.** M2 (flag drifted wording) and M3 (emit a full candidate header,
  gate on refcheck) are the deferred halves the v5 envelope already lists as out
  of scope.
- `dottalkpp/tools/help/generate_dotref_from_metadata_v1.py` -- Phase 3B,
  regenerates dotref.hpp from SYSCMD + SYSARGS, status `candidate`. Its own
  header records the honest gap: SYSCMD/SYSARGS carry no one-line summary, so
  curated summaries are carried forward from the existing header.
- `include/dotref.phase1_classic_db_dotref_snippet.hpp` -- a 1,996-byte Phase 1
  artifact from 2026-07-26.

So dotref.hpp is still the hand-curated authority. Nothing has been replaced.

### 13a. The lane already owns the tool for this question. It was never run here.

`python3 tools/fullstack_docs/dotref_autogen.py --root .`, report-only:

    registry commands    : 238
    native (cmd/edu/app) : 238
    dotref entries       : 249
    usage contracts      : 219
    native commands missing a dotref entry (candidates): 2

    {"APPGUI", "APPGUI", "Launch the windowed wxWidgets GUI as a separate
      process, or report by name why it cannot be launched.", true},   // from src/cli/app_gui.cpp
    {"GUI", "GUI", "TODO: no @dottalk.usage contract found", true},     // NEEDS CONTRACT

**Two, not nine.** The tool derives APPGUI's candidate line straight from its
contract -- the prose we have been discussing was already sitting in a
ready-to-paste form. This run spent effort eyeballing a transcript for something
the lane built a generator to answer. Cheapest-check-first, again.

### 13b. The three mechanisms, each with its own fix

| # | commands | mechanism | evidence |
| --- | --- | --- | --- |
| 1 | APPGUI, GUI | genuinely absent from dotref | `dotref_autogen.py`; both registered (`shell_commands.cpp:178`, `:199`), both dispatch `app_GUI` |
| 2 | FILE, UDATE, UDATETIME, UNOW, UTIME | expression functions leaking onto the command surface; the 64-name hardcoded roster drifted | section 12b |
| 3 | BUILD INFO, BUILD VECTORS | alias keys covered only INSIDE another entry's syntax string | below |

**Mechanism 3, newly identified.** `shell_commands.cpp:486-488` registers three
separate keys -- `BUILDVECTORS`, `BUILD VECTORS`, `BUILD INFO` -- all dispatching
`cmd_BUILDVECTORS`. dotref carries ONE entry whose syntax field is the string
`"BUILDVECTORS | BUILD VECTORS | BUILD INFO"` (`dotref.hpp:47`). The
uncurated-synthesizer test at `cmdhelp.cpp:787-789` is an **exact key match**:

    if (seen_keys.count("DOT|" + key)) seen_any = true;

`DOT|BUILD VECTORS` does not exist as a key, so both alias spellings are
synthesized as uncurated. **The syntax string is prose to a human and invisible
to the check.** Fix is an alias relation, not another dotref entry -- writing
two more entries would duplicate the same command three times.

### 13c. Why this matters more than nine placeholder rows

The three mechanisms need three different rulings and would have been fixed
wrongly as one. Mechanism 2 wants the roster derived; mechanism 3 wants alias
resolution in the seen_keys test; only mechanism 1 wants dotref entries -- and
for that one the generator already produced the text.

Separately, and unchanged by any of the three: `cmdhelp.cpp:803` hardcodes
`ci.supported = false` for every synthesized row, so APPGUI publishes
`supported=no` against its own contract's `status: supported` (section 12a).
That defect survives all three fixes and needs its own.

Evidence tier: **source-evidenced, tool-corroborated.** `dotref_autogen.py` was
executed read-only at `cac02a8b5` under python3; the counts above are its
output. No source, header, or table was modified.

---

## 14. STEWARD CORRECTION -- dotref.hpp is a manual SEED list, and APPGUI was
## simply never added. Sections 10a and 13 are re-weighted.

Steward, 2026-08-21: *"until then dotref.hpp is a manual collection of commands
that we add to dotref.hpp to start the harvest. We did not add appgui to
dotref.hpp so its not there."*

That is the fact this run was missing, and it changes what the APPGUI
observation IS.

**dotref.hpp is an input, not a mirror.** Entries are hand-added to SEED the
harvest. A command with no dotref entry has not been seeded yet. That is the
workflow operating normally, not a system failing. `dotref_autogen.py` is
explicitly the GENERATE step of "generate -> review -> promote" -- it exists
because seeding is manual and someone has to notice what is unseeded.

**What I got wrong.** Section 10a presented `HELP APPGUI` returning "No help
found" as a finding about three surfaces disagreeing, and section 13 built a
three-mechanism table on top of it. The evidence is all correct and re-measurable
-- but the FRAMING gave equal weight to an un-done manual step and to two real
defects. A reader of section 13b would have gone looking for a bug in mechanism
1. There is no bug in mechanism 1. There is an unseeded command, and the seed
line for it has already been generated:

        {"APPGUI", "APPGUI", "Launch the windowed wxWidgets GUI as a separate
          process, or report by name why it cannot be launched.", true},

Paste it into `dotref.hpp` and mechanism 1 is closed. `GUI` needs the same or an
alias relation to APPGUI.

**Read sections 10a, 12 and 13 with this correction attached.** They are not
withdrawn -- the measurements stand and the mechanisms are real -- but mechanism
1 is a housekeeping item, not a defect.

### 14a. What SURVIVES the correction, and why it still matters

**1. `cmdhelp.cpp:803` publishes a DETERMINATION derived from an ABSENCE.**
This is the one to keep. When a command is unseeded the synthesizer writes
`ci.supported = false`, and the store publishes `supported=no` -- for APPGUI,
against its own contract's `status: supported`. "Not yet seeded" and "not
supported" are different claims, and the second is the one that reaches the
operator, the command table, and every downstream surface. The honest output
for an unseeded command is pending or unknown.

This is exactly the house's recurring shape: a thing reporting a confident
result it did not establish. It is unaffected by the seeding workflow -- seeding
APPGUI fixes APPGUI and leaves the next unseeded command mislabelled the same
way.

**2. Mechanism 2 -- the drifted roster (section 12b).** Unaffected. Five
expression functions reach the command surface because a 64-name hardcoded set
in `cmdhelp.cpp:192-203` has drifted from `function_catalog` in both directions.
Seeding cannot fix it and should not be asked to: these are not commands anyone
would seed.

**3. Mechanism 3 -- BUILD INFO / BUILD VECTORS (section 13b).** Unaffected, and
seeding is the WRONG fix here: dotref already covers them inside BUILDVECTORS'
syntax string, and adding two more entries would triple one command. What is
missing is alias resolution in the exact-match test at `cmdhelp.cpp:787-789`.

### 14b. Downgraded to a question, not a defect

`HELP APPGUI` -> "No help found" now reads as **`HELP <verb>` answers only for
seeded commands**, because it renders the compiled dotref catalog. Whether that
is intended -- or whether `HELP` should fall back to HELP DATA, which already
holds 68 rows for APPGUI including the real contract prose -- is a lane design
question for the owner, not something to file as broken. Recorded as a question
with its evidence, and deliberately not as a finding.

### 14c. Open, and not guessed at

The steward also recalled *"i think the system had vectors"*. Not resolved here.
Two candidates were looked at and neither is asserted:
`dottalkpp/tools/help/generate_dotref_from_metadata_v1.py` regenerates
dotref.hpp from SYSCMD + SYSARGS and carries a `--pure` "coverage probe" mode
that quantifies exactly how much of dotref the metadata tables reproduce today;
and AIF-044's generated `build_vectors.hpp` is an unrelated engine-capacity
artifact that shares the word. **Which was meant is the owner's memory, not the
tree's, and this run does not have it.** Left open rather than filled in.

---

## 15. STEWARD DIRECTION -- manual dotref stands; automation is future work

Recorded 2026-08-21, member.derald: *"using dotref.hpp manually works but an
automated version is desired in the future."*

So the manual seed list is the accepted present state, not a defect awaiting
repair. Nothing in this run should be read as arguing otherwise, and section 14
is the correction that already says so.

**The automation is chartered, not net-new.** Two candidate tools exist:

- `tools/fullstack_docs/dotref_autogen.py` -- AIF-067 M1, report-only. M2 (flag
  curated wording that drifted from the contract) and M3 (emit a full candidate
  header, gate promotion on `refcheck_v1`) are the deferred halves.
- `dottalkpp/tools/help/generate_dotref_from_metadata_v1.py` -- Phase 3B,
  regenerates from SYSCMD + SYSARGS, `candidate`, with `--pure` as a coverage
  probe.

Whoever opens that work should read both before writing a third.

### 15a. The cheap bridge, offered and NOT built

Between "manual forever" and "generated header" there is one step that costs
almost nothing and removes the only real hazard of the manual list -- that a new
command stays unseeded silently, which is exactly how APPGUI reached a shipped
store labelled `supported=no`:

**Run `dotref_autogen.py --root .` in the pre-push gate as a WARN, not a block.**
It already prints the count and the ready-to-paste line; it takes about a second;
it is report-only by construction; and `tools/staging/prepush_gate.py` already
hosts advisory checks of this shape. A warn keeps seeding a human decision --
which is the point of a curated layer -- while making the backlog visible at the
moment it is created rather than at the next full-stack flush.

Not built. It touches `prepush_gate.py`, which is another lane's tool and had
uncommitted work in it as recently as 2026-08-12. Offered as the proportionate
next step whenever AIF-067 is picked up.
