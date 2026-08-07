#!/usr/bin/env python3
"""
source_contract_classifier_update_draft_v1_1.py

REPORT_ONLY draft classifier update simulation for SelfDoc source contracts.

Run from:
    D:\code\ccode

Reads:
    dottalkpp\docs\generated\reports\source_contracts_inventory.json
    dottalkpp\docs\generated\reports\source_contract_extension_vocabulary_v1_1.csv
    dottalkpp\docs\generated\reports\source_contract_classifier_tuning_v0.csv

Writes:
    dottalkpp\docs\generated\reports\source_contract_classifier_update_draft_v1_1.md
    dottalkpp\docs\generated\reports\source_contract_classifier_update_draft_v1_1.csv

Safety:
    REPORT_ONLY
    No source edits.
    No DBF writes.
    No CMDHELPCHK changes.
    No HELP DATA rebuild.
    No source contract repairs.

Purpose:
    Simulate classifier behavior after applying the accepted v1.1 vocabulary decisions.
    This is a draft/report only. It does not update the production probe.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPORT_DIRS = (
    Path("dottalkpp") / "docs" / "generated" / "reports",
    Path("docs") / "generated" / "reports",
)

INVENTORY_JSON = "source_contracts_inventory.json"
INVENTORY_CSV = "source_contracts_inventory.csv"
VOCAB_CSV = "source_contract_extension_vocabulary_v1_1.csv"
TUNING_CSV = "source_contract_classifier_tuning_v0.csv"

OUTPUT_MD = "source_contract_classifier_update_draft_v1_1.md"
OUTPUT_CSV = "source_contract_classifier_update_draft_v1_1.csv"


CORE_FIELDS = {
    "command",
    "commands",
    "owner",
    "category",
    "family",
    "summary",
    "usage",
    "syntax",
    "examples",
    "example",
    "notes",
    "note",
    "related",
    "status",
    "aliases",
    "alias",
    "shortcuts",
    "shortcut",
    "subcommands",
    "subcommand",
    "arguments",
    "argument",
    "returns",
    "errors",
    "warnings",
}

BASE_EXTENSION_FIELDS = {
    "usage-access",
    "effect",
    "mutates",
    "risk",
    "noargs",
    "requires_open_table",
    "requires_current_record",
    "requires_active_order",
    "requires_current_area",
    "requires_selected_area",
    "requires_workspace",
    "requires_file",
    "requires_index",
    "requires_memo",
    "requires_sqlite",
    "mutates_table_data",
    "mutates_cursor",
    "mutates_record_pointer",
    "mutates_order_state",
    "mutates_index_metadata",
    "mutates_session",
    "mutates_setting",
    "mutates_session_ui",
    "mutates_filesystem",
    "mutates_beta_status",
    "mutates_continue_state",
    "writes_dbf_record",
    "writes_dbf_records",
    "writes_table_data",
    "writes_table_buffer",
    "writes_memo",
    "writes_files",
    "writes_filesystem",
    "writes_lmdb_environment",
    "reads_files",
    "reads_index_file",
    "reads_table_records",
    "reads_current_record",
    "reads_current_table",
    "reads_open_work_areas",
    "appends_records",
    "updates_indexes",
    "updates_index",
    "index_maintenance",
    "marks_dirty",
    "marks_stale_field",
    "clears_order_state",
    "clears_console",
    "clears_all_relations",
    "clears_relations_for_table",
    "closes_area",
    "closes_current_area",
    "closes_memo_backend",
    "opens_area",
    "creates_files",
    "creates_index_file",
    "creates_table",
    "overwrites_files",
    "overwrites_index_file",
    "possible_overwrite",
    "archives_existing_environment",
    "drops_or_recreates_lmdb_databases",
    "raw_path_skips_inline_index_update",
    "one_lock_batch",
    "dirty_prompt_gate",
    "resets_table_buffer_state",
    "clears_table_buffer_changes",
    "partial_commit_possible",
    "record_locking",
    "cdx_lmdb_rebuild",
    "scans_records",
    "cursor_restore",
    "restores_cursor_best_effort",
    "changes_current_area_cursor",
    "separate_storage_engine",
    "table_buffer_semantics",
    "auto_is_conservative",
    "default_path_uses_indexes_slot",
    "default_path_uses_order_state",
    "manage_cdx_index_container_metadata",
    "manage_cnx_index_container_metadata",
    "diagnostic_tree_walk",
    "interactive",
    "audible_effect",
    "evaluates_expression",
    "executes_host_command",
    "launches_external_process",
    "delegates_to_append",
    "delegates_to_browse_module",
    "delegates_to_calcwrite",
    "delegates_to_create",
    "delegates_to_delete",
    "delegates_to_replace",
    "contract",
    "no_open_area_allowed",
    "staged_edits",
}

BASE_ALIAS_MAP = {
    "usage_access": "usage-access",
    "usageaccess": "usage-access",
    "no_args": "noargs",
    "no-args": "noargs",
}

REQUIRED_IDENTITY_ONE_OF = ({"command", "commands"},)
REQUIRED_SHAPE_ONE_OF = ({"usage", "syntax"},)
REQUIRED_SINGLE_FIELDS = {"summary"}


@dataclass
class InventoryRecord:
    path: str
    status: str
    has_contract: bool
    contract_count: int = 0
    fields_present: list[str] = field(default_factory=list)
    missing_recommended_fields: list[str] = field(default_factory=list)
    malformed_lines: list[str] = field(default_factory=list)
    unknown_fields: list[str] = field(default_factory=list)
    escrow_candidate: bool = False
    notes: list[str] = field(default_factory=list)


@dataclass
class DraftRow:
    path: str
    lane: str
    has_contract: bool
    current_status: str
    old_escrow_candidate: bool
    recommended_family: str
    draft_action: str
    accepted_by_v1_1: bool
    actionable_usage_backlog: bool
    needs_shape_review: bool
    missing_required_after_v1_1: list[str]
    unrecognized_after_v1_1: list[str]
    malformed_after_v1_1: bool
    notes: list[str]


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
    if ";" in text:
        return [p.strip() for p in text.split(";") if p.strip()]
    if "," in text:
        return [p.strip() for p in text.split(",") if p.strip()]
    return [text]


def normalize_field(field: str, alias_map: dict[str, str]) -> str:
    key = field.strip().lower().replace(" ", "_")
    return alias_map.get(key, key)


def find_report_dir(root: Path, explicit: str | None) -> Path:
    if explicit:
        d = root / explicit
        if not d.is_dir():
            raise SystemExit(f"Report directory not found: {d}")
        return d

    for rel in REPORT_DIRS:
        d = root / rel
        if (d / INVENTORY_JSON).is_file() and (d / VOCAB_CSV).is_file():
            return d

    checked = "\n".join(str(root / rel) for rel in REPORT_DIRS)
    raise SystemExit(f"Could not find required reports. Checked:\n{checked}")


def load_inventory(report_dir: Path) -> tuple[dict[str, Any], list[InventoryRecord], list[str]]:
    notes: list[str] = []
    json_path = report_dir / INVENTORY_JSON
    csv_path = report_dir / INVENTORY_CSV

    summary: dict[str, Any] = {}
    records: list[InventoryRecord] = []

    if json_path.is_file():
        payload = json.loads(json_path.read_text(encoding="utf-8"))
        summary = dict(payload.get("summary", {}))
        for item in payload.get("records", []):
            records.append(InventoryRecord(
                path=str(item.get("path", "")),
                status=str(item.get("status", "")),
                has_contract=parse_bool(item.get("has_contract", False)),
                contract_count=int(item.get("contract_count", 0) or 0),
                fields_present=parse_list(item.get("fields_present")),
                missing_recommended_fields=parse_list(item.get("missing_recommended_fields")),
                malformed_lines=parse_list(item.get("malformed_lines")),
                unknown_fields=parse_list(item.get("unknown_fields")),
                escrow_candidate=parse_bool(item.get("escrow_candidate", False)),
                notes=parse_list(item.get("notes")),
            ))
        notes.append(f"read inventory JSON: {json_path}")
    elif csv_path.is_file():
        with csv_path.open("r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            for item in reader:
                records.append(InventoryRecord(
                    path=str(item.get("path", "")),
                    status=str(item.get("status", "")),
                    has_contract=parse_bool(item.get("has_contract", False)),
                    contract_count=int(item.get("contract_count", 0) or 0),
                    fields_present=parse_list(item.get("fields_present")),
                    missing_recommended_fields=parse_list(item.get("missing_recommended_fields")),
                    malformed_lines=parse_list(item.get("malformed_lines")),
                    unknown_fields=parse_list(item.get("unknown_fields")),
                    escrow_candidate=parse_bool(item.get("escrow_candidate", False)),
                    notes=parse_list(item.get("notes")),
                ))
        notes.append(f"read inventory CSV: {csv_path}")
    else:
        raise SystemExit(f"Missing inventory input: {json_path} or {csv_path}")

    return summary, records, notes


def load_vocabulary(report_dir: Path) -> tuple[set[str], dict[str, str], list[dict[str, str]], list[str]]:
    path = report_dir / VOCAB_CSV
    if not path.is_file():
        raise SystemExit(f"Missing vocabulary input: {path}")

    accepted_extensions: set[str] = set()
    aliases: dict[str, str] = dict(BASE_ALIAS_MAP)
    decisions: list[dict[str, str]] = []

    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            field = str(row.get("field", "")).strip().lower()
            recommendation = str(row.get("recommendation", "")).strip()
            canonical = str(row.get("canonical_field", "")).strip().lower() or field
            decisions.append({
                "field": field,
                "recommendation": recommendation,
                "canonical_field": canonical,
                "count": str(row.get("count", "")),
                "rationale": str(row.get("rationale", "")),
            })

            if recommendation == "ACCEPT_EXTENSION":
                accepted_extensions.add(canonical)
                accepted_extensions.add(field)
            elif recommendation == "ACCEPT_ALIAS":
                aliases[field] = canonical
                accepted_extensions.add(canonical)

    notes = [f"read vocabulary CSV: {path}"]
    return accepted_extensions, aliases, decisions, notes


def load_tuning_counts(report_dir: Path) -> dict[str, int]:
    path = report_dir / TUNING_CSV
    counts: Counter[str] = Counter()
    if not path.is_file():
        return {}
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            counts[str(row.get("action_class", ""))] += 1
    return dict(counts)


def norm(path: str) -> str:
    return path.replace("\\", "/").lower()


def fname(path: str) -> str:
    return norm(path).rsplit("/", 1)[-1]


def lane_for_path(path: str) -> str:
    p = norm(path)
    name = fname(path)

    if p.startswith("src/cli/"):
        if name.startswith("cmd_") or "shell_commands" in name or "cmdhelp" in name or "help" in name:
            return "cli_command_help_surface"
        return "cli_support"
    if p.startswith("include/cli/"):
        return "cli_headers"
    if p.startswith("src/xexpr/") or p.startswith("include/xexpr"):
        return "expression_engine"
    if p.startswith("src/xbase/") or p.startswith("include/xbase") or p == "include/xbase.hpp":
        return "xbase_storage_engine"
    if p.startswith("src/xindex/") or p.startswith("include/xindex"):
        return "index_engine"
    if p.startswith("src/memo/") or p.startswith("include/memo"):
        return "memo_engine"
    if p.startswith("src/tv/") or p.startswith("include/tv"):
        return "tui_tv_layer"
    if p.startswith("bindings/") or p.startswith("src/python") or "pydottalk" in p:
        return "bindings_python"
    if p.startswith("dev/") or p.startswith("tests/") or "/test" in p:
        return "test_dev_harness"
    if p.endswith(".hpp") or p.endswith(".h"):
        return "public_or_shared_header"
    return "other_source"


def command_usage_target(path: str) -> bool:
    p = norm(path)
    name = fname(path)
    if p.startswith("src/cli/cmd_") and name.endswith(".cpp"):
        return True
    if p.startswith("src/cli/") and name in {
        "shell_commands.cpp",
        "cmdhelp.cpp",
        "cmd_help.cpp",
        "cmd_dothelp.cpp",
        "helpdata_cmdhelp_bridge.cpp",
    }:
        return True
    return False


def recommended_family(path: str) -> str:
    p = norm(path)
    name = fname(path)
    lane = lane_for_path(path)

    if command_usage_target(path):
        return "@dottalk.usage v1"
    if lane == "expression_engine":
        if name.startswith("fn_") or "function" in name:
            return "selfdoc.function_contract"
        return "selfdoc.api_contract" if p.startswith("include/") else "selfdoc.function_contract"
    if lane in {"xbase_storage_engine", "index_engine", "memo_engine"}:
        return "selfdoc.api_contract" if p.startswith("include/") else "selfdoc.engine_contract"
    if lane == "tui_tv_layer":
        return "selfdoc.ui_contract"
    if lane == "bindings_python":
        return "selfdoc.binding_contract"
    if lane == "test_dev_harness":
        return "selfdoc.test_contract or exclude_from_usage_contract"
    if lane in {"cli_headers", "public_or_shared_header"}:
        return "selfdoc.api_contract"
    return "manual_classification"


def required_missing(fields: set[str]) -> list[str]:
    missing: list[str] = []
    for group in REQUIRED_IDENTITY_ONE_OF:
        if not (fields & group):
            missing.append("command_or_commands")
    for field in REQUIRED_SINGLE_FIELDS:
        if field not in fields:
            missing.append(field)
    for group in REQUIRED_SHAPE_ONE_OF:
        if not (fields & group):
            missing.append("usage_or_syntax")
    return missing


def classify_record(rec: InventoryRecord, accepted_fields: set[str], alias_map: dict[str, str]) -> DraftRow:
    lane = lane_for_path(rec.path)
    family = recommended_family(rec.path)
    target = command_usage_target(rec.path)
    notes: list[str] = []

    normalized_fields = {normalize_field(f, alias_map) for f in rec.fields_present}
    missing = required_missing(normalized_fields) if rec.has_contract and target else []
    unrecognized = sorted(f for f in normalized_fields if f and f not in accepted_fields)
    malformed = bool(rec.malformed_lines)

    actionable = target and not rec.has_contract

    if actionable:
        action = "action_required_add_command_usage_contract"
        accepted = False
        shape_review = False
        notes.append("true missing command/help usage candidate")
    elif target and rec.has_contract:
        if missing or unrecognized or malformed:
            action = "review_existing_command_contract_shape"
            accepted = False
            shape_review = True
            if missing:
                notes.append("missing required: " + ", ".join(missing))
            if unrecognized:
                notes.append("unrecognized fields: " + ", ".join(unrecognized))
            if malformed:
                notes.append("malformed lines remain")
        else:
            action = "accepted_existing_command_contract"
            accepted = True
            shape_review = False
            notes.append("accepted by draft v1.1 classifier")
    elif family == "manual_classification":
        action = "manual_classification"
        accepted = False
        shape_review = False
    elif "api_contract" in family:
        action = "alternate_contract_api_or_exclude"
        accepted = False
        shape_review = False
    elif "function_contract" in family:
        action = "alternate_contract_function"
        accepted = False
        shape_review = False
    elif "engine_contract" in family:
        action = "alternate_contract_engine"
        accepted = False
        shape_review = False
    elif "ui_contract" in family:
        action = "alternate_contract_ui"
        accepted = False
        shape_review = False
    elif "binding_contract" in family:
        action = "alternate_contract_binding"
        accepted = False
        shape_review = False
    elif "test_contract" in family:
        action = "alternate_contract_test_or_exclude"
        accepted = False
        shape_review = False
    else:
        action = "manual_classification"
        accepted = False
        shape_review = False

    return DraftRow(
        path=rec.path,
        lane=lane,
        has_contract=rec.has_contract,
        current_status=rec.status,
        old_escrow_candidate=rec.escrow_candidate,
        recommended_family=family,
        draft_action=action,
        accepted_by_v1_1=accepted,
        actionable_usage_backlog=actionable,
        needs_shape_review=shape_review,
        missing_required_after_v1_1=missing,
        unrecognized_after_v1_1=unrecognized,
        malformed_after_v1_1=malformed,
        notes=notes,
    )


def write_csv(path: Path, rows: list[DraftRow]) -> None:
    fieldnames = [
        "path",
        "lane",
        "has_contract",
        "current_status",
        "old_escrow_candidate",
        "recommended_family",
        "draft_action",
        "accepted_by_v1_1",
        "actionable_usage_backlog",
        "needs_shape_review",
        "missing_required_after_v1_1",
        "unrecognized_after_v1_1",
        "malformed_after_v1_1",
        "notes",
    ]

    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({
                "path": row.path,
                "lane": row.lane,
                "has_contract": row.has_contract,
                "current_status": row.current_status,
                "old_escrow_candidate": row.old_escrow_candidate,
                "recommended_family": row.recommended_family,
                "draft_action": row.draft_action,
                "accepted_by_v1_1": row.accepted_by_v1_1,
                "actionable_usage_backlog": row.actionable_usage_backlog,
                "needs_shape_review": row.needs_shape_review,
                "missing_required_after_v1_1": "; ".join(row.missing_required_after_v1_1),
                "unrecognized_after_v1_1": "; ".join(row.unrecognized_after_v1_1),
                "malformed_after_v1_1": row.malformed_after_v1_1,
                "notes": "; ".join(row.notes),
            })


def md_escape(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def write_md(path: Path, csv_path: Path, inventory_summary: dict[str, Any], load_notes: list[str], vocab_decisions: list[dict[str, str]], rows: list[DraftRow], tuning_counts: dict[str, int]) -> None:
    action_counts = Counter(row.draft_action for row in rows)
    family_counts = Counter(row.recommended_family for row in rows)
    lane_counts = Counter(row.lane for row in rows)
    accepted = [row for row in rows if row.accepted_by_v1_1]
    shape_review = [row for row in rows if row.needs_shape_review]
    actionable = [row for row in rows if row.actionable_usage_backlog]
    unrecognized = Counter()
    missing = Counter()
    for row in rows:
        for field in row.unrecognized_after_v1_1:
            unrecognized[field] += 1
        for field in row.missing_required_after_v1_1:
            missing[field] += 1

    decision_counts = Counter(d["recommendation"] for d in vocab_decisions)

    lines: list[str] = []
    lines.append("# Source Contract Classifier Update Draft v1.1")
    lines.append("")
    lines.append(f"Generated UTC: `{datetime.now(timezone.utc).isoformat()}`")
    lines.append("")
    lines.append("Safety class: `REPORT_ONLY`")
    lines.append("")
    lines.append("## Scope")
    lines.append("")
    lines.append("This report simulates a draft classifier update using the v1.1 extension vocabulary decisions. It does not edit source files, write DBFs, modify CMDHELPCHK, rebuild HELP DATA, or repair headers.")
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
    lines.append("")
    lines.append("## Executive summary")
    lines.append("")
    lines.append(f"- Records reviewed: `{len(rows)}`")
    lines.append(f"- Previous broad escrow candidates: `{inventory_summary.get('escrow_candidate_count', 'unknown')}`")
    lines.append(f"- Actionable missing command/help usage contracts after v1.1 draft: `{len(actionable)}`")
    lines.append(f"- Existing command contracts accepted after v1.1 draft: `{len(accepted)}`")
    lines.append(f"- Existing command contracts needing shape review after v1.1 draft: `{len(shape_review)}`")
    lines.append(f"- Remaining distinct unrecognized fields after v1.1 draft: `{len(unrecognized)}`")
    lines.append("")
    lines.append("The v1.1 draft keeps the rule that `usage OR syntax` satisfies the command-shape field. It adds accepted extension fields and aliases from the v1.1 vocabulary report for simulation only.")
    lines.append("")
    lines.append("## v1.1 vocabulary decision counts")
    lines.append("")
    lines.append("| Vocabulary recommendation | Count |")
    lines.append("|---|---:|")
    for rec, count in decision_counts.most_common():
        lines.append(f"| `{md_escape(rec)}` | {count} |")
    lines.append("")
    lines.append("## Comparison to classifier tuning v0")
    lines.append("")
    if tuning_counts:
        lines.append("| v0 action class | v0 count |")
        lines.append("|---|---:|")
        for action, count in sorted(tuning_counts.items(), key=lambda x: (-x[1], x[0])):
            lines.append(f"| `{md_escape(action)}` | {count} |")
        lines.append("")
    lines.append("| v1.1 draft action class | Count |")
    lines.append("|---|---:|")
    for action, count in action_counts.most_common():
        lines.append(f"| `{md_escape(action)}` | {count} |")
    lines.append("")
    lines.append("## Recommended family counts")
    lines.append("")
    lines.append("| Recommended family | Count |")
    lines.append("|---|---:|")
    for family, count in family_counts.most_common():
        lines.append(f"| `{md_escape(family)}` | {count} |")
    lines.append("")
    lines.append("## Lane counts")
    lines.append("")
    lines.append("| Lane | Count |")
    lines.append("|---|---:|")
    for lane, count in lane_counts.most_common():
        lines.append(f"| `{md_escape(lane)}` | {count} |")
    lines.append("")
    lines.append("## Actionable missing command/help usage contracts")
    lines.append("")
    if not actionable:
        lines.append("No actionable missing command/help usage contracts remain.")
    else:
        lines.append("| Path | Lane | Recommended family |")
        lines.append("|---|---|---|")
        for row in sorted(actionable, key=lambda r: r.path.lower()):
            lines.append(f"| `{md_escape(row.path)}` | `{md_escape(row.lane)}` | `{md_escape(row.recommended_family)}` |")
    lines.append("")
    lines.append("## Existing command contracts needing shape review after v1.1 draft")
    lines.append("")
    if not shape_review:
        lines.append("No existing command contracts need shape review under v1.1 draft rules.")
    else:
        lines.append("| Path | Missing required | Unrecognized fields | Malformed |")
        lines.append("|---|---|---|---:|")
        for row in sorted(shape_review, key=lambda r: r.path.lower())[:250]:
            lines.append(
                f"| `{md_escape(row.path)}` | {md_escape(', '.join(row.missing_required_after_v1_1))} | "
                f"{md_escape(', '.join(row.unrecognized_after_v1_1))} | {row.malformed_after_v1_1} |"
            )
        if len(shape_review) > 250:
            lines.append(f"| ... | ... | ... | `{len(shape_review) - 250} more omitted from markdown table` |")
    lines.append("")
    lines.append("## Remaining missing required fields")
    lines.append("")
    if not missing:
        lines.append("No missing required fields remain among existing command usage contracts.")
    else:
        lines.append("| Missing required field | Count |")
        lines.append("|---|---:|")
        for field, count in missing.most_common():
            lines.append(f"| `{md_escape(field)}` | {count} |")
    lines.append("")
    lines.append("## Remaining unrecognized fields after v1.1 draft")
    lines.append("")
    if not unrecognized:
        lines.append("No unrecognized fields remain under v1.1 draft rules.")
    else:
        lines.append("| Field | Count |")
        lines.append("|---|---:|")
        for field, count in unrecognized.most_common(100):
            lines.append(f"| `{md_escape(field)}` | {count} |")
    lines.append("")
    lines.append("## Draft classifier update rules")
    lines.append("")
    lines.append("1. Limit `@dottalk.usage v1` requirement to command/help surfaces.")
    lines.append("2. Treat `usage OR syntax` as satisfying the command-shape requirement.")
    lines.append("3. Accept base v0 core fields, base v0 safety/effect extension fields, and v1.1 fields marked `ACCEPT_EXTENSION`.")
    lines.append("4. Normalize fields marked `ACCEPT_ALIAS` internally, but do not rewrite source headers.")
    lines.append("5. Preserve exact header text and header hashes; normalization is classifier-only and must occur after hashing.")
    lines.append("6. Keep alternate contract families separate from command usage contracts.")
    lines.append("7. Continue to report `ONE_OFF_REVIEW`, `REVIEW_BEFORE_ACCEPT`, and malformed fields as shape-review items.")
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
    parser = argparse.ArgumentParser(description="Simulate source contract classifier update draft v1.1.")
    parser.add_argument("--root", default=".", help="Project root. Default: current directory, normally D:\\code\\ccode.")
    parser.add_argument("--report-dir", default=None, help="Optional report directory relative to root.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = Path(args.root).resolve()
    report_dir = find_report_dir(root, args.report_dir)

    inventory_summary, records, load_notes = load_inventory(report_dir)
    accepted_extensions, alias_map, vocab_decisions, vocab_notes = load_vocabulary(report_dir)
    tuning_counts = load_tuning_counts(report_dir)
    load_notes.extend(vocab_notes)

    accepted_fields = CORE_FIELDS | BASE_EXTENSION_FIELDS | accepted_extensions | set(alias_map.keys()) | set(alias_map.values())

    draft_rows = [
        classify_record(rec, accepted_fields=accepted_fields, alias_map=alias_map)
        for rec in records
    ]

    out_md = report_dir / OUTPUT_MD
    out_csv = report_dir / OUTPUT_CSV

    write_csv(out_csv, draft_rows)
    write_md(out_md, out_csv, inventory_summary, load_notes, vocab_decisions, draft_rows, tuning_counts)

    print("SelfDoc source contract classifier update draft v1.1 complete.")
    print(f"Read report directory: {report_dir}")
    print(f"Records reviewed: {len(records)}")
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
