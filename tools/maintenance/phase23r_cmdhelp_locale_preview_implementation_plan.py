#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path

PHASE23R_NAME = "PHASE23R-CMDHELP-LOCALE-PREVIEW-IMPLEMENTATION-PLAN"
PHASE23Q_NAME = "PHASE23Q-CMDHELP-LOCALE-INTEGRATION-PLAN"
PHASE23O_NAME = "PHASE23O-ACTIVE-HELP-LOCALE-READBACK-PROOF"

TABLES = [
    "HELP_TOPIC_LOCALE",
    "HELP_SECTION_LOCALE",
    "HELP_LINE_LOCALE",
    "HELP_ARTIFACT_LOCALE",
]

SOURCE_KEYWORDS = [
    "CMDHELP",
    "HELP_TOPIC",
    "HELP_LINE",
    "SET LANGUAGE",
    "SET LOCALE",
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


def read_optional(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding='utf-8', errors='replace')


def count_files(paths: list[Path]) -> int:
    return sum(1 for p in paths if p.exists() and p.is_file())


def count_dirs(paths: list[Path]) -> int:
    return sum(1 for p in paths if p.exists() and p.is_dir())


def probe_phase23q_green(repo: Path) -> tuple[int, dict[str, object]]:
    manifest = repo / 'docs' / 'locale' / 'candidates' / PHASE23Q_NAME / 'manifests' / 'phase23q_cmdhelp_locale_integration_plan_manifest.json'
    report = repo / 'docs' / 'locale' / 'candidates' / PHASE23Q_NAME / 'reports' / 'PHASE23Q_CMDHELP_LOCALE_INTEGRATION_PLAN.md'
    text = read_optional(report)
    status_ok = 1 if 'PHASE23Q_CMDHELP_LOCALE_INTEGRATION_PLAN_GREEN_REPORT_ONLY' in text else 0
    manifest_ok = 0
    next_gate_ok = 0
    if manifest.exists():
        try:
            data = json.loads(read_optional(manifest))
            manifest_ok = 1 if data.get('status') == 'PHASE23Q_CMDHELP_LOCALE_INTEGRATION_PLAN_GREEN_REPORT_ONLY' else 0
            next_gate_ok = 1 if data.get('next_gate') == 'HOLD_OR_AUTHORIZE_PHASE23R_CMDHELP_LOCALE_PREVIEW_IMPLEMENTATION_PLAN' else 0
        except Exception:
            manifest_ok = 0
    green = 1 if manifest.exists() and report.exists() and (manifest_ok or status_ok) else 0
    return green, {
        'manifest': rel(repo, manifest),
        'manifest_exists': 1 if manifest.exists() else 0,
        'report': rel(repo, report),
        'report_exists': 1 if report.exists() else 0,
        'manifest_status_ok': manifest_ok,
        'report_status_ok': status_ok,
        'next_gate_ok': next_gate_ok,
    }


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
    ]
    marker_ok = 1 if all(m in text for m in markers) else 0
    green = 1 if transcript.exists() and marker_ok else 0
    return green, {
        'transcript': rel(repo, transcript),
        'transcript_exists': 1 if transcript.exists() else 0,
        'marker_ok': marker_ok,
    }


def discover_source_candidates(repo: Path) -> list[dict[str, object]]:
    roots = [repo / 'src', repo / 'dottalkpp', repo / 'include']
    exts = {'.cpp', '.hpp', '.h', '.cxx', '.cc', '.c', '.md', '.txt'}
    rows: list[dict[str, object]] = []
    seen: set[Path] = set()
    for root in roots:
        if not root.exists():
            continue
        for path in root.rglob('*'):
            if not path.is_file() or path.suffix.lower() not in exts:
                continue
            try:
                text = path.read_text(encoding='utf-8', errors='replace')
            except Exception:
                continue
            hits = [k for k in SOURCE_KEYWORDS if k.lower() in text.lower() or k.lower().replace(' ', '_') in path.name.lower()]
            if not hits:
                continue
            if path in seen:
                continue
            seen.add(path)
            role = 'unknown'
            low_name = path.name.lower()
            low_rel = rel(repo, path).lower()
            if 'cmdhelp' in low_name or 'cmdhelp' in low_rel:
                role = 'primary_cmdhelp_candidate'
            elif 'help' in low_name:
                role = 'help_support_candidate'
            elif 'language' in low_name or 'locale' in low_name:
                role = 'locale_language_support_candidate'
            rows.append({
                'path': rel(repo, path),
                'role': role,
                'hits': ';'.join(hits[:8]),
                'candidate_action': 'inspect before PHASE23S source patch; do not modify in PHASE23R',
            })
    rows.sort(key=lambda r: (0 if r['role'] == 'primary_cmdhelp_candidate' else 1, str(r['path'])))
    return rows[:80]


