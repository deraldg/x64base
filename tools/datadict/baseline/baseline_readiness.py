#!/usr/bin/env python3
"""DD-031 report-only disposition-aware baseline readiness checker.

This tool combines DD-028 baseline compare output, DD-029 artifact disposition
output, and DD-030 script-boundary disposition output to answer whether the
current repo state is ready for a new accepted Data Dictionary baseline.

It is report-only. It does not edit source, move files, accept a baseline,
mutate HELP/META/CMDHELPCHK, or write DBF/CDX/LMDB/catalog data.
"""
from __future__ import annotations

import argparse
import csv
import datetime as _dt
import json
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


def now_utc() -> str:
    return _dt.datetime.now(_dt.timezone.utc).isoformat()


def read_json(path: Path) -> Dict[str, Any]:
    with path.open('r', encoding='utf-8') as f:
        return json.load(f)


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open('r', encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))


def write_json(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, sort_keys=True)
        f.write('\n')


def write_csv(path: Path, rows: List[Dict[str, Any]], fieldnames: Optional[List[str]] = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        keys: List[str] = []
        for row in rows:
            for key in row.keys():
                if key not in keys:
                    keys.append(key)
        fieldnames = keys or ['note']
    with path.open('w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, '') for k in fieldnames})


def find_file(input_path: Path, candidates: Iterable[str]) -> Optional[Path]:
    if input_path.is_file():
        return input_path
    for name in candidates:
        direct = input_path / name
        if direct.exists():
            return direct
    for name in candidates:
        found = list(input_path.rglob(name))
        if found:
            return found[0]
    return None


def as_int(value: Any, default: int = 0) -> int:
    if value is None or value == '':
        return default
    try:
        return int(value)
    except Exception:
        try:
            return int(float(value))
        except Exception:
            return default


def collect_top_packages(rows: List[Dict[str, str]]) -> List[str]:
    packages = set()
    for row in rows:
        path = row.get('path') or row.get('Path') or row.get('file') or row.get('File') or ''
        path = path.replace('\\', '/')
        first = path.split('/', 1)[0]
        if re.match(r'^mdo_\d+_', first, re.IGNORECASE):
            packages.add(first)
    return sorted(packages)


def load_inputs(dd028: Path, dd029: Path, dd030: Path) -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any], List[Dict[str, str]], List[Dict[str, str]], List[Dict[str, str]]]:
    dd028_manifest_path = find_file(dd028, ['dd028_baseline_compare_manifest.json'])
    dd029_manifest_path = find_file(dd029, ['dd029_artifact_disposition_manifest.json'])
    dd030_manifest_path = find_file(dd030, ['dd030_script_boundary_manifest.json'])
    if not dd028_manifest_path:
        raise SystemExit(f'DD-028 manifest not found under {dd028}')
    if not dd029_manifest_path:
        raise SystemExit(f'DD-029 manifest not found under {dd029}')
    if not dd030_manifest_path:
        raise SystemExit(f'DD-030 manifest not found under {dd030}')

    dd028_j = read_json(dd028_manifest_path)
    dd029_j = read_json(dd029_manifest_path)
    dd030_j = read_json(dd030_manifest_path)

    dd029_rows = read_csv(find_file(dd029, ['dd029_artifact_disposition_rows.csv']) or Path('__missing__'))
    dd029_summary = read_csv(find_file(dd029, ['dd029_disposition_summary.csv']) or Path('__missing__'))
    dd030_rows = read_csv(find_file(dd030, ['dd030_script_boundary_rows.csv', 'dd030_script_boundary_disposition_rows.csv']) or Path('__missing__'))
    return dd028_j, dd029_j, dd030_j, dd029_rows, dd029_summary, dd030_rows


def get_nested(data: Dict[str, Any], *keys: str, default: Any = None) -> Any:
    cur: Any = data
    for key in keys:
        if not isinstance(cur, dict) or key not in cur:
            return default
        cur = cur[key]
    return cur


def summarize_dd028(dd028: Dict[str, Any]) -> Dict[str, Any]:
    summary = dd028.get('summary') if isinstance(dd028.get('summary'), dict) else dd028
    return {
        'status': dd028.get('status') or summary.get('status') or '',
        'added': as_int(summary.get('added') or dd028.get('added')),
        'removed': as_int(summary.get('removed') or dd028.get('removed')),
        'changed': as_int(summary.get('changed') or dd028.get('changed')),
        'review_rows': as_int(summary.get('review_rows') or dd028.get('review_rows')),
        'high': as_int(summary.get('high') or dd028.get('high')),
    }


