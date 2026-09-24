#!/usr/bin/env python3
"""Generate the Tier 0 state projection for the AI Portal (AIF-082, 6.1).

Tier 0 answers "where are we" without prose. It is GENERATED, never authored,
so it cannot drift the way a hand-maintained pointer does.

Sections: tree state, declared target, newest closeout, staleness warnings,
claimed lanes, and -- added AIF-096 -- "Sessions, lineage, asides": live
check-ins (heartbeat older than STALE_MIN is marked reapable, so an abandoned
straggler is never shown plainly 'live'), plus each run's aside chain (its
ordered claims -- the horizontal structure of a session) with parent + born_utc
from the durable lineage ledger. This is the coordination identity model rising
into the generated middle tier: it is automatic, so it rises by REGENERATION,
never by hand -- the atomic doctrine over it rises to the Tier 1 seed instead.

Design constraints, from the lane charter:

  * Output must stay small (target under 4 KB).
  * Output must be a PERSISTED FILE, readable by a partner with no shell, no
    python and no engine -- see 6.10, "the entry path runs at the capability of
    the weakest admitted partner". This script produces that file; it is never
    a prerequisite for reading it.
  * It must carry a STALENESS WARNING. A file that should have changed and did
    not is invisible to a diff, which is how CURRENT_TARGET.md stayed wrong
    across two independent assessments.

Usage (PowerShell 7, from D:\\code\\ccode):

    python labtalk\\ai_portal\\generate_tier0_state.py            # print only
    python labtalk\\ai_portal\\generate_tier0_state.py --write    # write the file

Exit codes: 0 ok, 1 could not locate the repository root.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

OUTPUT_RELATIVE = Path("labtalk/ai_portal/TIER0_STATE.md")
SIZE_TARGET = 4096


def repo_root() -> Path:
    here = Path(__file__).resolve()
    for candidate in [here.parent, *here.parents]:
        if (candidate / ".git").exists() and (candidate / "AI_README.md").exists():
            return candidate
    print("tier0: cannot locate repository root", file=sys.stderr)
    raise SystemExit(1)


def git(root: Path, *args: str) -> str:
    """Run git, returning stripped stdout. Empty string on any failure.

    Never raises. A sandbox or a git-less environment degrades to 'unknown'
    rather than failing the projection.
    """
    try:
        out = subprocess.run(
            ["git", *args],
            cwd=root,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=30,
            check=False,
        )
        return out.stdout.strip() if out.returncode == 0 else ""
    except (OSError, subprocess.SubprocessError):
        return ""


def claimed_lanes(root: Path) -> list[tuple[str, str, str]]:
    """Return (aif, lane, member) for each claim file, newest number first."""
    rows: list[tuple[str, str, str]] = []
    claim_dir = root / "coordination" / "aif"
    if not claim_dir.is_dir():
        return rows
    for path in sorted(claim_dir.glob("AIF-*.claim"), reverse=True):
        text = path.read_text(encoding="utf-8", errors="replace")
        fields = dict(
            re.findall(r"^(\w+)\s*:\s*(.+?)\s*$", text, flags=re.MULTILINE)
        )
        rows.append(
            (
                fields.get("aif", path.stem),
                fields.get("lane", "?"),
                fields.get("member", "?"),
            )
        )
    return rows


def intake_numbers(root: Path) -> set[str]:
    queue = root / "docs" / "ai-friendly" / "AI_INTERACTION_INTAKE_QUEUE_V1.md"
    if not queue.is_file():
        return set()
    text = queue.read_text(encoding="utf-8", errors="replace")
    return set(re.findall(r"^\|\s*(AIF-\d+)\s*\|", text, flags=re.MULTILINE))


def newest_closeout(root: Path) -> Path | None:
    folder = root / "docs" / "maintenance"
    if not folder.is_dir():
        return None
    dated = []
    for path in folder.glob("SESSION_CLOSEOUT_*.md"):
        match = re.search(r"(\d{4}-\d{2}-\d{2})\.md$", path.name)
        if match:
            dated.append((match.group(1), path))
    if not dated:
        return None
    return max(dated)[1]


def untracked_closeouts(root: Path, head: str) -> list[str]:
    """Names of SESSION_CLOSEOUT_*.md on disk that git does not track, newest first.

    Empty when git is unavailable (head == 'unknown'): not knowing is reported by
    the unmeasured-inputs warning, not by pretending every file is a widow.
    """
    folder = root / "docs" / "maintenance"
    if head == "unknown" or not folder.is_dir():
        return []
    tracked = set(git(root, "ls-files", "--", "docs/maintenance/").splitlines())
    names = [p.name for p in folder.glob("SESSION_CLOSEOUT_*.md")
             if f"docs/maintenance/{p.name}" not in tracked]
    def by_date(name: str) -> tuple[str, str]:
        match = re.search(r"(\d{4}-\d{2}-\d{2})\.md$", name)
        return (match.group(1) if match else "", name)
    return sorted(names, key=by_date, reverse=True)


def declared_target(root: Path) -> tuple[str, str]:
    """Return (heading, updated) from CURRENT_TARGET.md's first live section."""
    path = root / "docs" / "agents" / "CURRENT_TARGET.md"
    if not path.is_file():
        return ("unknown -- CURRENT_TARGET.md not found", "unknown")
    text = path.read_text(encoding="utf-8", errors="replace")
    updated = "unknown"
    # The file's header is an INDENTED key block (`    updated_utc : ...`), and
    # this used to match only an unindented `Updated_utc:` -- so from the day the
    # header took its current form, Tier 0 printed "updated : unknown" for a file
    # that carries its stamp on line 4. Measured 2026-09-23. Accept both forms.
    stamp = re.search(r"^\s*updated_utc\s*:\s*(.+?)\.?\s*$", text,
                      flags=re.MULTILINE | re.IGNORECASE)
    if stamp:
        updated = stamp.group(1)
    else:
        stamp = re.search(r"^\s*updated\s*:\s*(.+?)\.?\s*$", text,
                          flags=re.MULTILINE | re.IGNORECASE)
        if stamp:
            updated = stamp.group(1) + " (bare date -- see 6.5e)"
    heading = re.search(r"^##\s+(.+?)\s*$", text, flags=re.MULTILINE)
    return (heading.group(1) if heading else "unknown", updated)


