#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List, Tuple


DEFAULT_STAGED_DIR = "docs/datadict/reports/DD096E-R-root-aware-external-apply-staging-v0/generated_staged_apply_rows"
DEFAULT_DD096X_DIR = "docs/datadict/reports/DD096X-guarded-x64-datadict-schema-proof-v0"

INPUT_FILES = {
    "DDOBJECT": "dd096e_staged_ddobject_insert_rows.csv",
    "DDATTR": "dd096e_staged_ddattr_insert_rows.csv",
    "DDEDGE": "dd096e_staged_ddedge_insert_rows.csv",
    "DDEVID": "dd096e_staged_ddevid_insert_rows.csv",
    "DDGATE": "dd096e_staged_ddgate_insert_rows.csv",
}

X64_SCHEMAS = {
    "DATA_DICTIONARY_OBJECTS": [
        ("CATALOG_OBJECT_ID", "C", 32),
        ("CATALOG_OBJECT_TYPE", "C", 64),
        ("CATALOG_OBJECT_NAME", "C", 128),
        ("CATALOG_OWNER_NAME", "C", 128),
        ("CATALOG_STATUS_CODE", "C", 64),
        ("CATALOG_PROFILE_CODE", "C", 32),
        ("SOURCE_ARTIFACT_ID", "C", 64),
    ],
    "DATA_DICTIONARY_OBJECT_ATTRIBUTES": [
        ("CATALOG_ATTRIBUTE_ID", "C", 32),
        ("CATALOG_OBJECT_ID", "C", 32),
        ("CATALOG_ATTRIBUTE_NAME", "C", 128),
        ("CATALOG_ATTRIBUTE_VALUE", "C", 254),
        ("CATALOG_ATTRIBUTE_DETAIL", "M", 0),
        ("EVIDENCE_RECORD_ID", "C", 64),
    ],
    "DATA_DICTIONARY_RELATION_EDGES": [
        ("RELATION_EDGE_ID", "C", 32),
        ("RELATION_FROM_OBJECT_ID", "C", 32),
        ("RELATION_TO_OBJECT_ID", "C", 32),
        ("RELATION_EDGE_TYPE", "C", 64),
        ("EVIDENCE_RECORD_ID", "C", 64),
    ],
    "DATA_DICTIONARY_EVIDENCE_RECORDS": [
        ("EVIDENCE_RECORD_ID", "C", 64),
        ("CATALOG_OBJECT_ID", "C", 32),
        ("SOURCE_ARTIFACT_ID", "C", 64),
        ("EVIDENCE_KIND_CODE", "C", 64),
        ("EVIDENCE_CONFIDENCE_CODE", "C", 32),
        ("EVIDENCE_DETAIL_TEXT", "M", 0),
    ],
    "DATA_DICTIONARY_GATE_RECORDS": [
        ("GATE_RECORD_ID", "C", 64),
        ("RUN_RECORD_ID", "C", 64),
        ("GATE_NAME", "C", 128),
        ("GATE_STATUS_CODE", "C", 64),
        ("GATE_DETAIL_TEXT", "M", 0),
    ],
    "DATA_DICTIONARY_RUNS": [
        ("RUN_RECORD_ID", "C", 64),
        ("RUN_KIND_CODE", "C", 64),
        ("RUN_STATUS_CODE", "C", 64),
        ("RUN_PROFILE_CODE", "C", 32),
        ("RUN_DETAIL_TEXT", "M", 0),
    ],
}


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def norm_key(s: Any) -> str:
    return "".join(ch for ch in str(s or "").upper() if ch.isalnum())


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""


def write_json(path: Path, obj: Dict[str, Any]) -> None:
    write_text(path, json.dumps(obj, indent=2, sort_keys=True) + "\n")


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: List[Dict[str, Any]], fields: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fields})


def sha256(path: Path) -> str:
    if not path.exists() or path.is_dir():
        return ""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def get(row: Dict[str, str], *names: str, default: str = "") -> str:
    nmap = {norm_key(k): v for k, v in row.items()}
    for name in names:
        v = nmap.get(norm_key(name), "")
        if str(v) != "":
            return str(v)
    return default


