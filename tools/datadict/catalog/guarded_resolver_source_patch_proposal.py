#!/usr/bin/env python3
from __future__ import annotations
import argparse
import csv
import datetime as dt
import json
from pathlib import Path
from typing import Dict, List

REQUIRED = {
    "DD096ZFR": (
        "docs/datadict/reports/DD096ZFR-source-touchpoint-discovery-v0/dd096zfr_source_touchpoint_discovery_manifest.json",
        ["DD096ZFR_SOURCE_TOUCHPOINT_DISCOVERY_READY"],
    ),
    "DD096ZF": (
        "docs/datadict/reports/DD096ZF-ddict-resolver-bridge-source-plan-v0/dd096zf_ddict_resolver_bridge_source_plan_manifest.json",
        ["DD096ZF_DDICT_RESOLVER_BRIDGE_SOURCE_PLAN_READY"],
    ),
}

FOCUSED_PATHS = [
    ("src/cli/cmd_ddict.cpp", "primary DDICT command surface"),
    ("src/datadict/ddict_catalog_paths.cpp", "catalog path/root resolver"),
    ("src/datadict/ddict_object_resolver.cpp", "object lookup/resolution helper"),
    ("src/datadict/ddict_object_resolver.hpp", "object lookup/resolution helper header"),
    ("src/datadict/ddict_runtime_paths.cpp", "possible runtime path resolver"),
    ("src/datadict/ddict_runtime_paths.hpp", "possible runtime path resolver header"),
    ("src/datadict/ddict_catalog_resolver.cpp", "proposed new centralized resolver implementation"),
    ("src/datadict/ddict_catalog_resolver.hpp", "proposed new centralized resolver header"),
]

FAMILIES = [
    ("runs", "DDRUN", "DATA_DICTIONARY_RUNS", "RUN_RECORD_ID"),
    ("objects", "DDOBJECT", "DATA_DICTIONARY_OBJECTS", "CATALOG_OBJECT_ID"),
    ("attributes", "DDATTR", "DATA_DICTIONARY_OBJECT_ATTRIBUTES", "CATALOG_ATTRIBUTE_ID"),
    ("relations", "DDEDGE", "DATA_DICTIONARY_RELATION_EDGES", "RELATION_EDGE_ID"),
    ("evidence", "DDEVID", "DATA_DICTIONARY_EVIDENCE_RECORDS", "EVIDENCE_RECORD_ID"),
    ("gates", "DDGATE", "DATA_DICTIONARY_GATE_RECORDS", "GATE_RECORD_ID"),
]

TERMS = ["DDICT", "DDOBJECT", "DDATTR", "DDEDGE", "DDEVID", "DDGATE", "DDRUN", "DATA_DICTIONARY_OBJECTS", "CATALOG_OBJECT_ID"]

def now():
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")

def read_json(path: Path):
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return {}

def read_text(path: Path) -> str:
    if not path.exists() or not path.is_file():
        return ""
    try:
        if path.stat().st_size > 2_000_000:
            return ""
        return path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return ""

