#!/usr/bin/env python3
"""
prepush_gate.py -- mechanical enforcement of the AI_PORTAL Pre-Push Gate.

IT RUNS AT COMMIT TIME, NOT PUSH TIME, AND THE NAME DOES NOT SAY SO.
Recorded 2026-08-24. `.git/hooks/pre-commit` invokes this guard (right after
repository_role_guard.py); `.git/hooks/pre-push` does NOT. So every message this
prints appears during `git commit`, and a change set is refused before it is
ever a commit -- which is the better place to stop it, and is why the wiring is
correct even though the name is misleading.

The name is historical: the AI_PORTAL rule it enforces is called the Pre-Push
Gate, and the gate moved earlier than its rule's name did. NOT RENAMED, because
the name is cited by that rule and by run records; corrected here instead, which
is the only place a reader of this file will look. `.git/hooks/` is not tracked,
so the wiring cannot be documented from inside the repository except here.


Single source of truth for the exclusion list is AI_PORTAL.md (the
"Outside-AI Delivery Rule", line ~300):

    "Do not include binaries, build directories, generated runtime data,
     unrelated formatting, cleanup, or branch operations."

This guard inspects a change set (staged index by default, or a commit range)
and classifies each path into three lanes:

  HARD BLOCK  -- things that must never be committed to source:
                build trees, CMake byproducts, compiled binaries, IDE project
                files. Presence => exit 2 (the gate fails).

  WARN/ACK    -- versioned data & runtime fixtures (DBF/DBT/FPT/CNX/CDX/INX,
                LMDB, generated help/metadata catalogs) and suspiciously large
                change sets. These CAN be legitimate (a deliberate fixture
                promotion the task named), so they do not hard-fail; they
                require an explicit acknowledgement flag. Without it => exit 3.

  OK          -- source, headers, docs, scripts, configs, manifests.

Exit codes:  0 clean - 2 hard-blocked - 3 warn-needs-ack - 4 usage/git error.

Usage:
  python tools/staging/prepush_gate.py                 # check staged index
  python tools/staging/prepush_gate.py --range HEAD..@{u}   # check a push range
  python tools/staging/prepush_gate.py --allow-data    # ack intentional fixtures
  python tools/staging/prepush_gate.py --allow-mass     # ack a large change set
  python tools/staging/prepush_gate.py --strict-aif     # AIF ledger/intake recon is hard
  python tools/staging/prepush_gate.py --skip-aif       # skip the AIF-number collision gate
  python tools/staging/prepush_gate.py --install-hook   # install managed commit + push hooks

The gate is advisory-by-design for the WARN lane: it never silently drops a
file, it reports and asks a human (or an agent) to name the mutation. It also
runs the AIF-number collision gate (tools/coordination/aif_collision_gate.py),
which HARD-blocks a duplicate lane number at the commit chokepoint.
"""
from __future__ import annotations

import argparse
import fnmatch
import os
import re
import subprocess
import sys

# --- Threshold for the "mass change" heuristic ---------------------------------
MASS_CHANGE_THRESHOLD = 60

# --- Threshold for listing the staged set by name (stowaway visibility) --------
STAGED_LIST_THRESHOLD = 15

# --- The file that rides in every commit by design -----------------------------
# tier0-refresh regenerates this at the end of every gate run, so it is dirty
# again the moment a commit finishes. That is deliberate. The side effect is
# that THE STAGED SET IS NEVER EMPTY, so git's own "nothing to commit" refusal
# -- the thing that normally catches a re-run -- can never fire here.
TIER0_STATE_PATH = "labtalk/ai_portal/TIER0_STATE.md"


def is_tier0_only(paths, range_spec, allow):
    """True when the staged set is EXACTLY the state file and nothing else.

    Kept pure and separate from main() so it can be exercised without shelling
    out to every portal gate -- the same reason repository_role_guard exposes
    validate_worktree. STAGED INDEX ONLY: a --range check reads history that
    may already contain such commits, and blocking a push on a mistake already
    made is a permanently red gate, which is a switched-off gate.
    """
    if range_spec is not None or allow:
        return False
    return (len(paths) == 1
            and paths[0].replace("\\", "/") == TIER0_STATE_PATH)


def tier0_only_message():
    """The block text, as lines.

    THE FIRST INSTRUCTION IS TO READ THE LOG, NOT TO UNDO ANYTHING. On the
    occasion that produced this guard, the reflex was to remove the duplicate
    commit, and the reset reached for --hard in a shared worktree: 38 files of
    a concurrent session's uncommitted work, gone, unrecoverable because
    unstaged changes never enter the object database. The papercut cost
    nothing; the reflex cost everything. So this message never names a
    destructive verb.
    """
    return [
        "BLOCKED -- the only staged file is TIER0_STATE.md, which rides in "
        "every commit by design.",
        "This is what an accidental re-run of an already-successful commit "
        "looks like: the real change went in a moment ago, `git add` found "
        "nothing left, and the commit went ahead anyway on the regenerated "
        "state file alone -- carrying the previous message and none of its "
        "content.",
        "Check `git log --oneline -3` FIRST. If the message you are about to "
        "use is already there, the work IS committed and there is nothing to "
        "do; a duplicate that already exists is a cosmetic problem and not "
        "worth a history rewrite in a shared worktree.",
        "If a refresh-only commit really is what you want, re-run with "
        "--allow-tier0-only (or set X64BASE_ALLOW_TIER0_ONLY=1).",
    ]

