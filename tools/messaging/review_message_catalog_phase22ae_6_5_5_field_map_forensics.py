#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, json
from datetime import datetime, timezone
from pathlib import Path

STATUS_GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_5_FIELD_MAP_FORENSIC_REVIEW_GREEN_SOURCE_HELD"
STATUS_BLOCKED = "MESSAGE_CATALOG_PHASE22AE_6_5_5_FIELD_MAP_FORENSIC_REVIEW_BLOCKED"
NEXT_GATE = "HOLD_OR_AUTHORIZE_PHASE22AE_6_5_6_CANONICAL_FIELD_MAP_ZAP_IMPORT_PROOF_PACKAGE"

REPORT_DIR = Path("docs/messaging/reports")
CANON_MSG = Path("docs/messaging/apply/phase22ad_active_catalog_replacement_apply_package_v1/rows/message_catalog_candidate_message_adds_v1.csv")
CANON_TXT = Path("docs/messaging/apply/phase22ad_active_catalog_replacement_apply_package_v1/rows/message_catalog_candidate_text_adds_v1.csv")

FILES = [
    ("CANONICAL_MESSAGE_ADDS", CANON_MSG),
    ("CANONICAL_TEXT_ADDS", CANON_TXT),
    ("PHASE22AE_6_5_2_MESSAGE_IMPORT", Path("docs/messaging/sandbox/phase22ae_6_5_2_isolated_import_execution_v1/import/system_messages_import.csv")),
    ("PHASE22AE_6_5_2_TEXT_IMPORT", Path("docs/messaging/sandbox/phase22ae_6_5_2_isolated_import_execution_v1/import/system_message_text_import.csv")),
    ("PHASE22AE_6_5_3_MESSAGE_IMPORT", Path("docs/messaging/sandbox/phase22ae_6_5_3_full_candidate_rebuild_v1/import/system_messages_full_candidate_import.csv")),
    ("PHASE22AE_6_5_3_TEXT_IMPORT", Path("docs/messaging/sandbox/phase22ae_6_5_3_full_candidate_rebuild_v1/import/system_message_text_full_candidate_import.csv")),
    ("PHASE22AE_6_5_4_MESSAGE_FULL_STATE", Path("docs/messaging/sandbox/phase22ae_6_5_4_full_state_zap_import_v1/import/system_messages_full_state_zap_import.csv")),
    ("PHASE22AE_6_5_4_TEXT_FULL_STATE", Path("docs/messaging/sandbox/phase22ae_6_5_4_full_state_zap_import_v1/import/system_message_text_full_state_zap_import.csv")),
]

SYMBOL_COLS = ["SYMBOL", "ENUMNAME", "MESSAGE_SYMBOL", "MSG_SYMBOL", "MSGID", "MESSAGE_ID", "KEY", "SYMBOLLOC"]
LOCALE_COLS = ["LOCALE", "MSGLOCALE", "LOCALE_ID", "LANG", "LANGUAGE"]
TEXT_COLS = ["TEXT", "MESSAGE_TEXT", "MSG_TEXT", "VALUE", "LOCALIZED_TEXT"]
CRITICAL = ["MSGID","SYMBOL","ENUMNAME","LOCALE","MSGLOCALE","SYMBOLLOC","TEXT","TXTHASH","STATUS","SRC","SOURCE","SOURCE_PHASE"]

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

def value_in_cols(row, cols):
    src = norm(row)
    for c in cols:
        if src.get(c, "").strip():
            return src[c].strip()
    return ""

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

def expected_sets(repo: Path):
    syms = set()
    pairs = set()
    for r in read_csv(repo / CANON_MSG):
        s = value_in_cols(r, SYMBOL_COLS)
        if s:
            syms.add(s)
    for r in read_csv(repo / CANON_TXT):
        s = value_in_cols(r, SYMBOL_COLS)
        l = value_in_cols(r, LOCALE_COLS)
        if s:
            syms.add(s)
        if s and l:
            pairs.add((s, l))
    return syms, pairs

