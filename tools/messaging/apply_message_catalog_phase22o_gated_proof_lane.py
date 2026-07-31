#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import shutil
from datetime import datetime, timezone
from pathlib import Path

STATUS_GREEN = "MESSAGE_CATALOG_PHASE22O_GATED_ROUTING_PROOF_LANE_PATCH_APPLIED"
STATUS_BLOCKED = "MESSAGE_CATALOG_PHASE22O_GATED_ROUTING_PROOF_LANE_PATCH_BLOCKED"
NEXT_GATE = "BUILD_AND_RUN_PHASE22O_GATED_ROUTING_PROOF_SMOKE_THEN_VALIDATE"
REPORT_DIR = Path("docs/messaging/reports")
BACKUP_ROOT_BASE = Path("docs/messaging/backups")

PROOF_BEGIN = "// MSG-022O BEGIN routing proof mode helper"
PROOF_END = "// MSG-022O END routing proof mode helper"
HELPER_BEGIN = "// MSG-022I-B BEGIN controlled message emit helper"

PROOF_HELPER_BLOCK = r'''
// MSG-022O BEGIN routing proof mode helper
static bool& message_routing_proof_enabled() {
    static bool enabled = false;
    return enabled;
}

static void print_message_proof_status() {
    auto& out = cli::OutputRouter::instance().out();
    out << "Message routing proof mode: "
        << (message_routing_proof_enabled() ? "on" : "off") << "\n";
    out << "boundary: proof mode changes runtime diagnostic state only; no DBF/CDX/LMDB mutation; no runtime writeback\n";
}

static void handle_set_message_proof(std::istringstream& args) {
    std::string mode;
    args >> mode;
    const std::string up = up_copy(mode);

    if (up == "ON") {
        message_routing_proof_enabled() = true;
        print_message_proof_status();
        return;
    }

    if (up == "OFF") {
        message_routing_proof_enabled() = false;
        print_message_proof_status();
        return;
    }

    if (up == "CHECK" || up == "STATUS" || up.empty()) {
        print_message_proof_status();
        return;
    }

    auto& out = cli::OutputRouter::instance().out();
    out << "Usage:\n";
    out << "  SET MESSAGE PROOF ON\n";
    out << "  SET MESSAGE PROOF OFF\n";
    out << "  SET MESSAGE PROOF CHECK\n";
}
// MSG-022O END routing proof mode helper
'''

OLD_PROOF_LINE = 'route_out << "Message routing proof: active_dbf MESSAGE_LOCALE_SET\\n";'
NEW_PROOF_LINE = '''if (message_routing_proof_enabled()) {
                route_out << "Message routing proof: active_dbf MESSAGE_LOCALE_SET\\n";
            }'''

EMIT_BRANCH = '''        if (sub1 == "EMIT") {
            handle_set_message_emit(args, S.message_locale);
            return;
        }'''

PROOF_BRANCH = '''        if (sub1 == "PROOF") {
            handle_set_message_proof(args);
            return;
        }

        if (sub1 == "EMIT") {
            handle_set_message_emit(args, S.message_locale);
            return;
        }'''

USAGE_ANCHOR = '    out << "  SET MESSAGE CATALOG CHECK\\n";'
USAGE_PROOF_LINE = '    out << "  SET MESSAGE PROOF ON|OFF|CHECK\\n";'

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
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in fields})

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    if not path.exists() or not path.is_file():
        return ""
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
    return text[:b] + replacement.strip("\n") + text[e + len(end):]

def insert_before(text: str, anchor: str, block: str):
    pos = text.find(anchor)
    if pos < 0:
        return None
    return text[:pos] + block.strip("\n") + "\n\n" + text[pos:]

