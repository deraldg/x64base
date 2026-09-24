# Gate 5 -- Phase 5 candidates BOUND, and host and sandbox agree byte for byte

    Run           : DOCFLUSH-20260924-001, member.ai.claude.cowork for member.derald
    Gate          : 5. Candidate binding. NO import, NO promotion, NO mutation.
    Emitted       : 2026-09-24, host `build\Release\metacollect.exe` (MSVC)
    Status        : BOUND, review-needed.
    Closes        : the one open item on DOCFLUSH-20260825-001's Gate 5 binding,
                    and the SYSARGS +11% carried there.

## 1. What is bound

Gitignored by the `.gitignore` rule `docs/maintenance/lanes/**/runs/**/*.csv`,
as the METACOLLECT runbook requires. **Binding by SHA is what makes them
citable**, and this document is the tracked link.

    sha256                                                            rows   bytes  artifact
    45dc272ee59d1550d573ef577e6147b6a45e0b5228b0a43009b90b94855b4967   231   14170  SYSCMD_IMPORT_candidate_v1.csv
    6672a676b549be9b4eb4c31e4c60938dbd0b71d57838a5b34742f3c8e134f87f    79   40060  SYSFUNC_IMPORT_candidate_v1.csv
    82f5e600a6233e2641536884d9bc9fde9cd782e717d67290fdc065eef6eadc1e  1180  311297  SYSARGS_IMPORT_candidate_v1.csv
    eb13a240f772940aa16451711e0c59cacca4921b752baf0cdd5e70f3979f3d5e  1210  308710  metacollect_facts_v1.csv
    3490c6794f68fe672fdebdafc54ac35586f4aaa368acc981e23f363749c1d193   193   27184  metacollect_compare_v1.csv

**The rule is cited by TEXT, not by line.** Every prior document in this lane
cites it as `.gitignore:342`, which was true when written and is false now --
see section 9.

Movement since the 2026-08-26 emit, against a tree 167 `.cpp` files later:

    SYSCMD    229 ->  231   (+2)
    SYSFUNC    75 ->   79   (+4)   accounted, section 7
    SYSARGS  1066 -> 1180  (+114)  accounted, section 8

Live tables for scale (DBF header record counts):

    SYSCMD.dbf   212      candidate 231
    SYSFUNC.dbf   79      candidate  79   equal
    SYSARGS.dbf  249      candidate 1180  <- the live args table holds 21% of
                                              what source declares

## 2. THE OPEN ITEM FROM AUGUST, CLOSED -- and closed positively

The previous binding carried one caveat: the candidates were emitted by a
SANDBOX-built metacollect and *"whether the host MSVC binary produces
byte-identical output is UNPROVEN"*. Settled by building both against the SAME
source and comparing:

    host    build\Release\metacollect.exe          MSVC
    sandbox g++ 11.4, -O0, -j6, dt_meta TU list at CMakeLists.txt:771, /tmp

    SYSCMD_IMPORT_candidate_v1.csv    BYTE-IDENTICAL
    SYSFUNC_IMPORT_candidate_v1.csv   BYTE-IDENTICAL
    SYSARGS_IMPORT_candidate_v1.csv   BYTE-IDENTICAL

**No divergence.** The v6 resume state recorded a real host/sandbox gap in the
STORE (29,263 against 29,265); the metadata lane has none.

### 2a. The facts CSV "differed" by 2,420 lines and did not differ at all

    raw diff                                              2,420 lines
    after normalising the source-root spelling and
    the line endings                                      IDENTICAL

Two artifacts, and **neither belongs to metacollect**:

1. The host was invoked with `--source-root D:\code\ccode\src` and the sandbox
   with its POSIX mount path, so every `source_file` cell carries a different
   absolute prefix and separator.
2. **CRLF.** The facts CSV goes to STDOUT and PowerShell's `>` applied CRLF. The
   three import CSVs metacollect writes ITSELF came out byte-identical, which is
   the proof that the line endings are the SHELL's and not the tool's.

