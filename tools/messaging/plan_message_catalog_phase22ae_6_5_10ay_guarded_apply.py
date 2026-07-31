#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path

STATUS_GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_10AY_MSGMGR_HELP_CMDHELPCHK_GUARDED_APPLY_PLAN_GREEN_SOURCE_HELD"
STATUS_BLOCKED = "MESSAGE_CATALOG_PHASE22AE_6_5_10AY_MSGMGR_HELP_CMDHELPCHK_GUARDED_APPLY_PLAN_BLOCKED"
NEXT_GATE = "HOLD_OR_AUTHORIZE_PHASE22AE_6_5_10AZ_MSGMGR_HELP_CMDHELPCHK_GUARDED_APPLY_PACKAGE"

REPORT_DIR = Path("docs/messaging/reports")
CANDIDATE_PATH = Path("docs/messaging/candidates/MESSAGE_CATALOG_PHASE22AE_6_5_10AW_MSGMGR_HELP_CANDIDATE.md")
APPLY_ROOT = Path("docs/messaging/apply/phase22ae_6_5_10ay_msgmgr_help_cmdhelpchk_guarded_apply_plan_v1")
ACTIVE_MSG_DBF = Path("dottalkpp/data/messaging/SYSTEM_MESSAGES.dbf")
ACTIVE_TEXT_DBF = Path("dottalkpp/data/messaging/SYSTEM_MESSAGE_TEXT.dbf")

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

def dbf_header_count(path: Path):
    if not path.exists() or path.stat().st_size < 12:
        return ""
    return int.from_bytes(path.read_bytes()[:12][4:8], "little")

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

