#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import shutil
from datetime import datetime, timezone
from pathlib import Path

STATUS_GREEN = "MESSAGE_CATALOG_PHASE22S1_2_HELP_HINT_ROUTE_RELOCATION_APPLIED"
STATUS_BLOCKED = "MESSAGE_CATALOG_PHASE22S1_2_HELP_HINT_ROUTE_RELOCATION_BLOCKED"
NEXT_GATE = "BUILD_AND_RUN_PHASE22S1_HELP_HINT_ROUTING_SMOKE_THEN_VALIDATE"
REPORT_DIR = Path("docs/messaging/reports")
BACKUP_ROOT_BASE = Path("docs/messaging/backups")

ROUTE_BEGIN = "// MSG-022S1 BEGIN HELP_HINT_COMMAND active provider route"
ROUTE_END = "// MSG-022S1 END HELP_HINT_COMMAND active provider route"
ROUTE_BEGIN_11 = "// MSG-022S1_1 BEGIN HELP_HINT_COMMAND active provider route before fox local fallback"
ROUTE_END_11 = "// MSG-022S1_1 END HELP_HINT_COMMAND active provider route before fox local fallback"

FOX_LOCAL_LINE = "if (show_fox_topic_local(opts.term)) return;"

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

def line_offsets(text: str):
    offsets = []
    pos = 0
    for line in text.splitlines(keepends=True):
        offsets.append((pos, pos + len(line), line))
        pos += len(line)
    if not offsets and text:
        offsets.append((0, len(text), text))
    return offsets

def find_marker_line_range(lines, begin_marker: str, end_marker: str):
    begin_i = end_i = None
    for i, (_, _, line) in enumerate(lines):
        if begin_marker in line:
            begin_i = i
            break
    if begin_i is None:
        return None
    for j in range(begin_i, len(lines)):
        if end_marker in lines[j][2]:
            end_i = j
            break
    if end_i is None:
        return None

    # Include a following blank line if present so relocation does not leave double gaps.
    last_i = end_i
    if end_i + 1 < len(lines) and lines[end_i + 1][2].strip() == "":
        last_i = end_i + 1
    return begin_i, last_i

def find_fox_local_index(lines):
    hits = [i for i, (_, _, line) in enumerate(lines) if FOX_LOCAL_LINE in line]
    if not hits:
        return None
    # Prefer the hit near the HELP_HINT route if possible. There is usually one.
    return hits[0]

def normalize_route_block(block: str, indent: str):
    # Preserve the already-inserted call line but upgrade markers to the S1.2 form.
    return (
        f"{indent}// MSG-022S1_2 BEGIN HELP_HINT_COMMAND active provider route before fox local fallback\n"
        f"{indent}if (show_active_help_hint_command(opts.term)) return;\n"
        f"{indent}// MSG-022S1_2 END HELP_HINT_COMMAND active provider route before fox local fallback\n\n"
    )

