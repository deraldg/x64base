#!/usr/bin/env python3
"""
Registry evidence validator (AIF-062 follow-on).

Asserts that every artifact a registry CITES actually exists AND is tracked by git.

Why this exists: on 2026-07-25 a blanket `*.log` in .gitignore was found to be hiding
labtalk/proofs/runs/*.log -- the transcripts proofs.yaml rows point at as their evidence.
71 artifacts on disk, 0 tracked, 7 rows citing files absent from a clone. The registry's
central claim (that `runtime_observed` means a transcript exists) was unverifiable by
anyone not sitting at the maintainer's machine, and a fully crash-proven WAL lane read as
never-built. See docs/maintenance/AI_EVIDENCE_LAYER_VERSIONING_LANE_V1.md.

An untracked citation target is not evidence. It is a note.

Checks:
  proofs.yaml    every `source:` and `related:` path resolves and is tracked
  ai_runs.yaml   every `closeouts:` path resolves and is tracked
  lessons.yaml   every `path:` resolves (lesson bodies)

Advisory by default (reports, exit 0). --strict fails (exit 1).
Paths may be absolute (D:/code/ccode/...) or repo-relative; both are normalized.
External paths (e.g. D:/dev/x64base-site/...) are reported as out-of-repo, not failures.

  python tools/gates/validate_registries.py [--root <repo>] [--strict] [--quiet]

Owner: member.derald . steward: member.ai.claude.cowork . lane: AIF-062 . status: candidate
"""
import argparse
import subprocess
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("PyYAML required: pip install pyyaml --break-system-packages", file=sys.stderr)
    raise SystemExit(2)

ABS_PREFIXES = ("D:/code/ccode/", "d:/code/ccode/", "D:\\code\\ccode\\")


def normalize(p: str):
    """Return (repo_relative_path or None, is_external)."""
    s = str(p).strip().replace("\\", "/")
    if not s:
        return None, False
    for pre in (x.replace("\\", "/") for x in ABS_PREFIXES):
        if s.lower().startswith(pre.lower()):
            return s[len(pre):], False
    # any other absolute path is outside this repo
    if len(s) > 2 and s[1] == ":":
        return s, True
    if s.startswith("/"):
        return s, True
    return s, False


def tracked_set(root: Path) -> set:
    try:
        out = subprocess.check_output(["git", "-C", str(root), "ls-files"],
                                      text=True, errors="replace")
        return set(out.splitlines())
    except Exception as e:
        print(f"warning: git ls-files failed ({e}); tracking cannot be verified",
              file=sys.stderr)
        return set()


def load(root: Path, name: str):
    f = root / "labtalk" / "registries" / name
    if not f.is_file():
        return None
    try:
        return yaml.safe_load(f.read_text(encoding="utf-8", errors="replace"))
    except Exception as e:
        print(f"  PARSE FAIL {name}: {e}", file=sys.stderr)
        return "PARSE_FAIL"


def check(root: Path, tracked: set, rows, label: str, quiet: bool):
    """rows: list of (row_id, field, raw_path). Returns (ok, missing, untracked, external)."""
    ok = missing = untracked = external = 0
    for rid, field, raw in rows:
        rel, is_ext = normalize(raw)
        if rel is None:
            continue
        if is_ext:
            external += 1
            if not quiet:
                print(f"  EXTERNAL   {label}:{rid} [{field}] -> {rel}")
            continue
        if not (root / rel).exists():
            missing += 1
            print(f"  MISSING    {label}:{rid} [{field}] -> {rel}")
        elif tracked and rel not in tracked:
            untracked += 1
            print(f"  UNTRACKED  {label}:{rid} [{field}] -> {rel}")
        else:
            ok += 1
    return ok, missing, untracked, external


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", default=str(Path(__file__).resolve().parents[2]))
    ap.add_argument("--strict", action="store_true",
                    help="missing or untracked citations fail (exit 1)")
    ap.add_argument("--quiet", action="store_true",
                    help="suppress EXTERNAL lines")
    args = ap.parse_args()
    root = Path(args.root).resolve()

    tracked = tracked_set(root)
    print("=== registry evidence validator (AIF-062) ===")
    print(f"root:    {root}")
    print(f"tracked: {len(tracked)} files known to git\n")

    total_missing = total_untracked = total_ok = total_ext = 0
    parse_fail = False

    # --- proofs.yaml ---
    d = load(root, "proofs.yaml")
    if d == "PARSE_FAIL":
        parse_fail = True
    elif d:
        rows = []
        for p in d.get("proofs", []) or []:
            pid = p.get("id", "?")
            if p.get("source"):
                rows.append((pid, "source", p["source"]))
            for r in (p.get("related") or []):
                rows.append((pid, "related", r))
        o, m, u, e = check(root, tracked, rows, "proofs", args.quiet)
        print(f"proofs.yaml    : {o} ok, {m} missing, {u} untracked, {e} external")
        total_ok += o; total_missing += m; total_untracked += u; total_ext += e

    # --- ai_runs.yaml ---
    d = load(root, "ai_runs.yaml")
    if d == "PARSE_FAIL":
        parse_fail = True
    elif d:
        rows = []
        for r in d.get("runs", []) or []:
            rid = r.get("run_id", "?")
            for c in (r.get("closeouts") or []):
                rows.append((rid, "closeout", c))
        o, m, u, e = check(root, tracked, rows, "ai_runs", args.quiet)
        print(f"ai_runs.yaml   : {o} ok, {m} missing, {u} untracked, {e} external")
        total_ok += o; total_missing += m; total_untracked += u; total_ext += e

    # --- lessons.yaml ---
    d = load(root, "lessons.yaml")
    if d == "PARSE_FAIL":
        parse_fail = True
    elif d:
        rows = []
        skipped_idea = 0
        for l in d.get("lessons", []) or []:
            # A lesson at status: idea legitimately has no body yet -- the path is the
            # intended home, not a claim that it exists. Only check written lessons.
            if str(l.get("status", "")).strip() == "idea":
                skipped_idea += 1
                continue
            if l.get("path"):
                rows.append((l.get("id", "?"), "path", "labtalk/" + str(l["path"])))
        o, m, u, e = check(root, tracked, rows, "lessons", args.quiet)
        print(f"lessons.yaml   : {o} ok, {m} missing, {u} untracked, {e} external"
              + (f"  ({skipped_idea} at status:idea, body not yet written -- skipped)"
                 if skipped_idea else ""))
        total_ok += o; total_missing += m; total_untracked += u; total_ext += e

    print(f"\nTOTAL: {total_ok} verifiable, {total_missing} missing, "
          f"{total_untracked} untracked, {total_ext} external")

    if parse_fail:
        print("\nFAIL: a registry did not parse as YAML.", file=sys.stderr)
        return 1
    bad = total_missing + total_untracked
    if bad and args.strict:
        print(f"\nSTRICT: {bad} citation(s) not verifiable from a clone -> FAIL",
              file=sys.stderr)
        return 1
    if bad:
        print(f"\nadvisory: {bad} citation(s) not verifiable from a clone "
              f"(not a failure yet)")
    else:
        print("\nAll in-repo citations resolve and are tracked.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
