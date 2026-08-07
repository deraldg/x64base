#!/usr/bin/env python3
"""Derive MANIFEST.txt -- a publication receipt for the public snapshot.

AIF-090. `MANIFEST.txt` is on the `PROMOTE.manifest` allow-list, so it publishes
to the public repository root where GitHub displays it prominently -- but it had
no source in `development` and its content was an internal patch-drop note
("DotTalk++ X64 runtime field-length fix drop"). It was orphaned AND wrong.

WHAT THIS FILE ANSWERS THAT NOTHING ELSE ON `main` DOES: "what am I looking at,
and how stale is it?" `README.md` describes the project and `RELEASE_NOTES.md`
lists what a release contains, but neither states the provenance of the snapshot
in front of you. A cold outside agent measured exactly this gap on 2026-08-06:
it could not determine how far `main` trailed `development` and had to guess.

EVERY FIGURE HERE IS MEASURED, NONE ASSERTED. Command and function counts come
from the engine's own metadata tables via `tools/fullstack_docs/dbfread.py`; the
published inventory comes from `PROMOTE.manifest`; provenance comes from git.
That is the same discipline as `labtalk/ai_portal/TIER0_STATE.md`: generated, so
it cannot drift the way a hand-maintained file does.

    python tools/staging/generate_public_manifest.py           # report to stdout
    python tools/staging/generate_public_manifest.py --write    # write MANIFEST.txt
    python tools/staging/generate_public_manifest.py --check    # drift gate

Exit codes: 0 ok, 1 cannot read a required input, 2 --check found drift.

RUNS ON D: ONLY. The output is allow-listed, so the staging overlay carries it.
Never run this against, or write into, the staging tree: staging is a build
output regenerated from a clean `main` clone plus the manifest overlay, and
hand-writing there manufactures the dirty state that design exists to prevent.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "fullstack_docs"))
try:
    import dbfread  # stdlib-only reader, reused rather than reimplemented
except ImportError:  # pragma: no cover
    dbfread = None

MANIFEST = "PROMOTE.manifest"
OUTPUT = "MANIFEST.txt"
METADATA = "dottalkpp/data/metadata"

# Tables whose live row count is a meaningful public figure. Name -> label.
# Add a row here and it appears; nothing else needs changing.
SURFACE_TABLES = [
    ("SYSCMD", "commands registered"),
    ("SYSFUNC", "functions registered"),
    ("SYSARGS", "documented arguments"),
    ("SYSHELP", "help text entries"),
    ("SYSENTVAR", "entity variables"),
    ("SYSFLDDIC", "field dictionary rows"),
]


def repo_root() -> Path:
    here = Path(__file__).resolve()
    for c in [here.parent, *here.parents]:
        if (c / ".git").exists() and (c / "AI_README.md").exists():
            return c
    print("generate-public-manifest: cannot locate repository root", file=sys.stderr)
    raise SystemExit(1)


def git(root: Path, *args: str) -> str:
    """Read-only git. GIT_OPTIONAL_LOCKS=0 so this never takes .git/index.lock.

    Returns "not_determined" rather than guessing or crashing: a manifest that
    invents its own provenance is worse than one that admits it lacks it.
    """
    try:
        out = subprocess.check_output(
            ["git", "--no-optional-locks", "-C", str(root), *args],
            text=True, stderr=subprocess.DEVNULL, env={"GIT_OPTIONAL_LOCKS": "0",
                                                       "PATH": _path()},
        )
        return out.strip() or "not_determined"
    except Exception:
        return "not_determined"


def _path() -> str:
    import os
    return os.environ.get("PATH", "")


def allow_list(root: Path) -> tuple[list[str], int]:
    """Glob patterns from PROMOTE.manifest, and the count of commentary lines.

    The manifest is an allow-list: non-blank, non-comment lines are globs. The
    commentary is deliberately large and is NOT parsed as rules.
    """
    p = root / MANIFEST
    if not p.is_file():
        print(f"generate-public-manifest: {MANIFEST} not found", file=sys.stderr)
        raise SystemExit(1)
    globs, comments = [], 0
    for raw in p.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("#"):
            comments += 1
            continue
        globs.append(line)
    return globs, comments


def published_count(root: Path, globs: list[str]) -> tuple[int, int]:
    """Files on disk matched by the allow-list, and patterns that match nothing.

    A pattern matching nothing is a real signal -- it is how `CONTRIBUTING.md`
    sat allow-listed with no source for months -- so it is counted and shown,
    not silently dropped.
    """
    # EXCLUDE THE RECEIPT ITSELF. MANIFEST.txt is on the allow-list, so counting
    # it makes the figure describe a tree that contains this file -- and writing
    # the file then changes that figure, so --check fails immediately after
    # --write and only converges on a second run. A generated artifact must be a
    # FIXED POINT of its own generator. Caught by fixture, 2026-08-06: T2
    # (write-then-check) failed, which is why write-then-check is a fixture and
    # not an assumption.
    seen: set[Path] = set()
    empty = 0
    out = (root / OUTPUT).resolve()
    for g in globs:
        hits = [q for q in _match(root, g) if q.is_file() and q.resolve() != out]
        # The receipt is allow-listed but must not be counted as missing merely
        # because it is excluded from its own inventory.
        if not hits and Path(g).name != OUTPUT:
            empty += 1
        seen.update(hits)
    return len(seen), empty


def _match(root: Path, pattern: str):
    """Glob a PROMOTE.manifest pattern, correcting for `dir/**` semantics.

    `Path.glob("a/**")` yields DIRECTORIES, not files -- so every recursive
    manifest pattern silently matched nothing and the first version of this tool
    was about to report 29 of 80 allow-list patterns as broken. They were not:
    `dottalkpp/data/dbf/x64` alone holds 46 files. Measured on Python 3.10 and
    3.12; the trap is the same on both.

    Caught 2026-08-06 by checking a suspicious number against the filesystem
    before publishing it, which is the only reason it is not in the record as a
    finding about the repository.
    """
    hits = list(root.glob(pattern))
    if pattern.endswith("/**"):
        hits += list(root.glob(pattern + "/*"))
    return hits


def surface(root: Path) -> list[tuple[str, str, object]]:
    """Live row counts from the engine's own metadata tables."""
    rows = []
    for name, label in SURFACE_TABLES:
        path = root / METADATA / f"{name}.dbf"
        if dbfread is None:
            rows.append((name, label, "reader_unavailable"))
            continue
        if not path.is_file():
            rows.append((name, label, "absent"))
            continue
        try:
            t = dbfread.read(path)
            rows.append((name, label, t.live))
        except Exception as exc:  # noqa: BLE001 - report, never guess
            rows.append((name, label, f"unreadable: {type(exc).__name__}"))
    return rows


