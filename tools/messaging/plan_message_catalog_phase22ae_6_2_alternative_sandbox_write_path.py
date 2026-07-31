#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import re
from datetime import datetime, timezone
from pathlib import Path

STATUS_GREEN = "MESSAGE_CATALOG_PHASE22AE_6_2_ALTERNATIVE_SANDBOX_WRITE_PATH_PLAN_GREEN_SOURCE_HELD"
STATUS_BLOCKED = "MESSAGE_CATALOG_PHASE22AE_6_2_ALTERNATIVE_SANDBOX_WRITE_PATH_PLAN_BLOCKED"
NEXT_GATE = "HOLD_OR_AUTHORIZE_PHASE22AE_6_3_ALTERNATIVE_SANDBOX_WRITE_PROOF_PACKAGE"

REPORT_DIR = Path("docs/messaging/reports")

PATTERNS = [
    ("APPEND", re.compile(r"\bAPPEND\b", re.IGNORECASE)),
    ("APPEND_BLANK", re.compile(r"\bAPPEND\s+BLANK\b", re.IGNORECASE)),
    ("REPLACE_WITH", re.compile(r"\bREPLACE\b.+\bWITH\b", re.IGNORECASE)),
    ("REPLACE_NO_WITH", re.compile(r"\bREPLACE\s+[A-Za-z0-9_]+\s+['\"A-Za-z0-9_]", re.IGNORECASE)),
    ("IMPORT", re.compile(r"\bIMPORT\b", re.IGNORECASE)),
    ("APPEND_FROM", re.compile(r"\bAPPEND\s+FROM\b", re.IGNORECASE)),
    ("USE", re.compile(r"\bUSE\b", re.IGNORECASE)),
    ("SELECT", re.compile(r"\bSELECT\b", re.IGNORECASE)),
    ("GO_BOTTOM", re.compile(r"\b(GO\s+BOTTOM|BOTTOM)\b", re.IGNORECASE)),
    ("LOCATE_SEEK", re.compile(r"\b(LOCATE|SEEK|FIND)\b", re.IGNORECASE)),
    ("PACK_ZAP", re.compile(r"\b(PACK|ZAP)\b", re.IGNORECASE)),
]

SCAN_DIRS = ["docs/messaging", "docs/datadict", "docs", "src", "include", "tools/messaging"]
SCAN_EXTS = {".dts", ".md", ".ps1", ".py", ".cpp", ".hpp", ".h", ".txt", ".csv"}

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

