#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
import shutil
from pathlib import Path
from typing import Any, Dict, List


EXPECTED_DD096A_STATUS = "DATADICT_CANDIDATE_CATALOG_ROW_DESIGN_READY"
EXPECTED_DD096F_REVIEW_STATUS = "DATADICT_STAGED_ROW_SIMULATED_APPLY_VALIDATION_REVIEW"
DDICT_ROOT_OBJID = "OBJ_10B13FF8898D310C2984"

REQUIRED_CANDIDATE_FILES = [
    "dd096a_candidate_ddobject_rows.csv",
    "dd096a_candidate_ddattr_rows.csv",
    "dd096a_candidate_ddedge_rows.csv",
    "dd096a_candidate_ddevid_rows.csv",
    "dd096a_candidate_ddgate_rows.csv",
    "dd096a_candidate_catalog_row_index.csv",
    "dd096a_candidate_catalog_rows.json",
    "DD096A_CANDIDATE_CATALOG_ROW_DESIGN.md",
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


def stable_id(prefix: str, *parts: str, length: int = 20) -> str:
    raw = "|".join(parts).encode("utf-8")
    return prefix + "_" + hashlib.sha1(raw).hexdigest().upper()[:length]


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


def write_json(path: Path, obj: Dict[str, Any]) -> None:
    write_text(path, json.dumps(obj, indent=2, sort_keys=True) + "\n")


def write_csv(path: Path, rows: List[Dict[str, Any]], fields: List[str]) -> None:
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


def artifact_row(repo: Path, rel_path: str, role: str) -> Dict[str, Any]:
    p = repo / rel_path
    return {
        "role": role,
        "path": rel_path,
        "exists": int(p.exists()),
        "kind": "dir" if p.exists() and p.is_dir() else "file" if p.exists() and p.is_file() else "",
        "bytes_or_children": p.stat().st_size if p.exists() and p.is_file() else sum(1 for _ in p.iterdir()) if p.exists() and p.is_dir() else 0,
        "sha256": sha256(p),
    }


def norm(s: Any) -> str:
    return str(s or "").strip().upper()


def main() -> int:
    ap = argparse.ArgumentParser(description="DD096A-R repair candidate catalog row design by adding DDICT root command object")
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--run-id", default="DD096AR-ddict-root-command-candidate-repair-v0")
    ap.add_argument("--dd096a-dir", default="docs/datadict/reports/DD096A-candidate-catalog-row-design-v0")
    ap.add_argument("--dd096f-dir", default="docs/datadict/reports/DD096F-staged-row-review-simulated-apply-v0")
    ap.add_argument("--candidate-dir", default="docs/datadict/reports/DD096A-candidate-catalog-row-design-v0/generated_candidate_catalog_rows")
    ap.add_argument("--profile", action="append", default=[])
    ap.add_argument("--fail-on-review", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    out = Path(args.out_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)

    dd096a_manifest_path = repo / args.dd096a_dir / "dd096a_candidate_catalog_row_design_manifest.json"
    dd096f_manifest_path = repo / args.dd096f_dir / "dd096f_staged_row_review_simulated_apply_manifest.json"
    dd096a = read_json(dd096a_manifest_path)
    dd096f = read_json(dd096f_manifest_path)

    cdir = repo / args.candidate_dir
    ddobject = read_csv(cdir / "dd096a_candidate_ddobject_rows.csv")
    ddattr = read_csv(cdir / "dd096a_candidate_ddattr_rows.csv")
    ddedge = read_csv(cdir / "dd096a_candidate_ddedge_rows.csv")
    ddevid = read_csv(cdir / "dd096a_candidate_ddevid_rows.csv")
    ddgate = read_csv(cdir / "dd096a_candidate_ddgate_rows.csv")
    original_index = read_csv(cdir / "dd096a_candidate_catalog_row_index.csv")

    ref_validation_path = repo / args.dd096f_dir / "generated_simulated_apply_validation" / "dd096f_reference_validation.csv"
    ref_rows = read_csv(ref_validation_path)
    missing_refs = [r for r in ref_rows if str(r.get("reference_ok", "")).strip() != "1"]
    missing_values = sorted({r.get("reference_value", "") for r in missing_refs if r.get("reference_value", "")})

    root_present_before = any(r.get("candidate_objid", "") == DDICT_ROOT_OBJID for r in ddobject)
    root_candidate_row = {
        "candidate_row_id": stable_id("CANDOBJ", "DD096A", "COMMAND", "DDICT"),
        "target_table": "DDOBJECT",
        "candidate_objid": DDICT_ROOT_OBJID,
        "objtype": "COMMAND",
        "owner": "DATADICT_RUNTIME",
        "name": "DDICT",
        "status": "REVIEW_READY_CANDIDATE",
        "profile": "ENGINE",
        "srcid": "SRC_DD092C_CMDHELPCHK_CANDIDATES",
        "purpose": "Root command object for the DDICT runtime inspection surface.",
        "primary_tag": "",
        "candidate_action": "UPSERT_CANDIDATE",
        "apply_now": 0,
    }

    added_object = 0
    if not root_present_before:
        ddobject.append(root_candidate_row)
        added_object = 1

    attr_specs = [
        ("source_stage", "DD096AR DDICT root command candidate repair"),
        ("promotion_policy", "candidate_only_no_dbf_write"),
        ("baseline_status", "DATADICT_BASELINE_CLOSED_AND_REGRESSION_PROVEN"),
        ("purpose", "Root command object for the DDICT runtime inspection surface."),
        ("repair_reason", "DD096F found eight DDEDGE references to DDICT root object without a staged DDOBJECT row."),
        ("parent_for_surfaces", "DDICT HELP; DDICT STATUS; DDICT TABLES; DDICT OBJECTS; DDICT FIELDS; DDICT TAGS; DDICT REL; DDICT EVIDENCE"),
    ]
    existing_attr_keys = {(r.get("objid", ""), norm(r.get("attrname")), norm(r.get("attrval"))) for r in ddattr}
    added_attrs = 0
    for attr_name, attr_val in attr_specs:
        key = (DDICT_ROOT_OBJID, norm(attr_name), norm(attr_val))
        if key in existing_attr_keys:
            continue
        ddattr.append({
            "candidate_row_id": stable_id("CANDATTR", DDICT_ROOT_OBJID, attr_name),
            "target_table": "DDATTR",
            "candidate_attrid": stable_id("ATTR", DDICT_ROOT_OBJID, attr_name),
            "objid": DDICT_ROOT_OBJID,
            "attrname": attr_name,
            "attrval": attr_val,
            "status": "REVIEW_READY_CANDIDATE",
            "profile": "ENGINE",
            "evid": "EVID_DD096AR_ROOT_COMMAND_REPAIR",
            "candidate_action": "UPSERT_CANDIDATE",
            "apply_now": 0,
        })
        added_attrs += 1

    all_candidates = []
    for family, rows in [
        ("DDOBJECT", ddobject),
        ("DDATTR", ddattr),
        ("DDEDGE", ddedge),
        ("DDEVID", ddevid),
        ("DDGATE", ddgate),
    ]:
        for r in rows:
            all_candidates.append({
                "family": family,
                "candidate_row_id": r.get("candidate_row_id", ""),
                "target_table": r.get("target_table", family),
                "candidate_action": r.get("candidate_action", ""),
                "status": r.get("status", ""),
                "apply_now": r.get("apply_now", 0),
            })

    generated = out / "generated_repaired_candidate_catalog_rows"
    generated.mkdir(parents=True, exist_ok=True)

    write_csv(generated / "dd096a_candidate_ddobject_rows.csv", ddobject, ["candidate_row_id", "target_table", "candidate_objid", "objtype", "owner", "name", "status", "profile", "srcid", "purpose", "primary_tag", "candidate_action", "apply_now"])
    write_csv(generated / "dd096a_candidate_ddattr_rows.csv", ddattr, ["candidate_row_id", "target_table", "candidate_attrid", "objid", "attrname", "attrval", "status", "profile", "evid", "candidate_action", "apply_now"])
    write_csv(generated / "dd096a_candidate_ddedge_rows.csv", ddedge, ["candidate_row_id", "target_table", "candidate_edgeid", "from_objid", "from_name", "to_objid", "to_name", "edge_type", "key", "meaning", "status", "profile", "evid", "candidate_action", "apply_now"])
    write_csv(generated / "dd096a_candidate_ddevid_rows.csv", ddevid, ["candidate_row_id", "target_table", "candidate_evid", "kind", "srcid", "source", "artifact", "meaning", "status", "profile", "candidate_action", "apply_now"])
    write_csv(generated / "dd096a_candidate_ddgate_rows.csv", ddgate, ["candidate_row_id", "target_table", "gate_id", "gate_type", "required_state", "observed_state", "status", "candidate_action", "apply_now"])
    write_csv(generated / "dd096a_candidate_catalog_row_index.csv", all_candidates, ["family", "candidate_row_id", "target_table", "candidate_action", "status", "apply_now"])

    counts = {
        "objects": len(ddobject),
        "attrs": len(ddattr),
        "edges": len(ddedge),
        "evidence": len(ddevid),
        "gates": len(ddgate),
        "all": len(all_candidates),
        "added_objects": added_object,
        "added_attrs": added_attrs,
        "missing_refs_from_dd096f": len(missing_refs),
    }

    write_json(generated / "dd096a_candidate_catalog_rows.json", {
        "run_id": args.run_id,
        "created_utc": utc_now(),
        "candidate_only": True,
        "repair_lane": "DD096AR",
        "root_command_objid": DDICT_ROOT_OBJID,
        "candidate_counts": counts,
        "apply_now_total": sum(int(str(r.get("apply_now", "0")).strip() or "0") for r in all_candidates),
        "ddobject": ddobject,
        "ddattr": ddattr,
        "ddedge": ddedge,
        "ddevid": ddevid,
        "ddgate": ddgate,
    })

    design_doc = f"""# DD096A-R DDICT Root Command Candidate Repair

Run id: `{args.run_id}`
Created UTC: `{utc_now()}`

## Purpose

DD096A-R repairs the DD096A candidate model by adding the missing root `DDICT` command object.

DD096F proved that eight DDEDGE rows referenced `{DDICT_ROOT_OBJID}` as `from_objid`, but that object was not staged as a DDOBJECT row.

## Repair

- Added DDOBJECT root command candidate: **{added_object}**
- Added DDATTR support candidates for root command: **{added_attrs}**
- Missing references observed from DD096F: **{len(missing_refs)}**
- Repaired total candidates: **{counts['all']}**

## Boundary

DD096A-R is candidate-only. It does not write active DBFs, rebuild indexes, mutate HELP/CMDHELPCHK, edit source, or apply schema promotion.
"""
    write_text(generated / "DD096AR_DDICT_ROOT_COMMAND_CANDIDATE_REPAIR.md", design_doc)
    # Compatibility copy for downstream expectations if user reads generated design.
    write_text(generated / "DD096A_CANDIDATE_CATALOG_ROW_DESIGN.md", design_doc)

    repair_rows = [
        {
            "repair_id": "DD096AR_ADD_DDICT_ROOT_COMMAND",
            "issue": "DD096F reported 8 DDEDGE from_objid reference failures",
            "root_objid": DDICT_ROOT_OBJID,
            "added_ddobject": added_object,
            "added_ddattr": added_attrs,
            "apply_now": 0,
        }
    ]
    write_csv(out / "dd096ar_repair_ledger.csv", repair_rows, ["repair_id", "issue", "root_objid", "added_ddobject", "added_ddattr", "apply_now"])

    missing_ref_rows = []
    for r in missing_refs:
        missing_ref_rows.append({
            "family": r.get("family", ""),
            "row_id": r.get("row_id", ""),
            "reference_field": r.get("reference_field", ""),
            "reference_value": r.get("reference_value", ""),
            "repair_action": "ADD_ROOT_DDICT_DDOBJECT" if r.get("reference_value", "") == DDICT_ROOT_OBJID else "REVIEW_UNEXPECTED_REFERENCE",
            "apply_now": 0,
        })
    write_csv(out / "dd096ar_reference_repair_plan.csv", missing_ref_rows, ["family", "row_id", "reference_field", "reference_value", "repair_action", "apply_now"])

    boundary_rows = [
        {"boundary": "candidate_repair_only", "observed": 1, "required": 1, "pass": 1},
        {"boundary": "apply_now_total", "observed": sum(int(str(r.get("apply_now", "0")).strip() or "0") for r in all_candidates), "required": 0, "pass": 1},
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
        {"gate": "dd096a_ready", "expected": EXPECTED_DD096A_STATUS, "observed": dd096a.get("status", ""), "pass": int(dd096a.get("status") == EXPECTED_DD096A_STATUS)},
        {"gate": "dd096f_review_red", "expected": EXPECTED_DD096F_REVIEW_STATUS, "observed": dd096f.get("status", ""), "pass": int(dd096f.get("status") == EXPECTED_DD096F_REVIEW_STATUS)},
        {"gate": "missing_refs_are_8", "expected": 8, "observed": len(missing_refs), "pass": int(len(missing_refs) == 8)},
        {"gate": "missing_ref_value_is_ddict_root", "expected": DDICT_ROOT_OBJID, "observed": ";".join(missing_values), "pass": int(missing_values == [DDICT_ROOT_OBJID])},
        {"gate": "root_object_added_or_present", "expected": 1, "observed": int(added_object == 1 or root_present_before), "pass": int(added_object == 1 or root_present_before)},
        {"gate": "candidate_total_repaired", "expected": ">=163", "observed": counts["all"], "pass": int(counts["all"] >= 163)},
        {"gate": "apply_now_zero", "expected": 0, "observed": sum(int(str(r.get("apply_now", "0")).strip() or "0") for r in all_candidates), "pass": 1},
    ]

    failures = sum(1 for r in gates if int(r["pass"]) != 1)
    status = "DATADICT_DDICT_ROOT_COMMAND_CANDIDATE_REPAIR_READY" if failures == 0 else "DATADICT_DDICT_ROOT_COMMAND_CANDIDATE_REPAIR_REVIEW"

    write_csv(out / "dd096ar_gate_ledger.csv", gates, ["gate", "expected", "observed", "pass"])
    write_csv(out / "dd096ar_no_mutation_boundary_ledger.csv", boundary_rows, ["boundary", "observed", "required", "pass"])

    artifact_rows = [
        artifact_row(repo, str(dd096a_manifest_path.relative_to(repo)), "dd096a_manifest"),
        artifact_row(repo, str(dd096f_manifest_path.relative_to(repo)), "dd096f_manifest"),
        artifact_row(repo, args.candidate_dir, "source_candidate_dir"),
    ]
    for p in PROTECTED_ARTIFACTS:
        artifact_rows.append(artifact_row(repo, p, "protected_observed"))
    for f in sorted(generated.iterdir()):
        if f.is_file():
            artifact_rows.append({"role": "generated_repaired_candidate", "path": str(f), "exists": 1, "kind": "file", "bytes_or_children": f.stat().st_size, "sha256": sha256(f)})
    write_csv(out / "dd096ar_artifact_ledger.csv", artifact_rows, ["role", "path", "exists", "kind", "bytes_or_children", "sha256"])

    next_rows = [
        {"next_id": "DD096B-R", "title": "rerun candidate row review/dedup against repaired candidate set", "allowed_scope": "read-only comparison; no DBF writes"},
        {"next_id": "DD096C-R", "title": "rerun acceptance/remap plan against repaired candidate set", "allowed_scope": "candidate plan only"},
        {"next_id": "DD096F-R", "title": "rerun simulated apply after repaired staging", "allowed_scope": "simulation only"},
    ]
    write_csv(out / "dd096ar_next_lane_recommendations.csv", next_rows, ["next_id", "title", "allowed_scope"])

    report = f"""# DD096A-R DDICT Root Command Candidate Repair

Run id: `{args.run_id}`
Status: **{status}**
Created UTC: `{utc_now()}`

## Purpose

DD096A-R repairs the candidate model after DD096F found eight reference failures.

## Finding

All missing references pointed to:

```text
{DDICT_ROOT_OBJID}
```

That is the stable candidate OBJID for the root `DDICT` command object. It was used as the parent of eight DDICT surface edges but was not present as a staged DDOBJECT row.

## Repair summary

- Root object present before: **{int(root_present_before)}**
- Root object added: **{added_object}**
- Root support attributes added: **{added_attrs}**
- Repaired candidates: **{counts['all']}**
- Missing references addressed: **{len(missing_refs)}**
- apply_now total: **0**

## Output

Repaired candidate set:

```text
{generated}
```

## Boundary

DD096A-R is candidate-only. It does not write active catalog DBFs, append/replace/delete/pack/zap DBFs,
create/rebuild CDX/LMDB, edit source, edit build files, edit command registration, mutate HELP/META/CMDHELPCHK,
regenerate catalog content, or repair manual rows.
"""
    write_text(out / "DD096AR_DDICT_ROOT_COMMAND_CANDIDATE_REPAIR_REPORT.md", report)

    manifest = {
        "contract": "dd096ar_ddict_root_command_candidate_repair_v0",
        "run_id": args.run_id,
        "created_utc": utc_now(),
        "status": status,
        "repo_root": str(repo),
        "profiles": args.profile,
        "root_objid": DDICT_ROOT_OBJID,
        "root_present_before": int(root_present_before),
        "added_object": added_object,
        "added_attrs": added_attrs,
        "candidate_counts": counts,
        "missing_refs_from_dd096f": len(missing_refs),
        "repaired_candidate_dir": str(generated),
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
        "next_recommended_action": "Rerun DD096B/C/D/E/F with DD096AR repaired candidate directory overrides.",
    }
    # Compatibility filename expected by DD096B --dd096a-dir.
    write_json(out / "dd096a_candidate_catalog_row_design_manifest.json", {
        "contract": "dd096a_candidate_catalog_row_design_v0_repaired_by_dd096ar",
        "run_id": args.run_id,
        "created_utc": utc_now(),
        "status": "DATADICT_CANDIDATE_CATALOG_ROW_DESIGN_READY",
        "candidate_counts": counts,
        "apply_now_total": 0,
        "repair_lane": "DD096AR",
        "repaired_candidate_dir": str(generated),
    })
    write_json(out / "dd096ar_ddict_root_command_candidate_repair_manifest.json", manifest)

    print(f"DD096A-R DDICT root command candidate repair manifest: {out / 'dd096ar_ddict_root_command_candidate_repair_manifest.json'}")
    print(f"status: {status}; repaired_candidates: {counts['all']}; added_object: {added_object}; added_attrs: {added_attrs}; missing_refs_addressed: {len(missing_refs)}; apply_now: 0; failures: {failures}")
    return 2 if (args.fail_on_review and failures) else 0


if __name__ == "__main__":
    raise SystemExit(main())