def render(root: Path, *, stamped: bool) -> str:
    globs, comments = allow_list(root)
    files, empty = published_count(root, globs)
    branch = git(root, "rev-parse", "--abbrev-ref", "HEAD")
    commit = git(root, "rev-parse", "HEAD")
    short = commit[:9] if commit != "not_determined" else commit
    when = (datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            if stamped else "<generated at promotion time>")

    L = []
    a = L.append
    a("x64base -- public snapshot manifest")
    a("=" * 62)
    a("")
    a("GENERATED FILE. Do not edit by hand; your edit will be overwritten.")
    a("Regenerate from the development tree with:")
    a("")
    a("    python tools/staging/generate_public_manifest.py --write")
    a("")
    a("Every figure below is measured from the tree and from the engine's own")
    a("metadata tables at generation time. None is hand-maintained.")
    a("")
    a("Provenance")
    a("-" * 62)
    a(f"  promoted from branch : {branch}")
    a(f"  source commit        : {commit}")
    a(f"  short commit         : {short}")
    a(f"  generated (UTC)      : {when}")
    a("")
    a("  This snapshot is a PROJECTION of the development tree at the commit")
    a("  above, filtered through PROMOTE.manifest. It is not the whole tree.")
    a("  The `development` branch is also published on GitHub and moves ahead")
    a("  of this snapshot; see CONTRIBUTING.md for which branch to baseline on.")
    a("")
    a("Published inventory")
    a("-" * 62)
    a(f"  allow-list patterns  : {len(globs)}")
    a(f"  files matched on disk: {files}")
    a(f"  patterns matching 0  : {empty}")
    a(f"  manifest commentary  : {comments} lines")
    a("")
    a("  A pattern matching zero files means the allow-list promises something")
    a("  the development tree does not have. That is a defect, not a rounding")
    a("  error, and it is shown here so it cannot hide.")
    a("")
    a("Command and metadata surface")
    a("-" * 62)
    for name, label, value in surface(root):
        a(f"  {name:<10} {str(value):>8}  {label}")
    a("")
    a("  Read live from dottalkpp/data/metadata/*.dbf. These are registration")
    a("  counts, not proof of behavior: a registered command is source-evidenced")
    a("  until a runtime proof exists for it. See CONTRIBUTING.md, Reporting")
    a("  evidence.")
    a("")
    return "\n".join(L) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description="Derive the public MANIFEST.txt.")
    ap.add_argument("--write", action="store_true", help="write MANIFEST.txt")
    ap.add_argument("--check", action="store_true",
                    help="fail if MANIFEST.txt differs from a fresh derivation")
    args = ap.parse_args()
    root = repo_root()

    if args.check:
        # Compare UNSTAMPED so a timestamp difference is never mistaken for
        # content drift. The gate must fail on substance only.
        fresh = render(root, stamped=False)
        target = root / OUTPUT
        if not target.is_file():
            print(f"generate-public-manifest: FAIL -- {OUTPUT} absent; run --write",
                  file=sys.stderr)
            return 2
        have = target.read_text(encoding="utf-8", errors="replace")
        have_cmp = _strip_stamp(have)
        if have_cmp == _strip_stamp(fresh):
            print("generate-public-manifest: PASS -- MANIFEST.txt matches the tree")
            _report_lag(root, have)
            return 0
        print("generate-public-manifest: FAIL -- MANIFEST.txt does not match the "
              "tree it describes. Regenerate with --write.", file=sys.stderr)
        return 2

    text = render(root, stamped=True)
    if args.write:
        (root / OUTPUT).write_text(text, encoding="utf-8", newline="\n")
        print(f"generate-public-manifest: wrote {OUTPUT} ({len(text)} B)")
        return 0
    sys.stdout.write(text)
    return 0


