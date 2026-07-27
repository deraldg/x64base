#!/usr/bin/env python3
"""
AIF-067 M4 -- generate MessageId::SetUsageText from the @dottalk.subusage contracts.

WHY GENERATE THE STRING AND NOT READ THE TABLE
    The lane doc originally proposed rendering SET USAGE from SYSSUBCMD at
    runtime. Priced and rejected:
      - it makes a core DISCOVERABILITY command depend on a seeded DBF; SET USAGE
        failing because metadata was not seeded is worse than the drift it fixes
      - it needs a fallback for a missing table, and a fallback is a SECOND
        description of the surface, i.e. the original defect reissued
      - roughly a day of C++ for a guarantee obtainable at author time

BUILD GATES ARE HONOURED (M4b)
    Nine... eight ladder arms sit behind #if guards:
        DOTTALK_HAS_XINDEX   INDEX, ORDER, CNX
        DOTTALK_WITH_DEV     FILTER, RELATION, RELATIONS
        DOTTALK_WITH_INDEX   CDX, LMDB
    The hand-written literal listed all of them unconditionally, so a build
    without DOTTALK_WITH_DEV advertised SET FILTER / SET RELATION / SET RELATIONS
    while dispatching none of them. That is the SAME defect as the missing
    ERRORSTOP and INDEXTXN, pointing the other way: the first made working
    options invisible, this makes absent options visible. Both are the usage
    text disagreeing with the ladder.

    Fixed by emitting the option list as #if-guarded ADJACENT STRING LITERALS.
    The preprocessor runs first, so what reaches the compiler is a run of
    adjacent literals that it concatenates -- a compile-time constant with zero
    runtime cost, and no way for a configuration to advertise what it lacks.

    Note EVERY developer-tier option is gated, so the "Developer / transitional:"
    header is itself guarded by the OR of the three macros. Printing a section
    header above nothing is its own small lie.

WHAT THIS OWNS
    OWNS   the option lines. Command syntax is NOT translatable content -- the
           keywords are English in every locale, so a translator has nothing to
           do here and can only introduce error.
    LEAVES the framing prose in the message catalog, where translators reach it.
    (Splitting framing and options into two MessageIds is the cleaner end state
    and needs a C++ change to print_set_usage(); recorded as owed.)

REGION MARKERS
    The generated text is delimited by @generated:set-usage-text BEGIN/END so
    this tool owns an explicit region rather than pattern-matching a literal
    whose shape it just changed. --check compares the region verbatim.

MODES
    --check  compare only, exit 1 on drift. Run this in CI.
    --write  rewrite the region in place.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

MSG_FILE = Path("src/help/helpdata_messages.cpp")
LADDER = Path("src/cli/cmd_set.cpp")

BEGIN = "// @generated:set-usage-text BEGIN"
END = "// @generated:set-usage-text END"

# --------------------------------------------------------------------------- #
# TWO copies, not one (found 2026-07-27, after generating the first)
# --------------------------------------------------------------------------- #
# helpdata_messages.cpp carries the SET usage text TWICE:
#
#   1. the DESCRIPTOR table  { MessageId::SetUsageText, "SET_USAGE_TEXT",
#                              "COMMAND:SET", "USAGE", "INFO", <text> }
#      -- symbol, subject, category, severity, and the DEFAULT text
#   2. the LOCALE table      { MessageId::SetUsageText, "en-US", <text> }
#
# The first version of this generator rewrote only the locale row. The
# descriptor copy stayed on the old text -- missing ERRORSTOP and INDEXTXN,
# still advertising gated options unconditionally. Nothing looked wrong,
# because the locale row wins at resolution time and SET USAGE printed
# correctly; the stale copy only surfaces when locale lookup misses.
#
# That is this lane's own defect, committed by its own fix, one layer down:
# a surface described in two places where only one was made derived. It was
# caught by a grep for `#if` accidentally printing line 295 -- not by design,
# and not by the guard. Both copies are generated now, from one body.
BEGIN2 = "// @generated:set-usage-descriptor BEGIN"
END2 = "// @generated:set-usage-descriptor END"

DESCRIPTOR_PREFIX = [
    "{",
    "    MessageId::SetUsageText,",
    '    "SET_USAGE_TEXT",',
    '    "COMMAND:SET",',
    '    "USAGE",',
    '    "INFO",',
]

HEAD = ["Usage:", "  SET", "  SET USAGE", "  SET <option> [args]"]
PUBLIC_HDR = "Public options:"
DEV_HDR = "Developer / transitional:"

# --------------------------------------------------------------------------- #
# Alias visibility -- DECLARED, not mechanical
# --------------------------------------------------------------------------- #
# The first version of this generator emitted only each contract's canonical
# `usage:` lines, and the dry run showed it would have DELETED four SET LOCALE
# lines the hand-written literal carried. LOCALE is an alias of LANGUAGE, so
# nothing would have stopped dispatching -- it would simply have become
# undiscoverable. That is the exact defect this lane exists to close, arriving
# by way of its own fix. Generation removes drift; it does not by itself
# preserve intent, and the old text encoded an intent (advertise both spellings)
# that no contract field expressed.
#
#   EMITTED    LANGUAGE -> LOCALE     two equal user-facing spellings
#   SUPPRESSED CASE -> SETCASE        compatibility spellings, not synonyms;
#              NEAR -> SETNEAR        SETCASE is separately registered anyway,
#                                     and the old text listed neither
#   SUPPRESSED USAGE -> HELP, ?       covered by the header block
ALIAS_EMIT: dict[str, list[str]] = {"LANGUAGE": ["LOCALE"]}
SKIP_SUBS = {"USAGE"}


def parse_contracts(root: Path) -> list[dict]:
    text = (root / LADDER).read_text(encoding="utf-8", errors="replace")
    out = []
    for block in re.findall(r"// @dottalk\.subusage v1\n(?:\s*//[^\n]*\n)+", text):
        def get(k: str) -> str:
            m = re.search(rf"//\s*{k}:\s*(.+)", block)
            return m.group(1).strip() if m else ""

        sub = get("sub")
        if not sub:
            continue
        usage, collecting = [], False
        for line in block.split("\n"):
            body = line.strip()
            if not body.startswith("//"):
                continue
            b = body[2:]
            if re.match(r"^\s*usage:\s*$", b):
                collecting = True
                continue
            if collecting:
                if re.match(r"^\s{0,3}\S+:\s*", b):
                    collecting = False
                    continue
                # A blank comment line ends the usage list. Without this, prose
                # trailing inside the block is collected as syntax -- see the
                # matching note in generate_syssubcmd.py.
                if not b.strip():
                    collecting = False
                    continue
                usage.append(b.strip())
        out.append({"sub": sub.upper(), "tier": get("tier") or "public",
                    "gate": get("build-gate"), "usage": usage})
    return out


def option_lines(contracts: list[dict]) -> tuple[list, list, list[str]]:
    """Return (public, developer, gates_seen) as lists of (gate, text)."""
    pub, dev, gates = [], [], []
    for c in sorted(contracts, key=lambda c: c["sub"]):
        if c["sub"] in SKIP_SUBS:
            continue
        lines = list(c["usage"])
        for alias in ALIAS_EMIT.get(c["sub"], []):
            lines += [re.sub(rf"^SET {c['sub']}\b", f"SET {alias}", u)
                      for u in c["usage"]]
        if not lines:
            continue
        gate = c["gate"]
        if gate and gate not in gates:
            gates.append(gate)
        target = dev if c["tier"] == "developer" else pub
        target.extend((gate, "  " + l) for l in lines)
    return pub, dev, gates


def cpp_escape(s: str) -> str:
    return s.replace("\\", "\\\\").replace('"', '\\"')


def emit_region(contracts: list[dict], indent: str,
                begin: str = BEGIN, end: str = END,
                prefix: list[str] | None = None) -> str:
    pub, dev, _ = option_lines(contracts)
    body = indent + "    "

    def lit(s: str) -> str:
        return f'{body}"{cpp_escape(s)}\\n"'

    out = [begin,
           "// GENERATED by tools/fullstack_docs/generate_set_usage_text.py (AIF-067 M4).",
           "// Do not hand-edit -- fix the @dottalk.subusage contract in src/cli/cmd_set.cpp",
           "// and regenerate. `--check` compares this region verbatim.",
           "//",
           "// The #if blocks below are NOT decoration: eight SET options are compiled",
           "// conditionally, and a build that lacks them must not advertise them.",
           "// Adjacent string literals concatenate after preprocessing, so this stays a",
           "// single compile-time constant.",
           "//",
           "// This text exists TWICE (descriptor table + locale table). Both are",
           "// generated from this one body; see the note by BEGIN2 for why that",
           "// matters and how the second copy was missed.",
           ]
    if prefix is None:
        out.append(f'{indent}{{ MessageId::SetUsageText, "en-US",')
    else:
        out.extend(indent + p for p in prefix)

    def emit(rows: list) -> None:
        prev = None
        for gate, text in rows:
            if gate != prev:
                if prev:
                    out.append("#endif")
                if gate:
                    out.append(f"#if {gate}")
                prev = gate
            out.append(lit(text))
        if prev:
            out.append("#endif")

    for h in HEAD:
        out.append(lit(h))
    if pub:
        out.append(lit(PUBLIC_HDR))
        emit(pub)
    if dev:
        # Every developer-tier option is gated, so the header must be too --
        # a section heading above an empty section is its own small lie.
        dev_gates = sorted({g for g, _ in dev if g})
        cond = " || ".join(f"({g})" for g in dev_gates) if dev_gates else ""
        if cond:
            out.append(f"#if {cond}")
        out.append(lit(""))
        out.append(lit(DEV_HDR))
        emit(dev)
        if cond:
            out.append("#endif")

    out.append(f"{indent}}},")
    out.append(end)
    return "\n".join(out)


def _marked(lines: list[str], begin: str, end: str):
    b = e = None
    for i, l in enumerate(lines):
        if begin in l:
            b = i
        elif end in l and b is not None:
            e = i
            break
    return (b, e) if b is not None and e is not None else None


def locate_locale(lines: list[str]):
    """(start, end, indent) for the en-US locale row, markers inclusive."""
    m = _marked(lines, BEGIN, END)
    if m:
        for l in lines[m[0]:m[1]]:
            mm = re.match(r"^(\s*)\{\s*MessageId::SetUsageText", l)
            if mm:
                return m[0], m[1], mm.group(1)
        return m[0], m[1], "        "
    for i, l in enumerate(lines):
        if 'MessageId::SetUsageText, "en-US"' in l:
            return i, i, re.match(r"^(\s*)", l).group(1)
    raise SystemExit("MessageId::SetUsageText en-US row not found")


def locate_descriptor(lines: list[str]):
    """
    (start, end, indent) for the descriptor-table entry, markers inclusive.

    Pre-migration the entry spans several lines, so the fallback walks BACK to
    the opening brace and FORWARD to the closing `},` rather than assuming a
    one-line shape -- the mistake that hid this copy in the first place.
    """
    m = _marked(lines, BEGIN2, END2)
    if m:
        for l in lines[m[0]:m[1]]:
            mm = re.match(r"^(\s*)\{\s*$", l)
            if mm:
                return m[0], m[1], mm.group(1)
        return m[0], m[1], "        "
    for i, l in enumerate(lines):
        if re.match(r"^\s*MessageId::SetUsageText,\s*$", l):
            s = i
            while s > 0 and not re.match(r"^(\s*)\{\s*$", lines[s]):
                s -= 1
            e = i
            while e < len(lines) - 1 and not re.match(r"^\s*\},?\s*$", lines[e]):
                e += 1
            return s, e, re.match(r"^(\s*)", lines[s]).group(1)
    raise SystemExit("MessageId::SetUsageText descriptor entry not found")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    root = Path(a.root).resolve()

    contracts = parse_contracts(root)
    msg_path = root / MSG_FILE
    text = msg_path.read_text(encoding="utf-8", errors="surrogateescape")
    lines = text.splitlines()

    pub, dev, gates = option_lines(contracts)
    gated = sum(1 for g, _ in pub + dev if g)
    print(f"contracts {len(contracts)}   gated option lines {gated}   gates {gates}")

    # BOTH copies. Resolve regions first, then rewrite from the BOTTOM UP so the
    # earlier region's line indices are still valid after the later one changes
    # length.
    targets = []
    for name, loc, kw in (
        ("locale", locate_locale, {}),
        ("descriptor", locate_descriptor,
         {"begin": BEGIN2, "end": END2, "prefix": DESCRIPTOR_PREFIX}),
    ):
        s, e, indent = loc(lines)
        want = emit_region(contracts, indent, **kw)
        have = "\n".join(lines[s:e + 1])
        targets.append({"name": name, "s": s, "e": e,
                        "want": want, "have": have, "sync": have == want})

    drifted = [t for t in targets if not t["sync"]]
    for t in targets:
        print(f"  {t['name']:11} lines {t['s'] + 1}-{t['e'] + 1}  "
              f"{'IN SYNC' if t['sync'] else 'DRIFT'}")
    for t in drifted:
        hs = set(re.findall(r'"?\s*(SET [A-Z0-9_]+)', t["have"]))
        ws = set(re.findall(r'"?\s*(SET [A-Z0-9_]+)', t["want"]))
        for l in sorted(ws - hs):
            print(f"    [{t['name']}] + {l}")
        for l in sorted(hs - ws):
            print(f"    [{t['name']}] - {l}")
        if hs == ws:
            print(f"    [{t['name']}] option set unchanged; structure or guards differ")

    if not drifted:
        print("Both SetUsageText copies are IN SYNC with the contracts.")
        return 0
    if a.check:
        print("\n--check: a generated region does not match the contracts.")
        return 1
    if not a.write:
        print("\ndry run -- pass --write to rewrite")
        return 0

    for t in sorted(targets, key=lambda t: t["s"], reverse=True):
        if t["sync"]:
            continue
        lines = lines[:t["s"]] + t["want"].split("\n") + lines[t["e"] + 1:]
        print(f"rewrote {t['name']}")
    msg_path.write_text("\n".join(lines) + "\n", encoding="utf-8",
                        errors="surrogateescape")
    print(f"wrote {msg_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
