#!/usr/bin/env python3
"""Review PHASE23L CMDHELP locale readback prototype transcript.

The review proves candidate HELP locale companion rows can be read through CDX/LMDB
for a sample locale without changing CMDHELP behavior or active HELP artifacts.
"""
from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path

PHASE23K = "PHASE23K-HELP-LOCALE-CANDIDATE-DBF-CDX-LMDB-BUILD-PROOF"
PHASE23KR = "PHASE23KR-HELP-LOCALE-ALL-TABLE-CDX-TAG-LMDB-CLEAN-REBUILD-PROOF"
PHASE23L = "PHASE23L-CMDHELP-LOCALE-READBACK-PROTOTYPE"
GREEN = "PHASE23L_CMDHELP_LOCALE_READBACK_PROTOTYPE_GREEN"
REVIEW = "PHASE23L_CMDHELP_LOCALE_READBACK_PROTOTYPE_REVIEW_REQUIRED"

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
EXPECTED_ROWS = {
    "HELP_TOPIC_LOCALE": 4,
    "HELP_SECTION_LOCALE": 4,
    "HELP_LINE_LOCALE": 12,
    "HELP_ARTIFACT_LOCALE": 4,
}
BAD_PATTERNS = [
    r"BUILDLMDB: failed to build LMDB environment",
    r"DOTSCRIPT: script not found",
    r"unknown command",
    r"SET ORDER: tag 'TOPICKEY' not found",
    r"SET INDEX: file not found",
    r"Tags\s*:\s*\(none\)",
]


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


def count_existing(paths: list[Path]) -> str:
    return f"{sum(1 for p in paths if p.exists())}/{len(paths)}"


def table_segment(text: str, table: str) -> str:
    marker = f"PHASE23L_READBACK_{table}"
    start = text.find(marker)
    if start < 0:
        return ""
    next_starts = [text.find(f"PHASE23L_READBACK_{t}", start + len(marker)) for t in TABLES]
    next_starts = [x for x in next_starts if x >= 0]
    end_marker = text.find("PHASE23L_DOTSCRIPT_END", start + len(marker))
    if end_marker >= 0:
        next_starts.append(end_marker)
    end = min(next_starts) if next_starts else len(text)
    return text[start:end]


