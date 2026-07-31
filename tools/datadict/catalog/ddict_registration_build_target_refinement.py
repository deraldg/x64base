#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import datetime as _dt
import json
from pathlib import Path
from typing import Any, Dict, List

EXPECTED_DD066_STATUS = "DDICT_REGISTRATION_BUILD_DISCOVERY_READY"

EXCLUDE_BUILD_PREFIXES = (
    'side projects/',
    'foxapp/',
    '_drops/',
    '.mdo_backups/',
)

EXCLUDE_BUILD_CONTAINS = (
    '/build-legacy/',
    '/build-pro-md/',
    '/build-tests/',
    '/build_rdi/',
)

def utc_now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).isoformat(timespec='seconds')

def read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding='utf-8', errors='replace'))
    except Exception:
        return {}

def read_csv_dict(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open('r', newline='', encoding='utf-8', errors='replace') as f:
        return list(csv.DictReader(f))

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

def normalize_path(path: str) -> str:
    return path.replace('\\', '/').lower().strip()

def is_active_build_candidate(path: str) -> bool:
    p = normalize_path(path)
    if any(p.startswith(prefix) for prefix in EXCLUDE_BUILD_PREFIXES):
        return False
    if any(token in p for token in EXCLUDE_BUILD_CONTAINS):
        return False
    return True

def classify_build_candidate(path: str) -> str:
    p = normalize_path(path)
    if p == 'src/cmakelists.txt':
        return 'PRIMARY_ACTIVE_CMAKE_TARGET'
    if p.endswith('/cmakelists.txt') and is_active_build_candidate(path):
        return 'ACTIVE_CMAKE_REVIEW'
    if p.endswith('.vcxproj') and is_active_build_candidate(path):
        return 'ACTIVE_VCXPROJ_REVIEW'
    if not is_active_build_candidate(path):
        return 'EXCLUDED_LEGACY_OR_GENERATED_BUILD_ARTIFACT'
    return 'ACTIVE_BUILD_CONTEXT_REVIEW'

def classify_registration_candidate(path: str) -> str:
    p = normalize_path(path)
    if p == 'src/cli/command_registry.cpp':
        return 'PRIMARY_ACTIVE_REGISTRATION_TARGET'
    if p == 'include/cli/command_registry.hpp':
        return 'PRIMARY_REGISTRY_HEADER_REFERENCE'
    if p == 'src/cli/cmd_ddict.cpp':
        return 'NEW_DDICT_SOURCE_ALREADY_INSTALLED'
    if p == 'include/cli/cmd_ddict.hpp':
        return 'NEW_DDICT_HEADER_ALREADY_INSTALLED'
    if 'command_registry' in p:
        return 'REGISTRATION_CONTEXT_REVIEW'
    return 'COMMAND_PRECEDENT_OR_CONTEXT'

def select_registration(reg_summary: List[Dict[str, str]]) -> Dict[str, Any]:
    for row in reg_summary:
        if normalize_path(row.get('path', '')) == 'src/cli/command_registry.cpp':
            out = dict(row)
            out['accepted_target'] = 1
            out['target_classification'] = classify_registration_candidate(row.get('path', ''))
            out['reason'] = 'active source command registry implementation file'
            return out
    for row in reg_summary:
        if 'command_registry' in normalize_path(row.get('path', '')):
            out = dict(row)
            out['accepted_target'] = 1
            out['target_classification'] = classify_registration_candidate(row.get('path', ''))
            out['reason'] = 'fallback command registry path'
            return out
    return {'path': '', 'accepted_target': 0, 'target_classification': 'MISSING', 'reason': 'no registration target found'}

def select_build(build_summary: List[Dict[str, str]]) -> Dict[str, Any]:
    # Prefer the active source CMakeLists over stale/high-scoring generated or legacy project files.
    for row in build_summary:
        if normalize_path(row.get('path', '')) == 'src/cmakelists.txt':
            out = dict(row)
            out['accepted_target'] = 1
            out['target_classification'] = classify_build_candidate(row.get('path', ''))
            out['reason'] = 'active source tree CMakeLists target preferred over generated/legacy vcxproj files'
            return out
    for row in build_summary:
        if is_active_build_candidate(row.get('path', '')) and classify_build_candidate(row.get('path', '')).startswith('ACTIVE'):
            out = dict(row)
            out['accepted_target'] = 1
            out['target_classification'] = classify_build_candidate(row.get('path', ''))
            out['reason'] = 'fallback active build candidate after excluding generated/legacy paths'
            return out
    return {'path': '', 'accepted_target': 0, 'target_classification': 'MISSING', 'reason': 'no active build target found'}

def refine_build_summary(build_summary: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for row in build_summary:
        path = row.get('path', '')
        cls = classify_build_candidate(path)
        rows.append({
            'path': path,
            'original_score_total': row.get('score_total', ''),
            'original_max_score': row.get('max_score', ''),
            'original_hit_rows': row.get('hit_rows', ''),
            'target_classification': cls,
            'active_candidate': int(cls != 'EXCLUDED_LEGACY_OR_GENERATED_BUILD_ARTIFACT'),
            'acceptance_note': 'prefer only after active CMake is ruled out' if cls not in {'PRIMARY_ACTIVE_CMAKE_TARGET', 'EXCLUDED_LEGACY_OR_GENERATED_BUILD_ARTIFACT'} else ('accepted primary if present' if cls == 'PRIMARY_ACTIVE_CMAKE_TARGET' else 'excluded from patch plan'),
        })
    rows.sort(key=lambda r: (0 if r['target_classification'] == 'PRIMARY_ACTIVE_CMAKE_TARGET' else 1 if r['active_candidate'] else 2, r['path'].lower()))
    return rows

def build_patch_plan(reg_target: Dict[str, Any], build_target: Dict[str, Any]) -> List[Dict[str, Any]]:
    reg_path = reg_target.get('path', 'UNKNOWN') or 'UNKNOWN'
    build_path = build_target.get('path', 'UNKNOWN') or 'UNKNOWN'
    return [
        {
            'patch_id': 'P1_INCLUDE_DDICT_HEADER',
            'accepted_target': reg_path,
            'proposed_change': 'Add include/declaration for cli/cmd_ddict.hpp at the active command registry implementation site if required by local registry pattern.',
            'allowed_in_dd066r': 0,
            'future_package': 'DD-067',
            'risk': 'MEDIUM',
        },
        {
            'patch_id': 'P2_REGISTER_DDICT_DISPATCH',
            'accepted_target': reg_path,
            'proposed_change': 'Register top-level DDICT command to xbase::cmd_DDICT with raw argument tail, preserving read-only command contract.',
            'allowed_in_dd066r': 0,
            'future_package': 'DD-067',
            'risk': 'MEDIUM_HIGH',
        },
        {
            'patch_id': 'P3_ADD_CMD_DDICT_TO_ACTIVE_BUILD',
            'accepted_target': build_path,
            'proposed_change': 'Add src/cli/cmd_ddict.cpp to the active source build list; do not patch legacy/generated vcxproj paths first.',
            'allowed_in_dd066r': 0,
            'future_package': 'DD-067',
            'risk': 'MEDIUM',
        },
        {
            'patch_id': 'P4_BUILD_AND_DDICT_HELP_SMOKE',
            'accepted_target': 'dottalkpp/data/tests/dd065_ddict_usage_smoke.dts',
            'proposed_change': 'After DD-067 build/registration patch, rebuild and run DDICT HELP/status smoke.',
            'allowed_in_dd066r': 0,
            'future_package': 'DD-068',
            'risk': 'LOW',
        },
    ]

def main() -> int:
    ap = argparse.ArgumentParser(description='DD-066R focused DDICT registration/build target refinement')
    ap.add_argument('--repo-root', required=True)
    ap.add_argument('--out-dir', required=True)
    ap.add_argument('--run-id', default='DD066R-ddict-registration-build-target-refinement-v0')
    ap.add_argument('--dd066-dir', default='docs/datadict/reports/DD066-ddict-registration-build-discovery-v0')
    ap.add_argument('--write-readiness', action='store_true')
    ap.add_argument('--readiness-path', default='docs/datadict/runlog/DD-066R_DDICT_REGISTRATION_BUILD_TARGET_REFINEMENT.md')
    ap.add_argument('--profile', action='append', default=[])
    ap.add_argument('--fail-on-review', action='store_true')
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    out = Path(args.out_dir).resolve()
    dd066_dir = (repo / args.dd066_dir).resolve()
    readiness_path = (repo / args.readiness_path).resolve()
    out.mkdir(parents=True, exist_ok=True)

    dd066_manifest = read_json(dd066_dir / 'dd066_ddict_registration_build_discovery_manifest.json')
    reg_summary = read_csv_dict(dd066_dir / 'dd066_registration_file_summary.csv')
    build_summary = read_csv_dict(dd066_dir / 'dd066_build_file_summary.csv')
    original_patch = read_csv_dict(dd066_dir / 'dd066_patch_plan_report_only.csv')

    dd066_ready = dd066_manifest.get('status') == EXPECTED_DD066_STATUS
    reg_target = select_registration(reg_summary)
    build_target = select_build(build_summary)
    refined_build = refine_build_summary(build_summary)
    refined_patch = build_patch_plan(reg_target, build_target)

    original_build_target = ''
    for row in original_patch:
        if row.get('patch_id') == 'P3_BUILD_INCLUDE_SOURCE':
            original_build_target = row.get('target', '')
            break
    original_build_target_excluded = int(bool(original_build_target) and not is_active_build_candidate(original_build_target))
    build_target_is_active = int(bool(build_target.get('path')) and is_active_build_candidate(build_target.get('path', '')))
    build_target_is_src_cmake = int(normalize_path(build_target.get('path', '')) == 'src/cmakelists.txt')
    reg_target_ok = int(normalize_path(reg_target.get('path', '')) == 'src/cli/command_registry.cpp')

    readiness_written = 0
    gate_rows = [
        {'gate': 'dd066_discovery_ready', 'expected': EXPECTED_DD066_STATUS, 'observed': dd066_manifest.get('status', ''), 'pass': int(dd066_ready)},
        {'gate': 'registration_target_is_active_command_registry_cpp', 'expected': 1, 'observed': reg_target_ok, 'pass': reg_target_ok},
        {'gate': 'build_target_is_active_candidate', 'expected': 1, 'observed': build_target_is_active, 'pass': build_target_is_active},
        {'gate': 'build_target_prefers_src_cmakelists', 'expected': 1, 'observed': build_target_is_src_cmake, 'pass': build_target_is_src_cmake},
        {'gate': 'original_legacy_build_target_detected', 'expected': '0 or 1', 'observed': original_build_target_excluded, 'pass': 1},
        {'gate': 'refined_patch_plan_report_only', 'expected': 1, 'observed': 1, 'pass': 1},
        {'gate': 'readiness_written_when_requested', 'expected': int(args.write_readiness), 'observed': 0, 'pass': int(not args.write_readiness)},
    ]

    failures = sum(1 for r in gate_rows if int(r['pass']) != 1)
    status = 'DDICT_REGISTRATION_BUILD_TARGET_REFINEMENT_READY' if failures == 0 else 'DDICT_REGISTRATION_BUILD_TARGET_REFINEMENT_REVIEW'

    if args.write_readiness:
        readiness_path.parent.mkdir(parents=True, exist_ok=True)
        text = '\n'.join([
            '# DD-066R DDICT Registration / Build Target Refinement',
            '',
            f'Run id: `{args.run_id}`',
            f'Created UTC: `{utc_now()}`',
            f'Status: **{status}**',
            '',
            '## Accepted targets',
            '',
            f'- Registration: `{reg_target.get("path", "")}`',
            f'- Build: `{build_target.get("path", "")}`',
            '',
            '## Correction',
            '',
            f'Original DD-066 build target: `{original_build_target}`',
            f'Original build target excluded as legacy/generated: `{original_build_target_excluded}`',
            '',
            'DD-067 should patch the accepted active targets only, not legacy/generated build artifacts.',
            '',
        ])
        readiness_path.write_text(text, encoding='utf-8')
        readiness_written = 1
        for row in gate_rows:
            if row['gate'] == 'readiness_written_when_requested':
                row['observed'] = readiness_written
                row['pass'] = 1
        failures = sum(1 for r in gate_rows if int(r['pass']) != 1)
        status = 'DDICT_REGISTRATION_BUILD_TARGET_REFINEMENT_READY' if failures == 0 else 'DDICT_REGISTRATION_BUILD_TARGET_REFINEMENT_REVIEW'

    boundary_rows = [
        {'boundary': 'target_refinement_report_only', 'observed': 1, 'required': 1, 'pass': 1},
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

    accepted_targets = [
        {'target_kind': 'registration', 'accepted_path': reg_target.get('path', ''), 'classification': reg_target.get('target_classification', ''), 'reason': reg_target.get('reason', '')},
        {'target_kind': 'build', 'accepted_path': build_target.get('path', ''), 'classification': build_target.get('target_classification', ''), 'reason': build_target.get('reason', '')},
        {'target_kind': 'smoke', 'accepted_path': 'dottalkpp/data/tests/dd065_ddict_usage_smoke.dts', 'classification': 'RUNTIME_SMOKE_AFTER_REGISTRATION', 'reason': 'run only after DD-067 build/registration patch'},
    ]

    write_csv(out / 'dd066r_accepted_patch_targets.csv', accepted_targets, ['target_kind', 'accepted_path', 'classification', 'reason'])
    write_csv(out / 'dd066r_refined_build_file_summary.csv', refined_build, ['path', 'original_score_total', 'original_max_score', 'original_hit_rows', 'target_classification', 'active_candidate', 'acceptance_note'])
    write_csv(out / 'dd066r_refined_patch_plan_report_only.csv', refined_patch, ['patch_id', 'accepted_target', 'proposed_change', 'allowed_in_dd066r', 'future_package', 'risk'])
    write_csv(out / 'dd066r_gate_ledger.csv', gate_rows, ['gate', 'expected', 'observed', 'pass'])
    write_csv(out / 'dd066r_no_mutation_boundary_ledger.csv', boundary_rows, ['boundary', 'observed', 'required', 'pass'])

    report_lines = [
        '# DD-066R DDICT Registration / Build Target Refinement',
        '',
        f'Run id: `{args.run_id}`',
        f'Status: **{status}**',
        f'Created UTC: `{utc_now()}`',
        '',
        '## Purpose',
        '',
        'DD-066R refines the DD-066 discovery output so DD-067 does not patch stale legacy or generated build files.',
        '',
        '## Accepted targets',
        '',
        f'- Registration target: `{reg_target.get("path", "")}`',
        f'- Build target: `{build_target.get("path", "")}`',
        f'- Original DD-066 P3 target: `{original_build_target}`',
        f'- Original target excluded as legacy/generated: **{original_build_target_excluded}**',
        '',
        '## Boundary',
        '',
        'DD-066R is report-only. It does not edit C++ files, edit build files, register runtime commands, mutate active catalog data, mutate DBF/CDX/LMDB artifacts, or mutate HELP/META/CMDHELPCHK.',
        '',
    ]
    (out / 'DD066R_DDICT_REGISTRATION_BUILD_TARGET_REFINEMENT_REPORT.md').write_text('\n'.join(report_lines), encoding='utf-8')

    manifest = {
        'contract': 'dd066r_ddict_registration_build_target_refinement_v0',
        'run_id': args.run_id,
        'created_utc': utc_now(),
        'status': status,
        'repo_root': str(repo),
        'profiles': args.profile,
        'dd066_status': dd066_manifest.get('status', ''),
        'accepted_registration_target': reg_target.get('path', ''),
        'accepted_build_target': build_target.get('path', ''),
        'original_build_target': original_build_target,
        'original_build_target_excluded': original_build_target_excluded,
        'readiness_written': readiness_written,
        'readiness_path': str(readiness_path) if readiness_written else '',
        'failures': failures,
        'cxx_source_edits': 0,
        'build_file_edits': 0,
        'runtime_command_registration': 0,
        'active_catalog_mutation': 0,
        'next_recommended_action': 'DD-067 guarded registration/build patch only after explicit authorization',
    }
    write_json(out / 'dd066r_ddict_registration_build_target_refinement_manifest.json', manifest)

    print(f"DD-066R DDICT registration/build target refinement manifest: {out / 'dd066r_ddict_registration_build_target_refinement_manifest.json'}")
    print(f"status: {status}; registration_target: {reg_target.get('path', '')}; build_target: {build_target.get('path', '')}; failures: {failures}; readiness_written: {readiness_written}")
    return 2 if (args.fail_on_review and failures) else 0

if __name__ == '__main__':
    raise SystemExit(main())