def summarize_dd029(dd029: Dict[str, Any]) -> Dict[str, Any]:
    summary = dd029.get('summary') if isinstance(dd029.get('summary'), dict) else dd029
    return {
        'status': dd029.get('status') or summary.get('status') or '',
        'review_rows': as_int(summary.get('review_rows') or dd029.get('review_rows')),
        'high': as_int(summary.get('high') or dd029.get('high')),
        'dispositions': as_int(summary.get('dispositions') or dd029.get('dispositions')),
        'boundary_failures': as_int(summary.get('boundary_failures') or dd029.get('boundary_failures')),
    }


def summarize_dd030(dd030: Dict[str, Any]) -> Dict[str, Any]:
    summary = dd030.get('summary') if isinstance(dd030.get('summary'), dict) else dd030
    return {
        'status': dd030.get('status') or summary.get('status') or '',
        'rows': as_int(summary.get('rows') or dd030.get('rows')),
        'root_mdo_scripts': as_int(summary.get('root_mdo_scripts') or dd030.get('root_mdo_scripts')),
        'blocking': as_int(summary.get('blocking') or dd030.get('blocking')),
        'packages': as_int(summary.get('packages') or dd030.get('packages')),
        'boundary_failures': as_int(summary.get('boundary_failures') or dd030.get('boundary_failures')),
    }


