#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import shutil
from datetime import datetime, timezone
from pathlib import Path

STATUS_GREEN = "MESSAGE_CATALOG_PHASE22S1_4_BUILD_SYNTAX_LITERAL_NEWLINE_REPAIR_APPLIED"
STATUS_BLOCKED = "MESSAGE_CATALOG_PHASE22S1_4_BUILD_SYNTAX_LITERAL_NEWLINE_REPAIR_BLOCKED"
NEXT_GATE = "REBUILD_PHASE22S1_AFTER_LITERAL_NEWLINE_REPAIR"
REPORT_DIR = Path("docs/messaging/reports")
BACKUP_ROOT_BASE = Path("docs/messaging/backups")

TARGETS = [
    "src/cli/cmd_help.cpp",
    "src/help/message_catalog.hpp",
    "src/help/message_catalog.cpp",
    "src/cli/cmd_set.cpp",
]

# Only replace escaped-newline artifacts that are outside normal output strings.
# Do not globally replace "\n", because valid C++ string literals intentionally use it.
TARGETED_REPLACEMENTS = [
    ("\\n#include", "\n#include", "literal newline before include"),
    ("\\n// MSG-", "\n// MSG-", "literal newline before MSG marker"),
    ("\\ninline ", "\ninline ", "literal newline before inline"),
    ("\\nbool ", "\nbool ", "literal newline before bool declaration"),
    ("\\nvoid ", "\nvoid ", "literal newline before void declaration"),
    ("\\nnamespace ", "\nnamespace ", "literal newline before namespace"),
    ("\\n} // namespace", "\n} // namespace", "literal newline before namespace close"),
    ("\\n};", "\n};", "literal newline before brace-semicolon"),
]

BAD_PATTERNS = [
    "\\n#include",
    "\\n// MSG-",
    "\\ninline ",
    "\\nbool ",
    "\\nvoid ",
    "\\nnamespace ",
    "\\n} // namespace",
    "\\n};",
]

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

def repair_text(text: str):
    actions = []
    repaired = text
    for old, new, label in TARGETED_REPLACEMENTS:
        count = repaired.count(old)
        if count:
            repaired = repaired.replace(old, new)
            actions.append({"PATTERN": old, "REPLACEMENT_COUNT": count, "DETAIL": label})
    return repaired, actions

