#!/usr/bin/env python3
"""
WHO WRITES A FIELD, AND DOES IT GO THROUGH THE FUNNEL (AIF-156).

THE CLAIM THIS EXISTS TO MAKE, WHICH NO REGRESSION MARKER CAN.
PKPOLICY proves three write paths REFUSE a write to a declared PRIMARY key.
It cannot prove those are the ONLY paths, because a runtime marker cannot
enumerate a call site -- it can only exercise the ones somebody thought to
exercise. Arms prove routes; a gate proves there are no other routes. That
second claim is static, so it needs a static check.

WHAT IT LOOKS FOR: direct calls to the engine's field-write primitives from
outside the engine --

    DbArea::replaceFieldStored   the value write
    DbArea::replaceFieldNull     the null write
    DbArea::set                  the buffer write (record-level commit follows)

anywhere under src/ except src/xbase (which OWNS them) and src/tests.

EXEMPT BY ROUTE, NOT BY FLAG, and the exemption list is three files long:

    src/cli/xbase_cli_write.cpp    IS the funnel
    src/cli/append_support.cpp     the key GENERATOR -- it must write a
                                   primary key, and it is exempted by being
                                   below the funnel rather than by passing a
                                   bypass parameter, because a parameter can
                                   be passed by anyone and a route cannot
    src/cli/cmd_validate_unique.cpp  VALIDATE UNIQUE ... REPAIR, the
                                   inherited-data renumber tool the charter's
                                   step 3 deliberately preserves

ADVISORY, WITH A BASELINE, ON PURPOSE. The backlog is real and large; a gate
that blocks every commit on day one gets disabled, and a disabled gate measures
nothing. The baseline turns a claim into a list that can only shrink.

    NEW    a call site not in the baseline. Somebody added a direct write.
    FIXED  in the baseline and gone. Drop the line; a baseline that only ever
           grows stops being a measurement.

COMMENTS AND STRING LITERALS ARE STRIPPED BEFORE MATCHING, and that is not
tidiness -- this tree's registry summaries discuss replaceFieldStored at length
in prose, and cmd_regression.cpp alone would contribute a dozen phantom hits.
A gate that counts its own documentation is worse than no gate.
"""

import os
import re
import sys

ROOT = os.getcwd()
SRC = os.path.join(ROOT, "src")
BASELINE = os.path.join("tools", "staging", "field_write_callers_baseline.txt")

SKIP_DIRS = {
    os.path.join("src", "xbase"),   # owns the primitives
    os.path.join("src", "tests"),   # asserts on them directly, by design
}

EXEMPT_FILES = {
    os.path.join("src", "cli", "xbase_cli_write.cpp"),      # is the funnel
    os.path.join("src", "cli", "append_support.cpp"),       # the generator
    os.path.join("src", "cli", "cmd_validate_unique.cpp"),  # REPAIR
}

# `set(` IS DISCRIMINATED BY THE SHAPE OF ITS FIRST ARGUMENT, and this took
# three cuts. DbArea::set takes a 1-BASED FIELD INDEX; the name-keyed
# row-writer wrappers in identity_dbf_store and bbs_store take a STRING
# ("ID", "UKEY"). So "the first argument is not a quote" is the whole test.
#
# The first cut demanded a bare identifier or a number and MISSED
# `a.set(i + 1, v)` -- a real DbArea write, in two files, because the argument
# is an EXPRESSION. The second widened to allow member access and still missed
# it. Requiring a SHAPE the argument might not take is how a gate
# under-reports while looking clean, which is the one failure a gate must not
# have.
PATTERNS = [
    ("replaceFieldStored", re.compile(r"(?:\.|->)\s*replaceFieldStored\s*\(")),
    ("replaceFieldNull",   re.compile(r"(?:\.|->)\s*replaceFieldNull\s*\(")),
    ("set",                re.compile(r"(?:\.|->)\s*set\s*\(\s*(?![\"'])")),
]


