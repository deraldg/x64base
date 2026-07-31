#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

STATUS_GREEN = "MESSAGE_CATALOG_PHASE22E_3_PROVIDER_ACTIVE_PATH_RESOLVER_REPAIR_APPLIED"
STATUS_BLOCKED = "MESSAGE_CATALOG_PHASE22E_3_PROVIDER_ACTIVE_PATH_RESOLVER_REPAIR_BLOCKED"
NEXT_GATE = "BUILD_AND_RERUN_SET_MESSAGE_CATALOG_CHECK_THEN_VALIDATE_PHASE22E"
REPORT_DIR = Path("docs/messaging/reports")
BACKUP_ROOT_BASE = Path("docs/messaging/backups")

MESSAGE_CATALOG_CPP = '''// ============================================================================
// File: src/help/message_catalog.cpp
// Purpose: Runtime Messaging catalog provider boundary.
// Phase: MSG-022E.3 active path resolver repair.
// ============================================================================

#include "message_catalog.hpp"

#include "helpdata_messages.hpp"

#include <filesystem>
#include <vector>

namespace dottalk::helpdata {
namespace {

namespace fs = std::filesystem;

struct ActiveCatalogPaths {
    fs::path dbf_dir;
    fs::path indexes_dir;
    fs::path lmdb_dir;
    bool present = false;
};

std::string generic_string(const fs::path& p)
{
    return p.lexically_normal().generic_string();
}

std::vector<fs::path> data_root_candidates()
{
    std::vector<fs::path> roots;

    fs::path cur = fs::current_path();
    for (fs::path p = cur; !p.empty(); p = p.parent_path()) {
        roots.push_back(p / "dottalkpp" / "data");
        roots.push_back(p / "data");

        if (p == p.parent_path()) {
            break;
        }
    }

    // Keep the originally advertised relative path as last fallback for reports.
    roots.push_back(fs::path("dottalkpp") / "data");
    return roots;
}

bool messaging_artifacts_present(const fs::path& dbf_dir)
{
    return fs::exists(dbf_dir / "SYSTEM_MESSAGES.dbf")
        && fs::exists(dbf_dir / "SYSTEM_MESSAGE_TEXT.dbf")
        && fs::exists(dbf_dir / "SYSTEM_MESSAGE_TEXT.dtx");
}

ActiveCatalogPaths find_active_catalog_paths()
{
    for (const auto& data_root : data_root_candidates()) {
        // Current promoted active layout:
        //   dottalkpp/data/messaging
        //   dottalkpp/data/indexes/messaging
        //   dottalkpp/data/lmdb/messaging
        ActiveCatalogPaths current{
            data_root / "messaging",
            data_root / "indexes" / "messaging",
            data_root / "lmdb" / "messaging",
            false
        };
        if (messaging_artifacts_present(current.dbf_dir)) {
            current.present = true;
            return current;
        }

        // Defensive fallback if a later layout places DBFs below data/dbf/messaging.
        ActiveCatalogPaths dbf_subdir{
            data_root / "dbf" / "messaging",
            data_root / "indexes" / "messaging",
            data_root / "lmdb" / "messaging",
            false
        };
        if (messaging_artifacts_present(dbf_subdir.dbf_dir)) {
            dbf_subdir.present = true;
            return dbf_subdir;
        }
    }

    ActiveCatalogPaths fallback{
        fs::path("dottalkpp") / "data" / "messaging",
        fs::path("dottalkpp") / "data" / "indexes" / "messaging",
        fs::path("dottalkpp") / "data" / "lmdb" / "messaging",
        false
    };
    return fallback;
}

std::string apply_vars(std::string out,
                       const std::unordered_map<std::string, std::string>& vars)
{
    for (const auto& kv : vars) {
        const std::string needle = "{" + kv.first + "}";
        std::string::size_type pos = 0;
        while ((pos = out.find(needle, pos)) != std::string::npos) {
            out.replace(pos, needle.size(), kv.second);
            pos += kv.second.size();
        }
    }
    return out;
}

} // namespace

MessageCatalogStatus active_message_catalog_status()
{
    MessageCatalogStatus status;
    status.mode = MessageCatalogMode::CompiledFallback;

    const auto active = find_active_catalog_paths();
    status.active_dbf_dir = generic_string(active.dbf_dir);
    status.active_indexes_dir = generic_string(active.indexes_dir);
    status.active_lmdb_dir = generic_string(active.lmdb_dir);

    status.active_catalog_present = active.present;
    status.active_catalog_loaded = false;
    status.message_count = static_cast<int>(all_messages().size());
    status.text_row_count = 0;
    status.detail = status.active_catalog_present
        ? "active Messaging DBF artifacts present; compiled fallback still active"
        : "active Messaging DBF artifacts not found; compiled fallback active";
    return status;
}

std::string format_message_catalog(const std::string& /*locale*/,
                                   const std::string& symbol,
                                   const std::unordered_map<std::string, std::string>& vars)
{
    // Compiled/static fallback first. Active DBF row loading is Phase 22F after
    // the runtime DBF read API is selected and smoke-tested.
    const MessageDef* message = find_message_by_key(symbol);
    if (!message || !message->text) {
        return {};
    }
    return apply_vars(message->text, vars);
}

} // namespace dottalk::helpdata
'''

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

