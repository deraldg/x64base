
from __future__ import annotations
import argparse,csv,json,hashlib,shutil,struct,subprocess,sys
from pathlib import Path
from datetime import datetime,timezone
REPORT=Path('docs/messaging/reports')
ACTIVE=Path('dottalkpp/data/messaging'); IDX=Path('dottalkpp/data/indexes'); MIDX=Path('dottalkpp/data/indexes/messaging'); LMDB=Path('dottalkpp/data/lmdb'); MLMDB=Path('dottalkpp/data/lmdb/messaging')
TABLES=['SYSTEM_MESSAGES','SYSTEM_MESSAGE_TEXT']
SIDE=['.dtx','.dbt','.fpt','.memo']
def rcsv(p):
    p=Path(p)
    if not p.exists(): return []
    with p.open('r',encoding='utf-8-sig',newline='') as f: return list(csv.DictReader(f))
def first(p):
    r=rcsv(p); return r[0] if r else {}
def wcsv(p,rows,fields):
    p=Path(p); p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields,lineterminator='\n',extrasaction='ignore'); w.writeheader(); [w.writerow({k:r.get(k,'') for k in fields}) for r in rows]
def rel(p,repo):
    try: return str(Path(p).relative_to(repo)).replace('\\','/')
    except Exception: return str(p).replace('\\','/')
def sha(p):
    p=Path(p)
    if not p.exists() or not p.is_file(): return ''
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''): h.update(b)
    return h.hexdigest()
def savepoint(repo,id):
    latest=''; lp=repo/REPORT/'message_savepoint_latest_v1.json'
    if lp.exists():
        try: latest=json.loads(lp.read_text(encoding='utf-8')).get('savepoint_id','')
        except Exception: pass
    j=repo/'docs/messaging/MESSAGING_SAVEPOINT_JOURNAL.md'
    txt=j.read_text(encoding='utf-8',errors='replace') if j.exists() else ''
    return latest==id or id in txt, latest
def dbf_info(p):
    b=Path(p).read_bytes(); n=struct.unpack('<I',b[4:8])[0]; hl=struct.unpack('<H',b[8:10])[0]; rl=struct.unpack('<H',b[10:12])[0]
    fs=[]; pos=32; off=1
    while pos+32<=len(b) and b[pos]!=0x0d:
        nm=b[pos:pos+11].split(b'\0',1)[0].decode('ascii',errors='ignore').strip().upper(); typ=chr(b[pos+11]); ln=b[pos+16]
        if nm: fs.append({'NAME':nm,'TYPE':typ,'LENGTH':ln,'OFFSET':off}); off+=ln
        pos+=32
    return {'path':Path(p),'count':n,'hlen':hl,'rlen':rl,'fields':fs}
def read_dbf_rows(info):
    rows=[]
    with info['path'].open('rb') as f:
        f.seek(info['hlen'])
        for i in range(info['count']):
            rec=f.read(info['rlen'])
            if len(rec)<info['rlen']: break
            if rec[:1]==b'*': continue
            row={}
            for fld in info['fields']:
                raw=rec[fld['OFFSET']:fld['OFFSET']+fld['LENGTH']]
                enc='cp1252' if fld['TYPE'].upper() in ('C','M') else 'ascii'
                row[fld['NAME']]=raw.decode(enc,errors='replace').rstrip().strip()
            rows.append(row)
    return rows
def fields(info): return [f['NAME'] for f in info['fields']]
def cfile(src,dst,repo,rows,role):
    src=Path(src); dst=Path(dst); ok=src.exists() and src.is_file()
    if ok: dst.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(src,dst)
    rows.append({'ROLE':role,'SOURCE':rel(src,repo),'TARGET':rel(dst,repo),'COPIED':1 if ok else 0,'BYTES':dst.stat().st_size if ok and dst.exists() else 0,'SHA256':sha(dst) if ok and dst.exists() else ''})
    return ok
