#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import shutil
import struct
from datetime import datetime, timezone
from pathlib import Path

STATUS_GREEN = "MESSAGE_CATALOG_PHASE22AE_3_MEMO_AWARE_PROMOTION_PATH_GREEN_SOURCE_HELD"
STATUS_BLOCKED = "MESSAGE_CATALOG_PHASE22AE_3_MEMO_AWARE_PROMOTION_PATH_BLOCKED"
NEXT_GATE = "HOLD_OR_AUTHORIZE_PHASE22AE_4_MEMO_AWARE_ACTIVE_CATALOG_PROMOTION_PACKAGE"
REPORT_DIR = Path("docs/messaging/reports")
ACTIVE_MSG_ROOT = Path("dottalkpp/data/messaging")
APPLY_ROOT = Path("docs/messaging/apply/phase22ad_active_catalog_replacement_apply_package_v1")
CANDIDATE_ROOT = Path("docs/messaging/candidates/phase22aa_catalog_row_promotion_candidate_v1")

REQUIRED_SYMBOLS = ["MESSAGE_PROOF_MODE_STATUS", "MESSAGE_PROOF_BOUNDARY_NOTE"]
REQUIRED_LOCALES = ["en-US", "es", "fr", "de", "it"]

def read_csv(path: Path):
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

def first_row(path: Path):
    rows = read_csv(path)
    return rows[0] if rows else {}

def write_csv(path: Path, rows, fields):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        w.writeheader()
        for row in rows:
            w.writerow({k: row.get(k, "") for k in fields})

def sha256_file(path: Path) -> str:
    if not path.exists() or not path.is_file():
        return ""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def rel(path: Path, repo: Path) -> str:
    try:
        return str(path.relative_to(repo)).replace("\\", "/")
    except Exception:
        return str(path).replace("\\", "/")

def savepoint_present(repo: Path, savepoint_id: str):
    latest_path = repo / REPORT_DIR / "message_savepoint_latest_v1.json"
    latest_id = ""
    if latest_path.exists():
        try:
            latest = json.loads(latest_path.read_text(encoding="utf-8"))
            latest_id = latest.get("savepoint_id", "")
        except Exception:
            latest_id = ""
    journal = repo / "docs/messaging/MESSAGING_SAVEPOINT_JOURNAL.md"
    journal_text = journal.read_text(encoding="utf-8", errors="replace") if journal.exists() else ""
    return latest_id == savepoint_id or savepoint_id in journal_text, latest_id

