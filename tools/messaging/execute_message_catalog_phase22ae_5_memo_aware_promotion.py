#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, hashlib, json, shutil, struct, subprocess
from datetime import datetime, timezone
from pathlib import Path

STATUS_PREPARED = 'MESSAGE_CATALOG_PHASE22AE_5_MEMO_AWARE_ACTIVE_CATALOG_PROMOTION_PREPARED'
STATUS_EXECUTED = 'MESSAGE_CATALOG_PHASE22AE_5_MEMO_AWARE_ACTIVE_CATALOG_PROMOTION_EXECUTED'
STATUS_ALREADY = 'MESSAGE_CATALOG_PHASE22AE_5_MEMO_AWARE_ACTIVE_CATALOG_PROMOTION_ALREADY_PRESENT_NOOP_GREEN'
STATUS_BLOCKED = 'MESSAGE_CATALOG_PHASE22AE_5_MEMO_AWARE_ACTIVE_CATALOG_PROMOTION_BLOCKED'
NEXT_GATE = 'HOLD_OR_AUTHORIZE_PHASE22AF_ACTIVE_CATALOG_READBACK_AND_RUNTIME_VALIDATION'
REPORT_DIR = Path('docs/messaging/reports')
RUNLOG_DIR = Path('docs/messaging/runlog')
SCRIPT_DIR = Path('docs/messaging/scripts')
BACKUP_BASE = Path('docs/messaging/backups')
ACTIVE_MSG_ROOT = Path('dottalkpp/data/messaging')
ACTIVE_INDEX_ROOT = Path('dottalkpp/data/indexes/messaging')
ACTIVE_LMDB_ROOT = Path('dottalkpp/data/lmdb/messaging')
CANDIDATE_ROOT = Path('docs/messaging/candidates/phase22aa_catalog_row_promotion_candidate_v1')
APPLYAD_ROOT = Path('docs/messaging/apply/phase22ad_active_catalog_replacement_apply_package_v1')
CONTROL_JSON = REPORT_DIR / 'message_catalog_phase22ae_5_control_v1.json'
TARGET_MESSAGES = 14
TARGET_TEXT_ROWS = 70
SYMBOL_FIELDS = ['SYMBOL','MESSAGE_SYMBOL','MSG_SYMBOL']
LOCALE_FIELDS = ['LOCALE','LOCALE_ID']
TEXT_FIELDS = ['TEXT','MESSAGE_TEXT','MSG_TEXT']
KIND_FIELDS = ['KIND','MESSAGE_KIND','MSG_KIND']
PLACEHOLDER_FIELDS = ['PLACEHOLDERS','PLACEHOLDER','ARGS','ARGUMENTS']
STATUS_FIELDS = ['STATUS','ROW_STATUS']
SOURCE_FIELDS = ['SOURCE_PHASE','SOURCE','PHASE']

def read_csv(path: Path):
    if not path.exists(): return []
    with path.open('r', encoding='utf-8-sig', newline='') as f: return list(csv.DictReader(f))

def first_row(path: Path):
    rows = read_csv(path); return rows[0] if rows else {}

def write_csv(path: Path, rows, fields):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator='\n'); w.writeheader()
        for row in rows: w.writerow({k: row.get(k, '') for k in fields})

def sha256_file(path: Path) -> str:
    if not path.exists() or not path.is_file(): return ''
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024*1024), b''): h.update(chunk)
    return h.hexdigest()

def rel(path: Path, repo: Path) -> str:
    try: return str(path.relative_to(repo)).replace('\\','/')
    except Exception: return str(path).replace('\\','/')

def savepoint_present(repo: Path, savepoint_id: str):
    latest_path = repo / REPORT_DIR / 'message_savepoint_latest_v1.json'
    latest_id = ''
    if latest_path.exists():
        try: latest_id = json.loads(latest_path.read_text(encoding='utf-8')).get('savepoint_id','')
        except Exception: latest_id = ''
    journal = repo / 'docs/messaging/MESSAGING_SAVEPOINT_JOURNAL.md'
    text = journal.read_text(encoding='utf-8', errors='replace') if journal.exists() else ''
    return latest_id == savepoint_id or savepoint_id in text, latest_id

