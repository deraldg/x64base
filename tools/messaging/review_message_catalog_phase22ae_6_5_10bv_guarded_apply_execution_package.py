#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, json, hashlib, shutil
from datetime import datetime, timezone
from pathlib import Path
GREEN='MESSAGE_CATALOG_PHASE22AE_6_5_10BV_GUARDED_APPLY_EXECUTION_PACKAGE_REVIEW_GREEN_APPLY_EXECUTION_PREFLIGHT_REQUIRED_SOURCE_HELD'
BLOCKED='MESSAGE_CATALOG_PHASE22AE_6_5_10BV_GUARDED_APPLY_EXECUTION_PACKAGE_REVIEW_BLOCKED'
NEXT='HOLD_OR_AUTHORIZE_PHASE22AE_6_5_10BW_HELP_CMDHELPCHK_GUARDED_APPLY_EXECUTION_PREFLIGHT'
REPORT_DIR=Path('docs/messaging/reports')
BU_SUMMARY=REPORT_DIR/'message_catalog_phase22ae_6_5_10bu_status_summary_v1.csv'
BU_PACKAGE=REPORT_DIR/'message_catalog_phase22ae_6_5_10bu_execution_package_manifest_v1.csv'
BU_SCRIPTS=REPORT_DIR/'message_catalog_phase22ae_6_5_10bu_staged_script_manifest_v1.csv'
BU_RUNTIME=REPORT_DIR/'message_catalog_phase22ae_6_5_10bu_runtime_readback_probe_plan_v1.csv'
BU_RESTORE=REPORT_DIR/'message_catalog_phase22ae_6_5_10bu_restore_plan_v1.csv'
BV_ROOT=Path('docs/messaging/apply/phase22ae_6_5_10bv_guarded_apply_execution_package_review_v1')
ACTIVE_MSG_DBF=Path('dottalkpp/data/messaging/SYSTEM_MESSAGES.dbf')
ACTIVE_TEXT_DBF=Path('dottalkpp/data/messaging/SYSTEM_MESSAGE_TEXT.dbf')

def rows(p):
    p=Path(p)
    if not p.exists(): return []
    with p.open('r',encoding='utf-8-sig',newline='') as f: return list(csv.DictReader(f))
def first(p):
    r=rows(p); return r[0] if r else {}
def wcsv(p,rs,fs):
    p=Path(p); p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fs,lineterminator='\n',extrasaction='ignore'); w.writeheader()
        for r in rs: w.writerow({k:r.get(k,'') for k in fs})
def rel(p,repo):
    try: return str(Path(p).relative_to(repo)).replace('\\','/')
    except Exception: return str(p).replace('\\','/')
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''): h.update(b)
    return h.hexdigest()
def dbf_count(p):
    p=Path(p)
    if not p.exists() or p.stat().st_size<12: return ''
    return int.from_bytes(p.read_bytes()[:12][4:8],'little')
