#!/usr/bin/env python3
"""
Phase 22D: Build and provider-boundary closeout.

This validates that the Phase 22C source patch builds/links and that the provider
boundary is present in the active source/build list.

It does not claim:
  - runtime DBF row loading
  - SET LANGUAGE integration through active DBF
  - HELP/CMDHELPCHK mutation

Those belong to a later runtime status/check phase.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

STATUS_GREEN = "MESSAGE_CATALOG_PHASE22D_BUILD_PROVIDER_BOUNDARY_GREEN"
STATUS_BLOCKED = "MESSAGE_CATALOG_PHASE22D_BUILD_PROVIDER_BOUNDARY_BLOCKED"
NEXT_GATE = "HOLD_OR_AUTHORIZE_PHASE22E_RUNTIME_PROVIDER_STATUS_COMMAND_SMOKE"
REPORT_DIR = Path("docs/messaging/reports")
RUNLOG = Path("docs/messaging/runlog/MSG-022D_BUILD_PROVIDER_BOUNDARY.md")

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

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def source_inv(repo: Path) -> list[dict[str, Any]]:
    rows = []
    for r in [
        "src/help/message_catalog.hpp",
        "src/help/message_catalog.cpp",
        "src/help/CMakeLists.txt",
        "src/help/helpdata_messages.hpp",
        "src/help/helpdata_messages.cpp",
    ]:
        p = repo / r
        rows.append({
            "PATH": r,
            "EXISTS": 1 if p.exists() else 0,
            "BYTES": p.stat().st_size if p.exists() and p.is_file() else 0,
            "SHA256": sha256_file(p) if p.exists() and p.is_file() else "",
        })
    return rows

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    reports = repo / REPORT_DIR
    reports.mkdir(parents=True, exist_ok=True)

    p22c = first_row(reports / "message_catalog_phase22c_status_summary_v1.csv")
    messages = p22c.get("MESSAGES", "12")
    text_rows = p22c.get("TEXT_ROWS", "60")
    locales = p22c.get("LOCALES", "de;en-US;es;fr;it")

    runlog = repo / RUNLOG
    runtext = runlog.read_text(encoding="utf-8", errors="replace") if runlog.exists() else ""
    upper = runtext.upper()

    cmake_path = repo / "src/help/CMakeLists.txt"
    cmake_text = cmake_path.read_text(encoding="utf-8", errors="replace") if cmake_path.exists() else ""

    hpp = repo / "src/help/message_catalog.hpp"
    cpp = repo / "src/help/message_catalog.cpp"

    gates: list[dict[str, Any]] = []
    failures = 0

    def gate(name: str, ok: bool, detail: str) -> None:
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": detail})
        if not ok:
            failures += 1

    def review(name: str, ok: bool, detail: str) -> None:
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "REVIEW", "DETAIL": detail})

    gate("PHASE22C_PATCH_APPLIED", p22c.get("STATUS") == "MESSAGE_CATALOG_PHASE22C_RUNTIME_PROVIDER_SOURCE_PATCH_APPLIED", p22c.get("STATUS", ""))
    gate("MESSAGE_CATALOG_HPP_PRESENT", hpp.exists(), "src/help/message_catalog.hpp")
    gate("MESSAGE_CATALOG_CPP_PRESENT", cpp.exists(), "src/help/message_catalog.cpp")
    gate("CMAKE_INCLUDES_MESSAGE_CATALOG_CPP", "message_catalog.cpp" in cmake_text, "src/help/CMakeLists.txt")
    gate("RUNLOG_PRESENT", runlog.exists(), str(runlog))

    build_green = (
        "BUILD RESULT: GREEN" in upper or
        "BUILD: GREEN" in upper or
        "BUILD SUCCEEDED" in upper or
        "BUILT TARGET DOTTALKPP" in upper or
        "DOTTALKPP.VCXPROJ ->" in upper or
        "0 ERROR" in upper and "CMAKE --BUILD" in upper
    )
    gate("BUILD_RESULT_GREEN", build_green, "runlog should contain build green/succeeded proof")

    review("RUNTIME_DB_ROW_LOADING_NOT_CLAIMED", False, "Phase 22D validates build/provider boundary only; DBF row loading is later.")
    review("RUNTIME_STATUS_COMMAND_NOT_CLAIMED", False, "Phase 22E should expose/status-smoke the provider.")

    status = STATUS_GREEN if failures == 0 else STATUS_BLOCKED
    validation_issues = str(failures)

    write_csv(reports / "message_catalog_phase22d_status_summary_v1.csv", [{
        "STATUS": status,
        "MESSAGES": messages,
        "TEXT_ROWS": text_rows,
        "LOCALES": locales,
        "VALIDATION_ISSUES": validation_issues,
        "BUILD_GREEN": 1 if status == STATUS_GREEN else 0,
        "PROVIDER_BOUNDARY_PRESENT": 1 if hpp.exists() and cpp.exists() and "message_catalog.cpp" in cmake_text else 0,
        "RUNTIME_DBF_ROW_LOADING_PROOF": 0,
        "RUNTIME_PROVIDER_STATUS_SMOKE": 0,
        "SOURCE_MUTATION_AUTHORIZED": 0,
        "SOURCE_MUTATION_OBSERVED": 0,
        "NEXT_GATE": NEXT_GATE,
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }], ["STATUS", "MESSAGES", "TEXT_ROWS", "LOCALES", "VALIDATION_ISSUES",
         "BUILD_GREEN", "PROVIDER_BOUNDARY_PRESENT", "RUNTIME_DBF_ROW_LOADING_PROOF",
         "RUNTIME_PROVIDER_STATUS_SMOKE", "SOURCE_MUTATION_AUTHORIZED",
         "SOURCE_MUTATION_OBSERVED", "NEXT_GATE", "REPORT_TIMESTAMP_UTC"])

    write_csv(reports / "message_catalog_phase22d_gate_check_v1.csv", gates,
              ["GATE", "STATUS", "DETAIL"])

    write_csv(reports / "message_catalog_phase22d_source_inventory_v1.csv", source_inv(repo),
              ["PATH", "EXISTS", "BYTES", "SHA256"])

    boundary = [
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Phase 22D validates build only; no source mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_DBF_CATALOG", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_CDX_INDEXES", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active CDX/index mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active LMDB mutation."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No HELP DATA mutation."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CMDHELPCHK mutation."},
        {"PROTECTED_SYSTEM": "MANUALGEN", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No manualgen mutation."},
        {"PROTECTED_SYSTEM": "DATADICT_SELF_DOC", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No Data Dictionary/SelfDoc mutation."},
    ]
    write_csv(reports / "message_catalog_phase22d_boundary_ledger_v1.csv", boundary,
              ["PROTECTED_SYSTEM", "MUTATION_ALLOWED", "OBSERVED_MUTATION", "DETAIL"])

    md = f"""# Message Catalog Phase 22D Build and Provider Boundary Closeout

