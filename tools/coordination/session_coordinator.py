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
  status      Show active sessions, held locks, claimed AIF numbers, and unread quips.
  checkout    Deregister this session.
  quip        Ephemeral co-session note (the lightest rung -- no ledger, no history):
              `quip send --from <run> --to <run|all> --msg "..."`, `quip read --run <me> [--ack]`.

Owner: member.derald · steward: member.ai.claude.cowork · lane: AIF-050 · status: candidate
"""
import argparse
import datetime as dt
import os
import re
import subprocess
import sys
import time
from pathlib import Path

COORD = "coordination"
AIF_DIR = f"{COORD}/aif"
SESS_DIR = f"{COORD}/active_sessions"
LOCK_DIR = f"{COORD}/locks"
QUIP_DIR = f"{COORD}/quips"
AIF_LO, AIF_HI = 6, 999          # scan AIF-006 .. AIF-999
STALE_MIN = 240                  # presence/lock older than this (min) is reapable
INTAKE = "docs/ai-friendly/AI_INTERACTION_INTAKE_QUEUE_V1.md"


def now():
    # Timezone-aware UTC. Emits the identical "...Z" string utcnow() produced,
    # without the DeprecationWarning utcnow() raises on Python 3.12+ (this repo
    # runs 3.12.9), and without leaving a naive value that later arithmetic can
    # misread as local -- the bug fixed in _age_min().
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def ensure_dirs(root: Path):
    for d in (AIF_DIR, SESS_DIR, LOCK_DIR, QUIP_DIR):
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
    """Deregister a session.

    FIXED 2026-07-26: p.unlink() was unguarded, so a permission or sharing
    failure raised a raw PermissionError traceback rather than saying what went
    wrong. Observed when a sandboxed agent could read coordination/ but not
    unlink within it: the session stayed listed as active holding files nobody
    was editing, and the operator saw a stack trace instead of a next step.
    A coordination tool that crashes while releasing a claim is worse than one
    that never held it.
    """
    p = root / SESS_DIR / f"{run}.yaml"
    if not p.exists():
        print(f"(no active session {run})")
        return 0
    try:
        p.unlink()
    except OSError as exc:
        # AIF-082 6.8b, 2026-07-31: the 2026-07-26 fix stopped the traceback but
        # left the record reading `status: active` forever, so a session that
        # could not delete stayed listed as live. Observed that day: `status`
        # showed three active sessions, two stale by 12+ hours and one that had
        # tried to check out and failed. A presence signal that is mostly false
        # is a signal nobody reads, which is why no closeout in the tree records
        # having consulted it.
        #
        # Deleting is the preferred outcome; being HONEST is the required one.
        # If we cannot remove the file, rewrite it as closed so `status` can
        # filter it. Writing usually succeeds where unlinking fails, because the
        # mounts that refuse unlink still allow truncate-and-write.
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
            if "status: active" in text:
                text = text.replace("status: active", "status: closed")
            else:
                text = text.rstrip("\n") + "\nstatus: closed\n"
            text = text.rstrip("\n") + f"\nclosed_utc: {now()}\n"
            p.write_text(text, encoding="utf-8")
            print(f"CHECKED OUT {run} (marked closed; file could not be removed: {exc})")
            return 0
        except OSError as exc2:
            print(f"CHECKOUT FAILED {run}: {exc}", file=sys.stderr)
            print(f"  could not mark it closed either: {exc2}", file=sys.stderr)
            print(f"  the session record is still present: {p}", file=sys.stderr)
            print("  it will keep appearing in `status` until removed; delete it by hand",
                  file=sys.stderr)
            print("  or re-run this checkout from an account that can write there.",
                  file=sys.stderr)
            return 1
    print(f"CHECKED OUT {run}")
    return 0


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
    """Age of a presence/lock file in minutes.

    FIXED 2026-07-26: this read `dt.datetime.utcnow().timestamp()`. utcnow()
    returns a NAIVE datetime holding UTC wall-clock, and .timestamp() on a
    naive value interprets it as LOCAL time -- so on a UTC-7 host the result
    was inflated by exactly 420 minutes. Every session was reported
    "(420 min ago) [STALE]" the instant it checked in, which meant staleness
    detection could never fire and the [STALE] marker carried no information.
    Observed live during run COWORK-20260726-001.

    st_mtime is a true epoch, so compare it against a true epoch. time.time()
    is that, with no timezone in the path at all.
    """
    try:
        return (time.time() - p.stat().st_mtime) / 60.0
    except OSError:
        return 0.0


def _quip_stamp():
    # Filesystem-safe (no colons -- Windows), sortable, and unique to the
    # microsecond so two quips in the same second from one sender do not collide.
    return dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%S_%fZ")


def active_runs(root: Path):
    """Runs currently checked in (presence file present and not marked closed)."""
    out = []
    for f in (root / SESS_DIR).glob("*.yaml"):
        if "status: closed" not in f.read_text(errors="ignore"):
            out.append(f.stem)
    return out


def quip_send(root: Path, frm, to, msg):
    """Drop an ephemeral note in a co-session's inbox. One file per quip (O_EXCL
    create, so concurrent senders never contend and no lock is needed). `--to all`
    broadcasts to every other currently-checked-in run."""
    ensure_dirs(root)
    if to == "all":
        targets = [r for r in active_runs(root) if r != frm]
        if not targets:
            print("(no other checked-in sessions to quip)", file=sys.stderr)
            return 1
    else:
        targets = [to]
    for t in targets:
        inbox = root / QUIP_DIR / t
        inbox.mkdir(parents=True, exist_ok=True)
        for _ in range(8):  # retry the rare same-microsecond name collision
            p = inbox / f"{_quip_stamp()}-{frm}.quip"
            try:
                fd = os.open(str(p), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                break
            except FileExistsError:
                continue
        else:
            print(f"could not write a quip to {t} (name collisions)", file=sys.stderr)
            return 1
        with os.fdopen(fd, "w") as fh:
            fh.write(f"from: {frm}\nto: {t}\nsent_utc: {now()}\nmsg: {msg}\n")
    print(f"QUIP {frm} -> {', '.join(targets)}: {msg}")
    return 0


def quip_read(root: Path, run, since=None, ack=False):
    """Print my inbox oldest-to-newest. --since <stamp> filters by the filename
    stamp; --ack deletes the quips it printed (they are ephemeral by default)."""
    ensure_dirs(root)
    inbox = root / QUIP_DIR / run
    files = sorted(inbox.glob("*.quip")) if inbox.exists() else []
    if since:
        files = [f for f in files if f.name >= since]
    if not files:
        print(f"(no quips for {run})")
        return 0
    print(f"=== quips for {run} ({len(files)}) ===")
    def field(body, key):
        for line in body.splitlines():
            if line.startswith(key + ":"):
                return line.split(":", 1)[1].strip()
        return "?"
    for f in files:
        body = f.read_text(errors="ignore")
        print(f"  [{field(body, 'sent_utc')}] {field(body, 'from')}: {field(body, 'msg')}")
        if ack:
            try:
                f.unlink()
            except OSError:
                pass
    if ack:
        print(f"(acked {len(files)} quip(s))")
    return 0


def status(root: Path):
    ensure_dirs(root)
    print("=== session coordinator status ===")
    used = sorted(taken(root))
    nxt = next((n for n in range(AIF_LO, AIF_HI + 1) if n not in set(used)), None)
    print(f"AIF taken: {', '.join('%03d' % n for n in used) or '(none)'}")
    print(f"next-free AIF: {nxt:03d}" if nxt else "next-free: (none)")
    print(f"claim ledger: {sorted(f.name for f in (root/AIF_DIR).glob('AIF-*.claim'))}")
    # AIF-082 6.8b, 2026-07-31: separate LIVE from CLOSED and STALE. Previously
    # everything under active_sessions/ printed as an active session with a
    # [STALE] suffix, so the list was mostly noise and nobody consulted it. A
    # presence signal is only useful if "listed" means "probably working right
    # now" -- see cadence rule 4 in the Tier 1 seed, which depends on this.
    live, closed, stale_rows = [], [], []
    for f in sorted((root / SESS_DIR).glob("*.yaml")):
        age = _age_min(f)
        body = f.read_text(errors="ignore")
        if "status: closed" in body:
            closed.append((f, age))
        elif age > STALE_MIN:
            stale_rows.append((f, age))
        else:
            live.append((f, age))

    print("\nactive sessions (live):")
    for f, age in live:
        print(f"  {f.stem}  ({age:.0f} min ago)")
    if not live:
        print("  (none)")
    if stale_rows:
        print(f"\nstale, older than {STALE_MIN} min -- probably abandoned, reapable:")
        for f, age in stale_rows:
            print(f"  {f.stem}  ({age:.0f} min ago) [STALE]")
    if closed:
        print("\nclosed but not removed (checkout could not unlink):")
        for f, age in closed:
            print(f"  {f.stem}  ({age:.0f} min ago) [CLOSED]")
    qroot = root / QUIP_DIR
    inboxes = sorted(d for d in qroot.glob("*") if d.is_dir()) if qroot.exists() else []
    counts = [(d.name, len(list(d.glob("*.quip")))) for d in inboxes]
    counts = [(name, n) for name, n in counts if n]
    print("\nquips (unread by inbox):")
    if counts:
        for name, n in counts:
            print(f"  {name}: {n} unread")
    else:
        print("  (none)")

    print("\nlocks:")
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
    q = sub.add_parser("quip"); qs = q.add_subparsers(dest="qcmd", required=True)
    qsend = qs.add_parser("send"); qsend.add_argument("--from", dest="frm", required=True); qsend.add_argument("--to", required=True); qsend.add_argument("--msg", required=True)
    qread = qs.add_parser("read"); qread.add_argument("--run", required=True); qread.add_argument("--since", default=None); qread.add_argument("--ack", action="store_true")
    a = ap.parse_args()
    root = Path(a.root).resolve()
    if a.cmd == "claim-aif":
        return 0 if claim_aif(root, a.member, a.run, a.lane, a.number) is not None else 1
    if a.cmd == "release-aif":
        return release_aif(root, a.number, a.run, a.force)
    if a.cmd == "checkin":
        checkin(root, a.member, a.run, a.lanes, a.files); return 0
    if a.cmd == "checkout":
        return checkout(root, a.run)
    if a.cmd == "lock":
        return lock(root, a.target, a.run)
    if a.cmd == "unlock":
        unlock(root, a.target, a.run); return 0
    if a.cmd == "status":
        status(root); return 0
    if a.cmd == "quip":
        if a.qcmd == "send":
            return quip_send(root, a.frm, a.to, a.msg)
        if a.qcmd == "read":
            return quip_read(root, a.run, a.since, a.ack)
        return 2
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