STALE_MIN = 240  # heartbeat older than this (minutes) is reapable, per the coordinator


def _age_min(stamp: str, now_dt: datetime) -> float | None:
    """Minutes since an ISO '...Z' heartbeat, or None if it will not parse."""
    try:
        t = datetime.strptime(stamp.strip(), "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except (ValueError, AttributeError):
        return None
    return (now_dt - t).total_seconds() / 60.0


def active_sessions(root: Path, now_dt: datetime) -> list[tuple[str, str, bool]]:
    """(run, member, stale) for each non-closed presence file. stale = heartbeat older
    than STALE_MIN (reapable) or unparseable; marking an abandoned straggler plainly
    'live' would be the false-liveness Tier 0 exists to prevent. Transient: this is
    empty between sessions -- correct, not a gap."""
    out: list[tuple[str, str, bool]] = []
    folder = root / "coordination" / "active_sessions"
    if not folder.is_dir():
        return out
    for path in sorted(folder.glob("*.yaml")):
        text = path.read_text(encoding="utf-8", errors="replace")
        if "status: closed" in text:
            continue
        fields = dict(re.findall(r"^(\w+)\s*:\s*(.+?)\s*$", text, flags=re.MULTILINE))
        age = _age_min(fields.get("heartbeat_utc", ""), now_dt)
        stale = age is None or age > STALE_MIN
        out.append((fields.get("run_id", path.stem), fields.get("member", "?"), stale))
    return out


def lineage_records(root: Path) -> dict[str, dict[str, str]]:
    """run -> {parent, born_utc, member} from the DURABLE lineage ledger (AIF-096).
    Unlike presence this survives checkout, so a closed run's origin + parent remain
    answerable from HEAD."""
    out: dict[str, dict[str, str]] = {}
    folder = root / "coordination" / "lineage"
    if not folder.is_dir():
        return out
    for path in folder.glob("*.yaml"):
        fields = dict(
            re.findall(r"^(\w+)\s*:\s*(.+?)\s*$",
                       path.read_text(encoding="utf-8", errors="replace"),
                       flags=re.MULTILINE)
        )
        run = fields.get("run_id", path.stem)
        out[run] = {
            "parent": fields.get("parent", "none"),
            "born_utc": fields.get("born_utc", "unknown"),
            "member": fields.get("member", "?"),
        }
    return out


def run_asides(root: Path) -> list[tuple[str, str, list[str]]]:
    """(run, member, [AIF-nnn ascending]) newest-run-first. A run's aside chain is the
    ordered sequence of lane numbers it claimed -- the horizontal structure of a session,
    read straight off the durable claim ledger."""
    by_run: dict[str, list[str]] = {}
    member_of: dict[str, str] = {}
    claim_dir = root / "coordination" / "aif"
    if not claim_dir.is_dir():
        return []
    for path in sorted(claim_dir.glob("AIF-*.claim")):
        fields = dict(
            re.findall(r"^(\w+)\s*:\s*(.+?)\s*$",
                       path.read_text(encoding="utf-8", errors="replace"),
                       flags=re.MULTILINE)
        )
        run = fields.get("run_id", "?")
        member_of[run] = fields.get("member", "?")
        by_run.setdefault(run, []).append(fields.get("aif", path.stem))
    chains = [(run, member_of.get(run, "?"), sorted(aifs)) for run, aifs in by_run.items()]
    chains.sort(key=lambda rc: max(rc[2]) if rc[2] else "", reverse=True)
    return chains


def render(root: Path) -> str:
    now_dt = datetime.now(timezone.utc)
    now = now_dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    branch = git(root, "rev-parse", "--abbrev-ref", "HEAD") or "unknown"
    head = git(root, "rev-parse", "--short", "HEAD") or "unknown"
    head_date = git(root, "log", "-1", "--format=%ad", "--date=short") or "unknown"
    upstream = git(root, "rev-parse", "--short", "@{u}") or "unknown"
    ahead = git(root, "rev-list", "--count", "@{u}..HEAD") or "?"

    claims = claimed_lanes(root)
    rows = intake_numbers(root)
    unregistered = [aif for aif, _, _ in claims if aif not in rows]

    closeout = newest_closeout(root)
    closeout_name = closeout.name if closeout else "none found"
    closeout_behind = "?"
    closeout_uncommitted = False
    if closeout is not None:
        rel = closeout.relative_to(root).as_posix()
        last = git(root, "log", "-1", "--format=%h", "--", rel)
        if last:
            count = git(root, "rev-list", "--count", f"{last}..HEAD")
            closeout_behind = count or "?"
        elif head != "unknown":
            # git answered and no commit touches the file: it is on disk only.
            closeout_uncommitted = True
            closeout_behind = "not committed"

    target, target_updated = declared_target(root)

    lines: list[str] = []
    add = lines.append
    add("# Tier 0 -- generated state projection")
    add("")
    add("    GENERATED FILE. Do not edit; edits are overwritten.")
    add("    generator   : labtalk/ai_portal/generate_tier0_state.py")
    add(f"    generated_utc : {now}")
    add("    lane        : AIF-082 (6.1)")
    add("")
    add("Read this before acting. It is the only current-state source that")
    add("cannot drift, because nothing here is written by hand.")
    add("")
    add("## Tree")
    add("")
    add(f"    branch        : {branch}")
    add(f"    HEAD          : {head}  ({head_date})")
    add(f"    upstream      : {upstream}")
    add(f"    unpushed      : {ahead} commit(s) ahead of upstream")
    add("")
    add("## Declared target")
    add("")
    add(f"    updated       : {target_updated}")
    add(f"    section       : {target}")
    add("")
    add("## Newest closeout")
    add("")
    add(f"    file          : {closeout_name}")
    add(f"    commits behind HEAD : {closeout_behind}")
    add("")

    warnings: list[str] = []
    # AN INPUT THAT COULD NOT BE MEASURED IS A WARNING, NEVER SILENCE.
    # Before 2026-09-23 every check below skipped its "?" / "unknown" case, so a
    # projection whose inputs had failed printed "Staleness warnings: none" --
    # the one sentence in this file a reader acts on, asserting health it had not
    # measured. Found by a 43-day re-entry (proof.ai_portal.reentry_43day_20260923,
    # P1): "commits behind HEAD : ?" and "updated : unknown" beside "none".
    unmeasured = []
    for label, value in (("branch", branch), ("HEAD", head), ("upstream", upstream),
                         ("unpushed count", ahead), ("declared target stamp", target_updated),
                         ("newest-closeout distance", closeout_behind)):
        if value in ("?", "unknown") or value.startswith("unknown"):
            unmeasured.append(label)
    if closeout_uncommitted:
        warnings.append(
            f"The newest closeout by date, {closeout_name}, is on disk but in no "
            "commit. A clone cannot see it; whoever wrote it has not landed it."
        )
    widowed = untracked_closeouts(root, head)
    others = [name for name in widowed if name != closeout_name]
    if others:
        warnings.append(
            "Closeout(s) on disk but not tracked -- a session's record that never "
            "landed: " + ", ".join(others[:4])
            + (f" (+{len(others) - 4} more)" if len(others) > 4 else "") + "."
        )
    if unmeasured:
        warnings.append(
            "Could not measure: " + ", ".join(unmeasured) + ". This projection is "
            "INCOMPLETE; do not read the absence of other warnings as health."
        )
    if closeout_behind not in ("?", "0", "not committed"):
        warnings.append(
            f"The newest closeout is {closeout_behind} commit(s) behind HEAD. "
            "Work has landed that no closeout describes; read `git log` as well."
        )
    if unregistered:
        warnings.append(
            "Claim(s) with no intake row, so they read as ABANDONED from HEAD: "
            + ", ".join(sorted(unregistered))
            + ". Same shape as AIF-062/078/080."
        )
    if ahead not in ("?", "0"):
        warnings.append(f"{ahead} commit(s) are unpushed and invisible to a clone.")
    if "bare date" in target_updated:
        warnings.append(
            "CURRENT_TARGET.md carries a bare date, not a UTC timestamp (6.5e)."
        )

    add("## Staleness warnings")
    add("")
    if warnings:
        for item in warnings:
            add(f"- {item}")
    else:
        add("- none")
    add("")

    add("## Claimed lanes (newest first)")
    add("")
    add("| AIF | lane | steward | intake row |")
    add("| --- | --- | --- | --- |")
    for aif, lane, member in claims[:12]:
        mark = "yes" if aif in rows else "**MISSING**"
        add(f"| {aif} | {lane} | {member} | {mark} |")
    if len(claims) > 12:
        add(f"| ... | {len(claims) - 12} older claims omitted | | |")
    add("")

    add("## Sessions, lineage, asides")
    add("")
    live = active_sessions(root, now_dt)
    if live:
        for run, member, stale in live:
            tag = "  [stale, reapable]" if stale else ""
            add(f"    live   : {run}  ({member}){tag}")
    else:
        add("    live   : none checked in")
    add("")
    lin = lineage_records(root)
    asides = run_asides(root)
    add("Aside chains -- a run's claims in order (its horizontal structure);")
    add("parent + born_utc from the durable lineage ledger, '-' until a run wakes.")
    add("")
    add("| run | member | parent | born_utc | asides |")
    add("| --- | --- | --- | --- | --- |")
    for run, member, chain in asides[:8]:
        rec = lin.get(run, {})
        parent = rec.get("parent", "-")
        born = rec.get("born_utc", "-")
        chain_str = " -> ".join(chain[:6]) + (" ..." if len(chain) > 6 else "")
        add(f"| {run} | {member} | {parent} | {born} | {chain_str} |")
    if len(asides) > 8:
        add(f"| ... | | | | {len(asides) - 8} older run(s) omitted |")
    add("")

    add("Perishable detail lives in the artifacts these point at. Do not")
    add("restate anything above; regenerate it.")
    add("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate the Tier 0 state projection.")
    parser.add_argument("--write", action="store_true", help="write the file")
    args = parser.parse_args()

    root = repo_root()
    body = render(root)
    size = len(body.encode("utf-8"))

    if args.write:
        target = root / OUTPUT_RELATIVE
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(body, encoding="utf-8", newline="\n")
        print(f"tier0: wrote {OUTPUT_RELATIVE.as_posix()}  {size} B")
    else:
        print(body)
        print(f"--- tier0: {size} B (target under {SIZE_TARGET})", file=sys.stderr)

    if size > SIZE_TARGET:
        print(
            f"tier0: WARNING {size} B exceeds the {SIZE_TARGET} B target",
            file=sys.stderr,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
