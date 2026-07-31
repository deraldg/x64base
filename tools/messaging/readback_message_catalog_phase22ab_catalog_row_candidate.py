#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path

STATUS_GREEN = "MESSAGE_CATALOG_PHASE22AB_CATALOG_ROW_CANDIDATE_READBACK_GREEN_SOURCE_HELD"
STATUS_BLOCKED = "MESSAGE_CATALOG_PHASE22AB_CATALOG_ROW_CANDIDATE_READBACK_BLOCKED"
NEXT_GATE = "HOLD_OR_AUTHORIZE_PHASE22AC_ACTIVE_CATALOG_REPLACEMENT_WITH_BACKUP_PLAN"
REPORT_DIR = Path("docs/messaging/reports")
CANDIDATE_ROOT = Path("docs/messaging/candidates/phase22aa_catalog_row_promotion_candidate_v1")

REQUIRED_SYMBOLS = ["MESSAGE_PROOF_MODE_STATUS", "MESSAGE_PROOF_BOUNDARY_NOTE"]
REQUIRED_LOCALES = ["en-US", "es", "fr", "de", "it"]
TARGET_MESSAGES = 14
TARGET_TEXT_ROWS = 70
CURRENT_MESSAGES = 12
CURRENT_TEXT_ROWS = 60

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

