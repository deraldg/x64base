#!/usr/bin/env python3
"""
DD-040 report-only Catalog Row Projection Dry-Run.

Projects exact candidate CSV rows for the planned Data Dictionary catalog DBFs.
It does not create DBFs, write DBF rows, create CDX files, write LMDB data,
launch DotTalk++, mutate HELP/META/CMDHELPCHK, or promote catalog data.

Terminology:
- DDL/table definition describes structure.
- WORKSPACE describes live/open areas.
- This tool projects catalog rows from accepted evidence; it does not write catalog DBFs.
"""
from __future__ import annotations

import argparse
import csv
import datetime as _dt
import hashlib
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


CATALOG_TABLES = [
    "DDRUN", "DDBASE", "DDSOURCE", "DDOBJECT", "DDATTR", "DDEDGE",
    "DDEVID", "DDGATE", "DDREVIEW", "DDARTIF", "DDPROFILE"
]

PROFILE_ROWS = [
    {"PROFID": "ENGINE", "NAME": "ENGINE", "VISIBLE": "T", "NOTES": "Core x64base/Data Dictionary engine profile."},
    {"PROFID": "PROFESSIONAL", "NAME": "PROFESSIONAL", "VISIBLE": "T", "NOTES": "Professional/developer documentation profile."},
    {"PROFID": "OPTIONAL_OVERLAY", "NAME": "OPTIONAL_OVERLAY", "VISIBLE": "F", "NOTES": "Optional overlays such as educational/student/demo material."},
]


def utc_now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds")


def read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def stable_id(prefix: str, *parts: Any) -> str:
    raw = "|".join(str(p) for p in parts)
    return f"{prefix}_{hashlib.sha256(raw.encode('utf-8')).hexdigest()[:20].upper()}"


