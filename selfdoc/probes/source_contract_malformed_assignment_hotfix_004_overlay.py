#!/usr/bin/env python3
"""
source_contract_malformed_assignment_hotfix_004_overlay.py

REPORT_ONLY / OVERLAY_ONLY candidate overlay for malformed-assignment false positives.

Run from:
    D:\code\ccode

Reads:
    dottalkpp\docs\generated\reports\source_contracts_inventory_v1_1.csv
    dottalkpp\docs\generated\reports\source_contracts_inventory_v1_1.json
    dottalkpp\docs\generated\reports\source_contract_capture_hotfix_002_evidence_lanes.csv
    Batch 0 source files, read-only

Writes:
    dottalkpp\docs\generated\reports\source_contracts_inventory_v1_1_hotfix_004_candidate.md
    dottalkpp\docs\generated\reports\source_contracts_inventory_v1_1_hotfix_004_candidate.csv
    dottalkpp\docs\generated\reports\source_contracts_inventory_v1_1_hotfix_004_candidate.json
    dottalkpp\docs\generated\reports\source_contract_malformed_assignment_hotfix_004_validation.md
    dottalkpp\docs\generated\reports\source_contract_malformed_assignment_hotfix_004_validation.csv
    dottalkpp\docs\generated\reports\source_contract_malformed_assignment_hotfix_004_validation.json

Safety:
    REPORT_ONLY / OVERLAY_ONLY
    Does not edit source.
    Does not patch source_contract_inventory_probe_v1_1.py.
    Does not overwrite v1.1 inventory files.
    Does not write DBFs.
    Does not modify CMDHELPCHK.
    Does not rebuild HELP DATA.
    Does not repair source headers.
    Does not move/delete files.
    Does not promote v1.1 to default.

Purpose:
    003 proved the row hook did not clear malformed=True in v1.1 output.
    004 therefore avoids more blind probe surgery and creates a reviewable candidate overlay.

Overlay rule for Batch 0 nine rows:
    If current inventory says malformed=True / shape_review, but current source marker-anchored parse has:
      marker_is_first_payload: true
      anchored_parse_malformed_count: 0
      required command shape present
    then candidate output clears capture-only malformed state:
      malformed=False
      action_class=accepted_existing_command_contract
      status=accepted
      evidence_lane=CONFIRMED
      secondary_lane=DO_NOT_REPAIR
      source_repair_recommended=False

cmd_help.cpp:
    remains STALE_EVIDENCE / DO_NOT_REPAIR until hash/source freshness is explained.
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
REPORT_DIR = Path("dottalkpp") / "docs" / "generated" / "reports"

INV_CSV = REPORT_DIR / "source_contracts_inventory_v1_1.csv"
INV_JSON = REPORT_DIR / "source_contracts_inventory_v1_1.json"
LANES_CSV = REPORT_DIR / "source_contract_capture_hotfix_002_evidence_lanes.csv"

CAND_MD = REPORT_DIR / "source_contracts_inventory_v1_1_hotfix_004_candidate.md"
CAND_CSV = REPORT_DIR / "source_contracts_inventory_v1_1_hotfix_004_candidate.csv"
CAND_JSON = REPORT_DIR / "source_contracts_inventory_v1_1_hotfix_004_candidate.json"

VAL_MD = REPORT_DIR / "source_contract_malformed_assignment_hotfix_004_validation.md"
VAL_CSV = REPORT_DIR / "source_contract_malformed_assignment_hotfix_004_validation.csv"
VAL_JSON = REPORT_DIR / "source_contract_malformed_assignment_hotfix_004_validation.json"

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
class OverlayDecision:
    path: str
    source_exists: bool
    inventory_present: bool
    before_malformed: bool
    before_action_class: str
    before_status: str
    before_evidence_lane: str = ""
    marker_count: int = 0
    marker_anchored_hash: str = ""
    marker_is_first_payload: bool = False
    anchored_parse_malformed_count: int = 0
    anchored_parse_field_count: int = 0
    required_shape_present: bool = False
    overlay_applied: bool = False
    after_malformed: bool = False
    after_action_class: str = ""
    after_status: str = ""
    after_evidence_lane: str = ""
    after_secondary_lane: str = ""
    source_repair_recommended: bool = False
    validation_lane: str = ""
    confidence: str = ""
    recommended_next_action: str = ""
    rationale: str = ""
    notes: list[str] = field(default_factory=list)


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


def write_csv_rows(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
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
    marker_first_payload = False
    saw_payload = False

    for raw in block.splitlines():
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


def has_required_command_shape(fields: dict[str, list[str]]) -> bool:
    has_command = bool(fields.get("command") or fields.get("commands"))
    has_summary = bool(fields.get("summary"))
    has_usage_or_syntax = bool(fields.get("usage") or fields.get("syntax"))
    return has_command and has_summary and has_usage_or_syntax


def index_by_path(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    return {row.get("path", "").replace("\\", "/"): row for row in rows if row.get("path", "")}


def make_candidate_row(row: dict[str, str], decision: OverlayDecision) -> dict[str, Any]:
    out: dict[str, Any] = dict(row)

    # Add overlay columns without deleting original evidence.
    out["hotfix_004_overlay_applied"] = str(decision.overlay_applied)
    out["hotfix_004_validation_lane"] = decision.validation_lane
    out["hotfix_004_confidence"] = decision.confidence
    out["hotfix_004_marker_anchored_hash"] = decision.marker_anchored_hash
    out["hotfix_004_marker_is_first_payload"] = str(decision.marker_is_first_payload)
    out["hotfix_004_anchored_parse_malformed_count"] = str(decision.anchored_parse_malformed_count)
    out["hotfix_004_required_shape_present"] = str(decision.required_shape_present)
    out["hotfix_004_rationale"] = decision.rationale

    if decision.overlay_applied:
        out["malformed"] = "False"
        out["malformed_count"] = "0"
        out["malformed_lines"] = ""
        out["action_class"] = "accepted_existing_command_contract"
        out["status"] = "accepted"
        out["evidence_lane"] = "CONFIRMED"
        out["secondary_lane"] = "DO_NOT_REPAIR"
        out["source_repair_recommended"] = "False"
        out["repair_authorized"] = "False"

        notes = str(out.get("notes", "") or "")
        add = "hotfix_004_overlay: cleared capture-only malformed assignment after clean marker-anchored parse"
        out["notes"] = (notes + "; " + add).strip("; ") if notes else add

    return out


def analyze_path(root: Path, path: str, inv_row: dict[str, str], lane_row: dict[str, str]) -> OverlayDecision:
    src = root / path
    before_malformed = b(inv_row.get("malformed", False))
    before_action = inv_row.get("action_class", "")
    before_status = inv_row.get("status", "")
    before_lane = lane_row.get("evidence_lane", inv_row.get("evidence_lane", ""))

    decision = OverlayDecision(
        path=path,
        source_exists=src.is_file(),
        inventory_present=bool(inv_row),
        before_malformed=before_malformed,
        before_action_class=before_action,
        before_status=before_status,
        before_evidence_lane=before_lane,
        after_malformed=before_malformed,
        after_action_class=before_action,
        after_status=before_status,
        after_evidence_lane=before_lane,
        after_secondary_lane=lane_row.get("secondary_lane", inv_row.get("secondary_lane", "")),
        source_repair_recommended=False,
    )

    if not inv_row:
        decision.validation_lane = "STALE_EVIDENCE"
        decision.confidence = "LOW"
        decision.recommended_next_action = "refresh inventory; row is missing"
        decision.rationale = "Inventory row missing."
        return decision

    if not src.is_file():
        decision.validation_lane = "SOURCE_REVIEW"
        decision.confidence = "NONE"
        decision.recommended_next_action = "source file missing; cannot validate overlay"
        decision.rationale = "Source file missing."
        return decision

    text, notes = read_text(src)
    decision.notes.extend(notes)
    decision.marker_count = len(re.findall(re.escape(MARKER), text))
    anchored = marker_anchored_capture(text)
    decision.marker_anchored_hash = sha(anchored)
    fields, malformed_lines, marker_first = parse_anchored_fields(anchored)
    decision.marker_is_first_payload = marker_first
    decision.anchored_parse_field_count = len(fields)
    decision.anchored_parse_malformed_count = len(malformed_lines)
    decision.required_shape_present = has_required_command_shape(fields)

    if path == CMD_HELP:
        decision.validation_lane = "STALE_EVIDENCE"
        decision.after_evidence_lane = "STALE_EVIDENCE"
        decision.after_secondary_lane = "DO_NOT_REPAIR"
        decision.confidence = "HIGH"
        decision.recommended_next_action = "keep cmd_help.cpp in stale-evidence lane until hash/source freshness is explained"
        decision.rationale = "cmd_help.cpp is intentionally not fixed by the Batch 0 malformed-assignment overlay."
        return decision

    if path in BATCH0_NINE and before_malformed and marker_first and not malformed_lines and decision.required_shape_present:
        decision.overlay_applied = True
        decision.after_malformed = False
        decision.after_action_class = "accepted_existing_command_contract"
        decision.after_status = "accepted"
        decision.after_evidence_lane = "CONFIRMED"
        decision.after_secondary_lane = "DO_NOT_REPAIR"
        decision.validation_lane = "CONFIRMED"
        decision.confidence = "HIGH"
        decision.recommended_next_action = "review candidate overlay; source repair remains closed"
        decision.rationale = "Inventory malformed=True is not supported by marker-anchored clean parse with required command shape present."
        return decision

    if path in BATCH0_NINE and before_malformed:
        decision.validation_lane = "CLASSIFIER_REVIEW"
        decision.confidence = "MEDIUM"
        decision.recommended_next_action = "do not repair source; inspect remaining classifier evidence"
        decision.rationale = "Overlay rule did not apply cleanly."
        return decision

    decision.validation_lane = "CONFIRMED" if not before_malformed else "CLASSIFIER_REVIEW"
    decision.confidence = "MEDIUM"
    decision.recommended_next_action = "no overlay needed" if not before_malformed else "classifier review required"
    decision.rationale = "No capture-only malformed overlay was needed."
    return decision


def write_validation_csv(path: Path, decisions: list[OverlayDecision]) -> None:
    fieldnames = list(asdict(decisions[0]).keys()) if decisions else []
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for decision in decisions:
            data = asdict(decision)
            for key, value in list(data.items()):
                if isinstance(value, list):
                    data[key] = "; ".join(str(v) for v in value)
            writer.writerow(data)


def write_md(path: Path, summary: dict[str, Any], decisions: list[OverlayDecision]) -> None:
    lines = [
        "# Source Contract Malformed Assignment Hotfix 004 Overlay",
        "",
        f"Generated UTC: `{summary['generated_at_utc']}`",
        "",
        "Safety class: `REPORT_ONLY / OVERLAY_ONLY`",
        "",
        "## Verdict",
        "",
        "```text",
        f"overlay status: {summary['overlay_status']}",
        f"candidate inventory written: {summary['candidate_inventory_written']}",
        f"overlay_applied_count: {summary['overlay_applied_count']}",
        f"source_repair_recommended: {summary['source_repair_recommended']}",
        "source repairs: NOT AUTHORIZED",
        "probe patching: NOT PERFORMED",
        "DBF writes: NOT AUTHORIZED",
        "CMDHELPCHK changes: NOT AUTHORIZED",
        "HELP DATA rebuild: NOT AUTHORIZED",
        "v1.1 default promotion: NOT AUTHORIZED",
        "```",
        "",
        "## Interpretation",
        "",
        "Hotfix 003 proved the row hook did not clear `malformed=True` in the live v1.1 output. Hotfix 004 avoids another blind probe surgery and writes a separate candidate overlay. The original v1.1 inventory is not overwritten.",
        "",
        "## Summary counts",
        "",
    ]
    for key in [
        "rows_reviewed",
        "overlay_applied_count",
        "confirmed",
        "classifier_review",
        "stale_evidence",
        "source_review",
        "cmd_help_stale_evidence_do_not_repair",
        "source_repair_recommended",
    ]:
        lines.append(f"- {key}: `{summary.get(key, '')}`")
    lines += [
        "",
        "## Rows",
        "",
        "| Path | Before malformed | Overlay applied | After action | Lane | Confidence | Next action |",
        "|---|---:|---:|---|---|---|---|",
    ]
    for d in decisions:
        lines.append(
            f"| `{md_escape(d.path)}` | {d.before_malformed} | {d.overlay_applied} | "
            f"`{md_escape(d.after_action_class)}` | `{md_escape(d.validation_lane)}` | "
            f"`{md_escape(d.confidence)}` | {md_escape(d.recommended_next_action)} |"
        )
    lines += [
        "",
        "## Outputs",
        "",
        f"- `{CAND_MD}`",
        f"- `{CAND_CSV}`",
        f"- `{CAND_JSON}`",
        f"- `{VAL_MD}`",
        f"- `{VAL_CSV}`",
        f"- `{VAL_JSON}`",
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
    report_dir = root / REPORT_DIR
    report_dir.mkdir(parents=True, exist_ok=True)

    inv_rows = read_csv_rows(root / INV_CSV)
    inv_json = read_json(root / INV_JSON)
    lanes_rows = read_csv_rows(root / LANES_CSV)

    inv_by_path = index_by_path(inv_rows)
    lanes_by_path = index_by_path(lanes_rows)

    paths = list(BATCH0_NINE) + [CMD_HELP]
    decisions = [analyze_path(root, path, inv_by_path.get(path, {}), lanes_by_path.get(path, {})) for path in paths]

    decision_by_path = {d.path: d for d in decisions}

    # Build candidate inventory rows: preserve all rows and alter only overlay-approved rows.
    candidate_rows: list[dict[str, Any]] = []
    for row in inv_rows:
        path = row.get("path", "").replace("\\", "/")
        if path in decision_by_path:
            candidate_rows.append(make_candidate_row(row, decision_by_path[path]))
        else:
            out = dict(row)
            out.setdefault("hotfix_004_overlay_applied", "False")
            candidate_rows.append(out)

    # Preserve original field order and append overlay fields.
    fieldnames = list(inv_rows[0].keys()) if inv_rows else []
    overlay_fields = [
        "hotfix_004_overlay_applied",
        "hotfix_004_validation_lane",
        "hotfix_004_confidence",
        "hotfix_004_marker_anchored_hash",
        "hotfix_004_marker_is_first_payload",
        "hotfix_004_anchored_parse_malformed_count",
        "hotfix_004_required_shape_present",
        "hotfix_004_rationale",
    ]
    for field in overlay_fields:
        if field not in fieldnames:
            fieldnames.append(field)

    write_csv_rows(root / CAND_CSV, candidate_rows, fieldnames)

    counts = Counter(d.validation_lane for d in decisions)
    overlay_applied_count = sum(1 for d in decisions if d.overlay_applied)
    repair_count = sum(1 for d in decisions if d.source_repair_recommended)
    cmd_help_ok = any(d.path == CMD_HELP and d.validation_lane == "STALE_EVIDENCE" and d.after_secondary_lane == "DO_NOT_REPAIR" for d in decisions)

    inventory_summary = inv_json.get("summary", {}) if isinstance(inv_json.get("summary", {}), dict) else {}
    candidate_summary = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "OVERLAY_ONLY_GENERATED",
        "base_inventory_probe_version": inventory_summary.get("probe_version", ""),
        "base_inventory_rows": len(inv_rows),
        "candidate_inventory_rows": len(candidate_rows),
        "overlay_applied_count": overlay_applied_count,
        "cmd_help_stale_evidence_do_not_repair": cmd_help_ok,
        "source_repair_recommended": repair_count,
        "note": "Candidate overlay only. Original source_contracts_inventory_v1_1 outputs were not overwritten.",
        "non_mutation_guards": [
            "did_not_edit_source",
            "did_not_patch_probe",
            "did_not_overwrite_v1_1_inventory",
            "did_not_write_dbfs",
            "did_not_modify_cmdhelpchk",
            "did_not_rebuild_help_data",
            "did_not_repair_headers",
            "did_not_promote_v1_1_to_default",
            "did_not_move_or_delete_files",
        ],
    }

    validation_summary = {
        "generated_at_utc": candidate_summary["generated_at_utc"],
        "status": "REVIEW_ONLY_GENERATED",
        "overlay_status": "PASSED_OVERLAY_CANDIDATE" if overlay_applied_count == len(BATCH0_NINE) and repair_count == 0 and cmd_help_ok else "REVIEW_REQUIRED",
        "candidate_inventory_written": True,
        "base_inventory_probe_version": inventory_summary.get("probe_version", ""),
        "rows_reviewed": len(decisions),
        "overlay_applied_count": overlay_applied_count,
        "confirmed": counts.get("CONFIRMED", 0),
        "classifier_review": counts.get("CLASSIFIER_REVIEW", 0),
        "stale_evidence": counts.get("STALE_EVIDENCE", 0),
        "source_review": counts.get("SOURCE_REVIEW", 0),
        "cmd_help_stale_evidence_do_not_repair": cmd_help_ok,
        "source_repair_recommended": repair_count,
        "validation_lane_counts": dict(counts.most_common()),
        "recommended_next_overall_action": (
            "Review candidate overlay. If accepted, integrate the same final-row normalization into v1.1 writer/classifier deliberately."
            if overlay_applied_count == len(BATCH0_NINE) and repair_count == 0 and cmd_help_ok
            else "Overlay did not meet target; inspect validation rows before any probe patch."
        ),
        "non_mutation_guards": candidate_summary["non_mutation_guards"],
    }

    (root / CAND_JSON).write_text(json.dumps({"summary": candidate_summary, "rows": candidate_rows}, indent=2), encoding="utf-8")
    (root / VAL_JSON).write_text(json.dumps({"summary": validation_summary, "rows": [asdict(d) for d in decisions]}, indent=2), encoding="utf-8")
    write_validation_csv(root / VAL_CSV, decisions)
    write_md(root / VAL_MD, validation_summary, decisions)

    # Candidate MD is a concise pointer to the validation report.
    (root / CAND_MD).write_text(
        "\n".join([
            "# Source Contracts Inventory v1.1 Hotfix 004 Candidate",
            "",
            f"Generated UTC: `{candidate_summary['generated_at_utc']}`",
            "",
            "Safety class: `REPORT_ONLY / OVERLAY_ONLY`",
            "",
            "This is a candidate overlay inventory. It does not overwrite `source_contracts_inventory_v1_1.*`.",
            "",
            f"- base_inventory_probe_version: `{candidate_summary['base_inventory_probe_version']}`",
            f"- base_inventory_rows: `{candidate_summary['base_inventory_rows']}`",
            f"- candidate_inventory_rows: `{candidate_summary['candidate_inventory_rows']}`",
            f"- overlay_applied_count: `{candidate_summary['overlay_applied_count']}`",
            f"- cmd_help_stale_evidence_do_not_repair: `{candidate_summary['cmd_help_stale_evidence_do_not_repair']}`",
            f"- source_repair_recommended: `{candidate_summary['source_repair_recommended']}`",
            "",
            "See:",
            "",
            f"- `{VAL_MD}`",
            f"- `{VAL_CSV}`",
            f"- `{VAL_JSON}`",
            "",
        ]) + "\n",
        encoding="utf-8",
    )

    print("SelfDoc malformed assignment hotfix 004 overlay complete.")
    print(f"Overlay status: {validation_summary['overlay_status']}")
    print(f"Overlay applied count: {overlay_applied_count}")
    print(f"cmd_help stale evidence/do not repair: {cmd_help_ok}")
    print(f"Source repair recommended: {repair_count}")
    print(f"Wrote: {CAND_MD}")
    print(f"Wrote: {CAND_CSV}")
    print(f"Wrote: {CAND_JSON}")
    print(f"Wrote: {VAL_MD}")
    print(f"Wrote: {VAL_CSV}")
    print(f"Wrote: {VAL_JSON}")
    print("No source files were edited.")
    print("No probe patch was applied.")
    print("No v1.1 inventory files were overwritten.")
    print("No DBFs were written.")
    print("CMDHELPCHK was not modified.")
    print("HELP DATA was not rebuilt.")

    return 0 if validation_summary["overlay_status"] == "PASSED_OVERLAY_CANDIDATE" else 2


if __name__ == "__main__":
    raise SystemExit(main())
