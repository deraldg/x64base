#!/usr/bin/env python3
"""DD-032 report-only baseline-v1 acceptance plan builder."""
from __future__ import annotations
import argparse, csv, json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

BOUNDARY_ROWS = [
    ('source edits',0,0),('build execution',0,0),('DotTalk++ runtime launch',0,0),
    ('HELP mutation',0,0),('META mutation',0,0),('CMDHELPCHK mutation',0,0),
    ('DBF writes',0,0),('CDX writes',0,0),('LMDB writes',0,0),('catalog promotion',0,0),
    ('dictionary baseline replacement',0,0),('file moves/deletes',0,0),('protected-system mutations',0,0),
]
REQUIRED_TOOLS = [
    ('DD-024 scanner','tools/datadict/orchestrate/redoc_orchestrator.py'),
    ('DD-023 diff','tools/datadict/diff/redoc_diff.py'),
    ('DD-025 classifier','tools/datadict/review/change_classifier.py'),
    ('DD-026 triage','tools/datadict/review/triage_report.py'),
    ('DD-027 baseline accept','tools/datadict/baseline/baseline_accept.py'),
    ('DD-028 baseline check','tools/datadict/baseline/baseline_check.py'),
]

def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00','Z')

def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')

def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding='utf-8'))

def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for row in rows:
            w.writerow({field: row.get(field, '') for field in fields})

def resolve_manifest(path: Path, names: list[str]) -> Path:
    if path.is_file():
        return path
    if not path.exists():
        raise FileNotFoundError(f'path does not exist: {path}')
    for name in names:
        candidate = path / name
        if candidate.exists():
            return candidate
    matches = []
    for name in names:
        matches.extend(path.rglob(name))
    matches = sorted(set(matches))
    if len(matches) == 1:
        return matches[0]
    raise FileNotFoundError(f'could not resolve manifest in {path}; expected one of {names}')

def get_nested(obj: dict[str, Any], *path: str, default: Any = None) -> Any:
    cur: Any = obj
    for part in path:
        if not isinstance(cur, dict) or part not in cur:
            return default
        cur = cur[part]
    return cur

def status_of(value: Any) -> str:
    return str(value or '').strip().upper()

def psq(value: Path | str) -> str:
    s = str(value).replace('"', '`"')
    return '"' + s + '"'

def add_profiles(lines: list[str], profiles: list[str]) -> None:
    for i, profile in enumerate(profiles):
        suffix = ' `' if i < len(profiles)-1 else ''
        lines.append(f'  --profile {profile}{suffix}')

def command_block(py: str, script: str, args: list[tuple[str, str]], profiles: list[str]) -> list[str]:
    lines = [f'& {py} .\\{script} `']
    body = [(k, v) for k, v in args]
    for k, v in body:
        lines.append(f'  {k} {v} `')
    add_profiles(lines, profiles)
    return lines

