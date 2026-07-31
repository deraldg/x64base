#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

STATUS_GREEN = "LOCALE_PHASE23N_SCHEMA_LOCATION_CONTRACT_GREEN_REPORT_ONLY"
STATUS_BLOCKED = "LOCALE_PHASE23N_SCHEMA_LOCATION_CONTRACT_BLOCKED"
NEXT_GATE = "HOLD_OR_AUTHORIZE_PHASE23O_ACTIVE_SCHEMA_CONTRACT_PROMOTION"
REPORT_DIR = Path("docs/locale/reports")

ACTIVE_SCHEMA_TARGETS = [
    {
        "DOMAIN": "locale",
        "SCHEMA_ID": "LOCALE_SPINE",
        "TARGET_PATH": "dottalkpp/data/schemas/locale/locale_spine.dtschema",
        "TABLES": "SYSTEM_LOCALES;SYSTEM_LOCALE_FALLBACK",
        "SOURCE_OF_TRUTH": "active shared locale spine artifacts and Phase 23B-23G locale reports",
        "PROMOTION_STATUS": "PLANNED_NOT_PROMOTED",
    },
    {
        "DOMAIN": "messaging",
        "SCHEMA_ID": "MESSAGE_CATALOG",
        "TARGET_PATH": "dottalkpp/data/schemas/messaging/message_catalog.dtschema",
        "TABLES": "SYSTEM_MESSAGES;SYSTEM_MESSAGE_TEXT",
        "SOURCE_OF_TRUTH": "active Messaging DBF catalog artifacts and Phase 22 reports",
        "PROMOTION_STATUS": "PLANNED_NOT_PROMOTED",
    },
]

ROOT_POLICY = [
    {
        "ROOT_KIND": "ACTIVE_RUNTIME_DATA",
        "PATH_PATTERN": "dottalkpp/data/<domain>/",
        "POLICY": "Active DBF data files live here. Do not move candidate/proof DBFs into active roots by hand.",
    },
    {
        "ROOT_KIND": "ACTIVE_RUNTIME_INDEXES",
        "PATH_PATTERN": "dottalkpp/data/indexes/<domain>/",
        "POLICY": "Active CDX files live here. Promotion is guarded and hash/proof backed.",
    },
    {
        "ROOT_KIND": "ACTIVE_RUNTIME_LMDB",
        "PATH_PATTERN": "dottalkpp/data/lmdb/<domain>/",
        "POLICY": "Active LMDB env dirs live here. Promotion/rebuild is guarded.",
    },
    {
        "ROOT_KIND": "ACTIVE_RUNTIME_SCHEMA_CONTRACTS",
        "PATH_PATTERN": "dottalkpp/data/schemas/<domain>/",
        "POLICY": "Active schema contracts live here and describe active runtime DBF/CDX/LMDB contracts.",
    },
    {
        "ROOT_KIND": "CANDIDATE_PROOF_ARTIFACTS",
        "PATH_PATTERN": "docs/<lane>/candidates/...",
        "POLICY": "Candidate/proof artifacts remain as provenance. Do not move them by hand.",
    },
    {
        "ROOT_KIND": "REPORTS_AUDITS_SAVEPOINTS",
        "PATH_PATTERN": "docs/<lane>/reports/... and docs/<lane>/runlog/...",
        "POLICY": "Reports, audits, runlogs, savepoints, and proof text live here.",
    },
]

