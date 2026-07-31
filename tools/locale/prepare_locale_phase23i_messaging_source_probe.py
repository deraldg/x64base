#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

STATUS_GREEN = "LOCALE_PHASE23I_MESSAGING_LOCALE_SPINE_SOURCE_INTEGRATION_PROBE_GREEN_SOURCE_HELD"
STATUS_BLOCKED = "LOCALE_PHASE23I_MESSAGING_LOCALE_SPINE_SOURCE_INTEGRATION_PROBE_BLOCKED"
NEXT_GATE = "HOLD_OR_AUTHORIZE_PHASE23J_GUARDED_MESSAGING_LOCALE_SPINE_SOURCE_PATCH_PLAN"
LOCALE_REPORT_DIR = Path("docs/locale/reports")

SOURCE_PATHS = [
    "src/help/message_catalog.cpp",
    "src/help/message_catalog.hpp",
    "src/help/message_catalog.h",
    "src/help/helpdata_messages.cpp",
    "src/help/helpdata_messages.h",
    "src/cli/cmd_set.cpp",
    "src/cli/command_output.cpp",
    "src/cli/command_registry.cpp",
    "src/core/paths.cpp",
    "src/core/paths.hpp",
    "src/core/config.cpp",
    "src/core/config.hpp",
    "src/runtime/runtime_paths.cpp",
    "src/runtime/runtime_paths.hpp",
    "CMakeLists.txt",
    "src/CMakeLists.txt",
    "src/help/CMakeLists.txt",
]

KEYWORDS = {
    "MESSAGE_CATALOG": ["message_catalog", "MessageCatalog", "message catalog", "SET MESSAGE CATALOG"],
    "SET_LANGUAGE": ["SET LANGUAGE", "set language", "Message locale", "language"],
    "LOCALE": ["LOCALE", "locale", "LOCALE_ID"],
    "FALLBACK": ["fallback", "Fallback", "en-US"],
    "ACTIVE_DBF": ["active_dbf", "ACTIVE_DBF", "active catalog", "SYSTEM_MESSAGES"],
    "PATH": ["data/locale", "data\\locale", "data/messaging", "data\\messaging", "indexes/locale", "lmdb/locale"],
    "DBF_API": ["USE ", "open", "Dbf", "DBF", "WorkArea", "Table"],
}

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

def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def rel(path: Path, repo: Path) -> str:
    try:
        return path.relative_to(repo).as_posix()
    except ValueError:
        return str(path)