def patch_cmd_help(text: str):
    if "show_active_help_hint_command" not in text:
        raise RuntimeError("S1 helper not found: show_active_help_hint_command")
    if FOX_LOCAL_LINE not in text:
        raise RuntimeError("fox local fallback anchor not found: show_fox_topic_local(opts.term)")
    if "show_fox(area, opts.term);" not in text:
        raise RuntimeError("broad show_fox fallback anchor not found")

    lines = line_offsets(text)

    # Accept original S1, S1.1, or already-S1.2 markers.
    route_range = (
        find_marker_line_range(lines, ROUTE_BEGIN, ROUTE_END)
        or find_marker_line_range(lines, ROUTE_BEGIN_11, ROUTE_END_11)
        or find_marker_line_range(lines,
                                  "// MSG-022S1_2 BEGIN HELP_HINT_COMMAND active provider route before fox local fallback",
                                  "// MSG-022S1_2 END HELP_HINT_COMMAND active provider route before fox local fallback")
    )
    if route_range is None:
        raise RuntimeError("HELP_HINT_COMMAND route marker block not found")

    fox_i = find_fox_local_index(lines)
    if fox_i is None:
        raise RuntimeError("show_fox_topic_local anchor line not found")

    begin_i, end_i = route_range
    route_start = lines[begin_i][0]
    route_end = lines[end_i][1]
    fox_start = lines[fox_i][0]
    fox_line = lines[fox_i][2]
    indent = fox_line[:len(fox_line) - len(fox_line.lstrip())]

    new_route = normalize_route_block(text[route_start:route_end], indent)

    # Already before fox local: refresh markers only.
    if route_start < fox_start:
        patched = text[:route_start] + new_route + text[route_end:]
        return patched, [{"ACTION": "ROUTE_ALREADY_BEFORE_FOX_LOCAL_REFRESHED", "DETAIL": "HELP_HINT_COMMAND route already before show_fox_topic_local; markers refreshed"}]

    # Remove old route block, then recompute insertion point before fox local in the shortened text.
    without = text[:route_start] + text[route_end:]
    fox_pos = without.find(FOX_LOCAL_LINE)
    if fox_pos < 0:
        raise RuntimeError("show_fox_topic_local anchor missing after route removal")

    # Insert at beginning of the fox-local line.
    line_begin = without.rfind("\n", 0, fox_pos) + 1
    patched = without[:line_begin] + new_route + without[line_begin:]
    return patched, [{"ACTION": "RELOCATE_HELP_HINT_ROUTE", "DETAIL": "moved HELP_HINT_COMMAND route before show_fox_topic_local fallback using marker-based relocation"}]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--allow-source-mutation", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    reports = repo / REPORT_DIR
    reports.mkdir(parents=True, exist_ok=True)

    p22s1 = first_row(reports / "message_catalog_phase22s1_status_summary_v1.csv")
    messages = p22s1.get("MESSAGES", "12")
    text_rows = p22s1.get("TEXT_ROWS", "60")
    locales = p22s1.get("LOCALES", "de;en-US;es;fr;it")

    cmd_help = repo / "src/cli/cmd_help.cpp"
    smoke = repo / "docs/messaging/scripts/MESSAGE_CATALOG_PHASE22S1_HELP_HINT_ROUTING_SMOKE.dts"

    gates = []
    failures = 0
    def gate(name, ok, detail):
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": detail})
        if not ok:
            failures += 1

    gate("OPERATOR_AUTHORIZED_SOURCE_MUTATION", args.allow_source_mutation, "requires --allow-source-mutation")
    gate("PHASE22S1_PATCH_APPLIED", p22s1.get("STATUS") == "MESSAGE_CATALOG_PHASE22S1_HELP_HINT_RUNTIME_ROUTING_PATCH_APPLIED", p22s1.get("STATUS", ""))
    gate("CMD_HELP_PRESENT", cmd_help.exists(), rel(cmd_help, repo))

    # It is OK if S1.1 was blocked; require it only did not mutate.
    p22s11 = first_row(reports / "message_catalog_phase22s1_1_status_summary_v1.csv")
    if p22s11:
        gate("PHASE22S1_1_PRIOR_MUTATED_ZERO_OR_ABSENT", p22s11.get("SOURCE_FILES_MUTATED", "0") in ["", "0"], p22s11.get("SOURCE_FILES_MUTATED", ""))

    backup_rows, mutation_rows, action_rows, errors = [], [], [], []
    status = STATUS_BLOCKED

    if failures == 0:
        try:
            backup_root = repo / BACKUP_ROOT_BASE / f"MSG-022S1_2_HELP_HINT_ROUTE_RELOCATION_BACKUP_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
            backup(cmd_help, backup_root, repo, backup_rows)
            original = cmd_help.read_text(encoding="utf-8", errors="replace")
            patched, actions = patch_cmd_help(original)
            if patched != original:
                cmd_help.write_text(patched, encoding="utf-8")
                mutation_rows.append({
                    "TARGET_PATH": rel(cmd_help, repo),
                    "ACTION": "UPDATE",
                    "BYTES": cmd_help.stat().st_size,
                    "SHA256": sha256_file(cmd_help),
                    "DETAIL": "relocated HELP_HINT_COMMAND route before show_fox_topic_local fallback using marker-based repair",
                })
            for a in actions:
                action_rows.append({"TARGET_PATH": rel(cmd_help, repo), "ACTION": a["ACTION"], "DETAIL": a["DETAIL"]})

            smoke.parent.mkdir(parents=True, exist_ok=True)
            smoke.write_text("\n".join([
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

            status = STATUS_GREEN
        except Exception as exc:
            failures += 1
            errors.append(str(exc))
            gates.append({"GATE": "PATCH_PHASE22S1_2", "STATUS": "FAIL", "DETAIL": str(exc)})

    validation_issues = "0" if status == STATUS_GREEN else str(failures)

    write_csv(reports / "message_catalog_phase22s1_2_status_summary_v1.csv", [{
        "STATUS": status,
        "MESSAGES": messages,
        "TEXT_ROWS": text_rows,
        "LOCALES": locales,
        "VALIDATION_ISSUES": validation_issues,
        "SOURCE_MUTATION_AUTHORIZED": 1 if args.allow_source_mutation else 0,
        "SOURCE_FILES_MUTATED": len(mutation_rows),
        "SOURCE_BACKUP_ROWS": len(backup_rows),
        "ROUTED_SYMBOL": "HELP_HINT_COMMAND",
        "ROUTE_RELOCATED_BEFORE_FOX_LOCAL": 1 if status == STATUS_GREEN else 0,
        "SMOKE_SCRIPT_REWRITTEN": 1 if status == STATUS_GREEN else 0,
        "BUILD_EXECUTED": 0,
        "RUNTIME_SMOKE_EXECUTED": 0,
        "ERRORS": "; ".join(errors),
        "NEXT_GATE": NEXT_GATE,
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }], ["STATUS", "MESSAGES", "TEXT_ROWS", "LOCALES", "VALIDATION_ISSUES",
         "SOURCE_MUTATION_AUTHORIZED", "SOURCE_FILES_MUTATED", "SOURCE_BACKUP_ROWS",
         "ROUTED_SYMBOL", "ROUTE_RELOCATED_BEFORE_FOX_LOCAL", "SMOKE_SCRIPT_REWRITTEN",
         "BUILD_EXECUTED", "RUNTIME_SMOKE_EXECUTED", "ERRORS", "NEXT_GATE", "REPORT_TIMESTAMP_UTC"])
    write_csv(reports / "message_catalog_phase22s1_2_gate_check_v1.csv", gates, ["GATE", "STATUS", "DETAIL"])
    write_csv(reports / "message_catalog_phase22s1_2_patch_actions_v1.csv", action_rows, ["TARGET_PATH", "ACTION", "DETAIL"])
    write_csv(reports / "message_catalog_phase22s1_2_source_mutation_inventory_v1.csv", mutation_rows, ["TARGET_PATH", "ACTION", "BYTES", "SHA256", "DETAIL"])
    write_csv(reports / "message_catalog_phase22s1_2_source_backup_inventory_v1.csv", backup_rows, ["TARGET_PATH", "BACKUP_PATH", "BYTES", "SHA256", "ROLE"])

    boundary = [
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 1, "OBSERVED_MUTATION": len(mutation_rows), "DETAIL": "Authorized source mutation limited to cmd_help.cpp HELP_HINT_COMMAND route relocation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_DBF_CATALOG", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_CDX_INDEXES", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active CDX/index mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active LMDB mutation."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No HELP DATA rebuild or mutation."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CMDHELPCHK mutation."},
        {"PROTECTED_SYSTEM": "COMMAND_REGISTRY", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No command registry mutation."},
        {"PROTECTED_SYSTEM": "MANUALGEN", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No manualgen mutation."},
        {"PROTECTED_SYSTEM": "DATADICT_SELF_DOC", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No Data Dictionary/SelfDoc mutation."},
    ]
    write_csv(reports / "message_catalog_phase22s1_2_boundary_ledger_v1.csv", boundary, ["PROTECTED_SYSTEM", "MUTATION_ALLOWED", "OBSERVED_MUTATION", "DETAIL"])

    print(status)
    print(f"  messages: {messages}")
    print(f"  text rows: {text_rows}")
    print(f"  locales: {locales.replace(';', ', ')}")
    print(f"  validation issues: {validation_issues}")
    print(f"  source mutation authorized: {1 if args.allow_source_mutation else 0}")
    print(f"  source files mutated: {len(mutation_rows)}")
    print(f"  source backup rows: {len(backup_rows)}")
    print("  routed symbol: HELP_HINT_COMMAND")
    print(f"  route relocated before fox local: {1 if status == STATUS_GREEN else 0}")
    print(f"  smoke script rewritten: {1 if status == STATUS_GREEN else 0}")
    print("  build executed: 0")
    print("  runtime smoke executed: 0")
    print(f"  next gate: {NEXT_GATE}")
    print(f"  reports: {reports}")
    return 0 if status == STATUS_GREEN else 2

if __name__ == "__main__":
    raise SystemExit(main())
