---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260821-COWORK-009
  recorded_at_utc: 2026-08-21T14:40:00Z
  agent:
    provider: Anthropic
    product: Claude (Cowork)
    model: claude-opus-5
    access_mode: local_write
  session:
    id: not_exposed
    chat_reference: not_exposed
  project:
    id: project.x64base.runtime
    root: D:/code/ccode
  git:
    branch: development
    baseline_commit: 2aad9b379
  authorization:
    requested_by: maintainer (member.derald), in-session, "lets update and commit and publish" / "this is the perfect time to sync development to c:\x64base staging and update main"
    scope: >
      Closeout for the 2026-08-21 sitting: the dottalk_wx to dottalk_wb rename,
      the manualgen reclaim, the AIF-120 specimen work, and the promotion that
      reached github main as 9470a50d9.
  report:
    path: docs/maintenance/SESSION_CLOSEOUT_PROMOTION_TO_MAIN_AND_WORKBENCH_RENAME_2026-08-21.md
    kind: session_closeout
---

# Session closeout 2026-08-21 -- promotion to main, and the Workbench rename

Status: closeout, review-needed. Owner: member.derald.
Author: member.ai.claude.cowork. Run: COWORK-20260817-001.
Concurrent run in the same tree: COWORK-20260818-001 (AIF-120 R101-R108, threading ruling R11).

## What landed

`development` `2aad9b379` -> `370391ae8` -> `cac02a8b5`, seven commits.
`main` `72a449d05` -> **`9470a50d9`**, one promotion commit, 30 files.

| commit | what |
| --- | --- |
| `686c7e14e` | `src/gui/wx/res` tracked -- a build-breaking widow |
| `501a03b99` | `dottalk_wx` -> `dottalk_wb`, and the dead DLL-staging block |
| `ee954d39f` | `CLAUDE.md`: the bbsd remedy that did not work |
| `40300c726` | OI-011 manualgen reclaim, 10.47 G |
| `2e6c5592d` | OI-010 cites `dev-21`, the name the chapter has had all along |
| `e5b564690` | OI-009 closed: five launcher predecessors deleted, not tracked |
| `ea939d001` | the local-path pattern verified under .NET |
| `370391ae8` | `rebuild-staging`: `**` entries resolve |
| `cac02a8b5` | the launchers are named for the Workbench |

## The two that mattered most

**`src/gui/wx/res` was a widow that broke the build.** `main_frame.cpp:14`
includes `res/app_icon.hpp` and `CMakeLists.txt:51` adds `res/x64base.rc` to the
source list. `main_frame.cpp` was tracked; all eight files under `res/` were not.
**A fresh clone could not compile the Workbench.** Found while auditing the
rename, not while looking for it.

**The `.text` travel marker had never travelled.** `PROMOTE.manifest` carries
`**/*.text` and `.gitignore` carries an explicit `!**/*.text` durability guard so
the marker can never be excluded by accident. But `Get-ChildItem -Path` does not
implement `**` as a recursive glob -- it resolves as an ordinary single-level
wildcard -- so the entry matched nothing while
`docs/ai-friendly/DOTTALKPP_DOT_TEXT_CONVENTION.text` sat tracked two levels
down. The guard protecting it worked perfectly; the publisher reading it never
did. It reached `main` for the first time in `9470a50d9`.

## Four corrections to things this repository asserted about itself

1. **`CLAUDE.md` gave a remedy that does not work.** `Stop-ScheduledTask` returns
   success and leaves `dottalk_bbsd.exe` held; two consecutive builds still hit
   LNK1104. An ELEVATED `Stop-Process` is what worked. Corrected in `ee954d39f`.
2. **OI-011's gitignore claim was wrong at the level that mattered.**
   `check-ignore` returning nothing for the `manualgen` DIRECTORY was read as
   covering its contents. `docs/**/backups/` is precisely why twelve governance
   attestations sat unreachable: no `git add` could have taken them.
3. **OI-010 cited `dev-19-build-system.md`**, a name the chapter never had after
   its first day. The `cited-paths` gate reported it MISSING at every commit that
   touched the file.
4. **`PROMOTION_PROCESS.md` still asserts** that `messaging`/`metadata`/`sandbox`
   are "versioned in development". They are not. Recorded as OI-014 rather than
   silently fixed, because which way it resolves is a ruling.

## What I got wrong, and what caught it

- **Claimed a gitignore gap existed without reading `.gitignore`.** Every rule I
  proposed was already present. Measurement, not review, caught it.
- **Diagnosed the dead CMake block from reading.** Correct, but the proof was the
  absent COMMENT in a build log, and I should have led with that.
- **Read my own display indentation as file content.** I pipe output through
  `sed 's|^|  |'`, then matched against those two spaces. The Edit tool refusing
  the string is what caught it.
- **Broke YAML putting `day's` inside a single-quoted scalar.** The parse error
  pointed at the apostrophe, not at the quoted specimens I would have suspected.
- **Left `wb.run.ps1` as a bare name** when stripping path prefixes, which
  PowerShell will not execute from the current directory. Caught on read-back.
- **Wrote a promotion sequence that walked past a failed step.** `git rm` is
  all-or-nothing; two files had local modifications so it removed none of the
  four, and my step 6 sanity check is the only reason six launchers did not ship.
- **Skipped promotion step 3 entirely.** The maintainer caught it. See OI-015:
  the staging build is green but structurally cannot cover the GUI lane.

The pattern across all of them: the checks that fired were the ones that could
fail. The ones I reasoned my way to were the ones that needed a second look.

## Open, and where it is recorded

OI-013 `docs/gui` 14 on disk / 1 tracked. OI-014 the messaging claim.
OI-015 staging cannot cover the GUI lane. OI-016 a live workflow on the public
repo that neither author read. OI-017 71 machine-absolute paths already public.
OI-008, OI-010, OI-011 and OI-012 carry forward unchanged except as noted.

Not in the register, deliberately: `x64base-site` has one uncommitted file and
20 unpushed commits, and **the live pages are held at maintainer instruction**.
Pushing that branch changes nothing a visitor sees -- verified, the repo has no
`.github/` and therefore no deploy workflow.

## Housekeeping still owed in `D:\code\ccode`

Six root files are captured command lines from a mistyped redirect, not work:
`AIF-086 is the correct and sole con.txt`, `AIF-112 Phase-1 spike exercise
(Ha.txt`, ``Implemented `SYSCHATLNK`, the X64 m.txt``, `Stop-Process -Id 23932,
47296.txt`, `powershell -ExecutionPolicy Bypass.txt`, and `ws_proxy.txt` (check
that last one -- it may be deliberate).

Three orphans in `dottalkpp/bin` now that `APPGUI` resolves `dottalk_wb*`:
`dottalk_wx.exe`, `dottalk_wx_next.exe`, and `dottalk_wx.exe - Shortcut.lnk`.
The shortcut is the one that bites: it launches a stale binary rather than
failing.
