#!/usr/bin/env python3
"""
cmdhelpchk_phase2_crosswalk_probe_v0.py

REPORT_ONLY / CROSSWALK_ONLY probe for CMDHELPCHK Phase 2.

Run from:
    D:\code\ccode

Reads, when present:
    Source tree:
      src\cli\*.cpp
      include\**\*.hpp
    SelfDoc / source-contract inventory:
      dottalkpp\docs\generated\reports\source_contracts_inventory_v1_1.csv
      dottalkpp\docs\generated\reports\source_contracts_inventory_v1_1.json
      dottalkpp\docs\generated\reports\source_contract_hotfix_004_tuned_evidence_lanes.csv
      dottalkpp\docs\generated\reports\source_contract_inventory_v1_1_hotfix_004_promotion_review.json
    Architecture / authority:
      dottalkpp\docs\authority\artifact_intake_ledger.jsonl
      dottalkpp\docs\generated\reports\artifact_intake_current.md
      dottalkpp\docs\generated\reports\source_contract_hotfix004_arch_intake_record.json
      dottalkpp\docs\generated\DOCS_INDEX.md
    HELP/DOTHELP/CMDHELP text artifacts, if present:
      dottalkpp\docs\generated\**\*help*.md
      dottalkpp\docs\generated\**\*cmdhelp*.md
      dottalkpp\docs\generated\**\*dothelp*.md
      dottalkpp\docs\help\**\*.md
      dottalkpp\help\**\*.md

Writes:
    dottalkpp\docs\generated\reports\cmdhelpchk_phase2_crosswalk_v0.md
    dottalkpp\docs\generated\reports\cmdhelpchk_phase2_crosswalk_v0.csv
    dottalkpp\docs\generated\reports\cmdhelpchk_phase2_crosswalk_v0.json

Purpose:
    Inventory command surfaces, source contracts, DOTHELP/CMDHELP output artifacts,
    and authority records into one report-only crosswalk before any HELP DATA
    rebuild, CMDHELPCHK mutation, source repair, or v1.1 default promotion.

Safety:
    No DotTalk++ src/include edits.
    No source header repairs.
    No DBF writes.
    No HELP DATA rebuild.
    No CMDHELPCHK changes.
    No v1.1 source-contract default promotion.
    No project file moves/deletes.
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
from typing import Any, Iterable


MARKER = "@dottalk.usage v1"
EXPECTED_SOURCE_CONTRACT_VERSION = "v1.1-hotfix_004_writer_binding"

REPORT_DIR = Path("dottalkpp") / "docs" / "generated" / "reports"
OUT_MD = REPORT_DIR / "cmdhelpchk_phase2_crosswalk_v0.md"
OUT_CSV = REPORT_DIR / "cmdhelpchk_phase2_crosswalk_v0.csv"
OUT_JSON = REPORT_DIR / "cmdhelpchk_phase2_crosswalk_v0.json"

INV_CSV = REPORT_DIR / "source_contracts_inventory_v1_1.csv"
INV_JSON = REPORT_DIR / "source_contracts_inventory_v1_1.json"
TUNED_LANES_CSV = REPORT_DIR / "source_contract_hotfix_004_tuned_evidence_lanes.csv"
PROMOTION_JSON = REPORT_DIR / "source_contract_inventory_v1_1_hotfix_004_promotion_review.json"
ARCH_INTAKE_JSON = REPORT_DIR / "source_contract_hotfix004_arch_intake_record.json"
ARTIFACT_LEDGER = Path("dottalkpp") / "docs" / "authority" / "artifact_intake_ledger.jsonl"
ARTIFACT_INTAKE_MD = REPORT_DIR / "artifact_intake_current.md"
DOCS_INDEX = Path("dottalkpp") / "docs" / "generated" / "DOCS_INDEX.md"

COMMAND_SRC_GLOBS = [
    "src/cli/cmd_*.cpp",
    "src/cli/*cmd*.cpp",
    "src/cli/shell*.cpp",
    "src/cli/help*.cpp",
    "src/cli/browse/*.cpp",
]

HELP_ARTIFACT_GLOBS = [
    "dottalkpp/docs/generated/**/*help*.md",
    "dottalkpp/docs/generated/**/*cmdhelp*.md",
    "dottalkpp/docs/generated/**/*dothelp*.md",
    "dottalkpp/docs/help/**/*.md",
    "dottalkpp/help/**/*.md",
    "dottalkpp/docs/generated/**/*.txt",
]


@dataclass
class CrosswalkRow:
    path: str
    token: str
    surface_kind: str
    source_file_present: bool
    source_contract_present: bool
    source_contract_status: str
    action_class: str
    malformed: bool
    evidence_lane: str
    secondary_lane: str
    source_repair_recommended: bool
    authority_state: str
    help_artifact_count: int
    help_artifact_paths: str
    cmdhelp_artifact_count: int
    dothelp_artifact_count: int
    crosswalk_lane: str
    warning_class: str
    recommended_next_action: str
    notes: str = ""


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def b(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes", "y"}


def norm_path(value: object) -> str:
    return str(value or "").replace("\\", "/")


def md_escape(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def read_text(path: Path) -> str:
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"_read_error": f"{type(exc).__name__}: {exc}"}


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        return []
    with path.open("r", encoding="utf-8", newline="") as f:
        return [dict(row) for row in csv.DictReader(f)]


def index_by_path(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    indexed: dict[str, dict[str, str]] = {}
    for row in rows:
        path = norm_path(row.get("path", ""))
        if path:
            indexed[path] = row
    return indexed


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


def marker_anchored_contract(text: str) -> str:
    match = re.search(re.escape(MARKER), text)
    if not match:
        return ""

    start = text.rfind("\n", 0, match.start()) + 1
    line_end = text.find("\n", match.start())
    if line_end == -1:
        line_end = len(text)

    end = line_end
    while end < len(text):
        next_start = end + 1
        if next_start >= len(text):
            break
        next_end = text.find("\n", next_start)
        if next_end == -1:
            next_end = len(text)
        line = text[next_start:next_end]
        if line.lstrip().startswith("//"):
            end = next_end
            continue
        if line.strip() == "":
            after = next_end + 1
            if after < len(text):
                after_end = text.find("\n", after)
                if after_end == -1:
                    after_end = len(text)
                if text[after:after_end].lstrip().startswith("//"):
                    end = next_end
                    continue
        break
    return text[start:end]


def parse_contract_fields(contract: str) -> dict[str, list[str]]:
    fields: dict[str, list[str]] = {}
    seen_marker = False
    for raw in contract.splitlines():
        line = strip_comment_prefix(raw)
        if not line:
            continue
        if MARKER in line:
            seen_marker = True
            continue
        if not seen_marker:
            continue
        if set(line) <= {"-", "=", "_"}:
            continue
        match = re.match(r"^([A-Za-z][A-Za-z0-9_ -]{0,60})\s*:\s*(.*)$", line)
        if match:
            key = match.group(1).strip().lower().replace(" ", "_")
            value = match.group(2).strip()
            fields.setdefault(key, []).append(value)
        elif fields:
            last = next(reversed(fields))
            fields[last].append(line)
    return fields


def first_value(fields: dict[str, list[str]], *keys: str) -> str:
    for key in keys:
        values = fields.get(key, [])
        for value in values:
            if value:
                return value.strip()
    return ""


def split_tokens(value: str) -> list[str]:
    if not value:
        return []
    # Preserve things like "CMDHELP BUILD" as first token for command token matching.
    cleaned = value.replace("`", "").replace("<", " ").replace(">", " ")
    parts = re.split(r"[,;/|]+", cleaned)
    out: list[str] = []
    for part in parts:
        word = part.strip()
        if not word:
            continue
        first = word.split()[0].strip()
        first = re.sub(r"[^A-Za-z0-9_.$-]", "", first)
        if first:
            out.append(first.upper())
    return sorted(set(out))


def infer_token_from_path(path: str) -> str:
    name = Path(path).name
    stem = Path(name).stem
    if stem.startswith("cmd_"):
        token = stem[4:].upper()
    elif stem.startswith("cmd"):
        token = stem[3:].strip("_").upper()
    elif stem == "cmdhelp":
        token = "CMDHELP"
    elif stem == "shell_commands":
        token = "SHELL_COMMANDS"
    elif stem == "shell":
        token = "SHELL"
    elif "dothelp" in stem.lower():
        token = "DOTHELP"
    elif "help" in stem.lower():
        token = "HELP"
    else:
        token = stem.upper()
    return token.replace("_", "-")


def infer_surface_kind(path: str, row: dict[str, str], fields: dict[str, list[str]]) -> str:
    action = row.get("action_class", "")
    family = row.get("approved_family", "") or row.get("recommended_family", "")
    p = path.lower()

    if "registry" in action or "shell_commands.cpp" in p:
        return "command_registry"
    if "dispatch" in action:
        return "command_dispatcher"
    if "helper" in action or p.endswith("_utils.cpp") or "browse_util.cpp" in p or "status_helpers.cpp" in p:
        return "command_helper"
    if "command_family" in action or "help_subsystem" in family or "cmdhelp.cpp" in p or "cmd_dothelp.cpp" in p:
        return "command_family_or_subsystem"
    if p.endswith("shell.cpp"):
        return "cli_shell_core"
    if p.startswith("src/cli/cmd_"):
        return "simple_command_surface"
    if MARKER.lower() in " ".join(sum(fields.values(), [])).lower():
        return "contract_surface"
    return "command_adjacent"


def collect_source_files(root: Path) -> list[str]:
    found: set[str] = set()
    for pattern in COMMAND_SRC_GLOBS:
        for path in root.glob(pattern):
            if path.is_file():
                found.add(norm_path(path.relative_to(root)))
    return sorted(found)


def collect_help_artifacts(root: Path) -> list[str]:
    found: set[str] = set()
    for pattern in HELP_ARTIFACT_GLOBS:
        for path in root.glob(pattern):
            if path.is_file():
                # Exclude the crosswalk itself if rerun.
                rel = norm_path(path.relative_to(root))
                if "cmdhelpchk_phase2_crosswalk_v0" not in rel:
                    found.add(rel)
    return sorted(found)


def build_help_index(paths: list[str]) -> dict[str, list[str]]:
    index: dict[str, list[str]] = defaultdict(list)
    for path in paths:
        text = Path(path).name.upper() + " " + path.upper()
        words = set(re.findall(r"[A-Z][A-Z0-9_$-]{1,40}", text))
        for word in words:
            index[word].append(path)
    return index


def classify_row(
    path: str,
    token: str,
    surface_kind: str,
    inv: dict[str, str],
    source_present: bool,
    help_paths: list[str],
    authority_state: str,
) -> tuple[str, str, str]:
    action = inv.get("action_class", "")
    status = inv.get("status", "")
    malformed = b(inv.get("malformed", False))
    repair = b(inv.get("source_repair_recommended", False))
    evidence = inv.get("evidence_lane", "")
    secondary = inv.get("secondary_lane", "")

    if repair:
        return "SOURCE_REVIEW", "SOURCE_REPAIR_RECOMMENDED_UNAUTHORIZED", "Stop; review why source repair was recommended."

    if surface_kind in {"command_registry", "command_dispatcher", "command_helper", "cli_shell_core"}:
        return "INTENTIONAL_EXCEPTION", "INFRASTRUCTURE_NOT_SIMPLE_COMMAND", "Keep in alternate contract/helper lane; do not require simple command HELP row."

    if evidence == "STALE_EVIDENCE" or secondary == "STALE_EVIDENCE":
        return "STALE_EVIDENCE", "STALE_EVIDENCE", "Refresh source/report evidence before promotion or repair."

    if malformed:
        return "SOURCE_CONTRACT_REVIEW", "MALFORMED_OR_SHAPE_REVIEW", "Review contract shape before HELP crosswalk authority."

    if action in {"accepted_existing_command_contract", "accepted_existing_command_family_contract"} or status in {"accepted", "ok"}:
        if help_paths:
            return "CONFIRMED", "NONE", "Source contract has matching HELP/DOTHELP/CMDHELP artifact evidence."
        return "HELP_ARTIFACT_REVIEW", "NO_HELP_ARTIFACT_MATCH_FOUND", "Check whether generated HELP artifacts are missing or named differently."

    if action == "action_required_add_command_family_usage_contract":
        return "POLICY_REVIEW", "FAMILY_USAGE_CONTRACT_BACKLOG", "Plan family-level usage contract; do not patch automatically."

    if not inv and source_present:
        return "SOURCE_CONTRACT_REVIEW", "NO_INVENTORY_ROW_FOR_SOURCE", "Inspect source-contract inventory coverage."

    return "POLICY_REVIEW", "UNCLASSIFIED_CROSSWALK_STATE", "Classify this row in warning classifier phase."


def write_csv(path: Path, rows: list[CrosswalkRow]) -> None:
    fieldnames = list(asdict(rows[0]).keys()) if rows else []
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(asdict(row))


def write_md(path: Path, summary: dict[str, Any], rows: list[CrosswalkRow]) -> None:
    lines = [
        "# CMDHELPCHK Phase 2 Crosswalk Probe v0",
        "",
        f"Generated UTC: `{summary['generated_at_utc']}`",
        "",
        "Safety class: `REPORT_ONLY / CROSSWALK_ONLY`",
        "",
        "## Verdict",
        "",
        "```text",
        f"crosswalk status: {summary['crosswalk_status']}",
        f"source_contract_inventory_version: {summary['source_contract_inventory_version']}",
        f"rows: {summary['rows']}",
        f"source_repair_recommended: {summary['source_repair_recommended']}",
        "CMDHELPCHK changes: NOT AUTHORIZED",
        "HELP DATA rebuild: NOT AUTHORIZED",
        "DBF writes: NOT AUTHORIZED",
        "source repairs: NOT AUTHORIZED",
        "v1.1 default promotion: NOT AUTHORIZED",
        "```",
        "",
        "## Lane counts",
        "",
        "| Lane | Count |",
        "|---|---:|",
    ]
    for lane, count in summary["crosswalk_lane_counts"].items():
        lines.append(f"| `{md_escape(lane)}` | {count} |")

    lines += [
        "",
        "## Warning-class counts",
        "",
        "| Warning class | Count |",
        "|---|---:|",
    ]
    for warning, count in summary["warning_class_counts"].items():
        lines.append(f"| `{md_escape(warning)}` | {count} |")

    lines += [
        "",
        "## Crosswalk rows",
        "",
        "| Token | Surface kind | Path | Contract | HELP artifacts | Lane | Warning | Next action |",
        "|---|---|---|---|---:|---|---|---|",
    ]

    for row in rows[:200]:
        contract = row.action_class or row.source_contract_status
        lines.append(
            f"| `{md_escape(row.token)}` | `{md_escape(row.surface_kind)}` | `{md_escape(row.path)}` | "
            f"`{md_escape(contract)}` | {row.help_artifact_count} | `{md_escape(row.crosswalk_lane)}` | "
            f"`{md_escape(row.warning_class)}` | {md_escape(row.recommended_next_action)} |"
        )

    if len(rows) > 200:
        lines.append(f"| ... | ... | ... | ... | ... | ... | ... | `{len(rows) - 200} additional rows omitted from markdown; see CSV/JSON.` |")

    lines += [
        "",
        "## Interpretation",
        "",
        summary["interpretation"],
        "",
        "## Recommended next action",
        "",
        summary["recommended_next_action"],
        "",
        "## Inputs checked",
        "",
    ]
    for item in summary["inputs_checked"]:
        lines.append(f"- `{md_escape(item['path'])}`: `{item['state']}`")

    lines += [
        "",
        "## Non-mutation confirmation",
        "",
    ]
    for guard in summary["non_mutation_guards"]:
        lines.append(f"- `{guard}`")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


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
    inv_version = str(inv_summary.get("probe_version", ""))

    tuned_rows = read_csv_rows(root / TUNED_LANES_CSV)
    tuned_by_path = index_by_path(tuned_rows)

    promotion_json = read_json(root / PROMOTION_JSON)
    promotion_summary = promotion_json.get("summary", {}) if isinstance(promotion_json.get("summary", {}), dict) else {}

    arch_json = read_json(root / ARCH_INTAKE_JSON)
    arch_summary = arch_json.get("summary", {}) if isinstance(arch_json.get("summary", {}), dict) else {}

    ledger_text = read_text(root / ARTIFACT_LEDGER)
    docs_index_text = read_text(root / DOCS_INDEX)
    artifact_intake_text = read_text(root / ARTIFACT_INTAKE_MD)

    source_paths = collect_source_files(root)
    # Include inventory rows even if source glob missed them.
    source_paths = sorted(set(source_paths) | set(inv_by_path.keys()))

    help_artifacts = collect_help_artifacts(root)
    help_index = build_help_index(help_artifacts)

    rows: list[CrosswalkRow] = []
    for path in source_paths:
        inv = dict(inv_by_path.get(path, {}))
        tuned = tuned_by_path.get(path, {})
        if tuned:
            # Carry tuned lane interpretation for hotfix004 target rows.
            if tuned.get("tuned_evidence_lane"):
                inv["evidence_lane"] = tuned.get("tuned_evidence_lane", "")
            if tuned.get("tuned_secondary_lane"):
                inv["secondary_lane"] = tuned.get("tuned_secondary_lane", "")

        source_file = root / path
        text = read_text(source_file) if source_file.is_file() else ""
        fields = parse_contract_fields(marker_anchored_contract(text)) if text else {}

        token_values = split_tokens(first_value(fields, "command", "commands", "usage", "syntax"))
        if not token_values:
            token_values = [infer_token_from_path(path)]
        token = token_values[0]

        surface_kind = infer_surface_kind(path, inv, fields)

        matching_help: set[str] = set()
        for candidate in token_values + [token]:
            for artifact in help_index.get(candidate.upper(), []):
                matching_help.add(artifact)

        # For command-family/help subsystem files, include generic cmdhelp/dothelp/help artifacts.
        if surface_kind == "command_family_or_subsystem":
            for key in ("CMDHELP", "DOTHELP", "HELP"):
                for artifact in help_index.get(key, []):
                    matching_help.add(artifact)

        help_paths = sorted(matching_help)
        cmdhelp_count = sum(1 for p in help_paths if "cmdhelp" in p.lower())
        dothelp_count = sum(1 for p in help_paths if "dothelp" in p.lower())

        authority_state = ""
        if "INTAKE-2026-05-16-ARCH-SOURCE-CONTRACT-HOTFIX004" in ledger_text:
            authority_state = "hotfix004_arch_recorded"
        if path == "src/cli/cmd_help.cpp":
            authority_state = "stale_evidence_do_not_repair"
        elif path in {
            "src/cli/cmd_area.cpp",
            "src/cli/cmd_calcwrite.cpp",
            "src/cli/cmd_close.cpp",
            "src/cli/cmd_color.cpp",
            "src/cli/cmd_commit.cpp",
            "src/cli/cmd_copy.cpp",
            "src/cli/cmd_dir.cpp",
            "src/cli/cmd_foxhelp.cpp",
            "src/cli/cmd_list_lmdb.cpp",
        }:
            authority_state = "batch0_confirmed_do_not_repair"

        lane, warning, next_action = classify_row(
            path=path,
            token=token,
            surface_kind=surface_kind,
            inv=inv,
            source_present=source_file.is_file(),
            help_paths=help_paths,
            authority_state=authority_state,
        )

        rows.append(
            CrosswalkRow(
                path=path,
                token=token,
                surface_kind=surface_kind,
                source_file_present=source_file.is_file(),
                source_contract_present=bool(inv) and (bool(inv.get("header_hash", "")) or bool(inv.get("has_contract", "")) or bool(inv.get("contract_present", ""))),
                source_contract_status=inv.get("status", ""),
                action_class=inv.get("action_class", ""),
                malformed=b(inv.get("malformed", False)),
                evidence_lane=inv.get("evidence_lane", ""),
                secondary_lane=inv.get("secondary_lane", ""),
                source_repair_recommended=b(inv.get("source_repair_recommended", False)),
                authority_state=authority_state,
                help_artifact_count=len(help_paths),
                help_artifact_paths="; ".join(help_paths[:12]),
                cmdhelp_artifact_count=cmdhelp_count,
                dothelp_artifact_count=dothelp_count,
                crosswalk_lane=lane,
                warning_class=warning,
                recommended_next_action=next_action,
                notes="tokens=" + ",".join(token_values),
            )
        )

    rows.sort(key=lambda r: (r.crosswalk_lane, r.surface_kind, r.token, r.path))

    lane_counts = Counter(row.crosswalk_lane for row in rows)
    warning_counts = Counter(row.warning_class for row in rows)
    source_repair_count = sum(1 for row in rows if row.source_repair_recommended)

    if source_repair_count:
        crosswalk_status = "STOP_SOURCE_REPAIR_RECOMMENDED"
        recommended_next = "Review source-repair recommendations before any further CMDHELPCHK Phase 2 work."
    elif inv_version != EXPECTED_SOURCE_CONTRACT_VERSION:
        crosswalk_status = "REVIEW_SOURCE_CONTRACT_VERSION"
        recommended_next = "Refresh v1.1 source-contract inventory before treating crosswalk as promotion evidence."
    else:
        crosswalk_status = "REPORT_ONLY_CROSSWALK_GENERATED"
        recommended_next = "Build `cmdhelpchk_phase2_warning_classifier_v0` to classify remaining crosswalk warnings."

    inputs = [
        {"path": str(root / INV_CSV), "state": "present" if (root / INV_CSV).is_file() else "missing"},
        {"path": str(root / INV_JSON), "state": "present" if (root / INV_JSON).is_file() else "missing"},
        {"path": str(root / TUNED_LANES_CSV), "state": "present" if (root / TUNED_LANES_CSV).is_file() else "missing"},
        {"path": str(root / PROMOTION_JSON), "state": "present" if (root / PROMOTION_JSON).is_file() else "missing"},
        {"path": str(root / ARCH_INTAKE_JSON), "state": "present" if (root / ARCH_INTAKE_JSON).is_file() else "missing"},
        {"path": str(root / ARTIFACT_LEDGER), "state": "present" if (root / ARTIFACT_LEDGER).is_file() else "missing"},
        {"path": str(root / DOCS_INDEX), "state": "present" if (root / DOCS_INDEX).is_file() else "missing"},
        {"path": str(root / ARTIFACT_INTAKE_MD), "state": "present" if (root / ARTIFACT_INTAKE_MD).is_file() else "missing"},
    ]

    summary = {
        "generated_at_utc": now(),
        "status": "REPORT_ONLY_CROSSWALK_GENERATED",
        "crosswalk_status": crosswalk_status,
        "source_contract_inventory_version": inv_version,
        "expected_source_contract_inventory_version": EXPECTED_SOURCE_CONTRACT_VERSION,
        "rows": len(rows),
        "source_files_considered": len(source_paths),
        "help_artifacts_considered": len(help_artifacts),
        "source_repair_recommended": source_repair_count,
        "crosswalk_lane_counts": dict(lane_counts.most_common()),
        "warning_class_counts": dict(warning_counts.most_common()),
        "promotion_review_status": promotion_summary.get("promotion_review_status", ""),
        "arch_intake_status": arch_summary.get("arch_intake_status", ""),
        "hotfix004_ledgered": "INTAKE-2026-05-16-ARCH-SOURCE-CONTRACT-HOTFIX004" in ledger_text,
        "docs_index_present": bool(docs_index_text),
        "artifact_intake_present": bool(artifact_intake_text),
        "interpretation": "This crosswalk is visibility only. It inventories command-related source surfaces against source-contract state, HELP-like artifacts, and authority records. It does not prove runtime HELP behavior and does not authorize source repair, DBF writes, HELP DATA rebuild, CMDHELPCHK mutation, or v1.1 default promotion.",
        "recommended_next_action": recommended_next,
        "inputs_checked": inputs,
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

    write_csv(root / OUT_CSV, rows)
    (root / OUT_JSON).write_text(json.dumps({"summary": summary, "rows": [asdict(r) for r in rows]}, indent=2), encoding="utf-8")
    write_md(root / OUT_MD, summary, rows)

    print("CMDHELPCHK Phase 2 crosswalk probe v0 complete.")
    print(f"Crosswalk status: {crosswalk_status}")
    print(f"Source contract inventory version: {inv_version}")
    print(f"Rows: {len(rows)}")
    print(f"Source files considered: {len(source_paths)}")
    print(f"HELP artifacts considered: {len(help_artifacts)}")
    print(f"Source repair recommended: {source_repair_count}")
    print(f"Wrote: {OUT_MD}")
    print(f"Wrote: {OUT_CSV}")
    print(f"Wrote: {OUT_JSON}")
    print("No DotTalk++ src/include files were edited.")
    print("No DBFs were written.")
    print("HELP DATA was not rebuilt.")
    print("CMDHELPCHK was not modified.")
    print("v1.1 was not promoted to default.")

    return 0 if source_repair_count == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
