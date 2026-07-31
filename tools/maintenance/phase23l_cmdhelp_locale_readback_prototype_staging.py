#!/usr/bin/env python3
"""Stage PHASE23L CMDHELP locale readback prototype artifacts.

This stages a read-only DotScript probe that opens the PHASE23K candidate
HELP locale companion tables after PHASE23KR repaired their CDX/LMDB tags.
The probe does not mutate active HELP, CMDHELP, CMDHELPCHK, source, MAINT, or BBOX.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

PHASE23K = "PHASE23K-HELP-LOCALE-CANDIDATE-DBF-CDX-LMDB-BUILD-PROOF"
PHASE23KR = "PHASE23KR-HELP-LOCALE-ALL-TABLE-CDX-TAG-LMDB-CLEAN-REBUILD-PROOF"
PHASE23L = "PHASE23L-CMDHELP-LOCALE-READBACK-PROTOTYPE"
STATUS = "PHASE23L_CMDHELP_LOCALE_READBACK_PROTOTYPE_STAGING_GREEN_MANUAL_DOTSCRIPT_REQUIRED"

TABLES = [
    "HELP_TOPIC_LOCALE",
    "HELP_SECTION_LOCALE",
    "HELP_LINE_LOCALE",
    "HELP_ARTIFACT_LOCALE",
]
SAMPLE_TOPICS = [
    "DOT|AREA",
    "DOT|CMDHELP",
    "DOT|SET LANGUAGE",
    "DOT|SET LOCALE",
]
SAMPLE_LOCALE = "es"


def win(p: Path) -> str:
    return str(p).replace("/", "\\")


def relwin(repo: Path, p: Path) -> str:
    try:
        return win(p.relative_to(repo))
    except ValueError:
        return win(p)


def read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", default=".")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    k_dir = repo / "docs" / "locale" / "candidates" / PHASE23K
    kr_dir = repo / "docs" / "locale" / "candidates" / PHASE23KR
    l_dir = repo / "docs" / "locale" / "candidates" / PHASE23L
    runtime_dir = l_dir / "runtime"
    transcript_dir = l_dir / "transcripts"
    reports_dir = l_dir / "reports"
    for d in (runtime_dir, transcript_dir, reports_dir):
        d.mkdir(parents=True, exist_ok=True)

    kr_manifest = read_json(kr_dir / "reports" / "phase23kr_review_manifest.json")
    phase23kr_green = int(kr_manifest.get("status") == "PHASE23KR_HELP_LOCALE_ALL_TABLE_CDX_TAG_CREATE_AND_LMDB_CLEAN_REBUILD_PROOF_GREEN")

    dbf_dir = k_dir / "dbf"
    idx_dir = k_dir / "indexes"
    lmdb_dir = k_dir / "lmdb"
    missing: list[str] = []
    for d in (dbf_dir, idx_dir, lmdb_dir):
        if not d.exists():
            missing.append(win(d))
    for table in TABLES:
        for suffix, root in [(".dbf", dbf_dir), (".cdx", idx_dir), (".cdx.d", lmdb_dir)]:
            p = root / f"{table}{suffix}"
            if not p.exists():
                missing.append(win(p))

    if missing:
        print("PHASE23L_CMDHELP_LOCALE_READBACK_PROTOTYPE_STAGING_BLOCKED_MISSING_CANDIDATE_ARTIFACTS")
        print(f"phase23kr_green: {phase23kr_green}")
        print("missing:")
        for item in missing:
            print(f"  {item}")
        return 2

    dts = runtime_dir / "phase23l_cmdhelp_locale_readback_probe.dts"
    transcript = transcript_dir / "phase23l_cmdhelp_locale_readback_probe_transcript.txt"

    lines: list[str] = []
    lines.extend([
        "ECHO ON",
        "SET PAGING OFF",
        "ECHO PHASE23L_DOTSCRIPT_START",
        "ECHO PHASE23L_SCOPE_READONLY_CANDIDATE_TABLES_ONLY",
        f"ECHO PHASE23L_SAMPLE_LOCALE_{SAMPLE_LOCALE}",
        f"SETPATH DBF {win(dbf_dir)}",
        f"SETPATH INDEXES {win(idx_dir)}",
        f"SETPATH LMDB {win(lmdb_dir)}",
        "WORKSPACE CLOSE",
        "WORKSPACE OPEN DBF CDX",
        "STRUCT ALL INDEXES",
    ])
    for topic in SAMPLE_TOPICS:
        safe = topic.replace("|", "_").replace(" ", "_")
        lines.append(f"ECHO PHASE23L_SAMPLE_TOPIC_{safe}_{SAMPLE_LOCALE}")
    for table in TABLES:
        lines.extend([
            f"ECHO PHASE23L_READBACK_{table}",
            f"SELECT {table}",
            "AREA",
            "CDX INFO",
            f"SET INDEX TO {table}",
            "SET ORDER TO TAG TOPICKEY",
            "ASCEND",
            "TOP",
            "LIST ALL",
            "SET ORDER TO 0",
        ])
    lines.extend([
        "ECHO PHASE23L_DOTSCRIPT_END",
        "WORKSPACE CLOSE",
        "",
    ])
    dts.write_text("\n".join(lines), encoding="utf-8")

    manifest = {
        "status": STATUS,
        "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "repo_root": win(repo),
        "candidate_dir": relwin(repo, l_dir),
        "phase23k_candidate_dir": relwin(repo, k_dir),
        "phase23kr_candidate_dir": relwin(repo, kr_dir),
        "phase23kr_green": phase23kr_green,
        "candidate_dts": relwin(repo, dts),
        "expected_transcript": relwin(repo, transcript),
        "tables": TABLES,
        "sample_topics": SAMPLE_TOPICS,
        "sample_locale": SAMPLE_LOCALE,
        "lookup_contract": "TOPICKEY + LOCALE_ID readback through candidate CDX/LMDB",
        "source_files_written": 0,
        "active_help_dbf_written": 0,
        "active_help_cdx_written": 0,
        "active_help_lmdb_written": 0,
        "cmdhelp_behavior_changed": 0,
        "cmdhelpchk_behavior_changed": 0,
        "maint_behavior_changed": 0,
        "bbox_behavior_changed": 0,
        "runtime_execution_by_python": 0,
        "next_gate": "HOLD_OR_RUN_PHASE23L_DOTSCRIPT_AND_REVIEW_TRANSCRIPT",
    }
    (reports_dir / "phase23l_staging_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    command = f"DOTSCRIPT TRACE {win(dts)} OUT {win(transcript)}"
    print(STATUS)
    print(f"candidate_dir: {relwin(repo, l_dir)}")
    print(f"phase23k_candidate_dir: {relwin(repo, k_dir)}")
    print(f"phase23kr_green: {phase23kr_green}")
    print(f"candidate_tables: {len(TABLES)}")
    print(f"sample_locale: {SAMPLE_LOCALE}")
    print(f"sample_topics: {','.join(SAMPLE_TOPICS)}")
    print(f"candidate_dts: {relwin(repo, dts)}")
    print(f"expected_transcript: {relwin(repo, transcript)}")
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
    print("next_gate: HOLD_OR_RUN_PHASE23L_DOTSCRIPT_AND_REVIEW_TRANSCRIPT")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
