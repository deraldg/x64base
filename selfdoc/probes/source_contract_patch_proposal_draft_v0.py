#!/usr/bin/env python3
"""
source_contract_patch_proposal_draft_v0.py

REPORT_ONLY / PROPOSAL_ONLY patch proposal draft for source-contract Batch 0.

Run from:
    D:\code\ccode

Reads:
    dottalkpp\docs\generated\reports\source_contract_patch_proposal_plan_v0.csv
    dottalkpp\docs\generated\reports\source_contract_patch_proposal_plan_v0.json
    dottalkpp\docs\generated\reports\source_contracts_inventory_v1_1.csv
    source files named by Batch 0 rows, read-only

Writes:
    dottalkpp\docs\generated\reports\source_contract_patch_proposal_draft_v0.md
    dottalkpp\docs\generated\reports\source_contract_patch_proposal_draft_v0.csv
    dottalkpp\docs\generated\reports\source_contract_patch_proposal_draft_v0.json
    dottalkpp\docs\generated\patches\source_contract_patch_proposal_draft_v0\*.proposal.md
    dottalkpp\docs\generated\patches\source_contract_patch_proposal_draft_v0\*.proposal.json

Safety:
    REPORT_ONLY / PROPOSAL_ONLY
    Does not edit source.
    Does not apply patches.
    Does not create executable patch files.
    Does not create a repair batch.
    Does not write DBFs.
    Does not modify CMDHELPCHK.
    Does not rebuild HELP DATA.
    Does not promote v1.1 to default.
    Does not move/delete files.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from collections import Counter
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPORT_DIRS = (
    Path('dottalkpp') / 'docs' / 'generated' / 'reports',
    Path('docs') / 'generated' / 'reports',
)

PATCH_ROOT = Path('dottalkpp') / 'docs' / 'generated' / 'patches' / 'source_contract_patch_proposal_draft_v0'

PLAN_CSV = 'source_contract_patch_proposal_plan_v0.csv'
PLAN_JSON = 'source_contract_patch_proposal_plan_v0.json'
INV_CSV = 'source_contracts_inventory_v1_1.csv'

OUT_MD = 'source_contract_patch_proposal_draft_v0.md'
OUT_CSV = 'source_contract_patch_proposal_draft_v0.csv'
OUT_JSON = 'source_contract_patch_proposal_draft_v0.json'

MARKER = '@dottalk.usage v1'
SAFETY_CLASS = 'REPORT_ONLY / PROPOSAL_ONLY'


@dataclass
class ProposalRow:
    path: str
    selection_status: str
    proposal_lane: str
    proposed_action: str
    source_read_status: str
    inventory_header_hash: str = ''
    computed_header_hash: str = ''
    hash_matches_inventory: bool = False
    header_start_line: int = 0
    header_end_line: int = 0
    proposal_status: str = ''
    confidence: str = ''
    rationale: str = ''
    proposal_md: str = ''
    proposal_json: str = ''
    source_edit_authorized: bool = False
    patch_apply_authorized: bool = False
    executable_patch_file_created: bool = False
    notes: list[str] = field(default_factory=list)
    original_header_preview: str = ''
    proposed_header_preview: str = ''


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        return []
    with path.open('r', encoding='utf-8', newline='') as f:
        return [dict(row) for row in csv.DictReader(f)]


def read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except Exception as exc:
        return {'_read_error': f'{type(exc).__name__}: {exc}'}


def md_escape(value: object) -> str:
    return str(value).replace('|', '\\|').replace('\n', ' ')


def find_report_dir(root: Path, explicit: str | None) -> Path:
    if explicit:
        d = root / explicit
        if not d.is_dir():
            raise SystemExit(f'Report directory not found: {d}')
        return d
    for rel in REPORT_DIRS:
        d = root / rel
        if (d / PLAN_CSV).is_file():
            return d
    raise SystemExit('Could not find source_contract_patch_proposal_plan_v0.csv under dottalkpp\\docs\\generated\\reports')


def read_text(path: Path) -> tuple[str, list[str]]:
    raw = path.read_bytes()
    notes: list[str] = []
    for enc in ('utf-8-sig', 'utf-8', 'cp1252', 'latin-1'):
        try:
            text = raw.decode(enc, errors='strict')
            if enc not in ('utf-8', 'utf-8-sig'):
                notes.append(f'decoded_as={enc}')
            return text, notes
        except UnicodeDecodeError:
            pass
    notes.append('decoded_as=utf-8-surrogateescape')
    return raw.decode('utf-8', errors='surrogateescape'), notes


def line_number_for_offset(text: str, offset: int) -> int:
    return text.count('\n', 0, offset) + 1


def find_contract_blocks(text: str) -> list[tuple[int, int, str]]:
    blocks: list[tuple[int, int, str]] = []
    for match in re.finditer(re.escape(MARKER), text):
        marker_start = match.start()
        block_start = text.rfind('/*', 0, marker_start)
        block_end = text.find('*/', match.end())
        if block_start != -1 and block_end != -1:
            prior_close = text.rfind('*/', 0, marker_start)
            if prior_close < block_start:
                end = block_end + 2
                blocks.append((block_start, end, text[block_start:end]))
                continue

        line_start = text.rfind('\n', 0, marker_start) + 1
        line_end = text.find('\n', marker_start)
        if line_end == -1:
            line_end = len(text)
        start = line_start
        while start > 0:
            prev_end = start - 1
            prev_start = text.rfind('\n', 0, prev_end) + 1
            if text[prev_start:prev_end].lstrip().startswith('//'):
                start = prev_start
            else:
                break
        end = line_end
        while end < len(text):
            next_start = end + 1
            next_end = text.find('\n', next_start)
            if next_end == -1:
                next_end = len(text)
            if text[next_start:next_end].lstrip().startswith('//'):
                end = next_end
                if next_end == len(text):
                    break
            else:
                break
        blocks.append((start, end, text[start:end]))
    unique = {(s, e): b for s, e, b in blocks}
    return [(s, e, b) for (s, e), b in sorted(unique.items())]


def strip_comment_prefix(line: str) -> str:
    s = line.strip()
    if s.startswith('/*'):
        s = s[2:].lstrip()
    if s.endswith('*/'):
        s = s[:-2].rstrip()
    if s.startswith('//'):
        s = s[2:].lstrip()
    if s.startswith('*'):
        s = s[1:].lstrip()
    return s.rstrip()


def parse_contract_payload(header: str) -> tuple[list[str], list[str]]:
    payload: list[str] = []
    notes: list[str] = []
    marker_seen = False
    for raw in header.splitlines():
        line = strip_comment_prefix(raw)
        if not line or line in {'/*', '*/', '*'}:
            continue
        if MARKER in line:
            if marker_seen:
                notes.append('duplicate marker suppressed in proposal preview')
                continue
            payload.append(MARKER)
            marker_seen = True
            continue
        payload.append(line)
    if not marker_seen:
        payload.insert(0, MARKER)
        notes.append('marker inserted in proposal payload because capture did not normalize marker as first line')
    return payload, notes


def render_block_comment(payload_lines: list[str]) -> str:
    lines = ['/*']
    for line in payload_lines:
        lines.append(f' * {line}')
    lines.append(' */')
    return '\n'.join(lines)


def shorten(text: str, max_chars: int = 900) -> str:
    text = text.replace('\r\n', '\n')
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + '\n... [truncated in CSV preview]'


def safe_stem(path: str) -> str:
    stem = path.replace('\\', '/').replace('/', '__')
    return re.sub(r'[^A-Za-z0-9_.-]+', '_', stem)


def inventory_index(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    return {row.get('path', ''): row for row in rows if row.get('path', '')}


def selected_batch(plan_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    return [row for row in plan_rows if row.get('selection_status', '') == 'BATCH_0_CANDIDATE']


def write_individual_proposal(root: Path, out_dir: Path, proposal: ProposalRow, original_header: str, proposed_header: str) -> tuple[str, str]:
    stem = safe_stem(proposal.path)
    md_path = out_dir / f'{stem}.proposal.md'
    json_path = out_dir / f'{stem}.proposal.json'

    md = []
    md.append(f'# Source Contract Patch Proposal Draft: `{proposal.path}`')
    md.append('')
    md.append('Safety: `PROPOSAL_ONLY`')
    md.append('')
    md.append('This is a review artifact. It is not an executable patch file and must not be applied automatically.')
    md.append('')
    md.append('## Status')
    md.append('')
    md.append(f'- proposal_status: `{proposal.proposal_status}`')
    md.append(f'- confidence: `{proposal.confidence}`')
    md.append(f'- source_edit_authorized: `{proposal.source_edit_authorized}`')
    md.append(f'- patch_apply_authorized: `{proposal.patch_apply_authorized}`')
    md.append(f'- executable_patch_file_created: `{proposal.executable_patch_file_created}`')
    md.append(f'- inventory_header_hash: `{proposal.inventory_header_hash}`')
    md.append(f'- computed_header_hash: `{proposal.computed_header_hash}`')
    md.append(f'- hash_matches_inventory: `{proposal.hash_matches_inventory}`')
    md.append(f'- source lines: `{proposal.header_start_line}-{proposal.header_end_line}`')
    md.append('')
    md.append('## Rationale')
    md.append('')
    md.append(proposal.rationale)
    md.append('')
    md.append('## Original captured header')
    md.append('')
    md.append('```cpp')
    md.append(original_header.rstrip())
    md.append('```')
    md.append('')
    md.append('## Proposed normalized header')
    md.append('')
    md.append('```cpp')
    md.append(proposed_header.rstrip())
    md.append('```')
    md.append('')
    md.append('## Review checklist')
    md.append('')
    md.append('- Confirm the normalized block preserves the exact usage-contract payload text.')
    md.append('- Confirm no field meaning is changed.')
    md.append('- Confirm the proposed block is appropriate for this source file.')
    md.append('- Confirm this proposal should become an actual patch only after explicit authorization.')
    md_path.write_text('\n'.join(md) + '\n', encoding='utf-8')

    payload = {
        'path': proposal.path,
        'safety': 'PROPOSAL_ONLY',
        'proposal': asdict(proposal),
        'original_header': original_header,
        'proposed_header': proposed_header,
        'source_edit_authorized': False,
        'patch_apply_authorized': False,
        'executable_patch_file_created': False,
    }
    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding='utf-8')
    return str(md_path.relative_to(root)), str(json_path.relative_to(root))


def make_proposal(root: Path, out_dir: Path, plan: dict[str, str], inv: dict[str, str]) -> ProposalRow:
    rel_path = plan.get('path', '')
    source_path = root / rel_path
    row = ProposalRow(
        path=rel_path,
        selection_status=plan.get('selection_status', ''),
        proposal_lane=plan.get('proposal_lane', ''),
        proposed_action=plan.get('proposed_action', ''),
        source_read_status='not_read',
        inventory_header_hash=inv.get('header_hash', ''),
    )
    if not source_path.is_file():
        row.source_read_status = 'missing_source_file'
        row.proposal_status = 'BLOCKED'
        row.confidence = 'NONE'
        row.rationale = 'Source file was not found; no proposal could be generated.'
        row.notes.append(f'missing source file: {source_path}')
        return row
    try:
        text, notes = read_text(source_path)
        row.notes.extend(notes)
    except Exception as exc:
        row.source_read_status = 'read_error'
        row.proposal_status = 'BLOCKED'
        row.confidence = 'NONE'
        row.rationale = f'Source read failed: {type(exc).__name__}: {exc}'
        return row

    blocks = find_contract_blocks(text)
    if len(blocks) != 1:
        row.source_read_status = 'unexpected_contract_block_count'
        row.proposal_status = 'BLOCKED'
        row.confidence = 'LOW'
        row.rationale = f'Expected exactly one @dottalk.usage v1 block; found {len(blocks)}. Manual review required.'
        row.notes.append(f'contract block count: {len(blocks)}')
        return row

    start, end, original_header = blocks[0]
    computed_hash = hashlib.sha256(original_header.encode('utf-8', errors='surrogateescape')).hexdigest()
    row.computed_header_hash = computed_hash
    row.hash_matches_inventory = bool(row.inventory_header_hash) and row.inventory_header_hash == computed_hash
    row.header_start_line = line_number_for_offset(text, start)
    row.header_end_line = line_number_for_offset(text, end)

    payload_lines, proposal_notes = parse_contract_payload(original_header)
    row.notes.extend(proposal_notes)
    proposed_header = render_block_comment(payload_lines)

    if not row.hash_matches_inventory:
        row.proposal_status = 'REVIEW_REQUIRED_HASH_MISMATCH'
        row.confidence = 'LOW'
        row.rationale = 'Computed header hash does not match inventory hash. Proposal generated for review only; do not patch until inventory is refreshed or mismatch is explained.'
    elif original_header.strip() == proposed_header.strip():
        row.proposal_status = 'NO_TEXT_CHANGE_NEEDED_REVIEW_ONLY'
        row.confidence = 'MEDIUM'
        row.rationale = 'Header already matches normalized proposal rendering. The prior malformed flag may reflect parser/capture interpretation rather than required text change.'
    else:
        row.proposal_status = 'DRAFT_READY_REVIEW_ONLY'
        row.confidence = 'MEDIUM'
        row.rationale = 'Draft normalizes the captured @dottalk.usage v1 block into a single block-comment form while preserving payload lines. Review before any patch proposal is authorized.'

    row.source_read_status = 'read_ok'
    row.original_header_preview = shorten(original_header)
    row.proposed_header_preview = shorten(proposed_header)
    md_rel, json_rel = write_individual_proposal(root, out_dir, row, original_header, proposed_header)
    row.proposal_md = md_rel
    row.proposal_json = json_rel
    return row


def write_csv_report(path: Path, rows: list[ProposalRow]) -> None:
    fieldnames = [
        'path','selection_status','proposal_lane','proposed_action','source_read_status',
        'inventory_header_hash','computed_header_hash','hash_matches_inventory',
        'header_start_line','header_end_line','proposal_status','confidence','rationale',
        'proposal_md','proposal_json','source_edit_authorized','patch_apply_authorized',
        'executable_patch_file_created','notes','original_header_preview','proposed_header_preview',
    ]
    with path.open('w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            data = asdict(row)
            for key, value in list(data.items()):
                if isinstance(value, list):
                    data[key] = '; '.join(str(v) for v in value)
            writer.writerow(data)


def write_json_report(path: Path, summary: dict[str, Any], rows: list[ProposalRow]) -> None:
    path.write_text(json.dumps({'summary': summary, 'proposal_rows': [asdict(row) for row in rows]}, indent=2, ensure_ascii=False), encoding='utf-8')


def write_md_report(path: Path, csv_path: Path, json_path: Path, summary: dict[str, Any], rows: list[ProposalRow], load_notes: list[str]) -> None:
    lines = []
    lines.append('# Source Contract Patch Proposal Draft v0')
    lines.append('')
    lines.append(f"Generated UTC: `{summary['generated_at_utc']}`")
    lines.append('')
    lines.append(f'Safety class: `{SAFETY_CLASS}`')
    lines.append('')
    lines.append('## Verdict')
    lines.append('')
    lines.append('```text')
    lines.append('patch proposal draft: GENERATED')
    lines.append('patch files: NOT CREATED')
    lines.append('patch application: NOT AUTHORIZED')
    lines.append('source edits: NOT AUTHORIZED')
    lines.append('repair batch: NOT CREATED')
    lines.append('DBF writes: NOT AUTHORIZED')
    lines.append('CMDHELPCHK changes: NOT AUTHORIZED')
    lines.append('HELP DATA rebuild: NOT AUTHORIZED')
    lines.append('```')
    lines.append('')
    lines.append('## Scope')
    lines.append('')
    lines.append('This report generates reviewable proposal artifacts for Batch 0 only. It reads source files to capture current contract headers and writes proposal documents under `docs/generated/patches`. These are not executable patch files and must not be applied automatically.')
    lines.append('')
    lines.append('Inputs read:')
    lines.append('')
    for note in load_notes:
        lines.append(f'- `{md_escape(note)}`')
    lines.append('')
    lines.append('Outputs written:')
    lines.append('')
    lines.append(f'- `{path}`')
    lines.append(f'- `{csv_path}`')
    lines.append(f'- `{json_path}`')
    lines.append(f"- `{summary['proposal_output_dir']}`")
    lines.append('')
    lines.append('## Summary counts')
    lines.append('')
    for key in ['batch_0_rows','proposal_rows','draft_ready_review_only','no_text_change_needed_review_only','blocked_or_low_confidence','hash_mismatch_count']:
        lines.append(f"- {key}: `{summary.get(key, '')}`")
    lines.append('')
    lines.append('## Proposal status counts')
    lines.append('')
    lines.append('| Proposal status | Count |')
    lines.append('|---|---:|')
    for status, count in summary['proposal_status_counts'].items():
        lines.append(f'| `{md_escape(status)}` | {count} |')
    lines.append('')
    lines.append('## Batch 0 proposal rows')
    lines.append('')
    if rows:
        lines.append('| Path | Status | Hash OK | Lines | Proposal | Rationale |')
        lines.append('|---|---|---:|---|---|---|')
        for row in rows:
            lines.append(f"| `{md_escape(row.path)}` | `{md_escape(row.proposal_status)}` | {row.hash_matches_inventory} | `{row.header_start_line}-{row.header_end_line}` | `{md_escape(row.proposal_md)}` | {md_escape(row.rationale)} |")
    else:
        lines.append('No Batch 0 proposal rows found.')
    lines.append('')
    lines.append('## Planning rules')
    lines.append('')
    lines.append('```text')
    lines.append('This is not a patch.')
    lines.append('This is not a repair batch.')
    lines.append('Do not apply the proposal files automatically.')
    lines.append('Do not edit source from this report.')
    lines.append('Do not write DBFs.')
    lines.append('Do not rebuild HELP DATA.')
    lines.append('Do not modify CMDHELPCHK.')
    lines.append('A future patch bundle requires explicit approval after proposal review.')
    lines.append('```')
    lines.append('')
    lines.append('## Non-mutation confirmation')
    lines.append('')
    for guard in summary['non_mutation_guards']:
        lines.append(f'- `{md_escape(guard)}`')
    path.write_text('\n'.join(lines) + '\n', encoding='utf-8')


def main() -> int:
    parser = argparse.ArgumentParser(description='Create source contract patch proposal draft v0.')
    parser.add_argument('--root', default='.')
    parser.add_argument('--report-dir', default=None)
    args = parser.parse_args()

    root = Path(args.root).resolve()
    rd = find_report_dir(root, args.report_dir)
    plan_rows = read_csv_rows(rd / PLAN_CSV)
    _plan_json = read_json(rd / PLAN_JSON)
    inv_rows = read_csv_rows(rd / INV_CSV)
    inv = inventory_index(inv_rows)
    batch_rows = selected_batch(plan_rows)

    out_dir = root / PATCH_ROOT
    out_dir.mkdir(parents=True, exist_ok=True)
    proposal_rows = [make_proposal(root, out_dir, plan, inv.get(plan.get('path', ''), {})) for plan in batch_rows]

    status_counts = Counter(row.proposal_status for row in proposal_rows)
    hash_mismatch = sum(1 for row in proposal_rows if row.computed_header_hash and not row.hash_matches_inventory)
    blocked = sum(1 for row in proposal_rows if row.proposal_status.startswith('BLOCKED') or row.confidence in {'LOW', 'NONE'})

    summary = {
        'generated_at_utc': datetime.now(timezone.utc).isoformat(),
        'status': 'PROPOSAL_ONLY_GENERATED',
        'report_dir': str(rd),
        'proposal_output_dir': str(PATCH_ROOT),
        'batch_0_rows': len(batch_rows),
        'proposal_rows': len(proposal_rows),
        'draft_ready_review_only': status_counts.get('DRAFT_READY_REVIEW_ONLY', 0),
        'no_text_change_needed_review_only': status_counts.get('NO_TEXT_CHANGE_NEEDED_REVIEW_ONLY', 0),
        'blocked_or_low_confidence': blocked,
        'hash_mismatch_count': hash_mismatch,
        'proposal_status_counts': dict(status_counts.most_common()),
        'non_mutation_guards': [
            'did_not_edit_source',
            'did_not_apply_patches',
            'did_not_create_executable_patch_files',
            'did_not_create_repair_batch',
            'did_not_write_dbfs',
            'did_not_modify_cmdhelpchk',
            'did_not_rebuild_help_data',
            'did_not_repair_headers',
            'did_not_promote_v1_1_to_default',
            'did_not_move_or_delete_files',
        ],
    }

    out_md = rd / OUT_MD
    out_csv = rd / OUT_CSV
    out_json = rd / OUT_JSON
    load_notes = [
        f'read patch proposal plan CSV: {rd / PLAN_CSV}',
        f'read patch proposal plan JSON: {rd / PLAN_JSON}' if (rd / PLAN_JSON).is_file() else f'patch proposal plan JSON missing: {rd / PLAN_JSON}',
        f'read v1.1 inventory CSV: {rd / INV_CSV}' if (rd / INV_CSV).is_file() else f'v1.1 inventory CSV missing: {rd / INV_CSV}',
        f'read Batch 0 source files from project root: {root}',
    ]
    write_csv_report(out_csv, proposal_rows)
    write_json_report(out_json, summary, proposal_rows)
    write_md_report(out_md, out_csv, out_json, summary, proposal_rows, load_notes)

    print('SelfDoc source contract patch proposal draft v0 complete.')
    print(f'Read report directory: {rd}')
    print(f'Batch 0 rows: {len(batch_rows)}')
    print(f'Proposal rows: {len(proposal_rows)}')
    print(f"Draft-ready proposals: {summary['draft_ready_review_only']}")
    print(f"No-text-change review rows: {summary['no_text_change_needed_review_only']}")
    print(f"Blocked/low-confidence rows: {summary['blocked_or_low_confidence']}")
    print(f'Wrote: {out_md}')
    print(f'Wrote: {out_csv}')
    print(f'Wrote: {out_json}')
    print(f'Wrote proposal artifacts under: {PATCH_ROOT}')
    print('No source files were edited.')
    print('No patches were applied.')
    print('No executable patch files were created.')
    print('No repair batch was created.')
    print('No DBFs were written.')
    print('CMDHELPCHK was not modified.')
    print('HELP DATA was not rebuilt.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
