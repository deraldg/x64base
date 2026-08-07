#!/usr/bin/env python3
"""
source_contract_extension_vocabulary_v1_1.py

REPORT_ONLY vocabulary decision pass for SelfDoc source contracts.

Run from:
    D:\code\ccode

Reads:
    dottalkpp\docs\generated\reports\source_contract_classifier_tuning_v0.csv
    dottalkpp\docs\generated\reports\source_contracts_inventory.json

Writes:
    dottalkpp\docs\generated\reports\source_contract_extension_vocabulary_v1_1.md
    dottalkpp\docs\generated\reports\source_contract_extension_vocabulary_v1_1.csv

Safety:
    REPORT_ONLY
    No source edits.
    No DBF writes.
    No CMDHELPCHK changes.
    No HELP DATA rebuild.
    No source contract repairs.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPORT_DIRS = (
    Path("dottalkpp") / "docs" / "generated" / "reports",
    Path("docs") / "generated" / "reports",
)

TUNING_CSV = "source_contract_classifier_tuning_v0.csv"
INVENTORY_JSON = "source_contracts_inventory.json"

OUTPUT_MD = "source_contract_extension_vocabulary_v1_1.md"
OUTPUT_CSV = "source_contract_extension_vocabulary_v1_1.csv"


# v1.1 additions that are likely legitimate fields when seen in command contracts.
# This is still a report recommendation, not an automatic classifier mutation.
LIKELY_ACCEPT_EXTENSION = {
    "allow_no_open_table",
    "area_state",
    "batch_safe",
    "buffer_semantics",
    "builds_lmdb",
    "case_sensitive",
    "changes_paths",
    "clears_filter",
    "clears_scope",
    "compatibility",
    "creates_metadata",
    "creates_relation",
    "creates_workspace",
    "deleted_record_policy",
    "depends_on_active_area",
    "diagnostic",
    "dispatch",
    "educational",
    "error_state",
    "expression_context",
    "file_dialog",
    "filter_semantics",
    "help_surface",
    "index_order",
    "lmdb_backend",
    "loads_workspace",
    "memo_semantics",
    "metadata_lane",
    "multi_area",
    "opens_table",
    "parser_surface",
    "path_slot",
    "prints_output",
    "reads_dbf_header",
    "reads_metadata",
    "reads_workspace",
    "relation_graph",
    "requires_relation",
    "requires_sql",
    "requires_transaction",
    "restores_workspace",
    "safe_noop",
    "schema_semantics",
    "script_control",
    "session_only",
    "side_effect",
    "sql_bridge",
    "table_flavor",
    "touches_filesystem",
    "transactional",
    "tuple_surface",
    "ui_surface",
    "validates_metadata",
    "workspace_state",
    "writes_metadata",
    "writes_workspace",
}

# Common variants that should be normalized internally if approved.
ALIAS_MAP = {
    "usage_access": "usage-access",
    "usageaccess": "usage-access",
    "no_args": "noargs",
    "no-args": "noargs",
    "mutates_data": "mutates_table_data",
    "writes_file": "writes_files",
    "writes_filesystem": "writes_filesystem",
    "reads_file": "reads_files",
    "creates_file": "creates_files",
    "overwrites_file": "overwrites_files",
    "requires_table": "requires_open_table",
    "requires_area": "requires_current_area",
    "requires_record": "requires_current_record",
    "changes_cursor": "mutates_cursor",
    "changes_order": "mutates_order_state",
}

# Broad token patterns that usually indicate legitimate safety/effect fields.
ACCEPT_PATTERNS = (
    r"^(reads|writes|creates|opens|closes|clears|loads|saves|restores|validates|updates|rebuilds|drops|archives|executes|launches)_",
    r"^(requires|depends_on|delegates_to|mutates|touches)_",
    r".*_semantics$",
    r".*_state$",
    r".*_policy$",
    r".*_surface$",
    r".*_backend$",
    r".*_metadata$",
    r".*_context$",
    r".*_graph$",
    r".*_lane$",
)

# Likely prose or implementation detail keys that should not be promoted blindly.
CLEANUP_PATTERNS = (
    r"^todo",
    r"^fixme",
    r"^note\d*$",
    r".*\?$",
    r".*\s+.*",
    r".*[().,;:].*",
)


@dataclass
class TuningRow:
    path: str
    lane: str
    current_status: str
    has_contract: bool
    old_escrow_candidate: bool
    recommended_family: str
    action_class: str
    valid_after_tuning: bool
    actionable_usage_backlog: bool
    missing_after_tuning: list[str] = field(default_factory=list)
    unrecognized_after_tuning: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


@dataclass
class VocabularyDecision:
    field: str
    count: int
    lanes: list[str]
    actions: list[str]
    recommendation: str
    canonical_field: str
    rationale: str
    sample_paths: list[str]


def parse_bool(value: Any) -> bool:
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
    parts = [p.strip() for p in text.split(";")]
    return [p for p in parts if p]


def normalize_field(field: str) -> str:
    return field.strip().lower().replace(" ", "_")


def find_report_dir(root: Path, explicit: str | None) -> Path:
    if explicit:
        d = root / explicit
        if not d.is_dir():
            raise SystemExit(f"Report directory not found: {d}")
        return d

    for rel in REPORT_DIRS:
        d = root / rel
        if (d / TUNING_CSV).is_file():
            return d

    checked = "\n".join(str(root / rel) for rel in REPORT_DIRS)
    raise SystemExit(f"Could not find classifier tuning CSV. Checked:\n{checked}")


def load_tuning_csv(report_dir: Path) -> list[TuningRow]:
    path = report_dir / TUNING_CSV
    if not path.is_file():
        raise SystemExit(f"Missing required input: {path}")

    rows: list[TuningRow] = []
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for item in reader:
            rows.append(TuningRow(
                path=str(item.get("path", "")),
                lane=str(item.get("lane", "")),
                current_status=str(item.get("current_status", "")),
                has_contract=parse_bool(item.get("has_contract", False)),
                old_escrow_candidate=parse_bool(item.get("old_escrow_candidate", False)),
                recommended_family=str(item.get("recommended_family", "")),
                action_class=str(item.get("action_class", "")),
                valid_after_tuning=parse_bool(item.get("valid_after_tuning", False)),
                actionable_usage_backlog=parse_bool(item.get("actionable_usage_backlog", False)),
                missing_after_tuning=parse_list(item.get("missing_after_tuning")),
                unrecognized_after_tuning=parse_list(item.get("unrecognized_after_tuning")),
                notes=parse_list(item.get("notes")),
            ))
    return rows


def load_inventory_summary(report_dir: Path) -> dict[str, Any]:
    path = report_dir / INVENTORY_JSON
    if not path.is_file():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return dict(payload.get("summary", {}))


def matches_any(field: str, patterns: tuple[str, ...]) -> bool:
    return any(re.match(pattern, field) for pattern in patterns)


def decide_field(field: str, rows: list[TuningRow]) -> VocabularyDecision:
    normalized = normalize_field(field)
    lanes = sorted({row.lane for row in rows})
    actions = sorted({row.action_class for row in rows})
    sample_paths = [row.path for row in rows[:8]]

    if normalized in ALIAS_MAP:
        return VocabularyDecision(
            field=field,
            count=len(rows),
            lanes=lanes,
            actions=actions,
            recommendation="ACCEPT_ALIAS",
            canonical_field=ALIAS_MAP[normalized],
            rationale="Observed field is a spelling/format variant of an already accepted field.",
            sample_paths=sample_paths,
        )

    if normalized in LIKELY_ACCEPT_EXTENSION or matches_any(normalized, ACCEPT_PATTERNS):
        return VocabularyDecision(
            field=field,
            count=len(rows),
            lanes=lanes,
            actions=actions,
            recommendation="ACCEPT_EXTENSION",
            canonical_field=normalized,
            rationale="Field follows safety/effect metadata naming patterns and should be recognized as v1.1 extension vocabulary if approved.",
            sample_paths=sample_paths,
        )

    if matches_any(normalized, CLEANUP_PATTERNS):
        return VocabularyDecision(
            field=field,
            count=len(rows),
            lanes=lanes,
            actions=actions,
            recommendation="CLEANUP_LATER",
            canonical_field=normalized,
            rationale="Field looks like prose, punctuation, or local note text; do not promote automatically.",
            sample_paths=sample_paths,
        )

    if all(action.startswith("alternate_contract_") for action in actions):
        return VocabularyDecision(
            field=field,
            count=len(rows),
            lanes=lanes,
            actions=actions,
            recommendation="ALTERNATE_CONTRACT_FIELD",
            canonical_field=normalized,
            rationale="Field appears only in non-command alternate-contract lanes; defer to the future contract family vocabulary.",
            sample_paths=sample_paths,
        )

    if len(rows) == 1:
        return VocabularyDecision(
            field=field,
            count=len(rows),
            lanes=lanes,
            actions=actions,
            recommendation="ONE_OFF_REVIEW",
            canonical_field=normalized,
            rationale="Single occurrence; needs human review before adding to vocabulary.",
            sample_paths=sample_paths,
        )

    return VocabularyDecision(
        field=field,
        count=len(rows),
        lanes=lanes,
        actions=actions,
        recommendation="REVIEW_BEFORE_ACCEPT",
        canonical_field=normalized,
        rationale="Repeated but not covered by v1.1 acceptance patterns; review before adding to accepted vocabulary.",
        sample_paths=sample_paths,
    )


def build_decisions(rows: list[TuningRow]) -> list[VocabularyDecision]:
    by_field: dict[str, list[TuningRow]] = defaultdict(list)
    for row in rows:
        for field in row.unrecognized_after_tuning:
            cleaned = normalize_field(field)
            if cleaned:
                by_field[cleaned].append(row)

    decisions = [decide_field(field, field_rows) for field, field_rows in by_field.items()]
    decisions.sort(key=lambda d: (d.recommendation, -d.count, d.field))
    return decisions


def md_escape(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def write_csv(path: Path, decisions: list[VocabularyDecision]) -> None:
    fieldnames = [
        "field",
        "count",
        "recommendation",
        "canonical_field",
        "rationale",
        "lanes",
        "actions",
        "sample_paths",
    ]
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for d in decisions:
            writer.writerow({
                "field": d.field,
                "count": d.count,
                "recommendation": d.recommendation,
                "canonical_field": d.canonical_field,
                "rationale": d.rationale,
                "lanes": "; ".join(d.lanes),
                "actions": "; ".join(d.actions),
                "sample_paths": "; ".join(d.sample_paths),
            })


def write_md(path: Path, csv_path: Path, rows: list[TuningRow], decisions: list[VocabularyDecision], inventory_summary: dict[str, Any]) -> None:
    rec_counts = Counter(d.recommendation for d in decisions)
    action_counts = Counter(row.action_class for row in rows)
    actionable = [row for row in rows if row.actionable_usage_backlog]

    lines: list[str] = []
    lines.append("# Source Contract Extension Vocabulary v1.1")
    lines.append("")
    lines.append(f"Generated UTC: `{datetime.now(timezone.utc).isoformat()}`")
    lines.append("")
    lines.append("Safety class: `REPORT_ONLY`")
    lines.append("")
    lines.append("## Scope")
    lines.append("")
    lines.append("This report reviews remaining unrecognized source-contract fields after `source_contract_classifier_tuning_v0`. It recommends vocabulary decisions only. It does not edit source, write DBFs, modify CMDHELPCHK, rebuild HELP DATA, or repair headers.")
    lines.append("")
    lines.append("Outputs written:")
    lines.append("")
    lines.append(f"- `{path}`")
    lines.append(f"- `{csv_path}`")
    lines.append("")
    lines.append("## Current baseline")
    lines.append("")
    if inventory_summary:
        lines.append(f"- Inventory source files: `{inventory_summary.get('total_source_files', 'unknown')}`")
        lines.append(f"- Files with contracts: `{inventory_summary.get('files_with_contract', 'unknown')}`")
        lines.append(f"- Files missing contracts: `{inventory_summary.get('files_missing_contract', 'unknown')}`")
        lines.append(f"- Broad escrow candidates: `{inventory_summary.get('escrow_candidate_count', 'unknown')}`")
    lines.append(f"- Tuning rows reviewed: `{len(rows)}`")
    lines.append(f"- Actionable missing command/help usage contracts remain: `{len(actionable)}`")
    lines.append(f"- Distinct remaining unrecognized fields: `{len(decisions)}`")
    lines.append("")
    lines.append("## Recommendation counts")
    lines.append("")
    lines.append("| Recommendation | Count |")
    lines.append("|---|---:|")
    for rec, count in rec_counts.most_common():
        lines.append(f"| `{md_escape(rec)}` | {count} |")
    lines.append("")
    lines.append("## Tuning action counts")
    lines.append("")
    lines.append("| Action class | Count |")
    lines.append("|---|---:|")
    for action, count in action_counts.most_common():
        lines.append(f"| `{md_escape(action)}` | {count} |")
    lines.append("")
    lines.append("## Decision vocabulary")
    lines.append("")
    lines.append("| Field | Count | Recommendation | Canonical field | Rationale |")
    lines.append("|---|---:|---|---|---|")
    for d in decisions:
        lines.append(
            f"| `{md_escape(d.field)}` | {d.count} | `{md_escape(d.recommendation)}` | "
            f"`{md_escape(d.canonical_field)}` | {md_escape(d.rationale)} |"
        )
    lines.append("")
    lines.append("## Actionable missing command/help usage contracts")
    lines.append("")
    if not actionable:
        lines.append("No actionable missing command/help usage contracts remain.")
    else:
        lines.append("| Path | Lane | Action class |")
        lines.append("|---|---|---|")
        for row in sorted(actionable, key=lambda r: r.path.lower()):
            lines.append(f"| `{md_escape(row.path)}` | `{md_escape(row.lane)}` | `{md_escape(row.action_class)}` |")
    lines.append("")
    lines.append("## Proposed v1.1 policy")
    lines.append("")
    lines.append("1. Keep `usage OR syntax` as the command-shape rule.")
    lines.append("2. Promote fields marked `ACCEPT_EXTENSION` into the accepted safety/effect extension vocabulary after human review.")
    lines.append("3. Normalize fields marked `ACCEPT_ALIAS` internally, but do not rewrite source headers during this phase.")
    lines.append("4. Leave `CLEANUP_LATER`, `ONE_OFF_REVIEW`, and `REVIEW_BEFORE_ACCEPT` out of accepted vocabulary until reviewed.")
    lines.append("5. Keep alternate-contract fields out of command usage vocabulary unless they also appear in command/help surface contracts.")
    lines.append("6. Preserve exact header hashing; never normalize field text before hashing.")
    lines.append("")
    lines.append("## Next safe step")
    lines.append("")
    lines.append("After this report is reviewed, the next safe implementation would be a report-only classifier update draft that changes the probe's accepted field table and reruns inventory/review/tuning. Still no source edits.")
    lines.append("")
    lines.append("## Non-mutation confirmation")
    lines.append("")
    lines.append("- No source files edited.")
    lines.append("- No DBFs written.")
    lines.append("- No HELP DATA rebuilt.")
    lines.append("- No CMDHELPCHK implementation or configuration modified.")
    lines.append("- No source contract headers repaired.")
    lines.append("- This report writes markdown and CSV only.")

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Produce source contract extension vocabulary v1.1 report.")
    parser.add_argument("--root", default=".", help="Project root. Default: current directory, normally D:\\code\\ccode.")
    parser.add_argument("--report-dir", default=None, help="Optional report directory relative to root.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = Path(args.root).resolve()
    report_dir = find_report_dir(root, args.report_dir)

    rows = load_tuning_csv(report_dir)
    inventory_summary = load_inventory_summary(report_dir)
    decisions = build_decisions(rows)

    out_md = report_dir / OUTPUT_MD
    out_csv = report_dir / OUTPUT_CSV

    write_csv(out_csv, decisions)
    write_md(out_md, out_csv, rows, decisions, inventory_summary)

    print("SelfDoc source contract extension vocabulary v1.1 complete.")
    print(f"Read report directory: {report_dir}")
    print(f"Tuning rows reviewed: {len(rows)}")
    print(f"Distinct remaining unrecognized fields: {len(decisions)}")
    print(f"Wrote: {out_md}")
    print(f"Wrote: {out_csv}")
    print("No source files were edited.")
    print("No DBFs were written.")
    print("CMDHELPCHK was not modified.")
    print("HELP DATA was not rebuilt.")
    print("No repairs were made.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
