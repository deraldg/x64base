#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path

STATUS_GREEN = "MESSAGE_CATALOG_PHASE22AC_ACTIVE_CATALOG_REPLACEMENT_WITH_BACKUP_PLAN_GREEN_SOURCE_HELD"
STATUS_BLOCKED = "MESSAGE_CATALOG_PHASE22AC_ACTIVE_CATALOG_REPLACEMENT_WITH_BACKUP_PLAN_BLOCKED"
NEXT_GATE = "HOLD_OR_AUTHORIZE_PHASE22AD_ACTIVE_CATALOG_REPLACEMENT_APPLY_PACKAGE"
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

def list_artifacts(root: Path, repo: Path):
    rows = []
    if root.exists():
        for p in sorted(root.rglob("*")):
            if p.is_file():
                rows.append({
                    "ARTIFACT": rel(p, repo),
                    "BYTES": p.stat().st_size,
                    "SHA256": sha256_file(p),
                })
    return rows

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    reports = repo / REPORT_DIR
    reports.mkdir(parents=True, exist_ok=True)

    ab = first_row(reports / "message_catalog_phase22ab_status_summary_v1.csv")
    aa = first_row(reports / "message_catalog_phase22aa_status_summary_v1.csv")
    ab_savepoint_ok, latest_id = savepoint_present(repo, "MSG-022AB")

    candidate_root = repo / CANDIDATE_ROOT
    message_adds_path = candidate_root / "rows/message_catalog_candidate_message_adds_v1.csv"
    text_adds_path = candidate_root / "rows/message_catalog_candidate_text_adds_v1.csv"
    manifest_path = candidate_root / "manifest/message_catalog_phase22aa_candidate_manifest_v1.json"

    message_rows = read_csv(message_adds_path)
    text_rows = read_csv(text_adds_path)
    manifest = {}
    if manifest_path.exists():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except Exception:
            manifest = {}

    messages = ab.get("MESSAGES", aa.get("MESSAGES", "12"))
    text_count = ab.get("TEXT_ROWS", aa.get("TEXT_ROWS", "60"))
    locales = ab.get("LOCALES", aa.get("LOCALES", "en-US;es;fr;de;it"))
    target_messages = ab.get("TARGET_MESSAGES_AFTER_PROMOTION", "14")
    target_text_rows = ab.get("TARGET_TEXT_ROWS_AFTER_PROMOTION", "70")

    gates = []
    failures = 0

    def gate(name: str, ok: bool, detail: str):
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": detail})
        if not ok:
            failures += 1

    gate("PHASE22AB_READBACK_GREEN",
         ab.get("STATUS") == "MESSAGE_CATALOG_PHASE22AB_CATALOG_ROW_CANDIDATE_READBACK_GREEN_SOURCE_HELD",
         ab.get("STATUS", "missing"))
    gate("MSG_022AB_SAVEPOINT_PRESENT", ab_savepoint_ok, latest_id)
    gate("CANDIDATE_ROOT_EXISTS", candidate_root.exists(), rel(candidate_root, repo))
    gate("CANDIDATE_MESSAGE_ROWS_AVAILABLE", len(message_rows) == 2, f"rows={len(message_rows)}")
    gate("CANDIDATE_TEXT_ROWS_AVAILABLE", len(text_rows) == 10, f"rows={len(text_rows)}")
    gate("AB_TARGET_COUNTS_14_70",
         str(target_messages) == "14" and str(target_text_rows) == "70",
         f"target={target_messages}/{target_text_rows}")
    gate("AB_PLACEHOLDER_CONTRACT_VALIDATED",
         ab.get("PLACEHOLDER_CONTRACT_VALIDATED") == "1",
         ab.get("PLACEHOLDER_CONTRACT_VALIDATED", ""))
    gate("AB_LOCALE_COVERAGE_VALIDATED",
         ab.get("LOCALE_COVERAGE_VALIDATED") == "1",
         ab.get("LOCALE_COVERAGE_VALIDATED", ""))
    gate("AB_NO_ACTIVE_OR_HELP_MUTATION",
         ab.get("ACTIVE_CATALOG_MUTATION_OBSERVED") == "0" and
         ab.get("HELP_DATA_MUTATION_OBSERVED") == "0" and
         ab.get("CMDHELPCHK_MUTATION_OBSERVED") == "0",
         f"active={ab.get('ACTIVE_CATALOG_MUTATION_OBSERVED','')}; help={ab.get('HELP_DATA_MUTATION_OBSERVED','')}; cmdhelpchk={ab.get('CMDHELPCHK_MUTATION_OBSERVED','')}")
    gate("MANIFEST_TARGET_COUNTS_MATCH",
         manifest.get("target_messages_after_promotion") == 14 and
         manifest.get("target_text_rows_after_promotion") == 70,
         f"manifest_target={manifest.get('target_messages_after_promotion')}/{manifest.get('target_text_rows_after_promotion')}")

    active_roots = [
        {"ROOT_ID": "MSG_DBF", "PATH": "dottalkpp/data/messaging", "ROLE": "active messaging DBF/catalog root", "MUST_BACKUP_BEFORE_APPLY": 1},
        {"ROOT_ID": "MSG_INDEXES", "PATH": "dottalkpp/data/indexes/messaging", "ROLE": "active messaging CDX/index root", "MUST_BACKUP_BEFORE_APPLY": 1},
        {"ROOT_ID": "MSG_LMDB", "PATH": "dottalkpp/data/lmdb/messaging", "ROLE": "active messaging LMDB root", "MUST_BACKUP_BEFORE_APPLY": 1},
    ]
    for row in active_roots:
        p = repo / row["PATH"]
        row["EXISTS_NOW"] = 1 if p.exists() else 0
        row["FILE_COUNT_NOW"] = sum(1 for x in p.rglob("*") if x.is_file()) if p.exists() else 0
    write_csv(reports / "message_catalog_phase22ac_active_roots_plan_v1.csv", active_roots,
              ["ROOT_ID", "PATH", "ROLE", "MUST_BACKUP_BEFORE_APPLY", "EXISTS_NOW", "FILE_COUNT_NOW"])

    candidate_artifacts = list_artifacts(candidate_root, repo)
    write_csv(reports / "message_catalog_phase22ac_candidate_artifact_fingerprint_v1.csv", candidate_artifacts,
              ["ARTIFACT", "BYTES", "SHA256"])

    backup_plan = [
        {
            "STEP": 1,
            "ACTION": "STOP_RUNTIME",
            "DETAIL": "Confirm no dottalkpp process is running so active DBF/CDX/LMDB files are not locked.",
            "MUTATION_IN_22AC": 0,
            "REQUIRED_FOR_22AD": 1,
        },
        {
            "STEP": 2,
            "ACTION": "SNAPSHOT_ACTIVE_ARTIFACTS",
            "DETAIL": "Fingerprint current active messaging DBF/CDX/LMDB roots before any replacement.",
            "MUTATION_IN_22AC": 0,
            "REQUIRED_FOR_22AD": 1,
        },
        {
            "STEP": 3,
            "ACTION": "BACKUP_ACTIVE_ARTIFACTS",
            "DETAIL": "Copy active messaging DBF/CDX/LMDB roots to docs/messaging/backups/MSG-022AD_ACTIVE_CATALOG_REPLACEMENT_BACKUP_<timestamp>.",
            "MUTATION_IN_22AC": 0,
            "REQUIRED_FOR_22AD": 1,
        },
        {
            "STEP": 4,
            "ACTION": "STAGE_PROMOTION_SCRIPT",
            "DETAIL": "Create an apply package that adds exactly the two candidate message rows and ten text rows to active messaging catalog using the existing catalog import path.",
            "MUTATION_IN_22AC": 0,
            "REQUIRED_FOR_22AD": 1,
        },
        {
            "STEP": 5,
            "ACTION": "REBUILD_INDEX_LMDB_IF_REQUIRED",
            "DETAIL": "After active DBF row apply, rebuild CDX/LMDB only within the active messaging catalog roots.",
            "MUTATION_IN_22AC": 0,
            "REQUIRED_FOR_22AD": 1,
        },
        {
            "STEP": 6,
            "ACTION": "READBACK_ACTIVE_COUNTS",
            "DETAIL": "Validate active catalog reports 14 messages and 70 text rows, with all five locale rows for both new symbols.",
            "MUTATION_IN_22AC": 0,
            "REQUIRED_FOR_22AD": 1,
        },
        {
            "STEP": 7,
            "ACTION": "RUNTIME_SMOKE_AND_22V_REGRESSION",
            "DETAIL": "Run SET MESSAGE PROOF focused smoke and full 22V regression pack against the promoted active catalog.",
            "MUTATION_IN_22AC": 0,
            "REQUIRED_FOR_22AD": 1,
        },
    ]
    write_csv(reports / "message_catalog_phase22ac_active_replacement_backup_plan_v1.csv", backup_plan,
              ["STEP", "ACTION", "DETAIL", "MUTATION_IN_22AC", "REQUIRED_FOR_22AD"])

    apply_scope = [
        {"SCOPE_ITEM": "ALLOWED_ACTIVE_MUTATION_22AD", "VALUE": "active messaging catalog rows/index/lmdb only", "DETAIL": "Only after 22AD explicit authorization."},
        {"SCOPE_ITEM": "MESSAGE_ROWS_TO_ADD", "VALUE": "2", "DETAIL": "MESSAGE_PROOF_MODE_STATUS and MESSAGE_PROOF_BOUNDARY_NOTE."},
        {"SCOPE_ITEM": "TEXT_ROWS_TO_ADD", "VALUE": "10", "DETAIL": "Five locales for each new symbol."},
        {"SCOPE_ITEM": "TARGET_MESSAGES", "VALUE": "14", "DETAIL": "Current 12 plus 2."},
        {"SCOPE_ITEM": "TARGET_TEXT_ROWS", "VALUE": "70", "DETAIL": "Current 60 plus 10."},
        {"SCOPE_ITEM": "SOURCE_MUTATION", "VALUE": "forbidden", "DETAIL": "22AD should not edit source."},
        {"SCOPE_ITEM": "HELP_DATA_MUTATION", "VALUE": "forbidden", "DETAIL": "HELP DATA remains protected."},
        {"SCOPE_ITEM": "CMDHELPCHK_MUTATION", "VALUE": "forbidden", "DETAIL": "CMDHELPCHK remains protected."},
        {"SCOPE_ITEM": "ROLLBACK_REQUIRED", "VALUE": "yes", "DETAIL": "Active backup must be created before apply and retained."},
    ]
    write_csv(reports / "message_catalog_phase22ac_apply_scope_v1.csv", apply_scope,
              ["SCOPE_ITEM", "VALUE", "DETAIL"])

    risk_rows = [
        {"RISK": "file lock during active replacement", "MITIGATION": "confirm no dottalkpp process before 22AD apply; copy-item/datarun lock lessons from earlier phases"},
        {"RISK": "duplicate symbols/rows", "MITIGATION": "22AD apply must be idempotence-aware and refuse if active catalog already contains both symbols unless replacement mode is explicit"},
        {"RISK": "index/lmdb drift", "MITIGATION": "rebuild or validate active messaging CDX/LMDB after row apply"},
        {"RISK": "regression of existing runtime seams", "MITIGATION": "rerun focused proof smoke and 22V regression pack after active promotion"},
        {"RISK": "protected system mutation", "MITIGATION": "explicitly forbid source, HELP DATA, CMDHELPCHK, command registry, manualgen, and Data Dictionary/SelfDoc mutations"},
    ]
    write_csv(reports / "message_catalog_phase22ac_risk_register_v1.csv", risk_rows,
              ["RISK", "MITIGATION"])

    boundary = [
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Phase 22AC is plan-only; no source mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_DBF_CATALOG", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active DBF mutation in 22AC; mutation is deferred to authorized 22AD."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_CDX_INDEXES", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active CDX/index mutation in 22AC."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active LMDB mutation in 22AC."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No HELP DATA mutation."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CMDHELPCHK mutation."},
        {"PROTECTED_SYSTEM": "COMMAND_REGISTRY", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No command registry mutation."},
        {"PROTECTED_SYSTEM": "MANUALGEN", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No manualgen mutation."},
        {"PROTECTED_SYSTEM": "DATADICT_SELF_DOC", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No Data Dictionary/SelfDoc mutation."},
    ]
    write_csv(reports / "message_catalog_phase22ac_boundary_ledger_v1.csv", boundary,
              ["PROTECTED_SYSTEM", "MUTATION_ALLOWED", "OBSERVED_MUTATION", "DETAIL"])

    write_csv(reports / "message_catalog_phase22ac_gate_check_v1.csv", gates,
              ["GATE", "STATUS", "DETAIL"])

    status = STATUS_GREEN if failures == 0 else STATUS_BLOCKED
    validation_issues = str(failures)

    write_csv(reports / "message_catalog_phase22ac_status_summary_v1.csv", [{
        "STATUS": status,
        "MESSAGES": messages,
        "TEXT_ROWS": text_count,
        "LOCALES": locales,
        "VALIDATION_ISSUES": validation_issues,
        "PHASE22AB_GREEN": 1 if ab.get("STATUS") == "MESSAGE_CATALOG_PHASE22AB_CATALOG_ROW_CANDIDATE_READBACK_GREEN_SOURCE_HELD" else 0,
        "MSG_022AB_SAVEPOINT_PRESENT": 1 if ab_savepoint_ok else 0,
        "CANDIDATE_MESSAGE_ROWS": len(message_rows),
        "CANDIDATE_TEXT_ROWS": len(text_rows),
        "TARGET_MESSAGES_AFTER_PROMOTION": target_messages,
        "TARGET_TEXT_ROWS_AFTER_PROMOTION": target_text_rows,
        "ACTIVE_REPLACEMENT_PLAN_CREATED": 1 if status == STATUS_GREEN else 0,
        "SOURCE_FILES_MUTATED": 0,
        "ACTIVE_CATALOG_MUTATION_OBSERVED": 0,
        "HELP_DATA_MUTATION_OBSERVED": 0,
        "CMDHELPCHK_MUTATION_OBSERVED": 0,
        "NEXT_GATE": NEXT_GATE,
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }], ["STATUS", "MESSAGES", "TEXT_ROWS", "LOCALES", "VALIDATION_ISSUES",
         "PHASE22AB_GREEN", "MSG_022AB_SAVEPOINT_PRESENT",
         "CANDIDATE_MESSAGE_ROWS", "CANDIDATE_TEXT_ROWS",
         "TARGET_MESSAGES_AFTER_PROMOTION", "TARGET_TEXT_ROWS_AFTER_PROMOTION",
         "ACTIVE_REPLACEMENT_PLAN_CREATED", "SOURCE_FILES_MUTATED",
         "ACTIVE_CATALOG_MUTATION_OBSERVED", "HELP_DATA_MUTATION_OBSERVED",
         "CMDHELPCHK_MUTATION_OBSERVED", "NEXT_GATE", "REPORT_TIMESTAMP_UTC"])

    md = f"""# Message Catalog Phase 22AC Active Catalog Replacement with Backup Plan

Status: `{status}`

Phase 22AC plans the guarded active catalog replacement for the two candidate
proof-status symbols.

Candidate rows:

```text
message rows: {len(message_rows)}
text rows: {len(text_rows)}
```

Target active counts after a later authorized apply:

```text
messages: {target_messages}
text rows: {target_text_rows}
```

Phase 22AC is plan-only. It does not mutate source, active messaging DBF/CDX/LMDB,
HELP DATA, CMDHELPCHK, command registry, manualgen, or Data Dictionary/SelfDoc.

Next gate:

```text
{NEXT_GATE}
```
"""
    (reports / "MESSAGE_CATALOG_PHASE22AC_ACTIVE_CATALOG_REPLACEMENT_WITH_BACKUP_PLAN.md").write_text(md, encoding="utf-8")

    print(status)
    print(f"  messages: {messages}")
    print(f"  text rows: {text_count}")
    print(f"  locales: {locales.replace(';', ', ')}")
    print(f"  validation issues: {validation_issues}")
    print(f"  Phase 22AB green: {1 if ab.get('STATUS') == 'MESSAGE_CATALOG_PHASE22AB_CATALOG_ROW_CANDIDATE_READBACK_GREEN_SOURCE_HELD' else 0}")
    print(f"  MSG-022AB savepoint present: {1 if ab_savepoint_ok else 0}")
    print(f"  candidate message rows: {len(message_rows)}")
    print(f"  candidate text rows: {len(text_rows)}")
    print(f"  target messages after promotion: {target_messages}")
    print(f"  target text rows after promotion: {target_text_rows}")
    print(f"  active replacement plan created: {1 if status == STATUS_GREEN else 0}")
    print("  source files mutated: 0")
    print("  active catalog mutation observed: 0")
    print("  HELP DATA mutation observed: 0")
    print("  CMDHELPCHK mutation observed: 0")
    print(f"  next gate: {NEXT_GATE}")
    print(f"  reports: {reports}")
    return 0 if status == STATUS_GREEN else 2

if __name__ == "__main__":
    raise SystemExit(main())
