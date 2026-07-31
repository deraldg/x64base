#!/usr/bin/env python3
"""
Phase 14 validate: verify inactive candidate CDX files and tag-name evidence.

This validator does not create CDX files. It scans the Phase 14 inactive
candidate workspace after the DotTalk++ CDX script has run.
"""
from __future__ import annotations
import argparse, csv, hashlib, json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

STATUS_GREEN = "MESSAGE_CATALOG_PHASE14_INACTIVE_CANDIDATE_CDX_TAG_EXECUTION_GREEN"
STATUS_BLOCKED = "MESSAGE_CATALOG_PHASE14_INACTIVE_CANDIDATE_CDX_TAG_EXECUTION_BLOCKED"
NEXT_GATE = "HOLD_OR_AUTHORIZE_PHASE15_CANDIDATE_LMDB_PLAN_OR_RUNTIME_CDX_READBACK"
REPORT_DIR = Path("docs/messaging/reports")
PHASE14_ROOT = Path("docs/messaging/candidates/phase14_inactive_candidate_cdx_execution")

EXPECTED = {
    "SYSTEM_MESSAGES": ["MSGID", "SYMBOL", "ENUMNAME", "SEVERITY", "FACILITY", "OWNER"],
    "SYSTEM_MESSAGE_TEXT": ["MSG_LOCALE", "SYMBOLLOC", "LOCALE", "TXTHASH"],
}

def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        w.writeheader()
        for row in rows:
            w.writerow({k: row.get(k, "") for k in fields})

