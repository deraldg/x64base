#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,json,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path
STATUS_GREEN='MESSAGE_CATALOG_PHASE22AE_6_5_10AQ_SET_MESSAGE_CATALOG_READONLY_CONTRACT_PROOF_STAGED_SOURCE_HELD'
STATUS_BLOCKED='MESSAGE_CATALOG_PHASE22AE_6_5_10AQ_SET_MESSAGE_CATALOG_READONLY_CONTRACT_PROOF_STAGE_BLOCKED'
NEXT_GATE='RUN_PHASE22AE_6_5_10AQ_SET_MESSAGE_CATALOG_READONLY_CONTRACT_PROOF_THEN_VALIDATE'
REPORT_DIR=Path('docs/messaging/reports')
SCRIPT_PATH=Path('docs/messaging/scripts/MESSAGE_CATALOG_PHASE22AE_6_5_10AQ_SET_MESSAGE_CATALOG_READONLY_CONTRACT_PROOF.dts')
RUNLOG_PATH=Path('docs/messaging/runlog/MSG-022AE_6_5_10AQ_SET_MESSAGE_CATALOG_READONLY_CONTRACT_PROOF.md')
ACTIVE_MSG_DBF=Path('dottalkpp/data/messaging/SYSTEM_MESSAGES.dbf')
ACTIVE_TEXT_DBF=Path('dottalkpp/data/messaging/SYSTEM_MESSAGE_TEXT.dbf')

def read_csv(p):
    if not p.exists(): return []
    with p.open('r',encoding='utf-8-sig',newline='') as f: return list(csv.DictReader(f))
def first_row(p):
    r=read_csv(p); return r[0] if r else {}
def write_csv(p,rows,fields):
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields,lineterminator='\n',extrasaction='ignore'); w.writeheader()
        for row in rows: w.writerow({k:row.get(k,'') for k in fields})
def rel(p,repo):
    try: return str(p.relative_to(repo)).replace('\\','/')
    except Exception: return str(p).replace('\\','/')
def dbf_count(p):
    if not p.exists() or p.stat().st_size<12: return ''
    return int.from_bytes(p.read_bytes()[:12][4:8],'little')
def savepoint_present(repo,sid):
    latest=''; lp=repo/REPORT_DIR/'message_savepoint_latest_v1.json'
    if lp.exists():
        try: latest=json.loads(lp.read_text(encoding='utf-8')).get('savepoint_id','')
        except Exception: latest=''
    j=repo/'docs/messaging/MESSAGING_SAVEPOINT_JOURNAL.md'
    text=j.read_text(encoding='utf-8',errors='replace') if j.exists() else ''
    return latest==sid or sid in text, latest
