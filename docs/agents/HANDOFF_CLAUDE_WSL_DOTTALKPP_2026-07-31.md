# Handoff -- WSL / dottalkpp working session (new Claude project)

    from    : member.ai.claude.cowork, run 2026-07-31_cowork_output_capture_completeness
    owner   : member.derald
    repo    : D:\code\ccode  (branch `development`, remote deraldg/x64base)
    purpose : bring a fresh agent to productive in one read, without re-learning
              the traps below the expensive way

Everything here was verified against source or measured at runtime during
2026-07-30/31. Where something is inferred rather than checked, it says so.

---

## 1. Read these first, in this order

1. `CLAUDE.md` (repo root) -- binding conventions. Overrides default behaviour.
2. `dottalkpp/data/scripts/README.txt` -- .dts authoring and environment rules.
3. `docs/maintenance/AI_SESSION_COORDINATION_PROTOCOL_V1.md` -- commit/AIF doctrine.
4. `docs/ai-friendly/AI_INTERACTION_INTAKE_QUEUE_V1.md` -- the lane ledger. Long
   rows; read the last few for current state.

---

## 2. What this is

DotTalk++ / x64base: a modern C++20 xBase-inspired database runtime and command
shell. Three layers, each a real boundary:

    xbase   -- DBF/table/record engine (v32 "classic", v64 "x64")
    xindex  -- index backends behind IIndexBackend
    cli     -- the DotTalk++ shell, commands, DotScript

Index backends, and the distinction that matters:

    CdxBackend        CDX container over LMDB   transactional, maintains live
    CnxBackend        native CNX/V32, RUN1      batch; upsert/erase are NO-OPS
    CdxNativeBackend  native CDX-V64, RUN8      batch; LMDB-free, RAM-capable
    LmdbBackend / SnxBackend / BptBackend / BpTreeBackend

CNX and native-CDX `upsert`/`erase` set `stale_ = true` and return NORMALLY.
Every mutation against such an order leaves the index stale. That is routine,
not an edge case. Until 2026-07-31 it was silent.

---

## 3. Build (WSL)

    cd /mnt/d/code/ccode
    ./wslbuild.sh                     # configure if needed, build, stage
    ./wslbuild.sh dottalkpp -a        # build + REGRESSION ALL
    ./wslbuild.sh dottalkpp -t IDXSTALE   # build + REGRESSION RUN IDXSTALE

Preset `wsl-lean` -> `build-wsl-lean/`, staged to `dottalkpp/bin-wsl-lean/`.
It sets `VCPKG_MANIFEST_FEATURES=index`, so vcpkg installs four base packages
and NO tvision/wx/pybind11. Do NOT reintroduce the `vcpkg.json` <-> `vcpkg-wsl.json`
swap; the canonical manifest's features block already covers it, and an
unswapped run under the old scheme destructively reconciled the installed tree
("Removing 53/53 tvision:x64-linux"). The reasoning is written into the top of
`wslbuild.sh` -- read it before touching the build.

Windows/MSVC builds also exist (`build/`, preset `pro-md`). MSVC is NOT required
for engine work: the wsl presets carry `DOTTALK_INDEX_MODE: LMDB`, so LMDB paths
are provable on Linux. A previous session lost most of its runtime evidence to
the belief that MSVC was mandatory.

**Verify the binary contains your change.** `ninja: no work to do` plus two
different build stamps in `ABOUT` is genuinely ambiguous. Compare mtimes
(`.o` vs source) or grep the linked ELF for a string you just added. This is
cheap and it has already caught one false-green.

---

## 4. Run

Data root is `dottalkpp/data` and is the cwd the engine expects. On startup it
prints every path slot (DBF, INDEXES, LMDB, SCRIPTS, TMP, ...). Read that block;
it tells you which fixture family is active.

    # Windows, over the work data
    ./datarun.ps1
    ./datarun.ps1 -CommandLines 'USER LIST','BBS BOARDS'

    # WSL, direct
    cd /mnt/d/code/ccode/dottalkpp/data
    printf '%s\n' 'CMD1' 'CMD2' | ../bin-wsl-lean/dottalkpp

Do NOT run the raw build exe by hand on Windows; `datarun.ps1` stages the newest
binary and warns loudly if a running process blocks the copy.

The wsl-lean ELF needs glibc 2.38 / GLIBCXX 3.4.32 (built on Ubuntu 24.04,
GCC 13.3). It will not run on an older sandbox.

---

## 5. Capturing output -- READ THIS BEFORE WRITING A PROOF