# --- HARD BLOCK patterns (never belong in a source commit) ---------------------
# Directory-segment matches (any path containing the segment) and glob suffixes.
HARD_BLOCK_DIR_SEGMENTS = (
    "/CMakeFiles/",
    "/build-msvc/",
    "/_tvision_local/",
)
HARD_BLOCK_PATH_PREFIXES = (
    "build/",
    "out/",
    "dist/",
    "bin/",
    "obj/",
)
HARD_BLOCK_PATH_PREFIX_GLOBS = (
    "build-*/",
    "build_*/",
    "cmake-build-*/",
)
HARD_BLOCK_SUFFIXES = (
    ".exe", ".dll", ".lib", ".pdb", ".obj", ".ilk", ".exp", ".pch",
    ".sln", ".vcxproj", ".vcxproj.filters", ".vcxproj.user",
    ".recipe", ".tlog", ".lastbuildstate",
    # LMDB environments (data.mdb / lock.mdb). DERIVED index backend, measured at
    # 53 GB in dottalkpp/data/lmdb on 2026-07-14; it must NEVER reach C:\x64base or
    # GitHub -- publish the CDX and regenerate LMDB locally. The .gitignore ignores
    # /data/lmdb/ and DATA_DIR_SEGMENTS only WARNS on that path, so a stray .mdb
    # written elsewhere would slip the gate. A hard suffix block makes "never .mdb"
    # enforced by mechanism regardless of location (the gate is the memory).
    ".mdb",
)
HARD_BLOCK_BASENAMES = (
    "CMakeCache.txt",
    "cmake_install.cmake",
    "CTestTestfile.cmake",
    "build.ninja",
)

# --- WARN lane: versioned data & generated runtime data ------------------------
DATA_SUFFIXES = (".dbf", ".dbt", ".fpt", ".cnx", ".cdx", ".inx", ".mdx")
# NOT here, deliberately, by owner ruling 2026-08-19: the FoxPro designer
# extensions -- .scx/.sct, .mnx/.mnt, .vcx/.vct, .frx/.frt -- are VALID
# x64base extensions. AIF-120 R10 measured that they are DBF tables, and an
# earlier version of this line added them here on that basis. That conflated
# two different things: this list exists to flag RUNTIME DATA CHURN staged by
# accident (regenerated indexes, help tables), and a form or menu is an
# AUTHORED ARTIFACT this project produces. Being DBF-shaped is a fact about
# the container, not about the role. They stay source.
DATA_DIR_SEGMENTS = (
    "/data/dbf/",
    "/data/indexes/",
    "/data/lmdb/",
    "/data/help/",
    "/data/metadata/",
    "/data/manuals/",
)

# --- AIF-number collision gate (AIF-050 coordination enforcement) --------------
# The commit is the one chokepoint every parallel session funnels through, so the
# duplicate-AIF check runs here regardless of whether any session ran the
# coordinator. A duplicate is a HARD block (it can never be a legitimate commit).
AIF_COLLISION_GATE = "tools/coordination/aif_collision_gate.py"
REPOSITORY_ROLE_GUARD = "tools/staging/repository_role_guard.py"

# --- AI report-audit gate (portal report-hygiene enforcement) ------------------
# When a push touches the AI-portal report surface (closeouts, received external
# intake packages, or the report registries/contracts), the ai_report_audit
# invariant must hold tree-wide: every enforced closeout carries a valid
# provenance envelope and no report id is duplicated. This is the "hallmark" that
# keeps the audit green -- a HARD block on any hard finding (intake findings are
# advisory and never block).
REPORT_AUDIT_GATE = "labtalk/ai_portal/audit_trail.py"
REPORT_SURFACE_PREFIXES = (
    "docs/maintenance/SESSION_CLOSEOUT_",
    "docs/maintenance/external_ai_intake/",
    "labtalk/ai_portal/",
    "labtalk/registries/ai_report_audit.yaml",
    "labtalk/registries/ai_report_index.yaml",
    "labtalk/registries/projects.yaml",
)

# --- Portal feed registry (AIF-132, advisory observation cycle) ---------------
# The typed feed seam is intentionally advisory until its known-bad tests and a
# real observation cycle establish acceptable noise. Do not turn a finding into
# a hard block here; promotion is an owner ruling recorded by the feed contract.
PORTAL_FEED_GATE = "labtalk/ai_portal/validate_portal_feeds.py"
PORTAL_ASSERTION_GATE = "labtalk/ai_portal/validate_portal_assertions.py"
PORTAL_FEED_STATUS_GATE = "labtalk/ai_portal/build_portal_feed_status.py"
PORTAL_FEED_SURFACE_PREFIXES = (
    "docs/contracts/DOTTALK_PORTAL_FEED_CONTRACT_V1.md",
    "docs/maintenance/AIF132_AI_PORTAL_FEED_HARDENING_LANE_V1.md",
    "docs/maintenance/SESSION_CLOSEOUT_AI_PORTAL_FEED_HARDENING_2026-08-26.md",
    "docs/maintenance/SESSION_CLOSEOUT_AI_PORTAL_STRUCTURED_ASSERTIONS_2026-08-26.md",
    "labtalk/ai_portal/build_portal_feed_status.py",
    "labtalk/ai_portal/validate_portal_assertions.py",
    "labtalk/ai_portal/validate_portal_feeds.py",
    "labtalk/ai_portal/tests/test_build_portal_feed_status.py",
    "labtalk/ai_portal/tests/test_validate_portal_assertions.py",
    "labtalk/ai_portal/tests/test_validate_portal_feeds.py",
    "labtalk/registries/current_fullstack_doc_push.yaml",
    "labtalk/registries/portal_assertions.yaml",
    "labtalk/registries/portal_feeds.yaml",
    "labtalk/reports/portal/portal_feed_status_latest.json",
    "labtalk/reports/portal/portal_feed_status_latest.md",
)

