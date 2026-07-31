#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, hashlib, shutil
from datetime import datetime, timezone
from pathlib import Path

STATUS_GREEN = "MESSAGE_CATALOG_PHASE22G_SET_LANGUAGE_ACTIVE_CATALOG_LOOKUP_SOURCE_PATCH_APPLIED"
STATUS_BLOCKED = "MESSAGE_CATALOG_PHASE22G_SET_LANGUAGE_ACTIVE_CATALOG_LOOKUP_SOURCE_PATCH_BLOCKED"
NEXT_GATE = "BUILD_AND_RUN_SET_LANGUAGE_ACTIVE_LOOKUP_THEN_VALIDATE_PHASE22G"
REPORT_DIR = Path("docs/messaging/reports")
BACKUP_ROOT_BASE = Path("docs/messaging/backups")

HELPER_BEGIN = "// MSG-022G BEGIN SET LANGUAGE active catalog lookup helper"
HELPER_END = "// MSG-022G END SET LANGUAGE active catalog lookup helper"
BRANCH_BEGIN = "    // MSG-022G BEGIN SET LANGUAGE active catalog lookup"
BRANCH_END = "    // MSG-022G END SET LANGUAGE active catalog lookup"

HELPER_BLOCK = """
// MSG-022G BEGIN SET LANGUAGE active catalog lookup helper
static std::string& message_catalog_current_locale() {
    static std::string locale = "en-US";
    return locale;
}

static void print_message_catalog_language_check() {
    auto& out = cli::OutputRouter::instance().out();
    const auto status = dottalk::helpdata::active_message_catalog_status();
    const std::string locale = message_catalog_current_locale();
    const std::string sample = dottalk::helpdata::format_message_catalog(locale, "MESSAGE_LOCALE_SET");

    out << "SET LANGUAGE active catalog check:\\n";
    out << "  current language: " << locale << "\\n";
    out << "  message catalog mode: " << message_catalog_mode_name(status.mode) << "\\n";
    out << "  active catalog present: " << (status.active_catalog_present ? "yes" : "no") << "\\n";
    out << "  active catalog loaded: " << (status.active_catalog_loaded ? "yes" : "no") << "\\n";
    out << "  message count: " << status.message_count << "\\n";
    out << "  text row count: " << status.text_row_count << "\\n";
    out << "  lookup symbol: MESSAGE_LOCALE_SET\\n";
    out << "  lookup locale: " << locale << "\\n";
    out << "  lookup text: " << (sample.empty() ? "<empty>" : sample) << "\\n";
    out << "  runtime active catalog lookup proof: "
        << ((status.active_catalog_loaded && !sample.empty()) ? "yes" : "no") << "\\n";
    out << "  boundary: read-only lookup; no DBF/CDX/LMDB mutation; no runtime writeback\\n";
}

static void handle_set_language_or_locale(std::istringstream& args, const std::string& command_name) {
    auto& out = cli::OutputRouter::instance().out();

    std::string tok;
    args >> tok;
    tok = up_copy(tok);

    if (tok.empty()) {
        out << command_name << ": " << message_catalog_current_locale() << "\\n";
        return;
    }

    if (tok == "CHECK" || tok == "STATUS") {
        print_message_catalog_language_check();
        return;
    }

    std::string locale;
    if (tok == "TO") {
        args >> locale;
    } else {
        locale = tok;
    }

    if (locale.empty()) {
        out << "Usage: SET " << command_name << " <locale>|CHECK\\n";
        return;
    }

    message_catalog_current_locale() = locale;
    out << command_name << ": " << message_catalog_current_locale() << "\\n";
    print_message_catalog_language_check();
}
// MSG-022G END SET LANGUAGE active catalog lookup helper
"""

BRANCH_BLOCK = """
    // MSG-022G BEGIN SET LANGUAGE active catalog lookup
    if (opt == "LANGUAGE" || opt == "LOCALE") {
        handle_set_language_or_locale(args, opt);
        return;
    }
    // MSG-022G END SET LANGUAGE active catalog lookup

"""

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
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fields})

def sha256_file(path: Path):
    h = hashlib.sha256()
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
    rows.append({"TARGET_PATH": rel(path, repo), "BACKUP_PATH": rel(dst, repo), "BYTES": dst.stat().st_size, "SHA256": sha256_file(dst), "ROLE": "pre_patch_source_backup"})

def replace_between(text, begin, end, repl):
    b = text.find(begin)
    e = text.find(end)
    if b >= 0 and e >= b:
        return text[:b] + repl.strip() + text[e+len(end):]
    return None

def insert_before_first(text, needles, block, label):
    for needle in needles:
        pos = text.find(needle)
        if pos >= 0:
            return text[:pos] + block + text[pos:], f"inserted before {label}: {needle[:80]}"
    raise RuntimeError(f"cmd_set.cpp anchor not found for {label}")