def patch_cmd_set(text: str):
    actions = []

    required = [
        "Message routing proof: active_dbf MESSAGE_LOCALE_SET",
        "handle_set_message_emit(args, S.message_locale)",
        "SET MESSAGE EMIT",
        "MESSAGE_LOCALE_SET",
    ]
    for needle in required:
        if needle not in text:
            raise RuntimeError(f"required prior surface missing: {needle}")

    replaced = replace_between(text, PROOF_BEGIN, PROOF_END, PROOF_HELPER_BLOCK)
    if replaced is not None:
        text = replaced
        actions.append({
            "ACTION": "REPLACE_PROOF_HELPER",
            "DETAIL": "refreshed routing proof mode helper",
        })
    else:
        patched = insert_before(text, HELPER_BEGIN, PROOF_HELPER_BLOCK)
        if patched is None:
            raise RuntimeError("controlled message emit helper marker not found for proof helper insertion")
        text = patched
        actions.append({
            "ACTION": "INSERT_PROOF_HELPER",
            "DETAIL": "inserted routing proof mode helper before message emit helper",
        })

    if OLD_PROOF_LINE in text:
        text = text.replace(OLD_PROOF_LINE, NEW_PROOF_LINE, 1)
        actions.append({
            "ACTION": "GATE_ROUTING_PROOF_LINE",
            "DETAIL": "proof line now emits only when message_routing_proof_enabled() is true",
        })
    elif NEW_PROOF_LINE in text:
        actions.append({
            "ACTION": "ROUTING_PROOF_LINE_ALREADY_GATED",
            "DETAIL": "proof line already gated",
        })
    else:
        raise RuntimeError("routing proof output line anchor not found")

    if PROOF_BRANCH in text:
        actions.append({
            "ACTION": "PROOF_BRANCH_ALREADY_PRESENT",
            "DETAIL": "SET MESSAGE PROOF branch already present",
        })
    elif EMIT_BRANCH in text:
        text = text.replace(EMIT_BRANCH, PROOF_BRANCH, 1)
        actions.append({
            "ACTION": "INSERT_SET_MESSAGE_PROOF_BRANCH",
            "DETAIL": "added SET MESSAGE PROOF ON|OFF|CHECK branch",
        })
    else:
        raise RuntimeError("SET MESSAGE EMIT branch anchor not found for proof command insertion")

    if USAGE_PROOF_LINE in text:
        actions.append({
            "ACTION": "USAGE_ALREADY_PRESENT",
            "DETAIL": "SET MESSAGE PROOF usage already present",
        })
    elif USAGE_ANCHOR in text:
        text = text.replace(USAGE_ANCHOR, USAGE_ANCHOR + "\n" + USAGE_PROOF_LINE, 1)
        actions.append({
            "ACTION": "INSERT_USAGE_LINE",
            "DETAIL": "SET MESSAGE PROOF ON|OFF|CHECK",
        })
    else:
        actions.append({
            "ACTION": "USAGE_LINE_NOT_INSERTED",
            "DETAIL": "usage anchor not found; command branch still inserted",
        })

    return text, actions

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--allow-source-mutation", action="store_true")
    args = parser.parse_args()

    repo = Path(args.repo_root).resolve()
    reports = repo / REPORT_DIR
    reports.mkdir(parents=True, exist_ok=True)

    p22n = first_row(reports / "message_catalog_phase22n_status_summary_v1.csv")
    messages = p22n.get("MESSAGES", "12")
    text_rows = p22n.get("TEXT_ROWS", "60")
    locales = p22n.get("LOCALES", "de;en-US;es;fr;it")

    cmd_set = repo / "src/cli/cmd_set.cpp"

    gates = []
    failures = 0

    def gate(name: str, ok: bool, detail: str):
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": detail})
        if not ok:
            failures += 1

    gate("OPERATOR_AUTHORIZED_SOURCE_MUTATION", args.allow_source_mutation, "requires --allow-source-mutation")
    gate("PHASE22N_PROOF_LANE_PLAN_GREEN",
         p22n.get("STATUS") == "MESSAGE_CATALOG_PHASE22N_ROUTING_PROOF_LANE_GATING_PLAN_GREEN_SOURCE_HELD",
         p22n.get("STATUS", ""))
    gate("PROOF_LANE_DECISION_GATED",
         p22n.get("PROOF_LANE_DECISION") == "KEEP_TEMPORARY_GATED_LEARNING_TOOL",
         p22n.get("PROOF_LANE_DECISION", ""))
    gate("CMD_SET_CPP_PRESENT", cmd_set.exists(), rel(cmd_set, repo))

    backup_rows = []
    mutation_rows = []
    action_rows = []
    errors = []
    status = STATUS_BLOCKED

    if failures == 0:
        try:
            backup_root = repo / BACKUP_ROOT_BASE / f"MSG-022O_GATED_PROOF_LANE_BACKUP_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
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
                "DETAIL": "gated routing proof lane behind SET MESSAGE PROOF ON|OFF|CHECK",
            })
            status = STATUS_GREEN
        except Exception as exc:
            failures += 1
            errors.append(str(exc))
            gates.append({"GATE": "PATCH_CMD_SET_CPP", "STATUS": "FAIL", "DETAIL": str(exc)})

    validation_issues = "0" if status == STATUS_GREEN else str(failures)

    write_csv(reports / "message_catalog_phase22o_status_summary_v1.csv", [{
        "STATUS": status,
        "MESSAGES": messages,
        "TEXT_ROWS": text_rows,
        "LOCALES": locales,
        "VALIDATION_ISSUES": validation_issues,
        "SOURCE_MUTATION_AUTHORIZED": 1 if args.allow_source_mutation else 0,
        "SOURCE_FILES_MUTATED": len(mutation_rows),
        "SOURCE_BACKUP_ROWS": len(backup_rows),
        "PROOF_LANE_GATED": 1 if status == STATUS_GREEN else 0,
        "PROOF_COMMAND": "SET MESSAGE PROOF ON|OFF|CHECK",
        "BUILD_EXECUTED": 0,
        "RUNTIME_SMOKE_EXECUTED": 0,
        "ERRORS": "; ".join(errors),
        "NEXT_GATE": NEXT_GATE,
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }], ["STATUS", "MESSAGES", "TEXT_ROWS", "LOCALES", "VALIDATION_ISSUES",
         "SOURCE_MUTATION_AUTHORIZED", "SOURCE_FILES_MUTATED", "SOURCE_BACKUP_ROWS",
         "PROOF_LANE_GATED", "PROOF_COMMAND", "BUILD_EXECUTED",
         "RUNTIME_SMOKE_EXECUTED", "ERRORS", "NEXT_GATE", "REPORT_TIMESTAMP_UTC"])

    write_csv(reports / "message_catalog_phase22o_gate_check_v1.csv",
              gates,
              ["GATE", "STATUS", "DETAIL"])
    write_csv(reports / "message_catalog_phase22o_patch_actions_v1.csv",
              action_rows,
              ["TARGET_PATH", "ACTION", "DETAIL"])
    write_csv(reports / "message_catalog_phase22o_source_mutation_inventory_v1.csv",
              mutation_rows,
              ["TARGET_PATH", "ACTION", "BYTES", "SHA256", "DETAIL"])
    write_csv(reports / "message_catalog_phase22o_source_backup_inventory_v1.csv",
              backup_rows,
              ["TARGET_PATH", "BACKUP_PATH", "BYTES", "SHA256", "ROLE"])

    boundary = [
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 1, "OBSERVED_MUTATION": len(mutation_rows), "DETAIL": "Authorized source mutation limited to src/cli/cmd_set.cpp routing proof lane gating."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_DBF_CATALOG", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_CDX_INDEXES", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active CDX/index mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active LMDB mutation."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No HELP DATA mutation."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CMDHELPCHK mutation."},
        {"PROTECTED_SYSTEM": "MANUALGEN", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No manualgen mutation."},
        {"PROTECTED_SYSTEM": "DATADICT_SELF_DOC", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No Data Dictionary/SelfDoc mutation."},
    ]
    write_csv(reports / "message_catalog_phase22o_boundary_ledger_v1.csv",
              boundary,
              ["PROTECTED_SYSTEM", "MUTATION_ALLOWED", "OBSERVED_MUTATION", "DETAIL"])

    smoke = repo / "docs/messaging/scripts/MESSAGE_CATALOG_PHASE22O_GATED_ROUTING_PROOF_SMOKE.dts"
    smoke.parent.mkdir(parents=True, exist_ok=True)
    smoke.write_text("\n".join([
        "* MESSAGE_CATALOG_PHASE22O_GATED_ROUTING_PROOF_SMOKE.dts",
        "* Verify routing proof lane is explicitly gated.",
        "SET MESSAGE PROOF CHECK",
        "SET LANGUAGE es",
        "SET MESSAGE PROOF ON",
        "SET LANGUAGE es",
        "SET MESSAGE CATALOG CHECK",
        "SET MESSAGE PROOF OFF",
        "SET LANGUAGE es",
        "SET MESSAGE PROOF CHECK",
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
    print(f"  proof lane gated: {1 if status == STATUS_GREEN else 0}")
    print("  proof command: SET MESSAGE PROOF ON|OFF|CHECK")
    print("  build executed: 0")
    print("  runtime smoke executed: 0")
    print(f"  next gate: {NEXT_GATE}")
    print(f"  reports: {reports}")
    return 0 if status == STATUS_GREEN else 2

if __name__ == "__main__":
    raise SystemExit(main())