# Lines that carry WHEN and FROM WHERE the receipt was cut. `--check` must not
# compare these.
#
# WHY. The receipt is regenerated at PROMOTION time, not on every commit, so its
# provenance is expected to trail HEAD between promotions -- that lag is the
# information it exists to publish. Comparing it would turn this gate red on
# every single commit, and a permanently red gate is switched off within a day.
# `--check` therefore asks one question only: DO THE MEASURED FIGURES STILL
# DESCRIBE THE TREE. Staleness of provenance is reported, never failed.
#
# Caught 2026-08-07, the first time the gate ran after an unrelated commit: the
# inventory was identical (80/828/0) and it failed anyway.
PROVENANCE_PREFIXES = (
    "generated (UTC)",
    "source commit",
    "short commit",
    "promoted from branch",
)


def _report_lag(root: Path, have: str) -> None:
    """Say how far the receipt's provenance trails HEAD. Informational only.

    This is the number an outside reader most wants and cannot otherwise get:
    a cold agent measured exactly this gap on 2026-08-06 and had to guess.
    """
    stamped = ""
    for line in have.splitlines():
        s = line.strip()
        if s.startswith("source commit"):
            stamped = s.split(":", 1)[1].strip()
            break
    head = git(root, "rev-parse", "HEAD")
    if not stamped or head == "not_determined":
        return
    if stamped == head:
        print("  provenance: current with HEAD")
        return
    behind = git(root, "rev-list", "--count", f"{stamped}..{head}")
    n = behind if behind.isdigit() else "an unknown number of"
    print(f"  provenance: cut at {stamped[:9]}, HEAD is {head[:9]} "
          f"({n} commit(s) ahead)")
    print("  This lag is EXPECTED between promotions and is not a failure. "
          "Regenerate at promotion time so the published receipt names the "
          "commit actually being published.")


def _strip_stamp(text: str) -> str:
    """Drop provenance lines so --check compares substance only."""
    return "\n".join(
        l for l in text.splitlines()
        if not l.strip().startswith(PROVENANCE_PREFIXES)
    )


if __name__ == "__main__":
    sys.exit(main())
