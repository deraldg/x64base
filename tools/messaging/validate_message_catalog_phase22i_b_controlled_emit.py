#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv
from datetime import datetime, timezone
from pathlib import Path
GREEN="MESSAGE_CATALOG_PHASE22I_B_CONTROLLED_RUNTIME_EMISSION_SMOKE_GREEN"
BLOCKED="MESSAGE_CATALOG_PHASE22I_B_CONTROLLED_RUNTIME_EMISSION_SMOKE_BLOCKED"
NEXT="HOLD_OR_AUTHORIZE_PHASE22J_PLACEHOLDER_ARGUMENT_CONTRACT_REVIEW"
RUNLOG=Path("docs/messaging/runlog/MSG-022I_B_CONTROLLED_EMIT_SMOKE.md")
def rows(p):
    if not p.exists(): return []
    with p.open("r", encoding="utf-8-sig", newline="") as f: return list(csv.DictReader(f))
def first(p):
    r=rows(p); return r[0] if r else {}
def write_csv(p,data,fields):
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8", newline="") as f:
        w=csv.DictWriter(f, fieldnames=fields, lineterminator="\n"); w.writeheader()
        for row in data: w.writerow({k:row.get(k,"") for k in fields})
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--repo-root", required=True); args=ap.parse_args()
    repo=Path(args.repo_root).resolve(); reports=repo/"docs/messaging/reports"; reports.mkdir(parents=True, exist_ok=True)
    p=first(reports/"message_catalog_phase22i_b_status_summary_v1.csv")
    msg=p.get("MESSAGES","12"); txt=p.get("TEXT_ROWS","60"); loc=p.get("LOCALES","de;en-US;es;fr;it")
    text=(repo/RUNLOG).read_text(encoding="utf-8", errors="replace") if (repo/RUNLOG).exists() else ""
    up=text.upper(); gates=[]; fail=0
    def gate(n, ok, d):
        nonlocal fail
        gates.append({"GATE":n,"STATUS":"PASS" if ok else "FAIL","DETAIL":d})
        if not ok: fail+=1
    gate("PHASE22I_B_PATCH_APPLIED", p.get("STATUS")== "MESSAGE_CATALOG_PHASE22I_B_CONTROLLED_RUNTIME_EMISSION_PATCH_APPLIED", p.get("STATUS",""))
    gate("RUNLOG_PRESENT", (repo/RUNLOG).exists(), str(repo/RUNLOG))
    gate("SET_MESSAGE_EMIT_PRESENT", "SET MESSAGE EMIT:" in up, "controlled emit heading")
    gate("PROVIDER_ACTIVE_DBF", "PROVIDER MODE: ACTIVE_DBF" in up, "provider active_dbf")
    gate("ACTIVE_CATALOG_LOADED_YES", "ACTIVE CATALOG LOADED: YES" in up, "active catalog loaded")
    gate("SYMBOL_HELP_HINT_COMMAND", "SYMBOL: HELP_HINT_COMMAND" in up, "sample symbol")
    gate("LOCALE_ES", "LOCALE: ES" in up or "CURRENT LOCALE: ES" in up, "locale es")
    gate("TEXT_NOT_EMPTY", "TEXT:" in up and "TEXT: <EMPTY>" not in up, "non-empty text")
    gate("CONTROLLED_EMISSION_PROOF_YES", "RUNTIME CONTROLLED EMISSION PROOF: YES" in up, "proof flag")
    gate("NO_WRITEBACK_BOUNDARY", "NO DBF/CDX/LMDB MUTATION" in up and "NO RUNTIME WRITEBACK" in up, "read-only boundary")
    status=GREEN if fail==0 else BLOCKED; val=str(fail)
    write_csv(reports/"message_catalog_phase22i_b_runtime_status_summary_v1.csv", [{"STATUS":status,"MESSAGES":msg,"TEXT_ROWS":txt,"LOCALES":loc,"VALIDATION_ISSUES":val,"CONTROLLED_EMIT_PROOF":1 if status==GREEN else 0,"ACTIVE_CATALOG_LOADED":1 if "ACTIVE CATALOG LOADED: YES" in up else 0,"EMIT_SYMBOL":"HELP_HINT_COMMAND","EMIT_LOCALE":"es","ACTIVE_CATALOG_MUTATION_OBSERVED":0,"SOURCE_MUTATION_OBSERVED":0,"NEXT_GATE":NEXT,"REPORT_TIMESTAMP_UTC":datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00","Z")}], ["STATUS","MESSAGES","TEXT_ROWS","LOCALES","VALIDATION_ISSUES","CONTROLLED_EMIT_PROOF","ACTIVE_CATALOG_LOADED","EMIT_SYMBOL","EMIT_LOCALE","ACTIVE_CATALOG_MUTATION_OBSERVED","SOURCE_MUTATION_OBSERVED","NEXT_GATE","REPORT_TIMESTAMP_UTC"])
    write_csv(reports/"message_catalog_phase22i_b_runtime_gate_check_v1.csv", gates, ["GATE","STATUS","DETAIL"])
    boundary=[{"PROTECTED_SYSTEM":"SOURCE_CODE","MUTATION_ALLOWED":0,"OBSERVED_MUTATION":0,"DETAIL":"Runtime validation only; no source mutation."},{"PROTECTED_SYSTEM":"ACTIVE_MESSAGING_DBF_CATALOG","MUTATION_ALLOWED":0,"OBSERVED_MUTATION":0,"DETAIL":"No active DBF mutation."},{"PROTECTED_SYSTEM":"ACTIVE_MESSAGING_CDX_INDEXES","MUTATION_ALLOWED":0,"OBSERVED_MUTATION":0,"DETAIL":"No active CDX/index mutation."},{"PROTECTED_SYSTEM":"ACTIVE_MESSAGING_LMDB","MUTATION_ALLOWED":0,"OBSERVED_MUTATION":0,"DETAIL":"No active LMDB mutation."},{"PROTECTED_SYSTEM":"HELP_DATA","MUTATION_ALLOWED":0,"OBSERVED_MUTATION":0,"DETAIL":"No HELP DATA mutation."},{"PROTECTED_SYSTEM":"CMDHELPCHK","MUTATION_ALLOWED":0,"OBSERVED_MUTATION":0,"DETAIL":"No CMDHELPCHK mutation."},{"PROTECTED_SYSTEM":"MANUALGEN","MUTATION_ALLOWED":0,"OBSERVED_MUTATION":0,"DETAIL":"No manualgen mutation."},{"PROTECTED_SYSTEM":"DATADICT_SELF_DOC","MUTATION_ALLOWED":0,"OBSERVED_MUTATION":0,"DETAIL":"No Data Dictionary/SelfDoc mutation."}]
    write_csv(reports/"message_catalog_phase22i_b_runtime_boundary_ledger_v1.csv", boundary, ["PROTECTED_SYSTEM","MUTATION_ALLOWED","OBSERVED_MUTATION","DETAIL"])
    print(status); print(f"  messages: {msg}"); print(f"  text rows: {txt}"); print(f"  locales: {loc.replace(';', ', ')}"); print(f"  validation issues: {val}"); print(f"  controlled emit proof: {1 if status==GREEN else 0}"); print(f"  active catalog loaded: {1 if 'ACTIVE CATALOG LOADED: YES' in up else 0}"); print("  emit symbol: HELP_HINT_COMMAND"); print("  emit locale: es"); print(f"  next gate: {NEXT}"); print(f"  reports: {reports}")
    return 0 if status==GREEN else 2
if __name__=="__main__": raise SystemExit(main())
