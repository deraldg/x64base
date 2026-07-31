#!/usr/bin/env python3
"""
DotTalk++ / x64base physical dictionary extractor skeleton v0.

Report-only extractor. It does not launch DotTalk++, does not build C++, and does not
mutate repository files. It scans source/package evidence and emits a DD-006-shaped
physical dictionary manifest.

Target: Python 3.12+ with standard library only.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import struct
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

MANIFEST_SCHEMA_ID = "dottalk.physical_dictionary.manifest"
GENERATOR_NAME = "dd007_physical_dictionary_extractor"
GENERATOR_VERSION = "0.0.1-dd007"

SCRIPT_EXTENSIONS = {".dts", ".ps1", ".bat", ".cmd", ".py", ".sh"}
SOURCE_EXTENSIONS = {".cpp", ".hpp", ".h", ".c", ".cc", ".hh", ".ipp"}
CONFIG_EXTENSIONS = {".json", ".cmake", ".txt", ".md", ".yml", ".yaml"}

KEY_SOURCE_ANCHORS = [
    "include/xbase.hpp",
    "include/xbase/dbf_create.hpp",
    "include/xbase/fields.hpp",
    "include/xbase/field_name_policy.hpp",
    "src/xbase/dbf_file.cpp",
    "src/core/fields_mgr.cpp",
    "src/cli/dbf64_header_validate.cpp",
    "include/memo/memo_manager.hpp",
    "include/memo/memo_auto.hpp",
    "src/memo/memo_manager.cpp",
    "include/cdx/cdx.hpp",
    "include/cdx/cdx_meta.hpp",
    "src/cdx/cdx_file.cpp",
    "include/workspace/relation_state.hpp",
    "include/workspace/workarea_manager.hpp",
    "src/cli/cmd_workspace.cpp",
    "src/cli/cmd_rel.cpp",
    "src/cli/cmd_rule.cpp",
    "src/cli/field_constraints.cpp",
    "include/xexpr/eval_context.hpp",
    "src/cli/cmd_import.cpp",
    "src/cli/cmd_export.cpp",
    "src/cli/cmd_autodbf.cpp",
    "include/dt/meta/metafact.hpp",
    "src/meta/metacollect.cpp",
]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def safe_read_text(path: Path, max_bytes: int = 4_000_000) -> str:
    data = path.read_bytes()[:max_bytes]
    return data.decode("utf-8", errors="replace")


def relpath(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def make_source_id(n: int) -> str:
    return f"SRC-{n:05d}"


def kind_for_path(path: Path, root: Path) -> str:
    name = path.name.lower()
    ext = path.suffix.lower()
    r = relpath(path, root).lower()
    if ext == ".dbf":
        return "dbf_file"
    if r.endswith(".schema.json"):
        return "schema_json"
    if name in {"cmakelists.txt", "cmakepresets.json", "vcpkg.json"} or ext == ".cmake":
        return "build_config"
    if ext in SCRIPT_EXTENSIONS:
        return "script"
    if ext in SOURCE_EXTENSIONS:
        return "cpp_source"
    if ext in CONFIG_EXTENSIONS:
        return "config_or_doc"
    return "file"


def profile_for_path(path: Path, root: Path) -> str:
    r = relpath(path, root).lower()
    if "/edu/" in f"/{r}" or "/labtalk/" in f"/{r}" or "student" in r or "/cases/" in f"/{r}":
        return "educational"
    if "/bindings/" in f"/{r}" or "test" in r or "probe" in r:
        return "dev"
    if "/include/" in f"/{r}" or "/src/" in f"/{r}" or r in {"cmakelists.txt", "cmakepresets.json", "vcpkg.json"}:
        return "professional"
    return "unknown"


def boundary_for_source_kind(kind: str, path: Path, root: Path) -> str:
    r = relpath(path, root).lower()
    if kind == "dbf_file":
        return "runtime_data_observed_read_only"
    if kind == "script":
        if "savepoint" in r or "mdo" in r or "manualgen" in r:
            return "maintenance_script_report_only_until_classified"
        if r.endswith(".dts"):
            return "runtime_script_report_only_until_classified"
        return "script_report_only_until_classified"
    if kind in {"schema_json", "build_config"}:
        return "declaration_source_report_only"
    if kind == "cpp_source":
        return "source_contract_report_only"
    return "report_only"


def evidence_kind_for_source_kind(kind: str) -> str:
    return {
        "dbf_file": "runtime_file_observed",
        "schema_json": "declared_schema_source",
        "build_config": "build_declaration_source",
        "script": "script_source_observed",
        "cpp_source": "source_anchor_observed",
        "config_or_doc": "documentation_or_config_observed",
    }.get(kind, "file_observed")


def discover_sources(root: Path) -> Tuple[List[Dict[str, Any]], Dict[str, str]]:
    sources: List[Dict[str, Any]] = []
    source_by_rel: Dict[str, str] = {}
    candidates: List[Path] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if any(part in {".git", "build", "out", ".vs"} for part in path.parts):
            continue
        ext = path.suffix.lower()
        r = relpath(path, root)
        include = False
        if ext in SOURCE_EXTENSIONS | SCRIPT_EXTENSIONS | CONFIG_EXTENSIONS | {".dbf"}:
            include = True
        if r in KEY_SOURCE_ANCHORS:
            include = True
        if include:
            candidates.append(path)
    for i, path in enumerate(sorted(candidates, key=lambda p: relpath(p, root).lower()), 1):
        kind = kind_for_path(path, root)
        sid = make_source_id(i)
        r = relpath(path, root)
        source_by_rel[r] = sid
        sources.append({
            "source_id": sid,
            "source_kind": kind,
            "source_path": r,
            "source_hash": sha256_file(path),
            "source_line": None,
            "evidence_kind": evidence_kind_for_source_kind(kind),
            "trust_level": "source_observed",
            "profile_scope": profile_for_path(path, root),
            "boundary_class": boundary_for_source_kind(kind, path, root),
            "size_bytes": path.stat().st_size,
        })
    return sources, source_by_rel


def parse_declared_schema(root: Path, source_by_rel: Dict[str, str]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    tables: List[Dict[str, Any]] = []
    fields: List[Dict[str, Any]] = []
    indexes: List[Dict[str, Any]] = []
    schemas: List[Dict[str, Any]] = []
    warnings: List[Dict[str, Any]] = []
    schema_files = sorted(root.rglob("*.schema.json"))
    table_n = 0
    field_n = 0
    idx_n = 0
    for path in schema_files:
        r = relpath(path, root)
        source_ref = source_by_rel.get(r, "")
        try:
            data = json.loads(safe_read_text(path))
        except Exception as exc:
            schemas.append({"schema_id": f"SCHEMA-{len(schemas)+1:04d}", "schema_path": r, "loaded_ok": False, "source_ref": source_ref, "error": str(exc)})
            warnings.append({"warning_id": f"WARN-SCHEMA-{len(warnings)+1:04d}", "severity": "review", "message": f"Could not parse schema JSON: {r}: {exc}"})
            continue
        loaded_ok = isinstance(data, dict)
        schemas.append({
            "schema_id": f"SCHEMA-{len(schemas)+1:04d}",
            "schema_path": r,
            "loaded_ok": loaded_ok,
            "source_ref": source_ref,
            "schema_name": data.get("name") if isinstance(data, dict) else None,
            "schema_version": data.get("version") if isinstance(data, dict) else None,
        })
        if not isinstance(data, dict) or not isinstance(data.get("fields"), list) or not data.get("name"):
            continue
        table_n += 1
        table_id = f"TBL-SCHEMA-{table_n:04d}"
        table_name = str(data.get("name"))
        tables.append({
            "table_id": table_id,
            "logical_name": table_name,
            "physical_path": None,
            "table_flavor": None,
            "area_kind": "declared_schema",
            "record_count": None,
            "header_length": None,
            "record_length": None,
            "field_count": len(data.get("fields", [])),
            "open_verified": False,
            "source_ref": source_ref,
            "evidence_status": "declared_not_runtime_verified",
            "profile_scope": profile_for_path(path, root),
        })
        for ordinal, f in enumerate(data.get("fields", []), 1):
            if not isinstance(f, dict):
                continue
            field_n += 1
            fields.append({
                "field_id": f"FLD-SCHEMA-{field_n:05d}",
                "table_id": table_id,
                "logical_name": str(f.get("name", "")),
                "descriptor_name": str(f.get("name", "")) if f.get("name") is not None else None,
                "field_type": str(f.get("type", "unknown")),
                "width": f.get("length"),
                "decimals": f.get("decimals"),
                "ordinal": ordinal,
                "offset": None,
                "nullable": None if "required" not in f else not bool(f.get("required")),
                "evidence_status": "declared_not_runtime_verified",
                "source_ref": source_ref,
                "schema_path": r,
            })
        for idx in data.get("indexes", []) or []:
            if not isinstance(idx, dict):
                continue
            idx_n += 1
            order = idx.get("order")
            indexes.append({
                "index_id": f"IDX-SCHEMA-{idx_n:04d}",
                "table_id": table_id,
                "backend_kind": str(idx.get("engine", "declared")),
                "source_ref": source_ref,
                "tag_name": idx.get("name"),
                "order": order,
                "unique": idx.get("unique"),
                "nullable": idx.get("nullable"),
                "evidence_status": "declared_not_runtime_verified",
            })
    return tables, fields, indexes, schemas, warnings


def parse_dbf_header(path: Path) -> Dict[str, Any]:
    """Best-effort DBF header parser supporting standard and x64-prepped header prefixes.

    This function reads only local bytes and never mutates the DBF. It returns a compact
    physical fact row plus field descriptors when possible.
    """
    data = path.read_bytes()
    if len(data) < 32:
        raise ValueError("DBF shorter than 32 bytes")
    version = data[0]
    y, m, d = data[1], data[2], data[3]
    record_count32 = struct.unpack_from("<I", data, 4)[0]
    header_len16 = struct.unpack_from("<H", data, 8)[0]
    record_len16 = struct.unpack_from("<H", data, 10)[0]
    descriptor_start = 32
    table_flavor = "dbf_standard_candidate"
    # x64-prepped DBF evidence observed in project material uses descriptor offset 96.
    if len(data) >= 97 and data[96:97] not in {b"\r", b"\x00"}:
        possible_term = data.find(b"\r", 96, min(len(data), 4096))
        if possible_term != -1 and (possible_term - 96) % 32 == 0:
            descriptor_start = 96
            table_flavor = "dbf_x64_extended_prefix_candidate"
            # If available, prefer widened values at offsets visible in current project evidence.
            try:
                record_count32 = struct.unpack_from("<Q", data, 32)[0]
                header_len16 = struct.unpack_from("<Q", data, 40)[0]
                record_len16 = struct.unpack_from("<Q", data, 48)[0]
            except Exception:
                pass
    fields = []
    pos = descriptor_start
    ordinal = 0
    while pos + 32 <= len(data):
        if data[pos] == 0x0D:
            break
        name_bytes = data[pos:pos+11].split(b"\x00", 1)[0]
        try:
            name = name_bytes.decode("ascii", errors="replace").strip()
        except Exception:
            name = repr(name_bytes)
        ftype = chr(data[pos+11]) if data[pos+11] else "?"
        # Standard DBF has offset at 12 and length/decimals at 16/17. Project x64 descriptors may widen.
        offset = struct.unpack_from("<I", data, pos+12)[0]
        width = data[pos+16]
        decimals = data[pos+17]
        ordinal += 1
        fields.append({
            "name": name,
            "type": ftype,
            "width": int(width),
            "decimals": int(decimals),
            "ordinal": ordinal,
            "offset": int(offset),
        })
        pos += 32
    return {
        "version_byte": version,
        "last_update": f"{1900 + y:04d}-{m:02d}-{d:02d}" if 1 <= m <= 12 and 1 <= d <= 31 else None,
        "record_count": int(record_count32),
        "header_length": int(header_len16),
        "record_length": int(record_len16),
        "field_count": len(fields),
        "table_flavor": table_flavor,
        "descriptor_start": descriptor_start,
        "fields": fields,
    }


def parse_dbf_files(root: Path, source_by_rel: Dict[str, str], start_table_n: int, start_field_n: int) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    tables: List[Dict[str, Any]] = []
    fields: List[Dict[str, Any]] = []
    verify: List[Dict[str, Any]] = []
    warnings: List[Dict[str, Any]] = []
    table_n = start_table_n
    field_n = start_field_n
    for path in sorted(root.rglob("*.dbf")):
        r = relpath(path, root)
        source_ref = source_by_rel.get(r, "")
        table_n += 1
        table_id = f"TBL-DBF-{table_n:04d}"
        try:
            parsed = parse_dbf_header(path)
            ok = True
        except Exception as exc:
            parsed = {}
            ok = False
            warnings.append({"warning_id": f"WARN-DBF-{len(warnings)+1:04d}", "severity": "review", "message": f"Could not parse DBF header: {r}: {exc}"})
        tables.append({
            "table_id": table_id,
            "logical_name": path.stem,
            "physical_path": r,
            "table_flavor": parsed.get("table_flavor"),
            "area_kind": "runtime_file_observed",
            "record_count": parsed.get("record_count"),
            "header_length": parsed.get("header_length"),
            "record_length": parsed.get("record_length"),
            "field_count": parsed.get("field_count"),
            "open_verified": False,
            "source_ref": source_ref,
            "evidence_status": "physical_header_parsed" if ok else "physical_header_parse_failed",
        })
        verify.append({
            "verify_id": f"VERIFY-DBF-{len(verify)+1:04d}",
            "table_id": table_id,
            "verify_kind": "header_parse",
            "status": "parsed" if ok else "failed",
            "source_ref": source_ref,
        })
        for fd in parsed.get("fields", []):
            field_n += 1
            fields.append({
                "field_id": f"FLD-DBF-{field_n:05d}",
                "table_id": table_id,
                "logical_name": fd.get("name"),
                "descriptor_name": fd.get("name"),
                "field_type": fd.get("type"),
                "width": fd.get("width"),
                "decimals": fd.get("decimals"),
                "ordinal": fd.get("ordinal"),
                "offset": fd.get("offset"),
                "nullable": None,
                "evidence_status": "physical_header_parsed",
                "source_ref": source_ref,
            })
    return tables, fields, verify, warnings


def find_anchor_runtime_proof(root: Path, source_by_rel: Dict[str, str]) -> List[Dict[str, Any]]:
    proofs: List[Dict[str, Any]] = []
    for anchor in KEY_SOURCE_ANCHORS:
        p = root / anchor
        if p.exists():
            proofs.append({
                "proof_id": f"PROOF-SRC-{len(proofs)+1:04d}",
                "object_kind": "source_anchor",
                "status": "present",
                "source_ref": source_by_rel.get(anchor, ""),
                "anchor_path": anchor,
            })
    return proofs


def find_field_name_policy(root: Path, source_by_rel: Dict[str, str]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    anchor = "include/xbase/field_name_policy.hpp"
    path = root / anchor
    if path.exists():
        text = safe_read_text(path)
        rows.append({
            "policy_id": "FNP-0001",
            "logical_name": "field_name_policy_source_anchor",
            "descriptor_name": None,
            "truncated": "source_scan_needed",
            "mangled": "source_scan_needed",
            "sanitized": "source_scan_needed",
            "source_ref": source_by_rel.get(anchor, ""),
            "observed_terms": sorted(set(re.findall(r"\b(truncat\w*|mangl\w*|saniti\w*|normalize\w*)\b", text, flags=re.I)))[:20],
        })
    return rows


def write_csv(path: Path, rows: List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    keys: List[str] = []
    for row in rows:
        for k in row:
            if k not in keys:
                keys.append(k)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        for row in rows:
            clean = {}
            for k in keys:
                v = row.get(k)
                if isinstance(v, (list, dict)):
                    clean[k] = json.dumps(v, ensure_ascii=False, sort_keys=True)
                else:
                    clean[k] = v
            w.writerow(clean)


def build_manifest(repo_root: Path, repo_package: Optional[Path], profile: str, mode: str, harvest_run_id: Optional[str]) -> Dict[str, Any]:
    repo_root = repo_root.resolve()
    sources, source_by_rel = discover_sources(repo_root)
    schema_tables, schema_fields, indexes, schemas, schema_warnings = parse_declared_schema(repo_root, source_by_rel)
    dbf_tables, dbf_fields, table_verify, dbf_warnings = parse_dbf_files(repo_root, source_by_rel, len(schema_tables), len(schema_fields))
    warnings = schema_warnings + dbf_warnings
    if not dbf_tables:
        warnings.append({
            "warning_id": "WARN-NO-DBF-0001",
            "severity": "info",
            "message": "No .dbf files were found under repo root; manifest contains source/declaration evidence only.",
        })
    if not schema_tables:
        warnings.append({
            "warning_id": "WARN-NO-TABLE-SCHEMA-0001",
            "severity": "review",
            "message": "No table-bearing *.schema.json files were found under repo root.",
        })
    runtime_proof = find_anchor_runtime_proof(repo_root, source_by_rel)
    field_name_policy = find_field_name_policy(repo_root, source_by_rel)
    package_name = repo_package.name if repo_package else repo_root.name
    package_sha = sha256_file(repo_package) if repo_package and repo_package.exists() else sha256_file_for_tree_hint(repo_root)
    return {
        "schema_id": MANIFEST_SCHEMA_ID,
        "schema_version": "0.1-dd006-compatible",
        "harvest_run_id": harvest_run_id or f"DD007-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}",
        "generated_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "generator": {
            "name": GENERATOR_NAME,
            "version": GENERATOR_VERSION,
            "mode": "report_only_source_scan",
            "target_python": "3.12+",
        },
        "repo_package": {
            "name": package_name,
            "sha256": package_sha,
            "root_hint": repo_root.name,
        },
        "profile": profile,
        "mode": mode,
        "sources": sources,
        "tables": schema_tables + dbf_tables,
        "fields": schema_fields + dbf_fields,
        "field_name_policy": field_name_policy,
        "table_verify": table_verify,
        "memo_status": [],
        "indexes": indexes,
        "schemas": schemas,
        "workareas": [],
        "relations": [],
        "rules": [],
        "expressions": [],
        "import_profiles": [],
        "runtime_proof": runtime_proof,
        "warnings": warnings,
    }


def sha256_file_for_tree_hint(root: Path) -> str:
    h = hashlib.sha256()
    for path in sorted(root.rglob("*")):
        if path.is_file():
            r = relpath(path, root).encode("utf-8", errors="replace")
            h.update(r)
            h.update(b"\0")
            h.update(str(path.stat().st_size).encode("ascii"))
            h.update(b"\0")
    return h.hexdigest()


def write_outputs(manifest: Dict[str, Any], out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "physical_dictionary_manifest_v0.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    for key in ["sources", "tables", "fields", "field_name_policy", "table_verify", "indexes", "schemas", "runtime_proof", "warnings"]:
        write_csv(out_dir / f"{key}.csv", manifest.get(key, []))
    summary = [
        {"metric": "sources", "value": len(manifest.get("sources", []))},
        {"metric": "tables", "value": len(manifest.get("tables", []))},
        {"metric": "fields", "value": len(manifest.get("fields", []))},
        {"metric": "indexes", "value": len(manifest.get("indexes", []))},
        {"metric": "schemas", "value": len(manifest.get("schemas", []))},
        {"metric": "runtime_proof", "value": len(manifest.get("runtime_proof", []))},
        {"metric": "warnings", "value": len(manifest.get("warnings", []))},
    ]
    write_csv(out_dir / "summary.csv", summary)


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Report-only DotTalk++ / x64base physical dictionary manifest extractor skeleton.")
    ap.add_argument("--repo-root", required=True, type=Path, help="Repository root to scan read-only.")
    ap.add_argument("--out-dir", required=True, type=Path, help="Output directory for manifest and CSVs.")
    ap.add_argument("--repo-package", type=Path, default=None, help="Optional original repo package zip for package hash evidence.")
    ap.add_argument("--profile", choices=["engine", "professional", "educational", "dev", "unknown"], default="professional")
    ap.add_argument("--mode", choices=["report_only", "source_scan", "runtime_scan", "import_staging", "promotion_candidate"], default="source_scan")
    ap.add_argument("--harvest-run-id", default=None)
    args = ap.parse_args(argv)
    manifest = build_manifest(args.repo_root, args.repo_package, args.profile, args.mode, args.harvest_run_id)
    write_outputs(manifest, args.out_dir)
    print(json.dumps({
        "status": "ok",
        "mode": manifest["mode"],
        "sources": len(manifest.get("sources", [])),
        "tables": len(manifest.get("tables", [])),
        "fields": len(manifest.get("fields", [])),
        "indexes": len(manifest.get("indexes", [])),
        "warnings": len(manifest.get("warnings", [])),
        "out_dir": str(args.out_dir),
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