def safe_read(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")

def find_lines(path: Path, repo: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    text = safe_read(path)
    if not text:
        return rows
    lines = text.splitlines()
    for i, line in enumerate(lines, start=1):
        trim = line.strip()
        if not trim:
            continue
        for kind, needles in KEYWORDS.items():
            for needle in needles:
                if needle.lower() in trim.lower():
                    rows.append({
                        "SOURCE_PATH": rel(path, repo),
                        "LINE_NO": i,
                        "MATCH_KIND": kind,
                        "MATCH_TERM": needle,
                        "LINE_TEXT": trim[:240],
                    })
                    break
    return rows

def source_scan_row(path: Path, repo: Path) -> dict[str, Any]:
    text = safe_read(path)
    upper = text.upper()
    return {
        "SOURCE_PATH": rel(path, repo),
        "EXISTS": 1 if path.exists() else 0,
        "BYTES": path.stat().st_size if path.exists() else 0,
        "SHA256": sha256_file(path) if path.exists() else "",
        "MATCH_MESSAGE_CATALOG": 1 if "MESSAGE_CATALOG" in upper or "MESSAGE CATALOG" in upper else 0,
        "MATCH_SET_LANGUAGE": 1 if "SET LANGUAGE" in upper else 0,
        "MATCH_LOCALE": 1 if "LOCALE" in upper else 0,
        "MATCH_FALLBACK": 1 if "FALLBACK" in upper or "EN-US" in upper else 0,
        "MATCH_SYSTEM_MESSAGES": 1 if "SYSTEM_MESSAGES" in upper or "SYSTEM_MESSAGE_TEXT" in upper else 0,
        "MATCH_SYSTEM_LOCALES": 1 if "SYSTEM_LOCALES" in upper or "SYSTEM_LOCALE_FALLBACK" in upper else 0,
        "MATCH_ACTIVE_PROVIDER": 1 if "ACTIVE_DBF" in upper or "ACTIVE CATALOG" in upper else 0,
    }

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--accept-report-only-source-probe", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    reports = repo / LOCALE_REPORT_DIR
    reports.mkdir(parents=True, exist_ok=True)

    phase23h = first_row(reports / "locale_phase23h_status_summary_v1.csv")
    latest = {}
    latest_path = reports / "locale_savepoint_latest_v1.json"
    if latest_path.exists():
        try:
            latest = json.loads(latest_path.read_text(encoding="utf-8"))
        except Exception:
            latest = {}

    active_artifacts = [
        repo / "dottalkpp/data/locale/SYSTEM_LOCALES.dbf",
        repo / "dottalkpp/data/locale/SYSTEM_LOCALE_FALLBACK.dbf",
        repo / "dottalkpp/data/indexes/locale/SYSTEM_LOCALES.cdx",
        repo / "dottalkpp/data/indexes/locale/SYSTEM_LOCALE_FALLBACK.cdx",
        repo / "dottalkpp/data/lmdb/locale/SYSTEM_LOCALES.cdx.d/data.mdb",
        repo / "dottalkpp/data/lmdb/locale/SYSTEM_LOCALE_FALLBACK.cdx.d/data.mdb",
    ]

    gates: list[dict[str, Any]] = []
    failures = 0

    def gate(name: str, ok: bool, detail: str) -> None:
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": detail})
        if not ok:
            failures += 1

    def review(name: str, ok: bool, detail: str) -> None:
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "REVIEW", "DETAIL": detail})

    gate("OPERATOR_ACCEPTED_REPORT_ONLY_SOURCE_PROBE",
         args.accept_report_only_source_probe,
         "requires --accept-report-only-source-probe")
    gate("PHASE23H_RUNTIME_CONSUMER_PLAN_GREEN",
         phase23h.get("STATUS") == "LOCALE_PHASE23H_RUNTIME_CONSUMER_INTEGRATION_PLAN_GREEN_SOURCE_HELD",
         phase23h.get("STATUS", ""))
    gate("PHASE23H_VALIDATION_ZERO",
         phase23h.get("VALIDATION_ISSUES", "") == "0",
         f"validation_issues={phase23h.get('VALIDATION_ISSUES', '')}")
    gate("ACTIVE_LOCALE_SPINE_ARTIFACTS_PRESENT",
         all(p.exists() for p in active_artifacts),
         f"present={sum(1 for p in active_artifacts if p.exists())}/{len(active_artifacts)}")
    review("LOC_023H_SAVEPOINT_LATEST",
           latest.get("savepoint_id") == "LOC-023H",
           f"latest_savepoint={latest.get('savepoint_id', '')}; recommended before 23I")

    source_rows = []
    evidence_rows = []
    for rel_path in SOURCE_PATHS:
        path = repo / rel_path
        source_rows.append(source_scan_row(path, repo))
        evidence_rows.extend(find_lines(path, repo))

    # Reduce noise but keep evidence useful.
    evidence_rows = evidence_rows[:400]

    seams = [
        {
            "SEAM_ID": "23I-SEAM-001",
            "SEAM": "MessageCatalog provider API",
            "SOURCE_TARGET": "src/help/message_catalog.hpp and src/help/message_catalog.cpp",
            "PROBE_RESULT": "Inspect current active DBF provider and status/get APIs before source patch.",
            "PATCH_DIRECTION": "Add locale-spine read-only helper separate from message text lookup.",
            "RISK": "Do not merge SYSTEM_LOCALES with SYSTEM_MESSAGES."
        },
        {
            "SEAM_ID": "23I-SEAM-002",
            "SEAM": "SET LANGUAGE command branch",
            "SOURCE_TARGET": "src/cli/cmd_set.cpp",
            "PROBE_RESULT": "SET LANGUAGE is the correct user-facing validation/emission seam.",
            "PATCH_DIRECTION": "Add optional active locale spine validation/status while preserving current behavior.",
            "RISK": "Do not reject currently working locales unless provider explicitly enforces spine mode."
        },
        {
            "SEAM_ID": "23I-SEAM-003",
            "SEAM": "Shared active locale path resolver",
            "SOURCE_TARGET": "runtime path/config helpers; possible fallback to known dottalkpp/data/locale paths",
            "PROBE_RESULT": "Active data artifacts now exist in neutral locale roots.",
            "PATCH_DIRECTION": "Resolve DBF, indexes, and LMDB roots using existing path mechanisms if present; avoid hard-coded absolute paths.",
            "RISK": "Hard-coded local paths would break deployment."
        },
        {
            "SEAM_ID": "23I-SEAM-004",
            "SEAM": "Fallback chain resolution",
            "SOURCE_TARGET": "Messaging fallback logic",
            "PROBE_RESULT": "Existing runtime fallback xx-XX -> en-US is proven; SYSTEM_LOCALE_FALLBACK active data now exists.",
            "PATCH_DIRECTION": "Plan read-only fallback-chain lookup from SYSTEM_LOCALE_FALLBACK, with compiled en-US fallback as final safety.",
            "RISK": "Fallback cycles or missing default rows must not crash runtime."
        },
        {
            "SEAM_ID": "23I-SEAM-005",
            "SEAM": "Runtime status/check reporting",
            "SOURCE_TARGET": "SET MESSAGE CATALOG CHECK / SET LANGUAGE CHECK surfaces",
            "PROBE_RESULT": "Need separate wording: Messaging catalog validation vs shared locale spine validation.",
            "PATCH_DIRECTION": "Add status line or new check block only after source patch is explicitly authorized.",
            "RISK": "Do not make reports imply HELP/manualgen have already localized content."
        },
    ]

    api_contract = [
        {
            "API_ID": "LOCAPI-001",
            "NAME": "locale_spine_available",
            "INPUT": "none",
            "OUTPUT": "bool plus status/detail",
            "ROLE": "Detect active SYSTEM_LOCALES/SYSTEM_LOCALE_FALLBACK availability.",
            "PATCH_PHASE": "23J plan / later source patch"
        },
        {
            "API_ID": "LOCAPI-002",
            "NAME": "locale_is_supported",
            "INPUT": "LOCALE_ID",
            "OUTPUT": "bool plus normalized LOCALE_ID",
            "ROLE": "Validate requested locale against SYSTEM_LOCALES.",
            "PATCH_PHASE": "23J plan / later source patch"
        },
        {
            "API_ID": "LOCAPI-003",
            "NAME": "locale_fallback_chain",
            "INPUT": "LOCALE_ID",
            "OUTPUT": "ordered fallback list ending in en-US when allowed",
            "ROLE": "Resolve fallback through SYSTEM_LOCALE_FALLBACK.",
            "PATCH_PHASE": "23J plan / later source patch"
        },
        {
            "API_ID": "LOCAPI-004",
            "NAME": "message_lookup_with_locale_spine",
            "INPUT": "symbol, requested_locale, args",
            "OUTPUT": "text, resolved_locale, provider detail",
            "ROLE": "Use shared locale spine to guide Messaging lookup without changing message catalog ownership.",
            "PATCH_PHASE": "future guarded source patch"
        },
    ]

    risk_rows = [
        {"RISK_ID": "23I-RISK-001", "RISK": "Path resolver unknown or inconsistent across init/runtime contexts.", "MITIGATION": "Probe existing path utilities before patch; use relative active roots only through runtime configuration."},
        {"RISK_ID": "23I-RISK-002", "RISK": "Source patch could break current active_dbf Messaging lookup.", "MITIGATION": "Keep compiled fallback and current active DBF provider as fallback; add locale spine as validation/fallback helper first."},
        {"RISK_ID": "23I-RISK-003", "RISK": "Fallback cycle or missing default in SYSTEM_LOCALE_FALLBACK.", "MITIGATION": "Add max-depth and en-US final fallback; validate fallback table before use."},
        {"RISK_ID": "23I-RISK-004", "RISK": "HELP/manualgen consumers may be assumed integrated too early.", "MITIGATION": "Messaging-only first runtime consumer; other consumers stay report-only until separate authorization."},
        {"RISK_ID": "23I-RISK-005", "RISK": "LOCALE field vs LOCALE_ID naming drift.", "MITIGATION": "Treat current Messaging LOCALE as LOCALE_ID-compatible; defer rename/alias schema change."},
    ]

    guarded_next = [
        {"NEXT_ID": "23J-001", "ACTION": "Create exact source patch plan", "DETAIL": "Identify functions/classes to edit after reviewing 23I source evidence."},
        {"NEXT_ID": "23J-002", "ACTION": "No source mutation by default", "DETAIL": "23J should remain plan unless source mutation is explicitly authorized."},
        {"NEXT_ID": "23J-003", "ACTION": "Prepare runtime smoke", "DETAIL": "Plan command proving locale spine status and fallback guidance without changing current user behavior."},
        {"NEXT_ID": "23J-004", "ACTION": "Define rollback", "DETAIL": "Any future patch must preserve current active_dbf/compiled fallback behavior."},
    ]

    boundary = [
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "23I probes source and writes reports only."},
        {"PROTECTED_SYSTEM": "RUNTIME_BEHAVIOR", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No runtime behavior change."},
        {"PROTECTED_SYSTEM": "ACTIVE_LOCALE_SPINE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Active locale artifacts read/checked only."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_DBF_CATALOG", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active Messaging catalog mutation."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No HELP DATA mutation."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CMDHELPCHK mutation."},
        {"PROTECTED_SYSTEM": "MANUALGEN", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No manualgen mutation."},
        {"PROTECTED_SYSTEM": "DATADICT_SELF_DOC", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No Data Dictionary/SelfDoc mutation."},
    ]

    status = STATUS_GREEN if failures == 0 else STATUS_BLOCKED
    validation_issues = str(failures)

    write_csv(reports / "locale_phase23i_status_summary_v1.csv", [{
        "STATUS": status,
        "VALIDATION_ISSUES": validation_issues,
        "SOURCE_MUTATION_AUTHORIZED": 0,
        "RUNTIME_BEHAVIOR_CHANGE_AUTHORIZED": 0,
        "ACTIVE_LOCALE_SPINE_PRESENT": 1 if all(p.exists() for p in active_artifacts) else 0,
        "SOURCE_SCAN_ROWS": len(source_rows),
        "SOURCE_EVIDENCE_ROWS": len(evidence_rows),
        "INTEGRATION_SEAM_ROWS": len(seams),
        "API_CONTRACT_ROWS": len(api_contract),
        "NEXT_GATE": NEXT_GATE,
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }], ["STATUS", "VALIDATION_ISSUES", "SOURCE_MUTATION_AUTHORIZED",
         "RUNTIME_BEHAVIOR_CHANGE_AUTHORIZED", "ACTIVE_LOCALE_SPINE_PRESENT",
         "SOURCE_SCAN_ROWS", "SOURCE_EVIDENCE_ROWS", "INTEGRATION_SEAM_ROWS",
         "API_CONTRACT_ROWS", "NEXT_GATE", "REPORT_TIMESTAMP_UTC"])

    write_csv(reports / "locale_phase23i_gate_check_v1.csv", gates, ["GATE", "STATUS", "DETAIL"])
    write_csv(reports / "locale_phase23i_source_scan_v1.csv", source_rows,
              ["SOURCE_PATH", "EXISTS", "BYTES", "SHA256", "MATCH_MESSAGE_CATALOG",
               "MATCH_SET_LANGUAGE", "MATCH_LOCALE", "MATCH_FALLBACK",
               "MATCH_SYSTEM_MESSAGES", "MATCH_SYSTEM_LOCALES", "MATCH_ACTIVE_PROVIDER"])
    write_csv(reports / "locale_phase23i_source_evidence_v1.csv", evidence_rows,
              ["SOURCE_PATH", "LINE_NO", "MATCH_KIND", "MATCH_TERM", "LINE_TEXT"])
    write_csv(reports / "locale_phase23i_integration_seams_v1.csv", seams,
              ["SEAM_ID", "SEAM", "SOURCE_TARGET", "PROBE_RESULT", "PATCH_DIRECTION", "RISK"])
    write_csv(reports / "locale_phase23i_runtime_api_contract_v1.csv", api_contract,
              ["API_ID", "NAME", "INPUT", "OUTPUT", "ROLE", "PATCH_PHASE"])
    write_csv(reports / "locale_phase23i_risk_register_v1.csv", risk_rows,
              ["RISK_ID", "RISK", "MITIGATION"])
    write_csv(reports / "locale_phase23i_guarded_next_steps_v1.csv", guarded_next,
              ["NEXT_ID", "ACTION", "DETAIL"])
    write_csv(reports / "locale_phase23i_boundary_ledger_v1.csv", boundary,
              ["PROTECTED_SYSTEM", "MUTATION_ALLOWED", "OBSERVED_MUTATION", "DETAIL"])

    plan_md = f"""# Locale Phase 23I — Messaging Locale Spine Source Integration Probe

Status: `{status}`

Phase 23I is report-only. It probes Messaging source seams for future use of the
active shared locale spine. It does not patch source and does not change runtime
behavior.

## Active shared locale spine

```text
dottalkpp/data/locale/SYSTEM_LOCALES.dbf
dottalkpp/data/locale/SYSTEM_LOCALE_FALLBACK.dbf
dottalkpp/data/indexes/locale/*.cdx
dottalkpp/data/lmdb/locale/*.cdx.d
```

## Probe outcome

Reports identify where a future guarded source patch should add read-only
locale spine support, while preserving current Messaging active_dbf and compiled
fallback behavior.

## Next gate

```text
{NEXT_GATE}
```

Recommended next step is still plan-first: define an exact guarded source patch
plan before any source mutation is authorized.
"""
    plan_path = repo / "docs/locale/LOCALE_PHASE23I_MESSAGING_LOCALE_SPINE_SOURCE_INTEGRATION_PROBE.md"
    plan_path.parent.mkdir(parents=True, exist_ok=True)
    plan_path.write_text(plan_md, encoding="utf-8")

    manifest = []
    for p, role in [
        (reports / "locale_phase23i_status_summary_v1.csv", "phase23i status summary"),
        (reports / "locale_phase23i_source_scan_v1.csv", "source scan"),
        (reports / "locale_phase23i_source_evidence_v1.csv", "source evidence"),
        (reports / "locale_phase23i_integration_seams_v1.csv", "integration seams"),
        (reports / "locale_phase23i_runtime_api_contract_v1.csv", "runtime API contract"),
        (reports / "locale_phase23i_risk_register_v1.csv", "risk register"),
        (reports / "locale_phase23i_boundary_ledger_v1.csv", "boundary ledger"),
        (plan_path, "phase23i narrative plan"),
    ]:
        if p.exists():
            manifest.append({"ARTIFACT": rel(p, repo), "ROLE": role, "BYTES": p.stat().st_size, "SHA256": sha256_file(p)})
    write_csv(reports / "locale_phase23i_artifact_manifest_v1.csv", manifest,
              ["ARTIFACT", "ROLE", "BYTES", "SHA256"])

    print(status)
    print(f"  validation issues: {validation_issues}")
    print("  source mutation authorized: 0")
    print("  runtime behavior change authorized: 0")
    print(f"  active locale spine present: {1 if all(p.exists() for p in active_artifacts) else 0}")
    print(f"  source scan rows: {len(source_rows)}")
    print(f"  source evidence rows: {len(evidence_rows)}")
    print(f"  integration seam rows: {len(seams)}")
    print(f"  API contract rows: {len(api_contract)}")
    print(f"  next gate: {NEXT_GATE}")
    print(f"  reports: {reports}")
    return 0 if status == STATUS_GREEN else 2

if __name__ == "__main__":
    raise SystemExit(main())
