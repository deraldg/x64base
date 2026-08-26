#!/usr/bin/env python3
"""Fail-closed, report-only E5 freshness check for one HELP/META harvest.

The Gate 7 -> 8 entry condition is semantic: the manual harvest must reflect
the current HELP and META stores. File timestamps alone cannot prove that after
a checkout or copy. This audit reads the same DBFs as the interim exporter and
compares every normalized field of every row with a named harvest workspace.
It never writes to or promotes the workspace.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from itertools import zip_longest
from pathlib import Path


HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import dbfread  # noqa: E402
from export_help_meta_harvest import HELP_TABLES, META_TABLES, _cell  # noqa: E402


def compare_table(
    expected_header: list[str],
    expected_rows: list[dict[str, str]],
    csv_path: Path,
) -> dict[str, object]:
    """Compare one exported CSV with normalized source rows."""
    result: dict[str, object] = {
        "target_csv": csv_path.name,
        "exists": int(csv_path.is_file()),
        "header_match": 0,
        "source_rows": len(expected_rows),
        "harvest_rows": -1,
        "mismatched_rows": -1,
        "first_mismatch_row": None,
        "status": "MISSING",
    }
    if not csv_path.is_file():
        return result

    with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        actual_header = reader.fieldnames or []
        actual_rows = list(reader)

    result["harvest_rows"] = len(actual_rows)
    result["header_match"] = int(actual_header == expected_header)
    if actual_header != expected_header:
        result["status"] = "HEADER_MISMATCH"
        return result

    mismatches = 0
    first = None
    missing = object()
    for row_number, pair in enumerate(
        zip_longest(expected_rows, actual_rows, fillvalue=missing), start=2
    ):
        expected, actual = pair
        if expected is missing or actual is missing or expected != actual:
            mismatches += 1
            if first is None:
                first = row_number
    result["mismatched_rows"] = mismatches
    result["first_mismatch_row"] = first
    result["status"] = "PASS" if mismatches == 0 else "CONTENT_MISMATCH"
    return result


def read_manifest(path: Path) -> dict[str, dict[str, str]]:
    if not path.is_file():
        return {}
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return {row.get("target_csv", ""): row for row in csv.DictReader(handle)}


def manifest_findings(
    manifest: dict[str, dict[str, str]], expected_counts: dict[str, int]
) -> list[str]:
    findings: list[str] = []
    for target, count in expected_counts.items():
        row = manifest.get(target)
        if not row:
            findings.append(f"{target}: missing manifest row")
            continue
        if row.get("required", "").lower() != "yes":
            findings.append(f"{target}: required is not yes")
        if row.get("current_status", "").upper() != "EXPORTED":
            findings.append(f"{target}: current_status is not EXPORTED")
        if not row.get("export_method", "").strip():
            findings.append(f"{target}: export_method is blank")
        try:
            recorded = int(row.get("row_count", ""))
        except ValueError:
            recorded = -1
        if recorded != count:
            findings.append(
                f"{target}: manifest row_count {recorded} != source {count}"
            )
    return findings


def audit_workspace(repo_root: Path, workspace: Path) -> dict[str, object]:
    root = repo_root.resolve()
    target = workspace.resolve()
    definitions = [
        ("HELP", root / "dottalkpp" / "data" / "help", HELP_TABLES),
        ("META", root / "dottalkpp" / "data" / "metadata", META_TABLES),
    ]
    tables: list[dict[str, object]] = []
    expected_counts: dict[str, int] = {}

    for family, source_root, mapping in definitions:
        for csv_name, dbf_name in mapping.items():
            dbf_path = source_root / dbf_name
            if not dbf_path.is_file():
                tables.append({
                    "family": family,
                    "source_dbf": str(dbf_path),
                    "target_csv": csv_name,
                    "status": "SOURCE_MISSING",
                })
                continue
            table = dbfread.read(dbf_path)
            header = [field.name for field in table.fields]
            rows = [{key: _cell(value) for key, value in row.items()}
                    for row in table.rows]
            expected_counts[csv_name] = len(rows)
            comparison = compare_table(header, rows, target / csv_name)
            comparison["family"] = family
            comparison["source_dbf"] = str(dbf_path.relative_to(root)).replace("\\", "/")
            tables.append(comparison)

    manifest_path = target / "HELP_META_EXPORT_MANIFEST_v0.csv"
    manifest = read_manifest(manifest_path)
    manifest_issues = manifest_findings(manifest, expected_counts)
    failing_tables = [row for row in tables if row.get("status") != "PASS"]
    status = "PASS" if not failing_tables and not manifest_issues else "FAIL"
    return {
        "schema": "dottalk.fullstack.harvest_freshness.v1",
        "status": status,
        "mutation_performed": 0,
        "repo_root": str(root),
        "workspace": str(target),
        "table_count": len(tables),
        "passing_tables": len(tables) - len(failing_tables),
        "failing_tables": len(failing_tables),
        "manifest_findings": manifest_issues,
        "tables": tables,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--json-out", type=Path)
    args = parser.parse_args(argv)

    result = audit_workspace(args.repo_root, args.workspace)
    print(
        "E5 %s: %d/%d tables match current HELP/META; "
        "manifest_findings=%d; mutation_performed=0"
        % (
            result["status"],
            result["passing_tables"],
            result["table_count"],
            len(result["manifest_findings"]),
        )
    )
    for row in result["tables"]:
        if row.get("status") != "PASS":
            print(
                "  %s: %s source_rows=%s harvest_rows=%s first_mismatch=%s"
                % (
                    row.get("target_csv"),
                    row.get("status"),
                    row.get("source_rows", "?"),
                    row.get("harvest_rows", "?"),
                    row.get("first_mismatch_row", "?"),
                )
            )
    for finding in result["manifest_findings"]:
        print("  manifest: " + finding)

    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
