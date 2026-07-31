#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List, Tuple


EXPECTED_DD096E_STATUS = "DATADICT_EXTERNAL_APPLY_ROW_STAGING_READY"
EXPECTED_DD096D_STATUS = "DATADICT_GUARDED_APPLY_DESIGN_PREFLIGHT_READY"
EXPECTED_DD098_STATUS = "DATADICT_BASELINE_CLOSED_AND_REGRESSION_PROVEN"

DEFAULT_STAGED_DIR = "docs/datadict/reports/DD096E-external-apply-row-staging-v0/generated_staged_apply_rows"

REQUIRED_STAGED_FILES = [
    "dd096e_staged_ddobject_insert_rows.csv",
    "dd096e_suppressed_existing_ddobject_rows.csv",
    "dd096e_staged_ddattr_insert_rows.csv",
    "dd096e_staged_ddedge_insert_rows.csv",
    "dd096e_staged_ddevid_insert_rows.csv",
    "dd096e_staged_ddgate_insert_rows.csv",
    "dd096e_staged_apply_row_index.csv",
    "dd096e_staging_rules.csv",
]

PROTECTED_ARTIFACTS = [
    "dottalkpp/data/datadict",
    "dottalkpp/data/indexes/datadict",
    "dottalkpp/data/lmdb/datadict",
    "dottalkpp/data/workspaces/ddbase.dtschema",
    "src/datadict/ddict_catalog_paths.cpp",
    "src/cli/cmd_ddict.cpp",
    "src/CMakeLists.txt",
]


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def read_text(path: Path) -> str:
    if not path.exists() or path.is_dir():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(read_text(path))
    except Exception as exc:
        return {"_read_error": str(exc)}


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_json(path: Path, obj: Dict[str, object]) -> None:
    write_text(path, json.dumps(obj, indent=2, sort_keys=True) + "\n")


