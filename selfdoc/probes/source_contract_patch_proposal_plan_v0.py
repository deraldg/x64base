#!/usr/bin/env python3
"""
source_contract_patch_proposal_plan_v0.py

REPORT_ONLY / PLAN_ONLY patch proposal planning probe.

Run from:
    D:\code\ccode

Reads:
    dottalkpp\docs\generated\reports\source_contract_shape_review_policy_decisions_v0.csv
    dottalkpp\docs\generated\reports\source_contract_shape_review_policy_decisions_v0.json
    dottalkpp\docs\generated\reports\source_contract_shape_review_plan_v0.csv
    dottalkpp\docs\generated\reports\source_contract_shape_review_plan_v0.json

Writes:
    dottalkpp\docs\generated\reports\source_contract_patch_proposal_plan_v0.md
    dottalkpp\docs\generated\reports\source_contract_patch_proposal_plan_v0.csv
    dottalkpp\docs\generated\reports\source_contract_patch_proposal_plan_v0.json

Safety:
    REPORT_ONLY / PLAN_ONLY
    No source edits.
    No patch files.
    No repair batch.
    No DBF writes.
    No CMDHELPCHK changes.
    No HELP DATA rebuild.
    No v1.1 default promotion.
    No file moves/deletes.

Purpose:
    Use the policy-decisions report.
    Select a small future patch proposal batch from eligible cases.
    Prefer malformed/header-capture-only cases first.
    Exclude cases still needing policy review.
    Exclude cleanup-later/design-note cases.
    Generate a patch plan only, not a patch.
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

POLICY_CSV = "source_contract_shape_review_policy_decisions_v0.csv"
POLICY_JSON = "source_contract_shape_review_policy_decisions_v0.json"
SHAPE_CSV = "source_contract_shape_review_plan_v0.csv"
SHAPE_JSON = "source_contract_shape_review_plan_v0.json"

OUT_MD = "source_contract_patch_proposal_plan_v0.md"
OUT_CSV = "source_contract_patch_proposal_plan_v0.csv"
OUT_JSON = "source_contract_patch_proposal_plan_v0.json"

SAFETY_CLASS = "REPORT_ONLY / PLAN_ONLY"

DEFAULT_BATCH_SIZE = 10


@dataclass
class PlanRow:
    path: str
    lane: str = ""
    command_scope_role: str = ""
    recommended_family: str = ""
    policy_recommendation: str = ""
    review_class: str = ""
    priority: str = ""
    plan_action: str = ""
    malformed: bool = False
    missing_required_fields: list[str] = field(default_factory=list)
    unrecognized_fields: list[str] = field(default_factory=list)
    future_patch_proposal_eligible: bool = False
    selection_status: str = ""
    proposal_lane: str = ""
    proposed_action: str = ""
    rationale: str = ""
    repair_authorized: bool = False
    patch_file_authorized: bool = False


def b(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes", "y"}


def split_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()]
    text = str(value).strip()
    if not text:
        return []
    sep = ";" if ";" in text else ","
    return [part.strip() for part in text.split(sep) if part.strip()]


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


def find_report_dir(root: Path, explicit: str | None) -> Path:
    if explicit:
        d = root / explicit
        if not d.is_dir():
            raise SystemExit(f"Report directory not found: {d}")
        return d
    for rel in REPORT_DIRS:
        d = root / rel
        if (d / POLICY_CSV).is_file():
            return d
    raise SystemExit("Could not find source_contract_shape_review_policy_decisions_v0.csv under dottalkpp\\docs\\generated\\reports")


def build_shape_index(shape_rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    return {row.get("path", ""): row for row in shape_rows if row.get("path", "")}


def case_rows_from_policy(policy_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    return [row for row in policy_rows if row.get("row_type", "") == "CASE_DECISION"]


def rank_key(row: PlanRow) -> tuple[int, int, str]:
    # Preferred first batch: malformed/header-capture-only, no policy review, no missing required,
    # no unrecognized fields.
    priority_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
    lane_order = {
        "MALFORMED_CAPTURE_ONLY": 0,
        "MALFORMED_CAPTURE_PLUS_POLICY_REVIEW": 5,
        "MISSING_REQUIRED_SHAPE": 10,
        "OTHER_ELIGIBLE": 20,
        "EXCLUDED_POLICY_REVIEW": 50,
        "EXCLUDED_CLEANUP_LATER": 60,
        "NOT_ELIGIBLE": 99,
    }
    return (
        lane_order.get(row.proposal_lane, 99),
        priority_order.get(row.priority, 9),
        row.path.lower(),
    )


def classify_candidate(case: dict[str, str], shape_index: dict[str, dict[str, str]]) -> PlanRow:
    path = case.get("path", "")
    shape = shape_index.get(path, {})

    missing = split_list(case.get("missing_required_fields", ""))
    unrecognized = split_list(case.get("unrecognized_fields", ""))
    malformed = b(case.get("malformed", False))
    eligible = b(case.get("future_patch_proposal_eligible", False))
    policy = case.get("policy_recommendation", "")
    review_class = case.get("review_class", "")
    plan_action = case.get("plan_action", "")

    lane = shape.get("lane", "")
    role = shape.get("command_scope_role", "")
    family = shape.get("recommended_family", "")

    # Explicit exclusions from this plan.
    if not eligible:
        proposal_lane = "NOT_ELIGIBLE"
        selection_status = "EXCLUDED"
        proposed_action = "NO_PATCH_PROPOSAL"
        rationale = "Policy report did not mark this case as future patch proposal eligible."
    elif "POLICY_REVIEW" in policy:
        proposal_lane = "EXCLUDED_POLICY_REVIEW"
        selection_status = "EXCLUDED"
        proposed_action = "WAIT_FOR_POLICY_DECISION"
        rationale = "Case still needs policy/vocabulary review; excluded from first patch proposal batch."
    elif "CLEANUP" in policy or "DESIGN" in policy:
        proposal_lane = "EXCLUDED_CLEANUP_LATER"
        selection_status = "EXCLUDED"
        proposed_action = "KEEP_AS_CLEANUP_OR_DESIGN_NOTE"
        rationale = "Cleanup/design-note case; excluded from patch proposal batch."
    elif policy == "FUTURE_PATCH_PROPOSAL_ELIGIBLE_MALFORMED_CAPTURE" and malformed and not missing and not unrecognized:
        proposal_lane = "MALFORMED_CAPTURE_ONLY"
        selection_status = "CANDIDATE_POOL"
        proposed_action = "PLAN_HEADER_CAPTURE_PATCH_PROPOSAL"
        rationale = "Preferred first-batch candidate: malformed/header-capture only, no missing required fields and no policy-review fields."
    elif policy == "FUTURE_PATCH_PROPOSAL_ELIGIBLE_MALFORMED_CAPTURE" and malformed:
        proposal_lane = "MALFORMED_CAPTURE_ONLY"
        selection_status = "CANDIDATE_POOL"
        proposed_action = "PLAN_HEADER_CAPTURE_PATCH_PROPOSAL"
        rationale = "Malformed/header-capture candidate. Review unrecognized fields before actual patch proposal."
    elif policy == "FUTURE_PATCH_PROPOSAL_ELIGIBLE_MISSING_REQUIRED_SHAPE":
        proposal_lane = "MISSING_REQUIRED_SHAPE"
        selection_status = "BACKLOG"
        proposed_action = "PLAN_FAMILY_OR_COMMAND_CONTRACT_CONTENT_REVIEW"
        rationale = "Missing required shape requires content decision; keep out of first mechanical header-capture batch."
    elif "CAPTURE_PLUS_POLICY_REVIEW" in policy:
        proposal_lane = "MALFORMED_CAPTURE_PLUS_POLICY_REVIEW"
        selection_status = "BACKLOG"
        proposed_action = "WAIT_FOR_POLICY_DECISION_THEN_PLAN_PATCH"
        rationale = "Malformed/capture plus policy-review case; not safe for first batch."
    else:
        proposal_lane = "OTHER_ELIGIBLE"
        selection_status = "BACKLOG"
        proposed_action = "MANUAL_PATCH_PROPOSAL_REVIEW"
        rationale = "Eligible, but not a preferred first-batch header-capture-only case."

    return PlanRow(
        path=path,
        lane=lane,
        command_scope_role=role,
        recommended_family=family,
        policy_recommendation=policy,
        review_class=review_class,
        priority=case.get("priority", "") or shape.get("priority", ""),
        plan_action=plan_action,
        malformed=malformed,
        missing_required_fields=missing,
        unrecognized_fields=unrecognized,
        future_patch_proposal_eligible=eligible,
        selection_status=selection_status,
        proposal_lane=proposal_lane,
        proposed_action=proposed_action,
        rationale=rationale,
        repair_authorized=False,
        patch_file_authorized=False,
    )


def select_first_batch(rows: list[PlanRow], batch_size: int) -> list[PlanRow]:
    eligible = [
        row for row in rows
        if row.selection_status == "CANDIDATE_POOL"
        and row.proposal_lane == "MALFORMED_CAPTURE_ONLY"
        and "POLICY_REVIEW" not in row.policy_recommendation
    ]
    eligible.sort(key=rank_key)

    selected_paths = {row.path for row in eligible[:batch_size]}

    result = []
    for row in rows:
        if row.path in selected_paths:
            row.selection_status = "BATCH_0_CANDIDATE"
        result.append(row)

    result.sort(key=rank_key)
    return result


def write_csv_report(path: Path, rows: list[PlanRow]) -> None:
    fieldnames = [
        "path",
        "lane",
        "command_scope_role",
        "recommended_family",
        "policy_recommendation",
        "review_class",
        "priority",
        "plan_action",
        "malformed",
        "missing_required_fields",
        "unrecognized_fields",
        "future_patch_proposal_eligible",
        "selection_status",
        "proposal_lane",
        "proposed_action",
        "rationale",
        "repair_authorized",
        "patch_file_authorized",
    ]
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            data = asdict(row)
            for key, value in list(data.items()):
                if isinstance(value, list):
                    data[key] = "; ".join(str(v) for v in value)
            writer.writerow(data)


def write_json_report(path: Path, summary: dict[str, Any], rows: list[PlanRow]) -> None:
    path.write_text(
        json.dumps({"summary": summary, "plan_rows": [asdict(row) for row in rows]}, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def write_md_report(path: Path, csv_path: Path, json_path: Path, summary: dict[str, Any], rows: list[PlanRow], load_notes: list[str]) -> None:
    lines = []
    lines.append("# Source Contract Patch Proposal Plan v0")
    lines.append("")
    lines.append(f"Generated UTC: `{summary['generated_at_utc']}`")
    lines.append("")
    lines.append(f"Safety class: `{SAFETY_CLASS}`")
    lines.append("")
    lines.append("## Verdict")
    lines.append("")
    lines.append("```text")
    lines.append("patch proposal plan: GENERATED")
    lines.append("patch files: NOT CREATED")
    lines.append("repair batch: NOT CREATED")
    lines.append("source repairs: NOT AUTHORIZED")
    lines.append("DBF writes: NOT AUTHORIZED")
    lines.append("CMDHELPCHK changes: NOT AUTHORIZED")
    lines.append("HELP DATA rebuild: NOT AUTHORIZED")
    lines.append("```")
    lines.append("")
    lines.append("## Scope")
    lines.append("")
    lines.append("This report uses the policy-decisions report to select a small future patch proposal batch from eligible cases. It prefers malformed/header-capture-only cases and excludes policy-review, cleanup-later, and design-note cases. It is a plan only, not a patch.")
    lines.append("")
    lines.append("Inputs read:")
    lines.append("")
    for note in load_notes:
        lines.append(f"- `{md_escape(note)}`")
    lines.append("")
    lines.append("Outputs written:")
    lines.append("")
    lines.append(f"- `{path}`")
    lines.append(f"- `{csv_path}`")
    lines.append(f"- `{json_path}`")
    lines.append("")
    lines.append("## Summary counts")
    lines.append("")
    for key in [
        "policy_case_rows",
        "future_patch_proposal_eligible_cases",
        "batch_0_candidate_count",
        "candidate_pool_remaining",
        "excluded_policy_review",
        "excluded_cleanup_later",
        "missing_required_backlog",
        "malformed_capture_plus_policy_backlog",
    ]:
        lines.append(f"- {key}: `{summary.get(key, '')}`")
    lines.append("")
    lines.append("## Proposal lane counts")
    lines.append("")
    lines.append("| Proposal lane | Count |")
    lines.append("|---|---:|")
    for lane, count in summary["proposal_lane_counts"].items():
        lines.append(f"| `{md_escape(lane)}` | {count} |")
    lines.append("")
    lines.append("## Selection status counts")
    lines.append("")
    lines.append("| Selection status | Count |")
    lines.append("|---|---:|")
    for status, count in summary["selection_status_counts"].items():
        lines.append(f"| `{md_escape(status)}` | {count} |")
    lines.append("")
    lines.append("## Batch 0 candidates")
    lines.append("")
    selected = [row for row in rows if row.selection_status == "BATCH_0_CANDIDATE"]
    if selected:
        lines.append("| Path | Lane | Role | Family | Proposed action | Rationale |")
        lines.append("|---|---|---|---|---|---|")
        for row in selected:
            lines.append(
                f"| `{md_escape(row.path)}` | `{md_escape(row.lane)}` | `{md_escape(row.command_scope_role)}` | "
                f"`{md_escape(row.recommended_family)}` | `{md_escape(row.proposed_action)}` | {md_escape(row.rationale)} |"
            )
    else:
        lines.append("No batch 0 candidates selected.")
    lines.append("")
    lines.append("## Explicit exclusions")
    lines.append("")
    excluded = [row for row in rows if row.selection_status == "EXCLUDED"]
    if excluded:
        lines.append("| Path | Proposal lane | Policy recommendation | Rationale |")
        lines.append("|---|---|---|---|")
        for row in excluded[:200]:
            lines.append(
                f"| `{md_escape(row.path)}` | `{md_escape(row.proposal_lane)}` | "
                f"`{md_escape(row.policy_recommendation)}` | {md_escape(row.rationale)} |"
            )
    else:
        lines.append("No exclusions found.")
    lines.append("")
    lines.append("## Backlog lanes")
    lines.append("")
    backlog = [row for row in rows if row.selection_status == "BACKLOG"]
    if backlog:
        lines.append("| Path | Proposal lane | Proposed action | Rationale |")
        lines.append("|---|---|---|---|")
        for row in backlog[:200]:
            lines.append(
                f"| `{md_escape(row.path)}` | `{md_escape(row.proposal_lane)}` | "
                f"`{md_escape(row.proposed_action)}` | {md_escape(row.rationale)} |"
            )
    else:
        lines.append("No backlog rows found.")
    lines.append("")
    lines.append("## Planning rules")
    lines.append("")
    lines.append("```text")
    lines.append("This is not a patch.")
    lines.append("This is not a repair batch.")
    lines.append("Do not edit source from this plan.")
    lines.append("Do not write DBFs.")
    lines.append("Do not rebuild HELP DATA.")
    lines.append("Do not modify CMDHELPCHK.")
    lines.append("Batch 0 candidates may become patch proposals only after explicit approval.")
    lines.append("```")
    lines.append("")
    lines.append("## Non-mutation confirmation")
    lines.append("")
    for guard in summary["non_mutation_guards"]:
        lines.append(f"- `{md_escape(guard)}`")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Create source contract patch proposal plan v0.")
    parser.add_argument("--root", default=".")
    parser.add_argument("--report-dir", default=None)
    parser.add_argument("--batch-size", type=int, default=DEFAULT_BATCH_SIZE)
    args = parser.parse_args()

    root = Path(args.root).resolve()
    rd = find_report_dir(root, args.report_dir)

    policy_rows = read_csv_rows(rd / POLICY_CSV)
    policy_json = read_json(rd / POLICY_JSON)
    shape_rows = read_csv_rows(rd / SHAPE_CSV)
    _shape_json = read_json(rd / SHAPE_JSON)

    shape_index = build_shape_index(shape_rows)
    case_rows = case_rows_from_policy(policy_rows)

    plan_rows = [classify_candidate(row, shape_index) for row in case_rows]
    plan_rows = select_first_batch(plan_rows, max(0, args.batch_size))

    lane_counts = Counter(row.proposal_lane for row in plan_rows)
    status_counts = Counter(row.selection_status for row in plan_rows)

    summary = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "PLAN_ONLY_GENERATED",
        "report_dir": str(rd),
        "batch_size_requested": args.batch_size,
        "policy_case_rows": len(case_rows),
        "policy_report_status": policy_json.get("summary", {}).get("status", "") if isinstance(policy_json.get("summary", {}), dict) else "",
        "future_patch_proposal_eligible_cases": sum(1 for row in plan_rows if row.future_patch_proposal_eligible),
        "batch_0_candidate_count": status_counts.get("BATCH_0_CANDIDATE", 0),
        "candidate_pool_remaining": status_counts.get("CANDIDATE_POOL", 0),
        "excluded_policy_review": lane_counts.get("EXCLUDED_POLICY_REVIEW", 0),
        "excluded_cleanup_later": lane_counts.get("EXCLUDED_CLEANUP_LATER", 0),
        "missing_required_backlog": lane_counts.get("MISSING_REQUIRED_SHAPE", 0),
        "malformed_capture_plus_policy_backlog": lane_counts.get("MALFORMED_CAPTURE_PLUS_POLICY_REVIEW", 0),
        "proposal_lane_counts": dict(lane_counts.most_common()),
        "selection_status_counts": dict(status_counts.most_common()),
        "non_mutation_guards": [
            "did_not_edit_source",
            "did_not_write_dbfs",
            "did_not_modify_cmdhelpchk",
            "did_not_rebuild_help_data",
            "did_not_repair_headers",
            "did_not_create_patch_files",
            "did_not_create_repair_batch",
            "did_not_promote_v1_1_to_default",
            "did_not_move_or_delete_files",
        ],
    }

    out_md = rd / OUT_MD
    out_csv = rd / OUT_CSV
    out_json = rd / OUT_JSON

    load_notes = [
        f"read policy decisions CSV: {rd / POLICY_CSV}",
        f"read policy decisions JSON: {rd / POLICY_JSON}" if (rd / POLICY_JSON).is_file() else f"policy decisions JSON missing: {rd / POLICY_JSON}",
        f"read shape review plan CSV: {rd / SHAPE_CSV}" if (rd / SHAPE_CSV).is_file() else f"shape review plan CSV missing: {rd / SHAPE_CSV}",
        f"read shape review plan JSON: {rd / SHAPE_JSON}" if (rd / SHAPE_JSON).is_file() else f"shape review plan JSON missing: {rd / SHAPE_JSON}",
    ]

    write_csv_report(out_csv, plan_rows)
    write_json_report(out_json, summary, plan_rows)
    write_md_report(out_md, out_csv, out_json, summary, plan_rows, load_notes)

    print("SelfDoc source contract patch proposal plan v0 complete.")
    print(f"Read report directory: {rd}")
    print(f"Policy case rows: {len(case_rows)}")
    print(f"Future patch proposal eligible cases: {summary['future_patch_proposal_eligible_cases']}")
    print(f"Batch 0 candidates: {summary['batch_0_candidate_count']}")
    print(f"Candidate pool remaining: {summary['candidate_pool_remaining']}")
    print(f"Wrote: {out_md}")
    print(f"Wrote: {out_csv}")
    print(f"Wrote: {out_json}")
    print("No source files were edited.")
    print("No patch files were created.")
    print("No repair batch was created.")
    print("No DBFs were written.")
    print("CMDHELPCHK was not modified.")
    print("HELP DATA was not rebuilt.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