def backup(path: Path, backup_root: Path, repo: Path, rows: list[dict[str, Any]]) -> None:
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

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--allow-source-mutation", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    reports = repo / REPORT_DIR
    reports.mkdir(parents=True, exist_ok=True)

    p22e1 = first_row(reports / "message_catalog_phase22e_1_status_summary_v1.csv")
    messages = p22e1.get("MESSAGES", "12")
    text_rows = p22e1.get("TEXT_ROWS", "60")
    locales = p22e1.get("LOCALES", "de;en-US;es;fr;it")

    target = repo / "src/help/message_catalog.cpp"

    gates: list[dict[str, Any]] = []
    failures = 0

    def gate(name: str, ok: bool, detail: str) -> None:
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": detail})
        if not ok:
            failures += 1

    gate("OPERATOR_AUTHORIZED_SOURCE_MUTATION", args.allow_source_mutation, "requires --allow-source-mutation")
    gate("PHASE22E1_STATUS_HOOK_APPLIED", p22e1.get("STATUS") == "MESSAGE_CATALOG_PHASE22E_1_RUNTIME_PROVIDER_STATUS_SOURCE_PATCH_APPLIED", p22e1.get("STATUS", ""))
    gate("MESSAGE_CATALOG_CPP_PRESENT", target.exists(), rel(target, repo))
    gate("ACTIVE_MESSAGES_DBF_PRESENT", (repo / "dottalkpp/data/messaging/SYSTEM_MESSAGES.dbf").exists(), "dottalkpp/data/messaging/SYSTEM_MESSAGES.dbf")
    gate("ACTIVE_MESSAGE_TEXT_DBF_PRESENT", (repo / "dottalkpp/data/messaging/SYSTEM_MESSAGE_TEXT.dbf").exists(), "dottalkpp/data/messaging/SYSTEM_MESSAGE_TEXT.dbf")
    gate("ACTIVE_MESSAGE_TEXT_DTX_PRESENT", (repo / "dottalkpp/data/messaging/SYSTEM_MESSAGE_TEXT.dtx").exists(), "dottalkpp/data/messaging/SYSTEM_MESSAGE_TEXT.dtx")

    backup_rows: list[dict[str, Any]] = []
    mutation_rows: list[dict[str, Any]] = []

    status = STATUS_BLOCKED
    if failures == 0:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        backup_root = repo / BACKUP_ROOT_BASE / f"MSG-022E3_PROVIDER_PATH_REPAIR_BACKUP_{timestamp}"
        backup(target, backup_root, repo, backup_rows)

        target.write_text(MESSAGE_CATALOG_CPP, encoding="utf-8")
        mutation_rows.append({
            "TARGET_PATH": rel(target, repo),
            "ACTION": "REPLACE",
            "BYTES": target.stat().st_size,
            "SHA256": sha256_file(target),
            "DETAIL": "replaced provider status path resolver with cwd/ancestor-aware active catalog discovery",
        })
        status = STATUS_GREEN

    validation_issues = "0" if status == STATUS_GREEN else str(failures)

    write_csv(reports / "message_catalog_phase22e_3_status_summary_v1.csv", [{
        "STATUS": status,
        "MESSAGES": messages,
        "TEXT_ROWS": text_rows,
        "LOCALES": locales,
        "VALIDATION_ISSUES": validation_issues,
        "SOURCE_MUTATION_AUTHORIZED": 1 if args.allow_source_mutation else 0,
        "SOURCE_FILES_MUTATED": len(mutation_rows),
        "SOURCE_BACKUP_ROWS": len(backup_rows),
        "PROVIDER_ACTIVE_PATH_RESOLVER_REPAIRED": 1 if status == STATUS_GREEN else 0,
        "BUILD_EXECUTED": 0,
        "RUNTIME_SMOKE_EXECUTED": 0,
        "NEXT_GATE": "BUILD_AND_RERUN_SET_MESSAGE_CATALOG_CHECK_THEN_VALIDATE_PHASE22E",
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }], ["STATUS", "MESSAGES", "TEXT_ROWS", "LOCALES", "VALIDATION_ISSUES",
         "SOURCE_MUTATION_AUTHORIZED", "SOURCE_FILES_MUTATED", "SOURCE_BACKUP_ROWS",
         "PROVIDER_ACTIVE_PATH_RESOLVER_REPAIRED", "BUILD_EXECUTED", "RUNTIME_SMOKE_EXECUTED",
         "NEXT_GATE", "REPORT_TIMESTAMP_UTC"])

    write_csv(reports / "message_catalog_phase22e_3_gate_check_v1.csv", gates, ["GATE", "STATUS", "DETAIL"])
    write_csv(reports / "message_catalog_phase22e_3_source_mutation_inventory_v1.csv", mutation_rows,
              ["TARGET_PATH", "ACTION", "BYTES", "SHA256", "DETAIL"])
    write_csv(reports / "message_catalog_phase22e_3_source_backup_inventory_v1.csv", backup_rows,
              ["TARGET_PATH", "BACKUP_PATH", "BYTES", "SHA256", "ROLE"])

    boundary = [
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 1, "OBSERVED_MUTATION": len(mutation_rows), "DETAIL": "Authorized source mutation limited to src/help/message_catalog.cpp provider path resolver."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_DBF_CATALOG", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_CDX_INDEXES", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active CDX/index mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active LMDB mutation."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No HELP DATA mutation."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CMDHELPCHK mutation."},
        {"PROTECTED_SYSTEM": "MANUALGEN", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No manualgen mutation."},
        {"PROTECTED_SYSTEM": "DATADICT_SELF_DOC", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No Data Dictionary/SelfDoc mutation."},
    ]
    write_csv(reports / "message_catalog_phase22e_3_boundary_ledger_v1.csv", boundary,
              ["PROTECTED_SYSTEM", "MUTATION_ALLOWED", "OBSERVED_MUTATION", "DETAIL"])

    print(status)
    print(f"  messages: {messages}")
    print(f"  text rows: {text_rows}")
    print(f"  locales: {locales.replace(';', ', ')}")
    print(f"  validation issues: {validation_issues}")
    print(f"  source mutation authorized: {1 if args.allow_source_mutation else 0}")
    print(f"  source files mutated: {len(mutation_rows)}")
    print(f"  source backup rows: {len(backup_rows)}")
    print("  build executed: 0")
    print("  runtime smoke executed: 0")
    print(f"  next gate: {NEXT_GATE}")
    print(f"  reports: {reports}")
    return 0 if status == STATUS_GREEN else 2

if __name__ == "__main__":
    raise SystemExit(main())
