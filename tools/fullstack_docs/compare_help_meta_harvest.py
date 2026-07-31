#!/usr/bin/env python3
"""Compare two HELP/META CSV harvest workspaces without promoting either one."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


REQUIRED_FILES = (
    "HELP_CMD_ARGS.csv",
    "HELP_COMMANDS.csv",
    "HELP_HELP_ARTIFACTS.csv",
    "HELP_HELP_LINE.csv",
    "HELP_HELP_SECTION.csv",
    "HELP_HELP_TOPIC.csv",
    "META_SYSARGS.csv",
    "META_SYSCMD.csv",
    "META_SYSENTVAR.csv",
    "META_SYSFLDDIC.csv",
    "META_SYSFUNC.csv",
    "META_SYSHELP.csv",
    "META_SYSMSG.csv",
    "META_SYSSUBCMD.csv",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def csv_shape(path: Path) -> tuple[list[str], int]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle)
        header = next(reader, [])
        return header, sum(1 for _ in reader)


def compare(baseline: Path, candidate: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for name in REQUIRED_FILES:
        old = baseline / name
        new = candidate / name
        old_exists = old.is_file()
        new_exists = new.is_file()
        old_header, old_count = csv_shape(old) if old_exists else ([], -1)
        new_header, new_count = csv_shape(new) if new_exists else ([], -1)
        old_hash = sha256(old) if old_exists else ""
        new_hash = sha256(new) if new_exists else ""
        header_match = bool(old_exists and new_exists and old_header == new_header)
        hash_match = bool(old_exists and new_exists and old_hash == new_hash)
        if not old_exists or not new_exists:
            status = "MISSING_REQUIRED_FILE"
        elif hash_match:
            status = "UNCHANGED"
        elif header_match:
            status = "CONTENT_CHANGED_COMPATIBLE_HEADER"
        else:
            status = "HEADER_CHANGED"
        rows.append({
            "file_name": name,
            "family": "HELP" if name.startswith("HELP_") else "META",
            "baseline_exists": int(old_exists),
            "candidate_exists": int(new_exists),
            "baseline_rows": old_count,
            "candidate_rows": new_count,
            "row_delta": new_count - old_count if old_exists and new_exists else "",
            "header_match": int(header_match),
            "hash_match": int(hash_match),
            "baseline_sha256": old_hash,
            "candidate_sha256": new_hash,
            "status": status,
        })
    return rows


def write_outputs(output_dir: Path, baseline: Path, candidate: Path, rows: list[dict[str, object]]) -> dict[str, object]:
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / "help_meta_harvest_delta_v1.csv"
    json_path = output_dir / "help_meta_harvest_delta_v1.json"
    md_path = output_dir / "HELP_META_HARVEST_DELTA_V1.md"
    fields = list(rows[0].keys()) if rows else []
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

    summary = {
        "schema": "dottalk.manualgen.help_meta_harvest_delta.v1",
        "created_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "baseline_workspace": str(baseline.resolve()),
        "candidate_workspace": str(candidate.resolve()),
        "required_file_count": len(REQUIRED_FILES),
        "unchanged_files": sum(row["status"] == "UNCHANGED" for row in rows),
        "compatible_content_changes": sum(row["status"] == "CONTENT_CHANGED_COMPATIBLE_HEADER" for row in rows),
        "header_changed_files": sum(row["status"] == "HEADER_CHANGED" for row in rows),
        "missing_required_files": sum(row["status"] == "MISSING_REQUIRED_FILE" for row in rows),
        "baseline_rows": sum(int(row["baseline_rows"]) for row in rows if int(row["baseline_rows"]) >= 0),
        "candidate_rows": sum(int(row["candidate_rows"]) for row in rows if int(row["candidate_rows"]) >= 0),
        "promotion_performed": 0,
        "files": rows,
    }
    json_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# HELP/META Harvest Delta v1",
        "",
        "Status: comparison complete; no promotion performed.",
        "",
        f"- Baseline: `{summary['baseline_workspace']}`",
        f"- Candidate: `{summary['candidate_workspace']}`",
        f"- Required files: {summary['required_file_count']}",
        f"- Compatible content changes: {summary['compatible_content_changes']}",
        f"- Unchanged files: {summary['unchanged_files']}",
        f"- Header changes: {summary['header_changed_files']}",
        f"- Missing required files: {summary['missing_required_files']}",
        f"- Total rows: {summary['baseline_rows']} -> {summary['candidate_rows']} ({summary['candidate_rows'] - summary['baseline_rows']:+d})",
        "",
        "| File | Baseline | Candidate | Delta | Header | Status |",
        "|---|---:|---:|---:|---|---|",
    ]
    for row in rows:
        lines.append(f"| {row['file_name']} | {row['baseline_rows']} | {row['candidate_rows']} | {row['row_delta']} | {'MATCH' if row['header_match'] else 'CHANGED'} | {row['status']} |")
    lines.extend([
        "",
        "This report is an evidence comparison only. It does not replace the canonical harvest, change publication pointers, or claim that manual prose consumes the changed rows.",
        "",
    ])
    md_path.write_text("\n".join(lines), encoding="utf-8")
    return summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    rows = compare(args.baseline, args.candidate)
    summary = write_outputs(args.output_dir, args.baseline, args.candidate, rows)
    for key in ("required_file_count", "compatible_content_changes", "unchanged_files", "header_changed_files", "missing_required_files", "baseline_rows", "candidate_rows"):
        print(f"{key}={summary[key]}")
    return 2 if summary["header_changed_files"] or summary["missing_required_files"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
