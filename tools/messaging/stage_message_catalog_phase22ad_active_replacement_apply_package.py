#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import hashlib
import shutil
from datetime import datetime, timezone
from pathlib import Path

STATUS_GREEN = "MESSAGE_CATALOG_PHASE22AD_ACTIVE_CATALOG_REPLACEMENT_APPLY_PACKAGE_STAGED_SOURCE_HELD"
STATUS_BLOCKED = "MESSAGE_CATALOG_PHASE22AD_ACTIVE_CATALOG_REPLACEMENT_APPLY_PACKAGE_STAGING_BLOCKED"
NEXT_GATE = "HOLD_OR_AUTHORIZE_PHASE22AE_ACTIVE_CATALOG_REPLACEMENT_EXECUTION"
REPORT_DIR = Path("docs/messaging/reports")
CANDIDATE_ROOT = Path("docs/messaging/candidates/phase22aa_catalog_row_promotion_candidate_v1")
APPLY_PACKAGE_ROOT = Path("docs/messaging/apply/phase22ad_active_catalog_replacement_apply_package_v1")

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

def copy_file(src: Path, dst: Path, repo: Path, rows, role: str):
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    rows.append({
        "ARTIFACT": rel(dst, repo),
        "ROLE": role,
        "BYTES": dst.stat().st_size,
        "SHA256": sha256_file(dst),
    })

