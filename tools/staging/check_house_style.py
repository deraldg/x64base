#!/usr/bin/env python3
"""House style gate -- ASCII only in newly written documentation.

AIF-082, 6.5h. `CLAUDE.md` states the rule: no em-dashes in scripts or docs, use
`--` and `->`. It has no mechanism, and the portal that declares it is its
largest violator. Measured 2026-07-31:

    AI_PORTAL.md               87 non-ASCII
    CURRENT_TARGET_HISTORY.md  66
    AI_README.md                6

That is the AIF-079 declared-capability class applied to prose: the rule exists,
the enforcement does not. And 6.7 measured what happens to an unenforced
obligation -- 33 percent compliance, against 83 to 94 for the four that have
gates.

THE DESIGN POINT: this checks **added lines only**. The historical backlog never
blocks anyone, and new violations become impossible. A gate that fails on day one
because of somebody else's decade of text is a gate that gets bypassed, and a
bypassed gate is worse than none because it looks like protection.

Hard-blocks rather than warns. Replacing an em-dash with `--` costs seconds, and
6.7 measured that warnings do not change behaviour.

Usage (PowerShell 7, from D:\\code\\ccode):

    python tools\\staging\\check_house_style.py            # staged index (the gate)
    python tools\\staging\\check_house_style.py --range A..B
    python tools\\staging\\check_house_style.py --audit    # whole-tree backlog, never fails

Exit codes: 0 clean, 1 repo root not found, 2 violations in added lines.
`--audit` always exits 0; it reports, it does not judge.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

# Characters that most often sneak in, named so the message can teach the fix.
NAMED = {
    "\u2014": ("em-dash", "--"),
    "\u2013": ("en-dash", "--"),
    "\u2018": ("left single quote", "'"),
    "\u2019": ("right single quote", "'"),
    "\u201c": ("left double quote", '"'),
    "\u201d": ("right double quote", '"'),
    "\u2192": ("right arrow", "->"),
    "\u2190": ("left arrow", "<-"),
    "\u2194": ("two-way arrow", "<->"),
    "\u21d2": ("double arrow", "=>"),
    "\u00d7": ("multiplication sign", "x"),
    "\u2260": ("not-equal", "!="),
    "\u2265": ("greater-or-equal", ">="),
    "\u2264": ("less-or-equal", "<="),
    "\u25b6": ("play triangle", "removed"),
}

CHECKED_SUFFIXES = (".md",)


def repo_root() -> Path:
    here = Path(__file__).resolve()
    for candidate in [here.parent, *here.parents]:
        if (candidate / ".git").exists() and (candidate / "AI_README.md").exists():
            return candidate
    print("house-style: cannot locate repository root", file=sys.stderr)
    raise SystemExit(1)


def offenders(text: str) -> list[str]:
    """Describe every non-ASCII character in a line, teaching the replacement."""
    seen: dict[str, str] = {}
    for ch in text:
        if ord(ch) < 128 or ch in seen:
            continue
        if ch in NAMED:
            name, fix = NAMED[ch]
            seen[ch] = f"{name} -> use `{fix}`"
        else:
            seen[ch] = f"U+{ord(ch):04X} -> use an ASCII equivalent"
    return list(seen.values())


# A markdown table cell is separated by a SPACED pipe; inline content is not.
# `| AIF-121 | ... [IN <n>|FREE] ... |` -- the two outer pipes are separators and
# the one inside the brackets is BNF alternation that GFM still reads as a cell
# boundary, so the row renders with extra columns and its Notes cell is cut in
# three. Measured 2026-08-25 across the AIF intake register: 8 rows, 20 such
# pipes, ZERO false positives -- every hit was real inline content (BNF
# alternation, `DOT|PRINT`-style catalog keys, `CSV|PIPE|SDF` format lists).
#
# The fix is `\|`, which renders as a literal pipe and keeps the cell intact.
INLINE_PIPE = re.compile(r"(?<!\\)(?<=\S)\|(?=\S)")


def table_pipe_offenders(text: str) -> int:
    """Unescaped, unspaced pipes in what looks like a markdown table row."""
    line = text.rstrip()
    if not (line.startswith("| ") and line.endswith("|")):
        return 0
    return len(INLINE_PIPE.findall(line))


def added_lines(root: Path, rng: str | None) -> list[tuple[str, int, str]]:
    """(path, line-number, text) for every ADDED line in a checked file."""
    args = ["diff", "--cached", "-U0"] if rng is None else ["diff", "-U0", rng]
    out = subprocess.run(
        ["git", *args, "--"] + [f"*{s}" for s in CHECKED_SUFFIXES],
        cwd=root, capture_output=True, text=True,
        encoding="utf-8", errors="replace", timeout=60, check=False,
    )
    if out.returncode != 0:
        return []

    results: list[tuple[str, int, str]] = []
    path, lineno = "", 0
    for raw in out.stdout.splitlines():
        if raw.startswith("+++ b/"):
            path = raw[6:]
        elif raw.startswith("@@"):
            try:
                seg = raw.split("+", 1)[1].split(" ", 1)[0]
                lineno = int(seg.split(",")[0])
            except (IndexError, ValueError):
                lineno = 0
        elif raw.startswith("+") and not raw.startswith("+++"):
            results.append((path, lineno, raw[1:]))
            lineno += 1
    return results


PRUNE = {
    ".git", ".venv", ".venv312", "node_modules", "out", "dist", ".next",
    "build", "build-wsl", "build-wsl-lean", "vcpkg_installed", "__pycache__",
    ".pytest_cache", ".tmp", "bin", "bin-wsl-lean",
}


# The governance surface -- the only place this rule is about. A whole-tree walk
# was tried and abandoned: measured 2026-07-31, the repository holds 2,000+
# directories and 3,700+ markdown files, and the walk had not finished in 25
# seconds. Auditing all of it would report mostly vendored and generated text
# that nobody authored and nobody should edit.
AUDIT_ROOTS = ("docs", "labtalk")


def walk_markdown(root: Path):
    """Yield .md paths across the governance surface, pruning generated trees."""
    import os

    for name in sorted(root.glob("*.md")):
        yield name

    for top in AUDIT_ROOTS:
        base = root / top
        if not base.is_dir():
            continue
        for dirpath, dirnames, filenames in os.walk(base):
            dirnames[:] = [
                d for d in dirnames
                if d not in PRUNE and not d.startswith("build-") and not d.startswith("_")
            ]
            for fname in filenames:
                if fname.endswith(".md"):
                    yield Path(dirpath) / fname


def audit(root: Path) -> int:
    rows: list[tuple[int, str]] = []
    for path in walk_markdown(root):
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        count = sum(1 for ch in text if ord(ch) >= 128)
        if count:
            rows.append((count, str(path.relative_to(root)).replace("\\", "/")))
    rows.sort(reverse=True)
    total = sum(c for c, _ in rows)
    print(f"house-style AUDIT: {len(rows)} file(s), {total} non-ASCII character(s)")
    for count, name in rows[:25]:
        print(f"  {count:6d}  {name}")
    if len(rows) > 25:
        print(f"  ... {len(rows) - 25} more file(s)")
    print("")
    print("Backlog only. The gate checks ADDED lines, so none of this blocks a commit.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="ASCII-only gate for new documentation.")
    parser.add_argument("--range", dest="rng", default=None, help="commit range, e.g. HEAD~1..HEAD")
    parser.add_argument("--audit", action="store_true", help="report the whole-tree backlog")
    args = parser.parse_args()

    root = repo_root()
    if args.audit:
        return audit(root)

    findings = [
        (path, lineno, line, offenders(line))
        for path, lineno, line in added_lines(root, args.rng)
        if any(ord(ch) >= 128 for ch in line)
    ]

    # ADVISORY, NOT A HARD BLOCK, AND THE ASYMMETRY IS DELIBERATE.
    #
    # The ASCII rule blocks because `--` is ALWAYS a safe substitution. This one
    # cannot be: inside a fenced code block a line may legitimately begin with
    # `|` -- sample gate output, an illustrated table -- and escaping there would
    # CORRUPT the sample. This checker reads a diff, which carries no fence
    # state, so it cannot tell a real table row from an illustrated one.
    #
    # Upgrade path, if the noise proves to be zero: read the whole staged file
    # and track ``` fences, then this can block like its neighbour.
    pipes = [
        (path, lineno, line, n)
        for path, lineno, line in added_lines(root, args.rng)
        if (n := table_pipe_offenders(line))
    ]
    if pipes:
        total = sum(n for _, _, _, n in pipes)
        print(f"house-style: advisory -- {total} unescaped inline pipe(s) in "
              f"{len(pipes)} added table row(s); each one splits its cell")
        for path, lineno, line, n in pipes[:10]:
            print(f"  {path}:{lineno}  ({n})")
            print(f"      {line.strip()[:96]}")
        print("  Escape them as \\| -- renders as a literal pipe, cell stays whole.")

    if not findings:
        print("house-style: PASS -- no non-ASCII in added documentation lines")
        return 0

    print(f"house-style: FAIL -- {len(findings)} added line(s) carry non-ASCII")
    for path, lineno, line, fixes in findings[:40]:
        print(f"  {path}:{lineno}")
        for fix in fixes:
            print(f"      {fix}")
        print(f"      | {line.strip()[:100]}")
    if len(findings) > 40:
        print(f"  ... {len(findings) - 40} more line(s)")
    print("")
    print("`CLAUDE.md` requires ASCII in scripts and docs: use `--` and `->`.")
    print("Only ADDED lines are checked, so the historical backlog is not your")
    print("problem -- these are lines this change introduces.")
    print("")
    print("There is a fixer (AIF-090). It carries an explicit mapping table and")
    print("REFUSES to write a file containing a codepoint it does not know, so")
    print("it cannot silently mangle anything:")
    print("")
    print("    python tools/staging/ascii_normalize.py FILE...          # dry run")
    print("    python tools/staging/ascii_normalize.py --apply FILE...  # rewrite")
    print("    python tools/staging/ascii_normalize.py --table          # mapping")
    print("")
    print("Note: staging a previously UNTRACKED file makes every one of its")
    print("lines an added line, so the whole file must be clean, not just your")
    print("edit. Or `git commit --no-verify` if you are deliberately importing")
    print("text.")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
