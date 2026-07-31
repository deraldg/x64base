#!/usr/bin/env python3
from __future__ import annotations
import argparse
import csv
import datetime as dt
import json
import struct
from pathlib import Path
from typing import Dict, List

EXPECTED = {
    "DATA_DICTIONARY_OBJECTS": 10,
    "DATA_DICTIONARY_OBJECT_ATTRIBUTES": 127,
    "DATA_DICTIONARY_RELATION_EDGES": 16,
    "DATA_DICTIONARY_EVIDENCE_RECORDS": 7,
    "DATA_DICTIONARY_GATE_RECORDS": 3,
    "DATA_DICTIONARY_RUNS": 2,
}

def now():
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")

def read_json(path: Path):
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return {}

def wt(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")

def wj(path: Path, obj):
    wt(path, json.dumps(obj, indent=2, sort_keys=True) + "\n")

def wc(path: Path, rows: List[Dict], fields: List[str]):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        w.writeheader()
        for row in rows:
            w.writerow({k: row.get(k, "") for k in fields})

def dbf_header_info(path: Path) -> Dict:
    if not path.exists():
        return {
            "exists": 0,
            "version_byte_hex": "",
            "record_count": "",
            "header_length": "",
            "record_length": "",
            "bytes": 0,
        }
    data = path.read_bytes()[:32]
    if len(data) < 32:
        return {
            "exists": 1,
            "version_byte_hex": "",
            "record_count": "",
            "header_length": "",
            "record_length": "",
            "bytes": path.stat().st_size,
            "parse_error": "header_too_short",
        }
    version = data[0]
    rec_count = struct.unpack("<I", data[4:8])[0]
    header_len = struct.unpack("<H", data[8:10])[0]
    record_len = struct.unpack("<H", data[10:12])[0]
    return {
        "exists": 1,
        "version_byte_hex": f"0x{version:02X}",
        "record_count": rec_count,
        "header_length": header_len,
        "record_length": record_len,
        "bytes": path.stat().st_size,
        "parse_error": "",
    }

def make_runtime_dts(candidate_dbf: Path, candidate_index: Path, candidate_lmdb: Path) -> str:
    lines = []
    lines.append("* DD096Z-C candidate-root readback validation")
    lines.append("* This targets the inactive candidate root, not the active Data Dictionary catalog.")
    lines.append("* If SETPATH syntax changes, run the USE/AREA/STRUCT/LIST sequence manually after setting paths.")
    lines.append("")
    lines.append(f"SETPATH DBF {candidate_dbf}")
    lines.append(f"SETPATH INDEXES {candidate_index}")
    lines.append(f"SETPATH LMDB {candidate_lmdb}")
    lines.append("CLOSE ALL")
    lines.append("")
    for table, expected in EXPECTED.items():
        lines.append(f"* ---------------- {table} expected records: {expected} ----------------")
        lines.append(f"USE {table}")
        lines.append("AREA")
        lines.append("STRUCT")
        lines.append("TOP")
        lines.append("LIST")
        lines.append("CLOSE ALL")
        lines.append("")
    lines.append("* DD096Z-C done. Candidate readback should show expected counts and v64 runtime kind.")
    lines.append("")
    return "\n".join(lines) + "\n\n"

def parse_runtime_proof(text: str) -> List[Dict]:
    rows = []
    found = {}
    current = ""
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("File: "):
            parts = s.split()
            # Expected: File: NAME Recs: N Recno: 1
            if len(parts) >= 4:
                current = parts[1].upper()
                recs = ""
                if "Recs:" in parts:
                    i = parts.index("Recs:")
                    if i + 1 < len(parts):
                        recs = parts[i + 1]
                found.setdefault(current, {})["observed_recs"] = recs
        elif current and s.startswith("DBF Flavor"):
            found.setdefault(current, {})["dbf_flavor"] = s.split(":", 1)[1].strip()
        elif current and s.startswith("Runtime kind"):
            found.setdefault(current, {})["runtime_kind"] = s.split(":", 1)[1].strip()
    for table, expected in EXPECTED.items():
        got = found.get(table, {})
        obs = got.get("observed_recs", "")
        count_pass = int(str(obs).isdigit() and int(obs) == expected)
        v64_pass = int(got.get("dbf_flavor", "").lower() == "v64" and got.get("runtime_kind", "").lower() == "v64")
        rows.append({
            "table": table,
            "expected_recs": expected,
            "observed_recs": obs,
            "dbf_flavor": got.get("dbf_flavor", ""),
            "runtime_kind": got.get("runtime_kind", ""),
            "count_pass": count_pass,
            "v64_pass": v64_pass,
        })
    return rows

def main():
    ap = argparse.ArgumentParser(description="DD096Z-C candidate-root readback validation")
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--run-id", default="DD096ZC-candidate-root-readback-validation-v0")
    ap.add_argument("--dd096zb-dir", default="docs/datadict/reports/DD096ZB-backup-and-inactive-candidate-staging-v0")
    ap.add_argument("--runtime-proof", default="")
    ap.add_argument("--write-runtime-script", action="store_true")
    ap.add_argument("--profile", action="append", default=[])
    ap.add_argument("--fail-on-review", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    out = Path(args.out_dir).resolve()
    gen = out / "generated_candidate_readback_validation"
    gen.mkdir(parents=True, exist_ok=True)

    zb_manifest_path = repo / args.dd096zb_dir / "dd096zb_backup_and_inactive_candidate_staging_manifest.json"
    zb = read_json(zb_manifest_path)
    candidate_root = Path(zb.get("candidate_root", repo / "docs/datadict/candidates/DD096ZB-backup-and-inactive-candidate-staging-v0"))
    candidate_dbf = Path(zb.get("candidate_dbf_root", candidate_root / "dbf"))
    candidate_index = candidate_root / "indexes"
    candidate_lmdb = candidate_root / "lmdb"

    precondition_rows = [{
        "lane": "DD096ZB",
        "manifest_path": str(zb_manifest_path),
        "observed_status": zb.get("status", "MISSING"),
        "expected_status": "DD096ZB_BACKUP_CANDIDATE_STAGING_EXECUTED",
        "pass": int(zb.get("status") == "DD096ZB_BACKUP_CANDIDATE_STAGING_EXECUTED"),
    }]
    wc(gen / "dd096zc_precondition_ledger.csv", precondition_rows, ["lane","manifest_path","observed_status","expected_status","pass"])

    header_rows = []
    for table, expected in EXPECTED.items():
        path = candidate_dbf / f"{table}.dbf"
        info = dbf_header_info(path)
        observed = info.get("record_count", "")
        header_rows.append({
            "table": table,
            "path": str(path),
            "exists": info.get("exists", 0),
            "expected_recs": expected,
            "header_record_count": observed,
            "record_count_pass": int(str(observed).isdigit() and int(observed) == expected),
            "version_byte_hex": info.get("version_byte_hex", ""),
            "header_length": info.get("header_length", ""),
            "record_length": info.get("record_length", ""),
            "bytes": info.get("bytes", 0),
            "parse_error": info.get("parse_error", ""),
        })
    wc(gen / "dd096zc_candidate_dbf_header_validation.csv", header_rows, [
        "table","path","exists","expected_recs","header_record_count","record_count_pass","version_byte_hex","header_length","record_length","bytes","parse_error"
    ])

    dts_text = make_runtime_dts(candidate_dbf, candidate_index, candidate_lmdb)
    preview = gen / "DD096ZC_CANDIDATE_ROOT_READBACK_VALIDATION.dts"
    wt(preview, dts_text)

    runtime_script_written = 0
    runtime_path = repo / "dottalkpp/data/scripts/DD096ZC_CANDIDATE_ROOT_READBACK_VALIDATION.dts"
    if args.write_runtime_script:
        wt(runtime_path, dts_text)
        runtime_script_written = 1

    proof_supplied = 0
    runtime_rows = []
    if args.runtime_proof:
        p = Path(args.runtime_proof)
        if not p.is_absolute():
            p = repo / p
        text = p.read_text(encoding="utf-8", errors="replace") if p.exists() else ""
        proof_supplied = int(bool(text))
        runtime_rows = parse_runtime_proof(text)
    else:
        runtime_rows = [
            {"table": t, "expected_recs": e, "observed_recs": "", "dbf_flavor": "", "runtime_kind": "", "count_pass": 0, "v64_pass": 0}
            for t, e in EXPECTED.items()
        ]
    wc(gen / "dd096zc_runtime_readback_validation.csv", runtime_rows, ["table","expected_recs","observed_recs","dbf_flavor","runtime_kind","count_pass","v64_pass"])

    header_failures = sum(1 for r in header_rows if int(r["record_count_pass"]) != 1)
    precondition_failures = sum(1 for r in precondition_rows if int(r["pass"]) != 1)
    runtime_count_failures = sum(1 for r in runtime_rows if int(r["count_pass"]) != 1) if proof_supplied else 0
    runtime_v64_failures = sum(1 for r in runtime_rows if int(r["v64_pass"]) != 1) if proof_supplied else 0

    if precondition_failures or header_failures:
        status = "DD096ZC_CANDIDATE_ROOT_READBACK_REVIEW"
    elif proof_supplied and runtime_count_failures == 0 and runtime_v64_failures == 0:
        status = "DD096ZC_CANDIDATE_ROOT_READBACK_GREEN"
    else:
        status = "DD096ZC_CANDIDATE_ROOT_READBACK_READY"

    gates = [
        {"gate": "dd096zb_executed", "expected": 1, "observed": int(precondition_failures == 0), "pass": int(precondition_failures == 0)},
        {"gate": "candidate_header_counts_green", "expected": 0, "observed": header_failures, "pass": int(header_failures == 0)},
        {"gate": "runtime_script_written_if_requested", "expected": int(args.write_runtime_script), "observed": runtime_script_written, "pass": int(runtime_script_written == int(args.write_runtime_script))},
        {"gate": "runtime_count_failures_if_proof_supplied", "expected": 0, "observed": runtime_count_failures, "pass": int((not proof_supplied) or runtime_count_failures == 0)},
        {"gate": "runtime_v64_failures_if_proof_supplied", "expected": 0, "observed": runtime_v64_failures, "pass": int((not proof_supplied) or runtime_v64_failures == 0)},
        {"gate": "active_catalog_replacement", "expected": 0, "observed": 0, "pass": 1},
    ]
    failures = sum(1 for r in gates if int(r["pass"]) != 1)
    wc(out / "dd096zc_gate_ledger.csv", gates, ["gate","expected","observed","pass"])

    boundary = [
        ("candidate_root_readback_validation_only", 1, 1, 1),
        ("active_catalog_replacement", 0, 0, 1),
        ("active_catalog_dbf_copy_or_write", 0, 0, 1),
        ("active_cdx_lmdb_rebuild", 0, 0, 1),
        ("workspace_schema_mutation", 0, 0, 1),
        ("source_edits", 0, 0, 1),
        ("help_meta_cmdhelpchk_mutation", 0, 0, 1),
        ("manual_publication_mutation", 0, 0, 1),
    ]
    wc(out / "dd096zc_no_mutation_boundary_ledger.csv",
       [{"boundary": a, "observed": b, "required": c, "pass": d} for a,b,c,d in boundary],
       ["boundary","observed","required","pass"])

    report = f"""# DD096Z-C Candidate-Root Readback Validation

Run id: `{args.run_id}`
Status: **{status}**
Created UTC: `{now()}`

## Purpose

DD096Z-C validates the inactive candidate Data Dictionary root staged by DD096Z-B.

It does not replace the active Data Dictionary catalog.

## Summary

- Candidate root: `{candidate_root}`
- Candidate DBF root: `{candidate_dbf}`
- Header count failures: **{header_failures}**
- Runtime proof supplied: **{proof_supplied}**
- Runtime count failures: **{runtime_count_failures}**
- Runtime v64 failures: **{runtime_v64_failures}**
- Active catalog replacement: **0**

## Next lane

If candidate readback is green, DD096Z-D should plan candidate CDX/LMDB rebuild. Active catalog switch is still not authorized.
"""
    wt(out / "DD096ZC_CANDIDATE_ROOT_READBACK_VALIDATION_REPORT.md", report)

    manifest = {
        "contract": "dd096zc_candidate_root_readback_validation_v0",
        "run_id": args.run_id,
        "created_utc": now(),
        "status": status,
        "repo_root": str(repo),
        "profiles": args.profile,
        "candidate_root": str(candidate_root),
        "candidate_dbf_root": str(candidate_dbf),
        "header_count_failures": header_failures,
        "runtime_script_written": runtime_script_written,
        "runtime_proof_supplied": proof_supplied,
        "runtime_count_failures": runtime_count_failures,
        "runtime_v64_failures": runtime_v64_failures,
        "active_catalog_replacement": 0,
        "failures": failures,
        "next_recommended_action": "DD096Z-D candidate CDX/LMDB rebuild plan; no active replacement yet.",
    }
    wj(out / "dd096zc_candidate_root_readback_validation_manifest.json", manifest)

    print(f"DD096Z-C candidate readback manifest: {out / 'dd096zc_candidate_root_readback_validation_manifest.json'}")
    print(f"status: {status}; header_count_failures: {header_failures}; runtime_script_written: {runtime_script_written}; proof_supplied: {proof_supplied}; active_catalog_replacement: 0; failures: {failures}")
    return 2 if (args.fail_on_review and failures) else 0

if __name__ == "__main__":
    raise SystemExit(main())
