#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, datetime as dt, json, shutil
from pathlib import Path

REQUIRED = [
    ("DD096ZD2ZH", "docs/datadict/reports/DD096ZD2ZH-ddict-resolver-bridge-source-plan-v0/dd096zd2zh_ddict_resolver_bridge_source_plan_manifest.json", ["DD096ZD2ZH_DDICT_RESOLVER_BRIDGE_SOURCE_PLAN_READY"]),
]

ALIASES = [
    ("DDRUN", "DATA_DICTIONARY_RUNS", "run records"),
    ("DDOBJECT", "DATA_DICTIONARY_OBJECTS", "catalog objects"),
    ("DDATTR", "DATA_DICTIONARY_OBJECT_ATTRIBUTES", "object attributes / fields"),
    ("DDEDGE", "DATA_DICTIONARY_RELATION_EDGES", "relation edges"),
    ("DDEVID", "DATA_DICTIONARY_EVIDENCE_RECORDS", "evidence records"),
    ("DDGATE", "DATA_DICTIONARY_GATE_RECORDS", "gate records"),
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

def resolver_hpp() -> str:
    return """#pragma once
// DD096Z-D2ZI guarded resolver source patch.
// Compatibility bridge for legacy compact DD* names and x64 DATA_DICTIONARY_* names.

#include <string>
#include <vector>

namespace dottalk::datadict {

struct DDictCatalogBinding {
    const char* legacy_name;
    const char* x64_name;
    const char* family;
};

const std::vector<DDictCatalogBinding>& ddict_catalog_bindings();

std::string ddict_resolve_to_x64_catalog_name(const std::string& token);
std::string ddict_resolve_to_legacy_catalog_name(const std::string& token);
bool ddict_is_known_catalog_name(const std::string& token);

} // namespace dottalk::datadict
"""

def resolver_cpp() -> str:
    return """// DD096Z-D2ZI guarded resolver source patch.
// Compatibility bridge for legacy compact DD* names and x64 DATA_DICTIONARY_* names.

#include "ddict_catalog_resolver.hpp"

#include <algorithm>
#include <cctype>

namespace dottalk::datadict {

namespace {
std::string upper_copy(std::string s) {
    std::transform(s.begin(), s.end(), s.begin(), [](unsigned char c) {
        return static_cast<char>(std::toupper(c));
    });
    return s;
}
}

const std::vector<DDictCatalogBinding>& ddict_catalog_bindings() {
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

std::string ddict_resolve_to_x64_catalog_name(const std::string& token) {
    const std::string u = upper_copy(token);
    if (u == "DDICT") {
        return "DATA_DICTIONARY_OBJECTS";
    }
    for (const auto& b : ddict_catalog_bindings()) {
        if (u == b.legacy_name || u == b.x64_name) {
            return b.x64_name;
        }
    }
    return token;
}

std::string ddict_resolve_to_legacy_catalog_name(const std::string& token) {
    const std::string u = upper_copy(token);
    if (u == "DDICT") {
        return "DDOBJECT";
    }
    for (const auto& b : ddict_catalog_bindings()) {
        if (u == b.legacy_name || u == b.x64_name) {
            return b.legacy_name;
        }
    }
    return token;
}

bool ddict_is_known_catalog_name(const std::string& token) {
    const std::string u = upper_copy(token);
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

def smoke_dts() -> str:
    return "\n".join([
        "* DD096Z-D2ZI resolver source patch smoke draft",
        "* Read-only DDICT bridge smoke.",
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
    ap = argparse.ArgumentParser(description="DD096Z-D2ZI guarded resolver source patch")
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--run-id", default="DD096ZD2ZI-guarded-resolver-source-patch-v0")
    ap.add_argument("--profile", action="append", default=[])
    ap.add_argument("--apply-source-patch", action="store_true")
    ap.add_argument("--write-smoke-script", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    out = Path(args.out_dir).resolve()
    gen = out / "generated_guarded_resolver_source_patch"
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
    wc(gen / "dd096zd2zi_precondition_ledger.csv", pre_rows, ["lane","manifest_path","observed_status","expected_status","pass"])

    target_h = repo / "src/datadict/ddict_catalog_resolver.hpp"
    target_cpp = repo / "src/datadict/ddict_catalog_resolver.cpp"
    backup_root = repo / f"docs/datadict/backups/DD096ZD2ZI-source-backup-{dt.datetime.now().strftime('%Y%m%d_%H%M%S')}"
    smoke_path = repo / "dottalkpp/data/scripts/DD096ZD2ZI_DDICT_RESOLVER_BRIDGE_SMOKE.dts"

    h_text = resolver_hpp()
    cpp_text = resolver_cpp()
    smoke_text = smoke_dts()

    wt(gen / "ddict_catalog_resolver.hpp", h_text)
    wt(gen / "ddict_catalog_resolver.cpp", cpp_text)
    wt(gen / "DD096ZD2ZI_DDICT_RESOLVER_BRIDGE_SMOKE.dts", smoke_text)

    alias_rows = [{"legacy_name": a, "x64_name": b, "family": c} for a, b, c in ALIASES]
    wc(gen / "dd096zd2zi_alias_bridge_map.csv", alias_rows, ["legacy_name","x64_name","family"])

    callsite_rows = []
    for rel in ["src/cli/cmd_ddict.cpp", "src/datadict/ddict_catalog_paths.cpp", "src/datadict/ddict_object_resolver.cpp"]:
        p = repo / rel
        text = read_text(p)
        upper = text.upper()
        callsite_rows.append({
            "path": rel,
            "exists": int(p.exists()),
            "bytes": p.stat().st_size if p.exists() and p.is_file() else 0,
            "legacy_token_mentions": sum(upper.count(a) for a, _, _ in ALIASES),
            "x64_token_mentions": sum(upper.count(b) for _, b, _ in ALIASES),
            "patch_status": "inspect_for_callsite_integration_next",
        })
    wc(gen / "dd096zd2zi_callsite_inventory.csv", callsite_rows, ["path","exists","bytes","legacy_token_mentions","x64_token_mentions","patch_status"])

    source_files_written = 0
    backups_written = 0
    if args.apply_source_patch:
        if blockers:
            raise SystemExit("Precondition blockers present; refusing --apply-source-patch.")
        for target in [target_h, target_cpp]:
            if target.exists():
                backup = backup_root / target.relative_to(repo)
                backup.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(target, backup)
                backups_written += 1
        wt(target_h, h_text)
        wt(target_cpp, cpp_text)
        source_files_written = 2

    smoke_written = 0
    if args.write_smoke_script:
        wt(smoke_path, smoke_text)
        smoke_written = 1

    build_notes = """# DD096Z-D2ZI Build Registration Review

The guarded patch can add:

- `src/datadict/ddict_catalog_resolver.hpp`
- `src/datadict/ddict_catalog_resolver.cpp`

Build registration is not mutated by this package.

Before compiling, inspect the build system:

- if sources are globbed automatically, no CMake edit may be required.
- if sources are listed explicitly, add `src/datadict/ddict_catalog_resolver.cpp` to the appropriate target in a separately guarded build patch.

Call-site integration is also not performed in this package. D2ZJ should patch `DDICT FIELDS` and `DDICT TAGS` call sites after this resolver source is staged.
"""
    wt(gen / "DD096ZD2ZI_BUILD_REGISTRATION_REVIEW.md", build_notes)

    patch_sequence = [
        {"step_id": "D2ZI-01", "step": "Add isolated resolver source/header with legacy-to-x64 binding table."},
        {"step_id": "D2ZI-02", "step": "Review build registration; add cpp to target only if source globbing does not pick it up."},
        {"step_id": "D2ZI-03", "step": "Patch DDICT FIELDS call site to resolve DATA_DICTIONARY_* to bridge family."},
        {"step_id": "D2ZI-04", "step": "Patch DDICT TAGS call site to report physical CDX/LMDB when metadata rows are absent."},
        {"step_id": "D2ZI-05", "step": "Patch REL/EVIDENCE DDICT root token handling."},
        {"step_id": "D2ZI-06", "step": "Run build and D2ZI smoke."},
    ]
    wc(gen / "dd096zd2zi_next_patch_sequence.csv", patch_sequence, ["step_id","step"])

    failures = blockers
    status = "DD096ZD2ZI_GUARDED_RESOLVER_SOURCE_PATCH_READY"
    if args.apply_source_patch and failures == 0:
        status = "DD096ZD2ZI_GUARDED_RESOLVER_SOURCE_PATCH_APPLIED"
    elif failures:
        status = "DD096ZD2ZI_GUARDED_RESOLVER_SOURCE_PATCH_REVIEW"

    boundary = [
        {"boundary": "guarded_resolver_source_patch_package", "observed": 1, "required": 1, "pass": 1},
        {"boundary": "source_files_written", "observed": source_files_written, "required": 2 if args.apply_source_patch else 0, "pass": int(source_files_written == (2 if args.apply_source_patch else 0))},
        {"boundary": "build_file_edits", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "active_catalog_replacement", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "active_dbf_cdx_lmdb_mutation", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "help_meta_cmdhelpchk_mutation", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "manual_publication_mutation", "observed": 0, "required": 0, "pass": 1},
    ]
    wc(out / "dd096zd2zi_boundary_ledger.csv", boundary, ["boundary","observed","required","pass"])

    report = f"""# DD096Z-D2ZI Guarded Resolver Source Patch

Run id: `{args.run_id}`
Status: **{status}**
Created UTC: `{now()}`

## Purpose

D2ZI stages the first guarded source implementation for the DDICT resolver bridge.

It adds an isolated resolver binding layer only when `--apply-source-patch` is supplied. It does not patch DDICT call sites yet.

## Summary

- Precondition blockers: **{blockers}**
- Source files written: **{source_files_written}**
- Existing source backups written: **{backups_written}**
- Smoke script written: **{smoke_written}**
- Build file edits: **0**
- Active catalog mutation: **0**

## Written source files when applied

- `src/datadict/ddict_catalog_resolver.hpp`
- `src/datadict/ddict_catalog_resolver.cpp`

## Next lane

D2ZJ should patch DDICT FIELDS and TAGS call sites to use this resolver layer.
"""
    wt(out / "DD096ZD2ZI_GUARDED_RESOLVER_SOURCE_PATCH_REPORT.md", report)

    manifest = {
        "contract": "dd096zd2zi_guarded_resolver_source_patch_v0",
        "run_id": args.run_id,
        "created_utc": now(),
        "status": status,
        "repo_root": str(repo),
        "profiles": args.profile,
        "precondition_blockers": blockers,
        "apply_source_patch": int(args.apply_source_patch),
        "source_files_written": source_files_written,
        "backups_written": backups_written,
        "smoke_script_written": smoke_written,
        "build_file_edits": 0,
        "active_catalog_replacement": 0,
        "failures": failures,
        "next_recommended_action": "If applied, review build registration then proceed to D2ZJ call-site patch for FIELDS/TAGS.",
    }
    wj(out / "dd096zd2zi_guarded_resolver_source_patch_manifest.json", manifest)

    print(f"DD096Z-D2ZI guarded resolver source patch manifest: {out / 'dd096zd2zi_guarded_resolver_source_patch_manifest.json'}")
    print(f"status: {status}; precondition_blockers: {blockers}; source_files_written: {source_files_written}; build_file_edits: 0; active_catalog_replacement: 0; failures: {failures}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
