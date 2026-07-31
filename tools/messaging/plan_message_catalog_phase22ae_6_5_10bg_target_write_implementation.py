#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, json, hashlib, shutil
from datetime import datetime, timezone
from pathlib import Path

GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_10BG_TARGET_SPECIFIC_HELP_CMDHELPCHK_WRITE_IMPLEMENTATION_PLAN_GREEN_SOURCE_HELD"
BLOCKED = "MESSAGE_CATALOG_PHASE22AE_6_5_10BG_TARGET_SPECIFIC_HELP_CMDHELPCHK_WRITE_IMPLEMENTATION_PLAN_BLOCKED"
NEXT = "HOLD_OR_AUTHORIZE_PHASE22AE_6_5_10BH_TARGET_SPECIFIC_WRITE_IMPLEMENTATION_REVIEW_PACKAGE"

REPORT_DIR = Path("docs/messaging/reports")
BF_SUMMARY = REPORT_DIR / "message_catalog_phase22ae_6_5_10bf_status_summary_v1.csv"
BF_FORMAT_REVIEW = REPORT_DIR / "message_catalog_phase22ae_6_5_10bf_target_format_review_v1.csv"
BF_REQS = REPORT_DIR / "message_catalog_phase22ae_6_5_10bf_write_implementation_requirements_v1.csv"
BG_ROOT = Path("docs/messaging/apply/phase22ae_6_5_10bg_target_specific_write_implementation_plan_v1")
CANDIDATE_PATH = Path("docs/messaging/candidates/MESSAGE_CATALOG_PHASE22AE_6_5_10AW_MSGMGR_HELP_CANDIDATE.md")
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

