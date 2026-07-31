#!/usr/bin/env python3
"""
DD-026 DotTalk++ / x64base Data Dictionary review queue summarizer.

Reads DD-025 change classification output and produces a compact triage packet:
- lane counts
- severity counts
- gate counts
- top changed roots
- recommended next actions
- human-readable Markdown triage report

Report-only. Does not rescan source, launch DotTalk++, mutate HELP/META/CMDHELPCHK,
write DBFs, or promote dictionary facts.

Python: target 3.12+
"""
from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding='utf-8'))


def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open('r', newline='', encoding='utf-8') as f:
        return [dict(row) for row in csv.DictReader(f)]


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, '') for field in fields})


def resolve_dd025_dir(path: Path) -> Path:
    if path.is_dir():
        return path
    if path.is_file() and path.name == 'dd025_change_classification_manifest.json':
        return path.parent
    raise FileNotFoundError(f'could not resolve DD-025 run directory from {path}')


def split_gates(value: str) -> list[str]:
    if not value:
        return []
    parts = []
    for chunk in value.replace(',', ';').split(';'):
        token = chunk.strip()
        if token:
            parts.append(token)
    return parts


def root_for_path(path: str, depth: int = 2) -> str:
    clean = path.replace('\\', '/').strip('/')
    if not clean:
        return '(blank)'
    parts = [p for p in clean.split('/') if p]
    if not parts:
        return '(blank)'
    return '/'.join(parts[:max(1, depth)])


def severity_rank(value: str) -> int:
    return {'HIGH': 3, 'MEDIUM': 2, 'LOW': 1}.get((value or '').upper(), 0)


def status_from_counts(total: int, high: int, medium: int) -> str:
    if high:
        return 'BLOCKED_REVIEW'
    if total:
        return 'REVIEW'
    return 'PASS'


def action_for_gate(gate: str) -> str:
    gate = gate.strip()
    mapping = {
        'SOURCE_CONTRACT_RESCAN_REQUIRED': 'Rerun source-contract and @dottalk.usage harvest; compare command registry and usage blocks.',
        'HELP_COVERAGE_CHECK_REQUIRED': 'Run HELP/CMDHELPCHK report-only checks before promotion.',
        'RUNTIME_PROOF_REVIEW_REQUIRED': 'Capture or review runtime transcript proof for affected commands or physical behavior.',
        'PHYSICAL_DICTIONARY_RESCAN_REQUIRED': 'Rerun physical DBF/header/index/memo extraction and reconciliation.',
        'RELATION_TUPLE_RESCAN_REQUIRED': 'Rerun workspace/relation/tuple dictionary source map and proof planning.',
        'TRANSCRIPT_PROOF_REVIEW_REQUIRED': 'Run or review transcript parser output for affected runtime surface.',
        'METAFACT_RESCAN_REQUIRED': 'Rerun MetaFact/source-contract bridge extraction.',
        'CATALOG_STAGING_REVIEW_REQUIRED': 'Review staging import plan and promotion queue before any catalog write.',
        'XEXPR_RULE_RESCAN_REQUIRED': 'Rerun rules/constraints/xexpr link map and function catalog seed.',
        'BUILD_PROFILE_REVIEW_REQUIRED': 'Review CMake/profile boundary and engine/professional/educational split.',
        'OPTIONAL_OVERLAY_BOUNDARY_REVIEW_REQUIRED': 'Confirm whether changed artifact belongs in core, professional, or educational overlay.',
        'DATADICT_SELF_REVIEW_REQUIRED': 'Review Data Dictionary lane changes separately from product source drift.',
        'MANUALGEN_REVIEW_REQUIRED': 'Review manualgen impact and publication gate before manual replacement.',
        'DOC_REVIEW_REQUIRED': 'Review documentation changes for dictionary/HELP/manual links.',
        'SCRIPT_BOUNDARY_REVIEW_REQUIRED': 'Classify script role, allowed mutation class, and dependency links.',
        'DD_SCRIPT_RESCAN_REQUIRED': 'Rerun script registry inventory and boundary matrix.',
        'SCHEMA_RESCAN_REQUIRED': 'Rerun declared schema extraction.',
        'RULE_BINDING_REVIEW_REQUIRED': 'Review rule bindings and field constraint mapping.',
        'CONTRACT_REVIEW_REQUIRED': 'Review changed JSON/contract artifact and update schemas if needed.',
        'TOOL_REVIEW_REQUIRED': 'Run tool help/smoke and review report-only/mutation boundary.',
        'BINDING_SMOKE_REQUIRED': 'Rerun pydottalk or relevant binding smoke test.',
        'HUMAN_TRIAGE_REQUIRED': 'Human review required; no automatic promotion.'
    }
    return mapping.get(gate, 'Review gate and assign a lane-specific follow-up action.')


