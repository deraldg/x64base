# The Full-Stack Documentation Push -- recipe book

    Version   : **v6, 2026-09-25.** Numbered to the flush generation it
                describes, per the owner's instruction 2026-09-24: the book's
                version tracks the PUSH, not the document's own edit count.
                (Was "v1"; the filename keeps its _V1 suffix so the lane's
                existing citations to it do not break -- see 8f.)
                History: v1 2026-08-26 after DOCFLUSH-20260825-001; refreshed
                2026-09-24 with every [RAN] figure re-measured; v6 2026-09-25
                adds the real Gate 6 ladder, the promotion result, and the
                runnable-block rules in 0c. v6 was revised a SECOND time the
                same day, after the flush ran to Gate 4 apply: 0d states the two
                standing objectives, 0e is this run's improvement ledger, and
                parts 8g, 8h and 11 moved.
    By        : member.ai.claude.cowork, for member.derald
    Lane      : full_stack_documentation (AIF-068)
    Written   : after running flush v6 (DOCFLUSH-20260825-001) end to end
    Purpose   : one document that names every schema, program and step, so the
                next agent -- or CODEX planning the AI Portal -- does not have
                to reconstruct the pipeline from eleven lane documents.
    Status    : review-needed.

## 0. How to read this, and what is EVIDENCED versus REPORTED

Everything marked **[RAN]** was executed by the author during v6 and the figures
are measured. Everything marked **[DOC]** is taken from a lane document or a
tool's own contract and was NOT independently exercised. The distinction is not
decoration: three items filed as impossible during v6 turned out to be [DOC]
claims that no one had tested.

    planned          written down, nothing built
    source-evidenced read out of source or a tracked file
    runtime-proven   IT RAN, and the transcript exists

**Never write `runtime-proven` for something that did not run**, and name the
platform every time -- a sandbox green is not a green on the maintainer's
toolchain.

## 0c. RULES FOR EVERY RUNNABLE BLOCK IN THIS BOOK

Owner's rule, stated 2026-09-25 after four round trips lost to blocks that
assumed an environment they did not establish. Every one of these broke
something real.

**1. ESTABLISH THE ENVIRONMENT IN THE BLOCK.** A block starts with its own `cd`
and its own variable assignments. Do not assume the reader's working directory
or that a variable survived from an earlier block. Measured cost: a preflight
run from `D:\dev\x64base-site` failed on a path that only exists in
`D:\code\ccode`, and `--root .` silently pointed at the wrong tree.

**2. PIN THE INTERPRETER, AND USE `&`.**

    $py12 = 'D:\code\ccode\.venv312\Scripts\python.exe'
    & $py12 .\tools\...

`$py12 tools\...` is a PARSER ERROR -- PowerShell needs the call operator when
the executable is in a variable. Bare `python` is also wrong: exactly one
sub-check in this lane requires >= 3.12 (`command_catalog_sync.py`, reached
through preflight step 9) and the rest run on 3.10, so a bare `python` passes
eleven steps and fails the twelfth for a reason that looks like drift.
`py -3.12` is NOT a substitute -- the launcher does not see the venv, and on
this workstation it reported "No suitable Python runtime found" while
`.venv312` sat in the repo root. Nor is the vcpkg python: it is minimal and has
no PyYAML, so anything importing yaml dies with `ModuleNotFoundError`.

**THIS RULE WAS ALREADY WRITTEN DOWN AND I DID NOT READ IT.** `CLAUDE.md`'s
Conventions section has carried the `$py12` / NOT `py -3.12` / NOT vcpkg note
for some time, with the PyYAML reason attached. Four failed invocations came out
of not consulting the one file in this repo whose entire job is to be consulted
first. CLAUDE.md is the authority for rules 1-4; this section exists so a reader
already inside the book does not have to know that.

**3. NO `<placeholder>` INSIDE A QUOTED STRING.** Assign it as a variable on
the line above. `$out = '<run>\metacollect_phase'` was pasted verbatim and
raised OpenError. A placeholder that is syntactically valid gets executed.

**4. SHELL SYNTAX IS PART OF THE COMMAND.** `-Format s` already emits
`2026-09-24T20:05:00` with no `Z`; appending one makes it a separate argument
and argparse rejects it. Check the shell's output format before decorating it.

**WHY THIS IS IN THE BOOK AND NOT A STYLE NOTE.** Every block here is pasted by
someone who is not the author, often hours later, into a shell whose state
nobody recorded. A block that works only in the author's session is a [DOC]
claim wearing a [RAN] badge.

## 0d. THE TWO STANDING OBJECTIVES (owner, 2026-09-25)

Stated in the owner's words: **"update data, and improve the fullstack push with
every run."** Everything in this book serves one or the other, and a run that
does only the first is half a run.

    1  UPDATE DATA.  Get the documentation data current: HELP/META store ->
       canonical harvest -> candidates -> the manual -> the website authority.
       This is the visible product of a flush and it is the easier half.

    2  IMPROVE THE PUSH.  Every run must leave at least one instrument better
       than it found it, and must RECORD which one in that run's improvement
       ledger. Not "notice a defect" -- close one, or make one that could not
       answer a question able to answer it.

Why the second objective needs to be written down as an objective rather than a
hope: a flush is measured by whether the data moved, so the instruments that
measured it are never on the critical path. Left implicit, "improve the pipeline"
is what gets dropped when the run is long -- and this lane's entire history is
gates that went green on questions they could not answer, each one shipped by
somebody in a hurry to move data.

**The test for objective 2 is mechanical.** At closeout, name the instrument, the
question it could not answer before, and the question it answers now. If that
sentence cannot be written, objective 2 was not met, and saying so is the honest
closeout rather than a failed one.

## 0e. RUN IMPROVEMENT LEDGER -- DOCFLUSH-20260924-001 [RAN 2026-09-24/25]

What this run changed in the pipeline, against objective 2. Nine commits.

    d5491107c  Gate 5 bound. The accounting found two defects in the binding it
               was confirming.
    fc0b14725  SYSARGS gets the contract and the check SYSCMD has had since July.
               tools/fullstack_docs/validate_sysargs_candidate.py, 161 lines, 12
               clauses, 8 tests. ARG_ID uniqueness is a NEW clause the SYSCMD
               sibling never had; it fails today at rows=1180 findings=14 and the
               header says so in words so nobody loosens it. Contract recorded at
               METACOLLECT_SYSARGS_CANDIDATE_CONTRACT_V1.md, which also records
               that no sysargs .dtschema exists.
    64040cc99  Preflight step 10 was failing on its OWN CONFIG, not the tree.
               derive_anchor_map.py TARGET_MANUALS was missing "user"; adding it
               recovered a real ANCHOR-PERFORMANCE row the bug had hidden. The
               comment records why "student" was deliberately NOT added and that
               the reader manual is correctly not a directory.
    9d60f46e1  The harvest exporter and its checker disagreed by one function, so
               E5 could not pass. _recode moved INTO the exporter beside a single
               render(); the checker imports it. The measured failure (row 4860)
               is in the moved docstring. Two producers of one encoding is the
               same shape as the freshness repair that landed in the readers and
               never in the producer beside them.
    38ec8986d  The canonical harvest is PROMOTED. E5 10/14 -> 14/14,
               canonical_files_mutated=5, rollback_performed=0. Gate 6 opens.
    df698774a  The 22 standalone section link gaps decompose: 19 branch, 3
               content. Recipe book to v6. CLAUDE.md gains the runnable-block
               rules. Both Gate 4 authorizations, machine-verified against their
               own validators before being written.
    00f7796a7  The link gate is scoped to the one directory that was already
               fixed. See 8h.
    7cee40e5d  GATE 4 APPLIED. 168 rows, validation_findings=0,
               rollback_findings=0, reader_pointer_mutated=0, website_mutated=0.
               Reviewed as a diff first: 168 of 168 ledger rows produced a real
               modification and 0 files moved that the ledger does not name.
    a77e3b149  validation_fail_rows 1 -> 0.

**The instrument improved, stated per the 0d test:**

    derive_documentation_progress.py --check
      could not answer : WHICH field drifted. It compared whole text and printed
                         a boolean, so the only way to comply with its own
                         remedy was to re-derive BLIND -- which overwrites the
                         authority with whatever the tree currently says and
                         launders a regression into it as readily as it records
                         real progress.
      now answers      : every differing field by dotted name with both values.
                         field_differences() + flatten(), 8 tests. VOLATILE_FIELDS
                         is ONE list shared with strip_volatile so the text
                         verdict and the field explanation cannot disagree. It
                         returns None rather than [] when either side is
                         unparseable, because an empty list printed for a missing
                         artifact reads as clean.

The verdict stays the text comparison. The explainer can never turn a FAIL into
a PASS, and the tests pin that.

**AND THE FIRST ATTEMPT AT THIS FIX WAS HALF A FIX.** The deriver learned to name
its fields and the preflight kept printing a boolean, because step 9 greps for
exactly two lines -- `documentation-progress check=` and
`documentation-progress check:` -- and drops the rest of the output. The owner ran
the preflight, saw the identical FAIL, and said "almost made it".

That is the MIRROR of the defect this same run recorded in 9d60f46e1: there a
repair landed in the READERS and never in the producer beside them; here it landed
in the producer and never in the reader. Same lane, same day, opposite direction.
**A pipeline stage improved is not an improvement until the thing that prints it
knows.**

The relay is written to survive the next change: it forwards any line the deriver
INDENTS, rather than matching known phrases, so whatever the deriver learns to say
next arrives in the preflight without touching docpush_preflight.py.

**AND THE FIELD DIFF CAUGHT A LIVE DEFECT ON ITS FIRST REAL RUN.** Six fields
differed; two were not predicted and those two were the find:

    current_vertical.measured_fields   LOST   first_open_entry, publication_authorized
    current_vertical.carried_fields    GAINED the same two

Cause, measured: `runs/DOCFLUSH-20260914-001/` holds both
`gate8_publication_authorization.json` and `gate8_publication_evidence.json`;
`runs/DOCFLUSH-20260924-001/` holds neither. So `read_gate8()` returned None,
nothing wrote the two fields, and `vertical = dict(prior_vertical)` left the
09-14 answers standing. **A blind re-derive would have published
`publication_authorized: true` and `first_open_entry: "none"` in an artifact
stamped `run_id: DOCFLUSH-20260924-001`** -- a run that had not closed Gate 7,
let alone Gate 8. `content/docs/dottalk/command-reference.mdx:23` prints that
field verbatim: "First open publication gate: `none`."

`read_gate8`'s own docstring said what should happen -- "the site should keep
reporting E8 open" -- and no code implemented it. **The comment stated an intent
the implementation did not have**, which is a sharper failure than a missing check
because it reads as covered.

FIXED, owner ruling 2026-09-25: `first_open_entry: "E8"`, `publication_authorized:
false` on the absent path. Both states are now MEASURED, not carried -- "this run
directory holds no gate8 authorization" is a measurement of the run directory, and
classifying it so also stops the two fields churning between the two lists every
run. `gate8_vertical()` ALWAYS returns a non-empty dict, because returning nothing
is precisely what let the prior value stand; 6 more tests, including one asserting
both states name the same field set and one asserting they disagree on every field.

STILL OPEN and deliberately not changed: `publication_state` carries the prior
artifact's string on the same path, so an unpublished run reports the LAST run's
publication state. Same rot, not covered by the ruling, and what an unpublished
run's publication_state should read is a lane convention rather than a function's
to invent. Part 11.

**And a second thing the diff settled by NOT appearing.**
`canonical_harvest_tables_exported` stayed 10 and `carried_stale` stayed 4, which
I had predicted would move to 14 and 0. They are correct -- the manifest says
EXPORTED 10, CARRIED_STALE_MAY 4, total 44280 rows -- so the authority publishes
"4 tables carried stale" while step 7 publishes "14/14 tables match current
HELP/META". Both true, about different things, and a reader will take them as
contradictory. The four are META_SYSENTVAR (12 rows), META_SYSFLDDIC (16),
META_SYSHELP (8) and META_SYSMSG (**0**) -- so one of the four "matches" by being
empty on both sides, which is part 7's rule that an empty result is not a
measurement, landing inside a PASS.

**And running the suite to check those 8 tests found the bigger one:** 26 test
files, 104 tests, invoked by no gate, 7 of them erroring since 2026-09-13 -- in
the harvest promotion code THIS RUN used. See 8g-ter. That discovery is worth
more than the field diff, and it came from the routine act of running the tests
rather than from any check.

## 0b. Refresh ledger -- 2026-09-24, HEAD 9c4179367

