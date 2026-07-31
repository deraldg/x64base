#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
from pathlib import Path
from typing import Any, Dict, List


EXPECTED_DD078_STATUS = "DDICT_REL_SOURCE_PATCH_APPLIED_BUILD_REQUIRED"


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
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


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


def seen(upper: str, text: str) -> int:
    return int(text.upper() in upper)


def classify_runtime(text: str) -> Dict[str, Any]:
    upper = text.upper()
    return {
        "has_ddict_rel_ddobject_both": seen(upper, "DDICT REL DDOBJECT BOTH"),
        "has_ddict_rel_ddobject_out": seen(upper, "DDICT REL DDOBJECT OUT"),
        "has_ddict_rel_ddattr_in": seen(upper, "DDICT REL DDATTR IN"),
        "has_active_catalog": int("ACTIVE CATALOG:" in upper and "DATADICT" in upper),
        "has_read_only": seen(upper, "READ-ONLY"),
        "has_ddobject_resolved": int("OBJECT NAME   : DDOBJECT" in upper and "CATALOG_TABLE" in upper),
        "has_ddattr_resolved": int("OBJECT NAME   : DDATTR" in upper and "CATALOG_TABLE" in upper),
        "has_ddobject_outgoing_9": int("OUTGOING EDGES: 9" in upper or "OUTGOING EDGES : 9" in upper),
        "has_ddattr_outgoing_8": int("OUTGOING EDGES: 8" in upper or "OUTGOING EDGES : 8" in upper),
        "has_incoming_zero": int("INCOMING EDGES: 0" in upper or "INCOMING EDGES : 0" in upper),
        "has_has_field_rows": seen(upper, "HAS_FIELD"),
        "has_has_tag_rows": seen(upper, "HAS_TAG"),
        "has_direction_out": seen(upper, "OUT  HAS_FIELD"),
        "has_direction_header": int("DIR  EDGETYPE" in upper and "OTHEROBJ" in upper),
        "evidence_pending_preserved": int("DDICT EVIDENCE" in upper and "PENDING" in upper),
        "has_unknown_command_for_ddict": int("UNKNOWN COMMAND" in upper and "DDICT" in upper),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="DD-079 DDICT REL runtime closure")
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--run-id", default="DD079-ddict-rel-runtime-closure-v0")
    ap.add_argument("--dd078-dir", default="docs/datadict/reports/DD078-guarded-ddict-rel-implementation-apply-v0")
    ap.add_argument("--runtime-proof", required=True)
    ap.add_argument("--exe-path", default="build/src/Release/dottalkpp.exe")
    ap.add_argument("--write-closure", action="store_true")
    ap.add_argument("--closure-path", default="docs/datadict/runlog/DD-079_DDICT_REL_RUNTIME_CLOSURE.md")
    ap.add_argument("--profile", action="append", default=[])
    ap.add_argument("--fail-on-review", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    out = Path(args.out_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)

    dd078_dir = (repo / args.dd078_dir).resolve()
    dd078_manifest = read_json(dd078_dir / "dd078_guarded_ddict_rel_impl_manifest.json")
    proof_path = (repo / args.runtime_proof).resolve()
    exe_path = (repo / args.exe_path).resolve()
    closure_path = (repo / args.closure_path).resolve()

    proof_text = read_text(proof_path)
    classified = classify_runtime(proof_text)
    exe_exists = int(exe_path.exists())
    exe_bytes = exe_path.stat().st_size if exe_path.exists() else 0
    proof_exists = int(proof_path.exists())
    dd078_ok = int(dd078_manifest.get("status") == EXPECTED_DD078_STATUS)

    gate_rows = [
        {"gate": "dd078_source_patch_applied", "expected": EXPECTED_DD078_STATUS, "observed": dd078_manifest.get("status", ""), "pass": dd078_ok},
        {"gate": "dottalkpp_exe_exists", "expected": 1, "observed": exe_exists, "pass": exe_exists},
        {"gate": "dottalkpp_exe_nonempty", "expected": 1, "observed": int(exe_bytes > 0), "pass": int(exe_bytes > 0)},
        {"gate": "runtime_proof_exists", "expected": 1, "observed": proof_exists, "pass": proof_exists},
        {"gate": "ddict_rel_ddobject_both_seen", "expected": 1, "observed": classified["has_ddict_rel_ddobject_both"], "pass": classified["has_ddict_rel_ddobject_both"]},
        {"gate": "ddict_rel_ddobject_out_seen", "expected": 1, "observed": classified["has_ddict_rel_ddobject_out"], "pass": classified["has_ddict_rel_ddobject_out"]},
        {"gate": "ddict_rel_ddattr_in_seen", "expected": 1, "observed": classified["has_ddict_rel_ddattr_in"], "pass": classified["has_ddict_rel_ddattr_in"]},
        {"gate": "active_catalog_seen", "expected": 1, "observed": classified["has_active_catalog"], "pass": classified["has_active_catalog"]},
        {"gate": "read_only_seen", "expected": 1, "observed": classified["has_read_only"], "pass": classified["has_read_only"]},
        {"gate": "ddobject_resolved", "expected": 1, "observed": classified["has_ddobject_resolved"], "pass": classified["has_ddobject_resolved"]},
        {"gate": "ddattr_resolved", "expected": 1, "observed": classified["has_ddattr_resolved"], "pass": classified["has_ddattr_resolved"]},
        {"gate": "ddobject_outgoing_9_seen", "expected": 1, "observed": classified["has_ddobject_outgoing_9"], "pass": classified["has_ddobject_outgoing_9"]},
        {"gate": "ddattr_outgoing_8_seen", "expected": 1, "observed": classified["has_ddattr_outgoing_8"], "pass": classified["has_ddattr_outgoing_8"]},
        {"gate": "incoming_zero_seen", "expected": 1, "observed": classified["has_incoming_zero"], "pass": classified["has_incoming_zero"]},
        {"gate": "has_field_rows_seen", "expected": 1, "observed": classified["has_has_field_rows"], "pass": classified["has_has_field_rows"]},
        {"gate": "has_tag_rows_seen", "expected": 1, "observed": classified["has_has_tag_rows"], "pass": classified["has_has_tag_rows"]},
        {"gate": "direction_out_rows_seen", "expected": 1, "observed": classified["has_direction_out"], "pass": classified["has_direction_out"]},
        {"gate": "direction_header_seen", "expected": 1, "observed": classified["has_direction_header"], "pass": classified["has_direction_header"]},
        {"gate": "evidence_pending_preserved", "expected": 1, "observed": classified["evidence_pending_preserved"], "pass": classified["evidence_pending_preserved"]},
        {"gate": "no_unknown_command_for_ddict", "expected": 0, "observed": classified["has_unknown_command_for_ddict"], "pass": int(classified["has_unknown_command_for_ddict"] == 0)},
    ]

    boundary_rows = [
        {"boundary": "runtime_closure_only", "observed": 1, "required": 1, "pass": 1},
        {"boundary": "cxx_source_edits", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "registry_edits", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "build_file_edits", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "active_catalog_mutation", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "dbf_append_replace_delete_pack_zap", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "cdx_lmdb_create_rebuild", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "help_meta_cmdhelpchk_mutation", "observed": 0, "required": 0, "pass": 1},
    ]

    rel_rows = [
        {"command": "DDICT REL DDOBJECT BOTH", "seen": classified["has_ddict_rel_ddobject_both"], "resolved": classified["has_ddobject_resolved"], "expected_outgoing": 9, "outgoing_seen": classified["has_ddobject_outgoing_9"]},
        {"command": "DDICT REL DDOBJECT OUT", "seen": classified["has_ddict_rel_ddobject_out"], "resolved": classified["has_ddobject_resolved"], "expected_outgoing": 9, "outgoing_seen": classified["has_ddobject_outgoing_9"]},
        {"command": "DDICT REL DDATTR IN", "seen": classified["has_ddict_rel_ddattr_in"], "resolved": classified["has_ddattr_resolved"], "expected_outgoing": 8, "outgoing_seen": classified["has_ddattr_outgoing_8"]},
    ]

    failures = sum(1 for r in gate_rows if int(r["pass"]) != 1)
    status = "DDICT_REL_RUNTIME_CLOSURE_GREEN" if failures == 0 else "DDICT_REL_RUNTIME_CLOSURE_REVIEW"

    write_csv(out / "dd079_rel_runtime_gate_ledger.csv", gate_rows, ["gate", "expected", "observed", "pass"])
    write_csv(out / "dd079_rel_command_runtime_ledger.csv", rel_rows, ["command", "seen", "resolved", "expected_outgoing", "outgoing_seen"])
    write_csv(out / "dd079_rel_no_mutation_boundary_ledger.csv", boundary_rows, ["boundary", "observed", "required", "pass"])

    report = f"""# DD-079 DDICT REL Runtime Closure

Run id: `{args.run_id}`
Status: **{status}**
Created UTC: `{utc_now()}`

## Purpose

DD-079 closes the guarded `DDICT REL <object-id-or-name> [IN|OUT|BOTH]`
runtime milestone.

## Evidence

- DD-078 apply status: `{dd078_manifest.get('status', '')}`
- Runtime proof: `{rel(repo, proof_path)}`
- Executable: `{rel(repo, exe_path)}`
- Executable exists: **{exe_exists}**
- Executable bytes: **{exe_bytes}**

## Runtime classification

- DDICT REL DDOBJECT BOTH seen: **{classified['has_ddict_rel_ddobject_both']}**
- DDICT REL DDOBJECT OUT seen: **{classified['has_ddict_rel_ddobject_out']}**
- DDICT REL DDATTR IN seen: **{classified['has_ddict_rel_ddattr_in']}**
- DDOBJECT resolved: **{classified['has_ddobject_resolved']}**
- DDATTR resolved: **{classified['has_ddattr_resolved']}**
- HAS_FIELD rows seen: **{classified['has_has_field_rows']}**
- HAS_TAG rows seen: **{classified['has_has_tag_rows']}**
- READ-ONLY seen: **{classified['has_read_only']}**
- EVIDENCE pending preserved: **{classified['evidence_pending_preserved']}**

## Boundary

DD-079 closure is readback only. It does not edit C++ source, edit registry/build files,
mutate active catalog data, append/replace/delete/pack/zap DBFs, create/rebuild CDX/LMDB,
or mutate HELP/META/CMDHELPCHK.
"""
    (out / "DD079_DDICT_REL_RUNTIME_CLOSURE_REPORT.md").write_text(report, encoding="utf-8")

    closure_written = 0
    if args.write_closure:
        closure_path.parent.mkdir(parents=True, exist_ok=True)
        closure_path.write_text(report, encoding="utf-8")
        closure_written = 1

    manifest = {
        "contract": "dd079_ddict_rel_runtime_closure_v0",
        "run_id": args.run_id,
        "created_utc": utc_now(),
        "status": status,
        "repo_root": str(repo),
        "profiles": args.profile,
        "dd078_status": dd078_manifest.get("status", ""),
        "runtime_proof": rel(repo, proof_path),
        "exe_exists": exe_exists,
        "exe_bytes": exe_bytes,
        "closure_written": closure_written,
        "closure_path": str(closure_path) if closure_written else "",
        "failures": failures,
        "cxx_source_edits": 0,
        "registry_edits": 0,
        "build_file_edits": 0,
        "active_catalog_mutation": 0,
        "help_meta_cmdhelpchk_mutation": 0,
        "next_recommended_action": "DD-080 plan for guarded DDICT EVIDENCE implementation.",
    }
    write_json(out / "dd079_rel_runtime_closure_manifest.json", manifest)

    print(f"DD-079 REL runtime closure manifest: {out / 'dd079_rel_runtime_closure_manifest.json'}")
    print(f"status: {status}; failures: {failures}; closure_written: {closure_written}")
    return 2 if (args.fail_on_review and failures) else 0


if __name__ == "__main__":
    raise SystemExit(main())
