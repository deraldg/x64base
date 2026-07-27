#!/usr/bin/env python3
"""
AIF-067 -- convert multi-word @dottalk.usage contracts to VOLUNTARY usage.

THE PROBLEM
    cmd_setcase.cpp and its siblings declare `command: SET CASE` in the
    @dottalk.usage dialect, because they predate @dottalk.subusage. The SET
    ladder in cmd_set.cpp now ALSO declares the same subcommand via parent:/sub:.
    So the SET family is described TWICE, in two vocabularies, feeding two tables
    -- and nine of them sit in the live SYSCMD as though they were top-level
    commands, which they are not.

THE DECISION (member.derald, 2026-07-27)
    Option A, with a qualification worth more than the option:

    > "go with A and/but keep the richer summary/usage/risks as VOLUNTARY usage,
    >  under the @dottalk.file first, so it collects correctly as a file."

    The ladder keeps the authoritative subcommand identity -- contract and
    dispatch stay in one diff hunk, which is why AIF-067 put it there. But the
    handler files' prose is BETTER than the ladder's, and deleting good
    documentation to satisfy a schema would be the tool wagging the author.

    So the block STAYS, demoted from an identity claim to a voluntary
    description:

        @dottalk.usage v1        ->  @dottalk.usage.voluntary v1
        command: SET CASE        ->  documents: SET CASE

    `documents:` says "this file implements that surface". `command:` says "I am
    that command". Only the second is an identity, and only the second is
    harvested into SYSCMD.

WHY THE ORDER MATTERS
    @dottalk.file comes first and stays first. The voluntary block sits beneath
    it, so the census collects the file as a FILE -- with its subsystem, layer
    and owner -- and reads the voluntary text as description hanging off that
    identity rather than as a competing one.

EFFECT
    - nine spurious SYSCMD rows stop being generated
    - CONTRACT_QA sees no multi-word command identity
    - not one sentence of authored documentation is lost
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

MARK = "// @dottalk.usage v1"
NEWMARK = "// @dottalk.usage.voluntary v1"
CMD_LINE = re.compile(r"^(\s*//\s*)command:\s*(.+?)\s*$")


def tracked(root: Path) -> list[str]:
    out = subprocess.check_output(
        ["git", "--no-optional-locks", "-C", str(root), "ls-files", "src"], text=True)
    return [p for p in out.split("\n") if p.endswith(".cpp")]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args()
    root = Path(a.root).resolve()

    changed = []
    for rel in tracked(root):
        p = root / rel
        try:
            text = p.read_text(encoding="utf-8", errors="surrogateescape")
        except OSError:
            continue
        if MARK not in text:
            continue

        lines = text.split("\n")
        out, i, hits = [], 0, []
        while i < len(lines):
            line = lines[i]
            if line.strip() != MARK.strip():
                out.append(line)
                i += 1
                continue
            # collect this block
            blk, j = [line], i + 1
            while j < len(lines) and lines[j].lstrip().startswith("//") \
                    and lines[j].strip() != MARK.strip():
                blk.append(lines[j])
                j += 1
            # multi-word command: ?  -> demote the whole block
            name = None
            for b in blk:
                m = CMD_LINE.match(b)
                if m and " " in m.group(2).strip():
                    name = m.group(2).strip()
                    break
            if name:
                hits.append(name)
                nb = []
                for b in blk:
                    if b.strip() == MARK.strip():
                        pre = b[: b.index("//")]
                        nb.append(b.replace(MARK.strip(), NEWMARK.strip()))
                        # State the legal standing IN the block. member.derald:
                        # "we treat it legally -- it is not under contract,
                        # voluntary." A contract BINDS: the system may be checked
                        # against it and drift is a defect. A voluntary block
                        # offers a description and promises nothing, so no guard
                        # may report it as non-compliant. Saying so here means a
                        # reader never has to infer it from the marker.
                        nb.append(pre + "// NOT UNDER CONTRACT -- voluntary "
                                        "description, offered not promised.")
                        nb.append(pre + "// Nothing verifies this block and "
                                        "nothing may fail because of it.")
                        nb.append(pre + "// The binding identity for this "
                                        "surface is the @dottalk.subusage")
                        nb.append(pre + "// contract on its ladder arm in "
                                        "src/cli/cmd_set.cpp.")
                        continue
                    m = CMD_LINE.match(b)
                    if m and " " in m.group(2).strip():
                        nb.append(f"{m.group(1)}documents: {m.group(2).strip()}")
                        continue
                    nb.append(b)
                out.extend(nb)
            else:
                out.extend(blk)
            i = j
        if hits:
            changed.append((rel, hits))
            if a.write:
                p.write_text("\n".join(out), encoding="utf-8",
                             errors="surrogateescape")

    print(f"files with a multi-word command identity: {len(changed)}")
    for rel, hits in changed:
        print(f"  {rel:44} {', '.join(hits)}")
    print("\nwrote changes" if a.write else "\ndry run -- pass --write to apply")
    return 0


if __name__ == "__main__":
    sys.exit(main())
