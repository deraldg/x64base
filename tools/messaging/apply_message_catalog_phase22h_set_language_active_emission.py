#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

STATUS_GREEN = "MESSAGE_CATALOG_PHASE22H_SET_LANGUAGE_ACTIVE_MESSAGE_EMISSION_SOURCE_PATCH_APPLIED"
STATUS_BLOCKED = "MESSAGE_CATALOG_PHASE22H_SET_LANGUAGE_ACTIVE_MESSAGE_EMISSION_SOURCE_PATCH_BLOCKED"
NEXT_GATE = "BUILD_AND_RUN_SET_LANGUAGE_ACTIVE_MESSAGE_EMISSION_THEN_VALIDATE_PHASE22H"
REPORT_DIR = Path("docs/messaging/reports")
BACKUP_ROOT_BASE = Path("docs/messaging/backups")

HELPER_BEGIN = "// MSG-022H BEGIN SET LANGUAGE active message emission helper"
HELPER_END = "// MSG-022H END SET LANGUAGE active message emission helper"

HELPER_BLOCK = r'''// MSG-022H BEGIN SET LANGUAGE active message emission helper
static void print_language_active_message_emission_check(const std::string& current_locale) {
    auto& out = cli::OutputRouter::instance().out();
    const auto status = dottalk::helpdata::active_message_catalog_status();
    const std::string text =
        dottalk::helpdata::format_message_catalog(current_locale, "HELP_HINT_COMMAND");

    out << "SET LANGUAGE active message emission:\n";
    out << "  current locale: " << current_locale << "\n";
    out << "  provider mode: " << message_catalog_mode_name(status.mode) << "\n";
    out << "  active catalog loaded: " << (status.active_catalog_loaded ? "yes" : "no") << "\n";
    out << "  symbol: HELP_HINT_COMMAND\n";
    out << "  fallback locale: en-US\n";
    out << "  text: " << (text.empty() ? "<missing>" : text) << "\n";
    out << "  boundary: read-only emission; no DBF/CDX/LMDB mutation; no runtime writeback\n";
}
// MSG-022H END SET LANGUAGE active message emission helper

'''

OLD_CHECK_BLOCK = '''        if (tok_up == "CHECK" || tok_up == "VALIDATE" || tok_up == "CATALOG") {
            print_message_catalog_status();
            return;
        }
'''

NEW_CHECK_BLOCK = '''        if (tok_up == "CHECK" || tok_up == "VALIDATE" || tok_up == "CATALOG") {
            print_message_catalog_status();
            print_language_active_message_emission_check(S.message_locale);
            return;
        }
'''

def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

