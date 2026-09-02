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
    memo_columns: frozenset[str] = frozenset(),
) -> dict[str, object]:
    """Compare one exported CSV with normalized source rows.

    MEMO COLUMNS ARE EXCLUDED FROM THE COMPARISON, AND THAT IS THE FIX.

    Measured 2026-09-02 (DOCFLUSH-20260901-002): this check passed the
    memo-BLANK harvest and failed the memo-BEARING one, i.e. it certified the
    interim Python scaffold and rejected the engine.

    The reference side is built with `dbfread` + `export_help_meta_harvest._cell`.
    `dbfread` deliberately does not follow x64 memo blocks -- it returns
    `<memo:unresolved ptr=...>` and says so in its own comment -- and `_cell`
    blanks that marker. So the reference has EMPTY memo columns by construction.

    A harvest produced by the sanctioned engine exporter
    (`HELP_META_HARVEST_EXPORT_v1.ps1` -> `datarun.ps1` -> `EXPORT ... CSV`)
    resolves memo text properly. Measured on HELP_COMMANDS.csv, 462 rows both
    ways: engine USAGE/VERBOSE 462/462 populated, scaffold 0/462. Every table
    then reported CONTENT_MISMATCH at the first data row with IDENTICAL row
    counts -- the signature of a rendering difference, not staleness.

    Comparing a column the reference cannot render is not a check, it is a
    coin-flip weighted against the correct artifact. So those columns are
    skipped and reported separately, and the memo POPULATION is measured instead
    so the gate can say which producer made the harvest rather than silently
    preferring one.
    """
    result: dict[str, object] = {
        "target_csv": csv_path.name,
        "exists": int(csv_path.is_file()),
        "header_match": 0,
        "source_rows": len(expected_rows),
        "harvest_rows": -1,
        "mismatched_rows": -1,
        "first_mismatch_row": None,
        "memo_columns": sorted(memo_columns),
        "memo_columns_compared": 0,
        "memo_populated_rows": 0,
        "memo_rendering": "n/a",
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

    present_memo = [c for c in expected_header if c in memo_columns]
    if present_memo:
        populated = sum(
            1 for row in actual_rows
            if any((row.get(c) or "").strip() for c in present_memo)
        )
        result["memo_populated_rows"] = populated
        # Which producer made this harvest, stated rather than inferred.
        result["memo_rendering"] = (
            "RESOLVED (engine EXPORT CSV)" if populated
            else "BLANK (dbfread scaffold, or genuinely empty memo)"
        )

    def _cmp(row: dict[str, str]) -> dict[str, str]:
        # STRIP BOTH SIDES. The engine's `EXPORT ... CSV` preserves the DBF's
        # fixed-width padding, so a numeric renders as '       337'; dbfread
        # calls .strip() on every field, so the reference renders '337'. Same
        # value, different justification -- and comparing them raw made all six
        # HELP tables mismatch at the first data row.
        #
        # This is not a weakening. The reference side was ALREADY stripped for
        # every column, so no leading/trailing space distinction was ever
        # observable through this check; stripping both sides just makes that
        # symmetry explicit instead of penalising the producer that preserves
        # the on-disk form.
        return {k: (v or "").strip()
                for k, v in row.items() if k not in memo_columns}

    mismatches = 0
    first = None
    missing = object()
    for row_number, pair in enumerate(
        zip_longest(expected_rows, actual_rows, fillvalue=missing), start=2
    ):
        expected, actual = pair
        if expected is missing or actual is missing:
            mismatches += 1
            if first is None:
                first = row_number
            continue
        if _cmp(expected) != _cmp(actual):
            mismatches += 1
            if first is None:
                first = row_number
    result["mismatched_rows"] = mismatches
    result["first_mismatch_row"] = first
    result["status"] = "PASS" if mismatches == 0 else "CONTENT_MISMATCH"
    return result


def _recode(value: str) -> str:
    """Undo dbfread's latin1 decode so the reference reads as UTF-8.

    `dbfread` decodes record bytes with latin1 (`.decode("latin1")`), which never
    raises and therefore never reveals that the store actually holds UTF-8. An
    em-dash stored as E2 80 94 comes back as 'a\\x80\\x94'. The engine's
    `EXPORT ... CSV` writes real UTF-8, so every row containing a non-ASCII
    character compared unequal -- measured 2026-09-02 as the LAST cause of E5
    failing the engine export, 28 rows in HELP_LINE alone.

    Round-tripping latin1 -> bytes -> utf-8 recovers the true text. When the
    bytes are not valid UTF-8 the original is returned unchanged, so a genuinely
    latin1 store is not corrupted by this.

    This does NOT hide the non-ASCII; `audit_workspace` counts it per table and
    reports it, because the content it exposed is a real house-rule finding.
    """
    if value.isascii():
        return value
    try:
        return value.encode("latin1").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return value


def read_manifest(path: Path) -> dict[str, dict[str, str]]:
    if not path.is_file():
        return {}
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return {row.get("target_csv", ""): row for row in csv.DictReader(handle)}


def manifest_findings(
    manifest: dict[str, dict[str, str]], expected_counts: dict[str, int]
) -> list[str]:
    """Validate the export manifest, in EITHER schema.

    TWO SCHEMAS EXIST AND ONLY ONE WAS UNDERSTOOD (measured 2026-09-02):

        v0  export_help_meta_harvest.py (Python scaffold)
            source,table_name,target_csv,required,current_status,row_count,
            export_method,notes
        v1  HELP_META_HARVEST_EXPORT_v1.ps1 (sanctioned, engine-backed)
            target_csv,status,row_count,sha256,source,export_method

    This function read `current_status` and the caller opened `..._v0.csv` only,
    so a complete and correct v1 manifest produced 14 "missing manifest row"
    findings while sitting in the same directory.

    STATUS VOCABULARY. v1 writes CARRIED_STALE_MAY for the four META_* tables
    whose sources are not current -- the honest label, and the whole reason that
    producer exists ("so manualgen sees all 14 required files WITHOUT PRETENDING
    THE STALE FOUR ARE CURRENT"). Demanding EXPORTED flagged those rows FOR
    BEING TRUTHFUL. They are now accepted and surfaced separately, so a reader
    still learns which four are stale.
    """
    accepted = {"EXPORTED", "CARRIED_STALE_MAY"}
    findings: list[str] = []
    for target, count in expected_counts.items():
        row = manifest.get(target)
        if not row:
            findings.append(f"{target}: missing manifest row")
            continue
        # v0 has `required`; v1 does not carry the column at all.
        if "required" in row and row.get("required", "").lower() != "yes":
            findings.append(f"{target}: required is not yes")
        status = (row.get("current_status") or row.get("status") or "").upper()
        if status not in accepted:
            findings.append(
                f"{target}: status {status!r} is not one of {sorted(accepted)}"
            )
        if not row.get("export_method", "").strip():
            findings.append(f"{target}: export_method is blank")
        if status == "CARRIED_STALE_MAY":
            # Declared stale on purpose. Its row_count describes the carried
            # file, not the live source, so comparing them is meaningless.
            continue
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
            # Type "M" is a memo pointer. dbfread cannot follow it, so the
            # reference cannot render these columns and must not judge them.
            memo_cols = frozenset(f.name for f in table.fields
                                  if getattr(f, "type", "") == "M")
            rows = [{key: _recode(_cell(value)) for key, value in row.items()}
                    for row in table.rows]
            expected_counts[csv_name] = len(rows)
            comparison = compare_table(header, rows, target / csv_name,
                                       memo_columns=memo_cols)
            # Surface what _recode() normalized. The house rule is ASCII-only
            # ("no em-dashes; use -- / ->"), so non-ASCII in a SHIPPED HELP row
            # is a finding in its own right -- reported, never silently fixed.
            comparison["non_ascii_rows"] = sum(
                1 for row in rows
                if any(isinstance(v, str) and not v.isascii() for v in row.values())
            )
            comparison["family"] = family
            comparison["source_dbf"] = str(dbf_path.relative_to(root)).replace("\\", "/")
            tables.append(comparison)

    # v1 is the sanctioned engine producer's manifest; v0 is the Python
    # scaffold's. Prefer v1 when present. Hardcoding v0 is what made a correct
    # engine export look like fourteen missing manifest rows.
    manifest_path = next(
        (target / name for name in ("HELP_META_EXPORT_MANIFEST_v1.csv",
                                    "HELP_META_EXPORT_MANIFEST_v0.csv")
         if (target / name).is_file()),
        target / "HELP_META_EXPORT_MANIFEST_v0.csv",
    )
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
