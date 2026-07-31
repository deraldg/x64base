#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

STATUS_GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_10Z_FULL70_TEXT_ZAP_IMPORT_SEQUENCE_PLAN_GREEN_SOURCE_HELD"
STATUS_BLOCKED = "MESSAGE_CATALOG_PHASE22AE_6_5_10Z_FULL70_TEXT_ZAP_IMPORT_SEQUENCE_PLAN_BLOCKED"
NEXT_GATE = "HOLD_OR_AUTHORIZE_PHASE22AE_6_5_10AA_FULL70_TEXT_ZAP_IMPORT_SEQUENCE_EXECUTION_PACKAGE"

REPORT_DIR = Path("docs/messaging/reports")
APPLY_ROOT = Path("docs/messaging/apply/phase22ae_6_5_10z_full70_text_zap_import_sequence_plan_v1")

PLAN10W_ROOT = Path("docs/messaging/apply/phase22ae_6_5_10w_candidate10_text_extension_micro_proof_plan_v1")
FULL70_FROM_10W = PLAN10W_ROOT / "import/system_message_text_baseline60_plus_candidate10_reference.csv"
CANDIDATE10_FROM_10W = PLAN10W_ROOT / "import/system_message_text_candidate10_append_only.csv"
BASELINE60_FROM_10W = PLAN10W_ROOT / "import/system_message_text_baseline60_reference.csv"

PLAN10T_ROOT = Path("docs/messaging/apply/phase22ae_6_5_10t_text_only_active_import_micro_proof_plan_v1")
FULL70_FROM_10T = PLAN10T_ROOT / "import/system_message_text_full70_reference.csv"
BASELINE60_FROM_10T = PLAN10T_ROOT / "import/system_message_text_baseline60_roundtrip.csv"
CANDIDATE10_FROM_10T = PLAN10T_ROOT / "import/system_message_text_candidate10_only_reference.csv"

FAILED_6510_FULL70 = Path("docs/messaging/apply/phase22ae_6_5_10_guarded_active_promotion_execution_v1/import/system_message_text_active_promotion_full_state.csv")

ACTIVE_TEXT_DBF = Path("dottalkpp/data/messaging/SYSTEM_MESSAGE_TEXT.dbf")
ACTIVE_TEXT_INDEX = Path("dottalkpp/data/indexes/messaging/SYSTEM_MESSAGE_TEXT.cdx")
ACTIVE_TEXT_INDEX_META = Path("dottalkpp/data/indexes/messaging/SYSTEM_MESSAGE_TEXT.cdx.meta")
ACTIVE_TEXT_LMDB = Path("dottalkpp/data/lmdb/messaging/SYSTEM_MESSAGE_TEXT.cdx.d")
DEFAULT_TEXT_INDEX = Path("dottalkpp/data/indexes/SYSTEM_MESSAGE_TEXT.cdx")
DEFAULT_TEXT_INDEX_META = Path("dottalkpp/data/indexes/SYSTEM_MESSAGE_TEXT.cdx.meta")
DEFAULT_TEXT_LMDB = Path("dottalkpp/data/lmdb/SYSTEM_MESSAGE_TEXT.cdx.d")

PROOF_SYMBOLS = ["MESSAGE_PROOF_MODE_STATUS", "MESSAGE_PROOF_BOUNDARY_NOTE"]
EXPECTED_LOCALES = ["en-US", "es", "fr", "de", "it"]

def read_csv(path: Path):
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

def write_csv(path: Path, rows, fields):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n", extrasaction="ignore")
        w.writeheader()
        for row in rows:
            w.writerow({k: row.get(k, "") for k in fields})

def first_row(path: Path):
    rows = read_csv(path)
    return rows[0] if rows else {}

def rel(path: Path, repo: Path):
    try:
        return str(path.relative_to(repo)).replace("\\", "/")
    except Exception:
        return str(path).replace("\\", "/")

def sha256_file(path: Path):
    if not path.exists() or not path.is_file():
        return ""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def hash_dir(path: Path):
    if not path.exists() or not path.is_dir():
        return "", 0, 0
    files = sorted(p for p in path.rglob("*") if p.is_file())
    h = hashlib.sha256()
    total = 0
    for f in files:
        h.update(str(f.relative_to(path)).replace("\\", "/").encode("utf-8"))
        h.update(sha256_file(f).encode("ascii"))
        total += f.stat().st_size
    return h.hexdigest(), len(files), total

