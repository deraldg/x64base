#!/usr/bin/env python3
"""ASCII-normalize documentation so `check_house_style.py` can pass it.

AIF-090. `CLAUDE.md` requires ASCII in scripts and docs: `--` and `->`, never the
Unicode originals. `tools/staging/check_house_style.py` returns 2 (BLOCK) on
non-ASCII in ADDED lines, and every line of a previously-untracked file is an
added line. So a cited-but-untracked document cannot be committed until it is
normalized. That gate says a file FAILS; this one says how to fix it.

WHY THIS IS NOT A `sed` ONE-LINER. The repo's most-named defect shape is "a thing
that reports success without doing its job". A blind substitution is exactly
that: it silently mangles the codepoints nobody thought about. So the mapping is
an explicit table, and ANY non-ASCII character absent from that table is a HARD
FAILURE that refuses to write the file. Unknown input is never guessed at.

THIS FILE IS ITSELF PURE ASCII. The mapping is written with `\\uXXXX` escapes
rather than literal glyphs, so the tool obeys the rule it enforces and survives
any transport that mishandles encoding. `check_house_style.py` only scans `.md`
(`CHECKED_SUFFIXES`), so this is discipline rather than gate-driven -- which is
the point.

    python tools/staging/ascii_normalize.py FILE...           # dry run, report
    python tools/staging/ascii_normalize.py --apply FILE...   # rewrite in place
    python tools/staging/ascii_normalize.py --table           # print the mapping

Exit codes: 0 clean/ok, 1 bad usage or unreadable file, 2 unmapped codepoint
found (nothing written), 3 post-write verification failed.

Line endings are preserved byte-for-byte by round-tripping with `newline=""`,
which matters because `.gitattributes` pins `*.md text eol=lf` while other repo
files are CRLF. Use `open(..., newline="")`, NOT `Path.read_text(newline=...)`:
that keyword is 3.13+ and the host tools target 3.12.

Measured first use, 2026-08-06: 19 cited-but-untracked lane documents, 752
non-ASCII characters across 24 distinct codepoints, all reduced to 0; the
resulting commit passed `house-style` on ~3,400 added lines.
"""

from __future__ import annotations

import argparse
import re
import sys
import unicodedata
from pathlib import Path

# ---------------------------------------------------------------- mapping
# Named constants so the regex rules below stay readable while the source stays
# ASCII. Do not inline literal glyphs here.
SECTION_SIGN = "\u00a7"   # section sign
ELEMENT_OF = "\u2208"     # element of

# Regex rules run FIRST, because they need surrounding context that a
# character-level table cannot see. Each entry is (pattern, replacement, why).
REGEX_RULES = [
    (re.compile(SECTION_SIGN + r"\s*(?=\d)"), "sec. ", "section sign before a number"),
    (re.compile(SECTION_SIGN), "sec.", "bare section sign"),
    # An ALPHABETIC replacement must carry its own spacing or it fuses with its
    # neighbours: an unspaced element-of expression becomes `xinS`. Symbol
    # replacements (`!=`, `<=`) have no such hazard. Caught by fixture, 2026-08-06.
    (re.compile(r"\s*" + ELEMENT_OF + r"\s*"), " in ", "element-of, spaced"),
]

# Character-level table. Every non-ASCII codepoint that may appear MUST be here.
CHAR_MAP = {
    "\u2014": "--",     # EM DASH                       house rule: use --
    "\u2013": "-",      # EN DASH                       observed only in ranges
    "\u2026": "...",    # HORIZONTAL ELLIPSIS
    "\u2192": "->",     # RIGHTWARDS ARROW
    "\u2190": "<-",     # LEFTWARDS ARROW
    "\u2194": "<->",    # LEFT RIGHT ARROW
    "\u21d2": "=>",     # RIGHTWARDS DOUBLE ARROW
    "\u2260": "!=",     # NOT EQUAL TO
    "\u2248": "~=",     # ALMOST EQUAL TO
    "\u2264": "<=",     # LESS-THAN OR EQUAL TO
    "\u2265": ">=",     # GREATER-THAN OR EQUAL TO
    "\u2261": "==",     # IDENTICAL TO
    "\u2208": "in",     # ELEMENT OF                    (regex handles spacing)
    "\u00d7": "x",      # MULTIPLICATION SIGN           product and cross-product
    "\u00b1": "+/-",    # PLUS-MINUS SIGN
    "\u00b2": "^2",     # SUPERSCRIPT TWO
    "\u00b3": "^3",     # SUPERSCRIPT THREE
    "\u2074": "^4",     # SUPERSCRIPT FOUR
    "\u00b5": "u",      # MICRO SIGN                    us, not microsecond glyph
    "\u00b7": "-",      # MIDDLE DOT                    observed as a separator
    "\u2019": "'",      # RIGHT SINGLE QUOTATION MARK
    "\u2018": "'",      # LEFT SINGLE QUOTATION MARK
    "\u201c": '"',      # LEFT DOUBLE QUOTATION MARK
    "\u201d": '"',      # RIGHT DOUBLE QUOTATION MARK
    "\u00e7": "c",      # LATIN SMALL LETTER C WITH CEDILLA   ("facade")
    "\u00a0": " ",      # NO-BREAK SPACE
    "\u2011": "-",      # NON-BREAKING HYPHEN
    "\u2212": "-",      # MINUS SIGN
    # Status glyphs. REVIEW THESE: a glyph carries a judgement, and the ASCII
    # word chosen for it is an editorial act, not a transliteration.
    "\u2713": "yes",    # CHECK MARK                    seen in present? columns
    "\u2717": "no",     # BALLOT X                      paired with the above
    "\u2705": "[x]",    # WHITE HEAVY CHECK MARK        seen decorating "**DONE**"
}

