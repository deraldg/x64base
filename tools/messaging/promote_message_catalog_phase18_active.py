#!/usr/bin/env python3
"""
Phase 18: Active Messaging catalog promotion.

Promotes the proven Phase 15X/16X x64 Messaging candidate artifacts into the
active DotTalk++ data messaging catalog layout.

Default active layout:
  DBF     dottalkpp/data/messaging
  INDEXES dottalkpp/data/indexes/messaging
  LMDB    dottalkpp/data/lmdb/messaging

This is an authorized active Messaging catalog mutation only. It does not mutate
HELP DATA, CMDHELPCHK, source mining, source code, manuals, or production
SelfDoc/Data Dictionary catalogs.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

STATUS_GREEN = "MESSAGE_CATALOG_PHASE18_ACTIVE_PROMOTION_GREEN"
STATUS_BLOCKED = "MESSAGE_CATALOG_PHASE18_ACTIVE_PROMOTION_BLOCKED"
NEXT_GATE = "HOLD_OR_RUN_PHASE18_ACTIVE_READBACK_SMOKE"
REPORT_DIR = Path("docs/messaging/reports")
CANDIDATE_ROOT = Path("docs/messaging/candidates/phase15x_x64_candidate_rebuild")

TABLES = ["SYSTEM_MESSAGES", "SYSTEM_MESSAGE_TEXT"]

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

def inventory_file(path: Path, repo: Path, role: str) -> dict[str, Any]:
    return {
        "RELATIVE_PATH": str(path.relative_to(repo)).replace("\\", "/") if path.is_relative_to(repo) else str(path),
        "BYTES": path.stat().st_size,
        "SHA256": sha256_file(path),
        "ROLE": role,
    }

def copy_file(src: Path, dst: Path, repo: Path, rows: list[dict[str, Any]], role: str) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    rows.append({
        "SOURCE_PATH": str(src.relative_to(repo)).replace("\\", "/"),
        "TARGET_PATH": str(dst.relative_to(repo)).replace("\\", "/"),
        "BYTES": dst.stat().st_size,
        "SHA256": sha256_file(dst),
        "ROLE": role,
    })

def copy_dir(src: Path, dst: Path, repo: Path, rows: list[dict[str, Any]], role: str) -> None:
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)
    for p in sorted(dst.rglob("*")):
        if p.is_file():
            rel_src = src / p.relative_to(dst)
            rows.append({
                "SOURCE_PATH": str(rel_src.relative_to(repo)).replace("\\", "/"),
                "TARGET_PATH": str(p.relative_to(repo)).replace("\\", "/"),
                "BYTES": p.stat().st_size,
                "SHA256": sha256_file(p),
                "ROLE": role,
            })

def backup_existing(path: Path, backup_root: Path, repo: Path, rows: list[dict[str, Any]]) -> None:
    if not path.exists():
        return
    if path.is_file():
        target = backup_root / path.relative_to(repo)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)
        rows.append({
            "ORIGINAL_PATH": str(path.relative_to(repo)).replace("\\", "/"),
            "BACKUP_PATH": str(target.relative_to(repo)).replace("\\", "/"),
            "BYTES": target.stat().st_size,
            "SHA256": sha256_file(target),
            "ROLE": "backed_up_existing_active_file",
        })
    elif path.is_dir():
        target_dir = backup_root / path.relative_to(repo)
        if target_dir.exists():
            shutil.rmtree(target_dir)
        shutil.copytree(path, target_dir)
        for p in sorted(target_dir.rglob("*")):
            if p.is_file():
                orig = path / p.relative_to(target_dir)
                rows.append({
                    "ORIGINAL_PATH": str(orig.relative_to(repo)).replace("\\", "/"),
                    "BACKUP_PATH": str(p.relative_to(repo)).replace("\\", "/"),
                    "BYTES": p.stat().st_size,
                    "SHA256": sha256_file(p),
                    "ROLE": "backed_up_existing_active_dir_file",
                })

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--allow-active-messaging-catalog-promotion", action="store_true")
    ap.add_argument("--active-dbf-dir", default="")
    ap.add_argument("--active-indexes-dir", default="")
    ap.add_argument("--active-lmdb-dir", default="")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    reports = repo / REPORT_DIR
    reports.mkdir(parents=True, exist_ok=True)

    active_dbf = Path(args.active_dbf_dir).resolve() if args.active_dbf_dir else repo / "dottalkpp/data/messaging"
    active_indexes = Path(args.active_indexes_dir).resolve() if args.active_indexes_dir else repo / "dottalkpp/data/indexes/messaging"
    active_lmdb = Path(args.active_lmdb_dir).resolve() if args.active_lmdb_dir else repo / "dottalkpp/data/lmdb/messaging"

    candidate = repo / CANDIDATE_ROOT
    cand_dbf = candidate / "dbf"
    cand_indexes = candidate / "indexes"
    cand_lmdb = candidate / "lmdb"

    p16x = first_row(reports / "message_catalog_phase16x_status_summary_v1.csv")
    p17 = first_row(reports / "message_catalog_phase17_status_summary_v1.csv")

    messages = p16x.get("MESSAGES", "12")
    text_rows = p16x.get("TEXT_ROWS", "60")
    locales = p16x.get("LOCALES", "de;en-US;es;fr;it")

    gates: list[dict[str, Any]] = []
    failures = 0
    def gate(name: str, ok: bool, detail: str) -> None:
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": detail})
        if not ok:
            failures += 1

    gate("OPERATOR_AUTHORIZED_ACTIVE_MESSAGING_CATALOG_PROMOTION", args.allow_active_messaging_catalog_promotion, "requires --allow-active-messaging-catalog-promotion")
    gate("PHASE16X_STATUS_GREEN", p16x.get("STATUS") == "MESSAGE_CATALOG_PHASE16X_X64_CANDIDATE_LMDB_BUILD_GREEN", p16x.get("STATUS", ""))
    gate("PHASE17_REVIEW_PRESENT", bool(p17), "message_catalog_phase17_status_summary_v1.csv")
    if p17:
        gate("PHASE17_REVIEW_GREEN_OR_HELD", p17.get("STATUS") == "MESSAGE_CATALOG_PHASE17_PROMOTION_READINESS_REVIEW_GREEN_PROMOTION_HELD", p17.get("STATUS", ""))

    for t in TABLES:
        gate(f"CANDIDATE_{t}_DBF_PRESENT", (cand_dbf / f"{t}.dbf").exists(), str(cand_dbf / f"{t}.dbf"))
        # Memo sidecar expected for SYSTEM_MESSAGE_TEXT and accepted for SYSTEM_MESSAGES if present.
        if t == "SYSTEM_MESSAGE_TEXT":
            gate(f"CANDIDATE_{t}_DBT_PRESENT", (cand_dbf / f"{t}.dbt").exists(), str(cand_dbf / f"{t}.dbt"))
        gate(f"CANDIDATE_{t}_CDX_PRESENT", (cand_indexes / f"{t}.cdx").exists(), str(cand_indexes / f"{t}.cdx"))
        gate(f"CANDIDATE_{t}_LMDB_ENV_PRESENT", (cand_lmdb / f"{t}.cdx.d").exists(), str(cand_lmdb / f"{t}.cdx.d"))

    promoted_rows: list[dict[str, Any]] = []
    backup_rows: list[dict[str, Any]] = []
    active_path_rows = [
        {"PATH_ROLE": "ACTIVE_MESSAGING_DBF", "PATH": str(active_dbf)},
        {"PATH_ROLE": "ACTIVE_MESSAGING_INDEXES", "PATH": str(active_indexes)},
        {"PATH_ROLE": "ACTIVE_MESSAGING_LMDB", "PATH": str(active_lmdb)},
        {"PATH_ROLE": "CANDIDATE_DBF", "PATH": str(cand_dbf)},
        {"PATH_ROLE": "CANDIDATE_INDEXES", "PATH": str(cand_indexes)},
        {"PATH_ROLE": "CANDIDATE_LMDB", "PATH": str(cand_lmdb)},
    ]

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup_root = repo / "docs/messaging/backups" / f"MSG-018_ACTIVE_PROMOTION_BACKUP_{timestamp}"

    if failures == 0:
        active_dbf.mkdir(parents=True, exist_ok=True)
        active_indexes.mkdir(parents=True, exist_ok=True)
        active_lmdb.mkdir(parents=True, exist_ok=True)

        # Back up exactly the active artifacts this promotion will replace.
        for t in TABLES:
            for ext in [".dbf", ".dbt"]:
                backup_existing(active_dbf / f"{t}{ext}", backup_root, repo, backup_rows)
            backup_existing(active_indexes / f"{t}.cdx", backup_root, repo, backup_rows)
            backup_existing(active_lmdb / f"{t}.cdx.d", backup_root, repo, backup_rows)

        # Promote candidate DBF/DBT.
        for t in TABLES:
            copy_file(cand_dbf / f"{t}.dbf", active_dbf / f"{t}.dbf", repo, promoted_rows, "active_messaging_dbf")
            dbt_src = cand_dbf / f"{t}.dbt"
            if dbt_src.exists():
                copy_file(dbt_src, active_dbf / f"{t}.dbt", repo, promoted_rows, "active_messaging_dbt")
            copy_file(cand_indexes / f"{t}.cdx", active_indexes / f"{t}.cdx", repo, promoted_rows, "active_messaging_cdx")
            copy_dir(cand_lmdb / f"{t}.cdx.d", active_lmdb / f"{t}.cdx.d", repo, promoted_rows, "active_messaging_lmdb_env_file")

        # Create a runtime smoke script using active paths.
        smoke_dir = repo / "docs/messaging/scripts"
        smoke_dir.mkdir(parents=True, exist_ok=True)
        smoke = smoke_dir / "MESSAGE_CATALOG_PHASE18_ACTIVE_READBACK_SMOKE.dts"
        smoke.write_text("\n".join([
            "* MESSAGE_CATALOG_PHASE18_ACTIVE_READBACK_SMOKE.dts",
            "* Read-only active Messaging catalog smoke after MSG-018 promotion.",
            "CLOSE ALL",
            f"SET PATH DBF {active_dbf}",
            f"SET PATH INDEXES {active_indexes}",
            f"SET PATH LMDB {active_lmdb}",
            "",
            "SELECT 0",
            "USE SYSTEM_MESSAGES",
            "AREA",
            "COUNT",
            "STRUCT",
            "SL 3",
            "",
            "SELECT 1",
            "USE SYSTEM_MESSAGE_TEXT",
            "AREA",
            "COUNT",
            "STRUCT",
            "SL 3",
            "",
            "SELECT 2",
            "",
        ]), encoding="utf-8")
        promoted_rows.append({
            "SOURCE_PATH": "generated",
            "TARGET_PATH": str(smoke.relative_to(repo)).replace("\\", "/"),
            "BYTES": smoke.stat().st_size,
            "SHA256": sha256_file(smoke),
            "ROLE": "active_readback_smoke_script",
        })

    status = STATUS_GREEN if failures == 0 else STATUS_BLOCKED
    validation_issues = "0" if failures == 0 else str(failures)

    write_csv(reports / "message_catalog_phase18_status_summary_v1.csv", [{
        "STATUS": status,
        "MESSAGES": messages,
        "TEXT_ROWS": text_rows,
        "LOCALES": locales,
        "VALIDATION_ISSUES": validation_issues,
        "ACTIVE_PROMOTION_AUTHORIZED": 1 if args.allow_active_messaging_catalog_promotion else 0,
        "ACTIVE_DBF_FILES_PROMOTED": len([r for r in promoted_rows if r.get("ROLE") == "active_messaging_dbf"]),
        "ACTIVE_CDX_FILES_PROMOTED": len([r for r in promoted_rows if r.get("ROLE") == "active_messaging_cdx"]),
        "ACTIVE_LMDB_FILE_ROWS_PROMOTED": len([r for r in promoted_rows if r.get("ROLE") == "active_messaging_lmdb_env_file"]),
        "BACKUP_ROWS": len(backup_rows),
        "NEXT_GATE": NEXT_GATE,
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }], ["STATUS", "MESSAGES", "TEXT_ROWS", "LOCALES", "VALIDATION_ISSUES",
         "ACTIVE_PROMOTION_AUTHORIZED", "ACTIVE_DBF_FILES_PROMOTED",
         "ACTIVE_CDX_FILES_PROMOTED", "ACTIVE_LMDB_FILE_ROWS_PROMOTED",
         "BACKUP_ROWS", "NEXT_GATE", "REPORT_TIMESTAMP_UTC"])

    write_csv(reports / "message_catalog_phase18_gate_check_v1.csv", gates, ["GATE", "STATUS", "DETAIL"])
    write_csv(reports / "message_catalog_phase18_promotion_inventory_v1.csv", promoted_rows,
              ["SOURCE_PATH", "TARGET_PATH", "BYTES", "SHA256", "ROLE"])
    write_csv(reports / "message_catalog_phase18_backup_inventory_v1.csv", backup_rows,
              ["ORIGINAL_PATH", "BACKUP_PATH", "BYTES", "SHA256", "ROLE"])
    write_csv(reports / "message_catalog_phase18_active_paths_v1.csv", active_path_rows,
              ["PATH_ROLE", "PATH"])

    boundary = [
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_DBF_CATALOG", "MUTATION_ALLOWED": 1, "OBSERVED_MUTATION": len([r for r in promoted_rows if r.get("ROLE") in ("active_messaging_dbf", "active_messaging_dbt")]), "DETAIL": "Authorized promotion copies Messaging DBF/DBT artifacts to active messaging DBF path."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_CDX_INDEXES", "MUTATION_ALLOWED": 1, "OBSERVED_MUTATION": len([r for r in promoted_rows if r.get("ROLE") == "active_messaging_cdx"]), "DETAIL": "Authorized promotion copies Messaging CDX artifacts to active messaging indexes path."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_LMDB", "MUTATION_ALLOWED": 1, "OBSERVED_MUTATION": len([r for r in promoted_rows if r.get("ROLE") == "active_messaging_lmdb_env_file"]), "DETAIL": "Authorized promotion copies Messaging LMDB environment files to active messaging LMDB path."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No HELP DATA rebuild or mutation."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CMDHELPCHK mutation."},
        {"PROTECTED_SYSTEM": "SOURCE_MINING", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No source-mining mutation."},
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No source-code mutation."},
        {"PROTECTED_SYSTEM": "MANUALGEN", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No manualgen publication/catalog mutation."},
        {"PROTECTED_SYSTEM": "DATADICT_SELF_DOC", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No Data Dictionary/SelfDoc catalog mutation."},
    ]
    write_csv(reports / "message_catalog_phase18_boundary_ledger_v1.csv", boundary,
              ["PROTECTED_SYSTEM", "MUTATION_ALLOWED", "OBSERVED_MUTATION", "DETAIL"])

    manifest = {
        "status": status,
        "active_paths": active_path_rows,
        "messages": int(messages) if str(messages).isdigit() else messages,
        "text_rows": int(text_rows) if str(text_rows).isdigit() else text_rows,
        "locales": locales.split(";") if locales else [],
        "validation_issues": int(validation_issues) if str(validation_issues).isdigit() else validation_issues,
        "active_promotion_authorized": 1 if args.allow_active_messaging_catalog_promotion else 0,
        "promotion_inventory": promoted_rows,
        "backup_inventory": backup_rows,
        "next_gate": NEXT_GATE,
    }
    manifest_path = repo / "docs/messaging/reports/message_catalog_phase18_active_promotion_manifest_v1.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    print(status)
    print(f"  messages: {messages}")
    print(f"  text rows: {text_rows}")
    print(f"  locales: {locales.replace(';', ', ')}")
    print(f"  validation issues: {validation_issues}")
    print(f"  active promotion authorized: {1 if args.allow_active_messaging_catalog_promotion else 0}")
    print(f"  active dbf files promoted: {len([r for r in promoted_rows if r.get('ROLE') == 'active_messaging_dbf'])}")
    print(f"  active cdx files promoted: {len([r for r in promoted_rows if r.get('ROLE') == 'active_messaging_cdx'])}")
    print(f"  active lmdb file rows promoted: {len([r for r in promoted_rows if r.get('ROLE') == 'active_messaging_lmdb_env_file'])}")
    print(f"  backup rows: {len(backup_rows)}")
    print(f"  reports: {reports}")
    return 0 if status == STATUS_GREEN else 2

if __name__ == "__main__":
    raise SystemExit(main())