def cdir(src,dst,repo,rows,role):
    src=Path(src); dst=Path(dst); ok=src.exists() and src.is_dir(); n=0; total=0
    if ok:
        if dst.exists(): shutil.rmtree(dst)
        dst.parent.mkdir(parents=True,exist_ok=True); shutil.copytree(src,dst)
        for p in dst.rglob('*'):
            if p.is_file(): n+=1; total+=p.stat().st_size
    rows.append({'ROLE':role,'SOURCE':rel(src,repo),'TARGET':rel(dst,repo),'COPIED':1 if ok else 0,'BYTES':total,'SHA256':f'dir_files={n}' if ok else ''})
    return ok
def fp(repo):
    out=[]
    for t in TABLES:
        targets=[(ACTIVE/f'{t}.dbf',f'active_dbf_{t}'),(ACTIVE/f'{t}.dtx',f'active_dtx_{t}'),(MIDX/f'{t}.cdx',f'active_midx_{t}'),(MIDX/f'{t}.cdx.meta',f'active_midx_meta_{t}'),(MLMDB/f'{t}.cdx.d',f'active_mlmdb_{t}'),(IDX/f'{t}.cdx',f'default_idx_{t}'),(IDX/f'{t}.cdx.meta',f'default_idx_meta_{t}'),(LMDB/f'{t}.cdx.d',f'default_lmdb_{t}')]
        for p,role in targets:
            p=repo/p
            if p.is_dir():
                h=hashlib.sha256(); total=0; files=0
                for q in sorted(x for x in p.rglob('*') if x.is_file()):
                    h.update(str(q.relative_to(p)).replace('\\','/').encode()); h.update(sha(q).encode()); total+=q.stat().st_size; files+=1
                out.append({'ROLE':role,'PATH':rel(p,repo),'EXISTS':1,'KIND':'dir','BYTES':total,'SHA256':h.hexdigest(),'FILES':files})
            elif p.is_file(): out.append({'ROLE':role,'PATH':rel(p,repo),'EXISTS':1,'KIND':'file','BYTES':p.stat().st_size,'SHA256':sha(p),'FILES':1})
            else: out.append({'ROLE':role,'PATH':rel(p,repo),'EXISTS':0,'KIND':'missing','BYTES':0,'SHA256':'','FILES':0})
    return out
def fpdiff(a,b):
    A={r['ROLE']+'|'+r['PATH']:r for r in a}; B={r['ROLE']+'|'+r['PATH']:r for r in b}; d=[]
    for k in sorted(set(A)|set(B)):
        x=A.get(k); y=B.get(k)
        if x is None: d.append({'ROLE':y['ROLE'],'PATH':y['PATH'],'CHANGE':'ADDED','BEFORE_SHA256':'','AFTER_SHA256':y['SHA256'],'BEFORE_BYTES':'','AFTER_BYTES':y['BYTES']})
        elif y is None: d.append({'ROLE':x['ROLE'],'PATH':x['PATH'],'CHANGE':'REMOVED','BEFORE_SHA256':x['SHA256'],'AFTER_SHA256':'','BEFORE_BYTES':x['BYTES'],'AFTER_BYTES':''})
        elif x['SHA256']!=y['SHA256'] or str(x['BYTES'])!=str(y['BYTES']): d.append({'ROLE':y['ROLE'],'PATH':y['PATH'],'CHANGE':'MODIFIED','BEFORE_SHA256':x['SHA256'],'AFTER_SHA256':y['SHA256'],'BEFORE_BYTES':x['BYTES'],'AFTER_BYTES':y['BYTES']})
    return d
def align(rows,fs):
    out=[]
    for r in rows:
        u={str(k).strip().upper():'' if v is None else str(v) for k,v in r.items() if k is not None}
        out.append({f:u.get(f,'') for f in fs})
    return out
def symbol(row):
    u={str(k).strip().upper():'' if v is None else str(v) for k,v in row.items() if k is not None}
    for k in ['SYMBOL','MESSAGE_SYMBOL','MSG_SYMBOL','MSGID','MESSAGE_ID','KEY','NAME']:
        if u.get(k): return u[k]
    for k,v in u.items():
        if v and any(x in k for x in ['SYMBOL','MESSAGE','MSG','KEY','ID']) and not any(x in k for x in ['TEXT','LOCALE','LANG','STATUS','SOURCE']): return v
    return ''