def patch_cmd_set(text):
    actions = []
    new = text

    if '#include "help/message_catalog.hpp"' not in new:
        anchor = '#include "cli/table_state.hpp"'
        if anchor not in new:
            raise RuntimeError("include anchor not found")
        new = new.replace(anchor, anchor + '\n\n#include "help/message_catalog.hpp"', 1)
        actions.append({"ACTION":"INSERT_INCLUDE","DETAIL":"help/message_catalog.hpp"})
    else:
        actions.append({"ACTION":"INCLUDE_ALREADY_PRESENT","DETAIL":"help/message_catalog.hpp"})

    if "SET LANGUAGE <locale>|CHECK" not in new:
        line1 = '        << "  SET LANGUAGE <locale>|CHECK\\n"'
        line2 = '        << "  SET LOCALE <locale>|CHECK\\n"'
        anchor = '        << "  SET MESSAGE CATALOG CHECK\\n"'
        if anchor in new:
            new = new.replace(anchor, anchor + "\n" + line1 + "\n" + line2, 1)
            actions.append({"ACTION":"INSERT_USAGE_LINES","DETAIL":"SET LANGUAGE/LOCALE"})
        else:
            actions.append({"ACTION":"USAGE_LINES_NOT_INSERTED","DETAIL":"no SET MESSAGE usage anchor"})
    else:
        actions.append({"ACTION":"USAGE_ALREADY_PRESENT","DETAIL":"SET LANGUAGE/LOCALE"})

    if "message_catalog_mode_name(" not in new:
        raise RuntimeError("Phase 22F status helper missing message_catalog_mode_name")

    replaced = replace_between(new, HELPER_BEGIN, HELPER_END, HELPER_BLOCK)
    if replaced is None:
        new, detail = insert_before_first(new, ["static void print_set_usage() {"], HELPER_BLOCK + "\n", "SET LANGUAGE helper")
        actions.append({"ACTION":"INSERT_LANGUAGE_HELPER","DETAIL":detail})
    else:
        new = replaced
        actions.append({"ACTION":"REPLACE_LANGUAGE_HELPER","DETAIL":"refreshed MSG-022G helper"})

    replaced = replace_between(new, BRANCH_BEGIN, BRANCH_END, BRANCH_BLOCK)
    if replaced is None:
        new, detail = insert_before_first(new, ['    // MSG-022E BEGIN SET MESSAGE CATALOG CHECK', '    if (opt == "MESSAGE") {', '    if (opt == "TABLE") {'], BRANCH_BLOCK, "SET LANGUAGE branch")
        actions.append({"ACTION":"INSERT_LANGUAGE_BRANCH","DETAIL":detail})
    else:
        new = replaced
        actions.append({"ACTION":"REPLACE_LANGUAGE_BRANCH","DETAIL":"refreshed MSG-022G branch"})

    return new, actions

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--allow-source-mutation", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    reports = repo / REPORT_DIR
    reports.mkdir(parents=True, exist_ok=True)

    p22f = first_row(reports / "message_catalog_phase22f_runtime_status_summary_v1.csv")
    messages = p22f.get("MESSAGES", "12")
    text_rows = p22f.get("TEXT_ROWS", "60")
    locales = p22f.get("LOCALES", "de;en-US;es;fr;it")

    cmd_set = repo / "src/cli/cmd_set.cpp"
    gates = []
    failures = 0
    def gate(name, ok, detail):
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": detail})
        if not ok:
            failures += 1

    gate("OPERATOR_AUTHORIZED_SOURCE_MUTATION", args.allow_source_mutation, "requires --allow-source-mutation")
    gate("PHASE22F_ACTIVE_DBF_LOAD_GREEN", p22f.get("STATUS") == "MESSAGE_CATALOG_PHASE22F_ACTIVE_DBF_ROW_LOAD_PROVIDER_SMOKE_GREEN", p22f.get("STATUS", ""))
    gate("CMD_SET_CPP_PRESENT", cmd_set.exists(), rel(cmd_set, repo))
    gate("ACTIVE_MESSAGE_TEXT_DBF_PRESENT", (repo / "dottalkpp/data/messaging/SYSTEM_MESSAGE_TEXT.dbf").exists(), "dottalkpp/data/messaging/SYSTEM_MESSAGE_TEXT.dbf")

    backup_rows = []
    mutation_rows = []
    action_rows = []
    errors = []
    status = STATUS_BLOCKED
    if failures == 0:
        try:
            backup_root = repo / BACKUP_ROOT_BASE / f"MSG-022G_SET_LANGUAGE_LOOKUP_BACKUP_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
            backup(cmd_set, backup_root, repo, backup_rows)
            patched, actions = patch_cmd_set(cmd_set.read_text(encoding="utf-8", errors="replace"))
            cmd_set.write_text(patched, encoding="utf-8")
            for a in actions:
                action_rows.append({"TARGET_PATH": rel(cmd_set, repo), "ACTION": a["ACTION"], "DETAIL": a["DETAIL"]})
            mutation_rows.append({"TARGET_PATH": rel(cmd_set, repo), "ACTION": "UPDATE", "BYTES": cmd_set.stat().st_size, "SHA256": sha256_file(cmd_set), "DETAIL": "added SET LANGUAGE/SET LOCALE active catalog lookup smoke path"})
            status = STATUS_GREEN
        except Exception as exc:
            failures += 1
            errors.append(str(exc))
            gates.append({"GATE": "PATCH_CMD_SET_CPP", "STATUS": "FAIL", "DETAIL": str(exc)})

    validation = "0" if status == STATUS_GREEN else str(failures)
    write_csv(reports / "message_catalog_phase22g_status_summary_v1.csv", [{
        "STATUS": status, "MESSAGES": messages, "TEXT_ROWS": text_rows, "LOCALES": locales,
        "VALIDATION_ISSUES": validation, "SOURCE_MUTATION_AUTHORIZED": 1 if args.allow_source_mutation else 0,
        "SOURCE_FILES_MUTATED": len(mutation_rows), "SOURCE_BACKUP_ROWS": len(backup_rows),
        "SET_LANGUAGE_ACTIVE_LOOKUP_APPLIED": 1 if status == STATUS_GREEN else 0,
        "BUILD_EXECUTED": 0, "RUNTIME_SMOKE_EXECUTED": 0, "ERRORS": "; ".join(errors),
        "NEXT_GATE": NEXT_GATE, "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    }], ["STATUS","MESSAGES","TEXT_ROWS","LOCALES","VALIDATION_ISSUES","SOURCE_MUTATION_AUTHORIZED","SOURCE_FILES_MUTATED","SOURCE_BACKUP_ROWS","SET_LANGUAGE_ACTIVE_LOOKUP_APPLIED","BUILD_EXECUTED","RUNTIME_SMOKE_EXECUTED","ERRORS","NEXT_GATE","REPORT_TIMESTAMP_UTC"])
    write_csv(reports / "message_catalog_phase22g_gate_check_v1.csv", gates, ["GATE","STATUS","DETAIL"])
    write_csv(reports / "message_catalog_phase22g_patch_actions_v1.csv", action_rows, ["TARGET_PATH","ACTION","DETAIL"])
    write_csv(reports / "message_catalog_phase22g_source_mutation_inventory_v1.csv", mutation_rows, ["TARGET_PATH","ACTION","BYTES","SHA256","DETAIL"])
    write_csv(reports / "message_catalog_phase22g_source_backup_inventory_v1.csv", backup_rows, ["TARGET_PATH","BACKUP_PATH","BYTES","SHA256","ROLE"])

    boundary = [
        {"PROTECTED_SYSTEM":"SOURCE_CODE","MUTATION_ALLOWED":1,"OBSERVED_MUTATION":len(mutation_rows),"DETAIL":"Authorized source mutation limited to src/cli/cmd_set.cpp SET LANGUAGE/LOCALE lookup hook."},
        {"PROTECTED_SYSTEM":"ACTIVE_MESSAGING_DBF_CATALOG","MUTATION_ALLOWED":0,"OBSERVED_MUTATION":0,"DETAIL":"Provider read-only lookup; no active DBF mutation."},
        {"PROTECTED_SYSTEM":"ACTIVE_MESSAGING_CDX_INDEXES","MUTATION_ALLOWED":0,"OBSERVED_MUTATION":0,"DETAIL":"No active CDX/index mutation."},
        {"PROTECTED_SYSTEM":"ACTIVE_MESSAGING_LMDB","MUTATION_ALLOWED":0,"OBSERVED_MUTATION":0,"DETAIL":"No active LMDB mutation."},
        {"PROTECTED_SYSTEM":"HELP_DATA","MUTATION_ALLOWED":0,"OBSERVED_MUTATION":0,"DETAIL":"No HELP DATA mutation."},
        {"PROTECTED_SYSTEM":"CMDHELPCHK","MUTATION_ALLOWED":0,"OBSERVED_MUTATION":0,"DETAIL":"No CMDHELPCHK mutation."},
        {"PROTECTED_SYSTEM":"MANUALGEN","MUTATION_ALLOWED":0,"OBSERVED_MUTATION":0,"DETAIL":"No manualgen mutation."},
        {"PROTECTED_SYSTEM":"DATADICT_SELF_DOC","MUTATION_ALLOWED":0,"OBSERVED_MUTATION":0,"DETAIL":"No Data Dictionary/SelfDoc mutation."},
    ]
    write_csv(reports / "message_catalog_phase22g_boundary_ledger_v1.csv", boundary, ["PROTECTED_SYSTEM","MUTATION_ALLOWED","OBSERVED_MUTATION","DETAIL"])

    smoke = repo / "docs/messaging/scripts/MESSAGE_CATALOG_PHASE22G_SET_LANGUAGE_ACTIVE_LOOKUP_SMOKE.dts"
    smoke.parent.mkdir(parents=True, exist_ok=True)
    smoke.write_text("* MESSAGE_CATALOG_PHASE22G_SET_LANGUAGE_ACTIVE_LOOKUP_SMOKE.dts\nSET LANGUAGE es\nSET LANGUAGE CHECK\n\n", encoding="utf-8")

    print(status)
    print(f"  messages: {messages}")
    print(f"  text rows: {text_rows}")
    print(f"  locales: {locales.replace(';', ', ')}")
    print(f"  validation issues: {validation}")
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
