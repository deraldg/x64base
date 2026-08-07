#!/usr/bin/env python3
"""
source_contract_classifier_tuning_v0.py

REPORT_ONLY classifier tuning analysis for SelfDoc source-contract inventory.
Run from D:\code\ccode.

Reads source_contracts_inventory reports and writes:
  dottalkpp\docs\generated\reports\source_contract_classifier_tuning_v0.md
  dottalkpp\docs\generated\reports\source_contract_classifier_tuning_v0.csv

No source edits. No DBF writes. No CMDHELPCHK changes. No HELP DATA rebuild. No repairs.
"""
from __future__ import annotations

import argparse, csv, json
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPORT_DIRS = (Path('dottalkpp')/'docs'/'generated'/'reports', Path('docs')/'generated'/'reports')
INVENTORY_JSON = 'source_contracts_inventory.json'
INVENTORY_CSV = 'source_contracts_inventory.csv'
REVIEW_MD = 'source_contract_inventory_review_v0.md'
OUTPUT_MD = 'source_contract_classifier_tuning_v0.md'
OUTPUT_CSV = 'source_contract_classifier_tuning_v0.csv'

CORE_FIELDS = {
    'command','commands','owner','category','family','summary','usage','syntax','examples','example',
    'notes','note','related','status','aliases','alias','shortcuts','shortcut','subcommands','subcommand',
    'arguments','argument','returns','errors','warnings'
}

SAFETY_EXTENSION_FIELDS = {
    'usage-access','effect','mutates','risk','noargs','requires_open_table','requires_current_record',
    'requires_active_order','requires_current_area','requires_selected_area','requires_workspace','requires_file',
    'requires_index','requires_memo','requires_sqlite','mutates_table_data','mutates_cursor',
    'mutates_record_pointer','mutates_order_state','mutates_index_metadata','mutates_session','mutates_setting',
    'mutates_session_ui','mutates_filesystem','mutates_beta_status','mutates_continue_state','writes_dbf_record',
    'writes_dbf_records','writes_table_data','writes_table_buffer','writes_memo','writes_files','writes_filesystem',
    'writes_lmdb_environment','reads_files','reads_index_file','reads_table_records','reads_current_record',
    'reads_current_table','reads_open_work_areas','appends_records','updates_indexes','updates_index',
    'index_maintenance','marks_dirty','marks_stale_field','clears_order_state','clears_console','clears_all_relations',
    'clears_relations_for_table','closes_area','closes_current_area','closes_memo_backend','opens_area','creates_files',
    'creates_index_file','creates_table','overwrites_files','overwrites_index_file','possible_overwrite',
    'archives_existing_environment','drops_or_recreates_lmdb_databases','raw_path_skips_inline_index_update',
    'one_lock_batch','dirty_prompt_gate','resets_table_buffer_state','clears_table_buffer_changes',
    'partial_commit_possible','record_locking','cdx_lmdb_rebuild','scans_records','cursor_restore',
    'restores_cursor_best_effort','changes_current_area_cursor','separate_storage_engine','table_buffer_semantics',
    'auto_is_conservative','default_path_uses_indexes_slot','default_path_uses_order_state',
    'manage_cdx_index_container_metadata','manage_cnx_index_container_metadata','diagnostic_tree_walk','interactive',
    'audible_effect','evaluates_expression','executes_host_command','launches_external_process','delegates_to_append',
    'delegates_to_browse_module','delegates_to_calcwrite','delegates_to_create','delegates_to_delete',
    'delegates_to_replace','contract','no_open_area_allowed','staged_edits'
}
FIELD_ALIASES = {'usage_access':'usage-access','usageaccess':'usage-access','usage-access':'usage-access','no_args':'noargs','no-args':'noargs'}
ACCEPTED_FIELDS = CORE_FIELDS | SAFETY_EXTENSION_FIELDS | set(FIELD_ALIASES.keys())

@dataclass
class Record:
    path: str
    status: str
    has_contract: bool
    contract_count: int = 0
    fields_present: list[str] = field(default_factory=list)
    missing_recommended_fields: list[str] = field(default_factory=list)
    malformed_lines: list[str] = field(default_factory=list)
    unknown_fields: list[str] = field(default_factory=list)
    command_names: list[str] = field(default_factory=list)
    escrow_candidate: bool = False
    notes: list[str] = field(default_factory=list)

