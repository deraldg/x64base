#!/usr/bin/env python3
"""check_version_coherence.py -- gate: the product version has exactly ONE home.

Why this exists (the gate is the memory, AIF-082). The version is declared by
`project(DotTalkpp VERSION x)` in the root CMakeLists.txt, which reaches every
target through dottalk_apply_common_settings -> dottalk_apply_version_metadata
as -DDOTTALKPP_VERSION. Measured 2026-08-21, that one fact was ALSO hand-typed
in five other places. What the two copies actually held, verbatim -- and note
that this gate must quote them to explain itself, which is why these two lines
carry the very exemption marker the gate documents:

    CMakeLists.txt project()      the authority      "0.6"  # version-literal-ok: the drift this gate exists to catch, quoted as evidence
    include/dottalk/version.hpp   #ifndef fallback   "0.6-dev"  # version-literal-ok: the drift this gate exists to catch, quoted as evidence
    tools/version_info.py         `fallback_version` default in THREE signatures

The header's copy had ALREADY DRIFTED from the authority. A build that lost the
-D would have shipped the fallback as though it were real. Nothing compared
them, which is exactly why bumping the version kept being forgotten: the
forgetting was designed in.

AIF-120 collapsed the copies rather than policing them -- version_info.py now
reads the authority, and the C++ fallback was changed to a value that CANNOT
pass for a version. So the invariant this gate enforces is not "the copies
agree", it is "there are no copies":

  1. the authority parses, and
  2. the C++ fallback is the unconfigured marker, not a plausible number, and
  3. no file that references DOTTALKPP_VERSION carries a quoted version literal.

SCOPE, STATED RATHER THAN IMPLIED: check 3 covers files that mention
DOTTALKPP_VERSION plus tools/version_info.py -- derived from who actually
touches the version, not a hand-kept list. A version literal invented somewhere
that references none of that is out of scope, and this gate will not see it.

Usage (PowerShell 7, from D:\\code\\ccode):

    $py12 = "D:\\code\\ccode\\.venv312\\Scripts\\python.exe"
    & $py12 tools\\staging\\check_version_coherence.py

Exit codes: 0 clean, 1 repo root not found, 2 violations (blocking).
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

PROJECT_VERSION_RE = re.compile(
    r"project\s*\([^)]*?\bVERSION\s+([0-9][0-9A-Za-z.\-+]*)", re.IGNORECASE | re.DOTALL)

# The C++ fallback must be this: a value no reader can mistake for a release.
UNCONFIGURED_MARKER = "0.0-unconfigured"
FALLBACK_RE = re.compile(r'#\s*define\s+DOTTALKPP_VERSION\s+"([^"]*)"')

# A quoted literal that could pass for a release: MAJOR.MINOR at minimum.
#
# The first cut of this pattern allowed zero dots, so it flagged "1", "0", "23"
# and "8051" -- 61 false positives on the first run, including a C++ standard
# list and an 8051 opcode table. A bare integer is not a version; requiring a
# dot is what makes the match mean something.
VERSION_LITERAL_RE = re.compile(
    r'"([0-9]+\.[0-9]+(?:\.[0-9]+){0,2}(?:[-+][0-9A-Za-z.]+)?)"')

# Values that are deliberately NOT versions and exist so an unconfigured build
# cannot ship a plausible one. Exempt by value, not by location.
DELIBERATE_NON_VERSIONS = ("0.0-unconfigured", "0.0-unresolved")

# Source and build files only. `.txt` is admitted ONLY as CMakeLists.txt: the
# tree also carries flattened source dumps (flattened_sources.txt,
# tests/combined_sources_*.txt) which are concatenations of everything and
# therefore mention DOTTALKPP_VERSION without declaring anything.
CODE_SUFFIXES = (".py", ".hpp", ".h", ".cpp", ".cc", ".cmake")
SKIP_DIRS = ("/.git/", "/build", "/node_modules/", "/src/AIPortal/", "/__pycache__/")


def repo_root() -> Path | None:
    here = Path(__file__).resolve()
    for candidate in (here.parent, *here.parents):
        if (candidate / ".git").exists():
            return candidate
    return None


def tracked_files(root: Path) -> list[Path]:
    try:
        out = subprocess.run(["git", "--no-optional-locks", "-C", str(root),
                              "ls-files"], capture_output=True, text=True, timeout=60)
    except Exception:
        return []
    if out.returncode != 0:
        return []
    files = []
    for name in out.stdout.splitlines():
        basename = name.rsplit("/", 1)[-1]
        if not (name.endswith(CODE_SUFFIXES) or basename == "CMakeLists.txt"):
            continue
        posix = "/" + name
        if any(skip in posix for skip in SKIP_DIRS):
            continue
        files.append(root / name)
    return files


def main() -> int:
    root = repo_root()
    if root is None:
        print("check-version-coherence: repo root not found")
        return 1

    problems: list[str] = []

    # --- 1. the authority ---------------------------------------------------
    cmakelists = root / "CMakeLists.txt"
    authority = ""
    try:
        match = PROJECT_VERSION_RE.search(
            cmakelists.read_text(encoding="utf-8", errors="replace"))
        authority = match.group(1) if match else ""
    except OSError:
        pass
    if not authority:
        problems.append(
            "no version authority: CMakeLists.txt has no parseable "
            "project(DotTalkpp VERSION x)")
    else:
        print("check-version-coherence: authority = %s  (CMakeLists.txt project())"
              % authority)

    # --- 2. the C++ fallback must not be able to pass for a release ---------
    header = root / "include" / "dottalk" / "version.hpp"
    try:
        found = FALLBACK_RE.search(header.read_text(encoding="utf-8", errors="replace"))
    except OSError:
        found = None
    if found is None:
        problems.append("include/dottalk/version.hpp: no DOTTALKPP_VERSION fallback found")
    elif found.group(1) != UNCONFIGURED_MARKER:
        problems.append(
            'include/dottalk/version.hpp: fallback is "%s"; it must be "%s" so an '
            "unconfigured build cannot ship a plausible version" % (found.group(1),
                                                                    UNCONFIGURED_MARKER))

    # --- 3. no second declaration anywhere that touches the version ---------
    interested: list[Path] = []
    for path in tracked_files(root):
        if path == cmakelists or path == header:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if "DOTTALKPP_VERSION" in text or path.name == "version_info.py":
            interested.append(path)

    for path in interested:
        text = path.read_text(encoding="utf-8", errors="replace")
        for lineno, line in enumerate(text.splitlines(), 1):
            if "version-literal-ok" in line:
                continue
            for hit in VERSION_LITERAL_RE.finditer(line):
                if hit.group(1) in DELIBERATE_NON_VERSIONS:
                    continue
                problems.append(
                    "%s:%d: version literal \"%s\" -- the version is declared once, in "
                    "CMakeLists.txt project(); read it, do not restate it"
                    % (path.relative_to(root).as_posix(), lineno, hit.group(1)))

    print("check-version-coherence: %d file(s) reference the version" % len(interested))

    if problems:
        print("\ncheck-version-coherence: FAIL -- %d problem(s)." % len(problems))
        for problem in problems:
            print("  " + problem)
        print("\nFix: bump project(DotTalkpp VERSION x) in CMakeLists.txt and let every")
        print("other reader derive from it. Append '# version-literal-ok: <reason>' to a")
        print("line only when a literal is deliberate and is not a declaration.")
        return 2

    print("check-version-coherence: OK -- one authority, no second declaration.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
