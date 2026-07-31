#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

STATUS_APPLIED = "LOCALE_PHASE23K_GUARDED_MESSAGING_LOCALE_SPINE_SOURCE_PATCH_APPLIED_BUILD_HELD"
STATUS_BLOCKED = "LOCALE_PHASE23K_GUARDED_MESSAGING_LOCALE_SPINE_SOURCE_PATCH_BLOCKED"
NEXT_GATE = "BUILD_AND_RUN_PHASE23K_MESSAGING_LOCALE_SPINE_SCAFFOLD_SMOKE_THEN_VALIDATE"
LOCALE_REPORT_DIR = Path("docs/locale/reports")
BACKUP_ROOT = Path("docs/locale/backups")

HEADER_REL = Path("src/help/locale_spine_catalog.hpp")
CPP_REL = Path("src/help/locale_spine_catalog.cpp")
CMAKE_REL = Path("src/help/CMakeLists.txt")
SMOKE_REL = Path("docs/locale/scripts/LOCALE_PHASE23K_MESSAGING_LOCALE_SPINE_SCAFFOLD_SMOKE.dts")

HEADER_TEXT = r"""#pragma once

#include <string>
#include <vector>

namespace dottalk {
namespace locale_spine {

struct ActiveLocaleSpineStatus {
    bool dbf_present = false;
    bool cdx_present = false;
    bool lmdb_present = false;
    int locale_rows = -1;
    int fallback_rows = -1;
    std::string dbf_dir;
    std::string indexes_dir;
    std::string lmdb_dir;
    std::string detail;
};

ActiveLocaleSpineStatus active_locale_spine_status(const std::string& repo_root = std::string());

bool active_locale_spine_available(const std::string& repo_root = std::string());

std::vector<std::string> active_locale_fallback_chain(
    const std::string& requested_locale,
    const std::string& repo_root = std::string());

}  // namespace locale_spine
}  // namespace dottalk
"""

CPP_TEXT = r"""#include "locale_spine_catalog.hpp"

#include <cstdint>
#include <fstream>
#include <sstream>
#include <string>
#include <vector>

namespace dottalk {
namespace locale_spine {

namespace {

std::string join_path(const std::string& lhs, const std::string& rhs) {
    if (lhs.empty()) {
        return rhs;
    }
    const char last = lhs[lhs.size() - 1];
    if (last == '/' || last == '\\') {
        return lhs + rhs;
    }
    return lhs + "/" + rhs;
}

bool file_exists(const std::string& path) {
    std::ifstream in(path.c_str(), std::ios::binary);
    return in.good();
}

int dbf_record_count(const std::string& path) {
    std::ifstream in(path.c_str(), std::ios::binary);
    if (!in.good()) {
        return -1;
    }

    unsigned char header[8] = {0};
    in.read(reinterpret_cast<char*>(header), 8);
    if (in.gcount() < 8) {
        return -1;
    }

    const std::uint32_t count =
        static_cast<std::uint32_t>(header[4]) |
        (static_cast<std::uint32_t>(header[5]) << 8) |
        (static_cast<std::uint32_t>(header[6]) << 16) |
        (static_cast<std::uint32_t>(header[7]) << 24);

    if (count > static_cast<std::uint32_t>(100000000)) {
        return -1;
    }

    return static_cast<int>(count);
}

std::string locale_dbf_dir(const std::string& repo_root) {
    return join_path(repo_root, "dottalkpp/data/locale");
}

std::string locale_indexes_dir(const std::string& repo_root) {
    return join_path(repo_root, "dottalkpp/data/indexes/locale");
}

std::string locale_lmdb_dir(const std::string& repo_root) {
    return join_path(repo_root, "dottalkpp/data/lmdb/locale");
}

}  // namespace

ActiveLocaleSpineStatus active_locale_spine_status(const std::string& repo_root) {
    ActiveLocaleSpineStatus status;

    status.dbf_dir = locale_dbf_dir(repo_root);
    status.indexes_dir = locale_indexes_dir(repo_root);
    status.lmdb_dir = locale_lmdb_dir(repo_root);

    const std::string system_locales_dbf = join_path(status.dbf_dir, "SYSTEM_LOCALES.dbf");
    const std::string fallback_dbf = join_path(status.dbf_dir, "SYSTEM_LOCALE_FALLBACK.dbf");

    const std::string system_locales_cdx = join_path(status.indexes_dir, "SYSTEM_LOCALES.cdx");
    const std::string fallback_cdx = join_path(status.indexes_dir, "SYSTEM_LOCALE_FALLBACK.cdx");

    const std::string system_locales_lmdb = join_path(status.lmdb_dir, "SYSTEM_LOCALES.cdx.d/data.mdb");
    const std::string fallback_lmdb = join_path(status.lmdb_dir, "SYSTEM_LOCALE_FALLBACK.cdx.d/data.mdb");

    status.dbf_present = file_exists(system_locales_dbf) && file_exists(fallback_dbf);
    status.cdx_present = file_exists(system_locales_cdx) && file_exists(fallback_cdx);
    status.lmdb_present = file_exists(system_locales_lmdb) && file_exists(fallback_lmdb);

    status.locale_rows = dbf_record_count(system_locales_dbf);
    status.fallback_rows = dbf_record_count(fallback_dbf);

    std::ostringstream detail;
    detail << "active shared locale spine "
           << "dbf=" << (status.dbf_present ? "present" : "missing")
           << "; cdx=" << (status.cdx_present ? "present" : "missing")
           << "; lmdb=" << (status.lmdb_present ? "present" : "missing")
           << "; locale_rows=" << status.locale_rows
           << "; fallback_rows=" << status.fallback_rows;
    status.detail = detail.str();

    return status;
}

bool active_locale_spine_available(const std::string& repo_root) {
    const ActiveLocaleSpineStatus status = active_locale_spine_status(repo_root);
    return status.dbf_present && status.cdx_present && status.lmdb_present &&
           status.locale_rows >= 0 && status.fallback_rows >= 0;
}

std::vector<std::string> active_locale_fallback_chain(
    const std::string& requested_locale,
    const std::string& repo_root) {
    (void)repo_root;

    std::vector<std::string> chain;
    if (!requested_locale.empty()) {
        chain.push_back(requested_locale);
    }

    if (requested_locale != "en-US") {
        chain.push_back("en-US");
    }

    return chain;
}

}  // namespace locale_spine
}  // namespace dottalk
"""

