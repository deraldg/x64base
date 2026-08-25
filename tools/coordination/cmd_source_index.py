#!/usr/bin/env python3
"""Command -> handler -> SOURCE FILE. The last hop the SYSCMD catalog does not carry.

WHY THIS EXISTS. `dottalkpp/data/metadata/SYSCMD.dbf` is the command registry --
212 rows of CAN_NAME and HANDLER -- and it is the fastest way to find where a
verb lives without knowing any filenames. But the chain STOPS AT THE SYMBOL:
SYSCMD says SKIP is handled by cmd_SKIP and does not say which file that is.
Every other table in the metadata graph carries SRC_FILE; the command spine does
not.

Adding the column is a lane of its own -- SYSCMD's schema is declared in
tools/dbf/schema_registry.py with writable=False, guarded by a test, and that
registry has an open convention question (VER_AT widths, study finding R5)
blocking further catalogs from registering. So this DERIVES the hop instead,
from the tree, every time it runs. Nothing is cached and nothing can go stale.

AND IT REPORTS ITS OWN TRUSTWORTHINESS, which is the point. SYSCMD is GENERATED
by the full-stack documentation push, so it is exactly as old as the last one.
This tool prints that age AND the number of command files that changed since --
because staleness measured in DAYS means less each month as the project
accelerates, while staleness measured in CHANGE does not.

  $py12 tools\\coordination\\cmd_source_index.py            -- the report
  $py12 tools\\coordination\\cmd_source_index.py --map      -- name/handler/file, tab separated
"""
import datetime
import pathlib
import re
import struct
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
SYSCMD = ROOT / "dottalkpp" / "data" / "metadata" / "SYSCMD.dbf"
SCAN = ROOT / "src"

FIELDS = [("CMD_ID", 32), ("CAN_NAME", 80), ("TYPE", 20),
          ("VIS", 20), ("HANDLER", 96), ("ACTIVE", 1)]


def read_syscmd():
    """Rows plus the header's own last-update date.

    The DBF header carries its generation date in bytes 1-3, which makes every
    catalog self-dating for free -- no VER_AT column needed, and SYSCMD has none.
    Deleted rows are skipped: a row flagged '*' is not part of the registry, and
    reading past the flag is how a raw parser silently invents data.
    """
    raw = SYSCMD.read_bytes()
    yy, mm, dd = raw[1], raw[2], raw[3]
    nrec, hlen, rlen = struct.unpack("<IHH", raw[4:12])
    stamp = datetime.date(1900 + yy if yy >= 70 else 2000 + yy, mm, dd)

    offs, off = [], 1
    for name, size in FIELDS:
        offs.append((name, off, size))
        off += size

    rows = []
    for i in range(nrec):
        rec = raw[hlen + i * rlen: hlen + (i + 1) * rlen]
        if len(rec) < rlen or rec[:1] == b"*":
            continue
        rows.append({n: rec[a:a + s].decode("latin1").strip() for n, a, s in offs})
    return rows, stamp


def find_definitions(handlers):
    """Locate each named handler's DEFINITION -- and NOT its declaration.

    SEARCHES FOR THE NAMES THE REGISTRY GIVES, not for a `cmd_*` prefix. A first
    cut assumed the prefix and reported 18 unresolved handlers; 11 were `edu_*`
    and the parser was wrong, not the data.

    A SECOND CUT MATCHED DECLARATIONS AND WAS WORSE, because it was wrong while
    looking right. `extern void cmd_GOTO(...);` in cmd_browser.cpp matched, and
    since files were scanned in sorted order the first hit won -- so the tool
    reported GOTO in cmd_browser.cpp, TOP in cmd_browsetui.cpp and WORKSPACE in
    cmd_ersatz.cpp. All three are real files that really mention the symbol, and
    all three are the wrong answer. The aggregate looked perfect: 205 resolved,
    0 dangling.

    THAT IS THE FAILURE THIS HOUSE KEEPS NAMING. A count is a fact about a loop
    until something declares what it should be, and shape was asserted while
    every value went unchecked. It was caught by spot-checking six commands
    whose files were known from having read them the same day.

    So: the parameter list must be followed by `{`, not `;`. A declaration is
    skipped, a definition is kept, and a handler found in more than one place is
    REPORTED rather than silently resolved to whichever sorted first.
    """
    if not handlers:
        return {}, {}
    alt = "|".join(re.escape(h) for h in sorted(handlers))
    # name ( ...balanced-ish args... ) [const] {     -- the trailing brace is the
    # whole discriminator between a definition and a declaration.
    pat = re.compile(
        r"(?<![A-Za-z0-9_])(" + alt + r")\s*\([^;{}]*\)\s*(?:const\s*)?(?:noexcept\s*)?\{",
        re.M | re.S)
    hits = {}
    for path in sorted(SCAN.rglob("*.cpp")):
        try:
            text = path.read_text(encoding="latin1")
        except OSError:
            continue
        for m in pat.finditer(text):
            rel = path.relative_to(ROOT).as_posix()
            hits.setdefault(m.group(1), []).append(rel)
    found = {}
    multi = {}
    for name, paths in hits.items():
        uniq = sorted(set(paths))
        found[name] = uniq[0]
        if len(uniq) > 1:
            multi[name] = uniq
    return found, multi