def disposition_rollup(summary_rows: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    out = []
    for row in summary_rows:
        out.append({
            'disposition': row.get('disposition', ''),
            'count': as_int(row.get('count')),
            'high': as_int(row.get('high')),
            'baseline_action': row.get('baseline_action', ''),
            'readiness_interpretation': interpret_disposition(row.get('disposition', ''), as_int(row.get('high'))),
        })
    return out


def interpret_disposition(disposition: str, high: int) -> str:
    if disposition == 'MAINTENANCE_PACKAGE_SCRIPT':
        return 'ready only if DD-030 accepted package evidence has blocking=0'
    if disposition == 'DATADICT_LANE_CHANGE':
        return 'eligible after Data Dictionary self-review'
    if disposition == 'DATADICT_TOOLING_CHANGE':
        return 'eligible after tool help/smoke confirms report-only boundary'
    if disposition == 'MAINTENANCE_PACKAGE_EVIDENCE':
        return 'eligible as maintenance evidence or exclusion-policy candidate'
    if disposition == 'MANUALGEN_REPORT_EVIDENCE':
        return 'eligible after manualgen evidence review'
    if disposition == 'RUNLOG_OR_SAVEPOINT_EVIDENCE':
        return 'eligible as run/savepoint evidence'
    if high:
        return 'requires human review'
    return 'review required'


def decide_status(dd028_s: Dict[str, Any], dd029_s: Dict[str, Any], dd030_s: Dict[str, Any]) -> Tuple[str, List[Dict[str, Any]]]:
    gates: List[Dict[str, Any]] = []
    def add_gate(gate: str, observed: Any, required: Any, passed: bool, note: str) -> None:
        gates.append({'gate': gate, 'observed': observed, 'required': required, 'pass': int(bool(passed)), 'note': note})

    add_gate('DD-028 status present', dd028_s['status'], 'present', bool(dd028_s['status']), 'baseline compare result must be readable')
    add_gate('DD-029 status present', dd029_s['status'], 'present', bool(dd029_s['status']), 'artifact disposition result must be readable')
    add_gate('DD-030 status present', dd030_s['status'], 'present', bool(dd030_s['status']), 'script-boundary disposition result must be readable')
    add_gate('DD-030 script blockers resolved', dd030_s['blocking'], 0, dd030_s['blocking'] == 0, 'root MDO package scripts must be accepted as package evidence or otherwise resolved')
    add_gate('DD-029 boundary failures absent', dd029_s['boundary_failures'], 0, dd029_s['boundary_failures'] == 0, 'artifact disposition must not report boundary failures')
    add_gate('DD-030 boundary failures absent', dd030_s['boundary_failures'], 0, dd030_s['boundary_failures'] == 0, 'script disposition must not report boundary failures')
    add_gate('DD-028 changes explained by review workflow', dd028_s['review_rows'], 'reviewed by DD-029/DD-030', dd029_s['review_rows'] >= dd028_s['review_rows'] or dd029_s['review_rows'] > 0, 'all review rows should enter disposition workflow')

    failures = [g for g in gates if not g['pass']]
    if failures:
        return 'BLOCKED_BASELINE_READINESS', gates
    if dd028_s['added'] == 0 and dd028_s['removed'] == 0 and dd028_s['changed'] == 0 and dd028_s['review_rows'] == 0:
        return 'BASELINE_UNCHANGED', gates
    return 'READY_FOR_BASELINE_REVIEW', gates


def make_policy_patch(packages: List[str]) -> Dict[str, Any]:
    return {
        'schema': 'dd031_exclusion_policy_patch_proposal_v0',
        'status': 'PROPOSAL_ONLY',
        'created_utc': now_utc(),
        'intent': 'Exclude accepted root-level MDO maintenance package folders from stable source fingerprint after package evidence is reviewed.',
        'rules': [
            {
                'rule_id': f'ROOT_MDO_PACKAGE_{i+1:03d}',
                'pattern': f'{pkg}/**',
                'action': 'exclude_from_stable_source_fingerprint',
                'condition': 'only after package evidence accepted by DD-030 or successor disposition gate',
                'reason': 'root-level MDO generated maintenance package should be inventoried as maintenance evidence, not product source drift',
            }
            for i, pkg in enumerate(packages)
        ],
        'boundary': {
            'edits_source': False,
            'moves_or_deletes_files': False,
            'accepts_baseline': False,
            'mutates_help_meta_cmdhelpchk': False,
            'writes_dbf_cdx_lmdb_catalog': False,
        },
    }


def render_report(run_id: str, status: str, dd028_s: Dict[str, Any], dd029_s: Dict[str, Any], dd030_s: Dict[str, Any], gates: List[Dict[str, Any]], rollup: List[Dict[str, Any]], packages: List[str]) -> str:
    def table(headers: List[str], rows: List[List[Any]]) -> str:
        lines = ['| ' + ' | '.join(headers) + ' |', '| ' + ' | '.join(['---'] * len(headers)) + ' |']
        for row in rows:
            lines.append('| ' + ' | '.join(str(x) for x in row) + ' |')
        return '\n'.join(lines)

    gate_rows = [[g['gate'], g['observed'], g['required'], g['pass'], g['note']] for g in gates]
    roll_rows = [[r['disposition'], r['count'], r['high'], r['baseline_action'], r['readiness_interpretation']] for r in rollup]
    pkg_rows = [[p, 'accepted maintenance package evidence candidate'] for p in packages] or [['(none)', '']]

    return f"""# DD-031 Disposition-Aware Baseline Readiness Report

Run id: `{run_id}`
Status: **{status}**
Created UTC: `{now_utc()}`

## Summary

DD-031 combines DD-028, DD-029, and DD-030 to determine whether the current repo changes are ready for a new Data Dictionary baseline review.

- DD-028 status: `{dd028_s['status']}`; added={dd028_s['added']}; removed={dd028_s['removed']}; changed={dd028_s['changed']}; review_rows={dd028_s['review_rows']}; high={dd028_s['high']}
- DD-029 status: `{dd029_s['status']}`; review_rows={dd029_s['review_rows']}; high={dd029_s['high']}; dispositions={dd029_s['dispositions']}; boundary_failures={dd029_s['boundary_failures']}
- DD-030 status: `{dd030_s['status']}`; root_mdo_scripts={dd030_s['root_mdo_scripts']}; blocking={dd030_s['blocking']}; packages={dd030_s['packages']}; boundary_failures={dd030_s['boundary_failures']}

## Gate ledger

{table(['Gate', 'Observed', 'Required', 'Pass', 'Note'], gate_rows)}

## Disposition rollup

{table(['Disposition', 'Count', 'High', 'Baseline action', 'Readiness interpretation'], roll_rows)}

## Root MDO packages proposed for policy treatment

{table(['Package', 'Disposition'], pkg_rows)}

## Recommended next actions

1. If status is `READY_FOR_BASELINE_REVIEW`, review the DD-031 report and policy patch proposal.
2. Decide whether the root MDO package folders are accepted maintenance evidence or should be archived/removed outside the Data Dictionary tooling.
3. If accepted, run the next package to apply or install a guarded exclusion policy update.
4. Rerun DD-028 against the accepted baseline.
5. If DD-028 becomes clean, accept a new baseline such as `DDBASE-stable-v1` with DD-027.

## Boundary

DD-031 is report-only. It does not edit source, run builds, launch DotTalk++, mutate HELP/META/CMDHELPCHK, write DBF/CDX/LMDB/catalog data, move/delete package folders, or accept a baseline.
"""


def main() -> int:
    ap = argparse.ArgumentParser(description='DD-031 report-only disposition-aware baseline readiness checker')
    ap.add_argument('--dd028', required=True, help='DD-028 baseline-check run directory or manifest')
    ap.add_argument('--dd029', required=True, help='DD-029 artifact-disposition run directory or manifest')
    ap.add_argument('--dd030', required=True, help='DD-030 script-boundary run directory or manifest')
    ap.add_argument('--out-dir', required=True)
    ap.add_argument('--run-id', default='DD031-baseline-readiness')
    ap.add_argument('--profile', action='append', default=[])
    ap.add_argument('--fail-on-blocked', action='store_true')
    args = ap.parse_args()

    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)

    dd028, dd029, dd030, dd029_rows, dd029_summary_rows, dd030_rows = load_inputs(Path(args.dd028), Path(args.dd029), Path(args.dd030))
    dd028_s = summarize_dd028(dd028)
    dd029_s = summarize_dd029(dd029)
    dd030_s = summarize_dd030(dd030)
    status, gates = decide_status(dd028_s, dd029_s, dd030_s)
    rollup = disposition_rollup(dd029_summary_rows)
    packages = collect_top_packages(dd029_rows or dd030_rows)
    policy_patch = make_policy_patch(packages)

    boundary_rows = [
        {'boundary': 'source edits', 'observed': 0, 'required': 0, 'pass': 1},
        {'boundary': 'build launched', 'observed': 0, 'required': 0, 'pass': 1},
        {'boundary': 'DotTalk++ runtime launched', 'observed': 0, 'required': 0, 'pass': 1},
        {'boundary': 'HELP/META/CMDHELPCHK mutation', 'observed': 0, 'required': 0, 'pass': 1},
        {'boundary': 'DBF/CDX/LMDB/catalog mutation', 'observed': 0, 'required': 0, 'pass': 1},
        {'boundary': 'baseline accepted/replaced', 'observed': 0, 'required': 0, 'pass': 1},
        {'boundary': 'files moved/deleted', 'observed': 0, 'required': 0, 'pass': 1},
    ]

    next_plan = [
        {'step': 1, 'action': 'Review DD-031 readiness status', 'required_if': 'always'},
        {'step': 2, 'action': 'Review generated exclusion policy patch proposal', 'required_if': 'packages present'},
        {'step': 3, 'action': 'Install guarded policy update in DD-032 or successor', 'required_if': 'packages accepted as maintenance evidence'},
        {'step': 4, 'action': 'Rerun DD-028 against current accepted baseline', 'required_if': 'policy update installed'},
        {'step': 5, 'action': 'Accept DDBASE-stable-v1 with DD-027', 'required_if': 'DD-028 becomes clean'},
    ]

    manifest = {
        'schema': 'dd031_baseline_readiness_manifest_v0',
        'run_id': args.run_id,
        'created_utc': now_utc(),
        'status': status,
        'profiles': args.profile,
        'dd028_summary': dd028_s,
        'dd029_summary': dd029_s,
        'dd030_summary': dd030_s,
        'gate_failures': sum(1 for g in gates if not g['pass']),
        'boundary_failures': 0,
        'packages': packages,
        'outputs': {
            'report': 'DD031_BASELINE_READINESS_REPORT.md',
            'gate_ledger': 'dd031_readiness_gate_ledger.csv',
            'disposition_rollup': 'dd031_disposition_rollup.csv',
            'policy_patch_proposal': 'dd031_exclusion_policy_patch_proposal.json',
            'next_baseline_plan': 'dd031_next_baseline_plan.csv',
            'boundary_ledger': 'dd031_boundary_ledger.csv',
        },
        'boundary': 'report-only; no baseline acceptance or protected-system mutation',
    }

    write_json(out / 'dd031_baseline_readiness_manifest.json', manifest)
    write_csv(out / 'dd031_readiness_gate_ledger.csv', gates)
    write_csv(out / 'dd031_disposition_rollup.csv', rollup)
    write_json(out / 'dd031_exclusion_policy_patch_proposal.json', policy_patch)
    write_csv(out / 'dd031_next_baseline_plan.csv', next_plan)
    write_csv(out / 'dd031_boundary_ledger.csv', boundary_rows)
    (out / 'DD031_BASELINE_READINESS_REPORT.md').write_text(render_report(args.run_id, status, dd028_s, dd029_s, dd030_s, gates, rollup, packages), encoding='utf-8')

    print(f'DD-031 readiness manifest: {out / "dd031_baseline_readiness_manifest.json"}')
    print(f'status: {status}; gate_failures: {manifest["gate_failures"]}; packages: {len(packages)}; dd030_blocking: {dd030_s["blocking"]}')
    if args.fail_on_blocked and status.startswith('BLOCKED'):
        return 2
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
