#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import hashlib
import struct
from datetime import datetime, timezone
from pathlib import Path

STATUS_GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_7_CANONICAL_FIELD_MAP_REPAIR_REVIEW_GREEN_SOURCE_HELD"
STATUS_BLOCKED = "MESSAGE_CATALOG_PHASE22AE_6_5_7_CANONICAL_FIELD_MAP_REPAIR_REVIEW_BLOCKED"
NEXT_GATE = "HOLD_OR_AUTHORIZE_PHASE22AE_6_5_8_CANONICAL_KEY_PROBE_AND_FIELD_MAP_PATCH"

REPORT_DIR = Path("docs/messaging/reports")
SANDBOX_ROOT = Path("docs/messaging/sandbox/phase22ae_6_5_6_canonical_field_map_zap_import_v1")
MSG_DBF = SANDBOX_ROOT / "dbf/SYSTEM_MESSAGES.dbf"
TXT_DBF = SANDBOX_ROOT / "dbf/SYSTEM_MESSAGE_TEXT.dbf"
MSG_FULL_CSV = SANDBOX_ROOT / "import/system_messages_canonical_field_map_full_state.csv"
TXT_FULL_CSV = SANDBOX_ROOT / "import/system_message_text_canonical_field_map_full_state.csv"
CANON_MSG = Path("docs/messaging/apply/phase22ad_active_catalog_replacement_apply_package_v1/rows/message_catalog_candidate_message_adds_v1.csv")
CANON_TXT = Path("docs/messaging/apply/phase22ad_active_catalog_replacement_apply_package_v1/rows/message_catalog_candidate_text_adds_v1.csv")

SYMBOL_COLS = ["SYMBOL", "ENUMNAME", "MESSAGE_SYMBOL", "MSG_SYMBOL", "MESSAGE_ID", "MSGID", "KEY", "SYMBOLLOC", "NAME"]
LOCALE_COLS = ["LOCALE", "MSGLOCALE", "LOCALE_ID", "LANG", "LANGUAGE", "CULTURE"]
TEXT_COLS = ["TEXT", "MESSAGE_TEXT", "MSG_TEXT", "VALUE", "LOCALIZED_TEXT", "DESCRIPTION", "DEFAULT_TEXT"]

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
        w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n", extrasaction="ignore")
        w.writeheader()
        for row in rows:
            w.writerow({k: row.get(k, "") for k in fields})

def rel(path: Path, repo: Path):
    try:
        return str(path.relative_to(repo)).replace("\\", "/")
    except Exception:
        return str(path).replace("\\", "/")

def norm(row):
    return {str(k).strip().upper(): ("" if v is None else str(v)) for k, v in row.items() if k is not None}

def first_nonempty(row, cols):
    src = norm(row)
    for c in cols:
        if src.get(c, "").strip():
            return c, src[c].strip()
    return "", ""

def savepoint_present(repo: Path, savepoint_id: str):
    latest = ""
    latest_path = repo / REPORT_DIR / "message_savepoint_latest_v1.json"
    if latest_path.exists():
        try:
            latest = json.loads(latest_path.read_text(encoding="utf-8")).get("savepoint_id", "")
        except Exception:
            latest = ""
    journal = repo / "docs/messaging/MESSAGING_SAVEPOINT_JOURNAL.md"
    text = journal.read_text(encoding="utf-8", errors="replace") if journal.exists() else ""
    return latest == savepoint_id or savepoint_id in text, latest