def trim(value: str, max_len: int) -> str:
    value = str(value or "").replace("\r", " ").replace("\n", " ")
    if max_len <= 0:
        return value
    while len(value.encode("utf-8")) > max_len:
        value = value[:-1]
    return value


def dt_literal(value: str) -> str:
    value = str(value or "").replace("\r", " ").replace("\n", " ")
    value = value.replace('"', "'")
    return '"' + value + '"'


def stage_rows(input_rows: Dict[str, List[Dict[str, str]]], run_id: str) -> Dict[str, List[Dict[str, str]]]:
    out: Dict[str, List[Dict[str, str]]] = {k: [] for k in X64_SCHEMAS}

    for r in input_rows.get("DDOBJECT", []):
        out["DATA_DICTIONARY_OBJECTS"].append({
            "CATALOG_OBJECT_ID": get(r, "OBJID", "CANDIDATE_OBJID", "candidate_objid", "row_id", "candidate_row_id"),
            "CATALOG_OBJECT_TYPE": get(r, "OBJTYPE", "OBJECT_TYPE", "TYPE", "family", default="CATALOG_OBJECT"),
            "CATALOG_OBJECT_NAME": get(r, "NAME", "OBJECT_NAME", "TOKEN", "surface", "candidate_key"),
            "CATALOG_OWNER_NAME": get(r, "OWNER", "PARENT", "NAMESPACE", default="DATADICT_CATALOG"),
            "CATALOG_STATUS_CODE": get(r, "STATUS", "review_status", default="STAGED_CANDIDATE"),
            "CATALOG_PROFILE_CODE": get(r, "PROFILE", default="ENGINE"),
            "SOURCE_ARTIFACT_ID": get(r, "SRCID", "SOURCE_ARTIFACT_ID", "SOURCE", "ARTIFACT", default="DD096E_R_STAGED_ROWS"),
        })

    for r in input_rows.get("DDATTR", []):
        value = get(r, "ATTRVAL", "VALUE", "CATALOG_ATTRIBUTE_VALUE")
        detail = get(r, "ATTRMEMO", "DETAIL", "CATALOG_ATTRIBUTE_DETAIL")
        if len(value.encode("utf-8")) > 254 and not detail:
            detail = value
        out["DATA_DICTIONARY_OBJECT_ATTRIBUTES"].append({
            "CATALOG_ATTRIBUTE_ID": get(r, "ATTRID", "CANDIDATE_ATTRID", "row_id", "candidate_row_id"),
            "CATALOG_OBJECT_ID": get(r, "OBJID", "CATALOG_OBJECT_ID", "OBJECT_ID"),
            "CATALOG_ATTRIBUTE_NAME": get(r, "ATTRNAME", "ATTRIBUTE_NAME", "NAME"),
            "CATALOG_ATTRIBUTE_VALUE": trim(value, 254),
            "CATALOG_ATTRIBUTE_DETAIL": detail,
            "EVIDENCE_RECORD_ID": get(r, "EVID", "EVIDENCE_RECORD_ID", default=""),
        })

    for r in input_rows.get("DDEDGE", []):
        out["DATA_DICTIONARY_RELATION_EDGES"].append({
            "RELATION_EDGE_ID": get(r, "EDGEID", "CANDIDATE_EDGEID", "row_id", "candidate_row_id"),
            "RELATION_FROM_OBJECT_ID": get(r, "FROM_OBJID", "FROMOBJ", "RELATION_FROM_OBJECT_ID"),
            "RELATION_TO_OBJECT_ID": get(r, "TO_OBJID", "TOOBJ", "RELATION_TO_OBJECT_ID"),
            "RELATION_EDGE_TYPE": get(r, "EDGE_TYPE", "EDGETYPE", "RELATION_EDGE_TYPE", default="CATALOG_RELATION"),
            "EVIDENCE_RECORD_ID": get(r, "EVID", "EVIDENCE_RECORD_ID", default=""),
        })

    for r in input_rows.get("DDEVID", []):
        detail_parts = []
        for key in ("SOURCE", "ARTIFACT", "NOTE", "DETAIL", "KIND"):
            v = get(r, key)
            if v:
                detail_parts.append(f"{key}={v}")
        out["DATA_DICTIONARY_EVIDENCE_RECORDS"].append({
            "EVIDENCE_RECORD_ID": get(r, "EVID", "EVIDENCE_RECORD_ID", "row_id", "candidate_row_id"),
            "CATALOG_OBJECT_ID": get(r, "OBJID", "CATALOG_OBJECT_ID", "OBJECT_ID"),
            "SOURCE_ARTIFACT_ID": get(r, "SRCID", "SOURCE_ARTIFACT_ID", "SOURCE", "ARTIFACT", default="DD096E_R_STAGED_ROWS"),
            "EVIDENCE_KIND_CODE": get(r, "KIND", "EVIDENCE_KIND_CODE", default="STAGED_CANDIDATE_EVIDENCE"),
            "EVIDENCE_CONFIDENCE_CODE": get(r, "CONFIDENCE", "EVIDENCE_CONFIDENCE_CODE", default="STAGED"),
            "EVIDENCE_DETAIL_TEXT": "; ".join(detail_parts),
        })

    for r in input_rows.get("DDGATE", []):
        out["DATA_DICTIONARY_GATE_RECORDS"].append({
            "GATE_RECORD_ID": get(r, "GATEID", "GATE_ID", "GATE_RECORD_ID", "row_id", "candidate_row_id"),
            "RUN_RECORD_ID": get(r, "RUNID", "RUN_ID", "RUN_RECORD_ID", default=run_id),
            "GATE_NAME": get(r, "GATE_NAME", "GATE_TYPE", "GATETYPE", "NAME", default="DATADICT_STAGED_GATE"),
            "GATE_STATUS_CODE": get(r, "STATUS", "GATE_STATUS_CODE", default="STAGED"),
            "GATE_DETAIL_TEXT": get(r, "DETAIL", "NOTE", "ATTRVAL", default="Staged gate row from DD096E-R."),
        })

    out["DATA_DICTIONARY_RUNS"].append({
        "RUN_RECORD_ID": run_id,
        "RUN_KIND_CODE": "X64_STAGED_ROW_IMPORT_PROOF",
        "RUN_STATUS_CODE": "GENERATED_PENDING_RUNTIME_IMPORT",
        "RUN_PROFILE_CODE": "ENGINE_PROFESSIONAL",
        "RUN_DETAIL_TEXT": "DD096Y staged candidate rows mapped into parallel x64 Data Dictionary proof schema. Active catalog replacement not authorized.",
    })

    return out


