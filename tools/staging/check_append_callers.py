#!/usr/bin/env python3
# @dottalk.file v1
# subsystem: tools
# layer: gate
# owns: tools/staging/append_callers_baseline.txt
# project: project.x64base.runtime
# lane: OI-045
# owner: member.derald
# status: supported
"""Count every direct caller of DbArea::appendBlank() outside the engine.

WHY THIS EXISTS (OI-045, 2026-09-19).

`++_rec_count64` occurs EXACTLY ONCE in this tree -- src/xbase/dbf_file.cpp:421,
inside DbArea::appendBlank(). Nothing else grows a table; the public setters
setRecordCount / setRecordCount64 in include/xbase.hpp have no production caller
at all. So the "one common function for increasing the record count" that the
owner asked for on 2026-09-19 ALREADY EXISTS.

What does not exist is a GATEKEEPER in front of it. appendBlank() is a raw
byte-level operation -- it seeks to the end, writes a blank row, patches the
count at offset 4, and takes NO LOCK OF ANY KIND -- and command code reaches it
directly from 17 files. Only src/cli/append_support.cpp takes the table lock
first. src/cli/cmd_sql_insert.cpp and src/cli/table_state.cpp do not, which is
how a buffered INSERT's reserved recno goes stale and how COMMIT then overwrites
a live record (OI-043, measured 2026-09-19).

THIS GATE COMES BEFORE THE FUNNEL, ON PURPOSE. It is independent of how OI-043
is ruled -- it measures whichever design wins -- it makes the surface visible
today, and it ratchets against a 38th site arriving while the ruling is pending.

THE MODEL IS tools/staging/check_field_write_callers.py, which solved this exact
problem for field writes under AIF-156: "CONSOLIDATE THE ROUTE rather than mint
arms -- one funnel, plus a static gate proving nobody goes around it." The site
key, the baseline handling and the advisory exit are lifted from it deliberately.

AND ONE DELIBERATE DEPARTURE FROM THE MODEL, WHICH IS THE INTERESTING PART.

The field-write gate EXCLUDES a `x.set(` call when `x` is not a DbArea declared
in that same .cpp. That is right for `set(`, which collides with a dozen
unrelated wrappers. It would be WRONG here, and provably so:
src/dewey/hierarchy_service.cpp calls `_area.appendBlank()` three times, and
`_area` is a MEMBER declared in the .hpp -- a .cpp-only scan cannot see its type.
Excluding on an unconfirmed receiver would silently drop three real growers.

`appendBlank` needs no such discriminator: it takes no arguments and the name
collides with nothing. So EVERY call is counted, and a receiver whose type this
file cannot confirm is REPORTED, never dropped. That is the model's own stated
principle -- "Unknown is counted, never dropped" -- applied in the direction that
cannot lose a site.

Usage:
    python tools/staging/check_append_callers.py
    python tools/staging/check_append_callers.py --emit-baseline
    python tools/staging/check_append_callers.py --selftest

Advisory. Never returns non-zero for backlog; a gate that blocks on a backlog
predating it only teaches people to switch the gate off.
"""

import os
import re
import sys

ROOT = os.getcwd()
SRC = os.path.join(ROOT, "src")
# HEADERS ARE IN SCOPE TOO, AND THEY WERE NOT UNTIL 2026-09-19.
# The gate scanned src/ only. The moment the append funnel was written as
# include/cli/append_fence.hpp, the ONE call that matters most became
# invisible to the instrument measuring it -- and so would any future
# header-inlined grower. Scanning both and exempting the funnel BY NAME is
# the model's own posture (check_field_write_callers.py exempts
# src/cli/xbase_cli_write.cpp "is the funnel"), applied where it belongs.
INC = os.path.join(ROOT, "include")
SCAN_ROOTS = (SRC, INC)
BASELINE = os.path.join("tools", "staging", "append_callers_baseline.txt")

SKIP_DIRS = {
    os.path.join("src", "tests"),   # asserts on the primitive directly, by design
    os.path.join("src", "tools"),   # probes and cost harnesses, not command code
}