Re-measured, not edited from memory. **Every figure in the body is now the
September value**; this ledger records the MOVEMENT, which is history rather
than a second answer to "what is it now".

    THE STORE -- one source moved, and it is a REPAIR
      HELP_LINE        29,268 -> 18,715   because USAGE_CONTRACT 15,198 -> 4,556
      HELP_SECTION     14,601 -> 10,707
      HELP_ARTIFACTS   14,601 -> 10,707
      HELP_TOPIC          667 ->    669
      COMMANDS            462 ->    464
      CMD_ARGS          2,368 ->  2,378
      SYSFUNC              75 ->     79
    Every other SOURCE is flat or up. See section 2f -- the drop is the
    two-family contract collapse landing, and it was VERIFIED, not assumed.

    THE PIPELINE -- the preflight nearly doubled
      docpush_preflight   6 checks -> 12 (steps 1, 1b, 2, 3, 4, 5, 6, 6b,
                          7, 8, 9, 10). Steps 7, 8, 9 and 10 did not exist.
      **Step 8 IS the content-level assertion this book ranked #1 for v7.**
      tools/fullstack_docs   50 -> 62 py      tools/staging   23 -> 35 py
      tools/manualgen         5 ->  8 py      + tools/dbf 4, tools/tracking 2
      add_executable targets 27 -> 49
      Tier-1 seed ceiling  8,192 -> 16,384 B (raised 2026-09-04)
      ENGINE VERSION       0.6 -> 1.1  (CMakeLists.txt:24, the one authority)
      AIF intake rows      128 -> 165 distinct
      mandatory-tracked    62 docs / 10 scripts -> 66 / 16
      + ai_report_audit    NEW gate: portal report hygiene, 135 enforced
      R-numbers  19 declared / R127  ->  41 declared / R148
      lanes      AIF-131  ->  AIF-169        open items  17 -> 27 parked
      DOCFLUSH runs  7 -> 11 (20260901-001, -002, 20260902-001, 20260914-001)

    WHAT THIS BOOK GOT WRONG BY AGEING
      Part 11 ranked three open items. TWO ARE BUILT: the content-level
      assertion is preflight step 8 (contract drift), and the site
      present-state check is step 9. Only the rehearsal harness and the
      stated-impossibility check remain.

---

# PART ONE -- THE GROUND

## 1. Repository geography

    D:\code\ccode          DEVELOPMENT worktree, branch `development`.
                           All authoring happens here. This is the only tree the
                           push runs in.
    C:\x64base             PUBLICATION staging. Never touched without an explicit
                           instruction.
    D:\dev\x64base-site    WEBSITE source, branch `codex/lean-sites-publish`.
                           Same GitHub repo (deraldg/x64base), different branch.
                           Serves http://www.x64base.com.

`tools/staging/repository_role_guard.py` enforces this and runs as a `pre-commit`
hook. It refuses a root it does not recognise, which is correct behaviour in a
sandbox -- the mount path is unrelated to either declared root.

**THE SITE BRANCH IS AN ORPHAN, AND A BRANCH COMPARISON ACROSS THE TWO TREES IS
MEANINGLESS.** Measured 2026-09-25 because it nearly produced a wrong finding:

    D:\dev\x64base-site        git merge-base origin/main HEAD  ->  NOTHING
    files tracked on that branch                      470   all website
    files tracked on origin/main                    3,015   includes src/cli,
                                                            include/cli,
                                                            dottalkpp/data,
                                                            tools/manualgen
    rev-list --left-right --count origin/main...HEAD   96  262

`codex/lean-sites-publish` shares NO COMMON ANCESTOR with `main`. The two are
deliberately disjoint trees inside one repository, so "96 behind main" is not a
gap to reconcile -- it is the engine, which the website branch has never carried
and should not.

**Do not read that the way the ccode gap reads.** In `D:\code\ccode`,
`development` and `main` DO share history, `merge-base --is-ancestor` answers, and
the 99-commit gap strands 19 real command pages (8g-bis). Same command, same shape
of output, opposite meaning. This was one careless sentence away from being filed
as a second branch defect.

    THE RULE. Before reporting a branch gap, ask whether the branches share an
    ancestor. `rev-list --left-right --count` answers cheerfully for two
    unrelated histories and its number means nothing there.

And a reader running `git branch -r` in EITHER tree sees the other's branches,
because there is one remote. That is the trap this note exists for.

**RULING 2026-08-26: the website LINKS to the manual; it does not project it.**
That retires "website projection" as a state the pipeline must keep in sync.

## 2. The data layer -- what actually holds the documentation

### 2a. The HELP store -- `dottalkpp/data/help/` [RAN]

Six tables plus memo sidecars. Row counts are the live store as of
2026-08-26 01:11:28.

    TABLE            rows    fields
    HELP_TOPIC        669    TOPICID, TOPICKEY, CATALOG, TOPIC, TOPICTYPE,
                             STATUS, IMPLEMENT, SUPPORTED, PRIMARY, CONFID,
                             TITLE, SUMMARY, SECTIONS, LINES
    HELP_LINE       18715    LINEID, ARTID, TOPICKEY, CATALOG, TOPIC, KIND,
                             SOURCE, CONFID, SEVERITY, NAME, ROLE, LINE_NO,
                             PART_NO, TEXT
    HELP_SECTION    10707    SECTID, ARTID, TOPICID, TOPICKEY, KIND, SOURCE,
                             CONFID, SEVERITY, NAME, ORD, NLINES
    HELP_ARTIFACTS  10707    ID, CATALOG, COMMAND, CMDKEY, OWNER, KIND, SOURCE,
                             CONFID, SEVERITY, NAME, ORD, TEXT, DETAIL, EVIDENCE
    COMMANDS          464    ID, CATALOG, COMMAND, CMDKEY, IMPLEMENT,
                             SUPPORTED, USAGE, VERBOSE
    CMD_ARGS         2378    ID, CATALOG, COMMAND, CMDKEY, ARG, USAGE, VERBOSE

Plus `*_LOCALE` companions (HELP_TOPIC_LOCALE, HELP_LINE_LOCALE,
HELP_SECTION_LOCALE, HELP_ARTIFACT_LOCALE) and `.dbt` memo files
(`commands.dbt`, `cmd_args.dbt`, `help_artifacts.dbt`).

**`TOPICKEY` is `CATALOG|TOPIC`** -- `DOT|APPEND`, `FOX|FILE`, `ED|LOOPS`.
The join every consumer depends on is HELP_LINE.TOPICKEY -> HELP_TOPIC.TOPICKEY.

**CATALOG values seen** [RAN]: DOT 13689, SYSTEM 2663, FOX 1247, ED 842,
EDU 191, UI 28, EXT 21, DEV 18, INTERNAL 16 (HELP_LINE row counts).

**SOURCE values -- the provenance layer, and it is the most useful column in the
store** [RAN]:

    SOURCE_MINER     7701   leading comments and source facts
    USAGE_CONTRACT   4556   mined from `@dottalk.usage` blocks in C++ source
    SHARED_MSG       2663   the runtime message catalog
    DOTREF           1010   the hand-curated command catalog, COMPILED IN
    CURATED_DOC       868   hand-written documentation
    EDREF             786   the educational catalog, COMPILED IN
    FOXREF            667   the FoxPro-compat catalog, COMPILED IN
    REGISTRY          464   reflected from the C++ command registry

**KIND values** (15) [RAN]: SOURCE_FACT 4335, SYNTAX 3532, SUMMARY 2390,
NOTE 2171, STATUS 1566, USAGE 1364, MESSAGE 1026, RELATED 672, ARGUMENT 558,
EXAMPLE 535, ERROR 483, WARNING 45, HINT 19, ALIAS 18, DEPRECATION 1.

    NOTE: there is no RISK kind. `risk:` sub-blocks appear in 206 source files
    and reach ZERO rows in the built store (AIF-129).

### 2b. The METADATA store -- `dottalkpp/data/metadata/` [RAN]

Eight tables. This is the SelfDoc metadata layer; it is NOT the HELP store and
the two are built by different programs.

    SYSCMD       212  CMD_ID, CAN_NAME, TYPE, VIS, HANDLER, ACTIVE
    SYSFUNC       79  FUNC_ID, CAN_NAME, DISP_NAME, DEF_LOCALE, REGION_ID,
                      FUNC_CAT, MIN_ARGS, MAX_ARGS, IMPL_STAT, VIS_TIER, OWNER,
                      SRC_AUTH, SRC_FILE, HANDLER, CALC_CALL, PUB_SURF,
                      SELF_REG, MSG_CAT, ACTIVE, VER_AT, NOTES
    SYSARGS      249  ARG_ID, OWNER_KND, OWNER_NAM, ARG_NAME, DEF_LOCALE,
                      REGION_ID, ARG_KIND, VAL_SHAPE, REQUIRED, REPEAT,
                      SRC_AUTH, SRC_FILE, ACTIVE, VER_AT, NOTES
    SYSSUBCMD     31  SUB_ID, PARENT, SUB_NAME, QUAL_NAME, DISP_STYL, IMPL_STAT,
                      VIS_TIER, OWNER, REG_RING, LIFE_PH, SRC_AUTH, SRC_FILE,
                      HANDLER, PUB_SURF, DISP_REACH, OUT_ROUTE, MSG_CAT,
                      ACTIVE, VER_AT, NOTES
    SYSENTVAR     12  VAR_ID, TOKEN, VAR_KIND, CAN_TARG, HELP_OWNR, SRC_AUTH,
                      SRC_FILE, SHADOWS, DISP_REACH, PUB_SURF, ACTIVE, VER_AT,
                      NOTES
    SYSFLDDIC     16  TABLE_NAME, FIELD_NAME, LOG_NAME, FIELD_ROLE, VALUE_KIND,
                      ACTIVE, VER_AT, DESCR, NOTES
    SYSHELP        8  HLP_TXT_ID, OWNER_KND, OWNER_NAM, TEXT_KIND, SEQ,
                      SRC_AUTH, SRC_FILE, GENERATED, CURATED, ACTIVE, VER_AT,
                      TEXT_BODY, NOTES
    SYSMSG         0  MSG_ID, SYMBOL, ENUM_NAME, SEVERITY, FACILITY, SHORT_TXT,
                      IMPL_STAT, VIS_TIER, OWNER, SRC_AUTH, SRC_FILE, PUB_SURF,
                      USED_RUN, ACTIVE, VER_AT, SUG_ACT, NOTES   <- EMPTY

**SYSMSG has zero rows** and `metacollect --compare` warns about it. The
messaging lane (part 4c) is the reason.

**`DISP_REACH` exists on SYSSUBCMD and SYSENTVAR and NOT on SYSCMD** [RAN]. That
is why `metacollect`'s `dispatch_reachable` fact column is false for every row:
its only assignment reads `DISP_REACH`/`DISPATCH`/`HAS_HDLR` from a metadata row,
and the table that would answer the COMMAND question has no such field.

### 2b-bis. THE CONTRACT-FAMILY COLLAPSE, and why the store shrank by a third

**2026-09-13 (`b6dabae63`), on the owner's one-word instruction "normalize":
the store went from TWO contract families to ONE.** It reached the data in the
rebuild of 2026-09-23 and is the entire reason `HELP_LINE` fell 29,268 -> 18,715.

    before   CONTRACT_*       5,196 rows, written by helpdata_source_miner.cpp
             USAGE_CONTRACT*  3,817 rows, written by helpdata_cmdhelp_bridge.cpp
             deduped union    5,666  -- ~37% of contract text stored twice,
             and NEITHER was a superset, so a reader of one silently missed
             content and a reader of both double-counted.
    after    USAGE_CONTRACT*  4,556 rows.  CONTRACT_*  0.  223 topics covered.

**The row NAME says the opposite of the writer** -- `CONTRACT_*` was the
miner's and `USAGE_CONTRACT*` was the bridge's. Two earlier documents asserted
the reverse, from the names rather than the emitters. **Attributing a defect
from the row name alone blames the wrong file.**

The BRIDGE survived, and on measurement rather than preference: it covers 223
commands against the miner's 217 and misses none of the miner's, while the
miner truncated at `#` (losing four of seven published IDX usage forms) and
absorbed post-contract commentary (32 stored notes where `cmd_rel.cpp` declares
3). Full record:
`claude/MEASUREMENT_WHICH_CONTRACT_FAMILY_SURVIVES_AND_WHY_IT_WAS_NOT_THE_ONE_NAMED_FOR_IT.md`.