def changed_since(stamp):
    """Command files touched since the catalog was generated -- an UPPER BOUND.

    A commit touching cmd_skip.cpp does not necessarily change its CAN_NAME or
    HANDLER, so this is the fraction that MIGHT have drifted, not the fraction
    that did. Erring high is right for navigation and wrong to quote as measured
    drift, so it is labelled as a bound wherever it is printed.
    """
    try:
        out = subprocess.run(
            ["git", "log", "--name-only", "--pretty=format:",
             f"--since={stamp.isoformat()}", "--", "src/cli"],
            cwd=ROOT, capture_output=True, text=True, timeout=60).stdout
    except Exception:
        return None
    return len({ln.strip() for ln in out.splitlines()
                if ln.strip().startswith("src/cli/cmd_") and ln.strip().endswith(".cpp")})


def main():
    rows, stamp = read_syscmd()
    named = {r["HANDLER"] for r in rows if r["HANDLER"]}
    found, multi = find_definitions(named)

    resolved = [r for r in rows if r["HANDLER"] and r["HANDLER"] in found]
    dangling = [r for r in rows if r["HANDLER"] and r["HANDLER"] not in found]
    blank = [r for r in rows if not r["HANDLER"]]

    if "--map" in sys.argv:
        for r in sorted(resolved, key=lambda x: x["CAN_NAME"]):
            print(f"{r['CAN_NAME']}\t{r['HANDLER']}\t{found[r['HANDLER']]}")
        return 0

    age = (datetime.date.today() - stamp).days
    changed = changed_since(stamp)

    print("=== command -> source index ===")
    print(f"catalog      : {SYSCMD.relative_to(ROOT).as_posix()}")
    print(f"generated    : {stamp.isoformat()}  ({age} days ago)")
    if changed is not None:
        pct = 100.0 * changed / len(rows) if rows else 0.0
        print(f"drift bound  : {changed} command file(s) changed since, "
              f"vs {len(rows)} rows -- AT MOST {pct:.0f}% unverified")
    print()
    print(f"rows         : {len(rows)}")
    print(f"resolved     : {len(resolved)}  across {len(set(found.values()))} file(s)")
    print(f"dangling     : {len(dangling)}  (handler named, no definition found)")
    print(f"blank        : {len(blank)}  (row ACTIVE with no handler recorded)")

    if multi:
        print("\nDEFINED IN MORE THAN ONE PLACE -- reported, not silently picked.")
        print("The first is used; that choice is a guess and is shown as one:")
        for name, paths in sorted(multi.items()):
            print(f"   {name:<24} {', '.join(paths)}")

    if dangling:
        print("\nDANGLING -- the registry names a handler the tree does not define.")
        print("This is the failure that MISLEADS, and it should be empty:")
        for r in dangling:
            print(f"   {r['CAN_NAME']:<20} -> {r['HANDLER']}")

    if blank:
        print("\nBLANK HANDLER, ROW ACTIVE -- the registry OMITS rather than misleads,")
        print("which is the better failure, but these are omissions at the centre:")
        for r in blank:
            print(f"   {r['CAN_NAME']:<20} TYPE={r['TYPE']}")

    print("\nUSE THIS TO NAVIGATE, NEVER TO ASSERT. The catalog is a generated")
    print("snapshot; the tree is the fact. --map gives name/handler/file for the")
    print("resolved set, which is a starting point for reading, not evidence.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
