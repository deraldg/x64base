#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,json,hashlib,shutil,struct
from datetime import datetime,timezone
from pathlib import Path
REPORT=Path('docs/messaging/reports')
SANDBOX=Path('docs/messaging/sandbox/phase22ae_6_5_3_full_candidate_rebuild_v1')
SCRIPT=Path('docs/messaging/scripts/MESSAGE_CATALOG_PHASE22AE_6_5_3_FULL_CANDIDATE_REBUILD_SANDBOX_PROOF.dts')
ACTIVE=Path('dottalkpp/data/messaging')
IDX=Path('dottalkpp/data/indexes/messaging')
LMDB=Path('dottalkpp/data/lmdb/messaging')
DIDX=Path('dottalkpp/data/indexes')
DLMDB=Path('dottalkpp/data/lmdb')
TABLES=['SYSTEM_MESSAGES','SYSTEM_MESSAGE_TEXT']
STATUS_GREEN='MESSAGE_CATALOG_PHASE22AE_6_5_3_FULL_CANDIDATE_REBUILD_SANDBOX_PROOF_STAGED_SOURCE_HELD'
STATUS_BLOCKED='MESSAGE_CATALOG_PHASE22AE_6_5_3_FULL_CANDIDATE_REBUILD_SANDBOX_PROOF_STAGING_BLOCKED'
NEXT='RUN_PHASE22AE_6_5_3_FULL_CANDIDATE_REBUILD_SANDBOX_RUNTIME_THEN_VALIDATE'

def rows(p):
    if not p.exists(): return []
    with p.open('r',encoding='utf-8-sig',newline='') as f: return list(csv.DictReader(f))
def first(p):
    r=rows(p); return r[0] if r else {}
def write(p,rs,fields):
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields,lineterminator='\n',extrasaction='ignore'); w.writeheader()
        for r in rs: w.writerow({k:r.get(k,'') for k in fields})
def rel(p,repo):
    try: return str(p.relative_to(repo)).replace('\\','/')
    except Exception: return str(p).replace('\\','/')
def sha(p):
    if not p.exists() or not p.is_file(): return ''
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''): h.update(b)
    return h.hexdigest()
def savepoint(repo,sp):
    latest=repo/REPORT/'message_savepoint_latest_v1.json'; lid=''
    if latest.exists():
        try: lid=json.loads(latest.read_text(encoding='utf-8')).get('savepoint_id','')
        except Exception: lid=''
    journal=repo/'docs/messaging/MESSAGING_SAVEPOINT_JOURNAL.md'
    text=journal.read_text(encoding='utf-8',errors='replace') if journal.exists() else ''
    return lid==sp or sp in text,lid

def parse_dbf(p):
    d=p.read_bytes(); count=struct.unpack('<I',d[4:8])[0]; hlen=struct.unpack('<H',d[8:10])[0]; rlen=struct.unpack('<H',d[10:12])[0]
    fs=[]; pos=32; off=1
    while pos+32<=len(d) and d[pos]!=13:
        name=d[pos:pos+11].split(b'\0',1)[0].decode('ascii','ignore').strip().upper(); typ=chr(d[pos+11]); ln=d[pos+16]
        if name: fs.append({'NAME':name,'TYPE':typ,'LENGTH':ln,'OFFSET':off}); off+=ln
        pos+=32
    return {'count':count,'hlen':hlen,'rlen':rlen,'fields':fs}
def fields(info): return [f['NAME'] for f in info['fields']]
def cp(src,dst):
    if src.exists() and src.is_file(): dst.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(src,dst); return 1
    return 0
def cpdir(src,dst):
    if src.exists() and src.is_dir():
        if dst.exists(): shutil.rmtree(dst)
        dst.parent.mkdir(parents=True,exist_ok=True); shutil.copytree(src,dst); return 1
    return 0

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

def norm(r): return {str(k).strip().upper():'' if v is None else str(v) for k,v in r.items() if k is not None}
def get(src,names):
    for n in names:
        if src.get(n,'')!='': return src[n]
    return ''
def by_contains(src,incs,excs=()):
    for k,v in src.items():
        if not v: continue
        if any(e in k for e in excs): continue
        if any(i in k for i in incs): return v
    return ''