**HOW TO VERIFY IT IS THE REPAIR AND NOT A LOSS**, because the shape of a
one-third drop invites the wrong conclusion:

    count NAME families among SOURCE='USAGE_CONTRACT' HELP_LINE rows.
    CONTRACT_* == 0 and 223 distinct TOPICKEYs is the signature.
    223 is the number the 09-13 measurement PREDICTED for the survivor.

### 2c. Declared schemas -- `dottalkpp/data/schemas/` [RAN]

Only five `.dtschema` files exist. **The DBF field lists above are the real
schema for everything else** -- most tables have no declared schema file.

    metadata/syscmd_catalog.dtschema      physical schema for SYSCMD
    metadata/sysmsg_catalog.dtschema      physical schema for SYSMSG
    messaging/message_catalog.dtschema    the runtime message catalog
    help/help_locale_companions.dtschema  the *_LOCALE tables
    locale/locale_spine.dtschema          the locale spine

Directories present: `help/`, `locale/`, `messaging/`, `metadata/`, `spec/`,
`tables/`.

### 2d. Catalogs that are COMPILED INTO THE ENGINE -- the single most important fact

    include/dotref.hpp     the DOT command catalog
    include/foxref.hpp     the FOX (FoxPro-compat) catalog
    include/edref.hpp      the ED/EDU educational catalog
    include/devref.hpp     reserved, EMPTY BY DECLARATION

**These are C++ headers. Editing one is a SOURCE CHANGE, and the store cannot
reflect it until the engine is rebuilt.** This single fact is the cause of the
`exe newer than catalogs` gate, and of the 2026-08-12 cycle loss that produced
it.

**`dotref.hpp` is a MANUAL SEED LIST**, not a generated artifact -- the owner's
correction, 2026-08-21: *"dotref.hpp is a manual collection of commands that we
add to dotref.hpp to start the harvest."* A command absent from it is absent
from the harvest, and that is not a defect. An automated form is desired and
does not exist; `tools/fullstack_docs/dotref_autogen.py` is the seam.

### 2e. Derived indexes

    dottalkpp/data/indexes/   CDX
    dottalkpp/data/lmdb/      LMDB -- DERIVED FROM CDX. `BUILDLMDB` regenerates.

**LMDB is never authoritative.** If CDX and LMDB disagree, CDX wins and LMDB is
rebuilt.

---

# PART TWO -- THE PROGRAMS

## 3. Compiled programs

### 3a. `dottalkpp` -- the engine [RAN]

Builds the HELP store. Contains dotref/foxref/edref. Everything the operator
types goes through `shell_dispatch` / `shell_execute_line` in
`src/cli/shell_api.cpp`.

    HOST     .\build.ps1 -Testing          -> build\src\Release\dottalkpp.exe
             staged copy at dottalkpp\bin\dottalkpp.exe -- CHECK THEY MATCH
    SANDBOX  cmake + ninja, g++ 13.3, ~9 minutes. AIF-130 and
             docs/agents/HANDOFF_CLAUDE_COWORK_SANDBOX_BUILD_2026-08-12.md

**Verify the staged exe is the one you just built, by CONTENT not by stamp:**

    md5sum build/src/Release/dottalkpp.exe dottalkpp/bin/dottalkpp.exe
    strings -a build/src/Release/dottalkpp.exe | grep -c '<a string only your change introduces>'

**The banner lies, in two different ways** [RAN]:

    dottalk++ v0.6 (2026-08-24, c39d966c dirty)  (Aug 25 2026 18:00:12)

**That banner is QUOTED AS EVIDENCE from 2026-08-25 and is NOT current state.**
The version authority is `CMakeLists.txt:24`, `project(DotTalkpp VERSION 1.1)`,
and it reads **1.1** as of 2026-09-24. The line is left verbatim because
rewriting a quoted observation to match today falsifies the observation -- the
same reason the BOM'd acceptance records were committed unmodified rather than
normalised. **Annotate evidence; do not edit it.**

                    ^ commit from CMake CONFIGURE time (CMakeLists.txt:59),
                      never refreshed by `cmake --build`
                                              ^ __DATE__/__TIME__ from a TU that
                                                did not need recompiling

Neither half is a freshness proxy. Do not build an assertion on either.

### 3b. `metacollect` -- the metadata collector [RAN]

Standalone C++ source-reflection tool. NOT part of `dottalkpp.exe`, NOT a
registered command, no launcher. Emits candidates; mutates nothing.

    sources   src/tools/metacollect_main.cpp, src/meta/metacollect.cpp,
              include/dt/meta/metacollect.hpp
    target    `metacollect`, option DOTTALK_BUILD_METACOLLECT (default OFF)

    HOST     cmake -S . -B build -DDOTTALK_BUILD_METACOLLECT=ON
             cmake --build build --target metacollect --config Release
             -> build\Release\metacollect.exe
    SANDBOX  UNDER 40 SECONDS with plain g++, no CMake. `dt_meta` at
             CMakeLists.txt:771 enumerates all 11 TUs; add
             src/tools/metacollect_main.cpp. -I include -I src/cli/expr,
             -std=c++17. BUILD OUTSIDE THE TREE.

The last two TUs (`src/common/path_resolver.cpp`, `src/common/path_state.cpp`)
are there because `resolve_in_slot()` is compiled into TWO link closures and only
the engine's carried it. If you hit an undefined symbol, read the comment at
CMakeLists.txt:771 before adding a stub.

### 3c. Other CMake targets, and why they are not in the push

    dottalk_bbsd        BBS daemon
    dottalk_tui         ArcticTalk Turbo Vision front-end
    dottalk_wb          the windowed Workbench GUI (wxWidgets); APPGUI launches it
    dottalk_wb_next     next-generation GUI
    schema_inventory    website schema inventory (web phase)
    g0_slot_cost_probe  AIF-078 per-slot cost measurement
    fox_palette         opt-in TV palette editor (src/CMakeLists.txt:494)
    uidef_wx_demo       UIDEF-generated wx frontend (gui/uidef/CMakeLists.txt:182)

49 `add_executable` targets exist in total (27 in August).
**`arctictalk_workbench` is currently neither DECLARED nor EXCLUDED** in
`program_freshness_check.py`, which is the manifest-coverage check reporting its
own staleness exactly as designed. `tools/coordination/program_freshness_check.py`
requires every one to be DECLARED or EXCLUDED by name.

## 4. Python tooling, by role

Run everything with the host `$py12`:
`C:\Users\deral\vcpkg\installed\x64-windows\tools\python3\python.exe`.
Most tools run on 3.9+; two carry version guards (part 8d).

### 4a. Gate and preflight -- `tools/coordination/` (15) and `tools/staging/` (35)

    docpush_preflight.py            THE preflight. Six steps. tools/fullstack_docs/
    help_build_order_check.py       steps 4: catalogs -> exe -> LEGACY -> store
    help_store_check.py             step 5: the JOIN, and --against for a SET diff
    program_freshness_check.py      step 6: EVERY program, and python version guards
    aif_collision_gate.py           duplicate AIF numbers (HARD)
    r_collision_gate.py             duplicate R numbers (HARD)
    next_aif.py / next_r.py         allocators
    idcite.py                       `id-cite:ignore`, quote an id without spending it
    check_aif_claimed.py            a new intake row cites a claimed number
    session_coordinator.py          who is working now (stale entries common)
    check_open_items.py             parked items and their due dates

    prepush_gate.py                 the pre-commit hook's main body
    repository_role_guard.py        which tree may push where
    check_house_style.py            non-ASCII in ADDED doc lines; inline pipes
    ascii_normalize.py              the fixer, with an explicit mapping table
    check_cited_paths.py            a cited repo path must be TRACKED
    check_seed_budget.py            the Tier-1 seed's 8,192 B ceiling
    check_version_coherence.py      one version authority
    check_sandbox_git_guard.py      the sandbox git rules
    plan_gate5_staging_overlay.py / execute_gate5_staging_rebuild.py

    NEW since 2026-08-26, and every one of them runs in the pre-commit hook:
    check_append_callers.py        appendBlank() call sites vs a baseline
    check_field_write_callers.py   direct DbArea field writes vs a baseline
    check_declaration_order.py
    check_header_reachability.py
    check_manual_link_integrity.py every linked manual page exists and is tracked
    check_site_artifacts.py        the site's generated JSON authorities
    check_soak_evidence.py         the regression registry
    check_untracked_contracts.py

### 4b. The doc stack -- `tools/fullstack_docs/` (62)

    source_census.py                @dottalk.file coverage (preflight step 1)
    command_catalog_sync.py         website catalog vs registry (step 2)
    export_help_meta_harvest.py     THE FEEDER: 14 HELP/META tables -> CSV.
                                    `--out` REFUSES the canonical harvested/.
    dbfread.py                      the shared DBF reader. `t.live` is a COUNT,
                                    `t.rows` is the records. AIF-127 fixed an
                                    x64 false-terminator here.
    refcheck_v1.py                  every dotref/foxref entry resolves
    normcheck_v1.py                 FN_IDENTITY, REFLECTION, FN_COVERAGE
    edrefcheck_v1.py                the ED catalog
    stack_audit_v1.py               check G, COUNT_KINDS
    help_guard_v1.py / manual_guard_v1.py
    dotref_autogen.py               the seam for automating the seed list
    compare_help_meta_harvest.py    harvest vs store
    build_reference_identity_inventory.py
    build_website_feed_packet.py / validate_website_feed_packet.py
    stage_assembled_manual_to_site.py

### 4c. The other tool populations, and one of them is a problem

    tools/manualgen/       8      manualgen.py + 7 builders (part 6)
    tools/selfdoc/         7      the SelfDoc validators (part 5)
    tools/comments/        5      source-comment escrow and reharvest
    tools/contracts/       1      contract_scan.py
    tools/reports/        11      regression_index.py writes the website MDX
    tools/dbf/             4      schema_registry.py and friends (NEW since Aug)
    tools/tracking/        2      seed_tracking.py (NEW since Aug)
    tools/diagram/         2      generate_drawio_from_meta.py
    tools/datadict/        0 py   extractors live in subdirectories
    tools/messaging/     547      <- SEE BELOW

**`tools/messaging` holds 547 Python scripts** [RAN], and they are not a
toolset -- they are a per-step archive:
`append_messaging_savepoint_phase22ae_6_5_10ds0_b.py` and about five hundred
siblings. Every step of the message-catalog lane became a file. **This is the
largest single population of tooling in the tree, it has no index, and SYSMSG
still has zero rows.** Flagged for CODEX: any organizational plan for the AI
Portal has to decide what this directory IS before it can route anyone to it.

## 5. SelfDoc -- `selfdoc/` and `tools/selfdoc/`

