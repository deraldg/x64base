#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import datetime as _dt
import json
from pathlib import Path
from typing import Any, Dict, List


TAG_PLAN = {
    "DDRUN": [
        ("RUNID", "RUNID", "primary run id"),
        ("BASEID", "BASEID", "baseline id lookup"),
        ("STATUS", "STATUS", "status lookup"),
    ],
    "DDBASE": [
        ("BASEID", "BASEID", "primary baseline id"),
        ("RUNID", "RUNID", "acceptance run lookup"),
        ("STATUS", "STATUS", "baseline status lookup"),
    ],
    "DDSOURCE": [
        ("SRCID", "SRCID", "primary source id"),
        ("SHA256", "SHA256", "content hash lookup"),
        ("KIND", "KIND", "source kind lookup"),
    ],
    "DDOBJECT": [
        ("OBJID", "OBJID", "primary object id"),
        ("OBJTYPE", "OBJTYPE", "object type lookup"),
        ("SRCID", "SRCID", "source-object lookup"),
        ("NAME", "NAME", "object name lookup"),
    ],
    "DDATTR": [
        ("ATTRID", "ATTRID", "primary attribute id"),
        ("OBJID", "OBJID", "object attributes lookup"),
        ("ATTRNAME", "ATTRNAME", "attribute name lookup"),
        ("EVID", "EVID", "evidence lookup"),
    ],
    "DDEDGE": [
        ("EDGEID", "EDGEID", "primary edge id"),
        ("FROMOBJ", "FROMOBJ", "outgoing edges lookup"),
        ("TOOBJ", "TOOBJ", "incoming edges lookup"),
        ("EDGETYPE", "EDGETYPE", "edge type lookup"),
    ],
    "DDEVID": [
        ("EVID", "EVID", "primary evidence id"),
        ("OBJID", "OBJID", "object evidence lookup"),
        ("SRCID", "SRCID", "source evidence lookup"),
        ("KIND", "KIND", "evidence kind lookup"),
    ],
    "DDGATE": [
        ("GATEID", "GATEID", "primary gate id"),
        ("RUNID", "RUNID", "run gate lookup"),
        ("GATENAME", "GATENAME", "gate name lookup"),
        ("STATUS", "STATUS", "gate status lookup"),
    ],
    "DDREVIEW": [
        ("REVID", "REVID", "primary review id"),
        ("RUNID", "RUNID", "run review lookup"),
        ("SEVERITY", "SEVERITY", "severity lookup"),
        ("LANE", "LANE", "lane lookup"),
    ],
    "DDARTIF": [
        ("ARTID", "ARTID", "primary artifact id"),
        ("RUNID", "RUNID", "run artifact lookup"),
        ("KIND", "KIND", "artifact kind lookup"),
        ("STATUS", "STATUS", "artifact status lookup"),
    ],
    "DDPROFILE": [
        ("PROFID", "PROFID", "primary profile id"),
        ("NAME", "NAME", "profile name lookup"),
        ("VISIBLE", "VISIBLE", "visibility lookup"),
    ],
}

TABLE_ORDER = list(TAG_PLAN.keys())


def utc_now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds")


def read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8", errors="replace"))


