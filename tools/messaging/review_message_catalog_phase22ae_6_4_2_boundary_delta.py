#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

STATUS_GREEN = "MESSAGE_CATALOG_PHASE22AE_6_4_2_BOUNDARY_DELTA_CLASSIFICATION_GREEN_SOURCE_HELD"
STATUS_BLOCKED = "MESSAGE_CATALOG_PHASE22AE_6_4_2_BOUNDARY_DELTA_CLASSIFICATION_BLOCKED"
NEXT_GATE = "HOLD_OR_AUTHORIZE_PHASE22AE_6_4_3_FULLY_ISOLATED_SANDBOX_WRITE_PROOF_PACKAGE"

REPORT_DIR = Path("docs/messaging/reports")
DELTA_CSV = REPORT_DIR / "message_catalog_phase22ae_6_4_1_active_fingerprint_delta_v1.csv"
RESULT_CSV = REPORT_DIR / "message_catalog_phase22ae_6_4_1_single_variant_result_v1.csv"

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
            latest_id = json.loads(latest_path.read_text(encoding="utf-8")).get("savepoint_id", "")
        except Exception:
            latest_id = ""
    journal = repo / "docs/messaging/MESSAGING_SAVEPOINT_JOURNAL.md"
    text = journal.read_text(encoding="utf-8", errors="replace") if journal.exists() else ""
    return latest_id == savepoint_id or savepoint_id in text, latest_id