**A redirect is part of the measurement apparatus.** This is the manual's
CRLF/LF hash trap (recipe book 8b) in a second place, and it would have read as
a 2,420-line toolchain divergence to anyone who stopped at the raw diff.

### 2b. Three emitters wrote the compare file and it is one file

The compare was first produced by a metacollect built with g++ 11.4 on the
workstation's local Linux VM against `D:\code\ccode` directly. Before trusting
its output, that binary re-emitted the three import CSVs and they came out
**BYTE-IDENTICAL to the host MSVC emit already bound in section 1** -- an
emitter has to be shown to be the same emitter before a fourth output of it is
citable.

Then the owner ran the compare from the HOST binary at 18:13, which overwrote
that file. It came back with the same sha256:

    2026-08-26 18:0x   host   build\Release\metacollect.exe   MSVC
    2026-09-24 17:5x   local  g++ 11.4, workstation Linux VM
    2026-09-24 18:13   host   build\Release\metacollect.exe   MSVC
    3490c679...c1d193   27,184 bytes   all three

So the citation does not rest on the sandbox argument at all: **the host
produced this file itself, and it matches what the host produced 29 days ago.**

## 3. Contract compliance, checked before binding

Against `METACOLLECT_SYSCMD_CANDIDATE_CONTRACT_V1.md`:

    "repeated runs over unchanged source must be byte-identical"
      second sandbox emit, all three candidates      BYTE-IDENTICAL
    "rows sort by CAN_NAME"                          True, 231 rows
    unique CMD_ID / unique CAN_NAME                  True / True
    TYPE reserved set                                {command, syntax-command}
    VIS default/developer                            {public, developer}
    field order CMD_ID,CAN_NAME,TYPE,VIS,HANDLER,ACTIVE   exact

**The uniqueness clause covers SYSCMD and stops there.** Section 8 is what that
costs.

## 4. The candidate is a STRICT SUPERSET of the live table, and the excess is named

    candidate 231   live SYSCMD.dbf 212
    live rows with no candidate row :   0
    candidate rows not live         :  19

**Zero live-not-candidate is the load-bearing half** -- an import would orphan
nothing. And 19 is exactly the figure `normcheck_v1.py` reports as
*"registered commands absent from SYSCMD: 19 -- policy exclusions (dev/subcmd),
not gated"*. Two instruments, one number, reached independently. Named rather
than counted:

    APPGUI BUILD DDICT EVALDIFF GROUPCOMMIT SIMPLEBROWSER SMARTBROWSER SMTP
    WORKDESK                                    newer or dev-surface commands
    SETCASE SETCDX SETCNX SETFILTER SETINDEX
    SETLMDB SETNEAR SETORDER                    compatibility targets behind
                                                the routed SET forms
    SET RELATION  SET UNIQUE                    <- AIF-131's two surviving
                                                multiword registrations

**AIF-131 reads straight off this list.** `SET RELATION` and `SET UNIQUE` are
the dead-but-served multiword keys, present in the candidate and absent from the
live table. And the ERROR trio is NOT here, because `compact_command_name` folds
`ERROR CLEAR` into `ERROR_CLEAR` -- the August finding, reproduced on a tree 167
files later without being looked for.

## 5. What this binding does NOT authorize

No import into `SYSCMD.dbf`, no CDX, no LMDB, no HELP mutation, no manual
publication. The contract reserves any load to a separate reviewed mutation gate
with backup, before/after readback, rollback evidence and explicit authority.
Bound means citable and reproducible, nothing more.