def build_markdown(manifest: dict[str, Any], counts: dict[str, Any], lane_rows: list[dict[str, Any]], severity_rows: list[dict[str, Any]], gate_rows: list[dict[str, Any]], root_rows: list[dict[str, Any]], action_rows: list[dict[str, Any]], sample_rows: list[dict[str, Any]]) -> str:
    lines: list[str] = []
    lines.append('# DD-026 Review Queue Triage Report')
    lines.append('')
    lines.append(f"Run id: `{manifest.get('run_id')}`")
    lines.append(f"Status: **{manifest.get('status')}**")
    lines.append(f"Created UTC: `{manifest.get('created_utc')}`")
    lines.append('')
    lines.append('## Summary')
    lines.append('')
    lines.append(f"- Review rows: {counts.get('review_rows', 0)}")
    lines.append(f"- HIGH severity: {counts.get('high_severity_rows', 0)}")
    lines.append(f"- MEDIUM severity: {counts.get('medium_severity_rows', 0)}")
    lines.append(f"- LOW severity: {counts.get('low_severity_rows', 0)}")
    lines.append(f"- Review lanes: {counts.get('review_lanes', 0)}")
    lines.append(f"- Gates observed: {counts.get('gate_count', 0)}")
    lines.append('')
    lines.append('## Severity counts')
    lines.append('')
    lines.append('| Severity | Count |')
    lines.append('|---|---:|')
    for row in severity_rows:
        lines.append(f"| {row.get('severity','')} | {row.get('count','')} |")
    if not severity_rows:
        lines.append('| none | 0 |')
    lines.append('')
    lines.append('## Top review lanes')
    lines.append('')
    lines.append('| Lane | Count | High | Required disposition |')
    lines.append('|---|---:|---:|---|')
    for row in lane_rows[:20]:
        lines.append(f"| {row.get('review_lane','')} | {row.get('count','')} | {row.get('high_count','')} | {row.get('disposition','')} |")
    if not lane_rows:
        lines.append('| none | 0 | 0 | PASS |')
    lines.append('')
    lines.append('## Top gates')
    lines.append('')
    lines.append('| Gate | Count | Recommended action |')
    lines.append('|---|---:|---|')
    for row in gate_rows[:25]:
        lines.append(f"| {row.get('gate','')} | {row.get('count','')} | {row.get('recommended_action','')} |")
    if not gate_rows:
        lines.append('| none | 0 | No action required. |')
    lines.append('')
    lines.append('## Top changed roots')
    lines.append('')
    lines.append('| Root | Count | High | Lanes |')
    lines.append('|---|---:|---:|---|')
    for row in root_rows[:25]:
        lines.append(f"| {row.get('root','')} | {row.get('count','')} | {row.get('high_count','')} | {row.get('lanes','')} |")
    if not root_rows:
        lines.append('| none | 0 | 0 | none |')
    lines.append('')
    lines.append('## Recommended next actions')
    lines.append('')
    lines.append('| Priority | Action | Reason |')
    lines.append('|---:|---|---|')
    for row in action_rows[:20]:
        lines.append(f"| {row.get('priority','')} | {row.get('action','')} | {row.get('reason','')} |")
    if not action_rows:
        lines.append('| 1 | No action required | Review queue is empty. |')
    lines.append('')
    lines.append('## Sample review rows')
    lines.append('')
    lines.append('| Severity | Lane | Change | Path | Gates |')
    lines.append('|---|---|---|---|---|')
    for row in sample_rows[:30]:
        lines.append(f"| {row.get('severity','')} | {row.get('review_lane','')} | {row.get('change_kind','')} | `{row.get('path','')}` | {row.get('required_gates','')} |")
    if not sample_rows:
        lines.append('| none | none | none | none | none |')
    lines.append('')
    lines.append('## Boundary')
    lines.append('')
    lines.append('DD-026 is report-only. It does not edit source, launch DotTalk++, mutate HELP/META/CMDHELPCHK, write DBF/CDX/LMDB/catalog data, or promote dictionary facts.')
    lines.append('')
    return '\n'.join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description='DD-026 report-only review queue summarizer and triage report builder')
    parser.add_argument('--dd025', required=True, help='DD-025 classification run directory or manifest path')
    parser.add_argument('--out-dir', required=True, help='Output directory for DD-026 artifacts')
    parser.add_argument('--run-id', default=None, help='Stable DD-026 run id')
    parser.add_argument('--profile', action='append', default=[], help='Profile scope label; may be repeated')
    parser.add_argument('--top', type=int, default=25, help='Maximum rows to include in top/root/report tables')
    parser.add_argument('--fail-on-blocked', action='store_true', help='Exit nonzero if status is BLOCKED_REVIEW')
    args = parser.parse_args()

    dd025_dir = resolve_dd025_dir(Path(args.dd025).resolve())
    dd025_manifest_path = dd025_dir / 'dd025_change_classification_manifest.json'
    dd025_manifest = read_json(dd025_manifest_path) if dd025_manifest_path.exists() else {}
    queue = read_csv(dd025_dir / 'dd025_classified_review_queue.csv')

    lane_counter: Counter[str] = Counter()
    lane_high: Counter[str] = Counter()
    severity_counter: Counter[str] = Counter()
    gate_counter: Counter[str] = Counter()
    root_counter: Counter[str] = Counter()
    root_high: Counter[str] = Counter()
    root_lanes: dict[str, set[str]] = defaultdict(set)
    class_counter: Counter[str] = Counter()
    disposition_counter: Counter[str] = Counter()

    for row in queue:
        lane = row.get('review_lane') or 'unclassified_surface'
        severity = (row.get('severity') or 'UNKNOWN').upper()
        root = root_for_path(row.get('path', ''), depth=2)
        lane_counter[lane] += 1
        severity_counter[severity] += 1
        class_counter[row.get('change_class') or 'unknown'] += 1
        disposition_counter[row.get('promotion_disposition') or 'unknown'] += 1
        root_counter[root] += 1
        root_lanes[root].add(lane)
        if severity == 'HIGH':
            lane_high[lane] += 1
            root_high[root] += 1
        for gate in split_gates(row.get('required_gates', '')):
            gate_counter[gate] += 1

    lane_rows = []
    for lane, count in lane_counter.most_common():
        high = lane_high.get(lane, 0)
        lane_rows.append({
            'review_lane': lane,
            'count': count,
            'high_count': high,
            'disposition': 'BLOCKED_REVIEW' if high else 'REVIEW',
        })

    severity_rows = [{'severity': sev, 'count': count} for sev, count in sorted(severity_counter.items(), key=lambda kv: (-severity_rank(kv[0]), kv[0]))]
    gate_rows = [{'gate': gate, 'count': count, 'recommended_action': action_for_gate(gate)} for gate, count in gate_counter.most_common()]
    root_rows = []
    for root, count in root_counter.most_common():
        lanes = ', '.join(sorted(root_lanes[root]))
        root_rows.append({'root': root, 'count': count, 'high_count': root_high.get(root, 0), 'lanes': lanes})
    class_rows = [{'change_class': name, 'count': count} for name, count in class_counter.most_common()]
    disposition_rows = [{'promotion_disposition': name, 'count': count} for name, count in disposition_counter.most_common()]

    action_rows: list[dict[str, Any]] = []
    priority = 1
    for gate, count in gate_counter.most_common(20):
        action_rows.append({'priority': priority, 'gate': gate, 'count': count, 'action': action_for_gate(gate), 'reason': f'{count} review rows require {gate}'})
        priority += 1
    if not action_rows:
        action_rows.append({'priority': 1, 'gate': 'NONE', 'count': 0, 'action': 'No action required', 'reason': 'Review queue is empty.'})

    high = severity_counter.get('HIGH', 0)
    medium = severity_counter.get('MEDIUM', 0)
    status = status_from_counts(len(queue), high, medium)

    # Samples: high first, then medium, then low, preserving deterministic path order within rank.
    sample_rows = sorted(queue, key=lambda r: (-severity_rank(r.get('severity','')), r.get('review_lane',''), r.get('path','')))[:max(1, args.top)]

    out_dir = Path(args.out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    write_csv(out_dir / 'dd026_lane_triage.csv', lane_rows, ['review_lane','count','high_count','disposition'])
    write_csv(out_dir / 'dd026_severity_triage.csv', severity_rows, ['severity','count'])
    write_csv(out_dir / 'dd026_gate_triage.csv', gate_rows, ['gate','count','recommended_action'])
    write_csv(out_dir / 'dd026_top_roots.csv', root_rows, ['root','count','high_count','lanes'])
    write_csv(out_dir / 'dd026_change_class_triage.csv', class_rows, ['change_class','count'])
    write_csv(out_dir / 'dd026_promotion_disposition_triage.csv', disposition_rows, ['promotion_disposition','count'])
    write_csv(out_dir / 'dd026_recommended_next_actions.csv', action_rows, ['priority','gate','count','action','reason'])
    sample_fields = ['review_id','change_kind','path','object_kind','change_class','review_lane','severity','required_gates','recommended_action','promotion_disposition']
    write_csv(out_dir / 'dd026_sample_review_rows.csv', sample_rows, sample_fields)

    run_id = args.run_id or datetime.now(timezone.utc).strftime('DD026-TRIAGE-%Y%m%dT%H%M%SZ')
    counts = {
        'review_rows': len(queue),
        'high_severity_rows': high,
        'medium_severity_rows': medium,
        'low_severity_rows': severity_counter.get('LOW', 0),
        'review_lanes': len(lane_counter),
        'gate_count': len(gate_counter),
        'root_count': len(root_counter),
        'change_class_count': len(class_counter),
    }
    manifest = {
        'schema_version': 'dd026_review_queue_triage_v0',
        'run_id': run_id,
        'created_utc': datetime.now(timezone.utc).isoformat(),
        'status': status,
        'boundary': 'REPORT_ONLY_PROMOTION_BLOCKED',
        'profile_scope': args.profile,
        'dd025_manifest': str(dd025_manifest_path),
        'dd025_run_id': dd025_manifest.get('run_id'),
        'counts': counts,
        'outputs': {
            'triage_report_md': str(out_dir / 'DD026_TRIAGE_REPORT.md'),
            'lane_triage_csv': str(out_dir / 'dd026_lane_triage.csv'),
            'severity_triage_csv': str(out_dir / 'dd026_severity_triage.csv'),
            'gate_triage_csv': str(out_dir / 'dd026_gate_triage.csv'),
            'top_roots_csv': str(out_dir / 'dd026_top_roots.csv'),
            'recommended_next_actions_csv': str(out_dir / 'dd026_recommended_next_actions.csv'),
            'sample_review_rows_csv': str(out_dir / 'dd026_sample_review_rows.csv'),
        },
        'next_action': 'Use DD-026 triage report to choose lane-specific rescans and proof steps; do not promote without explicit authorization.',
    }
    write_json(out_dir / 'dd026_triage_manifest.json', manifest)
    report = build_markdown(manifest, counts, lane_rows[:args.top], severity_rows, gate_rows[:args.top], root_rows[:args.top], action_rows[:args.top], sample_rows[:args.top])
    (out_dir / 'DD026_TRIAGE_REPORT.md').write_text(report, encoding='utf-8')

    print(f'DD-026 triage manifest: {out_dir / "dd026_triage_manifest.json"}')
    print(f'status: {status}; review_rows: {len(queue)}; high: {high}; lanes: {len(lane_counter)}; gates: {len(gate_counter)}')
    if status == 'BLOCKED_REVIEW' and args.fail_on_blocked:
        return 2
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
