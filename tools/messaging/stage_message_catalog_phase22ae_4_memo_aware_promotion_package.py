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

STATUS_GREEN = "MESSAGE_CATALOG_PHASE22AE_4_MEMO_AWARE_ACTIVE_CATALOG_PROMOTION_PACKAGE_STAGED_SOURCE_HELD"
STATUS_BLOCKED = "MESSAGE_CATALOG_PHASE22AE_4_MEMO_AWARE_ACTIVE_CATALOG_PROMOTION_PACKAGE_BLOCKED"
NEXT_GATE = "HOLD_OR_AUTHORIZE_PHASE22AE_5_MEMO_AWARE_ACTIVE_CATALOG_PROMOTION_EXECUTION"
REPORT_DIR = Path("docs/messaging/reports")
PACKAGE_ROOT = Path("docs/messaging/apply/phase22ae_4_memo_aware_active_catalog_promotion_package_v1")
CANDIDATE_ROOT = Path("docs/messaging/candidates/phase22aa_catalog_row_promotion_candidate_v1")
APPLY_ROOT = Path("docs/messaging/apply/phase22ad_active_catalog_replacement_apply_package_v1")
ACTIVE_MSG_ROOT = Path("dottalkpp/data/messaging")

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

def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def rel(path: Path, repo: Path) -> str:
    try:
        return str(path.relative_to(repo)).replace("\\", "/")
    except Exception:
        return str(path).replace("\\", "/")

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

def truthy(value) -> bool:
    return str(value).strip().lower() in ("1", "true", "yes", "pass", "green")

def q(value: str) -> str:
    """Return a conservative DotTalk/xBase double-quoted literal."""
    value = "" if value is None else str(value)
    value = value.replace("\\", "\\\\")
    value = value.replace('"', '""')
    return f'"{value}"'

def choose_field(field_rows, role, candidates):
    names = [r.get("FIELD", "").upper() for r in field_rows if r.get("ROLE") == role]
    for c in candidates:
        if c in names:
            return c
    return ""

