#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
import shutil
from pathlib import Path
from typing import Any, Dict, List


EXPECTED_REVIEW_STATUS = "DATADICT_CANDIDATE_ROW_ACCEPTANCE_PLAN_REVIEW"
EXPECTED_READY_STATUS = "DATADICT_DDICT_ROOT_COMMAND_CANDIDATE_REPAIR_READY"
READY_STATUS = "DATADICT_CANDIDATE_ROW_ACCEPTANCE_PLAN_READY"


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def read_text(path: Path) -> str:
    if not path.exists() or path.is_dir():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(read_text(path))
    except Exception as exc:
        return {"_read_error": str(exc)}


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


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


def artifact_row(path: Path, role: str) -> Dict[str, Any]:
    return {
        "role": role,
        "path": str(path),
        "exists": int(path.exists()),
        "kind": "dir" if path.exists() and path.is_dir() else "file" if path.exists() and path.is_file() else "",
        "bytes_or_children": path.stat().st_size if path.exists() and path.is_file() else sum(1 for _ in path.iterdir()) if path.exists() and path.is_dir() else 0,
        "sha256": sha256(path),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="DD096C-R root-aware acceptance gate repair/closure")
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--run-id", default="DD096CR-acceptance-gate-repair-v0")
    ap.add_argument("--dd096cr-dir", default="docs/datadict/reports/DD096C-R-candidate-row-acceptance-plan-v0")
    ap.add_argument("--dd096ar-dir", default="docs/datadict/reports/DD096AR-ddict-root-command-candidate-repair-v0")
    ap.add_argument("--profile", action="append", default=[])
    ap.add_argument("--fail-on-review", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    out = Path(args.out_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)

    src_dir = repo / args.dd096cr_dir
    src_manifest_path = src_dir / "dd096c_candidate_row_acceptance_plan_manifest.json"
    src_gate_path = src_dir / "dd096c_gate_ledger.csv"
    src_acceptance_dir = src_dir / "generated_acceptance_plan"

    ar_manifest_path = repo / args.dd096ar_dir / "dd096ar_ddict_root_command_candidate_repair_manifest.json"

    src_manifest = read_json(src_manifest_path)
    ar_manifest = read_json(ar_manifest_path)
    src_gates = read_csv(src_gate_path)

    generated = out / "generated_acceptance_plan"
    if generated.exists():
        shutil.rmtree(generated)
    if src_acceptance_dir.exists():
        shutil.copytree(src_acceptance_dir, generated)
    else:
        generated.mkdir(parents=True, exist_ok=True)

    counts = src_manifest.get("counts", {})
    if not isinstance(counts, dict):
        counts = {}

    gate_rows = [
        {
            "gate": "dd096cr_source_status_is_review_due_to_legacy_gate",
            "expected": EXPECTED_REVIEW_STATUS,
            "observed": src_manifest.get("status", ""),
            "pass": int(src_manifest.get("status", "") == EXPECTED_REVIEW_STATUS),
        },
        {
            "gate": "dd096ar_root_repair_ready",
            "expected": EXPECTED_READY_STATUS,
            "observed": ar_manifest.get("status", ""),
            "pass": int(ar_manifest.get("status", "") == EXPECTED_READY_STATUS),
        },
        {
            "gate": "acceptance_rows_169",
            "expected": 169,
            "observed": counts.get("total_acceptance_rows", ""),
            "pass": int(str(counts.get("total_acceptance_rows", "")) == "169"),
        },
        {
            "gate": "reuse_existing_objects_11",
            "expected": 11,
            "observed": counts.get("duplicate_objects_reuse_active", ""),
            "pass": int(str(counts.get("duplicate_objects_reuse_active", "")) == "11"),
        },
        {
            "gate": "new_objects_root_aware_9",
            "expected": 9,
            "observed": counts.get("new_objects", ""),
            "pass": int(str(counts.get("new_objects", "")) == "9"),
        },
        {
            "gate": "objid_remaps_11",
            "expected": 11,
            "observed": counts.get("objid_remaps", ""),
            "pass": int(str(counts.get("objid_remaps", "")) == "11"),
        },
        {
            "gate": "attr_rebase_88",
            "expected": 88,
            "observed": counts.get("attrs_requiring_rebase", ""),
            "pass": int(str(counts.get("attrs_requiring_rebase", "")) == "88"),
        },
        {
            "gate": "edge_rebase_7",
            "expected": 7,
            "observed": counts.get("edges_requiring_rebase", ""),
            "pass": int(str(counts.get("edges_requiring_rebase", "")) == "7"),
        },
        {
            "gate": "apply_now_zero",
            "expected": 0,
            "observed": counts.get("apply_now_total", ""),
            "pass": int(str(counts.get("apply_now_total", "")) == "0"),
        },
        {
            "gate": "acceptance_dir_copied",
            "expected": 1,
            "observed": int(generated.exists()),
            "pass": int(generated.exists()),
        },
    ]

    failures = sum(1 for r in gate_rows if int(r["pass"]) != 1)
    status = READY_STATUS if failures == 0 else "DATADICT_CANDIDATE_ROW_ACCEPTANCE_GATE_REPAIR_REVIEW"

    boundary_rows = [
        {"boundary": "acceptance_gate_repair_report_only", "observed": 1, "required": 1, "pass": 1},
        {"boundary": "active_catalog_mutation", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "dbf_append_replace_delete_pack_zap", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "cdx_lmdb_create_rebuild", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "cxx_source_edits", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "build_file_edits", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "registry_edits", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "help_meta_cmdhelpchk_mutation", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "catalog_regeneration", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "manual_row_repair", "observed": 0, "required": 0, "pass": 1},
    ]

    write_csv(out / "dd096cr_gate_ledger.csv", gate_rows, ["gate", "expected", "observed", "pass"])
    write_csv(out / "dd096cr_no_mutation_boundary_ledger.csv", boundary_rows, ["boundary", "observed", "required", "pass"])

    artifact_rows = [
        artifact_row(src_manifest_path, "source_dd096cr_manifest"),
        artifact_row(src_gate_path, "source_dd096cr_gate_ledger"),
        artifact_row(src_acceptance_dir, "source_acceptance_dir"),
        artifact_row(ar_manifest_path, "dd096ar_manifest"),
        artifact_row(generated, "copied_acceptance_dir"),
    ]
    for f in sorted(generated.glob("*")):
        if f.is_file():
            artifact_rows.append(artifact_row(f, "generated_acceptance_plan_file"))
    write_csv(out / "dd096cr_artifact_ledger.csv", artifact_rows, ["role", "path", "exists", "kind", "bytes_or_children", "sha256"])

    next_rows = [
        {
            "next_id": "DD096D-R",
            "title": "rerun guarded apply design preflight against root-aware DD096C-R closure",
            "allowed_scope": "preflight/report-only; no DBF writes",
        },
        {
            "next_id": "DD096E-R",
            "title": "rerun external apply-row staging against root-aware acceptance plan",
            "allowed_scope": "external staging only; no active DBF writes",
        },
        {
            "next_id": "DD096F-R",
            "title": "rerun staged-row review and simulated apply",
            "allowed_scope": "simulation only; no active DBF writes",
        },
    ]
    write_csv(out / "dd096cr_next_lane_recommendations.csv", next_rows, ["next_id", "title", "allowed_scope"])

    report = f"""# DD096C-R Acceptance Gate Repair / Closure

Run id: `{args.run_id}`
Status: **{status}**
Created UTC: `{utc_now()}`

## Purpose

DD096C-R produced the correct repaired acceptance shape but reported REVIEW because the original DD096C gate expected `new_objects = 8`.

After DD096A-R added the root `DDICT` command object, the correct root-aware value is:

```text
new_objects = 9
```

That is:

```text
1 root DDICT command object
8 DDICT command-surface objects
```

## Root-aware acceptance summary

- Acceptance rows: **{counts.get('total_acceptance_rows', '')}**
- Reuse existing objects: **{counts.get('duplicate_objects_reuse_active', '')}**
- New objects: **{counts.get('new_objects', '')}**
- OBJID remaps: **{counts.get('objid_remaps', '')}**
- Attr rebases: **{counts.get('attrs_requiring_rebase', '')}**
- Edge rebases: **{counts.get('edges_requiring_rebase', '')}**
- apply_now: **{counts.get('apply_now_total', '')}**

## Boundary

DD096C-R gate repair is report/copy-only. It does not write DBFs, rebuild indexes, mutate HELP/CMDHELPCHK, edit source, or apply schema promotion.
"""
    write_text(out / "DD096CR_ACCEPTANCE_GATE_REPAIR_REPORT.md", report)

    compatible_manifest = dict(src_manifest)
    compatible_manifest.update({
        "contract": "dd096c_candidate_row_acceptance_plan_v0_root_aware_repaired_by_dd096cr",
        "run_id": args.run_id,
        "created_utc": utc_now(),
        "status": status,
        "root_aware_gate_repair": 1,
        "source_dd096cr_manifest": str(src_manifest_path),
        "dd096ar_manifest": str(ar_manifest_path),
        "failures": failures,
        "active_catalog_mutation": 0,
        "dbf_append_replace_delete_pack_zap": 0,
        "cdx_lmdb_create_rebuild": 0,
        "cxx_source_edits": 0,
        "build_file_edits": 0,
        "registry_edits": 0,
        "help_meta_cmdhelpchk_mutation": 0,
        "catalog_regeneration": 0,
        "manual_row_repair": 0,
        "next_recommended_action": "Run DD096D-R using this directory as --dd096c-dir.",
    })
    write_json(out / "dd096c_candidate_row_acceptance_plan_manifest.json", compatible_manifest)

    manifest = {
        "contract": "dd096cr_acceptance_gate_repair_v0",
        "run_id": args.run_id,
        "created_utc": utc_now(),
        "status": status,
        "profiles": args.profile,
        "source_status": src_manifest.get("status", ""),
        "root_aware_new_objects": counts.get("new_objects", ""),
        "failures": failures,
        "compatible_manifest": str(out / "dd096c_candidate_row_acceptance_plan_manifest.json"),
        "generated_acceptance_dir": str(generated),
        "active_catalog_mutation": 0,
        "dbf_append_replace_delete_pack_zap": 0,
        "cdx_lmdb_create_rebuild": 0,
        "cxx_source_edits": 0,
        "build_file_edits": 0,
        "registry_edits": 0,
        "help_meta_cmdhelpchk_mutation": 0,
        "catalog_regeneration": 0,
        "manual_row_repair": 0,
    }
    write_json(out / "dd096cr_acceptance_gate_repair_manifest.json", manifest)

    print(f"DD096C-R acceptance gate repair manifest: {out / 'dd096cr_acceptance_gate_repair_manifest.json'}")
    print(f"status: {status}; acceptance_rows: {counts.get('total_acceptance_rows','')}; reuse_existing_objects: {counts.get('duplicate_objects_reuse_active','')}; new_objects_root_aware: {counts.get('new_objects','')}; remaps: {counts.get('objid_remaps','')}; apply_now: {counts.get('apply_now_total','')}; failures: {failures}")
    return 2 if (args.fail_on_review and failures) else 0


if __name__ == "__main__":
    raise SystemExit(main())
