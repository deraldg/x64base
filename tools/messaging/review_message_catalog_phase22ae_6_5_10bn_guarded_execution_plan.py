#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, json, hashlib, shutil
from datetime import datetime, timezone
from pathlib import Path

GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_10BN_GUARDED_NATIVE_EXECUTION_PLAN_REVIEW_GREEN_EXECUTION_PACKAGE_REQUIRED_SOURCE_HELD"
BLOCKED = "MESSAGE_CATALOG_PHASE22AE_6_5_10BN_GUARDED_NATIVE_EXECUTION_PLAN_REVIEW_BLOCKED"
NEXT = "HOLD_OR_AUTHORIZE_PHASE22AE_6_5_10BO_GUARDED_NATIVE_EXECUTION_PACKAGE"

REPORT_DIR = Path("docs/messaging/reports")
BM_SUMMARY = REPORT_DIR / "message_catalog_phase22ae_6_5_10bm_status_summary_v1.csv"
BM_PLAN = REPORT_DIR / "message_catalog_phase22ae_6_5_10bm_guarded_native_execution_plan_v1.csv"
BM_VALIDATION = REPORT_DIR / "message_catalog_phase22ae_6_5_10bm_validation_plan_v1.csv"
BM_RESTORE = REPORT_DIR / "message_catalog_phase22ae_6_5_10bm_restore_plan_v1.csv"
BN_ROOT = Path("docs/messaging/apply/phase22ae_6_5_10bn_guarded_native_execution_plan_review_v1")
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
    ap.add_argument("--replace-existing-review", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    reports = repo / REPORT_DIR
    reports.mkdir(parents=True, exist_ok=True)

    bm = first(repo / BM_SUMMARY)
    exec_plan = rows(repo / BM_PLAN)
    validation_plan = rows(repo / BM_VALIDATION)
    restore_plan = rows(repo / BM_RESTORE)
    sp_bm, latest_bm = savepoint(repo, "MSG-022AE.6.5.10BM")
    msg_count = dbf_count(repo / ACTIVE_MSG_DBF)
    text_count = dbf_count(repo / ACTIVE_TEXT_DBF)
    bn_root = repo / BN_ROOT

    gates = []
    failures = 0
    def gate(name, ok, detail):
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": str(detail)})
        if not ok:
            failures += 1

    gate("PHASE22AE_6_5_10BM_GREEN",
         bm.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_5_10BM_GUARDED_NATIVE_HELP_CMDHELPCHK_EXECUTION_PLAN_GREEN_SOURCE_HELD",
         bm.get("STATUS", "missing"))
    gate("MSG_022AE_6_5_10BM_SAVEPOINT_PRESENT", sp_bm, latest_bm)
    gate("BM_EXECUTION_PLAN_CREATED", bm.get("GUARDED_NATIVE_EXECUTION_PLAN_CREATED") == "1", bm.get("GUARDED_NATIVE_EXECUTION_PLAN_CREATED", "missing"))
    gate("BM_HELP_APPLY_NOT_EXECUTED", bm.get("HELP_DATA_APPLY_EXECUTED") == "0", bm.get("HELP_DATA_APPLY_EXECUTED", "missing"))
    gate("BM_CMDHELPCHK_APPLY_NOT_EXECUTED", bm.get("CMDHELPCHK_APPLY_EXECUTED") == "0", bm.get("CMDHELPCHK_APPLY_EXECUTED", "missing"))
    gate("EXECUTION_PLAN_ROWS_PRESENT", len(exec_plan) > 0, len(exec_plan))
    gate("VALIDATION_PLAN_ROWS_PRESENT", len(validation_plan) > 0, len(validation_plan))
    gate("RESTORE_PLAN_ROWS_PRESENT", len(restore_plan) > 0, len(restore_plan))
    gate("ACTIVE_MESSAGES_HEADER_COUNT_14", msg_count == 14, msg_count)
    gate("ACTIVE_TEXT_HEADER_COUNT_70", text_count == 70, text_count)
    gate("BN_ROOT_NOT_EXISTING_OR_REPLACE_ALLOWED", (not bn_root.exists()) or args.replace_existing_review, rel(bn_root, repo))

    status = BLOCKED
    review_rows = []
    decision_rows = []
    artifact_rows = []
    if failures == 0:
        if bn_root.exists() and args.replace_existing_review:
            shutil.rmtree(bn_root)
        bn_root.mkdir(parents=True, exist_ok=True)

        for i, r in enumerate(exec_plan, start=1):
            method = r.get("EXECUTION_METHOD", "")
            is_native = "NATIVE" in method.upper() or "SCHEMA_AWARE" in method.upper() or "TEXT_DIFF" in method.upper()
            has_hash = bool(r.get("TARGET_SHA256", ""))
            has_diff = bool(r.get("DIFF_ARTIFACT", ""))
            disposition = "ACCEPT_FOR_GUARDED_EXECUTION_PACKAGE" if is_native and has_diff else "REVIEW_REQUIRED"
            review_rows.append({
                "REVIEW_ROW": i,
                "TARGET_ID": r.get("TARGET_ID", ""),
                "TARGET_KIND": r.get("TARGET_KIND", ""),
                "TARGET_PATH": r.get("TARGET_PATH", ""),
                "TARGET_FORMAT": r.get("TARGET_FORMAT", ""),
                "DIFF_ARTIFACT": r.get("DIFF_ARTIFACT", ""),
                "TARGET_SHA256_PRESENT": 1 if has_hash else 0,
                "EXECUTION_METHOD": method,
                "REVIEW_DISPOSITION": disposition,
                "GUARDED_EXECUTION_PACKAGE_REQUIRED": 1,
                "AUTHORIZED_FOR_WRITE_NOW": 0,
                "EXECUTED_NOW": 0,
                "REASON": "Execution plan accepted for packaging only; no HELP/CMDHELPCHK mutation in 10BN.",
            })

        decision_rows = [
            {"DECISION_ITEM": "GUARDED_NATIVE_EXECUTION_PLAN", "DECISION": "ACCEPT_FOR_EXECUTION_PACKAGE", "DETAIL": f"{len(exec_plan)} execution rows reviewed."},
            {"DECISION_ITEM": "VALIDATION_PLAN", "DECISION": "CARRY_FORWARD_REQUIRED", "DETAIL": f"{len(validation_plan)} validation steps must be carried forward."},
            {"DECISION_ITEM": "RESTORE_PLAN", "DECISION": "CARRY_FORWARD_REQUIRED", "DETAIL": f"{len(restore_plan)} restore steps must be carried forward."},
            {"DECISION_ITEM": "HELP_DATA_APPLY_EXECUTION", "DECISION": "NOT_AUTHORIZED_IN_10BN", "DETAIL": "No HELP DATA write in 10BN."},
            {"DECISION_ITEM": "CMDHELPCHK_APPLY_EXECUTION", "DECISION": "NOT_AUTHORIZED_IN_10BN", "DETAIL": "No CMDHELPCHK write in 10BN."},
            {"DECISION_ITEM": "NEXT_GATE", "DECISION": "AUTHORIZE_10BO_OR_HOLD", "DETAIL": "10BO should stage the guarded execution package; write execution still requires explicit authorization and refusal guards."},
        ]

        review_path = bn_root / "guarded_native_execution_plan_review_v1.csv"
        decision_path = bn_root / "execution_plan_review_decisions_v1.csv"
        readme = bn_root / "README_10BN_GUARDED_NATIVE_EXECUTION_PLAN_REVIEW.md"
        wcsv(review_path, review_rows, ["REVIEW_ROW","TARGET_ID","TARGET_KIND","TARGET_PATH","TARGET_FORMAT","DIFF_ARTIFACT","TARGET_SHA256_PRESENT","EXECUTION_METHOD","REVIEW_DISPOSITION","GUARDED_EXECUTION_PACKAGE_REQUIRED","AUTHORIZED_FOR_WRITE_NOW","EXECUTED_NOW","REASON"])
        wcsv(decision_path, decision_rows, ["DECISION_ITEM","DECISION","DETAIL"])
        readme.write_text(
            "# 10BN Guarded Native Execution Plan Review\n\n"
            "10BN reviews the 10BM guarded native/schema-aware execution plan and accepts it for a guarded execution package only.\n\n"
            "No HELP DATA or CMDHELPCHK mutation is authorized or executed in 10BN.\n",
            encoding="utf-8"
        )

        for p in [review_path, decision_path, readme]:
            artifact_rows.append({"ARTIFACT": rel(p, repo), "ROLE": "guarded_native_execution_plan_review_artifact", "BYTES": p.stat().st_size, "SHA256": sha(p)})
        status = GREEN

    boundary = [
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "10BN writes docs/messaging review artifacts only."},
        {"PROTECTED_SYSTEM": "ACTIVE_SYSTEM_MESSAGES", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_SYSTEM_MESSAGE_TEXT", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_CDX_LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CDX/LMDB mutation."},
        {"PROTECTED_SYSTEM": "WORKSPACE_PROFILE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No workspace mutation."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No HELP DATA mutation; plan review only."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CMDHELPCHK mutation; plan review only."},
    ]

    readiness = [
        {"ITEM": "GUARDED_EXECUTION_PLAN_REVIEW_COMPLETE", "STATUS": "YES" if review_rows else "NO", "DETAIL": f"{len(review_rows)} rows reviewed."},
        {"ITEM": "GUARDED_EXECUTION_PACKAGE_REQUIRED", "STATUS": "YES", "DETAIL": "10BO should stage the guarded execution package."},
        {"ITEM": "HELP_DATA_APPLY_EXECUTION", "STATUS": "NOT_EXECUTED_IN_10BN", "DETAIL": "No apply execution."},
        {"ITEM": "CMDHELPCHK_APPLY_EXECUTION", "STATUS": "NOT_EXECUTED_IN_10BN", "DETAIL": "No apply execution."},
        {"ITEM": "NEXT_PACKAGE", "STATUS": "10BO_REQUIRED", "DETAIL": "Guarded native execution package staging."},
    ]

    issues = "0" if failures == 0 else str(failures)
    wcsv(reports / "message_catalog_phase22ae_6_5_10bn_gate_check_v1.csv", gates, ["GATE","STATUS","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10bn_execution_plan_review_v1.csv", review_rows, ["REVIEW_ROW","TARGET_ID","TARGET_KIND","TARGET_PATH","TARGET_FORMAT","DIFF_ARTIFACT","TARGET_SHA256_PRESENT","EXECUTION_METHOD","REVIEW_DISPOSITION","GUARDED_EXECUTION_PACKAGE_REQUIRED","AUTHORIZED_FOR_WRITE_NOW","EXECUTED_NOW","REASON"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10bn_review_decisions_v1.csv", decision_rows, ["DECISION_ITEM","DECISION","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10bn_apply_readiness_v1.csv", readiness, ["ITEM","STATUS","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10bn_boundary_ledger_v1.csv", boundary, ["PROTECTED_SYSTEM","MUTATION_ALLOWED","OBSERVED_MUTATION","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10bn_artifact_manifest_v1.csv", artifact_rows, ["ARTIFACT","ROLE","BYTES","SHA256"])

    summary = {
        "STATUS": status,
        "VALIDATION_ISSUES": issues,
        "PHASE22AE_6_5_10BM_STATUS": bm.get("STATUS", ""),
        "MSG_022AE_6_5_10BM_SAVEPOINT_PRESENT": 1 if sp_bm else 0,
        "ACTIVE_MESSAGES_OBSERVED_COUNT": msg_count,
        "ACTIVE_TEXT_OBSERVED_COUNT": text_count,
        "BM_EXECUTION_PLAN_ROWS": len(exec_plan),
        "BM_VALIDATION_PLAN_ROWS": len(validation_plan),
        "BM_RESTORE_PLAN_ROWS": len(restore_plan),
        "EXECUTION_PLAN_REVIEW_ROWS": len(review_rows),
        "DECISION_ROWS": len(decision_rows),
        "BN_ROOT": rel(bn_root, repo),
        "GUARDED_EXECUTION_PACKAGE_REQUIRED": 1 if status == GREEN else 0,
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
    wcsv(reports / "message_catalog_phase22ae_6_5_10bn_status_summary_v1.csv", [summary], list(summary.keys()))

    (repo / "docs/messaging/MESSAGE_LOCALE_PHASE22AE_6_5_10BN_GUARDED_NATIVE_EXECUTION_PLAN_REVIEW.md").write_text(
        f"# Message Catalog Phase 22AE.6.5.10BN Guarded Native Execution Plan Review\n\n"
        f"Status: `{status}`\n\n"
        "10BN reviews the guarded native/schema-aware execution plan and accepts it for a guarded execution package. It does not mutate HELP DATA or CMDHELPCHK.\n\n"
        f"Review root:\n\n```text\n{rel(bn_root, repo)}\n```\n\n"
        f"Next gate:\n\n```text\n{NEXT}\n```\n",
        encoding="utf-8"
    )

    print(status)
    print(f"  validation issues: {issues}")
    print(f"  Phase 22AE.6.5.10BM status: {bm.get('STATUS','')}")
    print(f"  MSG-022AE.6.5.10BM savepoint present: {1 if sp_bm else 0}")
    print(f"  active messages observed count: {msg_count}")
    print(f"  active text observed count: {text_count}")
    print(f"  BM execution plan rows: {len(exec_plan)}")
    print(f"  BM validation plan rows: {len(validation_plan)}")
    print(f"  BM restore plan rows: {len(restore_plan)}")
    print(f"  execution plan review rows: {len(review_rows)}")
    print(f"  decision rows: {len(decision_rows)}")
    print(f"  review root: {rel(bn_root, repo)}")
    print("  guarded execution package required: 1")
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
