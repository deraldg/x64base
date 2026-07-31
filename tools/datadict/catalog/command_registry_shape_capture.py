#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import datetime as _dt
import json
import re
from pathlib import Path
from typing import Any, Dict, List


EXPECTED_REVIEW_STATUS = "DDICT_LOCAL_PATTERN_REGISTRATION_BUILD_PATCH_REVIEW"


PATTERNS = [
    ("include", r"^\s*#\s*include\s+"),
    ("namespace", r"^\s*namespace\s+"),
    ("using_dbarea", r"\busing\s+xbase::DbArea\b|\bDbArea\b"),
    ("function_def", r"^\s*(?:static\s+)?[A-Za-z_][A-Za-z0-9_:<>&*\s]+\s+[A-Za-z_][A-Za-z0-9_:]*\s*\([^;]*\)\s*\{?"),
    ("lambda", r"\[[^\]]*\]\s*\([^)]*\)\s*\{"),
    ("command_word", r"\b(command|registry|dispatch|handler|verb|token|builtin|entry|route)\b"),
    ("map_vector_array", r"\b(std::)?(map|unordered_map|vector|array)\b"),
    ("emplace_push", r"\b(emplace|insert|push_back|try_emplace|operator\[\])\b"),
    ("if_else_command", r"\bif\s*\(|\belse\b|\bswitch\s*\(|\bcase\b"),
    ("upper_token", r"\bupper\b|\btoupper\b|\btoken\b|\bverb\b|\bcmd\b"),
    ("string_literal", r'"[^"]+"'),
    ("cmd_symbol", r"\bcmd_[A-Za-z0-9_]+\b"),
    ("ddict", r"DDICT|cmd_DDICT|cmd_ddict"),
]


def utc_now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds")


def read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return {}


