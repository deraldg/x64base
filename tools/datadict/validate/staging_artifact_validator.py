#!/usr/bin/env python3
"""
DD-020 Staging Artifact Validator Skeleton v0

Report-only validator for DD-019-style catalog staging packages.

It checks package shape, manifest presence, CSV headers, required columns,
row counts, simple referential consistency, gate semantics, and file hashes.
It does not import to x64base, launch DotTalk++, build C++, mutate HELP,
run CMDHELPCHK, or promote catalog facts.

Target: Python 3.12+
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple


@dataclass
class CheckRow:
    check_id: str
    check_name: str
    status: str
    severity: str
    detail: str
    artifact: str = ""
    logical_table: str = ""


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(65536), b''):
            h.update(chunk)
    return h.hexdigest()


def read_csv(path: Path) -> List[Dict[str, str]]:
    with path.open('r', encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))


def csv_headers(path: Path) -> List[str]:
    with path.open('r', encoding='utf-8-sig', newline='') as f:
        reader = csv.reader(f)
        try:
            return next(reader)
        except StopIteration:
            return []


def write_csv(path: Path, rows: List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields: List[str] = []
    for row in rows:
        for key in row.keys():
            if key not in fields:
                fields.append(key)
    if not fields:
        fields = ['EMPTY']
    with path.open('w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for row in rows:
            w.writerow({k: row.get(k, '') for k in fields})


def load_optional_json(path: Path) -> Tuple[Dict[str, Any] | None, str | None]:
    try:
        return json.loads(path.read_text(encoding='utf-8')), None
    except Exception as exc:  # deliberately broad for validator reporting
        return None, str(exc)


def status_rank(status: str) -> int:
    order = {'PASS': 0, 'INFO': 0, 'REVIEW': 1, 'BLOCK': 2, 'FAIL': 3}
    return order.get(status.upper(), 1)


def validate_package(package_dir: Path, output_dir: Path) -> Dict[str, Any]:
    package_dir = package_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    checks: List[CheckRow] = []
    file_rows: List[Dict[str, Any]] = []
    table_rows: List[Dict[str, Any]] = []
    gate_rows: List[Dict[str, Any]] = []
    ref_rows: List[Dict[str, Any]] = []

    def add(name: str, status: str, severity: str, detail: str, artifact: str = '', logical_table: str = '') -> None:
        checks.append(CheckRow(f'CHK-{len(checks)+1:04d}', name, status, severity, detail, artifact, logical_table))

    if not package_dir.exists():
        add('PACKAGE_DIR_EXISTS', 'FAIL', 'fail', f'Package directory not found: {package_dir}')
        return emit_report(package_dir, output_dir, checks, file_rows, table_rows, gate_rows, ref_rows)
    add('PACKAGE_DIR_EXISTS', 'PASS', 'info', f'Package directory found: {package_dir}')

    manifest_candidates = sorted(package_dir.glob('*staging*manifest*.json')) + sorted(package_dir.glob('*manifest*.json'))
    manifest_path = manifest_candidates[0] if manifest_candidates else None
    manifest: Dict[str, Any] = {}
    if not manifest_path:
        add('MANIFEST_PRESENT', 'FAIL', 'fail', 'No staging/package manifest JSON found.')
    else:
        manifest_obj, err = load_optional_json(manifest_path)
        if err:
            add('MANIFEST_PARSE', 'FAIL', 'fail', f'Manifest parse failed: {err}', str(manifest_path.name))
        else:
            manifest = manifest_obj or {}
            add('MANIFEST_PARSE', 'PASS', 'info', 'Manifest JSON parsed.', str(manifest_path.name))

    schema_path = package_dir / 'dd019_catalog_staging_package_v0.schema.json'
    add('SCHEMA_PRESENT', 'PASS' if schema_path.exists() else 'REVIEW', 'review' if not schema_path.exists() else 'info',
        'Catalog staging schema present.' if schema_path.exists() else 'Catalog staging schema not found.', schema_path.name)

    table_plan_path = package_dir / 'dd019_catalog_table_plan_v0.csv'
    field_plan_path = package_dir / 'dd019_staging_table_field_plan_v0.csv'
    table_plan = read_csv(table_plan_path) if table_plan_path.exists() else []
    field_plan = read_csv(field_plan_path) if field_plan_path.exists() else []
    add('TABLE_PLAN_PRESENT', 'PASS' if table_plan else 'FAIL', 'fail' if not table_plan else 'info', f'Table-plan rows: {len(table_plan)}', table_plan_path.name)
    add('FIELD_PLAN_PRESENT', 'PASS' if field_plan else 'REVIEW', 'review' if not field_plan else 'info', f'Field-plan rows: {len(field_plan)}', field_plan_path.name)

    required_fields: Dict[str, List[str]] = {}
    planned_fields: Dict[str, List[str]] = {}
    for row in field_plan:
        table = row.get('logical_table', '')
        field = row.get('field', '')
        if not table or not field:
            continue
        planned_fields.setdefault(table, []).append(field)
        if row.get('required', '').lower() == 'yes':
            required_fields.setdefault(table, []).append(field)

    # Find files and hash them.
    for p in sorted(package_dir.rglob('*')):
        if p.is_file():
            rel = str(p.relative_to(package_dir)).replace('\\', '/')
            file_rows.append({
                'artifact': rel,
                'bytes': p.stat().st_size,
                'sha256': sha256_file(p),
                'kind': p.suffix.lower().lstrip('.') or 'file',
            })

    # Determine staging artifact map.
    staging_tables = manifest.get('staging_tables', []) if isinstance(manifest, dict) else []
    manifest_artifacts = {r.get('logical_table', ''): r.get('artifact', '') for r in staging_tables if isinstance(r, dict)}
    plan_tables = [r.get('logical_table', '') for r in table_plan if r.get('logical_table')]

    # Validate each planned table.
    sample_dir = package_dir / 'sample_output'
    loaded_tables: Dict[str, List[Dict[str, str]]] = {}
    for row in table_plan:
        table = row.get('logical_table', '')
        if not table:
            continue
        artifact = manifest_artifacts.get(table)
        if not artifact:
            # Derive likely name from table plan when not in manifest.
            artifact = 'dd019_' + table.lower().replace('dd_', '') + '_v0.csv'
        path = sample_dir / artifact
        exists = path.exists()
        headers = csv_headers(path) if exists else []
        rows = read_csv(path) if exists else []
        loaded_tables[table] = rows
        missing_cols = [c for c in required_fields.get(table, []) if c not in headers]
        missing_field_plan = table not in planned_fields
        blanks = 0
        if exists and not missing_field_plan:
            for r in rows:
                for c in required_fields.get(table, []):
                    if c in headers and str(r.get(c, '')).strip() == '':
                        blanks += 1
        status = 'PASS'
        severity = 'info'
        detail = f'rows={len(rows)} headers={len(headers)}'
        if not exists:
            # Missing execution artifacts are FAIL only when the table already has a
            # field plan. Tables planned but not yet field-specified remain REVIEW
            # so DD-020 can serve as a schema-readiness validator, not an execution gate.
            if table not in planned_fields:
                status = 'REVIEW'
                severity = 'review'
            else:
                status = 'REVIEW' if row.get('required_for_stage', '').lower() != 'yes' else 'FAIL'
                severity = 'review' if status == 'REVIEW' else 'fail'
            detail = 'artifact not found'
        elif missing_field_plan:
            status = 'REVIEW'
            severity = 'review'
            detail += '; no field plan for this table'
        elif missing_cols:
            status = 'FAIL'
            severity = 'fail'
            detail += '; missing required columns: ' + ', '.join(missing_cols)
        elif blanks:
            status = 'REVIEW'
            severity = 'review'
            detail += f'; blank required values={blanks}'
        table_rows.append({
            'logical_table': table,
            'artifact': f'sample_output/{artifact}',
            'exists': int(exists),
            'row_count': len(rows),
            'header_count': len(headers),
            'required_column_count': len(required_fields.get(table, [])),
            'missing_required_columns': ';'.join(missing_cols),
            'blank_required_values': blanks,
            'field_plan_present': int(not missing_field_plan),
            'status': status,
            'detail': detail,
        })
        add('TABLE_ARTIFACT_VALIDATE', status, severity, detail, f'sample_output/{artifact}', table)

    # Cross-row consistency checks for tables with sample artifacts.
    objects = loaded_tables.get('DD_OBJECT', [])
    evidence = loaded_tables.get('DD_EVIDENCE', [])
    attrs = loaded_tables.get('DD_ATTRIBUTE', [])
    edges = loaded_tables.get('DD_EDGE', [])
    gates = loaded_tables.get('DD_GATE', [])
    conflicts = loaded_tables.get('DD_CONFLICT', [])
    warnings = loaded_tables.get('DD_WARNING', [])
    promo = loaded_tables.get('DD_PROMOTION_QUEUE', [])

    object_ids = {r.get('OBJECT_ID', '') for r in objects}
    evidence_ids = {r.get('EVID_ID', '') for r in evidence}
    source_ids = {r.get('SOURCE_ID', '') for r in loaded_tables.get('DD_SOURCE', [])}

    def ref_check(name: str, rows: List[Dict[str, str]], field: str, valid: set[str], allow_blank: bool, table: str) -> None:
        bad = []
        for idx, row in enumerate(rows, start=2):
            val = row.get(field, '')
            if not val and allow_blank:
                continue
            if val not in valid:
                bad.append(f'row{idx}:{val}')
        status = 'PASS' if not bad else 'REVIEW'
        detail = 'ok' if not bad else ';'.join(bad[:20])
        ref_rows.append({'check_name': name, 'table': table, 'field': field, 'bad_count': len(bad), 'status': status, 'detail': detail})
        add(name, status, 'review' if bad else 'info', detail, logical_table=table)

    if objects and evidence:
        ref_check('EVIDENCE_OBJECT_REF', evidence, 'OBJECT_ID', object_ids, False, 'DD_EVIDENCE')
    if evidence and source_ids:
        ref_check('EVIDENCE_SOURCE_REF', evidence, 'SOURCE_ID', source_ids, False, 'DD_EVIDENCE')
    if attrs and object_ids:
        ref_check('ATTRIBUTE_OBJECT_REF', attrs, 'OBJECT_ID', object_ids, False, 'DD_ATTRIBUTE')
    if attrs and evidence_ids:
        ref_check('ATTRIBUTE_EVIDENCE_REF', attrs, 'EVID_ID', evidence_ids, False, 'DD_ATTRIBUTE')
    if edges and object_ids:
        ref_check('EDGE_FROM_REF', edges, 'FROM_ID', object_ids, False, 'DD_EDGE')
        ref_check('EDGE_TO_REF', edges, 'TO_ID', object_ids, False, 'DD_EDGE')
    if edges and evidence_ids:
        ref_check('EDGE_EVIDENCE_REF', edges, 'EVID_ID', evidence_ids, True, 'DD_EDGE')
    if conflicts and object_ids:
        ref_check('CONFLICT_OBJECT_REF', conflicts, 'OBJECT_ID', object_ids, False, 'DD_CONFLICT')

    # Gate semantics.
    promotion_gate_seen = False
    for row in gates:
        gate_name = row.get('GATE_NAME', '')
        result = row.get('RESULT', '')
        status = 'PASS'
        detail = row.get('DETAIL', '')
        if gate_name == 'PROMOTION_AUTHORIZED':
            promotion_gate_seen = True
            if result == 'PASS':
                status = 'FAIL'
                detail = 'Promotion gate is PASS in a report-only validator; should remain BLOCK without authorization.'
            elif result == 'BLOCK':
                status = 'PASS'
                detail = 'Promotion correctly blocked for report-only staging package.'
            else:
                status = 'REVIEW'
                detail = f'Unexpected promotion gate result: {result}'
        gate_rows.append({
            'GATE_ID': row.get('GATE_ID', ''),
            'GATE_NAME': gate_name,
            'RESULT': result,
            'validator_status': status,
            'detail': detail,
        })
    if gates and not promotion_gate_seen:
        add('PROMOTION_GATE_PRESENT', 'REVIEW', 'review', 'PROMOTION_AUTHORIZED gate not found.', logical_table='DD_GATE')
    elif gates:
        add('PROMOTION_GATE_PRESENT', 'PASS', 'info', 'PROMOTION_AUTHORIZED gate found and checked.', logical_table='DD_GATE')

    # Manifest count checks.
    src_proj = manifest.get('source_projection', {}) if isinstance(manifest, dict) else {}
    if src_proj:
        expected_objects = int(src_proj.get('projected_object_count', -1))
        expected_conflicts = int(src_proj.get('conflict_count', -1))
        expected_evidence = int(src_proj.get('evidence_stack_count', -1))
        count_checks = [
            ('MANIFEST_OBJECT_COUNT', expected_objects, len(objects), 'DD_OBJECT'),
            ('MANIFEST_CONFLICT_COUNT', expected_conflicts, len(conflicts), 'DD_CONFLICT'),
            ('MANIFEST_EVIDENCE_COUNT', expected_evidence, len(evidence), 'DD_EVIDENCE'),
        ]
        for name, expected, actual, table in count_checks:
            if expected < 0:
                add(name, 'REVIEW', 'review', 'Expected count absent from manifest.', logical_table=table)
            elif expected == actual:
                add(name, 'PASS', 'info', f'expected={expected} actual={actual}', logical_table=table)
            else:
                add(name, 'REVIEW', 'review', f'expected={expected} actual={actual}', logical_table=table)

    # Re-documentation readiness: file hashes and run spine must exist; promotion remains blocked.
    add('FILE_HASHES_CAPTURED', 'PASS' if file_rows else 'FAIL', 'fail' if not file_rows else 'info', f'file rows hashed={len(file_rows)}')
    add('REPORT_ONLY_BOUNDARY', 'PASS', 'info', 'Validator performs no import, runtime launch, HELP mutation, or catalog promotion.')

    return emit_report(package_dir, output_dir, checks, file_rows, table_rows, gate_rows, ref_rows)


def emit_report(package_dir: Path, output_dir: Path, checks: List[CheckRow], file_rows: List[Dict[str, Any]], table_rows: List[Dict[str, Any]], gate_rows: List[Dict[str, Any]], ref_rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    status_counts: Dict[str, int] = {}
    for c in checks:
        status_counts[c.status] = status_counts.get(c.status, 0) + 1
    overall = 'GREEN'
    if any(c.status == 'FAIL' for c in checks):
        overall = 'FAILED'
    elif any(c.status == 'BLOCK' for c in checks):
        overall = 'BLOCKED'
    elif any(c.status == 'REVIEW' for c in checks):
        overall = 'REVIEW'

    report = {
        'package_id': 'DD020_STAGING_ARTIFACT_VALIDATOR_SKELETON_v0',
        'boundary': 'REPORT_ONLY',
        'generated_at_utc': datetime.now(timezone.utc).isoformat(),
        'input_package_dir': str(package_dir),
        'overall_status': overall,
        'status_counts': status_counts,
        'file_count': len(file_rows),
        'table_artifact_count': len(table_rows),
        'gate_row_count': len(gate_rows),
        'referential_check_count': len(ref_rows),
        'checks': [asdict(c) for c in checks],
    }

    (output_dir / 'dd020_validation_report_v0.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    write_csv(output_dir / 'dd020_validation_checks_v0.csv', [asdict(c) for c in checks])
    write_csv(output_dir / 'dd020_file_manifest_v0.csv', file_rows)
    write_csv(output_dir / 'dd020_table_validation_v0.csv', table_rows)
    write_csv(output_dir / 'dd020_gate_validation_v0.csv', gate_rows)
    write_csv(output_dir / 'dd020_referential_validation_v0.csv', ref_rows)
    write_csv(output_dir / 'dd020_validation_summary_v0.csv', [{
        'overall_status': overall,
        'check_count': len(checks),
        'pass_count': status_counts.get('PASS', 0),
        'review_count': status_counts.get('REVIEW', 0),
        'block_count': status_counts.get('BLOCK', 0),
        'fail_count': status_counts.get('FAIL', 0),
        'file_count': len(file_rows),
        'table_artifact_count': len(table_rows),
        'gate_row_count': len(gate_rows),
        'referential_check_count': len(ref_rows),
    }])
    return report


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description='Validate DD-019-style catalog staging artifacts without mutation.')
    parser.add_argument('--package-dir', required=True, help='Directory containing a DD-019-style staging package.')
    parser.add_argument('--output-dir', required=True, help='Directory where validation reports should be written.')
    args = parser.parse_args(argv)
    report = validate_package(Path(args.package_dir), Path(args.output_dir))
    print(json.dumps({
        'overall_status': report['overall_status'],
        'check_count': len(report['checks']),
        'file_count': report['file_count'],
        'table_artifact_count': report['table_artifact_count'],
    }, indent=2))
    return 0 if report['overall_status'] in {'GREEN', 'REVIEW'} else 2


if __name__ == '__main__':
    raise SystemExit(main())