REVIEW_GLYPHS = {"\u2713", "\u2717", "\u2705"}


def describe(ch: str) -> str:
    try:
        name = unicodedata.name(ch)
    except ValueError:
        name = "unnamed"
    return f"U+{ord(ch):04X} {name}"


def normalize(text: str) -> tuple[str, dict[str, int]]:
    """Apply regex rules then the char table. Returns (text, counts)."""
    counts: dict[str, int] = {}
    for pattern, repl, _why in REGEX_RULES:
        text, n = pattern.subn(repl, text)
        if n:
            counts[pattern.pattern] = counts.get(pattern.pattern, 0) + n
    out = []
    for ch in text:
        if ord(ch) < 128:
            out.append(ch)
            continue
        if ch in CHAR_MAP:
            out.append(CHAR_MAP[ch])
            counts[ch] = counts.get(ch, 0) + 1
        else:
            out.append(ch)  # left intact; caller must refuse to write
            counts["UNMAPPED:" + ch] = counts.get("UNMAPPED:" + ch, 0) + 1
    return "".join(out), counts


def process(path: Path, apply: bool) -> int:
    try:
        # NOT Path.read_text(newline=...): that keyword is 3.13+ and the host
        # tools target 3.12. Caught by fixture on first run, 2026-08-06.
        with open(path, "r", encoding="utf-8", newline="") as fh:
            raw = fh.read()
    except (OSError, UnicodeDecodeError) as exc:
        print(f"  ERROR {path}: {exc}", file=sys.stderr)
        return 1

    before = sum(1 for ch in raw if ord(ch) >= 128)
    if before == 0:
        print(f"  clean  {path}")
        return 0

    new, counts = normalize(raw)
    unmapped = {k[len("UNMAPPED:"):]: v for k, v in counts.items()
                if k.startswith("UNMAPPED:")}

    detail = ", ".join(
        f"{describe(k)} x{v}" for k, v in sorted(counts.items())
        if len(k) == 1
    )
    regex_hits = sum(v for k, v in counts.items()
                     if len(k) > 1 and not k.startswith("UNMAPPED:"))
    print(f"  {'APPLY ' if apply else 'dryrun'} {path}")
    print(f"           {before} non-ASCII char(s)"
          f"{'; ' + str(regex_hits) + ' regex hit(s)' if regex_hits else ''}")
    if detail:
        print(f"           {detail}")

    for ch in sorted(set(counts) & REVIEW_GLYPHS):
        print(f"           REVIEW: {describe(ch)} -> {CHAR_MAP[ch]!r} "
              f"(editorial choice, not transliteration)")

    if unmapped:
        for ch, n in sorted(unmapped.items()):
            print(f"           UNMAPPED {describe(ch)} x{n} -- refusing to write",
                  file=sys.stderr)
        return 2

    if not apply:
        return 0

    with open(path, "w", encoding="utf-8", newline="") as fh:
        fh.write(new)
    with open(path, "r", encoding="utf-8", newline="") as fh:
        check = fh.read()
    left = sum(1 for ch in check if ord(ch) >= 128)
    if left:
        print(f"           VERIFY FAILED: {left} non-ASCII remain", file=sys.stderr)
        return 3
    print("           verified: 0 non-ASCII remain")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="ASCII-normalize documentation.")
    ap.add_argument("files", nargs="*", type=Path)
    ap.add_argument("--apply", action="store_true", help="rewrite in place")
    ap.add_argument("--table", action="store_true", help="print mapping and exit")
    args = ap.parse_args()

    if args.table:
        for pattern, repl, why in REGEX_RULES:
            print(f"  regex {pattern.pattern!r:34} -> {repl!r:8} {why}")
        for ch, repl in sorted(CHAR_MAP.items()):
            flag = "  <- REVIEW" if ch in REVIEW_GLYPHS else ""
            print(f"  {describe(ch):46} -> {repl!r}{flag}")
        return 0

    if not args.files:
        ap.error("no files given (use --table to inspect the mapping)")

    worst = 0
    for path in args.files:
        worst = max(worst, process(path, args.apply))
    print()
    print("PASS" if worst == 0 else f"FAIL (exit {worst})")
    return worst


if __name__ == "__main__":
    sys.exit(main())