def relpath(repo: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(repo.resolve()).as_posix()
    except Exception:
        return path.as_posix()


def load_current_baseline(repo: Path, pointer_arg: str, baseline_arg: str) -> Tuple[str, Path, Path, Dict[str, Any]]:
    pointer_path = repo / pointer_arg
    pointer: Dict[str, Any] = {}
    baseline_id = baseline_arg
    baseline_dir = repo / "docs/datadict/baselines" / baseline_id
    manifest = baseline_dir / "dd027_baseline_acceptance_manifest.json"

    if pointer_path.exists():
        pointer = read_json(pointer_path)
        baseline_id = str(pointer.get("baseline_id") or baseline_id)
        baseline_dir = repo / str(pointer.get("baseline_path", f"docs/datadict/baselines/{baseline_id}"))
        manifest = repo / str(pointer.get("baseline_manifest", f"docs/datadict/baselines/{baseline_id}/dd027_baseline_acceptance_manifest.json"))

    data: Dict[str, Any] = {}
    if manifest.exists():
        data = read_json(manifest)
    return baseline_id, baseline_dir, manifest, data


def read_csv_dict(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: List[Dict[str, Any]], fields: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for row in rows:
            w.writerow({k: row.get(k, "") for k in fields})


def write_json(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def add_source(repo: Path, sources: Dict[str, Dict[str, Any]], path: Path, kind: str) -> str:
    rel = relpath(repo, path)
    sid = stable_id("SRC", rel)
    if sid not in sources:
        exists = path.exists()
        sources[sid] = {
            "SRCID": sid,
            "PATH": rel,
            "KIND": kind,
            "SHA256": sha256_file(path) if exists and path.is_file() else "",
            "BYTES": path.stat().st_size if exists and path.is_file() else "",
            "PROFILE": "ENGINE",
        }
    return sid


def main() -> int:
    ap = argparse.ArgumentParser(description="DD-040 report-only catalog row projection dry-run")
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--run-id", default="DD040-catalog-row-projection-v0")
    ap.add_argument("--baseline", default="DDBASE-stable-v2")
    ap.add_argument("--pointer", default="docs/datadict/baselines/current_baseline.json")
    ap.add_argument("--dd039-dir", default="docs/datadict/definitions")
    ap.add_argument("--profile", action="append", default=[])
    ap.add_argument("--fail-on-review", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    out = Path(args.out_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)

    baseline_id, baseline_dir, baseline_manifest, baseline_data = load_current_baseline(repo, args.pointer, args.baseline)
    fingerprint = str(baseline_data.get("fingerprint") or baseline_data.get("aggregate_fingerprint") or baseline_data.get("accepted_fingerprint") or "")

    dd039_dir = repo / args.dd039_dir
    table_defs = read_csv_dict(dd039_dir / "dd039_catalog_table_definition_plan_v0.csv")
    field_defs = read_csv_dict(dd039_dir / "dd039_catalog_field_definition_plan_v0.csv")
    tag_defs = read_csv_dict(dd039_dir / "dd039_catalog_tag_definition_plan_v0.csv")
    gate_defs = read_csv_dict(dd039_dir / "dd039_catalog_definition_gate_ledger_v0.csv")

    sources: Dict[str, Dict[str, Any]] = {}
    artifacts: Dict[str, Dict[str, Any]] = {}
    objects: Dict[str, Dict[str, Any]] = {}
    attrs: List[Dict[str, Any]] = []
    edges: List[Dict[str, Any]] = []
    evid: List[Dict[str, Any]] = []
    gates: List[Dict[str, Any]] = []
    reviews: List[Dict[str, Any]] = []

    evidence_paths = [
        baseline_manifest,
        repo / args.pointer,
        repo / "docs/datadict/reports/DD038-current-baseline-pointer-v0/dd038_current_baseline_pointer_manifest.json",
        repo / "docs/datadict/reports/DD037-status-closure-v2-v0/dd037_status_closure_manifest.json",
        repo / "docs/datadict/reports/DD034-check-DDBASE-stable-v2-current/dd034_daily_redoc_status_manifest.json",
        repo / "docs/datadict/review_queue/DD036-stable-v2-acceptance-artifact-accepted-v0/dd036_baseline_acceptance_artifact_closure_manifest.json",
        repo / "docs/datadict/reports/DD039-catalog-dbfdll-definition-v0/dd039_catalog_dbf_ddl_definition_manifest.json",
    ]

    run_rows: List[Dict[str, Any]] = []
    base_rows: List[Dict[str, Any]] = []

    created = utc_now()
    run_rows.append({
        "RUNID": args.run_id,
        "KIND": "CATALOG_ROW_PROJECTION_DRY_RUN",
        "STATUS": "CATALOG_ROW_PROJECTION_READY",
        "CREATEDUTC": created,
        "BASEID": baseline_id,
        "FINGER": fingerprint,
        "PROFILE": ",".join(args.profile) if args.profile else "ENGINE",
        "NOTES": "DD-040 projection only; no DBF writes."
    })

    if baseline_manifest.exists():
        srcid = add_source(repo, sources, baseline_manifest, "baseline_manifest")
        base_rows.append({
            "BASEID": baseline_id,
            "STATUS": str(baseline_data.get("status", "")),
            "FINGER": fingerprint,
            "RUNID": str(baseline_data.get("run_id", "")),
            "MANIFEST": relpath(repo, baseline_manifest),
            "PROFILE": ",".join(args.profile) if args.profile else "ENGINE",
            "NOTES": "Accepted baseline projected from DD-027 manifest."
        })
        evid.append({
            "EVID": stable_id("EVID", baseline_id, srcid),
            "OBJID": stable_id("OBJ", "BASELINE", baseline_id),
            "SRCID": srcid,
            "KIND": "BASELINE_ACCEPTANCE_EVIDENCE",
            "CONF": "1.00",
            "DETAIL": "Accepted baseline manifest evidence."
        })

    # Project catalog table objects
    for row in table_defs:
        table = row.get("table", "")
        if not table:
            continue
        objid = stable_id("OBJ", "CATALOG_TABLE", table)
        objects[objid] = {
            "OBJID": objid,
            "OBJTYPE": "CATALOG_TABLE",
            "NAME": table,
            "OWNER": "DATADICT_CATALOG",
            "STATUS": "PLANNED_DDL_DEFINITION",
            "PROFILE": row.get("profile", "ENGINE"),
            "SRCID": "",
        }
        attrs.append({
            "ATTRID": stable_id("ATTR", objid, "primary_key"),
            "OBJID": objid,
            "ATTRNAME": "primary_key",
            "ATTRVAL": row.get("primary_key", ""),
            "ATTRMEMO": "",
            "EVID": ""
        })
        attrs.append({
            "ATTRID": stable_id("ATTR", objid, "purpose"),
            "OBJID": objid,
            "ATTRNAME": "purpose",
            "ATTRVAL": row.get("purpose", "")[:240],
            "ATTRMEMO": row.get("purpose", ""),
            "EVID": ""
        })

    # Project field objects and edges
    for row in field_defs:
        table = row.get("table", "")
        field = row.get("field", "")
        if not table or not field:
            continue
        table_obj = stable_id("OBJ", "CATALOG_TABLE", table)
        field_obj = stable_id("OBJ", "CATALOG_FIELD", table, field)
        objects[field_obj] = {
            "OBJID": field_obj,
            "OBJTYPE": "CATALOG_FIELD",
            "NAME": field,
            "OWNER": table,
            "STATUS": "PLANNED_FIELD_DEFINITION",
            "PROFILE": "ENGINE",
            "SRCID": "",
        }
        edgeid = stable_id("EDGE", table_obj, "HAS_FIELD", field_obj)
        edges.append({"EDGEID": edgeid, "FROMOBJ": table_obj, "TOOBJ": field_obj, "EDGETYPE": "HAS_FIELD", "EVID": ""})
        for attr_name in ["type", "width", "decimals", "required", "description"]:
            attrs.append({
                "ATTRID": stable_id("ATTR", field_obj, attr_name),
                "OBJID": field_obj,
                "ATTRNAME": attr_name,
                "ATTRVAL": row.get(attr_name, "")[:240],
                "ATTRMEMO": row.get(attr_name, ""),
                "EVID": ""
            })

    # Project tag/index objects
    for row in tag_defs:
        table = row.get("table", "")
        tag = row.get("tag", "")
        if not table or not tag:
            continue
        table_obj = stable_id("OBJ", "CATALOG_TABLE", table)
        tag_obj = stable_id("OBJ", "CATALOG_TAG", table, tag)
        objects[tag_obj] = {
            "OBJID": tag_obj,
            "OBJTYPE": "CATALOG_TAG",
            "NAME": tag,
            "OWNER": table,
            "STATUS": "PLANNED_TAG_DEFINITION",
            "PROFILE": "ENGINE",
            "SRCID": "",
        }
        edges.append({"EDGEID": stable_id("EDGE", table_obj, "HAS_TAG", tag_obj), "FROMOBJ": table_obj, "TOOBJ": tag_obj, "EDGETYPE": "HAS_TAG", "EVID": ""})
        for attr_name in ["expression", "kind", "description"]:
            attrs.append({
                "ATTRID": stable_id("ATTR", tag_obj, attr_name),
                "OBJID": tag_obj,
                "ATTRNAME": attr_name,
                "ATTRVAL": row.get(attr_name, "")[:240],
                "ATTRMEMO": row.get(attr_name, ""),
                "EVID": ""
            })

    # Project evidence artifacts
    for ep in evidence_paths:
        if ep.exists():
            srcid = add_source(repo, sources, ep, "datadict_evidence_artifact")
            artid = stable_id("ART", relpath(repo, ep))
            artifacts[artid] = {
                "ARTID": artid,
                "RUNID": args.run_id,
                "PATH": relpath(repo, ep),
                "KIND": "DATADICT_EVIDENCE",
                "STATUS": "PROJECTED",
                "SHA256": sources[srcid]["SHA256"],
            }

    # Gates from DD-039 gate ledger
    for row in gate_defs:
        gateid = stable_id("GATE", args.run_id, row.get("gate", ""))
        gates.append({
            "GATEID": gateid,
            "RUNID": args.run_id,
            "GATENAME": row.get("gate", ""),
            "STATUS": "PROJECTED_NOT_EXECUTED",
            "DETAIL": row.get("requirement", "")
        })

    # Add projection review row if no baseline fingerprint
    if not fingerprint:
        reviews.append({
            "REVID": stable_id("REV", args.run_id, "missing_fingerprint"),
            "RUNID": args.run_id,
            "SEVERITY": "HIGH",
            "LANE": "datadict_catalog_projection",
            "PATH": relpath(repo, baseline_manifest),
            "ACTION": "Resolve missing accepted baseline fingerprint before DBF write",
            "DETAIL": "Projection can continue, but DBF write must be blocked until baseline fingerprint is present."
        })

    outputs = {
        "DDRUN": run_rows,
        "DDBASE": base_rows,
        "DDSOURCE": list(sources.values()),
        "DDOBJECT": list(objects.values()),
        "DDATTR": attrs,
        "DDEDGE": edges,
        "DDEVID": evid,
        "DDGATE": gates,
        "DDREVIEW": reviews,
        "DDARTIF": list(artifacts.values()),
        "DDPROFILE": PROFILE_ROWS,
    }

    fields = {
        "DDRUN": ["RUNID", "KIND", "STATUS", "CREATEDUTC", "BASEID", "FINGER", "PROFILE", "NOTES"],
        "DDBASE": ["BASEID", "STATUS", "FINGER", "RUNID", "MANIFEST", "PROFILE", "NOTES"],
        "DDSOURCE": ["SRCID", "PATH", "KIND", "SHA256", "BYTES", "PROFILE"],
        "DDOBJECT": ["OBJID", "OBJTYPE", "NAME", "OWNER", "STATUS", "PROFILE", "SRCID"],
        "DDATTR": ["ATTRID", "OBJID", "ATTRNAME", "ATTRVAL", "ATTRMEMO", "EVID"],
        "DDEDGE": ["EDGEID", "FROMOBJ", "TOOBJ", "EDGETYPE", "EVID"],
        "DDEVID": ["EVID", "OBJID", "SRCID", "KIND", "CONF", "DETAIL"],
        "DDGATE": ["GATEID", "RUNID", "GATENAME", "STATUS", "DETAIL"],
        "DDREVIEW": ["REVID", "RUNID", "SEVERITY", "LANE", "PATH", "ACTION", "DETAIL"],
        "DDARTIF": ["ARTID", "RUNID", "PATH", "KIND", "STATUS", "SHA256"],
        "DDPROFILE": ["PROFID", "NAME", "VISIBLE", "NOTES"],
    }

    for table in CATALOG_TABLES:
        write_csv(out / f"dd040_projected_{table}.csv", outputs[table], fields[table])

    row_counts = {table: len(outputs[table]) for table in CATALOG_TABLES}
    blocking = len([r for r in reviews if r.get("SEVERITY") == "HIGH"])
    status = "CATALOG_ROW_PROJECTION_READY" if blocking == 0 else "CATALOG_ROW_PROJECTION_REVIEW"

    manifest = {
        "contract": "dd040_catalog_row_projection_dry_run_v0",
        "run_id": args.run_id,
        "created_utc": utc_now(),
        "status": status,
        "repo_root": str(repo),
        "baseline": baseline_id,
        "fingerprint": fingerprint,
        "profiles": args.profile,
        "projected_tables": CATALOG_TABLES,
        "row_counts": row_counts,
        "total_projected_rows": sum(row_counts.values()),
        "blocking_review_rows": blocking,
        "dbf_write_authorized": 0,
        "dbf_tables_created": 0,
        "dbf_rows_written": 0,
        "cdx_created": 0,
        "lmdb_written": 0,
        "protected_system_mutations": 0,
        "next_recommended_package": "DD-041 Sandbox Catalog DBF Creation and Readback Smoke, only after explicit write authorization",
    }
    write_json(out / "dd040_projection_manifest.json", manifest)

    write_csv(out / "dd040_projection_row_counts.csv",
              [{"table": k, "rows": v} for k, v in row_counts.items()],
              ["table", "rows"])

    report = f"""# DD-040 Catalog Row Projection Dry-Run Report

Run id: `{args.run_id}`
Status: **{status}**
Created UTC: `{manifest['created_utc']}`

## Baseline

- Baseline: `{baseline_id}`
- Fingerprint: `{fingerprint}`

## Projected rows

Total projected rows: **{manifest['total_projected_rows']}**

| Table | Rows |
|---|---:|
""" + "\n".join(f"| {k} | {v} |" for k, v in row_counts.items()) + f"""

## Boundary

DD-040 is report-only. It does not create DBFs, write DBF rows, create CDX files,
write LMDB data, launch DotTalk++, mutate HELP/META/CMDHELPCHK, or promote
catalog data.

## Next

DD-041 may create sandbox catalog DBFs and perform readback only after explicit
write authorization.
"""
    (out / "DD040_CATALOG_ROW_PROJECTION_REPORT.md").write_text(report, encoding="utf-8")

    print(f"DD-040 projection manifest: {out / 'dd040_projection_manifest.json'}")
    print(f"status: {status}; total_projected_rows: {manifest['total_projected_rows']}; dbf_rows_written: 0; blocking: {blocking}")
    return 2 if (args.fail_on_review and status.endswith("REVIEW")) else 0


if __name__ == "__main__":
    raise SystemExit(main())