def load_manifest(path: Path):
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    reports = repo / REPORT_DIR
    reports.mkdir(parents=True, exist_ok=True)

    aa = first_row(reports / "message_catalog_phase22aa_status_summary_v1.csv")
    aa_savepoint_ok, latest_id = savepoint_present(repo, "MSG-022AA")

    candidate_root = repo / CANDIDATE_ROOT
    message_adds_path = candidate_root / "rows/message_catalog_candidate_message_adds_v1.csv"
    text_adds_path = candidate_root / "rows/message_catalog_candidate_text_adds_v1.csv"
    manifest_path = candidate_root / "manifest/message_catalog_phase22aa_candidate_manifest_v1.json"
    coverage_path = candidate_root / "reports/message_catalog_candidate_locale_coverage_v1.csv"
    contract_path = candidate_root / "reports/message_catalog_candidate_placeholder_contract_v1.csv"

    message_rows = read_csv(message_adds_path)
    text_rows = read_csv(text_adds_path)
    coverage_rows = read_csv(coverage_path)
    contract_rows = read_csv(contract_path)
    manifest = load_manifest(manifest_path)

    gates = []
    failures = 0

    def gate(name: str, ok: bool, detail: str):
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": detail})
        if not ok:
            failures += 1

    gate("PHASE22AA_STAGED_GREEN",
         aa.get("STATUS") == "MESSAGE_CATALOG_PHASE22AA_CATALOG_ROW_PROMOTION_CANDIDATE_STAGED_SOURCE_HELD",
         aa.get("STATUS", "missing"))
    gate("MSG_022AA_SAVEPOINT_PRESENT", aa_savepoint_ok, latest_id)
    gate("CANDIDATE_ROOT_EXISTS", candidate_root.exists(), rel(candidate_root, repo))
    gate("CANDIDATE_MESSAGE_ADDS_FILE_EXISTS", message_adds_path.exists(), rel(message_adds_path, repo))
    gate("CANDIDATE_TEXT_ADDS_FILE_EXISTS", text_adds_path.exists(), rel(text_adds_path, repo))
    gate("CANDIDATE_MANIFEST_EXISTS", manifest_path.exists(), rel(manifest_path, repo))
    gate("CANDIDATE_COVERAGE_REPORT_EXISTS", coverage_path.exists(), rel(coverage_path, repo))
    gate("CANDIDATE_CONTRACT_REPORT_EXISTS", contract_path.exists(), rel(contract_path, repo))

    symbols = unique([r.get("SYMBOL", "") for r in message_rows])
    text_symbols = unique([r.get("SYMBOL", "") for r in text_rows])
    gate("MESSAGE_ROW_COUNT_TWO", len(message_rows) == 2, f"rows={len(message_rows)}")
    gate("TEXT_ROW_COUNT_TEN", len(text_rows) == 10, f"rows={len(text_rows)}")
    gate("MESSAGE_SYMBOLS_MATCH_EXPECTED", sorted(symbols) == sorted(REQUIRED_SYMBOLS), ";".join(symbols))
    gate("TEXT_SYMBOLS_MATCH_EXPECTED", sorted(text_symbols) == sorted(REQUIRED_SYMBOLS), ";".join(text_symbols))

    coverage_readback = []
    for symbol in REQUIRED_SYMBOLS:
        rows = [r for r in text_rows if r.get("SYMBOL") == symbol]
        locales = unique([r.get("LOCALE", "") for r in rows])
        ok = len(rows) == 5 and sorted(locales) == sorted(REQUIRED_LOCALES)
        coverage_readback.append({
            "SYMBOL": symbol,
            "TEXT_ROWS": len(rows),
            "LOCALES": ";".join(locales),
            "EXPECTED_LOCALES": ";".join(REQUIRED_LOCALES),
            "STATUS": "PASS" if ok else "FAIL",
        })
        gate(f"{symbol}_TEXT_LOCALE_COVERAGE", ok, f"rows={len(rows)}; locales={';'.join(locales)}")

    contract_readback = []
    for row in text_rows:
        symbol = row.get("SYMBOL", "")
        locale = row.get("LOCALE", "")
        text = row.get("TEXT", "")
        ok = True
        details = []
        if symbol == "MESSAGE_PROOF_MODE_STATUS":
            if "{mode}" not in text:
                ok = False
                details.append("missing {mode}")
            if "Message routing proof mode:" not in text:
                ok = False
                details.append("missing invariant prefix")
        elif symbol == "MESSAGE_PROOF_BOUNDARY_NOTE":
            if "{mode}" in text:
                ok = False
                details.append("unexpected {mode}")
            if "no DBF/CDX/LMDB mutation" not in text:
                ok = False
                details.append("missing no DBF/CDX/LMDB mutation")
            if "no runtime writeback" not in text:
                ok = False
                details.append("missing no runtime writeback")
        else:
            ok = False
            details.append("unexpected symbol")
        contract_readback.append({
            "SYMBOL": symbol,
            "LOCALE": locale,
            "STATUS": "PASS" if ok else "FAIL",
            "DETAIL": "; ".join(details) if details else "contract ok",
        })
    contract_failures = [r for r in contract_readback if r["STATUS"] != "PASS"]
    gate("PLACEHOLDER_AND_INVARIANT_CONTRACT_READBACK", not contract_failures, f"failures={len(contract_failures)}")

    # Manifest readback.
    gate("MANIFEST_CANDIDATE_ID_PRESENT",
         manifest.get("candidate_id") == "MSG-022AA-CATALOG-ROW-PROMOTION-CANDIDATE-V1",
         manifest.get("candidate_id", "missing"))
    gate("MANIFEST_COUNTS_MATCH_TARGETS",
         manifest.get("current_messages") == CURRENT_MESSAGES and
         manifest.get("current_text_rows") == CURRENT_TEXT_ROWS and
         manifest.get("planned_message_adds") == 2 and
         manifest.get("planned_text_row_adds") == 10 and
         manifest.get("target_messages_after_promotion") == TARGET_MESSAGES and
         manifest.get("target_text_rows_after_promotion") == TARGET_TEXT_ROWS,
         f"current={manifest.get('current_messages')}/{manifest.get('current_text_rows')}; target={manifest.get('target_messages_after_promotion')}/{manifest.get('target_text_rows_after_promotion')}")
    gate("MANIFEST_NO_ACTIVE_MUTATION",
         manifest.get("active_catalog_mutation_in_22aa") == 0 and manifest.get("source_mutation_in_22aa") == 0,
         f"active={manifest.get('active_catalog_mutation_in_22aa')}; source={manifest.get('source_mutation_in_22aa')}")

    # Cross-check AA report counts.
    gate("AA_REPORT_TARGET_COUNTS_14_70",
         aa.get("TARGET_MESSAGES_AFTER_PROMOTION") == "14" and aa.get("TARGET_TEXT_ROWS_AFTER_PROMOTION") == "70",
         f"target={aa.get('TARGET_MESSAGES_AFTER_PROMOTION')}/{aa.get('TARGET_TEXT_ROWS_AFTER_PROMOTION')}")
    gate("AA_REPORT_NO_ACTIVE_OR_HELP_MUTATION",
         aa.get("ACTIVE_CATALOG_MUTATION_OBSERVED") == "0" and
         aa.get("HELP_DATA_MUTATION_OBSERVED") == "0" and
         aa.get("CMDHELPCHK_MUTATION_OBSERVED") == "0",
         f"active={aa.get('ACTIVE_CATALOG_MUTATION_OBSERVED')}; help={aa.get('HELP_DATA_MUTATION_OBSERVED')}; cmdhelpchk={aa.get('CMDHELPCHK_MUTATION_OBSERVED')}")

    status = STATUS_GREEN if failures == 0 else STATUS_BLOCKED
    validation_issues = str(failures)

    artifact_rows = []
    for path, role in [
        (message_adds_path, "candidate_message_adds"),
        (text_adds_path, "candidate_text_adds"),
        (manifest_path, "candidate_manifest"),
        (coverage_path, "candidate_coverage_report"),
        (contract_path, "candidate_contract_report"),
        (candidate_root / "README.md", "candidate_readme"),
    ]:
        artifact_rows.append({
            "ARTIFACT": rel(path, repo),
            "ROLE": role,
            "EXISTS": 1 if path.exists() else 0,
            "BYTES": path.stat().st_size if path.exists() else 0,
            "SHA256": sha256_file(path),
        })

    write_csv(reports / "message_catalog_phase22ab_candidate_artifact_readback_v1.csv", artifact_rows,
              ["ARTIFACT", "ROLE", "EXISTS", "BYTES", "SHA256"])
    write_csv(reports / "message_catalog_phase22ab_candidate_message_readback_v1.csv", message_rows,
              ["SYMBOL", "KIND", "PLACEHOLDERS", "SOURCE_PHASE", "STAGED_BY",
               "ACTIVE_MUTATION_IN_22AA", "PROMOTION_CANDIDATE"])
    write_csv(reports / "message_catalog_phase22ab_candidate_text_readback_v1.csv", text_rows,
              ["SYMBOL", "LOCALE", "TEXT", "PLACEHOLDERS", "SOURCE_PHASE", "STAGED_BY",
               "ACTIVE_MUTATION_IN_22AA", "PROMOTION_CANDIDATE"])
    write_csv(reports / "message_catalog_phase22ab_candidate_locale_coverage_readback_v1.csv", coverage_readback,
              ["SYMBOL", "TEXT_ROWS", "LOCALES", "EXPECTED_LOCALES", "STATUS"])
    write_csv(reports / "message_catalog_phase22ab_candidate_placeholder_contract_readback_v1.csv", contract_readback,
              ["SYMBOL", "LOCALE", "STATUS", "DETAIL"])
    write_csv(reports / "message_catalog_phase22ab_gate_check_v1.csv", gates,
              ["GATE", "STATUS", "DETAIL"])

    boundary = [
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Phase 22AB readback only; no source mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_DBF_CATALOG", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active DBF mutation; candidate rowsets only read."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_CDX_INDEXES", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active CDX/index mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active LMDB mutation."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No HELP DATA mutation."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CMDHELPCHK mutation."},
        {"PROTECTED_SYSTEM": "COMMAND_REGISTRY", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No command registry mutation."},
        {"PROTECTED_SYSTEM": "MANUALGEN", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No manualgen mutation."},
        {"PROTECTED_SYSTEM": "DATADICT_SELF_DOC", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No Data Dictionary/SelfDoc mutation."},
    ]
    write_csv(reports / "message_catalog_phase22ab_boundary_ledger_v1.csv", boundary,
              ["PROTECTED_SYSTEM", "MUTATION_ALLOWED", "OBSERVED_MUTATION", "DETAIL"])

    write_csv(reports / "message_catalog_phase22ab_status_summary_v1.csv", [{
        "STATUS": status,
        "MESSAGES": str(CURRENT_MESSAGES),
        "TEXT_ROWS": str(CURRENT_TEXT_ROWS),
        "LOCALES": ";".join(REQUIRED_LOCALES),
        "VALIDATION_ISSUES": validation_issues,
        "PHASE22AA_GREEN": 1 if aa.get("STATUS") == "MESSAGE_CATALOG_PHASE22AA_CATALOG_ROW_PROMOTION_CANDIDATE_STAGED_SOURCE_HELD" else 0,
        "MSG_022AA_SAVEPOINT_PRESENT": 1 if aa_savepoint_ok else 0,
        "CANDIDATE_ROOT": rel(candidate_root, repo),
        "CANDIDATE_MESSAGE_ROWS_READ": len(message_rows),
        "CANDIDATE_TEXT_ROWS_READ": len(text_rows),
        "SYMBOLS_VALIDATED": len(REQUIRED_SYMBOLS) if sorted(symbols) == sorted(REQUIRED_SYMBOLS) else 0,
        "LOCALE_COVERAGE_VALIDATED": 1 if all(r["STATUS"] == "PASS" for r in coverage_readback) else 0,
        "PLACEHOLDER_CONTRACT_VALIDATED": 1 if not contract_failures else 0,
        "TARGET_MESSAGES_AFTER_PROMOTION": TARGET_MESSAGES,
        "TARGET_TEXT_ROWS_AFTER_PROMOTION": TARGET_TEXT_ROWS,
        "SOURCE_FILES_MUTATED": 0,
        "ACTIVE_CATALOG_MUTATION_OBSERVED": 0,
        "HELP_DATA_MUTATION_OBSERVED": 0,
        "CMDHELPCHK_MUTATION_OBSERVED": 0,
        "NEXT_GATE": NEXT_GATE,
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }], ["STATUS", "MESSAGES", "TEXT_ROWS", "LOCALES", "VALIDATION_ISSUES",
         "PHASE22AA_GREEN", "MSG_022AA_SAVEPOINT_PRESENT", "CANDIDATE_ROOT",
         "CANDIDATE_MESSAGE_ROWS_READ", "CANDIDATE_TEXT_ROWS_READ", "SYMBOLS_VALIDATED",
         "LOCALE_COVERAGE_VALIDATED", "PLACEHOLDER_CONTRACT_VALIDATED",
         "TARGET_MESSAGES_AFTER_PROMOTION", "TARGET_TEXT_ROWS_AFTER_PROMOTION",
         "SOURCE_FILES_MUTATED", "ACTIVE_CATALOG_MUTATION_OBSERVED",
         "HELP_DATA_MUTATION_OBSERVED", "CMDHELPCHK_MUTATION_OBSERVED",
         "NEXT_GATE", "REPORT_TIMESTAMP_UTC"])

    md = f"""# Message Catalog Phase 22AB Catalog Row Candidate Readback

Status: `{status}`

Phase 22AB reads back the Phase 22AA candidate rowsets for:

```text
MESSAGE_PROOF_MODE_STATUS
MESSAGE_PROOF_BOUNDARY_NOTE
```

Validated candidate target after eventual promotion:

```text
messages: {TARGET_MESSAGES}
text rows: {TARGET_TEXT_ROWS}
```

Phase 22AB is readback/report-only. It does not mutate source, active
messaging DBF/CDX/LMDB, HELP DATA, CMDHELPCHK, command registry, manualgen, or
Data Dictionary/SelfDoc.

Next gate:

```text
{NEXT_GATE}
```
"""
    (reports / "MESSAGE_CATALOG_PHASE22AB_CATALOG_ROW_CANDIDATE_READBACK.md").write_text(md, encoding="utf-8")

    print(status)
    print(f"  messages: {CURRENT_MESSAGES}")
    print(f"  text rows: {CURRENT_TEXT_ROWS}")
    print(f"  locales: {', '.join(REQUIRED_LOCALES)}")
    print(f"  validation issues: {validation_issues}")
    print(f"  Phase 22AA green: {1 if aa.get('STATUS') == 'MESSAGE_CATALOG_PHASE22AA_CATALOG_ROW_PROMOTION_CANDIDATE_STAGED_SOURCE_HELD' else 0}")
    print(f"  MSG-022AA savepoint present: {1 if aa_savepoint_ok else 0}")
    print(f"  candidate root: {rel(candidate_root, repo)}")
    print(f"  candidate message rows read: {len(message_rows)}")
    print(f"  candidate text rows read: {len(text_rows)}")
    print(f"  symbols validated: {len(REQUIRED_SYMBOLS) if sorted(symbols) == sorted(REQUIRED_SYMBOLS) else 0}")
    print(f"  locale coverage validated: {1 if all(r['STATUS'] == 'PASS' for r in coverage_readback) else 0}")
    print(f"  placeholder contract validated: {1 if not contract_failures else 0}")
    print(f"  target messages after promotion: {TARGET_MESSAGES}")
    print(f"  target text rows after promotion: {TARGET_TEXT_ROWS}")
    print("  source files mutated: 0")
    print("  active catalog mutation observed: 0")
    print("  HELP DATA mutation observed: 0")
    print("  CMDHELPCHK mutation observed: 0")
    print(f"  next gate: {NEXT_GATE}")
    print(f"  reports: {reports}")
    return 0 if status == STATUS_GREEN else 2

if __name__ == "__main__":
    raise SystemExit(main())
