#!/usr/bin/env python3
"""
source_contract_malformed_assignment_hotfix_003_validation.py

REPORT_ONLY / REVIEW_ONLY validation for malformed assignment hotfix 003.

Run after:
  python selfdoc\probes\source_contract_inventory_probe_v1_1.py
  python selfdoc\probes\source_contract_inventory_v1_1_classifier_gap_review.py
  python selfdoc\probes\source_contract_capture_hotfix_002_evidence_lanes.py

Reads:
  dottalkpp\docs\generated\reports\source_contracts_inventory_v1_1.csv
  dottalkpp\docs\generated\reports\source_contracts_inventory_v1_1.json
  dottalkpp\docs\generated\reports\source_contract_capture_hotfix_002_evidence_lanes.csv

Writes:
  dottalkpp\docs\generated\reports\source_contract_malformed_assignment_hotfix_003_validation.md
  dottalkpp\docs\generated\reports\source_contract_malformed_assignment_hotfix_003_validation.csv
  dottalkpp\docs\generated\reports\source_contract_malformed_assignment_hotfix_003_validation.json

Safety:
  No source edits.
  No DBF writes.
  No HELP DATA rebuild.
  No CMDHELPCHK changes.
  No repairs.
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

OUT_MD = REPORT_DIR / "source_contract_malformed_assignment_hotfix_003_validation.md"
OUT_CSV = REPORT_DIR / "source_contract_malformed_assignment_hotfix_003_validation.csv"
OUT_JSON = REPORT_DIR / "source_contract_malformed_assignment_hotfix_003_validation.json"

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


@dataclass
class ValidationRow:
    path: str
    inventory_present: bool
    malformed: bool
    action_class: str
    status: str
    evidence_lane: str = ""
    secondary_lane: str = ""
    source_repair_recommended: bool = False
    expected_state_met: bool = False
    validation_lane: str = ""
    recommended_next_action: str = ""


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


def main() -> int:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    inv = index_by_path(read_csv_rows(INV_CSV))
    lanes = index_by_path(read_csv_rows(LANES_CSV))
    inv_json = read_json(INV_JSON)
    inv_summary = inv_json.get("summary", {}) if isinstance(inv_json.get("summary", {}), dict) else {}
    probe_version = inv_summary.get("probe_version", "")

    rows: list[ValidationRow] = []
    for path in BATCH0_NINE:
        inv_row = inv.get(path, {})
        lane_row = lanes.get(path, {})

        malformed = b(inv_row.get("malformed", False))
        action_class = inv_row.get("action_class", "")
        status = inv_row.get("status", "")
        evidence_lane = lane_row.get("evidence_lane", inv_row.get("evidence_lane", ""))
        secondary_lane = lane_row.get("secondary_lane", inv_row.get("secondary_lane", ""))
        repair_recommended = b(lane_row.get("source_repair_recommended", inv_row.get("source_repair_recommended", False)))

        # Target: no longer malformed solely because of preamble capture, no repair recommended.
        expected = (not malformed) and (not repair_recommended) and action_class != "review_existing_command_contract_shape"

        if expected:
            validation_lane = "CONFIRMED"
            next_action = "no source repair; keep accepted/confirmed classification"
        elif malformed:
            validation_lane = "CLASSIFIER_REVIEW"
            next_action = "malformed flag still present; inspect row hook/classification assignment in v1.1 probe"
        else:
            validation_lane = "POLICY_REVIEW"
            next_action = "malformed cleared but action/status still needs review"

        rows.append(
            ValidationRow(
                path=path,
                inventory_present=bool(inv_row),
                malformed=malformed,
                action_class=action_class,
                status=status,
                evidence_lane=evidence_lane,
                secondary_lane=secondary_lane,
                source_repair_recommended=repair_recommended,
                expected_state_met=expected,
                validation_lane=validation_lane,
                recommended_next_action=next_action,
            )
        )

    # cmd_help evidence lane.
    cmd_help_inv = inv.get("src/cli/cmd_help.cpp", {})
    cmd_help_lane = lanes.get("src/cli/cmd_help.cpp", {})
    cmd_help_ok = cmd_help_lane.get("evidence_lane", "") == "STALE_EVIDENCE" and cmd_help_lane.get("secondary_lane", "") == "DO_NOT_REPAIR"

    validation_counts = Counter(row.validation_lane for row in rows)
    expected_met_count = sum(1 for row in rows if row.expected_state_met)
    source_repair_count = sum(1 for row in rows if row.source_repair_recommended)

    if expected_met_count == len(rows) and cmd_help_ok and source_repair_count == 0:
        validation_status = "PASSED"
        next_overall = "Batch 0 malformed-assignment false positives appear cleared. Continue promotion review; do not repair source."
    elif source_repair_count:
        validation_status = "FAILED_SOURCE_REPAIR_RECOMMENDED"
        next_overall = "Source repair recommendation appeared; stop and inspect classifier logic."
    else:
        validation_status = "NOT_PASSED_CLASSIFIER_REVIEW_REQUIRED"
        next_overall = "Malformed assignment is still not fully cleared. Inspect row hook and action_class assignment in v1.1 probe."

    summary = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "REVIEW_ONLY_GENERATED",
        "validation_status": validation_status,
        "inventory_probe_version": probe_version,
        "rows_reviewed": len(rows),
        "expected_state_met": expected_met_count,
        "classifier_review": validation_counts.get("CLASSIFIER_REVIEW", 0),
        "policy_review": validation_counts.get("POLICY_REVIEW", 0),
        "confirmed": validation_counts.get("CONFIRMED", 0),
        "source_repair_recommended": source_repair_count,
        "cmd_help_stale_evidence_do_not_repair": cmd_help_ok,
        "validation_lane_counts": dict(validation_counts.most_common()),
        "recommended_next_overall_action": next_overall,
        "non_mutation_guards": [
            "did_not_edit_source",
            "did_not_write_dbfs",
            "did_not_modify_cmdhelpchk",
            "did_not_rebuild_help_data",
            "did_not_repair_headers",
            "did_not_promote_v1_1_to_default",
            "did_not_move_or_delete_files",
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
        "# Source Contract Malformed Assignment Hotfix 003 Validation",
        "",
        f"Generated UTC: `{summary['generated_at_utc']}`",
        "",
        "Safety class: `REPORT_ONLY / REVIEW_ONLY`",
        "",
        "## Verdict",
        "",
        "```text",
        f"validation status: {validation_status}",
        f"inventory_probe_version: {probe_version}",
        f"expected_state_met: {expected_met_count}/{len(rows)}",
        f"source_repair_recommended: {source_repair_count}",
        f"cmd_help_stale_evidence_do_not_repair: {cmd_help_ok}",
        "source repairs: NOT AUTHORIZED",
        "DBF writes: NOT AUTHORIZED",
        "CMDHELPCHK changes: NOT AUTHORIZED",
        "HELP DATA rebuild: NOT AUTHORIZED",
        "```",
        "",
        "## Rows",
        "",
        "| Path | Malformed | Action class | Validation lane | Expected met | Next action |",
        "|---|---:|---|---|---:|---|",
    ]
    for row in rows:
        lines.append(
            f"| `{md_escape(row.path)}` | {row.malformed} | `{md_escape(row.action_class)}` | "
            f"`{md_escape(row.validation_lane)}` | {row.expected_state_met} | {md_escape(row.recommended_next_action)} |"
        )
    lines += [
        "",
        "## Recommended next action",
        "",
        next_overall,
        "",
        "## Non-mutation confirmation",
        "",
    ]
    for guard in summary["non_mutation_guards"]:
        lines.append(f"- `{guard}`")
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print("SelfDoc malformed assignment hotfix 003 validation complete.")
    print(f"Validation status: {validation_status}")
    print(f"Expected state met: {expected_met_count}/{len(rows)}")
    print(f"Source repair recommended: {source_repair_count}")
    print(f"cmd_help stale evidence/do not repair: {cmd_help_ok}")
    print(f"Wrote: {OUT_MD}")
    print(f"Wrote: {OUT_CSV}")
    print(f"Wrote: {OUT_JSON}")
    print("No source files were edited.")
    print("No DBFs were written.")
    print("CMDHELPCHK was not modified.")
    print("HELP DATA was not rebuilt.")

    return 0 if validation_status == "PASSED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