def main() -> int:
    parser = argparse.ArgumentParser(description='Stage PHASE23R CMDHELP locale preview implementation plan, report-only.')
    parser.add_argument('--repo-root', default='.')
    args = parser.parse_args()

    repo = Path(args.repo_root).resolve()
    cand_dir = repo / 'docs' / 'locale' / 'candidates' / PHASE23R_NAME
    reports_dir = cand_dir / 'reports'
    manifests_dir = cand_dir / 'manifests'
    runtime_dir = cand_dir / 'runtime'
    for d in (reports_dir, manifests_dir, runtime_dir):
        d.mkdir(parents=True, exist_ok=True)

    active_dbf_root = repo / 'dottalkpp' / 'data' / 'HELP'
    active_cdx_root = repo / 'dottalkpp' / 'data' / 'INDEXES' / 'HELP'
    active_lmdb_root = repo / 'dottalkpp' / 'data' / 'LMDB' / 'HELP'
    active_dbf_count = count_files([active_dbf_root / f'{t}.dbf' for t in TABLES])
    active_cdx_count = count_files([active_cdx_root / f'{t}.cdx' for t in TABLES])
    active_lmdb_count = count_dirs([active_lmdb_root / f'{t}.cdx.d' for t in TABLES])

    phase23q_green, phase23q_probe = probe_phase23q_green(repo)
    phase23o_green, phase23o_probe = probe_phase23o_green(repo)
    source_candidates = discover_source_candidates(repo)

    command_contract_rows = [
        {
            'surface': 'CMDHELP <topic>',
            'phase23r_disposition': 'unchanged default behavior',
            'locale_source': 'none unless later SET LANGUAGE integration is explicitly authorized',
            'draft_rows_visible': 0,
            'notes': 'Existing command must stay stable during preview implementation.',
        },
        {
            'surface': 'CMDHELP <topic> PREVIEW LOCALE <locale>',
            'phase23r_disposition': 'preferred preview-only command shape',
            'locale_source': 'explicit argument',
            'draft_rows_visible': 1,
            'notes': 'Safe because output is clearly marked preview and can show DRAFT_PLACEHOLDER / NEEDS_REVIEW rows.',
        },
        {
            'surface': 'CMDHELP <topic> LOCALE <locale>',
            'phase23r_disposition': 'optional alias; keep behind same preview safety gate',
            'locale_source': 'explicit argument',
            'draft_rows_visible': 1,
            'notes': 'May be convenient but less explicit than PREVIEW LOCALE.',
        },
        {
            'surface': 'CMDHELP PREVIEW LOCALE <locale> <topic>',
            'phase23r_disposition': 'parser may accept only if simple; otherwise defer',
            'locale_source': 'explicit argument',
            'draft_rows_visible': 1,
            'notes': 'Avoid parser ambiguity if current CMDHELP parser is position-sensitive.',
        },
        {
            'surface': 'SET LANGUAGE <locale> then CMDHELP <topic>',
            'phase23r_disposition': 'not implemented in PHASE23R/PHASE23S; plan only',
            'locale_source': 'global language state',
            'draft_rows_visible': 0,
            'notes': 'Default behavior change must wait until approved translations exist.',
        },
    ]
    write_csv(reports_dir / 'phase23r_preview_command_contract.csv', command_contract_rows,
              ['surface', 'phase23r_disposition', 'locale_source', 'draft_rows_visible', 'notes'])

    parser_rows = [
        {'step': 1, 'parser_task': 'Recognize optional PREVIEW token after CMDHELP topic or before LOCALE block', 'guard': 'do not disturb existing CMDHELP topic parsing'},
        {'step': 2, 'parser_task': 'Recognize LOCALE <locale_id> explicit argument', 'guard': 'validate against active/shared locale list or starter set'},
        {'step': 3, 'parser_task': 'Require PREVIEW mode before draft rows can be displayed', 'guard': 'draft rows never affect default CMDHELP output'},
        {'step': 4, 'parser_task': 'Normalize topic to TOPICKEY using existing CMDHELP topic resolution', 'guard': 'fallback to existing behavior if locale preview parse fails'},
        {'step': 5, 'parser_task': 'Emit parse diagnostics in preview only', 'guard': 'no new diagnostics for ordinary CMDHELP'},
    ]
    write_csv(reports_dir / 'phase23r_parser_contract.csv', parser_rows,
              ['step', 'parser_task', 'guard'])

    lookup_algorithm_rows = [
        {'step': 1, 'operation': 'Resolve topic via existing CMDHELP path', 'input': 'user topic token', 'output': 'TOPICKEY', 'fallback': 'existing CMDHELP behavior'},
        {'step': 2, 'operation': 'Open/read active HELP_TOPIC_LOCALE by TOPICKEY', 'input': 'TOPICKEY + LOCALE_ID', 'output': 'localized title row', 'fallback': 'source title'},
        {'step': 3, 'operation': 'Open/read active HELP_SECTION_LOCALE by TOPICKEY/SECTION_KEY', 'input': 'TOPICKEY + LOCALE_ID', 'output': 'localized section labels', 'fallback': 'source section labels'},
        {'step': 4, 'operation': 'Open/read active HELP_LINE_LOCALE by TOPICKEY/SECTION_KEY/LINE_ORDER', 'input': 'TOPICKEY + LOCALE_ID', 'output': 'localized line labels/text where valid', 'fallback': 'source line text'},
        {'step': 5, 'operation': 'Open/read active HELP_ARTIFACT_LOCALE for preview metadata', 'input': 'TOPICKEY + LOCALE_ID', 'output': 'localized artifact hash/status', 'fallback': 'source artifact metadata'},
        {'step': 6, 'operation': 'Apply status gate', 'input': 'TRANSL_STATUS + REVIEW_STATUS', 'output': 'preview/fallback decision', 'fallback': 'source/en-US'},
        {'step': 7, 'operation': 'Render preview banner', 'input': 'locale/status/fallback decision', 'output': 'explicit PREVIEW output', 'fallback': 'existing CMDHELP render'},
    ]
    write_csv(reports_dir / 'phase23r_runtime_lookup_algorithm.csv', lookup_algorithm_rows,
              ['step', 'operation', 'input', 'output', 'fallback'])

    status_gate_rows = [
        {'transl_status': 'SOURCE_CANONICAL', 'review_status': 'SOURCE', 'default_display': 'source/en-US', 'preview_display': 'source/en-US', 'fallback_required': 0},
        {'transl_status': 'DRAFT_PLACEHOLDER', 'review_status': 'NEEDS_REVIEW', 'default_display': 'source/en-US', 'preview_display': 'draft row with warning', 'fallback_required': 1},
        {'transl_status': 'DRAFT', 'review_status': 'NEEDS_REVIEW', 'default_display': 'source/en-US', 'preview_display': 'draft row with warning', 'fallback_required': 1},
        {'transl_status': 'TRANSLATED', 'review_status': 'NEEDS_REVIEW', 'default_display': 'source/en-US', 'preview_display': 'localized row with warning', 'fallback_required': 1},
        {'transl_status': 'TRANSLATED', 'review_status': 'APPROVED', 'default_display': 'held until future default-localized authorization', 'preview_display': 'localized row', 'fallback_required': 0},
        {'transl_status': 'STALE_SOURCE_HASH', 'review_status': 'ANY', 'default_display': 'source/en-US', 'preview_display': 'stale warning plus source fallback', 'fallback_required': 1},
    ]
    write_csv(reports_dir / 'phase23r_status_gate_matrix.csv', status_gate_rows,
              ['transl_status', 'review_status', 'default_display', 'preview_display', 'fallback_required'])

    output_contract_rows = [
        {'section': 'preview_banner', 'required': 1, 'content': 'CMDHELP LOCALE PREVIEW - not default command behavior'},
        {'section': 'topic_identity', 'required': 1, 'content': 'TOPICKEY, command/topic name, requested LOCALE_ID'},
        {'section': 'status_summary', 'required': 1, 'content': 'TRANSL_STATUS, REVIEW_STATUS, fallback decision'},
        {'section': 'localized_content', 'required': 1, 'content': 'localized title/section/line rows if available'},
        {'section': 'fallback_content', 'required': 1, 'content': 'source/en-US content shown when row is draft/missing/stale'},
        {'section': 'artifact_status', 'required': 0, 'content': 'HELP_ARTIFACT_LOCALE hash/status evidence'},
        {'section': 'footer', 'required': 1, 'content': 'normal CMDHELP output unchanged'},
    ]
    write_csv(reports_dir / 'phase23r_preview_output_contract.csv', output_contract_rows,
              ['section', 'required', 'content'])

    usage_contract_rows = [
        {'file_or_surface': 'primary CMDHELP source file', 'required_update': '@dottalk.usage v1 comment documents PREVIEW LOCALE syntax', 'phase': 'PHASE23S source patch candidate'},
        {'file_or_surface': 'CMDHELP help topic', 'required_update': 'candidate HELP text only; not active HELP mutation in PHASE23R', 'phase': 'later HELP lane'},
        {'file_or_surface': 'CMDHELPCHK', 'required_update': 'locale preview checks report-first', 'phase': 'PHASE23U'},
        {'file_or_surface': 'MAINT/BBOX', 'required_update': 'locale sidecar health visibility report-first', 'phase': 'PHASE23V'},
        {'file_or_surface': 'release notes / savepoint', 'required_update': 'record preview-only status and no default behavior change', 'phase': 'after build smoke'},
    ]
    write_csv(reports_dir / 'phase23r_usage_contract_update_plan.csv', usage_contract_rows,
              ['file_or_surface', 'required_update', 'phase'])

    source_boundary_rows = [
        {'boundary': 'no source files are changed by PHASE23R', 'value': 1},
        {'boundary': 'PHASE23S may stage source patch only after explicit authorization', 'value': 1},
        {'boundary': 'source patch must preserve existing CMDHELP behavior', 'value': 1},
        {'boundary': 'source patch must update @dottalk.usage v1 / usage comments if command syntax changes', 'value': 1},
        {'boundary': 'source patch must not alter active HELP DBF/CDX/LMDB artifacts', 'value': 1},
        {'boundary': 'source patch must include build and smoke test instructions', 'value': 1},
    ]
    write_csv(reports_dir / 'phase23r_source_patch_boundaries.csv', source_boundary_rows,
              ['boundary', 'value'])

    test_plan_rows = [
        {'test_id': 'R_SMOKE_DEFAULT_CMDHELP_AREA', 'command': 'CMDHELP AREA', 'expected': 'unchanged existing output'},
        {'test_id': 'R_SMOKE_PREVIEW_ES_AREA', 'command': 'CMDHELP AREA PREVIEW LOCALE es', 'expected': 'preview banner plus es draft/fallback status'},
        {'test_id': 'R_SMOKE_PREVIEW_ES_ABOUT', 'command': 'CMDHELP ABOUT PREVIEW LOCALE es', 'expected': 'preview banner plus es draft/fallback status'},
        {'test_id': 'R_SMOKE_PREVIEW_BAD_LOCALE', 'command': 'CMDHELP AREA PREVIEW LOCALE zz-ZZ', 'expected': 'clear invalid locale diagnostic and existing CMDHELP not harmed'},
        {'test_id': 'R_SMOKE_SET_LANGUAGE_UNCHANGED', 'command': 'SET LANGUAGE es then CMDHELP AREA', 'expected': 'default CMDHELP still unchanged until later authorization'},
        {'test_id': 'R_SMOKE_PATHS_UNCHANGED', 'command': 'AREA / path checks after smoke', 'expected': 'no path leakage from HELP locale active roots'},
    ]
    write_csv(reports_dir / 'phase23r_test_plan.csv', test_plan_rows,
              ['test_id', 'command', 'expected'])

    sequence_rows = [
        {'step': 1, 'phase': 'PHASE23R', 'action': 'accept implementation plan, report-only', 'mutation': 0},
        {'step': 2, 'phase': 'PHASE23S', 'action': 'stage candidate source patch for preview-only CMDHELP branch', 'mutation': 'candidate source files only after authorization'},
        {'step': 3, 'phase': 'PHASE23T', 'action': 'build dottalkpp and run smoke/default regression', 'mutation': 'build artifacts only'},
        {'step': 4, 'phase': 'PHASE23U', 'action': 'CMDHELPCHK locale checks report-first', 'mutation': 0},
        {'step': 5, 'phase': 'PHASE23V', 'action': 'MAINT/BBOX visibility report-first', 'mutation': 0},
        {'step': 6, 'phase': 'future', 'action': 'default localized HELP via SET LANGUAGE only after approved translations exist', 'mutation': 'explicit authorization required'},
    ]
    write_csv(reports_dir / 'phase23r_implementation_sequence.csv', sequence_rows,
              ['step', 'phase', 'action', 'mutation'])

    source_fields = ['path', 'role', 'hits', 'candidate_action']
    write_csv(reports_dir / 'phase23r_source_candidate_inventory.csv', source_candidates, source_fields)

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
    write_csv(reports_dir / 'phase23r_boundary_report.csv', boundary_rows,
              ['boundary', 'value'])

    source_inv_summary = 'No source candidates discovered by keyword scan; PHASE23S must inspect repo manually before source patch.'
    if source_candidates:
        source_inv_summary = f'{len(source_candidates)} source candidate file(s) inventoried for PHASE23S inspection.'

    report = f"""# PHASE23R CMDHELP Locale Preview Implementation Plan

Status: `PHASE23R_CMDHELP_LOCALE_PREVIEW_IMPLEMENTATION_PLAN_GREEN_REPORT_ONLY`

## Purpose

PHASE23Q accepted the integration contract. PHASE23R turns that contract into a concrete implementation plan for a future preview-only CMDHELP locale branch. This phase is report-only and does not patch source.

## Current foundation

- PHASE23Q green: `{phase23q_green}`
- PHASE23O readback proof present: `{phase23o_green}`
- Active HELP locale DBF artifacts: `{active_dbf_count}/4`
- Active HELP locale CDX artifacts: `{active_cdx_count}/4`
- Active HELP locale LMDB artifacts: `{active_lmdb_count}/4`
- Source inventory: {source_inv_summary}

## Preview command target

Preferred shape:

```text
CMDHELP <topic> PREVIEW LOCALE <locale>
```

Default shape remains unchanged:

```text
CMDHELP <topic>
```

## Implementation principle

The first runtime source patch should add only an explicit preview branch. It must not make `SET LANGUAGE` alter default CMDHELP output yet, because current non-English rows are draft/needs-review seed rows.

## Fallback principle

Default CMDHELP displays source/en-US. Preview may show draft rows with warnings, but must also state when fallback would be used.

## Usage contract requirement

Any PHASE23S source patch that changes command syntax must update `@dottalk.usage v1` or equivalent source-comment command usage contracts in the same guarded package.

## Next gate

`HOLD_OR_AUTHORIZE_PHASE23S_CMDHELP_LOCALE_PREVIEW_SOURCE_PATCH_STAGING`
"""
    write_text(reports_dir / 'PHASE23R_CMDHELP_LOCALE_PREVIEW_IMPLEMENTATION_PLAN.md', report)

    manifest = {
        'phase': 'PHASE23R',
        'status': 'PHASE23R_CMDHELP_LOCALE_PREVIEW_IMPLEMENTATION_PLAN_GREEN_REPORT_ONLY',
        'created_at': datetime.now(timezone.utc).isoformat(),
        'candidate_dir': rel(repo, cand_dir),
        'phase23q_green': phase23q_green,
        'phase23q_probe': phase23q_probe,
        'phase23o_green': phase23o_green,
        'phase23o_probe': phase23o_probe,
        'active_roots': [
            rel(repo, active_dbf_root),
            rel(repo, active_cdx_root),
            rel(repo, active_lmdb_root),
        ],
        'active_dbf_exists': f'{active_dbf_count}/4',
        'active_cdx_exists': f'{active_cdx_count}/4',
        'active_lmdb_exists': f'{active_lmdb_count}/4',
        'preview_command_contract_rows': len(command_contract_rows),
        'parser_contract_rows': len(parser_rows),
        'lookup_algorithm_rows': len(lookup_algorithm_rows),
        'status_gate_rows': len(status_gate_rows),
        'output_contract_rows': len(output_contract_rows),
        'usage_contract_rows': len(usage_contract_rows),
        'test_plan_rows': len(test_plan_rows),
        'source_candidate_rows': len(source_candidates),
        'boundaries': {row['boundary']: row['value'] for row in boundary_rows},
        'next_gate': 'HOLD_OR_AUTHORIZE_PHASE23S_CMDHELP_LOCALE_PREVIEW_SOURCE_PATCH_STAGING',
    }
    write_text(manifests_dir / 'phase23r_cmdhelp_locale_preview_implementation_plan_manifest.json', json.dumps(manifest, indent=2) + '\n')

    preconditions_ok = 1 if phase23q_green and active_dbf_count == 4 and active_cdx_count == 4 and active_lmdb_count == 4 else 0
    status = 'PHASE23R_CMDHELP_LOCALE_PREVIEW_IMPLEMENTATION_PLAN_GREEN_REPORT_ONLY' if preconditions_ok else 'PHASE23R_CMDHELP_LOCALE_PREVIEW_IMPLEMENTATION_PLAN_REVIEW_REQUIRED'

    print(status)
    print(f'candidate_dir: {rel(repo, cand_dir)}')
    print(f'phase23q_green: {phase23q_green}')
    print(f'phase23o_green: {phase23o_green}')
    print('read_scope: ACTIVE_HELP_LOCALE_ROOTS')
    print('active_roots: dottalkpp\\data\\HELP,dottalkpp\\data\\INDEXES\\HELP,dottalkpp\\data\\LMDB\\HELP')
    print(f'active_dbf_exists: {active_dbf_count}/4')
    print(f'active_cdx_exists: {active_cdx_count}/4')
    print(f'active_lmdb_exists: {active_lmdb_count}/4')
    print('implementation_model: CMDHELP_PREVIEW_LOCALE_EXPLICIT_ONLY_DEFAULT_UNCHANGED')
    print(f'preview_command_contract_rows: {len(command_contract_rows)}')
    print(f'parser_contract_rows: {len(parser_rows)}')
    print(f'lookup_algorithm_rows: {len(lookup_algorithm_rows)}')
    print(f'status_gate_rows: {len(status_gate_rows)}')
    print(f'preview_output_contract_rows: {len(output_contract_rows)}')
    print(f'usage_contract_update_rows: {len(usage_contract_rows)}')
    print(f'test_plan_rows: {len(test_plan_rows)}')
    print(f'source_candidate_rows: {len(source_candidates)}')
    print(f'manifest: {rel(repo, manifests_dir / "phase23r_cmdhelp_locale_preview_implementation_plan_manifest.json")}')
    print(f'implementation_plan: {rel(repo, reports_dir / "PHASE23R_CMDHELP_LOCALE_PREVIEW_IMPLEMENTATION_PLAN.md")}')
    print('source_files_written: 0')
    print('active_help_dbf_written: 0')
    print('active_help_cdx_written: 0')
    print('active_help_lmdb_written: 0')
    print('cmdhelp_behavior_changed: 0')
    print('cmdhelpchk_behavior_changed: 0')
    print('maint_behavior_changed: 0')
    print('bbox_behavior_changed: 0')
    print('runtime_execution_by_python: 0')
    print('next_gate: HOLD_OR_AUTHORIZE_PHASE23S_CMDHELP_LOCALE_PREVIEW_SOURCE_PATCH_STAGING' if preconditions_ok else 'next_gate: FIX_PHASE23R_PRECONDITIONS_OR_REVIEW_PHASE23Q')
    return 0 if preconditions_ok else 1


if __name__ == '__main__':
    raise SystemExit(main())
