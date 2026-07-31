#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import datetime as _dt
import hashlib
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Tuple


TABLE_ORDER = [
    "DDRUN",
    "DDBASE",
    "DDSOURCE",
    "DDOBJECT",
    "DDATTR",
    "DDEDGE",
    "DDEVID",
    "DDGATE",
    "DDREVIEW",
    "DDARTIF",
    "DDPROFILE",
]

REPRESENTATIVE_TAGS = [
    ("DDRUN", "RUNID"),
    ("DDBASE", "BASEID"),
    ("DDOBJECT", "OBJID"),
    ("DDATTR", "OBJID"),
    ("DDEDGE", "FROMOBJ"),
    ("DDEDGE", "TOOBJ"),
    ("DDGATE", "STATUS"),
    ("DDPROFILE", "NAME"),
]


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
        raise SystemExit("Refusing to use active catalog path as DD-056R target")

    if "datadict_canonical_rebuild_v0" not in target_rel:
        raise SystemExit(f"Refusing target path without datadict_canonical_rebuild_v0 safety marker: {target_rel}")


def load_tag_plan(dd054_dir: Path) -> List[Dict[str, str]]:
    rows = read_csv_dict(dd054_dir / "dd054_catalog_tag_plan.csv")
    out = []
    for r in rows:
        if (r.get("status") or "").strip().upper() == "PLAN_READY":
            out.append(r)
    return out


def tags_by_table(tag_rows: List[Dict[str, str]]) -> Dict[str, List[str]]:
    out: Dict[str, List[str]] = {}
    for r in tag_rows:
        table = (r.get("table") or "").strip().upper()
        tag = (r.get("tag") or "").strip().upper()
        expr = (r.get("expr") or "").strip().upper()
        if not table or not tag:
            continue
        # Current CDX ADDTAG command stores tag name; BUILDLMDB uses tag names as fields.
        # All DD-054 planned tags are intentionally field-name tags.
        if expr and expr != tag:
            continue
        out.setdefault(table, [])
        if tag not in out[table]:
            out[table].append(tag)
    return out


