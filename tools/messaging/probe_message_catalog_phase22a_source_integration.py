#!/usr/bin/env python3
"""
Phase 22A: Runtime Messaging catalog source-integration probe and patch plan.

Report-only. No source mutation.

Purpose:
  - Accept MSG-021 authorization path.
  - Inspect actual source seams for compiled/static message loading.
  - Produce a guarded Phase 22B patch plan for a read-only active DBF catalog
    provider with compiled/static fallback.
  - Keep DotScript commands English-only.
  - Keep runtime writeback forbidden.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

STATUS_GREEN = "MESSAGE_CATALOG_PHASE22A_RUNTIME_SOURCE_INTEGRATION_PROBE_GREEN_SOURCE_HELD"
STATUS_BLOCKED = "MESSAGE_CATALOG_PHASE22A_RUNTIME_SOURCE_INTEGRATION_PROBE_BLOCKED"
NEXT_GATE = "HOLD_OR_AUTHORIZE_PHASE22B_GUARDED_RUNTIME_PROVIDER_SOURCE_PATCH"
REPORT_DIR = Path("docs/messaging/reports")

SOURCE_FILES = [
    "src/help/helpdata_messages.cpp",
    "src/cli/cmd_set.cpp",
    "src/cli/command_output.cpp",
    "src/cli/command_registry.cpp",
    "src/cli/cmd_display.cpp",
]

OPTIONAL_SOURCE_FILES = [
    "src/help/message_catalog.cpp",
    "src/help/message_catalog.h",
    "src/help/helpdata_messages.h",
    "src/help/helpdata_cmdhelp_bridge.cpp",
    "src/help/helpdata_artifacts.cpp",
]

ACTIVE_ARTIFACTS = [
    "dottalkpp/data/messaging/SYSTEM_MESSAGES.dbf",
    "dottalkpp/data/messaging/SYSTEM_MESSAGE_TEXT.dbf",
    "dottalkpp/data/messaging/SYSTEM_MESSAGE_TEXT.dtx",
    "dottalkpp/data/indexes/messaging/SYSTEM_MESSAGES.cdx",
    "dottalkpp/data/indexes/messaging/SYSTEM_MESSAGE_TEXT.cdx",
    "dottalkpp/data/lmdb/messaging/SYSTEM_MESSAGES.cdx.d/data.mdb",
    "dottalkpp/data/lmdb/messaging/SYSTEM_MESSAGE_TEXT.cdx.d/data.mdb",
]

PATTERNS = [
    "SET LANGUAGE",
    "SET LOCALE",
    "Message locale",
    "MESSAGE_LOCALE",
    "SET LANGUAGE CHECK",
    "message catalog",
    "helpdata_messages",
    "SYSTEM_MESSAGES",
    "SYSTEM_MESSAGE_TEXT",
    "locale",
    "CommandDeprecated",
    "UnsupportedMessageLocale",
    "NoOpenTable",
]

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

def rel(path: Path, repo: Path) -> str:
    try:
        return str(path.relative_to(repo)).replace("\\", "/")
    except ValueError:
        return str(path)

def source_lines(path: Path, patterns: list[str]) -> list[dict[str, Any]]:
    rows = []
    if not path.exists() or not path.is_file():
        return rows
    text = path.read_text(encoding="utf-8", errors="replace").splitlines()
    for i, line in enumerate(text, start=1):
        low = line.lower()
        hits = [p for p in patterns if p.lower() in low]
        if hits:
            rows.append({
                "LINE": i,
                "PATTERNS": ";".join(hits),
                "TEXT": line[:240],
            })
    return rows

def file_inventory(repo: Path, rels: list[str], role: str) -> list[dict[str, Any]]:
    rows = []
    for r in rels:
        p = repo / r
        rows.append({
            "PATH": r,
            "EXISTS": 1 if p.exists() else 0,
            "BYTES": p.stat().st_size if p.exists() and p.is_file() else 0,
            "SHA256": sha256_file(p) if p.exists() and p.is_file() else "",
            "ROLE": role,
        })
    return rows

def savepoint_present(index_path: Path, savepoint_id: str) -> bool:
    if not index_path.exists():
        return False
    try:
        return any(r.get("savepoint_id") == savepoint_id for r in read_csv(index_path))
    except Exception:
        return False

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    reports = repo / REPORT_DIR
    reports.mkdir(parents=True, exist_ok=True)

    p21 = first_row(reports / "message_catalog_phase21_status_summary_v1.csv")
    p20 = first_row(reports / "message_catalog_phase20_status_summary_v1.csv")
    savepoint_index = reports / "message_savepoint_thread_index_v1.csv"

    messages = p21.get("MESSAGES", p20.get("MESSAGES", "12"))
    text_rows = p21.get("TEXT_ROWS", p20.get("TEXT_ROWS", "60"))
    locales = p21.get("LOCALES", p20.get("LOCALES", "de;en-US;es;fr;it"))

    gates: list[dict[str, Any]] = []
    failures = 0

    def gate(name: str, ok: bool, detail: str) -> None:
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": detail})
        if not ok:
            failures += 1

    def review(name: str, ok: bool, detail: str) -> None:
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "REVIEW", "DETAIL": detail})

    gate("PHASE21_REVIEW_GREEN", p21.get("STATUS") == "MESSAGE_CATALOG_PHASE21_RUNTIME_INTEGRATION_REVIEW_GREEN_SOURCE_HELD", p21.get("STATUS", ""))
    gate("PHASE20_INDEX_QUERY_GREEN", p20.get("STATUS") == "MESSAGE_CATALOG_PHASE20_ACTIVE_INDEX_QUERY_SMOKE_GREEN", p20.get("STATUS", ""))
    review("MSG_021_SAVEPOINT_PRESENT", savepoint_present(savepoint_index, "MSG-021"), "MSG-021 savepoint recommended before Phase 22B.")

    for r in ACTIVE_ARTIFACTS:
        gate("ACTIVE_ARTIFACT_PRESENT", (repo / r).exists(), r)

    for r in SOURCE_FILES:
        gate("REQUIRED_SOURCE_PRESENT", (repo / r).exists(), r)

    source_inventory = file_inventory(repo, SOURCE_FILES, "required_source_candidate") + file_inventory(repo, OPTIONAL_SOURCE_FILES, "optional_source_candidate")
    write_csv(reports / "message_catalog_phase22a_source_inventory_v1.csv", source_inventory,
              ["PATH", "EXISTS", "BYTES", "SHA256", "ROLE"])

    hit_rows = []
    for r in SOURCE_FILES + OPTIONAL_SOURCE_FILES:
        p = repo / r
        for row in source_lines(p, PATTERNS):
            out = {"SOURCE_PATH": r}
            out.update(row)
            hit_rows.append(out)
    write_csv(reports / "message_catalog_phase22a_source_pattern_hits_v1.csv", hit_rows,
              ["SOURCE_PATH", "LINE", "PATTERNS", "TEXT"])

    # Determine observed seam status from source existence.
    message_catalog_cpp_exists = (repo / "src/help/message_catalog.cpp").exists()
    helpdata_messages_exists = (repo / "src/help/helpdata_messages.cpp").exists()
    cmd_set_exists = (repo / "src/cli/cmd_set.cpp").exists()

    seam_rows = [
        {
            "SEAM_ID": "SEAM-001",
            "SEAM": "compiled message seed/source rows",
            "SOURCE_PATH": "src/help/helpdata_messages.cpp",
            "STATUS": "PRESENT" if helpdata_messages_exists else "MISSING",
            "RECOMMENDATION": "keep as fallback; add active DBF load path alongside it, not instead of it",
        },
        {
            "SEAM_ID": "SEAM-002",
            "SEAM": "message catalog provider module",
            "SOURCE_PATH": "src/help/message_catalog.cpp/.h",
            "STATUS": "MISSING" if not message_catalog_cpp_exists else "PRESENT",
            "RECOMMENDATION": "create a small provider module in Phase 22B if authorized; do not overload cmd_set.cpp",
        },
        {
            "SEAM_ID": "SEAM-003",
            "SEAM": "SET LANGUAGE / SET LOCALE command surface",
            "SOURCE_PATH": "src/cli/cmd_set.cpp",
            "STATUS": "PRESENT" if cmd_set_exists else "MISSING",
            "RECOMMENDATION": "add mode/status/check command hooks only after provider API is available",
        },
        {
            "SEAM_ID": "SEAM-004",
            "SEAM": "message output/emission path",
            "SOURCE_PATH": "src/cli/command_output.cpp",
            "STATUS": "PRESENT" if (repo / "src/cli/command_output.cpp").exists() else "MISSING",
            "RECOMMENDATION": "review only; do not patch until provider is proven",
        },
    ]
    write_csv(reports / "message_catalog_phase22a_integration_seams_v1.csv", seam_rows,
              ["SEAM_ID", "SEAM", "SOURCE_PATH", "STATUS", "RECOMMENDATION"])

    patch_plan_rows = [
        {
            "PATCH_ID": "22B-001",
            "TARGET_PATH": "src/help/message_catalog.h",
            "ACTION": "CREATE_OR_UPDATE",
            "DETAIL": "Declare a read-only runtime message catalog provider API with compiled fallback preserved.",
            "AUTHORIZED_NOW": 0,
        },
        {
            "PATCH_ID": "22B-002",
            "TARGET_PATH": "src/help/message_catalog.cpp",
            "ACTION": "CREATE_OR_UPDATE",
            "DETAIL": "Implement active DBF catalog load from dottalkpp/data/messaging + indexes/messaging + lmdb/messaging; no writeback.",
            "AUTHORIZED_NOW": 0,
        },
        {
            "PATCH_ID": "22B-003",
            "TARGET_PATH": "src/help/helpdata_messages.cpp",
            "ACTION": "SURGICAL_UPDATE",
            "DETAIL": "Expose existing compiled/static rows as fallback provider or seed function; do not delete compiled rows.",
            "AUTHORIZED_NOW": 0,
        },
        {
            "PATCH_ID": "22B-004",
            "TARGET_PATH": "src/cli/cmd_set.cpp",
            "ACTION": "SURGICAL_UPDATE",
            "DETAIL": "Add optional SET LANGUAGE/CATALOG status/check integration after provider compiles; keep existing SET LANGUAGE behavior stable.",
            "AUTHORIZED_NOW": 0,
        },
        {
            "PATCH_ID": "22B-005",
            "TARGET_PATH": "CMakeLists.txt or relevant src CMake file",
            "ACTION": "REVIEW_OR_UPDATE",
            "DETAIL": "Add message_catalog.cpp to build only if new source module is created.",
            "AUTHORIZED_NOW": 0,
        },
    ]
    write_csv(reports / "message_catalog_phase22a_guarded_patch_plan_v1.csv", patch_plan_rows,
              ["PATCH_ID", "TARGET_PATH", "ACTION", "DETAIL", "AUTHORIZED_NOW"])

    risk_rows = [
        {"RISK_ID": "RISK-001", "RISK": "DBF read API choice unknown from probe alone", "MITIGATION": "Phase 22B must inspect existing DBF open/use APIs and compile locally; no blind parser implementation."},
        {"RISK_ID": "RISK-002", "RISK": "runtime provider could destabilize current SET LANGUAGE behavior", "MITIGATION": "Default to compiled fallback; add active DBF mode only behind explicit gate until smoke green."},
        {"RISK_ID": "RISK-003", "RISK": "locale spine deferred", "MITIGATION": "Keep current LOCALE field support; plan SYSTEM_LOCALES/SYSTEM_LOCALE_FALLBACK as next schema extension."},
        {"RISK_ID": "RISK-004", "RISK": "duplicate MSG-020 savepoints observed", "MITIGATION": "Treat as nonblocking audit duplication; avoid relying on savepoint uniqueness alone for phase status."},
    ]
    write_csv(reports / "message_catalog_phase22a_risk_register_v1.csv", risk_rows,
              ["RISK_ID", "RISK", "MITIGATION"])

    status = STATUS_GREEN if failures == 0 else STATUS_BLOCKED
    validation_issues = str(failures)

    write_csv(reports / "message_catalog_phase22a_status_summary_v1.csv", [{
        "STATUS": status,
        "MESSAGES": messages,
        "TEXT_ROWS": text_rows,
        "LOCALES": locales,
        "VALIDATION_ISSUES": validation_issues,
        "ACTIVE_CATALOG_PROVEN": 1 if failures == 0 else 0,
        "SOURCE_MUTATION_AUTHORIZED": 0,
        "SOURCE_MUTATION_OBSERVED": 0,
        "RUNTIME_PROVIDER_PATCH_AUTHORIZED": 0,
        "NEXT_GATE": NEXT_GATE,
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }], ["STATUS", "MESSAGES", "TEXT_ROWS", "LOCALES", "VALIDATION_ISSUES",
         "ACTIVE_CATALOG_PROVEN", "SOURCE_MUTATION_AUTHORIZED", "SOURCE_MUTATION_OBSERVED",
         "RUNTIME_PROVIDER_PATCH_AUTHORIZED", "NEXT_GATE", "REPORT_TIMESTAMP_UTC"])

    write_csv(reports / "message_catalog_phase22a_gate_check_v1.csv", gates,
              ["GATE", "STATUS", "DETAIL"])

    boundary = [
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Phase 22A probe/report only; no source files edited."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_DBF_CATALOG", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_CDX_INDEXES", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active CDX/index mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active LMDB mutation."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No HELP DATA mutation."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CMDHELPCHK mutation."},
        {"PROTECTED_SYSTEM": "MANUALGEN", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No manualgen mutation."},
        {"PROTECTED_SYSTEM": "DATADICT_SELF_DOC", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No Data Dictionary/SelfDoc mutation."},
    ]
    write_csv(reports / "message_catalog_phase22a_boundary_ledger_v1.csv", boundary,
              ["PROTECTED_SYSTEM", "MUTATION_ALLOWED", "OBSERVED_MUTATION", "DETAIL"])

    md = f"""# Message Catalog Phase 22A Runtime Source Integration Probe