def strip_comments_and_strings(text, keep_strings=False):
    """Blank out // and /* */ comments and "..." literals, preserving newlines
    so reported line numbers stay true."""
    out = []
    i, n = 0, len(text)
    while i < n:
        c = text[i]
        if c == "/" and i + 1 < n and text[i + 1] == "/":
            while i < n and text[i] != "\n":
                out.append(" ")
                i += 1
        elif c == "/" and i + 1 < n and text[i + 1] == "*":
            out.append("  ")
            i += 2
            while i < n and not (text[i] == "*" and i + 1 < n and text[i + 1] == "/"):
                out.append("\n" if text[i] == "\n" else " ")
                i += 1
            if i < n:
                out.append("  ")
                i += 2
        elif c == "'":
            # CHAR LITERALS MUST BE STRIPPED BEFORE DOUBLE QUOTES, and this
            # cost a real miss: cmd_calcwrite.cpp:156 holds '"', so a stripper
            # that does not know char literals opens a string there and blanks
            # everything to the next quote -- including the direct
            # replaceFieldStored call at line 917. THE GATE UNDER-REPORTED AND
            # LOOKED CLEAN, which is the failure mode a gate must not have.
            out.append(" ")
            i += 1
            while i < n and text[i] != "'":
                if text[i] == "\\" and i + 1 < n:
                    out.append("  ")
                    i += 2
                    continue
                out.append("\n" if text[i] == "\n" else " ")
                i += 1
            if i < n:
                out.append(" ")
                i += 1
        elif c == '"':
            if keep_strings:
                out.append(c)
                i += 1
                while i < n and text[i] != '"':
                    if text[i] == "\\" and i + 1 < n:
                        out.append(text[i]); out.append(text[i + 1]); i += 2
                        continue
                    out.append(text[i]); i += 1
                if i < n:
                    out.append(text[i]); i += 1
                continue
            out.append(" ")
            i += 1
            while i < n and text[i] != '"':
                if text[i] == "\\" and i + 1 < n:
                    out.append("  ")
                    i += 2
                    continue
                out.append("\n" if text[i] == "\n" else " ")
                i += 1
            if i < n:
                out.append(" ")
                i += 1
        else:
            out.append(c)
            i += 1
    return "".join(out)


def scan():
    hits = []
    for dirpath, _dirnames, filenames in os.walk(SRC):
        rel_dir = os.path.relpath(dirpath, ROOT)
        if any(rel_dir == s or rel_dir.startswith(s + os.sep) for s in SKIP_DIRS):
            continue
        for fn in filenames:
            if not fn.endswith((".cpp", ".cc", ".cxx")):
                continue
            rel = os.path.relpath(os.path.join(dirpath, fn), ROOT)
            if rel.replace("\\", "/") in {p.replace("\\", "/") for p in EXEMPT_FILES}:
                continue
            try:
                with open(os.path.join(dirpath, fn), "r", encoding="utf-8",
                          errors="replace") as f:
                    text = f.read()
            except OSError:
                continue
            # TWO PASSES, BECAUSE THE PATTERNS WANT OPPOSITE THINGS.
            #
            # The NAME patterns need string literals GONE: this tree's registry
            # summaries are string literals that discuss replaceFieldStored at
            # length, and cmd_regression.cpp alone would contribute a dozen
            # phantom hits.
            #
            # The `set(` pattern needs them KEPT, because the whole test is
            # whether the first argument is a quote -- and a stripper that
            # blanks `w.set("ID"` to `w.set(    ` destroys the only evidence
            # that this is a name-keyed wrapper rather than a field write.
            # Stripping first made the discriminator match everything.
            no_strings = strip_comments_and_strings(text)
            with_strings = strip_comments_and_strings(text, keep_strings=True)
            for label, pat in PATTERNS:
                code = with_strings if label == "set" else no_strings
                for lineno, line in enumerate(code.split("\n"), 1):
                    if pat.search(line):
                        hits.append("%s:%d:%s" % (rel.replace("\\", "/"), lineno, label))
    return sorted(set(hits))


def main():
    hits = scan()

    by_file = {}
    for h in hits:
        by_file.setdefault(h.split(":")[0], 0)
        by_file[h.split(":")[0]] += 1

    print("field-write-callers: %d direct call site(s) in %d file(s) outside the engine"
          % (len(hits), len(by_file)))

    have_baseline = os.path.exists(BASELINE)
    if not have_baseline:
        print("  baseline %s is absent -- reporting the whole set as the backlog." % BASELINE)
        for f in sorted(by_file, key=lambda k: (-by_file[k], k)):
            print("    %4d  %s" % (by_file[f], f))
        print()
        print("  Write these lines to the baseline to freeze the backlog:")
        for h in hits:
            print(h)
        return 0

    with open(BASELINE, "r", encoding="utf-8") as f:
        base = sorted(set(l.strip() for l in f
                          if l.strip() and not l.startswith("#")))

    new = [h for h in hits if h not in base]
    fixed = [b for b in base if b not in hits]

    if new:
        print("  NEW -- a direct field write that does not go through the funnel:")
        for h in new:
            print("    " + h)
        print("  Route it through xbase::cli::replaceFieldStored / replaceFieldNull,")
        print("  or -- if it is a deliberate below-the-funnel writer like the key")
        print("  generator -- add it to EXEMPT_FILES with the reason, not to the baseline.")
    if fixed:
        print("  FIXED -- in the baseline and now routed, drop these lines:")
        for b in fixed:
            print("    " + b)
    if not new and not fixed:
        print("  PASS -- direct-write set matches the baseline exactly.")

    # ADVISORY: never non-zero. The backlog predates the funnel and blocking on
    # it would only teach people to switch the gate off.
    return 0


if __name__ == "__main__":
    sys.exit(main())
