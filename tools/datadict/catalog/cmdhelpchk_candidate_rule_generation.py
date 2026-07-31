#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List


EXPECTED_DD092B_STATUS = "DDICT_CMDHELPCHK_EXPECTATION_MAPPING_READY"

DEFAULT_DD092B_MAP = "docs/datadict/reports/DD092B-cmdhelpchk-expectation-mapping-v0/dd092b_cmdhelpchk_expectation_map.csv"
DEFAULT_DD092A_HELP = "docs/datadict/reports/DD092A-ddict-help-topic-candidate-generation-v0/generated_help_candidates/DDICT_HELP_TOPIC_CANDIDATE.md"

PROTECTED_ARTIFACTS = [
    "src/cli/cmd_ddict.cpp",
    "src/cli/cmd_cmdhelpchk.cpp",
    "src/cli/shell_commands.cpp",
    "src/cli/command_registry.cpp",
    "src/CMakeLists.txt",
    "dottalkpp/data/help",
    "dottalkpp/data/datadict",
    "dottalkpp/data/indexes/datadict",
    "dottalkpp/data/lmdb/datadict",
]

CANDIDATE_STATUSES = {
    "candidate_only": "CANDIDATE_ONLY_REVIEW_REQUIRED",
    "not_apply": "DO_NOT_APPLY_IN_DD092C",
}


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


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: List[Dict[str, Any]], fields: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fields})


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