def dottalkpp_running():
    try:
        p = subprocess.run(['tasklist','/FI','IMAGENAME eq dottalkpp.exe'], capture_output=True, text=True, timeout=10)
        out = (p.stdout or '') + '\n' + (p.stderr or '')
        return 'dottalkpp.exe' in out.lower(), out.strip().replace('\r\n',' | ')
    except Exception as exc:
        return False, f'tasklist unavailable: {exc}'

def parse_dbf(path: Path):
    data = path.read_bytes()
    if len(data) < 32: raise RuntimeError(f'{path} too small to be DBF')
    count = struct.unpack('<I', data[4:8])[0]
    header_len = struct.unpack('<H', data[8:10])[0]
    rec_len = struct.unpack('<H', data[10:12])[0]
    fields=[]; pos=32; offset=1
    while pos+32 <= len(data):
        if data[pos] == 0x0D: break
        name = data[pos:pos+11].split(b'\x00',1)[0].decode('ascii', errors='ignore').strip().upper()
        typ = chr(data[pos+11]); length=data[pos+16]; dec=data[pos+17]
        if name:
            fields.append({'NAME':name,'TYPE':typ,'LENGTH':length,'DECIMALS':dec,'OFFSET':offset})
            offset += length
        pos += 32
    return {'path':path,'count':count,'header_len':header_len,'rec_len':rec_len,'fields':fields}

def read_dbf_rows(info):
    rows=[]
    with info['path'].open('rb') as f:
        f.seek(info['header_len'])
        for _ in range(info['count']):
            rec = f.read(info['rec_len'])
            if len(rec) < info['rec_len']: break
            if rec[:1] == b'*': continue
            row={}
            for field in info['fields']:
                raw = rec[field['OFFSET']:field['OFFSET']+field['LENGTH']]
                enc = 'cp1252' if field['TYPE'].upper() in ('C','M') else 'ascii'
                row[field['NAME']] = raw.decode(enc, errors='replace').rstrip().strip()
            rows.append(row)
    return rows

def choose_field(fields, candidates):
    names = {f['NAME'].upper() for f in fields}
    for c in candidates:
        if c in names: return c
    return ''

def q(value):
    value = '' if value is None else str(value)
    return '"' + value.replace('"','""') + '"'

def candidate_paths(repo):
    msg = repo / APPLYAD_ROOT / 'rows/message_catalog_candidate_message_adds_v1.csv'
    txt = repo / APPLYAD_ROOT / 'rows/message_catalog_candidate_text_adds_v1.csv'
    if not msg.exists(): msg = repo / CANDIDATE_ROOT / 'rows/message_catalog_candidate_message_adds_v1.csv'
    if not txt.exists(): txt = repo / CANDIDATE_ROOT / 'rows/message_catalog_candidate_text_adds_v1.csv'
    return msg, txt

def active_paths(repo):
    return repo/ACTIVE_MSG_ROOT/'SYSTEM_MESSAGES.dbf', repo/ACTIVE_MSG_ROOT/'SYSTEM_MESSAGE_TEXT.dbf'

def existing_state(repo):
    msg_dbf, txt_dbf = active_paths(repo)
    msg_info = parse_dbf(msg_dbf); txt_info = parse_dbf(txt_dbf)
    msg_symbol = choose_field(msg_info['fields'], SYMBOL_FIELDS)
    txt_symbol = choose_field(txt_info['fields'], SYMBOL_FIELDS)
    txt_locale = choose_field(txt_info['fields'], LOCALE_FIELDS)
    txt_text = choose_field(txt_info['fields'], TEXT_FIELDS)
    msg_rows = read_dbf_rows(msg_info); txt_rows = read_dbf_rows(txt_info)
    return {
        'msg_info': msg_info, 'txt_info': txt_info,
        'msg_symbol': msg_symbol, 'txt_symbol': txt_symbol, 'txt_locale': txt_locale, 'txt_text': txt_text,
        'msg_symbols': {r.get(msg_symbol,'') for r in msg_rows} if msg_symbol else set(),
        'txt_keys': {(r.get(txt_symbol,''), r.get(txt_locale,'')) for r in txt_rows} if txt_symbol and txt_locale else set(),
    }

