#!/usr/bin/env python3
"""
source_contract_hotfix_004_integration_validation.py

REPORT_ONLY validation for integrated hotfix 004.

Run after:
  python selfdoc\probes\source_contract_inventory_probe_v1_1.py
  python selfdoc\probes\source_contract_inventory_v1_1_classifier_gap_review.py
  python selfdoc\probes\source_contract_capture_hotfix_002_evidence_lanes.py

Reads:
  dottalkpp\docs\generated\reports\source_contracts_inventory_v1_1.csv
  dottalkpp\docs\generated\reports\source_contracts_inventory_v1_1.json
  dottalkpp\docs\generated\reports\source_contract_capture_hotfix_002_evidence_lanes.csv

Writes:
  dottalkpp\docs\generated\reports\source_contract_hotfix_004_integration_validation.md
  dottalkpp\docs\generated\reports\source_contract_hotfix_004_integration_validation.csv
  dottalkpp\docs\generated\reports\source_contract_hotfix_004_integration_validation.json

Safety:
  No DotTalk++ source edits.
  No DBF writes.
  No HELP DATA rebuild.
  No CMDHELPCHK changes.
  No source repairs.
  No v1.1 default promotion.
"""

from __future__ import annotations

import csv
import json
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPORT_DIR = Path("dottalkpp") / "docs" / "generated" / "reports"
INV_CSV = REPORT_DIR / "source_contracts_inventory_v1_1.csv"
INV_JSON = REPORT_DIR / "source_contracts_inventory_v1_1.json"
LANES_CSV = REPORT_DIR / "source_contract_capture_hotfix_002_evidence_lanes.csv"

OUT_MD = REPORT_DIR / "source_contract_hotfix_004_integration_validation.md"
OUT_CSV = REPORT_DIR / "source_contract_hotfix_004_integration_validation.csv"
OUT_JSON = REPORT_DIR / "source_contract_hotfix_004_integration_validation.json"

BATCH0_NINE = [
    "src/cli/cmd_area.cpp",
    "src/cli/cmd_calcwrite.cpp",
    "src/cli/cmd_close.cpp",
    "src/cli/cmd_color.cpp",
    "src/cli/cmd_commit.cpp",
    "src/cli/cmd_copy.cpp",
    "src/cli/cmd_dir.cpp",
    "src/cli/cmd_foxhelp.cpp",
    "src/cli/cmd_list_lmdb.cpp",
]
CMD_HELP = "src/cli/cmd_help.cpp"


@dataclass
class ValidationRow:
    path: str
    row_present: bool
    malformed: bool
    action_class: str
    status: str
    evidence_lane: str
    secondary_lane: str
    source_repair_recommended: bool
    expected_state_met: bool
    validation_lane: str
    recommended_next_action: str


