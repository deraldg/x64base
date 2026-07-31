#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import shutil
from datetime import datetime, timezone
from pathlib import Path

STATUS_GREEN = "MESSAGE_CATALOG_PHASE22I_C_SET_LANGUAGE_LOCALE_STATE_BRIDGE_REPAIR_APPLIED"
STATUS_BLOCKED = "MESSAGE_CATALOG_PHASE22I_C_SET_LANGUAGE_LOCALE_STATE_BRIDGE_REPAIR_BLOCKED"
NEXT_GATE = "BUILD_AND_RUN_PHASE22I_C_LOCALE_BRIDGE_SMOKE_THEN_VALIDATE"
REPORT_DIR = Path("docs/messaging/reports")
BACKUP_ROOT_BASE = Path("docs/messaging/backups")

OLD_SIGNATURE = "static void handle_set_message_emit(std::istringstream& args) {"
NEW_SIGNATURE = "static void handle_set_message_emit(std::istringstream& args, const std::string& default_locale) {"

OLD_DEFAULT = "    std::string locale = message_catalog_current_locale();"
NEW_DEFAULT = "    std::string locale = default_locale.empty()\n        ? std::string(\"en-US\")\n        : default_locale;"

OLD_CALL = "            handle_set_message_emit(args);"
NEW_CALL = "            handle_set_message_emit(args, S.message_locale);"

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
        w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        w.writeheader()
        for row in rows:
            w.writerow({k: row.get(k, "") for k in fields})

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    if not path.exists() or not path.is_file():
        return ""
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def rel(path: Path, repo: Path):
    try:
        return str(path.relative_to(repo)).replace("\\", "/")
    except ValueError:
        return str(path)

def backup(path: Path, backup_root: Path, repo: Path, rows):
    if not path.exists():
        return
    dst = backup_root / rel(path, repo)
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, dst)
    rows.append({
        "TARGET_PATH": rel(path, repo),
        "BACKUP_PATH": rel(dst, repo),
        "BYTES": dst.stat().st_size,
        "SHA256": sha256_file(dst),
        "ROLE": "pre_patch_source_backup",
    })

def replace_once_or_already(text: str, old: str, new: str, label: str, actions):
    if old in text:
        text = text.replace(old, new, 1)
        actions.append({"ACTION": "REPLACE", "DETAIL": label})
        return text
    if new in text:
        actions.append({"ACTION": "ALREADY_PRESENT", "DETAIL": label})
        return text
    raise RuntimeError(f"required patch anchor not found for {label}")

