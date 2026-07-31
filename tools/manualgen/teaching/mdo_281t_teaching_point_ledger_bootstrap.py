#!/usr/bin/env python3
"""
MDO-281T Teaching Point Ledger Bootstrap v1

Report-only / documentation-lane bootstrap.

Creates or updates a lightweight Teaching Point Ledger under:

  docs/teaching/TEACHING_POINT_LEDGER.md
  docs/teaching/teaching_points_v1.csv
  docs/teaching/TEACHING_POINT_POLICY.md

and writes a run report under the selected out-dir.

This package is intentionally NOT a runtime catalog DBF load.
It does not create DBFs, CDXs, LMDB mirrors, HELP rows, CMDHELPCHK rows,
source edits, manual publication edits, or publication replacements.
"""
from __future__ import annotations

import argparse
import csv
import json
import shutil
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

CSV_FIELDS = [
    "TPID", "DATE", "TITLE", "AUDIENCE", "MANUAL_TARGET", "FEATURE_AREA",
    "EVIDENCE_CLASS", "STATUS", "PROMOTION_TARGET", "SUMMARY",
]

SEED_POINTS = [
    {
        "TPID": "TP-20260528-001",
        "DATE": "20260528",
        "TITLE": "Compatibility Names and Authoritative Names",
        "AUDIENCE": "Student;Developer",
        "MANUAL_TARGET": "Student Manual;Developer Manual",
        "FEATURE_AREA": "x64 names;DBF compatibility;name mangling",
        "EVIDENCE_CLASS": "DESIGN_INTENT;RUNTIME_PROVEN_PARTIAL",
        "STATUS": "CAPTURED",
        "PROMOTION_TARGET": "Student concept box;Developer x64 naming section",
        "SUMMARY": "DotTalk++ name mangling teaches a systems lesson inspired by the transition from short legacy filenames to longer modern names: keep a compatibility handle while preserving a richer authoritative identity.",
    },
    {
        "TPID": "TP-20260528-002",
        "DATE": "20260528",
        "TITLE": "Index Building as an Algorithm Laboratory",
        "AUDIENCE": "Student;Developer",
        "MANUAL_TARGET": "Student Manual;Developer Manual",
        "FEATURE_AREA": "indexing;INX;algorithms;sort timing",
        "EVIDENCE_CLASS": "DESIGN_INTENT",
        "STATUS": "CAPTURED",
        "PROMOTION_TARGET": "Student exercise;Developer extension note",
        "SUMMARY": "INX index creation should eventually allow a timed sort-method option so students can compare binary sort, bubble sort, and other algorithms against real data.",
    },
    {
        "TPID": "TP-20260528-003",
        "DATE": "20260528",
        "TITLE": "Commands as Extensible Learning Objects",
        "AUDIENCE": "Student;Developer",
        "MANUAL_TARGET": "Student Manual;Developer Manual",
        "FEATURE_AREA": "commands;functions;self-registration;extensions",
        "EVIDENCE_CLASS": "SOURCE_DEFINED_OR_RUNTIME_PROVEN_REVIEW",
        "STATUS": "CAPTURED",
        "PROMOTION_TARGET": "Student advanced chapter;Developer extension chapter",
        "SUMMARY": "DotTalk++ supports student or self-registering commands and functions, allowing learners and extensions to participate in the command/function ecosystem without rewriting the core.",
    },
    {
        "TPID": "TP-20260528-004",
        "DATE": "20260528",
        "TITLE": "Reserved Index Families for Student and Custom Extension",
        "AUDIENCE": "Student;Developer;Corporate Extension",
        "MANUAL_TARGET": "Developer Manual;Student Manual",
        "FEATURE_AREA": "indexing;SIX;SNX;custom indexes",
        "EVIDENCE_CLASS": "DESIGN_INTENT_OR_SOURCE_DEFINED_REVIEW",
        "STATUS": "CAPTURED",
        "PROMOTION_TARGET": "Developer indexing architecture;Student extension exercise",
        "SUMMARY": "SIX and SNX are reserved as index types for student work or corporate custom index systems, preserving extension space without colliding with core index families.",
    },
]