**Use `SET ALTERNATE`. Do not use `DOTSCRIPT ... OUT`.**

Measured 2026-07-31, same script and binary: `DOTSCRIPT OUT` produced 42 lines,
`SET ALTERNATE` 89. ALTERNATE is a strict superset. `DOTSCRIPT OUT` silently
drops everything routed through `cli::cmdout` -- the entire user-facing command
surface, including corrective warnings, which is precisely what a proof asserts
on.

Cause: the router installs its streambuf as `std::cout`'s buffer and tees the
alternate file inside it; `shell_transcript` tees one level higher at
`std::cout`, while `cmdout` writes to `routed_stream` directly. `routed_stream`
is a SIBLING of `std::cout`, not a child.

Full analysis: `docs/maintenance/OUTPUT_CAPTURE_COMPLETENESS_LANE_V1.md` and
`docs/maintenance/AIF_081_OUTPUT_CAPTURE_RUNTIME_PROOF_V1_20260731.md` (AIF-081).
The DOTSCRIPT help text still claims the opposite; it is wrong and unfixed.

    cd /mnt/d/code/ccode/dottalkpp/data
    printf '%s\n' \
      'SET ALTERNATE TO tmp/run.log' \
      'SET ALTERNATE ON' \
      'DOTSCRIPT scripts/<your_script>.dts' \
      'SET ALTERNATE OFF' \
      | ../bin-wsl-lean/dottalkpp

**Traces default ON.** `DOTTALK_INDEX_TRACE` and `DOTTALK_APPEND_TRACE` are
opt-OUT, not opt-in (`index_manager.cpp:449-457`, `append_support.cpp:74-82`).
Pin them explicitly if you want reproducible figures. Some spec text in the tree
says "run with DOTTALK_INDEX_TRACE=1", which teaches the inverse of the default.

---

## 6. DotScript (.dts) authoring rules

**Nesting: main plus exactly ONE subscript.** `cmd_dotscript.cpp:61`, enforced
at `:491` (`g_dotscript_depth >= 2`). Depth is checked before increment, so your
script is depth 1 and its `DO ..\X32` bootstrap is depth 2. A wrapper script
that invokes `DOTSCRIPT other.dts` pushes that bootstrap to depth 3 and is
REFUSED. Issue the `DOTSCRIPT` line at top level, via stdin.

**Environment first.** Every regression .dts sets up its own environment before
anything else: `DO X32`, `DO X64`, `DO SANDBOX`, `DO METADATA`, `DO MESSAGING`,
`DO VFP`. Scripts nested below `data/scripts` climb back to the data root
(`DO ..\..\X64`). Then open tables explicitly.

**Comment vocabulary** (`dotscript_lexing.hpp`):

    full-line : *  REM   (canonical)    #  //  &&  (tolerated)
    inline    : &&  #    (quote/escape aware)
    single &  : xBase macro operator, NEVER a comment

House marker is `&&`. Free-text commands that read to end of line (BBS POST,
CHAT) must be comment-free.

**`;` is position-dependent and will bite you.**

    trailing, unquoted -> LINE CONTINUATION  (script_reader.hpp:18)
    leading            -> line skipped       (dotscript_lexing.cpp:84)

A marker line ending in an unquoted `;` silently swallows the line beneath it.
Also note `is_comment_or_blank()` treats leading `;` as skippable while
`is_comment_line()` does not list `;` at all -- a live inconsistency inside the
module that was supposed to end exactly that kind of drift.

**Marker authoring -- learned across THREE failed attempts:**

    WORKS :  ? "NAME:" + (ALLTRIM(<field>) = "VALUE")
    FAILS :  ? "NAME:" + FOUND()                 -> renders EMPTY
    FAILS :  ? "NAME:" + (RECNO() = 1)           -> renders EMPTY
    FAILS :  ? "NAME:" + (ALLTRIM(STR(RECNO())) = "1")  -> renders EMPTY

`STR()` does NOT rescue `RECNO()`. Every assertion must be a FIELD comparison.
An empty render reads as failure, so a marker that cannot render is worse than
no marker.

**Guard the cursor.** Park on a known different record before every SEEK and
assert you moved. Two earlier proofs PASSED WHILE PROVING NOTHING because their
SEEKs errored (no active order), the cursor never moved, and each marker
re-read whatever record happened to be current. A test that reports success
while not running is the house's most-repeated defect class.

**Scoring CNX staleness:** score ORDER (`GO TOP`), not key lookup. CNX SEEK
compares live field values through a stale recno ordering, so a key probe proves
nothing either way. Measured: after moving MILLER -> AAAAA, `SEEK MILLER` misses
AND `SEEK AAAAA` still hits.