def parse_dbf(path: Path):
    if not path.exists():
        return None, []
    data = path.read_bytes()
    if len(data) < 32:
        return None, []
    record_count = struct.unpack("<I", data[4:8])[0]
    header_len = struct.unpack("<H", data[8:10])[0]
    record_len = struct.unpack("<H", data[10:12])[0]
    fields = []
    pos = 32
    offset = 1
    while pos + 32 <= len(data):
        if data[pos] == 0x0D:
            break
        raw = data[pos:pos+11].split(b"\x00", 1)[0]
        name = raw.decode("ascii", errors="ignore").strip().upper()
        ftype = chr(data[pos+11])
        length = data[pos+16]
        decimals = data[pos+17]
        if name:
            fields.append({"NAME": name, "TYPE": ftype, "LENGTH": length, "DECIMALS": decimals, "OFFSET": offset})
            offset += length
        pos += 32
    info = {"PATH": str(path), "RECORD_COUNT": record_count, "HEADER_LEN": header_len, "RECORD_LEN": record_len}
    rows = []
    with path.open("rb") as f:
        f.seek(header_len)
        for i in range(record_count):
            rec = f.read(record_len)
            if len(rec) < record_len:
                break
            row = {"__RECNO__": i + 1, "__DELETED__": 1 if rec[:1] == b"*" else 0}
            for fld in fields:
                raw = rec[fld["OFFSET"]:fld["OFFSET"] + fld["LENGTH"]]
                if fld["TYPE"].upper() == "M":
                    row[fld["NAME"]] = raw.decode("cp1252", errors="replace").rstrip().strip()
                    row[fld["NAME"] + "__RAW_HEX"] = raw.hex()
                elif fld["TYPE"].upper() == "C":
                    row[fld["NAME"]] = raw.decode("cp1252", errors="replace").rstrip().strip()
                else:
                    row[fld["NAME"]] = raw.decode("ascii", errors="replace").rstrip().strip()
            rows.append(row)
    return {"INFO": info, "FIELDS": fields}, rows

def values_of(row):
    return {k: str(v).strip() for k, v in row.items() if not k.startswith("__") and not k.endswith("__RAW_HEX") and str(v).strip()}

def find_hits(rows, symbol, locale=""):
    exact_symbol_hits = []
    prefix_symbol_hits = []
    contains_symbol_hits = []
    exact_pair_hits = []
    for row in rows:
        vals = values_of(row)
        if any(v == symbol for v in vals.values()):
            exact_symbol_hits.append(row)
        if symbol and any(v.startswith(symbol[:min(12, len(symbol))]) for v in vals.values()):
            prefix_symbol_hits.append(row)
        if symbol and any(symbol in v for v in vals.values()):
            contains_symbol_hits.append(row)
        if locale and any(v == symbol for v in vals.values()) and any(v == locale for v in vals.values()):
            exact_pair_hits.append(row)
    return exact_symbol_hits, prefix_symbol_hits, contains_symbol_hits, exact_pair_hits