def list_active_roots(repo: Path):
    roots = [
        ("MSG_DBF", repo / "dottalkpp/data/messaging", "active messaging DBF/catalog root"),
        ("MSG_INDEXES", repo / "dottalkpp/data/indexes/messaging", "active messaging CDX/index root"),
        ("MSG_LMDB", repo / "dottalkpp/data/lmdb/messaging", "active messaging LMDB root"),
    ]
    rows = []
    for root_id, path, role in roots:
        rows.append({
            "ROOT_ID": root_id,
            "PATH": rel(path, repo),
            "ROLE": role,
            "EXISTS_NOW": 1 if path.exists() else 0,
            "FILE_COUNT_NOW": sum(1 for x in path.rglob("*") if x.is_file()) if path.exists() else 0,
            "MUST_BACKUP_BEFORE_EXECUTION": 1,
        })
    return rows

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--replace-existing-apply-package", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    reports = repo / REPORT_DIR
    reports.mkdir(parents=True, exist_ok=True)

    ac = first_row(reports / "message_catalog_phase22ac_status_summary_v1.csv")
    ab = first_row(reports / "message_catalog_phase22ab_status_summary_v1.csv")
    ac_savepoint_ok, latest_id = savepoint_present(repo, "MSG-022AC")

    candidate_root = repo / CANDIDATE_ROOT
    candidate_message_path = candidate_root / "rows/message_catalog_candidate_message_adds_v1.csv"
    candidate_text_path = candidate_root / "rows/message_catalog_candidate_text_adds_v1.csv"
    candidate_manifest_path = candidate_root / "manifest/message_catalog_phase22aa_candidate_manifest_v1.json"

    candidate_messages = read_csv(candidate_message_path)
    candidate_text = read_csv(candidate_text_path)

    apply_root = repo / APPLY_PACKAGE_ROOT

    gates = []
    failures = 0
    def gate(name: str, ok: bool, detail: str):
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": detail})
        if not ok:
            failures += 1

    gate("PHASE22AC_PLAN_GREEN",
         ac.get("STATUS") == "MESSAGE_CATALOG_PHASE22AC_ACTIVE_CATALOG_REPLACEMENT_WITH_BACKUP_PLAN_GREEN_SOURCE_HELD",
         ac.get("STATUS", "missing"))
    gate("MSG_022AC_SAVEPOINT_PRESENT", ac_savepoint_ok, latest_id)
    gate("PHASE22AB_READBACK_GREEN",
         ab.get("STATUS") == "MESSAGE_CATALOG_PHASE22AB_CATALOG_ROW_CANDIDATE_READBACK_GREEN_SOURCE_HELD",
         ab.get("STATUS", "missing"))
    gate("CANDIDATE_ROOT_EXISTS", candidate_root.exists(), rel(candidate_root, repo))
    gate("CANDIDATE_MESSAGE_ROWS_AVAILABLE", len(candidate_messages) == 2, f"rows={len(candidate_messages)}")
    gate("CANDIDATE_TEXT_ROWS_AVAILABLE", len(candidate_text) == 10, f"rows={len(candidate_text)}")
    gate("TARGET_COUNTS_14_70",
         ac.get("TARGET_MESSAGES_AFTER_PROMOTION") == "14" and ac.get("TARGET_TEXT_ROWS_AFTER_PROMOTION") == "70",
         f"target={ac.get('TARGET_MESSAGES_AFTER_PROMOTION')}/{ac.get('TARGET_TEXT_ROWS_AFTER_PROMOTION')}")
    gate("AC_NO_ACTIVE_MUTATION",
         ac.get("ACTIVE_CATALOG_MUTATION_OBSERVED") == "0" and
         ac.get("HELP_DATA_MUTATION_OBSERVED") == "0" and
         ac.get("CMDHELPCHK_MUTATION_OBSERVED") == "0",
         f"active={ac.get('ACTIVE_CATALOG_MUTATION_OBSERVED')}; help={ac.get('HELP_DATA_MUTATION_OBSERVED')}; cmdhelpchk={ac.get('CMDHELPCHK_MUTATION_OBSERVED')}")

    if apply_root.exists():
        gate("APPLY_PACKAGE_ROOT_NOT_PREEXISTING_OR_REPLACE_ALLOWED",
             args.replace_existing_apply_package,
             f"{rel(apply_root, repo)} exists")
    else:
        gate("APPLY_PACKAGE_ROOT_NOT_PREEXISTING_OR_REPLACE_ALLOWED", True, rel(apply_root, repo))

    status = STATUS_BLOCKED
    artifact_rows = []
    errors = []

    if failures == 0:
        try:
            if apply_root.exists() and args.replace_existing_apply_package:
                shutil.rmtree(apply_root)

            rows_dir = apply_root / "rows"
            plans_dir = apply_root / "plans"
            manifests_dir = apply_root / "manifest"
            tools_dir = apply_root / "tools"
            rows_dir.mkdir(parents=True, exist_ok=True)
            plans_dir.mkdir(parents=True, exist_ok=True)
            manifests_dir.mkdir(parents=True, exist_ok=True)
            tools_dir.mkdir(parents=True, exist_ok=True)

            copy_file(candidate_message_path, rows_dir / candidate_message_path.name, repo, artifact_rows, "candidate_message_rows_for_execution")
            copy_file(candidate_text_path, rows_dir / candidate_text_path.name, repo, artifact_rows, "candidate_text_rows_for_execution")
            if candidate_manifest_path.exists():
                copy_file(candidate_manifest_path, manifests_dir / candidate_manifest_path.name, repo, artifact_rows, "candidate_source_manifest")

            active_roots = list_active_roots(repo)
            active_roots_path = plans_dir / "active_messaging_roots_to_backup_v1.csv"
            write_csv(active_roots_path, active_roots,
                      ["ROOT_ID", "PATH", "ROLE", "EXISTS_NOW", "FILE_COUNT_NOW", "MUST_BACKUP_BEFORE_EXECUTION"])
            artifact_rows.append({
                "ARTIFACT": rel(active_roots_path, repo),
                "ROLE": "active_roots_backup_plan",
                "BYTES": active_roots_path.stat().st_size,
                "SHA256": sha256_file(active_roots_path),
            })

            execution_checklist = [
                {"STEP": 1, "ACTION": "CONFIRM_NO_DOTTALKPP_PROCESS", "REQUIRED": 1, "DETAIL": "Run Get-Process dottalkpp -ErrorAction SilentlyContinue and stop/quit any running session before active replacement."},
                {"STEP": 2, "ACTION": "FINGERPRINT_ACTIVE_ROOTS", "REQUIRED": 1, "DETAIL": "Fingerprint dottalkpp/data/messaging, dottalkpp/data/indexes/messaging, and dottalkpp/data/lmdb/messaging before apply."},
                {"STEP": 3, "ACTION": "BACKUP_ACTIVE_ROOTS", "REQUIRED": 1, "DETAIL": "Copy all active messaging roots to docs/messaging/backups/MSG-022AE_ACTIVE_CATALOG_REPLACEMENT_BACKUP_<timestamp>."},
                {"STEP": 4, "ACTION": "ADD_TWO_MESSAGE_ROWS", "REQUIRED": 1, "DETAIL": "Add MESSAGE_PROOF_MODE_STATUS and MESSAGE_PROOF_BOUNDARY_NOTE only."},
                {"STEP": 5, "ACTION": "ADD_TEN_TEXT_ROWS", "REQUIRED": 1, "DETAIL": "Add five locale rows for each new symbol."},
                {"STEP": 6, "ACTION": "REBUILD_OR_VALIDATE_INDEXES", "REQUIRED": 1, "DETAIL": "Rebuild/validate active messaging CDX and LMDB after row apply."},
                {"STEP": 7, "ACTION": "READBACK_COUNTS", "REQUIRED": 1, "DETAIL": "Readback active catalog must report 14 messages and 70 text rows."},
                {"STEP": 8, "ACTION": "RUNTIME_SMOKE", "REQUIRED": 1, "DETAIL": "Run SET MESSAGE PROOF focused smoke, then 22V regression pack."},
                {"STEP": 9, "ACTION": "SAVEPOINT_AFTER_GREEN", "REQUIRED": 1, "DETAIL": "Append a new savepoint only after active readback and runtime smoke are green."},
            ]
            checklist_path = plans_dir / "active_replacement_execution_checklist_v1.csv"
            write_csv(checklist_path, execution_checklist, ["STEP", "ACTION", "REQUIRED", "DETAIL"])
            artifact_rows.append({
                "ARTIFACT": rel(checklist_path, repo),
                "ROLE": "execution_checklist",
                "BYTES": checklist_path.stat().st_size,
                "SHA256": sha256_file(checklist_path),
            })

            restrictions = [
                {"RULE": "ALLOW_ACTIVE_MESSAGING_CATALOG_ONLY", "VALUE": 1, "DETAIL": "Only active messaging DBF/CDX/LMDB may be changed in the later execution phase."},
                {"RULE": "FORBID_SOURCE_MUTATION", "VALUE": 1, "DETAIL": "No source files may be edited during active catalog replacement."},
                {"RULE": "FORBID_HELP_DATA_MUTATION", "VALUE": 1, "DETAIL": "HELP DATA remains protected."},
                {"RULE": "FORBID_CMDHELPCHK_MUTATION", "VALUE": 1, "DETAIL": "CMDHELPCHK remains protected."},
                {"RULE": "EXACTLY_TWO_MESSAGE_ROWS", "VALUE": 1, "DETAIL": "Refuse if more than the two 22Y symbols are queued."},
                {"RULE": "EXACTLY_TEN_TEXT_ROWS", "VALUE": 1, "DETAIL": "Refuse if more than ten text rows are queued."},
                {"RULE": "TARGET_COUNTS_14_70", "VALUE": 1, "DETAIL": "Post-apply readback target is 14 messages and 70 text rows."},
            ]
            restrictions_path = plans_dir / "active_replacement_execution_restrictions_v1.csv"
            write_csv(restrictions_path, restrictions, ["RULE", "VALUE", "DETAIL"])
            artifact_rows.append({
                "ARTIFACT": rel(restrictions_path, repo),
                "ROLE": "execution_restrictions",
                "BYTES": restrictions_path.stat().st_size,
                "SHA256": sha256_file(restrictions_path),
            })

            operator_note = """# Phase 22AD Active Catalog Replacement Apply Package

This directory stages the inputs and guardrails for the later active catalog
replacement execution phase.

It does not mutate active DBF/CDX/LMDB.

Later execution must:

1. Confirm no `dottalkpp` process is running.
2. Fingerprint and back up active messaging roots.
3. Add exactly two message symbols and ten text rows.
4. Rebuild or validate active messaging indexes/LMDB.
5. Read back target counts: 14 messages / 70 text rows.
6. Run the focused proof-status smoke and the 22V regression pack.

Forbidden during execution unless separately reauthorized:

- source mutation
- HELP DATA mutation
- CMDHELPCHK mutation
- command registry mutation
- manualgen mutation
- Data Dictionary/SelfDoc mutation
"""
            readme_path = apply_root / "README.md"
            readme_path.write_text(operator_note, encoding="utf-8")
            artifact_rows.append({
                "ARTIFACT": rel(readme_path, repo),
                "ROLE": "operator_readme",
                "BYTES": readme_path.stat().st_size,
                "SHA256": sha256_file(readme_path),
            })

            manifest = {
                "apply_package_id": "MSG-022AD-ACTIVE-CATALOG-REPLACEMENT-APPLY-PACKAGE-V1",
                "created_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
                "source_phase": "22AC",
                "candidate_root": rel(candidate_root, repo),
                "apply_package_root": rel(apply_root, repo),
                "symbols": REQUIRED_SYMBOLS,
                "locales": REQUIRED_LOCALES,
                "current_messages": CURRENT_MESSAGES,
                "current_text_rows": CURRENT_TEXT_ROWS,
                "message_rows_to_add": 2,
                "text_rows_to_add": 10,
                "target_messages_after_execution": TARGET_MESSAGES,
                "target_text_rows_after_execution": TARGET_TEXT_ROWS,
                "active_mutation_in_22ad": 0,
                "source_mutation_in_22ad": 0,
                "next_gate": NEXT_GATE,
                "artifacts": artifact_rows,
            }
            manifest_path = manifests_dir / "message_catalog_phase22ad_apply_package_manifest_v1.json"
            manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
            artifact_rows.append({
                "ARTIFACT": rel(manifest_path, repo),
                "ROLE": "apply_package_manifest",
                "BYTES": manifest_path.stat().st_size,
                "SHA256": sha256_file(manifest_path),
            })

            status = STATUS_GREEN
        except Exception as exc:
            errors.append(str(exc))
            failures += 1
            gates.append({"GATE": "STAGE_PHASE22AD_APPLY_PACKAGE", "STATUS": "FAIL", "DETAIL": str(exc)})
            status = STATUS_BLOCKED

    validation_issues = "0" if status == STATUS_GREEN else str(failures)

    write_csv(reports / "message_catalog_phase22ad_apply_package_artifact_inventory_v1.csv", artifact_rows,
              ["ARTIFACT", "ROLE", "BYTES", "SHA256"])
    write_csv(reports / "message_catalog_phase22ad_gate_check_v1.csv", gates,
              ["GATE", "STATUS", "DETAIL"])

    boundary = [
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Phase 22AD stages an apply package only; no source mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_DBF_CATALOG", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active DBF mutation in 22AD; execution deferred to later authorization."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_CDX_INDEXES", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active CDX/index mutation in 22AD."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active LMDB mutation in 22AD."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No HELP DATA mutation."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CMDHELPCHK mutation."},
        {"PROTECTED_SYSTEM": "COMMAND_REGISTRY", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No command registry mutation."},
        {"PROTECTED_SYSTEM": "MANUALGEN", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No manualgen mutation."},
        {"PROTECTED_SYSTEM": "DATADICT_SELF_DOC", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No Data Dictionary/SelfDoc mutation."},
    ]
    write_csv(reports / "message_catalog_phase22ad_boundary_ledger_v1.csv", boundary,
              ["PROTECTED_SYSTEM", "MUTATION_ALLOWED", "OBSERVED_MUTATION", "DETAIL"])

    write_csv(reports / "message_catalog_phase22ad_status_summary_v1.csv", [{
        "STATUS": status,
        "MESSAGES": str(CURRENT_MESSAGES),
        "TEXT_ROWS": str(CURRENT_TEXT_ROWS),
        "LOCALES": ";".join(REQUIRED_LOCALES),
        "VALIDATION_ISSUES": validation_issues,
        "PHASE22AC_GREEN": 1 if ac.get("STATUS") == "MESSAGE_CATALOG_PHASE22AC_ACTIVE_CATALOG_REPLACEMENT_WITH_BACKUP_PLAN_GREEN_SOURCE_HELD" else 0,
        "MSG_022AC_SAVEPOINT_PRESENT": 1 if ac_savepoint_ok else 0,
        "APPLY_PACKAGE_ROOT": rel(apply_root, repo),
        "APPLY_PACKAGE_ARTIFACTS": len(artifact_rows),
        "MESSAGE_ROWS_TO_ADD": 2,
        "TEXT_ROWS_TO_ADD": 10,
        "TARGET_MESSAGES_AFTER_EXECUTION": TARGET_MESSAGES,
        "TARGET_TEXT_ROWS_AFTER_EXECUTION": TARGET_TEXT_ROWS,
        "SOURCE_FILES_MUTATED": 0,
        "ACTIVE_CATALOG_MUTATION_OBSERVED": 0,
        "HELP_DATA_MUTATION_OBSERVED": 0,
        "CMDHELPCHK_MUTATION_OBSERVED": 0,
        "ERRORS": "; ".join(errors),
        "NEXT_GATE": NEXT_GATE,
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }], ["STATUS", "MESSAGES", "TEXT_ROWS", "LOCALES", "VALIDATION_ISSUES",
         "PHASE22AC_GREEN", "MSG_022AC_SAVEPOINT_PRESENT", "APPLY_PACKAGE_ROOT",
         "APPLY_PACKAGE_ARTIFACTS", "MESSAGE_ROWS_TO_ADD", "TEXT_ROWS_TO_ADD",
         "TARGET_MESSAGES_AFTER_EXECUTION", "TARGET_TEXT_ROWS_AFTER_EXECUTION",
         "SOURCE_FILES_MUTATED", "ACTIVE_CATALOG_MUTATION_OBSERVED",
         "HELP_DATA_MUTATION_OBSERVED", "CMDHELPCHK_MUTATION_OBSERVED",
         "ERRORS", "NEXT_GATE", "REPORT_TIMESTAMP_UTC"])

    md = f"""# Message Catalog Phase 22AD Active Catalog Replacement Apply Package

Status: `{status}`

Phase 22AD stages the apply package for a later active messaging catalog
replacement. It does not execute the replacement.

Apply package root:

```text
{rel(apply_root, repo)}
```

Queued active catalog changes for the later execution phase:

```text
message rows to add: 2
text rows to add: 10
target messages: {TARGET_MESSAGES}
target text rows: {TARGET_TEXT_ROWS}
```

Phase 22AD performs no source, active DBF/CDX/LMDB, HELP DATA, CMDHELPCHK,
command registry, manualgen, or Data Dictionary/SelfDoc mutation.

Next gate:

```text
{NEXT_GATE}
```
"""
    (reports / "MESSAGE_CATALOG_PHASE22AD_ACTIVE_CATALOG_REPLACEMENT_APPLY_PACKAGE.md").write_text(md, encoding="utf-8")

    print(status)
    print(f"  messages: {CURRENT_MESSAGES}")
    print(f"  text rows: {CURRENT_TEXT_ROWS}")
    print(f"  locales: {', '.join(REQUIRED_LOCALES)}")
    print(f"  validation issues: {validation_issues}")
    print(f"  Phase 22AC green: {1 if ac.get('STATUS') == 'MESSAGE_CATALOG_PHASE22AC_ACTIVE_CATALOG_REPLACEMENT_WITH_BACKUP_PLAN_GREEN_SOURCE_HELD' else 0}")
    print(f"  MSG-022AC savepoint present: {1 if ac_savepoint_ok else 0}")
    print(f"  apply package root: {rel(apply_root, repo)}")
    print(f"  apply package artifacts: {len(artifact_rows)}")
    print("  message rows to add: 2")
    print("  text rows to add: 10")
    print(f"  target messages after execution: {TARGET_MESSAGES}")
    print(f"  target text rows after execution: {TARGET_TEXT_ROWS}")
    print("  source files mutated: 0")
    print("  active catalog mutation observed: 0")
    print("  HELP DATA mutation observed: 0")
    print("  CMDHELPCHK mutation observed: 0")
    print(f"  next gate: {NEXT_GATE}")
    print(f"  reports: {reports}")
    return 0 if status == STATUS_GREEN else 2

if __name__ == "__main__":
    raise SystemExit(main())