Worked example carrying all of the above:
`dottalkpp/data/scripts/index_maintenance_failure_proof.dts` (regression
`IDXSTALE`). Note its header line 37 contradicts line 85 on the `STR(RECNO())`
rule; line 85 is the measured one. Unfixed.

---

## 7. Regressions

`REGRESSION` lists curated specs; `REGRESSION RUN <NAME>` runs one;
`REGRESSION ALL` runs the 8 default suites. Specs live in
`src/cli/cmd_regression.cpp` as a `std::array<RegressionSpec, N>` -- when adding
one, bump N and verify the declared size equals the entry count programmatically.
Declaring 31 with 32 entries has already happened once.

Default suites are green as of 0803f0f13. Explicit-run suites (IDXSTALE,
VUREPAIR, IDXDIFF, MEM, WAL_COMMIT_ROLLBACK, ...) mutate the filesystem or leave
session state and are deliberately out of the default set.

---

## 8. Git and coordination -- non-negotiable

Concurrent AI sessions share ONE working tree. `git status` shows ~20 modified
and hundreds of untracked files belonging to other sessions. Therefore:

  - **NEVER** `git add -A` or `git add .`. Name exact paths, always.
  - `git status --short` between add and commit. Verify only your paths are staged.
  - Use repeated `-m` flags. Here-strings and message files have both failed
    (`fatal: could not read log file`); a scratchpad path is not readable by
    Windows git.
  - The pre-commit gate runs automatically (`repository-role-guard`,
    AIF-collision, refcheck/normcheck). It HARD-blocks duplicate AIF numbers.
  - Claim lane numbers atomically, never by grep:

        python tools/coordination/session_coordinator.py claim-aif `
          --member member.ai.claude.cowork --run <run-id> --lane <lane>

    grep is not an allocator -- a previous session reported a number free that
    had been claimed and closed the same day.
  - **Register the lane BEFORE or WITH the work**, not after. Commit the intake
    row and the `coordination/aif/AIF-NNN.claim` file. The gate advisory
    "claim(s) with no intake row" means the lane reads as ABANDONED from HEAD
    even though its charter and code are committed. This has now happened three
    times (AIF-062, AIF-078, AIF-080).

**If you have a Linux sandbox: run NO git commands from it.** Even `git status`
refreshes the index, takes `index.lock`, and cannot unlink it across the mount,
which then blocks the owner's commits. Read files freely; run git only on the
Windows side. `claim-aif` shells out to `git grep`, so it is Windows-side too.

---

## 9. House style

  - No em-dashes anywhere in scripts or docs. Use `--` or `->`.
  - ASCII only in new content. Check with `grep -P '[^\x00-\x7F]'` before commit.
  - `&&` is the DotTalk inline comment marker, not `#`.
  - Cite `file:line` for every source claim.
  - Evidence tiers are load-bearing: `planned`, `source-evidenced`,
    `runtime-proven`. Do not write `runtime-proven` unless it ran, and do not
    leave the evidence somewhere uncommitted.

---

## 10. Open state as of 0803f0f13

    AIF-079  declared-but-unreferenced capability validator. Scanner NOT written.
    AIF-080  index container/engine orthogonality. M1 capacity gate LANDED.
             Message split deferred (text also lives in
             SYSTEM_MESSAGE_TEXT_IMPORT_v1.csv across 5 locales with hashes).
    AIF-081  output capture completeness. Findings recorded, NO fix landed.
             M0/M1 = move DOTSCRIPT OUT onto the router sink + correct the help
             text in the SAME commit. M2 = trace defaults, OWNER RULING NEEDED.

    Owner calls outstanding: AIF-069 marked closed with uncommitted evidence;
    AIF-068 claim disagrees with its lane doc; AIF-070 claimed, never registered.

Current workflow for index binding, per the owner (SET CNX / SET CDX are legacy
and still registered as `supported`, which the usage contract cannot express):

    SELECT n
    USE <table>
    SET INDEX TO <indexname>      && defaults to table name; extension .cdx
    SET ORDER TO TAG <tag>
    SEEK <value>

---

## 11. The one habit that matters

This codebase's most common defect is not a crash. It is a thing that reports
success without doing its job: a test that passes without running, a capture
that captures nothing, a declared capability with no implementation, a lane
whose evidence is invisible from HEAD. Assume that shape is present, and prefer
measuring to inferring -- including about your own claims. Two predictions made
during this session were confidently wrong and were caught only by reading the
source before writing them down.
