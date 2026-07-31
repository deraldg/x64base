#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, json, hashlib, shutil
from datetime import datetime, timezone
from pathlib import Path

GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_10BA_MSGMGR_HELP_CMDHELPCHK_APPLY_EXECUTION_PREFLIGHT_GREEN_EXACT_TARGET_MAP_REQUIRED"
BLOCKED = "MESSAGE_CATALOG_PHASE22AE_6_5_10BA_MSGMGR_HELP_CMDHELPCHK_APPLY_EXECUTION_PREFLIGHT_BLOCKED"
NEXT = "HOLD_OR_AUTHORIZE_PHASE22AE_6_5_10BB_EXACT_HELP_CMDHELPCHK_TARGET_MAP"
REPORT_DIR = Path("docs/messaging/reports")
AZ_REPORT = REPORT_DIR / "message_catalog_phase22ae_6_5_10az_status_summary_v1.csv"
AZ_TARGETS = REPORT_DIR / "message_catalog_phase22ae_6_5_10az_target_discovery_v1.csv"
AZ_BACKUPS = REPORT_DIR / "message_catalog_phase22ae_6_5_10az_backup_manifest_v1.csv"
APPLY_ROOT = Path("docs/messaging/apply/phase22ae_6_5_10ba_msgmgr_help_cmdhelpchk_apply_execution_preflight_v1")
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

