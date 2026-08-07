#!/usr/bin/env python3
"""
source_contract_shape_review_plan_v0.py

REPORT_ONLY / PLAN_ONLY shape-review planning probe.

Run from:
    D:\code\ccode

Reads:
    dottalkpp\docs\generated\reports\source_contracts_inventory_v1_1.csv
    dottalkpp\docs\generated\reports\source_contracts_inventory_v1_1.json
    dottalkpp\docs\generated\reports\source_contract_inventory_v1_1_promotion_candidate_report.json
    dottalkpp\docs\generated\reports\source_contract_inventory_v1_1_promotion_candidate_report.csv

Writes:
    dottalkpp\docs\generated\reports\source_contract_shape_review_plan_v0.md
    dottalkpp\docs\generated\reports\source_contract_shape_review_plan_v0.csv
    dottalkpp\docs\generated\reports\source_contract_shape_review_plan_v0.json

Safety:
    REPORT_ONLY / PLAN_ONLY
    No source edits.
    No DBF writes.
    No CMDHELPCHK changes.
    No HELP DATA rebuild.
    No repairs.
    No v1.1 default promotion.

Purpose:
    Use the corrected v1.1 classification model.
    Review remaining shape-review items.
    Separate real malformed/missing contract shapes from policy/vocabulary/design-note cases.
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

INV_CSV = "source_contracts_inventory_v1_1.csv"
INV_JSON = "source_contracts_inventory_v1_1.json"
PROMO_CSV = "source_contract_inventory_v1_1_promotion_candidate_report.csv"
PROMO_JSON = "source_contract_inventory_v1_1_promotion_candidate_report.json"

OUT_MD = "source_contract_shape_review_plan_v0.md"
OUT_CSV = "source_contract_shape_review_plan_v0.csv"
OUT_JSON = "source_contract_shape_review_plan_v0.json"

SAFETY_CLASS = "REPORT_ONLY / PLAN_ONLY"

# These are not blanket acceptances. They are review lanes to keep the plan disciplined.
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
)

DESIGN_NOTE_FIELD_HINTS = {
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
    "note_to_self",
    "developer_note",
    "developer_notes",
    "dev_note",
    "dev_notes",
    "rationale",
    "doctrine",
}

LIKELY_ALIAS_HINTS = {
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
}

TRUE_REQUIRED_FIELDS = {"command_or_commands", "summary", "usage_or_syntax"}


@dataclass
class ShapeReviewRow:
    path: str
    lane: str
    command_scope_role: str
    recommended_family: str
    action_class: str
    status: str
    review_class: str
    priority: str
    missing_required_fields: list[str] = field(default_factory=list)
    unrecognized_fields: list[str] = field(default_factory=list)
    malformed: bool = False
    header_hash: str = ""
    header_start_line: str = ""
    header_end_line: str = ""
    owner: str = ""
    command: str = ""
    commands: str = ""
    plan_action: str = ""
    repair_authorized: bool = False
    notes: list[str] = field(default_factory=list)


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


def norm_field(field: str) -> str:
    return field.strip().lower().replace(" ", "_")


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        return []
    with path.open("r", encoding="utf-8", newline="") as f:
        return [dict(row) for row in csv.DictReader(f)]


def read_summary(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        return dict(payload.get("summary", {}))
    except Exception as exc:
        return {"read_error": f"{type(exc).__name__}: {exc}"}


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
        if (d / INV_CSV).is_file():
            return d

    raise SystemExit("Could not find source_contracts_inventory_v1_1.csv under dottalkpp\\docs\\generated\\reports")


def classify_unrecognized_fields(fields: list[str]) -> tuple[str, list[str]]:
    normalized = [norm_field(f) for f in fields if f.strip()]
    if not normalized:
        return "NO_UNRECOGNIZED_FIELDS", []

    alias = [f for f in normalized if f in LIKELY_ALIAS_HINTS]
    design = [f for f in normalized if f in DESIGN_NOTE_FIELD_HINTS or any(h in f for h in ("design", "thin_wrapper", "implementation", "rationale", "doctrine"))]
    safety = [f for f in normalized if f.startswith(SAFETY_EFFECT_PREFIXES)]
    prose_like = [f for f in normalized if len(f) > 40 or "__" in f]
    other = [f for f in normalized if f not in set(alias + design + safety + prose_like)]

    notes = []
    if alias:
        notes.append("likely alias fields: " + ", ".join(sorted(set(alias))))
    if safety:
        notes.append("possible safety/effect fields for policy review: " + ", ".join(sorted(set(safety))[:20]))
    if design:
        notes.append("design/note metadata fields: " + ", ".join(sorted(set(design))[:20]))
    if prose_like:
        notes.append("prose-like or malformed field names: " + ", ".join(sorted(set(prose_like))[:20]))
    if other:
        notes.append("other unrecognized fields: " + ", ".join(sorted(set(other))[:20]))

    if alias and not other and not design and not prose_like:
        return "ALIAS_NORMALIZATION_REVIEW", notes
    if safety and not other and not design and not prose_like:
        return "SAFETY_EFFECT_POLICY_REVIEW", notes
    if design and not other:
        return "DESIGN_NOTE_OR_CLEANUP_LATER", notes
    if prose_like:
        return "PARSER_CAPTURE_OR_PROSE_FIELD_REVIEW", notes
    if other:
        return "UNRECOGNIZED_FIELD_POLICY_REVIEW", notes
    return "UNRECOGNIZED_FIELD_POLICY_REVIEW", notes


def classify_shape(row: dict[str, str]) -> ShapeReviewRow:
    missing = split_list(row.get("missing_required_fields", ""))
    unrecognized = split_list(row.get("unrecognized_fields", ""))
    malformed = b(row.get("malformed", False))
    path = row.get("path", "")

    review_classes = []
    notes = []

    if missing:
        review_classes.append("MISSING_REQUIRED_SHAPE")
        notes.append("missing required fields: " + ", ".join(missing))

    if malformed:
        review_classes.append("MALFORMED_HEADER_CAPTURE")
        notes.append("malformed/header-capture review required")

    unrec_class, unrec_notes = classify_unrecognized_fields(unrecognized)
    if unrec_class != "NO_UNRECOGNIZED_FIELDS":
        review_classes.append(unrec_class)
        notes.extend(unrec_notes)

    # Role-aware interpretation from the corrected v1.1 model.
    role = row.get("command_scope_role", "")
    family = row.get("recommended_family", "")
    action = row.get("action_class", "")

    if role in {"command_family_or_help_subsystem", "help_metadata_engine"}:
        notes.append("family/subsystem surface: review at family/subsystem scope, not simple command scope")
    if family == "@dottalk.usage v1":
        notes.append("ordinary command usage surface")
    elif family.startswith("selfdoc."):
        notes.append("alternate/selfdoc contract family: " + family)

    if not review_classes:
        review_classes.append("SHAPE_REVIEW_FLAG_ONLY")

    # Priority is a planning hint, not permission to repair.
    if "MISSING_REQUIRED_SHAPE" in review_classes or "MALFORMED_HEADER_CAPTURE" in review_classes:
        priority = "HIGH"
    elif "PARSER_CAPTURE_OR_PROSE_FIELD_REVIEW" in review_classes:
        priority = "HIGH"
    elif "UNRECOGNIZED_FIELD_POLICY_REVIEW" in review_classes:
        priority = "MEDIUM"
    else:
        priority = "LOW"

    if path in {"src/cli/cmdhelp.cpp", "src/cli/cmd_lmdb.cpp", "src/cli/cmd_buildlmdb.cpp", "src/cli/cmd_dothelp.cpp"}:
        priority = "HIGH"

    if "MISSING_REQUIRED_SHAPE" in review_classes or "MALFORMED_HEADER_CAPTURE" in review_classes:
        plan_action = "PLAN_REPAIR_REVIEW_LATER"
    elif "SAFETY_EFFECT_POLICY_REVIEW" in review_classes or "ALIAS_NORMALIZATION_REVIEW" in review_classes:
        plan_action = "POLICY_DECISION_BEFORE_REPAIR"
    elif "DESIGN_NOTE_OR_CLEANUP_LATER" in review_classes:
        plan_action = "CLASSIFY_AS_NOTES_OR_CLEANUP_LATER"
    else:
        plan_action = "MANUAL_CLASSIFICATION_REVIEW"

    return ShapeReviewRow(
        path=path,
        lane=row.get("lane", ""),
        command_scope_role=role,
        recommended_family=family,
        action_class=action,
        status=row.get("status", ""),
        review_class="+".join(review_classes),
        priority=priority,
        missing_required_fields=missing,
        unrecognized_fields=unrecognized,
        malformed=malformed,
        header_hash=row.get("header_hash", ""),
        header_start_line=row.get("header_start_line", ""),
        header_end_line=row.get("header_end_line", ""),
        owner=row.get("owner", ""),
        command=row.get("command", ""),
        commands=row.get("commands", ""),
        plan_action=plan_action,
        repair_authorized=False,
        notes=notes,
    )


def is_shape_review_row(row: dict[str, str]) -> bool:
    return b(row.get("is_shape_review_candidate", False)) or row.get("action_class", "") == "review_existing_command_contract_shape"


def write_csv_report(path: Path, rows: list[ShapeReviewRow]) -> None:
    fieldnames = [
        "path", "lane", "command_scope_role", "recommended_family", "action_class",
        "status", "review_class", "priority", "missing_required_fields",
        "unrecognized_fields", "malformed", "header_hash", "header_start_line",
        "header_end_line", "owner", "command", "commands", "plan_action",
        "repair_authorized", "notes",
    ]
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in rows:
            data = asdict(r)
            for key, value in list(data.items()):
                if isinstance(value, list):
                    data[key] = "; ".join(str(v) for v in value)
            writer.writerow(data)


def write_json_report(path: Path, summary: dict[str, Any], rows: list[ShapeReviewRow]) -> None:
    path.write_text(
        json.dumps({"summary": summary, "shape_review_rows": [asdict(r) for r in rows]}, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def write_md_report(path: Path, csv_path: Path, json_path: Path, summary: dict[str, Any], rows: list[ShapeReviewRow], load_notes: list[str]) -> None:
    lines = []
    lines.append("# Source Contract Shape Review Plan v0")
    lines.append("")
    lines.append(f"Generated UTC: `{summary['generated_at_utc']}`")
    lines.append("")
    lines.append(f"Safety class: `{SAFETY_CLASS}`")
    lines.append("")
    lines.append("## Verdict")
    lines.append("")
    lines.append("```text")
    lines.append("shape review plan: GENERATED")
    lines.append("source repairs: NOT AUTHORIZED")
    lines.append("DBF writes: NOT AUTHORIZED")
    lines.append("CMDHELPCHK changes: NOT AUTHORIZED")
    lines.append("HELP DATA rebuild: NOT AUTHORIZED")
    lines.append("```")
    lines.append("")
    lines.append("## Scope")
    lines.append("")
    lines.append("This plan uses the corrected v1.1 classification model to review remaining shape-review items. It separates malformed/missing contract shapes from policy, vocabulary, design-note, and cleanup-later cases. It is a planning artifact only.")
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
        "inventory_total_records",
        "inventory_shape_review_items",
        "planned_shape_review_rows",
        "high_priority_rows",
        "medium_priority_rows",
        "low_priority_rows",
        "distinct_unrecognized_fields_in_shape_rows",
    ]:
        lines.append(f"- {key}: `{summary.get(key, '')}`")
    lines.append("")
    lines.append("## Review class counts")
    lines.append("")
    lines.append("| Review class | Count |")
    lines.append("|---|---:|")
    for cls, count in summary["review_class_counts"].items():
        lines.append(f"| `{md_escape(cls)}` | {count} |")
    lines.append("")
    lines.append("## Plan action counts")
    lines.append("")
    lines.append("| Plan action | Count |")
    lines.append("|---|---:|")
    for action, count in summary["plan_action_counts"].items():
        lines.append(f"| `{md_escape(action)}` | {count} |")
    lines.append("")
    lines.append("## Top unrecognized fields in shape rows")
    lines.append("")
    if summary["top_unrecognized_fields"]:
        lines.append("| Field | Count |")
        lines.append("|---|---:|")
        for field, count in summary["top_unrecognized_fields"].items():
            lines.append(f"| `{md_escape(field)}` | {count} |")
    else:
        lines.append("No unrecognized fields found in shape-review rows.")
    lines.append("")
    lines.append("## High priority review rows")
    lines.append("")
    high_rows = [r for r in rows if r.priority == "HIGH"]
    if high_rows:
        lines.append("| Path | Review class | Family | Role | Plan action | Notes |")
        lines.append("|---|---|---|---|---|---|")
        for r in high_rows[:200]:
            lines.append(
                f"| `{md_escape(r.path)}` | `{md_escape(r.review_class)}` | `{md_escape(r.recommended_family)}` | "
                f"`{md_escape(r.command_scope_role)}` | `{md_escape(r.plan_action)}` | {md_escape('; '.join(r.notes))} |"
            )
    else:
        lines.append("No high priority rows.")
    lines.append("")
    lines.append("## Planning rules")
    lines.append("")
    lines.append("```text")
    lines.append("Do not repair source from this report.")
    lines.append("Do not write DBFs.")
    lines.append("Do not rebuild HELP DATA.")
    lines.append("Do not modify CMDHELPCHK.")
    lines.append("Policy/vocabulary/design-note cases must be reviewed before repair planning.")
    lines.append("Malformed/missing shape cases may become future patch proposals only after review.")
    lines.append("```")
    lines.append("")
    lines.append("## Non-mutation confirmation")
    lines.append("")
    for guard in summary["non_mutation_guards"]:
        lines.append(f"- `{md_escape(guard)}`")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Create source contract shape review plan v0.")
    parser.add_argument("--root", default=".")
    parser.add_argument("--report-dir", default=None)
    args = parser.parse_args()

    root = Path(args.root).resolve()
    rd = find_report_dir(root, args.report_dir)

    inv_rows = read_csv_rows(rd / INV_CSV)
    inv_summary = read_summary(rd / INV_JSON)
    promo_summary = read_summary(rd / PROMO_JSON)
    promo_rows = read_csv_rows(rd / PROMO_CSV)

    shape_rows = [classify_shape(row) for row in inv_rows if is_shape_review_row(row)]

    priority_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
    shape_rows.sort(key=lambda r: (priority_order.get(r.priority, 9), r.review_class, r.path.lower()))

    unrec_counter = Counter()
    for row in shape_rows:
        for field in row.unrecognized_fields:
            if field:
                unrec_counter[norm_field(field)] += 1

    review_counts = Counter(row.review_class for row in shape_rows)
    action_counts = Counter(row.plan_action for row in shape_rows)
    priority_counts = Counter(row.priority for row in shape_rows)

    summary = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "PLAN_ONLY_GENERATED",
        "report_dir": str(rd),
        "inventory_total_records": inv_summary.get("total_records", len(inv_rows)),
        "inventory_shape_review_items": inv_summary.get("existing_command_contracts_needing_shape_review", ""),
        "planned_shape_review_rows": len(shape_rows),
        "high_priority_rows": priority_counts.get("HIGH", 0),
        "medium_priority_rows": priority_counts.get("MEDIUM", 0),
        "low_priority_rows": priority_counts.get("LOW", 0),
        "distinct_unrecognized_fields_in_shape_rows": len(unrec_counter),
        "review_class_counts": dict(review_counts.most_common()),
        "plan_action_counts": dict(action_counts.most_common()),
        "priority_counts": dict(priority_counts.most_common()),
        "top_unrecognized_fields": dict(unrec_counter.most_common(100)),
        "promotion_candidate_status": promo_summary.get("status", ""),
        "promotion_candidate_rows": len(promo_rows),
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

    out_md = rd / OUT_MD
    out_csv = rd / OUT_CSV
    out_json = rd / OUT_JSON

    load_notes = [
        f"read v1.1 inventory CSV: {rd / INV_CSV}",
        f"read v1.1 inventory JSON: {rd / INV_JSON}" if (rd / INV_JSON).is_file() else f"v1.1 inventory JSON missing: {rd / INV_JSON}",
        f"read promotion candidate report JSON: {rd / PROMO_JSON}" if (rd / PROMO_JSON).is_file() else f"promotion candidate report JSON missing: {rd / PROMO_JSON}",
        f"read promotion candidate report CSV: {rd / PROMO_CSV}" if (rd / PROMO_CSV).is_file() else f"promotion candidate report CSV missing: {rd / PROMO_CSV}",
    ]

    write_csv_report(out_csv, shape_rows)
    write_json_report(out_json, summary, shape_rows)
    write_md_report(out_md, out_csv, out_json, summary, shape_rows, load_notes)

    print("SelfDoc source contract shape review plan v0 complete.")
    print(f"Read report directory: {rd}")
    print(f"Shape review rows planned: {len(shape_rows)}")
    print(f"High priority rows: {summary['high_priority_rows']}")
    print(f"Medium priority rows: {summary['medium_priority_rows']}")
    print(f"Low priority rows: {summary['low_priority_rows']}")
    print(f"Wrote: {out_md}")
    print(f"Wrote: {out_csv}")
    print(f"Wrote: {out_json}")
    print("No source files were edited.")
    print("No DBFs were written.")
    print("CMDHELPCHK was not modified.")
    print("HELP DATA was not rebuilt.")
    print("No repairs were made.")
    print("v1.1 was not promoted to default.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