def dottalkpp_running():
    if sys.platform.startswith('win'):
        try:
            cp=subprocess.run(['tasklist','/FI','IMAGENAME eq dottalkpp.exe'],capture_output=True,text=True,timeout=10)
            return 'dottalkpp.exe' in ((cp.stdout or '')+(cp.stderr or '')).lower()
        except Exception: return False
    return False

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--repo-root',required=True); ap.add_argument('--replace-existing-script',action='store_true'); args=ap.parse_args()
    repo=Path(args.repo_root).resolve(); reports=repo/REPORT_DIR; reports.mkdir(parents=True,exist_ok=True)
    ap_row=first_row(reports/'message_catalog_phase22ae_6_5_10ap_status_summary_v1.csv')
    sp,latest=savepoint_present(repo,'MSG-022AE.6.5.10AP')
    msg=dbf_count(repo/ACTIVE_MSG_DBF); text=dbf_count(repo/ACTIVE_TEXT_DBF); running=dottalkpp_running(); script=repo/SCRIPT_PATH
    gates=[]; failures=0
    def gate(name,ok,detail):
        nonlocal failures; gates.append({'GATE':name,'STATUS':'PASS' if ok else 'FAIL','DETAIL':str(detail)})
        if not ok: failures+=1
    gate('PHASE22AE_6_5_10AP_GREEN',ap_row.get('STATUS')=='MESSAGE_CATALOG_PHASE22AE_6_5_10AP_EXISTING_CONSUMER_SURFACE_CONTRACT_REVIEW_GREEN_SOURCE_HELD',ap_row.get('STATUS','missing'))
    gate('MSG_022AE_6_5_10AP_SAVEPOINT_PRESENT',sp,latest)
    gate('ACTIVE_MESSAGES_HEADER_COUNT_14',msg==14,msg)
    gate('ACTIVE_TEXT_HEADER_COUNT_70',text==70,text)
    gate('NO_DOTTALKPP_PROCESS_RUNNING',not running,running)
    gate('SCRIPT_NOT_EXISTING_OR_REPLACE_ALLOWED',(not script.exists()) or args.replace_existing_script,rel(script,repo))
    status=STATUS_BLOCKED
    if failures==0:
        script.parent.mkdir(parents=True,exist_ok=True)
        script.write_text('\n'.join([
            '* MESSAGE_CATALOG_PHASE22AE_6_5_10AQ_SET_MESSAGE_CATALOG_READONLY_CONTRACT_PROOF.dts',
            '* READ-ONLY low-level SET MESSAGE CATALOG CHECK/GET proof.',
            '* No ZAP, IMPORT, APPEND, REPLACE, PACK, CDX CREATE, BUILDLMDB, source mutation, HELP mutation, or CMDHELPCHK mutation.',
            '* GET syntax is being probed; usage/unknown syntax is a review result, not a DBF failure.',
            '* No QUIT here; quit manually in interactive runs.','',
            '* 1. Direct low-level check surface advertised by MSGMGR.','SET MESSAGE CATALOG CHECK','',
            '* 2. Direct low-level get/read surface probes. Exact syntax may be refined by this proof.',
            'SET MESSAGE CATALOG GET',
            'SET MESSAGE CATALOG GET MESSAGE_PROOF_MODE_STATUS en-US',
            'SET MESSAGE CATALOG GET MESSAGE_PROOF_MODE_STATUS es',
            'SET MESSAGE CATALOG GET MESSAGE_PROOF_BOUNDARY_NOTE en-US',
            'SET MESSAGE CATALOG GET MESSAGE_PROOF_BOUNDARY_NOTE it','',
            '* 3. Keep MSGMGR context visible after low-level probes.','MSGMGR STATUS','',
            '* 4. Final active table readback after probes.',
            f'USE {(repo/ACTIVE_MSG_DBF).resolve().as_posix()}','COUNT','LIST ALL',
            f'USE {(repo/ACTIVE_TEXT_DBF).resolve().as_posix()}','COUNT','LIST ALL','',
            '* 5. Final cross-table count proof.',
            f'USE {(repo/ACTIVE_MSG_DBF).resolve().as_posix()}','COUNT',
            f'USE {(repo/ACTIVE_TEXT_DBF).resolve().as_posix()}','COUNT',''
        ]),encoding='utf-8')
        status=STATUS_GREEN
    probes=[
        {'PROBE_ID':'AQ-001','COMMAND':'SET MESSAGE CATALOG CHECK','PURPOSE':'Prove advertised low-level active catalog check surface.','UNKNOWN_OR_USAGE_OK':0},
        {'PROBE_ID':'AQ-002','COMMAND':'SET MESSAGE CATALOG GET','PURPOSE':'Discover base GET usage/syntax.','UNKNOWN_OR_USAGE_OK':1},
        {'PROBE_ID':'AQ-003','COMMAND':'SET MESSAGE CATALOG GET MESSAGE_PROOF_MODE_STATUS en-US','PURPOSE':'Probe direct GET syntax for proof symbol en-US.','UNKNOWN_OR_USAGE_OK':1},
        {'PROBE_ID':'AQ-004','COMMAND':'SET MESSAGE CATALOG GET MESSAGE_PROOF_MODE_STATUS es','PURPOSE':'Probe direct GET syntax for proof symbol es.','UNKNOWN_OR_USAGE_OK':1},
        {'PROBE_ID':'AQ-005','COMMAND':'SET MESSAGE CATALOG GET MESSAGE_PROOF_BOUNDARY_NOTE en-US','PURPOSE':'Probe direct GET syntax for boundary symbol en-US.','UNKNOWN_OR_USAGE_OK':1},
        {'PROBE_ID':'AQ-006','COMMAND':'SET MESSAGE CATALOG GET MESSAGE_PROOF_BOUNDARY_NOTE it','PURPOSE':'Probe direct GET syntax for boundary symbol it.','UNKNOWN_OR_USAGE_OK':1},
    ]
    boundary=[
        {'PROTECTED_SYSTEM':'SOURCE_CODE','MUTATION_ALLOWED':0,'OBSERVED_MUTATION':0,'DETAIL':'10AQ stage is read-only/report artifact generation.'},
        {'PROTECTED_SYSTEM':'ACTIVE_SYSTEM_MESSAGES','MUTATION_ALLOWED':0,'OBSERVED_MUTATION':0,'DETAIL':'No DBF mutation.'},
        {'PROTECTED_SYSTEM':'ACTIVE_SYSTEM_MESSAGE_TEXT','MUTATION_ALLOWED':0,'OBSERVED_MUTATION':0,'DETAIL':'No DBF mutation.'},
        {'PROTECTED_SYSTEM':'ACTIVE_MESSAGING_CDX_LMDB','MUTATION_ALLOWED':0,'OBSERVED_MUTATION':0,'DETAIL':'No index/LMDB mutation.'},
        {'PROTECTED_SYSTEM':'COMMAND_ALIAS_REGISTRY','MUTATION_ALLOWED':0,'OBSERVED_MUTATION':0,'DETAIL':'No alias mutation.'},
        {'PROTECTED_SYSTEM':'HELP_DATA','MUTATION_ALLOWED':0,'OBSERVED_MUTATION':0,'DETAIL':'No HELP DATA mutation.'},
        {'PROTECTED_SYSTEM':'CMDHELPCHK','MUTATION_ALLOWED':0,'OBSERVED_MUTATION':0,'DETAIL':'No CMDHELPCHK mutation.'},
    ]
    issues='0' if status==STATUS_GREEN else str(failures)
    write_csv(reports/'message_catalog_phase22ae_6_5_10aq_stage_gate_check_v1.csv',gates,['GATE','STATUS','DETAIL'])
    write_csv(reports/'message_catalog_phase22ae_6_5_10aq_probe_manifest_v1.csv',probes,['PROBE_ID','COMMAND','PURPOSE','UNKNOWN_OR_USAGE_OK'])
    write_csv(reports/'message_catalog_phase22ae_6_5_10aq_stage_boundary_ledger_v1.csv',boundary,['PROTECTED_SYSTEM','MUTATION_ALLOWED','OBSERVED_MUTATION','DETAIL'])
    summary={'STATUS':status,'VALIDATION_ISSUES':issues,'PHASE22AE_6_5_10AP_STATUS':ap_row.get('STATUS',''),'MSG_022AE_6_5_10AP_SAVEPOINT_PRESENT':1 if sp else 0,'ACTIVE_MESSAGES_HEADER_COUNT_AT_STAGE':msg,'ACTIVE_TEXT_HEADER_COUNT_AT_STAGE':text,'DOTTALKPP_PROCESS_RUNNING':1 if running else 0,'SCRIPT_PATH':rel(script,repo) if script.exists() else '','RUNLOG_PATH':rel(repo/RUNLOG_PATH,repo),'READONLY_CONTRACT_PROOF_STAGED':1 if status==STATUS_GREEN else 0,'ALIASES_AUTHORIZED':0,'RUNTIME_CONSUMER_SOURCE_INTEGRATION_AUTHORIZED':0,'SOURCE_FILES_MUTATED':0,'ACTIVE_CATALOG_MUTATION_OBSERVED':0,'HELP_DATA_MUTATION_OBSERVED':0,'CMDHELPCHK_MUTATION_OBSERVED':0,'NEXT_GATE':NEXT_GATE,'REPORT_TIMESTAMP_UTC':datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00','Z')}
    write_csv(reports/'message_catalog_phase22ae_6_5_10aq_stage_status_summary_v1.csv',[summary],list(summary.keys()))
    (repo/'docs/messaging/MESSAGE_LOCALE_PHASE22AE_6_5_10AQ_SET_MESSAGE_CATALOG_READONLY_CONTRACT_PROOF.md').write_text(f"# Message Catalog Phase 22AE.6.5.10AQ SET MESSAGE CATALOG Read-Only Contract Proof\n\nStatus: `{status}`\n\n10AQ is read-only. It directly probes `SET MESSAGE CATALOG CHECK` and `SET MESSAGE CATALOG GET` surfaces advertised by MSGMGR, while preserving the active 14/70 catalog.\n\nNext gate:\n\n```text\n{NEXT_GATE}\n```\n",encoding='utf-8')
    print(status); print(f'  validation issues: {issues}'); print(f'  Phase 22AE.6.5.10AP status: {ap_row.get("STATUS","")}'); print(f'  MSG-022AE.6.5.10AP savepoint present: {1 if sp else 0}'); print(f'  active messages header count at stage: {msg}'); print(f'  active text header count at stage: {text}'); print(f'  dottalkpp process running: {1 if running else 0}'); print(f'  script path: {rel(script,repo) if script.exists() else ""}'); print('  readonly contract proof staged: '+('1' if status==STATUS_GREEN else '0')); print('  aliases authorized: 0'); print('  runtime consumer source integration authorized: 0'); print('  source files mutated: 0'); print('  active catalog mutation observed: 0'); print('  HELP DATA mutation observed: 0'); print('  CMDHELPCHK mutation observed: 0'); print(f'  next gate: {NEXT_GATE}'); print(f'  reports: {reports}')
    return 0 if status==STATUS_GREEN else 2
if __name__=='__main__': raise SystemExit(main())
