#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import datetime as _dt
import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List


EXPECTED_CHAIN = [
    ("DD-034", "Daily/current baseline status", "DD034-check-DDBASE-stable-v2-current", ""),
    ("DD-036", "Acceptance artifact closure", "DD036-stable-v2-acceptance-artifact-accepted-v0", "BASELINE_ACCEPTANCE_ARTIFACT_CLOSURE_ACCEPTED"),
    ("DD-037", "Status closure integration", "DD037-status-closure-v2-v0", "PASS_WITH_ACCEPTED_BASELINE_ARTIFACTS"),
    ("DD-038", "Current baseline pointer", "DD038-current-baseline-pointer-v0", "CURRENT_BASELINE_POINTER_READY"),
    ("DD-039", "Catalog DBF/DDL definition plan", "DD039-catalog-dbfdll-definition-v0", "CATALOG_DBF_DDL_DEFINITION_PLAN_READY"),
    ("DD-040", "Catalog row projection dry-run", "DD040-catalog-row-projection-v0", "CATALOG_ROW_PROJECTION_READY"),
    ("DD-041", "Sandbox catalog DBF creation/population", "DD041-sandbox-catalog-population-v0", ""),
    ("DD-042", "Sandbox catalog inspection", "DD042-sandbox-catalog-inspection-v0", "SANDBOX_CATALOG_INSPECTION_READY"),
    ("DD-043", "pydottalk/runtime sandbox readback", "DD043-pydottalk-runtime-readback-v1_1", "PYDOTTALK_RUNTIME_READBACK_GREEN"),
    ("DD-044", "Active catalog promotion plan gate", "DD044-active-catalog-promotion-plan-gate-v0", ""),
    ("DD-046", "CREATE X64 / IMPORT / memo / index probe", "DD046-v1_1-create-import-probe-pydottalk-after-dd048-v0", "DOTTALK_X64_CREATE_IMPORT_MEMO_INDEX_PROBE_GREEN"),
    ("DD-047", "IMPORT memo repair plan", "DD047-import-memo-repair-plan-v0", "IMPORT_MEMO_FIELD_REPAIR_REQUIRED"),
    ("DD-048", "IMPORT memo patch apply/proof", "DD048-import-memo-patch-apply-v0", "IMPORT_MEMO_FIELD_PATCH_APPLIED"),
    ("DD-049", "x64 header inspection/evidence closure", "DD049-x64-header-inspection-closure-v0", "X64_HEADER_INSPECTION_EVIDENCE_CLOSURE_GREEN"),
    ("DD-051", "Canonical catalog rebuild plan", "DD051-canonical-catalog-rebuild-plan-v0", "CANONICAL_CATALOG_REBUILD_PLAN_READY"),
    ("DD-052", "Canonical catalog CREATE X64 / IMPORT staging", "DD052-canonical-catalog-staging-verify-v0", "CANONICAL_CATALOG_STAGING_RUNTIME_VERIFY_GREEN"),
    ("DD-053", "Canonical catalog runtime/pydottalk readback", "DD053-canonical-catalog-runtime-readback-v0", "CANONICAL_CATALOG_RUNTIME_READBACK_GREEN"),
    ("DD-054", "Catalog CDX/tag plan", "DD054-catalog-cdx-tag-plan-v0", "CATALOG_CDX_TAG_PLAN_READY"),
    ("DD-055", "Superseded artifact-only index execution", "DD055-guarded-cdx-tag-execution-verify-v0", "CATALOG_CDX_TAG_EXECUTION_VERIFY_GREEN"),
    ("DD-055R", "Corrected CDX/TAG/INFO/BUILDLMDB plan", "DD055R-canonical-cdx-workflow-plan-v0", "CANONICAL_CDX_WORKFLOW_PLAN_READY_WITH_SYNTAX_REVIEW"),
    ("DD-056R", "Canonical CDX/ADDTAG/INFO/BUILDLMDB staging verify", "DD056R-canonical-cdx-buildlmdb-verify-v0", "CANONICAL_CDX_BUILDLMDB_STAGING_VERIFY_GREEN"),
    ("DD-057", "Active catalog promotion readiness", "DD057-active-catalog-promotion-readiness-v0", "ACTIVE_CATALOG_PROMOTION_READINESS_PLAN_READY"),
    ("DD-058", "Controlled active catalog promotion execution", "DD058-controlled-active-catalog-promotion-execute-v0", "ACTIVE_CATALOG_PROMOTION_EXECUTED_AND_VERIFIED"),
    ("DD-059", "Active catalog promotion closure", "DD059-active-catalog-promotion-closure-v0", "ACTIVE_CATALOG_PROMOTION_CLOSURE_GREEN"),
]


