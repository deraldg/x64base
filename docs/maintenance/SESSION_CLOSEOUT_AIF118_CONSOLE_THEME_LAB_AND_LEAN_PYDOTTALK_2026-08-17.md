---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260817-COWORK-001
  recorded_at_utc: 2026-08-17T15:30:00Z
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
    baseline_commit: e9d7e3aa4
  authorization:
    requested_by: maintainer (member.derald), in-session, "document everything, do your house work and good neighbor policies"
    scope: >
      Monday-morning closeout across two repositories. Records the console light
      theme, a site hydration defect made visible rather than caused, the Lab
      local-only surface, the derald.com registry correction, the OPEN_ITEMS
      rung, and the lean pydottalk build. Carries an explicit NOT-LANDED section
      because two slices this session depends on are still uncommitted.
  report:
    path: docs/maintenance/SESSION_CLOSEOUT_AIF118_CONSOLE_THEME_LAB_AND_LEAN_PYDOTTALK_2026-08-17.md
    kind: session_closeout
---

# Session Closeout -- AIF-118 day two: console theme, the Lab, and a lean pydottalk

Date: 2026-08-17 (morning). Owning lifecycle: PDLC.
SDLC lane: tooling / publication / build. **AIF-118**, continuing
`SESSION_CLOSEOUT_AIF118_GUARDS_SITE_AND_EDREF_SHAPE_2026-08-16.md`.
Charter: `docs/maintenance/AIF_118_SILENT_PASS_GUARD_LANE_V1.md`.
Repositories: `D:\code\ccode` (development) and `D:\dev\x64base-site`
(`codex/lean-sites-publish`).

## READ THIS FIRST -- two slices had NOT landed, and now have (RESOLVED same day)

Recorded at the top because the rest of this document is less important than
these, and because a closeout that buries its own gaps is the defect this lane
is named for.

1. **Codex's week of work is still uncommitted.** `tools/dbf/crud.py` (+17),
   `tools/dbf/maint_server.py` (+309), `tools/registries/registry_fragments.py`
   (+36), `tools/reports/build_reports.py` (+44),
   `tools/reports/serve_dynamic_reports.py` (+144), two modified test files, and
   two untracked test files. Reviewed, gate-checked and green (13 + 27 tests) --
   but not committed. He is out of credit for a week; the tree is shared; every
   other session commits around it.
2. **The board note telling him what changed is also uncommitted**
   (`docs/ai-friendly/PSEUDO_CHAT_BOARD.md`), as is the removal of the dead
   `PAGE` template from `maint_server.py`. So the good-neighbor notice exists
   only on one disk. **A note that is not committed is a note that was not
   sent**, which is precisely the failure the quip tool warned about on 08-16.

**RESOLVED 2026-08-17, later the same session.** Commands had been given twice and
not run; the third time they were, in priority order:

| commit | what |
| --- | --- |
| `6a931ab3d` | console: write-token boundary, loopback enforcement, `WRITE_LOCK`, crud `_deleted`/`_recno`; dead `PAGE` template removed |
| `7f532088f` | reports: fragment-sourced registries, `compose_registry()` with duplicate-id refusal |
| `f30a620a7` | gateway: fragment render path, `/health`, per-session write token |
| `a92b17fa1` | docs: schema-inventory website feed lane |
| `60224d96e` | the board note to Codex |

**The item that could not wait was a security boundary, not the data loss.**
Measured before landing: `is_loopback_host`, `require_local_json` and
`WRITE_LOCK` had ZERO occurrences in HEAD and 4 / 2 / 2 in the working tree.
HEAD's `do_POST` read the body and called `_do_op` with no content-type check
and no token, and `_do_op` defaults `write_enabled=True` for the standalone
server. `--host` defaults to loopback, which saved it, but nothing ENFORCED
that. The fix existed, was reviewed and was green; it simply was not in git.

Caveat kept honest: the ABSENCE of the guards is measured; exploitability was
never demonstrated against a running instance. "The guard is missing" is
certain; "you were breached" was never claimed.

**Why this section stays rather than being deleted.** It was true when written,
and the reason it stopped being true -- being asked "is there anything pending
that can't wait?" -- is the reusable part. Unlanded work does not announce
itself; someone has to ask.

## What landed

