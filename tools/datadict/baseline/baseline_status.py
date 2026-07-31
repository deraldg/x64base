#!/usr/bin/env python3
"""DD-034 v1.1 report-only daily Data Dictionary baseline status command.

Runs DD-028 against an accepted baseline and, only when DD-028 reports real
file/review deltas, optionally runs DD-033 to determine whether the deltas are
baseline self-artifacts. If DD-028 reports zero added/removed/changed/review
rows, the final status is PASS_NO_SOURCE_DRIFT.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, obj: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, sort_keys=True)
        f.write("\n")


def write_csv(path: Path, rows: Iterable[Dict[str, Any]], fieldnames: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for row in rows:
            w.writerow({k: row.get(k, "") for k in fieldnames})


def as_int(value: Any, default: int = 0) -> int:
    try:
        if value is None or value == "":
            return default
        return int(value)
    except Exception:
        return default


def first_int(obj: Dict[str, Any], keys: List[str], default: int = 0) -> int:
    for key in keys:
        if key in obj:
            return as_int(obj.get(key), default)
    # one-level nested search for summary-like sections
    for val in obj.values():
        if isinstance(val, dict):
            for key in keys:
                if key in val:
                    return as_int(val.get(key), default)
    return default


def first_str(obj: Dict[str, Any], keys: List[str], default: str = "") -> str:
    for key in keys:
        if key in obj and obj.get(key) is not None:
            return str(obj.get(key))
    for val in obj.values():
        if isinstance(val, dict):
            for key in keys:
                if key in val and val.get(key) is not None:
                    return str(val.get(key))
    return default


def run_child(cmd: List[str], transcript: Path) -> Tuple[int, str]:
    transcript.parent.mkdir(parents=True, exist_ok=True)
    proc = subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    transcript.write_text(proc.stdout, encoding="utf-8")
    return proc.returncode, proc.stdout


def find_manifest(run_dir: Path, name: str) -> Optional[Path]:
    direct = run_dir / name
    if direct.exists():
        return direct
    matches = list(run_dir.rglob(name))
    if matches:
        return matches[0]
    return None


def derive_baseline_id(path_text: str) -> str:
    p = Path(path_text)
    if p.is_file():
        return p.parent.name
    return p.name or "UNKNOWN_BASELINE"


def build_report(path: Path, manifest: Dict[str, Any]) -> None:
    lines = [
        "# DD-034 Daily Redoc Baseline Status Report",
        "",
        f"Run id: `{manifest['run_id']}`",
        f"Status: **{manifest['status']}**",
        f"Created UTC: `{manifest['created_utc']}`",
        "",
        "## Summary",
        "",
        f"- Baseline: `{manifest['baseline_id']}`",
        f"- DD-028 status: `{manifest.get('dd028_status','')}`",
        f"- Added: {manifest.get('added',0)}",
        f"- Removed: {manifest.get('removed',0)}",
        f"- Changed: {manifest.get('changed',0)}",
        f"- Review rows: {manifest.get('review_rows',0)}",
        f"- HIGH rows: {manifest.get('high',0)}",
        f"- Self artifacts: {manifest.get('self_artifacts',0)}",
        f"- Non-self artifacts: {manifest.get('non_self',0)}",
        f"- Blocking self-artifact rows: {manifest.get('self_artifact_blocking',0)}",
        "",
        "## Interpretation",
        "",
        manifest.get("interpretation", "No interpretation recorded."),
        "",
        "## Boundary",
        "",
        "DD-034 is report-only. It does not accept or replace a baseline, edit source, run builds, launch DotTalk++, mutate HELP/META/CMDHELPCHK, write DBF/CDX/LMDB/catalog data, or move/delete files.",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="DD-034 v1.1 report-only daily Data Dictionary baseline status command")
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--baseline", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--run-id", default="DD034-daily-redoc-status")
    ap.add_argument("--profile", action="append", default=[])
    ap.add_argument("--python", dest="python_exe", default=sys.executable)
    ap.add_argument("--plan-only", action="store_true")
    ap.add_argument("--accept-self-artifacts", action="store_true")
    ap.add_argument("--fail-on-review", action="store_true")
    ap.add_argument("--fail-on-blocked", action="store_true")
    args = ap.parse_args(argv)

    repo = Path(args.repo_root).resolve()
    out = Path(args.out_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)
    transcripts = out / "transcripts"
    profiles = args.profile or []
    baseline_id = derive_baseline_id(args.baseline)

    steps: List[Dict[str, Any]] = []
    boundary_rows = [
        {"boundary": "source edits", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "build executed", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "DotTalk++ runtime launch", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "HELP/META/CMDHELPCHK mutation", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "DBF/CDX/LMDB/catalog mutation", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "baseline replacement", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "file move/delete", "observed": 0, "required": 0, "pass": 1},
    ]

    if args.plan_only:
        manifest = {
            "schema_id": "dd034_daily_redoc_status_v1_1",
            "run_id": args.run_id,
            "created_utc": utc_now(),
            "status": "PLAN_ONLY",
            "baseline_id": baseline_id,
            "profiles": profiles,
            "planned_steps": ["DD-028 baseline_check", "DD-033 self-artifact closure only if DD-028 reports changes"],
            "boundary_failures": 0,
        }
        write_json(out / "dd034_daily_redoc_status_manifest.json", manifest)
        build_report(out / "DD034_DAILY_REDOC_STATUS_REPORT.md", manifest)
        print(f"DD-034 daily status manifest: {out / 'dd034_daily_redoc_status_manifest.json'}")
        print("status: PLAN_ONLY")
        return 0

    # Step 1: run DD-028 baseline_check.
    dd028_dir = out / "dd028_baseline_check"
    dd028_tool = repo / "tools" / "datadict" / "baseline" / "baseline_check.py"
    dd028_cmd = [args.python_exe, str(dd028_tool), "--repo-root", str(repo), "--baseline", args.baseline, "--out-dir", str(dd028_dir), "--run-id", f"{args.run_id}-dd028"]
    for p in profiles:
        dd028_cmd.extend(["--profile", p])
    rc, _ = run_child(dd028_cmd, transcripts / "dd028_baseline_check.txt")
    steps.append({"step": "DD-028 baseline_check", "return_code": rc, "output_dir": str(dd028_dir)})
    if rc != 0:
        status = "TOOL_ERROR"
        manifest = {
            "schema_id": "dd034_daily_redoc_status_v1_1",
            "run_id": args.run_id,
            "created_utc": utc_now(),
            "status": status,
            "baseline_id": baseline_id,
            "profiles": profiles,
            "tool_error_step": "DD-028 baseline_check",
            "steps": steps,
            "boundary_failures": 0,
            "interpretation": "DD-028 baseline check returned a nonzero exit code.",
        }
        write_json(out / "dd034_daily_redoc_status_manifest.json", manifest)
        write_csv(out / "dd034_step_ledger.csv", steps, ["step", "return_code", "output_dir"])
        write_csv(out / "dd034_boundary_ledger.csv", boundary_rows, ["boundary", "observed", "required", "pass"])
        build_report(out / "DD034_DAILY_REDOC_STATUS_REPORT.md", manifest)
        print(f"DD-034 daily status manifest: {out / 'dd034_daily_redoc_status_manifest.json'}")
        print("status: TOOL_ERROR; step: DD-028 baseline_check")
        return 2

    dd028_manifest_path = find_manifest(dd028_dir, "dd028_baseline_compare_manifest.json")
    if not dd028_manifest_path:
        raise SystemExit("Could not find DD-028 manifest in child output")
    dd028 = read_json(dd028_manifest_path)
    dd028_status = first_str(dd028, ["status"], "UNKNOWN")
    added = first_int(dd028, ["added", "added_count", "files_added"])
    removed = first_int(dd028, ["removed", "removed_count", "files_removed"])
    changed = first_int(dd028, ["changed", "changed_count", "files_changed"])
    review_rows = first_int(dd028, ["review_rows", "review_row_count"])
    high = first_int(dd028, ["high", "high_rows", "high_count"])

    self_artifacts = 0
    non_self = 0
    self_blocking = 0
    dd033_status = "NOT_RUN"
    dd033_dir = ""

    if added == 0 and removed == 0 and changed == 0 and review_rows == 0:
        status = "PASS_NO_SOURCE_DRIFT"
        interpretation = "DD-028 reported zero added, removed, changed, and review rows. DD-033 self-artifact closure was intentionally not run."
    else:
        dd033_dir_path = out / "dd033_self_artifact_closure"
        dd033_dir = str(dd033_dir_path)
        dd033_tool = repo / "tools" / "datadict" / "baseline" / "baseline_self_artifact_closure.py"
        dd033_cmd = [args.python_exe, str(dd033_tool), "--dd028", str(dd028_dir), "--out-dir", str(dd033_dir_path), "--run-id", f"{args.run_id}-dd033", "--baseline-id", baseline_id]
        for p in profiles:
            dd033_cmd.extend(["--profile", p])
        if args.accept_self_artifacts:
            dd033_cmd.append("--accept-self-artifacts")
        rc33, _ = run_child(dd033_cmd, transcripts / "dd033_self_artifact_closure.txt")
        steps.append({"step": "DD-033 self_artifact_closure", "return_code": rc33, "output_dir": str(dd033_dir_path)})
        if rc33 != 0:
            status = "TOOL_ERROR"
            interpretation = "DD-033 self-artifact closure returned a nonzero exit code."
        else:
            dd033_manifest_path = find_manifest(dd033_dir_path, "dd033_baseline_self_artifact_closure_manifest.json")
            if dd033_manifest_path:
                dd033 = read_json(dd033_manifest_path)
                dd033_status = first_str(dd033, ["status"], "UNKNOWN")
                self_artifacts = first_int(dd033, ["self_artifacts", "self_artifact_rows"])
                non_self = first_int(dd033, ["non_self", "non_self_artifacts", "non_self_rows"])
                self_blocking = first_int(dd033, ["blocking", "blocking_rows"])
            if non_self == 0 and self_artifacts > 0 and self_blocking == 0:
                status = "REVIEW_SELF_ARTIFACT_ACCEPTED"
                interpretation = "DD-028 reported changes, and DD-033 classified all changed rows as accepted baseline/review self-artifacts."
            elif non_self == 0 and self_artifacts > 0:
                status = "REVIEW_SELF_ARTIFACT_ONLY"
                interpretation = "DD-028 reported changes, and DD-033 classified them as baseline/review self-artifacts requiring explicit acceptance."
            elif high > 0:
                status = "BLOCKED_SCRIPT_BOUNDARY"
                interpretation = "DD-028 reported real review rows with HIGH severity. Run DD-029/DD-030 disposition before baseline movement."
            else:
                status = "REVIEW_REAL_CHANGE"
                interpretation = "DD-028 reported real source/review differences not fully explained as baseline self-artifacts."

    manifest = {
        "schema_id": "dd034_daily_redoc_status_v1_1",
        "run_id": args.run_id,
        "created_utc": utc_now(),
        "status": status,
        "baseline_id": baseline_id,
        "baseline": args.baseline,
        "repo_root": str(repo),
        "profiles": profiles,
        "dd028_manifest": str(dd028_manifest_path),
        "dd028_status": dd028_status,
        "added": added,
        "removed": removed,
        "changed": changed,
        "review_rows": review_rows,
        "high": high,
        "dd033_status": dd033_status,
        "dd033_output_dir": dd033_dir,
        "self_artifacts": self_artifacts,
        "non_self": non_self,
        "self_artifact_blocking": self_blocking,
        "steps": steps,
        "boundary_failures": 0,
        "interpretation": interpretation,
    }
    write_json(out / "dd034_daily_redoc_status_manifest.json", manifest)
    write_csv(out / "dd034_step_ledger.csv", steps, ["step", "return_code", "output_dir"])
    write_csv(out / "dd034_boundary_ledger.csv", boundary_rows, ["boundary", "observed", "required", "pass"])
    write_csv(out / "dd034_summary.csv", [manifest], ["run_id", "status", "baseline_id", "dd028_status", "added", "removed", "changed", "review_rows", "high", "self_artifacts", "non_self", "self_artifact_blocking"])
    build_report(out / "DD034_DAILY_REDOC_STATUS_REPORT.md", manifest)

    print(f"DD-034 daily status manifest: {out / 'dd034_daily_redoc_status_manifest.json'}")
    print(f"status: {status}; added: {added}; removed: {removed}; changed: {changed}; review_rows: {review_rows}; self_artifacts: {self_artifacts}; non_self: {non_self}")

    if status in {"TOOL_ERROR", "BLOCKED_SCRIPT_BOUNDARY"} and args.fail_on_blocked:
        return 2
    if status not in {"PASS_NO_SOURCE_DRIFT"} and args.fail_on_review:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