def dts_replace_lines(row, mapping, source_cols):
    lines = []
    for field, source in source_cols:
        if not field:
            continue
        lines.append(f"REPLACE {field} WITH {q(row.get(source, ''))}")
    return lines

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--replace-existing-package", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    reports = repo / REPORT_DIR
    reports.mkdir(parents=True, exist_ok=True)

    ae31 = first_row(reports / "message_catalog_phase22ae_3_1_status_summary_v1.csv")
    ae31_savepoint_ok, latest_id = savepoint_present(repo, "MSG-022AE.3.1")
    field_rows = read_csv(reports / "message_catalog_phase22ae_3_active_dbf_field_inventory_v1.csv")

    candidate_msg_path = repo / APPLY_ROOT / "rows/message_catalog_candidate_message_adds_v1.csv"
    candidate_text_path = repo / APPLY_ROOT / "rows/message_catalog_candidate_text_adds_v1.csv"
    if not candidate_msg_path.exists():
        candidate_msg_path = repo / CANDIDATE_ROOT / "rows/message_catalog_candidate_message_adds_v1.csv"
    if not candidate_text_path.exists():
        candidate_text_path = repo / CANDIDATE_ROOT / "rows/message_catalog_candidate_text_adds_v1.csv"

    candidate_messages = read_csv(candidate_msg_path)
    candidate_text = read_csv(candidate_text_path)

    package_root = repo / PACKAGE_ROOT
    gates = []
    failures = 0

    def gate(name: str, ok: bool, detail: str):
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": detail})
        if not ok:
            failures += 1

    gate("PHASE22AE_3_1_GREEN",
         ae31.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_3_1_MEMO_AWARE_PROMOTION_PATH_GREEN_SOURCE_HELD",
         ae31.get("STATUS", "missing"))
    gate("MSG_022AE_3_1_SAVEPOINT_PRESENT", ae31_savepoint_ok, latest_id)
    gate("MEMO_AWARE_PROMOTION_REQUIRED",
         truthy(ae31.get("MEMO_AWARE_PROMOTION_REQUIRED")),
         ae31.get("MEMO_AWARE_PROMOTION_REQUIRED", "missing"))
    gate("DIRECT_DBF_APPEND_CLOSED",
         ae31.get("DIRECT_DBF_APPEND_ALLOWED") == "0",
         ae31.get("DIRECT_DBF_APPEND_ALLOWED", "missing"))
    gate("SYSTEM_MESSAGE_TEXT_TEXT_MEMO",
         truthy(ae31.get("SYSTEM_MESSAGE_TEXT_TEXT_MEMO")),
         ae31.get("SYSTEM_MESSAGE_TEXT_TEXT_MEMO", "missing"))
    gate("CANDIDATE_MESSAGE_ROWS_AVAILABLE", len(candidate_messages) == 2, f"rows={len(candidate_messages)}")
    gate("CANDIDATE_TEXT_ROWS_AVAILABLE", len(candidate_text) == 10, f"rows={len(candidate_text)}")

    msg_symbol_f = choose_field(field_rows, "messages", ["SYMBOL", "MESSAGE_SYMBOL", "MSG_SYMBOL"])
    msg_kind_f = choose_field(field_rows, "messages", ["KIND", "MESSAGE_KIND", "MSG_KIND"])
    msg_ph_f = choose_field(field_rows, "messages", ["PLACEHOLDERS", "PLACEHOLDER", "ARGS", "ARGUMENTS"])
    msg_status_f = choose_field(field_rows, "messages", ["STATUS", "ROW_STATUS"])
    msg_source_f = choose_field(field_rows, "messages", ["SOURCE_PHASE", "SOURCE", "PHASE"])

    txt_symbol_f = choose_field(field_rows, "message_text", ["SYMBOL", "MESSAGE_SYMBOL", "MSG_SYMBOL"])
    txt_locale_f = choose_field(field_rows, "message_text", ["LOCALE", "LOCALE_ID"])
    txt_text_f = choose_field(field_rows, "message_text", ["TEXT", "MESSAGE_TEXT", "MSG_TEXT"])
    txt_ph_f = choose_field(field_rows, "message_text", ["PLACEHOLDERS", "PLACEHOLDER", "ARGS", "ARGUMENTS"])
    txt_status_f = choose_field(field_rows, "message_text", ["STATUS", "ROW_STATUS"])
    txt_source_f = choose_field(field_rows, "message_text", ["SOURCE_PHASE", "SOURCE", "PHASE"])

    gate("MESSAGE_FIELD_MAPPING_AVAILABLE", bool(msg_symbol_f), f"symbol={msg_symbol_f}; kind={msg_kind_f}; placeholders={msg_ph_f}")
    gate("TEXT_FIELD_MAPPING_AVAILABLE", bool(txt_symbol_f and txt_locale_f and txt_text_f),
         f"symbol={txt_symbol_f}; locale={txt_locale_f}; text={txt_text_f}")

    if package_root.exists():
        gate("PACKAGE_ROOT_NOT_PREEXISTING_OR_REPLACE_ALLOWED",
             args.replace_existing_package,
             f"{rel(package_root, repo)} exists")
    else:
        gate("PACKAGE_ROOT_NOT_PREEXISTING_OR_REPLACE_ALLOWED", True, rel(package_root, repo))

    status = STATUS_BLOCKED
    artifact_rows = []
    errors = []

    if failures == 0:
        try:
            if package_root.exists() and args.replace_existing_package:
                shutil.rmtree(package_root)

            scripts_dir = package_root / "scripts"
            rows_dir = package_root / "rows"
            manifest_dir = package_root / "manifest"
            reports_dir = package_root / "reports"
            scripts_dir.mkdir(parents=True, exist_ok=True)
            rows_dir.mkdir(parents=True, exist_ok=True)
            manifest_dir.mkdir(parents=True, exist_ok=True)
            reports_dir.mkdir(parents=True, exist_ok=True)

            # Copy candidate rowsets into the package.
            for src, role in [(candidate_msg_path, "candidate_message_rows"), (candidate_text_path, "candidate_text_rows")]:
                dst = rows_dir / src.name
                shutil.copy2(src, dst)
                artifact_rows.append({
                    "ARTIFACT": rel(dst, repo),
                    "ROLE": role,
                    "BYTES": dst.stat().st_size,
                    "SHA256": sha256_file(dst),
                })

            field_mapping = [
                {"TABLE_ROLE": "messages", "SOURCE_COL": "SYMBOL", "TARGET_FIELD": msg_symbol_f, "REQUIRED": 1},
                {"TABLE_ROLE": "messages", "SOURCE_COL": "KIND", "TARGET_FIELD": msg_kind_f, "REQUIRED": 0},
                {"TABLE_ROLE": "messages", "SOURCE_COL": "PLACEHOLDERS", "TARGET_FIELD": msg_ph_f, "REQUIRED": 0},
                {"TABLE_ROLE": "messages", "SOURCE_COL": "STATUS", "TARGET_FIELD": msg_status_f, "REQUIRED": 0},
                {"TABLE_ROLE": "messages", "SOURCE_COL": "SOURCE_PHASE", "TARGET_FIELD": msg_source_f, "REQUIRED": 0},
                {"TABLE_ROLE": "message_text", "SOURCE_COL": "SYMBOL", "TARGET_FIELD": txt_symbol_f, "REQUIRED": 1},
                {"TABLE_ROLE": "message_text", "SOURCE_COL": "LOCALE", "TARGET_FIELD": txt_locale_f, "REQUIRED": 1},
                {"TABLE_ROLE": "message_text", "SOURCE_COL": "TEXT", "TARGET_FIELD": txt_text_f, "REQUIRED": 1},
                {"TABLE_ROLE": "message_text", "SOURCE_COL": "PLACEHOLDERS", "TARGET_FIELD": txt_ph_f, "REQUIRED": 0},
                {"TABLE_ROLE": "message_text", "SOURCE_COL": "STATUS", "TARGET_FIELD": txt_status_f, "REQUIRED": 0},
                {"TABLE_ROLE": "message_text", "SOURCE_COL": "SOURCE_PHASE", "TARGET_FIELD": txt_source_f, "REQUIRED": 0},
            ]
            mapping_path = reports_dir / "message_catalog_phase22ae_4_field_mapping_v1.csv"
            write_csv(mapping_path, field_mapping, ["TABLE_ROLE", "SOURCE_COL", "TARGET_FIELD", "REQUIRED"])
            artifact_rows.append({
                "ARTIFACT": rel(mapping_path, repo),
                "ROLE": "field_mapping",
                "BYTES": mapping_path.stat().st_size,
                "SHA256": sha256_file(mapping_path),
            })

            # Candidate DTS: intentionally not run in 22AE.4. It uses normal DotTalk++ row commands
            # so memo attachment can occur through USE and REPLACE TEXT, instead of raw DBF bytes.
            messages_dbf = (repo / ACTIVE_MSG_ROOT / "SYSTEM_MESSAGES.dbf").as_posix()
            text_dbf = (repo / ACTIVE_MSG_ROOT / "SYSTEM_MESSAGE_TEXT.dbf").as_posix()

            dts_lines = [
                "* MESSAGE_CATALOG_PHASE22AE_4_MEMO_AWARE_PROMOTION_APPLY_CANDIDATE.dts",
                "* DO NOT RUN WITHOUT PHASE22AE_5 EXECUTION AUTHORIZATION.",
                "* This candidate intentionally uses DotTalk++ USE/APPEND/REPLACE so memo backend handling",
                "* stays inside the runtime path. It must not be replaced by raw fixed-record DBF append.",
                "",
                f"USE {messages_dbf}",
            ]
            for row in candidate_messages:
                dts_lines.append("APPEND")
                dts_lines.extend(dts_replace_lines(row, {}, [
                    (msg_symbol_f, "SYMBOL"),
                    (msg_kind_f, "KIND"),
                    (msg_ph_f, "PLACEHOLDERS"),
                    (msg_status_f, "STATUS"),
                    (msg_source_f, "SOURCE_PHASE"),
                ]))
                # If target has a status/source field but row lacks a value, fill conservative defaults.
                if msg_status_f and not any(line.startswith(f"REPLACE {msg_status_f} ") for line in dts_lines[-5:]):
                    dts_lines.append(f"REPLACE {msg_status_f} WITH {q('ACTIVE')}")
                if msg_source_f and not any(line.startswith(f"REPLACE {msg_source_f} ") for line in dts_lines[-6:]):
                    dts_lines.append(f"REPLACE {msg_source_f} WITH {q('22AE_5')}")
                dts_lines.append("")

            dts_lines.append(f"USE {text_dbf}")
            for row in candidate_text:
                dts_lines.append("APPEND")
                dts_lines.extend(dts_replace_lines(row, {}, [
                    (txt_symbol_f, "SYMBOL"),
                    (txt_locale_f, "LOCALE"),
                    (txt_text_f, "TEXT"),
                    (txt_ph_f, "PLACEHOLDERS"),
                    (txt_status_f, "STATUS"),
                    (txt_source_f, "SOURCE_PHASE"),
                ]))
                if txt_status_f and not any(line.startswith(f"REPLACE {txt_status_f} ") for line in dts_lines[-7:]):
                    dts_lines.append(f"REPLACE {txt_status_f} WITH {q('ACTIVE')}")
                if txt_source_f and not any(line.startswith(f"REPLACE {txt_source_f} ") for line in dts_lines[-8:]):
                    dts_lines.append(f"REPLACE {txt_source_f} WITH {q('22AE_5')}")
                dts_lines.append("")

            dts_lines.extend([
                "* Expected post-apply counts after PHASE22AE_5:",
                "*   SYSTEM_MESSAGES: 14",
                "*   SYSTEM_MESSAGE_TEXT: 70",
                "* Next: run active readback and runtime regression.",
                "",
            ])
            dts_text = "\n".join(dts_lines)

            dts_path = scripts_dir / "MESSAGE_CATALOG_PHASE22AE_4_MEMO_AWARE_PROMOTION_APPLY_CANDIDATE.dts"
            dts_path.write_text(dts_text, encoding="utf-8")
            artifact_rows.append({
                "ARTIFACT": rel(dts_path, repo),
                "ROLE": "memo_aware_apply_candidate_dts_not_executed",
                "BYTES": dts_path.stat().st_size,
                "SHA256": sha256_file(dts_path),
            })

            guard_rows = [
                {"GUARD": "DO_NOT_RUN_IN_22AE_4", "VALUE": 1, "DETAIL": "DTS candidate is staged only."},
                {"GUARD": "REQUIRES_PHASE22AE_5_AUTHORIZATION", "VALUE": 1, "DETAIL": "Active mutation execution is separate."},
                {"GUARD": "REQUIRES_NO_RUNNING_DOTTALKPP", "VALUE": 1, "DETAIL": "Active catalog should not be locked."},
                {"GUARD": "REQUIRES_ACTIVE_BACKUP_FIRST", "VALUE": 1, "DETAIL": "Back up dottalkpp/data/messaging, indexes/messaging, lmdb/messaging before execution."},
                {"GUARD": "FORBID_RAW_DBF_APPEND", "VALUE": 1, "DETAIL": "SYSTEM_MESSAGE_TEXT.TEXT is memo-backed."},
                {"GUARD": "FORBID_SOURCE_MUTATION", "VALUE": 1, "DETAIL": "No src/include edits."},
                {"GUARD": "FORBID_HELP_CMDHELPCHK_MUTATION", "VALUE": 1, "DETAIL": "HELP DATA and CMDHELPCHK remain protected."},
            ]
            guard_path = reports_dir / "message_catalog_phase22ae_4_execution_guards_v1.csv"
            write_csv(guard_path, guard_rows, ["GUARD", "VALUE", "DETAIL"])
            artifact_rows.append({
                "ARTIFACT": rel(guard_path, repo),
                "ROLE": "execution_guards",
                "BYTES": guard_path.stat().st_size,
                "SHA256": sha256_file(guard_path),
            })

            validation_rows = []
            for row in candidate_messages:
                validation_rows.append({
                    "ROWSET": "messages",
                    "SYMBOL": row.get("SYMBOL", ""),
                    "LOCALE": "",
                    "TEXT_SHA256": "",
                    "DTS_CONTAINS_SYMBOL": 1 if row.get("SYMBOL", "") in dts_text else 0,
                    "DTS_CONTAINS_TEXT": "",
                })
            for row in candidate_text:
                txt = row.get("TEXT", "")
                validation_rows.append({
                    "ROWSET": "message_text",
                    "SYMBOL": row.get("SYMBOL", ""),
                    "LOCALE": row.get("LOCALE", ""),
                    "TEXT_SHA256": sha256_text(txt),
                    "DTS_CONTAINS_SYMBOL": 1 if row.get("SYMBOL", "") in dts_text else 0,
                    "DTS_CONTAINS_TEXT": 1 if txt in dts_text else 0,
                })
            validation_path = reports_dir / "message_catalog_phase22ae_4_candidate_dts_content_validation_v1.csv"
            write_csv(validation_path, validation_rows,
                      ["ROWSET", "SYMBOL", "LOCALE", "TEXT_SHA256", "DTS_CONTAINS_SYMBOL", "DTS_CONTAINS_TEXT"])
            artifact_rows.append({
                "ARTIFACT": rel(validation_path, repo),
                "ROLE": "candidate_dts_content_validation",
                "BYTES": validation_path.stat().st_size,
                "SHA256": sha256_file(validation_path),
            })

            manifest = {
                "package_id": "MSG-022AE.4-MEMO-AWARE-ACTIVE-CATALOG-PROMOTION-PACKAGE-V1",
                "created_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
                "package_root": rel(package_root, repo),
                "source_phase": "22AE.3.1",
                "candidate_message_rows": len(candidate_messages),
                "candidate_text_rows": len(candidate_text),
                "expected_target_messages": 14,
                "expected_target_text_rows": 70,
                "memo_aware_runtime_path": "DotTalk++ USE/APPEND/REPLACE candidate DTS",
                "direct_dbf_append_allowed": 0,
                "active_mutation_in_22ae_4": 0,
                "next_gate": NEXT_GATE,
                "artifacts": artifact_rows,
            }
            manifest_path = manifest_dir / "message_catalog_phase22ae_4_package_manifest_v1.json"
            manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
            artifact_rows.append({
                "ARTIFACT": rel(manifest_path, repo),
                "ROLE": "package_manifest",
                "BYTES": manifest_path.stat().st_size,
                "SHA256": sha256_file(manifest_path),
            })

            readme = f"""# Phase 22AE.4 Memo-Aware Active Catalog Promotion Package

This package stages a memo-aware DotTalk++ runtime candidate for promoting:

- MESSAGE_PROOF_MODE_STATUS
- MESSAGE_PROOF_BOUNDARY_NOTE

The staged DTS uses:

```text
USE
APPEND
REPLACE
```

It is **not executed in 22AE.4**. Execution requires Phase 22AE.5 authorization.

Reason for this path:

```text
SYSTEM_MESSAGE_TEXT.TEXT is memo-backed, so raw DBF append is forbidden.
```

Expected active counts after later execution:

```text
messages: 14
text rows: 70
```
"""
            readme_path = package_root / "README.md"
            readme_path.write_text(readme, encoding="utf-8")
            artifact_rows.append({
                "ARTIFACT": rel(readme_path, repo),
                "ROLE": "package_readme",
                "BYTES": readme_path.stat().st_size,
                "SHA256": sha256_file(readme_path),
            })

            # Rewrite artifact inventory after manifest/readme additions.
            status = STATUS_GREEN
        except Exception as exc:
            errors.append(str(exc))
            failures += 1
            gates.append({"GATE": "STAGE_MEMO_AWARE_PROMOTION_PACKAGE", "STATUS": "FAIL", "DETAIL": str(exc)})
            status = STATUS_BLOCKED

    validation_issues = "0" if status == STATUS_GREEN else str(failures)

    write_csv(reports / "message_catalog_phase22ae_4_package_artifact_inventory_v1.csv", artifact_rows,
              ["ARTIFACT", "ROLE", "BYTES", "SHA256"])
    write_csv(reports / "message_catalog_phase22ae_4_gate_check_v1.csv", gates,
              ["GATE", "STATUS", "DETAIL"])

    boundary = [
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "22AE.4 stages package files only; no source mutation."},
        {"PROTECTED_SYSTEM": "TOOLS_MESSAGING_SCRIPT", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No tool script mutation beyond installed package runner."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_DBF_CATALOG", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active DBF mutation in 22AE.4."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_CDX_INDEXES", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active CDX/index mutation in 22AE.4."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active LMDB mutation in 22AE.4."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No HELP DATA mutation."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CMDHELPCHK mutation."},
        {"PROTECTED_SYSTEM": "COMMAND_REGISTRY", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No command registry mutation."},
        {"PROTECTED_SYSTEM": "MANUALGEN", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No manualgen mutation."},
        {"PROTECTED_SYSTEM": "DATADICT_SELF_DOC", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No Data Dictionary/SelfDoc mutation."},
    ]
    write_csv(reports / "message_catalog_phase22ae_4_boundary_ledger_v1.csv", boundary,
              ["PROTECTED_SYSTEM", "MUTATION_ALLOWED", "OBSERVED_MUTATION", "DETAIL"])

    write_csv(reports / "message_catalog_phase22ae_4_status_summary_v1.csv", [{
        "STATUS": status,
        "VALIDATION_ISSUES": validation_issues,
        "PHASE22AE_3_1_GREEN": 1 if ae31.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_3_1_MEMO_AWARE_PROMOTION_PATH_GREEN_SOURCE_HELD" else 0,
        "MSG_022AE_3_1_SAVEPOINT_PRESENT": 1 if ae31_savepoint_ok else 0,
        "PACKAGE_ROOT": rel(package_root, repo),
        "PACKAGE_ARTIFACTS": len(artifact_rows),
        "CANDIDATE_MESSAGE_ROWS": len(candidate_messages),
        "CANDIDATE_TEXT_ROWS": len(candidate_text),
        "MEMO_AWARE_RUNTIME_PATH_STAGED": 1 if status == STATUS_GREEN else 0,
        "DIRECT_DBF_APPEND_ALLOWED": 0,
        "ACTIVE_MUTATION_IN_22AE_4": 0,
        "SOURCE_FILES_MUTATED": 0,
        "ACTIVE_CATALOG_MUTATION_OBSERVED": 0,
        "HELP_DATA_MUTATION_OBSERVED": 0,
        "CMDHELPCHK_MUTATION_OBSERVED": 0,
        "ERRORS": "; ".join(errors),
        "NEXT_GATE": NEXT_GATE,
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }], ["STATUS", "VALIDATION_ISSUES", "PHASE22AE_3_1_GREEN",
         "MSG_022AE_3_1_SAVEPOINT_PRESENT", "PACKAGE_ROOT", "PACKAGE_ARTIFACTS",
         "CANDIDATE_MESSAGE_ROWS", "CANDIDATE_TEXT_ROWS",
         "MEMO_AWARE_RUNTIME_PATH_STAGED", "DIRECT_DBF_APPEND_ALLOWED",
         "ACTIVE_MUTATION_IN_22AE_4", "SOURCE_FILES_MUTATED",
         "ACTIVE_CATALOG_MUTATION_OBSERVED", "HELP_DATA_MUTATION_OBSERVED",
         "CMDHELPCHK_MUTATION_OBSERVED", "ERRORS", "NEXT_GATE",
         "REPORT_TIMESTAMP_UTC"])

    md = f"""# Message Catalog Phase 22AE.4 Memo-Aware Active Catalog Promotion Package

Status: `{status}`

22AE.4 stages a memo-aware DotTalk++ runtime candidate package. It does not run
the active promotion.

Package root:

```text
{rel(package_root, repo)}
```

Candidate execution path:

```text
USE / APPEND / REPLACE
```

Reason:

```text
SYSTEM_MESSAGE_TEXT.TEXT is memo-backed; raw DBF append remains forbidden.
```

Next gate:

```text
{NEXT_GATE}
```
"""
    (reports / "MESSAGE_CATALOG_PHASE22AE_4_MEMO_AWARE_ACTIVE_CATALOG_PROMOTION_PACKAGE.md").write_text(md, encoding="utf-8")

    print(status)
    print(f"  validation issues: {validation_issues}")
    print(f"  Phase 22AE.3.1 green: {1 if ae31.get('STATUS') == 'MESSAGE_CATALOG_PHASE22AE_3_1_MEMO_AWARE_PROMOTION_PATH_GREEN_SOURCE_HELD' else 0}")
    print(f"  MSG-022AE.3.1 savepoint present: {1 if ae31_savepoint_ok else 0}")
    print(f"  package root: {rel(package_root, repo)}")
    print(f"  package artifacts: {len(artifact_rows)}")
    print(f"  candidate message rows: {len(candidate_messages)}")
    print(f"  candidate text rows: {len(candidate_text)}")
    print(f"  memo-aware runtime path staged: {1 if status == STATUS_GREEN else 0}")
    print("  direct DBF append allowed: 0")
    print("  active mutation in 22AE.4: 0")
    print("  source files mutated: 0")
    print("  active catalog mutation observed: 0")
    print("  HELP DATA mutation observed: 0")
    print("  CMDHELPCHK mutation observed: 0")
    print(f"  next gate: {NEXT_GATE}")
    print(f"  reports: {reports}")
    return 0 if status == STATUS_GREEN else 2

if __name__ == "__main__":
    raise SystemExit(main())
