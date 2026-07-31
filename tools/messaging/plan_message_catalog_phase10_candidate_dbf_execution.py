#!/usr/bin/env python3
"""
Phase 10: Candidate DBF execution plan for DotTalk++ Messaging catalog.

This is plan-only. It consumes Phase 6/7/8/9 reports and writes Phase 10
planning reports under docs/messaging/reports. It does not create DBF/CDX/LMDB
artifacts, does not run DotTalk++, and does not promote any active catalog.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
from datetime import datetime, timezone

STATUS_GREEN = "MESSAGE_CATALOG_PHASE10_CANDIDATE_DBF_EXECUTION_PLAN_GREEN"
NEXT_GATE = "HOLD_OR_AUTHORIZE_PHASE11_INACTIVE_CANDIDATE_DBF_EXECUTION"
REPORT_DIR = Path("docs/messaging/reports")
CANDIDATE_ROOT = Path("docs/messaging/candidates/phase9_inactive_candidate_dbf_staging")

def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
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

def find_status(rows: list[dict[str, str]], expected: str) -> bool:
    return any((r.get("STATUS") or r.get("status") or "") == expected for r in rows)

def status_value(rows: list[dict[str, str]], key: str, default: str = "") -> str:
    if not rows:
        return default
    row = rows[0]
    return row.get(key) or row.get(key.upper()) or row.get(key.lower()) or default

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    reports = repo / REPORT_DIR
    candidate_root = repo / CANDIDATE_ROOT
    out = reports
    out.mkdir(parents=True, exist_ok=True)

    phase6_status_p = reports / "message_catalog_phase6_status_summary_v1.csv"
    phase7_status_p = reports / "message_catalog_phase7_status_summary_v1.csv"
    phase8_status_p = reports / "message_catalog_phase8_status_summary_v1.csv"
    phase9_status_p = reports / "message_catalog_phase9_status_summary_v1.csv"
    phase8_schema_p = reports / "message_catalog_phase8_dbf_schema_plan_v1.csv"
    phase8_tags_p = reports / "message_catalog_phase8_index_tag_plan_v1.csv"
    phase9_manifest_p = candidate_root / "candidate_manifest_v1.json"

    required_files = [
        ("PHASE6_STATUS", phase6_status_p),
        ("PHASE7_STATUS", phase7_status_p),
        ("PHASE8_STATUS", phase8_status_p),
        ("PHASE9_STATUS", phase9_status_p),
        ("PHASE8_SCHEMA_PLAN", phase8_schema_p),
        ("PHASE8_INDEX_TAG_PLAN", phase8_tags_p),
        ("PHASE9_CANDIDATE_MANIFEST", phase9_manifest_p),
    ]

    gate_rows: list[dict[str, object]] = []
    failures = 0
    for gate, path in required_files:
        ok = path.exists()
        gate_rows.append({"GATE": gate + "_PRESENT", "STATUS": "PASS" if ok else "FAIL", "DETAIL": str(path)})
        if not ok:
            failures += 1

    if failures:
        status = "MESSAGE_CATALOG_PHASE10_CANDIDATE_DBF_EXECUTION_PLAN_BLOCKED"
        messages = text_rows = validation_issues = "UNKNOWN"
        locales = ""
        manifest = {}
        candidate_artifacts = []
        schema_rows = []
        tag_rows = []
    else:
        p6 = read_csv(phase6_status_p)
        p7 = read_csv(phase7_status_p)
        p8 = read_csv(phase8_status_p)
        p9 = read_csv(phase9_status_p)
        schema_rows = read_csv(phase8_schema_p)
        tag_rows = read_csv(phase8_tags_p)
        manifest = json.loads(phase9_manifest_p.read_text(encoding="utf-8"))
        candidate_artifacts = manifest.get("candidate_artifacts", [])

        checks = [
            ("PHASE6_STATUS_GREEN", find_status(p6, "MESSAGE_CATALOG_PHASE6_SOURCE_EXPORT_GREEN"), "Phase 6 source export green"),
            ("PHASE7_STATUS_GREEN", find_status(p7, "MESSAGE_CATALOG_PHASE7_PROMOTION_READINESS_PLAN_GREEN"), "Phase 7 readiness plan green"),
            ("PHASE8_STATUS_GREEN", find_status(p8, "MESSAGE_CATALOG_PHASE8_DBF_SCHEMA_STAGING_PLAN_GREEN"), "Phase 8 DBF schema plan green"),
            ("PHASE9_STATUS_GREEN", find_status(p9, "MESSAGE_CATALOG_PHASE9_INACTIVE_CANDIDATE_STAGING_GREEN"), "Phase 9 inactive candidate staging green"),
            ("PHASE9_DBF_FILES_ZERO", str(manifest.get("dbf_files_created", "")) == "0" or manifest.get("dbf_files_created", None) == 0, "No DBF files were created in Phase 9"),
            ("PHASE9_ACTIVE_PROMOTION_ZERO", str(manifest.get("active_catalog_mutation", "")) == "0" or manifest.get("active_catalog_mutation", None) == 0, "No active catalog mutation in Phase 9"),
        ]
        for gate, ok, detail in checks:
            gate_rows.append({"GATE": gate, "STATUS": "PASS" if ok else "FAIL", "DETAIL": detail})
            if not ok:
                failures += 1

        messages = str(manifest.get("messages", status_value(p9, "MESSAGES", "0")))
        text_rows = str(manifest.get("text_rows", status_value(p9, "TEXT_ROWS", "0")))
        locales = ";".join(manifest.get("locales", [])) if isinstance(manifest.get("locales"), list) else status_value(p9, "LOCALES", "")
        validation_issues = str(manifest.get("validation_issues", status_value(p9, "VALIDATION_ISSUES", "0")))

        status = STATUS_GREEN if failures == 0 else "MESSAGE_CATALOG_PHASE10_CANDIDATE_DBF_EXECUTION_PLAN_BLOCKED"

    # Add explicit authorization gates.
    gate_rows.append({
        "GATE": "CANDIDATE_DBF_EXECUTION_NOT_AUTHORIZED",
        "STATUS": "PASS",
        "DETAIL": "Phase 10 is execution-plan-only; no candidate DBF execution performed.",
    })
    gate_rows.append({
        "GATE": "ACTIVE_PROMOTION_NOT_AUTHORIZED",
        "STATUS": "PASS",
        "DETAIL": "No active catalog replacement/promotion authorized.",
    })

    # Status summary
    status_rows = [{
        "STATUS": status,
        "MESSAGES": messages,
        "TEXT_ROWS": text_rows,
        "LOCALES": locales,
        "VALIDATION_ISSUES": validation_issues,
        "CANDIDATE_DBF_EXECUTION_AUTHORIZED": 0,
        "ACTIVE_PROMOTION_AUTHORIZED": 0,
        "NEXT_GATE": NEXT_GATE,
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }]
    write_csv(out / "message_catalog_phase10_status_summary_v1.csv", status_rows,
              ["STATUS", "MESSAGES", "TEXT_ROWS", "LOCALES", "VALIDATION_ISSUES",
               "CANDIDATE_DBF_EXECUTION_AUTHORIZED", "ACTIVE_PROMOTION_AUTHORIZED",
               "NEXT_GATE", "REPORT_TIMESTAMP_UTC"])

    # Execution plan rows
    execution_rows = [
        {"STEP": 1, "ACTION": "VERIFY_PHASE9_CANDIDATE_ARTIFACTS", "INPUT": "candidate_manifest_v1.json + Phase 9 import inputs", "OUTPUT": "candidate artifact integrity report", "EXECUTE_IN_PHASE10": 0, "NOTES": "Plan only."},
        {"STEP": 2, "ACTION": "CREATE_INACTIVE_CANDIDATE_DIRECTORIES", "INPUT": "Phase 8 path plan", "OUTPUT": "candidate dbf/index/lmdb directories", "EXECUTE_IN_PHASE10": 0, "NOTES": "Phase 11 candidate execution only if authorized."},
        {"STEP": 3, "ACTION": "CREATE_INACTIVE_DBF_TABLES", "INPUT": "Phase 8 DBF schema plan", "OUTPUT": "SYSTEM_MESSAGES.dbf and SYSTEM_MESSAGE_TEXT.dbf in inactive candidate path", "EXECUTE_IN_PHASE10": 0, "NOTES": "No active catalog path."},
        {"STEP": 4, "ACTION": "IMPORT_CANDIDATE_ROWS", "INPUT": "Phase 9 candidate import CSVs", "OUTPUT": "12 SYSTEM_MESSAGES rows and 60 SYSTEM_MESSAGE_TEXT rows", "EXECUTE_IN_PHASE10": 0, "NOTES": "Import only into inactive candidate DBFs."},
        {"STEP": 5, "ACTION": "CREATE_CDX_TAGS", "INPUT": "Phase 8 index/tag plan", "OUTPUT": "candidate-only CDX tags", "EXECUTE_IN_PHASE10": 0, "NOTES": "No active CDX/index mutation."},
        {"STEP": 6, "ACTION": "OPTIONAL_BUILD_LMDB", "INPUT": "candidate DBF/CDX only", "OUTPUT": "candidate-only LMDB environment", "EXECUTE_IN_PHASE10": 0, "NOTES": "Optional and gated; prior Data Dictionary evidence says CDX/tag prerequisites matter."},
        {"STEP": 7, "ACTION": "READBACK_VALIDATE_CANDIDATE", "INPUT": "candidate DBF/CDX/LMDB", "OUTPUT": "counts, tag checks, text-hash checks, locale coverage report", "EXECUTE_IN_PHASE10": 0, "NOTES": "Candidate proof before any promotion decision."},
        {"STEP": 8, "ACTION": "HOLD_FOR_PROMOTION_DECISION", "INPUT": "candidate readback reports", "OUTPUT": "future promotion/no-promotion decision", "EXECUTE_IN_PHASE10": 0, "NOTES": "Promotion is explicitly out of scope."},
    ]
    write_csv(out / "message_catalog_phase10_candidate_dbf_execution_plan_v1.csv", execution_rows,
              ["STEP", "ACTION", "INPUT", "OUTPUT", "EXECUTE_IN_PHASE10", "NOTES"])

    # DTS plan rows
    dts_rows = [
        {"SCRIPT": "MESSAGE_CATALOG_PHASE11_CREATE_INACTIVE_CANDIDATE_TABLES.dts", "PURPOSE": "Create candidate-only SYSTEM_MESSAGES and SYSTEM_MESSAGE_TEXT DBFs", "USES_PHASE9_TEMPLATE": 1, "EXECUTE_IN_PHASE10": 0, "BOUNDARY": "inactive candidate only"},
        {"SCRIPT": "MESSAGE_CATALOG_PHASE11_IMPORT_CANDIDATE_ROWS.dts", "PURPOSE": "Import Phase 9 CSV rows into inactive candidate DBFs", "USES_PHASE9_TEMPLATE": 0, "EXECUTE_IN_PHASE10": 0, "BOUNDARY": "inactive candidate only"},
        {"SCRIPT": "MESSAGE_CATALOG_PHASE11_CREATE_CANDIDATE_TAGS.dts", "PURPOSE": "Create candidate-only CDX tags from Phase 8 tag plan", "USES_PHASE9_TEMPLATE": 0, "EXECUTE_IN_PHASE10": 0, "BOUNDARY": "inactive candidate only"},
        {"SCRIPT": "MESSAGE_CATALOG_PHASE11_READBACK_VALIDATE_CANDIDATE.dts", "PURPOSE": "Runtime readback/count/tag smoke for candidate DBFs", "USES_PHASE9_TEMPLATE": 0, "EXECUTE_IN_PHASE10": 0, "BOUNDARY": "read-only candidate validation"},
    ]
    write_csv(out / "message_catalog_phase10_candidate_dts_plan_v1.csv", dts_rows,
              ["SCRIPT", "PURPOSE", "USES_PHASE9_TEMPLATE", "EXECUTE_IN_PHASE10", "BOUNDARY"])

    # Readback validation plan
    readback_rows = [
        {"CHECK": "SYSTEM_MESSAGES_COUNT", "EXPECTED": messages, "SOURCE": "phase9 manifest", "FAILS_IF": "count mismatch"},
        {"CHECK": "SYSTEM_MESSAGE_TEXT_COUNT", "EXPECTED": text_rows, "SOURCE": "phase9 manifest", "FAILS_IF": "count mismatch"},
        {"CHECK": "LOCALE_COVERAGE", "EXPECTED": locales, "SOURCE": "phase9 manifest", "FAILS_IF": "missing locale per message"},
        {"CHECK": "SYMBOL_UNIQUENESS", "EXPECTED": "unique", "SOURCE": "SYSTEM_MESSAGES", "FAILS_IF": "duplicate SYMBOL"},
        {"CHECK": "MSGID_UNIQUENESS", "EXPECTED": "unique", "SOURCE": "SYSTEM_MESSAGES", "FAILS_IF": "duplicate MSGID"},
        {"CHECK": "MSGID_LOCALE_UNIQUENESS", "EXPECTED": "unique", "SOURCE": "SYSTEM_MESSAGE_TEXT", "FAILS_IF": "duplicate MSGID+LOCALE"},
        {"CHECK": "PLACEHOLDER_PARITY", "EXPECTED": "pass", "SOURCE": "Phase 6 validation rules", "FAILS_IF": "locale template omits required placeholder"},
        {"CHECK": "TEXT_HASH_PARITY", "EXPECTED": "pass", "SOURCE": "Phase 9 candidate import rows", "FAILS_IF": "TEXT hash mismatch after import/readback"},
    ]
    write_csv(out / "message_catalog_phase10_readback_validation_plan_v1.csv", readback_rows,
              ["CHECK", "EXPECTED", "SOURCE", "FAILS_IF"])

    write_csv(out / "message_catalog_phase10_gate_check_v1.csv", gate_rows, ["GATE", "STATUS", "DETAIL"])

    boundary_rows = [
        {"PROTECTED_SYSTEM": "DBF_CATALOGS", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Phase 10 plans candidate DBF execution only; no DBF files created or opened for write."},
        {"PROTECTED_SYSTEM": "CDX_INDEXES", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CDX/index files created or rebuilt."},
        {"PROTECTED_SYSTEM": "LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No LMDB environment created or rebuilt."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No HELP DATA rebuild or mutation."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CMDHELPCHK mutation."},
        {"PROTECTED_SYSTEM": "SOURCE_MINING", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No source-mining mutation."},
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No source files edited by this script."},
        {"PROTECTED_SYSTEM": "RUNTIME_EXECUTION", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No DotTalk++ runtime execution required."},
        {"PROTECTED_SYSTEM": "CATALOG_PROMOTION", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active catalog promotion authorized or performed."},
    ]
    write_csv(out / "message_catalog_phase10_boundary_ledger_v1.csv", boundary_rows,
              ["PROTECTED_SYSTEM", "MUTATION_ALLOWED", "OBSERVED_MUTATION", "DETAIL"])

    # Markdown summary
    md = f"""# Message Catalog Phase 10 Candidate DBF Execution Plan

Status: `{status}`

Phase 10 is an execution plan only. It prepares the Phase 11 inactive-candidate
DBF execution lane but performs no DBF/CDX/LMDB creation and no active catalog
promotion.

## Counts

- Messages: {messages}
- Text rows: {text_rows}
- Locales: {locales}
- Validation issues: {validation_issues}

## Next gate

`{NEXT_GATE}`

## Boundary

No DBF writes, no CDX/index creation, no LMDB creation, no HELP DATA mutation,
no CMDHELPCHK mutation, no source-mining mutation, no source edits, no runtime
execution, and no active catalog promotion occurred in Phase 10.
"""
    (out / "MESSAGE_CATALOG_PHASE10_CANDIDATE_DBF_EXECUTION_PLAN_REPORT.md").write_text(md, encoding="utf-8")

    print(status)
    print(f"  messages: {messages}")
    print(f"  text rows: {text_rows}")
    print(f"  locales: {locales.replace(';', ', ')}")
    print(f"  validation issues: {validation_issues}")
    print("  candidate dbf execution authorized: 0")
    print("  active promotion authorized: 0")
    print(f"  reports: {out}")
    return 0 if status == STATUS_GREEN else 2

if __name__ == "__main__":
    raise SystemExit(main())