`d:\code\ccode\selfdoc\` (60 files, all tracked, 993 KB):

    5 policy documents      artifact lifecycle, collection imperfection,
                            external tool intake, inventory probe plan,
                            web diagnostic feedback. All PLAN_ONLY/REPORT_ONLY,
                            mutation authorization CLOSED.
    7 authority files       metadata_system_registry_v1.json (24 systems),
                            reference_identity_authority_v1.json (331 identities),
                            source_contract_vocabulary_v1.json,
                            two tool lineages, pipeline_manifest.yaml,
                            tool_manifest.yaml
    probes/  41 scripts     the retired source_contract_inventory_probe v1.1 lane
    attic/                  empty but for a README

Four validators, all read-only [RAN]:

    validate_reference_identity_authority.py   PASS  331 identities, 0 duplicates
    validate_source_contract_vocabulary.py     PASS
    validate_documentation_lineages.py         PASS
    validate_metadata_system_registry.py       FAIL  10 of 24 systems

**Nothing runs any of them.** No CI job, no hook; only their own tests reference
them. The registry's 10 mismatches are `source_sha256` pins from a single
session on 2026-07-16/17 whose entrypoints have since changed -- and the drift
correlates with which systems are being WORKED on. **Both PROTECTED mutators are
among the drifted** (META-008 `src/cli/cmdhelp.cpp`, 7 commits since its pin;
META-020 `src/xindex/cdx_meta.cpp`). The attestation decays fastest on exactly
the systems most worth attesting.

---

# PART THREE -- THE LADDER

## 6. Phases and gates, in order, with the commands

The numbering has a KNOWN COLLISION: the COOKBOOK calls Phase 7 "review and
close the dev-tree run" and Phase 8 "publication ascent"; the RUNBOOK line 201
calls Phase 7 "Web ascent to x64base.com". Say which you mean.

### Gate 0 -- preflight [RAN]

    $py12 tools\fullstack_docs\docpush_preflight.py --root .
    $py12 tools\fullstack_docs\docpush_preflight.py --root . --catalog <site>\command-catalog.mdx

    1   @dottalk.file coverage 100%, uncovered 0                   HARD
    1b  audit_contracts: helper-aware usage and dotref coverage    measure HARD,
                                                                   debt advisory
    2   website catalog matches the registry                       HARD (--catalog)
    3   plan doc is ASCII                                          advisory
    4   help_build_order_check: binding / exe newer than catalogs /
        store newer than exe / legacy before store / generation
        stamp / store integrity / status coherence                 HARD
    5   help_store_check: every HELP_LINE row names a topic        HARD
    6   program_freshness_check: every program newer than its
        sources; python version guards; manifest coverage          HARD
    6b  metacollect is BUILT, not merely fresh                     HARD
    7   harvest freshness (E5): the CANONICAL harvest matches the
        live HELP/META store                                       HARD
    8   CONTRACT DRIFT: every source usage contract is in the
        store, UNCHANGED                                           HARD
    9   site present-state: the website progress authority matches
        a fresh derivation                                         HARD (--site-root)
    10  anchor map                                                 HARD

**Re-run it after EVERY rebuild.** `--no-git` skips the worktree-binding check.

**STEP 8 IS THE CHECK THIS BOOK ASKED FOR.** Part 11 of the August version
ranked "a content-level assertion in the preflight" first, on the grounds that
6' is a membership check and the content diff was a hand-run workaround. It was
built. Measured 2026-09-24 it reported `CONTRACT DRIFT: 1 DIFFERENCE --
~ DOT|COPY [NOTE]`, which is the COPY contract that changed at 02:48 that
morning against a store built the previous evening. **It works, and it is the
answer to the blind spot this book named.** Step 9 likewise closes the
site-present-state gap.

**UNRUN IS NOT PASS**, and the preflight now says so in those words for steps 9
and 10. Step 10 currently fails on its own configuration --
`derive_anchor_map: target_manual 'user' is not in [command_reference,
developer, none, reader, site]` -- which is a defect in the check, not in the
tree.

### Gate 1 -- mine and count

Read the counters the miner already prints before designing a new measurement:
`Usage contracts mined directly: N row(s) from M file(s)` is emitted by every
`CMDHELP BUILD` and lands in the transcript.

### Gate 2 -- baseline

Capture the store's own generation stamp and back it up. The engine writes
`dottalkpp/data/help.bak-YYYYMMDD-HHMMSS/` automatically on a LEGACY build.

### Gate 3 -- package and authorization

Write the package; get the owner's authorization in writing; record who
authorized what.

### Gate 4 -- execute and validate [RAN]

**THE TWO REBUILD COMMANDS. Type them at the engine prompt, ONE AT A TIME.**

    cmdhelp build legacy
    cmdhelp build . d:\code\ccode\src

**`.` IS THE PROMPT, NOT SOMETHING YOU TYPE** -- it is DotTalk++'s prompt
character, the way `PS>` is PowerShell's, and a transcript shows it because the
engine printed it. Earlier drafts of this book wrote `. cmdhelp build legacy`
as if the dot were a prefix; it is not. Owner's correction, 2026-09-24.

**The `.` in the SECOND command IS real** and is the command's own argument:
`CMDHELP BUILD LEGACY` builds the legacy tables and `CMDHELP BUILD . <src>`
builds the current ones, where `.` names the current target. So one of the two
dots on that line is prompt and the other is argument, which is exactly why the
distinction is worth stating rather than assuming.

**NEVER pass both to `datarun.ps1 -CommandLines` as an array.** `--script` is
stdin redirection (`main.cpp:195-213`), so a nested `std::cin` read in the first
command eats the following line and only the first runs -- twice. It cost v5 two
cycles, the second time inside a script written by the steward who had just
documented it. Typing at the prompt has no stdin to redirect, so the trap cannot
be re-armed by copying a line.

Then validate:

    $py12 tools\coordination\help_store_check.py --against dottalkpp\data\help.bak-<pre-run>

    6'  topic-SET diff. Replaces the topic-count floor, which on 2026-08-24
        scored a REPAIR as a regression. ZERO LOST is the load-bearing half.
    1'  RETIRED IN PRACTICE -- the banner cannot answer (part 3a).
    5b  RETIRED -- an EDREF HELP_LINE count cannot witness a HELP_TOPIC.TITLE change.

**6' IS A MEMBERSHIP CHECK, NOT A CONTENT CHECK.** It cannot see a
SUBSTITUTION. The workaround, and it is still a hand-run [RAN]:

    read both stores with dbfread; key COMMANDS on (CATALOG, COMMAND) and
    HELP_LINE on the multiset of (TOPICKEY, KIND, SOURCE, ROLE, TEXT);
    EXCLUDE the id columns -- they renumber on insert and a raw diff read
    676 lines for a 2-row change.

### Phase 5 / Gate 5 -- metadata candidates [RAN]

    $mc = 'D:\code\ccode\build\Release\metacollect.exe'
    $run = 'D:\code\ccode\docs\maintenance\lanes\full_stack_documentation\runs\DOCFLUSH-20260924-001'
    $out = "$run\metacollect_phase"      # SUBSTITUTE YOUR RUN ID ABOVE, and
    mkdir $out -Force                     # create it -- metacollect will not
    & $mc --source-root D:\code\ccode\src --include-dev-commands --sysargs-include-keywords `
          --syscmd-import-out  "$out\SYSCMD_IMPORT_candidate_v1.csv" `
          --sysfunc-import-out "$out\SYSFUNC_IMPORT_candidate_v1.csv" `
          --sysargs-import-out "$out\SYSARGS_IMPORT_candidate_v1.csv" `
          > "$out\metacollect_facts_v1.csv" 2> "$out\metacollect_stderr_v1.txt"

    & $mc --source-root D:\code\ccode\src --compare `
          --compare-out "$out\metacollect_compare_v1.csv" `
          --metadata-root D:\code\ccode\dottalkpp\data\metadata

**VALIDATE BOTH CANDIDATES. Nothing else runs these.**

    python tools\fullstack_docs\validate_syscmd_candidate.py `
        "$out\SYSCMD_IMPORT_candidate_v1.csv" --repo-root .
    python tools\fullstack_docs\validate_sysargs_candidate.py `
        "$out\SYSARGS_IMPORT_candidate_v1.csv" --repo-root . `
        --syscmd-candidate "$out\SYSCMD_IMPORT_candidate_v1.csv"

    expected 2026-09-24:  SYSCMDCHK  OK   rows=231  findings=0
                          SYSARGSCHK FAIL rows=1180 findings=14

**THE SYSARGS FAIL IS CORRECT AND MUST NOT BE SILENCED.** All 14 are
`ARG_ID_DUPLICATE`, the keyword/placeholder collision in
`METACOLLECT_SYSARGS_CANDIDATE_CONTRACT_V1.md`. Run against the 08-05 and 08-26
candidates the same check reports 9 and 12 and nothing else, so the clauses are
right and the collision is the only defect. It goes green when the emitter's id
carries `arg_kind`.

**Neither validator was wired to anything before 2026-09-24.** The SYSCMD one
has existed since July, its contract said "the candidate must pass the focused
validator", and the only thing outside its own unit test that named it was one
July run document. A validator nobody runs is a contract clause nobody checks --
the same shape as `validate_metadata_system_registry.py` failing on 10 of 24
with no caller, which is still open in Part 11.

**A `<placeholder>` in a command block gets pasted.** `$out` read `'<run>\...'`
in the first edition, and it was pasted verbatim and raised OpenError. Any
placeholder left in a runnable block must be a variable you assign on the line
above, not angle brackets inside a quoted string.

v6 results [RAN] 2026-08-26: SYSCMD 229, SYSFUNC 75, SYSARGS 1066
(baselines 226/74/959). `--compare`: 192 WARN = 187 METADATA_ONLY command +
2 METADATA_ONLY function + 3 SOURCE_ONLY command.

v7 results [RAN] 2026-09-24: SYSCMD 231, SYSFUNC 79, SYSARGS 1180, and the
compare CSV came back **byte-identical to August's** -- same 27,184 bytes.
Explained, not lucky: `command_catalog.cpp` has not been touched since
2026-07-25 and `SYSCMD.dbf` since 2026-08-24, so both sides of that compare are
frozen. A flat instrument reports that ITS INPUTS did not move; it is not
evidence the lane is stable. SYSFUNC +4 is one commit (94782c434, the four
cursor functions) landing on both sides; SYSARGS +114 is 17 commands' usage
contracts growing, led by WORKSPACE 44, USER 22, SQLSEL 18.

**TRAP: `--sysargs-include-keywords` makes ARG_ID collide.** `ARG_ID` is
`ARG_<command>_<arg_name>` (`metacollect.cpp:1087`) while the row is aggregated
on `command|arg_kind|arg_name` (`:1084`), so a command whose usage text uses one
word as BOTH a literal keyword and a placeholder -- `SET PATH` and `<path>`,
`USER ... KEY` and `<key>` -- emits two different rows under one id. 9 such
collisions on 2026-08-05, 12 on 08-26, 14 on 09-24. The standard emit above
turns the flag on, so every candidate has carried them. Nothing catches it: the
contract's uniqueness clause is on SYSCMD. Check it with
`cut -d, -f1 SYSARGS_IMPORT_candidate_v1.csv | sort | uniq -d`.

**Candidate CSVs are gitignored** by the `.gitignore` rule
`docs/maintenance/lanes/**/runs/**/*.csv` -- cite it by TEXT, not by line: it
was line 342 on 2026-08-26 and is line 545 today, because the file grew above
it. Gate 5 binds them BY SHA-256 in a tracked document. The governing contract is
`METACOLLECT_SYSCMD_CANDIDATE_CONTRACT_V1.md` -- itself found untracked on
2026-08-26 and staged then. Its strongest clause is
**"repeated runs over unchanged source must be byte-identical"**, which makes a
re-emission a CHECK rather than a replacement.

**Binding authorizes NOTHING further.** Any load into SYSCMD.dbf, and any
CDX/LMDB work, needs a separate reviewed mutation gate with backup, readback,
rollback evidence and explicit authority.

### Phase 6 / Gate 6 -- the manual candidate [RAN]

**Re-export the harvest FIRST if it predates the Phase-4 rebuild.** This is E5
of the entry check and the cookbook flags it as the row that usually fails.

**USE THE ENGINE EXPORTER. The Python one cannot produce a promotable package.**

    pwsh -File dottalkpp\data\scripts\metadata\HELP_META_HARVEST_EXPORT_v1.ps1

