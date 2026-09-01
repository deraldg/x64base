# DOCFLUSH-20260901-001 -- the host-side proof package (E2, E5, E7)

    run       : DOCFLUSH-20260901-001 (v7)
    baseline  : 2d26612b9  (2026-09-01)
    for       : member.derald, on the host. A sandbox cannot produce any of this.
    posture   : commands to RUN, not results. Nothing below is claimed as proven.

Three entry conditions need the engine. v6 recorded E2 as **UNRUN** and E5 as
**PARTIAL**; the cookbook names E5 as *"the one runs usually fail first"*. This
file is the package so they can be run once, in order, with the output captured.

**Capture rule.** Use `*>` redirection or `SET ALTERNATE`. **Never
`DOTSCRIPT ... OUT`** -- AIF-081: it drops everything routed through
`cli::cmdout`, measured 42 lines against `SET ALTERNATE`'s 89 on the same script
and binary. `tmp/` is gitignored, so paste the decisive lines back or tee
somewhere tracked.

---

## E2 -- CMDHELPCHK reflection PASS

**Can be run against the EXISTING store.** It does not require a rebuild, and v7
has changed no source of its own, so no rebuild is indicated (see E8/M1).

```powershell
cd D:\code\ccode
./datarun.ps1 -CommandLines 'CMDHELPCHK' *> tmp\v7_e2_cmdhelpchk.log
```

`CMDHELPCHK` with no arguments runs reflection-system validation (its own
`@dottalk.usage` block; `REF` and `REFLECT` are explicit names for the same
mode). What E2 needs is that it reports PASS.

**Read the banner first.** If the build stamp has not moved since the last run
you looked at, you are reading a stale binary -- that cost three full help-build
cycles on 2026-08-26 before anyone checked the timestamp.

---

## E5 -- HELP/META harvest re-exported AFTER the build

**This is the condition that fails.** The rule is ordering, not existence: a
harvest exported BEFORE a build describes the previous store, and the manual then
omits whatever the build added. v6 recorded PARTIAL for exactly this reason.

**If v7 runs no build (the expected case), E5 is satisfiable by ordering
argument alone**: no build has occurred since v6's harvest, so the harvest is not
stale relative to any newer build. Record that reasoning explicitly rather than
re-exporting for its own sake.

**If a build IS run**, the harvest must follow it:

```powershell
$py12 = "D:\code\ccode\.venv312\Scripts\python.exe"
& $py12 .\tools\fullstack_docs\export_help_meta_harvest.py --out tmp\v7_harvest
& $py12 .\tools\fullstack_docs\compare_help_meta_harvest.py
```

Note the exporter's own limitation: under the v32 `dbfread` path, memo fields
come out as bare pointers. That is a known property, not a defect to chase.

---

## E7 -- HELP store backup with a named rollback

**Only needed if a build is run.** v6's `help.bak-20260825-180609` does not cover
a build v7 performs.

```powershell
$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
Copy-Item -Recurse D:\code\ccode\dottalkpp\data\help "D:\code\ccode\dottalkpp\data\help.bak-$stamp"
```

**Rollback, to name in the Gate 3 record:**

```powershell
Remove-Item -Recurse D:\code\ccode\dottalkpp\data\help
Rename-Item D:\code\ccode\dottalkpp\data\help.bak-<stamp> help
```

**Measured 2026-09-01: TWELVE backup directories already exist**, at ~54 MB each,
and nothing rotates them. That is roughly 650 MB of standing cost nobody owns.
Not v7's to fix, but v8 should either rotate or record a retention rule.

---

## If a build IS authorized -- the ordering that is not optional

```powershell
# 1. The daemon holds the store. Stop-ScheduledTask alone RETURNS SUCCESS AND
#    LEAVES IT RUNNING (CLAUDE.md, measured twice on 2026-08-21).
#    This must run ELEVATED.
Get-Process dottalk_bbsd | Stop-Process -Force
Get-Process dottalk_bbsd | Select-Object Id, Path        # confirm it is gone

# 2. Back up (E7 above).

# 3. LEGACY FIRST -- foxref feeds the legacy builder and a dotref change needs it.
./datarun.ps1 -CommandLines 'CMDHELP BUILD LEGACY','CMDHELP BUILD . D:\code\ccode\src' *> tmp\v7_build.log

# 4. Harvest AFTER the build (E5).

# 5. Restart the daemon or the BBS stays down until next logon.
Start-ScheduledTask -TaskName 'DotTalkBBSD'
```

---

## What must NOT be recorded

- **No sandbox result may be entered as E2 PASS.** The sandbox has no engine, and
  `repository_role_guard.py` correctly refuses the mount path -- a refusal there
  is expected and is not evidence about anything else.
- **A green exit is not a PASS.** Read the reflection output. A tool that reports
  success without having looked is the defect this project hunts, and this run
  has already produced one of its own (`cited-paths: no documents in scope`
  returning exit 0 while examining nothing).
- **Do not stage `src/` or `include/`.** Two source files modified in the tree
  belong to another session; see E8/M1.
