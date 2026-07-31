#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
from pathlib import Path
from typing import Any, Dict, List


EXPECTED_DD089H_STATUS = "DDICT_HELPER_BUILD_WIRING_APPLIED_BUILD_REQUIRED"

PARITY_COMMANDS = [
    {
        "test_id": "DDICT_HELP_PRESERVED",
        "command": "DDICT HELP",
        "needles": ["DDICT HELP", "DDICT STATUS", "DDICT TABLES", "DDICT OBJECTS"],
    },
    {
        "test_id": "DDICT_STATUS_PRESERVED",
        "command": "DDICT STATUS",
        "needles": ["DDICT STATUS", "ACTIVE CATALOG:", "READ-ONLY", "DBF TABLES", "CATALOG STATE"],
    },
    {
        "test_id": "DDICT_TABLES_PRESERVED",
        "command": "DDICT TABLES",
        "needles": ["DDICT TABLES", "DDRUN", "DDOBJECT", "DDATTR", "DDPROFILE"],
    },
    {
        "test_id": "DDICT_OBJECTS_PRESERVED",
        "command": "DDICT OBJECTS TYPE CATALOG_TABLE",
        "needles": ["DDICT OBJECTS TYPE CATALOG_TABLE", "TYPE FILTER   : CATALOG_TABLE", "OBJECT ROWS   : 11", "CATALOG_TABLE"],
    },
    {
        "test_id": "DDICT_FIELDS_PRESERVED",
        "command": "DDICT FIELDS DDOBJECT",
        "needles": ["DDICT FIELDS DDOBJECT", "FIELD ROWS", "OBJID", "OBJTYPE", "PROFILE"],
    },
    {
        "test_id": "DDICT_TAGS_PRESERVED",
        "command": "DDICT TAGS DDATTR",
        "needles": ["DDICT TAGS DDATTR", "CATALOG TAGS", "ATTRID", "OBJ_ATTR"],
    },
    {
        "test_id": "DDICT_REL_PRESERVED",
        "command": "DDICT REL DDOBJECT OUT",
        "needles": ["DDICT REL DDOBJECT OUT", "OUTGOING EDGES", "HAS_FIELD", "HAS_TAG"],
    },
    {
        "test_id": "DDICT_EVIDENCE_PRESERVED",
        "command": "DDICT EVIDENCE DDOBJECT",
        "needles": ["DDICT EVIDENCE DDOBJECT", "ATTRIBUTE EVIDENCE ROWS", "PRIMARY_KEY", "PURPOSE"],
    },
]

PROTECTED_UNTOUCHED = [
    "dottalkpp/data/metadata/datadict/DDRUN.dbf",
    "dottalkpp/data/metadata/datadict/DDBASE.dbf",
    "dottalkpp/data/metadata/datadict/DDOBJECT.dbf",
    "dottalkpp/data/metadata/datadict/DDATTR.dbf",
    "dottalkpp/data/metadata/datadict/DDEDGE.dbf",
    "dottalkpp/data/metadata/datadict/DDPROFILE.dbf",
]


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return {}


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""


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