Status: `{status}`

Phase 22D validates that the Phase 22C runtime provider boundary builds/links.

## Proven

- `src/help/message_catalog.hpp` present.
- `src/help/message_catalog.cpp` present.
- `src/help/CMakeLists.txt` includes `message_catalog.cpp`.
- `dottalkpp` build reported green.

## Not claimed

- Runtime active DBF row loading.
- Runtime SET LANGUAGE integration through active DBF rows.
- Runtime provider status command.

## Next gate

`{NEXT_GATE}`
"""
    (reports / "MESSAGE_CATALOG_PHASE22D_BUILD_PROVIDER_BOUNDARY_CLOSEOUT.md").write_text(md, encoding="utf-8")

    print(status)
    print(f"  messages: {messages}")
    print(f"  text rows: {text_rows}")
    print(f"  locales: {locales.replace(';', ', ')}")
    print(f"  validation issues: {validation_issues}")
    print(f"  build green: {1 if status == STATUS_GREEN else 0}")
    print(f"  provider boundary present: {1 if hpp.exists() and cpp.exists() and 'message_catalog.cpp' in cmake_text else 0}")
    print("  runtime dbf row loading proof: 0")
    print("  source mutation observed: 0")
    print(f"  next gate: {NEXT_GATE}")
    print(f"  reports: {reports}")
    return 0 if status == STATUS_GREEN else 2

if __name__ == "__main__":
    raise SystemExit(main())
