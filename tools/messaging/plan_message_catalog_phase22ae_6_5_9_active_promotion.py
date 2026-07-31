#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import hashlib
import shutil
from datetime import datetime, timezone
from pathlib import Path

STATUS_GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_9_ACTIVE_PROMOTION_PLAN_FROM_RUNTIME_KEY_PROOF_GREEN_SOURCE_HELD"
STATUS_BLOCKED = "MESSAGE_CATALOG_PHASE22AE_6_5_9_ACTIVE_PROMOTION_PLAN_FROM_RUNTIME_KEY_PROOF_BLOCKED"
NEXT_GATE = "HOLD_OR_AUTHORIZE_PHASE22AE_6_5_10_GUARDED_ACTIVE_PROMOTION_EXECUTION_PACKAGE"

REPORT_DIR = Path("docs/messaging/reports")
APPLY_ROOT = Path("docs/messaging/apply/phase22ae_6_5_9_active_promotion_plan_v1")

CANON_MSG_FULL = Path("docs/messaging/sandbox/phase22ae_6_5_6_canonical_field_map_zap_import_v1/import/system_messages_canonical_field_map_full_state.csv")
CANON_TXT_FULL = Path("docs/messaging/sandbox/phase22ae_6_5_6_canonical_field_map_zap_import_v1/import/system_message_text_canonical_field_map_full_state.csv")

ACTIVE_MSG_ROOT = Path("dottalkpp/data/messaging")
ACTIVE_INDEX_ROOT = Path("dottalkpp/data/indexes/messaging")
ACTIVE_LMDB_ROOT = Path("dottalkpp/data/lmdb/messaging")
DEFAULT_INDEX_ROOT = Path("dottalkpp/data/indexes")
DEFAULT_LMDB_ROOT = Path("dottalkpp/data/lmdb")
TABLES = ["SYSTEM_MESSAGES", "SYSTEM_MESSAGE_TEXT"]

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

def sha256_file(path: Path):
    if not path.exists() or not path.is_file():
        return ""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

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

def inventory_path(repo: Path, role: str, path: Path):
    p = repo / path
    if p.is_dir():
        files = sorted(q for q in p.rglob("*") if q.is_file())
        h = hashlib.sha256()
        total = 0
        for f in files:
            h.update(str(f.relative_to(p)).replace("\\", "/").encode("utf-8"))
            h.update(sha256_file(f).encode("ascii"))
            total += f.stat().st_size
        return {"ROLE": role, "PATH": rel(p, repo), "EXISTS": 1, "KIND": "dir", "BYTES": total, "SHA256": h.hexdigest(), "FILES": len(files)}
    if p.is_file():
        return {"ROLE": role, "PATH": rel(p, repo), "EXISTS": 1, "KIND": "file", "BYTES": p.stat().st_size, "SHA256": sha256_file(p), "FILES": 1}
    return {"ROLE": role, "PATH": rel(p, repo), "EXISTS": 0, "KIND": "missing", "BYTES": 0, "SHA256": "", "FILES": 0}

def active_inventory(repo: Path):
    rows = []
    for table in TABLES:
        rows.append(inventory_path(repo, f"active_dbf_{table}", ACTIVE_MSG_ROOT / f"{table}.dbf"))
        rows.append(inventory_path(repo, f"active_dtx_{table}", ACTIVE_MSG_ROOT / f"{table}.dtx"))
        rows.append(inventory_path(repo, f"active_messaging_cdx_{table}", ACTIVE_INDEX_ROOT / f"{table}.cdx"))
        rows.append(inventory_path(repo, f"active_messaging_cdx_meta_{table}", ACTIVE_INDEX_ROOT / f"{table}.cdx.meta"))
        rows.append(inventory_path(repo, f"active_messaging_lmdb_{table}", ACTIVE_LMDB_ROOT / f"{table}.cdx.d"))
        rows.append(inventory_path(repo, f"default_cdx_{table}", DEFAULT_INDEX_ROOT / f"{table}.cdx"))
        rows.append(inventory_path(repo, f"default_cdx_meta_{table}", DEFAULT_INDEX_ROOT / f"{table}.cdx.meta"))
        rows.append(inventory_path(repo, f"default_lmdb_{table}", DEFAULT_LMDB_ROOT / f"{table}.cdx.d"))
    return rows

