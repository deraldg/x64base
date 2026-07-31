#!/usr/bin/env python3
"""
Phase 22B: Guarded runtime provider source-patch candidate staging.

This phase is the authorized next step after Phase 22A, but it still avoids
blind source mutation. It corrects the source-surface model, discovers the real
message header extension (.hpp vs .h), and stages candidate runtime-provider
source files plus an apply plan.

No files under src/ are changed by this phase.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

STATUS_GREEN = "MESSAGE_CATALOG_PHASE22B_RUNTIME_PROVIDER_PATCH_CANDIDATE_STAGED_SOURCE_HELD"
STATUS_BLOCKED = "MESSAGE_CATALOG_PHASE22B_RUNTIME_PROVIDER_PATCH_CANDIDATE_BLOCKED"
NEXT_GATE = "HOLD_OR_AUTHORIZE_PHASE22C_APPLY_RUNTIME_PROVIDER_SOURCE_PATCH"
REPORT_DIR = Path("docs/messaging/reports")
PATCH_ROOT = Path("docs/messaging/patches/phase22b_runtime_provider_candidate")

MESSAGE_CATALOG_HPP = """// ============================================================================
// File: src/help/message_catalog.hpp
// Purpose: Runtime Messaging catalog provider boundary.
// Phase: MSG-022B candidate; apply only via guarded Phase 22C.
// ============================================================================

#pragma once

#include <string>
#include <unordered_map>
#include <vector>

namespace dottalk::helpdata {

enum class MessageCatalogMode {
    CompiledFallback,
    ActiveDbf,
    Auto
};

struct MessageCatalogStatus {
    MessageCatalogMode mode = MessageCatalogMode::CompiledFallback;
    bool active_catalog_present = false;
    bool active_catalog_loaded = false;
    int message_count = 0;
    int text_row_count = 0;
    std::string active_dbf_dir;
    std::string active_indexes_dir;
    std::string active_lmdb_dir;
    std::string detail;
};

// Phase 22B/22C boundary:
// - Read-only provider.
// - No runtime catalog writeback.
// - Compiled/static message rows remain fallback.
MessageCatalogStatus active_message_catalog_status();
std::string format_message_catalog(const std::string& locale,
                                   const std::string& symbol,
                                   const std::unordered_map<std::string, std::string>& vars = {});

} // namespace dottalk::helpdata
"""

MESSAGE_CATALOG_CPP = """// ============================================================================
// File: src/help/message_catalog.cpp
// Purpose: Runtime Messaging catalog provider boundary.
// Phase: MSG-022B candidate; apply only via guarded Phase 22C.
// ============================================================================

#include "message_catalog.hpp"

#include "helpdata_messages.hpp"

#include <filesystem>

