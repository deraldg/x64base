#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import shutil
from datetime import datetime, timezone
from pathlib import Path

STATUS_GREEN = "MESSAGE_CATALOG_PHASE22K_CONTROLLED_PLACEHOLDER_SUBSTITUTION_PATCH_APPLIED"
STATUS_BLOCKED = "MESSAGE_CATALOG_PHASE22K_CONTROLLED_PLACEHOLDER_SUBSTITUTION_PATCH_BLOCKED"
NEXT_GATE = "BUILD_AND_RUN_PHASE22K_PLACEHOLDER_SUBSTITUTION_SMOKE_THEN_VALIDATE"
REPORT_DIR = Path("docs/messaging/reports")
BACKUP_ROOT_BASE = Path("docs/messaging/backups")

HELPER_BEGIN = "// MSG-022I-B BEGIN controlled message emit helper"
HELPER_END = "// MSG-022I-B END controlled message emit helper"

ENHANCED_HELPER_BLOCK = r'''
// MSG-022I-B BEGIN controlled message emit helper
static void print_message_emit_usage() {
    auto& out = cli::OutputRouter::instance().out();
    out << "Usage:\n";
    out << "  SET MESSAGE CATALOG CHECK\n";
    out << "  SET MESSAGE EMIT <symbol> [LOCALE <locale>] [ARG <name> <value>]\n";
}

static void message_replace_all(std::string& text, const std::string& needle, const std::string& value) {
    if (needle.empty()) {
        return;
    }

    std::string::size_type pos = 0;
    while ((pos = text.find(needle, pos)) != std::string::npos) {
        text.replace(pos, needle.size(), value);
        pos += value.size();
    }
}

static bool message_apply_single_placeholder_arg(std::string& text,
                                                 const std::string& arg_name,
                                                 const std::string& arg_value) {
    if (arg_name.empty()) {
        return false;
    }

    const std::string lower_token = "{" + arg_name + "}";
    std::string upper_name = arg_name;
    for (char& ch : upper_name) {
        ch = static_cast<char>(std::toupper(static_cast<unsigned char>(ch)));
    }
    const std::string upper_token = "{" + upper_name + "}";

    const bool had_lower = text.find(lower_token) != std::string::npos;
    const bool had_upper = text.find(upper_token) != std::string::npos;

    message_replace_all(text, lower_token, arg_value);
    message_replace_all(text, upper_token, arg_value);

    return had_lower || had_upper;
}

static void handle_set_message_emit(std::istringstream& args, const std::string& default_locale) {
    auto& out = cli::OutputRouter::instance().out();

    std::string symbol;
    args >> symbol;
    if (symbol.empty()) {
        print_message_emit_usage();
        return;
    }

    std::string locale = default_locale.empty()
        ? std::string("en-US")
        : default_locale;

    std::string arg_name;
    std::string arg_value;

    std::string tok;
    while (args >> tok) {
        const std::string up = up_copy(tok);
        if (up == "LOCALE" || up == "LANGUAGE" || up == "TO") {
            std::string value;
            args >> value;
            if (!value.empty()) {
                locale = value;
            }
            continue;
        }

        if (up == "ARG") {
            std::string name;
            std::string value;
            args >> name;
            args >> value;
            if (!name.empty() && !value.empty()) {
                arg_name = name;
                arg_value = value;
            }
            continue;
        }
    }

    const auto status = dottalk::helpdata::active_message_catalog_status();
    const std::string raw_text = dottalk::helpdata::format_message_catalog(locale, symbol);
    std::string text = raw_text;
    bool substituted = false;

    if (!arg_name.empty()) {
        substituted = message_apply_single_placeholder_arg(text, arg_name, arg_value);
    }

    out << "SET MESSAGE EMIT:\n";
    out << "  current locale: " << locale << "\n";
    out << "  provider mode: " << message_catalog_mode_name(status.mode) << "\n";
    out << "  active catalog present: " << (status.active_catalog_present ? "yes" : "no") << "\n";
    out << "  active catalog loaded: " << (status.active_catalog_loaded ? "yes" : "no") << "\n";
    out << "  message count: " << status.message_count << "\n";
    out << "  text row count: " << status.text_row_count << "\n";
    out << "  symbol: " << symbol << "\n";
    out << "  locale: " << locale << "\n";
    out << "  placeholder arg supplied: "
        << (arg_name.empty() ? "<none>" : (arg_name + "=" + arg_value)) << "\n";
    out << "  placeholder substitution proof: " << (substituted ? "yes" : "no") << "\n";
    out << "  text: " << (text.empty() ? "<empty>" : text) << "\n";
    out << "  runtime controlled emission proof: "
        << ((status.active_catalog_loaded && !text.empty()) ? "yes" : "no") << "\n";
    out << "  boundary: explicit diagnostic emission; no DBF/CDX/LMDB mutation; no runtime writeback\n";
}
// MSG-022I-B END controlled message emit helper
'''

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

