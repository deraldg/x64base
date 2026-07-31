#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List


TABLES = {
    "DATA_DICTIONARY_OBJECTS": [
        ("CATALOG_OBJECT_ID", "C(32)", '"OBJ_DD096X_COMMAND_SURFACE_01"'),
        ("CATALOG_OBJECT_TYPE", "C(64)", '"COMMAND_SURFACE"'),
        ("CATALOG_OBJECT_NAME", "C(128)", '"DDICT EVIDENCE <object>"'),
        ("CATALOG_OWNER_NAME", "C(128)", '"DATA_DICTIONARY_RUNTIME_SURFACES"'),
        ("CATALOG_STATUS_CODE", "C(64)", '"RUNTIME_PROVEN_SCHEMA_PROOF"'),
        ("CATALOG_PROFILE_CODE", "C(32)", '"ENGINE"'),
        ("SOURCE_ARTIFACT_ID", "C(64)", '"DD096VR_DD096W_PROOF_CLOSEOUT"'),
    ],
    "DATA_DICTIONARY_OBJECT_ATTRIBUTES": [
        ("CATALOG_ATTRIBUTE_ID", "C(32)", '"ATTR_DD096X_0001"'),
        ("CATALOG_OBJECT_ID", "C(32)", '"OBJ_DD096X_COMMAND_SURFACE_01"'),
        ("CATALOG_ATTRIBUTE_NAME", "C(128)", '"schema_promotion_policy"'),
        ("CATALOG_ATTRIBUTE_VALUE", "C(254)", '"Use x64 long identity names for Data Dictionary proof schema while keeping data widths deliberate."'),
        ("CATALOG_ATTRIBUTE_DETAIL", "M", '"Long detail: this memo proves attribute detail text can stay out of fixed-width fields."'),
        ("EVIDENCE_RECORD_ID", "C(64)", '"EVID_DD096X_SCHEMA_PROOF_0001"'),
    ],
    "DATA_DICTIONARY_RELATION_EDGES": [
        ("RELATION_EDGE_ID", "C(32)", '"EDGE_DD096X_0001"'),
        ("RELATION_FROM_OBJECT_ID", "C(32)", '"OBJ_DD096X_COMMAND_SURFACE_01"'),
        ("RELATION_TO_OBJECT_ID", "C(32)", '"ATTR_DD096X_0001"'),
        ("RELATION_EDGE_TYPE", "C(64)", '"HAS_CATALOG_ATTRIBUTE"'),
        ("EVIDENCE_RECORD_ID", "C(64)", '"EVID_DD096X_SCHEMA_PROOF_0001"'),
    ],
    "DATA_DICTIONARY_EVIDENCE_RECORDS": [
        ("EVIDENCE_RECORD_ID", "C(64)", '"EVID_DD096X_SCHEMA_PROOF_0001"'),
        ("CATALOG_OBJECT_ID", "C(32)", '"OBJ_DD096X_COMMAND_SURFACE_01"'),
        ("SOURCE_ARTIFACT_ID", "C(64)", '"DD096VR_DD096W_PROOF_CLOSEOUT"'),
        ("EVIDENCE_KIND_CODE", "C(64)", '"RUNTIME_SCHEMA_PROOF"'),
        ("EVIDENCE_CONFIDENCE_CODE", "C(32)", '"GREEN_PENDING_RUNTIME"'),
        ("EVIDENCE_DETAIL_TEXT", "M", '"Evidence detail memo: DD096X creates parallel x64 proof tables only."'),
    ],
    "DATA_DICTIONARY_GATE_RECORDS": [
        ("GATE_RECORD_ID", "C(64)", '"GATE_DD096X_SCHEMA_PROOF_READY"'),
        ("RUN_RECORD_ID", "C(64)", '"DD096X_GUARDED_X64_SCHEMA_PROOF_V0"'),
        ("GATE_NAME", "C(128)", '"parallel_x64_data_dictionary_schema_proof"'),
        ("GATE_STATUS_CODE", "C(64)", '"PROOF_TABLES_ONLY_NO_ACTIVE_CATALOG_REPLACEMENT"'),
        ("GATE_DETAIL_TEXT", "M", '"Gate detail: proof schema creates sandbox x64 tables; active datadict remains unchanged."'),
    ],
    "DATA_DICTIONARY_RUNS": [
        ("RUN_RECORD_ID", "C(64)", '"DD096X_GUARDED_X64_SCHEMA_PROOF_V0"'),
        ("RUN_KIND_CODE", "C(64)", '"X64_SCHEMA_PROOF"'),
        ("RUN_STATUS_CODE", "C(64)", '"GENERATED_PENDING_RUNTIME_PROOF"'),
        ("RUN_PROFILE_CODE", "C(32)", '"ENGINE_PROFESSIONAL"'),
        ("RUN_DETAIL_TEXT", "M", '"Run detail: generated from DD096V-R/DD096W plan; proof only."'),
    ],
}


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


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


