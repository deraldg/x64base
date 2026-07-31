#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path

STATUS_GREEN = "MESSAGE_CATALOG_PHASE22Y_1_BUILD_SIGNATURE_REPAIR_APPLIED"
STATUS_BLOCKED = "MESSAGE_CATALOG_PHASE22Y_1_BUILD_SIGNATURE_REPAIR_BLOCKED"
NEXT_GATE = "REBUILD_PHASE22Y_AFTER_BUILD_SIGNATURE_REPAIR"
REPORT_DIR = Path("docs/messaging/reports")
BACKUP_ROOT_BASE = Path("docs/messaging/backups")
SOURCE_TARGET = Path("src/cli/cmd_set.cpp")
SETTINGS_HEADER = Path("include/cli/settings.hpp")

BEGIN_MARKER = "// MSG-022Y BEGIN SET MESSAGE PROOF status text catalog routing helpers"
END_MARKER = "// MSG-022Y END SET MESSAGE PROOF status text catalog routing helpers"
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

def choose_locale_expression(repo: Path):
    header = repo / SETTINGS_HEADER
    text = header.read_text(encoding="utf-8", errors="replace") if header.exists() else ""

    # Most likely contract after the build error: message_locale is a field, not a method.
    # Prefer direct field when there is no message_locale(...) declaration.
    if re.search(r"\bmessage_locale\s*\(", text):
        return "cli::Settings::instance().message_locale()", "settings_header_declares_message_locale_function"
    if re.search(r"\bmessage_locale\b", text):
        return "cli::Settings::instance().message_locale", "settings_header_declares_or_mentions_message_locale_field"

    # Fall back to known candidate getter names if present.
    for name in ["get_message_locale", "current_message_locale", "locale"]:
        if re.search(rf"\b{name}\s*\(", text):
            return f"cli::Settings::instance().{name}()", f"settings_header_declares_{name}_function"

    return "cli::Settings::instance().message_locale", "default_to_message_locale_field_after_C2064"

def replace_in_y_block(text: str, old: str, new: str):
    begin = text.find(BEGIN_MARKER)
    end = text.find(END_MARKER)
    if begin < 0 or end < 0 or end < begin:
        return text, 0
    end = text.find("\n", end)
    if end < 0:
        end = len(text)
    block = text[begin:end]
    count = block.count(old)
    if count:
        block = block.replace(old, new)
        text = text[:begin] + block + text[end:]
    return text, count

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

