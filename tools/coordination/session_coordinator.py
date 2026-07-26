#!/usr/bin/env python3
"""
Concurrent-session coordinator (AIF-050 coordination component).

The failure it removes: multiple AI/Cowork sessions on one branch collide because the only shared
state is git (which hides authorship) and a hand-edited intake queue that many agents append to at
once — proven live when four sessions collided on AIF-047 -> 048 -> 050 in one sitting.

Three primitives, all over the filesystem (the only medium concurrent local sessions actually share):

  claim-aif   Atomically claim the next-free (or a specific) AIF number. Uses O_CREAT|O_EXCL, so if
              two sessions race for the same number exactly one wins the create — a real allocator,
              not a hope. Durable claim files under coordination/aif/ are the allocation ledger.
  checkin     Register this session's presence (member, run, lanes, files) so others can SEE it.
  lock/unlock Advisory (cooperative) file lock for a contested shared doc; check before you edit.
  status      Show active sessions, held locks, and claimed AIF numbers.
  checkout    Deregister this session.

Owner: member.derald · steward: member.ai.claude.cowork · lane: AIF-050 · status: candidate
"""
import argparse
import datetime as dt
import os
import re
import subprocess
import sys
from pathlib import Path

COORD = "coordination"
AIF_DIR = f"{COORD}/aif"
SESS_DIR = f"{COORD}/active_sessions"
LOCK_DIR = f"{COORD}/locks"
AIF_LO, AIF_HI = 6, 999          # scan AIF-006 .. AIF-999
STALE_MIN = 240                  # presence/lock older than this (min) is reapable
INTAKE = "docs/ai-friendly/AI_INTERACTION_INTAKE_QUEUE_V1.md"


def now():
    return dt.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")


def ensure_dirs(root: Path):
    for d in (AIF_DIR, SESS_DIR, LOCK_DIR):
        (root / d).mkdir(parents=True, exist_ok=True)


def git_committed_aifs(root: Path):
    try:
        out = subprocess.check_output(
            ["git", "-C", str(root), "grep", "-hoE", r"AIF-[0-9]{3}", "HEAD", "--", "docs", "AI_PORTAL.md"],
            text=True, stderr=subprocess.DEVNULL)
        return set(re.findall(r"AIF-([0-9]{3})", out))
    except Exception:
        return set()


def working_tree_aifs(root: Path):
    p = root / INTAKE
    if not p.exists():
        return set()
    return set(re.findall(r"^\|\s*AIF-([0-9]{3})\b", p.read_text(errors="ignore"), re.MULTILINE))


def claimed_aifs(root: Path):
    d = root / AIF_DIR
    return {m.group(1) for f in d.glob("AIF-*.claim") if (m := re.match(r"AIF-(\d{3})\.claim", f.name))}


def taken(root: Path):
    return {int(x) for x in git_committed_aifs(root) | working_tree_aifs(root) | claimed_aifs(root)}


