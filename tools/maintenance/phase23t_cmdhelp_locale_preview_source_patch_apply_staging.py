#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, json, hashlib
from pathlib import Path
from datetime import datetime, timezone

PHASE="PHASE23T"
NAME="PHASE23T-CMDHELP-LOCALE-PREVIEW-SOURCE-PATCH-APPLY-STAGING"
STATUS_GREEN="PHASE23T_CMDHELP_LOCALE_PREVIEW_SOURCE_PATCH_APPLY_STAGING_GREEN_APPLY_SCRIPT_READY"
VERSION="v1.1-explicit-source-target-override"
STATUS_REVIEW="PHASE23T_CMDHELP_LOCALE_PREVIEW_SOURCE_PATCH_APPLY_STAGING_REVIEW_REQUIRED"
NEXT_GATE="HOLD_OR_RUN_PHASE23T_APPLY_SCRIPT_THEN_REVIEW_SOURCE_CONTRACT_PATCH"
TABLES=["HELP_TOPIC_LOCALE","HELP_SECTION_LOCALE","HELP_LINE_LOCALE","HELP_ARTIFACT_LOCALE"]
SOURCE_EXTS={".cpp",".cxx",".cc",".c",".hpp",".hh",".h"}
SKIP_DIRS={".git","build","out",".vs",".vscode","node_modules","__pycache__","candidate","candidates","published","rollback","backup","backups"}


def utc_now(): return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
def read_text(p:Path,limit:int=800000):
    try: return p.read_bytes()[:limit].decode('utf-8',errors='ignore')
    except Exception: return ''
def sha256_path(path:Path)->str:
    h=hashlib.sha256()
    if path.is_dir():
        for p in sorted(x for x in path.rglob('*') if x.is_file()):
            h.update(str(p.relative_to(path)).replace('\\','/').encode()); h.update(b'\0'); h.update(p.read_bytes()); h.update(b'\0')
    else:
        h.update(path.read_bytes())
    return h.hexdigest()
def write_csv(path:Path, rows:list[dict]):
    path.parent.mkdir(parents=True,exist_ok=True)
    fields=[]
    for r in rows:
        for k in r:
            if k not in fields: fields.append(k)
    with path.open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(rows)
def find_phase_green(repo:Path, phase_name:str, status_prefix:str):
    base=repo/'docs'/'locale'/'candidates'/phase_name
    if not base.exists(): return 0,None
    hits=[]
    for sub in ['manifests','reports']:
        d=base/sub
        if d.exists(): hits += list(d.glob('*.json')) + list(d.glob('*.md'))
    for p in hits:
        if status_prefix in read_text(p): return 1,p
    return 0,(hits[0] if hits else None)
def active_counts(repo:Path):
    roots=[repo/'dottalkpp'/'data'/'HELP',repo/'dottalkpp'/'data'/'INDEXES'/'HELP',repo/'dottalkpp'/'data'/'LMDB'/'HELP']
    lower=[repo/'dottalkpp'/'data'/'help',repo/'dottalkpp'/'data'/'indexes'/'help',repo/'dottalkpp'/'data'/'lmdb'/'help']
    roots=[lower[i] if (not roots[i].exists() and lower[i].exists()) else roots[i] for i in range(3)]
    dbf=sum(1 for t in TABLES if (roots[0]/f'{t}.dbf').exists())
    cdx=sum(1 for t in TABLES if (roots[1]/f'{t}.cdx').exists())
    lmdb=sum(1 for t in TABLES if (roots[2]/f'{t}.cdx.d').exists())
    return {'active_roots': ','.join(str(r.relative_to(repo)) for r in roots), 'active_dbf_exists':f'{dbf}/4','active_cdx_exists':f'{cdx}/4','active_lmdb_exists':f'{lmdb}/4','active_all_exists':int(dbf==4 and cdx==4 and lmdb==4)}
def load_phase23s_inventory(repo:Path):
    inv=repo/'docs'/'locale'/'candidates'/'PHASE23S-CMDHELP-LOCALE-PREVIEW-SOURCE-PATCH-STAGING'/'reports'/'phase23s_source_patch_target_inventory.csv'
    rows=[]
    if inv.exists():
        with inv.open(newline='',encoding='utf-8') as f:
            rows=list(csv.DictReader(f))
    return rows,inv