def first_row(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    rows = read_csv(path)
    return rows[0] if rows else {}

def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        w.writeheader()
        for row in rows:
            w.writerow({k: row.get(k, "") for k in fields})

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def rel(path: Path, repo: Path) -> str:
    try:
        return str(path.relative_to(repo)).replace("\\", "/")
    except ValueError:
        return str(path)

def backup(path: Path, backup_root: Path, repo: Path, rows: list[dict[str, Any]]) -> None:
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

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--allow-source-mutation", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    reports = repo / REPORT_DIR
    reports.mkdir(parents=True, exist_ok=True)

    p22g = first_row(reports / "message_catalog_phase22g_runtime_status_summary_v1.csv")
    messages = p22g.get("MESSAGES", "12")
    text_rows = p22g.get("TEXT_ROWS", "60")
    locales = p22g.get("LOCALES", "de;en-US;es;fr;it")

    cmd_set = repo / "src/cli/cmd_set.cpp"
    text = cmd_set.read_text(encoding="utf-8", errors="replace") if cmd_set.exists() else ""

    gates: list[dict[str, Any]] = []
    failures = 0

    def gate(name: str, ok: bool, detail: str) -> None:
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": detail})
        if not ok:
            failures += 1

    gate("OPERATOR_AUTHORIZED_SOURCE_MUTATION", args.allow_source_mutation, "requires --allow-source-mutation")
    gate("PHASE22G_LOOKUP_SMOKE_GREEN",
         p22g.get("STATUS") == "MESSAGE_CATALOG_PHASE22G_SET_MESSAGE_CATALOG_GET_SMOKE_GREEN",
         p22g.get("STATUS", ""))
    gate("CMD_SET_CPP_PRESENT", cmd_set.exists(), rel(cmd_set, repo))
    gate("MESSAGE_CATALOG_MODE_HELPER_PRESENT", "message_catalog_mode_name" in text, "message_catalog_mode_name")
    gate("SET_LANGUAGE_CHECK_BLOCK_PRESENT", OLD_CHECK_BLOCK in text or "print_language_active_message_emission_check" in text, "SET LANGUAGE CHECK branch")
    gate("SET_MESSAGE_CATALOG_GET_PRESENT", "SET MESSAGE CATALOG GET <symbol> [locale]" in text, "Phase 22G command")

    backup_rows: list[dict[str, Any]] = []
    mutation_rows: list[dict[str, Any]] = []
    patch_actions: list[dict[str, Any]] = []
    status = STATUS_BLOCKED

    if failures == 0:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        backup_root = repo / BACKUP_ROOT_BASE / f"MSG-022H_SET_LANGUAGE_ACTIVE_EMISSION_BACKUP_{timestamp}"
        backup(cmd_set, backup_root, repo, backup_rows)

        new_text = text

        if HELPER_BEGIN not in new_text:
            anchor = "static void print_set_usage() {"
            if anchor not in new_text:
                raise RuntimeError("cmd_set.cpp anchor not found: static void print_set_usage()")
            new_text = new_text.replace(anchor, HELPER_BLOCK + anchor, 1)
            patch_actions.append({
                "TARGET_PATH": rel(cmd_set, repo),
                "ACTION": "INSERT_HELPER",
                "DETAIL": "print_language_active_message_emission_check",
            })
        else:
            patch_actions.append({
                "TARGET_PATH": rel(cmd_set, repo),
                "ACTION": "HELPER_ALREADY_PRESENT",
                "DETAIL": "print_language_active_message_emission_check",
            })

        if OLD_CHECK_BLOCK in new_text:
            new_text = new_text.replace(OLD_CHECK_BLOCK, NEW_CHECK_BLOCK, 1)
            patch_actions.append({
                "TARGET_PATH": rel(cmd_set, repo),
                "ACTION": "PATCH_SET_LANGUAGE_CHECK",
                "DETAIL": "append active Messaging provider emission after existing catalog status",
            })
        elif "print_language_active_message_emission_check(S.message_locale)" in new_text:
            patch_actions.append({
                "TARGET_PATH": rel(cmd_set, repo),
                "ACTION": "SET_LANGUAGE_CHECK_ALREADY_PATCHED",
                "DETAIL": "print_language_active_message_emission_check already called",
            })
        else:
            raise RuntimeError("SET LANGUAGE CHECK block not found for Phase 22H patch")

        cmd_set.write_text(new_text, encoding="utf-8")

        mutation_rows.append({
            "TARGET_PATH": rel(cmd_set, repo),
            "ACTION": "UPDATE",
            "BYTES": cmd_set.stat().st_size,
            "SHA256": sha256_file(cmd_set),
            "DETAIL": "SET LANGUAGE CHECK now emits one active Messaging provider-backed message lookup",
        })
        status = STATUS_GREEN

    validation_issues = "0" if status == STATUS_GREEN else str(failures)

    write_csv(reports / "message_catalog_phase22h_status_summary_v1.csv", [{
        "STATUS": status,
        "MESSAGES": messages,
        "TEXT_ROWS": text_rows,
        "LOCALES": locales,
        "VALIDATION_ISSUES": validation_issues,
        "SOURCE_MUTATION_AUTHORIZED": 1 if args.allow_source_mutation else 0,
        "SOURCE_FILES_MUTATED": len(mutation_rows),
        "SOURCE_BACKUP_ROWS": len(backup_rows),
        "SET_LANGUAGE_ACTIVE_MESSAGE_EMISSION_APPLIED": 1 if status == STATUS_GREEN else 0,
        "BUILD_EXECUTED": 0,
        "RUNTIME_SMOKE_EXECUTED": 0,
        "NEXT_GATE": NEXT_GATE,
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }], ["STATUS", "MESSAGES", "TEXT_ROWS", "LOCALES", "VALIDATION_ISSUES",
         "SOURCE_MUTATION_AUTHORIZED", "SOURCE_FILES_MUTATED", "SOURCE_BACKUP_ROWS",
         "SET_LANGUAGE_ACTIVE_MESSAGE_EMISSION_APPLIED", "BUILD_EXECUTED",
         "RUNTIME_SMOKE_EXECUTED", "NEXT_GATE", "REPORT_TIMESTAMP_UTC"])

    write_csv(reports / "message_catalog_phase22h_gate_check_v1.csv", gates, ["GATE", "STATUS", "DETAIL"])
    write_csv(reports / "message_catalog_phase22h_patch_actions_v1.csv", patch_actions, ["TARGET_PATH", "ACTION", "DETAIL"])
    write_csv(reports / "message_catalog_phase22h_source_mutation_inventory_v1.csv", mutation_rows,
              ["TARGET_PATH", "ACTION", "BYTES", "SHA256", "DETAIL"])
    write_csv(reports / "message_catalog_phase22h_source_backup_inventory_v1.csv", backup_rows,
              ["TARGET_PATH", "BACKUP_PATH", "BYTES", "SHA256", "ROLE"])

    boundary = [
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 1, "OBSERVED_MUTATION": len(mutation_rows), "DETAIL": "Authorized source mutation limited to src/cli/cmd_set.cpp SET LANGUAGE CHECK emission hook."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_DBF_CATALOG", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Provider lookup reads active DBFs only; no active DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_CDX_INDEXES", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active CDX/index mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active LMDB mutation."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No HELP DATA mutation."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CMDHELPCHK mutation."},
        {"PROTECTED_SYSTEM": "MANUALGEN", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No manualgen mutation."},
        {"PROTECTED_SYSTEM": "DATADICT_SELF_DOC", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No Data Dictionary/SelfDoc mutation."},
    ]
    write_csv(reports / "message_catalog_phase22h_boundary_ledger_v1.csv", boundary,
              ["PROTECTED_SYSTEM", "MUTATION_ALLOWED", "OBSERVED_MUTATION", "DETAIL"])

    smoke = repo / "docs/messaging/scripts/MESSAGE_CATALOG_PHASE22H_SET_LANGUAGE_ACTIVE_EMISSION_SMOKE.dts"
    smoke.parent.mkdir(parents=True, exist_ok=True)
    smoke.write_text("\n".join([
        "* MESSAGE_CATALOG_PHASE22H_SET_LANGUAGE_ACTIVE_EMISSION_SMOKE.dts",
        "* Runtime-visible SET LANGUAGE active Messaging provider emission proof.",
        "* Expected: SET LANGUAGE CHECK prints active provider-backed HELP_HINT_COMMAND text.",
        "SET LANGUAGE CHECK",
        "SET LANGUAGE TO es",
        "SET LANGUAGE CHECK",
        "SET LANGUAGE TO DEFAULT",
        "SET LANGUAGE CHECK",
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