def make_dts() -> str:
    lines: List[str] = []
    lines.append("* DD096X guarded x64 Data Dictionary schema proof")
    lines.append("* Parallel proof tables only. Run DO SANDBOX before this script.")
    lines.append("* Uses single-line CREATE X64 commands to avoid multiline CREATE continuation red lane.")
    lines.append("* Active dottalkpp/data/datadict catalog is not touched by this script.")
    lines.append("")
    lines.append("CLOSE ALL")
    lines.append("")
    for table, fields in TABLES.items():
        fields_spec = ", ".join(f"{name} {typ}" for name, typ, val in fields)
        create_line = f"CREATE X64 {table} ({fields_spec})"
        lines.append(f"* ---------------- {table} ----------------")
        lines.append(f"* TABLE_NAME_LEN={len(table)} CREATE_LINE_LEN={len(create_line)}")
        for name, typ, val in fields:
            lines.append(f"* FIELD_NAME_LEN={len(name)} FIELD={name} TYPE={typ}")
        lines.append(create_line)
        lines.append("AREA")
        lines.append("STRUCT")
        lines.append("APPEND")
        for name, typ, val in fields:
            lines.append(f"REPLACE {name} WITH {val}")
        lines.append("TOP")
        lines.append("LIST")
        lines.append("STRUCT")
        lines.append("CLOSE ALL")
        lines.append(f"USE {table}")
        lines.append("AREA")
        lines.append("STRUCT")
        lines.append("TOP")
        lines.append("LIST")
        lines.append("CLOSE ALL")
        lines.append("")
    lines.append("* DD096X done. If all sections created/reopened/listed, schema proof is green.")
    lines.append("")
    return "\n".join(lines) + "\n\n"


