#!/usr/bin/env python3
"""
source_contract_capture_hotfix_002_evidence_lanes.py

REPORT_ONLY / REVIEW_ONLY postprocess for capture_hotfix_002.

Run after:
  python selfdoc\probes\source_contract_inventory_probe_v1_1.py

Reads:
  dottalkpp\docs\generated\reports\source_contracts_inventory_v1_1.csv
  dottalkpp\docs\generated\reports\source_contracts_inventory_v1_1.json
  Batch 0 source files, read-only

Writes:
  dottalkpp\docs\generated\reports\source_contract_capture_hotfix_002_evidence_lanes.md
  dottalkpp\docs\generated\reports\source_contract_capture_hotfix_002_evidence_lanes.csv
  dottalkpp\docs\generated\reports\source_contract_capture_hotfix_002_evidence_lanes.json

Safety:
  REPORT_ONLY / REVIEW_ONLY
  No source edits.
  No DBF writes.
  No HELP DATA rebuild.
  No CMDHELPCHK changes.
  No repairs.
  No v1.1 default promotion.

Purpose:
  Apply SelfDoc Collection Imperfection Policy lanes to the current Batch 0 issue:
    CAPTURE_REVIEW
    CLASSIFIER_REVIEW
    STALE_EVIDENCE
    DO_NOT_REPAIR
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

OUT_MD = REPORT_DIR / "source_contract_capture_hotfix_002_evidence_lanes.md"
OUT_CSV = REPORT_DIR / "source_contract_capture_hotfix_002_evidence_lanes.csv"
OUT_JSON = REPORT_DIR / "source_contract_capture_hotfix_002_evidence_lanes.json"

BATCH0 = [
    "src/cli/cmd_area.cpp",
    "src/cli/cmd_calcwrite.cpp",
    "src/cli/cmd_close.cpp",
    "src/cli/cmd_color.cpp",
    "src/cli/cmd_commit.cpp",
    "src/cli/cmd_copy.cpp",
    "src/cli/cmd_dir.cpp",
    "src/cli/cmd_foxhelp.cpp",
    "src/cli/cmd_help.cpp",
    "src/cli/cmd_list_lmdb.cpp",
]

LANE_CAPTURE_REVIEW = "CAPTURE_REVIEW"
LANE_CLASSIFIER_REVIEW = "CLASSIFIER_REVIEW"
LANE_STALE_EVIDENCE = "STALE_EVIDENCE"
LANE_DO_NOT_REPAIR = "DO_NOT_REPAIR"


@dataclass
class EvidenceLaneRow:
    path: str
    source_exists: bool
    inventory_row_present: bool
    inventory_malformed: bool = False
    action_class: str = ""
    header_hash: str = ""
    marker_count: int = 0
    marker_anchored_hash: str = ""
    hash_matches_inventory: bool = False
    marker_is_first_payload: bool = False
    preamble_before_marker_count: int = 0
    anchored_parse_malformed_count: int = 0
    anchored_parse_field_count: int = 0
    evidence_lane: str = ""
    secondary_lane: str = ""
    confidence: str = ""
    status: str = ""
    recommended_next_action: str = ""
    mutation_authorized: bool = False
    source_repair_authorized: bool = False
    source_repair_recommended: bool = False
    rationale: str = ""
    notes: list[str] = field(default_factory=list)


def b(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes", "y"}


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


def md_escape(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


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


def broad_preamble_count(text: str) -> int:
    match = re.search(re.escape(MARKER), text)
    if not match:
        return 0
    marker_start = match.start()
    line_start, _line_end, _line = line_bounds(text, marker_start)
    count = 0
    pos = line_start
    while pos > 0:
        prev_end = pos - 1
        prev_start = text.rfind("\n", 0, prev_end) + 1
        prev_line = text[prev_start:prev_end]
        if prev_line.lstrip().startswith("//"):
            count += 1
            pos = prev_start
            continue
        break
    return count


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


def parse_anchored_fields(block: str) -> tuple[int, int, bool]:
    fields: dict[str, list[str]] = {}
    malformed: list[str] = []
    seen_marker = False
    marker_first_payload = False
    payload_seen = False

    for raw in block.splitlines():
        line = strip_comment_prefix(raw)
        if not line:
            continue
        if MARKER in line:
            seen_marker = True
            if not payload_seen:
                marker_first_payload = True
            payload_seen = True
            continue
        payload_seen = True
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
        fields.setdefault(key, []).append(match.group(2).strip())

    return len(fields), len(malformed), marker_first_payload


def index_by_path(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    return {row.get("path", "").replace("\\", "/"): row for row in rows if row.get("path", "")}


def review_one(root: Path, path: str, inv: dict[str, str]) -> EvidenceLaneRow:
    src = root / path
    row = EvidenceLaneRow(
        path=path,
        source_exists=src.is_file(),
        inventory_row_present=bool(inv),
        inventory_malformed=b(inv.get("malformed", False)),
        action_class=inv.get("action_class", ""),
        header_hash=inv.get("header_hash", ""),
    )

    if not src.is_file():
        row.evidence_lane = LANE_SOURCE_REVIEW if False else "SOURCE_REVIEW"
        row.confidence = "NONE"
        row.status = "SOURCE_MISSING"
        row.recommended_next_action = "locate source before further review"
        row.rationale = "Source file could not be read."
        return row

    text, notes = read_text(src)
    row.notes.extend(notes)
    row.marker_count = len(re.findall(re.escape(MARKER), text))
    row.preamble_before_marker_count = broad_preamble_count(text)

    anchored = marker_anchored_capture(text)
    row.marker_anchored_hash = sha(anchored)
    row.hash_matches_inventory = bool(row.header_hash) and row.header_hash == row.marker_anchored_hash

    fields, malformed, marker_first = parse_anchored_fields(anchored)
    row.anchored_parse_field_count = fields
    row.anchored_parse_malformed_count = malformed
    row.marker_is_first_payload = marker_first

    if path.endswith("cmd_help.cpp") and not row.hash_matches_inventory:
        row.evidence_lane = LANE_STALE_EVIDENCE
        row.secondary_lane = LANE_DO_NOT_REPAIR
        row.confidence = "HIGH"
        row.status = "STALE_OR_DRIFTED_EVIDENCE"
        row.recommended_next_action = "refresh inventory/evidence or compare source history before any patch path"
        row.source_repair_recommended = False
        row.rationale = "cmd_help.cpp inventory hash does not match current marker-anchored capture; treat as stale/drifted evidence, not source defect."
        return row

    if row.inventory_malformed and row.hash_matches_inventory and malformed == 0 and marker_first:
        row.evidence_lane = LANE_CLASSIFIER_REVIEW
        row.secondary_lane = LANE_DO_NOT_REPAIR
        row.confidence = "HIGH"
        row.status = "MALFORMED_FLAG_NOT_SUPPORTED_BY_MARKER_ANCHORED_PARSE"
        row.recommended_next_action = "patch report-only classifier/shape-review rule; do not repair source"
        row.source_repair_recommended = False
        row.rationale = "Marker-anchored payload parses without malformed lines, but inventory still marks malformed."
        return row

    if row.inventory_malformed and row.preamble_before_marker_count > 0:
        row.evidence_lane = LANE_CAPTURE_REVIEW
        row.secondary_lane = LANE_CLASSIFIER_REVIEW
        row.confidence = "MEDIUM"
        row.status = "Preamble before marker remains implicated"
        row.recommended_next_action = "verify capture boundary and malformed assignment; do not repair source"
        row.source_repair_recommended = False
        row.rationale = "Preamble exists before marker; if this still drives malformed=True, the issue is capture/classifier logic."
        return row

    if not row.inventory_malformed and row.hash_matches_inventory:
        row.evidence_lane = "CONFIRMED"
        row.secondary_lane = LANE_DO_NOT_REPAIR
        row.confidence = "HIGH"
        row.status = "CAPTURE_HOTFIX_EFFECTIVE_FOR_FILE"
        row.recommended_next_action = "no source repair"
        row.source_repair_recommended = False
        row.rationale = "Inventory no longer marks the row malformed and marker-anchored hash matches."
        return row

    row.evidence_lane = "SOURCE_REVIEW"
    row.secondary_lane = LANE_DO_NOT_REPAIR
    row.confidence = "LOW"
    row.status = "REVIEW_REQUIRED"
    row.recommended_next_action = "manual review before classifier or source action"
    row.source_repair_recommended = False
    row.rationale = "Evidence did not match a known hotfix validation lane."
    return row


def write_csv(path: Path, rows: list[EvidenceLaneRow]) -> None:
    fields = [
        "path", "source_exists", "inventory_row_present", "inventory_malformed",
        "action_class", "header_hash", "marker_count", "marker_anchored_hash",
        "hash_matches_inventory", "marker_is_first_payload",
        "preamble_before_marker_count", "anchored_parse_malformed_count",
        "anchored_parse_field_count", "evidence_lane", "secondary_lane",
        "confidence", "status", "recommended_next_action", "mutation_authorized",
        "source_repair_authorized", "source_repair_recommended", "rationale", "notes",
    ]
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            data = asdict(row)
            for k, v in list(data.items()):
                if isinstance(v, list):
                    data[k] = "; ".join(str(x) for x in v)
            writer.writerow(data)


def write_md(path: Path, csv_path: Path, json_path: Path, summary: dict[str, Any], rows: list[EvidenceLaneRow]) -> None:
    lines = []
    lines.append("# Source Contract Capture Hotfix 002 Evidence Lanes")
    lines.append("")
    lines.append(f"Generated UTC: `{summary['generated_at_utc']}`")
    lines.append("")
    lines.append("Safety class: `REPORT_ONLY / REVIEW_ONLY`")
    lines.append("")
    lines.append("## Verdict")
    lines.append("")
    lines.append("```text")
    lines.append("capture hotfix 002 evidence lanes: GENERATED")
    lines.append(f"validation status: {summary['validation_status']}")
    lines.append("source repairs: NOT AUTHORIZED")
    lines.append("DBF writes: NOT AUTHORIZED")
    lines.append("CMDHELPCHK changes: NOT AUTHORIZED")
    lines.append("HELP DATA rebuild: NOT AUTHORIZED")
    lines.append("```")
    lines.append("")
    lines.append("## Summary counts")
    lines.append("")
    for key in [
        "rows_reviewed",
        "confirmed",
        "capture_review",
        "classifier_review",
        "stale_evidence",
        "do_not_repair",
        "source_repair_recommended",
    ]:
        lines.append(f"- {key}: `{summary.get(key, '')}`")
    lines.append("")
    lines.append("## Evidence lane counts")
    lines.append("")
    lines.append("| Lane | Count |")
    lines.append("|---|---:|")
    for lane, count in summary["evidence_lane_counts"].items():
        lines.append(f"| `{md_escape(lane)}` | {count} |")
    lines.append("")
    lines.append("## Rows")
    lines.append("")
    lines.append("| Path | Lane | Secondary | Confidence | Malformed | Status | Next action |")
    lines.append("|---|---|---|---|---:|---|---|")
    for row in rows:
        lines.append(
            f"| `{md_escape(row.path)}` | `{md_escape(row.evidence_lane)}` | `{md_escape(row.secondary_lane)}` | "
            f"`{md_escape(row.confidence)}` | {row.inventory_malformed} | `{md_escape(row.status)}` | {md_escape(row.recommended_next_action)} |"
        )
    lines.append("")
    lines.append("## Non-mutation confirmation")
    lines.append("")
    for guard in summary["non_mutation_guards"]:
        lines.append(f"- `{guard}`")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    args = parser.parse_args()
    root = Path(args.root).resolve()

    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    inv_rows = index_by_path(read_csv_rows(root / INV_CSV))
    inv_json = read_json(root / INV_JSON)

    rows = [review_one(root, path, inv_rows.get(path, {})) for path in BATCH0]
    rows.sort(key=lambda r: (r.evidence_lane, r.path))

    lane_counts = Counter(row.evidence_lane for row in rows)
    secondary_counts = Counter(row.secondary_lane for row in rows if row.secondary_lane)
    source_repair_recommended = sum(1 for row in rows if row.source_repair_recommended)

    if source_repair_recommended:
        validation_status = "SOURCE_REVIEW_REQUIRED"
    elif lane_counts.get(LANE_CLASSIFIER_REVIEW, 0) or lane_counts.get(LANE_CAPTURE_REVIEW, 0):
        validation_status = "CLASSIFIER_OR_CAPTURE_REVIEW_REQUIRED"
    elif lane_counts.get(LANE_STALE_EVIDENCE, 0):
        validation_status = "STALE_EVIDENCE_REVIEW_REQUIRED"
    else:
        validation_status = "ALL_REVIEWED_ROWS_CONFIRMED"

    summary = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "REVIEW_ONLY_GENERATED",
        "validation_status": validation_status,
        "inventory_probe_version": inv_json.get("summary", {}).get("probe_version", "") if isinstance(inv_json.get("summary", {}), dict) else "",
        "rows_reviewed": len(rows),
        "confirmed": lane_counts.get("CONFIRMED", 0),
        "capture_review": lane_counts.get(LANE_CAPTURE_REVIEW, 0),
        "classifier_review": lane_counts.get(LANE_CLASSIFIER_REVIEW, 0),
        "stale_evidence": lane_counts.get(LANE_STALE_EVIDENCE, 0),
        "do_not_repair": secondary_counts.get(LANE_DO_NOT_REPAIR, 0),
        "source_repair_recommended": source_repair_recommended,
        "evidence_lane_counts": dict(lane_counts.most_common()),
        "secondary_lane_counts": dict(secondary_counts.most_common()),
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

    write_csv(root / OUT_CSV, rows)
    (root / OUT_JSON).write_text(json.dumps({"summary": summary, "rows": [asdict(r) for r in rows]}, indent=2), encoding="utf-8")
    write_md(root / OUT_MD, root / OUT_CSV, root / OUT_JSON, summary, rows)

    print("SelfDoc capture hotfix 002 evidence lanes complete.")
    print(f"Validation status: {validation_status}")
    print(f"Rows reviewed: {len(rows)}")
    print(f"Classifier review: {summary['classifier_review']}")
    print(f"Capture review: {summary['capture_review']}")
    print(f"Stale evidence: {summary['stale_evidence']}")
    print(f"Do not repair: {summary['do_not_repair']}")
    print(f"Wrote: {OUT_MD}")
    print(f"Wrote: {OUT_CSV}")
    print(f"Wrote: {OUT_JSON}")
    print("No source files were edited.")
    print("No DBFs were written.")
    print("CMDHELPCHK was not modified.")
    print("HELP DATA was not rebuilt.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
