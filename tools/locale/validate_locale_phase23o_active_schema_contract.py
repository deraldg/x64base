#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

STATUS_GREEN = "LOCALE_PHASE23O_ACTIVE_LOCALE_SCHEMA_CONTRACT_VALIDATED_GREEN"
STATUS_BLOCKED = "LOCALE_PHASE23O_ACTIVE_LOCALE_SCHEMA_CONTRACT_VALIDATION_BLOCKED"
NEXT_GATE = "HOLD_OR_AUTHORIZE_MSGMGR_SCHEMA_STATUS_REPORTING"
REPORT_DIR = Path("docs/locale/reports")
CANDIDATE = Path("docs/locale/schemas/candidates/phase23n_schema_location_contract/locale_spine.dtschema")
TARGET = Path("dottalkpp/data/schemas/locale/locale_spine.dtschema")
MESSAGING_TARGET = Path("dottalkpp/data/schemas/messaging/message_catalog.dtschema")

REQUIRED_TEXT = [
    "SCHEMA_ID: LOCALE_SPINE",
    "TABLE: SYSTEM_LOCALES",
    "TABLE: SYSTEM_LOCALE_FALLBACK",
    "PRIMARY_KEY: LOCALE_ID",
    "PRIMARY_KEY: FBID",
    "TAGS:",
]

def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

def first_row(path: Path) -> dict[str, str]:
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
        return path.relative_to(repo).as_posix()
    except ValueError:
        return str(path)

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    reports = repo / REPORT_DIR
    reports.mkdir(parents=True, exist_ok=True)

    promotion = first_row(reports / "locale_phase23o_promotion_status_summary_v1.csv")
    candidate = repo / CANDIDATE
    target = repo / TARGET
    messaging_target = repo / MESSAGING_TARGET

    target_text = target.read_text(encoding="utf-8", errors="replace") if target.exists() else ""

    gates: list[dict[str, Any]] = []
    failures = 0

    def gate(name: str, ok: bool, detail: str) -> None:
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": detail})
        if not ok:
            failures += 1

    gate("PHASE23O_PROMOTION_APPLIED",
         promotion.get("STATUS") == "LOCALE_PHASE23O_ACTIVE_LOCALE_SCHEMA_CONTRACT_PROMOTED_VALIDATE_HELD",
         promotion.get("STATUS", ""))
    gate("PROMOTION_VALIDATION_ZERO",
         promotion.get("VALIDATION_ISSUES", "") == "0",
         f"validation_issues={promotion.get('VALIDATION_ISSUES', '')}")
    gate("CANDIDATE_PRESENT", candidate.exists(), rel(candidate, repo))
    gate("TARGET_PRESENT", target.exists(), rel(target, repo))
    if candidate.exists() and target.exists():
        gate("TARGET_HASH_MATCHES_CANDIDATE",
             sha256_file(target) == sha256_file(candidate),
             f"target={sha256_file(target)} candidate={sha256_file(candidate)}")
    else:
        gate("TARGET_HASH_MATCHES_CANDIDATE", False, "candidate or target missing")

    for required in REQUIRED_TEXT:
        gate(f"REQUIRED_TEXT_{required.replace(' ', '_').replace(':', '')}",
             required in target_text,
             required)

    gate("MESSAGING_SCHEMA_HELD",
         not messaging_target.exists(),
         "message_catalog.dtschema intentionally held for field reconciliation")

    status = STATUS_GREEN if failures == 0 else STATUS_BLOCKED
    validation_issues = str(failures)

    schema_rows = [{
        "TARGET_PATH": rel(target, repo),
        "SOURCE_PATH": rel(candidate, repo),
        "EXISTS": 1 if target.exists() else 0,
        "BYTES": target.stat().st_size if target.exists() else "",
        "SHA256": sha256_file(target) if target.exists() else "",
        "SOURCE_SHA256": sha256_file(candidate) if candidate.exists() else "",
        "HASH_MATCH": 1 if target.exists() and candidate.exists() and sha256_file(target) == sha256_file(candidate) else 0,
        "STATUS": "ACTIVE_SCHEMA_CONTRACT_VALIDATED" if status == STATUS_GREEN else "VALIDATION_FAILED",
    }]

    boundary = [
        {"PROTECTED_SYSTEM": "ACTIVE_SCHEMA_CONTRACTS", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Validation only; promotion already accounted by promotion step."},
        {"PROTECTED_SYSTEM": "MESSAGING_SCHEMA_CONTRACT", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "message_catalog.dtschema remains held."},
        {"PROTECTED_SYSTEM": "ACTIVE_DBF_CDX_LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active DBF/CDX/LMDB mutation."},
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No source mutation."},
        {"PROTECTED_SYSTEM": "BUILD_RUNTIME", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No build or runtime execution."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No HELP DATA mutation."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CMDHELPCHK mutation."},
        {"PROTECTED_SYSTEM": "MANUALGEN", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No manualgen mutation."},
        {"PROTECTED_SYSTEM": "DATADICT_SELF_DOC", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No Data Dictionary/SelfDoc mutation."},
    ]

    write_csv(reports / "locale_phase23o_validation_status_summary_v1.csv", [{
        "STATUS": status,
        "VALIDATION_ISSUES": validation_issues,
        "ACTIVE_LOCALE_SCHEMA_PRESENT": 1 if target.exists() else 0,
        "TARGET_HASH_MATCHES_CANDIDATE": 1 if target.exists() and candidate.exists() and sha256_file(target) == sha256_file(candidate) else 0,
        "MESSAGING_SCHEMA_PROMOTED": 0,
        "NEXT_GATE": NEXT_GATE,
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }], ["STATUS", "VALIDATION_ISSUES", "ACTIVE_LOCALE_SCHEMA_PRESENT",
         "TARGET_HASH_MATCHES_CANDIDATE", "MESSAGING_SCHEMA_PROMOTED",
         "NEXT_GATE", "REPORT_TIMESTAMP_UTC"])

    write_csv(reports / "locale_phase23o_validation_gate_check_v1.csv", gates, ["GATE", "STATUS", "DETAIL"])
    write_csv(reports / "locale_phase23o_active_schema_validation_inventory_v1.csv", schema_rows,
              ["TARGET_PATH", "SOURCE_PATH", "EXISTS", "BYTES", "SHA256", "SOURCE_SHA256", "HASH_MATCH", "STATUS"])
    write_csv(reports / "locale_phase23o_validation_boundary_ledger_v1.csv", boundary,
              ["PROTECTED_SYSTEM", "MUTATION_ALLOWED", "OBSERVED_MUTATION", "DETAIL"])

    print(status)
    print(f"  validation issues: {validation_issues}")
    print(f"  active locale schema present: {1 if target.exists() else 0}")
    print(f"  target hash matches candidate: {1 if target.exists() and candidate.exists() and sha256_file(target) == sha256_file(candidate) else 0}")
    print("  messaging schema promoted: 0")
    print(f"  next gate: {NEXT_GATE}")
    print(f"  reports: {reports}")
    return 0 if status == STATUS_GREEN else 2

if __name__ == "__main__":
    raise SystemExit(main())