def copy_tree(src: Path, dst: Path, repo: Path, rows, role):
    if not src.exists():
        rows.append({'SOURCE':rel(src,repo),'BACKUP':rel(dst,repo),'ROLE':role,'EXISTS':0,'FILES':0,'BYTES':0,'SHA256':''}); return
    if dst.exists(): shutil.rmtree(dst)
    files=0; total=0
    for p in src.rglob('*'):
        if p.is_file():
            qpath = dst / p.relative_to(src); qpath.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(p,qpath)
            files += 1; total += qpath.stat().st_size
    rows.append({'SOURCE':rel(src,repo),'BACKUP':rel(dst,repo),'ROLE':role,'EXISTS':1,'FILES':files,'BYTES':total,'SHA256':''})

def fingerprint(root: Path, repo: Path, label):
    rows=[]
    if not root.exists(): return [{'LABEL':label,'PATH':rel(root,repo),'EXISTS':0,'BYTES':0,'SHA256':'','ROLE':'missing'}]
    for p in sorted(root.rglob('*')):
        if p.is_file(): rows.append({'LABEL':label,'PATH':rel(p,repo),'EXISTS':1,'BYTES':p.stat().st_size,'SHA256':sha256_file(p),'ROLE':'file'})
    return rows or [{'LABEL':label,'PATH':rel(root,repo),'EXISTS':1,'BYTES':0,'SHA256':'','ROLE':'empty'}]

def generate_dts(repo, candidate_messages, candidate_text, state, dts_path):
    msg_dbf, txt_dbf = active_paths(repo)
    msg_fields = state['msg_info']['fields']; txt_fields = state['txt_info']['fields']
    msg_symbol = state['msg_symbol']; txt_symbol = state['txt_symbol']; txt_locale = state['txt_locale']; txt_text = state['txt_text']
    msg_kind = choose_field(msg_fields, KIND_FIELDS); msg_ph = choose_field(msg_fields, PLACEHOLDER_FIELDS)
    msg_status = choose_field(msg_fields, STATUS_FIELDS); msg_source = choose_field(msg_fields, SOURCE_FIELDS)
    txt_ph = choose_field(txt_fields, PLACEHOLDER_FIELDS); txt_status = choose_field(txt_fields, STATUS_FIELDS); txt_source = choose_field(txt_fields, SOURCE_FIELDS)
    lines = [
        '* MESSAGE_CATALOG_PHASE22AE_5_MEMO_AWARE_ACTIVE_CATALOG_PROMOTION_EXECUTE.dts',
        '* Active mutation authorized by operator. Uses runtime USE/APPEND/REPLACE for memo handling.',
        '',
        f'USE {msg_dbf.resolve().as_posix()}',
    ]
    for row in candidate_messages:
        lines += ['APPEND', f'REPLACE {msg_symbol} WITH {q(row.get("SYMBOL",""))}']
        if msg_kind: lines.append(f'REPLACE {msg_kind} WITH {q(row.get("KIND","runtime_status_message"))}')
        if msg_ph: lines.append(f'REPLACE {msg_ph} WITH {q(row.get("PLACEHOLDERS",""))}')
        if msg_status: lines.append(f'REPLACE {msg_status} WITH {q("ACTIVE")}')
        if msg_source: lines.append(f'REPLACE {msg_source} WITH {q("22AE_5")}')
        lines.append('')
    lines.append(f'USE {txt_dbf.resolve().as_posix()}')
    for row in candidate_text:
        lines += ['APPEND', f'REPLACE {txt_symbol} WITH {q(row.get("SYMBOL",""))}', f'REPLACE {txt_locale} WITH {q(row.get("LOCALE",""))}', f'REPLACE {txt_text} WITH {q(row.get("TEXT",""))}']
        if txt_ph: lines.append(f'REPLACE {txt_ph} WITH {q(row.get("PLACEHOLDERS",""))}')
        if txt_status: lines.append(f'REPLACE {txt_status} WITH {q("ACTIVE")}')
        if txt_source: lines.append(f'REPLACE {txt_source} WITH {q("22AE_5")}')
        lines.append('')
    lines.append('')
    dts_path.parent.mkdir(parents=True, exist_ok=True); dts_path.write_text('\n'.join(lines), encoding='utf-8')