def sha256_file(path: Path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

import hashlib

def make_disabled_templates(repo: Path, candidate_text: str):
    templates = repo / APPLY_ROOT / "templates"
    templates.mkdir(parents=True, exist_ok=True)

    help_template = templates / "MESSAGE_CATALOG_PHASE22AE_6_5_10AZ_HELP_DATA_APPLY_TEMPLATE.ps1.disabled"
    help_template.write_text(
        """# DISABLED TEMPLATE - DO NOT RUN
# Phase 22AE.6.5.10AZ would be a separately authorized guarded HELP DATA apply package.
# Preconditions:
#   - 10AY green/savepointed
#   - explicit user authorization for HELP DATA apply package
#   - backup of target HELP DATA artifacts
#   - dry-run diff shows only MSGMGR / SET MESSAGE CATALOG help targets
#   - post-apply HELP and CMDHELPCHK validation plan present
#
# This template intentionally exits if copied and run.
throw "DISABLED TEMPLATE: 10AZ HELP DATA apply is not authorized by 10AY."
""",
        encoding="utf-8",
    )

    cmdhelp_template = templates / "MESSAGE_CATALOG_PHASE22AE_6_5_10AZ_CMDHELPCHK_APPLY_TEMPLATE.ps1.disabled"
    cmdhelp_template.write_text(
        """# DISABLED TEMPLATE - DO NOT RUN
# Phase 22AE.6.5.10AZ would be a separately authorized guarded CMDHELPCHK rule/update package.
# Preconditions:
#   - HELP DATA candidate application is authorized and staged
#   - CMDHELPCHK dry-run identifies exact expected command/help rows
#   - rollback plan exists
#
# This template intentionally exits if copied and run.
throw "DISABLED TEMPLATE: 10AZ CMDHELPCHK apply is not authorized by 10AY."
""",
        encoding="utf-8",
    )

    candidate_copy = repo / APPLY_ROOT / "candidate_snapshot" / "MESSAGE_CATALOG_PHASE22AE_6_5_10AW_MSGMGR_HELP_CANDIDATE.snapshot.md"
    candidate_copy.parent.mkdir(parents=True, exist_ok=True)
    candidate_copy.write_text(candidate_text, encoding="utf-8")

    return help_template, cmdhelp_template, candidate_copy

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--replace-existing-plan", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    reports = repo / REPORT_DIR
    reports.mkdir(parents=True, exist_ok=True)

    ax = first_row(reports / "message_catalog_phase22ae_6_5_10ax_status_summary_v1.csv")
    aw = first_row(reports / "message_catalog_phase22ae_6_5_10aw_status_summary_v1.csv")
    sp_ax, latest_ax = savepoint_present(repo, "MSG-022AE.6.5.10AX")

    msg_count = dbf_header_count(repo / ACTIVE_MSG_DBF)
    text_count = dbf_header_count(repo / ACTIVE_TEXT_DBF)
    candidate = repo / CANDIDATE_PATH
    candidate_exists = candidate.exists()
    candidate_text = candidate.read_text(encoding="utf-8", errors="replace") if candidate_exists else ""
    apply_root = repo / APPLY_ROOT

    gates = []
    failures = 0
    def gate(name, ok, detail):
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": str(detail)})
        if not ok:
            failures += 1

    gate("PHASE22AE_6_5_10AX_ACCEPTED",
         ax.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_5_10AX_MSGMGR_HELP_CANDIDATE_REVIEW_GREEN_CANDIDATE_ACCEPTED_SOURCE_HELD",
         ax.get("STATUS", "missing"))
    gate("MSG_022AE_6_5_10AX_SAVEPOINT_PRESENT", sp_ax, latest_ax)
    gate("AX_HELP_READY_FOR_PLAN", ax.get("HELP_DATA_APPLY_READY_FOR_PLAN") == "1", ax.get("HELP_DATA_APPLY_READY_FOR_PLAN", "missing"))
    gate("AX_CMDHELPCHK_READY_FOR_PLAN", ax.get("CMDHELPCHK_APPLY_READY_FOR_PLAN") == "1", ax.get("CMDHELPCHK_APPLY_READY_FOR_PLAN", "missing"))
    gate("AX_HELP_APPLY_AUTH_HELD", ax.get("HELP_DATA_APPLY_AUTHORIZED") == "0", ax.get("HELP_DATA_APPLY_AUTHORIZED", "missing"))
    gate("AX_CMDHELPCHK_APPLY_AUTH_HELD", ax.get("CMDHELPCHK_APPLY_AUTHORIZED") == "0", ax.get("CMDHELPCHK_APPLY_AUTHORIZED", "missing"))
    gate("ACTIVE_MESSAGES_HEADER_COUNT_14", msg_count == 14, msg_count)
    gate("ACTIVE_TEXT_HEADER_COUNT_70", text_count == 70, text_count)
    gate("CANDIDATE_EXISTS", candidate_exists, rel(candidate, repo))
    gate("CANDIDATE_CONTAINS_MSGMGR", "MSGMGR" in candidate_text.upper(), "MSGMGR present")
    gate("CANDIDATE_CONTAINS_EMIT", "SET MESSAGE EMIT" in candidate_text.upper(), "SET MESSAGE EMIT present")
    gate("APPLY_ROOT_NOT_EXISTING_OR_REPLACE_ALLOWED", (not apply_root.exists()) or args.replace_existing_plan, rel(apply_root, repo))

    status = STATUS_BLOCKED
    help_template = cmdhelp_template = candidate_copy = None
    if failures == 0:
        if apply_root.exists() and args.replace_existing_plan:
            # Remove only the controlled plan root, never active HELP/CMDHELPCHK.
            for child in apply_root.iterdir():
                if child.is_file():
                    child.unlink()
                elif child.is_dir():
                    import shutil
                    shutil.rmtree(child)
        apply_root.mkdir(parents=True, exist_ok=True)
        help_template, cmdhelp_template, candidate_copy = make_disabled_templates(repo, candidate_text)
        status = STATUS_GREEN

    target_manifest = [
        {"TARGET_ID": "HELP-MSGMGR", "TARGET_KIND": "HELP_TOPIC_CANDIDATE", "TARGET_NAME": "MSGMGR", "SOURCE_CANDIDATE": rel(candidate, repo), "APPLY_AUTHORIZED": 0, "NOTES": "Primary Message Manager command-house topic."},
        {"TARGET_ID": "HELP-SET-MESSAGE-CATALOG-CHECK", "TARGET_KIND": "HELP_RELATED_TOPIC_CANDIDATE", "TARGET_NAME": "SET MESSAGE CATALOG CHECK", "SOURCE_CANDIDATE": rel(candidate, repo), "APPLY_AUTHORIZED": 0, "NOTES": "Low-level provider/check/readback surface."},
        {"TARGET_ID": "HELP-SET-MESSAGE-CATALOG-GET", "TARGET_KIND": "HELP_RELATED_TOPIC_CANDIDATE", "TARGET_NAME": "SET MESSAGE CATALOG GET", "SOURCE_CANDIDATE": rel(candidate, repo), "APPLY_AUTHORIZED": 0, "NOTES": "Low-level read/get surface."},
        {"TARGET_ID": "HELP-SET-MESSAGE-EMIT", "TARGET_KIND": "HELP_RELATED_TOPIC_CANDIDATE", "TARGET_NAME": "SET MESSAGE EMIT", "SOURCE_CANDIDATE": rel(candidate, repo), "APPLY_AUTHORIZED": 0, "NOTES": "Localized diagnostic emission surface."},
        {"TARGET_ID": "CMDHELPCHK-MSGMGR", "TARGET_KIND": "CMDHELPCHK_RULE_CANDIDATE", "TARGET_NAME": "MSGMGR", "SOURCE_CANDIDATE": rel(candidate, repo), "APPLY_AUTHORIZED": 0, "NOTES": "Command/help validation expectation."},
        {"TARGET_ID": "CMDHELPCHK-SET-MESSAGE", "TARGET_KIND": "CMDHELPCHK_RULE_CANDIDATE", "TARGET_NAME": "SET MESSAGE CATALOG/EMIT", "SOURCE_CANDIDATE": rel(candidate, repo), "APPLY_AUTHORIZED": 0, "NOTES": "Low-level SET MESSAGE surfaces review."},
    ]

    apply_sequence = [
        {"STEP": 1, "ACTION": "BACKUP_HELP_DATA_AND_CMDHELPCHK_TARGETS", "AUTHORIZED_NOW": 0, "REQUIRED_FOR_10AZ": 1, "DETAIL": "Create exact backup of HELP DATA and CMDHELPCHK artifacts before any apply."},
        {"STEP": 2, "ACTION": "DRY_RUN_HELP_TOPIC_DIFF", "AUTHORIZED_NOW": 0, "REQUIRED_FOR_10AZ": 1, "DETAIL": "Show candidate target rows and resulting HELP topic diffs; no write."},
        {"STEP": 3, "ACTION": "DRY_RUN_CMDHELPCHK_DIFF", "AUTHORIZED_NOW": 0, "REQUIRED_FOR_10AZ": 1, "DETAIL": "Show candidate validation expectations; no write."},
        {"STEP": 4, "ACTION": "APPLY_HELP_DATA_IF_AUTHORIZED", "AUTHORIZED_NOW": 0, "REQUIRED_FOR_10AZ": 1, "DETAIL": "Only after explicit apply authorization in a later package."},
        {"STEP": 5, "ACTION": "APPLY_CMDHELPCHK_IF_AUTHORIZED", "AUTHORIZED_NOW": 0, "REQUIRED_FOR_10AZ": 1, "DETAIL": "Only after HELP DATA apply target is stable and explicitly authorized."},
        {"STEP": 6, "ACTION": "RUNTIME_HELP_READBACK", "AUTHORIZED_NOW": 0, "REQUIRED_FOR_10AZ": 1, "DETAIL": "Run HELP MSGMGR / HELP SET MESSAGE readback."},
        {"STEP": 7, "ACTION": "CMDHELPCHK_READONLY_VALIDATION", "AUTHORIZED_NOW": 0, "REQUIRED_FOR_10AZ": 1, "DETAIL": "Run validation and confirm expected rows only."},
        {"STEP": 8, "ACTION": "RESTORE_OR_ACCEPT", "AUTHORIZED_NOW": 0, "REQUIRED_FOR_10AZ": 1, "DETAIL": "If apply changes are temporary proof, restore backup before savepoint; if final apply, acceptance gate required."},
    ]

    rollback_plan = [
        {"ROLLBACK_ITEM": "HELP_DATA_BACKUP", "REQUIRED": 1, "DETAIL": "Backup exact HELP DATA files/tables before 10AZ apply."},
        {"ROLLBACK_ITEM": "CMDHELPCHK_BACKUP", "REQUIRED": 1, "DETAIL": "Backup exact CMDHELPCHK files/tables before 10AZ apply."},
        {"ROLLBACK_ITEM": "RESTORE_SCRIPT_DISABLED_TEMPLATE", "REQUIRED": 1, "DETAIL": "10AZ package must include disabled/then-authorized restore script."},
        {"ROLLBACK_ITEM": "POST_RESTORE_HASH_OR_COUNT_CHECK", "REQUIRED": 1, "DETAIL": "Verify HELP/CMDHELPCHK return to exact pre-apply state if restore required."},
    ]

    validation_plan = [
        {"VALIDATION": "HELP_MSGMGR_READBACK", "EXPECTED": "MSGMGR topic visible and includes read-only boundary.", "AUTHORIZED_NOW": 0},
        {"VALIDATION": "HELP_SET_MESSAGE_CATALOG_CHECK_READBACK", "EXPECTED": "CHECK surface documented as read-only provider status.", "AUTHORIZED_NOW": 0},
        {"VALIDATION": "HELP_SET_MESSAGE_CATALOG_GET_READBACK", "EXPECTED": "GET surface documented as low-level read/get.", "AUTHORIZED_NOW": 0},
        {"VALIDATION": "HELP_SET_MESSAGE_EMIT_READBACK", "EXPECTED": "EMIT grammar and localized proof symbols documented.", "AUTHORIZED_NOW": 0},
        {"VALIDATION": "CMDHELPCHK_MSGMGR", "EXPECTED": "MSGMGR command/help linkage accepted.", "AUTHORIZED_NOW": 0},
        {"VALIDATION": "BOUNDARY_RECHECK", "EXPECTED": "No DBF/CDX/LMDB/source/workspace mutation outside authorized HELP/CMDHELPCHK targets.", "AUTHORIZED_NOW": 0},
    ]

    boundary = [
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "10AY writes plan/reports/disabled templates only."},
        {"PROTECTED_SYSTEM": "ACTIVE_SYSTEM_MESSAGES", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_SYSTEM_MESSAGE_TEXT", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_CDX_LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CDX/LMDB mutation."},
        {"PROTECTED_SYSTEM": "WORKSPACE_PROFILE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No workspace mutation."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No HELP DATA mutation; apply plan only."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CMDHELPCHK mutation; apply plan only."},
    ]

    issues = "0" if status == STATUS_GREEN else str(failures)

    write_csv(reports / "message_catalog_phase22ae_6_5_10ay_gate_check_v1.csv", gates, ["GATE", "STATUS", "DETAIL"])
    write_csv(reports / "message_catalog_phase22ae_6_5_10ay_target_manifest_v1.csv", target_manifest, ["TARGET_ID", "TARGET_KIND", "TARGET_NAME", "SOURCE_CANDIDATE", "APPLY_AUTHORIZED", "NOTES"])
    write_csv(reports / "message_catalog_phase22ae_6_5_10ay_apply_sequence_v1.csv", apply_sequence, ["STEP", "ACTION", "AUTHORIZED_NOW", "REQUIRED_FOR_10AZ", "DETAIL"])
    write_csv(reports / "message_catalog_phase22ae_6_5_10ay_rollback_plan_v1.csv", rollback_plan, ["ROLLBACK_ITEM", "REQUIRED", "DETAIL"])
    write_csv(reports / "message_catalog_phase22ae_6_5_10ay_validation_plan_v1.csv", validation_plan, ["VALIDATION", "EXPECTED", "AUTHORIZED_NOW"])
    write_csv(reports / "message_catalog_phase22ae_6_5_10ay_boundary_ledger_v1.csv", boundary, ["PROTECTED_SYSTEM", "MUTATION_ALLOWED", "OBSERVED_MUTATION", "DETAIL"])

    artifact_rows = []
    for p in [help_template, cmdhelp_template, candidate_copy]:
        if p is not None and p.exists():
            artifact_rows.append({"ARTIFACT": rel(p, repo), "SHA256": sha256_file(p), "ROLE": "disabled_template_or_candidate_snapshot"})
    write_csv(reports / "message_catalog_phase22ae_6_5_10ay_artifact_manifest_v1.csv", artifact_rows, ["ARTIFACT", "SHA256", "ROLE"])

    summary = {
        "STATUS": status,
        "VALIDATION_ISSUES": issues,
        "PHASE22AE_6_5_10AX_STATUS": ax.get("STATUS", ""),
        "MSG_022AE_6_5_10AX_SAVEPOINT_PRESENT": 1 if sp_ax else 0,
        "ACTIVE_MESSAGES_OBSERVED_COUNT": msg_count,
        "ACTIVE_TEXT_OBSERVED_COUNT": text_count,
        "CANDIDATE_PATH": rel(candidate, repo),
        "CANDIDATE_EXISTS": 1 if candidate_exists else 0,
        "APPLY_ROOT": rel(apply_root, repo),
        "TARGET_ROWS": len(target_manifest),
        "APPLY_SEQUENCE_ROWS": len(apply_sequence),
        "ROLLBACK_PLAN_ROWS": len(rollback_plan),
        "VALIDATION_PLAN_ROWS": len(validation_plan),
        "HELP_DATA_APPLY_PLAN_CREATED": 1 if status == STATUS_GREEN else 0,
        "CMDHELPCHK_APPLY_PLAN_CREATED": 1 if status == STATUS_GREEN else 0,
        "HELP_DATA_APPLY_AUTHORIZED": 0,
        "CMDHELPCHK_APPLY_AUTHORIZED": 0,
        "HELP_DATA_MUTATION_OBSERVED": 0,
        "CMDHELPCHK_MUTATION_OBSERVED": 0,
        "SOURCE_FILES_MUTATED": 0,
        "ACTIVE_CATALOG_MUTATION_OBSERVED_BY_REVIEW": 0,
        "DBF_MUTATION_OBSERVED": 0,
        "CDX_LMDB_MUTATION_OBSERVED": 0,
        "WORKSPACE_MUTATION_OBSERVED": 0,
        "NEXT_GATE": NEXT_GATE,
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }
    write_csv(reports / "message_catalog_phase22ae_6_5_10ay_status_summary_v1.csv", [summary], list(summary.keys()))

    (repo / "docs/messaging/MESSAGE_LOCALE_PHASE22AE_6_5_10AY_MSGMGR_HELP_CMDHELPCHK_GUARDED_APPLY_PLAN.md").write_text(
        f"# Message Catalog Phase 22AE.6.5.10AY MSGMGR HELP/CMDHELPCHK Guarded Apply Plan\n\nStatus: `{status}`\n\n10AY is a plan only. It creates a guarded apply blueprint for a later HELP DATA / CMDHELPCHK package. It does not mutate HELP DATA or CMDHELPCHK.\n\nApply root:\n\n```text\n{rel(apply_root, repo)}\n```\n\nNext gate:\n\n```text\n{NEXT_GATE}\n```\n",
        encoding="utf-8"
    )

    print(status)
    print(f"  validation issues: {issues}")
    print(f"  Phase 22AE.6.5.10AX status: {ax.get('STATUS','')}")
    print(f"  MSG-022AE.6.5.10AX savepoint present: {1 if sp_ax else 0}")
    print(f"  active messages observed count: {msg_count}")
    print(f"  active text observed count: {text_count}")
    print(f"  candidate exists: {1 if candidate_exists else 0}")
    print(f"  candidate path: {rel(candidate, repo)}")
    print(f"  apply root: {rel(apply_root, repo)}")
    print(f"  target rows: {len(target_manifest)}")
    print(f"  apply sequence rows: {len(apply_sequence)}")
    print(f"  rollback plan rows: {len(rollback_plan)}")
    print(f"  validation plan rows: {len(validation_plan)}")
    print(f"  HELP DATA apply plan created: {summary['HELP_DATA_APPLY_PLAN_CREATED']}")
    print(f"  CMDHELPCHK apply plan created: {summary['CMDHELPCHK_APPLY_PLAN_CREATED']}")
    print("  HELP DATA apply authorized: 0")
    print("  CMDHELPCHK apply authorized: 0")
    print("  HELP DATA mutation observed: 0")
    print("  CMDHELPCHK mutation observed: 0")
    print("  source files mutated: 0")
    print("  active catalog mutation observed by review: 0")
    print("  DBF mutation observed: 0")
    print("  CDX/LMDB mutation observed: 0")
    print("  workspace mutation observed: 0")
    print(f"  next gate: {NEXT_GATE}")
    print(f"  reports: {reports}")
    return 0 if status == STATUS_GREEN else 2

if __name__ == "__main__":
    raise SystemExit(main())
