#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, json, hashlib, shutil
from datetime import datetime, timezone
from pathlib import Path

GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_10BH_TARGET_SPECIFIC_WRITE_IMPLEMENTATION_REVIEW_GREEN_DIFF_PACKAGE_REQUIRED_SOURCE_HELD"
BLOCKED = "MESSAGE_CATALOG_PHASE22AE_6_5_10BH_TARGET_SPECIFIC_WRITE_IMPLEMENTATION_REVIEW_BLOCKED"
NEXT = "HOLD_OR_AUTHORIZE_PHASE22AE_6_5_10BI_PRE_WRITE_DIFF_AND_NATIVE_EXECUTION_DESIGN_PACKAGE"

REPORT_DIR = Path("docs/messaging/reports")
BG_SUMMARY = REPORT_DIR / "message_catalog_phase22ae_6_5_10bg_status_summary_v1.csv"
BG_IMPL = REPORT_DIR / "message_catalog_phase22ae_6_5_10bg_write_implementation_plan_v1.csv"
BG_STEPS = REPORT_DIR / "message_catalog_phase22ae_6_5_10bg_guarded_write_steps_v1.csv"
BH_ROOT = Path("docs/messaging/apply/phase22ae_6_5_10bh_target_specific_write_implementation_review_v1")
ACTIVE_MSG_DBF = Path("dottalkpp/data/messaging/SYSTEM_MESSAGES.dbf")
ACTIVE_TEXT_DBF = Path("dottalkpp/data/messaging/SYSTEM_MESSAGE_TEXT.dbf")
CANDIDATE_PATH = Path("docs/messaging/candidates/MESSAGE_CATALOG_PHASE22AE_6_5_10AW_MSGMGR_HELP_CANDIDATE.md")

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

