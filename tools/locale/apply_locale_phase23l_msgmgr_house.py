#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

STATUS_APPLIED = "LOCALE_PHASE23L_MSGMGR_HOUSE_COMMAND_SOURCE_PATCH_APPLIED_BUILD_HELD"
STATUS_BLOCKED = "LOCALE_PHASE23L_MSGMGR_HOUSE_COMMAND_SOURCE_PATCH_BLOCKED"
NEXT_GATE = "BUILD_AND_RUN_MSGMGR_HOUSE_COMMAND_SMOKE_THEN_VALIDATE"
LOCALE_REPORT_DIR = Path("docs/locale/reports")
BACKUP_ROOT = Path("docs/locale/backups")

CMD_REL = Path("src/cli/cmd_msgmgr.cpp")
CMAKE_CANDIDATES = [Path("src/cli/CMakeLists.txt"), Path("src/CMakeLists.txt"), Path("CMakeLists.txt")]
REGISTRY_CANDIDATES = [Path("src/cli/command_registry.cpp"), Path("src/cli/shell.cpp"), Path("src/shell.cpp")]
SMOKE_REL = Path("docs/locale/scripts/LOCALE_PHASE23L_MSGMGR_HOUSE_SMOKE.dts")

CMD_TEXT = '// src/cli/cmd_msgmgr.cpp\n// @dottalk.usage v1\n// owner: DOT|MSGMGR\n// command: MSGMGR\n// category: messaging\n// status: supported\n// noargs: usage\n// effect: report\n// mutates: no\n// usage-access: MSGMGR USAGE\n// summary:\n//   Message Manager command house for runtime messaging and locale-spine\n//   inspection surfaces.\n//\n// usage:\n//   MSGMGR\n//   MSGMGR USAGE\n//   MSGMGR STATUS\n//   MSGMGR CHECK\n//\n// notes:\n//   MSGMGR is the command house for Messaging manager surfaces.\n//   This first house registration is intentionally read-only.\n//   STATUS and CHECK report that the command house is registered and that\n//   runtime Messaging catalog checks remain owned by SET MESSAGE CATALOG\n//   until later guarded wiring phases.\n//   MSGMGR does not mutate DBF, CDX, LMDB, HELP DATA, CMDHELPCHK, manualgen,\n//   Data Dictionary, SelfDoc, or source-derived catalogs.\n//\n// related:\n//   SET MESSAGE CATALOG CHECK\n//   SET MESSAGE CATALOG GET\n//   SET LANGUAGE\n//   DDICT\n//\n\n#include <algorithm>\n#include <cctype>\n#include <iostream>\n#include <sstream>\n#include <string>\n\n#include "xbase.hpp"\n\nnamespace {\n\nstatic std::string msgmgr_upper(std::string s)\n{\n    std::transform(\n        s.begin(), s.end(), s.begin(),\n        [](unsigned char c) { return static_cast<char>(std::toupper(c)); }\n    );\n    return s;\n}\n\nstatic std::string msgmgr_trim(std::string s)\n{\n    auto is_space = [](unsigned char ch) { return std::isspace(ch) != 0; };\n\n    s.erase(\n        s.begin(),\n        std::find_if(s.begin(), s.end(), [&](unsigned char c) { return !is_space(c); })\n    );\n\n    s.erase(\n        std::find_if(s.rbegin(), s.rend(), [&](unsigned char c) { return !is_space(c); }).base(),\n        s.end()\n    );\n\n    return s;\n}\n\nstatic void print_msgmgr_usage()\n{\n    std::cout\n        << "Usage:\\n"\n        << "  MSGMGR                 (Show this usage)\\n"\n        << "  MSGMGR USAGE           (Show this usage)\\n"\n        << "  MSGMGR STATUS          (Report Message Manager command-house status)\\n"\n        << "  MSGMGR CHECK           (Read-only command-house check)\\n"\n        << "Notes:\\n"\n        << "  - MSGMGR is read-only in this phase.\\n"\n        << "  - Runtime message catalog proof remains available through SET MESSAGE CATALOG CHECK.\\n"\n        << "  - Locale-spine runtime wiring remains guarded for a later phase.\\n";\n}\n\nstatic void print_msgmgr_status()\n{\n    std::cout\n        << "MSGMGR STATUS\\n"\n        << "  command house        : registered\\n"\n        << "  read mode            : read-only\\n"\n        << "  active message check : SET MESSAGE CATALOG CHECK\\n"\n        << "  active message get   : SET MESSAGE CATALOG GET\\n"\n        << "  locale spine         : scaffold present; runtime status wiring held\\n"\n        << "  boundary             : no DBF/CDX/LMDB mutation; no runtime writeback\\n";\n}\n\n} // anonymous namespace\n\nvoid cmd_MSGMGR(xbase::DbArea& area, std::istringstream& args)\n{\n    (void)area;\n\n    std::string sub;\n    args >> sub;\n    sub = msgmgr_upper(msgmgr_trim(sub));\n\n    if (sub.empty() || sub == "USAGE" || sub == "HELP" || sub == "?" ||\n        sub == "/?" || sub == "-H" || sub == "--HELP") {\n        print_msgmgr_usage();\n        return;\n    }\n\n    if (sub == "STATUS" || sub == "CHECK") {\n        print_msgmgr_status();\n        return;\n    }\n\n    std::cout << "MSGMGR: unknown subcommand \'" << sub << "\'.\\n";\n    print_msgmgr_usage();\n}\n'
SMOKE_TEXT = '* LOCALE_PHASE23L_MSGMGR_HOUSE_SMOKE.dts\n* MSGMGR command-house smoke.\n* Boundary: read-only command-house registration proof.\n\nMSGMGR STATUS\nMSGMGR CHECK\n\n'

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