LOCALE_SCHEMA_DRAFT = """# locale_spine.dtschema
# Phase 23N candidate active schema contract draft.
# Target active path:
#   dottalkpp/data/schemas/locale/locale_spine.dtschema
#
# Active artifacts described:
#   dottalkpp/data/locale/SYSTEM_LOCALES.dbf
#   dottalkpp/data/locale/SYSTEM_LOCALE_FALLBACK.dbf
#   dottalkpp/data/indexes/locale/*.cdx
#   dottalkpp/data/lmdb/locale/*.cdx.d
#
# Boundary:
#   Draft only in Phase 23N. Do not treat as promoted until Phase 23O.

SCHEMA_ID: LOCALE_SPINE
SCHEMA_STATUS: CANDIDATE_DRAFT
ACTIVE_SCHEMA_TARGET: dottalkpp/data/schemas/locale/locale_spine.dtschema

TABLE: SYSTEM_LOCALES
PRIMARY_KEY: LOCALE_ID
FIELDS:
  LOCALE_ID
  BASE_LOCALE
  DISPLAY_NAME
  TEXT_DIR
  SOURCE_LOCALE
  LOCALE_STATUS
  DEFAULT_LOCALE
  FALLBACK_ALLOWED
TAGS:
  LOCALE_ID
  BASE_LOCALE
  LOCALE_STATUS
  SRC

TABLE: SYSTEM_LOCALE_FALLBACK
PRIMARY_KEY: FBID
FIELDS:
  FBID
  LOCALE_ID
  FALLBACK_TO
  FALLBACK_ORDER
  FALLBACK_TYPE
  RULE_STATUS
TAGS:
  FBID
  LOCALE_ID
  FALLBACK_TO
  FALLBACK_ORDER
  FALLBACK_TYPE
"""

MESSAGING_SCHEMA_DRAFT = """# message_catalog.dtschema
# Phase 23N candidate active schema contract draft.
# Target active path:
#   dottalkpp/data/schemas/messaging/message_catalog.dtschema
#
# Active artifacts described:
#   dottalkpp/data/messaging/SYSTEM_MESSAGES.dbf
#   dottalkpp/data/messaging/SYSTEM_MESSAGE_TEXT.dbf
#   dottalkpp/data/indexes/messaging/*.cdx
#   dottalkpp/data/lmdb/messaging/*.cdx.d
#
# Boundary:
#   Draft only in Phase 23N. Do not treat as promoted until Phase 23O.
#   Field/tag details should be reconciled against the active Messaging catalog
#   before active promotion.

SCHEMA_ID: MESSAGE_CATALOG
SCHEMA_STATUS: CANDIDATE_DRAFT_NEEDS_FIELD_RECONCILIATION
ACTIVE_SCHEMA_TARGET: dottalkpp/data/schemas/messaging/message_catalog.dtschema

TABLE: SYSTEM_MESSAGES
ROLE: stable message identity
FIELD_RECONCILIATION: REQUIRED_BEFORE_ACTIVE_PROMOTION

TABLE: SYSTEM_MESSAGE_TEXT
ROLE: localized message text by LOCALE_ID-compatible key
FIELD_RECONCILIATION: REQUIRED_BEFORE_ACTIVE_PROMOTION
"""

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

def inv_path(repo: Path, relp: str, role: str) -> dict[str, Any]:
    p = repo / relp
    return {
        "PATH": relp,
        "ROLE": role,
        "EXISTS": 1 if p.exists() else 0,
        "IS_DIR": 1 if p.is_dir() else 0,
        "IS_FILE": 1 if p.is_file() else 0,
        "BYTES": p.stat().st_size if p.exists() and p.is_file() else "",
        "SHA256": sha256_file(p) if p.exists() and p.is_file() else "",
    }