@dataclass
class BoundaryRow:
    boundary: str
    observed: int
    required: int
    passed: int

@dataclass
class OutputRow:
    artifact: str
    path: str
    exists: int
    role: str


def repo_rel(repo_root: Path, path: Path) -> str:
    try:
        return str(path.relative_to(repo_root)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def write_csv(path: Path, rows: Iterable[object], fieldnames=None) -> None:
    rows = list(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        if rows and hasattr(rows[0], "__dataclass_fields__"):
            fieldnames = list(asdict(rows[0]).keys())
            rows_out = [asdict(r) for r in rows]
        elif rows:
            fieldnames = list(rows[0].keys())
            rows_out = rows
        else:
            fieldnames = []
            rows_out = []
    else:
        rows_out = rows
    with path.open("w", newline="", encoding="utf-8") as f:
        if not fieldnames:
            return
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows_out:
            writer.writerow(row)


def load_existing_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def merge_points(existing: list[dict], seed: list[dict]) -> tuple[list[dict], int, int]:
    by_id: dict[str, dict] = {}
    order: list[str] = []
    for row in existing:
        tpid = (row.get("TPID") or "").strip()
        if not tpid:
            continue
        by_id[tpid] = {field: row.get(field, "") for field in CSV_FIELDS}
        order.append(tpid)
    added = 0
    skipped = 0
    for row in seed:
        tpid = row["TPID"]
        if tpid in by_id:
            skipped += 1
            continue
        by_id[tpid] = {field: row.get(field, "") for field in CSV_FIELDS}
        order.append(tpid)
        added += 1
    return [by_id[tpid] for tpid in order], added, skipped


def backup_if_needed(path: Path, backup_dir: Path) -> Path | None:
    if not path.exists():
        return None
    backup_dir.mkdir(parents=True, exist_ok=True)
    backup_path = backup_dir / path.name
    shutil.copy2(path, backup_path)
    return backup_path


def build_policy(run_id: str, created_utc: str) -> str:
    return f"""# Teaching Point Ledger Policy

Run id: `{run_id}`
Created UTC: `{created_utc}`

## Purpose

The Teaching Point Ledger captures small instructional insights before they are mature enough to become manual chapters, exercises, HELP notes, case studies, diagrams, or Data Dictionary evidence links.

The rule is:

```text
Do not lose teaching ideas just because they are not ready to become chapters.
```

## Evidence classes

```text
IDEA
DESIGN_INTENT
RUNTIME_PROVEN
RUNTIME_PROVEN_PARTIAL
SOURCE_DEFINED
HELP_DOCUMENTED
CMDHELPCHK_VALIDATED
DATADICT_CATALOGED
SELFDoc_REPORTED
REPORT_PROVEN
DEFERRED
HISTORICAL_LESSON
SOURCE_DEFINED_OR_RUNTIME_PROVEN_REVIEW
DESIGN_INTENT_OR_SOURCE_DEFINED_REVIEW
```

## Status values

```text
CAPTURED
NEEDS_PROOF
NEEDS_EXAMPLE
READY_FOR_STUDENT_MANUAL
READY_FOR_USER_MANUAL
READY_FOR_DEVELOPER_MANUAL
READY_FOR_CASE_STUDY
READY_FOR_EXERCISE
PROMOTED
DEFERRED
REJECTED
```

## Safety boundary

This policy and ledger do not mutate source files, HELP, CMDHELPCHK, active catalog DBFs, manual publications, Data Dictionary catalogs, CDX/LMDB artifacts, or runtime data.
"""


def build_ledger(points: list[dict], run_id: str, created_utc: str) -> str:
    lines = [
        "# Teaching Point Ledger", "", f"Run id: `{run_id}`  ", f"Created UTC: `{created_utc}`", "",
        "Purpose:", "", "```text", "Capture small teaching insights before they are ready to become chapters, exercises, HELP notes, diagrams, or catalog rows.", "```", "",
        "Working rule:", "", "```text", "Do not lose teaching ideas just because they are not ready to become chapters.", "```", "",
    ]
    for row in points:
        lines.extend([
            f"## {row['TPID']} - {row['TITLE']}", "",
            f"Status: {row['STATUS']}  ",
            f"Audience: {row['AUDIENCE']}  ",
            f"Manual target: {row['MANUAL_TARGET']}  ",
            f"Feature area: {row['FEATURE_AREA']}  ",
            f"Evidence class: {row['EVIDENCE_CLASS']}  ",
            f"Promotion target: {row['PROMOTION_TARGET']}", "",
            "Teaching point:", "", row["SUMMARY"], "",
            "Promotion notes:", "",
            "- Verify evidence class before promotion.",
            "- Decide whether this belongs in Student, User, Developer, case-study, exercise, HELP, or SelfDoc material.",
            "- Preserve source/runtime proof separately from the teaching idea.", "",
        ])
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="MDO-281T Teaching Point Ledger Bootstrap v1")
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--run-id", default="MDO281T-teaching-point-ledger-bootstrap-v1")
    parser.add_argument("--profile", action="append", default=[])
    parser.add_argument("--write-ledger", action="store_true", help="Write docs/teaching ledger/policy/CSV artifacts")
    parser.add_argument("--replace-existing", action="store_true", help="Replace existing ledger Markdown/policy Markdown; CSV is merged by TPID")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    out_dir = Path(args.out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    created_utc = datetime.now(timezone.utc).isoformat(timespec="seconds")

    docs_teaching = repo_root / "docs" / "teaching"
    ledger_path = docs_teaching / "TEACHING_POINT_LEDGER.md"
    csv_path = docs_teaching / "teaching_points_v1.csv"
    policy_path = docs_teaching / "TEACHING_POINT_POLICY.md"
    backup_dir = out_dir / "backups"

    existing_points = load_existing_csv(csv_path)
    merged_points, added_count, skipped_count = merge_points(existing_points, SEED_POINTS)
    docs_existed_before = 1 if docs_teaching.exists() else 0
    writes_authorized = 1 if args.write_ledger else 0

    if args.write_ledger:
        docs_teaching.mkdir(parents=True, exist_ok=True)
        if args.replace_existing:
            backup_if_needed(ledger_path, backup_dir)
            backup_if_needed(policy_path, backup_dir)
        backup_if_needed(csv_path, backup_dir)
        write_csv(csv_path, merged_points, fieldnames=CSV_FIELDS)
        if args.replace_existing or not ledger_path.exists():
            ledger_path.write_text(build_ledger(merged_points, args.run_id, created_utc), encoding="utf-8")
        if args.replace_existing or not policy_path.exists():
            policy_path.write_text(build_policy(args.run_id, created_utc), encoding="utf-8")
    else:
        preview_dir = out_dir / "preview_docs_teaching"
        preview_dir.mkdir(parents=True, exist_ok=True)
        write_csv(preview_dir / "teaching_points_v1.csv", merged_points, fieldnames=CSV_FIELDS)
        (preview_dir / "TEACHING_POINT_LEDGER.md").write_text(build_ledger(merged_points, args.run_id, created_utc), encoding="utf-8")
        (preview_dir / "TEACHING_POINT_POLICY.md").write_text(build_policy(args.run_id, created_utc), encoding="utf-8")

    boundary_rows = [
        BoundaryRow("teaching_ledger_bootstrap_only", 1, 1, 1),
        BoundaryRow("write_ledger_authorized", writes_authorized, writes_authorized, 1),
        BoundaryRow("source_file_mutation", 0, 0, 1),
        BoundaryRow("manual_publication_mutation", 0, 0, 1),
        BoundaryRow("manual_rebuild", 0, 0, 1),
        BoundaryRow("manual_catalog_dbf_create_or_load", 0, 0, 1),
        BoundaryRow("dbf_append_replace_delete_pack_zap", 0, 0, 1),
        BoundaryRow("cdx_lmdb_create_rebuild", 0, 0, 1),
        BoundaryRow("help_mutation", 0, 0, 1),
        BoundaryRow("cmdhelpchk_mutation", 0, 0, 1),
        BoundaryRow("datadict_catalog_mutation", 0, 0, 1),
        BoundaryRow("metadata_mutation", 0, 0, 1),
        BoundaryRow("publication_replacement", 0, 0, 1),
    ]
    output_rows = [
        OutputRow("TEACHING_POINT_LEDGER", repo_rel(repo_root, ledger_path), 1 if ledger_path.exists() else 0, "Markdown running ledger"),
        OutputRow("TEACHING_POINT_CSV", repo_rel(repo_root, csv_path), 1 if csv_path.exists() else 0, "CSV import/crosswalk seed"),
        OutputRow("TEACHING_POINT_POLICY", repo_rel(repo_root, policy_path), 1 if policy_path.exists() else 0, "Ledger policy"),
    ]
    write_csv(out_dir / "mdo_281t_teaching_point_seed_rows.csv", SEED_POINTS, fieldnames=CSV_FIELDS)
    write_csv(out_dir / "mdo_281t_no_mutation_boundary_ledger.csv", boundary_rows)
    write_csv(out_dir / "mdo_281t_output_ledger.csv", output_rows)

    status = "MDO281T_TEACHING_POINT_LEDGER_PREVIEW_GREEN"
    if args.write_ledger:
        status = "MDO281T_TEACHING_POINT_LEDGER_BOOTSTRAP_GREEN"

    report = f"""# MDO-281T Teaching Point Ledger Bootstrap

Run id: `{args.run_id}`
Status: **{status}**
Created UTC: `{created_utc}`

## Purpose

MDO-281T creates a lightweight running log for small teaching insights before they are mature enough to become manual chapters, exercises, HELP notes, diagrams, case studies, or catalog rows.

## Summary

- Seed teaching points: **{len(SEED_POINTS)}**
- Existing teaching points found: **{len(existing_points)}**
- Seed points added to merged CSV: **{added_count}**
- Seed points skipped because TPID already existed: **{skipped_count}**
- Write ledger authorized: **{writes_authorized}**
- docs/teaching existed before run: **{docs_existed_before}**
- Protected mutations: **0**

## Seeded points

```text
{chr(10).join(row['TPID'] + '  ' + row['TITLE'] for row in SEED_POINTS)}
```

## Output locations

```text
docs/teaching/TEACHING_POINT_LEDGER.md
docs/teaching/teaching_points_v1.csv
docs/teaching/TEACHING_POINT_POLICY.md
```

If `--write-ledger` was not supplied, preview copies were written under this report directory instead.

## Boundary

This package does not edit source files, rebuild manuals, replace publications, create/load DBFs, create/rebuild CDX/LMDB, mutate HELP, mutate CMDHELPCHK, mutate Data Dictionary catalogs, mutate metadata catalogs, or repair manual rows.
"""
    report_path = out_dir / "MDO281T_TEACHING_POINT_LEDGER_BOOTSTRAP_REPORT.md"
    report_path.write_text(report, encoding="utf-8")

    manifest = {
        "run_id": args.run_id,
        "status": status,
        "created_utc": created_utc,
        "repo_root": str(repo_root),
        "out_dir": str(out_dir),
        "profiles": args.profile,
        "write_ledger_authorized": writes_authorized,
        "seed_points": len(SEED_POINTS),
        "existing_points": len(existing_points),
        "added_count": added_count,
        "skipped_count": skipped_count,
        "protected_mutations": 0,
        "outputs": {
            "report": str(report_path),
            "seed_rows": str(out_dir / "mdo_281t_teaching_point_seed_rows.csv"),
            "boundary_ledger": str(out_dir / "mdo_281t_no_mutation_boundary_ledger.csv"),
            "output_ledger": str(out_dir / "mdo_281t_output_ledger.csv"),
        },
    }
    manifest_path = out_dir / "mdo_281t_teaching_point_ledger_bootstrap_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"MDO-281T teaching point ledger manifest: {manifest_path}")
    print(f"status: {status}; seed_points: {len(SEED_POINTS)}; added: {added_count}; skipped: {skipped_count}; write_ledger_authorized: {writes_authorized}; protected_mutations: 0")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