def wt(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")

def wj(path: Path, obj):
    wt(path, json.dumps(obj, indent=2, sort_keys=True) + "\n")

def wc(path: Path, rows: List[Dict], fields: List[str]):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        w.writeheader()
        for row in rows:
            w.writerow({k: row.get(k, "") for k in fields})

def count_terms(text: str) -> Dict[str, int]:
    up = text.upper()
    return {t: up.count(t.upper()) for t in TERMS}

def make_header_skeleton() -> str:
    return """// DD096Z-F2 proposal only: ddict_catalog_resolver.hpp
// Generated as a design artifact; do not install without a guarded apply package.
#pragma once

#include <string>
#include <vector>

namespace dottalk::datadict {

enum class CatalogMode {
    LegacyActive,
    X64Candidate,
    X64Active,
    DualBridge
};

enum class CatalogFamily {
    Runs,
    Objects,
    Attributes,
    Relations,
    Evidence,
    Gates
};

struct CatalogBinding {
    CatalogFamily family;
    CatalogMode mode;
    std::string logical_name;
    std::string legacy_table;
    std::string x64_table;
    std::string physical_table;
    std::string primary_key;
    std::string root_policy;
};

CatalogBinding resolveCatalogFamily(CatalogFamily family, CatalogMode mode);
bool resolveCatalogToken(const std::string& token, CatalogMode mode, CatalogFamily& out_family);
std::vector<CatalogBinding> catalogBindingsForMode(CatalogMode mode);

} // namespace dottalk::datadict
"""

def make_cpp_skeleton() -> str:
    rows = []
    for fam, legacy, x64, key in FAMILIES:
        enum_name = fam[:1].upper() + fam[1:]
        rows.append(f'    // {fam}: {legacy} <-> {x64}, key {key}')
    comment = "\n".join(rows)
    return f"""// DD096Z-F2 proposal only: ddict_catalog_resolver.cpp
// Generated as a design artifact; do not install without a guarded apply package.

#include "ddict_catalog_resolver.hpp"

namespace dottalk::datadict {{

{comment}

CatalogBinding resolveCatalogFamily(CatalogFamily family, CatalogMode mode) {{
    // Proposal: centralize all legacy DD* / x64 DATA_DICTIONARY_* physical table selection here.
    // Existing DDICT subcommands should ask this resolver rather than hard-code DDOBJECT/DDATTR/etc.
    switch (family) {{
    case CatalogFamily::Runs:
        return {{family, mode, "runs", "DDRUN", "DATA_DICTIONARY_RUNS", mode == CatalogMode::LegacyActive ? "DDRUN" : "DATA_DICTIONARY_RUNS", "RUN_RECORD_ID", "datadict"}};
    case CatalogFamily::Objects:
        return {{family, mode, "objects", "DDOBJECT", "DATA_DICTIONARY_OBJECTS", mode == CatalogMode::LegacyActive ? "DDOBJECT" : "DATA_DICTIONARY_OBJECTS", "CATALOG_OBJECT_ID", "datadict"}};
    case CatalogFamily::Attributes:
        return {{family, mode, "attributes", "DDATTR", "DATA_DICTIONARY_OBJECT_ATTRIBUTES", mode == CatalogMode::LegacyActive ? "DDATTR" : "DATA_DICTIONARY_OBJECT_ATTRIBUTES", "CATALOG_ATTRIBUTE_ID", "datadict"}};
    case CatalogFamily::Relations:
        return {{family, mode, "relations", "DDEDGE", "DATA_DICTIONARY_RELATION_EDGES", mode == CatalogMode::LegacyActive ? "DDEDGE" : "DATA_DICTIONARY_RELATION_EDGES", "RELATION_EDGE_ID", "datadict"}};
    case CatalogFamily::Evidence:
        return {{family, mode, "evidence", "DDEVID", "DATA_DICTIONARY_EVIDENCE_RECORDS", mode == CatalogMode::LegacyActive ? "DDEVID" : "DATA_DICTIONARY_EVIDENCE_RECORDS", "EVIDENCE_RECORD_ID", "datadict"}};
    case CatalogFamily::Gates:
        return {{family, mode, "gates", "DDGATE", "DATA_DICTIONARY_GATE_RECORDS", mode == CatalogMode::LegacyActive ? "DDGATE" : "DATA_DICTIONARY_GATE_RECORDS", "GATE_RECORD_ID", "datadict"}};
    }}
    return {{}};
}}

bool resolveCatalogToken(const std::string& token, CatalogMode mode, CatalogFamily& out_family) {{
    // Proposal only. Real implementation should use project string utilities/case folding.
    (void)mode;
    if (token == "DDOBJECT" || token == "DATA_DICTIONARY_OBJECTS") {{ out_family = CatalogFamily::Objects; return true; }}
    if (token == "DDATTR" || token == "DATA_DICTIONARY_OBJECT_ATTRIBUTES") {{ out_family = CatalogFamily::Attributes; return true; }}
    if (token == "DDEDGE" || token == "DATA_DICTIONARY_RELATION_EDGES") {{ out_family = CatalogFamily::Relations; return true; }}
    if (token == "DDEVID" || token == "DATA_DICTIONARY_EVIDENCE_RECORDS") {{ out_family = CatalogFamily::Evidence; return true; }}
    if (token == "DDGATE" || token == "DATA_DICTIONARY_GATE_RECORDS") {{ out_family = CatalogFamily::Gates; return true; }}
    if (token == "DDRUN" || token == "DATA_DICTIONARY_RUNS") {{ out_family = CatalogFamily::Runs; return true; }}
    return false;
}}

std::vector<CatalogBinding> catalogBindingsForMode(CatalogMode mode) {{
    return {{
        resolveCatalogFamily(CatalogFamily::Runs, mode),
        resolveCatalogFamily(CatalogFamily::Objects, mode),
        resolveCatalogFamily(CatalogFamily::Attributes, mode),
        resolveCatalogFamily(CatalogFamily::Relations, mode),
        resolveCatalogFamily(CatalogFamily::Evidence, mode),
        resolveCatalogFamily(CatalogFamily::Gates, mode),
    }};
}}

}} // namespace dottalk::datadict
"""

def main():
    ap = argparse.ArgumentParser(description="DD096Z-F2 guarded resolver source patch proposal")
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--run-id", default="DD096ZF2-guarded-resolver-source-patch-proposal-v0")
    ap.add_argument("--profile", action="append", default=[])
    ap.add_argument("--fail-on-review", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    out = Path(args.out_dir).resolve()
    gen = out / "generated_guarded_resolver_source_patch_proposal"
    gen.mkdir(parents=True, exist_ok=True)

    pre = []
    blockers = 0
    for lane, (rel, expected) in REQUIRED.items():
        path = repo / rel
        data = read_json(path)
        observed = data.get("status", "MISSING")
        passed = int(observed in expected)
        blockers += 0 if passed else 1
        pre.append({"lane": lane, "manifest_path": str(path), "observed_status": observed, "expected_status": "|".join(expected), "pass": passed})
    wc(gen / "dd096zf2_precondition_ledger.csv", pre, ["lane", "manifest_path", "observed_status", "expected_status", "pass"])

    touch_rows = []
    for rel, purpose in FOCUSED_PATHS:
        p = repo / rel
        text = read_text(p)
        counts = count_terms(text)
        touch_rows.append({
            "path": rel,
            "exists": int(p.exists()),
            "purpose": purpose,
            "bytes": p.stat().st_size if p.exists() and p.is_file() else 0,
            **{f"count_{t.lower()}": counts[t] for t in TERMS},
            "source_edits_in_this_package": 0,
        })
    fields = ["path", "exists", "purpose", "bytes"] + [f"count_{t.lower()}" for t in TERMS] + ["source_edits_in_this_package"]
    wc(gen / "dd096zf2_focused_source_touchpoints.csv", touch_rows, fields)

    proposal_rows = [
        {
            "proposed_file": "src/datadict/ddict_catalog_resolver.hpp",
            "action": "add_or_integrate",
            "reason": "central resolver header for catalog family/mode/binding",
            "actual_write_in_this_package": 0,
        },
        {
            "proposed_file": "src/datadict/ddict_catalog_resolver.cpp",
            "action": "add_or_integrate",
            "reason": "central resolver implementation for legacy DD* and x64 DATA_DICTIONARY_* bindings",
            "actual_write_in_this_package": 0,
        },
        {
            "proposed_file": "src/cli/cmd_ddict.cpp",
            "action": "patch_call_sites_later",
            "reason": "replace hard-coded DD* table names with resolver calls in DDICT surfaces",
            "actual_write_in_this_package": 0,
        },
        {
            "proposed_file": "src/datadict/ddict_catalog_paths.cpp",
            "action": "integrate_candidate_mode_later",
            "reason": "root/path policy for legacy_active, x64_candidate, x64_active, dual_bridge",
            "actual_write_in_this_package": 0,
        },
        {
            "proposed_file": "CMake/build registration",
            "action": "review_later",
            "reason": "new resolver .cpp may require build registration depending project layout",
            "actual_write_in_this_package": 0,
        },
    ]
    wc(gen / "dd096zf2_patch_proposal_plan.csv", proposal_rows, ["proposed_file", "action", "reason", "actual_write_in_this_package"])

    wc(gen / "dd096zf2_catalog_family_bindings.csv",
       [{"family": f, "legacy_table": legacy, "x64_table": x64, "primary_key": key, "proposal_only": 1} for f, legacy, x64, key in FAMILIES],
       ["family", "legacy_table", "x64_table", "primary_key", "proposal_only"])

    migration_steps = [
        ("F2-01", "Add resolver types and binding table as isolated source files or integrate into existing datadict helper boundary.", "proposal_only"),
        ("F2-02", "Compile with no DDICT call-site changes.", "future_guarded_apply"),
        ("F2-03", "Patch DDICT TABLES/FIELDS first to use resolver in legacy_active mode.", "future_guarded_apply"),
        ("F2-04", "Add x64_candidate mode command/flag only after legacy_active preserves behavior.", "future_guarded_apply"),
        ("F2-05", "Run DDICT STATUS/TABLES/FIELDS smoke in legacy_active and x64_candidate modes.", "future_guarded_apply"),
        ("F2-06", "Extend REL/EVIDENCE to resolver after TABLES/FIELDS smoke is green.", "future_guarded_apply"),
        ("F2-07", "Keep HELP/CMDHELPCHK external and candidate-only until DDICT runtime is green.", "future_guarded_apply"),
    ]
    wc(gen / "dd096zf2_incremental_patch_sequence.csv",
       [{"step_id": a, "step": b, "status": c} for a,b,c in migration_steps],
       ["step_id", "step", "status"])

    wt(gen / "proposed_source/ddict_catalog_resolver.hpp", make_header_skeleton())
    wt(gen / "proposed_source/ddict_catalog_resolver.cpp", make_cpp_skeleton())

    risks = [
        ("F2-RISK-001", "Adding new source files may require build-system registration.", "First apply package should either integrate into existing compiled file or add guarded build registration."),
        ("F2-RISK-002", "Directly patching all DDICT subcommands could break green legacy behavior.", "Patch TABLES/FIELDS first in legacy_active mode; expand later."),
        ("F2-RISK-003", "Case-folding/string utility mismatch could cause resolver token bugs.", "Use project-native string normalization in real patch, not proposal skeleton helpers."),
        ("F2-RISK-004", "x64_candidate root selection could accidentally touch active roots.", "Resolver binding must report root policy and run in read-only mode first."),
        ("F2-RISK-005", "Generated proposal skeleton namespace may not match actual project namespace.", "Treat skeleton as design artifact, not drop-in source."),
    ]
    wc(gen / "dd096zf2_risk_register.csv",
       [{"risk_id": a, "risk": b, "mitigation": c} for a,b,c in risks],
       ["risk_id", "risk", "mitigation"])

    boundary = [
        ("guarded_source_patch_proposal_only", 1, 1, 1),
        ("source_edits", 0, 0, 1),
        ("build_file_edits", 0, 0, 1),
        ("active_catalog_replacement", 0, 0, 1),
        ("active_catalog_dbf_copy_or_write", 0, 0, 1),
        ("candidate_cdx_lmdb_rebuild", 0, 0, 1),
        ("active_cdx_lmdb_rebuild", 0, 0, 1),
        ("workspace_schema_mutation", 0, 0, 1),
        ("help_meta_cmdhelpchk_mutation", 0, 0, 1),
        ("manual_publication_mutation", 0, 0, 1),
    ]
    wc(out / "dd096zf2_no_mutation_boundary_ledger.csv",
       [{"boundary": a, "observed": b, "required": c, "pass": d} for a,b,c,d in boundary],
       ["boundary", "observed", "required", "pass"])

    existing_focus = sum(1 for r in touch_rows if r["exists"])
    gates = [
        {"gate": "preconditions_green", "expected": 0, "observed": blockers, "pass": int(blockers == 0)},
        {"gate": "focused_existing_paths_found", "expected": ">0", "observed": existing_focus, "pass": int(existing_focus > 0)},
        {"gate": "proposal_source_written_to_reports_only", "expected": 2, "observed": 2, "pass": 1},
        {"gate": "source_edits_performed", "expected": 0, "observed": 0, "pass": 1},
    ]
    failures = sum(1 for row in gates if int(row["pass"]) != 1)
    wc(out / "dd096zf2_gate_ledger.csv", gates, ["gate", "expected", "observed", "pass"])

    status = "DD096ZF2_GUARDED_RESOLVER_SOURCE_PATCH_PROPOSAL_READY" if failures == 0 else "DD096ZF2_GUARDED_RESOLVER_SOURCE_PATCH_PROPOSAL_REVIEW"

    report = f"""# DD096Z-F2 Guarded Resolver Source Patch Proposal

Run id: `{args.run_id}`
Status: **{status}**
Created UTC: `{now()}`

## Purpose

DD096Z-F2 converts the corrected source touchpoint discovery into a guarded source patch proposal.

It does not edit source.

## Summary

- Precondition blockers: **{blockers}**
- Focused existing source paths found: **{existing_focus}**
- Proposal source files written under report directory only: **2**
- Source edits: **0**
- Build file edits: **0**
- Active catalog replacement: **0**

## Recommendation

Do not patch every DDICT surface at once. The first real source apply lane should be small:

1. Add or integrate a central catalog resolver.
2. Compile without call-site behavior changes.
3. Patch `DDICT TABLES` / `DDICT FIELDS` first in legacy-preserving mode.
4. Add x64 candidate mode only after legacy mode is green.
5. Extend `REL` and `EVIDENCE` later.

## Next lane

DD096Z-F3 should be a guarded source apply package only if explicitly authorized. Otherwise use DD096Z-G candidate smoke harness design.
"""
    wt(out / "DD096ZF2_GUARDED_RESOLVER_SOURCE_PATCH_PROPOSAL_REPORT.md", report)

    manifest = {
        "contract": "dd096zf2_guarded_resolver_source_patch_proposal_v0",
        "run_id": args.run_id,
        "created_utc": now(),
        "status": status,
        "repo_root": str(repo),
        "profiles": args.profile,
        "precondition_blockers": blockers,
        "focused_existing_paths_found": existing_focus,
        "source_edits": 0,
        "build_file_edits": 0,
        "active_catalog_replacement": 0,
        "candidate_cdx_lmdb_rebuild": 0,
        "active_cdx_lmdb_rebuild": 0,
        "failures": failures,
        "next_recommended_action": "DD096Z-F3 guarded source apply only if explicitly authorized, or DD096Z-G candidate smoke harness design.",
    }
    wj(out / "dd096zf2_guarded_resolver_source_patch_proposal_manifest.json", manifest)

    print(f"DD096Z-F2 guarded resolver source patch proposal manifest: {out / 'dd096zf2_guarded_resolver_source_patch_proposal_manifest.json'}")
    print(f"status: {status}; precondition_blockers: {blockers}; focused_existing_paths_found: {existing_focus}; source_edits: 0; active_catalog_replacement: 0; failures: {failures}")
    return 2 if (args.fail_on_review and failures) else 0

if __name__ == "__main__":
    raise SystemExit(main())