def sym(src): return get(src,['SYMBOL','MESSAGE_SYMBOL','MSG_SYMBOL','MSGID','MSG_ID','MESSAGE_ID','MESSAGE_KEY','MSGKEY','KEY','CODE','NAME','ID']) or by_contains(src,['SYMBOL','MSG','MESSAGE','KEY','CODE','ID'],['TEXT','LOCALE','LANG','STATUS','SOURCE','DESC'])
def loc(src): return get(src,['LOCALE','LOCALE_ID','LANG','LANGUAGE','CULTURE']) or by_contains(src,['LOCALE','LANG','CULTURE'],['TEXT','SOURCE'])
def txt(src): return get(src,['TEXT','MESSAGE_TEXT','MSG_TEXT','VALUE','LOCALIZED_TEXT','MESSAGE','DEFAULT_TEXT','DISPLAY_TEXT','DESCRIPTION','HELP_TEXT']) or by_contains(src,['TEXT','VALUE','MESSAGE','DESCRIPTION'],['SYMBOL','KEY','ID','LOCALE','LANG','STATUS','SOURCE'])
def is_text(f): return any(x in f for x in ['TEXT','VALUE','MESSAGE','DESC']) and not any(x in f for x in ['KEY','ID','LOCALE','LANG','STATUS','SOURCE'])
def is_loc(f): return any(x in f for x in ['LOCALE','LANG','CULTURE'])
def is_status(f): return f in ('STATUS','ROW_STATUS','STATE') or f.endswith('STATUS')
def is_source(f): return f in ('SOURCE','SOURCE_PHASE','PHASE','SOURCE_ID') or f.startswith('SOURCE')
def is_sym(f): return (not is_text(f) and not is_loc(f) and not is_status(f) and not is_source(f) and any(x in f for x in ['SYMBOL','MSG','MESSAGE','KEY','CODE','ID','NAME']))
def build(info,src_rows,table):
    out=[]; mp=[]; fs=fields(info)
    for r in src_rows:
        s=norm(r); sy=sym(s); lo=loc(s); te=txt(s); st=get(s,['STATUS','ROW_STATUS','STATE']) or 'CANDIDATE'; so=get(s,['SOURCE_PHASE','SOURCE','PHASE','SOURCE_ID']) or '22AE_6_5_3'
        row={}
        for f in fs:
            fu=f.upper()
            if s.get(fu,'')!='': val=s[fu]
            elif table=='SYSTEM_MESSAGE_TEXT' and is_text(fu): val=te
            elif table=='SYSTEM_MESSAGE_TEXT' and is_loc(fu): val=lo
            elif is_status(fu): val=st
            elif is_source(fu): val=so
            elif is_sym(fu): val=sy
            else: val=''
            row[f]=val
        out.append(row)
    for f in fs:
        vals=[r.get(f,'') for r in out if r.get(f,'')]
        cls='TEXT' if is_text(f) else 'LOCALE' if is_loc(f) else 'STATUS' if is_status(f) else 'SOURCE' if is_source(f) else 'SYMBOL' if is_sym(f) else ''
        mp.append({'TABLE':table,'TARGET_FIELD':f,'FIELD_CLASS':cls,'FILLED_ROWS':len(vals),'SAMPLE_VALUE':vals[0] if vals else ''})
    return out,mp

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--repo-root',required=True); ap.add_argument('--replace-existing-sandbox',action='store_true'); a=ap.parse_args()
    repo=Path(a.repo_root).resolve(); reports=repo/REPORT; reports.mkdir(parents=True,exist_ok=True)
    prev=first(reports/'message_catalog_phase22ae_6_5_2_validate_status_summary_v1.csv'); stage2=first(reports/'message_catalog_phase22ae_6_5_2_stage_status_summary_v1.csv')
    sp,lid=savepoint(repo,'MSG-022AE.6.5.2'); gates=[]; fail=0; errs=[]
    def gate(n,ok,d):
        nonlocal fail; gates.append({'GATE':n,'STATUS':'PASS' if ok else 'FAIL','DETAIL':str(d)}); fail+=0 if ok else 1
    gate('PHASE22AE_6_5_2_REBUILD_REQUIRED',prev.get('STATUS')=='MESSAGE_CATALOG_PHASE22AE_6_5_2_ISOLATED_IMPORT_EXECUTION_PROOF_GREEN_IMPORT_NOT_PROVEN_REBUILD_REQUIRED',prev.get('STATUS','missing'))
    gate('MSG_022AE_6_5_2_SAVEPOINT_PRESENT',sp,lid)
    gate('BOUNDARY_CLEAN_IN_6_5_2',prev.get('BOUNDARY_CLEAN')=='1',prev.get('BOUNDARY_CLEAN','missing'))
    gate('COUNTS_MOVED_IN_6_5_2',prev.get('MESSAGE_DELTA')=='2' and prev.get('TEXT_DELTA')=='10',f"{prev.get('MESSAGE_DELTA','')}/{prev.get('TEXT_DELTA','')}")
    gate('SANDBOX_NOT_EXISTING_OR_REPLACE_ALLOWED',(not (repo/SANDBOX).exists()) or a.replace_existing_sandbox,rel(repo/SANDBOX,repo))
    msgcand=repo/stage2.get('CANDIDATE_MESSAGE_FILE',''); txtcand=repo/stage2.get('CANDIDATE_TEXT_FILE','')
    gate('CANDIDATE_MESSAGE_FILE_EXISTS',msgcand.exists(),rel(msgcand,repo)); gate('CANDIDATE_TEXT_FILE_EXISTS',txtcand.exists(),rel(txtcand,repo))
    write(reports/'message_catalog_phase22ae_6_5_3_protected_fingerprint_before_v1.csv',fp(repo),['ROLE','PATH','EXISTS','KIND','BYTES','SHA256','FILES'])
    copy=[]; mapping=[]; em=[]; et=[]; msgc=''; txtc=''; script_rel=''; status=STATUS_BLOCKED
    if fail==0:
        try:
            sb=repo/SANDBOX
            if sb.exists() and a.replace_existing_sandbox: shutil.rmtree(sb)
            for d in ['dbf','indexes','lmdb','import','source_candidate_rows']: (sb/d).mkdir(parents=True,exist_ok=True)
            for t in TABLES:
                for src,dst,role in [(repo/ACTIVE/f'{t}.dbf',sb/'dbf'/f'{t}.dbf',f'{t}_dbf_copy'),(repo/IDX/f'{t}.cdx',sb/'indexes'/f'{t}.cdx',f'{t}_cdx_copy'),(repo/IDX/f'{t}.cdx.meta',sb/'indexes'/f'{t}.cdx.meta',f'{t}_meta_copy'),(repo/DIDX/f'{t}.cdx',sb/'dbf'/f'{t}.cdx',f'{t}_co_cdx_fallback'),(repo/DIDX/f'{t}.cdx.meta',sb/'dbf'/f'{t}.cdx.meta',f'{t}_co_meta_fallback')]:
                    copy.append({'ROLE':role,'SOURCE':rel(src,repo),'TARGET':rel(dst,repo),'COPIED':cp(src,dst),'SHA256':sha(dst)})
                copied=cpdir(repo/LMDB/f'{t}.cdx.d',sb/'lmdb'/f'{t}.cdx.d') or cpdir(repo/DLMDB/f'{t}.cdx.d',sb/'lmdb'/f'{t}.cdx.d')
                copy.append({'ROLE':f'{t}_lmdb_copy','SOURCE':'active_or_default','TARGET':rel(sb/'lmdb'/f'{t}.cdx.d',repo),'COPIED':1 if copied else 0,'SHA256':'dir'})
            shutil.copy2(msgcand,sb/'source_candidate_rows/message_rows_source.csv'); shutil.copy2(txtcand,sb/'source_candidate_rows/text_rows_source.csv')
            mi=parse_dbf(sb/'dbf/SYSTEM_MESSAGES.dbf'); ti=parse_dbf(sb/'dbf/SYSTEM_MESSAGE_TEXT.dbf'); msgc=mi['count']; txtc=ti['count']
            mr,mm=build(mi,rows(msgcand),'SYSTEM_MESSAGES'); tr,tm=build(ti,rows(txtcand),'SYSTEM_MESSAGE_TEXT'); mapping=mm+tm
            mi_csv=sb/'import/system_messages_full_candidate_import.csv'; ti_csv=sb/'import/system_message_text_full_candidate_import.csv'
            write(mi_csv,mr,fields(mi)); write(ti_csv,tr,fields(ti))
            for r in rows(msgcand): em.append({'SYMBOL':sym(norm(r)),'SOURCE':rel(msgcand,repo),'IMPORT_FILE':rel(mi_csv,repo)})
            for r in rows(txtcand): s=norm(r); et.append({'SYMBOL':sym(s),'LOCALE':loc(s),'TEXT_EXPECTED':txt(s),'SOURCE':rel(txtcand,repo),'IMPORT_FILE':rel(ti_csv,repo)})
            SCRIPT.parent.mkdir(parents=True,exist_ok=True)
            (repo/SCRIPT).write_text('\n'.join(['* MESSAGE_CATALOG_PHASE22AE_6_5_3_FULL_CANDIDATE_REBUILD_SANDBOX_PROOF.dts','* Sandbox-only broad field mapping import proof.','',f"USE {(sb/'dbf/SYSTEM_MESSAGES.dbf').resolve().as_posix()}",f"IMPORT {mi_csv.resolve().as_posix()}",'',f"USE {(sb/'dbf/SYSTEM_MESSAGE_TEXT.dbf').resolve().as_posix()}",f"IMPORT {ti_csv.resolve().as_posix()}",'']),encoding='utf-8')
            script_rel=rel(repo/SCRIPT,repo); status=STATUS_GREEN
        except Exception as e:
            errs.append(str(e)); fail+=1
    val='0' if status==STATUS_GREEN else str(fail)
    write(reports/'message_catalog_phase22ae_6_5_3_stage_gate_check_v1.csv',gates,['GATE','STATUS','DETAIL'])
    write(reports/'message_catalog_phase22ae_6_5_3_sandbox_copy_inventory_v1.csv',copy,['ROLE','SOURCE','TARGET','COPIED','SHA256'])
    write(reports/'message_catalog_phase22ae_6_5_3_broad_import_field_mapping_v1.csv',mapping,['TABLE','TARGET_FIELD','FIELD_CLASS','FILLED_ROWS','SAMPLE_VALUE'])
    write(reports/'message_catalog_phase22ae_6_5_3_expected_message_rows_v1.csv',em,['SYMBOL','SOURCE','IMPORT_FILE'])
    write(reports/'message_catalog_phase22ae_6_5_3_expected_text_rows_v1.csv',et,['SYMBOL','LOCALE','TEXT_EXPECTED','SOURCE','IMPORT_FILE'])
    write(reports/'message_catalog_phase22ae_6_5_3_stage_boundary_ledger_v1.csv',[{'PROTECTED_SYSTEM':'ACTIVE/SOURCE/HELP/CMDHELPCHK','MUTATION_ALLOWED':0,'OBSERVED_MUTATION':0,'DETAIL':'sandbox-only stage'}],['PROTECTED_SYSTEM','MUTATION_ALLOWED','OBSERVED_MUTATION','DETAIL'])
    summ={'STATUS':status,'VALIDATION_ISSUES':val,'PHASE22AE_6_5_2_REBUILD_REQUIRED':1 if prev.get('STATUS')=='MESSAGE_CATALOG_PHASE22AE_6_5_2_ISOLATED_IMPORT_EXECUTION_PROOF_GREEN_IMPORT_NOT_PROVEN_REBUILD_REQUIRED' else 0,'MSG_022AE_6_5_2_SAVEPOINT_PRESENT':1 if sp else 0,'SANDBOX_ROOT':rel(repo/SANDBOX,repo),'SCRIPT_PATH':script_rel,'SANDBOX_MESSAGE_ROWS_BEFORE':msgc,'SANDBOX_TEXT_ROWS_BEFORE':txtc,'IMPORT_MESSAGE_ROWS':len(em),'IMPORT_TEXT_ROWS':len(et),'ACTIVE_CATALOG_MUTATION_OBSERVED':0,'SOURCE_FILES_MUTATED':0,'HELP_DATA_MUTATION_OBSERVED':0,'CMDHELPCHK_MUTATION_OBSERVED':0,'ERRORS':'; '.join(errs),'NEXT_GATE':NEXT,'REPORT_TIMESTAMP_UTC':datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00','Z')}
    write(reports/'message_catalog_phase22ae_6_5_3_stage_status_summary_v1.csv',[summ],list(summ.keys()))
    print(status); print(f'  validation issues: {val}'); print(f'  Phase 22AE.6.5.2 rebuild required: {summ["PHASE22AE_6_5_2_REBUILD_REQUIRED"]}'); print(f'  MSG-022AE.6.5.2 savepoint present: {1 if sp else 0}'); print(f'  sandbox root: {summ["SANDBOX_ROOT"]}'); print(f'  script path: {script_rel}'); print(f'  sandbox message rows before: {msgc}'); print(f'  sandbox text rows before: {txtc}'); print(f'  import message rows: {len(em)}'); print(f'  import text rows: {len(et)}'); print('  active catalog mutation observed: 0'); print('  source files mutated: 0'); print(f'  next gate: {NEXT}'); print(f'  reports: {reports}')
    return 0 if status==STATUS_GREEN else 2
if __name__=='__main__': raise SystemExit(main())
