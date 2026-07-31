#!/usr/bin/env python3
"""
DD-029 report-only generated-package / maintenance-artifact disposition tool.

Classifies DD-025/DD-028 review rows into disposition buckets so the
redocumentation baseline can distinguish product/source drift from generated
maintenance packages, Data Dictionary self-changes, and accepted tooling changes.

Report-only: writes CSV/JSON/Markdown outputs only. Does not edit source,
run builds, launch DotTalk++, mutate HELP/META/CMDHELPCHK, or promote catalogs.
"""
from __future__ import annotations

import argparse
import csv
import fnmatch
import json
import os
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

DEFAULT_POLICY: Dict[str, Any] = {
    "policy_id": "DD029_GENERATED_PACKAGE_MAINTENANCE_ARTIFACT_POLICY_v0",
    "default_disposition": "HUMAN_TRIAGE_REQUIRED",
    "rules": [
        {
            "name": "root_mdo_package_script",
            "patterns": ["mdo_*/*.ps1", "mdo_*/*/*.ps1"],
            "disposition": "MAINTENANCE_PACKAGE_SCRIPT",
            "lane": "runtime_or_maintenance_script_surface",
            "severity": "HIGH",
            "required_action": "Classify package as generated/temporary/accepted evidence; do not treat as product source until reviewed.",
            "baseline_action": "EXCLUDE_FROM_STABLE_SOURCE_IF_PACKAGE_EVIDENCE_ACCEPTED",
            "requires": ["SCRIPT_BOUNDARY_REVIEW_REQUIRED", "DD_SCRIPT_RESCAN_REQUIRED"],
        },
        {
            "name": "root_mdo_package_docs",
            "patterns": ["mdo_*/README.md", "mdo_*/*.md", "mdo_*/*.csv", "mdo_*/*.json"],
            "disposition": "MAINTENANCE_PACKAGE_EVIDENCE",
            "lane": "maintenance_artifact_surface",
            "severity": "MEDIUM",
            "required_action": "Treat as package evidence; decide whether to archive, exclude from stable source, or promote as docs evidence.",
            "baseline_action": "EXCLUDE_FROM_STABLE_SOURCE_IF_PACKAGE_EVIDENCE_ACCEPTED",
            "requires": ["MAINTENANCE_ARTIFACT_DISPOSITION_REQUIRED"],
        },
        {
            "name": "datadict_docs",
            "patterns": ["docs/datadict/**"],
            "disposition": "DATADICT_LANE_CHANGE",
            "lane": "datadict_lane",
            "severity": "LOW",
            "required_action": "Review as Data Dictionary self-change; do not confuse with product source drift.",
            "baseline_action": "ELIGIBLE_AFTER_DATADICT_SELF_REVIEW",
            "requires": ["DATADICT_SELF_REVIEW_REQUIRED"],
        },
        {
            "name": "datadict_tools",
            "patterns": ["tools/datadict/**"],
            "disposition": "DATADICT_TOOLING_CHANGE",
            "lane": "tooling_surface",
            "severity": "MEDIUM",
            "required_action": "Run tool help/smoke; confirm report-only boundary before accepting baseline.",
            "baseline_action": "ELIGIBLE_AFTER_TOOL_SMOKE",
            "requires": ["TOOL_REVIEW_REQUIRED"],
        },
        {
            "name": "manualgen_reports",
            "patterns": ["docs/manuals/developer/manualgen/reports/**"],
            "disposition": "MANUALGEN_REPORT_EVIDENCE",
            "lane": "manualgen_lane",
            "severity": "MEDIUM",
            "required_action": "Review manualgen report evidence and publication gate impact.",
            "baseline_action": "ELIGIBLE_AFTER_MANUALGEN_REVIEW",
            "requires": ["MANUALGEN_REVIEW_REQUIRED"],
        },
        {
            "name": "savepoint_journal",
            "patterns": ["docs/MDO_SAVEPOINT_JOURNAL.md", "docs/datadict/runlog/**"],
            "disposition": "RUNLOG_OR_SAVEPOINT_EVIDENCE",
            "lane": "documentation_surface",
            "severity": "LOW",
            "required_action": "Preserve as run evidence; include in accepted evidence inventory, not product source drift.",
            "baseline_action": "ELIGIBLE_AS_EVIDENCE_ARTIFACT",
            "requires": ["DOC_REVIEW_REQUIRED"],
        },
        {
            "name": "core_source",
            "patterns": ["src/**", "include/**", "CMakeLists.txt", "CMakePresets.json", "cmake/**", "bindings/**"],
            "disposition": "PRODUCT_SOURCE_CHANGE",
            "lane": "product_source_surface",
            "severity": "HIGH",
            "required_action": "Run source contract, build/profile, HELP coverage, and relevant runtime proof checks.",
            "baseline_action": "NOT_BASELINE_ELIGIBLE_WITHOUT_SOURCE_REVIEW",
            "requires": ["SOURCE_CONTRACT_RESCAN_REQUIRED", "BUILD_PROFILE_REVIEW_REQUIRED"],
        },
        {
            "name": "dottalkpp_runtime_scripts",
            "patterns": ["dottalkpp/scripts/**", "dottalkpp/etc/**"],
            "disposition": "RUNTIME_SCRIPT_CHANGE",
            "lane": "runtime_or_maintenance_script_surface",
            "severity": "HIGH",
            "required_action": "Classify runtime role, mutation boundary, dependency links, and proof impact.",
            "baseline_action": "NOT_BASELINE_ELIGIBLE_WITHOUT_SCRIPT_REVIEW",
            "requires": ["SCRIPT_BOUNDARY_REVIEW_REQUIRED", "DD_SCRIPT_RESCAN_REQUIRED"],
        },
        {
            "name": "runtime_data",
            "patterns": ["dottalkpp/data/**"],
            "disposition": "RUNTIME_DATA_OR_BACKEND_CHANGE",
            "lane": "runtime_data_surface",
            "severity": "HIGH",
            "required_action": "Do not promote automatically; distinguish DBF/CDX/LMDB/runtime data from docs/tooling changes.",
            "baseline_action": "NOT_BASELINE_ELIGIBLE_WITHOUT_RUNTIME_DATA_REVIEW",
            "requires": ["RUNTIME_DATA_REVIEW_REQUIRED"],
        },
    ],
}


