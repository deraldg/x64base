# DOCFLUSH-20260901-002 -- the host run package

    run       : DOCFLUSH-20260901-002 (v8)
    baseline  : 45f699a23  (2026-09-01)
    owner     : member.derald
    steward   : member.ai.claude.cowork
    posture   : NOTHING BELOW HAS BEEN RUN. This is the list to authorize FROM,
                and the commands to run once authorized.

v8 ran Phases 0, 0.5 and 1 to completion in the sandbox. Phases 2 and 4 need the
engine, and one Phase 0.5 check needs Python 3.12. This file is that boundary,
in run order, with the traps named.

---

## H0 -- prerequisites, in this order

    1. Confirm the daemon is down. Stop-ScheduledTask ALONE IS NOT ENOUGH: it
       returns success and leaves the process running (measured 2026-08-21, two
       builds LNK1104 after a clean stop). From an ELEVATED shell:

         Get-Process dottalk_bbsd | Select-Object Id, Path
         Get-Process dottalk_bbsd | Stop-Process -Force
         Get-Process dottalk_bbsd | Select-Object Id, Path      # confirm gone

    2. Confirm the exe is current. datarun.ps1 warns loudly if it cannot stage a
       fresh build, but read the ABOUT banner in the transcript anyway -- reading
       a result without checking the build stamp is how v7 reported the same
       output three times.

---

## H1 -- Phase 0.5 residue: the catalog check (needs 3.12)

The sandbox has 3.10 only, so this one line of Phase 0.5 is unrun.

    $py12 = "D:\code\ccode\.venv312\Scripts\python.exe"
    & $py12 .\tools\fullstack_docs\command_catalog_sync.py check `
        --source-root D:\code\ccode `
        --catalog D:\dev\x64base-site\content\docs\dottalk\command-catalog.mdx

Target: `fallback 0`. NOT a mutation -- `check`, not `emit`. Note it reads the
site tree, which is on `codex/lean-sites-publish`; reading is fine, and E6
(regenerating the catalog) stays on HOLD until the branch question is ruled.

---

## H2 -- Phase 2: pre-refresh runtime baseline  (Gate 2)

Script is authored and in place:

    docs\maintenance\lanes\full_stack_documentation\runs\DOCFLUSH-20260901-002\
      runtime_baseline\fullstack_pre_refresh_runtime_v1.dts

Its 26 targeted topics are derived, not chosen: every `@dottalk.usage`-bearing
command file that changed since the store was built (2026-08-26 05:09:48), with
the `command:` read from each contract. Plus the five AIF-134 keys, the two
spaced BUILD spellings, and SET.

    $run = 'D:\code\ccode\docs\maintenance\lanes\full_stack_documentation\runs\DOCFLUSH-20260901-002\runtime_baseline'
    ./datarun.ps1 -CommandLines (Get-Content "$run\fullstack_pre_refresh_runtime_v1.dts") `
      | Tee-Object "$run\fullstack_pre_refresh_runtime_v1.txt"
    Set-Location D:\code\ccode

READ-ONLY. No BUILD, IMPORT, CREATE, REPLACE in the script.

**What to read in the transcript**, beyond reflection PASS and the counts:

  - **Mojibake.** Source em-dashes render as a CP437 garble. Record any, and the
    topic they came from.
  - **Topics that look CURRENT.** This is the BEFORE half and the store is from
    2026-08-26, so every one of the 26 should reflect the old contract. One that
    already looks current means the topic is not sourced where it is assumed to
    be -- that is the finding, not the stale ones.
  - **Capture with `*>` or Tee, never `DOTSCRIPT ... OUT`** -- AIF-081: OUT drops
    everything routed through `cli::cmdout` (42 lines vs 89, measured
    2026-07-31).

---

## H3 -- Phase 3: the refresh package  (Gate 3) -- GENERATED, needs a ruling

    docs\...\DOCFLUSH-20260901-002\help_refresh\
      HELP_REFRESH_MUTATION_PACKAGE_V1.md
      help_refresh_package_manifest_v1.json
      pre_refresh_help_file_manifest_v1.csv     18 protected files
      help_refresh_input_manifest_v1.csv
      protected manifest sha256: 36F8066B08B22679790398338A1920B81375AB32FD16E6CF492E8763261FF473

**The package and the preflight disagree, and Gate 3 needs that resolved before
Phase 4 runs:**

    docpush_preflight.py             FAIL -- store predates exe, LEGACY 63h45m
                                     newer than the store. Build required.
    prepare_help_refresh_package.py  current_help_build_required: false
                                     legacy_build_trigger: REVIEW_REQUIRED
                                     "DOTREF is not currently dirty; timestamps
                                      alone do not prove whether it diverged."

Steward's reading, not a ruling: **the build is required and LEGACY must run
first.** `include/dotref.hpp` changed since the store was built (it is in the
28-file change set), foxref feeds the LEGACY builder, and the store is already a
half-run with LEGACY 63 hours ahead of it. The package's "not dirty" is a
timestamp inference; the preflight's is an ordering fact.

That is the conditional trigger the package itself asks to have resolved.

---

## H4 -- Phase 4: execute the refresh  (Gate 4) -- THE MUTATION

**M1 + M2. Authorize as one pair or not at all: never build without the backup.**

    Stop-ScheduledTask -TaskName 'DotTalkBBSD'
    Get-Process dottalk_bbsd | Stop-Process -Force        # ELEVATED. See H0.

    $stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
    Copy-Item -Recurse D:\code\ccode\dottalkpp\data\help "D:\code\ccode\dottalkpp\data\help.bak-$stamp"
    # hash-verify the backup before building. E7 is "backup EXISTS and rollback
    # is NAMED", and an unverified copy names nothing.

    ./datarun.ps1 -CommandLines 'CMDHELP BUILD LEGACY','CMDHELP BUILD . D:\code\ccode\src'

    $run = 'D:\code\ccode\docs\maintenance\lanes\full_stack_documentation\runs\DOCFLUSH-20260901-002\help_refresh'
    ./datarun.ps1 -CommandLines (Get-Content "$run\fullstack_post_refresh_runtime_v1.dts") `
      | Tee-Object "$run\fullstack_post_refresh_runtime_v1.txt"
    Set-Location D:\code\ccode
    Start-ScheduledTask -TaskName 'DotTalkBBSD'            # or the BBS stays down until logon

    writes    : dottalkpp\data\help\ -- 10 .dbf tables plus memo sidecars, ~54 MB
    reversible: YES, from the backup above
    rollback  : restore the dated backup, then rerun H2's read-only transcript
    order     : LEGACY FIRST. foxref feeds the legacy builder and dotref changed.

