#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import datetime as _dt
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Tuple

EXPECTED_DD065_STATUS = "DDICT_RUNTIME_SOURCE_FILES_INSTALLED_REGISTRATION_PENDING"

def utc_now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).isoformat(timespec='seconds')

def read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding='utf-8', errors='replace'))
    except Exception:
        return {}

def write_json(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + '\n', encoding='utf-8')

def write_csv(path: Path, rows: List[Dict[str, Any]], fields: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator='\n')
        w.writeheader()
        for row in rows:
            w.writerow({k: row.get(k, '') for k in fields})

def safe_rel(repo: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(repo.resolve()).as_posix()
    except Exception:
        return path.as_posix()

def read_text(path: Path) -> str:
    return path.read_text(encoding='utf-8', errors='replace')

def score_registration_line(path: Path, line: str) -> Tuple[int, str]:
    p = path.as_posix().lower()
    t = line.lower()
    score = 0
    reasons: List[str] = []
    if 'command_registry' in p:
        score += 120
        reasons.append('command_registry_path')
    if 'cmd_' in p:
        score += 35
        reasons.append('cmd_file_path')
    if 'register' in t or 'dispatch' in t:
        score += 45
        reasons.append('register_dispatch_text')
    if 'command' in t:
        score += 25
        reasons.append('command_text')
    if 'about' in t or 'catalogcanary' in t or 'calc' in t or 'area' in t:
        score += 30
        reasons.append('known_command_reference')
    if 'cmd_' in t:
        score += 30
        reasons.append('cmd_symbol_reference')
    if 'ddict' in t:
        score += 100
        reasons.append('ddict_already_present')
    if 'help' in t or 'usage' in t:
        score += 10
        reasons.append('help_usage_context')
    return score, ','.join(reasons)

def scan_registration_candidates(repo: Path, max_rows: int = 250) -> List[Dict[str, Any]]:
    roots = [repo / 'include', repo / 'src', repo / 'bindings']
    suffixes = {'.hpp', '.h', '.cpp', '.cc', '.cxx', '.c'}
    rows: List[Dict[str, Any]] = []
    for root in roots:
        if not root.exists():
            continue
        files = [p for p in root.rglob('*') if p.is_file() and p.suffix.lower() in suffixes]
        files.sort(key=lambda p: (0 if 'command_registry' in p.as_posix().lower() else 1, p.as_posix().lower()))
        for path in files:
            try:
                lines = read_text(path).splitlines()
            except Exception:
                continue
            for i, line in enumerate(lines, start=1):
                score, reasons = score_registration_line(path, line)
                if score <= 0:
                    continue
                rows.append({
                    'path': safe_rel(repo, path),
                    'line': i,
                    'score': score,
                    'reasons': reasons,
                    'text': line.strip()[:600],
                })
    rows.sort(key=lambda r: (-int(r['score']), r['path'], int(r['line'])))
    return rows[:max_rows]

def score_build_line(path: Path, line: str) -> Tuple[int, str]:
    p = path.as_posix().lower()
    t = line.lower()
    score = 0
    reasons: List[str] = []
    if path.name.lower() in {'cmakelists.txt', 'makefile'} or path.suffix.lower() in {'.vcxproj', '.filters', '.props', '.targets', '.ninja', '.mk'}:
        score += 60
        reasons.append('build_file')
    if 'cmd_' in t and ('.cpp' in t or '.hpp' in t or '.h' in t):
        score += 70
        reasons.append('cmd_source_reference')
    if 'cmd_about' in t or 'cmd_catalogcanary' in t or 'cmd_calc' in t or 'cmd_area' in t:
        score += 50
        reasons.append('known_command_source_reference')
    if 'add_executable' in t or 'target_sources' in t or 'source_group' in t or 'clcompile' in t or 'sources' in t:
        score += 40
        reasons.append('build_rule_context')
    if 'ddict' in t:
        score += 100
        reasons.append('ddict_already_present')
    return score, ','.join(reasons)

def scan_build_candidates(repo: Path, max_rows: int = 250) -> List[Dict[str, Any]]:
    names = {'cmakelists.txt', 'makefile'}
    suffixes = {'.vcxproj', '.filters', '.props', '.targets', '.cmake', '.mk'}
    rows: List[Dict[str, Any]] = []
    files = []
    for path in repo.rglob('*'):
        if not path.is_file():
            continue
        rel = path.as_posix().lower()
        if '.git/' in rel or 'build/' in rel or 'out/' in rel:
            continue
        if path.name.lower() in names or path.suffix.lower() in suffixes:
            files.append(path)
    files.sort(key=lambda p: (0 if p.name.lower() == 'cmakelists.txt' else 1, p.as_posix().lower()))
    for path in files:
        try:
            lines = read_text(path).splitlines()
        except Exception:
            continue
        for i, line in enumerate(lines, start=1):
            score, reasons = score_build_line(path, line)
            if score <= 0:
                continue
            rows.append({
                'path': safe_rel(repo, path),
                'line': i,
                'score': score,
                'reasons': reasons,
                'text': line.strip()[:600],
            })
    rows.sort(key=lambda r: (-int(r['score']), r['path'], int(r['line'])))
    return rows[:max_rows]

def summarize_files(rows: List[Dict[str, Any]], kind: str, limit: int = 30) -> List[Dict[str, Any]]:
    by_file: Dict[str, Dict[str, Any]] = {}
    for row in rows:
        path = row['path']
        ent = by_file.setdefault(path, {'path': path, 'kind': kind, 'hit_rows': 0, 'score_total': 0, 'max_score': 0, 'reasons': set()})
        ent['hit_rows'] += 1
        ent['score_total'] += int(row['score'])
        ent['max_score'] = max(ent['max_score'], int(row['score']))
        for reason in str(row.get('reasons', '')).split(','):
            if reason:
                ent['reasons'].add(reason)
    out = []
    for ent in by_file.values():
        out.append({
            'path': ent['path'],
            'kind': kind,
            'hit_rows': ent['hit_rows'],
            'score_total': ent['score_total'],
            'max_score': ent['max_score'],
            'reasons': ','.join(sorted(ent['reasons'])),
            'recommended_use': classify_summary(ent['path'], kind, ent['reasons']),
        })
    out.sort(key=lambda r: (-int(r['score_total']), -int(r['max_score']), r['path']))
    return out[:limit]

def classify_summary(path: str, kind: str, reasons: set) -> str:
    p = path.lower()
    if kind == 'registration':
        if 'command_registry' in p:
            return 'PRIMARY_REGISTRATION_REVIEW'
        if 'cmd_catalogcanary' in p:
            return 'METADATA_COMMAND_PRECEDENT'
        if 'cmd_about' in p or 'cmd_calc' in p:
            return 'SIMPLE_COMMAND_PRECEDENT'
        if 'cmd_area' in p or 'cmd_browser' in p:
            return 'ACTIVE_AREA_READ_PRECEDENT'
        return 'REGISTRATION_CONTEXT_REVIEW'
    if kind == 'build':
        if p.endswith('cmakelists.txt'):
            return 'PRIMARY_CMAKE_REVIEW'
        if p.endswith('.vcxproj') or p.endswith('.filters'):
            return 'VISUAL_STUDIO_PROJECT_REVIEW'
        if p.endswith('.cmake'):
            return 'CMAKE_INCLUDE_REVIEW'
        return 'BUILD_CONTEXT_REVIEW'
    return 'CONTEXT_REVIEW'

def patch_plan(reg_summary: List[Dict[str, Any]], build_summary: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    primary_reg = next((r for r in reg_summary if r['recommended_use'] == 'PRIMARY_REGISTRATION_REVIEW'), reg_summary[0] if reg_summary else None)
    primary_build = next((r for r in build_summary if r['recommended_use'] in {'PRIMARY_CMAKE_REVIEW', 'VISUAL_STUDIO_PROJECT_REVIEW'}), build_summary[0] if build_summary else None)
    rows = []
    rows.append({
        'patch_id': 'P1_INCLUDE_HEADER',
        'target': primary_reg['path'] if primary_reg else 'UNKNOWN',
        'proposed_change': 'Include cli/cmd_ddict.hpp or equivalent declaration at the exact registry/dispatcher site',
        'allowed_in_dd066': 0,
        'future_package': 'DD-067',
        'risk': 'MEDIUM',
    })
    rows.append({
        'patch_id': 'P2_REGISTER_DDICT_COMMAND',
        'target': primary_reg['path'] if primary_reg else 'UNKNOWN',
        'proposed_change': 'Register DDICT command dispatch to xbase::cmd_DDICT with raw argument tail',
        'allowed_in_dd066': 0,
        'future_package': 'DD-067',
        'risk': 'MEDIUM_HIGH',
    })
    rows.append({
        'patch_id': 'P3_BUILD_INCLUDE_SOURCE',
        'target': primary_build['path'] if primary_build else 'UNKNOWN',
        'proposed_change': 'Add src/cli/cmd_ddict.cpp to the active build source list only after local build file is verified',
        'allowed_in_dd066': 0,
        'future_package': 'DD-067',
        'risk': 'MEDIUM',
    })
    rows.append({
        'patch_id': 'P4_RUNTIME_SMOKE_AFTER_BUILD',
        'target': 'dottalkpp/data/tests/dd065_ddict_usage_smoke.dts',
        'proposed_change': 'Run DDICT HELP/status smoke only after build and registration succeed',
        'allowed_in_dd066': 0,
        'future_package': 'DD-067 or DD-068',
        'risk': 'LOW',
    })
    return rows

def main() -> int:
    ap = argparse.ArgumentParser(description='DD-066 DDICT registration and build integration discovery')
    ap.add_argument('--repo-root', required=True)
    ap.add_argument('--out-dir', required=True)
    ap.add_argument('--run-id', default='DD066-ddict-registration-build-discovery-v0')
    ap.add_argument('--dd065-dir', default='docs/datadict/reports/DD065-guarded-ddict-runtime-source-install-v0')
    ap.add_argument('--header-path', default='include/cli/cmd_ddict.hpp')
    ap.add_argument('--source-path', default='src/cli/cmd_ddict.cpp')
    ap.add_argument('--smoke-path', default='dottalkpp/data/tests/dd065_ddict_usage_smoke.dts')
    ap.add_argument('--profile', action='append', default=[])
    ap.add_argument('--fail-on-review', action='store_true')
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    out = Path(args.out_dir).resolve()
    dd065_dir = (repo / args.dd065_dir).resolve()
    header_path = (repo / args.header_path).resolve()
    source_path = (repo / args.source_path).resolve()
    smoke_path = (repo / args.smoke_path).resolve()
    out.mkdir(parents=True, exist_ok=True)

    dd065_manifest = read_json(dd065_dir / 'dd065_guarded_ddict_runtime_source_package_manifest.json')
    dd065_ready = dd065_manifest.get('status') == EXPECTED_DD065_STATUS
    header_exists = header_path.exists()
    source_exists = source_path.exists()
    smoke_exists = smoke_path.exists()

    reg_rows = scan_registration_candidates(repo)
    build_rows = scan_build_candidates(repo)
    reg_summary = summarize_files(reg_rows, 'registration')
    build_summary = summarize_files(build_rows, 'build')
    patch_rows = patch_plan(reg_summary, build_summary)

    has_primary_reg = any(r['recommended_use'] == 'PRIMARY_REGISTRATION_REVIEW' for r in reg_summary)
    has_primary_build = any(r['recommended_use'] in {'PRIMARY_CMAKE_REVIEW', 'VISUAL_STUDIO_PROJECT_REVIEW', 'CMAKE_INCLUDE_REVIEW'} for r in build_summary)

    gate_rows = [
        {'gate': 'dd065_source_installed_registration_pending', 'expected': EXPECTED_DD065_STATUS, 'observed': dd065_manifest.get('status', ''), 'pass': int(dd065_ready)},
        {'gate': 'cmd_ddict_header_exists', 'expected': 1, 'observed': int(header_exists), 'pass': int(header_exists)},
        {'gate': 'cmd_ddict_source_exists', 'expected': 1, 'observed': int(source_exists), 'pass': int(source_exists)},
        {'gate': 'ddict_smoke_exists', 'expected': 1, 'observed': int(smoke_exists), 'pass': int(smoke_exists)},
        {'gate': 'registration_candidates_found', 'expected': '>=1', 'observed': len(reg_rows), 'pass': int(len(reg_rows) >= 1)},
        {'gate': 'build_candidates_found', 'expected': '>=1', 'observed': len(build_rows), 'pass': int(len(build_rows) >= 1)},
        {'gate': 'primary_registration_candidate_found', 'expected': 1, 'observed': int(has_primary_reg), 'pass': int(has_primary_reg)},
        {'gate': 'primary_build_candidate_found', 'expected': 1, 'observed': int(has_primary_build), 'pass': int(has_primary_build)},
        {'gate': 'patch_plan_report_only', 'expected': 1, 'observed': 1, 'pass': 1},
    ]
    failures = sum(1 for r in gate_rows if int(r['pass']) != 1)
    status = 'DDICT_REGISTRATION_BUILD_DISCOVERY_READY' if failures == 0 else 'DDICT_REGISTRATION_BUILD_DISCOVERY_REVIEW'

    boundary_rows = [
        {'boundary': 'registration_build_discovery_only', 'observed': 1, 'required': 1, 'pass': 1},
        {'boundary': 'cxx_source_edits', 'observed': 0, 'required': 0, 'pass': 1},
        {'boundary': 'build_file_edits', 'observed': 0, 'required': 0, 'pass': 1},
        {'boundary': 'runtime_command_registration', 'observed': 0, 'required': 0, 'pass': 1},
        {'boundary': 'active_catalog_mutation', 'observed': 0, 'required': 0, 'pass': 1},
        {'boundary': 'dbf_append_replace_delete_pack_zap', 'observed': 0, 'required': 0, 'pass': 1},
        {'boundary': 'cdx_lmdb_create_rebuild', 'observed': 0, 'required': 0, 'pass': 1},
        {'boundary': 'help_meta_cmdhelpchk_mutation', 'observed': 0, 'required': 0, 'pass': 1},
        {'boundary': 'catalog_regeneration', 'observed': 0, 'required': 0, 'pass': 1},
        {'boundary': 'manual_row_repair', 'observed': 0, 'required': 0, 'pass': 1},
    ]

    write_csv(out / 'dd066_registration_candidates.csv', reg_rows, ['path', 'line', 'score', 'reasons', 'text'])
    write_csv(out / 'dd066_registration_file_summary.csv', reg_summary, ['path', 'kind', 'hit_rows', 'score_total', 'max_score', 'reasons', 'recommended_use'])
    write_csv(out / 'dd066_build_candidates.csv', build_rows, ['path', 'line', 'score', 'reasons', 'text'])
    write_csv(out / 'dd066_build_file_summary.csv', build_summary, ['path', 'kind', 'hit_rows', 'score_total', 'max_score', 'reasons', 'recommended_use'])
    write_csv(out / 'dd066_patch_plan_report_only.csv', patch_rows, ['patch_id', 'target', 'proposed_change', 'allowed_in_dd066', 'future_package', 'risk'])
    write_csv(out / 'dd066_gate_ledger.csv', gate_rows, ['gate', 'expected', 'observed', 'pass'])
    write_csv(out / 'dd066_no_mutation_boundary_ledger.csv', boundary_rows, ['boundary', 'observed', 'required', 'pass'])

    report_lines = [
        '# DD-066 DDICT Registration and Build Integration Discovery',
        '',
        f'Run id: `{args.run_id}`',
        f'Status: **{status}**',
        f'Created UTC: `{utc_now()}`',
        '',
        '## Purpose',
        '',
        'DD-066 discovers the exact local registration and build integration candidates for DDICT.',
        '',
        '## Inputs',
        '',
        f'- DD-065 status: `{dd065_manifest.get("status", "")}`',
        f'- Header exists: **{int(header_exists)}**',
        f'- Source exists: **{int(source_exists)}**',
        f'- Smoke exists: **{int(smoke_exists)}**',
        '',
        '## Discovery counts',
        '',
        f'- Registration candidate rows: **{len(reg_rows)}**',
        f'- Registration summary files: **{len(reg_summary)}**',
        f'- Build candidate rows: **{len(build_rows)}**',
        f'- Build summary files: **{len(build_summary)}**',
        f'- Patch plan rows: **{len(patch_rows)}**',
        '',
        '## Boundary',
        '',
        'DD-066 is report-only. It does not edit C++ files, edit build files, register runtime commands, mutate the active catalog, mutate DBF/CDX/LMDB artifacts, or mutate HELP/META/CMDHELPCHK.',
        '',
        '## Next',
        '',
        'DD-067 may apply the guarded registration/build patch only after explicit authorization.',
        '',
    ]
    (out / 'DD066_DDICT_REGISTRATION_BUILD_DISCOVERY_REPORT.md').write_text('\n'.join(report_lines), encoding='utf-8')

    manifest = {
        'contract': 'dd066_ddict_registration_build_discovery_v0',
        'run_id': args.run_id,
        'created_utc': utc_now(),
        'status': status,
        'repo_root': str(repo),
        'profiles': args.profile,
        'dd065_status': dd065_manifest.get('status', ''),
        'header_exists': int(header_exists),
        'source_exists': int(source_exists),
        'smoke_exists': int(smoke_exists),
        'registration_candidate_rows': len(reg_rows),
        'registration_summary_files': len(reg_summary),
        'build_candidate_rows': len(build_rows),
        'build_summary_files': len(build_summary),
        'primary_registration_candidate_found': int(has_primary_reg),
        'primary_build_candidate_found': int(has_primary_build),
        'patch_plan_rows': len(patch_rows),
        'failures': failures,
        'cxx_source_edits': 0,
        'build_file_edits': 0,
        'runtime_command_registration': 0,
        'active_catalog_mutation': 0,
        'next_recommended_action': 'DD-067 guarded registration/build patch only after explicit authorization',
    }
    write_json(out / 'dd066_ddict_registration_build_discovery_manifest.json', manifest)

    print(f"DD-066 DDICT registration/build discovery manifest: {out / 'dd066_ddict_registration_build_discovery_manifest.json'}")
    print(f"status: {status}; reg_rows: {len(reg_rows)}; build_rows: {len(build_rows)}; failures: {failures}")
    return 2 if (args.fail_on_review and failures) else 0

if __name__ == '__main__':
    raise SystemExit(main())
