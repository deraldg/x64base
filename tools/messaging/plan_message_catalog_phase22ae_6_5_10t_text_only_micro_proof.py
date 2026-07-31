#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, json, hashlib, shutil
from datetime import datetime, timezone
from pathlib import Path

STATUS_GREEN='MESSAGE_CATALOG_PHASE22AE_6_5_10T_TEXT_ONLY_ACTIVE_IMPORT_MICRO_PROOF_PLAN_GREEN_SOURCE_HELD'
STATUS_BLOCKED='MESSAGE_CATALOG_PHASE22AE_6_5_10T_TEXT_ONLY_ACTIVE_IMPORT_MICRO_PROOF_PLAN_BLOCKED'
NEXT_GATE='HOLD_OR_AUTHORIZE_PHASE22AE_6_5_10U_TEXT_ONLY_ACTIVE_BASELINE_ROUNDTRIP_EXECUTION_PACKAGE'
REPORT_DIR=Path('docs/messaging/reports')
APPLY_ROOT=Path('docs/messaging/apply/phase22ae_6_5_10t_text_only_active_import_micro_proof_plan_v1')
TEXT70=Path('docs/messaging/apply/phase22ae_6_5_10_guarded_active_promotion_execution_v1/import/system_message_text_active_promotion_full_state.csv')
TEXT70_SANDBOX=Path('docs/messaging/sandbox/phase22ae_6_5_6_canonical_field_map_zap_import_v1/import/system_message_text_canonical_field_map_full_state.csv')
ACTIVE_TEXT=Path('dottalkpp/data/messaging/SYSTEM_MESSAGE_TEXT.dbf')
ACTIVE_TEXT_INDEX=Path('dottalkpp/data/indexes/messaging/SYSTEM_MESSAGE_TEXT.cdx')
ACTIVE_TEXT_LMDB=Path('dottalkpp/data/lmdb/messaging/SYSTEM_MESSAGE_TEXT.cdx.d')

def read_csv(path: Path):
    if not path.exists(): return []
    with path.open('r', encoding='utf-8-sig', newline='') as f: return list(csv.DictReader(f))

def first_row(path: Path):
    rows=read_csv(path); return rows[0] if rows else {}

def write_csv(path: Path, rows, fields):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8', newline='') as f:
        w=csv.DictWriter(f, fieldnames=fields, lineterminator='\n', extrasaction='ignore')
        w.writeheader()
        for r in rows: w.writerow({k:r.get(k,'') for k in fields})

def rel(path: Path, repo: Path):
    try: return str(path.relative_to(repo)).replace('\\','/')
    except Exception: return str(path).replace('\\','/')

def sha256_file(path: Path):
    if not path.exists() or not path.is_file(): return ''
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024), b''): h.update(chunk)
    return h.hexdigest()

def hash_dir(path: Path):
    if not path.exists() or not path.is_dir(): return '',0,0
    files=sorted(p for p in path.rglob('*') if p.is_file())
    h=hashlib.sha256(); total=0
    for p in files:
        h.update(str(p.relative_to(path)).replace('\\','/').encode())
        h.update(sha256_file(p).encode())
        total += p.stat().st_size
    return h.hexdigest(), len(files), total

def file_info(repo: Path, role: str, path: Path):
    p=repo/path
    if p.is_dir():
        h,n,b=hash_dir(p); return {'ROLE':role,'PATH':rel(p,repo),'EXISTS':1,'KIND':'dir','BYTES':b,'SHA256':h,'FILES':n}
    if p.is_file(): return {'ROLE':role,'PATH':rel(p,repo),'EXISTS':1,'KIND':'file','BYTES':p.stat().st_size,'SHA256':sha256_file(p),'FILES':1}
    return {'ROLE':role,'PATH':rel(p,repo),'EXISTS':0,'KIND':'missing','BYTES':0,'SHA256':'','FILES':0}

