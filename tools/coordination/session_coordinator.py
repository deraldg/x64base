#!/usr/bin/env python3
"""
Concurrent-session coordinator (AIF-050 coordination component).

The failure it removes: multiple AI/Cowork sessions on one branch collide because the only shared
state is git (which hides authorship) and a hand-edited intake queue that many agents append to at
once -- proven live when four sessions collided on AIF-047 -> 048 -> 050 in one sitting.

Three primitives, all over the filesystem (the only medium concurrent local sessions actually share):

  claim-aif   Atomically claim the next AIF number -- MAX+1, never a gap (AIF-135, ruled
              2026-08-30) -- or a specific one with --number. Uses O_CREAT|O_EXCL, so if two
              sessions race for the same number exactly one wins the create -- a real allocator,
              not a hope. Durable claim files under coordination/aif/ are the allocation ledger.
              The universe is the intake register plus the claim files, the same universe
              next_aif.py reports on, so the two tools cannot drift apart.
  checkin     Register this session's presence (member, run, lanes, files) so others can SEE it.
  lock/unlock Advisory (cooperative) file lock for a contested shared doc; check before you edit.
  status      Show active sessions, held locks, claimed AIF numbers, and unread quips.
  checkout    Deregister this session.
  quip        Ephemeral co-session note (the lightest rung -- no ledger, no history):
              `quip send --from <run> --to <run|all> --msg "..."`, `quip read --run <me> [--ack]`.

Owner: member.derald - steward: member.ai.claude.cowork - lane: AIF-050 - status: candidate
"""
import argparse
import datetime as dt
import idcite
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
LINEAGE_DIR = f"{COORD}/lineage"
# R126: an AIF number is an INTEGER; the padding is display. This bound is the
# SCAN range, and it WAS the real ceiling in the minting path -- %03d widens by
# itself past 999, but this range stopped dead at it, so `claim-aif` would have
# returned no candidate at AIF-999 while the formatter was perfectly happy.
# Raised, and the candidate list below is now LAZY so the wider bound costs
# nothing: the generator stops at the first free number, it does not build a
# million-element list.
AIF_LO, AIF_HI = 6, 999999       # scan AIF-006 .. AIF-999999
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
    r"""AIF numbers cited in COMMITTED prose. The only source that carries a
    number CITED BUT NOT ROWED -- working_tree_aifs() is row-anchored and
    claimed_aifs() reads the claim directory, so a number like AIF-043 (cited
    in other rows' Notes, no row of its own, no claim file) exists HERE OR
    NOWHERE.

    THIS FUNCTION FAILED SILENTLY ON WINDOWS AND HANDED OUT A LIVE NUMBER.
    Measured 2026-08-30, same repository, same minute, two interpreters:

        Linux   git_committed 154 entries -> lowest free AIF-150
        Windows git_committed   0 entries -> lowest free AIF-043

    `text=True` decodes with the LOCALE codec -- UTF-8 on Linux, cp1252 on
    Windows -- and one byte in docs/ (0x81 at offset 338792) raised
    UnicodeDecodeError, which `except Exception: return set()` turned into "the
    repository contains no committed AIF citations." The universe silently lost
    its only source for cited-but-unrowed numbers, AIF-043 became the lowest
    gap, and the allocator issued a number belonging to the live ramfs/VDISK
    lane. THIRD OCCURRENCE: 2026-08-26 twice (see AIF-132 and AIF-134 rows),
    2026-08-30 once.

    TWO REPAIRS, AND THE SECOND MATTERS MORE THAN THE FIRST:

      1. Decode EXPLICITLY as utf-8 with errors="replace". The corpus is
         utf-8; a replacement character in a prose scan costs nothing, because
         the regex matches ASCII digits.
      2. DO NOT SWALLOW THE FAILURE. A scan that cannot read its authority
         must SAY SO. Returning an empty set is indistinguishable from a
         genuinely empty corpus, which is the AIF-118 shape -- one answer for
         "broken" and for "fine" -- inside the tool whose whole job is to
         prevent collisions. next_aif.py already holds the right posture:
         "REFUSING: found zero AIF numbers in either source. That is far more
         likely to be a broken path than an empty project."

    RULED 2026-08-30 (AIF-135, owner `member.derald`: "max+1"). THIS FUNCTION
    IS NO LONGER AN ALLOCATION AUTHORITY. It is a HYGIENE REPORT, printed by
    status() and read by a human. taken() no longer calls it.

    WHY THE DEMOTION IS SAFE, AND IT IS ONLY SAFE BECAUSE THE RULE CHANGED.
    Under the old LOWEST-FREE-GAP rule this scan was load-bearing: it was the
    only sight the allocator had of a number CITED BUT NEITHER ROWED NOR
    CLAIMED, and such numbers exist. Measured 2026-08-30 against the whole
    tree: AIF-089, AIF-102 and AIF-146 are real, spent numbers with zero
    intake rows and zero claim files. Lowest-gap would have minted all three.
    Under max+1 they cannot be reached at all -- every one of them is BELOW
    the register's high-water mark, and a gap is never handed out.

    WHY THE WIDE SCAN COULD NOT BE THE max+1 UNIVERSE. It greps all of docs/,
    so R126's allocator-range examples (AIF-998/999/1000/999999) are in scope
    and max+1 over THIS universe yields AIF-1000000. Measured, same minute:
    wide max 999999, narrow max 149. It also matches things that are not
    numbers -- five hits resolve to "AIF-0", which is the regex `AIF-0*(\d+)`
    quoted in prose. A scan built to over-count is the right shape for a
    warning and the wrong shape for an allocator.
    """
    try:
        out = subprocess.check_output(
            # -hE not -hoE: grep returns LINES and the Python pattern below is the
            # single extractor, so the brace-shorthand rule lives in exactly one
            # place. POSIX ERE cannot express the negative lookahead at all.
            ["git", "-C", str(root), "grep", "-hE", r"AIF-[0-9]+", "HEAD", "--", "docs", "AI_PORTAL.md"],
            # Explicit codec: never the locale's. See the docstring.
            encoding="utf-8", errors="replace", stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError as e:
        # EXIT 1 IS AN ANSWER, NOT A FAILURE: git grep exits 1 when it matches
        # nothing. Empty is honest here.
        if e.returncode == 1:
            return set()
        # EXIT 128 is "not a repository" / "bad revision". Legitimate off a
        # checkout -- the unit tests build temp roots with no git at all -- so
        # empty is honest, but it is ANNOUNCED. The defect this function
        # carried was not the empty set; it was the SILENCE around it.
        print(f"WARNING: git grep could not scan committed AIF citations "
              f"(exit {e.returncode}); allocator is running on claims and rows only",
              file=sys.stderr)
        return set()
    except FileNotFoundError:
        print("WARNING: git not found; allocator is running on claims and rows only",
              file=sys.stderr)
        return set()
    except Exception as e:
        # ANYTHING ELSE MEANS GIT SPOKE AND WE COULD NOT HEAR IT. That is the
        # 2026-08-30 defect exactly, and it must never again be indistinguishable
        # from an empty corpus.
        raise RuntimeError(
            f"could not read committed AIF citations: {e.__class__.__name__}: {e}"
        ) from e
    # Prose scan -> honours id-cite:ignore. working_tree_aifs() below is
    # row-anchored (a DECLARATION) and deliberately does not.
    return set(re.findall(r"\bAIF-0*([0-9]+)\b(?!\{)", idcite.live_text(out)))


def working_tree_aifs(root: Path):
    p = root / INTAKE
    if not p.exists():
        return set()
    return set(re.findall(r"^\|\s*AIF-0*([0-9]+)\b", p.read_text(errors="ignore"), re.MULTILINE))


def claimed_aifs(root: Path):
    d = root / AIF_DIR
    return {m.group(1) for f in d.glob("AIF-*.claim") if (m := re.match(r"AIF-0*(\d+)\.claim", f.name))}


def intake_mentions(root: Path):
    """Numbers written ANYWHERE in the intake register, not only as row ids.

    This is the rung that carries a number cited inside another row's Notes --
    AIF-043 was exactly that on 2026-08-25: three mentions, no row of its own.
    Suppressible by `id-cite:ignore` because these are CITATIONS; row ids are
    DECLARATIONS and are unioned in separately by working_tree_aifs(), which
    honours no marker. Same split, same reasoning, as next_aif.py.
    """
    p = root / INTAKE
    if not p.exists():
        return set()
    text = p.read_text(encoding="utf-8", errors="replace")
    return set(re.findall(r"AIF-0*([0-9]+)\b(?!\{)", idcite.live_text(text)))


def taken(root: Path):
    """THE ALLOCATION UNIVERSE. Intake register (rows AND mentions) plus claim
    files -- exactly what next_aif.py reads, so the allocator and the reporter
    agree BY CONSTRUCTION rather than by two people keeping two scans in step.

    RULED 2026-08-30, AIF-135, owner `member.derald`: "max+1". The rule and the
    width are one decision, not two. Lowest-gap makes the width safety-critical
    (every unrowed citation anywhere in the tree must be visible or it gets
    minted); max+1 makes it nearly irrelevant (only the maximum matters). This
    tree took the rule, so it takes the narrow universe with it. The
    repository-wide citation grep is REJECTED as an allocation source -- it
    holds arithmetic examples and quoted regexes as well as citations, and one
    authority holding two kinds with no discriminator is the count-discipline
    defect R126 already ruled on. It survives as a report; see
    git_committed_aifs().
    """
    return {int(x) for x in working_tree_aifs(root) | intake_mentions(root) | claimed_aifs(root)}


def unrowed_citations(root: Path):
    r"""Numbers cited in committed prose that the allocation universe cannot
    see. NOT a collision list -- under max+1 none of these is reachable. It is
    a HYGIENE list: a number spent without a row is a number whose lane nobody
    can look up. Measured 2026-08-30: AIF-089, AIF-102, AIF-146.

    AIF-0 IS DROPPED, and it is worth saying why rather than filtering it
    quietly: the five hits behind it are the matcher `AIF-0*(\d+)` QUOTED IN
    PROSE, in the very files that document this allocator. Zero is not an
    identity in this sequence -- AIF_LO is 6 -- so a report that lists it is
    reporting on its own documentation.
    """
    # MEASURED AGAINST DECLARATIONS, NOT AGAINST taken(). A row id and a claim
    # file DECLARE an identity; a mention inside another row's Notes does not.
    # If this subtracted taken(), then citing a number anywhere in the register
    # would SILENCE the report while the missing row stayed missing -- one
    # answer for "rowed" and for "merely mentioned", in a report whose only
    # question is which spent numbers have no row.
    declared = {int(x) for x in working_tree_aifs(root) | claimed_aifs(root)}
    wide = {int(x) for x in git_committed_aifs(root)}
    return sorted(n for n in wide - declared if n > 0)


def next_aif_number(root: Path, used=None):
    """max + 1, and FAIL CLOSED on an empty authority.

    An empty universe is far more likely to be a broken path than an empty
    project, and handing out AIF-006 on it is a collision with sixty years of
    ledger. next_aif.py has refused on this condition since it was written;
    the allocator did not, and the allocator is the half that MINTS. Returns
    None when it will not answer.
    """
    used = taken(root) if used is None else used
    if not used:
        print("REFUSING: found zero AIF numbers in the intake register or the",
              file=sys.stderr)
        print(f"  claim ledger. Expected authority: {INTAKE}", file=sys.stderr)
        print(f"  and {AIF_DIR}/. That is a broken path, not an empty project.",
              file=sys.stderr)
        return None
    nxt = max(used) + 1
    if nxt > AIF_HI:
        print(f"REFUSING: max+1 is AIF-{nxt}, past the scan ceiling AIF-{AIF_HI}.",
              file=sys.stderr)
        return None
    return nxt


def claim_aif(root: Path, member, run, lane, want=None, backfill_existing=False):
    """Mint or reserve an AIF number.

    AUTOMATIC (`want is None`): max+1 over taken(). MONOTONIC -- a gap is never
    handed out. AIF-135, ruled 2026-08-30 by `member.derald`. The old rule
    walked from AIF_LO and took the lowest free number, which is how run
    COWORK-20260830-001 was issued AIF-043, a live lane, for the third time.

    EXPLICIT (`--number`): may mint ONLY the next monotonic number. A forward
    skip is refused, because a hole created deliberately is still a hole and
    the sequence has no way to say why AIF-140 exists while 136..139 do not.
    A number ALREADY IN THE UNIVERSE -- rowed, mentioned or claimed -- is a
    different operation: attaching a missing claim file to a known identity,
    which needs `--backfill-existing` said out loud. Writing the row before
    running the claim is how AIF-146 was burned; the allocator should make
    that an explicit act, not a silent one.

    Rules 2, 3, 4, 5 and 6 of AIF-135's presented design, implemented here in
    the development tree. The design is `member.ai.codex`'s
    (`docs/maintenance/AIF135_MONOTONIC_AIF_ALLOCATOR_ALIGNMENT_V1.md`); it was
    verified in another tree on 2026-08-26 and never landed here, which is how
    the same defect minted AIF-043 a third time on 2026-08-30.
    """
    ensure_dirs(root)
    used = taken(root)
    if want is not None:
        if want in used:
            if not backfill_existing:
                print(f"AIF-{want:03d} is already in the allocation universe "
                      f"(intake row, intake citation, or claim file).", file=sys.stderr)
                print("  Attaching a claim to a known identity is a different "
                      "operation: pass --backfill-existing to say so.", file=sys.stderr)
                return None
        else:
            nxt = next_aif_number(root, used)
            if nxt is None:
                return None
            if want != nxt:
                print(f"AIF-{want:03d} is not the next monotonic number; "
                      f"AIF-{nxt:03d} is.", file=sys.stderr)
                print("  A forward skip leaves a hole the sequence cannot "
                      "explain. Re-run without --number, or ask for "
                      f"AIF-{nxt:03d}.", file=sys.stderr)
                return None
        candidates = [want]
    else:
        start = next_aif_number(root, used)
        if start is None:
            return None
        candidates = range(start, AIF_HI + 1)
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


def record_birth(root: Path, member, run, parent):
    """Write this run's DURABLE birth record once -- run, member, parent, born_utc.

    Unlike presence (active_sessions/, deleted at checkout), this lineage record is
    TRACKED and permanent: it is the project remembering a chat's origin and parentage,
    so a checked-out or resumed session can still answer "when was I born / who am I
    continued from" from the ledger instead of from a memory it does not have. This is
    the parent edge the two-atom ontology named but did not yet track (AIF-096); it also
    closes the origin-time gap a checked-out session otherwise cannot recover. Write-once
    via O_EXCL: a resumed session KEEPS its original birth and parent -- re-waking never
    rewrites them. Returns the born_utc that stands (the existing one if already born)."""
    (root / LINEAGE_DIR).mkdir(parents=True, exist_ok=True)
    p = root / LINEAGE_DIR / f"{run}.yaml"
    born = now()
    try:
        fd = os.open(str(p), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        for line in p.read_text(errors="ignore").splitlines():
            if line.startswith("born_utc:"):
                return line.split(":", 1)[1].strip()
        return born
    with os.fdopen(fd, "w") as fh:
        fh.write(f"run_id: {run}\nmember: {member}\nparent: {parent or 'none'}\nborn_utc: {born}\n")
    return born


def holds(root: Path, run):
    """AIF numbers whose durable claim file cites this run (what the session owns)."""
    out = []
    for f in sorted((root / AIF_DIR).glob("*.claim")):
        body = f.read_text(errors="ignore")
        if f"run_id: {run}" in body:
            m = re.search(r"AIF-0*([0-9]+)", body)
            # %03d, not the raw capture: the capture is unpadded now.
            out.append("AIF-%03d" % int(m.group(1)) if m else f.stem)
    return out


def wake(root: Path, member, run, parent=None):
    """A session's documented FIRST move: adopt identity, record durable birth+parent,
    refresh presence, read the inbox, and print who you are FROM THE RECORD. This is the
    chat->project read the two-atom model requires -- awareness is a chat reading its own
    record off the durable atom, not the chat knowing itself (AIF-096). Idempotent: birth
    and parent are write-once, so re-waking a resumed run reprints the same lineage."""
    born = record_birth(root, member, run, parent)
    checkin(root, member, run, "", "")
    held = holds(root, run)
    inbox = root / QUIP_DIR / run
    unread = len(list(inbox.glob("*.quip"))) if inbox.exists() else 0
    par = "none"
    for line in (root / LINEAGE_DIR / f"{run}.yaml").read_text(errors="ignore").splitlines():
        if line.startswith("parent:"):
            par = line.split(":", 1)[1].strip()
    print(f"you are {run}  (member {member})")
    print(f"  born:   {born}")
    print(f"  parent: {par}")
    print(f"  holds:  {', '.join(held) if held else '(no claims)'}")
    print(f"  inbox:  {unread} unread quip(s)")
    return 0


def quip_send(root: Path, frm, to, msg):
    """Drop an ephemeral note in a co-session's inbox. One file per quip (O_EXCL
    create, so concurrent senders never contend and no lock is needed). `--to all`
    broadcasts to every other currently-checked-in run.

    Liveness (warn-and-deliver, AIF-096): a quip is a chat->chat edge and a chat is
    mortal, so a DIRECT quip to a run that is NOT checked in lands in a local,
    gitignored inbox that a fresh clone never sees. We still deliver it -- the run may
    return to this same tree and read its inbox -- but WARN and point up the ladder to
    the durable pseudo-chat board, so the sender chooses the rung knowingly instead of
    dropping in silence. `--to all` was already liveness-aware (it refuses when no peer
    is live); this gives the direct path the same awareness. The warning is advisory:
    delivery still succeeds, so the exit code stays 0."""
    ensure_dirs(root)
    live = set(active_runs(root))
    absent = None
    if to == "all":
        targets = [r for r in live if r != frm]
        if not targets:
            print("(no other checked-in sessions to quip)", file=sys.stderr)
            return 1
    else:
        targets = [to]
        if to not in live:
            absent = to
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
    if absent is not None:
        print(f"WARNING: {absent} is not checked in -- this quip waits in a local, "
              f"gitignored inbox and will NOT reach a fresh clone. For durable delivery "
              f"to an absent agent, post to the pseudo-chat board "
              f"(docs/ai-friendly/PSEUDO_CHAT_BOARD.md).", file=sys.stderr)
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
    acked = 0
    for f in files:
        body = f.read_text(errors="ignore")
        print(f"  [{field(body, 'sent_utc')}] {field(body, 'from')}: {field(body, 'msg')}")
        if ack:
            # Report what was DELETED, not what was read. Some mounts (the sandbox
            # coordination/ mount) refuse unlink; swallowing that and printing
            # len(files) claims success on every un-acked quip. Same defect fixed in
            # checkout() 2026-07-26; it was left here in quip_read (added 2026-08-07)
            # and caught by the AIF-090 co-session. Surface the failure, count the truth.
            try:
                f.unlink()
                acked += 1
            except OSError as exc:
                print(f"  NOT acked ({type(exc).__name__}): {f.name}")
    if ack:
        print(f"(acked {acked} of {len(files)} quip(s))")
    return 0


def status(root: Path):
    ensure_dirs(root)
    print("=== session coordinator status ===")
    used = sorted(taken(root))
    nxt = next_aif_number(root, set(used))
    print(f"AIF taken: {', '.join('%03d' % n for n in used) or '(none)'}")
    # max+1, AIF-135. Printing a lowest-gap number here would advertise a
    # number claim-aif will refuse to mint -- two answers to one question.
    print(f"next-free AIF (max+1): {nxt:03d}" if nxt else "next-free: (none -- authority unreadable)")
    gaps = sorted(set(range(min(used), max(used))) - set(used)) if used else []
    if gaps:
        print(f"gaps, NOT reusable ({len(gaps)}): "
              + ", ".join("AIF-%03d" % n for n in gaps))
    # TWO KINDS, NAMED SEPARATELY -- the count-discipline rule R126 ruled on.
    # Below the high-water mark, an unrowed citation is a SPENT NUMBER whose
    # lane nobody can look up. Above it, it is an ARITHMETIC EXAMPLE (R126's
    # allocator-range sentinels). One list holding both taught the old
    # allocator that AIF-1000000 was next.
    unrowed = unrowed_citations(root)
    hi = max(used) if used else 0
    spent = [n for n in unrowed if n <= hi]
    sentinels = [n for n in unrowed if n > hi]
    if spent:
        print(f"cited in committed prose, NOT rowed or claimed ({len(spent)}): "
              + ", ".join("AIF-%03d" % n for n in spent)
              + "  -- spent, unreachable under max+1, but no row to look up")
    if sentinels:
        print(f"above the high-water mark, treated as range examples "
              f"({len(sentinels)}): " + ", ".join("AIF-%d" % n for n in sentinels)
              + "  -- NOT allocations, and NOT allocation input")
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
    c = sub.add_parser("claim-aif"); c.add_argument("--member", required=True); c.add_argument("--run", required=True); c.add_argument("--lane", required=True); c.add_argument("--number", type=int, default=None); c.add_argument("--backfill-existing", action="store_true")
    r = sub.add_parser("release-aif"); r.add_argument("--number", type=int, required=True); r.add_argument("--run", required=True); r.add_argument("--force", action="store_true")
    ci = sub.add_parser("checkin"); ci.add_argument("--member", required=True); ci.add_argument("--run", required=True); ci.add_argument("--lanes", default=""); ci.add_argument("--files", default="")
    co = sub.add_parser("checkout"); co.add_argument("--run", required=True)
    wk = sub.add_parser("wake"); wk.add_argument("--member", required=True); wk.add_argument("--run", required=True); wk.add_argument("--parent", default=None)
    lk = sub.add_parser("lock"); lk.add_argument("target"); lk.add_argument("--run", required=True)
    ul = sub.add_parser("unlock"); ul.add_argument("target"); ul.add_argument("--run", required=True)
    sub.add_parser("status")
    q = sub.add_parser("quip"); qs = q.add_subparsers(dest="qcmd", required=True)
    qsend = qs.add_parser("send"); qsend.add_argument("--from", dest="frm", required=True); qsend.add_argument("--to", required=True); qsend.add_argument("--msg", required=True)
    qread = qs.add_parser("read"); qread.add_argument("--run", required=True); qread.add_argument("--since", default=None); qread.add_argument("--ack", action="store_true")
    a = ap.parse_args()
    root = Path(a.root).resolve()
    if a.cmd == "claim-aif":
        return 0 if claim_aif(root, a.member, a.run, a.lane, a.number,
                              a.backfill_existing) is not None else 1
    if a.cmd == "release-aif":
        return release_aif(root, a.number, a.run, a.force)
    if a.cmd == "checkin":
        checkin(root, a.member, a.run, a.lanes, a.files); return 0
    if a.cmd == "checkout":
        return checkout(root, a.run)
    if a.cmd == "wake":
        return wake(root, a.member, a.run, a.parent)
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