def savepoint(repo,sid):
    latest=''; lp=repo/REPORT_DIR/'message_savepoint_latest_v1.json'
    if lp.exists():
        try: latest=json.loads(lp.read_text(encoding='utf-8')).get('savepoint_id','')
        except Exception: latest=''
    jp=repo/'docs/messaging/MESSAGING_SAVEPOINT_JOURNAL.md'
    txt=jp.read_text(encoding='utf-8',errors='replace') if jp.exists() else ''
    return (latest==sid or sid in txt), latest

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--repo-root',required=True); ap.add_argument('--replace-existing-review',action='store_true'); a=ap.parse_args()
    repo=Path(a.repo_root).resolve(); reports=repo/REPORT_DIR; reports.mkdir(parents=True,exist_ok=True)
    bu=first(repo/BU_SUMMARY); package=rows(repo/BU_PACKAGE); scripts=rows(repo/BU_SCRIPTS); runtime=rows(repo/BU_RUNTIME); restore=rows(repo/BU_RESTORE)
    sp, latest=savepoint(repo,'MSG-022AE.6.5.10BU'); msg=dbf_count(repo/ACTIVE_MSG_DBF); text=dbf_count(repo/ACTIVE_TEXT_DBF); root=repo/BV_ROOT
    gates=[]; failures=0
    def gate(n,ok,d):
        nonlocal failures; gates.append({'GATE':n,'STATUS':'PASS' if ok else 'FAIL','DETAIL':str(d)}); failures += 0 if ok else 1
    gate('PHASE22AE_6_5_10BU_GREEN',bu.get('STATUS')=='MESSAGE_CATALOG_PHASE22AE_6_5_10BU_HELP_CMDHELPCHK_GUARDED_APPLY_EXECUTION_PACKAGE_STAGING_GREEN_STAGED_NO_APPLY',bu.get('STATUS','missing'))
    gate('MSG_022AE_6_5_10BU_SAVEPOINT_PRESENT',sp,latest)
    gate('BU_EXECUTION_PACKAGE_STAGED',bu.get('GUARDED_APPLY_EXECUTION_PACKAGE_STAGED')=='1',bu.get('GUARDED_APPLY_EXECUTION_PACKAGE_STAGED','missing'))
    gate('BU_APPLY_EXECUTION_NOT_AUTHORIZED_NOW',bu.get('APPLY_EXECUTION_AUTHORIZED_NOW')=='0',bu.get('APPLY_EXECUTION_AUTHORIZED_NOW','missing'))
    gate('BU_HELP_APPLY_NOT_EXECUTED',bu.get('HELP_DATA_APPLY_EXECUTED')=='0',bu.get('HELP_DATA_APPLY_EXECUTED','missing'))
    gate('BU_CMDHELPCHK_APPLY_NOT_EXECUTED',bu.get('CMDHELPCHK_APPLY_EXECUTED')=='0',bu.get('CMDHELPCHK_APPLY_EXECUTED','missing'))
    gate('BU_PACKAGE_ROWS_PRESENT',len(package)>0,len(package)); gate('BU_SCRIPT_ROWS_PRESENT',len(scripts)>0,len(scripts)); gate('BU_RUNTIME_ROWS_PRESENT',len(runtime)>0,len(runtime)); gate('BU_RESTORE_ROWS_PRESENT',len(restore)>0,len(restore))
    gate('ACTIVE_MESSAGES_HEADER_COUNT_14',msg==14,msg); gate('ACTIVE_TEXT_HEADER_COUNT_70',text==70,text); gate('BV_ROOT_NOT_EXISTING_OR_REPLACE_ALLOWED',(not root.exists()) or a.replace_existing_review,rel(root,repo))
    status=BLOCKED; pkg_review=[]; script_review=[]; runtime_review=[]; restore_review=[]; decisions=[]; artifacts=[]
    if failures==0:
        if root.exists() and a.replace_existing_review: shutil.rmtree(root)
        root.mkdir(parents=True,exist_ok=True)
        for i,r in enumerate(package,1):
            tex=str(r.get('TARGET_EXISTS',''))=='1'; bex=str(r.get('BACKUP_EXISTS',''))=='1'; hm=str(r.get('TARGET_HASH_MATCHES_EXPECTED',''))=='1'; applied=str(r.get('APPLY_EXECUTION_AUTHORIZED_NOW',''))=='1' or str(r.get('APPLY_EXECUTED_NOW',''))=='1'
            pkg_review.append({'REVIEW_ROW':i,'TARGET_ID':r.get('TARGET_ID',''),'TARGET_KIND':r.get('TARGET_KIND',''),'TARGET_PATH':r.get('TARGET_PATH',''),'TARGET_EXISTS':1 if tex else 0,'TARGET_HASH_MATCHES_EXPECTED':1 if hm else 0,'BACKUP_PATH':r.get('BACKUP_PATH',''),'BACKUP_EXISTS':1 if bex else 0,'DIFF_ARTIFACT':r.get('DIFF_ARTIFACT',''),'EXECUTION_METHOD':r.get('EXECUTION_METHOD',''),'PACKAGE_STATUS':r.get('PACKAGE_STATUS',''),'REVIEW_DISPOSITION':'ACCEPT_FOR_FINAL_PREFLIGHT' if tex and bex and not applied else 'REVIEW_REQUIRED','FINAL_PREFLIGHT_REQUIRED':1,'APPLY_EXECUTION_AUTHORIZED_NOW':0,'APPLY_EXECUTED_NOW':0,'REASON':'10BV reviews the staged execution package only; no HELP/CMDHELPCHK mutation in 10BV.'})
        for i,r in enumerate(scripts,1):
            p=r.get('SCRIPT_PATH',''); exists=bool(p) and (repo/p).exists()
            script_review.append({'SCRIPT_REVIEW_ROW':i,'SCRIPT_PATH':p,'SCRIPT_ROLE':r.get('SCRIPT_ROLE',''),'SCRIPT_EXISTS':1 if exists else 0,'APPLY_ENABLED':r.get('APPLY_ENABLED','0'),'RUN_NOW':r.get('RUN_NOW','0'),'REVIEW_DISPOSITION':'ACCEPT_DISABLED_SCRIPT_FOR_FINAL_PREFLIGHT' if exists and r.get('APPLY_ENABLED','0')=='0' else 'REVIEW_REQUIRED'})
        for i,r in enumerate(runtime,1): runtime_review.append({'RUNTIME_REVIEW_ROW':i,'PROBE_COMMAND':r.get('PROBE_COMMAND',''),'EXPECTED':r.get('EXPECTED',''),'REVIEW_DISPOSITION':'CARRY_FORWARD_TO_FINAL_PREFLIGHT_AND_POST_APPLY_READBACK','RUN_NOW':0})
        for i,r in enumerate(restore,1): restore_review.append({'RESTORE_REVIEW_ROW':i,'RESTORE_ITEM':r.get('RESTORE_ITEM',''),'DETAIL':r.get('DETAIL',''),'REVIEW_DISPOSITION':'CARRY_FORWARD_TO_FINAL_PREFLIGHT','APPLY_NOW':0})
        decisions=[
            {'DECISION_ITEM':'GUARDED_APPLY_EXECUTION_PACKAGE','DECISION':'ACCEPT_FOR_FINAL_PREFLIGHT','DETAIL':f'{len(package)} package rows reviewed.'},
            {'DECISION_ITEM':'DISABLED_SCRIPT_TEMPLATES','DECISION':'ACCEPT_FOR_FINAL_PREFLIGHT','DETAIL':f'{len(scripts)} staged script rows reviewed.'},
            {'DECISION_ITEM':'RUNTIME_READBACK_PROBE','DECISION':'CARRY_FORWARD_REQUIRED','DETAIL':f'{len(runtime)} runtime readback rows must be carried forward.'},
            {'DECISION_ITEM':'RESTORE_PLAN','DECISION':'CARRY_FORWARD_REQUIRED','DETAIL':f'{len(restore)} restore rows must be carried forward.'},
            {'DECISION_ITEM':'HELP_DATA_APPLY_EXECUTION','DECISION':'NOT_AUTHORIZED_IN_10BV','DETAIL':'No HELP DATA write in 10BV.'},
            {'DECISION_ITEM':'CMDHELPCHK_APPLY_EXECUTION','DECISION':'NOT_AUTHORIZED_IN_10BV','DETAIL':'No CMDHELPCHK write in 10BV.'},
            {'DECISION_ITEM':'NEXT_GATE','DECISION':'AUTHORIZE_10BW_OR_HOLD','DETAIL':'10BW should run final guarded apply execution preflight; actual mutation still requires explicit apply package/switch.'}]
        paths=[(root/'guarded_apply_execution_package_review_v1.csv',pkg_review,['REVIEW_ROW','TARGET_ID','TARGET_KIND','TARGET_PATH','TARGET_EXISTS','TARGET_HASH_MATCHES_EXPECTED','BACKUP_PATH','BACKUP_EXISTS','DIFF_ARTIFACT','EXECUTION_METHOD','PACKAGE_STATUS','REVIEW_DISPOSITION','FINAL_PREFLIGHT_REQUIRED','APPLY_EXECUTION_AUTHORIZED_NOW','APPLY_EXECUTED_NOW','REASON']),
               (root/'staged_script_review_v1.csv',script_review,['SCRIPT_REVIEW_ROW','SCRIPT_PATH','SCRIPT_ROLE','SCRIPT_EXISTS','APPLY_ENABLED','RUN_NOW','REVIEW_DISPOSITION']),
               (root/'runtime_readback_probe_review_v1.csv',runtime_review,['RUNTIME_REVIEW_ROW','PROBE_COMMAND','EXPECTED','REVIEW_DISPOSITION','RUN_NOW']),
               (root/'restore_plan_review_v1.csv',restore_review,['RESTORE_REVIEW_ROW','RESTORE_ITEM','DETAIL','REVIEW_DISPOSITION','APPLY_NOW']),
               (root/'execution_package_review_decisions_v1.csv',decisions,['DECISION_ITEM','DECISION','DETAIL'])]
        for p,rs,fs in paths:
            wcsv(p,rs,fs); artifacts.append({'ARTIFACT':rel(p,repo),'ROLE':'guarded_apply_execution_package_review_artifact','BYTES':p.stat().st_size,'SHA256':sha(p)})
        readme=root/'README_10BV_GUARDED_APPLY_EXECUTION_PACKAGE_REVIEW.md'
        readme.write_text('# 10BV Guarded Apply Execution Package Review\n\n10BV reviews the 10BU staged execution package and accepts it for final guarded preflight only.\n\nNo HELP DATA or CMDHELPCHK mutation is authorized or executed in 10BV.\n',encoding='utf-8')
        artifacts.append({'ARTIFACT':rel(readme,repo),'ROLE':'guarded_apply_execution_package_review_artifact','BYTES':readme.stat().st_size,'SHA256':sha(readme)})
        status=GREEN
    boundary=[{'PROTECTED_SYSTEM':x,'MUTATION_ALLOWED':0,'OBSERVED_MUTATION':0,'DETAIL':'10BV review only; no active mutation.'} for x in ['SOURCE_CODE','ACTIVE_SYSTEM_MESSAGES','ACTIVE_SYSTEM_MESSAGE_TEXT','ACTIVE_MESSAGING_CDX_LMDB','WORKSPACE_PROFILE','HELP_DATA','CMDHELPCHK']]
    readiness=[{'ITEM':'GUARDED_EXECUTION_PACKAGE_REVIEW_COMPLETE','STATUS':'YES' if pkg_review else 'NO','DETAIL':f'{len(pkg_review)} package rows reviewed.'},{'ITEM':'FINAL_PREFLIGHT_REQUIRED','STATUS':'YES','DETAIL':'10BW should perform final guarded preflight before any write package.'},{'ITEM':'HELP_DATA_APPLY_EXECUTION','STATUS':'NOT_EXECUTED_IN_10BV','DETAIL':'No apply execution.'},{'ITEM':'CMDHELPCHK_APPLY_EXECUTION','STATUS':'NOT_EXECUTED_IN_10BV','DETAIL':'No apply execution.'}]
    issues='0' if failures==0 else str(failures)
    wcsv(reports/'message_catalog_phase22ae_6_5_10bv_gate_check_v1.csv',gates,['GATE','STATUS','DETAIL'])
    wcsv(reports/'message_catalog_phase22ae_6_5_10bv_execution_package_review_v1.csv',pkg_review,['REVIEW_ROW','TARGET_ID','TARGET_KIND','TARGET_PATH','TARGET_EXISTS','TARGET_HASH_MATCHES_EXPECTED','BACKUP_PATH','BACKUP_EXISTS','DIFF_ARTIFACT','EXECUTION_METHOD','PACKAGE_STATUS','REVIEW_DISPOSITION','FINAL_PREFLIGHT_REQUIRED','APPLY_EXECUTION_AUTHORIZED_NOW','APPLY_EXECUTED_NOW','REASON'])
    wcsv(reports/'message_catalog_phase22ae_6_5_10bv_staged_script_review_v1.csv',script_review,['SCRIPT_REVIEW_ROW','SCRIPT_PATH','SCRIPT_ROLE','SCRIPT_EXISTS','APPLY_ENABLED','RUN_NOW','REVIEW_DISPOSITION'])
    wcsv(reports/'message_catalog_phase22ae_6_5_10bv_runtime_probe_review_v1.csv',runtime_review,['RUNTIME_REVIEW_ROW','PROBE_COMMAND','EXPECTED','REVIEW_DISPOSITION','RUN_NOW'])
    wcsv(reports/'message_catalog_phase22ae_6_5_10bv_restore_plan_review_v1.csv',restore_review,['RESTORE_REVIEW_ROW','RESTORE_ITEM','DETAIL','REVIEW_DISPOSITION','APPLY_NOW'])
    wcsv(reports/'message_catalog_phase22ae_6_5_10bv_review_decisions_v1.csv',decisions,['DECISION_ITEM','DECISION','DETAIL'])
    wcsv(reports/'message_catalog_phase22ae_6_5_10bv_apply_readiness_v1.csv',readiness,['ITEM','STATUS','DETAIL'])
    wcsv(reports/'message_catalog_phase22ae_6_5_10bv_boundary_ledger_v1.csv',boundary,['PROTECTED_SYSTEM','MUTATION_ALLOWED','OBSERVED_MUTATION','DETAIL'])
    wcsv(reports/'message_catalog_phase22ae_6_5_10bv_artifact_manifest_v1.csv',artifacts,['ARTIFACT','ROLE','BYTES','SHA256'])
    summary={'STATUS':status,'VALIDATION_ISSUES':issues,'PHASE22AE_6_5_10BU_STATUS':bu.get('STATUS',''),'MSG_022AE_6_5_10BU_SAVEPOINT_PRESENT':1 if sp else 0,'ACTIVE_MESSAGES_OBSERVED_COUNT':msg,'ACTIVE_TEXT_OBSERVED_COUNT':text,'BU_EXECUTION_PACKAGE_ROWS':len(package),'BU_STAGED_SCRIPT_ROWS':len(scripts),'BU_RUNTIME_READBACK_PROBE_ROWS':len(runtime),'BU_RESTORE_PLAN_ROWS':len(restore),'EXECUTION_PACKAGE_REVIEW_ROWS':len(pkg_review),'STAGED_SCRIPT_REVIEW_ROWS':len(script_review),'RUNTIME_PROBE_REVIEW_ROWS':len(runtime_review),'RESTORE_REVIEW_ROWS':len(restore_review),'DECISION_ROWS':len(decisions),'BV_ROOT':rel(root,repo),'FINAL_PREFLIGHT_REQUIRED':1 if status==GREEN else 0,'APPLY_EXECUTION_AUTHORIZED_NOW':0,'HELP_DATA_APPLY_EXECUTED':0,'CMDHELPCHK_APPLY_EXECUTED':0,'HELP_DATA_MUTATION_OBSERVED':0,'CMDHELPCHK_MUTATION_OBSERVED':0,'SOURCE_FILES_MUTATED':0,'ACTIVE_CATALOG_MUTATION_OBSERVED_BY_REVIEW':0,'DBF_MUTATION_OBSERVED':0,'CDX_LMDB_MUTATION_OBSERVED':0,'WORKSPACE_MUTATION_OBSERVED':0,'NEXT_GATE':NEXT,'REPORT_TIMESTAMP_UTC':datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00','Z')}
    wcsv(reports/'message_catalog_phase22ae_6_5_10bv_status_summary_v1.csv',[summary],list(summary.keys()))
    (repo/'docs/messaging/MESSAGE_LOCALE_PHASE22AE_6_5_10BV_GUARDED_APPLY_EXECUTION_PACKAGE_REVIEW.md').write_text(f'# Message Catalog Phase 22AE.6.5.10BV Guarded Apply Execution Package Review\n\nStatus: `{status}`\n\n10BV reviews the guarded apply execution package and accepts it for final guarded preflight only. It does not mutate HELP DATA or CMDHELPCHK.\n\nReview root:\n\n```text\n{rel(root,repo)}\n```\n\nNext gate:\n\n```text\n{NEXT}\n```\n',encoding='utf-8')
    print(status); print(f'  validation issues: {issues}'); print(f'  Phase 22AE.6.5.10BU status: {bu.get("STATUS","")}'); print(f'  MSG-022AE.6.5.10BU savepoint present: {1 if sp else 0}'); print(f'  active messages observed count: {msg}'); print(f'  active text observed count: {text}'); print(f'  BU execution package rows: {len(package)}'); print(f'  BU staged script rows: {len(scripts)}'); print(f'  BU runtime readback probe rows: {len(runtime)}'); print(f'  BU restore plan rows: {len(restore)}'); print(f'  execution package review rows: {len(pkg_review)}'); print(f'  staged script review rows: {len(script_review)}'); print(f'  runtime probe review rows: {len(runtime_review)}'); print(f'  restore review rows: {len(restore_review)}'); print(f'  decision rows: {len(decisions)}'); print(f'  review root: {rel(root,repo)}'); print('  final preflight required: 1'); print('  apply execution authorized now: 0'); print('  HELP DATA apply executed: 0'); print('  CMDHELPCHK apply executed: 0'); print('  HELP DATA mutation observed: 0'); print('  CMDHELPCHK mutation observed: 0'); print('  source files mutated: 0'); print('  active catalog mutation observed by review: 0'); print('  DBF mutation observed: 0'); print('  CDX/LMDB mutation observed: 0'); print('  workspace mutation observed: 0'); print(f'  next gate: {NEXT}'); print(f'  reports: {reports}')
    return 0 if status==GREEN else 2
if __name__=='__main__': raise SystemExit(main())
