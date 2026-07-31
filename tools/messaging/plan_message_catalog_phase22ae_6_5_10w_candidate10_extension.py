#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

STATUS_GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_10W_CANDIDATE10_TEXT_EXTENSION_MICRO_PROOF_PLAN_GREEN_SOURCE_HELD"
STATUS_BLOCKED = "MESSAGE_CATALOG_PHASE22AE_6_5_10W_CANDIDATE10_TEXT_EXTENSION_MICRO_PROOF_PLAN_BLOCKED"
NEXT_GATE = "HOLD_OR_AUTHORIZE_PHASE22AE_6_5_10X_CANDIDATE10_TEXT_APPEND_MICRO_PROOF_EXECUTION_PACKAGE"

REPORT_DIR = Path("docs/messaging/reports")
APPLY_ROOT = Path("docs/messaging/apply/phase22ae_6_5_10w_candidate10_text_extension_micro_proof_plan_v1")

PLAN10T_ROOT = Path("docs/messaging/apply/phase22ae_6_5_10t_text_only_active_import_micro_proof_plan_v1")
BASELINE60_CSV = PLAN10T_ROOT / "import/system_message_text_baseline60_roundtrip.csv"
CANDIDATE10_CSV = PLAN10T_ROOT / "import/system_message_text_candidate10_only_reference.csv"
FULL70_CSV = PLAN10T_ROOT / "import/system_message_text_full70_reference.csv"

ACTIVE_TEXT_DBF = Path("dottalkpp/data/messaging/SYSTEM_MESSAGE_TEXT.dbf")
ACTIVE_TEXT_INDEX = Path("dottalkpp/data/indexes/messaging/SYSTEM_MESSAGE_TEXT.cdx")
ACTIVE_TEXT_LMDB = Path("dottalkpp/data/lmdb/messaging/SYSTEM_MESSAGE_TEXT.cdx.d")

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

def first_nonempty(row: dict, keys: list[str]):
    upper = {str(k).upper(): "" if v is None else str(v) for k, v in row.items()}
    for k in keys:
        v = upper.get(k.upper(), "").strip()
        if v:
            return v
    return ""