@dataclass
class TunedRecord:
    path: str
    lane: str
    current_status: str
    has_contract: bool
    old_escrow_candidate: bool
    recommended_family: str
    action_class: str
    valid_after_tuning: bool
    actionable_usage_backlog: bool
    missing_after_tuning: list[str]
    unrecognized_after_tuning: list[str]
    notes: list[str]

def parse_bool(v: Any) -> bool:
    if isinstance(v, bool): return v
    return str(v).strip().lower() in {'true','1','yes','y'}

def parse_list(v: Any) -> list[str]:
    if v is None: return []
    if isinstance(v, list): return [str(x).strip() for x in v if str(x).strip()]
    s = str(v).strip()
    if not s: return []
    sep = ';' if ';' in s else ',' if ',' in s else None
    return [p.strip() for p in s.split(sep) if p.strip()] if sep else [s]

def normalize_field(name: str) -> str:
    k = name.strip().lower().replace(' ', '_')
    return FIELD_ALIASES.get(k, k)

def find_report_dir(root: Path, explicit: str|None) -> Path:
    if explicit:
        d = root/explicit
        if not d.is_dir(): raise SystemExit(f'Report directory not found: {d}')
        return d
    for rel in REPORT_DIRS:
        d = root/rel
        if (d/INVENTORY_JSON).is_file() or (d/INVENTORY_CSV).is_file(): return d
    raise SystemExit('Could not find source contract inventory reports.')

def load_records(report_dir: Path):
    notes=[]; records=[]; summary={}
    jp=report_dir/INVENTORY_JSON; cp=report_dir/INVENTORY_CSV; rp=report_dir/REVIEW_MD
    if jp.is_file():
        payload=json.loads(jp.read_text(encoding='utf-8'))
        summary=dict(payload.get('summary', {}))
        items=payload.get('records', [])
        notes.append(f'read JSON: {jp}')
    elif cp.is_file():
        with cp.open('r', encoding='utf-8', newline='') as f: items=list(csv.DictReader(f))
        notes.append(f'read CSV: {cp}')
    else:
        raise SystemExit(f'Missing inventory JSON/CSV in {report_dir}')
    for item in items:
        records.append(Record(
            path=str(item.get('path','')), status=str(item.get('status','')), has_contract=parse_bool(item.get('has_contract', False)),
            contract_count=int(item.get('contract_count',0) or 0), fields_present=parse_list(item.get('fields_present')),
            missing_recommended_fields=parse_list(item.get('missing_recommended_fields')), malformed_lines=parse_list(item.get('malformed_lines')),
            unknown_fields=parse_list(item.get('unknown_fields')), command_names=parse_list(item.get('command_names')),
            escrow_candidate=parse_bool(item.get('escrow_candidate', False)), notes=parse_list(item.get('notes'))))
    notes.append(f"review companion {'present' if rp.is_file() else 'missing'}: {rp}")
    return summary, records, notes

def norm(path: str) -> str: return path.replace('\\','/').lower()
def filename(path: str) -> str: return norm(path).rsplit('/',1)[-1]

def lane_for_path(path: str) -> str:
    p=norm(path); name=filename(path)
    if p.startswith('src/cli/'):
        if name.startswith('cmd_') or 'shell_commands' in name or 'cmdhelp' in name or 'help' in name: return 'cli_command_help_surface'
        return 'cli_support'
    if p.startswith('include/cli/'): return 'cli_headers'
    if p.startswith('src/xexpr/') or p.startswith('include/xexpr'): return 'expression_engine'
    if p.startswith('src/xbase/') or p.startswith('include/xbase') or p=='include/xbase.hpp': return 'xbase_storage_engine'
    if p.startswith('src/xindex/') or p.startswith('include/xindex'): return 'index_engine'
    if p.startswith('src/memo/') or p.startswith('include/memo'): return 'memo_engine'
    if p.startswith('src/tv/') or p.startswith('include/tv'): return 'tui_tv_layer'
    if p.startswith('bindings/') or p.startswith('src/python') or 'pydottalk' in p: return 'bindings_python'
    if p.startswith('dev/') or p.startswith('tests/') or '/test' in p: return 'test_dev_harness'
    if p.endswith('.hpp') or p.endswith('.h'): return 'public_or_shared_header'
    return 'other_source'

