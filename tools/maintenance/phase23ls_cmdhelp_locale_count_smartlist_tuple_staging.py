#!/usr/bin/env python3
"""PHASE23LS CMDHELP locale COUNT + SMARTLIST n + TUPLE readback staging.

Stages a read-only DotScript (.dts) probe that reads the PHASE23K/PHASE23KR
candidate HELP locale companion tables through the candidate DBF/CDX/LMDB roots.

This pass intentionally avoids LIST/LIST ALL and avoids full SMARTLIST ALL output.
It uses COUNT for full-row cardinality proof, SMARTLIST n for compact human
readback, and TUPLE * --VALUES-ONLY for deterministic current-row machine proof.

This package does not execute DotTalk++, does not write active HELP artifacts,
and does not change source or runtime behavior.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from datetime import datetime, timezone

PHASE = "PHASE23LS"
STATUS = "PHASE23LS_CMDHELP_LOCALE_COUNT_SMARTLIST_TUPLE_STAGING_GREEN_MANUAL_DOTSCRIPT_REQUIRED"
CANDIDATE_NAME = "PHASE23LS-CMDHELP-LOCALE-COUNT-SMARTLIST-TUPLE-READBACK-PROOF"
PHASE23K_NAME = "PHASE23K-HELP-LOCALE-CANDIDATE-DBF-CDX-LMDB-BUILD-PROOF"
PHASE23KR_NAME = "PHASE23KR-HELP-LOCALE-ALL-TABLE-CDX-TAG-LMDB-CLEAN-REBUILD-PROOF"

TABLES = [
    ("HELP_TOPIC_LOCALE", 10),
    ("HELP_SECTION_LOCALE", 10),
    ("HELP_LINE_LOCALE", 30),
    ("HELP_ARTIFACT_LOCALE", 10),
]
SAMPLE_TOPICS = ["DOT|ABOUT", "DOT|AREA"]
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

    dts = runtime_dir / "phase23ls_cmdhelp_locale_count_smartlist_tuple_probe.dts"
    transcript = transcript_dir / "phase23ls_cmdhelp_locale_count_smartlist_tuple_probe_transcript.txt"

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
        "ECHO PHASE23LS_DOTSCRIPT_START",
        "ECHO PHASE23LS_SCOPE_READONLY_CANDIDATE_TABLES_ONLY",
        "ECHO PHASE23LS_COUNT_SMARTLIST_N_TUPLE_CONTRACT",
        "ECHO PHASE23LS_NO_LIST_NO_SMARTLIST_ALL",
        f"ECHO PHASE23LS_SAMPLE_LOCALE_{SAMPLE_LOCALE}",
        f"SETPATH DBF {winpath(dbf_root)}",
        f"SETPATH INDEXES {winpath(idx_root)}",
        f"SETPATH LMDB {winpath(lmdb_root)}",
        "WORKSPACE CLOSE",
        "WORKSPACE OPEN DBF CDX",
    ]
    for topic in SAMPLE_TOPICS:
        marker = topic.replace("|", "_").replace(" ", "_")
        lines.append(f"ECHO PHASE23LS_SAMPLE_TOPIC_{marker}_{SAMPLE_LOCALE}")

    for table, n in TABLES:
        lines += [
            f"ECHO PHASE23LS_READBACK_{table}",
            f"SELECT {table}",
            "AREA",
            f"SET INDEX TO {table}",
            "CDX INFO",
            "SET ORDER TO TAG TOPICKEY",
            "ASCEND",
            "TOP",
            "COUNT",
            f"SMARTLIST {n}",
            f"ECHO PHASE23LS_TUPLE_{table}_TOP_VALUES_ONLY",
            "TUPLE * --VALUES-ONLY",
            f"ECHO PHASE23LS_TUPLE_{table}_COMPACT",
            "TUPLE TOPICKEY,LOCALE_ID,TRANSL_STATUS,REVIEW_STATUS --VALUES-ONLY",
            "SET ORDER TO 0",
        ]

    lines += [
        "WORKSPACE CLOSE",
        "ECHO PHASE23LS_PATH_RESET_TO_DEFAULT_DATA_ROOTS",
        f"SETPATH DBF {winpath(default_dbf)}",
        f"SETPATH INDEXES {winpath(default_idx)}",
        f"SETPATH LMDB {winpath(default_lmdb)}",
        "ECHO PHASE23LS_DOTSCRIPT_END",
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
        "candidate_tables": [t for t, _ in TABLES],
        "smartlist_limits": {t: n for t, n in TABLES},
        "sample_locale": SAMPLE_LOCALE,
        "sample_topics": SAMPLE_TOPICS,
        "dts": str(dts.relative_to(repo)),
        "expected_transcript": str(transcript.relative_to(repo)),
        "contract": [
            "Retained DotScript file uses .dts extension",
            "SET INDEX TO <table>",
            "SET ORDER TO TAG TOPICKEY",
            "COUNT for full-row cardinality proof",
            "SMARTLIST n for compact human-readable readback",
            "TUPLE * --VALUES-ONLY for deterministic current-row proof",
            "Optional compact TUPLE field set for parse-friendly current-row proof",
            "No LIST or LIST ALL",
            "No SMARTLIST ALL",
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
        "next_gate": "HOLD_OR_RUN_PHASE23LS_DOTSCRIPT_AND_REVIEW_TRANSCRIPT",
    }
    (report_dir / "phase23ls_staging_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    manual_run_command = f"DOTSCRIPT TRACE {winpath(dts)} OUT {winpath(transcript)}"
    print(STATUS)
    print(f"candidate_dir: {candidate_dir.relative_to(repo)}")
    print(f"phase23k_candidate_dir: {phase23k_dir.relative_to(repo)}")
    print(f"phase23kr_candidate_dir: {phase23kr_dir.relative_to(repo)}")
    print(f"candidate_tables: {len(TABLES)}")
    print("readback_contract: COUNT_PLUS_SMARTLIST_N_PLUS_TUPLE_VALUES_ONLY")
    print("retained_dotscript_extension: .dts")
    print("list_commands_planned: 0")
    print("smartlist_all_commands_planned: 0")
    print(f"sample_locale: {SAMPLE_LOCALE}")
    print(f"sample_topics: {','.join(SAMPLE_TOPICS)}")
    print(f"smartlist_limits: {','.join([f'{t}={n}' for t,n in TABLES])}")
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
    print("next_gate: HOLD_OR_RUN_PHASE23LS_DOTSCRIPT_AND_REVIEW_TRANSCRIPT")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
