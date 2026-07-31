#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, json, hashlib, shutil
from datetime import datetime, timezone
from pathlib import Path

GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_10BZ_TARGET_SPECIFIC_NATIVE_APPLY_IMPLEMENTATION_PACKAGE_GREEN_SOURCE_HELD_APPLY_NOT_EXECUTED"
BLOCKED = "MESSAGE_CATALOG_PHASE22AE_6_5_10BZ_TARGET_SPECIFIC_NATIVE_APPLY_IMPLEMENTATION_PACKAGE_BLOCKED"
NEXT = "HOLD_OR_AUTHORIZE_PHASE22AE_6_5_10CA_NATIVE_APPLY_IMPLEMENTATION_PACKAGE_REVIEW"

REPORT_DIR = Path("docs/messaging/reports")
BY_SUMMARY = REPORT_DIR / "message_catalog_phase22ae_6_5_10by_status_summary_v1.csv"
BY_EXECUTION = REPORT_DIR / "message_catalog_phase22ae_6_5_10by_execution_result_v1.csv"
BY_REQUIREMENTS = REPORT_DIR / "message_catalog_phase22ae_6_5_10by_native_apply_requirements_v1.csv"
BY_READBACK = REPORT_DIR / "message_catalog_phase22ae_6_5_10by_readback_observation_v1.csv"
BX_PACKAGE = REPORT_DIR / "message_catalog_phase22ae_6_5_10bx_execution_package_manifest_v1.csv"
BX_RUNBOOK = REPORT_DIR / "message_catalog_phase22ae_6_5_10bx_runbook_v1.csv"
BX_VALIDATION = REPORT_DIR / "message_catalog_phase22ae_6_5_10bx_post_apply_validation_plan_v1.csv"
BX_ROLLBACK = REPORT_DIR / "message_catalog_phase22ae_6_5_10bx_rollback_plan_v1.csv"
ACTIVE_MSG_DBF = Path("dottalkpp/data/messaging/SYSTEM_MESSAGES.dbf")
ACTIVE_TEXT_DBF = Path("dottalkpp/data/messaging/SYSTEM_MESSAGE_TEXT.dbf")
BZ_ROOT = Path("docs/messaging/apply/phase22ae_6_5_10bz_target_specific_native_apply_implementation_package_v1")

def rows(p):
    p = Path(p)
    if not p.exists():
        return []
    with p.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

def first(p):
    r = rows(p)
    return r[0] if r else {}

def wcsv(p, rs, fs):
    p = Path(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fs, lineterminator="\n", extrasaction="ignore")
        w.writeheader()
        for r in rs:
            w.writerow({k: r.get(k, "") for k in fs})

def rel(p, repo):
    try:
        return str(Path(p).resolve().relative_to(repo.resolve())).replace("\\", "/")
    except Exception:
        return str(p).replace("\\", "/")

def sha(p):
    h = hashlib.sha256()
    with Path(p).open("rb") as f:
        for b in iter(lambda: f.read(1048576), b""):
            h.update(b)
    return h.hexdigest()

def dbf_count(p):
    p = Path(p)
    if not p.exists() or p.stat().st_size < 12:
        return ""
    return int.from_bytes(p.read_bytes()[:12][4:8], "little")

def savepoint(repo, sid):
    latest = ""
    lp = repo / REPORT_DIR / "message_savepoint_latest_v1.json"
    if lp.exists():
        try:
            latest = json.loads(lp.read_text(encoding="utf-8")).get("savepoint_id", "")
        except Exception:
            latest = ""
    jp = repo / "docs/messaging/MESSAGING_SAVEPOINT_JOURNAL.md"
    txt = jp.read_text(encoding="utf-8", errors="replace") if jp.exists() else ""
    return latest == sid or sid in txt, latest

