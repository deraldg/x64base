#!/usr/bin/env python3
"""
DD-025 DotTalk++ / x64base data-dictionary change classifier.

Takes DD-023 diff output and converts raw added/removed/changed file rows into
an actionable review queue. Report-only by default. It does not rescan source,
launch DotTalk++, regenerate HELP, mutate DBFs, or promote catalog facts.

Python: target 3.12+
"""
from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding='utf-8'))


def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, '') for field in fields})


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open('r', newline='', encoding='utf-8') as f:
        return [dict(row) for row in csv.DictReader(f)]


def resolve_dd023_dir(path: Path) -> Path:
    if path.is_dir():
        return path
    if path.is_file() and path.name == 'dd023_redoc_diff_manifest.json':
        return path.parent
    raise FileNotFoundError(f'could not resolve DD-023 run directory from {path}')


def classify_path(path: str, object_kind: str) -> dict[str, str]:
    p = path.replace('\\', '/').lower()
    k = (object_kind or '').strip().lower()

    # Strong path-based lanes first.
    if p.startswith('src/') or p.startswith('include/'):
        if '/cli/' in p or p.startswith('src/cli/') or p.startswith('include/cli/'):
            return lane('source_code', 'command_or_cli_surface', 'HIGH', 'SOURCE_CONTRACT_RESCAN_REQUIRED;HELP_COVERAGE_CHECK_REQUIRED;RUNTIME_PROOF_REVIEW_REQUIRED', 'C++ CLI/source surface changed; rerun usage-contract, HELP, message, and runtime proof checks as applicable.')
        if '/xbase' in p or '/memo' in p or '/cdx' in p or '/xindex' in p:
            return lane('source_code', 'physical_engine_surface', 'HIGH', 'PHYSICAL_DICTIONARY_RESCAN_REQUIRED;RUNTIME_PROOF_REVIEW_REQUIRED', 'Physical engine/header/index/memo surface changed; rerun physical dictionary extraction and proof planning.')
        if '/workspace' in p or '/tuple' in p:
            return lane('source_code', 'relation_tuple_surface', 'HIGH', 'RELATION_TUPLE_RESCAN_REQUIRED;TRANSCRIPT_PROOF_REVIEW_REQUIRED', 'Workspace/relation/tuple surface changed; rerun relation dictionary source map and transcript proof review.')
        if '/dt/meta' in p or '/meta/' in p:
            return lane('source_code', 'metafact_metadata_surface', 'HIGH', 'METAFACT_RESCAN_REQUIRED;CATALOG_STAGING_REVIEW_REQUIRED', 'MetaFact/metadata surface changed; rerun source-contract/MetaFact bridge and staging review.')
        if '/xexpr' in p or '/expr/' in p:
            return lane('source_code', 'expression_rule_surface', 'HIGH', 'XEXPR_RULE_RESCAN_REQUIRED', 'Expression/function/rule surface changed; rerun rules/constraints/xexpr link map.')
        return lane('source_code', 'general_source_surface', 'MEDIUM', 'SOURCE_RESCAN_REQUIRED', 'Source code/header changed; review for dictionary impact.')

    if p.startswith('cmake/') or p.endswith('cmakelists.txt') or p.endswith('.cmake') or p.endswith('cmakepresets.json'):
        return lane('build_contract', 'build_profile_surface', 'HIGH', 'BUILD_PROFILE_REVIEW_REQUIRED;OPTIONAL_OVERLAY_BOUNDARY_REVIEW_REQUIRED', 'Build/configuration changed; review engine/professional/education profile boundaries.')

    if p.startswith('docs/datadict/'):
        return lane('datadict_generated_or_spec', 'datadict_lane', 'LOW', 'DATADICT_SELF_REVIEW_REQUIRED', 'Data Dictionary lane artifact changed; review but do not treat as engine source drift unless explicitly included.')

    if p.startswith('docs/manuals/developer/manualgen/'):
        return lane('manualgen_artifact', 'manualgen_lane', 'MEDIUM', 'MANUALGEN_REVIEW_REQUIRED', 'Manualgen artifact changed; review publication/regeneration impact separately from dictionary core.')

    if p.startswith('docs/'):
        return lane('documentation', 'documentation_surface', 'LOW', 'DOC_REVIEW_REQUIRED', 'Documentation changed; review for linked HELP/manual/dictionary impact.')

    if p.startswith('dottalkpp/scripts/') or p.endswith('.dts') or p.endswith('.ps1'):
        return lane('script', 'runtime_or_maintenance_script_surface', 'HIGH', 'SCRIPT_BOUNDARY_REVIEW_REQUIRED;DD_SCRIPT_RESCAN_REQUIRED', 'Runtime/maintenance script changed; classify script role, boundary, and dependency links.')

    if p.startswith('dottalkpp/data/schemas/') or '/schemas/' in p or p.endswith('.schema.json'):
        return lane('schema_rule', 'schema_surface', 'HIGH', 'SCHEMA_RESCAN_REQUIRED;RULE_BINDING_REVIEW_REQUIRED', 'Schema evidence changed; rerun declared schema and rule binding extraction.')

    if p.endswith('.json'):
        return lane('json_contract', 'json_contract_surface', 'MEDIUM', 'CONTRACT_REVIEW_REQUIRED', 'JSON contract/manifest changed; review whether schema or generated report.')

    if k in {'python_tool_or_test'} or p.endswith('.py'):
        return lane('python_tool', 'tooling_surface', 'MEDIUM', 'TOOL_REVIEW_REQUIRED', 'Python tool/test changed; run help/smoke and review boundary class.')

    if p.startswith('bindings/'):
        return lane('binding_surface', 'python_binding_surface', 'MEDIUM', 'BINDING_SMOKE_REQUIRED', 'Binding surface changed; rerun pydottalk smoke and dictionary API review.')

    return lane(k or 'unknown', 'unclassified_surface', 'MEDIUM', 'HUMAN_TRIAGE_REQUIRED', 'Unclassified change; human review required before promotion.')