def make_rule_rows(mapping_rows: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for i, row in enumerate(mapping_rows, start=1):
        subsurface = (row.get("subsurface") or "").upper()
        command = (row.get("command") or "DDICT").upper()
        surface = row.get("surface") or f"{command} {subsurface}".strip()
        rule_id = f"DDICT_CMDHELPCHK_{i:02d}_{subsurface or 'ROOT'}"
        out.append({
            "rule_id": rule_id,
            "command": command,
            "subsurface": subsurface,
            "surface": surface,
            "validation_kind": row.get("cmdhelpchk_validation_kind") or "usage_contract_presence",
            "candidate_help_topic": "DDICT",
            "candidate_help_section": subsurface or "ROOT",
            "expectation": row.get("expectation", ""),
            "runtime_proof_required": row.get("required_runtime_proof", ""),
            "candidate_status": CANDIDATE_STATUSES["candidate_only"],
            "apply_now": 0,
            "mutation_now": 0,
        })
    return out


def make_help_candidate_rows(mapping_rows: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    rows = [{
        "candidate_row_id": "DDICT_HELP_TOPIC",
        "row_kind": "topic",
        "topic": "DDICT",
        "parent_topic": "",
        "title": "DDICT",
        "usage": "DDICT HELP | STATUS | TABLES | OBJECTS | FIELDS <table> | TAGS <table> | REL <object> [IN|OUT|BOTH] | EVIDENCE <object>",
        "candidate_status": CANDIDATE_STATUSES["candidate_only"],
        "apply_now": 0,
    }]
    for i, row in enumerate(mapping_rows, start=1):
        subsurface = (row.get("subsurface") or "").upper()
        rows.append({
            "candidate_row_id": f"DDICT_HELP_SECTION_{i:02d}_{subsurface}",
            "row_kind": "section",
            "topic": f"DDICT_{subsurface}",
            "parent_topic": "DDICT",
            "title": row.get("surface", ""),
            "usage": row.get("surface", ""),
            "candidate_status": CANDIDATE_STATUSES["candidate_only"],
            "apply_now": 0,
        })
    return rows


def make_candidate_document(rule_rows: List[Dict[str, Any]], help_rows: List[Dict[str, Any]], created_utc: str, run_id: str) -> str:
    rule_lines = "\n".join(
        f"- `{r['rule_id']}`: `{r['surface']}` — {r['validation_kind']}"
        for r in rule_rows
    )
    help_lines = "\n".join(
        f"- `{r['candidate_row_id']}`: {r['title']}"
        for r in help_rows
    )
    return f"""# DD092C CMDHELPCHK Candidate Rules for DDICT

Run id: `{run_id}`
Created UTC: `{created_utc}`

## Purpose

This document is a review candidate only. It proposes CMDHELPCHK expectation rows/rules for the runtime-proven DDICT command surface.

No HELP DATA, CMDHELPCHK data, source files, command registry files, active catalog DBFs, CDX/LMDB artifacts, generated catalog content, or manual rows are mutated by DD092C.

## Proposed CMDHELPCHK rules

{rule_lines}

## Proposed HELP candidate rows

{help_lines}

## Review notes

- Treat DDICT as one command with sub-surfaces.
- Keep embedded `DDICT HELP` as runtime fallback.
- Candidate rows should not be applied until a later explicitly authorized guarded apply package.
- Runtime path layout is closed by DD093C and may be mentioned in help text, but CMDHELPCHK should validate usage/help coverage rather than runtime storage internals.
"""


def main() -> int:
    ap = argparse.ArgumentParser(description="DD092C CMDHELPCHK candidate row/rule generation")
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--run-id", default="DD092C-cmdhelpchk-candidate-rule-generation-v0")
    ap.add_argument("--dd092b-dir", default="docs/datadict/reports/DD092B-cmdhelpchk-expectation-mapping-v0")
    ap.add_argument("--expectation-map", default=DEFAULT_DD092B_MAP)
    ap.add_argument("--candidate-help", default=DEFAULT_DD092A_HELP)
    ap.add_argument("--profile", action="append", default=[])
    ap.add_argument("--fail-on-review", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    out = Path(args.out_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)

    dd092b_manifest_path = repo / args.dd092b_dir / "dd092b_cmdhelpchk_expectation_mapping_manifest.json"
    dd092b = read_json(dd092b_manifest_path)

    map_path = repo / args.expectation_map
    help_path = repo / args.candidate_help
    mapping_rows = read_csv(map_path)
    rule_rows = make_rule_rows(mapping_rows)
    help_rows = make_help_candidate_rows(mapping_rows)

    generated = out / "generated_cmdhelpchk_candidates"
    generated.mkdir(parents=True, exist_ok=True)

    created_utc = utc_now()
    candidate_doc = make_candidate_document(rule_rows, help_rows, created_utc, args.run_id)
    candidate_doc_path = generated / "DDICT_CMDHELPCHK_CANDIDATE_RULES.md"
    rules_csv_path = generated / "ddict_cmdhelpchk_candidate_rules.csv"
    help_rows_csv_path = generated / "ddict_help_candidate_rows.csv"
    rules_json_path = generated / "ddict_cmdhelpchk_candidate_rules.json"

    write_text(candidate_doc_path, candidate_doc)
    write_csv(rules_csv_path, rule_rows, ["rule_id", "command", "subsurface", "surface", "validation_kind", "candidate_help_topic", "candidate_help_section", "expectation", "runtime_proof_required", "candidate_status", "apply_now", "mutation_now"])
    write_csv(help_rows_csv_path, help_rows, ["candidate_row_id", "row_kind", "topic", "parent_topic", "title", "usage", "candidate_status", "apply_now"])
    write_json(rules_json_path, {"run_id": args.run_id, "created_utc": created_utc, "rules": rule_rows, "help_candidate_rows": help_rows})

    artifact_rows = [
        artifact_row(repo, str(Path(args.dd092b_dir) / "dd092b_cmdhelpchk_expectation_mapping_manifest.json"), "dd092b_manifest"),
        artifact_row(repo, args.expectation_map, "expectation_map"),
        artifact_row(repo, args.candidate_help, "candidate_help_topic"),
    ]
    for p in PROTECTED_ARTIFACTS:
        artifact_rows.append(artifact_row(repo, p, "protected_observed"))

    candidate_artifact_rows = [
        {"role": "candidate_document", "path": str(candidate_doc_path), "exists": int(candidate_doc_path.exists()), "bytes": candidate_doc_path.stat().st_size if candidate_doc_path.exists() else 0, "sha256": sha256(candidate_doc_path)},
        {"role": "candidate_rules_csv", "path": str(rules_csv_path), "exists": int(rules_csv_path.exists()), "bytes": rules_csv_path.stat().st_size if rules_csv_path.exists() else 0, "sha256": sha256(rules_csv_path)},
        {"role": "candidate_help_rows_csv", "path": str(help_rows_csv_path), "exists": int(help_rows_csv_path.exists()), "bytes": help_rows_csv_path.stat().st_size if help_rows_csv_path.exists() else 0, "sha256": sha256(help_rows_csv_path)},
        {"role": "candidate_rules_json", "path": str(rules_json_path), "exists": int(rules_json_path.exists()), "bytes": rules_json_path.stat().st_size if rules_json_path.exists() else 0, "sha256": sha256(rules_json_path)},
    ]

    gap_rows = [
        {
            "gap_id": "C1_APPLY_FORMAT_UNKNOWN",
            "question": "Do these candidate rows match the exact current CMDHELPCHK storage/apply format?",
            "recommended_resolution": "Review generated CSV/JSON against current HELP/CMDHELPCHK schema before any apply lane.",
            "mutation_now": 0,
        },
        {
            "gap_id": "C2_TOPIC_VS_SECTION",
            "question": "Should DDICT sub-surfaces become separate help topics?",
            "recommended_resolution": "Keep as candidate sections under one DDICT topic until existing HELP doctrine says otherwise.",
            "mutation_now": 0,
        },
        {
            "gap_id": "C3_RUNTIME_FALLBACK",
            "question": "Should embedded DDICT HELP be removed once external HELP rows exist?",
            "recommended_resolution": "No. Preserve runtime fallback.",
            "mutation_now": 0,
        },
    ]

    boundary_rows = [
        {"boundary": "candidate_rule_generation_only", "observed": 1, "required": 1, "pass": 1},
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
        {"gate": "dd092b_ready", "expected": EXPECTED_DD092B_STATUS, "observed": dd092b.get("status", ""), "pass": int(dd092b.get("status") == EXPECTED_DD092B_STATUS)},
        {"gate": "expectation_map_exists", "expected": 1, "observed": int(map_path.exists()), "pass": int(map_path.exists())},
        {"gate": "candidate_help_exists", "expected": 1, "observed": int(help_path.exists()), "pass": int(help_path.exists())},
        {"gate": "mapping_rows_8", "expected": 8, "observed": len(mapping_rows), "pass": int(len(mapping_rows) == 8)},
        {"gate": "candidate_rules_8", "expected": 8, "observed": len(rule_rows), "pass": int(len(rule_rows) == 8)},
        {"gate": "help_candidate_rows_9", "expected": 9, "observed": len(help_rows), "pass": int(len(help_rows) == 9)},
        {"gate": "candidate_artifacts_written", "expected": 4, "observed": sum(int(r["exists"]) for r in candidate_artifact_rows), "pass": int(sum(int(r["exists"]) for r in candidate_artifact_rows) == 4)},
        {"gate": "candidate_only_no_apply", "expected": 0, "observed": sum(int(r["apply_now"]) for r in rule_rows) + sum(int(r["apply_now"]) for r in help_rows), "pass": int((sum(int(r["apply_now"]) for r in rule_rows) + sum(int(r["apply_now"]) for r in help_rows)) == 0)},
    ]

    failures = sum(1 for r in gates if int(r["pass"]) != 1)
    status = "DDICT_CMDHELPCHK_CANDIDATE_RULES_GENERATED_REVIEW_READY" if failures == 0 else "DDICT_CMDHELPCHK_CANDIDATE_RULES_GENERATION_REVIEW"

    next_rows = [
        {"next_id": "DD092D", "title": "guarded HELP/CMDHELPCHK apply package", "allowed_scope": "only after explicit authorization and candidate review"},
        {"next_id": "DD094", "title": "Data Dictionary workspace schema savepoint", "allowed_scope": "capture ddbase.dtschema, workspace-load proof, and relation policy"},
        {"next_id": "DD095", "title": "Data Dictionary layout policy documentation", "allowed_scope": "document DBF/INDEXES/LMDB datadict layout and no metadata collision policy"},
    ]

    write_csv(out / "dd092c_candidate_artifacts.csv", candidate_artifact_rows, ["role", "path", "exists", "bytes", "sha256"])
    write_csv(out / "dd092c_input_artifact_inventory.csv", artifact_rows, ["role", "path", "exists", "kind", "bytes_or_children", "sha256"])
    write_csv(out / "dd092c_gap_review.csv", gap_rows, ["gap_id", "question", "recommended_resolution", "mutation_now"])
    write_csv(out / "dd092c_gate_ledger.csv", gates, ["gate", "expected", "observed", "pass"])
    write_csv(out / "dd092c_no_mutation_boundary_ledger.csv", boundary_rows, ["boundary", "observed", "required", "pass"])
    write_csv(out / "dd092c_next_lane_recommendations.csv", next_rows, ["next_id", "title", "allowed_scope"])

    report = f"""# DD092C CMDHELPCHK Candidate Rule Generation

Run id: `{args.run_id}`
Status: **{status}**
Created UTC: `{created_utc}`

## Purpose

DD092C generates review-only candidate CMDHELPCHK rules and HELP candidate rows for the runtime-proven DDICT command surface.

## Inputs

- DD092B manifest: `{dd092b_manifest_path}`
- DD092B status: `{dd092b.get('status', '')}`
- Expectation map: `{map_path}`
- DDICT HELP candidate: `{help_path}`

## Generated candidates

- Candidate rules: **{len(rule_rows)}**
- Candidate HELP rows: **{len(help_rows)}**
- Candidate document: `{candidate_doc_path}`

## Boundary

DD092C is candidate-generation/report-only. It does not edit C++ source, edit build files, edit command registration,
mutate active catalog DBFs, append/replace/delete/pack/zap DBFs, create/rebuild CDX/LMDB,
mutate HELP/META/CMDHELPCHK, regenerate catalog content, or repair manual rows.

## Recommended next lanes

```text
DD092D  guarded HELP/CMDHELPCHK apply package only after explicit authorization
DD094   Data Dictionary workspace schema savepoint
DD095   Data Dictionary layout policy documentation
```
"""
    write_text(out / "DD092C_CMDHELPCHK_CANDIDATE_RULE_GENERATION_REPORT.md", report)

    manifest = {
        "contract": "dd092c_cmdhelpchk_candidate_rule_generation_v0",
        "run_id": args.run_id,
        "created_utc": created_utc,
        "status": status,
        "repo_root": str(repo),
        "profiles": args.profile,
        "dd092b_status": dd092b.get("status", ""),
        "candidate_rules": len(rule_rows),
        "candidate_help_rows": len(help_rows),
        "candidate_artifacts": len(candidate_artifact_rows),
        "failures": failures,
        "apply_now": 0,
        "cxx_source_edits": 0,
        "build_file_edits": 0,
        "registry_edits": 0,
        "active_catalog_mutation": 0,
        "dbf_append_replace_delete_pack_zap": 0,
        "cdx_lmdb_create_rebuild": 0,
        "help_meta_cmdhelpchk_mutation": 0,
        "catalog_regeneration": 0,
        "manual_row_repair": 0,
        "next_recommended_action": "Review DD092C candidates, then either DD094 workspace schema savepoint or explicitly authorize DD092D apply planning.",
    }
    write_json(out / "dd092c_cmdhelpchk_candidate_rule_generation_manifest.json", manifest)

    print(f"DD092C CMDHELPCHK candidate rule generation manifest: {out / 'dd092c_cmdhelpchk_candidate_rule_generation_manifest.json'}")
    print(f"status: {status}; candidate_rules: {len(rule_rows)}; candidate_help_rows: {len(help_rows)}; failures: {failures}")
    return 2 if (args.fail_on_review and failures) else 0


if __name__ == "__main__":
    raise SystemExit(main())