## 6. The compare did not move by ONE BYTE in 29 days

    metacollect --source-root <src> --compare --metadata-root dottalkpp/data/metadata
    exit 0, 192 issue(s), all severity WARN
    [RAN on the host, 2026-09-24 18:13: "METACOLLECT compare: 192 issue(s)"]

      187  METADATA_ONLY  command    live SYSCMD row with no source-catalog fact
        2  METADATA_ONLY  function   STRCAT, TRIM
        3  SOURCE_ONLY    command    SET FILTER, SET INDEX, SET ORDER
                                     (src/cli/command_catalog.cpp)
    SYSMSG.dbf has zero rows and warned, as in August.

    cmp  DOCFLUSH-20260825-001/.../metacollect_compare_v1.csv
         DOCFLUSH-20260924-001/.../metacollect_compare_v1.csv     BYTE-IDENTICAL

Not "the same count" -- **the same 27,184 bytes, all 193 lines, same order**.
Twenty-nine days, 167 `.cpp` files, +114 SYSARGS rows, and this instrument
reports the identical file.

**And that is explained, not lucky.** Both sides of the command compare are
frozen in git:

    src/cli/command_catalog.cpp   last touched 3706da78c  2026-07-25
    SYSCMD.dbf                    last touched bc22f0472  2026-08-24

A compare between two files that have not changed returns what it returned
before. The correct reading of a flat instrument is *"its inputs did not move"*,
which is a fact about the inputs; it is not evidence that the lane is stable.

**Be careful what 187 means.** The compare's source side is the SOURCE CATALOG
(`command_catalog.cpp`), a different extractor from the seed emit's REGISTRY
scan. 187 is not "187 commands vanished"; it is "187 of 212 live SYSCMD rows
have no counterpart in the source-catalog extraction". The three SOURCE_ONLY
rows are multiword `SET` forms -- **AIF-131's family in a third catalog**, with
sightings now in the registry, the HELP store and the source catalog, and it has
not grown.

*(Correction carried back: `PHASE5_PREFLIGHT_AND_FINDING_V1.md` s7.3 labelled
the 189 as `METADATA_ONLY command` above a separate `2 ... function` line, which
totals 194 against its own stated 192. 189 is the METADATA_ONLY total across
both domains; the command figure is 187. `TRIAGE_LOG_20260824_V1.md` had it
right. Fixed in place.)*

## 7. SYSFUNC +4: accounted, by name and by commit

    94782c434  2026-09-05  The function catalogue learns the four cursor functions

Candidate 75 -> 79 and live `SYSFUNC.dbf` 75 -> 79, and `METADATA_ONLY function`
stayed at exactly two (`STRCAT`, `TRIM`). The four landed on BOTH sides in one
commit, which is the shape a healthy catalogue change has. No action.

## 8. SYSARGS +114: accounted -- and the accounting found a defect

    rows              1066 -> 1180   (+114)
    distinct ARG_ID   1054 -> 1166   (+112)
    added keys 143, removed keys 31, and 74 surviving keys changed a field

The net is 17 commands, not a mystery:

    WORKSPACE 44   USER 22   SQLSEL 18   REGRESSION 13   UPDATE 6   INSERT 6
    SQLHELP 6   SQLERASE 5   WHERECACHE 5   REL 4   GROUPCOMMIT 3   ERSATZ 2
    COPY 2   SORT 2   COUNT 2   REPLACE 2   SQLVER 1
    removed: AGGS 10   USE 9   SQLSEL 6   ERSATZ 5   REL 1

That is a month of WORKSPACE, USER and SQL work showing up in the usage
contracts -- AIF-169's SQLSEL/REL lane is visible in it by name. The August
+11% has the same shape (`aug05 -> aug26`: +109 -5, top owners USER 74,
WORKSPACE 27). **Two consecutive double-digit moves, both of them ordinary.**
The carried item from August is closed.

### 8a. ARG_ID COLLAPSES KEYWORD AND PLACEHOLDER -- 14 collisions, and growing

