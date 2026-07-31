#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List


EXPECTED_DD096_STATUS = "DATADICT_SCHEMA_PROMOTION_CATALOG_POLICY_READY"
EXPECTED_DD095_STATUS = "DATADICT_LAYOUT_POLICY_DOCUMENTED_GREEN"
EXPECTED_DD094_STATUS = "DATADICT_WORKSPACE_SCHEMA_SAVEPOINT_GREEN"
EXPECTED_DD093C_STATUS = "DDICT_FULL_PATH_REMAP_RUNTIME_CLOSURE_GREEN"

SMOKE_COMMANDS = [
    "SETPATH",
    "DO ddbase",
    "WORKSPACE LOAD ddbase",
    "WORKSPACE",
    "DDICT STATUS",
    "DDICT TABLES",
    "DDICT TAGS DDATTR",
    "DDICT TAGS DDOBJECT",
    "DDICT REL DDOBJECT OUT",
    "DDICT EVIDENCE DDOBJECT",
]

RUNTIME_NEEDLES = [
    ("setpath_seen", "SETPATH"),
    ("do_ddbase_seen", "DO ddbase"),
    ("workspace_load_seen", "WORKSPACE LOAD"),
    ("workspace_restored_11_7", "WORKSPACE LOAD: restored 11 area(s) and 7 relation(s)."),
    ("workspace_11_open", "WORKSPACE: 11 area(s) open."),
    ("ddict_status_seen", "DDICT STATUS"),
    ("active_catalog_datadict", "Active catalog: D:\\code\\ccode\\dottalkpp\\data\\datadict"),
    ("dbf_tables_11", "DBF tables    : 11 / 11"),
    ("catalog_present", "Catalog state : ACTIVE_CATALOG_PRESENT"),
    ("ddict_tables_seen", "DDICT TABLES"),
    ("ddict_tags_ddattr_seen", "DDICT TAGS DDATTR"),
    ("ddattr_cdx_subroot", "data\\indexes\\datadict\\ddattr.cdx"),
    ("ddattr_lmdb_subroot", "data\\lmdb\\datadict\\DDATTR.cdx.d"),
    ("ddict_tags_ddobject_seen", "DDICT TAGS DDOBJECT"),
    ("ddobject_cdx_subroot", "data\\indexes\\datadict\\ddobject.cdx"),
    ("ddobject_lmdb_subroot", "data\\lmdb\\datadict\\DDOBJECT.cdx.d"),
    ("ddict_rel_seen", "DDICT REL DDOBJECT OUT"),
    ("rel_outgoing_seen", "Outgoing edges:"),
    ("has_field_seen", "HAS_FIELD"),
    ("has_tag_seen", "HAS_TAG"),
    ("ddict_evidence_seen", "DDICT EVIDENCE DDOBJECT"),
    ("attribute_evidence_rows_seen", "Attribute evidence rows:"),
    ("primary_key_seen", "primary_key"),
]

PROTECTED_ARTIFACTS = [
    "dottalkpp/data/datadict",
    "dottalkpp/data/indexes/datadict",
    "dottalkpp/data/lmdb/datadict",
    "dottalkpp/data/workspaces/ddbase.dtschema",
    "docs/datadict/policy/DD095_DATADICT_LAYOUT_POLICY.md",
    "src/datadict/ddict_catalog_paths.cpp",
    "src/cli/cmd_ddict.cpp",
    "src/CMakeLists.txt",
]


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


def artifact_row(repo: Path, rel_path: str, role: str) -> Dict[str, Any]:
    p = repo / rel_path
    return {
        "role": role,
        "path": rel_path,
        "exists": int(p.exists()),
        "kind": "dir" if p.exists() and p.is_dir() else "file" if p.exists() and p.is_file() else "",
        "bytes_or_children": p.stat().st_size if p.exists() and p.is_file() else sum(1 for _ in p.iterdir()) if p.exists() and p.is_dir() else 0,
        "sha256": sha256(p),
    }


def make_smoke_text(include_quit: bool = False) -> str:
    cmds = list(SMOKE_COMMANDS)
    if include_quit:
        cmds.append("QUIT")
    # Final blank line is intentional for DotTalk++ paste/script execution.
    return "\n".join(cmds) + "\n\n"