EXEMPT_FILES = {
    # DEFINES appendBlank(). Counting the definition's own file would make the
    # gate report the thing it is measuring.
    os.path.join("src", "xbase", "dbf_file.cpp"),

    # THE GENERATOR. append_support.cpp is the APPEND verb itself: it takes the
    # table fence explicitly and generates a PRIMARY KEY inside it, which is why
    # the lock is held across more than the append. Routing it through the
    # funnel would nest a fence inside its own fence for no gain. This is the
    # model's "the generator" exemption (check_field_write_callers.py).
    os.path.join("src", "cli", "append_support.cpp"),

    # FRESH PRIVATE OUTPUTS, exempted BY FILE WITH THE REASON rather than by
    # dropping lines into the baseline -- a baseline of things that are FINE is
    # how a measurement stops meaning anything.
    #
    # Each of these appends into a destination IT JUST CREATED and opened, so
    # there is no concurrent holder to fence against and a lock file per output
    # buys nothing. Verified by reading where the receiver comes from, not
    # assumed from the command's name:
    #   cmd_copy.cpp     dst.open(dstp)        the COPY TO destination
    #   cmd_sort.cpp     out.open(out_path)    the SORT output
    #   cmd_ddl.cpp      area.open(out_dbf)    pre-sizing a table DDL just made
    #   fields_mgr.cpp   out.open(tempPath)    a TEMP file during schema rebuild
    #
    # THE COST IS REAL AND ACCEPTED: a future append added to one of these files
    # against a SHARED table will not be seen here. The trade is the same one
    # the model states, and the reason it holds is that all four write to a path
    # they created in the same function.
    os.path.join("src", "cli", "cmd_copy.cpp"),
    os.path.join("src", "cli", "cmd_sort.cpp"),
    os.path.join("src", "cli", "cmd_ddl.cpp"),
    os.path.join("src", "xbase", "fields_mgr.cpp"),

    # IS THE FUNNEL (OI-043, 2026-09-19). cli::fence::append_fenced() is the one
    # gatekeeper -- it takes the table fence, appends, and returns the record
    # number the FILE assigned. Counting it would make the gate report the route
    # it exists to prove people use.
    os.path.join("include", "cli", "append_fence.hpp"),
}

# NOT EXEMPT, AND THE DISTINCTION MATTERS: src/xbase/fields_mgr.cpp is INSIDE
# the engine directory but is a CALLER, not the owner -- it grows a table during
# a schema rebuild like any other caller. The field-write gate skips all of
# src/xbase because that directory owns the field primitives; here only the one
# file that owns THIS primitive is exempt. A directory-wide skip would have lost
# a real site to a rule copied without reading it.

LABEL = "appendBlank"
PATTERN = re.compile(r"(?:\.|->)\s*appendBlank\s*\(")
RECEIVER = re.compile(r"([A-Za-z_]\w*)\s*(?:\.|->)\s*appendBlank\s*\(")

# A DbArea-typed name as declared or received in this file. Used ONLY to
# annotate, never to exclude -- see the module docstring.
DBAREA_DECL = re.compile(
    r"(?:^|[^\w:])(?:(?:::)?xbase::)?DbArea\s*(?:const\s+)?[&*\s]*([A-Za-z_]\w*)"
)


def strip_comments_and_strings(text):
    """Blank out // and /* */ comments and "..." literals, preserving newlines
    so reported line numbers stay true.

    STRINGS MUST GO. src/cli/cmd_regression.cpp carries registry summaries that
    discuss appendBlank at length inside string literals; without this the gate
    would invent call sites out of prose. That is the exact over-count the
    field-write gate recorded when its own first cut grepped raw text.
    """
    out = []
    i = 0
    n = len(text)
    while i < n:
        c = text[i]
        nxt = text[i + 1] if i + 1 < n else ""
        if c == "/" and nxt == "/":
            while i < n and text[i] != "\n":
                out.append(" ")
                i += 1
        elif c == "/" and nxt == "*":
            out.append("  ")
            i += 2
            while i < n and not (text[i] == "*" and i + 1 < n and text[i + 1] == "/"):
                out.append("\n" if text[i] == "\n" else " ")
                i += 1
            if i < n:
                out.append("  ")
                i += 2
        elif c in "\"'":
            quote = c
            out.append(" ")
            i += 1
            while i < n and text[i] != quote:
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


