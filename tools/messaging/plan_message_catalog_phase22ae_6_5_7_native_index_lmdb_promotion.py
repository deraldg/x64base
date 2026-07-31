#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

STATUS_GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_7_NATIVE_INDEX_LMDB_REBUILD_AND_PROMOTION_PLAN_GREEN_SOURCE_HELD"
STATUS_BLOCKED = "MESSAGE_CATALOG_PHASE22AE_6_5_7_NATIVE_INDEX_LMDB_REBUILD_AND_PROMOTION_PLAN_BLOCKED"
NEXT_GATE = "HOLD_OR_AUTHORIZE_PHASE22AE_6_5_8_ACTIVE_BASENAME_CANDIDATE_STAGING_PACKAGE"

REPORT_DIR = Path("docs/messaging/reports")
SOURCE_SANDBOX = Path("docs/messaging/sandbox/phase22ae_6_5_6_1_work_area_select_import_v1/dbf")
CANDIDATE_ROOT = Path("docs/messaging/candidates/phase22ae_6_5_8_active_basename_candidate_v1")
ACTIVE_ROOT = Path("dottalkpp/data/messaging")
ACTIVE_INDEX_ROOT = Path("dottalkpp/data/indexes/messaging")
ACTIVE_LMDB_ROOT = Path("dottalkpp/data/lmdb/messaging")

SOURCE_MESSAGE_DBF = SOURCE_SANDBOX / "MSG6561_MESSAGES_NATIVE_IMPORT.dbf"
SOURCE_TEXT_DBF = SOURCE_SANDBOX / "MSG6561_TEXT_NATIVE_IMPORT.dbf"
SOURCE_TEXT_DTX = SOURCE_SANDBOX / "MSG6561_TEXT_NATIVE_IMPORT.dtx"

TARGET_MESSAGE_DBF = CANDIDATE_ROOT / "dbf/SYSTEM_MESSAGES.dbf"
TARGET_TEXT_DBF = CANDIDATE_ROOT / "dbf/SYSTEM_MESSAGE_TEXT.dbf"
TARGET_TEXT_DTX = CANDIDATE_ROOT / "dbf/SYSTEM_MESSAGE_TEXT.dtx"

def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

def first_row(path: Path) -> dict[str, str]:
    rows = read_csv(path)
    return rows[0] if rows else {}

def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n", extrasaction="ignore")
        w.writeheader()
        for row in rows:
            w.writerow({k: row.get(k, "") for k in fields})

def rel(path: Path, repo: Path) -> str:
    try:
        return str(path.relative_to(repo)).replace("\\", "/")
    except Exception:
        return str(path).replace("\\", "/")

def sha256_file(path: Path) -> str:
    if not path.exists() or not path.is_file():
        return ""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def savepoint_present(repo: Path, savepoint_id: str):
    latest = repo / REPORT_DIR / "message_savepoint_latest_v1.json"
    latest_id = ""
    if latest.exists():
        try:
            latest_id = json.loads(latest.read_text(encoding="utf-8")).get("savepoint_id", "")
        except Exception:
            latest_id = ""
    journal = repo / "docs/messaging/MESSAGING_SAVEPOINT_JOURNAL.md"
    text = journal.read_text(encoding="utf-8", errors="replace") if journal.exists() else ""
    return (latest_id == savepoint_id or savepoint_id in text), latest_id

