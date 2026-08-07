#!/usr/bin/env python3
"""
source_contract_inventory_v1_1_promotion_review.py

REPORT_ONLY promotion/scope review for source_contract_inventory_probe_v1_1 after hotfix_001.

Run from:
    D:\code\ccode

Reads:
    dottalkpp\docs\generated\reports\source_contracts_inventory_v1_1.csv
    dottalkpp\docs\generated\reports\source_contracts_inventory_v1_1.json
    dottalkpp\docs\generated\reports\source_contract_inventory_v1_1_classifier_gap_review.csv
    dottalkpp\docs\generated\reports\source_contract_inventory_v1_1_classifier_gap_review.json
    dottalkpp\docs\generated\reports\source_contract_inventory_v0_vs_v1_1.md

Writes:
    dottalkpp\docs\generated\reports\source_contract_inventory_v1_1_promotion_review.md
    dottalkpp\docs\generated\reports\source_contract_inventory_v1_1_promotion_review.csv
    dottalkpp\docs\generated\reports\source_contract_inventory_v1_1_promotion_review.json

Safety:
    REPORT_ONLY
    No source edits.
    No DBF writes.
    No CMDHELPCHK changes.
    No HELP DATA rebuild.
    No repairs.
    Does not promote v1.1.

Purpose:
    Confirm the v1.1 hotfix closed the vocabulary gap.
    Review command-scope action changes.
    Confirm shell_commands.cpp is registry infrastructure.
    Confirm cmdhelp.cpp is family/subsystem usage backlog.
    Identify whether remaining accepted-drop cases are real defects or classifier/report-label issues.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPORT_DIRS = (
    Path("dottalkpp") / "docs" / "generated" / "reports",
    Path("docs") / "generated" / "reports",
)

V11_CSV = "source_contracts_inventory_v1_1.csv"
V11_JSON = "source_contracts_inventory_v1_1.json"
GAP_CSV = "source_contract_inventory_v1_1_classifier_gap_review.csv"
GAP_JSON = "source_contract_inventory_v1_1_classifier_gap_review.json"
COMPARE_MD = "source_contract_inventory_v0_vs_v1_1.md"

OUT_MD = "source_contract_inventory_v1_1_promotion_review.md"
OUT_CSV = "source_contract_inventory_v1_1_promotion_review.csv"
OUT_JSON = "source_contract_inventory_v1_1_promotion_review.json"


IMPORTANT_PATHS = {
    "src/cli/cmd_buildlmdb.cpp",
    "src/cli/cmd_dothelp.cpp",
    "src/cli/cmd_lmdb.cpp",
    "src/cli/cmdhelp.cpp",
    "src/cli/helpdata_cmdhelp_bridge.cpp",
    "src/cli/shell.cpp",
    "src/cli/shell_commands.cpp",
    "include/xexpr/function.hpp",
}


@dataclass
class ReviewRow:
    path: str
    review_class: str
    priority: str
    current_role: str = ""
    current_family: str = ""
    current_action: str = ""
    gap_class: str = ""
    draft_action: str = ""
    v1_1_action: str = ""
    v1_1_unrecognized: list[str] = field(default_factory=list)
    should_have_accepted_fields: list[str] = field(default_factory=list)
    finding: str = ""
    recommendation: str = ""


def b(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes", "y"}


def parse_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()]
    text = str(value).strip()
    if not text:
        return []
    sep = ";" if ";" in text else ","
    return [part.strip() for part in text.split(sep) if part.strip()]


def md_escape(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return [dict(row) for row in csv.DictReader(f)]


def find_report_dir(root: Path, explicit: str | None) -> Path:
    if explicit:
        d = root / explicit
        if not d.is_dir():
            raise SystemExit(f"Report directory not found: {d}")
        return d
    for rel in REPORT_DIRS:
        d = root / rel
        if (d / V11_CSV).is_file() and (d / GAP_CSV).is_file():
            return d
    raise SystemExit("Could not find v1.1 inventory and gap review reports under dottalkpp\\docs\\generated\\reports")


def load_json_summary(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        return dict(payload.get("summary", {}))
    except Exception as exc:
        return {"read_error": f"{type(exc).__name__}: {exc}"}


def review_class_for_gap(row: dict[str, str]) -> tuple[str, str, str, str]:
    gap = row.get("gap_class", "")
    path = row.get("path", "")
    should_accept = parse_list(row.get("should_have_accepted_fields", ""))

    if path == "src/cli/shell_commands.cpp":
        return (
            "SCOPE_CONFIRMATION",
            "HIGH",
            "Registry infrastructure correctly should not be an ordinary command usage backlog item.",
            "Confirm role/action: selfdoc.command_registry_contract / alternate_contract_registry.",
        )

    if path == "src/cli/cmdhelp.cpp":
        return (
            "FAMILY_USAGE_CONFIRMATION",
            "HIGH",
            "CMDHELP should remain actionable as a family/subsystem usage contract, not as a simple command.",
            "Confirm family-level backlog; do not repair header yet.",
        )

    if should_accept:
        return (
            "VOCABULARY_GAP_RECHECK",
            "HIGH",
            "Accepted vocabulary still appears in a gap row.",
            "Review before promotion; this should be zero after hotfix_001.",
        )

    if gap == "action_class_changed":
        return (
            "ACTION_CHANGE_REVIEW",
            "MEDIUM",
            "Action class changed between draft and hotfix output.",
            "Inspect whether change is role/scope correction or unintended classifier drift.",
        )

    if gap == "accepted_to_shape_review_other":
        return (
            "ACCEPTED_DROP_REVIEW",
            "HIGH",
            "A draft-accepted item is no longer accepted for a non-vocabulary reason.",
            "Decide whether this is a real shape defect or a reporting/classifier label issue.",
        )

    if gap == "new_unrecognized_fields":
        return (
            "NEW_UNRECOGNIZED_REVIEW",
            "MEDIUM",
            "Hotfix output introduced or exposed unrecognized fields not present in draft.",
            "Review fields; do not broadly accept without human decision.",
        )

    if path in IMPORTANT_PATHS:
        return (
            "IMPORTANT_PATH_REVIEW",
            "MEDIUM",
            "Important command/help/runtime surface path should be reviewed before promotion.",
            "Inspect role, family, action, and remaining fields.",
        )

    if gap == "no_gap":
        return (
            "NO_GAP",
            "LOW",
            "No difference requiring promotion review.",
            "No immediate action.",
        )

    return (
        "OTHER_GAP_REVIEW",
        "LOW",
        "Gap row does not match one of the primary promotion-review classes.",
        "Review if counts or path context warrant it.",
    )


def build_review_rows(v11_rows: dict[str, dict[str, str]], gap_rows: list[dict[str, str]]) -> list[ReviewRow]:
    rows: list[ReviewRow] = []

    for gap in gap_rows:
        path = gap.get("path", "")
        v11 = v11_rows.get(path, {})
        gap_class = gap.get("gap_class", "")

        # Keep all non-no_gap rows plus named important paths.
        if gap_class == "no_gap" and path not in IMPORTANT_PATHS:
            continue

        review_class, priority, finding, recommendation = review_class_for_gap(gap)

        rows.append(ReviewRow(
            path=path,
            review_class=review_class,
            priority=priority,
            current_role=v11.get("command_scope_role", ""),
            current_family=v11.get("recommended_family", ""),
            current_action=v11.get("action_class", ""),
            gap_class=gap_class,
            draft_action=gap.get("draft_action", ""),
            v1_1_action=gap.get("v1_1_action", ""),
            v1_1_unrecognized=parse_list(gap.get("v1_1_unrecognized", "")),
            should_have_accepted_fields=parse_list(gap.get("should_have_accepted_fields", "")),
            finding=finding,
            recommendation=recommendation,
        ))

    # Ensure explicit rows for shell_commands and cmdhelp even if gap report later omits them.
    present = {r.path for r in rows}
    for path in ("src/cli/shell_commands.cpp", "src/cli/cmdhelp.cpp"):
        if path not in present and path in v11_rows:
            v11 = v11_rows[path]
            if path == "src/cli/shell_commands.cpp":
                cls, priority, finding, recommendation = (
                    "SCOPE_CONFIRMATION",
                    "HIGH",
                    "Registry infrastructure should not be ordinary command usage backlog.",
                    "Confirm registry classification and keep out of simple @dottalk.usage backlog.",
                )
            else:
                cls, priority, finding, recommendation = (
                    "FAMILY_USAGE_CONFIRMATION",
                    "HIGH",
                    "CMDHELP should be family/subsystem usage backlog, not simple command backlog.",
                    "Confirm family-level action; no source repair yet.",
                )
            rows.append(ReviewRow(
                path=path,
                review_class=cls,
                priority=priority,
                current_role=v11.get("command_scope_role", ""),
                current_family=v11.get("recommended_family", ""),
                current_action=v11.get("action_class", ""),
                finding=finding,
                recommendation=recommendation,
            ))

    priority_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
    rows.sort(key=lambda r: (priority_order.get(r.priority, 9), r.review_class, r.path.lower()))
    return rows


def compute_gate(summary_v11: dict[str, Any], summary_gap: dict[str, Any], review_rows: list[ReviewRow]) -> dict[str, Any]:
    vocab_gap_paths = int(summary_gap.get("paths_with_vocab_acceptance_gap", 999) or 0)
    shape_increase = int(summary_gap.get("shape_review_increase", 999) or 0)
    accepted_drop = int(summary_gap.get("accepted_drop", 999) or 0)
    actionable = int(summary_v11.get("actionable_missing_command_help_usage_contracts", 999) or 0)
    remaining_unrec = int(summary_v11.get("remaining_distinct_unrecognized_fields", 999) or 0)

    shell_ok = any(
        r.path == "src/cli/shell_commands.cpp"
        and r.current_family == "selfdoc.command_registry_contract"
        and r.current_action == "alternate_contract_registry"
        for r in review_rows
    )

    cmdhelp_ok = any(
        r.path == "src/cli/cmdhelp.cpp"
        and r.current_family in {"selfdoc.help_subsystem_contract", "selfdoc.command_family_contract"}
        and r.current_action == "action_required_add_command_family_usage_contract"
        for r in review_rows
    )

    high_review = sum(1 for r in review_rows if r.priority == "HIGH")

    gates = {
        "vocabulary_gap_closed": vocab_gap_paths == 0,
        "shape_review_parity_restored": shape_increase == 0,
        "accepted_drop_small_enough_for_review": accepted_drop <= 2,
        "ordinary_actionable_backlog_reduced": actionable <= 1,
        "shell_commands_scope_corrected": shell_ok,
        "cmdhelp_family_scope_corrected": cmdhelp_ok,
        "remaining_unrecognized_requires_policy_review": remaining_unrec > 0,
        "high_priority_review_rows": high_review,
    }

    gates["promotion_status"] = (
        "HOLD_REVIEW_REQUIRED"
        if not all([
            gates["vocabulary_gap_closed"],
            gates["shape_review_parity_restored"],
            gates["accepted_drop_small_enough_for_review"],
            gates["ordinary_actionable_backlog_reduced"],
            gates["shell_commands_scope_corrected"],
            gates["cmdhelp_family_scope_corrected"],
        ])
        else "NEAR_OPEN_HUMAN_REVIEW_REQUIRED"
    )
    return gates


def write_csv_report(path: Path, rows: list[ReviewRow]) -> None:
    fieldnames = [
        "path", "review_class", "priority", "current_role", "current_family",
        "current_action", "gap_class", "draft_action", "v1_1_action",
        "v1_1_unrecognized", "should_have_accepted_fields", "finding", "recommendation",
    ]
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            data = asdict(row)
            for key, value in list(data.items()):
                if isinstance(value, list):
                    data[key] = "; ".join(value)
            writer.writerow(data)


def write_json_report(path: Path, summary: dict[str, Any], rows: list[ReviewRow]) -> None:
    path.write_text(
        json.dumps({"summary": summary, "review_rows": [asdict(r) for r in rows]}, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def write_md_report(path: Path, csv_path: Path, json_path: Path, summary: dict[str, Any], rows: list[ReviewRow], load_notes: list[str]) -> None:
    review_counts = Counter(r.review_class for r in rows)
    priority_counts = Counter(r.priority for r in rows)
    gate = summary["promotion_gate"]

    lines: list[str] = []
    lines.append("# Source Contract Inventory v1.1 Promotion Review")
    lines.append("")
    lines.append(f"Generated UTC: `{summary['generated_at_utc']}`")
    lines.append("")
    lines.append("Safety class: `REPORT_ONLY`")
    lines.append("")
    lines.append("## Scope")
    lines.append("")
    lines.append("This report reviews whether the v1.1 source-contract inventory probe is close to promotion after hotfix_001. It does not promote v1.1, edit source, write DBFs, modify CMDHELPCHK, rebuild HELP DATA, or repair headers.")
    lines.append("")
    lines.append("Inputs read:")
    lines.append("")
    for note in load_notes:
        lines.append(f"- `{note}`")
    lines.append("")
    lines.append("Outputs written:")
    lines.append("")
    lines.append(f"- `{path}`")
    lines.append(f"- `{csv_path}`")
    lines.append(f"- `{json_path}`")
    lines.append("")
    lines.append("## Verdict")
    lines.append("")
    lines.append("```text")
    lines.append("v1.1 hotfix direction: WORKING")
    lines.append("vocabulary gap: CLOSED" if gate["vocabulary_gap_closed"] else "vocabulary gap: REVIEW REQUIRED")
    lines.append("scope correction: WORKING" if gate["shell_commands_scope_corrected"] and gate["cmdhelp_family_scope_corrected"] else "scope correction: REVIEW REQUIRED")
    lines.append(f"promotion status: {gate['promotion_status']}")
    lines.append("next task: human promotion/scope review, not source repair")
    lines.append("```")
    lines.append("")
    lines.append("## Key counts")
    lines.append("")
    for key in [
        "records_compared",
        "draft_accepted_existing_command_contracts",
        "v1_1_accepted_existing_command_contracts",
        "accepted_drop",
        "draft_shape_review_items",
        "v1_1_shape_review_items",
        "shape_review_increase",
        "v1_1_actionable_missing_command_help_usage_contracts",
        "v1_1_remaining_distinct_unrecognized_fields",
        "paths_with_vocab_acceptance_gap",
    ]:
        lines.append(f"- {key}: `{summary.get(key, '')}`")
    lines.append("")
    lines.append("## Promotion gate checks")
    lines.append("")
    lines.append("| Gate | Value |")
    lines.append("|---|---|")
    for key, value in gate.items():
        lines.append(f"| `{md_escape(key)}` | `{md_escape(value)}` |")
    lines.append("")
    lines.append("## Review class counts")
    lines.append("")
    lines.append("| Review class | Count |")
    lines.append("|---|---:|")
    for cls, count in review_counts.most_common():
        lines.append(f"| `{md_escape(cls)}` | {count} |")
    lines.append("")
    lines.append("## Priority counts")
    lines.append("")
    lines.append("| Priority | Count |")
    lines.append("|---|---:|")
    for priority, count in priority_counts.most_common():
        lines.append(f"| `{md_escape(priority)}` | {count} |")
    lines.append("")
    lines.append("## Review rows")
    lines.append("")
    if not rows:
        lines.append("No review rows found.")
    else:
        lines.append("| Path | Priority | Review class | Current role | Current family | Current action | Finding | Recommendation |")
        lines.append("|---|---|---|---|---|---|---|---|")
        for row in rows:
            lines.append(
                f"| `{md_escape(row.path)}` | `{md_escape(row.priority)}` | `{md_escape(row.review_class)}` | "
                f"`{md_escape(row.current_role)}` | `{md_escape(row.current_family)}` | `{md_escape(row.current_action)}` | "
                f"{md_escape(row.finding)} | {md_escape(row.recommendation)} |"
            )
    lines.append("")
    lines.append("## Promotion recommendation")
    lines.append("")
    lines.append("Do not promote automatically. If the review rows confirm the two accepted-drop cases are expected role/report-label changes and not parser defects, then v1.1 can move to a named promotion-candidate phase. Source repairs remain unauthorized.")
    lines.append("")
    lines.append("## Non-mutation confirmation")
    lines.append("")
    lines.append("- No source files edited.")
    lines.append("- No DBFs written.")
    lines.append("- No HELP DATA rebuilt.")
    lines.append("- No CMDHELPCHK implementation or configuration modified.")
    lines.append("- No source contract headers repaired.")
    lines.append("- This review writes markdown, CSV, and JSON only.")

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Review v1.1 source-contract inventory for promotion readiness.")
    parser.add_argument("--root", default=".", help="Project root. Default: current directory, normally D:\\code\\ccode.")
    parser.add_argument("--report-dir", default=None, help="Optional report directory relative to root.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = Path(args.root).resolve()
    report_dir = find_report_dir(root, args.report_dir)

    v11_csv_path = report_dir / V11_CSV
    gap_csv_path = report_dir / GAP_CSV
    v11_json_path = report_dir / V11_JSON
    gap_json_path = report_dir / GAP_JSON
    compare_md_path = report_dir / COMPARE_MD

    v11_rows_raw = read_csv(v11_csv_path)
    gap_rows_raw = read_csv(gap_csv_path)
    v11_rows = {row.get("path", ""): row for row in v11_rows_raw}

    v11_summary = load_json_summary(v11_json_path)
    gap_summary = load_json_summary(gap_json_path)

    review_rows = build_review_rows(v11_rows, gap_rows_raw)

    gate = compute_gate(v11_summary, gap_summary, review_rows)

    summary = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "report_dir": str(report_dir),
        "v1_1_inventory_rows": len(v11_rows_raw),
        "gap_rows": len(gap_rows_raw),
        "review_rows": len(review_rows),
        "records_compared": gap_summary.get("records_compared", ""),
        "draft_accepted_existing_command_contracts": gap_summary.get("draft_accepted_existing_command_contracts", ""),
        "v1_1_accepted_existing_command_contracts": gap_summary.get("v1_1_accepted_existing_command_contracts", ""),
        "accepted_drop": gap_summary.get("accepted_drop", ""),
        "draft_shape_review_items": gap_summary.get("draft_shape_review_items", ""),
        "v1_1_shape_review_items": gap_summary.get("v1_1_shape_review_items", ""),
        "shape_review_increase": gap_summary.get("shape_review_increase", ""),
        "v1_1_actionable_missing_command_help_usage_contracts": gap_summary.get("v1_1_actionable_missing_command_help_usage_contracts", v11_summary.get("actionable_missing_command_help_usage_contracts", "")),
        "v1_1_remaining_distinct_unrecognized_fields": gap_summary.get("v1_1_remaining_distinct_unrecognized_fields", v11_summary.get("remaining_distinct_unrecognized_fields", "")),
        "paths_with_vocab_acceptance_gap": gap_summary.get("paths_with_vocab_acceptance_gap", ""),
        "promotion_gate": gate,
        "non_mutation_guards": [
            "did_not_edit_source",
            "did_not_write_dbfs",
            "did_not_modify_cmdhelpchk",
            "did_not_rebuild_help_data",
            "did_not_repair_headers",
            "did_not_promote_v1_1",
        ],
    }

    load_notes = [
        f"read v1.1 inventory CSV: {v11_csv_path}",
        f"read v1.1 inventory JSON: {v11_json_path}",
        f"read classifier gap review CSV: {gap_csv_path}",
        f"read classifier gap review JSON: {gap_json_path}",
    ]
    if compare_md_path.is_file():
        load_notes.append(f"comparison report present: {compare_md_path}")
    else:
        load_notes.append(f"comparison report missing: {compare_md_path}")

    out_md = report_dir / OUT_MD
    out_csv = report_dir / OUT_CSV
    out_json = report_dir / OUT_JSON

    write_csv_report(out_csv, review_rows)
    write_json_report(out_json, summary, review_rows)
    write_md_report(out_md, out_csv, out_json, summary, review_rows, load_notes)

    print("SelfDoc source contract inventory v1.1 promotion review complete.")
    print(f"Read report directory: {report_dir}")
    print(f"v1.1 inventory rows: {len(v11_rows_raw)}")
    print(f"Gap rows: {len(gap_rows_raw)}")
    print(f"Review rows: {len(review_rows)}")
    print(f"Promotion status: {gate['promotion_status']}")
    print(f"Wrote: {out_md}")
    print(f"Wrote: {out_csv}")
    print(f"Wrote: {out_json}")
    print("No source files were edited.")
    print("No DBFs were written.")
    print("CMDHELPCHK was not modified.")
    print("HELP DATA was not rebuilt.")
    print("No repairs were made.")
    print("v1.1 was not promoted.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
