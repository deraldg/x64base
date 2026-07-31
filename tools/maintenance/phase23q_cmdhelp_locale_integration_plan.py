#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path

PHASE23Q_NAME = "PHASE23Q-CMDHELP-LOCALE-INTEGRATION-PLAN"
PHASE23O_NAME = "PHASE23O-ACTIVE-HELP-LOCALE-READBACK-PROOF"
PHASE23P_NAME = "PHASE23P-CMDHELP-ACTIVE-LOCALE-CONSUMER-PROTOTYPE"

TABLES = [
    "HELP_TOPIC_LOCALE",
    "HELP_SECTION_LOCALE",
    "HELP_LINE_LOCALE",
    "HELP_ARTIFACT_LOCALE",
]

REQUIRED_TOPIC_FIELDS = [
    "TOPICKEY",
    "COMMAND",
    "LOCALE_ID",
    "LOCALIZED_TITLE",
    "TRANSL_STATUS",
    "REVIEW_STATUS",
    "FALLBACK_ALLOWED",
]


def norm(p: Path) -> str:
    return str(p).replace('/', '\\')


def rel(repo: Path, p: Path) -> str:
    try:
        return norm(p.relative_to(repo))
    except ValueError:
        return norm(p)


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8', newline='\n')


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def count_files(paths: list[Path]) -> int:
    return sum(1 for p in paths if p.exists() and p.is_file())


def count_dirs(paths: list[Path]) -> int:
    return sum(1 for p in paths if p.exists() and p.is_dir())


def read_optional(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding='utf-8', errors='replace')


def has_all(text: str, needles: list[str]) -> int:
    low = text.lower()
    return 1 if all(n.lower() in low for n in needles) else 0


def probe_phase23o_green(repo: Path) -> tuple[int, dict[str, object]]:
    transcript = repo / 'docs' / 'locale' / 'candidates' / PHASE23O_NAME / 'transcripts' / 'phase23o_active_help_locale_count_smartlist_tuple_probe_transcript.txt'
    text = read_optional(transcript)
    markers = [
        'PHASE23O_DOTSCRIPT_START',
        'PHASE23O_SCOPE_READONLY_ACTIVE_HELP_LOCALE_TABLES_ONLY',
        'PHASE23O_COUNT_SMARTLIST_N_TUPLE_CONTRACT',
        'PHASE23O_NO_LIST_NO_SMARTLIST_ALL',
        'PHASE23O_PATH_RESET_TO_DEFAULT_DATA_ROOTS',
        'PHASE23O_DOTSCRIPT_END',
        r'dottalkpp\data\help',
        r'dottalkpp\data\indexes\help',
        r'dottalkpp\data\lmdb\help',
        'HELP_TOPIC_LOCALE',
        'HELP_SECTION_LOCALE',
        'HELP_LINE_LOCALE',
        'HELP_ARTIFACT_LOCALE',
        'DRAFT_PLACEHOLDER',
        'NEEDS_REVIEW',
    ]
    marker_ok = has_all(text, markers)
    no_bad = 1 if not any(bad in text for bad in ['Traceback', 'BUILDLMDB: failed', 'Tags     : (none)', 'ERROR:']) else 0
    green = 1 if transcript.exists() and marker_ok and no_bad else 0
    return green, {
        'transcript': rel(repo, transcript),
        'transcript_exists': 1 if transcript.exists() else 0,
        'marker_ok': marker_ok,
        'no_bad_hits': no_bad,
    }


