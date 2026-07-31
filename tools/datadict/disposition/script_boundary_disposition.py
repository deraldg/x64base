#!/usr/bin/env python3
"""DD-030 report-only script boundary disposition tool.

Reads a DD-029 artifact disposition run and classifies maintenance package scripts,
especially root-level mdo_* package folders, without mutating the repo.
"""
from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Optional

SCHEMA_VERSION = "dd030.script_boundary_disposition.v0"

SCRIPT_EXTS = {".ps1", ".bat", ".cmd", ".sh", ".py", ".dts"}


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def norm_path(s: str) -> str:
    return (s or "").replace("\\", "/").strip()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        for row in rows:
            w.writerow(row)


def find_dd029_rows(review: Path) -> Path:
    if review.is_file():
        return review
    candidates = [
        review / "dd029_artifact_disposition_rows.csv",
        review / "dd025_classified_review_queue.csv",
        review / "classification" / "dd025_classified_review_queue.csv",
        review / "triage" / "dd026_sample_review_rows.csv",
    ]
    for c in candidates:
        if c.exists():
            return c
    matches = list(review.rglob("dd029_artifact_disposition_rows.csv"))
    if matches:
        return matches[0]
    matches = list(review.rglob("*review*queue*.csv"))
    if matches:
        return matches[0]
    raise FileNotFoundError(f"Could not find DD-029/DD-025 review rows under {review}")


def load_policy(path: Optional[Path]) -> dict:
    if path and path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {
        "package_folder_patterns": ["mdo_*", "MDO-*"],
        "script_extensions": sorted(SCRIPT_EXTS),
        "root_level_mdo_package": {
            "classification": "maintenance_package_evidence",
            "script_disposition": "maintenance_package_script",
            "stable_source_action": "exclude_if_package_evidence_accepted",
            "requires_review": True,
        },
    }


def first_segment(path: str) -> str:
    return norm_path(path).split("/", 1)[0]


def is_root_mdo_package(path: str) -> bool:
    seg = first_segment(path).lower()
    return seg.startswith("mdo_") or seg.startswith("mdo-")


def is_script(path: str) -> bool:
    return Path(norm_path(path)).suffix.lower() in SCRIPT_EXTS


def classify_row(row: dict[str, str]) -> dict[str, object]:
    path = norm_path(row.get("path") or row.get("Path") or row.get("file") or row.get("File") or "")
    disposition = row.get("disposition") or row.get("Disposition") or ""
    severity = row.get("severity") or row.get("Severity") or ""
    lane = row.get("lane") or row.get("Lane") or ""
    change = row.get("change") or row.get("Change") or row.get("change_kind") or row.get("ChangeKind") or ""

    package_id = first_segment(path) if is_root_mdo_package(path) else ""
    script = is_script(path)

    if package_id and script:
        boundary_class = "ROOT_MDO_PACKAGE_SCRIPT"
        proposed_disposition = "MAINTENANCE_PACKAGE_SCRIPT"
        stable_source_action = "EXCLUDE_FROM_STABLE_SOURCE_IF_PACKAGE_EVIDENCE_ACCEPTED"
        required_action = "Review package as generated/temporary/accepted maintenance evidence; do not treat as product source until promoted."
        blocks_baseline = "1"
    elif package_id:
        boundary_class = "ROOT_MDO_PACKAGE_EVIDENCE"
        proposed_disposition = "MAINTENANCE_PACKAGE_EVIDENCE"
        stable_source_action = "EXCLUDE_FROM_STABLE_SOURCE_IF_PACKAGE_EVIDENCE_ACCEPTED"
        required_action = "Review package evidence; archive/exclude/promote deliberately."
        blocks_baseline = "0"
    elif path.startswith("tools/datadict/"):
        boundary_class = "DATADICT_TOOL"
        proposed_disposition = "DATADICT_TOOLING_CHANGE"
        stable_source_action = "INCLUDE_AFTER_TOOL_SMOKE"
        required_action = "Run tool help/smoke and confirm report-only boundary."
        blocks_baseline = "0"
    elif path.startswith("docs/datadict/"):
        boundary_class = "DATADICT_EVIDENCE"
        proposed_disposition = "DATADICT_LANE_CHANGE"
        stable_source_action = "INCLUDE_AFTER_DATADICT_SELF_REVIEW"
        required_action = "Review as Data Dictionary self-change."
        blocks_baseline = "0"
    elif path.startswith("docs/manuals/developer/manualgen/"):
        boundary_class = "MANUALGEN_EVIDENCE"
        proposed_disposition = "MANUALGEN_REPORT_EVIDENCE"
        stable_source_action = "INCLUDE_AFTER_MANUALGEN_REVIEW"
        required_action = "Review manualgen impact and publication gate."
        blocks_baseline = "0"
    elif path == "docs/MDO_SAVEPOINT_JOURNAL.md" or "SAVEPOINT" in path.upper():
        boundary_class = "SAVEPOINT_EVIDENCE"
        proposed_disposition = "RUNLOG_OR_SAVEPOINT_EVIDENCE"
        stable_source_action = "INCLUDE_AS_EVIDENCE_ARTIFACT"
        required_action = "Preserve as run/savepoint evidence."
        blocks_baseline = "0"
    else:
        boundary_class = "HUMAN_TRIAGE"
        proposed_disposition = disposition or "HUMAN_TRIAGE_REQUIRED"
        stable_source_action = "REVIEW_REQUIRED"
        required_action = "Human review required; no automatic baseline acceptance."
        blocks_baseline = "1" if severity.upper() == "HIGH" else "0"

    return {
        "path": path,
        "change": change,
        "source_severity": severity,
        "source_lane": lane,
        "source_disposition": disposition,
        "package_id": package_id,
        "is_script": "1" if script else "0",
        "boundary_class": boundary_class,
        "proposed_disposition": proposed_disposition,
        "stable_source_action": stable_source_action,
        "required_action": required_action,
        "blocks_baseline": blocks_baseline,
    }