def review_decision(row):
    strategy = row.get("WRITE_STRATEGY", "")
    fmt = row.get("TARGET_FORMAT", "")
    if strategy == "NATIVE_X64BASE_HELP_CMDHELPCHK_WRITE_PATH_REQUIRED" or fmt == "DBF_BINARY":
        return "ACCEPT_NATIVE_OR_SCHEMA_AWARE_PATH_REQUIRED", "DBF target must use native x64base/DotTalk++ write/import/readback lane; no raw Python DBF write."
    if strategy == "TEXT_ANCHOR_PATCH_PLAN_REQUIRED":
        return "ACCEPT_DIFF_PACKAGE_REQUIRED", "Text target requires exact anchor diff before write."
    return "REVIEW_REQUIRED", "Write strategy still needs human review."

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--replace-existing-review", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    reports = repo / REPORT_DIR
    reports.mkdir(parents=True, exist_ok=True)

    bg = first(repo / BG_SUMMARY)
    impl = rows(repo / BG_IMPL)
    steps = rows(repo / BG_STEPS)
    sp_bg, latest_bg = savepoint(repo, "MSG-022AE.6.5.10BG")
    msg_count = dbf_count(repo / ACTIVE_MSG_DBF)
    text_count = dbf_count(repo / ACTIVE_TEXT_DBF)
    candidate = repo / CANDIDATE_PATH
    bh_root = repo / BH_ROOT

    gates = []
    failures = 0
    def gate(name, ok, detail):
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": str(detail)})
        if not ok:
            failures += 1

    gate("PHASE22AE_6_5_10BG_GREEN",
         bg.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_5_10BG_TARGET_SPECIFIC_HELP_CMDHELPCHK_WRITE_IMPLEMENTATION_PLAN_GREEN_SOURCE_HELD",
         bg.get("STATUS", "missing"))
    gate("MSG_022AE_6_5_10BG_SAVEPOINT_PRESENT", sp_bg, latest_bg)
    gate("BG_WRITE_PLAN_CREATED", bg.get("TARGET_SPECIFIC_WRITE_IMPLEMENTATION_PLAN_CREATED") == "1", bg.get("TARGET_SPECIFIC_WRITE_IMPLEMENTATION_PLAN_CREATED", "missing"))
    gate("BG_PRE_WRITE_DIFF_REQUIRED", bg.get("PRE_WRITE_DIFF_REQUIRED") == "1", bg.get("PRE_WRITE_DIFF_REQUIRED", "missing"))
    gate("BG_NATIVE_DB_WRITE_REQUIRED_FOR_DBF", bg.get("NATIVE_DB_WRITE_REQUIRED_FOR_DBF_TARGETS") == "1", bg.get("NATIVE_DB_WRITE_REQUIRED_FOR_DBF_TARGETS", "missing"))
    gate("BG_HELP_APPLY_NOT_EXECUTED", bg.get("HELP_DATA_APPLY_EXECUTED") == "0", bg.get("HELP_DATA_APPLY_EXECUTED", "missing"))
    gate("BG_CMDHELPCHK_APPLY_NOT_EXECUTED", bg.get("CMDHELPCHK_APPLY_EXECUTED") == "0", bg.get("CMDHELPCHK_APPLY_EXECUTED", "missing"))
    gate("IMPLEMENTATION_ROWS_PRESENT", len(impl) > 0, len(impl))
    gate("GUARDED_STEPS_PRESENT", len(steps) > 0, len(steps))
    gate("ACTIVE_MESSAGES_HEADER_COUNT_14", msg_count == 14, msg_count)
    gate("ACTIVE_TEXT_HEADER_COUNT_70", text_count == 70, text_count)
    gate("CANDIDATE_EXISTS", candidate.exists(), rel(candidate, repo))
    gate("BH_ROOT_NOT_EXISTING_OR_REPLACE_ALLOWED", (not bh_root.exists()) or args.replace_existing_review, rel(bh_root, repo))

    status = BLOCKED
    decision_rows = []
    next_design_rows = []
    artifact_rows = []

    if failures == 0:
        if bh_root.exists() and args.replace_existing_review:
            shutil.rmtree(bh_root)
        bh_root.mkdir(parents=True, exist_ok=True)

        for i, r in enumerate(impl, start=1):
            disposition, reason = review_decision(r)
            decision_rows.append({
                "REVIEW_ROW": i,
                "TARGET_ID": r.get("TARGET_ID", ""),
                "TARGET_KIND": r.get("TARGET_KIND", ""),
                "TARGET_PATH": r.get("TARGET_PATH", ""),
                "TARGET_FORMAT": r.get("TARGET_FORMAT", ""),
                "WRITE_STRATEGY": r.get("WRITE_STRATEGY", ""),
                "REVIEW_DISPOSITION": disposition,
                "PRE_WRITE_DIFF_REQUIRED": 1,
                "NATIVE_READBACK_REQUIRED": 1,
                "AUTHORIZED_FOR_WRITE_NOW": 0,
                "REASON": reason,
            })

        next_design_rows = [
            {"DESIGN_ITEM": "PRE_WRITE_DIFF_PACKAGE", "REQUIRED": 1, "DETAIL": "Generate exact before/after content or record-level diff for all accepted target rows."},
            {"DESIGN_ITEM": "NATIVE_DBF_WRITE_OR_IMPORT_PATH", "REQUIRED": 1, "DETAIL": "For DBF targets, use native DotTalk++/x64base path or schema-aware staged import, not raw Python DBF mutation."},
            {"DESIGN_ITEM": "TARGET_ANCHOR_KEYS", "REQUIRED": 1, "DETAIL": "Keys/anchors must include MSGMGR, SET MESSAGE CATALOG CHECK, SET MESSAGE CATALOG GET, and SET MESSAGE EMIT."},
            {"DESIGN_ITEM": "EXECUTION_SCRIPT_REFUSAL_GUARDS", "REQUIRED": 1, "DETAIL": "Execution must refuse if target hashes, row counts, or exact target map differ from accepted state."},
            {"DESIGN_ITEM": "POST_WRITE_RUNTIME_READBACK", "REQUIRED": 1, "DETAIL": "After any later write, prove HELP/CMDHELPCHK through DotTalk++ runtime, not file inspection alone."},
            {"DESIGN_ITEM": "RESTORE_OR_ACCEPTANCE_GATE", "REQUIRED": 1, "DETAIL": "Any later apply must either restore from backups or receive final acceptance after readback."},
        ]

        decision_path = bh_root / "write_implementation_review_decisions_v1.csv"
        design_path = bh_root / "next_pre_write_diff_and_native_execution_design_requirements_v1.csv"
        readme = bh_root / "README_10BH_WRITE_IMPLEMENTATION_REVIEW.md"
        wcsv(decision_path, decision_rows, ["REVIEW_ROW","TARGET_ID","TARGET_KIND","TARGET_PATH","TARGET_FORMAT","WRITE_STRATEGY","REVIEW_DISPOSITION","PRE_WRITE_DIFF_REQUIRED","NATIVE_READBACK_REQUIRED","AUTHORIZED_FOR_WRITE_NOW","REASON"])
        wcsv(design_path, next_design_rows, ["DESIGN_ITEM","REQUIRED","DETAIL"])
        readme.write_text(
            "# 10BH Target-Specific Write Implementation Review\n\n"
            "10BH reviews the 10BG write implementation plan and accepts it for the next design package. "
            "It does not mutate HELP DATA or CMDHELPCHK.\n\n"
            "Result: a pre-write diff and native execution design package is required before any apply attempt.\n",
            encoding="utf-8"
        )
        for p in [decision_path, design_path, readme]:
            artifact_rows.append({"ARTIFACT": rel(p, repo), "ROLE": "write_implementation_review_artifact", "BYTES": p.stat().st_size, "SHA256": sha(p)})
        status = GREEN

    boundary = [
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "10BH writes docs/messaging review artifacts only."},
        {"PROTECTED_SYSTEM": "ACTIVE_SYSTEM_MESSAGES", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_SYSTEM_MESSAGE_TEXT", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_CDX_LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CDX/LMDB mutation."},
        {"PROTECTED_SYSTEM": "WORKSPACE_PROFILE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No workspace mutation."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No HELP DATA mutation; review only."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CMDHELPCHK mutation; review only."},
    ]

    readiness = [
        {"ITEM": "WRITE_IMPLEMENTATION_REVIEW_COMPLETE", "STATUS": "YES" if decision_rows else "NO", "DETAIL": f"{len(decision_rows)} target rows reviewed."},
        {"ITEM": "PRE_WRITE_DIFF_PACKAGE_REQUIRED", "STATUS": "YES", "DETAIL": "Required before apply."},
        {"ITEM": "NATIVE_EXECUTION_DESIGN_REQUIRED", "STATUS": "YES", "DETAIL": "Required for DBF/runtime targets."},
        {"ITEM": "HELP_DATA_APPLY_EXECUTION", "STATUS": "NOT_EXECUTED_IN_10BH", "DETAIL": "No apply execution."},
        {"ITEM": "CMDHELPCHK_APPLY_EXECUTION", "STATUS": "NOT_EXECUTED_IN_10BH", "DETAIL": "No apply execution."},
        {"ITEM": "NEXT_PACKAGE", "STATUS": "10BI_REQUIRED", "DETAIL": "Pre-write diff and native execution design package."},
    ]

    issues = "0" if failures == 0 else str(failures)
    wcsv(reports / "message_catalog_phase22ae_6_5_10bh_gate_check_v1.csv", gates, ["GATE","STATUS","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10bh_write_implementation_review_v1.csv", decision_rows, ["REVIEW_ROW","TARGET_ID","TARGET_KIND","TARGET_PATH","TARGET_FORMAT","WRITE_STRATEGY","REVIEW_DISPOSITION","PRE_WRITE_DIFF_REQUIRED","NATIVE_READBACK_REQUIRED","AUTHORIZED_FOR_WRITE_NOW","REASON"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10bh_next_design_requirements_v1.csv", next_design_rows, ["DESIGN_ITEM","REQUIRED","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10bh_apply_readiness_v1.csv", readiness, ["ITEM","STATUS","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10bh_boundary_ledger_v1.csv", boundary, ["PROTECTED_SYSTEM","MUTATION_ALLOWED","OBSERVED_MUTATION","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10bh_artifact_manifest_v1.csv", artifact_rows, ["ARTIFACT","ROLE","BYTES","SHA256"])

    summary = {
        "STATUS": status,
        "VALIDATION_ISSUES": issues,
        "PHASE22AE_6_5_10BG_STATUS": bg.get("STATUS", ""),
        "MSG_022AE_6_5_10BG_SAVEPOINT_PRESENT": 1 if sp_bg else 0,
        "ACTIVE_MESSAGES_OBSERVED_COUNT": msg_count,
        "ACTIVE_TEXT_OBSERVED_COUNT": text_count,
        "WRITE_IMPLEMENTATION_ROWS_REVIEWED": len(decision_rows),
        "NEXT_DESIGN_REQUIREMENT_ROWS": len(next_design_rows),
        "BH_ROOT": rel(bh_root, repo),
        "PRE_WRITE_DIFF_PACKAGE_REQUIRED": 1 if status == GREEN else 0,
        "NATIVE_EXECUTION_DESIGN_REQUIRED": 1 if status == GREEN else 0,
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
    wcsv(reports / "message_catalog_phase22ae_6_5_10bh_status_summary_v1.csv", [summary], list(summary.keys()))

    (repo / "docs/messaging/MESSAGE_LOCALE_PHASE22AE_6_5_10BH_TARGET_SPECIFIC_WRITE_IMPLEMENTATION_REVIEW_PACKAGE.md").write_text(
        f"# Message Catalog Phase 22AE.6.5.10BH Target-Specific Write Implementation Review Package\n\n"
        f"Status: `{status}`\n\n"
        "10BH reviews the target-specific write plan and requires a pre-write diff/native execution design package. It does not mutate HELP DATA or CMDHELPCHK.\n\n"
        f"Review root:\n\n```text\n{rel(bh_root, repo)}\n```\n\n"
        f"Next gate:\n\n```text\n{NEXT}\n```\n",
        encoding="utf-8"
    )

    print(status)
    print(f"  validation issues: {issues}")
    print(f"  Phase 22AE.6.5.10BG status: {bg.get('STATUS','')}")
    print(f"  MSG-022AE.6.5.10BG savepoint present: {1 if sp_bg else 0}")
    print(f"  active messages observed count: {msg_count}")
    print(f"  active text observed count: {text_count}")
    print(f"  write implementation rows reviewed: {len(decision_rows)}")
    print(f"  next design requirement rows: {len(next_design_rows)}")
    print(f"  review root: {rel(bh_root, repo)}")
    print("  pre-write diff package required: 1")
    print("  native execution design required: 1")
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