def main() -> int:
    ap = argparse.ArgumentParser(description="DD097 Data Dictionary layout regression smoke package")
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--run-id", default="DD097-datadict-layout-regression-smoke-v0")
    ap.add_argument("--dd096-dir", default="docs/datadict/reports/DD096-datadict-schema-promotion-catalog-policy-v0")
    ap.add_argument("--dd095-dir", default="docs/datadict/reports/DD095-datadict-layout-policy-documentation-v0")
    ap.add_argument("--dd094-dir", default="docs/datadict/reports/DD094-datadict-workspace-schema-savepoint-v0")
    ap.add_argument("--dd093c-dir", default="docs/datadict/reports/DD093C-ddict-full-path-remap-runtime-closure-v0")
    ap.add_argument("--runtime-proof", default="")
    ap.add_argument("--write-closure", action="store_true")
    ap.add_argument("--closure-path", default="docs/datadict/runlog/DD-097_DATADICT_LAYOUT_REGRESSION_SMOKE_CLOSURE.md")
    ap.add_argument("--profile", action="append", default=[])
    ap.add_argument("--fail-on-review", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    out = Path(args.out_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)

    dd096_manifest_path = repo / args.dd096_dir / "dd096_datadict_schema_promotion_catalog_policy_manifest.json"
    dd095_manifest_path = repo / args.dd095_dir / "dd095_datadict_layout_policy_documentation_manifest.json"
    dd094_manifest_path = repo / args.dd094_dir / "dd094_datadict_workspace_schema_savepoint_manifest.json"
    dd093c_manifest_path = repo / args.dd093c_dir / "dd093c_ddict_full_path_remap_runtime_closure_manifest.json"

    dd096 = read_json(dd096_manifest_path)
    dd095 = read_json(dd095_manifest_path)
    dd094 = read_json(dd094_manifest_path)
    dd093c = read_json(dd093c_manifest_path)

    generated_dir = out / "generated_smoke"
    generated_dir.mkdir(parents=True, exist_ok=True)
    smoke_dts = generated_dir / "DD097_DATADICT_LAYOUT_REGRESSION_SMOKE.dts"
    smoke_cli = generated_dir / "DD097_DATADICT_LAYOUT_REGRESSION_SMOKE_CLI_PASTE.txt"
    smoke_cli_quit = generated_dir / "DD097_DATADICT_LAYOUT_REGRESSION_SMOKE_CLI_PASTE_WITH_QUIT.txt"
    write_text(smoke_dts, make_smoke_text(False))
    write_text(smoke_cli, make_smoke_text(False))
    write_text(smoke_cli_quit, make_smoke_text(True))

    runtime_rows: List[Dict[str, Any]] = []
    runtime_path = repo / args.runtime_proof if args.runtime_proof else None
    runtime_text = read_text(runtime_path) if runtime_path else ""
    runtime_lower = runtime_text.lower()
    for key, needle in RUNTIME_NEEDLES:
        runtime_rows.append({
            "proof_key": key,
            "needle": needle,
            "seen": int(needle.lower() in runtime_lower) if runtime_text else "",
        })

    command_rows = []
    for i, cmd in enumerate(SMOKE_COMMANDS, start=1):
        command_rows.append({
            "order": i,
            "command": cmd,
            "purpose": {
                "SETPATH": "show current runtime path family",
                "DO ddbase": "activate Data Dictionary DBF/INDEXES/LMDB roots",
                "WORKSPACE LOAD ddbase": "restore 11 areas and 7 relations",
                "WORKSPACE": "display restored workspace",
                "DDICT STATUS": "prove active catalog and table count",
                "DDICT TABLES": "prove 11 catalog tables visible",
                "DDICT TAGS DDATTR": "prove CDX/LMDB subroot artifact discovery for DDATTR",
                "DDICT TAGS DDOBJECT": "prove CDX/LMDB subroot artifact discovery for DDOBJECT",
                "DDICT REL DDOBJECT OUT": "prove relation traversal",
                "DDICT EVIDENCE DDOBJECT": "prove evidence/attribute inspection",
            }.get(cmd, ""),
        })

    artifact_rows = [
        artifact_row(repo, str(dd096_manifest_path.relative_to(repo)), "dd096_manifest"),
        artifact_row(repo, str(dd095_manifest_path.relative_to(repo)), "dd095_manifest"),
        artifact_row(repo, str(dd094_manifest_path.relative_to(repo)), "dd094_manifest"),
        artifact_row(repo, str(dd093c_manifest_path.relative_to(repo)), "dd093c_manifest"),
    ]
    if runtime_path:
        try:
            runtime_rel = str(runtime_path.resolve().relative_to(repo.resolve())).replace("\\", "/")
        except Exception:
            runtime_rel = str(runtime_path)
        artifact_rows.append(artifact_row(repo, runtime_rel, "runtime_proof"))
    for p in PROTECTED_ARTIFACTS:
        artifact_rows.append(artifact_row(repo, p, "protected_observed"))
    for role, path in [
        ("generated_smoke_dts", smoke_dts),
        ("generated_cli_paste", smoke_cli),
        ("generated_cli_paste_with_quit", smoke_cli_quit),
    ]:
        artifact_rows.append({
            "role": role,
            "path": str(path),
            "exists": int(path.exists()),
            "kind": "file",
            "bytes_or_children": path.stat().st_size if path.exists() else 0,
            "sha256": sha256(path),
        })

    runtime_seen = sum(1 for r in runtime_rows if r["seen"] == 1)
    runtime_total = len(runtime_rows)
    runtime_required_pass = int((not args.runtime_proof) or runtime_seen == runtime_total)

    boundary_rows = [
        {"boundary": "layout_regression_smoke_only", "observed": 1, "required": 1, "pass": 1},
        {"boundary": "cxx_source_edits", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "build_file_edits", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "registry_edits", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "active_catalog_mutation", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "dbf_append_replace_delete_pack_zap", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "cdx_lmdb_create_rebuild", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "help_meta_cmdhelpchk_mutation", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "catalog_regeneration", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "manual_row_repair", "observed": 0, "required": 0, "pass": 1},
    ]

    gates = [
        {"gate": "dd096_ready", "expected": EXPECTED_DD096_STATUS, "observed": dd096.get("status", ""), "pass": int(dd096.get("status") == EXPECTED_DD096_STATUS)},
        {"gate": "dd095_green", "expected": EXPECTED_DD095_STATUS, "observed": dd095.get("status", ""), "pass": int(dd095.get("status") == EXPECTED_DD095_STATUS)},
        {"gate": "dd094_green", "expected": EXPECTED_DD094_STATUS, "observed": dd094.get("status", ""), "pass": int(dd094.get("status") == EXPECTED_DD094_STATUS)},
        {"gate": "dd093c_green", "expected": EXPECTED_DD093C_STATUS, "observed": dd093c.get("status", ""), "pass": int(dd093c.get("status") == EXPECTED_DD093C_STATUS)},
        {"gate": "smoke_dts_generated", "expected": 1, "observed": int(smoke_dts.exists()), "pass": int(smoke_dts.exists())},
        {"gate": "smoke_command_count", "expected": len(SMOKE_COMMANDS), "observed": len(command_rows), "pass": int(len(command_rows) == len(SMOKE_COMMANDS))},
        {"gate": "runtime_proof_supplied", "expected": "optional", "observed": int(bool(args.runtime_proof)), "pass": 1},
        {"gate": "runtime_needles_all_seen_if_supplied", "expected": runtime_total if args.runtime_proof else "not supplied", "observed": runtime_seen if args.runtime_proof else "not supplied", "pass": runtime_required_pass},
        {"gate": "no_mutation", "expected": 1, "observed": 1, "pass": 1},
    ]

    failures = sum(1 for r in gates if int(r["pass"]) != 1)
    if args.runtime_proof and failures == 0:
        status = "DATADICT_LAYOUT_REGRESSION_SMOKE_GREEN"
    elif failures == 0:
        status = "DATADICT_LAYOUT_REGRESSION_SMOKE_PACKAGE_READY"
    else:
        status = "DATADICT_LAYOUT_REGRESSION_SMOKE_REVIEW"

    next_rows = [
        {"next_id": "RUN_SMOKE", "title": "Run generated smoke in DotTalk++ and capture transcript", "allowed_scope": "runtime proof only"},
        {"next_id": "DD097_CLOSE", "title": "Rerun DD097 with --runtime-proof and --write-closure", "allowed_scope": "report-only closure"},
        {"next_id": "DD096A", "title": "candidate catalog-row design for schema promotion", "allowed_scope": "candidate rows only; no DBF writes"},
        {"next_id": "DD092D", "title": "guarded HELP/CMDHELPCHK apply planning", "allowed_scope": "only after explicit authorization and candidate review"},
    ]

    write_csv(out / "dd097_smoke_command_plan.csv", command_rows, ["order", "command", "purpose"])
    write_csv(out / "dd097_runtime_proof_ledger.csv", runtime_rows, ["proof_key", "needle", "seen"])
    write_csv(out / "dd097_artifact_ledger.csv", artifact_rows, ["role", "path", "exists", "kind", "bytes_or_children", "sha256"])
    write_csv(out / "dd097_gate_ledger.csv", gates, ["gate", "expected", "observed", "pass"])
    write_csv(out / "dd097_no_mutation_boundary_ledger.csv", boundary_rows, ["boundary", "observed", "required", "pass"])
    write_csv(out / "dd097_next_lane_recommendations.csv", next_rows, ["next_id", "title", "allowed_scope"])

    report = f"""# DD097 Data Dictionary Layout Regression Smoke

Run id: `{args.run_id}`
Status: **{status}**
Created UTC: `{utc_now()}`

## Purpose

DD097 creates and optionally closes a repeatable regression smoke for the Data Dictionary baseline.

It proves the accepted layout remains functional:

```text
DBF     dottalkpp/data/datadict
INDEXES dottalkpp/data/indexes/datadict
LMDB    dottalkpp/data/lmdb/datadict
```

## Inputs

- DD096 status: `{dd096.get('status', '')}`
- DD095 status: `{dd095.get('status', '')}`
- DD094 status: `{dd094.get('status', '')}`
- DD093C status: `{dd093c.get('status', '')}`

## Generated smoke files

- DTS smoke: `{smoke_dts}`
- CLI paste smoke: `{smoke_cli}`
- CLI paste smoke with QUIT: `{smoke_cli_quit}`

## Runtime proof

- Runtime proof supplied: **{int(bool(args.runtime_proof))}**
- Runtime needles seen: **{runtime_seen} / {runtime_total if args.runtime_proof else 'not supplied'}**

## Boundary

DD097 is layout-regression-smoke/report-only. It does not edit C++ source, edit build files,
edit command registration, mutate active catalog DBFs, append/replace/delete/pack/zap DBFs,
create/rebuild CDX/LMDB, mutate HELP/META/CMDHELPCHK, regenerate catalog content, or repair manual rows.
"""
    write_text(out / "DD097_DATADICT_LAYOUT_REGRESSION_SMOKE_REPORT.md", report)

    closure_written = 0
    closure_path = repo / args.closure_path
    if args.write_closure:
        write_text(closure_path, report)
        closure_written = 1

    manifest = {
        "contract": "dd097_datadict_layout_regression_smoke_v0",
        "run_id": args.run_id,
        "created_utc": utc_now(),
        "status": status,
        "repo_root": str(repo),
        "profiles": args.profile,
        "dd096_status": dd096.get("status", ""),
        "dd095_status": dd095.get("status", ""),
        "dd094_status": dd094.get("status", ""),
        "dd093c_status": dd093c.get("status", ""),
        "smoke_commands": len(command_rows),
        "runtime_proof_supplied": int(bool(args.runtime_proof)),
        "runtime_needles_seen": runtime_seen,
        "runtime_needles_total": runtime_total,
        "failures": failures,
        "closure_written": closure_written,
        "closure_path": str(closure_path) if closure_written else "",
        "cxx_source_edits": 0,
        "build_file_edits": 0,
        "registry_edits": 0,
        "active_catalog_mutation": 0,
        "dbf_append_replace_delete_pack_zap": 0,
        "cdx_lmdb_create_rebuild": 0,
        "help_meta_cmdhelpchk_mutation": 0,
        "catalog_regeneration": 0,
        "manual_row_repair": 0,
        "next_recommended_action": "Run smoke and rerun DD097 with runtime proof, or proceed to DD096A after smoke green.",
    }
    write_json(out / "dd097_datadict_layout_regression_smoke_manifest.json", manifest)

    print(f"DD097 Data Dictionary layout regression smoke manifest: {out / 'dd097_datadict_layout_regression_smoke_manifest.json'}")
    print(f"status: {status}; commands: {len(command_rows)}; runtime_needles: {runtime_seen}/{runtime_total if args.runtime_proof else 'not supplied'}; failures: {failures}; closure_written: {closure_written}")
    return 2 if (args.fail_on_review and failures) else 0


if __name__ == "__main__":
    raise SystemExit(main())