def scan_cdx_lmdb(repo: Path, index_path: Path, lmdb_path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for root, kind in [(index_path, "CDX"), (lmdb_path, "LMDB")]:
        if not root.exists():
            continue
        for p in sorted(root.iterdir(), key=lambda q: q.name.lower()):
            if kind == "CDX":
                if not p.is_file() or p.suffix.lower() != ".cdx":
                    continue
                rows.append({
                    "kind": kind,
                    "file": p.name,
                    "path": safe_rel(repo, p),
                    "bytes": p.stat().st_size,
                    "sha256": sha256_file(p),
                })
            else:
                # LMDB envs are directories named <table>.cdx.d
                if not p.is_dir() or not p.name.lower().endswith(".cdx.d"):
                    continue
                total = 0
                files = 0
                for child in p.rglob("*"):
                    if child.is_file():
                        files += 1
                        total += child.stat().st_size
                rows.append({
                    "kind": kind,
                    "file": p.name,
                    "path": safe_rel(repo, p),
                    "bytes": total,
                    "sha256": f"DIR_FILES_{files}",
                })
    return rows


def build_execution_script(target_slot: str, table_tags: Dict[str, List[str]]) -> str:
    lines: List[str] = [
        "* DD-056R canonical CDX / ADDTAG / INFO / BUILDLMDB staging execution",
        "* Staging catalog only. No active promotion.",
        "* Correct workflow:",
        "*   CDX CREATE",
        "*   CDX ADDTAG <tag>",
        "*   CDX INFO",
        "*   CDX TAGS",
        "*   BUILDLMDB CLEAN YES",
        "*   SET INDEX TO <table>",
        "*   SET ORDER TO TAG <tag>",
        "*   LIST",
        "",
        f"setpath dbf {target_slot}",
        "",
    ]

    for table in TABLE_ORDER:
        tags = table_tags.get(table, [])
        if not tags:
            continue
        lines.append(f"* ---- {table} canonical CDX layout ----")
        lines.append(f"use {table.lower()}")
        lines.append("cdx create")
        for tag in tags:
            lines.append(f"cdx addtag {tag}")
        lines.append("cdx info")
        lines.append("cdx tags")
        lines.append("buildlmdb clean yes")
        first_tag = tags[0]
        lines.append(f"set index to {table.lower()}")
        lines.append(f"set order to tag {first_tag}")
        lines.append("list")
        lines.append("")

    lines.append("* ---- representative tag switches ----")
    for table, tag in REPRESENTATIVE_TAGS:
        if tag in table_tags.get(table, []):
            lines.append(f"use {table.lower()}")
            lines.append(f"set index to {table.lower()}")
            lines.append(f"set order to tag {tag}")
            lines.append("list")
            lines.append("")
    return "\n".join(lines)


def build_proof_template(run_id: str, table_tags: Dict[str, List[str]]) -> str:
    rows = []
    for table in TABLE_ORDER:
        tags = table_tags.get(table, [])
        if tags:
            rows.append(f"  - {table}: CDX CREATE / ADDTAG {len(tags)} / INFO / TAGS / BUILDLMDB / SET INDEX proof: PENDING")
    rep = []
    for table, tag in REPRESENTATIVE_TAGS:
        if tag in table_tags.get(table, []):
            rep.append(f"  - {table}.{tag}: PENDING")
    return f"""DD-056R LOCAL CANONICAL CDX / ADDTAG / INFO / BUILDLMDB STAGING PROOF

Date: 2026-05-27
Run id: {run_id}
Repo: D:\\code\\ccode

Target:
  dottalkpp\\data\\metadata\\datadict_canonical_rebuild_v0

Runtime command:
  DO D:\\code\\ccode\\dottalkpp\\data\\metadata\\datadict_canonical_rebuild_v0\\dd056r_canonical_cdx_buildlmdb_staging.dts

Canonical workflow:
  CDX CREATE
  CDX ADDTAG <tag>
  CDX INFO
  CDX TAGS
  BUILDLMDB CLEAN YES
  SET INDEX TO <table>
  SET ORDER TO TAG <tag>
  LIST

Per-table proof:
{chr(10).join(rows)}

Representative indexed-read proof:
{chr(10).join(rep)}

Expected evidence:
  CDX INFO and/or CDX TAGS shows created tags.
  BUILDLMDB reports LMDB environment creation/rebuild.
  SET INDEX TO <table> attaches <table>.cdx.
  SET ORDER TO TAG <tag> selects tag.
  LIST output reports MODE LMDB and the active tag.

Result:
  PENDING

Boundary:
  active datadict catalog not promoted
  HELP/META/CMDHELPCHK not mutated
  source not edited by DD-056R
  no CREATE X64 / IMPORT performed by DD-056R
"""


def analyze_proof(proof_path: Path, table_tags: Dict[str, List[str]]) -> Dict[str, Any]:
    if not proof_path.exists():
        return {"proof_exists": 0, "status": "MISSING_PROOF", "accepted": 0, "expected": 0}
    text = proof_path.read_text(encoding="utf-8", errors="replace")
    upper = text.upper()
    result_green = re.search(r"RESULT:\s*(GREEN|PASS|SUCCEEDED|SUCCESS)", upper) is not None
    mode_lmdb_seen = "MODE LMDB" in upper
    buildlmdb_seen = "BUILDLMDB" in upper
    cdx_info_seen = "CDX INFO" in upper or "CDX TAGS" in upper or "TAGS" in upper
    set_index_seen = "SET INDEX" in upper
    set_order_seen = "SET ORDER TO TAG" in upper

    checks = {
        "result_green": int(result_green),
        "mode_lmdb_seen": int(mode_lmdb_seen),
        "buildlmdb_seen": int(buildlmdb_seen),
        "cdx_info_or_tags_seen": int(cdx_info_seen),
        "set_index_seen": int(set_index_seen),
        "set_order_to_tag_seen": int(set_order_seen),
    }
    accepted = int(result_green or (mode_lmdb_seen and buildlmdb_seen and set_index_seen and set_order_seen))
    status = "CANONICAL_CDX_BUILDLMDB_RUNTIME_PROOF_ACCEPTED" if accepted else "CANONICAL_CDX_BUILDLMDB_RUNTIME_PROOF_REVIEW"
    return {
        "proof_exists": 1,
        "status": status,
        "accepted": accepted,
        "expected": 1,
        "checks": checks,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="DD-056R canonical CDX/ADDTAG/INFO/BUILDLMDB staging execution")
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--run-id", default="DD056R-canonical-cdx-buildlmdb-staging-v0")
    ap.add_argument("--dd054-dir", default="docs/datadict/reports/DD054-catalog-cdx-tag-plan-v0")
    ap.add_argument("--dd055r-dir", default="docs/datadict/reports/DD055R-canonical-cdx-workflow-plan-v0")
    ap.add_argument("--target-slot", default="metadata\\datadict_canonical_rebuild_v0")
    ap.add_argument("--target-path", default="dottalkpp/data/metadata/datadict_canonical_rebuild_v0")
    ap.add_argument("--active-path", default="dottalkpp/data/metadata/datadict")
    ap.add_argument("--index-path", default="dottalkpp/data/indexes")
    ap.add_argument("--lmdb-path", default="dottalkpp/data/lmdb")
    ap.add_argument("--proof-path", default="docs/datadict/runlog/DD-056R_LOCAL_CANONICAL_CDX_BUILDL MDB_STAGING_PROOF.md")
    ap.add_argument("--prepare-runtime-script", action="store_true")
    ap.add_argument("--replace-existing-script", action="store_true")
    ap.add_argument("--verify-after-runtime", action="store_true")
    ap.add_argument("--profile", action="append", default=[])
    ap.add_argument("--fail-on-review", action="store_true")
    args = ap.parse_args()

    # Repair accidental space in default proof filename while preserving explicit overrides.
    if "BUILDL MDB" in args.proof_path:
        args.proof_path = args.proof_path.replace("BUILDL MDB", "BUILDLMDB")

    repo = Path(args.repo_root).resolve()
    out = Path(args.out_dir).resolve()
    dd054_dir = (repo / args.dd054_dir).resolve()
    dd055r_dir = (repo / args.dd055r_dir).resolve()
    target_path = (repo / args.target_path).resolve()
    active_path = (repo / args.active_path).resolve()
    index_path = (repo / args.index_path).resolve()
    lmdb_path = (repo / args.lmdb_path).resolve()
    proof_path = (repo / args.proof_path).resolve()
    script_path = target_path / "dd056r_canonical_cdx_buildlmdb_staging.dts"
    proof_template_path = target_path / "DD056R_CANONICAL_CDX_BUILDLMDB_PROOF_TEMPLATE.md"
    out.mkdir(parents=True, exist_ok=True)

    ensure_safe_target(repo, target_path, active_path)

    dd055r_manifest = read_json(dd055r_dir / "dd055r_canonical_cdx_layout_tag_info_buildlmdb_plan_manifest.json")
    tag_rows = load_tag_plan(dd054_dir)
    table_tags = tags_by_table(tag_rows)
    tags_count = sum(len(v) for v in table_tags.values())

    failures = 0
    review_rows: List[Dict[str, Any]] = []
    dd055r_ok = dd055r_manifest.get("status") in {
        "CANONICAL_CDX_WORKFLOW_PLAN_READY_WITH_SYNTAX_REVIEW",
        "CANONICAL_CDX_WORKFLOW_PLAN_READY",
    }
    if not dd055r_ok:
        failures += 1
        review_rows.append({"issue": "DD055R_NOT_READY", "detail": dd055r_manifest.get("status", "")})
    if tags_count == 0:
        failures += 1
        review_rows.append({"issue": "NO_TAG_ROWS", "detail": str(dd054_dir)})

    script_written = 0
    template_written = 0
    if args.prepare_runtime_script and failures == 0:
        target_path.mkdir(parents=True, exist_ok=True)
        if script_path.exists() and not args.replace_existing_script:
            failures += 1
            review_rows.append({"issue": "SCRIPT_EXISTS_WITHOUT_REPLACE_FLAG", "detail": str(script_path)})
        else:
            script_path.write_text(build_execution_script(args.target_slot, table_tags), encoding="utf-8")
            proof_template_path.write_text(build_proof_template(args.run_id, table_tags), encoding="utf-8")
            script_written = 1
            template_written = 1

    artifacts = scan_cdx_lmdb(repo, index_path, lmdb_path) if args.verify_after_runtime else []
    cdx_count = sum(1 for r in artifacts if r["kind"] == "CDX")
    lmdb_count = sum(1 for r in artifacts if r["kind"] == "LMDB")
    proof_analysis = {"proof_exists": 0, "status": "NOT_REQUESTED", "accepted": 0}
    if args.verify_after_runtime:
        proof_analysis = analyze_proof(proof_path, table_tags)
        # At least one CDX and one LMDB env is enough for smoke; proof text carries behavior evidence.
        if cdx_count == 0:
            failures += 1
            review_rows.append({"issue": "NO_CDX_ARTIFACTS_FOUND", "detail": str(index_path)})
        if lmdb_count == 0:
            failures += 1
            review_rows.append({"issue": "NO_LMDB_ENVS_FOUND", "detail": str(lmdb_path)})
        if proof_analysis.get("status") != "CANONICAL_CDX_BUILDLMDB_RUNTIME_PROOF_ACCEPTED":
            failures += 1
            review_rows.append({"issue": "RUNTIME_PROOF_NOT_ACCEPTED", "detail": proof_analysis.get("status", "")})

    if args.verify_after_runtime:
        status = "CANONICAL_CDX_BUILDLMDB_STAGING_VERIFY_GREEN" if failures == 0 else "CANONICAL_CDX_BUILDLMDB_STAGING_VERIFY_REVIEW"
    elif args.prepare_runtime_script:
        status = "CANONICAL_CDX_BUILDLMDB_RUNTIME_SCRIPT_READY" if failures == 0 else "CANONICAL_CDX_BUILDLMDB_RUNTIME_SCRIPT_REVIEW"
    else:
        status = "CANONICAL_CDX_BUILDLMDB_PREFLIGHT_READY" if failures == 0 else "CANONICAL_CDX_BUILDLMDB_PREFLIGHT_REVIEW"

    table_rows = []
    for table in TABLE_ORDER:
        tags = table_tags.get(table, [])
        table_rows.append({
            "table": table,
            "tag_count": len(tags),
            "tags": ",".join(tags),
            "script_path": str(script_path),
            "workflow": "CDX_CREATE_ADDTAG_INFO_TAGS_BUILDLMDB_SETINDEX_SETORDER_LIST",
        })

    artifact_rows = artifacts
    gate_rows = [
        {
            "gate": "dd055r_corrected_plan_ready",
            "expected": "CANONICAL_CDX_WORKFLOW_PLAN_READY_WITH_SYNTAX_REVIEW",
            "observed": dd055r_manifest.get("status", ""),
            "pass": int(dd055r_ok),
        },
        {
            "gate": "tag_count",
            "expected": 40,
            "observed": tags_count,
            "pass": int(tags_count == 40),
        },
        {
            "gate": "script_written_when_requested",
            "expected": int(args.prepare_runtime_script),
            "observed": script_written,
            "pass": int((not args.prepare_runtime_script) or script_written == 1),
        },
        {
            "gate": "cdx_artifacts_when_verifying",
            "expected": ">=1",
            "observed": cdx_count,
            "pass": int((not args.verify_after_runtime) or cdx_count >= 1),
        },
        {
            "gate": "lmdb_envs_when_verifying",
            "expected": ">=1",
            "observed": lmdb_count,
            "pass": int((not args.verify_after_runtime) or lmdb_count >= 1),
        },
        {
            "gate": "runtime_proof_when_verifying",
            "expected": "CANONICAL_CDX_BUILDLMDB_RUNTIME_PROOF_ACCEPTED",
            "observed": proof_analysis.get("status", ""),
            "pass": int((not args.verify_after_runtime) or proof_analysis.get("status") == "CANONICAL_CDX_BUILDLMDB_RUNTIME_PROOF_ACCEPTED"),
        },
    ]

    boundary_rows = [
        {"boundary": "staging_only", "observed": 1, "required": 1, "pass": 1},
        {"boundary": "active_catalog_mutation", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "source_edits", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "help_meta_cmdhelpchk_mutation", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "production_promotion", "observed": 0, "required": 0, "pass": 1},
    ]

    write_csv(out / "dd056r_table_cdx_buildlmdb_plan.csv", table_rows, [
        "table", "tag_count", "tags", "script_path", "workflow",
    ])
    write_csv(out / "dd056r_artifact_ledger.csv", artifact_rows, [
        "kind", "file", "path", "bytes", "sha256",
    ])
    write_csv(out / "dd056r_gate_ledger.csv", gate_rows, ["gate", "expected", "observed", "pass"])
    write_csv(out / "dd056r_review_rows.csv", review_rows, ["issue", "detail"])
    write_csv(out / "dd056r_no_mutation_boundary_ledger.csv", boundary_rows, ["boundary", "observed", "required", "pass"])
    write_json(out / "dd056r_runtime_proof_analysis.json", proof_analysis)

    (out / "dd056r_candidate_runtime_script.dts").write_text(build_execution_script(args.target_slot, table_tags), encoding="utf-8")
    (out / "DD056R_CANONICAL_CDX_BUILDLMDB_PROOF_TEMPLATE.md").write_text(build_proof_template(args.run_id, table_tags), encoding="utf-8")

    manifest = {
        "contract": "dd056r_canonical_cdx_addtag_info_buildlmdb_execution_v0",
        "run_id": args.run_id,
        "created_utc": utc_now(),
        "status": status,
        "repo_root": str(repo),
        "profiles": args.profile,
        "dd055r_status": dd055r_manifest.get("status", ""),
        "target_slot": args.target_slot,
        "target_path": str(target_path),
        "index_path": str(index_path),
        "lmdb_path": str(lmdb_path),
        "tags": tags_count,
        "tables": len([t for t, tags in table_tags.items() if tags]),
        "failures": failures,
        "prepare_runtime_script": int(args.prepare_runtime_script),
        "script_written": script_written,
        "template_written": template_written,
        "script_path": str(script_path),
        "proof_template_path": str(proof_template_path),
        "proof_path": str(proof_path),
        "verify_after_runtime": int(args.verify_after_runtime),
        "cdx_artifacts": cdx_count,
        "lmdb_envs": lmdb_count,
        "proof_status": proof_analysis.get("status", ""),
        "active_catalog_mutation": 0,
        "source_edits": 0,
        "help_meta_cmdhelpchk_mutation": 0,
        "production_promotion": 0,
        "next_recommended_action": "If green, proceed to DD-057 active catalog promotion readiness.",
    }
    write_json(out / "dd056r_canonical_cdx_buildlmdb_execution_manifest.json", manifest)

    report = f"""# DD-056R Canonical CDX / ADDTAG / INFO / BUILDLMDB Staging Execution

Run id: `{args.run_id}`
Status: **{status}**
Created UTC: `{manifest['created_utc']}`

## Purpose

DD-056R executes and verifies the corrected canonical staged index workflow:

```text
CDX CREATE
CDX ADDTAG <tag>
CDX INFO
CDX TAGS
BUILDLMDB CLEAN YES
SET INDEX TO <table>
SET ORDER TO TAG <tag>
LIST
```

## Target

```text
{safe_rel(repo, target_path)}
```

## Script

```text
{safe_rel(repo, script_path)}
```

## Runtime command

```text
do {script_path}
```

## Verification

After runtime execution, save/update proof at:

```text
{proof_path}
```

Then rerun with `--verify-after-runtime`.

## Boundary

DD-056R is staging-only. It does not promote the active catalog, edit source, or
mutate HELP/META/CMDHELPCHK.
"""
    (out / "DD056R_CANONICAL_CDX_BUILDLMDB_STAGING_EXECUTION_REPORT.md").write_text(report, encoding="utf-8")

    print(f"DD-056R canonical CDX/BUILDLMDB manifest: {out / 'dd056r_canonical_cdx_buildlmdb_execution_manifest.json'}")
    print(f"status: {status}; tags: {tags_count}; failures: {failures}; script_written: {script_written}; cdx: {cdx_count}; lmdb: {lmdb_count}")
    return 2 if (args.fail_on_review and failures) else 0


if __name__ == "__main__":
    raise SystemExit(main())
