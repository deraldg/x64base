#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

STATUS_GREEN = "MESSAGE_CATALOG_PHASE22C_RUNTIME_PROVIDER_SOURCE_PATCH_APPLIED"
STATUS_BLOCKED = "MESSAGE_CATALOG_PHASE22C_RUNTIME_PROVIDER_SOURCE_PATCH_BLOCKED"
NEXT_GATE = "HOLD_OR_RUN_PHASE22D_BUILD_AND_PROVIDER_STATUS_SMOKE"
REPORT_DIR = Path("docs/messaging/reports")
PATCH_ROOT = Path("docs/messaging/patches/phase22b_runtime_provider_candidate")
BACKUP_ROOT_BASE = Path("docs/messaging/backups")

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
        return str(path.relative_to(repo)).replace("\\", "/")
    except ValueError:
        return str(path)

def copy_backup(path: Path, backup_root: Path, repo: Path, rows: list[dict[str, Any]]) -> None:
    if not path.exists():
        return
    dst = backup_root / rel(path, repo)
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, dst)
    rows.append({
        "TARGET_PATH": rel(path, repo),
        "BACKUP_PATH": rel(dst, repo),
        "BYTES": dst.stat().st_size,
        "SHA256": sha256_file(dst),
        "ROLE": "pre_patch_source_backup",
    })