def norm_path(value: str) -> str:
    p = (value or "").strip().strip('"').replace("\\", "/")
    # Strip repo-root-looking prefix if present.
    m = re.search(r"(?:[A-Za-z]:)?/?code/ccode/(.*)$", p, re.IGNORECASE)
    if m:
        p = m.group(1)
    while p.startswith("./"):
        p = p[2:]
    return p


def glob_match(path: str, pattern: str) -> bool:
    path = norm_path(path)
    pattern = pattern.replace("\\", "/")
    if pattern.endswith("/**"):
        return path == pattern[:-3].rstrip("/") or path.startswith(pattern[:-3])
    return fnmatch.fnmatch(path, pattern)


def load_policy(path: Optional[Path]) -> Dict[str, Any]:
    if path and path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return DEFAULT_POLICY


def find_review_csv(input_path: Path) -> Path:
    if input_path.is_file():
        return input_path
    candidates = [
        input_path / "classification" / "dd025_classified_review_queue.csv",
        input_path / "dd025_classified_review_queue.csv",
        input_path / "dd023_review_queue.csv",
        input_path / "diff" / "dd023_review_queue.csv",
        input_path / "triage" / "dd026_sample_review_rows.csv",
    ]
    for c in candidates:
        if c.exists():
            return c
    matches = list(input_path.rglob("dd025_classified_review_queue.csv"))
    if not matches:
        matches = list(input_path.rglob("*review*queue*.csv"))
    if not matches:
        raise FileNotFoundError(f"No review queue CSV found under {input_path}")
    return matches[0]


