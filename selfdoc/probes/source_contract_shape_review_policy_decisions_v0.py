#!/usr/bin/env python3
"""
source_contract_shape_review_policy_decisions_v0.py

REPORT_ONLY / PLAN_ONLY policy-decision probe for source-contract shape review.

Run from:
    D:\code\ccode

Reads:
    dottalkpp\docs\generated\reports\source_contract_shape_review_plan_v0.csv
    dottalkpp\docs\generated\reports\source_contract_shape_review_plan_v0.json
    dottalkpp\docs\generated\reports\source_contracts_inventory_v1_1.csv
    dottalkpp\docs\generated\reports\source_contracts_inventory_v1_1.json

Writes:
    dottalkpp\docs\generated\reports\source_contract_shape_review_policy_decisions_v0.md
    dottalkpp\docs\generated\reports\source_contract_shape_review_policy_decisions_v0.csv
    dottalkpp\docs\generated\reports\source_contract_shape_review_policy_decisions_v0.json

Safety:
    REPORT_ONLY / PLAN_ONLY
    No source edits.
    No DBF writes.
    No CMDHELPCHK changes.
    No HELP DATA rebuild.
    No repairs.
    No v1.1 default promotion.

Purpose:
    Review distinct unrecognized fields and remaining shape-review lanes.
    Decide policy recommendations:
      - accepted safety/effect vocabulary candidates
      - notes/design metadata candidates
      - cleanup-later prose/malformed field candidates
      - alias-normalization candidates
      - malformed/header-capture cases eligible for future patch proposal planning
    Produce a plan only.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPORT_DIRS = (
    Path("dottalkpp") / "docs" / "generated" / "reports",
    Path("docs") / "generated" / "reports",
)

SHAPE_CSV = "source_contract_shape_review_plan_v0.csv"
SHAPE_JSON = "source_contract_shape_review_plan_v0.json"
INV_CSV = "source_contracts_inventory_v1_1.csv"
INV_JSON = "source_contracts_inventory_v1_1.json"

OUT_MD = "source_contract_shape_review_policy_decisions_v0.md"
OUT_CSV = "source_contract_shape_review_policy_decisions_v0.csv"
OUT_JSON = "source_contract_shape_review_policy_decisions_v0.json"

SAFETY_CLASS = "REPORT_ONLY / PLAN_ONLY"

ALIASES = {
    "usage_access": "usage-access",
    "usageaccess": "usage-access",
    "mutates_data": "mutates_table_data",
    "no_args": "noargs",
    "no-args": "noargs",
    "requires_table": "requires_open_table",
    "requires_area": "requires_current_area",
    "requires_record": "requires_current_record",
    "writes_file": "writes_files",
    "reads_file": "reads_files",
    "creates_file": "creates_files",
    "overwrites_file": "overwrites_files",
    "modifies": "mutates",
    "side_effects": "effect",
}

SAFETY_EFFECT_PREFIXES = (
    "requires_",
    "mutates_",
    "reads_",
    "writes_",
    "creates_",
    "opens_",
    "closes_",
    "clears_",
    "changes_",
    "loads_",
    "saves_",
    "updates_",
    "builds_",
    "rebuilds_",
    "deletes_",
    "drops_",
    "overwrites_",
    "validates_",
    "scans_",
    "emits_",
    "launches_",
    "executes_",
    "delegates_",
    "archives_",
    "marks_",
    "resets_",
)

KNOWN_SAFE_ACCEPT = {
    "requires_confirmation_for_existing_environment",
    "requires_confirmation",
    "requires_force",
    "requires_clean",
    "requires_output_path",
    "requires_index_order",
    "requires_active_area",
    "requires_open_table",
    "requires_current_record",
    "requires_current_area",
    "requires_workspace",
    "requires_relation",
    "requires_sql",
    "requires_transaction",
    "writes_lmdb_environment",
    "writes_index_file",
    "writes_index_files",
    "writes_dbf",
    "writes_dbf_record",
    "writes_dbf_records",
    "reads_dbf_header",
    "reads_metadata",
    "reads_workspace",
    "reads_table_records",
    "mutates_order_state",
    "mutates_relation_state",
    "mutates_path_state",
    "mutates_table_data",
    "mutates_index_backend",
    "updates_index",
    "updates_indexes",
    "builds_lmdb",
    "rebuilds_lmdb",
    "overwrites_index_file",
    "overwrites_files",
    "creates_index_file",
    "creates_metadata",
    "creates_workspace",
    "loads_workspace",
    "restores_workspace",
    "validates_metadata",
    "scans_records",
    "executes_command",
    "delegates_to_append",
    "delegates_to_replace",
}

DESIGN_NOTE_FIELDS = {
    "design",
    "design_note",
    "design_notes",
    "file",
    "files",
    "thin_wrapper",
    "thin_wrappers",
    "wrapper",
    "wrappers",
    "implementation",
    "implementation_note",
    "implementation_notes",
    "internal",
    "internal_note",
    "internal_notes",
    "backend",
    "backend_note",
    "backend_notes",
    "developer_note",
    "developer_notes",
    "dev_note",
    "dev_notes",
    "rationale",
    "doctrine",
    "compatibility_note",
    "legacy_note",
    "migration_note",
}

CLEANUP_PHRASE_HINTS = (
    "this_command_",
    "this_file_",
    "intentionally_",
    "currently_",
    "should_",
    "must_",
    "because_",
    "when_",
    "where_",
    "over_",
    "under_",
)


@dataclass
class FieldDecision:
    field: str
    count: int
    recommendation: str
    canonical_field: str = ""
    confidence: str = ""
    rationale: str = ""
    example_paths: list[str] = field(default_factory=list)
    repair_authorized: bool = False


@dataclass
class CaseDecision:
    path: str
    review_class: str
    priority: str
    plan_action: str
    policy_recommendation: str
    malformed: bool = False
    missing_required_fields: list[str] = field(default_factory=list)
    unrecognized_fields: list[str] = field(default_factory=list)
    future_patch_proposal_eligible: bool = False
    repair_authorized: bool = False
    rationale: str = ""


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


def b(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes", "y"}


def norm_field(field: str) -> str:
    return field.strip().lower().replace(" ", "_")


def is_prose_like(field: str) -> bool:
    f = norm_field(field)
    if len(f) >= 45:
        return True
    if any(hint in f for hint in CLEANUP_PHRASE_HINTS):
        return True
    if re.search(r"_[a-z]{1,2}_", f):
        return True
    return False


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


def find_report_dir(root: Path, explicit: str | None) -> Path:
    if explicit:
        d = root / explicit
        if not d.is_dir():
            raise SystemExit(f"Report directory not found: {d}")
        return d
    for rel in REPORT_DIRS:
        d = root / rel
        if (d / SHAPE_CSV).is_file():
            return d
    raise SystemExit("Could not find source_contract_shape_review_plan_v0.csv under dottalkpp\\docs\\generated\\reports")


def md_escape(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def decide_field(field: str, count: int, paths: list[str]) -> FieldDecision:
    f = norm_field(field)
    examples = sorted(set(paths))[:8]

    if f in ALIASES:
        return FieldDecision(
            field=f,
            count=count,
            recommendation="ACCEPT_ALIAS_NORMALIZATION",
            canonical_field=ALIASES[f],
            confidence="HIGH",
            rationale="Known alias form; normalize internally without rewriting source.",
            example_paths=examples,
        )

    if f in KNOWN_SAFE_ACCEPT:
        return FieldDecision(
            field=f,
            count=count,
            recommendation="ACCEPT_SAFETY_EFFECT_VOCABULARY",
            canonical_field=f,
            confidence="HIGH",
            rationale="Explicit safety/effect field already matches accepted SelfDoc semantics.",
            example_paths=examples,
        )

    if f.startswith(SAFETY_EFFECT_PREFIXES):
        return FieldDecision(
            field=f,
            count=count,
            recommendation="REVIEW_AS_SAFETY_EFFECT_VOCABULARY",
            canonical_field=f,
            confidence="MEDIUM",
            rationale="Looks like a safety/effect field. Accept only after policy review; do not repair source.",
            example_paths=examples,
        )

    if f in DESIGN_NOTE_FIELDS or any(h in f for h in ("design", "implementation", "rationale", "doctrine", "thin_wrapper")):
        return FieldDecision(
            field=f,
            count=count,
            recommendation="CLASSIFY_AS_NOTES_OR_DESIGN_METADATA",
            canonical_field="notes",
            confidence="MEDIUM",
            rationale="Looks like design/developer metadata rather than command usage shape.",
            example_paths=examples,
        )

    if is_prose_like(f):
        return FieldDecision(
            field=f,
            count=count,
            recommendation="CLEANUP_LATER_PROSE_OR_CAPTURE_FIELD",
            canonical_field="notes",
            confidence="MEDIUM",
            rationale="Looks prose-like or capture-derived. Do not accept globally; review capture/source shape later.",
            example_paths=examples,
        )

    return FieldDecision(
        field=f,
        count=count,
        recommendation="HOLD_FOR_HUMAN_POLICY_REVIEW",
        canonical_field="",
        confidence="LOW",
        rationale="Not enough evidence to accept as vocabulary. Keep in review lane.",
        example_paths=examples,
    )


def decide_case(row: dict[str, str]) -> CaseDecision:
    path = row.get("path", "")
    review_class = row.get("review_class", "")
    priority = row.get("priority", "")
    plan_action = row.get("plan_action", "")
    missing = split_list(row.get("missing_required_fields", ""))
    unrec = [norm_field(f) for f in split_list(row.get("unrecognized_fields", ""))]
    malformed = b(row.get("malformed", False))

    if missing:
        return CaseDecision(
            path=path,
            review_class=review_class,
            priority="HIGH",
            plan_action=plan_action,
            policy_recommendation="FUTURE_PATCH_PROPOSAL_ELIGIBLE_MISSING_REQUIRED_SHAPE",
            malformed=malformed,
            missing_required_fields=missing,
            unrecognized_fields=unrec,
            future_patch_proposal_eligible=True,
            rationale="Missing required command-shape fields. Eligible for future patch proposal after review, not immediate repair.",
        )

    if malformed and unrec:
        return CaseDecision(
            path=path,
            review_class=review_class,
            priority="HIGH",
            plan_action=plan_action,
            policy_recommendation="FUTURE_PATCH_PROPOSAL_ELIGIBLE_CAPTURE_PLUS_POLICY_REVIEW",
            malformed=malformed,
            missing_required_fields=missing,
            unrecognized_fields=unrec,
            future_patch_proposal_eligible=True,
            rationale="Malformed/capture issue plus unrecognized fields. Needs human review before any patch proposal.",
        )

    if malformed:
        return CaseDecision(
            path=path,
            review_class=review_class,
            priority="HIGH",
            plan_action=plan_action,
            policy_recommendation="FUTURE_PATCH_PROPOSAL_ELIGIBLE_MALFORMED_CAPTURE",
            malformed=malformed,
            missing_required_fields=missing,
            unrecognized_fields=unrec,
            future_patch_proposal_eligible=True,
            rationale="Malformed/header-capture issue. Eligible for future patch proposal planning only.",
        )

    if any(is_prose_like(f) for f in unrec):
        return CaseDecision(
            path=path,
            review_class=review_class,
            priority=priority or "MEDIUM",
            plan_action=plan_action,
            policy_recommendation="CLEANUP_LATER_PROSE_OR_DESIGN_NOTE",
            malformed=malformed,
            missing_required_fields=missing,
            unrecognized_fields=unrec,
            future_patch_proposal_eligible=False,
            rationale="Contains prose-like/design-note field. Classify as notes/design/cleanup-later, not broad vocabulary.",
        )

    if unrec:
        return CaseDecision(
            path=path,
            review_class=review_class,
            priority=priority or "MEDIUM",
            plan_action=plan_action,
            policy_recommendation="POLICY_REVIEW_REQUIRED_BEFORE_REPAIR",
            malformed=malformed,
            missing_required_fields=missing,
            unrecognized_fields=unrec,
            future_patch_proposal_eligible=False,
            rationale="Unrecognized fields remain. Review vocabulary/policy before any patch proposal.",
        )

    return CaseDecision(
        path=path,
        review_class=review_class,
        priority=priority or "LOW",
        plan_action=plan_action,
        policy_recommendation="NO_POLICY_DECISION_NEEDED",
        malformed=malformed,
        missing_required_fields=missing,
        unrecognized_fields=unrec,
        future_patch_proposal_eligible=False,
        rationale="No actionable policy issue detected.",
    )


def write_field_csv(path: Path, fields: list[FieldDecision], cases: list[CaseDecision]) -> None:
    # Single CSV with row_type so both field decisions and case decisions are inspectable in one file.
    fieldnames = [
        "row_type",
        "field",
        "count",
        "recommendation",
        "canonical_field",
        "confidence",
        "example_paths",
        "path",
        "review_class",
        "priority",
        "plan_action",
        "policy_recommendation",
        "malformed",
        "missing_required_fields",
        "unrecognized_fields",
        "future_patch_proposal_eligible",
        "repair_authorized",
        "rationale",
    ]
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for item in fields:
            writer.writerow({
                "row_type": "FIELD_DECISION",
                "field": item.field,
                "count": item.count,
                "recommendation": item.recommendation,
                "canonical_field": item.canonical_field,
                "confidence": item.confidence,
                "example_paths": "; ".join(item.example_paths),
                "repair_authorized": item.repair_authorized,
                "rationale": item.rationale,
            })
        for item in cases:
            writer.writerow({
                "row_type": "CASE_DECISION",
                "path": item.path,
                "review_class": item.review_class,
                "priority": item.priority,
                "plan_action": item.plan_action,
                "policy_recommendation": item.policy_recommendation,
                "malformed": item.malformed,
                "missing_required_fields": "; ".join(item.missing_required_fields),
                "unrecognized_fields": "; ".join(item.unrecognized_fields),
                "future_patch_proposal_eligible": item.future_patch_proposal_eligible,
                "repair_authorized": item.repair_authorized,
                "rationale": item.rationale,
            })


def write_json_report(path: Path, summary: dict[str, Any], fields: list[FieldDecision], cases: list[CaseDecision]) -> None:
    path.write_text(
        json.dumps(
            {
                "summary": summary,
                "field_decisions": [asdict(item) for item in fields],
                "case_decisions": [asdict(item) for item in cases],
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


def write_md_report(path: Path, csv_path: Path, json_path: Path, summary: dict[str, Any], fields: list[FieldDecision], cases: list[CaseDecision], load_notes: list[str]) -> None:
    lines = []
    lines.append("# Source Contract Shape Review Policy Decisions v0")
    lines.append("")
    lines.append(f"Generated UTC: `{summary['generated_at_utc']}`")
    lines.append("")
    lines.append(f"Safety class: `{SAFETY_CLASS}`")
    lines.append("")
    lines.append("## Verdict")
    lines.append("")
    lines.append("```text")
    lines.append("policy decision plan: GENERATED")
    lines.append("source repairs: NOT AUTHORIZED")
    lines.append("repair batch: NOT CREATED")
    lines.append("DBF writes: NOT AUTHORIZED")
    lines.append("CMDHELPCHK changes: NOT AUTHORIZED")
    lines.append("HELP DATA rebuild: NOT AUTHORIZED")
    lines.append("```")
    lines.append("")
    lines.append("## Scope")
    lines.append("")
    lines.append("This report reviews distinct unrecognized fields and shape-review cases from `source_contract_shape_review_plan_v0`. It recommends policy lanes only. It does not accept vocabulary into the live classifier, patch source, write DBFs, rebuild HELP DATA, or modify CMDHELPCHK.")
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
        "shape_review_rows",
        "distinct_unrecognized_fields",
        "accepted_safety_effect_candidates",
        "safety_effect_review_candidates",
        "alias_normalization_candidates",
        "notes_or_design_metadata_candidates",
        "cleanup_later_candidates",
        "hold_for_human_policy_review",
        "future_patch_proposal_eligible_cases",
    ]:
        lines.append(f"- {key}: `{summary.get(key, '')}`")
    lines.append("")
    lines.append("## Field recommendation counts")
    lines.append("")
    lines.append("| Recommendation | Count |")
    lines.append("|---|---:|")
    for recommendation, count in summary["field_recommendation_counts"].items():
        lines.append(f"| `{md_escape(recommendation)}` | {count} |")
    lines.append("")
    lines.append("## Case policy recommendation counts")
    lines.append("")
    lines.append("| Policy recommendation | Count |")
    lines.append("|---|---:|")
    for recommendation, count in summary["case_policy_recommendation_counts"].items():
        lines.append(f"| `{md_escape(recommendation)}` | {count} |")
    lines.append("")
    lines.append("## Accepted safety/effect vocabulary candidates")
    lines.append("")
    accepted = [f for f in fields if f.recommendation == "ACCEPT_SAFETY_EFFECT_VOCABULARY"]
    if accepted:
        lines.append("| Field | Count | Rationale |")
        lines.append("|---|---:|---|")
        for item in accepted:
            lines.append(f"| `{md_escape(item.field)}` | {item.count} | {md_escape(item.rationale)} |")
    else:
        lines.append("No high-confidence accepted safety/effect candidates found.")
    lines.append("")
    lines.append("## Safety/effect fields requiring policy review")
    lines.append("")
    review = [f for f in fields if f.recommendation == "REVIEW_AS_SAFETY_EFFECT_VOCABULARY"]
    if review:
        lines.append("| Field | Count | Example paths |")
        lines.append("|---|---:|---|")
        for item in review[:100]:
            lines.append(f"| `{md_escape(item.field)}` | {item.count} | {md_escape('; '.join(item.example_paths))} |")
    else:
        lines.append("No medium-confidence safety/effect review candidates found.")
    lines.append("")
    lines.append("## Notes/design/cleanup-later candidates")
    lines.append("")
    notes_design = [f for f in fields if f.recommendation in {"CLASSIFY_AS_NOTES_OR_DESIGN_METADATA", "CLEANUP_LATER_PROSE_OR_CAPTURE_FIELD"}]
    if notes_design:
        lines.append("| Field | Recommendation | Count | Rationale |")
        lines.append("|---|---|---:|---|")
        for item in notes_design[:100]:
            lines.append(f"| `{md_escape(item.field)}` | `{md_escape(item.recommendation)}` | {item.count} | {md_escape(item.rationale)} |")
    else:
        lines.append("No notes/design/cleanup-later field candidates found.")
    lines.append("")
    lines.append("## Future patch proposal eligible cases")
    lines.append("")
    eligible = [c for c in cases if c.future_patch_proposal_eligible]
    if eligible:
        lines.append("| Path | Policy recommendation | Missing required | Malformed | Rationale |")
        lines.append("|---|---|---|---:|---|")
        for item in eligible[:200]:
            lines.append(
                f"| `{md_escape(item.path)}` | `{md_escape(item.policy_recommendation)}` | "
                f"{md_escape('; '.join(item.missing_required_fields))} | {item.malformed} | {md_escape(item.rationale)} |"
            )
    else:
        lines.append("No future patch proposal eligible cases found.")
    lines.append("")
    lines.append("## Planning rules")
    lines.append("")
    lines.append("```text")
    lines.append("This report is not a repair batch.")
    lines.append("Accepted candidates are policy recommendations only.")
    lines.append("Do not rewrite source from this report.")
    lines.append("Do not write DBFs.")
    lines.append("Do not rebuild HELP DATA.")
    lines.append("Do not modify CMDHELPCHK.")
    lines.append("Future patch proposals require explicit approval after this policy review.")
    lines.append("```")
    lines.append("")
    lines.append("## Non-mutation confirmation")
    lines.append("")
    for guard in summary["non_mutation_guards"]:
        lines.append(f"- `{md_escape(guard)}`")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Create source contract shape-review policy decisions v0.")
    parser.add_argument("--root", default=".")
    parser.add_argument("--report-dir", default=None)
    args = parser.parse_args()

    root = Path(args.root).resolve()
    rd = find_report_dir(root, args.report_dir)

    shape_rows = read_csv_rows(rd / SHAPE_CSV)
    _shape_json = read_json(rd / SHAPE_JSON)
    _inv_rows = read_csv_rows(rd / INV_CSV)
    _inv_json = read_json(rd / INV_JSON)

    field_counts = Counter()
    field_paths: dict[str, list[str]] = defaultdict(list)
    for row in shape_rows:
        path = row.get("path", "")
        for field in split_list(row.get("unrecognized_fields", "")):
            f = norm_field(field)
            if not f:
                continue
            field_counts[f] += 1
            field_paths[f].append(path)

    field_decisions = [
        decide_field(field, count, field_paths[field])
        for field, count in sorted(field_counts.items(), key=lambda item: (-item[1], item[0]))
    ]

    case_decisions = [decide_case(row) for row in shape_rows]
    case_decisions.sort(key=lambda c: ({"HIGH": 0, "MEDIUM": 1, "LOW": 2}.get(c.priority, 9), c.policy_recommendation, c.path.lower()))

    field_rec_counts = Counter(item.recommendation for item in field_decisions)
    case_rec_counts = Counter(item.policy_recommendation for item in case_decisions)

    summary = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "PLAN_ONLY_GENERATED",
        "report_dir": str(rd),
        "shape_review_rows": len(shape_rows),
        "distinct_unrecognized_fields": len(field_decisions),
        "accepted_safety_effect_candidates": field_rec_counts.get("ACCEPT_SAFETY_EFFECT_VOCABULARY", 0),
        "safety_effect_review_candidates": field_rec_counts.get("REVIEW_AS_SAFETY_EFFECT_VOCABULARY", 0),
        "alias_normalization_candidates": field_rec_counts.get("ACCEPT_ALIAS_NORMALIZATION", 0),
        "notes_or_design_metadata_candidates": field_rec_counts.get("CLASSIFY_AS_NOTES_OR_DESIGN_METADATA", 0),
        "cleanup_later_candidates": field_rec_counts.get("CLEANUP_LATER_PROSE_OR_CAPTURE_FIELD", 0),
        "hold_for_human_policy_review": field_rec_counts.get("HOLD_FOR_HUMAN_POLICY_REVIEW", 0),
        "future_patch_proposal_eligible_cases": sum(1 for item in case_decisions if item.future_patch_proposal_eligible),
        "field_recommendation_counts": dict(field_rec_counts.most_common()),
        "case_policy_recommendation_counts": dict(case_rec_counts.most_common()),
        "non_mutation_guards": [
            "did_not_edit_source",
            "did_not_write_dbfs",
            "did_not_modify_cmdhelpchk",
            "did_not_rebuild_help_data",
            "did_not_repair_headers",
            "did_not_promote_v1_1_to_default",
            "did_not_create_repair_batch",
            "did_not_move_or_delete_files",
        ],
    }

    out_md = rd / OUT_MD
    out_csv = rd / OUT_CSV
    out_json = rd / OUT_JSON

    load_notes = [
        f"read shape review plan CSV: {rd / SHAPE_CSV}",
        f"read shape review plan JSON: {rd / SHAPE_JSON}" if (rd / SHAPE_JSON).is_file() else f"shape review plan JSON missing: {rd / SHAPE_JSON}",
        f"read v1.1 inventory CSV: {rd / INV_CSV}" if (rd / INV_CSV).is_file() else f"v1.1 inventory CSV missing: {rd / INV_CSV}",
        f"read v1.1 inventory JSON: {rd / INV_JSON}" if (rd / INV_JSON).is_file() else f"v1.1 inventory JSON missing: {rd / INV_JSON}",
    ]

    write_field_csv(out_csv, field_decisions, case_decisions)
    write_json_report(out_json, summary, field_decisions, case_decisions)
    write_md_report(out_md, out_csv, out_json, summary, field_decisions, case_decisions, load_notes)

    print("SelfDoc source contract shape review policy decisions v0 complete.")
    print(f"Read report directory: {rd}")
    print(f"Shape review rows: {len(shape_rows)}")
    print(f"Distinct unrecognized fields: {len(field_decisions)}")
    print(f"Future patch proposal eligible cases: {summary['future_patch_proposal_eligible_cases']}")
    print(f"Wrote: {out_md}")
    print(f"Wrote: {out_csv}")
    print(f"Wrote: {out_json}")
    print("No source files were edited.")
    print("No DBFs were written.")
    print("CMDHELPCHK was not modified.")
    print("HELP DATA was not rebuilt.")
    print("No repairs were made.")
    print("No repair batch was created.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