def write_json(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: List[Dict[str, Any]], fields: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        w.writeheader()
        for row in rows:
            w.writerow({k: row.get(k, "") for k in fields})


def safe_rel(repo: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(repo.resolve()).as_posix()
    except Exception:
        return path.as_posix()


def line_window(lines: List[str], center: int, radius: int = 6) -> str:
    start = max(1, center - radius)
    end = min(len(lines), center + radius)
    out = []
    for lineno in range(start, end + 1):
        out.append(f"{lineno:04d}: {lines[lineno-1]}")
    return "\n".join(out)


def scan_registry(repo: Path, registry_path: Path) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    text = registry_path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    compiled = [(name, re.compile(pattern, re.IGNORECASE)) for name, pattern in PATTERNS]

    hit_rows: List[Dict[str, Any]] = []
    excerpt_rows: List[Dict[str, Any]] = []
    symbol_rows: List[Dict[str, Any]] = []

    for idx, line in enumerate(lines, start=1):
        hits = [name for name, rx in compiled if rx.search(line)]
        if hits:
            hit_rows.append({
                "path": safe_rel(repo, registry_path),
                "line": idx,
                "hits": ",".join(hits),
                "text": line.strip()[:800],
            })

    # Symbol/literal summary
    literals = {}
    cmd_symbols = {}
    identifiers = {}
    for idx, line in enumerate(lines, start=1):
        for m in re.finditer(r'"([^"]+)"', line):
            token = m.group(1)
            literals.setdefault(token, {"kind": "string_literal", "token": token, "count": 0, "first_line": idx})
            literals[token]["count"] += 1
        for m in re.finditer(r"\bcmd_[A-Za-z0-9_]+\b", line):
            token = m.group(0)
            cmd_symbols.setdefault(token, {"kind": "cmd_symbol", "token": token, "count": 0, "first_line": idx})
            cmd_symbols[token]["count"] += 1
        for m in re.finditer(r"\b[A-Za-z_][A-Za-z0-9_]*(?:Command|Handler|Registry|Dispatch|Entry|Table|Map)\b", line):
            token = m.group(0)
            identifiers.setdefault(token, {"kind": "identifier", "token": token, "count": 0, "first_line": idx})
            identifiers[token]["count"] += 1

    symbol_rows = list(literals.values()) + list(cmd_symbols.values()) + list(identifiers.values())
    symbol_rows.sort(key=lambda r: (r["kind"], str(r["token"]).upper()))

    # High-value excerpts around registry words, cmd symbols, literals, and if/switch.
    centers = []
    for row in hit_rows:
        hs = row["hits"]
        if any(k in hs for k in ["command_word", "emplace_push", "cmd_symbol", "if_else_command", "map_vector_array", "ddict"]):
            centers.append(int(row["line"]))
    # Deduplicate nearby centers.
    selected = []
    for c in sorted(centers):
        if not selected or c - selected[-1] > 8:
            selected.append(c)
    for n, c in enumerate(selected[:40], start=1):
        excerpt_rows.append({
            "excerpt_id": f"EX{n:03d}",
            "path": safe_rel(repo, registry_path),
            "center_line": c,
            "excerpt": line_window(lines, c, radius=7),
        })

    return hit_rows, symbol_rows, excerpt_rows


def scan_cmake(repo: Path, cmake_path: Path) -> List[Dict[str, Any]]:
    if not cmake_path.exists():
        return []
    lines = cmake_path.read_text(encoding="utf-8", errors="replace").splitlines()
    rows = []
    for idx, line in enumerate(lines, start=1):
        ll = line.lower()
        reason = []
        if "glob" in ll:
            reason.append("glob")
        if "*.cpp" in ll or ".cpp" in ll:
            reason.append("cpp")
        if "cli" in ll:
            reason.append("cli")
        if "target_sources" in ll or "add_executable" in ll or "add_library" in ll:
            reason.append("target")
        if "cmd_ddict" in ll:
            reason.append("ddict")
        if reason:
            rows.append({
                "path": safe_rel(repo, cmake_path),
                "line": idx,
                "reason": ",".join(reason),
                "text": line.strip()[:800],
            })
    return rows


def main() -> int:
    ap = argparse.ArgumentParser(description="DD-067S report-only command registry shape capture")
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--run-id", default="DD067S-command-registry-shape-capture-v0")
    ap.add_argument("--dd067r-dir", default="docs/datadict/reports/DD067R-local-pattern-ddict-registration-build-patch-v0")
    ap.add_argument("--registry-path", default="src/cli/command_registry.cpp")
    ap.add_argument("--cmake-path", default="src/CMakeLists.txt")
    ap.add_argument("--profile", action="append", default=[])
    ap.add_argument("--fail-on-review", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    out = Path(args.out_dir).resolve()
    dd067r_dir = (repo / args.dd067r_dir).resolve()
    registry_path = (repo / args.registry_path).resolve()
    cmake_path = (repo / args.cmake_path).resolve()
    out.mkdir(parents=True, exist_ok=True)

    dd067r_manifest = read_json(dd067r_dir / "dd067r_local_pattern_ddict_registration_build_patch_manifest.json")
    dd067r_review_ok = dd067r_manifest.get("status") == EXPECTED_REVIEW_STATUS
    registry_exists = registry_path.exists()
    cmake_exists = cmake_path.exists()

    failures = 0
    review_rows: List[Dict[str, Any]] = []
    if not dd067r_review_ok:
        review_rows.append({"issue": "DD067R_STATUS_NOT_EXPECTED_REVIEW", "detail": dd067r_manifest.get("status", "")})
    if not registry_exists:
        failures += 1
        review_rows.append({"issue": "REGISTRY_MISSING", "detail": str(registry_path)})
    if not cmake_exists:
        failures += 1
        review_rows.append({"issue": "CMAKE_MISSING", "detail": str(cmake_path)})

    hit_rows: List[Dict[str, Any]] = []
    symbol_rows: List[Dict[str, Any]] = []
    excerpt_rows: List[Dict[str, Any]] = []
    cmake_rows: List[Dict[str, Any]] = []
    if registry_exists:
        hit_rows, symbol_rows, excerpt_rows = scan_registry(repo, registry_path)
    if cmake_exists:
        cmake_rows = scan_cmake(repo, cmake_path)

    string_count = sum(1 for r in symbol_rows if r.get("kind") == "string_literal")
    cmd_symbol_count = sum(1 for r in symbol_rows if r.get("kind") == "cmd_symbol")
    ddict_already = any("DDICT" in str(r.get("token", "")).upper() for r in symbol_rows) or any("DDICT" in str(r.get("text", "")).upper() for r in hit_rows)
    has_registry_words = any("command_word" in r.get("hits", "") for r in hit_rows)
    has_function_defs = any("function_def" in r.get("hits", "") for r in hit_rows)

    gate_rows = [
        {"gate": "registry_exists", "expected": 1, "observed": int(registry_exists), "pass": int(registry_exists)},
        {"gate": "cmake_exists", "expected": 1, "observed": int(cmake_exists), "pass": int(cmake_exists)},
        {"gate": "registry_hits_captured", "expected": ">=1", "observed": len(hit_rows), "pass": int(len(hit_rows) >= 1)},
        {"gate": "registry_excerpts_captured", "expected": ">=1", "observed": len(excerpt_rows), "pass": int(len(excerpt_rows) >= 1)},
        {"gate": "string_literals_counted", "expected": ">=0", "observed": string_count, "pass": 1},
        {"gate": "cmd_symbols_counted", "expected": ">=0", "observed": cmd_symbol_count, "pass": 1},
        {"gate": "cmake_shape_captured", "expected": ">=1", "observed": len(cmake_rows), "pass": int(len(cmake_rows) >= 1)},
    ]
    failures += sum(1 for r in gate_rows if int(r["pass"]) != 1)

    status = "COMMAND_REGISTRY_SHAPE_CAPTURE_READY" if failures == 0 else "COMMAND_REGISTRY_SHAPE_CAPTURE_REVIEW"

    boundary_rows = [
        {"boundary": "shape_capture_report_only", "observed": 1, "required": 1, "pass": 1},
        {"boundary": "cxx_source_edits", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "build_file_edits", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "runtime_command_registration", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "active_catalog_mutation", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "dbf_append_replace_delete_pack_zap", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "cdx_lmdb_create_rebuild", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "help_meta_cmdhelpchk_mutation", "observed": 0, "required": 0, "pass": 1},
    ]

    write_csv(out / "dd067s_registry_shape_hits.csv", hit_rows, ["path", "line", "hits", "text"])
    write_csv(out / "dd067s_registry_symbols.csv", symbol_rows, ["kind", "token", "count", "first_line"])
    write_csv(out / "dd067s_registry_excerpts.csv", excerpt_rows, ["excerpt_id", "path", "center_line", "excerpt"])
    write_csv(out / "dd067s_cmake_shape_hits.csv", cmake_rows, ["path", "line", "reason", "text"])
    write_csv(out / "dd067s_gate_ledger.csv", gate_rows, ["gate", "expected", "observed", "pass"])
    write_csv(out / "dd067s_review_rows.csv", review_rows, ["issue", "detail"])
    write_csv(out / "dd067s_no_mutation_boundary_ledger.csv", boundary_rows, ["boundary", "observed", "required", "pass"])

    # Human-readable excerpts file for quick paste-back.
    excerpt_text = []
    for r in excerpt_rows:
        excerpt_text.append(f"## {r['excerpt_id']} center line {r['center_line']}\n\n```cpp\n{r['excerpt']}\n```\n")
    (out / "DD067S_REGISTRY_EXCERPTS_FOR_REVIEW.md").write_text("\n".join(excerpt_text), encoding="utf-8")

    report = f"""# DD-067S Command Registry Shape Capture

Run id: `{args.run_id}`
Status: **{status}**
Created UTC: `{utc_now()}`

## Purpose

DD-067S captures the actual local shape of `src/cli/command_registry.cpp` after
DD-067R showed that no mirrorable registration block was detected.

## Findings

- Registry exists: **{int(registry_exists)}**
- CMake exists: **{int(cmake_exists)}**
- Registry hit rows: **{len(hit_rows)}**
- Registry symbol rows: **{len(symbol_rows)}**
- Registry excerpt rows: **{len(excerpt_rows)}**
- CMake shape rows: **{len(cmake_rows)}**
- String literal count: **{string_count}**
- cmd_ symbol count: **{cmd_symbol_count}**
- DDICT already present: **{int(ddict_already)}**
- Registry words present: **{int(has_registry_words)}**
- Function defs present: **{int(has_function_defs)}**

## Boundary

DD-067S is report-only. It does not edit C++ source, edit build files, register
runtime commands, mutate active catalog data, mutate DBF/CDX/LMDB artifacts, or
mutate HELP/META/CMDHELPCHK.
"""
    (out / "DD067S_COMMAND_REGISTRY_SHAPE_CAPTURE_REPORT.md").write_text(report, encoding="utf-8")

    manifest = {
        "contract": "dd067s_command_registry_shape_capture_v0",
        "run_id": args.run_id,
        "created_utc": utc_now(),
        "status": status,
        "repo_root": str(repo),
        "profiles": args.profile,
        "dd067r_status": dd067r_manifest.get("status", ""),
        "registry_path": safe_rel(repo, registry_path),
        "cmake_path": safe_rel(repo, cmake_path),
        "registry_hits": len(hit_rows),
        "registry_symbols": len(symbol_rows),
        "registry_excerpts": len(excerpt_rows),
        "cmake_hits": len(cmake_rows),
        "string_literals": string_count,
        "cmd_symbols": cmd_symbol_count,
        "ddict_already_present": int(ddict_already),
        "failures": failures,
        "cxx_source_edits": 0,
        "build_file_edits": 0,
        "runtime_command_registration": 0,
        "active_catalog_mutation": 0,
        "next_recommended_action": "Use registry excerpts to create DD-067T exact local registration patch or hand-apply command_registry.cpp patch if simple.",
    }
    write_json(out / "dd067s_command_registry_shape_capture_manifest.json", manifest)

    print(f"DD-067S command registry shape capture manifest: {out / 'dd067s_command_registry_shape_capture_manifest.json'}")
    print(f"status: {status}; registry_hits: {len(hit_rows)}; excerpts: {len(excerpt_rows)}; cmake_hits: {len(cmake_rows)}; failures: {failures}")
    return 2 if (args.fail_on_review and failures) else 0


if __name__ == "__main__":
    raise SystemExit(main())
