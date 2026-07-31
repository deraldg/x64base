#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

STATUS_GREEN = "LOCALE_PHASE23J_GUARDED_MESSAGING_LOCALE_SPINE_SOURCE_PATCH_PLAN_GREEN_SOURCE_HELD"
STATUS_BLOCKED = "LOCALE_PHASE23J_GUARDED_MESSAGING_LOCALE_SPINE_SOURCE_PATCH_PLAN_BLOCKED"
NEXT_GATE = "HOLD_OR_AUTHORIZE_PHASE23K_GUARDED_MESSAGING_LOCALE_SPINE_SOURCE_PATCH_APPLICATION"
LOCALE_REPORT_DIR = Path("docs/locale/reports")

PATCH_TARGETS = [
    {
        "PATCH_ID": "23K-001",
        "TARGET_PATH": "src/help/message_catalog.hpp",
        "ACTION": "DECLARE_READ_ONLY_LOCALE_SPINE_TYPES_AND_API",
        "INTENT": "Declare small runtime-facing structs/functions for active shared locale spine status, supported locale check, and fallback chain lookup.",
        "MUTATION_PHASE": "23K if explicitly authorized",
        "SAFETY": "Must not remove existing compiled fallback or active Messaging catalog interfaces.",
    },
    {
        "PATCH_ID": "23K-002",
        "TARGET_PATH": "src/help/message_catalog.cpp",
        "ACTION": "IMPLEMENT_READ_ONLY_ACTIVE_LOCALE_SPINE_HELPER",
        "INTENT": "Open/read active SYSTEM_LOCALES and SYSTEM_LOCALE_FALLBACK from dottalkpp/data/locale paths and expose status/fallback helpers.",
        "MUTATION_PHASE": "23K if explicitly authorized",
        "SAFETY": "Read-only; no DBF/CDX/LMDB mutation; missing spine falls back to current behavior.",
    },
    {
        "PATCH_ID": "23K-003",
        "TARGET_PATH": "src/cli/cmd_set.cpp",
        "ACTION": "ADD_STATUS_OR_CHECK_SURFACE_FOR_LOCALE_SPINE",
        "INTENT": "Allow SET LANGUAGE / SET MESSAGE CATALOG status/check path to report locale spine availability without changing normal language selection semantics.",
        "MUTATION_PHASE": "23K if explicitly authorized",
        "SAFETY": "Current SET LANGUAGE and SET MESSAGE CATALOG GET behavior must remain green.",
    },
    {
        "PATCH_ID": "23K-004",
        "TARGET_PATH": "docs/locale/scripts/LOCALE_PHASE23K_RUNTIME_SMOKE.dts",
        "ACTION": "STAGE_RUNTIME_SMOKE_SCRIPT",
        "INTENT": "Smoke should prove current Messaging lookup still works and active locale spine status/fallback is reported read-only.",
        "MUTATION_PHASE": "23K or later if explicitly authorized",
        "SAFETY": "DotScript only; no HELP/CMDHELPCHK/manualgen/Data Dictionary/SelfDoc mutation.",
    },
]

API_ROWS = [
    {
        "API_ID": "LOCSPINE-001",
        "API_NAME": "active_locale_spine_status",
        "CALL_SITE": "message_catalog provider/status surface",
        "INPUT": "none",
        "OUTPUT": "available, active dbf/index/lmdb dirs, locale_count, fallback_rule_count, detail",
        "FALLBACK": "If unavailable, report unavailable and preserve current Messaging provider behavior.",
    },
    {
        "API_ID": "LOCSPINE-002",
        "API_NAME": "active_locale_is_supported",
        "CALL_SITE": "SET LANGUAGE validation/check and message lookup planning",
        "INPUT": "requested_locale",
        "OUTPUT": "supported bool, normalized_locale, status detail",
        "FALLBACK": "If spine unavailable, use current Messaging catalog locale discovery.",
    },
    {
        "API_ID": "LOCSPINE-003",
        "API_NAME": "active_locale_fallback_chain",
        "CALL_SITE": "Messaging lookup fallback guidance",
        "INPUT": "requested_locale",
        "OUTPUT": "ordered fallback locale list ending in en-US when allowed",
        "FALLBACK": "If spine unavailable or invalid, use proven en-US fallback.",
    },
    {
        "API_ID": "LOCSPINE-004",
        "API_NAME": "message_lookup_preserving_current_provider",
        "CALL_SITE": "SET MESSAGE CATALOG GET / SET LANGUAGE emission",
        "INPUT": "symbol, requested_locale, optional args",
        "OUTPUT": "localized text, provider mode, resolved/fallback locale",
        "FALLBACK": "Current active_dbf and compiled fallback remain authoritative safety net.",
    },
]

