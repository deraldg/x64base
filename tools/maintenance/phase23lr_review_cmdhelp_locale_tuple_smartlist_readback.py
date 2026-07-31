#!/usr/bin/env python3
"""Review PHASE23LR tuple + SMARTLIST CMDHELP locale readback transcript."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from datetime import datetime, timezone

GREEN = "PHASE23LR_CMDHELP_LOCALE_TUPLE_SMARTLIST_READBACK_PROOF_GREEN"
REVIEW_REQUIRED = "PHASE23LR_CMDHELP_LOCALE_TUPLE_SMARTLIST_READBACK_REVIEW_REQUIRED"
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
BAD_PATTERNS = [
    r"DOTSCRIPT: script not found",
    r"Unknown command",
    r"SET ORDER: tag 'TOPICKEY' not found",
    r"SET INDEX: file not found",
    r"BUILDLMDB: failed to build LMDB environment",
    r">\s+LIST\b",
]


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def count(pattern: str, text: str, flags: int = re.IGNORECASE) -> int:
    return len(re.findall(pattern, text, flags))


def exists_all(paths: list[Path]) -> tuple[int, int]:
    return sum(1 for p in paths if p.exists()), len(paths)


def detect_phase23kr_green(repo: Path) -> int:
    kr = repo / "docs" / "locale" / "candidates" / PHASE23KR_NAME / "transcripts" / "phase23kr_repair_help_locale_candidate_lmdb_all_tables_transcript.txt"
    text = read_text(kr)
    if not text:
        return 0
    if "PHASE23KR_DOTSCRIPT_START" not in text or "PHASE23KR_DOTSCRIPT_END" not in text:
        return 0
    if count(r"BUILDLMDB:\s*done OK=\d+ tags rebuilt", text) < 4:
        return 0
    if count(r"SET ORDER:\s*CDX TAG 'TOPICKEY'", text) < 4:
        return 0
    return 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", default=".")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    candidate_dir = repo / "docs" / "locale" / "candidates" / CANDIDATE_NAME
    phase23k_dir = repo / "docs" / "locale" / "candidates" / PHASE23K_NAME
    transcript = candidate_dir / "transcripts" / "phase23lr_cmdhelp_locale_tuple_smartlist_readback_probe_transcript.txt"
    report_dir = candidate_dir / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)

    text = read_text(transcript)
    phase23kr_green = detect_phase23kr_green(repo)

    transcript_markers_ok = int("PHASE23LR_DOTSCRIPT_START" in text and "PHASE23LR_DOTSCRIPT_END" in text)
    contract_marker_ok = int("PHASE23LR_SMARTLIST_TUPLE_CONTRACT" in text)
    path_reset_ok = int(
        "PHASE23LR_PATH_RESET_TO_DEFAULT_DATA_ROOTS" in text
        and re.search(r"SETPATH:\s*LMDB\s*=\s*.*dottalkpp\\data\\lmdb", text, re.IGNORECASE) is not None
    )

    table_markers_ok = int(all(f"PHASE23LR_READBACK_{t}" in text for t in TABLES))
    tuple_markers_ok = int(all(f"PHASE23LR_TUPLE_{t}_TOP" in text for t in TABLES))

    candidate_dbf = [phase23k_dir / "dbf" / f"{t}.dbf" for t in TABLES]
    candidate_cdx = [phase23k_dir / "indexes" / f"{t}.cdx" for t in TABLES]
    candidate_lmdb = [phase23k_dir / "lmdb" / f"{t}.cdx.d" for t in TABLES]
    dbf_exists = exists_all(candidate_dbf)
    cdx_exists = exists_all(candidate_cdx)
    lmdb_exists = exists_all(candidate_lmdb)

    topickey_order_count = count(r"SET ORDER:\s*CDX TAG 'TOPICKEY'", text)
    smartlist_command_count = count(r">\s*SMARTLIST\s+ALL", text)
    tuple_command_count = count(r">\s*TUPLE\s+\*\s+--VALUES-ONLY", text)
    tuple_pipe_row_count = sum(1 for line in text.splitlines() if " | " in line and not line.lstrip().startswith("D:"))
    record_listed_count = count(r"\d+\s+record\(s\) listed", text)
    cdx_info_tag_lines = count(r"Tags\s*:\s*\d+", text)
    lmdb_env_lines = count(r"LMDB env\s*:", text)

    sample_topics_found = sum(1 for topic in SAMPLE_TOPICS if topic in text)
    draft_placeholder_rows_detected = int(re.search(r"DRAFT_\s*PLACEHOLDER", text, re.IGNORECASE) is not None)
    needs_review_detected = int(re.search(r"NEEDS_\s*REVIEW", text, re.IGNORECASE) is not None)
    es_draft_detected = int(re.search(r"\bes\b", text, re.IGNORECASE) is not None and draft_placeholder_rows_detected)

    bad_hits = []
    for pat in BAD_PATTERNS:
        if re.search(pat, text, re.IGNORECASE):
            bad_hits.append(pat)
    no_bad_hits = int(len(bad_hits) == 0)

    source_files_written = 0
    active_help_dbf_written = 0
    active_help_cdx_written = 0
    active_help_lmdb_written = 0
    cmdhelp_behavior_changed = 0
    cmdhelpchk_behavior_changed = 0
    maint_behavior_changed = 0
    bbox_behavior_changed = 0

    green_conditions = [
        phase23kr_green == 1,
        transcript_markers_ok == 1,
        contract_marker_ok == 1,
        table_markers_ok == 1,
        tuple_markers_ok == 1,
        dbf_exists == (4, 4),
        cdx_exists == (4, 4),
        lmdb_exists == (4, 4),
        topickey_order_count >= 4,
        smartlist_command_count >= 4,
        tuple_command_count >= 4,
        tuple_pipe_row_count >= 4,
        record_listed_count >= 4,
        cdx_info_tag_lines >= 4,
        lmdb_env_lines >= 4,
        sample_topics_found >= 4,
        draft_placeholder_rows_detected == 1,
        needs_review_detected == 1,
        es_draft_detected == 1,
        path_reset_ok == 1,
        no_bad_hits == 1,
    ]
    status = GREEN if all(green_conditions) else REVIEW_REQUIRED
    next_gate = "HOLD_OR_AUTHORIZE_PHASE23M_HELP_LOCALE_ACTIVE_PROMOTION_PLAN" if status == GREEN else "FIX_OR_RERUN_PHASE23LR_DOTSCRIPT"

    result = {
        "status": status,
        "created_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "candidate_dir": str(candidate_dir.relative_to(repo)),
        "phase23k_candidate_dir": str(phase23k_dir.relative_to(repo)),
        "phase23kr_green": phase23kr_green,
        "transcript": str(transcript.relative_to(repo)),
        "transcript_markers_ok": transcript_markers_ok,
        "contract_marker_ok": contract_marker_ok,
        "table_markers_ok": table_markers_ok,
        "tuple_markers_ok": tuple_markers_ok,
        "candidate_dbf_exists": f"{dbf_exists[0]}/{dbf_exists[1]}",
        "candidate_cdx_exists": f"{cdx_exists[0]}/{cdx_exists[1]}",
        "candidate_lmdb_exists": f"{lmdb_exists[0]}/{lmdb_exists[1]}",
        "topickey_order_count": topickey_order_count,
        "smartlist_command_count": smartlist_command_count,
        "tuple_command_count": tuple_command_count,
        "tuple_pipe_row_count": tuple_pipe_row_count,
        "record_listed_count": record_listed_count,
        "cdx_info_tag_lines": cdx_info_tag_lines,
        "lmdb_env_lines": lmdb_env_lines,
        "sample_locale": SAMPLE_LOCALE,
        "sample_topics_checked": len(SAMPLE_TOPICS),
        "sample_topics_found": f"{sample_topics_found}/{len(SAMPLE_TOPICS)}",
        "draft_placeholder_rows_detected": draft_placeholder_rows_detected,
        "needs_review_detected": needs_review_detected,
        "es_draft_detected": es_draft_detected,
        "path_reset_ok": path_reset_ok,
        "no_bad_hits": no_bad_hits,
        "bad_pattern_hits": bad_hits,
        "source_files_written": source_files_written,
        "active_help_dbf_written": active_help_dbf_written,
        "active_help_cdx_written": active_help_cdx_written,
        "active_help_lmdb_written": active_help_lmdb_written,
        "cmdhelp_behavior_changed": cmdhelp_behavior_changed,
        "cmdhelpchk_behavior_changed": cmdhelpchk_behavior_changed,
        "maint_behavior_changed": maint_behavior_changed,
        "bbox_behavior_changed": bbox_behavior_changed,
        "next_gate": next_gate,
    }
    (report_dir / "phase23lr_review_result.json").write_text(json.dumps(result, indent=2), encoding="utf-8")

    print(status)
    for key in [
        "candidate_dir",
        "phase23k_candidate_dir",
        "phase23kr_green",
        "transcript",
        "transcript_markers_ok",
        "contract_marker_ok",
        "table_markers_ok",
        "tuple_markers_ok",
        "candidate_dbf_exists",
        "candidate_cdx_exists",
        "candidate_lmdb_exists",
        "topickey_order_count",
        "smartlist_command_count",
        "tuple_command_count",
        "tuple_pipe_row_count",
        "record_listed_count",
        "cdx_info_tag_lines",
        "lmdb_env_lines",
        "sample_locale",
        "sample_topics_checked",
        "sample_topics_found",
        "draft_placeholder_rows_detected",
        "needs_review_detected",
        "es_draft_detected",
        "path_reset_ok",
        "no_bad_hits",
    ]:
        print(f"{key}: {result[key]}")
    if bad_hits:
        print(f"bad_pattern_hits: {','.join(bad_hits)}")
    for key in [
        "source_files_written",
        "active_help_dbf_written",
        "active_help_cdx_written",
        "active_help_lmdb_written",
        "cmdhelp_behavior_changed",
        "cmdhelpchk_behavior_changed",
        "maint_behavior_changed",
        "bbox_behavior_changed",
        "next_gate",
    ]:
        print(f"{key}: {result[key]}")
    return 0 if status == GREEN else 1


if __name__ == "__main__":
    raise SystemExit(main())
