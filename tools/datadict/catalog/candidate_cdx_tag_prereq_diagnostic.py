#!/usr/bin/env python3
from __future__ import annotations
import argparse
import csv
import datetime as dt
import json
import re
from pathlib import Path
from typing import Dict, List

REQUIRED = {
    "DD096ZGQ": (
        "docs/datadict/reports/DD096ZGQ-candidate-raw-smoke-closure-v0/dd096zgq_candidate_raw_smoke_closure_manifest.json",
        ["DD096ZGQ_CANDIDATE_RAW_SMOKE_CLOSURE_GREEN"],
    ),
    "DD096ZD2": (
        "docs/datadict/reports/DD096ZD2-candidate-only-cdx-lmdb-rebuild-execution-v0/dd096zd2_candidate_only_cdx_lmdb_rebuild_execution_manifest.json",
        [
            "DD096ZD2_CANDIDATE_ONLY_CDX_LMDB_REBUILD_EXECUTION_READY",
            "DD096ZD2_CANDIDATE_ONLY_CDX_LMDB_REBUILD_EXECUTION_REVIEW",
            "DD096ZD2_CANDIDATE_ONLY_CDX_LMDB_REBUILD_EXECUTION_GREEN",
        ],
    ),
}

TABLES = [
    ("DATA_DICTIONARY_OBJECTS", 10, [("CATALOG_OBJECT_ID", "CATALOG_OBJECT_ID"), ("CATALOG_OBJECT_NAME", "CATALOG_OBJECT_NAME")]),
    ("DATA_DICTIONARY_OBJECT_ATTRIBUTES", 127, [("CATALOG_OBJECT_ID", "CATALOG_OBJECT_ID"), ("CATALOG_ATTRIBUTE_NAME", "CATALOG_ATTRIBUTE_NAME")]),
    ("DATA_DICTIONARY_RELATION_EDGES", 16, [("RELATION_FROM_OBJECT_ID", "RELATION_FROM_OBJECT_ID"), ("RELATION_TO_OBJECT_ID", "RELATION_TO_OBJECT_ID")]),
    ("DATA_DICTIONARY_EVIDENCE_RECORDS", 7, [("CATALOG_OBJECT_ID", "CATALOG_OBJECT_ID")]),
    ("DATA_DICTIONARY_GATE_RECORDS", 3, [("GATE_RECORD_ID", "GATE_RECORD_ID")]),
    ("DATA_DICTIONARY_RUNS", 2, [("RUN_RECORD_ID", "RUN_RECORD_ID")]),
]

def now():
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")

def read_json(path: Path):
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return {}

def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")

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

def parse_runtime_proof(text: str) -> Dict:
    up = text.upper()
    opened = len(re.findall(r"OPENED\s+DATA_DICTIONARY_[A-Z_]+\s+\(V64\)\s*:\s*RECORD COUNT", up))
    lmdb_failed = len(re.findall(r"BUILDLMDB:\s*FAILED TO BUILD LMDB ENVIRONMENT", up))
    lmdb_target = len(re.findall(r"BUILDLMDB:\s*TARGET CONTAINER", up))
    env_lines = len(re.findall(r"BUILDLMDB:\s*LMDB ENV", up))
    index_none = len(re.findall(r"INDEX FILE\s*:\s*\(NONE\)", up))
    tags_none = len(re.findall(r"TAGS\s*:\s*\(NONE\)", up))
    candidate_path_seen = int("DOCS\\DATADICT\\CANDIDATES" in up or "DOCS/DATADICT/CANDIDATES" in up)
    active_datadict_seen = int("DOTTALKPP\\DATA\\DATADICT" in up or "DOTTALKPP/DATA/DATADICT" in up)
    cdx_valid_seen = len(re.findall(r"VALID INDEX/INDICES\s*:\s*CDX", up))
    return {
        "opened_v64_count": opened,
        "buildlmdb_target_count": lmdb_target,
        "buildlmdb_env_count": env_lines,
        "buildlmdb_failed_count": lmdb_failed,
        "index_none_count": index_none,
        "tags_none_count": tags_none,
        "valid_cdx_seen_count": cdx_valid_seen,
        "candidate_path_seen": candidate_path_seen,
        "active_datadict_seen": active_datadict_seen,
    }