# --- Normalization guards (refcheck / normcheck) -- catalog-drift enforcement ----
# The command/function surface is described in several places (registry, SYSCMD,
# SYSFUNC, the *ref help catalogs, command_catalog) authored by different hands at
# different times. These guards fail when those descriptions disagree, so the drift
# a multi-session flush accumulates ("herding cats") cannot quietly re-open. Run
# ADVISORY by default (report, never block an in-flight commit); promote to a hard
# block per-lane via each guard's own LANE_SEVERITY, or wholesale with --strict-norm.
# Only run when the change set actually touches the surface (doc-only commits skip).
NORMALIZATION_GUARDS = (
    ("refcheck", "tools/fullstack_docs/refcheck_v1.py", ("--root", "{root}")),
    ("normcheck", "tools/fullstack_docs/normcheck_v1.py", ("{root}",)),
    # edrefcheck guards the EDUCATIONAL catalog, whose failure mode differs from
    # refcheck's: refcheck asks "does this command exist", edrefcheck asks "does
    # this teaching material hold together as a course" -- a script_ref naming a
    # file that is not there, a prereq naming a topic that is not there, a title
    # over the C80 that HELP_TOPIC.TITLE would silently truncate. Added under
    # AIF-118; `include/` is already in NORM_RELEVANT_PREFIXES, so a change to
    # include/edref.hpp triggers it without widening the trigger set.
    ("edrefcheck", "tools/fullstack_docs/edrefcheck_v1.py", ("--root", "{root}")),
)
NORM_RELEVANT_PREFIXES = (
    "include/", "src/cli/", "src/ext/", "src/help/",
    "dottalkpp/data/metadata/", "tools/fullstack_docs/",
)

# --- Embedded-BOM guard --------------------------------------------------------
# A UTF-8 BOM (EF BB BF) after byte 0 breaks MSVC (C3872/C2014/C2143). This is the
# AIF-062 backfill regression: a banner prepended above a BOM stranded it mid-file.
# HARD-block any staged C/C++ source whose blob carries an embedded BOM.
UTF8_BOM = b"\xef\xbb\xbf"
BOM_CHECK_SUFFIXES = (
    ".h", ".hpp", ".hh", ".hxx", ".ipp", ".inl",
    ".c", ".cc", ".cpp", ".cxx",
)


def run_git(args: list[str]) -> str:
    try:
        out = subprocess.run(
            ["git"] + args,
            check=True, capture_output=True, text=True,
        )
        return out.stdout
    except FileNotFoundError:
        print("prepush-gate: git not found on PATH", file=sys.stderr)
        sys.exit(4)
    except subprocess.CalledProcessError as e:
        print(f"prepush-gate: git {' '.join(args)} failed:\n{e.stderr}", file=sys.stderr)
        sys.exit(4)


def changed_paths(range_spec: str | None) -> list[str]:
    if range_spec:
        raw = run_git(["diff", "--name-only", "--diff-filter=ACMR", range_spec])
    else:
        raw = run_git(["diff", "--cached", "--name-only", "--diff-filter=ACMR"])
    return [p.strip().strip('"') for p in raw.splitlines() if p.strip()]


def norm(path: str) -> str:
    return "/" + path.replace("\\", "/").lstrip("/")


def is_hard_block(path: str) -> bool:
    p = norm(path)
    base = p.rsplit("/", 1)[-1]
    rel = p.lstrip("/")
    if any(seg in p for seg in HARD_BLOCK_DIR_SEGMENTS):
        return True
    if any(rel.startswith(pre) for pre in HARD_BLOCK_PATH_PREFIXES):
        return True
    if any(fnmatch.fnmatch(rel, g + "*") for g in HARD_BLOCK_PATH_PREFIX_GLOBS):
        return True
    if base in HARD_BLOCK_BASENAMES:
        return True
    low = base.lower()
    if any(low.endswith(sfx) for sfx in HARD_BLOCK_SUFFIXES):
        return True
    return False


def is_data_fixture(path: str) -> bool:
    p = norm(path).lower()
    if any(p.endswith(sfx) for sfx in DATA_SUFFIXES):
        return True
    if any(seg in p for seg in DATA_DIR_SEGMENTS):
        return True
    return False


def _staged_blob(path: str, range_spec: str | None) -> bytes | None:
    """Return the bytes git will commit for `path` (staged index, or range tip)."""
    rev = range_spec.split("..")[-1] if range_spec else ""
    spec = f"{rev}:{path}" if rev else f":{path}"
    try:
        out = subprocess.run(["git", "show", spec], capture_output=True)
    except FileNotFoundError:
        return None
    return out.stdout if out.returncode == 0 else None


def embedded_bom_offenders(paths: list[str], range_spec: str | None) -> list[str]:
    """C/C++ source paths whose committed blob carries a BOM after byte 0."""
    bad = []
    for p in paths:
        if not p.lower().endswith(BOM_CHECK_SUFFIXES):
            continue
        blob = _staged_blob(p, range_spec)
        if blob is not None and blob.find(UTF8_BOM) > 0:
            bad.append(p)
    return bad


def run_aif_collision_gate(strict: bool) -> int:
    """Run the AIF-number collision gate at the repo root and return its exit code
    (0 clean, 1 duplicate / strict-unreconciled). A missing gate script is treated
    as non-fatal so this stays robust if the coordination toolkit is absent; its
    own report is inherited to stdout/stderr in place."""
    root = run_git(["rev-parse", "--show-toplevel"]).strip()
    gate = os.path.join(root, *AIF_COLLISION_GATE.split("/"))
    if not os.path.isfile(gate):
        print(f"prepush-gate: AIF collision gate not found (skipped): {AIF_COLLISION_GATE}",
              file=sys.stderr)
        return 0
    cmd = [sys.executable, gate, "--root", root]
    if strict:
        cmd.append("--strict")
    return subprocess.run(cmd).returncode