def file_row(repo: Path, role: str, path: Path) -> dict[str, Any]:
    return {
        "ROLE": role,
        "PATH": rel(path, repo),
        "EXISTS": 1 if path.exists() else 0,
        "BYTES": path.stat().st_size if path.exists() and path.is_file() else "",
        "SHA256": sha256_file(path),
    }

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    reports = repo / REPORT_DIR
    reports.mkdir(parents=True, exist_ok=True)

    summary6562 = first_row(reports / "message_catalog_phase22ae_6_5_6_2_status_summary_v1.csv")
    sp_ok, latest_sp = savepoint_present(repo, "MSG-022AE.6.5.6.2")

    gates = []
    failures = 0
    def gate(name: str, ok: bool, detail: Any):
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": str(detail)})
        if not ok:
            failures += 1

    gate("PHASE22AE_6_5_6_2_GREEN",
         summary6562.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_5_6_2_TEXT_KEY_MEMO_SIDECAR_READBACK_REPAIR_GREEN_SOURCE_HELD",
         summary6562.get("STATUS", "missing"))
    gate("MSG_022AE_6_5_6_2_SAVEPOINT_PRESENT", sp_ok, latest_sp)
    gate("NATIVE_IMPORT_COUNTS_14_70", summary6562.get("COUNTS_14_70") == "1",
         f"{summary6562.get('MESSAGE_ROWS_AFTER','')}/{summary6562.get('TEXT_ROWS_AFTER','')}")
    gate("RAW_KEYS_PROVEN_2_AND_10", summary6562.get("RAW_MESSAGE_KEYS_FOUND") == "2" and summary6562.get("RAW_TEXT_KEYS_FOUND") == "10",
         f"{summary6562.get('RAW_MESSAGE_KEYS_FOUND','')}/{summary6562.get('RAW_TEXT_KEYS_FOUND','')}")
    gate("TEXT_DTX_PROVEN", summary6562.get("TEXT_DTX_EXISTS") == "1" and summary6562.get("TEXT_DTX_GREW_VS_ACTIVE_BASELINE") == "1",
         f"exists={summary6562.get('TEXT_DTX_EXISTS','')}; grew={summary6562.get('TEXT_DTX_GREW_VS_ACTIVE_BASELINE','')}; bytes={summary6562.get('TEXT_DTX_BYTES','')}")
    gate("ACTIVE_BOUNDARY_CLEAN", summary6562.get("BOUNDARY_CLEAN") == "1" and summary6562.get("ACTIVE_CATALOG_MUTATION_OBSERVED") == "0",
         f"boundary={summary6562.get('BOUNDARY_CLEAN','')}; active={summary6562.get('ACTIVE_CATALOG_MUTATION_OBSERVED','')}")
    gate("SOURCE_MESSAGE_DBF_EXISTS", (repo / SOURCE_MESSAGE_DBF).exists(), rel(repo / SOURCE_MESSAGE_DBF, repo))
    gate("SOURCE_TEXT_DBF_EXISTS", (repo / SOURCE_TEXT_DBF).exists(), rel(repo / SOURCE_TEXT_DBF, repo))
    gate("SOURCE_TEXT_DTX_EXISTS", (repo / SOURCE_TEXT_DTX).exists(), rel(repo / SOURCE_TEXT_DTX, repo))

    source_inventory = [
        file_row(repo, "native_import_source_message_dbf", repo / SOURCE_MESSAGE_DBF),
        file_row(repo, "native_import_source_text_dbf", repo / SOURCE_TEXT_DBF),
        file_row(repo, "native_import_source_text_dtx", repo / SOURCE_TEXT_DTX),
    ]
    active_inventory = [
        file_row(repo, "active_message_dbf", repo / ACTIVE_ROOT / "SYSTEM_MESSAGES.dbf"),
        file_row(repo, "active_text_dbf", repo / ACTIVE_ROOT / "SYSTEM_MESSAGE_TEXT.dbf"),
        file_row(repo, "active_text_dtx", repo / ACTIVE_ROOT / "SYSTEM_MESSAGE_TEXT.dtx"),
        file_row(repo, "active_message_cdx", repo / ACTIVE_INDEX_ROOT / "SYSTEM_MESSAGES.cdx"),
        file_row(repo, "active_text_cdx", repo / ACTIVE_INDEX_ROOT / "SYSTEM_MESSAGE_TEXT.cdx"),
    ]

    candidate_artifacts = [
        {"ROLE": "candidate_message_dbf", "SOURCE": rel(repo / SOURCE_MESSAGE_DBF, repo), "TARGET": rel(repo / TARGET_MESSAGE_DBF, repo), "ACTION": "copy_native_imported_dbf_to_active_basename_candidate"},
        {"ROLE": "candidate_text_dbf", "SOURCE": rel(repo / SOURCE_TEXT_DBF, repo), "TARGET": rel(repo / TARGET_TEXT_DBF, repo), "ACTION": "copy_native_imported_dbf_to_active_basename_candidate"},
        {"ROLE": "candidate_text_dtx", "SOURCE": rel(repo / SOURCE_TEXT_DTX, repo), "TARGET": rel(repo / TARGET_TEXT_DTX, repo), "ACTION": "copy_native_imported_memo_sidecar_to_active_basename_candidate"},
        {"ROLE": "candidate_index_root", "SOURCE": "", "TARGET": rel(repo / CANDIDATE_ROOT / "indexes", repo), "ACTION": "future_native_cdx_rebuild_only_after_authorization"},
        {"ROLE": "candidate_lmdb_root", "SOURCE": "", "TARGET": rel(repo / CANDIDATE_ROOT / "lmdb", repo), "ACTION": "future_native_lmdb_rebuild_only_after_authorization"},
    ]

    execution_plan = [
        {"STEP": 1, "PHASE": "6.5.8", "ACTION": "Create active-basename candidate root under docs/messaging/candidates.", "MUTATION_SCOPE": "candidate-only", "ACTIVE_MUTATION": 0},
        {"STEP": 2, "PHASE": "6.5.8", "ACTION": "Copy native-imported sandbox DBF/DTX artifacts to SYSTEM_MESSAGES / SYSTEM_MESSAGE_TEXT active basenames in candidate DBF root.", "MUTATION_SCOPE": "candidate-only", "ACTIVE_MUTATION": 0},
        {"STEP": 3, "PHASE": "6.5.8", "ACTION": "Generate a DotTalk++ candidate readback script that opens candidate SYSTEM_* DBFs by absolute path and proves 14/70 and text sidecar attach.", "MUTATION_SCOPE": "candidate-only/read-only runtime", "ACTIVE_MUTATION": 0},
        {"STEP": 4, "PHASE": "6.5.9", "ACTION": "Run native CDX rebuild for candidate copies only, after explicit authorization and with no active index writes.", "MUTATION_SCOPE": "candidate indexes only", "ACTIVE_MUTATION": 0},
        {"STEP": 5, "PHASE": "6.5.10", "ACTION": "Run native BUILDLMDB for candidate copies only, after candidate CDX proof is green.", "MUTATION_SCOPE": "candidate LMDB only", "ACTIVE_MUTATION": 0},
        {"STEP": 6, "PHASE": "6.5.11", "ACTION": "Run active-basename candidate runtime provider/readback proof in isolated/candidate path before active replacement.", "MUTATION_SCOPE": "candidate/read-only active", "ACTIVE_MUTATION": 0},
        {"STEP": 7, "PHASE": "6.5.12", "ACTION": "Only after explicit authorization, perform backup + active replacement + post-promotion readback + rollback plan.", "MUTATION_SCOPE": "active messaging catalog/index/lmdb", "ACTIVE_MUTATION": "requires explicit future authorization"},
    ]

    risk_rows = [
        {"RISK": "Active provider basename expectations", "MITIGATION": "Use active basenames in candidate root before any active promotion."},
        {"RISK": "Memo sidecar attach", "MITIGATION": "Carry SYSTEM_MESSAGE_TEXT.dtx alongside candidate SYSTEM_MESSAGE_TEXT.dbf and prove runtime attach/readback."},
        {"RISK": "Index/LMDB drift", "MITIGATION": "Rebuild CDX and LMDB natively in candidate roots, never with raw byte tooling."},
        {"RISK": "Path ambiguity", "MITIGATION": "Use absolute DBF/CSV paths in proof scripts; use SET PATH helper only as convenience, not as authoritative proof."},
        {"RISK": "Duplicate import rows", "MITIGATION": "Do not rerun import proof on existing imported sandbox; copy from proven 6.5.6.1 artifacts."},
    ]

    status = STATUS_GREEN if failures == 0 else STATUS_BLOCKED
    validation_issues = "0" if failures == 0 else str(failures)

    write_csv(reports / "message_catalog_phase22ae_6_5_7_gate_check_v1.csv",
              gates, ["GATE", "STATUS", "DETAIL"])
    write_csv(reports / "message_catalog_phase22ae_6_5_7_source_inventory_v1.csv",
              source_inventory, ["ROLE", "PATH", "EXISTS", "BYTES", "SHA256"])
    write_csv(reports / "message_catalog_phase22ae_6_5_7_active_inventory_v1.csv",
              active_inventory, ["ROLE", "PATH", "EXISTS", "BYTES", "SHA256"])
    write_csv(reports / "message_catalog_phase22ae_6_5_7_candidate_artifact_plan_v1.csv",
              candidate_artifacts, ["ROLE", "SOURCE", "TARGET", "ACTION"])
    write_csv(reports / "message_catalog_phase22ae_6_5_7_execution_plan_v1.csv",
              execution_plan, ["STEP", "PHASE", "ACTION", "MUTATION_SCOPE", "ACTIVE_MUTATION"])
    write_csv(reports / "message_catalog_phase22ae_6_5_7_risk_register_v1.csv",
              risk_rows, ["RISK", "MITIGATION"])

    boundary = [
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Plan-only; no source mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_DBF_CATALOG", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Plan-only; no active DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_CDX_INDEXES", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Plan-only; no active CDX mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Plan-only; no active LMDB mutation."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No HELP DATA mutation."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CMDHELPCHK mutation."},
    ]
    write_csv(reports / "message_catalog_phase22ae_6_5_7_boundary_ledger_v1.csv",
              boundary, ["PROTECTED_SYSTEM", "MUTATION_ALLOWED", "OBSERVED_MUTATION", "DETAIL"])

    write_csv(reports / "message_catalog_phase22ae_6_5_7_status_summary_v1.csv", [{
        "STATUS": status,
        "VALIDATION_ISSUES": validation_issues,
        "PHASE22AE_6_5_6_2_GREEN": 1 if summary6562.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_5_6_2_TEXT_KEY_MEMO_SIDECAR_READBACK_REPAIR_GREEN_SOURCE_HELD" else 0,
        "MSG_022AE_6_5_6_2_SAVEPOINT_PRESENT": 1 if sp_ok else 0,
        "MESSAGE_ROWS": summary6562.get("MESSAGE_ROWS_AFTER", ""),
        "TEXT_ROWS": summary6562.get("TEXT_ROWS_AFTER", ""),
        "RAW_MESSAGE_KEYS_FOUND": summary6562.get("RAW_MESSAGE_KEYS_FOUND", ""),
        "RAW_TEXT_KEYS_FOUND": summary6562.get("RAW_TEXT_KEYS_FOUND", ""),
        "TEXT_DTX_BYTES": summary6562.get("TEXT_DTX_BYTES", ""),
        "CANDIDATE_ROOT": rel(repo / CANDIDATE_ROOT, repo),
        "ACTIVE_PROMOTION_AUTHORIZED": 0,
        "CANDIDATE_STAGING_AUTHORIZED": 0,
        "CANDIDATE_INDEX_LMDB_REBUILD_AUTHORIZED": 0,
        "SOURCE_FILES_MUTATED": 0,
        "ACTIVE_CATALOG_MUTATION_OBSERVED": 0,
        "HELP_DATA_MUTATION_OBSERVED": 0,
        "CMDHELPCHK_MUTATION_OBSERVED": 0,
        "NEXT_GATE": NEXT_GATE if status == STATUS_GREEN else "HOLD_AND_FIX_PHASE22AE_6_5_7_PLAN_PRECONDITIONS",
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }], ["STATUS", "VALIDATION_ISSUES", "PHASE22AE_6_5_6_2_GREEN",
         "MSG_022AE_6_5_6_2_SAVEPOINT_PRESENT", "MESSAGE_ROWS", "TEXT_ROWS",
         "RAW_MESSAGE_KEYS_FOUND", "RAW_TEXT_KEYS_FOUND", "TEXT_DTX_BYTES",
         "CANDIDATE_ROOT", "ACTIVE_PROMOTION_AUTHORIZED", "CANDIDATE_STAGING_AUTHORIZED",
         "CANDIDATE_INDEX_LMDB_REBUILD_AUTHORIZED", "SOURCE_FILES_MUTATED",
         "ACTIVE_CATALOG_MUTATION_OBSERVED", "HELP_DATA_MUTATION_OBSERVED",
         "CMDHELPCHK_MUTATION_OBSERVED", "NEXT_GATE", "REPORT_TIMESTAMP_UTC"])

    md = f"""# Message Catalog Phase 22AE.6.5.7 Native Index/LMDB Rebuild and Promotion Plan

Status: `{status}`

6.5.7 is plan-only. It authorizes no candidate staging, no CDX/LMDB rebuild,
and no active replacement. It records the safe path after 6.5.6.2 proved native
IMPORT CSV with memo sidecar support.

Key evidence:

```text
message rows: {summary6562.get("MESSAGE_ROWS_AFTER", "")}
text rows: {summary6562.get("TEXT_ROWS_AFTER", "")}
message keys: {summary6562.get("RAW_MESSAGE_KEYS_FOUND", "")}/2
text keys: {summary6562.get("RAW_TEXT_KEYS_FOUND", "")}/10
text .dtx bytes: {summary6562.get("TEXT_DTX_BYTES", "")}
```

Next gate:

```text
{NEXT_GATE if status == STATUS_GREEN else "HOLD_AND_FIX_PHASE22AE_6_5_7_PLAN_PRECONDITIONS"}
```
"""
    (reports / "MESSAGE_CATALOG_PHASE22AE_6_5_7_NATIVE_INDEX_LMDB_REBUILD_AND_PROMOTION_PLAN.md").write_text(md, encoding="utf-8")

    print(status)
    print(f"  validation issues: {validation_issues}")
    print(f"  Phase 22AE.6.5.6.2 green: {1 if summary6562.get('STATUS') == 'MESSAGE_CATALOG_PHASE22AE_6_5_6_2_TEXT_KEY_MEMO_SIDECAR_READBACK_REPAIR_GREEN_SOURCE_HELD' else 0}")
    print(f"  MSG-022AE.6.5.6.2 savepoint present: {1 if sp_ok else 0}")
    print(f"  message/text rows: {summary6562.get('MESSAGE_ROWS_AFTER','')}/{summary6562.get('TEXT_ROWS_AFTER','')}")
    print(f"  raw message/text keys: {summary6562.get('RAW_MESSAGE_KEYS_FOUND','')}/{summary6562.get('RAW_TEXT_KEYS_FOUND','')}")
    print(f"  text dtx bytes: {summary6562.get('TEXT_DTX_BYTES','')}")
    print(f"  candidate root planned: {rel(repo / CANDIDATE_ROOT, repo)}")
    print("  active promotion authorized: 0")
    print("  candidate staging authorized: 0")
    print("  candidate index/lmdb rebuild authorized: 0")
    print("  source files mutated: 0")
    print("  active catalog mutation observed: 0")
    print("  HELP DATA mutation observed: 0")
    print("  CMDHELPCHK mutation observed: 0")
    print(f"  next gate: {NEXT_GATE if status == STATUS_GREEN else 'HOLD_AND_FIX_PHASE22AE_6_5_7_PLAN_PRECONDITIONS'}")
    print(f"  reports: {reports}")
    return 0 if status == STATUS_GREEN else 2

if __name__ == "__main__":
    raise SystemExit(main())
