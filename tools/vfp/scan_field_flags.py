#!/usr/bin/env python3
"""Scan every TRACKED file in this repository for DBF field-flag bytes.

WHY THIS EXISTS, which is the whole point of it
-----------------------------------------------
On 2026-09-04 the AIF-091 M1 lane established that `VfpField::flags` had been
read from BYTE 23 (the autoincrement STEP value) when the format puts field
flags at BYTE 18.  The reassurance offered at the time was a measurement:

    "every VFP- and x64-flavor table in this repository carries ZERO at byte 18
     AND ZERO at byte 23 (21 tables) -- the wrong byte and the right byte agree
     on every file we own."

THAT WAS FALSE.  The sweep globbed `*.dbf`.  Visual FoxPro does not name all of
its tables `.dbf`: an `.SCX` is a form, a `.VCX` a class library, an `.MNX` a
menu, an `.FRX` a report -- every one of them a DBF-format table.  Seven tracked
files disagree between byte 18 and byte 23, and all seven were written by VFP
itself.  The counterexamples were never absent; they were filtered out.

So this script selects files BY MAGIC BYTE, never by extension, and enumerates
candidates from `git ls-files` rather than walking the tree (a broad walk over a
mounted filesystem times out and returns empty, which is the same failure mode
one layer down: an instrument that reports a clean absence when it simply could
not look).

Usage, from the repository root:

    python tools/vfp/scan_field_flags.py              # summary + disagreements
    python tools/vfp/scan_field_flags.py --all        # every field of every table
    python tools/vfp/scan_field_flags.py --nonzero    # only fields with any flag set

Exit status is 0 always: this is an instrument, not a gate.  It reports.
"""

import os
import subprocess
import sys

# Version bytes that indicate a DBF-format table this project cares about.
VER_OK = {0x03: "classic",
          0x83: "classic+memo",
          0xF5: "FoxPro 2.6 memo",
          0x30: "VFP",
          0x31: "VFP autoinc",
          0x32: "VFP varlength",
          0x64: "x64"}

# Bit meanings at byte 18, per Microsoft "Table File Structure".
# 0x0C is autoincrementing and CARRIES the 0x04 bit, so it is tested first.
def describe_flags(b):
    if b == 0:
        return ""
    parts = []
    if (b & 0x0C) == 0x0C:
        parts.append("autoinc")
    elif b & 0x04:
        parts.append("binary")
    if b & 0x02:
        parts.append("nullable")
    if b & 0x01:
        parts.append("system")
    left = b & ~0x0F
    if left:
        parts.append("unknown:0x%02X" % left)
    return "+".join(parts) if parts else "0x%02X" % b


def tracked_files():
    out = subprocess.run(["git", "--no-optional-locks", "ls-files"],
                         capture_output=True, text=True, check=True)
    return [ln for ln in out.stdout.split("\n") if ln]


def read_descriptors(path):
    """Return (version, [(name, type, length, byte18, byte23)]) or None."""
    try:
        if os.path.getsize(path) < 64:
            return None
        with open(path, "rb") as f:
            data = f.read(9000)
    except OSError:
        return None

    if not data or data[0] not in VER_OK:
        return None

    hdr_len = data[8] | (data[9] << 8)
    if hdr_len < 65 or hdr_len > 65535:
        return None
    n = (hdr_len - 32 - 1) // 32
    if n < 1 or n > 255:
        return None

    rows = []
    off = 32
    for _ in range(n):
        d = data[off:off + 32]
        if len(d) < 32:
            return None
        if d[0] == 0x0D:          # header terminator
            break
        name = d[0:11].split(b"\x00")[0]
        # A real descriptor name is printable ASCII. Anything else means this is
        # not a DBF header and the magic byte was a coincidence -- refuse rather
        # than report noise as data.
        if not name or any(c < 32 or c > 126 for c in name):
            return None
        rows.append((name.decode("latin-1"), chr(d[11]), d[16], d[18], d[23]))
        off += 32

    if not rows:
        return None
    return data[0], rows


def main(argv):
    show_all = "--all" in argv
    show_nonzero = "--nonzero" in argv

    tables = []
    for p in tracked_files():
        got = read_descriptors(p)
        if got:
            tables.append((p, got[0], got[1]))

    by_ver = {}
    for _, ver, _rows in tables:
        by_ver[ver] = by_ver.get(ver, 0) + 1

    print("tracked DBF-format files (selected by MAGIC BYTE, not extension): %d"
          % len(tables))
    for ver in sorted(by_ver):
        print("    0x%02X %-16s %d" % (ver, VER_OK[ver], by_ver[ver]))
    print()

    disagree = []
    nonzero = []
    for p, ver, rows in tables:
        for r in rows:
            if r[3] != r[4]:
                disagree.append((p, ver, r))
            if r[3] or r[4]:
                nonzero.append((p, ver, r))

    print("FIELDS WHERE BYTE 18 != BYTE 23 -- the right byte and the byte this")
    print("engine used to read DISAGREE.  These are the only files in the tree")
    print("that can tell the two layouts apart: %d" % len(disagree))
    if not disagree:
        print("    (none -- which does NOT mean the decoder is right; it means")
        print("     nothing here can distinguish.  See the module docstring.)")
    for p, ver, r in disagree:
        print("    %-42s 0x%02X  %-11s %s len=%-4d byte18=0x%02X [%s]  byte23=0x%02X"
              % (p, ver, r[0], r[1], r[2], r[3], describe_flags(r[3]), r[4]))
    print()

    if show_nonzero:
        print("ALL FIELDS WITH ANY NONZERO FLAG BYTE: %d" % len(nonzero))
        for p, ver, r in nonzero:
            print("    %-42s 0x%02X  %-11s %s byte18=0x%02X [%s] byte23=0x%02X"
                  % (p, ver, r[0], r[1], r[3], describe_flags(r[3]), r[4]))
        print()

    if show_all:
        for p, ver, rows in tables:
            print("%s  ver=0x%02X  fields=%d" % (p, ver, len(rows)))
            for r in rows:
                print("    %-11s %s len=%-4d dec=%-3s byte18=0x%02X [%s] byte23=0x%02X"
                      % (r[0], r[1], r[2], "", r[3], describe_flags(r[3]), r[4]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