def run_report_audit_gate() -> int:
    """Run the AI report-audit at the repo root and return its exit code (0 green,
    1 hard closeout findings). A missing script is non-fatal (returns 0) so the
    gate stays robust if the portal toolkit is absent; the audit's own report is
    inherited to stdout in place."""
    root = run_git(["rev-parse", "--show-toplevel"]).strip()
    gate = os.path.join(root, *REPORT_AUDIT_GATE.split("/"))
    if not os.path.isfile(gate):
        print(f"prepush-gate: report-audit gate not found (skipped): {REPORT_AUDIT_GATE}",
              file=sys.stderr)
        return 0
    return subprocess.run([sys.executable, gate, "--repo-root", root]).returncode


def run_normalization_guards() -> int:
    """Run refcheck + normcheck. Their reports print (so drift is never forgotten);
    returns 1 if any reported a fail-lane, 0 otherwise. A missing guard is skipped
    (non-fatal), so this stays robust if the fullstack-docs toolkit is absent."""
    root = run_git(["rev-parse", "--show-toplevel"]).strip()
    worst = 0
    for name, rel, extra in NORMALIZATION_GUARDS:
        script = os.path.join(root, *rel.split("/"))
        if not os.path.isfile(script):
            print(f"prepush-gate: normalization guard not found (skipped): {rel}",
                  file=sys.stderr)
            continue
        cmd = [sys.executable, script] + [a.format(root=root) for a in extra]
        if subprocess.run(cmd, cwd=root).returncode != 0:
            worst = 1
    return worst


def run_repository_role_guard() -> int:
    """Validate the current path and branch before inspecting a change set."""
    root = run_git(["rev-parse", "--show-toplevel"]).strip()
    guard = os.path.join(root, *REPOSITORY_ROLE_GUARD.split("/"))
    if not os.path.isfile(guard):
        print(
            f"prepush-gate: repository role guard missing: {REPOSITORY_ROLE_GUARD}",
            file=sys.stderr,
        )
        return 2
    return subprocess.run([sys.executable, guard, "--root", root]).returncode


def install_hook() -> int:
    root = run_git(["rev-parse", "--show-toplevel"]).strip()
    guard = os.path.join(root, *REPOSITORY_ROLE_GUARD.split("/"))
    return subprocess.run(
        [sys.executable, guard, "--root", root, "--install-hooks"]
    ).returncode


