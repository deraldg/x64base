# The Full-Stack Documentation Push -- recipe book

    Version   : v1, 2026-08-26
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

**RULING 2026-08-26: the website LINKS to the manual; it does not project it.**
That retires "website projection" as a state the pipeline must keep in sync.

## 2. The data layer -- what actually holds the documentation

### 2a. The HELP store -- `dottalkpp/data/help/` [RAN]

Six tables plus memo sidecars. Row counts are the live store as of
2026-08-26 01:11:28.

    TABLE            rows    fields
    HELP_TOPIC        667    TOPICID, TOPICKEY, CATALOG, TOPIC, TOPICTYPE,
                             STATUS, IMPLEMENT, SUPPORTED, PRIMARY, CONFID,
                             TITLE, SUMMARY, SECTIONS, LINES
    HELP_LINE       29268    LINEID, ARTID, TOPICKEY, CATALOG, TOPIC, KIND,
                             SOURCE, CONFID, SEVERITY, NAME, ROLE, LINE_NO,
                             PART_NO, TEXT
    HELP_SECTION    14601    SECTID, ARTID, TOPICID, TOPICKEY, KIND, SOURCE,
                             CONFID, SEVERITY, NAME, ORD, NLINES
    HELP_ARTIFACTS  14601    ID, CATALOG, COMMAND, CMDKEY, OWNER, KIND, SOURCE,
                             CONFID, SEVERITY, NAME, ORD, TEXT, DETAIL, EVIDENCE
    COMMANDS          462    ID, CATALOG, COMMAND, CMDKEY, IMPLEMENT,
                             SUPPORTED, USAGE, VERBOSE
    CMD_ARGS         2368    ID, CATALOG, COMMAND, CMDKEY, ARG, USAGE, VERBOSE

Plus `*_LOCALE` companions (HELP_TOPIC_LOCALE, HELP_LINE_LOCALE,
HELP_SECTION_LOCALE, HELP_ARTIFACT_LOCALE) and `.dbt` memo files
(`commands.dbt`, `cmd_args.dbt`, `help_artifacts.dbt`).

**`TOPICKEY` is `CATALOG|TOPIC`** -- `DOT|APPEND`, `FOX|FILE`, `ED|LOOPS`.
The join every consumer depends on is HELP_LINE.TOPICKEY -> HELP_TOPIC.TOPICKEY.

**CATALOG values seen** [RAN]: DOT 23330, SYSTEM 2637, FOX 1247, ED 842,
EDU 832, UI 132, EXT 91, DEV 89, INTERNAL 68 (HELP_LINE row counts).

**SOURCE values -- the provenance layer, and it is the most useful column in the
store** [RAN]:

    USAGE_CONTRACT  15198   mined from `@dottalk.usage` blocks in C++ source
    SOURCE_MINER     7644   leading comments and source facts
    SHARED_MSG       2637   the runtime message catalog
    DOTREF           1006   the hand-curated command catalog, COMPILED IN
    CURATED_DOC       868   hand-written documentation
    EDREF             786   the educational catalog, COMPILED IN
    FOXREF            667   the FoxPro-compat catalog, COMPILED IN
    REGISTRY          462   reflected from the C++ command registry

**KIND values** (15) [RAN]: SYNTAX 6083, USAGE 6031, SOURCE_FACT 4302, NOTE 3743,
SUMMARY 2391, RELATED 1980, STATUS 1560, EXAMPLE 1078, MESSAGE 1009,
ARGUMENT 495, ERROR 478, ALIAS 53, WARNING 45, HINT 19, DEPRECATION 1.

    NOTE: there is no RISK kind. `risk:` sub-blocks appear in 206 source files
    and reach ZERO rows in the built store (AIF-129).

### 2b. The METADATA store -- `dottalkpp/data/metadata/` [RAN]

Eight tables. This is the SelfDoc metadata layer; it is NOT the HELP store and
the two are built by different programs.

    SYSCMD       212  CMD_ID, CAN_NAME, TYPE, VIS, HANDLER, ACTIVE
    SYSFUNC       75  FUNC_ID, CAN_NAME, DISP_NAME, DEF_LOCALE, REGION_ID,
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

27 `add_executable` targets exist in total. `tools/coordination/program_freshness_check.py`
requires every one to be DECLARED or EXCLUDED by name.

## 4. Python tooling, by role

Run everything with the host `$py12`:
`C:\Users\deral\vcpkg\installed\x64-windows\tools\python3\python.exe`.
Most tools run on 3.9+; two carry version guards (part 8d).

### 4a. Gate and preflight -- `tools/coordination/` (15) and `tools/staging/` (23)

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

