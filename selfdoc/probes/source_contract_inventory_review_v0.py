#!/usr/bin/env python3
"""
source_contract_inventory_review_v0.py

REPORT_ONLY review of SelfDoc source_contracts_inventory outputs.

Run from:
    D:\code\ccode

Reads:
    dottalkpp\docs\generated\reports\source_contracts_inventory.json
    dottalkpp\docs\generated\reports\source_contracts_inventory.csv
    dottalkpp\docs\generated\reports\source_contracts_inventory.md

Writes:
    dottalkpp\docs\generated\reports\source_contract_inventory_review_v0.md

No source edits. No DBF writes. No CMDHELPCHK changes. No HELP DATA rebuild.
No source contract repairs.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_REPORT_DIRS = (
    Path("dottalkpp") / "docs" / "generated" / "reports",
    Path("docs") / "generated" / "reports",
)

INPUT_JSON = "source_contracts_inventory.json"
INPUT_CSV = "source_contracts_inventory.csv"
INPUT_MD = "source_contracts_inventory.md"
OUTPUT_MD = "source_contract_inventory_review_v0.md"


@dataclass
class Record:
    path: str
    status: str
    has_contract: bool
    contract_count: int = 0
    fields_present: list[str] = field(default_factory=list)
    missing_recommended_fields: list[str] = field(default_factory=list)
    malformed_lines: list[str] = field(default_factory=list)
    unknown_fields: list[str] = field(default_factory=list)
    command_names: list[str] = field(default_factory=list)
    escrow_candidate: bool = False
    notes: list[str] = field(default_factory=list)


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
        return [part.strip() for part in text.split(";") if part.strip()]
    if "," in text:
        return [part.strip() for part in text.split(",") if part.strip()]
    return [text]


def find_report_dir(root: Path, explicit: str | None) -> Path:
    if explicit:
        d = root / explicit
        if not d.is_dir():
            raise SystemExit(f"Report directory not found: {d}")
        return d

    for rel in DEFAULT_REPORT_DIRS:
        d = root / rel
        if (d / INPUT_JSON).is_file() or (d / INPUT_CSV).is_file():
            return d

    checked = "\n".join(str(root / rel) for rel in DEFAULT_REPORT_DIRS)
    raise SystemExit(f"Could not find inventory reports. Checked:\n{checked}")


def load_records(report_dir: Path) -> tuple[dict[str, Any], list[Record], list[str]]:
    notes: list[str] = []
    json_path = report_dir / INPUT_JSON
    csv_path = report_dir / INPUT_CSV
    md_path = report_dir / INPUT_MD

    summary: dict[str, Any] = {}
    records: list[Record] = []

    if json_path.is_file():
        payload = json.loads(json_path.read_text(encoding="utf-8"))
        summary = dict(payload.get("summary", {}))
        for item in payload.get("records", []):
            records.append(Record(
                path=str(item.get("path", "")),
                status=str(item.get("status", "")),
                has_contract=parse_bool(item.get("has_contract", False)),
                contract_count=int(item.get("contract_count", 0) or 0),
                fields_present=parse_list(item.get("fields_present")),
                missing_recommended_fields=parse_list(item.get("missing_recommended_fields")),
                malformed_lines=parse_list(item.get("malformed_lines")),
                unknown_fields=parse_list(item.get("unknown_fields")),
                command_names=parse_list(item.get("command_names")),
                escrow_candidate=parse_bool(item.get("escrow_candidate", False)),
                notes=parse_list(item.get("notes")),
            ))
        notes.append(f"read JSON: {json_path}")
    elif csv_path.is_file():
        with csv_path.open("r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            for item in reader:
                records.append(Record(
                    path=str(item.get("path", "")),
                    status=str(item.get("status", "")),
                    has_contract=parse_bool(item.get("has_contract", False)),
                    contract_count=int(item.get("contract_count", 0) or 0),
                    fields_present=parse_list(item.get("fields_present")),
                    missing_recommended_fields=parse_list(item.get("missing_recommended_fields")),
                    malformed_lines=parse_list(item.get("malformed_lines")),
                    unknown_fields=parse_list(item.get("unknown_fields")),
                    command_names=parse_list(item.get("command_names")),
                    escrow_candidate=parse_bool(item.get("escrow_candidate", False)),
                    notes=parse_list(item.get("notes")),
                ))
        notes.append(f"read CSV: {csv_path}")
    else:
        raise SystemExit(f"Missing required inventory input: {json_path} or {csv_path}")

    if md_path.is_file():
        notes.append(f"markdown companion present: {md_path}")
    else:
        notes.append(f"markdown companion missing: {md_path}")

    return summary, records, notes


def norm(path: str) -> str:
    return path.replace("\\", "/").lower()


def lane_for_path(path: str) -> str:
    p = norm(path)
    name = p.rsplit("/", 1)[-1]

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


def recommended_contract_type(path: str) -> str:
    p = norm(path)
    name = p.rsplit("/", 1)[-1]

    if p.startswith("src/cli/cmd_") and name.endswith(".cpp"):
        return "@dottalk.usage v1"
    if p.startswith("src/cli/") and name in {
        "shell_commands.cpp",
        "cmdhelp.cpp",
        "cmd_help.cpp",
        "cmd_dothelp.cpp",
        "helpdata_cmdhelp_bridge.cpp",
    }:
        return "@dottalk.usage v1 or selfdoc.tool_contract"
    if p.startswith("src/cli/") and ("help" in name or "cmdhelp" in name):
        return "selfdoc.help_miner_contract"
    if p.startswith("src/xexpr/") and name.startswith("fn_"):
        return "selfdoc.function_contract"
    if p.startswith("include/") and not name.startswith("cmd_"):
        return "selfdoc.api_contract or exclude_from_usage_contract"
    if p.startswith("src/xbase/") or p.startswith("src/xindex/") or p.startswith("src/memo/"):
        return "selfdoc.engine_contract"
    if p.startswith("src/tv/"):
        return "selfdoc.ui_contract"
    if p.startswith("bindings/") or "pydottalk" in p:
        return "selfdoc.binding_contract"
    if p.startswith("dev/") or "test" in p:
        return "selfdoc.test_contract or exclude_from_usage_contract"
    return "classify_before_contract"


def needs_usage_contract(path: str) -> bool:
    p = norm(path)
    name = p.rsplit("/", 1)[-1]
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


def should_exclude_from_usage(path: str) -> bool:
    p = norm(path)
    if p.startswith("include/") and not p.startswith("include/cli/"):
        return True
    if p.startswith("src/xbase/") or p.startswith("src/xindex/") or p.startswith("src/memo/"):
        return True
    if p.startswith("src/xexpr/"):
        return True
    if p.startswith("src/tv/"):
        return True
    if p.startswith("bindings/"):
        return True
    if p.startswith("dev/") or p.startswith("tests/") or "/test" in p:
        return True
    return False


def escrow_reasons(rec: Record) -> list[str]:
    reasons: list[str] = []
    if not rec.has_contract:
        reasons.append("missing_contract")
    if rec.contract_count > 1:
        reasons.append("multiple_contracts")
    for field in rec.missing_recommended_fields:
        reasons.append(f"missing_recommended:{field}")
    if rec.malformed_lines:
        reasons.append("malformed_lines")
    for field in rec.unknown_fields:
        reasons.append(f"unknown_field:{field}")
    if rec.status and rec.status not in {"ok", "missing_contract"}:
        reasons.append(f"status:{rec.status}")
    if not reasons and rec.escrow_candidate:
        reasons.append("escrow_flag_without_specific_reason")
    return reasons


def md_escape(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def write_review(report_dir: Path, summary: dict[str, Any], records: list[Record], load_notes: list[str]) -> Path:
    output = report_dir / OUTPUT_MD

    status_counts = Counter(rec.status for rec in records)
    lane_counts = Counter(lane_for_path(rec.path) for rec in records)
    missing_by_lane = Counter(lane_for_path(rec.path) for rec in records if not rec.has_contract)
    reason_counts: Counter[str] = Counter()

    needs_usage_missing: list[Record] = []
    usage_present_but_escrow: list[Record] = []
    exclude_or_other_contract: list[Record] = []
    review_before_decision: list[Record] = []

    for rec in records:
        for reason in escrow_reasons(rec):
            reason_counts[reason] += 1

        if needs_usage_contract(rec.path):
            if not rec.has_contract:
                needs_usage_missing.append(rec)
            elif rec.escrow_candidate:
                usage_present_but_escrow.append(rec)
        elif should_exclude_from_usage(rec.path):
            if not rec.has_contract or rec.escrow_candidate:
                exclude_or_other_contract.append(rec)
        else:
            if not rec.has_contract or rec.escrow_candidate:
                review_before_decision.append(rec)

    lines: list[str] = []
    lines.append("# Source Contract Inventory Review v0")
    lines.append("")
    lines.append(f"Generated UTC: `{datetime.now(timezone.utc).isoformat()}`")
    lines.append("")
    lines.append("Safety class: `REPORT_ONLY`")
    lines.append("")
    lines.append("## Scope and guardrails")
    lines.append("")
    lines.append("This review summarizes the existing `source_contracts_inventory` reports. It does not edit source, write DBFs, repair headers, rebuild HELP DATA, or modify CMDHELPCHK.")
    lines.append("")
    lines.append("Inputs read:")
    lines.append("")
    for note in load_notes:
        lines.append(f"- `{note}`")
    lines.append("")
    lines.append("Output written:")
    lines.append("")
    lines.append(f"- `{output}`")
    lines.append("")
    lines.append("## Executive summary")
    lines.append("")
    lines.append(f"- Total source records reviewed: `{len(records)}`")
    lines.append(f"- Files with contracts: `{sum(1 for r in records if r.has_contract)}`")
    lines.append(f"- Files missing contracts: `{sum(1 for r in records if not r.has_contract)}`")
    lines.append(f"- Escrow candidates: `{sum(1 for r in records if r.escrow_candidate)}`")
    lines.append(f"- Files that appear to actually need `@dottalk.usage v1` and are missing it: `{len(needs_usage_missing)}`")
    lines.append(f"- Files with a usage contract but still escrow due to field/shape issues: `{len(usage_present_but_escrow)}`")
    lines.append(f"- Files better suited to exclusion or another contract type: `{len(exclude_or_other_contract)}`")
    lines.append(f"- Files needing manual classification before a contract decision: `{len(review_before_decision)}`")
    lines.append("")
    lines.append("Interpretation: the first inventory is intentionally strict. A broad escrow count is useful baseline evidence, not a failure by itself.")
    lines.append("")
    lines.append("## Status counts")
    lines.append("")
    lines.append("| Status | Count |")
    lines.append("|---|---:|")
    for status, count in status_counts.most_common():
        lines.append(f"| `{md_escape(status)}` | {count} |")
    lines.append("")
    lines.append("## Top escrow reasons")
    lines.append("")
    lines.append("| Reason | Count |")
    lines.append("|---|---:|")
    for reason, count in reason_counts.most_common(20):
        lines.append(f"| `{md_escape(reason)}` | {count} |")
    lines.append("")
    lines.append("## Missing-contract files by lane")
    lines.append("")
    lines.append("| Lane | Missing contract files | Total files in lane |")
    lines.append("|---|---:|---:|")
    for lane, count in missing_by_lane.most_common():
        lines.append(f"| `{md_escape(lane)}` | {count} | {lane_counts[lane]} |")
    lines.append("")
    lines.append("## Lane classification policy")
    lines.append("")
    lane_policy = {
        "cli_command_help_surface": ("@dottalk.usage v1", "Command handlers, command HELP surfaces, and registry/help bridge files are strongest usage-contract candidates."),
        "cli_support": ("manual classification", "Some CLI support files may need tool/helper contracts, but not all are user-facing command contracts."),
        "cli_headers": ("api/tool contract or usage contract if public command-facing", "Headers should not automatically inherit command usage contracts."),
        "expression_engine": ("selfdoc.function_contract", "Function-layer files should be reviewed as function catalog contracts."),
        "xbase_storage_engine": ("selfdoc.engine_contract", "Storage/DbArea files should generally be engine contracts."),
        "index_engine": ("selfdoc.engine_contract", "Index backend files should generally be engine/backend contracts."),
        "memo_engine": ("selfdoc.engine_contract", "Memo subsystem files should generally be engine/backend contracts."),
        "tui_tv_layer": ("selfdoc.ui_contract", "UI/Turbo Vision files need a UI contract type if documented."),
        "bindings_python": ("selfdoc.binding_contract", "Bindings should use binding/API contracts."),
        "test_dev_harness": ("selfdoc.test_contract or exclude", "Test/dev harness files should not be counted as missing command usage contracts by default."),
        "public_or_shared_header": ("api contract or exclude", "Shared headers are not automatically user command surfaces."),
        "other_source": ("manual classification", "Needs one-by-one triage before assigning a contract type."),
    }
    lines.append("| Lane | Contract recommendation | Notes |")
    lines.append("|---|---|---|")
    for lane, _ in lane_counts.most_common():
        rec, note = lane_policy.get(lane, ("manual classification", "No lane policy yet."))
        lines.append(f"| `{md_escape(lane)}` | `{md_escape(rec)}` | {md_escape(note)} |")
    lines.append("")
    lines.append("## Files that actually need `@dottalk.usage v1`")
    lines.append("")
    lines.append("These are likely command/help surface files where a missing command usage contract should remain on the backlog.")
    lines.append("")
    if not needs_usage_missing:
        lines.append("No missing `@dottalk.usage v1` files were identified by the current classifier.")
    else:
        lines.append("| Path | Lane | Recommended contract |")
        lines.append("|---|---|---|")
        for rec in sorted(needs_usage_missing, key=lambda r: r.path.lower()):
            lines.append(f"| `{md_escape(rec.path)}` | `{lane_for_path(rec.path)}` | `{recommended_contract_type(rec.path)}` |")
    lines.append("")
    lines.append("## Files with usage contracts but still escrow")
    lines.append("")
    lines.append("These already have `@dottalk.usage v1`, but the probe still flagged missing recommended fields, unknown fields, malformed lines, or multiple contracts.")
    lines.append("")
    if not usage_present_but_escrow:
        lines.append("No command/help-surface files with existing usage contracts were flagged as escrow.")
    else:
        lines.append("| Path | Status | Reasons | Fields present |")
        lines.append("|---|---|---|---|")
        for rec in sorted(usage_present_but_escrow, key=lambda r: r.path.lower())[:200]:
            lines.append(
                f"| `{md_escape(rec.path)}` | `{md_escape(rec.status)}` | "
                f"{md_escape(', '.join(escrow_reasons(rec)))} | "
                f"{md_escape(', '.join(rec.fields_present))} |"
            )
        if len(usage_present_but_escrow) > 200:
            lines.append(f"| ... | ... | `{len(usage_present_but_escrow) - 200} more omitted from markdown table` | ... |")
    lines.append("")
    lines.append("## Files to exclude or assign another contract type")
    lines.append("")
    lines.append("These should not automatically receive `@dottalk.usage v1`. They should either be excluded from command usage inventory or assigned another SelfDoc contract type.")
    lines.append("")
    if not exclude_or_other_contract:
        lines.append("No exclusion/alternate-contract candidates identified.")
    else:
        lines.append("| Path | Lane | Recommended contract type | Current status |")
        lines.append("|---|---|---|---|")
        for rec in sorted(exclude_or_other_contract, key=lambda r: (lane_for_path(r.path), r.path.lower()))[:250]:
            lines.append(
                f"| `{md_escape(rec.path)}` | `{lane_for_path(rec.path)}` | "
                f"`{recommended_contract_type(rec.path)}` | `{md_escape(rec.status)}` |"
            )
        if len(exclude_or_other_contract) > 250:
            lines.append(f"| ... | ... | `{len(exclude_or_other_contract) - 250} more omitted from markdown table` | ... |")
    lines.append("")
    lines.append("## Manual classification queue")
    lines.append("")
    lines.append("These files are not confidently command usage surfaces and are not confidently excluded by the current lane classifier.")
    lines.append("")
    if not review_before_decision:
        lines.append("No manual classification queue items identified.")
    else:
        lines.append("| Path | Lane | Status | Suggested next action |")
        lines.append("|---|---|---|---|")
        for rec in sorted(review_before_decision, key=lambda r: r.path.lower())[:200]:
            lines.append(
                f"| `{md_escape(rec.path)}` | `{lane_for_path(rec.path)}` | "
                f"`{md_escape(rec.status)}` | `{recommended_contract_type(rec.path)}` |"
            )
        if len(review_before_decision) > 200:
            lines.append(f"| ... | ... | `{len(review_before_decision) - 200} more omitted from markdown table` | ... |")
    lines.append("")
    lines.append("## Classifier tuning recommendations")
    lines.append("")
    lines.append("1. Split the current single `@dottalk.usage v1` expectation into contract families: command usage, function catalog, engine/API, UI, binding, test/probe, and generated/report artifacts.")
    lines.append("2. Do not count all `src\\` and `include\\` files as missing command usage contracts. Restrict required `@dottalk.usage v1` to command/help surface lanes first, especially `src\\cli\\cmd_*.cpp` and selected HELP/registry bridge files.")
    lines.append("3. Treat function implementation files such as `fn_*.cpp` as candidates for `selfdoc.function_contract`, not command usage contracts.")
    lines.append("4. Treat storage/backend files under xbase, xindex, memo, LMDB, and low-level infrastructure as engine/API contract candidates, not user command contracts.")
    lines.append("5. Treat headers as API/owner contract candidates unless they directly define user-visible command usage.")
    lines.append("6. Keep missing contracts as escrow candidates, but report a narrower `action_required_usage_contract` count so the backlog is actionable.")
    lines.append("7. Separate `missing_contract` from `malformed_existing_contract`; missing files may need lane assignment, while malformed existing headers need field-shape review.")
    lines.append("8. Preserve exact header hashing for existing contracts; do not normalize or repair marker text during inventory/review.")
    lines.append("")
    lines.append("## Recommended next work")
    lines.append("")
    lines.append("1. Add a lane-aware mode to `source_contract_inventory_probe.py` that reports both broad escrow and actionable command-usage backlog.")
    lines.append("2. Review the command/help surface missing list before adding any headers.")
    lines.append("3. Define separate SelfDoc contract schemas for function, engine, API/header, UI, binding, and test/probe files.")
    lines.append("4. Only after those categories are approved, plan small source-contract repair batches.")
    lines.append("")
    lines.append("## Non-mutation confirmation")
    lines.append("")
    lines.append("- No source files edited.")
    lines.append("- No DBFs written.")
    lines.append("- No HELP DATA rebuilt.")
    lines.append("- No CMDHELPCHK implementation or configuration modified.")
    lines.append("- No source contract headers repaired.")
    lines.append("- No loose scripts promoted.")
    lines.append("- This review writes only a markdown report.")

    output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return output


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Review source_contracts_inventory reports.")
    parser.add_argument("--root", default=".", help="Project root. Default: current directory, normally D:\\code\\ccode.")
    parser.add_argument("--report-dir", default=None, help="Optional report directory relative to root.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = Path(args.root).resolve()
    report_dir = find_report_dir(root, args.report_dir)
    summary, records, notes = load_records(report_dir)
    output = write_review(report_dir, summary, records, notes)

    print("SelfDoc source contract inventory review complete.")
    print(f"Read report directory: {report_dir}")
    print(f"Records reviewed: {len(records)}")
    print(f"Wrote: {output}")
    print("No source files were edited.")
    print("No DBFs were written.")
    print("CMDHELPCHK was not modified.")
    print("HELP DATA was not rebuilt.")
    print("No repairs were made.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
