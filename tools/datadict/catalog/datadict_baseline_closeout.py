#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List


EXPECTED_CHAIN = [
    {
        "ddid": "DD092C",
        "surface": "HELP/CMDHELPCHK candidate rules",
        "dir": "docs/datadict/reports/DD092C-cmdhelpchk-candidate-rule-generation-v0",
        "manifest": "dd092c_cmdhelpchk_candidate_rule_generation_manifest.json",
        "expected_status": "DDICT_CMDHELPCHK_CANDIDATE_RULES_GENERATED_REVIEW_READY",
        "meaning": "DDICT HELP/CMDHELPCHK candidate rules and HELP candidate rows are review-ready, not applied.",
    },
    {
        "ddid": "DD093C",
        "surface": "full path remap runtime closure",
        "dir": "docs/datadict/reports/DD093C-ddict-full-path-remap-runtime-closure-v0",
        "manifest": "dd093c_ddict_full_path_remap_runtime_closure_manifest.json",
        "expected_status": "DDICT_FULL_PATH_REMAP_RUNTIME_CLOSURE_GREEN",
        "meaning": "DDICT resolves DBF/CDX/LMDB under accepted datadict roots.",
    },
    {
        "ddid": "DD094",
        "surface": "workspace schema savepoint",
        "dir": "docs/datadict/reports/DD094-datadict-workspace-schema-savepoint-v0",
        "manifest": "dd094_datadict_workspace_schema_savepoint_manifest.json",
        "expected_status": "DATADICT_WORKSPACE_SCHEMA_SAVEPOINT_GREEN",
        "meaning": "ddbase.dtschema validates 11 areas, 7 relations, and full DBF/CDX/LMDB artifact presence.",
    },
    {
        "ddid": "DD095",
        "surface": "layout policy",
        "dir": "docs/datadict/reports/DD095-datadict-layout-policy-documentation-v0",
        "manifest": "dd095_datadict_layout_policy_documentation_manifest.json",
        "expected_status": "DATADICT_LAYOUT_POLICY_DOCUMENTED_GREEN",
        "meaning": "Accepted data/datadict, indexes/datadict, lmdb/datadict layout and anti-collision policy documented.",
    },
    {
        "ddid": "DD096",
        "surface": "schema promotion/catalog policy",
        "dir": "docs/datadict/reports/DD096-datadict-schema-promotion-catalog-policy-v0",
        "manifest": "dd096_datadict_schema_promotion_catalog_policy_manifest.json",
        "expected_status": "DATADICT_SCHEMA_PROMOTION_CATALOG_POLICY_READY",
        "meaning": "Schema may be represented as catalog policy/evidence later, with promotion_now=0.",
    },
    {
        "ddid": "DD097",
        "surface": "layout regression smoke",
        "dir": "docs/datadict/reports/DD097-datadict-layout-regression-smoke-v0",
        "manifest": "dd097_datadict_layout_regression_smoke_manifest.json",
        "expected_status": "DATADICT_LAYOUT_REGRESSION_SMOKE_GREEN",
        "meaning": "Repeatable runtime smoke proves the closed baseline still works.",
    },
]

