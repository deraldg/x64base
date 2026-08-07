#!/usr/bin/env python3
"""
cmdhelpchk_phase2_warning_classifier_v0.py

REPORT_ONLY / WARNING_CLASSIFIER_ONLY probe for CMDHELPCHK Phase 2.

Run from:
    D:\code\ccode

Reads:
    dottalkpp\docs\generated\reports\cmdhelpchk_phase2_crosswalk_v0.csv
    dottalkpp\docs\generated\reports\cmdhelpchk_phase2_crosswalk_v0.json

Writes:
    dottalkpp\docs\generated\reports\cmdhelpchk_phase2_warning_classifier_v0.md
    dottalkpp\docs\generated\reports\cmdhelpchk_phase2_warning_classifier_v0.csv
    dottalkpp\docs\generated\reports\cmdhelpchk_phase2_warning_classifier_v0.json
    dottalkpp\docs\generated\reports\cmdhelpchk_phase2_warning_classifier_priority_v0.md

Purpose:
    Classify CMDHELPCHK Phase 2 crosswalk warnings into source, HELP artifact,
    metadata, documentation, stale evidence, intentional exception, and policy-review
    lanes before any HELP DATA rebuild, CMDHELPCHK mutation, source repair,
    or v1.1 default promotion.

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

CROSSWALK_CSV = REPORT_DIR / "cmdhelpchk_phase2_crosswalk_v0.csv"
CROSSWALK_JSON = REPORT_DIR / "cmdhelpchk_phase2_crosswalk_v0.json"

OUT_MD = REPORT_DIR / "cmdhelpchk_phase2_warning_classifier_v0.md"
OUT_CSV = REPORT_DIR / "cmdhelpchk_phase2_warning_classifier_v0.csv"
OUT_JSON = REPORT_DIR / "cmdhelpchk_phase2_warning_classifier_v0.json"
OUT_PRIORITY_MD = REPORT_DIR / "cmdhelpchk_phase2_warning_classifier_priority_v0.md"


@dataclass
class ClassifiedWarningRow:
    path: str
    token: str
    surface_kind: str
    original_crosswalk_lane: str
    original_warning_class: str
    action_class: str
    source_contract_status: str
    malformed: bool
    help_artifact_count: int
    authority_state: str
    source_repair_recommended: bool
    phase2_lane: str
    phase2_policy_family: str
    priority: str
    confidence: str
    requires_human_review: bool
    allows_source_repair: bool
    allows_dbf_write: bool
    allows_help_rebuild: bool
    recommended_next_action: str
    rationale: str


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


def classify(row: dict[str, str]) -> ClassifiedWarningRow:
    path = row.get("path", "")
    token = row.get("token", "")
    surface_kind = row.get("surface_kind", "")
    original_lane = row.get("crosswalk_lane", "")
    warning = row.get("warning_class", "")
    action = row.get("action_class", "")
    status = row.get("source_contract_status", "")
    malformed = b(row.get("malformed", False))
    help_count = i(row.get("help_artifact_count", 0))
    authority = row.get("authority_state", "")
    source_repair = b(row.get("source_repair_recommended", False))

    p = path.lower()

    phase2_lane = "POLICY_REVIEW"
    family = "unclassified_policy_review"
    priority = "MEDIUM"
    confidence = "MEDIUM"
    human = True
    next_action = "Review in policy lane before any mutation."
    rationale = "Default policy-review classification."

    if source_repair:
        phase2_lane = "STOP_UNAUTHORIZED_SOURCE_REPAIR"
        family = "source_repair_guard"
        priority = "CRITICAL"
        confidence = "HIGH"
        human = True
        next_action = "Stop and inspect why any report recommends source repair."
        rationale = "No CMDHELPCHK Phase 2 report may authorize source repair from classification alone."

    elif warning == "INFRASTRUCTURE_NOT_SIMPLE_COMMAND" or original_lane == "INTENTIONAL_EXCEPTION":
        phase2_lane = "INTENTIONAL_EXCEPTION"
        family = "command_infrastructure_or_helper"
        priority = "LOW"
        confidence = "HIGH"
        human = False
        next_action = "Keep in alternate contract/helper lane; do not require simple command HELP row."
        rationale = "Infrastructure, registry, dispatcher, helper, or shell core is not an ordinary user command."

    elif warning == "STALE_EVIDENCE" or original_lane == "STALE_EVIDENCE":
        phase2_lane = "STALE_EVIDENCE"
        family = "evidence_freshness"
        priority = "HIGH"
        confidence = "HIGH"
        human = True
        next_action = "Refresh evidence or explain hash/source freshness before promotion or repair."
        rationale = "Stale evidence is not a source defect and remains do-not-repair."

    elif warning == "NO_HELP_ARTIFACT_MATCH_FOUND" or original_lane == "HELP_ARTIFACT_REVIEW":
        phase2_lane = "HELP_ARTIFACT_REVIEW"
        family = "generated_help_artifact_coverage"
        priority = "HIGH"
        confidence = "HIGH"
        human = True
        next_action = "Check generated HELP/DOTHELP/CMDHELP artifact naming or coverage; do not edit source."
        rationale = "Accepted source contract exists, but the crosswalk did not find matching generated HELP artifact evidence."

    elif warning == "FAMILY_USAGE_CONTRACT_BACKLOG" or action == "action_required_add_command_family_usage_contract":
        phase2_lane = "POLICY_REVIEW"
        family = "command_family_usage_contract_backlog"
        priority = "HIGH"
        confidence = "HIGH"
        human = True
        next_action = "Plan family-level usage contract; do not patch automatically."
        rationale = "Command-family/app subsystem contracts require human scope decision."

    elif warning == "MALFORMED_OR_SHAPE_REVIEW" or malformed or action == "review_existing_command_contract_shape":
        phase2_lane = "SOURCE_CONTRACT_SHAPE_REVIEW"
        family = "shape_review_not_repair"
        priority = "MEDIUM"
        confidence = "MEDIUM"
        human = True
        next_action = "Route to shape-review planning; source repair remains unauthorized."
        rationale = "Shape-review warning requires classification before any patch proposal."

    elif action == "alternate_contract_engine" or "/xbase/" in p or "/xindex/" in p or "/cdx/" in p or "/memo/" in p or "/tuple/" in p:
        phase2_lane = "METADATA_OR_ENGINE_CONTRACT_REVIEW"
        family = "engine_or_storage_contract_family"
        priority = "MEDIUM"
        confidence = "MEDIUM"
        human = True
        next_action = "Assign or confirm engine/storage contract family; do not require command HELP row."
        rationale = "Engine/storage files should not be flattened into simple command HELP obligations."

    elif action == "alternate_contract_ui" or "/tv/" in p or "/dli/" in p or "browse" in p or "browser" in p:
        phase2_lane = "UI_OR_BROWSER_CONTRACT_REVIEW"
        family = "ui_browser_contract_family"
        priority = "MEDIUM"
        confidence = "MEDIUM"
        human = True
        next_action = "Assign UI/browser contract family or exclude from command HELP crosswalk."
        rationale = "UI/browser surfaces need a different contract family than simple command HELP."

    elif action == "alternate_contract_api_or_exclude" or p.startswith("include/"):
        phase2_lane = "API_OR_HEADER_CONTRACT_REVIEW"
        family = "api_header_or_declaration_contract"
        priority = "MEDIUM"
        confidence = "MEDIUM"
        human = True
        next_action = "Confirm API/header contract family or exclusion rule."
        rationale = "Headers and API declarations should not be assumed to own user HELP entries."

    elif action == "manual_classification":
        phase2_lane = "MANUAL_CLASSIFICATION"
        family = "manual_classification_backlog"
        priority = "MEDIUM"
        confidence = "HIGH"
        human = True
        next_action = "Classify as command, helper, engine, UI, test, generated, or exclusion in a later pass."
        rationale = "Inventory already marked the row as requiring manual classification."

    elif any(part in p for part in ["/test", "/tests", "/smoke", "/probe", "/probes"]):
        phase2_lane = "TEST_OR_PROBE_CONTRACT_REVIEW"
        family = "test_probe_or_diagnostic"
        priority = "LOW"
        confidence = "MEDIUM"
        human = True
        next_action = "Assign test/probe contract family or exclude from command HELP crosswalk."
        rationale = "Test/probe files are not ordinary HELP command surfaces."

    elif surface_kind == "command_adjacent":
        phase2_lane = "COMMAND_ADJACENT_POLICY_REVIEW"
        family = "command_adjacent_unknown"
        priority = "MEDIUM"
        confidence = "LOW"
        human = True
        next_action = "Refine command-adjacent classification rules."
        rationale = "Command-adjacent row remains too broad for a mutation decision."

    elif help_count > 0 and status == "accepted":
        phase2_lane = "CONFIRMED"
        family = "source_contract_with_help_artifact"
        priority = "LOW"
        confidence = "HIGH"
        human = False
        next_action = "No action."
        rationale = "Accepted source contract has matching HELP-like artifact evidence."

    return ClassifiedWarningRow(
        path=path,
        token=token,
        surface_kind=surface_kind,
        original_crosswalk_lane=original_lane,
        original_warning_class=warning,
        action_class=action,
        source_contract_status=status,
        malformed=malformed,
        help_artifact_count=help_count,
        authority_state=authority,
        source_repair_recommended=source_repair,
        phase2_lane=phase2_lane,
        phase2_policy_family=family,
        priority=priority,
        confidence=confidence,
        requires_human_review=human,
        allows_source_repair=False,
        allows_dbf_write=False,
        allows_help_rebuild=False,
        recommended_next_action=next_action,
        rationale=rationale,
    )


def write_csv(path: Path, rows: list[ClassifiedWarningRow]) -> None:
    fieldnames = list(asdict(rows[0]).keys()) if rows else []
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(asdict(row))


def write_md(path: Path, summary: dict[str, Any], rows: list[ClassifiedWarningRow]) -> None:
    lines = [
        "# CMDHELPCHK Phase 2 Warning Classifier v0",
        "",
        f"Generated UTC: `{summary['generated_at_utc']}`",
        "",
        "Safety class: `REPORT_ONLY / WARNING_CLASSIFIER_ONLY`",
        "",
        "## Verdict",
        "",
        "```text",
        f"classifier status: {summary['classifier_status']}",
        f"rows reviewed: {summary['rows_reviewed']}",
        f"source_repair_recommended: {summary['source_repair_recommended']}",
        f"critical_stop_count: {summary['critical_stop_count']}",
        "CMDHELPCHK changes: NOT AUTHORIZED",
        "HELP DATA rebuild: NOT AUTHORIZED",
        "DBF writes: NOT AUTHORIZED",
        "source repairs: NOT AUTHORIZED",
        "v1.1 default promotion: NOT AUTHORIZED",
        "```",
        "",
        "## Phase 2 lane counts",
        "",
        "| Lane | Count |",
        "|---|---:|",
    ]
    for lane, count in summary["phase2_lane_counts"].items():
        lines.append(f"| `{md_escape(lane)}` | {count} |")

    lines += [
        "",
        "## Policy-family counts",
        "",
        "| Family | Count |",
        "|---|---:|",
    ]
    for family, count in summary["policy_family_counts"].items():
        lines.append(f"| `{md_escape(family)}` | {count} |")

    lines += [
        "",
        "## Priority counts",
        "",
        "| Priority | Count |",
        "|---|---:|",
    ]
    for priority, count in summary["priority_counts"].items():
        lines.append(f"| `{md_escape(priority)}` | {count} |")

    lines += [
        "",
        "## High-priority rows",
        "",
        "| Token | Path | Lane | Family | Warning | Next action |",
        "|---|---|---|---|---|---|",
    ]
    high_rows = [r for r in rows if r.priority in {"CRITICAL", "HIGH"}]
    for row in high_rows[:120]:
        lines.append(
            f"| `{md_escape(row.token)}` | `{md_escape(row.path)}` | `{md_escape(row.phase2_lane)}` | "
            f"`{md_escape(row.phase2_policy_family)}` | `{md_escape(row.original_warning_class)}` | "
            f"{md_escape(row.recommended_next_action)} |"
        )
    if len(high_rows) > 120:
        lines.append(f"| ... | ... | ... | ... | ... | `{len(high_rows) - 120} additional high-priority rows omitted; see CSV/JSON.` |")

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


def write_priority_md(path: Path, summary: dict[str, Any], rows: list[ClassifiedWarningRow]) -> None:
    lines = [
        "# CMDHELPCHK Phase 2 Warning Classifier Priority View v0",
        "",
        "## Immediate review lanes",
        "",
    ]
    for lane in [
        "STOP_UNAUTHORIZED_SOURCE_REPAIR",
        "STALE_EVIDENCE",
        "HELP_ARTIFACT_REVIEW",
        "POLICY_REVIEW",
        "SOURCE_CONTRACT_SHAPE_REVIEW",
    ]:
        lane_rows = [r for r in rows if r.phase2_lane == lane]
        if not lane_rows:
            continue
        lines += [
            f"## {lane}",
            "",
            f"Count: `{len(lane_rows)}`",
            "",
            "| Token | Path | Family | Priority | Next action |",
            "|---|---|---|---|---|",
        ]
        for row in lane_rows[:80]:
            lines.append(
                f"| `{md_escape(row.token)}` | `{md_escape(row.path)}` | `{md_escape(row.phase2_policy_family)}` | "
                f"`{md_escape(row.priority)}` | {md_escape(row.recommended_next_action)} |"
            )
        if len(lane_rows) > 80:
            lines.append(f"| ... | ... | ... | ... | `{len(lane_rows) - 80} additional rows omitted; see CSV/JSON.` |")
        lines.append("")
    lines += [
        "## Safety reminder",
        "",
        "```text",
        "This classifier is report-only.",
        "It does not authorize source repair.",
        "It does not authorize DBF writes.",
        "It does not authorize HELP DATA rebuild.",
        "It does not authorize CMDHELPCHK mutation.",
        "```",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    (root / REPORT_DIR).mkdir(parents=True, exist_ok=True)

    crosswalk_rows = read_csv_rows(root / CROSSWALK_CSV)
    crosswalk_json = read_json(root / CROSSWALK_JSON)
    crosswalk_summary = crosswalk_json.get("summary", {}) if isinstance(crosswalk_json.get("summary", {}), dict) else {}

    rows = [classify(row) for row in crosswalk_rows]

    lane_counts = Counter(row.phase2_lane for row in rows)
    family_counts = Counter(row.phase2_policy_family for row in rows)
    priority_counts = Counter(row.priority for row in rows)
    confidence_counts = Counter(row.confidence for row in rows)

    source_repair_count = sum(1 for row in rows if row.source_repair_recommended)
    critical_stop_count = sum(1 for row in rows if row.phase2_lane == "STOP_UNAUTHORIZED_SOURCE_REPAIR")

    if not crosswalk_rows:
        status = "HOLD_NO_CROSSWALK_INPUT"
        next_action = "Run cmdhelpchk_phase2_crosswalk_probe_v0 first."
    elif critical_stop_count:
        status = "STOP_REVIEW_REQUIRED"
        next_action = "Review unauthorized source-repair recommendations before continuing."
    else:
        status = "REPORT_ONLY_WARNING_CLASSIFICATION_GENERATED"
        next_action = "Build `cmdhelpchk_phase2_canary_plan_v0` using these classified warning lanes."

    summary = {
        "generated_at_utc": now(),
        "status": "REPORT_ONLY_WARNING_CLASSIFIER_GENERATED",
        "classifier_status": status,
        "rows_reviewed": len(rows),
        "crosswalk_status": crosswalk_summary.get("crosswalk_status", ""),
        "source_contract_inventory_version": crosswalk_summary.get("source_contract_inventory_version", ""),
        "source_repair_recommended": source_repair_count,
        "critical_stop_count": critical_stop_count,
        "phase2_lane_counts": dict(lane_counts.most_common()),
        "policy_family_counts": dict(family_counts.most_common()),
        "priority_counts": dict(priority_counts.most_common()),
        "confidence_counts": dict(confidence_counts.most_common()),
        "human_review_required": sum(1 for row in rows if row.requires_human_review),
        "source_repair_authorized": False,
        "dbf_writes_authorized": False,
        "help_data_rebuild_authorized": False,
        "cmdhelpchk_changes_authorized": False,
        "v1_1_default_promotion_authorized": False,
        "interpretation": "This classifier narrows crosswalk warnings into review lanes. Large policy-review counts are expected because the crosswalk intentionally considers all 899 source-contract inventory rows, not only ordinary user command files. The classifier provides visibility and sequencing only; it does not authorize mutation.",
        "recommended_next_action": next_action,
        "inputs_checked": [
            {"path": str(root / CROSSWALK_CSV), "state": "present" if (root / CROSSWALK_CSV).is_file() else "missing"},
            {"path": str(root / CROSSWALK_JSON), "state": "present" if (root / CROSSWALK_JSON).is_file() else "missing"},
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
    (root / OUT_JSON).write_text(json.dumps({"summary": summary, "rows": [asdict(r) for r in rows]}, indent=2), encoding="utf-8")
    write_md(root / OUT_MD, summary, rows)
    write_priority_md(root / OUT_PRIORITY_MD, summary, rows)

    print("CMDHELPCHK Phase 2 warning classifier v0 complete.")
    print(f"Classifier status: {status}")
    print(f"Rows reviewed: {len(rows)}")
    print(f"Source repair recommended: {source_repair_count}")
    print(f"Critical stop count: {critical_stop_count}")
    print(f"Wrote: {OUT_MD}")
    print(f"Wrote: {OUT_CSV}")
    print(f"Wrote: {OUT_JSON}")
    print(f"Wrote: {OUT_PRIORITY_MD}")
    print("No DotTalk++ src/include files were edited.")
    print("No DBFs were written.")
    print("HELP DATA was not rebuilt.")
    print("CMDHELPCHK was not modified.")
    print("v1.1 was not promoted to default.")

    return 0 if status != "STOP_REVIEW_REQUIRED" and status != "HOLD_NO_CROSSWALK_INPUT" else 2


if __name__ == "__main__":
    raise SystemExit(main())