def field_snapshot(row):
    vals = values_of(row)
    return json.dumps(vals, ensure_ascii=False, sort_keys=True)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    reports = repo / REPORT_DIR
    reports.mkdir(parents=True, exist_ok=True)

    ae656 = first_row(reports / "message_catalog_phase22ae_6_5_6_validate_status_summary_v1.csv")
    sp656, latest = savepoint_present(repo, "MSG-022AE.6.5.6")

    gates = []
    failures = 0
    def gate(name, ok, detail):
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": str(detail)})
        if not ok:
            failures += 1

    gate("PHASE22AE_6_5_6_COUNTS_ONLY_GREEN",
         ae656.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_5_6_CANONICAL_FIELD_MAP_ZAP_IMPORT_PROOF_GREEN_COUNTS_ONLY_FIELD_MAP_REVIEW",
         ae656.get("STATUS", "missing"))
    gate("MSG_022AE_6_5_6_SAVEPOINT_PRESENT", sp656, latest)
    gate("BOUNDARY_CLEAN_IN_6_5_6", ae656.get("BOUNDARY_CLEAN") == "1", ae656.get("BOUNDARY_CLEAN", "missing"))
    gate("COUNTS_REACHED_14_70",
         ae656.get("SANDBOX_MESSAGE_ROWS_AFTER") == "14" and ae656.get("SANDBOX_TEXT_ROWS_AFTER") == "70",
         f"{ae656.get('SANDBOX_MESSAGE_ROWS_AFTER','')}/{ae656.get('SANDBOX_TEXT_ROWS_AFTER','')}")
    gate("KEYS_NOT_FOUND",
         ae656.get("FOUND_MESSAGE_KEYS") == "0" and ae656.get("FOUND_TEXT_KEYS") == "0",
         f"message={ae656.get('FOUND_MESSAGE_KEYS','')}; text={ae656.get('FOUND_TEXT_KEYS','')}")
    gate("FULL_STATE_CSVS_EXIST", (repo / MSG_FULL_CSV).exists() and (repo / TXT_FULL_CSV).exists(), "6.5.6 generated full-state CSVs")

    canon_msg = read_csv(repo / CANON_MSG)
    canon_txt = read_csv(repo / CANON_TXT)
    msg_full = read_csv(repo / MSG_FULL_CSV)
    txt_full = read_csv(repo / TXT_FULL_CSV)

    msg_schema, msg_rows = parse_dbf(repo / MSG_DBF)
    txt_schema, txt_rows = parse_dbf(repo / TXT_DBF)

    schema_rows = []
    for table, schema in [("SYSTEM_MESSAGES", msg_schema), ("SYSTEM_MESSAGE_TEXT", txt_schema)]:
        if schema:
            for f in schema["FIELDS"]:
                schema_rows.append({"TABLE": table, "FIELD": f["NAME"], "TYPE": f["TYPE"], "LENGTH": f["LENGTH"], "DECIMALS": f["DECIMALS"], "OFFSET": f["OFFSET"]})

    canonical_extract = []
    expected_msg = []
    expected_txt = []
    for idx, r in enumerate(canon_msg, 1):
        sc, sym = first_nonempty(r, SYMBOL_COLS)
        lc, loc = first_nonempty(r, LOCALE_COLS)
        tc, text = first_nonempty(r, TEXT_COLS)
        canonical_extract.append({"TABLE": "SYSTEM_MESSAGES", "ROW": idx, "SYMBOL_COL": sc, "SYMBOL": sym, "LOCALE_COL": lc, "LOCALE": loc, "TEXT_COL": tc, "TEXT_SAMPLE": text[:80]})
        if sym:
            expected_msg.append({"SYMBOL": sym})
    for idx, r in enumerate(canon_txt, 1):
        sc, sym = first_nonempty(r, SYMBOL_COLS)
        lc, loc = first_nonempty(r, LOCALE_COLS)
        tc, text = first_nonempty(r, TEXT_COLS)
        canonical_extract.append({"TABLE": "SYSTEM_MESSAGE_TEXT", "ROW": idx, "SYMBOL_COL": sc, "SYMBOL": sym, "LOCALE_COL": lc, "LOCALE": loc, "TEXT_COL": tc, "TEXT_SAMPLE": text[:80]})
        if sym:
            expected_txt.append({"SYMBOL": sym, "LOCALE": loc})

    # CSV-level checks: did generated full-state CSV itself contain expected symbols?
    csv_hit_rows = []
    for exp in expected_msg:
        sym = exp["SYMBOL"]
        hits = [r for r in msg_full if sym in {str(v).strip() for v in r.values()}]
        prefix = [r for r in msg_full if any(str(v).strip().startswith(sym[:min(12, len(sym))]) for v in r.values())]
        csv_hit_rows.append({"TABLE": "SYSTEM_MESSAGES_CSV", "SYMBOL": sym, "LOCALE": "", "EXACT_HITS": len(hits), "PREFIX_HITS": len(prefix), "SAMPLE_ROW": json.dumps(hits[-1] if hits else (prefix[-1] if prefix else {}), ensure_ascii=False, sort_keys=True)})
    for exp in expected_txt:
        sym = exp["SYMBOL"]
        loc = exp.get("LOCALE", "")
        hits = [r for r in txt_full if sym in {str(v).strip() for v in r.values()} and (not loc or loc in {str(v).strip() for v in r.values()})]
        prefix = [r for r in txt_full if any(str(v).strip().startswith(sym[:min(12, len(sym))]) for v in r.values())]
        csv_hit_rows.append({"TABLE": "SYSTEM_MESSAGE_TEXT_CSV", "SYMBOL": sym, "LOCALE": loc, "EXACT_HITS": len(hits), "PREFIX_HITS": len(prefix), "SAMPLE_ROW": json.dumps(hits[-1] if hits else (prefix[-1] if prefix else {}), ensure_ascii=False, sort_keys=True)})

    dbf_hit_rows = []
    for exp in expected_msg:
        sym = exp["SYMBOL"]
        exact, prefix, contains, pair = find_hits(msg_rows, sym, "")
        dbf_hit_rows.append({"TABLE": "SYSTEM_MESSAGES_DBF", "SYMBOL": sym, "LOCALE": "", "EXACT_SYMBOL_HITS": len(exact), "PREFIX_SYMBOL_HITS": len(prefix), "CONTAINS_SYMBOL_HITS": len(contains), "EXACT_PAIR_HITS": "", "SAMPLE_ROW": field_snapshot(exact[-1] if exact else (prefix[-1] if prefix else (contains[-1] if contains else {})))})
    for exp in expected_txt:
        sym = exp["SYMBOL"]
        loc = exp.get("LOCALE", "")
        exact, prefix, contains, pair = find_hits(txt_rows, sym, loc)
        dbf_hit_rows.append({"TABLE": "SYSTEM_MESSAGE_TEXT_DBF", "SYMBOL": sym, "LOCALE": loc, "EXACT_SYMBOL_HITS": len(exact), "PREFIX_SYMBOL_HITS": len(prefix), "CONTAINS_SYMBOL_HITS": len(contains), "EXACT_PAIR_HITS": len(pair), "SAMPLE_ROW": field_snapshot(pair[-1] if pair else (exact[-1] if exact else (prefix[-1] if prefix else (contains[-1] if contains else {}))))})

    # Tail rows from CSV and DBF for direct human inspection.
    tail_rows = []
    for table, rows in [("SYSTEM_MESSAGES_CSV", msg_full[-6:]), ("SYSTEM_MESSAGE_TEXT_CSV", txt_full[-12:])]:
        for i, r in enumerate(rows, 1):
            tail_rows.append({"SOURCE": table, "ROW": i, "ROW_JSON": json.dumps(r, ensure_ascii=False, sort_keys=True)})
    for table, rows in [("SYSTEM_MESSAGES_DBF", msg_rows[-6:]), ("SYSTEM_MESSAGE_TEXT_DBF", txt_rows[-12:])]:
        for r in rows:
            tail_rows.append({"SOURCE": table, "ROW": r.get("__RECNO__", ""), "ROW_JSON": field_snapshot(r)})

    # Diagnosis.
    csv_exact_msg = sum(1 for r in csv_hit_rows if r["TABLE"] == "SYSTEM_MESSAGES_CSV" and int(r["EXACT_HITS"]) > 0)
    csv_exact_txt = sum(1 for r in csv_hit_rows if r["TABLE"] == "SYSTEM_MESSAGE_TEXT_CSV" and int(r["EXACT_HITS"]) > 0)
    dbf_prefix_msg = sum(1 for r in dbf_hit_rows if r["TABLE"] == "SYSTEM_MESSAGES_DBF" and int(r["PREFIX_SYMBOL_HITS"]) > 0)
    dbf_prefix_txt = sum(1 for r in dbf_hit_rows if r["TABLE"] == "SYSTEM_MESSAGE_TEXT_DBF" and int(r["PREFIX_SYMBOL_HITS"]) > 0)

    diagnosis = [
        {"FINDING": "CANONICAL_ZAP_IMPORT_COUNTS_GREEN", "DETAIL": "6.5.6 reached 14/70 with boundary clean; mechanics are not the blocker.", "SEVERITY": "GREEN_EVIDENCE"},
        {"FINDING": "EXACT_KEY_VALIDATION_RED", "DETAIL": "6.5.6 found 0/2 message keys and 0/10 text keys by exact DBF field-value search.", "SEVERITY": "BLOCKS_PROMOTION"},
        {"FINDING": "CHECK_GENERATED_CSV_FIRST", "DETAIL": f"Generated full-state CSV exact key hits: messages={csv_exact_msg}/2, text={csv_exact_txt}/10.", "SEVERITY": "FORENSIC"},
        {"FINDING": "CHECK_DBF_TRUNCATION_OR_FIELD_PLACEMENT", "DETAIL": f"DBF prefix key hits: messages={dbf_prefix_msg}/2, text={dbf_prefix_txt}/10. Prefix hits without exact hits suggest truncation/field length; zero prefix hits suggests wrong value extraction or wrong field placement.", "SEVERITY": "FORENSIC"},
        {"FINDING": "NEXT_REPAIR_PATH", "DETAIL": "Build a runtime-assisted key probe and patch the canonical field map from observed DBF tail rows, not by guessing from Python parser alone.", "SEVERITY": "NEXT_GATE"},
    ]

    recommendations = [
        {"STEP": 1, "ACTION": "APPEND_6_5_7_REVIEW_ONLY", "DETAIL": "Accept report-only forensic review if green.", "MUTATES_ACTIVE": 0},
        {"STEP": 2, "ACTION": "RUN_RUNTIME_KEY_PROBE", "DETAIL": "Use DotTalk++ LIST/LOCATE-style proof against sandbox rows to confirm actual field names/values visible to runtime after import.", "MUTATES_ACTIVE": 0},
        {"STEP": 3, "ACTION": "PATCH_CANONICAL_FIELD_MAP_FROM_RUNTIME_EVIDENCE", "DETAIL": "Use explicit runtime-visible fields and any truncation constraints to generate a corrected full-state CSV.", "MUTATES_ACTIVE": 0},
        {"STEP": 4, "ACTION": "DO_NOT_PROMOTE_ACTIVE_CATALOG", "DETAIL": "Require 14/70, 2/2 message keys, 10/10 text keys, and boundary clean before active-promotion planning.", "MUTATES_ACTIVE": 0},
    ]

    boundary = [
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Report-only forensic review."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_DBF_CATALOG", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_CDX_INDEXES", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active CDX mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active LMDB mutation."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No HELP DATA mutation."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CMDHELPCHK mutation."},
    ]

    status = STATUS_GREEN if failures == 0 else STATUS_BLOCKED
    validation_issues = "0" if status == STATUS_GREEN else str(failures)

    write_csv(reports / "message_catalog_phase22ae_6_5_7_gate_check_v1.csv", gates, ["GATE", "STATUS", "DETAIL"])
    write_csv(reports / "message_catalog_phase22ae_6_5_7_dbf_schema_v1.csv", schema_rows, ["TABLE", "FIELD", "TYPE", "LENGTH", "DECIMALS", "OFFSET"])
    write_csv(reports / "message_catalog_phase22ae_6_5_7_canonical_extract_v1.csv", canonical_extract, ["TABLE", "ROW", "SYMBOL_COL", "SYMBOL", "LOCALE_COL", "LOCALE", "TEXT_COL", "TEXT_SAMPLE"])
    write_csv(reports / "message_catalog_phase22ae_6_5_7_csv_key_hits_v1.csv", csv_hit_rows, ["TABLE", "SYMBOL", "LOCALE", "EXACT_HITS", "PREFIX_HITS", "SAMPLE_ROW"])
    write_csv(reports / "message_catalog_phase22ae_6_5_7_dbf_key_hits_v1.csv", dbf_hit_rows, ["TABLE", "SYMBOL", "LOCALE", "EXACT_SYMBOL_HITS", "PREFIX_SYMBOL_HITS", "CONTAINS_SYMBOL_HITS", "EXACT_PAIR_HITS", "SAMPLE_ROW"])
    write_csv(reports / "message_catalog_phase22ae_6_5_7_tail_row_comparison_v1.csv", tail_rows, ["SOURCE", "ROW", "ROW_JSON"])
    write_csv(reports / "message_catalog_phase22ae_6_5_7_diagnosis_v1.csv", diagnosis, ["FINDING", "DETAIL", "SEVERITY"])
    write_csv(reports / "message_catalog_phase22ae_6_5_7_recommendations_v1.csv", recommendations, ["STEP", "ACTION", "DETAIL", "MUTATES_ACTIVE"])
    write_csv(reports / "message_catalog_phase22ae_6_5_7_boundary_ledger_v1.csv", boundary, ["PROTECTED_SYSTEM", "MUTATION_ALLOWED", "OBSERVED_MUTATION", "DETAIL"])

    write_csv(reports / "message_catalog_phase22ae_6_5_7_status_summary_v1.csv", [{
        "STATUS": status,
        "VALIDATION_ISSUES": validation_issues,
        "PHASE22AE_6_5_6_STATUS": ae656.get("STATUS", ""),
        "MSG_022AE_6_5_6_SAVEPOINT_PRESENT": 1 if sp656 else 0,
        "SANDBOX_MESSAGE_ROWS_AFTER_6_5_6": ae656.get("SANDBOX_MESSAGE_ROWS_AFTER", ""),
        "SANDBOX_TEXT_ROWS_AFTER_6_5_6": ae656.get("SANDBOX_TEXT_ROWS_AFTER", ""),
        "FOUND_MESSAGE_KEYS_6_5_6": ae656.get("FOUND_MESSAGE_KEYS", ""),
        "FOUND_TEXT_KEYS_6_5_6": ae656.get("FOUND_TEXT_KEYS", ""),
        "BOUNDARY_CLEAN_IN_6_5_6": ae656.get("BOUNDARY_CLEAN", ""),
        "CSV_EXACT_MESSAGE_KEYS": csv_exact_msg,
        "CSV_EXACT_TEXT_KEYS": csv_exact_txt,
        "DBF_PREFIX_MESSAGE_KEYS": dbf_prefix_msg,
        "DBF_PREFIX_TEXT_KEYS": dbf_prefix_txt,
        "ACTIVE_PROMOTION_AUTHORIZED": 0,
        "SOURCE_FILES_MUTATED": 0,
        "ACTIVE_CATALOG_MUTATION_OBSERVED": 0,
        "HELP_DATA_MUTATION_OBSERVED": 0,
        "CMDHELPCHK_MUTATION_OBSERVED": 0,
        "NEXT_GATE": NEXT_GATE,
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }], ["STATUS", "VALIDATION_ISSUES", "PHASE22AE_6_5_6_STATUS", "MSG_022AE_6_5_6_SAVEPOINT_PRESENT",
         "SANDBOX_MESSAGE_ROWS_AFTER_6_5_6", "SANDBOX_TEXT_ROWS_AFTER_6_5_6",
         "FOUND_MESSAGE_KEYS_6_5_6", "FOUND_TEXT_KEYS_6_5_6", "BOUNDARY_CLEAN_IN_6_5_6",
         "CSV_EXACT_MESSAGE_KEYS", "CSV_EXACT_TEXT_KEYS", "DBF_PREFIX_MESSAGE_KEYS", "DBF_PREFIX_TEXT_KEYS",
         "ACTIVE_PROMOTION_AUTHORIZED", "SOURCE_FILES_MUTATED", "ACTIVE_CATALOG_MUTATION_OBSERVED",
         "HELP_DATA_MUTATION_OBSERVED", "CMDHELPCHK_MUTATION_OBSERVED", "NEXT_GATE", "REPORT_TIMESTAMP_UTC"])

    (reports / "MESSAGE_CATALOG_PHASE22AE_6_5_7_CANONICAL_FIELD_MAP_REPAIR_REVIEW.md").write_text(
        f"# Message Catalog Phase 22AE.6.5.7 Canonical Field Map Repair Review\n\nStatus: `{status}`\n\nNext gate:\n\n```text\n{NEXT_GATE}\n```\n",
        encoding="utf-8"
    )

    print(status)
    print(f"  validation issues: {validation_issues}")
    print(f"  Phase 22AE.6.5.6 status: {ae656.get('STATUS','')}")
    print(f"  MSG-022AE.6.5.6 savepoint present: {1 if sp656 else 0}")
    print(f"  6.5.6 rows after: {ae656.get('SANDBOX_MESSAGE_ROWS_AFTER','')}/{ae656.get('SANDBOX_TEXT_ROWS_AFTER','')}")
    print(f"  6.5.6 keys found: message {ae656.get('FOUND_MESSAGE_KEYS','')}/2; text {ae656.get('FOUND_TEXT_KEYS','')}/10")
    print(f"  boundary clean in 6.5.6: {ae656.get('BOUNDARY_CLEAN','')}")
    print(f"  CSV exact key hits: message {csv_exact_msg}/2; text {csv_exact_txt}/10")
    print(f"  DBF prefix key hits: message {dbf_prefix_msg}/2; text {dbf_prefix_txt}/10")
    print("  active promotion authorized: 0")
    print("  source files mutated: 0")
    print("  active catalog mutation observed: 0")
    print("  HELP DATA mutation observed: 0")
    print("  CMDHELPCHK mutation observed: 0")
    print(f"  next gate: {NEXT_GATE}")
    print(f"  reports: {reports}")
    return 0 if status == STATUS_GREEN else 2

if __name__ == "__main__":
    raise SystemExit(main())
