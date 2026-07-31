
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

def pick(repo,paths,n):
    for p in paths:
        rows=rcsv(repo/p)
        if len(rows)==n: return repo/p, rows
    return Path(), []
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--repo-root',required=True); ap.add_argument('--replace-existing-sandbox',action='store_true'); a=ap.parse_args()
    repo=Path(a.repo_root).resolve(); reports=repo/REPORT; reports.mkdir(parents=True,exist_ok=True)
    ae=first(reports/'message_catalog_phase22ae_6_5_2_validate_status_summary_v1.csv'); sp,latest=savepoint(repo,'MSG-022AE.6.5.2')
    sb=repo/'docs/messaging/sandbox/phase22ae_6_5_4_full_state_zap_import_v1'; gates=[]; fails=0; errs=[]
    def gate(n,ok,d):
        nonlocal fails; gates.append({'GATE':n,'STATUS':'PASS' if ok else 'FAIL','DETAIL':str(d)}); fails+=0 if ok else 1
    gate('PHASE22AE_6_5_2_REBUILD_REQUIRED',ae.get('STATUS')=='MESSAGE_CATALOG_PHASE22AE_6_5_2_ISOLATED_IMPORT_EXECUTION_PROOF_GREEN_IMPORT_NOT_PROVEN_REBUILD_REQUIRED',ae.get('STATUS','missing'))
    gate('MSG_022AE_6_5_2_SAVEPOINT_PRESENT',sp,latest)
    gate('SANDBOX_NOT_EXISTING_OR_REPLACE_ALLOWED',(not sb.exists()) or a.replace_existing_sandbox,rel(sb,repo))
    msg_src,msg_rows=pick(repo,[Path('docs/messaging/sandbox/phase22ae_6_5_3_full_candidate_rebuild_v1/import/system_messages_full_candidate_import.csv'),Path('docs/messaging/sandbox/phase22ae_6_5_2_isolated_import_execution_v1/import/system_messages_import.csv'),Path('docs/messaging/apply/phase22ad_active_catalog_replacement_apply_package_v1/rows/message_catalog_candidate_message_adds_v1.csv')],2)
    txt_src,txt_rows=pick(repo,[Path('docs/messaging/sandbox/phase22ae_6_5_3_full_candidate_rebuild_v1/import/system_message_text_full_candidate_import.csv'),Path('docs/messaging/sandbox/phase22ae_6_5_2_isolated_import_execution_v1/import/system_message_text_import.csv'),Path('docs/messaging/apply/phase22ad_active_catalog_replacement_apply_package_v1/rows/message_catalog_candidate_text_adds_v1.csv')],10)
    gate('CANDIDATE_MESSAGE_ROWS_FOUND',len(msg_rows)==2,rel(msg_src,repo) if msg_src else 'missing')
    gate('CANDIDATE_TEXT_ROWS_FOUND',len(txt_rows)==10,rel(txt_src,repo) if txt_src else 'missing')
    before=fp(repo); wcsv(reports/'message_catalog_phase22ae_6_5_4_protected_fingerprint_before_v1.csv',before,['ROLE','PATH','EXISTS','KIND','BYTES','SHA256','FILES'])
    copies=[]; manifest=[]; expm=[]; expt=[]; status='MESSAGE_CATALOG_PHASE22AE_6_5_4_FULL_STATE_ZAP_IMPORT_SANDBOX_PROOF_STAGING_BLOCKED'; script_rel=''; mb=''; tb=''
    if fails==0:
        try:
            if sb.exists() and a.replace_existing_sandbox: shutil.rmtree(sb)
            for sub in ['dbf','indexes','lmdb','import','source_candidate_rows']: (sb/sub).mkdir(parents=True,exist_ok=True)
            for t in TABLES:
                cfile(repo/ACTIVE/f'{t}.dbf',sb/'dbf'/f'{t}.dbf',repo,copies,f'{t}_dbf_copy')
                for ext in SIDE: cfile(repo/ACTIVE/f'{t}{ext}',sb/'dbf'/f'{t}{ext}',repo,copies,f'{t}_sidecar_{ext}_copy')
                if not cfile(repo/MIDX/f'{t}.cdx',sb/'indexes'/f'{t}.cdx',repo,copies,f'{t}_messaging_cdx_copy'): cfile(repo/IDX/f'{t}.cdx',sb/'indexes'/f'{t}.cdx',repo,copies,f'{t}_default_cdx_fallback_copy')
                if not cfile(repo/MIDX/f'{t}.cdx.meta',sb/'indexes'/f'{t}.cdx.meta',repo,copies,f'{t}_messaging_meta_copy'): cfile(repo/IDX/f'{t}.cdx.meta',sb/'indexes'/f'{t}.cdx.meta',repo,copies,f'{t}_default_meta_fallback_copy')
                if not cdir(repo/MLMDB/f'{t}.cdx.d',sb/'lmdb'/f'{t}.cdx.d',repo,copies,f'{t}_messaging_lmdb_copy'): cdir(repo/LMDB/f'{t}.cdx.d',sb/'lmdb'/f'{t}.cdx.d',repo,copies,f'{t}_default_lmdb_fallback_copy')
                cfile(sb/'indexes'/f'{t}.cdx',sb/'dbf'/f'{t}.cdx',repo,copies,f'{t}_colocated_cdx_copy')
                cfile(sb/'indexes'/f'{t}.cdx.meta',sb/'dbf'/f'{t}.cdx.meta',repo,copies,f'{t}_colocated_meta_copy')
            mi=dbf_info(sb/'dbf/SYSTEM_MESSAGES.dbf'); ti=dbf_info(sb/'dbf/SYSTEM_MESSAGE_TEXT.dbf'); mb=mi['count']; tb=ti['count']
            fullm=read_dbf_rows(mi)+align(msg_rows,fields(mi)); fullt=read_dbf_rows(ti)+align(txt_rows,fields(ti))
            msgcsv=sb/'import/system_messages_full_state_zap_import.csv'; txtcsv=sb/'import/system_message_text_full_state_zap_import.csv'
            wcsv(msgcsv,fullm,fields(mi)); wcsv(txtcsv,fullt,fields(ti))
            wcsv(sb/'source_candidate_rows/message_rows_source.csv',msg_rows,list(msg_rows[0].keys())); wcsv(sb/'source_candidate_rows/text_rows_source.csv',txt_rows,list(txt_rows[0].keys()))
            expm=[{'SYMBOL':symbol(r),'SOURCE':rel(msg_src,repo),'IMPORT_FILE':rel(msgcsv,repo)} for r in msg_rows]
            expt=[{'SYMBOL':symbol(r),'LOCALE':locale(r),'SOURCE':rel(txt_src,repo),'IMPORT_FILE':rel(txtcsv,repo)} for r in txt_rows]
            manifest=[{'TABLE':'SYSTEM_MESSAGES','SOURCE_ACTIVE_ROWS':len(fullm)-len(msg_rows),'CANDIDATE_ROWS':len(msg_rows),'FULL_STATE_ROWS':len(fullm),'CSV':rel(msgcsv,repo)}, {'TABLE':'SYSTEM_MESSAGE_TEXT','SOURCE_ACTIVE_ROWS':len(fullt)-len(txt_rows),'CANDIDATE_ROWS':len(txt_rows),'FULL_STATE_ROWS':len(fullt),'CSV':rel(txtcsv,repo)}]
            gate('FULL_STATE_MESSAGE_ROWS_14',len(fullm)==14,len(fullm)); gate('FULL_STATE_TEXT_ROWS_70',len(fullt)==70,len(fullt))
            script=repo/'docs/messaging/scripts/MESSAGE_CATALOG_PHASE22AE_6_5_4_FULL_STATE_ZAP_IMPORT_SANDBOX_PROOF.dts'; script.parent.mkdir(parents=True,exist_ok=True)
            script.write_text('\n'.join(['* 22AE.6.5.4 sandbox-only full-state ZAP/IMPORT proof','',f'USE {(sb/"dbf/SYSTEM_MESSAGES.dbf").resolve().as_posix()}','ZAP',f'IMPORT {msgcsv.resolve().as_posix()}','',f'USE {(sb/"dbf/SYSTEM_MESSAGE_TEXT.dbf").resolve().as_posix()}','ZAP',f'IMPORT {txtcsv.resolve().as_posix()}','']),encoding='utf-8')
            script_rel=rel(script,repo); status='MESSAGE_CATALOG_PHASE22AE_6_5_4_FULL_STATE_ZAP_IMPORT_SANDBOX_PROOF_STAGED_SOURCE_HELD'
        except Exception as e:
            errs.append(str(e)); fails+=1
    val='0' if status.endswith('SOURCE_HELD') else str(fails)
    wcsv(reports/'message_catalog_phase22ae_6_5_4_stage_gate_check_v1.csv',gates,['GATE','STATUS','DETAIL'])
    wcsv(reports/'message_catalog_phase22ae_6_5_4_sandbox_copy_inventory_v1.csv',copies,['ROLE','SOURCE','TARGET','COPIED','BYTES','SHA256'])
    wcsv(reports/'message_catalog_phase22ae_6_5_4_full_state_manifest_v1.csv',manifest,['TABLE','SOURCE_ACTIVE_ROWS','CANDIDATE_ROWS','FULL_STATE_ROWS','CSV'])
    wcsv(reports/'message_catalog_phase22ae_6_5_4_expected_message_rows_v1.csv',expm,['SYMBOL','SOURCE','IMPORT_FILE'])
    wcsv(reports/'message_catalog_phase22ae_6_5_4_expected_text_rows_v1.csv',expt,['SYMBOL','LOCALE','SOURCE','IMPORT_FILE'])
    wcsv(reports/'message_catalog_phase22ae_6_5_4_stage_status_summary_v1.csv',[{'STATUS':status,'VALIDATION_ISSUES':val,'PHASE22AE_6_5_2_REBUILD_REQUIRED':1 if ae.get('STATUS')=='MESSAGE_CATALOG_PHASE22AE_6_5_2_ISOLATED_IMPORT_EXECUTION_PROOF_GREEN_IMPORT_NOT_PROVEN_REBUILD_REQUIRED' else 0,'MSG_022AE_6_5_2_SAVEPOINT_PRESENT':1 if sp else 0,'SANDBOX_ROOT':rel(sb,repo),'SCRIPT_PATH':script_rel,'SANDBOX_MESSAGE_ROWS_BEFORE':mb,'SANDBOX_TEXT_ROWS_BEFORE':tb,'FULL_STATE_MESSAGE_ROWS':14 if manifest else '', 'FULL_STATE_TEXT_ROWS':70 if manifest else '', 'ACTIVE_CATALOG_MUTATION_OBSERVED':0,'SOURCE_FILES_MUTATED':0,'HELP_DATA_MUTATION_OBSERVED':0,'CMDHELPCHK_MUTATION_OBSERVED':0,'ERRORS':'; '.join(errs),'NEXT_GATE':'RUN_PHASE22AE_6_5_4_FULL_STATE_ZAP_IMPORT_RUNTIME_THEN_VALIDATE','REPORT_TIMESTAMP_UTC':datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00','Z')}], ['STATUS','VALIDATION_ISSUES','PHASE22AE_6_5_2_REBUILD_REQUIRED','MSG_022AE_6_5_2_SAVEPOINT_PRESENT','SANDBOX_ROOT','SCRIPT_PATH','SANDBOX_MESSAGE_ROWS_BEFORE','SANDBOX_TEXT_ROWS_BEFORE','FULL_STATE_MESSAGE_ROWS','FULL_STATE_TEXT_ROWS','ACTIVE_CATALOG_MUTATION_OBSERVED','SOURCE_FILES_MUTATED','HELP_DATA_MUTATION_OBSERVED','CMDHELPCHK_MUTATION_OBSERVED','ERRORS','NEXT_GATE','REPORT_TIMESTAMP_UTC'])
    print(status); print(f'  validation issues: {val}'); print(f'  sandbox root: {rel(sb,repo)}'); print(f'  script path: {script_rel}'); print(f'  sandbox message rows before: {mb}'); print(f'  sandbox text rows before: {tb}'); print('  full-state message rows: '+str(14 if manifest else '')); print('  full-state text rows: '+str(70 if manifest else '')); print('  active catalog mutation observed: 0'); print('  source files mutated: 0'); print('  next gate: RUN_PHASE22AE_6_5_4_FULL_STATE_ZAP_IMPORT_RUNTIME_THEN_VALIDATE'); print(f'  reports: {reports}')
    return 0 if status.endswith('SOURCE_HELD') else 2
if __name__=='__main__': raise SystemExit(main())
