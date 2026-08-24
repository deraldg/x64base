#!/usr/bin/env python3
"""Report the next free R-number (doctrine rules and lane rulings share one space).

WHY THIS EXISTS. On 2026-08-24 a ruling was about to be stamped R7 on the
assumption that each AIF lane carried its own R1..Rn series. It does not: the
R-space is ONE FLAT GLOBAL SEQUENCE, and R7 had been taken since 2026-08-06
(the owner ruling on AIF-090). Nothing detected that. There was no register, no
allocator and no gate -- the number was checked only because someone happened
to grep. This is the allocator that closes it.

WHY IT IS NOT A ONE-LINER, and this is the part that differs from next_aif.py:
an AIF number can be taken in two DECLARED places, so reading the union of two
files is enough. An R number can be taken in a place nobody declared -- a code
comment written two years ago. So this tool reads:

  1. docs/ai-friendly/R_RULING_REGISTER_V1.md -- the DECLARED register. Rows
     are `| RNNN | ...`.
  2. THE TREE ITSELF -- every `Rnnn` citation in the scanned directories.

The authority is the UNION, and the second source is the one that would have
caught R7. Reading only the register is the tempting mistake and it collides
with roughly a hundred citations that predate the register.

A CITATION BURNS A NUMBER EVEN WHEN NOBODY CAN SAY WHAT IT MEANT. If R44 is
cited and no row explains it, it is reserved, not free. You cannot safely reuse
a number whose meaning you cannot find.

NEXT FREE IS max + 1, NEVER the lowest gap. Gaps are REPORTED so a human can
rule on them; they are never handed out.

THE SCAN SCOPE IS PRINTED, ALWAYS. A scope is a denominator, and an unstated
denominator is how a bounded number turns into an unbounded claim (AIF-090 D2).
If a directory carrying R-citations is not in SCAN_DIRS, this tool is wrong and
its output says exactly where to look.

Run:  $py12 tools\\coordination\\next_r.py
"""
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
REGISTER = ROOT / "docs" / "ai-friendly" / "R_RULING_REGISTER_V1.md"

# Directories that actually carry R-citations, measured 2026-08-24. NOT the
# whole tree: a full-tree walk over this repo takes long enough that the tool
# would stop being run, and a tool that is not run is not a gate.
SCAN_DIRS = [
    "docs/ai-friendly",
    "docs/maintenance",
    "coordination",
    "rules",
    "labtalk",
    "src/cli",
    "src/xbase",
    "src/gui",
    "src/tests",
    "include",
]
SCAN_SUFFIXES = (".md", ".cpp", ".hpp", ".h", ".py")

# ZERO PADDING IS DISPLAY, NOT IDENTITY. The register's earliest rows are
# padded (R095, R096, R099) and later ones are not. A pattern that did not
# normalise would report R95 as FREE while R095 is taken -- the AIF-118 shape
# (the same answer for "absent" and "fine") inside the instrument built to
# prevent it. next_aif.py carries this same lesson in its own comment; it is
# repeated here rather than cross-referenced because the next person to edit
# this regex will be reading THIS file.
CITE = re.compile(r"\bR0*(\d{1,3})\b")
ROW = re.compile(r"^\|\s*R0*(\d{1,3})\s*\|", re.MULTILINE)


def declared() -> set[int]:
    if not REGISTER.is_file():
        print(f"WARNING: register not found: {REGISTER}", file=sys.stderr)
        return set()
    return {int(m) for m in ROW.findall(
        REGISTER.read_text(encoding="utf-8", errors="replace"))}


def cited_map() -> dict[str, set[int]]:
    """{repo-relative posix path: numbers cited in it}.

    PER FILE, not a flat set, because the gate has to answer a question a flat
    set cannot: "is this number cited by anything OTHER than the files this
    change touches". Declaring R119 and citing it in the same change is the
    NORMAL flow -- allocate, declare, cite -- and a gate that could not tell
    that apart from stealing an occupied number would hard-fail every correct
    first use. Found by reasoning it through before shipping, not by it firing.
    """
    out: dict[str, set[int]] = {}
    for rel in SCAN_DIRS:
        base = ROOT / rel
        if not base.is_dir():
            print(f"WARNING: scan dir missing: {rel}", file=sys.stderr)
            continue
        for p in base.rglob("*"):
            if not p.is_file() or p.suffix.lower() not in SCAN_SUFFIXES:
                continue
            if "__pycache__" in p.parts:
                continue
            try:
                nums = {int(m) for m in CITE.findall(
                    p.read_text(encoding="utf-8", errors="replace"))}
            except OSError:
                continue
            out[p.relative_to(ROOT).as_posix()] = nums
    return out


def cited() -> tuple[set[int], int]:
    m = cited_map()
    nums: set[int] = set()
    for v in m.values():
        nums |= v
    return nums, len(m)


def main() -> int:
    reg = declared()
    cite, files = cited()
    taken = reg | cite

    if not taken:
        print("REFUSING: found zero R-numbers in the register or the tree.")
        print("  That is far more likely to be a broken path than an empty")
        print("  project, and handing out R1 on it would be a collision.")
        return 2

    hi = max(taken)
    nxt = hi + 1

    print("=== next free R-number ===")
    print(f"scan scope      : {len(SCAN_DIRS)} dir(s), {files} file(s), "
          f"suffixes {' '.join(SCAN_SUFFIXES)}")
    for rel in SCAN_DIRS:
        print(f"                  {rel}")
    print(f"register        : {len(reg)} declared   "
          f"{REGISTER.relative_to(ROOT)}")
    print(f"cited in tree   : {len(cite)} number(s)")
    print(f"union           : {len(taken)} distinct")
    print(f"highest taken   : R{hi}")
    print()
    print(f"NEXT FREE       : R{nxt}")
    print()
    print("Record it in the register BEFORE you cite it. Include the KIND")
    print("column -- doctrine and rulings share this sequence, so the kind")
    print("cannot be inferred from the number.")
    print()

    undeclared = sorted(cite - reg)
    if undeclared:
        print(f"cited but NOT declared ({len(undeclared)}) -- reserved, never "
              f"reusable, back-fill welcome:")
        print("  " + ", ".join(f"R{n}" for n in undeclared))

    phantom = sorted(reg - cite)
    if phantom:
        print(f"declared but cited nowhere in scope ({len(phantom)}): "
              + ", ".join(f"R{n}" for n in phantom))

    gaps = sorted(set(range(min(taken), hi)) - taken)
    if gaps:
        print(f"gaps, NOT reusable ({len(gaps)}): "
              + ", ".join(f"R{n}" for n in gaps))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