def make_inventory_dts(candidate_dbf: Path, candidate_index: Path, candidate_lmdb: Path) -> str:
    lines = []
    lines.append("* DD096Z-D2R candidate CDX/tag prerequisite inventory")
    lines.append("* Safe inventory only. Candidate paths only.")
    lines.append(f"SETPATH DBF {candidate_dbf}")
    lines.append(f"SETPATH INDEXES {candidate_index}")
    lines.append(f"SETPATH LMDB {candidate_lmdb}")
    lines.append("CLOSE ALL")
    lines.append("")
    for table, expected, tags in TABLES:
        lines.append(f"* ---- inventory {table}; expected {expected} records ----")
        lines.append(f"USE {table}")
        lines.append("AREA")
        lines.append("STRUCT")
        lines.append("* Observe Index file, Tags, Active tag. Do not run BUILDLMDB in this inventory script.")
        lines.append("CLOSE ALL")
        lines.append("")
    return "\n".join(lines) + "\n\n"

def make_tag_syntax_probe_dts(candidate_dbf: Path, candidate_index: Path, candidate_lmdb: Path) -> str:
    lines = []
    lines.append("* DD096Z-D2R candidate tag syntax probe")
    lines.append("* REVIEW BEFORE RUNNING.")
    lines.append("* Candidate paths only. This is intended to prove the exact CDX/tag creation syntax on ONE small/representative table first.")
    lines.append("* If the first form works, stop and report transcript. Do not blindly run all variants.")
    lines.append("")
    lines.append(f"SETPATH DBF {candidate_dbf}")
    lines.append(f"SETPATH INDEXES {candidate_index}")
    lines.append(f"SETPATH LMDB {candidate_lmdb}")
    lines.append("CLOSE ALL")
    lines.append("USE DATA_DICTIONARY_RUNS")
    lines.append("AREA")
    lines.append("STRUCT")
    lines.append("")
    lines.append("* Candidate command forms to test one-at-a-time, based on observed project command surface.")
    lines.append("* Uncomment exactly one form during manual review, then rerun inventory.")
    lines.append("*")
    lines.append("* FORM A:")
    lines.append("* INDEX ON RUN_RECORD_ID TAG RUN_RECORD_ID")
    lines.append("*")
    lines.append("* FORM B:")
    lines.append("* CDX ADDTAG RUN_RECORD_ID RUN_RECORD_ID")
    lines.append("*")
    lines.append("* FORM C:")
    lines.append("* CDX ADDTAG RUN_RECORD_ID ON RUN_RECORD_ID")
    lines.append("*")
    lines.append("* FORM D:")
    lines.append("* TAG RUN_RECORD_ID ON RUN_RECORD_ID")
    lines.append("")
    lines.append("AREA")
    lines.append("* Do not BUILDLMDB until a real tag is visible in AREA.")
    lines.append("CLOSE ALL")
    lines.append("")
    return "\n".join(lines) + "\n\n"

def make_lmdb_retry_after_tags_dts(candidate_dbf: Path, candidate_index: Path, candidate_lmdb: Path) -> str:
    lines = []
    lines.append("* DD096Z-D2R LMDB retry after candidate tags are proven")
    lines.append("* DO NOT RUN until candidate tag inventory proves real tags exist.")
    lines.append(f"SETPATH DBF {candidate_dbf}")
    lines.append(f"SETPATH INDEXES {candidate_index}")
    lines.append(f"SETPATH LMDB {candidate_lmdb}")
    lines.append("CLOSE ALL")
    lines.append("")
    for table, expected, tags in TABLES:
        lines.append(f"* ---- LMDB retry {table}; expected {expected} records ----")
        lines.append(f"USE {table}")
        lines.append("AREA")
        lines.append("* Confirm Tags are not (none) before running BUILDLMDB.")
        lines.append("* BUILDLMDB CLEAN YES")
        lines.append("CLOSE ALL")
        lines.append("")
    return "\n".join(lines) + "\n\n"