def rel(path: Path | None, repo: Path) -> str:
    if path is None:
        return ""
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
    rows.append({"SOURCE_PATH": rel(path, repo), "BACKUP_PATH": rel(target, repo), "BYTES": target.stat().st_size, "SHA256": sha256_file(target), "ACTION": "BACKUP_EXISTING_FILE"})

def write_managed_file(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")

def find_registry(repo: Path) -> Path | None:
    for relp in REGISTRY_CANDIDATES:
        p = repo / relp
        if p.exists():
            text = p.read_text(encoding="utf-8", errors="replace")
            if "cmd_DDICT" in text or "cmd_DDL" in text or "cmd_AREA" in text:
                return p
    src = repo / "src"
    if src.exists():
        for p in src.rglob("*.cpp"):
            name = p.name.lower()
            if "command" not in name and "shell" not in name and "registry" not in name:
                continue
            text = p.read_text(encoding="utf-8", errors="replace")
            if ("cmd_DDICT" in text or "cmd_DDL" in text or "cmd_AREA" in text) and "[" in text and "]" in text:
                return p
    return None

def clone_declaration(text: str) -> tuple[str, str]:
    if re.search(r"\bcmd_MSGMGR\b", text):
        return text, "already_present"
    for anchor in ["cmd_DDICT", "cmd_DDL", "cmd_AREA"]:
        m = re.search(r"(?m)^(.*\b(?:extern\s+)?void\s+" + anchor + r"\s*\([^;{]*\)\s*;.*)$", text)
        if m:
            line = m.group(1)
            new_line = line.replace(anchor, "cmd_MSGMGR")
            return text[:m.end()] + "\n" + new_line + text[m.end():], f"declaration_after_{anchor}"
    return text, "declaration_anchor_missing"

def clone_registration_block(text: str) -> tuple[str, str]:
    if re.search(r"\bMSGMGR\b", text) and "cmd_MSGMGR" in text:
        return text, "already_present"
    lines = text.splitlines(keepends=True)
    for anchor in ["DDICT", "DDL", "AREA"]:
        for i, line in enumerate(lines):
            if anchor in line and f"cmd_{anchor}" in line and "[" in line:
                j = i
                while j < min(len(lines), i + 12):
                    if ";" in lines[j]:
                        block = "".join(lines[i:j+1])
                        new_block = block.replace(anchor, "MSGMGR").replace(f"cmd_{anchor}", "cmd_MSGMGR")
                        return "".join(lines[:j+1] + [new_block] + lines[j+1:]), f"lambda_registration_after_{anchor}"
                    j += 1
            if anchor in line and f"cmd_{anchor}" in line:
                if "register" in line.lower() or "add" in line.lower() or "emplace" in line.lower() or "{" in line:
                    new_line = line.replace(anchor, "MSGMGR").replace(f"cmd_{anchor}", "cmd_MSGMGR")
                    return "".join(lines[:i+1] + [new_line] + lines[i+1:]), f"registration_after_{anchor}"
    return text, "registration_anchor_missing"

def patch_registry(text: str) -> tuple[str, str, str]:
    after_decl, decl_status = clone_declaration(text)
    after_reg, reg_status = clone_registration_block(after_decl)
    return after_reg, decl_status, reg_status

def patch_cmake_text(original: str) -> tuple[str, str]:
    if "cmd_msgmgr.cpp" in original:
        return original, "already_present"
    for anchor in ["cmd_ddict.cpp", "cmd_ddl.cpp", "cmd_area.cpp"]:
        idx = original.find(anchor)
        if idx >= 0:
            line_start = original.rfind("\n", 0, idx) + 1
            line_end = original.find("\n", idx)
            if line_end < 0:
                line_end = len(original)
            line = original[line_start:line_end]
            indent = line[:len(line) - len(line.lstrip())]
            insert = indent + "cmd_msgmgr.cpp"
            if line.strip().endswith(","):
                insert += ","
            return original[:line_end] + "\n" + insert + original[line_end:], f"inserted_after_{anchor}"
    if "GLOB" in original.upper() and "*.cpp" in original:
        return original, "glob_detected_no_cmake_mutation"
    return original, "anchor_missing_no_cmake_mutation"

def patch_cmake(repo: Path) -> tuple[Path | None, str, bool]:
    for relp in CMAKE_CANDIDATES:
        p = repo / relp
        if not p.exists():
            continue
        original = p.read_text(encoding="utf-8", errors="replace")
        patched, status = patch_cmake_text(original)
        if patched != original:
            p.write_text(patched, encoding="utf-8", newline="\n")
            return p, status, True
        if status in ("already_present", "glob_detected_no_cmake_mutation"):
            return p, status, False
    return None, "cmake_not_found", False

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--allow-source-mutation", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    reports = repo / LOCALE_REPORT_DIR
    reports.mkdir(parents=True, exist_ok=True)

    phase23k = first_row(reports / "locale_phase23k_status_summary_v1.csv")

    gates: list[dict[str, Any]] = []
    failures = 0
    def gate(name: str, ok: bool, detail: str) -> None:
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": detail})
        if not ok:
            failures += 1

    gate("OPERATOR_ALLOWED_SOURCE_MUTATION", args.allow_source_mutation, "requires --allow-source-mutation")
    gate("PHASE23K_BUILD_SMOKE_GREEN", phase23k.get("STATUS") == "LOCALE_PHASE23K_MESSAGING_LOCALE_SPINE_SOURCE_SCAFFOLD_BUILD_SMOKE_GREEN", phase23k.get("STATUS", ""))
    gate("PHASE23K_VALIDATION_ZERO", phase23k.get("VALIDATION_ISSUES", "") == "0", f"validation_issues={phase23k.get('VALIDATION_ISSUES', '')}")

    registry = find_registry(repo)
    gate("REGISTRY_FILE_FOUND", registry is not None, rel(registry, repo) if registry else "no registry/shell file with command anchors found")

    cmd_path = repo / CMD_REL
    smoke_path = repo / SMOKE_REL

    if cmd_path.exists():
        existing = cmd_path.read_text(encoding="utf-8", errors="replace")
        gate("CMD_MSGMGR_SAFE_TO_REPLACE", "@dottalk.usage v1" in existing and "cmd_MSGMGR" in existing, "existing cmd_msgmgr.cpp must be managed/compatible")

    status = STATUS_BLOCKED
    mutation_rows: list[dict[str, Any]] = []
    backup_rows: list[dict[str, Any]] = []
    registry_status = "not_attempted"
    decl_status = "not_attempted"
    cmake_status = "not_attempted"

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup_root = repo / BACKUP_ROOT / f"LOC-023L_MSGMGR_HOUSE_BACKUP_{timestamp}"

    if failures == 0:
        assert registry is not None
        backup_file(cmd_path, backup_root, repo, backup_rows)
        backup_file(registry, backup_root, repo, backup_rows)
        for relp in CMAKE_CANDIDATES:
            p = repo / relp
            if p.exists():
                backup_file(p, backup_root, repo, backup_rows)
                break
        backup_file(smoke_path, backup_root, repo, backup_rows)

        write_managed_file(cmd_path, CMD_TEXT)
        mutation_rows.append({"TARGET_PATH": rel(cmd_path, repo), "ACTION": "CREATE_OR_REPLACE_CMD_MSGMGR", "BYTES": cmd_path.stat().st_size, "SHA256": sha256_file(cmd_path)})

        reg_original = registry.read_text(encoding="utf-8", errors="replace")
        reg_patched, decl_status, registry_status = patch_registry(reg_original)
        if registry_status == "registration_anchor_missing":
            write_csv(reports / "locale_phase23l_msgmgr_registration_blocker_v1.csv", [{
                "REGISTRY_PATH": rel(registry, repo),
                "DECL_STATUS": decl_status,
                "REGISTRATION_STATUS": registry_status,
                "DETAIL": "Could not find lambda/registration anchor for MSGMGR; no registry mutation applied."
            }], ["REGISTRY_PATH", "DECL_STATUS", "REGISTRATION_STATUS", "DETAIL"])
            if not (backup_root / rel(cmd_path, repo)).exists() and cmd_path.exists():
                cmd_path.unlink()
            failures += 1
        else:
            if reg_patched != reg_original:
                registry.write_text(reg_patched, encoding="utf-8", newline="\n")
                mutation_rows.append({"TARGET_PATH": rel(registry, repo), "ACTION": f"UPDATE_REGISTRY_{decl_status}_{registry_status}", "BYTES": registry.stat().st_size, "SHA256": sha256_file(registry)})
            cmake_path, cmake_status, cmake_mutated = patch_cmake(repo)
            if cmake_mutated and cmake_path is not None:
                mutation_rows.append({"TARGET_PATH": rel(cmake_path, repo), "ACTION": f"UPDATE_CMAKE_{cmake_status}", "BYTES": cmake_path.stat().st_size, "SHA256": sha256_file(cmake_path)})
            write_managed_file(smoke_path, SMOKE_TEXT)
            mutation_rows.append({"TARGET_PATH": rel(smoke_path, repo), "ACTION": "CREATE_OR_REPLACE_MSGMGR_SMOKE", "BYTES": smoke_path.stat().st_size, "SHA256": sha256_file(smoke_path)})
            status = STATUS_APPLIED

    validation_issues = "0" if status == STATUS_APPLIED else str(failures)
    boundary = [
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 1, "OBSERVED_MUTATION": len([r for r in mutation_rows if r["TARGET_PATH"].startswith("src/")]), "DETAIL": "Authorized narrow MSGMGR command-house source patch."},
        {"PROTECTED_SYSTEM": "DOCS_LOCALE_SCRIPT", "MUTATION_ALLOWED": 1, "OBSERVED_MUTATION": len([r for r in mutation_rows if r["TARGET_PATH"].startswith("docs/")]), "DETAIL": "Runtime smoke script staged."},
        {"PROTECTED_SYSTEM": "BUILD", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No build executed by apply package."},
        {"PROTECTED_SYSTEM": "RUNTIME_BEHAVIOR", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Runtime behavior not proven until build/smoke."},
        {"PROTECTED_SYSTEM": "ACTIVE_LOCALE_SPINE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active locale DBF/CDX/LMDB mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_DBF_CATALOG", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active Messaging catalog mutation."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No HELP DATA mutation."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CMDHELPCHK mutation."},
        {"PROTECTED_SYSTEM": "MANUALGEN", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No manualgen mutation."},
        {"PROTECTED_SYSTEM": "DATADICT_SELF_DOC", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No Data Dictionary/SelfDoc mutation."},
    ]

    write_csv(reports / "locale_phase23l_msgmgr_apply_status_summary_v1.csv", [{
        "STATUS": status,
        "VALIDATION_ISSUES": validation_issues,
        "SOURCE_MUTATION_AUTHORIZED": 1 if args.allow_source_mutation else 0,
        "SOURCE_FILES_MUTATED": len([r for r in mutation_rows if r["TARGET_PATH"].startswith("src/")]),
        "DOCS_LOCALE_FILES_MUTATED": len([r for r in mutation_rows if r["TARGET_PATH"].startswith("docs/")]),
        "BACKUP_ROWS": len(backup_rows),
        "REGISTRY_PATH": rel(registry, repo) if registry else "",
        "DECLARATION_STATUS": decl_status,
        "REGISTRATION_STATUS": registry_status,
        "CMAKE_STATUS": cmake_status,
        "BUILD_EXECUTED": 0,
        "RUNTIME_SMOKE_EXECUTED": 0,
        "NEXT_GATE": NEXT_GATE,
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }], ["STATUS","VALIDATION_ISSUES","SOURCE_MUTATION_AUTHORIZED","SOURCE_FILES_MUTATED","DOCS_LOCALE_FILES_MUTATED","BACKUP_ROWS","REGISTRY_PATH","DECLARATION_STATUS","REGISTRATION_STATUS","CMAKE_STATUS","BUILD_EXECUTED","RUNTIME_SMOKE_EXECUTED","NEXT_GATE","REPORT_TIMESTAMP_UTC"])
    write_csv(reports / "locale_phase23l_msgmgr_apply_gate_check_v1.csv", gates, ["GATE", "STATUS", "DETAIL"])
    write_csv(reports / "locale_phase23l_msgmgr_source_mutation_inventory_v1.csv", mutation_rows, ["TARGET_PATH", "ACTION", "BYTES", "SHA256"])
    write_csv(reports / "locale_phase23l_msgmgr_source_backup_inventory_v1.csv", backup_rows, ["SOURCE_PATH", "BACKUP_PATH", "BYTES", "SHA256", "ACTION"])
    write_csv(reports / "locale_phase23l_msgmgr_boundary_ledger_v1.csv", boundary, ["PROTECTED_SYSTEM", "MUTATION_ALLOWED", "OBSERVED_MUTATION", "DETAIL"])

    print(status)
    print(f"  validation issues: {validation_issues}")
    print(f"  source mutation authorized: {1 if args.allow_source_mutation else 0}")
    print(f"  source files mutated: {len([r for r in mutation_rows if r['TARGET_PATH'].startswith('src/')])}")
    print(f"  docs locale files mutated: {len([r for r in mutation_rows if r['TARGET_PATH'].startswith('docs/')])}")
    print(f"  backup rows: {len(backup_rows)}")
    print(f"  registry path: {rel(registry, repo) if registry else ''}")
    print(f"  declaration status: {decl_status}")
    print(f"  registration status: {registry_status}")
    print(f"  cmake status: {cmake_status}")
    print("  build executed: 0")
    print("  runtime smoke executed: 0")
    print(f"  next gate: {NEXT_GATE}")
    print(f"  reports: {reports}")
    return 0 if status == STATUS_APPLIED else 2

if __name__ == "__main__":
    raise SystemExit(main())
