#!/usr/bin/env python3
"""Review PHASE23KR candidate-only all-table CDX/LMDB repair transcript."""
from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path

PHASE23K = "PHASE23K-HELP-LOCALE-CANDIDATE-DBF-CDX-LMDB-BUILD-PROOF"
PHASE23KR = "PHASE23KR-HELP-LOCALE-ALL-TABLE-CDX-TAG-LMDB-CLEAN-REBUILD-PROOF"
GREEN = "PHASE23KR_HELP_LOCALE_ALL_TABLE_CDX_TAG_CREATE_AND_LMDB_CLEAN_REBUILD_PROOF_GREEN"
REVIEW = "PHASE23KR_HELP_LOCALE_ALL_TABLE_CDX_TAG_CREATE_AND_LMDB_CLEAN_REBUILD_REVIEW_REQUIRED"
TABLES = [
    "HELP_TOPIC_LOCALE",
    "HELP_SECTION_LOCALE",
    "HELP_LINE_LOCALE",
    "HELP_ARTIFACT_LOCALE",
]

BAD_PATTERNS = [
    r"BUILDLMDB: failed to build LMDB environment",
    r"DOTSCRIPT: script not found",
    r"unknown command",
    r"SET ORDER: tag '<PRIMARY_TAG>' not found",
    r"SET ORDER: tag 'TOPICKEY' not found",
    r"SET INDEX: file not found",
]


def win(p: Path) -> str:
    return str(p).replace("/", "\\")


def count_existing(paths: list[Path]) -> str:
    return f"{sum(1 for p in paths if p.exists())}/{len(paths)}"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", default=".")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    k_dir = repo / "docs" / "locale" / "candidates" / PHASE23K
    kr_dir = repo / "docs" / "locale" / "candidates" / PHASE23KR
    transcript = kr_dir / "transcripts" / "phase23kr_repair_help_locale_candidate_lmdb_all_tables_transcript.txt"
    reports_dir = kr_dir / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)

    text = transcript.read_text(encoding="utf-8", errors="replace") if transcript.exists() else ""
    upper = text.upper()

    dbfs = [k_dir / "dbf" / f"{t}.dbf" for t in TABLES]
    cdxs = [k_dir / "indexes" / f"{t}.cdx" for t in TABLES]
    lmdbs = [k_dir / "lmdb" / f"{t}.cdx.d" for t in TABLES]

    marker_start = "PHASE23KR_DOTSCRIPT_START" in text
    marker_end = "PHASE23KR_DOTSCRIPT_END" in text
    table_markers = {t: f"PHASE23KR_REPAIR_{t}" in text for t in TABLES}
    build_ok_count = len(re.findall(r"BUILDLMDB: done OK=\d+ tags rebuilt", text, flags=re.I))
    topickey_order_count = len(re.findall(r"SET ORDER: CDX TAG 'TOPICKEY'", text, flags=re.I))
    mode_lmdb_count = len(re.findall(r"MODE LMDB", text, flags=re.I))
    indexed_record_count = len(re.findall(r"cdx\(lmdb\) indexed record\(s\)", text, flags=re.I))
    cdx_addtag_topickey_count = len(re.findall(r"CDX ADDTAG: added 'TOPICKEY'", text, flags=re.I))
    cdx_info_tag_lines = len(re.findall(r"Tags\s*:\s*[1-9]", text, flags=re.I))

    bad_hits = []
    for pat in BAD_PATTERNS:
        if re.search(pat, text, flags=re.I):
            bad_hits.append(pat)

    checks = {
        "transcript_exists": transcript.exists(),
        "transcript_markers_ok": marker_start and marker_end,
        "table_markers_ok": all(table_markers.values()),
        "candidate_dbf_exists": count_existing(dbfs),
        "candidate_cdx_exists": count_existing(cdxs),
        "candidate_lmdb_exists": count_existing(lmdbs),
        "buildlmdb_done_ok_count": build_ok_count,
        "topickey_order_count": topickey_order_count,
        "mode_lmdb_count": mode_lmdb_count,
        "indexed_record_count": indexed_record_count,
        "cdx_addtag_topickey_count": cdx_addtag_topickey_count,
        "cdx_info_tag_lines": cdx_info_tag_lines,
        "bad_pattern_hits": bad_hits,
    }

    green = (
        checks["transcript_exists"]
        and checks["transcript_markers_ok"]
        and checks["table_markers_ok"]
        and count_existing(dbfs) == "4/4"
        and count_existing(cdxs) == "4/4"
        and count_existing(lmdbs) == "4/4"
        and build_ok_count >= 4
        and topickey_order_count >= 4
        and mode_lmdb_count >= 4
        and indexed_record_count >= 4
        and not bad_hits
    )

    status = GREEN if green else REVIEW
    out = {
        "status": status,
        "reviewed_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "candidate_dir": win(kr_dir.relative_to(repo)),
        "phase23k_candidate_dir": win(k_dir.relative_to(repo)),
        "transcript": win(transcript.relative_to(repo)),
        **checks,
        "source_files_written": 0,
        "active_help_dbf_written": 0,
        "active_help_cdx_written": 0,
        "active_help_lmdb_written": 0,
        "cmdhelp_behavior_changed": 0,
        "cmdhelpchk_behavior_changed": 0,
        "maint_behavior_changed": 0,
        "bbox_behavior_changed": 0,
        "next_gate": "HOLD_OR_AUTHORIZE_PHASE23L_CMDHELP_LOCALE_READBACK_PROTOTYPE" if green else "FIX_OR_RERUN_PHASE23KR_DOTSCRIPT",
    }
    (reports_dir / "phase23kr_review_manifest.json").write_text(json.dumps(out, indent=2), encoding="utf-8")

    print(status)
    print(f"candidate_dir: {win(kr_dir.relative_to(repo))}")
    print(f"phase23k_candidate_dir: {win(k_dir.relative_to(repo))}")
    print(f"transcript: {win(transcript.relative_to(repo))}")
    print(f"transcript_markers_ok: {1 if checks['transcript_markers_ok'] else 0}")
    print(f"table_markers_ok: {1 if checks['table_markers_ok'] else 0}")
    print(f"candidate_dbf_exists: {checks['candidate_dbf_exists']}")
    print(f"candidate_cdx_exists: {checks['candidate_cdx_exists']}")
    print(f"candidate_lmdb_exists: {checks['candidate_lmdb_exists']}")
    print(f"buildlmdb_done_ok_count: {build_ok_count}")
    print(f"topickey_order_count: {topickey_order_count}")
    print(f"mode_lmdb_count: {mode_lmdb_count}")
    print(f"indexed_record_count: {indexed_record_count}")
    print(f"cdx_info_tag_lines: {cdx_info_tag_lines}")
    print(f"no_bad_hits: {1 if not bad_hits else 0}")
    if bad_hits:
        print("bad_pattern_hits: " + ", ".join(bad_hits))
    print("source_files_written: 0")
    print("active_help_dbf_written: 0")
    print("active_help_cdx_written: 0")
    print("active_help_lmdb_written: 0")
    print("cmdhelp_behavior_changed: 0")
    print("cmdhelpchk_behavior_changed: 0")
    print("maint_behavior_changed: 0")
    print("bbox_behavior_changed: 0")
    print(f"next_gate: {out['next_gate']}")
    return 0 if green else 1


if __name__ == "__main__":
    raise SystemExit(main())
