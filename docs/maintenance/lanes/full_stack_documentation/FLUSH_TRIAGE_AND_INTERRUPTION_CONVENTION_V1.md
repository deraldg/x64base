# Flush triage + interruption convention

- **Status**: convention + live triage
- **Owner**: member.derald
- **Recorded**: 2026-07-27 (Cowork), run DOCFLUSH-20260722-001
- **Goal it serves**: reach the web again (publish to x64base.com). Two prior flushes
  reached it "rough"; each pass improves the process. This is the third.

## The interruption convention (member.derald, 2026-07-27)

A flush is a long push toward publication, and it gets interrupted -- a data fire, a
rename, a "wait, this is wrong". Undisciplined, every interruption becomes a full
detour and the web recedes. So every interruption is CATEGORIZED the moment it
arrives, and the category decides what happens to the main thread:

| category | meaning | what happens to the flush | how it is recorded |
|---|---|---|---|
| **minor** | small, non-blocking | keep going; do NOT detour | one line in the triage board (so it is not forgotten) |
| **medium** | needs review, not now | keep going; flag for a review pass | a row with a decision owed |
| **hard stop** | flush cannot correctly continue past it | STOP, handle it, then resume | its own note + resolution before the thread continues |

The rule that makes it work: **a minor or medium interruption is NOTED, not chased.**
The note is the safety net that lets the thread stay on the web goal. Only a hard stop
earns a detour.

### This session, categorized in hindsight (worked example)

- STUDENTS.dbf was a mangled 0-record stub -> **hard stop** (publishing/teaching off
  corrupt sample data is wrong): stopped, replaced, reindexed, proved, resumed.
- `BROWSE->BROWSER` rename -> **medium** (correct call, needed review + rebuild):
  handled, but it re-staled SYSCMD -- exactly the kind of ripple a medium item should
  leave a NOTE for. It did not, which is why a guard caught it later. Lesson: a medium
  interruption's note must list its downstream ripples.
- LMDB oversize, identity errors, help gaps -> **minor/medium**: noted and worked in
  order without derailing the push.

## Live triage board -- open items toward the web

Ordered by what blocks publication. "Hard stop" = the published docs would be WRONG
until fixed; "medium" = review/architecture, current state can ship if labeled;
"minor" = note and defer.

### 2026-07-28 push -- manual phase COMPLETE and PUBLICATION-READY
Full record: `runs/DOCFLUSH-20260722-001/SESSION_CLOSEOUT_SELFDOC_FULLSTACK_PUSH_2026-07-28.md`.
The manualgen curation chain was re-based to harvest `HELPMETA-20260728T003402Z`
(six gates green), the prose lane was parked (July-identical, hardcoded renderer),
and the data-driven command reference (164/164) was ACCEPTED via an authorized
gate-4 apply (`MANRUN-20260728T041930Z-5DE4733C`, 168 rows, reversible). The five
functions `STUFF/PADL/PADR/PADC/PROPER` are in the accepted manual;
`audit_manual_publication_readiness` = `pass=26 review=0 fail=0`. Commits AIF-068
`2d138e001`, `9a1c8981b`, `08173b663`. Web ascent (promotion -> website -> Pages ->
verify) NOT started. Flush is PARTIAL: browser rename deferred (owed, below).
New owed items from this push:
- Revert the parked prose-policy expansion (prose_review.py 8->16 + selective_merge
  selector) to restore its two risk-boundary tests; the 2026-07-28 prose decision
  then becomes moot.
- Add `@dottalk.usage` contracts for uncontracted-but-real commands `UDATE`,
  `UDATETIME`, `UNOW`, `UTIME`, `ORDER`; re-harvest to promote them out of
  partial-help (they currently mis-classify as source-miner noise).
- MDO-347E candidate combined still 25 sections; refresh to 28 for clean MDO-350E
  re-execution lineage (active target already reconciled to 28 in the status doc).
- Published manual + accepted artifacts are untracked working state -- decide track
  vs documented-gitignore.
- AIF-068 has a claim file but no intake-queue row (prepush advisory).

### HARD STOP -- must be true before the catalog-derived docs publish
- **Re-seed SYSCMD** (runtime). Status 2026-07-28: SYSCMD is 212 and no longer names
  the dead `SIMPLEBROWSE`/`SMARTBROWSE` -- but it does NOT yet name the new
  `...BROWSER` either, because the `app_*_browser.cpp` rename slice is uncommitted and
  `generate_syscmd` mines only git-tracked files. Commit that slice -> re-seed to
  SYSCMD 214 -> re-harvest so the browser rename can publish (see the 2026-07-28
  push block above; deferred from the partial flush).
