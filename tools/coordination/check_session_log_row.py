#!/usr/bin/env python3
"""Warn when a closeout lands without its dashboard Session Log row.

AIF-082, 6.13. The AIF-006 closeout obligation has five parts. Four of them have
mechanisms behind them and hold at 83 to 94 percent compliance. The fifth, the
Session Log row in `docs/ai-friendly/AI_FRIENDLY_DASHBOARD_V1.md`, has no
mechanism at all and holds at 33 percent -- measured 2026-07-31 across AIF-063
to AIF-082.

That is the cleanest available demonstration of the house thesis: **a rule with
no gate is obeyed a third of the time.** This is the gate.

Deliberately a WARNING, never a hard block. A commit that adds a closeout is
usually the right commit; refusing it would punish the sessions doing the most
work. The point is to make the omission visible at the moment it happens rather
than two months later in a probe.

Usage (PowerShell 7, from D:\\code\\ccode):

    python tools\\coordination\\check_session_log_row.py               # staged index
    python tools\\coordination\\check_session_log_row.py --range A..B  # a commit range
    python tools\\coordination\\check_session_log_row.py --audit       # whole tree

Exit codes: 0 nothing to warn about, 1 repo root not found, 3 warning issued.
Never returns 2; it does not hard-block.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

DASHBOARD = "docs/ai-friendly/AI_FRIENDLY_DASHBOARD_V1.md"
CLOSEOUT_RE = re.compile(r"docs/maintenance/SESSION_CLOSEOUT_[^/]+\.md$")
AIF_RE = re.compile(r"\bAIF-(\d{3})\b")


def repo_root() -> Path:
    here = Path(__file__).resolve()
    for candidate in [here.parent, *here.parents]:
        if (candidate / ".git").exists() and (candidate / "AI_README.md").exists():
            return candidate
    print("session-log-check: cannot locate repository root", file=sys.stderr)
    raise SystemExit(1)


def git_lines(root: Path, *args: str) -> list[str]:
    out = subprocess.run(
        ["git", *args], cwd=root, capture_output=True, text=True,
        encoding="utf-8", errors="replace", timeout=60, check=False
    )
    return out.stdout.split("\n") if out.returncode == 0 else []


def changed_closeouts(root: Path, rng: str | None, audit: bool) -> list[str]:
    if audit:
        folder = root / "docs" / "maintenance"
        return sorted(
            f"docs/maintenance/{p.name}"
            for p in folder.glob("SESSION_CLOSEOUT_*.md")
            if p.name != "SESSION_CLOSEOUT_TEMPLATE.md"
        )
    args = ["diff", "--cached", "--name-only"] if rng is None else ["diff", "--name-only", rng]
    return [
        line.strip()
        for line in git_lines(root, *args)
        if line.strip() and CLOSEOUT_RE.search(line.strip())
    ]


def lanes_with_evidence(root: Path) -> dict[str, list[str]]:
    """AIF ids that demonstrably happened, mapped to the evidence that proves it.

    CORRECTED 2026-07-31T21:00Z. The first version audited CLOSEOUTS and asked
    whether each had a Session Log row. That denominator is wrong, and it was
    wrong in the direction that flatters the checker: **a lane is not a
    closeout.** AIF-080 and AIF-081 each landed committed evidence -- a lane
    charter, and for 081 a separate runtime-proof document -- and neither wrote
    a `SESSION_CLOSEOUT_*` file. They were therefore invisible to this check,
    which reported "OK, every closeout in scope has a Session Log row" while the
    two lanes known to be missing rows sat outside its scope entirely.

    That is this project's signature defect (something reporting success without
    doing its job) inside the gate written to detect that defect. Found by a
    cold agent on its first task, not by the author.

    A lane counts as having happened if it holds a claim file AND at least one
    durable artifact. The claim ledger is the authoritative allocator, so it is
    the right spine to hang this on.
    """
    evidence: dict[str, list[str]] = {}
    claim_dir = root / "coordination" / "aif"
    if not claim_dir.is_dir():
        return evidence

    maint = root / "docs" / "maintenance"
    queue = root / "docs" / "ai-friendly" / "AI_INTERACTION_INTAKE_QUEUE_V1.md"
    queue_text = queue.read_text(encoding="utf-8", errors="replace") if queue.is_file() else ""

    docs: list[tuple[str, str]] = []
    if maint.is_dir():
        for p in maint.glob("*.md"):
            if p.name == "SESSION_CLOSEOUT_TEMPLATE.md":
                continue
            head = "\n".join(
                p.read_text(encoding="utf-8", errors="replace").splitlines()[:60]
            )
            docs.append((f"docs/maintenance/{p.name}", head))

    for claim in sorted(claim_dir.glob("AIF-*.claim")):
        aif = claim.stem
        found: list[str] = []
        for rel, head in docs:
            if aif in head:
                found.append(rel)
        if re.search(rf"^\|\s*{re.escape(aif)}\s*\|", queue_text, flags=re.MULTILINE):
            found.append("intake row")
        if found:
            evidence[aif] = found
    return evidence


def owning_lane(path: Path) -> str | None:
    """The lane this closeout is ABOUT, not every lane it mentions.

    First version of this checker matched any AIF number anywhere in the body.
    Closeouts cite neighbouring lanes constantly, so that test passed 79 of 83
    times while the 6.7 probe -- which asked the stricter question, does THIS
    lane have a row -- found 12 of 18 missing. The loose version was reporting
    compliance that does not exist. Caught by running it.

    The owning lane is named in the H1 title, by convention:
        # Session Closeout -- <topic> (AIF-082)
    Falling back to the first AIF in the envelope/header region if the title
    omits it.
    """
    if not path.is_file():
        return None
    text = path.read_text(encoding="utf-8", errors="replace")

    for line in text.splitlines():
        if line.startswith("# "):
            hit = AIF_RE.search(line)
            return f"AIF-{hit.group(1)}" if hit else None

    head = "\n".join(text.splitlines()[:40])
    hit = AIF_RE.search(head)
    return f"AIF-{hit.group(1)}" if hit else None


def main() -> int:
    parser = argparse.ArgumentParser(description="Warn on a closeout with no Session Log row.")
    parser.add_argument("--range", dest="rng", default=None, help="commit range, e.g. HEAD~3..HEAD")
    parser.add_argument("--audit", action="store_true", help="check every closeout in the tree")
    args = parser.parse_args()

    root = repo_root()
    dashboard_text = (root / DASHBOARD).read_text(encoding="utf-8", errors="replace") \
        if (root / DASHBOARD).is_file() else ""

    # AUDIT walks LANES, not closeouts. See lanes_with_evidence() for why the
    # original denominator was wrong and what it hid.
    if args.audit:
        lanes = lanes_with_evidence(root)
        missing = {a: ev for a, ev in lanes.items() if a not in dashboard_text}
        print(f"session-log-check: {len(lanes)} lane(s) with committed evidence")
        if not missing:
            print("session-log-check: OK -- every such lane has a Session Log row")
            return 0
        pct = round(100 * (len(lanes) - len(missing)) / len(lanes))
        print(f"session-log-check: WARNING -- {len(missing)} lane(s) with NO Session Log row "
              f"({pct}% compliance)")
        for aif in sorted(missing):
            print(f"  {aif}  evidence: {', '.join(missing[aif][:3])}")
        print("")
        print(f"AIF-006 asks for a row in {DASHBOARD}.")
        print("Warning, not a block. Add the row, or say in the lane doc why none is owed.")
        return 3

    closeouts = changed_closeouts(root, args.rng, args.audit)
    if not closeouts:
        print("session-log-check: no closeouts in scope -- nothing to check")
        return 0

    findings: list[str] = []
    unattributed = 0
    for rel in closeouts:
        lane = owning_lane(root / rel)
        if lane is None:
            unattributed += 1
            continue
        if lane not in dashboard_text:
            findings.append(f"{rel}  ({lane})")

    print(f"session-log-check: inspected {len(closeouts)} closeout(s)")
    if unattributed:
        print(
            f"session-log-check: {unattributed} closeout(s) name no lane in their"
            " title -- not checkable, and arguably its own defect"
        )
    if not findings:
        print("session-log-check: OK -- every closeout in scope has a Session Log row")
        return 0

    print(f"session-log-check: WARNING -- {len(findings)} closeout(s) with no Session Log row")
    for item in findings:
        print(f"  {item}")
    print("")
    print(f"AIF-006 asks for a row in {DASHBOARD}.")
    print("Measured 2026-07-31: this obligation held at 33% while the four with")
    print("gates held at 83-94%. This is a warning, not a block -- add the row, or")
    print("state in the closeout why none is owed.")
    return 3


if __name__ == "__main__":
    raise SystemExit(main())
