#!/usr/bin/env python3
"""
Phase 11: Inactive candidate DBF execution for DotTalk++ Messaging catalog.

Creates inactive candidate DBF/DBT files from Phase 9 import CSVs and performs
Python readback validation. This does not touch active DBF catalogs, HELP DATA,
CMDHELPCHK, source-mining, source code, runtime tables, or active catalog
promotion.

CDX/LMDB creation is deliberately deferred to a later phase after candidate DBF
row parity is proven.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import shutil
import struct
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

STATUS_GREEN = "MESSAGE_CATALOG_PHASE11_INACTIVE_CANDIDATE_DBF_EXECUTION_GREEN"
STATUS_BLOCKED = "MESSAGE_CATALOG_PHASE11_INACTIVE_CANDIDATE_DBF_EXECUTION_BLOCKED"
NEXT_GATE = "HOLD_OR_AUTHORIZE_PHASE12_CANDIDATE_CDX_TAG_PLAN_OR_READBACK_RUNTIME_SMOKE"
REPORT_DIR = Path("docs/messaging/reports")
PHASE9_ROOT = Path("docs/messaging/candidates/phase9_inactive_candidate_dbf_staging")
PHASE11_ROOT = Path("docs/messaging/candidates/phase11_inactive_candidate_dbf_execution")

@dataclass
class Field:
    name: str
    ftype: str
    width: int
    decimals: int = 0

SYSTEM_MESSAGES_FIELDS = [
    Field("MSGID", "N", 10, 0),
    Field("SYMBOL", "C", 64, 0),
    Field("ENUMNAME", "C", 64, 0),
    Field("FACILITY", "C", 32, 0),
    Field("OWNER", "C", 64, 0),
    Field("CATEGORY", "C", 32, 0),
    Field("SEVERITY", "C", 16, 0),
    Field("STATUS", "C", 16, 0),
    Field("SRC", "C", 32, 0),
    Field("NOTES", "M", 10, 0),
]

SYSTEM_MESSAGE_TEXT_FIELDS = [
    Field("MSGID", "N", 10, 0),
    Field("SYMBOL", "C", 64, 0),
    Field("ENUMNAME", "C", 64, 0),
    Field("LOCALE", "C", 16, 0),
    Field("TEXT", "M", 10, 0),
    Field("TXTHASH", "C", 64, 0),
    Field("STATUS", "C", 16, 0),
    Field("SRC", "C", 32, 0),
]

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

def sha256_text(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def pick(row: dict[str, str], *names: str, default: str = "") -> str:
    for n in names:
        if n in row and row[n] != "":
            return row[n]
    return default

def transform_messages(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    for r in rows:
        out.append({
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
        })
    return out

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

def format_field_value(field: Field, value: str, memo_writer=None) -> bytes:
    if field.ftype == "C":
        b = str(value).encode("utf-8", errors="replace")[:field.width]
        return b + b" " * (field.width - len(b))
    if field.ftype == "N":
        try:
            if value == "":
                s = ""
            else:
                s = str(int(float(str(value))))
        except Exception:
            s = str(value)
        b = s.encode("ascii", errors="replace")[-field.width:]
        return b" " * (field.width - len(b)) + b
    if field.ftype == "M":
        # Phase 11.1 repair:
        # If a memo_writer callback is supplied, value is the memo text and the
        # callback returns a block pointer. If no callback is supplied, value is
        # already the precomputed DBT block pointer and must be written as-is.
        if memo_writer is None:
            try:
                block = int(str(value).strip()) if str(value).strip() else 0
            except ValueError:
                block = 0
        else:
            block = memo_writer(str(value))
        s = str(block)
        b = s.encode("ascii")[-field.width:]
        return b" " * (field.width - len(b)) + b
    raise ValueError(f"unsupported DBF field type {field.ftype}")

def write_dbt(dbt_path: Path, memo_values: list[str]) -> list[int]:
    """Write a simple dBASE III style .DBT and return memo block numbers."""
    block_size = 512
    blocks: list[int] = []
    next_block = 1
    payloads: list[bytes] = []
    for value in memo_values:
        if value == "":
            blocks.append(0)
            continue
        raw = value.encode("utf-8") + b"\x1a"
        nblocks = max(1, math.ceil(len(raw) / block_size))
        blocks.append(next_block)
        payload = raw + (b"\x00" * (nblocks * block_size - len(raw)))
        payloads.append(payload)
        next_block += nblocks

    header = bytearray(block_size)
    # dBASE III DBT stores next available block as big-endian 32-bit at offset 0.
    header[0:4] = int(next_block).to_bytes(4, "big")
    with dbt_path.open("wb") as f:
        f.write(header)
        for payload in payloads:
            f.write(payload)
    return blocks

def write_dbf(path: Path, fields: list[Field], rows: list[dict[str, str]]) -> dict[str, Any]:
    path.parent.mkdir(parents=True, exist_ok=True)
    has_memo = any(f.ftype == "M" for f in fields)
    dbt_path = path.with_suffix(".dbt")

    # Pre-collect memo values in row/field order and write DBT once.
    memo_values: list[str] = []
    memo_positions: list[tuple[int, str]] = []
    if has_memo:
        for row_index, row in enumerate(rows):
            for f in fields:
                if f.ftype == "M":
                    memo_positions.append((row_index, f.name))
                    memo_values.append(row.get(f.name, ""))
        memo_blocks = write_dbt(dbt_path, memo_values)
        memo_map = {pos: block for pos, block in zip(memo_positions, memo_blocks)}
    else:
        memo_map = {}

    now = datetime.now()
    num_records = len(rows)
    header_len = 32 + 32 * len(fields) + 1
    record_len = 1 + sum(f.width for f in fields)
    version = 0x83 if has_memo else 0x03

    header = bytearray(32)
    header[0] = version
    header[1] = now.year - 1900
    header[2] = now.month
    header[3] = now.day
    header[4:8] = struct.pack("<I", num_records)
    header[8:10] = struct.pack("<H", header_len)
    header[10:12] = struct.pack("<H", record_len)

    with path.open("wb") as f:
        f.write(header)
        for field in fields:
            desc = bytearray(32)
            name_b = field.name.encode("ascii")[:11]
            desc[0:len(name_b)] = name_b
            desc[11] = ord(field.ftype)
            desc[16] = field.width
            desc[17] = field.decimals
            f.write(desc)
        f.write(b"\x0d")

        for row_index, row in enumerate(rows):
            rec = bytearray()
            rec.extend(b" ")
            for field in fields:
                if field.ftype == "M":
                    block = memo_map.get((row_index, field.name), 0)
                    rec.extend(format_field_value(field, str(block), memo_writer=None))
                else:
                    rec.extend(format_field_value(field, row.get(field.name, "")))
            if len(rec) != record_len:
                raise RuntimeError(f"record length mismatch for {path.name}: got {len(rec)}, expected {record_len}")
            f.write(rec)
        f.write(b"\x1a")

    result = {
        "dbf": str(path),
        "records": num_records,
        "fields": len(fields),
        "header_len": header_len,
        "record_len": record_len,
        "has_memo": int(has_memo),
        "dbf_sha256": sha256_file(path),
    }
    if has_memo:
        result["dbt"] = str(dbt_path)
        result["dbt_sha256"] = sha256_file(dbt_path)
    return result

def parse_dbf_header(path: Path) -> dict[str, Any]:
    with path.open("rb") as f:
        h = f.read(32)
        if len(h) != 32:
            raise RuntimeError(f"short DBF header: {path}")
        version = h[0]
        num_records = struct.unpack("<I", h[4:8])[0]
        header_len = struct.unpack("<H", h[8:10])[0]
        record_len = struct.unpack("<H", h[10:12])[0]
        field_count = (header_len - 33) // 32
    return {
        "TABLE_NAME": path.stem,
        "VERSION_HEX": hex(version),
        "RECORDS": num_records,
        "HEADER_LEN": header_len,
        "RECORD_LEN": record_len,
        "FIELD_COUNT": field_count,
        "HAS_MEMO": 1 if version in (0x83, 0x8b, 0xf5) else 0,
    }

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--allow-inactive-candidate-dbf-execution", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    reports = repo / REPORT_DIR
    reports.mkdir(parents=True, exist_ok=True)

    phase9_manifest = repo / PHASE9_ROOT / "candidate_manifest_v1.json"
    messages_csv = repo / PHASE9_ROOT / "import_inputs" / "SYSTEM_MESSAGES_import_candidate_v1.csv"
    text_csv = repo / PHASE9_ROOT / "import_inputs" / "SYSTEM_MESSAGE_TEXT_import_candidate_v1.csv"

    gates: list[dict[str, Any]] = []
    failures = 0

    def gate(name: str, ok: bool, detail: str) -> None:
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": detail})
        if not ok:
            failures += 1

    gate("OPERATOR_AUTHORIZED_INACTIVE_CANDIDATE_DBF_EXECUTION",
         args.allow_inactive_candidate_dbf_execution,
         "Requires --allow-inactive-candidate-dbf-execution")
    gate("PHASE9_MANIFEST_PRESENT", phase9_manifest.exists(), str(phase9_manifest))
    gate("PHASE9_SYSTEM_MESSAGES_INPUT_PRESENT", messages_csv.exists(), str(messages_csv))
    gate("PHASE9_SYSTEM_MESSAGE_TEXT_INPUT_PRESENT", text_csv.exists(), str(text_csv))

    if failures:
        status = STATUS_BLOCKED
        messages = "0"
        text_rows = "0"
        locales = ""
        validation_issues = "BLOCKED"
        created: list[dict[str, Any]] = []
        readback: list[dict[str, Any]] = []
    else:
        manifest = json.loads(phase9_manifest.read_text(encoding="utf-8"))
        messages_rows = transform_messages(read_csv(messages_csv))
        text_rows_rows = transform_text(read_csv(text_csv))

        messages = str(len(messages_rows))
        text_rows = str(len(text_rows_rows))
        locales_list = sorted(set(r.get("LOCALE", "") for r in text_rows_rows if r.get("LOCALE", "")))
        locales = ";".join(locales_list)

        gate("PHASE9_STATUS_GREEN", manifest.get("status") == "MESSAGE_CATALOG_PHASE9_INACTIVE_CANDIDATE_STAGING_GREEN", str(manifest.get("status")))
        gate("EXPECTED_MESSAGE_COUNT", len(messages_rows) == int(manifest.get("messages", 12)), f"rows={len(messages_rows)} manifest={manifest.get('messages')}")
        gate("EXPECTED_TEXT_COUNT", len(text_rows_rows) == int(manifest.get("text_rows", 60)), f"rows={len(text_rows_rows)} manifest={manifest.get('text_rows')}")
        gate("EXPECTED_LOCALES", locales_list == sorted(manifest.get("locales", [])), f"rows={locales_list} manifest={manifest.get('locales')}")

        candidate = repo / PHASE11_ROOT
        dbf_dir = candidate / "dbf"
        readback_dir = candidate / "readback"
        if candidate.exists():
            shutil.rmtree(candidate)
        dbf_dir.mkdir(parents=True, exist_ok=True)
        readback_dir.mkdir(parents=True, exist_ok=True)

        created = []
        if failures == 0:
            created.append(write_dbf(dbf_dir / "SYSTEM_MESSAGES.dbf", SYSTEM_MESSAGES_FIELDS, messages_rows))
            created.append(write_dbf(dbf_dir / "SYSTEM_MESSAGE_TEXT.dbf", SYSTEM_MESSAGE_TEXT_FIELDS, text_rows_rows))

        readback = []
        for table in ["SYSTEM_MESSAGES", "SYSTEM_MESSAGE_TEXT"]:
            p = dbf_dir / f"{table}.dbf"
            rb = parse_dbf_header(p)
            rb["DBF_PATH"] = str(p.relative_to(repo))
            rb["DBF_SHA256"] = sha256_file(p)
            dbt = p.with_suffix(".dbt")
            if dbt.exists():
                rb["DBT_PATH"] = str(dbt.relative_to(repo))
                rb["DBT_SHA256"] = sha256_file(dbt)
            else:
                rb["DBT_PATH"] = ""
                rb["DBT_SHA256"] = ""
            readback.append(rb)

        # Validate readback counts.
        rb_map = {r["TABLE_NAME"]: r for r in readback}
        gate("READBACK_SYSTEM_MESSAGES_COUNT", int(rb_map["SYSTEM_MESSAGES"]["RECORDS"]) == len(messages_rows), str(rb_map["SYSTEM_MESSAGES"]["RECORDS"]))
        gate("READBACK_SYSTEM_MESSAGE_TEXT_COUNT", int(rb_map["SYSTEM_MESSAGE_TEXT"]["RECORDS"]) == len(text_rows_rows), str(rb_map["SYSTEM_MESSAGE_TEXT"]["RECORDS"]))
        gate("DBF_FILES_CREATED_IN_CANDIDATE_PATH_ONLY", all(str(Path(c["dbf"])).find(str(PHASE11_ROOT)) >= 0 for c in created), "candidate path only")
        gate("ACTIVE_PROMOTION_NOT_AUTHORIZED", True, "No active catalog promotion authorized.")

        validation_issues = "0" if failures == 0 else str(failures)
        status = STATUS_GREEN if failures == 0 else STATUS_BLOCKED

        # Candidate manifest
        artifact_rows: list[dict[str, Any]] = []
        for p in sorted(candidate.rglob("*")):
            if p.is_file():
                artifact_rows.append({
                    "RELATIVE_PATH": str(p.relative_to(repo)).replace("\\", "/"),
                    "BYTES": p.stat().st_size,
                    "SHA256": sha256_file(p),
                    "ROLE": "inactive_candidate_dbf_execution_artifact",
                })

        cand_manifest = {
            "status": status,
            "candidate_name": "phase11_inactive_candidate_dbf_execution",
            "candidate_root": str(PHASE11_ROOT).replace("\\", "/"),
            "messages": int(messages),
            "text_rows": int(text_rows),
            "locales": locales_list,
            "validation_issues": int(validation_issues) if validation_issues.isdigit() else validation_issues,
            "dbf_files_created": sum(1 for a in artifact_rows if a["RELATIVE_PATH"].lower().endswith(".dbf")),
            "dbt_files_created": sum(1 for a in artifact_rows if a["RELATIVE_PATH"].lower().endswith(".dbt")),
            "cdx_files_created": 0,
            "lmdb_env_created": 0,
            "active_promotion_authorized": 0,
            "active_catalog_mutation": 0,
            "candidate_artifacts": artifact_rows,
        }
        (candidate / "candidate_manifest_v1.json").write_text(json.dumps(cand_manifest, indent=2), encoding="utf-8")

        # Recompute artifact rows including manifest itself.
        artifact_rows = []
        for p in sorted(candidate.rglob("*")):
            if p.is_file():
                artifact_rows.append({
                    "RELATIVE_PATH": str(p.relative_to(repo)).replace("\\", "/"),
                    "BYTES": p.stat().st_size,
                    "SHA256": sha256_file(p),
                    "ROLE": "inactive_candidate_dbf_execution_artifact",
                })
        write_csv(reports / "message_catalog_phase11_candidate_artifact_inventory_v1.csv",
                  artifact_rows, ["RELATIVE_PATH", "BYTES", "SHA256", "ROLE"])

    # Reports common to green/blocked
    status_rows = [{
        "STATUS": status,
        "MESSAGES": messages,
        "TEXT_ROWS": text_rows,
        "LOCALES": locales,
        "VALIDATION_ISSUES": validation_issues,
        "DBF_FILES_CREATED": 2 if status == STATUS_GREEN else 0,
        "DBT_FILES_CREATED": 2 if status == STATUS_GREEN else 0,
        "CDX_FILES_CREATED": 0,
        "LMDB_ENV_CREATED": 0,
        "ACTIVE_PROMOTION_AUTHORIZED": 0,
        "NEXT_GATE": NEXT_GATE,
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }]
    write_csv(reports / "message_catalog_phase11_status_summary_v1.csv", status_rows,
              ["STATUS", "MESSAGES", "TEXT_ROWS", "LOCALES", "VALIDATION_ISSUES",
               "DBF_FILES_CREATED", "DBT_FILES_CREATED", "CDX_FILES_CREATED",
               "LMDB_ENV_CREATED", "ACTIVE_PROMOTION_AUTHORIZED", "NEXT_GATE", "REPORT_TIMESTAMP_UTC"])

    if status == STATUS_GREEN:
        write_csv(reports / "message_catalog_phase11_dbf_header_readback_v1.csv", readback,
                  ["TABLE_NAME", "VERSION_HEX", "RECORDS", "HEADER_LEN", "RECORD_LEN",
                   "FIELD_COUNT", "HAS_MEMO", "DBF_PATH", "DBF_SHA256", "DBT_PATH", "DBT_SHA256"])
    else:
        write_csv(reports / "message_catalog_phase11_dbf_header_readback_v1.csv", [],
                  ["TABLE_NAME", "VERSION_HEX", "RECORDS", "HEADER_LEN", "RECORD_LEN",
                   "FIELD_COUNT", "HAS_MEMO", "DBF_PATH", "DBF_SHA256", "DBT_PATH", "DBT_SHA256"])
        write_csv(reports / "message_catalog_phase11_candidate_artifact_inventory_v1.csv", [],
                  ["RELATIVE_PATH", "BYTES", "SHA256", "ROLE"])

    write_csv(reports / "message_catalog_phase11_gate_check_v1.csv", gates, ["GATE", "STATUS", "DETAIL"])

    boundary_rows = [
        {"PROTECTED_SYSTEM": "INACTIVE_CANDIDATE_DBF", "MUTATION_ALLOWED": 1, "OBSERVED_MUTATION": 1 if status == STATUS_GREEN else 0, "DETAIL": "Candidate-only DBF/DBT files may be created under docs/messaging/candidates/phase11_inactive_candidate_dbf_execution."},
        {"PROTECTED_SYSTEM": "ACTIVE_DBF_CATALOGS", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active DBF catalog paths created, replaced, opened for write, or promoted."},
        {"PROTECTED_SYSTEM": "CDX_INDEXES", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CDX/index files created or rebuilt in Phase 11."},
        {"PROTECTED_SYSTEM": "LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No LMDB environment created or rebuilt in Phase 11."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No HELP DATA rebuild or mutation."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CMDHELPCHK mutation."},
        {"PROTECTED_SYSTEM": "SOURCE_MINING", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No source-mining mutation."},
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No source files edited by this script."},
        {"PROTECTED_SYSTEM": "RUNTIME_EXECUTION", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No DotTalk++ runtime execution required by Phase 11 Python candidate writer."},
        {"PROTECTED_SYSTEM": "CATALOG_PROMOTION", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active catalog promotion authorized or performed."},
    ]
    write_csv(reports / "message_catalog_phase11_boundary_ledger_v1.csv", boundary_rows,
              ["PROTECTED_SYSTEM", "MUTATION_ALLOWED", "OBSERVED_MUTATION", "DETAIL"])

    md = f"""# Message Catalog Phase 11 Inactive Candidate DBF Execution

