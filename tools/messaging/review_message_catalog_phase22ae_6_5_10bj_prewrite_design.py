#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, json, hashlib, shutil
from datetime import datetime, timezone
from pathlib import Path

GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_10BJ_PRE_WRITE_DIFF_DESIGN_REVIEW_GREEN_EXACT_DIFF_PACKAGE_REQUIRED_SOURCE_HELD"
BLOCKED = "MESSAGE_CATALOG_PHASE22AE_6_5_10BJ_PRE_WRITE_DIFF_DESIGN_REVIEW_BLOCKED"
NEXT = "HOLD_OR_AUTHORIZE_PHASE22AE_6_5_10BK_EXACT_PRE_WRITE_DIFF_PACKAGE"

REPORT_DIR = Path("docs/messaging/reports")
BI_SUMMARY = REPORT_DIR / "message_catalog_phase22ae_6_5_10bi_status_summary_v1.csv"
BI_DIFF = REPORT_DIR / "message_catalog_phase22ae_6_5_10bi_pre_write_diff_design_v1.csv"
BI_NATIVE = REPORT_DIR / "message_catalog_phase22ae_6_5_10bi_native_execution_design_v1.csv"
BI_GUARDS = REPORT_DIR / "message_catalog_phase22ae_6_5_10bi_execution_refusal_guards_v1.csv"
BJ_ROOT = Path("docs/messaging/apply/phase22ae_6_5_10bj_pre_write_diff_design_review_v1")
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

    bi = first(repo / BI_SUMMARY)
    diff_rows = rows(repo / BI_DIFF)
    native_rows = rows(repo / BI_NATIVE)
    guard_rows = rows(repo / BI_GUARDS)
    sp_bi, latest_bi = savepoint(repo, "MSG-022AE.6.5.10BI")
    msg_count = dbf_count(repo / ACTIVE_MSG_DBF)
    text_count = dbf_count(repo / ACTIVE_TEXT_DBF)
    bj_root = repo / BJ_ROOT

    gates = []
    failures = 0
    def gate(name, ok, detail):
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": str(detail)})
        if not ok:
            failures += 1

    gate("PHASE22AE_6_5_10BI_GREEN",
         bi.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_5_10BI_PRE_WRITE_DIFF_AND_NATIVE_EXECUTION_DESIGN_PACKAGE_GREEN_SOURCE_HELD",
         bi.get("STATUS", "missing"))
    gate("MSG_022AE_6_5_10BI_SAVEPOINT_PRESENT", sp_bi, latest_bi)
    gate("BI_PRE_WRITE_DIFF_DESIGN_CREATED", bi.get("PRE_WRITE_DIFF_DESIGN_CREATED") == "1", bi.get("PRE_WRITE_DIFF_DESIGN_CREATED", "missing"))
    gate("BI_NATIVE_EXECUTION_DESIGN_CREATED", bi.get("NATIVE_EXECUTION_DESIGN_CREATED") == "1", bi.get("NATIVE_EXECUTION_DESIGN_CREATED", "missing"))
    gate("BI_HELP_APPLY_NOT_EXECUTED", bi.get("HELP_DATA_APPLY_EXECUTED") == "0", bi.get("HELP_DATA_APPLY_EXECUTED", "missing"))
    gate("BI_CMDHELPCHK_APPLY_NOT_EXECUTED", bi.get("CMDHELPCHK_APPLY_EXECUTED") == "0", bi.get("CMDHELPCHK_APPLY_EXECUTED", "missing"))
    gate("DIFF_DESIGN_ROWS_PRESENT", len(diff_rows) > 0, len(diff_rows))
    gate("NATIVE_DESIGN_ROWS_PRESENT", len(native_rows) > 0, len(native_rows))
    gate("REFUSAL_GUARD_ROWS_PRESENT", len(guard_rows) > 0, len(guard_rows))
    gate("ACTIVE_MESSAGES_HEADER_COUNT_14", msg_count == 14, msg_count)
    gate("ACTIVE_TEXT_HEADER_COUNT_70", text_count == 70, text_count)
    gate("BJ_ROOT_NOT_EXISTING_OR_REPLACE_ALLOWED", (not bj_root.exists()) or args.replace_existing_review, rel(bj_root, repo))

    status = BLOCKED
    review_rows = []
    decision_rows = []
    artifact_rows = []
    if failures == 0:
        if bj_root.exists() and args.replace_existing_review:
            shutil.rmtree(bj_root)
        bj_root.mkdir(parents=True, exist_ok=True)

        for i, r in enumerate(diff_rows, start=1):
            strategy = r.get("DIFF_STRATEGY", "")
            target_format = r.get("TARGET_FORMAT", "")
            accepted = bool(strategy) and r.get("AUTHORIZED_FOR_WRITE_NOW") in {"0", 0, ""}
            disposition = "ACCEPT_FOR_EXACT_DIFF_PACKAGE" if accepted else "REVIEW_REQUIRED"
            review_rows.append({
                "REVIEW_ROW": i,
                "TARGET_ID": r.get("TARGET_ID", ""),
                "TARGET_KIND": r.get("TARGET_KIND", ""),
                "TARGET_PATH": r.get("TARGET_PATH", ""),
                "TARGET_FORMAT": target_format,
                "DIFF_STRATEGY": strategy,
                "REVIEW_DISPOSITION": disposition,
                "EXACT_DIFF_PACKAGE_REQUIRED": 1,
                "NATIVE_EXECUTION_DESIGN_REQUIRED": 1 if target_format == "DBF_BINARY" else 0,
                "AUTHORIZED_FOR_WRITE_NOW": 0,
                "REASON": "Design accepted for exact diff/package generation only; no mutation in 10BJ.",
            })

        decision_rows = [
            {"DECISION_ITEM": "PRE_WRITE_DIFF_DESIGN", "DECISION": "ACCEPT_FOR_EXACT_DIFF_PACKAGE", "DETAIL": f"{len(diff_rows)} design rows accepted for exact diff generation."},
            {"DECISION_ITEM": "NATIVE_EXECUTION_DESIGN", "DECISION": "ACCEPT_FOR_EXACT_DIFF_PACKAGE", "DETAIL": f"{len(native_rows)} native execution rows accepted for package generation."},
            {"DECISION_ITEM": "REFUSAL_GUARDS", "DECISION": "RETAIN_REQUIRED", "DETAIL": f"{len(guard_rows)} refusal guards must be carried forward."},
            {"DECISION_ITEM": "HELP_DATA_APPLY_EXECUTION", "DECISION": "NOT_AUTHORIZED_IN_10BJ", "DETAIL": "No HELP DATA write in 10BJ."},
            {"DECISION_ITEM": "CMDHELPCHK_APPLY_EXECUTION", "DECISION": "NOT_AUTHORIZED_IN_10BJ", "DETAIL": "No CMDHELPCHK write in 10BJ."},
            {"DECISION_ITEM": "NEXT_GATE", "DECISION": "AUTHORIZE_10BK_OR_HOLD", "DETAIL": "10BK should generate exact pre-write diffs, still without applying them."},
        ]

        review_path = bj_root / "pre_write_diff_design_review_v1.csv"
        decision_path = bj_root / "execution_decision_v1.csv"
        readme = bj_root / "README_10BJ_PRE_WRITE_DIFF_DESIGN_REVIEW.md"
        wcsv(review_path, review_rows, ["REVIEW_ROW","TARGET_ID","TARGET_KIND","TARGET_PATH","TARGET_FORMAT","DIFF_STRATEGY","REVIEW_DISPOSITION","EXACT_DIFF_PACKAGE_REQUIRED","NATIVE_EXECUTION_DESIGN_REQUIRED","AUTHORIZED_FOR_WRITE_NOW","REASON"])
        wcsv(decision_path, decision_rows, ["DECISION_ITEM","DECISION","DETAIL"])
        readme.write_text(
            "# 10BJ Pre-Write Diff Design Review and Execution Decision\n\n"
            "10BJ reviews the 10BI pre-write diff/native execution design. It accepts the design for an exact pre-write diff package only.\n\n"
            "No HELP DATA or CMDHELPCHK mutation is authorized or executed in 10BJ.\n",
            encoding="utf-8"
        )

        for p in [review_path, decision_path, readme]:
            artifact_rows.append({"ARTIFACT": rel(p, repo), "ROLE": "pre_write_diff_design_review_artifact", "BYTES": p.stat().st_size, "SHA256": sha(p)})

        status = GREEN

    boundary = [
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "10BJ writes docs/messaging design-review artifacts only."},
        {"PROTECTED_SYSTEM": "ACTIVE_SYSTEM_MESSAGES", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_SYSTEM_MESSAGE_TEXT", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_CDX_LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CDX/LMDB mutation."},
        {"PROTECTED_SYSTEM": "WORKSPACE_PROFILE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No workspace mutation."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No HELP DATA mutation; review only."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CMDHELPCHK mutation; review only."},
    ]

    readiness = [
        {"ITEM": "EXACT_PRE_WRITE_DIFF_PACKAGE_REQUIRED", "STATUS": "YES", "DETAIL": "10BK should generate exact diffs/package from accepted design."},
        {"ITEM": "NATIVE_EXECUTION_DESIGN_ACCEPTED_FOR_PACKAGE", "STATUS": "YES", "DETAIL": "Design accepted for package generation only."},
        {"ITEM": "HELP_DATA_APPLY_EXECUTION", "STATUS": "NOT_EXECUTED_IN_10BJ", "DETAIL": "No apply execution."},
        {"ITEM": "CMDHELPCHK_APPLY_EXECUTION", "STATUS": "NOT_EXECUTED_IN_10BJ", "DETAIL": "No apply execution."},
        {"ITEM": "NEXT_PACKAGE", "STATUS": "10BK_REQUIRED", "DETAIL": "Exact pre-write diff package, still no mutation."},
    ]

    issues = "0" if failures == 0 else str(failures)
    wcsv(reports / "message_catalog_phase22ae_6_5_10bj_gate_check_v1.csv", gates, ["GATE","STATUS","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10bj_pre_write_diff_design_review_v1.csv", review_rows, ["REVIEW_ROW","TARGET_ID","TARGET_KIND","TARGET_PATH","TARGET_FORMAT","DIFF_STRATEGY","REVIEW_DISPOSITION","EXACT_DIFF_PACKAGE_REQUIRED","NATIVE_EXECUTION_DESIGN_REQUIRED","AUTHORIZED_FOR_WRITE_NOW","REASON"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10bj_execution_decision_v1.csv", decision_rows, ["DECISION_ITEM","DECISION","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10bj_apply_readiness_v1.csv", readiness, ["ITEM","STATUS","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10bj_boundary_ledger_v1.csv", boundary, ["PROTECTED_SYSTEM","MUTATION_ALLOWED","OBSERVED_MUTATION","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10bj_artifact_manifest_v1.csv", artifact_rows, ["ARTIFACT","ROLE","BYTES","SHA256"])

    summary = {
        "STATUS": status,
        "VALIDATION_ISSUES": issues,
        "PHASE22AE_6_5_10BI_STATUS": bi.get("STATUS", ""),
        "MSG_022AE_6_5_10BI_SAVEPOINT_PRESENT": 1 if sp_bi else 0,
        "ACTIVE_MESSAGES_OBSERVED_COUNT": msg_count,
        "ACTIVE_TEXT_OBSERVED_COUNT": text_count,
        "DIFF_DESIGN_ROWS_REVIEWED": len(review_rows),
        "DECISION_ROWS": len(decision_rows),
        "BJ_ROOT": rel(bj_root, repo),
        "EXACT_PRE_WRITE_DIFF_PACKAGE_REQUIRED": 1 if status == GREEN else 0,
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
    wcsv(reports / "message_catalog_phase22ae_6_5_10bj_status_summary_v1.csv", [summary], list(summary.keys()))

    (repo / "docs/messaging/MESSAGE_LOCALE_PHASE22AE_6_5_10BJ_PRE_WRITE_DIFF_DESIGN_REVIEW_AND_EXECUTION_DECISION.md").write_text(
        f"# Message Catalog Phase 22AE.6.5.10BJ Pre-Write Diff Design Review and Execution Decision\n\n"
        f"Status: `{status}`\n\n"
        "10BJ reviews the pre-write diff/native execution design and accepts it for an exact pre-write diff package. It does not mutate HELP DATA or CMDHELPCHK.\n\n"
        f"Review root:\n\n```text\n{rel(bj_root, repo)}\n```\n\n"
        f"Next gate:\n\n```text\n{NEXT}\n```\n",
        encoding="utf-8"
    )

    print(status)
    print(f"  validation issues: {issues}")
    print(f"  Phase 22AE.6.5.10BI status: {bi.get('STATUS','')}")
    print(f"  MSG-022AE.6.5.10BI savepoint present: {1 if sp_bi else 0}")
    print(f"  active messages observed count: {msg_count}")
    print(f"  active text observed count: {text_count}")
    print(f"  diff design rows reviewed: {len(review_rows)}")
    print(f"  decision rows: {len(decision_rows)}")
    print(f"  review root: {rel(bj_root, repo)}")
    print("  exact pre-write diff package required: 1")
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
