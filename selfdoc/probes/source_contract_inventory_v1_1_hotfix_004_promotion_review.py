#!/usr/bin/env python3
"""
source_contract_inventory_v1_1_hotfix_004_promotion_review.py

REPORT_ONLY / REVIEW_ONLY promotion review for the v1.1-hotfix_004_writer_binding
source-contract inventory candidate.

Run from:
    D:\code\ccode

Reads:
    dottalkpp\docs\generated\reports\source_contracts_inventory_v1_1.csv
    dottalkpp\docs\generated\reports\source_contracts_inventory_v1_1.json
    dottalkpp\docs\generated\reports\source_contract_hotfix_004_validation_lane_tuning.csv
    dottalkpp\docs\generated\reports\source_contract_hotfix_004_validation_lane_tuning.json
    dottalkpp\docs\generated\reports\source_contract_hotfix_004_tuned_evidence_lanes.csv
    optional prior promotion/candidate review reports if present

Writes:
    dottalkpp\docs\generated\reports\source_contract_inventory_v1_1_hotfix_004_promotion_review.md
    dottalkpp\docs\generated\reports\source_contract_inventory_v1_1_hotfix_004_promotion_review.csv
    dottalkpp\docs\generated\reports\source_contract_inventory_v1_1_hotfix_004_promotion_review.json

Purpose:
    Review the v1.1-hotfix_004_writer_binding state as a promotion candidate.
    Compare against prior v1.1 candidate counts when available.
    Confirm Batch 0 false shape-review count is reduced by 9.
    Confirm source_repair_recommended remains 0.
    Keep cmd_help.cpp in STALE_EVIDENCE / DO_NOT_REPAIR.
    Do not promote to default automatically.

Safety:
    REPORT_ONLY / REVIEW_ONLY
    No DotTalk++ src/include edits.
    No source header repairs.
    No DBF writes.
    No HELP DATA rebuild.
    No CMDHELPCHK changes.
    No v1.1 default promotion.
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


EXPECTED_VERSION = "v1.1-hotfix_004_writer_binding"

REPORT_DIR = Path("dottalkpp") / "docs" / "generated" / "reports"

INV_CSV = REPORT_DIR / "source_contracts_inventory_v1_1.csv"
INV_JSON = REPORT_DIR / "source_contracts_inventory_v1_1.json"

TUNING_CSV = REPORT_DIR / "source_contract_hotfix_004_validation_lane_tuning.csv"
TUNING_JSON = REPORT_DIR / "source_contract_hotfix_004_validation_lane_tuning.json"
TUNED_LANES_CSV = REPORT_DIR / "source_contract_hotfix_004_tuned_evidence_lanes.csv"
TUNED_LANES_JSON = REPORT_DIR / "source_contract_hotfix_004_tuned_evidence_lanes.json"

OUT_MD = REPORT_DIR / "source_contract_inventory_v1_1_hotfix_004_promotion_review.md"
OUT_CSV = REPORT_DIR / "source_contract_inventory_v1_1_hotfix_004_promotion_review.csv"
OUT_JSON = REPORT_DIR / "source_contract_inventory_v1_1_hotfix_004_promotion_review.json"

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

# Prior human-reviewed v1.1 candidate expectation before capture/malformed hotfixing.
# Used only as a fallback if a prior report JSON is not found.
FALLBACK_PRIOR_COUNTS = {
    "accepted_existing_command_contracts": 101,
    "existing_command_contracts_needing_shape_review": 73,
    "batch0_false_shape_review_count": 9,
}

PRIOR_JSON_CANDIDATES = [
    REPORT_DIR / "source_contract_inventory_v1_1_promotion_candidate_report.json",
    REPORT_DIR / "source_contract_inventory_v1_1_promotion_review.json",
    REPORT_DIR / "source_contract_inventory_v1_1_classifier_gap_review.json",
]


@dataclass
class ReviewRow:
    path: str
    category: str
    current_present: bool
    malformed: bool
    action_class: str
    status: str
    evidence_lane: str
    secondary_lane: str
    source_repair_recommended: bool
    expected_state_met: bool
    review_lane: str
    recommendation: str
    note: str


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def b(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes", "y"}


def norm_path(path: object) -> str:
    return str(path or "").replace("\\", "/")


def md_escape(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


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
    return {norm_path(row.get("path", "")): row for row in rows if row.get("path", "")}


def find_prior_summary(root: Path) -> tuple[dict[str, Any], str]:
    for rel in PRIOR_JSON_CANDIDATES:
        path = root / rel
        data = read_json(path)
        if not data:
            continue
        summary = data.get("summary", {})
        if isinstance(summary, dict) and summary:
            return summary, str(path)
    return dict(FALLBACK_PRIOR_COUNTS), "fallback_prior_counts_from_handoff"


def count_current(inv_rows: list[dict[str, str]]) -> dict[str, Any]:
    actions = Counter(row.get("action_class", "") for row in inv_rows)
    statuses = Counter(row.get("status", "") for row in inv_rows)
    lanes = Counter(row.get("evidence_lane", "") for row in inv_rows if row.get("evidence_lane", ""))

    malformed_count = sum(1 for row in inv_rows if b(row.get("malformed", False)))
    repair_count = sum(1 for row in inv_rows if b(row.get("source_repair_recommended", False)))
    files_with_contracts = sum(1 for row in inv_rows if b(row.get("has_contract", row.get("contract_present", False))) or row.get("header_hash", ""))

    return {
        "total_records": len(inv_rows),
        "files_with_contracts_inferred": files_with_contracts,
        "accepted_existing_command_contracts": actions.get("accepted_existing_command_contract", 0),
        "existing_command_contracts_needing_shape_review": actions.get("review_existing_command_contract_shape", 0),
        "actionable_family_command_usage_contracts": actions.get("action_required_add_command_family_usage_contract", 0),
        "registry_contract_candidates": actions.get("alternate_contract_registry", 0),
        "malformed_rows": malformed_count,
        "source_repair_recommended": repair_count,
        "status_counts": dict(statuses.most_common()),
        "action_class_counts": dict(actions.most_common()),
        "evidence_lane_counts": dict(lanes.most_common()),
    }


def summarize_tuning(root: Path) -> tuple[dict[str, Any], str]:
    for rel in (TUNING_JSON, TUNED_LANES_JSON):
        data = read_json(root / rel)
        summary = data.get("summary", {})
        if isinstance(summary, dict) and summary:
            return summary, str(root / rel)
    return {}, ""


def get_lane(row: dict[str, str], tuned_row: dict[str, str]) -> tuple[str, str]:
    evidence = row.get("evidence_lane", "") or tuned_row.get("tuned_evidence_lane", "") or tuned_row.get("evidence_lane", "")
    secondary = row.get("secondary_lane", "") or tuned_row.get("tuned_secondary_lane", "") or tuned_row.get("secondary_lane", "")
    return evidence, secondary


def build_review_rows(inv_by_path: dict[str, dict[str, str]], tuned_by_path: dict[str, dict[str, str]]) -> list[ReviewRow]:
    rows: list[ReviewRow] = []

    for path in BATCH0_NINE:
        row = inv_by_path.get(path, {})
        tuned = tuned_by_path.get(path, {})
        evidence, secondary = get_lane(row, tuned)
        malformed = b(row.get("malformed", False))
        action = row.get("action_class", "")
        status = row.get("status", "")
        repair = b(row.get("source_repair_recommended", False))
        expected = (
            bool(row)
            and not malformed
            and action == "accepted_existing_command_contract"
            and status in {"accepted", "accepted_existing_command_contract", "ok"}
            and evidence in {"CONFIRMED", "accepted", "accepted_existing_command_contract", ""}
            and secondary in {"DO_NOT_REPAIR", ""}
            and not repair
        )
        rows.append(
            ReviewRow(
                path=path,
                category="batch0_false_shape_review",
                current_present=bool(row),
                malformed=malformed,
                action_class=action,
                status=status,
                evidence_lane=evidence,
                secondary_lane=secondary,
                source_repair_recommended=repair,
                expected_state_met=expected,
                review_lane="CONFIRMED" if expected else "PROMOTION_BLOCKER_REVIEW",
                recommendation="accept hotfix_004 correction; no source repair" if expected else "review row before promotion",
                note="Batch 0 capture-only false shape-review should be accepted/confirmed.",
            )
        )

    row = inv_by_path.get(CMD_HELP, {})
    tuned = tuned_by_path.get(CMD_HELP, {})
    evidence, secondary = get_lane(row, tuned)
    malformed = b(row.get("malformed", False))
    action = row.get("action_class", "")
    status = row.get("status", "")
    repair = b(row.get("source_repair_recommended", False))
    expected = bool(row) and evidence == "STALE_EVIDENCE" and secondary == "DO_NOT_REPAIR" and not repair
    rows.append(
        ReviewRow(
            path=CMD_HELP,
            category="cmd_help_stale_evidence",
            current_present=bool(row),
            malformed=malformed,
            action_class=action,
            status=status,
            evidence_lane=evidence,
            secondary_lane=secondary,
            source_repair_recommended=repair,
            expected_state_met=expected,
            review_lane="STALE_EVIDENCE" if expected else "PROMOTION_BLOCKER_REVIEW",
            recommendation="keep stale-evidence/do-not-repair; no source repair" if expected else "restore stale-evidence/do-not-repair lane",
            note="cmd_help.cpp remains a freshness/hash evidence issue, not a repair target.",
        )
    )

    return rows


def write_csv_report(path: Path, rows: list[ReviewRow]) -> None:
    fieldnames = list(asdict(rows[0]).keys()) if rows else []
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(asdict(row))


def write_md(path: Path, summary: dict[str, Any], rows: list[ReviewRow]) -> None:
    lines = [
        "# Source Contract Inventory v1.1 Hotfix 004 Promotion Review",
        "",
        f"Generated UTC: `{summary['generated_at_utc']}`",
        "",
        "Safety class: `REPORT_ONLY / REVIEW_ONLY`",
        "",
        "## Verdict",
        "",
        "```text",
        f"promotion review status: {summary['promotion_review_status']}",
        f"inventory_probe_version: {summary['inventory_probe_version']}",
        f"batch0_confirmed: {summary['batch0_confirmed']}/9",
        f"batch0_false_shape_review_reduced_by: {summary['batch0_false_shape_review_reduced_by']}",
        f"cmd_help_stale_evidence_do_not_repair: {summary['cmd_help_stale_evidence_do_not_repair']}",
        f"source_repair_recommended: {summary['source_repair_recommended']}",
        "v1.1 default promotion: NOT AUTHORIZED",
        "source repairs: NOT AUTHORIZED",
        "DBF writes: NOT AUTHORIZED",
        "HELP DATA rebuild: NOT AUTHORIZED",
        "CMDHELPCHK changes: NOT AUTHORIZED",
        "```",
        "",
        "## Count comparison",
        "",
        "| Count | Prior | Current | Delta |",
        "|---|---:|---:|---:|",
    ]

    for item in summary["count_comparison"]:
        lines.append(
            f"| `{md_escape(item['name'])}` | {item['prior']} | {item['current']} | {item['delta']} |"
        )

    lines += [
        "",
        "## Target rows",
        "",
        "| Path | Category | Malformed | Action class | Status | Lane | Secondary | Expected | Recommendation |",
        "|---|---|---:|---|---|---|---|---:|---|",
    ]
    for row in rows:
        lines.append(
            f"| `{md_escape(row.path)}` | `{md_escape(row.category)}` | {row.malformed} | "
            f"`{md_escape(row.action_class)}` | `{md_escape(row.status)}` | "
            f"`{md_escape(row.evidence_lane)}` | `{md_escape(row.secondary_lane)}` | "
            f"{row.expected_state_met} | {md_escape(row.recommendation)} |"
        )

    lines += [
        "",
        "## Interpretation",
        "",
        summary["interpretation"],
        "",
        "## Recommendation",
        "",
        summary["recommended_next_action"],
        "",
        "## Inputs",
        "",
    ]
    for inp in summary["inputs"]:
        lines.append(f"- `{md_escape(inp)}`")

    lines += [
        "",
        "## Non-mutation confirmation",
        "",
    ]
    for guard in summary["non_mutation_guards"]:
        lines.append(f"- `{guard}`")

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    (root / REPORT_DIR).mkdir(parents=True, exist_ok=True)

    inv_rows = read_csv_rows(root / INV_CSV)
    inv_by_path = index_by_path(inv_rows)

    inv_json = read_json(root / INV_JSON)
    inv_summary = inv_json.get("summary", {}) if isinstance(inv_json.get("summary", {}), dict) else {}
    probe_version = str(inv_summary.get("probe_version", ""))

    tuned_rows = read_csv_rows(root / TUNING_CSV)
    if not tuned_rows:
        tuned_rows = read_csv_rows(root / TUNED_LANES_CSV)
    tuned_by_path = index_by_path(tuned_rows)

    tuning_summary, tuning_source = summarize_tuning(root)
    prior_summary, prior_source = find_prior_summary(root)
    current_counts = count_current(inv_rows)

    review_rows = build_review_rows(inv_by_path, tuned_by_path)

    batch_confirmed = sum(1 for row in review_rows if row.category == "batch0_false_shape_review" and row.expected_state_met)
    batch_current_shape_review = sum(1 for row in review_rows if row.category == "batch0_false_shape_review" and row.action_class == "review_existing_command_contract_shape")
    batch_prior_false_shape = int(prior_summary.get("batch0_false_shape_review_count", FALLBACK_PRIOR_COUNTS["batch0_false_shape_review_count"]))
    batch_reduced_by = batch_prior_false_shape - batch_current_shape_review

    cmd_help_ok = any(row.category == "cmd_help_stale_evidence" and row.expected_state_met for row in review_rows)
    repair_count = current_counts.get("source_repair_recommended", 0)

    comparison_names = [
        "accepted_existing_command_contracts",
        "existing_command_contracts_needing_shape_review",
        "source_repair_recommended",
    ]
    count_comparison = []
    for name in comparison_names:
        prior = int(prior_summary.get(name, FALLBACK_PRIOR_COUNTS.get(name, 0)) or 0)
        current = int(current_counts.get(name, 0) or 0)
        count_comparison.append({"name": name, "prior": prior, "current": current, "delta": current - prior})

    count_comparison.append(
        {
            "name": "batch0_false_shape_review_count",
            "prior": batch_prior_false_shape,
            "current": batch_current_shape_review,
            "delta": batch_current_shape_review - batch_prior_false_shape,
        }
    )

    if probe_version != EXPECTED_VERSION:
        review_status = "HOLD_WRONG_PROBE_VERSION"
        interpretation = "The inventory is not from v1.1-hotfix_004_writer_binding, so promotion review cannot be accepted yet."
        next_action = "Rerun the writer-binding inventory and validation before promotion review."
    elif batch_confirmed == len(BATCH0_NINE) and cmd_help_ok and repair_count == 0 and batch_reduced_by == len(BATCH0_NINE):
        review_status = "PROMOTION_CANDIDATE_REVIEW_PASSED_NOT_DEFAULT"
        interpretation = "The v1.1-hotfix_004_writer_binding candidate corrected the nine Batch 0 false shape-review rows, kept cmd_help.cpp in stale-evidence/do-not-repair, and did not recommend source repair."
        next_action = "Record v1.1-hotfix_004_writer_binding as a reviewed promotion candidate. Do not promote to default until a separate explicit promotion decision."
    else:
        review_status = "HOLD_REVIEW_REQUIRED"
        interpretation = "One or more target promotion conditions did not pass. Review the target rows and count comparison."
        next_action = "Inspect the promotion review rows before any promotion or repair planning."

    summary = {
        "generated_at_utc": now(),
        "status": "REPORT_ONLY_GENERATED",
        "promotion_review_status": review_status,
        "inventory_probe_version": probe_version,
        "expected_inventory_probe_version": EXPECTED_VERSION,
        "prior_summary_source": prior_source,
        "tuning_summary_source": tuning_source,
        "total_records": len(inv_rows),
        "current_counts": current_counts,
        "prior_summary": prior_summary,
        "tuning_summary": tuning_summary,
        "count_comparison": count_comparison,
        "batch0_confirmed": batch_confirmed,
        "batch0_false_shape_review_prior": batch_prior_false_shape,
        "batch0_false_shape_review_current": batch_current_shape_review,
        "batch0_false_shape_review_reduced_by": batch_reduced_by,
        "cmd_help_stale_evidence_do_not_repair": cmd_help_ok,
        "source_repair_recommended": repair_count,
        "interpretation": interpretation,
        "recommended_next_action": next_action,
        "inputs": [
            str(root / INV_CSV),
            str(root / INV_JSON),
            str(root / TUNING_CSV),
            str(root / TUNING_JSON),
            str(root / TUNED_LANES_CSV),
            str(root / TUNED_LANES_JSON),
            prior_source,
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

    write_csv_report(root / OUT_CSV, review_rows)
    (root / OUT_JSON).write_text(json.dumps({"summary": summary, "rows": [asdict(r) for r in review_rows]}, indent=2), encoding="utf-8")
    write_md(root / OUT_MD, summary, review_rows)

    print("SelfDoc source contract v1.1 hotfix 004 promotion review complete.")
    print(f"Promotion review status: {review_status}")
    print(f"Inventory probe version: {probe_version}")
    print(f"Batch 0 confirmed: {batch_confirmed}/9")
    print(f"Batch 0 false shape-review reduced by: {batch_reduced_by}")
    print(f"cmd_help stale evidence / do not repair: {cmd_help_ok}")
    print(f"Source repair recommended: {repair_count}")
    print(f"Wrote: {OUT_MD}")
    print(f"Wrote: {OUT_CSV}")
    print(f"Wrote: {OUT_JSON}")
    print("No DotTalk++ src/include files were edited.")
    print("No DBFs were written.")
    print("HELP DATA was not rebuilt.")
    print("CMDHELPCHK was not modified.")
    print("v1.1 was not promoted to default.")

    return 0 if review_status == "PROMOTION_CANDIDATE_REVIEW_PASSED_NOT_DEFAULT" else 2


if __name__ == "__main__":
    raise SystemExit(main())
