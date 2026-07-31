#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import datetime as _dt
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Tuple


EXPECTED_DD064_STATUS = "DDICT_GUARDED_RUNTIME_IMPLEMENTATION_PLAN_READY"

FOCUS_TARGETS = [
    {
        "target_id": "T01_COMMAND_HEADER_PATTERN",
        "role": "Command declaration/header pattern",
        "preferred_path_contains": "include/cli/cmd_",
        "strong_examples": "include/cli/cmd_about.hpp;include/cli/cmd_dbarea.hpp;include/cli/cmd_calc.hpp",
        "future_candidate": "include/cli/cmd_ddict.hpp",
        "implementation_action": "CREATE_NEW_HEADER_AFTER_AUTH",
        "auth_required": 1,
    },
    {
        "target_id": "T02_COMMAND_SOURCE_PATTERN",
        "role": "Command implementation/source pattern",
        "preferred_path_contains": "src/cli/cmd_",
        "strong_examples": "src/cli/cmd_catalogcanary.cpp;src/cli/cmd_about.cpp;src/cli/cmd_dbarea.cpp;src/cli/cmd_area.cpp",
        "future_candidate": "src/cli/cmd_ddict.cpp",
        "implementation_action": "CREATE_NEW_SOURCE_AFTER_AUTH",
        "auth_required": 1,
    },
    {
        "target_id": "T03_COMMAND_REGISTRY_HOOK",
        "role": "Runtime command registry/dispatch hook",
        "preferred_path_contains": "command_registry",
        "strong_examples": "include/cli/command_registry.hpp",
        "future_candidate": "existing command registration site to be patched after exact local verification",
        "implementation_action": "PATCH_EXISTING_REGISTRATION_AFTER_AUTH",
        "auth_required": 1,
    },
    {
        "target_id": "T04_READONLY_DBAREA_SERVICE_PATTERN",
        "role": "Read-only DbArea/service access pattern",
        "preferred_path_contains": "DbArea",
        "strong_examples": "include/workspace/workarea_manager.hpp;include/xindex/dbarea_adapt.hpp;src/cli/cmd_area.cpp;src/cli/cmd_count.cpp",
        "future_candidate": "datadict read-only service/helper inside CLI/runtime layer",
        "implementation_action": "CREATE_OR_REUSE_READONLY_SERVICE_AFTER_AUTH",
        "auth_required": 1,
    },
    {
        "target_id": "T05_INDEXED_READ_PATTERN",
        "role": "Existing index/order/list/read path reference",
        "preferred_path_contains": "cmd_set;cmd_list;cmd_count;cmd_use",
        "strong_examples": "include/dli/cmd_set.hpp;src/cli/cmd_buildlmdb.cpp;src/cli/cmd_area.cpp",
        "future_candidate": "DDICT service uses existing active CDX/LMDB read path; no rebuild",
        "implementation_action": "REFERENCE_ONLY_IN_DD064R",
        "auth_required": 0,
    },
    {
        "target_id": "T06_USAGE_TEXT_PATTERN",
        "role": "Usage text / command self-help pattern",
        "preferred_path_contains": "usage;help",
        "strong_examples": "src/cli/cmd_about.cpp;src/cli/cmd_aggs.cpp;src/cli/cmd_calc.cpp",
        "future_candidate": "DDICT usage text generated from DD-063R contract, not HELP DATA mutation",
        "implementation_action": "STAGE_USAGE_TEXT_AFTER_AUTH",
        "auth_required": 1,
    },
    {
        "target_id": "T07_TEST_SCRIPT_PATTERN",
        "role": "Runtime smoke/test path",
        "preferred_path_contains": "tests;scripts;data/tests",
        "strong_examples": "dottalkpp/data/tests or docs/datadict reports as discovered locally",
        "future_candidate": "dd065_ddict_runtime_smoke.dts",
        "implementation_action": "CREATE_TEST_SCRIPT_AFTER_AUTH",
        "auth_required": 1,
    },
]

IMPLEMENTATION_SLICES = [
    {
        "slice_id": "S1_MINIMAL_USAGE_ONLY",
        "commands": "DDICT HELP",
        "purpose": "Add command shell and usage output only.",
        "risk": "LOW",
        "requires_active_catalog": 0,
        "auth_required": 1,
    },
    {
        "slice_id": "S2_STATUS_TABLES",
        "commands": "DDICT STATUS;DDICT TABLES",
        "purpose": "Prove active catalog open/read/count path.",
        "risk": "MEDIUM",
        "requires_active_catalog": 1,
        "auth_required": 1,
    },
    {
        "slice_id": "S3_FIELDS_TAGS",
        "commands": "DDICT FIELDS;DDICT TAGS",
        "purpose": "Prove relationship/attribute traversal over active catalog.",
        "risk": "MEDIUM",
        "requires_active_catalog": 1,
        "auth_required": 1,
    },
    {
        "slice_id": "S4_REL_EVIDENCE_OBJECTS",
        "commands": "DDICT OBJECTS;DDICT REL;DDICT EVIDENCE",
        "purpose": "Broader graph/evidence surfaces after core proof.",
        "risk": "MEDIUM_HIGH",
        "requires_active_catalog": 1,
        "auth_required": 1,
    },
]