SMOKE_ROWS = [
    {
        "SMOKE_ID": "23K-SMOKE-001",
        "COMMAND_OR_SCRIPT": "SET MESSAGE CATALOG CHECK",
        "EXPECTED": "Current Messaging catalog validation remains green with 12 messages and 60 text rows.",
        "BOUNDARY": "read-only",
    },
    {
        "SMOKE_ID": "23K-SMOKE-002",
        "COMMAND_OR_SCRIPT": "SET MESSAGE CATALOG GET HELP_HINT_COMMAND LOCALE es ARG command=USE",
        "EXPECTED": "Spanish active_dbf message lookup still returns substituted HELP USE text.",
        "BOUNDARY": "read-only",
    },
    {
        "SMOKE_ID": "23K-SMOKE-003",
        "COMMAND_OR_SCRIPT": "new/extended locale spine status/check surface",
        "EXPECTED": "Reports SYSTEM_LOCALES active, 5 locale rows, SYSTEM_LOCALE_FALLBACK active, 5 fallback rows.",
        "BOUNDARY": "read-only",
    },
    {
        "SMOKE_ID": "23K-SMOKE-004",
        "COMMAND_OR_SCRIPT": "fallback lookup for xx-XX",
        "EXPECTED": "Still resolves through explicit/default fallback to en-US.",
        "BOUNDARY": "read-only",
    },
]