MANIFEST_NAMES = [
    "manifest.json",
    "dd034_manifest.json",
    "dd036_baseline_acceptance_artifact_closure_manifest.json",
    "dd037_status_closure_manifest.json",
    "dd038_current_baseline_pointer_manifest.json",
    "dd039_catalog_dbf_ddl_definition_manifest.json",
    "dd040_projection_manifest.json",
    "dd041_sandbox_catalog_population_manifest.json",
    "dd042_sandbox_catalog_inspection_manifest.json",
    "dd043_pydottalk_runtime_readback_manifest.json",
    "dd044_active_catalog_promotion_plan_manifest.json",
    "dd046_dottalk_x64_create_import_probe_manifest.json",
    "dd047_import_memo_repair_plan_manifest.json",
    "dd048_import_memo_patch_manifest.json",
    "dd049_x64_header_inspection_evidence_closure_manifest.json",
    "dd051_canonical_catalog_rebuild_plan_manifest.json",
    "dd052_canonical_catalog_staging_manifest.json",
    "dd053_canonical_catalog_runtime_readback_manifest.json",
    "dd054_catalog_cdx_tag_plan_manifest.json",
    "dd055_guarded_cdx_tag_execution_manifest.json",
    "dd055r_canonical_cdx_layout_tag_info_buildlmdb_plan_manifest.json",
    "dd056r_canonical_cdx_buildlmdb_execution_manifest.json",
    "dd057_active_catalog_promotion_readiness_manifest.json",
    "dd058_controlled_active_catalog_promotion_manifest.json",
    "dd059_active_catalog_promotion_closure_manifest.json",
]


def utc_now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds")


def read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return {}


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


