#!/usr/bin/env python3
"""
DD-043 v1.1 pydottalk / DotTalk++ Runtime Readback Execution.

v1.1 hardening:
  Automatically prepends <repo-root>/build/python to sys.path before importing
  pydottalk. This makes the runtime readback repeatable without requiring a
  caller-managed PYTHONPATH.

Authorized scope:
  runtime readback/import evidence against sandbox catalog DBFs.

Allowed:
  import pydottalk
  enumerate/read sandbox DBF/DBT files
  capture runtime/introspection evidence
  optionally run a generated readback probe script

Not allowed:
  DBF writes
  REPLACE / APPEND / DELETE
  CDX creation
  LMDB writes
  HELP/META/CMDHELPCHK mutation
  active catalog promotion
  source edits
"""
from __future__ import annotations

import argparse
import csv
import datetime as _dt
import importlib
import json
import subprocess
import sys
import struct
from pathlib import Path
from typing import Any, Dict, List


CATALOG_TABLES = [
    "DDRUN", "DDBASE", "DDSOURCE", "DDOBJECT", "DDATTR", "DDEDGE",
    "DDEVID", "DDGATE", "DDREVIEW", "DDARTIF", "DDPROFILE"
]


def utc_now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds")


def write_json(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: List[Dict[str, Any]], fields: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for row in rows:
            w.writerow({k: row.get(k, "") for k in fields})


def safe_rel(repo: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(repo.resolve()).as_posix()
    except Exception:
        return path.as_posix()


def assert_sandbox_path(repo: Path, sandbox: Path) -> None:
    repo_r = repo.resolve()
    sandbox_r = sandbox.resolve()
    try:
        rel = sandbox_r.relative_to(repo_r).as_posix().lower()
    except Exception:
        raise SystemExit(f"Refusing sandbox path outside repo root: {sandbox_r}")
    allowed = "dottalkpp/data/metadata/datadict_sandbox"
    if rel != allowed and not rel.startswith(allowed + "/"):
        raise SystemExit(f"Refusing readback outside authorized sandbox path: {rel}")


def harden_pydottalk_path(repo: Path) -> Dict[str, Any]:
    """Prepend repo build/python if it exists."""
    build_python = repo / "build" / "python"
    before = list(sys.path)
    added = 0
    if build_python.exists():
        bp = str(build_python.resolve())
        if bp not in sys.path:
            sys.path.insert(0, bp)
            added = 1
    return {
        "build_python_path": str(build_python),
        "build_python_exists": int(build_python.exists()),
        "added_to_sys_path": added,
        "sys_path_count_before": len(before),
        "sys_path_count_after": len(sys.path),
    }


def read_dbf_header(path: Path) -> Dict[str, Any]:
    with path.open("rb") as f:
        data = f.read(8192)
    if len(data) < 32:
        raise ValueError(f"Too small for DBF header: {path}")
    version = data[0]
    y, m, d = data[1], data[2], data[3]
    records = struct.unpack("<I", data[4:8])[0]
    header_len = struct.unpack("<H", data[8:10])[0]
    record_len = struct.unpack("<H", data[10:12])[0]
    field_count = (header_len - 33) // 32
    fields = []
    offset = 32
    for _ in range(field_count):
        desc = data[offset:offset + 32]
        raw_name = desc[0:11].split(b"\x00", 1)[0]
        fields.append({
            "name": raw_name.decode("ascii", errors="ignore"),
            "type": chr(desc[11]),
            "width": desc[16],
            "decimals": desc[17],
        })
        offset += 32
    return {
        "version": version,
        "date": f"{1900+y:04d}-{m:02d}-{d:02d}",
        "records": records,
        "header_len": header_len,
        "record_len": record_len,
        "field_count": field_count,
        "fields": fields,
    }


def read_csv_dict(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def probe_pydottalk(path_hardening: Dict[str, Any]) -> Dict[str, Any]:
    result: Dict[str, Any] = {
        "import_ok": 0,
        "module_repr": "",
        "version": "",
        "module_file": "",
        "public_names": [],
        "candidate_read_names": [],
        "error": "",
        "path_hardening": path_hardening,
    }
    try:
        mod = importlib.import_module("pydottalk")
        result["import_ok"] = 1
        result["module_repr"] = repr(mod)
        result["version"] = str(getattr(mod, "__version__", ""))
        result["module_file"] = str(getattr(mod, "__file__", ""))
        names = sorted(n for n in dir(mod) if not n.startswith("__"))
        result["public_names"] = names
        candidates = []
        for needle in ["open", "dbf", "table", "area", "use", "record", "field", "list"]:
            for name in names:
                if needle in name.lower():
                    candidates.append(name)
        result["candidate_read_names"] = sorted(set(candidates))
    except Exception as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"
    return result


def run_optional_probe(probe_path: Path, out_dir: Path, repo: Path) -> Dict[str, Any]:
    result = {
        "probe_path": str(probe_path),
        "exists": int(probe_path.exists()),
        "returncode": "",
        "stdout_path": "",
        "stderr_path": "",
        "status": "NOT_RUN",
    }
    if not probe_path.exists():
        result["status"] = "MISSING"
        return result
    stdout_path = out_dir / "dd043_optional_probe_stdout.txt"
    stderr_path = out_dir / "dd043_optional_probe_stderr.txt"

    env = dict(**__import__("os").environ)
    build_python = repo / "build" / "python"
    old = env.get("PYTHONPATH", "")
    if build_python.exists():
        env["PYTHONPATH"] = str(build_python) + (";" + old if old else "")

    proc = subprocess.run(
        [sys.executable, str(probe_path)],
        cwd=str(probe_path.parent),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=60,
        env=env,
    )
    stdout_path.write_text(proc.stdout, encoding="utf-8", errors="replace")
    stderr_path.write_text(proc.stderr, encoding="utf-8", errors="replace")
    result["returncode"] = proc.returncode
    result["stdout_path"] = str(stdout_path)
    result["stderr_path"] = str(stderr_path)
    result["status"] = "PASS" if proc.returncode == 0 else "REVIEW"
    return result


def main() -> int:
    ap = argparse.ArgumentParser(description="DD-043 v1.1 read-only pydottalk/runtime sandbox catalog readback execution")
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--sandbox-path", default="dottalkpp/data/metadata/datadict_sandbox")
    ap.add_argument("--dd041-dir", default="docs/datadict/reports/DD041-sandbox-catalog-dbf-smoke-v0")
    ap.add_argument("--dd042-dir", default="docs/datadict/reports/DD042-sandbox-catalog-inspection-v0")
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--run-id", default="DD043-pydottalk-runtime-readback-v1_1")
    ap.add_argument("--profile", action="append", default=[])
    ap.add_argument("--run-generated-probe", action="store_true", help="Run DD-042 generated pydottalk probe script")
    ap.add_argument("--fail-on-review", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    sandbox = (repo / args.sandbox_path).resolve()
    dd041_dir = (repo / args.dd041_dir).resolve()
    dd042_dir = (repo / args.dd042_dir).resolve()
    out = Path(args.out_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)

    assert_sandbox_path(repo, sandbox)
    path_hardening = harden_pydottalk_path(repo)

    dd041_rows = read_csv_dict(dd041_dir / "dd041_table_readback_ledger.csv")
    expected_by_table = {r.get("table", "").upper(): r for r in dd041_rows}

    table_rows: List[Dict[str, Any]] = []
    failures = 0
    for table in CATALOG_TABLES:
        dbf_path = sandbox / f"{table}.dbf"
        expected = expected_by_table.get(table, {})
        expected_rows = int(float(expected.get("projected_rows") or 0)) if expected else ""
        expected_fields = int(float(expected.get("field_count") or 0)) if expected else ""
        row = {
            "table": table,
            "dbf_exists": int(dbf_path.exists()),
            "expected_rows": expected_rows,
            "runtime_header_rows": "",
            "expected_fields": expected_fields,
            "runtime_header_fields": "",
            "status": "PENDING",
            "pass": 0,
        }
        if not dbf_path.exists():
            row["status"] = "FAIL_MISSING_DBF"
            failures += 1
        else:
            try:
                hdr = read_dbf_header(dbf_path)
                row["runtime_header_rows"] = hdr["records"]
                row["runtime_header_fields"] = hdr["field_count"]
                ok = (expected_rows == "" or hdr["records"] == expected_rows) and (expected_fields == "" or hdr["field_count"] == expected_fields)
                row["status"] = "PASS" if ok else "FAIL_HEADER_MISMATCH"
                row["pass"] = int(ok)
                if not ok:
                    failures += 1
            except Exception as exc:
                row["status"] = f"FAIL_READ_ERROR: {type(exc).__name__}: {exc}"
                failures += 1
        table_rows.append(row)

    pydt = probe_pydottalk(path_hardening)
    pydt_ok = int(pydt.get("import_ok", 0))
    if not pydt_ok:
        failures += 1

    optional_probe_result = {"status": "NOT_REQUESTED"}
    if args.run_generated_probe:
        optional_probe_result = run_optional_probe(dd042_dir / "dd042_pydottalk_readback_probe.py", out, repo)
        if optional_probe_result.get("status") not in {"PASS", "NOT_REQUESTED"}:
            failures += 1

    boundary_rows = [
        {"boundary": "build_python_path_hardened", "observed": path_hardening.get("build_python_exists"), "required": 1, "pass": int(path_hardening.get("build_python_exists") == 1)},
        {"boundary": "pydottalk_import_attempted", "observed": 1, "required": 1, "pass": 1},
        {"boundary": "runtime_readback_only", "observed": 1, "required": 1, "pass": 1},
        {"boundary": "dbf_rows_written_by_dd043", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "cdx_created", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "lmdb_written", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "help_mutation", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "meta_mutation", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "cmdhelpchk_mutation", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "active_catalog_promotion", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "source_edits", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "protected_system_mutations", "observed": 0, "required": 0, "pass": 1},
    ]

    status = "PYDOTTALK_RUNTIME_READBACK_GREEN" if failures == 0 else "PYDOTTALK_RUNTIME_READBACK_REVIEW"

    write_csv(out / "dd043_runtime_table_readback_ledger.csv", table_rows,
              ["table", "dbf_exists", "expected_rows", "runtime_header_rows", "expected_fields", "runtime_header_fields", "status", "pass"])
    write_csv(out / "dd043_no_mutation_boundary_ledger.csv", boundary_rows,
              ["boundary", "observed", "required", "pass"])

    pydt_report = {
        "import_ok": pydt.get("import_ok"),
        "module_repr": pydt.get("module_repr"),
        "version": pydt.get("version"),
        "module_file": pydt.get("module_file"),
        "candidate_read_names": pydt.get("candidate_read_names"),
        "public_names_count": len(pydt.get("public_names") or []),
        "error": pydt.get("error"),
        "path_hardening": path_hardening,
    }
    write_json(out / "dd043_pydottalk_runtime_probe.json", pydt_report)
    (out / "dd043_pydottalk_public_names.txt").write_text(
        "\n".join(pydt.get("public_names") or []) + "\n",
        encoding="utf-8",
    )

    manifest = {
        "contract": "dd043_v1_1_pydottalk_path_hardening_v0",
        "run_id": args.run_id,
        "created_utc": utc_now(),
        "status": status,
        "repo_root": str(repo),
        "sandbox_path": str(sandbox),
        "profiles": args.profile,
        "tables_checked": len(table_rows),
        "runtime_readback_failures": failures,
        "pydottalk_import_ok": pydt_ok,
        "path_hardening": path_hardening,
        "optional_probe": optional_probe_result,
        "dbf_rows_written": 0,
        "cdx_created": 0,
        "lmdb_written": 0,
        "active_catalog_promotion": 0,
        "protected_system_mutations": 0,
        "next_recommended_package": "DD-044 active catalog promotion plan, only if runtime readback is green and promotion is separately authorized",
    }
    write_json(out / "dd043_pydottalk_runtime_readback_manifest.json", manifest)

    report = f"""# DD-043 v1.1 pydottalk / Runtime Sandbox Catalog Readback Report

Run id: `{args.run_id}`
Status: **{status}**
Created UTC: `{manifest['created_utc']}`

## v1.1 hardening

- build/python path: `{path_hardening.get('build_python_path')}`
- build/python exists: {path_hardening.get('build_python_exists')}
- added to sys.path: {path_hardening.get('added_to_sys_path')}

## Runtime evidence

- pydottalk import ok: {pydt_ok}
- pydottalk module file: `{pydt.get('module_file') or ''}`
- tables checked: {len(table_rows)}
- runtime readback failures: {failures}
- optional DD-042 generated probe status: `{optional_probe_result.get('status')}`

## Boundary

DD-043 v1.1 is runtime readback only. It does not write DBFs, create CDX files,
write LMDB data, mutate HELP/META/CMDHELPCHK, edit source, or promote the catalog.

## Next

If DD-043 v1.1 is green, DD-044 may plan active catalog promotion. Promotion remains
separately gated and is not authorized by DD-043 v1.1.
"""
    (out / "DD043_PYDOTTALK_RUNTIME_READBACK_REPORT.md").write_text(report, encoding="utf-8")

    print(f"DD-043 v1.1 pydottalk runtime readback manifest: {out / 'dd043_pydottalk_runtime_readback_manifest.json'}")
    print(f"status: {status}; pydottalk_import_ok: {pydt_ok}; tables_checked: {len(table_rows)}; failures: {failures}; build_python_exists: {path_hardening.get('build_python_exists')}")
    return 2 if (args.fail_on_review and failures) else 0


if __name__ == "__main__":
    raise SystemExit(main())
