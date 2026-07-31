#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import datetime as _dt
import difflib
import json
import re
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

EXPECTED_DD066R_STATUS = "DDICT_REGISTRATION_BUILD_TARGET_REFINEMENT_READY"

KNOWN_COMMANDS = {'ABOUT','HELP','AREA','COUNT','LIST','USE','CALC','CATALOGCANARY','CMDHELPCHK','GPS','WORKSPACE','ERSATZ'}

def utc_now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).isoformat(timespec='seconds')

def stamp() -> str:
    return _dt.datetime.now().strftime('%Y%m%d-%H%M%S')

def read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding='utf-8', errors='replace'))
    except Exception:
        return {}

def read_csv_dict(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open('r', newline='', encoding='utf-8', errors='replace') as f:
        return list(csv.DictReader(f))

def write_json(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + '\n', encoding='utf-8')

def write_csv(path: Path, rows: List[Dict[str, Any]], fields: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator='\n')
        w.writeheader()
        for row in rows:
            w.writerow({k: row.get(k, '') for k in fields})

def safe_rel(repo: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(repo.resolve()).as_posix()
    except Exception:
        return path.as_posix()

def read_text(path: Path) -> str:
    return path.read_text(encoding='utf-8', errors='replace')

def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8')

def unified_diff(old: str, new: str, fromfile: str, tofile: str) -> str:
    return ''.join(difflib.unified_diff(old.splitlines(keepends=True), new.splitlines(keepends=True), fromfile=fromfile, tofile=tofile, lineterm=''))

def get_accepted_target(rows: List[Dict[str, str]], kind: str) -> str:
    for row in rows:
        if row.get('target_kind') == kind:
            return row.get('accepted_path', '')
    return ''

def insert_include(reg_text: str) -> Tuple[str, Dict[str, Any]]:
    if 'cmd_ddict.hpp' in reg_text:
        return reg_text, {'patch_part': 'include', 'patch_needed': 0, 'patch_possible': 1, 'reason': 'cmd_ddict.hpp include already present', 'insert_after': '', 'new_entry': ''}
    lines = reg_text.splitlines()
    include_indices = [i for i, line in enumerate(lines) if re.match(r'\s*#\s*include\s+', line)]
    if not include_indices:
        return reg_text, {'patch_part': 'include', 'patch_needed': 1, 'patch_possible': 0, 'reason': 'no include block found', 'insert_after': '', 'new_entry': ''}
    anchor = include_indices[-1]
    entry = '#include "cli/cmd_ddict.hpp"'
    new_lines = lines[:anchor+1] + [entry] + lines[anchor+1:]
    return '\n'.join(new_lines) + ('\n' if reg_text.endswith('\n') else ''), {'patch_part': 'include', 'patch_needed': 1, 'patch_possible': 1, 'reason': 'insert include after existing include block', 'insert_after': lines[anchor].strip(), 'new_entry': entry}

def brace_delta(line: str) -> int:
    # simple enough for command initializer regions; ignores braces inside strings.
    s = re.sub(r'"(?:\\.|[^"\\])*"', '""', line)
    return s.count('{') - s.count('}')

def find_entry_block(lines: List[str], token_index: int) -> Tuple[int, int]:
    start = token_index
    # Move upward to likely initializer start if current line is a continuation.
    while start > 0 and not ('{' in lines[start] or lines[start].lstrip().startswith(('register', 'add', 'emplace', 'cmds', 'commands'))):
        start -= 1
        if token_index - start > 8:
            start = token_index
            break
    depth = 0
    saw_open = False
    end = token_index
    for idx in range(start, min(len(lines), start + 20)):
        depth += brace_delta(lines[idx])
        if '{' in lines[idx]:
            saw_open = True
        end = idx
        if saw_open and depth <= 0 and idx >= token_index:
            break
        if idx >= token_index and lines[idx].rstrip().endswith((');', '},', '};')) and not saw_open:
            break
    return start, end

def command_token_matches(line: str) -> List[re.Match[str]]:
    out = []
    for m in re.finditer(r'"([A-Za-z][A-Za-z0-9_ -]*)"', line):
        if m.group(1).upper() in KNOWN_COMMANDS:
            out.append(m)
    return out

def transform_registration_block(block: str) -> Tuple[Optional[str], Dict[str, Any]]:
    original = block
    # First replace a known quoted command token.
    m = None
    for match in re.finditer(r'"([A-Za-z][A-Za-z0-9_ -]*)"', block):
        if match.group(1).upper() in KNOWN_COMMANDS:
            m = match
            break
    if not m:
        return None, {'reason': 'no known command string in block'}
    block = block[:m.start()] + '"DDICT"' + block[m.end():]

    replacements = 0
    # Replace common command handler symbols.
    block2, n = re.subn(r'\bcmd_[A-Za-z0-9_]+\b', 'cmd_DDICT', block, count=1)
    block = block2
    replacements += n
    if replacements == 0:
        block2, n = re.subn(r'\b[A-Za-z0-9_]*Command\b', 'cmd_DDICT', block, count=1)
        block = block2
        replacements += n
    if replacements == 0:
        block2, n = re.subn(r'\b[A-Za-z0-9_]*Handler\b', 'cmd_DDICT', block, count=1)
        block = block2
        replacements += n

    # If the local registry uses command enum tokens, do not invent enum DDICT unless already supported.
    block = re.sub(r'\bCommandId::[A-Za-z0-9_]+\b', 'CommandId::DDICT', block, count=1)

    if 'cmd_DDICT' not in block:
        return None, {'reason': 'block transformed command name but no callable handler could be safely replaced'}
    if block == original:
        return None, {'reason': 'block unchanged'}
    return block, {'reason': 'mirrored local registration block with DDICT/cmd_DDICT'}

def patch_registry_entry(reg_text: str) -> Tuple[str, Dict[str, Any], str]:
    if 'cmd_DDICT' in reg_text or '"DDICT"' in reg_text:
        return reg_text, {'patch_part': 'registration', 'patch_needed': 0, 'patch_possible': 1, 'reason': 'DDICT registration already present', 'insert_after': '', 'new_entry': ''}, ''
    lines = reg_text.splitlines()
    candidates = []
    for idx, line in enumerate(lines):
        if command_token_matches(line):
            start, end = find_entry_block(lines, idx)
            block = '\n'.join(lines[start:end+1])
            candidate, info = transform_registration_block(block)
            candidates.append({'start': start, 'end': end, 'block': block, 'candidate': candidate or '', 'reason': info.get('reason', '')})
            if candidate:
                new_lines = lines[:end+1] + candidate.splitlines() + lines[end+1:]
                return '\n'.join(new_lines) + ('\n' if reg_text.endswith('\n') else ''), {'patch_part': 'registration', 'patch_needed': 1, 'patch_possible': 1, 'reason': info.get('reason', ''), 'insert_after': lines[end].strip(), 'new_entry': candidate.splitlines()[0].strip()}, '\n\n'.join(c['candidate'] or ('# candidate failed: ' + c['reason'] + '\n' + c['block']) for c in candidates[:8])
    return reg_text, {'patch_part': 'registration', 'patch_needed': 1, 'patch_possible': 0, 'reason': 'no mirrorable local command registration block found', 'insert_after': '', 'new_entry': ''}, ''

def patch_registry(reg_text: str) -> Tuple[str, List[Dict[str, Any]], str]:
    after_include, include_info = insert_include(reg_text)
    after_reg, reg_info, candidates_text = patch_registry_entry(after_include)
    return after_reg, [include_info, reg_info], candidates_text

def cmake_has_glob_for_cli(cmake_text: str) -> bool:
    t = cmake_text.replace('\\', '/').lower()
    if 'glob' in t and 'cli/*.cpp' in t:
        return True
    if 'glob_recurse' in t and '*.cpp' in t:
        return True
    return False

def patch_cmake(cmake_text: str) -> Tuple[str, Dict[str, Any]]:
    if 'cmd_ddict.cpp' in cmake_text:
        return cmake_text, {'patch_part': 'build_source_entry', 'patch_needed': 0, 'patch_possible': 1, 'reason': 'cmd_ddict.cpp already present', 'insert_after': '', 'new_entry': ''}
    if cmake_has_glob_for_cli(cmake_text):
        return cmake_text, {'patch_part': 'build_source_entry', 'patch_needed': 0, 'patch_possible': 1, 'reason': 'CMake appears to glob cli/*.cpp or all *.cpp; explicit source entry not needed', 'insert_after': '', 'new_entry': ''}
    lines = cmake_text.splitlines()
    anchors = []
    for idx, line in enumerate(lines):
        ll = line.lower().replace('\\', '/')
        if '.cpp' in ll and ('cli/' in ll or 'cmd_' in ll or 'command_registry.cpp' in ll):
            anchors.append(idx)
    if not anchors:
        # Try source variable closing paren after target_sources/add_executable block.
        return cmake_text, {'patch_part': 'build_source_entry', 'patch_needed': 1, 'patch_possible': 0, 'reason': 'no explicit .cpp source anchor and no glob source pattern found', 'insert_after': '', 'new_entry': ''}
    preferred = None
    for idx in anchors:
        ll = lines[idx].lower().replace('\\', '/')
        if 'command_registry.cpp' in ll or 'cmd_catalogcanary.cpp' in ll:
            preferred = idx
            break
    if preferred is None:
        preferred = anchors[-1]
    anchor_line = lines[preferred]
    indent = anchor_line[:len(anchor_line) - len(anchor_line.lstrip())]
    if 'cli/' in anchor_line.replace('\\','/').lower():
        entry = indent + 'cli/cmd_ddict.cpp'
    else:
        entry = indent + 'cmd_ddict.cpp'
    new_lines = lines[:preferred+1] + [entry] + lines[preferred+1:]
    return '\n'.join(new_lines) + ('\n' if cmake_text.endswith('\n') else ''), {'patch_part': 'build_source_entry', 'patch_needed': 1, 'patch_possible': 1, 'reason': 'inserted cmd_ddict.cpp after local source anchor', 'insert_after': anchor_line.strip(), 'new_entry': entry.strip()}

def backup_file(repo: Path, backup_dir: Path, path: Path) -> Path:
    rel = path.resolve().relative_to(repo.resolve())
    dest = backup_dir / rel
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, dest)
    return dest

def main() -> int:
    ap = argparse.ArgumentParser(description='DD-067R local-pattern DDICT registration/build patch repair')
    ap.add_argument('--repo-root', required=True)
    ap.add_argument('--out-dir', required=True)
    ap.add_argument('--run-id', default='DD067R-local-pattern-ddict-registration-build-patch-v0')
    ap.add_argument('--dd066r-dir', default='docs/datadict/reports/DD066R-ddict-registration-build-target-refinement-final-v0')
    ap.add_argument('--fallback-dd066r-dir', default='docs/datadict/reports/DD066R-ddict-registration-build-target-refinement-v0')
    ap.add_argument('--apply-patch', action='store_true')
    ap.add_argument('--backup-root', default='docs/datadict/backups')
    ap.add_argument('--profile', action='append', default=[])
    ap.add_argument('--fail-on-review', action='store_true')
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    out = Path(args.out_dir).resolve()
    dd066r_dir = (repo / args.dd066r_dir).resolve()
    if not dd066r_dir.exists():
        dd066r_dir = (repo / args.fallback_dd066r_dir).resolve()
    backup_root = (repo / args.backup_root).resolve()
    out.mkdir(parents=True, exist_ok=True)

    dd066r_manifest = read_json(dd066r_dir / 'dd066r_ddict_registration_build_target_refinement_manifest.json')
    targets = read_csv_dict(dd066r_dir / 'dd066r_accepted_patch_targets.csv')
    reg_target = ''
    build_target = ''
    smoke_target = ''
    for row in targets:
        if row.get('target_kind') == 'registration': reg_target = row.get('accepted_path', '')
        if row.get('target_kind') == 'build': build_target = row.get('accepted_path', '')
        if row.get('target_kind') == 'smoke': smoke_target = row.get('accepted_path', '')
    reg_path = (repo / reg_target).resolve() if reg_target else repo / 'MISSING_REGISTRATION_TARGET'
    build_path = (repo / build_target).resolve() if build_target else repo / 'MISSING_BUILD_TARGET'
    smoke_path = (repo / smoke_target).resolve() if smoke_target else repo / 'MISSING_SMOKE_TARGET'

    failures = 0
    review_rows: List[Dict[str, Any]] = []
    if dd066r_manifest.get('status') != EXPECTED_DD066R_STATUS:
        failures += 1
        review_rows.append({'issue': 'DD066R_NOT_READY', 'detail': dd066r_manifest.get('status', '')})
    for label, path in [('registration', reg_path), ('build', build_path), ('smoke', smoke_path)]:
        if not path.exists():
            failures += 1
            review_rows.append({'issue': f'{label.upper()}_TARGET_MISSING', 'detail': str(path)})

    patch_rows: List[Dict[str, Any]] = []
    diff_texts: List[str] = []
    candidate_text = ''
    reg_old = build_old = reg_new = build_new = ''
    if failures == 0:
        reg_old = reg_path.read_text(encoding='utf-8', errors='replace')
        build_old = build_path.read_text(encoding='utf-8', errors='replace')
        reg_new, reg_rows, candidate_text = patch_registry(reg_old)
        build_new, build_row = patch_cmake(build_old)
        for row in reg_rows:
            row['target'] = safe_rel(repo, reg_path)
            patch_rows.append(row)
        build_row['target'] = safe_rel(repo, build_path)
        patch_rows.append(build_row)
        for row in patch_rows:
            if int(row.get('patch_needed', 0)) == 1 and int(row.get('patch_possible', 0)) != 1:
                failures += 1
                review_rows.append({'issue': 'PATCH_NOT_POSSIBLE', 'detail': f"{row.get('patch_part')} {row.get('target')} {row.get('reason')}"})
        if reg_new != reg_old:
            diff_texts.append(unified_diff(reg_old, reg_new, safe_rel(repo, reg_path) + '.before', safe_rel(repo, reg_path) + '.after'))
        if build_new != build_old:
            diff_texts.append(unified_diff(build_old, build_new, safe_rel(repo, build_path) + '.before', safe_rel(repo, build_path) + '.after'))

    (out / 'dd067r_patch_preview.diff').write_text('\n'.join(diff_texts), encoding='utf-8')
    (out / 'dd067r_registration_candidate_blocks.txt').write_text(candidate_text, encoding='utf-8')

    files_patched = 0
    backup_dir = ''
    if args.apply_patch and failures == 0:
        backup_dir_path = backup_root / f'{args.run_id}_{_dt.datetime.now().strftime("%Y%m%d-%H%M%S")}'
        backup_file(repo, backup_dir_path, reg_path)
        backup_file(repo, backup_dir_path, build_path)
        backup_dir = str(backup_dir_path)
        if reg_new != reg_old:
            write_text(reg_path, reg_new)
            files_patched += 1
        if build_new != build_old:
            write_text(build_path, build_new)
            files_patched += 1

    applied = int(args.apply_patch and failures == 0)
    if args.apply_patch:
        status = 'DDICT_LOCAL_PATTERN_REGISTRATION_BUILD_PATCH_APPLIED_BUILD_REQUIRED' if failures == 0 else 'DDICT_LOCAL_PATTERN_REGISTRATION_BUILD_PATCH_REVIEW'
    else:
        status = 'DDICT_LOCAL_PATTERN_REGISTRATION_BUILD_PATCH_READY' if failures == 0 else 'DDICT_LOCAL_PATTERN_REGISTRATION_BUILD_PATCH_REVIEW'

    gate_rows = [
        {'gate': 'dd066r_ready', 'expected': EXPECTED_DD066R_STATUS, 'observed': dd066r_manifest.get('status', ''), 'pass': int(dd066r_manifest.get('status') == EXPECTED_DD066R_STATUS)},
        {'gate': 'registration_target_exists', 'expected': 1, 'observed': int(reg_path.exists()), 'pass': int(reg_path.exists())},
        {'gate': 'build_target_exists', 'expected': 1, 'observed': int(build_path.exists()), 'pass': int(build_path.exists())},
        {'gate': 'smoke_target_exists', 'expected': 1, 'observed': int(smoke_path.exists()), 'pass': int(smoke_path.exists())},
        {'gate': 'patch_parts_possible', 'expected': 1, 'observed': int(failures == 0), 'pass': int(failures == 0)},
        {'gate': 'patch_applied_when_requested', 'expected': int(args.apply_patch), 'observed': applied, 'pass': int((not args.apply_patch) or applied == 1)},
    ]
    boundary_rows = [
        {'boundary': 'local_pattern_guarded_patch', 'observed': 1, 'required': 1, 'pass': 1},
        {'boundary': 'cxx_source_or_build_edits', 'observed': files_patched, 'required': files_patched if args.apply_patch else 0, 'pass': int((args.apply_patch and files_patched >= 0) or (not args.apply_patch and files_patched == 0))},
        {'boundary': 'active_catalog_mutation', 'observed': 0, 'required': 0, 'pass': 1},
        {'boundary': 'dbf_append_replace_delete_pack_zap', 'observed': 0, 'required': 0, 'pass': 1},
        {'boundary': 'cdx_lmdb_create_rebuild', 'observed': 0, 'required': 0, 'pass': 1},
        {'boundary': 'help_meta_cmdhelpchk_mutation', 'observed': 0, 'required': 0, 'pass': 1},
        {'boundary': 'catalog_regeneration', 'observed': 0, 'required': 0, 'pass': 1},
        {'boundary': 'manual_row_repair', 'observed': 0, 'required': 0, 'pass': 1},
    ]
    write_csv(out / 'dd067r_patch_part_ledger.csv', patch_rows, ['patch_part','target','patch_needed','patch_possible','reason','insert_after','new_entry'])
    write_csv(out / 'dd067r_gate_ledger.csv', gate_rows, ['gate','expected','observed','pass'])
    write_csv(out / 'dd067r_review_rows.csv', review_rows, ['issue','detail'])
    write_csv(out / 'dd067r_no_mutation_boundary_ledger.csv', boundary_rows, ['boundary','observed','required','pass'])

    report_lines = [
        '# DD-067R Local-Pattern DDICT Registration / Build Patch Repair',
        '',
        f'Run id: `{args.run_id}`',
        f'Status: **{status}**',
        f'Created UTC: `{utc_now()}`',
        '',
        '## Purpose',
        '',
        'DD-067R repairs DD-067 by using local-pattern probes for command registration and CMake source inclusion.',
        '',
        '## Targets',
        '',
        f'- Registration: `{safe_rel(repo, reg_path)}`',
        f'- Build: `{safe_rel(repo, build_path)}`',
        f'- Smoke: `{safe_rel(repo, smoke_path)}`',
        '',
        '## Result',
        '',
        f'- Apply requested: **{int(args.apply_patch)}**',
        f'- Applied: **{applied}**',
        f'- Files patched: **{files_patched}**',
        f'- Backup dir: `{backup_dir}`',
        '',
        '## Boundary',
        '',
        'DD-067R does not mutate the active catalog, DBF/CDX/LMDB artifacts, HELP/META/CMDHELPCHK, catalog content, or manual rows.',
        '',
    ]
    (out / 'DD067R_LOCAL_PATTERN_DDICT_REGISTRATION_BUILD_PATCH_REPORT.md').write_text('\n'.join(report_lines), encoding='utf-8')

    manifest = {
        'contract': 'dd067r_local_pattern_ddict_registration_build_patch_v0',
        'run_id': args.run_id,
        'created_utc': utc_now(),
        'status': status,
        'repo_root': str(repo),
        'profiles': args.profile,
        'registration_target': safe_rel(repo, reg_path),
        'build_target': safe_rel(repo, build_path),
        'smoke_target': safe_rel(repo, smoke_path),
        'apply_patch': int(args.apply_patch),
        'applied': applied,
        'files_patched': files_patched,
        'backup_dir': backup_dir,
        'failures': failures,
        'active_catalog_mutation': 0,
        'help_meta_cmdhelpchk_mutation': 0,
        'next_recommended_action': 'Build DotTalk++ and run DDICT HELP smoke if patch applied; otherwise inspect review rows and candidate blocks.',
    }
    write_json(out / 'dd067r_local_pattern_ddict_registration_build_patch_manifest.json', manifest)
    print(f"DD-067R local-pattern DDICT patch manifest: {out / 'dd067r_local_pattern_ddict_registration_build_patch_manifest.json'}")
    print(f"status: {status}; applied: {applied}; files_patched: {files_patched}; failures: {failures}")
    return 2 if (args.fail_on_review and failures) else 0

if __name__ == '__main__':
    raise SystemExit(main())
