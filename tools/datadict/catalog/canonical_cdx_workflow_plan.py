#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import datetime as _dt
import json
import re
from pathlib import Path
from typing import Any, Dict, List


SEARCH_FILES = [
    "src/cli/cmd_index.cpp",
    "src/cli/cmd_create.cpp",
    "src/cli/cmd_buildlmdb.cpp",
    "src/cli/cmd_cdx.cpp",
    "src/cli/cmd_tag.cpp",
    "src/cli/cmd_info.cpp",
    "src/cli/cmd_use.cpp",
    "include/cli/cmd_index.hpp",
    "include/cli/cmd_buildlmdb.hpp",
]


KEY_PATTERNS = [
    "BUILDLMDB",
    "CREATE CDX",
    "CREATE INDEX",
    "INDEX ON",
    "TAG",
    "ADD TAG",
    "INFO",
    "CDX",
    "COMPOUND",
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


def safe_rel(repo: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(repo.resolve()).as_posix()
    except Exception:
        return path.as_posix()


def scan_source_evidence(repo: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    candidates: List[Path] = []
    for rel in SEARCH_FILES:
        p = repo / rel
        if p.exists():
            candidates.append(p)
    for root in [repo / "src", repo / "include", repo / "dottalkpp" / "data" / "help"]:
        if root.exists():
            for p in root.rglob("*"):
                if p.is_file() and p.suffix.lower() in {".cpp", ".hpp", ".h", ".md", ".txt", ".dts"}:
                    name = p.name.lower()
                    if any(k.lower().replace(" ", "") in name.replace("_", "").replace("-", "") for k in ["cdx", "index", "buildlmdb", "tag"]):
                        candidates.append(p)
    # de-dup
    seen = set()
    unique = []
    for p in candidates:
        key = str(p.resolve()).lower()
        if key not in seen:
            seen.add(key)
            unique.append(p)
    for p in unique:
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        lines = text.splitlines()
        for i, line in enumerate(lines, start=1):
            up = line.upper()
            if any(pat in up for pat in KEY_PATTERNS):
                rows.append({
                    "path": safe_rel(repo, p),
                    "line": i,
                    "pattern_hits": ",".join([pat for pat in KEY_PATTERNS if pat in up]),
                    "text": line.strip()[:500],
                })
    return rows[:1000]


def infer_syntax_hints(evidence_rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    text = "\n".join(str(r.get("text", "")) for r in evidence_rows).upper()
    return {
        "has_buildlmdb": int("BUILDLMDB" in text),
        "has_create_cdx_literal": int("CREATE CDX" in text),
        "has_create_index_literal": int("CREATE INDEX" in text),
        "has_index_on_tag_literal": int("INDEX ON" in text and "TAG" in text),
        "has_add_tag_literal": int("ADD TAG" in text),
        "has_info_literal": int("INFO" in text),
    }


def load_tag_plan(dd054_dir: Path) -> List[Dict[str, str]]:
    rows = read_csv_dict(dd054_dir / "dd054_catalog_tag_plan.csv")
    return [r for r in rows if (r.get("status") or "").upper() == "PLAN_READY"]


def build_corrected_manifest_rows(tag_rows: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for r in tag_rows:
        table = (r.get("table") or "").strip().upper()
        expr = (r.get("expr") or "").strip().upper()
        tag = (r.get("tag") or "").strip().upper()
        rows.append({
            "table": table,
            "tag": tag,
            "expr": expr,
            "logical_tag_plan_status": "REUSE_DD054_TAG_PLAN",
            "canonical_step_1": "CREATE_CDX_LAYOUT_CONTAINER",
            "canonical_step_2": "ADD_TAG_TO_CDX",
            "canonical_step_3": "INFO_CDX_LAYOUT",
            "canonical_step_4": "BUILDLMDB_FROM_CDX_LAYOUT",
            "execution_status": "PLAN_ONLY_REQUIRES_SYNTAX_CONFIRMATION",
        })
    return rows


def build_script_template(tag_rows: List[Dict[str, str]], target_slot: str) -> str:
    lines = [
        "* DD-055R canonical CDX/TAG/INFO/BUILDLMDB workflow template",
        "* PLAN ONLY. Do not execute until exact DotTalk++ CDX command syntax is confirmed.",
        "*",
        "* Correct workflow doctrine:",
        "*   1. Create CDX/index container/layout.",
        "*   2. Add tags to that CDX.",
        "*   3. Inspect layout with INFO.",
        "*   4. BUILDLMDB reads CDX layout and creates LMDB indexes.",
        "*",
        f"setpath dbf {target_slot}",
        "",
    ]
    current = None
    for r in tag_rows:
        table = (r.get("table") or "").strip().upper()
        expr = (r.get("expr") or "").strip().upper()
        tag = (r.get("tag") or "").strip().upper()
        if table != current:
            if current is not None:
                lines.extend([
                    "*   INFO <cdx/layout>                  && confirm tags/expressions",
                    "*   BUILDLMDB <table/layout>           && after INFO proof, not in DD-055R",
                    "",
                ])
            lines.extend([
                f"* ---- {table} ----",
                f"use {table.lower()}",
                f"*   CREATE CDX/LAYOUT FOR {table}       && exact command syntax required",
            ])
            current = table
        lines.append(f"*   ADD TAG {tag} ON {expr}             && exact command syntax required")
    if current is not None:
        lines.extend([
            "*   INFO <cdx/layout>                  && confirm tags/expressions",
            "*   BUILDLMDB <table/layout>           && after INFO proof, not in DD-055R",
            "",
        ])
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description="DD-055R corrected canonical CDX layout/tag/info/BUILDLMDB plan")
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--run-id", default="DD055R-canonical-cdx-layout-tag-info-buildlmdb-plan-v0")
    ap.add_argument("--dd054-dir", default="docs/datadict/reports/DD054-catalog-cdx-tag-plan-v0")
    ap.add_argument("--dd055-dir", default="docs/datadict/reports/DD055-guarded-cdx-tag-execution-verify-v0")
    ap.add_argument("--target-slot", default="metadata\\datadict_canonical_rebuild_v0")
    ap.add_argument("--target-path", default="dottalkpp/data/metadata/datadict_canonical_rebuild_v0")
    ap.add_argument("--active-path", default="dottalkpp/data/metadata/datadict")
    ap.add_argument("--profile", action="append", default=[])
    ap.add_argument("--fail-on-review", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    out = Path(args.out_dir).resolve()
    dd054_dir = (repo / args.dd054_dir).resolve()
    dd055_dir = (repo / args.dd055_dir).resolve()
    target_path = (repo / args.target_path).resolve()
    active_path = (repo / args.active_path).resolve()
    out.mkdir(parents=True, exist_ok=True)

    if target_path.resolve() == active_path.resolve():
        raise SystemExit("Refusing active catalog path")

    dd054_manifest = read_json(dd054_dir / "dd054_catalog_cdx_tag_plan_manifest.json")
    dd055_manifest = read_json(dd055_dir / "dd055_guarded_cdx_tag_execution_manifest.json")
    tag_rows = load_tag_plan(dd054_dir)
    evidence_rows = scan_source_evidence(repo)
    syntax_hints = infer_syntax_hints(evidence_rows)
    corrected_rows = build_corrected_manifest_rows(tag_rows)

    # DD-055 v0 is artifact evidence, but it is explicitly reclassified as partial/superseded.
    dd054_green = dd054_manifest.get("status") == "CATALOG_CDX_TAG_PLAN_READY"
    has_tags = len(tag_rows) == int(dd054_manifest.get("tags_ready", len(tag_rows)) or len(tag_rows))
    syntax_review = not (syntax_hints["has_buildlmdb"] and (syntax_hints["has_create_cdx_literal"] or syntax_hints["has_create_index_literal"] or syntax_hints["has_index_on_tag_literal"]))

    failures = 0
    if not dd054_green:
        failures += 1
    if not has_tags:
        failures += 1

    # syntax_review is not a failure; it is the point of DD-055R if exact syntax is not inferable.
    status = "CANONICAL_CDX_WORKFLOW_PLAN_READY_WITH_SYNTAX_REVIEW" if failures == 0 else "CANONICAL_CDX_WORKFLOW_PLAN_BLOCKED"

    gate_rows = [
        {
            "gate": "dd054_logical_tag_plan_ready",
            "expected": "CATALOG_CDX_TAG_PLAN_READY",
            "observed": dd054_manifest.get("status", ""),
            "pass": int(dd054_green),
        },
        {
            "gate": "tag_rows_available",
            "expected": dd054_manifest.get("tags_ready", ""),
            "observed": len(tag_rows),
            "pass": int(has_tags),
        },
        {
            "gate": "dd055_v0_reclassified_partial",
            "expected": "partial/superseded accepted as noncanonical",
            "observed": dd055_manifest.get("status", ""),
            "pass": 1,
        },
        {
            "gate": "buildlmdb_source_or_help_hint_found",
            "expected": 1,
            "observed": syntax_hints["has_buildlmdb"],
            "pass": syntax_hints["has_buildlmdb"],
        },
        {
            "gate": "cdx_create_or_index_syntax_hint_found",
            "expected": 1,
            "observed": int(syntax_hints["has_create_cdx_literal"] or syntax_hints["has_create_index_literal"] or syntax_hints["has_index_on_tag_literal"]),
            "pass": int(syntax_hints["has_create_cdx_literal"] or syntax_hints["has_create_index_literal"] or syntax_hints["has_index_on_tag_literal"]),
        },
    ]

    boundary_rows = [
        {"boundary": "report_only_correction_plan", "observed": 1, "required": 1, "pass": 1},
        {"boundary": "cdx_index_created", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "lmdb_build_executed", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "active_catalog_mutation", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "staging_catalog_mutation", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "source_edits", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "help_meta_cmdhelpchk_mutation", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "promotion_executed", "observed": 0, "required": 0, "pass": 1},
    ]

    write_csv(out / "dd055r_corrected_cdx_workflow_plan.csv", corrected_rows, [
        "table", "tag", "expr", "logical_tag_plan_status", "canonical_step_1",
        "canonical_step_2", "canonical_step_3", "canonical_step_4", "execution_status",
    ])
    write_csv(out / "dd055r_source_help_syntax_evidence.csv", evidence_rows, [
        "path", "line", "pattern_hits", "text",
    ])
    write_csv(out / "dd055r_gate_ledger.csv", gate_rows, ["gate", "expected", "observed", "pass"])
    write_csv(out / "dd055r_no_mutation_boundary_ledger.csv", boundary_rows, ["boundary", "observed", "required", "pass"])
    write_json(out / "dd055r_syntax_hints.json", syntax_hints)

    script = build_script_template(tag_rows, args.target_slot)
    (out / "dd055r_candidate_cdx_layout_tag_info_buildlmdb_template.dts").write_text(script, encoding="utf-8")

    manifest = {
        "contract": "dd055r_canonical_cdx_layout_tag_info_buildlmdb_plan_v0",
        "run_id": args.run_id,
        "created_utc": utc_now(),
        "status": status,
        "repo_root": str(repo),
        "profiles": args.profile,
        "dd054_status": dd054_manifest.get("status", ""),
        "dd055_v0_status": dd055_manifest.get("status", ""),
        "dd055_v0_reclassification": "PARTIAL_ARTIFACT_EVIDENCE_SUPERSEDED_AS_CANONICAL_INDEX_PROOF",
        "tags_planned": len(tag_rows),
        "syntax_hints": syntax_hints,
        "syntax_review_required": int(syntax_review),
        "failures": failures,
        "target_slot": args.target_slot,
        "target_path": str(target_path),
        "cdx_index_created": 0,
        "lmdb_build_executed": 0,
        "active_catalog_mutation": 0,
        "staging_catalog_mutation": 0,
        "source_edits": 0,
        "help_meta_cmdhelpchk_mutation": 0,
        "promotion_executed": 0,
        "next_recommended_action": "DD-056R exact CDX syntax capture/execution only after syntax is confirmed from source/help or user example.",
    }
    write_json(out / "dd055r_canonical_cdx_layout_tag_info_buildlmdb_plan_manifest.json", manifest)

    report = f"""# DD-055R Canonical CDX Layout / TAG / INFO / BUILDLMDB Plan

Run id: `{args.run_id}`
Status: **{status}**
Created UTC: `{manifest['created_utc']}`

## Correction

DD-055 v0 is reclassified as partial artifact evidence and superseded as canonical
index proof. The canonical workflow is:

```text
1. Create CDX/index container/layout.
2. Add tags to that CDX.
3. Inspect layout with INFO.
4. BUILDLMDB reads the CDX layout and creates LMDB indexes.
```

## Inputs

- DD-054 logical tag plan: `{dd054_manifest.get('status', '')}`
- DD-055 v0 status: `{dd055_manifest.get('status', '')}`
- Tags planned: **{len(tag_rows)}**

## Syntax evidence hints

```json
{json.dumps(syntax_hints, indent=2)}
```

## Boundary

DD-055R is report-only. It does not create CDX/indexes, does not run BUILDLMDB,
does not mutate active/staging catalog data, does not edit source, and does not
mutate HELP/META/CMDHELPCHK.

## Next

DD-056R should capture/confirm exact CDX command syntax, then execute the
canonical CDX/TAG/INFO workflow against the staging catalog only.
"""
    (out / "DD055R_CANONICAL_CDX_LAYOUT_TAG_INFO_BUILDLMDB_PLAN.md").write_text(report, encoding="utf-8")

    print(f"DD-055R canonical CDX workflow plan manifest: {out / 'dd055r_canonical_cdx_layout_tag_info_buildlmdb_plan_manifest.json'}")
    print(f"status: {status}; tags: {len(tag_rows)}; failures: {failures}; syntax_review_required: {int(syntax_review)}")
    return 2 if (args.fail_on_review and failures) else 0


if __name__ == "__main__":
    raise SystemExit(main())
