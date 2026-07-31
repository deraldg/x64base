#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

STATUS_GREEN = "LOCALE_PHASE23B_CANDIDATE_SYSTEM_LOCALE_SCHEMA_STAGING_GREEN"
STATUS_BLOCKED = "LOCALE_PHASE23B_CANDIDATE_SYSTEM_LOCALE_SCHEMA_STAGING_BLOCKED"
NEXT_GATE = "HOLD_OR_AUTHORIZE_PHASE23C_CANDIDATE_SYSTEM_LOCALES_X64_DBF_RUNTIME_EXECUTION"
LOCALE_REPORT_DIR = Path("docs/locale/reports")
CANDIDATE_ROOT = Path("docs/locale/candidates/phase23b_shared_locale_spine_candidate")

SYSTEM_LOCALES_ROWS = [
    {
        "LOCALE_ID": "en-US",
        "BASE_LOCALE": "en",
        "DISPLAY_NAME": "English (United States)",
        "TEXT_DIR": "LTR",
        "LOCALE_STATUS": "DEFAULT_ACTIVE",
        "DEFAULT_LOCALE": ".T.",
        "FALLBACK_ALLOWED": ".F.",
        "SRC": "LOC-023A",
    },
    {
        "LOCALE_ID": "es",
        "BASE_LOCALE": "es",
        "DISPLAY_NAME": "Spanish",
        "TEXT_DIR": "LTR",
        "LOCALE_STATUS": "ACTIVE",
        "DEFAULT_LOCALE": ".F.",
        "FALLBACK_ALLOWED": ".T.",
        "SRC": "LOC-023A",
    },
    {
        "LOCALE_ID": "fr",
        "BASE_LOCALE": "fr",
        "DISPLAY_NAME": "French",
        "TEXT_DIR": "LTR",
        "LOCALE_STATUS": "ACTIVE",
        "DEFAULT_LOCALE": ".F.",
        "FALLBACK_ALLOWED": ".T.",
        "SRC": "LOC-023A",
    },
    {
        "LOCALE_ID": "de",
        "BASE_LOCALE": "de",
        "DISPLAY_NAME": "German",
        "TEXT_DIR": "LTR",
        "LOCALE_STATUS": "ACTIVE",
        "DEFAULT_LOCALE": ".F.",
        "FALLBACK_ALLOWED": ".T.",
        "SRC": "LOC-023A",
    },
    {
        "LOCALE_ID": "it",
        "BASE_LOCALE": "it",
        "DISPLAY_NAME": "Italian",
        "TEXT_DIR": "LTR",
        "LOCALE_STATUS": "ACTIVE",
        "DEFAULT_LOCALE": ".F.",
        "FALLBACK_ALLOWED": ".T.",
        "SRC": "LOC-023A",
    },
]

FALLBACK_ROWS = [
    {
        "FBID": "FB-001",
        "LOCALE_ID": "es",
        "FALLBACK_TO": "en-US",
        "FALLBACK_ORDER": "100",
        "FALLBACK_TYPE": "DEFAULT",
        "APPLIES_TO": "ALL_CONSUMERS_WHEN_ENABLED",
        "RULE_STATUS": "PLANNED_FROM_RUNTIME_PROOF",
        "SRC": "LOC-023A",
    },
    {
        "FBID": "FB-002",
        "LOCALE_ID": "fr",
        "FALLBACK_TO": "en-US",
        "FALLBACK_ORDER": "100",
        "FALLBACK_TYPE": "DEFAULT",
        "APPLIES_TO": "ALL_CONSUMERS_WHEN_ENABLED",
        "RULE_STATUS": "PLANNED",
        "SRC": "LOC-023A",
    },
    {
        "FBID": "FB-003",
        "LOCALE_ID": "de",
        "FALLBACK_TO": "en-US",
        "FALLBACK_ORDER": "100",
        "FALLBACK_TYPE": "DEFAULT",
        "APPLIES_TO": "ALL_CONSUMERS_WHEN_ENABLED",
        "RULE_STATUS": "PLANNED",
        "SRC": "LOC-023A",
    },
    {
        "FBID": "FB-004",
        "LOCALE_ID": "it",
        "FALLBACK_TO": "en-US",
        "FALLBACK_ORDER": "100",
        "FALLBACK_TYPE": "DEFAULT",
        "APPLIES_TO": "ALL_CONSUMERS_WHEN_ENABLED",
        "RULE_STATUS": "PLANNED",
        "SRC": "LOC-023A",
    },
    {
        "FBID": "FB-005",
        "LOCALE_ID": "*",
        "FALLBACK_TO": "en-US",
        "FALLBACK_ORDER": "999",
        "FALLBACK_TYPE": "GLOBAL_DEFAULT",
        "APPLIES_TO": "RUNTIME_LOOKUP_WHEN_ENABLED",
        "RULE_STATUS": "PROVEN_NOT_TABLE_BACKED_YET",
        "SRC": "MSG-022G-022I",
    },
]