def rel(repo: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(repo.resolve()).as_posix()
    except Exception:
        return path.as_posix()


def sha256(path: Path) -> str:
    import hashlib
    if not path.exists():
        return ""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def has_any_build_success(text: str) -> int:
    upper = text.upper()
    return int(
        "DOTTALKPP.VCXPROJ ->" in upper
        or "BUILT TARGET DOTTALKPP" in upper
        or "DOTTALKPP.EXE" in upper and "ERROR " not in upper and "FAILED" not in upper
    )


def has_build_failure(text: str) -> int:
    upper = text.upper()
    fail_needles = [
        " ERROR ",
        ": ERROR",
        "FATAL ERROR",
        "FAILED",
        "LNK1120",
        "LNK2019",
        "C2039",
        "C2143",
        "C2059",
        "MSB",
    ]
    return int(any(n in upper for n in fail_needles))


def main() -> int:
    ap = argparse.ArgumentParser(description="DD-089I DDICT refactor build/runtime parity closure")
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--run-id", default="DD089I-ddict-refactor-parity-closure-v0")
    ap.add_argument("--dd089h-dir", default="docs/datadict/reports/DD089H-guarded-build-wiring-apply-v0")
    ap.add_argument("--build-proof", required=True)
    ap.add_argument("--runtime-proof", required=True)
    ap.add_argument("--exe-path", default="build/src/Release/dottalkpp.exe")
    ap.add_argument("--write-closure", action="store_true")
    ap.add_argument("--closure-path", default="docs/datadict/runlog/DD-089I_DDICT_REFACTOR_PARITY_CLOSURE.md")
    ap.add_argument("--profile", action="append", default=[])
    ap.add_argument("--fail-on-review", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    out = Path(args.out_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)

    dd089h_dir = (repo / args.dd089h_dir).resolve()
    dd089h_manifest = read_json(dd089h_dir / "dd089h_guarded_build_wiring_manifest.json")
    build_proof = (repo / args.build_proof).resolve()
    runtime_proof = (repo / args.runtime_proof).resolve()
    exe_path = (repo / args.exe_path).resolve()
    closure_path = (repo / args.closure_path).resolve()

    build_text = read_text(build_proof)
    runtime_text = read_text(runtime_proof)
    build_upper = build_text.upper()
    runtime_upper = runtime_text.upper()

    dd089h_green = int(dd089h_manifest.get("status") == EXPECTED_DD089H_STATUS)
    exe_exists = int(exe_path.exists())
    exe_bytes = exe_path.stat().st_size if exe_path.exists() else 0
    build_exists = int(build_proof.exists())
    runtime_exists = int(runtime_proof.exists())
    build_success = has_any_build_success(build_text)
    build_failure = has_build_failure(build_text)

    parity_rows: List[Dict[str, Any]] = []
    for item in PARITY_COMMANDS:
        missing = [needle for needle in item["needles"] if needle.upper() not in runtime_upper]
        parity_rows.append({
            "test_id": item["test_id"],
            "command": item["command"],
            "needles_expected": len(item["needles"]),
            "needles_seen": len(item["needles"]) - len(missing),
            "pass": int(len(missing) == 0),
            "missing": ";".join(missing),
        })

    runtime_no_unknown = int(not ("UNKNOWN COMMAND" in runtime_upper and "DDICT" in runtime_upper))
    runtime_read_only = int("READ-ONLY" in runtime_upper)
    runtime_active_catalog = int("ACTIVE CATALOG:" in runtime_upper and "DATADICT" in runtime_upper)
    runtime_no_pending = int("ACCEPTED BY CONTRACT BUT RUNTIME READ IMPLEMENTATION IS PENDING" not in runtime_upper)

    protected_rows = []
    for rel_path in PROTECTED_UNTOUCHED:
        path = repo / rel_path
        protected_rows.append({
            "protected_path": rel_path,
            "exists": int(path.exists()),
            "bytes": path.stat().st_size if path.exists() else 0,
            "hash": sha256(path),
            "mutated_by_dd089i": 0,
        })

    gate_rows = [
        {"gate": "dd089h_build_wiring_applied", "expected": EXPECTED_DD089H_STATUS, "observed": dd089h_manifest.get("status", ""), "pass": dd089h_green},
        {"gate": "build_proof_exists", "expected": 1, "observed": build_exists, "pass": build_exists},
        {"gate": "build_success_seen", "expected": 1, "observed": build_success, "pass": build_success},
        {"gate": "build_failure_not_seen", "expected": 0, "observed": build_failure, "pass": int(build_failure == 0)},
        {"gate": "dottalkpp_exe_exists", "expected": 1, "observed": exe_exists, "pass": exe_exists},
        {"gate": "dottalkpp_exe_nonempty", "expected": 1, "observed": int(exe_bytes > 0), "pass": int(exe_bytes > 0)},
        {"gate": "runtime_proof_exists", "expected": 1, "observed": runtime_exists, "pass": runtime_exists},
        {"gate": "runtime_active_catalog_seen", "expected": 1, "observed": runtime_active_catalog, "pass": runtime_active_catalog},
        {"gate": "runtime_read_only_seen", "expected": 1, "observed": runtime_read_only, "pass": runtime_read_only},
        {"gate": "runtime_no_unknown_ddict", "expected": 1, "observed": runtime_no_unknown, "pass": runtime_no_unknown},
        {"gate": "runtime_no_pending_surfaces", "expected": 1, "observed": runtime_no_pending, "pass": runtime_no_pending},
        {"gate": "all_parity_commands_pass", "expected": len(PARITY_COMMANDS), "observed": sum(1 for r in parity_rows if int(r["pass"]) == 1), "pass": int(sum(1 for r in parity_rows if int(r["pass"]) == 1) == len(PARITY_COMMANDS))},
    ]

    failures = sum(1 for row in gate_rows if int(row["pass"]) != 1)
    status = "DDICT_REFACTOR_BUILD_RUNTIME_PARITY_CLOSURE_GREEN" if failures == 0 else "DDICT_REFACTOR_BUILD_RUNTIME_PARITY_CLOSURE_REVIEW"

    boundary_rows = [
        {"boundary": "parity_closure_readback_only", "observed": 1, "required": 1, "pass": 1},
        {"boundary": "cxx_source_edits", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "build_file_edits", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "registry_edits", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "active_catalog_mutation", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "dbf_append_replace_delete_pack_zap", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "cdx_lmdb_create_rebuild", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "help_meta_cmdhelpchk_mutation", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "catalog_regeneration", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "manual_row_repair", "observed": 0, "required": 0, "pass": 1},
    ]

    next_rows = [
        {
            "next_id": "DD090",
            "title": "Data Dictionary reader refactor cycle savepoint",
            "allowed_scope": "report-only savepoint after parity closure green",
        },
        {
            "next_id": "DD091",
            "title": "HELP/CMDHELPCHK integration plan",
            "allowed_scope": "separate guarded plan; no automatic HELP mutation",
        },
        {
            "next_id": "DD092",
            "title": "pydottalk active Data Dictionary reader API",
            "allowed_scope": "separate API implementation plan using proven helper doctrine",
        },
    ]

    write_csv(out / "dd089i_build_gate_ledger.csv", gate_rows, ["gate", "expected", "observed", "pass"])
    write_csv(out / "dd089i_parity_command_ledger.csv", parity_rows, ["test_id", "command", "needles_expected", "needles_seen", "pass", "missing"])
    write_csv(out / "dd089i_protected_catalog_ledger.csv", protected_rows, ["protected_path", "exists", "bytes", "hash", "mutated_by_dd089i"])
    write_csv(out / "dd089i_no_mutation_boundary_ledger.csv", boundary_rows, ["boundary", "observed", "required", "pass"])
    write_csv(out / "dd089i_next_lane_recommendations.csv", next_rows, ["next_id", "title", "allowed_scope"])

    report = f"""# DD-089I DDICT Refactor Build/Runtime Parity Closure

Run id: `{args.run_id}`
Status: **{status}**
Created UTC: `{utc_now()}`

## Purpose

DD-089I closes the DDICT read-helper refactor only after both build proof and runtime parity proof are present.

## Inputs

- DD-089H status: `{dd089h_manifest.get('status', '')}`
- Build proof: `{rel(repo, build_proof)}`
- Runtime proof: `{rel(repo, runtime_proof)}`
- Executable: `{rel(repo, exe_path)}`

## Build classification

- Build proof exists: **{build_exists}**
- Build success seen: **{build_success}**
- Build failure seen: **{build_failure}**
- Executable exists: **{exe_exists}**
- Executable bytes: **{exe_bytes}**

## Runtime classification

- Active catalog seen: **{runtime_active_catalog}**
- READ-ONLY seen: **{runtime_read_only}**
- No unknown DDICT command: **{runtime_no_unknown}**
- No pending runtime surfaces: **{runtime_no_pending}**
- Parity commands passed: **{sum(1 for r in parity_rows if int(r['pass']) == 1)} / {len(PARITY_COMMANDS)}**

## Boundary

DD-089I is closure/readback only. It does not edit C++ source, edit build files,
edit command registration, mutate active catalog data, append/replace/delete/pack/zap DBFs,
create/rebuild CDX/LMDB, mutate HELP/META/CMDHELPCHK, regenerate catalog content, or repair manual rows.
"""
    (out / "DD089I_DDICT_REFACTOR_BUILD_RUNTIME_PARITY_CLOSURE_REPORT.md").write_text(report, encoding="utf-8")

    closure_written = 0
    if args.write_closure:
        closure_path.parent.mkdir(parents=True, exist_ok=True)
        closure_path.write_text(report, encoding="utf-8")
        closure_written = 1

    manifest = {
        "contract": "dd089i_ddict_refactor_parity_closure_v0",
        "run_id": args.run_id,
        "created_utc": utc_now(),
        "status": status,
        "repo_root": str(repo),
        "profiles": args.profile,
        "dd089h_status": dd089h_manifest.get("status", ""),
        "build_proof": rel(repo, build_proof),
        "runtime_proof": rel(repo, runtime_proof),
        "exe_path": rel(repo, exe_path),
        "exe_exists": exe_exists,
        "exe_bytes": exe_bytes,
        "build_success": build_success,
        "build_failure": build_failure,
        "parity_passed": sum(1 for r in parity_rows if int(r["pass"]) == 1),
        "parity_total": len(PARITY_COMMANDS),
        "failures": failures,
        "closure_written": closure_written,
        "closure_path": str(closure_path) if closure_written else "",
        "cxx_source_edits": 0,
        "build_file_edits": 0,
        "registry_edits": 0,
        "active_catalog_mutation": 0,
        "dbf_append_replace_delete_pack_zap": 0,
        "cdx_lmdb_create_rebuild": 0,
        "help_meta_cmdhelpchk_mutation": 0,
        "catalog_regeneration": 0,
        "manual_row_repair": 0,
        "next_recommended_action": "DD090 report-only refactor cycle savepoint if green.",
    }
    write_json(out / "dd089i_ddict_refactor_parity_closure_manifest.json", manifest)

    print(f"DD-089I DDICT refactor parity closure manifest: {out / 'dd089i_ddict_refactor_parity_closure_manifest.json'}")
    print(f"status: {status}; parity: {manifest['parity_passed']}/{manifest['parity_total']}; failures: {failures}; closure_written: {closure_written}")
    return 2 if (args.fail_on_review and failures) else 0


if __name__ == "__main__":
    raise SystemExit(main())
