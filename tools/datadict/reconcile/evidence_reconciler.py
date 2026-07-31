#!/usr/bin/env python3
"""
DD-018 report-only evidence reconciler skeleton.

Purpose:
  Merge physical data-dictionary evidence from declared schema manifests,
  static DBF header projections, and future runtime transcript proof manifests
  into a reviewed projection plus conflict queue.

Boundary:
  This tool is read-only. It does not open DotTalk++, does not mutate DBF/CDX/LMDB,
  and does not write to project catalogs. It only writes JSON/CSV reports.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

TRUST_RANK = {
    "runtime_proven": 100,
    "RUNTIME_TRANSCRIPT_PROOF": 95,
    "runtime_transcript_proof": 95,
    "STATIC_DBF_HEADER_PARSE": 70,
    "static_dbf_header_parse": 70,
    "declared_schema": 50,
    "declared": 50,
    "source_defined": 45,
    "source_registry": 40,
    "source_contract": 40,
    "generated_report": 25,
    "ai_draft": 10,
    "unknown": 0,
}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def canon_name(value: Any) -> str:
    text = str(value or "").strip().upper()
    text = re.sub(r"[^A-Z0-9_]+", "_", text)
    text = re.sub(r"_+", "_", text).strip("_")
    return text or "UNKNOWN"


def table_key_from_path(path: Any) -> str:
    if not path:
        return ""
    name = Path(str(path)).stem
    return canon_name(name)


def table_key(row: Dict[str, Any]) -> str:
    return canon_name(
        row.get("canonical_name")
        or row.get("logical_name")
        or row.get("table_name")
        or row.get("file_name")
        or table_key_from_path(row.get("physical_path") or row.get("path"))
        or row.get("table_id")
    )


def field_key(row: Dict[str, Any], table_lookup: Dict[str, str] | None = None) -> Tuple[str, str, int]:
    tid = row.get("table_id") or row.get("table_ref") or ""
    table = ""
    if table_lookup and tid in table_lookup:
        table = table_lookup[tid]
    table = table or canon_name(row.get("table_name") or row.get("table_logical_name") or tid)
    field = canon_name(row.get("logical_name") or row.get("field_name") or row.get("descriptor_name") or row.get("name"))
    ordinal_raw = row.get("ordinal") or row.get("field_ordinal") or 0
    try:
        ordinal = int(ordinal_raw)
    except Exception:
        ordinal = 0
    return (table, field, ordinal)


def detect_evidence_kind(row: Dict[str, Any], default: str) -> str:
    return str(row.get("evidence_kind") or row.get("area_kind") or row.get("evidence_status") or default)


def trust_rank(kind: str) -> int:
    k = str(kind or "unknown")
    return TRUST_RANK.get(k, TRUST_RANK.get(k.lower(), 0))


def normalize_table(row: Dict[str, Any], source_file: str, source_kind: str) -> Dict[str, Any]:
    evidence_kind = detect_evidence_kind(row, source_kind)
    key = table_key(row)
    return {
        "object_kind": "table",
        "object_key": key,
        "table_id": row.get("table_id") or row.get("id") or key,
        "logical_name": row.get("logical_name") or row.get("table_name") or row.get("file_name") or key,
        "physical_path": row.get("physical_path") or row.get("path"),
        "table_flavor": row.get("table_flavor") or row.get("header_kind"),
        "record_count": row.get("record_count"),
        "header_length": row.get("header_length"),
        "record_length": row.get("record_length"),
        "field_count": row.get("field_count"),
        "profile_scope": row.get("profile_scope") or row.get("profile") or "unknown",
        "source_file": source_file,
        "source_kind": source_kind,
        "evidence_kind": evidence_kind,
        "trust_rank": trust_rank(evidence_kind),
        "raw": row,
    }


def normalize_field(row: Dict[str, Any], source_file: str, source_kind: str, table_lookup: Dict[str, str]) -> Dict[str, Any]:
    evidence_kind = detect_evidence_kind(row, source_kind)
    tkey, fkey, ordinal = field_key(row, table_lookup)
    return {
        "object_kind": "field",
        "object_key": f"{tkey}.{fkey}" if fkey != "UNKNOWN" else f"{tkey}.ORDINAL_{ordinal}",
        "table_key": tkey,
        "field_key": fkey,
        "table_id": row.get("table_id"),
        "field_id": row.get("field_id") or f"{tkey}.{fkey}",
        "logical_name": row.get("logical_name") or row.get("field_name") or row.get("descriptor_name") or fkey,
        "descriptor_name": row.get("descriptor_name") or row.get("field_name") or row.get("logical_name") or fkey,
        "field_type": row.get("field_type"),
        "width": row.get("width"),
        "decimals": row.get("decimals"),
        "offset": row.get("offset"),
        "ordinal": ordinal,
        "nullable": row.get("nullable"),
        "profile_scope": row.get("profile_scope") or "unknown",
        "source_file": source_file,
        "source_kind": source_kind,
        "evidence_kind": evidence_kind,
        "trust_rank": trust_rank(evidence_kind),
        "raw": row,
    }


def load_evidence(path: Path) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    source_kind = "unknown"
    if data.get("manifest_kind") == "DD017_STATIC_DBF_PHYSICAL_PROJECTION":
        source_kind = "static_dbf_header_parse"
    elif data.get("schema_version") or data.get("generator"):
        source_kind = "declared_schema_or_source_manifest"
    elif data.get("transcript_run") or data.get("commands"):
        source_kind = "runtime_transcript_candidate"

    table_rows = data.get("tables") or []
    table_evidence = [normalize_table(r, str(path), source_kind) for r in table_rows]
    table_lookup = {}
    for ev in table_evidence:
        if ev.get("table_id"):
            table_lookup[str(ev["table_id"])] = ev["object_key"]

    field_rows = data.get("fields") or []
    field_evidence = [normalize_field(r, str(path), source_kind, table_lookup) for r in field_rows]
    meta = {
        "path": str(path),
        "sha256": sha256_file(path),
        "source_kind": source_kind,
        "table_rows": len(table_rows),
        "field_rows": len(field_rows),
    }
    return table_evidence, field_evidence, meta


def pick_winner(items: List[Dict[str, Any]]) -> Dict[str, Any]:
    return sorted(items, key=lambda x: (x.get("trust_rank", 0), -len(str(x.get("source_file", "")))), reverse=True)[0]


def conflict_values(items: List[Dict[str, Any]], attrs: Iterable[str]) -> List[Dict[str, Any]]:
    conflicts = []
    for attr in attrs:
        vals = {}
        for it in items:
            val = it.get(attr)
            if val is None or val == "":
                continue
            vals.setdefault(str(val), []).append(it)
        if len(vals) > 1:
            conflicts.append({
                "attribute": attr,
                "values": sorted(vals.keys()),
                "evidence_count": sum(len(v) for v in vals.values()),
                "reason": "conflicting_values_across_evidence",
            })
    return conflicts


def reconcile_group(object_kind: str, key: str, items: List[Dict[str, Any]]) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    winner = pick_winner(items)
    if object_kind == "table":
        attrs = ["logical_name", "physical_path", "table_flavor", "record_count", "header_length", "record_length", "field_count", "profile_scope"]
    else:
        attrs = ["logical_name", "descriptor_name", "field_type", "width", "decimals", "offset", "ordinal", "nullable", "profile_scope"]
    conflicts = conflict_values(items, attrs)
    projection = {k: winner.get(k) for k in [
        "object_kind", "object_key", "table_key", "field_key", "table_id", "field_id",
        "logical_name", "descriptor_name", "physical_path", "table_flavor", "field_type",
        "width", "decimals", "offset", "ordinal", "nullable", "record_count", "header_length",
        "record_length", "field_count", "profile_scope", "evidence_kind", "trust_rank", "source_file"
    ] if k in winner}
    projection["evidence_count"] = len(items)
    projection["conflict_count"] = len(conflicts)
    projection["review_status"] = "needs_review" if conflicts else "candidate_projection"
    conflict_rows = []
    for c in conflicts:
        conflict_rows.append({
            "object_kind": object_kind,
            "object_key": key,
            "attribute": c["attribute"],
            "values": " | ".join(c["values"]),
            "evidence_count": c["evidence_count"],
            "reason": c["reason"],
            "review_status": "needs_human_review",
        })
    return projection, conflict_rows


def write_csv(path: Path, rows: List[Dict[str, Any]], fieldnames: List[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        keys = []
        for r in rows:
            for k in r.keys():
                if k not in keys:
                    keys.append(k)
        fieldnames = keys
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)


def main() -> int:
    ap = argparse.ArgumentParser(description="DD-018 report-only data-dictionary evidence reconciler")
    ap.add_argument("--input", action="append", required=True, help="Input JSON manifest/projection. Repeatable.")
    ap.add_argument("--outdir", required=True, help="Output directory for JSON/CSV reports.")
    args = ap.parse_args()

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    all_tables: List[Dict[str, Any]] = []
    all_fields: List[Dict[str, Any]] = []
    input_meta: List[Dict[str, Any]] = []
    for raw in args.input:
        path = Path(raw)
        t, f, m = load_evidence(path)
        all_tables.extend(t)
        all_fields.extend(f)
        input_meta.append(m)

    table_groups: Dict[str, List[Dict[str, Any]]] = {}
    for ev in all_tables:
        table_groups.setdefault(ev["object_key"], []).append(ev)
    field_groups: Dict[str, List[Dict[str, Any]]] = {}
    for ev in all_fields:
        field_groups.setdefault(ev["object_key"], []).append(ev)

    projections: List[Dict[str, Any]] = []
    conflicts: List[Dict[str, Any]] = []
    for key, items in sorted(table_groups.items()):
        p, c = reconcile_group("table", key, items)
        projections.append(p)
        conflicts.extend(c)
    for key, items in sorted(field_groups.items()):
        p, c = reconcile_group("field", key, items)
        projections.append(p)
        conflicts.extend(c)

    evidence_stack = []
    for ev in all_tables + all_fields:
        evidence_stack.append({
            "object_kind": ev["object_kind"],
            "object_key": ev["object_key"],
            "evidence_kind": ev["evidence_kind"],
            "trust_rank": ev["trust_rank"],
            "source_kind": ev["source_kind"],
            "source_file": ev["source_file"],
            "logical_name": ev.get("logical_name"),
            "descriptor_name": ev.get("descriptor_name"),
            "field_type": ev.get("field_type"),
            "width": ev.get("width"),
            "decimals": ev.get("decimals"),
            "offset": ev.get("offset"),
            "ordinal": ev.get("ordinal"),
        })

    manifest = {
        "manifest_kind": "DD018_EVIDENCE_RECONCILIATION_REPORT",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "mode": "report_only_no_catalog_mutation",
        "input_meta": input_meta,
        "counts": {
            "input_files": len(input_meta),
            "table_evidence_rows": len(all_tables),
            "field_evidence_rows": len(all_fields),
            "projected_objects": len(projections),
            "conflict_rows": len(conflicts),
        },
        "trust_rank": TRUST_RANK,
        "projected_objects": projections,
        "conflict_queue": conflicts,
        "evidence_stack": evidence_stack,
    }

    (outdir / "dd018_reconciliation_report_v0.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    write_csv(outdir / "dd018_projected_objects_v0.csv", projections)
    write_csv(outdir / "dd018_conflict_queue_v0.csv", conflicts, ["object_kind","object_key","attribute","values","evidence_count","reason","review_status"])
    write_csv(outdir / "dd018_evidence_stack_v0.csv", evidence_stack)
    write_csv(outdir / "dd018_input_manifest_index_v0.csv", input_meta)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
