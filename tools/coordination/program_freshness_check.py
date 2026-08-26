#!/usr/bin/env python3
"""program_freshness_check.py -- Gate 0 for EVERY program the doc push runs.

WHY THIS EXISTS, in the owner's words (2026-08-25):

    "so step 1 is really compile all of the programs first in the fullstack push"

Gate 0 already answers that for ONE program. `help_build_order_check.py` checks
`exe newer than catalogs` for `dottalkpp.exe`, because dotref/foxref/edref are
COMPILED IN and a stale engine republishes the old catalog. That check is
correct and this tool does not repeat it -- see "What this does NOT check".

THE PUSH RUNS MORE THAN ONE PROGRAM. Flush v6 Phase 5 runs `metacollect`, a
SEPARATE CMake target, default OFF, whose staleness nothing was testing. On
2026-08-26 it was verified BY HAND -- exe 2026-08-25 12:59 against a newest
source of 2026-08-05 20:56 -- and a hand check is not a gate. Had it been stale,
Phase 5 would have emitted candidates from a source scan that predated the
change under test: the 2026-08-12 failure verbatim, one program to the left.

Two questions, one per program kind:

  COMPILED   is the binary newer than every source that goes into it?
  PYTHON     what version does it demand, and is the demand an EQUALITY?

The second exists because on 2026-08-26 a `!= (3, 12)` guard made a runnable
tool read as blocked. An equality guard refuses 3.13 as readily as 3.10, and the
tools it guards carry `from __future__ import annotations` -- written to be
portable, then pinned to one version. A guard is a fact about an INTERPRETER,
not about the question; this reports the shape so the pin is a DECISION rather
than an inheritance.

THE MANIFEST CANNOT GO STALE SILENTLY. Every `add_executable()` in the tree is
either DECLARED below or EXCLUDED below with a reason. A target that is neither
is reported by name. A manifest that quietly stops covering the tree is the
defect this lane keeps paying for -- a written record outliving the thing it
points at -- so the record is checked against the thing.

  $py tools/coordination/program_freshness_check.py            # from repo root
  $py tools/coordination/program_freshness_check.py --root .   # explicit
  ... --strict     an undeclared add_executable target is an ERROR, not a note

Exit: 0 all declared programs fresh, 1 a program is stale, 2 could not read.
No third-party deps. Runs on Python 3.9+.
Owner: member.derald . steward: member.ai.claude.cowork . lane: AIF-068.
"""
import argparse
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# DECLARED: the programs a full-stack doc push actually runs.
#
# `sources` are repo-relative. A path ending in "/" is a directory: every .cpp
# and .hpp under it counts. The metacollect list is the dt_meta TU list from
# CMakeLists.txt:771 plus the entrypoint -- keep it in step with that block, and
# note that CMakeLists.txt:771 is enumerated precisely so it CAN be kept in step.
# ---------------------------------------------------------------------------
COMPILED = {
    "metacollect": {
        "role": "Phase 5 -- SYSCMD/SYSFUNC/SYSARGS candidate emit, and --compare",
        "exe": ["build/Release/metacollect.exe",
                "build/metacollect-docflush/Release/metacollect.exe",
                "build/metacollect"],
        "sources": [
            "src/tools/metacollect_main.cpp",
            "src/meta/metacollect.cpp",
            "include/dt/meta/metacollect.hpp",
            "src/cli/expr/date/date_arith.cpp",
            "src/cli/expr/date/date_utils.cpp",
            "src/cli/expr/fn_date.cpp",
            "src/cli/expr/fn_numeric.cpp",
            "src/cli/expr/fn_string.cpp",
            "src/cli/expr/function_catalog.cpp",
            "src/datadict/ddict_read_helpers.cpp",
            "src/datadict/ddict_dbf_reader.cpp",
            "src/common/path_resolver.cpp",
            "src/common/path_state.cpp",
        ],
        "cmake_option": "DOTTALK_BUILD_METACOLLECT",
    },
}