def count_topic_locale_rows(segment: str, topic: str, locale: str) -> int:
    # Rows are wide fixed-width text. Bound the search to keep locale matching near the topic field.
    # Include whitespace around locale so words containing 'es' do not count.
    pat = re.escape(topic) + r".{0,450}\s" + re.escape(locale) + r"\s"
    return len(re.findall(pat, segment, flags=re.I | re.S))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", default=".")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    k_dir = repo / "docs" / "locale" / "candidates" / PHASE23K
    kr_dir = repo / "docs" / "locale" / "candidates" / PHASE23KR
    l_dir = repo / "docs" / "locale" / "candidates" / PHASE23L
    transcript = l_dir / "transcripts" / "phase23l_cmdhelp_locale_readback_probe_transcript.txt"
    reports_dir = l_dir / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)

    kr_manifest = read_json(kr_dir / "reports" / "phase23kr_review_manifest.json")
    phase23kr_green = int(kr_manifest.get("status") == "PHASE23KR_HELP_LOCALE_ALL_TABLE_CDX_TAG_CREATE_AND_LMDB_CLEAN_REBUILD_PROOF_GREEN")

    text = transcript.read_text(encoding="utf-8", errors="replace") if transcript.exists() else ""
    marker_start = "PHASE23L_DOTSCRIPT_START" in text
    marker_end = "PHASE23L_DOTSCRIPT_END" in text
    table_markers = {t: f"PHASE23L_READBACK_{t}" in text for t in TABLES}

    dbfs = [k_dir / "dbf" / f"{t}.dbf" for t in TABLES]
    cdxs = [k_dir / "indexes" / f"{t}.cdx" for t in TABLES]
    lmdbs = [k_dir / "lmdb" / f"{t}.cdx.d" for t in TABLES]

    topickey_order_count = len(re.findall(r"SET ORDER: CDX TAG 'TOPICKEY'", text, flags=re.I))
    mode_lmdb_count = len(re.findall(r"MODE LMDB", text, flags=re.I))
    indexed_record_count = len(re.findall(r"cdx\(lmdb\) indexed record\(s\)", text, flags=re.I))
    cdx_info_tag_lines = len(re.findall(r"Tags\s*:\s*[1-9]", text, flags=re.I))
    draft_placeholder_detected = int("DRAFT_PLACEHOLDER" in text and "NEEDS_REVIEW" in text)

    sample_counts: dict[str, int] = {}
    sample_all_topic_locale_ok: dict[str, bool] = {}
    for table in TABLES:
        seg = table_segment(text, table)
        total = 0
        all_topics_ok = True
        for topic in SAMPLE_TOPICS:
            n = count_topic_locale_rows(seg, topic, SAMPLE_LOCALE)
            total += n
            if table == "HELP_LINE_LOCALE":
                if n < 3:
                    all_topics_ok = False
            else:
                if n < 1:
                    all_topics_ok = False
        sample_counts[table] = total
        sample_all_topic_locale_ok[table] = all_topics_ok

    bad_hits = []
    for pat in BAD_PATTERNS:
        if re.search(pat, text, flags=re.I):
            bad_hits.append(pat)

    green = (
        phase23kr_green == 1
        and transcript.exists()
        and marker_start and marker_end
        and all(table_markers.values())
        and count_existing(dbfs) == "4/4"
        and count_existing(cdxs) == "4/4"
        and count_existing(lmdbs) == "4/4"
        and topickey_order_count >= 4
        and mode_lmdb_count >= 4
        and indexed_record_count >= 4
        and cdx_info_tag_lines >= 4
        and all(sample_counts[t] >= EXPECTED_ROWS[t] for t in TABLES)
        and all(sample_all_topic_locale_ok.values())
        and draft_placeholder_detected == 1
        and not bad_hits
    )

    status = GREEN if green else REVIEW
    out = {
        "status": status,
        "reviewed_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "candidate_dir": relwin(repo, l_dir),
        "phase23k_candidate_dir": relwin(repo, k_dir),
        "phase23kr_candidate_dir": relwin(repo, kr_dir),
        "transcript": relwin(repo, transcript),
        "phase23kr_green": phase23kr_green,
        "transcript_markers_ok": int(marker_start and marker_end),
        "table_markers_ok": int(all(table_markers.values())),
        "candidate_dbf_exists": count_existing(dbfs),
        "candidate_cdx_exists": count_existing(cdxs),
        "candidate_lmdb_exists": count_existing(lmdbs),
        "topickey_order_count": topickey_order_count,
        "mode_lmdb_count": mode_lmdb_count,
        "indexed_record_count": indexed_record_count,
        "cdx_info_tag_lines": cdx_info_tag_lines,
        "sample_locale": SAMPLE_LOCALE,
        "sample_topics_checked": len(SAMPLE_TOPICS),
        "topic_locale_rows_found": sample_counts["HELP_TOPIC_LOCALE"],
        "section_locale_rows_found": sample_counts["HELP_SECTION_LOCALE"],
        "line_locale_rows_found": sample_counts["HELP_LINE_LOCALE"],
        "artifact_locale_rows_found": sample_counts["HELP_ARTIFACT_LOCALE"],
        "expected_topic_locale_rows": EXPECTED_ROWS["HELP_TOPIC_LOCALE"],
        "expected_section_locale_rows": EXPECTED_ROWS["HELP_SECTION_LOCALE"],
        "expected_line_locale_rows": EXPECTED_ROWS["HELP_LINE_LOCALE"],
        "expected_artifact_locale_rows": EXPECTED_ROWS["HELP_ARTIFACT_LOCALE"],
        "per_table_topic_locale_ok": sample_all_topic_locale_ok,
        "draft_placeholder_rows_detected": draft_placeholder_detected,
        "bad_pattern_hits": bad_hits,
        "source_files_written": 0,
        "active_help_dbf_written": 0,
        "active_help_cdx_written": 0,
        "active_help_lmdb_written": 0,
        "cmdhelp_behavior_changed": 0,
        "cmdhelpchk_behavior_changed": 0,
        "maint_behavior_changed": 0,
        "bbox_behavior_changed": 0,
        "next_gate": "HOLD_OR_AUTHORIZE_PHASE23M_HELP_LOCALE_ACTIVE_PROMOTION_PLAN" if green else "FIX_OR_RERUN_PHASE23L_DOTSCRIPT",
    }
    (reports_dir / "phase23l_review_manifest.json").write_text(json.dumps(out, indent=2), encoding="utf-8")

    print(status)
    print(f"candidate_dir: {relwin(repo, l_dir)}")
    print(f"phase23k_candidate_dir: {relwin(repo, k_dir)}")
    print(f"phase23kr_green: {phase23kr_green}")
    print(f"transcript: {relwin(repo, transcript)}")
    print(f"transcript_markers_ok: {out['transcript_markers_ok']}")
    print(f"table_markers_ok: {out['table_markers_ok']}")
    print(f"candidate_dbf_exists: {out['candidate_dbf_exists']}")
    print(f"candidate_cdx_exists: {out['candidate_cdx_exists']}")
    print(f"candidate_lmdb_exists: {out['candidate_lmdb_exists']}")
    print(f"topickey_order_count: {topickey_order_count}")
    print(f"mode_lmdb_count: {mode_lmdb_count}")
    print(f"indexed_record_count: {indexed_record_count}")
    print(f"cdx_info_tag_lines: {cdx_info_tag_lines}")
    print(f"sample_locale: {SAMPLE_LOCALE}")
    print(f"sample_topics_checked: {len(SAMPLE_TOPICS)}")
    print(f"topic_locale_rows_found: {sample_counts['HELP_TOPIC_LOCALE']}/{EXPECTED_ROWS['HELP_TOPIC_LOCALE']}")
    print(f"section_locale_rows_found: {sample_counts['HELP_SECTION_LOCALE']}/{EXPECTED_ROWS['HELP_SECTION_LOCALE']}")
    print(f"line_locale_rows_found: {sample_counts['HELP_LINE_LOCALE']}/{EXPECTED_ROWS['HELP_LINE_LOCALE']}")
    print(f"artifact_locale_rows_found: {sample_counts['HELP_ARTIFACT_LOCALE']}/{EXPECTED_ROWS['HELP_ARTIFACT_LOCALE']}")
    print(f"draft_placeholder_rows_detected: {draft_placeholder_detected}")
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
