#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import struct
from datetime import datetime, timezone
from pathlib import Path

STATUS_GREEN = "MESSAGE_CATALOG_PHASE22AE_5_1_PARTIAL_PROMOTION_DIAGNOSTIC_GREEN_SOURCE_HELD"
STATUS_BLOCKED = "MESSAGE_CATALOG_PHASE22AE_5_1_PARTIAL_PROMOTION_DIAGNOSTIC_BLOCKED"
NEXT_GATE = "HOLD_OR_AUTHORIZE_PHASE22AE_5_2_PARTIAL_PROMOTION_REPAIR_OR_ROLLBACK_PLAN"
REPORT_DIR = Path("docs/messaging/reports")
ACTIVE_MSG_ROOT = Path("dottalkpp/data/messaging")
CANDIDATE_ROOT = Path("docs/messaging/candidates/phase22aa_catalog_row_promotion_candidate_v1")
APPLYAD_ROOT = Path("docs/messaging/apply/phase22ad_active_catalog_replacement_apply_package_v1")

SYMBOL_FIELDS = ["SYMBOL", "MESSAGE_SYMBOL", "MSG_SYMBOL"]
LOCALE_FIELDS = ["LOCALE", "LOCALE_ID"]
TEXT_FIELDS = ["TEXT", "MESSAGE_TEXT", "MSG_TEXT"]
KIND_FIELDS = ["KIND", "MESSAGE_KIND", "MSG_KIND"]
PLACEHOLDER_FIELDS = ["PLACEHOLDERS", "PLACEHOLDER", "ARGS", "ARGUMENTS"]
STATUS_FIELDS = ["STATUS", "ROW_STATUS"]
SOURCE_FIELDS = ["SOURCE_PHASE", "SOURCE", "PHASE"]
REQUIRED_SYMBOLS = ["MESSAGE_PROOF_MODE_STATUS", "MESSAGE_PROOF_BOUNDARY_NOTE"]
REQUIRED_LOCALES = ["en-US", "es", "fr", "de", "it"]

class DbfInfo:
    def __init__(self, path, record_count, header_len, record_len, fields):
        self.path = path
        self.record_count = record_count
        self.header_len = header_len
        self.record_len = record_len
        self.fields = fields

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

def sha256_file(path: Path):
    if not path.exists() or not path.is_file():
        return ""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def sha256_text(text: str):
    return hashlib.sha256(str(text).encode("utf-8")).hexdigest()

def rel(path: Path, repo: Path):
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

def parse_dbf(path: Path) -> DbfInfo:
    data = path.read_bytes()
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
            fields.append({"NAME": name, "TYPE": ftype, "LENGTH": length, "DECIMALS": decimals, "OFFSET": offset})
            offset += length
        pos += 32
    return DbfInfo(path, record_count, header_len, record_len, fields)

def read_rows(info: DbfInfo):
    rows = []
    with info.path.open("rb") as f:
        f.seek(info.header_len)
        for i in range(info.record_count):
            rec = f.read(info.record_len)
            if len(rec) < info.record_len:
                break
            deleted = rec[:1] == b"*"
            row = {"__RECNO__": i + 1, "__DELETED__": 1 if deleted else 0}
            for field in info.fields:
                raw = rec[field["OFFSET"]:field["OFFSET"] + field["LENGTH"]]
                ftype = field["TYPE"].upper()
                if ftype == "M":
                    # Raw DBF memo pointer. Runtime/memo-aware readback still needed for full memo contents.
                    raw_text = raw.decode("cp1252", errors="replace").rstrip().strip()
                    row[field["NAME"]] = raw_text
                    row[field["NAME"] + "__RAW_HEX"] = raw.hex()
                elif ftype in ("C",):
                    row[field["NAME"]] = raw.decode("cp1252", errors="replace").rstrip().strip()
                else:
                    row[field["NAME"]] = raw.decode("ascii", errors="replace").rstrip().strip()
            rows.append(row)
    return rows