That is the sanctioned producer: it runs the .dts, promotes into
`harvested\export_runs\HELPMETA-<utc>\`, carries the four stale May `META_*`
forward LABELLED `CARRIED_STALE`, and writes
`HELP_META_EXPORT_MANIFEST_v1.csv` -- row counts AND a SHA-256 per file.

    $py12 tools\fullstack_docs\export_help_meta_harvest.py --repo-root . --out <candidate dir>
    -> 14 tables, 44,280 rows   [RAN 2026-09-24; the 62,570 above was v6, before
                                 the USAGE_CONTRACT collapse took HELP_LINE from
                                 29,268 to 18,730]

The Python scaffold is fine for MEASURING the store -- it reads all 14 tables
from the live DBFs and reached **E5 PASS 14/14** on 2026-09-24. It is NOT a
promotion producer: it writes `HELP_META_EXPORT_MANIFEST_v0.csv`, a different
schema with NO per-file hash, and the planner requires one manifest spelling
present in BOTH workspaces. Canonical carries v1, the scaffold writes v0, so
`resolve_manifest_name` finds neither in both, falls back to v0, and reports:

    FAIL_PLAN_ONLY: mutation_rows=9 noops=5 apply_available=0
      CANONICAL_MISSING:HELP_META_EXPORT_MANIFEST_v0.csv
      PACKAGE_INCOMPLETE:14/15

**That is not the planner being wrong.** The planner was already repaired for
exactly this on 2026-09-14 and its comment says so. The repair landed in the
READERS -- the freshness checker and the planner -- and never in the producer
beside them, which is the same shape twice in one tool chain.

Then:

    $base = '--repo-root','D:\code\ccode','--manual','developer',
            '--publication-workspace','<workspace>',
            '--harvest-workspace','<candidate dir>'
    & $py12 .\tools\manualgen\manualgen.py @base inventory
    & $py12 .\tools\manualgen\manualgen.py @base validate
    & $py12 .\tools\manualgen\manualgen.py @base export-manifest
    & $py12 .\tools\manualgen\manualgen.py @base build-dry-run

**`boundary_fail_rows=0` is the acceptance condition.** Nine boundaries:
publication not rebuilt, published workspace not mutated, media not touched,
no x64base tables, no C++ written, no HELP/META/CMDHELPCHK mutation.

Then the R127 allow-list page generator -- **`--dry-run` FIRST, ALWAYS**:

    & $py12 .\tools\manualgen\build_postbaseline_supported_command_pages.py `
        --current-topics <harvest>\HELP_HELP_TOPIC.csv `
        --baseline-topics <prior harvest>\HELP_HELP_TOPIC.csv `
        --help-lines <harvest>\HELP_HELP_LINE.csv `
        --accepted-command-dir <workspace>\command_reference_v1\commands `
        --output-dir <run>\command_pages_<date> `
        --compose-catalog FOX --compose-catalog UI --compose-catalog DEV `
        --reference-run <run>/<harvest> `
        --expected-topic-key "DOT|<KEY>" ... --dry-run

**The allow-list is the point**: the tool VERIFIES a named list, it does not
deduce one. Without `--expected-topic-key` it reports EXPECTED_KEY_MISMATCH and
fails, by design. "Supported topic with no page" returns 109 on this tree and
nothing in the data distinguishes the twenty that were chosen.

**Two things it will not tell you** [RAN]: `pages=0 lineage=0` is printed on a
dry run because the counts report what was WRITTEN; and `supported()` filters
`CATALOG == "DOT"`, so non-DOT topics are outside the input set and are never
mentioned. 53 supported topics sit outside it -- 30 FOX (expression functions),
23 ED (teaching concepts).

### Gate 6, THE REST OF IT -- nine steps, not four [RAN 2026-09-25]

The four commands above (inventory, validate, export-manifest, build-dry-run) are
the ENTRY to Gate 6, not the whole of it. Read off `manualgen.py --help` and run
end to end on 2026-09-25, the ladder to an applied manual candidate is:

    1  build-reference-candidate                 no args    -> REFERENCE_RUN
    2  build-curation-candidate                  no args    (disposition reads it)
    3  build-disposition-candidate               no args    -> DISPOSITION_RUN
    4  build-command-reference-candidate                    -> COMMAND_RUN
           --reference-run <1> --disposition-run <3>
    5  build-publication-structure-candidate     no args    -> STRUCTURE_RUN
    6  OWNER writes gate4_status_approval.json
    7  build-gate4-acceptance-plan                          -> the plan
           --command-run <4> --structure-run <5> --status-approval <6>
    8  OWNER writes gate4_apply_authorization.json
    9  apply-gate4-acceptance

**EVERY STEP MINTS ITS OWN `MANRUN-`, and steps 4 and 7 want EXACT ids from
earlier steps.** Capture each id as it prints; there is no "latest run" fallback
and a wrong id is a refusal, not a warning.

[RAN 2026-09-25] against harvest HELPMETA-20260924T195925Z:

    parity-review        exact_hash_match=0 section_parity_fail_rows=0
                         diff_review_rows=5 boundary_fail_rows=0
    reference candidate  topics=669 lines=18730/18730 commands=464 args=2378
                         syscmd=212 compact_aliases_resolved=8
                         command_without_topic=0            PASS
    curation candidate   topics 669/669 shelves=9, no duplicates, none unclassified
    disposition          dispositions=71/71 approved_section_topics=479   PASS
    command reference    pages=164/164 lineage_rows=6356 attention=2
                         local_path_hits=0 accepted_reader_mutated=0
                         website_mutated=0        PASS_CANDIDATE_ONLY
    structure candidate  ALREADY_NORMALIZED_NOOP, balance 24/24, diff 0 bytes,
                         dispositions proposed 0, accepted reader hash unchanged
                         EA2E12A9...A5A8F before AND after   PASS_CANDIDATE_ONLY

**`diff_review_rows=5` IS NOT FIVE SECTIONS.** It is the five REVIEW rows of
`mdo_227_parity_diff_reason_v1.csv`; `section_parity_fail_rows=0` and all 25
sections are present in BOTH artifacts. The hash mismatch survives CRLF
normalization, header stripping AND whitespace normalization, so it is real
content -- the rebuilt harvest reaching the prose -- and not a formatting
artifact. Misreading that number as five broken sections was a live error in
this session's own review.

**THE STATUS LEDGER HASH IS NOT RUN-SPECIFIC WHEN THE LEDGER IS EMPTY.** The
2026-09-25 structure candidate's `status_disposition_ledger.csv` is the 29-byte
string `status,note\nEMPTY,No rows.` and hashes to
`1A0DBD33E3EC2F01AFF9699367EE6E8E58B9294A081446CB33F87A9C7160D47F` -- BYTE FOR
BYTE the same hash recorded in DOCFLUSH-20260914-001's approval eleven days
earlier, because an empty ledger is an empty ledger. The approval's
`status_ledger_sha256` therefore binds the DECISION SHAPE, not the run; the
`structure_candidate_run` field is the only part that identifies which run was
approved. Worth knowing before treating a matching hash as evidence of anything.

### PREFLIGHT STEP 9 IS AN EXIT CONDITION, NOT AN ENTRY ONE

`derive_documentation_progress.py` reads the NEWEST `DOCFLUSH-*` directory and
requires `gate4_apply_authorization.json` in it, whose `plan_run` must start with
`MANRUN-`. That file is written at step 8 above -- AFTER Gate 6. So for any fresh
run, step 9 fails from the moment the run directory exists until that run's own
Gate 6 apply lands:

    no gate4_apply_authorization.json in ...runs\DOCFLUSH-<this run>.
      The manual candidate is the applied plan run; without the
      authorization record there is nothing to name.

**The preflight therefore cannot be all-green at the start of a run, by
construction.** This book presented it as an entry check without saying so, and
step 9 sat on the blockers list for a day while blocking nothing. Read steps 1-8
and 10 as entry; read 9 as the gate that says Gate 6 has not finished.

**ITS FIRST ACTUAL VERDICT, 2026-09-25, after the Gate 4 apply landed:**

     9. site present-state: documentation-progress check=FAIL --
        artifact differs from a fresh derivation
        website_static_pages_built and website_pagefind_pages_indexed NOT
        compared -- no build in scope. Every other measured field was.

That is the first time step 9 has said anything but UNRUN, and reaching it took
THREE layers, each masking the next: no `--site-root`, then Python 3.10 instead
of 3.12, then the missing authorization record. Name all three when explaining
this to the next agent -- a fix at any one layer looks like the whole answer.

**AND STEP 9 CANNOT BE SATISFIED WITHOUT A WEBSITE BUILD.** The remedy line says
"drop --check and pass --static-pages / --indexed-pages", and the tool REFUSES to
write without them:

    if not args.check and (args.static_pages is None or args.indexed_pages is None):
        print("... --static-pages and --indexed-pages are required to write the
               artifact. They come from this run's own build; a field carried
               forward silently is a field that rots.")

So a `next build` plus pagefind is a PREREQUISITE of step 9 turning green, and
this book did not say so. The refusal is correct and must not be worked around:
those two counts are the only fields in the authority that cannot be derived from
the ccode tree, which is exactly why they are the two that rot.

Read the FAIL before re-deriving. The artifact on disk is the 2026-09-14
derivation -- `as_of_date 2026-09-14`, `run_id DOCFLUSH-20260914-001`,
`canonical_harvest_tables_exported 10`, `carried_stale 4`. This run moved the
harvest to 14/0 and the run id, so a FAIL is EXPECTED here and re-deriving is
correct. That is a conclusion from reading the fields, not from trusting the
verdict; see 0e for why the check now prints them.

### Phase 7 -- review and close the dev-tree run (COOKBOOK numbering)

Review five states for pointer agreement -- candidate workspace, accepted/
canonical manifest, active reader artifact, publication manifest, and (retired
by the 2026-08-26 ruling) website projection. Write a closeout separating
dev-refresh / candidate / promotion / staging / commit / push.

**Do NOT claim a public push from here.**

### Phase 7 -> 8 entry check -- eight fail-closed rows

    E1  dev-tree run closed at Gate 7
    E2  HELP current + CMDHELPCHK reflection PASS
    E3  contracts 100%, catalog fallback 0
    E4  refcheck_v1 + normcheck_v1 PASS
    E5  HELP/META harvest re-exported AFTER the Phase-4 build   <- usually fails
    E6  command-catalog.mdx regenerated, fallback 0
    E7  HELP store backup exists, rollback path named
    E8  owner authorization for EACH distinct mutation

### Phase 8 -- publication ascent

Manual and website are CONSUMERS. Reuse the 9-gate
`DOCUMENTATION_TO_X64BASE_COM_ASCENT_V1.md`. The website step is now a LINK.

    $py12 tools\reports\regression_index.py `
        --write-mdx D:\dev\x64base-site\content\docs\engine\regression-and-proof-testing.mdx `
        --sha (git rev-parse HEAD)

---

# PART FOUR -- THE DISCIPLINE

### PHASE 8, THE WEBSITE HALF -- AN ORDER THAT IS CIRCULAR IF YOU GUESS [RAN 2026-09-25]

Preflight step 9 cannot pass without a website build, and the obvious order
deadlocks. Written down because this run walked into it twice, from two directions.

    documentation-progress-v1.json is the authority for ELEVEN of the site's 16
    freshness contracts. Re-deriving it REQUIRES --static-pages and
    --indexed-pages, which come from `next build` and `pagefind`. And
    `npm run build` runs check:freshness BEFORE next build.

    So: re-derive first  ->  11 contracts fail against pages that still quote the
    old authority  ->  build stops  ->  no counts  ->  cannot re-derive.

**THE ORDER THAT WORKS:**

    1  npm run build                      with the OLD authority in place. Pages
                                          match it, freshness passes, capture the
                                          two counts from the output.
    2  derive_documentation_progress.py   --static-pages N --indexed-pages M
    3  node scripts/check-site-freshness.mjs
                                          Read its `missing:` lines. They are the
                                          exact strings to write. Do NOT recompute
                                          them -- see 8g-quater.
    4  edit the named pages
    5  npm run build                      again, to confirm
    6  docpush_preflight.py --site-root   step 9 can now pass

**THE SAME TRAP CATCHES THE ENGINE ARTIFACTS, FROM THE OTHER SIDE.** The two
engine authorities have their own derivers and their own pages:

    npm run derive:pk-authority     -- --engine D:\code\ccode
    npm run derive:sqlsel-authority -- --engine D:\code\ccode

Both REQUIRE --engine and refuse to default it, which is correct -- see 8h.
Running them advances `engine.commit_short`, and two contracts require the PAGES to
carry that stamp verbatim, so the build stops until
`content/docs/engine/primary-keys.mdx` and `.../sqlsel-and-sql-conformance.mdx` are
updated. Measured 2026-09-25: the facts in both artifacts were unchanged and ONLY
the stamp moved, exactly as the engine-side advisory had been reporting for days.

    THE GENERAL RULE. Re-deriving ANY authority makes every page that quotes it
    stale in the same instant. Re-derive an authority and fix its pages as ONE
    step, never as two.

**VERIFY THE MANUAL LINKS BEFORE CALLING THE WEBSITE HALF DONE** (owner
instruction, 2026-09-25). Measured this run, all green:

    5 download targets    developer_manual_publication_v1.md, and
                          developer-manual-latest .html / .md / .pdf, plus
                          DEVELOPER_MANUAL_LATEST.json -- present in public/ AND
                          in the built out/. Checking public/ alone is NOT the
                          check: the build copies, and a copy can be missing.
    3 routes              /docs/dev/developer-manual, /docs/dev/manual-assembly,
                          /downloads -- each has out/<route>/index.html.
    2 branch links        docs/manuals/user/sqlsel.md and performance.md resolve
                          on origin/development. These track a BRANCH, so they
                          are the ones that can rot with no change to the site.
    8 pinned permalinks   pinned to be9350531, reachable from origin/main, so
                          they are publicly fetchable. Pinning is correct
                          practice and needs no maintenance.

The staged manual downloads are deliberately NOT advanced by a Gate 4 acceptance:
the manifest stays dated 2026-07-23 and two contracts bind the visible date and
counts to it. Gate 4 accepting 164 pages into the dev tree is a different
assembly, and advancing the downloads because the dev tree moved would be the
error.

**Counts are only valid while the page SET is unchanged.** 2026-09-25 measured 178
static and 171 indexed, both up one from 09-14. Prose edits to existing pages keep
the counts valid; adding or removing a page invalidates the counts captured at step
1 and needs a third build.

**And `website_pagefind_pages_indexed` is not a count of pages.** pagefind reports
`Found 235 files matching **/*.{html}` then `Indexed 171 pages`, because it ignores
pages with no `data-pagefind-body` element. So 178 built against 171 indexed is 7
pages deliberately outside search, and neither the field name nor the artifact says
so. The next person comparing the two will wonder.

## 7. The count discipline

1. **Name what is in a count.** A substring grep is not a count of the thing you
   named. `@dottalk\.` matched `@dottalk.file` and returned 578, not 229.
   **Print the DISTINCT MATCHED STRINGS, not just the number.**
2. **Guard the authority you NAME**, not the working set you happened to build
   (AIF-128: a guard named the registry and tested a three-source union, so the
   registry could vanish and the guard would pass).
3. **Check the freshness stamp of a REF, not just a report.** A nine-day-stale
   `origin/main` produced a drift audit claiming 29/70 when the truth was 9/64.
   **An audit against a stale baseline does not merely miss things; it INVENTS
   work.**
4. **Derive numbers and INCIDENTS; do not assert them.** A "real widow" that git
   showed never existed reached a commit message and a source docstring.
5. **An empty result is not a measurement.** Check the instrument RAN before
   believing what it says, especially when what it says is zero.
6. **An item is BLOCKED only when someone has tried it and been stopped.** If
   you can write the settling command down, it is QUEUED.

## 8. The named traps

### 8a. THE proxy family -- a check that cannot answer the question put to it

Six live instances found in v6 [RAN]:

    IMPLEMENT            answers "is there a registration"; read as "can this be typed"
    a manual sha256      answers "same newline?"; read as "same manual?"
    the banner           two halves, two staleness mechanisms, neither a freshness proxy
    dispatch_reachable   FALSE ON ALL 1,083 ROWS -- and it is NAMED after the right question
    pages=0              true about what was written; read as what was selected
    the DOT-only filter  silence; read as "nothing to page"

**Before writing an assertion, ask what OTHER world produces the same number.**
If the answer is "a healthy one" or "a broken one", it is not measuring what it
claims. Three of eight Gate 4 assertions failed this test in v5.

### 8b. A cheap red light is CAMOUFLAGE

The published manual is CRLF and the assembler writes LF, so
`dry_run_hash_matches_current_combined` can never be 1. A raw diff read 9,009 of
9,081 lines changed. `tr -d '\r'` first and it is 123 lines in two hunks -- and
the second hunk was 117 lines and two whole H1 sections. **Anyone who remembered
the newline problem and moved on would have shipped a manual missing two
sections.**

### 8c. Multiword registry keys are dead on arrival

`shell_dispatch` reads ONE token and looks that up. A registry key containing a
space can never match. `preprocess_for_dispatch` rewrites exactly two forms
(`SET RELATIONS ...` and `RELATIONS ...` -> `REL ...`). Fixed for BUILD in
`90e5dce0b` (AIF-131) by making BUILD a ROUTER. **Five survive** [RAN]:
`ERROR CLEAR`/`ERROR STATUS`/`ERROR TEST` (dead AND unserved -- there is no
`ERROR` parent) and `SET UNIQUE`/`SET RELATION` (dead but served, because SET is
registered and reads its own next token).

### 8c-bis. A CATALOG ENTRY AGES IN PARTS

A `dotref.hpp` entry is **name, syntax, summary, supported**, and those age
independently. `refcheck_v1.py` gates the NAME (does it resolve?) and nothing
gates the SYNTAX. Measured 2026-09-24: coverage PASS with 0 phantoms, while six
commands' syntax strings were behind their own `@dottalk.usage` headers and
`AUTODBF` said `TO` where the handler takes `FROM`.

**dotref.hpp is a MANUAL SEED LIST, so editing it for one reason does not make
it current for another. A dotref EDIT is not a dotref REFRESH.** The commit that
last touched it (`b6dabae63`) is NEWER than the workspace lane whose verbs are
still missing.

Generalise it: **when one artifact carries several claims, a gate on one claim
reads as a gate on the artifact.** Same shape as `IMPLEMENT` in 8a.

### 8d. Version guards and other false ceilings

    build_postbaseline_supported_command_pages.py:391
        if sys.version_info[:2] != (3, 12)     <- an EQUALITY; refuses 3.13 too

Measured [RAN]: byte-identical output on 3.10, 3.11, 3.12 and 3.13. All 35 files
carry `from __future__ import annotations` and parse clean under 3.8 grammar.
**The real floor is 3.9**, and it is stdlib not syntax --
`str.removeprefix`/`removesuffix` at `manualgen_lib/validation.py:58`,
`gate4_acceptance.py:150`, `publication_structure_candidate.py:61`.

**"It is a Windows exe" is a fact about a FILE. "Requires Python 3.12" is a fact
about an INTERPRETER. Neither is a fact about the QUESTION.**

### 8e-pre. A PSEUDO-MEMO POINTER IS A LINE ID, NOT PROSE

`HELP_ARTIFACTS.TEXT`, `.DETAIL` and `.EVIDENCE` are memo columns, and
`dbfread` does not follow memo blocks -- it yields the literal string
`<memo:unresolved ptr='N'>`. Two consequences, both of which have produced a
false measurement in this lane:

    1  COMPARING THEM COMPARES POINTERS, which are unique by construction, so a
       duplicate scan returns "0 duplicates" from a store full of duplicates.
       Recorded in FINDING_TWO_MINERS_COVER_THE_SAME_BLOCK_AND_THE_DEDUP_KEY_
       ENDS_IN_EVIDENCE.md, whose own first blast-radius run hit it.
    2  FILTERING THEM BY SUBSTRING excludes everything. On 2026-09-24 a count of
       artifacts with a non-empty EVIDENCE column filtered on `'memo' not in
       value` -- and EVERY value contains "memo", so the filter removed all
       4,548 rows and printed 0, which read as "provenance is gone".

**Test the POINTER VALUE (`ptr='0'` means empty), never the rendered string.**
And reassemble prose from `HELP_LINE` ROLE=TEXT parts, which is where the text
actually lives.

### 8e-bis. ONE POLARITY CHECKED IS NOT THE PROPERTY CHECKED

`check_site_artifacts.py` carries this in its own output, and it is the
sharpest instance of the proxy family anyone in this project has written down:

> it read "nothing on the site is false" for six days while four sentences
> across two pages described a scanner retired 2026-09-04 and a SQLSEL
> predicate form retired 2026-09-10. **Neither retirement changed a counted
> fact.**

And the site's own `npm run check:freshness` was green on BOTH tiers throughout:
tier 1 compares exact values, and no value was stale; tier 2 sweeps for a
SHIPPED capability described as planned or missing, **and its authority is a list
of what ships, so a page asserting a REMOVED surface has no entry to match.**

**A sweep for "claimed but absent" is not a sweep for "absent but claimed".**
Ask which direction your check runs in, and whether the other direction has an
owner. The four sentences were found by a person asking.

### 8e. Sandbox conduct [RAN]

    read-only git    fine WITH `--no-optional-locks`. A plain `git status`
                     TAKES THE INDEX LOCK and can wedge the maintainer's tree.
    git add          WORKS, and cannot unlink its own lock afterwards, so the
                     NEXT add fails until the zero-byte lock is moved aside.
                     Pass every path to ONE `git add`, or clear between adds.
                     AND AN ADD WHOSE STDERR YOU FILTERED IS NOT AN ADD YOU
                     VERIFIED -- one returned exit 0 and staged nothing.
    git commit       NOT from a sandbox: the pre-commit hook runs
                     repository_role_guard then prepush_gate, minutes of work.
    deleting         a sandbox CANNOT delete. `mv` orphans aside.
    building         YES. All of it. See part 3.

### 8g. A GATE SCOPED TO THE DIRECTORY WHERE THE DEFECT WAS FOUND

The proxy family's sharpest instance, because the checker was written FOR the
defect it now cannot see.

`check_manual_link_integrity.py` was built 2026-09-02 after 47 untracked command
pages were found under `command_reference_v1/commands/`. Its docstring is correct
about why that matters: an untracked publication means the acceptance ledgers are
the ONLY record of a change, so an apply cannot be reviewed as a diff, and the
diff review is this lane's entire defence. It asserts LINKED IMPLIES TRACKED and
NO UNTRACKED STRAYS. Both are the right assertions.

    :87  --manual-root default =
         docs/manuals/developer/manualgen/published/
         developer_manual_publication_v1/command_reference_v1

Measured 2026-09-25, the publication's tracking state on `development`:

    subtree                                    on disk  tracked  on main
    command_reference_v1/commands/*.md            164      164      183
    command_reference_v1/README.md                  1        1        1
    developer_manual_publication_v1.md              1        1        1
    sections/sections/*.md                         28        0       24
    appendices/*                                    4        0        4
    README.md            (publication root)         1        0        1
    ..._v1_appendices.md (publication root)         1        0        1

**The gate's scope is exactly and only the subtree that is fully tracked.** It
reads one README's 164 links; the 183 links the section files carry are outside
it. Its stray sweep globs `<manual-root>/commands/*.md` only, so 28 untracked
section files and 4 untracked appendices in sibling directories produce zero
strays. It prints PASS on every commit.

Nothing else covers it. `check_mandatory_tracked.py:62` builds its set from paths
the ENTRY_DOCS cite, so a file nothing cites cannot be declared and a file not
declared cannot fail. Its PASS on `sections/sections` is structural, not earned.

**THE RULE.** A gate built in response to a defect found in one directory must be
scoped to the CLASS of the defect, not to the directory it was found in.
Otherwise its green is a report on the region somebody already repaired. And have
it NAME ITS SCOPE in its own output: "164 link target(s) in the accepted README"
does not say which README, or that a second set of 183 links exists one directory
over.

### 8g-bis. THIS LANE KEEPS ITS GUARANTEES OUTSIDE THE REPOSITORY

Three instances, all measured 2026-09-25, and they are one disease:

    28 section files + 4 appendices + 2 publication-root files   UNTRACKED
        The published manual. Tracked on origin/main, not here.
    commit-fullstack-guards-and-conversion-proofs.ps1            UNTRACKED
        Holds the scoped-pathspec commit discipline AND the stale-index.lock
        handling with an age check. Both were needed twice in one session.
        Dated one-off for run COWORK-20260726-001, so it is a PATTERN to
        generalize, not a tool to run.
    manualgen_factory_common_v1.ps1                              UNTRACKED
        Zero consumers: `grep -l manualgen_factory_common_v1 *.ps1` returns
        only itself. Superseded by the Python manualgen toolchain. A DELETE
        candidate, not a track candidate. Its boundary text is still correct
        doctrine and belongs in a document, not a dead library.

**FOURTH INSTANCE, found 2026-09-25 in the WEBSITE tree, and it is the worst of
the four because this run quoted it as evidence.**

    scripts/check-site-freshness.mjs        MODIFIED, uncommitted since 09-14
    scripts/check-retirement-polarity.mjs   UNTRACKED since 09-15, 5657 B
    scripts/engine-retirements-v1.json      UNTRACKED since 09-15
    scripts/retirement-polarity-exemptions.json  UNTRACKED since 09-15
    site repo HEAD: b0bcccd67, 2026-09-23

The uncommitted diff to `check-site-freshness.mjs` IS the tier-1/tier-2 repair --
the one that moved the exit to the end of the file so a single stale number can no
longer silence the prose sweep. Its own comment records the measurement: every
build one morning failed on a date mismatch while two published pages denied a
shipped capability, and the sweep never ran once. **This run quoted that line three
times tonight** -- "Tier 1 FAILED above. Tier 2 runs anyway" -- as an example of an
instrument behaving well. It behaves because of a diff no clone has.

And the three untracked files are a WORKING retirement-polarity checker:

    node scripts/check-retirement-polarity.mjs
    Retirement polarity sweep: 0 assertion(s) over 2 retirement(s) and 1 stated
    exemption(s). Nothing on the site states a retired surface as live.

It records exactly the two retirements the standing engine-side advisory names --
`sql.verb.scanner` 2026-09-04 and `sqlsel.predicate.scanner` 2026-09-09 -- and
that advisory has been printing, on every commit for days, that this polarity is
the one nothing checks. **Somebody built it on 2026-09-15 and it has sat on the
floor for ten days**, wired into no npm script and no other script, so
`npm run build` has never called it.

The pattern is now unmistakable and it is not carelessness about git. It is that
this lane's instruments get built in the moment a defect is felt, used once by the
person who built them, and never enter the repository -- so the NEXT person meets
the defect again with no tool. Four instances, three repositories, one disease.

And the branch gap underneath all of it:

    files tracked on origin/main : 3174     on HEAD : 6542
    tracked on origin/main and NOT on HEAD : 803
    rev-list --left-right --count origin/main...HEAD : 99  1620

Development is 1620 ahead and 99 behind, and one of those 99 (`be9350531`,
2026-07-18) carries 19 command pages including USE, SELECT, LIST and WORKSPACE.
Either reconcile the 99, or record the publish-to-main step as a one-way door and
stop measuring development against publications it does not carry. 803 files is
too many to be an accident.

### 8g-quinquies. 140 OF 152 SITE PAGES HAVE NO CONTRACT, AND SOME SAY "CURRENT"

Owner instruction, 2026-09-25: a page that hand-lists a count "needs to be
annotated as a hand maintenance item until it is automated." Measured first,
because the size of the gap decides whether annotation is a note or a policy.

    content/**/*.mdx                          152 pages
    named as a target by a freshness contract  12
    covered by nothing                       140