def classify_path(path: str) -> tuple[str, str, str]:
    p = path.replace("\\", "/")
    lower = p.lower()

    if lower.startswith("dottalkpp/data/messaging/"):
        return "ACTIVE_MESSAGING_DBF_ROOT", "FAIL_IF_CHANGED", "Active messaging DBF catalog root."

    if lower.startswith("dottalkpp/data/indexes/messaging/"):
        return "ACTIVE_MESSAGING_INDEX_SUBROOT", "FAIL_IF_CHANGED", "Active messaging index subroot."

    if lower.startswith("dottalkpp/data/lmdb/messaging/"):
        return "ACTIVE_MESSAGING_LMDB_SUBROOT", "FAIL_IF_CHANGED", "Active messaging LMDB subroot."

    if lower == "dottalkpp/data/indexes/system_messages.cdx" or lower == "dottalkpp/data/indexes/system_messages.cdx.meta":
        return "DEFAULT_INDEX_ROOT_MESSAGE_CATALOG", "BOUNDARY_FAIL", "Default index root file for SYSTEM_MESSAGES."

    if lower == "dottalkpp/data/indexes/system_message_text.cdx" or lower == "dottalkpp/data/indexes/system_message_text.cdx.meta":
        return "DEFAULT_INDEX_ROOT_MESSAGE_CATALOG", "BOUNDARY_FAIL", "Default index root file for SYSTEM_MESSAGE_TEXT."

    if lower.startswith("dottalkpp/data/lmdb/system_messages.cdx.d") or lower.startswith("dottalkpp/data/lmdb/system_message_text.cdx.d"):
        return "DEFAULT_LMDB_ROOT_MESSAGE_CATALOG", "BOUNDARY_FAIL", "Default LMDB root for messaging catalog."

    if lower.startswith("dottalkpp/data/indexes/"):
        # Broad default index root churn. It is not necessarily active messaging catalog mutation,
        # but it is out of scope for a clean sandbox proof.
        parts = p.split("/")
        filename = parts[-1] if parts else p
        if filename.upper().startswith("MAN"):
            return "DEFAULT_INDEX_ROOT_MANUALGEN_CHURN", "BOUNDARY_REVIEW", "Default index root MAN* churn, likely unrelated to messaging DBF but not clean."
        if "/backups/" in lower:
            return "DEFAULT_INDEX_ROOT_BACKUP_CHURN", "BOUNDARY_REVIEW", "Default index backup churn, likely environmental/default-root churn."
        return "DEFAULT_INDEX_ROOT_OTHER_CHURN", "BOUNDARY_REVIEW", "Default index root churn outside sandbox."

    if lower.startswith("dottalkpp/data/lmdb/"):
        if "/man" in lower or lower.endswith("manrun.cdx.d") or lower.endswith("mansection.cdx.d"):
            return "DEFAULT_LMDB_ROOT_MANUALGEN_CHURN", "BOUNDARY_REVIEW", "Default LMDB MAN* churn, likely unrelated but not clean."
        return "DEFAULT_LMDB_ROOT_OTHER_CHURN", "BOUNDARY_REVIEW", "Default LMDB root churn outside sandbox."

    return "OTHER", "REVIEW", "Unclassified fingerprint delta."

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    reports = repo / REPORT_DIR
    reports.mkdir(parents=True, exist_ok=True)

    ae641 = first_row(reports / "message_catalog_phase22ae_6_4_1_validate_status_summary_v1.csv")
    ae64 = first_row(reports / "message_catalog_phase22ae_6_4_status_summary_v1.csv")
    sp64, latest_id = savepoint_present(repo, "MSG-022AE.6.4")

    delta_rows = read_csv(repo / DELTA_CSV)
    result = first_row(repo / RESULT_CSV)

    gates = []
    failures = 0
    def gate(name: str, ok: bool, detail: str):
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": str(detail)})
        if not ok:
            failures += 1

    gate("PHASE22AE_6_4_GREEN",
         ae64.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_4_DEEP_COMMAND_SURFACE_WRITE_SEMANTICS_REVIEW_GREEN_SOURCE_HELD",
         ae64.get("STATUS", "missing"))
    gate("MSG_022AE_6_4_SAVEPOINT_PRESENT", sp64, latest_id)
    gate("PHASE22AE_6_4_1_BLOCKED",
         ae641.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_4_1_SINGLE_VARIANT_FORENSIC_SANDBOX_PROOF_BLOCKED",
         ae641.get("STATUS", "missing"))
    gate("PHASE22AE_6_4_1_PARTIAL_EVIDENCE",
         ae641.get("PARTIAL_EVIDENCE") == "1",
         ae641.get("PARTIAL_EVIDENCE", "missing"))
    gate("PHASE22AE_6_4_1_DELTA_FILE_PRESENT",
         len(delta_rows) > 0,
         f"delta rows={len(delta_rows)}")

    classified = []
    counts = Counter()
    dispositions = Counter()
    for row in delta_rows:
        path = row.get("PATH", "")
        cls, disp, note = classify_path(path)
        counts[cls] += 1
        dispositions[disp] += 1
        classified.append({
            "PATH": path,
            "CHANGE": row.get("CHANGE", ""),
            "CLASSIFICATION": cls,
            "DISPOSITION": disp,
            "NOTE": note,
            "BEFORE_BYTES": row.get("BEFORE_BYTES", ""),
            "AFTER_BYTES": row.get("AFTER_BYTES", ""),
            "BEFORE_SHA256": row.get("BEFORE_SHA256", ""),
            "AFTER_SHA256": row.get("AFTER_SHA256", ""),
        })

    root_summary = []
    for cls, count in sorted(counts.items()):
        example = next((r for r in classified if r["CLASSIFICATION"] == cls), {})
        root_summary.append({
            "CLASSIFICATION": cls,
            "DELTA_ROWS": count,
            "PRIMARY_DISPOSITION": example.get("DISPOSITION", ""),
            "EXAMPLE_PATH": example.get("PATH", ""),
            "NOTE": example.get("NOTE", ""),
        })

    true_active_messaging_deltas = sum(counts[k] for k in [
        "ACTIVE_MESSAGING_DBF_ROOT",
        "ACTIVE_MESSAGING_INDEX_SUBROOT",
        "ACTIVE_MESSAGING_LMDB_SUBROOT",
    ])
    default_message_catalog_deltas = sum(counts[k] for k in [
        "DEFAULT_INDEX_ROOT_MESSAGE_CATALOG",
        "DEFAULT_LMDB_ROOT_MESSAGE_CATALOG",
    ])
    default_root_churn = len(delta_rows) - true_active_messaging_deltas

    conclusions = [
        {
            "CONCLUSION": "6_4_1_NOT_APPENDABLE",
            "DETAIL": "22AE.6.4.1 remains blocked and must not be savepointed as green.",
            "EVIDENCE": ae641.get("STATUS", ""),
        },
        {
            "CONCLUSION": "ROW_APPEND_WITHOUT_KEYS_RECONFIRMED",
            "DETAIL": "Single V1 forensic run moved counts by one but found zero exact message/text keys.",
            "EVIDENCE": f"message_delta={result.get('MESSAGE_DELTA','')}; text_delta={result.get('TEXT_DELTA','')}; message_keys={result.get('MESSAGE_EXACT_SYMBOL_ROWS','')}; text_keys={result.get('TEXT_EXACT_SYMBOL_LOCALE_ROWS','')}",
        },
        {
            "CONCLUSION": "BOUNDARY_DELTA_IS_BROAD_DEFAULT_ROOT_CHURN",
            "DETAIL": "The fingerprint delta includes broad dottalkpp/data/indexes and/or dottalkpp/data/lmdb churn, not just the sandbox target.",
            "EVIDENCE": f"total_delta_rows={len(delta_rows)}; default_root_churn={default_root_churn}",
        },
        {
            "CONCLUSION": "TRUE_ACTIVE_MESSAGING_DBF_DELTA_CLASSIFIED",
            "DETAIL": "Direct active messaging DBF-root changes are counted separately from default index/LMDB churn.",
            "EVIDENCE": f"true_active_messaging_deltas={true_active_messaging_deltas}; default_message_catalog_deltas={default_message_catalog_deltas}",
        },
        {
            "CONCLUSION": "NEXT_PROOF_MUST_ISOLATE_INDEX_AND_LMDB_ROOTS",
            "DETAIL": "Opening sandbox DBFs with current runtime/pathing is not sufficient; next proof must force or verify sandbox-local index/LMDB paths before any write test.",
            "EVIDENCE": "22AE.6.4.3 should be fully isolated sandbox proof package.",
        },
    ]

    repair_plan = [
        {
            "STEP": 1,
            "ACTION": "DO_NOT_APPEND_6_4_1",
            "DETAIL": "6.4.1 is blocked. Keep it as diagnostic evidence only.",
            "MUTATES_ACTIVE": 0,
        },
        {
            "STEP": 2,
            "ACTION": "BUILD_FRESH_SANDBOX_WITH_LOCAL_INDEX_AND_LMDB_ROOTS",
            "DETAIL": "Next package must create sandbox DBF, indexes, and LMDB roots under docs/messaging/sandbox only.",
            "MUTATES_ACTIVE": 0,
        },
        {
            "STEP": 3,
            "ACTION": "AVOID_DEFAULT_INDEX_ROOT_FINGERPRINT_NOISE",
            "DETAIL": "Fingerprint only protected messaging roots and selected default message-catalog files, not unrelated MAN*/backup/system-wide indexes, unless doing an environmental audit.",
            "MUTATES_ACTIVE": 0,
        },
        {
            "STEP": 4,
            "ACTION": "PROVE_PATH_BINDING_BEFORE_WRITES",
            "DETAIL": "Before APPEND, run read-only open/check commands that demonstrate which CDX/LMDB paths are attached for the sandbox DBFs.",
            "MUTATES_ACTIVE": 0,
        },
        {
            "STEP": 5,
            "ACTION": "RUN_ONE_WRITE_VARIANT_ONLY_AFTER_PATH_PROOF",
            "DETAIL": "Only after sandbox-local path proof should the package run the V1 write shape again.",
            "MUTATES_ACTIVE": 0,
        },
        {
            "STEP": 6,
            "ACTION": "READBACK_BOTH_KEYS_AND_BOUNDARIES",
            "DETAIL": "Require exact message/text key rows and zero protected-root deltas before considering promotion design.",
            "MUTATES_ACTIVE": 0,
        },
    ]

    forbidden = [
        {"RULE": "NO_6_4_1_SAVEPOINT", "DETAIL": "6.4.1 blocked with boundary changes and zero exact keys."},
        {"RULE": "NO_ACTIVE_PROMOTION", "DETAIL": "No two-table write path is proven."},
        {"RULE": "NO_RETRY_AGAINST_ACTIVE", "DETAIL": "Further retries must stay in sandbox only."},
        {"RULE": "NO_DEFAULT_ROOT_INDEX_OR_LMDB_SIDE_EFFECTS", "DETAIL": "Future proof must demonstrate sandbox-local index/LMDB pathing."},
        {"RULE": "NO_RAW_MEMO_DBF_WRITE", "DETAIL": "Memo-backed text must remain handled by proven runtime/table mechanisms."},
    ]

    boundary = [
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "6.4.2 is report-only."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_DBF_CATALOG", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active DBF writes in 6.4.2."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_CDX_INDEXES", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "6.4.2 only classifies prior deltas."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "6.4.2 only classifies prior deltas."},
        {"PROTECTED_SYSTEM": "DEFAULT_INDEX_LMDB_ROOTS", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No new default-root mutations in 6.4.2."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No HELP DATA mutation."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CMDHELPCHK mutation."},
    ]

    status = STATUS_GREEN if failures == 0 else STATUS_BLOCKED
    validation_issues = str(failures)

    write_csv(reports / "message_catalog_phase22ae_6_4_2_gate_check_v1.csv", gates, ["GATE", "STATUS", "DETAIL"])
    write_csv(reports / "message_catalog_phase22ae_6_4_2_delta_classification_v1.csv", classified, ["PATH", "CHANGE", "CLASSIFICATION", "DISPOSITION", "NOTE", "BEFORE_BYTES", "AFTER_BYTES", "BEFORE_SHA256", "AFTER_SHA256"])
    write_csv(reports / "message_catalog_phase22ae_6_4_2_root_summary_v1.csv", root_summary, ["CLASSIFICATION", "DELTA_ROWS", "PRIMARY_DISPOSITION", "EXAMPLE_PATH", "NOTE"])
    write_csv(reports / "message_catalog_phase22ae_6_4_2_conclusions_v1.csv", conclusions, ["CONCLUSION", "DETAIL", "EVIDENCE"])
    write_csv(reports / "message_catalog_phase22ae_6_4_3_isolation_repair_plan_v1.csv", repair_plan, ["STEP", "ACTION", "DETAIL", "MUTATES_ACTIVE"])
    write_csv(reports / "message_catalog_phase22ae_6_4_2_forbidden_paths_v1.csv", forbidden, ["RULE", "DETAIL"])
    write_csv(reports / "message_catalog_phase22ae_6_4_2_boundary_ledger_v1.csv", boundary, ["PROTECTED_SYSTEM", "MUTATION_ALLOWED", "OBSERVED_MUTATION", "DETAIL"])

    write_csv(reports / "message_catalog_phase22ae_6_4_2_status_summary_v1.csv", [{
        "STATUS": status,
        "VALIDATION_ISSUES": validation_issues,
        "PHASE22AE_6_4_GREEN": 1 if ae64.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_4_DEEP_COMMAND_SURFACE_WRITE_SEMANTICS_REVIEW_GREEN_SOURCE_HELD" else 0,
        "MSG_022AE_6_4_SAVEPOINT_PRESENT": 1 if sp64 else 0,
        "PHASE22AE_6_4_1_STATUS": ae641.get("STATUS", ""),
        "PHASE22AE_6_4_1_SAVEPOINT_ALLOWED": 0,
        "TOTAL_DELTA_ROWS_CLASSIFIED": len(delta_rows),
        "TRUE_ACTIVE_MESSAGING_DELTAS": true_active_messaging_deltas,
        "DEFAULT_MESSAGE_CATALOG_INDEX_LMDB_DELTAS": default_message_catalog_deltas,
        "DEFAULT_ROOT_CHURN_DELTAS": default_root_churn,
        "ROW_APPEND_WITHOUT_KEYS_RECONFIRMED": 1 if (result.get("COUNTS_MOVE_ONCE") == "1" and result.get("TWO_TABLE_VARIANT_PROVEN") == "0") else 0,
        "RECOMMENDED_NEXT_PATH": "FULLY_ISOLATED_SANDBOX_WRITE_PROOF_PACKAGE",
        "ACTIVE_PROMOTION_AUTHORIZED": 0,
        "SOURCE_FILES_MUTATED": 0,
        "ACTIVE_CATALOG_MUTATION_OBSERVED": 0,
        "HELP_DATA_MUTATION_OBSERVED": 0,
        "CMDHELPCHK_MUTATION_OBSERVED": 0,
        "NEXT_GATE": NEXT_GATE,
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }], ["STATUS", "VALIDATION_ISSUES", "PHASE22AE_6_4_GREEN", "MSG_022AE_6_4_SAVEPOINT_PRESENT",
         "PHASE22AE_6_4_1_STATUS", "PHASE22AE_6_4_1_SAVEPOINT_ALLOWED",
         "TOTAL_DELTA_ROWS_CLASSIFIED", "TRUE_ACTIVE_MESSAGING_DELTAS",
         "DEFAULT_MESSAGE_CATALOG_INDEX_LMDB_DELTAS", "DEFAULT_ROOT_CHURN_DELTAS",
         "ROW_APPEND_WITHOUT_KEYS_RECONFIRMED", "RECOMMENDED_NEXT_PATH",
         "ACTIVE_PROMOTION_AUTHORIZED", "SOURCE_FILES_MUTATED", "ACTIVE_CATALOG_MUTATION_OBSERVED",
         "HELP_DATA_MUTATION_OBSERVED", "CMDHELPCHK_MUTATION_OBSERVED", "NEXT_GATE", "REPORT_TIMESTAMP_UTC"])

    md = f"""# Message Catalog Phase 22AE.6.4.2 Boundary Delta Classification

Status: `{status}`

22AE.6.4.1 remains blocked and must not be appended. This report classifies its
boundary deltas and prepares a fully isolated sandbox proof plan.

Key counts:

```text
total delta rows: {len(delta_rows)}
true active messaging deltas: {true_active_messaging_deltas}
default message-catalog index/LMDB deltas: {default_message_catalog_deltas}
default root churn deltas: {default_root_churn}
```

Next gate:

```text
{NEXT_GATE}
```
"""
    (reports / "MESSAGE_CATALOG_PHASE22AE_6_4_2_BOUNDARY_DELTA_CLASSIFICATION.md").write_text(md, encoding="utf-8")

    print(status)
    print(f"  validation issues: {validation_issues}")
    print(f"  Phase 22AE.6.4 green: {1 if ae64.get('STATUS') == 'MESSAGE_CATALOG_PHASE22AE_6_4_DEEP_COMMAND_SURFACE_WRITE_SEMANTICS_REVIEW_GREEN_SOURCE_HELD' else 0}")
    print(f"  MSG-022AE.6.4 savepoint present: {1 if sp64 else 0}")
    print(f"  Phase 22AE.6.4.1 status: {ae641.get('STATUS', '')}")
    print("  Phase 22AE.6.4.1 savepoint allowed: 0")
    print(f"  total delta rows classified: {len(delta_rows)}")
    print(f"  true active messaging deltas: {true_active_messaging_deltas}")
    print(f"  default message-catalog index/lmdb deltas: {default_message_catalog_deltas}")
    print(f"  default root churn deltas: {default_root_churn}")
    print(f"  row append without keys reconfirmed: {1 if (result.get('COUNTS_MOVE_ONCE') == '1' and result.get('TWO_TABLE_VARIANT_PROVEN') == '0') else 0}")
    print("  recommended next path: FULLY_ISOLATED_SANDBOX_WRITE_PROOF_PACKAGE")
    print("  active promotion authorized: 0")
    print("  source files mutated: 0")
    print("  active catalog mutation observed: 0")
    print("  HELP DATA mutation observed: 0")
    print("  CMDHELPCHK mutation observed: 0")
    print(f"  next gate: {NEXT_GATE}")
    print(f"  reports: {reports}")
    return 0 if status == STATUS_GREEN else 2

if __name__ == "__main__":
    raise SystemExit(main())