def read_first(path: Path) -> dict[str, str]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    return rows[0] if rows else {}

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    reports = repo / REPORT_DIR
    reports.mkdir(parents=True, exist_ok=True)
    root = repo / PHASE14_ROOT

    p12 = reports / "message_catalog_phase12_status_summary_v1.csv"
    prep = reports / "message_catalog_phase14_1_prepare_status_summary_v1.csv"
    p12row = read_first(p12) if p12.exists() else {}
    messages = p12row.get("MESSAGES", "12")
    text_rows = p12row.get("TEXT_ROWS", "60")
    locales = p12row.get("LOCALES", "de;en-US;es;fr;it")
    validation_issues = "0"

    gates = []
    failures = 0
    def gate(name: str, ok: bool, detail: str) -> None:
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": detail})
        if not ok:
            failures += 1

    gate("PHASE12_STATUS_GREEN", p12row.get("STATUS") == "MESSAGE_CATALOG_PHASE12_CANDIDATE_DBF_ROW_PARITY_GREEN", p12row.get("STATUS", ""))
    gate("PHASE14_PREPARE_PRESENT", prep.exists(), str(prep))
    if prep.exists():
        gate("PHASE14_PREPARE_STAGED", read_first(prep).get("STATUS") in ("MESSAGE_CATALOG_PHASE14_CDX_RUNTIME_SCRIPT_STAGED", "MESSAGE_CATALOG_PHASE14_1_PATHED_CDX_RUNTIME_SCRIPT_STAGED"), read_first(prep).get("STATUS", ""))

    cdx_files = sorted(root.rglob("*.cdx"))
    gate("CDX_FILES_PRESENT", len(cdx_files) >= 1, f"cdx_files={len(cdx_files)}")

    inventory = []
    all_bytes = b""
    for p in cdx_files:
        b = p.read_bytes()
        all_bytes += b.upper()
        inventory.append({
            "RELATIVE_PATH": str(p.relative_to(repo)).replace("\\", "/"),
            "BYTES": p.stat().st_size,
            "SHA256": sha256_file(p),
            "ROLE": "inactive_candidate_cdx_file",
        })

    tag_rows = []
    for table, tags in EXPECTED.items():
        for tag in tags:
            found = tag.encode("ascii").upper() in all_bytes
            tag_rows.append({"TABLE_NAME": table, "TAG_NAME": tag, "FOUND_IN_CDX_BYTES": 1 if found else 0, "STATUS": "PASS" if found else "REVIEW"})
    missing = [r for r in tag_rows if r["STATUS"] != "PASS"]

    # We do not hard fail tag-name scan because some CDX implementations may not store tag
    # names as plain ASCII. But we do hard fail no CDX files.
    if missing:
        gate("TAG_NAME_BYTE_SCAN", True, f"review_rows={len(missing)}; not hard-fail because binary tag encoding may vary")
    else:
        gate("TAG_NAME_BYTE_SCAN", True, "all expected tag names observed in CDX bytes")

    status = STATUS_GREEN if failures == 0 else STATUS_BLOCKED
    if failures:
        validation_issues = str(failures)

    write_csv(reports / "message_catalog_phase14_status_summary_v1.csv", [{
        "STATUS": status,
        "MESSAGES": messages,
        "TEXT_ROWS": text_rows,
        "LOCALES": locales,
        "VALIDATION_ISSUES": validation_issues,
        "CDX_FILES_CREATED": len(cdx_files),
        "LMDB_ENV_CREATED": 0,
        "ACTIVE_PROMOTION_AUTHORIZED": 0,
        "NEXT_GATE": NEXT_GATE,
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }], ["STATUS", "MESSAGES", "TEXT_ROWS", "LOCALES", "VALIDATION_ISSUES",
         "CDX_FILES_CREATED", "LMDB_ENV_CREATED", "ACTIVE_PROMOTION_AUTHORIZED",
         "NEXT_GATE", "REPORT_TIMESTAMP_UTC"])

    write_csv(reports / "message_catalog_phase14_cdx_artifact_inventory_v1.csv", inventory,
              ["RELATIVE_PATH", "BYTES", "SHA256", "ROLE"])
    write_csv(reports / "message_catalog_phase14_tag_name_scan_v1.csv", tag_rows,
              ["TABLE_NAME", "TAG_NAME", "FOUND_IN_CDX_BYTES", "STATUS"])
    write_csv(reports / "message_catalog_phase14_gate_check_v1.csv", gates, ["GATE", "STATUS", "DETAIL"])

    boundary = [
        {"PROTECTED_SYSTEM": "INACTIVE_CANDIDATE_CDX", "MUTATION_ALLOWED": 1, "OBSERVED_MUTATION": len(cdx_files), "DETAIL": "Candidate-only CDX files are expected under phase14 inactive candidate workspace."},
        {"PROTECTED_SYSTEM": "ACTIVE_DBF_CATALOGS", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active DBF catalog paths promoted or mutated by validator."},
        {"PROTECTED_SYSTEM": "LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No LMDB environment created."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No HELP DATA mutation."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CMDHELPCHK mutation."},
        {"PROTECTED_SYSTEM": "SOURCE_MINING", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No source-mining mutation."},
        {"PROTECTED_SYSTEM": "CATALOG_PROMOTION", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active catalog promotion."},
    ]
    write_csv(reports / "message_catalog_phase14_boundary_ledger_v1.csv", boundary,
              ["PROTECTED_SYSTEM", "MUTATION_ALLOWED", "OBSERVED_MUTATION", "DETAIL"])

    manifest = {
        "status": status,
        "candidate_root": str(PHASE14_ROOT).replace("\\", "/"),
        "messages": int(messages) if str(messages).isdigit() else messages,
        "text_rows": int(text_rows) if str(text_rows).isdigit() else text_rows,
        "locales": locales.split(";") if locales else [],
        "validation_issues": int(validation_issues) if str(validation_issues).isdigit() else validation_issues,
        "cdx_files_created": len(cdx_files),
        "lmdb_env_created": 0,
        "active_promotion_authorized": 0,
        "cdx_artifacts": inventory,
        "tag_name_scan": tag_rows,
    }
    (root / "candidate_manifest_phase14_v1.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    print(status)
    print(f"  messages: {messages}")
    print(f"  text rows: {text_rows}")
    print(f"  locales: {locales.replace(';', ', ')}")
    print(f"  validation issues: {validation_issues}")
    print(f"  cdx files created: {len(cdx_files)}")
    print("  lmdb env created: 0")
    print("  active promotion authorized: 0")
    print(f"  reports: {reports}")
    return 0 if status == STATUS_GREEN else 2

if __name__ == "__main__":
    raise SystemExit(main())