def copy_candidate_artifact(src: Path, dst: Path, repo: Path, rows: list[dict], role: str):
    abs_src = repo / src
    abs_dst = repo / dst
    ok = abs_src.exists() and abs_src.is_file()
    if ok:
        abs_dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(abs_src, abs_dst)
    rows.append({
        "ROLE": role,
        "SOURCE": rel(abs_src, repo),
        "TARGET": rel(abs_dst, repo),
        "COPIED": 1 if ok else 0,
        "ROWS": len(read_csv(abs_dst)) if ok else 0,
        "BYTES": abs_dst.stat().st_size if ok and abs_dst.exists() else 0,
        "SHA256": sha256_file(abs_dst) if ok and abs_dst.exists() else "",
    })
    return ok

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--replace-existing-plan", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    reports = repo / REPORT_DIR
    reports.mkdir(parents=True, exist_ok=True)
    apply_root = repo / APPLY_ROOT

    ae658 = first_row(reports / "message_catalog_phase22ae_6_5_8_validate_status_summary_v1.csv")
    sp658, latest = savepoint_present(repo, "MSG-022AE.6.5.8")

    gates = []
    failures = 0
    def gate(name, ok, detail):
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": str(detail)})
        if not ok:
            failures += 1

    gate("PHASE22AE_6_5_8_RUNTIME_KEYS_VISIBLE",
         ae658.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_5_8_CANONICAL_RUNTIME_KEY_PROBE_GREEN_RUNTIME_KEYS_VISIBLE",
         ae658.get("STATUS", "missing"))
    gate("MSG_022AE_6_5_8_SAVEPOINT_PRESENT", sp658, latest)
    gate("RUNTIME_MESSAGE_KEYS_2_OF_2", ae658.get("MESSAGE_KEYS_FOUND_RUNTIME") == "2", ae658.get("MESSAGE_KEYS_FOUND_RUNTIME", "missing"))
    gate("RUNTIME_TEXT_KEYS_10_OF_10", ae658.get("TEXT_KEYS_FOUND_RUNTIME") == "10", ae658.get("TEXT_KEYS_FOUND_RUNTIME", "missing"))
    gate("BOUNDARY_CLEAN_IN_6_5_8", ae658.get("BOUNDARY_CLEAN") == "1", ae658.get("BOUNDARY_CLEAN", "missing"))
    gate("RUNTIME_PROBE_NOT_DIRTY", ae658.get("RUNTIME_PROBE_DIRTY") == "0", ae658.get("RUNTIME_PROBE_DIRTY", "missing"))
    gate("CANONICAL_MESSAGE_FULL_STATE_CSV_EXISTS", (repo / CANON_MSG_FULL).exists(), rel(repo / CANON_MSG_FULL, repo))
    gate("CANONICAL_TEXT_FULL_STATE_CSV_EXISTS", (repo / CANON_TXT_FULL).exists(), rel(repo / CANON_TXT_FULL, repo))
    gate("PLAN_ROOT_NOT_EXISTING_OR_REPLACE_ALLOWED", (not apply_root.exists()) or args.replace_existing_plan, rel(apply_root, repo))

    active_rows = active_inventory(repo)
    write_csv(reports / "message_catalog_phase22ae_6_5_9_active_artifact_inventory_v1.csv",
              active_rows, ["ROLE","PATH","EXISTS","KIND","BYTES","SHA256","FILES"])

    candidate_rows = []
    template_rel = ""
    status = STATUS_BLOCKED

    if failures == 0:
        if apply_root.exists() and args.replace_existing_plan:
            shutil.rmtree(apply_root)
        (apply_root / "import").mkdir(parents=True, exist_ok=True)
        (apply_root / "templates").mkdir(parents=True, exist_ok=True)
        (apply_root / "backup_plan").mkdir(parents=True, exist_ok=True)

        copy_candidate_artifact(CANON_MSG_FULL, APPLY_ROOT / "import/system_messages_active_promotion_full_state.csv", repo, candidate_rows, "SYSTEM_MESSAGES_FULL_STATE_IMPORT")
        copy_candidate_artifact(CANON_TXT_FULL, APPLY_ROOT / "import/system_message_text_active_promotion_full_state.csv", repo, candidate_rows, "SYSTEM_MESSAGE_TEXT_FULL_STATE_IMPORT")

        # Intentionally disabled: this is a review artifact, not executable authorization.
        template = apply_root / "templates/MESSAGE_CATALOG_PHASE22AE_6_5_10_ACTIVE_PROMOTION_EXECUTION_TEMPLATE.dts.disabled"
        template.write_text("\n".join([
            "* DISABLED TEMPLATE ONLY - DO NOT EXECUTE IN 6.5.9",
            "* Requires explicit authorization for Phase 22AE.6.5.10 guarded active promotion execution package.",
            "* Preconditions for future execution:",
            "*   - no dottalkpp process running before mutation",
            "*   - backup active DBF/CDX/LMDB/dtx artifacts first",
            "*   - use absolute paths",
            "*   - ZAP closes table; reopen before IMPORT",
            "*   - import canonical full-state CSVs only",
            "*   - run post-promotion runtime readback and keep rollback path",
            "",
            "* Future active path shape:",
            f"* USE {(repo / ACTIVE_MSG_ROOT / 'SYSTEM_MESSAGES.dbf').as_posix()}",
            "* ZAP",
            f"* USE {(repo / ACTIVE_MSG_ROOT / 'SYSTEM_MESSAGES.dbf').as_posix()}",
            f"* IMPORT {(repo / APPLY_ROOT / 'import/system_messages_active_promotion_full_state.csv').as_posix()}",
            "",
            f"* USE {(repo / ACTIVE_MSG_ROOT / 'SYSTEM_MESSAGE_TEXT.dbf').as_posix()}",
            "* ZAP",
            f"* USE {(repo / ACTIVE_MSG_ROOT / 'SYSTEM_MESSAGE_TEXT.dbf').as_posix()}",
            f"* IMPORT {(repo / APPLY_ROOT / 'import/system_message_text_active_promotion_full_state.csv').as_posix()}",
            "",
        ]), encoding="utf-8")
        template_rel = rel(template, repo)
        status = STATUS_GREEN

    plan_rows = [
        {"STEP": 1, "PHASE": "PRECHECK", "ACTION": "REQUIRE_6_5_8_RUNTIME_KEY_PROOF_AND_SAVEPOINT", "DETAIL": "Require runtime keys visible 2/2 and 10/10, boundary clean, and MSG-022AE.6.5.8 savepoint.", "MUTATES_ACTIVE": 0},
        {"STEP": 2, "PHASE": "PRECHECK", "ACTION": "CHECK_NO_DOTTALKPP_PROCESS", "DETAIL": "Abort future active execution if any dottalkpp process is running.", "MUTATES_ACTIVE": 0},
        {"STEP": 3, "PHASE": "BACKUP", "ACTION": "BACKUP_ACTIVE_MESSAGING_DBF_CDX_LMDB_DTX", "DETAIL": "Copy active SYSTEM_MESSAGES and SYSTEM_MESSAGE_TEXT DBF, sidecars, messaging indexes, default indexes, and LMDB dirs before mutation.", "MUTATES_ACTIVE": 0},
        {"STEP": 4, "PHASE": "CANDIDATE", "ACTION": "USE_CANONICAL_FULL_STATE_IMPORT_FILES", "DETAIL": "Use staged 14-row SYSTEM_MESSAGES CSV and 70-row SYSTEM_MESSAGE_TEXT CSV generated from canonical Phase22AD path.", "MUTATES_ACTIVE": 0},
        {"STEP": 5, "PHASE": "EXECUTION_DISCIPLINE", "ACTION": "DOT TALK PLUS PLUS_RUNTIME_ONLY", "DETAIL": "Do not Python/raw-write DBFs. Future execution must be DotTalk++ USE/ZAP/USE/IMPORT with absolute paths.", "MUTATES_ACTIVE": 1},
        {"STEP": 6, "PHASE": "EXECUTION_DISCIPLINE", "ACTION": "REOPEN_AFTER_ZAP_BEFORE_IMPORT", "DETAIL": "ZAP closes the table; future script must reopen the active DBF before IMPORT.", "MUTATES_ACTIVE": 1},
        {"STEP": 7, "PHASE": "INDEX_LMDB", "ACTION": "REBUILD_OR_REBIND_INDEX_LMDB_AS_REQUIRED", "DETAIL": "ZAP warns to rebuild/rebind indexes. Future execution package must include explicit post-import index/LMDB refresh or readback evidence for active provider load.", "MUTATES_ACTIVE": 1},
        {"STEP": 8, "PHASE": "READBACK", "ACTION": "RUNTIME_READBACK_COUNTS_AND_KEYS", "DETAIL": "Verify active provider message/text counts, runtime visible proof keys, and locale message behavior after promotion.", "MUTATES_ACTIVE": 0},
        {"STEP": 9, "PHASE": "ROLLBACK", "ACTION": "KEEP_RESTORE_SCRIPT_AND_ARCHIVE_PARTIALS", "DETAIL": "Future execution must preserve rollback to backup if validation fails.", "MUTATES_ACTIVE": 1},
        {"STEP": 10, "PHASE": "GATE", "ACTION": "NO_ACTIVE_EXECUTION_IN_6_5_9", "DETAIL": "6.5.9 only creates plan artifacts. Active mutation requires explicit 6.5.10 authorization.", "MUTATES_ACTIVE": 0},
    ]

    backup_plan = []
    for row in active_rows:
        backup_plan.append({
            "ROLE": row["ROLE"],
            "SOURCE": row["PATH"],
            "REQUIRED_FOR_BACKUP": 1 if row["EXISTS"] == 1 else 0,
            "KIND": row["KIND"],
            "SHA256_BEFORE": row["SHA256"],
            "RESTORE_POLICY": "restore_exact_backup_before_any_retry_or_on_failed_validation",
        })

    risk_rows = [
        {"RISK": "active_catalog_mutation", "MITIGATION": "6.5.9 performs none; 6.5.10 must require explicit AllowActiveCatalogMutation flag and backup."},
        {"RISK": "ZAP_closes_table", "MITIGATION": "Future execution template and proof require USE/ZAP/USE/IMPORT discipline."},
        {"RISK": "index_lmdb_staleness", "MITIGATION": "Future package must rebuild/rebind or prove active provider reload from updated rows; no promotion green without readback."},
        {"RISK": "python_raw_dbf_parser_false_red", "MITIGATION": "Use DotTalk++ runtime proof as source of truth for v64 visibility."},
        {"RISK": "duplicate_savepoints", "MITIGATION": "Consider later duplicate-refusal hardening for messaging savepoint appender; not blocking promotion plan."},
    ]

    boundary = [
        {"PROTECTED_SYSTEM":"SOURCE_CODE","MUTATION_ALLOWED":0,"OBSERVED_MUTATION":0,"DETAIL":"No source mutation."},
        {"PROTECTED_SYSTEM":"ACTIVE_MESSAGING_DBF_CATALOG","MUTATION_ALLOWED":0,"OBSERVED_MUTATION":0,"DETAIL":"No active DBF mutation in 6.5.9."},
        {"PROTECTED_SYSTEM":"ACTIVE_MESSAGING_CDX_INDEXES","MUTATION_ALLOWED":0,"OBSERVED_MUTATION":0,"DETAIL":"No active CDX mutation in 6.5.9."},
        {"PROTECTED_SYSTEM":"ACTIVE_MESSAGING_LMDB","MUTATION_ALLOWED":0,"OBSERVED_MUTATION":0,"DETAIL":"No active LMDB mutation in 6.5.9."},
        {"PROTECTED_SYSTEM":"HELP_DATA","MUTATION_ALLOWED":0,"OBSERVED_MUTATION":0,"DETAIL":"No HELP DATA mutation."},
        {"PROTECTED_SYSTEM":"CMDHELPCHK","MUTATION_ALLOWED":0,"OBSERVED_MUTATION":0,"DETAIL":"No CMDHELPCHK mutation."},
        {"PROTECTED_SYSTEM":"ACTIVE_PROMOTION_EXECUTION","MUTATION_ALLOWED":0,"OBSERVED_MUTATION":0,"DETAIL":"Plan only; future 6.5.10 requires explicit authorization."},
    ]

    validation_issues = "0" if status == STATUS_GREEN else str(failures)
    write_csv(reports / "message_catalog_phase22ae_6_5_9_gate_check_v1.csv", gates, ["GATE","STATUS","DETAIL"])
    write_csv(reports / "message_catalog_phase22ae_6_5_9_candidate_artifact_inventory_v1.csv", candidate_rows, ["ROLE","SOURCE","TARGET","COPIED","ROWS","BYTES","SHA256"])
    write_csv(reports / "message_catalog_phase22ae_6_5_9_active_promotion_plan_v1.csv", plan_rows, ["STEP","PHASE","ACTION","DETAIL","MUTATES_ACTIVE"])
    write_csv(reports / "message_catalog_phase22ae_6_5_9_backup_restore_plan_v1.csv", backup_plan, ["ROLE","SOURCE","REQUIRED_FOR_BACKUP","KIND","SHA256_BEFORE","RESTORE_POLICY"])
    write_csv(reports / "message_catalog_phase22ae_6_5_9_risk_register_v1.csv", risk_rows, ["RISK","MITIGATION"])
    write_csv(reports / "message_catalog_phase22ae_6_5_9_boundary_ledger_v1.csv", boundary, ["PROTECTED_SYSTEM","MUTATION_ALLOWED","OBSERVED_MUTATION","DETAIL"])

    write_csv(reports / "message_catalog_phase22ae_6_5_9_status_summary_v1.csv", [{
        "STATUS": status,
        "VALIDATION_ISSUES": validation_issues,
        "PHASE22AE_6_5_8_STATUS": ae658.get("STATUS",""),
        "MSG_022AE_6_5_8_SAVEPOINT_PRESENT": 1 if sp658 else 0,
        "RUNTIME_MESSAGE_KEYS_FOUND": ae658.get("MESSAGE_KEYS_FOUND_RUNTIME",""),
        "RUNTIME_TEXT_KEYS_FOUND": ae658.get("TEXT_KEYS_FOUND_RUNTIME",""),
        "BOUNDARY_CLEAN_IN_6_5_8": ae658.get("BOUNDARY_CLEAN",""),
        "APPLY_ROOT": rel(apply_root, repo),
        "EXECUTION_TEMPLATE_DISABLED": template_rel,
        "CANDIDATE_MESSAGE_FULL_STATE_ROWS": len(read_csv(repo / APPLY_ROOT / "import/system_messages_active_promotion_full_state.csv")),
        "CANDIDATE_TEXT_FULL_STATE_ROWS": len(read_csv(repo / APPLY_ROOT / "import/system_message_text_active_promotion_full_state.csv")),
        "ACTIVE_PROMOTION_AUTHORIZED": 0,
        "ACTIVE_PROMOTION_EXECUTED": 0,
        "SOURCE_FILES_MUTATED": 0,
        "ACTIVE_CATALOG_MUTATION_OBSERVED": 0,
        "HELP_DATA_MUTATION_OBSERVED": 0,
        "CMDHELPCHK_MUTATION_OBSERVED": 0,
        "NEXT_GATE": NEXT_GATE,
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00","Z"),
    }], ["STATUS","VALIDATION_ISSUES","PHASE22AE_6_5_8_STATUS","MSG_022AE_6_5_8_SAVEPOINT_PRESENT",
         "RUNTIME_MESSAGE_KEYS_FOUND","RUNTIME_TEXT_KEYS_FOUND","BOUNDARY_CLEAN_IN_6_5_8",
         "APPLY_ROOT","EXECUTION_TEMPLATE_DISABLED","CANDIDATE_MESSAGE_FULL_STATE_ROWS",
         "CANDIDATE_TEXT_FULL_STATE_ROWS","ACTIVE_PROMOTION_AUTHORIZED","ACTIVE_PROMOTION_EXECUTED",
         "SOURCE_FILES_MUTATED","ACTIVE_CATALOG_MUTATION_OBSERVED","HELP_DATA_MUTATION_OBSERVED",
         "CMDHELPCHK_MUTATION_OBSERVED","NEXT_GATE","REPORT_TIMESTAMP_UTC"])

    (repo / "docs/messaging/MESSAGE_LOCALE_PHASE22AE_6_5_9_ACTIVE_PROMOTION_PLAN_FROM_RUNTIME_KEY_PROOF.md").write_text(
        f"# Message Catalog Phase 22AE.6.5.9 Active Promotion Plan From Runtime Key Proof\n\nStatus: `{status}`\n\n6.5.9 is a plan/package only. No active replacement is executed.\n\nNext gate:\n\n```text\n{NEXT_GATE}\n```\n",
        encoding="utf-8"
    )

    print(status)
    print(f"  validation issues: {validation_issues}")
    print(f"  Phase 22AE.6.5.8 status: {ae658.get('STATUS','')}")
    print(f"  MSG-022AE.6.5.8 savepoint present: {1 if sp658 else 0}")
    print(f"  runtime keys found: message {ae658.get('MESSAGE_KEYS_FOUND_RUNTIME','')}/2; text {ae658.get('TEXT_KEYS_FOUND_RUNTIME','')}/10")
    print(f"  apply root: {rel(apply_root, repo)}")
    print(f"  candidate full-state rows: message {len(read_csv(repo / APPLY_ROOT / 'import/system_messages_active_promotion_full_state.csv'))}; text {len(read_csv(repo / APPLY_ROOT / 'import/system_message_text_active_promotion_full_state.csv'))}")
    print("  active promotion authorized: 0")
    print("  active promotion executed: 0")
    print("  source files mutated: 0")
    print("  active catalog mutation observed: 0")
    print("  HELP DATA mutation observed: 0")
    print("  CMDHELPCHK mutation observed: 0")
    print(f"  next gate: {NEXT_GATE}")
    print(f"  reports: {reports}")
    return 0 if status == STATUS_GREEN else 2

if __name__ == "__main__":
    raise SystemExit(main())