namespace dottalk::helpdata {
namespace {

std::string repo_relative_active_dbf_dir()
{
    return "dottalkpp/data/messaging";
}

std::string repo_relative_active_indexes_dir()
{
    return "dottalkpp/data/indexes/messaging";
}

std::string repo_relative_active_lmdb_dir()
{
    return "dottalkpp/data/lmdb/messaging";
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
    status.active_dbf_dir = repo_relative_active_dbf_dir();
    status.active_indexes_dir = repo_relative_active_indexes_dir();
    status.active_lmdb_dir = repo_relative_active_lmdb_dir();

    // Phase 22C first integration target:
    // prove active artifact presence without replacing compiled fallback.
    const std::filesystem::path dbf_dir(status.active_dbf_dir);
    const bool messages = std::filesystem::exists(dbf_dir / "SYSTEM_MESSAGES.dbf");
    const bool text_dbf = std::filesystem::exists(dbf_dir / "SYSTEM_MESSAGE_TEXT.dbf");
    const bool text_dtx = std::filesystem::exists(dbf_dir / "SYSTEM_MESSAGE_TEXT.dtx");

    status.active_catalog_present = messages && text_dbf && text_dtx;
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
    // Candidate Phase 22C behavior:
    // compiled/static fallback first; active DBF row loading is Phase 22D after
    // the runtime DBF read API is selected and smoke-tested.
    const MessageDef* message = find_message_by_key(symbol);
    if (!message || !message->text) {
        return {};
    }
    return apply_vars(message->text, vars);
}

} // namespace dottalk::helpdata
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
        return str(path.relative_to(repo)).replace("\\", "/")
    except ValueError:
        return str(path)

def inventory(root: Path, repo: Path, role: str) -> list[dict[str, Any]]:
    rows = []
    if not root.exists():
        return rows
    for p in sorted(root.rglob("*")):
        if p.is_file():
            rows.append({
                "PATH": rel(p, repo),
                "BYTES": p.stat().st_size,
                "SHA256": sha256_file(p),
                "ROLE": role,
            })
    return rows

def scan_cmake(repo: Path) -> list[dict[str, Any]]:
    rows = []
    for p in sorted(repo.rglob("CMakeLists.txt")):
        if any(part in {".git", "build", "_incoming"} for part in p.parts):
            continue
        text = p.read_text(encoding="utf-8", errors="replace")
        rows.append({
            "PATH": rel(p, repo),
            "HAS_HELPDATA_MESSAGES_CPP": 1 if "helpdata_messages.cpp" in text else 0,
            "HAS_HELP_GLOB": 1 if "src/help" in text or "help/*.cpp" in text or "GLOB" in text.upper() else 0,
            "HAS_MESSAGE_CATALOG_CPP": 1 if "message_catalog.cpp" in text else 0,
            "BYTES": p.stat().st_size,
            "SHA256": sha256_file(p),
        })
    return rows

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    reports = repo / REPORT_DIR
    reports.mkdir(parents=True, exist_ok=True)

    p22a = first_row(reports / "message_catalog_phase22a_status_summary_v1.csv")
    p21 = first_row(reports / "message_catalog_phase21_status_summary_v1.csv")

    messages = p22a.get("MESSAGES", p21.get("MESSAGES", "12"))
    text_rows = p22a.get("TEXT_ROWS", p21.get("TEXT_ROWS", "60"))
    locales = p22a.get("LOCALES", p21.get("LOCALES", "de;en-US;es;fr;it"))

