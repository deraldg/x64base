#!/usr/bin/env python3
from __future__ import annotations
import argparse
import csv
import datetime as dt
import json
import re
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

REQUIRED = {
    "DD096ZG": (
        "docs/datadict/reports/DD096ZG-candidate-smoke-harness-design-v0/dd096zg_candidate_smoke_harness_design_manifest.json",
        ["DD096ZG_CANDIDATE_SMOKE_HARNESS_DESIGN_READY"],
    ),
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

def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")

def parse_transcript(text: str):
    rows = []
    found = {}
    current = ""
    dbf_root_hits = 0
    active_root_hits = 0
    future_contract_hits = 0

    if "docs\\datadict\\candidates\\DD096ZB-backup-and-inactive-candidate-staging-v0\\dbf" in text or "docs/datadict/candidates/DD096ZB-backup-and-inactive-candidate-staging-v0/dbf" in text:
        dbf_root_hits = 1
    if "dottalkpp\\data\\datadict" in text.lower() or "dottalkpp/data/datadict" in text.lower():
        active_root_hits = 1
    if "FUTURE_DDICT_BRIDGE_SMOKE_CONTRACT" in text.upper():
        future_contract_hits = 1

    for line in text.splitlines():
        m = re.search(r"Opened\s+([A-Z0-9_]+)\s+\(v64\)\s*:\s*Record count\s+(\d+)", line, re.IGNORECASE)
        if m:
            table = m.group(1).upper()
            found.setdefault(table, {})["opened_count"] = int(m.group(2))
            current = table
            continue
        m = re.search(r"File:\s+([A-Z0-9_]+)\s+Recs:\s+(\d+)", line, re.IGNORECASE)
        if m:
            table = m.group(1).upper()
            found.setdefault(table, {})["area_count"] = int(m.group(2))
            current = table
            continue
        if current:
            m = re.search(r"DBF Flavor\s*:\s*([A-Za-z0-9_]+)", line)
            if m:
                found.setdefault(current, {})["dbf_flavor"] = m.group(1)
            m = re.search(r"Runtime kind\s*:\s*([A-Za-z0-9_]+)", line)
            if m:
                found.setdefault(current, {})["runtime_kind"] = m.group(1)
            m = re.search(r"Path:\s*(.*)", line)
            if m:
                found.setdefault(current, {})["path"] = m.group(1).strip()

    for table, expected in EXPECTED.items():
        got = found.get(table, {})
        observed = got.get("area_count", got.get("opened_count", ""))
        opened = got.get("opened_count", "")
        count_pass = int(str(observed).isdigit() and int(observed) == expected)
        opened_pass = int(str(opened).isdigit() and int(opened) == expected)
        v64_pass = int(str(got.get("dbf_flavor", "")).lower() == "v64" and str(got.get("runtime_kind", "")).lower() == "v64")
        candidate_path_pass = int("docs" in str(got.get("path", "")).lower() and "datadict" in str(got.get("path", "")).lower() and "candidates" in str(got.get("path", "")).lower())
        rows.append({
            "table": table,
            "expected_recs": expected,
            "opened_count": opened,
            "area_count": got.get("area_count", ""),
            "dbf_flavor": got.get("dbf_flavor", ""),
            "runtime_kind": got.get("runtime_kind", ""),
            "path": got.get("path", ""),
            "opened_pass": opened_pass,
            "count_pass": count_pass,
            "v64_pass": v64_pass,
            "candidate_path_pass": candidate_path_pass,
        })
    return rows, dbf_root_hits, active_root_hits, future_contract_hits

def main():
    ap = argparse.ArgumentParser(description="DD096ZG-Q candidate raw-smoke transcript closure")
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--run-id", default="DD096ZGQ-candidate-raw-smoke-closure-v0")
    ap.add_argument("--runtime-proof", required=True)
    ap.add_argument("--profile", action="append", default=[])
    ap.add_argument("--fail-on-review", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    out = Path(args.out_dir).resolve()
    gen = out / "generated_candidate_raw_smoke_closure"
    gen.mkdir(parents=True, exist_ok=True)

    pre = []
    blockers = 0
    for lane, (rel, expected_list) in REQUIRED.items():
        path = repo / rel
        data = read_json(path)
        observed = data.get("status", "MISSING")
        passed = int(observed in expected_list)
        blockers += 0 if passed else 1
        pre.append({
            "lane": lane,
            "manifest_path": str(path),
            "observed_status": observed,
            "expected_status": "|".join(expected_list),
            "pass": passed,
        })
    wc(gen / "dd096zgq_precondition_ledger.csv", pre, ["lane","manifest_path","observed_status","expected_status","pass"])

    proof_path = Path(args.runtime_proof)
    if not proof_path.is_absolute():
        proof_path = repo / proof_path
    text = read_text(proof_path)
    proof_supplied = int(bool(text))

    runtime_rows, candidate_root_seen, active_root_seen, future_contract_seen = parse_transcript(text)
    wc(gen / "dd096zgq_runtime_readback_validation.csv", runtime_rows, [
        "table","expected_recs","opened_count","area_count","dbf_flavor","runtime_kind","path","opened_pass","count_pass","v64_pass","candidate_path_pass"
    ])

    count_failures = sum(1 for r in runtime_rows if int(r["count_pass"]) != 1)
    opened_failures = sum(1 for r in runtime_rows if int(r["opened_pass"]) != 1)
    v64_failures = sum(1 for r in runtime_rows if int(r["v64_pass"]) != 1)
    candidate_path_failures = sum(1 for r in runtime_rows if int(r["candidate_path_pass"]) != 1)

    boundary = [
        ("candidate_raw_smoke_closure_only", 1, 1, 1),
        ("runtime_proof_supplied", proof_supplied, 1, int(proof_supplied == 1)),
        ("future_ddict_bridge_contract_not_executed", 0 if future_contract_seen else 1, 1, int(future_contract_seen == 0)),
        ("active_catalog_replacement", 0, 0, 1),
        ("active_catalog_dbf_copy_or_write", 0, 0, 1),
        ("candidate_cdx_lmdb_rebuild", 0, 0, 1),
        ("active_cdx_lmdb_rebuild", 0, 0, 1),
        ("source_edits", 0, 0, 1),
        ("build_file_edits", 0, 0, 1),
        ("workspace_schema_mutation", 0, 0, 1),
        ("help_meta_cmdhelpchk_mutation", 0, 0, 1),
        ("manual_publication_mutation", 0, 0, 1),
    ]
    wc(out / "dd096zgq_no_mutation_boundary_ledger.csv",
       [{"boundary": a, "observed": b, "required": c, "pass": d} for a,b,c,d in boundary],
       ["boundary","observed","required","pass"])

    gates = [
        {"gate": "preconditions_green", "expected": 0, "observed": blockers, "pass": int(blockers == 0)},
        {"gate": "runtime_proof_supplied", "expected": 1, "observed": proof_supplied, "pass": int(proof_supplied == 1)},
        {"gate": "candidate_root_seen", "expected": 1, "observed": candidate_root_seen, "pass": int(candidate_root_seen == 1)},
        {"gate": "active_root_not_seen", "expected": 0, "observed": active_root_seen, "pass": int(active_root_seen == 0)},
        {"gate": "opened_count_failures", "expected": 0, "observed": opened_failures, "pass": int(opened_failures == 0)},
        {"gate": "area_count_failures", "expected": 0, "observed": count_failures, "pass": int(count_failures == 0)},
        {"gate": "v64_failures", "expected": 0, "observed": v64_failures, "pass": int(v64_failures == 0)},
        {"gate": "candidate_path_failures", "expected": 0, "observed": candidate_path_failures, "pass": int(candidate_path_failures == 0)},
        {"gate": "future_contract_not_executed", "expected": 0, "observed": future_contract_seen, "pass": int(future_contract_seen == 0)},
    ]
    failures = sum(1 for row in gates if int(row["pass"]) != 1)
    wc(out / "dd096zgq_gate_ledger.csv", gates, ["gate","expected","observed","pass"])

    status = "DD096ZGQ_CANDIDATE_RAW_SMOKE_CLOSURE_GREEN" if failures == 0 else "DD096ZGQ_CANDIDATE_RAW_SMOKE_CLOSURE_REVIEW"

    report = f"""# DD096ZG-Q Candidate Raw-Smoke Transcript Closure

Run id: `{args.run_id}`
Status: **{status}**
Created UTC: `{now()}`

## Purpose

DD096ZG-Q closes the runnable candidate raw-smoke lane by parsing the DD096ZG runtime transcript.

It validates the inactive candidate DATA_DICTIONARY_* tables only. It does not validate the future DDICT resolver bridge contract.

## Summary

- Runtime proof supplied: **{proof_supplied}**
- Candidate root seen: **{candidate_root_seen}**
- Active root seen: **{active_root_seen}**
- Opened-count failures: **{opened_failures}**
- Area-count failures: **{count_failures}**
- v64 failures: **{v64_failures}**
- Candidate-path failures: **{candidate_path_failures}**
- Future DDICT bridge contract executed: **{future_contract_seen}**
- Active catalog replacement: **0**
- Source edits: **0**

## Interpretation

If green, the inactive candidate root has runtime readback proof independent of the active Data Dictionary catalog.

## Next lane

DD096Z-D2 candidate-only CDX/LMDB rebuild execution is the next safe infrastructure lane. DD096Z-F3 guarded resolver source apply remains a separate explicit-authorization lane.
"""
    wt(out / "DD096ZGQ_CANDIDATE_RAW_SMOKE_CLOSURE_REPORT.md", report)

    manifest = {
        "contract": "dd096zgq_candidate_raw_smoke_closure_v0",
        "run_id": args.run_id,
        "created_utc": now(),
        "status": status,
        "repo_root": str(repo),
        "profiles": args.profile,
        "runtime_proof": str(proof_path),
        "runtime_proof_supplied": proof_supplied,
        "candidate_root_seen": candidate_root_seen,
        "active_root_seen": active_root_seen,
        "opened_count_failures": opened_failures,
        "area_count_failures": count_failures,
        "v64_failures": v64_failures,
        "candidate_path_failures": candidate_path_failures,
        "future_contract_executed": future_contract_seen,
        "active_catalog_replacement": 0,
        "source_edits": 0,
        "candidate_cdx_lmdb_rebuild": 0,
        "failures": failures,
        "next_recommended_action": "DD096Z-D2 candidate-only CDX/LMDB rebuild execution, or separately authorized DD096Z-F3 resolver source apply.",
    }
    wj(out / "dd096zgq_candidate_raw_smoke_closure_manifest.json", manifest)

    print(f"DD096ZG-Q candidate raw-smoke closure manifest: {out / 'dd096zgq_candidate_raw_smoke_closure_manifest.json'}")
    print(f"status: {status}; proof_supplied: {proof_supplied}; opened_failures: {opened_failures}; count_failures: {count_failures}; v64_failures: {v64_failures}; active_catalog_replacement: 0; failures: {failures}")
    return 2 if (args.fail_on_review and failures) else 0

if __name__ == "__main__":
    raise SystemExit(main())
