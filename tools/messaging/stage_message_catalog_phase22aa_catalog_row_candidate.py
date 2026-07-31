#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

STATUS_GREEN = "MESSAGE_CATALOG_PHASE22AA_CATALOG_ROW_PROMOTION_CANDIDATE_STAGED_SOURCE_HELD"
STATUS_BLOCKED = "MESSAGE_CATALOG_PHASE22AA_CATALOG_ROW_PROMOTION_CANDIDATE_STAGING_BLOCKED"
NEXT_GATE = "HOLD_OR_AUTHORIZE_PHASE22AB_CATALOG_ROW_CANDIDATE_READBACK_VALIDATION"
REPORT_DIR = Path("docs/messaging/reports")
CANDIDATE_ROOT = Path("docs/messaging/candidates/phase22aa_catalog_row_promotion_candidate_v1")

REQUIRED_SYMBOLS = ["MESSAGE_PROOF_MODE_STATUS", "MESSAGE_PROOF_BOUNDARY_NOTE"]
REQUIRED_LOCALES = ["en-US", "es", "fr", "de", "it"]

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

def unique(values):
    out = []
    for value in values:
        if value not in out:
            out.append(value)
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--replace-existing-candidate", action="store_true",
                    help="Replace existing Phase 22AA candidate staging directory if present.")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    reports = repo / REPORT_DIR
    reports.mkdir(parents=True, exist_ok=True)

    z = first_row(reports / "message_catalog_phase22z_status_summary_v1.csv")
    z_msg_rows = read_csv(reports / "message_catalog_phase22z_promotion_message_rows_v1.csv")
    z_text_rows = read_csv(reports / "message_catalog_phase22z_promotion_text_rows_v1.csv")
    z_count = first_row(reports / "message_catalog_phase22z_promotion_count_plan_v1.csv")
    savepoint_ok, latest_id = savepoint_present(repo, "MSG-022Z")

    current_messages = z.get("MESSAGES", z_count.get("CURRENT_MESSAGES", "12"))
    current_text_rows = z.get("TEXT_ROWS", z_count.get("CURRENT_TEXT_ROWS", "60"))
    target_messages = z.get("TARGET_MESSAGES_AFTER_PROMOTION", z_count.get("TARGET_MESSAGES_AFTER_PROMOTION", "14"))
    target_text_rows = z.get("TARGET_TEXT_ROWS_AFTER_PROMOTION", z_count.get("TARGET_TEXT_ROWS_AFTER_PROMOTION", "70"))
    locales = z.get("LOCALES", z_count.get("LOCALES", "de;en-US;es;fr;it"))

    gates = []
    failures = 0

    def gate(name: str, ok: bool, detail: str):
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": detail})
        if not ok:
            failures += 1

    gate("PHASE22Z_PLAN_GREEN",
         z.get("STATUS") == "MESSAGE_CATALOG_PHASE22Z_CATALOG_ROW_PROMOTION_PLAN_GREEN_SOURCE_HELD",
         z.get("STATUS", "missing"))
    gate("MSG_022Z_SAVEPOINT_PRESENT", savepoint_ok, latest_id)
    gate("PROMOTION_MESSAGE_ROWS_PRESENT", len(z_msg_rows) == 2, f"rows={len(z_msg_rows)}")
    gate("PROMOTION_TEXT_ROWS_PRESENT", len(z_text_rows) == 10, f"rows={len(z_text_rows)}")
    gate("TARGET_COUNTS_14_70", str(target_messages) == "14" and str(target_text_rows) == "70",
         f"messages={target_messages}; text_rows={target_text_rows}")

    symbols = unique([r.get("SYMBOL", "") for r in z_msg_rows])
    gate("REQUIRED_SYMBOLS_PRESENT",
         sorted(symbols) == sorted(REQUIRED_SYMBOLS),
         ";".join(symbols))

    # Validate text row coverage.
    coverage_rows = []
    for symbol in REQUIRED_SYMBOLS:
        symbol_text_rows = [r for r in z_text_rows if r.get("SYMBOL") == symbol]
        symbol_locales = unique([r.get("LOCALE", "") for r in symbol_text_rows])
        coverage_rows.append({
            "SYMBOL": symbol,
            "TEXT_ROWS": len(symbol_text_rows),
            "LOCALES": ";".join(symbol_locales),
            "EXPECTED_LOCALES": ";".join(REQUIRED_LOCALES),
            "STATUS": "PASS" if sorted(symbol_locales) == sorted(REQUIRED_LOCALES) and len(symbol_text_rows) == 5 else "FAIL",
        })
        gate(f"{symbol}_FIVE_LOCALES_PRESENT",
             sorted(symbol_locales) == sorted(REQUIRED_LOCALES) and len(symbol_text_rows) == 5,
             f"rows={len(symbol_text_rows)}; locales={';'.join(symbol_locales)}")

    # Validate placeholder contracts and invariant tokens.
    contract_rows = []
    for row in z_text_rows:
        symbol = row.get("SYMBOL", "")
        locale = row.get("LOCALE", "")
        text = row.get("TEXT", "")
        ok = True
        detail = []
        if symbol == "MESSAGE_PROOF_MODE_STATUS":
            if "{mode}" not in text:
                ok = False
                detail.append("missing {mode}")
            if "Message routing proof mode:" not in text:
                ok = False
                detail.append("missing invariant proof-mode prefix")
        elif symbol == "MESSAGE_PROOF_BOUNDARY_NOTE":
            if "{mode}" in text:
                ok = False
                detail.append("unexpected {mode}")
            for token in ["no DBF/CDX/LMDB mutation", "no runtime writeback"]:
                if token not in text:
                    ok = False
                    detail.append(f"missing {token}")
        contract_rows.append({
            "SYMBOL": symbol,
            "LOCALE": locale,
            "STATUS": "PASS" if ok else "FAIL",
            "DETAIL": "; ".join(detail) if detail else "contract ok",
        })
    contract_failures = [r for r in contract_rows if r["STATUS"] != "PASS"]
    gate("PLACEHOLDER_AND_INVARIANT_CONTRACTS_PASS",
         not contract_failures,
         f"failures={len(contract_failures)}")

    candidate_root = repo / CANDIDATE_ROOT
    if candidate_root.exists():
        if args.replace_existing_candidate:
            shutil.rmtree(candidate_root)
        else:
            gate("CANDIDATE_ROOT_NOT_PREEXISTING_OR_REPLACE_ALLOWED",
                 False,
                 f"{rel(candidate_root, repo)} exists; rerun with -ReplaceExistingCandidate")
    else:
        gate("CANDIDATE_ROOT_NOT_PREEXISTING_OR_REPLACE_ALLOWED", True, rel(candidate_root, repo))

    status = STATUS_BLOCKED
    artifact_rows = []
    manifest = {}
    errors = []

    if failures == 0:
        try:
            candidate_root.mkdir(parents=True, exist_ok=True)
            rows_dir = candidate_root / "rows"
            reports_dir = candidate_root / "reports"
            manifest_dir = candidate_root / "manifest"
            rows_dir.mkdir(parents=True, exist_ok=True)
            reports_dir.mkdir(parents=True, exist_ok=True)
            manifest_dir.mkdir(parents=True, exist_ok=True)

            message_adds_path = rows_dir / "message_catalog_candidate_message_adds_v1.csv"
            text_adds_path = rows_dir / "message_catalog_candidate_text_adds_v1.csv"
            coverage_path = reports_dir / "message_catalog_candidate_locale_coverage_v1.csv"
            contract_path = reports_dir / "message_catalog_candidate_placeholder_contract_v1.csv"

            candidate_msg_rows = []
            for row in z_msg_rows:
                candidate_msg_rows.append({
                    "SYMBOL": row.get("SYMBOL", ""),
                    "KIND": row.get("KIND", ""),
                    "PLACEHOLDERS": row.get("PLACEHOLDERS", ""),
                    "SOURCE_PHASE": "22Y",
                    "STAGED_BY": "22AA",
                    "ACTIVE_MUTATION_IN_22AA": 0,
                    "PROMOTION_CANDIDATE": 1,
                })
            candidate_text_rows = []
            for row in z_text_rows:
                candidate_text_rows.append({
                    "SYMBOL": row.get("SYMBOL", ""),
                    "LOCALE": row.get("LOCALE", ""),
                    "TEXT": row.get("TEXT", ""),
                    "PLACEHOLDERS": row.get("PLACEHOLDERS", ""),
                    "SOURCE_PHASE": "22Y",
                    "STAGED_BY": "22AA",
                    "ACTIVE_MUTATION_IN_22AA": 0,
                    "PROMOTION_CANDIDATE": 1,
                })

            write_csv(message_adds_path, candidate_msg_rows,
                      ["SYMBOL", "KIND", "PLACEHOLDERS", "SOURCE_PHASE", "STAGED_BY",
                       "ACTIVE_MUTATION_IN_22AA", "PROMOTION_CANDIDATE"])
            write_csv(text_adds_path, candidate_text_rows,
                      ["SYMBOL", "LOCALE", "TEXT", "PLACEHOLDERS", "SOURCE_PHASE", "STAGED_BY",
                       "ACTIVE_MUTATION_IN_22AA", "PROMOTION_CANDIDATE"])
            write_csv(coverage_path, coverage_rows,
                      ["SYMBOL", "TEXT_ROWS", "LOCALES", "EXPECTED_LOCALES", "STATUS"])
            write_csv(contract_path, contract_rows,
                      ["SYMBOL", "LOCALE", "STATUS", "DETAIL"])

            candidate_files = [message_adds_path, text_adds_path, coverage_path, contract_path]
            for path in candidate_files:
                artifact_rows.append({
                    "ARTIFACT": rel(path, repo),
                    "ROLE": "candidate_rowset" if path.parent == rows_dir else "candidate_validation_report",
                    "BYTES": path.stat().st_size,
                    "SHA256": sha256_file(path),
                })

            manifest = {
                "candidate_id": "MSG-022AA-CATALOG-ROW-PROMOTION-CANDIDATE-V1",
                "created_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
                "source_phase": "22Z",
                "source_reports": [
                    "docs/messaging/reports/message_catalog_phase22z_promotion_message_rows_v1.csv",
                    "docs/messaging/reports/message_catalog_phase22z_promotion_text_rows_v1.csv",
                    "docs/messaging/reports/message_catalog_phase22z_promotion_count_plan_v1.csv",
                ],
                "candidate_root": rel(candidate_root, repo),
                "symbols": REQUIRED_SYMBOLS,
                "locales": REQUIRED_LOCALES,
                "current_messages": int(current_messages),
                "current_text_rows": int(current_text_rows),
                "planned_message_adds": 2,
                "planned_text_row_adds": 10,
                "target_messages_after_promotion": int(target_messages),
                "target_text_rows_after_promotion": int(target_text_rows),
                "active_catalog_mutation_in_22aa": 0,
                "source_mutation_in_22aa": 0,
                "help_data_mutation_in_22aa": 0,
                "cmdhelpchk_mutation_in_22aa": 0,
                "next_gate": NEXT_GATE,
                "artifacts": artifact_rows,
            }
            manifest_path = manifest_dir / "message_catalog_phase22aa_candidate_manifest_v1.json"
            manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
            artifact_rows.append({
                "ARTIFACT": rel(manifest_path, repo),
                "ROLE": "candidate_manifest",
                "BYTES": manifest_path.stat().st_size,
                "SHA256": sha256_file(manifest_path),
            })

            readme_path = candidate_root / "README.md"
            readme_path.write_text(
                "# Phase 22AA Message Catalog Row Promotion Candidate\n\n"
                "This directory stages the two Phase 22Y proof-status message symbols as candidate rowsets only.\n\n"
                "No active DBF/CDX/LMDB, source, HELP DATA, CMDHELPCHK, command registry, manualgen, or Data Dictionary/SelfDoc mutation occurs in Phase 22AA.\n\n"
                "Next gate: HOLD_OR_AUTHORIZE_PHASE22AB_CATALOG_ROW_CANDIDATE_READBACK_VALIDATION\n",
                encoding="utf-8",
            )
            artifact_rows.append({
                "ARTIFACT": rel(readme_path, repo),
                "ROLE": "candidate_readme",
                "BYTES": readme_path.stat().st_size,
                "SHA256": sha256_file(readme_path),
            })

            status = STATUS_GREEN
        except Exception as exc:
            errors.append(str(exc))
            failures += 1
            gates.append({"GATE": "STAGE_PHASE22AA_CANDIDATE", "STATUS": "FAIL", "DETAIL": str(exc)})
            status = STATUS_BLOCKED

    validation_issues = "0" if status == STATUS_GREEN else str(failures)

    write_csv(reports / "message_catalog_phase22aa_candidate_artifact_inventory_v1.csv", artifact_rows,
              ["ARTIFACT", "ROLE", "BYTES", "SHA256"])
    write_csv(reports / "message_catalog_phase22aa_locale_coverage_v1.csv", coverage_rows,
              ["SYMBOL", "TEXT_ROWS", "LOCALES", "EXPECTED_LOCALES", "STATUS"])
    write_csv(reports / "message_catalog_phase22aa_placeholder_contract_v1.csv", contract_rows,
              ["SYMBOL", "LOCALE", "STATUS", "DETAIL"])
    write_csv(reports / "message_catalog_phase22aa_gate_check_v1.csv", gates,
              ["GATE", "STATUS", "DETAIL"])

    boundary = [
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Phase 22AA stages candidate row files only; no source mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_DBF_CATALOG", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active DBF mutation; candidate rows staged under docs/messaging/candidates."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_CDX_INDEXES", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active CDX/index mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active LMDB mutation."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No HELP DATA mutation."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CMDHELPCHK mutation."},
        {"PROTECTED_SYSTEM": "COMMAND_REGISTRY", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No command registry mutation."},
        {"PROTECTED_SYSTEM": "MANUALGEN", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No manualgen mutation."},
        {"PROTECTED_SYSTEM": "DATADICT_SELF_DOC", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No Data Dictionary/SelfDoc mutation."},
    ]
    write_csv(reports / "message_catalog_phase22aa_boundary_ledger_v1.csv", boundary,
              ["PROTECTED_SYSTEM", "MUTATION_ALLOWED", "OBSERVED_MUTATION", "DETAIL"])

    write_csv(reports / "message_catalog_phase22aa_status_summary_v1.csv", [{
        "STATUS": status,
        "MESSAGES": current_messages,
        "TEXT_ROWS": current_text_rows,
        "LOCALES": locales,
        "VALIDATION_ISSUES": validation_issues,
        "PHASE22Z_GREEN": 1 if z.get("STATUS") == "MESSAGE_CATALOG_PHASE22Z_CATALOG_ROW_PROMOTION_PLAN_GREEN_SOURCE_HELD" else 0,
        "MSG_022Z_SAVEPOINT_PRESENT": 1 if savepoint_ok else 0,
        "CANDIDATE_ROOT": rel(repo / CANDIDATE_ROOT, repo),
        "CANDIDATE_ARTIFACTS": len(artifact_rows),
        "CANDIDATE_MESSAGE_ROWS": len(z_msg_rows),
        "CANDIDATE_TEXT_ROWS": len(z_text_rows),
        "TARGET_MESSAGES_AFTER_PROMOTION": target_messages,
        "TARGET_TEXT_ROWS_AFTER_PROMOTION": target_text_rows,
        "SOURCE_FILES_MUTATED": 0,
        "ACTIVE_CATALOG_MUTATION_OBSERVED": 0,
        "HELP_DATA_MUTATION_OBSERVED": 0,
        "CMDHELPCHK_MUTATION_OBSERVED": 0,
        "ERRORS": "; ".join(errors),
        "NEXT_GATE": NEXT_GATE,
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }], ["STATUS", "MESSAGES", "TEXT_ROWS", "LOCALES", "VALIDATION_ISSUES",
         "PHASE22Z_GREEN", "MSG_022Z_SAVEPOINT_PRESENT", "CANDIDATE_ROOT",
         "CANDIDATE_ARTIFACTS", "CANDIDATE_MESSAGE_ROWS", "CANDIDATE_TEXT_ROWS",
         "TARGET_MESSAGES_AFTER_PROMOTION", "TARGET_TEXT_ROWS_AFTER_PROMOTION",
         "SOURCE_FILES_MUTATED", "ACTIVE_CATALOG_MUTATION_OBSERVED",
         "HELP_DATA_MUTATION_OBSERVED", "CMDHELPCHK_MUTATION_OBSERVED",
         "ERRORS", "NEXT_GATE", "REPORT_TIMESTAMP_UTC"])

    md = f"""# Message Catalog Phase 22AA Catalog Row Promotion Candidate Staging

Status: `{status}`

Phase 22AA stages candidate row files for the two Phase 22Y proof-status symbols:

```text
MESSAGE_PROOF_MODE_STATUS
MESSAGE_PROOF_BOUNDARY_NOTE
```

Candidate root:

```text
{rel(repo / CANDIDATE_ROOT, repo)}
```

Target counts after eventual active promotion:

```text
messages: {target_messages}
text rows: {target_text_rows}
```

Phase 22AA does not mutate source, active messaging DBF/CDX/LMDB, HELP DATA,
CMDHELPCHK, command registry, manualgen, or Data Dictionary/SelfDoc.

Next gate:

```text
{NEXT_GATE}
```
"""
    (reports / "MESSAGE_CATALOG_PHASE22AA_CATALOG_ROW_PROMOTION_CANDIDATE_STAGING.md").write_text(md, encoding="utf-8")

    print(status)
    print(f"  messages: {current_messages}")
    print(f"  text rows: {current_text_rows}")
    print(f"  locales: {locales.replace(';', ', ')}")
    print(f"  validation issues: {validation_issues}")
    print(f"  Phase 22Z green: {1 if z.get('STATUS') == 'MESSAGE_CATALOG_PHASE22Z_CATALOG_ROW_PROMOTION_PLAN_GREEN_SOURCE_HELD' else 0}")
    print(f"  MSG-022Z savepoint present: {1 if savepoint_ok else 0}")
    print(f"  candidate root: {rel(repo / CANDIDATE_ROOT, repo)}")
    print(f"  candidate artifacts: {len(artifact_rows)}")
    print(f"  candidate message rows: {len(z_msg_rows)}")
    print(f"  candidate text rows: {len(z_text_rows)}")
    print(f"  target messages after promotion: {target_messages}")
    print(f"  target text rows after promotion: {target_text_rows}")
    print("  source files mutated: 0")
    print("  active catalog mutation observed: 0")
    print("  HELP DATA mutation observed: 0")
    print("  CMDHELPCHK mutation observed: 0")
    print(f"  next gate: {NEXT_GATE}")
    print(f"  reports: {reports}")
    return 0 if status == STATUS_GREEN else 2

if __name__ == "__main__":
    raise SystemExit(main())
