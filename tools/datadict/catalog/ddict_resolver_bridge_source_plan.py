#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, datetime as dt, json
from pathlib import Path

REQUIRED = [
    ("DD096ZD2ZG", "docs/datadict/reports/DD096ZD2ZG-post-apply-smoke-triage-v0/dd096zd2zg_post_apply_smoke_triage_manifest.json", ["DD096ZD2ZG_POST_APPLY_SMOKE_TRIAGE_CLASSIFIED"]),
]

SOURCE_CANDIDATES = [
    ("src/cli/cmd_ddict.cpp", "primary DDICT command surface"),
    ("src/datadict/ddict_catalog_paths.cpp", "catalog path/root resolver"),
    ("src/datadict/ddict_object_resolver.cpp", "object lookup/resolution helper"),
    ("src/datadict/ddict_object_resolver.hpp", "object lookup/resolution helper header"),
    ("src/datadict/ddict_runtime_paths.cpp", "possible runtime path resolver"),
    ("src/datadict/ddict_runtime_paths.hpp", "possible runtime path resolver header"),
    ("src/datadict/ddict_catalog_resolver.cpp", "proposed centralized resolver implementation"),
    ("src/datadict/ddict_catalog_resolver.hpp", "proposed centralized resolver header"),
    ("CMakeLists.txt", "top-level build registration"),
    ("src/CMakeLists.txt", "source build registration"),
]

ALIASES = [
    ("DDRUN", "DATA_DICTIONARY_RUNS", "run records"),
    ("DDOBJECT", "DATA_DICTIONARY_OBJECTS", "catalog objects"),
    ("DDATTR", "DATA_DICTIONARY_OBJECT_ATTRIBUTES", "object attributes / fields"),
    ("DDEDGE", "DATA_DICTIONARY_RELATION_EDGES", "relation edges"),
    ("DDEVID", "DATA_DICTIONARY_EVIDENCE_RECORDS", "evidence records"),
    ("DDGATE", "DATA_DICTIONARY_GATE_RECORDS", "gate records"),
]

SMOKES = [
    ("DDICT STATUS", "active catalog present and read-only"),
    ("DDICT TABLES", "legacy and/or DATA_DICTIONARY_* families report honestly"),
    ("DDICT FIELDS DATA_DICTIONARY_OBJECTS", "x64 long name resolves to field rows or physical/metadata bridge"),
    ("DDICT FIELDS DDOBJECT", "legacy alias continues to work"),
    ("DDICT TAGS DATA_DICTIONARY_OBJECTS", "physical CDX/LMDB tags or catalog tags report honestly"),
    ("DDICT REL DDICT BOTH", "DDICT root token resolves or smoke target is updated to valid root object"),
    ("DDICT EVIDENCE DDICT", "DDICT root token resolves or smoke target is updated to valid root object"),
]

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
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")