def savepoint_present(repo: Path, savepoint_id: str):
    latest=''; latest_path=repo/REPORT_DIR/'message_savepoint_latest_v1.json'
    if latest_path.exists():
        try: latest=json.loads(latest_path.read_text(encoding='utf-8')).get('savepoint_id','')
        except Exception: latest=''
    journal=repo/'docs/messaging/MESSAGING_SAVEPOINT_JOURNAL.md'
    text=journal.read_text(encoding='utf-8', errors='replace') if journal.exists() else ''
    return latest==savepoint_id or savepoint_id in text, latest

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--repo-root', required=True); ap.add_argument('--replace-existing-plan', action='store_true'); args=ap.parse_args()
    repo=Path(args.repo_root).resolve(); reports=repo/REPORT_DIR; reports.mkdir(parents=True, exist_ok=True)
    s10=first_row(reports/'message_catalog_phase22ae_6_5_10s_status_summary_v1.csv')
    sp10s, latest=savepoint_present(repo, 'MSG-022AE.6.5.10S')
    apply_root=repo/APPLY_ROOT
    gates=[]; failures=0
    def gate(name, ok, detail):
        nonlocal failures; gates.append({'GATE':name,'STATUS':'PASS' if ok else 'FAIL','DETAIL':str(detail)}); failures += 0 if ok else 1
    gate('PHASE22AE_6_5_10S_GREEN', s10.get('STATUS')=='MESSAGE_CATALOG_PHASE22AE_6_5_10S_ACTIVE_TEXT_IMPORT_FAILURE_FORENSIC_REVIEW_GREEN_SOURCE_HELD', s10.get('STATUS','missing'))
    gate('MSG_022AE_6_5_10S_SAVEPOINT_PRESENT', sp10s, latest)
    gate('ACTIVE_PROMOTION_RETRY_CLOSED_IN_10S', s10.get('ACTIVE_PROMOTION_RETRY_ALLOWED')=='0', s10.get('ACTIVE_PROMOTION_RETRY_ALLOWED','missing'))
    gate('TEXT_IMPORT_CSVS_IDENTICAL_IN_10S', s10.get('TEXT_IMPORT_CSVS_IDENTICAL')=='1', s10.get('TEXT_IMPORT_CSVS_IDENTICAL','missing'))
    gate('ACTIVE_TEXT_BASELINE_60_AFTER_ROLLBACK', s10.get('ACTIVE_TEXT_AFTER_ROLLBACK_RECORD_COUNT')=='60', s10.get('ACTIVE_TEXT_AFTER_ROLLBACK_RECORD_COUNT','missing'))
    gate('TEXT70_ACTIVE_CSV_EXISTS', (repo/TEXT70).exists(), rel(repo/TEXT70,repo))
    gate('TEXT70_SANDBOX_CSV_EXISTS', (repo/TEXT70_SANDBOX).exists(), rel(repo/TEXT70_SANDBOX,repo))
    gate('APPLY_ROOT_NOT_EXISTING_OR_REPLACE_ALLOWED', (not apply_root.exists()) or args.replace_existing_plan, rel(apply_root,repo))
    text70=read_csv(repo/TEXT70); headers=list(text70[0].keys()) if text70 else []
    baseline60=text70[:60] if len(text70)>=60 else []; candidate10=text70[60:70] if len(text70)>=70 else []
    gate('TEXT70_CSV_HAS_70_ROWS', len(text70)==70, len(text70))
    gate('DERIVED_BASELINE60_HAS_60_ROWS', len(baseline60)==60, len(baseline60))
    gate('DERIVED_CANDIDATE10_HAS_10_ROWS', len(candidate10)==10, len(candidate10))
    artifacts=[file_info(repo,'active_text_dbf_current_baseline',ACTIVE_TEXT), file_info(repo,'active_text_index',ACTIVE_TEXT_INDEX), file_info(repo,'active_text_lmdb',ACTIVE_TEXT_LMDB), file_info(repo,'source_text70_active_csv',TEXT70), file_info(repo,'source_text70_sandbox_csv',TEXT70_SANDBOX)]
    candidate_artifacts=[]; baseline_rel=''; candidate_rel=''; template_rel=''; status=STATUS_BLOCKED
    if failures==0:
        if apply_root.exists() and args.replace_existing_plan: shutil.rmtree(apply_root)
        (apply_root/'import').mkdir(parents=True, exist_ok=True); (apply_root/'templates').mkdir(parents=True, exist_ok=True); (apply_root/'rollback').mkdir(parents=True, exist_ok=True)
        baseline_path=apply_root/'import/system_message_text_baseline60_roundtrip.csv'
        candidate_path=apply_root/'import/system_message_text_candidate10_only_reference.csv'
        full70_path=apply_root/'import/system_message_text_full70_reference.csv'
        write_csv(baseline_path, baseline60, headers); write_csv(candidate_path, candidate10, headers); shutil.copy2(repo/TEXT70, full70_path)
        baseline_rel=rel(baseline_path,repo); candidate_rel=rel(candidate_path,repo)
        candidate_artifacts=[
            {'ROLE':'BASELINE60_ROUNDTRIP_CSV','PATH':baseline_rel,'ROWS':len(read_csv(baseline_path)),'BYTES':baseline_path.stat().st_size,'SHA256':sha256_file(baseline_path),'PURPOSE':'Future 10U active text-only roundtrip input; restore backup after proof.'},
            {'ROLE':'CANDIDATE10_REFERENCE_CSV','PATH':candidate_rel,'ROWS':len(read_csv(candidate_path)),'BYTES':candidate_path.stat().st_size,'SHA256':sha256_file(candidate_path),'PURPOSE':'Reference only; not for first micro proof execution.'},
            {'ROLE':'FULL70_REFERENCE_CSV','PATH':rel(full70_path,repo),'ROWS':len(read_csv(full70_path)),'BYTES':full70_path.stat().st_size,'SHA256':sha256_file(full70_path),'PURPOSE':'Reference copy from failed active/full sandbox-proven text path.'},
        ]
        template=apply_root/'templates/MESSAGE_CATALOG_PHASE22AE_6_5_10U_TEXT_ONLY_ACTIVE_BASELINE_ROUNDTRIP_TEMPLATE.dts.disabled'
        template.write_text('\n'.join([
            '* DISABLED TEMPLATE ONLY - DO NOT EXECUTE IN 10T',
            '* Future 10U must backup active text artifacts and restore exact backup after proof, regardless of success.',
            '* No QUIT here; quit manually in interactive runs.',
            '',
            f'* USE {(repo/ACTIVE_TEXT).resolve().as_posix()}', '* ZAP',
            f'* USE {(repo/ACTIVE_TEXT).resolve().as_posix()}', f'* IMPORT {baseline_path.resolve().as_posix()}',
            f'* USE {(repo/ACTIVE_TEXT).resolve().as_posix()}', '* COUNT', '* LIST ALL',
            '', '* Restore exact backup after readback. Do not leave proof-mutated active artifacts in place.'
        ]), encoding='utf-8')
        template_rel=rel(template,repo); status=STATUS_GREEN
    plan_rows=[
        {'STEP':1,'PHASE':'PRECONDITION','ACTION':'REQUIRE_10S_GREEN_AND_SAVEPOINT','DETAIL':'10S must show rollback baseline 60, identical CSVs, and retry closed.','MUTATES_ACTIVE':0},
        {'STEP':2,'PHASE':'CANDIDATE_SOURCE','ACTION':'DERIVE_BASELINE60_FROM_PROVEN_FULL70_CSV','DETAIL':'Use first 60 rows of canonical full-state text CSV as baseline roundtrip input.','MUTATES_ACTIVE':0},
        {'STEP':3,'PHASE':'FUTURE_10U_EXECUTION_SHAPE','ACTION':'TEXT_ONLY_ACTIVE_ROUNDTRIP','DETAIL':'Future 10U should test only SYSTEM_MESSAGE_TEXT, not SYSTEM_MESSAGES and not candidate 70-row promotion.','MUTATES_ACTIVE':1},
        {'STEP':4,'PHASE':'FUTURE_10U_DISCIPLINE','ACTION':'BACKUP_ZAP_REOPEN_IMPORT_COUNT_LIST_RESTORE','DETAIL':'Backup first, USE/ZAP/USE/IMPORT baseline60, COUNT/LIST, then restore backup always.','MUTATES_ACTIVE':1},
        {'STEP':5,'PHASE':'HOLD','ACTION':'NO_ACTIVE_EXECUTION_IN_10T','DETAIL':'10T produces plan/candidate files only; 10U requires explicit authorization.','MUTATES_ACTIVE':0},
    ]
    risks=[
        {'RISK':'active_text_roundtrip_can_fail_like_6_5_10','MITIGATION':'Use text-only baseline60 proof and restore exact backup after readback.'},
        {'RISK':'logical_catalog_changes_left_in_active_path','MITIGATION':'Restore backup regardless of result; 10U proof is diagnostic only.'},
        {'RISK':'index_lmdb_binding_or_flush_effects','MITIGATION':'10U must fingerprint DBF/CDX/LMDB before/after and capture DotTalk++ runtime evidence.'},
        {'RISK':'full_promotion_retry_too_broad','MITIGATION':'Do not touch SYSTEM_MESSAGES or 70-row candidates in first micro proof.'},
    ]
    boundary=[
        {'PROTECTED_SYSTEM':'SOURCE_CODE','MUTATION_ALLOWED':0,'OBSERVED_MUTATION':0,'DETAIL':'No source mutation.'},
        {'PROTECTED_SYSTEM':'ACTIVE_MESSAGING_DBF_CATALOG','MUTATION_ALLOWED':0,'OBSERVED_MUTATION':0,'DETAIL':'10T is plan-only; no active DBF mutation.'},
        {'PROTECTED_SYSTEM':'ACTIVE_MESSAGING_CDX_INDEXES','MUTATION_ALLOWED':0,'OBSERVED_MUTATION':0,'DETAIL':'10T is plan-only; no active CDX mutation.'},
        {'PROTECTED_SYSTEM':'ACTIVE_MESSAGING_LMDB','MUTATION_ALLOWED':0,'OBSERVED_MUTATION':0,'DETAIL':'10T is plan-only; no active LMDB mutation.'},
        {'PROTECTED_SYSTEM':'HELP_DATA','MUTATION_ALLOWED':0,'OBSERVED_MUTATION':0,'DETAIL':'No HELP DATA mutation.'},
        {'PROTECTED_SYSTEM':'CMDHELPCHK','MUTATION_ALLOWED':0,'OBSERVED_MUTATION':0,'DETAIL':'No CMDHELPCHK mutation.'},
        {'PROTECTED_SYSTEM':'ACTIVE_TEXT_MICRO_PROOF_EXECUTION','MUTATION_ALLOWED':0,'OBSERVED_MUTATION':0,'DETAIL':'Future 10U requires explicit authorization.'},
    ]
    validation_issues='0' if status==STATUS_GREEN else str(failures)
    write_csv(reports/'message_catalog_phase22ae_6_5_10t_gate_check_v1.csv', gates, ['GATE','STATUS','DETAIL'])
    write_csv(reports/'message_catalog_phase22ae_6_5_10t_artifact_inventory_v1.csv', artifacts, ['ROLE','PATH','EXISTS','KIND','BYTES','SHA256','FILES'])
    write_csv(reports/'message_catalog_phase22ae_6_5_10t_candidate_artifacts_v1.csv', candidate_artifacts, ['ROLE','PATH','ROWS','BYTES','SHA256','PURPOSE'])
    write_csv(reports/'message_catalog_phase22ae_6_5_10t_micro_proof_plan_v1.csv', plan_rows, ['STEP','PHASE','ACTION','DETAIL','MUTATES_ACTIVE'])
    write_csv(reports/'message_catalog_phase22ae_6_5_10t_risk_register_v1.csv', risks, ['RISK','MITIGATION'])
    write_csv(reports/'message_catalog_phase22ae_6_5_10t_boundary_ledger_v1.csv', boundary, ['PROTECTED_SYSTEM','MUTATION_ALLOWED','OBSERVED_MUTATION','DETAIL'])
    write_csv(reports/'message_catalog_phase22ae_6_5_10t_status_summary_v1.csv', [{
        'STATUS':status,'VALIDATION_ISSUES':validation_issues,'PHASE22AE_6_5_10S_STATUS':s10.get('STATUS',''),'MSG_022AE_6_5_10S_SAVEPOINT_PRESENT':1 if sp10s else 0,
        'TEXT_IMPORT_CSVS_IDENTICAL_IN_10S':s10.get('TEXT_IMPORT_CSVS_IDENTICAL',''),'ACTIVE_TEXT_BASELINE_60_AFTER_ROLLBACK':s10.get('ACTIVE_TEXT_AFTER_ROLLBACK_RECORD_COUNT',''),
        'APPLY_ROOT':rel(apply_root,repo),'BASELINE60_ROUNDTRIP_CSV':baseline_rel,'BASELINE60_ROWS':len(baseline60),'CANDIDATE10_REFERENCE_CSV':candidate_rel,'CANDIDATE10_ROWS':len(candidate10),
        'EXECUTION_TEMPLATE_DISABLED':template_rel,'ACTIVE_TEXT_MICRO_PROOF_AUTHORIZED':0,'ACTIVE_TEXT_MICRO_PROOF_EXECUTED':0,'SOURCE_FILES_MUTATED':0,'ACTIVE_CATALOG_MUTATION_OBSERVED':0,
        'HELP_DATA_MUTATION_OBSERVED':0,'CMDHELPCHK_MUTATION_OBSERVED':0,'NEXT_GATE':NEXT_GATE,'REPORT_TIMESTAMP_UTC':datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00','Z')
    }], ['STATUS','VALIDATION_ISSUES','PHASE22AE_6_5_10S_STATUS','MSG_022AE_6_5_10S_SAVEPOINT_PRESENT','TEXT_IMPORT_CSVS_IDENTICAL_IN_10S','ACTIVE_TEXT_BASELINE_60_AFTER_ROLLBACK','APPLY_ROOT','BASELINE60_ROUNDTRIP_CSV','BASELINE60_ROWS','CANDIDATE10_REFERENCE_CSV','CANDIDATE10_ROWS','EXECUTION_TEMPLATE_DISABLED','ACTIVE_TEXT_MICRO_PROOF_AUTHORIZED','ACTIVE_TEXT_MICRO_PROOF_EXECUTED','SOURCE_FILES_MUTATED','ACTIVE_CATALOG_MUTATION_OBSERVED','HELP_DATA_MUTATION_OBSERVED','CMDHELPCHK_MUTATION_OBSERVED','NEXT_GATE','REPORT_TIMESTAMP_UTC'])
    (repo/'docs/messaging/MESSAGE_LOCALE_PHASE22AE_6_5_10T_TEXT_ONLY_ACTIVE_IMPORT_MICRO_PROOF_PLAN.md').write_text(f"# Message Catalog Phase 22AE.6.5.10T Text-Only Active Import Micro-Proof Plan\n\nStatus: `{status}`\n\n10T is plan-only. It stages a baseline60 text roundtrip CSV and a disabled template for future 10U diagnostic proof. No active mutation occurs in 10T.\n\nNext gate:\n\n```text\n{NEXT_GATE}\n```\n", encoding='utf-8')
    print(status)
    print(f'  validation issues: {validation_issues}')
    print(f'  Phase 22AE.6.5.10S status: {s10.get("STATUS","")}')
    print(f'  MSG-022AE.6.5.10S savepoint present: {1 if sp10s else 0}')
    print(f'  text import CSVs identical in 10S: {s10.get("TEXT_IMPORT_CSVS_IDENTICAL","")}')
    print(f'  active text baseline after rollback: {s10.get("ACTIVE_TEXT_AFTER_ROLLBACK_RECORD_COUNT","")}')
    print(f'  apply root: {rel(apply_root,repo)}')
    print(f'  baseline60 roundtrip rows: {len(baseline60)}')
    print(f'  candidate10 reference rows: {len(candidate10)}')
    print(f'  execution template disabled: {template_rel}')
    print('  active text micro proof authorized: 0')
    print('  active text micro proof executed: 0')
    print('  source files mutated: 0')
    print('  active catalog mutation observed: 0')
    print('  HELP DATA mutation observed: 0')
    print('  CMDHELPCHK mutation observed: 0')
    print(f'  next gate: {NEXT_GATE}')
    print(f'  reports: {reports}')
    return 0 if status==STATUS_GREEN else 2
if __name__=='__main__': raise SystemExit(main())
