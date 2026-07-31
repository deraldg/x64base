#!/usr/bin/env python3
"""
Phase 14.1 repair: prepare inactive candidate CDX execution using DotTalk path lanes.

This repairs Phase 14 by generating the runtime script in the normal DotTalk
shape:
  SET PATH DBF <candidate dbf dir>
  SET PATH INDEXES <candidate indexes dir>
  SET PATH LMDB <candidate lmdb dir>
  SELECT <area>
  USE <table>
  CDX CREATE
  CDX ADDTAG ...

No CDX files are created by the prepare step.
"""
from __future__ import annotations
import argparse, csv, hashlib, json, shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

STATUS = "MESSAGE_CATALOG_PHASE14_1_PATHED_CDX_RUNTIME_SCRIPT_STAGED"
NEXT_GATE = "RUN_DOTTALK_PHASE14_1_SCRIPT_THEN_VALIDATE_CANDIDATE_CDX_TAGS"
REPORT_DIR = Path("docs/messaging/reports")
PHASE11_DBF = Path("docs/messaging/candidates/phase11_inactive_candidate_dbf_execution/dbf")
PHASE14_ROOT = Path("docs/messaging/candidates/phase14_inactive_candidate_cdx_execution")

TAGS = {
    "SYSTEM_MESSAGES": [
        ("MSGID", "STR(MSGID,10,0)"),
        ("SYMBOL", "SYMBOL"),
        ("ENUMNAME", "ENUMNAME"),
        ("SEVERITY", "SEVERITY"),
        ("FACILITY", "FACILITY"),
        ("OWNER", "OWNER"),
    ],
    "SYSTEM_MESSAGE_TEXT": [
        ("MSG_LOCALE", "STR(MSGID,10,0)+LOCALE"),
        ("SYMBOLLOC", "SYMBOL+LOCALE"),
        ("LOCALE", "LOCALE"),
        ("TXTHASH", "TXTHASH"),
    ],
}

