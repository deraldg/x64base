#!/usr/bin/env python3
"""check-soak-evidence -- a promotion must name the runs it stands on.

WHY THIS EXISTS. Promotion doctrine says a spec enters the default suite on TWO
GREEN RUNS ON A BUILD NOBODY CHANGED ANYTHING ON. Nothing checked it. On
2026-09-08 that rule came within one edit of being silently unmet: two green
VARCHARRESET runs were taken either side of a one-line string change, and only a
deliberately taken third run on an unchanged build made the soak real. Nothing in
the tree would have noticed, because the rule lived entirely in whoever was
promoting remembering to look.

WHAT IT CHECKS. When a spec's `in_default_suite` flag flips false -> true in the
staged src/cli/cmd_regression.cpp, coordination/SOAK_EVIDENCE.md must carry TWO
OR MORE rows for that spec whose BANNER strings are BYTE-IDENTICAL and whose
verdicts read PASS. The banner is the engine's own startup line -- version,
commit hash, dirty flag, build timestamp -- so two identical banners were the
same build of the same tree, and two different ones were not.

WHAT IT CANNOT DO, AND THE COMMENT IS HERE SO NOBODY READS MORE INTO A GREEN.
IT CANNOT PROVE A RUN HAPPENED. Captures live in gitignored tmp/, so this gate
never sees them; the rows are transcribed by a person. It converts "I remembered
to compare the build stamps" into a comparison the gate performs and cannot
forget. Transcribing a banner nobody observed is falsifying evidence, not
defeating a check, and no gate at this layer can tell those apart.

Exit codes: 0 clean, 2 hard-blocked, 4 usage/git error.
"""

import re
import subprocess
import sys

SPEC_FILE = "src/cli/cmd_regression.cpp"
EVIDENCE = "coordination/SOAK_EVIDENCE.md"
MIN_RUNS = 2


def git(args):
    out = subprocess.run(["git", "--no-optional-locks"] + args,
                         capture_output=True, text=True)
    if out.returncode != 0:
        return None
    return out.stdout


def staged_names():
    raw = git(["diff", "--cached", "--name-only", "--diff-filter=ACMR"])
    if raw is None:
        return None
    return [n.strip().replace("\\", "/") for n in raw.splitlines() if n.strip()]


# ---------------------------------------------------------------------------
# PARSING IS A PURE FUNCTION ON TEXT, deliberately: it takes no git and no
# filesystem, so it can be exercised directly against a file. A parser that can
# only be run by the gate that calls it is a parser nobody tests.
# ---------------------------------------------------------------------------
NAME_RE = re.compile(r'^\s*"([A-Z][A-Z0-9_]*)",\s*$')


def default_suite_flags(text):
    """Map spec name -> in_default_suite bool, read from the registry array.

    The entry shape is NAME, script, summary, in_default_suite, ... and the flag
    is the FIRST bare true/false after the three string literals. Comment lines
    and continuation strings are skipped rather than counted, because several
    entries carry a trailing `// PROMOTED ...` note on the flag's own line.
    """
    flags = {}
    lines = text.splitlines()
    for i, line in enumerate(lines):
        m = NAME_RE.match(line)
        if not m:
            continue
        name = m.group(1)
        # NO FIXED LOOKAHEAD WINDOW. The first version of this used 40 lines and
        # SILENTLY MISSED USE_AGAIN, whose summary is a multi-line concatenated
        # string literal running well past that. A parser that quietly drops one
        # entry is worse than one that fails, because the whole point of this
        # gate is to notice a flag it would then never have looked at. The scan
        # now ends at the NEXT entry, so entry length cannot defeat it.
        for j in range(i + 1, len(lines)):
            t = lines[j].strip()
            if not t or t.startswith("//"):
                continue
            if t.startswith('"'):          # script path or (multi-line) summary
                continue
            if t.startswith("true"):
                flags[name] = True
                break
            if t.startswith("false"):
                flags[name] = False
                break
            if NAME_RE.match(lines[j]) or t.startswith("}};"):
                break                      # next entry / array end: no flag found
    return flags


def evidence_rows(text):
    """Map spec -> list of (banner, verdict) from the evidence table."""
    rows = {}
    for line in text.splitlines():
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 3:
            continue
        spec = cells[0]
        if not re.fullmatch(r"[A-Z][A-Z0-9_]*", spec):
            continue                        # separator rows
        if spec == "SPEC" and cells[1].upper() == "BANNER":
            continue                        # the table header is not a spec
        rows.setdefault(spec, []).append((cells[1], cells[2]))
    return rows


def main(argv):
    names = staged_names()
    if names is None:
        print("check-soak-evidence: not a git worktree -- skipped")
        return 0
    if SPEC_FILE not in names:
        print("check-soak-evidence: no regression registry in scope -- "
              "nothing to check")
        return 0

    staged = git(["show", ":" + SPEC_FILE])
    head = git(["show", "HEAD:" + SPEC_FILE])
    if staged is None:
        print("check-soak-evidence: cannot read the staged registry",
              file=sys.stderr)
        return 4
    if head is None:
        head = ""                            # first commit: everything is new

    now = default_suite_flags(staged)
    before = default_suite_flags(head)

    promoted = sorted(n for n, v in now.items()
                      if v and not before.get(n, False))
    if not promoted:
        print("check-soak-evidence: no spec promoted in this change set -- "
              "nothing to check")
        return 0

    ev_text = git(["show", ":" + EVIDENCE])
    if ev_text is None:
        ev_text = git(["show", "HEAD:" + EVIDENCE]) or ""
    rows = evidence_rows(ev_text)

    bad = False
    for spec in promoted:
        got = rows.get(spec, [])
        passing = [r for r in got if "PASS" in r[1].upper()]
        banners = {r[0] for r in passing}
        print(f"check-soak-evidence: {spec} promoted -- "
              f"{len(passing)} passing row(s), "
              f"{len(banners)} distinct banner(s)")
        if len(passing) < MIN_RUNS:
            print(f"  BLOCKED -- {spec} needs at least {MIN_RUNS} PASS rows in "
                  f"{EVIDENCE} and has {len(passing)}.", file=sys.stderr)
            bad = True
        elif len(banners) != 1:
            print(f"  BLOCKED -- {spec}'s rows do not share one banner, so they "
                  f"were NOT run against the same build of the same tree:",
                  file=sys.stderr)
            for b in sorted(banners):
                print(f"      {b}", file=sys.stderr)
            bad = True

    if bad:
        print("\n  A promotion says the suite now checks something on every run. "
              "The soak is what makes that claim survive contact with a build "
              "nobody looked at. Take the runs, copy the banner OUT OF THE "
              "CAPTURE FILE, and record them.", file=sys.stderr)
        return 2

    print("check-soak-evidence: PASS -- every promoted spec names two or more "
          "PASS runs on one build.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