def patch_cmd_set(text: str):
    actions = []

    required = [
        "S.message_locale",
        "SET MESSAGE EMIT",
        "handle_set_message_emit",
        "message_catalog_current_locale()",
    ]
    for needle in required:
        if needle not in text:
            raise RuntimeError(f"required prior surface missing: {needle}")

    text = replace_once_or_already(
        text,
        OLD_SIGNATURE,
        NEW_SIGNATURE,
        "handle_set_message_emit accepts default_locale",
        actions,
    )

    text = replace_once_or_already(
        text,
        OLD_DEFAULT,
        NEW_DEFAULT,
        "SET MESSAGE EMIT default locale uses caller-provided locale state",
        actions,
    )

    text = replace_once_or_already(
        text,
        OLD_CALL,
        NEW_CALL,
        "SET MESSAGE EMIT branch passes S.message_locale",
        actions,
    )

    return text, actions

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--allow-source-mutation", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    reports = repo / REPORT_DIR
    reports.mkdir(parents=True, exist_ok=True)

    p22ib1 = first_row(reports / "message_catalog_phase22i_b_1_status_summary_v1.csv")
    messages = p22ib1.get("MESSAGES", "12")
    text_rows = p22ib1.get("TEXT_ROWS", "60")
    locales = p22ib1.get("LOCALES", "de;en-US;es;fr;it")

    cmd_set = repo / "src/cli/cmd_set.cpp"

    gates = []
    failures = 0

    def gate(name, ok, detail):
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": detail})
        if not ok:
            failures += 1

    gate("OPERATOR_AUTHORIZED_SOURCE_MUTATION", args.allow_source_mutation, "requires --allow-source-mutation")
    gate("PHASE22I_B1_PARTIAL_REPAIR_REQUIRED",
         p22ib1.get("STATUS") == "MESSAGE_CATALOG_PHASE22I_B_CONTROLLED_EMISSION_PARTIAL_DEFAULT_LOCALE_BRIDGE_REPAIR_REQUIRED",
         p22ib1.get("STATUS", ""))
    gate("EXPLICIT_EMIT_PROOF_PRESENT",
         p22ib1.get("CONTROLLED_EXPLICIT_EMIT_PROOF") == "1",
         p22ib1.get("CONTROLLED_EXPLICIT_EMIT_PROOF", ""))
    gate("DEFAULT_BRIDGE_MISSING",
         p22ib1.get("DEFAULT_LOCALE_BRIDGE_PROOF") == "0",
         p22ib1.get("DEFAULT_LOCALE_BRIDGE_PROOF", ""))
    gate("CMD_SET_CPP_PRESENT", cmd_set.exists(), rel(cmd_set, repo))

    backup_rows = []
    mutation_rows = []
    action_rows = []
    errors = []
    status = STATUS_BLOCKED

    if failures == 0:
        try:
            backup_root = repo / BACKUP_ROOT_BASE / f"MSG-022I-C_LOCALE_BRIDGE_BACKUP_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
            backup(cmd_set, backup_root, repo, backup_rows)

            original = cmd_set.read_text(encoding="utf-8", errors="replace")
            patched, actions = patch_cmd_set(original)
            cmd_set.write_text(patched, encoding="utf-8")

            for action in actions:
                action_rows.append({
                    "TARGET_PATH": rel(cmd_set, repo),
                    "ACTION": action["ACTION"],
                    "DETAIL": action["DETAIL"],
                })

            mutation_rows.append({
                "TARGET_PATH": rel(cmd_set, repo),
                "ACTION": "UPDATE",
                "BYTES": cmd_set.stat().st_size,
                "SHA256": sha256_file(cmd_set),
                "DETAIL": "bridged SET MESSAGE EMIT default locale to S.message_locale while preserving explicit LOCALE override",
            })
            status = STATUS_GREEN
        except Exception as exc:
            failures += 1
            errors.append(str(exc))
            gates.append({"GATE": "PATCH_CMD_SET_CPP", "STATUS": "FAIL", "DETAIL": str(exc)})

    validation_issues = "0" if status == STATUS_GREEN else str(failures)

    write_csv(reports / "message_catalog_phase22i_c_status_summary_v1.csv", [{
        "STATUS": status,
        "MESSAGES": messages,
        "TEXT_ROWS": text_rows,
        "LOCALES": locales,
        "VALIDATION_ISSUES": validation_issues,
        "SOURCE_MUTATION_AUTHORIZED": 1 if args.allow_source_mutation else 0,
        "SOURCE_FILES_MUTATED": len(mutation_rows),
        "SOURCE_BACKUP_ROWS": len(backup_rows),
        "LOCALE_STATE_BRIDGE_REPAIR_APPLIED": 1 if status == STATUS_GREEN else 0,
        "BUILD_EXECUTED": 0,
        "RUNTIME_SMOKE_EXECUTED": 0,
        "ERRORS": "; ".join(errors),
        "NEXT_GATE": NEXT_GATE,
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }], ["STATUS", "MESSAGES", "TEXT_ROWS", "LOCALES", "VALIDATION_ISSUES",
         "SOURCE_MUTATION_AUTHORIZED", "SOURCE_FILES_MUTATED", "SOURCE_BACKUP_ROWS",
         "LOCALE_STATE_BRIDGE_REPAIR_APPLIED", "BUILD_EXECUTED", "RUNTIME_SMOKE_EXECUTED",
         "ERRORS", "NEXT_GATE", "REPORT_TIMESTAMP_UTC"])

    write_csv(reports / "message_catalog_phase22i_c_gate_check_v1.csv", gates,
              ["GATE", "STATUS", "DETAIL"])
    write_csv(reports / "message_catalog_phase22i_c_patch_actions_v1.csv", action_rows,
              ["TARGET_PATH", "ACTION", "DETAIL"])
    write_csv(reports / "message_catalog_phase22i_c_source_mutation_inventory_v1.csv", mutation_rows,
              ["TARGET_PATH", "ACTION", "BYTES", "SHA256", "DETAIL"])
    write_csv(reports / "message_catalog_phase22i_c_source_backup_inventory_v1.csv", backup_rows,
              ["TARGET_PATH", "BACKUP_PATH", "BYTES", "SHA256", "ROLE"])

    boundary = [
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 1, "OBSERVED_MUTATION": len(mutation_rows), "DETAIL": "Authorized source mutation limited to src/cli/cmd_set.cpp locale-state bridge for SET MESSAGE EMIT."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_DBF_CATALOG", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_CDX_INDEXES", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active CDX/index mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active LMDB mutation."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No HELP DATA mutation."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CMDHELPCHK mutation."},
        {"PROTECTED_SYSTEM": "MANUALGEN", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No manualgen mutation."},
        {"PROTECTED_SYSTEM": "DATADICT_SELF_DOC", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No Data Dictionary/SelfDoc mutation."},
    ]
    write_csv(reports / "message_catalog_phase22i_c_boundary_ledger_v1.csv", boundary,
              ["PROTECTED_SYSTEM", "MUTATION_ALLOWED", "OBSERVED_MUTATION", "DETAIL"])

    smoke = repo / "docs/messaging/scripts/MESSAGE_CATALOG_PHASE22I_C_LOCALE_BRIDGE_SMOKE.dts"
    smoke.parent.mkdir(parents=True, exist_ok=True)
    smoke.write_text("\n".join([
        "* MESSAGE_CATALOG_PHASE22I_C_LOCALE_BRIDGE_SMOKE.dts",
        "* Verify SET MESSAGE EMIT default locale bridges to real SET LANGUAGE state.",
        "SET LANGUAGE es",
        "SET MESSAGE EMIT HELP_HINT_COMMAND",
        "SET MESSAGE EMIT HELP_HINT_COMMAND LOCALE es",
        "",
    ]), encoding="utf-8")

    print(status)
    print(f"  messages: {messages}")
    print(f"  text rows: {text_rows}")
    print(f"  locales: {locales.replace(';', ', ')}")
    print(f"  validation issues: {validation_issues}")
    print(f"  source mutation authorized: {1 if args.allow_source_mutation else 0}")
    print(f"  source files mutated: {len(mutation_rows)}")
    print(f"  source backup rows: {len(backup_rows)}")
    print("  build executed: 0")
    print("  runtime smoke executed: 0")
    print(f"  next gate: {NEXT_GATE}")
    print(f"  reports: {reports}")
    return 0 if status == STATUS_GREEN else 2

if __name__ == "__main__":
    raise SystemExit(main())