DEF_RE = re.compile(r"^[A-Za-z_][\w:<>,&*\s]*?([A-Za-z_]\w*)\s*\([^;]*$")
CTRL = {"if", "for", "while", "switch", "catch", "return", "else", "do"}


def enclosing_function(lines, index):
    """Nearest preceding definition-shaped line, by name. Heuristic on purpose.

    It does not need to be a parser. It needs to be STABLE under insertions
    above the site, and to differ when the site genuinely moves elsewhere. A
    wrong-but-consistent answer still keys correctly; only a FLAPPING answer
    would reintroduce drift, and a definition line does not move relative to
    the body it opens. This is why the key is not file:line -- the field-write
    gate produced ten false-positive drift reports on byte-identical
    relocations before its key was migrated.
    """
    for i in range(index, -1, -1):
        line = lines[i]
        if not line or line[0].isspace():
            continue
        m = DEF_RE.match(line)
        if m and m.group(1) not in CTRL:
            return m.group(1)
    return "<file-scope>"


def call_text(line):
    return re.sub(r"\s+", " ", line.strip())


def site_key(rel_slash, func, text, label, nth=1):
    """file :: function :: call text :: label #N

    THE ORDINAL IS NOT DECORATION, AND IT IS THIS GATE'S FIRST FINDING.

    The model gate keys on (file, function, call text) alone. That is enough
    for FIELD writes, whose call text carries a field name and a value and so
    differs site to site. It is NOT enough here: appendBlank takes no
    arguments, so its call text is frequently byte-identical. Measured
    2026-09-19 before this fix -- src/identity/identity_dbf_store.cpp calls
    `a.appendBlank(); RowW w{a, err};` TEN times inside save_identity_tables,
    and the three-part key collapsed all ten into ONE site. The gate reported
    26 sites where 37 exist, and reported it cleanly. A gate that
    under-reports while looking clean is the single failure a gate must not
    have, and copying the model's key without testing it against this tree
    produced exactly that.

    N is the 1-based occurrence of this exact (function, call text) pair within
    the file, in line order. What that buys and what it costs:
      KEEPS  insertions above the block do not renumber anything, so a
             relocation is still silent -- the property the whole key exists for
      GAINS  an 11th identical call in the same function appears as NEW
      COSTS  removing the 3rd of ten identical calls reports the 10th as FIXED,
             not the 3rd. The COUNT and the FUNCTION are right and the identity
             of which indistinguishable line went is not. That is honest for
             sites nothing in the source distinguishes, and it is stated here
             rather than discovered later.
    """
    return "%s :: %s :: %s :: %s #%d" % (rel_slash, func, text, label, nth)


ORDINAL_TAIL = re.compile(r" #\d+$")


def is_legacy_baseline(entries):
    """True for a baseline written before the current key shape.

    TWO legacy shapes now, not one: the file:line shape the model migrated off,
    and the three-part shape this gate itself emitted for one afternoon before
    the ordinal was added. Both must refuse comparison rather than diff, because
    diffing across shapes reports every site FIXED and every site NEW at once.
    """
    if not entries:
        return False
    if not any(" :: " in e for e in entries):
        return True                       # file:line
    return not all(ORDINAL_TAIL.search(e) for e in entries)   # no ordinal