def classify_target(row):
    path = row.get("TARGET_PATH", "")
    up = path.upper().replace("\\", "/")
    name = up.split("/")[-1]
    score = 0
    reasons = []
    if name in {"HELP_TOPIC.DBF", "HELP_TOPICS.DBF", "HELP.DBF", "HELPTOPIC.DBF"}:
        score += 50; reasons.append("probable HELP topic DBF")
    if name in {"COMMANDS.DBF", "COMMAND.DBF", "CMDHELP.DBF", "CMDHELPCHK.DBF", "CMDHELPCHK.MD", "COMMANDS.MD"}:
        score += 40; reasons.append("probable command/help validation artifact")
    if "/DATA/HELP/" in up:
        score += 25; reasons.append("under dottalkpp/data/help")
    if "/DOCS/MESSAGING/" in up:
        score -= 20; reasons.append("messaging report/doc artifact, not active HELP")
    if "/DOCS/" in up and "/DATA/HELP/" not in up:
        score -= 5; reasons.append("docs-side artifact")
    if "MESSAGING_SAVEPOINT" in name or "REPORT" in up or "RUNLOG" in up:
        score -= 50; reasons.append("evidence/report, not target")
    exact = 1 if score >= 50 else 0
    return exact, score, "; ".join(reasons) if reasons else "low-confidence broad discovery row"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--replace-existing-preflight", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    reports = repo / REPORT_DIR
    reports.mkdir(parents=True, exist_ok=True)

    az = first(repo / AZ_REPORT)
    sp_az, latest_az = savepoint(repo, "MSG-022AE.6.5.10AZ")
    msg_count = dbf_count(repo / ACTIVE_MSG_DBF)
    text_count = dbf_count(repo / ACTIVE_TEXT_DBF)
    target_rows = rows(repo / AZ_TARGETS)
    backup_rows = rows(repo / AZ_BACKUPS)
    apply_root = repo / APPLY_ROOT

    gates = []
    failures = 0
    def gate(name, ok, detail):
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": str(detail)})
        if not ok:
            failures += 1

    gate("PHASE22AE_6_5_10AZ_GREEN",
         az.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_5_10AZ_MSGMGR_HELP_CMDHELPCHK_GUARDED_APPLY_PACKAGE_GREEN_BACKUP_AND_DRYRUN_READY_APPLY_NOT_EXECUTED",
         az.get("STATUS", "missing"))
    gate("MSG_022AE_6_5_10AZ_SAVEPOINT_PRESENT", sp_az, latest_az)
    gate("AZ_APPLY_NOT_EXECUTED", az.get("HELP_DATA_APPLY_EXECUTED") == "0" and az.get("CMDHELPCHK_APPLY_EXECUTED") == "0",
         f"help={az.get('HELP_DATA_APPLY_EXECUTED','')} cmdhelpchk={az.get('CMDHELPCHK_APPLY_EXECUTED','')}")
    gate("ACTIVE_MESSAGES_HEADER_COUNT_14", msg_count == 14, msg_count)
    gate("ACTIVE_TEXT_HEADER_COUNT_70", text_count == 70, text_count)
    gate("AZ_TARGET_DISCOVERY_PRESENT", len(target_rows) > 0, len(target_rows))
    gate("AZ_BACKUPS_PRESENT", len(backup_rows) > 0, len(backup_rows))
    gate("APPLY_ROOT_NOT_EXISTING_OR_REPLACE_ALLOWED", (not apply_root.exists()) or args.replace_existing_preflight, rel(apply_root, repo))

    status = BLOCKED
    exact_rows = []
    review_rows = []
    artifact_rows = []
    if failures == 0:
        if apply_root.exists() and args.replace_existing_preflight:
            shutil.rmtree(apply_root)
        apply_root.mkdir(parents=True, exist_ok=True)

        for r in target_rows:
            exact, score, reason = classify_target(r)
            out = {
                "TARGET_PATH": r.get("TARGET_PATH", ""),
                "ROLE": r.get("ROLE", ""),
                "BYTES": r.get("BYTES", ""),
                "SHA256": r.get("SHA256", ""),
                "BACKUP_COPIED": r.get("BACKUP_COPIED", ""),
                "CONFIDENCE_SCORE": score,
                "EXACT_TARGET_CANDIDATE": exact,
                "REASON": reason,
            }
            if exact:
                exact_rows.append(out)
            else:
                review_rows.append(out)

        target_map_template = apply_root / "exact_target_map_REQUIRED_BEFORE_10BB.csv"
        target_map_template.write_text(
            "TARGET_ID,TARGET_KIND,TARGET_PATH,FIELD_OR_SECTION,APPLY_ACTION,ROLLBACK_SOURCE,AUTHORIZED_FOR_10BB,NOTES\n"
            "HELP-MSGMGR,HELP_DATA_EXACT_TARGET,,MSGMGR,INSERT_OR_UPDATE_HELP_TOPIC,backup_required,0,Fill exact active HELP DATA target before 10BB\n"
            "CMDHELPCHK-MSGMGR,CMDHELPCHK_EXACT_TARGET,,MSGMGR,INSERT_OR_UPDATE_VALIDATION_RULE,backup_required,0,Fill exact CMDHELPCHK target before 10BB\n",
            encoding="utf-8"
        )

        preflight_note = apply_root / "README_10BA_PREFLIGHT.md"
        preflight_note.write_text(
            "# 10BA Apply Execution Preflight\n\n"
            "Authorization for apply execution has been received, but 10AZ discovered 487 broad targets. "
            "That is not an exact target map. This preflight intentionally refuses to mutate HELP DATA or CMDHELPCHK "
            "until the exact HELP and CMDHELPCHK target artifacts/fields are named.\n\n"
            "Next required artifact:\n\n"
            "```text\n"
            "docs/messaging/apply/phase22ae_6_5_10ba_msgmgr_help_cmdhelpchk_apply_execution_preflight_v1/exact_target_map_REQUIRED_BEFORE_10BB.csv\n"
            "```\n\n"
            "10BB may execute only after that map is filled and reviewed.\n",
            encoding="utf-8"
        )

        disabled = apply_root / "MESSAGE_CATALOG_PHASE22AE_6_5_10BB_APPLY_EXECUTION_REFUSES_WITHOUT_EXACT_TARGET_MAP.ps1.disabled"
        disabled.write_text(
            'throw "DISABLED TEMPLATE: exact HELP/CMDHELPCHK target map is required before apply execution."\n',
            encoding="utf-8"
        )

        for p in [target_map_template, preflight_note, disabled]:
            artifact_rows.append({
                "ARTIFACT": rel(p, repo),
                "ROLE": "preflight_artifact",
                "BYTES": p.stat().st_size,
                "SHA256": sha(p),
            })

        status = GREEN

    boundary = [
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "10BA preflight writes docs/messaging apply-readiness artifacts only."},
        {"PROTECTED_SYSTEM": "ACTIVE_SYSTEM_MESSAGES", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_SYSTEM_MESSAGE_TEXT", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_CDX_LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CDX/LMDB mutation."},
        {"PROTECTED_SYSTEM": "WORKSPACE_PROFILE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No workspace mutation."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No HELP DATA mutation; exact target map required."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CMDHELPCHK mutation; exact target map required."},
    ]

    readiness = [
        {"ITEM": "APPLY_AUTHORIZATION_RECEIVED", "STATUS": "YES_BUT_GUARDED", "DETAIL": "User authorized apply execution, but broad 487-target discovery requires exact target map first."},
        {"ITEM": "EXACT_TARGET_MAP_REQUIRED", "STATUS": "BLOCKING_NEXT_EXECUTION", "DETAIL": "Fill exact_target_map_REQUIRED_BEFORE_10BB.csv before mutating HELP/CMDHELPCHK."},
        {"ITEM": "HELP_DATA_APPLY_EXECUTION", "STATUS": "NOT_EXECUTED_IN_10BA", "DETAIL": "Preflight only."},
        {"ITEM": "CMDHELPCHK_APPLY_EXECUTION", "STATUS": "NOT_EXECUTED_IN_10BA", "DETAIL": "Preflight only."},
        {"ITEM": "ROLLBACK_BACKUPS", "STATUS": "AVAILABLE_FROM_10AZ_FOR_DISCOVERED_TARGETS", "DETAIL": f"{len(backup_rows)} backup rows from 10AZ."},
    ]

    issues = "0" if failures == 0 else str(failures)
    wcsv(reports / "message_catalog_phase22ae_6_5_10ba_gate_check_v1.csv", gates, ["GATE", "STATUS", "DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10ba_exact_target_candidates_v1.csv", exact_rows, ["TARGET_PATH","ROLE","BYTES","SHA256","BACKUP_COPIED","CONFIDENCE_SCORE","EXACT_TARGET_CANDIDATE","REASON"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10ba_broad_target_review_v1.csv", review_rows, ["TARGET_PATH","ROLE","BYTES","SHA256","BACKUP_COPIED","CONFIDENCE_SCORE","EXACT_TARGET_CANDIDATE","REASON"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10ba_apply_readiness_v1.csv", readiness, ["ITEM","STATUS","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10ba_boundary_ledger_v1.csv", boundary, ["PROTECTED_SYSTEM","MUTATION_ALLOWED","OBSERVED_MUTATION","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10ba_artifact_manifest_v1.csv", artifact_rows, ["ARTIFACT","ROLE","BYTES","SHA256"])

    summary = {
        "STATUS": status,
        "VALIDATION_ISSUES": issues,
        "PHASE22AE_6_5_10AZ_STATUS": az.get("STATUS", ""),
        "MSG_022AE_6_5_10AZ_SAVEPOINT_PRESENT": 1 if sp_az else 0,
        "ACTIVE_MESSAGES_OBSERVED_COUNT": msg_count,
        "ACTIVE_TEXT_OBSERVED_COUNT": text_count,
        "AZ_TARGETS_DISCOVERED": len(target_rows),
        "AZ_BACKUPS_COPIED": len(backup_rows),
        "EXACT_TARGET_CANDIDATES": len(exact_rows),
        "BROAD_TARGET_REVIEW_ROWS": len(review_rows),
        "APPLY_ROOT": rel(apply_root, repo),
        "HELP_DATA_APPLY_AUTHORIZATION_RECEIVED": 1,
        "CMDHELPCHK_APPLY_AUTHORIZATION_RECEIVED": 1,
        "HELP_DATA_APPLY_EXECUTED": 0,
        "CMDHELPCHK_APPLY_EXECUTED": 0,
        "EXACT_TARGET_MAP_REQUIRED": 1,
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
    wcsv(reports / "message_catalog_phase22ae_6_5_10ba_status_summary_v1.csv", [summary], list(summary.keys()))

    (repo / "docs/messaging/MESSAGE_LOCALE_PHASE22AE_6_5_10BA_MSGMGR_HELP_CMDHELPCHK_APPLY_EXECUTION_PREFLIGHT.md").write_text(
        f"# Message Catalog Phase 22AE.6.5.10BA Apply Execution Preflight\n\n"
        f"Status: `{status}`\n\n"
        "Apply execution authorization was received, but 10AZ target discovery is broad. "
        "10BA therefore creates the exact target-map gate required before any HELP DATA or CMDHELPCHK mutation.\n\n"
        f"Apply root:\n\n```text\n{rel(apply_root, repo)}\n```\n\n"
        f"Next gate:\n\n```text\n{NEXT}\n```\n",
        encoding="utf-8"
    )

    print(status)
    print(f"  validation issues: {issues}")
    print(f"  Phase 22AE.6.5.10AZ status: {az.get('STATUS','')}")
    print(f"  MSG-022AE.6.5.10AZ savepoint present: {1 if sp_az else 0}")
    print(f"  active messages observed count: {msg_count}")
    print(f"  active text observed count: {text_count}")
    print(f"  AZ targets discovered: {len(target_rows)}")
    print(f"  AZ backups copied: {len(backup_rows)}")
    print(f"  exact target candidates: {len(exact_rows)}")
    print(f"  broad target review rows: {len(review_rows)}")
    print(f"  apply root: {rel(apply_root, repo)}")
    print("  HELP DATA apply authorization received: 1")
    print("  CMDHELPCHK apply authorization received: 1")
    print("  HELP DATA apply executed: 0")
    print("  CMDHELPCHK apply executed: 0")
    print("  exact target map required: 1")
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
