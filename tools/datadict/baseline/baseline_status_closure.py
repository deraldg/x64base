#!/usr/bin/env python3
"""DD-037 report-only status command closure integration.

Consumes a DD-034 daily status packet and optional DD-036 baseline acceptance
artifact closure packet. Emits a final operator-facing status.
"""
from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


def load_json(path: Path) -> Dict[str, Any]:
    with path.open('r', encoding='utf-8') as f:
        return json.load(f)


def find_file(root: Path, name: str) -> Optional[Path]:
    if root.is_file() and root.name == name:
        return root
    if root.is_dir():
        direct = root / name
        if direct.exists():
            return direct
        matches = list(root.rglob(name))
        if matches:
            return matches[0]
    return None


def load_dd034_summary(dd034: Path) -> Dict[str, Any]:
    manifest_path = find_file(dd034, 'dd034_daily_redoc_status_manifest.json')
    if not manifest_path:
        raise FileNotFoundError(f'Cannot find dd034_daily_redoc_status_manifest.json under {dd034}')
    m = load_json(manifest_path)
    # Support both flat and nested field styles.
    summary = {
        'manifest_path': str(manifest_path),
        'status': m.get('status', ''),
        'added': int(m.get('added', m.get('added_count', 0)) or 0),
        'removed': int(m.get('removed', m.get('removed_count', 0)) or 0),
        'changed': int(m.get('changed', m.get('changed_count', 0)) or 0),
        'review_rows': int(m.get('review_rows', 0) or 0),
        'high': int(m.get('high', m.get('high_rows', 0)) or 0),
        'self_artifacts': int(m.get('self_artifacts', 0) or 0),
        'non_self': int(m.get('non_self', m.get('non_self_artifacts', 0)) or 0),
    }
    return summary


def load_dd036_summary(dd036: Optional[Path]) -> Dict[str, Any]:
    if not dd036:
        return {'present': False, 'status': '', 'rows': 0, 'acceptance_artifacts': 0, 'non_acceptance': 0, 'blocking': 0}
    manifest_path = find_file(dd036, 'dd036_baseline_acceptance_artifact_closure_manifest.json')
    if not manifest_path:
        raise FileNotFoundError(f'Cannot find dd036_baseline_acceptance_artifact_closure_manifest.json under {dd036}')
    m = load_json(manifest_path)
    return {
        'present': True,
        'manifest_path': str(manifest_path),
        'status': m.get('status', ''),
        'rows': int(m.get('rows', 0) or 0),
        'acceptance_artifacts': int(m.get('acceptance_artifacts', 0) or 0),
        'non_acceptance': int(m.get('non_acceptance', 0) or 0),
        'blocking': int(m.get('blocking', 0) or 0),
    }


def decide_status(dd034: Dict[str, Any], dd036: Dict[str, Any]) -> str:
    if dd034['added'] == 0 and dd034['removed'] == 0 and dd034['changed'] == 0 and dd034['review_rows'] == 0:
        return 'PASS_NO_SOURCE_DRIFT'
    if dd036.get('present'):
        if (dd036.get('status') == 'BASELINE_ACCEPTANCE_ARTIFACT_CLOSURE_ACCEPTED'
                and dd036.get('blocking') == 0
                and dd036.get('non_acceptance') == 0
                and dd036.get('acceptance_artifacts') == dd034.get('review_rows')):
            return 'PASS_WITH_ACCEPTED_BASELINE_ARTIFACTS'
        if (dd036.get('acceptance_artifacts') == dd034.get('review_rows')
                and dd036.get('non_acceptance') == 0):
            return 'REVIEW_BASELINE_ARTIFACTS_UNACCEPTED'
    return 'REVIEW_REAL_CHANGE'


