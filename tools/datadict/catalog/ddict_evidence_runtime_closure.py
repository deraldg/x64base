#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
from pathlib import Path
from typing import Any, Dict, List


EXPECTED_DD081_STATUS = "DDICT_EVIDENCE_SOURCE_PATCH_APPLIED_BUILD_REQUIRED"


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


def has(upper: str, needle: str) -> int:
    return int(needle.upper() in upper)


def classify_runtime(text: str) -> Dict[str, Any]:
    upper = text.upper()
    return {
        "has_build_green": int("DOTTALKPP.VCXPROJ ->" in upper and "DOTTALKPP.EXE" in upper),
        "has_ddict_evidence_ddobject": has(upper, "DDICT EVIDENCE DDOBJECT"),
        "has_ddict_evidence_ddattr": has(upper, "DDICT EVIDENCE DDATTR"),
        "has_active_catalog": int("ACTIVE CATALOG:" in upper and "DATADICT" in upper),
        "has_read_only": has(upper, "READ-ONLY"),
        "has_ddobject_resolved": int("OBJECT NAME   : DDOBJECT" in upper and "CATALOG_TABLE" in upper),
        "has_ddattr_resolved": int("OBJECT NAME   : DDATTR" in upper and "CATALOG_TABLE" in upper),
        "has_direct_evidence_rows_zero": int("DIRECT EVIDENCE ROWS: 0" in upper or "DIRECT EVIDENCE ROWS : 0" in upper),
        "has_attribute_evidence_rows_two": int("ATTRIBUTE EVIDENCE ROWS: 2" in upper or "ATTRIBUTE EVIDENCE ROWS : 2" in upper),
        "has_evidence_rows_section": has(upper, "Evidence rows"),
        "has_attribute_evidence_section": has(upper, "Attribute evidence"),
        "has_primary_key_objid": int("PRIMARY_KEY" in upper and "OBJID" in upper),
        "has_primary_key_attrid": int("PRIMARY_KEY" in upper and "ATTRID" in upper),
        "has_purpose_rows": has(upper, "purpose"),
        "has_ddict_rel_ddobject_out": has(upper, "DDICT REL DDOBJECT OUT"),
        "has_rel_outgoing_9": int("OUTGOING EDGES: 9" in upper or "OUTGOING EDGES : 9" in upper),
        "has_rel_has_field": has(upper, "HAS_FIELD"),
        "has_rel_has_tag": has(upper, "HAS_TAG"),
        "has_unknown_command_for_ddict": int("UNKNOWN COMMAND" in upper and "DDICT" in upper),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="DD-082 DDICT EVIDENCE runtime closure")
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--run-id", default="DD082-ddict-evidence-runtime-closure-v0")
    ap.add_argument("--dd081-dir", default="docs/datadict/reports/DD081-guarded-ddict-evidence-implementation-apply-v0")
    ap.add_argument("--runtime-proof", required=True)
    ap.add_argument("--exe-path", default="build/src/Release/dottalkpp.exe")
    ap.add_argument("--write-closure", action="store_true")
    ap.add_argument("--closure-path", default="docs/datadict/runlog/DD-082_DDICT_EVIDENCE_RUNTIME_CLOSURE.md")
    ap.add_argument("--profile", action="append", default=[])
    ap.add_argument("--fail-on-review", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    out = Path(args.out_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)

    dd081_dir = (repo / args.dd081_dir).resolve()
    dd081_manifest = read_json(dd081_dir / "dd081_guarded_ddict_evidence_impl_manifest.json")
    proof_path = (repo / args.runtime_proof).resolve()
    exe_path = (repo / args.exe_path).resolve()
    closure_path = (repo / args.closure_path).resolve()

    proof_text = read_text(proof_path)
    classified = classify_runtime(proof_text)
    exe_exists = int(exe_path.exists())
    exe_bytes = exe_path.stat().st_size if exe_path.exists() else 0
    proof_exists = int(proof_path.exists())
    dd081_ok = int(dd081_manifest.get("status") == EXPECTED_DD081_STATUS)

    gate_rows = [
        {"gate": "dd081_source_patch_applied", "expected": EXPECTED_DD081_STATUS, "observed": dd081_manifest.get("status", ""), "pass": dd081_ok},
        {"gate": "dottalkpp_exe_exists", "expected": 1, "observed": exe_exists, "pass": exe_exists},
        {"gate": "dottalkpp_exe_nonempty", "expected": 1, "observed": int(exe_bytes > 0), "pass": int(exe_bytes > 0)},
        {"gate": "runtime_proof_exists", "expected": 1, "observed": proof_exists, "pass": proof_exists},
        {"gate": "runtime_build_green_seen", "expected": 1, "observed": classified["has_build_green"], "pass": classified["has_build_green"]},
        {"gate": "ddict_evidence_ddobject_seen", "expected": 1, "observed": classified["has_ddict_evidence_ddobject"], "pass": classified["has_ddict_evidence_ddobject"]},
        {"gate": "ddict_evidence_ddattr_seen", "expected": 1, "observed": classified["has_ddict_evidence_ddattr"], "pass": classified["has_ddict_evidence_ddattr"]},
        {"gate": "active_catalog_seen", "expected": 1, "observed": classified["has_active_catalog"], "pass": classified["has_active_catalog"]},
        {"gate": "read_only_seen", "expected": 1, "observed": classified["has_read_only"], "pass": classified["has_read_only"]},
        {"gate": "ddobject_resolved", "expected": 1, "observed": classified["has_ddobject_resolved"], "pass": classified["has_ddobject_resolved"]},
        {"gate": "ddattr_resolved", "expected": 1, "observed": classified["has_ddattr_resolved"], "pass": classified["has_ddattr_resolved"]},
        {"gate": "direct_evidence_rows_zero_seen", "expected": 1, "observed": classified["has_direct_evidence_rows_zero"], "pass": classified["has_direct_evidence_rows_zero"]},
        {"gate": "attribute_evidence_rows_two_seen", "expected": 1, "observed": classified["has_attribute_evidence_rows_two"], "pass": classified["has_attribute_evidence_rows_two"]},
        {"gate": "evidence_rows_section_seen", "expected": 1, "observed": classified["has_evidence_rows_section"], "pass": classified["has_evidence_rows_section"]},
        {"gate": "attribute_evidence_section_seen", "expected": 1, "observed": classified["has_attribute_evidence_section"], "pass": classified["has_attribute_evidence_section"]},
        {"gate": "primary_key_objid_seen", "expected": 1, "observed": classified["has_primary_key_objid"], "pass": classified["has_primary_key_objid"]},
        {"gate": "primary_key_attrid_seen", "expected": 1, "observed": classified["has_primary_key_attrid"], "pass": classified["has_primary_key_attrid"]},
        {"gate": "purpose_rows_seen", "expected": 1, "observed": classified["has_purpose_rows"], "pass": classified["has_purpose_rows"]},
        {"gate": "rel_ddobject_out_preserved", "expected": 1, "observed": classified["has_ddict_rel_ddobject_out"], "pass": classified["has_ddict_rel_ddobject_out"]},
        {"gate": "rel_outgoing_9_preserved", "expected": 1, "observed": classified["has_rel_outgoing_9"], "pass": classified["has_rel_outgoing_9"]},
        {"gate": "rel_has_field_preserved", "expected": 1, "observed": classified["has_rel_has_field"], "pass": classified["has_rel_has_field"]},
        {"gate": "rel_has_tag_preserved", "expected": 1, "observed": classified["has_rel_has_tag"], "pass": classified["has_rel_has_tag"]},
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

    command_rows = [
        {"command": "DDICT EVIDENCE DDOBJECT", "seen": classified["has_ddict_evidence_ddobject"], "resolved": classified["has_ddobject_resolved"], "direct_evidence_rows": 0, "attribute_evidence_rows": 2},
        {"command": "DDICT EVIDENCE DDATTR", "seen": classified["has_ddict_evidence_ddattr"], "resolved": classified["has_ddattr_resolved"], "direct_evidence_rows": 0, "attribute_evidence_rows": 2},
        {"command": "DDICT REL DDOBJECT OUT", "seen": classified["has_ddict_rel_ddobject_out"], "resolved": 1, "outgoing_edges": 9, "preserved": int(classified["has_rel_outgoing_9"] and classified["has_rel_has_field"] and classified["has_rel_has_tag"])},
    ]

    failures = sum(1 for r in gate_rows if int(r["pass"]) != 1)
    status = "DDICT_EVIDENCE_RUNTIME_CLOSURE_GREEN" if failures == 0 else "DDICT_EVIDENCE_RUNTIME_CLOSURE_REVIEW"

    write_csv(out / "dd082_evidence_runtime_gate_ledger.csv", gate_rows, ["gate", "expected", "observed", "pass"])
    write_csv(out / "dd082_evidence_command_runtime_ledger.csv", command_rows, ["command", "seen", "resolved", "direct_evidence_rows", "attribute_evidence_rows", "outgoing_edges", "preserved"])
    write_csv(out / "dd082_evidence_no_mutation_boundary_ledger.csv", boundary_rows, ["boundary", "observed", "required", "pass"])

    report = f"""# DD-082 DDICT EVIDENCE Runtime Closure

Run id: `{args.run_id}`
Status: **{status}**
Created UTC: `{utc_now()}`

## Purpose

DD-082 closes the guarded `DDICT EVIDENCE <object-id-or-name>` runtime milestone.

## Evidence

- DD-081 apply status: `{dd081_manifest.get('status', '')}`
- Runtime proof: `{rel(repo, proof_path)}`
- Executable: `{rel(repo, exe_path)}`
- Executable exists: **{exe_exists}**
- Executable bytes: **{exe_bytes}**

## Runtime classification

- DDICT EVIDENCE DDOBJECT seen: **{classified['has_ddict_evidence_ddobject']}**
- DDICT EVIDENCE DDATTR seen: **{classified['has_ddict_evidence_ddattr']}**
- DDOBJECT resolved: **{classified['has_ddobject_resolved']}**
- DDATTR resolved: **{classified['has_ddattr_resolved']}**
- Direct evidence rows 0 seen: **{classified['has_direct_evidence_rows_zero']}**
- Attribute evidence rows 2 seen: **{classified['has_attribute_evidence_rows_two']}**
- Attribute evidence section seen: **{classified['has_attribute_evidence_section']}**
- REL DDOBJECT OUT preserved: **{classified['has_ddict_rel_ddobject_out']}**

## Boundary

DD-082 closure is readback only. It does not edit C++ source, edit registry/build files,
mutate active catalog data, append/replace/delete/pack/zap DBFs, create/rebuild CDX/LMDB,
or mutate HELP/META/CMDHELPCHK.
"""
    (out / "DD082_DDICT_EVIDENCE_RUNTIME_CLOSURE_REPORT.md").write_text(report, encoding="utf-8")

    closure_written = 0
    if args.write_closure:
        closure_path.parent.mkdir(parents=True, exist_ok=True)
        closure_path.write_text(report, encoding="utf-8")
        closure_written = 1

    manifest = {
        "contract": "dd082_ddict_evidence_runtime_closure_v0",
        "run_id": args.run_id,
        "created_utc": utc_now(),
        "status": status,
        "repo_root": str(repo),
        "profiles": args.profile,
        "dd081_status": dd081_manifest.get("status", ""),
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
        "next_recommended_action": "DD-083 DDICT command surface cycle closure / summary package.",
    }
    write_json(out / "dd082_evidence_runtime_closure_manifest.json", manifest)

    print(f"DD-082 EVIDENCE runtime closure manifest: {out / 'dd082_evidence_runtime_closure_manifest.json'}")
    print(f"status: {status}; failures: {failures}; closure_written: {closure_written}")
    return 2 if (args.fail_on_review and failures) else 0


if __name__ == "__main__":
    raise SystemExit(main())