def scan_fallback(repo:Path,limit:int=120):
    rows=[]; seen=set()
    for base in [repo/'src', repo/'include', repo/'dottalkpp']:
        if not base.exists(): continue
        for p in base.rglob('*'):
            if len(rows)>=limit: break
            if not p.is_file() or p.suffix.lower() not in SOURCE_EXTS: continue
            rel=p.relative_to(repo)
            if any(part in SKIP_DIRS for part in rel.parts): continue
            txt=read_text(p,300000); up=txt.upper(); low=str(rel).lower()
            if 'CMDHELP' in up or 'cmdhelp' in low:
                rows.append({'source_path':str(rel),'name_hit':int('cmdhelp' in low),'content_hit':1,'usage_contract_hit':int('@DOTTALK.USAGE' in up),'cmdhelp_contract_hit':int('CMDHELP' in up),'size_bytes':p.stat().st_size,'sha256':sha256_path(p)[:16],'recommended_role':'PRIMARY_CMDHELP_COMMAND_SURFACE_CANDIDATE' if 'cmdhelp' in low else 'SECONDARY_REVIEW_CANDIDATE'})
        if len(rows)>=limit: break
    return rows
def select_targets(repo:Path, rows:list[dict]):
    existing=[]
    for r in rows:
        rel=r.get('source_path','')
        p=repo/rel
        if p.exists() and p.is_file():
            rr=dict(r); rr['exists']='1'; rr['source_path']=rel; existing.append(rr)
    primary=[r for r in existing if r.get('recommended_role')=='PRIMARY_CMDHELP_COMMAND_SURFACE_CANDIDATE']
    if not primary:
        primary=[r for r in existing if 'cmdhelp' in Path(r.get('source_path','')).name.lower()]
    cpp_primary=[r for r in primary if Path(r.get('source_path','')).suffix.lower() in {'.cpp','.cxx','.cc','.c'}]
    if len(cpp_primary)==1: return cpp_primary, existing
    if len(primary)==1: return primary, existing
    return primary, existing

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--repo-root',default='.'); ap.add_argument('--source-target', default='', help='Explicit source target such as src\\cli\\cmdhelp.cpp')
    args=ap.parse_args(); repo=Path(args.repo_root).resolve()
    cand=repo/'docs'/'locale'/'candidates'/NAME
    reports=cand/'reports'; manifests=cand/'manifests'; runtime=cand/'runtime'; patches=cand/'patches'
    for d in [reports,manifests,runtime,patches]: d.mkdir(parents=True,exist_ok=True)
    phase23s_green,_=find_phase_green(repo,'PHASE23S-CMDHELP-LOCALE-PREVIEW-SOURCE-PATCH-STAGING','PHASE23S_CMDHELP_LOCALE_PREVIEW_SOURCE_PATCH_STAGING_GREEN_SOURCE_HELD')
    phase23r_green,_=find_phase_green(repo,'PHASE23R-CMDHELP-LOCALE-PREVIEW-IMPLEMENTATION-PLAN','PHASE23R_CMDHELP_LOCALE_PREVIEW_IMPLEMENTATION_PLAN_GREEN_REPORT_ONLY')
    phase23q_green,_=find_phase_green(repo,'PHASE23Q-CMDHELP-LOCALE-INTEGRATION-PLAN','PHASE23Q_CMDHELP_LOCALE_INTEGRATION_PLAN_GREEN_REPORT_ONLY')
    phase23o_green,_=find_phase_green(repo,'PHASE23O-ACTIVE-HELP-LOCALE-READBACK-PROOF','PHASE23O_ACTIVE_HELP_LOCALE_READBACK_PROOF_GREEN')
    counts=active_counts(repo)
    rows,inv_path=load_phase23s_inventory(repo)
    if not rows: rows=scan_fallback(repo)
    selected, existing=select_targets(repo,rows)
    source_target_override=(args.source_target or '').strip().strip('\"').strip("'")
    override_used=0
    override_valid=0
    override_reason=''
    if source_target_override:
        override_used=1
        norm_override=source_target_override.replace('\\','/')
        target_file=repo / norm_override
        if not target_file.exists() or not target_file.is_file():
            selected=[]; override_reason='override_target_missing'
        elif target_file.suffix.lower() not in SOURCE_EXTS:
            selected=[]; override_reason='override_target_not_source_file'
        else:
            txt=read_text(target_file,300000)
            if 'CMDHELP' not in txt.upper():
                selected=[]; override_reason='override_target_missing_cmdhelp_anchor'
            else:
                rel=target_file.relative_to(repo).as_posix()
                selected=[{'source_path':rel,'recommended_role':'EXPLICIT_SOURCE_TARGET_OVERRIDE','name_hit':int('cmdhelp' in target_file.name.lower()),'content_hit':1,'usage_contract_hit':int('@DOTTALK.USAGE' in txt.upper()),'cmdhelp_contract_hit':1,'size_bytes':target_file.stat().st_size,'sha256':sha256_path(target_file)[:16],'exists':'1'}]
                override_valid=1; override_reason='override_target_valid'
                if not any((repo/(r.get('source_path','').replace('\\','/'))).resolve()==target_file.resolve() for r in existing if r.get('source_path')):
                    existing.append(dict(selected[0]))
    target_unique=int(len(selected)==1)
    target_path=selected[0]['source_path'] if target_unique else ''
    inventory_rows=[]
    for r in existing:
        rr=dict(r); rr['selected_for_apply']=int(target_unique and r.get('source_path','').replace('\\','/')==target_path.replace('\\','/')); rr['source_target_override_used']=override_used; rr['source_target_override_valid']=override_valid; rr['source_target_override_reason']=override_reason; inventory_rows.append(rr)
    write_csv(reports/'phase23t_source_target_selection.csv',inventory_rows)
    apply_py=repo/'tools'/'maintenance'/'phase23t_apply_cmdhelp_locale_preview_source_contract.py'
    review_py=repo/'tools'/'maintenance'/'phase23t_review_cmdhelp_locale_preview_source_patch.py'
    apply_ps=runtime/'phase23t_apply_cmdhelp_locale_preview_source_contract.ps1'
    apply_ps.write_text("""param(\n  [string]$RepoRoot = '.',\n  [switch]$ConfirmPhase23T\n)\nif (-not $ConfirmPhase23T) {\n  Write-Error 'Refusing to apply PHASE23T source patch without -ConfirmPhase23T.'\n  exit 2\n}\n$py12 = Join-Path $RepoRoot 'build\\vcpkg_installed\\x64-windows\\tools\\python3\\python.exe'\nif (-not (Test-Path $py12)) { $py12 = 'python' }\n& $py12 (Join-Path $RepoRoot 'tools\\maintenance\\phase23t_apply_cmdhelp_locale_preview_source_contract.py') --repo-root $RepoRoot --confirm-phase23t\nexit $LASTEXITCODE\n""",encoding='utf-8')
    patch_contract=[
        {'item':'patch_kind','value':'source_contract_marker_only','note':'This phase anchors the source contract; runtime behavior remains unchanged.'},
        {'item':'command_surface','value':'CMDHELP <topic> PREVIEW LOCALE <locale>','note':'Planned explicit preview surface.'},
        {'item':'default_behavior','value':'CMDHELP <topic> unchanged','note':'Normal CMDHELP must remain unchanged.'},
        {'item':'fallback_policy','value':'DRAFT_PLACEHOLDER or NEEDS_REVIEW falls back to source/default','note':'No approved translations exposed by default.'},
        {'item':'usage_contract','value':'@dottalk.usage v1 must stay synchronized','note':'Future implementation patch must update usage docs.'},
    ]
    write_csv(reports/'phase23t_source_contract_patch_contract.csv',patch_contract)
    md=reports/'PHASE23T_CMDHELP_LOCALE_PREVIEW_SOURCE_PATCH_APPLY_STAGING.md'
    status=STATUS_GREEN if phase23s_green and phase23r_green and phase23q_green and phase23o_green and counts['active_all_exists'] and target_unique else STATUS_REVIEW
    md.write_text('\n'.join([
        '# PHASE23T CMDHELP Locale Preview Source Patch Apply Staging','',f'Status: `{status}`','',
        'PHASE23T prepares a guarded source apply script. The apply script writes only a source contract marker/comment unless a future phase implements runtime behavior.', '',
        '## Guardrails','',
        '- Refuse apply unless `-ConfirmPhase23T` is supplied.',
        '- Refuse apply unless a unique CMDHELP source target is identified.',
        '- Create a rollback backup before writing source.',
        '- Preserve default `CMDHELP <topic>` behavior.',
        '- Do not write HELP DBF/CDX/LMDB data.', '',
        '## Selection','',
        f'- Unique target: {target_unique}',
        f'- Source target override used: {override_used}',
        f'- Source target override valid: {override_valid}',
        f'- Source target override reason: {override_reason}',
        f'- Target path: `{target_path}`' if target_path else '- Target path: `(not selected)`', '',
        f'Apply script: `{apply_ps.relative_to(repo)}`','',f'Next gate: `{NEXT_GATE}`',''
    ]),encoding='utf-8')
    manifest={'phase':PHASE,'status':status,'created_at':utc_now(),'candidate_dir':str(cand.relative_to(repo)),'phase23s_green':phase23s_green,'phase23r_green':phase23r_green,'phase23q_green':phase23q_green,'phase23o_green':phase23o_green,'read_scope':'ACTIVE_HELP_LOCALE_ROOTS','active_roots':counts['active_roots'],'active_dbf_exists':counts['active_dbf_exists'],'active_cdx_exists':counts['active_cdx_exists'],'active_lmdb_exists':counts['active_lmdb_exists'],'source_inventory_rows':len(existing),'unique_source_target':target_unique,'source_target_override_used':override_used,'source_target_override_valid':override_valid,'source_target_override_reason':override_reason,'selected_source_target':target_path,'apply_script':str(apply_ps.relative_to(repo)),'source_files_written':0,'source_patch_applied_by_staging':0,'active_help_dbf_written':0,'active_help_cdx_written':0,'active_help_lmdb_written':0,'cmdhelp_behavior_changed':0,'cmdhelpchk_behavior_changed':0,'maint_behavior_changed':0,'bbox_behavior_changed':0,'runtime_execution_by_python':0,'next_gate':NEXT_GATE}
    mpath=manifests/'phase23t_cmdhelp_locale_preview_source_patch_apply_staging_manifest.json'; mpath.write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    print(status)
    print(f'version: {VERSION}')
    print(f'candidate_dir: {cand.relative_to(repo)}')
    print(f'phase23s_green: {phase23s_green}')
    print(f'phase23r_green: {phase23r_green}')
    print(f'phase23q_green: {phase23q_green}')
    print(f'phase23o_green: {phase23o_green}')
    print('read_scope: ACTIVE_HELP_LOCALE_ROOTS')
    print(f"active_roots: {counts['active_roots']}")
    print(f"active_dbf_exists: {counts['active_dbf_exists']}")
    print(f"active_cdx_exists: {counts['active_cdx_exists']}")
    print(f"active_lmdb_exists: {counts['active_lmdb_exists']}")
    print('implementation_model: CMDHELP_PREVIEW_LOCALE_EXPLICIT_ONLY_DEFAULT_UNCHANGED')
    print(f'source_inventory_rows: {len(existing)}')
    print(f'unique_source_target: {target_unique}')
    print(f'source_target_override_used: {override_used}')
    print(f'source_target_override_valid: {override_valid}')
    print(f'source_target_override_reason: {override_reason}')
    print(f'selected_source_target: {target_path}')
    print(f'manifest: {mpath.relative_to(repo)}')
    print(f'source_patch_apply_staging_report: {md.relative_to(repo)}')
    print(f'source_target_selection: {(reports/"phase23t_source_target_selection.csv").relative_to(repo)}')
    print(f'apply_script: {apply_ps.relative_to(repo)}')
    print(f'apply_command: .\\{apply_ps.relative_to(repo)} -RepoRoot . -ConfirmPhase23T')
    print('source_files_written: 0')
    print('source_patch_applied_by_staging: 0')
    print('active_help_dbf_written: 0')
    print('active_help_cdx_written: 0')
    print('active_help_lmdb_written: 0')
    print('cmdhelp_behavior_changed: 0')
    print('cmdhelpchk_behavior_changed: 0')
    print('maint_behavior_changed: 0')
    print('bbox_behavior_changed: 0')
    print('runtime_execution_by_python: 0')
    print(f'next_gate: {NEXT_GATE if status==STATUS_GREEN else "FIX_SOURCE_TARGET_SELECTION_OR_REVIEW_PHASE23S_INVENTORY"}')
    return 0 if status==STATUS_GREEN else 2
if __name__=='__main__': raise SystemExit(main())