| commit | repo | what |
| --- | --- | --- |
| `e9d7e3aa4` | ccode | console light theme, all colour through variables, contrast measured, 7 guard arms |
| `846b0ca02` | ccode | `coordination/OPEN_ITEMS.md` + `check_open_items.py`, wired advisory |
| `a35ebe1bf` | ccode | lean standalone pydottalk build; `DOTTALK_ROOT` anchors the three shared libs |
| `91e814a1d` | ccode | starter README corrected; OI-002 and OI-003 parked |
| `4a941f273` | site | `suppressHydrationWarning` on `<html>` |
| `84939eeb4` | site | `/lab` local-only surface; Dewey experiments moved out of `/docs/dev` |
| `4d35f2b3d` | site | stub at `/docs/dev/experimental` instead of a 404 |
| `0ad92d7dc` | site | derald.com note corrected against the registry |

## The findings, in the order they matter

**1. Four things the parent build had been silently providing.** The Python
binding links three libraries and references `dottalkpp`, `tvision` and
`dottalk_tvui` zero times, yet `build.ps1:164` hardcodes
`--target dottalkpp pydottalk`, so a 4-source module built the entire CLI plus
the Turbo Vision lib and the tvision vcpkg package. Making it standalone
surfaced what the root CMakeLists had been supplying to `src/xbase|memo|xindex`
without either side saying so:

- the GENERATED `dottalk/build_vectors.hpp` (exists in no source tree);
- `NOMINMAX` -- `<windows.h>` defines `max()` as a macro, so
  `std::numeric_limits<T>::max()` became `C2589: '(' illegal token on right side
  of '::'`, 30+ errors across 7 lines of `dbf_file.cpp`, **none of which
  mentioned windows.h or max**;
- `CMAKE_MSVC_RUNTIME_LIBRARY`;
- seven feature flags emitted as `=1`/`=0`.

**Only the first two announce themselves.** A CRT mismatch links cleanly and
misbehaves at runtime. An undefined `DOTTALK_WITH_INDEX` reads as 0 under `#if`,
so the module would compile a different view of the same structs than the
libraries it links -- links cleanly, then corrupts. The compile error was the
easy half.

Result: `xbase` + `xindex` + `memo` + 4 TUs, both smokes green via ctest, and
the main build verified green FIRST because the `DOTTALK_ROOT` substitution
touched libraries the CLI depends on.

**2. Fixing the gateway did not cause the hydration error, it revealed one.**
`app/layout.tsx` renders `<html>` with no `suppressHydrationWarning` while the
no-flash script mutates `documentElement.classList` before React hydrates. That
mismatch had been firing on `:3002` since the theme script was written and was
invisible on `:3000` because React never hydrated there (3 of 490 elements with
a fiber). Yesterday's WebSocket proxy made hydration real; the warning followed.
Verified after the fix: 168/206 hydrated, `[HMR] connected`, no error. It only
ever appeared for dark/system users -- in light mode `classList.toggle('dark',
false)` removes nothing and the markup matches.

**3. The console was dark-only; it now carries both, measured.** 32 hex literals
and 4 rgba values moved into two palettes as 24 new variables, so there is zero
colour literal past the palette block -- the mechanical guarantee, since a
literal cannot follow a theme. Light is the default per the owner ruling of
2026-08-11, `html.dark` restores Codex's midnight palette byte-for-byte, and the
preference shares the website's `localStorage("theme")` key rather than becoming
a fourth theme mechanism. Contrast measured, not eyeballed: light min 4.61:1,
dark min 4.51:1. `tools/dbf/tests/test_maint_console_theme.py`, 7 arms, 4
mutations each proven to fail.

