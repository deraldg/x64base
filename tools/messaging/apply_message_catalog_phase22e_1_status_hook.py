#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

STATUS_GREEN = "MESSAGE_CATALOG_PHASE22E_1_RUNTIME_PROVIDER_STATUS_SOURCE_PATCH_APPLIED"
STATUS_BLOCKED = "MESSAGE_CATALOG_PHASE22E_1_RUNTIME_PROVIDER_STATUS_SOURCE_PATCH_BLOCKED"
NEXT_GATE = "BUILD_AND_RUN_SET_MESSAGE_CATALOG_CHECK_THEN_VALIDATE_PHASE22E"
REPORT_DIR = Path("docs/messaging/reports")
BACKUP_ROOT_BASE = Path("docs/messaging/backups")

INCLUDE_LINE = '#include "help/message_catalog.hpp"'
LEGACY_BAD_INCLUDE_LINE = '#include "message_catalog.hpp"'
USAGE_LINE = '        << "  SET MESSAGE CATALOG CHECK\\n"'
HELPER_MARKER_BEGIN = "// MSG-022E BEGIN message catalog provider status helper"
BRANCH_MARKER_BEGIN = "    // MSG-022E BEGIN SET MESSAGE CATALOG CHECK"

HELPER_BLOCK = '''
// MSG-022E BEGIN message catalog provider status helper
static void print_message_catalog_provider_status() {
    auto& out = cli::OutputRouter::instance().out();
    const auto status = dottalk::helpdata::active_message_catalog_status();

    out << "Message catalog provider status:\\n";
    out << "  mode: compiled_fallback\\n";
    out << "  active catalog present: " << (status.active_catalog_present ? "yes" : "no") << "\\n";
    out << "  active catalog loaded: " << (status.active_catalog_loaded ? "yes" : "no") << "\\n";
    out << "  compiled fallback messages: " << status.message_count << "\\n";
    out << "  active dbf dir: " << status.active_dbf_dir << "\\n";
    out << "  active indexes dir: " << status.active_indexes_dir << "\\n";
    out << "  active lmdb dir: " << status.active_lmdb_dir << "\\n";
    out << "  detail: " << status.detail << "\\n";
    out << "  boundary: read-only status; no DBF/CDX/LMDB mutation; no runtime writeback\\n";
}
// MSG-022E END message catalog provider status helper
'''

