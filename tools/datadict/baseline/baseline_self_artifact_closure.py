#!/usr/bin/env python3
"""DD-033 report-only baseline self-artifact closure.

Reads a DD-028 baseline check packet, reviews DD-023 file diff rows, and
classifies rows caused by the baseline/review artifacts created by the just-run
baseline acceptance sequence. It never edits source, baselines, or policy.
"""
from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def read_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, obj: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        json.dump(obj, f, indent=2, sort_keys=True)
        f.write("\n")


def write_csv(path: Path, rows: List[Dict[str, Any]], fieldnames: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        for row in rows:
            w.writerow(row)


def load_csv(path: Path) -> List[Dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def resolve_dd028_dir(arg: str) -> Path:
    p = Path(arg)
    if p.is_file():
        return p.parent
    return p


def find_diff_csv(dd028_dir: Path) -> Path:
    candidates = [
        dd028_dir / "diff" / "dd023_file_diff.csv",
        dd028_dir / "dd023_file_diff.csv",
    ]
    for c in candidates:
        if c.exists():
            return c
    matches = list(dd028_dir.rglob("dd023_file_diff.csv"))
    if matches:
        return matches[0]
    raise FileNotFoundError(f"Could not find dd023_file_diff.csv under {dd028_dir}")


def find_dd028_manifest(dd028_dir: Path) -> Path | None:
    candidates = [
        dd028_dir / "dd028_baseline_compare_manifest.json",
    ]
    for c in candidates:
        if c.exists():
            return c
    matches = list(dd028_dir.rglob("dd028_baseline_compare_manifest.json"))
    return matches[0] if matches else None


def classify_path(path: str, baseline_id: str) -> Tuple[str, str, str]:
    norm = path.replace("\\", "/").lstrip("./")
    # Self-artifacts produced by accepting/checking the same baseline sequence.
    baseline_prefix = f"docs/datadict/baselines/{baseline_id}/"
    if norm.startswith(baseline_prefix):
        return ("BASELINE_SELF_ARTIFACT", "ACCEPT_SELF_ARTIFACTS_OR_EXCLUDE_FROM_FINAL_DRIFT", "LOW")
    if norm.startswith("docs/datadict/review_queue/DD025-stable-v1-A-to-B/"):
        return ("BASELINE_REVIEW_SELF_ARTIFACT", "ACCEPT_SELF_ARTIFACTS_OR_EXCLUDE_FROM_FINAL_DRIFT", "LOW")
    if norm.startswith("docs/datadict/review_queue/DD026-stable-v1-A-to-B/"):
        return ("BASELINE_REVIEW_SELF_ARTIFACT", "ACCEPT_SELF_ARTIFACTS_OR_EXCLUDE_FROM_FINAL_DRIFT", "LOW")
    if norm.startswith("docs/datadict/review_queue/DD025-") or norm.startswith("docs/datadict/review_queue/DD026-"):
        return ("DATADICT_REVIEW_ARTIFACT", "HUMAN_TRIAGE_REQUIRED", "MEDIUM")
    if norm.startswith("docs/datadict/reports/DD028-"):
        return ("DATADICT_REPORT_ARTIFACT", "HUMAN_TRIAGE_REQUIRED", "MEDIUM")
    if norm.startswith("docs/datadict/"):
        return ("DATADICT_ARTIFACT", "DATADICT_SELF_REVIEW_REQUIRED", "LOW")
    return ("NON_SELF_ARTIFACT", "HUMAN_TRIAGE_REQUIRED", "HIGH")


def main() -> int:
    ap = argparse.ArgumentParser(description="DD-033 report-only baseline self-artifact closure")
    ap.add_argument("--dd028", required=True, help="DD-028 baseline-check run directory or manifest")
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--run-id", default="DD033-baseline-self-artifact-closure")
    ap.add_argument("--baseline-id", required=True)
    ap.add_argument("--profile", action="append", default=[])
    ap.add_argument("--accept-self-artifacts", action="store_true")
    ap.add_argument("--fail-on-blocked", action="store_true")
    args = ap.parse_args()

    dd028_dir = resolve_dd028_dir(args.dd028)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    diff_csv = find_diff_csv(dd028_dir)
    dd028_manifest_path = find_dd028_manifest(dd028_dir)
    dd028_manifest: Dict[str, Any] = read_json(dd028_manifest_path) if dd028_manifest_path else {}
    rows = load_csv(diff_csv)

    classified: List[Dict[str, Any]] = []
    self_count = 0
    non_self_count = 0
    blocking = 0
    for row in rows:
        path = row.get("path", "")
        disposition, action, severity = classify_path(path, args.baseline_id)
        is_self = disposition in {"BASELINE_SELF_ARTIFACT", "BASELINE_REVIEW_SELF_ARTIFACT"}
        if is_self:
            self_count += 1
        else:
            non_self_count += 1
        blocked = (not is_self) or (is_self and not args.accept_self_artifacts)
        if blocked:
            blocking += 1
        classified.append({
            "change_kind": row.get("change_kind") or row.get("change") or "",
            "path": path,
            "object_kind": row.get("object_kind", ""),
            "disposition": disposition,
            "severity": severity,
            "required_action": action,
            "is_self_artifact": "1" if is_self else "0",
            "blocking": "1" if blocked else "0",
            "base_sha256": row.get("base_sha256", ""),
            "candidate_sha256": row.get("candidate_sha256", ""),
            "base_bytes": row.get("base_bytes", ""),
            "candidate_bytes": row.get("candidate_bytes", ""),
        })

    if not rows:
        status = "PASS"
    elif non_self_count == 0 and args.accept_self_artifacts and blocking == 0:
        status = "SELF_ARTIFACT_CLOSURE_ACCEPTED"
    elif non_self_count == 0:
        status = "SELF_ARTIFACT_CLOSURE_REVIEW"
    else:
        status = "BLOCKED_NON_SELF_ARTIFACT_REVIEW"

    summary_rows: List[Dict[str, Any]] = []
    buckets: Dict[str, Dict[str, int]] = {}
    for r in classified:
        b = buckets.setdefault(str(r["disposition"]), {"count": 0, "blocking": 0})
        b["count"] += 1
        b["blocking"] += int(r["blocking"])
    for disp, vals in sorted(buckets.items()):
        summary_rows.append({"disposition": disp, "count": vals["count"], "blocking": vals["blocking"]})

    boundary_rows = [
        {"boundary": "source edits", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "build", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "DotTalk runtime launch", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "HELP mutation", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "META mutation", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "CMDHELPCHK mutation", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "DBF/CDX/LMDB/catalog mutation", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "baseline replacement", "observed": 0, "required": 0, "pass": 1},
    ]

    manifest = {
        "schema": "dd033_baseline_self_artifact_closure_v0",
        "run_id": args.run_id,
        "created_utc": utc_now(),
        "status": status,
        "baseline_id": args.baseline_id,
        "profiles": args.profile,
        "dd028_dir": str(dd028_dir),
        "dd028_status": dd028_manifest.get("status", ""),
        "diff_csv": str(diff_csv),
        "rows": len(rows),
        "self_artifacts": self_count,
        "non_self": non_self_count,
        "blocking": blocking,
        "accepted_self_artifacts": bool(args.accept_self_artifacts),
        "boundary_failures": 0,
    }

    write_json(out_dir / "dd033_baseline_self_artifact_closure_manifest.json", manifest)
    write_csv(out_dir / "dd033_self_artifact_rows.csv", classified, [
        "change_kind", "path", "object_kind", "disposition", "severity", "required_action",
        "is_self_artifact", "blocking", "base_sha256", "candidate_sha256", "base_bytes", "candidate_bytes"
    ])
    write_csv(out_dir / "dd033_disposition_summary.csv", summary_rows, ["disposition", "count", "blocking"])
    write_csv(out_dir / "dd033_boundary_ledger.csv", boundary_rows, ["boundary", "observed", "required", "pass"])

    report_lines = [
        "# DD-033 Baseline Self-Artifact Closure Report",
        "",
        f"Run id: `{args.run_id}`",
        f"Status: **{status}**",
        f"Created UTC: `{manifest['created_utc']}`",
        "",
        "## Summary",
        "",
        f"- Baseline id: `{args.baseline_id}`",
        f"- Rows examined: {len(rows)}",
        f"- Self-artifacts: {self_count}",
        f"- Non-self rows: {non_self_count}",
        f"- Blocking rows: {blocking}",
        f"- Explicit self-artifact acceptance: {1 if args.accept_self_artifacts else 0}",
        "",
        "## Disposition summary",
        "",
        "| Disposition | Count | Blocking |",
        "|---|---:|---:|",
    ]
    for s in summary_rows:
        report_lines.append(f"| {s['disposition']} | {s['count']} | {s['blocking']} |")
    report_lines.extend([
        "",
        "## Sample rows",
        "",
        "| Change | Disposition | Path | Blocking |",
        "|---|---|---|---:|",
    ])
    for r in classified[:25]:
        report_lines.append(f"| {r['change_kind']} | {r['disposition']} | `{r['path']}` | {r['blocking']} |")
    report_lines.extend([
        "",
        "## Boundary",
        "",
        "DD-033 is report-only. It does not edit source, run builds, launch DotTalk++, mutate HELP/META/CMDHELPCHK, write DBF/CDX/LMDB/catalog data, or replace a baseline.",
        "",
    ])
    (out_dir / "DD033_BASELINE_SELF_ARTIFACT_CLOSURE_REPORT.md").write_text("\n".join(report_lines), encoding="utf-8")

    print(f"DD-033 self-artifact closure manifest: {out_dir / 'dd033_baseline_self_artifact_closure_manifest.json'}")
    print(f"status: {status}; rows: {len(rows)}; self_artifacts: {self_count}; non_self: {non_self_count}; blocking: {blocking}")
    if args.fail_on_blocked and status.startswith("BLOCKED"):
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
