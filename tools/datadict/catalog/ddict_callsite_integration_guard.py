#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, datetime as dt, json, re
from pathlib import Path

REQUIRED = [
    ("DD096ZD2ZI", "docs/datadict/reports/DD096ZD2ZI-guarded-resolver-source-patch-v0/dd096zd2zi_guarded_resolver_source_patch_manifest.json", ["DD096ZD2ZI_GUARDED_RESOLVER_SOURCE_PATCH_APPLIED"]),
]

ALIASES = [
    ("DDRUN", "DATA_DICTIONARY_RUNS"),
    ("DDOBJECT", "DATA_DICTIONARY_OBJECTS"),
    ("DDATTR", "DATA_DICTIONARY_OBJECT_ATTRIBUTES"),
    ("DDEDGE", "DATA_DICTIONARY_RELATION_EDGES"),
    ("DDEVID", "DATA_DICTIONARY_EVIDENCE_RECORDS"),
    ("DDGATE", "DATA_DICTIONARY_GATE_RECORDS"),
]

SOURCE_TARGETS = [
    ("src/cli/cmd_ddict.cpp", "primary call-site patch target"),
    ("src/datadict/ddict_object_resolver.cpp", "resolver helper integration target"),
    ("src/datadict/ddict_catalog_paths.cpp", "path/root behavior review"),
    ("src/datadict/ddict_catalog_resolver.hpp", "new resolver header"),
    ("src/datadict/ddict_catalog_resolver.cpp", "new resolver implementation"),
    ("CMakeLists.txt", "top-level build review"),
    ("src/CMakeLists.txt", "source build review"),
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

def source_metrics(text: str):
    u = text.upper()
    return {
        "line_count": text.count("\n") + (1 if text else 0),
        "has_resolver_include": int("DDICT_CATALOG_RESOLVER" in u or "ddict_catalog_resolver" in text),
        "has_fields_surface": int("FIELDS" in u),
        "has_tags_surface": int("TAGS" in u),
        "has_rel_surface": int("REL" in u),
        "has_evidence_surface": int("EVIDENCE" in u),
        "legacy_mentions": sum(u.count(a) for a, _ in ALIASES),
        "x64_mentions": sum(u.count(b) for _, b in ALIASES),
        "no_fields_found_mentions": u.count("NO_FIELDS_FOUND"),
        "no_catalog_tags_found_mentions": u.count("NO_CATALOG_TAGS_FOUND"),
        "object_not_found_mentions": u.count("OBJECT_NOT_FOUND"),
    }

def find_lines(text: str, patterns):
    rows = []
    for lineno, line in enumerate(text.splitlines(), start=1):
        u = line.upper()
        for p in patterns:
            if p.upper() in u:
                rows.append({"line": lineno, "pattern": p, "text": line[:220]})
    return rows

def smoke_dts() -> str:
    return "\n".join([
        "* DD096Z-D2ZJ DDICT call-site bridge smoke",
        "* Read-only smoke after FIELDS/TAGS call-site integration.",
        "DDICT STATUS",
        "DDICT TABLES",
        "DDICT FIELDS DATA_DICTIONARY_OBJECTS",
        "DDICT FIELDS DDOBJECT",
        "DDICT TAGS DATA_DICTIONARY_OBJECTS",
        "DDICT TAGS DDOBJECT",
        "DDICT REL DDICT BOTH",
        "DDICT EVIDENCE DDICT",
        "",
    ])

def integration_notes() -> str:
    return """# DD096Z-D2ZJ Call-Site Integration Notes

D2ZI added the resolver source layer, but DDICT still needs call-site integration.

## Required source behavior

### FIELDS

Before looking up field metadata, resolve the user token through:

- `dottalk::datadict::ddict_resolve_to_x64_catalog_name(token)`
- or `ddict_resolve_to_legacy_catalog_name(token)` depending on which backing catalog is being queried.

The smoke target is:

```text
DDICT FIELDS DATA_DICTIONARY_OBJECTS
DDICT FIELDS DDOBJECT
```

Both should return compatible field information or an honest bridge explanation.

### TAGS

`DDICT TAGS DATA_DICTIONARY_OBJECTS` already sees physical artifacts, but reports `NO_CATALOG_TAGS_FOUND`.

The call site should distinguish:

1. physical DBF/CDX/LMDB artifacts exist
2. catalog tag rows absent
3. physical CDX tag metadata can still be reported

Acceptable bridge behavior:

```text
Catalog tags  : 0
Physical tags : <n>
Result        : PHYSICAL_TAGS_FOUND_NO_CATALOG_ROWS
```

### REL / EVIDENCE

`DDICT REL DDICT BOTH` and `DDICT EVIDENCE DDICT` currently return `OBJECT_NOT_FOUND`.

Either:

- make `DDICT` resolve as a root catalog object alias, or
- update smoke target to a real object token after documenting the canonical root token.

## Do not mutate

- HELP
- CMDHELPCHK
- manuals
- active DBF/CDX/LMDB artifacts
"""

def main():
    ap = argparse.ArgumentParser(description="DD096Z-D2ZJ DDICT call-site integration guard")
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--run-id", default="DD096ZD2ZJ-ddict-callsite-integration-guard-v0")
    ap.add_argument("--profile", action="append", default=[])
    ap.add_argument("--write-smoke-script", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    out = Path(args.out_dir).resolve()
    gen = out / "generated_ddict_callsite_integration_guard"
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
    wc(gen / "dd096zd2zj_precondition_ledger.csv", pre_rows, ["lane","manifest_path","observed_status","expected_status","pass"])

    inv_rows = []
    for rel, purpose in SOURCE_TARGETS:
        p = repo / rel
        text = read_text(p)
        metrics = source_metrics(text)
        inv_rows.append({
            "path": rel,
            "exists": int(p.exists()),
            "bytes": p.stat().st_size if p.exists() and p.is_file() else 0,
            "purpose": purpose,
            **metrics,
        })
    wc(gen / "dd096zd2zj_source_inventory.csv", inv_rows, [
        "path","exists","bytes","purpose","line_count","has_resolver_include","has_fields_surface",
        "has_tags_surface","has_rel_surface","has_evidence_surface","legacy_mentions","x64_mentions",
        "no_fields_found_mentions","no_catalog_tags_found_mentions","object_not_found_mentions"
    ])

    cmd_text = read_text(repo / "src/cli/cmd_ddict.cpp")
    hit_patterns = ["FIELDS", "TAGS", "NO_FIELDS_FOUND", "NO_CATALOG_TAGS_FOUND", "OBJECT_NOT_FOUND", "DDOBJECT", "DDATTR", "DDEDGE", "DDEVID", "DDGATE", "DDRUN"]
    hit_rows = find_lines(cmd_text, hit_patterns)
    wc(gen / "dd096zd2zj_cmd_ddict_line_hits.csv", hit_rows, ["line","pattern","text"])

    alias_rows = [{"legacy": a, "x64": b, "callsite_policy": "resolve both spellings before lookup"} for a, b in ALIASES]
    wc(gen / "dd096zd2zj_alias_policy.csv", alias_rows, ["legacy","x64","callsite_policy"])

    patch_steps = [
        {"step_id": "D2ZJ-01", "step": "Add include for src/datadict/ddict_catalog_resolver.hpp to cmd_ddict.cpp or appropriate helper."},
        {"step_id": "D2ZJ-02", "step": "Patch DDICT FIELDS token normalization using resolver before object/owner lookup."},
        {"step_id": "D2ZJ-03", "step": "Patch DDICT TAGS to report physical CDX/LMDB tags when catalog metadata rows are absent."},
        {"step_id": "D2ZJ-04", "step": "Preserve DDOBJECT legacy behavior as compatibility baseline."},
        {"step_id": "D2ZJ-05", "step": "Defer REL/EVIDENCE root-token patch until FIELDS/TAGS smoke is green unless implementation is trivial."},
        {"step_id": "D2ZJ-06", "step": "Review build registration for ddict_catalog_resolver.cpp; patch build only if needed."},
        {"step_id": "D2ZJ-07", "step": "Build and run DD096ZD2ZJ_DDICT_CALLSITE_BRIDGE_SMOKE."},
    ]
    wc(gen / "dd096zd2zj_patch_sequence.csv", patch_steps, ["step_id","step"])

    wt(gen / "DD096ZD2ZJ_CALLSITE_INTEGRATION_NOTES.md", integration_notes())
    smoke_text = smoke_dts()
    wt(gen / "DD096ZD2ZJ_DDICT_CALLSITE_BRIDGE_SMOKE.dts", smoke_text)

    smoke_written = 0
    if args.write_smoke_script:
        wt(repo / "dottalkpp/data/scripts/DD096ZD2ZJ_DDICT_CALLSITE_BRIDGE_SMOKE.dts", smoke_text)
        smoke_written = 1

    required_missing = sum(1 for rel, _ in [("src/cli/cmd_ddict.cpp",""), ("src/datadict/ddict_catalog_resolver.hpp",""), ("src/datadict/ddict_catalog_resolver.cpp","")] if not (repo / rel).exists())
    failures = blockers + required_missing
    status = "DD096ZD2ZJ_DDICT_CALLSITE_INTEGRATION_GUARD_READY" if failures == 0 else "DD096ZD2ZJ_DDICT_CALLSITE_INTEGRATION_GUARD_REVIEW"

    boundary = [
        {"boundary": "ddict_callsite_integration_guard_only", "observed": 1, "required": 1, "pass": 1},
        {"boundary": "source_edits", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "build_file_edits", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "active_catalog_replacement", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "active_dbf_cdx_lmdb_mutation", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "help_meta_cmdhelpchk_mutation", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "manual_publication_mutation", "observed": 0, "required": 0, "pass": 1},
    ]
    wc(out / "dd096zd2zj_no_mutation_boundary_ledger.csv", boundary, ["boundary","observed","required","pass"])

    report = f"""# DD096Z-D2ZJ DDICT Call-Site Integration Guard

Run id: `{args.run_id}`
Status: **{status}**
Created UTC: `{now()}`

## Purpose

D2ZJ prepares the call-site integration step after D2ZI applied the isolated resolver source files.

This package does not edit source. It inspects current source and stages the exact next patch sequence for DDICT FIELDS and TAGS.

## Summary

- Precondition blockers: **{blockers}**
- Required files missing: **{required_missing}**
- Smoke script written: **{smoke_written}**
- Source edits: **0**
- Build file edits: **0**
- Active catalog mutation: **0**

## Next implementation target

D2ZK should be the guarded source patch that actually updates DDICT call sites, after reviewing this inventory.
"""
    wt(out / "DD096ZD2ZJ_DDICT_CALLSITE_INTEGRATION_GUARD_REPORT.md", report)

    manifest = {
        "contract": "dd096zd2zj_ddict_callsite_integration_guard_v0",
        "run_id": args.run_id,
        "created_utc": now(),
        "status": status,
        "repo_root": str(repo),
        "profiles": args.profile,
        "precondition_blockers": blockers,
        "required_files_missing": required_missing,
        "smoke_script_written": smoke_written,
        "source_edits": 0,
        "build_file_edits": 0,
        "active_catalog_replacement": 0,
        "failures": failures,
        "next_recommended_action": "Review line hits and authorize D2ZK guarded DDICT FIELDS/TAGS source patch.",
    }
    wj(out / "dd096zd2zj_ddict_callsite_integration_guard_manifest.json", manifest)

    print(f"DD096Z-D2ZJ DDICT call-site integration guard manifest: {out / 'dd096zd2zj_ddict_callsite_integration_guard_manifest.json'}")
    print(f"status: {status}; precondition_blockers: {blockers}; required_files_missing: {required_missing}; source_edits: 0; failures: {failures}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