def read_csv(path: Path) -> List[Dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def row_path(row: Dict[str, str]) -> str:
    for key in ("path", "relative_path", "file", "file_path", "FullName", "Path"):
        if row.get(key):
            return norm_path(row[key])
    # Some rows may use object_id-style path.
    for key, value in row.items():
        if value and ("/" in value or "\\" in value) and not key.lower().endswith("gates"):
            return norm_path(value)
    return ""


def first(row: Dict[str, str], *keys: str, default: str = "") -> str:
    for key in keys:
        if row.get(key) not in (None, ""):
            return str(row[key])
    return default


def classify(path: str, row: Dict[str, str], policy: Dict[str, Any]) -> Dict[str, Any]:
    for rule in policy.get("rules", []):
        for pat in rule.get("patterns", []):
            if glob_match(path, pat):
                return {
                    "rule": rule.get("name", ""),
                    "disposition": rule.get("disposition", ""),
                    "lane": rule.get("lane", first(row, "lane", "review_lane", default="")),
                    "severity": rule.get("severity", first(row, "severity", default="MEDIUM")),
                    "required_action": rule.get("required_action", ""),
                    "baseline_action": rule.get("baseline_action", ""),
                    "requires": ";".join(rule.get("requires", [])),
                }
    return {
        "rule": "default",
        "disposition": policy.get("default_disposition", "HUMAN_TRIAGE_REQUIRED"),
        "lane": first(row, "lane", "review_lane", default="unclassified_surface"),
        "severity": first(row, "severity", default="MEDIUM"),
        "required_action": "Human disposition required before baseline acceptance.",
        "baseline_action": "NOT_BASELINE_ELIGIBLE_WITHOUT_HUMAN_TRIAGE",
        "requires": "HUMAN_TRIAGE_REQUIRED",
    }


def write_csv(path: Path, rows: List[Dict[str, Any]], fieldnames: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fieldnames})