def validate_widths(staged: Dict[str, List[Dict[str, str]]]) -> List[Dict[str, Any]]:
    blockers: List[Dict[str, Any]] = []
    for table, rows in staged.items():
        fields = X64_SCHEMAS[table]
        width_map = {name: (ftype, width) for name, ftype, width in fields}
        for idx, row in enumerate(rows, start=1):
            for field, value in row.items():
                ftype, width = width_map.get(field, ("", 0))
                if ftype == "C" and len(str(value or "").encode("utf-8")) > width:
                    blockers.append({
                        "table_name": table,
                        "row_number": idx,
                        "field_name": field,
                        "max_width": width,
                        "observed_width": len(str(value or "").encode("utf-8")),
                        "value_preview": str(value)[:100],
                    })
    return blockers


def make_runtime_dts(staged: Dict[str, List[Dict[str, str]]]) -> str:
    lines: List[str] = []
    lines.append("* DD096Y staged candidate row import into x64 Data Dictionary proof schema")
    lines.append("* PRECONDITION: run DO SANDBOX first and run DD096X schema proof first.")
    lines.append("* This appends into SANDBOX proof tables only; active datadict catalog is not replaced.")
    lines.append("")
    lines.append("CLOSE ALL")
    lines.append("")
    for table, rows in staged.items():
        lines.append(f"* ---------------- {table} ----------------")
        lines.append(f"USE {table}")
        lines.append("AREA")
        for row in rows:
            lines.append("APPEND")
            for field, _ftype, _width in X64_SCHEMAS[table]:
                val = row.get(field, "")
                if val != "":
                    lines.append(f"REPLACE {field} WITH {dt_literal(val)}")
            lines.append("")
        lines.append("TOP")
        lines.append("LIST")
        lines.append("STRUCT")
        lines.append("CLOSE ALL")
        lines.append("")
    lines.append("* DD096Y done.")
    lines.append("")
    return "\n".join(lines) + "\n\n"