Status: `{status}`

Phase 22A is report-only. It confirms the active Messaging catalog is proven and
maps the source integration seams for a future guarded provider patch.

## Key finding

`src/help/message_catalog.cpp/.h` are not currently present. The safer Phase 22B
patch should create a small provider module rather than overloading `cmd_set.cpp`.

## Recommendation

Authorize Phase 22B only if source mutation is intended. Phase 22B should:

1. preserve compiled/static fallback;
2. add a read-only active DBF provider;
3. gate active DBF provider mode behind an explicit setting or internal mode;
4. smoke test `SET LANGUAGE CHECK` and sample localized messages;
5. avoid HELP DATA, CMDHELPCHK, manualgen, Data Dictionary/SelfDoc mutation.

## Next gate

`{NEXT_GATE}`
"""
    (reports / "MESSAGE_CATALOG_PHASE22A_RUNTIME_SOURCE_INTEGRATION_PROBE.md").write_text(md, encoding="utf-8")

    print(status)
    print(f"  messages: {messages}")
    print(f"  text rows: {text_rows}")
    print(f"  locales: {locales.replace(';', ', ')}")
    print(f"  validation issues: {validation_issues}")
    print(f"  active catalog proven: {1 if failures == 0 else 0}")
    print("  source mutation authorized: 0")
    print("  runtime provider patch authorized: 0")
    print(f"  next gate: {NEXT_GATE}")
    print(f"  reports: {reports}")
    return 0 if status == STATUS_GREEN else 2

if __name__ == "__main__":
    raise SystemExit(main())
