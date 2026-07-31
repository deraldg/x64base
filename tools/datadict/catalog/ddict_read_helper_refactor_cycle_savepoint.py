#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List

EXPECTED_DD089I_STATUS = "DDICT_REFACTOR_BUILD_RUNTIME_PARITY_CLOSURE_GREEN"

RUNTIME_SURFACES = [
    "DDICT HELP",
    "DDICT STATUS",
    "DDICT TABLES",
    "DDICT OBJECTS TYPE CATALOG_TABLE",
    "DDICT FIELDS DDOBJECT",
    "DDICT TAGS DDATTR",
    "DDICT REL DDOBJECT OUT",
    "DDICT EVIDENCE DDOBJECT",
]

CHAIN = [
    ("DD089D", "guarded helper source apply", "docs/datadict/reports/DD089D-guarded-helper-source-apply-apply-v0/dd089d_guarded_helper_source_apply_manifest.json"),
    ("DD089E", "cmd_ddict helper integration preview", "docs/datadict/reports/DD089E-cmd-ddict-helper-integration-preview-v0/dd089e_cmd_ddict_helper_integration_preview_manifest.json"),
    ("DD089F", "cmd_ddict integration apply/build-wiring plan", "docs/datadict/reports/DD089F-cmd-ddict-integration-apply-build-wiring-plan-v0/dd089f_cmd_ddict_integration_apply_build_wiring_plan_manifest.json"),
    ("DD089G", "guarded cmd_ddict integration apply", "docs/datadict/reports/DD089G-guarded-cmd-ddict-integration-apply-apply-v0/dd089g_guarded_cmd_ddict_integration_apply_manifest.json"),
    ("DD089H", "guarded helper build wiring", "docs/datadict/reports/DD089H-guarded-build-wiring-apply-v0/dd089h_guarded_build_wiring_manifest.json"),
    ("DD089I", "build/runtime parity closure", "docs/datadict/reports/DD089I-ddict-refactor-parity-closure-v0/dd089i_ddict_refactor_parity_closure_manifest.json"),
    ("DD089J", "helper compile repair", "docs/datadict/reports/DD089J-ddict-helper-compile-repair-apply-v0/dd089j_ddict_helper_compile_repair_manifest.json"),
    ("DD089K", "catalog_paths kTables repair", "docs/datadict/reports/DD089K-ddict-catalog-paths-ktables-compile-repair-apply-v0/dd089k_ddict_catalog_paths_ktables_compile_repair_manifest.json"),
    ("DD089L", "kTables shape repair", "docs/datadict/reports/DD089L-ddict-ktables-shape-compile-repair-apply-v0/dd089l_ddict_ktables_shape_compile_repair_manifest.json"),
]


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except Exception as exc:
        return {"_read_error": str(exc)}


def sha256(path: Path) -> str:
    if not path.exists():
        return ""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def write_json(path: Path, obj: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: List[Dict[str, Any]], fields: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fields})