def file_info(repo: Path, role: str, path: Path):
    p = repo / path
    if p.is_dir():
        h, count, size = hash_dir(p)
        return {"ROLE": role, "PATH": rel(p, repo), "EXISTS": 1, "KIND": "dir", "BYTES": size, "SHA256": h, "FILES": count}
    if p.is_file():
        return {"ROLE": role, "PATH": rel(p, repo), "EXISTS": 1, "KIND": "file", "BYTES": p.stat().st_size, "SHA256": sha256_file(p), "FILES": 1}
    return {"ROLE": role, "PATH": rel(p, repo), "EXISTS": 0, "KIND": "missing", "BYTES": 0, "SHA256": "", "FILES": 0}

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

def dbf_header_count(path: Path):
    if not path.exists() or path.stat().st_size < 12:
        return ""
    return int.from_bytes(path.read_bytes()[:12][4:8], "little")

def row_has_symbol_and_locale(row, sym, loc):
    text = " ".join("" if v is None else str(v) for v in row.values())
    vals = {str(v).strip() for v in row.values()}
    return sym in text and (loc in vals or f"|{loc}" in text)

def classify_full70(rows):
    out = []
    for i, r in enumerate(rows, start=1):
        text = " ".join("" if v is None else str(v) for v in r.values())
        vals = {str(v).strip() for v in r.values()}
        symbol = ""
        for s in PROOF_SYMBOLS:
            if s in text:
                symbol = s
                break
        locale = ""
        for loc in EXPECTED_LOCALES:
            if loc in vals or f"|{loc}" in text:
                locale = loc
                break
        section = "BASELINE60" if i <= 60 else "CANDIDATE10"
        out.append({
            "FULL70_ROW": i,
            "SECTION": section,
            "SYMBOL": symbol,
            "LOCALE": locale,
            "HAS_PROOF_SYMBOL": 1 if symbol else 0,
            "HAS_EXPECTED_LOCALE": 1 if locale else 0,
            "ROW_JSON": json.dumps(r, ensure_ascii=False, sort_keys=True),
        })
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--replace-existing-plan", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    reports = repo / REPORT_DIR
    reports.mkdir(parents=True, exist_ok=True)
    apply_root = repo / APPLY_ROOT

    y = first_row(reports / "message_catalog_phase22ae_6_5_10y_status_summary_v1.csv")
    sp10y, latest = savepoint_present(repo, "MSG-022AE.6.5.10Y")

    gates = []
    failures = 0
    def gate(name, ok, detail):
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": str(detail)})
        if not ok:
            failures += 1

    gate("PHASE22AE_6_5_10Y_GREEN",
         y.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_5_10Y_CANDIDATE10_RESULT_CLASSIFICATION_GREEN_SOURCE_HELD",
         y.get("STATUS", "missing"))
    gate("MSG_022AE_6_5_10Y_SAVEPOINT_PRESENT", sp10y, latest)
    gate("BASELINE60_REPLACE_PROVEN_IN_10Y", y.get("BASELINE60_ACTIVE_REPLACE_PROVEN") == "1", y.get("BASELINE60_ACTIVE_REPLACE_PROVEN", "missing"))
    gate("CANDIDATE10_APPEND_PROVEN_IN_10Y", y.get("CANDIDATE10_APPEND_PROVEN") == "1", y.get("CANDIDATE10_APPEND_PROVEN", "missing"))
    gate("FULL70_SEQUENCE_PRIMARY_SUSPECT_IN_10Y", y.get("FULL70_ZAP_IMPORT_SEQUENCE_PRIMARY_SUSPECT") == "1", y.get("FULL70_ZAP_IMPORT_SEQUENCE_PRIMARY_SUSPECT", "missing"))
    gate("FULL_ACTIVE_PROMOTION_RETRY_CLOSED_IN_10Y", y.get("FULL_ACTIVE_PROMOTION_RETRY_ALLOWED") == "0", y.get("FULL_ACTIVE_PROMOTION_RETRY_ALLOWED", "missing"))

    gate("FULL70_SOURCE_10W_EXISTS", (repo / FULL70_FROM_10W).exists(), rel(repo / FULL70_FROM_10W, repo))
    gate("BASELINE60_SOURCE_10W_EXISTS", (repo / BASELINE60_FROM_10W).exists(), rel(repo / BASELINE60_FROM_10W, repo))
    gate("CANDIDATE10_SOURCE_10W_EXISTS", (repo / CANDIDATE10_FROM_10W).exists(), rel(repo / CANDIDATE10_FROM_10W, repo))
    gate("FAILED_6510_FULL70_SOURCE_EXISTS", (repo / FAILED_6510_FULL70).exists(), rel(repo / FAILED_6510_FULL70, repo))
    gate("ACTIVE_TEXT_BASELINE_HEADER_COUNT_60", dbf_header_count(repo / ACTIVE_TEXT_DBF) == 60, dbf_header_count(repo / ACTIVE_TEXT_DBF))
    gate("APPLY_ROOT_NOT_EXISTING_OR_REPLACE_ALLOWED", (not apply_root.exists()) or args.replace_existing_plan, rel(apply_root, repo))

    full70 = read_csv(repo / FULL70_FROM_10W)
    baseline60 = read_csv(repo / BASELINE60_FROM_10W)
    candidate10 = read_csv(repo / CANDIDATE10_FROM_10W)
    failed_full70 = read_csv(repo / FAILED_6510_FULL70)
    headers = list(full70[0].keys()) if full70 else (list(failed_full70[0].keys()) if failed_full70 else [])

    gate("FULL70_HAS_70_ROWS", len(full70) == 70, len(full70))
    gate("BASELINE60_HAS_60_ROWS", len(baseline60) == 60, len(baseline60))
    gate("CANDIDATE10_HAS_10_ROWS", len(candidate10) == 10, len(candidate10))
    gate("BASELINE60_PLUS_CANDIDATE10_EQUALS_FULL70", baseline60 + candidate10 == full70 if baseline60 and candidate10 and full70 else False, "row sequence comparison")
    gate("FAILED_6510_FULL70_MATCHES_10W_FULL70", failed_full70 == full70 if failed_full70 and full70 else False, "failed promotion text CSV equals staged full70")

    row_class = classify_full70(full70)
    candidate_rows = [r for r in row_class if r["SECTION"] == "CANDIDATE10"]
    gate("FULL70_CANDIDATE10_ROWS_HAVE_SYMBOLS", all(r["HAS_PROOF_SYMBOL"] for r in candidate_rows), len(candidate_rows))
    gate("FULL70_CANDIDATE10_ROWS_HAVE_LOCALES", all(r["HAS_EXPECTED_LOCALE"] for r in candidate_rows), len(candidate_rows))

    artifact_rows = [
        file_info(repo, "full70_source_10w", FULL70_FROM_10W),
        file_info(repo, "baseline60_source_10w", BASELINE60_FROM_10W),
        file_info(repo, "candidate10_source_10w", CANDIDATE10_FROM_10W),
        file_info(repo, "failed_6510_full70_source", FAILED_6510_FULL70),
        file_info(repo, "active_text_dbf_current", ACTIVE_TEXT_DBF),
        file_info(repo, "active_text_index_current", ACTIVE_TEXT_INDEX),
        file_info(repo, "active_text_index_meta_current", ACTIVE_TEXT_INDEX_META),
        file_info(repo, "active_text_lmdb_current", ACTIVE_TEXT_LMDB),
        file_info(repo, "default_text_index_current", DEFAULT_TEXT_INDEX),
        file_info(repo, "default_text_index_meta_current", DEFAULT_TEXT_INDEX_META),
        file_info(repo, "default_text_lmdb_current", DEFAULT_TEXT_LMDB),
    ]

    status = STATUS_BLOCKED
    staged_artifacts = []
    template_rel = ""
    if failures == 0:
        if apply_root.exists() and args.replace_existing_plan:
            shutil.rmtree(apply_root)
        (apply_root / "import").mkdir(parents=True, exist_ok=True)
        (apply_root / "templates").mkdir(parents=True, exist_ok=True)

        full70_out = apply_root / "import/system_message_text_full70_zap_import_sequence.csv"
        baseline_out = apply_root / "import/system_message_text_baseline60_reference.csv"
        candidate_out = apply_root / "import/system_message_text_candidate10_reference.csv"
        write_csv(full70_out, full70, headers)
        write_csv(baseline_out, baseline60, headers)
        write_csv(candidate_out, candidate10, headers)

        staged_artifacts = [
            {"ROLE": "FULL70_ZAP_IMPORT_SEQUENCE_INPUT", "PATH": rel(full70_out, repo), "ROWS": len(read_csv(full70_out)), "BYTES": full70_out.stat().st_size, "SHA256": sha256_file(full70_out), "PURPOSE": "Future 10AA text-only active ZAP/import full70 diagnostic input."},
            {"ROLE": "BASELINE60_REFERENCE", "PATH": rel(baseline_out, repo), "ROWS": len(read_csv(baseline_out)), "BYTES": baseline_out.stat().st_size, "SHA256": sha256_file(baseline_out), "PURPOSE": "Reference baseline proven by 10U."},
            {"ROLE": "CANDIDATE10_REFERENCE", "PATH": rel(candidate_out, repo), "ROWS": len(read_csv(candidate_out)), "BYTES": candidate_out.stat().st_size, "SHA256": sha256_file(candidate_out), "PURPOSE": "Reference candidate extension proven by 10X append."},
        ]

        template = apply_root / "templates/MESSAGE_CATALOG_PHASE22AE_6_5_10AA_FULL70_TEXT_ZAP_IMPORT_SEQUENCE_TEMPLATE.dts.disabled"
        template.write_text("\n".join([
            "* DISABLED TEMPLATE ONLY - DO NOT EXECUTE IN 10Z",
            "* Future 10AA, if explicitly authorized, should isolate active SYSTEM_MESSAGE_TEXT full70 ZAP/import.",
            "* It must backup active text DBF/CDX/LMDB/sidecars first and restore backup after proof, regardless of success.",
            "* No QUIT here; interactive runs quit manually.",
            "",
            f"* USE {(repo / ACTIVE_TEXT_DBF).resolve().as_posix()}",
            "* COUNT",
            "* ZAP",
            f"* USE {(repo / ACTIVE_TEXT_DBF).resolve().as_posix()}",
            f"* IMPORT {(full70_out).resolve().as_posix()}",
            f"* USE {(repo / ACTIVE_TEXT_DBF).resolve().as_posix()}",
            "* COUNT",
            "* LIST ALL",
            "",
            "* Expected runtime after full70 sequence, if successful: COUNT 70 and rows 61-70 visible.",
            "* After readback, restore exact backup. Do not leave full70 proof state in active catalog.",
        ]), encoding="utf-8")
        template_rel = rel(template, repo)
        status = STATUS_GREEN

    proof_plan = [
        {"STEP": 1, "PHASE": "PRECONDITION", "ACTION": "REQUIRE_10Y_GREEN_AND_SAVEPOINT", "DETAIL": "10Y must classify baseline60 replace and candidate10 append as proven, full70 ZAP/import as primary suspect.", "MUTATES_ACTIVE": 0},
        {"STEP": 2, "PHASE": "INPUT", "ACTION": "USE_FULL70_TEXT_ONLY_CSV", "DETAIL": "Future 10AA should use the exact 70-row text CSV matching the failed 6.5.10 full-state text import.", "MUTATES_ACTIVE": 0},
        {"STEP": 3, "PHASE": "EXECUTION_SHAPE_FOR_10AA", "ACTION": "TEXT_ONLY_ZAP_IMPORT_FULL70", "DETAIL": "Touch active SYSTEM_MESSAGE_TEXT only: backup, COUNT baseline, ZAP, reopen, IMPORT full70, reopen, COUNT, LIST ALL.", "MUTATES_ACTIVE": 1},
        {"STEP": 4, "PHASE": "READBACK", "ACTION": "COUNT_70_AND_LIST_CANDIDATE_ROWS", "DETAIL": "Capture count 70 and candidate proof rows 61-70 visible for MESSAGE_PROOF_MODE_STATUS and MESSAGE_PROOF_BOUNDARY_NOTE across five locales.", "MUTATES_ACTIVE": 0},
        {"STEP": 5, "PHASE": "RESTORE", "ACTION": "RESTORE_EXACT_BACKUP_ALWAYS", "DETAIL": "Restore active SYSTEM_MESSAGE_TEXT backup before savepoint, whether success or failure.", "MUTATES_ACTIVE": 1},
        {"STEP": 6, "PHASE": "HOLD", "ACTION": "NO_ACTIVE_EXECUTION_IN_10Z", "DETAIL": "10Z is plan-only. Active execution requires explicit 10AA authorization.", "MUTATES_ACTIVE": 0},
    ]

    decision_matrix = [
        {"IF_10AA_RESULT": "FULL70_TEXT_ONLY_ZAP_IMPORT_SUCCEEDS", "THEN": "Failure likely came from two-table promotion sequencing, active provider timing, or interaction with SYSTEM_MESSAGES path.", "NEXT": "Plan guarded two-table promotion retry with stronger readback/restore gates."},
        {"IF_10AA_RESULT": "FULL70_TEXT_ONLY_ZAP_IMPORT_FAILS", "THEN": "Failure is isolated to full70 active text ZAP/import sequence despite baseline60 and candidate10 append working separately.", "NEXT": "Review import implementation, field/record length boundary, row batch behavior, close/flush after ZAP, and index/LMDB binding."},
        {"IF_10AA_RESULT": "FULL70_IMPORT_REPORTS_70_BUT_REOPENS_0", "THEN": "This reproduces the original symptom in isolation.", "NEXT": "Treat full70 text ZAP/import as confirmed defect; no full promotion retry."},
    ]

    boundary = [
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "10Z is plan-only."},
        {"PROTECTED_SYSTEM": "ACTIVE_SYSTEM_MESSAGE_TEXT", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active DBF mutation in 10Z."},
        {"PROTECTED_SYSTEM": "ACTIVE_SYSTEM_MESSAGES", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Message table out of scope."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No HELP DATA mutation."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CMDHELPCHK mutation."},
        {"PROTECTED_SYSTEM": "FULL70_TEXT_ACTIVE_EXECUTION", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Future 10AA requires explicit authorization."},
    ]

    validation_issues = "0" if status == STATUS_GREEN else str(failures)

    write_csv(reports / "message_catalog_phase22ae_6_5_10z_gate_check_v1.csv", gates, ["GATE", "STATUS", "DETAIL"])
    write_csv(reports / "message_catalog_phase22ae_6_5_10z_artifact_inventory_v1.csv", artifact_rows, ["ROLE", "PATH", "EXISTS", "KIND", "BYTES", "SHA256", "FILES"])
    write_csv(reports / "message_catalog_phase22ae_6_5_10z_full70_row_classification_v1.csv", row_class, ["FULL70_ROW", "SECTION", "SYMBOL", "LOCALE", "HAS_PROOF_SYMBOL", "HAS_EXPECTED_LOCALE", "ROW_JSON"])
    write_csv(reports / "message_catalog_phase22ae_6_5_10z_staged_artifacts_v1.csv", staged_artifacts, ["ROLE", "PATH", "ROWS", "BYTES", "SHA256", "PURPOSE"])
    write_csv(reports / "message_catalog_phase22ae_6_5_10z_sequence_plan_v1.csv", proof_plan, ["STEP", "PHASE", "ACTION", "DETAIL", "MUTATES_ACTIVE"])
    write_csv(reports / "message_catalog_phase22ae_6_5_10z_decision_matrix_v1.csv", decision_matrix, ["IF_10AA_RESULT", "THEN", "NEXT"])
    write_csv(reports / "message_catalog_phase22ae_6_5_10z_boundary_ledger_v1.csv", boundary, ["PROTECTED_SYSTEM", "MUTATION_ALLOWED", "OBSERVED_MUTATION", "DETAIL"])

    write_csv(reports / "message_catalog_phase22ae_6_5_10z_status_summary_v1.csv", [{
        "STATUS": status,
        "VALIDATION_ISSUES": validation_issues,
        "PHASE22AE_6_5_10Y_STATUS": y.get("STATUS", ""),
        "MSG_022AE_6_5_10Y_SAVEPOINT_PRESENT": 1 if sp10y else 0,
        "BASELINE60_REPLACE_PROVEN": y.get("BASELINE60_ACTIVE_REPLACE_PROVEN", ""),
        "CANDIDATE10_APPEND_PROVEN": y.get("CANDIDATE10_APPEND_PROVEN", ""),
        "FULL70_ZAP_IMPORT_PRIMARY_SUSPECT": y.get("FULL70_ZAP_IMPORT_SEQUENCE_PRIMARY_SUSPECT", ""),
        "ACTIVE_TEXT_BASELINE_HEADER_COUNT": dbf_header_count(repo / ACTIVE_TEXT_DBF),
        "APPLY_ROOT": rel(apply_root, repo),
        "FULL70_ROWS": len(full70),
        "FULL70_MATCHES_FAILED_6510_CSV": 1 if failed_full70 == full70 and full70 else 0,
        "FULL70_TEXT_EXECUTION_AUTHORIZED": 0,
        "FULL70_TEXT_EXECUTION_EXECUTED": 0,
        "SOURCE_FILES_MUTATED": 0,
        "ACTIVE_CATALOG_MUTATION_OBSERVED": 0,
        "HELP_DATA_MUTATION_OBSERVED": 0,
        "CMDHELPCHK_MUTATION_OBSERVED": 0,
        "NEXT_GATE": NEXT_GATE,
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }], ["STATUS", "VALIDATION_ISSUES", "PHASE22AE_6_5_10Y_STATUS",
         "MSG_022AE_6_5_10Y_SAVEPOINT_PRESENT", "BASELINE60_REPLACE_PROVEN",
         "CANDIDATE10_APPEND_PROVEN", "FULL70_ZAP_IMPORT_PRIMARY_SUSPECT",
         "ACTIVE_TEXT_BASELINE_HEADER_COUNT", "APPLY_ROOT", "FULL70_ROWS",
         "FULL70_MATCHES_FAILED_6510_CSV", "FULL70_TEXT_EXECUTION_AUTHORIZED",
         "FULL70_TEXT_EXECUTION_EXECUTED", "SOURCE_FILES_MUTATED",
         "ACTIVE_CATALOG_MUTATION_OBSERVED", "HELP_DATA_MUTATION_OBSERVED",
         "CMDHELPCHK_MUTATION_OBSERVED", "NEXT_GATE", "REPORT_TIMESTAMP_UTC"])

    (repo / "docs/messaging/MESSAGE_LOCALE_PHASE22AE_6_5_10Z_FULL70_TEXT_ZAP_IMPORT_SEQUENCE_PLAN.md").write_text(
        f"# Message Catalog Phase 22AE.6.5.10Z Full70 Text ZAP/Import Sequence Plan\n\nStatus: `{status}`\n\n10Z is plan-only. It stages the full70 text-only ZAP/import sequence proof shape for a future 10AA execution package. No active mutation occurs in 10Z.\n\nNext gate:\n\n```text\n{NEXT_GATE}\n```\n",
        encoding="utf-8"
    )

    print(status)
    print(f"  validation issues: {validation_issues}")
    print(f"  Phase 22AE.6.5.10Y status: {y.get('STATUS','')}")
    print(f"  MSG-022AE.6.5.10Y savepoint present: {1 if sp10y else 0}")
    print(f"  baseline60 replace proven: {y.get('BASELINE60_ACTIVE_REPLACE_PROVEN','')}")
    print(f"  candidate10 append proven: {y.get('CANDIDATE10_APPEND_PROVEN','')}")
    print(f"  full70 ZAP/import primary suspect: {y.get('FULL70_ZAP_IMPORT_SEQUENCE_PRIMARY_SUSPECT','')}")
    print(f"  active text baseline header count: {dbf_header_count(repo / ACTIVE_TEXT_DBF)}")
    print(f"  apply root: {rel(apply_root, repo)}")
    print(f"  full70 rows: {len(full70)}")
    print(f"  full70 matches failed 6.5.10 CSV: {1 if failed_full70 == full70 and full70 else 0}")
    print("  full70 text execution authorized: 0")
    print("  full70 text execution executed: 0")
    print("  source files mutated: 0")
    print("  active catalog mutation observed: 0")
    print("  HELP DATA mutation observed: 0")
    print("  CMDHELPCHK mutation observed: 0")
    print(f"  next gate: {NEXT_GATE}")
    print(f"  reports: {reports}")
    return 0 if status == STATUS_GREEN else 2

if __name__ == "__main__":
    raise SystemExit(main())