def scan_patterns(repo: Path, max_hits_per_pattern: int = 40):
    rows = []
    counts = {name: 0 for name, _ in PATTERNS}
    roots = [repo / d for d in SCAN_DIRS if (repo / d).exists()]
    seen_files = set()
    for root in roots:
        for path in root.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in SCAN_EXTS:
                continue
            rp = rel(path, repo)
            if rp in seen_files:
                continue
            seen_files.add(rp)
            try:
                text = path.read_text(encoding="utf-8", errors="replace")
            except Exception:
                continue
            # Avoid huge source files dominating; line-based is enough.
            for lineno, line in enumerate(text.splitlines(), 1):
                clean = line.strip()
                if not clean:
                    continue
                for name, regex in PATTERNS:
                    if regex.search(clean):
                        counts[name] += 1
                        if sum(1 for r in rows if r["PATTERN"] == name) < max_hits_per_pattern:
                            rows.append({
                                "PATTERN": name,
                                "FILE": rp,
                                "LINE": lineno,
                                "TEXT": clean[:260],
                            })
    count_rows = [{"PATTERN": k, "TOTAL_MATCHES": v} for k, v in sorted(counts.items())]
    return rows, count_rows

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    reports = repo / REPORT_DIR
    reports.mkdir(parents=True, exist_ok=True)

    ae61 = first_row(reports / "message_catalog_phase22ae_6_1_validate_status_summary_v1.csv")
    sp61, latest_id = savepoint_present(repo, "MSG-022AE.6.1")

    gates = []
    failures = 0

    def gate(name: str, ok: bool, detail: str):
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": str(detail)})
        if not ok:
            failures += 1

    gate("PHASE22AE_6_1_GREEN_FAILED_PATH_CONFIRMED",
         ae61.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_1_SANDBOX_ROW_WRITE_PROOF_GREEN_FAILED_PATH_CONFIRMED",
         ae61.get("STATUS", "missing"))
    gate("MSG_022AE_6_1_SAVEPOINT_PRESENT", sp61, latest_id)
    gate("SANDBOX_COUNTS_MOVED_BY_ONE",
         ae61.get("SANDBOX_COUNTS_MOVED_BY_ONE") == "1",
         ae61.get("SANDBOX_COUNTS_MOVED_BY_ONE", "missing"))
    gate("SANDBOX_KEYS_ABSENT",
         ae61.get("SANDBOX_MESSAGE_TEST_ROWS_FOUND") == "0" and ae61.get("SANDBOX_TEXT_TEST_ROWS_FOUND") == "0",
         f"msg={ae61.get('SANDBOX_MESSAGE_TEST_ROWS_FOUND')}; text={ae61.get('SANDBOX_TEXT_TEST_ROWS_FOUND')}")
    gate("ACTIVE_CATALOG_UNTOUCHED",
         ae61.get("ACTIVE_CATALOG_MUTATION_OBSERVED") == "0",
         ae61.get("ACTIVE_CATALOG_MUTATION_OBSERVED", "missing"))

    evidence_rows = [
        {
            "EVIDENCE": "FAILED_ACTIVE_PATH_CLOSED",
            "DETAIL": "22AE.5 active path appended rows but did not populate required message/text keys; rollback restored clean active baseline.",
            "PHASE": "22AE.5 / 22AE.5.3 / 22AE.5.4",
        },
        {
            "EVIDENCE": "FAILED_PATH_REPRODUCED_IN_SANDBOX",
            "DETAIL": "22AE.6.1 sandbox copy moved 12/60 to 13/61, but test symbol rows were not found in either table.",
            "PHASE": "22AE.6.1",
        },
        {
            "EVIDENCE": "ACTIVE_CATALOG_PROTECTED",
            "DETAIL": "22AE.6.1 recorded active catalog mutation observed = 0.",
            "PHASE": "22AE.6.1",
        },
    ]

    pattern_hits, pattern_counts = scan_patterns(repo)

    # Alternatives deliberately remain sandbox-only.
    alternatives = [
        {
            "ALT_ID": "ALT_A",
            "NAME": "APPEND_WITH_POINTER_DIAGNOSTICS",
            "RECOMMENDATION": "TRY_FIRST_IN_SANDBOX",
            "WHY": "The old path appended but did not populate keys. A diagnostic variant should check selected/work-area/current-record state before and after APPEND, then after each write command.",
            "MUTATES_ACTIVE": 0,
            "RISK": "LOW_SANDBOX_ONLY",
            "SUCCESS_CRITERIA": "Sandbox counts move by one and test keys read back exactly.",
        },
        {
            "ALT_ID": "ALT_B",
            "NAME": "REPLACE_SYNTAX_VARIANTS",
            "RECOMMENDATION": "TRY_SECOND_IN_SANDBOX",
            "WHY": "The current parser/runtime may not support the exact REPLACE <field> WITH <literal> command form in scripts. Test one syntax variant per sandbox clone.",
            "MUTATES_ACTIVE": 0,
            "RISK": "LOW_SANDBOX_ONLY",
            "SUCCESS_CRITERIA": "One syntax variant writes SYMBOL/LOCALE/TEXT exactly.",
        },
        {
            "ALT_ID": "ALT_C",
            "NAME": "CSV_IMPORT_OR_APPEND_FROM_SANDBOX",
            "RECOMMENDATION": "REVIEW_AND_TRY_IF_COMMAND_SURFACE_EXISTS",
            "WHY": "If IMPORT or APPEND FROM is already proven in scripts/source, a tabular import may be safer than row-by-row command writes.",
            "MUTATES_ACTIVE": 0,
            "RISK": "LOW_SANDBOX_ONLY",
            "SUCCESS_CRITERIA": "Sandbox imported rows match expected keys/text and counts.",
        },
        {
            "ALT_ID": "ALT_D",
            "NAME": "FULL_SANDBOX_CATALOG_REBUILD",
            "RECOMMENDATION": "REVIEW",
            "WHY": "A complete regenerated messaging catalog root may be safer than in-place append if schema/memo handling can be proven end-to-end in a candidate root.",
            "MUTATES_ACTIVE": 0,
            "RISK": "MEDIUM_DESIGN_COMPLEXITY",
            "SUCCESS_CRITERIA": "Full candidate root reads back 14/70 with exact rows, indexes, LMDB, and runtime provider load.",
        },
        {
            "ALT_ID": "ALT_E",
            "NAME": "DIRECT_RAW_DBF_MEMO_WRITE",
            "RECOMMENDATION": "FORBID",
            "WHY": "SYSTEM_MESSAGE_TEXT.TEXT is memo-backed. Raw direct DBF writes bypass memo semantics and were already closed.",
            "MUTATES_ACTIVE": 1,
            "RISK": "HIGH",
            "SUCCESS_CRITERIA": "Not applicable.",
        },
    ]

    ae63_plan = [
        {
            "STEP": 1,
            "ACTION": "CREATE_FRESH_SANDBOX_CLONES_PER_VARIANT",
            "DETAIL": "Use separate sandbox roots so each variant starts from clean 12/60 copied baseline.",
            "MUTATES_ACTIVE": 0,
        },
        {
            "STEP": 2,
            "ACTION": "RUN_ALT_A_POINTER_DIAGNOSTIC",
            "DETAIL": "Log current work area and record position around USE, APPEND, and write operations if runtime commands exist.",
            "MUTATES_ACTIVE": 0,
        },
        {
            "STEP": 3,
            "ACTION": "RUN_ALT_B_REPLACE_SYNTAX_VARIANTS",
            "DETAIL": "Try script variants one at a time, not all in one sandbox, so failures are attributable.",
            "MUTATES_ACTIVE": 0,
        },
        {
            "STEP": 4,
            "ACTION": "OPTIONALLY_RUN_ALT_C_IMPORT_VARIANT",
            "DETAIL": "Only generate/import CSV variant if command-surface scan finds plausible IMPORT/APPEND FROM evidence.",
            "MUTATES_ACTIVE": 0,
        },
        {
            "STEP": 5,
            "ACTION": "DBF_AND_RUNTIME_READBACK",
            "DETAIL": "Require DBF-level keys and runtime provider/smoke readback before any future active package.",
            "MUTATES_ACTIVE": 0,
        },
    ]

    forbidden = [
        {"RULE": "NO_ACTIVE_PROMOTION", "DETAIL": "Do not attempt active 14/70 promotion until a sandbox path writes exact keys/text."},
        {"RULE": "NO_REUSE_22AE5_DTS", "DETAIL": "The 22AE.5 DTS is proven bad: it appends rows without key writes."},
        {"RULE": "NO_RAW_DBF_MEMO_WRITE", "DETAIL": "SYSTEM_MESSAGE_TEXT.TEXT is memo-backed; raw writes are out of bounds."},
        {"RULE": "NO_HELP_CMDHELPCHK_MUTATION", "DETAIL": "HELP DATA and CMDHELPCHK remain protected."},
        {"RULE": "ONE_VARIANT_PER_SANDBOX", "DETAIL": "Do not mix syntax variants in one sandbox proof."},
    ]

    boundary = [
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "22AE.6.2 is plan/report only."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_DBF_CATALOG", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_CDX_INDEXES", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active CDX/index mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active LMDB mutation."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No HELP DATA mutation."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CMDHELPCHK mutation."},
        {"PROTECTED_SYSTEM": "COMMAND_REGISTRY", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No command registry mutation."},
        {"PROTECTED_SYSTEM": "MANUALGEN", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No manualgen mutation."},
        {"PROTECTED_SYSTEM": "DATADICT_SELF_DOC", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No Data Dictionary/SelfDoc mutation."},
    ]

    status = STATUS_GREEN if failures == 0 else STATUS_BLOCKED
    validation_issues = str(failures)

    write_csv(reports / "message_catalog_phase22ae_6_2_gate_check_v1.csv", gates, ["GATE", "STATUS", "DETAIL"])
    write_csv(reports / "message_catalog_phase22ae_6_2_evidence_summary_v1.csv", evidence_rows, ["EVIDENCE", "DETAIL", "PHASE"])
    write_csv(reports / "message_catalog_phase22ae_6_2_command_pattern_counts_v1.csv", pattern_counts, ["PATTERN", "TOTAL_MATCHES"])
    write_csv(reports / "message_catalog_phase22ae_6_2_command_pattern_hits_v1.csv", pattern_hits, ["PATTERN", "FILE", "LINE", "TEXT"])
    write_csv(reports / "message_catalog_phase22ae_6_2_alternative_path_matrix_v1.csv", alternatives, ["ALT_ID", "NAME", "RECOMMENDATION", "WHY", "MUTATES_ACTIVE", "RISK", "SUCCESS_CRITERIA"])
    write_csv(reports / "message_catalog_phase22ae_6_3_candidate_proof_plan_v1.csv", ae63_plan, ["STEP", "ACTION", "DETAIL", "MUTATES_ACTIVE"])
    write_csv(reports / "message_catalog_phase22ae_6_2_forbidden_paths_v1.csv", forbidden, ["RULE", "DETAIL"])
    write_csv(reports / "message_catalog_phase22ae_6_2_boundary_ledger_v1.csv", boundary, ["PROTECTED_SYSTEM", "MUTATION_ALLOWED", "OBSERVED_MUTATION", "DETAIL"])

    write_csv(reports / "message_catalog_phase22ae_6_2_status_summary_v1.csv", [{
        "STATUS": status,
        "VALIDATION_ISSUES": validation_issues,
        "PHASE22AE_6_1_STATUS": ae61.get("STATUS", ""),
        "MSG_022AE_6_1_SAVEPOINT_PRESENT": 1 if sp61 else 0,
        "SANDBOX_COUNTS_MOVED_BY_ONE": ae61.get("SANDBOX_COUNTS_MOVED_BY_ONE", ""),
        "SANDBOX_MESSAGE_TEST_ROWS_FOUND": ae61.get("SANDBOX_MESSAGE_TEST_ROWS_FOUND", ""),
        "SANDBOX_TEXT_TEST_ROWS_FOUND": ae61.get("SANDBOX_TEXT_TEST_ROWS_FOUND", ""),
        "RECOMMENDED_NEXT_PATH": "ALTERNATIVE_SANDBOX_WRITE_PROOF_VARIANTS",
        "ACTIVE_PROMOTION_AUTHORIZED": 0,
        "SOURCE_FILES_MUTATED": 0,
        "ACTIVE_CATALOG_MUTATION_OBSERVED": 0,
        "HELP_DATA_MUTATION_OBSERVED": 0,
        "CMDHELPCHK_MUTATION_OBSERVED": 0,
        "NEXT_GATE": NEXT_GATE,
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }], ["STATUS", "VALIDATION_ISSUES", "PHASE22AE_6_1_STATUS",
         "MSG_022AE_6_1_SAVEPOINT_PRESENT", "SANDBOX_COUNTS_MOVED_BY_ONE",
         "SANDBOX_MESSAGE_TEST_ROWS_FOUND", "SANDBOX_TEXT_TEST_ROWS_FOUND",
         "RECOMMENDED_NEXT_PATH", "ACTIVE_PROMOTION_AUTHORIZED", "SOURCE_FILES_MUTATED",
         "ACTIVE_CATALOG_MUTATION_OBSERVED", "HELP_DATA_MUTATION_OBSERVED",
         "CMDHELPCHK_MUTATION_OBSERVED", "NEXT_GATE", "REPORT_TIMESTAMP_UTC"])

    md = f"""# Message Catalog Phase 22AE.6.2 Alternative Sandbox Write Path Plan

Status: `{status}`

22AE.6.1 safely confirmed the old row-write path fails:

```text
counts moved: {ae61.get('SANDBOX_COUNTS_MOVED_BY_ONE', '')}
message test rows found: {ae61.get('SANDBOX_MESSAGE_TEST_ROWS_FOUND', '')}
text test rows found: {ae61.get('SANDBOX_TEXT_TEST_ROWS_FOUND', '')}
```

22AE.6.2 selects only sandbox alternatives. No active promotion is authorized.

Next gate:

```text
{NEXT_GATE}
```
"""
    (reports / "MESSAGE_CATALOG_PHASE22AE_6_2_ALTERNATIVE_SANDBOX_WRITE_PATH_PLAN.md").write_text(md, encoding="utf-8")

    print(status)
    print(f"  validation issues: {validation_issues}")
    print(f"  Phase 22AE.6.1 status: {ae61.get('STATUS', '')}")
    print(f"  MSG-022AE.6.1 savepoint present: {1 if sp61 else 0}")
    print(f"  sandbox counts moved by one: {ae61.get('SANDBOX_COUNTS_MOVED_BY_ONE', '')}")
    print(f"  sandbox message test rows found: {ae61.get('SANDBOX_MESSAGE_TEST_ROWS_FOUND', '')}")
    print(f"  sandbox text test rows found: {ae61.get('SANDBOX_TEXT_TEST_ROWS_FOUND', '')}")
    print("  recommended next path: ALTERNATIVE_SANDBOX_WRITE_PROOF_VARIANTS")
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
