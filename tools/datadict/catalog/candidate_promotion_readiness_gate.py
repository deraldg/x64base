#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, datetime as dt, json, os
from pathlib import Path

CANDIDATE_TABLES = [
    ("DATA_DICTIONARY_OBJECTS", "DDOBJECT", 10, ["CATALOG_OBJECT_ID", "CATALOG_OBJECT_NAME"]),
    ("DATA_DICTIONARY_OBJECT_ATTRIBUTES", "DDATTR", 127, ["CATALOG_OBJECT_ID", "CATALOG_ATTRIBUTE_NAME"]),
    ("DATA_DICTIONARY_RELATION_EDGES", "DDEDGE", 16, ["RELATION_FROM_OBJECT_ID", "RELATION_TO_OBJECT_ID"]),
    ("DATA_DICTIONARY_EVIDENCE_RECORDS", "DDEVID", 7, ["CATALOG_OBJECT_ID"]),
    ("DATA_DICTIONARY_GATE_RECORDS", "DDGATE", 3, ["GATE_RECORD_ID"]),
    ("DATA_DICTIONARY_RUNS", "DDRUN", 2, ["RUN_RECORD_ID"]),
]

REQUIRED = [
    ("DD096YQ", "docs/datadict/reports/DD096YQ-post-import-validation-readback-v0/dd096yq_post_import_validation_readback_manifest.json", ["DD096YQ_POST_IMPORT_VALIDATION_GREEN"]),
    ("DD096ZGQ", "docs/datadict/reports/DD096ZGQ-candidate-raw-smoke-closure-v0/dd096zgq_candidate_raw_smoke_closure_manifest.json", ["DD096ZGQ_CANDIDATE_RAW_SMOKE_CLOSURE_GREEN"]),
    ("DD096ZD2S", "docs/datadict/reports/DD096ZD2S-single-table-cdx-lmdb-proof-closure-v0/dd096zd2s_single_table_cdx_lmdb_proof_closure_manifest.json", ["DD096ZD2S_SINGLE_TABLE_CDX_LMDB_PROOF_GREEN"]),
    ("DD096ZD2ZC", "docs/datadict/reports/DD096ZD2ZC-current-session-select-clean-tiny-rebuild-v0/dd096zd2zc_current_session_select_clean_tiny_rebuild_manifest.json", ["DD096ZD2ZC_CURRENT_SESSION_SELECT_CLEAN_TINY_REBUILD_GREEN"]),
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

def wt(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")

def wj(path: Path, obj):
    wt(path, json.dumps(obj, indent=2, sort_keys=True) + "\n")

def wc(path: Path, rows, fields):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        w.writeheader()
        for row in rows:
            w.writerow({k: row.get(k, "") for k in fields})

def size_bytes(path: Path) -> int:
    if not path.exists():
        return 0
    if path.is_file():
        try:
            return path.stat().st_size
        except OSError:
            return 0
    total = 0
    for root, _dirs, files in os.walk(path):
        for name in files:
            try:
                total += (Path(root) / name).stat().st_size
            except OSError:
                pass
    return total

def main():
    ap = argparse.ArgumentParser(description="DD096Z-D2ZD candidate promotion readiness gate")
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--run-id", default="DD096ZD2ZD-candidate-promotion-readiness-gate-v0")
    ap.add_argument("--profile", action="append", default=[])
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    out = Path(args.out_dir).resolve()
    gen = out / "generated_candidate_promotion_readiness_gate"
    gen.mkdir(parents=True, exist_ok=True)

    pre_rows = []
    blockers = 0
    for lane, rel, expected in REQUIRED:
        p = repo / rel
        data = read_json(p)
        observed = data.get("status", "MISSING")
        passed = int(observed in expected)
        blockers += 0 if passed else 1
        pre_rows.append({"lane": lane, "manifest_path": str(p), "observed_status": observed, "expected_status": "|".join(expected), "pass": passed})
    wc(gen / "dd096zd2zd_precondition_ledger.csv", pre_rows, ["lane","manifest_path","observed_status","expected_status","pass"])

    zb = read_json(repo / "docs/datadict/reports/DD096ZB-backup-and-inactive-candidate-staging-v0/dd096zb_backup_and_inactive_candidate_staging_manifest.json")
    candidate_root = Path(zb.get("candidate_root", repo / "docs/datadict/candidates/DD096ZB-backup-and-inactive-candidate-staging-v0"))
    candidate_dbf = Path(zb.get("candidate_dbf_root", candidate_root / "dbf"))
    candidate_indexes = candidate_root / "indexes"
    candidate_lmdb = candidate_root / "lmdb"

    active_dbf = repo / "dottalkpp/data/datadict"
    active_indexes = repo / "dottalkpp/data/indexes/datadict"
    active_lmdb = repo / "dottalkpp/data/lmdb/datadict"
    active_workspace = repo / "dottalkpp/data/workspaces/ddbase.dtschema"

    root_rows = []
    for family, p, policy in [
        ("candidate_root", candidate_root, "source_for_future_apply"),
        ("candidate_dbf", candidate_dbf, "source_for_future_apply"),
        ("candidate_indexes", candidate_indexes, "source_for_future_apply"),
        ("candidate_lmdb", candidate_lmdb, "source_for_future_apply"),
        ("active_dbf", active_dbf, "protected_target"),
        ("active_indexes", active_indexes, "protected_target"),
        ("active_lmdb", active_lmdb, "protected_target"),
        ("active_workspace_schema", active_workspace, "protected_target"),
    ]:
        root_rows.append({"root_family": family, "path": str(p), "exists": int(p.exists()), "bytes": size_bytes(p), "policy": policy})
    wc(gen / "dd096zd2zd_root_inventory.csv", root_rows, ["root_family","path","exists","bytes","policy"])

    table_rows = []
    missing_artifacts = 0
    for new_table, legacy, expected, tags in CANDIDATE_TABLES:
        dbf = candidate_dbf / f"{new_table}.dbf"
        cdx = candidate_indexes / f"{new_table}.cdx"
        lmdb = candidate_lmdb / f"{new_table}.cdx.d"
        for p in [dbf, cdx, lmdb]:
            if not p.exists():
                missing_artifacts += 1
        table_rows.append({
            "new_x64_table": new_table,
            "legacy_bridge_name": legacy,
            "expected_records": expected,
            "candidate_dbf_exists": int(dbf.exists()),
            "candidate_cdx_exists": int(cdx.exists()),
            "candidate_lmdb_exists": int(lmdb.exists()),
            "required_tags": ";".join(tags),
            "promotion_policy": "candidate_only_ready_for_apply_planning",
        })
    wc(gen / "dd096zd2zd_candidate_artifact_matrix.csv", table_rows, ["new_x64_table","legacy_bridge_name","expected_records","candidate_dbf_exists","candidate_cdx_exists","candidate_lmdb_exists","required_tags","promotion_policy"])

    bridge_rows = [{"legacy_surface": legacy, "new_x64_table": new_table, "readiness": "bridge_required_before_or_during_apply", "notes": "DDICT resolver/alias compatibility must handle legacy and x64 names."} for new_table, legacy, expected, tags in CANDIDATE_TABLES]
    wc(gen / "dd096zd2zd_resolver_bridge_requirements.csv", bridge_rows, ["legacy_surface","new_x64_table","readiness","notes"])

    gate_rows = [
        {"gate": "required_preconditions_green", "observed": blockers, "required": 0, "pass": int(blockers == 0)},
        {"gate": "candidate_artifacts_present", "observed": missing_artifacts, "required": 0, "pass": int(missing_artifacts == 0)},
        {"gate": "active_replacement_authorized", "observed": 0, "required": 0, "pass": 1},
        {"gate": "active_catalog_replacement_executed", "observed": 0, "required": 0, "pass": 1},
        {"gate": "active_cdx_lmdb_rebuild_executed", "observed": 0, "required": 0, "pass": 1},
        {"gate": "source_edits_executed", "observed": 0, "required": 0, "pass": 1},
        {"gate": "help_cmdhelpchk_mutation_executed", "observed": 0, "required": 0, "pass": 1},
    ]
    failures = sum(1 for r in gate_rows if int(r["pass"]) != 1)
    wc(out / "dd096zd2zd_gate_ledger.csv", gate_rows, ["gate","observed","required","pass"])

    boundary_rows = [
        {"boundary": "candidate_promotion_readiness_gate_only", "observed": 1, "required": 1, "pass": 1},
        {"boundary": "active_catalog_replacement", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "active_catalog_dbf_copy_or_write", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "active_cdx_lmdb_rebuild", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "workspace_schema_mutation", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "source_edits", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "help_meta_cmdhelpchk_mutation", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "manual_publication_mutation", "observed": 0, "required": 0, "pass": 1},
    ]
    wc(out / "dd096zd2zd_no_mutation_boundary_ledger.csv", boundary_rows, ["boundary","observed","required","pass"])

    checklist = """# DD096Z-D2ZD Manual Promotion Readiness Checklist

This checklist is intentionally report-only.

## Before any active replacement

- Confirm DD096Z-D2ZC is green.
- Confirm candidate DBF/CDX/LMDB roots are under docs/datadict/candidates.
- Confirm active roots are under dottalkpp/data/datadict, dottalkpp/data/indexes/datadict, and dottalkpp/data/lmdb/datadict.
- Confirm old compact DD* table names and new DATA_DICTIONARY_* table names have a resolver/alias plan.
- Confirm DDICT can be moved through a compatibility bridge or feature flag before active replacement.
- Confirm workspace schema impact is planned.
- Confirm HELP/CMDHELPCHK are not mutated by this promotion lane.
- Confirm active backup target exists or will be created.
- Confirm rollback policy is explicit.
- Confirm no active replacement occurs without a separate explicit apply authorization.
"""
    wt(gen / "DD096ZD2ZD_MANUAL_PROMOTION_READINESS_CHECKLIST.md", checklist)

    status = "DD096ZD2ZD_CANDIDATE_PROMOTION_READINESS_READY" if failures == 0 else "DD096ZD2ZD_CANDIDATE_PROMOTION_READINESS_REVIEW"

    report = f"""# DD096Z-D2ZD Candidate Promotion Readiness Gate

Run id: `{args.run_id}`
Status: **{status}**
Created UTC: `{now()}`

## Purpose

DD096Z-D2ZD begins the post-D2ZC lane.

D2ZC is green, so the candidate DATA_DICTIONARY_* DBF/CDX/LMDB set is ready for promotion planning. This package is a readiness gate only. It does not replace active catalogs.

## Summary

- Precondition blockers: **{blockers}**
- Missing candidate artifacts: **{missing_artifacts}**
- Readiness failures: **{failures}**
- Active catalog replacement: **0**
- Active DBF copy/write: **0**
- Active CDX/LMDB rebuild: **0**
- Source edits: **0**
- HELP/CMDHELPCHK mutation: **0**

## Candidate source roots

- `{candidate_dbf}`
- `{candidate_indexes}`
- `{candidate_lmdb}`

## Protected active roots

- `{active_dbf}`
- `{active_indexes}`
- `{active_lmdb}`

## Next safe lane

If this readiness gate is accepted, the next package should be a guarded active-replacement apply plan, still not execution unless explicitly authorized.
"""
    wt(out / "DD096ZD2ZD_CANDIDATE_PROMOTION_READINESS_GATE_REPORT.md", report)

    manifest = {
        "contract": "dd096zd2zd_candidate_promotion_readiness_gate_v0",
        "run_id": args.run_id,
        "created_utc": now(),
        "status": status,
        "repo_root": str(repo),
        "profiles": args.profile,
        "candidate_dbf_root": str(candidate_dbf),
        "candidate_indexes_root": str(candidate_indexes),
        "candidate_lmdb_root": str(candidate_lmdb),
        "active_dbf_root": str(active_dbf),
        "active_indexes_root": str(active_indexes),
        "active_lmdb_root": str(active_lmdb),
        "precondition_blockers": blockers,
        "missing_candidate_artifacts": missing_artifacts,
        "active_catalog_replacement": 0,
        "active_cdx_lmdb_rebuild": 0,
        "source_edits": 0,
        "failures": failures,
        "next_recommended_action": "Review readiness outputs, then authorize guarded active replacement plan package if desired.",
    }
    wj(out / "dd096zd2zd_candidate_promotion_readiness_gate_manifest.json", manifest)

    print(f"DD096Z-D2ZD candidate promotion readiness manifest: {out / 'dd096zd2zd_candidate_promotion_readiness_gate_manifest.json'}")
    print(f"status: {status}; precondition_blockers: {blockers}; missing_candidate_artifacts: {missing_artifacts}; active_catalog_replacement: 0; failures: {failures}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
