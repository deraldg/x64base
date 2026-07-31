
from __future__ import annotations
import argparse, csv, subprocess, sys
from pathlib import Path
OK="MESSAGE_CATALOG_PHASE22AE_6_5_9_1_CANDIDATE_CDX_SETPATH_REPAIR_GREEN_SOURCE_HELD"
def first(p):
    with p.open("r", encoding="utf-8-sig", newline="") as f:
        r=list(csv.DictReader(f)); return r[0] if r else {}
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--accept-messaging-savepoint", action="store_true")
    a=ap.parse_args()
    if not a.accept_messaging_savepoint:
        print("[MSG-022AE.6.5.9.1] Refusing without --accept-messaging-savepoint", file=sys.stderr); return 2
    repo=Path(a.repo_root).resolve()
    row=first(repo/"docs/messaging/reports/message_catalog_phase22ae_6_5_9_1_validate_status_summary_v1.csv")
    if row.get("STATUS","") != OK:
        print(f"[MSG-022AE.6.5.9.1] Refusing savepoint: expected {OK}, got {row.get('STATUS','')}", file=sys.stderr); return 2
    generic=repo/"tools/messaging/append_messaging_savepoint.py"
    cmd=[
        sys.executable,str(generic),"--repo-root",str(repo),
        "--savepoint-id","MSG-022AE.6.5.9.1","--lane","MESSAGING","--status",OK,
        "--phase","Phase 22AE.6.5.9.1 candidate CDX SETPATH repair",
        "--summary","6.5.9.1 repaired the failed candidate CDX rebuild path by using simple DTS path setup via SETPATH DBF and SETPATH INDEXES, with no SET CDX or SET INDEXES TO, and preserved active/default index boundaries.",
        "--next-gate",row.get("NEXT_GATE",""),
        "--source-reports","docs/messaging/reports/message_catalog_phase22ae_6_5_9_1_validate_status_summary_v1.csv;docs/messaging/reports/message_catalog_phase22ae_6_5_9_1_candidate_cdx_inventory_v1.csv;docs/messaging/reports/message_catalog_phase22ae_6_5_9_1_boundary_ledger_v1.csv",
        "--validation-issues",row.get("VALIDATION_ISSUES","0"),
        "--allowed-candidate-mutations","candidate-only CDX rebuild under docs/messaging/candidates using SETPATH INDEXES",
        "--forbidden-active-mutations","no active/default index mutation; no active DBF/catalog mutation; no active LMDB mutation; no source edits; no HELP DATA mutation; no CMDHELPCHK mutation",
        "--accept-messaging-savepoint"
    ]
    return subprocess.call(cmd)
if __name__=="__main__":
    raise SystemExit(main())
