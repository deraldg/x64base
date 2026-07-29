#!/usr/bin/env python3
"""sql_conformance_gate.py -- the SQL conformance map must point at real commands.

`include/sql_ref.hpp` documents SQL constructs as other engines implement them.
Its `x64` field answers, per construct, whether x64base does that and by which
command (AIF-074, 2026-07-29). The field's governing rule is: NEVER restate a
command's grammar there -- name the command and point at its USAGE. Grammar
copied into a second place drifts from the first.

This gate enforces the half of that rule a machine can check: every
"<COMMAND> USAGE" pointer in an x64 field must name a command the shell
actually registers. A conformance map that sends a reader to a command that
does not exist is worse than no map, because it reads as authoritative.

It also REPORTS coverage (mapped vs unmapped). Coverage is informational and
never fails: an empty x64 field means "nobody has checked yet", which is an
honest state. Only a broken pointer fails.

Usage:
  python tools/staging/sql_conformance_gate.py [repo_root]

Exit codes:
  0  every USAGE pointer resolves
  1  at least one pointer names an unregistered command
  2  inputs could not be parsed (hard failure -- a gate that cannot see its
     subject must not report success)
"""

import os
import re
import sys


def read(path: str) -> str:
    with open(path, encoding="utf-8", errors="replace") as fh:
        return fh.read()


def collect_registered(root: str):
    """Command names the shell registry actually registers, upper-cased."""
    names = set()
    src = os.path.join(root, "src")
    if not os.path.isdir(src):
        return names
    for dirpath, _dirs, files in os.walk(src):
        for name in files:
            if not name.endswith(".cpp"):
                continue
            text = read(os.path.join(dirpath, name))
            for m in re.findall(r'registry\(\)\.add\(\s*"([^"]+)"', text):
                names.add(m.upper())
            for m in re.findall(r'add_alias\(\s*"([^"]+)"', text):
                names.add(m.upper())
    return names


def collect_entries(root: str):
    """Return [(construct_name, x64_text)] for entries with a populated x64 field.

    The catalog is a C++ aggregate initializer list. Rather than parse C++, split
    on entry starts ({"NAME",) and treat everything up to the next entry as that
    entry's body -- the x64 text is the only place the marker words appear.
    """
    path = os.path.join(root, "include", "sql_ref.hpp")
    if not os.path.isfile(path):
        return None, "include/sql_ref.hpp not found at " + path
    text = read(path)
    start = text.find("items = {")
    if start < 0:
        return None, "could not locate the catalog initializer in sql_ref.hpp"
    body = text[start:]

    starts = [(m.start(), m.group(1)) for m in re.finditer(r'\{"([A-Z0-9][A-Z0-9\-]*)",', body)]
    if not starts:
        return None, "catalog located but no entries parsed"

    out = []
    for i, (pos, name) in enumerate(starts):
        end = starts[i + 1][0] if i + 1 < len(starts) else len(body)
        chunk = body[pos:end]
        # The x64 field is the trailing string run; markers make it identifiable.
        if re.search(r"SUPPORTED|EQUIVALENT|PARTIAL|N/A|USAGE", chunk):
            out.append((name, chunk))
        else:
            out.append((name, ""))
    return out, None


USAGE_REF = re.compile(r"\b([A-Z][A-Z0-9_]*(?:\s+[A-Z][A-Z0-9_]*)?)\s+USAGE\b")


def resolves(candidate: str, registered: set) -> bool:
    c = candidate.strip().upper()
    if c in registered or c.replace(" ", "_") in registered:
        return True
    # A two-word pointer may name a command plus a subcommand (TABLE BUFFER);
    # accept when the leading word is itself a registered command.
    head = c.split()[0]
    return head in registered


def main() -> int:
    root = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else os.getcwd())

    entries, err = collect_entries(root)
    if err:
        print("SQL CONFORMANCE GATE: CANNOT VERIFY -- " + err)
        return 2

    registered = collect_registered(root)
    if not registered:
        print("SQL CONFORMANCE GATE: CANNOT VERIFY -- no registry().add(...) found under src/")
        return 2

    mapped = [(n, t) for n, t in entries if t]
    broken = []
    pointers = 0
    for name, text in mapped:
        for m in USAGE_REF.finditer(text):
            cand = m.group(1)
            # "SEE X USAGE" -- drop a leading SEE/AND that the regex may absorb.
            cand = re.sub(r"^(SEE|AND)\s+", "", cand.strip())
            if not cand:
                continue
            pointers += 1
            if not resolves(cand, registered):
                broken.append((name, cand))

    total = len(entries)
    print("SQL CONFORMANCE GATE")
    print("  constructs      : {0}".format(total))
    print("  mapped to x64   : {0}".format(len(mapped)))
    print("  not yet mapped  : {0}  (informational -- honest 'unchecked', never a failure)"
          .format(total - len(mapped)))
    print("  USAGE pointers  : {0} checked against {1} registered commands"
          .format(pointers, len(registered)))

    if broken:
        print("")
        print("FAIL: {0} pointer(s) name a command that is not registered:".format(len(broken)))
        for construct, cand in broken:
            print("  {0:<22} -> '{1} USAGE'  NOT REGISTERED".format(construct, cand))
        print("")
        print("  Fix the pointer in include/sql_ref.hpp, or register the command.")
        return 1

    print("")
    print("PASS: every USAGE pointer in the conformance map resolves to a real command.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
