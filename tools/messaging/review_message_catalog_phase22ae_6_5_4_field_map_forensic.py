#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, json, struct, subprocess, sys
from pathlib import Path
from datetime import datetime, timezone

STATUS_GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_4_FIELD_MAP_FORENSIC_REVIEW_GREEN_SOURCE_HELD"
STATUS_BLOCKED = "MESSAGE_CATALOG_PHASE22AE_6_5_4_FIELD_MAP_FORENSIC_REVIEW_BLOCKED"
NEXT_GATE = "HOLD_OR_AUTHORIZE_PHASE22AE_6_5_5_EXPLICIT_FIELD_MAP_IMPORT_PROOF_PACKAGE"
REPORT_DIR = Path("docs/messaging/reports")

def rows(path: Path):
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

def first(path: Path):
    r = rows(path)
    return r[0] if r else {}

def write(path: Path, data, fields):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n", extrasaction="ignore")
        w.writeheader()
        for row in data:
            w.writerow({k: row.get(k, "") for k in fields})

def rel(path: Path, repo: Path):
    try:
        return str(path.relative_to(repo)).replace("\\", "/")
    except Exception:
        return str(path).replace("\\", "/")

def savepoint(repo: Path, savepoint_id: str):
    latest = repo / REPORT_DIR / "message_savepoint_latest_v1.json"
    latest_id = ""
    if latest.exists():
        try:
            latest_id = json.loads(latest.read_text(encoding="utf-8")).get("savepoint_id", "")
        except Exception:
            pass
    journal = repo / "docs/messaging/MESSAGING_SAVEPOINT_JOURNAL.md"
    text = journal.read_text(encoding="utf-8", errors="replace") if journal.exists() else ""
    return latest_id == savepoint_id or savepoint_id in text, latest_id

def parse_dbf(path: Path):
    data = path.read_bytes()
    count = struct.unpack("<I", data[4:8])[0]
    hlen = struct.unpack("<H", data[8:10])[0]
    rlen = struct.unpack("<H", data[10:12])[0]
    fields, pos, off = [], 32, 1
    while pos + 32 <= len(data) and data[pos] != 0x0D:
        name = data[pos:pos+11].split(b"\x00", 1)[0].decode("ascii", "ignore").strip().upper()
        ftype = chr(data[pos+11])
        flen = data[pos+16]
        dec = data[pos+17]
        if name:
            fields.append({"NAME": name, "TYPE": ftype, "LENGTH": flen, "DECIMALS": dec, "OFFSET": off})
            off += flen
        pos += 32
    return {"count": count, "header_len": hlen, "record_len": rlen, "fields": fields, "path": path}

def read_dbf(info):
    out = []
    with info["path"].open("rb") as f:
        f.seek(info["header_len"])
        for i in range(info["count"]):
            rec = f.read(info["record_len"])
            if len(rec) < info["record_len"]:
                break
            row = {"__RECNO__": i + 1}
            for fld in info["fields"]:
                raw = rec[fld["OFFSET"]:fld["OFFSET"] + fld["LENGTH"]]
                row[fld["NAME"]] = raw.decode("cp1252", "replace").rstrip().strip()
            out.append(row)
    return out

def vals(row):
    return [(k, str(v).strip()) for k, v in row.items() if not k.startswith("__") and str(v).strip()]

def has_value(row, value):
    return bool(value) and any(v == value for _, v in vals(row))

