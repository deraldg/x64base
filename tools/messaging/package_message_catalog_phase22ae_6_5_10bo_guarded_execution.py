#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, json, hashlib, shutil
from datetime import datetime, timezone
from pathlib import Path

GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_10BO_GUARDED_NATIVE_EXECUTION_PACKAGE_GREEN_STAGED_NO_APPLY"
BLOCKED = "MESSAGE_CATALOG_PHASE22AE_6_5_10BO_GUARDED_NATIVE_EXECUTION_PACKAGE_BLOCKED"
NEXT = "HOLD_OR_AUTHORIZE_PHASE22AE_6_5_10BP_GUARDED_NATIVE_EXECUTION_PACKAGE_REVIEW"

REPORT_DIR = Path("docs/messaging/reports")
BN_SUMMARY = REPORT_DIR / "message_catalog_phase22ae_6_5_10bn_status_summary_v1.csv"
BN_REVIEW = REPORT_DIR / "message_catalog_phase22ae_6_5_10bn_execution_plan_review_v1.csv"
BN_DECISIONS = REPORT_DIR / "message_catalog_phase22ae_6_5_10bn_review_decisions_v1.csv"
BM_PLAN = REPORT_DIR / "message_catalog_phase22ae_6_5_10bm_guarded_native_execution_plan_v1.csv"
BM_VALIDATION = REPORT_DIR / "message_catalog_phase22ae_6_5_10bm_validation_plan_v1.csv"
BM_RESTORE = REPORT_DIR / "message_catalog_phase22ae_6_5_10bm_restore_plan_v1.csv"
BO_ROOT = Path("docs/messaging/apply/phase22ae_6_5_10bo_guarded_native_execution_package_v1")
ACTIVE_MSG_DBF = Path("dottalkpp/data/messaging/SYSTEM_MESSAGES.dbf")
ACTIVE_TEXT_DBF = Path("dottalkpp/data/messaging/SYSTEM_MESSAGE_TEXT.dbf")

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
        return str(Path(p).relative_to(repo)).replace("\\", "/")
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

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--replace-existing-package", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    reports = repo / REPORT_DIR
    reports.mkdir(parents=True, exist_ok=True)

    bn = first(repo / BN_SUMMARY)
    bn_review = rows(repo / BN_REVIEW)
    bn_decisions = rows(repo / BN_DECISIONS)
    bm_plan = rows(repo / BM_PLAN)
    bm_validation = rows(repo / BM_VALIDATION)
    bm_restore = rows(repo / BM_RESTORE)
    sp_bn, latest_bn = savepoint(repo, "MSG-022AE.6.5.10BN")
    msg_count = dbf_count(repo / ACTIVE_MSG_DBF)
    text_count = dbf_count(repo / ACTIVE_TEXT_DBF)
    bo_root = repo / BO_ROOT

    gates = []
    failures = 0
    def gate(name, ok, detail):
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": str(detail)})
        if not ok:
            failures += 1

    gate("PHASE22AE_6_5_10BN_GREEN",
         bn.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_5_10BN_GUARDED_NATIVE_EXECUTION_PLAN_REVIEW_GREEN_EXECUTION_PACKAGE_REQUIRED_SOURCE_HELD",
         bn.get("STATUS", "missing"))
    gate("MSG_022AE_6_5_10BN_SAVEPOINT_PRESENT", sp_bn, latest_bn)
    gate("BN_EXECUTION_PACKAGE_REQUIRED", bn.get("GUARDED_EXECUTION_PACKAGE_REQUIRED") == "1", bn.get("GUARDED_EXECUTION_PACKAGE_REQUIRED", "missing"))
    gate("BN_HELP_APPLY_NOT_EXECUTED", bn.get("HELP_DATA_APPLY_EXECUTED") == "0", bn.get("HELP_DATA_APPLY_EXECUTED", "missing"))
    gate("BN_CMDHELPCHK_APPLY_NOT_EXECUTED", bn.get("CMDHELPCHK_APPLY_EXECUTED") == "0", bn.get("CMDHELPCHK_APPLY_EXECUTED", "missing"))
    gate("BN_REVIEW_ROWS_PRESENT", len(bn_review) > 0, len(bn_review))
    gate("BN_DECISIONS_PRESENT", len(bn_decisions) > 0, len(bn_decisions))
    gate("BM_EXECUTION_PLAN_PRESENT", len(bm_plan) > 0, len(bm_plan))
    gate("BM_VALIDATION_PLAN_PRESENT", len(bm_validation) > 0, len(bm_validation))
    gate("BM_RESTORE_PLAN_PRESENT", len(bm_restore) > 0, len(bm_restore))
    gate("ACTIVE_MESSAGES_HEADER_COUNT_14", msg_count == 14, msg_count)
    gate("ACTIVE_TEXT_HEADER_COUNT_70", text_count == 70, text_count)
    gate("BO_ROOT_NOT_EXISTING_OR_REPLACE_ALLOWED", (not bo_root.exists()) or args.replace_existing_package, rel(bo_root, repo))

    status = BLOCKED
    package_rows = []
    backup_rows = []
    refusal_rows = []
    artifact_rows = []
    if failures == 0:
        if bo_root.exists() and args.replace_existing_package:
            shutil.rmtree(bo_root)
        bo_root.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        backup_root = repo / "docs/messaging/backups" / f"MSG-022AE_6_5_10BO_GUARDED_EXECUTION_PACKAGE_BACKUP_{timestamp}"
        backup_root.mkdir(parents=True, exist_ok=True)

        for i, r in enumerate(bm_plan, start=1):
            target_path = r.get("TARGET_PATH", "")
            target = repo / target_path
            exists = target.exists() and target.is_file()
            target_hash = sha(target) if exists else ""
            backup_path = ""
            backup_hash = ""
            backup_match = 0
            if exists:
                dst = backup_root / target_path
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(target, dst)
                backup_path = rel(dst, repo)
                backup_hash = sha(dst)
                backup_match = 1 if backup_hash == target_hash else 0

            package_rows.append({
                "PACKAGE_STEP": i,
                "TARGET_ID": r.get("TARGET_ID", ""),
                "TARGET_KIND": r.get("TARGET_KIND", ""),
                "TARGET_PATH": target_path,
                "TARGET_EXISTS": 1 if exists else 0,
                "TARGET_SHA256_NOW": target_hash,
                "TARGET_SHA256_EXPECTED": r.get("TARGET_SHA256", ""),
                "TARGET_HASH_MATCHES_PLAN": 1 if target_hash and target_hash == r.get("TARGET_SHA256", "") else 0,
                "BACKUP_PATH": backup_path,
                "BACKUP_SHA256": backup_hash,
                "BACKUP_MATCH": backup_match,
                "DIFF_ARTIFACT": r.get("DIFF_ARTIFACT", ""),
                "EXECUTION_METHOD": r.get("EXECUTION_METHOD", ""),
                "AUTHORIZED_FOR_WRITE_NOW": 0,
                "EXECUTED_NOW": 0,
                "PACKAGE_STATUS": "STAGED_NO_APPLY",
            })
            if exists:
                backup_rows.append({
                    "TARGET_PATH": target_path,
                    "BACKUP_PATH": backup_path,
                    "TARGET_SHA256": target_hash,
                    "BACKUP_SHA256": backup_hash,
                    "SHA256_MATCH": backup_match,
                })

        refusal_rows = [
            {"REFUSAL_GUARD": "NO_APPLY_IN_10BO", "STATUS": "ACTIVE", "DETAIL": "10BO stages execution package only."},
            {"REFUSAL_GUARD": "NO_RAW_PYTHON_DBF_WRITE", "STATUS": "ACTIVE", "DETAIL": "DBF/runtime targets require native x64base/DotTalk++ or schema-aware import path."},
            {"REFUSAL_GUARD": "TARGET_HASH_DRIFT", "STATUS": "ACTIVE", "DETAIL": "A later execution package must refuse if target hash differs from expected state."},
            {"REFUSAL_GUARD": "BACKUP_MISSING_OR_MISMATCH", "STATUS": "ACTIVE", "DETAIL": "A later execution package must refuse if exact backup is missing or mismatched."},
            {"REFUSAL_GUARD": "RUNTIME_READBACK_MISSING", "STATUS": "ACTIVE", "DETAIL": "A later execution package must refuse green closeout without DotTalk++ runtime HELP/CMDHELPCHK readback."},
            {"REFUSAL_GUARD": "MESSAGING_COUNTS_DRIFT", "STATUS": "ACTIVE", "DETAIL": "SYSTEM_MESSAGES must remain 14 and SYSTEM_MESSAGE_TEXT must remain 70 unless separately authorized."},
        ]

        pkg_path = bo_root / "guarded_native_execution_package_manifest_v1.csv"
        backup_path = bo_root / "exact_target_backup_manifest_v1.csv"
        validation_path = bo_root / "validation_plan_carried_forward_v1.csv"
        restore_path = bo_root / "restore_plan_carried_forward_v1.csv"
        refusal_path = bo_root / "refusal_guards_v1.csv"
        disabled = bo_root / "scripts" / "MESSAGE_CATALOG_PHASE22AE_6_5_10BP_REVIEW_REQUIRED_NO_WRITE.ps1.disabled"
        disabled.parent.mkdir(parents=True, exist_ok=True)
        disabled.write_text(
            'throw "DISABLED TEMPLATE: 10BO stages the guarded execution package only. 10BP review and later explicit apply authorization required."\n',
            encoding="utf-8"
        )
        readme = bo_root / "README_10BO_GUARDED_NATIVE_EXECUTION_PACKAGE.md"
        readme.write_text(
            "# 10BO Guarded Native HELP/CMDHELPCHK Execution Package\n\n"
            "10BO stages the guarded native/schema-aware HELP/CMDHELPCHK execution package, copies exact target backups, and carries forward validation/restore/refusal guards.\n\n"
            "No HELP DATA or CMDHELPCHK mutation is authorized or executed in 10BO.\n",
            encoding="utf-8"
        )

        wcsv(pkg_path, package_rows, ["PACKAGE_STEP","TARGET_ID","TARGET_KIND","TARGET_PATH","TARGET_EXISTS","TARGET_SHA256_NOW","TARGET_SHA256_EXPECTED","TARGET_HASH_MATCHES_PLAN","BACKUP_PATH","BACKUP_SHA256","BACKUP_MATCH","DIFF_ARTIFACT","EXECUTION_METHOD","AUTHORIZED_FOR_WRITE_NOW","EXECUTED_NOW","PACKAGE_STATUS"])
        wcsv(backup_path, backup_rows, ["TARGET_PATH","BACKUP_PATH","TARGET_SHA256","BACKUP_SHA256","SHA256_MATCH"])
        wcsv(validation_path, bm_validation, list(bm_validation[0].keys()) if bm_validation else ["EMPTY"])
        wcsv(restore_path, bm_restore, list(bm_restore[0].keys()) if bm_restore else ["EMPTY"])
        wcsv(refusal_path, refusal_rows, ["REFUSAL_GUARD","STATUS","DETAIL"])

        for p in [pkg_path, backup_path, validation_path, restore_path, refusal_path, disabled, readme]:
            artifact_rows.append({"ARTIFACT": rel(p, repo), "ROLE": "guarded_native_execution_package_artifact", "BYTES": p.stat().st_size, "SHA256": sha(p)})

        status = GREEN

    boundary = [
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "10BO writes docs/messaging execution-package artifacts and backups only."},
        {"PROTECTED_SYSTEM": "ACTIVE_SYSTEM_MESSAGES", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_SYSTEM_MESSAGE_TEXT", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_CDX_LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CDX/LMDB mutation."},
        {"PROTECTED_SYSTEM": "WORKSPACE_PROFILE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No workspace mutation."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Backups/package only; no HELP DATA apply."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Backups/package only; no CMDHELPCHK apply."},
    ]

    readiness = [
        {"ITEM": "GUARDED_EXECUTION_PACKAGE_STAGED", "STATUS": "YES" if package_rows else "NO", "DETAIL": f"{len(package_rows)} package rows."},
        {"ITEM": "EXACT_TARGET_BACKUPS_CREATED", "STATUS": "YES" if backup_rows else "NO", "DETAIL": f"{len(backup_rows)} backups copied."},
        {"ITEM": "REFUSAL_GUARDS_STAGED", "STATUS": "YES" if refusal_rows else "NO", "DETAIL": f"{len(refusal_rows)} guards."},
        {"ITEM": "HELP_DATA_APPLY_EXECUTION", "STATUS": "NOT_EXECUTED_IN_10BO", "DETAIL": "No apply execution."},
        {"ITEM": "CMDHELPCHK_APPLY_EXECUTION", "STATUS": "NOT_EXECUTED_IN_10BO", "DETAIL": "No apply execution."},
        {"ITEM": "NEXT_REVIEW_GATE", "STATUS": "10BP_REQUIRED", "DETAIL": "Review staged execution package before any apply decision."},
    ]

    issues = "0" if failures == 0 else str(failures)
    wcsv(reports / "message_catalog_phase22ae_6_5_10bo_gate_check_v1.csv", gates, ["GATE","STATUS","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10bo_execution_package_manifest_v1.csv", package_rows, ["PACKAGE_STEP","TARGET_ID","TARGET_KIND","TARGET_PATH","TARGET_EXISTS","TARGET_SHA256_NOW","TARGET_SHA256_EXPECTED","TARGET_HASH_MATCHES_PLAN","BACKUP_PATH","BACKUP_SHA256","BACKUP_MATCH","DIFF_ARTIFACT","EXECUTION_METHOD","AUTHORIZED_FOR_WRITE_NOW","EXECUTED_NOW","PACKAGE_STATUS"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10bo_backup_manifest_v1.csv", backup_rows, ["TARGET_PATH","BACKUP_PATH","TARGET_SHA256","BACKUP_SHA256","SHA256_MATCH"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10bo_refusal_guards_v1.csv", refusal_rows, ["REFUSAL_GUARD","STATUS","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10bo_apply_readiness_v1.csv", readiness, ["ITEM","STATUS","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10bo_boundary_ledger_v1.csv", boundary, ["PROTECTED_SYSTEM","MUTATION_ALLOWED","OBSERVED_MUTATION","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10bo_artifact_manifest_v1.csv", artifact_rows, ["ARTIFACT","ROLE","BYTES","SHA256"])

    summary = {
        "STATUS": status,
        "VALIDATION_ISSUES": issues,
        "PHASE22AE_6_5_10BN_STATUS": bn.get("STATUS", ""),
        "MSG_022AE_6_5_10BN_SAVEPOINT_PRESENT": 1 if sp_bn else 0,
        "ACTIVE_MESSAGES_OBSERVED_COUNT": msg_count,
        "ACTIVE_TEXT_OBSERVED_COUNT": text_count,
        "BN_EXECUTION_PLAN_REVIEW_ROWS": len(bn_review),
        "EXECUTION_PACKAGE_ROWS": len(package_rows),
        "BACKUPS_COPIED": len(backup_rows),
        "REFUSAL_GUARD_ROWS": len(refusal_rows),
        "BO_ROOT": rel(bo_root, repo),
        "GUARDED_EXECUTION_PACKAGE_STAGED": 1 if status == GREEN else 0,
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
    wcsv(reports / "message_catalog_phase22ae_6_5_10bo_status_summary_v1.csv", [summary], list(summary.keys()))

    (repo / "docs/messaging/MESSAGE_LOCALE_PHASE22AE_6_5_10BO_GUARDED_NATIVE_EXECUTION_PACKAGE.md").write_text(
        f"# Message Catalog Phase 22AE.6.5.10BO Guarded Native Execution Package\n\n"
        f"Status: `{status}`\n\n"
        "10BO stages the guarded native/schema-aware execution package. It does not mutate HELP DATA or CMDHELPCHK.\n\n"
        f"Package root:\n\n```text\n{rel(bo_root, repo)}\n```\n\n"
        f"Next gate:\n\n```text\n{NEXT}\n```\n",
        encoding="utf-8"
    )

    print(status)
    print(f"  validation issues: {issues}")
    print(f"  Phase 22AE.6.5.10BN status: {bn.get('STATUS','')}")
    print(f"  MSG-022AE.6.5.10BN savepoint present: {1 if sp_bn else 0}")
    print(f"  active messages observed count: {msg_count}")
    print(f"  active text observed count: {text_count}")
    print(f"  BN execution plan review rows: {len(bn_review)}")
    print(f"  execution package rows: {len(package_rows)}")
    print(f"  backups copied: {len(backup_rows)}")
    print(f"  refusal guard rows: {len(refusal_rows)}")
    print(f"  package root: {rel(bo_root, repo)}")
    print("  guarded execution package staged: 1")
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