def rel(repo: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(repo.resolve()).as_posix()
    except Exception:
        return path.as_posix()


def proof_row(repo: Path, role: str, rel_path: str) -> Dict[str, Any]:
    p = repo / rel_path
    return {
        "role": role,
        "path": rel_path,
        "exists": int(p.exists()),
        "bytes": p.stat().st_size if p.exists() else 0,
        "sha256": sha256(p),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="DD-090 DDICT read-helper refactor cycle savepoint")
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--run-id", default="DD090-ddict-read-helper-refactor-cycle-savepoint-v0")
    ap.add_argument("--dd089i-dir", default="docs/datadict/reports/DD089I-ddict-refactor-parity-closure-v0")
    ap.add_argument("--runtime-proof", default="docs/datadict/runlog/DD-089I_DDICT_REFACTOR_RUNTIME_PROOF.md")
    ap.add_argument("--build-proof", default="docs/datadict/runlog/DD-089I_DDICT_REFACTOR_BUILD_PROOF.md")
    ap.add_argument("--write-savepoint", action="store_true")
    ap.add_argument("--savepoint-path", default="docs/datadict/runlog/DD-090_DDICT_READ_HELPER_REFACTOR_CYCLE_SAVEPOINT.md")
    ap.add_argument("--profile", action="append", default=[])
    ap.add_argument("--fail-on-review", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    out = Path(args.out_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)

    dd089i_manifest_path = repo / args.dd089i_dir / "dd089i_ddict_refactor_parity_closure_manifest.json"
    dd089i = read_json(dd089i_manifest_path)

    runtime_proof = repo / args.runtime_proof
    build_proof = repo / args.build_proof
    runtime_text = runtime_proof.read_text(encoding="utf-8", errors="replace") if runtime_proof.exists() else ""
    runtime_upper = runtime_text.upper()

    chain_rows: List[Dict[str, Any]] = []
    for ddid, name, manifest_rel in CHAIN:
        p = repo / manifest_rel
        m = read_json(p)
        chain_rows.append({
            "ddid": ddid,
            "name": name,
            "manifest": manifest_rel,
            "manifest_exists": int(p.exists()),
            "status": m.get("status", ""),
            "failures": m.get("failures", ""),
            "applied": m.get("applied", ""),
            "closure_written": m.get("closure_written", ""),
        })

    surface_rows = [{"surface": s, "seen_in_runtime_proof": int(s.upper() in runtime_upper)} for s in RUNTIME_SURFACES]

    proof_rows = [
        proof_row(repo, "build_proof", args.build_proof),
        proof_row(repo, "runtime_proof", args.runtime_proof),
        proof_row(repo, "dd089i_manifest", args.dd089i_dir + "/dd089i_ddict_refactor_parity_closure_manifest.json"),
        proof_row(repo, "dd089i_build_gate_ledger", args.dd089i_dir + "/dd089i_build_gate_ledger.csv"),
        proof_row(repo, "dd089i_parity_command_ledger", args.dd089i_dir + "/dd089i_parity_command_ledger.csv"),
        proof_row(repo, "dd089i_boundary_ledger", args.dd089i_dir + "/dd089i_no_mutation_boundary_ledger.csv"),
    ]

    boundary_rows = [
        {"boundary": "savepoint_report_only", "observed": 1, "required": 1, "pass": 1},
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
        {"next_id": "DD091", "title": "QUIT/EXIT command-chain consistency lane", "allowed_scope": "report or guarded consistency package for CLI, DO/.dts, and ArcticTalk/TUI paths"},
        {"next_id": "DD092", "title": "Data Dictionary HELP/CMDHELPCHK integration plan", "allowed_scope": "report-only plan; no HELP mutation without explicit authorization"},
        {"next_id": "DD093", "title": "Data Dictionary helper API hardening", "allowed_scope": "separate cleanup plan after parity green"},
    ]

    parity_passed = int(dd089i.get("parity_passed", 0) or 0)
    parity_total = int(dd089i.get("parity_total", 8) or 8)
    build_success = int(dd089i.get("build_success", 0) or 0)
    build_failure = int(dd089i.get("build_failure", 0) or 0)
    surfaces_seen = sum(int(r["seen_in_runtime_proof"]) for r in surface_rows)
    dd089i_green = int(dd089i.get("status") == EXPECTED_DD089I_STATUS)

    gate_rows = [
        {"gate": "dd089i_green", "expected": EXPECTED_DD089I_STATUS, "observed": dd089i.get("status", ""), "pass": dd089i_green},
        {"gate": "dd089i_parity_8_of_8", "expected": "8/8", "observed": f"{parity_passed}/{parity_total}", "pass": int(parity_passed == 8 and parity_total == 8)},
        {"gate": "build_success_recorded", "expected": 1, "observed": build_success, "pass": int(build_success == 1)},
        {"gate": "build_failure_not_recorded", "expected": 0, "observed": build_failure, "pass": int(build_failure == 0)},
        {"gate": "runtime_surfaces_seen_in_proof", "expected": 8, "observed": surfaces_seen, "pass": int(surfaces_seen == 8)},
        {"gate": "build_proof_exists", "expected": 1, "observed": int(build_proof.exists()), "pass": int(build_proof.exists())},
        {"gate": "runtime_proof_exists", "expected": 1, "observed": int(runtime_proof.exists()), "pass": int(runtime_proof.exists())},
        {"gate": "savepoint_report_only", "expected": 1, "observed": 1, "pass": 1},
    ]

    failures = sum(1 for r in gate_rows if int(r["pass"]) != 1)
    status = "DDICT_READ_HELPER_REFACTOR_CYCLE_SAVEPOINT_GREEN" if failures == 0 else "DDICT_READ_HELPER_REFACTOR_CYCLE_SAVEPOINT_REVIEW"

    write_csv(out / "dd090_refactor_chain_ledger.csv", chain_rows, ["ddid", "name", "manifest", "manifest_exists", "status", "failures", "applied", "closure_written"])
    write_csv(out / "dd090_runtime_surface_ledger.csv", surface_rows, ["surface", "seen_in_runtime_proof"])
    write_csv(out / "dd090_proof_artifact_ledger.csv", proof_rows, ["role", "path", "exists", "bytes", "sha256"])
    write_csv(out / "dd090_gate_ledger.csv", gate_rows, ["gate", "expected", "observed", "pass"])
    write_csv(out / "dd090_no_mutation_boundary_ledger.csv", boundary_rows, ["boundary", "observed", "required", "pass"])
    write_csv(out / "dd090_next_lane_recommendations.csv", next_rows, ["next_id", "title", "allowed_scope"])

    report = f"""# DD-090 DDICT Read-Helper Refactor Cycle Savepoint

Run id: `{args.run_id}`
Status: **{status}**
Created UTC: `{utc_now()}`

## Purpose

DD-090 captures a report-only savepoint after DD-089I closes the Data Dictionary read-helper refactor cycle.

## Accepted prior closure

- DD-089I manifest: `{rel(repo, dd089i_manifest_path)}`
- DD-089I status: `{dd089i.get('status', '')}`
- Runtime parity: **{parity_passed} / {parity_total}**
- Build success recorded: **{build_success}**
- Build failure recorded: **{build_failure}**

## Runtime surfaces

Observed in runtime proof: **{surfaces_seen} / 8**

```text
DDICT HELP
DDICT STATUS
DDICT TABLES
DDICT OBJECTS TYPE CATALOG_TABLE
DDICT FIELDS DDOBJECT
DDICT TAGS DDATTR
DDICT REL DDOBJECT OUT
DDICT EVIDENCE DDOBJECT
```

## Cycle interpretation

The DDICT command surface is runtime-proven after helper extraction/refactor:

- helper source apply
- `cmd_ddict.cpp` integration
- helper source build wiring
- compile repairs DD-089J/K/L
- build/runtime parity closed green in DD-089I

## Boundary

DD-090 is report-only. It does not edit C++ source, edit build files, edit command registration,
mutate active catalog DBFs, append/replace/delete/pack/zap DBFs, create/rebuild CDX/LMDB,
mutate HELP/META/CMDHELPCHK, regenerate catalog content, or repair manual rows.

## Recommended next lanes

```text
DD-091  QUIT/EXIT command-chain consistency lane
DD-092  Data Dictionary HELP/CMDHELPCHK integration plan
DD-093  Data Dictionary helper API hardening / cleanup plan
```
"""
    (out / "DD090_DDICT_READ_HELPER_REFACTOR_CYCLE_SAVEPOINT_REPORT.md").write_text(report, encoding="utf-8")

    savepoint_written = 0
    savepoint_path = repo / args.savepoint_path
    if args.write_savepoint:
        savepoint_path.parent.mkdir(parents=True, exist_ok=True)
        savepoint_path.write_text(report, encoding="utf-8")
        savepoint_written = 1

    manifest = {
        "contract": "dd090_ddict_read_helper_refactor_cycle_savepoint_v0",
        "run_id": args.run_id,
        "created_utc": utc_now(),
        "status": status,
        "repo_root": str(repo),
        "profiles": args.profile,
        "dd089i_status": dd089i.get("status", ""),
        "parity_passed": parity_passed,
        "parity_total": parity_total,
        "build_success": build_success,
        "build_failure": build_failure,
        "runtime_surfaces_seen": surfaces_seen,
        "failures": failures,
        "savepoint_written": savepoint_written,
        "savepoint_path": str(savepoint_path) if savepoint_written else "",
        "cxx_source_edits": 0,
        "build_file_edits": 0,
        "registry_edits": 0,
        "active_catalog_mutation": 0,
        "dbf_append_replace_delete_pack_zap": 0,
        "cdx_lmdb_create_rebuild": 0,
        "help_meta_cmdhelpchk_mutation": 0,
        "catalog_regeneration": 0,
        "manual_row_repair": 0,
        "next_recommended_action": "DD-091 QUIT/EXIT command-chain consistency lane, or DD-092 Data Dictionary HELP/CMDHELPCHK integration plan.",
    }
    write_json(out / "dd090_ddict_read_helper_refactor_cycle_savepoint_manifest.json", manifest)

    print(f"DD-090 DDICT read-helper refactor cycle savepoint manifest: {out / 'dd090_ddict_read_helper_refactor_cycle_savepoint_manifest.json'}")
    print(f"status: {status}; parity: {parity_passed}/{parity_total}; runtime_surfaces: {surfaces_seen}/8; failures: {failures}; savepoint_written: {savepoint_written}")
    return 2 if (args.fail_on_review and failures) else 0


if __name__ == "__main__":
    raise SystemExit(main())
