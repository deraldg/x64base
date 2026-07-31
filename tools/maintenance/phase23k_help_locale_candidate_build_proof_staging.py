#!/usr/bin/env python3
"""PHASE23K HELP locale candidate DBF/CDX/LMDB build proof staging.

This is a guarded staging package. Python writes candidate-only data files,
DotScript build/readback scripts, and a manifest. It does not execute DotTalk++
and does not mutate active HELP, source, CMDHELP, CMDHELPCHK, MAINT, or BBOX.

The generated DotScript intentionally writes only to the candidate directory:
  docs/locale/candidates/PHASE23K-HELP-LOCALE-CANDIDATE-DBF-CDX-LMDB-BUILD-PROOF
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List

STATUS = "PHASE23K_HELP_LOCALE_CANDIDATE_DBF_CDX_LMDB_BUILD_PROOF_STAGING_GREEN_MANUAL_DOTSCRIPT_REQUIRED"
NEXT_GATE = "HOLD_OR_RUN_PHASE23K_DOTSCRIPT_AND_REVIEW_TRANSCRIPT"
FINAL_GREEN_STATUS = "PHASE23K_HELP_LOCALE_CANDIDATE_DBF_CDX_LMDB_BUILD_PROOF_GREEN_CANDIDATE_ARTIFACTS_PROVEN"
PHASE23J_STATUS = "PHASE23J_HELP_LOCALE_SAMPLE_ROW_MATERIALIZATION_PLAN_GREEN_CANDIDATE_ONLY"
PHASE23J_SLUG = "PHASE23J-HELP-LOCALE-SAMPLE-ROW-MATERIALIZATION-PLAN"
PHASE23K_SLUG = "PHASE23K-HELP-LOCALE-CANDIDATE-DBF-CDX-LMDB-BUILD-PROOF"

TABLE_SOURCES = [
    {
        "table": "HELP_TOPIC_LOCALE",
        "csv": "phase23j_help_topic_locale_sample_rows.csv",
        "primary_tag": "TOPICLOC",
        "primary_field": "TOPICKEY",
        "fields": [
            ("RUN_ID", "C(40)"),
            ("TOPIC_LOCALE_ID", "C(24)"),
            ("TOPICKEY", "C(96)"),
            ("COMMAND", "C(64)"),
            ("LOCALE_ID", "C(16)"),
            ("TEXT_DIR", "C(8)"),
            ("SOURCE_TITLE", "C(180)"),
            ("LOCALIZED_TITLE", "C(240)"),
            ("SOURCE_HASH", "C(24)"),
            ("LOCALIZED_HASH", "C(24)"),
            ("TRANSL_STATUS", "C(32)"),
            ("REVIEW_STATUS", "C(32)"),
            ("FALLBACK_ALLOWED", "L"),
            ("CREATED_AT", "C(32)"),
        ],
    },
    {
        "table": "HELP_SECTION_LOCALE",
        "csv": "phase23j_help_section_locale_sample_rows.csv",
        "primary_tag": "SECTIONLC",
        "primary_field": "TOPICKEY",
        "fields": [
            ("RUN_ID", "C(40)"),
            ("SECTION_LOCALE_ID", "C(24)"),
            ("TOPICKEY", "C(96)"),
            ("SECTION_KEY", "C(40)"),
            ("LOCALE_ID", "C(16)"),
            ("SECTION_ORDER", "N(10,0)"),
            ("SOURCE_LABEL", "C(80)"),
            ("LOCALIZED_LABEL", "C(120)"),
            ("SOURCE_HASH", "C(24)"),
            ("LOCALIZED_HASH", "C(24)"),
            ("TRANSL_STATUS", "C(32)"),
            ("REVIEW_STATUS", "C(32)"),
            ("FALLBACK_ALLOWED", "L"),
            ("CREATED_AT", "C(32)"),
        ],
    },
    {
        "table": "HELP_LINE_LOCALE",
        "csv": "phase23j_help_line_locale_sample_rows.csv",
        "primary_tag": "LINELOC",
        "primary_field": "TOPICKEY",
        "fields": [
            ("RUN_ID", "C(40)"),
            ("LINE_LOCALE_ID", "C(24)"),
            ("TOPICKEY", "C(96)"),
            ("SECTION_KEY", "C(40)"),
            ("KIND", "C(40)"),
            ("ROLE", "C(40)"),
            ("LINE_ORDER", "N(10,0)"),
            ("LOCALE_ID", "C(16)"),
            ("LOCALIZED_LABEL", "C(120)"),
            ("SOURCE_TEXT", "M"),
            ("LOCALIZED_TEXT", "M"),
            ("SOURCE_HASH", "C(24)"),
            ("LOCALIZED_HASH", "C(24)"),
            ("TRANSL_STATUS", "C(32)"),
            ("REVIEW_STATUS", "C(32)"),
            ("FALLBACK_ALLOWED", "L"),
            ("CREATED_AT", "C(32)"),
        ],
    },
    {
        "table": "HELP_ARTIFACT_LOCALE",
        "csv": "phase23j_help_artifact_locale_sample_rows.csv",
        "primary_tag": "ARTLOC",
        "primary_field": "TOPICKEY",
        "fields": [
            ("RUN_ID", "C(40)"),
            ("ARTIFACT_LOCALE_ID", "C(24)"),
            ("TOPICKEY", "C(96)"),
            ("ARTIFACT_KIND", "C(64)"),
            ("LOCALE_ID", "C(16)"),
            ("SOURCE_ARTIFACT_HASH", "C(24)"),
            ("LOCALIZED_ARTIFACT_HASH", "C(24)"),
            ("TRANSL_STATUS", "C(32)"),
            ("REVIEW_STATUS", "C(32)"),
            ("FALLBACK_ALLOWED", "L"),
            ("CREATED_AT", "C(32)"),
        ],
    },
]


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def stable_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()[:16].upper()


def rel(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root)).replace("/", "\\")
    except ValueError:
        return str(path).replace("/", "\\")


def win_abs(path: Path) -> str:
    return str(path.resolve()).replace("/", "\\")


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as f:
        return [dict(row) for row in csv.DictReader(f)]


def write_csv(path: Path, rows: List[Dict[str, Any]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames: List[str] = []
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def find_phase23j_dir(repo_root: Path) -> Path | None:
    base = repo_root / "docs" / "locale" / "candidates" / PHASE23J_SLUG
    if base.exists():
        return base
    candidates = repo_root / "docs" / "locale" / "candidates"
    if not candidates.exists():
        return None
    for path in candidates.rglob("phase23j_manifest.json"):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if data.get("status") == PHASE23J_STATUS:
            return path.parent
    return None


def has_phase23j_green(phase23j_dir: Path | None) -> bool:
    if not phase23j_dir:
        return False
    manifest = phase23j_dir / "phase23j_manifest.json"
    if manifest.exists():
        try:
            return json.loads(manifest.read_text(encoding="utf-8")).get("status") == PHASE23J_STATUS
        except Exception:
            pass
    for path in phase23j_dir.rglob("*"):
        if not path.is_file() or path.stat().st_size > 2_000_000:
            continue
        try:
            if PHASE23J_STATUS in path.read_text(encoding="utf-8", errors="ignore"):
                return True
        except OSError:
            continue
    return False


def dts_quote(value: Any) -> str:
    text = "" if value is None else str(value)
    # Keep generated commands one-line and conservative. Non-ASCII is preserved.
    text = text.replace("\r", " ").replace("\n", " ")
    text = text.replace('"', "'")
    if len(text) > 900:
        text = text[:900]
    return f'"{text}"'


def dts_value(field_type: str, value: Any) -> str:
    text = "" if value is None else str(value)
    kind = field_type.upper()
    if kind.startswith("L"):
        return ".T." if text.strip() not in ("", "0", "F", "False", "false", ".F.") else ".F."
    if kind.startswith(("N", "I", "F", "B", "Y")):
        return text.strip() if text.strip() else "0"
    return dts_quote(text)


def create_statement(table: str, fields: List[tuple[str, str]]) -> str:
    body = ", ".join(f"{name} {spec}" for name, spec in fields)
    return f"CREATE X64 {table} ({body})"


def build_dts(candidate_dir: Path, dbf_dir: Path, indexes_dir: Path, lmdb_dir: Path, row_sets: Dict[str, List[Dict[str, str]]]) -> str:
    lines: List[str] = []
    lines.extend([
        "* ============================================================",
        "* PHASE23K HELP locale candidate DBF/CDX/LMDB build proof",
        "* Candidate-only. Writes only to PHASE23K candidate paths.",
        "* ============================================================",
        "ECHO ON",
        "SET PAGING OFF",
        "ECHO PHASE23K_DOTSCRIPT_START",
        f"SETPATH DBF {win_abs(dbf_dir)}",
        f"SETPATH INDEXES {win_abs(indexes_dir)}",
        f"SETPATH LMDB {win_abs(lmdb_dir)}",
        "WORKSPACE CLOSE",
    ])
    for spec in TABLE_SOURCES:
        table = spec["table"]
        rows = row_sets.get(table, [])
        fields: List[tuple[str, str]] = spec["fields"]
        tag = spec["primary_tag"]
        tag_field = spec["primary_field"]
        lines.append(f"ECHO PHASE23K_CREATE_TABLE_{table}")
        lines.append(create_statement(table, fields))
        for row in rows:
            lines.append("APPEND")
            for field_name, field_type in fields:
                if field_name in row:
                    lines.append(f"REPLACE {field_name} WITH {dts_value(field_type, row.get(field_name, ''))}")
        lines.append("STRUCT")
        lines.append("SMARTLIST ALL")
        lines.append(f"ECHO PHASE23K_CREATE_CDX_{table}")
        lines.append(f"CDX CREATE {table} TAG {tag} ON {tag_field}")
        lines.append(f"SET INDEX TO {table}.CDX")
        lines.append(f"SET ORDER TO TAG {tag}")
        lines.append("AREA")
        lines.append("SMARTLIST ALL")
        lines.append(f"ECHO PHASE23K_BUILD_LMDB_{table}")
        lines.append("BUILDLMDB CLEAN TINY YES")
        lines.append("STATUS")
        lines.append("SMARTLIST ALL")
    lines.extend([
        "ECHO PHASE23K_REOPEN_READBACK_START",
        "WORKSPACE CLOSE",
        f"SETPATH DBF {win_abs(dbf_dir)}",
        f"SETPATH INDEXES {win_abs(indexes_dir)}",
        f"SETPATH LMDB {win_abs(lmdb_dir)}",
        "WORKSPACE OPEN DBF",
    ])
    for spec in TABLE_SOURCES:
        table = spec["table"]
        tag = spec["primary_tag"]
        lines.append(f"ECHO PHASE23K_READBACK_{table}")
        lines.append(f"SELECT {table}")
        lines.append("AREA")
        lines.append(f"SET INDEX TO {table}.CDX")
        lines.append(f"SET ORDER TO TAG {tag}")
        lines.append("SMARTLIST ALL")
    lines.extend([
        "ECHO PHASE23K_DOTSCRIPT_END",
        "SET ORDER TO 0",
        "WORKSPACE CLOSE",
        "",
    ])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Stage PHASE23K candidate HELP locale DBF/CDX/LMDB build proof.")
    parser.add_argument("--repo-root", default=".", help="Repository root")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    if not repo_root.exists():
        raise SystemExit(f"repo root does not exist: {repo_root}")

    phase23j_dir = find_phase23j_dir(repo_root)
    phase23j_green = 1 if has_phase23j_green(phase23j_dir) else 0

    candidate_dir = repo_root / "docs" / "locale" / "candidates" / PHASE23K_SLUG
    data_dir = candidate_dir / "data"
    runtime_dir = candidate_dir / "runtime"
    transcript_dir = candidate_dir / "transcripts"
    dbf_dir = candidate_dir / "dbf"
    indexes_dir = candidate_dir / "indexes"
    lmdb_dir = candidate_dir / "lmdb"
    for d in [data_dir, runtime_dir, transcript_dir, dbf_dir, indexes_dir, lmdb_dir]:
        d.mkdir(parents=True, exist_ok=True)

    row_sets: Dict[str, List[Dict[str, str]]] = {}
    missing_inputs: List[str] = []
    for spec in TABLE_SOURCES:
        src = (phase23j_dir / spec["csv"]) if phase23j_dir else Path("__missing__")
        rows = read_csv(src)
        if not rows:
            missing_inputs.append(spec["csv"])
        table = spec["table"]
        row_sets[table] = rows
        write_csv(data_dir / f"phase23k_input_{table.lower()}.csv", rows)

    created_at = now_utc()
    run_id = "PHASE23K-" + stable_hash(str(candidate_dir) + created_at)
    dts_text = build_dts(candidate_dir, dbf_dir, indexes_dir, lmdb_dir, row_sets)
    dts_path = runtime_dir / "phase23k_build_help_locale_candidate_tables.dts"
    dts_path.write_text(dts_text, encoding="utf-8", newline="\n")

    transcript_path = transcript_dir / "phase23k_build_help_locale_candidate_tables_transcript.txt"
    run_command = f"DOTSCRIPT TRACE {rel(dts_path, repo_root)} OUT {rel(transcript_path, repo_root)}"

    table_counts = {spec["table"]: len(row_sets.get(spec["table"], [])) for spec in TABLE_SOURCES}
    total_rows = sum(table_counts.values())
    boundary = {
        "source_files_written": 0,
        "active_help_dbf_written": 0,
        "active_help_cdx_written": 0,
        "active_help_lmdb_written": 0,
        "cmdhelp_behavior_changed": 0,
        "cmdhelpchk_behavior_changed": 0,
        "maint_behavior_changed": 0,
        "bbox_behavior_changed": 0,
        "active_locale_catalog_mutation": 0,
        "candidate_script_written": 1,
        "candidate_data_copied": 1,
        "runtime_execution_by_python": 0,
    }
    manifest = {
        "status": STATUS,
        "run_id": run_id,
        "created_at": created_at,
        "repo_root": str(repo_root),
        "candidate_dir": rel(candidate_dir, repo_root),
        "phase23j_dir": rel(phase23j_dir, repo_root) if phase23j_dir else None,
        "phase23j_green": phase23j_green,
        "missing_inputs": missing_inputs,
        "table_counts": table_counts,
        "total_candidate_rows_planned": total_rows,
        "candidate_tables": [spec["table"] for spec in TABLE_SOURCES],
        "primary_tags": {spec["table"]: spec["primary_tag"] for spec in TABLE_SOURCES},
        "candidate_paths": {
            "dbf": rel(dbf_dir, repo_root),
            "indexes": rel(indexes_dir, repo_root),
            "lmdb": rel(lmdb_dir, repo_root),
            "runtime_script": rel(dts_path, repo_root),
            "expected_transcript": rel(transcript_path, repo_root),
        },
        "manual_run_command": run_command,
        "boundary": boundary,
        "next_gate": NEXT_GATE,
        "final_green_status_after_review": FINAL_GREEN_STATUS,
        "notes": [
            "Python only stages candidate data, runtime scripts, and manifests.",
            "Run the generated DOTSCRIPT command in DotTalk++ to create candidate DBF/CDX/LMDB artifacts.",
            "BUILDLMDB uses CLEAN TINY YES because these are small metadata proof tables.",
            "Generated DotScript includes a final blank line so the last command is executed.",
        ],
    }
    (candidate_dir / "phase23k_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    md = [
        f"# {STATUS}",
        "",
        f"Run ID: `{run_id}`",
        f"Created at: `{created_at}`",
        f"Candidate dir: `{rel(candidate_dir, repo_root)}`",
        "",
        "## Purpose",
        "",
        "Stage a candidate-only DotScript build/readback proof for HELP locale companion DBF/CDX/LMDB artifacts.",
        "",
        "## Manual DotTalk++ run command",
        "",
        "Paste this from the DotTalk++ prompt after staging:",
        "",
        "```text",
        run_command,
        "```",
        "",
        "Then run the review script:",
        "",
        "```powershell",
        "$py12 = \"D:\\code\\ccode\\build\\vcpkg_installed\\x64-windows\\tools\\python3\\python.exe\"",
        "& $py12 .\\tools\\maintenance\\phase23k_review_help_locale_candidate_build_proof.py --repo-root .",
        "```",
        "",
        "## Candidate row counts",
        "",
    ]
    for table, count in table_counts.items():
        md.append(f"- `{table}`: {count}")
    md.extend([
        f"- `total_candidate_rows_planned`: {total_rows}",
        "",
        "## Boundary",
        "",
    ])
    for key, value in boundary.items():
        md.append(f"- `{key}`: {value}")
    md.extend(["", "## Next gate", "", f"`{NEXT_GATE}`", ""])
    (candidate_dir / "PHASE23K_HELP_LOCALE_CANDIDATE_DBF_CDX_LMDB_BUILD_PROOF_STAGING.md").write_text("\n".join(md), encoding="utf-8")

    print(STATUS)
    print(f"candidate_dir: {rel(candidate_dir, repo_root)}")
    print(f"phase23j_green: {phase23j_green}")
    print(f"candidate_tables: {len(TABLE_SOURCES)}")
    print(f"candidate_rows_planned: {total_rows}")
    for table, count in table_counts.items():
        print(f"{table.lower()}_rows: {count}")
    print(f"candidate_dts: {rel(dts_path, repo_root)}")
    print(f"expected_transcript: {rel(transcript_path, repo_root)}")
    print(f"manual_run_command: {run_command}")
    for key in [
        "source_files_written", "active_help_dbf_written", "active_help_cdx_written", "active_help_lmdb_written",
        "cmdhelp_behavior_changed", "cmdhelpchk_behavior_changed", "maint_behavior_changed", "bbox_behavior_changed",
        "runtime_execution_by_python",
    ]:
        print(f"{key}: {boundary[key]}")
    print(f"next_gate: {NEXT_GATE}")
    if missing_inputs:
        print("review_warning: missing PHASE23J inputs: " + ", ".join(missing_inputs))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