def parse_dbf(path: Path):
    data = path.read_bytes()
    if len(data) < 32:
        raise RuntimeError(f"{path} is too small to be a DBF")
    version = data[0]
    record_count = struct.unpack("<I", data[4:8])[0]
    header_len = struct.unpack("<H", data[8:10])[0]
    record_len = struct.unpack("<H", data[10:12])[0]
    fields = []
    pos = 32
    offset = 1
    while pos + 32 <= len(data):
        if data[pos] == 0x0D:
            break
        raw_name = data[pos:pos+11].split(b"\x00", 1)[0]
        name = raw_name.decode("ascii", errors="ignore").strip().upper()
        ftype = chr(data[pos+11])
        length = data[pos+16]
        decimals = data[pos+17]
        if name:
            fields.append({
                "NAME": name,
                "TYPE": ftype,
                "LENGTH": length,
                "DECIMALS": decimals,
                "OFFSET": offset,
            })
            offset += length
        pos += 32
    return {
        "PATH": path,
        "VERSION": version,
        "RECORD_COUNT": record_count,
        "HEADER_LEN": header_len,
        "RECORD_LEN": record_len,
        "FIELDS": fields,
        "HAS_MEMO_FIELD": any(f["TYPE"].upper() == "M" for f in fields),
    }

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    reports = repo / REPORT_DIR
    reports.mkdir(parents=True, exist_ok=True)

    ae = first_row(reports / "message_catalog_phase22ae_status_summary_v1.csv")
    ad = first_row(reports / "message_catalog_phase22ad_status_summary_v1.csv")
    ad_savepoint_ok, latest_id = savepoint_present(repo, "MSG-022AD")

    active_root = repo / ACTIVE_MSG_ROOT
    system_messages = active_root / "SYSTEM_MESSAGES.dbf"
    system_text = active_root / "SYSTEM_MESSAGE_TEXT.dbf"
    system_text_fpt = active_root / "SYSTEM_MESSAGE_TEXT.fpt"

    candidate_msg_path = repo / APPLY_ROOT / "rows/message_catalog_candidate_message_adds_v1.csv"
    candidate_text_path = repo / APPLY_ROOT / "rows/message_catalog_candidate_text_adds_v1.csv"
    if not candidate_msg_path.exists():
        candidate_msg_path = repo / CANDIDATE_ROOT / "rows/message_catalog_candidate_message_adds_v1.csv"
    if not candidate_text_path.exists():
        candidate_text_path = repo / CANDIDATE_ROOT / "rows/message_catalog_candidate_text_adds_v1.csv"

    candidate_msg = read_csv(candidate_msg_path)
    candidate_text = read_csv(candidate_text_path)

    gates = []
    failures = 0
    def gate(name: str, ok: bool, detail: str):
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": detail})
        if not ok:
            failures += 1

    gate("PHASE22AD_GREEN", ad.get("STATUS") == "MESSAGE_CATALOG_PHASE22AD_ACTIVE_CATALOG_REPLACEMENT_APPLY_PACKAGE_STAGED_SOURCE_HELD", ad.get("STATUS", "missing"))
    gate("MSG_022AD_SAVEPOINT_PRESENT", ad_savepoint_ok, latest_id)
    gate("PHASE22AE_BLOCKED_ON_MEMO", "memo field; direct memo append is not supported" in ae.get("ERRORS", ""), ae.get("ERRORS", "missing"))
    gate("NO_ACTIVE_MUTATION_FROM_FAILED_22AE_REPORTED",
         ae.get("ACTIVE_CATALOG_MUTATION_OBSERVED") == "0" and ae.get("MESSAGE_ROWS_ADDED") == "0" and ae.get("TEXT_ROWS_ADDED") == "0",
         f"active={ae.get('ACTIVE_CATALOG_MUTATION_OBSERVED')}; msg={ae.get('MESSAGE_ROWS_ADDED')}; text={ae.get('TEXT_ROWS_ADDED')}")
    gate("ACTIVE_SYSTEM_MESSAGES_DBF_EXISTS", system_messages.exists(), rel(system_messages, repo))
    gate("ACTIVE_SYSTEM_MESSAGE_TEXT_DBF_EXISTS", system_text.exists(), rel(system_text, repo))
    gate("CANDIDATE_MESSAGE_ROWS_AVAILABLE", len(candidate_msg) == 2, f"rows={len(candidate_msg)}")
    gate("CANDIDATE_TEXT_ROWS_AVAILABLE", len(candidate_text) == 10, f"rows={len(candidate_text)}")

    dbf_rows = []
    field_rows = []
    errors = []
    text_has_memo = False

    for path, role in [(system_messages, "messages"), (system_text, "message_text")]:
        if path.exists():
            try:
                info = parse_dbf(path)
                dbf_rows.append({
                    "ROLE": role,
                    "PATH": rel(path, repo),
                    "VERSION": info["VERSION"],
                    "RECORD_COUNT": info["RECORD_COUNT"],
                    "HEADER_LEN": info["HEADER_LEN"],
                    "RECORD_LEN": info["RECORD_LEN"],
                    "HAS_MEMO_FIELD": 1 if info["HAS_MEMO_FIELD"] else 0,
                    "SIDE_CAR_FPT_EXISTS": 1 if (path.with_suffix(".fpt")).exists() else 0,
                    "SIDE_CAR_DBT_EXISTS": 1 if (path.with_suffix(".dbt")).exists() else 0,
                    "SHA256": sha256_file(path),
                })
                if role == "message_text":
                    text_has_memo = info["HAS_MEMO_FIELD"]
                for f in info["FIELDS"]:
                    field_rows.append({
                        "ROLE": role,
                        "DBF": rel(path, repo),
                        "FIELD": f["NAME"],
                        "TYPE": f["TYPE"],
                        "LENGTH": f["LENGTH"],
                        "DECIMALS": f["DECIMALS"],
                        "OFFSET": f["OFFSET"],
                    })
            except Exception as exc:
                errors.append(f"{path}: {exc}")

    gate("SYSTEM_MESSAGE_TEXT_TEXT_IS_MEMO",
         any(r["ROLE"] == "message_text" and r["FIELD"] == "TEXT" and r["TYPE"].upper() == "M" for r in field_rows),
         "TEXT memo field expected")
    gate("SYSTEM_MESSAGE_TEXT_MEMO_SIDECAR_PRESENT",
         system_text_fpt.exists() or (system_text.with_suffix(".dbt")).exists(),
         f"fpt={system_text_fpt.exists()}; dbt={system_text.with_suffix('.dbt').exists()}")

    candidate_review = []
    for row in candidate_text:
        text = row.get("TEXT", "")
        candidate_review.append({
            "SYMBOL": row.get("SYMBOL", ""),
            "LOCALE": row.get("LOCALE", ""),
            "TEXT_LENGTH_CHARS": len(text),
            "TEXT_SHA256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
            "REQUIRES_MEMO_WRITE": 1,
            "DIRECT_DBF_APPEND_ALLOWED": 0,
        })

    promotion_path = [
        {
            "STEP": 1,
            "ACTION": "DO_NOT_USE_RAW_DBF_APPEND_FOR_SYSTEM_MESSAGE_TEXT",
            "DETAIL": "SYSTEM_MESSAGE_TEXT.TEXT is memo-backed. The next apply must go through a memo-aware path.",
            "MUTATES_ACTIVE": 0,
        },
        {
            "STEP": 2,
            "ACTION": "USE_RUNTIME_OR_EXISTING_IMPORT_PATH",
            "DETAIL": "Preferred: use DotTalk++/x64base memo-aware APPEND/REPLACE or existing messaging catalog import/rebuild utility to write TEXT memo values.",
            "MUTATES_ACTIVE": 0,
        },
        {
            "STEP": 3,
            "ACTION": "BACKUP_ACTIVE_MESSAGING_ROOTS",
            "DETAIL": "Before the memo-aware apply, back up dottalkpp/data/messaging, dottalkpp/data/indexes/messaging, and dottalkpp/data/lmdb/messaging.",
            "MUTATES_ACTIVE": 0,
        },
        {
            "STEP": 4,
            "ACTION": "ADD_EXACTLY_2_MESSAGE_ROWS_AND_10_TEXT_MEMO_ROWS",
            "DETAIL": "Only MESSAGE_PROOF_MODE_STATUS and MESSAGE_PROOF_BOUNDARY_NOTE may be promoted, with five locales each.",
            "MUTATES_ACTIVE": 0,
        },
        {
            "STEP": 5,
            "ACTION": "REBUILD_OR_VALIDATE_INDEXES_AND_LMDB",
            "DETAIL": "After active row/memo write, rebuild or validate active messaging CDX/LMDB.",
            "MUTATES_ACTIVE": 0,
        },
        {
            "STEP": 6,
            "ACTION": "READBACK_ACTIVE_COUNTS_AND_TEXT",
            "DETAIL": "Readback must show 14 messages, 70 text rows, and exact text values for all 10 new locale rows.",
            "MUTATES_ACTIVE": 0,
        },
        {
            "STEP": 7,
            "ACTION": "RUN_22Y_FOCUSED_SMOKE_AND_22V_REGRESSION",
            "DETAIL": "Runtime proof must still show active_dbf provider, proof-status routing, and all prior seams green.",
            "MUTATES_ACTIVE": 0,
        },
    ]

    status = STATUS_GREEN if failures == 0 else STATUS_BLOCKED
    validation_issues = str(failures)

    write_csv(reports / "message_catalog_phase22ae_3_active_dbf_memo_probe_v1.csv", dbf_rows,
              ["ROLE", "PATH", "VERSION", "RECORD_COUNT", "HEADER_LEN", "RECORD_LEN",
               "HAS_MEMO_FIELD", "SIDE_CAR_FPT_EXISTS", "SIDE_CAR_DBT_EXISTS", "SHA256"])
    write_csv(reports / "message_catalog_phase22ae_3_active_dbf_field_inventory_v1.csv", field_rows,
              ["ROLE", "DBF", "FIELD", "TYPE", "LENGTH", "DECIMALS", "OFFSET"])
    write_csv(reports / "message_catalog_phase22ae_3_candidate_text_memo_review_v1.csv", candidate_review,
              ["SYMBOL", "LOCALE", "TEXT_LENGTH_CHARS", "TEXT_SHA256",
               "REQUIRES_MEMO_WRITE", "DIRECT_DBF_APPEND_ALLOWED"])
    write_csv(reports / "message_catalog_phase22ae_3_memo_aware_promotion_path_v1.csv", promotion_path,
              ["STEP", "ACTION", "DETAIL", "MUTATES_ACTIVE"])
    write_csv(reports / "message_catalog_phase22ae_3_gate_check_v1.csv", gates,
              ["GATE", "STATUS", "DETAIL"])

    boundary = [
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Phase 22AE.3 is probe/plan only; no source mutation."},
        {"PROTECTED_SYSTEM": "TOOLS_MESSAGING_SCRIPT", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No tool script mutation in 22AE.3."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_DBF_CATALOG", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active DBF mutation in 22AE.3."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_CDX_INDEXES", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active CDX/index mutation in 22AE.3."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active LMDB mutation in 22AE.3."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No HELP DATA mutation."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CMDHELPCHK mutation."},
        {"PROTECTED_SYSTEM": "COMMAND_REGISTRY", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No command registry mutation."},
        {"PROTECTED_SYSTEM": "MANUALGEN", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No manualgen mutation."},
        {"PROTECTED_SYSTEM": "DATADICT_SELF_DOC", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No Data Dictionary/SelfDoc mutation."},
    ]
    write_csv(reports / "message_catalog_phase22ae_3_boundary_ledger_v1.csv", boundary,
              ["PROTECTED_SYSTEM", "MUTATION_ALLOWED", "OBSERVED_MUTATION", "DETAIL"])

    write_csv(reports / "message_catalog_phase22ae_3_status_summary_v1.csv", [{
        "STATUS": status,
        "VALIDATION_ISSUES": validation_issues,
        "PHASE22AD_GREEN": 1 if ad.get("STATUS") == "MESSAGE_CATALOG_PHASE22AD_ACTIVE_CATALOG_REPLACEMENT_APPLY_PACKAGE_STAGED_SOURCE_HELD" else 0,
        "MSG_022AD_SAVEPOINT_PRESENT": 1 if ad_savepoint_ok else 0,
        "PHASE22AE_BLOCKED_ON_MEMO": 1 if "memo field; direct memo append is not supported" in ae.get("ERRORS", "") else 0,
        "SYSTEM_MESSAGE_TEXT_TEXT_MEMO": 1 if text_has_memo else 0,
        "DIRECT_DBF_APPEND_ALLOWED": 0,
        "MEMO_AWARE_PROMOTION_REQUIRED": 1,
        "CANDIDATE_MESSAGE_ROWS": len(candidate_msg),
        "CANDIDATE_TEXT_ROWS": len(candidate_text),
        "SOURCE_FILES_MUTATED": 0,
        "TOOL_FILES_MUTATED": 0,
        "ACTIVE_CATALOG_MUTATION_OBSERVED": 0,
        "ACTIVE_INDEX_MUTATION_OBSERVED": 0,
        "ACTIVE_LMDB_MUTATION_OBSERVED": 0,
        "HELP_DATA_MUTATION_OBSERVED": 0,
        "CMDHELPCHK_MUTATION_OBSERVED": 0,
        "ERRORS": "; ".join(errors),
        "NEXT_GATE": NEXT_GATE,
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }], ["STATUS", "VALIDATION_ISSUES", "PHASE22AD_GREEN", "MSG_022AD_SAVEPOINT_PRESENT",
         "PHASE22AE_BLOCKED_ON_MEMO", "SYSTEM_MESSAGE_TEXT_TEXT_MEMO",
         "DIRECT_DBF_APPEND_ALLOWED", "MEMO_AWARE_PROMOTION_REQUIRED",
         "CANDIDATE_MESSAGE_ROWS", "CANDIDATE_TEXT_ROWS",
         "SOURCE_FILES_MUTATED", "TOOL_FILES_MUTATED", "ACTIVE_CATALOG_MUTATION_OBSERVED",
         "ACTIVE_INDEX_MUTATION_OBSERVED", "ACTIVE_LMDB_MUTATION_OBSERVED",
         "HELP_DATA_MUTATION_OBSERVED", "CMDHELPCHK_MUTATION_OBSERVED",
         "ERRORS", "NEXT_GATE", "REPORT_TIMESTAMP_UTC"])

    md = f"""# Message Catalog Phase 22AE.3 Memo-Aware Promotion Path

Status: `{status}`

Phase 22AE.3 records why direct DBF append is the wrong execution path:

```text
SYSTEM_MESSAGE_TEXT.TEXT is memo-backed
```

Therefore the active promotion must use a memo-aware runtime/import path, not raw
DBF record append.

No mutation occurred in 22AE.3.

Next gate:

```text
{NEXT_GATE}
```
"""
    (reports / "MESSAGE_CATALOG_PHASE22AE_3_MEMO_AWARE_PROMOTION_PATH.md").write_text(md, encoding="utf-8")

    print(status)
    print(f"  validation issues: {validation_issues}")
    print(f"  Phase 22AD green: {1 if ad.get('STATUS') == 'MESSAGE_CATALOG_PHASE22AD_ACTIVE_CATALOG_REPLACEMENT_APPLY_PACKAGE_STAGED_SOURCE_HELD' else 0}")
    print(f"  MSG-022AD savepoint present: {1 if ad_savepoint_ok else 0}")
    print(f"  Phase 22AE blocked on memo: {1 if 'memo field; direct memo append is not supported' in ae.get('ERRORS', '') else 0}")
    print(f"  SYSTEM_MESSAGE_TEXT.TEXT memo: {1 if text_has_memo else 0}")
    print("  direct DBF append allowed: 0")
    print("  memo-aware promotion required: 1")
    print(f"  candidate message rows: {len(candidate_msg)}")
    print(f"  candidate text rows: {len(candidate_text)}")
    print("  source files mutated: 0")
    print("  tool files mutated: 0")
    print("  active catalog mutation observed: 0")
    print("  HELP DATA mutation observed: 0")
    print("  CMDHELPCHK mutation observed: 0")
    print(f"  next gate: {NEXT_GATE}")
    print(f"  reports: {reports}")
    return 0 if status == STATUS_GREEN else 2

if __name__ == "__main__":
    raise SystemExit(main())