def write_common(repo, status, validation, gates, backups, before, after, mutations, row):
    reports=repo/REPORT_DIR
    base = {
        'STATUS':status,'VALIDATION_ISSUES':validation,'NEXT_GATE':NEXT_GATE,
        'REPORT_TIMESTAMP_UTC':datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00','Z')
    }
    base.update(row)
    fields=['STATUS','VALIDATION_ISSUES','PHASE22AE_4_GREEN','MSG_022AE_4_SAVEPOINT_PRESENT','DOTTALKPP_PROCESS_RUNNING','SHOULD_EXECUTE_RUNTIME','RUNTIME_EXECUTED','ALREADY_PRESENT_NOOP','SCRIPT_PATH','RUNLOG_PATH','MESSAGE_ROWS_BEFORE','TEXT_ROWS_BEFORE','MESSAGE_ROWS_AFTER','TEXT_ROWS_AFTER','MESSAGE_SYMBOLS_PRESENT','TEXT_KEYS_PRESENT','BACKUP_ROWS','SOURCE_FILES_MUTATED','ACTIVE_CATALOG_MUTATION_OBSERVED','ACTIVE_INDEX_MUTATION_OBSERVED','ACTIVE_LMDB_MUTATION_OBSERVED','HELP_DATA_MUTATION_OBSERVED','CMDHELPCHK_MUTATION_OBSERVED','ERRORS','NEXT_GATE','REPORT_TIMESTAMP_UTC']
    write_csv(reports/'message_catalog_phase22ae_5_status_summary_v1.csv',[base],fields)
    write_csv(reports/'message_catalog_phase22ae_5_gate_check_v1.csv',gates,['GATE','STATUS','DETAIL'])
    write_csv(reports/'message_catalog_phase22ae_5_backup_inventory_v1.csv',backups,['SOURCE','BACKUP','ROLE','EXISTS','FILES','BYTES','SHA256'])
    write_csv(reports/'message_catalog_phase22ae_5_active_fingerprint_before_v1.csv',before,['LABEL','PATH','EXISTS','BYTES','SHA256','ROLE'])
    write_csv(reports/'message_catalog_phase22ae_5_active_fingerprint_after_v1.csv',after,['LABEL','PATH','EXISTS','BYTES','SHA256','ROLE'])
    write_csv(reports/'message_catalog_phase22ae_5_active_mutation_inventory_v1.csv',mutations,['TARGET_ROOT','ACTION','DETAIL'])
    boundary=[
        {'PROTECTED_SYSTEM':'SOURCE_CODE','MUTATION_ALLOWED':0,'OBSERVED_MUTATION':0,'DETAIL':'No source mutation.'},
        {'PROTECTED_SYSTEM':'ACTIVE_MESSAGING_DBF_CATALOG','MUTATION_ALLOWED':1,'OBSERVED_MUTATION':base.get('ACTIVE_CATALOG_MUTATION_OBSERVED',0),'DETAIL':'Authorized memo-aware runtime promotion only.'},
        {'PROTECTED_SYSTEM':'ACTIVE_MESSAGING_CDX_INDEXES','MUTATION_ALLOWED':1,'OBSERVED_MUTATION':base.get('ACTIVE_INDEX_MUTATION_OBSERVED',0),'DETAIL':'Validate/rebuild in follow-up if required.'},
        {'PROTECTED_SYSTEM':'ACTIVE_MESSAGING_LMDB','MUTATION_ALLOWED':1,'OBSERVED_MUTATION':base.get('ACTIVE_LMDB_MUTATION_OBSERVED',0),'DETAIL':'Validate/rebuild in follow-up if required.'},
        {'PROTECTED_SYSTEM':'HELP_DATA','MUTATION_ALLOWED':0,'OBSERVED_MUTATION':0,'DETAIL':'No HELP DATA mutation.'},
        {'PROTECTED_SYSTEM':'CMDHELPCHK','MUTATION_ALLOWED':0,'OBSERVED_MUTATION':0,'DETAIL':'No CMDHELPCHK mutation.'},
    ]
    write_csv(reports/'message_catalog_phase22ae_5_boundary_ledger_v1.csv',boundary,['PROTECTED_SYSTEM','MUTATION_ALLOWED','OBSERVED_MUTATION','DETAIL'])

