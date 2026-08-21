# HELP refresh package v1 (Phase 3 / Gate 3)

    Run       : DOCFLUSH-20260812-001 (full-stack doc flush v5)
    Gate      : 3, reviewed HELP refresh package
    Prepared  : 2026-08-21, session COWORK-20260821-002, sandbox, report-only
    Baseline  : runtime_baseline/GATE2_BASELINE_REVIEW_V1.md
                + runtime_baseline/GATE2_ADDENDUM_V1.md (re-baseline at HEAD)
    Entry HEAD: cac02a8b5, branch development
    Status    : AWAITING AUTHORIZATION -- member.derald. Nothing here has run.
                The author does not self-approve.

---

## 1. Why a rebuild is authorized

The store was last built **2026-08-15 19:49**, outside a gate. Measured since
then, at `cac02a8b5`:

| input | changed? | evidence |
| --- | --- | --- |
| `include/dotref.hpp` | **YES**, 260 -> 261 entries | `358c14a8a` adds `SMTP` |
| `include/foxref.hpp` | no, 175 entries both ends | no commit touches it |
| `include/edref.hpp` | **YES**, twice | `810686319`, `aac6b8bdf` (one-line title per topic, 29/29) |
| contract blocks in `src/**/*.cpp` | **YES**, 2 files | see below |

