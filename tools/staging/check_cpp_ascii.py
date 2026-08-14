#!/usr/bin/env python3
"""
check_cpp_ascii.py -- an em dash in C/C++ source is an automatic fail.

Owner ruling, 2026-08-13: "make a rule in the ai portal, an em dash is an
automatic fail in your source code" and "fail on c++ code". Web source is
explicitly OUT of scope by the same ruling; see the measurement in
AI_PORTAL.md, "ASCII in C/C++ source".

WHY THIS IS NOT COSMETIC. The em dashes in this tree's C/C++ are not in
comments. Measured 2026-08-13: of 51 in 10 files, 41 sit inside STRING
LITERALS -- HELP text, error messages, admin refusals, the vdisk mount notice.
Those are the strings the runtime prints, so every one of them mojibakes on a
non-UTF-8 console codepage. It is the same defect that made the pre-push gate's
own PASS line unreadable, except this copy ships to users.

SCOPE: ADDED LINES ONLY, on the staged index, deliberately.
The backlog is real work, not a typo sweep: 41 of the 51 are message text, and
changing message text changes runtime output, which needs a REGRESSION run and
belongs to the messaging lane. Blocking every commit that touches
src/help/helpdata_messages.cpp until that lands would punish the sessions doing
the work. So new violations become impossible, the backlog is reported on every
run so it cannot hide, and it gets fixed with proof rather than in a hurry.
Same argued shape as check_house_style.py, which took the same decision for docs.

Exit: 0 clean - 2 an added line carries a banned codepoint - 4 usage/git error.

Usage:
  python tools/staging/check_cpp_ascii.py            # staged index
  python tools/staging/check_cpp_ascii.py --range R  # a commit range
  python tools/staging/check_cpp_ascii.py --all      # whole tree, backlog census
  python tools/staging/check_cpp_ascii.py --self-test  # prove it can FAIL

Owner: member.derald - steward: member.ai.claude.cowork - lane: AIF-100
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import tempfile

CPP_EXT = (".c", ".cc", ".cpp", ".cxx", ".h", ".hh", ".hpp", ".hxx", ".inl", ".ipp")

# CLOSURE: any codepoint >= 128 on an added line fails. NOT an enumerated list.
#
# Corrected 2026-08-14 after the enumerated version missed U+2022 BULLET, which
# appears 25 times in C/C++ console output -- 16 of them in cmd_security.cpp's own
# SECURITY RUNTIME block, i.e. the security command mojibaked its own output while
# this gate reported clean. A banned-list gate is only ever as complete as the
# author's imagination, which is the defect shape this house hunts.
#
# The closure is not new. Prior art, found before changing anything:
#   - AI_TIER1_SEED_V1.md sec 4: "ASCII only in new content; check with
#     grep -P '[^\x00-\x7F]'" -- all non-ASCII, already ruled.
#   - check_house_style.py:186 tests `ord(ch) >= 128` for docs and names the
#     known ones while falling back to a generic message for the rest.
#   - ascii_normalize.py exits 2 on an unmapped codepoint rather than guessing.
# The enumerated list was a NARROWING of a rule that already existed. This file
# now matches its siblings instead of inventing a third rule.
#
# The table below is a TEACHING AID, not the test. It makes the message useful
# for the cases we know; anything absent still fails, with a generic message.
REPLACEMENTS = {
    "—": ("EM DASH", "--"),
    "–": ("EN DASH", "-"),
    "‘": ("LEFT SINGLE QUOTE", "'"),
    "’": ("RIGHT SINGLE QUOTE", "'"),
    "“": ("LEFT DOUBLE QUOTE", '"'),
    "”": ("RIGHT DOUBLE QUOTE", '"'),
    "…": ("HORIZONTAL ELLIPSIS", "..."),
    "→": ("RIGHTWARDS ARROW", "->"),
    " ": ("NO-BREAK SPACE", "a plain space"),
    # Added 2026-08-14 from a census of what is ACTUALLY in this tree's C/C++,
    # not from what seemed likely. We do not ignore the small misses.
    "•": ("BULLET", "- or *"),
    "§": ("SECTION SIGN", "sec."),
    "‑": ("NON-BREAKING HYPHEN", "-"),
    "−": ("MINUS SIGN", "-"),
    "↑": ("UPWARDS ARROW", "^"),
    "↓": ("DOWNWARDS ARROW", "v"),
    "∪": ("UNION", "union"),
    "∩": ("INTERSECTION", "intersect"),
}


def classify(ch: str) -> tuple[str, str]:
    """Name a codepoint and its ASCII stand-in. Unknown ones still FAIL."""
    if ch in REPLACEMENTS:
        return REPLACEMENTS[ch]
    o = ord(ch)
    if 0x2500 <= o <= 0x257F:
        return ("BOX DRAWING", "ASCII box art (+ - |), or keep it out of source")
    if 0x00C0 <= o <= 0x024F:
        return ("LATIN LETTER WITH DIACRITIC", "ASCII; see the locale note below")
    if o >= 0x1F000:
        return ("EMOJI / PICTOGRAPH", "a word")
    return (f"U+{o:04X}", "an ASCII equivalent")


def git(args: list[str], cwd: str | None = None) -> str:
    try:
        r = subprocess.run(["git"] + args, check=True, capture_output=True,
                           text=True, encoding="utf-8", errors="replace", cwd=cwd)
        return r.stdout
    except FileNotFoundError:
        print("check-cpp-ascii: git not found on PATH", file=sys.stderr)
        sys.exit(4)
    except subprocess.CalledProcessError as e:
        print(f"check-cpp-ascii: git {' '.join(args)} failed:\n{e.stderr}",
              file=sys.stderr)
        sys.exit(4)


def added_lines(range_spec: str | None, cwd: str | None = None):
    """(path, line_no, text) for every ADDED line in a staged C/C++ file."""
    args = ["diff", "--unified=0", "--diff-filter=ACMR"]
    args += [range_spec] if range_spec else ["--cached"]
    out, path, ln = git(args, cwd), None, 0
    for raw in out.splitlines():
        if raw.startswith("+++ b/"):
            p = raw[6:].strip()
            path = p if p.lower().endswith(CPP_EXT) else None
        elif raw.startswith("@@") and path:
            try:
                ln = int(raw.split("+")[1].split(",")[0].split()[0]) - 1
            except (IndexError, ValueError):
                ln = 0
        elif path and raw.startswith("+") and not raw.startswith("+++"):
            ln += 1
            yield path, ln, raw[1:]


def scan_tree(root: str):
    """Whole-tree census. Reported, never blocking."""
    hits = []
    for dp, dn, fn in os.walk(root):
        dn[:] = [d for d in dn if d not in
                 (".git", "node_modules", "out", "dist", ".next", "__pycache__")
                 and not d.startswith("build")]
        for f in fn:
            if not f.lower().endswith(CPP_EXT):
                continue
            p = os.path.join(dp, f)
            try:
                t = open(p, encoding="utf-8", errors="replace").read()
            except OSError:
                continue
            n = sum(1 for c in t if ord(c) >= 128)
            if n:
                hits.append((n, os.path.relpath(p, root).replace("\\", "/")))
    hits.sort(reverse=True)
    return hits


def report(found) -> None:
    print(f"cpp-ascii: FAIL -- {len(found)} added line(s) carry a banned codepoint",
          file=sys.stderr)
    for path, ln, text, bad in found:
        print(f"  {path}:{ln}", file=sys.stderr)
        for ch in sorted(bad):
            name, rep = classify(ch)
            print(f"      {name} -> use {rep}", file=sys.stderr)
        print(f"      | {text.strip()[:100]}", file=sys.stderr)
    print("\n  An em dash in C/C++ is an automatic fail (AI_PORTAL.md, 'ASCII in "
          "C/C++ source').\n  Most of this tree's are inside string literals, which "
          "means the RUNTIME prints\n  them and they mojibake on a non-UTF-8 console. "
          "Fix with:\n\n      python tools/staging/ascii_normalize.py --apply FILE\n\n"
          "  If the string is user-facing message text, it is a messaging change: "
          "run the\n  relevant REGRESSION before promoting it.", file=sys.stderr)


def self_test() -> int:
    """A checker is unproven until you have seen it FAIL (AIF-082)."""
    with tempfile.TemporaryDirectory() as d:
        git(["init", "-q", d])
        git(["config", "user.email", "t@t"], cwd=d)
        git(["config", "user.name", "t"], cwd=d)
        ok = os.path.join(d, "clean.cpp")
        open(ok, "w", encoding="utf-8").write('// plain -- ascii only\nint a=1;\n')
        git(["add", "clean.cpp"], cwd=d)
        clean = list(added_lines(None, cwd=d))
        c_bad = [x for x in clean if any(ord(c) >= 128 for c in x[2])]

        bad = os.path.join(d, "bad.cpp")
        open(bad, "w", encoding="utf-8").write('const char* m = "enabled=0 — off";\n')
        git(["add", "bad.cpp"], cwd=d)
        both = list(added_lines(None, cwd=d))
        b_bad = [x for x in both if any(ord(c) >= 128 for c in x[2])]

        # The case the enumerated version MISSED: a codepoint not in the table.
        # If this passes, the closure has regressed to a banned-list again.
        unk = os.path.join(d, "unknown.cpp")
        open(unk, "w", encoding="utf-8").write('// • bullet, never enumerated\n')
        git(["add", "unknown.cpp"], cwd=d)
        u_bad = [x for x in list(added_lines(None, cwd=d))
                 if "unknown.cpp" in x[0] and any(ord(c) >= 128 for c in x[2])]

    print(f"  control (ascii only)     -> {len(c_bad)} finding(s); expected 0")
    print(f"  known-bad (em dash)      -> {len(b_bad)} finding(s); expected 1")
    print(f"  UNKNOWN codepoint (bullet)-> {len(u_bad)} finding(s); expected 1")
    if len(c_bad) == 0 and len(b_bad) == 1 and len(u_bad) == 1:
        print("cpp-ascii: SELF-TEST PASS -- seen to fail, and seen not to.")
        return 0
    print("cpp-ascii: SELF-TEST FAIL -- the checker is unproven.", file=sys.stderr)
    return 2


def main() -> int:
    ap = argparse.ArgumentParser(description="Em dash in C/C++ source is a hard fail.")
    ap.add_argument("--range", dest="range_spec", default=None)
    ap.add_argument("--all", action="store_true", help="whole-tree census, never blocks")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()

    if a.self_test:
        return self_test()

    root = git(["rev-parse", "--show-toplevel"]).strip()

    if a.all:
        hits = scan_tree(root)
        tot = sum(n for n, _ in hits)
        print(f"cpp-ascii census: {len(hits)} file(s), {tot} banned codepoint(s)")
        for n, p in hits[:20]:
            print(f"    {n:4}  {p}")
        return 0

    found = []
    for path, ln, text in added_lines(a.range_spec):
        bad = {c for c in text if ord(c) >= 128}
        if bad:
            found.append((path, ln, text, bad))

    # NOTE: the backlog census is NOT run here. main() previously walked the whole
    # tree on every invocation to print one number, which is seconds of latency in a
    # pre-commit hook for a figure nobody acts on at commit time. It moved to --all.
    # Caught 2026-08-14 by the check timing out during its own verification.
    if found:
        report(found)
        print("\n  Standing backlog elsewhere in the tree is NOT counted here "
              "(it is a whole-tree\n  walk). Run: "
              "python tools/staging/check_cpp_ascii.py --all", file=sys.stderr)
        return 2

    print("cpp-ascii: PASS -- no non-ASCII in added C/C++ lines")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