def _run_portal_check(rel: str, extra: list[str]) -> int:
    """Run an AIF-082 portal check. A MISSING check is never fatal.

    Deliberate: these four are newer than the gate and a clone or an older
    worktree may not carry them yet. A gate that hard-fails because an optional
    sub-check is absent would wedge exactly the people it exists to protect --
    which is the failure `check_mandatory_tracked.py` was written to detect, and
    it would be poor form to introduce it here.
    """
    root = run_git(["rev-parse", "--show-toplevel"]).strip()
    script = os.path.join(root, *rel.split("/"))
    if not os.path.exists(script):
        print(f"  (skipped: {rel} not present)")
        return 0
    try:
        return subprocess.run([sys.executable, script] + extra, cwd=root).returncode
    except (OSError, subprocess.SubprocessError) as exc:
        print(f"  (skipped: {rel} could not run: {exc})")
        return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="AI_PORTAL Pre-Push Gate enforcement.")
    ap.add_argument("--range", dest="range_spec", default=None,
                    help="commit range to check (e.g. HEAD..@{u}); default = staged index")
    ap.add_argument("--allow-data", action="store_true",
                    help="acknowledge intentional data/fixture changes (the task named the mutation)")
    ap.add_argument("--allow-mass", action="store_true",
                    help="acknowledge a large change set")
    ap.add_argument("--allow-tier0-only", action="store_true",
                    help="acknowledge a commit whose only staged file is "
                         "TIER0_STATE.md (normally an accidental re-run)")
    ap.add_argument("--install-hook", action="store_true",
                    help="install this gate as a git pre-commit hook and exit")
    ap.add_argument("--strict-aif", action="store_true",
                    help="promote the AIF ledger/intake reconciliation to a hard failure")
    ap.add_argument("--skip-aif", action="store_true",
                    help="skip the AIF-number collision gate")
    ap.add_argument("--skip-report-audit", action="store_true",
                    help="skip the AI report-audit (portal report-hygiene) gate")
    ap.add_argument("--skip-norm", action="store_true",
                    help="skip the normalization (refcheck/normcheck) catalog-drift guards")
    ap.add_argument("--skip-portal", action="store_true",
                    help="skip the AIF-082 portal gates (house style, mandatory-tracked, "
                         "stale index.lock, Session Log row)")
    ap.add_argument("--strict-norm", action="store_true",
                    help="promote normalization catalog drift to a hard failure (exit 2)")
    args = ap.parse_args()

    # The two acknowledgement flags are also readable from the environment, following the
    # X64BASE_ALLOW_STAGING_BRANCH precedent in repository_role_guard.py.
    #
    # Why this is needed: the pre-commit hook invokes this gate with NO arguments, so when
    # the gate refuses and says "re-run with --allow-mass", there is no way to comply from
    # a normal `git commit`. The only route left was --no-verify, which discards every
    # other check in the gate -- the mass-change warning would end up disabling the
    # hard-block, house-style, and mandatory-tracked checks along with itself. That is a
    # strictly worse outcome than the thing being acknowledged.
    #
    # An env var keeps the acknowledgement NARROW (one flag), SCOPED (one command
    # invocation), and LOUD (announced below). It is not a bypass: hard-blocks still fail.
    #
    #   Windows : set X64BASE_ALLOW_MASS=1  &&  git commit ...
    #   POSIX   : X64BASE_ALLOW_MASS=1 git commit ...
    if os.environ.get("X64BASE_ALLOW_MASS") == "1":
        args.allow_mass = True
    if os.environ.get("X64BASE_ALLOW_DATA") == "1":
        args.allow_data = True
    if os.environ.get("X64BASE_ALLOW_TIER0_ONLY") == "1":
        args.allow_tier0_only = True
    for name, on in (("X64BASE_ALLOW_MASS", args.allow_mass),
                     ("X64BASE_ALLOW_DATA", args.allow_data),
                     ("X64BASE_ALLOW_TIER0_ONLY", args.allow_tier0_only)):
        if on and os.environ.get(name) == "1":
            print(f"prepush-gate: {name}=1 -- acknowledgement accepted from the "
                  f"environment. Every other check still runs.")

    if args.install_hook:
        return install_hook()

    if run_repository_role_guard() != 0:
        print(
            "prepush-gate: BLOCKED -- repository path/branch role check failed.",
            file=sys.stderr,
        )
        return 2

    paths = changed_paths(args.range_spec)
    scope = args.range_spec or "staged index"
    if not paths:
        print(f"prepush-gate: no changes in {scope} -- clean.")
        return 0

    hard = [p for p in paths if is_hard_block(p)]
    data = [p for p in paths if p not in hard and is_data_fixture(p)]
    ok = [p for p in paths if p not in hard and p not in data]

    print(f"prepush-gate: inspecting {len(paths)} path(s) in {scope}")
    print(f"  source/docs/config : {len(ok)}")
    print(f"  data/fixtures      : {len(data)}")
    print(f"  hard-block         : {len(hard)}")

    # STAGED-SET VISIBILITY -- advisory by name, small sets only. Counts alone
    # let a pre-staged stowaway ride: a file staged by another session (or a
    # hook) is invisible in "N path(s)" until the commit's own stat output, when
    # it is already in history. Measured 2026-08-10: cf5caa7bb shipped a third
    # file its author never staged. Listing every path for sets under the
    # threshold makes the stowaway visible at the moment it can still be
    # unstaged; large sets already trip the mass-change WARN above.
    if len(paths) <= STAGED_LIST_THRESHOLD:
        for p in sorted(paths):
            print(f"    = {p}")

    # TIER0-ONLY COMMIT -- hard, staged index only (AIF-078, 2026-08-29).
    #
    # TIER0_STATE.md rides in every commit BY DESIGN, so the staged set is
    # never empty and git's "nothing to commit" refusal -- the safety net that
    # normally catches a re-run of an already-successful commit -- can never
    # fire in this repository. Every accidental re-run therefore SUCCEEDS,
    # producing a real commit that carries the previous one's message and none
    # of its content.
    #
    # MEASURED, THREE TIMES IN ONE SESSION (2026-08-28/29). The third produced
    # a70145a63, a duplicate of 272a00a54's message with 204 lines of the work
    # missing, sitting one commit ABOVE the real one -- so `git log` shows the
    # empty one first. Undoing that duplicate is what cost a concurrent session
    # 38 files of uncommitted work. The guard is cheap; it sits upstream of an
    # expensive reflex.
    #
    # THERE IS NO CASE where committing ONLY the regenerated state file is the
    # intent: it is derived, it is refreshed automatically, and it rides in the
    # next real commit anyway. A deliberate refresh-only commit stays reachable
    # through the acknowledgement -- narrow, scoped and loud like the other two.
    if is_tier0_only(paths, args.range_spec, args.allow_tier0_only):
        print("", file=sys.stderr)
        for line in tier0_only_message():
            print(f"  {line}", file=sys.stderr)
        print("\nprepush-gate: FAIL (exit 2).", file=sys.stderr)
        return 2

    exit_code = 0

    if hard:
        print("\n  BLOCKED -- these never belong in a source commit "
              "(build trees / binaries / IDE project files):", file=sys.stderr)
        for p in sorted(hard)[:40]:
            print(f"    X {p}", file=sys.stderr)
        if len(hard) > 40:
            print(f"    ... and {len(hard) - 40} more", file=sys.stderr)
        print("  Unstage them (git restore --staged <path>) or add to .gitignore.",
              file=sys.stderr)
        exit_code = 2

    if data and not args.allow_data:
        print("\n  WARN -- data/runtime fixtures staged. These are report-only unless "
              "the task named the mutation.", file=sys.stderr)
        for p in sorted(data)[:40]:
            print(f"    ? {p}", file=sys.stderr)
        if len(data) > 40:
            print(f"    ... and {len(data) - 40} more", file=sys.stderr)
        print("  If intentional, re-run with --allow-data (or restore them).",
              file=sys.stderr)
        if exit_code == 0:
            exit_code = 3

    if len(paths) > MASS_CHANGE_THRESHOLD and not args.allow_mass:
        print(f"\n  WARN -- {len(paths)} paths staged (> {MASS_CHANGE_THRESHOLD}). "
              "Large sets often mean an accidental mass add or an un-sliced batch.",
              file=sys.stderr)
        print("  Confirm the scope, then re-run with --allow-mass if intentional.",
              file=sys.stderr)
        if exit_code == 0:
            exit_code = 3

    bom = embedded_bom_offenders(paths, args.range_spec)
    if bom:
        print("\n  BLOCKED -- staged source file(s) carry an embedded UTF-8 BOM "
              "(EF BB BF after byte 0), which breaks MSVC (C3872/C2014):", file=sys.stderr)
        for p in sorted(bom)[:40]:
            print(f"    x {p}", file=sys.stderr)
        if len(bom) > 40:
            print(f"    ... and {len(bom) - 40} more", file=sys.stderr)
        print("  Re-save as UTF-8 without BOM (strip the stray bytes) before committing.",
              file=sys.stderr)
        exit_code = 2  # hard block

    if not args.skip_aif:
        print()  # spacer before the sub-gate's own report
        if run_aif_collision_gate(args.strict_aif) != 0:
            print("\n  BLOCKED -- AIF-number collision: a duplicate lane number is present "
                  "in the intake queue. Renumber one via "
                  "tools/coordination/session_coordinator.py claim-aif.", file=sys.stderr)
            exit_code = 2  # hard block dominates any WARN already set

    touches_report_surface = any(
        p.replace("\\", "/").startswith(REPORT_SURFACE_PREFIXES) for p in paths)
    if not args.skip_report_audit and touches_report_surface:
        print("\n=== AI report-audit (portal report hygiene) ===")
        if run_report_audit_gate() != 0:
            print("\n  BLOCKED -- AI report-audit found hard findings (a closeout is missing "
                  "its ai_report_audit envelope, or a report id is duplicated). Fix the "
                  "envelope(s) or renumber the id; intake-package findings are advisory and "
                  "never block.", file=sys.stderr)
            exit_code = 2  # hard block

    touches_portal_feed_surface = any(
        p.replace("\\", "/").startswith(PORTAL_FEED_SURFACE_PREFIXES) for p in paths)
    if touches_portal_feed_surface:
        print("\n=== Portal feed contract (AIF-132, advisory) ===")
        feed_rc = _run_portal_check(PORTAL_FEED_GATE, [])
        assertion_rc = _run_portal_check(PORTAL_ASSERTION_GATE, [])
        status_rc = _run_portal_check(PORTAL_FEED_STATUS_GATE, ["--check"])
        if any(rc != 0 for rc in (feed_rc, assertion_rc, status_rc)):
            print("\n  ADVISORY -- Portal feed validation reported drift or could not "
                  "evaluate the registries/status projection. NOT blocking during the AIF-132 "
                  "observation cycle; review the findings above before hardening.")

    touches_surface = any(
        p.replace("\\", "/").startswith(NORM_RELEVANT_PREFIXES) for p in paths)
    if not args.skip_norm and touches_surface:
        print("\n=== normalization guards (refcheck / normcheck) ===")
        if run_normalization_guards() != 0:
            if args.strict_norm:
                print("\n  BLOCKED -- normalization guard found catalog drift "
                      "(--strict-norm).", file=sys.stderr)
                exit_code = 2
            else:
                print("\n  ADVISORY -- catalog drift present (see above); NOT blocking. "
                      "Re-derive the lagging catalog (SYSCMD/SYSFUNC), or promote to a "
                      "hard block with --strict-norm / a lane's LANE_SEVERITY.")

    # ---- AIF-082 portal gates ------------------------------------------------
    # Four checks, each closing a rule that previously had no mechanism. 6.7
    # measured what that absence costs: obligations with gates held at 83-94
    # percent compliance, the one without held at 33. Severities differ on
    # purpose and each is argued, not assumed.
    if not args.skip_portal:
        print("\n=== AIF-082 portal gates ===")

        # 1. INDEX LOCK -- DELIBERATELY NOT CHECKED HERE. R138, amended the
        # same day it was made.
        #
        # This gate runs from .git/hooks/pre-commit, which means it executes
        # INSIDE a commit that git has already begun. `.git/index.lock` is
        # therefore ALWAYS present while this code runs, it is git's own, and
        # its size is the pending index for the very commit being gated --
        # measured at 668857 bytes for a one-file change and 668961 with a
        # second file staged.
        #
        # WHICH MAKES THE CHECK LOGICALLY DEAD IN THIS CONTEXT, not merely
        # noisy. The condition it exists to catch -- a STALE lock left by a
        # killed git -- cannot reach here: git refuses the commit with "Unable
        # to create .git/index.lock: File exists" before any hook runs. So the
        # check could only ever see the one lock that is guaranteed to be
        # innocent. A switch that moves nothing is not an open.
        #
        # It cost three false BLOCKs on 2026-09-01 before anyone read the hook
        # file, and the summary it printed -- "a stale index.lock is present.
        # Remove it" -- was instructing the maintainer to delete git's live
        # commit lock mid-commit.
        #
        # THE CHECK ITSELF IS GOOD AND IS KEPT. It is correct wherever no
        # commit is in flight, which is everywhere except here:
        #
        #     python tools\\staging\\check_sandbox_git_guard.py --lock-only
        #
        # Run it when a commit has ALREADY failed on a lock, or at session
        # start. tools/staging/test_git_guard_lock.py holds its four states.

        # 2. HOUSE STYLE -- hard, ADDED LINES ONLY. The 6,951-character backlog
        # never blocks anyone; new violations become impossible. Falsification
        # tested both directions 2026-07-31 before being wired in here.
        rc = _run_portal_check("tools/staging/check_house_style.py", [])
        if rc == 2:
            print("\n  BLOCKED -- non-ASCII in added documentation lines. "
                  "CLAUDE.md requires ASCII: use `--` and `->`. Only lines this "
                  "change introduces are checked.", file=sys.stderr)
            exit_code = 2

        # 2b. VERSION COHERENCE -- hard. The product version is declared by
        # `project(DotTalkpp VERSION x)` and was ALSO hand-typed in five other
        # places, one of which had already drifted ("0.6-dev" against the
        # authority's "0.6"). Nothing compared them, which is why bumping the
        # version kept being forgotten -- the forgetting was designed in.
        # AIF-120 collapsed the copies instead of policing them, so this gate
        # enforces "there are no copies" rather than "the copies agree".
        # Falsification tested 2026-08-21: a reintroduced literal and a
        # plausible C++ fallback each go red; the missing-authority arm is
        # written but was NOT observed firing.
        rc = _run_portal_check("tools/staging/check_version_coherence.py", [])
        if rc == 2:
            print("\n  BLOCKED -- the version is declared in more than one "
                  "place. Bump project(DotTalkpp VERSION x) in CMakeLists.txt "
                  "and let every other reader derive from it.", file=sys.stderr)
            exit_code = 2

        # 3. MANDATORY SET TRACKED -- hard. Found 16 portal-declared files
        # untracked, including the repository-role contract every document
        # defers to and the role guard this very gate invokes.
        rc = _run_portal_check("labtalk/ai_portal/check_mandatory_tracked.py", [])
        if rc == 2:
            print("\n  BLOCKED -- a file the portal declares mandatory is not "
                  "tracked, so a clone cannot read it. Commit it, or stop "
                  "declaring it mandatory.", file=sys.stderr)
            exit_code = 2

        # 4. SESSION LOG ROW -- WARN, never block. A commit that adds a closeout
        # is usually the right commit; refusing it would punish the sessions
        # doing the most work. Visibility at the moment of omission is the goal.
        rc = _run_portal_check("tools/coordination/check_session_log_row.py", [])
        if rc == 3:
            print("\n  ADVISORY -- a closeout is landing with no Session Log row "
                  "in the dashboard (AIF-006). NOT blocking. Add the row, or say "
                  "in the closeout why none is owed.")

        # 5. SELF-DECLARED BYTE BUDGETS -- ADVISORY for one cycle, then hard
        # (AIF-090 R4). The Tier 1 seed declares an 8,192 B ceiling about itself
        # and AI_PORTAL.md cites that ceiling as the project's exemplar of a
        # BOUNDED metric. Measured 2026-08-06 by a cold probe: the seed was
        # 8,990 B, over by 798, and nothing had noticed -- because the ceiling
        # was enforced by whoever happened to be watching. This is that rule
        # becoming a gate, which is the seed's own fourth bullet: a rule that
        # gains a hard-failing gate may then demote out of the entry path.
        #
        # FLIPPED TO HARD 2026-08-07 after 12 clean commits (AIF-090 R4). The
        # ceiling was the project's cited exemplar of a bounded metric and had
        # still drifted 798 B unnoticed, because it was enforced by whoever
        # happened to be watching. Now it is enforced by this.
        # 6. CITED PATHS -- ADVISORY, and scoped to this change set. A document
        # that cites a repo path it does not ship is the house's WIDOW, and
        # section 10 of the working rules says to sweep for them. That sweep had
        # no mechanism, and AIF-120 R42 measured the cost: a ruling shipped
        # asserting a fix that was not in tracked code, because `git add` on a
        # gitignored path is a SILENT no-op. The commit was clean and every gate
        # above passed -- correctly, since an ignored path never reaches the
        # staged index they inspect. Nine committed tools were unimportable on a
        # fresh clone for the same reason.
        #
        # Advisory, not blocking: a widow is usually someone forgetting to stage
        # one file, and refusing the commit that carries the rest of their work
        # is the wrong trade. Scoped to changed documents for the reason 5b
        # gives -- a check that reports the whole tree's backlog every commit
        # stops being read by the third day.
        rc = _run_portal_check("tools/staging/check_cited_paths.py", [])
        if rc == 3:
            print("\n  ADVISORY -- a document in this change set cites a repo path "
                  "that is not tracked (see above). NOT blocking. Stage the file, "
                  "or stop citing it. An IGNORED path can never be staged at all.")

        # 5d. MANUAL LINK INTEGRITY -- hard. Every page the accepted command
        # reference links to must exist AND BE TRACKED.
        #
        # Measured 2026-09-02 from the commit output of `5c1a39f7f`: the accepted
        # command reference had NEVER been tracked. All 165 pages landed as
        # `create mode`. The reader was in the repository; the 164 pages it links
        # to were not, so nothing looked wrong from either end.
        #
        # Every Gate 4 apply since 2026-07-18 therefore wrote into files git
        # could not see, which means NO APPLY COULD BE REVIEWED AS A DIFF -- and
        # that review is this lane's only real defence. Four Gate 4 plans were
        # built that day and three were discarded on exactly that review; all
        # three reported PASS_PLAN_ONLY findings=0.
        #
        # Hard rather than advisory, unlike 5c: a link that resolves only on the
        # author's disk is broken for every other reader, and unlike a widowed
        # citation it cannot be a staging oversight -- the file is either in the
        # repository or it is not. Both arms falsification-tested against a
        # fixture before being wired in here (missing, untracked-but-linked, and
        # stray each report distinctly).
        rc = _run_portal_check("tools/staging/check_manual_link_integrity.py", [])
        if rc == 2:
            print("\n  BLOCKED -- the accepted manual links to a page that is "
                  "missing or untracked. A link to an untracked page resolves on "
                  "one machine and nowhere else; the accepted manual is a "
                  "deliverable and belongs in the repository.", file=sys.stderr)
            exit_code = 2

        rc = _run_portal_check("tools/staging/check_seed_budget.py", [])
        if rc == 2:
            print("\n  BLOCKED -- a document is over the byte budget it declares "
                  "about itself. Adding requires REMOVING or DEMOTING, and "
                  "demoting means moving, not restating.", file=sys.stderr)
            exit_code = 2

        # 5b. OPEN ITEMS -- ADVISORY, and deliberately never anything else.
        # coordination/OPEN_ITEMS.md is the rung below a lane: work too small
        # for an AIF claim and too real to lose in chat. Every row is deferred
        # BY CHOICE, so blocking on one would teach the operator to delete the
        # row instead of doing the work -- losing the item AND reporting clean,
        # which is worse than never having written it down.
        #
        # It speaks only when a row's own NEXT LOOK date has passed. A count
        # that prints every commit stops being read by the third day; a date
        # makes the reminder periodic, and the row is silent until the day you
        # yourself asked to hear about it.
        rc = _run_portal_check("tools/coordination/check_open_items.py", [])
        if rc == 3:
            print("\n  ADVISORY -- open item(s) past their NEXT LOOK date "
                  "(coordination/OPEN_ITEMS.md). NOT blocking. Do it, or move "
                  "the date -- moving it is legitimate, leaving it stale is not.")

        # 6. NEW INTAKE ROWS CITE A CLAIMED AIF -- ADVISORY for one cycle, then
        # hard (AIF-092). The anti-collision loop had an allocator with no teeth
        # and a detector that only fires AFTER two lanes have collided: nothing
        # forced a lane through `claim-aif`, so a number chosen by eye satisfied
        # the duplicate check right up until someone else chose the same one.
        # Measured 2026-08-07: 25 claim files against 89 intake rows.
        #
        # ADDED ROWS ONLY, for the same reason `check_house_style.py` checks
        # added lines: 65 rows predate coordination, and a gate that fails on
        # those would be switched off within a day.
        # FLIPPED TO HARD 2026-08-07. The advisory cycle was short (2 commits)
        # but it surfaced the defect that mattered: a MODIFIED legacy row shows
        # in the diff as an added line, so trusting the marker would have
        # blocked routine maintenance on any of the 65 pre-coordination rows.
        # The check now compares against the pre-image and fires only on a
        # number NEW to the queue. Verified both directions before arming.
        # 6a. R-NUMBER COLLISIONS -- hard on a real collision, advisory on the
        # backlog. Added 2026-08-24 after a NEAR-MISS, not after a failure: a
        # ruling was about to be stamped R7 on the assumption that each AIF lane
        # carried its own R1..Rn series. It does not -- the R-space is one flat
        # global sequence and R7 has been taken since 2026-08-06 (the owner
        # ruling on AIF-090). Nothing detected it. The number was checked only
        # because someone happened to grep before typing.
        #
        # The AIF pair took two goes to get teeth (an optional allocator, then
        # a detector that only fired after a collision, then check_aif_claimed
        # closing it from the front). The R pair is built with both halves from
        # the start because that lesson is already paid for.
        #
        # THE BACKLOG IS ADVISORY AND WILL STAY THAT WAY. Roughly a hundred
        # numbers are cited with no register row and predate the register by
        # years. Blocking on those would be red every commit, and a permanently
        # red gate is a switched-off gate.
        rc = _run_portal_check("tools/coordination/r_collision_gate.py", [])
        if rc == 2:
            print("\n  BLOCKED -- R-number collision: either a duplicate row in "
                  "the register, or a newly declared number the tree already "
                  "cites. Run tools/coordination/next_r.py and take max+1; "
                  "grep is not an allocator.", file=sys.stderr)
            exit_code = 2
        elif rc == 3:
            print("\n  ADVISORY -- R-numbers cited with no register row. NOT "
                  "blocking. Back-fill what they meant when you next touch one; "
                  "they are reserved either way.")

        rc = _run_portal_check("tools/coordination/check_aif_claimed.py", [])
        if rc == 2:
            print("\n  BLOCKED -- a new intake row names an AIF number with no "
                  "claim file. Claim it atomically; grep is not an allocator. "
                  "Editing an existing row is not affected.", file=sys.stderr)
            exit_code = 2

        # 7. PUBLICATION RECEIPT IS FRESH -- hard, but ONLY when the receipt is
        # itself being committed (AIF-092 O-3).
        #
        # WHY NOT EVERY COMMIT. MANIFEST.txt reports 828 allow-listed files, and
        # that figure moves whenever any one of them is added or removed. A gate
        # comparing it on every commit would be red most days, and a permanently
        # red gate is switched off -- the same trap that made the seed-budget
        # ceiling drift and that this session hit twice more (the receipt's own
        # provenance line, and the legacy-intake-row false positive).
        #
        # The receipt is a PROMOTION-time artifact. Between promotions it is
        # EXPECTED to trail the tree; that lag is information, not drift. So the
        # only question worth blocking on is the narrow one: if you are
        # committing the receipt, is it freshly derived rather than stale or
        # hand-edited? Regenerating at promotion time is a separate step (O-4).
        if any(p.replace("\\", "/") == "MANIFEST.txt" for p in paths):
            rc = _run_portal_check("tools/staging/generate_public_manifest.py",
                                   ["--check"])
            if rc == 2:
                print("\n  BLOCKED -- MANIFEST.txt is staged but does not match "
                      "the tree it describes. It is GENERATED: run "
                      "`python tools/staging/generate_public_manifest.py --write`, "
                      "do not hand-edit it.", file=sys.stderr)
                exit_code = 2

    if exit_code == 0:
        print("\nprepush-gate: PASS -- change set is source/docs/config only "
              "(or acknowledged), no embedded BOM, no AIF-number collision.")
    else:
        print(f"\nprepush-gate: FAIL (exit {exit_code}).", file=sys.stderr)
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