def safe_rel(repo: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(repo.resolve()).as_posix()
    except Exception:
        return path.as_posix()


def find_report_dir(repo: Path, name: str) -> Path:
    direct = repo / "docs" / "datadict" / "reports" / name
    if direct.exists():
        return direct
    alt = repo / "docs" / "datadict" / "review_queue" / name
    if alt.exists():
        return alt
    matches = []
    for root in [repo / "docs" / "datadict" / "reports", repo / "docs" / "datadict" / "review_queue"]:
        if root.exists():
            matches.extend([p for p in root.rglob(name) if p.is_dir()])
    matches.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return matches[0] if matches else direct


def find_manifest_in_dir(path: Path) -> Path:
    if not path.exists():
        return path / "MISSING_MANIFEST.json"
    exacts = [path / name for name in MANIFEST_NAMES if (path / name).exists()]
    if exacts:
        exacts.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        return exacts[0]
    manifests = list(path.glob("*manifest*.json"))
    manifests.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return manifests[0] if manifests else path / "MISSING_MANIFEST.json"


def collect_chain(repo: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for dd_id, description, report_dir_name, expected_status in EXPECTED_CHAIN:
        report_dir = find_report_dir(repo, report_dir_name)
        manifest_path = find_manifest_in_dir(report_dir)
        manifest = read_json(manifest_path)
        observed_status = manifest.get("status", "")
        exists = int(report_dir.exists())
        manifest_exists = int(manifest_path.exists())
        if expected_status:
            status_ok = int(observed_status == expected_status)
        else:
            # Historical/probe entries may be informational but should be present if used.
            status_ok = int(bool(observed_status) or exists)
        rows.append({
            "dd_id": dd_id,
            "description": description,
            "report_dir": safe_rel(repo, report_dir),
            "report_dir_exists": exists,
            "manifest": safe_rel(repo, manifest_path),
            "manifest_exists": manifest_exists,
            "expected_status": expected_status,
            "observed_status": observed_status,
            "status_ok": status_ok,
            "sha256": sha256_file(manifest_path) if manifest_path.exists() else "",
            "classification": "CANONICAL" if not dd_id.endswith("55") else "SUPERSEDED_PARTIAL_EVIDENCE",
        })
    return rows


def read_dd059_summary(repo: Path, dd059_dir: Path) -> Dict[str, Any]:
    return read_json(dd059_dir / "dd059_active_catalog_closure_summary.json")


def write_savepoint(repo: Path, out: Path, run_id: str, summary: Dict[str, Any], chain_rows: List[Dict[str, Any]]) -> Path:
    savepoint = repo / "docs" / "datadict" / "runlog" / "DD-060_DATADICT_PROMOTION_CYCLE_SAVEPOINT.md"
    savepoint.parent.mkdir(parents=True, exist_ok=True)
    text = f"""# DD-060 Data Dictionary Promotion Cycle Savepoint

Run id: `{run_id}`
Created UTC: `{utc_now()}`

## Active state

```text
{summary.get('active_catalog_state', 'UNKNOWN')}
```

## Closure evidence

- DD-058 status: `{summary.get('dd058_status', '')}`
- Runtime proof status: `{summary.get('runtime_proof_status', '')}`
- Active DBFs: `{summary.get('active_dbf_count', '')}`
- Active CDX containers: `{summary.get('active_cdx_count', '')}`
- Active LMDB environments: `{summary.get('active_lmdb_count', '')}`
- MODE LMDB hits: `{summary.get('mode_lmdb_hits', '')}`

## Backup / rollback

```text
Backup directory:
{summary.get('backup_dir', '')}

Restore script:
{summary.get('restore_script', '')}
```

## Chain status

```text
Canonical/reviewed chain rows: {len(chain_rows)}
Rows not status-ok: {sum(1 for r in chain_rows if int(r.get('status_ok', 0)) != 1)}
```

## Boundary

DD-060 savepoint closure is report/documentation only. It does not mutate the active
catalog, source, HELP/META/CMDHELPCHK, catalog content, or rows.

## Next

DD-061 may plan the active Data Dictionary consumer/read API.
"""
    savepoint.write_text(text, encoding="utf-8")
    return savepoint


def main() -> int:
    ap = argparse.ArgumentParser(description="DD-060 report-only Data Dictionary promotion cycle savepoint closure")
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--run-id", default="DD060-datadict-promotion-cycle-savepoint-v0")
    ap.add_argument("--dd059-dir", default="docs/datadict/reports/DD059-active-catalog-promotion-closure-v0")
    ap.add_argument("--write-savepoint", action="store_true", help="Write docs/datadict/runlog/DD-060_DATADICT_PROMOTION_CYCLE_SAVEPOINT.md")
    ap.add_argument("--profile", action="append", default=[])
    ap.add_argument("--fail-on-review", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    out = Path(args.out_dir).resolve()
    dd059_dir = (repo / args.dd059_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)

    chain_rows = collect_chain(repo)
    dd059_manifest = read_json(dd059_dir / "dd059_active_catalog_promotion_closure_manifest.json")
    dd059_summary = read_dd059_summary(repo, dd059_dir)

    dd059_green = dd059_manifest.get("status") == "ACTIVE_CATALOG_PROMOTION_CLOSURE_GREEN"
    active_state_ok = dd059_summary.get("active_catalog_state") == "ACTIVE_DATA_DICTIONARY_CATALOG_PROMOTED_AND_RUNTIME_VERIFIED"
    runtime_ok = dd059_summary.get("runtime_proof_status") == "ACTIVE_RUNTIME_INDEXED_LMDB_PROOF_ACCEPTED"

    chain_blockers = [
        r for r in chain_rows
        if r["dd_id"] in {"DD-052", "DD-053", "DD-056R", "DD-057", "DD-058", "DD-059"} and int(r.get("status_ok", 0)) != 1
    ]

    savepoint_path = ""
    savepoint_written = 0
    if args.write_savepoint:
        sp = write_savepoint(repo, out, args.run_id, dd059_summary, chain_rows)
        savepoint_path = str(sp)
        savepoint_written = 1

    gate_rows = [
        {
            "gate": "dd059_closure_green",
            "expected": "ACTIVE_CATALOG_PROMOTION_CLOSURE_GREEN",
            "observed": dd059_manifest.get("status", ""),
            "pass": int(dd059_green),
        },
        {
            "gate": "active_catalog_state_promoted_runtime_verified",
            "expected": "ACTIVE_DATA_DICTIONARY_CATALOG_PROMOTED_AND_RUNTIME_VERIFIED",
            "observed": dd059_summary.get("active_catalog_state", ""),
            "pass": int(active_state_ok),
        },
        {
            "gate": "runtime_lmdb_proof_accepted",
            "expected": "ACTIVE_RUNTIME_INDEXED_LMDB_PROOF_ACCEPTED",
            "observed": dd059_summary.get("runtime_proof_status", ""),
            "pass": int(runtime_ok),
        },
        {
            "gate": "active_dbf_count",
            "expected": 11,
            "observed": dd059_summary.get("active_dbf_count", ""),
            "pass": int(str(dd059_summary.get("active_dbf_count", "")) == "11"),
        },
        {
            "gate": "active_cdx_count",
            "expected": 11,
            "observed": dd059_summary.get("active_cdx_count", ""),
            "pass": int(str(dd059_summary.get("active_cdx_count", "")) == "11"),
        },
        {
            "gate": "active_lmdb_count",
            "expected": 11,
            "observed": dd059_summary.get("active_lmdb_count", ""),
            "pass": int(str(dd059_summary.get("active_lmdb_count", "")) == "11"),
        },
        {
            "gate": "critical_chain_blockers",
            "expected": 0,
            "observed": len(chain_blockers),
            "pass": int(len(chain_blockers) == 0),
        },
        {
            "gate": "savepoint_written_when_requested",
            "expected": int(args.write_savepoint),
            "observed": savepoint_written,
            "pass": int((not args.write_savepoint) or savepoint_written == 1),
        },
    ]

    boundary_rows = [
        {"boundary": "savepoint_closure_report_only", "observed": 1, "required": 1, "pass": 1},
        {"boundary": "active_catalog_mutation", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "source_edits", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "help_meta_cmdhelpchk_mutation", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "catalog_regeneration", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "manual_row_repair", "observed": 0, "required": 0, "pass": 1},
    ]

    failures = sum(1 for r in gate_rows if int(r["pass"]) != 1)
    status = "DATADICT_PROMOTION_CYCLE_SAVEPOINT_GREEN" if failures == 0 else "DATADICT_PROMOTION_CYCLE_SAVEPOINT_REVIEW"

    write_csv(out / "dd060_datadict_chain_ledger.csv", chain_rows, [
        "dd_id", "description", "report_dir", "report_dir_exists", "manifest", "manifest_exists",
        "expected_status", "observed_status", "status_ok", "sha256", "classification",
    ])
    write_csv(out / "dd060_gate_ledger.csv", gate_rows, ["gate", "expected", "observed", "pass"])
    write_csv(out / "dd060_no_mutation_boundary_ledger.csv", boundary_rows, ["boundary", "observed", "required", "pass"])

    summary = {
        "savepoint_state": "DATADICT_ACTIVE_CATALOG_PROMOTION_CYCLE_CLOSED" if failures == 0 else "DATADICT_ACTIVE_CATALOG_PROMOTION_CYCLE_REVIEW",
        "dd059_status": dd059_manifest.get("status", ""),
        "active_catalog_state": dd059_summary.get("active_catalog_state", ""),
        "runtime_proof_status": dd059_summary.get("runtime_proof_status", ""),
        "active_dbf_count": dd059_summary.get("active_dbf_count", ""),
        "active_cdx_count": dd059_summary.get("active_cdx_count", ""),
        "active_lmdb_count": dd059_summary.get("active_lmdb_count", ""),
        "backup_dir": dd059_summary.get("backup_dir", ""),
        "restore_script": dd059_summary.get("restore_script", ""),
        "chain_rows": len(chain_rows),
        "critical_chain_blockers": len(chain_blockers),
        "savepoint_written": savepoint_written,
        "savepoint_path": savepoint_path,
    }
    write_json(out / "dd060_promotion_cycle_savepoint_summary.json", summary)

    manifest = {
        "contract": "dd060_datadict_promotion_cycle_savepoint_closure_v0",
        "run_id": args.run_id,
        "created_utc": utc_now(),
        "status": status,
        "repo_root": str(repo),
        "profiles": args.profile,
        "dd059_status": dd059_manifest.get("status", ""),
        "active_catalog_state": dd059_summary.get("active_catalog_state", ""),
        "runtime_proof_status": dd059_summary.get("runtime_proof_status", ""),
        "backup_dir": dd059_summary.get("backup_dir", ""),
        "restore_script": dd059_summary.get("restore_script", ""),
        "chain_rows": len(chain_rows),
        "critical_chain_blockers": len(chain_blockers),
        "write_savepoint": int(args.write_savepoint),
        "savepoint_written": savepoint_written,
        "savepoint_path": savepoint_path,
        "failures": failures,
        "active_catalog_mutation": 0,
        "source_edits": 0,
        "help_meta_cmdhelpchk_mutation": 0,
        "catalog_regeneration": 0,
        "manual_row_repair": 0,
        "next_recommended_action": "DD-061 active Data Dictionary consumer/read API plan.",
    }
    write_json(out / "dd060_datadict_promotion_cycle_savepoint_manifest.json", manifest)

    report = f"""# DD-060 Data Dictionary Promotion Cycle Savepoint Closure

Run id: `{args.run_id}`
Status: **{status}**
Created UTC: `{manifest['created_utc']}`

## Purpose

DD-060 closes the DD-034 through DD-059 Data Dictionary promotion cycle as a
project savepoint.

## Active catalog state

```text
{dd059_summary.get('active_catalog_state', '')}
```

## Closure evidence

- DD-059 status: `{dd059_manifest.get('status', '')}`
- Runtime proof status: `{dd059_summary.get('runtime_proof_status', '')}`
- Active DBFs: **{dd059_summary.get('active_dbf_count', '')}**
- Active CDX containers: **{dd059_summary.get('active_cdx_count', '')}**
- Active LMDB environments: **{dd059_summary.get('active_lmdb_count', '')}**
- Backup directory: `{dd059_summary.get('backup_dir', '')}`
- Restore script: `{dd059_summary.get('restore_script', '')}`

## Chain

- Chain rows captured: **{len(chain_rows)}**
- Critical chain blockers: **{len(chain_blockers)}**

## Boundary

DD-060 is savepoint/report closure only. It does not mutate the active catalog,
source, HELP/META/CMDHELPCHK, catalog content, or rows.

## Next

DD-061 may begin the active Data Dictionary consumer/read API plan.
"""
    (out / "DD060_DATADICT_PROMOTION_CYCLE_SAVEPOINT_CLOSURE_REPORT.md").write_text(report, encoding="utf-8")

    print(f"DD-060 Data Dictionary promotion cycle savepoint manifest: {out / 'dd060_datadict_promotion_cycle_savepoint_manifest.json'}")
    print(f"status: {status}; failures: {failures}; chain_rows: {len(chain_rows)}; savepoint_written: {savepoint_written}")
    return 2 if (args.fail_on_review and failures) else 0


if __name__ == "__main__":
    raise SystemExit(main())
