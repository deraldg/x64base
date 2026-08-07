#!/usr/bin/env python3
"""
source_contract_inventory_probe.py

SelfDoc source contract inventory probe.

Safety class:
    REPORT_ONLY

Run from the DotTalk++ project root:

    cd D:\code\ccode
    python selfdoc\probes\source_contract_inventory_probe.py

This repository layout is expected:

    D:\code\ccode\src
    D:\code\ccode\include
    D:\code\ccode\dottalkpp

Writes report outputs only:

    dottalkpp\docs\generated\reports\source_contracts_inventory.md
    dottalkpp\docs\generated\reports\source_contracts_inventory.csv
    dottalkpp\docs\generated\reports\source_contracts_inventory.json

Safety rules:
    - scan source only
    - do not edit source
    - do not write DBFs
    - do not modify CMDHELPCHK
    - do not repair headers
    - do not rebuild HELP DATA
    - preserve canonical @dottalk.usage v1 header text
    - hash header text
    - report malformed/missing fields honestly
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Optional


SAFETY_CLASS = "REPORT_ONLY"
MARKER = "@dottalk.usage v1"

DEFAULT_SCAN_DIRS = ("src", "include")
SOURCE_SUFFIXES = {
    ".c",
    ".cc",
    ".cpp",
    ".cxx",
    ".h",
    ".hh",
    ".hpp",
    ".hxx",
}

REPORT_DIR = Path("dottalkpp") / "docs" / "generated" / "reports"
MD_REPORT = REPORT_DIR / "source_contracts_inventory.md"
CSV_REPORT = REPORT_DIR / "source_contracts_inventory.csv"
JSON_REPORT = REPORT_DIR / "source_contracts_inventory.json"

KNOWN_FIELDS = {
    "command",
    "commands",
    "owner",
    "family",
    "category",
    "summary",
    "syntax",
    "usage",
    "examples",
    "example",
    "notes",
    "note",
    "related",
    "status",
    "source",
    "safety",
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

RECOMMENDED_FIELDS = ("command", "summary", "syntax")


@dataclass
class ContractRecord:
    path: str
    size_bytes: int
    has_contract: bool
    contract_count: int
    status: str
    header_sha256: str = ""
    header_start_line: int = 0
    header_end_line: int = 0
    header_line_count: int = 0
    fields_present: list[str] = field(default_factory=list)
    missing_recommended_fields: list[str] = field(default_factory=list)
    malformed_lines: list[str] = field(default_factory=list)
    unknown_fields: list[str] = field(default_factory=list)
    command_names: list[str] = field(default_factory=list)
    escrow_candidate: bool = False
    notes: list[str] = field(default_factory=list)
    header_text: str = ""


def is_source_file(path: Path) -> bool:
    return path.is_file() and path.suffix.lower() in SOURCE_SUFFIXES


def iter_source_files(root: Path, scan_dirs: Iterable[str]) -> Iterable[Path]:
    for rel in scan_dirs:
        base = root / rel
        if not base.exists():
            continue
        if not base.is_dir():
            continue
        for path in base.rglob("*"):
            if is_source_file(path):
                yield path


def read_text_lossless_enough(path: Path) -> tuple[str, list[str]]:
    notes: list[str] = []
    raw = path.read_bytes()

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
    """Return exact source slices containing each @dottalk.usage v1 contract."""

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

        line_start = text.rfind("\n", 0, marker_start) + 1
        line_end = text.find("\n", marker_start)
        if line_end == -1:
            line_end = len(text)

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

    unique: dict[tuple[int, int], str] = {}
    for start, end, block in blocks:
        unique[(start, end)] = block
    return [(start, end, block) for (start, end), block in sorted(unique.items())]


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


def parse_fields(header_text: str) -> tuple[dict[str, list[str]], list[str], list[str]]:
    fields: dict[str, list[str]] = {}
    malformed: list[str] = []
    unknown: list[str] = []

    for raw_line in header_text.splitlines():
        line = strip_comment_prefix(raw_line)
        if not line:
            continue
        if MARKER in line:
            continue

        if set(line) <= {"-", "=", "_"}:
            continue

        match = re.match(r"^([A-Za-z][A-Za-z0-9_ -]{0,40})\s*:\s*(.*)$", line)
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

        if key not in KNOWN_FIELDS:
            unknown.append(key)

    return fields, malformed, sorted(set(unknown))


def command_names_from_fields(fields: dict[str, list[str]]) -> list[str]:
    names: list[str] = []
    for key in ("command", "commands", "owner"):
        for value in fields.get(key, []):
            parts = re.split(r"[,;|]", value)
            for part in parts:
                candidate = part.strip()
                if candidate:
                    names.append(candidate)
    return sorted(set(names))


def classify_record(path: Path, root: Path) -> ContractRecord:
    rel = path.relative_to(root).as_posix()
    size = path.stat().st_size

    try:
        text, notes = read_text_lossless_enough(path)
    except Exception as exc:
        return ContractRecord(
            path=rel,
            size_bytes=size,
            has_contract=False,
            contract_count=0,
            status="read_error",
            notes=[f"read_error={type(exc).__name__}: {exc}"],
            escrow_candidate=True,
        )

    blocks = find_contract_blocks(text)

    if not blocks:
        return ContractRecord(
            path=rel,
            size_bytes=size,
            has_contract=False,
            contract_count=0,
            status="missing_contract",
            escrow_candidate=True,
            notes=notes,
        )

    status = "multiple_contracts" if len(blocks) > 1 else "ok"

    start, end, header = blocks[0]
    fields_map, malformed, unknown = parse_fields(header)

    fields_present = sorted(fields_map.keys())
    missing = [name for name in RECOMMENDED_FIELDS if name not in fields_map]

    if malformed:
        status = "malformed"
    elif missing:
        status = "missing_recommended_fields"
    elif unknown and status == "ok":
        status = "unknown_fields"

    if len(blocks) > 1 and status == "ok":
        status = "multiple_contracts"

    header_bytes = header.encode("utf-8", errors="surrogateescape")
    digest = hashlib.sha256(header_bytes).hexdigest()

    start_line = line_number_for_offset(text, start)
    end_line = line_number_for_offset(text, end)

    escrow = bool(missing or malformed or len(blocks) > 1 or unknown)

    return ContractRecord(
        path=rel,
        size_bytes=size,
        has_contract=True,
        contract_count=len(blocks),
        status=status,
        header_sha256=digest,
        header_start_line=start_line,
        header_end_line=end_line,
        header_line_count=max(1, end_line - start_line + 1),
        fields_present=fields_present,
        missing_recommended_fields=missing,
        malformed_lines=malformed,
        unknown_fields=unknown,
        command_names=command_names_from_fields(fields_map),
        escrow_candidate=escrow,
        notes=notes,
        header_text=header,
    )


def summarize(records: list[ContractRecord], root: Path, scan_dirs: tuple[str, ...]) -> dict[str, object]:
    status_counts: dict[str, int] = {}
    for rec in records:
        status_counts[rec.status] = status_counts.get(rec.status, 0) + 1

    with_contract = sum(1 for rec in records if rec.has_contract)
    missing_contract = sum(1 for rec in records if not rec.has_contract)
    escrow = sum(1 for rec in records if rec.escrow_candidate)

    return {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "repo_root": str(root),
        "safety_class": SAFETY_CLASS,
        "marker": MARKER,
        "scan_dirs": list(scan_dirs),
        "source_suffixes": sorted(SOURCE_SUFFIXES),
        "recommended_fields": list(RECOMMENDED_FIELDS),
        "total_source_files": len(records),
        "files_with_contract": with_contract,
        "files_missing_contract": missing_contract,
        "escrow_candidate_count": escrow,
        "status_counts": dict(sorted(status_counts.items())),
        "outputs": {
            "markdown": str(MD_REPORT),
            "csv": str(CSV_REPORT),
            "json": str(JSON_REPORT),
        },
        "non_mutation_guards": [
            "did_not_edit_source",
            "did_not_write_dbfs",
            "did_not_modify_cmdhelpchk",
            "did_not_rebuild_help_data",
            "did_not_repair_headers",
        ],
    }


def write_json(records: list[ContractRecord], summary: dict[str, object]) -> None:
    payload = {
        "summary": summary,
        "records": [asdict(rec) for rec in records],
    }
    JSON_REPORT.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def write_csv(records: list[ContractRecord]) -> None:
    fieldnames = [
        "path",
        "size_bytes",
        "has_contract",
        "contract_count",
        "status",
        "header_sha256",
        "header_start_line",
        "header_end_line",
        "header_line_count",
        "fields_present",
        "missing_recommended_fields",
        "malformed_lines",
        "unknown_fields",
        "command_names",
        "escrow_candidate",
        "notes",
    ]

    with CSV_REPORT.open("w", newline="", encoding="utf-8") as report:
        writer = csv.DictWriter(report, fieldnames=fieldnames)
        writer.writeheader()
        for rec in records:
            row = asdict(rec)
            row.pop("header_text", None)
            for key, value in list(row.items()):
                if isinstance(value, list):
                    row[key] = "; ".join(str(item) for item in value)
            writer.writerow(row)


def md_escape(text: object) -> str:
    value = str(text)
    return value.replace("|", "\\|").replace("\n", " ")


def write_markdown(records: list[ContractRecord], summary: dict[str, object]) -> None:
    lines: list[str] = []
    lines.append("# Source Contracts Inventory")
    lines.append("")
    lines.append(f"Generated UTC: `{summary['generated_at_utc']}`")
    lines.append("")
    lines.append("Safety class: `REPORT_ONLY`")
    lines.append("")
    lines.append("## Scope")
    lines.append("")
    lines.append("This report inventories source usage contracts only. It does not edit source, write DBFs, modify CMDHELPCHK, repair headers, or rebuild HELP DATA.")
    lines.append("")
    lines.append("Scanned source roots:")
    lines.append("")
    for scan_dir in summary["scan_dirs"]:  # type: ignore[index]
        lines.append(f"- `{scan_dir}`")
    lines.append("")
    lines.append(f"Contract marker: `{MARKER}`")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- Total source files: `{summary['total_source_files']}`")
    lines.append(f"- Files with contract: `{summary['files_with_contract']}`")
    lines.append(f"- Files missing contract: `{summary['files_missing_contract']}`")
    lines.append(f"- Escrow candidates: `{summary['escrow_candidate_count']}`")
    lines.append("")
    lines.append("### Status counts")
    lines.append("")
    lines.append("| Status | Count |")
    lines.append("|---|---:|")
    status_counts = summary["status_counts"]
    if isinstance(status_counts, dict):
        for status, count in status_counts.items():
            lines.append(f"| `{md_escape(status)}` | {count} |")
    lines.append("")
    lines.append("## Recommended fields")
    lines.append("")
    for name in RECOMMENDED_FIELDS:
        lines.append(f"- `{name}`")
    lines.append("")
    lines.append("Missing recommended fields are reported honestly as escrow candidates. The probe does not repair them.")
    lines.append("")
    lines.append("## Inventory")
    lines.append("")
    lines.append("| Path | Status | Contracts | Header SHA-256 | Lines | Fields | Missing recommended | Unknown fields | Escrow |")
    lines.append("|---|---|---:|---|---:|---|---|---|---:|")

    for rec in records:
        line_range = ""
        if rec.header_start_line:
            line_range = f"{rec.header_start_line}-{rec.header_end_line}"
        lines.append(
            "| "
            f"`{md_escape(rec.path)}` | "
            f"`{md_escape(rec.status)}` | "
            f"{rec.contract_count} | "
            f"`{md_escape(rec.header_sha256[:16] if rec.header_sha256 else '')}` | "
            f"{md_escape(line_range)} | "
            f"{md_escape(', '.join(rec.fields_present))} | "
            f"{md_escape(', '.join(rec.missing_recommended_fields))} | "
            f"{md_escape(', '.join(rec.unknown_fields))} | "
            f"{'Y' if rec.escrow_candidate else 'N'} |"
        )

    escrow_records = [rec for rec in records if rec.escrow_candidate]
    lines.append("")
    lines.append("## Escrow candidates")
    lines.append("")
    if not escrow_records:
        lines.append("No escrow candidates found.")
    else:
        lines.append("| Path | Reason | Notes |")
        lines.append("|---|---|---|")
        for rec in escrow_records:
            reasons: list[str] = []
            if not rec.has_contract:
                reasons.append("missing contract")
            if rec.contract_count > 1:
                reasons.append("multiple contracts")
            if rec.missing_recommended_fields:
                reasons.append("missing recommended: " + ", ".join(rec.missing_recommended_fields))
            if rec.malformed_lines:
                reasons.append("malformed lines")
            if rec.unknown_fields:
                reasons.append("unknown fields: " + ", ".join(rec.unknown_fields))
            if rec.status == "read_error":
                reasons.append("read error")
            lines.append(f"| `{md_escape(rec.path)}` | {md_escape('; '.join(reasons))} | {md_escape('; '.join(rec.notes))} |")

    lines.append("")
    lines.append("## Header hashing")
    lines.append("")
    lines.append("Header SHA-256 values are computed over the exact captured `@dottalk.usage v1` comment text using round-trippable decoding. The probe preserves the captured header text in the JSON report and does not normalize it for hashing.")
    lines.append("")
    lines.append("## Outputs")
    lines.append("")
    lines.append(f"- `{MD_REPORT}`")
    lines.append(f"- `{CSV_REPORT}`")
    lines.append(f"- `{JSON_REPORT}`")
    lines.append("")
    lines.append("## Non-mutation confirmation")
    lines.append("")
    guards = summary["non_mutation_guards"]
    if isinstance(guards, list):
        for guard in guards:
            lines.append(f"- `{guard}`")

    MD_REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Inventory DotTalk++ source usage contracts.")
    parser.add_argument(
        "--root",
        default=".",
        help="Project root. Default: current directory, normally D:\\code\\ccode.",
    )
    parser.add_argument(
        "--scan-dir",
        action="append",
        dest="scan_dirs",
        help="Source directory to scan. May be repeated. Default: src and include.",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress summary output.",
    )
    return parser.parse_args(argv)


def preflight(root: Path, scan_dirs: tuple[str, ...]) -> list[str]:
    warnings: list[str] = []

    if not (root / "src").is_dir():
        warnings.append("expected source directory missing: src")
    if not (root / "include").is_dir():
        warnings.append("expected include directory missing: include")
    if not (root / "dottalkpp").is_dir():
        warnings.append("expected runtime/data subtree missing: dottalkpp")

    for directory in scan_dirs:
        if not (root / directory).is_dir():
            warnings.append(f"scan directory missing: {directory}")

    return warnings


def main(argv: Optional[list[str]] = None) -> int:
    args = parse_args(argv)
    root = Path(args.root).resolve()
    scan_dirs = tuple(args.scan_dirs) if args.scan_dirs else DEFAULT_SCAN_DIRS

    warnings = preflight(root, scan_dirs)
    for warning in warnings:
        print(f"WARNING: {warning}", file=sys.stderr)

    files = sorted(iter_source_files(root, scan_dirs), key=lambda source_path: source_path.as_posix().lower())
    records = [classify_record(path, root) for path in files]
    summary = summarize(records, root, scan_dirs)
    summary["preflight_warnings"] = warnings

    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    write_json(records, summary)
    write_csv(records)
    write_markdown(records, summary)

    if not args.quiet:
        print("SelfDoc source contract inventory complete.")
        print(f"Safety class: {SAFETY_CLASS}")
        print(f"Project root: {root}")
        print(f"Scanned source files: {summary['total_source_files']}")
        print(f"Files with contracts: {summary['files_with_contract']}")
        print(f"Files missing contracts: {summary['files_missing_contract']}")
        print(f"Escrow candidates: {summary['escrow_candidate_count']}")
        print(f"Wrote: {MD_REPORT}")
        print(f"Wrote: {CSV_REPORT}")
        print(f"Wrote: {JSON_REPORT}")
        print("No source files were edited.")
        print("No DBFs were written.")
        print("CMDHELPCHK was not modified.")
        print("HELP DATA was not rebuilt.")
        print("No headers were repaired.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