def main():
    ap = argparse.ArgumentParser(description="DD096Z-D2R candidate CDX/tag prerequisite diagnostic")
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--run-id", default="DD096ZD2R-candidate-cdx-tag-prereq-diagnostic-v0")
    ap.add_argument("--runtime-proof", default="")
    ap.add_argument("--write-runtime-scripts", action="store_true")
    ap.add_argument("--profile", action="append", default=[])
    ap.add_argument("--fail-on-review", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    out = Path(args.out_dir).resolve()
    gen = out / "generated_candidate_cdx_tag_prereq_diagnostic"
    gen.mkdir(parents=True, exist_ok=True)

    manifests = {}
    pre = []
    blockers = 0
    for lane, (rel, expected_list) in REQUIRED.items():
        path = repo / rel
        data = read_json(path)
        manifests[lane] = data
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
    wc(gen / "dd096zd2r_precondition_ledger.csv", pre, ["lane","manifest_path","observed_status","expected_status","pass"])

    zb = read_json(repo / "docs/datadict/reports/DD096ZB-backup-and-inactive-candidate-staging-v0/dd096zb_backup_and_inactive_candidate_staging_manifest.json")
    candidate_root = Path(zb.get("candidate_root", repo / "docs/datadict/candidates/DD096ZB-backup-and-inactive-candidate-staging-v0"))
    candidate_dbf = Path(zb.get("candidate_dbf_root", candidate_root / "dbf"))
    candidate_index = candidate_root / "indexes"
    candidate_lmdb = candidate_root / "lmdb"

    target_rows = [
        {"root": "candidate_dbf", "path": str(candidate_dbf), "exists": int(candidate_dbf.exists()), "write_policy": "read_open_only"},
        {"root": "candidate_indexes", "path": str(candidate_index), "exists": int(candidate_index.exists()), "write_policy": "candidate_tags_only_after_manual_syntax_proof"},
        {"root": "candidate_lmdb", "path": str(candidate_lmdb), "exists": int(candidate_lmdb.exists()), "write_policy": "retry_only_after_tags_exist"},
        {"root": "active_datadict", "path": str(repo / "dottalkpp/data/datadict"), "exists": int((repo / "dottalkpp/data/datadict").exists()), "write_policy": "forbidden"},
        {"root": "active_indexes", "path": str(repo / "dottalkpp/data/indexes/datadict"), "exists": int((repo / "dottalkpp/data/indexes/datadict").exists()), "write_policy": "forbidden"},
        {"root": "active_lmdb", "path": str(repo / "dottalkpp/data/lmdb/datadict"), "exists": int((repo / "dottalkpp/data/lmdb/datadict").exists()), "write_policy": "forbidden"},
    ]
    wc(gen / "dd096zd2r_target_root_policy_ledger.csv", target_rows, ["root","path","exists","write_policy"])

    tag_rows = []
    for table, expected, tags in TABLES:
        for tag_name, expr in tags:
            tag_rows.append({
                "table": table,
                "expected_records": expected,
                "tag_name": tag_name,
                "expression": expr,
                "syntax_status": "requires_runtime_probe",
                "candidate_only": 1,
            })
    wc(gen / "dd096zd2r_candidate_tag_prereq_plan.csv", tag_rows, ["table","expected_records","tag_name","expression","syntax_status","candidate_only"])

    proof_supplied = 0
    proof = {}
    if args.runtime_proof:
        p = Path(args.runtime_proof)
        if not p.is_absolute():
            p = repo / p
        text = read_text(p)
        proof_supplied = int(bool(text))
        proof = parse_runtime_proof(text)
    else:
        proof = {
            "opened_v64_count": 0,
            "buildlmdb_target_count": 0,
            "buildlmdb_env_count": 0,
            "buildlmdb_failed_count": 0,
            "index_none_count": 0,
            "tags_none_count": 0,
            "valid_cdx_seen_count": 0,
            "candidate_path_seen": 0,
            "active_datadict_seen": 0,
        }
    proof_rows = [{"metric": k, "value": v} for k, v in proof.items()]
    proof_rows.append({"metric": "proof_supplied", "value": proof_supplied})
    wc(gen / "dd096zd2r_runtime_failure_diagnostic.csv", proof_rows, ["metric","value"])

    hypothesis_rows = [
        {
            "hypothesis_id": "D2R-H01",
            "hypothesis": "BUILDLMDB failed because candidate CDX containers/tags do not actually exist even though CDX is a valid index type.",
            "evidence": "Runtime shows Index file: (none), Tags: (none), then BUILDLMDB failed for each table.",
            "next_probe": "Create or prove a single candidate tag on DATA_DICTIONARY_RUNS before retrying BUILDLMDB.",
            "priority": "HIGH",
        },
        {
            "hypothesis_id": "D2R-H02",
            "hypothesis": "BUILDLMDB requires a non-empty CDX target container and cannot create one from DBF-only state.",
            "evidence": "BUILDLMDB target container paths were candidate-scoped but failed uniformly.",
            "next_probe": "After a candidate tag appears in AREA, rerun BUILDLMDB on that one table only.",
            "priority": "HIGH",
        },
        {
            "hypothesis_id": "D2R-H03",
            "hypothesis": "Long x64 table names or long field names may interact with CDX/LMDB path or tag generation.",
            "evidence": "Candidate tables have long DATA_DICTIONARY_* names and long field names.",
            "next_probe": "Start with DATA_DICTIONARY_RUNS and RUN_RECORD_ID; if still failing, test a short-name control table later.",
            "priority": "MEDIUM",
        },
        {
            "hypothesis_id": "D2R-H04",
            "hypothesis": "LMDB environment creation failure may be filesystem/path related.",
            "evidence": "Candidate lmdb backup directories were created, so write access seems partly available.",
            "next_probe": "If tag prerequisite is satisfied and LMDB still fails, inspect filesystem/envdir creation separately.",
            "priority": "MEDIUM",
        },
    ]
    wc(gen / "dd096zd2r_failure_hypothesis_register.csv", hypothesis_rows, ["hypothesis_id","hypothesis","evidence","next_probe","priority"])

    inventory_dts = make_inventory_dts(candidate_dbf, candidate_index, candidate_lmdb)
    probe_dts = make_tag_syntax_probe_dts(candidate_dbf, candidate_index, candidate_lmdb)
    retry_dts = make_lmdb_retry_after_tags_dts(candidate_dbf, candidate_index, candidate_lmdb)
    wt(gen / "DD096ZD2R_CANDIDATE_CDX_TAG_INVENTORY.dts", inventory_dts)
    wt(gen / "DD096ZD2R_CANDIDATE_TAG_SYNTAX_PROBE.dts", probe_dts)
    wt(gen / "DD096ZD2R_LMDB_RETRY_AFTER_TAGS_EXIST_REVIEW.dts", retry_dts)

    scripts_written = 0
    if args.write_runtime_scripts:
        wt(repo / "dottalkpp/data/scripts/DD096ZD2R_CANDIDATE_CDX_TAG_INVENTORY.dts", inventory_dts)
        wt(repo / "dottalkpp/data/scripts/DD096ZD2R_CANDIDATE_TAG_SYNTAX_PROBE.dts", probe_dts)
        wt(repo / "dottalkpp/data/scripts/DD096ZD2R_LMDB_RETRY_AFTER_TAGS_EXIST_REVIEW.dts", retry_dts)
        scripts_written = 1

    boundary = [
        ("candidate_cdx_tag_prereq_diagnostic_only", 1, 1, 1),
        ("runtime_scripts_written", scripts_written, int(args.write_runtime_scripts), int(scripts_written == int(args.write_runtime_scripts))),
        ("active_catalog_replacement", 0, 0, 1),
        ("active_catalog_dbf_copy_or_write", 0, 0, 1),
        ("active_cdx_lmdb_rebuild", 0, 0, 1),
        ("source_edits", 0, 0, 1),
        ("build_file_edits", 0, 0, 1),
        ("workspace_schema_mutation", 0, 0, 1),
        ("help_meta_cmdhelpchk_mutation", 0, 0, 1),
        ("manual_publication_mutation", 0, 0, 1),
    ]
    wc(out / "dd096zd2r_no_mutation_boundary_ledger.csv",
       [{"boundary": a, "observed": b, "required": c, "pass": d} for a,b,c,d in boundary],
       ["boundary","observed","required","pass"])

    lmdb_failures_seen = int(proof.get("buildlmdb_failed_count", 0))
    tags_none_seen = int(proof.get("tags_none_count", 0))
    gates = [
        {"gate": "preconditions_accepted", "expected": 0, "observed": blockers, "pass": int(blockers == 0)},
        {"gate": "runtime_failure_proof_supplied_or_not_required", "expected": "review", "observed": proof_supplied, "pass": 1},
        {"gate": "candidate_path_seen_if_proof_supplied", "expected": 1 if proof_supplied else 0, "observed": proof.get("candidate_path_seen", 0), "pass": int((not proof_supplied) or proof.get("candidate_path_seen", 0) == 1)},
        {"gate": "active_datadict_not_seen_if_proof_supplied", "expected": 0, "observed": proof.get("active_datadict_seen", 0), "pass": int((not proof_supplied) or proof.get("active_datadict_seen", 0) == 0)},
        {"gate": "lmdb_failures_identified_for_review", "expected": ">=0", "observed": lmdb_failures_seen, "pass": 1},
        {"gate": "tags_none_identified_for_review", "expected": ">=0", "observed": tags_none_seen, "pass": 1},
        {"gate": "active_rebuild_performed_by_generator", "expected": 0, "observed": 0, "pass": 1},
    ]
    failures = sum(1 for g in gates if int(g["pass"]) != 1)
    wc(out / "dd096zd2r_gate_ledger.csv", gates, ["gate","expected","observed","pass"])

    status = "DD096ZD2R_CANDIDATE_CDX_TAG_PREREQ_DIAGNOSTIC_READY" if failures == 0 else "DD096ZD2R_CANDIDATE_CDX_TAG_PREREQ_DIAGNOSTIC_REVIEW"

    report = f"""# DD096Z-D2R Candidate CDX/Tag Prerequisite Diagnostic

Run id: `{args.run_id}`
Status: **{status}**
Created UTC: `{now()}`

## Purpose

DD096Z-D2R diagnoses why candidate-only `BUILDLMDB CLEAN YES` failed after DD096Z-D2.

It does not retry LMDB blindly. It first proves whether candidate CDX containers/tags exist and which tag-creation command syntax is safe.

## Summary

- Precondition blockers: **{blockers}**
- Runtime proof supplied: **{proof_supplied}**
- BUILDLMDB failures observed: **{proof.get('buildlmdb_failed_count', 0)}**
- Index none count observed: **{proof.get('index_none_count', 0)}**
- Tags none count observed: **{proof.get('tags_none_count', 0)}**
- Candidate path seen: **{proof.get('candidate_path_seen', 0)}**
- Active datadict root seen: **{proof.get('active_datadict_seen', 0)}**
- Runtime scripts written: **{scripts_written}**
- Active catalog replacement: **0**
- Active CDX/LMDB rebuild: **0**

## Interpretation

The likely blocker is not candidate DBF readback. Candidate v64 readback is already green.

The likely blocker is the index prerequisite: `BUILDLMDB` was asked to mirror candidate CDX paths while `AREA` still reported `Index file: (none)` and `Tags: (none)`.

## Runtime scripts

- `DD096ZD2R_CANDIDATE_CDX_TAG_INVENTORY`
- `DD096ZD2R_CANDIDATE_TAG_SYNTAX_PROBE`
- `DD096ZD2R_LMDB_RETRY_AFTER_TAGS_EXIST_REVIEW`

Only the inventory script is safe to run immediately. The syntax probe should be edited/uncommented one form at a time. The LMDB retry script keeps `BUILDLMDB` commented until tags are proven.

## Next lane

Run inventory first. Then test one tag syntax on `DATA_DICTIONARY_RUNS`. Do not rerun full LMDB until a real candidate tag is visible.
"""
    wt(out / "DD096ZD2R_CANDIDATE_CDX_TAG_PREREQ_DIAGNOSTIC_REPORT.md", report)

    manifest = {
        "contract": "dd096zd2r_candidate_cdx_tag_prereq_diagnostic_v0",
        "run_id": args.run_id,
        "created_utc": now(),
        "status": status,
        "repo_root": str(repo),
        "profiles": args.profile,
        "candidate_root": str(candidate_root),
        "candidate_dbf_root": str(candidate_dbf),
        "candidate_index_root": str(candidate_index),
        "candidate_lmdb_root": str(candidate_lmdb),
        "precondition_blockers": blockers,
        "runtime_proof_supplied": proof_supplied,
        "buildlmdb_failures_observed": proof.get("buildlmdb_failed_count", 0),
        "tags_none_count": proof.get("tags_none_count", 0),
        "index_none_count": proof.get("index_none_count", 0),
        "runtime_scripts_written": scripts_written,
        "active_catalog_replacement": 0,
        "active_cdx_lmdb_rebuild": 0,
        "source_edits": 0,
        "failures": failures,
        "next_recommended_action": "Run candidate CDX/tag inventory; then prove one tag syntax on DATA_DICTIONARY_RUNS before retrying BUILDLMDB.",
    }
    wj(out / "dd096zd2r_candidate_cdx_tag_prereq_diagnostic_manifest.json", manifest)

    print(f"DD096Z-D2R candidate CDX/tag prerequisite diagnostic manifest: {out / 'dd096zd2r_candidate_cdx_tag_prereq_diagnostic_manifest.json'}")
    print(f"status: {status}; precondition_blockers: {blockers}; buildlmdb_failures_observed: {proof.get('buildlmdb_failed_count', 0)}; tags_none_count: {proof.get('tags_none_count', 0)}; runtime_scripts_written: {scripts_written}; active_catalog_replacement: 0; failures: {failures}")
    return 2 if (args.fail_on_review and failures) else 0

if __name__ == "__main__":
    raise SystemExit(main())