**4. derald.com had not lapsed, and my first answer said it had.** The page a
browser showed -- an unrelated medical practice over a rejected certificate --
was read as evidence the name was gone. Verisign RDAP says otherwise:
registered 2004-06-24, expires **2027-06-24**, GoDaddy, all four client locks
set, last changed 2026-07-08. Retiring a host (`c244300da`, "Point artifact
links to dottalkpp.com") is NOT releasing a name, and collapsing the two is what
produced the wrong sentence. Corrected in `app/retro/page.tsx` with the mistake
left visible. Tracked as OI-001, `where = dns`, because the fix happens in a
registrar panel and no commit here can close it.

**5. A rung below a lane now exists.** `coordination/OPEN_ITEMS.md` plus
`check_open_items.py`, surfaced by the pre-push gate when a row's own NEXT LOOK
date passes. Prior art decided the shape: quips are the documented lightest rung
but live in a gitignored inbox, `BACKLOG_TRIAGE` is a dated snapshot, and
`ai_portal_tasks.yaml` is a publication projection. The nag mechanism was chosen
against AIF-006's own measurement -- ungated obligations held at 33 percent,
gated ones at 83-94. It never blocks: every row is deferred by choice, and
blocking would teach people to delete rows. Three items parked.

**6. The Lab.** `/lab`, a local-only surface reusing all three existing layers
(nav gate, `LOCAL_ONLY_DIRS` strip, publish refusal), proven by planting an
`out/lab` and watching the stripper remove `lab` and `retro` while keeping
`docs`. The Dewey/hierarchy inventory moved there from `/docs/dev/experimental`,
which now serves a stub rather than a 404 -- owner's call, and the right one for
anyone holding the old URL.

## Ground truth ledger

**Verified by running, output read:**

- `dottalkpp.exe` rebuilt green AFTER the `DOTTALK_ROOT` change to
  `src/xbase|memo|xindex` -- the risky half, checked before the lean path.
- Lean build: `xbase.lib`, `xindex.lib`, `memo.lib`, 4 TUs,
  `pydottalk.cp312-win_amd64.pyd`. No `cmd_*.cpp`, no TUI, no BBS.
- `ctest --test-dir build-pydottalk -C Release`: 2/2 passed.
- Console theme guard: 7 arms, 4 mutations, control green.
- Site: 168/206 hydrated on `:3000`, `[HMR] connected`, hydration error gone.
- `/lab/experimental` renders with `noindex, nofollow`; `/docs/dev/experimental`
  renders the stub, not a 404; all four of its links resolve.
- Strip proof in a writable temp root: `out/lab` and `out/retro` removed,
  `out/docs` kept.
- `check_open_items.py`: silent before the date, speaks on it, reports age when
  overdue, names a malformed row rather than dropping it.
- Verisign RDAP for derald.com, quoted above.

**NOT verified:**

- ~~No WSL or Linux build of the lean CMake.~~ **DONE the same day.** It found a
  fifth parent-provided global -- `CMAKE_POSITION_INDEPENDENT_CODE`, set nowhere in
  this repository, failing at LINK on ELF for any shared module. Builds, links and
  imports after the fix (`pydottalk 0.4.0`, Python 3.10). It also proved the house
  index compiles with ZERO lmdb (22 xindex TUs: `cnx_backend`, `cdx_native_backend`,
  `index_manager`), correcting a conflation in the lean file that had collapsed
  LEGACY into NONE.
- **Still MSVC-only: the LMDB index path.** lmdb will not link on this container's
  glibc (`__isoc23_strtol`), so `DOTTALK_INDEX_MODE=LMDB` is untested on Linux.
- **It was a mounted Linux container, not the maintainer's WSL host.** Same class of
  evidence, not identical.
- The lean build has not been run from a clean clone -- only from this tree,
  which already had vcpkg packages present.
- `pydottalk_smoke_x64.py` and the other sandbox probes were NOT run; only the
  two ctest-registered smokes were.
- Whether any smoke needs `dottalkpp.exe` present was never tested, which is why
  `-ViaRootBuild` was kept rather than deleted.

## The session's own errors, recorded rather than smoothed

1. **Brandmark at 4.00:1.** Reused `--acc`, tuned for the page background, on
   the mark gradient. Caught by measuring every pair, not by looking.
2. **A JSX comment as a sibling of `<html>`** in `layout.tsx` -- a syntax error
   that would have failed the build. Caught by reading the file back.
3. **"The domain is no longer ours"** -- an inference from a stranger's webpage,
   written as a finding. Disproved by the registry.
4. **`lib/site.ts` written for a bug that did not exist.** Concluded the two
   `IS_LOCAL_PREVIEW` predicates disagreed because `/retro` was absent from the
   DOM. It was absent because the More menu was COLLAPSED. The measurement was
   right; the inference was wrong. Owner corrected it in five words.
5. **`git status --porcelain` without `-uall`** reported a clean directory that
   held 20 untracked files, and a `/tmp` redirect swallowed output when the
   sandbox disk filled -- twice reading a blank result as an absence.
6. **A grep for `color-scheme: dark`** matched `prefers-color-scheme: dark`
   inside a media query and reported the light theme was not the default.
7. **The PowerShell single-survivor collapse.** `@(...) | Where-Object` returns
   a STRING when one item survives, so `$candidates[0]` returned `D` -- the
   first character of a path. CMake got `-D Python3_EXECUTABLE=D`, ignored it,
   fell back to system Python 3.13.5, and reported "missing Development
   components" -- an error naming the wrong problem entirely.

Six of the seven were caught by measuring a second way. The seventh was caught
by the owner.

## Owed next

- **Commit Codex's slice and the board note.** Highest value, lowest effort.
- `src/bindings/` dead code (OI-002) and `build.ps1 -PyOnly` (OI-003).
- OI-001, derald.com DNS, at the registrar.
- A Linux/WSL run of the lean CMake before anyone claims it is portable.
