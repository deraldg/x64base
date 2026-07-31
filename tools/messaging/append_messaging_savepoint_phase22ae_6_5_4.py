
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
    ap=argparse.ArgumentParser(); ap.add_argument('--repo-root',required=True); ap.add_argument('--accept-messaging-savepoint',action='store_true'); a=ap.parse_args()
    repo=Path(a.repo_root).resolve(); row=first(repo/'docs/messaging/reports/message_catalog_phase22ae_6_5_4_validate_status_summary_v1.csv')
    ok={'MESSAGE_CATALOG_PHASE22AE_6_5_4_FULL_STATE_ZAP_IMPORT_SANDBOX_PROOF_GREEN_FULL_STATE_ZAP_IMPORT_PROVEN','MESSAGE_CATALOG_PHASE22AE_6_5_4_FULL_STATE_ZAP_IMPORT_SANDBOX_PROOF_GREEN_COUNTS_ONLY_FIELD_MAP_REVIEW'}
    if not a.accept_messaging_savepoint or row.get('STATUS','') not in ok:
        print(f"[MSG-022AE.6.5.4] Refusing savepoint: got {row.get('STATUS','missing')}",file=sys.stderr); return 2
    cmd=[sys.executable,str(repo/'tools/messaging/append_messaging_savepoint.py'),'--repo-root',str(repo),'--savepoint-id','MSG-022AE.6.5.4','--lane','MESSAGING','--status',row.get('STATUS',''),'--phase','Phase 22AE.6.5.4 full-state ZAP/IMPORT sandbox proof','--summary','Full-state ZAP/IMPORT sandbox proof completed against isolated DBF copies; active promotion remains gated by resulting status and next gate.','--next-gate',row.get('NEXT_GATE',''),'--source-reports','docs/messaging/reports/message_catalog_phase22ae_6_5_4_validate_status_summary_v1.csv;docs/messaging/reports/message_catalog_phase22ae_6_5_4_zap_import_result_v1.csv;docs/messaging/reports/message_catalog_phase22ae_6_5_4_found_message_keys_v1.csv;docs/messaging/reports/message_catalog_phase22ae_6_5_4_found_text_keys_v1.csv','--messages',row.get('SANDBOX_MESSAGE_ROWS_AFTER',''),'--text-rows',row.get('SANDBOX_TEXT_ROWS_AFTER',''),'--locales','en-US;es;fr;de;it','--validation-issues',row.get('VALIDATION_ISSUES','0'),'--allowed-candidate-mutations','isolated sandbox ZAP/IMPORT only','--forbidden-active-mutations','no active DBF/catalog mutation; no active CDX/index mutation; no active LMDB mutation; no source edits; no HELP DATA mutation; no CMDHELPCHK mutation','--accept-messaging-savepoint']
    return subprocess.call(cmd)
if __name__=='__main__': raise SystemExit(main())
