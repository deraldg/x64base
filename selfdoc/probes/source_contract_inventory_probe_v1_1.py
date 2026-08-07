#!/usr/bin/env python3
"""
source_contract_inventory_probe_v1_1.py

Versioned REPORT_ONLY SelfDoc source contract inventory probe, hotfix_001.

Run from:
    D:\code\ccode

Scans:
    src\
    include\

Writes only:
    dottalkpp\docs\generated\reports\source_contracts_inventory_v1_1.md
    dottalkpp\docs\generated\reports\source_contracts_inventory_v1_1.csv
    dottalkpp\docs\generated\reports\source_contracts_inventory_v1_1.json
    dottalkpp\docs\generated\reports\source_contract_inventory_v0_vs_v1_1.md

Safety:
    REPORT_ONLY
    Does not edit source.
    Does not write DBFs.
    Does not modify CMDHELPCHK.
    Does not rebuild HELP DATA.
    Does not repair headers.
    Does not overwrite v0 probe or v0 reports.

hotfix_001:
    - Carries forward accepted v1.1 vocabulary from:
        source_contract_extension_vocabulary_v1_1.csv
        source_contract_inventory_v1_1_classifier_gap_review.csv
    - Adds command-scope roles:
        simple command
        command family
        subsystem / applet
        command registry
        command dispatcher
        command helper
        help / metadata engine
    - Reclassifies shell_commands.cpp as registry infrastructure.
    - Reclassifies cmdhelp.cpp as HELP subsystem / command-family usage candidate.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from collections import Counter
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Optional


SAFETY_CLASS = "REPORT_ONLY"
PROBE_VERSION = "v1.1-hotfix_004_writer_binding"
MARKER = "@dottalk.usage v1"

DEFAULT_SCAN_DIRS = ("src", "include")
SOURCE_SUFFIXES = {".c", ".cc", ".cpp", ".cxx", ".h", ".hh", ".hpp", ".hxx"}

REPORT_DIR = Path("dottalkpp") / "docs" / "generated" / "reports"
OUT_MD = REPORT_DIR / "source_contracts_inventory_v1_1.md"
OUT_CSV = REPORT_DIR / "source_contracts_inventory_v1_1.csv"
OUT_JSON = REPORT_DIR / "source_contracts_inventory_v1_1.json"
OUT_COMPARE_MD = REPORT_DIR / "source_contract_inventory_v0_vs_v1_1.md"

V0_JSON = REPORT_DIR / "source_contracts_inventory.json"
DRAFT_CSV = REPORT_DIR / "source_contract_classifier_update_draft_v1_1.csv"
VOCAB_CSV = REPORT_DIR / "source_contract_extension_vocabulary_v1_1.csv"
GAP_REVIEW_CSV = REPORT_DIR / "source_contract_inventory_v1_1_classifier_gap_review.csv"


CORE_FIELDS = {
    "alias", "aliases", "argument", "arguments", "category", "command", "commands",
    "errors", "example", "examples", "family", "note", "notes", "owner", "related",
    "returns", "shortcut", "shortcuts", "status", "subcommand", "subcommands",
    "summary", "syntax", "usage", "warnings",
}

RECOMMENDED_FIELDS = {"owner", "category", "status", "risk", "mutates", "related"}

BASE_EXTENSION_FIELDS = {
    "effect", "mutates", "risk", "usage-access", "noargs",
    "requires_open_table", "requires_current_record", "requires_active_order",
    "requires_current_area", "requires_selected_area", "requires_workspace",
    "requires_file", "requires_index", "requires_memo", "requires_sqlite",
    "mutates_cursor", "mutates_table_data", "mutates_record_pointer",
    "mutates_order_state", "mutates_index_metadata", "mutates_index_backend",
    "mutates_relation_state", "mutates_session", "mutates_setting",
    "mutates_session_settings", "mutates_session_ui", "mutates_filesystem",
    "mutates_path_state", "mutates_filter_state", "mutates_table_file",
    "mutates_beta_status", "mutates_continue_state", "mutates_current_area",
    "writes_files", "writes_filesystem", "writes_console", "writes_dbf",
    "writes_dbf_record", "writes_dbf_records", "writes_table_data",
    "writes_table_buffer", "writes_memo", "writes_lmdb_environment",
    "writes_index_file", "writes_index_files", "reads_files", "reads_filesystem",
    "reads_index_data", "reads_index_file", "reads_table_records",
    "reads_current_record", "reads_current_table", "reads_open_work_areas",
    "reads_workspace_state", "reads_schema", "appends_records", "updates_indexes",
    "updates_index", "index_maintenance", "marks_dirty", "marks_stale_field",
    "clears_order_state", "clears_console", "clears_all_relations",
    "clears_relations_for_table", "clears_error_state", "closes_area",
    "closes_current_area", "closes_table", "closes_memo_backend", "opens_area",
    "opens_sqlite_db", "creates_files", "creates_index_file", "creates_table",
    "overwrites_files", "overwrites_index_file", "possible_overwrite",
    "archives_existing_environment", "drops_or_recreates_lmdb_databases",
    "raw_path_skips_inline_index_update", "one_lock_batch", "dirty_prompt_gate",
    "resets_table_buffer_state", "clears_table_buffer_changes",
    "partial_commit_possible", "record_locking", "cdx_lmdb_rebuild",
    "scans_records", "cursor_restore", "restores_cursor_best_effort",
    "changes_current_area_cursor", "separate_storage_engine",
    "table_buffer_semantics", "auto_is_conservative",
    "default_path_uses_indexes_slot", "default_path_uses_order_state",
    "manage_cdx_index_container_metadata", "manage_cnx_index_container_metadata",
    "diagnostic_tree_walk", "interactive", "audible_effect", "evaluates_expression",
    "executes_command", "executes_commands", "executes_host_command",
    "executes_shell", "executes_sql", "launches_external_process", "launches_ui",
    "delegates_to_append", "delegates_to_browse_module", "delegates_to_calcwrite",
    "delegates_to_create", "delegates_to_delete", "delegates_to_replace",
    "contract", "no_open_area_allowed", "staged_edits",
    "allow_no_open_table", "area_state", "batch_safe", "buffer_semantics",
    "builds_lmdb", "case_sensitive", "changes_paths", "clears_filter",
    "clears_scope", "compatibility", "creates_metadata", "creates_relation",
    "creates_workspace", "deleted_record_policy", "depends_on_active_area",
    "diagnostic", "dispatch", "educational", "error_state", "expression_context",
    "file_dialog", "filter_semantics", "help_surface", "index_order",
    "lmdb_backend", "loads_workspace", "memo_semantics", "metadata_lane",
    "multi_area", "opens_table", "parser_surface", "path_slot", "prints_output",
    "reads_dbf_header", "reads_metadata", "reads_workspace", "relation_graph",
    "requires_relation", "requires_sql", "requires_transaction",
    "restores_workspace", "safe_noop", "schema_semantics", "script_control",
    "session_only", "side_effect", "sql_bridge", "table_flavor",
    "touches_filesystem", "transactional", "tuple_surface", "ui_surface",
    "validates_metadata", "workspace_state", "writes_metadata", "writes_workspace",
}

BASE_ALIAS_MAP = {
    "mutates_data": "mutates_table_data",
    "usage_access": "usage-access",
    "usageaccess": "usage-access",
    "no_args": "noargs",
    "no-args": "noargs",
    "writes_file": "writes_files",
    "reads_file": "reads_files",
    "creates_file": "creates_files",
    "overwrites_file": "overwrites_files",
    "requires_table": "requires_open_table",
    "requires_area": "requires_current_area",
    "requires_record": "requires_current_record",
    "changes_cursor": "mutates_cursor",
    "changes_order": "mutates_order_state",
}


@dataclass
class Vocabulary:
    accepted_extensions: set[str] = field(default_factory=set)
    alias_map: dict[str, str] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)


@dataclass
class Record:
    path: str
    lane: str
    command_scope_role: str
    recommended_family: str
    lifecycle_class: str
    has_contract: bool
    contract_count: int
    contract_marker: str
    status: str
    action_class: str
    is_actionable_command_usage_backlog: bool
    is_broad_escrow_candidate: bool
    is_shape_review_candidate: bool
    missing_required_fields: list[str] = field(default_factory=list)
    unrecognized_fields: list[str] = field(default_factory=list)
    accepted_extension_fields: list[str] = field(default_factory=list)
    alias_fields: list[str] = field(default_factory=list)
    malformed: bool = False
    header_hash: str = ""
    header_start_line: int = 0
    header_end_line: int = 0
    owner: str = ""
    command: str = ""
    commands: str = ""
    summary_present: bool = False
    usage_present: bool = False
    syntax_present: bool = False
    risk_present: bool = False
    mutates_present: bool = False
    related_present: bool = False
    notes: list[str] = field(default_factory=list)
    header_text: str = ""


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
    sep = ";" if ";" in text else ","
    return [part.strip() for part in text.split(sep) if part.strip()]


def normalize_key(value: str) -> str:
    return value.strip().lower().replace(" ", "_").replace("-", "-")


def normalize_field(field: str, alias_map: dict[str, str]) -> str:
    key = normalize_key(field)
    return alias_map.get(key, key)


def load_external_vocabulary(report_dir: Path) -> Vocabulary:
    vocab = Vocabulary(
        accepted_extensions=set(BASE_EXTENSION_FIELDS),
        alias_map=dict(BASE_ALIAS_MAP),
        notes=[],
    )

    if VOCAB_CSV.is_file():
        try:
            with VOCAB_CSV.open("r", encoding="utf-8", newline="") as f:
                for row in csv.DictReader(f):
                    field = normalize_key(str(row.get("field", "")))
                    rec = str(row.get("recommendation", "")).strip()
                    canonical = normalize_key(str(row.get("canonical_field", ""))) or field
                    if not field:
                        continue
                    if rec == "ACCEPT_EXTENSION":
                        vocab.accepted_extensions.add(field)
                        vocab.accepted_extensions.add(canonical)
                    elif rec == "ACCEPT_ALIAS":
                        vocab.alias_map[field] = canonical
                        vocab.accepted_extensions.add(canonical)
            vocab.notes.append(f"loaded vocabulary decisions: {VOCAB_CSV}")
        except Exception as exc:
            vocab.notes.append(f"failed to load vocabulary decisions: {type(exc).__name__}: {exc}")
    else:
        vocab.notes.append(f"vocabulary decision file not found: {VOCAB_CSV}")

    if GAP_REVIEW_CSV.is_file():
        try:
            added = 0
            with GAP_REVIEW_CSV.open("r", encoding="utf-8", newline="") as f:
                for row in csv.DictReader(f):
                    for col in ("should_have_accepted_fields", "missing_from_impl_vocab"):
                        for field in parse_list(row.get(col, "")):
                            normalized = normalize_key(field)
                            if normalized:
                                vocab.accepted_extensions.add(normalized)
                                added += 1
            vocab.notes.append(f"loaded accepted gap fields: {GAP_REVIEW_CSV} ({added} entries scanned)")
        except Exception as exc:
            vocab.notes.append(f"failed to load gap review fields: {type(exc).__name__}: {exc}")
    else:
        vocab.notes.append(f"classifier gap review file not found: {GAP_REVIEW_CSV}")

    return vocab


def is_source_file(path: Path) -> bool:
    return path.is_file() and path.suffix.lower() in SOURCE_SUFFIXES


def iter_source_files(root: Path, scan_dirs: Iterable[str]) -> Iterable[Path]:
    for rel in scan_dirs:
        base = root / rel
        if base.is_dir():
            for path in base.rglob("*"):
                if is_source_file(path):
                    yield path


def read_text(path: Path) -> tuple[str, list[str]]:
    raw = path.read_bytes()
    notes: list[str] = []
    for enc in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            text = raw.decode(enc, errors="strict")
            if enc not in ("utf-8", "utf-8-sig"):
                notes.append(f"decoded_as={enc}")
            return text, notes
        except UnicodeDecodeError:
            pass
    text = raw.decode("utf-8", errors="surrogateescape")
    notes.append("decoded_as=utf-8-surrogateescape")
    return text, notes


def line_number_for_offset(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def find_contract_blocks(text: str) -> list[tuple[int, int, str]]:
    # Capture hotfix 002 / malformed-assignment hotfix 003:
    # - For line-comment contracts, the @dottalk.usage v1 marker line is the contract start.
    # - Contiguous // lines before the marker are optional preamble/context, not contract payload.
    # - Contiguous // lines after the marker remain part of the contract.
    # - Block comments are still captured as an enclosing block; parse_fields() ignores pre-marker payload.
    blocks: list[tuple[int, int, str]] = []

    for match in re.finditer(re.escape(MARKER), text):
        marker_start = match.start()

        block_start = text.rfind("/*", 0, marker_start)
        block_end = text.find("*/", match.end())
        if block_start != -1 and block_end != -1:
            prior_close = text.rfind("*/", 0, marker_start)
            if prior_close < block_start:
                end = block_end + 2
                blocks.append((block_start, end, text[block_start:end]))
                continue

        line_start = text.rfind("\\n", 0, marker_start) + 1
        line_end = text.find("\\n", marker_start)
        if line_end == -1:
            line_end = len(text)

        start = line_start
        end = line_end

        while end < len(text):
            next_start = end + 1
            if next_start >= len(text):
                break

            next_end = text.find("\\n", next_start)
            if next_end == -1:
                next_end = len(text)

            next_line = text[next_start:next_end]

            if next_line.lstrip().startswith("//"):
                end = next_end
                if next_end == len(text):
                    break
                continue

            if next_line.strip() == "":
                after_blank_start = next_end + 1
                if after_blank_start >= len(text):
                    break
                after_blank_end = text.find("\\n", after_blank_start)
                if after_blank_end == -1:
                    after_blank_end = len(text)
                after_blank_line = text[after_blank_start:after_blank_end]
                if after_blank_line.lstrip().startswith("//"):
                    end = next_end
                    continue

            break

        blocks.append((start, end, text[start:end]))

    unique = {(s, e): b for s, e, b in blocks}
    return [(s, e, b) for (s, e), b in sorted(unique.items())]


def strip_comment_prefix(line: str) -> str:
    s = line.strip()
    if s.startswith("/*"):
        s = s[2:].lstrip()
    if s.endswith("*/"):
        s = s[:-2].rstrip()
    if s.startswith("//"):
        s = s[2:].lstrip()
    if s.startswith("*"):
        s = s[1:].lstrip()
    return s.rstrip()


def parse_fields(header_text: str) -> tuple[dict[str, list[str]], list[str]]:
    # Capture hotfix 002 / malformed-assignment hotfix 003:
    # - Lines before @dottalk.usage v1 are preamble/context, not payload.
    # - Preamble lines must not make the contract malformed.
    # - Field parsing begins only after the marker has been seen.
    # - Continuation lines after a parsed field are still attached to that field.
    fields: dict[str, list[str]] = {}
    malformed: list[str] = []
    seen_marker = False
    ignored_preamble_lines = 0

    for raw_line in header_text.splitlines():
        line = strip_comment_prefix(raw_line)

        if not line:
            continue

        if MARKER in line:
            seen_marker = True
            continue

        if not seen_marker:
            ignored_preamble_lines += 1
            continue

        if set(line) <= {"-", "=", "_"}:
            continue

        match = re.match(r"^([A-Za-z][A-Za-z0-9_ -]{0,60})\\s*:\\s*(.*)$", line)
        if not match:
            if fields:
                last_key = next(reversed(fields))
                fields[last_key].append(line)
            else:
                malformed.append(line)
            continue

        key = match.group(1).strip().lower().replace(" ", "_")
        value = match.group(2).strip()
        fields.setdefault(key, []).append(value)

    return fields, malformed


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


def command_registry_target(path: str) -> bool:
    p = norm(path)
    name = fname(path)
    return p.startswith("src/cli/") and name in {
        "shell_commands.cpp",
    }


def command_dispatch_target(path: str) -> bool:
    p = norm(path)
    name = fname(path)
    return p.startswith("src/cli/") and name in {
        "shell.cpp",
        "shell_dispatch.cpp",
    }


def help_metadata_engine_target(path: str) -> bool:
    p = norm(path)
    name = fname(path)
    return p.startswith("src/cli/") and name in {
        "helpdata_cmdhelp_bridge.cpp",
        "cmdhelp_miner.cpp",
        "cmdhelp_builder.cpp",
    }


def command_family_target(path: str) -> bool:
    p = norm(path)
    name = fname(path)
    return p.startswith("src/cli/") and name in {
        "cmdhelp.cpp",
        "cmd_help.cpp",
        "cmd_dothelp.cpp",
    }


def command_helper_target(path: str) -> bool:
    p = norm(path)
    name = fname(path)
    return p.startswith("src/cli/") and (
        name.endswith("_helper.cpp") or
        name.endswith("_helpers.cpp") or
        name.endswith("_util.cpp") or
        name.endswith("_utils.cpp")
    )


def simple_command_target(path: str) -> bool:
    p = norm(path)
    name = fname(path)
    return p.startswith("src/cli/cmd_") and name.endswith(".cpp")


def command_usage_target(path: str) -> bool:
    return simple_command_target(path) or command_family_target(path)


def command_scope_role(path: str) -> str:
    if command_registry_target(path):
        return "command_registry"
    if command_dispatch_target(path):
        return "command_dispatcher"
    if help_metadata_engine_target(path):
        return "help_metadata_engine"
    if command_family_target(path):
        return "command_family_or_help_subsystem"
    if command_helper_target(path):
        return "command_helper"
    if simple_command_target(path):
        return "simple_command"
    return "non_command_source"


def recommended_family(path: str) -> str:
    p = norm(path)
    name = fname(path)
    lane = lane_for_path(path)

    if command_registry_target(path):
        return "selfdoc.command_registry_contract"
    if command_dispatch_target(path):
        return "selfdoc.command_dispatch_contract"
    if help_metadata_engine_target(path):
        return "selfdoc.help_metadata_engine_contract"
    if command_family_target(path):
        return "selfdoc.help_subsystem_contract"
    if command_helper_target(path):
        return "selfdoc.command_helper_contract"
    if simple_command_target(path):
        return "@dottalk.usage v1"
    if lane == "expression_engine":
        return "selfdoc.function_contract" if (name.startswith("fn_") or not p.startswith("include/")) else "selfdoc.api_contract"
    if lane in {"xbase_storage_engine", "index_engine", "memo_engine"}:
        return "selfdoc.api_contract" if p.startswith("include/") else "selfdoc.engine_contract"
    if lane == "tui_tv_layer":
        return "selfdoc.ui_contract"
    if lane == "bindings_python":
        return "selfdoc.binding_contract"
    if lane == "test_dev_harness":
        return "selfdoc.test_contract"
    if lane in {"cli_headers", "public_or_shared_header"}:
        return "selfdoc.api_contract"
    return "manual_classification"


def lifecycle_class_for_path(path: str) -> str:
    p = norm(path)
    if p.startswith("src/") or p.startswith("include/"):
        return "CANONICAL"
    return "CANDIDATE"


def action_for_alternate_family(family: str) -> str:
    if family == "selfdoc.command_registry_contract":
        return "alternate_contract_registry"
    if family == "selfdoc.command_dispatch_contract":
        return "alternate_contract_dispatch"
    if family == "selfdoc.command_helper_contract":
        return "alternate_contract_helper"
    if family == "selfdoc.help_metadata_engine_contract":
        return "alternate_contract_help_metadata_engine"
    if family in {"selfdoc.help_subsystem_contract", "selfdoc.command_family_contract"}:
        return "action_required_add_command_family_usage_contract"
    if family == "selfdoc.api_contract":
        return "alternate_contract_api_or_exclude"
    if family == "selfdoc.engine_contract":
        return "alternate_contract_engine"
    if family == "selfdoc.ui_contract":
        return "alternate_contract_ui"
    if family == "selfdoc.function_contract":
        return "alternate_contract_function"
    if family == "selfdoc.binding_contract":
        return "alternate_contract_binding"
    if family == "selfdoc.test_contract":
        return "alternate_contract_test_or_exclude"
    return "manual_classification"


def first_value(fields: dict[str, list[str]], key: str) -> str:
    vals = fields.get(key, [])
    return vals[0] if vals else ""


def required_missing(normalized_fields: set[str]) -> list[str]:
    missing: list[str] = []
    if not ({"command", "commands"} & normalized_fields):
        missing.append("command_or_commands")
    if "summary" not in normalized_fields:
        missing.append("summary")
    if not ({"usage", "syntax"} & normalized_fields):
        missing.append("usage_or_syntax")
    return missing


# ---- SelfDoc malformed-assignment hotfix 003 helpers ----
# These helpers are report-only classifier logic. They do not edit source.
# Doctrine: SelfDoc reports are evidence, not verdicts.

HOTFIX_003_BATCH0_CAPTURE_REVIEW_PATHS = {
    "src/cli/cmd_area.cpp",
    "src/cli/cmd_calcwrite.cpp",
    "src/cli/cmd_close.cpp",
    "src/cli/cmd_color.cpp",
    "src/cli/cmd_commit.cpp",
    "src/cli/cmd_copy.cpp",
    "src/cli/cmd_dir.cpp",
    "src/cli/cmd_foxhelp.cpp",
    "src/cli/cmd_list_lmdb.cpp",
}


def _hotfix003_norm_path(path: object) -> str:
    return str(path or "").replace("\\", "/")


def _hotfix003_has_required_shape(fields: dict[str, list[str]]) -> bool:
    # Command shape is satisfied by command/commands, summary, and usage OR syntax.
    if not isinstance(fields, dict):
        return False
    has_command = bool(fields.get("command") or fields.get("commands"))
    has_summary = bool(fields.get("summary"))
    has_usage_or_syntax = bool(fields.get("usage") or fields.get("syntax"))
    return has_command and has_summary and has_usage_or_syntax


def _hotfix003_marker_is_first_payload_line(header_text: str) -> bool:
    for raw_line in str(header_text or "").splitlines():
        line = strip_comment_prefix(raw_line)
        if not line:
            continue
        return MARKER in line
    return False


def _hotfix003_should_clear_malformed(path: object, header_text: str, fields: dict[str, list[str]], malformed_lines: list[str]) -> bool:
    # Do not carry malformed=True from broad preamble capture when marker-anchored
    # contract payload is clean and required shape is present.
    norm_path = _hotfix003_norm_path(path)
    if norm_path.endswith("cmd_help.cpp"):
        # cmd_help.cpp remains an evidence freshness/hash lane, not a source repair target.
        return False

    if norm_path not in HOTFIX_003_BATCH0_CAPTURE_REVIEW_PATHS:
        # Conservative first pass: only clear the already-reviewed Batch 0
        # capture-only false positives.
        return False

    if not _hotfix003_marker_is_first_payload_line(header_text):
        return False

    if malformed_lines:
        return False

    return _hotfix003_has_required_shape(fields)


def _hotfix003_apply_row(row: dict, header_text: str, fields: dict[str, list[str]], malformed_lines: list[str]) -> dict:
    # Normalize the row after normal classification, without authorizing source repair.
    if not isinstance(row, dict):
        return row

    path = _hotfix003_norm_path(row.get("path", ""))
    if _hotfix003_should_clear_malformed(path, header_text, fields, malformed_lines):
        row["malformed"] = False
        row["malformed_count"] = 0
        row["malformed_lines"] = ""
        row["evidence_lane"] = "CONFIRMED"
        row["secondary_lane"] = "DO_NOT_REPAIR"
        row["source_repair_recommended"] = False
        row["repair_authorized"] = False

        if row.get("action_class") == "review_existing_command_contract_shape":
            row["action_class"] = "accepted_existing_command_contract"

        if row.get("status") in {"shape_review", "review", "malformed"}:
            row["status"] = "accepted"

        notes = str(row.get("notes", "") or "")
        add = "hotfix_003: cleared capture-only malformed flag after marker-anchored clean parse"
        row["notes"] = (notes + "; " + add).strip("; ") if notes else add

    elif path.endswith("cmd_help.cpp"):
        row["evidence_lane"] = "STALE_EVIDENCE"
        row["secondary_lane"] = "DO_NOT_REPAIR"
        row["source_repair_recommended"] = False
        row["repair_authorized"] = False

    return row
# ---- end SelfDoc malformed-assignment hotfix 003 helpers ----


def classify_file(path: Path, root: Path, vocab: Vocabulary) -> Record:
    rel = path.relative_to(root).as_posix()
    lane = lane_for_path(rel)
    role = command_scope_role(rel)
    family = recommended_family(rel)
    lifecycle = lifecycle_class_for_path(rel)
    is_command_target = command_usage_target(rel)

    accepted_fields = CORE_FIELDS | vocab.accepted_extensions | set(vocab.alias_map.keys()) | set(vocab.alias_map.values())

    try:
        text, read_notes = read_text(path)
    except Exception as exc:
        return Record(
            path=rel, lane=lane, command_scope_role=role, recommended_family=family, lifecycle_class=lifecycle,
            has_contract=False, contract_count=0, contract_marker=MARKER, status="read_error",
            action_class="manual_classification", is_actionable_command_usage_backlog=False,
            is_broad_escrow_candidate=True, is_shape_review_candidate=False, malformed=True,
            notes=[f"read_error={type(exc).__name__}: {exc}"],
        )

    blocks = find_contract_blocks(text)
    if not blocks:
        if command_family_target(rel):
            action = "action_required_add_command_family_usage_contract"
            actionable = True
            notes = read_notes + ["family-level command/help subsystem usage candidate"]
        elif simple_command_target(rel):
            action = "action_required_add_command_usage_contract"
            actionable = True
            notes = read_notes + ["simple command usage candidate"]
        else:
            action = action_for_alternate_family(family)
            actionable = False
            notes = read_notes + (
                ["command infrastructure contract candidate"]
                if role in {"command_registry", "command_dispatcher", "command_helper", "help_metadata_engine"}
                else []
            )
        return Record(
            path=rel, lane=lane, command_scope_role=role, recommended_family=family, lifecycle_class=lifecycle,
            has_contract=False, contract_count=0, contract_marker=MARKER, status="missing_contract",
            action_class=action, is_actionable_command_usage_backlog=actionable,
            is_broad_escrow_candidate=True, is_shape_review_candidate=False, notes=notes,
        )

    start, end, header = blocks[0]
    header_hash = hashlib.sha256(header.encode("utf-8", errors="surrogateescape")).hexdigest()

    fields_raw, malformed_lines = parse_fields(header)
    normalized_fields = {normalize_field(k, vocab.alias_map) for k in fields_raw.keys()}

    missing_required = required_missing(normalized_fields) if is_command_target else []
    unrecognized = sorted(k for k in normalized_fields if k not in accepted_fields)
    accepted_ext = sorted(k for k in normalized_fields if k in vocab.accepted_extensions)
    alias_fields = sorted(k for k in fields_raw.keys() if normalize_field(k, vocab.alias_map) != normalize_key(k))
    malformed = bool(malformed_lines)
    has_shape_issue = bool(missing_required or unrecognized or malformed or len(blocks) > 1)

    if is_command_target:
        if has_shape_issue:
            action = "review_existing_command_contract_shape"
            status = "shape_review"
        else:
            action = "accepted_existing_command_family_contract" if command_family_target(rel) else "accepted_existing_command_contract"
            status = "accepted"
    else:
        action = action_for_alternate_family(family)
        status = "alternate_contract_recommended" if family != "manual_classification" else "manual_classification"

    is_shape_review = is_command_target and has_shape_issue
    broad_escrow = (not blocks) or is_shape_review or (not is_command_target and family == "manual_classification")

    return Record(
        path=rel, lane=lane, command_scope_role=role, recommended_family=family, lifecycle_class=lifecycle,
        has_contract=True, contract_count=len(blocks), contract_marker=MARKER, status=status,
        action_class=action, is_actionable_command_usage_backlog=False,
        is_broad_escrow_candidate=broad_escrow, is_shape_review_candidate=is_shape_review,
        missing_required_fields=missing_required, unrecognized_fields=unrecognized,
        accepted_extension_fields=accepted_ext, alias_fields=alias_fields, malformed=malformed,
        header_hash=header_hash, header_start_line=line_number_for_offset(text, start),
        header_end_line=line_number_for_offset(text, end), owner=first_value(fields_raw, "owner"),
        command=first_value(fields_raw, "command"), commands=first_value(fields_raw, "commands"),
        summary_present="summary" in normalized_fields, usage_present="usage" in normalized_fields,
        syntax_present="syntax" in normalized_fields, risk_present="risk" in normalized_fields,
        mutates_present="mutates" in normalized_fields, related_present="related" in normalized_fields,
        notes=read_notes + malformed_lines, header_text=header,
    )


def summarize(records: list[Record], root: Path, scan_dirs: tuple[str, ...], vocab: Vocabulary) -> dict[str, Any]:
    unrecognized = Counter()
    for rec in records:
        for field in rec.unrecognized_fields:
            unrecognized[field] += 1

    accepted_simple = sum(1 for r in records if r.action_class == "accepted_existing_command_contract")
    accepted_family = sum(1 for r in records if r.action_class == "accepted_existing_command_family_contract")

    return {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "root": str(root),
        "safety_class": SAFETY_CLASS,
        "probe_version": PROBE_VERSION,
        "scan_dirs": list(scan_dirs),
        "contract_marker": MARKER,
        "total_records": len(records),
        "files_with_contracts": sum(1 for r in records if r.has_contract),
        "files_missing_contracts": sum(1 for r in records if not r.has_contract),
        "broad_escrow_candidates": sum(1 for r in records if r.is_broad_escrow_candidate),
        "actionable_missing_command_help_usage_contracts": sum(1 for r in records if r.is_actionable_command_usage_backlog),
        "actionable_simple_command_usage_contracts": sum(1 for r in records if r.action_class == "action_required_add_command_usage_contract"),
        "actionable_family_command_usage_contracts": sum(1 for r in records if r.action_class == "action_required_add_command_family_usage_contract"),
        "registry_contract_candidates": sum(1 for r in records if r.action_class == "alternate_contract_registry"),
        "dispatch_contract_candidates": sum(1 for r in records if r.action_class == "alternate_contract_dispatch"),
        "helper_contract_candidates": sum(1 for r in records if r.action_class == "alternate_contract_helper"),
        "help_metadata_engine_contract_candidates": sum(1 for r in records if r.action_class == "alternate_contract_help_metadata_engine"),
        "accepted_existing_command_contracts": accepted_simple + accepted_family,
        "accepted_existing_simple_command_contracts": accepted_simple,
        "accepted_existing_command_family_contracts": accepted_family,
        "existing_command_contracts_needing_shape_review": sum(1 for r in records if r.is_shape_review_candidate),
        "remaining_distinct_unrecognized_fields": len(unrecognized),
        "lane_counts": dict(Counter(r.lane for r in records).most_common()),
        "command_scope_role_counts": dict(Counter(r.command_scope_role for r in records).most_common()),
        "recommended_family_counts": dict(Counter(r.recommended_family for r in records).most_common()),
        "action_class_counts": dict(Counter(r.action_class for r in records).most_common()),
        "status_counts": dict(Counter(r.status for r in records).most_common()),
        "unrecognized_field_counts": dict(unrecognized.most_common()),
        "external_vocabulary_notes": vocab.notes,
        "accepted_extension_count": len(vocab.accepted_extensions),
        "alias_count": len(vocab.alias_map),
        "outputs": {
            "markdown": str(OUT_MD),
            "csv": str(OUT_CSV),
            "json": str(OUT_JSON),
            "comparison": str(OUT_COMPARE_MD),
        },
        "non_mutation_guards": [
            "did_not_edit_source",
            "did_not_write_dbfs",
            "did_not_modify_cmdhelpchk",
            "did_not_rebuild_help_data",
            "did_not_repair_headers",
            "did_not_overwrite_v0_probe",
            "did_not_overwrite_v0_reports",
        ],
    }


def write_json(records: list[Record], summary: dict[str, Any]) -> None:
    OUT_JSON.write_text(
        json.dumps({"summary": summary, "records": [asdict(r) for r in records]}, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def write_csv_report(records: list[Record]) -> None:
    fieldnames = [
        "path", "lane", "command_scope_role", "recommended_family", "lifecycle_class",
        "has_contract", "contract_count", "contract_marker", "status", "action_class",
        "is_actionable_command_usage_backlog", "is_broad_escrow_candidate",
        "is_shape_review_candidate", "missing_required_fields", "unrecognized_fields",
        "accepted_extension_fields", "alias_fields", "malformed", "header_hash",
        "header_start_line", "header_end_line", "owner", "command", "commands",
        "summary_present", "usage_present", "syntax_present", "risk_present",
        "mutates_present", "related_present", "notes",
    ]
    with OUT_CSV.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for rec in records:
            row = asdict(rec)
            row.pop("header_text", None)
            for key, value in list(row.items()):
                if isinstance(value, list):
                    row[key] = "; ".join(str(x) for x in value)
            writer.writerow(row)


def md_escape(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def write_markdown(records: list[Record], summary: dict[str, Any]) -> None:
    actionable = [r for r in records if r.is_actionable_command_usage_backlog]
    shape_review = [r for r in records if r.is_shape_review_candidate]

    lines: list[str] = []
    lines.append("# Source Contracts Inventory v1.1")
    lines.append("")
    lines.append(f"Generated UTC: `{summary['generated_at_utc']}`")
    lines.append("")
    lines.append(f"Safety class: `{summary['safety_class']}`")
    lines.append(f"Probe version: `{summary['probe_version']}`")
    lines.append("")
    lines.append("## Scope")
    lines.append("")
    lines.append("Versioned v1.1 source-contract inventory with hotfix 004 writer binding. It scans `src\\` and `include\\`, carries forward accepted vocabulary from review reports, distinguishes command-scope roles, and writes only v1.1 reports under `dottalkpp\\docs\\generated\\reports`.")
    lines.append("")
    lines.append("## Summary counts")
    lines.append("")
    for key in [
        "total_records",
        "files_with_contracts",
        "files_missing_contracts",
        "broad_escrow_candidates",
        "actionable_missing_command_help_usage_contracts",
        "actionable_simple_command_usage_contracts",
        "actionable_family_command_usage_contracts",
        "registry_contract_candidates",
        "dispatch_contract_candidates",
        "helper_contract_candidates",
        "help_metadata_engine_contract_candidates",
        "accepted_existing_command_contracts",
        "accepted_existing_simple_command_contracts",
        "accepted_existing_command_family_contracts",
        "existing_command_contracts_needing_shape_review",
        "remaining_distinct_unrecognized_fields",
        "accepted_extension_count",
        "alias_count",
    ]:
        lines.append(f"- {key}: `{summary[key]}`")
    lines.append("")
    lines.append("## External vocabulary notes")
    lines.append("")
    for note in summary["external_vocabulary_notes"]:
        lines.append(f"- `{md_escape(note)}`")
    lines.append("")
    lines.append("## Command scope role counts")
    lines.append("")
    lines.append("| Role | Count |")
    lines.append("|---|---:|")
    for role, count in summary["command_scope_role_counts"].items():
        lines.append(f"| `{md_escape(role)}` | {count} |")
    lines.append("")
    lines.append("## Action class counts")
    lines.append("")
    lines.append("| Action class | Count |")
    lines.append("|---|---:|")
    for action, count in summary["action_class_counts"].items():
        lines.append(f"| `{md_escape(action)}` | {count} |")
    lines.append("")
    lines.append("## Recommended family counts")
    lines.append("")
    lines.append("| Recommended family | Count |")
    lines.append("|---|---:|")
    for family, count in summary["recommended_family_counts"].items():
        lines.append(f"| `{md_escape(family)}` | {count} |")
    lines.append("")
    lines.append("## Actionable missing command/help usage contracts")
    lines.append("")
    if not actionable:
        lines.append("No actionable missing command/help usage contracts found.")
    else:
        lines.append("| Path | Role | Lane | Recommended family | Action class |")
        lines.append("|---|---|---|---|---|")
        for rec in sorted(actionable, key=lambda r: r.path.lower()):
            lines.append(f"| `{md_escape(rec.path)}` | `{md_escape(rec.command_scope_role)}` | `{md_escape(rec.lane)}` | `{md_escape(rec.recommended_family)}` | `{md_escape(rec.action_class)}` |")
    lines.append("")
    lines.append("## Existing command contracts needing shape review")
    lines.append("")
    if not shape_review:
        lines.append("No existing command contracts need shape review.")
    else:
        lines.append("| Path | Role | Missing required | Unrecognized fields | Malformed |")
        lines.append("|---|---|---|---|---:|")
        for rec in sorted(shape_review, key=lambda r: r.path.lower())[:250]:
            lines.append(
                f"| `{md_escape(rec.path)}` | `{md_escape(rec.command_scope_role)}` | "
                f"{md_escape(', '.join(rec.missing_required_fields))} | "
                f"{md_escape(', '.join(rec.unrecognized_fields))} | {rec.malformed} |"
            )
    lines.append("")
    lines.append("## Remaining unrecognized fields")
    lines.append("")
    if not summary["unrecognized_field_counts"]:
        lines.append("No unrecognized fields remain.")
    else:
        lines.append("| Field | Count |")
        lines.append("|---|---:|")
        for field, count in list(summary["unrecognized_field_counts"].items())[:100]:
            lines.append(f"| `{md_escape(field)}` | {count} |")
    lines.append("")
    lines.append("## Non-mutation confirmation")
    lines.append("")
    for guard in summary["non_mutation_guards"]:
        lines.append(f"- `{guard}`")

    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def load_v0_summary() -> dict[str, Any]:
    if not V0_JSON.is_file():
        return {}
    try:
        return dict(json.loads(V0_JSON.read_text(encoding="utf-8")).get("summary", {}))
    except Exception as exc:
        return {"load_error": str(exc)}


def load_draft_counts() -> dict[str, int]:
    if not DRAFT_CSV.is_file():
        return {}
    counts = Counter()
    try:
        with DRAFT_CSV.open("r", encoding="utf-8", newline="") as f:
            for row in csv.DictReader(f):
                key = str(row.get("draft_action", ""))
                counts[key] += 1
    except Exception:
        return {}
    return dict(counts)


def write_comparison(summary: dict[str, Any]) -> None:
    v0 = load_v0_summary()
    draft_counts = load_draft_counts()

    lines: list[str] = []
    lines.append("# Source Contract Inventory v0 vs v1.1")
    lines.append("")
    lines.append(f"Generated UTC: `{summary['generated_at_utc']}`")
    lines.append("")
    lines.append("Safety class: `REPORT_ONLY`")
    lines.append("")
    lines.append("This comparison is informational only. It does not overwrite v0 reports and does not promote v1.1 to default.")
    lines.append("")
    lines.append("## Count comparison")
    lines.append("")
    lines.append("| Metric | v0/draft | v1.1 hotfix_001 |")
    lines.append("|---|---:|---:|")
    rows = [
        ("records/files reviewed", v0.get("total_source_files", v0.get("total_records", "")), summary["total_records"]),
        ("files with contracts", v0.get("files_with_contract", v0.get("files_with_contracts", "")), summary["files_with_contracts"]),
        ("files missing contracts", v0.get("files_missing_contract", v0.get("files_missing_contracts", "")), summary["files_missing_contracts"]),
        ("broad escrow candidates", v0.get("escrow_candidate_count", v0.get("broad_escrow_candidates", "")), summary["broad_escrow_candidates"]),
        ("actionable missing command/help usage contracts", "", summary["actionable_missing_command_help_usage_contracts"]),
        ("actionable family command usage contracts", "", summary["actionable_family_command_usage_contracts"]),
        ("registry contract candidates", "", summary["registry_contract_candidates"]),
        ("accepted existing command contracts", draft_counts.get("accepted_existing_command_contract", ""), summary["accepted_existing_command_contracts"]),
        ("shape review command contracts", draft_counts.get("review_existing_command_contract_shape", ""), summary["existing_command_contracts_needing_shape_review"]),
    ]
    for metric, old, new in rows:
        lines.append(f"| {md_escape(metric)} | `{md_escape(old)}` | `{md_escape(new)}` |")
    lines.append("")
    lines.append("## Promotion gate")
    lines.append("")
    lines.append("v1.1 remains a candidate probe until this comparison is reviewed, counts are understood, false positives are classified, and no mutation occurred.")
    lines.append("")
    lines.append("## Non-mutation confirmation")
    lines.append("")
    lines.append("- v0 probe not overwritten.")
    lines.append("- v0 reports not overwritten.")
    lines.append("- No source edits.")
    lines.append("- No DBF writes.")
    lines.append("- No HELP DATA rebuild.")
    lines.append("- No CMDHELPCHK changes.")

    OUT_COMPARE_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def preflight(root: Path, scan_dirs: tuple[str, ...]) -> list[str]:
    warnings: list[str] = []
    for expected in ("src", "include", "dottalkpp", "selfdoc"):
        if not (root / expected).exists():
            warnings.append(f"expected project-root entry missing: {expected}")
    for scan_dir in scan_dirs:
        if not (root / scan_dir).is_dir():
            warnings.append(f"scan directory missing: {scan_dir}")
    return warnings


def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Inventory DotTalk++ source contracts using v1.1 hotfix_001 classifier.")
    parser.add_argument("--root", default=".", help="Project root. Default: current directory, normally D:\\code\\ccode.")
    parser.add_argument("--scan-dir", action="append", dest="scan_dirs", help="Source directory to scan. Default: src and include.")
    parser.add_argument("--quiet", action="store_true", help="Suppress summary output.")
    return parser.parse_args(argv)


def main(argv: Optional[list[str]] = None) -> int:
    args = parse_args(argv)
    root = Path(args.root).resolve()
    scan_dirs = tuple(args.scan_dirs) if args.scan_dirs else DEFAULT_SCAN_DIRS

    warnings = preflight(root, scan_dirs)
    for warning in warnings:
        print(f"WARNING: {warning}")

    vocab = load_external_vocabulary(REPORT_DIR)

    files = sorted(iter_source_files(root, scan_dirs), key=lambda p: p.as_posix().lower())
    records = [classify_file(path, root, vocab) for path in files]
    summary = summarize(records, root, scan_dirs, vocab)
    summary["preflight_warnings"] = warnings

    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    write_json(records, summary)
    write_csv_report(records)
    write_markdown(records, summary)
    write_comparison(summary)

    if not args.quiet:
        print("SelfDoc source contract inventory v1.1 hotfix 004 writer binding complete.")
        print(f"Safety class: {SAFETY_CLASS}")
        print(f"Project root: {root}")
        print(f"Records reviewed: {summary['total_records']}")
        print(f"Files with contracts: {summary['files_with_contracts']}")
        print(f"Files missing contracts: {summary['files_missing_contracts']}")
        print(f"Broad escrow candidates: {summary['broad_escrow_candidates']}")
        print(f"Actionable missing command/help usage contracts: {summary['actionable_missing_command_help_usage_contracts']}")
        print(f"Actionable simple command usage contracts: {summary['actionable_simple_command_usage_contracts']}")
        print(f"Actionable family command usage contracts: {summary['actionable_family_command_usage_contracts']}")
        print(f"Registry contract candidates: {summary['registry_contract_candidates']}")
        print(f"Accepted existing command contracts: {summary['accepted_existing_command_contracts']}")
        print(f"Existing command contracts needing shape review: {summary['existing_command_contracts_needing_shape_review']}")
        print(f"Remaining distinct unrecognized fields: {summary['remaining_distinct_unrecognized_fields']}")
        print(f"Wrote: {OUT_MD}")
        print(f"Wrote: {OUT_CSV}")
        print(f"Wrote: {OUT_JSON}")
        print(f"Wrote: {OUT_COMPARE_MD}")
        print("No source files were edited.")
        print("No DBFs were written.")
        print("CMDHELPCHK was not modified.")
        print("HELP DATA was not rebuilt.")
        print("No headers were repaired.")
        print("v0 probe and v0 reports were not overwritten.")
    return 0


# ---- SelfDoc hotfix 004 writer-binding normalization ----
# SelfDoc tooling may evolve. DotTalk++ runtime/source/data mutation remains gated.
# This block normalizes report rows at writer boundary. It does not edit source,
# write DBFs, rebuild HELP DATA, modify CMDHELPCHK, or promote v1.1 to default.

from pathlib import Path as _SelfDocHotfix004Path
import re as _selfdoc_hotfix004_re
import functools as _selfdoc_hotfix004_functools

SELFDOC_HOTFIX_004_WRITER_BINDING_VERSION = "v1.1-hotfix_004_writer_binding"

SELFDOC_HOTFIX_004_BATCH0_CAPTURE_ONLY_PATHS = {
    "src/cli/cmd_area.cpp",
    "src/cli/cmd_calcwrite.cpp",
    "src/cli/cmd_close.cpp",
    "src/cli/cmd_color.cpp",
    "src/cli/cmd_commit.cpp",
    "src/cli/cmd_copy.cpp",
    "src/cli/cmd_dir.cpp",
    "src/cli/cmd_foxhelp.cpp",
    "src/cli/cmd_list_lmdb.cpp",
}

SELFDOC_HOTFIX_004_CMD_HELP_PATH = "src/cli/cmd_help.cpp"


def _selfdoc_hotfix004_norm_path(path: object) -> str:
    return str(path or "").replace("\\", "/")


def _selfdoc_hotfix004_get(row: object, name: str, default: object = "") -> object:
    if isinstance(row, dict):
        return row.get(name, default)
    return getattr(row, name, default)


def _selfdoc_hotfix004_set(row: object, name: str, value: object) -> None:
    if isinstance(row, dict):
        row[name] = value
        return
    try:
        setattr(row, name, value)
    except Exception:
        pass


def _selfdoc_hotfix004_get_path(row: object) -> str:
    for name in ("path", "source_path", "file_path", "file", "relpath", "relative_path"):
        value = _selfdoc_hotfix004_get(row, name, "")
        if value:
            return _selfdoc_hotfix004_norm_path(value)
    return ""


def _selfdoc_hotfix004_note(row: object, text: str) -> None:
    current = _selfdoc_hotfix004_get(row, "notes", "")
    if isinstance(current, list):
        if text not in current:
            current.append(text)
        _selfdoc_hotfix004_set(row, "notes", current)
        return

    cur = str(current or "")
    if text not in cur:
        _selfdoc_hotfix004_set(row, "notes", (cur + "; " + text).strip("; ") if cur else text)


def _selfdoc_hotfix004_read_text(path: _SelfDocHotfix004Path) -> str:
    raw = path.read_bytes()
    for enc in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            return raw.decode(enc, errors="strict")
        except UnicodeDecodeError:
            pass
    return raw.decode("utf-8", errors="surrogateescape")


def _selfdoc_hotfix004_line_bounds(text: str, offset: int) -> tuple[int, int, str]:
    start = text.rfind("\n", 0, offset) + 1
    end = text.find("\n", offset)
    if end == -1:
        end = len(text)
    return start, end, text[start:end]


def _selfdoc_hotfix004_marker_anchored_capture(text: str) -> str:
    match = _selfdoc_hotfix004_re.search(_selfdoc_hotfix004_re.escape(MARKER), text)
    if not match:
        return ""

    line_start, line_end, _line = _selfdoc_hotfix004_line_bounds(text, match.start())
    end = line_end

    while end < len(text):
        next_start = end + 1
        if next_start >= len(text):
            break

        next_end = text.find("\n", next_start)
        if next_end == -1:
            next_end = len(text)

        next_line = text[next_start:next_end]

        if next_line.lstrip().startswith("//"):
            end = next_end
            if next_end == len(text):
                break
            continue

        if next_line.strip() == "":
            after_blank_start = next_end + 1
            if after_blank_start >= len(text):
                break
            after_blank_end = text.find("\n", after_blank_start)
            if after_blank_end == -1:
                after_blank_end = len(text)
            after_blank_line = text[after_blank_start:after_blank_end]
            if after_blank_line.lstrip().startswith("//"):
                end = next_end
                continue

        break

    return text[line_start:end]


def _selfdoc_hotfix004_strip_comment_prefix(line: str) -> str:
    s = line.strip()
    if s.startswith("/*"):
        s = s[2:].lstrip()
    if s.endswith("*/"):
        s = s[:-2].rstrip()
    if s.startswith("//"):
        s = s[2:].lstrip()
    if s.startswith("*"):
        s = s[1:].lstrip()
    return s.rstrip()


def _selfdoc_hotfix004_parse_anchored_fields(block: str) -> tuple[dict[str, list[str]], list[str], bool]:
    fields: dict[str, list[str]] = {}
    malformed: list[str] = []
    seen_marker = False
    saw_payload = False
    marker_first_payload = False

    for raw in str(block or "").splitlines():
        line = _selfdoc_hotfix004_strip_comment_prefix(raw)
        if not line:
            continue

        if MARKER in line:
            seen_marker = True
            if not saw_payload:
                marker_first_payload = True
            saw_payload = True
            continue

        saw_payload = True

        if not seen_marker:
            continue

        if set(line) <= {"-", "=", "_"}:
            continue

        match = _selfdoc_hotfix004_re.match(r"^([A-Za-z][A-Za-z0-9_ -]{0,60})\s*:\s*(.*)$", line)
        if not match:
            if fields:
                last_key = next(reversed(fields))
                fields[last_key].append(line)
            else:
                malformed.append(line)
            continue

        key = match.group(1).strip().lower().replace(" ", "_")
        value = match.group(2).strip()
        fields.setdefault(key, []).append(value)

    return fields, malformed, marker_first_payload


def _selfdoc_hotfix004_has_required_command_shape(fields: dict[str, list[str]]) -> bool:
    has_command = bool(fields.get("command") or fields.get("commands"))
    has_summary = bool(fields.get("summary"))
    has_usage_or_syntax = bool(fields.get("usage") or fields.get("syntax"))
    return has_command and has_summary and has_usage_or_syntax


def _selfdoc_hotfix004_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes", "y"}


def _selfdoc_hotfix004_should_clear_row(row: object) -> tuple[bool, str]:
    path = _selfdoc_hotfix004_get_path(row)

    if path not in SELFDOC_HOTFIX_004_BATCH0_CAPTURE_ONLY_PATHS:
        return False, "not_batch0_capture_only_path"

    source_path = _SelfDocHotfix004Path(path)
    if not source_path.is_file():
        return False, "source_missing"

    try:
        text = _selfdoc_hotfix004_read_text(source_path)
    except Exception as exc:
        return False, f"source_read_error:{type(exc).__name__}"

    capture = _selfdoc_hotfix004_marker_anchored_capture(text)
    fields, malformed, marker_first = _selfdoc_hotfix004_parse_anchored_fields(capture)
    required_shape = _selfdoc_hotfix004_has_required_command_shape(fields)

    if not marker_first:
        return False, "marker_not_first_payload"
    if malformed:
        return False, "anchored_parse_has_malformed_payload"
    if not required_shape:
        return False, "required_command_shape_missing"

    return True, "clean_marker_anchored_payload_with_required_shape"


def _selfdoc_hotfix004_normalize_row(row: object) -> object:
    path = _selfdoc_hotfix004_get_path(row)

    if path == SELFDOC_HOTFIX_004_CMD_HELP_PATH:
        _selfdoc_hotfix004_set(row, "evidence_lane", "STALE_EVIDENCE")
        _selfdoc_hotfix004_set(row, "secondary_lane", "DO_NOT_REPAIR")
        _selfdoc_hotfix004_set(row, "source_repair_recommended", False)
        _selfdoc_hotfix004_set(row, "repair_authorized", False)
        _selfdoc_hotfix004_note(row, "hotfix_004_writer_binding: cmd_help.cpp held as STALE_EVIDENCE / DO_NOT_REPAIR")
        return row

    should_clear, reason = _selfdoc_hotfix004_should_clear_row(row)

    if should_clear:
        _selfdoc_hotfix004_set(row, "malformed", False)
        _selfdoc_hotfix004_set(row, "malformed_count", 0)
        _selfdoc_hotfix004_set(row, "malformed_lines", "")
        _selfdoc_hotfix004_set(row, "action_class", "accepted_existing_command_contract")
        _selfdoc_hotfix004_set(row, "status", "accepted")
        _selfdoc_hotfix004_set(row, "evidence_lane", "CONFIRMED")
        _selfdoc_hotfix004_set(row, "secondary_lane", "DO_NOT_REPAIR")
        _selfdoc_hotfix004_set(row, "source_repair_recommended", False)
        _selfdoc_hotfix004_set(row, "repair_authorized", False)
        _selfdoc_hotfix004_note(row, "hotfix_004_writer_binding: cleared capture-only malformed assignment after clean marker-anchored parse")
    elif path in SELFDOC_HOTFIX_004_BATCH0_CAPTURE_ONLY_PATHS:
        _selfdoc_hotfix004_set(row, "evidence_lane", "CLASSIFIER_REVIEW")
        _selfdoc_hotfix004_set(row, "secondary_lane", "DO_NOT_REPAIR")
        _selfdoc_hotfix004_set(row, "source_repair_recommended", False)
        _selfdoc_hotfix004_set(row, "repair_authorized", False)
        _selfdoc_hotfix004_note(row, f"hotfix_004_writer_binding: capture-only row not cleared: {reason}")

    return row


def _selfdoc_hotfix004_is_row_sequence(value: object) -> bool:
    if not isinstance(value, list):
        return False
    if not value:
        return False
    sample = value[0]
    return isinstance(sample, dict) or bool(_selfdoc_hotfix004_get_path(sample))


def _selfdoc_hotfix004_finalize_rows(rows: object) -> object:
    if not isinstance(rows, list):
        return rows
    return [_selfdoc_hotfix004_normalize_row(row) for row in rows]


def _selfdoc_hotfix004_row_action(row: object) -> str:
    return str(_selfdoc_hotfix004_get(row, "action_class", "") or "")


def _selfdoc_hotfix004_update_summary(summary: object, rows: object) -> None:
    if not isinstance(summary, dict) or not isinstance(rows, list):
        return

    actions = [_selfdoc_hotfix004_row_action(row) for row in rows]
    malformed_count = sum(1 for row in rows if _selfdoc_hotfix004_bool(_selfdoc_hotfix004_get(row, "malformed", False)))

    if "probe_version" in summary or "total_records" in summary or "files_with_contracts" in summary:
        summary["probe_version"] = SELFDOC_HOTFIX_004_WRITER_BINDING_VERSION

    if "accepted_existing_command_contracts" in summary:
        summary["accepted_existing_command_contracts"] = actions.count("accepted_existing_command_contract")
    if "existing_command_contracts_needing_shape_review" in summary:
        summary["existing_command_contracts_needing_shape_review"] = actions.count("review_existing_command_contract_shape")
    if "malformed_contracts" in summary:
        summary["malformed_contracts"] = malformed_count
    if "source_repair_recommended" in summary:
        summary["source_repair_recommended"] = 0


def _selfdoc_hotfix004_normalize_args_kwargs(args: tuple, kwargs: dict) -> tuple[tuple, dict]:
    args_list = list(args)
    normalized_rows = None

    for index, value in enumerate(args_list):
        if _selfdoc_hotfix004_is_row_sequence(value):
            args_list[index] = _selfdoc_hotfix004_finalize_rows(value)
            normalized_rows = args_list[index]

    for key in ("rows", "records", "inventory_rows", "items"):
        value = kwargs.get(key)
        if _selfdoc_hotfix004_is_row_sequence(value):
            kwargs[key] = _selfdoc_hotfix004_finalize_rows(value)
            normalized_rows = kwargs[key]

    for value in args_list:
        if isinstance(value, dict):
            _selfdoc_hotfix004_update_summary(value, normalized_rows)
    for value in kwargs.values():
        if isinstance(value, dict):
            _selfdoc_hotfix004_update_summary(value, normalized_rows)

    return tuple(args_list), kwargs


def _selfdoc_hotfix004_wrap_writer(name: str) -> bool:
    fn = globals().get(name)
    if not callable(fn):
        return False
    if getattr(fn, "_selfdoc_hotfix004_wrapped", False):
        return True

    @_selfdoc_hotfix004_functools.wraps(fn)
    def wrapper(*args, **kwargs):
        new_args, new_kwargs = _selfdoc_hotfix004_normalize_args_kwargs(args, kwargs)
        return fn(*new_args, **new_kwargs)

    wrapper._selfdoc_hotfix004_wrapped = True
    globals()[name] = wrapper
    return True


def _selfdoc_hotfix004_bind_writer_hooks() -> dict[str, bool]:
    result = {}
    for name in (
        "write_csv_report",
        "write_json_report",
        "write_md_report",
        "write_markdown_report",
        "write_comparison_report",
        "write_reports",
        "write_outputs",
    ):
        result[name] = _selfdoc_hotfix004_wrap_writer(name)
    return result


SELFDOC_HOTFIX_004_WRITER_BINDINGS = _selfdoc_hotfix004_bind_writer_hooks()
# ---- end SelfDoc hotfix 004 writer-binding normalization ----


if __name__ == "__main__":
    raise SystemExit(main())
