---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260822-COWORK-112
  recorded_at_utc: 2026-08-22T19:52:00Z
  agent:
    provider: Anthropic
    product: Claude (Cowork)
    model: claude-opus-5
    access_mode: local_write
  session:
    id: not_exposed
    chat_reference: not_exposed
    run_id: COWORK-20260822-001
  project:
    id: project.x64base.runtime
    root: D:/code/ccode
  git:
    branch: development
    baseline_commit: 3908abed5
  authorization:
    requested_by: maintainer (member.derald), in-session 2026-08-22 -- "your
      rebuilds are usually costly, a single change and I am rebuilding every
      single .cpp", then "fix it all" after the three mechanisms were measured.
  report:
    path: docs/maintenance/AIF122_BUILD_STAMP_REBUILD_COST_RULING_V1.md
    kind: ruling
---

# AIF-122 -- one edit rebuilt every .cpp: three mechanisms, measured and fixed

Status: **ruling, review-needed.** Code landed under the steward's explicit
"fix it all"; the author does not self-approve.
Owner: member.derald. Author: member.ai.claude.cowork, run `COWORK-20260822-001`.
Date: 2026-08-22. Baseline `3908abed5`. Claim: `coordination/aif/AIF-122.claim`.

The steward's question was **"is it because we are sitting on two different
stamps?"** Close. It is **one stamp, on four hundred command lines.**

---

## 1. The measurement that separated the three causes

HEAD did not move between the build and the probe, so the SHA was identical,
and the regression suite had just run:

    STUDENTS.dtx before REGRESSION RUN NAME_AMBIG : 12:22:02
    STUDENTS.dtx after                            : 12:36:10
    cmake --build  (reconfigure fired, SHA unchanged)
    .cpp files compiled                           : 1

**One file.** So a reconfigure with an unchanged SHA is nearly free, and the
full-tree rebuilds seen all day were paid for by the SHA, not by the
reconfigure.

| # | trigger | mechanism | measured cost |
|---|---|---|---|
| 1 | a commit | the git SHA is a `-D` on every TU's command line | **~400 TUs** |
| 2 | any configure | `file(WRITE)` rewrites a generated TU unconditionally | 1 TU |
| 3 | a regression run | 254 of 257 `CONFIGURE_DEPENDS` entries are runtime data | ~13 s reconfigure |

## 2. The expensive one -- the stamp was on every command line

`CMakeLists.txt:394-404` (as was):

```cmake
target_compile_definitions(${target_name} PRIVATE
    DOTTALKPP_VERSION=\"${DOTTALKPP_VERSION_LABEL}\"
    DOTTALKPP_VERSION_DATE=\"${DOTTALKPP_VERSION_DATE}\"
    DOTTALKPP_GIT_SHA=\"${DOTTALKPP_GIT_SHA}\"
    DOTTALKPP_GIT_DIRTY=${DOTTALKPP_GIT_DIRTY})
```

Not a generated header -- a `-D` on the compiler invocation of **every TU in
every target it touched**, applied through `dottalk_apply_common_settings`.
Change the SHA and every command line changes, so every TU recompiles. Observed
twice: `83f5032e` -> `3908abed`, full tree, for change sets of 8 and 4 files.

**The readership is two files.** `DOTTALKPP_GIT_SHA` and its three siblings are
consumed in exactly one place -- `include/dottalk/version.hpp`, which wraps them
in inline accessors behind `#ifndef` fallbacks -- and that header has **two
includers**: `src/cli/cmd_version.cpp` and `src/gui/wx/main_frame.cpp`. Four
hundred translation units carried a value two of them read.

**Fixed:** the stamp is emitted as `generated/dottalk/version_stamp.hpp` from
`config/version_stamp.hpp.in` via `configure_file`, which is
**copy-if-different** -- the file's mtime moves only when a value actually
changes. `version.hpp` picks it up behind `__has_include` and keeps its
fallbacks, so the header still stands alone in a non-CMake build.
`dottalk_apply_version_metadata()` is **deleted**, not emptied: an emptied
function with two live call sites is the AIF-079 shape this lane has now
catalogued five times.

**A commit now recompiles 2 files instead of ~400.**

## 3. The proof of the mechanism was in the same build log

The single file that recompiled on the free reconfigure was
`cmd_palette_stub.cpp`, and `src/CMakeLists.txt:484-496` explained it: the
PALETTE stub was emitted with **`file(WRITE)`**, which is *not*
copy-if-different and rewrote byte-identical content with a fresh mtime on
every configure.

**The contrast is the evidence.** The same configure regenerated
`build_vectors.hpp` through `configure_file` and that cost **zero** TUs. One
build log, two CMake commands, one generated file each, **1 against 0**. That
difference is the whole argument for sec 2's fix, and it arrived by accident.