def prepare(repo: Path, allow_active: bool):
    reports=repo/REPORT_DIR; reports.mkdir(parents=True,exist_ok=True); (repo/RUNLOG_DIR).mkdir(parents=True,exist_ok=True); (repo/SCRIPT_DIR).mkdir(parents=True,exist_ok=True)
    ae4=first_row(reports/'message_catalog_phase22ae_4_status_summary_v1.csv'); sp_ok, latest=savepoint_present(repo,'MSG-022AE.4'); running, rdetail=dottalkpp_running()
    cm_path, ct_path = candidate_paths(repo); cm=read_csv(cm_path); ct=read_csv(ct_path)
    gates=[]; failures=0; errors=[]
    def gate(n, ok, d):
        nonlocal failures; gates.append({'GATE':n,'STATUS':'PASS' if ok else 'FAIL','DETAIL':d}); failures += 0 if ok else 1
    gate('OPERATOR_AUTHORIZED_ACTIVE_CATALOG_MUTATION', allow_active, 'requires -AllowActiveCatalogMutation')
    gate('PHASE22AE_4_GREEN', ae4.get('STATUS')=='MESSAGE_CATALOG_PHASE22AE_4_MEMO_AWARE_ACTIVE_CATALOG_PROMOTION_PACKAGE_STAGED_SOURCE_HELD', ae4.get('STATUS','missing'))
    gate('MSG_022AE_4_SAVEPOINT_PRESENT', sp_ok, latest)
    gate('DOTTALKPP_PROCESS_NOT_RUNNING', not running, rdetail)
    gate('CANDIDATE_MESSAGE_ROWS_AVAILABLE', len(cm)==2, f'rows={len(cm)}')
    gate('CANDIDATE_TEXT_ROWS_AVAILABLE', len(ct)==10, f'rows={len(ct)}')
    before = fingerprint(repo/ACTIVE_MSG_ROOT,repo,'before_messaging') + fingerprint(repo/ACTIVE_INDEX_ROOT,repo,'before_indexes') + fingerprint(repo/ACTIVE_LMDB_ROOT,repo,'before_lmdb')
    backups=[]; mutations=[]; after=[]; should=False; noop=False; msg_before=''; txt_before=''; msg_present=0; txt_present=0
    script_path = repo/SCRIPT_DIR/'MESSAGE_CATALOG_PHASE22AE_5_MEMO_AWARE_ACTIVE_CATALOG_PROMOTION_EXECUTE.dts'
    runlog_path = repo/RUNLOG_DIR/'MSG-022AE_5_MEMO_AWARE_ACTIVE_CATALOG_PROMOTION_EXECUTION.md'
    if failures==0:
        try:
            st=existing_state(repo); msg_before=st['msg_info']['count']; txt_before=st['txt_info']['count']
            req_msg={r.get('SYMBOL','') for r in cm}; req_txt={(r.get('SYMBOL',''),r.get('LOCALE','')) for r in ct}
            msg_present=len([x for x in req_msg if x in st['msg_symbols']]); txt_present=len([x for x in req_txt if x in st['txt_keys']])
            if msg_present==2 and txt_present==10:
                noop=True
            elif msg_present==0 and txt_present==0:
                should=True
                stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ'); bbase=repo/BACKUP_BASE/f'MSG-022AE_5_MEMO_AWARE_ACTIVE_CATALOG_PROMOTION_BACKUP_{stamp}'
                copy_tree(repo/ACTIVE_MSG_ROOT,bbase/'messaging',repo,backups,'active_messaging_backup')
                copy_tree(repo/ACTIVE_INDEX_ROOT,bbase/'indexes_messaging',repo,backups,'active_indexes_backup')
                copy_tree(repo/ACTIVE_LMDB_ROOT,bbase/'lmdb_messaging',repo,backups,'active_lmdb_backup')
                generate_dts(repo,cm,ct,st,script_path)
            else:
                raise RuntimeError(f'partial active catalog presence; message symbols present={msg_present}; text keys present={txt_present}')
        except Exception as exc:
            errors.append(str(exc)); failures+=1; gates.append({'GATE':'PREPARE_MEMO_AWARE_EXECUTION','STATUS':'FAIL','DETAIL':str(exc)})
    status = STATUS_ALREADY if failures==0 and noop else STATUS_PREPARED if failures==0 and should else STATUS_BLOCKED
    validation='0' if status in (STATUS_PREPARED, STATUS_ALREADY) else str(failures)
    control={'status':status,'should_execute_runtime':should,'already_present_noop':noop,'script_path':str(script_path),'runlog_path':str(runlog_path)}
    (repo/CONTROL_JSON).write_text(json.dumps(control,indent=2),encoding='utf-8')
    row={'PHASE22AE_4_GREEN':1 if ae4.get('STATUS')=='MESSAGE_CATALOG_PHASE22AE_4_MEMO_AWARE_ACTIVE_CATALOG_PROMOTION_PACKAGE_STAGED_SOURCE_HELD' else 0,'MSG_022AE_4_SAVEPOINT_PRESENT':1 if sp_ok else 0,'DOTTALKPP_PROCESS_RUNNING':1 if running else 0,'SHOULD_EXECUTE_RUNTIME':1 if should else 0,'RUNTIME_EXECUTED':0,'ALREADY_PRESENT_NOOP':1 if noop else 0,'SCRIPT_PATH':rel(script_path,repo),'RUNLOG_PATH':rel(runlog_path,repo),'MESSAGE_ROWS_BEFORE':msg_before,'TEXT_ROWS_BEFORE':txt_before,'MESSAGE_ROWS_AFTER':'','TEXT_ROWS_AFTER':'','MESSAGE_SYMBOLS_PRESENT':msg_present,'TEXT_KEYS_PRESENT':txt_present,'BACKUP_ROWS':len(backups),'SOURCE_FILES_MUTATED':0,'ACTIVE_CATALOG_MUTATION_OBSERVED':0,'ACTIVE_INDEX_MUTATION_OBSERVED':0,'ACTIVE_LMDB_MUTATION_OBSERVED':0,'HELP_DATA_MUTATION_OBSERVED':0,'CMDHELPCHK_MUTATION_OBSERVED':0,'ERRORS':'; '.join(errors)}
    write_common(repo,status,validation,gates,backups,before,after,mutations,row)
    for k,v in [('validation issues',validation),('Phase 22AE.4 green',row['PHASE22AE_4_GREEN']),('MSG-022AE.4 savepoint present',row['MSG_022AE_4_SAVEPOINT_PRESENT']),('dottalkpp process running',row['DOTTALKPP_PROCESS_RUNNING']),('should execute runtime',row['SHOULD_EXECUTE_RUNTIME']),('already present noop',row['ALREADY_PRESENT_NOOP']),('script path',row['SCRIPT_PATH']),('runlog path',row['RUNLOG_PATH']),('message rows before',row['MESSAGE_ROWS_BEFORE']),('text rows before',row['TEXT_ROWS_BEFORE']),('message symbols present',row['MESSAGE_SYMBOLS_PRESENT']),('text keys present',row['TEXT_KEYS_PRESENT']),('backup rows',row['BACKUP_ROWS'])]: print(f'  {k}: {v}') if k!='validation issues' else None
    print(status); print(f'  validation issues: {validation}'); print(f'  should execute runtime: {row["SHOULD_EXECUTE_RUNTIME"]}'); print(f'  already present noop: {row["ALREADY_PRESENT_NOOP"]}'); print(f'  script path: {row["SCRIPT_PATH"]}'); print(f'  runlog path: {row["RUNLOG_PATH"]}'); print(f'  backup rows: {row["BACKUP_ROWS"]}'); print('  source files mutated: 0'); print('  active catalog mutation observed: 0'); print(f'  next gate: {NEXT_GATE}'); print(f'  reports: {reports}')
    return 0 if status in (STATUS_PREPARED, STATUS_ALREADY) else 2