# PYTHON programs the push runs, with the floor each one ACTUALLY needs.
# "floor" is what the code requires; the tool reports the guard it FINDS and
# compares. Where they disagree, the guard is the thing to look at.
PYTHON_PROGRAMS = {
    "tools/manualgen/manualgen.py":
        {"role": "Phase 6 -- inventory / validate / export-manifest / build-dry-run"},
    "tools/manualgen/build_postbaseline_supported_command_pages.py":
        {"role": "Phase 6 -- R127 allow-list page generator"},
    "tools/manualgen/build_complete_command_reference_index.py":
        {"role": "Phase 6 -- provenance-layered index"},
    "tools/fullstack_docs/export_help_meta_harvest.py":
        {"role": "Phase 6 -- HELP/META harvest export (the feeder)"},
}

# EXCLUDED add_executable targets, each with the reason it is not push scope.
# A reason is required. "not needed" is not a reason; say what it IS.
EXCLUDED = {
    "dottalkpp": "the engine -- covered by help_build_order_check.py's "
                 "`exe newer than catalogs`, which is the RIGHT check for it "
                 "(dotref/foxref/edref are compiled IN). Two tools answering "
                 "one question is the R5 defect; deferred on purpose.",
    "dottalk_bbsd": "BBS daemon; not in the documentation push.",
    "dottalk_tui": "ArcticTalk TUI front-end; not in the documentation push.",
    "schema_inventory": "website schema inventory; belongs to the web phase, "
                        "which is out of scope for v6.",
    "g0_slot_cost_probe": "AIF-078 measurement probe, run by hand when the cap "
                          "ruling is revisited.",
    "memo_zoo": "memo subsystem demo.",
    "dottalk_wb": "the windowed Workbench GUI.",
    "dottalk_wb_next": "the next-generation Workbench GUI.",
    "fox_palette": "opt-in standalone Turbo Vision palette editor "
                   "(src/CMakeLists.txt:494, DOTTALK_WITH_TV + "
                   "DOTTALK_BUILD_PALETTE_EXE); not in the documentation push.",
    "uidef_wx_demo": "UIDEF-generated wx frontend demo "
                     "(gui/uidef/CMakeLists.txt:182); a separate target from "
                     "APPGUI and not wired to it -- see the APPGUI usage "
                     "contract, which refuses a document argument for exactly "
                     "this reason.",
}
TEST_TARGET_RE = re.compile(r"(^|_)(test|smoke|probe)s?($|_)")

ADD_EXE_RE = re.compile(r"^\s*add_executable\s*\(\s*([A-Za-z0-9_]+)", re.MULTILINE)
# Both shapes seen in this tree: a tuple compare and an ordered compare.
GUARD_RE = re.compile(
    r"sys\.version_info(?:\[:2\])?\s*(==|!=|<|<=|>|>=)\s*\(\s*(\d+)\s*,\s*(\d+)\s*\)")


def newest(root, rels):
    """(mtime, path) of the newest declared source. None if none exist."""
    best = None
    for rel in rels:
        p = root / rel
        if rel.endswith("/"):
            if not p.is_dir():
                continue
            it = [q for q in p.rglob("*") if q.suffix in (".cpp", ".hpp") and q.is_file()]
        else:
            it = [p] if p.is_file() else []
        for q in it:
            m = q.stat().st_mtime
            if best is None or m > best[0]:
                best = (m, q)
    return best


def stamp(t):
    import datetime
    return datetime.datetime.fromtimestamp(t).strftime("%Y-%m-%d %H:%M:%S")


