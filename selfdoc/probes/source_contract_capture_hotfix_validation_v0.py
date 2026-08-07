#!/usr/bin/env python3
"""
source_contract_capture_hotfix_validation_v0.py

REPORT_ONLY / REVIEW_ONLY validation pass for the v1.1 capture hotfix.

Run from:
    D:\code\ccode

Reads:
    selfdoc\probes\source_contract_inventory_probe_v1_1.py
    dottalkpp\docs\generated\reports\source_contracts_inventory_v1_1.csv
    dottalkpp\docs\generated\reports\source_contracts_inventory_v1_1.json
    dottalkpp\docs\generated\reports\source_contract_inventory_v1_1_classifier_gap_review.csv
    dottalkpp\docs\generated\reports\source_contract_capture_logic_review_v0.csv
    Batch 0 source files, read-only

Writes:
    dottalkpp\docs\generated\reports\source_contract_capture_hotfix_validation_v0.md
    dottalkpp\docs\generated\reports\source_contract_capture_hotfix_validation_v0.csv
    dottalkpp\docs\generated\reports\source_contract_capture_hotfix_validation_v0.json

Safety:
    REPORT_ONLY / REVIEW_ONLY
    No source edits.
    No probe patching.
    No patch files.
    No repair batch.
    No DBF writes.
    No CMDHELPCHK changes.
    No HELP DATA rebuild.
    No v1.1 default promotion.
    No file moves/deletes.

Purpose:
    Compare the intended capture-hotfix rule against actual v1.1 output.
    Explain why Batch 0 files still have malformed=True.
    Check whether malformed is computed from:
      broad captured header
      marker-anchored payload
      marker position
      preamble count
      trailing blank line
      stale/cached output or hash mismatch
    Recommend the next classifier/probe fix if needed.
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
SAFETY_CLASS = "REPORT_ONLY / REVIEW_ONLY"

REPORT_DIRS = (
    Path("dottalkpp") / "docs" / "generated" / "reports",
    Path("docs") / "generated" / "reports",
)

PROBE_PATH = Path("selfdoc") / "probes" / "source_contract_inventory_probe_v1_1.py"
INV_CSV = "source_contracts_inventory_v1_1.csv"
INV_JSON = "source_contracts_inventory_v1_1.json"
GAP_CSV = "source_contract_inventory_v1_1_classifier_gap_review.csv"
CAPTURE_REVIEW_CSV = "source_contract_capture_logic_review_v0.csv"

OUT_MD = "source_contract_capture_hotfix_validation_v0.md"
OUT_CSV = "source_contract_capture_hotfix_validation_v0.csv"
OUT_JSON = "source_contract_capture_hotfix_validation_v0.json"

BATCH0_FALLBACK = [
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


@dataclass
class ValidationRow:
    path: str
    source_exists: bool
    inventory_row_present: bool
    inventory_malformed: bool = False
    inventory_status: str = ""
    inventory_action_class: str = ""
    inventory_header_hash: str = ""
    marker_count: int = 0

    broad_hash: str = ""
    marker_anchored_hash: str = ""
    exact_marker_line_hash: str = ""
    inventory_matches_broad: bool = False
    inventory_matches_marker_anchored: bool = False
    inventory_matches_exact_marker_line: bool = False

    broad_start_line: int = 0
    broad_end_line: int = 0
    anchored_start_line: int = 0
    anchored_end_line: int = 0
    marker_line_number: int = 0

    broad_preamble_before_marker_count: int = 0
    broad_marker_is_first_payload: bool = False
    anchored_marker_is_first_payload: bool = False
    anchored_trailing_blank_lines: int = 0

    anchored_fields_count: int = 0
    anchored_malformed_count: int = 0
    anchored_malformed_preview: str = ""

    diagnosis: str = ""
    likely_root_cause: str = ""
    recommended_next_action: str = ""
    priority: str = ""

    source_repair_needed: bool = False
    classifier_probe_fix_needed: bool = False
    inventory_refresh_needed: bool = False
    manual_review_needed: bool = False

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


def sha(text: str) -> str:
    if not text:
        return ""
    return hashlib.sha256(text.encode("utf-8", errors="surrogateescape")).hexdigest()


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
    if offset < 0:
        return 0
    return text.count("\n", 0, offset) + 1


def line_bounds(text: str, offset: int) -> tuple[int, int, str]:
    start = text.rfind("\n", 0, offset) + 1
    end = text.find("\n", offset)
    if end == -1:
        end = len(text)
    return start, end, text[start:end]


def marker_offsets(text: str) -> list[int]:
    return [m.start() for m in re.finditer(re.escape(MARKER), text)]


def broad_capture(text: str) -> list[tuple[int, int, str]]:
    blocks: list[tuple[int, int, str]] = []
    for marker_start in marker_offsets(text):
        block_start = text.rfind("/*", 0, marker_start)
        block_end = text.find("*/", marker_start)
        if block_start != -1 and block_end != -1:
            prior_close = text.rfind("*/", 0, marker_start)
            if prior_close < block_start:
                end = block_end + 2
                blocks.append((block_start, end, text[block_start:end]))
                continue

        line_start, line_end, _line = line_bounds(text, marker_start)
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
            break

        blocks.append((start, end, text[start:end]))

    unique = {(s, e): block for s, e, block in blocks}
    return [(s, e, block) for (s, e), block in sorted(unique.items())]


def marker_anchored_capture(text: str) -> list[tuple[int, int, str]]:
    blocks: list[tuple[int, int, str]] = []
    for marker_start in marker_offsets(text):
        block_start = text.rfind("/*", 0, marker_start)
        block_end = text.find("*/", marker_start)
        if block_start != -1 and block_end != -1:
            prior_close = text.rfind("*/", 0, marker_start)
            if prior_close < block_start:
                end = block_end + 2
                blocks.append((block_start, end, text[block_start:end]))
                continue

        line_start, line_end, _line = line_bounds(text, marker_start)
        start = line_start
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

        blocks.append((start, end, text[start:end]))

    unique = {(s, e): block for s, e, block in blocks}
    return [(s, e, block) for (s, e), block in sorted(unique.items())]


def exact_marker_line_capture(text: str) -> list[tuple[int, int, str]]:
    blocks = []
    for off in marker_offsets(text):
        start, end, line = line_bounds(text, off)
        blocks.append((start, end, line))
    return blocks


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


def payload_lines(block: str) -> list[str]:
    out = []
    for raw in block.splitlines():
        line = strip_comment_prefix(raw)
        if line:
            out.append(line)
    return out


def marker_first_payload(block: str) -> bool:
    lines = payload_lines(block)
    return bool(lines) and MARKER in lines[0]


def preamble_before_marker_count(block: str) -> int:
    count = 0
    for line in payload_lines(block):
        if MARKER in line:
            return count
        count += 1
    return count


def trailing_blank_lines(block: str) -> int:
    lines = block.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    count = 0
    for line in reversed(lines):
        if line.strip() == "":
            count += 1
        else:
            break
    return count


def parse_fields_marker_anchored(block: str) -> tuple[dict[str, list[str]], list[str]]:
    fields: dict[str, list[str]] = {}
    malformed: list[str] = []
    seen_marker = False

    for raw in block.splitlines():
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


def index_by_path(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    return {row.get("path", "").replace("\\", "/"): row for row in rows if row.get("path", "")}


def batch_paths(capture_review_rows: list[dict[str, str]], inventory_rows: dict[str, dict[str, str]]) -> list[str]:
    paths = []
    for row in capture_review_rows:
        path = row.get("path", "").replace("\\", "/")
        if path:
            paths.append(path)
    if not paths:
        paths = list(BATCH0_FALLBACK)

    # Keep cmd_help.cpp even if not malformed because it is the evidence case.
    unique = []
    seen = set()
    for path in paths:
        if path and path not in seen:
            unique.append(path)
            seen.add(path)
    return unique


def inspect_probe(root: Path) -> dict[str, Any]:
    path = root / PROBE_PATH
    if not path.is_file():
        return {
            "probe_present": False,
            "probe_version_line": "",
            "has_anchor_comment": False,
            "has_parse_seen_marker": False,
            "has_upward_walk_in_find_contract_blocks": False,
            "diagnosis": "probe file missing",
        }

    text = path.read_text(encoding="utf-8", errors="replace")
    version_match = re.search(r'PROBE_VERSION\s*=\s*"([^"]+)"', text)
    version = version_match.group(1) if version_match else ""

    # The hotfix should anchor at marker line and parse after seen_marker.
    has_anchor_comment = "anchor at marker line" in text or "marker line is the contract start" in text
    has_parse_seen_marker = "seen_marker" in text and "if not seen_marker" in text
    has_upward_walk = "while start > 0" in text and "prev_line.lstrip().startswith" in text

    if has_anchor_comment and has_parse_seen_marker and not has_upward_walk:
        diagnosis = "probe appears to contain capture hotfix"
    elif has_anchor_comment and has_parse_seen_marker and has_upward_walk:
        diagnosis = "probe has hotfix markers but may still contain upward preamble walk elsewhere"
    else:
        diagnosis = "probe may not contain full capture hotfix"

    return {
        "probe_present": True,
        "probe_version_line": version,
        "has_anchor_comment": has_anchor_comment,
        "has_parse_seen_marker": has_parse_seen_marker,
        "has_upward_walk_in_find_contract_blocks": has_upward_walk,
        "diagnosis": diagnosis,
    }


def review_one(root: Path, path: str, inv: dict[str, str]) -> ValidationRow:
    source = root / path
    row = ValidationRow(
        path=path,
        source_exists=source.is_file(),
        inventory_row_present=bool(inv),
        inventory_malformed=b(inv.get("malformed", False)),
        inventory_status=inv.get("status", ""),
        inventory_action_class=inv.get("action_class", ""),
        inventory_header_hash=inv.get("header_hash", ""),
    )

    if not source.is_file():
        row.diagnosis = "SOURCE_FILE_MISSING"
        row.likely_root_cause = "source file not found"
        row.recommended_next_action = "locate source before validating capture"
        row.priority = "HIGH"
        row.manual_review_needed = True
        return row

    text, notes = read_text(source)
    row.notes.extend(notes)

    offsets = marker_offsets(text)
    row.marker_count = len(offsets)
    if offsets:
        row.marker_line_number = line_number_for_offset(text, offsets[0])

    broad = broad_capture(text)
    anchored = marker_anchored_capture(text)
    exact = exact_marker_line_capture(text)

    if broad:
        start, end, block = broad[0]
        row.broad_hash = sha(block)
        row.inventory_matches_broad = bool(row.inventory_header_hash) and row.inventory_header_hash == row.broad_hash
        row.broad_start_line = line_number_for_offset(text, start)
        row.broad_end_line = line_number_for_offset(text, end)
        row.broad_preamble_before_marker_count = preamble_before_marker_count(block)
        row.broad_marker_is_first_payload = marker_first_payload(block)

    if anchored:
        start, end, block = anchored[0]
        row.marker_anchored_hash = sha(block)
        row.inventory_matches_marker_anchored = bool(row.inventory_header_hash) and row.inventory_header_hash == row.marker_anchored_hash
        row.anchored_start_line = line_number_for_offset(text, start)
        row.anchored_end_line = line_number_for_offset(text, end)
        row.anchored_marker_is_first_payload = marker_first_payload(block)
        row.anchored_trailing_blank_lines = trailing_blank_lines(block)
        fields, malformed = parse_fields_marker_anchored(block)
        row.anchored_fields_count = len(fields)
        row.anchored_malformed_count = len(malformed)
        row.anchored_malformed_preview = "; ".join(malformed[:5])

    if exact:
        _start, _end, block = exact[0]
        row.exact_marker_line_hash = sha(block)
        row.inventory_matches_exact_marker_line = bool(row.inventory_header_hash) and row.inventory_header_hash == row.exact_marker_line_hash

    # Diagnosis.
    if path.endswith("cmd_help.cpp") and not row.inventory_matches_marker_anchored:
        row.diagnosis = "CMD_HELP_HASH_MISMATCH_STILL_UNEXPLAINED"
        row.likely_root_cause = "inventory hash does not match current marker-anchored capture"
        row.recommended_next_action = "refresh inventory evidence or compare source timestamp/history before any patch path"
        row.priority = "HIGH"
        row.inventory_refresh_needed = True
        return row

    if row.marker_count != 1:
        row.diagnosis = "UNEXPECTED_MARKER_COUNT"
        row.likely_root_cause = "scanner cannot safely choose a single contract block"
        row.recommended_next_action = "manual marker-count review before classifier patch"
        row.priority = "HIGH"
        row.manual_review_needed = True
        return row

    if row.inventory_malformed and row.inventory_matches_broad and not row.inventory_matches_marker_anchored:
        row.diagnosis = "RERUN_USED_BROAD_CAPTURE_NOT_ANCHORED_CAPTURE"
        row.likely_root_cause = "v1.1 output still hashes the broad preamble-including block"
        row.recommended_next_action = "patch or verify find_contract_blocks replacement in v1.1 probe; rerun inventory"
        row.priority = "HIGH"
        row.classifier_probe_fix_needed = True
        return row

    if row.inventory_malformed and row.inventory_matches_marker_anchored and row.anchored_malformed_count == 0:
        row.diagnosis = "MALFORMED_FLAG_COMPUTED_OUTSIDE_MARKER_ANCHORED_PARSE"
        row.likely_root_cause = "malformed flag is stale or computed from another rule after field parsing"
        row.recommended_next_action = "inspect classify_file malformed assignment and shape-review criteria in v1.1 probe"
        row.priority = "HIGH"
        row.classifier_probe_fix_needed = True
        return row

    if row.inventory_malformed and row.inventory_matches_marker_anchored and row.anchored_malformed_count > 0:
        row.diagnosis = "ANCHOR_CAPTURE_STILL_HAS_MALFORMED_PAYLOAD_AFTER_MARKER"
        row.likely_root_cause = "lines after marker are not field lines and occur before any parsed field"
        row.recommended_next_action = "review whether post-marker prose should be notes/continuation or whether source contract shape is actually malformed"
        row.priority = "HIGH"
        row.manual_review_needed = True
        return row

    if row.inventory_malformed and not row.inventory_matches_broad and not row.inventory_matches_marker_anchored:
        row.diagnosis = "INVENTORY_HASH_MATCHES_NEITHER_BROAD_NOR_ANCHORED"
        row.likely_root_cause = "stale report, source changed, or capture algorithm differs from validation model"
        row.recommended_next_action = "refresh inventory and compare probe implementation before any patch path"
        row.priority = "HIGH"
        row.inventory_refresh_needed = True
        return row

    if not row.inventory_malformed and row.inventory_matches_marker_anchored:
        row.diagnosis = "CAPTURE_HOTFIX_VALIDATED_FOR_FILE"
        row.likely_root_cause = "none"
        row.recommended_next_action = "no source repair; keep classifier result"
        row.priority = "LOW"
        return row

    row.diagnosis = "MANUAL_VALIDATION_REQUIRED"
    row.likely_root_cause = "validation did not match a known evidence pattern"
    row.recommended_next_action = "inspect row manually before patching classifier/probe"
    row.priority = "MEDIUM"
    row.manual_review_needed = True
    return row


def write_csv_report(path: Path, rows: list[ValidationRow]) -> None:
    fields = [
        "path",
        "source_exists",
        "inventory_row_present",
        "inventory_malformed",
        "inventory_status",
        "inventory_action_class",
        "inventory_header_hash",
        "marker_count",
        "broad_hash",
        "marker_anchored_hash",
        "exact_marker_line_hash",
        "inventory_matches_broad",
        "inventory_matches_marker_anchored",
        "inventory_matches_exact_marker_line",
        "broad_start_line",
        "broad_end_line",
        "anchored_start_line",
        "anchored_end_line",
        "marker_line_number",
        "broad_preamble_before_marker_count",
        "broad_marker_is_first_payload",
        "anchored_marker_is_first_payload",
        "anchored_trailing_blank_lines",
        "anchored_fields_count",
        "anchored_malformed_count",
        "anchored_malformed_preview",
        "diagnosis",
        "likely_root_cause",
        "recommended_next_action",
        "priority",
        "source_repair_needed",
        "classifier_probe_fix_needed",
        "inventory_refresh_needed",
        "manual_review_needed",
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


def write_json_report(path: Path, summary: dict[str, Any], rows: list[ValidationRow]) -> None:
    path.write_text(
        json.dumps({"summary": summary, "validation_rows": [asdict(row) for row in rows]}, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def write_md_report(path: Path, csv_path: Path, json_path: Path, summary: dict[str, Any], rows: list[ValidationRow], load_notes: list[str]) -> None:
    lines = []
    lines.append("# Source Contract Capture Hotfix Validation v0")
    lines.append("")
    lines.append(f"Generated UTC: `{summary['generated_at_utc']}`")
    lines.append("")
    lines.append(f"Safety class: `{SAFETY_CLASS}`")
    lines.append("")
    lines.append("## Verdict")
    lines.append("")
    lines.append("```text")
    lines.append("capture hotfix validation: GENERATED")
    lines.append(f"validation status: {summary['validation_status']}")
    lines.append("source repairs: NOT AUTHORIZED")
    lines.append("probe patching: NOT PERFORMED")
    lines.append("DBF writes: NOT AUTHORIZED")
    lines.append("CMDHELPCHK changes: NOT AUTHORIZED")
    lines.append("HELP DATA rebuild: NOT AUTHORIZED")
    lines.append("```")
    lines.append("")
    lines.append("## Scope")
    lines.append("")
    lines.append("This report compares the intended marker-anchored capture rule against actual v1.1 inventory output. It explains why Batch 0 rows may still have `malformed=True`. It does not edit source and does not patch the probe.")
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
    lines.append("## Probe inspection")
    lines.append("")
    for key, value in summary["probe_inspection"].items():
        lines.append(f"- {key}: `{md_escape(value)}`")
    lines.append("")
    lines.append("## Summary counts")
    lines.append("")
    for key in [
        "rows_reviewed",
        "inventory_malformed_rows",
        "inventory_matches_broad_count",
        "inventory_matches_marker_anchored_count",
        "classifier_probe_fix_needed",
        "inventory_refresh_needed",
        "manual_review_needed",
        "source_repair_needed",
    ]:
        lines.append(f"- {key}: `{summary.get(key, '')}`")
    lines.append("")
    lines.append("## Diagnosis counts")
    lines.append("")
    lines.append("| Diagnosis | Count |")
    lines.append("|---|---:|")
    for diagnosis, count in summary["diagnosis_counts"].items():
        lines.append(f"| `{md_escape(diagnosis)}` | {count} |")
    lines.append("")
    lines.append("## Validation rows")
    lines.append("")
    lines.append("| Path | Malformed | Broad match | Anchored match | Anchored malformed | Diagnosis | Next action |")
    lines.append("|---|---:|---:|---:|---:|---|---|")
    for row in rows:
        lines.append(
            f"| `{md_escape(row.path)}` | {row.inventory_malformed} | {row.inventory_matches_broad} | "
            f"{row.inventory_matches_marker_anchored} | {row.anchored_malformed_count} | "
            f"`{md_escape(row.diagnosis)}` | {md_escape(row.recommended_next_action)} |"
        )
    lines.append("")
    lines.append("## Likely next action")
    lines.append("")
    lines.append(summary["recommended_next_overall_action"])
    lines.append("")
    lines.append("## Non-mutation confirmation")
    lines.append("")
    for guard in summary["non_mutation_guards"]:
        lines.append(f"- `{md_escape(guard)}`")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate source contract v1.1 capture hotfix.")
    parser.add_argument("--root", default=".")
    parser.add_argument("--report-dir", default=None)
    args = parser.parse_args()

    root = Path(args.root).resolve()
    rd = find_report_dir(root, args.report_dir)

    inventory = index_by_path(read_csv_rows(rd / INV_CSV))
    inv_json = read_json(rd / INV_JSON)
    gap_rows = read_csv_rows(rd / GAP_CSV)
    capture_review_rows = read_csv_rows(rd / CAPTURE_REVIEW_CSV)

    paths = batch_paths(capture_review_rows, inventory)
    rows = [review_one(root, path, inventory.get(path, {})) for path in paths]
    rows.sort(key=lambda row: ({"HIGH": 0, "MEDIUM": 1, "LOW": 2}.get(row.priority, 9), row.path.lower()))

    diagnosis_counts = Counter(row.diagnosis for row in rows)
    probe_info = inspect_probe(root)

    classifier_fix_needed = sum(1 for row in rows if row.classifier_probe_fix_needed)
    inventory_refresh_needed = sum(1 for row in rows if row.inventory_refresh_needed)
    manual_review_needed = sum(1 for row in rows if row.manual_review_needed)
    source_repair_needed = sum(1 for row in rows if row.source_repair_needed)

    if classifier_fix_needed:
        validation_status = "NOT_PASSED_CLASSIFIER_PROBE_FIX_NEEDED"
        recommended_next = "Patch only the report-only v1.1 probe capture/classification logic, then rerun inventory and this validation. Do not edit source."
    elif inventory_refresh_needed and not classifier_fix_needed:
        validation_status = "PARTIAL_PASS_INVENTORY_REFRESH_NEEDED"
        recommended_next = "Refresh inventory/evidence for hash-mismatch rows before any promotion or patch path. Do not edit source."
    elif manual_review_needed:
        validation_status = "PARTIAL_PASS_MANUAL_REVIEW_NEEDED"
        recommended_next = "Manual review remains for rows where anchored payload is actually malformed or marker evidence is ambiguous."
    else:
        validation_status = "PASSED_FOR_REVIEWED_ROWS"
        recommended_next = "Capture hotfix appears validated for reviewed rows. Continue promotion review, not source repair."

    summary = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "REVIEW_ONLY_GENERATED",
        "validation_status": validation_status,
        "report_dir": str(rd),
        "probe_inspection": probe_info,
        "inventory_total_records": inv_json.get("summary", {}).get("total_records", "") if isinstance(inv_json.get("summary", {}), dict) else "",
        "gap_rows": len(gap_rows),
        "rows_reviewed": len(rows),
        "inventory_malformed_rows": sum(1 for row in rows if row.inventory_malformed),
        "inventory_matches_broad_count": sum(1 for row in rows if row.inventory_matches_broad),
        "inventory_matches_marker_anchored_count": sum(1 for row in rows if row.inventory_matches_marker_anchored),
        "classifier_probe_fix_needed": classifier_fix_needed,
        "inventory_refresh_needed": inventory_refresh_needed,
        "manual_review_needed": manual_review_needed,
        "source_repair_needed": source_repair_needed,
        "diagnosis_counts": dict(diagnosis_counts.most_common()),
        "recommended_next_overall_action": recommended_next,
        "non_mutation_guards": [
            "did_not_edit_source",
            "did_not_patch_probe",
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
        f"read probe source: {root / PROBE_PATH}",
        f"read v1.1 inventory CSV: {rd / INV_CSV}",
        f"read v1.1 inventory JSON: {rd / INV_JSON}" if (rd / INV_JSON).is_file() else f"v1.1 inventory JSON missing: {rd / INV_JSON}",
        f"read classifier gap review CSV: {rd / GAP_CSV}" if (rd / GAP_CSV).is_file() else f"classifier gap review CSV missing: {rd / GAP_CSV}",
        f"read capture logic review CSV: {rd / CAPTURE_REVIEW_CSV}" if (rd / CAPTURE_REVIEW_CSV).is_file() else f"capture logic review CSV missing, used fallback Batch 0 list: {rd / CAPTURE_REVIEW_CSV}",
        f"read Batch 0 source files from project root: {root}",
    ]

    write_csv_report(out_csv, rows)
    write_json_report(out_json, summary, rows)
    write_md_report(out_md, out_csv, out_json, summary, rows, load_notes)

    print("SelfDoc source contract capture hotfix validation v0 complete.")
    print(f"Read report directory: {rd}")
    print(f"Validation status: {validation_status}")
    print(f"Rows reviewed: {len(rows)}")
    print(f"Classifier/probe fix needed: {classifier_fix_needed}")
    print(f"Inventory refresh needed: {inventory_refresh_needed}")
    print(f"Manual review needed: {manual_review_needed}")
    print(f"Source repair needed: {source_repair_needed}")
    print(f"Wrote: {out_md}")
    print(f"Wrote: {out_csv}")
    print(f"Wrote: {out_json}")
    print("No source files were edited.")
    print("No probe patch was applied.")
    print("No patches were applied.")
    print("No patch files were created.")
    print("No repair batch was created.")
    print("No DBFs were written.")
    print("CMDHELPCHK was not modified.")
    print("HELP DATA was not rebuilt.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