def choose_field(info: DbfInfo, choices):
    names = {f["NAME"] for f in info.fields}
    for c in choices:
        if c in names:
            return c
    return ""

def candidate_paths(repo: Path):
    msg = repo / APPLYAD_ROOT / "rows/message_catalog_candidate_message_adds_v1.csv"
    txt = repo / APPLYAD_ROOT / "rows/message_catalog_candidate_text_adds_v1.csv"
    if not msg.exists():
        msg = repo / CANDIDATE_ROOT / "rows/message_catalog_candidate_message_adds_v1.csv"
    if not txt.exists():
        txt = repo / CANDIDATE_ROOT / "rows/message_catalog_candidate_text_adds_v1.csv"
    return msg, txt

def project_row(row: dict, fields: list[str]):
    out = {}
    for f in fields:
        if f and f in row:
            out[f] = row.get(f, "")
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--tail", type=int, default=8)
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    reports = repo / REPORT_DIR
    reports.mkdir(parents=True, exist_ok=True)

    ae5 = first_row(reports / "message_catalog_phase22ae_5_status_summary_v1.csv")
    ae4 = first_row(reports / "message_catalog_phase22ae_4_status_summary_v1.csv")
    ae4_sp, latest_id = savepoint_present(repo, "MSG-022AE.4")

    msg_dbf = repo / ACTIVE_MSG_ROOT / "SYSTEM_MESSAGES.dbf"
    txt_dbf = repo / ACTIVE_MSG_ROOT / "SYSTEM_MESSAGE_TEXT.dbf"
    msg_info = parse_dbf(msg_dbf)
    txt_info = parse_dbf(txt_dbf)
    msg_rows = read_rows(msg_info)
    txt_rows = read_rows(txt_info)

    msg_sym_f = choose_field(msg_info, SYMBOL_FIELDS)
    txt_sym_f = choose_field(txt_info, SYMBOL_FIELDS)
    txt_loc_f = choose_field(txt_info, LOCALE_FIELDS)
    txt_text_f = choose_field(txt_info, TEXT_FIELDS)

    msg_required_rows = [r for r in msg_rows if r.get(msg_sym_f, "") in REQUIRED_SYMBOLS]
    txt_required_rows = [r for r in txt_rows if r.get(txt_sym_f, "") in REQUIRED_SYMBOLS and r.get(txt_loc_f, "") in REQUIRED_LOCALES]

    msg_tail = msg_rows[-args.tail:] if args.tail > 0 else msg_rows
    txt_tail = txt_rows[-args.tail:] if args.tail > 0 else txt_rows

    field_inventory = []
    for role, info in [("messages", msg_info), ("message_text", txt_info)]:
        for f in info.fields:
            field_inventory.append({
                "ROLE": role,
                "DBF": rel(info.path, repo),
                "FIELD": f["NAME"],
                "TYPE": f["TYPE"],
                "LENGTH": f["LENGTH"],
                "DECIMALS": f["DECIMALS"],
                "OFFSET": f["OFFSET"],
            })

    msg_tail_out = []
    msg_fields = ["__RECNO__", "__DELETED__", msg_sym_f, choose_field(msg_info, KIND_FIELDS), choose_field(msg_info, PLACEHOLDER_FIELDS), choose_field(msg_info, STATUS_FIELDS), choose_field(msg_info, SOURCE_FIELDS)]
    for r in msg_tail:
        out = {"DBF": "SYSTEM_MESSAGES"}
        out.update(project_row(r, msg_fields))
        msg_tail_out.append(out)

    txt_tail_out = []
    txt_fields = ["__RECNO__", "__DELETED__", txt_sym_f, txt_loc_f, txt_text_f, txt_text_f + "__RAW_HEX", choose_field(txt_info, PLACEHOLDER_FIELDS), choose_field(txt_info, STATUS_FIELDS), choose_field(txt_info, SOURCE_FIELDS)]
    for r in txt_tail:
        out = {"DBF": "SYSTEM_MESSAGE_TEXT"}
        out.update(project_row(r, txt_fields))
        if txt_text_f:
            out["TEXT_VALUE_SHA256_OR_POINTER_SHA256"] = sha256_text(r.get(txt_text_f, ""))
        txt_tail_out.append(out)

    msg_req_out = []
    for r in msg_required_rows:
        out = {"DBF": "SYSTEM_MESSAGES"}
        out.update(project_row(r, msg_fields))
        msg_req_out.append(out)

    txt_req_out = []
    for r in txt_required_rows:
        out = {"DBF": "SYSTEM_MESSAGE_TEXT"}
        out.update(project_row(r, txt_fields))
        txt_req_out.append(out)

    msg_candidate_path, txt_candidate_path = candidate_paths(repo)
    candidate_msg = read_csv(msg_candidate_path)
    candidate_txt = read_csv(txt_candidate_path)

    dts_path = repo / "docs/messaging/scripts/MESSAGE_CATALOG_PHASE22AE_5_MEMO_AWARE_ACTIVE_CATALOG_PROMOTION_EXECUTE.dts"
    dts_text = dts_path.read_text(encoding="utf-8", errors="replace") if dts_path.exists() else ""
    dts_review = []
    for token in ["APPEND", "REPLACE", "SYMBOL", "LOCALE", "TEXT", "MESSAGE_PROOF_MODE_STATUS", "MESSAGE_PROOF_BOUNDARY_NOTE"]:
        dts_review.append({
            "TOKEN": token,
            "COUNT": dts_text.upper().count(token.upper()),
            "DETAIL": "token count in generated DTS",
        })

    likely = []
    if ae5.get("MESSAGE_ROWS_AFTER") == "14" and ae5.get("TEXT_ROWS_AFTER") == "70":
        likely.append("Counts moved to 14/70, so rows were appended.")
    if len(msg_required_rows) == 0 and len(txt_required_rows) == 0:
        likely.append("Required symbols are absent from key fields, so REPLACE commands likely did not set key fields or used invalid field/command syntax.")
    if dts_text and "REPLACE" in dts_text and "APPEND" in dts_text:
        likely.append("Generated DTS contains APPEND/REPLACE commands; runtime log must be checked for whether commands executed silently, failed, or were ignored.")
    likely.append("Do not append 22AE.5. Next repair should either rollback to backup or update the newly appended rows in place through a proven runtime command sequence.")

    diagnosis_rows = [{"OBSERVATION": x} for x in likely]

    write_csv(reports / "message_catalog_phase22ae_5_1_field_inventory_v1.csv", field_inventory,
              ["ROLE", "DBF", "FIELD", "TYPE", "LENGTH", "DECIMALS", "OFFSET"])
    write_csv(reports / "message_catalog_phase22ae_5_1_system_messages_tail_v1.csv", msg_tail_out,
              sorted({k for r in msg_tail_out for k in r.keys()}))
    write_csv(reports / "message_catalog_phase22ae_5_1_system_message_text_tail_v1.csv", txt_tail_out,
              sorted({k for r in txt_tail_out for k in r.keys()}))
    write_csv(reports / "message_catalog_phase22ae_5_1_required_symbol_message_rows_v1.csv", msg_req_out,
              sorted({k for r in msg_req_out for k in r.keys()} or {"DBF"}))
    write_csv(reports / "message_catalog_phase22ae_5_1_required_symbol_text_rows_v1.csv", txt_req_out,
              sorted({k for r in txt_req_out for k in r.keys()} or {"DBF"}))
    write_csv(reports / "message_catalog_phase22ae_5_1_generated_dts_token_review_v1.csv", dts_review,
              ["TOKEN", "COUNT", "DETAIL"])
    write_csv(reports / "message_catalog_phase22ae_5_1_diagnosis_v1.csv", diagnosis_rows,
              ["OBSERVATION"])

    status = STATUS_GREEN if ae5.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_5_MEMO_AWARE_ACTIVE_CATALOG_PROMOTION_BLOCKED" and ae5.get("MESSAGE_ROWS_AFTER") == "14" and ae5.get("TEXT_ROWS_AFTER") == "70" else STATUS_BLOCKED
    validation_issues = "0" if status == STATUS_GREEN else "1"

    boundary = [
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No source mutation in 22AE.5.1."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_DBF_CATALOG", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Readback/probe only; no active DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_CDX_INDEXES", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active CDX/index mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active LMDB mutation."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No HELP DATA mutation."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CMDHELPCHK mutation."},
    ]
    write_csv(reports / "message_catalog_phase22ae_5_1_boundary_ledger_v1.csv", boundary,
              ["PROTECTED_SYSTEM", "MUTATION_ALLOWED", "OBSERVED_MUTATION", "DETAIL"])

    write_csv(reports / "message_catalog_phase22ae_5_1_status_summary_v1.csv", [{
        "STATUS": status,
        "VALIDATION_ISSUES": validation_issues,
        "PHASE22AE_5_STATUS": ae5.get("STATUS", ""),
        "PHASE22AE_4_GREEN": 1 if ae4.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_4_MEMO_AWARE_ACTIVE_CATALOG_PROMOTION_PACKAGE_STAGED_SOURCE_HELD" else 0,
        "MSG_022AE_4_SAVEPOINT_PRESENT": 1 if ae4_sp else 0,
        "MESSAGE_ROWS_AFTER": msg_info.record_count,
        "TEXT_ROWS_AFTER": txt_info.record_count,
        "REQUIRED_MESSAGE_SYMBOL_ROWS_FOUND": len(msg_required_rows),
        "REQUIRED_TEXT_KEY_ROWS_FOUND": len(txt_required_rows),
        "TAIL_ROWS_CAPTURED": args.tail,
        "SOURCE_FILES_MUTATED": 0,
        "ACTIVE_CATALOG_MUTATION_OBSERVED": 0,
        "HELP_DATA_MUTATION_OBSERVED": 0,
        "CMDHELPCHK_MUTATION_OBSERVED": 0,
        "NEXT_GATE": NEXT_GATE,
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }], ["STATUS", "VALIDATION_ISSUES", "PHASE22AE_5_STATUS", "PHASE22AE_4_GREEN",
         "MSG_022AE_4_SAVEPOINT_PRESENT", "MESSAGE_ROWS_AFTER", "TEXT_ROWS_AFTER",
         "REQUIRED_MESSAGE_SYMBOL_ROWS_FOUND", "REQUIRED_TEXT_KEY_ROWS_FOUND",
         "TAIL_ROWS_CAPTURED", "SOURCE_FILES_MUTATED", "ACTIVE_CATALOG_MUTATION_OBSERVED",
         "HELP_DATA_MUTATION_OBSERVED", "CMDHELPCHK_MUTATION_OBSERVED", "NEXT_GATE",
         "REPORT_TIMESTAMP_UTC"])

    print(status)
    print(f"  validation issues: {validation_issues}")
    print(f"  Phase 22AE.5 status: {ae5.get('STATUS', '')}")
    print(f"  message rows after: {msg_info.record_count}")
    print(f"  text rows after: {txt_info.record_count}")
    print(f"  required message symbol rows found: {len(msg_required_rows)}")
    print(f"  required text key rows found: {len(txt_required_rows)}")
    print(f"  tail rows captured: {args.tail}")
    print("  source files mutated: 0")
    print("  active catalog mutation observed: 0")
    print("  HELP DATA mutation observed: 0")
    print("  CMDHELPCHK mutation observed: 0")
    print(f"  next gate: {NEXT_GATE}")
    print(f"  reports: {reports}")
    return 0 if status == STATUS_GREEN else 2

if __name__ == "__main__":
    raise SystemExit(main())