The post-refresh `.dts` is the same script as H2 (identical command set is what
makes the comparison valid). Copy it into `help_refresh\` before running, then:

    & $py12 .\tools\fullstack_docs\compare_runtime_baselines.py   # the Gate 4 diff

Gate 4 passes on: reflection PASS; line/topic counts >= baseline; the 26 targeted
topics resolve AND show the new contract text; LEGACY delta visible. The primary
store is often idempotent -- that is expected, not a failure.

**Housekeeping this run inherits and should not skip:** twelve `help.bak-*`
directories already exist, ~617 MB, and nothing rotates them. A thirteenth is
about to be created.

---

## H5 -- immediately after Phase 4, before anything else

**E5 is the entry condition runs usually fail.** The harvest must be re-exported
AFTER the build, or the manual omits every new command:

    & $py12 .\tools\fullstack_docs\export_help_meta_harvest.py
    & $py12 .\tools\fullstack_docs\check_help_meta_harvest_freshness.py
    & $py12 .\tools\fullstack_docs\docpush_preflight.py    # expect: PASS, no FAIL lines

The preflight re-run is the proof the Phase 4 pair actually cleared
`help_build_order_check`. Until that prints without FAIL, Phases 5 and 6 do not
start.

---

## What is NOT in this package, deliberately

    Phase 5  metacollect candidates    blocked behind Phase 4; candidate-only when
                                       it runs, and import is a separate gate
    Phase 6  manualgen candidate       blocked behind E5. Running it against the
                                       stale harvest produces a manual missing 26
                                       commands, which is exactly the failure E5
                                       exists to prevent.
    E6       command-catalog.mdx emit  HOLD. Site tree is on codex/lean-sites-publish,
                                       198 commits ahead of site main; main is a
                                       2026-07-03 snapshot. Writing a generated
                                       page there needs the branch ruling first.
    Phase 8  publication               NOT ENTERED. Separate lane, nine gates.

## Rulings this run is waiting on

    R1  Phase 4 authorization -- H4's M1+M2 pair. Everything downstream blocks here.
    R2  AIF-134: router or delete, five keys. Phase 1's review queue reaches the
        same three ERROR rows independently (Gate 1).
    R3  H3's disagreement: confirm LEGACY-first, or accept the package's
        "not dirty" reading and explain the preflight FAIL another way.
    R4  V6_HINTS section 4 -- FILE / UDATE / UDATETIME / UTIME / UNOW. v5 left three
        candidate rulings open. `src/cli/cmdhelp.cpp` was changed on 2026-09-01 to
        delegate `is_expression_function_name()` to the function catalog, which is
        candidate (b), shipped without the ruling. It is in the exe. It needs the
        ruling retroactively or a revert, and it is in scope for this run because
        Phase 4 rebuilds what it feeds.
