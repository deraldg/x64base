#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from datetime import datetime, timezone

PHASE23P_NAME = "PHASE23P-CMDHELP-ACTIVE-LOCALE-CONSUMER-PROTOTYPE"
PHASE23O_NAME = "PHASE23O-ACTIVE-HELP-LOCALE-READBACK-PROOF"
TABLES = [
    "HELP_TOPIC_LOCALE",
    "HELP_SECTION_LOCALE",
    "HELP_LINE_LOCALE",
    "HELP_ARTIFACT_LOCALE",
]
SMARTLIST_LIMITS = {
    "HELP_TOPIC_LOCALE": 10,
    "HELP_SECTION_LOCALE": 10,
    "HELP_LINE_LOCALE": 30,
    "HELP_ARTIFACT_LOCALE": 10,
}


def norm(p: Path) -> str:
    return str(p).replace('/', '\\')


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8', newline='\n')


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            w.writerow(r)


def exists_count(paths: list[Path]) -> int:
    return sum(1 for p in paths if p.exists())


def dir_exists_count(paths: list[Path]) -> int:
    return sum(1 for p in paths if p.exists() and p.is_dir())


def phase23o_green_probe(repo: Path) -> int:
    transcript = repo / 'docs' / 'locale' / 'candidates' / PHASE23O_NAME / 'transcripts' / 'phase23o_active_help_locale_count_smartlist_tuple_probe_transcript.txt'
    if not transcript.exists():
        return 0
    text = transcript.read_text(encoding='utf-8', errors='replace')
    required = [
        'PHASE23O_DOTSCRIPT_START',
        'PHASE23O_SCOPE_READONLY_ACTIVE_HELP_LOCALE_TABLES_ONLY',
        'PHASE23O_COUNT_SMARTLIST_N_TUPLE_CONTRACT',
        'PHASE23O_NO_LIST_NO_SMARTLIST_ALL',
        'PHASE23O_PATH_RESET_TO_DEFAULT_DATA_ROOTS',
        'PHASE23O_DOTSCRIPT_END',
        r'dottalkpp\data\help',
        'HELP_TOPIC_LOCALE',
        'HELP_LINE_LOCALE',
    ]
    low = text.lower()
    return 1 if all(x.lower() in low for x in required) else 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--repo-root', default='.')
    args = ap.parse_args()
    repo = Path(args.repo_root).resolve()

    cand_dir = repo / 'docs' / 'locale' / 'candidates' / PHASE23P_NAME
    runtime_dir = cand_dir / 'runtime'
    reports_dir = cand_dir / 'reports'
    manifests_dir = cand_dir / 'manifests'
    transcripts_dir = cand_dir / 'transcripts'
    for d in (runtime_dir, reports_dir, manifests_dir, transcripts_dir):
        d.mkdir(parents=True, exist_ok=True)

    active_dbf_root = repo / 'dottalkpp' / 'data' / 'HELP'
    active_cdx_root = repo / 'dottalkpp' / 'data' / 'INDEXES' / 'HELP'
    active_lmdb_root = repo / 'dottalkpp' / 'data' / 'LMDB' / 'HELP'
    dbf_paths = [active_dbf_root / f'{t}.dbf' for t in TABLES]
    cdx_paths = [active_cdx_root / f'{t}.cdx' for t in TABLES]
    lmdb_paths = [active_lmdb_root / f'{t}.cdx.d' for t in TABLES]

    dts_path = runtime_dir / 'phase23p_cmdhelp_active_locale_consumer_probe.dts'
    transcript_path = transcripts_dir / 'phase23p_cmdhelp_active_locale_consumer_probe_transcript.txt'

    repo_win = norm(repo)
    lines = [
        'ECHO ON',
        'SET PAGING OFF',
        'ECHO PHASE23P_DOTSCRIPT_START',
        'ECHO PHASE23P_SCOPE_READONLY_ACTIVE_HELP_LOCALE_CONSUMER_PROTOTYPE',
        'ECHO PHASE23P_CONSUMER_MODEL_CMDHELP_TOPICKEY_LOCALE_STATUS_PREVIEW_ONLY',
        'ECHO PHASE23P_SAMPLE_LOCALE_es',
        f'SETPATH DBF {repo_win}\\dottalkpp\\data\\help',
        f'SETPATH INDEXES {repo_win}\\dottalkpp\\data\\indexes\\help',
        f'SETPATH LMDB {repo_win}\\dottalkpp\\data\\lmdb\\help',
        'WORKSPACE CLOSE',
        'WORKSPACE OPEN DBF CDX',
        'ECHO PHASE23P_BASE_HELP_TOPIC_DEFAULT_CONTEXT',
        'SELECT HELP_TOPIC',
        'AREA',
        'COUNT',
        'SMARTLIST 10',
        'ECHO PHASE23P_TOPIC_LOCALE_CONSUMER_CONTEXT',
        'SELECT HELP_TOPIC_LOCALE',
        'AREA',
        'SET INDEX TO HELP_TOPIC_LOCALE',
        'CDX INFO',
        'SET ORDER TO TAG TOPICKEY',
        'ASCEND',
        'TOP',
        'COUNT',
        'SMARTLIST 10',
        'ECHO PHASE23P_TUPLE_TOPIC_LOCALE_CONSUMER_COMPACT',
        'TUPLE TOPICKEY,COMMAND,LOCALE_ID,LOCALIZED_TITLE,TRANSL_STATUS,REVIEW_STATUS --VALUES-ONLY',
        'SET ORDER TO 0',
        'ECHO PHASE23P_SECTION_LOCALE_CONSUMER_CONTEXT',
        'SELECT HELP_SECTION_LOCALE',
        'AREA',
        'SET INDEX TO HELP_SECTION_LOCALE',
        'CDX INFO',
        'SET ORDER TO TAG TOPICKEY',
        'ASCEND',
        'TOP',
        'COUNT',
        'SMARTLIST 10',
        'ECHO PHASE23P_TUPLE_SECTION_LOCALE_CONSUMER_COMPACT',
        'TUPLE TOPICKEY,SECTION_KEY,LOCALE_ID,LOCALIZED_LABEL,TRANSL_STATUS,REVIEW_STATUS --VALUES-ONLY',
        'SET ORDER TO 0',
        'ECHO PHASE23P_LINE_LOCALE_CONSUMER_CONTEXT',
        'SELECT HELP_LINE_LOCALE',
        'AREA',
        'SET INDEX TO HELP_LINE_LOCALE',
        'CDX INFO',
        'SET ORDER TO TAG TOPICKEY',
        'ASCEND',
        'TOP',
        'COUNT',
        'SMARTLIST 30',
        'ECHO PHASE23P_TUPLE_LINE_LOCALE_CONSUMER_COMPACT',
        'TUPLE TOPICKEY,SECTION_KEY,KIND,ROLE,LOCALE_ID,LOCALIZED_LABEL,TRANSL_STATUS,REVIEW_STATUS --VALUES-ONLY',
        'SET ORDER TO 0',
        'ECHO PHASE23P_ARTIFACT_LOCALE_CONSUMER_CONTEXT',
        'SELECT HELP_ARTIFACT_LOCALE',
        'AREA',
        'SET INDEX TO HELP_ARTIFACT_LOCALE',
        'CDX INFO',
        'SET ORDER TO TAG TOPICKEY',
        'ASCEND',
        'TOP',
        'COUNT',
        'SMARTLIST 10',
        'ECHO PHASE23P_TUPLE_ARTIFACT_LOCALE_CONSUMER_COMPACT',
        'TUPLE TOPICKEY,ARTIFACT_KIND,LOCALE_ID,TRANSL_STATUS,REVIEW_STATUS --VALUES-ONLY',
        'SET ORDER TO 0',
        'ECHO PHASE23P_CONSUMER_DECISION_DRAFT_ROWS_PREVIEW_ONLY',
        'ECHO PHASE23P_NO_CMDHELP_OUTPUT_BEHAVIOR_CHANGED',
        'ECHO PHASE23P_NO_CMDHELPCHK_BEHAVIOR_CHANGED',
        'WORKSPACE CLOSE',
        'ECHO PHASE23P_PATH_RESET_TO_DEFAULT_DATA_ROOTS',
        f'SETPATH DBF {repo_win}\\dottalkpp\\data\\dbf',
        f'SETPATH INDEXES {repo_win}\\dottalkpp\\data\\indexes',
        f'SETPATH LMDB {repo_win}\\dottalkpp\\data\\lmdb',
        'ECHO PHASE23P_DOTSCRIPT_END',
        '',
    ]
    write_text(dts_path, '\n'.join(lines))

    manual_command = f'DOTSCRIPT TRACE {norm(dts_path)} OUT {norm(transcript_path)}'

    plan_rows = []
    for table in TABLES:
        plan_rows.append({
            'table': table,
            'active_dbf': norm(active_dbf_root / f'{table}.dbf'),
            'active_cdx': norm(active_cdx_root / f'{table}.cdx'),
            'active_lmdb': norm(active_lmdb_root / f'{table}.cdx.d'),
            'consumer_role': 'active locale sidecar lookup by TOPICKEY plus LOCALE_ID/status fields',
            'smartlist_limit': SMARTLIST_LIMITS[table],
        })
    write_csv(reports_dir / 'phase23p_cmdhelp_active_locale_consumer_plan.csv', plan_rows,
              ['table','active_dbf','active_cdx','active_lmdb','consumer_role','smartlist_limit'])

    phase23o_green = phase23o_green_probe(repo)
    manifest = {
        'phase': 'PHASE23P',
        'status': 'PHASE23P_CMDHELP_ACTIVE_LOCALE_CONSUMER_PROTOTYPE_STAGING_GREEN_MANUAL_DOTSCRIPT_REQUIRED',
        'created_at': datetime.now(timezone.utc).isoformat(),
        'candidate_dir': norm(cand_dir.relative_to(repo)),
        'phase23o_green_probe': phase23o_green,
        'read_scope': 'ACTIVE_HELP_LOCALE_ROOTS',
        'active_roots': [
            norm(active_dbf_root.relative_to(repo)),
            norm(active_cdx_root.relative_to(repo)),
            norm(active_lmdb_root.relative_to(repo)),
        ],
        'candidate_tables': TABLES,
        'retained_dotscript': norm(dts_path.relative_to(repo)),
        'expected_transcript': norm(transcript_path.relative_to(repo)),
        'manual_run_command': manual_command,
        'source_files_written': 0,
        'active_help_dbf_written': 0,
        'active_help_cdx_written': 0,
        'active_help_lmdb_written': 0,
        'cmdhelp_behavior_changed': 0,
        'cmdhelpchk_behavior_changed': 0,
        'maint_behavior_changed': 0,
        'bbox_behavior_changed': 0,
        'runtime_execution_by_python': 0,
        'next_gate': 'HOLD_OR_RUN_PHASE23P_DOTSCRIPT_AND_REVIEW_TRANSCRIPT',
    }
    write_text(manifests_dir / 'phase23p_cmdhelp_active_locale_consumer_prototype_manifest.json',
               json.dumps(manifest, indent=2) + '\n')

    report = (
        '# PHASE23P CMDHELP Active Locale Consumer Prototype Staging\n\n'
        'Status: `PHASE23P_CMDHELP_ACTIVE_LOCALE_CONSUMER_PROTOTYPE_STAGING_GREEN_MANUAL_DOTSCRIPT_REQUIRED`\n\n'
        'Scope: read-only active HELP locale sidecar consumer prototype.\n\n'
        'This stage does not alter CMDHELP behavior. It proves active HELP base context, active locale sidecar readback, TOPICKEY ordering, bounded SMARTLIST, and compact tuple proof rows.\n\n'
        'Manual DotTalk++ command:\n\n'
        '```text\n' + manual_command + '\n\n```\n\n'
        'Review after running DotScript:\n\n'
        '```powershell\n'
        '$py12 = "D:\\code\\ccode\\build\\vcpkg_installed\\x64-windows\\tools\\python3\\python.exe"\n'
        '& $py12 .\\tools\\maintenance\\phase23p_review_cmdhelp_active_locale_consumer_prototype.py --repo-root .\n'
        '```\n'
    )
    write_text(reports_dir / 'PHASE23P_CMDHELP_ACTIVE_LOCALE_CONSUMER_PROTOTYPE.md', report)

    active_dbf_count = exists_count(dbf_paths)
    active_cdx_count = exists_count(cdx_paths)
    active_lmdb_count = dir_exists_count(lmdb_paths)

    print('PHASE23P_CMDHELP_ACTIVE_LOCALE_CONSUMER_PROTOTYPE_STAGING_GREEN_MANUAL_DOTSCRIPT_REQUIRED')
    print(f'candidate_dir: {norm(cand_dir.relative_to(repo))}')
    print(f'phase23o_green: {phase23o_green}')
    print('read_scope: ACTIVE_HELP_LOCALE_ROOTS')
    print('active_roots: dottalkpp\\data\\HELP,dottalkpp\\data\\INDEXES\\HELP,dottalkpp\\data\\LMDB\\HELP')
    print(f'active_dbf_exists: {active_dbf_count}/4')
    print(f'active_cdx_exists: {active_cdx_count}/4')
    print(f'active_lmdb_exists: {active_lmdb_count}/4')
    print('candidate_tables: 4')
    print('consumer_model: CMDHELP_TOPICKEY_LOCALE_STATUS_PREVIEW_ONLY')
    print('sample_locale: es')
    print('list_commands_planned: 0')
    print('smartlist_all_commands_planned: 0')
    print(f'retained_dotscript: {norm(dts_path.relative_to(repo))}')
    print(f'expected_transcript: {norm(transcript_path.relative_to(repo))}')
    print(f'manual_run_command: {manual_command}')
    print('source_files_written: 0')
    print('active_help_dbf_written: 0')
    print('active_help_cdx_written: 0')
    print('active_help_lmdb_written: 0')
    print('cmdhelp_behavior_changed: 0')
    print('cmdhelpchk_behavior_changed: 0')
    print('maint_behavior_changed: 0')
    print('bbox_behavior_changed: 0')
    print('runtime_execution_by_python: 0')
    print('next_gate: HOLD_OR_RUN_PHASE23P_DOTSCRIPT_AND_REVIEW_TRANSCRIPT')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