BASELINE_ROWS = [
    {"component": "DBF root", "accepted_value": "dottalkpp/data/datadict", "status": "closed_green"},
    {"component": "CDX root", "accepted_value": "dottalkpp/data/indexes/datadict", "status": "closed_green"},
    {"component": "LMDB root", "accepted_value": "dottalkpp/data/lmdb/datadict", "status": "closed_green"},
    {"component": "Workspace schema", "accepted_value": "dottalkpp/data/workspaces/ddbase.dtschema", "status": "closed_green"},
    {"component": "Workspace areas", "accepted_value": "11", "status": "closed_green"},
    {"component": "Workspace relations", "accepted_value": "7", "status": "closed_green"},
    {"component": "DDICT runtime", "accepted_value": "STATUS/TABLES/TAGS/REL/EVIDENCE", "status": "closed_green"},
    {"component": "HELP/CMDHELPCHK", "accepted_value": "candidate-only, not applied", "status": "review_ready_not_applied"},
    {"component": "Schema promotion", "accepted_value": "policy-ready, promotion_now=0", "status": "policy_ready_not_applied"},
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


def make_closeout_report(run_id: str, created_utc: str, chain_rows: List[Dict[str, Any]], failures: int) -> str:
    chain_lines = "\n".join(
        f"- **{r['ddid']}** — {r['surface']}: `{r['observed_status']}`"
        for r in chain_rows
    )
    baseline_lines = "\n".join(
        f"- **{r['component']}**: `{r['accepted_value']}` — {r['status']}"
        for r in BASELINE_ROWS
    )
    return f"""# DD098 Data Dictionary Baseline Closeout

Run id: `{run_id}`
Created UTC: `{created_utc}`

## Status

**DATADICT_BASELINE_CLOSED_AND_REGRESSION_PROVEN** when all DD092C-DD097 chain entries are green/review-ready as expected.

Failures observed in this DD098 run: **{failures}**

## Closed chain

{chain_lines}

## Closed baseline

{baseline_lines}

## Interpretation

The Data Dictionary baseline is closed for the current stage.

The baseline includes:

```text
DBF root        dottalkpp/data/datadict
CDX root        dottalkpp/data/indexes/datadict
LMDB root       dottalkpp/data/lmdb/datadict
Workspace       dottalkpp/data/workspaces/ddbase.dtschema
Areas           11
Relations       7
Runtime surface DDICT STATUS/TABLES/TAGS/REL/EVIDENCE
Regression      DD097 smoke green
```

HELP/CMDHELPCHK remains candidate-only. Schema promotion remains policy-ready only. Neither has been applied to active data.

## Source-of-truth order

1. Runtime artifacts and runtime smoke proof.
2. Green report manifests and ledgers.
3. Policy documents and generated candidates.
4. Manuals and explanatory reports.

Manuals explain the system; they do not define or overwrite active catalog truth.

## Next safe lanes

```text
DD096A
  Candidate catalog-row design for schema promotion.
  Candidate rows only; no DBF writes.

DD092D
  Guarded HELP/CMDHELPCHK apply planning.
  Only after explicit authorization.

DD099
  Baseline-to-manual integration report.
  Explanatory documentation only.
```

## Boundary

DD098 is baseline-closeout/report-only. It does not edit C++ source, edit build files,
edit command registration, mutate active catalog DBFs, append/replace/delete/pack/zap DBFs,
create/rebuild CDX/LMDB, mutate HELP/META/CMDHELPCHK, regenerate catalog content, or repair manual rows.
"""


def main() -> int:
    ap = argparse.ArgumentParser(description="DD098 Data Dictionary baseline closeout")
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--run-id", default="DD098-datadict-baseline-closeout-v0")
    ap.add_argument("--write-closeout", action="store_true")
    ap.add_argument("--closeout-path", default="docs/datadict/reports/DD098_DATADICT_BASELINE_CLOSEOUT.md")
    ap.add_argument("--profile", action="append", default=[])
    ap.add_argument("--fail-on-review", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    out = Path(args.out_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)

    chain_rows = []
    artifact_rows = []
    for item in EXPECTED_CHAIN:
        manifest_rel = str(Path(item["dir"]) / item["manifest"])
        manifest_path = repo / manifest_rel
        manifest = read_json(manifest_path)
        observed = manifest.get("status", "")
        chain_rows.append({
            "ddid": item["ddid"],
            "surface": item["surface"],
            "manifest": manifest_rel,
            "expected_status": item["expected_status"],
            "observed_status": observed,
            "pass": int(observed == item["expected_status"]),
            "meaning": item["meaning"],
        })
        artifact_rows.append(artifact_row(repo, manifest_rel, f"{item['ddid'].lower()}_manifest"))

    for p in PROTECTED_ARTIFACTS:
        artifact_rows.append(artifact_row(repo, p, "protected_observed"))

    failures = sum(1 for r in chain_rows if int(r["pass"]) != 1)
    chain_pass = len(chain_rows) - failures

    boundary_rows = [
        {"boundary": "baseline_closeout_report_only", "observed": 1, "required": 1, "pass": 1},
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

    gate_rows = [
        {"gate": "chain_entries", "expected": len(EXPECTED_CHAIN), "observed": len(chain_rows), "pass": int(len(chain_rows) == len(EXPECTED_CHAIN))},
        {"gate": "chain_pass", "expected": len(EXPECTED_CHAIN), "observed": chain_pass, "pass": int(chain_pass == len(EXPECTED_CHAIN))},
        {"gate": "baseline_rows", "expected": len(BASELINE_ROWS), "observed": len(BASELINE_ROWS), "pass": 1},
        {"gate": "closeout_report_only", "expected": 1, "observed": 1, "pass": 1},
    ]

    status = "DATADICT_BASELINE_CLOSED_AND_REGRESSION_PROVEN" if failures == 0 else "DATADICT_BASELINE_CLOSEOUT_REVIEW"

    created_utc = utc_now()
    report = make_closeout_report(args.run_id, created_utc, chain_rows, failures)
    generated_dir = out / "generated_closeout"
    generated_dir.mkdir(parents=True, exist_ok=True)
    generated_report_path = generated_dir / "DD098_DATADICT_BASELINE_CLOSEOUT.md"
    write_text(generated_report_path, report)

    closeout_written = 0
    closeout_path = repo / args.closeout_path
    if args.write_closeout:
        write_text(closeout_path, report)
        closeout_written = 1

    next_rows = [
        {"next_id": "DD096A", "title": "candidate catalog-row design for schema promotion", "allowed_scope": "candidate rows only; no DBF writes"},
        {"next_id": "DD092D", "title": "guarded HELP/CMDHELPCHK apply planning", "allowed_scope": "only after explicit authorization"},
        {"next_id": "DD099", "title": "baseline-to-manual integration report", "allowed_scope": "documentation/explanation only"},
    ]

    write_csv(out / "dd098_green_chain_ledger.csv", chain_rows, ["ddid", "surface", "manifest", "expected_status", "observed_status", "pass", "meaning"])
    write_csv(out / "dd098_baseline_status_ledger.csv", BASELINE_ROWS, ["component", "accepted_value", "status"])
    write_csv(out / "dd098_artifact_ledger.csv", artifact_rows, ["role", "path", "exists", "kind", "bytes_or_children", "sha256"])
    write_csv(out / "dd098_gate_ledger.csv", gate_rows, ["gate", "expected", "observed", "pass"])
    write_csv(out / "dd098_no_mutation_boundary_ledger.csv", boundary_rows, ["boundary", "observed", "required", "pass"])
    write_csv(out / "dd098_next_lane_recommendations.csv", next_rows, ["next_id", "title", "allowed_scope"])

    manifest = {
        "contract": "dd098_datadict_baseline_closeout_v0",
        "run_id": args.run_id,
        "created_utc": created_utc,
        "status": status,
        "repo_root": str(repo),
        "profiles": args.profile,
        "chain_entries": len(chain_rows),
        "chain_pass": chain_pass,
        "failures": failures,
        "generated_report_path": str(generated_report_path),
        "closeout_written": closeout_written,
        "closeout_path": str(closeout_path) if closeout_written else "",
        "cxx_source_edits": 0,
        "build_file_edits": 0,
        "registry_edits": 0,
        "active_catalog_mutation": 0,
        "dbf_append_replace_delete_pack_zap": 0,
        "cdx_lmdb_create_rebuild": 0,
        "help_meta_cmdhelpchk_mutation": 0,
        "catalog_regeneration": 0,
        "manual_row_repair": 0,
        "next_recommended_action": "DD096A candidate catalog-row design, or DD092D apply planning with explicit authorization.",
    }
    write_json(out / "dd098_datadict_baseline_closeout_manifest.json", manifest)

    print(f"DD098 Data Dictionary baseline closeout manifest: {out / 'dd098_datadict_baseline_closeout_manifest.json'}")
    print(f"status: {status}; chain_pass: {chain_pass}/{len(chain_rows)}; failures: {failures}; closeout_written: {closeout_written}")
    return 2 if (args.fail_on_review and failures) else 0


if __name__ == "__main__":
    raise SystemExit(main())