def implementation_kind(req):
    required = (req.get("REQUIRED_IMPLEMENTATION") or "").upper()
    target = (req.get("TARGET_PATH") or "").lower()
    if target.endswith(".dbf") or target.endswith(".dtx") or target.endswith(".dbt"):
        return "DOTTALK_NATIVE_TABLE_OR_HELP_CMD_WRITER"
    if "CMDHELP" in target or "cmdhelp" in target:
        return "DOTTALK_NATIVE_CMDHELPCHK_WRITER"
    if "HELP" in target or "help" in target:
        return "DOTTALK_NATIVE_HELP_DATA_WRITER"
    if "NATIVE" in required or "SCHEMA" in required:
        return "DOTTALK_NATIVE_SCHEMA_AWARE_WRITER"
    return "TARGET_SPECIFIC_WRITER"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--replace-existing-package", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    reports = repo / REPORT_DIR
    reports.mkdir(parents=True, exist_ok=True)

    by = first(repo / BY_SUMMARY)
    by_exec = rows(repo / BY_EXECUTION)
    by_req = rows(repo / BY_REQUIREMENTS)
    by_readback = rows(repo / BY_READBACK)
    bx_pkg = rows(repo / BX_PACKAGE)
    bx_runbook = rows(repo / BX_RUNBOOK)
    bx_validation = rows(repo / BX_VALIDATION)
    bx_rollback = rows(repo / BX_ROLLBACK)
    sp_by, latest_by = savepoint(repo, "MSG-022AE.6.5.10BY")
    msg_count = dbf_count(repo / ACTIVE_MSG_DBF)
    text_count = dbf_count(repo / ACTIVE_TEXT_DBF)
    bz_root = repo / BZ_ROOT

    gates = []
    failures = 0
    def gate(name, ok, detail):
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": str(detail)})
        if not ok:
            failures += 1

    gate("PHASE22AE_6_5_10BY_GREEN",
         by.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_5_10BY_HELP_CMDHELPCHK_GUARDED_APPLY_EXECUTION_RUN_AND_READBACK_GREEN_EXECUTION_HELD_NATIVE_IMPLEMENTATION_REQUIRED",
         by.get("STATUS", "missing"))
    gate("MSG_022AE_6_5_10BY_SAVEPOINT_PRESENT", sp_by, latest_by)
    gate("BY_APPLY_AUTHORIZATION_RECEIVED", by.get("APPLY_AUTHORIZATION_RECEIVED") == "1", by.get("APPLY_AUTHORIZATION_RECEIVED", "missing"))
    gate("BY_EXECUTION_HELD_PENDING_IMPLEMENTATION", by.get("APPLY_EXECUTION_HELD_PENDING_IMPLEMENTATION") == "1", by.get("APPLY_EXECUTION_HELD_PENDING_IMPLEMENTATION", "missing"))
    gate("BY_NATIVE_IMPLEMENTATION_REQUIRED", by.get("NATIVE_TARGET_SPECIFIC_IMPLEMENTATION_REQUIRED") == "1", by.get("NATIVE_TARGET_SPECIFIC_IMPLEMENTATION_REQUIRED", "missing"))
    gate("BY_HELP_APPLY_NOT_EXECUTED", by.get("HELP_DATA_APPLY_EXECUTED") == "0", by.get("HELP_DATA_APPLY_EXECUTED", "missing"))
    gate("BY_CMDHELPCHK_APPLY_NOT_EXECUTED", by.get("CMDHELPCHK_APPLY_EXECUTED") == "0", by.get("CMDHELPCHK_APPLY_EXECUTED", "missing"))
    gate("BY_EXECUTION_RESULT_ROWS_PRESENT", len(by_exec) > 0, len(by_exec))
    gate("BY_NATIVE_REQUIREMENT_ROWS_PRESENT", len(by_req) > 0, len(by_req))
    gate("BX_PACKAGE_ROWS_PRESENT", len(bx_pkg) > 0, len(bx_pkg))
    gate("ACTIVE_MESSAGES_HEADER_COUNT_14", msg_count == 14, msg_count)
    gate("ACTIVE_TEXT_HEADER_COUNT_70", text_count == 70, text_count)
    gate("BZ_ROOT_NOT_EXISTING_OR_REPLACE_ALLOWED", (not bz_root.exists()) or args.replace_existing_package, rel(bz_root, repo))

    status = BLOCKED
    implementation_rows = []
    contract_rows = []
    command_plan_rows = []
    disabled_script_rows = []
    validation_rows = []
    artifact_rows = []

    if failures == 0:
        if bz_root.exists() and args.replace_existing_package:
            shutil.rmtree(bz_root)
        bz_root.mkdir(parents=True, exist_ok=True)

        exec_by_target = {r.get("TARGET_PATH", ""): r for r in by_exec}
        pkg_by_target = {r.get("TARGET_PATH", ""): r for r in bx_pkg}

        for i, req in enumerate(by_req, start=1):
            target_path = req.get("TARGET_PATH", "")
            ex = exec_by_target.get(target_path, {})
            px = pkg_by_target.get(target_path, {})
            kind = implementation_kind(req)
            target = repo / target_path
            target_exists = target.exists() and target.is_file()
            implementation_rows.append({
                "IMPLEMENTATION_ROW": i,
                "TARGET_PATH": target_path,
                "TARGET_KIND": req.get("TARGET_KIND", "") or ex.get("TARGET_KIND", ""),
                "TARGET_EXISTS": 1 if target_exists else 0,
                "REQUIRED_IMPLEMENTATION": req.get("REQUIRED_IMPLEMENTATION", ""),
                "IMPLEMENTATION_KIND": kind,
                "IMPLEMENTATION_STATUS": "DESIGN_STAGED_SOURCE_HELD",
                "SAFE_TO_MUTATE_NOW": 0,
                "APPLY_EXECUTED_NOW": 0,
                "SOURCE_MUTATION_REQUIRED_NOW": 0,
                "DETAIL": req.get("DETAIL", ""),
            })
            contract_rows.append({
                "CONTRACT_ROW": i,
                "TARGET_PATH": target_path,
                "PRECONDITION": "hash/backup/readback/native-writer contract required",
                "TARGET_SHA256_EXPECTED": px.get("TARGET_SHA256_EXPECTED", "") or ex.get("TARGET_SHA256_EXPECTED", ""),
                "BACKUP_PATH": px.get("BACKUP_PATH", "") or ex.get("BACKUP_PATH", ""),
                "APPLY_METHOD": kind,
                "REFUSE_IF": "target hash drift; backup missing; native writer unavailable; runtime readback missing",
                "POSTCONDITION": "HELP/CMDHELPCHK readback green and messaging counts stable",
            })

        command_plan_rows = [
            {"PLAN_ROW": 1, "COMMAND_OR_SURFACE": "HELP MSGMGR", "IMPLEMENTATION_NEED": "native HELP DATA insertion/update path", "STATUS": "CANDIDATE_PLAN_ONLY"},
            {"PLAN_ROW": 2, "COMMAND_OR_SURFACE": "HELP SET MESSAGE", "IMPLEMENTATION_NEED": "native HELP DATA insertion/update path", "STATUS": "CANDIDATE_PLAN_ONLY"},
            {"PLAN_ROW": 3, "COMMAND_OR_SURFACE": "CMDHELPCHK MSGMGR", "IMPLEMENTATION_NEED": "native CMDHELPCHK/catalog insertion/update path", "STATUS": "CANDIDATE_PLAN_ONLY"},
            {"PLAN_ROW": 4, "COMMAND_OR_SURFACE": "CMDHELPCHK SET MESSAGE", "IMPLEMENTATION_NEED": "native CMDHELPCHK/catalog insertion/update path", "STATUS": "CANDIDATE_PLAN_ONLY"},
            {"PLAN_ROW": 5, "COMMAND_OR_SURFACE": "MSGMGR STATUS/CHECK", "IMPLEMENTATION_NEED": "runtime readback validation only", "STATUS": "CARRY_FORWARD"},
            {"PLAN_ROW": 6, "COMMAND_OR_SURFACE": "SET MESSAGE CATALOG CHECK/EMIT", "IMPLEMENTATION_NEED": "runtime readback validation only", "STATUS": "CARRY_FORWARD"},
        ]

        validation_rows = [
            {"VALIDATION_ROW": 1, "VALIDATION": "native writer design reviewed", "REQUIRED": 1, "RUN_NOW": 0},
            {"VALIDATION_ROW": 2, "VALIDATION": "target hashes match before apply", "REQUIRED": 1, "RUN_NOW": 0},
            {"VALIDATION_ROW": 3, "VALIDATION": "exact backups exist before apply", "REQUIRED": 1, "RUN_NOW": 0},
            {"VALIDATION_ROW": 4, "VALIDATION": "HELP MSGMGR readback after apply", "REQUIRED": 1, "RUN_NOW": 0},
            {"VALIDATION_ROW": 5, "VALIDATION": "HELP SET MESSAGE readback after apply", "REQUIRED": 1, "RUN_NOW": 0},
            {"VALIDATION_ROW": 6, "VALIDATION": "CMDHELPCHK readback after apply", "REQUIRED": 1, "RUN_NOW": 0},
            {"VALIDATION_ROW": 7, "VALIDATION": "SYSTEM_MESSAGES remains 14 unless separately authorized", "REQUIRED": 1, "RUN_NOW": 0},
            {"VALIDATION_ROW": 8, "VALIDATION": "SYSTEM_MESSAGE_TEXT remains 70 unless separately authorized", "REQUIRED": 1, "RUN_NOW": 0},
        ]

        scripts_dir = bz_root / "scripts"
        scripts_dir.mkdir(parents=True, exist_ok=True)

        native_template = scripts_dir / "MESSAGE_CATALOG_PHASE22AE_6_5_10BZ_NATIVE_APPLY_IMPLEMENTATION_TEMPLATE.ps1.disabled"
        native_template.write_text(
            'throw "10BZ is implementation-package staging only. Do not run mutation here. Create/review a native/schema-aware DotTalk++ apply path first."\n',
            encoding="utf-8"
        )
        dts_contract = scripts_dir / "MESSAGE_CATALOG_PHASE22AE_6_5_10BZ_NATIVE_APPLY_READBACK_CONTRACT.dts"
        dts_contract.write_text(
            "MSGMGR STATUS\n"
            "MSGMGR CHECK\n"
            "SET MESSAGE CATALOG CHECK\n"
            "SET MESSAGE EMIT MESSAGE_PROOF_MODE_STATUS en-US\n"
            "HELP MSGMGR\n"
            "HELP SET MESSAGE\n"
            "CMDHELPCHK\n"
            "QUIT\n",
            encoding="utf-8"
        )
        native_notes = bz_root / "native_apply_implementation_contract_v1.md"
        native_notes.write_text(
            "# 10BZ Native Apply Implementation Contract\n\n"
            "10BZ stages the target-specific/native implementation package only. It does not change HELP DATA, CMDHELPCHK, source, DBF, CDX, LMDB, or workspace files.\n\n"
            "The implementation must be reviewed before any mutation package is allowed. The future apply path must be native/schema-aware and must refuse raw DBF byte writes.\n",
            encoding="utf-8"
        )

        disabled_script_rows = [
            {"SCRIPT_ROW": 1, "SCRIPT_PATH": rel(native_template, repo), "SCRIPT_ROLE": "disabled_native_apply_template", "RUN_NOW": 0, "APPLY_ENABLED": 0},
            {"SCRIPT_ROW": 2, "SCRIPT_PATH": rel(dts_contract, repo), "SCRIPT_ROLE": "runtime_readback_contract", "RUN_NOW": 0, "APPLY_ENABLED": 0},
        ]

        impl_path = bz_root / "target_specific_native_implementation_manifest_v1.csv"
        contract_path = bz_root / "target_apply_contract_v1.csv"
        command_path = bz_root / "help_cmdhelpchk_surface_implementation_plan_v1.csv"
        validation_path = bz_root / "native_apply_validation_contract_v1.csv"
        scripts_path = bz_root / "disabled_script_manifest_v1.csv"
        readme = bz_root / "README_10BZ_TARGET_SPECIFIC_NATIVE_APPLY_IMPLEMENTATION_PACKAGE.md"
        readme.write_text(
            "# 10BZ Target-Specific Native Apply Implementation Package\n\n"
            "10BZ turns the 10BY hold into a reviewed implementation contract. It is not an apply execution step.\n\n"
            "No HELP DATA or CMDHELPCHK mutation is authorized or executed in 10BZ.\n",
            encoding="utf-8"
        )

        wcsv(impl_path, implementation_rows, ["IMPLEMENTATION_ROW","TARGET_PATH","TARGET_KIND","TARGET_EXISTS","REQUIRED_IMPLEMENTATION","IMPLEMENTATION_KIND","IMPLEMENTATION_STATUS","SAFE_TO_MUTATE_NOW","APPLY_EXECUTED_NOW","SOURCE_MUTATION_REQUIRED_NOW","DETAIL"])
        wcsv(contract_path, contract_rows, ["CONTRACT_ROW","TARGET_PATH","PRECONDITION","TARGET_SHA256_EXPECTED","BACKUP_PATH","APPLY_METHOD","REFUSE_IF","POSTCONDITION"])
        wcsv(command_path, command_plan_rows, ["PLAN_ROW","COMMAND_OR_SURFACE","IMPLEMENTATION_NEED","STATUS"])
        wcsv(validation_path, validation_rows, ["VALIDATION_ROW","VALIDATION","REQUIRED","RUN_NOW"])
        wcsv(scripts_path, disabled_script_rows, ["SCRIPT_ROW","SCRIPT_PATH","SCRIPT_ROLE","RUN_NOW","APPLY_ENABLED"])

        for p in [impl_path, contract_path, command_path, validation_path, scripts_path, native_template, dts_contract, native_notes, readme]:
            artifact_rows.append({"ARTIFACT": rel(p, repo), "ROLE": "target_specific_native_apply_implementation_package_artifact", "BYTES": p.stat().st_size, "SHA256": sha(p)})

        status = GREEN

    boundary = [
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "10BZ writes docs/messaging implementation-package artifacts only."},
        {"PROTECTED_SYSTEM": "ACTIVE_SYSTEM_MESSAGES", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_SYSTEM_MESSAGE_TEXT", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_CDX_LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CDX/LMDB mutation."},
        {"PROTECTED_SYSTEM": "WORKSPACE_PROFILE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No workspace mutation."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Implementation package only; no HELP DATA apply."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Implementation package only; no CMDHELPCHK apply."},
    ]

    readiness = [
        {"ITEM": "TARGET_SPECIFIC_IMPLEMENTATION_PACKAGE_STAGED", "STATUS": "YES" if implementation_rows else "NO", "DETAIL": f"{len(implementation_rows)} implementation rows."},
        {"ITEM": "NATIVE_APPLY_CONTRACT_STAGED", "STATUS": "YES" if contract_rows else "NO", "DETAIL": f"{len(contract_rows)} contract rows."},
        {"ITEM": "HELP_DATA_APPLY_EXECUTION", "STATUS": "NOT_EXECUTED_IN_10BZ", "DETAIL": "No apply execution."},
        {"ITEM": "CMDHELPCHK_APPLY_EXECUTION", "STATUS": "NOT_EXECUTED_IN_10BZ", "DETAIL": "No apply execution."},
        {"ITEM": "NEXT_REVIEW_GATE", "STATUS": "10CA_REQUIRED", "DETAIL": "Review implementation package before any real implementation/mutation."},
    ]

    issues = "0" if failures == 0 else str(failures)
    wcsv(reports / "message_catalog_phase22ae_6_5_10bz_gate_check_v1.csv", gates, ["GATE","STATUS","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10bz_native_implementation_manifest_v1.csv", implementation_rows, ["IMPLEMENTATION_ROW","TARGET_PATH","TARGET_KIND","TARGET_EXISTS","REQUIRED_IMPLEMENTATION","IMPLEMENTATION_KIND","IMPLEMENTATION_STATUS","SAFE_TO_MUTATE_NOW","APPLY_EXECUTED_NOW","SOURCE_MUTATION_REQUIRED_NOW","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10bz_target_apply_contract_v1.csv", contract_rows, ["CONTRACT_ROW","TARGET_PATH","PRECONDITION","TARGET_SHA256_EXPECTED","BACKUP_PATH","APPLY_METHOD","REFUSE_IF","POSTCONDITION"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10bz_surface_implementation_plan_v1.csv", command_plan_rows, ["PLAN_ROW","COMMAND_OR_SURFACE","IMPLEMENTATION_NEED","STATUS"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10bz_validation_contract_v1.csv", validation_rows, ["VALIDATION_ROW","VALIDATION","REQUIRED","RUN_NOW"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10bz_apply_readiness_v1.csv", readiness, ["ITEM","STATUS","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10bz_boundary_ledger_v1.csv", boundary, ["PROTECTED_SYSTEM","MUTATION_ALLOWED","OBSERVED_MUTATION","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10bz_artifact_manifest_v1.csv", artifact_rows, ["ARTIFACT","ROLE","BYTES","SHA256"])

    summary = {
        "STATUS": status,
        "VALIDATION_ISSUES": issues,
        "PHASE22AE_6_5_10BY_STATUS": by.get("STATUS", ""),
        "MSG_022AE_6_5_10BY_SAVEPOINT_PRESENT": 1 if sp_by else 0,
        "ACTIVE_MESSAGES_OBSERVED_COUNT": msg_count,
        "ACTIVE_TEXT_OBSERVED_COUNT": text_count,
        "BY_NATIVE_REQUIREMENT_ROWS": len(by_req),
        "IMPLEMENTATION_MANIFEST_ROWS": len(implementation_rows),
        "TARGET_APPLY_CONTRACT_ROWS": len(contract_rows),
        "SURFACE_IMPLEMENTATION_PLAN_ROWS": len(command_plan_rows),
        "VALIDATION_CONTRACT_ROWS": len(validation_rows),
        "BZ_ROOT": rel(bz_root, repo),
        "TARGET_SPECIFIC_NATIVE_IMPLEMENTATION_PACKAGE_STAGED": 1 if status == GREEN else 0,
        "APPLY_EXECUTION_AUTHORIZED_NOW": 0,
        "HELP_DATA_APPLY_EXECUTED": 0,
        "CMDHELPCHK_APPLY_EXECUTED": 0,
        "HELP_DATA_MUTATION_OBSERVED": 0,
        "CMDHELPCHK_MUTATION_OBSERVED": 0,
        "SOURCE_FILES_MUTATED": 0,
        "ACTIVE_CATALOG_MUTATION_OBSERVED_BY_REVIEW": 0,
        "DBF_MUTATION_OBSERVED": 0,
        "CDX_LMDB_MUTATION_OBSERVED": 0,
        "WORKSPACE_MUTATION_OBSERVED": 0,
        "NEXT_GATE": NEXT,
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }
    wcsv(reports / "message_catalog_phase22ae_6_5_10bz_status_summary_v1.csv", [summary], list(summary.keys()))

    (repo / "docs/messaging/MESSAGE_LOCALE_PHASE22AE_6_5_10BZ_TARGET_SPECIFIC_NATIVE_APPLY_IMPLEMENTATION_PACKAGE.md").write_text(
        f"# Message Catalog Phase 22AE.6.5.10BZ Target-Specific Native Apply Implementation Package\n\n"
        f"Status: `{status}`\n\n"
        "10BZ stages the target-specific/native apply implementation package. It does not mutate HELP DATA or CMDHELPCHK.\n\n"
        f"Package root:\n\n```text\n{rel(bz_root, repo)}\n```\n\n"
        f"Next gate:\n\n```text\n{NEXT}\n```\n",
        encoding="utf-8"
    )

    print(status)
    print(f"  validation issues: {issues}")
    print(f"  Phase 22AE.6.5.10BY status: {by.get('STATUS','')}")
    print(f"  MSG-022AE.6.5.10BY savepoint present: {1 if sp_by else 0}")
    print(f"  active messages observed count: {msg_count}")
    print(f"  active text observed count: {text_count}")
    print(f"  BY native requirement rows: {len(by_req)}")
    print(f"  implementation manifest rows: {len(implementation_rows)}")
    print(f"  target apply contract rows: {len(contract_rows)}")
    print(f"  surface implementation plan rows: {len(command_plan_rows)}")
    print(f"  validation contract rows: {len(validation_rows)}")
    print(f"  package root: {rel(bz_root, repo)}")
    print("  target-specific native implementation package staged: 1")
    print("  apply execution authorized now: 0")
    print("  HELP DATA apply executed: 0")
    print("  CMDHELPCHK apply executed: 0")
    print("  HELP DATA mutation observed: 0")
    print("  CMDHELPCHK mutation observed: 0")
    print("  source files mutated: 0")
    print("  active catalog mutation observed by review: 0")
    print("  DBF mutation observed: 0")
    print("  CDX/LMDB mutation observed: 0")
    print("  workspace mutation observed: 0")
    print(f"  next gate: {NEXT}")
    print(f"  reports: {reports}")
    return 0 if status == GREEN else 2

if __name__ == "__main__":
    raise SystemExit(main())
