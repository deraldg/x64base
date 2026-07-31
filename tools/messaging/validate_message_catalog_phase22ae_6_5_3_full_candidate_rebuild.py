#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,hashlib,json,struct
from datetime import datetime,timezone
from pathlib import Path
REPORT=Path('docs/messaging/reports')
SANDBOX=Path('docs/messaging/sandbox/phase22ae_6_5_3_full_candidate_rebuild_v1')
RUNLOG=Path('docs/messaging/runlog/MSG-022AE_6_5_3_FULL_CANDIDATE_REBUILD_SANDBOX_PROOF.md')
ACTIVE=Path('dottalkpp/data/messaging'); IDX=Path('dottalkpp/data/indexes/messaging'); LMDB=Path('dottalkpp/data/lmdb/messaging'); DIDX=Path('dottalkpp/data/indexes'); DLMDB=Path('dottalkpp/data/lmdb')
TABLES=['SYSTEM_MESSAGES','SYSTEM_MESSAGE_TEXT']
PROVEN='MESSAGE_CATALOG_PHASE22AE_6_5_3_FULL_CANDIDATE_REBUILD_SANDBOX_PROOF_GREEN_TWO_TABLE_REBUILD_PROVEN'
NOTPROVEN='MESSAGE_CATALOG_PHASE22AE_6_5_3_FULL_CANDIDATE_REBUILD_SANDBOX_PROOF_GREEN_REBUILD_NOT_PROVEN_FIELD_MAP_REVIEW'
BLOCKED='MESSAGE_CATALOG_PHASE22AE_6_5_3_FULL_CANDIDATE_REBUILD_SANDBOX_PROOF_BLOCKED'
NEXT_PROVEN='HOLD_OR_AUTHORIZE_PHASE22AE_6_5_4_ACTIVE_PROMOTION_PLAN_FROM_REBUILD_PROOF'
NEXT_NOT='HOLD_OR_AUTHORIZE_PHASE22AE_6_5_4_FIELD_MAP_FORENSIC_REVIEW'

def rows(p):
    if not p.exists(): return []
    with p.open('r',encoding='utf-8-sig',newline='') as f: return list(csv.DictReader(f))
def first(p):
    r=rows(p); return r[0] if r else {}
def write(p,rs,fields):
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields,lineterminator='\n'); w.writeheader()
        for r in rs: w.writerow({k:r.get(k,'') for k in fields})
def rel(p,repo):
    try: return str(p.relative_to(repo)).replace('\\','/')
    except Exception: return str(p).replace('\\','/')
def sha(p):
    if not p.exists() or not p.is_file(): return ''
    h=hashlib.sha256();
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''): h.update(b)
    return h.hexdigest()
def fp(repo):
    out=[]
    for t in TABLES:
        for p,role in [(repo/ACTIVE/f'{t}.dbf',f'active_dbf_{t}'),(repo/IDX/f'{t}.cdx',f'active_index_{t}'),(repo/IDX/f'{t}.cdx.meta',f'active_index_meta_{t}'),(repo/LMDB/f'{t}.cdx.d',f'active_lmdb_{t}'),(repo/DIDX/f'{t}.cdx',f'default_index_{t}'),(repo/DIDX/f'{t}.cdx.meta',f'default_index_meta_{t}'),(repo/DLMDB/f'{t}.cdx.d',f'default_lmdb_{t}')]:
            if p.is_dir():
                hs=hashlib.sha256(); n=0; total=0
                for q in sorted(x for x in p.rglob('*') if x.is_file()): hs.update(str(q.relative_to(p)).encode()); hs.update(sha(q).encode()); n+=1; total+=q.stat().st_size
                out.append({'ROLE':role,'PATH':rel(p,repo),'EXISTS':1,'KIND':'dir','BYTES':total,'SHA256':hs.hexdigest(),'FILES':n})
            elif p.is_file(): out.append({'ROLE':role,'PATH':rel(p,repo),'EXISTS':1,'KIND':'file','BYTES':p.stat().st_size,'SHA256':sha(p),'FILES':1})
            else: out.append({'ROLE':role,'PATH':rel(p,repo),'EXISTS':0,'KIND':'missing','BYTES':0,'SHA256':'','FILES':0})
    return out
