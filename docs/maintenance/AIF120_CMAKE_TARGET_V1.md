---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260820-COWORK-085
  recorded_at_utc: 2026-08-20T13:10:00Z
  agent:
    provider: Anthropic
    product: Claude (Cowork)
    model: claude-opus-5
    access_mode: local_write
  session:
    id: not_exposed
    chat_reference: not_exposed
    run_id: COWORK-20260818-001
  project:
    id: project.x64base.gui
    root: D:/code/ccode/gui
  git:
    branch: development
    baseline_commit: cc295406b
  authorization:
    requested_by: maintainer (member.derald), in-session -- "build it", then
      "look at code/ccode/cmakelists.txt for options", then "thats those two
      demos" identifying DOTTALK_WITH_WX and DOTTALK_WITH_GUI as the template
      samples.
    scope: >
      A CMake target that builds a wx frontend from a UIDEF document. Adds
      gui/uidef/CMakeLists.txt only. Reads src/ and config/; changes neither,
      and does not touch the root build.
  report:
    path: docs/maintenance/AIF120_CMAKE_TARGET_V1.md
    kind: ruling
---

# AIF-120 -- R76: the UIDEF document is a CMake source, and extracting the target found the same globals pydottalk found

**Status: review-needed.** The author does not self-approve.

## 0. The one-paragraph version

R72 left "a CMake target" as an open unit and noted the 46-object link had been
assembled by hand. `gui/uidef/CMakeLists.txt` closes it, and does one thing worth
more than convenience: **it makes the document a build input.** `cmake --build`
authors `FRAMEDEMO.DBF` from `author_frame.py`, generates C++ from it with
`uidef_wx.py --stream`, compiles that against the engine, and links a running
window. If a design table is a source, the build should say so; now it does.

**Evidence tier: runtime-proven.** Clean configure and build from an empty tree in
62 seconds, 66 translation units, four static libraries, a 2.27 MB binary, and the
window renders MCC records.

## 1. What the build does

```
author_frame.py  ->  FRAMEDEMO.DBF        the document
uidef_wx.py      ->  FRAMEDEMO_ui.cpp     163 lines of generated C++
wx_host.cpp      ->  the host (R72)
                 ->  uidef_wx_demo
```

Both intermediates are `add_custom_command` outputs with real `DEPENDS`, so editing
`author_frame.py` re-authors the document and regenerates the C++; editing
`uidef_wx.py` regenerates without re-authoring. Neither is checked in, which is
exactly why R75 made the fixtures reproducible instead of committing them.

`-DUIDEF_DOCUMENT=<stem>` selects a different document.

## 2. Standalone, on the pydottalk precedent

Configuring the root build to produce one window would also build `dottalkpp` --
roughly 400 `cmd_*.cpp`. AIF-119 measured that exact waste for a four-source Python
module and answered it with a standalone project that adds the libraries it needs
by `DOTTALK_ROOT` and lets them describe themselves.

Same answer here, same reason. This file adds `src/xbase`, `src/memo`, `src/xexpr`
and `src/help` as subprojects and **does not restate one line** of their source
lists. Measured cost of the difference: **66 translation units** against the
several hundred a root configure would compile.

## 3. It is NOT `DOTTALK_WITH_WX`, and that is an owner ruling

The root already has:

```cmake
DOTTALK_WITH_GUI  "Build GUI-neutral application services"   OFF
DOTTALK_WITH_WX   "Build wxWidgets windowed GUI frontend"    OFF
```

**Owner, 2026-08-20: those two build the template samples** -- the wx GUIs written
in parallel as tests, for someone to copy from, not a permanent product. So this
target attaches to neither. Wiring `uidef_wx_demo` into `DOTTALK_WITH_WX` would
fuse a generated frontend into a sample's build and make one option mean two
things.

If the root build should ever gain this target, the house pattern is a new option
plus `cmake/AddUidefWxIfPresent.cmake` on the `AddPydotTalkIfPresent` model. Not
done here; it is an owner decision about the root build.

## 4. The globals the root supplies silently -- AIF-118, reproduced exactly

The first build failed twice before it failed usefully:

```
include/xbase.hpp:31: fatal error: dottalk/build_vectors.hpp: No such file or directory
src/help/message_catalog.cpp:18: fatal error: cli/memo_field_store.hpp: No such file or directory
```

AIF-118 recorded this class for pydottalk in August: *"extracting it exposed four
globals the parent had been supplying silently"* -- and **the first item on that
list was the generated `dottalk/build_vectors.hpp`.** It was the first thing to
fail here too, in a different consumer, four months later. `xbase.hpp` includes it
unconditionally; `src/help` includes `cli/...`; neither path is set by anything
below the root.

