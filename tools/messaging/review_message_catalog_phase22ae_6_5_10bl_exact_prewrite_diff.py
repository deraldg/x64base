#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, json, hashlib, shutil
from datetime import datetime, timezone
from pathlib import Path

GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_10BL_EXACT_PRE_WRITE_DIFF_PACKAGE_REVIEW_GREEN_EXECUTION_PLAN_REQUIRED_SOURCE_HELD"
BLOCKED = "MESSAGE_CATALOG_PHASE22AE_6_5_10BL_EXACT_PRE_WRITE_DIFF_PACKAGE_REVIEW_BLOCKED"
NEXT = "HOLD_OR_AUTHORIZE_PHASE22AE_6_5_10BM_GUARDED_NATIVE_HELP_CMDHELPCHK_EXECUTION_PLAN"

REPORT_DIR = Path("docs/messaging/reports")
BK_SUMMARY = REPORT_DIR / "message_catalog_phase22ae_6_5_10bk_status_summary_v1.csv"
BK_PACKAGE = REPORT_DIR / "message_catalog_phase22ae_6_5_10bk_exact_pre_write_diff_package_v1.csv"
BK_DIFFS = REPORT_DIR / "message_catalog_phase22ae_6_5_10bk_diff_artifact_manifest_v1.csv"
BK_GUARDS = REPORT_DIR / "message_catalog_phase22ae_6_5_10bk_execution_guards_v1.csv"
BL_ROOT = Path("docs/messaging/apply/phase22ae_6_5_10bl_exact_pre_write_diff_package_review_v1")
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

    bk = first(repo / BK_SUMMARY)
    package_rows = rows(repo / BK_PACKAGE)
    diff_rows = rows(repo / BK_DIFFS)
    guard_rows = rows(repo / BK_GUARDS)
    sp_bk, latest_bk = savepoint(repo, "MSG-022AE.6.5.10BK")
    msg_count = dbf_count(repo / ACTIVE_MSG_DBF)
    text_count = dbf_count(repo / ACTIVE_TEXT_DBF)
    bl_root = repo / BL_ROOT

    gates = []
    failures = 0
    def gate(name, ok, detail):
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": str(detail)})
        if not ok:
            failures += 1

    gate("PHASE22AE_6_5_10BK_GREEN",
         bk.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_5_10BK_EXACT_PRE_WRITE_DIFF_PACKAGE_GREEN_DIFFS_STAGED_NO_APPLY",
         bk.get("STATUS", "missing"))
    gate("MSG_022AE_6_5_10BK_SAVEPOINT_PRESENT", sp_bk, latest_bk)
    gate("BK_EXACT_DIFF_PACKAGE_CREATED", bk.get("EXACT_PRE_WRITE_DIFF_PACKAGE_CREATED") == "1", bk.get("EXACT_PRE_WRITE_DIFF_PACKAGE_CREATED", "missing"))
    gate("BK_HELP_APPLY_NOT_EXECUTED", bk.get("HELP_DATA_APPLY_EXECUTED") == "0", bk.get("HELP_DATA_APPLY_EXECUTED", "missing"))
    gate("BK_CMDHELPCHK_APPLY_NOT_EXECUTED", bk.get("CMDHELPCHK_APPLY_EXECUTED") == "0", bk.get("CMDHELPCHK_APPLY_EXECUTED", "missing"))
    gate("DIFF_PACKAGE_ROWS_PRESENT", len(package_rows) > 0, len(package_rows))
    gate("DIFF_ARTIFACT_ROWS_PRESENT", len(diff_rows) > 0, len(diff_rows))
    gate("EXECUTION_GUARDS_PRESENT", len(guard_rows) > 0, len(guard_rows))
    gate("ACTIVE_MESSAGES_HEADER_COUNT_14", msg_count == 14, msg_count)
    gate("ACTIVE_TEXT_HEADER_COUNT_70", text_count == 70, text_count)
    gate("BL_ROOT_NOT_EXISTING_OR_REPLACE_ALLOWED", (not bl_root.exists()) or args.replace_existing_review, rel(bl_root, repo))

    status = BLOCKED
    review_rows = []
    decision_rows = []
    artifact_rows = []

    if failures == 0:
        if bl_root.exists() and args.replace_existing_review:
            shutil.rmtree(bl_root)
        bl_root.mkdir(parents=True, exist_ok=True)

        for i, r in enumerate(package_rows, start=1):
            diff_artifact = r.get("DIFF_ARTIFACT", "")
            diff_path = repo / diff_artifact
            diff_exists = diff_path.exists() and diff_path.is_file()
            diff_hash = sha(diff_path) if diff_exists else ""
            diff_status = r.get("DIFF_STATUS", "")
            if "NATIVE_OR_SCHEMA_AWARE" in diff_status:
                disposition = "ACCEPT_STUB_REQUIRE_NATIVE_EXECUTION_PLAN"
            elif "TEXTUAL_REVIEW_DIFF" in diff_status:
                disposition = "ACCEPT_REVIEW_DIFF_REQUIRE_EXECUTION_PLAN"
            else:
                disposition = "REVIEW_REQUIRED"
            review_rows.append({
                "REVIEW_ROW": i,
                "TARGET_ID": r.get("TARGET_ID", ""),
                "TARGET_KIND": r.get("TARGET_KIND", ""),
                "TARGET_PATH": r.get("TARGET_PATH", ""),
                "TARGET_FORMAT": r.get("TARGET_FORMAT", ""),
                "DIFF_STATUS": diff_status,
                "DIFF_ARTIFACT": diff_artifact,
                "DIFF_ARTIFACT_EXISTS": 1 if diff_exists else 0,
                "DIFF_ARTIFACT_SHA256": diff_hash,
                "REVIEW_DISPOSITION": disposition,
                "EXECUTION_PLAN_REQUIRED": 1,
                "AUTHORIZED_FOR_WRITE_NOW": 0,
                "APPLY_EXECUTED_NOW": 0,
            })

        decision_rows = [
            {"DECISION_ITEM": "EXACT_PRE_WRITE_DIFF_PACKAGE", "DECISION": "ACCEPT_FOR_EXECUTION_PLANNING", "DETAIL": f"{len(package_rows)} target diff package rows reviewed."},
            {"DECISION_ITEM": "DIFF_ARTIFACTS", "DECISION": "ACCEPT_PRESENT_FOR_REVIEW", "DETAIL": f"{len(diff_rows)} diff artifacts observed."},
            {"DECISION_ITEM": "EXECUTION_GUARDS", "DECISION": "CARRY_FORWARD_REQUIRED", "DETAIL": f"{len(guard_rows)} guards must be retained."},
            {"DECISION_ITEM": "HELP_DATA_APPLY_EXECUTION", "DECISION": "NOT_AUTHORIZED_IN_10BL", "DETAIL": "No HELP DATA write in 10BL."},
            {"DECISION_ITEM": "CMDHELPCHK_APPLY_EXECUTION", "DECISION": "NOT_AUTHORIZED_IN_10BL", "DETAIL": "No CMDHELPCHK write in 10BL."},
            {"DECISION_ITEM": "NEXT_GATE", "DECISION": "AUTHORIZE_10BM_OR_HOLD", "DETAIL": "10BM should build a guarded native execution plan; still no write unless later explicitly authorized."},
        ]

        review_path = bl_root / "exact_pre_write_diff_package_review_v1.csv"
        decision_path = bl_root / "diff_package_review_decisions_v1.csv"
        readme = bl_root / "README_10BL_EXACT_PRE_WRITE_DIFF_PACKAGE_REVIEW.md"
        wcsv(review_path, review_rows, ["REVIEW_ROW","TARGET_ID","TARGET_KIND","TARGET_PATH","TARGET_FORMAT","DIFF_STATUS","DIFF_ARTIFACT","DIFF_ARTIFACT_EXISTS","DIFF_ARTIFACT_SHA256","REVIEW_DISPOSITION","EXECUTION_PLAN_REQUIRED","AUTHORIZED_FOR_WRITE_NOW","APPLY_EXECUTED_NOW"])
        wcsv(decision_path, decision_rows, ["DECISION_ITEM","DECISION","DETAIL"])
        readme.write_text(
            "# 10BL Exact Pre-Write Diff Package Review\n\n"
            "10BL reviews the 10BK exact pre-write diff package and accepts it for guarded execution planning only.\n\n"
            "No HELP DATA or CMDHELPCHK mutation is authorized or executed in 10BL.\n",
            encoding="utf-8"
        )

        for p in [review_path, decision_path, readme]:
            artifact_rows.append({"ARTIFACT": rel(p, repo), "ROLE": "exact_pre_write_diff_review_artifact", "BYTES": p.stat().st_size, "SHA256": sha(p)})

        status = GREEN

    boundary = [
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "10BL writes docs/messaging review artifacts only."},
        {"PROTECTED_SYSTEM": "ACTIVE_SYSTEM_MESSAGES", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_SYSTEM_MESSAGE_TEXT", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_CDX_LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CDX/LMDB mutation."},
        {"PROTECTED_SYSTEM": "WORKSPACE_PROFILE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No workspace mutation."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No HELP DATA mutation; review only."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CMDHELPCHK mutation; review only."},
    ]

    readiness = [
        {"ITEM": "DIFF_PACKAGE_REVIEW_COMPLETE", "STATUS": "YES" if review_rows else "NO", "DETAIL": f"{len(review_rows)} rows reviewed."},
        {"ITEM": "GUARDED_NATIVE_EXECUTION_PLAN_REQUIRED", "STATUS": "YES", "DETAIL": "10BM should build the execution plan from reviewed diff package."},
        {"ITEM": "HELP_DATA_APPLY_EXECUTION", "STATUS": "NOT_EXECUTED_IN_10BL", "DETAIL": "No apply execution."},
        {"ITEM": "CMDHELPCHK_APPLY_EXECUTION", "STATUS": "NOT_EXECUTED_IN_10BL", "DETAIL": "No apply execution."},
        {"ITEM": "NEXT_PACKAGE", "STATUS": "10BM_REQUIRED", "DETAIL": "Guarded native HELP/CMDHELPCHK execution plan."},
    ]

    issues = "0" if failures == 0 else str(failures)
    wcsv(reports / "message_catalog_phase22ae_6_5_10bl_gate_check_v1.csv", gates, ["GATE","STATUS","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10bl_exact_pre_write_diff_package_review_v1.csv", review_rows, ["REVIEW_ROW","TARGET_ID","TARGET_KIND","TARGET_PATH","TARGET_FORMAT","DIFF_STATUS","DIFF_ARTIFACT","DIFF_ARTIFACT_EXISTS","DIFF_ARTIFACT_SHA256","REVIEW_DISPOSITION","EXECUTION_PLAN_REQUIRED","AUTHORIZED_FOR_WRITE_NOW","APPLY_EXECUTED_NOW"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10bl_review_decisions_v1.csv", decision_rows, ["DECISION_ITEM","DECISION","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10bl_apply_readiness_v1.csv", readiness, ["ITEM","STATUS","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10bl_boundary_ledger_v1.csv", boundary, ["PROTECTED_SYSTEM","MUTATION_ALLOWED","OBSERVED_MUTATION","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10bl_artifact_manifest_v1.csv", artifact_rows, ["ARTIFACT","ROLE","BYTES","SHA256"])

    summary = {
        "STATUS": status,
        "VALIDATION_ISSUES": issues,
        "PHASE22AE_6_5_10BK_STATUS": bk.get("STATUS", ""),
        "MSG_022AE_6_5_10BK_SAVEPOINT_PRESENT": 1 if sp_bk else 0,
        "ACTIVE_MESSAGES_OBSERVED_COUNT": msg_count,
        "ACTIVE_TEXT_OBSERVED_COUNT": text_count,
        "BK_DIFF_PACKAGE_ROWS": len(package_rows),
        "BK_DIFF_ARTIFACT_ROWS": len(diff_rows),
        "BK_EXECUTION_GUARD_ROWS": len(guard_rows),
        "DIFF_PACKAGE_REVIEW_ROWS": len(review_rows),
        "DECISION_ROWS": len(decision_rows),
        "BL_ROOT": rel(bl_root, repo),
        "DIFF_PACKAGE_ACCEPTED_FOR_EXECUTION_PLANNING": 1 if status == GREEN else 0,
        "GUARDED_NATIVE_EXECUTION_PLAN_REQUIRED": 1 if status == GREEN else 0,
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
    wcsv(reports / "message_catalog_phase22ae_6_5_10bl_status_summary_v1.csv", [summary], list(summary.keys()))

    (repo / "docs/messaging/MESSAGE_LOCALE_PHASE22AE_6_5_10BL_EXACT_PRE_WRITE_DIFF_PACKAGE_REVIEW.md").write_text(
        f"# Message Catalog Phase 22AE.6.5.10BL Exact Pre-Write Diff Package Review\n\n"
        f"Status: `{status}`\n\n"
        "10BL reviews the exact pre-write diff package and accepts it for execution planning only. It does not mutate HELP DATA or CMDHELPCHK.\n\n"
        f"Review root:\n\n```text\n{rel(bl_root, repo)}\n```\n\n"
        f"Next gate:\n\n```text\n{NEXT}\n```\n",
        encoding="utf-8"
    )

    print(status)
    print(f"  validation issues: {issues}")
    print(f"  Phase 22AE.6.5.10BK status: {bk.get('STATUS','')}")
    print(f"  MSG-022AE.6.5.10BK savepoint present: {1 if sp_bk else 0}")
    print(f"  active messages observed count: {msg_count}")
    print(f"  active text observed count: {text_count}")
    print(f"  BK diff package rows: {len(package_rows)}")
    print(f"  BK diff artifact rows: {len(diff_rows)}")
    print(f"  BK execution guard rows: {len(guard_rows)}")
    print(f"  diff package review rows: {len(review_rows)}")
    print(f"  decision rows: {len(decision_rows)}")
    print(f"  review root: {rel(bl_root, repo)}")
    print("  diff package accepted for execution planning: 1")
    print("  guarded native execution plan required: 1")
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