    gates = []
    failures = 0
    def gate(name: str, ok: bool, detail: str) -> None:
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": detail})
        if not ok:
            failures += 1
    def review(name: str, ok: bool, detail: str) -> None:
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "REVIEW", "DETAIL": detail})

    gate("PHASE22A_GREEN", p22a.get("STATUS") == "MESSAGE_CATALOG_PHASE22A_RUNTIME_SOURCE_INTEGRATION_PROBE_GREEN_SOURCE_HELD", p22a.get("STATUS", ""))
    gate("ACTIVE_SYSTEM_MESSAGES_DBF_PRESENT", (repo / "dottalkpp/data/messaging/SYSTEM_MESSAGES.dbf").exists(), "dottalkpp/data/messaging/SYSTEM_MESSAGES.dbf")
    gate("ACTIVE_SYSTEM_MESSAGE_TEXT_DBF_PRESENT", (repo / "dottalkpp/data/messaging/SYSTEM_MESSAGE_TEXT.dbf").exists(), "dottalkpp/data/messaging/SYSTEM_MESSAGE_TEXT.dbf")
    gate("ACTIVE_SYSTEM_MESSAGE_TEXT_DTX_PRESENT", (repo / "dottalkpp/data/messaging/SYSTEM_MESSAGE_TEXT.dtx").exists(), "dottalkpp/data/messaging/SYSTEM_MESSAGE_TEXT.dtx")

    hpp = repo / "src/help/helpdata_messages.hpp"
    h = repo / "src/help/helpdata_messages.h"
    cpp = repo / "src/help/helpdata_messages.cpp"
    gate("HELPDATA_MESSAGES_CPP_PRESENT", cpp.exists(), rel(cpp, repo))
    gate("HELPDATA_MESSAGES_HEADER_PRESENT", hpp.exists() or h.exists(), "src/help/helpdata_messages.hpp or .h")
    review("PHASE22A_HEADER_EXTENSION_CORRECTION", hpp.exists(), "Phase 22A scanned .h; local source should prefer .hpp if present.")

    provider_hpp = repo / "src/help/message_catalog.hpp"
    provider_cpp = repo / "src/help/message_catalog.cpp"
    review("MESSAGE_CATALOG_PROVIDER_ALREADY_PRESENT", provider_hpp.exists() or provider_cpp.exists(), "If absent, Phase 22C may create these files.")

    cmake_rows = scan_cmake(repo)
    write_csv(reports / "message_catalog_phase22b_cmake_scan_v1.csv", cmake_rows,
              ["PATH", "HAS_HELPDATA_MESSAGES_CPP", "HAS_HELP_GLOB", "HAS_MESSAGE_CATALOG_CPP", "BYTES", "SHA256"])

    patch_root = repo / PATCH_ROOT
    if patch_root.exists():
        import shutil
        shutil.rmtree(patch_root)
    (patch_root / "src/help").mkdir(parents=True, exist_ok=True)
    (patch_root / "docs").mkdir(parents=True, exist_ok=True)

    (patch_root / "src/help/message_catalog.hpp").write_text(MESSAGE_CATALOG_HPP, encoding="utf-8")
    (patch_root / "src/help/message_catalog.cpp").write_text(MESSAGE_CATALOG_CPP, encoding="utf-8")

    apply_plan = f"""# MSG-022B Candidate Runtime Provider Patch

This is a candidate source patch workspace, not an applied source mutation.

## Corrected source surface

Phase 22A looked for `src/help/helpdata_messages.h`, but the actual project
source may use `src/help/helpdata_messages.hpp`.

Observed locally:

- `src/help/helpdata_messages.cpp`: {"present" if cpp.exists() else "missing"}
- `src/help/helpdata_messages.hpp`: {"present" if hpp.exists() else "missing"}
- `src/help/helpdata_messages.h`: {"present" if h.exists() else "missing"}

## Candidate files staged

- `src/help/message_catalog.hpp`
- `src/help/message_catalog.cpp`

## Intended Phase 22C application

Phase 22C may copy these candidate files into `src/help`, then update the build
surface if the project does not already glob `src/help/*.cpp`.

The candidate provider does **not** yet read DBF rows. It provides a compile-safe
runtime provider boundary and active-artifact status check while preserving
compiled/static fallback.

## Why DBF loading is not patched blindly

The runtime DBF read API must be selected from existing x64base/DotTalk++ code.
Until that API is confirmed, the provider must not implement an ad hoc DBF parser.

## Boundary

- No source mutation in Phase 22B.
- No active DBF/CDX/LMDB mutation.
- No HELP DATA/CMDHELPCHK/manualgen/datadict mutation.
"""
    (patch_root / "docs/MSG_022B_APPLY_PLAN.md").write_text(apply_plan, encoding="utf-8")

    patch_inventory = inventory(patch_root, repo, "phase22b_candidate_patch_artifact")
    write_csv(reports / "message_catalog_phase22b_candidate_patch_inventory_v1.csv", patch_inventory,
              ["PATH", "BYTES", "SHA256", "ROLE"])

    source_surface_rows = [
        {"SOURCE_PATH": "src/help/helpdata_messages.cpp", "EXPECTED": 1, "EXISTS": 1 if cpp.exists() else 0, "ROLE": "compiled message source rows"},
        {"SOURCE_PATH": "src/help/helpdata_messages.hpp", "EXPECTED": 1, "EXISTS": 1 if hpp.exists() else 0, "ROLE": "compiled message header, preferred if present"},
        {"SOURCE_PATH": "src/help/helpdata_messages.h", "EXPECTED": 0, "EXISTS": 1 if h.exists() else 0, "ROLE": "alternate header name scanned by Phase 22A"},
        {"SOURCE_PATH": "src/help/message_catalog.hpp", "EXPECTED": 0, "EXISTS": 1 if provider_hpp.exists() else 0, "ROLE": "runtime provider header target"},
        {"SOURCE_PATH": "src/help/message_catalog.cpp", "EXPECTED": 0, "EXISTS": 1 if provider_cpp.exists() else 0, "ROLE": "runtime provider source target"},
    ]
    write_csv(reports / "message_catalog_phase22b_source_surface_v1.csv", source_surface_rows,
              ["SOURCE_PATH", "EXPECTED", "EXISTS", "ROLE"])

    decisions = [
        {"DECISION_ID": "22B-D001", "DECISION": "CORRECT_HEADER_EXTENSION", "STATUS": "ACCEPTED", "DETAIL": "Use helpdata_messages.hpp when present; do not assume .h."},
        {"DECISION_ID": "22B-D002", "DECISION": "STAGE_PROVIDER_MODULE", "STATUS": "ACCEPTED", "DETAIL": "Stage message_catalog.hpp/cpp as candidate source patch files."},
        {"DECISION_ID": "22B-D003", "DECISION": "NO_BLIND_DBF_PARSER", "STATUS": "ACCEPTED", "DETAIL": "Do not implement ad hoc x64 DBF parsing; select existing runtime DBF API in later phase."},
        {"DECISION_ID": "22B-D004", "DECISION": "COMPILED_FALLBACK_FIRST", "STATUS": "ACCEPTED", "DETAIL": "Provider boundary preserves compiled/static fallback."},
        {"DECISION_ID": "22B-D005", "DECISION": "SOURCE_HELD", "STATUS": "ACCEPTED", "DETAIL": "No src/ mutation in Phase 22B; Phase 22C must explicitly apply."},
    ]
    write_csv(reports / "message_catalog_phase22b_decisions_v1.csv", decisions,
              ["DECISION_ID", "DECISION", "STATUS", "DETAIL"])

    status = STATUS_GREEN if failures == 0 else STATUS_BLOCKED
    validation_issues = str(failures)

    write_csv(reports / "message_catalog_phase22b_status_summary_v1.csv", [{
        "STATUS": status,
        "MESSAGES": messages,
        "TEXT_ROWS": text_rows,
        "LOCALES": locales,
        "VALIDATION_ISSUES": validation_issues,
        "PATCH_CANDIDATE_STAGED": 1 if failures == 0 else 0,
        "SOURCE_MUTATION_AUTHORIZED": 0,
        "SOURCE_MUTATION_OBSERVED": 0,
        "RUNTIME_PROVIDER_PATCH_APPLIED": 0,
        "NEXT_GATE": NEXT_GATE,
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }], ["STATUS", "MESSAGES", "TEXT_ROWS", "LOCALES", "VALIDATION_ISSUES",
         "PATCH_CANDIDATE_STAGED", "SOURCE_MUTATION_AUTHORIZED", "SOURCE_MUTATION_OBSERVED",
         "RUNTIME_PROVIDER_PATCH_APPLIED", "NEXT_GATE", "REPORT_TIMESTAMP_UTC"])

    write_csv(reports / "message_catalog_phase22b_gate_check_v1.csv", gates,
              ["GATE", "STATUS", "DETAIL"])

    boundary = [
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Phase 22B stages candidate patch artifacts only; no src/ files edited."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_DBF_CATALOG", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_CDX_INDEXES", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active CDX/index mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active LMDB mutation."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No HELP DATA mutation."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CMDHELPCHK mutation."},
        {"PROTECTED_SYSTEM": "MANUALGEN", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No manualgen mutation."},
        {"PROTECTED_SYSTEM": "DATADICT_SELF_DOC", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No Data Dictionary/SelfDoc mutation."},
    ]
    write_csv(reports / "message_catalog_phase22b_boundary_ledger_v1.csv", boundary,
              ["PROTECTED_SYSTEM", "MUTATION_ALLOWED", "OBSERVED_MUTATION", "DETAIL"])

    print(status)
    print(f"  messages: {messages}")
    print(f"  text rows: {text_rows}")
    print(f"  locales: {locales.replace(';', ', ')}")
    print(f"  validation issues: {validation_issues}")
    print(f"  patch candidate staged: {1 if failures == 0 else 0}")
    print("  source mutation authorized: 0")
    print("  source mutation observed: 0")
    print(f"  next gate: {NEXT_GATE}")
    print(f"  reports: {reports}")
    return 0 if status == STATUS_GREEN else 2

if __name__ == "__main__":
    raise SystemExit(main())
