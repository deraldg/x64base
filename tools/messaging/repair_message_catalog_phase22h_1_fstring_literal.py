#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
from datetime import datetime, timezone
from pathlib import Path

STATUS_GREEN = "MESSAGE_CATALOG_PHASE22H_1_FSTRING_LITERAL_REPAIR_APPLIED"
STATUS_BLOCKED = "MESSAGE_CATALOG_PHASE22H_1_FSTRING_LITERAL_REPAIR_BLOCKED"
REPORT_DIR = Path("docs/messaging/reports")

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

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    reports = repo / REPORT_DIR
    reports.mkdir(parents=True, exist_ok=True)

    target = repo / "tools/messaging/review_message_catalog_phase22h_emission_pilot_closeout.py"

    gates = []
    failures = 0

    def gate(name, ok, detail):
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": detail})
        if not ok:
            failures += 1

    gate("TARGET_SCRIPT_PRESENT", target.exists(), str(target))

    mutation_rows = []
    status = STATUS_BLOCKED

    if failures == 0:
        text = target.read_text(encoding="utf-8", errors="replace")
        before = text
        before_hash = sha256_file(target)

        # The Phase 22H report writer uses an f-string for markdown. The literal
        # placeholder token {command} must be escaped inside that f-string.
        text = text.replace("validation for `{command}`.", "validation for `{{command}}`.")
        text = text.replace("validation for `{COMMAND}`.", "validation for `{{COMMAND}}`.")

        if text == before:
            # Treat already-repaired scripts as green if the escaped literal is present.
            gate("FSTRING_LITERAL_ALREADY_ESCAPED", "`{{command}}`" in text or "`{{COMMAND}}`" in text,
                 "expected escaped placeholder literal in generated markdown f-string")
        else:
            target.write_text(text, encoding="utf-8")
            mutation_rows.append({
                "TARGET_PATH": "tools/messaging/review_message_catalog_phase22h_emission_pilot_closeout.py",
                "ACTION": "UPDATE",
                "BEFORE_SHA256": before_hash,
                "AFTER_SHA256": sha256_file(target),
                "DETAIL": "escaped literal {command} inside generated markdown f-string",
            })

        # Compile after the repair. This will catch the syntax class of defects.
        import py_compile
        try:
            py_compile.compile(str(target), doraise=True)
            gate("REPAIRED_SCRIPT_COMPILES", True, str(target))
        except Exception as exc:
            gate("REPAIRED_SCRIPT_COMPILES", False, str(exc))

        if failures == 0:
            status = STATUS_GREEN

    validation_issues = "0" if status == STATUS_GREEN else str(failures)

    write_csv(reports / "message_catalog_phase22h_1_status_summary_v1.csv", [{
        "STATUS": status,
        "VALIDATION_ISSUES": validation_issues,
        "TOOLING_REPAIR_APPLIED": 1 if status == STATUS_GREEN else 0,
        "SOURCE_CODE_MUTATION": 0,
        "ACTIVE_CATALOG_MUTATION": 0,
        "TARGET_SCRIPT": "tools/messaging/review_message_catalog_phase22h_emission_pilot_closeout.py",
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }], ["STATUS", "VALIDATION_ISSUES", "TOOLING_REPAIR_APPLIED", "SOURCE_CODE_MUTATION",
         "ACTIVE_CATALOG_MUTATION", "TARGET_SCRIPT", "REPORT_TIMESTAMP_UTC"])

    write_csv(reports / "message_catalog_phase22h_1_gate_check_v1.csv", gates,
              ["GATE", "STATUS", "DETAIL"])

    write_csv(reports / "message_catalog_phase22h_1_tooling_repair_inventory_v1.csv", mutation_rows,
              ["TARGET_PATH", "ACTION", "BEFORE_SHA256", "AFTER_SHA256", "DETAIL"])

    boundary = [
        {"PROTECTED_SYSTEM": "MESSAGING_TOOLING", "MUTATION_ALLOWED": 1, "OBSERVED_MUTATION": len(mutation_rows), "DETAIL": "Repair limited to Phase 22H review script f-string literal."},
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No runtime source mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_DBF_CATALOG", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_CDX_INDEXES", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active CDX/index mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active LMDB mutation."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No HELP DATA mutation."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CMDHELPCHK mutation."},
        {"PROTECTED_SYSTEM": "MANUALGEN", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No manualgen mutation."},
        {"PROTECTED_SYSTEM": "DATADICT_SELF_DOC", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No Data Dictionary/SelfDoc mutation."},
    ]
    write_csv(reports / "message_catalog_phase22h_1_boundary_ledger_v1.csv", boundary,
              ["PROTECTED_SYSTEM", "MUTATION_ALLOWED", "OBSERVED_MUTATION", "DETAIL"])

    print(status)
    print(f"  validation issues: {validation_issues}")
    print(f"  tooling repair applied: {1 if status == STATUS_GREEN else 0}")
    print("  source code mutation: 0")
    print("  active catalog mutation: 0")
    print(f"  reports: {reports}")
    return 0 if status == STATUS_GREEN else 2

if __name__ == "__main__":
    raise SystemExit(main())
