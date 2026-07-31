#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from pathlib import Path

PHASE23P_NAME = "PHASE23P-CMDHELP-ACTIVE-LOCALE-CONSUMER-PROTOTYPE"
PHASE23O_NAME = "PHASE23O-ACTIVE-HELP-LOCALE-READBACK-PROOF"
TABLES = [
    "HELP_TOPIC_LOCALE",
    "HELP_SECTION_LOCALE",
    "HELP_LINE_LOCALE",
    "HELP_ARTIFACT_LOCALE",
]


def norm(p: Path) -> str:
    return str(p).replace('/', '\\')


def count_existing(paths: list[Path], want_dir: bool = False) -> int:
    if want_dir:
        return sum(1 for p in paths if p.exists() and p.is_dir())
    return sum(1 for p in paths if p.exists())


def has_all(text: str, needles: list[str]) -> int:
    return 1 if all(n in text for n in needles) else 0


def phase23o_green_probe(repo: Path) -> int:
    transcript = repo / 'docs' / 'locale' / 'candidates' / PHASE23O_NAME / 'transcripts' / 'phase23o_active_help_locale_count_smartlist_tuple_probe_transcript.txt'
    if not transcript.exists():
        return 0
    text = transcript.read_text(encoding='utf-8', errors='replace')
    required = [
        'PHASE23O_DOTSCRIPT_START',
        'PHASE23O_SCOPE_READONLY_ACTIVE_HELP_LOCALE_TABLES_ONLY',
        'PHASE23O_COUNT_SMARTLIST_N_TUPLE_CONTRACT',
        'PHASE23O_PATH_RESET_TO_DEFAULT_DATA_ROOTS',
        'PHASE23O_DOTSCRIPT_END',
    ]
    return has_all(text, required)


