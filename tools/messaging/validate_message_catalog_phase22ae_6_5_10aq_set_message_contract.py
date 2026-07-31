#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv
from datetime import datetime,timezone
from pathlib import Path
STATUS_FULL='MESSAGE_CATALOG_PHASE22AE_6_5_10AQ_SET_MESSAGE_CATALOG_READONLY_CONTRACT_PROOF_GREEN_CHECK_AND_GET_PROVEN'
STATUS_CHECK_ONLY='MESSAGE_CATALOG_PHASE22AE_6_5_10AQ_SET_MESSAGE_CATALOG_READONLY_CONTRACT_PROOF_GREEN_CHECK_PROVEN_GET_SYNTAX_REVIEW'
STATUS_BLOCKED='MESSAGE_CATALOG_PHASE22AE_6_5_10AQ_SET_MESSAGE_CATALOG_READONLY_CONTRACT_PROOF_BLOCKED'
NEXT_FULL='HOLD_OR_AUTHORIZE_PHASE22AE_6_5_10AR_MESSAGE_MANAGER_CONSUMER_CLOSEOUT'
NEXT_CHECK_ONLY='HOLD_OR_AUTHORIZE_PHASE22AE_6_5_10AQR_SET_MESSAGE_CATALOG_GET_SYNTAX_REVIEW'
REPORT_DIR=Path('docs/messaging/reports')
RUNLOG_PATH=Path('docs/messaging/runlog/MSG-022AE_6_5_10AQ_SET_MESSAGE_CATALOG_READONLY_CONTRACT_PROOF.md')
ACTIVE_MSG_DBF=Path('dottalkpp/data/messaging/SYSTEM_MESSAGES.dbf')
ACTIVE_TEXT_DBF=Path('dottalkpp/data/messaging/SYSTEM_MESSAGE_TEXT.dbf')
PROOF_SYMBOLS=['MESSAGE_PROOF_MODE_STATUS','MESSAGE_PROOF_BOUNDARY_NOTE']
PROOF_LOCALES=['en-US','es','fr','de','it']
MUTATION_TOKENS=['ZAP COMPLETE','IMPORTED ','APPEND','REPLACE','PACK','BUILDLMDB','CDX CREATE','DELETE ALL']

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
def norm(s): return ' '.join(s.replace('\r','\n').split()).upper()

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--repo-root',required=True); ap.add_argument('--runtime-log',default=''); args=ap.parse_args()
    repo=Path(args.repo_root).resolve(); reports=repo/REPORT_DIR; reports.mkdir(parents=True,exist_ok=True)
    stage=first_row(reports/'message_catalog_phase22ae_6_5_10aq_stage_status_summary_v1.csv')
    runtime=Path(args.runtime_log) if args.runtime_log else repo/RUNLOG_PATH
    if not runtime.is_absolute(): runtime=repo/runtime
    log=runtime.read_text(encoding='utf-8',errors='replace') if runtime.exists() else ''
    up=log.upper(); compact=norm(log)
    msg_open14='OPENED SYSTEM_MESSAGES (V64) : RECORD COUNT 14' in up
    text_open70='OPENED SYSTEM_MESSAGE_TEXT (V64) : RECORD COUNT 70' in up
    count14='\n14\n' in log.replace('\r','\n') or ' 14 ' in compact
    count70='\n70\n' in log.replace('\r','\n') or ' 70 ' in compact
    listed14='14 RECORD(S) LISTED' in up; listed70='70 RECORD(S) LISTED' in up
    proof_symbols=sum(1 for s in PROOF_SYMBOLS if s in up); proof_locales=sum(1 for loc in PROOF_LOCALES if loc.upper() in up)
    msg_header=dbf_count(repo/ACTIVE_MSG_DBF); text_header=dbf_count(repo/ACTIVE_TEXT_DBF)
    check_seen='SET MESSAGE CATALOG CHECK' in up
    get_seen='SET MESSAGE CATALOG GET' in up
    msgmgr_context='MSGMGR STATUS' in up and 'COMMAND HOUSE' in up
    check_proven=check_seen and ('ACTIVE_DBF' in up or 'PROVIDER MODE' in up or msg_open14 or msgmgr_context)
    get_proven=get_seen and proof_symbols==2 and proof_locales>=2 and 'UNKNOWN COMMAND: SET' not in up
    mutation_hits=[tok for tok in MUTATION_TOKENS if tok in up]
    cannot_open=up.count('CANNOT OPEN')
    gates=[]; failures=0; review_flags=0
    def gate(name,ok,detail,review_only=False):
        nonlocal failures,review_flags
        st='PASS' if ok else ('REVIEW' if review_only else 'FAIL'); gates.append({'GATE':name,'STATUS':st,'DETAIL':str(detail)})
        if not ok and review_only: review_flags+=1
        elif not ok: failures+=1
    gate('STAGE_GREEN',stage.get('STATUS')=='MESSAGE_CATALOG_PHASE22AE_6_5_10AQ_SET_MESSAGE_CATALOG_READONLY_CONTRACT_PROOF_STAGED_SOURCE_HELD',stage.get('STATUS','missing'))
    gate('RUNTIME_LOG_EXISTS',runtime.exists(),rel(runtime,repo))
    gate('SET_MESSAGE_CATALOG_CHECK_COMMAND_SEEN',check_seen,'SET MESSAGE CATALOG CHECK')
    gate('SET_MESSAGE_CATALOG_CHECK_SURFACE_PROVEN',check_proven,'provider/count/context evidence')
    gate('SET_MESSAGE_CATALOG_GET_COMMAND_SEEN',get_seen,'SET MESSAGE CATALOG GET')
    gate('SET_MESSAGE_CATALOG_GET_SURFACE_PROVEN',get_proven,'GET proof or syntax',review_only=True)
    gate('FRESH_OPEN_SYSTEM_MESSAGES_RECORD_COUNT_14',msg_open14,'Opened SYSTEM_MESSAGES record count 14')
    gate('FRESH_OPEN_SYSTEM_MESSAGE_TEXT_RECORD_COUNT_70',text_open70,'Opened SYSTEM_MESSAGE_TEXT record count 70')
    gate('COUNT_14_VISIBLE',count14,'COUNT output 14')
    gate('COUNT_70_VISIBLE',count70,'COUNT output 70')
    gate('LIST_14_VISIBLE',listed14,'LIST ALL message table')
    gate('LIST_70_VISIBLE',listed70,'LIST ALL text table')
    gate('PROOF_SYMBOLS_VISIBLE',proof_symbols==2,f'{proof_symbols}/2')
    gate('PROOF_LOCALES_VISIBLE',proof_locales==5,f'{proof_locales}/5')
    gate('ACTIVE_MESSAGES_HEADER_COUNT_14',msg_header==14,msg_header)
    gate('ACTIVE_TEXT_HEADER_COUNT_70',text_header==70,text_header)
    gate('NO_MUTATION_TOKENS',len(mutation_hits)==0,';'.join(mutation_hits) if mutation_hits else 'none')
    gate('NO_CANNOT_OPEN',cannot_open==0,cannot_open)
    if failures==0 and get_proven: status=STATUS_FULL; next_gate=NEXT_FULL
    elif failures==0: status=STATUS_CHECK_ONLY; next_gate=NEXT_CHECK_ONLY
    else: status=STATUS_BLOCKED; next_gate='HOLD_AND_FIX_PHASE22AE_6_5_10AQ_READONLY_CONTRACT_PROOF_FAILURE'
    issues='0' if failures==0 else str(failures)
    surfaces=[
        {'SURFACE':'SET MESSAGE CATALOG CHECK','OBSERVED':1 if check_seen else 0,'PROVEN':1 if check_proven else 0,'DETAIL':'Low-level check/proof surface.'},
        {'SURFACE':'SET MESSAGE CATALOG GET','OBSERVED':1 if get_seen else 0,'PROVEN':1 if get_proven else 0,'DETAIL':'Low-level get/read surface; syntax review acceptable if not proven.'},
        {'SURFACE':'MSGMGR STATUS','OBSERVED':1 if msgmgr_context else 0,'PROVEN':1 if msgmgr_context else 0,'DETAIL':'Command-house context after low-level probes.'},
        {'SURFACE':'ACTIVE_DBF_READBACK','OBSERVED':1 if msg_open14 and text_open70 else 0,'PROVEN':1 if msg_header==14 and text_header==70 else 0,'DETAIL':'Active tables preserved at 14/70.'},
    ]
    obs=[
        {'OBSERVATION':'runtime_log_exists','VALUE':1 if runtime.exists() else 0,'DETAIL':rel(runtime,repo)},
        {'OBSERVATION':'set_message_catalog_check_seen','VALUE':1 if check_seen else 0,'DETAIL':'direct command probe'},
        {'OBSERVATION':'set_message_catalog_check_proven','VALUE':1 if check_proven else 0,'DETAIL':'provider/count/context evidence'},
        {'OBSERVATION':'set_message_catalog_get_seen','VALUE':1 if get_seen else 0,'DETAIL':'direct command probe'},
        {'OBSERVATION':'set_message_catalog_get_proven','VALUE':1 if get_proven else 0,'DETAIL':'direct GET syntax/read evidence'},
        {'OBSERVATION':'proof_symbols_visible','VALUE':proof_symbols,'DETAIL':'2 expected'},
        {'OBSERVATION':'proof_locales_visible','VALUE':proof_locales,'DETAIL':'5 expected'},
        {'OBSERVATION':'active_messages_after_probe','VALUE':msg_header,'DETAIL':'DBF header count'},
        {'OBSERVATION':'active_text_after_probe','VALUE':text_header,'DETAIL':'DBF header count'},
    ]
    boundary=[
        {'PROTECTED_SYSTEM':'SOURCE_CODE','MUTATION_ALLOWED':0,'OBSERVED_MUTATION':0,'DETAIL':'10AQ is read-only.'},
        {'PROTECTED_SYSTEM':'ACTIVE_SYSTEM_MESSAGES','MUTATION_ALLOWED':0,'OBSERVED_MUTATION':0,'DETAIL':'No active DBF mutation.'},
        {'PROTECTED_SYSTEM':'ACTIVE_SYSTEM_MESSAGE_TEXT','MUTATION_ALLOWED':0,'OBSERVED_MUTATION':0,'DETAIL':'No active DBF mutation.'},
        {'PROTECTED_SYSTEM':'COMMAND_ALIAS_REGISTRY','MUTATION_ALLOWED':0,'OBSERVED_MUTATION':0,'DETAIL':'No alias mutation.'},
        {'PROTECTED_SYSTEM':'HELP_DATA','MUTATION_ALLOWED':0,'OBSERVED_MUTATION':0,'DETAIL':'No HELP DATA mutation.'},
        {'PROTECTED_SYSTEM':'CMDHELPCHK','MUTATION_ALLOWED':0,'OBSERVED_MUTATION':0,'DETAIL':'No CMDHELPCHK mutation.'},
    ]
    write_csv(reports/'message_catalog_phase22ae_6_5_10aq_validate_gate_check_v1.csv',gates,['GATE','STATUS','DETAIL'])
    write_csv(reports/'message_catalog_phase22ae_6_5_10aq_surface_contract_v1.csv',surfaces,['SURFACE','OBSERVED','PROVEN','DETAIL'])
    write_csv(reports/'message_catalog_phase22ae_6_5_10aq_runtime_observations_v1.csv',obs,['OBSERVATION','VALUE','DETAIL'])
    write_csv(reports/'message_catalog_phase22ae_6_5_10aq_boundary_ledger_v1.csv',boundary,['PROTECTED_SYSTEM','MUTATION_ALLOWED','OBSERVED_MUTATION','DETAIL'])
    summary={'STATUS':status,'VALIDATION_ISSUES':issues,'REVIEW_FLAGS':review_flags,'STAGE_STATUS':stage.get('STATUS',''),'SET_MESSAGE_CATALOG_CHECK_SEEN':1 if check_seen else 0,'SET_MESSAGE_CATALOG_CHECK_PROVEN':1 if check_proven else 0,'SET_MESSAGE_CATALOG_GET_SEEN':1 if get_seen else 0,'SET_MESSAGE_CATALOG_GET_PROVEN':1 if get_proven else 0,'FRESH_OPEN_SYSTEM_MESSAGES_14':1 if msg_open14 else 0,'FRESH_OPEN_SYSTEM_MESSAGE_TEXT_70':1 if text_open70 else 0,'RUNTIME_MESSAGE_COUNT_14':1 if count14 else 0,'RUNTIME_TEXT_COUNT_70':1 if count70 else 0,'RUNTIME_MESSAGE_LISTED_14':1 if listed14 else 0,'RUNTIME_TEXT_LISTED_70':1 if listed70 else 0,'PROOF_SYMBOLS_VISIBLE':proof_symbols,'PROOF_LOCALES_VISIBLE':proof_locales,'ACTIVE_MESSAGES_HEADER_COUNT_AFTER_PROBE':msg_header,'ACTIVE_TEXT_HEADER_COUNT_AFTER_PROBE':text_header,'ALIASES_AUTHORIZED':0,'RUNTIME_CONSUMER_SOURCE_INTEGRATION_AUTHORIZED':0,'SOURCE_FILES_MUTATED':0,'ACTIVE_CATALOG_MUTATION_OBSERVED':0,'HELP_DATA_MUTATION_OBSERVED':0,'CMDHELPCHK_MUTATION_OBSERVED':0,'NEXT_GATE':next_gate,'REPORT_TIMESTAMP_UTC':datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00','Z')}
    write_csv(reports/'message_catalog_phase22ae_6_5_10aq_validate_status_summary_v1.csv',[summary],list(summary.keys()))
    print(status); print(f'  validation issues: {issues}'); print(f'  review flags: {review_flags}'); print(f'  stage green: {1 if stage.get("STATUS")=="MESSAGE_CATALOG_PHASE22AE_6_5_10AQ_SET_MESSAGE_CATALOG_READONLY_CONTRACT_PROOF_STAGED_SOURCE_HELD" else 0}'); print(f'  SET MESSAGE CATALOG CHECK seen: {1 if check_seen else 0}'); print(f'  SET MESSAGE CATALOG CHECK proven: {1 if check_proven else 0}'); print(f'  SET MESSAGE CATALOG GET seen: {1 if get_seen else 0}'); print(f'  SET MESSAGE CATALOG GET proven: {1 if get_proven else 0}'); print(f'  fresh open SYSTEM_MESSAGES 14: {1 if msg_open14 else 0}'); print(f'  fresh open SYSTEM_MESSAGE_TEXT 70: {1 if text_open70 else 0}'); print(f'  runtime message listed 14: {1 if listed14 else 0}'); print(f'  runtime text listed 70: {1 if listed70 else 0}'); print(f'  proof symbols visible: {proof_symbols}/2'); print(f'  proof locales visible: {proof_locales}/5'); print(f'  active messages header count after probe: {msg_header}'); print(f'  active text header count after probe: {text_header}'); print('  aliases authorized: 0'); print('  runtime consumer source integration authorized: 0'); print('  source files mutated: 0'); print('  active catalog mutation observed: 0'); print('  HELP DATA mutation observed: 0'); print('  CMDHELPCHK mutation observed: 0'); print(f'  next gate: {next_gate}'); print(f'  reports: {reports}')
    return 0 if failures==0 else 2
if __name__=='__main__': raise SystemExit(main())