def claim_aif(root: Path, member, run, lane, want=None):
    ensure_dirs(root)
    used = taken(root)
    candidates = [want] if want is not None else [n for n in range(AIF_LO, AIF_HI + 1) if n not in used]
    for n in candidates:
        path = root / AIF_DIR / f"AIF-{n:03d}.claim"
        try:
            fd = os.open(str(path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)  # atomic: one winner
        except FileExistsError:
            existing = path.read_text(errors="ignore").strip()
            if want is not None:
                print(f"AIF-{n:03d} already claimed:\n{existing}", file=sys.stderr)
                return None
            continue
        with os.fdopen(fd, "w") as fh:
            fh.write(f"aif: AIF-{n:03d}\nrun_id: {run}\nmember: {member}\nlane: {lane}\nclaimed_utc: {now()}\n")
        print(f"CLAIMED AIF-{n:03d}  (run {run}, {member}, lane '{lane}')")
        return n
    print("no free AIF number found", file=sys.stderr)
    return None


def release_aif(root: Path, number, run, force=False):
    """Void a claim (lane abandoned/demoted, or an erroneous/demo claim). Only the claiming run
    releases it, unless --force (maintainer override)."""
    path = root / AIF_DIR / f"AIF-{number:03d}.claim"
    if not path.exists():
        print(f"(no claim on AIF-{number:03d})")
        return 0
    body = path.read_text(errors="ignore")
    m = re.search(r"run_id:\s*(\S+)", body)
    owner_run = m.group(1) if m else "?"
    if owner_run != run and not force:
        print(f"AIF-{number:03d} claimed by {owner_run}, not {run}; use --force (maintainer) to override",
              file=sys.stderr)
        return 1
    path.unlink()
    print(f"RELEASED AIF-{number:03d} (was {owner_run})")
    return 0


def checkin(root: Path, member, run, lanes, files):
    ensure_dirs(root)
    p = root / SESS_DIR / f"{run}.yaml"
    p.write_text(f"run_id: {run}\nmember: {member}\nlanes: [{lanes}]\nfiles: [{files}]\n"
                 f"heartbeat_utc: {now()}\nstatus: active\n")
    print(f"CHECKED IN  {run} ({member})  lanes=[{lanes}]")


def checkout(root: Path, run):
    p = root / SESS_DIR / f"{run}.yaml"
    if p.exists():
        p.unlink()
        print(f"CHECKED OUT {run}")
    else:
        print(f"(no active session {run})")


def lock(root: Path, target, run):
    ensure_dirs(root)
    key = target.replace("/", "__")
    p = root / LOCK_DIR / f"{key}.lock"
    try:
        fd = os.open(str(p), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        print(f"LOCK HELD on {target}:\n{p.read_text(errors='ignore').strip()}", file=sys.stderr)
        return 1
    with os.fdopen(fd, "w") as fh:
        fh.write(f"target: {target}\nheld_by: {run}\nlocked_utc: {now()}\n")
    print(f"LOCKED {target}  (held_by {run})")
    return 0


def unlock(root: Path, target, run):
    key = target.replace("/", "__")
    p = root / LOCK_DIR / f"{key}.lock"
    if p.exists():
        p.unlink()
        print(f"UNLOCKED {target}")
    else:
        print(f"(no lock on {target})")


def _age_min(p: Path):
    try:
        return (dt.datetime.utcnow().timestamp() - p.stat().st_mtime) / 60.0
    except Exception:
        return 0.0


def status(root: Path):
    ensure_dirs(root)
    print("=== session coordinator status ===")
    used = sorted(taken(root))
    nxt = next((n for n in range(AIF_LO, AIF_HI + 1) if n not in set(used)), None)
    print(f"AIF taken: {', '.join('%03d' % n for n in used) or '(none)'}")
    print(f"next-free AIF: {nxt:03d}" if nxt else "next-free: (none)")
    print(f"claim ledger: {sorted(f.name for f in (root/AIF_DIR).glob('AIF-*.claim'))}")
    print("\nactive sessions:")
    for f in sorted((root / SESS_DIR).glob("*.yaml")):
        stale = " [STALE]" if _age_min(f) > STALE_MIN else ""
        print(f"  {f.stem}  ({_age_min(f):.0f} min ago){stale}")
    print("locks:")
    for f in sorted((root / LOCK_DIR).glob("*.lock")):
        stale = " [STALE]" if _age_min(f) > STALE_MIN else ""
        print(f"  {f.read_text(errors='ignore').splitlines()[0]}  ({_age_min(f):.0f} min){stale}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", default=".")
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("claim-aif"); c.add_argument("--member", required=True); c.add_argument("--run", required=True); c.add_argument("--lane", required=True); c.add_argument("--number", type=int, default=None)
    r = sub.add_parser("release-aif"); r.add_argument("--number", type=int, required=True); r.add_argument("--run", required=True); r.add_argument("--force", action="store_true")
    ci = sub.add_parser("checkin"); ci.add_argument("--member", required=True); ci.add_argument("--run", required=True); ci.add_argument("--lanes", default=""); ci.add_argument("--files", default="")
    co = sub.add_parser("checkout"); co.add_argument("--run", required=True)
    lk = sub.add_parser("lock"); lk.add_argument("target"); lk.add_argument("--run", required=True)
    ul = sub.add_parser("unlock"); ul.add_argument("target"); ul.add_argument("--run", required=True)
    sub.add_parser("status")
    a = ap.parse_args()
    root = Path(a.root).resolve()
    if a.cmd == "claim-aif":
        return 0 if claim_aif(root, a.member, a.run, a.lane, a.number) is not None else 1
    if a.cmd == "release-aif":
        return release_aif(root, a.number, a.run, a.force)
    if a.cmd == "checkin":
        checkin(root, a.member, a.run, a.lanes, a.files); return 0
    if a.cmd == "checkout":
        checkout(root, a.run); return 0
    if a.cmd == "lock":
        return lock(root, a.target, a.run)
    if a.cmd == "unlock":
        unlock(root, a.target, a.run); return 0
    if a.cmd == "status":
        status(root); return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
