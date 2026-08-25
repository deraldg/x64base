#!/usr/bin/env python3
"""Did the full-stack doc push actually do what its transcript says? Ask the clock and the tables.

WHY THIS EXISTS. Flush v5 lost cycles to four failures that a transcript cannot
show and a human cannot reliably eyeball. All four are ORDERING facts -- who was
built before what -- and every one of them produced output that looked correct:

  2026-08-12  the store was rebuilt by an exe that PREDATED the dotref commit.
              The transcript was complete, well-formed, and evidence of nothing.
              Cost: a full cycle, plus a wrong theory invented to explain it.

  2026-08-24  CMDHELP BUILD LEGACY and CMDHELP BUILD . <src> were passed as one
              two-element -CommandLines array and ONLY THE FIRST RAN. --script
              is stdin redirection (main.cpp:195-213), so a nested std::cin read
              eats the following line. COMMANDS.dbf moved; HELP_LINE.dbf did
              not. The transcript looked fine. Caught only by comparing mtimes.

  2026-08-24  the exe was built from a DIRTY worktree three commits behind HEAD,
              including another session's uncommitted file, so the store was not
              reproducible from any commit. The banner says so -- "c39d966c
              dirty" -- and nobody read it, because the assertion that would
              have was withdrawn for being unsound and never replaced.

  2026-08-05+ 2,757 HELP_LINE rows carried a blank TOPICKEY, 9.4% of the store,
              through five rebuilds, while CMDHELPCHK said "OK no structural
              issues found" (AIF-126). A single-table gate cannot see a broken
              join.

Every one is cheap to detect and expensive to miss. This runs in about a second,
reads only file times and DBF headers, needs no engine and no build, and works
in a sandbox that cannot compile.

  $py12 tools\\coordination\\docpush_preflight.py            -- before you start
  $py12 tools\\coordination\\docpush_preflight.py --after    -- after a rebuild
  $py12 tools\\coordination\\docpush_preflight.py --no-git   -- skip git checks
  $py12 tools\\coordination\\docpush_preflight.py --prior-art "<subject>"
  $py12 tools\\coordination\\docpush_preflight.py --store <dir>  -- check a backup

Exit codes: 0 all checks pass, 1 a check failed, 2 could not read what it needs.
"""
import argparse
import datetime
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve()
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE.parent))

EXE = ROOT / "build" / "src" / "Release" / "dottalkpp.exe"
HELP = ROOT / "dottalkpp" / "data" / "help"
CATALOGS = ["include/dotref.hpp", "include/foxref.hpp", "include/edref.hpp"]
LEGACY = ["COMMANDS.dbf", "CMD_ARGS.dbf"]
STORE = ["HELP_LINE.dbf", "HELP_TOPIC.dbf"]
PRIOR_ART = ["labtalk/registries/ai_portal_tasks.yaml"]

PASS, FAIL, WARN, SKIP = "PASS", "FAIL", "WARN", "skip"


class Report:
    def __init__(self):
        self.rows = []

    def add(self, verdict, name, detail, why=None):
        self.rows.append((verdict, name, detail, why))

    def render(self):
        print("docpush preflight -- %s" % ROOT)
        print()
        for verdict, name, detail, why in self.rows:
            print("  %-5s %-26s %s" % (verdict, name, detail))
            if why and verdict in (FAIL, WARN):
                for line in why.splitlines():
                    print("        %s" % line)
        bad = [r for r in self.rows if r[0] == FAIL]
        print()
        if bad:
            print("RESULT: %d check(s) FAILED -- %s"
                  % (len(bad), ", ".join(r[1] for r in bad)))
        else:
            warns = [r for r in self.rows if r[0] == WARN]
            print("RESULT: clean%s" % (" (%d warning(s))" % len(warns) if warns else ""))
        return 1 if bad else 0


def mtime(p):
    try:
        return p.stat().st_mtime
    except OSError:
        return None


def stamp(t):
    if t is None:
        return "(missing)"
    return datetime.datetime.fromtimestamp(t).strftime("%Y-%m-%d %H:%M:%S")


