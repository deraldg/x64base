#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
from pathlib import Path
from typing import Any, Dict, List


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def write_json(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: List[Dict[str, Any]], fields: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in fields})


def rel(repo: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(repo.resolve()).as_posix()
    except Exception:
        return path.as_posix()


def runtime_classify(text: str) -> Dict[str, int]:
    u = text.upper()
    has_usage = int("USAGE:" in u and "DDICT" in u)
    has_help = int("DDICT HELP" in u or has_usage)
    unknown = int("UNKNOWN COMMAND" in u and "DDICT" in u)
    pending = int("RUNTIME READ IMPLEMENTATION IS PENDING" in u or "ACCEPTED BY CONTRACT" in u or "PENDING" in u)
    return {
        "has_ddict_help": has_help,
        "has_usage": has_usage,
        "has_pending_message": pending,
        "has_unknown_command_for_ddict": unknown,
        "runtime_smoke_green": int(has_help and has_usage and not unknown),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="DD-068 DDICT build/runtime smoke closure")
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--run-id", default="DD068-ddict-build-runtime-smoke-closure-v0")
    ap.add_argument("--exe-path", default="build/src/Release/dottalkpp.exe")
    ap.add_argument("--header-path", default="include/cli/cmd_ddict.hpp")
    ap.add_argument("--source-path", default="src/cli/cmd_ddict.cpp")
    ap.add_argument("--registry-path", default="src/cli/command_registry.cpp")
    ap.add_argument("--cmake-path", default="src/CMakeLists.txt")
    ap.add_argument("--smoke-path", default="dottalkpp/data/tests/dd065_ddict_usage_smoke.dts")
    ap.add_argument("--runtime-proof", default="")
    ap.add_argument("--write-closure", action="store_true")
    ap.add_argument("--closure-path", default="docs/datadict/runlog/DD-068_DDICT_BUILD_RUNTIME_SMOKE_CLOSURE.md")
    ap.add_argument("--profile", action="append", default=[])
    ap.add_argument("--fail-on-review", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    out = Path(args.out_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)

    exe = (repo / args.exe_path).resolve()
    header = (repo / args.header_path).resolve()
    source = (repo / args.source_path).resolve()
    registry = (repo / args.registry_path).resolve()
    cmake = (repo / args.cmake_path).resolve()
    smoke = (repo / args.smoke_path).resolve()
    proof = (repo / args.runtime_proof).resolve() if args.runtime_proof else None
    closure = (repo / args.closure_path).resolve()

    header_text = read_text(header)
    source_text = read_text(source)
    registry_text = read_text(registry)
    cmake_text = read_text(cmake)
    proof_text = read_text(proof) if proof else ""

    exe_exists = int(exe.exists())
    exe_bytes = exe.stat().st_size if exe.exists() else 0
    header_shape = int("cmd_DDICT" in header_text and "std::istringstream" in header_text and "xbase::DbArea" in header_text)
    source_shape = int("void cmd_DDICT" in source_text and "std::istringstream" in source_text)
    registry_has = int("DDICT" in registry_text and "cmd_DDICT" in registry_text)
    cmake_ok = int(("GLOB_RECURSE" in cmake_text and "*.cpp" in cmake_text) or "cmd_ddict.cpp" in cmake_text)
    runtime = runtime_classify(proof_text)
    proof_present = int(bool(proof_text.strip()))

    artifact_rows = [
        {"artifact": "exe", "path": rel(repo, exe), "exists": exe_exists, "bytes": exe_bytes},
        {"artifact": "header", "path": rel(repo, header), "exists": int(header.exists()), "bytes": header.stat().st_size if header.exists() else 0},
        {"artifact": "source", "path": rel(repo, source), "exists": int(source.exists()), "bytes": source.stat().st_size if source.exists() else 0},
        {"artifact": "registry", "path": rel(repo, registry), "exists": int(registry.exists()), "bytes": registry.stat().st_size if registry.exists() else 0},
        {"artifact": "cmake", "path": rel(repo, cmake), "exists": int(cmake.exists()), "bytes": cmake.stat().st_size if cmake.exists() else 0},
        {"artifact": "smoke", "path": rel(repo, smoke), "exists": int(smoke.exists()), "bytes": smoke.stat().st_size if smoke.exists() else 0},
    ]

    gate_rows = [
        {"gate": "dottalkpp_exe_exists", "expected": 1, "observed": exe_exists, "pass": exe_exists},
        {"gate": "dottalkpp_exe_nonempty", "expected": 1, "observed": int(exe_bytes > 0), "pass": int(exe_bytes > 0)},
        {"gate": "header_house_handler_shape", "expected": 1, "observed": header_shape, "pass": header_shape},
        {"gate": "source_house_handler_shape", "expected": 1, "observed": source_shape, "pass": source_shape},
        {"gate": "registry_has_ddict", "expected": 1, "observed": registry_has, "pass": registry_has},
        {"gate": "cmake_includes_or_globs_ddict_source", "expected": 1, "observed": cmake_ok, "pass": cmake_ok},
        {"gate": "runtime_proof_present", "expected": "0 or 1", "observed": proof_present, "pass": 1},
        {"gate": "runtime_smoke_green_if_proof_present", "expected": "1 if proof supplied", "observed": runtime["runtime_smoke_green"], "pass": int((not proof_present) or runtime["runtime_smoke_green"])},
    ]

    runtime_rows = [{"check": k, "observed": v} for k, v in runtime.items()]
    boundary_rows = [
        {"boundary": "closure_readback_only", "observed": 1, "required": 1, "pass": 1},
        {"boundary": "cxx_source_edits", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "build_file_edits", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "active_catalog_mutation", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "dbf_append_replace_delete_pack_zap", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "cdx_lmdb_create_rebuild", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "help_meta_cmdhelpchk_mutation", "observed": 0, "required": 0, "pass": 1},
    ]

    failures = sum(1 for row in gate_rows if int(row["pass"]) != 1)
    if proof_present:
        status = "DDICT_BUILD_RUNTIME_SMOKE_CLOSURE_GREEN" if failures == 0 else "DDICT_BUILD_RUNTIME_SMOKE_CLOSURE_REVIEW"
    else:
        status = "DDICT_BUILD_GREEN_RUNTIME_SMOKE_PENDING" if failures == 0 else "DDICT_BUILD_RUNTIME_SMOKE_CLOSURE_REVIEW"

    write_csv(out / "dd068_artifact_ledger.csv", artifact_rows, ["artifact", "path", "exists", "bytes"])
    write_csv(out / "dd068_gate_ledger.csv", gate_rows, ["gate", "expected", "observed", "pass"])
    write_csv(out / "dd068_runtime_smoke_ledger.csv", runtime_rows, ["check", "observed"])
    write_csv(out / "dd068_no_mutation_boundary_ledger.csv", boundary_rows, ["boundary", "observed", "required", "pass"])

    report = f"""# DD-068 DDICT Build and Runtime Smoke Closure

Run id: `{args.run_id}`
Status: **{status}**
Created UTC: `{utc_now()}`

## Build

- Executable: `{rel(repo, exe)}`
- Executable exists: **{exe_exists}**
- Executable bytes: **{exe_bytes}**

## DDICT integration

- Header house handler shape: **{header_shape}**
- Source house handler shape: **{source_shape}**
- Registry has DDICT/cmd_DDICT: **{registry_has}**
- CMake includes or globs DDICT source: **{cmake_ok}**

## Runtime smoke

- Runtime proof supplied: **{proof_present}**
- Runtime smoke green: **{runtime['runtime_smoke_green']}**

## Boundary

DD-068 is closure/readback only. It does not edit C++ source, edit build files,
mutate active catalog data, mutate DBF/CDX/LMDB artifacts, mutate
HELP/META/CMDHELPCHK, regenerate catalog content, or repair manual rows.
"""
    (out / "DD068_DDICT_BUILD_RUNTIME_SMOKE_CLOSURE_REPORT.md").write_text(report, encoding="utf-8")

    closure_written = 0
    if args.write_closure:
        closure.parent.mkdir(parents=True, exist_ok=True)
        closure.write_text(report, encoding="utf-8")
        closure_written = 1

    manifest = {
        "contract": "dd068_ddict_build_runtime_smoke_closure_v0",
        "run_id": args.run_id,
        "created_utc": utc_now(),
        "status": status,
        "repo_root": str(repo),
        "profiles": args.profile,
        "exe_exists": exe_exists,
        "exe_bytes": exe_bytes,
        "header_house_handler_shape": header_shape,
        "source_house_handler_shape": source_shape,
        "registry_has_ddict": registry_has,
        "cmake_includes_or_globs_ddict_source": cmake_ok,
        "runtime_proof_present": proof_present,
        "runtime_smoke_green": runtime["runtime_smoke_green"],
        "closure_written": closure_written,
        "closure_path": str(closure) if closure_written else "",
        "failures": failures,
        "cxx_source_edits": 0,
        "build_file_edits": 0,
        "active_catalog_mutation": 0,
        "help_meta_cmdhelpchk_mutation": 0,
        "next_recommended_action": "Run DDICT HELP and rerun with --runtime-proof if runtime proof is pending; then proceed to DD-069 read surface implementation plan.",
    }
    write_json(out / "dd068_ddict_build_runtime_smoke_closure_manifest.json", manifest)

    print(f"DD-068 DDICT build/runtime smoke closure manifest: {out / 'dd068_ddict_build_runtime_smoke_closure_manifest.json'}")
    print(f"status: {status}; exe_exists: {exe_exists}; runtime_smoke_green: {runtime['runtime_smoke_green']}; failures: {failures}; closure_written: {closure_written}")
    return 2 if (args.fail_on_review and failures) else 0


if __name__ == "__main__":
    raise SystemExit(main())