def cmake_targets(root):
    found = set()
    for f in list(root.glob("CMakeLists.txt")) + list(root.glob("src/**/CMakeLists.txt")) \
            + list(root.glob("gui/**/CMakeLists.txt")):
        try:
            found |= set(ADD_EXE_RE.findall(f.read_text(encoding="utf-8", errors="replace")))
        except OSError:
            continue
    return found


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", default=".")
    ap.add_argument("--strict", action="store_true",
                    help="an undeclared add_executable target is an error")
    a = ap.parse_args(argv)
    root = Path(a.root).resolve()
    if not (root / "CMakeLists.txt").is_file():
        print("program-freshness: could not find CMakeLists.txt under %s" % root)
        return 2

    print("=== program freshness -- every program the push runs ===")
    stale, unreadable = [], []

    # ---- compiled -------------------------------------------------------
    for name, spec in sorted(COMPILED.items()):
        exe = next((root / e for e in spec["exe"] if (root / e).is_file()), None)
        src = newest(root, spec["sources"])
        if src is None:
            print("  ERROR %-16s no declared source is on disk -- the manifest is wrong"
                  % name)
            unreadable.append(name)
            continue
        if exe is None:
            print("  skip  %-16s not built (%s)" % (name, spec["exe"][0]))
            print("        %s" % spec["role"])
            continue
        et, st = exe.stat().st_mtime, src[0]
        rel = src[1].relative_to(root).as_posix()
        if et >= st:
            print("  PASS  %-16s exe %s > newest source %s" % (name, stamp(et), stamp(st)))
        else:
            print("  FAIL  %-16s exe %s is OLDER than %s (%s)"
                  % (name, stamp(et), stamp(st), rel))
            print("        %s" % spec["role"])
            print("        A stale program reports the tree as it was BEFORE the "
                  "change under test.")
            stale.append(name)

    # ---- python ---------------------------------------------------------
    print("  --- python programs: the version guard each one declares ---")
    for rel, spec in sorted(PYTHON_PROGRAMS.items()):
        p = root / rel
        if not p.is_file():
            print("  ERROR %-52s not on disk" % rel)
            unreadable.append(rel)
            continue
        m = GUARD_RE.search(p.read_text(encoding="utf-8", errors="replace"))
        if not m:
            print("  none  %-52s no version guard" % rel)
            continue
        op, maj, mnr = m.group(1), m.group(2), m.group(3)
        shape = "%s (%s, %s)" % (op, maj, mnr)
        if op in ("==", "!="):
            print("  NOTE  %-52s guard is an EQUALITY: %s" % (rel, shape))
            print("        It refuses every version above the pin as readily as "
                  "every version below it.")
        else:
            print("  ok    %-52s guard is a FLOOR: %s" % (rel, shape))

    # ---- manifest coverage ---------------------------------------------
    declared = set(COMPILED) | set(EXCLUDED)
    targets = cmake_targets(root)
    undeclared = sorted(t for t in targets - declared if not TEST_TARGET_RE.search(t))
    print("  --- manifest coverage: %d add_executable target(s) in the tree ---"
          % len(targets))
    if undeclared:
        print("  %s %d target(s) neither declared nor excluded:"
              % ("ERROR" if a.strict else "note ", len(undeclared)))
        for t in undeclared:
            print("        %s" % t)
        print("        Declare it in COMPILED if the push runs it, or in EXCLUDED "
              "with the reason it does not.")
        if a.strict:
            unreadable.extend(undeclared)
    else:
        print("  ok    every non-test target is declared or excluded by name")

    print()
    # AIF-128: exit 1 says "your thing is wrong", exit 2 says "I could not
    # measure". When BOTH are true the STALE finding is the one that was
    # actually established, and downgrading it to "could not measure" is the
    # guard-tests-the-union defect -- a verdict arriving from a different
    # question than the message names. Found by fault injection 2026-08-26,
    # in the first run of this tool's own injection suite: a synthetic root
    # with a genuinely stale exe returned 2, and the FAIL line above it was
    # true and unheeded. Report both; let the harder verdict win.
    if unreadable:
        print("PROGRAM FRESHNESS: could not measure -- %s" % ", ".join(unreadable))
    if stale:
        print("PROGRAM FRESHNESS FAIL: rebuild %s before running the push."
              % ", ".join(stale))
        return 1
    if unreadable:
        return 2
    print("PROGRAM FRESHNESS PASS -- every declared program is newer than its sources.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