### 4b. The doc stack -- `tools/fullstack_docs/` (50)

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

    tools/manualgen/       5      manualgen.py + 4 builders (part 6)
    tools/selfdoc/         7      the SelfDoc validators (part 5)
    tools/comments/        5      source-comment escrow and reharvest
    tools/contracts/       1      contract_scan.py
    tools/reports/        10      regression_index.py writes the website MDX
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

    1  @dottalk.file coverage 100%, uncovered 0                    HARD
    2  website catalog matches the registry                        HARD (needs --catalog)
    3  plan doc is ASCII                                           advisory
    4  help_build_order_check: binding / exe newer than catalogs /
       store newer than exe / legacy before store / generation
       stamp / store integrity / status coherence                  HARD
    5  help_store_check: every HELP_LINE row names a topic         HARD
    6  program_freshness_check: every program newer than its
       sources; python version guards; manifest coverage           HARD

**Re-run it after EVERY rebuild.** `--no-git` skips the worktree-binding check.

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

**THE TWO REBUILD COMMANDS. Type them at the `.` prompt, ONE AT A TIME.**

    . cmdhelp build legacy
    . cmdhelp build . d:\code\ccode\src

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
    $out = '<run>\metacollect_phase'
    & $mc --source-root D:\code\ccode\src --include-dev-commands --sysargs-include-keywords `
          --syscmd-import-out  "$out\SYSCMD_IMPORT_candidate_v1.csv" `
          --sysfunc-import-out "$out\SYSFUNC_IMPORT_candidate_v1.csv" `
          --sysargs-import-out "$out\SYSARGS_IMPORT_candidate_v1.csv" `
          > "$out\metacollect_facts_v1.csv" 2> "$out\metacollect_stderr_v1.txt"

    & $mc --source-root D:\code\ccode\src --compare `
          --compare-out "$out\metacollect_compare_v1.csv" `
          --metadata-root D:\code\ccode\dottalkpp\data\metadata

v6 results [RAN]: SYSCMD 229, SYSFUNC 75, SYSARGS 1066 (baselines 226/74/959).
`--compare`: 192 WARN, 189 METADATA_ONLY, 3 SOURCE_ONLY.

**Candidate CSVs are gitignored** (`.gitignore:342`), so Gate 5 binds them BY
SHA-256 in a tracked document. The governing contract is
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

    $py12 tools\fullstack_docs\export_help_meta_harvest.py --repo-root . --out <candidate dir>
    -> 14 tables, 62,570 rows

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

## 10. Where v6 left things (2026-08-26)

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

## 11. Open, ranked -- the input CODEX should plan against

1. **A content-level assertion in the preflight.** 6' is membership only; the
   content diff is still hand-run and it saw the substantive half of v6.
2. **A rehearsal harness.** The sandbox can build every program and run the whole
   push. Turn the owner's run from a DISCOVERY into a VERIFICATION: predict, then
   diff. Measured on 2026-08-25 -- four of five headline numbers predicted
   exactly, and the fifth (29263 vs 29265, LEGACY arg rows 2609 vs 2363) is a
   real host/sandbox divergence and the reason a rehearsal must be a COMPARISON.
3. **A stated-impossibility check** -- flag any routing document asserting
   "cannot build / cannot run" with no adjacent measurement date. Would have
   fired on all four of v6's false ceilings.
4. **Harden the manual** -- resolve the developer variants; decide what the
   student and user manuals should be.
5. **Five open rulings** -- multiword registrations, `dispatch_reachable`, the
   CRLF/LF hash, the DOT-only page filter, the `!= (3, 12)` guard.
6. **`validate_metadata_system_registry.py` fails on 10 of 24 and nothing runs
   it.** The check conflates "the registry is malformed" with "this attestation
   needs renewing", so it can only be green immediately after a re-pin.
7. **`tools/messaging`, 547 scripts, no index, SYSMSG still empty.**
8. **AIF-129** -- `status=` and `risk:` sub-block vocabularies. `risk:` is in 206
   files and reaches zero store rows.
9. **56 owner topics that can never render** (AIF-126).
10. **`binding` will never be clean and must be EXPLAINED, not fixed.**

## 12. For CODEX, planning the AI Portal

The portal's job is ROUTING: getting an arriving agent to the truth in the
mandatory reading order, without a trigger it has to know to fire.

    labtalk/ai_portal/AI_TIER1_SEED_V1.md     8,192 B HARD CEILING (89% used).
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
    How to verify : every [RAN] figure is reproducible by the command beside it.
                    Table shapes: read the DBFs with tools/fullstack_docs/dbfread.py.
                    Tool counts: ls the directories named in part 4.
                    The phase ladder: FULL_STACK_DOCUMENTATION_FLUSH_COOKBOOK_V2.md
                    (V1 SUPERSEDED 2026-09-02)
                    and FULL_STACK_DOCUMENTATION_RUNBOOK_V1.md, which is also
                    where the Phase 7 numbering collision is visible.
    How to undo   : delete this document. It asserts nothing the tree does not.