- **Remove the stale `dotref` browse duplicates** (lines 854/1013: `SMARTBROWSE`/
  `SIMPLEBROWSE`, no-R) that sit beside the correct `...BROWSER` entries. `refcheck`
  flags them; `cmdhelp` mines `dotref`, so they publish wrong help.

### MEDIUM -- review / architecture (ship labeled, resolve deliberately)
- Retire `generate_syscmd.py`; make **metacollect** the sole harvester and re-harvest
  current source (M0 unwind). Single source of truth.
- Build the **M3 `*ref` emitter** (contracts -> `dotref`/`foxref`/... via metacollect)
  so the catalogs generate instead of drift.
- ~~`foxref` documents 5 unimplemented functions (`STUFF/PADL/PADR/PADC/PROPER`)~~
  DONE (2026-07-28): implemented, catalogued (SYSFUNC 74), and accepted into the
  manual command reference via gate-4 apply `MANRUN-20260728T041930Z-5DE4733C`.
- `FOXREF` -> `@dottalk.file` reference-module reclassification (last identity error).
- `DDICT` PDLC turnover (non-canonical contract; excluded from SYSCMD until repaired).
- `@dottalk.inert` ratification (proposed; no confirmed instance).
- `CASE` typing (`syntax-command` vs `command`).
- Wire `refcheck` + `normcheck` into `stack_audit_v1`/prepush.

### MINOR -- note, do not block
- 3 help gaps `BBS`/`CANARY`/`NET` (contracts exist; the generator closes them).
- `STU_REPEAT`/`STU_UPPER` -- student-extension functions; confirm authority.
- Maintenance family audit (`DDICT/MSGMGR/MANUAL/MANSTAR/BBOX/MAINT`, gated/experimental
  inspectors, "possibly antiquated").
- Restored x64 `STUDENTS` env is 128 MiB; a `BUILDLMDB CLEAN TINY` drops it to 32.
- `SMARTBROWSE` back-compat alias dropped in the rename.
- **Browsers dropped from SYSCMD by the `BROWSE->BROWSER` rename** (surfaced by the
  2026-07-27 SYSCMD re-seed, 214->212). Root cause (found 2026-07-27):
  `generate_syscmd.tracked()` mines only `git ls-files`, so it sees ONLY git-tracked
  files. The renamed impls `src/cli/app_simple_browser.cpp` / `app_smart_browser.cpp`
  are UNTRACKED and the old `cmd_*_browser.cpp` are `git rm`-pending, so their
  `@dottalk.usage` contracts are invisible to the generator. Registration lives in
  tracked `shell_commands.cpp` (-> "registered"); the contract lives only in the
  untracked file (-> "registered but uncontracted"). Two parts:
    - DONE: fixed a typo in `app_simple_browser.cpp` -- it declared
      `command: SIMPLEBROWSERR` / `owner: DOT|SIMPLEBROWSERR` (double-R); corrected to
      `SIMPLEBROWSER` so the eventual commit lands without a new IDENTITY ERROR.
      (`app_smart_browser.cpp` was already correct.)
    - OWED: commit the browser rename slice (`git add` the two `app_*_browser.cpp`,
      `git rm` the two `cmd_*_browser.cpp`; CMakeLists already updated, runtime already
      works). Only once tracked does `generate_syscmd` mine `SIMPLEBROWSER`/
      `SMARTBROWSER`; the next SYSCMD seed then re-admits them (212 -> 214). Likely
      another session's in-flight work -- do not fuse into unrelated slices.
  Non-blocking -- a coverage gap, not a contradiction, so `normcheck`/`refcheck` stay
  green until then.
- **Manualgen harvest feeder -- BUILT 2026-07-27** (`HELP_META_HARVEST_EXPORT_v1`).
  The HELP/META CSV harvest (manualgen's input) is regenerable again; it had been
  frozen May exhaust with only 1 of 14 export scripts committed. Run
  `HELPMETA-20260727T233835Z` carries the current 10 tables. OWED: refresh the 4
  stale `META_*` sources (SYSENTVAR/SYSFLDDIC/SYSHELP/SYSMSG, currently
  carried-labelled) and a native MAINT harvest verb to replace the .ps1/.dts
  scaffolding. Closeout: `SESSION_CLOSEOUT_HELP_META_HARVEST_FEEDER_2026-07-27.md`.

## How this speeds the flush

The two guards (`refcheck`, `normcheck`) mean hard stops now ANNOUNCE themselves
instead of being discovered by eye near the finish. So the triage board can be trusted:
if both guards are green and the hard-stop rows are closed, the catalog surface is
publish-clean. The medium/minor rows travel WITH the publication as labeled state
rather than blocking it -- which is how a rough flush becomes a quick one.
