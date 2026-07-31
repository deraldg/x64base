#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import shutil
from datetime import datetime, timezone
from pathlib import Path

STATUS_GREEN = "MESSAGE_CATALOG_PHASE22S1_HELP_HINT_RUNTIME_ROUTING_PATCH_APPLIED"
STATUS_BLOCKED = "MESSAGE_CATALOG_PHASE22S1_HELP_HINT_RUNTIME_ROUTING_PATCH_BLOCKED"
NEXT_GATE = "BUILD_AND_RUN_PHASE22S1_HELP_HINT_ROUTING_SMOKE_THEN_VALIDATE"
REPORT_DIR = Path("docs/messaging/reports")
BACKUP_ROOT_BASE = Path("docs/messaging/backups")

HDR_BEGIN = "// MSG-022S1 BEGIN shared routing proof lane declarations"
HDR_END = "// MSG-022S1 END shared routing proof lane declarations"
HDR_BLOCK = '''
// MSG-022S1 BEGIN shared routing proof lane declarations
bool message_routing_proof_enabled();
void set_message_routing_proof_enabled(bool enabled);
// MSG-022S1 END shared routing proof lane declarations
'''

CPP_BEGIN = "// MSG-022S1 BEGIN shared routing proof lane state"
CPP_END = "// MSG-022S1 END shared routing proof lane state"
CPP_BLOCK = '''
// MSG-022S1 BEGIN shared routing proof lane state
namespace {
bool& message_routing_proof_flag()
{
    static bool enabled = false;
    return enabled;
}
} // namespace

bool message_routing_proof_enabled()
{
    return message_routing_proof_flag();
}

void set_message_routing_proof_enabled(bool enabled)
{
    message_routing_proof_flag() = enabled;
}
// MSG-022S1 END shared routing proof lane state
'''

CMD_SET_HELPER_BEGIN = "// MSG-022O BEGIN routing proof mode helper"
CMD_SET_HELPER_END = "// MSG-022O END routing proof mode helper"
CMD_SET_HELPER_BLOCK = '''
// MSG-022O BEGIN routing proof mode helper
static bool message_routing_proof_enabled() {
    return dottalk::helpdata::message_routing_proof_enabled();
}

static void set_message_routing_proof_enabled(bool enabled) {
    dottalk::helpdata::set_message_routing_proof_enabled(enabled);
}

static void print_message_proof_status() {
    auto& out = cli::OutputRouter::instance().out();
    out << "Message routing proof mode: "
        << (message_routing_proof_enabled() ? "on" : "off") << "\\n";
    out << "boundary: proof mode changes runtime diagnostic state only; no DBF/CDX/LMDB mutation; no runtime writeback\\n";
}

static void handle_set_message_proof(std::istringstream& args) {
    std::string mode;
    args >> mode;
    const std::string up = up_copy(mode);

    if (up == "ON") {
        set_message_routing_proof_enabled(true);
        print_message_proof_status();
        return;
    }

    if (up == "OFF") {
        set_message_routing_proof_enabled(false);
        print_message_proof_status();
        return;
    }

    if (up == "CHECK" || up == "STATUS" || up.empty()) {
        print_message_proof_status();
        return;
    }

    auto& out = cli::OutputRouter::instance().out();
    out << "Usage:\\n";
    out << "  SET MESSAGE PROOF ON\\n";
    out << "  SET MESSAGE PROOF OFF\\n";
    out << "  SET MESSAGE PROOF CHECK\\n";
}
// MSG-022O END routing proof mode helper
'''