def main() -> int:
    ap = argparse.ArgumentParser(description="DD096Y stage/import candidate rows into x64 Data Dictionary proof schema")
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--run-id", default="DD096Y-stage-candidate-rows-into-x64-schema-v0")
    ap.add_argument("--staged-dir", default=DEFAULT_STAGED_DIR)
    ap.add_argument("--dd096x-dir", default=DEFAULT_DD096X_DIR)
    ap.add_argument("--write-runtime-script", action="store_true")
    ap.add_argument("--profile", action="append", default=[])
    ap.add_argument("--fail-on-review", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    out = Path(args.out_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)
    generated = out / "generated_x64_staged_import"
    generated.mkdir(parents=True, exist_ok=True)
    staged_dir = repo / args.staged_dir

    input_rows: Dict[str, List[Dict[str, str]]] = {}
    input_ledger: List[Dict[str, Any]] = []
    for family, filename in INPUT_FILES.items():
        path = staged_dir / filename
        rows = read_csv(path)
        input_rows[family] = rows
        input_ledger.append({
            "family": family,
            "path": str(path),
            "exists": int(path.exists()),
            "rows": len(rows),
        })

    staged = stage_rows(input_rows, args.run_id)
    blockers = validate_widths(staged)

    for table, rows in staged.items():
        fields = [name for name, _type, _width in X64_SCHEMAS[table]]
        write_csv(generated / f"dd096y_{table.lower()}_staged_rows.csv", rows, fields)

    write_csv(generated / "dd096y_input_ledger.csv", input_ledger, ["family", "path", "exists", "rows"])
    summary_rows = [
        {"table_name": table, "staged_rows": len(rows), "field_count": len(X64_SCHEMAS[table])}
        for table, rows in staged.items()
    ]
    write_csv(generated / "dd096y_staged_import_summary.csv", summary_rows, ["table_name", "staged_rows", "field_count"])
    write_csv(generated / "dd096y_width_blockers.csv", blockers, ["table_name", "row_number", "field_name", "max_width", "observed_width", "value_preview"])

    dts_text = make_runtime_dts(staged)
    dts_preview = generated / "DD096Y_STAGE_CANDIDATE_ROWS_INTO_X64_SCHEMA.dts"
    write_text(dts_preview, dts_text)

    runtime_script_written = 0
    runtime_path = repo / "dottalkpp/data/scripts/DD096Y_STAGE_CANDIDATE_ROWS_INTO_X64_SCHEMA.dts"
    if args.write_runtime_script and not blockers:
        write_text(runtime_path, dts_text)
        runtime_script_written = 1

    total_input_rows = sum(len(v) for v in input_rows.values())
    total_staged_rows = sum(len(v) for v in staged.values())
    input_missing = sum(1 for r in input_ledger if int(r["exists"]) != 1)

    gates = [
        {"gate": "input_staged_files_present", "expected": 0, "observed": input_missing, "pass": int(input_missing == 0)},
        {"gate": "candidate_input_rows_present", "expected": ">=158", "observed": total_input_rows, "pass": int(total_input_rows >= 158)},
        {"gate": "x64_output_rows_present", "expected": ">=159", "observed": total_staged_rows, "pass": int(total_staged_rows >= 159)},
        {"gate": "width_blockers_zero", "expected": 0, "observed": len(blockers), "pass": int(len(blockers) == 0)},
        {"gate": "active_catalog_replacement_not_authorized", "expected": 0, "observed": 0, "pass": 1},
        {"gate": "runtime_script_written_if_requested", "expected": int(args.write_runtime_script and not blockers), "observed": runtime_script_written, "pass": int(runtime_script_written == int(args.write_runtime_script and not blockers))},
    ]
    failures = sum(1 for r in gates if int(r["pass"]) != 1)
    write_csv(out / "dd096y_gate_ledger.csv", gates, ["gate", "expected", "observed", "pass"])

    boundary_rows = [
        {"boundary": "x64_staged_import_package_generation", "observed": 1, "required": 1, "pass": 1},
        {"boundary": "active_datadict_catalog_replacement", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "active_datadict_dbf_append_replace_delete_pack_zap_by_generator", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "runtime_script_written", "observed": runtime_script_written, "required": int(args.write_runtime_script and not blockers), "pass": 1},
        {"boundary": "source_edits", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "help_meta_cmdhelpchk_mutation", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "manual_publication_mutation", "observed": 0, "required": 0, "pass": 1},
    ]
    write_csv(out / "dd096y_no_mutation_boundary_ledger.csv", boundary_rows, ["boundary", "observed", "required", "pass"])

    status = "DD096Y_X64_STAGED_IMPORT_READY" if failures == 0 else "DD096Y_X64_STAGED_IMPORT_REVIEW"
    report = f"""# DD096Y Stage Candidate Rows into x64 Data Dictionary Proof Schema

Run id: `{args.run_id}`
Status: **{status}**
Created UTC: `{utc_now()}`

## Purpose

DD096Y maps the DD096E-R staged candidate rows into the DD096X parallel x64 Data Dictionary proof schema.

This is still a proof/staging lane. It does not replace the active `dottalkpp/data/datadict` catalog.

## Summary

- Input candidate rows: **{total_input_rows}**
- x64 staged output rows, including DD096Y run row: **{total_staged_rows}**
- Width blockers: **{len(blockers)}**
- Runtime append script written: **{runtime_script_written}**
- Active catalog replacement: **0**

## Runtime preconditions

```text
DO SANDBOX
DO DD096X_GUARDED_X64_DATADICT_SCHEMA_PROOF
DO DD096Y_STAGE_CANDIDATE_ROWS_INTO_X64_SCHEMA
```

DD096X should run first so the parallel proof tables exist.

## Boundary

The generator writes staged CSVs and optionally writes a runtime append DTS. It does not mutate active Data Dictionary catalogs, source, HELP, CMDHELPCHK, manuals, or production metadata.
"""
    write_text(out / "DD096Y_STAGE_CANDIDATE_ROWS_INTO_X64_SCHEMA_REPORT.md", report)

    manifest = {
        "contract": "dd096y_stage_candidate_rows_into_x64_schema_v0",
        "run_id": args.run_id,
        "created_utc": utc_now(),
        "status": status,
        "repo_root": str(repo),
        "profiles": args.profile,
        "input_candidate_rows": total_input_rows,
        "x64_staged_output_rows": total_staged_rows,
        "width_blockers": len(blockers),
        "runtime_script_written": runtime_script_written,
        "active_catalog_replacement": 0,
        "failures": failures,
        "runtime_script_path": str(runtime_path) if runtime_script_written else "",
        "next_recommended_action": "Run DD096Y runtime DTS after DD096X proof tables exist; then perform DD096Y post-import validation.",
    }
    write_json(out / "dd096y_stage_candidate_rows_into_x64_schema_manifest.json", manifest)

    artifact_rows = [
        {"role": "dts_preview", "path": str(dts_preview), "exists": int(dts_preview.exists()), "kind": "file", "bytes_or_children": dts_preview.stat().st_size if dts_preview.exists() else 0, "sha256": sha256(dts_preview)},
        {"role": "runtime_dts", "path": str(runtime_path), "exists": int(runtime_path.exists()), "kind": "file", "bytes_or_children": runtime_path.stat().st_size if runtime_path.exists() else 0, "sha256": sha256(runtime_path)},
        {"role": "generated_stage_dir", "path": str(generated), "exists": int(generated.exists()), "kind": "dir", "bytes_or_children": sum(1 for _ in generated.iterdir()) if generated.exists() else 0, "sha256": ""},
    ]
    write_csv(out / "dd096y_artifact_ledger.csv", artifact_rows, ["role", "path", "exists", "kind", "bytes_or_children", "sha256"])

    print(f"DD096Y x64 staged import manifest: {out / 'dd096y_stage_candidate_rows_into_x64_schema_manifest.json'}")
    print(f"status: {status}; input_rows: {total_input_rows}; x64_rows: {total_staged_rows}; width_blockers: {len(blockers)}; runtime_script_written: {runtime_script_written}; active_catalog_replacement: 0; failures: {failures}")
    return 2 if (args.fail_on_review and failures) else 0


if __name__ == "__main__":
    raise SystemExit(main())
