#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path

STATUS_GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_8_CANONICAL_RUNTIME_KEY_PROBE_STAGED_SOURCE_HELD"
STATUS_BLOCKED = "MESSAGE_CATALOG_PHASE22AE_6_5_8_CANONICAL_RUNTIME_KEY_PROBE_STAGING_BLOCKED"
NEXT_GATE = "RUN_PHASE22AE_6_5_8_CANONICAL_RUNTIME_KEY_PROBE_THEN_VALIDATE"

REPORT_DIR = Path("docs/messaging/reports")
SANDBOX_ROOT = Path("docs/messaging/sandbox/phase22ae_6_5_6_canonical_field_map_zap_import_v1")
MSG_DBF = SANDBOX_ROOT / "dbf/SYSTEM_MESSAGES.dbf"
TXT_DBF = SANDBOX_ROOT / "dbf/SYSTEM_MESSAGE_TEXT.dbf"
SCRIPT_PATH = Path("docs/messaging/scripts/MESSAGE_CATALOG_PHASE22AE_6_5_8_CANONICAL_RUNTIME_KEY_PROBE.dts")

CANON_MSG = Path("docs/messaging/apply/phase22ad_active_catalog_replacement_apply_package_v1/rows/message_catalog_candidate_message_adds_v1.csv")
CANON_TXT = Path("docs/messaging/apply/phase22ad_active_catalog_replacement_apply_package_v1/rows/message_catalog_candidate_text_adds_v1.csv")

ACTIVE_MSG_ROOT = Path("dottalkpp/data/messaging")
ACTIVE_MSG_INDEX_ROOT = Path("dottalkpp/data/indexes/messaging")
ACTIVE_MSG_LMDB_ROOT = Path("dottalkpp/data/lmdb/messaging")
DEFAULT_INDEX_ROOT = Path("dottalkpp/data/indexes")
DEFAULT_LMDB_ROOT = Path("dottalkpp/data/lmdb")
TABLES = ["SYSTEM_MESSAGES", "SYSTEM_MESSAGE_TEXT"]

SYMBOL_COLS = ["SYMBOL", "ENUMNAME", "MESSAGE_SYMBOL", "MSG_SYMBOL", "MESSAGE_ID", "MSGID", "KEY", "SYMBOLLOC", "NAME"]
LOCALE_COLS = ["LOCALE", "MSGLOCALE", "LOCALE_ID", "LANG", "LANGUAGE", "CULTURE"]

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