The 12 are the whole of the automated surface. This lane's instinct is to trust the
site because `check:freshness` is green, and green covers 8 percent of the pages.

**FOUR uncovered pages were measured and all four had drifted:**

    /docs/dev/roadmap                 245 registered command keys, 300 with
                                      aliases, dated 2026-09-05. The engine's own
                                      normalization gate prints 247 and 302 on
                                      every commit that stages a tool. Two runs of
                                      drift beside a live measurement.
    /docs/dev/current-lanes           calls DOCFLUSH-20260825-001 the "Current
                                      run". Two runs stale. 239/239 keys, 670
                                      topics, 29,480 HELP lines.
    /docs/dev/documentation-progress  heading "Current measured state", every
                                      figure from August: 239/239, 63,217 harvest
                                      rows, 29,480 HELP lines, 171 static / 164
                                      indexed, manual candidate MANRUN-20260826.
    /docs/dev/full-stack-documentation-push
                                      heading "Current proof table" / "Reviewed
                                      current state", the same August figures.

HELP lines on two of those read 29,480 against a measured 18,730. **Off by 10,750,
under the word "Current", for eleven days** -- the contract-family collapse landed
on 09-14 and no contract reaches those pages.

**THE DISTINCTION THAT MATTERS.** 8e-bis says one polarity checked is not the
property checked. This is the other axis: a page can be wrong without any COVERED
page being wrong. `check-site-freshness` proves 12 pages agree with a generated
authority. It says nothing about the other 140, and its green line reads as though
it does.