Two further facts, found by the steward searching Explorer for the file:

- The generated body was a CMake **bracket argument** (`[=[ ... ]=]`), which
  performs no variable expansion, and contained nothing to expand anyway. **It
  was a constant** -- seven fixed lines of C++, generated at configure time.
- **Thirteen copies existed across eight build trees, at two byte counts** --
  219 in the Windows trees, 213 in the WSL ones. Six bytes on a seven-line
  file: `file(WRITE)` writes native line endings, so the generated TU was not
  byte-stable across platforms.

**Fixed:** the stub is now `src/cli/cmd_palette_stub.cpp`, a tracked source
file picked up by the existing `GLOB_RECURSE` like every other command. A
constant belongs in source, where a person can find it -- which is how it was
found.

## 4. Verifying the build dirtied the build

`CMakeLists.txt:646-651` registered every file the product manifest names as
`CMAKE_CONFIGURE_DEPENDS`. **254 of those 257 entries are runtime data under
`dottalkpp/data/`**, including `dottalkpp/data/dbf/x64/STUDENTS.dtx`, a memo
sidecar the regression suite writes. CMake named the trigger itself, every
time:

    the file 'dottalkpp/data/dbf/x64/STUDENTS.dtx' is newer than
    'build/CMakeFiles/generate.stamp.depend'

So the loop closed on itself: **verify -> data file touched -> reconfigure.**
The inventory's only consumers are the `install()` rules; the file list is an
input to packaging, not a reason to re-run CMake.

**Fixed:** `${DOTTALK_PACKAGE_FILES}` removed from the property. The manifest
and the script that reads it stay -- those are the things whose change
genuinely alters the configure.

## 5. A correction to my own framing, same session

Before measuring, I told the steward the mechanisms "compound, and together
make every commit-and-check cycle cost the whole tree." **That overstated it.**
Measured, #3 costs 13 seconds and #2 costs one file; **#1 is essentially the
entire rebuild bill.** They are three findings, not one compounding one.

Recorded because the wrong framing would have sent the fix at the wrong file:
#3 is the more interesting-looking defect and #1 is the one that hurts. This is
the house's own "measure the claim, not a proxy" rule catching its own author.

## 6. Verification

**Behavioural, not merely syntactic** -- the stamp path was compiled and RUN
against `include/dottalk/version.hpp`, both ways:

    with generated stamp : v0.6 (2026-08-22, 3908abed dirty)
    without (fallback)   : v0.0-unconfigured (Aug 22 2026)

The first is **byte-identical to the banner the real build prints**, and the
second degrades exactly as `version.hpp`'s existing comment promises -- an
implausible version rather than a plausible lie.

Also clean: `g++ -fsyntax-only -std=c++20 -Wall -Wextra` on
`src/cli/cmd_palette_stub.cpp`, and `cmd_version.cpp` with and without the
generated header on the include path.

**OWED, steward-side:** MSVC configure + build, then `REGRESSION ALL`. The
expected new evidence is the **second** build: commit anything, rebuild, and
count compiled files. It should be 2, not ~400.

**Superseded -- this OWED item was carried out and this expectation was wrong.
See sec 6a.**

## 6a. AMENDMENT 2026-08-22 -- the post-fix measurement, and a second wrong prediction by the author

The OWED work in sec 6 was carried out. All three fixes landed as `fe4dae225`,
MSVC configure + build clean, `REGRESSION ALL` green on all 8 defaults, and the
banner reads `v0.6 (2026-08-22, fe4dae22 dirty)` -- not `0.0-unconfigured`, so
the generated header is genuinely on the include path and the fallback is not
silently winning.

Then four probes:

| probe | state | reconfigure? | .cpp compiled |
|---|---|---|---|
| 1 | pre-fix, HEAD unmoved, suite had just run | yes | **1** |
| 2 | post-fix, no source change | no | **0** |
| 3 | post-fix, after an empty commit that moved the SHA | no | **0** |
| 4 | post-fix, SHA still moved, configure FORCED | yes | **3** |

**Fix #2 is confirmed** -- probe 2 costs 0 where the old tree paid 1 on every
configure. **Fix #3 is confirmed** -- `REGRESSION ALL` wrote `STUDENTS.dtx` and
no `CMake is re-running because ... STUDENTS.dtx` line followed.

**Fix #1 is confirmed by probe 4, not by probe 3**, and sec 6 was wrong about
which probe would show it. I predicted the post-commit rebuild would be "2"
(in conversation, "about 3" once the second GUI target was counted), and said
that ~400 would mean I had missed a site. Probe 3 returned **0** -- neither of
the two outcomes I told the steward to watch for.

The error is in the framing, not the fix. `configure_file` runs at **configure**
time only. Probe 3 moved the SHA but never reconfigured, so the stamp header was
never regenerated, so nothing that depends on it rebuilt. The `~3` figure is the
cost of *a commit plus a configure*, not of a commit.