ACCEPTED_IMPLEMENTATION_RULES = [
    {
        "rule_id": "R01_READ_ONLY",
        "rule": "DDICT implementation must be read-only and must not expose mutation verbs.",
    },
    {
        "rule_id": "R02_NO_REBUILD",
        "rule": "DDICT must not CREATE DBF, IMPORT, CDX CREATE, CDX ADDTAG, or BUILDLMDB.",
    },
    {
        "rule_id": "R03_ACTIVE_CATALOG_ONLY",
        "rule": "DDICT reads the active metadata/datadict catalog, not staging/sandbox paths by default.",
    },
    {
        "rule_id": "R04_ENGINE_SAFE",
        "rule": "DDICT must not depend on LabTalk/student artifacts; it belongs to engine/runtime metadata capabilities.",
    },
    {
        "rule_id": "R05_HELP_SEPARATE",
        "rule": "DDICT usage text may be staged, but HELP/META/CMDHELPCHK mutation is a later explicit package.",
    },
    {
        "rule_id": "R06_TEST_FIRST",
        "rule": "DD-065 must include runtime smoke commands and no-mutation boundary evidence.",
    },
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


def read_csv_dict(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8", errors="replace") as f:
        return list(csv.DictReader(f))


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


def safe_rel(repo: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(repo.resolve()).as_posix()
    except Exception:
        return path.as_posix()


def score_row(row: Dict[str, str]) -> Tuple[int, str]:
    path = (row.get("path") or "").lower()
    hits = (row.get("hits") or "").lower()
    text = (row.get("text") or "").lower()
    score = 0
    reasons: List[str] = []

    if "include/cli/command_registry" in path:
        score += 100
        reasons.append("command_registry_header")
    if "command_registry" in path or "command_dispatch" in hits:
        score += 40
        reasons.append("dispatch")
    if "/cmd_" in path or "\\cmd_" in path or path.endswith(".cpp") and "cmd_" in path:
        score += 35
        reasons.append("cmd_pattern")
    if "cmd_catalogcanary" in path or "metadata" in path or "datadict" in path or "data_dictionary" in hits:
        score += 60
        reasons.append("metadata_precedent")
    if "help_surface" in hits or "usage" in text:
        score += 20
        reasons.append("usage_pattern")
    if "dbarea_read" in hits or "dbarea" in text:
        score += 25
        reasons.append("dbarea_read")
    if "set_index_order" in hits or "set order" in text or "set index" in text:
        score += 20
        reasons.append("index_order")
    if "list_count" in hits or "count" in text or "list" in text:
        score += 12
        reasons.append("list_count")
    if "append" in path or "replace" in path or "delete" in path or "buildlmdb" in path:
        score -= 15
        reasons.append("mutation_or_rebuild_caution")
    return score, ",".join(reasons)


def focus_scan_rows(rows: List[Dict[str, str]], limit: int = 80) -> List[Dict[str, Any]]:
    scored: List[Dict[str, Any]] = []
    seen = set()
    for row in rows:
        score, reasons = score_row(row)
        key = (row.get("path", ""), row.get("line", ""))
        if key in seen:
            continue
        seen.add(key)
        if score <= 0:
            continue
        scored.append({
            "path": row.get("path", ""),
            "line": row.get("line", ""),
            "hits": row.get("hits", ""),
            "score": score,
            "reasons": reasons,
            "implementation_relevance": row.get("implementation_relevance", ""),
            "text": row.get("text", ""),
        })
    scored.sort(key=lambda r: (-int(r["score"]), r["path"], int(r["line"]) if str(r["line"]).isdigit() else 0))
    return scored[:limit]


def summarize_by_file(rows: List[Dict[str, Any]], limit: int = 25) -> List[Dict[str, Any]]:
    by_file: Dict[str, Dict[str, Any]] = {}
    for row in rows:
        path = row["path"]
        entry = by_file.setdefault(path, {
            "path": path,
            "hit_rows": 0,
            "max_score": 0,
            "score_total": 0,
            "reasons": set(),
            "recommended_use": "",
        })
        entry["hit_rows"] += 1
        entry["max_score"] = max(entry["max_score"], int(row["score"]))
        entry["score_total"] += int(row["score"])
        for reason in str(row.get("reasons", "")).split(","):
            if reason:
                entry["reasons"].add(reason)

    out: List[Dict[str, Any]] = []
    for path, entry in by_file.items():
        reasons = ",".join(sorted(entry["reasons"]))
        recommended_use = classify_file_use(path, reasons)
        out.append({
            "path": path,
            "hit_rows": entry["hit_rows"],
            "max_score": entry["max_score"],
            "score_total": entry["score_total"],
            "reasons": reasons,
            "recommended_use": recommended_use,
        })
    out.sort(key=lambda r: (-int(r["score_total"]), -int(r["max_score"]), r["path"]))
    return out[:limit]


def classify_file_use(path: str, reasons: str) -> str:
    p = path.lower()
    if "command_registry" in p:
        return "PRIMARY_DISPATCH_REGISTRY_REVIEW"
    if "cmd_catalogcanary" in p:
        return "PRIMARY_METADATA_COMMAND_PRECEDENT_REVIEW"
    if "cmd_about" in p or "cmd_aggs" in p or "cmd_calc" in p:
        return "USAGE_AND_COMMAND_STYLE_PRECEDENT"
    if "cmd_area" in p or "cmd_count" in p or "cmd_list" in p or "cmd_browser" in p:
        return "READ_OUTPUT_PRECEDENT"
    if "cmd_buildlmdb" in p or "cmd_append" in p or "cmd_replace" in p:
        return "NEGATIVE_BOUNDARY_REFERENCE_MUTATION_AVOID"
    if "workarea" in p or "dbarea" in p:
        return "DBAREA_ACCESS_PRECEDENT"
    return "CONTEXT_REVIEW"


def acceptance_markdown(run_id: str, status: str, summary_rows: List[Dict[str, Any]]) -> str:
    top = "\n".join(f"- `{r['path']}` — {r['recommended_use']}" for r in summary_rows[:12])
    return f"""# DD-064R DDICT Runtime Hook Triage / Implementation Readiness

Run id: `{run_id}`
Created UTC: `{utc_now()}`
Status: **{status}**

## Purpose

DD-064R reduces the broad DD-064 source-hook scan into a focused implementation
readiness map for a later guarded DDICT implementation package.

## Accepted focus

{top}

## Implementation rule

DD-064R is still report-only. It does not edit C++ source, create source files,
register runtime commands, mutate the active catalog, mutate DBF/CDX/LMDB
artifacts, or mutate HELP/META/CMDHELPCHK.

## Next

DD-065 may implement only after explicit authorization.
"""


def main() -> int:
    ap = argparse.ArgumentParser(description="DD-064R focused DDICT runtime hook triage / implementation readiness")
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--run-id", default="DD064R-ddict-runtime-hook-triage-readiness-v0")
    ap.add_argument("--dd064-dir", default="docs/datadict/reports/DD064-guarded-ddict-runtime-implementation-plan-v0")
    ap.add_argument("--dd064-scan-dir", default="docs/datadict/reports/DD064-guarded-ddict-runtime-implementation-plan-scan-v0")
    ap.add_argument("--write-readiness", action="store_true")
    ap.add_argument("--readiness-path", default="docs/datadict/runlog/DD-064R_DDICT_RUNTIME_HOOK_TRIAGE_READINESS.md")
    ap.add_argument("--profile", action="append", default=[])
    ap.add_argument("--fail-on-review", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    out = Path(args.out_dir).resolve()
    dd064_dir = (repo / args.dd064_dir).resolve()
    dd064_scan_dir = (repo / args.dd064_scan_dir).resolve()
    readiness_path = (repo / args.readiness_path).resolve()
    out.mkdir(parents=True, exist_ok=True)

    dd064_manifest = read_json(dd064_dir / "dd064_guarded_ddict_runtime_implementation_plan_manifest.json")
    dd064_scan_manifest = read_json(dd064_scan_dir / "dd064_guarded_ddict_runtime_implementation_plan_manifest.json")
    component_rows = read_csv_dict(dd064_dir / "dd064_component_plan.csv")
    service_rows = read_csv_dict(dd064_dir / "dd064_readonly_service_contract.csv")
    test_rows = read_csv_dict(dd064_dir / "dd064_runtime_test_plan.csv")
    scan_rows = read_csv_dict(dd064_scan_dir / "dd064_source_hook_inventory.csv")

    dd064_ready = dd064_manifest.get("status") == EXPECTED_DD064_STATUS
    dd064_scan_ready = dd064_scan_manifest.get("status") == EXPECTED_DD064_STATUS
    focused_rows = focus_scan_rows(scan_rows)
    file_summary_rows = summarize_by_file(focused_rows)

    # Hard readiness: DD064 green, scan green, focused files include at least dispatch and command-style precedent.
    summary_uses = {r["recommended_use"] for r in file_summary_rows}
    has_dispatch = any("DISPATCH" in u for u in summary_uses)
    has_command_precedent = any("COMMAND" in u or "USAGE" in u for u in summary_uses)
    has_read_precedent = any("READ" in u or "DBAREA" in u for u in summary_uses)

    readiness_written = 0
    failures = 0
    review_rows: List[Dict[str, Any]] = []

    if not dd064_ready:
        failures += 1
        review_rows.append({"issue": "DD064_PLAN_NOT_READY", "detail": dd064_manifest.get("status", "")})
    if not dd064_scan_ready:
        failures += 1
        review_rows.append({"issue": "DD064_SCAN_NOT_READY", "detail": dd064_scan_manifest.get("status", "")})
    if not focused_rows:
        failures += 1
        review_rows.append({"issue": "NO_FOCUSED_SOURCE_ROWS", "detail": "DD064 source scan did not yield focused rows"})
    if not has_dispatch:
        failures += 1
        review_rows.append({"issue": "NO_DISPATCH_CANDIDATE", "detail": "Focused rows did not include command registry/dispatch candidate"})
    if not has_command_precedent:
        failures += 1
        review_rows.append({"issue": "NO_COMMAND_PRECEDENT", "detail": "Focused rows did not include command style/usage precedent"})
    if not has_read_precedent:
        failures += 1
        review_rows.append({"issue": "NO_READ_PRECEDENT", "detail": "Focused rows did not include read/DbArea precedent"})

    status = "DDICT_RUNTIME_HOOK_TRIAGE_READINESS_GREEN" if failures == 0 else "DDICT_RUNTIME_HOOK_TRIAGE_READINESS_REVIEW"

    if args.write_readiness:
        readiness_path.parent.mkdir(parents=True, exist_ok=True)
        readiness_path.write_text(acceptance_markdown(args.run_id, status, file_summary_rows), encoding="utf-8")
        readiness_written = 1

    gate_rows = [
        {
            "gate": "dd064_plan_ready",
            "expected": EXPECTED_DD064_STATUS,
            "observed": dd064_manifest.get("status", ""),
            "pass": int(dd064_ready),
        },
        {
            "gate": "dd064_scan_ready",
            "expected": EXPECTED_DD064_STATUS,
            "observed": dd064_scan_manifest.get("status", ""),
            "pass": int(dd064_scan_ready),
        },
        {
            "gate": "focused_source_rows_present",
            "expected": ">=1",
            "observed": len(focused_rows),
            "pass": int(len(focused_rows) >= 1),
        },
        {
            "gate": "dispatch_candidate_present",
            "expected": 1,
            "observed": int(has_dispatch),
            "pass": int(has_dispatch),
        },
        {
            "gate": "command_precedent_present",
            "expected": 1,
            "observed": int(has_command_precedent),
            "pass": int(has_command_precedent),
        },
        {
            "gate": "read_dbarea_precedent_present",
            "expected": 1,
            "observed": int(has_read_precedent),
            "pass": int(has_read_precedent),
        },
        {
            "gate": "readiness_written_when_requested",
            "expected": int(args.write_readiness),
            "observed": readiness_written,
            "pass": int((not args.write_readiness) or readiness_written == 1),
        },
    ]

    boundary_rows = [
        {"boundary": "runtime_hook_triage_report_only", "observed": 1, "required": 1, "pass": 1},
        {"boundary": "cxx_source_edits", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "new_source_files_created", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "runtime_command_registration", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "active_catalog_mutation", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "dbf_append_replace_delete_pack_zap", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "cdx_lmdb_create_rebuild", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "help_meta_cmdhelpchk_mutation", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "catalog_regeneration", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "manual_row_repair", "observed": 0, "required": 0, "pass": 1},
    ]

    write_csv(out / "dd064r_focus_target_plan.csv", FOCUS_TARGETS, [
        "target_id", "role", "preferred_path_contains", "strong_examples",
        "future_candidate", "implementation_action", "auth_required",
    ])
    write_csv(out / "dd064r_focused_source_hook_rows.csv", focused_rows, [
        "path", "line", "hits", "score", "reasons", "implementation_relevance", "text",
    ])
    write_csv(out / "dd064r_focused_file_summary.csv", file_summary_rows, [
        "path", "hit_rows", "max_score", "score_total", "reasons", "recommended_use",
    ])
    write_csv(out / "dd064r_implementation_slice_plan.csv", IMPLEMENTATION_SLICES, [
        "slice_id", "commands", "purpose", "risk", "requires_active_catalog", "auth_required",
    ])
    write_csv(out / "dd064r_accepted_implementation_rules.csv", ACCEPTED_IMPLEMENTATION_RULES, [
        "rule_id", "rule",
    ])
    write_csv(out / "dd064r_gate_ledger.csv", gate_rows, ["gate", "expected", "observed", "pass"])
    write_csv(out / "dd064r_review_rows.csv", review_rows, ["issue", "detail"])
    write_csv(out / "dd064r_no_mutation_boundary_ledger.csv", boundary_rows, ["boundary", "observed", "required", "pass"])

    report = f"""# DD-064R DDICT Runtime Hook Triage / Implementation Readiness

Run id: `{args.run_id}`
Status: **{status}**
Created UTC: `{utc_now()}`

## Purpose

DD-064R reduces DD-064's broad source scan into a focused implementation
readiness map for a later guarded `DDICT` implementation package.

## Inputs

- DD-064 plan status: `{dd064_manifest.get('status', '')}`
- DD-064 scan status: `{dd064_scan_manifest.get('status', '')}`
- DD-064 scan rows: **{len(scan_rows)}**

## Focused output

- Focused source rows: **{len(focused_rows)}**
- Focused file summaries: **{len(file_summary_rows)}**
- Focus targets: **{len(FOCUS_TARGETS)}**
- Implementation slices: **{len(IMPLEMENTATION_SLICES)}**

## Readiness classification

```text
Dispatch candidate present: {int(has_dispatch)}
Command precedent present: {int(has_command_precedent)}
Read/DbArea precedent present: {int(has_read_precedent)}
```

## Boundary

DD-064R is report-only. It does not edit C++ source, create source files,
register runtime commands, mutate the active catalog, append/replace/delete/pack/zap,
rebuild CDX/LMDB, mutate HELP/META/CMDHELPCHK, regenerate catalog content, or repair rows.

## Next

DD-065 may implement only after explicit authorization.
"""
    (out / "DD064R_DDICT_RUNTIME_HOOK_TRIAGE_READINESS_REPORT.md").write_text(report, encoding="utf-8")
    (out / "DD064R_DDICT_RUNTIME_HOOK_TRIAGE_READINESS.md").write_text(acceptance_markdown(args.run_id, status, file_summary_rows), encoding="utf-8")

    manifest = {
        "contract": "dd064r_ddict_runtime_hook_triage_readiness_v0",
        "run_id": args.run_id,
        "created_utc": utc_now(),
        "status": status,
        "repo_root": str(repo),
        "profiles": args.profile,
        "dd064_status": dd064_manifest.get("status", ""),
        "dd064_scan_status": dd064_scan_manifest.get("status", ""),
        "scan_rows": len(scan_rows),
        "focused_source_rows": len(focused_rows),
        "focused_file_summaries": len(file_summary_rows),
        "focus_targets": len(FOCUS_TARGETS),
        "implementation_slices": len(IMPLEMENTATION_SLICES),
        "dispatch_candidate_present": int(has_dispatch),
        "command_precedent_present": int(has_command_precedent),
        "read_dbarea_precedent_present": int(has_read_precedent),
        "readiness_written": readiness_written,
        "readiness_path": str(readiness_path) if readiness_written else "",
        "failures": failures,
        "cxx_source_edits": 0,
        "new_source_files_created": 0,
        "runtime_command_registration": 0,
        "active_catalog_mutation": 0,
        "dbf_append_replace_delete_pack_zap": 0,
        "cdx_lmdb_create_rebuild": 0,
        "help_meta_cmdhelpchk_mutation": 0,
        "catalog_regeneration": 0,
        "manual_row_repair": 0,
        "next_recommended_action": "DD-065 guarded DDICT runtime implementation only after explicit authorization.",
    }
    write_json(out / "dd064r_ddict_runtime_hook_triage_readiness_manifest.json", manifest)

    print(f"DD-064R DDICT runtime hook triage manifest: {out / 'dd064r_ddict_runtime_hook_triage_readiness_manifest.json'}")
    print(f"status: {status}; focused_rows: {len(focused_rows)}; files: {len(file_summary_rows)}; failures: {failures}; readiness_written: {readiness_written}")
    return 2 if (args.fail_on_review and failures) else 0


if __name__ == "__main__":
    raise SystemExit(main())