def scan():
    hits = []
    unconfirmed = []
    where = {}
    exempt_slash = {p.replace("\\", "/") for p in EXEMPT_FILES}
    for root in SCAN_ROOTS:
      for dirpath, _dirnames, filenames in os.walk(root):
          rel_dir = os.path.relpath(dirpath, ROOT)
          if any(rel_dir == s or rel_dir.startswith(s + os.sep) for s in SKIP_DIRS):
              continue
          for fn in sorted(filenames):
              if not fn.endswith((".cpp", ".cc", ".cxx", ".hpp", ".h")):
                  continue
              rel = os.path.relpath(os.path.join(dirpath, fn), ROOT)
              rel_slash = rel.replace("\\", "/")
              if rel_slash in exempt_slash:
                  continue
              try:
                  with open(os.path.join(dirpath, fn), "r", encoding="utf-8",
                            errors="replace") as f:
                      text = f.read()
              except OSError:
                  continue
              code = strip_comments_and_strings(text)
              code_lines = code.split("\n")
              areas = set(DBAREA_DECL.findall(code))
              seen = {}   # (function, call text) -> how many already counted here
              for lineno, line in enumerate(code_lines, 1):
                  if not PATTERN.search(line):
                      continue
                  func = enclosing_function(code_lines, lineno - 1)
                  ctext = call_text(line)
                  seen[(func, ctext)] = seen.get((func, ctext), 0) + 1
                  key = site_key(rel_slash, func, ctext, LABEL, seen[(func, ctext)])
                  hits.append(key)
                  where[key] = "%s:%d" % (rel_slash, lineno)
                  m = RECEIVER.search(line)
                  recv = m.group(1) if m else None
                  if recv is None or recv not in areas:
                      # COUNTED ANYWAY. Reported so a reader can confirm by hand.
                      unconfirmed.append(
                          "%s:%d  (%s not declared DbArea in this file)"
                          % (rel_slash, lineno, recv if recv else "<receiver not a plain name>"))
    return sorted(set(hits)), sorted(set(unconfirmed)), where


def selftest():
    """Falsify the KEY and the STRIPPER -- the two things that can go quiet."""
    rc = 0

    before = [
        "#include <a.hpp>",
        "static bool grow(DbArea& a) {",
        "    if (!a.appendBlank()) { return false; }",
        "    return true;",
        "}",
    ]
    after = [
        "#include <a.hpp>",
        "#include <b.hpp>",
        "struct WsLock { int held; };",
        "",
        "static bool grow(DbArea& a) {",
        "    if (!a.appendBlank()) { return false; }",
        "    return true;",
        "}",
    ]
    k1 = site_key("f.cpp", enclosing_function(before, 2), call_text(before[2]), LABEL)
    k2 = site_key("f.cpp", enclosing_function(after, 5), call_text(after[5]), LABEL)
    if k1 != k2:
        print("selftest FAIL: a relocation changed the key")
        print("  before: " + k1)
        print("  after : " + k2)
        return 2
    print("selftest: relocation is silent          OK")

    added = list(after)
    added.insert(6, "    if (!a.appendBlank()) { return true; }")
    k3 = site_key("f.cpp", enclosing_function(added, 6), call_text(added[6]), LABEL)
    if k3 == k1:
        print("selftest FAIL: a genuinely new grower did not change the key")
        return 2
    print("selftest: a new grower still speaks     OK")

    moved = ["static bool other(DbArea& a) {",
             "    if (!a.appendBlank()) { return false; }",
             "}"]
    k4 = site_key("f.cpp", enclosing_function(moved, 1), call_text(moved[1]), LABEL)
    if k4 == k1:
        print("selftest FAIL: the same text in another function kept the key")
        return 2
    print("selftest: another function differs      OK")

    # THE STRIPPER. A gate that counts prose over-reports and then gets ignored.
    prose = '\n'.join([
        'static void reg() {',
        '    add("a.appendBlank() is the only grower");   // and a comment: b.appendBlank()',
        '}',
    ])
    stripped = strip_comments_and_strings(prose)
    if PATTERN.search(stripped):
        print("selftest FAIL: a mention in a string or comment was counted as a call")
        return 2
    print("selftest: prose is not a call site      OK")

    if len(stripped.split("\n")) != len(prose.split("\n")):
        print("selftest FAIL: the stripper changed the line count -- line numbers would lie")
        return 2
    print("selftest: line numbers survive stripping OK")

    # THE ORDINAL. Two identical calls in one function are TWO growers.
    twin = [
        "static bool grow_two(DbArea& a) {",
        "    a.appendBlank();",
        "    a.appendBlank();",
        "}",
    ]
    t1 = site_key("f.cpp", enclosing_function(twin, 1), call_text(twin[1]), LABEL, 1)
    t2 = site_key("f.cpp", enclosing_function(twin, 2), call_text(twin[2]), LABEL, 2)
    if t1 == t2:
        print("selftest FAIL: two identical calls in one function collapsed to one key")
        return 2
    print("selftest: identical twins are two sites OK")

    # ...and pushing the whole block down must not renumber either of them.
    shifted = ["#include <b.hpp>", "", "struct WsLock { int held; };"] + twin
    s1 = site_key("f.cpp", enclosing_function(shifted, 4), call_text(shifted[4]), LABEL, 1)
    s2 = site_key("f.cpp", enclosing_function(shifted, 5), call_text(shifted[5]), LABEL, 2)
    if (s1, s2) != (t1, t2):
        print("selftest FAIL: a relocation renumbered an ordinal")
        print("  before: %s | %s" % (t1, t2))
        print("  after : %s | %s" % (s1, s2))
        return 2
    print("selftest: ordinals survive relocation   OK")

    if is_legacy_baseline([site_key("f.cpp", "g", "a.appendBlank();", LABEL, 1)]):
        print("selftest FAIL: a current-shape baseline was called legacy")
        return 2
    if not is_legacy_baseline(["f.cpp :: g :: a.appendBlank(); :: appendBlank"]):
        print("selftest FAIL: the pre-ordinal shape was not detected as legacy")
        return 2
    print("selftest: legacy shapes refuse a diff   OK")

    # AND THE DEPARTURE FROM THE MODEL: a receiver this file cannot type-confirm
    # must still be COUNTED. hierarchy_service.cpp's `_area` is the real case.
    member = ["void HierarchyService::add_child() {",
              "    _area.appendBlank();",
              "}"]
    code = "\n".join(member)
    if not PATTERN.search(code):
        print("selftest FAIL: a member-receiver call was not matched at all")
        return 2
    if "_area" in set(DBAREA_DECL.findall(code)):
        print("selftest FAIL: the fixture no longer models an unconfirmable receiver")
        return 2
    print("selftest: unconfirmed receiver counted  OK")
    return rc


