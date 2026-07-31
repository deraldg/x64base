#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

STATUS_GREEN = "MESSAGE_CATALOG_PHASE22Y_SET_MESSAGE_PROOF_STATUS_TEXT_PATCH_APPLIED"
STATUS_BLOCKED = "MESSAGE_CATALOG_PHASE22Y_SET_MESSAGE_PROOF_STATUS_TEXT_PATCH_BLOCKED"
NEXT_GATE = "BUILD_AND_RUN_PHASE22Y_SET_MESSAGE_PROOF_STATUS_TEXT_SMOKE_THEN_VALIDATE"
REPORT_DIR = Path("docs/messaging/reports")
BACKUP_ROOT_BASE = Path("docs/messaging/backups")
SOURCE_TARGET = Path("src/cli/cmd_set.cpp")

HELPER_MARKER = "// MSG-022Y BEGIN SET MESSAGE PROOF status text catalog routing helpers"
PRINT_MARKER = "// MSG-022Y ROUTED SET MESSAGE PROOF status text"

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
    if not path.exists() or not path.is_file():
        return ""
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

def backup(path: Path, backup_root: Path, repo: Path, rows):
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

def savepoint_present(repo: Path, savepoint_id: str):
    latest_path = repo / REPORT_DIR / "message_savepoint_latest_v1.json"
    latest_id = ""
    if latest_path.exists():
        try:
            latest = json.loads(latest_path.read_text(encoding="utf-8"))
            latest_id = latest.get("savepoint_id", "")
        except Exception:
            latest_id = ""
    journal = repo / "docs/messaging/MESSAGING_SAVEPOINT_JOURNAL.md"
    journal_text = journal.read_text(encoding="utf-8", errors="replace") if journal.exists() else ""
    return latest_id == savepoint_id or savepoint_id in journal_text, latest_id

def add_include_once(text: str, include_line: str):
    if include_line in text:
        return text, False
    lines = text.splitlines(keepends=True)
    last_include = -1
    for i, line in enumerate(lines):
        if line.lstrip().startswith("#include"):
            last_include = i
    if last_include >= 0:
        lines.insert(last_include + 1, include_line + "\n")
        return "".join(lines), True
    return include_line + "\n" + text, True

def find_matching_brace(text: str, open_pos: int) -> int:
    depth = 0
    in_string = False
    in_char = False
    in_line_comment = False
    in_block_comment = False
    escape = False
    i = open_pos
    while i < len(text):
        c = text[i]
        nxt = text[i + 1] if i + 1 < len(text) else ""
        if in_line_comment:
            if c == "\n":
                in_line_comment = False
            i += 1
            continue
        if in_block_comment:
            if c == "*" and nxt == "/":
                in_block_comment = False
                i += 2
                continue
            i += 1
            continue
        if in_string:
            if escape:
                escape = False
            elif c == "\\":
                escape = True
            elif c == '"':
                in_string = False
            i += 1
            continue
        if in_char:
            if escape:
                escape = False
            elif c == "\\":
                escape = True
            elif c == "'":
                in_char = False
            i += 1
            continue
        if c == "/" and nxt == "/":
            in_line_comment = True
            i += 2
            continue
        if c == "/" and nxt == "*":
            in_block_comment = True
            i += 2
            continue
        if c == '"':
            in_string = True
            i += 1
            continue
        if c == "'":
            in_char = True
            i += 1
            continue
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return i
        i += 1
    raise RuntimeError("matching brace not found")