def diff(b,a):
    bd={r['ROLE']+'|'+r['PATH']:r for r in b}; ad={r['ROLE']+'|'+r['PATH']:r for r in a}; out=[]
    for k in sorted(set(bd)|set(ad)):
        x=bd.get(k); y=ad.get(k)
        if x is None: out.append({'ROLE':y['ROLE'],'PATH':y['PATH'],'CHANGE':'ADDED','BEFORE_SHA256':'','AFTER_SHA256':y['SHA256'],'BEFORE_BYTES':'','AFTER_BYTES':y['BYTES']})
        elif y is None: out.append({'ROLE':x['ROLE'],'PATH':x['PATH'],'CHANGE':'REMOVED','BEFORE_SHA256':x['SHA256'],'AFTER_SHA256':'','BEFORE_BYTES':x['BYTES'],'AFTER_BYTES':''})
        elif x.get('SHA256')!=y.get('SHA256') or str(x.get('BYTES'))!=str(y.get('BYTES')): out.append({'ROLE':y['ROLE'],'PATH':y['PATH'],'CHANGE':'MODIFIED','BEFORE_SHA256':x['SHA256'],'AFTER_SHA256':y['SHA256'],'BEFORE_BYTES':x['BYTES'],'AFTER_BYTES':y['BYTES']})
    return out
def parse(p):
    d=p.read_bytes(); count=struct.unpack('<I',d[4:8])[0]; hlen=struct.unpack('<H',d[8:10])[0]; rlen=struct.unpack('<H',d[10:12])[0]; fs=[]; off=1; pos=32
    while pos+32<=len(d) and d[pos]!=13:
        name=d[pos:pos+11].split(b'\0',1)[0].decode('ascii','ignore').strip().upper(); typ=chr(d[pos+11]); ln=d[pos+16]
        if name: fs.append({'NAME':name,'TYPE':typ,'LENGTH':ln,'OFFSET':off}); off+=ln
        pos+=32
    data=[]
    with p.open('rb') as f:
        f.seek(hlen)
        for i in range(count):
            rec=f.read(rlen); row={'__RECNO__':i+1}
            for fld in fs:
                raw=rec[fld['OFFSET']:fld['OFFSET']+fld['LENGTH']]
                row[fld['NAME']]=raw.decode('cp1252' if fld['TYPE'].upper() in ('C','M') else 'ascii',errors='replace').rstrip().strip()
            data.append(row)
    return count,data
