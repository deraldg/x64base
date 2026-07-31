#!/usr/bin/env python3
"""
DD-028 DotTalk++ / x64base Data Dictionary baseline compare command.

Runs the report-only redocumentation check against an accepted DD-027 baseline:
  DD-024 scan -> DD-023 diff -> DD-025 classify -> DD-026 triage -> DD-028 summary.

This is the everyday check command: "Did anything meaningful change since the accepted baseline?"

Report-only. It does not edit source, build, launch DotTalk++ runtime, mutate HELP/META/CMDHELPCHK,
write DBF/CDX/LMDB catalogs, or promote dictionary facts.

Python: target 3.12+
"""
from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


BOUNDARY_ROWS = [
    ('source edits', 0, 0),
    ('build execution', 0, 0),
    ('DotTalk++ runtime launch', 0, 0),
    ('HELP mutation', 0, 0),
    ('META mutation', 0, 0),
    ('CMDHELPCHK mutation', 0, 0),
    ('DBF writes', 0, 0),
    ('CDX writes', 0, 0),
    ('LMDB writes', 0, 0),
    ('catalog promotion', 0, 0),
    ('dictionary baseline replacement', 0, 0),
    ('protected-system mutations', 0, 0),
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


def intish(value: Any, default: int = 0) -> int:
    if value is None:
        return default
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    try:
        return int(str(value).strip())
    except Exception:
        return default


def get_status(obj: dict[str, Any]) -> str:
    return str(obj.get('status') or obj.get('result') or '').strip().upper()


def get_count(obj: dict[str, Any], *names: str) -> int:
    for n in names:
        if n in obj:
            return intish(obj.get(n))
    for container in ('counts', 'summary'):
        d = obj.get(container)
        if isinstance(d, dict):
            for n in names:
                if n in d:
                    return intish(d.get(n))
    return 0


def get_nested(obj: dict[str, Any], *path: str, default: Any = None) -> Any:
    cur: Any = obj
    for part in path:
        if not isinstance(cur, dict) or part not in cur:
            return default
        cur = cur[part]
    return cur


def resolve_manifest(path: Path, names: list[str]) -> Path:
    if path.is_file():
        return path
    if not path.exists():
        raise FileNotFoundError(f'path does not exist: {path}')
    for name in names:
        candidate = path / name
        if candidate.exists():
            return candidate
    matches: list[Path] = []
    for name in names:
        matches.extend(path.rglob(name))
    matches = sorted(set(matches))
    if len(matches) == 1:
        return matches[0]
    raise FileNotFoundError(f'could not resolve manifest in {path}; expected one of {names}')


def resolve_baseline_manifest(path: Path) -> Path:
    return resolve_manifest(path, ['dd027_baseline_acceptance_manifest.json'])


def resolve_tool(repo_root: Path, rel: str) -> Path:
    p = repo_root / rel
    if not p.exists():
        raise FileNotFoundError(f'missing required tool: {p}')
    return p


def run_step(name: str, cmd: list[str], cwd: Path, transcript_dir: Path, execute: bool = True) -> dict[str, Any]:
    transcript_dir.mkdir(parents=True, exist_ok=True)
    transcript = transcript_dir / f'{name}.txt'
    row: dict[str, Any] = {
        'step': name,
        'command': ' '.join(cmd),
        'transcript': str(transcript),
        'exit_code': '',
        'status': 'PLANNED' if not execute else 'RUNNING',
    }
    if not execute:
        transcript.write_text('PLAN ONLY - command not executed\n' + ' '.join(cmd) + '\n', encoding='utf-8')
        return row
    proc = subprocess.run(cmd, cwd=str(cwd), text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    transcript.write_text(proc.stdout, encoding='utf-8')
    row['exit_code'] = proc.returncode
    row['status'] = 'PASS' if proc.returncode == 0 else 'FAIL'
    return row


def read_optional_manifest(path: Path, names: list[str]) -> tuple[Path | None, dict[str, Any] | None]:
    try:
        m = resolve_manifest(path, names)
        return m, read_json(m)
    except Exception:
        return None, None


def main() -> int:
    ap = argparse.ArgumentParser(description='DD-028 report-only accepted-baseline redocumentation check')
    ap.add_argument('--repo-root', required=True, help='Repository root to scan')
    ap.add_argument('--baseline', required=True, help='Accepted DD-027 baseline directory or manifest')
    ap.add_argument('--out-dir', required=True, help='Output directory for DD-028 run packet')
    ap.add_argument('--run-id', default=None, help='Stable DD-028 run id')
    ap.add_argument('--profile', action='append', default=[], help='Profile scope label; may be repeated')
    ap.add_argument('--python', dest='python_exe', default=sys.executable, help='Python executable to use for child tools; default current interpreter')
    ap.add_argument('--plan-only', action='store_true', help='Do not execute child tools; emit step plan only')
    ap.add_argument('--no-exclude-defaults', action='store_true', help='Pass through to scanner for diagnostics')
    ap.add_argument('--include-generated-evidence', action='store_true', help='Pass through to scanner deliberately')
    ap.add_argument('--exclude', action='append', default=[], help='Additional scanner exclusion; may be repeated')
    ap.add_argument('--fail-on-review', action='store_true', help='Exit nonzero when final status is REVIEW or BLOCKED_REVIEW')
    ap.add_argument('--fail-on-blocked', action='store_true', help='Exit nonzero only when final status is BLOCKED_REVIEW or TOOL_ERROR')
    args = ap.parse_args()

    repo_root = Path(args.repo_root).resolve()
    out_dir = Path(args.out_dir).resolve()
    run_id = args.run_id or datetime.now(timezone.utc).strftime('DD028-CHECK-%Y%m%dT%H%M%SZ')
    profiles = args.profile or ['UNSPECIFIED']
    py = str(Path(args.python_exe).resolve()) if args.python_exe else sys.executable

    out_dir.mkdir(parents=True, exist_ok=True)
    transcript_dir = out_dir / 'transcripts'

    baseline_manifest_path = resolve_baseline_manifest(Path(args.baseline).resolve())
    baseline = read_json(baseline_manifest_path)
    baseline_id = str(baseline.get('baseline_id') or Path(args.baseline).name)
    baseline_status = get_status(baseline)
    baseline_fingerprint = str(baseline.get('aggregate_fingerprint') or get_nested(baseline, 'exclusion_policy', 'aggregate_fingerprint', default='') or '')
    baseline_scan_manifest = str(baseline.get('scan_manifest') or '')
    if not baseline_scan_manifest:
        raise RuntimeError('baseline manifest does not include scan_manifest; cannot compare')

    scan_dir = out_dir / 'scan'
    diff_dir = out_dir / 'diff'
    class_dir = out_dir / 'classification'
    triage_dir = out_dir / 'triage'

    orch = resolve_tool(repo_root, 'tools/datadict/orchestrate/redoc_orchestrator.py')
    diff_tool = resolve_tool(repo_root, 'tools/datadict/diff/redoc_diff.py')
    classifier = resolve_tool(repo_root, 'tools/datadict/review/change_classifier.py')
    triage_tool = resolve_tool(repo_root, 'tools/datadict/review/triage_report.py')

    scan_cmd = [py, str(orch), '--repo-root', str(repo_root), '--out-dir', str(scan_dir), '--run-id', f'{run_id}-scan']
    for p in profiles:
        scan_cmd += ['--profile', p]
    if args.no_exclude_defaults:
        scan_cmd.append('--no-exclude-defaults')
    if args.include_generated_evidence:
        scan_cmd.append('--include-generated-evidence')
    for ex in args.exclude:
        scan_cmd += ['--exclude', ex]

    diff_cmd = [py, str(diff_tool), '--base', baseline_scan_manifest, '--candidate', str(scan_dir), '--out-dir', str(diff_dir), '--run-id', f'{run_id}-diff']
    for p in profiles:
        diff_cmd += ['--profile', p]

    class_cmd = [py, str(classifier), '--dd023', str(diff_dir), '--out-dir', str(class_dir), '--run-id', f'{run_id}-classify']
    for p in profiles:
        class_cmd += ['--profile', p]

    triage_cmd = [py, str(triage_tool), '--dd025', str(class_dir), '--out-dir', str(triage_dir), '--run-id', f'{run_id}-triage']
    for p in profiles:
        triage_cmd += ['--profile', p]

    steps: list[dict[str, Any]] = []
    final_status = 'PASS'
    warnings: list[str] = []

    for name, cmd in [('scan', scan_cmd), ('diff', diff_cmd), ('classify', class_cmd), ('triage', triage_cmd)]:
        step = run_step(name, cmd, repo_root, transcript_dir, execute=not args.plan_only)
        steps.append(step)
        if step['status'] == 'FAIL':
            final_status = 'TOOL_ERROR'
            warnings.append(f'step failed: {name}; see {step["transcript"]}')
            break

    scan_manifest_path: Path | None = None; scan: dict[str, Any] | None = None
    diff_manifest_path: Path | None = None; diff: dict[str, Any] | None = None
    class_manifest_path: Path | None = None; clas: dict[str, Any] | None = None
    triage_manifest_path: Path | None = None; triage: dict[str, Any] | None = None

    if not args.plan_only:
        scan_manifest_path, scan = read_optional_manifest(scan_dir, ['dd022_redoc_run_manifest.json'])
        diff_manifest_path, diff = read_optional_manifest(diff_dir, ['dd023_redoc_diff_manifest.json'])
        class_manifest_path, clas = read_optional_manifest(class_dir, ['dd025_change_classification_manifest.json'])
        triage_manifest_path, triage = read_optional_manifest(triage_dir, ['dd026_triage_manifest.json'])

    candidate_fingerprint = ''
    source_files_scanned = 0
    excluded_files = 0
    scan_warnings = 0
    added = removed = changed = 0
    review_rows = high_rows = lanes = gates = 0

    if scan:
        candidate_fingerprint = str(scan.get('aggregate_fingerprint') or get_nested(scan, 'exclusion_policy', 'aggregate_fingerprint', default='') or '')
        source_files_scanned = get_count(scan, 'source_files_scanned', 'scanned_files', 'included_files')
        excluded_files = get_count(scan, 'excluded', 'excluded_files', 'source_files_excluded')
        scan_warnings = get_count(scan, 'warnings', 'warning_count')
    if diff:
        added = get_count(diff, 'added', 'added_files', 'added_count', 'files_added')
        removed = get_count(diff, 'removed', 'removed_files', 'removed_count', 'files_removed')
        changed = get_count(diff, 'changed', 'changed_files', 'changed_count', 'files_changed')
    if triage:
        review_rows = get_count(triage, 'review_rows', 'review_queue_rows')
        high_rows = get_count(triage, 'high', 'high_rows')
        lanes = get_count(triage, 'lanes', 'lane_count')
        gates = get_count(triage, 'gates', 'gate_count')

    if final_status != 'TOOL_ERROR':
        if args.plan_only:
            final_status = 'PLAN_ONLY'
        elif scan is None or diff is None or clas is None or triage is None:
            final_status = 'TOOL_ERROR'
            warnings.append('one or more expected child manifests were not found')
        elif get_status(scan) != 'PASS':
            final_status = 'BLOCKED_REVIEW'
        elif high_rows > 0 or get_status(triage) == 'BLOCKED_REVIEW':
            final_status = 'BLOCKED_REVIEW'
        elif added or removed or changed or review_rows > 0 or get_status(diff) != 'PASS' or get_status(clas) not in {'PASS',''} or get_status(triage) not in {'PASS',''}:
            final_status = 'REVIEW'
        else:
            final_status = 'PASS'

    boundary_rows = [
        {'boundary': name, 'observed': observed, 'required': required, 'pass': 1 if observed == required else 0}
        for name, observed, required in BOUNDARY_ROWS
    ]

    step_rows = []
    for s in steps:
        step_rows.append({
            'step': s['step'],
            'status': s['status'],
            'exit_code': s.get('exit_code',''),
            'transcript': s.get('transcript',''),
            'command': s.get('command',''),
        })

    summary_rows = [
        {'metric': 'run_id', 'value': run_id},
        {'metric': 'baseline_id', 'value': baseline_id},
        {'metric': 'baseline_status', 'value': baseline_status},
        {'metric': 'final_status', 'value': final_status},
        {'metric': 'baseline_fingerprint', 'value': baseline_fingerprint},
        {'metric': 'candidate_fingerprint', 'value': candidate_fingerprint},
        {'metric': 'fingerprint_match', 'value': 1 if baseline_fingerprint and candidate_fingerprint and baseline_fingerprint == candidate_fingerprint else 0},
        {'metric': 'source_files_scanned', 'value': source_files_scanned},
        {'metric': 'excluded_files', 'value': excluded_files},
        {'metric': 'scan_warnings', 'value': scan_warnings},
        {'metric': 'added', 'value': added},
        {'metric': 'removed', 'value': removed},
        {'metric': 'changed', 'value': changed},
        {'metric': 'review_rows', 'value': review_rows},
        {'metric': 'high_rows', 'value': high_rows},
        {'metric': 'lanes', 'value': lanes},
        {'metric': 'gates', 'value': gates},
        {'metric': 'warnings', 'value': len(warnings)},
    ]

    write_csv(out_dir / 'dd028_step_ledger.csv', step_rows, ['step','status','exit_code','transcript','command'])
    write_csv(out_dir / 'dd028_summary.csv', summary_rows, ['metric','value'])
    write_csv(out_dir / 'dd028_boundary_ledger.csv', boundary_rows, ['boundary','observed','required','pass'])

    recommended: list[dict[str, Any]] = []
    if final_status == 'PASS':
        recommended.append({'priority': 1, 'action': 'No redocumentation change required', 'note': 'Candidate scan matches accepted baseline.'})
    elif final_status == 'REVIEW':
        recommended.append({'priority': 1, 'action': 'Review DD-026 triage packet', 'note': 'Meaningful non-blocking drift detected.'})
        recommended.append({'priority': 2, 'action': 'Run specialized rescans for affected lanes', 'note': 'Use DD-025 lane/gate classification to choose follow-up.'})
    elif final_status == 'BLOCKED_REVIEW':
        recommended.append({'priority': 1, 'action': 'Stop promotion', 'note': 'High severity or blocked triage rows were emitted.'})
        recommended.append({'priority': 2, 'action': 'Review high severity rows', 'note': 'Do not update baseline until resolved or explicitly accepted.'})
    elif final_status == 'TOOL_ERROR':
        recommended.append({'priority': 1, 'action': 'Repair toolchain or path issue', 'note': '; '.join(warnings)})
    else:
        recommended.append({'priority': 1, 'action': 'Review plan-only command ledger', 'note': 'No child tools were executed.'})
    write_csv(out_dir / 'dd028_recommended_next_actions.csv', recommended, ['priority','action','note'])

    manifest = {
        'schema': 'dd028_baseline_compare_run_v0',
        'run_id': run_id,
        'created_utc': utc_now(),
        'status': final_status,
        'boundary': 'REPORT_ONLY_NO_PROMOTION',
        'profiles': profiles,
        'repo_root': str(repo_root),
        'baseline_manifest': str(baseline_manifest_path),
        'baseline_id': baseline_id,
        'baseline_status': baseline_status,
        'baseline_scan_manifest': baseline_scan_manifest,
        'scan_manifest': str(scan_manifest_path) if scan_manifest_path else '',
        'diff_manifest': str(diff_manifest_path) if diff_manifest_path else '',
        'classification_manifest': str(class_manifest_path) if class_manifest_path else '',
        'triage_manifest': str(triage_manifest_path) if triage_manifest_path else '',
        'counts': {
            'source_files_scanned': source_files_scanned,
            'excluded_files': excluded_files,
            'scan_warnings': scan_warnings,
            'added': added,
            'removed': removed,
            'changed': changed,
            'review_rows': review_rows,
            'high_rows': high_rows,
            'lanes': lanes,
            'gates': gates,
            'warnings': len(warnings),
        },
        'fingerprints': {
            'baseline': baseline_fingerprint,
            'candidate': candidate_fingerprint,
            'match': bool(baseline_fingerprint and candidate_fingerprint and baseline_fingerprint == candidate_fingerprint),
        },
        'outputs': {
            'step_ledger_csv': str(out_dir / 'dd028_step_ledger.csv'),
            'summary_csv': str(out_dir / 'dd028_summary.csv'),
            'boundary_ledger_csv': str(out_dir / 'dd028_boundary_ledger.csv'),
            'recommended_next_actions_csv': str(out_dir / 'dd028_recommended_next_actions.csv'),
            'triage_report_md': str(triage_dir / 'DD026_TRIAGE_REPORT.md'),
        },
        'warnings': warnings,
        'next_action': recommended[0]['action'] if recommended else '',
    }
    write_json(out_dir / 'dd028_baseline_compare_manifest.json', manifest)

    md = f"""# DD-028 Baseline Compare Report\n\n- Run ID: `{run_id}`\n- Baseline: `{baseline_id}`\n- Status: **{final_status}**\n- Boundary: report-only; no source/build/HELP/META/CMDHELPCHK/DBF/CDX/LMDB/catalog mutation.\n\n## Fingerprints\n\n- Baseline: `{baseline_fingerprint}`\n- Candidate: `{candidate_fingerprint}`\n- Match: `{manifest['fingerprints']['match']}`\n\n## Counts\n\n| Metric | Value |\n|---|---:|\n| Source files scanned | {source_files_scanned} |\n| Excluded files | {excluded_files} |\n| Added | {added} |\n| Removed | {removed} |\n| Changed | {changed} |\n| Review rows | {review_rows} |\n| High rows | {high_rows} |\n| Lanes | {lanes} |\n| Gates | {gates} |\n| Warnings | {len(warnings)} |\n\n## Recommended next actions\n\n"""
    for r in recommended:
        md += f"{r['priority']}. **{r['action']}** — {r['note']}\n"
    md += "\n## Child artifacts\n\n"
    for label, value in [('scan', scan_manifest_path), ('diff', diff_manifest_path), ('classification', class_manifest_path), ('triage', triage_manifest_path)]:
        md += f"- {label}: `{value or ''}`\n"
    (out_dir / 'DD028_BASELINE_COMPARE_REPORT.md').write_text(md, encoding='utf-8')

    print(f'DD-028 baseline compare manifest: {out_dir / "dd028_baseline_compare_manifest.json"}')
    print(f'status: {final_status}; added: {added}; removed: {removed}; changed: {changed}; review_rows: {review_rows}; high: {high_rows}')
    if args.fail_on_review and final_status in {'REVIEW','BLOCKED_REVIEW','TOOL_ERROR'}:
        return 2
    if args.fail_on_blocked and final_status in {'BLOCKED_REVIEW','TOOL_ERROR'}:
        return 2
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