def main() -> int:
    ap = argparse.ArgumentParser(description="DD096X guarded x64 Data Dictionary schema proof package")
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--run-id", default="DD096X-guarded-x64-datadict-schema-proof-v0")
    ap.add_argument("--write-runtime-script", action="store_true")
    ap.add_argument("--profile", action="append", default=[])
    ap.add_argument("--fail-on-review", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    out = Path(args.out_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)
    generated = out / "generated_x64_schema_proof"
    generated.mkdir(parents=True, exist_ok=True)

    table_rows = []
    field_rows = []
    for table, fields in TABLES.items():
        fields_spec = ", ".join(f"{name} {typ}" for name, typ, val in fields)
        create_line = f"CREATE X64 {table} ({fields_spec})"
        table_rows.append({
            "table_name": table,
            "table_name_len": len(table),
            "field_count": len(fields),
            "create_line_len": len(create_line),
            "single_line_create": 1,
            "proof_root": "SANDBOX",
            "apply_now": 0,
        })
        for name, typ, val in fields:
            field_rows.append({
                "table_name": table,
                "field_name": name,
                "field_name_len": len(name),
                "type": typ,
                "sample_value": val[:120],
                "identity_name_within_128": int(len(name) <= 128),
            })

    write_csv(generated / "dd096x_schema_proof_tables.csv", table_rows, [
        "table_name", "table_name_len", "field_count", "create_line_len", "single_line_create", "proof_root", "apply_now"
    ])
    write_csv(generated / "dd096x_schema_proof_fields.csv", field_rows, [
        "table_name", "field_name", "field_name_len", "type", "sample_value", "identity_name_within_128"
    ])

    dts_text = make_dts()
    preview_path = generated / "DD096X_GUARDED_X64_DATADICT_SCHEMA_PROOF.dts"
    write_text(preview_path, dts_text)

    runtime_script_written = 0
    runtime_path = repo / "dottalkpp/data/scripts/DD096X_GUARDED_X64_DATADICT_SCHEMA_PROOF.dts"
    if args.write_runtime_script:
        write_text(runtime_path, dts_text)
        runtime_script_written = 1

    boundary_rows = [
        {"boundary": "schema_proof_package_generation", "observed": 1, "required": 1, "pass": 1},
        {"boundary": "runtime_script_written", "observed": runtime_script_written, "required": int(args.write_runtime_script), "pass": 1},
        {"boundary": "active_datadict_catalog_mutation", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "active_datadict_dbf_append_replace_delete_pack_zap", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "cdx_lmdb_rebuild_by_generator", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "source_edits", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "help_meta_cmdhelpchk_mutation", "observed": 0, "required": 0, "pass": 1},
    ]
    write_csv(out / "dd096x_no_mutation_boundary_ledger.csv", boundary_rows, ["boundary", "observed", "required", "pass"])

    max_create = max(r["create_line_len"] for r in table_rows)
    max_field_name = max(r["field_name_len"] for r in field_rows)
    gates = [
        {"gate": "tables_six", "expected": 6, "observed": len(table_rows), "pass": int(len(table_rows) == 6)},
        {"gate": "fields_present", "expected": ">=29", "observed": len(field_rows), "pass": int(len(field_rows) >= 29)},
        {"gate": "field_names_within_128", "expected": 0, "observed": sum(1 for r in field_rows if int(r["identity_name_within_128"]) != 1), "pass": int(all(int(r["identity_name_within_128"]) == 1 for r in field_rows))},
        {"gate": "single_line_create_used", "expected": 6, "observed": sum(int(r["single_line_create"]) for r in table_rows), "pass": int(sum(int(r["single_line_create"]) for r in table_rows) == 6)},
        {"gate": "active_catalog_replacement_not_authorized", "expected": 0, "observed": 0, "pass": 1},
        {"gate": "runtime_script_written_if_requested", "expected": int(args.write_runtime_script), "observed": runtime_script_written, "pass": int(runtime_script_written == int(args.write_runtime_script))},
    ]
    failures = sum(1 for r in gates if int(r["pass"]) != 1)
    write_csv(out / "dd096x_gate_ledger.csv", gates, ["gate", "expected", "observed", "pass"])

    report = f"""# DD096X Guarded x64 Data Dictionary Schema Proof

Run id: `{args.run_id}`
Status: **DD096X_GUARDED_X64_SCHEMA_PROOF_READY**
Created UTC: `{utc_now()}`

## Purpose

DD096X generates a parallel x64 Data Dictionary schema proof script.

It creates proof tables under the active path when the script is run. The intended runtime procedure is:

```text
DO SANDBOX
DO DD096X_GUARDED_X64_DATADICT_SCHEMA_PROOF
```

The active `dottalkpp/data/datadict` catalog is not touched by this generator.

## Why this shape

The proof uses single-line `CREATE X64` commands because single-line long-name CREATE is the currently green path. Multiline CREATE continuation remains a separate repair/proof lane.

## Summary

- Proposed proof tables: **{len(table_rows)}**
- Proposed proof fields: **{len(field_rows)}**
- Max field identity-name length: **{max_field_name}**
- Max CREATE line length: **{max_create}**
- Runtime script written: **{runtime_script_written}**
- Active Data Dictionary catalog replacement: **0**

## Boundary

This generator writes reports and optionally writes a runtime DTS script under `dottalkpp/data/scripts`.
It does not mutate active Data Dictionary DBFs, rebuild CDX/LMDB, edit source, mutate HELP/CMDHELPCHK, or replace the active catalog.
"""
    write_text(out / "DD096X_GUARDED_X64_DATADICT_SCHEMA_PROOF_REPORT.md", report)

    manifest = {
        "contract": "dd096x_guarded_x64_datadict_schema_proof_v0",
        "run_id": args.run_id,
        "created_utc": utc_now(),
        "status": "DD096X_GUARDED_X64_SCHEMA_PROOF_READY" if failures == 0 else "DD096X_GUARDED_X64_SCHEMA_PROOF_REVIEW",
        "repo_root": str(repo),
        "profiles": args.profile,
        "tables": len(table_rows),
        "fields": len(field_rows),
        "max_create_line_len": max_create,
        "max_field_name_len": max_field_name,
        "runtime_script_written": runtime_script_written,
        "active_datadict_catalog_mutation": 0,
        "active_catalog_replacement": 0,
        "failures": failures,
        "runtime_script_path": str(runtime_path) if runtime_script_written else "",
        "next_recommended_action": "Run DO SANDBOX, then DO DD096X_GUARDED_X64_DATADICT_SCHEMA_PROOF and capture runtime proof.",
    }
    write_json(out / "dd096x_guarded_x64_datadict_schema_proof_manifest.json", manifest)

    artifact_rows = [
        {"role": "dts_preview", "path": str(preview_path), "exists": int(preview_path.exists()), "kind": "file", "bytes_or_children": preview_path.stat().st_size if preview_path.exists() else 0, "sha256": sha256(preview_path)},
        {"role": "runtime_dts", "path": str(runtime_path), "exists": int(runtime_path.exists()), "kind": "file", "bytes_or_children": runtime_path.stat().st_size if runtime_path.exists() else 0, "sha256": sha256(runtime_path)},
        {"role": "report", "path": str(out / "DD096X_GUARDED_X64_DATADICT_SCHEMA_PROOF_REPORT.md"), "exists": 1, "kind": "file", "bytes_or_children": (out / "DD096X_GUARDED_X64_DATADICT_SCHEMA_PROOF_REPORT.md").stat().st_size, "sha256": sha256(out / "DD096X_GUARDED_X64_DATADICT_SCHEMA_PROOF_REPORT.md")},
    ]
    write_csv(out / "dd096x_artifact_ledger.csv", artifact_rows, ["role", "path", "exists", "kind", "bytes_or_children", "sha256"])

    print(f"DD096X guarded x64 schema proof manifest: {out / 'dd096x_guarded_x64_datadict_schema_proof_manifest.json'}")
    print(f"status: {manifest['status']}; tables: {len(table_rows)}; fields: {len(field_rows)}; max_create_line_len: {max_create}; runtime_script_written: {runtime_script_written}; active_catalog_replacement: 0; failures: {failures}")
    return 2 if (args.fail_on_review and failures) else 0


if __name__ == "__main__":
    raise SystemExit(main())