ROLLBACK_ROWS = [
    {
        "ROLLBACK_ID": "RB-001",
        "TRIGGER": "Build failure after source patch",
        "ACTION": "Restore source backups created by patch package; rerun build.",
        "EXPECTED_SAFE_STATE": "Messaging provider remains at LOC-023I/23J behavior.",
    },
    {
        "ROLLBACK_ID": "RB-002",
        "TRIGGER": "Runtime smoke regression in SET LANGUAGE or SET MESSAGE CATALOG GET",
        "ACTION": "Restore patched source files and rebuild; active locale spine data may remain because it is inert without source consumer.",
        "EXPECTED_SAFE_STATE": "Existing active_dbf/compiled fallback behavior restored.",
    },
    {
        "ROLLBACK_ID": "RB-003",
        "TRIGGER": "Locale spine unavailable on target runtime",
        "ACTION": "Provider reports unavailable and continues current Messaging catalog fallback.",
        "EXPECTED_SAFE_STATE": "No runtime crash; no catalog mutation.",
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

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def rel(path: Path, repo: Path) -> str:
    try:
        return path.relative_to(repo).as_posix()
    except ValueError:
        return str(path)

def safe_read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    return read_csv(path)

def summarize_evidence(evidence_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    counts: dict[tuple[str, str], int] = {}
    examples: dict[tuple[str, str], str] = {}
    for row in evidence_rows:
        key = (row.get("SOURCE_PATH", ""), row.get("MATCH_KIND", ""))
        counts[key] = counts.get(key, 0) + 1
        if key not in examples:
            examples[key] = row.get("LINE_TEXT", "")[:200]
    out = []
    for (source, kind), count in sorted(counts.items()):
        out.append({
            "SOURCE_PATH": source,
            "MATCH_KIND": kind,
            "EVIDENCE_ROWS": count,
            "EXAMPLE": examples.get((source, kind), ""),
        })
    return out

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--accept-report-only-guarded-patch-plan", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    reports = repo / LOCALE_REPORT_DIR
    reports.mkdir(parents=True, exist_ok=True)

    phase23i = first_row(reports / "locale_phase23i_status_summary_v1.csv")
    source_scan = safe_read_csv(reports / "locale_phase23i_source_scan_v1.csv")
    source_evidence = safe_read_csv(reports / "locale_phase23i_source_evidence_v1.csv")
    seams = safe_read_csv(reports / "locale_phase23i_integration_seams_v1.csv")
    api_contract = safe_read_csv(reports / "locale_phase23i_runtime_api_contract_v1.csv")

    latest = {}
    latest_path = reports / "locale_savepoint_latest_v1.json"
    if latest_path.exists():
        try:
            latest = json.loads(latest_path.read_text(encoding="utf-8"))
        except Exception:
            latest = {}

    gates: list[dict[str, Any]] = []
    failures = 0

    def gate(name: str, ok: bool, detail: str) -> None:
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": detail})
        if not ok:
            failures += 1

    def review(name: str, ok: bool, detail: str) -> None:
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "REVIEW", "DETAIL": detail})

    gate("OPERATOR_ACCEPTED_REPORT_ONLY_GUARDED_PATCH_PLAN",
         args.accept_report_only_guarded_patch_plan,
         "requires --accept-report-only-guarded-patch-plan")
    gate("PHASE23I_SOURCE_PROBE_GREEN",
         phase23i.get("STATUS") == "LOCALE_PHASE23I_MESSAGING_LOCALE_SPINE_SOURCE_INTEGRATION_PROBE_GREEN_SOURCE_HELD",
         phase23i.get("STATUS", ""))
    gate("PHASE23I_VALIDATION_ZERO",
         phase23i.get("VALIDATION_ISSUES", "") == "0",
         f"validation_issues={phase23i.get('VALIDATION_ISSUES', '')}")
    gate("PHASE23I_SOURCE_MUTATION_HELD",
         phase23i.get("SOURCE_MUTATION_AUTHORIZED", "") == "0",
         f"source_mutation_authorized={phase23i.get('SOURCE_MUTATION_AUTHORIZED', '')}")
    gate("PHASE23I_RUNTIME_CHANGE_HELD",
         phase23i.get("RUNTIME_BEHAVIOR_CHANGE_AUTHORIZED", "") == "0",
         f"runtime_behavior_change_authorized={phase23i.get('RUNTIME_BEHAVIOR_CHANGE_AUTHORIZED', '')}")
    gate("SOURCE_EVIDENCE_AVAILABLE",
         len(source_evidence) > 0,
         f"source_evidence_rows={len(source_evidence)}")
    review("LOC_023I_SAVEPOINT_LATEST",
           latest.get("savepoint_id") == "LOC-023I",
           f"latest_savepoint={latest.get('savepoint_id', '')}; recommended before 23J")

    target_rows = []
    for target in PATCH_TARGETS:
        target_path = repo / target["TARGET_PATH"]
        target_rows.append({
            **target,
            "EXISTS": 1 if target_path.exists() else 0,
            "BYTES": target_path.stat().st_size if target_path.exists() else 0,
            "SHA256": sha256_file(target_path) if target_path.exists() else "",
        })

    required_source_missing = [r for r in target_rows if r["TARGET_PATH"].startswith("src/") and not r["EXISTS"]]
    gate("REQUIRED_SOURCE_TARGETS_PRESENT",
         len(required_source_missing) == 0,
         f"missing_source_targets={len(required_source_missing)}")

    status = STATUS_GREEN if failures == 0 else STATUS_BLOCKED
    validation_issues = str(failures)

    evidence_summary = summarize_evidence(source_evidence)

    patch_sequence = [
        {"STEP": 1, "ACTION": "CREATE_SOURCE_BACKUPS", "DETAIL": "Backup only explicitly targeted source files before any mutation in 23K."},
        {"STEP": 2, "ACTION": "ADD_LOCALE_SPINE_TYPES_API", "DETAIL": "Declare small read-only locale spine status/support/fallback API in message_catalog header."},
        {"STEP": 3, "ACTION": "IMPLEMENT_READ_ONLY_LOCALE_SPINE_READER", "DETAIL": "Implement active SYSTEM_LOCALES/SYSTEM_LOCALE_FALLBACK reader with missing-spine graceful fallback."},
        {"STEP": 4, "ACTION": "WIRE_STATUS_SURFACE_ONLY", "DETAIL": "Expose locale spine status/check path without changing SET LANGUAGE semantics yet."},
        {"STEP": 5, "ACTION": "BUILD_AND_SMOKE", "DETAIL": "Build, then run current Messaging smoke plus new locale spine status smoke."},
        {"STEP": 6, "ACTION": "VALIDATE_AND_SAVEPOINT", "DETAIL": "Only savepoint if source hashes, build, and runtime smokes pass."},
    ]

    no_go = [
        {"NO_GO_ID": "NG-001", "CONDITION": "Any source target missing or hash unexpectedly changed before patch.", "ACTION": "Do not apply 23K."},
        {"NO_GO_ID": "NG-002", "CONDITION": "Cannot find safe insertion anchors in message_catalog/cmd_set.", "ACTION": "Return to source probe; no broad rewrite."},
        {"NO_GO_ID": "NG-003", "CONDITION": "Patch would alter active Messaging DBF schema or SYSTEM_MESSAGE_TEXT rows.", "ACTION": "Reject; locale spine is separate infrastructure."},
        {"NO_GO_ID": "NG-004", "CONDITION": "Patch requires HELP/CMDHELPCHK/manualgen/Data Dictionary mutation.", "ACTION": "Split into later consumer-specific lane."},
        {"NO_GO_ID": "NG-005", "CONDITION": "Current SET LANGUAGE / SET MESSAGE CATALOG GET smoke fails.", "ACTION": "Rollback source patch."},
    ]

    boundary = [
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "23J is report-only source patch plan."},
        {"PROTECTED_SYSTEM": "BUILD", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No build execution."},
        {"PROTECTED_SYSTEM": "RUNTIME_BEHAVIOR", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No runtime behavior change."},
        {"PROTECTED_SYSTEM": "ACTIVE_LOCALE_SPINE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No DBF/CDX/LMDB mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_DBF_CATALOG", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active Messaging catalog mutation."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No HELP DATA mutation."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CMDHELPCHK mutation."},
        {"PROTECTED_SYSTEM": "MANUALGEN", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No manualgen mutation."},
        {"PROTECTED_SYSTEM": "DATADICT_SELF_DOC", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No Data Dictionary/SelfDoc mutation."},
    ]

    write_csv(reports / "locale_phase23j_status_summary_v1.csv", [{
        "STATUS": status,
        "VALIDATION_ISSUES": validation_issues,
        "SOURCE_MUTATION_AUTHORIZED": 0,
        "SOURCE_PATCH_APPLICATION_AUTHORIZED": 0,
        "BUILD_EXECUTION_AUTHORIZED": 0,
        "RUNTIME_BEHAVIOR_CHANGE_AUTHORIZED": 0,
        "SOURCE_SCAN_ROWS_FROM_23I": len(source_scan),
        "SOURCE_EVIDENCE_ROWS_FROM_23I": len(source_evidence),
        "PATCH_TARGET_ROWS": len(target_rows),
        "API_PLAN_ROWS": len(API_ROWS),
        "RUNTIME_SMOKE_ROWS": len(SMOKE_ROWS),
        "NEXT_GATE": NEXT_GATE,
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }], ["STATUS", "VALIDATION_ISSUES", "SOURCE_MUTATION_AUTHORIZED",
         "SOURCE_PATCH_APPLICATION_AUTHORIZED", "BUILD_EXECUTION_AUTHORIZED",
         "RUNTIME_BEHAVIOR_CHANGE_AUTHORIZED", "SOURCE_SCAN_ROWS_FROM_23I",
         "SOURCE_EVIDENCE_ROWS_FROM_23I", "PATCH_TARGET_ROWS", "API_PLAN_ROWS",
         "RUNTIME_SMOKE_ROWS", "NEXT_GATE", "REPORT_TIMESTAMP_UTC"])

    write_csv(reports / "locale_phase23j_gate_check_v1.csv", gates, ["GATE", "STATUS", "DETAIL"])
    write_csv(reports / "locale_phase23j_source_patch_targets_v1.csv", target_rows,
              ["PATCH_ID", "TARGET_PATH", "ACTION", "INTENT", "MUTATION_PHASE", "SAFETY", "EXISTS", "BYTES", "SHA256"])
    write_csv(reports / "locale_phase23j_source_evidence_summary_v1.csv", evidence_summary,
              ["SOURCE_PATH", "MATCH_KIND", "EVIDENCE_ROWS", "EXAMPLE"])
    write_csv(reports / "locale_phase23j_runtime_api_plan_v1.csv", API_ROWS,
              ["API_ID", "API_NAME", "CALL_SITE", "INPUT", "OUTPUT", "FALLBACK"])
    write_csv(reports / "locale_phase23j_patch_sequence_v1.csv", patch_sequence,
              ["STEP", "ACTION", "DETAIL"])
    write_csv(reports / "locale_phase23j_runtime_smoke_plan_v1.csv", SMOKE_ROWS,
              ["SMOKE_ID", "COMMAND_OR_SCRIPT", "EXPECTED", "BOUNDARY"])
    write_csv(reports / "locale_phase23j_rollback_plan_v1.csv", ROLLBACK_ROWS,
              ["ROLLBACK_ID", "TRIGGER", "ACTION", "EXPECTED_SAFE_STATE"])
    write_csv(reports / "locale_phase23j_no_go_criteria_v1.csv", no_go,
              ["NO_GO_ID", "CONDITION", "ACTION"])
    write_csv(reports / "locale_phase23j_boundary_ledger_v1.csv", boundary,
              ["PROTECTED_SYSTEM", "MUTATION_ALLOWED", "OBSERVED_MUTATION", "DETAIL"])

    plan_md = f"""# Locale Phase 23J — Guarded Messaging Locale Spine Source Patch Plan

Status: `{status}`

Phase 23J is report-only. It converts the Phase 23I source evidence into an
exact guarded source patch plan for a later phase. It does not patch source,
does not run a build, and does not change runtime behavior.

## Design target

Messaging should become the first runtime consumer of the active shared locale
spine, while keeping domain ownership separate:

```text
SYSTEM_LOCALES / SYSTEM_LOCALE_FALLBACK  -> shared locale infrastructure
SYSTEM_MESSAGES / SYSTEM_MESSAGE_TEXT    -> Messaging-owned runtime text
```

## Guarded patch direction

The later source patch should add read-only locale-spine support around the
Messaging provider/status path. It must preserve:

```text
current active_dbf message lookup
compiled fallback
SET LANGUAGE behavior
SET MESSAGE CATALOG GET behavior
```

## Next gate

```text
{NEXT_GATE}
```

23K must be separately authorized because it would be a source mutation phase.
"""
    plan_path = repo / "docs/locale/LOCALE_PHASE23J_GUARDED_MESSAGING_LOCALE_SPINE_SOURCE_PATCH_PLAN.md"
    plan_path.parent.mkdir(parents=True, exist_ok=True)
    plan_path.write_text(plan_md, encoding="utf-8")

    manifest = []
    for p, role in [
        (reports / "locale_phase23j_status_summary_v1.csv", "phase23j status summary"),
        (reports / "locale_phase23j_source_patch_targets_v1.csv", "source patch targets"),
        (reports / "locale_phase23j_source_evidence_summary_v1.csv", "source evidence summary"),
        (reports / "locale_phase23j_runtime_api_plan_v1.csv", "runtime API plan"),
        (reports / "locale_phase23j_patch_sequence_v1.csv", "patch sequence"),
        (reports / "locale_phase23j_runtime_smoke_plan_v1.csv", "runtime smoke plan"),
        (reports / "locale_phase23j_rollback_plan_v1.csv", "rollback plan"),
        (reports / "locale_phase23j_no_go_criteria_v1.csv", "no-go criteria"),
        (reports / "locale_phase23j_boundary_ledger_v1.csv", "boundary ledger"),
        (plan_path, "phase23j narrative plan"),
    ]:
        if p.exists():
            manifest.append({"ARTIFACT": rel(p, repo), "ROLE": role, "BYTES": p.stat().st_size, "SHA256": sha256_file(p)})
    write_csv(reports / "locale_phase23j_artifact_manifest_v1.csv", manifest,
              ["ARTIFACT", "ROLE", "BYTES", "SHA256"])

    print(status)
    print(f"  validation issues: {validation_issues}")
    print("  source mutation authorized: 0")
    print("  source patch application authorized: 0")
    print("  build execution authorized: 0")
    print("  runtime behavior change authorized: 0")
    print(f"  source scan rows from 23I: {len(source_scan)}")
    print(f"  source evidence rows from 23I: {len(source_evidence)}")
    print(f"  patch target rows: {len(target_rows)}")
    print(f"  API plan rows: {len(API_ROWS)}")
    print(f"  runtime smoke rows: {len(SMOKE_ROWS)}")
    print(f"  next gate: {NEXT_GATE}")
    print(f"  reports: {reports}")
    return 0 if status == STATUS_GREEN else 2

if __name__ == "__main__":
    raise SystemExit(main())
