#!/usr/bin/env python3
"""
DotTalk++ Message Catalog Phase 9
Inactive candidate DBF staging artifacts only.

Reads Phase 6/7/8 report CSVs and stages candidate import inputs,
schema script templates, manifests, and boundary reports for the future
SYSTEM_MESSAGES / SYSTEM_MESSAGE_TEXT DBF catalog. This script does not
create DBF/CDX/LMDB artifacts, does not run DotTalk++, and does not promote
any active catalog.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

STATUS = "MESSAGE_CATALOG_PHASE9_INACTIVE_CANDIDATE_STAGING_GREEN"
CANDIDATE_NAME = "phase9_inactive_candidate_dbf_staging"


def read_csv(path: Path) -> List[Dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: List[Dict[str, object]], fieldnames: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        w.writeheader()
        for row in rows:
            w.writerow({k: row.get(k, "") for k in fieldnames})


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def copy_text(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(src.read_text(encoding="utf-8-sig"), encoding="utf-8")


def require(path: Path, failures: List[Dict[str, str]], label: str) -> None:
    if not path.exists():
        failures.append({"GATE": label, "STATUS": "FAIL", "DETAIL": f"Missing {path}"})
    else:
        failures.append({"GATE": label, "STATUS": "PASS", "DETAIL": "OK"})


def make_dts_script(messages_csv: str, text_csv: str) -> str:
    return f"""* DotTalk++ Message Catalog Phase 9 inactive candidate schema script template