def write_csv(path: Path, rows: List[Dict[str, object]], fields: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        w.writeheader()
        for row in rows:
            w.writerow({k: row.get(k, "") for k in fields})


def sha256(path: Path) -> str:
    if not path.exists() or path.is_dir():
        return ""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def artifact_row(repo: Path, rel_path: str, role: str) -> Dict[str, object]:
    p = repo / rel_path
    return {
        "role": role,
        "path": rel_path,
        "exists": int(p.exists()),
        "kind": "dir" if p.exists() and p.is_dir() else "file" if p.exists() and p.is_file() else "",
        "bytes_or_children": p.stat().st_size if p.exists() and p.is_file() else sum(1 for _ in p.iterdir()) if p.exists() and p.is_dir() else 0,
        "sha256": sha256(p),
    }


def int_field(row: Dict[str, str], name: str) -> int:
    try:
        return int(str(row.get(name, "0")).strip() or "0")
    except ValueError:
        return 1


def norm(s: object) -> str:
    return str(s or "").strip().upper()


def le16(b: bytes, pos: int) -> int:
    return int.from_bytes(b[pos:pos+2], "little", signed=False) if pos + 2 <= len(b) else 0


def le32(b: bytes, pos: int) -> int:
    return int.from_bytes(b[pos:pos+4], "little", signed=False) if pos + 4 <= len(b) else 0


def parse_dbf(path: Path, limit: int = 100000) -> Tuple[List[Dict[str, str]], Dict[str, object]]:
    meta: Dict[str, object] = {"path": str(path), "exists": int(path.exists()), "fields": [], "records_read": 0, "parse_warning": ""}
    if not path.exists():
        meta["parse_warning"] = "missing_dbf"
        return [], meta
    data = path.read_bytes()
    size = len(data)
    if size < 64:
        meta["parse_warning"] = "file_too_small"
        return [], meta

    std_header_len = le16(data, 8)
    std_record_len = le16(data, 10)
    ext_header_len = le32(data, 0x28)
    ext_record_len = le32(data, 0x30)

    header_len = std_header_len if 32 <= std_header_len < size else ext_header_len
    if not (32 <= header_len < size):
        for pos in range(32, min(size, 4096)):
            if data[pos] == 0x0D:
                header_len = pos + 1
                break
    record_len = std_record_len if 1 <= std_record_len < 100000 else ext_record_len
    if not (32 <= header_len < size and 1 <= record_len < 100000):
        meta["parse_warning"] = "could_not_determine_header_or_record_len"
        return [], meta

    descriptor_start = 96 if size > 96 and data[96] not in (0x00, 0x0D) and 96 < header_len else 32
    fields: List[Dict[str, object]] = []
    pos = descriptor_start
    while pos + 32 <= size and pos < header_len:
        if data[pos] == 0x0D:
            break
        desc = data[pos:pos+32]
        name = desc[:11].split(b"\x00", 1)[0].decode("ascii", errors="ignore").strip().upper()
        if not name:
            break
        ftype = chr(desc[11]) if 32 <= desc[11] < 127 else "C"
        off = le32(desc, 12)
        flen = desc[16]
        candidates = [flen, le16(desc, 16), le32(desc, 16), le32(desc, 20), le32(desc, 24)]
        flen = next((x for x in candidates if 0 < x <= record_len), flen)
        fields.append({"name": name, "type": ftype, "offset": off, "length": flen})
        pos += 32

    if fields and any(int(f["offset"]) <= 0 or int(f["offset"]) + int(f["length"]) > record_len for f in fields):
        off = 1
        for f in fields:
            f["offset"] = off
            off += int(f["length"])

    meta["fields"] = fields
    meta["field_count"] = len(fields)
    meta["header_len"] = header_len
    meta["record_len"] = record_len
    meta["descriptor_start"] = descriptor_start

    rows: List[Dict[str, str]] = []
    if not fields:
        meta["parse_warning"] = "no_fields_found"
        return rows, meta

    max_records = max(0, (size - header_len) // record_len)
    for i in range(min(max_records, limit)):
        start = header_len + i * record_len
        rec = data[start:start+record_len]
        if len(rec) < record_len:
            continue
        if rec[0:1] == b"*":
            continue
        if rec[0:1] == b"\x1A":
            break
        row: Dict[str, str] = {}
        for f in fields:
            raw = rec[int(f["offset"]):int(f["offset"]) + int(f["length"])]
            row[str(f["name"])] = raw.decode("utf-8", errors="replace").strip()
        rows.append(row)
    meta["records_read"] = len(rows)
    return rows, meta


def main() -> int:
    ap = argparse.ArgumentParser(description="DD096F staged-row review and simulated apply validation")
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--run-id", default="DD096F-staged-row-review-simulated-apply-v0")
    ap.add_argument("--dd096e-dir", default="docs/datadict/reports/DD096E-external-apply-row-staging-v0")
    ap.add_argument("--dd096d-dir", default="docs/datadict/reports/DD096D-guarded-apply-design-preflight-v0")
    ap.add_argument("--dd098-dir", default="docs/datadict/reports/DD098-datadict-baseline-closeout-v0")
    ap.add_argument("--staged-dir", default=DEFAULT_STAGED_DIR)
    ap.add_argument("--profile", action="append", default=[])
    ap.add_argument("--fail-on-review", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    out = Path(args.out_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)

    dd096e_manifest_path = repo / args.dd096e_dir / "dd096e_external_apply_row_staging_manifest.json"
    dd096d_manifest_path = repo / args.dd096d_dir / "dd096d_guarded_apply_design_preflight_manifest.json"
    dd098_manifest_path = repo / args.dd098_dir / "dd098_datadict_baseline_closeout_manifest.json"

    dd096e = read_json(dd096e_manifest_path)
    dd096d = read_json(dd096d_manifest_path)
    dd098 = read_json(dd098_manifest_path)

    sdir = repo / args.staged_dir
    staged_obj = read_csv(sdir / "dd096e_staged_ddobject_insert_rows.csv")
    suppressed_obj = read_csv(sdir / "dd096e_suppressed_existing_ddobject_rows.csv")
    staged_attr = read_csv(sdir / "dd096e_staged_ddattr_insert_rows.csv")
    staged_edge = read_csv(sdir / "dd096e_staged_ddedge_insert_rows.csv")
    staged_evid = read_csv(sdir / "dd096e_staged_ddevid_insert_rows.csv")
    staged_gate = read_csv(sdir / "dd096e_staged_ddgate_insert_rows.csv")
    staged_index = read_csv(sdir / "dd096e_staged_apply_row_index.csv")
    staging_rules = read_csv(sdir / "dd096e_staging_rules.csv")

    file_rows = []
    for name in REQUIRED_STAGED_FILES:
        p = sdir / name
        file_rows.append({"required_file": name, "path": str(p), "exists": int(p.exists()), "bytes": p.stat().st_size if p.exists() else 0, "sha256": sha256(p)})

    active_obj_rows, active_obj_meta = parse_dbf(repo / "dottalkpp/data/datadict/DDOBJECT.dbf")
    active_obj_keys = {(norm(r.get("OBJTYPE")), norm(r.get("OWNER")), norm(r.get("NAME"))) for r in active_obj_rows}

    duplicate_risk_rows = []
    for r in staged_obj:
        key = (norm(r.get("objtype")), norm(r.get("owner")), norm(r.get("name")))
        duplicate_risk_rows.append({
            "target_table": "DDOBJECT",
            "staged_id": r.get("objid", ""),
            "staged_key": "|".join(key),
            "active_duplicate_seen": int(key in active_obj_keys),
            "risk": "DUPLICATE_BLOCKER" if key in active_obj_keys else "OK_NEW_OBJECT",
        })

    allowed_objids = {r.get("objid", "") for r in staged_obj if r.get("objid", "")}
    allowed_objids.update(r.get("active_objid", "") for r in suppressed_obj if r.get("active_objid", ""))

    ref_rows = []
    missing_attr_refs = 0
    for r in staged_attr:
        ok = r.get("objid", "") in allowed_objids
        missing_attr_refs += 0 if ok else 1
        ref_rows.append({
            "family": "DDATTR",
            "row_id": r.get("attrid", ""),
            "reference_field": "objid",
            "reference_value": r.get("objid", ""),
            "reference_ok": int(ok),
        })
    missing_edge_refs = 0
    for r in staged_edge:
        for field in ["from_objid", "to_objid"]:
            ok = r.get(field, "") in allowed_objids
            missing_edge_refs += 0 if ok else 1
            ref_rows.append({
                "family": "DDEDGE",
                "row_id": r.get("edgeid", ""),
                "reference_field": field,
                "reference_value": r.get(field, ""),
                "reference_ok": int(ok),
            })

    apply_now_total = sum(int_field(r, "apply_now") for rows in [staged_obj, suppressed_obj, staged_attr, staged_edge, staged_evid, staged_gate, staged_index] for r in rows)

    target_counts = [
        {"target_table": "DDOBJECT", "staged_rows": len(staged_obj), "suppressed_existing_rows": len(suppressed_obj), "simulated_insert_rows": len(staged_obj), "apply_now": 0},
        {"target_table": "DDATTR", "staged_rows": len(staged_attr), "suppressed_existing_rows": 0, "simulated_insert_rows": len(staged_attr), "apply_now": 0},
        {"target_table": "DDEDGE", "staged_rows": len(staged_edge), "suppressed_existing_rows": 0, "simulated_insert_rows": len(staged_edge), "apply_now": 0},
        {"target_table": "DDEVID", "staged_rows": len(staged_evid), "suppressed_existing_rows": 0, "simulated_insert_rows": len(staged_evid), "apply_now": 0},
        {"target_table": "DDGATE", "staged_rows": len(staged_gate), "suppressed_existing_rows": 0, "simulated_insert_rows": len(staged_gate), "apply_now": 0},
    ]

    simulated_sequence = [
        {"step": 1, "phase": "verify", "description": "Verify staged files and green prerequisites.", "simulated_only": 1, "apply_now": 0},
        {"step": 2, "phase": "suppress", "description": "Keep 11 existing DDOBJECT catalog-table rows suppressed from insert.", "simulated_only": 1, "apply_now": 0},
        {"step": 3, "phase": "validate_refs", "description": "Validate DDATTR and DDEDGE references against active reused OBJIDs plus staged new OBJIDs.", "simulated_only": 1, "apply_now": 0},
        {"step": 4, "phase": "duplicate_check", "description": "Check staged DDOBJECT rows for active duplicate risk.", "simulated_only": 1, "apply_now": 0},
        {"step": 5, "phase": "simulate_counts", "description": "Compute target insert counts without opening DBFs for write.", "simulated_only": 1, "apply_now": 0},
        {"step": 6, "phase": "hold", "description": "Hold for explicit authorization before any future active-catalog mutation.", "simulated_only": 1, "apply_now": 0},
    ]

    duplicate_blockers = sum(1 for r in duplicate_risk_rows if r["active_duplicate_seen"] == 1)
    ref_failures = missing_attr_refs + missing_edge_refs
    staged_total = len(staged_index)
    simulated_insert_total = sum(r["simulated_insert_rows"] for r in target_counts)

    generated = out / "generated_simulated_apply_validation"
    generated.mkdir(parents=True, exist_ok=True)

    write_csv(generated / "dd096f_required_staged_files.csv", file_rows, ["required_file", "path", "exists", "bytes", "sha256"])
    write_csv(generated / "dd096f_target_row_counts.csv", target_counts, ["target_table", "staged_rows", "suppressed_existing_rows", "simulated_insert_rows", "apply_now"])
    write_csv(generated / "dd096f_ddobject_duplicate_risk.csv", duplicate_risk_rows, ["target_table", "staged_id", "staged_key", "active_duplicate_seen", "risk"])
    write_csv(generated / "dd096f_reference_validation.csv", ref_rows, ["family", "row_id", "reference_field", "reference_value", "reference_ok"])
    write_csv(generated / "dd096f_simulated_apply_sequence.csv", simulated_sequence, ["step", "phase", "description", "simulated_only", "apply_now"])

    validation_rows = [
        {"validation": "required_staged_files_present", "expected": len(REQUIRED_STAGED_FILES), "observed": sum(int(r["exists"]) for r in file_rows), "pass": int(sum(int(r["exists"]) for r in file_rows) == len(REQUIRED_STAGED_FILES))},
        {"validation": "staged_index_count", "expected": 151, "observed": staged_total, "pass": int(staged_total == 151)},
        {"validation": "simulated_insert_total", "expected": 151, "observed": simulated_insert_total, "pass": int(simulated_insert_total == 151)},
        {"validation": "suppressed_existing_objects", "expected": 11, "observed": len(suppressed_obj), "pass": int(len(suppressed_obj) == 11)},
        {"validation": "new_objects_only", "expected": 8, "observed": len(staged_obj), "pass": int(len(staged_obj) == 8)},
        {"validation": "ddobject_duplicate_blockers", "expected": 0, "observed": duplicate_blockers, "pass": int(duplicate_blockers == 0)},
        {"validation": "reference_failures", "expected": 0, "observed": ref_failures, "pass": int(ref_failures == 0)},
        {"validation": "apply_now_zero", "expected": 0, "observed": apply_now_total, "pass": int(apply_now_total == 0)},
        {"validation": "staging_rules_pass", "expected": len(staging_rules), "observed": sum(1 for r in staging_rules if str(r.get("pass", "")).strip() == "1"), "pass": int(sum(1 for r in staging_rules if str(r.get("pass", "")).strip() == "1") == len(staging_rules))},
    ]
    write_csv(generated / "dd096f_validation_ledger.csv", validation_rows, ["validation", "expected", "observed", "pass"])

    simulation_failures = sum(1 for r in validation_rows if int(r["pass"]) != 1)

    boundary_rows = [
        {"boundary": "staged_row_review_simulation_only", "observed": 1, "required": 1, "pass": 1},
        {"boundary": "apply_now_total", "observed": apply_now_total, "required": 0, "pass": int(apply_now_total == 0)},
        {"boundary": "active_catalog_mutation", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "dbf_append_replace_delete_pack_zap", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "cdx_lmdb_create_rebuild", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "cxx_source_edits", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "build_file_edits", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "registry_edits", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "help_meta_cmdhelpchk_mutation", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "catalog_regeneration", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "manual_row_repair", "observed": 0, "required": 0, "pass": 1},
    ]

    gates = [
        {"gate": "dd096e_ready", "expected": EXPECTED_DD096E_STATUS, "observed": dd096e.get("status", ""), "pass": int(dd096e.get("status") == EXPECTED_DD096E_STATUS)},
        {"gate": "dd096d_ready", "expected": EXPECTED_DD096D_STATUS, "observed": dd096d.get("status", ""), "pass": int(dd096d.get("status") == EXPECTED_DD096D_STATUS)},
        {"gate": "dd098_closed", "expected": EXPECTED_DD098_STATUS, "observed": dd098.get("status", ""), "pass": int(dd098.get("status") == EXPECTED_DD098_STATUS)},
        {"gate": "simulation_validations_pass", "expected": len(validation_rows), "observed": sum(int(r["pass"]) for r in validation_rows), "pass": int(simulation_failures == 0)},
        {"gate": "active_obj_dbf_parsed", "expected": 1, "observed": int(not active_obj_meta.get("parse_warning")), "pass": int(not active_obj_meta.get("parse_warning"))},
        {"gate": "apply_now_zero", "expected": 0, "observed": apply_now_total, "pass": int(apply_now_total == 0)},
    ]

    failures = sum(1 for r in gates if int(r["pass"]) != 1)
    status = "DATADICT_STAGED_ROW_SIMULATED_APPLY_VALIDATION_READY" if failures == 0 else "DATADICT_STAGED_ROW_SIMULATED_APPLY_VALIDATION_REVIEW"

    artifact_rows = [
        artifact_row(repo, str(dd096e_manifest_path.relative_to(repo)), "dd096e_manifest"),
        artifact_row(repo, str(dd096d_manifest_path.relative_to(repo)), "dd096d_manifest"),
        artifact_row(repo, str(dd098_manifest_path.relative_to(repo)), "dd098_manifest"),
        artifact_row(repo, args.staged_dir, "staged_dir"),
    ]
    for p in PROTECTED_ARTIFACTS:
        artifact_rows.append(artifact_row(repo, p, "protected_observed"))
    for f in sorted(generated.iterdir()):
        if f.is_file():
            artifact_rows.append({"role": "generated_simulation", "path": str(f), "exists": 1, "kind": "file", "bytes_or_children": f.stat().st_size, "sha256": sha256(f)})

    next_rows = [
        {"next_id": "DD096G", "title": "final guarded apply package design", "allowed_scope": "design only until explicit authorization"},
        {"next_id": "DD092D", "title": "guarded HELP/CMDHELPCHK apply planning", "allowed_scope": "only after explicit authorization"},
        {"next_id": "DD099", "title": "baseline-to-manual integration report", "allowed_scope": "documentation/explanation only"},
    ]

    write_csv(out / "dd096f_gate_ledger.csv", gates, ["gate", "expected", "observed", "pass"])
    write_csv(out / "dd096f_no_mutation_boundary_ledger.csv", boundary_rows, ["boundary", "observed", "required", "pass"])
    write_csv(out / "dd096f_artifact_ledger.csv", artifact_rows, ["role", "path", "exists", "kind", "bytes_or_children", "sha256"])
    write_csv(out / "dd096f_next_lane_recommendations.csv", next_rows, ["next_id", "title", "allowed_scope"])

    report = f"""# DD096F Staged-Row Review and Simulated Apply Validation

Run id: `{args.run_id}`
Status: **{status}**
Created UTC: `{utc_now()}`

## Purpose

DD096F validates the DD096E staged rows as if they were going to be applied, but only in memory/report form.

It is not an apply lane. It writes no active DBFs and performs no catalog mutation.

## Summary

- Staged row index: **{staged_total}**
- Simulated insert total: **{simulated_insert_total}**
- Suppressed existing DDOBJECT rows: **{len(suppressed_obj)}**
- Staged new DDOBJECT rows: **{len(staged_obj)}**
- DDOBJECT duplicate blockers: **{duplicate_blockers}**
- Reference failures: **{ref_failures}**
- Validation failures: **{simulation_failures}**
- apply_now total: **{apply_now_total}**

## Boundary

DD096F is staged-row-review/simulation-only. It does not edit C++ source, edit build files,
edit command registration, mutate active catalog DBFs, append/replace/delete/pack/zap DBFs,
create/rebuild CDX/LMDB, mutate HELP/META/CMDHELPCHK, regenerate catalog content, or repair manual rows.
"""
    write_text(out / "DD096F_STAGED_ROW_REVIEW_SIMULATED_APPLY_REPORT.md", report)

    manifest = {
        "contract": "dd096f_staged_row_review_simulated_apply_v0",
        "run_id": args.run_id,
        "created_utc": utc_now(),
        "status": status,
        "repo_root": str(repo),
        "profiles": args.profile,
        "staged_total": staged_total,
        "simulated_insert_total": simulated_insert_total,
        "suppressed_existing_objects": len(suppressed_obj),
        "staged_new_objects": len(staged_obj),
        "duplicate_blockers": duplicate_blockers,
        "reference_failures": ref_failures,
        "validation_failures": simulation_failures,
        "apply_now_total": apply_now_total,
        "failures": failures,
        "cxx_source_edits": 0,
        "build_file_edits": 0,
        "registry_edits": 0,
        "active_catalog_mutation": 0,
        "dbf_append_replace_delete_pack_zap": 0,
        "cdx_lmdb_create_rebuild": 0,
        "help_meta_cmdhelpchk_mutation": 0,
        "catalog_regeneration": 0,
        "manual_row_repair": 0,
        "next_recommended_action": "DD096G final guarded apply package design, still design-only unless explicitly authorized.",
    }
    write_json(out / "dd096f_staged_row_review_simulated_apply_manifest.json", manifest)

    print(f"DD096F staged-row review/simulated apply manifest: {out / 'dd096f_staged_row_review_simulated_apply_manifest.json'}")
    print(f"status: {status}; staged: {staged_total}; simulated_insert: {simulated_insert_total}; duplicate_blockers: {duplicate_blockers}; ref_failures: {ref_failures}; validation_failures: {simulation_failures}; apply_now: {apply_now_total}; failures: {failures}")
    return 2 if (args.fail_on_review and failures) else 0


if __name__ == "__main__":
    raise SystemExit(main())
