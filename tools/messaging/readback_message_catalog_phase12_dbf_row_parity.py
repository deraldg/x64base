#!/usr/bin/env python3
"""
Phase 12: Candidate DBF row/memo parity readback for DotTalk++ Messaging catalog.

Reads the inactive candidate DBF/DBT files created in Phase 11 and compares
their row/memo content back to the Phase 9 candidate import CSVs.

No DBF/CDX/LMDB creation, no active catalog promotion, no HELP/CMDHELPCHK
mutation, no source-mining mutation, and no DotTalk++ runtime execution.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import struct
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

STATUS_GREEN = "MESSAGE_CATALOG_PHASE12_CANDIDATE_DBF_ROW_PARITY_GREEN"
STATUS_BLOCKED = "MESSAGE_CATALOG_PHASE12_CANDIDATE_DBF_ROW_PARITY_BLOCKED"
NEXT_GATE = "HOLD_OR_AUTHORIZE_PHASE13_CANDIDATE_CDX_TAG_PLAN"
REPORT_DIR = Path("docs/messaging/reports")
PHASE9_ROOT = Path("docs/messaging/candidates/phase9_inactive_candidate_dbf_staging")
PHASE11_ROOT = Path("docs/messaging/candidates/phase11_inactive_candidate_dbf_execution")

@dataclass
class DbfField:
    name: str
    ftype: str
    width: int
    decimals: int

def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

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

def sha256_text(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

def pick(row: dict[str, str], *names: str, default: str = "") -> str:
    for n in names:
        if n in row and row[n] != "":
            return row[n]
    return default

def transform_messages(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    return [{
        "MSGID": pick(r, "MSGID", "MESSAGE_ID"),
        "SYMBOL": pick(r, "SYMBOL"),
        "ENUMNAME": pick(r, "ENUMNAME", "ENUM_NAME"),
        "FACILITY": pick(r, "FACILITY", default="GLOBAL"),
        "OWNER": pick(r, "OWNER", "OWNER_SUBSYSTEM", default="GLOBAL"),
        "CATEGORY": pick(r, "CATEGORY", default="STATUS"),
        "SEVERITY": pick(r, "SEVERITY", default="INFO"),
        "STATUS": pick(r, "STATUS", default="ACTIVE"),
        "SRC": pick(r, "SRC", "SOURCE", default="PHASE6"),
        "NOTES": pick(r, "NOTES", default=""),
    } for r in rows]

def transform_text(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    for r in rows:
        text = pick(r, "TEXT", "TEXT_TEMPLATE")
        out.append({
            "MSGID": pick(r, "MSGID", "MESSAGE_ID"),
            "SYMBOL": pick(r, "SYMBOL"),
            "ENUMNAME": pick(r, "ENUMNAME", "ENUM_NAME"),
            "LOCALE": pick(r, "LOCALE"),
            "TEXT": text,
            "TXTHASH": pick(r, "TXTHASH", "TEXT_HASH", default=sha256_text(text)),
            "STATUS": pick(r, "STATUS", default="ACTIVE"),
            "SRC": pick(r, "SRC", "SOURCE", default="PHASE6"),
        })
    return out

def read_dbt_memo(dbt_path: Path, block: int) -> str:
    if block <= 0 or not dbt_path.exists():
        return ""
    block_size = 512
    with dbt_path.open("rb") as f:
        f.seek(block * block_size)
        chunks = []
        while True:
            b = f.read(block_size)
            if not b:
                break
            idx = b.find(b"\x1a")
            if idx >= 0:
                chunks.append(b[:idx])
                break
            chunks.append(b)
            if len(chunks) > 1024:
                break
    raw = b"".join(chunks).rstrip(b"\x00")
    return raw.decode("utf-8", errors="replace")

def parse_dbf(path: Path) -> tuple[dict[str, Any], list[DbfField], list[dict[str, str]]]:
    with path.open("rb") as f:
        header = f.read(32)
        if len(header) != 32:
            raise RuntimeError(f"short DBF header: {path}")
        version = header[0]
        records = struct.unpack("<I", header[4:8])[0]
        header_len = struct.unpack("<H", header[8:10])[0]
        record_len = struct.unpack("<H", header[10:12])[0]
        field_count = (header_len - 33) // 32

        fields: list[DbfField] = []
        for _ in range(field_count):
            desc = f.read(32)
            name = desc[0:11].split(b"\x00", 1)[0].decode("ascii", errors="replace").strip()
            ftype = chr(desc[11])
            width = desc[16]
            decimals = desc[17]
            fields.append(DbfField(name, ftype, width, decimals))

        term = f.read(1)
        if term != b"\x0d":
            raise RuntimeError(f"DBF field descriptor terminator missing: {path}")

        dbt_path = path.with_suffix(".dbt")
        rows: list[dict[str, str]] = []
        for _ in range(records):
            rec = f.read(record_len)
            if len(rec) != record_len:
                raise RuntimeError(f"short DBF record in {path}")
            deleted_flag = rec[0:1]
            if deleted_flag == b"*":
                continue
            pos = 1
            row: dict[str, str] = {}
            for field in fields:
                raw = rec[pos:pos + field.width]
                pos += field.width
                if field.ftype in ("C", "N"):
                    value = raw.decode("utf-8", errors="replace").strip()
                elif field.ftype == "M":
                    ptr_s = raw.decode("ascii", errors="replace").strip()
                    try:
                        ptr = int(ptr_s) if ptr_s else 0
                    except ValueError:
                        ptr = 0
                    value = read_dbt_memo(dbt_path, ptr)
                else:
                    value = raw.decode("utf-8", errors="replace").strip()
                row[field.name] = value
            rows.append(row)

    meta = {
        "TABLE_NAME": path.stem,
        "VERSION_HEX": hex(version),
        "RECORDS": records,
        "HEADER_LEN": header_len,
        "RECORD_LEN": record_len,
        "FIELD_COUNT": field_count,
        "HAS_MEMO": 1 if version in (0x83, 0x8b, 0xf5) else 0,
        "DBF_PATH": str(path),
        "DBF_SHA256": sha256_file(path),
        "DBT_PATH": str(path.with_suffix(".dbt")) if path.with_suffix(".dbt").exists() else "",
        "DBT_SHA256": sha256_file(path.with_suffix(".dbt")) if path.with_suffix(".dbt").exists() else "",
    }
    return meta, fields, rows

def compare_rows(table: str, expected: list[dict[str, str]], actual: list[dict[str, str]], key_fields: list[str]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    issue_count = 0

    def key(row: dict[str, str]) -> str:
        return "|".join(row.get(k, "") for k in key_fields)

    exp_map = {key(r): r for r in expected}
    act_map = {key(r): r for r in actual}

    for k in sorted(set(exp_map) | set(act_map)):
        er = exp_map.get(k)
        ar = act_map.get(k)
        if er is None:
            issue_count += 1
            rows.append({"TABLE_NAME": table, "ROW_KEY": k, "FIELD": "*ROW*", "STATUS": "EXTRA_ACTUAL", "EXPECTED": "", "ACTUAL": json.dumps(ar, ensure_ascii=False)})
            continue
        if ar is None:
            issue_count += 1
            rows.append({"TABLE_NAME": table, "ROW_KEY": k, "FIELD": "*ROW*", "STATUS": "MISSING_ACTUAL", "EXPECTED": json.dumps(er, ensure_ascii=False), "ACTUAL": ""})
            continue
        for field, ev in er.items():
            av = ar.get(field, "")
            if str(ev) != str(av):
                issue_count += 1
                rows.append({"TABLE_NAME": table, "ROW_KEY": k, "FIELD": field, "STATUS": "MISMATCH", "EXPECTED": ev, "ACTUAL": av})

    if issue_count == 0:
        rows.append({"TABLE_NAME": table, "ROW_KEY": "*ALL*", "FIELD": "*ALL*", "STATUS": "PASS", "EXPECTED": str(len(expected)), "ACTUAL": str(len(actual))})
    return rows

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    reports = repo / REPORT_DIR
    reports.mkdir(parents=True, exist_ok=True)

    gates: list[dict[str, Any]] = []
    failures = 0

    def gate(name: str, ok: bool, detail: str) -> None:
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": detail})
        if not ok:
            failures += 1

    p11_summary = reports / "message_catalog_phase11_status_summary_v1.csv"
    p11_manifest = repo / PHASE11_ROOT / "candidate_manifest_v1.json"
    msg_dbf = repo / PHASE11_ROOT / "dbf" / "SYSTEM_MESSAGES.dbf"
    txt_dbf = repo / PHASE11_ROOT / "dbf" / "SYSTEM_MESSAGE_TEXT.dbf"
    msg_csv = repo / PHASE9_ROOT / "import_inputs" / "SYSTEM_MESSAGES_import_candidate_v1.csv"
    txt_csv = repo / PHASE9_ROOT / "import_inputs" / "SYSTEM_MESSAGE_TEXT_import_candidate_v1.csv"

    for gate_name, path in [
        ("PHASE11_STATUS_PRESENT", p11_summary),
        ("PHASE11_MANIFEST_PRESENT", p11_manifest),
        ("SYSTEM_MESSAGES_DBF_PRESENT", msg_dbf),
        ("SYSTEM_MESSAGE_TEXT_DBF_PRESENT", txt_dbf),
        ("SYSTEM_MESSAGES_IMPORT_CSV_PRESENT", msg_csv),
        ("SYSTEM_MESSAGE_TEXT_IMPORT_CSV_PRESENT", txt_csv),
    ]:
        gate(gate_name, path.exists(), str(path))

    messages = "0"
    text_rows = "0"
    locales = ""
    issue_rows: list[dict[str, Any]] = []
    readback_rows: list[dict[str, Any]] = []

    if failures == 0:
        manifest = json.loads(p11_manifest.read_text(encoding="utf-8"))
        gate("PHASE11_STATUS_GREEN", manifest.get("status") == "MESSAGE_CATALOG_PHASE11_INACTIVE_CANDIDATE_DBF_EXECUTION_GREEN", str(manifest.get("status")))
        exp_messages = transform_messages(read_csv(msg_csv))
        exp_text = transform_text(read_csv(txt_csv))

        msg_meta, msg_fields, act_messages = parse_dbf(msg_dbf)
        txt_meta, txt_fields, act_text = parse_dbf(txt_dbf)
        readback_rows = [msg_meta, txt_meta]

        messages = str(len(act_messages))
        text_rows = str(len(act_text))
        locales = ";".join(sorted(set(r.get("LOCALE", "") for r in act_text if r.get("LOCALE"))))

        gate("SYSTEM_MESSAGES_COUNT", len(act_messages) == len(exp_messages), f"actual={len(act_messages)} expected={len(exp_messages)}")
        gate("SYSTEM_MESSAGE_TEXT_COUNT", len(act_text) == len(exp_text), f"actual={len(act_text)} expected={len(exp_text)}")
        gate("LOCALE_COVERAGE", sorted(set(r.get("LOCALE", "") for r in act_text)) == sorted(set(r.get("LOCALE", "") for r in exp_text)), f"actual={locales}")

        issue_rows.extend(compare_rows("SYSTEM_MESSAGES", exp_messages, act_messages, ["MSGID"]))
        issue_rows.extend(compare_rows("SYSTEM_MESSAGE_TEXT", exp_text, act_text, ["MSGID", "LOCALE"]))

        real_issues = [r for r in issue_rows if r.get("STATUS") != "PASS"]
        gate("ROW_MEMO_PARITY", len(real_issues) == 0, f"issues={len(real_issues)}")
    else:
        real_issues = []

    status = STATUS_GREEN if failures == 0 else STATUS_BLOCKED
    validation_issues = str(len([r for r in issue_rows if r.get("STATUS") != "PASS"]) + failures)

    write_csv(reports / "message_catalog_phase12_status_summary_v1.csv", [{
        "STATUS": status,
        "MESSAGES": messages,
        "TEXT_ROWS": text_rows,
        "LOCALES": locales,
        "VALIDATION_ISSUES": validation_issues,
        "DBF_FILES_CREATED": 0,
        "DBT_FILES_CREATED": 0,
        "CDX_FILES_CREATED": 0,
        "LMDB_ENV_CREATED": 0,
        "ACTIVE_PROMOTION_AUTHORIZED": 0,
        "NEXT_GATE": NEXT_GATE,
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }], ["STATUS", "MESSAGES", "TEXT_ROWS", "LOCALES", "VALIDATION_ISSUES",
         "DBF_FILES_CREATED", "DBT_FILES_CREATED", "CDX_FILES_CREATED", "LMDB_ENV_CREATED",
         "ACTIVE_PROMOTION_AUTHORIZED", "NEXT_GATE", "REPORT_TIMESTAMP_UTC"])

    write_csv(reports / "message_catalog_phase12_dbf_readback_v1.csv", readback_rows,
              ["TABLE_NAME", "VERSION_HEX", "RECORDS", "HEADER_LEN", "RECORD_LEN", "FIELD_COUNT",
               "HAS_MEMO", "DBF_PATH", "DBF_SHA256", "DBT_PATH", "DBT_SHA256"])

    write_csv(reports / "message_catalog_phase12_row_parity_v1.csv", issue_rows,
              ["TABLE_NAME", "ROW_KEY", "FIELD", "STATUS", "EXPECTED", "ACTUAL"])

    write_csv(reports / "message_catalog_phase12_gate_check_v1.csv", gates, ["GATE", "STATUS", "DETAIL"])

    boundary_rows = [
        {"PROTECTED_SYSTEM": "INACTIVE_CANDIDATE_DBF", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Phase 12 reads existing inactive candidate DBF/DBT files only."},
        {"PROTECTED_SYSTEM": "ACTIVE_DBF_CATALOGS", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active DBF catalog paths created, replaced, opened for write, or promoted."},
        {"PROTECTED_SYSTEM": "CDX_INDEXES", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CDX/index files created or rebuilt."},
        {"PROTECTED_SYSTEM": "LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No LMDB environment created or rebuilt."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No HELP DATA rebuild or mutation."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CMDHELPCHK mutation."},
        {"PROTECTED_SYSTEM": "SOURCE_MINING", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No source-mining mutation."},
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No source files edited by this script."},
        {"PROTECTED_SYSTEM": "RUNTIME_EXECUTION", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No DotTalk++ runtime execution required."},
        {"PROTECTED_SYSTEM": "CATALOG_PROMOTION", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active catalog promotion authorized or performed."},
    ]
    write_csv(reports / "message_catalog_phase12_boundary_ledger_v1.csv", boundary_rows,
              ["PROTECTED_SYSTEM", "MUTATION_ALLOWED", "OBSERVED_MUTATION", "DETAIL"])

    md = f"""# Message Catalog Phase 12 Candidate DBF Row/Memo Parity