SMOKE_TEXT = r"""* LOCALE_PHASE23K_MESSAGING_LOCALE_SPINE_SCAFFOLD_SMOKE.dts
* Guarded runtime smoke after Phase 23K source scaffold.
* Boundary: current Messaging behavior should remain unchanged.

SET MESSAGE CATALOG CHECK
SET MESSAGE CATALOG GET HELP_HINT_COMMAND LOCALE en-US ARG command=USE
SET MESSAGE CATALOG GET HELP_HINT_COMMAND LOCALE es ARG command=USE
SET MESSAGE CATALOG GET HELP_HINT_COMMAND LOCALE xx-XX ARG command=USE

"""

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

def backup_file(path: Path, backup_root: Path, repo: Path, rows: list[dict[str, Any]]) -> None:
    if not path.exists():
        return
    target = backup_root / rel(path, repo)
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, target)
    rows.append({
        "SOURCE_PATH": rel(path, repo),
        "BACKUP_PATH": rel(target, repo),
        "BYTES": target.stat().st_size,
        "SHA256": sha256_file(target),
        "ACTION": "BACKUP_EXISTING_FILE",
    })

def write_managed_file(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")

def patch_cmake_text(original: str) -> tuple[str, str]:
    if "locale_spine_catalog.cpp" in original:
        return original, "already_present"

    for anchor in ["message_catalog.cpp", "helpdata_messages.cpp"]:
        idx = original.find(anchor)
        if idx >= 0:
            line_start = original.rfind("\n", 0, idx) + 1
            line_end = original.find("\n", idx)
            if line_end < 0:
                line_end = len(original)
            line = original[line_start:line_end]
            indent = line[:len(line) - len(line.lstrip())]
            insert = indent + "locale_spine_catalog.cpp"
            if line.strip().endswith(","):
                insert += ","
            patched = original[:line_end] + "\n" + insert + original[line_end:]
            return patched, f"inserted_after_{anchor}"

    if "GLOB" in original.upper() and "*.cpp" in original:
        return original, "glob_detected_no_cmake_mutation"

    return original, "anchor_missing_no_cmake_mutation"

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--allow-source-mutation", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    reports = repo / LOCALE_REPORT_DIR
    reports.mkdir(parents=True, exist_ok=True)

    phase23j = first_row(reports / "locale_phase23j_status_summary_v1.csv")
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

    gate("OPERATOR_ALLOWED_SOURCE_MUTATION",
         args.allow_source_mutation,
         "requires --allow-source-mutation")
    gate("PHASE23J_PATCH_PLAN_GREEN",
         phase23j.get("STATUS") == "LOCALE_PHASE23J_GUARDED_MESSAGING_LOCALE_SPINE_SOURCE_PATCH_PLAN_GREEN_SOURCE_HELD",
         phase23j.get("STATUS", ""))
    gate("PHASE23J_VALIDATION_ZERO",
         phase23j.get("VALIDATION_ISSUES", "") == "0",
         f"validation_issues={phase23j.get('VALIDATION_ISSUES', '')}")
    gate("PHASE23J_SOURCE_MUTATION_HELD",
         phase23j.get("SOURCE_MUTATION_AUTHORIZED", "") == "0",
         f"source_mutation_authorized={phase23j.get('SOURCE_MUTATION_AUTHORIZED', '')}")
    review("LOC_023J_SAVEPOINT_LATEST",
           latest.get("savepoint_id") == "LOC-023J",
           f"latest_savepoint={latest.get('savepoint_id', '')}; recommended before 23K")

    help_dir = repo / "src/help"
    gate("HELP_SOURCE_DIR_PRESENT", help_dir.exists(), rel(help_dir, repo))

    header = repo / HEADER_REL
    cpp = repo / CPP_REL
    cmake = repo / CMAKE_REL
    smoke = repo / SMOKE_REL

    if header.exists():
        existing = header.read_text(encoding="utf-8", errors="replace")
        gate("HEADER_SAFE_TO_REPLACE",
             "namespace locale_spine" in existing and "active_locale_spine_status" in existing,
             "existing locale_spine_catalog.hpp must be managed/compatible")
    if cpp.exists():
        existing = cpp.read_text(encoding="utf-8", errors="replace")
        gate("CPP_SAFE_TO_REPLACE",
             "namespace locale_spine" in existing and "active_locale_spine_status" in existing,
             "existing locale_spine_catalog.cpp must be managed/compatible")

    status = STATUS_BLOCKED
    mutation_rows: list[dict[str, Any]] = []
    backup_rows: list[dict[str, Any]] = []
    cmake_status = "not_attempted"

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup_root = repo / BACKUP_ROOT / f"LOC-023K_SOURCE_PATCH_BACKUP_{timestamp}"

    if failures == 0:
        for p in [header, cpp, cmake, smoke]:
            backup_file(p, backup_root, repo, backup_rows)

        write_managed_file(header, HEADER_TEXT)
        mutation_rows.append({
            "TARGET_PATH": rel(header, repo),
            "ACTION": "CREATE_OR_REPLACE",
            "BYTES": header.stat().st_size,
            "SHA256": sha256_file(header),
        })

        write_managed_file(cpp, CPP_TEXT)
        mutation_rows.append({
            "TARGET_PATH": rel(cpp, repo),
            "ACTION": "CREATE_OR_REPLACE",
            "BYTES": cpp.stat().st_size,
            "SHA256": sha256_file(cpp),
        })

        if cmake.exists():
            original = cmake.read_text(encoding="utf-8", errors="replace")
            patched, cmake_status = patch_cmake_text(original)
            if patched != original:
                cmake.write_text(patched, encoding="utf-8", newline="\n")
                mutation_rows.append({
                    "TARGET_PATH": rel(cmake, repo),
                    "ACTION": f"UPDATE_CMAKE_{cmake_status}",
                    "BYTES": cmake.stat().st_size,
                    "SHA256": sha256_file(cmake),
                })
        else:
            cmake_status = "cmake_missing_no_update"

        write_managed_file(smoke, SMOKE_TEXT)
        mutation_rows.append({
            "TARGET_PATH": rel(smoke, repo),
            "ACTION": "CREATE_OR_REPLACE_RUNTIME_SMOKE_SCRIPT",
            "BYTES": smoke.stat().st_size,
            "SHA256": sha256_file(smoke),
        })

        status = STATUS_APPLIED

    validation_issues = "0" if status == STATUS_APPLIED else str(failures)

    boundary = [
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 1, "OBSERVED_MUTATION": len([r for r in mutation_rows if r["TARGET_PATH"].startswith("src/")]), "DETAIL": "Authorized 23K narrow source scaffold mutation."},
        {"PROTECTED_SYSTEM": "DOCS_LOCALE_SCRIPT", "MUTATION_ALLOWED": 1, "OBSERVED_MUTATION": len([r for r in mutation_rows if r["TARGET_PATH"].startswith("docs/")]), "DETAIL": "Runtime smoke script staged under docs/locale/scripts."},
        {"PROTECTED_SYSTEM": "BUILD", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No build executed by apply package."},
        {"PROTECTED_SYSTEM": "RUNTIME_BEHAVIOR", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No runtime behavior changed until build/smoke and later wiring."},
        {"PROTECTED_SYSTEM": "ACTIVE_LOCALE_SPINE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active DBF/CDX/LMDB mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_DBF_CATALOG", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active Messaging catalog mutation."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No HELP DATA mutation."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CMDHELPCHK mutation."},
        {"PROTECTED_SYSTEM": "MANUALGEN", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No manualgen mutation."},
        {"PROTECTED_SYSTEM": "DATADICT_SELF_DOC", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No Data Dictionary/SelfDoc mutation."},
    ]

    write_csv(reports / "locale_phase23k_apply_status_summary_v1.csv", [{
        "STATUS": status,
        "VALIDATION_ISSUES": validation_issues,
        "SOURCE_MUTATION_AUTHORIZED": 1 if args.allow_source_mutation else 0,
        "SOURCE_FILES_MUTATED": len([r for r in mutation_rows if r["TARGET_PATH"].startswith("src/")]),
        "DOCS_LOCALE_FILES_MUTATED": len([r for r in mutation_rows if r["TARGET_PATH"].startswith("docs/")]),
        "SOURCE_BACKUP_ROWS": len(backup_rows),
        "CMAKE_UPDATE_STATUS": cmake_status,
        "BUILD_EXECUTED": 0,
        "RUNTIME_SMOKE_EXECUTED": 0,
        "NEXT_GATE": NEXT_GATE,
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }], ["STATUS", "VALIDATION_ISSUES", "SOURCE_MUTATION_AUTHORIZED",
         "SOURCE_FILES_MUTATED", "DOCS_LOCALE_FILES_MUTATED", "SOURCE_BACKUP_ROWS",
         "CMAKE_UPDATE_STATUS", "BUILD_EXECUTED", "RUNTIME_SMOKE_EXECUTED",
         "NEXT_GATE", "REPORT_TIMESTAMP_UTC"])

    write_csv(reports / "locale_phase23k_apply_gate_check_v1.csv", gates, ["GATE", "STATUS", "DETAIL"])
    write_csv(reports / "locale_phase23k_source_mutation_inventory_v1.csv", mutation_rows,
              ["TARGET_PATH", "ACTION", "BYTES", "SHA256"])
    write_csv(reports / "locale_phase23k_source_backup_inventory_v1.csv", backup_rows,
              ["SOURCE_PATH", "BACKUP_PATH", "BYTES", "SHA256", "ACTION"])
    write_csv(reports / "locale_phase23k_boundary_ledger_v1.csv", boundary,
              ["PROTECTED_SYSTEM", "MUTATION_ALLOWED", "OBSERVED_MUTATION", "DETAIL"])

    print(status)
    print(f"  validation issues: {validation_issues}")
    print(f"  source mutation authorized: {1 if args.allow_source_mutation else 0}")
    print(f"  source files mutated: {len([r for r in mutation_rows if r['TARGET_PATH'].startswith('src/')])}")
    print(f"  docs locale files mutated: {len([r for r in mutation_rows if r['TARGET_PATH'].startswith('docs/')])}")
    print(f"  source backup rows: {len(backup_rows)}")
    print(f"  cmake update status: {cmake_status}")
    print("  build executed: 0")
    print("  runtime smoke executed: 0")
    print(f"  next gate: {NEXT_GATE}")
    print(f"  reports: {reports}")
    return 0 if status == STATUS_APPLIED else 2

if __name__ == "__main__":
    raise SystemExit(main())
