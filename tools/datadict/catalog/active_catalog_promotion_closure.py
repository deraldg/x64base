#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import datetime as _dt
import hashlib
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Tuple


TABLES = [
    "DDRUN",
    "DDBASE",
    "DDSOURCE",
    "DDOBJECT",
    "DDATTR",
    "DDEDGE",
    "DDEVID",
    "DDGATE",
    "DDREVIEW",
    "DDARTIF",
    "DDPROFILE",
]

EXPECTED_COUNTS = {
    "DDRUN": 1,
    "DDBASE": 1,
    "DDSOURCE": 7,
    "DDOBJECT": 100,
    "DDATTR": 423,
    "DDEDGE": 89,
    "DDEVID": 1,
    "DDGATE": 6,
    "DDREVIEW": 0,
    "DDARTIF": 7,
    "DDPROFILE": 3,
}

RUNTIME_REP_TAGS = [
    ("DDRUN", "RUNID"),
    ("DDBASE", "BASEID"),
    ("DDOBJECT", "OBJID"),
    ("DDATTR", "OBJID"),
    ("DDEDGE", "FROMOBJ"),
    ("DDGATE", "STATUS"),
    ("DDPROFILE", "NAME"),
]


def utc_now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds")


def read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8", errors="replace"))


def read_csv_dict(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8", errors="replace") as f:
        return list(csv.DictReader(f))


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


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def dir_summary(path: Path) -> Tuple[int, int, str]:
    if not path.exists() or not path.is_dir():
        return 0, 0, ""
    files = 0
    total = 0
    h = hashlib.sha256()
    for p in sorted(path.rglob("*"), key=lambda q: q.as_posix().lower()):
        if p.is_file():
            files += 1
            b = p.read_bytes()
            total += len(b)
            h.update(p.relative_to(path).as_posix().encode("utf-8"))
            h.update(b)
    return files, total, h.hexdigest()


def safe_rel(repo: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(repo.resolve()).as_posix()
    except Exception:
        return path.as_posix()


def validate_dd058(dd058_dir: Path) -> Dict[str, Any]:
    manifest = read_json(dd058_dir / "dd058_controlled_active_catalog_promotion_manifest.json")
    backup = read_csv_dict(dd058_dir / "dd058_backup_ledger.csv")
    copy_rows = read_csv_dict(dd058_dir / "dd058_promotion_copy_ledger.csv")
    pydt = read_csv_dict(dd058_dir / "dd058_post_promotion_pydottalk_readback.csv")
    gates = read_csv_dict(dd058_dir / "dd058_gate_ledger.csv")
    boundary = read_csv_dict(dd058_dir / "dd058_no_mutation_boundary_ledger.csv")

    pydt_pass = True
    pydt_rows = 0
    for r in pydt:
        table = (r.get("table") or "").strip().upper()
        if table:
            pydt_rows += 1
        if str(r.get("row_count_match", "")).strip() != "1":
            pydt_pass = False

    gate_pass = all(str(r.get("pass", "")).strip() == "1" for r in gates) if gates else False
    boundary_pass = all(str(r.get("pass", "")).strip() == "1" for r in boundary) if boundary else False
    copy_required_fail = [
        r for r in copy_rows
        if str(r.get("required", "0")).strip() == "1" and str(r.get("action", "")).strip().upper() != "COPIED"
    ]

    return {
        "manifest": manifest,
        "backup_rows": len(backup),
        "copy_rows": len(copy_rows),
        "pydottalk_rows": pydt_rows,
        "pydottalk_pass": int(pydt_pass and pydt_rows == len(TABLES)),
        "gate_pass": int(gate_pass),
        "boundary_pass": int(boundary_pass),
        "copy_required_failures": len(copy_required_fail),
        "backup_dir": manifest.get("backup_dir", ""),
        "restore_script": manifest.get("restore_script", ""),
    }


def analyze_runtime_proof(proof_path: Path) -> Dict[str, Any]:
    if not proof_path.exists():
        return {
            "proof_exists": 0,
            "status": "MISSING_RUNTIME_PROOF",
            "mode_lmdb_hits": 0,
            "representative_hits": 0,
            "detail": f"missing proof file: {proof_path}",
        }

    text = proof_path.read_text(encoding="utf-8", errors="replace")
    upper = text.upper()
    mode_lmdb_hits = upper.count("MODE LMDB")
    set_index_hits = upper.count("SET INDEX")
    set_order_hits = upper.count("SET ORDER")
    active_path_seen = int("METADATA\\DATADICT" in upper or "METADATA/DATADICT" in upper)

    rep_rows: List[Dict[str, Any]] = []
    representative_hits = 0
    for table, tag in RUNTIME_REP_TAGS:
        table_seen = table in upper or table.lower() in text
        tag_seen = f"TAG '{tag}'" in upper or f"TAG {tag}" in upper or f"TAG={tag}" in upper
        lmdb_near = "MODE LMDB" in upper
        accepted = int(table_seen and tag_seen and lmdb_near)
        representative_hits += accepted
        rep_rows.append({
            "table": table,
            "tag": tag,
            "table_seen": int(table_seen),
            "tag_seen": int(tag_seen),
            "mode_lmdb_seen": int(lmdb_near),
            "accepted": accepted,
        })

    accepted = int(mode_lmdb_hits >= 5 and representative_hits >= 5)
    status = "ACTIVE_RUNTIME_INDEXED_LMDB_PROOF_ACCEPTED" if accepted else "ACTIVE_RUNTIME_INDEXED_LMDB_PROOF_REVIEW"
    return {
        "proof_exists": 1,
        "status": status,
        "mode_lmdb_hits": mode_lmdb_hits,
        "set_index_hits": set_index_hits,
        "set_order_hits": set_order_hits,
        "active_path_seen": active_path_seen,
        "representative_hits": representative_hits,
        "expected_representative_hits": len(RUNTIME_REP_TAGS),
        "sha256": sha256_file(proof_path),
        "rep_rows": rep_rows,
    }


def inventory_active(repo: Path, active_path: Path, index_path: Path, lmdb_path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for table in TABLES:
        stem = table.lower()
        for kind, path in [
            ("DBF", active_path / f"{stem}.dbf"),
            ("DTX", active_path / f"{stem}.dtx"),
            ("CDX", index_path / f"{stem}.cdx"),
            ("LMDB", lmdb_path / f"{stem}.cdx.d"),
        ]:
            if path.is_file():
                rows.append({
                    "table": table,
                    "kind": kind,
                    "path": safe_rel(repo, path),
                    "exists": 1,
                    "bytes": path.stat().st_size,
                    "sha256": sha256_file(path),
                    "file_count": "",
                })
            elif path.is_dir():
                files, total, digest = dir_summary(path)
                rows.append({
                    "table": table,
                    "kind": kind,
                    "path": safe_rel(repo, path),
                    "exists": 1,
                    "bytes": total,
                    "sha256": digest,
                    "file_count": files,
                })
            else:
                rows.append({
                    "table": table,
                    "kind": kind,
                    "path": safe_rel(repo, path),
                    "exists": 0,
                    "bytes": "",
                    "sha256": "",
                    "file_count": "",
                })
    return rows


def build_runtime_proof_template() -> str:
    return """DD-058 LOCAL ACTIVE CATALOG RUNTIME PROOF

Date: 2026-05-27
Repo: D:\\code\\ccode

Runtime command:
  DO D:\\code\\ccode\\docs\\datadict\\reports\\DD058-controlled-active-catalog-promotion-execute-v0\\dd058_post_promotion_runtime_verify.dts

Expected evidence:
  USE active metadata\\datadict tables.
  SET INDEX TO <table> attaches <table>.cdx.
  SET ORDER TO TAG <tag> selects an active tag.
  LIST reports MODE LMDB.

Representative tags:
  DDRUN.RUNID
  DDBASE.BASEID
  DDOBJECT.OBJID
  DDATTR.OBJID
  DDEDGE.FROMOBJ
  DDGATE.STATUS
  DDPROFILE.NAME

Result:
  PENDING
"""


def main() -> int:
    ap = argparse.ArgumentParser(description="DD-059 report-only active catalog promotion closure")
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--run-id", default="DD059-active-catalog-promotion-closure-v0")
    ap.add_argument("--active-path", default="dottalkpp/data/metadata/datadict")
    ap.add_argument("--index-path", default="dottalkpp/data/indexes")
    ap.add_argument("--lmdb-path", default="dottalkpp/data/lmdb")
    ap.add_argument("--dd058-dir", default="docs/datadict/reports/DD058-controlled-active-catalog-promotion-execute-v0")
    ap.add_argument("--runtime-proof", default="docs/datadict/runlog/DD-058_LOCAL_ACTIVE_CATALOG_RUNTIME_PROOF.md")
    ap.add_argument("--write-proof-template", action="store_true")
    ap.add_argument("--profile", action="append", default=[])
    ap.add_argument("--fail-on-review", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    out = Path(args.out_dir).resolve()
    active_path = (repo / args.active_path).resolve()
    index_path = (repo / args.index_path).resolve()
    lmdb_path = (repo / args.lmdb_path).resolve()
    dd058_dir = (repo / args.dd058_dir).resolve()
    runtime_proof = (repo / args.runtime_proof).resolve()
    out.mkdir(parents=True, exist_ok=True)

    if args.write_proof_template:
        runtime_proof.parent.mkdir(parents=True, exist_ok=True)
        if not runtime_proof.exists():
            runtime_proof.write_text(build_runtime_proof_template(), encoding="utf-8")

    dd058 = validate_dd058(dd058_dir)
    runtime = analyze_runtime_proof(runtime_proof)
    active_rows = inventory_active(repo, active_path, index_path, lmdb_path)

    active_dbf_count = sum(1 for r in active_rows if r["kind"] == "DBF" and r["exists"] == 1)
    active_cdx_count = sum(1 for r in active_rows if r["kind"] == "CDX" and r["exists"] == 1)
    active_lmdb_count = sum(1 for r in active_rows if r["kind"] == "LMDB" and r["exists"] == 1)

    dd058_status_ok = dd058["manifest"].get("status") == "ACTIVE_CATALOG_PROMOTION_EXECUTED_AND_VERIFIED"
    runtime_ok = runtime.get("status") == "ACTIVE_RUNTIME_INDEXED_LMDB_PROOF_ACCEPTED"

    gate_rows = [
        {
            "gate": "dd058_executed_and_verified",
            "expected": "ACTIVE_CATALOG_PROMOTION_EXECUTED_AND_VERIFIED",
            "observed": dd058["manifest"].get("status", ""),
            "pass": int(dd058_status_ok),
        },
        {
            "gate": "dd058_pydottalk_readback_pass",
            "expected": 1,
            "observed": dd058["pydottalk_pass"],
            "pass": int(dd058["pydottalk_pass"] == 1),
        },
        {
            "gate": "dd058_backup_created",
            "expected": ">=1",
            "observed": dd058["backup_rows"],
            "pass": int(dd058["backup_rows"] >= 1),
        },
        {
            "gate": "dd058_required_copy_failures",
            "expected": 0,
            "observed": dd058["copy_required_failures"],
            "pass": int(dd058["copy_required_failures"] == 0),
        },
        {
            "gate": "active_runtime_lmdb_proof",
            "expected": "ACTIVE_RUNTIME_INDEXED_LMDB_PROOF_ACCEPTED",
            "observed": runtime.get("status", ""),
            "pass": int(runtime_ok),
        },
        {
            "gate": "active_dbf_count",
            "expected": len(TABLES),
            "observed": active_dbf_count,
            "pass": int(active_dbf_count == len(TABLES)),
        },
        {
            "gate": "active_cdx_count",
            "expected": len(TABLES),
            "observed": active_cdx_count,
            "pass": int(active_cdx_count == len(TABLES)),
        },
        {
            "gate": "active_lmdb_count",
            "expected": len(TABLES),
            "observed": active_lmdb_count,
            "pass": int(active_lmdb_count == len(TABLES)),
        },
    ]

    boundary_rows = [
        {"boundary": "closure_report_only", "observed": 1, "required": 1, "pass": 1},
        {"boundary": "active_catalog_mutation_by_dd059", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "source_edits", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "help_meta_cmdhelpchk_mutation", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "catalog_regeneration", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "manual_row_repair", "observed": 0, "required": 0, "pass": 1},
    ]

    failures = sum(1 for r in gate_rows if int(r["pass"]) != 1)
    status = "ACTIVE_CATALOG_PROMOTION_CLOSURE_GREEN" if failures == 0 else "ACTIVE_CATALOG_PROMOTION_CLOSURE_REVIEW"

    write_csv(out / "dd059_gate_ledger.csv", gate_rows, ["gate", "expected", "observed", "pass"])
    write_csv(out / "dd059_no_mutation_boundary_ledger.csv", boundary_rows, ["boundary", "observed", "required", "pass"])
    write_csv(out / "dd059_active_artifact_inventory.csv", active_rows, ["table", "kind", "path", "exists", "bytes", "sha256", "file_count"])
    write_csv(out / "dd059_runtime_representative_tag_ledger.csv", runtime.get("rep_rows", []), ["table", "tag", "table_seen", "tag_seen", "mode_lmdb_seen", "accepted"])

    runtime_json = {k: v for k, v in runtime.items() if k != "rep_rows"}
    write_json(out / "dd059_runtime_proof_analysis.json", runtime_json)

    closure_summary = {
        "active_catalog_state": "ACTIVE_DATA_DICTIONARY_CATALOG_PROMOTED_AND_RUNTIME_VERIFIED" if failures == 0 else "ACTIVE_DATA_DICTIONARY_CATALOG_PROMOTION_REVIEW",
        "dd058_status": dd058["manifest"].get("status", ""),
        "backup_dir": dd058.get("backup_dir", ""),
        "restore_script": dd058.get("restore_script", ""),
        "active_dbf_count": active_dbf_count,
        "active_cdx_count": active_cdx_count,
        "active_lmdb_count": active_lmdb_count,
        "runtime_proof": str(runtime_proof),
        "runtime_proof_status": runtime.get("status", ""),
        "mode_lmdb_hits": runtime.get("mode_lmdb_hits", 0),
    }
    write_json(out / "dd059_active_catalog_closure_summary.json", closure_summary)

    manifest = {
        "contract": "dd059_active_catalog_promotion_closure_v0",
        "run_id": args.run_id,
        "created_utc": utc_now(),
        "status": status,
        "repo_root": str(repo),
        "profiles": args.profile,
        "dd058_dir": str(dd058_dir),
        "dd058_status": dd058["manifest"].get("status", ""),
        "runtime_proof": str(runtime_proof),
        "runtime_proof_status": runtime.get("status", ""),
        "backup_dir": dd058.get("backup_dir", ""),
        "restore_script": dd058.get("restore_script", ""),
        "active_dbf_count": active_dbf_count,
        "active_cdx_count": active_cdx_count,
        "active_lmdb_count": active_lmdb_count,
        "failures": failures,
        "active_catalog_mutation_by_dd059": 0,
        "source_edits": 0,
        "help_meta_cmdhelpchk_mutation": 0,
        "catalog_regeneration": 0,
        "manual_row_repair": 0,
        "next_recommended_action": "DD-060 active Data Dictionary consumer/read API plan or hold and begin documentation update.",
    }
    write_json(out / "dd059_active_catalog_promotion_closure_manifest.json", manifest)

    report = f"""# DD-059 Active Catalog Promotion Closure

Run id: `{args.run_id}`
Status: **{status}**
Created UTC: `{manifest['created_utc']}`

## Purpose

DD-059 closes the controlled active Data Dictionary catalog promotion cycle.

## Inputs

- DD-058 status: `{dd058["manifest"].get("status", "")}`
- Runtime proof: `{safe_rel(repo, runtime_proof)}`
- Runtime proof status: `{runtime.get("status", "")}`

## Active catalog closure state

```text
{closure_summary["active_catalog_state"]}
```

## Artifact counts

- Active DBFs: **{active_dbf_count}**
- Active CDX containers: **{active_cdx_count}**
- Active LMDB environments: **{active_lmdb_count}**
- MODE LMDB hits in runtime proof: **{runtime.get("mode_lmdb_hits", 0)}**

## Backup / rollback

- Backup directory: `{dd058.get("backup_dir", "")}`
- Restore script: `{dd058.get("restore_script", "")}`

## Boundary

DD-059 is report-only. It does not mutate active catalog files, source,
HELP/META/CMDHELPCHK, catalog content, or rows.
"""
    (out / "DD059_ACTIVE_CATALOG_PROMOTION_CLOSURE_REPORT.md").write_text(report, encoding="utf-8")

    print(f"DD-059 active catalog promotion closure manifest: {out / 'dd059_active_catalog_promotion_closure_manifest.json'}")
    print(f"status: {status}; failures: {failures}; active_dbf: {active_dbf_count}; cdx: {active_cdx_count}; lmdb: {active_lmdb_count}; runtime_proof: {runtime.get('status', '')}")
    return 2 if (args.fail_on_review and failures) else 0


if __name__ == "__main__":
    raise SystemExit(main())
