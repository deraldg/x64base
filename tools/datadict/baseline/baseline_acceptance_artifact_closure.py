#!/usr/bin/env python3
"""DD-036 report-only baseline acceptance proof artifact closure.

Classifies DD-028/DD-034 diff rows that appear immediately after a baseline
acceptance. It is intentionally report-only: no baseline is accepted, no files
are moved, and no protected-system state is mutated.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def read_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def locate_dd023_diff_csv(input_path: Path) -> Path:
    """Accept DD-034 directory, DD-028 directory, diff directory, or CSV path."""
    if input_path.is_file():
        if input_path.name.lower().endswith('.csv'):
            return input_path
        # manifest path: use parent and search below it
        start = input_path.parent
    else:
        start = input_path
    candidates = [
        start / 'dd028_baseline_check' / 'diff' / 'dd023_file_diff.csv',
        start / 'diff' / 'dd023_file_diff.csv',
        start / 'dd023_file_diff.csv',
    ]
    for c in candidates:
        if c.exists():
            return c
    found = list(start.rglob('dd023_file_diff.csv')) if start.exists() else []
    if found:
        # Prefer nested DD-028 baseline_check if present.
        found.sort(key=lambda p: (0 if 'dd028_baseline_check' in str(p).replace('\\','/') else 1, len(str(p))))
        return found[0]
    raise FileNotFoundError(f"Could not find dd023_file_diff.csv under {input_path}")


def read_csv_dicts(path: Path) -> List[dict]:
    with path.open('r', encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))


def write_csv_dicts(path: Path, rows: List[dict], fieldnames: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, '') for k in fieldnames})


def norm_path(p: str) -> str:
    return (p or '').replace('\\', '/').strip()


@dataclass
class Disposition:
    change_kind: str
    path: str
    object_kind: str
    disposition: str
    artifact_class: str
    accepted_by_flag: int
    blocking: int
    reason: str


def classify(path: str, baseline_id: str, accept: bool) -> Tuple[str, str, str]:
    p = norm_path(path)
    baseline_prefix = f"docs/datadict/baselines/{baseline_id}/"
    if p.startswith(baseline_prefix):
        return (
            'BASELINE_ACCEPTANCE_PACKET',
            'baseline_acceptance_artifact',
            'baseline packet created by DD-027 acceptance for the same baseline id',
        )
    # Clean A/B proof artifacts created by the baseline acceptance sequence.
    stable_pat = re.compile(r"^docs/datadict/review_queue/(DD025|DD026)-stable-v\d+-A-to-B/")
    if stable_pat.match(p):
        return (
            'BASELINE_STABLE_PROOF_PACKET',
            'baseline_proof_artifact',
            'clean stable A/B classification or triage proof for baseline acceptance',
        )
    # Also allow a more explicit baseline id if used in names.
    version_match = re.search(r"stable-v(\d+)", baseline_id)
    if version_match:
        v = version_match.group(1)
        if p.startswith(f"docs/datadict/review_queue/DD025-stable-v{v}-A-to-B/") or p.startswith(f"docs/datadict/review_queue/DD026-stable-v{v}-A-to-B/"):
            return (
                'BASELINE_STABLE_PROOF_PACKET',
                'baseline_proof_artifact',
                'clean stable A/B classification or triage proof for this baseline version',
            )
    return ('NON_ACCEPTANCE_ARTIFACT', 'non_acceptance_artifact', 'not recognized as baseline acceptance/proof artifact')


def load_summary_counts(dd_input: Path) -> Dict[str, int]:
    """Best-effort extraction of DD-034/DD-028 summary counts."""
    start = dd_input.parent if dd_input.is_file() else dd_input
    manifests = [
        start / 'dd034_daily_redoc_status_manifest.json',
        start / 'dd028_baseline_compare_manifest.json',
        start / 'dd028_baseline_check' / 'dd028_baseline_compare_manifest.json',
    ]
    for m in manifests:
        if m.exists():
            data = read_json(m)
            out = {}
            for key in ['added', 'removed', 'changed', 'review_rows', 'high', 'self_artifacts', 'non_self']:
                val = data.get(key, data.get('summary', {}).get(key, 0))
                try: out[key] = int(val)
                except Exception: out[key] = 0
            return out
    return {}


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description='DD-036 report-only baseline acceptance proof artifact closure')
    ap.add_argument('--dd034', required=True, help='DD-034/DD-028 run directory, manifest, or dd023_file_diff.csv')
    ap.add_argument('--out-dir', required=True)
    ap.add_argument('--run-id', default='DD036-baseline-acceptance-artifact-closure')
    ap.add_argument('--baseline-id', required=True)
    ap.add_argument('--profile', action='append', default=[])
    ap.add_argument('--accept-acceptance-artifacts', action='store_true', help='Accept baseline/proof artifacts for this report; still no mutation')
    ap.add_argument('--fail-on-blocked', action='store_true')
    args = ap.parse_args(argv)

    inp = Path(args.dd034)
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)

    diff_csv = locate_dd023_diff_csv(inp)
    rows = read_csv_dicts(diff_csv)
    dispositions: List[dict] = []
    counts: Dict[str, int] = {}
    blocking = 0
    acceptance_artifacts = 0
    non_acceptance = 0

    for r in rows:
        p = norm_path(r.get('path', ''))
        disp, cls, reason = classify(p, args.baseline_id, args.accept_acceptance_artifacts)
        is_acceptance = disp in {'BASELINE_ACCEPTANCE_PACKET', 'BASELINE_STABLE_PROOF_PACKET'}
        if is_acceptance:
            acceptance_artifacts += 1
        else:
            non_acceptance += 1
        row_blocking = 0
        if not is_acceptance:
            row_blocking = 1
        elif not args.accept_acceptance_artifacts:
            row_blocking = 1
        if row_blocking:
            blocking += 1
        counts[disp] = counts.get(disp, 0) + 1
        dispositions.append(asdict(Disposition(
            change_kind=r.get('change_kind', r.get('change', '')),
            path=p,
            object_kind=r.get('object_kind', ''),
            disposition=disp,
            artifact_class=cls,
            accepted_by_flag=1 if (is_acceptance and args.accept_acceptance_artifacts) else 0,
            blocking=row_blocking,
            reason=reason,
        )))

    if non_acceptance and blocking:
        status = 'BLOCKED_NON_ACCEPTANCE_ARTIFACT_REVIEW'
    elif blocking:
        status = 'BASELINE_ACCEPTANCE_ARTIFACT_CLOSURE_REVIEW'
    else:
        status = 'BASELINE_ACCEPTANCE_ARTIFACT_CLOSURE_ACCEPTED'

    summary_counts = load_summary_counts(inp)
    manifest = {
        'schema': 'dd036_baseline_acceptance_artifact_closure_v0',
        'run_id': args.run_id,
        'created_utc': utc_now(),
        'status': status,
        'baseline_id': args.baseline_id,
        'profiles': args.profile,
        'input': str(inp),
        'diff_csv': str(diff_csv),
        'rows': len(rows),
        'acceptance_artifacts': acceptance_artifacts,
        'non_acceptance_artifacts': non_acceptance,
        'blocking': blocking,
        'acceptance_artifacts_accepted': bool(args.accept_acceptance_artifacts),
        'disposition_counts': counts,
        'source_summary_counts': summary_counts,
        'boundary': {
            'source_edits': 0,
            'build_run': 0,
            'runtime_launch': 0,
            'help_meta_cmdhelpchk_mutation': 0,
            'dbf_cdx_lmdb_catalog_mutation': 0,
            'baseline_replacement': 0,
            'file_moves_or_deletes': 0,
        },
    }
    (out/'dd036_baseline_acceptance_artifact_closure_manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    write_csv_dicts(out/'dd036_acceptance_artifact_rows.csv', dispositions, [
        'change_kind','path','object_kind','disposition','artifact_class','accepted_by_flag','blocking','reason'
    ])
    summary_rows = []
    for disp, count in sorted(counts.items()):
        high_block = sum(1 for d in dispositions if d['disposition'] == disp and d['blocking'])
        summary_rows.append({'disposition': disp, 'count': count, 'blocking': high_block})
    write_csv_dicts(out/'dd036_disposition_summary.csv', summary_rows, ['disposition','count','blocking'])
    boundary_rows = [{'boundary': k, 'observed': v, 'required': 0, 'pass': 1 if v == 0 else 0} for k, v in manifest['boundary'].items()]
    write_csv_dicts(out/'dd036_boundary_ledger.csv', boundary_rows, ['boundary','observed','required','pass'])

    report = []
    report.append('# DD-036 Baseline Acceptance Proof Artifact Closure Report\n')
    report.append(f"Run id: `{args.run_id}`\n")
    report.append(f"Status: **{status}**\n")
    report.append(f"Created UTC: `{manifest['created_utc']}`\n")
    report.append(f"Baseline id: `{args.baseline_id}`\n")
    report.append('\n## Summary\n')
    report.append(f"- Rows examined: {len(rows)}\n")
    report.append(f"- Acceptance/proof artifacts: {acceptance_artifacts}\n")
    report.append(f"- Non-acceptance artifacts: {non_acceptance}\n")
    report.append(f"- Blocking rows: {blocking}\n")
    report.append(f"- Accepted by flag: {1 if args.accept_acceptance_artifacts else 0}\n")
    report.append('\n## Dispositions\n\n')
    report.append('| Disposition | Count | Blocking |\n|---|---:|---:|\n')
    for r in summary_rows:
        report.append(f"| {r['disposition']} | {r['count']} | {r['blocking']} |\n")
    report.append('\n## Sample rows\n\n')
    report.append('| Change | Disposition | Blocking | Path |\n|---|---|---:|---|\n')
    for d in dispositions[:20]:
        report.append(f"| {d['change_kind']} | {d['disposition']} | {d['blocking']} | `{d['path']}` |\n")
    report.append('\n## Boundary\n\n')
    report.append('DD-036 is report-only. It does not accept or replace a baseline, edit source, run builds, launch DotTalk++, mutate HELP/META/CMDHELPCHK, write DBF/CDX/LMDB/catalog data, or move/delete files.\n')
    (out/'DD036_BASELINE_ACCEPTANCE_ARTIFACT_CLOSURE_REPORT.md').write_text(''.join(report), encoding='utf-8')

    print(f"DD-036 acceptance-artifact closure manifest: {out/'dd036_baseline_acceptance_artifact_closure_manifest.json'}")
    print(f"status: {status}; rows: {len(rows)}; acceptance_artifacts: {acceptance_artifacts}; non_acceptance: {non_acceptance}; blocking: {blocking}")
    if args.fail_on_blocked and blocking:
        return 2
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