Rows exceed distinct `ARG_ID` because **14 ARG_IDs are emitted twice with
different content**, and this is not new:

    2026-08-05   959 rows,  950 keys,   9 collisions
    2026-08-26  1066 rows, 1054 keys,  12 collisions
    2026-09-24  1180 rows, 1166 keys,  14 collisions

    ARG_BBS_SUBJECT  ARG_CODASYL_SET  ARG_ERASE_TABLE  ARG_FIELDMGR_NAME
    ARG_FIELDMGR_TYPE  ARG_IDX_TAG  ARG_RETRO_STYLE  ARG_SET_FILE
    ARG_SET_PATH  ARG_SQLSEL_SELECT  ARG_SQLSEL_VALUES  ARG_USER_KEY
    ARG_USER_SECRET  ARG_WORKSPACE_FILE

They differ in `ARG_KIND` (14 of 14), `VAL_SHAPE` (14 of 14) and `NOTES` (11 of
14). `ARG_SET_PATH`, in full:

    keyword     literal   usage=SET PATH <slot> <path>
    placeholder path      usage=SET DEVICE TO FILE <path> ; usage=SET PATH <slot> <path>

**The same word in two roles in one command's own usage text.** `SET PATH` the
keyword and `<path>` the placeholder; `USER ... KEY` and `<key>`.

The cause is two lines apart in the emitter:

    src/meta/metacollect.cpp:1084   aggregate_key = command | arg_kind | arg_name
    src/meta/metacollect.cpp:1087   arg_id        = "ARG_" + command + "_" + arg_name

**The aggregation key has three components and the identifier it emits has
two.** metacollect knows the distinction, keeps the rows correctly apart, and
then throws the distinction away in the name.

Reachable only with `--sysargs-include-keywords` (`metacollect.cpp:1081-1083`
drops keyword tokens otherwise) -- and that flag is in the standard emit
recorded in the recipe book. **The defect is created by the documented flag
set**, which is why it has been in every candidate for at least seven weeks.

Why nobody hit it: nothing imports SYSARGS. Live `SYSARGS.dbf` holds 249 rows
against a candidate of 1180. The day someone loads this table keyed on ARG_ID,
14 rows collide and one of each pair wins silently.

Not fixed here -- Gate 5 binds, it does not mutate. Filed as a finding with the
one-line remedy (include `arg_kind` in the id, or reject non-unique ARG_ID in
the contract) and a note that the SYSCMD uniqueness clause needs a SYSARGS
counterpart, since the clause that exists is on the table that was never at
risk.

## 9. The citation that expired

Four prior documents and this one cited the ignore rule as `.gitignore:342`. It
is at line **545** today, and line 342 is now a comment about WRITEBACK -- a
wrong citation that resolves to plausible-looking text.

    .gitignore at ad34e9145 (2026-08-26)   360 lines, rule at 342   TRUE then
    .gitignore at HEAD      (2026-09-24)   573 lines, rule at 545   FALSE now

Nothing was edited near the rule; the file grew above it. **A `path:line`
citation into a file that grows is a claim with a shelf life**, and nothing in
the gate suite checks one. All five citations are corrected to quote the rule
TEXT, which is greppable and does not move. Filed as a finding.

## Good Neighbor

    What changed  : this document; five CSVs in this directory, all gitignored.
                    The sandbox binaries were built outside the repo and are not
                    in it. Nothing in dottalkpp/data/metadata was touched.
                    Two prior documents corrected: a stale line citation (5
                    sites) and one mislabelled compare figure.
    Whose area    : lane full_stack_documentation / AIF-068.
    Authorization : member.derald, 2026-09-24 -- ran the host emit.
    Verify        : sha256sum the five files against section 1.
                    Re-emit and cmp -- the contract requires byte-identity.
                    Section 4: normcheck_v1.py's "absent from SYSCMD" line.
                    Section 6: cmp the two runs' compare CSVs.
                    Section 8a: cut -d, -f1 the SYSARGS candidate, sort, uniq -d.
    Undo          : delete this document; the candidates remain, unbound.