**Fixed by reuse, not restatement.** This file runs the root's own
`config/build_vectors.cmake` and its own `build_vectors.hpp.in` template, then sets
the include paths directory-scoped the way the root does at `CMakeLists.txt:300`.
A second hand-kept capacity table would be the drift AIF-119 forbids.

Worth stating because it is a prediction that came true: AIF-118's closeout said
*"if the root build ever grows a Linux .so target it needs the same line"* about
PIC. The generalisation is broader than that sentence -- **any target extracted
from this tree inherits the parent's silent globals, and the list is already
written down.** Reading it first would have saved this ruling two failed builds.

## 5. The one list this file carries

29 files, listed explicitly. They belong to **no library target** -- they are
globbed straight into the `dottalkpp` executable at `src/CMakeLists.txt:92`. Of the
46 translation units R72 measured, 16 belong to a library and are linked without
being named; the other 29 have never had a list of their own, so this is the first
one rather than a second copy.

The right end state is a `dottalk_cli_rt` static library that both `dottalkpp` and
this target link. That is **R61's boundary with a build consequence**, it is an
engine-build change, and it belongs to whoever owns `src/CMakeLists.txt`. Until
then this list drifts LOUDLY: a new dependency fails at link, not silently at
runtime. Each path is checked at configure time, so a moved file fails with its own
name rather than as a missing symbol.

**A hazard worth naming while nobody is standing on it:** `src/CMakeLists.txt` has
a duplicate-basename shadow guard (AIF-043) that globs library sources from a
**hardcoded list of five directories** -- `xbase`, `xindex`, `xexpr`, `value`,
`memo`. A future `dottalk_cli_rt` built from `src/cli` would be outside that list
and therefore invisible to the guard, which is precisely the shadow the guard
exists to catch. Whoever builds that library should widen the guard in the same
commit.

## 6. Proof

```
cmake -S gui/uidef -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build -j4
```

| | |
|---|---|
| clean configure + build, empty tree | **62 s** |
| translation units | **66** |
| libraries built | `libxbase.a`, `libmemo.a`, `libxexpr.a`, `libdottalk_helpdata.a` |
| binary | `uidef_wx_demo`, 2 268 520 bytes |
| generated C++ | 163 lines, produced by the build |
| run | `uidef_host: 2 area(s) open, cursor hook installed, SOURCE relations attached`, then the window |

Capture: `docs/maintenance/evidence/AIF120_R76_cmake_build.png` -- the tree with
`(matches: 2)`, the summary reading `ENROLL : 2`, three MCC rows, and the
`status_line()` footer, all from a binary produced by `cmake --build` and nothing
else.

The only build warnings are pre-existing `-Wformat-truncation` in house library
sources (`field_codec.cpp`, `value_normalize.hpp`, `expr/date/date_arith.cpp`).
None in this target and none in generated code.

## 7. Open

- **MSVC.** Still. This configures and builds under gcc 13 / wx 3.2.4 / Linux and has never seen the maintainer's compiler. `cmake/MSVCWarnings.cmake` is wired in, which is a start and not a test.
- **`DOTTALK_WITH_INDEX` defaults OFF**, so the LMDB/CDX path is not exercised by this target as configured. R73's positive half remains owed.
- **`dottalk_cli_rt`** -- section 5. The list works; the library is better.
- **Root-build integration** -- section 3, deliberately not done.

## 8. Good Neighbor

| | |
|---|---|
| What changed | new `gui/uidef/CMakeLists.txt`; this ruling; one evidence image; ledger rows |
| Whose area | AIF-120. `src/`, `config/` and the root `CMakeLists.txt` are **read only** -- nothing in the engine build is touched |
| Authorization | maintainer, in-session: "build it", plus the ruling on what the two existing wx options are for |
| How to verify | the two commands in section 6, then `R70_DBF=<dbf/x64> UIDEF_TABLES=STUDENTS,ENROLL ./uidef_wx_demo` |
| How to undo | delete the file. Nothing else references it; the root build never sees it |
| Risk | none to the existing build, which does not know this target exists |

## 9. Handoff -- PowerShell, run in `D:\code\ccode`

```powershell
git status -uall

git add gui/uidef/CMakeLists.txt
git add docs/maintenance/AIF120_CMAKE_TARGET_V1.md
git add docs/maintenance/evidence/AIF120_R76_cmake_build.png
git add docs/maintenance/AIF120_LANE_STATUS_AND_FIXTURES_V1.md

git status -uall

git commit -m "AIF-120: R76 -- a CMake target that builds a wx frontend FROM a UIDEF document; extracting it hit the same silent parent globals AIF-118 recorded for pydottalk"
```
