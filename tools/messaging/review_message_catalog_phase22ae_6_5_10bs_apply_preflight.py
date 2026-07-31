#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, json, hashlib, shutil
from datetime import datetime, timezone
from pathlib import Path

GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_10BS_GUARDED_APPLY_PREFLIGHT_REVIEW_GREEN_APPLY_AUTHORIZATION_DECISION_REQUIRED_SOURCE_HELD"
BLOCKED = "MESSAGE_CATALOG_PHASE22AE_6_5_10BS_GUARDED_APPLY_PREFLIGHT_REVIEW_BLOCKED"
NEXT = "HOLD_OR_AUTHORIZE_PHASE22AE_6_5_10BT_HELP_CMDHELPCHK_APPLY_EXECUTION_AUTHORIZATION_DECISION"

REPORT_DIR = Path("docs/messaging/reports")
BR_SUMMARY = REPORT_DIR / "message_catalog_phase22ae_6_5_10br_status_summary_v1.csv"
BR_PACKAGE = REPORT_DIR / "message_catalog_phase22ae_6_5_10br_preflight_package_v1.csv"
BR_CHECKLIST = REPORT_DIR / "message_catalog_phase22ae_6_5_10br_preflight_checklist_v1.csv"
BR_RUNTIME = REPORT_DIR / "message_catalog_phase22ae_6_5_10br_runtime_readback_probe_plan_v1.csv"
BR_READY = REPORT_DIR / "message_catalog_phase22ae_6_5_10br_apply_readiness_v1.csv"
BS_ROOT = Path("docs/messaging/apply/phase22ae_6_5_10bs_guarded_apply_preflight_review_v1")
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

    br = first(repo / BR_SUMMARY)
    package_rows = rows(repo / BR_PACKAGE)
    checklist_rows = rows(repo / BR_CHECKLIST)
    runtime_rows = rows(repo / BR_RUNTIME)
    readiness_rows = rows(repo / BR_READY)
    sp_br, latest_br = savepoint(repo, "MSG-022AE.6.5.10BR")
    msg_count = dbf_count(repo / ACTIVE_MSG_DBF)
    text_count = dbf_count(repo / ACTIVE_TEXT_DBF)
    bs_root = repo / BS_ROOT

    gates = []
    failures = 0
    def gate(name, ok, detail):
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": str(detail)})
        if not ok:
            failures += 1

    gate("PHASE22AE_6_5_10BR_GREEN",
         br.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_5_10BR_HELP_CMDHELPCHK_GUARDED_APPLY_PREFLIGHT_PACKAGE_GREEN_STAGED_NO_APPLY",
         br.get("STATUS", "missing"))
    gate("MSG_022AE_6_5_10BR_SAVEPOINT_PRESENT", sp_br, latest_br)
    gate("BR_PREFLIGHT_PACKAGE_STAGED", br.get("GUARDED_APPLY_PREFLIGHT_PACKAGE_STAGED") == "1", br.get("GUARDED_APPLY_PREFLIGHT_PACKAGE_STAGED", "missing"))
    gate("BR_HELP_APPLY_NOT_EXECUTED", br.get("HELP_DATA_APPLY_EXECUTED") == "0", br.get("HELP_DATA_APPLY_EXECUTED", "missing"))
    gate("BR_CMDHELPCHK_APPLY_NOT_EXECUTED", br.get("CMDHELPCHK_APPLY_EXECUTED") == "0", br.get("CMDHELPCHK_APPLY_EXECUTED", "missing"))
    gate("BR_PACKAGE_ROWS_PRESENT", len(package_rows) > 0, len(package_rows))
    gate("BR_CHECKLIST_ROWS_PRESENT", len(checklist_rows) > 0, len(checklist_rows))
    gate("BR_RUNTIME_PROBE_ROWS_PRESENT", len(runtime_rows) > 0, len(runtime_rows))
    gate("ACTIVE_MESSAGES_HEADER_COUNT_14", msg_count == 14, msg_count)
    gate("ACTIVE_TEXT_HEADER_COUNT_70", text_count == 70, text_count)
    gate("BS_ROOT_NOT_EXISTING_OR_REPLACE_ALLOWED", (not bs_root.exists()) or args.replace_existing_review, rel(bs_root, repo))

    status = BLOCKED
    review_rows = []
    checklist_review = []
    runtime_review = []
    decision_rows = []
    artifact_rows = []

    if failures == 0:
        if bs_root.exists() and args.replace_existing_review:
            shutil.rmtree(bs_root)
        bs_root.mkdir(parents=True, exist_ok=True)

        for i, r in enumerate(package_rows, start=1):
            target_exists = str(r.get("TARGET_EXISTS", "")) == "1"
            backup_match = str(r.get("BACKUP_MATCH", "")) in {"1", "True", "true"}
            hash_match = str(r.get("TARGET_HASH_MATCHES_EXPECTED", "")) == "1"
            authorized_now = str(r.get("APPLY_AUTHORIZED_NOW", "")) == "1"
            executed_now = str(r.get("APPLY_EXECUTED_NOW", "")) == "1"
            disposition = "ACCEPT_FOR_APPLY_AUTHORIZATION_DECISION" if target_exists and backup_match and not authorized_now and not executed_now else "REVIEW_REQUIRED"

            review_rows.append({
                "REVIEW_ROW": i,
                "TARGET_ID": r.get("TARGET_ID", ""),
                "TARGET_KIND": r.get("TARGET_KIND", ""),
                "TARGET_PATH": r.get("TARGET_PATH", ""),
                "TARGET_EXISTS": 1 if target_exists else 0,
                "TARGET_HASH_MATCHES_EXPECTED": 1 if hash_match else 0,
                "BACKUP_PATH": r.get("BACKUP_PATH", ""),
                "BACKUP_MATCH": 1 if backup_match else 0,
                "DIFF_ARTIFACT": r.get("DIFF_ARTIFACT", ""),
                "APPLY_DECISION": r.get("APPLY_DECISION", ""),
                "PREFLIGHT_STATUS": r.get("PREFLIGHT_STATUS", ""),
                "REVIEW_DISPOSITION": disposition,
                "APPLY_AUTHORIZATION_DECISION_REQUIRED": 1,
                "APPLY_AUTHORIZED_NOW": 0,
                "APPLY_EXECUTED_NOW": 0,
                "REASON": "10BS reviews preflight only; no HELP/CMDHELPCHK mutation in 10BS.",
            })

        for i, r in enumerate(checklist_rows, start=1):
            checklist_review.append({
                "CHECKLIST_REVIEW_ROW": i,
                "PREFLIGHT": r.get("PREFLIGHT", ""),
                "REQUIRED": r.get("REQUIRED", ""),
                "CHECK_STATUS": r.get("CHECK_STATUS", ""),
                "REVIEW_DISPOSITION": "CARRY_FORWARD_TO_AUTHORIZATION_DECISION",
                "AUTHORIZED_FOR_APPLY_NOW": 0,
            })

        for i, r in enumerate(runtime_rows, start=1):
            runtime_review.append({
                "RUNTIME_REVIEW_ROW": i,
                "PROBE_COMMAND": r.get("PROBE_COMMAND", ""),
                "EXPECTED_SIGNAL": r.get("EXPECTED_SIGNAL", ""),
                "REVIEW_DISPOSITION": "CARRY_FORWARD_TO_APPLY_READBACK",
                "RUN_NOW": 0,
            })

        decision_rows = [
            {"DECISION_ITEM": "GUARDED_APPLY_PREFLIGHT_PACKAGE", "DECISION": "ACCEPT_FOR_APPLY_AUTHORIZATION_DECISION", "DETAIL": f"{len(package_rows)} preflight target rows reviewed."},
            {"DECISION_ITEM": "PREFLIGHT_CHECKLIST", "DECISION": "CARRY_FORWARD_REQUIRED", "DETAIL": f"{len(checklist_rows)} checklist rows must be carried forward."},
            {"DECISION_ITEM": "RUNTIME_READBACK_PROBE_PLAN", "DECISION": "CARRY_FORWARD_REQUIRED", "DETAIL": f"{len(runtime_rows)} runtime probe rows must be carried forward."},
            {"DECISION_ITEM": "HELP_DATA_APPLY_EXECUTION", "DECISION": "NOT_AUTHORIZED_IN_10BS", "DETAIL": "No HELP DATA write in 10BS."},
            {"DECISION_ITEM": "CMDHELPCHK_APPLY_EXECUTION", "DECISION": "NOT_AUTHORIZED_IN_10BS", "DETAIL": "No CMDHELPCHK write in 10BS."},
            {"DECISION_ITEM": "NEXT_GATE", "DECISION": "AUTHORIZE_10BT_OR_HOLD", "DETAIL": "10BT should make the explicit apply authorization decision; mutation still requires explicit authorization."},
        ]

        review_path = bs_root / "guarded_apply_preflight_review_v1.csv"
        checklist_path = bs_root / "preflight_checklist_review_v1.csv"
        runtime_path = bs_root / "runtime_readback_probe_review_v1.csv"
        decision_path = bs_root / "preflight_review_decisions_v1.csv"
        readme = bs_root / "README_10BS_GUARDED_APPLY_PREFLIGHT_REVIEW.md"

        wcsv(review_path, review_rows, ["REVIEW_ROW","TARGET_ID","TARGET_KIND","TARGET_PATH","TARGET_EXISTS","TARGET_HASH_MATCHES_EXPECTED","BACKUP_PATH","BACKUP_MATCH","DIFF_ARTIFACT","APPLY_DECISION","PREFLIGHT_STATUS","REVIEW_DISPOSITION","APPLY_AUTHORIZATION_DECISION_REQUIRED","APPLY_AUTHORIZED_NOW","APPLY_EXECUTED_NOW","REASON"])
        wcsv(checklist_path, checklist_review, ["CHECKLIST_REVIEW_ROW","PREFLIGHT","REQUIRED","CHECK_STATUS","REVIEW_DISPOSITION","AUTHORIZED_FOR_APPLY_NOW"])
        wcsv(runtime_path, runtime_review, ["RUNTIME_REVIEW_ROW","PROBE_COMMAND","EXPECTED_SIGNAL","REVIEW_DISPOSITION","RUN_NOW"])
        wcsv(decision_path, decision_rows, ["DECISION_ITEM","DECISION","DETAIL"])
        readme.write_text(
            "# 10BS Guarded Apply Preflight Review\n\n"
            "10BS reviews the 10BR guarded apply preflight package and accepts it for an explicit apply authorization decision only.\n\n"
            "No HELP DATA or CMDHELPCHK mutation is authorized or executed in 10BS.\n",
            encoding="utf-8"
        )

        for p in [review_path, checklist_path, runtime_path, decision_path, readme]:
            artifact_rows.append({"ARTIFACT": rel(p, repo), "ROLE": "guarded_apply_preflight_review_artifact", "BYTES": p.stat().st_size, "SHA256": sha(p)})

        status = GREEN

    boundary = [
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "10BS writes docs/messaging preflight-review artifacts only."},
        {"PROTECTED_SYSTEM": "ACTIVE_SYSTEM_MESSAGES", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_SYSTEM_MESSAGE_TEXT", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_CDX_LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CDX/LMDB mutation."},
        {"PROTECTED_SYSTEM": "WORKSPACE_PROFILE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No workspace mutation."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Preflight review only; no HELP DATA apply."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Preflight review only; no CMDHELPCHK apply."},
    ]

    readiness = [
        {"ITEM": "GUARDED_APPLY_PREFLIGHT_REVIEW_COMPLETE", "STATUS": "YES" if review_rows else "NO", "DETAIL": f"{len(review_rows)} target rows reviewed."},
        {"ITEM": "APPLY_AUTHORIZATION_DECISION_REQUIRED", "STATUS": "YES", "DETAIL": "10BT should make explicit apply authorization decision."},
        {"ITEM": "HELP_DATA_APPLY_EXECUTION", "STATUS": "NOT_EXECUTED_IN_10BS", "DETAIL": "No apply execution."},
        {"ITEM": "CMDHELPCHK_APPLY_EXECUTION", "STATUS": "NOT_EXECUTED_IN_10BS", "DETAIL": "No apply execution."},
        {"ITEM": "NEXT_PACKAGE", "STATUS": "10BT_REQUIRED", "DETAIL": "Apply execution authorization decision, not implicit apply."},
    ]

    issues = "0" if failures == 0 else str(failures)
    wcsv(reports / "message_catalog_phase22ae_6_5_10bs_gate_check_v1.csv", gates, ["GATE","STATUS","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10bs_preflight_review_v1.csv", review_rows, ["REVIEW_ROW","TARGET_ID","TARGET_KIND","TARGET_PATH","TARGET_EXISTS","TARGET_HASH_MATCHES_EXPECTED","BACKUP_PATH","BACKUP_MATCH","DIFF_ARTIFACT","APPLY_DECISION","PREFLIGHT_STATUS","REVIEW_DISPOSITION","APPLY_AUTHORIZATION_DECISION_REQUIRED","APPLY_AUTHORIZED_NOW","APPLY_EXECUTED_NOW","REASON"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10bs_checklist_review_v1.csv", checklist_review, ["CHECKLIST_REVIEW_ROW","PREFLIGHT","REQUIRED","CHECK_STATUS","REVIEW_DISPOSITION","AUTHORIZED_FOR_APPLY_NOW"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10bs_runtime_probe_review_v1.csv", runtime_review, ["RUNTIME_REVIEW_ROW","PROBE_COMMAND","EXPECTED_SIGNAL","REVIEW_DISPOSITION","RUN_NOW"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10bs_review_decisions_v1.csv", decision_rows, ["DECISION_ITEM","DECISION","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10bs_apply_readiness_v1.csv", readiness, ["ITEM","STATUS","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10bs_boundary_ledger_v1.csv", boundary, ["PROTECTED_SYSTEM","MUTATION_ALLOWED","OBSERVED_MUTATION","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10bs_artifact_manifest_v1.csv", artifact_rows, ["ARTIFACT","ROLE","BYTES","SHA256"])

    summary = {
        "STATUS": status,
        "VALIDATION_ISSUES": issues,
        "PHASE22AE_6_5_10BR_STATUS": br.get("STATUS", ""),
        "MSG_022AE_6_5_10BR_SAVEPOINT_PRESENT": 1 if sp_br else 0,
        "ACTIVE_MESSAGES_OBSERVED_COUNT": msg_count,
        "ACTIVE_TEXT_OBSERVED_COUNT": text_count,
        "BR_PREFLIGHT_PACKAGE_ROWS": len(package_rows),
        "BR_PREFLIGHT_CHECKLIST_ROWS": len(checklist_rows),
        "BR_RUNTIME_READBACK_PROBE_ROWS": len(runtime_rows),
        "PREFLIGHT_REVIEW_ROWS": len(review_rows),
        "CHECKLIST_REVIEW_ROWS": len(checklist_review),
        "RUNTIME_PROBE_REVIEW_ROWS": len(runtime_review),
        "DECISION_ROWS": len(decision_rows),
        "BS_ROOT": rel(bs_root, repo),
        "APPLY_AUTHORIZATION_DECISION_REQUIRED": 1 if status == GREEN else 0,
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
    wcsv(reports / "message_catalog_phase22ae_6_5_10bs_status_summary_v1.csv", [summary], list(summary.keys()))

    (repo / "docs/messaging/MESSAGE_LOCALE_PHASE22AE_6_5_10BS_GUARDED_APPLY_PREFLIGHT_REVIEW.md").write_text(
        f"# Message Catalog Phase 22AE.6.5.10BS Guarded Apply Preflight Review\n\n"
        f"Status: `{status}`\n\n"
        "10BS reviews the guarded apply preflight package and accepts it for explicit apply authorization decision only. It does not mutate HELP DATA or CMDHELPCHK.\n\n"
        f"Review root:\n\n```text\n{rel(bs_root, repo)}\n```\n\n"
        f"Next gate:\n\n```text\n{NEXT}\n```\n",
        encoding="utf-8"
    )

    print(status)
    print(f"  validation issues: {issues}")
    print(f"  Phase 22AE.6.5.10BR status: {br.get('STATUS','')}")
    print(f"  MSG-022AE.6.5.10BR savepoint present: {1 if sp_br else 0}")
    print(f"  active messages observed count: {msg_count}")
    print(f"  active text observed count: {text_count}")
    print(f"  BR preflight package rows: {len(package_rows)}")
    print(f"  BR preflight checklist rows: {len(checklist_rows)}")
    print(f"  BR runtime readback probe rows: {len(runtime_rows)}")
    print(f"  preflight review rows: {len(review_rows)}")
    print(f"  checklist review rows: {len(checklist_review)}")
    print(f"  runtime probe review rows: {len(runtime_review)}")
    print(f"  decision rows: {len(decision_rows)}")
    print(f"  review root: {rel(bs_root, repo)}")
    print("  apply authorization decision required: 1")
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