def update_help_cmake(cmake_path: Path) -> tuple[bool, str]:
    text = cmake_path.read_text(encoding="utf-8", errors="replace")
    if "message_catalog.cpp" in text:
        return False, "message_catalog.cpp already present"
    anchor = "    helpdata_messages.cpp"
    if anchor not in text:
        raise RuntimeError("src/help/CMakeLists.txt does not contain expected helpdata_messages.cpp anchor")
    cmake_path.write_text(text.replace(anchor, anchor + "\n    message_catalog.cpp", 1), encoding="utf-8")
    return True, "inserted message_catalog.cpp after helpdata_messages.cpp"

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--allow-source-mutation", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    reports = repo / REPORT_DIR
    reports.mkdir(parents=True, exist_ok=True)

    p22b = first_row(reports / "message_catalog_phase22b_status_summary_v1.csv")
    messages = p22b.get("MESSAGES", "12")
    text_rows = p22b.get("TEXT_ROWS", "60")
    locales = p22b.get("LOCALES", "de;en-US;es;fr;it")

    patch_root = repo / PATCH_ROOT
    cand_hpp = patch_root / "src/help/message_catalog.hpp"
    cand_cpp = patch_root / "src/help/message_catalog.cpp"
    target_hpp = repo / "src/help/message_catalog.hpp"
    target_cpp = repo / "src/help/message_catalog.cpp"
    cmake_path = repo / "src/help/CMakeLists.txt"

    gates: list[dict[str, Any]] = []
    failures = 0

    def gate(name: str, ok: bool, detail: str) -> None:
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": detail})
        if not ok:
            failures += 1

    gate("OPERATOR_AUTHORIZED_SOURCE_MUTATION", args.allow_source_mutation, "requires --allow-source-mutation")
    gate("PHASE22B_CANDIDATE_STAGED", p22b.get("STATUS") == "MESSAGE_CATALOG_PHASE22B_RUNTIME_PROVIDER_PATCH_CANDIDATE_STAGED_SOURCE_HELD", p22b.get("STATUS", ""))
    gate("CANDIDATE_MESSAGE_CATALOG_HPP_PRESENT", cand_hpp.exists(), rel(cand_hpp, repo))
    gate("CANDIDATE_MESSAGE_CATALOG_CPP_PRESENT", cand_cpp.exists(), rel(cand_cpp, repo))
    gate("TARGET_HELP_DIR_PRESENT", (repo / "src/help").exists(), "src/help")
    gate("TARGET_CMAKE_PRESENT", cmake_path.exists(), rel(cmake_path, repo))
    gate("ACTIVE_MESSAGES_DBF_STILL_PRESENT", (repo / "dottalkpp/data/messaging/SYSTEM_MESSAGES.dbf").exists(), "dottalkpp/data/messaging/SYSTEM_MESSAGES.dbf")
    gate("ACTIVE_MESSAGE_TEXT_DBF_STILL_PRESENT", (repo / "dottalkpp/data/messaging/SYSTEM_MESSAGE_TEXT.dbf").exists(), "dottalkpp/data/messaging/SYSTEM_MESSAGE_TEXT.dbf")

    backup_rows: list[dict[str, Any]] = []
    mutation_rows: list[dict[str, Any]] = []
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup_root = repo / BACKUP_ROOT_BASE / f"MSG-022C_SOURCE_PATCH_BACKUP_{timestamp}"

    status = STATUS_BLOCKED
    if failures == 0:
        for t in [target_hpp, target_cpp, cmake_path]:
            copy_backup(t, backup_root, repo, backup_rows)

        target_hpp.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(cand_hpp, target_hpp)
        mutation_rows.append({
            "TARGET_PATH": rel(target_hpp, repo),
            "ACTION": "CREATE_OR_REPLACE",
            "BYTES": target_hpp.stat().st_size,
            "SHA256": sha256_file(target_hpp),
            "DETAIL": "copied staged candidate provider header",
        })

        shutil.copy2(cand_cpp, target_cpp)
        mutation_rows.append({
            "TARGET_PATH": rel(target_cpp, repo),
            "ACTION": "CREATE_OR_REPLACE",
            "BYTES": target_cpp.stat().st_size,
            "SHA256": sha256_file(target_cpp),
            "DETAIL": "copied staged candidate provider source",
        })

        changed_cmake, cmake_detail = update_help_cmake(cmake_path)
        mutation_rows.append({
            "TARGET_PATH": rel(cmake_path, repo),
            "ACTION": "UPDATE" if changed_cmake else "NO_CHANGE",
            "BYTES": cmake_path.stat().st_size,
            "SHA256": sha256_file(cmake_path),
            "DETAIL": cmake_detail,
        })

        status = STATUS_GREEN

    validation_issues = "0" if status == STATUS_GREEN else str(failures)

    write_csv(reports / "message_catalog_phase22c_status_summary_v1.csv", [{
        "STATUS": status,
        "MESSAGES": messages,
        "TEXT_ROWS": text_rows,
        "LOCALES": locales,
        "VALIDATION_ISSUES": validation_issues,
        "SOURCE_MUTATION_AUTHORIZED": 1 if args.allow_source_mutation else 0,
        "SOURCE_FILES_MUTATED": len([r for r in mutation_rows if r["ACTION"] in ("CREATE_OR_REPLACE", "UPDATE")]),
        "SOURCE_BACKUP_ROWS": len(backup_rows),
        "RUNTIME_PROVIDER_PATCH_APPLIED": 1 if status == STATUS_GREEN else 0,
        "BUILD_EXECUTED": 0,
        "NEXT_GATE": NEXT_GATE,
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }], ["STATUS", "MESSAGES", "TEXT_ROWS", "LOCALES", "VALIDATION_ISSUES",
         "SOURCE_MUTATION_AUTHORIZED", "SOURCE_FILES_MUTATED", "SOURCE_BACKUP_ROWS",
         "RUNTIME_PROVIDER_PATCH_APPLIED", "BUILD_EXECUTED", "NEXT_GATE", "REPORT_TIMESTAMP_UTC"])

    write_csv(reports / "message_catalog_phase22c_gate_check_v1.csv", gates, ["GATE", "STATUS", "DETAIL"])
    write_csv(reports / "message_catalog_phase22c_source_mutation_inventory_v1.csv", mutation_rows,
              ["TARGET_PATH", "ACTION", "BYTES", "SHA256", "DETAIL"])
    write_csv(reports / "message_catalog_phase22c_source_backup_inventory_v1.csv", backup_rows,
              ["TARGET_PATH", "BACKUP_PATH", "BYTES", "SHA256", "ROLE"])

    boundary = [
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 1, "OBSERVED_MUTATION": len([r for r in mutation_rows if r["ACTION"] in ("CREATE_OR_REPLACE", "UPDATE")]), "DETAIL": "Authorized source mutation limited to message_catalog.hpp/cpp and src/help/CMakeLists.txt."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_DBF_CATALOG", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_CDX_INDEXES", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active CDX/index mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active LMDB mutation."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No HELP DATA rebuild or mutation."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CMDHELPCHK mutation."},
        {"PROTECTED_SYSTEM": "MANUALGEN", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No manualgen mutation."},
        {"PROTECTED_SYSTEM": "DATADICT_SELF_DOC", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No Data Dictionary/SelfDoc mutation."},
    ]
    write_csv(reports / "message_catalog_phase22c_boundary_ledger_v1.csv", boundary,
              ["PROTECTED_SYSTEM", "MUTATION_ALLOWED", "OBSERVED_MUTATION", "DETAIL"])

    md = f"""# Message Catalog Phase 22C Source Patch Apply

Status: `{status}`

Phase 22C applies the staged provider boundary source patch.

## Applied source scope

- `src/help/message_catalog.hpp`
- `src/help/message_catalog.cpp`
- `src/help/CMakeLists.txt` only if `message_catalog.cpp` needed to be added

## Not performed

- No build executed.
- No runtime smoke executed.
- No active DBF/CDX/LMDB mutation.
- No HELP DATA/CMDHELPCHK/manualgen/Data Dictionary mutation.

## Next gate

`{NEXT_GATE}`
"""
    (reports / "MESSAGE_CATALOG_PHASE22C_SOURCE_PATCH_APPLY.md").write_text(md, encoding="utf-8")

    print(status)
    print(f"  messages: {messages}")
    print(f"  text rows: {text_rows}")
    print(f"  locales: {locales.replace(';', ', ')}")
    print(f"  validation issues: {validation_issues}")
    print(f"  source mutation authorized: {1 if args.allow_source_mutation else 0}")
    print(f"  source files mutated: {len([r for r in mutation_rows if r['ACTION'] in ('CREATE_OR_REPLACE', 'UPDATE')])}")
    print(f"  source backup rows: {len(backup_rows)}")
    print("  build executed: 0")
    print(f"  next gate: {NEXT_GATE}")
    print(f"  reports: {reports}")
    return 0 if status == STATUS_GREEN else 2

if __name__ == "__main__":
    raise SystemExit(main())