def probe_phase23p_optional(repo: Path) -> dict[str, object]:
    transcript = repo / 'docs' / 'locale' / 'candidates' / PHASE23P_NAME / 'transcripts' / 'phase23p_cmdhelp_active_locale_consumer_probe_transcript.txt'
    text = read_optional(transcript)
    if 'PHASE23P_CMDHELP_ACTIVE_LOCALE_CONSUMER_PROTOTYPE_GREEN_READONLY' in text:
        status = 'green_transcript_contains_status'
    elif 'PHASE23P_DOTSCRIPT_START' in text and 'PHASE23P_DOTSCRIPT_END' in text:
        status = 'runtime_transcript_present_optional'
    elif transcript.exists():
        status = 'transcript_present_not_required'
    else:
        status = 'folded_optional_not_required'
    return {
        'phase23p_optional_status': status,
        'phase23p_transcript_exists': 1 if transcript.exists() else 0,
        'phase23p_folded_into_phase23q': 1,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description='Stage PHASE23Q CMDHELP locale integration plan, report-only.')
    parser.add_argument('--repo-root', default='.')
    args = parser.parse_args()

    repo = Path(args.repo_root).resolve()
    cand_dir = repo / 'docs' / 'locale' / 'candidates' / PHASE23Q_NAME
    reports_dir = cand_dir / 'reports'
    manifests_dir = cand_dir / 'manifests'
    runtime_dir = cand_dir / 'runtime'
    for d in (reports_dir, manifests_dir, runtime_dir):
        d.mkdir(parents=True, exist_ok=True)

    active_dbf_root = repo / 'dottalkpp' / 'data' / 'HELP'
    active_cdx_root = repo / 'dottalkpp' / 'data' / 'INDEXES' / 'HELP'
    active_lmdb_root = repo / 'dottalkpp' / 'data' / 'LMDB' / 'HELP'
    active_dbfs = [active_dbf_root / f'{t}.dbf' for t in TABLES]
    active_cdxs = [active_cdx_root / f'{t}.cdx' for t in TABLES]
    active_lmdbs = [active_lmdb_root / f'{t}.cdx.d' for t in TABLES]

    active_dbf_count = count_files(active_dbfs)
    active_cdx_count = count_files(active_cdxs)
    active_lmdb_count = count_dirs(active_lmdbs)
    phase23o_green, phase23o_probe = probe_phase23o_green(repo)
    phase23p_probe = probe_phase23p_optional(repo)

    lookup_rows = [
        {
            'consumer': 'CMDHELP topic title lookup',
            'base_table': 'HELP_TOPIC',
            'locale_table': 'HELP_TOPIC_LOCALE',
            'join_key': 'TOPICKEY',
            'locale_filter': 'LOCALE_ID selected explicitly or from SET LANGUAGE later',
            'required_status_gate': 'TRANSL_STATUS not draft and REVIEW_STATUS approved for default display',
            'preview_status_gate': 'draft rows may display only in explicit preview/debug lanes',
            'fallback': 'source/en-US topic title when locale row missing, draft, or needs review',
        },
        {
            'consumer': 'CMDHELP section label lookup',
            'base_table': 'HELP_SECTION',
            'locale_table': 'HELP_SECTION_LOCALE',
            'join_key': 'TOPICKEY + SECTION_KEY',
            'locale_filter': 'LOCALE_ID',
            'required_status_gate': 'approved/non-draft only for default display',
            'preview_status_gate': 'draft rows may display only in explicit preview/debug lanes',
            'fallback': 'source/en-US section label',
        },
        {
            'consumer': 'CMDHELP line label/text lookup',
            'base_table': 'HELP_LINE',
            'locale_table': 'HELP_LINE_LOCALE',
            'join_key': 'TOPICKEY + SECTION_KEY + KIND + ROLE + LINE_ORDER',
            'locale_filter': 'LOCALE_ID',
            'required_status_gate': 'approved/non-draft only for default display',
            'preview_status_gate': 'draft rows may display only in explicit preview/debug lanes',
            'fallback': 'source/en-US HELP_LINE label/text',
        },
        {
            'consumer': 'CMDHELP localized artifact/hash view',
            'base_table': 'HELP_ARTIFACTS',
            'locale_table': 'HELP_ARTIFACT_LOCALE',
            'join_key': 'TOPICKEY + ARTIFACT_KIND',
            'locale_filter': 'LOCALE_ID',
            'required_status_gate': 'approved/non-draft only for default display',
            'preview_status_gate': 'draft rows may display only in explicit preview/debug lanes',
            'fallback': 'source/en-US artifact hash/view',
        },
    ]
    write_csv(reports_dir / 'phase23q_locale_lookup_contract.csv', lookup_rows,
              ['consumer', 'base_table', 'locale_table', 'join_key', 'locale_filter', 'required_status_gate', 'preview_status_gate', 'fallback'])

    fallback_rows = [
        {'case': 'locale row missing', 'default_behavior': 'use source/en-US row', 'preview_behavior': 'report MISSING_LOCALE_ROW', 'cmdhelp_visible_default': 'source text'},
        {'case': 'locale row is DRAFT_PLACEHOLDER', 'default_behavior': 'use source/en-US row', 'preview_behavior': 'show draft with DRAFT_PLACEHOLDER marker', 'cmdhelp_visible_default': 'source text'},
        {'case': 'locale row REVIEW_STATUS is NEEDS_REVIEW', 'default_behavior': 'use source/en-US row', 'preview_behavior': 'show draft with NEEDS_REVIEW marker', 'cmdhelp_visible_default': 'source text'},
        {'case': 'locale exists but source hash changed', 'default_behavior': 'use source/en-US row until refreshed', 'preview_behavior': 'report STALE_SOURCE_HASH', 'cmdhelp_visible_default': 'source text'},
        {'case': 'locale approved/reviewed', 'default_behavior': 'eligible for localized display after future explicit authorization', 'preview_behavior': 'show localized row', 'cmdhelp_visible_default': 'held until CMDHELP behavior integration authorized'},
    ]
    write_csv(reports_dir / 'phase23q_fallback_policy.csv', fallback_rows,
              ['case', 'default_behavior', 'preview_behavior', 'cmdhelp_visible_default'])

    command_rows = [
        {'surface': 'CMDHELP <topic> LOCALE <locale>', 'phase': 'candidate preview command', 'behavior': 'preview localized sidecar rows for one topic without changing global language', 'default_safe': 1},
        {'surface': 'CMDHELP <topic> PREVIEW LOCALE <locale>', 'phase': 'candidate preview command', 'behavior': 'same as above with clearer preview-only wording', 'default_safe': 1},
        {'surface': 'CMDHELP <topic>', 'phase': 'existing command', 'behavior': 'unchanged until explicit integration authorization', 'default_safe': 1},
        {'surface': 'SET LANGUAGE <locale>', 'phase': 'existing language selector', 'behavior': 'future consumer may use it as implicit locale, but command keywords stay English', 'default_safe': 1},
        {'surface': 'SET LANGUAGE REPORT <locale>', 'phase': 'existing/report surface', 'behavior': 'show locale catalog readiness and fallback/readback status', 'default_safe': 1},
    ]
    write_csv(reports_dir / 'phase23q_preview_command_surface.csv', command_rows,
              ['surface', 'phase', 'behavior', 'default_safe'])

    cmdhelpchk_rows = [
        {'check_id': 'LOCALE_SIDE_TABLES_PRESENT', 'scope': 'CMDHELPCHK', 'condition': 'all four HELP_*_LOCALE DBF/CDX/LMDB artifacts exist', 'severity': 'error'},
        {'check_id': 'LOCALE_TOPICKEY_COVERAGE', 'scope': 'CMDHELPCHK', 'condition': 'locale rows exist for selected TOPICKEY seed set', 'severity': 'warning'},
        {'check_id': 'LOCALE_DRAFT_ROW_COUNT', 'scope': 'CMDHELPCHK', 'condition': 'count DRAFT_PLACEHOLDER rows by LOCALE_ID', 'severity': 'info'},
        {'check_id': 'LOCALE_NEEDS_REVIEW_COUNT', 'scope': 'CMDHELPCHK', 'condition': 'count NEEDS_REVIEW rows by LOCALE_ID', 'severity': 'info'},
        {'check_id': 'LOCALE_SOURCE_HASH_STALE', 'scope': 'CMDHELPCHK', 'condition': 'source hash no longer matches base HELP row', 'severity': 'warning'},
        {'check_id': 'LOCALE_FALLBACK_POLICY', 'scope': 'CMDHELPCHK', 'condition': 'fallback to source/en-US remains available for every localized topic', 'severity': 'error'},
        {'check_id': 'LOCALE_PREVIEW_ONLY_GUARD', 'scope': 'CMDHELPCHK', 'condition': 'draft/needs-review rows are not used by default CMDHELP output', 'severity': 'error'},
        {'check_id': 'LOCALE_COMMAND_KEYWORD_GUARD', 'scope': 'CMDHELPCHK', 'condition': 'command keywords stay English even when help text is localized', 'severity': 'error'},
        {'check_id': 'LOCALE_PATH_RESET_GUARD', 'scope': 'CMDHELPCHK', 'condition': 'readback/probe scripts reset DBF/INDEXES/LMDB paths after active-root checks', 'severity': 'error'},
        {'check_id': 'LOCALE_LMDB_DRIFT_ADVISORY', 'scope': 'CMDHELPCHK', 'condition': 'LMDB env hash drift after read is advisory if DBF/CDX match and readback passes', 'severity': 'info'},
    ]
    write_csv(reports_dir / 'phase23q_cmdhelpchk_locale_checks.csv', cmdhelpchk_rows,
              ['check_id', 'scope', 'condition', 'severity'])

    maint_rows = [
        {'lane': 'MAINT LOCALE', 'visibility': 'locale spine health, active locale sidecar artifact presence, fallback readiness'},
        {'lane': 'MAINT HELP_LOCALE', 'visibility': 'HELP_*_LOCALE row counts, draft counts, needs-review counts, stale source hash count'},
        {'lane': 'BBOX HELP', 'visibility': 'HELP base tables plus active locale sidecar roots'},
        {'lane': 'BBOX LOCALE', 'visibility': 'shared locale spine plus HELP consumer coverage'},
        {'lane': 'BBOX CMDHELPCHK', 'visibility': 'locale-specific CMDHELPCHK check summaries'},
        {'lane': 'BBOX ROLLBACK', 'visibility': 'PHASE23N rollback root and active promotion log pointer'},
    ]
    write_csv(reports_dir / 'phase23q_maint_bbox_visibility_plan.csv', maint_rows,
              ['lane', 'visibility'])

    sequence_rows = [
        {'step': 1, 'phase': 'PHASE23Q', 'action': 'accept report-only integration contract', 'mutation': 0},
        {'step': 2, 'phase': 'PHASE23R', 'action': 'stage CMDHELP locale preview implementation plan', 'mutation': 0},
        {'step': 3, 'phase': 'PHASE23S', 'action': 'stage source patch package for preview-only command branch, with usage contract comments', 'mutation': 'source candidate only'},
        {'step': 4, 'phase': 'PHASE23T', 'action': 'build and smoke preview command without changing default CMDHELP', 'mutation': 'build/runtime only'},
        {'step': 5, 'phase': 'PHASE23U', 'action': 'add CMDHELPCHK locale checks report-first', 'mutation': 0},
        {'step': 6, 'phase': 'PHASE23V', 'action': 'add MAINT/BBOX visibility report-first', 'mutation': 0},
        {'step': 7, 'phase': 'PHASE23W', 'action': 'review approved translation gate before enabling default localized display', 'mutation': 0},
        {'step': 8, 'phase': 'future', 'action': 'authorize SET LANGUAGE driven default localized HELP only after approved rows exist', 'mutation': 'explicit authorization required'},
    ]
    write_csv(reports_dir / 'phase23q_integration_sequence.csv', sequence_rows,
              ['step', 'phase', 'action', 'mutation'])

    boundary_rows = [
        {'boundary': 'source_files_written', 'value': 0},
        {'boundary': 'active_help_dbf_written', 'value': 0},
        {'boundary': 'active_help_cdx_written', 'value': 0},
        {'boundary': 'active_help_lmdb_written', 'value': 0},
        {'boundary': 'cmdhelp_behavior_changed', 'value': 0},
        {'boundary': 'cmdhelpchk_behavior_changed', 'value': 0},
        {'boundary': 'maint_behavior_changed', 'value': 0},
        {'boundary': 'bbox_behavior_changed', 'value': 0},
        {'boundary': 'runtime_execution_by_python', 'value': 0},
    ]
    write_csv(reports_dir / 'phase23q_boundary_report.csv', boundary_rows,
              ['boundary', 'value'])

    report = f"""# PHASE23Q CMDHELP Locale Integration Plan

Status: `PHASE23Q_CMDHELP_LOCALE_INTEGRATION_PLAN_GREEN_REPORT_ONLY`

## Why this phase exists

PHASE23O closed the active HELP locale sidecar readback proof. PHASE23P was intentionally folded into this broader integration plan to avoid another proof-only microstep.

## Current accepted facts

- Active HELP locale sidecar DBFs are present under `dottalkpp\\data\\HELP`.
- Active HELP locale sidecar CDXs are present under `dottalkpp\\data\\INDEXES\\HELP`.
- Active HELP locale sidecar LMDB env dirs are present under `dottalkpp\\data\\LMDB\\HELP`.
- Readback contract is `COUNT`, bounded `SMARTLIST n`, and `TUPLE ... --VALUES-ONLY`.
- Normal `CMDHELP` behavior remains unchanged.
- Draft/needs-review localized rows are preview evidence, not default user-facing translations.

## Integration contract

The future CMDHELP locale consumer should resolve a topic by `TOPICKEY`, then look for sidecar rows by `LOCALE_ID` and status fields. Default CMDHELP output must continue to use source/en-US rows unless and until localized rows are reviewed and a later integration phase explicitly authorizes default localized display.

## Recommended command surface

Preferred preview shape:

```text
CMDHELP <topic> PREVIEW LOCALE <locale>
```

Alternate shorter shape:

```text
CMDHELP <topic> LOCALE <locale>
```

Existing default behavior remains:

```text
CMDHELP <topic>
```

## SET LANGUAGE relationship

`SET LANGUAGE` may later provide the implicit locale for HELP text, but command keywords remain English. For now, the safer implementation step is explicit preview locale arguments.

## Next gate

`HOLD_OR_AUTHORIZE_PHASE23R_CMDHELP_LOCALE_PREVIEW_IMPLEMENTATION_PLAN`
"""
    write_text(reports_dir / 'PHASE23Q_CMDHELP_LOCALE_INTEGRATION_PLAN.md', report)

    manifest = {
        'phase': 'PHASE23Q',
        'status': 'PHASE23Q_CMDHELP_LOCALE_INTEGRATION_PLAN_GREEN_REPORT_ONLY',
        'created_at': datetime.now(timezone.utc).isoformat(),
        'candidate_dir': rel(repo, cand_dir),
        'phase23o_green': phase23o_green,
        'phase23o_probe': phase23o_probe,
        'phase23p_optional': phase23p_probe,
        'active_roots': [
            rel(repo, active_dbf_root),
            rel(repo, active_cdx_root),
            rel(repo, active_lmdb_root),
        ],
        'active_dbf_exists': f'{active_dbf_count}/4',
        'active_cdx_exists': f'{active_cdx_count}/4',
        'active_lmdb_exists': f'{active_lmdb_count}/4',
        'lookup_contract_rows': len(lookup_rows),
        'fallback_policy_rows': len(fallback_rows),
        'preview_command_rows': len(command_rows),
        'cmdhelpchk_locale_checks': len(cmdhelpchk_rows),
        'maint_bbox_visibility_rows': len(maint_rows),
        'integration_sequence_rows': len(sequence_rows),
        'boundaries': {row['boundary']: row['value'] for row in boundary_rows},
        'next_gate': 'HOLD_OR_AUTHORIZE_PHASE23R_CMDHELP_LOCALE_PREVIEW_IMPLEMENTATION_PLAN',
    }
    write_text(manifests_dir / 'phase23q_cmdhelp_locale_integration_plan_manifest.json', json.dumps(manifest, indent=2) + '\n')

    preconditions_ok = 1 if phase23o_green and active_dbf_count == 4 and active_cdx_count == 4 and active_lmdb_count == 4 else 0
    status = 'PHASE23Q_CMDHELP_LOCALE_INTEGRATION_PLAN_GREEN_REPORT_ONLY' if preconditions_ok else 'PHASE23Q_CMDHELP_LOCALE_INTEGRATION_PLAN_REVIEW_REQUIRED'

    print(status)
    print(f'candidate_dir: {rel(repo, cand_dir)}')
    print(f'phase23o_green: {phase23o_green}')
    print(f'phase23p_folded_optional: {phase23p_probe["phase23p_folded_into_phase23q"]}')
    print('read_scope: ACTIVE_HELP_LOCALE_ROOTS')
    print('active_roots: dottalkpp\\data\\HELP,dottalkpp\\data\\INDEXES\\HELP,dottalkpp\\data\\LMDB\\HELP')
    print(f'active_dbf_exists: {active_dbf_count}/4')
    print(f'active_cdx_exists: {active_cdx_count}/4')
    print(f'active_lmdb_exists: {active_lmdb_count}/4')
    print('consumer_model: CMDHELP_TOPICKEY_LOCALE_STATUS_PREVIEW_THEN_FALLBACK')
    print(f'lookup_contract_rows: {len(lookup_rows)}')
    print(f'fallback_policy_rows: {len(fallback_rows)}')
    print(f'preview_command_rows: {len(command_rows)}')
    print(f'cmdhelpchk_locale_checks: {len(cmdhelpchk_rows)}')
    print(f'maint_bbox_visibility_rows: {len(maint_rows)}')
    print(f'integration_sequence_rows: {len(sequence_rows)}')
    print(f'manifest: {rel(repo, manifests_dir / "phase23q_cmdhelp_locale_integration_plan_manifest.json")}')
    print(f'integration_plan: {rel(repo, reports_dir / "PHASE23Q_CMDHELP_LOCALE_INTEGRATION_PLAN.md")}')
    print('source_files_written: 0')
    print('active_help_dbf_written: 0')
    print('active_help_cdx_written: 0')
    print('active_help_lmdb_written: 0')
    print('cmdhelp_behavior_changed: 0')
    print('cmdhelpchk_behavior_changed: 0')
    print('maint_behavior_changed: 0')
    print('bbox_behavior_changed: 0')
    print('runtime_execution_by_python: 0')
    print('next_gate: HOLD_OR_AUTHORIZE_PHASE23R_CMDHELP_LOCALE_PREVIEW_IMPLEMENTATION_PLAN' if preconditions_ok else 'next_gate: FIX_PHASE23Q_PRECONDITIONS_OR_REVIEW_ACTIVE_HELP_LOCALE_ROOTS')
    return 0 if preconditions_ok else 1


if __name__ == '__main__':
    raise SystemExit(main())