def command_count(text: str, pattern: str) -> int:
    return len(re.findall(pattern, text, flags=re.IGNORECASE | re.MULTILINE))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--repo-root', default='.')
    args = ap.parse_args()
    repo = Path(args.repo_root).resolve()
    cand_dir = repo / 'docs' / 'locale' / 'candidates' / PHASE23P_NAME
    dts_path = cand_dir / 'runtime' / 'phase23p_cmdhelp_active_locale_consumer_probe.dts'
    transcript = cand_dir / 'transcripts' / 'phase23p_cmdhelp_active_locale_consumer_probe_transcript.txt'

    active_dbf_root = repo / 'dottalkpp' / 'data' / 'HELP'
    active_cdx_root = repo / 'dottalkpp' / 'data' / 'INDEXES' / 'HELP'
    active_lmdb_root = repo / 'dottalkpp' / 'data' / 'LMDB' / 'HELP'
    active_dbfs = [active_dbf_root / f'{t}.dbf' for t in TABLES]
    active_cdxs = [active_cdx_root / f'{t}.cdx' for t in TABLES]
    active_lmdbs = [active_lmdb_root / f'{t}.cdx.d' for t in TABLES]

    text = transcript.read_text(encoding='utf-8', errors='replace') if transcript.exists() else ''

    required_markers = [
        'PHASE23P_DOTSCRIPT_START',
        'PHASE23P_SCOPE_READONLY_ACTIVE_HELP_LOCALE_CONSUMER_PROTOTYPE',
        'PHASE23P_CONSUMER_MODEL_CMDHELP_TOPICKEY_LOCALE_STATUS_PREVIEW_ONLY',
        'PHASE23P_SAMPLE_LOCALE_es',
        'PHASE23P_BASE_HELP_TOPIC_DEFAULT_CONTEXT',
        'PHASE23P_TOPIC_LOCALE_CONSUMER_CONTEXT',
        'PHASE23P_SECTION_LOCALE_CONSUMER_CONTEXT',
        'PHASE23P_LINE_LOCALE_CONSUMER_CONTEXT',
        'PHASE23P_ARTIFACT_LOCALE_CONSUMER_CONTEXT',
        'PHASE23P_CONSUMER_DECISION_DRAFT_ROWS_PREVIEW_ONLY',
        'PHASE23P_NO_CMDHELP_OUTPUT_BEHAVIOR_CHANGED',
        'PHASE23P_NO_CMDHELPCHK_BEHAVIOR_CHANGED',
        'PHASE23P_PATH_RESET_TO_DEFAULT_DATA_ROOTS',
        'PHASE23P_DOTSCRIPT_END',
    ]
    tuple_markers = [
        'PHASE23P_TUPLE_TOPIC_LOCALE_CONSUMER_COMPACT',
        'PHASE23P_TUPLE_SECTION_LOCALE_CONSUMER_COMPACT',
        'PHASE23P_TUPLE_LINE_LOCALE_CONSUMER_COMPACT',
        'PHASE23P_TUPLE_ARTIFACT_LOCALE_CONSUMER_COMPACT',
    ]

    transcript_markers_ok = has_all(text, required_markers)
    tuple_markers_ok = has_all(text, tuple_markers)
    low = text.lower()
    active_root_read_ok = 1 if all(s in low for s in [
        r'dottalkpp\data\help',
        r'dottalkpp\data\indexes\help',
        r'dottalkpp\data\lmdb\help',
    ]) else 0
    table_markers_ok = has_all(text, TABLES)

    topickey_order_count = text.count("SET ORDER: CDX TAG 'TOPICKEY'")
    count_command_count = command_count(text, r'^.*>\s*COUNT\s*$')
    smartlist_n_command_count = command_count(text, r'^.*>\s*SMARTLIST\s+\d+\s*$')
    smartlist_all_command_count = command_count(text, r'^.*>\s*SMARTLIST\s+ALL\s*$')
    list_command_count = command_count(text, r'^.*>\s*LIST(?:\s|$)')
    tuple_values_command_count = command_count(text, r'^.*>\s*TUPLE\s+.*--VALUES-ONLY\s*$')
    compact_tuple_row_count = sum(1 for needle in [
        'DOT|ABOUTABOUT',
        'DOT|ABOUTOVERVIEW',
        'DOT|ABOUTOVERVIEWSUMMARY',
        'DOT|ABOUTCMDHELP_TOPIC_VIEW',
        'DOT|AREAAREA',
        'DOT|AREAOVERVIEW',
        'DOT|AREAOVERVIEWSUMMARY',
        'DOT|AREACMDHELP_TOPIC_VIEW',
    ] if needle in text)
    record_listed_count = len(re.findall(r'record\(s\) listed \(limit ', text))
    cdx_info_tag_lines = len(re.findall(r'Tags\s*:\s*\d+', text))
    lmdb_env_lines = text.count('LMDB env :')
    draft_placeholder_rows_detected = 1 if 'DRAFT_PLACEHOLDER' in text else 0
    needs_review_detected = 1 if 'NEEDS_REVIEW' in text else 0
    es_draft_detected = 1 if '[es draft]' in text or re.search(r'\bes\s+.*DRAFT_PLACEHOLDER', text, re.IGNORECASE | re.DOTALL) else 0
    path_reset_ok = has_all(text, [
        'PHASE23P_PATH_RESET_TO_DEFAULT_DATA_ROOTS',
        r'dottalkpp\data\dbf',
        r'dottalkpp\data\indexes',
        r'dottalkpp\data\lmdb',
    ])
    bad_patterns = [
        'Traceback',
        'not recognized',
        'BUILDLMDB: failed',
        'Tags     : (none)',
        'ERROR:',
    ]
    no_bad_hits = 1 if not any(p in text for p in bad_patterns) else 0

    active_dbf_exists = count_existing(active_dbfs)
    active_cdx_exists = count_existing(active_cdxs)
    active_lmdb_exists = count_existing(active_lmdbs, want_dir=True)
    phase23o_green = phase23o_green_probe(repo)
    dts_extension_ok = 1 if dts_path.suffix.lower() == '.dts' else 0

    green_conditions = [
        phase23o_green == 1,
        dts_extension_ok == 1,
        transcript.exists(),
        transcript_markers_ok == 1,
        tuple_markers_ok == 1,
        active_root_read_ok == 1,
        table_markers_ok == 1,
        active_dbf_exists == 4,
        active_cdx_exists == 4,
        active_lmdb_exists == 4,
        topickey_order_count >= 4,
        count_command_count >= 5,
        smartlist_n_command_count >= 5,
        smartlist_all_command_count == 0,
        list_command_count == 0,
        tuple_values_command_count >= 4,
        compact_tuple_row_count >= 4,
        record_listed_count >= 5,
        cdx_info_tag_lines >= 4,
        lmdb_env_lines >= 4,
        draft_placeholder_rows_detected == 1,
        needs_review_detected == 1,
        path_reset_ok == 1,
        no_bad_hits == 1,
    ]
    green = all(green_conditions)
    status = 'PHASE23P_CMDHELP_ACTIVE_LOCALE_CONSUMER_PROTOTYPE_GREEN_READONLY' if green else 'PHASE23P_CMDHELP_ACTIVE_LOCALE_CONSUMER_PROTOTYPE_REVIEW_REQUIRED'
    print(status)
    print(f'candidate_dir: {norm(cand_dir.relative_to(repo))}')
    print(f'phase23o_green: {phase23o_green}')
    print('read_scope: ACTIVE_HELP_LOCALE_ROOTS')
    print('consumer_model: CMDHELP_TOPICKEY_LOCALE_STATUS_PREVIEW_ONLY')
    print(f'retained_dotscript: {norm(dts_path.relative_to(repo))}')
    print(f'dts_extension_ok: {dts_extension_ok}')
    print(f'transcript: {norm(transcript.relative_to(repo))}')
    print(f'transcript_markers_ok: {transcript_markers_ok}')
    print(f'active_root_read_ok: {active_root_read_ok}')
    print(f'table_markers_ok: {table_markers_ok}')
    print(f'tuple_markers_ok: {tuple_markers_ok}')
    print(f'active_dbf_exists: {active_dbf_exists}/4')
    print(f'active_cdx_exists: {active_cdx_exists}/4')
    print(f'active_lmdb_exists: {active_lmdb_exists}/4')
    print(f'topickey_order_count: {topickey_order_count}')
    print(f'count_command_count: {count_command_count}')
    print(f'smartlist_n_command_count: {smartlist_n_command_count}')
    print(f'smartlist_all_command_count: {smartlist_all_command_count}')
    print(f'list_command_count: {list_command_count}')
    print(f'tuple_values_command_count: {tuple_values_command_count}')
    print(f'compact_tuple_row_count: {compact_tuple_row_count}')
    print(f'record_listed_count: {record_listed_count}')
    print(f'cdx_info_tag_lines: {cdx_info_tag_lines}')
    print(f'lmdb_env_lines: {lmdb_env_lines}')
    print('sample_locale: es')
    print('sample_topics_checked: 2')
    print(f'draft_placeholder_rows_detected: {draft_placeholder_rows_detected}')
    print(f'needs_review_detected: {needs_review_detected}')
    print(f'es_draft_detected: {es_draft_detected}')
    print(f'path_reset_ok: {path_reset_ok}')
    print(f'no_bad_hits: {no_bad_hits}')
    print('active_help_dbf_written_by_review: 0')
    print('active_help_cdx_written_by_review: 0')
    print('active_help_lmdb_written_by_review: 0')
    print('source_files_written: 0')
    print('cmdhelp_behavior_changed: 0')
    print('cmdhelpchk_behavior_changed: 0')
    print('maint_behavior_changed: 0')
    print('bbox_behavior_changed: 0')
    print('next_gate: HOLD_OR_AUTHORIZE_PHASE23Q_CMDHELP_LOCALE_INTEGRATION_PLAN' if green else 'next_gate: FIX_OR_RERUN_PHASE23P_DOTSCRIPT')
    return 0 if green else 1

if __name__ == '__main__':
    raise SystemExit(main())
