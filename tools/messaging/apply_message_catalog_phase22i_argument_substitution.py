#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

STATUS_GREEN = "MESSAGE_CATALOG_PHASE22I_ARGUMENT_SUBSTITUTION_SOURCE_PATCH_APPLIED"
STATUS_BLOCKED = "MESSAGE_CATALOG_PHASE22I_ARGUMENT_SUBSTITUTION_SOURCE_PATCH_BLOCKED"
NEXT_GATE = "BUILD_AND_RUN_ARGUMENT_SUBSTITUTION_THEN_VALIDATE_PHASE22I"
REPORT_DIR = Path("docs/messaging/reports")
BACKUP_ROOT_BASE = Path("docs/messaging/backups")

BRANCH_BEGIN = "    // MSG-022E BEGIN SET MESSAGE CATALOG CHECK"
BRANCH_END = "    // MSG-022E END SET MESSAGE CATALOG CHECK"

BRANCH_REPLACEMENT = '''    // MSG-022E BEGIN SET MESSAGE CATALOG CHECK
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

        if (sub1 == "CATALOG" && sub2 == "GET") {
            std::string symbol;
            std::string locale;
            args >> symbol;
            args >> locale;

            if (symbol.empty()) {
                out << "Usage: SET MESSAGE CATALOG GET <symbol> [locale] [name=value ...]\\n";
                return;
            }

            if (locale.empty()) {
                locale = "en-US";
            }

            std::unordered_map<std::string, std::string> vars;
            std::string assignment;
            while (args >> assignment) {
                const auto eq = assignment.find('=');
                if (eq == std::string::npos || eq == 0) {
                    continue;
                }
                const std::string key = assignment.substr(0, eq);
                const std::string value = assignment.substr(eq + 1);
                vars[key] = value;
            }

            const auto status = dottalk::helpdata::active_message_catalog_status();
            const std::string text = dottalk::helpdata::format_message_catalog(locale, symbol, vars);

            out << "Message catalog get:\\n";
            out << "  symbol: " << symbol << "\\n";
            out << "  locale: " << locale << "\\n";
            out << "  provider mode: " << message_catalog_mode_name(status.mode) << "\\n";
            out << "  active catalog loaded: " << (status.active_catalog_loaded ? "yes" : "no") << "\\n";
            out << "  fallback locale: en-US\\n";
            out << "  argument count: " << vars.size() << "\\n";
            for (const auto& kv : vars) {
                out << "  argument " << kv.first << ": " << kv.second << "\\n";
            }
            out << "  text: " << (text.empty() ? "<missing>" : text) << "\\n";
            out << "  boundary: read-only lookup/substitution; no DBF/CDX/LMDB mutation; no runtime writeback\\n";
            return;
        }

        out << "Usage: SET MESSAGE CATALOG CHECK\\n";
        out << "       SET MESSAGE CATALOG GET <symbol> [locale] [name=value ...]\\n";
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

def replace_between(text: str, begin: str, end: str, replacement: str) -> str:
    b = text.find(begin)
    e = text.find(end)
    if b < 0 or e < 0 or e < b:
        raise RuntimeError(f"marker block not found: {begin} ... {end}")
    e += len(end)
    return text[:b] + replacement + text[e:]

def ensure_include(text: str, include_line: str) -> tuple[str, bool]:
    if include_line in text:
        return text, False
    # Prefer standard include cluster if present.
    anchors = [
        "#include <vector>",
        "#include <string>",
        "#include <sstream>",
    ]
    for anchor in anchors:
        if anchor in text:
            return text.replace(anchor, anchor + "\n" + include_line, 1), True
    # Fallback near first include.
    if "#include " in text:
        idx = text.find("#include ")
        line_end = text.find("\n", idx)
        if line_end >= 0:
            return text[:line_end+1] + include_line + "\n" + text[line_end+1:], True
    raise RuntimeError("could not insert include <unordered_map>")

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--allow-source-mutation", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    reports = repo / REPORT_DIR
    reports.mkdir(parents=True, exist_ok=True)

    p22h = first_row(reports / "message_catalog_phase22h_runtime_status_summary_v1.csv")
    messages = p22h.get("MESSAGES", "12")
    text_rows = p22h.get("TEXT_ROWS", "60")
    locales = p22h.get("LOCALES", "de;en-US;es;fr;it")

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
    gate("PHASE22H_ACTIVE_EMISSION_GREEN",
         p22h.get("STATUS") == "MESSAGE_CATALOG_PHASE22H_SET_LANGUAGE_ACTIVE_MESSAGE_EMISSION_SMOKE_GREEN",
         p22h.get("STATUS", ""))
    gate("CMD_SET_CPP_PRESENT", cmd_set.exists(), rel(cmd_set, repo))
    gate("CMD_SET_HAS_MESSAGE_BRANCH_MARKERS",
         BRANCH_BEGIN in text and BRANCH_END in text,
         "MSG-022E message branch markers")
    gate("FORMAT_MESSAGE_CATALOG_CALL_PRESENT",
         "format_message_catalog(locale, symbol" in text,
         "Phase 22G lookup call")

    backup_rows: list[dict[str, Any]] = []
    mutation_rows: list[dict[str, Any]] = []
    patch_actions: list[dict[str, Any]] = []
    status = STATUS_BLOCKED

    if failures == 0:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        backup_root = repo / BACKUP_ROOT_BASE / f"MSG-022I_ARGUMENT_SUBSTITUTION_BACKUP_{timestamp}"
        backup(cmd_set, backup_root, repo, backup_rows)

        new_text = replace_between(text, BRANCH_BEGIN, BRANCH_END, BRANCH_REPLACEMENT)
        new_text, inserted_include = ensure_include(new_text, "#include <unordered_map>")
        if inserted_include:
            patch_actions.append({
                "TARGET_PATH": rel(cmd_set, repo),
                "ACTION": "INSERT_INCLUDE",
                "DETAIL": "#include <unordered_map>",
            })

        cmd_set.write_text(new_text, encoding="utf-8")

        patch_actions.append({
            "TARGET_PATH": rel(cmd_set, repo),
            "ACTION": "PATCH_SET_MESSAGE_CATALOG_GET",
            "DETAIL": "parse name=value arguments and pass vars to format_message_catalog",
        })

        mutation_rows.append({
            "TARGET_PATH": rel(cmd_set, repo),
            "ACTION": "UPDATE",
            "BYTES": cmd_set.stat().st_size,
            "SHA256": sha256_file(cmd_set),
            "DETAIL": "SET MESSAGE CATALOG GET now supports name=value argument substitution",
        })
        status = STATUS_GREEN

    validation_issues = "0" if status == STATUS_GREEN else str(failures)

    write_csv(reports / "message_catalog_phase22i_status_summary_v1.csv", [{
        "STATUS": status,
        "MESSAGES": messages,
        "TEXT_ROWS": text_rows,
        "LOCALES": locales,
        "VALIDATION_ISSUES": validation_issues,
        "SOURCE_MUTATION_AUTHORIZED": 1 if args.allow_source_mutation else 0,
        "SOURCE_FILES_MUTATED": len(mutation_rows),
        "SOURCE_BACKUP_ROWS": len(backup_rows),
        "ARGUMENT_SUBSTITUTION_APPLIED": 1 if status == STATUS_GREEN else 0,
        "BUILD_EXECUTED": 0,
        "RUNTIME_SMOKE_EXECUTED": 0,
        "NEXT_GATE": NEXT_GATE,
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }], ["STATUS", "MESSAGES", "TEXT_ROWS", "LOCALES", "VALIDATION_ISSUES",
         "SOURCE_MUTATION_AUTHORIZED", "SOURCE_FILES_MUTATED", "SOURCE_BACKUP_ROWS",
         "ARGUMENT_SUBSTITUTION_APPLIED", "BUILD_EXECUTED", "RUNTIME_SMOKE_EXECUTED",
         "NEXT_GATE", "REPORT_TIMESTAMP_UTC"])

    write_csv(reports / "message_catalog_phase22i_gate_check_v1.csv", gates, ["GATE", "STATUS", "DETAIL"])
    write_csv(reports / "message_catalog_phase22i_patch_actions_v1.csv", patch_actions, ["TARGET_PATH", "ACTION", "DETAIL"])
    write_csv(reports / "message_catalog_phase22i_source_mutation_inventory_v1.csv", mutation_rows,
              ["TARGET_PATH", "ACTION", "BYTES", "SHA256", "DETAIL"])
    write_csv(reports / "message_catalog_phase22i_source_backup_inventory_v1.csv", backup_rows,
              ["TARGET_PATH", "BACKUP_PATH", "BYTES", "SHA256", "ROLE"])

    boundary = [
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 1, "OBSERVED_MUTATION": len(mutation_rows), "DETAIL": "Authorized source mutation limited to src/cli/cmd_set.cpp SET MESSAGE CATALOG GET argument parsing."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_DBF_CATALOG", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Provider lookup/substitution reads active DBFs only; no active DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_CDX_INDEXES", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active CDX/index mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active LMDB mutation."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No HELP DATA mutation."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CMDHELPCHK mutation."},
        {"PROTECTED_SYSTEM": "MANUALGEN", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No manualgen mutation."},
        {"PROTECTED_SYSTEM": "DATADICT_SELF_DOC", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No Data Dictionary/SelfDoc mutation."},
    ]
    write_csv(reports / "message_catalog_phase22i_boundary_ledger_v1.csv", boundary,
              ["PROTECTED_SYSTEM", "MUTATION_ALLOWED", "OBSERVED_MUTATION", "DETAIL"])

    smoke = repo / "docs/messaging/scripts/MESSAGE_CATALOG_PHASE22I_ARGUMENT_SUBSTITUTION_SMOKE.dts"
    smoke.parent.mkdir(parents=True, exist_ok=True)
    smoke.write_text("\n".join([
        "* MESSAGE_CATALOG_PHASE22I_ARGUMENT_SUBSTITUTION_SMOKE.dts",
        "* Runtime-visible placeholder substitution proof.",
        "* Expected: {command} is replaced with USE in active-catalog text.",
        "SET MESSAGE CATALOG CHECK",
        "SET MESSAGE CATALOG GET HELP_HINT_COMMAND en-US command=USE",
        "SET MESSAGE CATALOG GET HELP_HINT_COMMAND es command=USE",
        "SET MESSAGE CATALOG GET HELP_HINT_COMMAND xx-XX command=USE",
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