def write_json(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def read_csv_dict(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8", errors="replace") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: List[Dict[str, Any]], fields: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        w.writeheader()
        for row in rows:
            w.writerow({k: row.get(k, "") for k in fields})


def safe_rel(repo: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(repo.resolve()).as_posix()
    except Exception:
        return path.as_posix()


def build_field_map(dd053_dir: Path) -> Dict[str, set[str]]:
    rows = read_csv_dict(dd053_dir / "dd053_field_descriptor_ledger.csv")
    out: Dict[str, set[str]] = {}
    for r in rows:
        table = (r.get("table") or "").strip().upper()
        name = (r.get("name") or "").strip().upper()
        if not table or not name:
            continue
        out.setdefault(table, set()).add(name)
    return out


def build_row_counts(dd053_dir: Path) -> Dict[str, int]:
    rows = read_csv_dict(dd053_dir / "dd053_table_readback_ledger.csv")
    out: Dict[str, int] = {}
    for r in rows:
        table = (r.get("table") or "").strip().upper()
        val = r.get("pydottalk_rows") or r.get("expected_rows") or "0"
        if not table:
            continue
        try:
            out[table] = int(float(val))
        except Exception:
            out[table] = 0
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="DD-054 report-only catalog CDX/tag plan")
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--run-id", default="DD054-catalog-cdx-tag-plan-v0")
    ap.add_argument("--dd053-dir", default="docs/datadict/reports/DD053-canonical-catalog-runtime-readback-v0")
    ap.add_argument("--target-slot", default="metadata\\datadict_canonical_rebuild_v0")
    ap.add_argument("--target-path", default="dottalkpp/data/metadata/datadict_canonical_rebuild_v0")
    ap.add_argument("--profile", action="append", default=[])
    ap.add_argument("--fail-on-review", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    out = Path(args.out_dir).resolve()
    dd053_dir = (repo / args.dd053_dir).resolve()
    target_path = (repo / args.target_path).resolve()
    out.mkdir(parents=True, exist_ok=True)

    dd053_manifest = read_json(dd053_dir / "dd053_canonical_catalog_runtime_readback_manifest.json")
    fields_by_table = build_field_map(dd053_dir)
    row_counts = build_row_counts(dd053_dir)

    tag_rows: List[Dict[str, Any]] = []
    missing_rows: List[Dict[str, Any]] = []
    dts_lines: List[str] = [
        "* DD-054 catalog CDX/tag candidate script",
        "* PLAN ONLY. Do not execute until DD-055 or explicit index-build authorization.",
        f"setpath dbf {args.target_slot}",
        "",
    ]

    total_tags = 0
    failures = 0
    for table in TABLE_ORDER:
        table_fields = fields_by_table.get(table, set())
        dbf_path = target_path / f"{table.lower()}.dbf"
        dts_lines.append(f"* ---- {table} ----")
        dts_lines.append(f"use {table.lower()}")
        for expr, tag, purpose in TAG_PLAN[table]:
            total_tags += 1
            field_present = int(expr.upper() in table_fields)
            tag_len_ok = int(1 <= len(tag) <= 10)
            expr_safe = int(expr.isidentifier() and expr.upper() == expr)
            tag_safe = int(tag.isidentifier() and tag.upper() == tag)
            planned_command = f"index on {expr} tag {tag}"
            status = "PLAN_READY" if field_present and tag_len_ok and expr_safe and tag_safe else "REVIEW"
            if status != "PLAN_READY":
                failures += 1
                missing_rows.append({
                    "table": table,
                    "expr": expr,
                    "tag": tag,
                    "field_present": field_present,
                    "tag_len_ok": tag_len_ok,
                    "expr_safe": expr_safe,
                    "tag_safe": tag_safe,
                    "status": status,
                })
            tag_rows.append({
                "table": table,
                "row_count": row_counts.get(table, ""),
                "dbf_path": safe_rel(repo, dbf_path),
                "expr": expr,
                "tag": tag,
                "purpose": purpose,
                "field_present": field_present,
                "tag_len_ok": tag_len_ok,
                "expr_safe": expr_safe,
                "tag_safe": tag_safe,
                "planned_command": planned_command,
                "status": status,
            })
            dts_lines.append(planned_command)
        dts_lines.append("")

    dd053_green = dd053_manifest.get("status") == "CANONICAL_CATALOG_RUNTIME_READBACK_GREEN"
    if not dd053_green:
        failures += 1

    gate_rows = [
        {
            "gate": "dd053_runtime_readback_green",
            "expected": "CANONICAL_CATALOG_RUNTIME_READBACK_GREEN",
            "observed": dd053_manifest.get("status", ""),
            "pass": int(dd053_green),
        },
        {
            "gate": "tables_with_field_descriptor_ledgers",
            "expected": len(TABLE_ORDER),
            "observed": sum(1 for t in TABLE_ORDER if fields_by_table.get(t)),
            "pass": int(sum(1 for t in TABLE_ORDER if fields_by_table.get(t)) == len(TABLE_ORDER)),
        },
        {
            "gate": "planned_tags_ready",
            "expected": total_tags,
            "observed": sum(1 for r in tag_rows if r["status"] == "PLAN_READY"),
            "pass": int(sum(1 for r in tag_rows if r["status"] == "PLAN_READY") == total_tags),
        },
    ]

    boundary_rows = [
        {"boundary": "report_only_plan", "observed": 1, "required": 1, "pass": 1},
        {"boundary": "cdx_index_created", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "active_catalog_mutation", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "staging_catalog_mutation", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "source_edits", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "help_meta_cmdhelpchk_mutation", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "lmdb_build", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "promotion_executed", "observed": 0, "required": 0, "pass": 1},
    ]

    status = "CATALOG_CDX_TAG_PLAN_READY" if failures == 0 else "CATALOG_CDX_TAG_PLAN_REVIEW"

    write_csv(out / "dd054_catalog_tag_plan.csv", tag_rows, [
        "table", "row_count", "dbf_path", "expr", "tag", "purpose", "field_present",
        "tag_len_ok", "expr_safe", "tag_safe", "planned_command", "status",
    ])
    write_csv(out / "dd054_tag_plan_review_rows.csv", missing_rows, [
        "table", "expr", "tag", "field_present", "tag_len_ok", "expr_safe", "tag_safe", "status",
    ])
    write_csv(out / "dd054_gate_ledger.csv", gate_rows, ["gate", "expected", "observed", "pass"])
    write_csv(out / "dd054_no_mutation_boundary_ledger.csv", boundary_rows, ["boundary", "observed", "required", "pass"])
    (out / "dd054_candidate_index_build_script.dts").write_text("\n".join(dts_lines) + "\n", encoding="utf-8")

    manifest = {
        "contract": "dd054_catalog_cdx_tag_plan_v0",
        "run_id": args.run_id,
        "created_utc": utc_now(),
        "status": status,
        "repo_root": str(repo),
        "profiles": args.profile,
        "target_slot": args.target_slot,
        "target_path": str(target_path),
        "dd053_status": dd053_manifest.get("status", ""),
        "tables_planned": len(TABLE_ORDER),
        "tags_planned": total_tags,
        "tags_ready": sum(1 for r in tag_rows if r["status"] == "PLAN_READY"),
        "failures": failures,
        "candidate_script": str(out / "dd054_candidate_index_build_script.dts"),
        "cdx_index_created": 0,
        "active_catalog_mutation": 0,
        "staging_catalog_mutation": 0,
        "source_edits": 0,
        "help_meta_cmdhelpchk_mutation": 0,
        "lmdb_build": 0,
        "promotion_executed": 0,
        "next_recommended_action": "DD-055 guarded CDX/tag execution against staging catalog only.",
    }
    write_json(out / "dd054_catalog_cdx_tag_plan_manifest.json", manifest)

    report = f"""# DD-054 Catalog CDX / Tag Plan

Run id: `{args.run_id}`
Status: **{status}**
Created UTC: `{manifest['created_utc']}`

## Purpose

DD-054 plans CDX/tag creation for the staged real Data Dictionary catalog after
DD-053 proved the runtime-created x64 DBFs, row counts, descriptors, and memo
sidecars.

## Inputs

- DD-053 status: `{dd053_manifest.get('status', '')}`
- Target: `{safe_rel(repo, target_path)}`

## Planned tags

- Tables planned: **{len(TABLE_ORDER)}**
- Tags planned: **{total_tags}**
- Tags ready: **{manifest['tags_ready']}**
- Review/failure rows: **{len(missing_rows)}**

## Boundary

DD-054 is report-only. It does not create CDX/indexes, mutate the staging catalog,
mutate the active catalog, edit source, build LMDB, or mutate HELP/META/CMDHELPCHK.

## Next

If green, DD-055 may execute CDX/tag creation against the staging catalog only,
with explicit authorization and post-run verification.
"""
    (out / "DD054_CATALOG_CDX_TAG_PLAN.md").write_text(report, encoding="utf-8")

    print(f"DD-054 catalog CDX/tag plan manifest: {out / 'dd054_catalog_cdx_tag_plan_manifest.json'}")
    print(f"status: {status}; tags: {total_tags}; ready: {manifest['tags_ready']}; failures: {failures}")
    return 2 if (args.fail_on_review and failures) else 0


if __name__ == "__main__":
    raise SystemExit(main())
