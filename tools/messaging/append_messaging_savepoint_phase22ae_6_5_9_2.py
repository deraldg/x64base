
from __future__ import annotations
import argparse, csv, subprocess, sys
from pathlib import Path
OK="MESSAGE_CATALOG_PHASE22AE_6_5_9_2_CANDIDATE_CDX_BUILDLMDB_WORKAREA_PROOF_GREEN_SOURCE_HELD"
def first(p):
    with p.open("r", encoding="utf-8-sig", newline="") as f:
        r=list(csv.DictReader(f)); return r[0] if r else {}
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--accept-messaging-savepoint", action="store_true")
    a=ap.parse_args()
    if not a.accept_messaging_savepoint:
        print("[MSG-022AE.6.5.9.2] Refusing without --accept-messaging-savepoint", file=sys.stderr); return 2
    repo=Path(a.repo_root).resolve()
    row=first(repo/"docs/messaging/reports/message_catalog_phase22ae_6_5_9_2_validate_status_summary_v1.csv")
    if row.get("STATUS","") != OK:
        print(f"[MSG-022AE.6.5.9.2] Refusing savepoint: expected {OK}, got {row.get('STATUS','')}", file=sys.stderr); return 2
    generic=repo/"tools/messaging/append_messaging_savepoint.py"
    cmd=[
        sys.executable,str(generic),"--repo-root",str(repo),
        "--savepoint-id","MSG-022AE.6.5.9.2","--lane","MESSAGING","--status",OK,
        "--phase","Phase 22AE.6.5.9.2 candidate CDX BUILDLMDB work-area proof",
        "--summary","6.5.9.2 proved candidate-only CDX plus BUILDLMDB with explicit SELECT 1/2 work areas, SETPATH DBF/INDEXES/LMDB, usable SET INDEX/SET ORDER, and WORKSPACE visibility, without active/default path mutation.",
        "--next-gate",row.get("NEXT_GATE",""),
        "--source-reports","docs/messaging/reports/message_catalog_phase22ae_6_5_9_2_validate_status_summary_v1.csv;docs/messaging/reports/message_catalog_phase22ae_6_5_9_2_candidate_index_lmdb_inventory_v1.csv;docs/messaging/reports/message_catalog_phase22ae_6_5_9_2_boundary_ledger_v1.csv",
        "--validation-issues",row.get("VALIDATION_ISSUES","0"),
        "--allowed-candidate-mutations","candidate-only CDX and LMDB rebuild under docs/messaging/candidates using SETPATH INDEXES and SETPATH LMDB",
        "--forbidden-active-mutations","no active/default index mutation; no active/default LMDB mutation; no active DBF/catalog mutation; no source edits; no HELP DATA mutation; no CMDHELPCHK mutation",
        "--accept-messaging-savepoint"
    ]
    return subprocess.call(cmd)
if __name__=="__main__":
    raise SystemExit(main())
