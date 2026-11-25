#!/usr/bin/env python3
"""Generate the Tier 0 state projection for the AI Portal (AIF-082, 6.1).

Tier 0 answers "where are we" without prose. It is GENERATED, never authored,
and the persisted snapshot can be checked against the current inputs.

Sections: tree state, declared target, handoff routing, staleness warnings,
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
    python labtalk\\ai_portal\\generate_tier0_state.py --check    # compare with file
    python labtalk\\ai_portal\\generate_tier0_state.py --lane AIF-NNN  # read-only handoff

Exit codes: 0 ok/current, 1 input could not be read, 2 invalid arguments,
3 stale, unavailable, or ambiguous.
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
GENERATED_UTC_PREFIX = "    generated_utc : "


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
    """Legacy date-only snapshot for global context; never selects a handoff."""
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


def utc_stamp(value) -> datetime | None:
    try:
        stamp = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return stamp.astimezone(timezone.utc) if stamp.tzinfo is not None else None
    except ValueError:
        return None


def lane_handoff(root: Path, lane: str) -> tuple[str, int]:
    """Resolve a claimed lane against its run records, without writing state."""
    import yaml

    module_root = str(Path(__file__).resolve().parents[2])
    if module_root not in sys.path:
        sys.path.insert(0, module_root)
    from tools.registries.registry_fragments import SPECS, read_fragments

    claim = root / "coordination" / "aif" / f"{lane}.claim"
    lines = [f"# {lane} handoff"]
    if not claim.is_file():
        return "\n".join(lines + ["No durable claim; no handoff selected."]), 3
    if not git(root, "rev-parse", "HEAD"):
        return "\n".join(lines + ["Git HEAD unavailable; visibility could not be measured."]), 1

    folder = root / "labtalk" / "registries"
    try:
        header, records = read_fragments(root, SPECS["ai_runs.yaml"])
        if header is None:
            records = yaml.safe_load((folder / "ai_runs.yaml").read_text(encoding="utf-8"))["runs"]
    except yaml.YAMLError as exc:
        raise ValueError(f"invalid run registry YAML: {exc}") from exc
    upstream = git(root, "rev-parse", "--verify", "@{u}")
    ranked = {}
    issues = set()
    legacy_unranked = set()
    for run in records:
        if lane not in (run.get("lanes") or []):
            continue
        if header is None:
            source = "labtalk/registries/ai_runs.yaml"
        else:
            source = f"labtalk/registries/runs.d/{run['run_id']}.yaml"
        for rel in run.get("closeouts") or []:
            path = root / rel
            relative = Path(rel)
            if (path.suffix != ".md" or not path.resolve().is_relative_to(root.resolve())
                    or relative.is_absolute() or relative.drive or ".." in relative.parts):
                raise ValueError(f"invalid closeout path in {source}: {rel}")
            rel = path.relative_to(root).as_posix()
            if not path.is_file():
                issues.add(f"absent from worktree: {rel}")
                continue
            head_blob = git(root, "rev-parse", "--verify", f"HEAD:{rel}")
            # The audit envelope is the timestamp authority. Older reports can
            # use a clearly labeled Git timestamp when that is all we have.
            body = path.read_text(encoding="utf-8")
            envelope = body.split("\n---\n", 1)[0][4:] if body.startswith("---\n") else ""
            try:
                data = yaml.safe_load(envelope) or {}
            except yaml.YAMLError as exc:
                raise ValueError(f"invalid closeout YAML in {rel}: {exc}") from exc
            audit = data.get("ai_report_audit", {}) if isinstance(data, dict) else {}
            recorded = audit.get("recorded_at_utc")
            stamp = utc_stamp(recorded)
            basis = "report recorded UTC"
            if recorded is None and head_blob:
                stamp = utc_stamp(git(root, "log", "-1", "--format=%cI", "--", rel))
                basis = "Git last-change UTC; legacy closeout has no recorded timestamp"
            if stamp is None:
                if recorded is None:
                    legacy_unranked.add(rel)
                else:
                    issues.add(f"invalid recorded UTC timestamp: {rel}")
                continue
            order = (recorded is not None, stamp)
            _, _, _, sources = ranked.setdefault(rel, (order, basis, head_blob, set()))
            sources.add(source)

    if ranked and not issues:
        newest = max(candidate[0] for candidate in ranked.values())
        winners = [rel for rel, candidate in ranked.items() if candidate[0] == newest]
        if len(winners) == 1 and (newest[0] or not legacy_unranked):
            rel = winners[0]
            (_, stamp), basis, head_blob, sources = ranked[rel]
            lines += [f"closeout: {rel}", f"timestamp: {stamp.isoformat()} ({basis})"]
            if not head_blob:
                lines.append("artifact: local-only; absent from HEAD")
            elif git(root, "hash-object", "--", rel) != head_blob:
                lines.append("artifact: committed at HEAD; worktree copy differs")
            else:
                lines.append("artifact: committed at HEAD")
            if upstream:
                upstream_blob = git(root, "rev-parse", "--verify", f"{upstream}:{rel}")
                lines.append("artifact at configured upstream: " + (
                    "absent" if not upstream_blob else
                    "matches HEAD" if upstream_blob == head_blob else "differs from HEAD"
                ))
            else:
                lines.append("artifact at configured upstream: unmeasured (no upstream ref)")
            for source in sorted(sources):
                binding = git(root, "rev-parse", "--verify", f"HEAD:{source}")
                local = git(root, "hash-object", "--", source)
                visibility = "matches HEAD" if binding and binding == local else "local-only binding"
                upstream_source = git(root, "rev-parse", "--verify", f"{upstream}:{source}") if upstream else ""
                if upstream:
                    visibility += "; upstream " + (
                        "absent" if not upstream_source else
                        "matches worktree" if upstream_source == local else "differs from worktree"
                    )
                lines.append(f"run record: {source} ({visibility})")
            for rel in sorted(legacy_unranked):
                lines.append(f"unranked legacy companion (no recorded or committed UTC): {rel}")
            return "\n".join(lines), 0
        if len(winners) > 1:
            issues.add("equally recent UTC records: " + ", ".join(sorted(winners)))
    issues.update(f"cannot order legacy closeout (no recorded or committed UTC): {rel}"
                  for rel in legacy_unranked)
    if not ranked and not issues:
        issues.add("no closeout registered for this claim")
    return "\n".join(lines + ["No handoff selected.", *sorted(issues)]), 3


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
    add("Before relying on this snapshot, run the generator with --check.")
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
    add("## Handoff")
    add("")
    add("    lane selected : none (use --lane AIF-NNN for an assigned lane)")
    add("")
    add("### Latest dated closeout filename (all lanes; context only)")
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
            f"The global dated closeout, {closeout_name}, is on disk but in no "
            "commit."
        )
    widowed = untracked_closeouts(root, head)
    others = [name for name in widowed if name != closeout_name]
    if others:
        warnings.append(
            "Untracked closeout(s): " + ", ".join(others[:2])
            + (f" (+{len(others) - 2} more)" if len(others) > 2 else "") + "."
        )
    if unmeasured:
        warnings.append(
            "Could not measure: " + ", ".join(unmeasured) + ". This projection is "
            "INCOMPLETE; do not read the absence of other warnings as health."
        )
    if closeout_behind not in ("?", "0", "not committed"):
        warnings.append(
            f"The global dated closeout is {closeout_behind} commit(s) behind HEAD. "
            "Read the assigned lane's handoff and `git log` for its actual state."
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
    add("Aside chains are ordered claims. Parent and birth UTC come from the lineage ledger.")
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

    add("Use the source artifacts for detail. Regenerate instead of restating this snapshot.")
    add("")
    return "\n".join(lines)


def normalized_for_check(text: str) -> str:
    """Normalize transport line endings and the volatile generation stamp.

    Every other rendered state line is load-bearing: HEAD, upstream, target,
    closeouts, warnings, claims, sessions, and lineage. A check that ignored
    any of those could report a stale projection current.
    """
    lines = text.replace("\r\n", "\n").replace("\r", "\n").splitlines()
    return "\n".join(
        GENERATED_UTC_PREFIX + "<volatile>"
        if line.startswith(GENERATED_UTC_PREFIX)
        else line
        for line in lines
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate the Tier 0 state projection.")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--write", action="store_true", help="write the file")
    mode.add_argument(
        "--check",
        action="store_true",
        help="fail when the persisted projection differs from current measured state",
    )
    mode.add_argument("--lane", metavar="AIF-NNN", help="show the assigned lane's handoff without writing")
    args = parser.parse_args(argv)

    root = repo_root()
    if args.lane is not None:
        if not re.fullmatch(r"AIF-\d{3,}", args.lane):
            parser.error("--lane requires an exact AIF claim number, such as AIF-174")
        try:
            body, code = lane_handoff(root, args.lane)
        except (ImportError, OSError, KeyError, TypeError, ValueError) as exc:
            print(f"tier0: cannot resolve {args.lane}: {exc}", file=sys.stderr)
            return 1
        print(body)
        return code
    body = render(root)
    size = len(body.encode("utf-8"))
    target = root / OUTPUT_RELATIVE
    result = 0

    if args.write:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(body, encoding="utf-8", newline="\n")
        print(f"tier0: wrote {OUTPUT_RELATIVE.as_posix()}  {size} B")
    elif args.check:
        if not target.is_file():
            print(
                f"tier0: stale -- missing {OUTPUT_RELATIVE.as_posix()}",
                file=sys.stderr,
            )
            result = 3
        else:
            persisted = target.read_text(encoding="utf-8", errors="replace")
            if normalized_for_check(persisted) != normalized_for_check(body):
                print(
                    f"tier0: stale -- {OUTPUT_RELATIVE.as_posix()}",
                    file=sys.stderr,
                )
                result = 3
            else:
                print(f"tier0: current -- {OUTPUT_RELATIVE.as_posix()}")
    else:
        print(body)
        print(f"--- tier0: {size} B (target under {SIZE_TARGET})", file=sys.stderr)

    if size > SIZE_TARGET:
        print(
            f"tier0: WARNING {size} B exceeds the {SIZE_TARGET} B target",
            file=sys.stderr,
        )
    return result


if __name__ == "__main__":
    raise SystemExit(main())