def gap(a, b):
    """Human-readable signed gap b - a."""
    d = int(abs(b - a))
    unit = "%dm" % (d // 60) if d >= 60 else "%ds" % d
    if d >= 3600:
        unit = "%dh%02dm" % (d // 3600, (d % 3600) // 60)
    return unit


def git(args):
    try:
        out = subprocess.run(["git", "--no-optional-locks"] + args,
                             cwd=str(ROOT), capture_output=True, text=True,
                             timeout=30)
        return out.stdout if out.returncode == 0 else None
    except (OSError, subprocess.SubprocessError):
        return None


# --- the ordering checks ---------------------------------------------------
# Each one encodes a failure that actually happened, named in the docstring.

def check_binding(rep):
    """Is the exe reproducible from a commit? The 2026-08-24 failure."""
    head = git(["rev-parse", "--short", "HEAD"])
    if head is None:
        rep.add(SKIP, "binding", "git unavailable")
        return
    head = head.strip()
    dirty = git(["status", "--porcelain", "-uno"])
    if dirty is None:
        rep.add(SKIP, "binding", "could not read worktree state")
        return
    files = [l[3:] for l in dirty.splitlines() if l.strip()]
    if not files:
        rep.add(PASS, "binding", "worktree clean at %s" % head)
        return
    shown = "\n".join("  %s" % f for f in files[:8])
    if len(files) > 8:
        shown += "\n  ... and %d more" % (len(files) - 8)
    rep.add(WARN, "binding",
            "%d tracked file(s) modified at %s" % (len(files), head),
            "A store built now is NOT reproducible from any commit.\n"
            "Record it as runtime-proven against a WORKTREE, never against HEAD,\n"
            "and re-bind once these land:\n" + shown)


def check_exe_after_catalogs(rep):
    """dotref/foxref/edref are compiled IN. A stale exe publishes the old
    catalog silently. The 2026-08-12 failure."""
    exe = mtime(EXE)
    if exe is None:
        rep.add(FAIL, "exe present", "%s is missing" % EXE.name,
                "Nothing downstream can be trusted without it.")
        return None
    late = []
    for rel in CATALOGS:
        t = mtime(ROOT / rel)
        if t is not None and t > exe:
            late.append((rel, t))
    if late:
        rep.add(FAIL, "exe newer than catalogs",
                "exe %s is OLDER than %d catalog(s)" % (stamp(exe), len(late)),
                "\n".join("%s edited %s -- %s AFTER the exe was built"
                          % (rel, stamp(t), gap(exe, t)) for rel, t in late)
                + "\nThe catalogs are COMPILED IN. Rebuild before rebuilding the\n"
                  "store, or the store publishes the previous catalog and the\n"
                  "transcript will not say so.")
    else:
        rep.add(PASS, "exe newer than catalogs", "exe %s" % stamp(exe))
    return exe


def check_store_after_exe(rep, exe):
    """A store rebuilt by a stale exe looks like evidence and is not."""
    if exe is None:
        return None
    times = {n: mtime(HELP / n) for n in STORE}
    missing = [n for n, t in times.items() if t is None]
    if missing:
        rep.add(FAIL, "store present", "missing %s" % ", ".join(missing))
        return None
    oldest = min(times.values())
    if oldest < exe:
        rep.add(FAIL, "store newer than exe",
                "store %s predates exe %s" % (stamp(oldest), stamp(exe)),
                "The store was built by an EARLIER exe than the one on disk.\n"
                "Rebuild the store, or any assertion against it is measuring\n"
                "the previous build. This is the 2026-08-12 failure exactly.")
    else:
        rep.add(PASS, "store newer than exe",
                "store %s, %s after exe" % (stamp(oldest), gap(exe, oldest)))
    return times


def check_legacy_then_store(rep, times):
    """CMDHELP BUILD LEGACY then CMDHELP BUILD . <src>, as TWO separate
    datarun invocations. The 2026-08-24 half-run."""
    if not times:
        return
    legacy = {n: mtime(HELP / n) for n in LEGACY}
    if any(t is None for t in legacy.values()):
        rep.add(WARN, "legacy before store", "LEGACY artifacts missing",
                "CMDHELP BUILD LEGACY has never run against this store.")
        return
    newest_legacy = max(legacy.values())
    oldest_store = min(times.values())
    # Tolerance: a single pass that writes all four within a second or two is
    # fine. Only a store that is MEANINGFULLY older than LEGACY means the second
    # command never ran -- tonight's case was two HOURS older.
    if oldest_store < newest_legacy - 2:
        rep.add(FAIL, "legacy before store",
                "LEGACY %s is %s NEWER than the store %s"
                % (stamp(newest_legacy), gap(oldest_store, newest_legacy),
                   stamp(oldest_store)),
                "CMDHELP BUILD LEGACY ran and CMDHELP BUILD . <src> DID NOT.\n"
                "COMMANDS.dbf and CMD_ARGS.dbf moved; HELP_LINE.dbf and\n"
                "HELP_TOPIC.dbf did not. Almost certainly both were passed in\n"
                "one -CommandLines ARRAY: --script is stdin redirection\n"
                "(main.cpp:195-213), so a nested std::cin read in the first\n"
                "command eats the second line and only the first runs.\n"
                "ONE datarun.ps1 INVOCATION PER HELP-MUTATING COMMAND. Never an\n"
                "array. The transcript of a half-run looks complete.")
    else:
        rep.add(PASS, "legacy before store",
                "LEGACY %s -> store %s (%s later)"
                % (stamp(newest_legacy), stamp(oldest_store),
                   gap(newest_legacy, oldest_store)))


def check_store_integrity(rep):
    """The join no single-table gate can see. AIF-126."""
    try:
        import help_store_check as hsc
    except ImportError:
        rep.add(SKIP, "store integrity", "help_store_check.py not importable")
        return
    try:
        d = hsc.inspect(HELP)
    except (IOError, ValueError) as e:
        rep.add(FAIL, "store integrity", "could not read store: %s" % e)
        return
    problems = []
    if d["blank_key_rows"]:
        problems.append("%d line row(s) with a BLANK TOPICKEY" % d["blank_key_rows"])
    if d["orphan_headers"]:
        problems.append("%d header(s) with no lines" % len(d["orphan_headers"]))
    if d["orphan_lines"]:
        problems.append("%d line key(s) with no header" % len(d["orphan_lines"]))
    if problems:
        rep.add(FAIL, "store integrity", "; ".join(problems),
                "CMDHELPCHK reports OK over exactly this condition -- it checks\n"
                "one table at a time and the defect lives in the JOIN.\n"
                "Full detail: $py12 tools\\coordination\\help_store_check.py")
    else:
        rep.add(PASS, "store integrity",
                "%d topics reachable, every line row names one"
                % d["topics_reachable"])
    if d["pending_and_authoritative"]:
        rep.add(WARN, "status coherence",
                "%d row(s) are STATUS=pending and CONFID=AUTHORITATIVE at once"
                % d["pending_and_authoritative"],
                "The store says the same content is settled and unwritten.")


def check_generation_stamp(rep):
    """The DBF header carries its own build date -- free, and it cannot lie
    about a store that did not rebuild."""
    try:
        import help_store_check as hsc
        line = hsc.read_dbf(HELP / "HELP_LINE.dbf", ["TOPICKEY"])
        topic = hsc.read_dbf(HELP / "HELP_TOPIC.dbf", ["TOPICKEY"])
    except (IOError, ValueError, ImportError) as e:
        rep.add(SKIP, "generation stamp", str(e))
        return
    if line["gen"] != topic["gen"]:
        rep.add(FAIL, "generation stamp",
                "HELP_LINE %s but HELP_TOPIC %s" % (line["gen"], topic["gen"]),
                "The two tables were generated on different days. One rebuild\n"
                "did not reach both.")
    else:
        rep.add(PASS, "generation stamp", "both tables %s" % line["gen"])


def check_prior_art(rep, subject):
    """Twice in v5 a 'discovery' was already written down. Cheapest check
    there is."""
    hits = []
    for rel in PRIOR_ART:
        p = ROOT / rel
        if not p.exists():
            continue
        for n, ln in enumerate(p.read_text(encoding="latin1").splitlines(), 1):
            if subject.lower() in ln.lower():
                hits.append("%s:%d  %s" % (rel, n, ln.strip()[:100]))
    runs = ROOT / "docs/maintenance/lanes/full_stack_documentation/runs"
    if runs.exists():
        for p in sorted(runs.glob("*/NEXT_PUSH_CONTINUATION*")) + \
                 sorted(runs.glob("*/V6_HINTS*")):
            for n, ln in enumerate(p.read_text(encoding="latin1").splitlines(), 1):
                if subject.lower() in ln.lower():
                    hits.append("%s:%d  %s"
                                % (p.relative_to(ROOT), n, ln.strip()[:100]))
    if hits:
        rep.add(WARN, "prior art", "%d mention(s) of %r already on record"
                % (len(hits), subject),
                "\n".join(hits[:10])
                + ("\n... and %d more" % (len(hits) - 10) if len(hits) > 10 else "")
                + "\nRead these before calling it a discovery.")
    else:
        rep.add(PASS, "prior art", "no prior mention of %r" % subject)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--after", action="store_true",
                    help="post-rebuild mode: ordering checks are FAILs, not warnings")
    ap.add_argument("--no-git", action="store_true")
    ap.add_argument("--prior-art", metavar="SUBJECT",
                    help="search the lane's own record before claiming a finding")
    ap.add_argument("--store", metavar="DIR", default=None,
                    help="check a different help store (e.g. a help.bak-* snapshot)")
    a = ap.parse_args()

    global HELP
    if a.store:
        HELP = pathlib.Path(a.store)
        if not HELP.is_absolute():
            HELP = ROOT / a.store

    if not ROOT.exists():
        sys.stderr.write("docpush_preflight: cannot find repo root\n")
        return 2

    rep = Report()
    if a.prior_art:
        check_prior_art(rep, a.prior_art)
        return rep.render()

    if not a.no_git:
        check_binding(rep)
    exe = check_exe_after_catalogs(rep)
    times = check_store_after_exe(rep, exe)
    check_legacy_then_store(rep, times)
    check_generation_stamp(rep)
    check_store_integrity(rep)
    return rep.render()


if __name__ == "__main__":
    sys.exit(main())
