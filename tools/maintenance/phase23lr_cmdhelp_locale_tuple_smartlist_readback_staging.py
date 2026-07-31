#!/usr/bin/env python3
"""PHASE23LR CMDHELP locale tuple + SMARTLIST readback proof staging.

Stages a read-only DotScript probe that reads the PHASE23K/PHASE23KR candidate
HELP locale companion tables through the candidate DBF/CDX/LMDB roots.

This package does not execute DotTalk++, does not write active HELP artifacts,
and does not change source or runtime behavior.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from datetime import datetime, timezone

PHASE = "PHASE23LR"
STATUS = "PHASE23LR_CMDHELP_LOCALE_TUPLE_SMARTLIST_READBACK_STAGING_GREEN_MANUAL_DOTSCRIPT_REQUIRED"
CANDIDATE_NAME = "PHASE23LR-CMDHELP-LOCALE-TUPLE-SMARTLIST-READBACK-PROOF"
PHASE23K_NAME = "PHASE23K-HELP-LOCALE-CANDIDATE-DBF-CDX-LMDB-BUILD-PROOF"
PHASE23KR_NAME = "PHASE23KR-HELP-LOCALE-ALL-TABLE-CDX-TAG-LMDB-CLEAN-REBUILD-PROOF"

TABLES = [
    "HELP_TOPIC_LOCALE",
    "HELP_SECTION_LOCALE",
    "HELP_LINE_LOCALE",
    "HELP_ARTIFACT_LOCALE",
]
SAMPLE_TOPICS = ["DOT|AREA", "DOT|CMDHELP", "DOT|SET LANGUAGE", "DOT|SET LOCALE"]
SAMPLE_LOCALE = "es"


def winpath(p: Path) -> str:
    return str(p.resolve()).replace("/", "\\")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", default=".")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    phase23k_dir = repo / "docs" / "locale" / "candidates" / PHASE23K_NAME
    phase23kr_dir = repo / "docs" / "locale" / "candidates" / PHASE23KR_NAME
    candidate_dir = repo / "docs" / "locale" / "candidates" / CANDIDATE_NAME
    runtime_dir = candidate_dir / "runtime"
    transcript_dir = candidate_dir / "transcripts"
    report_dir = candidate_dir / "reports"
    for d in (runtime_dir, transcript_dir, report_dir):
        d.mkdir(parents=True, exist_ok=True)

    dts = runtime_dir / "phase23lr_cmdhelp_locale_tuple_smartlist_readback_probe.dts"
    transcript = transcript_dir / "phase23lr_cmdhelp_locale_tuple_smartlist_readback_probe_transcript.txt"

    dbf_root = phase23k_dir / "dbf"
    idx_root = phase23k_dir / "indexes"
    lmdb_root = phase23k_dir / "lmdb"

    default_dbf = repo / "dottalkpp" / "data" / "dbf"
    default_idx = repo / "dottalkpp" / "data" / "indexes"
    default_lmdb = repo / "dottalkpp" / "data" / "lmdb"

    lines: list[str] = []
    lines += [
        "ECHO ON",
        "SET PAGING OFF",
        "ECHO PHASE23LR_DOTSCRIPT_START",
        "ECHO PHASE23LR_SCOPE_READONLY_CANDIDATE_TABLES_ONLY",
        "ECHO PHASE23LR_SMARTLIST_TUPLE_CONTRACT",
        f"ECHO PHASE23LR_SAMPLE_LOCALE_{SAMPLE_LOCALE}",
        f"SETPATH DBF {winpath(dbf_root)}",
        f"SETPATH INDEXES {winpath(idx_root)}",
        f"SETPATH LMDB {winpath(lmdb_root)}",
        "WORKSPACE CLOSE",
        "WORKSPACE OPEN DBF CDX",
    ]
    for topic in SAMPLE_TOPICS:
        marker = topic.replace("|", "_").replace(" ", "_")
        lines.append(f"ECHO PHASE23LR_SAMPLE_TOPIC_{marker}_{SAMPLE_LOCALE}")

    for table in TABLES:
        lines += [
            f"ECHO PHASE23LR_READBACK_{table}",
            f"SELECT {table}",
            "AREA",
            f"SET INDEX TO {table}",
            "CDX INFO",
            "SET ORDER TO TAG TOPICKEY",
            "ASCEND",
            "TOP",
            "SMARTLIST ALL",
            f"ECHO PHASE23LR_TUPLE_{table}_TOP",
            "TUPLE * --VALUES-ONLY",
            "SET ORDER TO 0",
        ]

    lines += [
        "WORKSPACE CLOSE",
        "ECHO PHASE23LR_PATH_RESET_TO_DEFAULT_DATA_ROOTS",
        f"SETPATH DBF {winpath(default_dbf)}",
        f"SETPATH INDEXES {winpath(default_idx)}",
        f"SETPATH LMDB {winpath(default_lmdb)}",
        "ECHO PHASE23LR_DOTSCRIPT_END",
        "",
    ]
    dts.write_text("\n".join(lines), encoding="utf-8")

    manifest = {
        "phase": PHASE,
        "status": STATUS,
        "created_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "candidate_dir": str(candidate_dir.relative_to(repo)),
        "phase23k_candidate_dir": str(phase23k_dir.relative_to(repo)),
        "phase23kr_candidate_dir": str(phase23kr_dir.relative_to(repo)),
        "candidate_tables": TABLES,
        "sample_locale": SAMPLE_LOCALE,
        "sample_topics": SAMPLE_TOPICS,
        "dts": str(dts.relative_to(repo)),
        "expected_transcript": str(transcript.relative_to(repo)),
        "contract": [
            "SET INDEX TO <table>",
            "SET ORDER TO TAG TOPICKEY",
            "SMARTLIST ALL for broad human-readable readback",
            "TUPLE * --VALUES-ONLY for deterministic current-row proof",
            "Reset DBF/INDEXES/LMDB paths back to default data roots at script end",
        ],
        "source_files_written": 0,
        "active_help_dbf_written": 0,
        "active_help_cdx_written": 0,
        "active_help_lmdb_written": 0,
        "cmdhelp_behavior_changed": 0,
        "cmdhelpchk_behavior_changed": 0,
        "maint_behavior_changed": 0,
        "bbox_behavior_changed": 0,
        "runtime_execution_by_python": 0,
        "next_gate": "HOLD_OR_RUN_PHASE23LR_DOTSCRIPT_AND_REVIEW_TRANSCRIPT",
    }
    (report_dir / "phase23lr_staging_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    manual_run_command = f"DOTSCRIPT TRACE {winpath(dts)} OUT {winpath(transcript)}"
    print(STATUS)
    print(f"candidate_dir: {candidate_dir.relative_to(repo)}")
    print(f"phase23k_candidate_dir: {phase23k_dir.relative_to(repo)}")
    print(f"phase23kr_candidate_dir: {phase23kr_dir.relative_to(repo)}")
    print(f"candidate_tables: {len(TABLES)}")
    print("readback_contract: SMARTLIST_ALL_PLUS_TUPLE_VALUES_ONLY")
    print(f"sample_locale: {SAMPLE_LOCALE}")
    print(f"sample_topics: {','.join(SAMPLE_TOPICS)}")
    print(f"candidate_dts: {dts.relative_to(repo)}")
    print(f"expected_transcript: {transcript.relative_to(repo)}")
    print(f"manual_run_command: {manual_run_command}")
    print("source_files_written: 0")
    print("active_help_dbf_written: 0")
    print("active_help_cdx_written: 0")
    print("active_help_lmdb_written: 0")
    print("cmdhelp_behavior_changed: 0")
    print("cmdhelpchk_behavior_changed: 0")
    print("maint_behavior_changed: 0")
    print("bbox_behavior_changed: 0")
    print("runtime_execution_by_python: 0")
    print("next_gate: HOLD_OR_RUN_PHASE23LR_DOTSCRIPT_AND_REVIEW_TRANSCRIPT")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