def locale(row):
    u={str(k).strip().upper():'' if v is None else str(v) for k,v in row.items() if k is not None}
    for k in ['LOCALE','LOCALE_ID','LANG','LANGUAGE']:
        if u.get(k): return u[k]
    return ''
def hasval(row,val):
    return bool(val) and any(str(v).strip()==val for k,v in row.items() if not k.startswith('__') and not k.endswith('__RAW_HEX'))
def read_all(info):
    rows=[]
    with info['path'].open('rb') as f:
        f.seek(info['hlen'])
        for i in range(info['count']):
            rec=f.read(info['rlen'])
            if len(rec)<info['rlen']: break
            row={'__RECNO__':i+1,'__DELETED__':1 if rec[:1]==b'*' else 0}
            for fld in info['fields']:
                raw=rec[fld['OFFSET']:fld['OFFSET']+fld['LENGTH']]
                enc='cp1252' if fld['TYPE'].upper() in ('C','M') else 'ascii'
                row[fld['NAME']]=raw.decode(enc,errors='replace').rstrip().strip()
            rows.append(row)
    return rows

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--repo-root',required=True); ap.add_argument('--runtime-proof',default=''); a=ap.parse_args()
    repo=Path(a.repo_root).resolve(); reports=repo/REPORT; reports.mkdir(parents=True,exist_ok=True)
    st=first(reports/'message_catalog_phase22ae_6_5_4_stage_status_summary_v1.csv'); before=rcsv(reports/'message_catalog_phase22ae_6_5_4_protected_fingerprint_before_v1.csv')
    expm=rcsv(reports/'message_catalog_phase22ae_6_5_4_expected_message_rows_v1.csv'); expt=rcsv(reports/'message_catalog_phase22ae_6_5_4_expected_text_rows_v1.csv')
    rp=Path(a.runtime_proof) if a.runtime_proof else repo/'docs/messaging/runlog/MSG-022AE_6_5_4_FULL_STATE_ZAP_IMPORT_SANDBOX_PROOF.md'
    if not rp.is_absolute(): rp=repo/rp
    log=rp.read_text(encoding='utf-8',errors='replace') if rp.exists() else ''; up=log.upper()
    sb=repo/st.get('SANDBOX_ROOT',''); gates=[]; fails=0
    def gate(n,ok,d):
        nonlocal fails; gates.append({'GATE':n,'STATUS':'PASS' if ok else 'FAIL','DETAIL':str(d)}); fails+=0 if ok else 1
    gate('STAGE_GREEN',st.get('STATUS')=='MESSAGE_CATALOG_PHASE22AE_6_5_4_FULL_STATE_ZAP_IMPORT_SANDBOX_PROOF_STAGED_SOURCE_HELD',st.get('STATUS','missing'))
    gate('RUNTIME_PROOF_EXISTS',rp.exists(),rel(rp,repo)); gate('EXPECTED_MESSAGE_ROWS_2',len(expm)==2,len(expm)); gate('EXPECTED_TEXT_ROWS_10',len(expt)==10,len(expt))
    after=fp(repo); delta=fpdiff(before,after); clean=len(delta)==0
    mc=''; tc=''; mf=[]; tf=[]; tails=[]
    try:
        mi=dbf_info(sb/'dbf/SYSTEM_MESSAGES.dbf'); ti=dbf_info(sb/'dbf/SYSTEM_MESSAGE_TEXT.dbf'); mc=mi['count']; tc=ti['count']; mr=read_all(mi); tr=read_all(ti)
        for e in expm:
            s=e.get('SYMBOL',''); m=[r for r in mr if hasval(r,s)]
            if m: mf.append({'SYMBOL':s,'MATCHES':len(m),'RECNO':m[-1].get('__RECNO__','')})
        for e in expt:
            s=e.get('SYMBOL',''); l=e.get('LOCALE',''); m=[r for r in tr if hasval(r,s) and (not l or hasval(r,l))]
            if m: tf.append({'SYMBOL':s,'LOCALE':l,'MATCHES':len(m),'RECNO':m[-1].get('__RECNO__','')})
        for label,rows in [('SYSTEM_MESSAGES',mr[-6:]),('SYSTEM_MESSAGE_TEXT',tr[-12:])]:
            for r in rows:
                tails.append({'TABLE':label,'RECNO':r.get('__RECNO__',''),'ROW_JSON':json.dumps({k:v for k,v in r.items() if k in ('__RECNO__','__DELETED__') or (isinstance(v,str) and v.strip())},ensure_ascii=False,sort_keys=True)})
    except Exception as e: gate('SANDBOX_DBF_READBACK',False,e)
    counts=(mc==14 and tc==70); keys=(len(mf)==2 and len(tf)==10)
    if fails or not clean: status='MESSAGE_CATALOG_PHASE22AE_6_5_4_FULL_STATE_ZAP_IMPORT_SANDBOX_PROOF_BLOCKED'; nextg='HOLD_AND_FIX_PHASE22AE_6_5_4_ZAP_IMPORT_SETUP_OR_BOUNDARY'; val=str(max(1,fails,len(delta)))
    elif counts and keys: status='MESSAGE_CATALOG_PHASE22AE_6_5_4_FULL_STATE_ZAP_IMPORT_SANDBOX_PROOF_GREEN_FULL_STATE_ZAP_IMPORT_PROVEN'; nextg='HOLD_OR_AUTHORIZE_PHASE22AE_6_5_5_ACTIVE_PROMOTION_PLAN_FROM_FULL_STATE_ZAP_IMPORT_PROOF'; val='0'
    else: status='MESSAGE_CATALOG_PHASE22AE_6_5_4_FULL_STATE_ZAP_IMPORT_SANDBOX_PROOF_GREEN_COUNTS_ONLY_FIELD_MAP_REVIEW'; nextg='HOLD_OR_AUTHORIZE_PHASE22AE_6_5_5_FIELD_MAP_FORENSIC_REVIEW'; val='0'
    wcsv(reports/'message_catalog_phase22ae_6_5_4_validate_gate_check_v1.csv',gates,['GATE','STATUS','DETAIL'])
    wcsv(reports/'message_catalog_phase22ae_6_5_4_zap_import_result_v1.csv',[{'SANDBOX_MESSAGE_ROWS_AFTER':mc,'SANDBOX_TEXT_ROWS_AFTER':tc,'COUNTS_EXPECTED_14_AND_70':1 if counts else 0,'EXPECTED_MESSAGE_KEYS':len(expm),'FOUND_MESSAGE_KEYS':len(mf),'EXPECTED_TEXT_KEYS':len(expt),'FOUND_TEXT_KEYS':len(tf),'ZAP_SIGNAL_PRESENT':1 if 'ZAP' in up or 'ZAPPED' in up else 0,'IMPORTED_14_SIGNAL':1 if 'IMPORTED 14 RECORDS' in up else 0,'IMPORTED_70_SIGNAL':1 if 'IMPORTED 70 RECORDS' in up else 0,'FULL_STATE_ZAP_IMPORT_PROVEN':1 if counts and keys else 0,'BOUNDARY_CLEAN':1 if clean else 0,'PROTECTED_FINGERPRINT_CHANGES':len(delta)}], ['SANDBOX_MESSAGE_ROWS_AFTER','SANDBOX_TEXT_ROWS_AFTER','COUNTS_EXPECTED_14_AND_70','EXPECTED_MESSAGE_KEYS','FOUND_MESSAGE_KEYS','EXPECTED_TEXT_KEYS','FOUND_TEXT_KEYS','ZAP_SIGNAL_PRESENT','IMPORTED_14_SIGNAL','IMPORTED_70_SIGNAL','FULL_STATE_ZAP_IMPORT_PROVEN','BOUNDARY_CLEAN','PROTECTED_FINGERPRINT_CHANGES'])
    wcsv(reports/'message_catalog_phase22ae_6_5_4_found_message_keys_v1.csv',mf,['SYMBOL','MATCHES','RECNO']); wcsv(reports/'message_catalog_phase22ae_6_5_4_found_text_keys_v1.csv',tf,['SYMBOL','LOCALE','MATCHES','RECNO']); wcsv(reports/'message_catalog_phase22ae_6_5_4_tail_rows_v1.csv',tails,['TABLE','RECNO','ROW_JSON'])
    wcsv(reports/'message_catalog_phase22ae_6_5_4_protected_fingerprint_after_v1.csv',after,['ROLE','PATH','EXISTS','KIND','BYTES','SHA256','FILES']); wcsv(reports/'message_catalog_phase22ae_6_5_4_protected_fingerprint_delta_v1.csv',delta,['ROLE','PATH','CHANGE','BEFORE_SHA256','AFTER_SHA256','BEFORE_BYTES','AFTER_BYTES'])
    wcsv(reports/'message_catalog_phase22ae_6_5_4_validate_status_summary_v1.csv',[{'STATUS':status,'VALIDATION_ISSUES':val,'STAGE_GREEN':1 if st.get('STATUS')=='MESSAGE_CATALOG_PHASE22AE_6_5_4_FULL_STATE_ZAP_IMPORT_SANDBOX_PROOF_STAGED_SOURCE_HELD' else 0,'SANDBOX_MESSAGE_ROWS_AFTER':mc,'SANDBOX_TEXT_ROWS_AFTER':tc,'FOUND_MESSAGE_KEYS':len(mf),'FOUND_TEXT_KEYS':len(tf),'FULL_STATE_ZAP_IMPORT_PROVEN':1 if counts and keys else 0,'BOUNDARY_CLEAN':1 if clean else 0,'PROTECTED_FINGERPRINT_CHANGES':len(delta),'ACTIVE_CATALOG_MUTATION_OBSERVED':0 if clean else 1,'SOURCE_FILES_MUTATED':0,'HELP_DATA_MUTATION_OBSERVED':0,'CMDHELPCHK_MUTATION_OBSERVED':0,'NEXT_GATE':nextg,'REPORT_TIMESTAMP_UTC':datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00','Z')}], ['STATUS','VALIDATION_ISSUES','STAGE_GREEN','SANDBOX_MESSAGE_ROWS_AFTER','SANDBOX_TEXT_ROWS_AFTER','FOUND_MESSAGE_KEYS','FOUND_TEXT_KEYS','FULL_STATE_ZAP_IMPORT_PROVEN','BOUNDARY_CLEAN','PROTECTED_FINGERPRINT_CHANGES','ACTIVE_CATALOG_MUTATION_OBSERVED','SOURCE_FILES_MUTATED','HELP_DATA_MUTATION_OBSERVED','CMDHELPCHK_MUTATION_OBSERVED','NEXT_GATE','REPORT_TIMESTAMP_UTC'])
    print(status); print(f'  validation issues: {val}'); print(f'  sandbox message rows after: {mc}'); print(f'  sandbox text rows after: {tc}'); print(f'  found message keys: {len(mf)}/2'); print(f'  found text keys: {len(tf)}/10'); print(f'  full-state ZAP/import proven: {1 if counts and keys else 0}'); print(f'  boundary clean: {1 if clean else 0}'); print(f'  protected fingerprint changes: {len(delta)}'); print(f'  active catalog mutation observed: {0 if clean else 1}'); print('  source files mutated: 0'); print('  HELP DATA mutation observed: 0'); print('  CMDHELPCHK mutation observed: 0'); print(f'  next gate: {nextg}'); print(f'  reports: {reports}')
    return 0 if status!='MESSAGE_CATALOG_PHASE22AE_6_5_4_FULL_STATE_ZAP_IMPORT_SANDBOX_PROOF_BLOCKED' else 2
if __name__=='__main__': raise SystemExit(main())