def list_some_files(root: Path, repo: Path, role: str, max_rows: int = 50) -> list[dict[str, Any]]:
    if not root.exists():
        return []
    rows = []
    for p in sorted(root.rglob("*")):
        if not p.is_file():
            continue
        rows.append({
            "PATH": rel(p, repo),
            "ROLE": role,
            "BYTES": p.stat().st_size,
            "SHA256": sha256_file(p),
        })
        if len(rows) >= max_rows:
            break
    return rows

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--accept-report-only-schema-location-plan", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    reports = repo / REPORT_DIR
    reports.mkdir(parents=True, exist_ok=True)

    phase23m = first_row(reports / "locale_phase23m_msgmgr_audit_status_summary_v1.csv")
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

    gate("OPERATOR_ACCEPTED_REPORT_ONLY_SCHEMA_LOCATION_PLAN",
         args.accept_report_only_schema_location_plan,
         "requires --accept-report-only-schema-location-plan")
    gate("PHASE23M_MSGMGR_AUDIT_GREEN",
         phase23m.get("STATUS") == "LOCALE_PHASE23M_MSGMGR_HAND_EDIT_AND_SAVEPOINT_AUDIT_GREEN_REPORT_ONLY",
         phase23m.get("STATUS", ""))
    gate("PHASE23M_VALIDATION_ZERO",
         phase23m.get("VALIDATION_ISSUES", "") == "0",
         f"validation_issues={phase23m.get('VALIDATION_ISSUES', '')}")
    review("LATEST_SAVEPOINT_IS_23M_OR_LATER",
           latest.get("savepoint_id") == "LOC-023M-MSGMGR-AUDIT",
           f"latest_savepoint={latest.get('savepoint_id', '')}")

    root_inventory = []
    for item in ROOT_POLICY:
        root_inventory.append({
            "ROOT_KIND": item["ROOT_KIND"],
            "PATH_PATTERN": item["PATH_PATTERN"],
            "POLICY": item["POLICY"],
        })

    artifact_inventory = []
    for relp, role in [
        ("dottalkpp/data/locale", "active locale DBF root"),
        ("dottalkpp/data/indexes/locale", "active locale CDX root"),
        ("dottalkpp/data/lmdb/locale", "active locale LMDB root"),
        ("dottalkpp/data/messaging", "active Messaging DBF root"),
        ("dottalkpp/data/indexes/messaging", "active Messaging CDX root"),
        ("dottalkpp/data/lmdb/messaging", "active Messaging LMDB root"),
        ("dottalkpp/data/schemas", "active schema root"),
        ("dottalkpp/data/schemas/locale", "target active locale schema root"),
        ("dottalkpp/data/schemas/messaging", "target active Messaging schema root"),
        ("docs/locale/candidates", "locale candidate/proof root"),
        ("docs/locale/reports", "locale reports root"),
        ("docs/locale/runlog", "locale runlog root"),
    ]:
        artifact_inventory.append(inv_path(repo, relp, role))

    # Important active files.
    for relp, role in [
        ("dottalkpp/data/locale/SYSTEM_LOCALES.dbf", "active locale table"),
        ("dottalkpp/data/locale/SYSTEM_LOCALE_FALLBACK.dbf", "active locale table"),
        ("dottalkpp/data/indexes/locale/SYSTEM_LOCALES.cdx", "active locale cdx"),
        ("dottalkpp/data/indexes/locale/SYSTEM_LOCALE_FALLBACK.cdx", "active locale cdx"),
        ("dottalkpp/data/lmdb/locale/SYSTEM_LOCALES.cdx.d/data.mdb", "active locale lmdb data"),
        ("dottalkpp/data/lmdb/locale/SYSTEM_LOCALE_FALLBACK.cdx.d/data.mdb", "active locale lmdb data"),
        ("dottalkpp/data/messaging/SYSTEM_MESSAGES.dbf", "active messaging table"),
        ("dottalkpp/data/messaging/SYSTEM_MESSAGE_TEXT.dbf", "active messaging table"),
    ]:
        artifact_inventory.append(inv_path(repo, relp, role))

    schema_root_files = list_some_files(repo / "dottalkpp/data/schemas", repo, "existing active schema-root file", 100)
    candidate_files = list_some_files(repo / "docs/locale/candidates", repo, "locale candidate/proof file", 100)

    # Write candidate drafts under docs only.
    draft_dir = repo / "docs/locale/schemas/candidates/phase23n_schema_location_contract"
    draft_dir.mkdir(parents=True, exist_ok=True)
    locale_draft = draft_dir / "locale_spine.dtschema"
    messaging_draft = draft_dir / "message_catalog.dtschema"
    locale_draft.write_text(LOCALE_SCHEMA_DRAFT, encoding="utf-8")
    messaging_draft.write_text(MESSAGING_SCHEMA_DRAFT, encoding="utf-8")

    draft_rows = [
        {
            "DRAFT_PATH": rel(locale_draft, repo),
            "TARGET_PATH": "dottalkpp/data/schemas/locale/locale_spine.dtschema",
            "SCHEMA_ID": "LOCALE_SPINE",
            "STATUS": "CANDIDATE_DRAFT_READY_FOR_PHASE23O_REVIEW",
            "BYTES": locale_draft.stat().st_size,
            "SHA256": sha256_file(locale_draft),
        },
        {
            "DRAFT_PATH": rel(messaging_draft, repo),
            "TARGET_PATH": "dottalkpp/data/schemas/messaging/message_catalog.dtschema",
            "SCHEMA_ID": "MESSAGE_CATALOG",
            "STATUS": "CANDIDATE_DRAFT_FIELD_RECONCILIATION_REQUIRED",
            "BYTES": messaging_draft.stat().st_size,
            "SHA256": sha256_file(messaging_draft),
        },
    ]

    promotion_plan = [
        {
            "STEP": 1,
            "ACTION": "KEEP_EXISTING_CANDIDATES_IN_PLACE",
            "DETAIL": "Do not move docs/.../candidates artifacts by hand; they remain provenance.",
        },
        {
            "STEP": 2,
            "ACTION": "PROMOTE_LOCALE_SCHEMA_CONTRACT_FIRST",
            "DETAIL": "Phase 23O may create dottalkpp/data/schemas/locale/locale_spine.dtschema from the Phase 23N draft after review.",
        },
        {
            "STEP": 3,
            "ACTION": "RECONCILE_MESSAGING_SCHEMA_FIELDS",
            "DETAIL": "Before active Messaging schema promotion, reconcile active SYSTEM_MESSAGES/SYSTEM_MESSAGE_TEXT fields/tags from runtime/catalog evidence.",
        },
        {
            "STEP": 4,
            "ACTION": "UPDATE_MSGMGR_STATUS_AFTER_SCHEMA_PROMOTION",
            "DETAIL": "Only after active schema contracts exist should MSGMGR STATUS report schema contract paths.",
        },
    ]

    boundary = [
        {"PROTECTED_SYSTEM": "ACTIVE_DBF_CDX_LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active DBF/CDX/LMDB mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_SCHEMA_CONTRACTS", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No dottalkpp/data/schemas active schema files created in 23N."},
        {"PROTECTED_SYSTEM": "DOCS_CANDIDATE_SCHEMA_DRAFTS", "MUTATION_ALLOWED": 1, "OBSERVED_MUTATION": len(draft_rows), "DETAIL": "Candidate schema drafts created under docs/locale/schemas/candidates."},
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No source mutation."},
        {"PROTECTED_SYSTEM": "BUILD_RUNTIME", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No build or runtime execution."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No HELP DATA mutation."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CMDHELPCHK mutation."},
        {"PROTECTED_SYSTEM": "MANUALGEN", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No manualgen mutation."},
        {"PROTECTED_SYSTEM": "DATADICT_SELF_DOC", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No Data Dictionary/SelfDoc mutation."},
    ]

    status = STATUS_GREEN if failures == 0 else STATUS_BLOCKED
    validation_issues = str(failures)

    write_csv(reports / "locale_phase23n_schema_location_status_summary_v1.csv", [{
        "STATUS": status,
        "VALIDATION_ISSUES": validation_issues,
        "REPORT_ONLY_PLAN": 1,
        "ACTIVE_SCHEMA_MUTATION_AUTHORIZED": 0,
        "ACTIVE_SCHEMA_FILES_CREATED": 0,
        "CANDIDATE_SCHEMA_DRAFTS_CREATED": len(draft_rows),
        "ACTIVE_SCHEMA_TARGETS": len(ACTIVE_SCHEMA_TARGETS),
        "NEXT_GATE": NEXT_GATE,
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }], ["STATUS", "VALIDATION_ISSUES", "REPORT_ONLY_PLAN", "ACTIVE_SCHEMA_MUTATION_AUTHORIZED",
         "ACTIVE_SCHEMA_FILES_CREATED", "CANDIDATE_SCHEMA_DRAFTS_CREATED",
         "ACTIVE_SCHEMA_TARGETS", "NEXT_GATE", "REPORT_TIMESTAMP_UTC"])

    write_csv(reports / "locale_phase23n_schema_location_gate_check_v1.csv", gates, ["GATE", "STATUS", "DETAIL"])
    write_csv(reports / "locale_phase23n_root_policy_v1.csv", root_inventory, ["ROOT_KIND", "PATH_PATTERN", "POLICY"])
    write_csv(reports / "locale_phase23n_active_artifact_inventory_v1.csv", artifact_inventory, ["PATH", "ROLE", "EXISTS", "IS_DIR", "IS_FILE", "BYTES", "SHA256"])
    write_csv(reports / "locale_phase23n_existing_schema_files_v1.csv", schema_root_files, ["PATH", "ROLE", "BYTES", "SHA256"])
    write_csv(reports / "locale_phase23n_candidate_artifact_sample_v1.csv", candidate_files, ["PATH", "ROLE", "BYTES", "SHA256"])
    write_csv(reports / "locale_phase23n_active_schema_targets_v1.csv", ACTIVE_SCHEMA_TARGETS, ["DOMAIN", "SCHEMA_ID", "TARGET_PATH", "TABLES", "SOURCE_OF_TRUTH", "PROMOTION_STATUS"])
    write_csv(reports / "locale_phase23n_schema_candidate_drafts_v1.csv", draft_rows, ["DRAFT_PATH", "TARGET_PATH", "SCHEMA_ID", "STATUS", "BYTES", "SHA256"])
    write_csv(reports / "locale_phase23n_schema_promotion_plan_v1.csv", promotion_plan, ["STEP", "ACTION", "DETAIL"])
    write_csv(reports / "locale_phase23n_boundary_ledger_v1.csv", boundary, ["PROTECTED_SYSTEM", "MUTATION_ALLOWED", "OBSERVED_MUTATION", "DETAIL"])

    plan_doc = repo / "docs/locale/LOCALE_PHASE23N_SCHEMA_LOCATION_CONTRACT.md"
    plan_doc.parent.mkdir(parents=True, exist_ok=True)
    plan_doc.write_text(f"""# Locale Phase 23N — Schema Location Contract

Status: `{status}`

Accepted layout doctrine:

```text
Active runtime data:
  dottalkpp/data/<domain>/
  dottalkpp/data/indexes/<domain>/
  dottalkpp/data/lmdb/<domain>/

Active runtime schema contracts:
  dottalkpp/data/schemas/<domain>/

Candidate/proof artifacts:
  docs/<lane>/candidates/...

Reports/audits/savepoints:
  docs/<lane>/reports/...
  docs/<lane>/runlog/...
```

Phase 23N is report-only for active schemas. It creates candidate schema drafts
under `docs/locale/schemas/candidates/...` but does not create active schema
files under `dottalkpp/data/schemas/...`.

## Next gate

```text
{NEXT_GATE}
```
""", encoding="utf-8")

    print(status)
    print(f"  validation issues: {validation_issues}")
    print("  report-only plan: 1")
    print("  active schema mutation authorized: 0")
    print("  active schema files created: 0")
    print(f"  candidate schema drafts created: {len(draft_rows)}")
    print(f"  active schema targets: {len(ACTIVE_SCHEMA_TARGETS)}")
    print(f"  next gate: {NEXT_GATE}")
    print(f"  reports: {reports}")
    return 0 if status == STATUS_GREEN else 2

if __name__ == "__main__":
    raise SystemExit(main())
