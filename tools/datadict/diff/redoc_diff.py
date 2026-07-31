#!/usr/bin/env python3
"""
DD-023 DotTalk++ / x64base data-dictionary redocumentation diff skeleton.

Compares two DD-022 run directories or manifests. Report-only by default.
It does not scan the repo, launch DotTalk++, edit source, regenerate HELP, or
promote catalog data.

Python: target 3.12+
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def load_json(path: Path) -> Any:
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


def resolve_manifest(path: Path) -> Path:
    if path.is_file():
        return path
    candidate = path / 'dd022_redoc_run_manifest.json'
    if candidate.exists():
        return candidate
    matches = list(path.rglob('dd022_redoc_run_manifest.json'))
    if len(matches) == 1:
        return matches[0]
    raise FileNotFoundError(f'could not resolve DD-022 manifest from {path}')


def load_source_inventory(manifest_path: Path, manifest: dict[str, Any]) -> tuple[dict[str, dict[str, Any]], list[str]]:
    warnings: list[str] = []
    artifacts = manifest.get('artifacts', []) or []
    csv_path: Path | None = None
    for art in artifacts:
        if art.get('kind') == 'source_inventory' and art.get('path'):
            p = Path(str(art['path']))
            if not p.exists():
                # Allow a manifest/run directory to have moved since the original run.
                alt = manifest_path.parent / Path(str(art['path'])).name
                if alt.exists():
                    p = alt
            if p.exists():
                csv_path = p
                break
    if csv_path is None:
        alt = manifest_path.parent / 'dd022_source_inventory.csv'
        if alt.exists():
            csv_path = alt
    if csv_path is None:
        warnings.append(f'no source inventory CSV found for {manifest_path}')
        return {}, warnings
    rows: dict[str, dict[str, Any]] = {}
    with csv_path.open('r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        required = {'path', 'sha256'}
        missing = required - set(reader.fieldnames or [])
        if missing:
            warnings.append(f'source inventory missing columns {sorted(missing)}: {csv_path}')
            return {}, warnings
        for row in reader:
            rel = str(row.get('path', '')).replace('\\', '/').strip()
            if not rel:
                continue
            rows[rel] = dict(row)
    return rows, warnings


def classify_file(path: str) -> str:
    lower = path.lower()
    if lower.startswith('include/') or lower.endswith(('.hpp', '.h')):
        return 'source_header'
    if lower.startswith('src/') or lower.endswith(('.cpp', '.c', '.cc')):
        return 'source_code'
    if lower.endswith('.py'):
        return 'python_tool_or_test'
    if lower.endswith('.ps1'):
        return 'powershell_script'
    if lower.endswith('.dts'):
        return 'dotscript'
    if lower.endswith('.json'):
        return 'json_schema_or_manifest'
    if lower.endswith('.md'):
        return 'markdown_doc'
    if lower.endswith('.txt'):
        return 'text_doc_or_log'
    if lower.endswith('.cmake') or 'cmakelists.txt' in lower:
        return 'build_contract'
    return 'other_tracked_source'


def build_diff(base_rows: dict[str, dict[str, Any]], cand_rows: dict[str, dict[str, Any]]):
    base_keys = set(base_rows)
    cand_keys = set(cand_rows)
    added = sorted(cand_keys - base_keys)
    removed = sorted(base_keys - cand_keys)
    common = sorted(base_keys & cand_keys)
    changed = [p for p in common if base_rows[p].get('sha256') != cand_rows[p].get('sha256')]
    unchanged = [p for p in common if base_rows[p].get('sha256') == cand_rows[p].get('sha256')]
    return added, removed, changed, unchanged


def summarize_by_kind(paths: list[str]) -> dict[str, int]:
    out: dict[str, int] = {}
    for p in paths:
        k = classify_file(p)
        out[k] = out.get(k, 0) + 1
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description='DD-023 report-only redocumentation run diff skeleton')
    parser.add_argument('--base', required=True, help='Base DD-022 manifest file or run directory')
    parser.add_argument('--candidate', required=True, help='Candidate DD-022 manifest file or run directory')
    parser.add_argument('--out-dir', required=True, help='Output directory for DD-023 diff artifacts')
    parser.add_argument('--run-id', default=None, help='Stable diff run id')
    parser.add_argument('--profile', action='append', default=[], help='Profile scope label; may be repeated')
    parser.add_argument('--fail-on-review', action='store_true', help='Exit nonzero if status is REVIEW')
    args = parser.parse_args()

    out_dir = Path(args.out_dir).resolve()
    run_id = args.run_id or datetime.now(timezone.utc).strftime('DD023-DIFF-%Y%m%dT%H%M%SZ')
    warnings: list[str] = []

    base_manifest_path = resolve_manifest(Path(args.base).resolve())
    cand_manifest_path = resolve_manifest(Path(args.candidate).resolve())
    base_manifest = load_json(base_manifest_path)
    cand_manifest = load_json(cand_manifest_path)

    base_rows, w = load_source_inventory(base_manifest_path, base_manifest); warnings.extend(w)
    cand_rows, w = load_source_inventory(cand_manifest_path, cand_manifest); warnings.extend(w)

    added, removed, changed, unchanged = build_diff(base_rows, cand_rows)

    detail_fields = ['change_kind', 'path', 'object_kind', 'base_sha256', 'candidate_sha256', 'base_bytes', 'candidate_bytes']
    detail_rows: list[dict[str, Any]] = []
    for p in added:
        detail_rows.append({'change_kind': 'ADDED', 'path': p, 'object_kind': classify_file(p), 'candidate_sha256': cand_rows[p].get('sha256', ''), 'candidate_bytes': cand_rows[p].get('bytes', '')})
    for p in removed:
        detail_rows.append({'change_kind': 'REMOVED', 'path': p, 'object_kind': classify_file(p), 'base_sha256': base_rows[p].get('sha256', ''), 'base_bytes': base_rows[p].get('bytes', '')})
    for p in changed:
        detail_rows.append({'change_kind': 'CHANGED', 'path': p, 'object_kind': classify_file(p), 'base_sha256': base_rows[p].get('sha256', ''), 'candidate_sha256': cand_rows[p].get('sha256', ''), 'base_bytes': base_rows[p].get('bytes', ''), 'candidate_bytes': cand_rows[p].get('bytes', '')})

    review_rows: list[dict[str, Any]] = []
    for row in detail_rows:
        kind = row['object_kind']
        change = row['change_kind']
        needs = 'YES'
        gate = 'DD_REVIEW_DISPOSITION_REQUIRED'
        notes = 'Review source/documentation drift before promotion.'
        if kind in {'markdown_doc', 'text_doc_or_log'}:
            gate = 'DOC_REVIEW_REQUIRED'
        elif kind in {'source_code', 'source_header'}:
            gate = 'SOURCE_CONTRACT_RESCAN_REQUIRED'
            notes = 'Rerun source-contract, command, HELP, and runtime-proof checks as applicable.'
        elif kind in {'dotscript', 'powershell_script', 'python_tool_or_test'}:
            gate = 'SCRIPT_BOUNDARY_REVIEW_REQUIRED'
            notes = 'Check script boundary class and lifecycle role.'
        elif kind in {'json_schema_or_manifest', 'build_contract'}:
            gate = 'CONTRACT_REVIEW_REQUIRED'
        review_rows.append({'path': row['path'], 'change_kind': change, 'object_kind': kind, 'needs_review': needs, 'gate': gate, 'notes': notes})

    summary_rows = [
        {'metric': 'run_id', 'value': run_id},
        {'metric': 'base_run_id', 'value': base_manifest.get('run_id', '')},
        {'metric': 'candidate_run_id', 'value': cand_manifest.get('run_id', '')},
        {'metric': 'base_status', 'value': base_manifest.get('status', '')},
        {'metric': 'candidate_status', 'value': cand_manifest.get('status', '')},
        {'metric': 'base_source_files', 'value': str(len(base_rows))},
        {'metric': 'candidate_source_files', 'value': str(len(cand_rows))},
        {'metric': 'added_files', 'value': str(len(added))},
        {'metric': 'removed_files', 'value': str(len(removed))},
        {'metric': 'changed_files', 'value': str(len(changed))},
        {'metric': 'unchanged_files', 'value': str(len(unchanged))},
        {'metric': 'review_queue_rows', 'value': str(len(review_rows))},
        {'metric': 'warnings', 'value': str(len(warnings))},
    ]

    by_kind_rows: list[dict[str, Any]] = []
    for change_name, paths in [('ADDED', added), ('REMOVED', removed), ('CHANGED', changed)]:
        for kind, count in sorted(summarize_by_kind(paths).items()):
            by_kind_rows.append({'change_kind': change_name, 'object_kind': kind, 'count': count})

    status = 'PASS'
    if warnings:
        status = 'REVIEW'
    if added or removed or changed:
        status = 'REVIEW'

    out_dir.mkdir(parents=True, exist_ok=True)
    write_csv(out_dir / 'dd023_diff_summary.csv', summary_rows, ['metric', 'value'])
    write_csv(out_dir / 'dd023_file_diff.csv', detail_rows, detail_fields)
    write_csv(out_dir / 'dd023_change_by_kind.csv', by_kind_rows, ['change_kind', 'object_kind', 'count'])
    write_csv(out_dir / 'dd023_review_queue.csv', review_rows, ['path', 'change_kind', 'object_kind', 'needs_review', 'gate', 'notes'])

    manifest = {
        'schema_version': 'dd023_redoc_diff_run_v0',
        'run_id': run_id,
        'created_utc': datetime.now(timezone.utc).isoformat(),
        'status': status,
        'boundary': 'REPORT_ONLY_PROMOTION_BLOCKED',
        'profile_scope': args.profile,
        'base_manifest': str(base_manifest_path),
        'candidate_manifest': str(cand_manifest_path),
        'base_run_id': base_manifest.get('run_id'),
        'candidate_run_id': cand_manifest.get('run_id'),
        'counts': {
            'base_source_files': len(base_rows),
            'candidate_source_files': len(cand_rows),
            'added_files': len(added),
            'removed_files': len(removed),
            'changed_files': len(changed),
            'unchanged_files': len(unchanged),
            'review_queue_rows': len(review_rows),
            'warnings': len(warnings),
        },
        'outputs': {
            'summary_csv': str(out_dir / 'dd023_diff_summary.csv'),
            'file_diff_csv': str(out_dir / 'dd023_file_diff.csv'),
            'change_by_kind_csv': str(out_dir / 'dd023_change_by_kind.csv'),
            'review_queue_csv': str(out_dir / 'dd023_review_queue.csv'),
        },
        'warnings': warnings,
        'next_action': 'Review DD-023 queue; rerun specialized extractors for changed lanes; do not promote without explicit authorization.',
    }
    manifest_path = out_dir / 'dd023_redoc_diff_manifest.json'
    write_json(manifest_path, manifest)
    print(f'DD-023 diff manifest: {manifest_path}')
    print(f'status: {status}; added: {len(added)}; removed: {len(removed)}; changed: {len(changed)}; warnings: {len(warnings)}')
    if status == 'REVIEW' and args.fail_on_review:
        return 2
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
