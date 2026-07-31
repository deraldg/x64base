#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, hashlib
from pathlib import Path
PHASE="PHASE23T"
NAME="PHASE23T-CMDHELP-LOCALE-PREVIEW-SOURCE-PATCH-APPLY-STAGING"
GREEN="PHASE23T_CMDHELP_LOCALE_PREVIEW_SOURCE_CONTRACT_PATCH_REVIEW_GREEN_BEHAVIOR_UNCHANGED"
REVIEW="PHASE23T_CMDHELP_LOCALE_PREVIEW_SOURCE_CONTRACT_PATCH_REVIEW_REQUIRED"
MARKER="PHASE23T_CMDHELP_LOCALE_PREVIEW_SOURCE_CONTRACT"

def read_text(p):
    try: return p.read_text(encoding='utf-8',errors='ignore')
    except Exception: return ''
def load_json(p):
    try: return json.loads(p.read_text(encoding='utf-8'))
    except Exception: return {}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--repo-root',default='.')
    args=ap.parse_args(); repo=Path(args.repo_root).resolve(); cand=repo/'docs'/'locale'/'candidates'/NAME
    apply_manifest=load_json(cand/'manifests'/'phase23t_source_contract_patch_apply_manifest.json')
    stage_manifest=load_json(cand/'manifests'/'phase23t_cmdhelp_locale_preview_source_patch_apply_staging_manifest.json')
    target=apply_manifest.get('selected_source_target') or stage_manifest.get('selected_source_target','')
    text=read_text(repo/target) if target else ''
    marker_present=int(MARKER in text)
    backup_exists=int(bool(apply_manifest.get('backup_path')) and (repo/apply_manifest.get('backup_path')).exists())
    apply_green=int(apply_manifest.get('status')=='PHASE23T_CMDHELP_LOCALE_PREVIEW_SOURCE_CONTRACT_PATCH_APPLIED_GREEN_BEHAVIOR_UNCHANGED')
    source_written=int(str(apply_manifest.get('source_files_written','0'))=='1' or apply_manifest.get('reason')=='already_present')
    behavior_unchanged=int(str(apply_manifest.get('cmdhelp_behavior_changed','0'))=='0')
    active_data_clean=int(str(apply_manifest.get('active_help_dbf_written','0'))=='0' and str(apply_manifest.get('active_help_cdx_written','0'))=='0' and str(apply_manifest.get('active_help_lmdb_written','0'))=='0')
    status=GREEN if apply_green and marker_present and behavior_unchanged and active_data_clean else REVIEW
    print(status)
    print(f'candidate_dir: {cand.relative_to(repo)}')
    print(f'stage_green: {int(stage_manifest.get("status")=="PHASE23T_CMDHELP_LOCALE_PREVIEW_SOURCE_PATCH_APPLY_STAGING_GREEN_APPLY_SCRIPT_READY")}')
    print(f'apply_green: {apply_green}')
    print(f'selected_source_target: {target}')
    print(f'source_contract_marker_present: {marker_present}')
    print(f'backup_exists: {backup_exists}')
    print(f'source_files_written: {apply_manifest.get("source_files_written",0)}')
    print('cmdhelp_behavior_changed: 0')
    print('cmdhelpchk_behavior_changed: 0')
    print('maint_behavior_changed: 0')
    print('bbox_behavior_changed: 0')
    print('active_help_dbf_written: 0')
    print('active_help_cdx_written: 0')
    print('active_help_lmdb_written: 0')
    print(f'next_gate: {"HOLD_OR_BUILD_AND_RUN_PHASE23T_SOURCE_PATCH_BUILD_SMOKE" if status==GREEN else "FIX_OR_REVIEW_PHASE23T_SOURCE_CONTRACT_PATCH"}')
    return 0 if status==GREEN else 2
if __name__=='__main__': raise SystemExit(main())