def remaining_bad_patterns(text: str):
    rows = []
    for pat in BAD_PATTERNS:
        count = text.count(pat)
        if count:
            rows.append({"PATTERN": pat, "COUNT": count})
    return rows

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--allow-source-mutation", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    reports = repo / REPORT_DIR
    reports.mkdir(parents=True, exist_ok=True)

    p22s13 = first_row(reports / "message_catalog_phase22s1_3_status_summary_v1.csv")
    messages = p22s13.get("MESSAGES", "12")
    text_rows = p22s13.get("TEXT_ROWS", "60")
    locales = p22s13.get("LOCALES", "de;en-US;es;fr;it")

    gates = []
    failures = 0
    def gate(name, ok, detail):
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": detail})
        if not ok:
            failures += 1

    gate("OPERATOR_AUTHORIZED_SOURCE_MUTATION", args.allow_source_mutation, "requires --allow-source-mutation")
    gate("PHASE22S1_3_REPAIR_GREEN",
         p22s13.get("STATUS") == "MESSAGE_CATALOG_PHASE22S1_3_HELP_HINT_ROUTE_RELOCATION_AND_LITERAL_REPAIR_APPLIED",
         p22s13.get("STATUS", ""))
    for relpath in TARGETS:
        gate(f"{relpath.upper().replace('/', '_').replace('.', '_')}_PRESENT",
             (repo / relpath).exists(), relpath)

    backup_rows, mutation_rows, action_rows, remaining_rows, errors = [], [], [], [], []
    status = STATUS_BLOCKED

    if failures == 0:
        try:
            backup_root = repo / BACKUP_ROOT_BASE / f"MSG-022S1_4_LITERAL_NEWLINE_BUILD_REPAIR_BACKUP_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
            for relpath in TARGETS:
                path = repo / relpath
                original = path.read_text(encoding="utf-8", errors="replace")
                repaired, actions = repair_text(original)
                if actions:
                    backup(path, backup_root, repo, backup_rows)
                    path.write_text(repaired, encoding="utf-8")
                    mutation_rows.append({
                        "TARGET_PATH": relpath,
                        "ACTION": "UPDATE",
                        "BYTES": path.stat().st_size,
                        "SHA256": sha256_file(path),
                        "DETAIL": "targeted escaped-newline source repair for build syntax",
                    })
                    for a in actions:
                        action_rows.append({
                            "TARGET_PATH": relpath,
                            "ACTION": "REPAIR_LITERAL_ESCAPED_NEWLINE",
                            "PATTERN": a["PATTERN"],
                            "REPLACEMENT_COUNT": a["REPLACEMENT_COUNT"],
                            "DETAIL": a["DETAIL"],
                        })
                remaining = remaining_bad_patterns(path.read_text(encoding="utf-8", errors="replace"))
                for r in remaining:
                    remaining_rows.append({
                        "TARGET_PATH": relpath,
                        "PATTERN": r["PATTERN"],
                        "COUNT": r["COUNT"],
                    })

            # Rewrite the runtime smoke with real line endings too.
            smoke = repo / "docs/messaging/scripts/MESSAGE_CATALOG_PHASE22S1_HELP_HINT_ROUTING_SMOKE.dts"
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

            if remaining_rows:
                failures += 1
                gates.append({
                    "GATE": "NO_TARGETED_LITERAL_NEWLINE_ARTIFACTS_REMAIN",
                    "STATUS": "FAIL",
                    "DETAIL": f"{len(remaining_rows)} targeted literal escaped-newline pattern rows remain",
                })
            else:
                gates.append({
                    "GATE": "NO_TARGETED_LITERAL_NEWLINE_ARTIFACTS_REMAIN",
                    "STATUS": "PASS",
                    "DETAIL": "0 targeted bad patterns remain",
                })

            status = STATUS_GREEN if failures == 0 else STATUS_BLOCKED
        except Exception as exc:
            failures += 1
            errors.append(str(exc))
            gates.append({"GATE": "PATCH_PHASE22S1_4", "STATUS": "FAIL", "DETAIL": str(exc)})

    validation_issues = "0" if status == STATUS_GREEN else str(failures)

    write_csv(reports / "message_catalog_phase22s1_4_status_summary_v1.csv", [{
        "STATUS": status,
        "MESSAGES": messages,
        "TEXT_ROWS": text_rows,
        "LOCALES": locales,
        "VALIDATION_ISSUES": validation_issues,
        "SOURCE_MUTATION_AUTHORIZED": 1 if args.allow_source_mutation else 0,
        "SOURCE_FILES_MUTATED": len(mutation_rows),
        "SOURCE_BACKUP_ROWS": len(backup_rows),
        "LITERAL_NEWLINE_REPAIR_ROWS": len(action_rows),
        "REMAINING_BAD_PATTERN_ROWS": len(remaining_rows),
        "BUILD_EXECUTED": 0,
        "RUNTIME_SMOKE_EXECUTED": 0,
        "ERRORS": "; ".join(errors),
        "NEXT_GATE": NEXT_GATE,
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }], ["STATUS", "MESSAGES", "TEXT_ROWS", "LOCALES", "VALIDATION_ISSUES",
         "SOURCE_MUTATION_AUTHORIZED", "SOURCE_FILES_MUTATED", "SOURCE_BACKUP_ROWS",
         "LITERAL_NEWLINE_REPAIR_ROWS", "REMAINING_BAD_PATTERN_ROWS",
         "BUILD_EXECUTED", "RUNTIME_SMOKE_EXECUTED", "ERRORS", "NEXT_GATE", "REPORT_TIMESTAMP_UTC"])

    write_csv(reports / "message_catalog_phase22s1_4_gate_check_v1.csv", gates, ["GATE", "STATUS", "DETAIL"])
    write_csv(reports / "message_catalog_phase22s1_4_patch_actions_v1.csv", action_rows,
              ["TARGET_PATH", "ACTION", "PATTERN", "REPLACEMENT_COUNT", "DETAIL"])
    write_csv(reports / "message_catalog_phase22s1_4_source_mutation_inventory_v1.csv", mutation_rows,
              ["TARGET_PATH", "ACTION", "BYTES", "SHA256", "DETAIL"])
    write_csv(reports / "message_catalog_phase22s1_4_source_backup_inventory_v1.csv", backup_rows,
              ["TARGET_PATH", "BACKUP_PATH", "BYTES", "SHA256", "ROLE"])
    write_csv(reports / "message_catalog_phase22s1_4_remaining_bad_patterns_v1.csv", remaining_rows,
              ["TARGET_PATH", "PATTERN", "COUNT"])

    boundary = [
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 1, "OBSERVED_MUTATION": len(mutation_rows), "DETAIL": "Authorized source mutation limited to targeted escaped-newline repair in Phase 22S1 touched files."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_DBF_CATALOG", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_CDX_INDEXES", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active CDX/index mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active LMDB mutation."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No HELP DATA rebuild or mutation."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CMDHELPCHK mutation."},
        {"PROTECTED_SYSTEM": "COMMAND_REGISTRY", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No command registry mutation."},
        {"PROTECTED_SYSTEM": "MANUALGEN", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No manualgen mutation."},
        {"PROTECTED_SYSTEM": "DATADICT_SELF_DOC", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No Data Dictionary/SelfDoc mutation."},
    ]
    write_csv(reports / "message_catalog_phase22s1_4_boundary_ledger_v1.csv", boundary,
              ["PROTECTED_SYSTEM", "MUTATION_ALLOWED", "OBSERVED_MUTATION", "DETAIL"])

    print(status)
    print(f"  messages: {messages}")
    print(f"  text rows: {text_rows}")
    print(f"  locales: {locales.replace(';', ', ')}")
    print(f"  validation issues: {validation_issues}")
    print(f"  source mutation authorized: {1 if args.allow_source_mutation else 0}")
    print(f"  source files mutated: {len(mutation_rows)}")
    print(f"  source backup rows: {len(backup_rows)}")
    print(f"  literal newline repair rows: {len(action_rows)}")
    print(f"  remaining bad pattern rows: {len(remaining_rows)}")
    print("  build executed: 0")
    print("  runtime smoke executed: 0")
    print(f"  next gate: {NEXT_GATE}")
    print(f"  reports: {reports}")
    return 0 if status == STATUS_GREEN else 2

if __name__ == "__main__":
    raise SystemExit(main())