**Fixes #1 and #3 interact, and sec 4 did not anticipate it.** #3 removed the
mechanism that used to force a reconfigure on nearly every cycle. With that
gone, configures are rare, so the SHA is re-read rarely, so #1's per-commit cost
is usually zero and occasionally ~3. Better than predicted, for an unpredicted
reason.

To close the #1 measurement honestly, force a configure and count:

    cmake -S . -B build
    cmake --build build --config Release 2>&1 | Tee-Object tmp\rebuild_probe4.txt
    (Select-String -Path tmp\rebuild_probe4.txt -Pattern '\.cpp$' | Measure-Object).Count

Run and measured: **3**, and the three are named in the build log --
`main_frame.cpp` twice (once for `dottalk_wb`, once for `dottalk_wb_next`) and
`cmd_version.cpp` once. That is exactly the includer set identified in sec 2, with
no fourth file and no fourth target. **Fix #1 is confirmed: ~400 -> 3 per
configure, 0 per commit.**

Probe 4 is the falsifier, not probe 3. Had it returned ~400 the stamp would
still be on the command lines; had it returned 0 the header would not be
regenerating at all and the fix would be inert. It returned neither.

### Consequence: the staleness moved, it did not go away

The banner will now go stale **more often than before**, because the SHA is only
re-read at configure time and configures are now rare. The data-file
`CONFIGURE_DEPENDS` churn that sec 4 removed was accidentally acting as a stamp
refresher -- expensively, but it was doing it.

This is R118's staleness finding re-pointed, and it is the same line of CMake
seen from the other end (sec 2). The trade is deliberate and correct: a stale
SHA in a banner is cheap, 400 TUs per commit is not. But it is a trade, and it
belongs in the record rather than being rediscovered. If a fresh SHA ever has to
be **guaranteed**, the fix is a **build-time** custom command that writes the
stamp header, still copy-if-different -- not a return to per-TU defines.

### Two smaller notes from the probes

- `git commit --allow-empty` reported `1 file changed, 5 insertions(+), 5
  deletions(-)`: the `tier0-refresh` hook regenerated `TIER0_STATE.md`. An
  `--allow-empty` commit is not an inert probe in this tree.
- The probe commit `c9efaae94` is **local, not pushed**. Keeping or dropping it
  is the steward's call.

**Evidence tier for this amendment: measured throughout.** Probes 1-4 are
compiled-file counts from build logs; the three files in probe 4 are named by
the log itself, not inferred.

## 7. Found while working, NOT fixed -- AIF-079 instance #6

`src/palette/cmd_palette_shim.cpp` defines a real `cmd_PALETTE` that forwards
to `cmd_FOX_PALETTE`. `src/palette` is in `_EXCLUDE_DIRS` ("palette handled
explicitly"), and the only CMake reference to that basename is a prune entry
for a **different, nonexistent** path (`src/cli/cmd_palette_shim.cpp`,
`src/CMakeLists.txt:321`). So the shim is referenced by no build file and is
compiled by nothing.

It was checked because adding a second `cmd_PALETTE` definition would have been
a duplicate-symbol link error; it is not, and the check is the finding.
Reported, not touched -- deleting it is a separate ruling.

## 8. Evidence tier

**Measured:** sec 1 (timestamps and the compiled-file count), sec 3 (the 1-vs-0
contrast, the 13 copies at two byte counts), sec 4 (254 of 257), sec 6.
**Source-evidenced:** sec 2 (both the define site and the two includers), sec 7.
**Chat/AI output:** sec 5's reading of my own error.

## 9. Good Neighbor note

- **What changed.** `CMakeLists.txt` (stamp `configure_file`; the metadata
  function and its two call sites deleted; data files off `CONFIGURE_DEPENDS`);
  `src/CMakeLists.txt` (stub generation removed); `include/dottalk/version.hpp`
  (guarded include of the stamp); **new** `config/version_stamp.hpp.in`;
  **new** `src/cli/cmd_palette_stub.cpp`; this document; the claim file; the
  intake row.
- **Whose area.** The build system, which is shared ground and not this lane's
  by default. It has an explicit go: the steward's "fix it all", 2026-08-22.
- **What authorization.** As above. Covers these three mechanisms only. It does
  NOT cover deleting the dead palette shim (sec 7), the eight stale build trees
  under `ccode`, or the `__DATE__`/`__TIME__` split across four TUs that R118's
  notes separately record.
- **How to verify.** sec 6's two commands reproduce the behavioural check
  without this tree. Then: build, commit a one-line change, rebuild, count
  compiled files.
- **How to undo.** Revert the commit. The two new files are additions; nothing
  was renamed, and no generated artifact outlives a `build/` directory.