Seventeen contract-bearing `.cpp` files were touched in that window. Diffing
comment lines between `d4661f4a3` (the nearest commit before the store's mtime)
and HEAD, only **three** files changed a comment at all, and only two changed a
contract:

- `src/cli/cmd_smtp.cpp` -- **NEW FILE**, new `@dottalk.usage v1`,
  `command: SMTP`, `status: review-needed`.
- `src/cli/app_gui.cpp` -- **NEW FILE**, new `@dottalk.usage v1`,
  `command: APPGUI`.
- `src/cli/cmd_vdisk.cpp` -- 2 comment lines, at line 90. Its contract block
  runs lines 11-62, so the change is OUTSIDE the block. **Not** a HELP input.

So the authorized delta is small and named: one dotref entry, two new contracts,
and the edref title work. Expected magnitude is a few hundred rows, not a
rewrite.

**A caveat that must ride with every number above.** HELP DATA still carries no
provenance rows (v6 hints section 2), so "the store was built from
`d4661f4a3`" is the nearest commit by timestamp, not a fact the store can
confirm. Whether the tree was clean at 19:49 is unrecoverable. If Gate 4's diff
is materially larger than this package predicts, that is the likeliest reason --
and it is an argument for the provenance stamp, not a defect in the build.

## 2. What this package does NOT do

Engine HELP only. No metadata import (Phase 5), no manual publication
(Phase 6), no website apply, no promotion to `C:\x64base`, no pointer change.
The website matrix CLOSING gate in `D:\dev\x64base-site` is a separate,
still-owed condition and v5 cannot close without it.

## 3. The sequence, as a gate rather than a note

v4 wrote this down. v5 skipped two steps of it on 2026-08-12 and lost a cycle.
The v6 hints promote it to a seven-step gate; this package runs it in full even
where a step looks like a no-op.

    1. COMMIT the dotref/foxref/contract slice     <- already landed (358c14a8a,
                                                      810686319, aac6b8bdf)
    2. REBUILD the engine                          <- REQUIRED. dotref is
                                                      compiled IN; a stale exe
                                                      silently publishes the old
                                                      catalog
    3. back up dottalkpp/data/help
    4. kill the daemon (it locks the store)
    5. CMDHELP BUILD LEGACY
    6. CMDHELP BUILD . <ABS src>
    7. verify with DOTHELP / HELP <verb>, NOT by grepping the DBFs

Step 5 is run even though `foxref.hpp` did not change: the store's LEGACY
currency has never been verified in this run, and LEGACY-first is the recipe's
gate for a dotref change, which this is.

Step 7 is not decoration. Grepping the built store cannot attribute a hit to a
source when dotref and the `@dottalk.usage` block carry similar wording -- that
produced a confident wrong answer in v5 (Gate 2, section 2).

## 4. Step 4 is not `Stop-ScheduledTask`

Corrected in `ee954d39f` and measured again 2026-08-21: `Stop-ScheduledTask`
returns success and leaves `dottalk_bbsd.exe` holding its file. It stops what the
scheduler still tracks. The daemon is started at logon, so an **elevated**
`Stop-Process` is what actually ends it. Confirm before and after; restart it
afterwards or the BBS stays down until next logon.

## 5. Pre-build backup reference (current store, measured 2026-08-21)

    HELP_LINE.dbf          13693307  0bb6dca5e49ffd22
    HELP_ARTIFACTS.dbf      3671972  fc83bba02a06e6db
    HELP_TOPIC.dbf           308840  95de4311cb292a37
    HELP_SECTION.dbf         2692812  7a49f02d4c2fe14f
    COMMANDS.dbf               48800  be65a4dad0ebae5d
    CMD_ARGS.dbf              300994  893aa171b0454356

    (sizes in bytes; sha256 first 16 hex)

## 6. Rollback

Restore the backup directory over `dottalkpp\data\help` with the daemon stopped,
then re-run `CMDHELPCHK` and confirm structural PASS on the restored store. No
git action: the store is not version-controlled.

## 7. Authorized host command sequence (maintainer runs; the sandbox cannot build)

```powershell
# --- run from D:\code\ccode -------------------------------------------------
Set-Location D:\code\ccode

# 1. the slice is already committed. Confirm, do not assume:
git --no-optional-locks log -1 --oneline -- include/dotref.hpp
git status --short -uall -- include/dotref.hpp include/edref.hpp src/cli/cmd_smtp.cpp src/cli/app_gui.cpp

# 2. REBUILD -- dotref is compiled into the exe
cmake --build build --target dottalkpp --config Release

# 3. back up the HELP store
$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
Copy-Item -Recurse D:\code\ccode\dottalkpp\data\help "D:\code\ccode\dottalkpp\data\help.bak-$stamp"

# 4. kill the daemon. ELEVATED shell -- Stop-ScheduledTask alone does NOT work.
Get-Process dottalk_bbsd -ErrorAction SilentlyContinue | Select-Object Id, Path
Get-Process dottalk_bbsd -ErrorAction SilentlyContinue | Stop-Process -Force
Get-Process dottalk_bbsd -ErrorAction SilentlyContinue | Select-Object Id, Path   # expect nothing

# 5 + 6. LEGACY first, then the current build
./datarun.ps1 -CommandLines 'CMDHELP BUILD LEGACY','CMDHELP BUILD . D:\code\ccode\src'

# 7. post-build capture (report-only). datarun.ps1 has NO -Script parameter;
#    source the .dts lines into -CommandLines and let datarun stage its own temp .dts.
$run = 'D:\code\ccode\docs\maintenance\lanes\full_stack_documentation\runs\DOCFLUSH-20260812-001\help_refresh'
./datarun.ps1 -CommandLines (Get-Content "$run\fullstack_post_refresh_runtime_v1.dts") |
  Tee-Object "$run\fullstack_post_refresh_runtime_v1.txt"
Set-Location D:\code\ccode

# 8. bring the daemon back
Start-ScheduledTask -TaskName 'DotTalkBBSD'
Get-Process dottalk_bbsd | Select-Object Id, Path
```

Note the quoting rule: comma-separated arguments are quoted as ONE string where
a tool takes a list, because PowerShell splits `--files a,b` into two argv
entries. The `-CommandLines` array above is deliberately an array, not a list in
one string -- each element is one CLI line.

## 8. Gate 4 assertions (what the transcript must show)

Fail any one and Gate 4 does not pass.

1. `ABOUT` reports a build stamp LATER than `358c14a8a`. A stale exe is the
   failure this whole sequence exists to prevent, and it is checkable in one
   line.
2. `CMDHELPCHK` structural status == PASS, blank artifact texts == 0.
3. `HELP SMTP` and `CMDHELP SMTP` resolve. `HELP APPGUI` and `CMDHELP APPGUI`
   resolve. "No help found" for any of the four == FAIL.
4. `DOTHELP` renders the `SMTP` entry with the syntax string from
   `include/dotref.hpp:SMTP`. This is step 7 of the sequence and it is the
   authoritative instrument -- do not substitute a grep of the DBFs.
5. `CMDHELP SOURCE`: `FOXREF` == 665 (foxref.hpp did not change; a move here
   means something else did). `EDREF` != 786 (edref.hpp changed twice; a FLAT
   EDREF means the edref work did not reach the store). `DOTREF` >= 992.
6. Line and topic counts >= 28,827 / 528. Record the deltas either way.
7. Diff `fullstack_post_refresh_runtime_v1.txt` against
   `../runtime_baseline/fullstack_pre_refresh_runtime_v1.txt`. The first block
   of the two scripts is identical by construction, so the diff is the result.
8. Transcript is free of mojibake. 0 non-ASCII inside contract blocks was
   measured on 2026-08-12; a garble means the store predates `4c584ba8f`.

## 9. Still blocked, and NOT part of this package

`FN_COVERAGE` should now read 75/75: the `dt_meta` link was repaired
(`d99f4ed9c`) and the `FN_FILE` row landed (`b9d267df8`). **Neither has been
verified by a run** -- the sandbox cannot build. Item 2 of the Gate 4 assertions
does not cover it; if the maintainer wants it settled in the same pass, add
`FN_COVERAGE` to the post-refresh script before running. It is left out here
because a metacollect build is a separate authorization from a HELP build, and
this package deliberately does not bundle them.

Beware the decoy while checking: `D:\code\ccode\SYSFUNC_IMPORT_v1.csv` is an
UNTRACKED 2026-06-27 copy with 64 functions and no `FN_FILE`. The live authority
is `dottalkpp\data\scripts\metadata\SYSFUNC_IMPORT_v1.csv` (75 functions,
`FN_FILE` present), which is what the tooling reads.

## 10. Gate 3 acceptance

- [ ] member.derald authorizes the named mutation package: engine rebuild,
      `CMDHELP BUILD LEGACY`, `CMDHELP BUILD . D:\code\ccode\src`.
- [ ] Backup and rollback are concrete (sections 5 and 6) and the affected paths
      are named.
- [ ] The build is NOT bundled with Phase 5 metadata, Phase 6 manual
      publication, or any website apply.

---

## Good Neighbor note

    WHAT CHANGED   : three new documents under
                     runs/DOCFLUSH-20260812-001/ --
                     runtime_baseline/GATE2_ADDENDUM_V1.md,
                     help_refresh/HELP_REFRESH_PACKAGE_V1.md,
                     help_refresh/fullstack_post_refresh_runtime_v1.dts.
                     No source, no data, no store, no git mutation.
    WHOSE AREA     : lane full_stack_documentation, owner member.derald,
                     steward member.ai.claude.cowork. AIF-114 is named in the
                     addendum section 3a as the home for a question found here,
                     not acted on.
    AUTHORIZATION  : the current request -- "Full-Stack SelfDoc push v5", plus
                     an in-session ruling to re-baseline and prepare the Gate 4
                     package rather than execute it. NO authorization to build,
                     to rebuild HELP, or to commit.
    VERIFY OR UNDO : git --no-optional-locks status --short -uall -- \
                       docs/maintenance/lanes/full_stack_documentation/runs/DOCFLUSH-20260812-001
                     Undo is deleting the three files; nothing else was touched.