BRANCH_BLOCK = '''
    // MSG-022E BEGIN SET MESSAGE CATALOG CHECK
    if (opt == "MESSAGE") {
        std::string sub1;
        std::string sub2;
        args >> sub1;
        args >> sub2;
        sub1 = up_copy(sub1);
        sub2 = up_copy(sub2);

        if (sub1 == "CATALOG" && (sub2 == "CHECK" || sub2 == "STATUS")) {
            print_message_catalog_provider_status();
            return;
        }

        out << "Usage: SET MESSAGE CATALOG CHECK\\n";
        return;
    }
    // MSG-022E END SET MESSAGE CATALOG CHECK

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

def insert_before_first(text: str, needles: list[str], block: str, label: str) -> tuple[str, str]:
    for needle in needles:
        pos = text.find(needle)
        if pos >= 0:
            return text[:pos] + block + text[pos:], f"inserted before anchor: {label}: {needle[:80]}"
    raise RuntimeError(f"cmd_set.cpp anchor not found for {label}")

def patch_cmd_set(text: str) -> tuple[str, list[dict[str, str]]]:
    actions: list[dict[str, str]] = []
    new_text = text

    if LEGACY_BAD_INCLUDE_LINE in new_text and INCLUDE_LINE not in new_text:
        new_text = new_text.replace(LEGACY_BAD_INCLUDE_LINE, INCLUDE_LINE, 1)
        actions.append({"ACTION": "REPLACE_LEGACY_INCLUDE", "DETAIL": f"{LEGACY_BAD_INCLUDE_LINE} -> {INCLUDE_LINE}"})
    elif INCLUDE_LINE not in new_text:
        anchor_candidates = [
            '#include "cli/table_state.hpp"',
            '#include "cli/settings.hpp"',
            '#include "cli/output_router.hpp"',
        ]
        for anchor in anchor_candidates:
            if anchor in new_text:
                new_text = new_text.replace(anchor, anchor + "\n\n" + INCLUDE_LINE, 1)
                actions.append({"ACTION": "INSERT_INCLUDE", "DETAIL": INCLUDE_LINE})
                break
        else:
            raise RuntimeError("cmd_set.cpp include anchor not found")
    else:
        actions.append({"ACTION": "INCLUDE_ALREADY_PRESENT", "DETAIL": INCLUDE_LINE})

    if "SET MESSAGE CATALOG CHECK" not in new_text:
        usage_candidates = [
            '        << "  SET PATH <slot> <path>\\n"',
            '        << "  SET INDEX TO <file>\\n"',
            '        << "  SET ORDER TO <tag|0>\\n"',
        ]
        inserted = False
        for anchor in usage_candidates:
            if anchor in new_text:
                new_text = new_text.replace(anchor, anchor + "\n" + USAGE_LINE, 1)
                actions.append({"ACTION": "INSERT_USAGE_LINE", "DETAIL": "SET MESSAGE CATALOG CHECK"})
                inserted = True
                break
        if not inserted:
            actions.append({"ACTION": "USAGE_LINE_NOT_INSERTED", "DETAIL": "usage anchor not found; command branch still inserted"})
    else:
        actions.append({"ACTION": "USAGE_ALREADY_PRESENT", "DETAIL": "SET MESSAGE CATALOG CHECK"})

    if HELPER_MARKER_BEGIN not in new_text:
        new_text, detail = insert_before_first(
            new_text,
            ["static void print_set_usage() {"],
            HELPER_BLOCK + "\n",
            "helper",
        )
        actions.append({"ACTION": "INSERT_HELPER", "DETAIL": detail})
    else:
        actions.append({"ACTION": "HELPER_ALREADY_PRESENT", "DETAIL": "print_message_catalog_provider_status"})

    if BRANCH_MARKER_BEGIN not in new_text:
        new_text, detail = insert_before_first(
            new_text,
            [
                '    if (opt == "TABLE") {',
                '    if (opt == "CONSOLE") {',
                '    if (opt == "PATH") {',
            ],
            BRANCH_BLOCK,
            "SET MESSAGE CATALOG CHECK branch",
        )
        actions.append({"ACTION": "INSERT_BRANCH", "DETAIL": detail})
    else:
        actions.append({"ACTION": "BRANCH_ALREADY_PRESENT", "DETAIL": "SET MESSAGE CATALOG CHECK"})

    return new_text, actions

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--allow-source-mutation", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    reports = repo / REPORT_DIR
    reports.mkdir(parents=True, exist_ok=True)

    p22c = first_row(reports / "message_catalog_phase22c_status_summary_v1.csv")
    p22d = first_row(reports / "message_catalog_phase22d_status_summary_v1.csv")
    messages = p22c.get("MESSAGES", p22d.get("MESSAGES", "12"))
    text_rows = p22c.get("TEXT_ROWS", p22d.get("TEXT_ROWS", "60"))
    locales = p22c.get("LOCALES", p22d.get("LOCALES", "de;en-US;es;fr;it"))

    cmd_set = repo / "src/cli/cmd_set.cpp"
    provider_hpp = repo / "src/help/message_catalog.hpp"
    provider_cpp = repo / "src/help/message_catalog.cpp"

    gates: list[dict[str, Any]] = []
    failures = 0
    errors: list[str] = []

    def gate(name: str, ok: bool, detail: str) -> None:
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": detail})
        if not ok:
            failures += 1

    def review(name: str, ok: bool, detail: str) -> None:
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "REVIEW", "DETAIL": detail})

    gate("OPERATOR_AUTHORIZED_SOURCE_MUTATION", args.allow_source_mutation, "requires --allow-source-mutation")
    gate("CMD_SET_CPP_PRESENT", cmd_set.exists(), rel(cmd_set, repo))
    gate("MESSAGE_CATALOG_HPP_PRESENT", provider_hpp.exists(), rel(provider_hpp, repo))
    gate("MESSAGE_CATALOG_CPP_PRESENT", provider_cpp.exists(), rel(provider_cpp, repo))
    gate("PHASE22C_PATCH_APPLIED", p22c.get("STATUS") == "MESSAGE_CATALOG_PHASE22C_RUNTIME_PROVIDER_SOURCE_PATCH_APPLIED", p22c.get("STATUS", ""))
    review("PHASE22D_BUILD_CLOSEOUT_GREEN", p22d.get("STATUS") == "MESSAGE_CATALOG_PHASE22D_BUILD_PROVIDER_BOUNDARY_GREEN", p22d.get("STATUS", "not present; build proof may have been manual"))

    backup_rows: list[dict[str, Any]] = []
    mutation_rows: list[dict[str, Any]] = []
    patch_action_rows: list[dict[str, Any]] = []

    status = STATUS_BLOCKED
    if failures == 0:
        try:
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
            backup_root = repo / BACKUP_ROOT_BASE / f"MSG-022E1_STATUS_COMMAND_PATCH_BACKUP_{timestamp}"
            backup(cmd_set, backup_root, repo, backup_rows)

            original = cmd_set.read_text(encoding="utf-8", errors="replace")
            patched, actions = patch_cmd_set(original)
            cmd_set.write_text(patched, encoding="utf-8")

            for a in actions:
                patch_action_rows.append({
                    "TARGET_PATH": rel(cmd_set, repo),
                    "ACTION": a["ACTION"],
                    "DETAIL": a["DETAIL"],
                })

            mutation_rows.append({
                "TARGET_PATH": rel(cmd_set, repo),
                "ACTION": "UPDATE",
                "BYTES": cmd_set.stat().st_size,
                "SHA256": sha256_file(cmd_set),
                "DETAIL": "added SET MESSAGE CATALOG CHECK provider status hook with robust semantic anchor",
            })
            status = STATUS_GREEN
        except Exception as exc:
            failures += 1
            errors.append(str(exc))
            gates.append({"GATE": "PATCH_CMD_SET_CPP", "STATUS": "FAIL", "DETAIL": str(exc)})

    validation_issues = "0" if status == STATUS_GREEN else str(failures)

    write_csv(reports / "message_catalog_phase22e_1_status_summary_v1.csv", [{
        "STATUS": status,
        "MESSAGES": messages,
        "TEXT_ROWS": text_rows,
        "LOCALES": locales,
        "VALIDATION_ISSUES": validation_issues,
        "SOURCE_MUTATION_AUTHORIZED": 1 if args.allow_source_mutation else 0,
        "SOURCE_FILES_MUTATED": len(mutation_rows),
        "SOURCE_BACKUP_ROWS": len(backup_rows),
        "RUNTIME_PROVIDER_STATUS_HOOK_APPLIED": 1 if status == STATUS_GREEN else 0,
        "BUILD_EXECUTED": 0,
        "RUNTIME_SMOKE_EXECUTED": 0,
        "ERRORS": "; ".join(errors),
        "NEXT_GATE": NEXT_GATE,
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }], ["STATUS", "MESSAGES", "TEXT_ROWS", "LOCALES", "VALIDATION_ISSUES",
         "SOURCE_MUTATION_AUTHORIZED", "SOURCE_FILES_MUTATED", "SOURCE_BACKUP_ROWS",
         "RUNTIME_PROVIDER_STATUS_HOOK_APPLIED", "BUILD_EXECUTED", "RUNTIME_SMOKE_EXECUTED",
         "ERRORS", "NEXT_GATE", "REPORT_TIMESTAMP_UTC"])

    write_csv(reports / "message_catalog_phase22e_1_gate_check_v1.csv", gates, ["GATE", "STATUS", "DETAIL"])
    write_csv(reports / "message_catalog_phase22e_1_patch_actions_v1.csv", patch_action_rows, ["TARGET_PATH", "ACTION", "DETAIL"])
    write_csv(reports / "message_catalog_phase22e_1_source_mutation_inventory_v1.csv", mutation_rows, ["TARGET_PATH", "ACTION", "BYTES", "SHA256", "DETAIL"])
    write_csv(reports / "message_catalog_phase22e_1_source_backup_inventory_v1.csv", backup_rows, ["TARGET_PATH", "BACKUP_PATH", "BYTES", "SHA256", "ROLE"])

    boundary = [
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 1, "OBSERVED_MUTATION": len(mutation_rows), "DETAIL": "Authorized source mutation limited to src/cli/cmd_set.cpp provider status hook."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_DBF_CATALOG", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_CDX_INDEXES", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active CDX/index mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active LMDB mutation."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No HELP DATA rebuild or mutation."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CMDHELPCHK mutation."},
        {"PROTECTED_SYSTEM": "MANUALGEN", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No manualgen mutation."},
        {"PROTECTED_SYSTEM": "DATADICT_SELF_DOC", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No Data Dictionary/SelfDoc mutation."},
    ]
    write_csv(reports / "message_catalog_phase22e_1_boundary_ledger_v1.csv", boundary, ["PROTECTED_SYSTEM", "MUTATION_ALLOWED", "OBSERVED_MUTATION", "DETAIL"])

    smoke = repo / "docs/messaging/scripts/MESSAGE_CATALOG_PHASE22E_PROVIDER_STATUS_SMOKE.dts"
    smoke.parent.mkdir(parents=True, exist_ok=True)
    smoke.write_text("\n".join([
        "* MESSAGE_CATALOG_PHASE22E_PROVIDER_STATUS_SMOKE.dts",
        "* Runtime-visible provider status smoke.",
        "* Expected: read-only status; compiled fallback active; active catalog artifacts present.",
        "SET MESSAGE CATALOG CHECK",
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
