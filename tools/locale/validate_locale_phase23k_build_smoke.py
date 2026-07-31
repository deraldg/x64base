#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

STATUS_GREEN = "LOCALE_PHASE23K_MESSAGING_LOCALE_SPINE_SOURCE_SCAFFOLD_BUILD_SMOKE_GREEN"
STATUS_BLOCKED = "LOCALE_PHASE23K_MESSAGING_LOCALE_SPINE_SOURCE_SCAFFOLD_BUILD_SMOKE_BLOCKED"
NEXT_GATE = "HOLD_OR_AUTHORIZE_PHASE23L_MESSAGING_LOCALE_SPINE_RUNTIME_STATUS_WIRING_PLAN"
LOCALE_REPORT_DIR = Path("docs/locale/reports")
RUNLOG = Path("docs/locale/runlog/LOC-023K_BUILD_AND_SMOKE_PROOF.md")

def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

def first_row(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    rows = read_csv(path)
    return rows[0] if rows else {}

def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        w.writeheader()
        for row in rows:
            w.writerow({k: row.get(k, "") for k in fields})

def exists_i(path: Path) -> int:
    return 1 if path.exists() else 0

def has_build_success(upper: str) -> bool:
    return (
        "DOTTALKPP.VCXPROJ ->" in upper
        or "BUILT TARGET DOTTALKPP" in upper
        or "BUILD SUCCEEDED" in upper
    )

def has_message_catalog_status_green(upper: str) -> bool:
    if "MESSAGE CATALOG VALIDATION: GREEN" in upper:
        return True
    if "MESSAGE_CATALOG" in upper and "VALIDATION ISSUES: 0" in upper:
        return True
    return (
        "MESSAGE CATALOG PROVIDER STATUS:" in upper
        and "MODE: ACTIVE_DBF" in upper
        and "ACTIVE CATALOG LOADED: YES" in upper
        and "MESSAGE COUNT: 12" in upper
        and "TEXT ROW COUNT: 60" in upper
    )

def has_en_lookup(upper: str) -> bool:
    return "LOCALE: EN-US" in upper and "TYPE HELP USE FOR MORE INFORMATION." in upper

def has_es_lookup(upper: str) -> bool:
    return "LOCALE: ES" in upper and "ESCRIBA HELP USE PARA OBTENER MAS INFORMACION." in upper

def has_fallback_lookup(upper: str) -> bool:
    return (
        "LOCALE: XX-XX" in upper
        and "FALLBACK LOCALE: EN-US" in upper
        and "TYPE HELP USE FOR MORE INFORMATION." in upper
    )

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    reports = repo / LOCALE_REPORT_DIR
    reports.mkdir(parents=True, exist_ok=True)

    apply_row = first_row(reports / "locale_phase23k_apply_status_summary_v1.csv")
    runlog = repo / RUNLOG
    text = runlog.read_text(encoding="utf-8", errors="replace") if runlog.exists() else ""
    upper = text.upper()

    header = repo / "src/help/locale_spine_catalog.hpp"
    cpp = repo / "src/help/locale_spine_catalog.cpp"

    gates: list[dict[str, Any]] = []
    failures = 0

    def gate(name: str, ok: bool, detail: str) -> None:
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": detail})
        if not ok:
            failures += 1

    gate("PHASE23K_APPLY_STATUS_GREEN",
         apply_row.get("STATUS") == "LOCALE_PHASE23K_GUARDED_MESSAGING_LOCALE_SPINE_SOURCE_PATCH_APPLIED_BUILD_HELD",
         apply_row.get("STATUS", ""))
    gate("HEADER_PRESENT", header.exists(), str(header))
    gate("CPP_PRESENT", cpp.exists(), str(cpp))
    gate("RUNLOG_PRESENT", runlog.exists(), str(runlog))
    gate("BUILD_SUCCESS_PROOF",
         has_build_success(upper),
         "expected cmake/MSBuild dottalkpp target success proof")
    gate("MESSAGE_CATALOG_STATUS_STILL_GREEN",
         has_message_catalog_status_green(upper),
         "current Messaging provider status/check should remain green: active_dbf, loaded, 12/60")
    gate("MESSAGE_GET_EN_STILL_WORKS",
         has_en_lookup(upper),
         "English lookup/substitution should work")
    gate("MESSAGE_GET_ES_STILL_WORKS",
         has_es_lookup(upper),
         "Spanish lookup/substitution should work")
    gate("MESSAGE_GET_FALLBACK_STILL_WORKS",
         has_fallback_lookup(upper),
         "unsupported locale fallback should still resolve to en-US")
    gate("NO_PROTECTED_MUTATION_TEXT",
         "HELP DATA MUTATION" not in upper and "CMDHELPCHK MUTATION" not in upper,
         "no protected mutation proof text")

    status = STATUS_GREEN if failures == 0 else STATUS_BLOCKED
    validation_issues = str(failures)

    boundary = [
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "23K validation only; source mutation already accounted by apply step."},
        {"PROTECTED_SYSTEM": "BUILD", "MUTATION_ALLOWED": 1, "OBSERVED_MUTATION": 1 if has_build_success(upper) else 0, "DETAIL": "Build proof supplied by operator."},
        {"PROTECTED_SYSTEM": "RUNTIME_SMOKE", "MUTATION_ALLOWED": 1, "OBSERVED_MUTATION": 1 if has_message_catalog_status_green(upper) else 0, "DETAIL": "Runtime smoke proof supplied by operator."},
        {"PROTECTED_SYSTEM": "ACTIVE_LOCALE_SPINE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active DBF/CDX/LMDB mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_DBF_CATALOG", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active Messaging catalog mutation."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No HELP DATA mutation."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CMDHELPCHK mutation."},
        {"PROTECTED_SYSTEM": "MANUALGEN", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No manualgen mutation."},
        {"PROTECTED_SYSTEM": "DATADICT_SELF_DOC", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No Data Dictionary/SelfDoc mutation."},
    ]

    write_csv(reports / "locale_phase23k_status_summary_v1.csv", [{
        "STATUS": status,
        "VALIDATION_ISSUES": validation_issues,
        "HEADER_PRESENT": exists_i(header),
        "CPP_PRESENT": exists_i(cpp),
        "BUILD_PROOF": 1 if has_build_success(upper) else 0,
        "RUNTIME_SMOKE_PROOF": 1 if status == STATUS_GREEN else 0,
        "MESSAGE_PROVIDER_STATUS_PROOF": 1 if has_message_catalog_status_green(upper) else 0,
        "EN_LOOKUP_PROOF": 1 if has_en_lookup(upper) else 0,
        "ES_LOOKUP_PROOF": 1 if has_es_lookup(upper) else 0,
        "FALLBACK_LOOKUP_PROOF": 1 if has_fallback_lookup(upper) else 0,
        "NEXT_GATE": NEXT_GATE,
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }], ["STATUS", "VALIDATION_ISSUES", "HEADER_PRESENT", "CPP_PRESENT",
         "BUILD_PROOF", "RUNTIME_SMOKE_PROOF", "MESSAGE_PROVIDER_STATUS_PROOF",
         "EN_LOOKUP_PROOF", "ES_LOOKUP_PROOF", "FALLBACK_LOOKUP_PROOF",
         "NEXT_GATE", "REPORT_TIMESTAMP_UTC"])

    write_csv(reports / "locale_phase23k_gate_check_v1.csv", gates, ["GATE", "STATUS", "DETAIL"])
    write_csv(reports / "locale_phase23k_validation_boundary_ledger_v1.csv", boundary,
              ["PROTECTED_SYSTEM", "MUTATION_ALLOWED", "OBSERVED_MUTATION", "DETAIL"])

    print(status)
    print(f"  validation issues: {validation_issues}")
    print(f"  header present: {exists_i(header)}")
    print(f"  cpp present: {exists_i(cpp)}")
    print(f"  build proof: {1 if has_build_success(upper) else 0}")
    print(f"  runtime smoke proof: {1 if status == STATUS_GREEN else 0}")
    print(f"  message provider status proof: {1 if has_message_catalog_status_green(upper) else 0}")
    print(f"  en lookup proof: {1 if has_en_lookup(upper) else 0}")
    print(f"  es lookup proof: {1 if has_es_lookup(upper) else 0}")
    print(f"  fallback lookup proof: {1 if has_fallback_lookup(upper) else 0}")
    print(f"  next gate: {NEXT_GATE}")
    print(f"  reports: {reports}")
    return 0 if status == STATUS_GREEN else 2

if __name__ == "__main__":
    raise SystemExit(main())