HELP_HELPER_BEGIN = "// MSG-022S1 BEGIN HELP_HINT_COMMAND active provider helper"
HELP_HELPER_END = "// MSG-022S1 END HELP_HINT_COMMAND active provider helper"
HELP_HELPER_BLOCK = '''
// MSG-022S1 BEGIN HELP_HINT_COMMAND active provider helper
inline void help_apply_placeholder(std::string& text,
                                   const std::string& placeholder,
                                   const std::string& value)
{
    const std::string token1 = "{" + placeholder + "}";
    const std::string token2 = "{" + uptrim(placeholder) + "}";

    std::size_t pos = 0;
    while ((pos = text.find(token1, pos)) != std::string::npos) {
        text.replace(pos, token1.size(), value);
        pos += value.size();
    }

    pos = 0;
    while ((pos = text.find(token2, pos)) != std::string::npos) {
        text.replace(pos, token2.size(), value);
        pos += value.size();
    }
}

inline bool show_active_help_hint_command(const std::string& command_token)
{
    const auto status = dottalk::helpdata::active_message_catalog_status();
    if (!status.active_catalog_loaded) {
        return false;
    }

    const std::string locale = cli::Settings::instance().message_locale.empty()
        ? std::string("en-US")
        : cli::Settings::instance().message_locale;

    std::string text = dottalk::helpdata::format_message_catalog(locale, "HELP_HINT_COMMAND");
    if (text.empty()) {
        return false;
    }

    help_apply_placeholder(text, "command", command_token);
    out() << text << "\\n";

    if (dottalk::helpdata::message_routing_proof_enabled()) {
        out() << "Message routing proof: active_dbf HELP_HINT_COMMAND\\n";
    }

    return true;
}
// MSG-022S1 END HELP_HINT_COMMAND active provider helper
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
        w = csv.DictWriter(f, fieldnames=fields, lineterminator="\\n")
        w.writeheader()
        for row in rows:
            w.writerow({k: row.get(k, "") for k in fields})

def sha256_file(path: Path) -> str:
    if not path.exists() or not path.is_file():
        return ""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def rel(path: Path, repo: Path) -> str:
    try:
        return str(path.relative_to(repo)).replace("\\\\", "/")
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

def replace_between(text: str, begin: str, end: str, replacement: str):
    b = text.find(begin)
    e = text.find(end)
    if b < 0 or e < 0 or e < b:
        return None
    return text[:b] + replacement.strip("\\n") + text[e + len(end):]

def insert_before(text: str, anchor: str, block: str):
    pos = text.find(anchor)
    if pos < 0:
        return None
    return text[:pos] + block.strip("\\n") + "\\n\\n" + text[pos:]

def patch_header(text: str):
    actions = []
    if HDR_BEGIN in text and HDR_END in text:
        patched = replace_between(text, HDR_BEGIN, HDR_END, HDR_BLOCK)
        actions.append(("REFRESH_HEADER_DECLARATIONS", "shared routing proof declarations refreshed"))
        return patched, actions
    if "message_routing_proof_enabled()" in text and "set_message_routing_proof_enabled" in text:
        actions.append(("HEADER_DECLARATIONS_ALREADY_PRESENT", "shared routing proof declarations already present"))
        return text, actions
    for anchor in ["} // namespace dottalk::helpdata", "} // namespace dottalk::helpdata\\n"]:
        patched = insert_before(text, anchor, HDR_BLOCK)
        if patched is not None:
            actions.append(("INSERT_HEADER_DECLARATIONS", "inserted before namespace close"))
            return patched, actions
    raise RuntimeError("message_catalog.hpp namespace close anchor not found")

def patch_cpp(text: str):
    actions = []
    if CPP_BEGIN in text and CPP_END in text:
        patched = replace_between(text, CPP_BEGIN, CPP_END, CPP_BLOCK)
        actions.append(("REFRESH_CPP_PROOF_STATE", "shared routing proof definitions refreshed"))
        return patched, actions
    if "message_routing_proof_enabled()" in text and "set_message_routing_proof_enabled" in text:
        actions.append(("CPP_PROOF_STATE_ALREADY_PRESENT", "shared routing proof definitions already present"))
        return text, actions
    for anchor in ["} // namespace dottalk::helpdata", "} // namespace dottalk::helpdata\\n"]:
        patched = insert_before(text, anchor, CPP_BLOCK)
        if patched is not None:
            actions.append(("INSERT_CPP_PROOF_STATE", "inserted before namespace close"))
            return patched, actions
    patched = text.rstrip() + "\\n\\nnamespace dottalk::helpdata {\\n" + CPP_BLOCK.strip("\\n") + "\\n} // namespace dottalk::helpdata\\n"
    actions.append(("APPEND_CPP_PROOF_STATE_NAMESPACE", "appended shared routing proof state in namespace block"))
    return patched, actions

def patch_cmd_set(text: str):
    actions = []
    if CMD_SET_HELPER_BEGIN not in text or CMD_SET_HELPER_END not in text:
        raise RuntimeError("MSG-022O routing proof helper block not found in cmd_set.cpp")
    patched = replace_between(text, CMD_SET_HELPER_BEGIN, CMD_SET_HELPER_END, CMD_SET_HELPER_BLOCK)
    if patched is None:
        raise RuntimeError("could not replace MSG-022O routing proof helper")
    actions.append(("BRIDGE_CMD_SET_PROOF_HELPER", "cmd_set proof helper now uses shared message_catalog proof state"))
    return patched, actions

def patch_cmd_help(text: str):
    actions = []
    if "src/cli/cmd_help.cpp" not in text[:1000]:
        raise RuntimeError("cmd_help.cpp identity marker not found near top")
    if "show_fox(area, opts.term);" not in text:
        raise RuntimeError("legacy show_fox fallback anchor not found")
    if "if (show_fox_topic_local(opts.term)) return;" not in text:
        raise RuntimeError("show_fox_topic_local anchor not found")
    if "cli::Settings::instance().message_locale" in text and "HELP_HINT_COMMAND active provider helper" in text:
        actions.append(("CMD_HELP_ALREADY_PATCHED", "HELP_HINT_COMMAND helper already present"))
    else:
        if '#include "cli/settings.hpp"' not in text:
            text = text.replace('#include "cli/output_router.hpp"', '#include "cli/output_router.hpp"\\n#include "cli/settings.hpp"', 1)
            actions.append(("INSERT_CMD_HELP_SETTINGS_INCLUDE", "inserted cli/settings.hpp include"))
        if '#include "help/message_catalog.hpp"' not in text:
            text = text.replace('#include "help/reference_collection.hpp"', '#include "help/reference_collection.hpp"\\n#include "help/message_catalog.hpp"', 1)
            actions.append(("INSERT_CMD_HELP_MESSAGE_CATALOG_INCLUDE", "inserted help/message_catalog.hpp include"))
        helper_insert_anchor = "inline bool show_reflected_command_topic(const std::string& term_up)"
        patched = insert_before(text, helper_insert_anchor, HELP_HELPER_BLOCK)
        if patched is None:
            raise RuntimeError("cmd_help helper insertion anchor not found")
        text = patched
        actions.append(("INSERT_CMD_HELP_HELP_HINT_HELPER", "inserted HELP_HINT_COMMAND active provider helper"))

    legacy_anchor = '''            if (show_fox_topic_local(opts.term)) return;
            show_fox(area, opts.term);
            return;'''
    routed_block = '''            if (show_fox_topic_local(opts.term)) return;

            // MSG-022S1 BEGIN HELP_HINT_COMMAND active provider route
            if (show_active_help_hint_command(opts.term)) return;
            // MSG-022S1 END HELP_HINT_COMMAND active provider route

            show_fox(area, opts.term);
            return;'''
    if "MSG-022S1 BEGIN HELP_HINT_COMMAND active provider route" in text:
        actions.append(("CMD_HELP_ROUTE_ALREADY_PRESENT", "HELP_HINT_COMMAND route already present"))
    elif legacy_anchor in text:
        text = text.replace(legacy_anchor, routed_block, 1)
        actions.append(("INSERT_CMD_HELP_ROUTE", "inserted route before broad legacy show_fox fallback"))
    else:
        raise RuntimeError("cmd_help legacy fallback block shape not found")
    return text, actions

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--allow-source-mutation", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    reports = repo / REPORT_DIR
    reports.mkdir(parents=True, exist_ok=True)

    p22s0 = first_row(reports / "message_catalog_phase22s0_status_summary_v1.csv")
    messages = p22s0.get("MESSAGES", "12")
    text_rows = p22s0.get("TEXT_ROWS", "60")
    locales = p22s0.get("LOCALES", "de;en-US;es;fr;it")

    paths = {
        "cmd_help": repo / "src/cli/cmd_help.cpp",
        "cmd_set": repo / "src/cli/cmd_set.cpp",
        "msg_h": repo / "src/help/message_catalog.hpp",
        "msg_cpp": repo / "src/help/message_catalog.cpp",
    }

    gates = []
    failures = 0
    def gate(name, ok, detail):
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": detail})
        if not ok:
            failures += 1

    gate("OPERATOR_AUTHORIZED_SOURCE_MUTATION", args.allow_source_mutation, "requires --allow-source-mutation")
    gate("PHASE22S0_ANCHOR_PROBE_GREEN",
         p22s0.get("STATUS") == "MESSAGE_CATALOG_PHASE22S0_HELP_HINT_SOURCE_ANCHOR_PROBE_GREEN_PATCH_HELD",
         p22s0.get("STATUS", ""))
    gate("SELECTED_SYMBOL_HELP_HINT_COMMAND",
         p22s0.get("SELECTED_SYMBOL") == "HELP_HINT_COMMAND",
         p22s0.get("SELECTED_SYMBOL", ""))
    for key, path in paths.items():
        gate(f"{key.upper()}_PRESENT", path.exists(), rel(path, repo))

    backup_rows, mutation_rows, action_rows, errors = [], [], [], []
    status = STATUS_BLOCKED

    if failures == 0:
        try:
            backup_root = repo / BACKUP_ROOT_BASE / f"MSG-022S1_HELP_HINT_ROUTING_BACKUP_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
            for p in paths.values():
                backup(p, backup_root, repo, backup_rows)

            patchers = {
                "msg_h": patch_header,
                "msg_cpp": patch_cpp,
                "cmd_set": patch_cmd_set,
                "cmd_help": patch_cmd_help,
            }
            for key in ["msg_h", "msg_cpp", "cmd_set", "cmd_help"]:
                path = paths[key]
                original = path.read_text(encoding="utf-8", errors="replace")
                patched, actions = patchers[key](original)
                if patched != original:
                    path.write_text(patched, encoding="utf-8")
                    mutation_rows.append({
                        "TARGET_PATH": rel(path, repo),
                        "ACTION": "UPDATE",
                        "BYTES": path.stat().st_size,
                        "SHA256": sha256_file(path),
                        "DETAIL": f"Phase 22S1 patched {key}",
                    })
                for action, detail in actions:
                    action_rows.append({
                        "TARGET_PATH": rel(path, repo),
                        "ACTION": action,
                        "DETAIL": detail,
                    })
            status = STATUS_GREEN
        except Exception as exc:
            failures += 1
            errors.append(str(exc))
            gates.append({"GATE": "PATCH_PHASE22S1", "STATUS": "FAIL", "DETAIL": str(exc)})

    validation_issues = "0" if status == STATUS_GREEN else str(failures)

    write_csv(reports / "message_catalog_phase22s1_status_summary_v1.csv", [{
        "STATUS": status,
        "MESSAGES": messages,
        "TEXT_ROWS": text_rows,
        "LOCALES": locales,
        "VALIDATION_ISSUES": validation_issues,
        "SOURCE_MUTATION_AUTHORIZED": 1 if args.allow_source_mutation else 0,
        "SOURCE_FILES_MUTATED": len(mutation_rows),
        "SOURCE_BACKUP_ROWS": len(backup_rows),
        "ROUTED_SYMBOL": "HELP_HINT_COMMAND",
        "HELP_HINT_ROUTING_PATCH_APPLIED": 1 if status == STATUS_GREEN else 0,
        "SHARED_PROOF_STATE_BRIDGE_APPLIED": 1 if status == STATUS_GREEN else 0,
        "BUILD_EXECUTED": 0,
        "RUNTIME_SMOKE_EXECUTED": 0,
        "ERRORS": "; ".join(errors),
        "NEXT_GATE": NEXT_GATE,
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }], ["STATUS", "MESSAGES", "TEXT_ROWS", "LOCALES", "VALIDATION_ISSUES",
         "SOURCE_MUTATION_AUTHORIZED", "SOURCE_FILES_MUTATED", "SOURCE_BACKUP_ROWS",
         "ROUTED_SYMBOL", "HELP_HINT_ROUTING_PATCH_APPLIED", "SHARED_PROOF_STATE_BRIDGE_APPLIED",
         "BUILD_EXECUTED", "RUNTIME_SMOKE_EXECUTED", "ERRORS", "NEXT_GATE", "REPORT_TIMESTAMP_UTC"])

    write_csv(reports / "message_catalog_phase22s1_gate_check_v1.csv", gates, ["GATE", "STATUS", "DETAIL"])
    write_csv(reports / "message_catalog_phase22s1_patch_actions_v1.csv", action_rows, ["TARGET_PATH", "ACTION", "DETAIL"])
    write_csv(reports / "message_catalog_phase22s1_source_mutation_inventory_v1.csv", mutation_rows, ["TARGET_PATH", "ACTION", "BYTES", "SHA256", "DETAIL"])
    write_csv(reports / "message_catalog_phase22s1_source_backup_inventory_v1.csv", backup_rows, ["TARGET_PATH", "BACKUP_PATH", "BYTES", "SHA256", "ROLE"])

    boundary = [
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 1, "OBSERVED_MUTATION": len(mutation_rows), "DETAIL": "Authorized source mutation limited to Messaging proof bridge and narrow HELP_HINT_COMMAND route."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_DBF_CATALOG", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_CDX_INDEXES", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active CDX/index mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active LMDB mutation."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No HELP DATA rebuild or mutation."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CMDHELPCHK mutation."},
        {"PROTECTED_SYSTEM": "COMMAND_REGISTRY", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No command registry mutation."},
        {"PROTECTED_SYSTEM": "MANUALGEN", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No manualgen mutation."},
        {"PROTECTED_SYSTEM": "DATADICT_SELF_DOC", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No Data Dictionary/SelfDoc mutation."},
    ]
    write_csv(reports / "message_catalog_phase22s1_boundary_ledger_v1.csv", boundary, ["PROTECTED_SYSTEM", "MUTATION_ALLOWED", "OBSERVED_MUTATION", "DETAIL"])

    smoke = repo / "docs/messaging/scripts/MESSAGE_CATALOG_PHASE22S1_HELP_HINT_ROUTING_SMOKE.dts"
    smoke.parent.mkdir(parents=True, exist_ok=True)
    smoke.write_text("\\n".join([
        "* MESSAGE_CATALOG_PHASE22S1_HELP_HINT_ROUTING_SMOKE.dts",
        "* Verify HELP_HINT_COMMAND routes through active provider and proof lane is shared/gated.",
        "SET LANGUAGE es",
        "SET MESSAGE PROOF OFF",
        "HELP __MSG22S1_UNKNOWN__",
        "SET MESSAGE PROOF ON",
        "HELP __MSG22S1_UNKNOWN__",
        "SET MESSAGE CATALOG CHECK",
        "SET MESSAGE PROOF OFF",
        "HELP __MSG22S1_UNKNOWN__",
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
    print("  routed symbol: HELP_HINT_COMMAND")
    print(f"  shared proof state bridge applied: {1 if status == STATUS_GREEN else 0}")
    print("  build executed: 0")
    print("  runtime smoke executed: 0")
    print(f"  next gate: {NEXT_GATE}")
    print(f"  reports: {reports}")
    return 0 if status == STATUS_GREEN else 2

if __name__ == "__main__":
    raise SystemExit(main())