def write_csv(path: Path, rows: List[Dict[str, Any]], fields: List[str]) -> None:
    with path.open('w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, '') for k in fields})


def main() -> int:
    ap = argparse.ArgumentParser(description='DD-037 report-only status closure integration')
    ap.add_argument('--dd034', required=True, help='DD-034 daily status run directory or manifest')
    ap.add_argument('--dd036', required=False, help='DD-036 accepted/review closure directory or manifest')
    ap.add_argument('--out-dir', required=True)
    ap.add_argument('--run-id', default='DD037-status-closure')
    ap.add_argument('--baseline-id', required=True)
    ap.add_argument('--profile', action='append', default=[])
    ap.add_argument('--fail-on-review', action='store_true')
    ap.add_argument('--fail-on-blocked', action='store_true')
    args = ap.parse_args()

    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    dd034 = load_dd034_summary(Path(args.dd034))
    dd036 = load_dd036_summary(Path(args.dd036)) if args.dd036 else load_dd036_summary(None)
    status = decide_status(dd034, dd036)
    created = datetime.now(timezone.utc).isoformat()

    manifest = {
        'run_id': args.run_id,
        'created_utc': created,
        'status': status,
        'baseline_id': args.baseline_id,
        'profiles': args.profile,
        'dd034': dd034,
        'dd036': dd036,
        'review_rows': dd034['review_rows'],
        'accepted_closure_rows': dd036.get('acceptance_artifacts', 0) if dd036.get('status') == 'BASELINE_ACCEPTANCE_ARTIFACT_CLOSURE_ACCEPTED' else 0,
        'unexplained_rows': 0 if status in ('PASS_NO_SOURCE_DRIFT', 'PASS_WITH_ACCEPTED_BASELINE_ARTIFACTS') else dd034['review_rows'] - dd036.get('acceptance_artifacts', 0),
        'boundary': {
            'report_only': True,
            'source_edits': 0,
            'build': 0,
            'runtime_launch': 0,
            'help_meta_cmdhelpchk_mutation': 0,
            'dbf_cdx_lmdb_catalog_mutation': 0,
            'baseline_replacement': 0,
            'file_moves_or_deletes': 0,
        }
    }
    (out / 'dd037_status_closure_manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    write_csv(out / 'dd037_summary.csv', [{
        'run_id': args.run_id,
        'status': status,
        'baseline_id': args.baseline_id,
        'review_rows': manifest['review_rows'],
        'accepted_closure_rows': manifest['accepted_closure_rows'],
        'unexplained_rows': manifest['unexplained_rows'],
    }], ['run_id','status','baseline_id','review_rows','accepted_closure_rows','unexplained_rows'])
    write_csv(out / 'dd037_boundary_ledger.csv', [
        {'boundary': 'source edits', 'observed': 0, 'required': 0, 'pass': 1},
        {'boundary': 'build', 'observed': 0, 'required': 0, 'pass': 1},
        {'boundary': 'runtime launch', 'observed': 0, 'required': 0, 'pass': 1},
        {'boundary': 'HELP/META/CMDHELPCHK mutation', 'observed': 0, 'required': 0, 'pass': 1},
        {'boundary': 'DBF/CDX/LMDB/catalog mutation', 'observed': 0, 'required': 0, 'pass': 1},
        {'boundary': 'baseline replacement', 'observed': 0, 'required': 0, 'pass': 1},
        {'boundary': 'file moves/deletes', 'observed': 0, 'required': 0, 'pass': 1},
    ], ['boundary','observed','required','pass'])
    report = f"""# DD-037 Status Closure Report

Run id: `{args.run_id}`
Status: **{status}**
Created UTC: `{created}`
Baseline: `{args.baseline_id}`

## Summary

- DD-034 review rows: {dd034['review_rows']}
- DD-034 added/removed/changed: {dd034['added']} / {dd034['removed']} / {dd034['changed']}
- DD-036 present: {dd036.get('present')}
- DD-036 status: `{dd036.get('status','')}`
- DD-036 acceptance artifacts: {dd036.get('acceptance_artifacts',0)}
- DD-036 non-acceptance rows: {dd036.get('non_acceptance',0)}
- Unexplained rows: {manifest['unexplained_rows']}

## Interpretation

"""
    if status == 'PASS_WITH_ACCEPTED_BASELINE_ARTIFACTS':
        report += 'The DD-034 review rows are fully explained by DD-036 accepted baseline acceptance/proof artifacts. No product source drift is indicated.\n'
    elif status == 'PASS_NO_SOURCE_DRIFT':
        report += 'DD-034 found no source drift relative to the accepted baseline.\n'
    elif status == 'REVIEW_BASELINE_ARTIFACTS_UNACCEPTED':
        report += 'DD-034 rows appear to be baseline acceptance/proof artifacts, but DD-036 has not accepted them.\n'
    else:
        report += 'DD-034 reported rows not fully explained by DD-036 accepted closure. Human review remains required.\n'
    report += """
## Boundary

DD-037 is report-only. It does not accept or replace a baseline, edit source, run builds, launch DotTalk++, mutate HELP/META/CMDHELPCHK, write DBF/CDX/LMDB/catalog data, or move/delete files.
"""
    (out / 'DD037_STATUS_CLOSURE_REPORT.md').write_text(report, encoding='utf-8')
    print(f"DD-037 status closure manifest: {out / 'dd037_status_closure_manifest.json'}")
    print(f"status: {status}; review_rows: {manifest['review_rows']}; accepted_closure_rows: {manifest['accepted_closure_rows']}; unexplained_rows: {manifest['unexplained_rows']}")
    if args.fail_on_review and status not in ('PASS_NO_SOURCE_DRIFT','PASS_WITH_ACCEPTED_BASELINE_ARTIFACTS'):
        return 2
    if args.fail_on_blocked and status == 'REVIEW_REAL_CHANGE':
        return 2
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