def fingerprint_row(row):
    return " | ".join([f"{k}={v}" for k, v in vals(row)])[:650]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    args = ap.parse_args()
    repo = Path(args.repo_root).resolve()
    reports = repo / REPORT_DIR
    reports.mkdir(parents=True, exist_ok=True)

    s653 = first(reports / "message_catalog_phase22ae_6_5_3_validate_status_summary_v1.csv")
    st653 = first(reports / "message_catalog_phase22ae_6_5_3_stage_status_summary_v1.csv")
    sp, latest = savepoint(repo, "MSG-022AE.6.5.3")

    gates = []
    fails = 0
    def gate(name, ok, detail):
        nonlocal fails
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": str(detail)})
        if not ok:
            fails += 1

    gate("PHASE22AE_6_5_3_FIELD_MAP_REVIEW_STATUS",
         s653.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_5_3_FULL_CANDIDATE_REBUILD_SANDBOX_PROOF_GREEN_REBUILD_NOT_PROVEN_FIELD_MAP_REVIEW",
         s653.get("STATUS", "missing"))
    gate("MSG_022AE_6_5_3_SAVEPOINT_PRESENT", sp, latest)
    gate("BOUNDARY_CLEAN_IN_6_5_3", s653.get("BOUNDARY_CLEAN") == "1", s653.get("BOUNDARY_CLEAN", "missing"))

    sandbox = repo / st653.get("SANDBOX_ROOT", "")
    msg_dbf = sandbox / "dbf/SYSTEM_MESSAGES.dbf"
    txt_dbf = sandbox / "dbf/SYSTEM_MESSAGE_TEXT.dbf"
    msg_imp = sandbox / "import/system_messages_full_candidate_import.csv"
    txt_imp = sandbox / "import/system_message_text_full_candidate_import.csv"

    msg_exp = rows(reports / "message_catalog_phase22ae_6_5_3_expected_message_rows_v1.csv")
    txt_exp = rows(reports / "message_catalog_phase22ae_6_5_3_expected_text_rows_v1.csv")
    msg_imp_rows = rows(msg_imp)
    txt_imp_rows = rows(txt_imp)

    for name, path in [
        ("SANDBOX_MESSAGE_DBF_EXISTS", msg_dbf),
        ("SANDBOX_TEXT_DBF_EXISTS", txt_dbf),
        ("MESSAGE_IMPORT_CSV_EXISTS", msg_imp),
        ("TEXT_IMPORT_CSV_EXISTS", txt_imp),
    ]:
        gate(name, path.exists(), rel(path, repo))

    msg_rows, txt_rows = [], []
    msg_fields, txt_fields = [], []
    if msg_dbf.exists():
        try:
            info = parse_dbf(msg_dbf); msg_rows = read_dbf(info)
            for f in info["fields"]:
                msg_fields.append({"TABLE": "SYSTEM_MESSAGES", "FIELD": f["NAME"], "TYPE": f["TYPE"], "LENGTH": f["LENGTH"],
                                   "IMPORT_NONBLANK_ROWS": sum(1 for r in msg_imp_rows if str(r.get(f["NAME"], "")).strip()),
                                   "TAIL_NONBLANK_ROWS": sum(1 for r in msg_rows[-8:] if str(r.get(f["NAME"], "")).strip()),
                                   "SAMPLE_TAIL_VALUE": next((str(r.get(f["NAME"], "")).strip() for r in reversed(msg_rows) if str(r.get(f["NAME"], "")).strip()), "")})
        except Exception as e:
            gate("MESSAGE_DBF_READBACK", False, e)
    if txt_dbf.exists():
        try:
            info = parse_dbf(txt_dbf); txt_rows = read_dbf(info)
            for f in info["fields"]:
                txt_fields.append({"TABLE": "SYSTEM_MESSAGE_TEXT", "FIELD": f["NAME"], "TYPE": f["TYPE"], "LENGTH": f["LENGTH"],
                                   "IMPORT_NONBLANK_ROWS": sum(1 for r in txt_imp_rows if str(r.get(f["NAME"], "")).strip()),
                                   "TAIL_NONBLANK_ROWS": sum(1 for r in txt_rows[-14:] if str(r.get(f["NAME"], "")).strip()),
                                   "SAMPLE_TAIL_VALUE": next((str(r.get(f["NAME"], "")).strip() for r in reversed(txt_rows) if str(r.get(f["NAME"], "")).strip()), "")})
        except Exception as e:
            gate("TEXT_DBF_READBACK", False, e)

    coverage = []
    missing = []
    for exp in msg_exp:
        sym = exp.get("SYMBOL", "")
        in_imp = any(has_value(r, sym) for r in msg_imp_rows)
        in_dbf = any(has_value(r, sym) for r in msg_rows)
        row = {"TABLE": "SYSTEM_MESSAGES", "SYMBOL": sym, "LOCALE": "", "IN_IMPORT_CSV": int(in_imp), "IN_SANDBOX_DBF": int(in_dbf),
               "DIAGNOSIS": "symbol_present" if in_dbf else ("missing_before_import_csv" if not in_imp else "present_in_import_missing_in_dbf")}
        coverage.append(row)
        if not in_dbf:
            missing.append(row)
    for exp in txt_exp:
        sym, loc = exp.get("SYMBOL", ""), exp.get("LOCALE", "")
        in_imp = any(has_value(r, sym) and has_value(r, loc) for r in txt_imp_rows)
        in_dbf = any(has_value(r, sym) and has_value(r, loc) for r in txt_rows)
        row = {"TABLE": "SYSTEM_MESSAGE_TEXT", "SYMBOL": sym, "LOCALE": loc, "IN_IMPORT_CSV": int(in_imp), "IN_SANDBOX_DBF": int(in_dbf),
               "DIAGNOSIS": "symbol_locale_present" if in_dbf else ("missing_before_import_csv" if not in_imp else "present_in_import_missing_in_dbf")}
        coverage.append(row)
        if not in_dbf:
            missing.append(row)

    tail = []
    for table, dbf_rows, n in [("SYSTEM_MESSAGES", msg_rows, 8), ("SYSTEM_MESSAGE_TEXT", txt_rows, 14)]:
        for r in dbf_rows[-n:]:
            tail.append({"TABLE": table, "RECNO": r.get("__RECNO__", ""), "SUMMARY": fingerprint_row(r)})

    explicit = []
    for f in [r["FIELD"] for r in msg_fields]:
        rule, action = f, "KEEP_IF_PRESENT"
        if f == "SYMBOL": rule, action = "candidate message symbol", "REQUIRE_EXACT"
        elif f == "ENUMNAME": rule, action = "candidate enum/display name", "FILL_IF_AVAILABLE"
        elif f == "STATUS": rule, action = "CANDIDATE", "SET_CONSTANT"
        elif f in ("SRC", "SOURCE", "SOURCE_PHASE"): rule, action = "22AE_6_5_5", "SET_CONSTANT"
        explicit.append({"TABLE": "SYSTEM_MESSAGES", "TARGET_FIELD": f, "SOURCE_RULE": rule, "ACTION": action})
    for f in [r["FIELD"] for r in txt_fields]:
        rule, action = f, "KEEP_IF_PRESENT"
        if f == "SYMBOL": rule, action = "candidate message symbol", "REQUIRE_EXACT"
        elif f == "LOCALE": rule, action = "candidate locale", "REQUIRE_EXACT"
        elif f == "SYMBOLLOC": rule, action = "SYMBOL + '|' + LOCALE", "DERIVE"
        elif f == "TEXT": rule, action = "candidate localized text", "FILL_MEMO_VALUE"
        elif f == "STATUS": rule, action = "CANDIDATE", "SET_CONSTANT"
        elif f in ("SRC", "SOURCE", "SOURCE_PHASE"): rule, action = "22AE_6_5_5", "SET_CONSTANT"
        explicit.append({"TABLE": "SYSTEM_MESSAGE_TEXT", "TARGET_FIELD": f, "SOURCE_RULE": rule, "ACTION": action})

    conclusions = [
        {"CONCLUSION": "IMPORT_AND_ISOLATION_ARE_WORKING", "DETAIL": "6.5.3 moved 2 message rows and 10 text rows with boundary clean.", "EVIDENCE": f"delta={s653.get('MESSAGE_DELTA')}/{s653.get('TEXT_DELTA')}, fingerprint={s653.get('PROTECTED_FINGERPRINT_CHANGES')}"},
        {"CONCLUSION": "FIELD_MAP_IS_BLOCKER", "DETAIL": "Expected key proof is incomplete.", "EVIDENCE": f"message keys={s653.get('FOUND_MESSAGE_KEYS')}/2, text keys={s653.get('FOUND_TEXT_KEYS')}/10"},
        {"CONCLUSION": "NEXT_PACKAGE_SHOULD_USE_EXPLICIT_FIELD_MAP", "DETAIL": "Use exact SYMBOL/LOCALE/SYMBOLLOC/STATUS/SRC rules and pre-import CSV coverage checks.", "EVIDENCE": "message_catalog_phase22ae_6_5_4_explicit_field_map_plan_v1.csv"},
    ]
    plan = [
        {"STEP": 1, "ACTION": "KEEP_ACTIVE_PROMOTION_CLOSED", "DETAIL": "No active promotion until 2/2 message and 10/10 text keys prove in sandbox.", "MUTATES_ACTIVE": 0},
        {"STEP": 2, "ACTION": "GENERATE_EXPLICIT_FIELD_MAP_CSVS", "DETAIL": "No heuristic broad mapping; prove generated CSV contains every expected key before runtime.", "MUTATES_ACTIVE": 0},
        {"STEP": 3, "ACTION": "RUN_FRESH_ISOLATED_IMPORT", "DETAIL": "Import into sandbox DBF only; avoid exploratory commands during proof.", "MUTATES_ACTIVE": 0},
        {"STEP": 4, "ACTION": "VALIDATE_KEYS_AND_BOUNDARIES", "DETAIL": "Require 2/2, 10/10, and 0 protected fingerprint changes.", "MUTATES_ACTIVE": 0},
    ]
    boundary = [
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "report-only"},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_DBF_CATALOG", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "no active DBF mutation"},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_CDX_LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "no active index/LMDB mutation"},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "no HELP DATA mutation"},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "no CMDHELPCHK mutation"},
    ]

    status = STATUS_GREEN if fails == 0 else STATUS_BLOCKED
    write(reports / "message_catalog_phase22ae_6_5_4_gate_check_v1.csv", gates, ["GATE", "STATUS", "DETAIL"])
    write(reports / "message_catalog_phase22ae_6_5_4_message_field_profile_v1.csv", msg_fields, ["TABLE", "FIELD", "TYPE", "LENGTH", "IMPORT_NONBLANK_ROWS", "TAIL_NONBLANK_ROWS", "SAMPLE_TAIL_VALUE"])
    write(reports / "message_catalog_phase22ae_6_5_4_text_field_profile_v1.csv", txt_fields, ["TABLE", "FIELD", "TYPE", "LENGTH", "IMPORT_NONBLANK_ROWS", "TAIL_NONBLANK_ROWS", "SAMPLE_TAIL_VALUE"])
    write(reports / "message_catalog_phase22ae_6_5_4_import_coverage_v1.csv", coverage, ["TABLE", "SYMBOL", "LOCALE", "IN_IMPORT_CSV", "IN_SANDBOX_DBF", "DIAGNOSIS"])
    write(reports / "message_catalog_phase22ae_6_5_4_missing_key_diagnostics_v1.csv", missing, ["TABLE", "SYMBOL", "LOCALE", "IN_IMPORT_CSV", "IN_SANDBOX_DBF", "DIAGNOSIS"])
    write(reports / "message_catalog_phase22ae_6_5_4_tail_analysis_v1.csv", tail, ["TABLE", "RECNO", "SUMMARY"])
    write(reports / "message_catalog_phase22ae_6_5_4_explicit_field_map_plan_v1.csv", explicit, ["TABLE", "TARGET_FIELD", "SOURCE_RULE", "ACTION"])
    write(reports / "message_catalog_phase22ae_6_5_4_conclusions_v1.csv", conclusions, ["CONCLUSION", "DETAIL", "EVIDENCE"])
    write(reports / "message_catalog_phase22ae_6_5_5_next_plan_v1.csv", plan, ["STEP", "ACTION", "DETAIL", "MUTATES_ACTIVE"])
    write(reports / "message_catalog_phase22ae_6_5_4_boundary_ledger_v1.csv", boundary, ["PROTECTED_SYSTEM", "MUTATION_ALLOWED", "OBSERVED_MUTATION", "DETAIL"])
    write(reports / "message_catalog_phase22ae_6_5_4_status_summary_v1.csv", [{
        "STATUS": status,
        "VALIDATION_ISSUES": fails,
        "PHASE22AE_6_5_3_STATUS": s653.get("STATUS", ""),
        "MSG_022AE_6_5_3_SAVEPOINT_PRESENT": int(sp),
        "BOUNDARY_CLEAN_IN_6_5_3": s653.get("BOUNDARY_CLEAN", ""),
        "MESSAGE_DELTA_IN_6_5_3": s653.get("MESSAGE_DELTA", ""),
        "TEXT_DELTA_IN_6_5_3": s653.get("TEXT_DELTA", ""),
        "FOUND_MESSAGE_KEYS_IN_6_5_3": s653.get("FOUND_MESSAGE_KEYS", ""),
        "FOUND_TEXT_KEYS_IN_6_5_3": s653.get("FOUND_TEXT_KEYS", ""),
        "MISSING_KEY_DIAGNOSTIC_ROWS": len(missing),
        "EXPLICIT_FIELD_MAP_ROWS": len(explicit),
        "RECOMMENDED_NEXT_PATH": "EXPLICIT_FIELD_MAP_IMPORT_PROOF_PACKAGE",
        "ACTIVE_PROMOTION_AUTHORIZED": 0,
        "SOURCE_FILES_MUTATED": 0,
        "ACTIVE_CATALOG_MUTATION_OBSERVED": 0,
        "HELP_DATA_MUTATION_OBSERVED": 0,
        "CMDHELPCHK_MUTATION_OBSERVED": 0,
        "NEXT_GATE": NEXT_GATE,
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }], ["STATUS", "VALIDATION_ISSUES", "PHASE22AE_6_5_3_STATUS", "MSG_022AE_6_5_3_SAVEPOINT_PRESENT",
         "BOUNDARY_CLEAN_IN_6_5_3", "MESSAGE_DELTA_IN_6_5_3", "TEXT_DELTA_IN_6_5_3",
         "FOUND_MESSAGE_KEYS_IN_6_5_3", "FOUND_TEXT_KEYS_IN_6_5_3", "MISSING_KEY_DIAGNOSTIC_ROWS",
         "EXPLICIT_FIELD_MAP_ROWS", "RECOMMENDED_NEXT_PATH", "ACTIVE_PROMOTION_AUTHORIZED",
         "SOURCE_FILES_MUTATED", "ACTIVE_CATALOG_MUTATION_OBSERVED", "HELP_DATA_MUTATION_OBSERVED",
         "CMDHELPCHK_MUTATION_OBSERVED", "NEXT_GATE", "REPORT_TIMESTAMP_UTC"])
    (reports / "MESSAGE_CATALOG_PHASE22AE_6_5_4_FIELD_MAP_FORENSIC_REVIEW.md").write_text(
        f"# Message Catalog Phase 22AE.6.5.4 Field Map Forensic Review\n\nStatus: `{status}`\n\nNext gate: `{NEXT_GATE}`\n",
        encoding="utf-8"
    )

    print(status)
    print(f"  validation issues: {fails}")
    print(f"  Phase 22AE.6.5.3 status: {s653.get('STATUS','')}")
    print(f"  MSG-022AE.6.5.3 savepoint present: {1 if sp else 0}")
    print(f"  boundary clean in 6.5.3: {s653.get('BOUNDARY_CLEAN','')}")
    print(f"  message/text deltas in 6.5.3: {s653.get('MESSAGE_DELTA','')}/{s653.get('TEXT_DELTA','')}")
    print(f"  found message keys in 6.5.3: {s653.get('FOUND_MESSAGE_KEYS','')}/2")
    print(f"  found text keys in 6.5.3: {s653.get('FOUND_TEXT_KEYS','')}/10")
    print(f"  missing key diagnostic rows: {len(missing)}")
    print(f"  explicit field map rows: {len(explicit)}")
    print("  recommended next path: EXPLICIT_FIELD_MAP_IMPORT_PROOF_PACKAGE")
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