* Purpose: future candidate-only DBF creation/import for SYSTEM_MESSAGES and SYSTEM_MESSAGE_TEXT.
* Generated report-only staging artifact. DO NOT run unless Phase 10 explicitly authorizes candidate DBF execution.
* Source import inputs:
*   {messages_csv}
*   {text_csv}
*
* Boundary:
*   - inactive candidate area only
*   - no active catalog replacement
*   - no HELP DATA rebuild
*   - no CMDHELPCHK mutation
*   - no source-mining mutation
*
* PSEUDOCODE / EXECUTION TEMPLATE ONLY
* Future Phase 10 may replace this with runtime-verified DotTalk++ syntax.
*
* Candidate tables:
*   SYSTEM_MESSAGES
*     MSGID N(10,0)
*     SYMBOL C(64)
*     ENUMNAME C(64)
*     FACILITY C(32)
*     OWNER C(64)
*     CATEGORY C(32)
*     SEVERITY C(16)
*     STATUS C(16)
*     SRC C(32)
*     NOTES M
*
*   SYSTEM_MESSAGE_TEXT
*     MSGID N(10,0)
*     SYMBOL C(64)
*     ENUMNAME C(64)
*     LOCALE C(16)
*     TEXT M
*     TXTHASH C(64)
*     STATUS C(16)
*     SRC C(32)
*
* Candidate index tags:
*   SYSTEM_MESSAGES: MSGID, SYMBOL, ENUMNAME, SEVERITY, FACILITY, OWNER
*   SYSTEM_MESSAGE_TEXT: MSG_LOCALE, SYMBOLLOC, LOCALE, TXTHASH
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--allow-candidate-staging", action="store_true", help="Required explicit gate for candidate staging artifacts")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    reports = repo / "docs" / "messaging" / "reports"
    candidate_root = repo / "docs" / "messaging" / "candidates" / CANDIDATE_NAME
    import_inputs = candidate_root / "import_inputs"
    schema_scripts = candidate_root / "schema_scripts"
    candidate_reports = candidate_root / "reports"

    phase6_status = reports / "message_catalog_phase6_status_summary_v1.csv"
    phase6_messages = reports / "message_catalog_phase6_system_messages_v1.csv"
    phase6_text = reports / "message_catalog_phase6_system_message_text_v1.csv"
    phase6_validation = reports / "message_catalog_phase6_validation_v1.csv"
    phase7_status = reports / "message_catalog_phase7_status_summary_v1.csv"
    phase8_status = reports / "message_catalog_phase8_status_summary_v1.csv"
    phase8_schema = reports / "message_catalog_phase8_dbf_schema_plan_v1.csv"
    phase8_tags = reports / "message_catalog_phase8_index_tag_plan_v1.csv"

    gates: List[Dict[str, str]] = []
    for label, path in [
        ("PHASE6_STATUS_PRESENT", phase6_status),
        ("PHASE6_MESSAGES_PRESENT", phase6_messages),
        ("PHASE6_TEXT_PRESENT", phase6_text),
        ("PHASE7_STATUS_PRESENT", phase7_status),
        ("PHASE8_STATUS_PRESENT", phase8_status),
        ("PHASE8_SCHEMA_PRESENT", phase8_schema),
        ("PHASE8_TAG_PLAN_PRESENT", phase8_tags),
    ]:
        require(path, gates, label)

    if not args.allow_candidate_staging:
        gates.append({"GATE": "CANDIDATE_STAGING_AUTHORIZED", "STATUS": "FAIL", "DETAIL": "Missing --allow-candidate-staging"})
    else:
        gates.append({"GATE": "CANDIDATE_STAGING_AUTHORIZED", "STATUS": "PASS", "DETAIL": "Operator supplied --allow-candidate-staging"})

    if any(g["STATUS"] != "PASS" for g in gates):
        write_csv(reports / "message_catalog_phase9_gate_check_v1.csv", gates, ["GATE", "STATUS", "DETAIL"])
        print("MESSAGE_CATALOG_PHASE9_INACTIVE_CANDIDATE_STAGING_BLOCKED")
        print(f"  gate failures: {sum(1 for g in gates if g['STATUS'] != 'PASS')}")
        print(f"  reports: {reports}")
        return 2

    messages = read_csv(phase6_messages)
    texts = read_csv(phase6_text)
    validation_rows = read_csv(phase6_validation) if phase6_validation.exists() else []
    locales = sorted({r.get("LOCALE", "") for r in texts if r.get("LOCALE", "")})

    # Stage import inputs as normalized UTF-8 CSVs.
    staged_messages = import_inputs / "SYSTEM_MESSAGES_import_candidate_v1.csv"
    staged_text = import_inputs / "SYSTEM_MESSAGE_TEXT_import_candidate_v1.csv"
    copy_text(phase6_messages, staged_messages)
    copy_text(phase6_text, staged_text)

    # Stage Phase 8 schema/tag plans alongside candidate inputs.
    copy_text(phase8_schema, schema_scripts / "SYSTEM_MESSAGES_SYSTEM_MESSAGE_TEXT_schema_plan_v1.csv")
    copy_text(phase8_tags, schema_scripts / "SYSTEM_MESSAGES_SYSTEM_MESSAGE_TEXT_index_tag_plan_v1.csv")
    write_text(schema_scripts / "MESSAGE_CATALOG_PHASE9_CANDIDATE_SCHEMA_TEMPLATE.dts", make_dts_script(str(staged_messages.relative_to(repo)), str(staged_text.relative_to(repo))))

    artifact_rows = []
    for path in [
        staged_messages,
        staged_text,
        schema_scripts / "SYSTEM_MESSAGES_SYSTEM_MESSAGE_TEXT_schema_plan_v1.csv",
        schema_scripts / "SYSTEM_MESSAGES_SYSTEM_MESSAGE_TEXT_index_tag_plan_v1.csv",
        schema_scripts / "MESSAGE_CATALOG_PHASE9_CANDIDATE_SCHEMA_TEMPLATE.dts",
    ]:
        artifact_rows.append({
            "RELATIVE_PATH": str(path.relative_to(repo)).replace("\\", "/"),
            "BYTES": path.stat().st_size,
            "SHA256": sha256_file(path),
            "ROLE": "candidate_staging_artifact",
        })

    manifest = {
        "status": STATUS,
        "candidate_name": CANDIDATE_NAME,
        "candidate_root": str(candidate_root.relative_to(repo)).replace("\\", "/"),
        "messages": len(messages),
        "text_rows": len(texts),
        "locales": locales,
        "validation_issues": len(validation_rows),
        "candidate_artifacts": artifact_rows,
        "dbf_files_created": 0,
        "cdx_files_created": 0,
        "lmdb_env_created": 0,
        "active_promotion_authorized": 0,
        "active_catalog_mutation": 0,
    }
    write_text(candidate_root / "candidate_manifest_v1.json", json.dumps(manifest, indent=2) + "\n")
    artifact_rows.append({
        "RELATIVE_PATH": str((candidate_root / "candidate_manifest_v1.json").relative_to(repo)).replace("\\", "/"),
        "BYTES": (candidate_root / "candidate_manifest_v1.json").stat().st_size,
        "SHA256": sha256_file(candidate_root / "candidate_manifest_v1.json"),
        "ROLE": "candidate_manifest",
    })

    # Reports
    status_rows = [{
        "STATUS": STATUS,
        "MESSAGES": len(messages),
        "TEXT_ROWS": len(texts),
        "LOCALES": ";".join(locales),
        "VALIDATION_ISSUES": len(validation_rows),
        "CANDIDATE_STAGING_AUTHORIZED": 1,
        "DBF_FILES_CREATED": 0,
        "CDX_FILES_CREATED": 0,
        "LMDB_CREATED": 0,
        "ACTIVE_PROMOTION_AUTHORIZED": 0,
        "CANDIDATE_ROOT": str(candidate_root.relative_to(repo)).replace("\\", "/"),
    }]
    write_csv(reports / "message_catalog_phase9_status_summary_v1.csv", status_rows, list(status_rows[0].keys()))
    write_csv(reports / "message_catalog_phase9_gate_check_v1.csv", gates + [
        {"GATE": "DBF_CREATION_ZERO", "STATUS": "PASS", "DETAIL": "No DBF files created by Phase 9."},
        {"GATE": "ACTIVE_PROMOTION_NOT_AUTHORIZED", "STATUS": "PASS", "DETAIL": "No active catalog promotion authorized."},
    ], ["GATE", "STATUS", "DETAIL"])
    write_csv(reports / "message_catalog_phase9_candidate_artifact_inventory_v1.csv", artifact_rows, ["RELATIVE_PATH", "BYTES", "SHA256", "ROLE"])
    write_csv(candidate_reports / "message_catalog_phase9_candidate_artifact_inventory_v1.csv", artifact_rows, ["RELATIVE_PATH", "BYTES", "SHA256", "ROLE"])

    boundary_rows = [
        {"PROTECTED_SYSTEM": "DBF_CATALOGS", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No DBF files created, opened for write, or promoted. Candidate import CSV/schema artifacts only."},
        {"PROTECTED_SYSTEM": "CDX_INDEXES", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CDX/index files created or rebuilt."},
        {"PROTECTED_SYSTEM": "LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No LMDB environment created or rebuilt."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No HELP DATA rebuild or mutation."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CMDHELPCHK mutation."},
        {"PROTECTED_SYSTEM": "SOURCE_MINING", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No source-mining mutation."},
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No source files edited by this script."},
        {"PROTECTED_SYSTEM": "RUNTIME_EXECUTION", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No DotTalk++ runtime execution required."},
        {"PROTECTED_SYSTEM": "CATALOG_PROMOTION", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active catalog promotion authorized or performed."},
    ]
    write_csv(reports / "message_catalog_phase9_boundary_ledger_v1.csv", boundary_rows, ["PROTECTED_SYSTEM", "MUTATION_ALLOWED", "OBSERVED_MUTATION", "DETAIL"])

    md = f"""# Message Catalog Phase 9 Inactive Candidate Staging Report

Status: `{STATUS}`

## Counts

- Messages: {len(messages)}
- Text rows: {len(texts)}
- Locales: {', '.join(locales)}
- Validation issues: {len(validation_rows)}

## Candidate root

`{str(candidate_root.relative_to(repo)).replace('\\', '/')}`

## Boundary

Phase 9 created inactive candidate staging artifacts only. It did not create DBF, CDX, or LMDB artifacts and did not promote any active catalog.

## Next gate

`HOLD_OR_AUTHORIZE_PHASE10_CANDIDATE_DBF_EXECUTION_PLAN`
"""
    write_text(reports / "MESSAGE_CATALOG_PHASE9_INACTIVE_CANDIDATE_STAGING_REPORT.md", md)
    write_text(candidate_reports / "MESSAGE_CATALOG_PHASE9_INACTIVE_CANDIDATE_STAGING_REPORT.md", md)

    print(STATUS)
    print(f"  messages: {len(messages)}")
    print(f"  text rows: {len(texts)}")
    print(f"  locales: {', '.join(locales)}")
    print(f"  validation issues: {len(validation_rows)}")
    print("  candidate artifacts staged: 6")
    print("  dbf files created: 0")
    print("  active promotion authorized: 0")
    print(f"  reports: {reports}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