def main():
    if "--selftest" in sys.argv:
        return selftest()
    if "--emit-baseline" in sys.argv:
        hits, _u, _w = scan()
        for h in hits:
            print(h)
        return 0

    hits, unconfirmed, where = scan()

    by_file = {}
    for h in hits:
        f = h.split(" :: ")[0]
        by_file[f] = by_file.get(f, 0) + 1

    print("append-callers: %d direct appendBlank() call site(s) in %d file(s)"
          % (len(hits), len(by_file)))
    print("  the primitive takes no lock and records no allocation (OI-043, OI-045)")

    if unconfirmed:
        print("  %d call(s) COUNTED whose receiver this file cannot type-confirm:"
              % len(unconfirmed))
        print("  Counted, never dropped -- a member declared in a .hpp reads this way.")
        for u in unconfirmed:
            print("    " + u)

    have_baseline = os.path.exists(BASELINE)
    if not have_baseline:
        print("  baseline %s is absent -- reporting the whole set as the backlog." % BASELINE)
        for f in sorted(by_file, key=lambda k: (-by_file[k], k)):
            print("    %4d  %s" % (by_file[f], f))
        print()
        print("  Freeze it with:")
        print("    python tools/staging/check_append_callers.py --emit-baseline")
        return 0

    with open(BASELINE, "r", encoding="utf-8") as f:
        base = sorted(set(l.strip() for l in f
                          if l.strip() and not l.startswith("#")))

    if is_legacy_baseline(base):
        print("  BASELINE IS IN AN OLD file:line SHAPE -- not compared this run.")
        print("  Regenerate with --emit-baseline and diff the COUNTS before committing.")
        print("  current site count: %d in %d file(s)" % (len(hits), len(by_file)))
        return 0

    new = [h for h in hits if h not in base]
    fixed = [b for b in base if b not in hits]

    if new:
        print("  NEW -- a table grower that does not go through a gatekeeper:")
        for h in new:
            print("    %s        [%s]" % (h, where.get(h, "?")))
        print("  Route it through the append gatekeeper once OI-043 is ruled, or -- if")
        print("  it is a deliberate below-the-funnel grower -- add the FILE to")
        print("  EXEMPT_FILES with the reason, not the line to the baseline.")
    if fixed:
        print("  FIXED -- in the baseline and now routed, drop these lines:")
        for b in fixed:
            print("    " + b)
    if not new and not fixed:
        print("  PASS -- append-caller set matches the baseline exactly.")

    # ADVISORY, never non-zero. The backlog predates the gatekeeper.
    return 0


if __name__ == "__main__":
    sys.exit(main())