def lane(change_class: str, lane_name: str, severity: str, gates: str, action: str) -> dict[str, str]:
    return {
        'change_class': change_class,
        'review_lane': lane_name,
        'severity': severity,
        'required_gates': gates,
        'recommended_action': action,
    }


def disposition(change_kind: str, severity: str) -> str:
    if severity == 'HIGH':
        return 'BLOCK_PROMOTION_PENDING_REVIEW'
    if change_kind in {'REMOVED', 'CHANGED'}:
        return 'REVIEW_REQUIRED'
    return 'QUEUE_FOR_TRIAGE'


def main() -> int:
    parser = argparse.ArgumentParser(description='DD-025 report-only change classification and review queue builder')
    parser.add_argument('--dd023', required=True, help='DD-023 diff run directory or manifest path')
    parser.add_argument('--out-dir', required=True, help='Output directory for DD-025 artifacts')
    parser.add_argument('--run-id', default=None, help='Stable DD-025 run id')
    parser.add_argument('--profile', action='append', default=[], help='Profile scope label; may be repeated')
    parser.add_argument('--fail-on-high', action='store_true', help='Exit nonzero if HIGH severity review rows are emitted')
    args = parser.parse_args()

    dd023_dir = resolve_dd023_dir(Path(args.dd023).resolve())
    dd023_manifest_path = dd023_dir / 'dd023_redoc_diff_manifest.json'
    dd023_manifest = read_json(dd023_manifest_path) if dd023_manifest_path.exists() else {}
    file_diff = read_csv(dd023_dir / 'dd023_file_diff.csv')

    rows: list[dict[str, Any]] = []
    for i, row in enumerate(file_diff, start=1):
        path = row.get('path', '')
        change_kind = row.get('change_kind', '')
        object_kind = row.get('object_kind', '')
        cls = classify_path(path, object_kind)
        rows.append({
            'review_id': f'DD025-REV-{i:05d}',
            'change_kind': change_kind,
            'path': path,
            'object_kind': object_kind,
            'change_class': cls['change_class'],
            'review_lane': cls['review_lane'],
            'severity': cls['severity'],
            'required_gates': cls['required_gates'],
            'recommended_action': cls['recommended_action'],
            'promotion_disposition': disposition(change_kind, cls['severity']),
            'base_sha256': row.get('base_sha256', ''),
            'candidate_sha256': row.get('candidate_sha256', ''),
            'base_bytes': row.get('base_bytes', ''),
            'candidate_bytes': row.get('candidate_bytes', ''),
        })

    summary: dict[tuple[str, str], int] = {}
    sev: dict[str, int] = {}
    lane_counts: dict[str, int] = {}
    for row in rows:
        summary[(row['change_kind'], row['change_class'])] = summary.get((row['change_kind'], row['change_class']), 0) + 1
        sev[row['severity']] = sev.get(row['severity'], 0) + 1
        lane_counts[row['review_lane']] = lane_counts.get(row['review_lane'], 0) + 1

    summary_rows = [
        {'change_kind': ck, 'change_class': cc, 'count': count}
        for (ck, cc), count in sorted(summary.items())
    ]
    severity_rows = [{'severity': k, 'count': v} for k, v in sorted(sev.items())]
    lane_rows = [{'review_lane': k, 'count': v} for k, v in sorted(lane_counts.items())]

    high_count = sev.get('HIGH', 0)
    status = 'PASS'
    if rows:
        status = 'REVIEW'
    if high_count:
        status = 'BLOCKED_REVIEW'

    out_dir = Path(args.out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    fields = ['review_id','change_kind','path','object_kind','change_class','review_lane','severity','required_gates','recommended_action','promotion_disposition','base_sha256','candidate_sha256','base_bytes','candidate_bytes']
    write_csv(out_dir / 'dd025_classified_review_queue.csv', rows, fields)
    write_csv(out_dir / 'dd025_classification_summary.csv', summary_rows, ['change_kind','change_class','count'])
    write_csv(out_dir / 'dd025_severity_summary.csv', severity_rows, ['severity','count'])
    write_csv(out_dir / 'dd025_review_lane_summary.csv', lane_rows, ['review_lane','count'])

    run_id = args.run_id or datetime.now(timezone.utc).strftime('DD025-CLASSIFY-%Y%m%dT%H%M%SZ')
    manifest = {
        'schema_version': 'dd025_change_classification_review_queue_v0',
        'run_id': run_id,
        'created_utc': datetime.now(timezone.utc).isoformat(),
        'status': status,
        'boundary': 'REPORT_ONLY_PROMOTION_BLOCKED',
        'profile_scope': args.profile,
        'dd023_manifest': str(dd023_manifest_path),
        'dd023_run_id': dd023_manifest.get('run_id'),
        'counts': {
            'review_rows': len(rows),
            'high_severity_rows': high_count,
            'medium_severity_rows': sev.get('MEDIUM', 0),
            'low_severity_rows': sev.get('LOW', 0),
            'review_lanes': len(lane_counts),
        },
        'outputs': {
            'classified_review_queue_csv': str(out_dir / 'dd025_classified_review_queue.csv'),
            'classification_summary_csv': str(out_dir / 'dd025_classification_summary.csv'),
            'severity_summary_csv': str(out_dir / 'dd025_severity_summary.csv'),
            'review_lane_summary_csv': str(out_dir / 'dd025_review_lane_summary.csv'),
        },
        'next_action': 'Review DD-025 rows; run specialized extractors/proof plans for affected lanes; do not promote without explicit authorization.',
    }
    write_json(out_dir / 'dd025_change_classification_manifest.json', manifest)
    print(f'DD-025 classification manifest: {out_dir / "dd025_change_classification_manifest.json"}')
    print(f'status: {status}; review_rows: {len(rows)}; high: {high_count}; lanes: {len(lane_counts)}')
    if high_count and args.fail_on_high:
        return 2
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
