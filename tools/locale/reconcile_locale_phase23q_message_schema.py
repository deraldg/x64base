#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import struct
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

STATUS_GREEN = "LOCALE_PHASE23Q_MESSAGE_CATALOG_SCHEMA_RECONCILIATION_GREEN_REPORT_ONLY"
STATUS_BLOCKED = "LOCALE_PHASE23Q_MESSAGE_CATALOG_SCHEMA_RECONCILIATION_BLOCKED"
NEXT_GATE = "HOLD_OR_AUTHORIZE_PHASE23R_MESSAGE_CATALOG_ACTIVE_SCHEMA_PROMOTION_PLAN"
REPORT_DIR = Path("docs/locale/reports")

ACTIVE_TABLES = [
    {
        "TABLE": "SYSTEM_MESSAGES",
        "DBF": "dottalkpp/data/messaging/SYSTEM_MESSAGES.dbf",
        "CDX": "dottalkpp/data/indexes/messaging/SYSTEM_MESSAGES.cdx",
        "LMDB": "dottalkpp/data/lmdb/messaging/SYSTEM_MESSAGES.cdx.d/data.mdb",
        "ROLE": "stable message identity",
    },
    {
        "TABLE": "SYSTEM_MESSAGE_TEXT",
        "DBF": "dottalkpp/data/messaging/SYSTEM_MESSAGE_TEXT.dbf",
        "CDX": "dottalkpp/data/indexes/messaging/SYSTEM_MESSAGE_TEXT.cdx",
        "LMDB": "dottalkpp/data/lmdb/messaging/SYSTEM_MESSAGE_TEXT.cdx.d/data.mdb",
        "ROLE": "localized message text rows by locale",
    },
]

EXPECTED_PHASE22_HINTS = {
    "messages": "12",
    "text_rows": "60",
    "locales": "de;en-US;es;fr;it",
}

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

