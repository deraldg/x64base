#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

STATUS_GREEN = "LOCALE_PHASE23H_RUNTIME_CONSUMER_INTEGRATION_PLAN_GREEN_SOURCE_HELD"
STATUS_BLOCKED = "LOCALE_PHASE23H_RUNTIME_CONSUMER_INTEGRATION_PLAN_BLOCKED"
NEXT_GATE = "HOLD_OR_AUTHORIZE_PHASE23I_MESSAGING_LOCALE_SPINE_SOURCE_INTEGRATION_PROBE"
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

def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def file_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")

def contains_any(text: str, needles: list[str]) -> int:
    upper = text.upper()
    return 1 if any(n.upper() in upper for n in needles) else 0

def rel(path: Path, repo: Path) -> str:
    try:
        return path.relative_to(repo).as_posix()
    except ValueError:
        return str(path)

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--accept-report-only-runtime-consumer-plan", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    reports = repo / LOCALE_REPORT_DIR
    reports.mkdir(parents=True, exist_ok=True)

    phase23g = first_row(reports / "locale_phase23g_status_summary_v1.csv")
    latest = {}
    latest_path = reports / "locale_savepoint_latest_v1.json"
    if latest_path.exists():
        try:
            latest = json.loads(latest_path.read_text(encoding="utf-8"))
        except Exception:
            latest = {}

    active_dbf = repo / "dottalkpp/data/locale"
    active_indexes = repo / "dottalkpp/data/indexes/locale"
    active_lmdb = repo / "dottalkpp/data/lmdb/locale"

    active_artifacts = [
        active_dbf / "SYSTEM_LOCALES.dbf",
        active_dbf / "SYSTEM_LOCALE_FALLBACK.dbf",
        active_indexes / "SYSTEM_LOCALES.cdx",
        active_indexes / "SYSTEM_LOCALE_FALLBACK.cdx",
        active_lmdb / "SYSTEM_LOCALES.cdx.d" / "data.mdb",
        active_lmdb / "SYSTEM_LOCALE_FALLBACK.cdx.d" / "data.mdb",
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

    gate("OPERATOR_ACCEPTED_REPORT_ONLY_RUNTIME_CONSUMER_PLAN",
         args.accept_report_only_runtime_consumer_plan,
         "requires --accept-report-only-runtime-consumer-plan")
    gate("PHASE23G_ACTIVE_LOCALE_SPINE_GREEN",
         phase23g.get("STATUS") == "LOCALE_PHASE23G_ACTIVE_LOCALE_SPINE_PROMOTION_READBACK_GREEN",
         phase23g.get("STATUS", ""))
    gate("PHASE23G_VALIDATION_ZERO",
         phase23g.get("VALIDATION_ISSUES", "") == "0",
         f"validation_issues={phase23g.get('VALIDATION_ISSUES', '')}")
    gate("ACTIVE_LOCALE_SPINE_ARTIFACTS_PRESENT",
         all(p.exists() for p in active_artifacts),
         f"present={sum(1 for p in active_artifacts if p.exists())}/{len(active_artifacts)}")
    review("LOC_023G_SAVEPOINT_LATEST",
           latest.get("savepoint_id") == "LOC-023G",
           f"latest_savepoint={latest.get('savepoint_id', '')}; recommended before source integration planning")

    source_scan = []
    for rel_path in SOURCE_PATHS:
        path = repo / rel_path
        txt = file_text(path)
        source_scan.append({
            "SOURCE_PATH": rel_path,
            "EXISTS": 1 if path.exists() else 0,
            "BYTES": path.stat().st_size if path.exists() else 0,
            "SHA256": sha256_file(path) if path.exists() else "",
            "HAS_MESSAGE_CATALOG": contains_any(txt, ["message_catalog", "MessageCatalog", "message catalog"]),
            "HAS_SET_LANGUAGE": contains_any(txt, ["SET LANGUAGE", "set language"]),
            "HAS_LOCALE": contains_any(txt, ["LOCALE", "locale"]),
            "HAS_ACTIVE_DBF": contains_any(txt, ["active_dbf", "ACTIVE_DBF", "active Messaging DBF"]),
            "HAS_FALLBACK": contains_any(txt, ["fallback", "FALLBACK"]),
        })

    seams = [
        {
            "SEAM_ID": "23H-SEAM-001",
            "SEAM": "active shared locale spine artifact paths",
            "CURRENT_STATUS": "PROVEN_ACTIVE_DATA",
            "SOURCE_OR_ARTIFACT": "dottalkpp/data/locale; dottalkpp/data/indexes/locale; dottalkpp/data/lmdb/locale",
            "RECOMMENDATION": "Expose read-only path resolver for shared locale spine; do not hard-code Messaging-only locale paths.",
        },
        {
            "SEAM_ID": "23H-SEAM-002",
            "SEAM": "Messaging provider current locale/fallback behavior",
            "CURRENT_STATUS": "PROVEN_WITH_INLINE_FALLBACK",
            "SOURCE_OR_ARTIFACT": "src/help/message_catalog.cpp / runtime SET MESSAGE CATALOG GET behavior",
            "RECOMMENDATION": "Map existing fallback behavior to SYSTEM_LOCALE_FALLBACK after source probe; keep compiled fallback available.",
        },
        {
            "SEAM_ID": "23H-SEAM-003",
            "SEAM": "SET LANGUAGE command surface",
            "CURRENT_STATUS": "PROVEN_CONSUMER_SURFACE",
            "SOURCE_OR_ARTIFACT": "src/cli/cmd_set.cpp",
            "RECOMMENDATION": "SET LANGUAGE should eventually validate requested LOCALE_ID against SYSTEM_LOCALES when active spine mode enabled.",
        },
        {
            "SEAM_ID": "23H-SEAM-004",
            "SEAM": "runtime message lookup",
            "CURRENT_STATUS": "PROVEN_ACTIVE_DBF_PROVIDER",
            "SOURCE_OR_ARTIFACT": "SYSTEM_MESSAGES / SYSTEM_MESSAGE_TEXT active Messaging catalog",
            "RECOMMENDATION": "Do not merge locale spine with message text catalog; Messaging stays domain-owned and references LOCALE_ID.",
        },
        {
            "SEAM_ID": "23H-SEAM-005",
            "SEAM": "future shared consumers",
            "CURRENT_STATUS": "DEFERRED",
            "SOURCE_OR_ARTIFACT": "HELP; CMDHELPCHK; MAN*; SelfDoc; Data Dictionary",
            "RECOMMENDATION": "Keep 23I Messaging-only as first consumer integration probe; other consumers remain report-only until separately authorized.",
        },
    ]

    mapping = [
        {"CURRENT_BEHAVIOR": "Supported locales are inferred from SYSTEM_MESSAGE_TEXT LOCALE values", "SPINE_MAPPING": "Validate/list supported locales from SYSTEM_LOCALES", "PHASE": "23I probe then later patch", "RISK": "Do not break current message lookup if locale spine is unavailable."},
        {"CURRENT_BEHAVIOR": "Unsupported locale falls back to en-US", "SPINE_MAPPING": "Resolve fallback chain through SYSTEM_LOCALE_FALLBACK", "PHASE": "23I/23J", "RISK": "Fallback must remain explicit and testable."},
        {"CURRENT_BEHAVIOR": "SET LANGUAGE CHECK reports Messaging catalog rows/locales", "SPINE_MAPPING": "Add optional locale spine status section or separate SET LOCALE SPINE CHECK", "PHASE": "after 23I plan", "RISK": "Avoid confusing Messaging catalog validation with shared locale spine validation."},
        {"CURRENT_BEHAVIOR": "Message text rows use LOCALE field", "SPINE_MAPPING": "Treat LOCALE as LOCALE_ID-compatible for current catalog; future schema may rename/alias", "PHASE": "deferred", "RISK": "Avoid rewriting stable catalog tables during integration."},
        {"CURRENT_BEHAVIOR": "Argument substitution proven in Messaging", "SPINE_MAPPING": "No direct locale spine impact; placeholder schema remains separate future phase", "PHASE": "deferred", "RISK": "Do not combine placeholder schema with locale spine."},
    ]

    patch_plan = [
        {"PATCH_ID": "23I-001", "TARGET": "src/help/message_catalog.hpp/.cpp", "ACTION": "SOURCE_PROBE_OR_PLAN", "DETAIL": "Identify provider object/API and add plan for read-only SYSTEM_LOCALES/SYSTEM_LOCALE_FALLBACK resolver; no source mutation in 23H."},
        {"PATCH_ID": "23I-002", "TARGET": "src/cli/cmd_set.cpp", "ACTION": "SOURCE_PROBE_OR_PLAN", "DETAIL": "Find SET LANGUAGE hooks and decide where locale spine validation/status belongs; no source mutation in 23H."},
        {"PATCH_ID": "23I-003", "TARGET": "runtime path resolver", "ACTION": "SOURCE_PROBE_OR_PLAN", "DETAIL": "Confirm path API for dottalkpp/data/locale, indexes/locale, lmdb/locale."},
        {"PATCH_ID": "23I-004", "TARGET": "DotScript smoke", "ACTION": "RUNTIME_PLAN", "DETAIL": "Plan read-only runtime command/smoke proving active locale spine can be opened and fallback rows read."},
        {"PATCH_ID": "23I-005", "TARGET": "boundary/savepoint", "ACTION": "REPORT", "DETAIL": "Keep HELP/CMDHELPCHK/manualgen/Data Dictionary/SelfDoc/source held unless separately authorized."},
    ]

    decisions = [
        {"DECISION_ID": "23H-DEC-001", "DECISION": "ONE_SHARED_LOCALE_SPINE", "STATUS": "ACCEPTED", "DETAIL": "SYSTEM_LOCALES and SYSTEM_LOCALE_FALLBACK are shared infrastructure, not Messaging-only."},
        {"DECISION_ID": "23H-DEC-002", "DECISION": "MESSAGING_FIRST_RUNTIME_CONSUMER", "STATUS": "ACCEPTED", "DETAIL": "Messaging is first integration target because runtime message localization is already proven."},
        {"DECISION_ID": "23H-DEC-003", "DECISION": "NO_SOURCE_MUTATION_IN_23H", "STATUS": "ACCEPTED", "DETAIL": "23H is plan/probe only."},
        {"DECISION_ID": "23H-DEC-004", "DECISION": "COMPILED_AND_CURRENT_ACTIVE_MESSAGE_FALLBACK_REMAIN", "STATUS": "ACCEPTED", "DETAIL": "Locale spine integration must not remove existing compiled/message fallback."},
        {"DECISION_ID": "23H-DEC-005", "DECISION": "OTHER_CONSUMERS_DEFERRED", "STATUS": "ACCEPTED", "DETAIL": "HELP/CMDHELPCHK/manualgen/Data Dictionary/SelfDoc consume later through separate guarded lanes."},
    ]

    boundary = [
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "23H creates reports only; no source mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_LOCALE_SPINE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "23H reads/reports active locale spine; no DBF/CDX/LMDB mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_DBF_CATALOG", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active Messaging catalog mutation."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No HELP DATA mutation."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CMDHELPCHK mutation."},
        {"PROTECTED_SYSTEM": "MANUALGEN", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No manualgen mutation."},
        {"PROTECTED_SYSTEM": "DATADICT_SELF_DOC", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No Data Dictionary/SelfDoc mutation."},
        {"PROTECTED_SYSTEM": "RUNTIME_BEHAVIOR", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No runtime behavior change in 23H."},
    ]

    status = STATUS_GREEN if failures == 0 else STATUS_BLOCKED
    validation_issues = str(failures)

    write_csv(reports / "locale_phase23h_status_summary_v1.csv", [{
        "STATUS": status,
        "VALIDATION_ISSUES": validation_issues,
        "SOURCE_MUTATION_AUTHORIZED": 0,
        "RUNTIME_INTEGRATION_AUTHORIZED": 0,
        "ACTIVE_LOCALE_SPINE_PROVEN": 1 if phase23g.get("STATUS") == "LOCALE_PHASE23G_ACTIVE_LOCALE_SPINE_PROMOTION_READBACK_GREEN" else 0,
        "SOURCE_SCAN_ROWS": len(source_scan),
        "INTEGRATION_SEAM_ROWS": len(seams),
        "PATCH_PLAN_ROWS": len(patch_plan),
        "NEXT_GATE": NEXT_GATE,
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }], ["STATUS", "VALIDATION_ISSUES", "SOURCE_MUTATION_AUTHORIZED",
         "RUNTIME_INTEGRATION_AUTHORIZED", "ACTIVE_LOCALE_SPINE_PROVEN",
         "SOURCE_SCAN_ROWS", "INTEGRATION_SEAM_ROWS", "PATCH_PLAN_ROWS",
         "NEXT_GATE", "REPORT_TIMESTAMP_UTC"])

    write_csv(reports / "locale_phase23h_gate_check_v1.csv", gates, ["GATE", "STATUS", "DETAIL"])
    write_csv(reports / "locale_phase23h_source_scan_v1.csv", source_scan,
              ["SOURCE_PATH", "EXISTS", "BYTES", "SHA256", "HAS_MESSAGE_CATALOG",
               "HAS_SET_LANGUAGE", "HAS_LOCALE", "HAS_ACTIVE_DBF", "HAS_FALLBACK"])
    write_csv(reports / "locale_phase23h_runtime_integration_seams_v1.csv", seams,
              ["SEAM_ID", "SEAM", "CURRENT_STATUS", "SOURCE_OR_ARTIFACT", "RECOMMENDATION"])
    write_csv(reports / "locale_phase23h_messaging_locale_spine_mapping_v1.csv", mapping,
              ["CURRENT_BEHAVIOR", "SPINE_MAPPING", "PHASE", "RISK"])
    write_csv(reports / "locale_phase23h_guarded_patch_plan_v1.csv", patch_plan,
              ["PATCH_ID", "TARGET", "ACTION", "DETAIL"])
    write_csv(reports / "locale_phase23h_decisions_v1.csv", decisions,
              ["DECISION_ID", "DECISION", "STATUS", "DETAIL"])
    write_csv(reports / "locale_phase23h_boundary_ledger_v1.csv", boundary,
              ["PROTECTED_SYSTEM", "MUTATION_ALLOWED", "OBSERVED_MUTATION", "DETAIL"])

    plan_md = f"""# Locale Phase 23H — Runtime Consumer Integration Plan

Status: `{status}`

Phase 23H is report-only. It plans how runtime consumers should use the active
shared locale spine now promoted under neutral active paths.

## Active locale spine

```text
dottalkpp/data/locale
dottalkpp/data/indexes/locale
dottalkpp/data/lmdb/locale
```

## First runtime consumer

Messaging remains the first runtime consumer candidate. This phase does not
change Messaging runtime behavior and does not mutate source.

## Integration rule

The shared locale spine is not a Messaging catalog. Messaging keeps its domain
identity/text tables and references the shared `LOCALE_ID` model.

## Next gate

```text
{NEXT_GATE}
```

That next phase should be a source integration probe/plan. It should not patch
source until the exact seams and path APIs are verified.
"""
    plan_path = repo / "docs/locale/LOCALE_PHASE23H_RUNTIME_CONSUMER_INTEGRATION_PLAN.md"
    plan_path.parent.mkdir(parents=True, exist_ok=True)
    plan_path.write_text(plan_md, encoding="utf-8")

    manifest = []
    for p, role in [
        (reports / "locale_phase23h_status_summary_v1.csv", "phase23h status summary"),
        (reports / "locale_phase23h_source_scan_v1.csv", "source scan"),
        (reports / "locale_phase23h_runtime_integration_seams_v1.csv", "runtime integration seams"),
        (reports / "locale_phase23h_messaging_locale_spine_mapping_v1.csv", "messaging locale spine mapping"),
        (reports / "locale_phase23h_guarded_patch_plan_v1.csv", "guarded patch plan"),
        (reports / "locale_phase23h_decisions_v1.csv", "integration decisions"),
        (reports / "locale_phase23h_boundary_ledger_v1.csv", "boundary ledger"),
        (plan_path, "phase23h narrative plan"),
    ]:
        if p.exists():
            manifest.append({
                "ARTIFACT": rel(p, repo),
                "ROLE": role,
                "BYTES": p.stat().st_size,
                "SHA256": sha256_file(p),
            })
    write_csv(reports / "locale_phase23h_artifact_manifest_v1.csv", manifest,
              ["ARTIFACT", "ROLE", "BYTES", "SHA256"])

    print(status)
    print(f"  validation issues: {validation_issues}")
    print("  source mutation authorized: 0")
    print("  runtime integration authorized: 0")
    print(f"  active locale spine proven: {1 if phase23g.get('STATUS') == 'LOCALE_PHASE23G_ACTIVE_LOCALE_SPINE_PROMOTION_READBACK_GREEN' else 0}")
    print(f"  source scan rows: {len(source_scan)}")
    print(f"  integration seam rows: {len(seams)}")
    print(f"  patch plan rows: {len(patch_plan)}")
    print(f"  next gate: {NEXT_GATE}")
    print(f"  reports: {reports}")
    return 0 if status == STATUS_GREEN else 2

if __name__ == "__main__":
    raise SystemExit(main())