Status: `{status}`

Phase 12 reads the inactive candidate DBF/DBT files created in Phase 11 and
compares row/memo content to the Phase 9 candidate import CSVs.

## Counts

- Messages: {messages}
- Text rows: {text_rows}
- Locales: {locales}
- Validation issues: {validation_issues}

## Next gate

`{NEXT_GATE}`

## Boundary

No DBF/DBT files are created in Phase 12; existing inactive candidate DBF/DBT
files are read only. No CDX/LMDB, HELP DATA, CMDHELPCHK, source-mining,
source-code, runtime, or active catalog promotion mutation occurs.
"""
    (reports / "MESSAGE_CATALOG_PHASE12_CANDIDATE_DBF_ROW_PARITY_REPORT.md").write_text(md, encoding="utf-8")

    print(status)
    print(f"  messages: {messages}")
    print(f"  text rows: {text_rows}")
    print(f"  locales: {locales.replace(';', ', ')}")
    print(f"  validation issues: {validation_issues}")
    print("  dbf files created: 0")
    print("  dbt files created: 0")
    print("  cdx files created: 0")
    print("  lmdb env created: 0")
    print("  active promotion authorized: 0")
    print(f"  reports: {reports}")
    return 0 if status == STATUS_GREEN else 2

if __name__ == "__main__":
    raise SystemExit(main())