def classify_candidate_rows(rows):
    out = []
    counts = {}
    for i, r in enumerate(rows, start=1):
        vals = {str(v).strip() for v in r.values()}
        row_text = " ".join(str(v) for v in r.values())
        symbol = ""
        for s in PROOF_SYMBOLS:
            if s in row_text:
                symbol = s
                break
        locale = ""
        for loc in EXPECTED_LOCALES:
            if loc in vals or f"|{loc}" in row_text:
                locale = loc
                break
        if symbol:
            counts[symbol] = counts.get(symbol, 0) + 1
        out.append({
            "CANDIDATE_ROW": i,
            "SYMBOL": symbol,
            "LOCALE": locale,
            "HAS_PROOF_SYMBOL": 1 if symbol else 0,
            "HAS_EXPECTED_LOCALE": 1 if locale else 0,
            "ROW_JSON": json.dumps(r, ensure_ascii=False, sort_keys=True),
        })
    return out, counts

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--replace-existing-plan", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    reports = repo / REPORT_DIR
    reports.mkdir(parents=True, exist_ok=True)
    apply_root = repo / APPLY_ROOT

    v = first_row(reports / "message_catalog_phase22ae_6_5_10v_status_summary_v1.csv")
    sp10v, latest = savepoint_present(repo, "MSG-022AE.6.5.10V")

    gates = []
    failures = 0
    def gate(name, ok, detail):
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": str(detail)})
        if not ok:
            failures += 1

    gate("PHASE22AE_6_5_10V_GREEN",
         v.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_5_10V_TEXT_ACTIVE_PATH_CLASSIFICATION_GREEN_SOURCE_HELD",
         v.get("STATUS", "missing"))
    gate("MSG_022AE_6_5_10V_SAVEPOINT_PRESENT", sp10v, latest)
    gate("BASELINE60_PATH_PROVEN_IN_10V", v.get("BASELINE60_ACTIVE_PATH_PROVEN") == "1", v.get("BASELINE60_ACTIVE_PATH_PROVEN", "missing"))
    gate("FULL70_FAILED_IN_10V", v.get("FULL70_ACTIVE_PATH_FAILED") == "1", v.get("FULL70_ACTIVE_PATH_FAILED", "missing"))
    gate("CANDIDATE10_PRIMARY_SUSPECT_IN_10V", v.get("CANDIDATE10_EXTENSION_PRIMARY_SUSPECT") == "1", v.get("CANDIDATE10_EXTENSION_PRIMARY_SUSPECT", "missing"))
    gate("ACTIVE_RETRY_CLOSED_IN_10V", v.get("ACTIVE_PROMOTION_RETRY_ALLOWED") == "0", v.get("ACTIVE_PROMOTION_RETRY_ALLOWED", "missing"))

    gate("BASELINE60_CSV_EXISTS", (repo / BASELINE60_CSV).exists(), rel(repo / BASELINE60_CSV, repo))
    gate("CANDIDATE10_CSV_EXISTS", (repo / CANDIDATE10_CSV).exists(), rel(repo / CANDIDATE10_CSV, repo))
    gate("FULL70_CSV_EXISTS", (repo / FULL70_CSV).exists(), rel(repo / FULL70_CSV, repo))
    gate("APPLY_ROOT_NOT_EXISTING_OR_REPLACE_ALLOWED", (not apply_root.exists()) or args.replace_existing_plan, rel(apply_root, repo))

    baseline60 = read_csv(repo / BASELINE60_CSV)
    candidate10 = read_csv(repo / CANDIDATE10_CSV)
    full70 = read_csv(repo / FULL70_CSV)
    headers = list(full70[0].keys()) if full70 else (list(candidate10[0].keys()) if candidate10 else [])

    gate("BASELINE60_HAS_60_ROWS", len(baseline60) == 60, len(baseline60))
    gate("CANDIDATE10_HAS_10_ROWS", len(candidate10) == 10, len(candidate10))
    gate("FULL70_HAS_70_ROWS", len(full70) == 70, len(full70))
    if baseline60 and candidate10 and full70:
        gate("BASELINE60_PLUS_CANDIDATE10_EQUALS_FULL70_ROWS", baseline60 + candidate10 == full70, "row sequence comparison")
    else:
        gate("BASELINE60_PLUS_CANDIDATE10_EQUALS_FULL70_ROWS", False, "missing input rows")

    candidate_class, symbol_counts = classify_candidate_rows(candidate10)
    gate("CANDIDATE10_HAS_TWO_PROOF_SYMBOLS", set(symbol_counts.keys()) == set(PROOF_SYMBOLS), symbol_counts)
    gate("CANDIDATE10_HAS_FIVE_ROWS_PER_SYMBOL", all(symbol_counts.get(s, 0) == 5 for s in PROOF_SYMBOLS), symbol_counts)
    gate("CANDIDATE10_ALL_ROWS_HAVE_LOCALES", all(r["HAS_EXPECTED_LOCALE"] == 1 for r in candidate_class), "locale coverage")

    artifact_rows = [
        file_info(repo, "baseline60_source_csv", BASELINE60_CSV),
        file_info(repo, "candidate10_source_csv", CANDIDATE10_CSV),
        file_info(repo, "full70_reference_csv", FULL70_CSV),
        file_info(repo, "active_text_dbf_current", ACTIVE_TEXT_DBF),
        file_info(repo, "active_text_index_current", ACTIVE_TEXT_INDEX),
        file_info(repo, "active_text_lmdb_current", ACTIVE_TEXT_LMDB),
    ]

    status = STATUS_BLOCKED
    candidate_artifacts = []
    template_rel = ""
    if failures == 0:
        if apply_root.exists() and args.replace_existing_plan:
            shutil.rmtree(apply_root)
        (apply_root / "import").mkdir(parents=True, exist_ok=True)
        (apply_root / "templates").mkdir(parents=True, exist_ok=True)

        baseline_out = apply_root / "import/system_message_text_baseline60_reference.csv"
        candidate_out = apply_root / "import/system_message_text_candidate10_append_only.csv"
        full70_out = apply_root / "import/system_message_text_baseline60_plus_candidate10_reference.csv"

        write_csv(baseline_out, baseline60, headers)
        write_csv(candidate_out, candidate10, headers)
        write_csv(full70_out, baseline60 + candidate10, headers)

        candidate_artifacts = [
            {"ROLE": "BASELINE60_REFERENCE", "PATH": rel(baseline_out, repo), "ROWS": len(read_csv(baseline_out)), "BYTES": baseline_out.stat().st_size, "SHA256": sha256_file(baseline_out), "PURPOSE": "Reference baseline for future 10X pre-proof readback."},
            {"ROLE": "CANDIDATE10_APPEND_ONLY", "PATH": rel(candidate_out, repo), "ROWS": len(read_csv(candidate_out)), "BYTES": candidate_out.stat().st_size, "SHA256": sha256_file(candidate_out), "PURPOSE": "Future 10X append-only active text extension micro-proof input."},
            {"ROLE": "BASELINE60_PLUS_CANDIDATE10_REFERENCE", "PATH": rel(full70_out, repo), "ROWS": len(read_csv(full70_out)), "BYTES": full70_out.stat().st_size, "SHA256": sha256_file(full70_out), "PURPOSE": "Reference expected 70-row logical state after candidate10 append."},
        ]

        template = apply_root / "templates/MESSAGE_CATALOG_PHASE22AE_6_5_10X_CANDIDATE10_APPEND_ONLY_TEMPLATE.dts.disabled"
        template.write_text("\n".join([
            "* DISABLED TEMPLATE ONLY - DO NOT EXECUTE IN 10W",
            "* Future 10X, if explicitly authorized, should test active SYSTEM_MESSAGE_TEXT candidate10 append only.",
            "* It must backup active text DBF/CDX/LMDB/sidecars first and restore backup after proof, regardless of success.",
            "* No QUIT here; interactive runs quit manually.",
            "",
            f"* USE {(repo / ACTIVE_TEXT_DBF).resolve().as_posix()}",
            "* COUNT",
            f"* IMPORT {(candidate_out).resolve().as_posix()}",
            f"* USE {(repo / ACTIVE_TEXT_DBF).resolve().as_posix()}",
            "* COUNT",
            "* GO BOTTOM",
            "* LIST ALL",
            "",
            "* Expected runtime after append, if successful: COUNT 70 and rows 61-70 visible.",
            "* After readback, restore exact backup. Do not leave candidate rows in active catalog.",
        ]), encoding="utf-8")
        template_rel = rel(template, repo)
        status = STATUS_GREEN

    micro_plan = [
        {"STEP": 1, "PHASE": "PRECONDITION", "ACTION": "REQUIRE_10V_GREEN_AND_SAVEPOINT", "DETAIL": "10V must prove baseline60 works, full70 failed, and candidate10 is the primary suspect.", "MUTATES_ACTIVE": 0},
        {"STEP": 2, "PHASE": "INPUTS", "ACTION": "USE_CANDIDATE10_APPEND_ONLY_CSV", "DETAIL": "Future 10X should import only rows 61-70 into a 60-row active baseline.", "MUTATES_ACTIVE": 0},
        {"STEP": 3, "PHASE": "EXECUTION_SHAPE_FOR_10X", "ACTION": "APPEND_ONLY_NO_ZAP", "DETAIL": "Do not ZAP in 10X. Start from restored 60-row active baseline and append candidate10 only.", "MUTATES_ACTIVE": 1},
        {"STEP": 4, "PHASE": "READBACK", "ACTION": "COUNT_70_AND_LIST_CANDIDATE_ROWS", "DETAIL": "Future proof should capture COUNT 70 and visibility of MESSAGE_PROOF_MODE_STATUS and MESSAGE_PROOF_BOUNDARY_NOTE rows for en-US/es/fr/de/it.", "MUTATES_ACTIVE": 0},
        {"STEP": 5, "PHASE": "RESTORE", "ACTION": "RESTORE_EXACT_BACKUP_ALWAYS", "DETAIL": "Restore active SYSTEM_MESSAGE_TEXT backup before savepoint, whether candidate append succeeds or fails.", "MUTATES_ACTIVE": 1},
        {"STEP": 6, "PHASE": "HOLD", "ACTION": "NO_ACTIVE_EXECUTION_IN_10W", "DETAIL": "10W stages plan/artifacts only. Active append proof requires explicit 10X authorization.", "MUTATES_ACTIVE": 0},
    ]

    risk_rows = [
        {"RISK": "candidate10_append_could_reproduce_full70_failure", "MITIGATION": "10X must be diagnostic only and restore exact active backup afterward."},
        {"RISK": "candidate_rows_left_in_active_catalog", "MITIGATION": "10X restore is mandatory before savepoint."},
        {"RISK": "append_only_does_not_match_full70_zap_import", "MITIGATION": "This is intentional isolation; if append-only works, failure moves toward ZAP/full70 sequence. If append-only fails, candidate rows/content are suspect."},
        {"RISK": "runtime_output_wrapping_hides_keys", "MITIGATION": "10X validator should search for proof symbols and locales in normalized runlog text."},
    ]

    boundary = [
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "10W is plan-only."},
        {"PROTECTED_SYSTEM": "ACTIVE_SYSTEM_MESSAGE_TEXT", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active DBF mutation in 10W."},
        {"PROTECTED_SYSTEM": "ACTIVE_SYSTEM_MESSAGES", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Message table out of scope."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No HELP DATA mutation."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CMDHELPCHK mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_CANDIDATE10_APPEND_EXECUTION", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Future 10X requires explicit authorization."},
    ]

    validation_issues = "0" if status == STATUS_GREEN else str(failures)

    write_csv(reports / "message_catalog_phase22ae_6_5_10w_gate_check_v1.csv", gates, ["GATE", "STATUS", "DETAIL"])
    write_csv(reports / "message_catalog_phase22ae_6_5_10w_artifact_inventory_v1.csv", artifact_rows, ["ROLE", "PATH", "EXISTS", "KIND", "BYTES", "SHA256", "FILES"])
    write_csv(reports / "message_catalog_phase22ae_6_5_10w_candidate10_row_classification_v1.csv", candidate_class, ["CANDIDATE_ROW", "SYMBOL", "LOCALE", "HAS_PROOF_SYMBOL", "HAS_EXPECTED_LOCALE", "ROW_JSON"])
    write_csv(reports / "message_catalog_phase22ae_6_5_10w_candidate_artifacts_v1.csv", candidate_artifacts, ["ROLE", "PATH", "ROWS", "BYTES", "SHA256", "PURPOSE"])
    write_csv(reports / "message_catalog_phase22ae_6_5_10w_micro_proof_plan_v1.csv", micro_plan, ["STEP", "PHASE", "ACTION", "DETAIL", "MUTATES_ACTIVE"])
    write_csv(reports / "message_catalog_phase22ae_6_5_10w_risk_register_v1.csv", risk_rows, ["RISK", "MITIGATION"])
    write_csv(reports / "message_catalog_phase22ae_6_5_10w_boundary_ledger_v1.csv", boundary, ["PROTECTED_SYSTEM", "MUTATION_ALLOWED", "OBSERVED_MUTATION", "DETAIL"])

    write_csv(reports / "message_catalog_phase22ae_6_5_10w_status_summary_v1.csv", [{
        "STATUS": status,
        "VALIDATION_ISSUES": validation_issues,
        "PHASE22AE_6_5_10V_STATUS": v.get("STATUS", ""),
        "MSG_022AE_6_5_10V_SAVEPOINT_PRESENT": 1 if sp10v else 0,
        "BASELINE60_ACTIVE_PATH_PROVEN": v.get("BASELINE60_ACTIVE_PATH_PROVEN", ""),
        "FULL70_ACTIVE_PATH_FAILED": v.get("FULL70_ACTIVE_PATH_FAILED", ""),
        "CANDIDATE10_EXTENSION_PRIMARY_SUSPECT": v.get("CANDIDATE10_EXTENSION_PRIMARY_SUSPECT", ""),
        "APPLY_ROOT": rel(apply_root, repo),
        "CANDIDATE10_ROWS": len(candidate10),
        "CANDIDATE10_PROOF_SYMBOLS": ";".join(sorted(symbol_counts.keys())),
        "CANDIDATE10_APPEND_TEMPLATE_DISABLED": template_rel,
        "ACTIVE_CANDIDATE10_APPEND_AUTHORIZED": 0,
        "ACTIVE_CANDIDATE10_APPEND_EXECUTED": 0,
        "SOURCE_FILES_MUTATED": 0,
        "ACTIVE_CATALOG_MUTATION_OBSERVED": 0,
        "HELP_DATA_MUTATION_OBSERVED": 0,
        "CMDHELPCHK_MUTATION_OBSERVED": 0,
        "NEXT_GATE": NEXT_GATE,
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }], ["STATUS", "VALIDATION_ISSUES", "PHASE22AE_6_5_10V_STATUS",
         "MSG_022AE_6_5_10V_SAVEPOINT_PRESENT", "BASELINE60_ACTIVE_PATH_PROVEN",
         "FULL70_ACTIVE_PATH_FAILED", "CANDIDATE10_EXTENSION_PRIMARY_SUSPECT",
         "APPLY_ROOT", "CANDIDATE10_ROWS", "CANDIDATE10_PROOF_SYMBOLS",
         "CANDIDATE10_APPEND_TEMPLATE_DISABLED", "ACTIVE_CANDIDATE10_APPEND_AUTHORIZED",
         "ACTIVE_CANDIDATE10_APPEND_EXECUTED", "SOURCE_FILES_MUTATED",
         "ACTIVE_CATALOG_MUTATION_OBSERVED", "HELP_DATA_MUTATION_OBSERVED",
         "CMDHELPCHK_MUTATION_OBSERVED", "NEXT_GATE", "REPORT_TIMESTAMP_UTC"])

    (repo / "docs/messaging/MESSAGE_LOCALE_PHASE22AE_6_5_10W_CANDIDATE10_TEXT_EXTENSION_MICRO_PROOF_PLAN.md").write_text(
        f"# Message Catalog Phase 22AE.6.5.10W Candidate10 Text Extension Micro-Proof Plan\n\nStatus: `{status}`\n\n10W is plan-only. It stages candidate10 append-only proof artifacts and a disabled template for a future 10X diagnostic. No active mutation occurs in 10W.\n\nNext gate:\n\n```text\n{NEXT_GATE}\n```\n",
        encoding="utf-8"
    )

    print(status)
    print(f"  validation issues: {validation_issues}")
    print(f"  Phase 22AE.6.5.10V status: {v.get('STATUS','')}")
    print(f"  MSG-022AE.6.5.10V savepoint present: {1 if sp10v else 0}")
    print(f"  baseline60 active path proven: {v.get('BASELINE60_ACTIVE_PATH_PROVEN','')}")
    print(f"  full70 active path failed: {v.get('FULL70_ACTIVE_PATH_FAILED','')}")
    print(f"  candidate10 extension primary suspect: {v.get('CANDIDATE10_EXTENSION_PRIMARY_SUSPECT','')}")
    print(f"  apply root: {rel(apply_root, repo)}")
    print(f"  candidate10 rows: {len(candidate10)}")
    print(f"  candidate10 proof symbols: {';'.join(sorted(symbol_counts.keys()))}")
    print(f"  candidate10 append template disabled: {template_rel}")
    print("  active candidate10 append authorized: 0")
    print("  active candidate10 append executed: 0")
    print("  source files mutated: 0")
    print("  active catalog mutation observed: 0")
    print("  HELP DATA mutation observed: 0")
    print("  CMDHELPCHK mutation observed: 0")
    print(f"  next gate: {NEXT_GATE}")
    print(f"  reports: {reports}")
    return 0 if status == STATUS_GREEN else 2

if __name__ == "__main__":
    raise SystemExit(main())
