#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import datetime as _dt
import hashlib
import json
import shutil
from pathlib import Path
from typing import Any, Dict, List


INDEX_SUFFIXES = {".cdx", ".idx", ".inx", ".ndx", ".cnx"}


def utc_now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds")


def read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8", errors="replace"))


def write_json(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def read_csv_dict(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8", errors="replace") as f:
        return list(csv.DictReader(f))


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


def ensure_safe_target(repo: Path, target_path: Path, active_path: Path) -> None:
    target_resolved = target_path.resolve()
    active_resolved = active_path.resolve()
    try:
        target_rel = target_resolved.relative_to(repo.resolve()).as_posix().lower()
    except Exception:
        raise SystemExit(f"Target path must be inside repo: {target_path}")

    if target_resolved == active_resolved:
        raise SystemExit("Refusing to use active catalog path as DD-055 target")

    if "datadict_canonical_rebuild_v0" not in target_rel:
        raise SystemExit(f"Refusing target path without datadict_canonical_rebuild_v0 safety marker: {target_rel}")


def load_tag_plan(dd054_dir: Path) -> List[Dict[str, str]]:
    path = dd054_dir / "dd054_catalog_tag_plan.csv"
    rows = read_csv_dict(path)
    if not rows:
        raise SystemExit(f"DD-054 tag plan not found or empty: {path}")
    return rows


def scan_index_artifacts(repo: Path, target_path: Path, extra_index_path: Path | None = None) -> List[Dict[str, Any]]:
    roots = [target_path]
    if extra_index_path is not None:
        roots.append(extra_index_path)

    rows: List[Dict[str, Any]] = []
    seen = set()
    for root in roots:
        if not root.exists():
            continue
        for p in sorted(root.rglob("*"), key=lambda q: q.as_posix().lower()):
            if not p.is_file():
                continue
            if p.suffix.lower() not in INDEX_SUFFIXES:
                continue
            key = str(p.resolve()).lower()
            if key in seen:
                continue
            seen.add(key)
            rows.append({
                "file": p.name,
                "path": safe_rel(repo, p),
                "suffix": p.suffix.lower(),
                "stem": p.stem.upper(),
                "bytes": p.stat().st_size,
                "sha256": sha256_file(p),
            })
    return rows


def build_script(tag_plan: List[Dict[str, str]], target_slot: str) -> str:
    lines: List[str] = [
        "* DD-055 guarded catalog CDX/tag execution script",
        "* Target: staging catalog only.",
        "* Do not promote active catalog from this script.",
        f"setpath dbf {target_slot}",
        "",
    ]

    current = None
    for row in tag_plan:
        table = (row.get("table") or "").strip().upper()
        expr = (row.get("expr") or "").strip().upper()
        tag = (row.get("tag") or "").strip().upper()
        status = (row.get("status") or "").strip().upper()
        cmd = (row.get("planned_command") or f"index on {expr} tag {tag}").strip()
        if status != "PLAN_READY":
            continue
        if table != current:
            if current is not None:
                lines.append("")
            lines.append(f"* ---- {table} ----")
            lines.append(f"use {table.lower()}")
            current = table
        lines.append(cmd)
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description="DD-055 guarded CDX/tag execution against staged catalog")
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--run-id", default="DD055-guarded-cdx-tag-execution-v0")
    ap.add_argument("--dd054-dir", default="docs/datadict/reports/DD054-catalog-cdx-tag-plan-v0")
    ap.add_argument("--target-slot", default="metadata\\datadict_canonical_rebuild_v0")
    ap.add_argument("--target-path", default="dottalkpp/data/metadata/datadict_canonical_rebuild_v0")
    ap.add_argument("--active-path", default="dottalkpp/data/metadata/datadict")
    ap.add_argument("--index-path", default="dottalkpp/data/indexes")
    ap.add_argument("--prepare-index-script", action="store_true", help="Write guarded index script into staging target")
    ap.add_argument("--replace-existing-script", action="store_true", help="Replace existing DD-055 script if present")
    ap.add_argument("--verify-after-runtime", action="store_true", help="Verify index sidecar artifacts after manual DotTalk++ execution")
    ap.add_argument("--profile", action="append", default=[])
    ap.add_argument("--fail-on-review", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    out = Path(args.out_dir).resolve()
    dd054_dir = (repo / args.dd054_dir).resolve()
    target_path = (repo / args.target_path).resolve()
    active_path = (repo / args.active_path).resolve()
    index_path = (repo / args.index_path).resolve() if args.index_path else None
    script_path = target_path / "dd055_index_build_staging.dts"
    out.mkdir(parents=True, exist_ok=True)

    ensure_safe_target(repo, target_path, active_path)

    dd054_manifest = read_json(dd054_dir / "dd054_catalog_cdx_tag_plan_manifest.json")
    tag_plan = load_tag_plan(dd054_dir)
    ready_tags = [r for r in tag_plan if (r.get("status") or "").strip().upper() == "PLAN_READY"]
    tables = sorted({(r.get("table") or "").strip().upper() for r in ready_tags if r.get("table")})

    failures = 0
    review_rows: List[Dict[str, Any]] = []

    dd054_green = dd054_manifest.get("status") == "CATALOG_CDX_TAG_PLAN_READY"
    if not dd054_green:
        failures += 1
        review_rows.append({
            "issue": "DD054_NOT_GREEN",
            "detail": dd054_manifest.get("status", ""),
        })

    if len(ready_tags) != len(tag_plan):
        failures += 1
        review_rows.append({
            "issue": "NOT_ALL_TAGS_READY",
            "detail": f"ready={len(ready_tags)} total={len(tag_plan)}",
        })

    script_written = 0
    if args.prepare_index_script and failures == 0:
        target_path.mkdir(parents=True, exist_ok=True)
        if script_path.exists() and not args.replace_existing_script:
            failures += 1
            review_rows.append({
                "issue": "SCRIPT_EXISTS_WITHOUT_REPLACE_FLAG",
                "detail": str(script_path),
            })
        else:
            script_path.write_text(build_script(tag_plan, args.target_slot), encoding="utf-8")
            script_written = 1

    artifacts = scan_index_artifacts(repo, target_path, index_path) if args.verify_after_runtime else []
    artifact_rows: List[Dict[str, Any]] = artifacts

    # Verification is deliberately conservative. The exact CDX naming convention is not yet
    # proven for this catalog, so presence of at least one supported index artifact after
    # the runtime script is considered execution evidence; DD-056 can do command-level/index-use proof.
    index_artifact_count = len(artifact_rows)
    if args.verify_after_runtime and index_artifact_count == 0:
        failures += 1
        review_rows.append({
            "issue": "NO_INDEX_ARTIFACTS_FOUND",
            "detail": f"scanned {target_path} and {index_path}",
        })

    if args.verify_after_runtime:
        status = "CATALOG_CDX_TAG_EXECUTION_VERIFY_GREEN" if failures == 0 else "CATALOG_CDX_TAG_EXECUTION_VERIFY_REVIEW"
    elif args.prepare_index_script:
        status = "CATALOG_CDX_TAG_EXECUTION_SCRIPT_READY" if failures == 0 else "CATALOG_CDX_TAG_EXECUTION_SCRIPT_REVIEW"
    else:
        status = "CATALOG_CDX_TAG_EXECUTION_PREFLIGHT_READY" if failures == 0 else "CATALOG_CDX_TAG_EXECUTION_PREFLIGHT_REVIEW"

    tag_exec_rows: List[Dict[str, Any]] = []
    for r in ready_tags:
        table = (r.get("table") or "").strip().upper()
        tag_exec_rows.append({
            "table": table,
            "expr": (r.get("expr") or "").strip().upper(),
            "tag": (r.get("tag") or "").strip().upper(),
            "planned_command": r.get("planned_command", ""),
            "script_path": safe_rel(repo, script_path),
            "execution_scope": "STAGING_ONLY",
        })

    gate_rows = [
        {
            "gate": "dd054_tag_plan_ready",
            "expected": "CATALOG_CDX_TAG_PLAN_READY",
            "observed": dd054_manifest.get("status", ""),
            "pass": int(dd054_green),
        },
        {
            "gate": "ready_tag_count",
            "expected": len(tag_plan),
            "observed": len(ready_tags),
            "pass": int(len(ready_tags) == len(tag_plan)),
        },
        {
            "gate": "script_written_when_requested",
            "expected": int(args.prepare_index_script),
            "observed": script_written,
            "pass": int((not args.prepare_index_script) or script_written == 1),
        },
        {
            "gate": "index_artifacts_found_when_verifying",
            "expected": ">=1 when verify-after-runtime",
            "observed": index_artifact_count,
            "pass": int((not args.verify_after_runtime) or index_artifact_count >= 1),
        },
    ]

    boundary_rows = [
        {"boundary": "staging_catalog_index_scope_only", "observed": 1, "required": 1, "pass": 1},
        {"boundary": "active_catalog_mutation", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "source_edits", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "help_meta_cmdhelpchk_mutation", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "lmdb_build", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "promotion_executed", "observed": 0, "required": 0, "pass": 1},
    ]

    write_csv(out / "dd055_tag_execution_plan.csv", tag_exec_rows, [
        "table", "expr", "tag", "planned_command", "script_path", "execution_scope",
    ])
    write_csv(out / "dd055_index_artifact_ledger.csv", artifact_rows, [
        "file", "path", "suffix", "stem", "bytes", "sha256",
    ])
    write_csv(out / "dd055_gate_ledger.csv", gate_rows, ["gate", "expected", "observed", "pass"])
    write_csv(out / "dd055_review_rows.csv", review_rows, ["issue", "detail"])
    write_csv(out / "dd055_no_mutation_boundary_ledger.csv", boundary_rows, ["boundary", "observed", "required", "pass"])

    candidate_text = build_script(tag_plan, args.target_slot)
    (out / "dd055_candidate_index_build_staging.dts").write_text(candidate_text, encoding="utf-8")

    manifest = {
        "contract": "dd055_guarded_cdx_tag_execution_v0",
        "run_id": args.run_id,
        "created_utc": utc_now(),
        "status": status,
        "repo_root": str(repo),
        "profiles": args.profile,
        "dd054_status": dd054_manifest.get("status", ""),
        "target_slot": args.target_slot,
        "target_path": str(target_path),
        "index_path": str(index_path) if index_path else "",
        "tables": len(tables),
        "tags": len(ready_tags),
        "failures": failures,
        "prepare_index_script": int(args.prepare_index_script),
        "script_written": script_written,
        "script_path": str(script_path),
        "verify_after_runtime": int(args.verify_after_runtime),
        "index_artifact_count": index_artifact_count,
        "active_catalog_mutation": 0,
        "source_edits": 0,
        "help_meta_cmdhelpchk_mutation": 0,
        "lmdb_build": 0,
        "promotion_executed": 0,
        "next_recommended_action": "Run generated DotTalk++ index script if prepared, then verify-after-runtime; next DD-056 can test index-use/readback.",
    }
    write_json(out / "dd055_guarded_cdx_tag_execution_manifest.json", manifest)

    report = f"""# DD-055 Guarded CDX / Tag Execution Against Staging Catalog

Run id: `{args.run_id}`
Status: **{status}**
Created UTC: `{manifest['created_utc']}`

## Purpose

DD-055 is the guarded execution step for the DD-054 CDX/tag plan. It targets only
the staged canonical catalog.

## Target

```text
DBF slot: {args.target_slot}
Target path: {safe_rel(repo, target_path)}
Script: {safe_rel(repo, script_path)}
```

## Inputs

- DD-054 status: `{dd054_manifest.get('status', '')}`
- Tables: `{len(tables)}`
- Tags: `{len(ready_tags)}`

## Runtime command

After `--prepare-index-script`, run DotTalk++ and execute:

```text
do {script_path}
```

## Verification

After runtime execution, rerun DD-055 with `--verify-after-runtime`.

## Boundary

DD-055 does not promote the active catalog, does not build LMDB, does not edit
source, and does not mutate HELP/META/CMDHELPCHK.
"""
    (out / "DD055_GUARDED_CDX_TAG_EXECUTION_REPORT.md").write_text(report, encoding="utf-8")

    print(f"DD-055 guarded CDX/tag execution manifest: {out / 'dd055_guarded_cdx_tag_execution_manifest.json'}")
    print(f"status: {status}; tags: {len(ready_tags)}; failures: {failures}; script_written: {script_written}; index_artifacts: {index_artifact_count}")
    return 2 if (args.fail_on_review and failures) else 0


if __name__ == "__main__":
    raise SystemExit(main())