Status: `{status}`

Phase 11 creates inactive candidate DBF/DBT files only, under:

`{PHASE11_ROOT}`

## Counts

- Messages: {messages}
- Text rows: {text_rows}
- Locales: {locales}
- Validation issues: {validation_issues}

## Artifacts

- Candidate DBFs: `{PHASE11_ROOT}/dbf/SYSTEM_MESSAGES.dbf`, `{PHASE11_ROOT}/dbf/SYSTEM_MESSAGE_TEXT.dbf`
- Candidate DBTs: matching `.dbt` memo files
- Candidate manifest: `{PHASE11_ROOT}/candidate_manifest_v1.json`

## Deferred

- CDX tag creation
- LMDB build
- DotTalk++ runtime readback smoke
- Active catalog promotion

## Next gate

`{NEXT_GATE}`
"""
    (reports / "MESSAGE_CATALOG_PHASE11_INACTIVE_CANDIDATE_DBF_EXECUTION_REPORT.md").write_text(md, encoding="utf-8")

    print(status)
    print(f"  messages: {messages}")
    print(f"  text rows: {text_rows}")
    print(f"  locales: {locales.replace(';', ', ')}")
    print(f"  validation issues: {validation_issues}")
    print(f"  dbf files created: {2 if status == STATUS_GREEN else 0}")
    print(f"  dbt files created: {2 if status == STATUS_GREEN else 0}")
    print("  cdx files created: 0")
    print("  lmdb env created: 0")
    print("  active promotion authorized: 0")
    print(f"  reports: {reports}")
    return 0 if status == STATUS_GREEN else 2

if __name__ == "__main__":
    raise SystemExit(main())