def write_markdown(path: Path, manifest: Dict[str, Any], lane_rows: List[Dict[str, Any]], disposition_rows: List[Dict[str, Any]], action_rows: List[Dict[str, Any]], sample_rows: List[Dict[str, Any]]) -> None:
    lines: List[str] = []
    lines.append("# DD-029 Artifact Disposition Report")
    lines.append("")
    lines.append(f"Run id: `{manifest['run_id']}`")
    lines.append(f"Status: **{manifest['status']}**")
    lines.append(f"Created UTC: `{manifest['created_utc']}`")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- Review rows examined: {manifest['review_rows']}")
    lines.append(f"- HIGH rows after disposition: {manifest['high_rows']}")
    lines.append(f"- Disposition buckets: {manifest['disposition_count']}")
    lines.append(f"- Boundary failures: {manifest['boundary_failures']}")
    lines.append("")
    lines.append("## Dispositions")
    lines.append("")
    lines.append("| Disposition | Count | High | Baseline action |")
    lines.append("|---|---:|---:|---|")
    for r in disposition_rows:
        lines.append(f"| {r['disposition']} | {r['count']} | {r['high']} | {r['baseline_action']} |")
    lines.append("")
    lines.append("## Lanes")
    lines.append("")
    lines.append("| Lane | Count | High |")
    lines.append("|---|---:|---:|")
    for r in lane_rows:
        lines.append(f"| {r['lane']} | {r['count']} | {r['high']} |")
    lines.append("")
    lines.append("## Recommended actions")
    lines.append("")
    lines.append("| Priority | Action | Count |")
    lines.append("|---:|---|---:|")
    for i, r in enumerate(action_rows, 1):
        lines.append(f"| {i} | {r['required_action']} | {r['count']} |")
    lines.append("")
    lines.append("## Sample disposition rows")
    lines.append("")
    lines.append("| Severity | Disposition | Change | Path | Required action |")
    lines.append("|---|---|---|---|---|")
    for r in sample_rows:
        lines.append(f"| {r['severity']} | {r['disposition']} | {r['change_kind']} | `{r['path']}` | {r['required_action']} |")
    lines.append("")
    lines.append("## Boundary")
    lines.append("")
    lines.append("DD-029 is report-only. It does not edit source, launch DotTalk++, mutate HELP/META/CMDHELPCHK, write DBF/CDX/LMDB/catalog data, or promote dictionary facts.")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="DD-029 report-only generated package / maintenance artifact disposition")
    ap.add_argument("--review", required=True, help="DD-025/DD-028 review queue directory or review CSV")
    ap.add_argument("--out-dir", required=True, help="Output directory for DD-029 disposition artifacts")
    ap.add_argument("--run-id", default="DD029-artifact-disposition")
    ap.add_argument("--policy", help="Optional generated artifact policy JSON")
    ap.add_argument("--profile", action="append", default=[])
    ap.add_argument("--fail-on-blocked", action="store_true")
    args = ap.parse_args(argv)

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    policy = load_policy(Path(args.policy) if args.policy else None)
    review_csv = find_review_csv(Path(args.review))
    rows = read_csv(review_csv)

    disposition_rows: List[Dict[str, Any]] = []
    for i, row in enumerate(rows, 1):
        path = row_path(row)
        meta = classify(path, row, policy)
        change_kind = first(row, "change_kind", "change", "kind", default="")
        orig_sev = first(row, "severity", default="")
        orig_lane = first(row, "lane", "review_lane", default="")
        gates = first(row, "gates", "required_gates", "gate", default="")
        disposition_rows.append({
            "row_id": f"DD029ROW-{i:06d}",
            "path": path,
            "change_kind": change_kind,
            "original_lane": orig_lane,
            "original_severity": orig_sev,
            "original_gates": gates,
            **meta,
        })

    lane_counter: Dict[str, Counter] = defaultdict(Counter)
    disposition_counter: Dict[str, Counter] = defaultdict(Counter)
    action_counter: Counter = Counter()
    for r in disposition_rows:
        lane_counter[r["lane"]]["count"] += 1
        disposition_counter[r["disposition"]]["count"] += 1
        if str(r["severity"]).upper() == "HIGH":
            lane_counter[r["lane"]]["high"] += 1
            disposition_counter[r["disposition"]]["high"] += 1
        disposition_counter[r["disposition"]]["baseline_action:" + r["baseline_action"]] += 1
        action_counter[r["required_action"]] += 1

    lane_summary = [
        {"lane": lane, "count": c["count"], "high": c["high"]}
        for lane, c in sorted(lane_counter.items(), key=lambda kv: (-kv[1]["count"], kv[0]))
    ]
    disp_summary = []
    for disp, c in sorted(disposition_counter.items(), key=lambda kv: (-kv[1]["count"], kv[0])):
        baseline_actions = [k.split(":", 1)[1] for k, v in c.items() if k.startswith("baseline_action:")]
        disp_summary.append({
            "disposition": disp,
            "count": c["count"],
            "high": c["high"],
            "baseline_action": ";".join(sorted(set(baseline_actions))),
        })
    action_rows = [
        {"required_action": action, "count": count}
        for action, count in action_counter.most_common()
    ]

    high_rows = sum(1 for r in disposition_rows if str(r["severity"]).upper() == "HIGH")
    blocked = any(str(r["baseline_action"]).startswith("NOT_BASELINE_ELIGIBLE") for r in disposition_rows)
    status = "PASS" if not disposition_rows else ("BLOCKED_DISPOSITION_REVIEW" if blocked or high_rows else "REVIEW")
    manifest = {
        "schema": "dd029_artifact_disposition_manifest_v0",
        "run_id": args.run_id,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "profiles": args.profile,
        "input_review_csv": str(review_csv),
        "policy_id": policy.get("policy_id", ""),
        "review_rows": len(disposition_rows),
        "high_rows": high_rows,
        "disposition_count": len(disp_summary),
        "lane_count": len(lane_summary),
        "boundary_failures": 0,
        "outputs": {
            "disposition_rows": "dd029_artifact_disposition_rows.csv",
            "disposition_summary": "dd029_disposition_summary.csv",
            "lane_summary": "dd029_lane_summary.csv",
            "action_summary": "dd029_required_action_summary.csv",
            "report": "DD029_ARTIFACT_DISPOSITION_REPORT.md",
        },
    }

    write_csv(out_dir / "dd029_artifact_disposition_rows.csv", disposition_rows, [
        "row_id", "path", "change_kind", "original_lane", "original_severity", "original_gates",
        "rule", "disposition", "lane", "severity", "requires", "baseline_action", "required_action",
    ])
    write_csv(out_dir / "dd029_lane_summary.csv", lane_summary, ["lane", "count", "high"])
    write_csv(out_dir / "dd029_disposition_summary.csv", disp_summary, ["disposition", "count", "high", "baseline_action"])
    write_csv(out_dir / "dd029_required_action_summary.csv", action_rows, ["required_action", "count"])
    (out_dir / "dd029_artifact_disposition_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    (out_dir / "dd029_policy_effective.json").write_text(json.dumps(policy, indent=2), encoding="utf-8")
    write_markdown(out_dir / "DD029_ARTIFACT_DISPOSITION_REPORT.md", manifest, lane_summary, disp_summary, action_rows, disposition_rows[:30])

    print(f"DD-029 disposition manifest: {out_dir / 'dd029_artifact_disposition_manifest.json'}")
    print(f"status: {status}; review_rows: {len(disposition_rows)}; high: {high_rows}; dispositions: {len(disp_summary)}")
    if args.fail_on_blocked and status == "BLOCKED_DISPOSITION_REVIEW":
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