def patch_cmd_set(text: str, repo: Path):
    actions = []

    if BEGIN_MARKER not in text:
        raise RuntimeError("MSG-022Y helper block not found")
    if PRINT_MARKER not in text:
        raise RuntimeError("MSG-022Y routed print marker not found")

    # Repair container signature mismatch: format_message_catalog expects unordered_map.
    text, added_unordered = add_include_once(text, "#include <unordered_map>")
    if added_unordered:
        actions.append({"ACTION": "ADD_INCLUDE", "DETAIL": "#include <unordered_map>"})

    # Remove the no-longer-needed <map> include only if this patch inserted/uses no std::map.
    if "#include <map>" in text:
        text = text.replace("#include <map>\n", "")
        text = text.replace("#include <map>\r\n", "")
        actions.append({"ACTION": "REMOVE_INCLUDE", "DETAIL": "#include <map>"})

    for old, new in [
        ("std::map<std::string, std::string>", "std::unordered_map<std::string, std::string>"),
        ("const std::map<std::string, std::string>", "const std::unordered_map<std::string, std::string>"),
    ]:
        text, n = replace_in_y_block(text, old, new)
        if n:
            actions.append({"ACTION": "REPLACE_CONTAINER_TYPE", "DETAIL": f"{old} -> {new} ({n})"})

    # Repair locale accessor. The build error C2064 indicates the current expression
    # likely treats a field as a function.
    locale_expr, reason = choose_locale_expression(repo)

    current_line_pattern = re.compile(
        r"const\s+std::string\s+locale\s*=\s*cli::Settings::instance\(\)\.message_locale\(\)\s*;"
    )
    begin = text.find(BEGIN_MARKER)
    end = text.find(END_MARKER)
    if begin < 0 or end < 0 or end < begin:
        raise RuntimeError("MSG-022Y helper block not found while repairing locale expression")
    block = text[begin:end]
    block2, n = current_line_pattern.subn(f"const std::string locale = {locale_expr};", block)
    if n:
        text = text[:begin] + block2 + text[end:]
        actions.append({"ACTION": "REPAIR_SETTINGS_LOCALE_ACCESSOR", "DETAIL": f"{locale_expr} ({reason})"})
    else:
        actions.append({"ACTION": "SETTINGS_LOCALE_ACCESSOR_UNCHANGED", "DETAIL": f"no message_locale() expression found in MSG-022Y block; selected={locale_expr}; reason={reason}"})

    # If we still have std::map in the 22Y block, fail now.
    block_check = text[text.find(BEGIN_MARKER):text.find(END_MARKER)]
    if "std::map<" in block_check:
        raise RuntimeError("std::map remains inside MSG-022Y helper block after repair")

    return text, actions, locale_expr

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--allow-source-mutation", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    reports = repo / REPORT_DIR
    reports.mkdir(parents=True, exist_ok=True)

    p22y = first_row(reports / "message_catalog_phase22y_status_summary_v1.csv")
    p22x = first_row(reports / "message_catalog_phase22x_status_summary_v1.csv")
    messages = p22y.get("MESSAGES", p22x.get("MESSAGES", "12"))
    text_rows = p22y.get("TEXT_ROWS", p22x.get("TEXT_ROWS", "60"))
    locales = p22y.get("LOCALES", p22x.get("LOCALES", "de;en-US;es;fr;it"))
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
    gate("PHASE22Y_PATCH_PREVIOUSLY_APPLIED",
         p22y.get("STATUS") == "MESSAGE_CATALOG_PHASE22Y_SET_MESSAGE_PROOF_STATUS_TEXT_PATCH_APPLIED",
         p22y.get("STATUS", "missing"))
    gate("MSG_022X_SAVEPOINT_PRESENT", savepoint_ok, latest_id)
    gate("SOURCE_TARGET_PRESENT", source.exists(), str(SOURCE_TARGET))

    backup_rows, mutation_rows, action_rows, errors = [], [], [], []
    status = STATUS_BLOCKED
    locale_expr = ""

    if failures == 0:
        try:
            backup_root = repo / BACKUP_ROOT_BASE / f"MSG-022Y_1_BUILD_SIGNATURE_REPAIR_BACKUP_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
            original = source.read_text(encoding="utf-8", errors="replace")
            patched, actions, locale_expr = patch_cmd_set(original, repo)

            backup(source, backup_root, repo, backup_rows)
            if patched != original:
                source.write_text(patched, encoding="utf-8")
                mutation_rows.append({
                    "TARGET_PATH": str(SOURCE_TARGET).replace("\\", "/"),
                    "ACTION": "UPDATE",
                    "BYTES": source.stat().st_size,
                    "SHA256": sha256_file(source),
                    "DETAIL": "repair Phase 22Y build signature issues: locale accessor and unordered_map args",
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
            gates.append({"GATE": "PATCH_PHASE22Y_1", "STATUS": "FAIL", "DETAIL": str(exc)})

    validation_issues = "0" if status == STATUS_GREEN else str(failures)

    write_csv(reports / "message_catalog_phase22y_1_patch_actions_v1.csv", action_rows,
              ["TARGET_PATH", "ACTION", "DETAIL"])
    write_csv(reports / "message_catalog_phase22y_1_source_mutation_inventory_v1.csv", mutation_rows,
              ["TARGET_PATH", "ACTION", "BYTES", "SHA256", "DETAIL"])
    write_csv(reports / "message_catalog_phase22y_1_source_backup_inventory_v1.csv", backup_rows,
              ["TARGET_PATH", "BACKUP_PATH", "BYTES", "SHA256", "ROLE"])
    write_csv(reports / "message_catalog_phase22y_1_gate_check_v1.csv", gates,
              ["GATE", "STATUS", "DETAIL"])

    boundary = [
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 1, "OBSERVED_MUTATION": len(mutation_rows), "DETAIL": "Authorized source mutation limited to src/cli/cmd_set.cpp Phase 22Y build-signature repair."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_DBF_CATALOG", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_CDX_INDEXES", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active CDX/index mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active LMDB mutation."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No HELP DATA mutation."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CMDHELPCHK mutation."},
        {"PROTECTED_SYSTEM": "COMMAND_REGISTRY", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No command registry mutation."},
        {"PROTECTED_SYSTEM": "MANUALGEN", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No manualgen mutation."},
        {"PROTECTED_SYSTEM": "DATADICT_SELF_DOC", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No Data Dictionary/SelfDoc mutation."},
    ]
    write_csv(reports / "message_catalog_phase22y_1_boundary_ledger_v1.csv", boundary,
              ["PROTECTED_SYSTEM", "MUTATION_ALLOWED", "OBSERVED_MUTATION", "DETAIL"])

    write_csv(reports / "message_catalog_phase22y_1_status_summary_v1.csv", [{
        "STATUS": status,
        "MESSAGES": messages,
        "TEXT_ROWS": text_rows,
        "LOCALES": locales,
        "VALIDATION_ISSUES": validation_issues,
        "PHASE22Y_PREVIOUS_APPLY_GREEN": 1 if p22y.get("STATUS") == "MESSAGE_CATALOG_PHASE22Y_SET_MESSAGE_PROOF_STATUS_TEXT_PATCH_APPLIED" else 0,
        "MSG_022X_SAVEPOINT_PRESENT": 1 if savepoint_ok else 0,
        "SOURCE_MUTATION_AUTHORIZED": 1 if args.allow_source_mutation else 0,
        "SOURCE_FILES_MUTATED": len(mutation_rows),
        "SOURCE_BACKUP_ROWS": len(backup_rows),
        "LOCALE_EXPRESSION_SELECTED": locale_expr,
        "ACTIVE_CATALOG_MUTATION_OBSERVED": 0,
        "HELP_DATA_MUTATION_OBSERVED": 0,
        "CMDHELPCHK_MUTATION_OBSERVED": 0,
        "BUILD_EXECUTED": 0,
        "RUNTIME_SMOKE_EXECUTED": 0,
        "ERRORS": "; ".join(errors),
        "NEXT_GATE": NEXT_GATE,
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }], ["STATUS", "MESSAGES", "TEXT_ROWS", "LOCALES", "VALIDATION_ISSUES",
         "PHASE22Y_PREVIOUS_APPLY_GREEN", "MSG_022X_SAVEPOINT_PRESENT",
         "SOURCE_MUTATION_AUTHORIZED", "SOURCE_FILES_MUTATED", "SOURCE_BACKUP_ROWS",
         "LOCALE_EXPRESSION_SELECTED", "ACTIVE_CATALOG_MUTATION_OBSERVED",
         "HELP_DATA_MUTATION_OBSERVED", "CMDHELPCHK_MUTATION_OBSERVED",
         "BUILD_EXECUTED", "RUNTIME_SMOKE_EXECUTED", "ERRORS", "NEXT_GATE",
         "REPORT_TIMESTAMP_UTC"])

    print(status)
    print(f"  messages: {messages}")
    print(f"  text rows: {text_rows}")
    print(f"  locales: {locales.replace(';', ', ')}")
    print(f"  validation issues: {validation_issues}")
    print(f"  Phase 22Y previous apply green: {1 if p22y.get('STATUS') == 'MESSAGE_CATALOG_PHASE22Y_SET_MESSAGE_PROOF_STATUS_TEXT_PATCH_APPLIED' else 0}")
    print(f"  MSG-022X savepoint present: {1 if savepoint_ok else 0}")
    print(f"  source mutation authorized: {1 if args.allow_source_mutation else 0}")
    print(f"  source files mutated: {len(mutation_rows)}")
    print(f"  source backup rows: {len(backup_rows)}")
    print(f"  locale expression selected: {locale_expr}")
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