def b(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes", "y"}


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


def index_by_path(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    return {row.get("path", "").replace("\\", "/"): row for row in rows if row.get("path", "")}


def md_escape(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def validate_path(path: str, inv: dict[str, str], lanes: dict[str, str]) -> ValidationRow:
    malformed = b(inv.get("malformed", False))
    action_class = inv.get("action_class", "")
    status = inv.get("status", "")
    evidence_lane = inv.get("evidence_lane", lanes.get("evidence_lane", ""))
    secondary_lane = inv.get("secondary_lane", lanes.get("secondary_lane", ""))
    repair = b(inv.get("source_repair_recommended", lanes.get("source_repair_recommended", False)))

    if path in BATCH0_NINE:
        expected = (
            bool(inv)
            and not malformed
            and action_class == "accepted_existing_command_contract"
            and status in {"accepted", "accepted_existing_command_contract", "ok"}
            and evidence_lane in {"CONFIRMED", "accepted", "accepted_existing_command_contract", ""}
            and secondary_lane in {"DO_NOT_REPAIR", ""}
            and not repair
        )
        lane = "CONFIRMED" if expected else "CLASSIFIER_REVIEW"
        next_action = "continue promotion review; no source repair" if expected else "inspect final-row normalization hook and row writer"
    elif path == CMD_HELP:
        expected = (
            bool(inv)
            and evidence_lane == "STALE_EVIDENCE"
            and secondary_lane == "DO_NOT_REPAIR"
            and not repair
        )
        lane = "STALE_EVIDENCE" if expected else "CLASSIFIER_REVIEW"
        next_action = "keep stale-evidence/do-not-repair lane" if expected else "restore cmd_help stale-evidence/do-not-repair lane"
    else:
        expected = False
        lane = "REVIEW"
        next_action = "not a target path"

    return ValidationRow(
        path=path,
        row_present=bool(inv),
        malformed=malformed,
        action_class=action_class,
        status=status,
        evidence_lane=evidence_lane,
        secondary_lane=secondary_lane,
        source_repair_recommended=repair,
        expected_state_met=expected,
        validation_lane=lane,
        recommended_next_action=next_action,
    )


def main() -> int:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    inv_rows = index_by_path(read_csv_rows(INV_CSV))
    lane_rows = index_by_path(read_csv_rows(LANES_CSV))
    inv_json = read_json(INV_JSON)
    inv_summary = inv_json.get("summary", {}) if isinstance(inv_json.get("summary", {}), dict) else {}
    probe_version = inv_summary.get("probe_version", "")

    rows = [validate_path(path, inv_rows.get(path, {}), lane_rows.get(path, {})) for path in BATCH0_NINE + [CMD_HELP]]

    counts = Counter(row.validation_lane for row in rows)
    expected_met = sum(1 for row in rows if row.expected_state_met)
    batch_expected = sum(1 for row in rows if row.path in BATCH0_NINE and row.expected_state_met)
    cmd_help_ok = any(row.path == CMD_HELP and row.expected_state_met for row in rows)
    repair_count = sum(1 for row in rows if row.source_repair_recommended)

    if batch_expected == len(BATCH0_NINE) and cmd_help_ok and repair_count == 0:
        validation_status = "PASSED"
        next_action = "Hotfix 004 integration is validated for target rows. Continue v1.1 promotion review; do not repair source."
    else:
        validation_status = "NOT_PASSED_REVIEW_REQUIRED"
        next_action = "Inspect v1.1 final-row normalization and report writer; do not repair source."

    summary = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "REPORT_ONLY_GENERATED",
        "validation_status": validation_status,
        "inventory_probe_version": probe_version,
        "rows_reviewed": len(rows),
        "expected_state_met": expected_met,
        "batch0_expected_state_met": batch_expected,
        "cmd_help_stale_evidence_do_not_repair": cmd_help_ok,
        "source_repair_recommended": repair_count,
        "validation_lane_counts": dict(counts.most_common()),
        "recommended_next_overall_action": next_action,
        "non_mutation_guards": [
            "did_not_edit_dottalkpp_src_or_include",
            "did_not_write_dbfs",
            "did_not_modify_cmdhelpchk",
            "did_not_rebuild_help_data",
            "did_not_repair_source_headers",
            "did_not_promote_v1_1_to_default",
            "did_not_move_or_delete_project_files",
        ],
    }

    with OUT_CSV.open("w", encoding="utf-8", newline="") as f:
        fieldnames = list(asdict(rows[0]).keys()) if rows else []
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(asdict(row))

    OUT_JSON.write_text(json.dumps({"summary": summary, "rows": [asdict(r) for r in rows]}, indent=2), encoding="utf-8")

    lines = [
        "# Source Contract Hotfix 004 Integration Validation",
        "",
        f"Generated UTC: `{summary['generated_at_utc']}`",
        "",
        "Safety class: `REPORT_ONLY validation`",
        "",
        "## Verdict",
        "",
        "```text",
        f"validation status: {validation_status}",
        f"inventory_probe_version: {probe_version}",
        f"batch0_expected_state_met: {batch_expected}/{len(BATCH0_NINE)}",
        f"cmd_help_stale_evidence_do_not_repair: {cmd_help_ok}",
        f"source_repair_recommended: {repair_count}",
        "source repairs: NOT AUTHORIZED",
        "DBF writes: NOT AUTHORIZED",
        "CMDHELPCHK changes: NOT AUTHORIZED",
        "HELP DATA rebuild: NOT AUTHORIZED",
        "v1.1 default promotion: NOT AUTHORIZED",
        "```",
        "",
        "## Rows",
        "",
        "| Path | Malformed | Action class | Status | Lane | Secondary | Expected | Next action |",
        "|---|---:|---|---|---|---|---:|---|",
    ]
    for row in rows:
        lines.append(
            f"| `{md_escape(row.path)}` | {row.malformed} | `{md_escape(row.action_class)}` | "
            f"`{md_escape(row.status)}` | `{md_escape(row.evidence_lane)}` | "
            f"`{md_escape(row.secondary_lane)}` | {row.expected_state_met} | {md_escape(row.recommended_next_action)} |"
        )
    lines += [
        "",
        "## Recommended next action",
        "",
        next_action,
        "",
        "## Non-mutation confirmation",
        "",
    ]
    for guard in summary["non_mutation_guards"]:
        lines.append(f"- `{guard}`")
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print("SelfDoc hotfix 004 integration validation complete.")
    print(f"Validation status: {validation_status}")
    print(f"Inventory probe version: {probe_version}")
    print(f"Batch 0 expected state: {batch_expected}/{len(BATCH0_NINE)}")
    print(f"cmd_help stale evidence / do not repair: {cmd_help_ok}")
    print(f"Source repair recommended: {repair_count}")
    print(f"Wrote: {OUT_MD}")
    print(f"Wrote: {OUT_CSV}")
    print(f"Wrote: {OUT_JSON}")
    print("No DotTalk++ src/include files were edited.")
    print("No DBFs were written.")
    print("CMDHELPCHK was not modified.")
    print("HELP DATA was not rebuilt.")
    return 0 if validation_status == "PASSED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