def markdown_table(rows: list[dict[str, object]], headers: list[str]) -> str:
    if not rows:
        return "(none)\n"
    out = []
    out.append("| " + " | ".join(headers) + " |")
    out.append("|" + "|".join(["---" for _ in headers]) + "|")
    for r in rows:
        out.append("| " + " | ".join(str(r.get(h, "")) for h in headers) + " |")
    return "\n".join(out) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description="DD-030 report-only script boundary disposition")
    ap.add_argument("--dd029", required=True, help="DD-029 disposition directory or rows CSV")
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--run-id", default="DD030-script-boundary-disposition")
    ap.add_argument("--policy")
    ap.add_argument("--profile", action="append", default=[])
    ap.add_argument("--accept-package-evidence", action="store_true", help="Mark root MDO package scripts as accepted evidence for this report; still no mutation")
    ap.add_argument("--fail-on-blocked", action="store_true")
    args = ap.parse_args()

    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    dd029_path = find_dd029_rows(Path(args.dd029))
    policy = load_policy(Path(args.policy) if args.policy else None)
    rows_in = read_csv(dd029_path)
    rows = [classify_row(r) for r in rows_in]

    if args.accept_package_evidence:
        for r in rows:
            if r["boundary_class"] == "ROOT_MDO_PACKAGE_SCRIPT":
                r["blocks_baseline"] = "0"
                r["stable_source_action"] = "EXCLUDE_FROM_STABLE_SOURCE_AFTER_ACCEPTANCE"
                r["required_action"] = "Accepted as maintenance package evidence for this DD-030 report; implement exclusion/update through separate DD-031 policy step."

    boundary_counter = Counter(r["boundary_class"] for r in rows)
    disposition_counter = Counter(r["proposed_disposition"] for r in rows)
    package_counter = Counter(r["package_id"] for r in rows if r["package_id"])
    blocking = [r for r in rows if str(r.get("blocks_baseline")) == "1"]
    root_scripts = [r for r in rows if r["boundary_class"] == "ROOT_MDO_PACKAGE_SCRIPT"]

    status = "PASS"
    if blocking:
        status = "BLOCKED_SCRIPT_BOUNDARY_REVIEW"
    elif rows:
        status = "REVIEW"

    row_fields = ["path","change","source_severity","source_lane","source_disposition","package_id","is_script","boundary_class","proposed_disposition","stable_source_action","required_action","blocks_baseline"]
    write_csv(out / "dd030_script_boundary_rows.csv", rows, row_fields)
    write_csv(out / "dd030_blocking_script_rows.csv", blocking, row_fields)

    package_rows = [{"package_id": k, "rows": v, "script_rows": sum(1 for r in root_scripts if r["package_id"] == k), "recommended_action": "accept_as_maintenance_package_evidence_or_archive"} for k, v in package_counter.items()]
    write_csv(out / "dd030_package_summary.csv", package_rows, ["package_id","rows","script_rows","recommended_action"])

    summary_rows = [{"boundary_class": k, "count": v, "blocks": sum(1 for r in rows if r["boundary_class"] == k and r["blocks_baseline"] == "1")} for k,v in boundary_counter.items()]
    write_csv(out / "dd030_boundary_summary.csv", summary_rows, ["boundary_class","count","blocks"])

    next_actions = [
        {"priority": 1, "action": "Review root-level MDO package scripts as maintenance package evidence, not product source.", "condition": "root_mdo_package_scripts_present", "count": len(root_scripts)},
        {"priority": 2, "action": "If accepted, use DD-031 to patch stable exclusion policy; do not manually hide files without ledger.", "condition": "package_evidence_accepted", "count": len(root_scripts)},
        {"priority": 3, "action": "Rerun DD-028 after policy update and accept DDBASE-stable-v1 only after clean pass.", "condition": "post_dd031", "count": 1},
    ]
    write_csv(out / "dd030_next_actions.csv", next_actions, ["priority","action","condition","count"])

    exclusion_patch = {
        "schema_version": "dd030.exclusion_policy_patch_proposal.v0",
        "run_id": args.run_id,
        "status": "PROPOSAL_ONLY",
        "requires_dd031": True,
        "accepted_package_evidence": bool(args.accept_package_evidence),
        "proposed_exclusions": sorted({f"{pkg}/" for pkg in package_counter if pkg.lower().startswith("mdo_") or pkg.lower().startswith("mdo-")}),
        "inventory_lane": "maintenance_artifact_inventory",
        "notes": "Do not apply automatically. DD-031 should update scanner policy only after human acceptance."
    }
    (out / "dd030_exclusion_policy_patch_proposal.json").write_text(json.dumps(exclusion_patch, indent=2), encoding="utf-8")

    manifest = {
        "schema_version": SCHEMA_VERSION,
        "run_id": args.run_id,
        "created_utc": now_utc(),
        "status": status,
        "profiles": args.profile,
        "inputs": {"dd029_rows": str(dd029_path), "policy": args.policy or "embedded_default"},
        "summary": {
            "review_rows": len(rows),
            "root_mdo_package_scripts": len(root_scripts),
            "blocking_rows": len(blocking),
            "packages": len(package_counter),
            "boundary_classes": len(boundary_counter),
        },
        "boundary": {
            "report_only": True,
            "source_edits": 0,
            "build": 0,
            "runtime_launch": 0,
            "help_meta_cmdhelpchk_mutation": 0,
            "dbf_cdx_lmdb_catalog_mutation": 0,
            "baseline_acceptance": 0,
        },
        "outputs": {
            "rows_csv": "dd030_script_boundary_rows.csv",
            "blocking_csv": "dd030_blocking_script_rows.csv",
            "package_summary_csv": "dd030_package_summary.csv",
            "exclusion_policy_patch_proposal": "dd030_exclusion_policy_patch_proposal.json",
            "report": "DD030_SCRIPT_BOUNDARY_REPORT.md",
        }
    }
    (out / "dd030_script_boundary_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    report = []
    report.append("# DD-030 Script Boundary Disposition Report\n")
    report.append(f"Run id: `{args.run_id}`  \n")
    report.append(f"Status: **{status}**  \n")
    report.append(f"Created UTC: `{manifest['created_utc']}`\n")
    report.append("## Summary\n")
    report.append(f"- Review rows examined: {len(rows)}\n")
    report.append(f"- Root MDO package script rows: {len(root_scripts)}\n")
    report.append(f"- Blocking rows: {len(blocking)}\n")
    report.append(f"- Package folders observed: {len(package_counter)}\n")
    report.append(f"- Boundary classes: {len(boundary_counter)}\n")
    report.append("\n## Boundary summary\n")
    report.append(markdown_table(summary_rows, ["boundary_class", "count", "blocks"]))
    report.append("\n## Package summary\n")
    report.append(markdown_table(package_rows[:30], ["package_id", "rows", "script_rows", "recommended_action"]))
    report.append("\n## Blocking rows sample\n")
    report.append(markdown_table(blocking[:25], ["source_severity", "boundary_class", "path", "stable_source_action"]))
    report.append("\n## Recommended next actions\n")
    report.append(markdown_table(next_actions, ["priority", "action", "condition", "count"]))
    report.append("\n## Boundary\n")
    report.append("DD-030 is report-only. It does not edit source, run scripts, launch DotTalk++, mutate HELP/META/CMDHELPCHK, write DBF/CDX/LMDB/catalog data, or accept a baseline.\n")
    (out / "DD030_SCRIPT_BOUNDARY_REPORT.md").write_text("\n".join(report), encoding="utf-8")

    print(f"DD-030 script boundary manifest: {out / 'dd030_script_boundary_manifest.json'}")
    print(f"status: {status}; rows: {len(rows)}; root_mdo_scripts: {len(root_scripts)}; blocking: {len(blocking)}; packages: {len(package_counter)}")
    if args.fail_on_blocked and status.startswith("BLOCKED"):
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
