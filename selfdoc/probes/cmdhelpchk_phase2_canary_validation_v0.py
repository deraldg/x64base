#!/usr/bin/env python3
"""
cmdhelpchk_phase2_canary_validation_v0.py

REPORT_ONLY / CANARY_VALIDATION_ONLY probe for CMDHELPCHK Phase 2.

Run from:
    D:\code\ccode

Reads:
    dottalkpp\docs\generated\reports\cmdhelpchk_phase2_canary_plan_v0.csv
    dottalkpp\docs\generated\reports\cmdhelpchk_phase2_canary_plan_v0.json
    dottalkpp\docs\generated\reports\cmdhelpchk_phase2_warning_classifier_v0.json
    dottalkpp\docs\generated\reports\cmdhelpchk_phase2_warning_classifier_v0.csv

Writes:
    dottalkpp\docs\generated\reports\cmdhelpchk_phase2_canary_validation_v0.md
    dottalkpp\docs\generated\reports\cmdhelpchk_phase2_canary_validation_v0.csv
    dottalkpp\docs\generated\reports\cmdhelpchk_phase2_canary_validation_v0.json

Purpose:
    Validate the canary plan itself before moving to promotion-gate planning.
    This does not execute runtime canaries. It checks whether the planned canaries
    preserve mutation guards, cover the high-priority lanes, and keep the next
    work in report-only territory.

Safety:
    No DotTalk++ src/include edits.
    No source header repairs.
    No DBF writes.
    No HELP DATA rebuild.
    No CMDHELPCHK changes.
    No v1.1 source-contract default promotion.
    No project file moves/deletes.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPORT_DIR = Path("dottalkpp") / "docs" / "generated" / "reports"

CANARY_PLAN_CSV = REPORT_DIR / "cmdhelpchk_phase2_canary_plan_v0.csv"
CANARY_PLAN_JSON = REPORT_DIR / "cmdhelpchk_phase2_canary_plan_v0.json"
CLASSIFIER_JSON = REPORT_DIR / "cmdhelpchk_phase2_warning_classifier_v0.json"
CLASSIFIER_CSV = REPORT_DIR / "cmdhelpchk_phase2_warning_classifier_v0.csv"

OUT_MD = REPORT_DIR / "cmdhelpchk_phase2_canary_validation_v0.md"
OUT_CSV = REPORT_DIR / "cmdhelpchk_phase2_canary_validation_v0.csv"
OUT_JSON = REPORT_DIR / "cmdhelpchk_phase2_canary_validation_v0.json"

REQUIRED_CANARY_IDS = [
    "CMDHELPCHK-P2-CANARY-001",
    "CMDHELPCHK-P2-CANARY-002",
    "CMDHELPCHK-P2-CANARY-003",
    "CMDHELPCHK-P2-CANARY-004",
    "CMDHELPCHK-P2-CANARY-005",
    "CMDHELPCHK-P2-CANARY-006",
    "CMDHELPCHK-P2-CANARY-007",
]


@dataclass
class ValidationRow:
    check_id: str
    check_name: str
    status: str
    priority: str
    evidence: str
    expected: str
    actual: str
    recommendation: str
    mutation_authorized: bool


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def b(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes", "y"}


def i(value: Any) -> int:
    try:
        return int(str(value).strip())
    except Exception:
        return 0


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        return []
    with path.open("r", encoding="utf-8", newline="") as f:
        return [dict(row) for row in csv.DictReader(f)]


def read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"_read_error": f"{type(exc).__name__}: {exc}"}


def md_escape(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def add_check(rows: list[ValidationRow], check_id: str, check_name: str, ok: bool, priority: str, evidence: str, expected: str, actual: str, recommendation: str, status_if_fail: str = "FAIL") -> None:
    rows.append(ValidationRow(
        check_id=check_id,
        check_name=check_name,
        status="PASS" if ok else status_if_fail,
        priority=priority,
        evidence=evidence,
        expected=expected,
        actual=actual,
        recommendation=recommendation if not ok else "No action.",
        mutation_authorized=False,
    ))


def write_csv(path: Path, rows: list[ValidationRow]) -> None:
    fields = list(asdict(rows[0]).keys()) if rows else []
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow(asdict(row))


def write_md(path: Path, summary: dict[str, Any], rows: list[ValidationRow], canaries: list[dict[str, str]]) -> None:
    lines = [
        "# CMDHELPCHK Phase 2 Canary Validation v0",
        "",
        f"Generated UTC: `{summary['generated_at_utc']}`",
        "",
        "Safety class: `REPORT_ONLY / CANARY_VALIDATION_ONLY`",
        "",
        "## Verdict",
        "",
        "```text",
        f"validation status: {summary['validation_status']}",
        f"canaries reviewed: {summary['canaries_reviewed']}",
        f"validation checks: {summary['validation_checks']}",
        f"failed checks: {summary['failed_checks']}",
        f"warning checks: {summary['warning_checks']}",
        "CMDHELPCHK changes: NOT AUTHORIZED",
        "HELP DATA rebuild: NOT AUTHORIZED",
        "DBF writes: NOT AUTHORIZED",
        "source repairs: NOT AUTHORIZED",
        "v1.1 default promotion: NOT AUTHORIZED",
        "```",
        "",
        "## Validation checks",
        "",
        "| Check | Status | Priority | Expected | Actual | Recommendation |",
        "|---|---|---|---|---|---|",
    ]
    for row in rows:
        lines.append(
            f"| `{md_escape(row.check_name)}` | `{md_escape(row.status)}` | `{md_escape(row.priority)}` | "
            f"{md_escape(row.expected)} | {md_escape(row.actual)} | {md_escape(row.recommendation)} |"
        )

    lines += [
        "",
        "## Canary plan snapshot",
        "",
        "| Canary | Lane | Priority | Status | Rows | Mutation authorized |",
        "|---|---|---|---|---:|---:|",
    ]
    for c in canaries:
        lines.append(
            f"| `{md_escape(c.get('canary_id', ''))}` | `{md_escape(c.get('lane', ''))}` | "
            f"`{md_escape(c.get('priority', ''))}` | `{md_escape(c.get('status', ''))}` | "
            f"{md_escape(c.get('source_rows', ''))} | `{md_escape(c.get('mutation_authorized', ''))}` |"
        )

    lines += [
        "",
        "## Interpretation",
        "",
        summary["interpretation"],
        "",
        "## Recommended next action",
        "",
        summary["recommended_next_action"],
        "",
        "## Non-mutation confirmation",
        "",
    ]
    for guard in summary["non_mutation_guards"]:
        lines.append(f"- `{guard}`")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    (root / REPORT_DIR).mkdir(parents=True, exist_ok=True)

    canary_rows = read_csv_rows(root / CANARY_PLAN_CSV)
    canary_json = read_json(root / CANARY_PLAN_JSON)
    canary_summary = canary_json.get("summary", {}) if isinstance(canary_json.get("summary", {}), dict) else {}

    classifier_json = read_json(root / CLASSIFIER_JSON)
    classifier_summary = classifier_json.get("summary", {}) if isinstance(classifier_json.get("summary", {}), dict) else {}
    classifier_rows = read_csv_rows(root / CLASSIFIER_CSV)

    rows: list[ValidationRow] = []

    canary_ids = {row.get("canary_id", "") for row in canary_rows}
    missing_ids = [cid for cid in REQUIRED_CANARY_IDS if cid not in canary_ids]
    add_check(
        rows,
        "CV-001",
        "required_canary_ids_present",
        not missing_ids and len(canary_rows) >= len(REQUIRED_CANARY_IDS),
        "HIGH",
        "canary_plan_csv",
        "All required canary IDs present.",
        "missing=" + ",".join(missing_ids) if missing_ids else f"present={len(canary_ids)}",
        "Regenerate cmdhelpchk_phase2_canary_plan_v0 before moving to promotion-gate planning.",
    )

    mutation_enabled = [row for row in canary_rows if b(row.get("mutation_authorized", False))]
    add_check(
        rows,
        "CV-002",
        "all_canaries_non_mutating",
        not mutation_enabled,
        "CRITICAL",
        "canary_plan_csv",
        "No canary authorizes mutation.",
        f"mutation_authorized_rows={len(mutation_enabled)}",
        "Stop; canary validation must remain report-only.",
    )

    failing_canaries = [row for row in canary_rows if row.get("status", "") == "FAIL"]
    add_check(
        rows,
        "CV-003",
        "no_failed_canaries",
        not failing_canaries,
        "CRITICAL",
        "canary_plan_csv",
        "No canary status is FAIL.",
        f"failed_canaries={len(failing_canaries)}",
        "Review failed canary before any further Phase 2 build.",
    )

    classifier_source_repair = i(classifier_summary.get("source_repair_recommended", 0))
    add_check(
        rows,
        "CV-004",
        "classifier_source_repair_zero",
        classifier_source_repair == 0,
        "CRITICAL",
        "warning_classifier_summary",
        "source_repair_recommended == 0.",
        f"source_repair_recommended={classifier_source_repair}",
        "Stop; do not proceed while any source repair is recommended.",
    )

    critical_stop = i(classifier_summary.get("critical_stop_count", 0))
    add_check(
        rows,
        "CV-005",
        "classifier_critical_stop_zero",
        critical_stop == 0,
        "CRITICAL",
        "warning_classifier_summary",
        "critical_stop_count == 0.",
        f"critical_stop_count={critical_stop}",
        "Stop; resolve critical stop rows first.",
    )

    lane_counts = classifier_summary.get("phase2_lane_counts", {}) if isinstance(classifier_summary.get("phase2_lane_counts", {}), dict) else {}
    help_artifact_count = int(lane_counts.get("HELP_ARTIFACT_REVIEW", 0) or 0)
    stale_count = int(lane_counts.get("STALE_EVIDENCE", 0) or 0)
    policy_count = int(lane_counts.get("POLICY_REVIEW", 0) or 0)

    add_check(
        rows,
        "CV-006",
        "high_priority_lanes_have_canaries",
        help_artifact_count >= 0 and stale_count >= 0 and policy_count >= 0 and {"CMDHELPCHK-P2-CANARY-002", "CMDHELPCHK-P2-CANARY-003", "CMDHELPCHK-P2-CANARY-004"}.issubset(canary_ids),
        "HIGH",
        "warning_classifier_summary_and_canary_plan",
        "HELP_ARTIFACT_REVIEW, STALE_EVIDENCE, and POLICY_REVIEW are represented by canaries.",
        f"help_artifact={help_artifact_count}; stale={stale_count}; policy={policy_count}",
        "Add or regenerate high-priority lane canaries.",
    )

    source_rows_by_canary = {row.get("canary_id", ""): i(row.get("source_rows", 0)) for row in canary_rows}
    add_check(
        rows,
        "CV-007",
        "expected_high_priority_counts_preserved",
        source_rows_by_canary.get("CMDHELPCHK-P2-CANARY-002", -1) == help_artifact_count
        and source_rows_by_canary.get("CMDHELPCHK-P2-CANARY-003", -1) == stale_count
        and source_rows_by_canary.get("CMDHELPCHK-P2-CANARY-004", -1) == policy_count,
        "MEDIUM",
        "canary_plan_vs_warning_classifier",
        "Canary row counts match classifier lane counts for high-priority lanes.",
        f"canary_HELP_ARTIFACT={source_rows_by_canary.get('CMDHELPCHK-P2-CANARY-002')}; classifier_HELP_ARTIFACT={help_artifact_count}; "
        f"canary_STALE={source_rows_by_canary.get('CMDHELPCHK-P2-CANARY-003')}; classifier_STALE={stale_count}; "
        f"canary_POLICY={source_rows_by_canary.get('CMDHELPCHK-P2-CANARY-004')}; classifier_POLICY={policy_count}",
        "Review count mismatch before using the canary plan as evidence.",
        status_if_fail="WARN",
    )

    # Sanity check broad backlog exists and is not promoted as a blocker.
    broad = source_rows_by_canary.get("CMDHELPCHK-P2-CANARY-007", 0)
    add_check(
        rows,
        "CV-008",
        "broad_backlog_is_classified_not_blocking",
        broad >= 0 and "CMDHELPCHK-P2-CANARY-007" in canary_ids,
        "MEDIUM",
        "canary_plan_csv",
        "Broad backlog has its own canary and does not block focused Phase 2 canaries.",
        f"broad_backlog_rows={broad}",
        "Add broad backlog canary or rerun canary plan.",
        status_if_fail="WARN",
    )

    status_counts = Counter(row.status for row in rows)
    failed = status_counts.get("FAIL", 0)
    warnings = status_counts.get("WARN", 0)

    if not canary_rows:
        validation_status = "HOLD_NO_CANARY_PLAN_INPUT"
        next_action = "Run cmdhelpchk_phase2_canary_plan_v0.py first."
    elif failed:
        validation_status = "STOP_CANARY_VALIDATION_FAILED"
        next_action = "Fix failed canary validation checks before continuing."
    elif warnings:
        validation_status = "PASS_WITH_WARNINGS"
        next_action = "Review warnings, then build `cmdhelpchk_phase2_promotion_gate_v0`."
    else:
        validation_status = "PASS"
        next_action = "Build `cmdhelpchk_phase2_promotion_gate_v0`."

    summary = {
        "generated_at_utc": now(),
        "status": "REPORT_ONLY_CANARY_VALIDATION_GENERATED",
        "validation_status": validation_status,
        "canary_plan_status": canary_summary.get("canary_plan_status", ""),
        "classifier_status": classifier_summary.get("classifier_status", ""),
        "canaries_reviewed": len(canary_rows),
        "classifier_rows_reviewed": len(classifier_rows),
        "validation_checks": len(rows),
        "failed_checks": failed,
        "warning_checks": warnings,
        "check_status_counts": dict(status_counts.most_common()),
        "required_canary_ids": REQUIRED_CANARY_IDS,
        "source_repair_authorized": False,
        "dbf_writes_authorized": False,
        "help_data_rebuild_authorized": False,
        "cmdhelpchk_changes_authorized": False,
        "v1_1_default_promotion_authorized": False,
        "interpretation": "This validation checks the canary plan as an evidence artifact only. It does not execute runtime canaries and does not authorize mutation. Passing means the plan is coherent enough to feed the next report-only promotion-gate planning step.",
        "recommended_next_action": next_action,
        "inputs_checked": [
            {"path": str(root / CANARY_PLAN_CSV), "state": "present" if (root / CANARY_PLAN_CSV).is_file() else "missing"},
            {"path": str(root / CANARY_PLAN_JSON), "state": "present" if (root / CANARY_PLAN_JSON).is_file() else "missing"},
            {"path": str(root / CLASSIFIER_JSON), "state": "present" if (root / CLASSIFIER_JSON).is_file() else "missing"},
            {"path": str(root / CLASSIFIER_CSV), "state": "present" if (root / CLASSIFIER_CSV).is_file() else "missing"},
        ],
        "non_mutation_guards": [
            "did_not_edit_dottalkpp_src_or_include",
            "did_not_apply_source_repair_patches",
            "did_not_write_dbfs",
            "did_not_rebuild_help_data",
            "did_not_modify_cmdhelpchk",
            "did_not_promote_v1_1_to_default",
            "did_not_move_or_delete_project_files",
        ],
    }

    write_csv(root / OUT_CSV, rows)
    (root / OUT_JSON).write_text(json.dumps({"summary": summary, "validation_rows": [asdict(r) for r in rows], "canaries": canary_rows}, indent=2), encoding="utf-8")
    write_md(root / OUT_MD, summary, rows, canary_rows)

    print("CMDHELPCHK Phase 2 canary validation v0 complete.")
    print(f"Validation status: {validation_status}")
    print(f"Canaries reviewed: {len(canary_rows)}")
    print(f"Validation checks: {len(rows)}")
    print(f"Failed checks: {failed}")
    print(f"Warning checks: {warnings}")
    print(f"Wrote: {OUT_MD}")
    print(f"Wrote: {OUT_CSV}")
    print(f"Wrote: {OUT_JSON}")
    print("No DotTalk++ src/include files were edited.")
    print("No DBFs were written.")
    print("HELP DATA was not rebuilt.")
    print("CMDHELPCHK was not modified.")
    print("v1.1 was not promoted to default.")

    return 0 if failed == 0 and canary_rows else 2


if __name__ == "__main__":
    raise SystemExit(main())
