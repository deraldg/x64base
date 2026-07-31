#!/usr/bin/env python3
"""
DD-027 DotTalk++ / x64base Data Dictionary baseline acceptance tool.

Accepts a green, report-only redocumentation run as the comparison baseline.
It reads DD-022/DD-024 scan manifests plus optional DD-023 diff and DD-026 triage
manifests, validates gates, and writes an accepted-baseline packet.

Report-only. Does not mutate source, build outputs, HELP/META/CMDHELPCHK, DBF/CDX/LMDB,
or promoted dictionary catalogs.

Python: target 3.12+
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from datetime import datetime, timezone


def file_sha256_local(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()
from pathlib import Path
from typing import Any


REQUIRED_BOUNDARIES = [
    'source edits',
    'build execution',
    'runtime launch',
    'HELP mutation',
    'META mutation',
    'CMDHELPCHK mutation',
    'DBF writes',
    'CDX writes',
    'LMDB writes',
    'catalog promotion',
    'publication replacement',
    'protected-system mutations',
]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00','Z')


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding='utf-8'))


def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for row in rows:
            w.writerow({field: row.get(field, '') for field in fields})


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def resolve_manifest(path: Path, preferred_names: list[str]) -> Path:
    if path.is_file():
        return path
    if not path.is_dir():
        raise FileNotFoundError(f'path does not exist: {path}')
    for name in preferred_names:
        candidate = path / name
        if candidate.exists():
            return candidate
    candidates = sorted(path.glob('*.json'))
    if len(candidates) == 1:
        return candidates[0]
    raise FileNotFoundError(f'could not resolve manifest in {path}; expected one of {preferred_names}')


def intish(value: Any, default: int = 0) -> int:
    if value is None:
        return default
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    try:
        return int(str(value).strip())
    except Exception:
        return default


def get_count(obj: dict[str, Any], *keys: str) -> int:
    for key in keys:
        if key in obj:
            return intish(obj.get(key))
    counts = obj.get('counts')
    if isinstance(counts, dict):
        for key in keys:
            if key in counts:
                return intish(counts.get(key))
    summary = obj.get('summary')
    if isinstance(summary, dict):
        for key in keys:
            if key in summary:
                return intish(summary.get(key))
    return 0


def get_nested(obj: dict[str, Any], *keys: str, default: Any = '') -> Any:
    for key in keys:
        cur: Any = obj
        ok = True
        for part in key.split('.'):
            if isinstance(cur, dict) and part in cur:
                cur = cur[part]
            else:
                ok = False
                break
        if ok:
            return cur
    return default


def get_count_nested(obj: dict[str, Any], *keys: str) -> int:
    direct = get_count(obj, *[k for k in keys if '.' not in k])
    if direct:
        return direct
    for key in keys:
        if '.' in key:
            value = get_nested(obj, key, default=None)
            if value is not None:
                return intish(value)
    return 0


def get_status(obj: dict[str, Any]) -> str:
    return str(obj.get('status') or obj.get('result') or '').strip().upper()


def gate_row(gate: str, observed: Any, required: Any, passed: bool, note: str = '') -> dict[str, Any]:
    return {
        'gate': gate,
        'observed': observed,
        'required': required,
        'pass': 1 if passed else 0,
        'note': note,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description='DD-027 report-only baseline acceptance and run registry builder')
    ap.add_argument('--scan', required=True, help='DD-022/DD-024 scan run directory or dd022_redoc_run_manifest.json')
    ap.add_argument('--diff', help='Optional DD-023 clean diff directory or manifest proving stability')
    ap.add_argument('--triage', help='Optional DD-026 clean triage directory or manifest proving empty review queue')
    ap.add_argument('--out-dir', required=True, help='Output directory for accepted baseline packet')
    ap.add_argument('--run-id', default='DD027-baseline-acceptance-v0', help='Stable DD-027 run id')
    ap.add_argument('--baseline-id', default='', help='Accepted baseline id; default derived from run id')
    ap.add_argument('--profile', action='append', default=[], help='Profile scope label; may be repeated')
    ap.add_argument('--allow-scan-warnings', action='store_true', help='Allow scan warnings while still requiring PASS scan status')
    ap.add_argument('--allow-review-triage', action='store_true', help='Allow triage status REVIEW; HIGH rows still block')
    ap.add_argument('--fail-on-blocked', action='store_true', help='Exit nonzero if baseline acceptance is blocked')
    args = ap.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    scan_manifest_path = resolve_manifest(Path(args.scan), ['dd022_redoc_run_manifest.json'])
    scan = read_json(scan_manifest_path)

    diff_manifest_path: Path | None = None
    diff: dict[str, Any] | None = None
    if args.diff:
        diff_manifest_path = resolve_manifest(Path(args.diff), ['dd023_redoc_diff_manifest.json'])
        diff = read_json(diff_manifest_path)

    triage_manifest_path: Path | None = None
    triage: dict[str, Any] | None = None
    if args.triage:
        triage_manifest_path = resolve_manifest(Path(args.triage), ['dd026_triage_manifest.json'])
        triage = read_json(triage_manifest_path)

    created = utc_now()
    baseline_id = args.baseline_id or args.run_id.replace('DD027-', 'DDBASE-')
    profiles = args.profile or ['UNSPECIFIED']

    gates: list[dict[str, Any]] = []

    scan_status = get_status(scan)
    scan_warnings = get_count(scan, 'warnings', 'warning_count')
    source_files_scanned = get_count_nested(scan, 'source_files_scanned', 'scanned_files', 'included_files', 'exclusion_policy.stable_source_count')
    excluded_files = get_count_nested(scan, 'excluded', 'excluded_files', 'source_files_excluded', 'exclusion_policy.excluded_count')
    aggregate_fingerprint = str(
        scan.get('aggregate_fingerprint')
        or scan.get('source_aggregate_fingerprint')
        or get_nested(scan, 'exclusion_policy.aggregate_fingerprint', default='')
        or ''
    )

    gates.append(gate_row('scan manifest resolved', str(scan_manifest_path), 'exists', scan_manifest_path.exists()))
    gates.append(gate_row('scan status PASS', scan_status, 'PASS', scan_status == 'PASS'))
    gates.append(gate_row('scan source files present', source_files_scanned, '> 0', source_files_scanned > 0))
    gates.append(gate_row('scan warnings acceptable', scan_warnings, '0 unless --allow-scan-warnings', args.allow_scan_warnings or scan_warnings == 0))
    gates.append(gate_row('aggregate fingerprint present', aggregate_fingerprint[:16] + ('...' if aggregate_fingerprint else ''), 'non-empty', bool(aggregate_fingerprint)))

    if diff is not None and diff_manifest_path is not None:
        diff_status = get_status(diff)
        added = get_count(diff, 'added', 'added_count', 'files_added')
        removed = get_count(diff, 'removed', 'removed_count', 'files_removed')
        changed = get_count(diff, 'changed', 'changed_count', 'files_changed')
        diff_warnings = get_count(diff, 'warnings', 'warning_count')
        gates.append(gate_row('diff manifest resolved', str(diff_manifest_path), 'exists', diff_manifest_path.exists()))
        gates.append(gate_row('diff status PASS', diff_status, 'PASS', diff_status == 'PASS'))
        gates.append(gate_row('diff added zero', added, '0', added == 0))
        gates.append(gate_row('diff removed zero', removed, '0', removed == 0))
        gates.append(gate_row('diff changed zero', changed, '0', changed == 0))
        gates.append(gate_row('diff warnings zero', diff_warnings, '0', diff_warnings == 0))
    else:
        added = removed = changed = diff_warnings = ''
        gates.append(gate_row('diff proof supplied', 'missing', 'recommended clean DD-023 diff', False, 'Baseline can be designed without diff proof, but should not be accepted as stable.'))

    if triage is not None and triage_manifest_path is not None:
        triage_status = get_status(triage)
        review_rows = get_count(triage, 'review_rows')
        high_rows = get_count(triage, 'high', 'high_severity_rows')
        lanes = get_count(triage, 'lanes', 'review_lanes')
        triage_status_ok = triage_status == 'PASS' or (args.allow_review_triage and triage_status == 'REVIEW')
        gates.append(gate_row('triage manifest resolved', str(triage_manifest_path), 'exists', triage_manifest_path.exists()))
        gates.append(gate_row('triage status acceptable', triage_status, 'PASS unless --allow-review-triage', triage_status_ok))
        gates.append(gate_row('triage high rows zero', high_rows, '0', high_rows == 0))
        gates.append(gate_row('triage review rows zero', review_rows, '0 unless --allow-review-triage', args.allow_review_triage or review_rows == 0))
        gates.append(gate_row('triage lanes zero', lanes, '0 unless --allow-review-triage', args.allow_review_triage or lanes == 0))
    else:
        review_rows = high_rows = lanes = ''
        gates.append(gate_row('triage proof supplied', 'missing', 'recommended clean DD-026 triage', False, 'Baseline should include triage proof before acceptance.'))

    boundary_rows = []
    for boundary in REQUIRED_BOUNDARIES:
        boundary_rows.append({
            'boundary': boundary,
            'observed': 0,
            'required': 0,
            'pass': 1,
            'note': 'DD-027 writes only baseline acceptance artifacts under the requested output directory.'
        })

    gate_failures = sum(1 for row in gates if intish(row.get('pass')) != 1)
    boundary_failures = sum(1 for row in boundary_rows if intish(row.get('pass')) != 1)
    status = 'ACCEPTED_BASELINE' if gate_failures == 0 and boundary_failures == 0 else 'BLOCKED_BASELINE_REVIEW'

    artifact_rows = []
    for role, path in [('scan_manifest', scan_manifest_path), ('diff_manifest', diff_manifest_path), ('triage_manifest', triage_manifest_path)]:
        if path is not None:
            artifact_rows.append({
                'role': role,
                'path': str(path),
                'sha256': file_sha256(path),
                'bytes': path.stat().st_size,
            })

    registry_rows = [{
        'baseline_id': baseline_id,
        'accepted_by_run_id': args.run_id,
        'created_utc': created,
        'status': status,
        'profiles': ';'.join(profiles),
        'scan_manifest': str(scan_manifest_path),
        'diff_manifest': str(diff_manifest_path or ''),
        'triage_manifest': str(triage_manifest_path or ''),
        'source_files_scanned': source_files_scanned,
        'excluded_files': excluded_files,
        'aggregate_fingerprint': aggregate_fingerprint,
        'review_rows': review_rows,
        'high_rows': high_rows,
        'next_comparison_target': str(scan_manifest_path),
        'notes': 'Report-only accepted baseline packet; no catalog promotion.' if status == 'ACCEPTED_BASELINE' else 'Acceptance blocked; inspect gate ledger.',
    }]

    comparison_target = {
        'baseline_id': baseline_id,
        'status': status,
        'accepted_scan_manifest': str(scan_manifest_path),
        'aggregate_fingerprint': aggregate_fingerprint,
        'source_files_scanned': source_files_scanned,
        'excluded_files': excluded_files,
        'profiles': profiles,
        'next_run_should_compare_against': str(scan_manifest_path),
        'recommended_next_command_pattern': 'redoc_orchestrator.py -> redoc_diff.py --base <accepted_scan_run> --candidate <new_scan_run> -> change_classifier.py -> triage_report.py',
    }

    manifest = {
        'schema': 'dd027_baseline_acceptance_manifest_v0',
        'run_id': args.run_id,
        'baseline_id': baseline_id,
        'created_utc': created,
        'status': status,
        'profiles': profiles,
        'scan_manifest': str(scan_manifest_path),
        'diff_manifest': str(diff_manifest_path or ''),
        'triage_manifest': str(triage_manifest_path or ''),
        'source_files_scanned': source_files_scanned,
        'excluded_files': excluded_files,
        'aggregate_fingerprint': aggregate_fingerprint,
        'gate_failures': gate_failures,
        'boundary_failures': boundary_failures,
        'review_rows': review_rows,
        'high_rows': high_rows,
        'artifact_count': len(artifact_rows),
        'report_only_boundary': {
            'source_edits': 0,
            'build_execution': 0,
            'runtime_launch': 0,
            'help_meta_cmdhelpchk_mutation': 0,
            'dbf_cdx_lmdb_catalog_mutation': 0,
            'dictionary_promotion': 0,
        }
    }

    md_lines = [
        '# DD-027 Baseline Acceptance Report',
        '',
        f"Run id: `{args.run_id}`",
        f"Baseline id: `{baseline_id}`",
        f"Status: **{status}**",
        f"Created UTC: `{created}`",
        '',
        '## Accepted scan candidate',
        '',
        f"- Scan manifest: `{scan_manifest_path}`",
        f"- Source files scanned: {source_files_scanned}",
        f"- Excluded files: {excluded_files}",
        f"- Aggregate fingerprint: `{aggregate_fingerprint}`",
        '',
        '## Stability proof',
        '',
        f"- Diff manifest: `{diff_manifest_path or ''}`",
        f"- Triage manifest: `{triage_manifest_path or ''}`",
        f"- Gate failures: {gate_failures}",
        f"- Boundary failures: {boundary_failures}",
        '',
        '## Gate ledger',
        '',
        '| Gate | Observed | Required | Pass | Note |',
        '|---|---|---|---:|---|',
    ]
    for row in gates:
        md_lines.append(f"| {row['gate']} | {row['observed']} | {row['required']} | {row['pass']} | {row.get('note','')} |")
    md_lines += [
        '',
        '## Boundary ledger',
        '',
        '| Boundary | Observed | Required | Pass |',
        '|---|---:|---:|---:|',
    ]
    for row in boundary_rows:
        md_lines.append(f"| {row['boundary']} | {row['observed']} | {row['required']} | {row['pass']} |")
    md_lines += [
        '',
        '## Result',
        '',
        'This packet accepts a baseline only when scan, clean diff, clean triage, and no-mutation boundaries are green. It does not promote dictionary DBFs or mutate HELP/META/CMDHELPCHK.',
        ''
    ]

    write_json(out_dir / 'dd027_baseline_acceptance_manifest.json', manifest)
    write_json(out_dir / 'dd027_next_comparison_target.json', comparison_target)
    write_csv(out_dir / 'dd027_gate_ledger.csv', gates, ['gate','observed','required','pass','note'])
    write_csv(out_dir / 'dd027_boundary_ledger.csv', boundary_rows, ['boundary','observed','required','pass','note'])
    write_csv(out_dir / 'dd027_artifact_manifest.csv', artifact_rows, ['role','path','sha256','bytes'])
    write_csv(out_dir / 'dd027_run_registry_row.csv', registry_rows, ['baseline_id','accepted_by_run_id','created_utc','status','profiles','scan_manifest','diff_manifest','triage_manifest','source_files_scanned','excluded_files','aggregate_fingerprint','review_rows','high_rows','next_comparison_target','notes'])
    (out_dir / 'DD027_BASELINE_ACCEPTANCE_REPORT.md').write_text('\n'.join(md_lines), encoding='utf-8')

    print(f'DD-027 baseline manifest: {out_dir / "dd027_baseline_acceptance_manifest.json"}')
    print(f'status: {status}; gate_failures: {gate_failures}; boundary_failures: {boundary_failures}; fingerprint: {aggregate_fingerprint}')
    return 2 if status.startswith('BLOCKED') and args.fail_on_blocked else 0


if __name__ == '__main__':
    raise SystemExit(main())