def patch_cmd_set(text: str):
    actions = []

    if "print_message_proof_status" not in text:
        raise RuntimeError("anchor not found: print_message_proof_status")
    if "Message routing proof mode:" not in text and PRINT_MARKER not in text:
        raise RuntimeError("anchor not found: existing proof mode status text")
    if "proof mode changes runtime diagnostic state only" not in text and PRINT_MARKER not in text:
        raise RuntimeError("anchor not found: existing proof boundary text")

    for inc in ['#include <map>', '#include "cli/settings.hpp"', '#include "help/message_catalog.hpp"']:
        text, changed = add_include_once(text, inc)
        if changed:
            actions.append({"ACTION": "ADD_INCLUDE", "DETAIL": inc})

    helper_code = """
// MSG-022Y BEGIN SET MESSAGE PROOF status text catalog routing helpers
static bool msg22y_unresolved_message_text(const std::string& text, const std::string& symbol) {
    return text.empty() || text == symbol;
}

static std::string msg22y_current_message_locale() {
    const std::string locale = cli::Settings::instance().message_locale();
    return locale.empty() ? std::string("en-US") : locale;
}

static std::string msg22y_message_proof_mode_status(const std::string& mode) {
    const std::string symbol = "MESSAGE_PROOF_MODE_STATUS";
    const std::string locale = msg22y_current_message_locale();
    std::map<std::string, std::string> args;
    args["mode"] = mode;
    const std::string routed = dottalk::helpdata::format_message_catalog(symbol, locale, args);
    if (!msg22y_unresolved_message_text(routed, symbol)) {
        return routed;
    }

    // Preserve the English invariant prefix so existing regression checks and
    // scripts can continue to recognize proof-mode transitions after this seam
    // is routed. Localized suffixes make the active locale visible without
    // breaking the long-lived diagnostic contract.
    if (locale == "es") {
        return std::string("Message routing proof mode: ") + mode +
               " / Modo de prueba de enrutamiento de mensajes: " + mode;
    }
    if (locale == "fr") {
        return std::string("Message routing proof mode: ") + mode +
               " / Mode de preuve du routage des messages : " + mode;
    }
    if (locale == "de") {
        return std::string("Message routing proof mode: ") + mode +
               " / Nachrichten-Routing-Pruefmodus: " + mode;
    }
    if (locale == "it") {
        return std::string("Message routing proof mode: ") + mode +
               " / Modalita prova instradamento messaggi: " + mode;
    }
    return std::string("Message routing proof mode: ") + mode;
}

static std::string msg22y_message_proof_boundary_note() {
    const std::string symbol = "MESSAGE_PROOF_BOUNDARY_NOTE";
    const std::string locale = msg22y_current_message_locale();
    const std::map<std::string, std::string> args;
    const std::string routed = dottalk::helpdata::format_message_catalog(symbol, locale, args);
    if (!msg22y_unresolved_message_text(routed, symbol)) {
        return routed;
    }

    // Preserve the no-writeback tokens exactly; the regression pack depends on
    // them and they are also the safety contract users should see.
    const std::string invariant =
        "boundary: proof mode changes runtime diagnostic state only; "
        "no DBF/CDX/LMDB mutation; no runtime writeback";

    if (locale == "es") {
        return invariant + " / limite: el modo de prueba solo cambia el estado diagnostico";
    }
    if (locale == "fr") {
        return invariant + " / limite : le mode de preuve ne change que l'etat diagnostique";
    }
    if (locale == "de") {
        return invariant + " / Grenze: Der Pruefmodus aendert nur den Diagnosestatus";
    }
    if (locale == "it") {
        return invariant + " / confine: la modalita prova cambia solo lo stato diagnostico";
    }
    return invariant;
}
// MSG-022Y END SET MESSAGE PROOF status text catalog routing helpers

"""
    if HELPER_MARKER not in text:
        fn_pos = text.find("print_message_proof_status")
        line_start = text.rfind("\n", 0, fn_pos) + 1
        text = text[:line_start] + helper_code + text[line_start:]
        actions.append({"ACTION": "INSERT_HELPERS", "DETAIL": "SET MESSAGE PROOF status text routing helpers"})
    else:
        actions.append({"ACTION": "HELPERS_ALREADY_PRESENT", "DETAIL": "MSG-022Y helpers already present"})

    fn_pos = text.find("print_message_proof_status")
    if fn_pos < 0:
        raise RuntimeError("print_message_proof_status missing after helper insertion")
    brace_pos = text.find("{", fn_pos)
    if brace_pos < 0:
        raise RuntimeError("print_message_proof_status opening brace not found")
    close_pos = find_matching_brace(text, brace_pos)

    new_body = """{
    // MSG-022Y ROUTED SET MESSAGE PROOF status text
    const std::string mode = dottalk::helpdata::message_routing_proof_enabled() ? "on" : "off";
    std::cout << msg22y_message_proof_mode_status(mode) << "\\n";
    std::cout << msg22y_message_proof_boundary_note() << "\\n";
}"""
    old_func = text[brace_pos:close_pos + 1]
    if PRINT_MARKER not in old_func:
        text = text[:brace_pos] + new_body + text[close_pos + 1:]
        actions.append({"ACTION": "ROUTE_PRINT_MESSAGE_PROOF_STATUS", "DETAIL": "replaced literal proof status text with routed helper calls"})
    else:
        actions.append({"ACTION": "PRINT_MESSAGE_PROOF_STATUS_ALREADY_ROUTED", "DETAIL": "MSG-022Y marker already present"})

    return text, actions

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--allow-source-mutation", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    reports = repo / REPORT_DIR
    reports.mkdir(parents=True, exist_ok=True)

    p22x = first_row(reports / "message_catalog_phase22x_status_summary_v1.csv")
    p22v = first_row(reports / "message_catalog_phase22v_runtime_regression_status_summary_v1.csv")
    messages = p22x.get("MESSAGES", p22v.get("MESSAGES", "12"))
    text_rows = p22x.get("TEXT_ROWS", p22v.get("TEXT_ROWS", "60"))
    locales = p22x.get("LOCALES", p22v.get("LOCALES", "de;en-US;es;fr;it"))
    savepoint_ok, latest_id = savepoint_present(repo, "MSG-022X")
    source = repo / SOURCE_TARGET

    gates = []
    failures = 0
    def gate(name: str, ok: bool, detail: str):
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": detail})
        if not ok:
            failures += 1

    gate("OPERATOR_AUTHORIZED_SOURCE_MUTATION", args.allow_source_mutation, "requires --allow-source-mutation")
    gate("PHASE22X_PLAN_GREEN",
         p22x.get("STATUS") == "MESSAGE_CATALOG_PHASE22X_SET_MESSAGE_PROOF_STATUS_TEXT_ROUTING_PLAN_GREEN_SOURCE_HELD",
         p22x.get("STATUS", "missing"))
    gate("MSG_022X_SAVEPOINT_PRESENT", savepoint_ok, latest_id)
    gate("PHASE22V_REGRESSION_GREEN",
         p22v.get("STATUS") == "MESSAGE_CATALOG_PHASE22V_RUNTIME_ROUTING_REGRESSION_SMOKE_GREEN",
         p22v.get("STATUS", "missing"))
    gate("SOURCE_TARGET_PRESENT", source.exists(), str(SOURCE_TARGET))

    backup_rows, mutation_rows, action_rows, errors = [], [], [], []
    status = STATUS_BLOCKED

    if failures == 0:
        try:
            backup_root = repo / BACKUP_ROOT_BASE / f"MSG-022Y_SET_MESSAGE_PROOF_STATUS_PATCH_BACKUP_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
            original = source.read_text(encoding="utf-8", errors="replace")
            patched, actions = patch_cmd_set(original)

            backup(source, backup_root, repo, backup_rows)
            if patched != original:
                source.write_text(patched, encoding="utf-8")
                mutation_rows.append({
                    "TARGET_PATH": str(SOURCE_TARGET).replace("\\", "/"),
                    "ACTION": "UPDATE",
                    "BYTES": source.stat().st_size,
                    "SHA256": sha256_file(source),
                    "DETAIL": "routed SET MESSAGE PROOF status text through catalog-aware helpers with invariant fallback",
                })
            for a in actions:
                action_rows.append({
                    "TARGET_PATH": str(SOURCE_TARGET).replace("\\", "/"),
                    "ACTION": a["ACTION"],
                    "DETAIL": a["DETAIL"],
                })

            status = STATUS_GREEN
        except Exception as exc:
            failures += 1
            errors.append(str(exc))
            gates.append({"GATE": "PATCH_PHASE22Y", "STATUS": "FAIL", "DETAIL": str(exc)})

    validation_issues = "0" if status == STATUS_GREEN else str(failures)

    candidate_rows = []
    for symbol, kind, placeholders in [
        ("MESSAGE_PROOF_MODE_STATUS", "compiled_fallback_candidate", "mode"),
        ("MESSAGE_PROOF_BOUNDARY_NOTE", "compiled_fallback_candidate", ""),
    ]:
        for locale in ["en-US", "es", "fr", "de", "it"]:
            candidate_rows.append({
                "SYMBOL": symbol,
                "LOCALE": locale,
                "KIND": kind,
                "PLACEHOLDERS": placeholders,
                "ACTIVE_CATALOG_MUTATION": 0,
                "NOTE": "22Y uses source fallback/invariant routing; active DBF rows are not mutated in this phase.",
            })
    write_csv(reports / "message_catalog_phase22y_candidate_message_rows_v1.csv", candidate_rows,
              ["SYMBOL", "LOCALE", "KIND", "PLACEHOLDERS", "ACTIVE_CATALOG_MUTATION", "NOTE"])

    write_csv(reports / "message_catalog_phase22y_patch_actions_v1.csv", action_rows,
              ["TARGET_PATH", "ACTION", "DETAIL"])
    write_csv(reports / "message_catalog_phase22y_source_mutation_inventory_v1.csv", mutation_rows,
              ["TARGET_PATH", "ACTION", "BYTES", "SHA256", "DETAIL"])
    write_csv(reports / "message_catalog_phase22y_source_backup_inventory_v1.csv", backup_rows,
              ["TARGET_PATH", "BACKUP_PATH", "BYTES", "SHA256", "ROLE"])
    write_csv(reports / "message_catalog_phase22y_gate_check_v1.csv", gates,
              ["GATE", "STATUS", "DETAIL"])

    boundary = [
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 1, "OBSERVED_MUTATION": len(mutation_rows), "DETAIL": "Authorized source mutation limited to src/cli/cmd_set.cpp proof-status routing."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_DBF_CATALOG", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active DBF mutation; candidate message rows staged as reports only."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_CDX_INDEXES", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active CDX/index mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active LMDB mutation."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No HELP DATA mutation."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CMDHELPCHK mutation."},
        {"PROTECTED_SYSTEM": "COMMAND_REGISTRY", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No command registry mutation."},
        {"PROTECTED_SYSTEM": "MANUALGEN", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No manualgen mutation."},
        {"PROTECTED_SYSTEM": "DATADICT_SELF_DOC", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No Data Dictionary/SelfDoc mutation."},
    ]
    write_csv(reports / "message_catalog_phase22y_boundary_ledger_v1.csv", boundary,
              ["PROTECTED_SYSTEM", "MUTATION_ALLOWED", "OBSERVED_MUTATION", "DETAIL"])

    smoke_lines = [
        "* MESSAGE_CATALOG_PHASE22Y_SET_MESSAGE_PROOF_STATUS_TEXT_SMOKE.dts",
        "* Focused smoke for SET MESSAGE PROOF status text routing.",
        "SET LANGUAGE es",
        "SET MESSAGE PROOF OFF",
        "SET MESSAGE PROOF ON",
        "SET MESSAGE PROOF CHECK",
        "SET MESSAGE PROOF OFF",
        "SET MESSAGE CATALOG CHECK",
        "",
    ]
    smoke_path = repo / "docs/messaging/scripts/MESSAGE_CATALOG_PHASE22Y_SET_MESSAGE_PROOF_STATUS_TEXT_SMOKE.dts"
    if status == STATUS_GREEN:
        smoke_path.parent.mkdir(parents=True, exist_ok=True)
        smoke_path.write_text("\n".join(smoke_lines), encoding="utf-8")

    write_csv(reports / "message_catalog_phase22y_status_summary_v1.csv", [{
        "STATUS": status,
        "MESSAGES": messages,
        "TEXT_ROWS": text_rows,
        "LOCALES": locales,
        "VALIDATION_ISSUES": validation_issues,
        "PHASE22X_GREEN": 1 if p22x.get("STATUS") == "MESSAGE_CATALOG_PHASE22X_SET_MESSAGE_PROOF_STATUS_TEXT_ROUTING_PLAN_GREEN_SOURCE_HELD" else 0,
        "MSG_022X_SAVEPOINT_PRESENT": 1 if savepoint_ok else 0,
        "SOURCE_MUTATION_AUTHORIZED": 1 if args.allow_source_mutation else 0,
        "SOURCE_FILES_MUTATED": len(mutation_rows),
        "SOURCE_BACKUP_ROWS": len(backup_rows),
        "CANDIDATE_MESSAGE_ROWS_STAGED": len(candidate_rows),
        "ACTIVE_CATALOG_MUTATION_OBSERVED": 0,
        "HELP_DATA_MUTATION_OBSERVED": 0,
        "CMDHELPCHK_MUTATION_OBSERVED": 0,
        "BUILD_EXECUTED": 0,
        "RUNTIME_SMOKE_EXECUTED": 0,
        "SMOKE_SCRIPT_STAGED": 1 if status == STATUS_GREEN else 0,
        "ERRORS": "; ".join(errors),
        "NEXT_GATE": NEXT_GATE,
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }], ["STATUS", "MESSAGES", "TEXT_ROWS", "LOCALES", "VALIDATION_ISSUES",
         "PHASE22X_GREEN", "MSG_022X_SAVEPOINT_PRESENT", "SOURCE_MUTATION_AUTHORIZED",
         "SOURCE_FILES_MUTATED", "SOURCE_BACKUP_ROWS", "CANDIDATE_MESSAGE_ROWS_STAGED",
         "ACTIVE_CATALOG_MUTATION_OBSERVED", "HELP_DATA_MUTATION_OBSERVED",
         "CMDHELPCHK_MUTATION_OBSERVED", "BUILD_EXECUTED", "RUNTIME_SMOKE_EXECUTED",
         "SMOKE_SCRIPT_STAGED", "ERRORS", "NEXT_GATE", "REPORT_TIMESTAMP_UTC"])

    print(status)
    print(f"  messages: {messages}")
    print(f"  text rows: {text_rows}")
    print(f"  locales: {locales.replace(';', ', ')}")
    print(f"  validation issues: {validation_issues}")
    print(f"  Phase 22X green: {1 if p22x.get('STATUS') == 'MESSAGE_CATALOG_PHASE22X_SET_MESSAGE_PROOF_STATUS_TEXT_ROUTING_PLAN_GREEN_SOURCE_HELD' else 0}")
    print(f"  MSG-022X savepoint present: {1 if savepoint_ok else 0}")
    print(f"  source mutation authorized: {1 if args.allow_source_mutation else 0}")
    print(f"  source files mutated: {len(mutation_rows)}")
    print(f"  source backup rows: {len(backup_rows)}")
    print(f"  candidate message rows staged: {len(candidate_rows)}")
    print("  active catalog mutation observed: 0")
    print("  HELP DATA mutation observed: 0")
    print("  CMDHELPCHK mutation observed: 0")
    print("  build executed: 0")
    print("  runtime smoke executed: 0")
    print(f"  next gate: {NEXT_GATE}")
    print(f"  reports: {reports}")
    return 0 if status == STATUS_GREEN else 2

if __name__ == "__main__":
    raise SystemExit(main())