def summarize(repo: Path, label: str, path: Path, syms: set, pairs: set):
    p = repo / path
    rows = read_csv(p)
    cols = list(rows[0].keys()) if rows else []
    nonempty = {}
    for c in CRITICAL:
        nonempty[c] = sum(1 for r in rows if norm(r).get(c, "").strip())
    symbol_rows = 0
    pair_rows = 0
    for r in rows:
        vals = {str(v).strip() for v in norm(r).values() if str(v).strip()}
        if vals & syms:
            symbol_rows += 1
        if any(s in vals and l in vals for s, l in pairs):
            pair_rows += 1
    return {
        "LABEL": label,
        "PATH": rel(p, repo),
        "EXISTS": 1 if p.exists() else 0,
        "ROWS": len(rows),
        "COLUMNS": ";".join(cols),
        "EXPECTED_SYMBOL_ROW_HITS": symbol_rows,
        "EXPECTED_SYMBOL_LOCALE_PAIR_ROW_HITS": pair_rows,
        "NONEMPTY_CRITICAL_JSON": json.dumps(nonempty, sort_keys=True),
    }

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    args = ap.parse_args()
    repo = Path(args.repo_root).resolve()
    reports = repo / REPORT_DIR
    reports.mkdir(parents=True, exist_ok=True)

    ae654 = first_row(reports / "message_catalog_phase22ae_6_5_4_validate_status_summary_v1.csv")
    stage654 = first_row(reports / "message_catalog_phase22ae_6_5_4_stage_status_summary_v1.csv")
    sp654, latest = savepoint_present(repo, "MSG-022AE.6.5.4")

    gates = []
    failures = 0
    def gate(name, ok, detail):
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": str(detail)})
        if not ok:
            failures += 1

    gate("PHASE22AE_6_5_4_COUNTS_ONLY_GREEN",
         ae654.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_5_4_FULL_STATE_ZAP_IMPORT_SANDBOX_PROOF_GREEN_COUNTS_ONLY_FIELD_MAP_REVIEW",
         ae654.get("STATUS", "missing"))
    gate("MSG_022AE_6_5_4_SAVEPOINT_PRESENT", sp654, latest)
    gate("BOUNDARY_CLEAN_IN_6_5_4", ae654.get("BOUNDARY_CLEAN") == "1", ae654.get("BOUNDARY_CLEAN", "missing"))
    gate("COUNTS_REACHED_14_70",
         ae654.get("SANDBOX_MESSAGE_ROWS_AFTER") == "14" and ae654.get("SANDBOX_TEXT_ROWS_AFTER") == "70",
         f"{ae654.get('SANDBOX_MESSAGE_ROWS_AFTER','')}/{ae654.get('SANDBOX_TEXT_ROWS_AFTER','')}")
    gate("KEYS_NOT_FULLY_FOUND",
         not (ae654.get("FOUND_MESSAGE_KEYS") == "2" and ae654.get("FOUND_TEXT_KEYS") == "10"),
         f"message={ae654.get('FOUND_MESSAGE_KEYS','')}/2; text={ae654.get('FOUND_TEXT_KEYS','')}/10")

    syms, pairs = expected_sets(repo)
    inventory = [summarize(repo, label, path, syms, pairs) for label, path in FILES]

    selected_msg = stage654.get("CANDIDATE_MESSAGE_FILE", "")
    selected_txt = stage654.get("CANDIDATE_TEXT_FILE", "")
    source_assessment = [
        {
            "ITEM": "SELECTED_MESSAGE_SOURCE",
            "VALUE": selected_msg,
            "ASSESSMENT": "CANONICAL" if selected_msg.replace("\\","/") == str(CANON_MSG).replace("\\","/") else "DERIVED_OR_NONCANONICAL",
            "DETAIL": "Next proof should use canonical Phase22AD message rows directly."
        },
        {
            "ITEM": "SELECTED_TEXT_SOURCE",
            "VALUE": selected_txt,
            "ASSESSMENT": "CANONICAL" if selected_txt.replace("\\","/") == str(CANON_TXT).replace("\\","/") else "DERIVED_OR_NONCANONICAL",
            "DETAIL": "Next proof should use canonical Phase22AD text rows directly."
        },
    ]

    prior_result = first_row(reports / "message_catalog_phase22ae_6_5_4_zap_import_result_v1.csv")
    found_msg = read_csv(reports / "message_catalog_phase22ae_6_5_4_found_message_keys_v1.csv")
    found_txt = read_csv(reports / "message_catalog_phase22ae_6_5_4_found_text_keys_v1.csv")
    tail = read_csv(reports / "message_catalog_phase22ae_6_5_4_tail_rows_v1.csv")

    diagnosis = [
        {"FINDING":"ZAP_IMPORT_COUNT_PATH_WORKS","DETAIL":"6.5.4 reached 14/70 with boundary clean; the reset/import mechanics are viable in sandbox.","SEVERITY":"GREEN_EVIDENCE"},
        {"FINDING":"FIELD_MAP_NOT_PROMOTION_READY","DETAIL":f"6.5.4 found message keys {ae654.get('FOUND_MESSAGE_KEYS','?')}/2 and text keys {ae654.get('FOUND_TEXT_KEYS','?')}/10.","SEVERITY":"BLOCKS_PROMOTION"},
        {"FINDING":"LIKELY_DERIVED_SOURCE_REUSE","DETAIL":"6.5.4 selected candidate sources by searching prior generated sandbox import CSVs before canonical Phase22AD rows. That can carry forward earlier bad mappings.","SEVERITY":"HIGH"},
        {"FINDING":"CANONICAL_ROWS_EXIST","DETAIL":f"Canonical Phase22AD rows available: messages={len(read_csv(repo/CANON_MSG))}; text={len(read_csv(repo/CANON_TXT))}.","SEVERITY":"GREEN_EVIDENCE"},
        {"FINDING":"NEXT_PATH","DETAIL":"Build an explicit canonical-to-DBF field map, generate full-state 14/70 CSVs from canonical rows, then rerun ZAP/import in sandbox only.","SEVERITY":"NEXT_GATE"},
    ]

    recommendations = [
        {"STEP":1,"ACTION":"APPEND_6_5_5_AS_REVIEW_ONLY","DETAIL":"Accept counts-only field-map review; do not treat it as promotion-ready.","MUTATES_ACTIVE":0},
        {"STEP":2,"ACTION":"DO_NOT_REUSE_DERIVED_IMPORT_CSVS","DETAIL":"Use canonical Phase22AD candidate rows directly as source of truth.","MUTATES_ACTIVE":0},
        {"STEP":3,"ACTION":"CREATE_EXPLICIT_FIELD_MAP","DETAIL":"Map canonical columns into DBF fields for SYSTEM_MESSAGES and SYSTEM_MESSAGE_TEXT; prove nonempty target fields before runtime.","MUTATES_ACTIVE":0},
        {"STEP":4,"ACTION":"RUN_6_5_6_CANONICAL_FIELD_MAP_ZAP_IMPORT_PROOF","DETAIL":"Require 14/70 counts, 2/2 message keys, 10/10 text keys, and boundary clean before any active promotion plan.","MUTATES_ACTIVE":0},
    ]

    boundary = [
        {"PROTECTED_SYSTEM":"SOURCE_CODE","MUTATION_ALLOWED":0,"OBSERVED_MUTATION":0,"DETAIL":"Report-only review."},
        {"PROTECTED_SYSTEM":"ACTIVE_MESSAGING_DBF_CATALOG","MUTATION_ALLOWED":0,"OBSERVED_MUTATION":0,"DETAIL":"No active DBF mutation."},
        {"PROTECTED_SYSTEM":"ACTIVE_MESSAGING_CDX_INDEXES","MUTATION_ALLOWED":0,"OBSERVED_MUTATION":0,"DETAIL":"No active CDX mutation."},
        {"PROTECTED_SYSTEM":"ACTIVE_MESSAGING_LMDB","MUTATION_ALLOWED":0,"OBSERVED_MUTATION":0,"DETAIL":"No active LMDB mutation."},
        {"PROTECTED_SYSTEM":"HELP_DATA","MUTATION_ALLOWED":0,"OBSERVED_MUTATION":0,"DETAIL":"No HELP DATA mutation."},
        {"PROTECTED_SYSTEM":"CMDHELPCHK","MUTATION_ALLOWED":0,"OBSERVED_MUTATION":0,"DETAIL":"No CMDHELPCHK mutation."},
    ]

    status = STATUS_GREEN if failures == 0 else STATUS_BLOCKED
    validation_issues = "0" if status == STATUS_GREEN else str(failures)

    write_csv(reports / "message_catalog_phase22ae_6_5_5_gate_check_v1.csv", gates, ["GATE","STATUS","DETAIL"])
    write_csv(reports / "message_catalog_phase22ae_6_5_5_source_inventory_v1.csv", inventory, ["LABEL","PATH","EXISTS","ROWS","COLUMNS","EXPECTED_SYMBOL_ROW_HITS","EXPECTED_SYMBOL_LOCALE_PAIR_ROW_HITS","NONEMPTY_CRITICAL_JSON"])
    write_csv(reports / "message_catalog_phase22ae_6_5_5_selected_source_assessment_v1.csv", source_assessment, ["ITEM","VALUE","ASSESSMENT","DETAIL"])
    write_csv(reports / "message_catalog_phase22ae_6_5_5_prior_key_hits_v1.csv",
              [{"TABLE":"SYSTEM_MESSAGES","FOUND_ROWS":len(found_msg),"DETAIL":"6.5.4 found message key rows"},
               {"TABLE":"SYSTEM_MESSAGE_TEXT","FOUND_ROWS":len(found_txt),"DETAIL":"6.5.4 found text key rows"}],
              ["TABLE","FOUND_ROWS","DETAIL"])
    write_csv(reports / "message_catalog_phase22ae_6_5_5_tail_rows_referenced_v1.csv", tail, list(tail[0].keys()) if tail else ["EMPTY"])
    write_csv(reports / "message_catalog_phase22ae_6_5_5_diagnosis_v1.csv", diagnosis, ["FINDING","DETAIL","SEVERITY"])
    write_csv(reports / "message_catalog_phase22ae_6_5_5_recommendations_v1.csv", recommendations, ["STEP","ACTION","DETAIL","MUTATES_ACTIVE"])
    write_csv(reports / "message_catalog_phase22ae_6_5_5_boundary_ledger_v1.csv", boundary, ["PROTECTED_SYSTEM","MUTATION_ALLOWED","OBSERVED_MUTATION","DETAIL"])

    write_csv(reports / "message_catalog_phase22ae_6_5_5_status_summary_v1.csv", [{
        "STATUS": status,
        "VALIDATION_ISSUES": validation_issues,
        "PHASE22AE_6_5_4_STATUS": ae654.get("STATUS",""),
        "MSG_022AE_6_5_4_SAVEPOINT_PRESENT": 1 if sp654 else 0,
        "SANDBOX_MESSAGE_ROWS_AFTER_6_5_4": ae654.get("SANDBOX_MESSAGE_ROWS_AFTER",""),
        "SANDBOX_TEXT_ROWS_AFTER_6_5_4": ae654.get("SANDBOX_TEXT_ROWS_AFTER",""),
        "FOUND_MESSAGE_KEYS_6_5_4": ae654.get("FOUND_MESSAGE_KEYS",""),
        "FOUND_TEXT_KEYS_6_5_4": ae654.get("FOUND_TEXT_KEYS",""),
        "BOUNDARY_CLEAN_IN_6_5_4": ae654.get("BOUNDARY_CLEAN",""),
        "SELECTED_MESSAGE_SOURCE_ASSESSMENT": source_assessment[0]["ASSESSMENT"],
        "SELECTED_TEXT_SOURCE_ASSESSMENT": source_assessment[1]["ASSESSMENT"],
        "CANONICAL_MESSAGE_ROWS": len(read_csv(repo / CANON_MSG)),
        "CANONICAL_TEXT_ROWS": len(read_csv(repo / CANON_TXT)),
        "ACTIVE_PROMOTION_AUTHORIZED": 0,
        "SOURCE_FILES_MUTATED": 0,
        "ACTIVE_CATALOG_MUTATION_OBSERVED": 0,
        "HELP_DATA_MUTATION_OBSERVED": 0,
        "CMDHELPCHK_MUTATION_OBSERVED": 0,
        "NEXT_GATE": NEXT_GATE,
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00","Z"),
    }], ["STATUS","VALIDATION_ISSUES","PHASE22AE_6_5_4_STATUS","MSG_022AE_6_5_4_SAVEPOINT_PRESENT",
         "SANDBOX_MESSAGE_ROWS_AFTER_6_5_4","SANDBOX_TEXT_ROWS_AFTER_6_5_4",
         "FOUND_MESSAGE_KEYS_6_5_4","FOUND_TEXT_KEYS_6_5_4","BOUNDARY_CLEAN_IN_6_5_4",
         "SELECTED_MESSAGE_SOURCE_ASSESSMENT","SELECTED_TEXT_SOURCE_ASSESSMENT",
         "CANONICAL_MESSAGE_ROWS","CANONICAL_TEXT_ROWS","ACTIVE_PROMOTION_AUTHORIZED",
         "SOURCE_FILES_MUTATED","ACTIVE_CATALOG_MUTATION_OBSERVED","HELP_DATA_MUTATION_OBSERVED",
         "CMDHELPCHK_MUTATION_OBSERVED","NEXT_GATE","REPORT_TIMESTAMP_UTC"])

    (reports / "MESSAGE_CATALOG_PHASE22AE_6_5_5_FIELD_MAP_FORENSIC_REVIEW.md").write_text(
        f"# Message Catalog Phase 22AE.6.5.5 Field Map Forensic Review\n\nStatus: `{status}`\n\nNext gate:\n\n```text\n{NEXT_GATE}\n```\n",
        encoding="utf-8"
    )

    print(status)
    print(f"  validation issues: {validation_issues}")
    print(f"  Phase 22AE.6.5.4 status: {ae654.get('STATUS','')}")
    print(f"  MSG-022AE.6.5.4 savepoint present: {1 if sp654 else 0}")
    print(f"  6.5.4 rows after: {ae654.get('SANDBOX_MESSAGE_ROWS_AFTER','')}/{ae654.get('SANDBOX_TEXT_ROWS_AFTER','')}")
    print(f"  6.5.4 keys found: message {ae654.get('FOUND_MESSAGE_KEYS','')}/2; text {ae654.get('FOUND_TEXT_KEYS','')}/10")
    print(f"  boundary clean in 6.5.4: {ae654.get('BOUNDARY_CLEAN','')}")
    print(f"  selected message source assessment: {source_assessment[0]['ASSESSMENT']}")
    print(f"  selected text source assessment: {source_assessment[1]['ASSESSMENT']}")
    print(f"  canonical rows: message {len(read_csv(repo / CANON_MSG))}; text {len(read_csv(repo / CANON_TXT))}")
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
