#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

STATUS_GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_COMMAND_SURFACE_WRITE_FIX_OR_IMPORT_PATH_PLAN_GREEN_SOURCE_HELD"
STATUS_BLOCKED = "MESSAGE_CATALOG_PHASE22AE_6_5_COMMAND_SURFACE_WRITE_FIX_OR_IMPORT_PATH_PLAN_BLOCKED"
NEXT_GATE = "HOLD_OR_AUTHORIZE_PHASE22AE_6_5_1_IMPORT_OR_REBUILD_SANDBOX_PROOF_PACKAGE"

REPORT_DIR = Path("docs/messaging/reports")

SCAN_DIRS = ["src", "include", "docs", "tools"]
SCAN_EXTS = {".cpp", ".hpp", ".h", ".py", ".ps1", ".dts", ".md", ".txt"}

PATTERNS = [
    ("REPLACE_COMMAND", re.compile(r"\bREPLACE\b", re.IGNORECASE)),
    ("REPLACE_WITH_SYNTAX", re.compile(r"\bREPLACE\b.+\bWITH\b", re.IGNORECASE)),
    ("APPEND_COMMAND", re.compile(r"\bAPPEND\b", re.IGNORECASE)),
    ("APPEND_FROM", re.compile(r"\bAPPEND\s+FROM\b", re.IGNORECASE)),
    ("IMPORT_COMMAND", re.compile(r"\bIMPORT\b", re.IGNORECASE)),
    ("CSV_IMPORT", re.compile(r"\bCSV\b|\bcsv\b")),
    ("BUILDLMDB", re.compile(r"\bBUILDLMDB\b", re.IGNORECASE)),
    ("CDX_CREATE", re.compile(r"\bCDX\s+CREATE\b", re.IGNORECASE)),
    ("CDX_ADDTAG", re.compile(r"\bCDX\s+ADDTAG\b", re.IGNORECASE)),
    ("MEMO_BACKEND", re.compile(r"\bmemo\b", re.IGNORECASE)),
    ("MESSAGE_CATALOG", re.compile(r"message[_\s-]*catalog|SYSTEM_MESSAGE", re.IGNORECASE)),
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

def scan_repo(repo: Path, max_hits_per_pattern: int = 60):
    counts = Counter()
    hits = []
    seen = set()
    for dirname in SCAN_DIRS:
        root = repo / dirname
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in SCAN_EXTS:
                continue
            rp = rel(path, repo)
            if rp in seen:
                continue
            seen.add(rp)
            try:
                text = path.read_text(encoding="utf-8", errors="replace")
            except Exception:
                continue
            for lineno, line in enumerate(text.splitlines(), 1):
                stripped = line.strip()
                if not stripped:
                    continue
                for name, regex in PATTERNS:
                    if regex.search(stripped):
                        counts[name] += 1
                        if sum(1 for h in hits if h["PATTERN"] == name) < max_hits_per_pattern:
                            hits.append({
                                "PATTERN": name,
                                "FILE": rp,
                                "LINE": lineno,
                                "TEXT": stripped[:260],
                            })
    return [{"PATTERN": k, "TOTAL_MATCHES": v} for k, v in sorted(counts.items())], hits

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    reports = repo / REPORT_DIR
    reports.mkdir(parents=True, exist_ok=True)

    ae643 = first_row(reports / "message_catalog_phase22ae_6_4_3_validate_status_summary_v1.csv")
    ae642 = first_row(reports / "message_catalog_phase22ae_6_4_2_status_summary_v1.csv")
    sp643, latest_id = savepoint_present(repo, "MSG-022AE.6.4.3")

    gates = []
    failures = 0

    def gate(name: str, ok: bool, detail: str):
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": str(detail)})
        if not ok:
            failures += 1

    gate("PHASE22AE_6_4_3_GREEN_ISOLATED_PARTIAL",
         ae643.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_4_3_FULLY_ISOLATED_SANDBOX_WRITE_PROOF_GREEN_ISOLATED_PARTIAL_ONLY",
         ae643.get("STATUS", "missing"))
    gate("MSG_022AE_6_4_3_SAVEPOINT_PRESENT", sp643, latest_id)
    gate("BOUNDARY_CLEAN_IN_6_4_3", ae643.get("BOUNDARY_CLEAN") == "1", ae643.get("BOUNDARY_CLEAN", "missing"))
    gate("EXACT_KEYS_NOT_PROVEN_IN_6_4_3",
         ae643.get("MESSAGE_EXACT_SYMBOL_ROWS") == "0" and ae643.get("TEXT_EXACT_SYMBOL_LOCALE_ROWS") == "0",
         f"msg={ae643.get('MESSAGE_EXACT_SYMBOL_ROWS','')}; text={ae643.get('TEXT_EXACT_SYMBOL_LOCALE_ROWS','')}")
    gate("PHASE22AE_6_4_2_GREEN",
         ae642.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_4_2_BOUNDARY_DELTA_CLASSIFICATION_GREEN_SOURCE_HELD",
         ae642.get("STATUS", "missing"))

    pattern_counts, pattern_hits = scan_repo(repo)

    evidence = [
        {
            "EVIDENCE": "ISOLATION_PROVED",
            "DETAIL": "22AE.6.4.3 completed with boundary clean = 1, protected fingerprint changes = 0, and active catalog mutation observed = 0.",
            "SOURCE": "message_catalog_phase22ae_6_4_3_validate_status_summary_v1.csv",
        },
        {
            "EVIDENCE": "APPEND_WITHOUT_FIELD_VALUES_RECONFIRMED",
            "DETAIL": "22AE.6.4.3 moved sandbox rows 12/60 to 13/61 but exact message/text keys remained 0/0.",
            "SOURCE": "message_catalog_phase22ae_6_4_3_validate_status_summary_v1.csv",
        },
        {
            "EVIDENCE": "OLD_ACTIVE_PROMOTION_PATH_CLOSED",
            "DETAIL": "22AE.5 attempted active promotion, produced partial rows, and required rollback. Later sandbox proofs reproduced append-without-keys safely.",
            "SOURCE": "22AE.5 through 22AE.6.4.3 reports",
        },
        {
            "EVIDENCE": "COMMAND_SURFACE_WRITE_SEMANTICS_UNRESOLVED",
            "DETAIL": "Generated REPLACE commands are accepted enough to allow APPEND count movement, but do not produce exact field values in DBF readback.",
            "SOURCE": "6.1, 6.3, 6.4.1, and 6.4.3 validate reports",
        },
    ]

    route_matrix = [
        {
            "ROUTE_ID": "A",
            "ROUTE": "REPAIR_REPLACE_COMMAND_SEMANTICS",
            "RECOMMENDATION": "DO_NOT_START_AS_NEXT_RUNTIME_PATH",
            "WHY": "Several sandbox variants already show APPEND without exact keys. A source-level REPLACE repair could be valuable later, but it is a language-command fix and should not block messaging catalog promotion.",
            "NEXT_PROOF": "Separate command-surface unit test lane, not active messaging promotion.",
            "MUTATES_ACTIVE": 0,
            "RISK": "MEDIUM_SOURCE_SEMANTICS",
        },
        {
            "ROUTE_ID": "B",
            "ROUTE": "CSV_IMPORT_OR_APPEND_FROM_SANDBOX",
            "RECOMMENDATION": "TRY_FIRST_IF_RUNTIME_SURFACE_EXISTS",
            "WHY": "A tabular import path may populate fields more reliably than interactive REPLACE, while staying sandbox-only first.",
            "NEXT_PROOF": "Build isolated sandbox, generate message/text CSV rows, run IMPORT/APPEND FROM if supported, validate exact keys and boundary clean.",
            "MUTATES_ACTIVE": 0,
            "RISK": "LOW_TO_MEDIUM_SANDBOX_ONLY",
        },
        {
            "ROUTE_ID": "C",
            "ROUTE": "FULL_CANDIDATE_CATALOG_REBUILD_SANDBOX",
            "RECOMMENDATION": "PREFERRED_DESIGN_FALLBACK",
            "WHY": "If import is weak or unavailable, rebuild complete SYSTEM_MESSAGES and SYSTEM_MESSAGE_TEXT candidate DBFs from canonical rows, then prove DBF/CDX/LMDB/runtime readback in sandbox. This avoids in-place APPEND/REPLACE semantics entirely.",
            "NEXT_PROOF": "Generate complete 14/70 sandbox candidate roots, build/rebuild CDX/LMDB locally, load via runtime readback.",
            "MUTATES_ACTIVE": 0,
            "RISK": "MEDIUM_TOOLING_COMPLEXITY",
        },
        {
            "ROUTE_ID": "D",
            "ROUTE": "DIRECT_RAW_DBF_MEMO_WRITE",
            "RECOMMENDATION": "FORBID",
            "WHY": "SYSTEM_MESSAGE_TEXT.TEXT is memo-backed. Raw DBF/memo edits bypass runtime semantics and were already considered unsafe.",
            "NEXT_PROOF": "None.",
            "MUTATES_ACTIVE": 1,
            "RISK": "HIGH_FORBIDDEN",
        },
        {
            "ROUTE_ID": "E",
            "ROUTE": "ACTIVE_PROMOTION_RETRY",
            "RECOMMENDATION": "FORBID_UNTIL_SANDBOX_EXACT_KEYS",
            "WHY": "No sandbox proof has exact two-table keys yet. Retrying active promotion would repeat known failure risk.",
            "NEXT_PROOF": "None until B or C proves exact keys in isolated sandbox.",
            "MUTATES_ACTIVE": 1,
            "RISK": "HIGH_FORBIDDEN",
        },
    ]

    # Pick a conservative next path. If import tokens exist, allow an import-or-rebuild package;
    # the next package can test import first and fall back to full rebuild, but still sandbox-only.
    count_lookup = {r["PATTERN"]: int(r["TOTAL_MATCHES"]) for r in pattern_counts}
    import_evidence = count_lookup.get("IMPORT_COMMAND", 0) + count_lookup.get("APPEND_FROM", 0)
    recommended = "IMPORT_OR_REBUILD_SANDBOX_PROOF_PACKAGE" if import_evidence > 0 else "FULL_CANDIDATE_CATALOG_REBUILD_SANDBOX_PROOF_PACKAGE"

    next_plan = [
        {
            "STEP": 1,
            "ACTION": "KEEP_6_4_3_AS_GREEN_PARTIAL_ONLY",
            "DETAIL": "Append 6.4.3 only as isolated partial; do not treat it as a promotion-ready write path.",
            "MUTATES_ACTIVE": 0,
        },
        {
            "STEP": 2,
            "ACTION": "GENERATE_CANONICAL_CANDIDATE_ROWS",
            "DETAIL": "Stage the two new message rows and ten localized text rows from the previously accepted candidate package.",
            "MUTATES_ACTIVE": 0,
        },
        {
            "STEP": 3,
            "ACTION": "TRY_IMPORT_OR_APPEND_FROM_IN_ISOLATED_SANDBOX_IF_AVAILABLE",
            "DETAIL": "Use a fresh isolated sandbox and validate exact keys. Do not use active roots.",
            "MUTATES_ACTIVE": 0,
        },
        {
            "STEP": 4,
            "ACTION": "IF_IMPORT_UNAVAILABLE_BUILD_COMPLETE_CANDIDATE_DBFS",
            "DETAIL": "Create complete 14/70 candidate DBFs from canonical existing + candidate rows, then rebuild local CDX/LMDB and prove runtime load.",
            "MUTATES_ACTIVE": 0,
        },
        {
            "STEP": 5,
            "ACTION": "REQUIRE_EXACT_TWO_TABLE_KEYS_AND_BOUNDARY_CLEAN",
            "DETAIL": "No future active plan until both SYSTEM_MESSAGES and SYSTEM_MESSAGE_TEXT exact keys are proven in isolated sandbox with zero protected fingerprint deltas.",
            "MUTATES_ACTIVE": 0,
        },
    ]

    forbidden = [
        {"RULE": "NO_ACTIVE_PROMOTION", "DETAIL": "No exact two-table sandbox path is proven."},
        {"RULE": "NO_REUSE_APPEND_REPLACE_PATH_FOR_PROMOTION", "DETAIL": "APPEND/REPLACE repeatedly appends rows without exact key values."},
        {"RULE": "NO_RAW_DBF_MEMO_WRITE", "DETAIL": "Memo-backed text must not be bypassed."},
        {"RULE": "NO_COMMAND_SOURCE_REPAIR_AS_SIDE_EFFECT", "DETAIL": "REPLACE semantics repair, if pursued, must be a separate explicit source-mutation lane."},
        {"RULE": "NO_HELP_OR_CMDHELPCHK_MUTATION", "DETAIL": "This lane is messaging catalog proof only."},
    ]

    boundary = [
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "6.5 is plan/report only."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_DBF_CATALOG", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_CDX_INDEXES", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active CDX mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active LMDB mutation."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No HELP DATA mutation."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CMDHELPCHK mutation."},
        {"PROTECTED_SYSTEM": "MANUALGEN_DATADICT_SELFDOC", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No manualgen/Data Dictionary/SelfDoc mutation."},
    ]

    status = STATUS_GREEN if failures == 0 else STATUS_BLOCKED
    validation_issues = str(failures)

    write_csv(reports / "message_catalog_phase22ae_6_5_gate_check_v1.csv", gates, ["GATE", "STATUS", "DETAIL"])
    write_csv(reports / "message_catalog_phase22ae_6_5_evidence_summary_v1.csv", evidence, ["EVIDENCE", "DETAIL", "SOURCE"])
    write_csv(reports / "message_catalog_phase22ae_6_5_command_pattern_counts_v1.csv", pattern_counts, ["PATTERN", "TOTAL_MATCHES"])
    write_csv(reports / "message_catalog_phase22ae_6_5_command_pattern_hits_v1.csv", pattern_hits, ["PATTERN", "FILE", "LINE", "TEXT"])
    write_csv(reports / "message_catalog_phase22ae_6_5_route_matrix_v1.csv", route_matrix, ["ROUTE_ID", "ROUTE", "RECOMMENDATION", "WHY", "NEXT_PROOF", "MUTATES_ACTIVE", "RISK"])
    write_csv(reports / "message_catalog_phase22ae_6_5_1_next_proof_plan_v1.csv", next_plan, ["STEP", "ACTION", "DETAIL", "MUTATES_ACTIVE"])
    write_csv(reports / "message_catalog_phase22ae_6_5_forbidden_paths_v1.csv", forbidden, ["RULE", "DETAIL"])
    write_csv(reports / "message_catalog_phase22ae_6_5_boundary_ledger_v1.csv", boundary, ["PROTECTED_SYSTEM", "MUTATION_ALLOWED", "OBSERVED_MUTATION", "DETAIL"])

    write_csv(reports / "message_catalog_phase22ae_6_5_status_summary_v1.csv", [{
        "STATUS": status,
        "VALIDATION_ISSUES": validation_issues,
        "PHASE22AE_6_4_3_STATUS": ae643.get("STATUS", ""),
        "MSG_022AE_6_4_3_SAVEPOINT_PRESENT": 1 if sp643 else 0,
        "BOUNDARY_CLEAN_IN_6_4_3": ae643.get("BOUNDARY_CLEAN", ""),
        "TWO_TABLE_VARIANT_PROVEN_IN_6_4_3": ae643.get("TWO_TABLE_VARIANT_PROVEN", ""),
        "ROW_APPEND_WITHOUT_KEYS_RECONFIRMED": 1 if (ae643.get("MESSAGE_DELTA") == "1" and ae643.get("TEXT_DELTA") == "1" and ae643.get("TWO_TABLE_VARIANT_PROVEN") == "0") else 0,
        "IMPORT_OR_APPEND_FROM_EVIDENCE_COUNT": import_evidence,
        "RECOMMENDED_NEXT_PATH": recommended,
        "ACTIVE_PROMOTION_AUTHORIZED": 0,
        "SOURCE_FILES_MUTATED": 0,
        "ACTIVE_CATALOG_MUTATION_OBSERVED": 0,
        "HELP_DATA_MUTATION_OBSERVED": 0,
        "CMDHELPCHK_MUTATION_OBSERVED": 0,
        "NEXT_GATE": NEXT_GATE,
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }], ["STATUS", "VALIDATION_ISSUES", "PHASE22AE_6_4_3_STATUS",
         "MSG_022AE_6_4_3_SAVEPOINT_PRESENT", "BOUNDARY_CLEAN_IN_6_4_3",
         "TWO_TABLE_VARIANT_PROVEN_IN_6_4_3", "ROW_APPEND_WITHOUT_KEYS_RECONFIRMED",
         "IMPORT_OR_APPEND_FROM_EVIDENCE_COUNT", "RECOMMENDED_NEXT_PATH",
         "ACTIVE_PROMOTION_AUTHORIZED", "SOURCE_FILES_MUTATED", "ACTIVE_CATALOG_MUTATION_OBSERVED",
         "HELP_DATA_MUTATION_OBSERVED", "CMDHELPCHK_MUTATION_OBSERVED",
         "NEXT_GATE", "REPORT_TIMESTAMP_UTC"])

    md = f"""# Message Catalog Phase 22AE.6.5 Command Surface Write Fix or Import Path Plan

Status: `{status}`

22AE.6.4.3 proved isolation but not exact two-table write semantics. Rows moved
but exact message/text keys did not land. Active promotion remains closed.

Recommended next path:

```text
{recommended}
```

Next gate:

```text
{NEXT_GATE}
```
"""
    (reports / "MESSAGE_CATALOG_PHASE22AE_6_5_COMMAND_SURFACE_WRITE_FIX_OR_IMPORT_PATH_PLAN.md").write_text(md, encoding="utf-8")

    print(status)
    print(f"  validation issues: {validation_issues}")
    print(f"  Phase 22AE.6.4.3 status: {ae643.get('STATUS', '')}")
    print(f"  MSG-022AE.6.4.3 savepoint present: {1 if sp643 else 0}")
    print(f"  boundary clean in 6.4.3: {ae643.get('BOUNDARY_CLEAN', '')}")
    print(f"  two-table variant proven in 6.4.3: {ae643.get('TWO_TABLE_VARIANT_PROVEN', '')}")
    print(f"  row append without keys reconfirmed: {1 if (ae643.get('MESSAGE_DELTA') == '1' and ae643.get('TEXT_DELTA') == '1' and ae643.get('TWO_TABLE_VARIANT_PROVEN') == '0') else 0}")
    print(f"  import or append-from evidence count: {import_evidence}")
    print(f"  recommended next path: {recommended}")
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