def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

def first_row(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    rows = read_csv(path)
    return rows[0] if rows else {}

def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        w.writeheader()
        for row in rows:
            w.writerow({k: row.get(k, "") for k in fields})

def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def dq(value: str) -> str:
    escaped = str(value).replace('"', '""')
    return f'"{escaped}"'

def dts_replace(row: dict[str, str], logical_fields: set[str], numeric_fields: set[str]) -> list[str]:
    lines = ["APPEND"]
    for key, value in row.items():
        if key in logical_fields:
            lines.append(f"REPLACE {key} WITH {value}")
        elif key in numeric_fields:
            lines.append(f"REPLACE {key} WITH {value}")
        else:
            lines.append(f"REPLACE {key} WITH {dq(value)}")
    lines.append("")
    return lines

def make_create_script(repo: Path) -> str:
    candidate = repo / CANDIDATE_ROOT
    dbf = candidate / "dbf"
    indexes = candidate / "indexes"
    lmdb = candidate / "lmdb"
    lines = [
        "* LOCALE_PHASE23B_CREATE_X64_LOCALE_SPINE_CANDIDATES.dts",
        "* Candidate-only x64 DBF creation for shared locale spine.",
        "* Boundary: inactive candidate path only; no active catalog promotion.",
        "CLOSE ALL",
        f"SET PATH DBF {dbf}",
        f"SET PATH INDEXES {indexes}",
        f"SET PATH LMDB {lmdb}",
        "",
        "* Clean prior inactive candidate tables from this candidate path only.",
        "ERASE SYSTEM_LOCALES CONFIRM",
        "ERASE SYSTEM_LOCALE_FALLBACK CONFIRM",
        "",
        "* Create shared locale spine candidate tables as native x64 DBFs.",
        "CREATE X64 SYSTEM_LOCALES (LOCALE_ID C(16), BASE_LOCALE C(16), DISPLAY_NAME C(80), TEXT_DIR C(3), LOCALE_STATUS C(24), DEFAULT_LOCALE L, FALLBACK_ALLOWED L, SRC C(32))",
        "",
    ]
    for row in SYSTEM_LOCALES_ROWS:
        lines.extend(dts_replace(row, {"DEFAULT_LOCALE", "FALLBACK_ALLOWED"}, set()))

    lines.extend([
        "CREATE X64 SYSTEM_LOCALE_FALLBACK (FBID C(16), LOCALE_ID C(16), FALLBACK_TO C(16), FALLBACK_ORDER N(6,0), FALLBACK_TYPE C(24), APPLIES_TO C(80), RULE_STATUS C(32), SRC C(32))",
        "",
    ])
    for row in FALLBACK_ROWS:
        lines.extend(dts_replace(row, set(), {"FALLBACK_ORDER"}))

    lines.extend([
        "SELECT 2",
        "* Phase 23B candidate x64 locale spine DBF create/seed script complete.",
        "",
    ])
    return "\n".join(lines)

def make_cdx_script(repo: Path) -> str:
    candidate = repo / CANDIDATE_ROOT
    dbf = candidate / "dbf"
    indexes = candidate / "indexes"
    lmdb = candidate / "lmdb"
    lines = [
        "* LOCALE_PHASE23B_CREATE_CANDIDATE_CDX_TAGS.dts",
        "* Candidate-only CDX tag script for shared locale spine.",
        "* Boundary: inactive candidate path only; no active catalog promotion.",
        "CLOSE ALL",
        f"SET PATH DBF {dbf}",
        f"SET PATH INDEXES {indexes}",
        f"SET PATH LMDB {lmdb}",
        "",
        "SELECT 0",
        "USE SYSTEM_LOCALES",
        "CDX CREATE",
        "CDX ADDTAG LOCALE_ID",
        "CDX ADDTAG BASE_LOCALE",
        "CDX ADDTAG LOCALE_STATUS",
        "CDX ADDTAG SRC",
        "",
        "SELECT 1",
        "USE SYSTEM_LOCALE_FALLBACK",
        "CDX CREATE",
        "CDX ADDTAG FBID",
        "CDX ADDTAG LOCALE_ID",
        "CDX ADDTAG FALLBACK_TO",
        "CDX ADDTAG FALLBACK_ORDER",
        "CDX ADDTAG FALLBACK_TYPE",
        "",
        "SELECT 2",
        "* Phase 23B candidate CDX tag script complete.",
        "",
    ]
    return "\n".join(lines)

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--accept-candidate-schema-staging", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    reports = repo / LOCALE_REPORT_DIR
    reports.mkdir(parents=True, exist_ok=True)

    phase23a = first_row(reports / "locale_phase23a_status_summary_v1.csv")
    proven_locales = phase23a.get("CURRENT_PROVEN_LOCALES", "de;en-US;es;fr;it")
    proof_messages = phase23a.get("MESSAGING_PROOF_MESSAGES", "12")
    proof_text_rows = phase23a.get("MESSAGING_PROOF_TEXT_ROWS", "60")

    gates: list[dict[str, Any]] = []
    failures = 0

    def gate(name: str, ok: bool, detail: str) -> None:
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": detail})
        if not ok:
            failures += 1

    gate("OPERATOR_ACCEPTED_CANDIDATE_SCHEMA_STAGING",
         args.accept_candidate_schema_staging,
         "requires --accept-candidate-schema-staging")
    gate("PHASE23A_SHARED_LOCALE_CONTRACT_GREEN",
         phase23a.get("STATUS") == "LOCALE_PHASE23A_SHARED_LOCALE_CONTRACT_GREEN_REPORT_ONLY",
         phase23a.get("STATUS", ""))
    gate("PHASE23A_VALIDATION_ZERO",
         phase23a.get("VALIDATION_ISSUES", "") == "0",
         f"validation_issues={phase23a.get('VALIDATION_ISSUES', '')}")

    candidate = repo / CANDIDATE_ROOT
    dbf_dir = candidate / "dbf"
    index_dir = candidate / "indexes"
    lmdb_dir = candidate / "lmdb"
    scripts_dir = candidate / "scripts"

    status = STATUS_GREEN if failures == 0 else STATUS_BLOCKED
    validation_issues = str(failures)

    if status == STATUS_GREEN:
        for p in [dbf_dir, index_dir, lmdb_dir, scripts_dir]:
            p.mkdir(parents=True, exist_ok=True)

        create_script = make_create_script(repo)
        cdx_script = make_cdx_script(repo)

        create_path = scripts_dir / "LOCALE_PHASE23B_CREATE_X64_LOCALE_SPINE_CANDIDATES.dts"
        cdx_path = scripts_dir / "LOCALE_PHASE23B_CREATE_CANDIDATE_CDX_TAGS.dts"
        create_path.write_text(create_script, encoding="utf-8")
        cdx_path.write_text(cdx_script, encoding="utf-8")

        write_csv(candidate / "SYSTEM_LOCALES_seed_plan_v1.csv", SYSTEM_LOCALES_ROWS,
                  ["LOCALE_ID", "BASE_LOCALE", "DISPLAY_NAME", "TEXT_DIR", "LOCALE_STATUS",
                   "DEFAULT_LOCALE", "FALLBACK_ALLOWED", "SRC"])
        write_csv(candidate / "SYSTEM_LOCALE_FALLBACK_seed_plan_v1.csv", FALLBACK_ROWS,
                  ["FBID", "LOCALE_ID", "FALLBACK_TO", "FALLBACK_ORDER", "FALLBACK_TYPE",
                   "APPLIES_TO", "RULE_STATUS", "SRC"])

    schema_rows = [
        {"TABLE": "SYSTEM_LOCALES", "FIELD": "LOCALE_ID", "TYPE": "C(16)", "ROLE": "canonical shared locale key", "TAG_PLAN": "LOCALE_ID"},
        {"TABLE": "SYSTEM_LOCALES", "FIELD": "BASE_LOCALE", "TYPE": "C(16)", "ROLE": "base language/parent tag", "TAG_PLAN": "BASE_LOCALE"},
        {"TABLE": "SYSTEM_LOCALES", "FIELD": "DISPLAY_NAME", "TYPE": "C(80)", "ROLE": "human-readable locale name", "TAG_PLAN": ""},
        {"TABLE": "SYSTEM_LOCALES", "FIELD": "TEXT_DIR", "TYPE": "C(3)", "ROLE": "LTR/RTL", "TAG_PLAN": ""},
        {"TABLE": "SYSTEM_LOCALES", "FIELD": "LOCALE_STATUS", "TYPE": "C(24)", "ROLE": "locale status", "TAG_PLAN": "LOCALE_STATUS"},
        {"TABLE": "SYSTEM_LOCALES", "FIELD": "DEFAULT_LOCALE", "TYPE": "L", "ROLE": "default locale flag", "TAG_PLAN": ""},
        {"TABLE": "SYSTEM_LOCALES", "FIELD": "FALLBACK_ALLOWED", "TYPE": "L", "ROLE": "fallback allowed flag", "TAG_PLAN": ""},
        {"TABLE": "SYSTEM_LOCALES", "FIELD": "SRC", "TYPE": "C(32)", "ROLE": "source/provenance lane", "TAG_PLAN": "SRC"},
        {"TABLE": "SYSTEM_LOCALE_FALLBACK", "FIELD": "FBID", "TYPE": "C(16)", "ROLE": "stable fallback row id", "TAG_PLAN": "FBID"},
        {"TABLE": "SYSTEM_LOCALE_FALLBACK", "FIELD": "LOCALE_ID", "TYPE": "C(16)", "ROLE": "source locale", "TAG_PLAN": "LOCALE_ID"},
        {"TABLE": "SYSTEM_LOCALE_FALLBACK", "FIELD": "FALLBACK_TO", "TYPE": "C(16)", "ROLE": "fallback locale", "TAG_PLAN": "FALLBACK_TO"},
        {"TABLE": "SYSTEM_LOCALE_FALLBACK", "FIELD": "FALLBACK_ORDER", "TYPE": "N(6,0)", "ROLE": "fallback priority", "TAG_PLAN": "FALLBACK_ORDER"},
        {"TABLE": "SYSTEM_LOCALE_FALLBACK", "FIELD": "FALLBACK_TYPE", "TYPE": "C(24)", "ROLE": "fallback rule kind", "TAG_PLAN": "FALLBACK_TYPE"},
        {"TABLE": "SYSTEM_LOCALE_FALLBACK", "FIELD": "APPLIES_TO", "TYPE": "C(80)", "ROLE": "consumer applicability", "TAG_PLAN": ""},
        {"TABLE": "SYSTEM_LOCALE_FALLBACK", "FIELD": "RULE_STATUS", "TYPE": "C(32)", "ROLE": "rule status/provenance state", "TAG_PLAN": ""},
        {"TABLE": "SYSTEM_LOCALE_FALLBACK", "FIELD": "SRC", "TYPE": "C(32)", "ROLE": "source/provenance lane", "TAG_PLAN": ""},
    ]

    script_rows = []
    if status == STATUS_GREEN:
        for p, role in [
            (scripts_dir / "LOCALE_PHASE23B_CREATE_X64_LOCALE_SPINE_CANDIDATES.dts", "candidate x64 DBF create and seed script"),
            (scripts_dir / "LOCALE_PHASE23B_CREATE_CANDIDATE_CDX_TAGS.dts", "candidate CDX tag script for later execution"),
            (candidate / "SYSTEM_LOCALES_seed_plan_v1.csv", "seed plan for SYSTEM_LOCALES"),
            (candidate / "SYSTEM_LOCALE_FALLBACK_seed_plan_v1.csv", "seed plan for SYSTEM_LOCALE_FALLBACK"),
        ]:
            if p.exists():
                text = p.read_text(encoding="utf-8", errors="replace")
                script_rows.append({
                    "ARTIFACT": p.relative_to(repo).as_posix(),
                    "ROLE": role,
                    "BYTES": p.stat().st_size,
                    "SHA256": sha256_text(text),
                })

    boundary = [
        {"PROTECTED_SYSTEM": "INACTIVE_LOCALE_CANDIDATE_SCRIPTS", "MUTATION_ALLOWED": 1, "OBSERVED_MUTATION": len(script_rows), "DETAIL": "Candidate scripts/seed-plan artifacts staged under docs/locale/candidates only."},
        {"PROTECTED_SYSTEM": "INACTIVE_LOCALE_CANDIDATE_DBF", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No DBF runtime execution in Phase 23B; only create script staged."},
        {"PROTECTED_SYSTEM": "INACTIVE_LOCALE_CANDIDATE_CDX", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CDX runtime execution in Phase 23B; only CDX script staged."},
        {"PROTECTED_SYSTEM": "INACTIVE_LOCALE_CANDIDATE_LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No LMDB runtime execution in Phase 23B."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_DBF_CATALOG", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active Messaging catalog mutation."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No HELP DATA mutation."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CMDHELPCHK mutation."},
        {"PROTECTED_SYSTEM": "MANUALGEN", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No manualgen mutation."},
        {"PROTECTED_SYSTEM": "DATADICT_SELF_DOC", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No Data Dictionary/SelfDoc mutation."},
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No source mutation."},
    ]

    write_csv(reports / "locale_phase23b_status_summary_v1.csv", [{
        "STATUS": status,
        "PROVEN_LOCALES_FROM_23A": proven_locales,
        "MESSAGING_PROOF_MESSAGES": proof_messages,
        "MESSAGING_PROOF_TEXT_ROWS": proof_text_rows,
        "VALIDATION_ISSUES": validation_issues,
        "SYSTEM_LOCALES_SEED_ROWS": len(SYSTEM_LOCALES_ROWS),
        "SYSTEM_LOCALE_FALLBACK_SEED_ROWS": len(FALLBACK_ROWS),
        "CANDIDATE_CREATE_SCRIPT_STAGED": 1 if status == STATUS_GREEN else 0,
        "CANDIDATE_CDX_SCRIPT_STAGED": 1 if status == STATUS_GREEN else 0,
        "CANDIDATE_DBF_FILES_CREATED": 0,
        "CANDIDATE_CDX_FILES_CREATED": 0,
        "CANDIDATE_LMDB_ENVS_CREATED": 0,
        "PROTECTED_MUTATIONS": 0,
        "NEXT_GATE": NEXT_GATE,
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }], ["STATUS", "PROVEN_LOCALES_FROM_23A", "MESSAGING_PROOF_MESSAGES",
         "MESSAGING_PROOF_TEXT_ROWS", "VALIDATION_ISSUES", "SYSTEM_LOCALES_SEED_ROWS",
         "SYSTEM_LOCALE_FALLBACK_SEED_ROWS", "CANDIDATE_CREATE_SCRIPT_STAGED",
         "CANDIDATE_CDX_SCRIPT_STAGED", "CANDIDATE_DBF_FILES_CREATED",
         "CANDIDATE_CDX_FILES_CREATED", "CANDIDATE_LMDB_ENVS_CREATED",
         "PROTECTED_MUTATIONS", "NEXT_GATE", "REPORT_TIMESTAMP_UTC"])

    write_csv(reports / "locale_phase23b_gate_check_v1.csv", gates, ["GATE", "STATUS", "DETAIL"])
    write_csv(reports / "locale_phase23b_schema_inventory_v1.csv", schema_rows,
              ["TABLE", "FIELD", "TYPE", "ROLE", "TAG_PLAN"])
    write_csv(reports / "locale_phase23b_seed_inventory_system_locales_v1.csv", SYSTEM_LOCALES_ROWS,
              ["LOCALE_ID", "BASE_LOCALE", "DISPLAY_NAME", "TEXT_DIR", "LOCALE_STATUS",
               "DEFAULT_LOCALE", "FALLBACK_ALLOWED", "SRC"])
    write_csv(reports / "locale_phase23b_seed_inventory_fallback_v1.csv", FALLBACK_ROWS,
              ["FBID", "LOCALE_ID", "FALLBACK_TO", "FALLBACK_ORDER", "FALLBACK_TYPE",
               "APPLIES_TO", "RULE_STATUS", "SRC"])
    write_csv(reports / "locale_phase23b_staged_artifact_inventory_v1.csv", script_rows,
              ["ARTIFACT", "ROLE", "BYTES", "SHA256"])
    write_csv(reports / "locale_phase23b_boundary_ledger_v1.csv", boundary,
              ["PROTECTED_SYSTEM", "MUTATION_ALLOWED", "OBSERVED_MUTATION", "DETAIL"])

    plan_md = f"""# Locale Phase 23B — Candidate System Locale Schema Staging

Status: `{status}`

Phase 23B stages inactive candidate scripts for the shared locale spine:

```text
SYSTEM_LOCALES
SYSTEM_LOCALE_FALLBACK
```

This is candidate staging only. It does not execute DotTalk++, does not create
DBF/CDX/LMDB artifacts, and does not promote any active catalog.

## Candidate workspace

```text
docs/locale/candidates/phase23b_shared_locale_spine_candidate
```

## Staged scripts

```text
docs/locale/candidates/phase23b_shared_locale_spine_candidate/scripts/LOCALE_PHASE23B_CREATE_X64_LOCALE_SPINE_CANDIDATES.dts
docs/locale/candidates/phase23b_shared_locale_spine_candidate/scripts/LOCALE_PHASE23B_CREATE_CANDIDATE_CDX_TAGS.dts
```

## Seed rows

```text
SYSTEM_LOCALES: {len(SYSTEM_LOCALES_ROWS)}
SYSTEM_LOCALE_FALLBACK: {len(FALLBACK_ROWS)}
```

## Runtime execution status

```text
candidate DBF files created: 0
candidate CDX files created: 0
candidate LMDB envs created: 0
```

## Next gate

```text
{NEXT_GATE}
```
"""
    plan_path = repo / "docs/locale/LOCALE_PHASE23B_CANDIDATE_SYSTEM_LOCALE_SCHEMA_STAGING.md"
    plan_path.write_text(plan_md, encoding="utf-8")

    manifest_rows = script_rows[:]
    for p, role in [
        (reports / "locale_phase23b_status_summary_v1.csv", "phase23b status summary"),
        (reports / "locale_phase23b_schema_inventory_v1.csv", "phase23b schema inventory"),
        (reports / "locale_phase23b_boundary_ledger_v1.csv", "phase23b boundary ledger"),
        (plan_path, "phase23b narrative plan"),
    ]:
        if p.exists():
            text = p.read_text(encoding="utf-8", errors="replace")
            manifest_rows.append({
                "ARTIFACT": p.relative_to(repo).as_posix(),
                "ROLE": role,
                "BYTES": p.stat().st_size,
                "SHA256": sha256_text(text),
            })
    write_csv(reports / "locale_phase23b_artifact_manifest_v1.csv", manifest_rows,
              ["ARTIFACT", "ROLE", "BYTES", "SHA256"])

    print(status)
    print(f"  proven locales from 23A: {proven_locales.replace(';', ', ')}")
    print(f"  validation issues: {validation_issues}")
    print(f"  SYSTEM_LOCALES seed rows: {len(SYSTEM_LOCALES_ROWS)}")
    print(f"  SYSTEM_LOCALE_FALLBACK seed rows: {len(FALLBACK_ROWS)}")
    print(f"  candidate create script staged: {1 if status == STATUS_GREEN else 0}")
    print(f"  candidate cdx script staged: {1 if status == STATUS_GREEN else 0}")
    print("  candidate dbf files created: 0")
    print("  candidate cdx files created: 0")
    print("  candidate lmdb envs created: 0")
    print(f"  next gate: {NEXT_GATE}")
    print(f"  reports: {reports}")
    return 0 if status == STATUS_GREEN else 2

if __name__ == "__main__":
    raise SystemExit(main())