**THE CONVENTION, applied to /docs/dev/roadmap this run.** A page carrying
hand-maintained counts gets a visible block saying so, and the block names three
things or it is decoration:

    1  that NO contract covers this page, so the numbers drift silently
    2  the COMMAND that re-measures them, if one exists
    3  the drift ALREADY OBSERVED, with both values and both dates

Point 3 is what makes it a maintenance item rather than a disclaimer. "These
numbers may be stale" is worth nothing; "these read 245/300 on 2026-09-05 and
247/302 on 2026-09-25, and here is the gate that prints the real ones" is a task.
Where no command can produce the number, the honest annotation says to delete the
count rather than let it age.

### 8g-quater. NEVER RECOMPUTE WHAT A CHECKER ALREADY COMPUTES

Third instance in one session, and the third was mine.

    9d60f46e1   the harvest exporter and its freshness checker each had their
                own _recode. Fixed by moving it into the exporter.
    (same run)  the progress deriver learned to name its fields; the preflight
                that prints it kept grepping two headline lines. Producer fixed,
                reader not.
    (same run)  bringing the SITE pages back into agreement, I reimplemented
                check-site-freshness.mjs's own template expansion in Python.

The third diverged from the original on two types:

    JS  String(false)        -> "false"     Python  str(False)     -> "False"
    JS  String(["A","B"])    -> "A,B"       Python  str(["A","B"]) -> "['A', 'B']"

It proposed rewriting `| In the default suite | false | false |` to `False`,
**breaking a contract that was passing**, and reported 222 phantom failures on
another page whose every inline code span matched a bare-placeholder template. A
non-greedy regex in the same script would have written
`status is reconciled through 2026-09-25026-09-14`. A dry run caught all three and
nothing was written.

**THE RULE.** When a checker already computes a value, do not recompute it. Run it
and read what it says. `check-site-freshness.mjs` prints

    missing: | HELP lines | 18,730 |

which is the literal string it wants, for every failing template. That output is an
API. Eight replacements taken verbatim from it landed first try, after a hand-rolled
expander had been wrong about three of them.

The general shape: a second producer of one fact is not a convenience, it is a
divergence with a delay -- and the delay is what makes it expensive, because all
three instances here read as working code until something compared them.

### 8g-ter. A TEST SUITE NO GATE RUNS IS NOT COVERAGE, IT IS A FILE

Found 2026-09-25 by running the suite, which is apparently not a routine act.

    tools/fullstack_docs/tests/   26 files, 104 tests
    invoked by prepush_gate.py, the AIF-082 portal gates, .githooks : NOWHERE

**7 of those 104 have been ERRORING for twelve days.**

    AttributeError: module 'harvest_promotion_plan' has no attribute 'PACKAGE_FILES'
      test_build_help_meta_harvest_promotion_plan.py   4 tests
      test_apply_help_meta_harvest_promotion.py        3 tests