def read_first(path: Path) -> dict[str, str]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
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

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--allow-inactive-candidate-cdx-execution", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    reports = repo / REPORT_DIR
    reports.mkdir(parents=True, exist_ok=True)

    gates: list[dict[str, Any]] = []
    failures = 0
    def gate(name: str, ok: bool, detail: str) -> None:
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": detail})
        if not ok:
            failures += 1

    phase12_status = reports / "message_catalog_phase12_status_summary_v1.csv"
    phase13_status = reports / "message_catalog_phase13_status_summary_v1.csv"
    gate("OPERATOR_AUTHORIZED_INACTIVE_CANDIDATE_CDX_EXECUTION", args.allow_inactive_candidate_cdx_execution, "requires --allow-inactive-candidate-cdx-execution")
    gate("PHASE12_STATUS_PRESENT", phase12_status.exists(), str(phase12_status))
    gate("PHASE13_STATUS_PRESENT", phase13_status.exists(), str(phase13_status))
    if phase12_status.exists():
        gate("PHASE12_STATUS_GREEN", read_first(phase12_status).get("STATUS") == "MESSAGE_CATALOG_PHASE12_CANDIDATE_DBF_ROW_PARITY_GREEN", read_first(phase12_status).get("STATUS", ""))
    if phase13_status.exists():
        gate("PHASE13_STATUS_GREEN", read_first(phase13_status).get("STATUS") == "MESSAGE_CATALOG_PHASE13_CANDIDATE_CDX_TAG_PLAN_GREEN", read_first(phase13_status).get("STATUS", ""))

    for name in ["SYSTEM_MESSAGES", "SYSTEM_MESSAGE_TEXT"]:
        gate(f"{name}_DBF_PRESENT", (repo / PHASE11_DBF / f"{name}.dbf").exists(), str(repo / PHASE11_DBF / f"{name}.dbf"))
        gate(f"{name}_DBT_PRESENT", (repo / PHASE11_DBF / f"{name}.dbt").exists(), str(repo / PHASE11_DBF / f"{name}.dbt"))

    p12 = read_first(phase12_status) if phase12_status.exists() else {}
    messages = p12.get("MESSAGES", "12")
    text_rows = p12.get("TEXT_ROWS", "60")
    locales = p12.get("LOCALES", "de;en-US;es;fr;it")
    validation_issues = p12.get("VALIDATION_ISSUES", "0")

    if failures == 0:
        root = repo / PHASE14_ROOT
        if root.exists():
            shutil.rmtree(root)

        dbf_dir = root / "dbf"
        indexes_dir = root / "indexes"
        lmdb_dir = root / "lmdb"
        scripts_dir = root / "scripts"

        for d in [dbf_dir, indexes_dir, lmdb_dir, scripts_dir]:
            d.mkdir(parents=True, exist_ok=True)

        for name in ["SYSTEM_MESSAGES", "SYSTEM_MESSAGE_TEXT"]:
            shutil.copy2(repo / PHASE11_DBF / f"{name}.dbf", dbf_dir / f"{name}.dbf")
            shutil.copy2(repo / PHASE11_DBF / f"{name}.dbt", dbf_dir / f"{name}.dbt")

        # IMPORTANT: use DotTalk path lanes and table opens, not path-qualified USE.
        # Final blank line is intentionally included.
        dbf_rel = (PHASE14_ROOT / "dbf").as_posix()
        idx_rel = (PHASE14_ROOT / "indexes").as_posix()
        lmdb_rel = (PHASE14_ROOT / "lmdb").as_posix()

        lines = [
            "* MESSAGE_CATALOG_PHASE14_1_CREATE_CANDIDATE_CDX_TAGS.dts",
            "* Candidate-only CDX tag creation for messaging catalog.",
            "* Boundary: inactive candidate path only; no active catalog promotion.",
            "CLOSE ALL",
            f"SET PATH DBF {dbf_rel}",
            f"SET PATH INDEXES {idx_rel}",
            f"SET PATH LMDB {lmdb_rel}",
            "",
            "SELECT 0",
            "USE SYSTEM_MESSAGES",
            "CDX CREATE",
        ]
        for tag, expr in TAGS["SYSTEM_MESSAGES"]:
            lines.append(f"CDX ADDTAG {tag} {expr}")

        lines.extend([
            "",
            "SELECT 1",
            "USE SYSTEM_MESSAGE_TEXT",
            "CDX CREATE",
        ])
        for tag, expr in TAGS["SYSTEM_MESSAGE_TEXT"]:
            lines.append(f"CDX ADDTAG {tag} {expr}")

        lines.extend([
            "",
            "SELECT 2",
            "* Phase 14.1 candidate CDX tag script complete.",
            "",
        ])

        dts = scripts_dir / "MESSAGE_CATALOG_PHASE14_1_CREATE_CANDIDATE_CDX_TAGS.dts"
        dts.write_text("\n".join(lines), encoding="utf-8")

        readme = root / "PHASE14_1_RUNTIME_RUN_INSTRUCTIONS.md"
        readme.write_text(f"""# Phase 14.1 Runtime Instructions

Run DotTalk++ from repo root and execute:

```text
DO {PHASE14_ROOT.as_posix()}/scripts/MESSAGE_CATALOG_PHASE14_1_CREATE_CANDIDATE_CDX_TAGS
QUIT
```

The script sets:

```text
SET PATH DBF {dbf_rel}
SET PATH INDEXES {idx_rel}
SET PATH LMDB {lmdb_rel}
```

Then opens each table in its own work area and creates candidate-only CDX tags.
""", encoding="utf-8")

        artifact_rows = []
        for p in sorted(root.rglob("*")):
            if p.is_file():
                artifact_rows.append({
                    "RELATIVE_PATH": str(p.relative_to(repo)).replace("\\", "/"),
                    "BYTES": p.stat().st_size,
                    "SHA256": sha256_file(p),
                    "ROLE": "phase14_1_cdx_execution_staging_artifact",
                })
        write_csv(reports / "message_catalog_phase14_1_staging_artifact_inventory_v1.csv",
                  artifact_rows, ["RELATIVE_PATH", "BYTES", "SHA256", "ROLE"])

        manifest = {
            "status": STATUS,
            "candidate_name": "phase14_inactive_candidate_cdx_execution",
            "candidate_root": str(PHASE14_ROOT).replace("\\", "/"),
            "dbf_path": dbf_rel,
            "indexes_path": idx_rel,
            "lmdb_path": lmdb_rel,
            "messages": int(messages),
            "text_rows": int(text_rows),
            "locales": locales.split(";") if locales else [],
            "validation_issues": int(validation_issues) if validation_issues.isdigit() else validation_issues,
            "script": str((PHASE14_ROOT / "scripts" / "MESSAGE_CATALOG_PHASE14_1_CREATE_CANDIDATE_CDX_TAGS.dts")).replace("\\", "/"),
            "cdx_files_created_by_prepare": 0,
            "lmdb_env_created": 0,
            "active_promotion_authorized": 0,
            "candidate_artifacts": artifact_rows,
        }
        (root / "candidate_manifest_prepare_v1.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    else:
        write_csv(reports / "message_catalog_phase14_1_staging_artifact_inventory_v1.csv", [], ["RELATIVE_PATH", "BYTES", "SHA256", "ROLE"])

    status = STATUS if failures == 0 else "MESSAGE_CATALOG_PHASE14_1_PATHED_CDX_RUNTIME_SCRIPT_BLOCKED"
    write_csv(reports / "message_catalog_phase14_1_prepare_status_summary_v1.csv", [{
        "STATUS": status,
        "MESSAGES": messages,
        "TEXT_ROWS": text_rows,
        "LOCALES": locales,
        "VALIDATION_ISSUES": validation_issues,
        "CDX_RUNTIME_SCRIPT_STAGED": 1 if failures == 0 else 0,
        "CDX_FILES_CREATED": 0,
        "LMDB_ENV_CREATED": 0,
        "ACTIVE_PROMOTION_AUTHORIZED": 0,
        "NEXT_GATE": NEXT_GATE,
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }], ["STATUS", "MESSAGES", "TEXT_ROWS", "LOCALES", "VALIDATION_ISSUES",
         "CDX_RUNTIME_SCRIPT_STAGED", "CDX_FILES_CREATED", "LMDB_ENV_CREATED",
         "ACTIVE_PROMOTION_AUTHORIZED", "NEXT_GATE", "REPORT_TIMESTAMP_UTC"])

    write_csv(reports / "message_catalog_phase14_1_prepare_gate_check_v1.csv", gates, ["GATE", "STATUS", "DETAIL"])

    boundary = [
        {"PROTECTED_SYSTEM": "INACTIVE_CANDIDATE_DBF_COPY", "MUTATION_ALLOWED": 1, "OBSERVED_MUTATION": 1 if failures == 0 else 0, "DETAIL": "Phase 14.1 prepare copies proven Phase 11 DBF/DBT files into phase14 inactive candidate workspace."},
        {"PROTECTED_SYSTEM": "INACTIVE_CANDIDATE_PATHS", "MUTATION_ALLOWED": 1, "OBSERVED_MUTATION": 1 if failures == 0 else 0, "DETAIL": "Creates candidate dbf/indexes/lmdb directories only under docs/messaging/candidates."},
        {"PROTECTED_SYSTEM": "CDX_INDEXES", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Prepare step creates no CDX/index files."},
        {"PROTECTED_SYSTEM": "LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Prepare step creates candidate lmdb directory only; no LMDB environment."},
        {"PROTECTED_SYSTEM": "ACTIVE_DBF_CATALOGS", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active DBF catalog paths touched."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No HELP DATA mutation."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CMDHELPCHK mutation."},
        {"PROTECTED_SYSTEM": "SOURCE_MINING", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No source-mining mutation."},
        {"PROTECTED_SYSTEM": "CATALOG_PROMOTION", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active catalog promotion."},
    ]
    write_csv(reports / "message_catalog_phase14_1_prepare_boundary_ledger_v1.csv", boundary,
              ["PROTECTED_SYSTEM", "MUTATION_ALLOWED", "OBSERVED_MUTATION", "DETAIL"])

    print(status)
    print(f"  messages: {messages}")
    print(f"  text rows: {text_rows}")
    print(f"  locales: {locales.replace(';', ', ')}")
    print(f"  validation issues: {validation_issues}")
    print(f"  cdx runtime script staged: {1 if failures == 0 else 0}")
    print("  cdx files created: 0")
    print("  lmdb env created: 0")
    print("  active promotion authorized: 0")
    print(f"  reports: {reports}")
    return 0 if failures == 0 else 2

if __name__ == "__main__":
    raise SystemExit(main())