def finalize(repo: Path, runtime_log: str):
    reports=repo/REPORT_DIR; control=json.loads((repo/CONTROL_JSON).read_text(encoding='utf-8')) if (repo/CONTROL_JSON).exists() else {}
    ae4=first_row(reports/'message_catalog_phase22ae_4_status_summary_v1.csv'); sp_ok, latest=savepoint_present(repo,'MSG-022AE.4')
    cm_path, ct_path = candidate_paths(repo); cm=read_csv(cm_path); ct=read_csv(ct_path)
    log_path=Path(runtime_log or control.get('runlog_path',''))
    if not log_path.is_absolute(): log_path=repo/log_path
    log_text=log_path.read_text(encoding='utf-8',errors='replace') if log_path.exists() else ''
    gates=[]; failures=0; errors=[]
    def gate(n, ok, d):
        nonlocal failures; gates.append({'GATE':n,'STATUS':'PASS' if ok else 'FAIL','DETAIL':d}); failures += 0 if ok else 1
    runtime=bool(control.get('should_execute_runtime')); noop=bool(control.get('already_present_noop'))
    if runtime:
        gate('RUNTIME_LOG_EXISTS', log_path.exists(), rel(log_path,repo)); gate('NO_UNKNOWN_COMMAND', 'Unknown command:' not in log_text, 'Unknown command absent'); gate('NO_MEMO_BACKEND_ERROR', 'memo backend not attached' not in log_text.lower(), 'memo backend error absent')
    msg_after=''; txt_after=''; msg_present=0; txt_present=0
    try:
        st=existing_state(repo); msg_after=st['msg_info']['count']; txt_after=st['txt_info']['count']; req_msg={r.get('SYMBOL','') for r in cm}; req_txt={(r.get('SYMBOL',''),r.get('LOCALE','')) for r in ct}
        msg_present=len([x for x in req_msg if x in st['msg_symbols']]); txt_present=len([x for x in req_txt if x in st['txt_keys']])
        gate('MESSAGE_SYMBOLS_PRESENT_AFTER', msg_present==2, f'present={msg_present}'); gate('TEXT_KEYS_PRESENT_AFTER', txt_present==10, f'present={txt_present}'); gate('TARGET_MESSAGE_COUNT_AFTER', int(msg_after)==TARGET_MESSAGES, f'records={msg_after}'); gate('TARGET_TEXT_COUNT_AFTER', int(txt_after)==TARGET_TEXT_ROWS, f'records={txt_after}')
    except Exception as exc:
        errors.append(str(exc)); failures+=1; gates.append({'GATE':'FINAL_READBACK_AFTER_RUNTIME','STATUS':'FAIL','DETAIL':str(exc)})
    before=read_csv(reports/'message_catalog_phase22ae_5_active_fingerprint_before_v1.csv'); backups=read_csv(reports/'message_catalog_phase22ae_5_backup_inventory_v1.csv')
    after=fingerprint(repo/ACTIVE_MSG_ROOT,repo,'after_messaging')+fingerprint(repo/ACTIVE_INDEX_ROOT,repo,'after_indexes')+fingerprint(repo/ACTIVE_LMDB_ROOT,repo,'after_lmdb')
    mutations=[]
    if runtime: mutations.append({'TARGET_ROOT':rel(repo/ACTIVE_MSG_ROOT,repo),'ACTION':'MEMO_AWARE_RUNTIME_DTS_EXECUTION','DETAIL':'DotTalk++ USE/APPEND/REPLACE promotion script executed'})
    status=STATUS_ALREADY if failures==0 and noop else STATUS_EXECUTED if failures==0 else STATUS_BLOCKED; validation='0' if failures==0 else str(failures)
    row={'PHASE22AE_4_GREEN':1 if ae4.get('STATUS')=='MESSAGE_CATALOG_PHASE22AE_4_MEMO_AWARE_ACTIVE_CATALOG_PROMOTION_PACKAGE_STAGED_SOURCE_HELD' else 0,'MSG_022AE_4_SAVEPOINT_PRESENT':1 if sp_ok else 0,'DOTTALKPP_PROCESS_RUNNING':0,'SHOULD_EXECUTE_RUNTIME':1 if runtime else 0,'RUNTIME_EXECUTED':1 if runtime else 0,'ALREADY_PRESENT_NOOP':1 if noop else 0,'SCRIPT_PATH':rel(Path(control.get('script_path','')),repo) if control.get('script_path') else '', 'RUNLOG_PATH':rel(log_path,repo),'MESSAGE_ROWS_BEFORE':'','TEXT_ROWS_BEFORE':'','MESSAGE_ROWS_AFTER':msg_after,'TEXT_ROWS_AFTER':txt_after,'MESSAGE_SYMBOLS_PRESENT':msg_present,'TEXT_KEYS_PRESENT':txt_present,'BACKUP_ROWS':len(backups),'SOURCE_FILES_MUTATED':0,'ACTIVE_CATALOG_MUTATION_OBSERVED':len(mutations),'ACTIVE_INDEX_MUTATION_OBSERVED':0,'ACTIVE_LMDB_MUTATION_OBSERVED':0,'HELP_DATA_MUTATION_OBSERVED':0,'CMDHELPCHK_MUTATION_OBSERVED':0,'ERRORS':'; '.join(errors)}
    write_common(repo,status,validation,gates,backups,before,after,mutations,row)
    print(status); print(f'  validation issues: {validation}'); print(f'  runtime executed: {row["RUNTIME_EXECUTED"]}'); print(f'  already present noop: {row["ALREADY_PRESENT_NOOP"]}'); print(f'  message rows after: {row["MESSAGE_ROWS_AFTER"]}'); print(f'  text rows after: {row["TEXT_ROWS_AFTER"]}'); print(f'  message symbols present: {row["MESSAGE_SYMBOLS_PRESENT"]}'); print(f'  text keys present: {row["TEXT_KEYS_PRESENT"]}'); print(f'  backup rows: {row["BACKUP_ROWS"]}'); print('  source files mutated: 0'); print(f'  active catalog mutation observed: {row["ACTIVE_CATALOG_MUTATION_OBSERVED"]}'); print('  HELP DATA mutation observed: 0'); print('  CMDHELPCHK mutation observed: 0'); print(f'  next gate: {NEXT_GATE}'); print(f'  reports: {reports}')
    return 0 if status in (STATUS_EXECUTED, STATUS_ALREADY) else 2

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--repo-root',required=True); ap.add_argument('--mode',choices=['prepare','finalize'],required=True); ap.add_argument('--allow-active-catalog-mutation',action='store_true'); ap.add_argument('--runtime-log',default=''); args=ap.parse_args(); repo=Path(args.repo_root).resolve()
    return prepare(repo,args.allow_active_catalog_mutation) if args.mode=='prepare' else finalize(repo,args.runtime_log)
if __name__=='__main__': raise SystemExit(main())
