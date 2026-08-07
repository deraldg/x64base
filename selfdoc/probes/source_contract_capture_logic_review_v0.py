#!/usr/bin/env python3
"""
source_contract_capture_logic_review_v0.py

REPORT_ONLY / REVIEW_ONLY capture-logic review for source-contract Batch 0.

Run from:
    D:\code\ccode

Reads:
    dottalkpp\docs\generated\reports\source_contract_patch_proposal_draft_v0_1_marker_preserving.csv
    dottalkpp\docs\generated\reports\source_contract_patch_proposal_draft_v0_1_marker_preserving.json
    dottalkpp\docs\generated\reports\source_contract_patch_proposal_review_v0.csv
    dottalkpp\docs\generated\reports\source_contracts_inventory_v1_1.csv
    dottalkpp\docs\generated\reports\source_contracts_inventory_v1_1.json
    Batch 0 source files, read-only

Writes:
    dottalkpp\docs\generated\reports\source_contract_capture_logic_review_v0.md
    dottalkpp\docs\generated\reports\source_contract_capture_logic_review_v0.csv
    dottalkpp\docs\generated\reports\source_contract_capture_logic_review_v0.json

Safety:
    REPORT_ONLY / REVIEW_ONLY
    No source edits.
    No patch files.
    No patch application.
    No repair batch.
    No DBF writes.
    No CMDHELPCHK changes.
    No HELP DATA rebuild.
    No v1.1 default promotion.
    No file moves/deletes.

Purpose:
    Use marker-preserving draft evidence.
    Determine why headers were classified as malformed if source text should remain unchanged.
    Check scanner/capture rules around line-comment blocks, leading blank lines, preamble text,
    marker position, and header boundary detection.
    Investigate cmd_help.cpp hash mismatch.
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


REPORT_DIRS = (
    Path("dottalkpp") / "docs" / "generated" / "reports",
    Path("docs") / "generated" / "reports",
)

DRAFT01_CSV = "source_contract_patch_proposal_draft_v0_1_marker_preserving.csv"
DRAFT01_JSON = "source_contract_patch_proposal_draft_v0_1_marker_preserving.json"
REVIEW_V0_CSV = "source_contract_patch_proposal_review_v0.csv"
INV_CSV = "source_contracts_inventory_v1_1.csv"
INV_JSON = "source_contracts_inventory_v1_1.json"

OUT_MD = "source_contract_capture_logic_review_v0.md"
OUT_CSV = "source_contract_capture_logic_review_v0.csv"
OUT_JSON = "source_contract_capture_logic_review_v0.json"

MARKER = "@dottalk.usage v1"
SAFETY_CLASS = "REPORT_ONLY / REVIEW_ONLY"


@dataclass
class CaptureReviewRow:
    path: str
    source_read_status: str
    inventory_status: str = ""
    inventory_malformed: bool = False
    inventory_header_hash: str = ""
    marker_preserving_hash: str = ""
    current_broad_hash: str = ""
    current_strict_line_hash: str = ""
    exact_marker_line_hash: str = ""
    marker_preserving_matches_inventory: bool = False
    current_broad_matches_inventory: bool = False
    current_strict_line_matches_inventory: bool = False
    exact_marker_line_matches_inventory: bool = False
    marker_count: int = 0
    current_broad_block_count: int = 0
    current_strict_line_block_count: int = 0
    marker_line_number: int = 0
    current_broad_start_line: int = 0
    current_broad_end_line: int = 0
    current_strict_start_line: int = 0
    current_strict_end_line: int = 0
    marker_is_first_payload_line: bool = False
    leading_comment_preamble_lines: int = 0
    leading_blank_lines_in_capture: int = 0
    trailing_blank_lines_in_capture: int = 0
    line_comment_style: bool = False
    block_comment_style: bool = False
    old_review_class: str = ""
    old_review_status: str = ""
    draft01_status: str = ""
    capture_diagnosis: str = ""
    recommended_next_action: str = ""
    priority: str = ""
    source_repair_likely_needed: bool = False
    classifier_capture_fix_likely: bool = False
    inventory_refresh_needed: bool = False
    notes: list[str] = field(default_factory=list)


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


def b(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes", "y"}


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
        if (d / DRAFT01_CSV).is_file():
            return d
    raise SystemExit("Could not find marker-preserving draft report under dottalkpp\\docs\\generated\\reports")


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


def sha(text: str) -> str:
    if not text:
        return ""
    return hashlib.sha256(text.encode("utf-8", errors="surrogateescape")).hexdigest()


def line_number_for_offset(text: str, offset: int) -> int:
    if offset < 0:
        return 0
    return text.count("\n", 0, offset) + 1


def line_bounds_for_offset(text: str, offset: int) -> tuple[int, int, str]:
    start = text.rfind("\n", 0, offset) + 1
    end = text.find("\n", offset)
    if end == -1:
        end = len(text)
    return start, end, text[start:end]


def find_marker_offsets(text: str) -> list[int]:
    return [m.start() for m in re.finditer(re.escape(MARKER), text)]


def broad_capture_current(text: str) -> list[tuple[int, int, str]]:
    """
    Replicates the broad line-comment capture style used by earlier probes,
    including contiguous // lines around the marker.
    """
    blocks = []
    for marker_start in find_marker_offsets(text):
        block_start = text.rfind("/*", 0, marker_start)
        block_end = text.find("*/", marker_start)
        if block_start != -1 and block_end != -1:
            prior_close = text.rfind("*/", 0, marker_start)
            if prior_close < block_start:
                end = block_end + 2
                blocks.append((block_start, end, text[block_start:end]))
                continue

        line_start, line_end, _line = line_bounds_for_offset(text, marker_start)

        start = line_start
        while start > 0:
            prev_end = start - 1
            prev_start = text.rfind("\n", 0, prev_end) + 1
            prev_line = text[prev_start:prev_end]
            if prev_line.lstrip().startswith("//"):
                start = prev_start
            else:
                break

        end = line_end
        while end < len(text):
            next_start = end + 1
            next_end = text.find("\n", next_start)
            if next_end == -1:
                next_end = len(text)
            next_line = text[next_start:next_end]
            if next_line.lstrip().startswith("//"):
                end = next_end
                if next_end == len(text):
                    break
            else:
                break

        blocks.append((start, end, text[start:end]))

    unique = {(s, e): b for s, e, b in blocks}
    return [(s, e, b) for (s, e), b in sorted(unique.items())]


def strict_marker_line_comment_capture(text: str) -> list[tuple[int, int, str]]:
    """
    Stricter proposed capture:
      - marker line is anchor
      - only include contiguous line-comment lines
      - stop at blank lines
      - stop if a previous line-comment looks like a non-contract preamble and marker is not first payload
    This function is diagnostic only.
    """
    blocks = []
    field_re = re.compile(r"^\s*//\s*([A-Za-z][A-Za-z0-9_ -]{0,60})\s*:")
    for marker_start in find_marker_offsets(text):
        line_start, line_end, _line = line_bounds_for_offset(text, marker_start)

        start = line_start
        # Walk up only through adjacent // lines that look like contract fields or the marker.
        while start > 0:
            prev_end = start - 1
            prev_start = text.rfind("\n", 0, prev_end) + 1
            prev_line = text[prev_start:prev_end]
            if not prev_line.lstrip().startswith("//"):
                break
            if MARKER in prev_line or field_re.match(prev_line) or prev_line.strip() == "//":
                start = prev_start
            else:
                # Treat prose/preamble comment above marker as outside contract.
                break

        end = line_end
        while end < len(text):
            next_start = end + 1
            next_end = text.find("\n", next_start)
            if next_end == -1:
                next_end = len(text)
            next_line = text[next_start:next_end]
            if not next_line.lstrip().startswith("//"):
                break
            # After marker, allow all contiguous // lines; they may be continuation text.
            end = next_end
            if next_end == len(text):
                break

        blocks.append((start, end, text[start:end]))

    unique = {(s, e): b for s, e, b in blocks}
    return [(s, e, b) for (s, e), b in sorted(unique.items())]


def exact_marker_line_capture(text: str) -> list[tuple[int, int, str]]:
    blocks = []
    for marker_start in find_marker_offsets(text):
        line_start, line_end, line = line_bounds_for_offset(text, marker_start)
        blocks.append((line_start, line_end, line))
    return blocks


def strip_comment_payload(line: str) -> str:
    s = line.strip()
    if s.startswith("//"):
        return s[2:].strip()
    if s.startswith("*"):
        return s[1:].strip()
    if s.startswith("/*"):
        return s[2:].strip()
    if s.endswith("*/"):
        return s[:-2].strip()
    return s


def payload_lines(block: str) -> list[str]:
    out = []
    for line in block.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        payload = strip_comment_payload(line)
        if payload:
            out.append(payload)
    return out


def marker_is_first_payload(block: str) -> bool:
    lines = payload_lines(block)
    return bool(lines) and MARKER in lines[0]


def leading_preamble_count(block: str) -> int:
    count = 0
    for payload in payload_lines(block):
        if MARKER in payload:
            return count
        count += 1
    return count


def blank_edges(block: str) -> tuple[int, int]:
    lines = block.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    leading = 0
    for line in lines:
        if line.strip() == "":
            leading += 1
        else:
            break
    trailing = 0
    for line in reversed(lines):
        if line.strip() == "":
            trailing += 1
        else:
            break
    return leading, trailing


def index_by_path(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    return {row.get("path", ""): row for row in rows if row.get("path", "")}


def review_one(root: Path, draft_row: dict[str, str], inventory: dict[str, str], old_review: dict[str, str]) -> CaptureReviewRow:
    rel = draft_row.get("path", "")
    source_path = root / rel
    notes = []

    row = CaptureReviewRow(
        path=rel,
        source_read_status="not_read",
        inventory_status=inventory.get("status", ""),
        inventory_malformed=b(inventory.get("malformed", False)),
        inventory_header_hash=inventory.get("header_hash", ""),
        marker_preserving_hash=draft_row.get("computed_header_hash", ""),
        marker_preserving_matches_inventory=b(draft_row.get("hash_matches_inventory", False)),
        old_review_class=old_review.get("review_class", ""),
        old_review_status=old_review.get("review_status", ""),
        draft01_status=draft_row.get("proposal_status", ""),
    )

    if not source_path.is_file():
        row.source_read_status = "missing_source_file"
        row.capture_diagnosis = "BLOCKED_MISSING_SOURCE"
        row.recommended_next_action = "restore_or_locate_source_before_capture_review"
        row.priority = "HIGH"
        notes.append(f"missing source file: {source_path}")
        row.notes = notes
        return row

    try:
        text, read_notes = read_text(source_path)
        notes.extend(read_notes)
    except Exception as exc:
        row.source_read_status = "read_error"
        row.capture_diagnosis = "BLOCKED_READ_ERROR"
        row.recommended_next_action = "resolve_read_error_before_capture_review"
        row.priority = "HIGH"
        row.notes = notes + [f"{type(exc).__name__}: {exc}"]
        return row

    row.source_read_status = "read_ok"
    marker_offsets = find_marker_offsets(text)
    row.marker_count = len(marker_offsets)

    broad = broad_capture_current(text)
    strict = strict_marker_line_comment_capture(text)
    exact = exact_marker_line_capture(text)

    row.current_broad_block_count = len(broad)
    row.current_strict_line_block_count = len(strict)

    if marker_offsets:
        row.marker_line_number = line_number_for_offset(text, marker_offsets[0])

    if broad:
        start, end, block = broad[0]
        row.current_broad_hash = sha(block)
        row.current_broad_matches_inventory = bool(row.inventory_header_hash) and row.current_broad_hash == row.inventory_header_hash
        row.current_broad_start_line = line_number_for_offset(text, start)
        row.current_broad_end_line = line_number_for_offset(text, end)
        row.marker_is_first_payload_line = marker_is_first_payload(block)
        row.leading_comment_preamble_lines = leading_preamble_count(block)
        leading_blank, trailing_blank = blank_edges(block)
        row.leading_blank_lines_in_capture = leading_blank
        row.trailing_blank_lines_in_capture = trailing_blank
        stripped = block.lstrip()
        row.line_comment_style = any(line.lstrip().startswith("//") for line in block.splitlines())
        row.block_comment_style = stripped.startswith("/*")

    if strict:
        start, end, block = strict[0]
        row.current_strict_line_hash = sha(block)
        row.current_strict_line_matches_inventory = bool(row.inventory_header_hash) and row.current_strict_line_hash == row.inventory_header_hash
        row.current_strict_start_line = line_number_for_offset(text, start)
        row.current_strict_end_line = line_number_for_offset(text, end)

    if exact:
        _start, _end, block = exact[0]
        row.exact_marker_line_hash = sha(block)
        row.exact_marker_line_matches_inventory = bool(row.inventory_header_hash) and row.exact_marker_line_hash == row.inventory_header_hash

    # Diagnosis.
    if rel.endswith("cmd_help.cpp") and not row.marker_preserving_matches_inventory:
        row.capture_diagnosis = "INVENTORY_HASH_MISMATCH_REQUIRES_REFRESH_OR_SOURCE_CHANGE_EXPLANATION"
        row.recommended_next_action = "refresh_v1_1_inventory_for_this_file_or_compare_source_timestamp_before_any_patch_path"
        row.priority = "HIGH"
        row.inventory_refresh_needed = True
        row.classifier_capture_fix_likely = False
        notes.append("cmd_help.cpp hash mismatch is treated as freshness/evidence issue, not source repair target")
    elif row.marker_count != 1:
        row.capture_diagnosis = "UNEXPECTED_MARKER_COUNT"
        row.recommended_next_action = "manual_review_marker_count_before_capture_logic_change"
        row.priority = "HIGH"
        row.source_repair_likely_needed = False
        row.classifier_capture_fix_likely = True
    elif row.current_broad_matches_inventory and row.marker_preserving_matches_inventory and not row.marker_is_first_payload_line:
        row.capture_diagnosis = "BROAD_CAPTURE_INCLUDED_PREAMBLE_BEFORE_MARKER"
        row.recommended_next_action = "adjust_capture_logic_to_anchor_marker_as_contract_start_or_allow_preamble_without_malformed_flag"
        row.priority = "HIGH"
        row.classifier_capture_fix_likely = True
        notes.append("source text should likely remain unchanged; broad capture appears too strict")
    elif row.current_broad_matches_inventory and row.marker_preserving_matches_inventory:
        row.capture_diagnosis = "SOURCE_TEXT_STABLE_CAPTURE_RULE_TOO_STRICT"
        row.recommended_next_action = "review malformed criteria for line-comment contract blocks before source repair"
        row.priority = "MEDIUM"
        row.classifier_capture_fix_likely = True
        notes.append("marker-preserving draft proposed no text change and hashes match inventory")
    elif row.current_strict_line_matches_inventory and not row.current_broad_matches_inventory:
        row.capture_diagnosis = "STRICT_CAPTURE_MATCHES_INVENTORY_BROAD_CAPTURE_DIFFERS"
        row.recommended_next_action = "standardize capture strategy and rerun inventory candidate"
        row.priority = "MEDIUM"
        row.classifier_capture_fix_likely = True
    elif not row.marker_preserving_matches_inventory:
        row.capture_diagnosis = "HASH_MISMATCH_GENERAL"
        row.recommended_next_action = "refresh inventory or explain source drift before any proposal path"
        row.priority = "HIGH"
        row.inventory_refresh_needed = True
    else:
        row.capture_diagnosis = "MANUAL_CAPTURE_REVIEW_REQUIRED"
        row.recommended_next_action = "inspect source/proposal/inventory evidence manually"
        row.priority = "MEDIUM"

    row.notes = notes
    return row


def write_csv_report(path: Path, rows: list[CaptureReviewRow]) -> None:
    fields = [
        "path",
        "source_read_status",
        "inventory_status",
        "inventory_malformed",
        "inventory_header_hash",
        "marker_preserving_hash",
        "current_broad_hash",
        "current_strict_line_hash",
        "exact_marker_line_hash",
        "marker_preserving_matches_inventory",
        "current_broad_matches_inventory",
        "current_strict_line_matches_inventory",
        "exact_marker_line_matches_inventory",
        "marker_count",
        "current_broad_block_count",
        "current_strict_line_block_count",
        "marker_line_number",
        "current_broad_start_line",
        "current_broad_end_line",
        "current_strict_start_line",
        "current_strict_end_line",
        "marker_is_first_payload_line",
        "leading_comment_preamble_lines",
        "leading_blank_lines_in_capture",
        "trailing_blank_lines_in_capture",
        "line_comment_style",
        "block_comment_style",
        "old_review_class",
        "old_review_status",
        "draft01_status",
        "capture_diagnosis",
        "recommended_next_action",
        "priority",
        "source_repair_likely_needed",
        "classifier_capture_fix_likely",
        "inventory_refresh_needed",
        "notes",
    ]
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            data = asdict(row)
            for key, value in list(data.items()):
                if isinstance(value, list):
                    data[key] = "; ".join(str(v) for v in value)
            writer.writerow(data)


def write_json_report(path: Path, summary: dict[str, Any], rows: list[CaptureReviewRow]) -> None:
    path.write_text(
        json.dumps({"summary": summary, "capture_review_rows": [asdict(row) for row in rows]}, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def write_md_report(path: Path, csv_path: Path, json_path: Path, summary: dict[str, Any], rows: list[CaptureReviewRow], load_notes: list[str]) -> None:
    lines = []
    lines.append("# Source Contract Capture Logic Review v0")
    lines.append("")
    lines.append(f"Generated UTC: `{summary['generated_at_utc']}`")
    lines.append("")
    lines.append(f"Safety class: `{SAFETY_CLASS}`")
    lines.append("")
    lines.append("## Verdict")
    lines.append("")
    lines.append("```text")
    lines.append("capture logic review: GENERATED")
    lines.append("source repairs: NOT AUTHORIZED")
    lines.append("patch application: NOT AUTHORIZED")
    lines.append("repair batch: NOT CREATED")
    lines.append("DBF writes: NOT AUTHORIZED")
    lines.append("CMDHELPCHK changes: NOT AUTHORIZED")
    lines.append("HELP DATA rebuild: NOT AUTHORIZED")
    lines.append("```")
    lines.append("")
    lines.append("## Scope")
    lines.append("")
    lines.append("This review uses the marker-preserving draft evidence to determine whether Batch 0 needs source repair or capture/parser logic changes. It checks line-comment blocks, marker position, preamble lines, boundary detection, and the cmd_help.cpp hash mismatch.")
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
        "rows_reviewed",
        "classifier_capture_fix_likely",
        "source_repair_likely_needed",
        "inventory_refresh_needed",
        "hash_mismatch_count",
        "cmd_help_hash_mismatch_count",
        "preamble_before_marker_count",
        "unexpected_marker_count",
    ]:
        lines.append(f"- {key}: `{summary.get(key, '')}`")
    lines.append("")
    lines.append("## Diagnosis counts")
    lines.append("")
    lines.append("| Diagnosis | Count |")
    lines.append("|---|---:|")
    for diagnosis, count in summary["capture_diagnosis_counts"].items():
        lines.append(f"| `{md_escape(diagnosis)}` | {count} |")
    lines.append("")
    lines.append("## Review rows")
    lines.append("")
    lines.append("| Path | Diagnosis | Next action | Capture fix likely | Inventory refresh | Source repair likely |")
    lines.append("|---|---|---|---:|---:|---:|")
    for row in rows:
        lines.append(
            f"| `{md_escape(row.path)}` | `{md_escape(row.capture_diagnosis)}` | "
            f"{md_escape(row.recommended_next_action)} | {row.classifier_capture_fix_likely} | "
            f"{row.inventory_refresh_needed} | {row.source_repair_likely_needed} |"
        )
    lines.append("")
    lines.append("## cmd_help.cpp hash mismatch")
    lines.append("")
    cmd_help = [row for row in rows if row.path.endswith("cmd_help.cpp")]
    if cmd_help:
        row = cmd_help[0]
        lines.append(f"- diagnosis: `{row.capture_diagnosis}`")
        lines.append(f"- inventory_hash: `{row.inventory_header_hash}`")
        lines.append(f"- marker_preserving_hash: `{row.marker_preserving_hash}`")
        lines.append(f"- current_broad_hash: `{row.current_broad_hash}`")
        lines.append(f"- recommended_next_action: `{row.recommended_next_action}`")
    else:
        lines.append("cmd_help.cpp was not part of this review set.")
    lines.append("")
    lines.append("## Capture/parser implications")
    lines.append("")
    lines.append("```text")
    lines.append("If marker-preserving evidence shows no source text change is needed, do not repair source.")
    lines.append("Prefer capture/parser rule adjustment over source rewriting when hashes match and marker/visual structure are stable.")
    lines.append("Treat cmd_help.cpp hash mismatch as an evidence freshness issue until explained.")
    lines.append("Do not create patch bundles from capture diagnostics alone.")
    lines.append("```")
    lines.append("")
    lines.append("## Non-mutation confirmation")
    lines.append("")
    for guard in summary["non_mutation_guards"]:
        lines.append(f"- `{md_escape(guard)}`")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Review source contract capture logic for Batch 0.")
    parser.add_argument("--root", default=".")
    parser.add_argument("--report-dir", default=None)
    args = parser.parse_args()

    root = Path(args.root).resolve()
    rd = find_report_dir(root, args.report_dir)

    draft_rows = read_csv_rows(rd / DRAFT01_CSV)
    _draft_json = read_json(rd / DRAFT01_JSON)
    old_review_rows = index_by_path(read_csv_rows(rd / REVIEW_V0_CSV))
    inv_rows = index_by_path(read_csv_rows(rd / INV_CSV))
    _inv_json = read_json(rd / INV_JSON)

    rows = [
        review_one(root, draft, inv_rows.get(draft.get("path", ""), {}), old_review_rows.get(draft.get("path", ""), {}))
        for draft in draft_rows
    ]

    rows.sort(key=lambda row: ({"HIGH": 0, "MEDIUM": 1, "LOW": 2}.get(row.priority, 9), row.path.lower()))

    diagnosis_counts = Counter(row.capture_diagnosis for row in rows)
    hash_mismatch_count = sum(1 for row in rows if row.marker_preserving_hash and not row.marker_preserving_matches_inventory)

    summary = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "REVIEW_ONLY_GENERATED",
        "report_dir": str(rd),
        "rows_reviewed": len(rows),
        "classifier_capture_fix_likely": sum(1 for row in rows if row.classifier_capture_fix_likely),
        "source_repair_likely_needed": sum(1 for row in rows if row.source_repair_likely_needed),
        "inventory_refresh_needed": sum(1 for row in rows if row.inventory_refresh_needed),
        "hash_mismatch_count": hash_mismatch_count,
        "cmd_help_hash_mismatch_count": sum(1 for row in rows if row.path.endswith("cmd_help.cpp") and row.inventory_refresh_needed),
        "preamble_before_marker_count": sum(1 for row in rows if row.leading_comment_preamble_lines > 0),
        "unexpected_marker_count": sum(1 for row in rows if row.marker_count != 1),
        "capture_diagnosis_counts": dict(diagnosis_counts.most_common()),
        "non_mutation_guards": [
            "did_not_edit_source",
            "did_not_apply_patches",
            "did_not_create_patch_files",
            "did_not_create_repair_batch",
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
        f"read marker-preserving draft CSV: {rd / DRAFT01_CSV}",
        f"read marker-preserving draft JSON: {rd / DRAFT01_JSON}" if (rd / DRAFT01_JSON).is_file() else f"marker-preserving draft JSON missing: {rd / DRAFT01_JSON}",
        f"read prior proposal review CSV: {rd / REVIEW_V0_CSV}" if (rd / REVIEW_V0_CSV).is_file() else f"prior proposal review CSV missing: {rd / REVIEW_V0_CSV}",
        f"read v1.1 inventory CSV: {rd / INV_CSV}" if (rd / INV_CSV).is_file() else f"v1.1 inventory CSV missing: {rd / INV_CSV}",
        f"read Batch 0 source files from project root: {root}",
    ]

    write_csv_report(out_csv, rows)
    write_json_report(out_json, summary, rows)
    write_md_report(out_md, out_csv, out_json, summary, rows, load_notes)

    print("SelfDoc source contract capture logic review v0 complete.")
    print(f"Read report directory: {rd}")
    print(f"Rows reviewed: {len(rows)}")
    print(f"Classifier/capture fix likely: {summary['classifier_capture_fix_likely']}")
    print(f"Inventory refresh needed: {summary['inventory_refresh_needed']}")
    print(f"Source repair likely needed: {summary['source_repair_likely_needed']}")
    print(f"Hash mismatches: {summary['hash_mismatch_count']}")
    print(f"Wrote: {out_md}")
    print(f"Wrote: {out_csv}")
    print(f"Wrote: {out_json}")
    print("No source files were edited.")
    print("No patches were applied.")
    print("No patch files were created.")
    print("No repair batch was created.")
    print("No DBFs were written.")
    print("CMDHELPCHK was not modified.")
    print("HELP DATA was not rebuilt.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
