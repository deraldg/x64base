#!/usr/bin/env python3
"""
source_contract_hotfix_004_validation_lane_tuning.py

SelfDoc report/probe validation-lane tuning for hotfix 004.

Run from:
    D:\code\ccode

Run after:
    python selfdoc\probes\source_contract_inventory_probe_v1_1.py
    python selfdoc\probes\source_contract_capture_hotfix_002_evidence_lanes.py
    python selfdoc\probes\source_contract_hotfix_004_writer_binding_validation.py

Reads:
    dottalkpp\docs\generated\reports\source_contracts_inventory_v1_1.csv
    dottalkpp\docs\generated\reports\source_contracts_inventory_v1_1.json
    dottalkpp\docs\generated\reports\source_contract_capture_hotfix_002_evidence_lanes.csv
    Batch 0 source files, read-only

Writes:
    dottalkpp\docs\generated\reports\source_contract_hotfix_004_tuned_evidence_lanes.md
    dottalkpp\docs\generated\reports\source_contract_hotfix_004_tuned_evidence_lanes.csv
    dottalkpp\docs\generated\reports\source_contract_hotfix_004_tuned_evidence_lanes.json
    dottalkpp\docs\generated\reports\source_contract_hotfix_004_validation_lane_tuning.md
    dottalkpp\docs\generated\reports\source_contract_hotfix_004_validation_lane_tuning.csv
    dottalkpp\docs\generated\reports\source_contract_hotfix_004_validation_lane_tuning.json

Purpose:
    Tune the validator/evidence-lane interpretation after writer-binding hotfix 004.

    Rows with:
      malformed: false
      action_class: accepted_existing_command_contract
      status: accepted
      clean marker-anchored parse
      source_repair_recommended: false

    should be treated as:
      CONFIRMED / DO_NOT_REPAIR

    not:
      SOURCE_REVIEW

    cmd_help.cpp remains:
      STALE_EVIDENCE / DO_NOT_REPAIR

Safety:
    SelfDoc report/probe tuning only.
    Does not edit DotTalk++ src/include.
    Does not write DBFs.
    Does not rebuild HELP DATA.
    Does not modify CMDHELPCHK.
    Does not repair source headers.
    Does not promote v1.1 to default.
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
from typing import Any


MARKER = "@dottalk.usage v1"
EXPECTED_VERSION = "v1.1-hotfix_004_writer_binding"

REPORT_DIR = Path("dottalkpp") / "docs" / "generated" / "reports"
INV_CSV = REPORT_DIR / "source_contracts_inventory_v1_1.csv"
INV_JSON = REPORT_DIR / "source_contracts_inventory_v1_1.json"
OLD_LANES_CSV = REPORT_DIR / "source_contract_capture_hotfix_002_evidence_lanes.csv"

TUNED_LANES_MD = REPORT_DIR / "source_contract_hotfix_004_tuned_evidence_lanes.md"
TUNED_LANES_CSV = REPORT_DIR / "source_contract_hotfix_004_tuned_evidence_lanes.csv"
TUNED_LANES_JSON = REPORT_DIR / "source_contract_hotfix_004_tuned_evidence_lanes.json"

TUNING_MD = REPORT_DIR / "source_contract_hotfix_004_validation_lane_tuning.md"
TUNING_CSV = REPORT_DIR / "source_contract_hotfix_004_validation_lane_tuning.csv"
TUNING_JSON = REPORT_DIR / "source_contract_hotfix_004_validation_lane_tuning.json"

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


@dataclass
class TunedLaneRow:
    path: str
    source_exists: bool
    inventory_row_present: bool
    inventory_probe_version: str
    malformed: bool
    action_class: str
    status: str
    prior_evidence_lane: str
    prior_secondary_lane: str
    tuned_evidence_lane: str
    tuned_secondary_lane: str
    confidence: str
    marker_count: int
    marker_anchored_hash: str
    marker_is_first_payload: bool
    anchored_parse_malformed_count: int
    anchored_parse_field_count: int
    required_shape_present: bool
    source_repair_recommended: bool
    expected_state_met: bool
    validation_lane: str
    recommended_next_action: str
    rationale: str
    notes: list[str] = field(default_factory=list)


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def b(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes", "y"}


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


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


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
    notes.append("decoded_as=utf-8-surrogateescape")
    return raw.decode("utf-8", errors="surrogateescape"), notes


def sha(text: str) -> str:
    if not text:
        return ""
    return hashlib.sha256(text.encode("utf-8", errors="surrogateescape")).hexdigest()


def norm_path(path: object) -> str:
    return str(path or "").replace("\\", "/")


def index_by_path(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    return {norm_path(row.get("path", "")): row for row in rows if row.get("path", "")}


def line_bounds(text: str, offset: int) -> tuple[int, int, str]:
    start = text.rfind("\n", 0, offset) + 1
    end = text.find("\n", offset)
    if end == -1:
        end = len(text)
    return start, end, text[start:end]


def marker_anchored_capture(text: str) -> str:
    match = re.search(re.escape(MARKER), text)
    if not match:
        return ""

    line_start, line_end, _line = line_bounds(text, match.start())
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


def parse_anchored_fields(block: str) -> tuple[dict[str, list[str]], list[str], bool]:
    fields: dict[str, list[str]] = {}
    malformed: list[str] = []
    seen_marker = False
    saw_payload = False
    marker_first_payload = False

    for raw in str(block or "").splitlines():
        line = strip_comment_prefix(raw)
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

        match = re.match(r"^([A-Za-z][A-Za-z0-9_ -]{0,60})\s*:\s*(.*)$", line)
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


def has_required_shape(fields: dict[str, list[str]]) -> bool:
    return bool(fields.get("command") or fields.get("commands")) and bool(fields.get("summary")) and bool(fields.get("usage") or fields.get("syntax"))


def analyze_target(root: Path, path: str, probe_version: str, inv: dict[str, str], old_lane: dict[str, str]) -> TunedLaneRow:
    source = root / path
    notes: list[str] = []
    source_exists = source.is_file()

    marker_count = 0
    marker_hash = ""
    marker_first = False
    malformed_count = 0
    field_count = 0
    required_shape = False

    if source_exists:
        text, read_notes = read_text(source)
        notes.extend(read_notes)
        marker_count = len(re.findall(re.escape(MARKER), text))
        capture = marker_anchored_capture(text)
        marker_hash = sha(capture)
        fields, malformed_lines, marker_first = parse_anchored_fields(capture)
        malformed_count = len(malformed_lines)
        field_count = len(fields)
        required_shape = has_required_shape(fields)

    malformed = b(inv.get("malformed", False))
    action_class = inv.get("action_class", "")
    status = inv.get("status", "")
    prior_lane = old_lane.get("evidence_lane", inv.get("evidence_lane", ""))
    prior_secondary = old_lane.get("secondary_lane", inv.get("secondary_lane", ""))
    repair = b(inv.get("source_repair_recommended", old_lane.get("source_repair_recommended", False)))

    tuned_lane = prior_lane
    tuned_secondary = prior_secondary or "DO_NOT_REPAIR"
    confidence = "LOW"
    validation_lane = "REVIEW"
    expected = False
    next_action = "manual review"
    rationale = ""

    if path == CMD_HELP:
        tuned_lane = "STALE_EVIDENCE"
        tuned_secondary = "DO_NOT_REPAIR"
        confidence = "HIGH"
        expected = not repair
        validation_lane = "STALE_EVIDENCE" if expected else "POLICY_REVIEW"
        next_action = "keep cmd_help.cpp stale evidence / do-not-repair until hash/source freshness is explained"
        rationale = "cmd_help.cpp remains protected as stale evidence; this tuning does not repair it."
    elif path in BATCH0_NINE:
        accepted_row_state = (
            bool(inv)
            and not malformed
            and action_class == "accepted_existing_command_contract"
            and status in {"accepted", "accepted_existing_command_contract", "ok"}
            and not repair
        )
        clean_evidence = (
            source_exists
            and marker_count == 1
            and marker_first
            and malformed_count == 0
            and required_shape
        )

        if accepted_row_state and clean_evidence:
            tuned_lane = "CONFIRMED"
            tuned_secondary = "DO_NOT_REPAIR"
            confidence = "HIGH"
            expected = True
            validation_lane = "CONFIRMED"
            next_action = "continue v1.1 promotion review; no source repair"
            rationale = "Accepted row state plus clean marker-anchored parse should not be SOURCE_REVIEW."
        elif accepted_row_state:
            tuned_lane = "ACCEPTED_EQUIVALENT"
            tuned_secondary = "DO_NOT_REPAIR"
            confidence = "MEDIUM"
            expected = True
            validation_lane = "ACCEPTED_EQUIVALENT"
            next_action = "accepted row state is corrected; review evidence details if needed"
            rationale = "Row state is corrected; evidence detail is incomplete or conservative."
        else:
            tuned_lane = "CLASSIFIER_REVIEW"
            tuned_secondary = "DO_NOT_REPAIR"
            confidence = "MEDIUM"
            expected = False
            validation_lane = "CLASSIFIER_REVIEW"
            next_action = "row state still not accepted; inspect writer-binding output"
            rationale = "Row state does not meet accepted-equivalent conditions."

    return TunedLaneRow(
        path=path,
        source_exists=source_exists,
        inventory_row_present=bool(inv),
        inventory_probe_version=probe_version,
        malformed=malformed,
        action_class=action_class,
        status=status,
        prior_evidence_lane=prior_lane,
        prior_secondary_lane=prior_secondary,
        tuned_evidence_lane=tuned_lane,
        tuned_secondary_lane=tuned_secondary,
        confidence=confidence,
        marker_count=marker_count,
        marker_anchored_hash=marker_hash,
        marker_is_first_payload=marker_first,
        anchored_parse_malformed_count=malformed_count,
        anchored_parse_field_count=field_count,
        required_shape_present=required_shape,
        source_repair_recommended=repair,
        expected_state_met=expected,
        validation_lane=validation_lane,
        recommended_next_action=next_action,
        rationale=rationale,
        notes=notes,
    )


def write_tuned_evidence_md(path: Path, summary: dict[str, Any], rows: list[TunedLaneRow]) -> None:
    lines = [
        "# Source Contract Hotfix 004 Tuned Evidence Lanes",
        "",
        f"Generated UTC: `{summary['generated_at_utc']}`",
        "",
        "Safety class: `SelfDoc report/validation tuning`",
        "",
        "## Verdict",
        "",
        "```text",
        f"tuned evidence status: {summary['tuned_evidence_status']}",
        f"inventory_probe_version: {summary['inventory_probe_version']}",
        f"confirmed_or_accepted_equivalent: {summary['confirmed_or_accepted_equivalent']}/9",
        f"cmd_help_stale_evidence_do_not_repair: {summary['cmd_help_stale_evidence_do_not_repair']}",
        f"source_repair_recommended: {summary['source_repair_recommended']}",
        "source repairs: NOT AUTHORIZED",
        "DBF writes: NOT AUTHORIZED",
        "HELP DATA rebuild: NOT AUTHORIZED",
        "CMDHELPCHK changes: NOT AUTHORIZED",
        "v1.1 default promotion: NOT AUTHORIZED",
        "```",
        "",
        "## Rows",
        "",
        "| Path | Prior lane | Tuned lane | Secondary | Confidence | Expected | Rationale |",
        "|---|---|---|---|---|---:|---|",
    ]
    for row in rows:
        lines.append(
            f"| `{md_escape(row.path)}` | `{md_escape(row.prior_evidence_lane)}` | "
            f"`{md_escape(row.tuned_evidence_lane)}` | `{md_escape(row.tuned_secondary_lane)}` | "
            f"`{md_escape(row.confidence)}` | {row.expected_state_met} | {md_escape(row.rationale)} |"
        )
    lines += [
        "",
        "## Non-mutation confirmation",
        "",
    ]
    for guard in summary["non_mutation_guards"]:
        lines.append(f"- `{guard}`")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_tuning_md(path: Path, summary: dict[str, Any], rows: list[TunedLaneRow]) -> None:
    lines = [
        "# Source Contract Hotfix 004 Validation Lane Tuning",
        "",
        f"Generated UTC: `{summary['generated_at_utc']}`",
        "",
        "Safety class: `SelfDoc validation tuning`",
        "",
        "## Verdict",
        "",
        "```text",
        f"validation status: {summary['validation_status']}",
        f"inventory_probe_version: {summary['inventory_probe_version']}",
        f"batch0_tuned_expected_state_met: {summary['batch0_tuned_expected_state_met']}/9",
        f"cmd_help_stale_evidence_do_not_repair: {summary['cmd_help_stale_evidence_do_not_repair']}",
        f"source_repair_recommended: {summary['source_repair_recommended']}",
        "source repairs: NOT AUTHORIZED",
        "DBF writes: NOT AUTHORIZED",
        "HELP DATA rebuild: NOT AUTHORIZED",
        "CMDHELPCHK changes: NOT AUTHORIZED",
        "v1.1 default promotion: NOT AUTHORIZED",
        "```",
        "",
        "## Interpretation",
        "",
        "The row-state correction is treated as functionally valid when the inventory row is accepted, no source repair is recommended, and the marker-anchored parse is clean. A conservative previous lane such as `SOURCE_REVIEW` is tuned to `CONFIRMED` or `ACCEPTED_EQUIVALENT` for these corrected rows.",
        "",
        "## Rows",
        "",
        "| Path | Malformed | Action | Status | Tuned lane | Expected | Next action |",
        "|---|---:|---|---|---|---:|---|",
    ]
    for row in rows:
        lines.append(
            f"| `{md_escape(row.path)}` | {row.malformed} | `{md_escape(row.action_class)}` | "
            f"`{md_escape(row.status)}` | `{md_escape(row.tuned_evidence_lane)}` | "
            f"{row.expected_state_met} | {md_escape(row.recommended_next_action)} |"
        )
    lines += [
        "",
        "## Recommended next action",
        "",
        summary["recommended_next_overall_action"],
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

    inv_rows = index_by_path(read_csv_rows(root / INV_CSV))
    old_lanes = index_by_path(read_csv_rows(root / OLD_LANES_CSV))
    inv_json = read_json(root / INV_JSON)
    inv_summary = inv_json.get("summary", {}) if isinstance(inv_json.get("summary", {}), dict) else {}
    probe_version = str(inv_summary.get("probe_version", ""))

    paths = list(BATCH0_NINE) + [CMD_HELP]
    rows = [analyze_target(root, path, probe_version, inv_rows.get(path, {}), old_lanes.get(path, {})) for path in paths]

    lane_counts = Counter(row.tuned_evidence_lane for row in rows)
    batch_expected = sum(1 for row in rows if row.path in BATCH0_NINE and row.expected_state_met)
    cmd_help_ok = any(row.path == CMD_HELP and row.tuned_evidence_lane == "STALE_EVIDENCE" and row.tuned_secondary_lane == "DO_NOT_REPAIR" and not row.source_repair_recommended for row in rows)
    repair_count = sum(1 for row in rows if row.source_repair_recommended)

    if probe_version != EXPECTED_VERSION:
        validation_status = "NOT_PASSED_WRONG_PROBE_VERSION"
        next_action = "Rerun writer-binding inventory first; tuned validation requires v1.1-hotfix_004_writer_binding output."
    elif batch_expected == len(BATCH0_NINE) and cmd_help_ok and repair_count == 0:
        validation_status = "PASSED"
        next_action = "Validation-lane tuning passes. Continue v1.1 promotion review; do not repair source."
    else:
        validation_status = "NOT_PASSED_REVIEW_REQUIRED"
        next_action = "Review tuned rows. Row-state or stale-evidence expectations are not fully met."

    common_guards = [
        "did_not_edit_dottalkpp_src_or_include",
        "did_not_apply_source_repair_patches",
        "did_not_write_dbfs",
        "did_not_rebuild_help_data",
        "did_not_modify_cmdhelpchk",
        "did_not_promote_v1_1_to_default",
        "did_not_move_or_delete_project_files",
    ]

    tuned_summary = {
        "generated_at_utc": now(),
        "status": "TUNED_EVIDENCE_LANES_GENERATED",
        "tuned_evidence_status": "GENERATED",
        "inventory_probe_version": probe_version,
        "confirmed_or_accepted_equivalent": batch_expected,
        "cmd_help_stale_evidence_do_not_repair": cmd_help_ok,
        "source_repair_recommended": repair_count,
        "tuned_lane_counts": dict(lane_counts.most_common()),
        "non_mutation_guards": common_guards,
    }

    tuning_summary = {
        "generated_at_utc": tuned_summary["generated_at_utc"],
        "status": "VALIDATION_LANE_TUNING_GENERATED",
        "validation_status": validation_status,
        "inventory_probe_version": probe_version,
        "rows_reviewed": len(rows),
        "batch0_tuned_expected_state_met": batch_expected,
        "cmd_help_stale_evidence_do_not_repair": cmd_help_ok,
        "source_repair_recommended": repair_count,
        "tuned_lane_counts": dict(lane_counts.most_common()),
        "recommended_next_overall_action": next_action,
        "non_mutation_guards": common_guards,
    }

    fieldnames = list(asdict(rows[0]).keys()) if rows else []
    row_dicts = []
    for row in rows:
        data = asdict(row)
        data["notes"] = "; ".join(row.notes)
        row_dicts.append(data)

    write_csv(root / TUNED_LANES_CSV, row_dicts, fieldnames)
    write_csv(root / TUNING_CSV, row_dicts, fieldnames)

    (root / TUNED_LANES_JSON).write_text(json.dumps({"summary": tuned_summary, "rows": row_dicts}, indent=2), encoding="utf-8")
    (root / TUNING_JSON).write_text(json.dumps({"summary": tuning_summary, "rows": row_dicts}, indent=2), encoding="utf-8")

    write_tuned_evidence_md(root / TUNED_LANES_MD, tuned_summary, rows)
    write_tuning_md(root / TUNING_MD, tuning_summary, rows)

    print("SelfDoc hotfix 004 validation-lane tuning complete.")
    print(f"Validation status: {validation_status}")
    print(f"Inventory probe version: {probe_version}")
    print(f"Batch 0 tuned expected state: {batch_expected}/9")
    print(f"cmd_help stale evidence / do not repair: {cmd_help_ok}")
    print(f"Source repair recommended: {repair_count}")
    print(f"Wrote: {TUNED_LANES_MD}")
    print(f"Wrote: {TUNED_LANES_CSV}")
    print(f"Wrote: {TUNED_LANES_JSON}")
    print(f"Wrote: {TUNING_MD}")
    print(f"Wrote: {TUNING_CSV}")
    print(f"Wrote: {TUNING_JSON}")
    print("No DotTalk++ src/include files were edited.")
    print("No DBFs were written.")
    print("HELP DATA was not rebuilt.")
    print("CMDHELPCHK was not modified.")
    print("v1.1 was not promoted to default.")

    return 0 if validation_status == "PASSED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