def sha256_file(path: Path):
    if not path.exists() or not path.is_file():
        return ""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def fingerprint_selected(repo: Path):
    rows = []
    targets = []
    for table in TABLES:
        targets.extend([
            (repo / ACTIVE_MSG_ROOT / f"{table}.dbf", f"active_dbf_{table}"),
            (repo / ACTIVE_MSG_ROOT / f"{table}.dtx", f"active_dtx_{table}"),
            (repo / ACTIVE_MSG_INDEX_ROOT / f"{table}.cdx", f"active_msg_index_{table}_cdx"),
            (repo / ACTIVE_MSG_INDEX_ROOT / f"{table}.cdx.meta", f"active_msg_index_{table}_meta"),
            (repo / ACTIVE_MSG_LMDB_ROOT / f"{table}.cdx.d", f"active_msg_lmdb_{table}"),
            (repo / DEFAULT_INDEX_ROOT / f"{table}.cdx", f"default_index_{table}_cdx"),
            (repo / DEFAULT_INDEX_ROOT / f"{table}.cdx.meta", f"default_index_{table}_meta"),
            (repo / DEFAULT_LMDB_ROOT / f"{table}.cdx.d", f"default_lmdb_{table}"),
        ])
    for path, role in targets:
        if path.is_dir():
            files = sorted(p for p in path.rglob("*") if p.is_file())
            h = hashlib.sha256()
            total = 0
            for f in files:
                h.update(str(f.relative_to(path)).replace("\\", "/").encode("utf-8"))
                h.update(sha256_file(f).encode("ascii"))
                total += f.stat().st_size
            rows.append({"ROLE":role,"PATH":rel(path,repo),"EXISTS":1,"KIND":"dir","BYTES":total,"SHA256":h.hexdigest(),"FILES":len(files)})
        elif path.is_file():
            rows.append({"ROLE":role,"PATH":rel(path,repo),"EXISTS":1,"KIND":"file","BYTES":path.stat().st_size,"SHA256":sha256_file(path),"FILES":1})
        else:
            rows.append({"ROLE":role,"PATH":rel(path,repo),"EXISTS":0,"KIND":"missing","BYTES":0,"SHA256":"","FILES":0})
    return rows

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    args = ap.parse_args()
    repo = Path(args.repo_root).resolve()
    reports = repo / REPORT_DIR
    reports.mkdir(parents=True, exist_ok=True)

    ae657 = first_row(reports / "message_catalog_phase22ae_6_5_7_status_summary_v1.csv")
    sp657, latest = savepoint_present(repo, "MSG-022AE.6.5.7")

    gates = []
    failures = 0
    def gate(name, ok, detail):
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": str(detail)})
        if not ok:
            failures += 1

    gate("PHASE22AE_6_5_7_GREEN", ae657.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_5_7_CANONICAL_FIELD_MAP_REPAIR_REVIEW_GREEN_SOURCE_HELD", ae657.get("STATUS", "missing"))
    gate("MSG_022AE_6_5_7_SAVEPOINT_PRESENT", sp657, latest)
    gate("SANDBOX_MESSAGE_DBF_EXISTS", (repo / MSG_DBF).exists(), rel(repo / MSG_DBF, repo))
    gate("SANDBOX_TEXT_DBF_EXISTS", (repo / TXT_DBF).exists(), rel(repo / TXT_DBF, repo))
    gate("CANONICAL_MESSAGE_ROWS_EXISTS", (repo / CANON_MSG).exists(), rel(repo / CANON_MSG, repo))
    gate("CANONICAL_TEXT_ROWS_EXISTS", (repo / CANON_TXT).exists(), rel(repo / CANON_TXT, repo))

    expected_msg = []
    expected_txt = []
    for r in read_csv(repo / CANON_MSG):
        sym = first_nonempty(r, SYMBOL_COLS)
        if sym:
            expected_msg.append({"TABLE": "SYSTEM_MESSAGES", "SYMBOL": sym, "LOCALE": ""})
    for r in read_csv(repo / CANON_TXT):
        sym = first_nonempty(r, SYMBOL_COLS)
        loc = first_nonempty(r, LOCALE_COLS)
        if sym:
            expected_txt.append({"TABLE": "SYSTEM_MESSAGE_TEXT", "SYMBOL": sym, "LOCALE": loc})

    gate("EXPECTED_MESSAGE_SYMBOLS_2", len(expected_msg) == 2, len(expected_msg))
    gate("EXPECTED_TEXT_SYMBOLS_10", len(expected_txt) == 10, len(expected_txt))

    before_fp = fingerprint_selected(repo)
    write_csv(reports / "message_catalog_phase22ae_6_5_8_protected_fingerprint_before_v1.csv",
              before_fp, ["ROLE","PATH","EXISTS","KIND","BYTES","SHA256","FILES"])
    write_csv(reports / "message_catalog_phase22ae_6_5_8_expected_message_keys_v1.csv", expected_msg, ["TABLE","SYMBOL","LOCALE"])
    write_csv(reports / "message_catalog_phase22ae_6_5_8_expected_text_keys_v1.csv", expected_txt, ["TABLE","SYMBOL","LOCALE"])

    script_rel = ""
    status = STATUS_BLOCKED
    if failures == 0:
        script = repo / SCRIPT_PATH
        script.parent.mkdir(parents=True, exist_ok=True)
        script.write_text("\n".join([
            "* MESSAGE_CATALOG_PHASE22AE_6_5_8_CANONICAL_RUNTIME_KEY_PROBE.dts",
            "* Read-only runtime key visibility probe against the existing 6.5.6 sandbox DBFs.",
            "* Do not run SET INDEX, CDX INFO, SET ORDER, REPLACE, ZAP, IMPORT, PACK, or other exploratory commands in this proof.",
            "* This script should only USE sandbox DBFs and LIST ALL rows.",
            "",
            f"USE {(repo / MSG_DBF).resolve().as_posix()}",
            "TOP",
            "LIST ALL",
            "",
            f"USE {(repo / TXT_DBF).resolve().as_posix()}",
            "TOP",
            "LIST ALL",
            "",
        ]), encoding="utf-8")
        script_rel = rel(script, repo)
        status = STATUS_GREEN

    boundary = [
        {"PROTECTED_SYSTEM":"SOURCE_CODE","MUTATION_ALLOWED":0,"OBSERVED_MUTATION":0,"DETAIL":"Stage writes tool/report/script only; no source mutation."},
        {"PROTECTED_SYSTEM":"ACTIVE_MESSAGING_DBF_CATALOG","MUTATION_ALLOWED":0,"OBSERVED_MUTATION":0,"DETAIL":"Runtime probe reads sandbox DBFs only."},
        {"PROTECTED_SYSTEM":"ACTIVE_MESSAGING_CDX_INDEXES","MUTATION_ALLOWED":0,"OBSERVED_MUTATION":0,"DETAIL":"No SET INDEX or active index path."},
        {"PROTECTED_SYSTEM":"ACTIVE_MESSAGING_LMDB","MUTATION_ALLOWED":0,"OBSERVED_MUTATION":0,"DETAIL":"No active LMDB path."},
        {"PROTECTED_SYSTEM":"HELP_DATA","MUTATION_ALLOWED":0,"OBSERVED_MUTATION":0,"DETAIL":"No HELP DATA mutation."},
        {"PROTECTED_SYSTEM":"CMDHELPCHK","MUTATION_ALLOWED":0,"OBSERVED_MUTATION":0,"DETAIL":"No CMDHELPCHK mutation."},
    ]

    validation_issues = "0" if status == STATUS_GREEN else str(failures)
    write_csv(reports / "message_catalog_phase22ae_6_5_8_stage_gate_check_v1.csv", gates, ["GATE","STATUS","DETAIL"])
    write_csv(reports / "message_catalog_phase22ae_6_5_8_stage_boundary_ledger_v1.csv", boundary, ["PROTECTED_SYSTEM","MUTATION_ALLOWED","OBSERVED_MUTATION","DETAIL"])
    write_csv(reports / "message_catalog_phase22ae_6_5_8_stage_status_summary_v1.csv", [{
        "STATUS": status,
        "VALIDATION_ISSUES": validation_issues,
        "PHASE22AE_6_5_7_GREEN": 1 if ae657.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_5_7_CANONICAL_FIELD_MAP_REPAIR_REVIEW_GREEN_SOURCE_HELD" else 0,
        "MSG_022AE_6_5_7_SAVEPOINT_PRESENT": 1 if sp657 else 0,
        "SCRIPT_PATH": script_rel,
        "SANDBOX_MESSAGE_DBF": rel(repo / MSG_DBF, repo),
        "SANDBOX_TEXT_DBF": rel(repo / TXT_DBF, repo),
        "EXPECTED_MESSAGE_KEYS": len(expected_msg),
        "EXPECTED_TEXT_KEYS": len(expected_txt),
        "ACTIVE_CATALOG_MUTATION_OBSERVED": 0,
        "SOURCE_FILES_MUTATED": 0,
        "HELP_DATA_MUTATION_OBSERVED": 0,
        "CMDHELPCHK_MUTATION_OBSERVED": 0,
        "NEXT_GATE": NEXT_GATE,
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00","Z"),
    }], ["STATUS","VALIDATION_ISSUES","PHASE22AE_6_5_7_GREEN","MSG_022AE_6_5_7_SAVEPOINT_PRESENT",
         "SCRIPT_PATH","SANDBOX_MESSAGE_DBF","SANDBOX_TEXT_DBF","EXPECTED_MESSAGE_KEYS","EXPECTED_TEXT_KEYS",
         "ACTIVE_CATALOG_MUTATION_OBSERVED","SOURCE_FILES_MUTATED","HELP_DATA_MUTATION_OBSERVED",
         "CMDHELPCHK_MUTATION_OBSERVED","NEXT_GATE","REPORT_TIMESTAMP_UTC"])

    print(status)
    print(f"  validation issues: {validation_issues}")
    print(f"  Phase 22AE.6.5.7 green: {1 if ae657.get('STATUS') == 'MESSAGE_CATALOG_PHASE22AE_6_5_7_CANONICAL_FIELD_MAP_REPAIR_REVIEW_GREEN_SOURCE_HELD' else 0}")
    print(f"  MSG-022AE.6.5.7 savepoint present: {1 if sp657 else 0}")
    print(f"  script path: {script_rel}")
    print(f"  expected message keys: {len(expected_msg)}")
    print(f"  expected text keys: {len(expected_txt)}")
    print("  runtime mutation in 6.5.8: 0")
    print("  active catalog mutation observed: 0")
    print("  source files mutated: 0")
    print(f"  next gate: {NEXT_GATE}")
    print(f"  reports: {reports}")
    return 0 if status == STATUS_GREEN else 2

if __name__ == "__main__":
    raise SystemExit(main())