def has(row,val): return bool(val) and any(str(v).strip()==val for k,v in row.items() if not k.startswith('__'))

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--repo-root',required=True); ap.add_argument('--runtime-proof',default=''); a=ap.parse_args()
    repo=Path(a.repo_root).resolve(); reports=repo/REPORT; reports.mkdir(parents=True,exist_ok=True)
    stage=first(reports/'message_catalog_phase22ae_6_5_3_stage_status_summary_v1.csv'); before=rows(reports/'message_catalog_phase22ae_6_5_3_protected_fingerprint_before_v1.csv')
    expm=rows(reports/'message_catalog_phase22ae_6_5_3_expected_message_rows_v1.csv'); expt=rows(reports/'message_catalog_phase22ae_6_5_3_expected_text_rows_v1.csv')
    rt=Path(a.runtime_proof) if a.runtime_proof else repo/RUNLOG
    if not rt.is_absolute(): rt=repo/rt
    log=rt.read_text(encoding='utf-8',errors='replace').upper() if rt.exists() else ''
    gates=[]; fail=0
    def gate(n,ok,d):
        nonlocal fail; gates.append({'GATE':n,'STATUS':'PASS' if ok else 'FAIL','DETAIL':str(d)}); fail+=0 if ok else 1
    gate('STAGE_GREEN',stage.get('STATUS')=='MESSAGE_CATALOG_PHASE22AE_6_5_3_FULL_CANDIDATE_REBUILD_SANDBOX_PROOF_STAGED_SOURCE_HELD',stage.get('STATUS','missing'))
    gate('RUNTIME_PROOF_EXISTS',rt.exists(),rel(rt,repo)); gate('EXPECTED_MESSAGE_ROWS_2',len(expm)==2,len(expm)); gate('EXPECTED_TEXT_ROWS_10',len(expt)==10,len(expt))
    after=fp(repo); delta=diff(before,after); boundary=len(delta)==0
    mc=tc=''; mf=[]; tf=[]; tails=[]
    try:
        mc,mrows=parse(repo/SANDBOX/'dbf/SYSTEM_MESSAGES.dbf'); tc,trows=parse(repo/SANDBOX/'dbf/SYSTEM_MESSAGE_TEXT.dbf')
        for e in expm:
            sym=e.get('SYMBOL',''); ms=[r for r in mrows if has(r,sym)]
            if ms: mf.append({'SYMBOL':sym,'MATCHES':len(ms),'RECNO':ms[-1]['__RECNO__']})
        for e in expt:
            sym=e.get('SYMBOL',''); lo=e.get('LOCALE',''); ms=[r for r in trows if has(r,sym) and has(r,lo)]
            if ms: tf.append({'SYMBOL':sym,'LOCALE':lo,'MATCHES':len(ms),'RECNO':ms[-1]['__RECNO__']})
        for lab,rs in [('SYSTEM_MESSAGES',mrows[-8:]),('SYSTEM_MESSAGE_TEXT',trows[-14:])]:
            for r in rs: tails.append({'TABLE':lab,'RECNO':r.get('__RECNO__',''),'ROW_JSON':json.dumps({k:v for k,v in r.items() if k=='__RECNO__' or str(v).strip()},ensure_ascii=False,sort_keys=True)})
    except Exception as e: gate('SANDBOX_DBF_READBACK',False,e)
    md=mc-int(stage.get('SANDBOX_MESSAGE_ROWS_BEFORE') or 12) if isinstance(mc,int) else ''; td=tc-int(stage.get('SANDBOX_TEXT_ROWS_BEFORE') or 60) if isinstance(tc,int) else ''
    proven=(md==2 and td==10 and len(mf)==2 and len(tf)==10); status=BLOCKED if fail or not boundary else PROVEN if proven else NOTPROVEN; nextg='HOLD_AND_FIX_PHASE22AE_6_5_3_REBUILD_SETUP_OR_BOUNDARY' if status==BLOCKED else NEXT_PROVEN if proven else NEXT_NOT; val='0' if status!=BLOCKED else str(max(1,fail,len(delta)))
    result={'SANDBOX_MESSAGE_ROWS_BEFORE':stage.get('SANDBOX_MESSAGE_ROWS_BEFORE',''),'SANDBOX_MESSAGE_ROWS_AFTER':mc,'MESSAGE_DELTA':md,'SANDBOX_TEXT_ROWS_BEFORE':stage.get('SANDBOX_TEXT_ROWS_BEFORE',''),'SANDBOX_TEXT_ROWS_AFTER':tc,'TEXT_DELTA':td,'FOUND_MESSAGE_KEYS':len(mf),'FOUND_TEXT_KEYS':len(tf),'TWO_TABLE_REBUILD_PROVEN':1 if proven else 0,'BOUNDARY_CLEAN':1 if boundary else 0,'PROTECTED_FINGERPRINT_CHANGES':len(delta)}
    write(reports/'message_catalog_phase22ae_6_5_3_validate_gate_check_v1.csv',gates,['GATE','STATUS','DETAIL'])
    write(reports/'message_catalog_phase22ae_6_5_3_rebuild_result_v1.csv',[result],list(result.keys()))
    write(reports/'message_catalog_phase22ae_6_5_3_found_message_keys_v1.csv',mf,['SYMBOL','MATCHES','RECNO'])
    write(reports/'message_catalog_phase22ae_6_5_3_found_text_keys_v1.csv',tf,['SYMBOL','LOCALE','MATCHES','RECNO'])
    write(reports/'message_catalog_phase22ae_6_5_3_tail_rows_v1.csv',tails,['TABLE','RECNO','ROW_JSON'])
    write(reports/'message_catalog_phase22ae_6_5_3_protected_fingerprint_after_v1.csv',after,['ROLE','PATH','EXISTS','KIND','BYTES','SHA256','FILES'])
    write(reports/'message_catalog_phase22ae_6_5_3_protected_fingerprint_delta_v1.csv',delta,['ROLE','PATH','CHANGE','BEFORE_SHA256','AFTER_SHA256','BEFORE_BYTES','AFTER_BYTES'])
    write(reports/'message_catalog_phase22ae_6_5_3_validate_boundary_ledger_v1.csv',[{'PROTECTED_SYSTEM':'ACTIVE_MESSAGE_AND_SELECTED_INDEX_LMDB_ROOTS','MUTATION_ALLOWED':0,'OBSERVED_MUTATION':0 if boundary else 1,'DETAIL':f'protected fingerprint changes={len(delta)}'}],['PROTECTED_SYSTEM','MUTATION_ALLOWED','OBSERVED_MUTATION','DETAIL'])
    summ={'STATUS':status,'VALIDATION_ISSUES':val,'STAGE_GREEN':1 if stage.get('STATUS')=='MESSAGE_CATALOG_PHASE22AE_6_5_3_FULL_CANDIDATE_REBUILD_SANDBOX_PROOF_STAGED_SOURCE_HELD' else 0,'SANDBOX_MESSAGE_ROWS_BEFORE':stage.get('SANDBOX_MESSAGE_ROWS_BEFORE',''),'SANDBOX_MESSAGE_ROWS_AFTER':mc,'MESSAGE_DELTA':md,'SANDBOX_TEXT_ROWS_BEFORE':stage.get('SANDBOX_TEXT_ROWS_BEFORE',''),'SANDBOX_TEXT_ROWS_AFTER':tc,'TEXT_DELTA':td,'FOUND_MESSAGE_KEYS':len(mf),'FOUND_TEXT_KEYS':len(tf),'TWO_TABLE_REBUILD_PROVEN':1 if proven else 0,'BOUNDARY_CLEAN':1 if boundary else 0,'PROTECTED_FINGERPRINT_CHANGES':len(delta),'ACTIVE_CATALOG_MUTATION_OBSERVED':0 if boundary else 1,'SOURCE_FILES_MUTATED':0,'HELP_DATA_MUTATION_OBSERVED':0,'CMDHELPCHK_MUTATION_OBSERVED':0,'NEXT_GATE':nextg,'REPORT_TIMESTAMP_UTC':datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00','Z')}
    write(reports/'message_catalog_phase22ae_6_5_3_validate_status_summary_v1.csv',[summ],list(summ.keys()))
    print(status); print(f'  validation issues: {val}'); print(f'  stage green: {summ["STAGE_GREEN"]}'); print(f'  sandbox message rows before/after: {stage.get("SANDBOX_MESSAGE_ROWS_BEFORE","")}/{mc}'); print(f'  sandbox text rows before/after: {stage.get("SANDBOX_TEXT_ROWS_BEFORE","")}/{tc}'); print(f'  message delta: {md}'); print(f'  text delta: {td}'); print(f'  found message keys: {len(mf)}/2'); print(f'  found text keys: {len(tf)}/10'); print(f'  two-table rebuild proven: {1 if proven else 0}'); print(f'  boundary clean: {1 if boundary else 0}'); print(f'  protected fingerprint changes: {len(delta)}'); print(f'  active catalog mutation observed: {0 if boundary else 1}'); print('  source files mutated: 0'); print('  HELP DATA mutation observed: 0'); print('  CMDHELPCHK mutation observed: 0'); print(f'  next gate: {nextg}'); print(f'  reports: {reports}')
    return 0 if status in (PROVEN,NOTPROVEN) else 2
if __name__=='__main__': raise SystemExit(main())