def command_usage_target(path: str) -> bool:
    p=norm(path); name=filename(path)
    return (p.startswith('src/cli/cmd_') and name.endswith('.cpp')) or (p.startswith('src/cli/') and name in {'shell_commands.cpp','cmdhelp.cpp','cmd_help.cpp','cmd_dothelp.cpp','helpdata_cmdhelp_bridge.cpp'})

def recommended_family(path: str) -> str:
    p=norm(path); name=filename(path); lane=lane_for_path(path)
    if command_usage_target(path): return '@dottalk.usage v1'
    if lane=='expression_engine': return 'selfdoc.function_contract' if (name.startswith('fn_') or 'function' in name or p.startswith('src/')) else 'selfdoc.api_contract'
    if lane in {'xbase_storage_engine','index_engine','memo_engine'}: return 'selfdoc.api_contract' if p.startswith('include/') else 'selfdoc.engine_contract'
    if lane=='tui_tv_layer': return 'selfdoc.ui_contract'
    if lane=='bindings_python': return 'selfdoc.binding_contract'
    if lane=='test_dev_harness': return 'selfdoc.test_contract or exclude_from_usage_contract'
    if lane in {'cli_headers','public_or_shared_header'}: return 'selfdoc.api_contract or exclude_from_usage_contract'
    return 'manual_classification'

def missing_after_tuning(rec: Record) -> list[str]:
    if not rec.has_contract: return ['contract']
    fields={normalize_field(f) for f in rec.fields_present}
    missing=[]
    if not ({'command','commands'} & fields): missing.append('command_or_commands')
    if 'summary' not in fields: missing.append('summary')
    if not ({'usage','syntax'} & fields): missing.append('usage_or_syntax')
    return missing

def unrecognized_after_tuning(rec: Record) -> list[str]:
    fields={normalize_field(f) for f in rec.fields_present}
    return sorted(f for f in fields if f not in ACCEPTED_FIELDS)

def tune_record(rec: Record) -> TunedRecord:
    lane=lane_for_path(rec.path); family=recommended_family(rec.path)
    missing=missing_after_tuning(rec); unrec=unrecognized_after_tuning(rec); malformed=bool(rec.malformed_lines)
    actionable=command_usage_target(rec.path) and not rec.has_contract
    notes=[]
    if actionable:
        action='action_required_add_command_usage_contract'; notes.append('true missing command/help usage candidate')
    elif command_usage_target(rec.path) and rec.has_contract:
        if missing or unrec or malformed:
            action='review_existing_command_contract_shape'
            if missing: notes.append('missing after tuning: '+', '.join(missing))
            if unrec: notes.append('unrecognized after tuning: '+', '.join(unrec))
            if malformed: notes.append('malformed lines remain')
        else:
            action='accepted_existing_command_contract'; notes.append('existing command usage contract accepted after tuning')
    elif family.startswith('selfdoc.api_contract'): action='alternate_contract_api_or_exclude'
    elif family=='selfdoc.function_contract': action='alternate_contract_function'
    elif family=='selfdoc.engine_contract': action='alternate_contract_engine'
    elif family=='selfdoc.ui_contract': action='alternate_contract_ui'
    elif family=='selfdoc.binding_contract': action='alternate_contract_binding'
    elif family.startswith('selfdoc.test_contract'): action='alternate_contract_test_or_exclude'
    else: action='manual_classification'
    valid=bool(rec.has_contract and not missing and not unrec and not malformed)
    return TunedRecord(rec.path,lane,rec.status,rec.has_contract,rec.escrow_candidate,family,action,valid,actionable,missing,unrec,notes)

def md_escape(v: object) -> str: return str(v).replace('|','\\|').replace('\n',' ')

def write_csv_report(path: Path, tuned: list[TunedRecord]):
    fields=['path','lane','current_status','has_contract','old_escrow_candidate','recommended_family','action_class','valid_after_tuning','actionable_usage_backlog','missing_after_tuning','unrecognized_after_tuning','notes']
    with path.open('w', encoding='utf-8', newline='') as f:
        w=csv.DictWriter(f, fieldnames=fields); w.writeheader()
        for r in tuned:
            w.writerow({**{k:getattr(r,k) for k in fields if k not in {'missing_after_tuning','unrecognized_after_tuning','notes'}}, 'missing_after_tuning':'; '.join(r.missing_after_tuning), 'unrecognized_after_tuning':'; '.join(r.unrecognized_after_tuning), 'notes':'; '.join(r.notes)})