def main() -> int:
    ap = argparse.ArgumentParser(description='DD-032 report-only baseline-v1 acceptance plan builder')
    ap.add_argument('--repo-root', required=True)
    ap.add_argument('--current-baseline', required=True)
    ap.add_argument('--out-dir', required=True)
    ap.add_argument('--run-id', default='DD032-baseline-v1-plan-v0')
    ap.add_argument('--next-baseline-id', default='DDBASE-stable-v1')
    ap.add_argument('--readiness', default=None)
    ap.add_argument('--python-var', default='$py12')
    ap.add_argument('--profile', action='append', default=[])
    ap.add_argument('--fail-on-blocked', action='store_true')
    args = ap.parse_args()

    repo_root = Path(args.repo_root).resolve()
    out_dir = Path(args.out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    profiles = args.profile or ['UNSPECIFIED']
    baseline_manifest_path = resolve_manifest(Path(args.current_baseline).resolve(), ['dd027_baseline_acceptance_manifest.json'])
    baseline = read_json(baseline_manifest_path)
    baseline_id = str(baseline.get('baseline_id') or Path(args.current_baseline).name)
    fp = str(baseline.get('aggregate_fingerprint') or get_nested(baseline, 'exclusion_policy', 'aggregate_fingerprint', default='') or '')
    scan_manifest = str(baseline.get('scan_manifest') or '')

    readiness_path = None
    readiness_status = 'NOT_PROVIDED'
    readiness_failures = ''
    if args.readiness:
        rp = resolve_manifest(Path(args.readiness).resolve(), ['dd031_baseline_readiness_manifest.json'])
        readiness_path = str(rp)
        r = read_json(rp)
        readiness_status = status_of(r.get('status'))
        readiness_failures = str(r.get('gate_failures',''))

    gate_rows: list[dict[str, Any]] = []
    def gate(name: str, observed: Any, required: Any, passed: bool, note: str='') -> None:
        gate_rows.append({'gate': name, 'observed': observed, 'required': required, 'pass': 1 if passed else 0, 'note': note})
    gate('current baseline manifest exists', str(baseline_manifest_path), 'present', baseline_manifest_path.exists())
    gate('current baseline accepted', status_of(baseline.get('status')), 'ACCEPTED_BASELINE', status_of(baseline.get('status')) == 'ACCEPTED_BASELINE')
    gate('current baseline fingerprint present', fp, 'non-empty', bool(fp))
    gate('current baseline scan manifest reference present', scan_manifest, 'non-empty', bool(scan_manifest))
    for name, rel in REQUIRED_TOOLS:
        gate(f'required tool present: {name}', rel, 'present', (repo_root / rel).exists())
    if args.readiness:
        ok = readiness_status in {'BASELINE_UNCHANGED','READY_FOR_BASELINE_REVIEW','REVIEW','PASS'} and str(readiness_failures or '0') in {'','0'}
        gate('DD-031 readiness provided', readiness_status, 'nonblocking readiness', ok, readiness_path or '')
    else:
        gate('DD-031 readiness provided', 'not provided', 'optional', True, 'DD-032 can still produce the plan')
    gate_failures = sum(1 for r in gate_rows if not r['pass'])
    status = 'BASELINE_V1_PLAN_READY' if gate_failures == 0 else 'BLOCKED_BASELINE_V1_PLAN'

    reports = repo_root / 'docs' / 'datadict' / 'reports'
    review = repo_root / 'docs' / 'datadict' / 'review_queue'
    baselines = repo_root / 'docs' / 'datadict' / 'baselines'
    scan_a = 'DDRUN-stable-v1-A'; scan_b = 'DDRUN-stable-v1-B'; diff_ab = 'DDRUN-stable-v1-A-to-B-diff'
    class_ab = 'DD025-stable-v1-A-to-B'; triage_ab = 'DD026-stable-v1-A-to-B'
    accept_run = 'DD027-stable-v1-baseline-acceptance'; check_run = 'DD028-check-stable-v1-current'
    py = args.python_var

    lines = [
        '# DD-032 guarded Data Dictionary baseline-v1 acceptance command plan',
        f'# Repo: {repo_root}', f'# Current baseline: {baseline_id}', f'# Next baseline: {args.next_baseline_id}',
        '# Boundary: report-only scans/diffs/classification/triage until DD-027 baseline acceptance.', '',
        f'cd {psq(repo_root)}', '', f'& {py} --version', '',
        '# 1. Fresh stable scan A after DD-031/DD-032 installation.',
    ]
    lines += command_block(py, 'tools\\datadict\\orchestrate\\redoc_orchestrator.py', [('--repo-root', psq(repo_root)),('--out-dir', psq(reports/scan_a)),('--run-id', scan_a)], profiles)
    lines += ['', '# 2. Fresh stable scan B after DD-031/DD-032 installation.']
    lines += command_block(py, 'tools\\datadict\\orchestrate\\redoc_orchestrator.py', [('--repo-root', psq(repo_root)),('--out-dir', psq(reports/scan_b)),('--run-id', scan_b)], profiles)
    lines += ['', '# 3. Prove stable A/B has zero meaningful drift.']
    lines += command_block(py, 'tools\\datadict\\diff\\redoc_diff.py', [('--base', psq(reports/scan_a)),('--candidate', psq(reports/scan_b)),('--out-dir', psq(reports/diff_ab)),('--run-id', diff_ab)], profiles)
    lines += ['', '# 4. Classify the stable A/B diff.']
    lines += command_block(py, 'tools\\datadict\\review\\change_classifier.py', [('--dd023', psq(reports/diff_ab)),('--out-dir', psq(review/class_ab)),('--run-id', class_ab)], profiles)
    lines += ['', '# 5. Triage the stable A/B classification.']
    lines += command_block(py, 'tools\\datadict\\review\\triage_report.py', [('--dd025', psq(review/class_ab)),('--out-dir', psq(review/triage_ab)),('--run-id', triage_ab)], profiles)
    lines += ['', f'# 6. Accept {args.next_baseline_id} only if steps 1-5 are green.']
    lines += command_block(py, 'tools\\datadict\\baseline\\baseline_accept.py', [('--scan', psq(reports/scan_b)),('--diff', psq(reports/diff_ab)),('--triage', psq(review/triage_ab)),('--out-dir', psq(baselines/args.next_baseline_id)),('--run-id', accept_run),('--baseline-id', args.next_baseline_id)], profiles)
    lines += ['', '# 7. Check the repo against the newly accepted baseline.']
    lines += command_block(py, 'tools\\datadict\\baseline\\baseline_check.py', [('--repo-root', psq(repo_root)),('--baseline', psq(baselines/args.next_baseline_id)),('--out-dir', psq(reports/check_run)),('--run-id', check_run)], profiles)
    commands = '\n'.join(lines) + '\n'

    command_rows = [
        {'step':1,'name':'stable scan A','tool':'redoc_orchestrator.py','output':str(reports/scan_a),'expected':'PASS'},
        {'step':2,'name':'stable scan B','tool':'redoc_orchestrator.py','output':str(reports/scan_b),'expected':'PASS'},
        {'step':3,'name':'stable A/B diff','tool':'redoc_diff.py','output':str(reports/diff_ab),'expected':'PASS added=0 removed=0 changed=0'},
        {'step':4,'name':'classify stable A/B','tool':'change_classifier.py','output':str(review/class_ab),'expected':'PASS review_rows=0'},
        {'step':5,'name':'triage stable A/B','tool':'triage_report.py','output':str(review/triage_ab),'expected':'PASS review_rows=0'},
        {'step':6,'name':'accept v1 baseline','tool':'baseline_accept.py','output':str(baselines/args.next_baseline_id),'expected':'ACCEPTED_BASELINE'},
        {'step':7,'name':'check against v1 baseline','tool':'baseline_check.py','output':str(reports/check_run),'expected':'PASS added=0 removed=0 changed=0'},
    ]
    boundary_rows = [{'boundary': b, 'observed': obs, 'required': req, 'pass': 1 if obs == req else 0} for b, obs, req in BOUNDARY_ROWS]
    next_steps = [
        {'priority':1,'action':'Run the generated command plan.','reason':'Fresh A/B proof is required after DD-031/DD-032 installation.'},
        {'priority':2,'action':'Verify stable A/B diff is PASS with zero changes.','reason':'Do not accept v1 if scanner is unstable.'},
        {'priority':3,'action':'Accept DDBASE-stable-v1 with DD-027 only after green proof.','reason':'Baseline movement must be explicit.'},
        {'priority':4,'action':'Run DD-028 against DDBASE-stable-v1.','reason':'Everyday baseline check should then pass.'},
    ]
    manifest = {
        'schema':'dd032_baseline_v1_acceptance_plan_v0','run_id':args.run_id,'status':status,'created_utc':utc_now(),
        'repo_root':str(repo_root),'profiles':profiles,'current_baseline_id':baseline_id,
        'current_baseline_manifest':str(baseline_manifest_path),'current_aggregate_fingerprint':fp,
        'next_baseline_id':args.next_baseline_id,'readiness_manifest':readiness_path,'readiness_status':readiness_status,
        'gate_failures':gate_failures,'boundary_failures':sum(1 for r in boundary_rows if not r['pass']),'command_plan':command_rows,
    }
    write_json(out_dir/'dd032_baseline_v1_acceptance_plan_manifest.json', manifest)
    write_csv(out_dir/'dd032_gate_ledger.csv', gate_rows, ['gate','observed','required','pass','note'])
    write_csv(out_dir/'dd032_boundary_ledger.csv', boundary_rows, ['boundary','observed','required','pass'])
    write_csv(out_dir/'dd032_command_plan.csv', command_rows, ['step','name','tool','output','expected'])
    write_csv(out_dir/'dd032_next_steps.csv', next_steps, ['priority','action','reason'])
    (out_dir/'dd032_accept_baseline_v1_commands.ps1').write_text(commands, encoding='utf-8')
    report = f"""# DD-032 Baseline v1 Acceptance Plan\n\nRun id: `{args.run_id}`  \nStatus: **{status}**  \nCreated UTC: `{manifest['created_utc']}`\n\nCurrent baseline: `{baseline_id}`  \nCurrent fingerprint: `{fp}`  \nNext baseline candidate: `{args.next_baseline_id}`\n\nGate failures: **{gate_failures}**  \nBoundary failures: **{manifest['boundary_failures']}**\n\nRequired sequence: fresh scan A, fresh scan B, clean A/B diff, empty classification, empty triage, explicit DD-027 acceptance, then DD-028 check against v1.\n\nBoundary: report-only plan. It does not edit source, run builds, launch DotTalk++, mutate HELP/META/CMDHELPCHK, write DBF/CDX/LMDB/catalog data, move/delete files, or accept a baseline.\n"""
    (out_dir/'DD032_BASELINE_V1_ACCEPTANCE_PLAN.md').write_text(report, encoding='utf-8')
    print(f'DD-032 baseline v1 plan manifest: {out_dir / "dd032_baseline_v1_acceptance_plan_manifest.json"}')
    print(f'status: {status}; gate_failures: {gate_failures}; next_baseline: {args.next_baseline_id}')
    return 2 if args.fail_on_blocked and status.startswith('BLOCKED') else 0

if __name__ == '__main__':
    raise SystemExit(main())
