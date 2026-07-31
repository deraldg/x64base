#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, json, hashlib, shutil
from pathlib import Path
from datetime import datetime, timezone

PHASE="PHASE23T"
STAGE_NAME="PHASE23T-CMDHELP-LOCALE-PREVIEW-SOURCE-PATCH-APPLY-STAGING"
GREEN="PHASE23T_CMDHELP_LOCALE_PREVIEW_SOURCE_CONTRACT_PATCH_APPLIED_GREEN_BEHAVIOR_UNCHANGED"
REVIEW="PHASE23T_CMDHELP_LOCALE_PREVIEW_SOURCE_CONTRACT_PATCH_REVIEW_REQUIRED"
MARKER="PHASE23T_CMDHELP_LOCALE_PREVIEW_SOURCE_CONTRACT"
BLOCK=[
"// @dottalk.locale-preview-contract v1 PHASE23T_CMDHELP_LOCALE_PREVIEW_SOURCE_CONTRACT",
"// CMDHELP <topic> PREVIEW LOCALE <locale> is the explicit-only locale preview surface.",
"// Default CMDHELP behavior remains unchanged until a separately authorized runtime implementation patch.",
"// Locale rows with DRAFT_PLACEHOLDER or NEEDS_REVIEW fall back to source/default text.",
]

def utc_now(): return datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')
def read_text(p:Path):
    try: return p.read_text(encoding='utf-8',errors='ignore')
    except Exception: return ''
def sha256(p:Path):
    h=hashlib.sha256(); h.update(p.read_bytes()); return h.hexdigest()
def load_manifest(repo:Path):
    p=repo/'docs'/'locale'/'candidates'/STAGE_NAME/'manifests'/'phase23t_cmdhelp_locale_preview_source_patch_apply_staging_manifest.json'
    if not p.exists(): return {},p
    return json.loads(p.read_text(encoding='utf-8')),p
def insert_block(text:str):
    if MARKER in text: return text, 'already_present'
    lines=text.splitlines()
    idx=None
    for i,l in enumerate(lines):
        if '@dottalk.usage' in l.lower(): idx=i+1
    if idx is None:
        for i,l in enumerate(lines):
            if 'CMDHELP' in l.upper(): idx=i; break
    if idx is None: return text, 'anchor_missing'
    lines[idx:idx]=['']+BLOCK+['']
    return '\n'.join(lines)+('\n' if text.endswith('\n') else ''), 'inserted'

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--repo-root',default='.'); ap.add_argument('--confirm-phase23t',action='store_true')
    args=ap.parse_args(); repo=Path(args.repo_root).resolve()
    cand=repo/'docs'/'locale'/'candidates'/STAGE_NAME
    reports=cand/'reports'; rollback=cand/'rollback'/f'source_pre_phase23t_{utc_now()}'; manifests=cand/'manifests'
    reports.mkdir(parents=True,exist_ok=True); rollback.mkdir(parents=True,exist_ok=True); manifests.mkdir(parents=True,exist_ok=True)
    stage,stage_path=load_manifest(repo)
    selected=stage.get('selected_source_target','')
    status=REVIEW; reason=''
    wrote=0; behavior_changed=0; backup_path=''; before_hash=''; after_hash=''
    if not args.confirm_phase23t:
        reason='missing_confirm_phase23t'
    elif not stage or stage.get('status')!='PHASE23T_CMDHELP_LOCALE_PREVIEW_SOURCE_PATCH_APPLY_STAGING_GREEN_APPLY_SCRIPT_READY':
        reason='staging_not_green'
    elif not selected:
        reason='no_unique_selected_source_target'
    else:
        target=repo/selected
        if not target.exists():
            reason='selected_source_target_missing'
        else:
            text=read_text(target)
            if 'CMDHELP' not in text.upper():
                reason='cmdhelp_anchor_missing'
            else:
                before_hash=sha256(target)
                backup=rollback/selected
                backup.parent.mkdir(parents=True,exist_ok=True)
                shutil.copy2(target,backup); backup_path=str(backup.relative_to(repo))
                new_text,mode=insert_block(text)
                if mode=='anchor_missing':
                    reason='insert_anchor_missing'
                elif mode=='already_present':
                    reason='already_present'
                    status=GREEN; after_hash=before_hash
                else:
                    target.write_text(new_text,encoding='utf-8')
                    wrote=1; status=GREEN; reason='source_contract_marker_inserted'; after_hash=sha256(target)
    log=reports/'PHASE23T_SOURCE_CONTRACT_PATCH_APPLY_LOG.txt'
    log.write_text('\n'.join([f'PHASE23T_APPLY_STATUS={status}',f'reason={reason}',f'selected_source_target={selected}',f'source_files_written={wrote}',f'cmdhelp_behavior_changed={behavior_changed}',f'backup_path={backup_path}',f'before_hash={before_hash}',f'after_hash={after_hash}','PHASE23T_APPLY_END']),encoding='utf-8')
    manifest={'phase':PHASE,'status':status,'reason':reason,'selected_source_target':selected,'source_files_written':wrote,'source_contract_marker':MARKER,'backup_path':backup_path,'before_hash':before_hash,'after_hash':after_hash,'cmdhelp_behavior_changed':behavior_changed,'cmdhelpchk_behavior_changed':0,'maint_behavior_changed':0,'bbox_behavior_changed':0,'active_help_dbf_written':0,'active_help_cdx_written':0,'active_help_lmdb_written':0,'apply_log':str(log.relative_to(repo)),'next_gate':'HOLD_OR_BUILD_AND_RUN_PHASE23T_SOURCE_PATCH_BUILD_SMOKE' if status==GREEN else 'FIX_OR_REVIEW_PHASE23T_SOURCE_PATCH_APPLY'}
    mpath=manifests/'phase23t_source_contract_patch_apply_manifest.json'; mpath.write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    print(status); print(f'candidate_dir: {cand.relative_to(repo)}'); print(f'selected_source_target: {selected}'); print(f'reason: {reason}'); print(f'source_files_written: {wrote}'); print(f'backup_path: {backup_path}'); print(f'before_hash: {before_hash}'); print(f'after_hash: {after_hash}'); print('cmdhelp_behavior_changed: 0'); print('cmdhelpchk_behavior_changed: 0'); print('maint_behavior_changed: 0'); print('bbox_behavior_changed: 0'); print('active_help_dbf_written: 0'); print('active_help_cdx_written: 0'); print('active_help_lmdb_written: 0'); print(f'apply_log: {log.relative_to(repo)}'); print(f'manifest: {mpath.relative_to(repo)}'); print(f"next_gate: {manifest['next_gate']}")
    return 0 if status==GREEN else 2
if __name__=='__main__': raise SystemExit(main())