`6ff960730` (2026-09-13, "record the authorized promotion of the canonical
HELP/META harvest") replaced `PACKAGE_FILES = tuple(REQUIRED_FILES) +
(MANIFEST_NAME,)` with `MANIFEST_NAMES = (...)`. Both tracked test files still
reference the old name. Nothing reported it because nothing runs them.

**The part that should sting.** The code those 7 tests cover is
`build_help_meta_harvest_promotion_plan.py` and its apply -- which is what THIS
RUN used to promote the canonical harvest in `38ec8986d`. A promotion that
mutated 5 canonical files was executed by code whose test suite had been erroring
for twelve days, and the run reported `rollback_performed=0` and looked clean.

The promotion was independently verified by its own plan/apply ledgers and the
E5 14/14 result, so this is not a claim that the promotion was wrong. It is the
observation that **the test suite contributed nothing to that confidence and
could not have**, and that eight new tests added in this very run join a suite
nobody runs.

    THE RULE. Coverage is what a gate runs. A test file that no gate invokes
    measures nothing about the tree -- it measures only that somebody once cared.
    Either wire the suite into the gate chain, or stop counting it as coverage in
    closeouts.

### 8h. THE INSTRUMENTS THAT BEHAVE -- copy these, not the green ones

This book names traps. It should also name the two checks that got it right,
because they are the pattern the others should be rewritten toward.

**The mass-change guard.** `prepush_gate.py:593`, threshold 60. This run staged
168 legitimate paths and the gate went to exit 3 with "large sets often mean an
accidental mass add or an un-sliced batch. Confirm the scope, then re-run with
--allow-mass if intentional." It fails on a shape that is USUALLY wrong. Every
gate this lane filed a finding against went green on a question it could not
answer; this one went red on one it could.

Its escape hatch is the better half. From its own comment at :481 -- the
pre-commit hook passes no arguments, so the only way to comply with "re-run with
--allow-mass" was `--no-verify`, which would have disabled the hard-block,
house-style and mandatory-tracked checks along with the warning. That is strictly
worse than the thing being acknowledged. So:

    Windows : set X64BASE_ALLOW_MASS=1  &&  git commit ...
    POSIX   : X64BASE_ALLOW_MASS=1 git commit ...

NARROW (one flag), SCOPED (one invocation), LOUD (announced in the output). Not a
bypass: hard-blocks still fail. **When a check must be overridable, build the
override rather than leaving --no-verify as the only door.**

**The deriver's refusal to guess.** `derive_documentation_progress.py` raises
rather than deriving when a sub-check gives no verdict:

    DeriveError command catalog check: could not find its verdict line
      A missing verdict is NOT a zero. Refusing to derive.

Measured: this is what stopped a field-level diff from being computed off-host,
correctly, because the catalog check needs the Windows engine. An instrument that
refuses is worth more than one that reports a plausible number.

### 8f. Staging history into history

Staging a previously-untracked file makes EVERY line an added line, so
`check_house_style.py` checks the whole file. Four historical records carry a
`U+FEFF` BOM and blocked a commit. **Do not run the normaliser on a file whose
hash is already bound** -- stripping the BOM from the accepted manual changes
`5ADFCDED...` to `89B6F551...` and falsifies a recorded acceptance. The gate's
own message offers the route: `git commit --no-verify` for deliberate imports.

## 9. Evidence and identity conventions

    AIF-NNN   lane/finding numbers. Claim: `coordination/aif/AIF-NNN.claim`.
              Intake row: `docs/ai-friendly/AI_INTERACTION_INTAKE_QUEUE_V1.md`.
              A NUMBER IS AN INTEGER; padding is display only (R126).
              Allocator: `tools/coordination/next_aif.py`.
    R-NNN     rulings. `tools/coordination/next_r.py`. 19 declared, 125 cited.
    MDO-NNN   manual documentation operations (the manualgen lane).
    META-NNN  SelfDoc metadata systems (24, in the registry).
    OI-NNN    open items, `check_open_items.py`.
    id-cite:ignore   quote an identity without spending it (`idcite.py`).

**Good Neighbor block** -- every lane document ends with: What changed / Whose
area / Authorization / How to verify / How to undo.

---

# PART FIVE -- STATE AND OPEN WORK

## 10. Where things stand (refreshed 2026-09-24; v6 closed 2026-08-26)

    HEAD 9c4179367, pushed. FOUR MORE DOCFLUSH RUNS have happened since v6 --
    DOCFLUSH-20260901-001, -002, 20260902-001, 20260914-001 -- and this book
    does not describe them. Read their run directories before assuming v6 is
    the latest state of the lane.

    The preflight currently FAILS on four steps: 4 (store older than exe),
    7 (harvest freshness), 9 (UNRUN, needs --site-root) and 10 (UNRUN, the
    check's own config). Step 8 PASSES with one named difference, DOT|COPY.

### v6's own closing state (2026-08-26)

    Gate 0    GREEN. Standing WARN: 167 rows STATUS=pending + CONFID=AUTHORITATIVE.
    Gate 4    validated twice; 6' green both times.
    Gate 5    BOUND by SHA (sandbox-built collector; host attestation open).
    Gate 6    ACCEPTED as candidate; boundary_fail_rows=0.
    Gate 7    CLOSED. 31 records entered history for the first time.
    Phase 8   NOT ENTERED. Out of scope for v6 by the GIGO ruling.

**The manuals are treated COLLECTIVELY by owner ruling, 2026-08-26**, pending a
hardening pass. On disk: developer 4,208 markdown files, student 1, user 1. Four
developer-manual assembly variants exist (4118/4597/4710/4597 lines,
26/26/29/26 H1s) and the ACTIVE pointer names the smallest.

## 11. Open, ranked -- refreshed 2026-09-25 after Gate 4 apply

**CLOSED by DOCFLUSH-20260924-001.** Every one is a commit, not a claim; see 0e.

    step 7   harvest freshness   FAIL 10/14  ->  PASS 14/14   (38ec8986d)
    step 10  anchor map          failing on its own config -> PASS (64040cc99)
    step 9   site present-state  UNRUN (3 layers) -> its first real verdict
    Gate 5   bound                                            (d5491107c)
    Gate 6   ladder run end to end, acceptance plan PASS_PLAN_ONLY mutations=168
    Gate 4   APPLIED, 168 rows, 0 findings, 0 rollback         (7cee40e5d)
    SYSARGS  no contract, no check -> both, 12 clauses, 8 tests (fc0b14725)
    exporter/checker one-function disagreement                 (9d60f46e1)
    validation_fail_rows  1 -> 0                               (a77e3b149)
    the "22 dead links"  ->  19 branch + 3 content, measured    (df698774a)
    derive_documentation_progress --check names its fields   (this run, see 0e)

**Still open, re-ranked. The first four are new and outrank what was here.**

1. **THE `tools/fullstack_docs/tests` SUITE IS RUN BY NO GATE, and 7 of its 104
   tests have been erroring for twelve days.** `PACKAGE_FILES` was renamed to
   `MANIFEST_NAMES` in 6ff960730 (2026-09-13) and both harvest-promotion test
   files still reference the old name. This run promoted the canonical harvest
   with that very code. Fix the 7, then wire the suite into the gate chain --
   in that order, because wiring in a red suite gets the wiring reverted. See
   8g-ter.
2. **A WEBSITE BUILD is a prerequisite of step 9 and nothing says so.** The
   authority cannot be written without `--static-pages` and `--indexed-pages`
   from this run's own build, and the tool correctly refuses. Until a flush runs
   `next build` plus pagefind, step 9 cannot go green no matter what else is
   fixed. Either fold the build into the ladder or record step 9 as reachable
   only in Phase 8.
3. **28 section files, 4 appendices and 2 publication-root files are UNTRACKED,
   and no gate asserts they should be tracked.** The one gate whose subject is
   exactly this is scoped one directory away. See 8g and 8g-bis. This is the
   defect underneath the 22 and it is bigger than the 22.
4. **Development is 99 commits behind origin/main; 803 tracked files exist there
   and not here.** Reconcile, or declare the publish a one-way door and stop
   measuring development against publications it does not carry.
5. **USER, BUILDVECTORS and VDISK have no command page on any branch.** The only
   genuine content debt in the 22, and each is the companion of one of the four
   sections main does not publish. Three pages, not twenty-two.
6. **`publication_state` carries the prior run's value when gate8 is absent.**
   The sibling of the defect fixed this run, and NOT covered by the 2026-09-25
   ruling, which named `first_open_entry` and `publication_authorized` only. An
   unpublished run currently reports the last run's publication state. Decide
   what it should read, then implement it beside `GATE8_OPEN_VERTICAL`.
7. **`news-current-status` binds a CURRENT measurement to a HISTORICAL record.**
   It requires the interpolated sentence "{website_command_keys} command keys
   matched to {website_command_rows_parsed} parsed contracts" to appear somewhere
   in `milestones.json`. Until 2026-09-25 the only entry carrying it was the
   2026-09-14 one, so the first change to the catalog count would have demanded
   EDITING A HISTORICAL NEWS ENTRY -- a citation, not a claim. Mitigated by
   anchoring the phrase in the current entry too; the contract still cannot tell
   the two apart. Same family as 8e-bis.
8. **140 of the site's 152 content pages are covered by no freshness contract,
   and four measured ones had drifted.** Two carry August figures under the
   heading "Current", with HELP lines reading 29,480 against a measured 18,730.
   `/docs/dev/roadmap` is corrected and annotated this run per the owner's
   instruction; `current-lanes`, `documentation-progress` and
   `full-stack-documentation-push` are NOT, and all three present a two-runs-old
   flush as current. Either bring them under contracts or annotate them the same
   way. See 8g-quinquies for the convention.
9. **The authority says "4 tables carried stale" while step 7 says "14/14
   match".** Both true, about different things. META_SYSENTVAR, META_SYSFLDDIC,
   META_SYSHELP and META_SYSMSG have been carried since May; META_SYSMSG has
   ZERO rows, so its match is vacuous. Either rename the field so it stops
   reading as a freshness verdict, or re-export the four.
10. **`command_reference_candidate.py:427` derives the page set from the accepted
   reader's OWN PRIOR LINKS**, with 164 hardcoded at :525. A command the reader
   never links can never get a page however completely the harvest and the
   disposition cover it -- and the tool's help text already says "the accepted
   reader's linked command pages", so the behaviour is documented and its
   consequence is not. Either derive from the approved topic set, or record at
   :427 that 164 is a FLOOR and not a measurement.
11. **A rehearsal harness.** Unchanged and still ranked high. Turn the owner's run
   from a DISCOVERY into a VERIFICATION: predict, then diff. Measured 2026-08-25,
   four of five headline numbers predicted exactly; the fifth is a real
   host/sandbox divergence and the reason a rehearsal must be a COMPARISON.
12. **A stated-impossibility check** -- flag any routing document asserting
   "cannot build / cannot run" with no adjacent measurement date. Would have
   fired on all four August false ceilings.
13. **dotref SYNTAX drift has no check.** `refcheck_v1.py` proves every entry
   RESOLVES and nothing proves the syntax still DESCRIBES the handler. Six
   commands are behind their own headers; AUTODBF is inverted (`TO` where the
   handler takes `FROM`).
14. **Add `destination_file_exists` and the branch name to the standalone section
   link gap ledger.** Its existing column,
   `present_in_accepted_reader_destination_set`, is a true and useless fact: it
   asks whether the reader links the destination when the question was whether
   the destination exists, and on which branch.
15. **`program_freshness_check.py` does not know `arctictalk_workbench`** (its
    manifest-coverage check is reporting its own staleness, as designed).
16. **Harden the manual** -- resolve the developer variants; decide what the
    student and user manuals should be. Treated COLLECTIVELY by owner ruling.
17. **Five open rulings** -- multiword registrations, `dispatch_reachable`, the
    CRLF/LF hash, the DOT-only page filter, the `!= (3, 12)` guard in
    `build_postbaseline_supported_command_pages.py`.
18. **`validate_metadata_system_registry.py` fails on 10 of 24 and nothing runs
    it.** It conflates "the registry is malformed" with "this attestation needs
    renewing", so it can only be green immediately after a re-pin.
19. **`tools/messaging`, 547 scripts, no index, SYSMSG still empty.**
20. **AIF-129** -- `status=` and `risk:` sub-block vocabularies.
21. **138 rows STATUS=pending + CONFID=AUTHORITATIVE** (was 167).
22. **Two untracked `.dtschema` files**; no sysargs schema exists at all.
23. **Six em-dashes in `helpdata_messages.cpp`**, against house style.
24. **ARG_ID remedy (1) at `metacollect.cpp:1087`** -- the collapse of keyword
    and placeholder that the new SYSARGS uniqueness clause now fails on.
25. **Two DOCFLUSH runs open with no Gate 7** -- 20260902-001, 20260914-001.
26. **`binding` will never be clean and must be EXPLAINED, not fixed.**

### 11b. My own errors this run, recorded because the pattern is the lesson

Not housekeeping. Every one of these was caught by the owner asking a question,
and the ratio is the point.

    the 22 dead links, cause    blamed R127's --expected-topic-key allow-list.
                                Wrong generator entirely -- that belongs to
                                build_postbaseline_supported_command_pages.py.
    the 22 dead links, scope    titled it "none of them exist" after measuring
                                ONE branch. 19 of 22 existed in two places.
                                Fixed only because the owner asked "missing from
                                github, the site, the manual?"
    five environment errors     $py12 without &; `py -3.12` while standing in
                                the site tree; bare `python`; a stray Z from
                                -Format s; blocks with no cd. Drew explicit
                                reproof. The rule was ALREADY in CLAUDE.md and
                                I had not read it. Now also 0c.
    pasted source as commands   quoted the internals of
                                commit-fullstack-guards-and-conversion-proofs.ps1
                                as a runnable block. $lock and $ClearStaleLock
                                exist only inside that script and the `...` was
                                a literal ellipsis. The owner ran it. This is
                                rule 3 of 0c violated by the author of 0c.
    a stale index.lock          my own `git status` hit a 115s ceiling and was
                                killed, leaving a 0-byte .git/index.lock that
                                blocked the owner's next FOUR commands. Read-only
                                intent is not read-only effect. Sandbox git calls
                                must be scoped tightly enough to finish.
    diff_review_rows=5          read as five differing sections. It is five
                                REVIEW rows of the parity CSV;
                                section_parity_fail_rows=0, all 25 present.
    four near-misses            nearly filed the reader manual as a phantom (it
                                is at repo root); nearly chased a ghost prepush
                                FAIL from old scrollback; assumed sections/sections
                                was a stray duplicate tree (it is the real
                                layout); assumed the status ledger hash was
                                run-specific (an empty ledger is an empty ledger).

**The lesson, stated once:** every one of these was a conclusion drawn from one
measurement when a second was cheap. The count discipline in part 7 says derive
don't assert, and an empty result is not a measurement. Add: **one tree is not the
tree, and one branch is not the repository.**

## 12. For CODEX, planning the AI Portal

The portal's job is ROUTING: getting an arriving agent to the truth in the
mandatory reading order, without a trigger it has to know to fire.

    labtalk/ai_portal/AI_TIER1_SEED_V1.md     16,384 B HARD CEILING, raised
                                              from 8,192 on 2026-09-04.
                                              8,718 B used, 53%.
                                              Invariants and POINTERS only.
                                              Adding requires DEMOTING, and
                                              demoting means MOVING, not restating.
    labtalk/ai_portal/TIER0_STATE.md          generated
    labtalk/registries/portal_recall_graph.yaml  61 nodes, 18 triggers
    labtalk/ai_portal/recall.py               `recall.py <trigger>` -> smallest
                                              working set, MEASURED in bytes
    RECALL_FALLBACK_TABLE_V1.md               GENERATED from the graph. Never
                                              hand-edit; `recall.py --write-fallback`
    CLAUDE.md / AI_README.md / AI_PORTAL.md   the entry documents

**The defect the portal keeps producing, and the one to design against:** AIF-130
corrected `AI_README.md` and did not sweep. The same false ceiling stayed live in
`CLAUDE.md` -- which is where a Claude session STARTS, is tier 1, and whose node
was **the first thing `trigger.work_in_sandbox` returned.** The trigger added as
the fix was leading with the falsehood it was meant to route around. Five agents
re-derived the same fact.

**Three structural lessons for the plan:**

1. **A correction that lands somewhere other than where the reader ARRIVES is
   not a correction.** Eleven documents cited the correcting document and the
   corrected document was not one of them.
2. **A router is only as true as its LABELS, and an anchor is a COUPLING.** The
   graph node's label carried the falsehood independently of the file, and the
   anchor broke when the heading was fixed. Both must be corrected with the target.
3. **GENERATED MIRRORS ARE THE RIGHT DESIGN.** The fallback table had the stale
   label verbatim and ONE regeneration fixed it. A hand-copied table would have
   had to be found first.

**And the thing nothing currently does:** no gate checks that a routing document
is TRUE. `cited-paths` checks that a path is tracked; `check_seed_budget` checks
size; nothing checks that "you cannot build" is still a fact. Item 3 of part 11
is the smallest useful version of that.

## Good Neighbor

    What changed  : one new document. No source, no data, no store, no tool.
    Whose area    : lane full_stack_documentation / AIF-068.
    Authorization : member.derald, 2026-08-26 -- "Give me a detailed recipe book
                    for all of the work you have done AND know about in the full
                    stack document push."
                    REFRESH: member.derald, 2026-09-24 -- "refresh".
    Refresh miss  : the FIRST pass of this refresh claimed "every [RAN] figure
                    re-measured" and had not checked the ENGINE VERSION, which
                    had moved 0.6 -> 1.1. Caught from a gate line in the commit
                    that carried the refresh. A claim of completeness is itself
                    a claim, and this one was not measured before it was made.
    2nd revision  : member.derald, 2026-09-25 -- "update the recipe book with
                    every thing we have corrected or need corrected", and then
                    "we have two objectives, update data, and improve the
                    fullstack push with every run". The second is now 0d, stated
                    as an objective rather than a hope, with a mechanical test.
                    NEW in this revision: 0d (the two objectives), 0e (this run's
                    improvement ledger, nine commits), 8g (a gate scoped to the
                    directory where the defect was found), 8g-bis (this lane
                    keeps its guarantees outside the repository), 8h (the
                    instruments that behave -- copy these, not the green ones),
                    11b (my own errors this run). REWRITTEN: part 11 entirely,
                    and the step 9 section now records its first real verdict and
                    that a website build is a prerequisite nobody had written
                    down.
    Refresh scope : every [RAN] figure re-measured against HEAD 9c4179367. The
                    store, the SOURCE/KIND/CATALOG distributions, the metadata
                    tables, the tool counts, the add_executable total, the seed
                    ceiling, the R and AIF ranges, and the preflight step table.
                    Sections 2b-bis, 8c-bis, 8e-pre and 8e-bis are NEW. Part 11
                    is re-ranked and records that two of its top three are BUILT.
                    Corrected IN PLACE so there is ONE answer per number; the
                    movement is in the refresh ledger at 0b, which is history
                    rather than a second answer.
    How to verify : every [RAN] figure is reproducible by the command beside it.
                    Table shapes: read the DBFs with tools/fullstack_docs/dbfread.py.
                    Tool counts: ls the directories named in part 4.
                    The phase ladder: FULL_STACK_DOCUMENTATION_FLUSH_COOKBOOK_V2.md
                    (V1 SUPERSEDED 2026-09-02)
                    and FULL_STACK_DOCUMENTATION_RUNBOOK_V1.md, which is also
                    where the Phase 7 numbering collision is visible.
    How to undo   : delete this document. It asserts nothing the tree does not.