def wt(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")

def wj(path: Path, obj):
    wt(path, json.dumps(obj, indent=2, sort_keys=True) + "\n")

def wc(path: Path, rows, fields):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        w.writeheader()
        for row in rows:
            w.writerow({k: row.get(k, "") for k in fields})

def find_patterns(text: str):
    up = text.upper()
    return {
        "mentions_ddict": int("DDICT" in up),
        "mentions_ddobject": int("DDOBJECT" in up),
        "mentions_ddattr": int("DDATTR" in up),
        "mentions_data_dictionary": int("DATA_DICTIONARY" in up),
        "mentions_fields_surface": int("FIELDS" in up),
        "mentions_tags_surface": int("TAGS" in up),
        "mentions_rel_surface": int("REL" in up),
        "mentions_evidence_surface": int("EVIDENCE" in up),
        "hardcoded_legacy_count": sum(up.count(a) for a, _, _ in ALIASES),
        "new_x64_count": sum(up.count(b) for _, b, _ in ALIASES),
    }

def make_resolver_header() -> str:
    return """#pragma once
// DD096Z-D2ZH draft resolver contract.
// Generated as a proposal only unless explicitly applied in a later package.

#include <string>
#include <vector>

namespace dottalk::datadict {

struct DDictCatalogBinding {
    const char* legacy_name;
    const char* x64_name;
    const char* family;
};

inline const std::vector<DDictCatalogBinding>& ddict_catalog_bindings() {
    static const std::vector<DDictCatalogBinding> kBindings = {
        {"DDRUN",    "DATA_DICTIONARY_RUNS",              "run records"},
        {"DDOBJECT", "DATA_DICTIONARY_OBJECTS",           "catalog objects"},
        {"DDATTR",   "DATA_DICTIONARY_OBJECT_ATTRIBUTES", "object attributes"},
        {"DDEDGE",   "DATA_DICTIONARY_RELATION_EDGES",    "relation edges"},
        {"DDEVID",   "DATA_DICTIONARY_EVIDENCE_RECORDS",  "evidence records"},
        {"DDGATE",   "DATA_DICTIONARY_GATE_RECORDS",      "gate records"},
    };
    return kBindings;
}

std::string ddict_resolve_catalog_surface_name(const std::string& token);
std::string ddict_resolve_legacy_surface_name(const std::string& token);
bool ddict_is_known_catalog_surface(const std::string& token);

} // namespace dottalk::datadict
"""

def make_resolver_cpp() -> str:
    return """// DD096Z-D2ZH draft resolver contract.
// Generated as a proposal only unless explicitly applied in a later package.

#include "ddict_catalog_resolver.hpp"

#include <algorithm>
#include <cctype>

namespace dottalk::datadict {

static std::string upcase_copy(std::string s) {
    std::transform(s.begin(), s.end(), s.begin(), [](unsigned char c) {
        return static_cast<char>(std::toupper(c));
    });
    return s;
}

std::string ddict_resolve_catalog_surface_name(const std::string& token) {
    const std::string u = upcase_copy(token);
    for (const auto& b : ddict_catalog_bindings()) {
        if (u == b.legacy_name || u == b.x64_name) {
            return b.x64_name;
        }
    }
    if (u == "DDICT") {
        return "DATA_DICTIONARY_OBJECTS";
    }
    return token;
}

std::string ddict_resolve_legacy_surface_name(const std::string& token) {
    const std::string u = upcase_copy(token);
    for (const auto& b : ddict_catalog_bindings()) {
        if (u == b.legacy_name || u == b.x64_name) {
            return b.legacy_name;
        }
    }
    if (u == "DDICT") {
        return "DDOBJECT";
    }
    return token;
}

bool ddict_is_known_catalog_surface(const std::string& token) {
    const std::string u = upcase_copy(token);
    if (u == "DDICT") {
        return true;
    }
    for (const auto& b : ddict_catalog_bindings()) {
        if (u == b.legacy_name || u == b.x64_name) {
            return true;
        }
    }
    return false;
}

} // namespace dottalk::datadict
"""

def make_smoke_dts() -> str:
    return "\n".join([
        "* DD096Z-D2ZH DDICT resolver bridge smoke draft",
        "* Read-only smoke after resolver/catalog-reader bridge implementation.",
        "DDICT STATUS",
        "DDICT TABLES",
        "DDICT FIELDS DATA_DICTIONARY_OBJECTS",
        "DDICT FIELDS DDOBJECT",
        "DDICT TAGS DATA_DICTIONARY_OBJECTS",
        "DDICT REL DDICT BOTH",
        "DDICT EVIDENCE DDICT",
        "",
    ])

def main():
    ap = argparse.ArgumentParser(description="DD096Z-D2ZH DDICT resolver bridge source plan")
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--run-id", default="DD096ZD2ZH-ddict-resolver-bridge-source-plan-v0")
    ap.add_argument("--profile", action="append", default=[])
    ap.add_argument("--write-draft-files", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    out = Path(args.out_dir).resolve()
    gen = out / "generated_ddict_resolver_bridge_source_plan"
    gen.mkdir(parents=True, exist_ok=True)

    pre_rows = []
    blockers = 0
    for lane, rel, expected in REQUIRED:
        p = repo / rel
        data = read_json(p)
        observed = data.get("status", "MISSING")
        passed = int(observed in expected)
        blockers += 0 if passed else 1
        pre_rows.append({"lane": lane, "manifest_path": str(p), "observed_status": observed, "expected_status": "|".join(expected), "pass": passed})
    wc(gen / "dd096zd2zh_precondition_ledger.csv", pre_rows, ["lane","manifest_path","observed_status","expected_status","pass"])

    source_rows = []
    for rel, purpose in SOURCE_CANDIDATES:
        p = repo / rel
        text = read_text(p)
        pat = find_patterns(text)
        source_rows.append({
            "path": rel,
            "exists": int(p.exists()),
            "bytes": p.stat().st_size if p.exists() and p.is_file() else 0,
            "purpose": purpose,
            **pat,
        })
    wc(gen / "dd096zd2zh_source_inventory.csv", source_rows, [
        "path","exists","bytes","purpose","mentions_ddict","mentions_ddobject","mentions_ddattr",
        "mentions_data_dictionary","mentions_fields_surface","mentions_tags_surface","mentions_rel_surface",
        "mentions_evidence_surface","hardcoded_legacy_count","new_x64_count"
    ])

    alias_rows = []
    for legacy, x64, family in ALIASES:
        alias_rows.append({
            "legacy_name": legacy,
            "x64_name": x64,
            "family": family,
            "required_behavior": "both names resolve to the same catalog family",
            "compatibility": "legacy name must continue working",
        })
    wc(gen / "dd096zd2zh_alias_bridge_map.csv", alias_rows, ["legacy_name","x64_name","family","required_behavior","compatibility"])

    patch_sequence = [
        {"step_id": "D2ZH-01", "step": "Inventory DDICT source call sites and identify hard-coded DD* names."},
        {"step_id": "D2ZH-02", "step": "Add resolver binding table in isolated datadict source/header or integrate into existing resolver."},
        {"step_id": "D2ZH-03", "step": "Patch FIELDS surface first so DATA_DICTIONARY_OBJECTS resolves while DDOBJECT still works."},
        {"step_id": "D2ZH-04", "step": "Patch TAGS surface to report physical CDX/LMDB tags when catalog tag rows are absent."},
        {"step_id": "D2ZH-05", "step": "Patch REL/EVIDENCE smoke target handling for DDICT root token or choose a valid root object token."},
        {"step_id": "D2ZH-06", "step": "Build and run DDICT bridge smoke in read-only mode."},
        {"step_id": "D2ZH-07", "step": "Only after green bridge smoke, close D2ZF active replacement as green."},
    ]
    wc(gen / "dd096zd2zh_incremental_patch_sequence.csv", patch_sequence, ["step_id","step"])

    smoke_rows = []
    for surface, purpose in SMOKES:
        smoke_rows.append({"surface": surface, "purpose": purpose, "expected_after_bridge": "green_or_honest_physical_report"})
    wc(gen / "dd096zd2zh_bridge_smoke_matrix.csv", smoke_rows, ["surface","purpose","expected_after_bridge"])

    draft_h = make_resolver_header()
    draft_cpp = make_resolver_cpp()
    smoke_dts = make_smoke_dts()
    wt(gen / "ddict_catalog_resolver.hpp.draft", draft_h)
    wt(gen / "ddict_catalog_resolver.cpp.draft", draft_cpp)
    wt(gen / "DD096ZD2ZH_DDICT_RESOLVER_BRIDGE_SMOKE.dts", smoke_dts)

    draft_files_written = 0
    if args.write_draft_files:
        wt(repo / "docs/datadict/drafts/DD096ZD2ZH/ddict_catalog_resolver.hpp.draft", draft_h)
        wt(repo / "docs/datadict/drafts/DD096ZD2ZH/ddict_catalog_resolver.cpp.draft", draft_cpp)
        wt(repo / "dottalkpp/data/scripts/DD096ZD2ZH_DDICT_RESOLVER_BRIDGE_SMOKE.dts", smoke_dts)
        draft_files_written = 1

    source_missing = sum(1 for r in source_rows if r["path"] in ["src/cli/cmd_ddict.cpp", "src/datadict/ddict_catalog_paths.cpp", "src/datadict/ddict_object_resolver.cpp"] and r["exists"] == 0)
    failures = blockers + source_missing

    status = "DD096ZD2ZH_DDICT_RESOLVER_BRIDGE_SOURCE_PLAN_READY" if failures == 0 else "DD096ZD2ZH_DDICT_RESOLVER_BRIDGE_SOURCE_PLAN_REVIEW"

    boundary_rows = [
        {"boundary": "ddict_resolver_bridge_source_plan_only", "observed": 1, "required": 1, "pass": 1},
        {"boundary": "source_edits", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "build_file_edits", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "active_catalog_replacement", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "active_dbf_cdx_lmdb_mutation", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "help_meta_cmdhelpchk_mutation", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "manual_publication_mutation", "observed": 0, "required": 0, "pass": 1},
    ]
    wc(out / "dd096zd2zh_no_mutation_boundary_ledger.csv", boundary_rows, ["boundary","observed","required","pass"])

    report = f"""# DD096Z-D2ZH DDICT Resolver Bridge Source Plan

Run id: `{args.run_id}`
Status: **{status}**
Created UTC: `{now()}`

## Purpose

DD096Z-D2ZH starts the DDICT resolver/catalog-reader bridge lane after D2ZG classified the post-apply smoke.

This package does not edit source. It inventories likely source call sites, defines the legacy-to-x64 alias bridge, stages draft resolver files, and creates the next smoke matrix.

## Summary

- Precondition blockers: **{blockers}**
- Required source files missing: **{source_missing}**
- Draft files written to repo: **{draft_files_written}**
- Source edits: **0**
- Build file edits: **0**
- Active catalog mutation: **0**

## Primary compatibility map

- `DDOBJECT` -> `DATA_DICTIONARY_OBJECTS`
- `DDATTR` -> `DATA_DICTIONARY_OBJECT_ATTRIBUTES`
- `DDEDGE` -> `DATA_DICTIONARY_RELATION_EDGES`
- `DDEVID` -> `DATA_DICTIONARY_EVIDENCE_RECORDS`
- `DDGATE` -> `DATA_DICTIONARY_GATE_RECORDS`
- `DDRUN` -> `DATA_DICTIONARY_RUNS`

## Next safe lane

After review, authorize a guarded source patch package that applies the resolver bridge incrementally, starting with FIELDS and TAGS.
"""
    wt(out / "DD096ZD2ZH_DDICT_RESOLVER_BRIDGE_SOURCE_PLAN_REPORT.md", report)

    manifest = {
        "contract": "dd096zd2zh_ddict_resolver_bridge_source_plan_v0",
        "run_id": args.run_id,
        "created_utc": now(),
        "status": status,
        "repo_root": str(repo),
        "profiles": args.profile,
        "precondition_blockers": blockers,
        "required_source_files_missing": source_missing,
        "draft_files_written": draft_files_written,
        "source_edits": 0,
        "build_file_edits": 0,
        "active_catalog_replacement": 0,
        "failures": failures,
        "next_recommended_action": "Review source inventory and authorize D2ZI guarded resolver source patch if desired.",
    }
    wj(out / "dd096zd2zh_ddict_resolver_bridge_source_plan_manifest.json", manifest)

    print(f"DD096Z-D2ZH DDICT resolver bridge source plan manifest: {out / 'dd096zd2zh_ddict_resolver_bridge_source_plan_manifest.json'}")
    print(f"status: {status}; precondition_blockers: {blockers}; required_source_files_missing: {source_missing}; source_edits: 0; failures: {failures}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
