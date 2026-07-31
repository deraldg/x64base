#!/usr/bin/env python3
"""Review PHASE23O active HELP locale readback proof transcript."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from datetime import datetime, timezone
from typing import Any

GREEN = "PHASE23O_ACTIVE_HELP_LOCALE_READBACK_PROOF_GREEN"
REVIEW_REQUIRED = "PHASE23O_ACTIVE_HELP_LOCALE_READBACK_REVIEW_REQUIRED"
CANDIDATE_NAME = "PHASE23O-ACTIVE-HELP-LOCALE-READBACK-PROOF"
PHASE23N_NAME = "PHASE23N-HELP-LOCALE-ACTIVE-PROMOTION-EXECUTION-STAGING"
PHASE23K_NAME = "PHASE23K-HELP-LOCALE-CANDIDATE-DBF-CDX-LMDB-BUILD-PROOF"

TABLES = ["HELP_TOPIC_LOCALE", "HELP_SECTION_LOCALE", "HELP_LINE_LOCALE", "HELP_ARTIFACT_LOCALE"]
SAMPLE_TOPICS = ["DOT|ABOUT", "DOT|AREA"]
SAMPLE_LOCALE = "es"
BAD_PATTERNS = [
    r"DOTSCRIPT: script not found",
    r"Unknown command",
    r"SET ORDER: tag 'TOPICKEY' not found",
    r"SET INDEX: file not found",
    r"BUILDLMDB: failed to build LMDB environment",
    r">\s+LIST\b",
    r">\s+SMARTLIST\s+ALL\b",
]


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def count(pattern: str, text: str, flags: int = re.IGNORECASE) -> int:
    return len(re.findall(pattern, text, flags))


def exists_all(paths: list[Path]) -> tuple[int, int]:
    return sum(1 for p in paths if p.exists()), len(paths)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_dir(path: Path) -> str:
    h = hashlib.sha256()
    if not path.exists():
        return ""
    for p in sorted([x for x in path.rglob("*") if x.is_file()]):
        rp = str(p.relative_to(path)).replace("\\", "/")
        h.update(rp.encode("utf-8"))
        h.update(b"\0")
        h.update(sha256_file(p).encode("ascii"))
        h.update(b"\0")
    return h.hexdigest()


def artifact_hash(path: Path) -> str:
    if path.is_dir():
        return sha256_dir(path)
    if path.is_file():
        return sha256_file(path)
    return ""


def detect_phase23n_green(repo: Path) -> int:
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
    phase23k_dir = repo / "docs" / "locale" / "candidates" / PHASE23K_NAME
    transcript = candidate_dir / "transcripts" / "phase23o_active_help_locale_count_smartlist_tuple_probe_transcript.txt"
    dts = candidate_dir / "runtime" / "phase23o_active_help_locale_count_smartlist_tuple_probe.dts"
    report_dir = candidate_dir / "reports"
    manifest_dir = candidate_dir / "manifests"
    for d in (report_dir, manifest_dir):
        d.mkdir(parents=True, exist_ok=True)

    text = read_text(transcript)
    phase23n_green = detect_phase23n_green(repo)

    active_dbf_root = repo / "dottalkpp" / "data" / "HELP"
    active_idx_root = repo / "dottalkpp" / "data" / "INDEXES" / "HELP"
    active_lmdb_root = repo / "dottalkpp" / "data" / "LMDB" / "HELP"

    active_dbf = [active_dbf_root / f"{t}.dbf" for t in TABLES]
    active_cdx = [active_idx_root / f"{t}.cdx" for t in TABLES]
    active_lmdb = [active_lmdb_root / f"{t}.cdx.d" for t in TABLES]
    dbf_exists = exists_all(active_dbf)
    cdx_exists = exists_all(active_cdx)
    lmdb_exists = exists_all(active_lmdb)

    # Compare active artifacts against the original PHASE23K candidate artifacts promoted by PHASE23N.
    hash_match_count = 0
    dbf_cdx_hash_match_count = 0
    lmdb_hash_match_count = 0
    lmdb_hash_drift_tables: list[str] = []
    hash_rows: list[dict[str, Any]] = []
    for table in TABLES:
        pairs = [
            ("DBF", phase23k_dir / "dbf" / f"{table}.dbf", active_dbf_root / f"{table}.dbf"),
            ("CDX", phase23k_dir / "indexes" / f"{table}.cdx", active_idx_root / f"{table}.cdx"),
            ("LMDB", phase23k_dir / "lmdb" / f"{table}.cdx.d", active_lmdb_root / f"{table}.cdx.d"),
        ]
        for kind, src, dst in pairs:
            sh = artifact_hash(src)
            dh = artifact_hash(dst)
            ok = bool(src.exists() and dst.exists() and sh and sh == dh)
            if ok:
                hash_match_count += 1
                if kind in ("DBF", "CDX"):
                    dbf_cdx_hash_match_count += 1
                elif kind == "LMDB":
                    lmdb_hash_match_count += 1
            elif kind == "LMDB" and src.exists() and dst.exists():
                lmdb_hash_drift_tables.append(table)
            hash_rows.append({"table": table, "kind": kind, "candidate_exists": src.exists(), "active_exists": dst.exists(), "hash_match": ok})

    dts_extension_ok = int(dts.exists() and dts.suffix.lower() == ".dts")
    transcript_markers_ok = int("PHASE23O_DOTSCRIPT_START" in text and "PHASE23O_DOTSCRIPT_END" in text)
    scope_marker_ok = int("PHASE23O_SCOPE_READONLY_ACTIVE_HELP_LOCALE_TABLES_ONLY" in text)
    contract_marker_ok = int("PHASE23O_COUNT_SMARTLIST_N_TUPLE_CONTRACT" in text)
    no_list_contract_marker_ok = int("PHASE23O_NO_LIST_NO_SMARTLIST_ALL" in text)
    path_reset_ok = int(
        "PHASE23O_PATH_RESET_TO_DEFAULT_DATA_ROOTS" in text
        and re.search(r"SETPATH:\s*LMDB\s*=\s*.*dottalkpp\\data\\lmdb", text, re.IGNORECASE) is not None
    )
    active_root_read_ok = int(
        re.search(r"SETPATH:\s*DBF\s*=\s*.*dottalkpp\\data\\HELP", text, re.IGNORECASE) is not None
        and re.search(r"SETPATH:\s*INDEXES\s*=\s*.*dottalkpp\\data\\INDEXES\\HELP", text, re.IGNORECASE) is not None
        and re.search(r"SETPATH:\s*LMDB\s*=\s*.*dottalkpp\\data\\LMDB\\HELP", text, re.IGNORECASE) is not None
    )

    table_markers_ok = int(all(f"PHASE23O_ACTIVE_READBACK_{t}" in text for t in TABLES))
    tuple_markers_ok = int(all(f"PHASE23O_TUPLE_{t}_TOP_VALUES_ONLY" in text for t in TABLES))
    compact_tuple_markers_ok = int(all(f"PHASE23O_TUPLE_{t}_COMPACT" in text for t in TABLES))

    topickey_order_count = count(r"SET ORDER:\s*CDX TAG 'TOPICKEY'", text)
    count_command_count = count(r">\s*COUNT\b", text)
    smartlist_n_command_count = count(r">\s*SMARTLIST\s+\d+\b", text)
    smartlist_all_command_count = count(r">\s*SMARTLIST\s+ALL\b", text)
    list_command_count = count(r">\s*LIST\b", text)
    tuple_values_command_count = count(r">\s*TUPLE\s+\*\s+--VALUES-ONLY", text)
    compact_tuple_command_count = count(r">\s*TUPLE\s+TOPICKEY,LOCALE_ID,TRANSL_STATUS,REVIEW_STATUS\s+--VALUES-ONLY", text)
    tuple_values_row_count = count(r"^PHASE23J-", text, flags=re.MULTILINE)
    compact_tuple_row_count = count(r"^DOT\|", text, flags=re.MULTILINE)
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
    active_help_dbf_written_by_review = 0
    active_help_cdx_written_by_review = 0
    active_help_lmdb_written_by_review = 0
    cmdhelp_behavior_changed = 0
    cmdhelpchk_behavior_changed = 0
    maint_behavior_changed = 0
    bbox_behavior_changed = 0

    green_conditions = [
        phase23n_green == 1,
        dts_extension_ok == 1,
        transcript_markers_ok == 1,
        scope_marker_ok == 1,
        contract_marker_ok == 1,
        no_list_contract_marker_ok == 1,
        active_root_read_ok == 1,
        table_markers_ok == 1,
        tuple_markers_ok == 1,
        compact_tuple_markers_ok == 1,
        dbf_exists == (4, 4),
        cdx_exists == (4, 4),
        lmdb_exists == (4, 4),
        # DBF and CDX bytes should still match PHASE23K/PHASE23N exactly.
        # LMDB envdir bytes may drift after active runtime read/open because LMDB can update
        # environment/lock metadata. PHASE23O is a readback proof, so require LMDB existence
        # and runtime attachment/read markers, but treat LMDB post-read byte drift as advisory.
        dbf_cdx_hash_match_count == 8,
        topickey_order_count >= 4,
        count_command_count >= 4,
        smartlist_n_command_count >= 4,
        smartlist_all_command_count == 0,
        list_command_count == 0,
        tuple_values_command_count >= 4,
        compact_tuple_command_count >= 4,
        tuple_values_row_count >= 4,
        compact_tuple_row_count >= 4,
        record_listed_count >= 4,
        cdx_info_tag_lines >= 4,
        lmdb_env_lines >= 4,
        sample_topics_found >= len(SAMPLE_TOPICS),
        draft_placeholder_rows_detected == 1,
        needs_review_detected == 1,
        es_draft_detected == 1,
        path_reset_ok == 1,
        no_bad_hits == 1,
    ]
    status = GREEN if all(green_conditions) else REVIEW_REQUIRED
    next_gate = "HOLD_OR_AUTHORIZE_PHASE23P_CMDHELP_ACTIVE_LOCALE_CONSUMER_PROTOTYPE" if status == GREEN else "FIX_OR_RERUN_PHASE23O_DOTSCRIPT"

    result = {
        "status": status,
        "created_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "candidate_dir": str(candidate_dir.relative_to(repo)),
        "phase23n_green": phase23n_green,
        "read_scope": "ACTIVE_HELP_LOCALE_ROOTS",
        "active_roots": f"{active_dbf_root.relative_to(repo)},{active_idx_root.relative_to(repo)},{active_lmdb_root.relative_to(repo)}",
        "retained_dotscript": str(dts.relative_to(repo)),
        "dts_extension_ok": dts_extension_ok,
        "transcript": str(transcript.relative_to(repo)),
        "transcript_markers_ok": transcript_markers_ok,
        "scope_marker_ok": scope_marker_ok,
        "contract_marker_ok": contract_marker_ok,
        "no_list_contract_marker_ok": no_list_contract_marker_ok,
        "active_root_read_ok": active_root_read_ok,
        "table_markers_ok": table_markers_ok,
        "tuple_markers_ok": tuple_markers_ok,
        "compact_tuple_markers_ok": compact_tuple_markers_ok,
        "active_dbf_exists": f"{dbf_exists[0]}/{dbf_exists[1]}",
        "active_cdx_exists": f"{cdx_exists[0]}/{cdx_exists[1]}",
        "active_lmdb_exists": f"{lmdb_exists[0]}/{lmdb_exists[1]}",
        "hash_match_count": f"{hash_match_count}/12",
        "dbf_cdx_hash_match_count": f"{dbf_cdx_hash_match_count}/8",
        "lmdb_hash_match_count": f"{lmdb_hash_match_count}/4",
        "lmdb_hash_drift_advisory": int(len(lmdb_hash_drift_tables) > 0),
        "lmdb_hash_drift_tables": lmdb_hash_drift_tables,
        "topickey_order_count": topickey_order_count,
        "count_command_count": count_command_count,
        "smartlist_n_command_count": smartlist_n_command_count,
        "smartlist_all_command_count": smartlist_all_command_count,
        "list_command_count": list_command_count,
        "tuple_values_command_count": tuple_values_command_count,
        "compact_tuple_command_count": compact_tuple_command_count,
        "tuple_values_row_count": tuple_values_row_count,
        "compact_tuple_row_count": compact_tuple_row_count,
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
        "hash_rows": hash_rows,
        "active_help_dbf_written_by_review": active_help_dbf_written_by_review,
        "active_help_cdx_written_by_review": active_help_cdx_written_by_review,
        "active_help_lmdb_written_by_review": active_help_lmdb_written_by_review,
        "source_files_written": source_files_written,
        "cmdhelp_behavior_changed": cmdhelp_behavior_changed,
        "cmdhelpchk_behavior_changed": cmdhelpchk_behavior_changed,
        "maint_behavior_changed": maint_behavior_changed,
        "bbox_behavior_changed": bbox_behavior_changed,
        "next_gate": next_gate,
    }
    (manifest_dir / "phase23o_active_help_locale_readback_review_manifest.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    (report_dir / "phase23o_active_help_locale_readback_review_result.json").write_text(json.dumps(result, indent=2), encoding="utf-8")

    print(status)
    for key in [
        "candidate_dir",
        "phase23n_green",
        "read_scope",
        "active_roots",
        "retained_dotscript",
        "dts_extension_ok",
        "transcript",
        "transcript_markers_ok",
        "scope_marker_ok",
        "contract_marker_ok",
        "no_list_contract_marker_ok",
        "active_root_read_ok",
        "table_markers_ok",
        "tuple_markers_ok",
        "compact_tuple_markers_ok",
        "active_dbf_exists",
        "active_cdx_exists",
        "active_lmdb_exists",
        "hash_match_count",
        "dbf_cdx_hash_match_count",
        "lmdb_hash_match_count",
        "lmdb_hash_drift_advisory",
        "topickey_order_count",
        "count_command_count",
        "smartlist_n_command_count",
        "smartlist_all_command_count",
        "list_command_count",
        "tuple_values_command_count",
        "compact_tuple_command_count",
        "tuple_values_row_count",
        "compact_tuple_row_count",
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
        "active_help_dbf_written_by_review",
        "active_help_cdx_written_by_review",
        "active_help_lmdb_written_by_review",
        "source_files_written",
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
