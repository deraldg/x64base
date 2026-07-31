#!/usr/bin/env python3
"""Stage PHASE23KR candidate-only CDX tag creation and LMDB clean rebuild proof.

This script writes only candidate proof artifacts under docs/locale/candidates.
It does not execute DotTalk++ and does not mutate active HELP/CMDHELP/source data.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

PHASE23K = "PHASE23K-HELP-LOCALE-CANDIDATE-DBF-CDX-LMDB-BUILD-PROOF"
PHASE23KR = "PHASE23KR-HELP-LOCALE-ALL-TABLE-CDX-TAG-LMDB-CLEAN-REBUILD-PROOF"
STATUS = "PHASE23KR_HELP_LOCALE_ALL_TABLE_CDX_TAG_CREATE_AND_LMDB_CLEAN_REBUILD_STAGING_GREEN_MANUAL_DOTSCRIPT_REQUIRED"

TABLES = [
    "HELP_TOPIC_LOCALE",
    "HELP_SECTION_LOCALE",
    "HELP_LINE_LOCALE",
    "HELP_ARTIFACT_LOCALE",
]

TAGS = ["RUN_ID", "TOPICKEY"]


def win(p: Path) -> str:
    return str(p).replace("/", "\\")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", default=".")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    k_dir = repo / "docs" / "locale" / "candidates" / PHASE23K
    kr_dir = repo / "docs" / "locale" / "candidates" / PHASE23KR
    runtime_dir = kr_dir / "runtime"
    transcript_dir = kr_dir / "transcripts"
    reports_dir = kr_dir / "reports"
    for d in (runtime_dir, transcript_dir, reports_dir):
        d.mkdir(parents=True, exist_ok=True)

    dbf_dir = k_dir / "dbf"
    idx_dir = k_dir / "indexes"
    lmdb_dir = k_dir / "lmdb"

    missing = []
    for d in (dbf_dir, idx_dir, lmdb_dir):
        if not d.exists():
            missing.append(win(d))
    for table in TABLES:
        if not (dbf_dir / f"{table}.dbf").exists():
            missing.append(win(dbf_dir / f"{table}.dbf"))

    if missing:
        print("PHASE23KR_HELP_LOCALE_ALL_TABLE_REPAIR_STAGING_BLOCKED_MISSING_PHASE23K_CANDIDATES")
        print("missing:")
        for item in missing:
            print(f"  {item}")
        return 2

    dts = runtime_dir / "phase23kr_repair_help_locale_candidate_lmdb_all_tables.dts"
    transcript = transcript_dir / "phase23kr_repair_help_locale_candidate_lmdb_all_tables_transcript.txt"

    lines: list[str] = []
    lines.extend([
        "ECHO ON",
        "SET PAGING OFF",
        "ECHO PHASE23KR_DOTSCRIPT_START",
        f"SETPATH DBF {win(dbf_dir)}",
        f"SETPATH INDEXES {win(idx_dir)}",
        f"SETPATH LMDB {win(lmdb_dir)}",
        "WORKSPACE CLOSE",
        "WORKSPACE OPEN DBF CDX",
        "STRUCT ALL INDEXES",
    ])

    for table in TABLES:
        lines.append(f"ECHO PHASE23KR_REPAIR_{table}")
        lines.append(f"SELECT {table}")
        lines.append("AREA")
        lines.append("CDX INFO")
        for tag in TAGS:
            lines.append(f"CDX ADDTAG {tag}")
        lines.append("CDX INFO")
        lines.append(f"SET INDEX TO {table}")
        lines.append("SET ORDER TO TAG TOPICKEY")
        lines.append("BUILDLMDB CLEAN YES")
        lines.append(f"SET INDEX TO {table}")
        lines.append("SET ORDER TO TAG TOPICKEY")
        lines.append("ASCEND")
        lines.append("TOP")
        lines.append("LIST 5")
        lines.append("DESC")
        lines.append("TOP")
        lines.append("LIST 5")
        lines.append("ASCEND")
        lines.append("SET ORDER TO 0")

    lines.extend([
        "ECHO PHASE23KR_DOTSCRIPT_END",
        "WORKSPACE CLOSE",
        "",
    ])
    dts.write_text("\n".join(lines), encoding="utf-8")

    manifest = {
        "status": STATUS,
        "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "repo_root": win(repo),
        "phase23k_candidate_dir": win(k_dir),
        "candidate_dir": win(kr_dir.relative_to(repo)),
        "candidate_dts": win(dts.relative_to(repo)),
        "expected_transcript": win(transcript.relative_to(repo)),
        "candidate_tables": TABLES,
        "tags_to_create": TAGS,
        "candidate_dbf_expected": len(TABLES),
        "candidate_cdx_expected": len(TABLES),
        "candidate_lmdb_expected": len(TABLES),
        "source_files_written": 0,
        "active_help_dbf_written": 0,
        "active_help_cdx_written": 0,
        "active_help_lmdb_written": 0,
        "cmdhelp_behavior_changed": 0,
        "cmdhelpchk_behavior_changed": 0,
        "maint_behavior_changed": 0,
        "bbox_behavior_changed": 0,
        "runtime_execution_by_python": 0,
        "next_gate": "HOLD_OR_RUN_PHASE23KR_DOTSCRIPT_AND_REVIEW_TRANSCRIPT",
    }
    (reports_dir / "phase23kr_staging_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    command = f"DOTSCRIPT TRACE {win(dts)} OUT {win(transcript)}"

    print(STATUS)
    print(f"candidate_dir: {win(kr_dir.relative_to(repo))}")
    print(f"phase23k_candidate_dir: {win(k_dir.relative_to(repo))}")
    print(f"candidate_tables: {len(TABLES)}")
    print(f"tags_to_create: {','.join(TAGS)}")
    print(f"candidate_dts: {win(dts.relative_to(repo))}")
    print(f"expected_transcript: {win(transcript.relative_to(repo))}")
    print(f"manual_run_command: {command}")
    print("source_files_written: 0")
    print("active_help_dbf_written: 0")
    print("active_help_cdx_written: 0")
    print("active_help_lmdb_written: 0")
    print("cmdhelp_behavior_changed: 0")
    print("cmdhelpchk_behavior_changed: 0")
    print("maint_behavior_changed: 0")
    print("bbox_behavior_changed: 0")
    print("runtime_execution_by_python: 0")
    print("next_gate: HOLD_OR_RUN_PHASE23KR_DOTSCRIPT_AND_REVIEW_TRANSCRIPT")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
