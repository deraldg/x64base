#!/usr/bin/env python3
"""PHASE23O active HELP locale readback proof staging.

Stages a read-only retained DotScript (.dts) probe that reads the promoted
active HELP locale companion tables through the active HELP DBF/CDX/LMDB roots.

This phase proves the PHASE23N-promoted active sidecar artifacts without
changing CMDHELP, CMDHELPCHK, MAINT, BBOX, source, or active HELP data.

Contract:
- retained DotScript extension: .dts
- COUNT for row-count proof
- SMARTLIST n for bounded human-readable readback
- TUPLE * --VALUES-ONLY and compact TUPLE for deterministic row proof
- no LIST, no LIST ALL, no SMARTLIST ALL
- reset paths back to default data roots at script end
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from datetime import datetime, timezone

PHASE = "PHASE23O"
STATUS = "PHASE23O_ACTIVE_HELP_LOCALE_READBACK_STAGING_GREEN_MANUAL_DOTSCRIPT_REQUIRED"
CANDIDATE_NAME = "PHASE23O-ACTIVE-HELP-LOCALE-READBACK-PROOF"
PHASE23N_NAME = "PHASE23N-HELP-LOCALE-ACTIVE-PROMOTION-EXECUTION-STAGING"
PHASE23K_NAME = "PHASE23K-HELP-LOCALE-CANDIDATE-DBF-CDX-LMDB-BUILD-PROOF"

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


def phase23n_green(repo: Path) -> int:
    p = repo / "docs" / "locale" / "candidates" / PHASE23N_NAME / "manifests" / "phase23n_help_locale_active_promotion_review_manifest.json"
    if not p.exists():
        return 0
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return 0
    return int(data.get("status") == "PHASE23N_HELP_LOCALE_ACTIVE_PROMOTION_REVIEW_GREEN_ACTIVE_ARTIFACTS_MATCH_CANDIDATE" and data.get("active_promotion_executed") == 1)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", default=".")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    candidate_dir = repo / "docs" / "locale" / "candidates" / CANDIDATE_NAME
    phase23n_dir = repo / "docs" / "locale" / "candidates" / PHASE23N_NAME
    phase23k_dir = repo / "docs" / "locale" / "candidates" / PHASE23K_NAME
    runtime_dir = candidate_dir / "runtime"
    transcript_dir = candidate_dir / "transcripts"
    report_dir = candidate_dir / "reports"
    manifest_dir = candidate_dir / "manifests"
    for d in (runtime_dir, transcript_dir, report_dir, manifest_dir):
        d.mkdir(parents=True, exist_ok=True)

    dts = runtime_dir / "phase23o_active_help_locale_count_smartlist_tuple_probe.dts"
    transcript = transcript_dir / "phase23o_active_help_locale_count_smartlist_tuple_probe_transcript.txt"

    active_dbf = repo / "dottalkpp" / "data" / "HELP"
    active_idx = repo / "dottalkpp" / "data" / "INDEXES" / "HELP"
    active_lmdb = repo / "dottalkpp" / "data" / "LMDB" / "HELP"

    default_dbf = repo / "dottalkpp" / "data" / "dbf"
    default_idx = repo / "dottalkpp" / "data" / "indexes"
    default_lmdb = repo / "dottalkpp" / "data" / "lmdb"

    lines: list[str] = []
    lines += [
        "ECHO ON",
        "SET PAGING OFF",
        "ECHO PHASE23O_DOTSCRIPT_START",
        "ECHO PHASE23O_SCOPE_READONLY_ACTIVE_HELP_LOCALE_TABLES_ONLY",
        "ECHO PHASE23O_COUNT_SMARTLIST_N_TUPLE_CONTRACT",
        "ECHO PHASE23O_NO_LIST_NO_SMARTLIST_ALL",
        f"ECHO PHASE23O_SAMPLE_LOCALE_{SAMPLE_LOCALE}",
        f"SETPATH DBF {winpath(active_dbf)}",
        f"SETPATH INDEXES {winpath(active_idx)}",
        f"SETPATH LMDB {winpath(active_lmdb)}",
        "WORKSPACE CLOSE",
        "WORKSPACE OPEN DBF CDX",
    ]
    for topic in SAMPLE_TOPICS:
        marker = topic.replace("|", "_").replace(" ", "_")
        lines.append(f"ECHO PHASE23O_SAMPLE_TOPIC_{marker}_{SAMPLE_LOCALE}")

    for table, n in TABLES:
        lines += [
            f"ECHO PHASE23O_ACTIVE_READBACK_{table}",
            f"SELECT {table}",
            "AREA",
            f"SET INDEX TO {table}",
            "CDX INFO",
            "SET ORDER TO TAG TOPICKEY",
            "ASCEND",
            "TOP",
            "COUNT",
            f"SMARTLIST {n}",
            f"ECHO PHASE23O_TUPLE_{table}_TOP_VALUES_ONLY",
            "TUPLE * --VALUES-ONLY",
            f"ECHO PHASE23O_TUPLE_{table}_COMPACT",
            "TUPLE TOPICKEY,LOCALE_ID,TRANSL_STATUS,REVIEW_STATUS --VALUES-ONLY",
            "SET ORDER TO 0",
        ]

    lines += [
        "WORKSPACE CLOSE",
        "ECHO PHASE23O_PATH_RESET_TO_DEFAULT_DATA_ROOTS",
        f"SETPATH DBF {winpath(default_dbf)}",
        f"SETPATH INDEXES {winpath(default_idx)}",
        f"SETPATH LMDB {winpath(default_lmdb)}",
        "ECHO PHASE23O_DOTSCRIPT_END",
        "",
    ]
    dts.write_text("\n".join(lines), encoding="utf-8")

    active_dbf_exists = sum(1 for t, _ in TABLES if (active_dbf / f"{t}.dbf").exists())
    active_cdx_exists = sum(1 for t, _ in TABLES if (active_idx / f"{t}.cdx").exists())
    active_lmdb_exists = sum(1 for t, _ in TABLES if (active_lmdb / f"{t}.cdx.d").exists())

    manifest = {
        "phase": PHASE,
        "status": STATUS,
        "created_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "candidate_dir": str(candidate_dir.relative_to(repo)),
        "phase23n_candidate_dir": str(phase23n_dir.relative_to(repo)),
        "phase23k_candidate_dir": str(phase23k_dir.relative_to(repo)),
        "phase23n_green": phase23n_green(repo),
        "active_roots": {
            "dbf": str(active_dbf.relative_to(repo)),
            "indexes": str(active_idx.relative_to(repo)),
            "lmdb": str(active_lmdb.relative_to(repo)),
        },
        "active_dbf_exists": f"{active_dbf_exists}/4",
        "active_cdx_exists": f"{active_cdx_exists}/4",
        "active_lmdb_exists": f"{active_lmdb_exists}/4",
        "tables": [t for t, _ in TABLES],
        "smartlist_limits": {t: n for t, n in TABLES},
        "sample_locale": SAMPLE_LOCALE,
        "sample_topics": SAMPLE_TOPICS,
        "retained_dotscript": str(dts.relative_to(repo)),
        "expected_transcript": str(transcript.relative_to(repo)),
        "contract": [
            "Read from active HELP locale DBF/CDX/LMDB roots",
            "Retained DotScript uses .dts extension",
            "SET INDEX TO <table>",
            "SET ORDER TO TAG TOPICKEY",
            "COUNT for row-count proof",
            "SMARTLIST n for bounded human readback",
            "TUPLE * --VALUES-ONLY for deterministic current-row proof",
            "Compact TUPLE field set for parse-friendly row proof",
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
        "next_gate": "HOLD_OR_RUN_PHASE23O_DOTSCRIPT_AND_REVIEW_TRANSCRIPT",
    }
    (manifest_dir / "phase23o_active_help_locale_readback_staging_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    manual_run_command = f"DOTSCRIPT TRACE {winpath(dts)} OUT {winpath(transcript)}"
    print(STATUS)
    print(f"candidate_dir: {candidate_dir.relative_to(repo)}")
    print(f"phase23n_candidate_dir: {phase23n_dir.relative_to(repo)}")
    print(f"phase23k_candidate_dir: {phase23k_dir.relative_to(repo)}")
    print(f"phase23n_green: {manifest['phase23n_green']}")
    print("read_scope: ACTIVE_HELP_LOCALE_ROOTS")
    print(f"active_roots: {active_dbf.relative_to(repo)},{active_idx.relative_to(repo)},{active_lmdb.relative_to(repo)}")
    print(f"active_dbf_exists: {active_dbf_exists}/4")
    print(f"active_cdx_exists: {active_cdx_exists}/4")
    print(f"active_lmdb_exists: {active_lmdb_exists}/4")
    print(f"candidate_tables: {len(TABLES)}")
    print("readback_contract: COUNT_PLUS_SMARTLIST_N_PLUS_TUPLE_VALUES_ONLY")
    print("retained_dotscript_extension: .dts")
    print("list_commands_planned: 0")
    print("smartlist_all_commands_planned: 0")
    print(f"sample_locale: {SAMPLE_LOCALE}")
    print(f"sample_topics: {','.join(SAMPLE_TOPICS)}")
    print(f"smartlist_limits: {','.join([f'{t}={n}' for t,n in TABLES])}")
    print(f"retained_dotscript: {dts.relative_to(repo)}")
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
    print("next_gate: HOLD_OR_RUN_PHASE23O_DOTSCRIPT_AND_REVIEW_TRANSCRIPT")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