def replace_between(text: str, begin: str, end: str, repl: str):
    b = text.find(begin)
    e = text.find(end)
    if b < 0 or e < 0 or e < b:
        return None
    return text[:b] + repl.strip() + text[e + len(end):]

def patch_cmd_set(text: str):
    actions = []

    required = [
        "SET MESSAGE EMIT",
        "handle_set_message_emit(args, S.message_locale)",
        "message_catalog_mode_name(",
        "format_message_catalog(locale, symbol)",
    ]
    for needle in required:
        if needle not in text:
            raise RuntimeError(f"required prior surface missing: {needle}")

    replaced = replace_between(text, HELPER_BEGIN, HELPER_END, ENHANCED_HELPER_BLOCK)
    if replaced is None:
        raise RuntimeError("controlled message emit helper marker not found")

    actions.append({
        "ACTION": "REPLACE_EMIT_HELPER",
        "DETAIL": "enhance SET MESSAGE EMIT with single ARG name value placeholder substitution",
    })

    return replaced, actions

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--allow-source-mutation", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    reports = repo / REPORT_DIR
    reports.mkdir(parents=True, exist_ok=True)

    p22j = first_row(reports / "message_catalog_phase22j_status_summary_v1.csv")
    messages = p22j.get("MESSAGES", "12")
    text_rows = p22j.get("TEXT_ROWS", "60")
    locales = p22j.get("LOCALES", "de;en-US;es;fr;it")

    cmd_set = repo / "src/cli/cmd_set.cpp"

    gates = []
    failures = 0

    def gate(name, ok, detail):
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": detail})
        if not ok:
            failures += 1

    gate("OPERATOR_AUTHORIZED_SOURCE_MUTATION", args.allow_source_mutation, "requires --allow-source-mutation")
    gate("PHASE22J_PLACEHOLDER_CONTRACT_GREEN",
         p22j.get("STATUS") == "MESSAGE_CATALOG_PHASE22J_PLACEHOLDER_ARGUMENT_CONTRACT_REVIEW_GREEN_SOURCE_HELD",
         p22j.get("STATUS", ""))
    gate("COMMAND_PLACEHOLDER_EVIDENCE_PRESENT",
         int(p22j.get("COMMAND_PLACEHOLDER_EVIDENCE_ROWS", "0") or "0") > 0,
         p22j.get("COMMAND_PLACEHOLDER_EVIDENCE_ROWS", ""))
    gate("CMD_SET_CPP_PRESENT", cmd_set.exists(), rel(cmd_set, repo))

    backup_rows = []
    mutation_rows = []
    action_rows = []
    errors = []
    status = STATUS_BLOCKED

    if failures == 0:
        try:
            backup_root = repo / BACKUP_ROOT_BASE / f"MSG-022K_PLACEHOLDER_SUBSTITUTION_BACKUP_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
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
                "DETAIL": "added controlled single ARG placeholder substitution for SET MESSAGE EMIT diagnostic path",
            })
            status = STATUS_GREEN
        except Exception as exc:
            failures += 1
            errors.append(str(exc))
            gates.append({"GATE": "PATCH_CMD_SET_CPP", "STATUS": "FAIL", "DETAIL": str(exc)})

    validation_issues = "0" if status == STATUS_GREEN else str(failures)

    write_csv(reports / "message_catalog_phase22k_status_summary_v1.csv", [{
        "STATUS": status,
        "MESSAGES": messages,
        "TEXT_ROWS": text_rows,
        "LOCALES": locales,
        "VALIDATION_ISSUES": validation_issues,
        "SOURCE_MUTATION_AUTHORIZED": 1 if args.allow_source_mutation else 0,
        "SOURCE_FILES_MUTATED": len(mutation_rows),
        "SOURCE_BACKUP_ROWS": len(backup_rows),
        "PLACEHOLDER_SUBSTITUTION_PATCH_APPLIED": 1 if status == STATUS_GREEN else 0,
        "BUILD_EXECUTED": 0,
        "RUNTIME_SMOKE_EXECUTED": 0,
        "ERRORS": "; ".join(errors),
        "NEXT_GATE": NEXT_GATE,
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }], ["STATUS", "MESSAGES", "TEXT_ROWS", "LOCALES", "VALIDATION_ISSUES",
         "SOURCE_MUTATION_AUTHORIZED", "SOURCE_FILES_MUTATED", "SOURCE_BACKUP_ROWS",
         "PLACEHOLDER_SUBSTITUTION_PATCH_APPLIED", "BUILD_EXECUTED", "RUNTIME_SMOKE_EXECUTED",
         "ERRORS", "NEXT_GATE", "REPORT_TIMESTAMP_UTC"])

    write_csv(reports / "message_catalog_phase22k_gate_check_v1.csv", gates,
              ["GATE", "STATUS", "DETAIL"])
    write_csv(reports / "message_catalog_phase22k_patch_actions_v1.csv", action_rows,
              ["TARGET_PATH", "ACTION", "DETAIL"])
    write_csv(reports / "message_catalog_phase22k_source_mutation_inventory_v1.csv", mutation_rows,
              ["TARGET_PATH", "ACTION", "BYTES", "SHA256", "DETAIL"])
    write_csv(reports / "message_catalog_phase22k_source_backup_inventory_v1.csv", backup_rows,
              ["TARGET_PATH", "BACKUP_PATH", "BYTES", "SHA256", "ROLE"])

    boundary = [
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 1, "OBSERVED_MUTATION": len(mutation_rows), "DETAIL": "Authorized source mutation limited to src/cli/cmd_set.cpp SET MESSAGE EMIT diagnostic placeholder substitution."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_DBF_CATALOG", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_CDX_INDEXES", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active CDX/index mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active LMDB mutation."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No HELP DATA mutation."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CMDHELPCHK mutation."},
        {"PROTECTED_SYSTEM": "MANUALGEN", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No manualgen mutation."},
        {"PROTECTED_SYSTEM": "DATADICT_SELF_DOC", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No Data Dictionary/SelfDoc mutation."},
    ]
    write_csv(reports / "message_catalog_phase22k_boundary_ledger_v1.csv", boundary,
              ["PROTECTED_SYSTEM", "MUTATION_ALLOWED", "OBSERVED_MUTATION", "DETAIL"])

    smoke = repo / "docs/messaging/scripts/MESSAGE_CATALOG_PHASE22K_PLACEHOLDER_SUBSTITUTION_SMOKE.dts"
    smoke.parent.mkdir(parents=True, exist_ok=True)
    smoke.write_text("\n".join([
        "* MESSAGE_CATALOG_PHASE22K_PLACEHOLDER_SUBSTITUTION_SMOKE.dts",
        "* Controlled placeholder substitution pilot for HELP_HINT_COMMAND.",
        "SET LANGUAGE es",
        "SET MESSAGE EMIT HELP_HINT_COMMAND ARG command HELP",
        "SET MESSAGE EMIT HELP_HINT_COMMAND LOCALE es ARG command HELP",
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