def write_md_report(path: Path, records: list[Record], tuned: list[TunedRecord], load_notes: list[str], csv_path: Path):
    action_counts=Counter(t.action_class for t in tuned); family_counts=Counter(t.recommended_family for t in tuned); lane_counts=Counter(t.lane for t in tuned); old_counts=Counter(r.status for r in records)
    missing_counts=Counter(x for t in tuned for x in t.missing_after_tuning); unrec_counts=Counter(x for t in tuned for x in t.unrecognized_after_tuning)
    actionable=[t for t in tuned if t.actionable_usage_backlog]; accepted=[t for t in tuned if t.action_class=='accepted_existing_command_contract']; review=[t for t in tuned if t.action_class=='review_existing_command_contract_shape']
    lines=[]
    a=lines.append
    a('# Source Contract Classifier Tuning v0'); a(''); a(f"Generated UTC: `{datetime.now(timezone.utc).isoformat()}`"); a(''); a('Safety class: `REPORT_ONLY`'); a('')
    a('## Scope'); a(''); a('This report defines classifier tuning rules for SelfDoc source contracts. It does not edit source files, write DBFs, modify CMDHELPCHK, rebuild HELP DATA, or repair headers.'); a('')
    a('Inputs read:'); a(''); [a(f'- `{n}`') for n in load_notes]; a(''); a('Outputs written:'); a(''); a(f'- `{path}`'); a(f'- `{csv_path}`'); a('')
    a('## Executive summary'); a(''); a(f'- Records reviewed: `{len(records)}`'); a(f'- Previous broad escrow candidates: `{sum(1 for r in records if r.escrow_candidate)}`'); a(f'- Actionable missing command/help usage contracts after tuning: `{len(actionable)}`'); a(f'- Existing command contracts accepted after tuning: `{len(accepted)}`'); a(f'- Existing command contracts needing shape review after tuning: `{len(review)}`'); a('')
    a('The core tuning decision is that `usage` OR `syntax` satisfies the command shape field. Existing rich safety fields such as `effect`, `mutates`, `risk`, and `usage-access` should be recognized as valid v1 extension metadata, not unknown defects.'); a('')
    a('## Accepted `@dottalk.usage v1` vocabulary'); a(''); a('### Core fields'); a(''); [a(f'- `{f}`') for f in sorted(CORE_FIELDS)]; a(''); a('### Safety/effect extension fields'); a(''); [a(f'- `{f}`') for f in sorted(SAFETY_EXTENSION_FIELDS)]; a('')
    a('### Required/recommended shape'); a(''); a('```text'); a('required identity: command OR commands'); a('required summary : summary'); a('required shape   : usage OR syntax'); a('recommended      : owner, category, status, risk, mutates, related'); a('extensions       : accepted safety/effect fields listed above'); a('```'); a('')
    a('## Contract family recommendations'); a(''); a('| Family | Applies to |'); a('|---|---|'); a('| `@dottalk.usage v1` | `src\\cli\\cmd_*.cpp` and selected command/help bridge files |'); a('| `selfdoc.function_contract` | function-layer files such as `fn_*.cpp`, function registry, xexpr function surfaces |'); a('| `selfdoc.engine_contract` | xbase, xindex, memo, storage/backend implementation files |'); a('| `selfdoc.api_contract` | headers and declaration/API companion files |'); a('| `selfdoc.ui_contract` | Turbo Vision / UI layer files |'); a('| `selfdoc.binding_contract` | pydottalk / language binding files |'); a('| `selfdoc.test_contract` | tests, dev harnesses, probes, smokes |'); a('| `exclude_from_usage_contract` | generated, purely internal, or irrelevant files after review |'); a('')
    def table(title, headers, rows):
        a(f'## {title}'); a(''); a('| ' + ' | '.join(headers) + ' |'); a('|' + '|'.join(['---']*len(headers)) + '|'); [a('| ' + ' | '.join(str(x) for x in row) + ' |') for row in rows]; a('')
    table('Old inventory status counts',['Old status','Count'], [(f'`{md_escape(k)}`',v) for k,v in old_counts.most_common()])
    table('Tuned action counts',['Action class','Count'], [(f'`{md_escape(k)}`',v) for k,v in action_counts.most_common()])
    table('Recommended family counts',['Recommended family','Count'], [(f'`{md_escape(k)}`',v) for k,v in family_counts.most_common()])
    table('Lane counts',['Lane','Count'], [(f'`{md_escape(k)}`',v) for k,v in lane_counts.most_common()])
    table('Missing fields after tuning',['Missing tuned field','Count'], [(f'`{md_escape(k)}`',v) for k,v in missing_counts.most_common()] or [('None',0)])
    table('Unrecognized fields after tuning',['Unrecognized field','Count'], [(f'`{md_escape(k)}`',v) for k,v in unrec_counts.most_common(50)] or [('None',0)])
    a('## Actionable missing command/help usage contracts'); a('')
    if actionable:
        a('| Path | Lane | Recommended family |'); a('|---|---|---|')
        for r in sorted(actionable, key=lambda x:x.path.lower()): a(f'| `{md_escape(r.path)}` | `{md_escape(r.lane)}` | `{md_escape(r.recommended_family)}` |')
    else: a('No actionable missing command/help usage contracts found.')
    a('')
    a('## Existing command contracts needing shape review after tuning'); a('')
    if review:
        a('| Path | Missing after tuning | Unrecognized after tuning | Notes |'); a('|---|---|---|---|')
        for r in sorted(review, key=lambda x:x.path.lower())[:200]: a(f'| `{md_escape(r.path)}` | {md_escape(", ".join(r.missing_after_tuning))} | {md_escape(", ".join(r.unrecognized_after_tuning))} | {md_escape("; ".join(r.notes))} |')
        if len(review)>200: a(f'| ... | ... | ... | `{len(review)-200} more omitted from markdown table` |')
    else: a('No existing command contracts need shape review after tuning.')
    a(''); a('## Classifier tuning rules to implement later'); a('')
    for item in ['Restrict required `@dottalk.usage v1` targets to command/help surfaces, not all source files.','Accept `usage` OR `syntax` as the command shape field.','Recognize rich safety/effect fields as valid extension metadata.','Normalize `usage_access` and `usage-access` internally without rewriting source.','Keep broad escrow reporting, but add a narrower actionable backlog class.','Emit alternate contract family recommendations for function, engine, API/header, UI, binding, and test/probe files.','Continue hashing exact header text; no normalization before hashing.','Do not repair or rewrite source contracts during classifier tuning.']:
        a(f'{len([l for l in lines if l.startswith(str(1))])}. {item}' if False else f'- {item}')
    a(''); a('## Non-mutation confirmation'); a(''); [a(f'- {x}') for x in ['No source files edited.','No DBFs written.','No HELP DATA rebuilt.','No CMDHELPCHK implementation or configuration modified.','No source contract headers repaired.','This report writes markdown and CSV only.']]
    path.write_text('\n'.join(lines)+'\n', encoding='utf-8')

def parse_args():
    p=argparse.ArgumentParser(description='Produce SelfDoc source contract classifier tuning v0 report.')
    p.add_argument('--root', default='.', help='Project root. Default: current directory, normally D:\\code\\ccode.')
    p.add_argument('--report-dir', default=None, help='Optional report directory relative to root.')
    return p.parse_args()

def main() -> int:
    args=parse_args(); root=Path(args.root).resolve(); report_dir=find_report_dir(root,args.report_dir)
    summary, records, notes=load_records(report_dir); tuned=[tune_record(r) for r in records]
    out_md=report_dir/OUTPUT_MD; out_csv=report_dir/OUTPUT_CSV
    write_csv_report(out_csv,tuned); write_md_report(out_md,records,tuned,notes,out_csv)
    print('SelfDoc source contract classifier tuning v0 complete.'); print(f'Read report directory: {report_dir}'); print(f'Records reviewed: {len(records)}'); print(f'Wrote: {out_md}'); print(f'Wrote: {out_csv}'); print('No source files were edited.'); print('No DBFs were written.'); print('CMDHELPCHK was not modified.'); print('HELP DATA was not rebuilt.'); print('No repairs were made.')
    return 0

if __name__=='__main__': raise SystemExit(main())
