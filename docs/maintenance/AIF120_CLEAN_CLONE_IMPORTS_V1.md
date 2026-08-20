---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260820-COWORK-095
  recorded_at_utc: 2026-08-21T01:30:00Z
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
    root: D:/code/ccode
  git:
    branch: development
    baseline_commit: fdacdbfe9
  authorization:
    requested_by: steward (member.derald), in-session -- "next we solve the msvc
      issue for r76".
    scope: >
      Remove the first blocker on R76's MSVC build: eleven tools in gui/uidef
      import a gitignored file, so the CMake target cannot generate its own
      source on a fresh checkout. Writes gui/uidef/ and docs/ only.
  report:
    path: docs/maintenance/AIF120_CLEAN_CLONE_IMPORTS_V1.md
    kind: ruling
---

# AIF-120 -- R87: the MSVC build fails before the compiler starts

**Status: review-needed.** The author does not self-approve.

## 0. The one-paragraph version

MSVC has been the lane's oldest open item since R70, waiting on a Windows
toolchain. Looking for what would break there first, the answer turned out not to
need one: **eleven tools in `gui/uidef` import a GITIGNORED file, and one of them
is a CMake custom command.** On a fresh checkout the R76 target fails while
generating its own source, before a compiler is invoked -- on any platform. MSVC
is simply where it would have been discovered, because a fresh Windows checkout
is the only clean clone anybody was going to make.

## 1. The ruling

**R87. `gui/uidef` loads the tracked VFP reader by absolute path, from
`tools/vfp/read_vfp_binary.py`, through one module that refuses rather than falls
back.**

`gui/uidef/read_vfp_binary.py` is a gitignored working copy. It is not a source.  <!-- cite-check:ignore -->

## 2. What was measured

Eleven files said `from read_vfp_binary import Dbf`:

    contend_test import_mnx import_scx infer_flow manifest relate_test
    uidef_html uidef_text uidef_tk uidef_tk_host uidef_wx

Seven already carried a fix for exactly this, and **the fix was wrong**:

    sys.path.insert(0, os.path.join(HERE, '..', 'vfp'))    # -> gui/vfp

`gui/vfp` does not exist; `gui/` contains `README.md` and `uidef` and nothing
else. From `gui/uidef` the tracked directory is `../../tools/vfp`. The comment
above that line reads *"tools/vfp goes on the path FIRST so the ignored copy can
never shadow it"* -- so the correction was written, explained, believed, and never
did anything. The ignored copy answered every import, and the mistake was
invisible to everyone whose tree contained it, which is everyone who had ever run
the tools once.

The other four never got the fix at all. One of them is `uidef_wx.py`, which
`gui/uidef/CMakeLists.txt` runs as `add_custom_command` to generate the C++.

## 3. Proof, and it is the only proof that means anything here

The gitignored copy was moved out of `gui/uidef` (into `_to_delete/`, because
`device_bash` cannot unlink on the mount), reproducing a clean clone exactly:

    from read_vfp_binary import Dbf
      -> ModuleNotFoundError: No module named 'read_vfp_binary'   <- every tool, before

    import _vfp
      -> tools/vfp/read_vfp_binary.py                             <- after

With the copy still absent: all six importable tools load, all six author scripts
run, **20 fixtures author and all four backends render every one of them.**

## 4. Two design decisions, stated

- **Loaded by explicit path, not through `sys.path`.** Every importer also
  inserts its own directory, so a path-order fix depends on which insert ran
  last -- which is precisely how the original fix could look correct. `importlib`
  on an absolute filename has no ordering to get wrong, and the ignored copy
  becomes unreachable rather than merely lower-priority.
- **It raises rather than falling back.** A fallback to the ignored copy would
  restore the silence being removed.

## 5. Also on the MSVC path

- **`add_executable(uidef_wx_demo WIN32 ...)`** -- added. `WIN32` is ignored off
  Windows; on Windows it is the difference between a GUI-subsystem executable and
  a console one, and since wx supplies `WinMain` there, a console target is the
  classic first MSVC link failure for a wx CMake project: an unresolved entry
  point with nothing in the message that names wx.
- **The engine closure is already Windows-aware.** All 31 translation units this
  target compiles were checked: `output_router.cpp` and `table_state.cpp` guard
  their POSIX headers with `#ifdef _WIN32`, and all three `localtime_r` /
  `gmtime_r` sites already carry `localtime_s` / `gmtime_s` branches with MSVC's
  reversed argument order. No `__attribute__`, no `#pragma GCC`, no
  `__PRETTY_FUNCTION__`, no VLA. `cmake/MSVCWarnings.cmake` already supplies
  `/permissive- /Zc:__cplusplus /Zc:preprocessor /EHsc /utf-8`.
- **`uidef.py` writes the DBF with `"wb"`**, so Windows text-mode translation
  cannot corrupt a document.

**What remains is genuinely a Windows box:** `find_package(wxWidgets REQUIRED)`
needs `wxWidgets_ROOT_DIR` / `wxWidgets_LIB_DIR` or a CMake-built wx config
package, and nothing in this ruling can test a link.

## 6. Reported, not fixed

**The Tk backend crashes on `N5_ordinal_spec.DBF`** -- `_tkinter.TclError: Column
#3 out of range`, in `frame_widget` at `uidef_tk.py:258`, `w.heading(c, text=c)`.
Confirmed PRE-EXISTING: the 2026-08-20 13:50 generator, before the splitter and
before R85.3, fails identically. One of twenty fixtures. An unhandled traceback
is not a refusal, and this backend is supposed to refuse in words.

## 7. How to disprove this

- **R87 is wrong** if `gui/vfp` was ever a real directory, or if some entry point
  needs the ignored copy. Neither is true today: `git ls-files` places the reader
  only at `tools/vfp/read_vfp_binary.py`.
- **Section 5's MSVC claims are inspection, not a build.** Any one of them is
  disproved by a compiler. That is the point of running it.

## 8. Good Neighbor note

- **What changed:** `gui/uidef/` -- one new module (`_vfp.py`), eleven import
  sites, two dead `sys.path` inserts removed, and `WIN32` on one
  `add_executable`. The gitignored `gui/uidef/read_vfp_binary.py` was moved to  <!-- cite-check:ignore -->
  `gui/uidef/_to_delete/`; it is untracked either way and the steward can delete
  that folder.
- **Whose area:** AIF-120. No engine source, no gate, no other lane's file.
- **What authorization:** steward, in-session, "next we solve the msvc issue for
  r76".
- **How to verify:** delete or move `gui/uidef/read_vfp_binary.py`, then run  <!-- cite-check:ignore -->
  `python3 author_cases.py` and `python3 uidef_wx.py P8_splitter_nested.DBF out.cpp`.
  Both work. Before this change both raise `ModuleNotFoundError`.
- **How to undo:** revert. Nothing outside `gui/uidef` is touched, and the
  `WIN32` flag is inert on Linux.
