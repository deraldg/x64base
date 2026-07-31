#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import re
from pathlib import Path
from typing import Any, Dict, List


EXPECTED_COUNTS = {
    "DATA_DICTIONARY_OBJECTS": 10,
    "DATA_DICTIONARY_OBJECT_ATTRIBUTES": 127,
    "DATA_DICTIONARY_RELATION_EDGES": 16,
    "DATA_DICTIONARY_EVIDENCE_RECORDS": 7,
    "DATA_DICTIONARY_GATE_RECORDS": 3,
    "DATA_DICTIONARY_RUNS": 2,
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


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path and path.exists() else ""


def make_validation_dts() -> str:
    lines: List[str] = []
    lines.append("* DD096YQ post-import validation/readback for x64 Data Dictionary proof schema")
    lines.append("* PRECONDITION: run DD096X, then DD096Y in SANDBOX before this validation.")
    lines.append("* This script reads SANDBOX proof tables only. It does not mutate active datadict.")
    lines.append("")
    lines.append("DO SANDBOX")
    lines.append("CLOSE ALL")
    lines.append("")
    for table, expected in EXPECTED_COUNTS.items():
        lines.append(f"* ---------------- {table} expected records: {expected} ----------------")
        lines.append(f"USE {table}")
        lines.append("AREA")
        lines.append("STRUCT")
        lines.append("TOP")
        lines.append("LIST")
        lines.append("CLOSE ALL")
        lines.append("")
    lines.append("* DD096YQ done. Verify each AREA reports the expected Recs count above.")
    lines.append("")
    return "\n".join(lines) + "\n\n"


def parse_runtime_proof(text: str) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    current_table = ""
    current_flavor = ""
    current_runtime = ""

    # We parse AREA blocks. Each table can appear multiple times; keep the last observed Recs count/flavor/runtime.
    found: Dict[str, Dict[str, Any]] = {}
    for line in text.splitlines():
        m = re.search(r"File:\s+([A-Z0-9_]+)\s+Recs:\s+(\d+)", line, re.IGNORECASE)
        if m:
            current_table = m.group(1).upper()
            row = found.setdefault(current_table, {
                "table_name": current_table,
                "observed_recs": "",
                "expected_recs": EXPECTED_COUNTS.get(current_table, ""),
                "dbf_flavor": "",
                "runtime_kind": "",
                "seen": 1,
            })
            row["observed_recs"] = int(m.group(2))
            row["seen"] = 1
            continue
        if current_table:
            m = re.search(r"DBF Flavor\s*:\s*([A-Za-z0-9_]+)", line)
            if m:
                found.setdefault(current_table, {"table_name": current_table})["dbf_flavor"] = m.group(1)
            m = re.search(r"Runtime kind\s*:\s*([A-Za-z0-9_]+)", line)
            if m:
                found.setdefault(current_table, {"table_name": current_table})["runtime_kind"] = m.group(1)

    for table, expected in EXPECTED_COUNTS.items():
        row = found.get(table, {
            "table_name": table,
            "observed_recs": "",
            "expected_recs": expected,
            "dbf_flavor": "",
            "runtime_kind": "",
            "seen": 0,
        })
        row["expected_recs"] = expected
        obs = row.get("observed_recs", "")
        row["count_pass"] = int(str(obs) != "" and int(obs) == expected)
        row["v64_pass"] = int(str(row.get("dbf_flavor", "")).lower() == "v64" and str(row.get("runtime_kind", "")).lower() == "v64")
        rows.append(row)

    return rows


def main() -> int:
    ap = argparse.ArgumentParser(description="DD096YQ post-import validation/readback for x64 Data Dictionary proof schema")
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--run-id", default="DD096YQ-post-import-validation-readback-v0")
    ap.add_argument("--runtime-proof", default="")
    ap.add_argument("--write-runtime-script", action="store_true")
    ap.add_argument("--profile", action="append", default=[])
    ap.add_argument("--fail-on-review", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    out = Path(args.out_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)
    gen = out / "generated_post_import_validation"
    gen.mkdir(parents=True, exist_ok=True)

    expected_rows = [
        {"table_name": table, "expected_recs": recs, "validation_source": "DD096X seed row + DD096Y staged rows"}
        for table, recs in EXPECTED_COUNTS.items()
    ]
    write_csv(gen / "dd096yq_expected_counts.csv", expected_rows, ["table_name", "expected_recs", "validation_source"])

    dts_text = make_validation_dts()
    preview_path = gen / "DD096YQ_POST_IMPORT_VALIDATION_READBACK.dts"
    write_text(preview_path, dts_text)

    runtime_script_written = 0
    runtime_path = repo / "dottalkpp/data/scripts/DD096YQ_POST_IMPORT_VALIDATION_READBACK.dts"
    if args.write_runtime_script:
        write_text(runtime_path, dts_text)
        runtime_script_written = 1

    runtime_rows: List[Dict[str, Any]] = []
    proof_supplied = 0
    if args.runtime_proof:
        proof_path = (repo / args.runtime_proof).resolve() if not Path(args.runtime_proof).is_absolute() else Path(args.runtime_proof)
        text = read_text(proof_path)
        proof_supplied = int(bool(text))
        runtime_rows = parse_runtime_proof(text)
    else:
        runtime_rows = [
            {"table_name": table, "expected_recs": recs, "observed_recs": "", "dbf_flavor": "", "runtime_kind": "", "seen": 0, "count_pass": 0, "v64_pass": 0}
            for table, recs in EXPECTED_COUNTS.items()
        ]

    write_csv(gen / "dd096yq_runtime_readback_validation.csv", runtime_rows, [
        "table_name", "expected_recs", "observed_recs", "dbf_flavor", "runtime_kind", "seen", "count_pass", "v64_pass"
    ])

    count_failures = sum(1 for r in runtime_rows if int(r.get("count_pass", 0)) != 1) if proof_supplied else 0
    v64_failures = sum(1 for r in runtime_rows if int(r.get("v64_pass", 0)) != 1) if proof_supplied else 0
    status = "DD096YQ_POST_IMPORT_VALIDATION_READY"
    if proof_supplied and count_failures == 0 and v64_failures == 0:
        status = "DD096YQ_POST_IMPORT_VALIDATION_GREEN"
    elif proof_supplied:
        status = "DD096YQ_POST_IMPORT_VALIDATION_REVIEW"

    gates = [
        {"gate": "expected_counts_written", "expected": 6, "observed": len(expected_rows), "pass": int(len(expected_rows) == 6)},
        {"gate": "runtime_script_written_if_requested", "expected": int(args.write_runtime_script), "observed": runtime_script_written, "pass": int(runtime_script_written == int(args.write_runtime_script))},
        {"gate": "runtime_proof_supplied", "expected": "optional", "observed": proof_supplied, "pass": 1},
        {"gate": "count_failures_if_proof_supplied", "expected": 0, "observed": count_failures, "pass": int((not proof_supplied) or count_failures == 0)},
        {"gate": "v64_failures_if_proof_supplied", "expected": 0, "observed": v64_failures, "pass": int((not proof_supplied) or v64_failures == 0)},
        {"gate": "active_catalog_replacement_not_authorized", "expected": 0, "observed": 0, "pass": 1},
    ]
    failures = sum(1 for r in gates if int(r["pass"]) != 1)
    write_csv(out / "dd096yq_gate_ledger.csv", gates, ["gate", "expected", "observed", "pass"])

    boundary = [
        {"boundary": "post_import_validation_only", "observed": 1, "required": 1, "pass": 1},
        {"boundary": "active_datadict_catalog_replacement", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "active_datadict_dbf_append_replace_delete_pack_zap_by_generator", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "runtime_validation_script_written", "observed": runtime_script_written, "required": int(args.write_runtime_script), "pass": 1},
        {"boundary": "source_edits", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "help_meta_cmdhelpchk_mutation", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "manual_publication_mutation", "observed": 0, "required": 0, "pass": 1},
    ]
    write_csv(out / "dd096yq_no_mutation_boundary_ledger.csv", boundary, ["boundary", "observed", "required", "pass"])

    report = f"""# DD096YQ Post-Import Validation / Readback

Run id: `{args.run_id}`
Status: **{status}**
Created UTC: `{utc_now()}`

## Purpose

DD096YQ validates the DD096Y staged import into the DD096X parallel x64 Data Dictionary proof schema.

Expected record counts after DD096X + DD096Y are:

```text
DATA_DICTIONARY_OBJECTS             10
DATA_DICTIONARY_OBJECT_ATTRIBUTES  127
DATA_DICTIONARY_RELATION_EDGES      16
DATA_DICTIONARY_EVIDENCE_RECORDS     7
DATA_DICTIONARY_GATE_RECORDS         3
DATA_DICTIONARY_RUNS                 2
```

## Runtime validation

Run this in DotTalk++ after DD096X and DD096Y:

```text
DO SANDBOX
DO DD096YQ_POST_IMPORT_VALIDATION_READBACK
```

## Summary

- Runtime script written: **{runtime_script_written}**
- Runtime proof supplied to parser: **{proof_supplied}**
- Count failures: **{count_failures}**
- v64 failures: **{v64_failures}**
- Active catalog replacement: **0**

## Boundary

This lane validates SANDBOX proof tables only. It does not replace the active Data Dictionary catalog, mutate HELP/CMDHELPCHK, edit source, rebuild manuals, or promote production metadata.
"""
    write_text(out / "DD096YQ_POST_IMPORT_VALIDATION_READBACK_REPORT.md", report)

    manifest = {
        "contract": "dd096yq_post_import_validation_readback_v0",
        "run_id": args.run_id,
        "created_utc": utc_now(),
        "status": status,
        "repo_root": str(repo),
        "profiles": args.profile,
        "runtime_script_written": runtime_script_written,
        "runtime_proof_supplied": proof_supplied,
        "count_failures": count_failures,
        "v64_failures": v64_failures,
        "active_catalog_replacement": 0,
        "failures": failures,
        "next_recommended_action": "Run runtime validation script; if green, proceed to DD096Z promotion planning only.",
    }
    write_json(out / "dd096yq_post_import_validation_readback_manifest.json", manifest)

    print(f"DD096YQ post-import validation manifest: {out / 'dd096yq_post_import_validation_readback_manifest.json'}")
    print(f"status: {status}; runtime_script_written: {runtime_script_written}; proof_supplied: {proof_supplied}; count_failures: {count_failures}; v64_failures: {v64_failures}; active_catalog_replacement: 0; failures: {failures}")
    return 2 if (args.fail_on_review and failures) else 0


if __name__ == "__main__":
    raise SystemExit(main())