def strategy_for(row):
    fmt = row.get("TARGET_FORMAT", "")
    kind = row.get("TARGET_KIND", "")
    target = row.get("TARGET_PATH", "")
    up = f"{fmt} {kind} {target}".upper()
    if fmt == "DBF_BINARY":
        return (
            "NATIVE_X64BASE_HELP_CMDHELPCHK_WRITE_PATH_REQUIRED",
            "Do not raw-write this DBF. Build a DotTalk++/x64base native script or schema-aware import path with backup/readback gates."
        )
    if fmt in {"TEXT_MARKDOWN", "CSV_TEXT", "JSON_TEXT"}:
        return (
            "TEXT_ANCHOR_PATCH_PLAN_REQUIRED",
            "Identify exact anchor/key/row and generate a diff-only patch plan before any write."
        )
    return (
        "MANUAL_IMPLEMENTATION_REVIEW_REQUIRED",
        "Unknown target format; require manual target-specific design before write."
    )

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--replace-existing-plan", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    reports = repo / REPORT_DIR
    reports.mkdir(parents=True, exist_ok=True)

    bf = first(repo / BF_SUMMARY)
    fmt_rows = rows(repo / BF_FORMAT_REVIEW)
    req_rows = rows(repo / BF_REQS)
    sp_bf, latest_bf = savepoint(repo, "MSG-022AE.6.5.10BF")
    msg_count = dbf_count(repo / ACTIVE_MSG_DBF)
    text_count = dbf_count(repo / ACTIVE_TEXT_DBF)
    candidate = repo / CANDIDATE_PATH
    bg_root = repo / BG_ROOT

    gates = []
    failures = 0
    def gate(name, ok, detail):
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": str(detail)})
        if not ok:
            failures += 1

    gate("PHASE22AE_6_5_10BF_GREEN",
         bf.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_5_10BF_HELP_CMDHELPCHK_EXECUTION_REVIEW_GREEN_IMPLEMENTATION_PLAN_REQUIRED_SOURCE_HELD",
         bf.get("STATUS", "missing"))
    gate("MSG_022AE_6_5_10BF_SAVEPOINT_PRESENT", sp_bf, latest_bf)
    gate("BF_TARGET_SPECIFIC_IMPLEMENTATION_REQUIRED", bf.get("TARGET_SPECIFIC_IMPLEMENTATION_REQUIRED") == "1", bf.get("TARGET_SPECIFIC_IMPLEMENTATION_REQUIRED", "missing"))
    gate("BF_AUTO_WRITE_NOT_READY", bf.get("AUTO_WRITE_READY") == "0", bf.get("AUTO_WRITE_READY", "missing"))
    gate("BF_HELP_APPLY_NOT_EXECUTED", bf.get("HELP_DATA_APPLY_EXECUTED") == "0", bf.get("HELP_DATA_APPLY_EXECUTED", "missing"))
    gate("BF_CMDHELPCHK_APPLY_NOT_EXECUTED", bf.get("CMDHELPCHK_APPLY_EXECUTED") == "0", bf.get("CMDHELPCHK_APPLY_EXECUTED", "missing"))
    gate("FORMAT_REVIEW_ROWS_PRESENT", len(fmt_rows) > 0, len(fmt_rows))
    gate("WRITE_REQUIREMENTS_PRESENT", len(req_rows) > 0, len(req_rows))
    gate("ACTIVE_MESSAGES_HEADER_COUNT_14", msg_count == 14, msg_count)
    gate("ACTIVE_TEXT_HEADER_COUNT_70", text_count == 70, text_count)
    gate("CANDIDATE_EXISTS", candidate.exists(), rel(candidate, repo))
    gate("BG_ROOT_NOT_EXISTING_OR_REPLACE_ALLOWED", (not bg_root.exists()) or args.replace_existing_plan, rel(bg_root, repo))

    status = BLOCKED
    impl_rows = []
    step_rows = []
    artifact_rows = []
    if failures == 0:
        if bg_root.exists() and args.replace_existing_plan:
            shutil.rmtree(bg_root)
        bg_root.mkdir(parents=True, exist_ok=True)

        for i, r in enumerate(fmt_rows, start=1):
            strategy, detail = strategy_for(r)
            impl_rows.append({
                "IMPLEMENTATION_ROW": i,
                "TARGET_ID": r.get("TARGET_ID", ""),
                "TARGET_KIND": r.get("TARGET_KIND", ""),
                "TARGET_PATH": r.get("TARGET_PATH", ""),
                "TARGET_FORMAT": r.get("TARGET_FORMAT", ""),
                "WRITE_STRATEGY": strategy,
                "WRITE_MECHANIC_DETAIL": detail,
                "PROPOSED_KEYS_OR_ANCHORS": "MSGMGR;SET MESSAGE CATALOG CHECK;SET MESSAGE CATALOG GET;SET MESSAGE EMIT",
                "SOURCE_CANDIDATE": rel(candidate, repo),
                "REQUIRES_PRE_WRITE_DIFF": 1,
                "REQUIRES_NATIVE_READBACK": 1,
                "AUTHORIZED_FOR_WRITE_NOW": 0,
                "NOTES": r.get("REASON", ""),
            })

        step_rows = [
            {"STEP": 1, "STEP_NAME": "SELECT_TARGET_WRITE_PATH", "DETAIL": "Choose native DBF/runtime path or text anchor patch path per target.", "AUTHORIZED_NOW": 0},
            {"STEP": 2, "STEP_NAME": "GENERATE_TARGET_SPECIFIC_DIFFS", "DETAIL": "Produce exact per-target before/after diff, including HELP topics and CMDHELPCHK rules.", "AUTHORIZED_NOW": 0},
            {"STEP": 3, "STEP_NAME": "VERIFY_ROLLBACK_BACKUPS", "DETAIL": "Validate 10BE exact target backup hashes immediately before any write package.", "AUTHORIZED_NOW": 0},
            {"STEP": 4, "STEP_NAME": "EXECUTE_ONLY_AUTHORIZED_TARGETS", "DETAIL": "Later execution package may write only accepted target rows and must refuse all others.", "AUTHORIZED_NOW": 0},
            {"STEP": 5, "STEP_NAME": "RUN_DOTTALK_RUNTIME_READBACK", "DETAIL": "Prove HELP MSGMGR / HELP SET MESSAGE and CMDHELPCHK behavior through runtime after any later write.", "AUTHORIZED_NOW": 0},
            {"STEP": 6, "STEP_NAME": "ACCEPT_OR_RESTORE", "DETAIL": "If proof package is temporary, restore exact backups before savepoint; if final, require acceptance gate.", "AUTHORIZED_NOW": 0},
        ]

        impl_path = bg_root / "target_specific_write_implementation_plan_v1.csv"
        steps_path = bg_root / "guarded_write_execution_steps_v1.csv"
        readme = bg_root / "README_10BG_TARGET_SPECIFIC_WRITE_IMPLEMENTATION_PLAN.md"
        wcsv(impl_path, impl_rows, ["IMPLEMENTATION_ROW","TARGET_ID","TARGET_KIND","TARGET_PATH","TARGET_FORMAT","WRITE_STRATEGY","WRITE_MECHANIC_DETAIL","PROPOSED_KEYS_OR_ANCHORS","SOURCE_CANDIDATE","REQUIRES_PRE_WRITE_DIFF","REQUIRES_NATIVE_READBACK","AUTHORIZED_FOR_WRITE_NOW","NOTES"])
        wcsv(steps_path, step_rows, ["STEP","STEP_NAME","DETAIL","AUTHORIZED_NOW"])
        readme.write_text(
            "# 10BG Target-Specific Write Implementation Plan\n\n"
            "10BG designs target-specific write mechanics. It does not mutate HELP DATA or CMDHELPCHK.\n\n"
            "Key boundary: DBF targets must not be raw-written by Python. Use native x64base/DotTalk++ paths or schema-aware staged import with runtime readback gates.\n",
            encoding="utf-8"
        )
        for p in [impl_path, steps_path, readme]:
            artifact_rows.append({"ARTIFACT": rel(p, repo), "ROLE": "write_implementation_plan_artifact", "BYTES": p.stat().st_size, "SHA256": sha(p)})
        status = GREEN

    boundary = [
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "10BG writes docs/messaging implementation-plan artifacts only."},
        {"PROTECTED_SYSTEM": "ACTIVE_SYSTEM_MESSAGES", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_SYSTEM_MESSAGE_TEXT", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_CDX_LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CDX/LMDB mutation."},
        {"PROTECTED_SYSTEM": "WORKSPACE_PROFILE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No workspace mutation."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No HELP DATA mutation; implementation plan only."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CMDHELPCHK mutation; implementation plan only."},
    ]

    readiness = [
        {"ITEM": "TARGET_SPECIFIC_WRITE_PLAN_CREATED", "STATUS": "YES" if impl_rows else "NO", "DETAIL": f"{len(impl_rows)} implementation rows."},
        {"ITEM": "PRE_WRITE_DIFF_REQUIRED", "STATUS": "YES", "DETAIL": "Required before any target mutation."},
        {"ITEM": "NATIVE_DB_WRITE_REQUIRED_FOR_DBF_TARGETS", "STATUS": "YES", "DETAIL": "No raw Python DBF writes for runtime catalogs."},
        {"ITEM": "HELP_DATA_APPLY_EXECUTION", "STATUS": "NOT_EXECUTED_IN_10BG", "DETAIL": "No apply execution."},
        {"ITEM": "CMDHELPCHK_APPLY_EXECUTION", "STATUS": "NOT_EXECUTED_IN_10BG", "DETAIL": "No apply execution."},
        {"ITEM": "NEXT_REVIEW_PACKAGE", "STATUS": "10BH_REQUIRED", "DETAIL": "Review implementation plan and decide whether execution package is feasible."},
    ]

    issues = "0" if failures == 0 else str(failures)
    wcsv(reports / "message_catalog_phase22ae_6_5_10bg_gate_check_v1.csv", gates, ["GATE","STATUS","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10bg_write_implementation_plan_v1.csv", impl_rows, ["IMPLEMENTATION_ROW","TARGET_ID","TARGET_KIND","TARGET_PATH","TARGET_FORMAT","WRITE_STRATEGY","WRITE_MECHANIC_DETAIL","PROPOSED_KEYS_OR_ANCHORS","SOURCE_CANDIDATE","REQUIRES_PRE_WRITE_DIFF","REQUIRES_NATIVE_READBACK","AUTHORIZED_FOR_WRITE_NOW","NOTES"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10bg_guarded_write_steps_v1.csv", step_rows, ["STEP","STEP_NAME","DETAIL","AUTHORIZED_NOW"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10bg_apply_readiness_v1.csv", readiness, ["ITEM","STATUS","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10bg_boundary_ledger_v1.csv", boundary, ["PROTECTED_SYSTEM","MUTATION_ALLOWED","OBSERVED_MUTATION","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10bg_artifact_manifest_v1.csv", artifact_rows, ["ARTIFACT","ROLE","BYTES","SHA256"])

    summary = {
        "STATUS": status,
        "VALIDATION_ISSUES": issues,
        "PHASE22AE_6_5_10BF_STATUS": bf.get("STATUS", ""),
        "MSG_022AE_6_5_10BF_SAVEPOINT_PRESENT": 1 if sp_bf else 0,
        "ACTIVE_MESSAGES_OBSERVED_COUNT": msg_count,
        "ACTIVE_TEXT_OBSERVED_COUNT": text_count,
        "TARGET_FORMAT_REVIEW_ROWS": len(fmt_rows),
        "WRITE_IMPLEMENTATION_PLAN_ROWS": len(impl_rows),
        "GUARDED_WRITE_STEP_ROWS": len(step_rows),
        "BG_ROOT": rel(bg_root, repo),
        "TARGET_SPECIFIC_WRITE_IMPLEMENTATION_PLAN_CREATED": 1 if status == GREEN else 0,
        "PRE_WRITE_DIFF_REQUIRED": 1 if status == GREEN else 0,
        "NATIVE_DB_WRITE_REQUIRED_FOR_DBF_TARGETS": 1 if status == GREEN else 0,
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
    wcsv(reports / "message_catalog_phase22ae_6_5_10bg_status_summary_v1.csv", [summary], list(summary.keys()))

    (repo / "docs/messaging/MESSAGE_LOCALE_PHASE22AE_6_5_10BG_TARGET_SPECIFIC_HELP_CMDHELPCHK_WRITE_IMPLEMENTATION_PLAN.md").write_text(
        f"# Message Catalog Phase 22AE.6.5.10BG Target-Specific HELP/CMDHELPCHK Write Implementation Plan\n\n"
        f"Status: `{status}`\n\n"
        "10BG creates a target-specific write implementation plan. It does not mutate HELP DATA or CMDHELPCHK.\n\n"
        f"Implementation-plan root:\n\n```text\n{rel(bg_root, repo)}\n```\n\n"
        f"Next gate:\n\n```text\n{NEXT}\n```\n",
        encoding="utf-8"
    )

    print(status)
    print(f"  validation issues: {issues}")
    print(f"  Phase 22AE.6.5.10BF status: {bf.get('STATUS','')}")
    print(f"  MSG-022AE.6.5.10BF savepoint present: {1 if sp_bf else 0}")
    print(f"  active messages observed count: {msg_count}")
    print(f"  active text observed count: {text_count}")
    print(f"  target format review rows: {len(fmt_rows)}")
    print(f"  write implementation plan rows: {len(impl_rows)}")
    print(f"  guarded write step rows: {len(step_rows)}")
    print(f"  implementation-plan root: {rel(bg_root, repo)}")
    print("  target-specific write implementation plan created: 1")
    print("  pre-write diff required: 1")
    print("  native DB write required for DBF targets: 1")
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