def parse_dbf_header(path: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    meta = {
        "DBF_PATH": str(path),
        "PARSE_STATUS": "MISSING",
        "DBF_VERSION": "",
        "RECORD_COUNT": "",
        "HEADER_LENGTH": "",
        "RECORD_LENGTH": "",
        "FIELD_COUNT": "",
    }
    fields: list[dict[str, Any]] = []
    if not path.exists():
        return meta, fields

    data = path.read_bytes()
    if len(data) < 32:
        meta["PARSE_STATUS"] = "TOO_SHORT"
        return meta, fields

    version = data[0]
    rec_count = struct.unpack("<I", data[4:8])[0]
    header_len = struct.unpack("<H", data[8:10])[0]
    rec_len = struct.unpack("<H", data[10:12])[0]

    meta.update({
        "PARSE_STATUS": "PARSED",
        "DBF_VERSION": f"0x{version:02X}",
        "RECORD_COUNT": rec_count,
        "HEADER_LENGTH": header_len,
        "RECORD_LENGTH": rec_len,
    })

    pos = 32
    ordinal = 0
    while pos + 32 <= len(data) and pos < header_len:
        desc = data[pos:pos+32]
        if desc[0] == 0x0D:
            break
        raw_name = desc[0:11].split(b"\x00", 1)[0]
        try:
            name = raw_name.decode("ascii", errors="replace").strip()
        except Exception:
            name = raw_name.hex()
        try:
            ftype = chr(desc[11])
        except Exception:
            ftype = "?"
        flen = desc[16]
        fdec = desc[17]
        ordinal += 1
        fields.append({
            "TABLE": path.stem.upper(),
            "ORDINAL": ordinal,
            "DBF_DESCRIPTOR_NAME": name,
            "TYPE": ftype,
            "LENGTH": flen,
            "DECIMALS": fdec,
            "NOTE": "DBF descriptor token; x64 authoritative long metadata may be richer if present",
        })
        pos += 32

    meta["FIELD_COUNT"] = len(fields)
    return meta, fields

def scan_schema_hints(repo: Path) -> list[dict[str, Any]]:
    roots = [
        repo / "docs/messaging",
        repo / "docs/locale",
        repo / "dottalkpp/data/schemas",
    ]
    patterns = [
        "SYSTEM_MESSAGES",
        "SYSTEM_MESSAGE_TEXT",
        "MESSAGE_ID",
        "SYMBOL",
        "LOCALE_ID",
        "MESSAGE_TEXT",
        "TEXT",
        "SEVERITY",
        "CATEGORY",
    ]
    rows: list[dict[str, Any]] = []
    for root in roots:
        if not root.exists():
            continue
        for p in sorted(root.rglob("*")):
            if not p.is_file():
                continue
            if p.suffix.lower() not in {".md", ".csv", ".json", ".txt", ".dtschema", ".dts"}:
                continue
            try:
                lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
            except Exception:
                continue
            for i, line in enumerate(lines, start=1):
                u = line.upper()
                for pat in patterns:
                    if pat in u:
                        rows.append({
                            "SOURCE_PATH": rel(p, repo),
                            "LINE_NO": i,
                            "MATCH_TERM": pat,
                            "LINE_TEXT": line.strip()[:240],
                        })
                        break
                if len(rows) >= 500:
                    return rows
    return rows

def schema_field_block(table: str, fields: list[dict[str, Any]]) -> str:
    lines = [f"TABLE: {table}", "FIELDS:"]
    table_fields = [f for f in fields if f.get("TABLE") == table]
    for f in table_fields:
        lines.append(f"  {f['DBF_DESCRIPTOR_NAME']}  TYPE={f['TYPE']} LEN={f['LENGTH']} DEC={f['DECIMALS']}")
    if not table_fields:
        lines.append("  FIELD_RECONCILIATION_REQUIRED")
    lines.append("")
    lines.append("TAG_RECONCILIATION: REQUIRED_FROM_CDX_OR_RUNTIME_PROOF")
    return "\n".join(lines)

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--accept-report-only-reconciliation", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    reports = repo / REPORT_DIR
    reports.mkdir(parents=True, exist_ok=True)

    phase23p = first_row(reports / "locale_phase23p_msgmgr_schema_status_validation_summary_v1.csv")
    latest = {}
    latest_path = reports / "locale_savepoint_latest_v1.json"
    if latest_path.exists():
        try:
            latest = json.loads(latest_path.read_text(encoding="utf-8"))
        except Exception:
            latest = {}

    gates: list[dict[str, Any]] = []
    failures = 0

    def gate(name: str, ok: bool, detail: str) -> None:
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": detail})
        if not ok:
            failures += 1

    def review(name: str, ok: bool, detail: str) -> None:
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "REVIEW", "DETAIL": detail})

    gate("OPERATOR_ACCEPTED_REPORT_ONLY_RECONCILIATION",
         args.accept_report_only_reconciliation,
         "requires --accept-report-only-reconciliation")
    gate("PHASE23P_SCHEMA_STATUS_GREEN",
         phase23p.get("STATUS") == "LOCALE_PHASE23P_MSGMGR_SCHEMA_STATUS_BUILD_SMOKE_GREEN",
         phase23p.get("STATUS", ""))
    gate("PHASE23P_VALIDATION_ZERO",
         phase23p.get("VALIDATION_ISSUES", "") == "0",
         f"validation_issues={phase23p.get('VALIDATION_ISSUES', '')}")
    review("LATEST_SAVEPOINT_IS_23P",
           latest.get("savepoint_id") == "LOC-023P-MSGMGR-SCHEMA-STATUS",
           f"latest_savepoint={latest.get('savepoint_id', '')}")

    artifact_rows: list[dict[str, Any]] = []
    dbf_meta_rows: list[dict[str, Any]] = []
    dbf_field_rows: list[dict[str, Any]] = []

    for item in ACTIVE_TABLES:
        for kind in ["DBF", "CDX", "LMDB"]:
            p = repo / item[kind]
            artifact_rows.append({
                "TABLE": item["TABLE"],
                "KIND": kind,
                "PATH": item[kind],
                "ROLE": item["ROLE"],
                "EXISTS": 1 if p.exists() else 0,
                "IS_FILE": 1 if p.is_file() else 0,
                "BYTES": p.stat().st_size if p.exists() and p.is_file() else "",
                "SHA256": sha256_file(p) if p.exists() and p.is_file() else "",
            })
            if kind == "DBF":
                gate(f"{item['TABLE']}_DBF_PRESENT", p.exists(), item[kind])
                meta, fields = parse_dbf_header(p)
                meta["TABLE"] = item["TABLE"]
                meta["PATH"] = item[kind]
                dbf_meta_rows.append(meta)
                dbf_field_rows.extend(fields)
                gate(f"{item['TABLE']}_DBF_HEADER_PARSED",
                     meta.get("PARSE_STATUS") == "PARSED",
                     f"parse_status={meta.get('PARSE_STATUS')}")
                gate(f"{item['TABLE']}_FIELDS_OBSERVED",
                     int(meta.get("FIELD_COUNT") or 0) > 0,
                     f"field_count={meta.get('FIELD_COUNT')}")
            else:
                review(f"{item['TABLE']}_{kind}_PRESENT",
                       p.exists(),
                       item[kind])

    # Phase 22 report hints; accept any available prior summary.
    message_report_candidates = [
        repo / "docs/messaging/reports/message_catalog_phase22i_status_summary_v1.csv",
        repo / "docs/messaging/reports/message_catalog_phase22j_status_summary_v1.csv",
        repo / "docs/messaging/reports/message_catalog_phase22h_status_summary_v1.csv",
        repo / "docs/messaging/reports/message_catalog_phase22g_status_summary_v1.csv",
    ]
    phase22_rows = []
    for p in message_report_candidates:
        row = first_row(p)
        if row:
            phase22_rows.append({
                "SOURCE_PATH": rel(p, repo),
                "STATUS": row.get("STATUS", ""),
                "MESSAGES": row.get("MESSAGES", row.get("messages", "")),
                "TEXT_ROWS": row.get("TEXT_ROWS", row.get("text_rows", "")),
                "LOCALES": row.get("LOCALES", row.get("locales", "")),
                "VALIDATION_ISSUES": row.get("VALIDATION_ISSUES", row.get("validation_issues", "")),
            })

    review("PHASE22_MESSAGE_REPORTS_FOUND", len(phase22_rows) > 0, f"phase22 report rows={len(phase22_rows)}")

    hint_rows = scan_schema_hints(repo)

    # Candidate schema draft from active DBF header fields.
    draft_dir = repo / "docs/locale/schemas/candidates/phase23q_message_catalog_reconciliation"
    draft_dir.mkdir(parents=True, exist_ok=True)
    draft_path = draft_dir / "message_catalog.dtschema"
    draft_text = f"""# message_catalog.dtschema
# Phase 23Q candidate schema reconciliation draft.
# Target active path after a later authorized promotion:
#   dottalkpp/data/schemas/messaging/message_catalog.dtschema
#
# Reconciliation source:
#   active Messaging DBF headers under dottalkpp/data/messaging
#   phase 22 Messaging runtime proof reports
#
# Status:
#   CANDIDATE_RECONCILED_FROM_ACTIVE_DBF_HEADER
#   CDX_TAG_RECONCILIATION_REQUIRED_BEFORE_ACTIVE_PROMOTION

SCHEMA_ID: MESSAGE_CATALOG
SCHEMA_STATUS: CANDIDATE_RECONCILED_FROM_ACTIVE_DBF_HEADER
ACTIVE_SCHEMA_TARGET: dottalkpp/data/schemas/messaging/message_catalog.dtschema

{schema_field_block("SYSTEM_MESSAGES", dbf_field_rows)}

{schema_field_block("SYSTEM_MESSAGE_TEXT", dbf_field_rows)}

EXPECTED_RUNTIME_PROOF:
  MESSAGE_COUNT: {EXPECTED_PHASE22_HINTS["messages"]}
  TEXT_ROW_COUNT: {EXPECTED_PHASE22_HINTS["text_rows"]}
  LOCALES: {EXPECTED_PHASE22_HINTS["locales"]}

PROMOTION_REQUIREMENTS:
  ACTIVE_DBF_HEADERS_PARSED: required
  CDX_TAGS_RECONCILED: required
  RUNTIME_PROVIDER_STATUS_GREEN: required
  NO_ACTIVE_DBF_CDX_LMDB_MUTATION: required
"""
    draft_path.write_text(draft_text, encoding="utf-8")

    candidate_rows = [{
        "DRAFT_PATH": rel(draft_path, repo),
        "TARGET_PATH": "dottalkpp/data/schemas/messaging/message_catalog.dtschema",
        "SCHEMA_ID": "MESSAGE_CATALOG",
        "STATUS": "CANDIDATE_RECONCILED_FROM_ACTIVE_DBF_HEADER_TAGS_PENDING",
        "BYTES": draft_path.stat().st_size,
        "SHA256": sha256_file(draft_path),
    }]

    promotion_plan = [
        {
            "STEP": 1,
            "ACTION": "REVIEW_DBF_HEADER_FIELD_ROWS",
            "DETAIL": "Review DBF descriptor fields for SYSTEM_MESSAGES and SYSTEM_MESSAGE_TEXT.",
        },
        {
            "STEP": 2,
            "ACTION": "RECONCILE_CDX_TAGS",
            "DETAIL": "Use runtime readback/source reports to confirm index tag names before active schema promotion.",
        },
        {
            "STEP": 3,
            "ACTION": "PROMOTE_MESSAGE_CATALOG_SCHEMA_ONLY_AFTER_TAG_REVIEW",
            "DETAIL": "Create dottalkpp/data/schemas/messaging/message_catalog.dtschema in a later guarded phase.",
        },
        {
            "STEP": 4,
            "ACTION": "UPDATE_MSGMGR_STATUS_AFTER_PROMOTION",
            "DETAIL": "Change MSGMGR STATUS from messaging schema held to active path only after promotion is validated.",
        },
    ]

    boundary = [
        {"PROTECTED_SYSTEM": "ACTIVE_SCHEMA_CONTRACTS", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active schema promotion in Phase 23Q."},
        {"PROTECTED_SYSTEM": "DOCS_CANDIDATE_SCHEMA_DRAFTS", "MUTATION_ALLOWED": 1, "OBSERVED_MUTATION": 1, "DETAIL": "Candidate Messaging schema draft created under docs/locale/schemas/candidates."},
        {"PROTECTED_SYSTEM": "ACTIVE_DBF_CDX_LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active DBF/CDX/LMDB mutation."},
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No source mutation."},
        {"PROTECTED_SYSTEM": "BUILD_RUNTIME", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No build/runtime execution."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No HELP DATA mutation."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CMDHELPCHK mutation."},
        {"PROTECTED_SYSTEM": "MANUALGEN", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No manualgen mutation."},
        {"PROTECTED_SYSTEM": "DATADICT_SELF_DOC", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No Data Dictionary/SelfDoc mutation."},
    ]

    status = STATUS_GREEN if failures == 0 else STATUS_BLOCKED
    validation_issues = str(failures)

    write_csv(reports / "locale_phase23q_message_schema_reconciliation_status_summary_v1.csv", [{
        "STATUS": status,
        "VALIDATION_ISSUES": validation_issues,
        "REPORT_ONLY_RECONCILIATION": 1,
        "ACTIVE_SCHEMA_MUTATION_AUTHORIZED": 0,
        "ACTIVE_SCHEMA_FILES_CREATED": 0,
        "CANDIDATE_SCHEMA_DRAFTS_CREATED": 1,
        "ACTIVE_MESSAGING_TABLES_RECONCILED": len([m for m in dbf_meta_rows if m.get("PARSE_STATUS") == "PARSED"]),
        "DBF_FIELD_ROWS": len(dbf_field_rows),
        "PHASE22_REPORT_ROWS": len(phase22_rows),
        "SCHEMA_HINT_ROWS": len(hint_rows),
        "NEXT_GATE": NEXT_GATE,
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }], ["STATUS", "VALIDATION_ISSUES", "REPORT_ONLY_RECONCILIATION",
         "ACTIVE_SCHEMA_MUTATION_AUTHORIZED", "ACTIVE_SCHEMA_FILES_CREATED",
         "CANDIDATE_SCHEMA_DRAFTS_CREATED", "ACTIVE_MESSAGING_TABLES_RECONCILED",
         "DBF_FIELD_ROWS", "PHASE22_REPORT_ROWS", "SCHEMA_HINT_ROWS",
         "NEXT_GATE", "REPORT_TIMESTAMP_UTC"])

    write_csv(reports / "locale_phase23q_message_schema_reconciliation_gate_check_v1.csv", gates, ["GATE", "STATUS", "DETAIL"])
    write_csv(reports / "locale_phase23q_active_messaging_artifact_inventory_v1.csv", artifact_rows,
              ["TABLE", "KIND", "PATH", "ROLE", "EXISTS", "IS_FILE", "BYTES", "SHA256"])
    write_csv(reports / "locale_phase23q_active_messaging_dbf_header_v1.csv", dbf_meta_rows,
              ["TABLE", "PATH", "DBF_PATH", "PARSE_STATUS", "DBF_VERSION", "RECORD_COUNT", "HEADER_LENGTH", "RECORD_LENGTH", "FIELD_COUNT"])
    write_csv(reports / "locale_phase23q_active_messaging_dbf_fields_v1.csv", dbf_field_rows,
              ["TABLE", "ORDINAL", "DBF_DESCRIPTOR_NAME", "TYPE", "LENGTH", "DECIMALS", "NOTE"])
    write_csv(reports / "locale_phase23q_phase22_message_report_hints_v1.csv", phase22_rows,
              ["SOURCE_PATH", "STATUS", "MESSAGES", "TEXT_ROWS", "LOCALES", "VALIDATION_ISSUES"])
    write_csv(reports / "locale_phase23q_schema_hint_scan_v1.csv", hint_rows,
              ["SOURCE_PATH", "LINE_NO", "MATCH_TERM", "LINE_TEXT"])
    write_csv(reports / "locale_phase23q_message_schema_candidate_draft_v1.csv", candidate_rows,
              ["DRAFT_PATH", "TARGET_PATH", "SCHEMA_ID", "STATUS", "BYTES", "SHA256"])
    write_csv(reports / "locale_phase23q_message_schema_promotion_plan_v1.csv", promotion_plan,
              ["STEP", "ACTION", "DETAIL"])
    write_csv(reports / "locale_phase23q_boundary_ledger_v1.csv", boundary,
              ["PROTECTED_SYSTEM", "MUTATION_ALLOWED", "OBSERVED_MUTATION", "DETAIL"])

    doc = repo / "docs/locale/LOCALE_PHASE23Q_MESSAGE_CATALOG_SCHEMA_RECONCILIATION.md"
    doc.parent.mkdir(parents=True, exist_ok=True)
    doc.write_text(f"""# Locale Phase 23Q — Message Catalog Schema Reconciliation

Status: `{status}`

Phase 23Q is report-only. It reconciles active Messaging DBF header fields for:

```text
SYSTEM_MESSAGES
SYSTEM_MESSAGE_TEXT
```

It creates a candidate schema draft under:

```text
docs/locale/schemas/candidates/phase23q_message_catalog_reconciliation/message_catalog.dtschema
```

It does not promote an active schema under `dottalkpp/data/schemas/messaging/`.
CDX tag reconciliation remains required before active promotion.

## Next gate

```text
{NEXT_GATE}
```
""", encoding="utf-8")

    print(status)
    print(f"  validation issues: {validation_issues}")
    print("  report-only reconciliation: 1")
    print("  active schema mutation authorized: 0")
    print("  active schema files created: 0")
    print("  candidate schema drafts created: 1")
    print(f"  active Messaging tables reconciled: {len([m for m in dbf_meta_rows if m.get('PARSE_STATUS') == 'PARSED'])}")
    print(f"  DBF field rows: {len(dbf_field_rows)}")
    print(f"  Phase 22 report rows: {len(phase22_rows)}")
    print(f"  schema hint rows: {len(hint_rows)}")
    print(f"  next gate: {NEXT_GATE}")
    print(f"  reports: {reports}")
    return 0 if status == STATUS_GREEN else 2

if __name__ == "__main__":
    raise SystemExit(main())
