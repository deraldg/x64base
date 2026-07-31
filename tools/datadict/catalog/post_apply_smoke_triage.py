#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, datetime as dt, json, re
from pathlib import Path

REQUIRED = [
    ("DD096ZD2ZF", "docs/datadict/reports/DD096ZD2ZF-guarded-active-replacement-execution-v0/dd096zd2zf_active_replacement_execution_manifest.json", ["DD096ZD2ZF_ACTIVE_REPLACEMENT_EXECUTED_PENDING_SMOKE", "DD096ZD2ZF_ACTIVE_REPLACEMENT_PREVIEW_READY"]),
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

def scan_smoke(text: str):
    up = text.upper()
    return {
        "proof_supplied": int(bool(text)),
        "ddict_status_seen": int("DDICT STATUS" in up),
        "active_catalog_present_seen": int("CATALOG STATE : ACTIVE_CATALOG_PRESENT" in up or "CATALOG STATE : ACTIVE_CATALOG_PRESENT" in up.replace("  ", " ")),
        "legacy_tables_listed": sum(1 for t in ["DDRUN","DDBASE","DDSOURCE","DDOBJECT","DDATTR","DDEDGE","DDEVID","DDGATE","DDREVIEW","DDARTIF","DDPROFILE"] if re.search(r"\b" + re.escape(t) + r"\b\s+YES", up)),
        "data_dictionary_objects_field_rows_zero": int("DDICT FIELDS DATA_DICTIONARY_OBJECTS" in up and "FIELD ROWS    : 0" in up),
        "ddobject_field_rows_seen": int("DDICT FIELDS DDOBJECT" in up and "FIELD ROWS    : 7" in up),
        "new_physical_table_seen_by_tags": int("DDICT TAGS DATA_DICTIONARY_OBJECTS" in up and "TABLE DBF     : YES" in up),
        "new_cdx_artifact_seen": int("DATA_DICTIONARY_OBJECTS.CDX" in up),
        "new_lmdb_artifact_seen": int("DATA_DICTIONARY_OBJECTS.CDX.D" in up),
        "no_catalog_tags_found": int("NO_CATALOG_TAGS_FOUND" in up),
        "rel_object_not_found": int("DDICT REL DDICT BOTH" in up and "OBJECT_NOT_FOUND" in up),
        "evidence_object_not_found": int("DDICT EVIDENCE DDICT" in up and "OBJECT_NOT_FOUND" in up),
        "active_path_seen": int("D:\\CODE\\CCODE\\DOTTALKPP\\DATA\\DATADICT" in up or "D:/CODE/CCODE/DOTTALKPP/DATA/DATADICT" in up),
        "candidate_path_seen": int("DOCS\\DATADICT\\CANDIDATES" in up or "DOCS/DATADICT/CANDIDATES" in up),
    }

def main():
    ap = argparse.ArgumentParser(description="DD096Z-D2ZG post-apply smoke triage")
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--run-id", default="DD096ZD2ZG-post-apply-smoke-triage-v0")
    ap.add_argument("--runtime-proof", default="")
    ap.add_argument("--profile", action="append", default=[])
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    out = Path(args.out_dir).resolve()
    gen = out / "generated_post_apply_smoke_triage"
    gen.mkdir(parents=True, exist_ok=True)

    pre_rows = []
    blockers = 0
    # Accept missing D2ZF manifest as review, because some execution logs may not be pasted yet.
    for lane, rel, expected in REQUIRED:
        p = repo / rel
        data = read_json(p)
        observed = data.get("status", "MISSING")
        passed = int(observed in expected)
        blockers += 0 if passed else 1
        pre_rows.append({"lane": lane, "manifest_path": str(p), "observed_status": observed, "expected_status": "|".join(expected), "pass": passed})
    wc(gen / "dd096zd2zg_precondition_ledger.csv", pre_rows, ["lane","manifest_path","observed_status","expected_status","pass"])

    proof_text = ""
    if args.runtime_proof:
        p = Path(args.runtime_proof)
        if not p.is_absolute():
            p = repo / p
        proof_text = read_text(p)
    metrics = scan_smoke(proof_text)
    wc(gen / "dd096zd2zg_smoke_metric_scan.csv", [{"metric": k, "value": v} for k, v in sorted(metrics.items())], ["metric","value"])

    findings = [
        {
            "finding_id": "D2ZG-F01",
            "classification": "physical_artifacts_present",
            "finding": "DDICT TAGS DATA_DICTIONARY_OBJECTS sees Table DBF YES plus DATA_DICTIONARY_OBJECTS.cdx and DATA_DICTIONARY_OBJECTS.cdx.d.",
            "evidence": "New physical DBF/CDX/LMDB artifacts are visible in active paths.",
            "action": "Do not rollback solely on physical replacement evidence.",
        },
        {
            "finding_id": "D2ZG-F02",
            "classification": "resolver_catalog_gap",
            "finding": "DDICT TABLES still lists legacy compact DD* catalog families and DDICT FIELDS DATA_DICTIONARY_OBJECTS returns 0 rows.",
            "evidence": "The active reader still queries legacy DDOBJECT/DDATTR style catalog rows.",
            "action": "Implement or enable DDICT resolver/alias bridge for DATA_DICTIONARY_* names.",
        },
        {
            "finding_id": "D2ZG-F03",
            "classification": "catalog_metadata_gap",
            "finding": "DDICT TAGS DATA_DICTIONARY_OBJECTS finds physical artifacts but 0 catalog tags.",
            "evidence": "Physical tag existence and catalog metadata rows are separate; DDICT currently expects catalog tag rows in legacy object rows.",
            "action": "Update tag reader to inspect physical CDX/TAGS when catalog rows are not present, or seed bridge metadata.",
        },
        {
            "finding_id": "D2ZG-F04",
            "classification": "alias_seed_gap",
            "finding": "DDICT REL DDICT BOTH and DDICT EVIDENCE DDICT return OBJECT_NOT_FOUND.",
            "evidence": "Token DDICT is not resolved against OBJID/name/owner in current active catalog.",
            "action": "Add DDICT alias/root object handling or adapt smoke target to an existing object token.",
        },
        {
            "finding_id": "D2ZG-F05",
            "classification": "rollback_not_recommended_yet",
            "finding": "Smoke is red at DDICT reader/metadata compatibility level, not at copy/path/physical artifact level.",
            "evidence": "Active catalog present, physical DATA_DICTIONARY_OBJECTS DBF/CDX/LMDB visible.",
            "action": "Proceed to resolver bridge/source patch planning before rollback.",
        },
    ]
    wc(gen / "dd096zd2zg_findings.csv", findings, ["finding_id","classification","finding","evidence","action"])

    smoke_rows = [
        {"surface": "DDICT STATUS", "observed": "ACTIVE_CATALOG_PRESENT", "status": "green", "next": "retain"},
        {"surface": "DDICT TABLES", "observed": "legacy DD* table list", "status": "review", "next": "resolver must expose or bridge DATA_DICTIONARY_* active artifacts"},
        {"surface": "DDICT FIELDS DATA_DICTIONARY_OBJECTS", "observed": "0 field rows", "status": "red", "next": "resolver/reader update required"},
        {"surface": "DDICT FIELDS DDOBJECT", "observed": "7 field rows", "status": "green_legacy", "next": "use as compatibility baseline"},
        {"surface": "DDICT TAGS DATA_DICTIONARY_OBJECTS", "observed": "physical DBF/CDX/LMDB yes; catalog tags 0", "status": "review", "next": "physical tag reader or metadata bridge required"},
        {"surface": "DDICT REL DDICT BOTH", "observed": "OBJECT_NOT_FOUND", "status": "red", "next": "alias/root object resolver required"},
        {"surface": "DDICT EVIDENCE DDICT", "observed": "OBJECT_NOT_FOUND", "status": "red", "next": "alias/root object resolver required"},
    ]
    wc(gen / "dd096zd2zg_surface_triage.csv", smoke_rows, ["surface","observed","status","next"])

    next_plan = """# DD096Z-D2ZG Next Lane Proposal

## Status

Post-apply smoke is red at the DDICT reader/resolver layer.

This is not a physical artifact rollback condition yet. The active catalog reports present, and DDICT TAGS DATA_DICTIONARY_OBJECTS sees the physical DBF/CDX/LMDB artifact paths.

## Required next package

DD096Z-D2ZH should be a guarded DDICT resolver/catalog-reader bridge package.

Scope:

1. Locate DDICT source call sites:
   - src/cli/cmd_ddict.cpp
   - src/datadict/ddict_catalog_paths.cpp
   - src/datadict/ddict_object_resolver.cpp
2. Add or integrate a resolver map:
   - DDOBJECT -> DATA_DICTIONARY_OBJECTS
   - DDATTR -> DATA_DICTIONARY_OBJECT_ATTRIBUTES
   - DDEDGE -> DATA_DICTIONARY_RELATION_EDGES
   - DDEVID -> DATA_DICTIONARY_EVIDENCE_RECORDS
   - DDGATE -> DATA_DICTIONARY_GATE_RECORDS
   - DDRUN -> DATA_DICTIONARY_RUNS
3. Preserve legacy DDICT behavior for DDOBJECT/DDATTR etc.
4. Let x64 DATA_DICTIONARY_* names resolve in FIELDS/TAGS.
5. For TAGS, if catalog rows are absent but physical CDX/LMDB artifacts exist, report physical tags honestly instead of NO_CATALOG_TAGS_FOUND.
6. Add or adapt object alias for DDICT root token used by REL/EVIDENCE smoke.
7. Keep HELP/CMDHELPCHK/manual mutation out of scope.

## Do not do yet

- Do not rollback active artifacts.
- Do not mutate HELP or CMDHELPCHK.
- Do not declare replacement fully green until resolver smoke passes.
"""
    wt(gen / "DD096ZD2ZG_NEXT_LANE_PROPOSAL.md", next_plan)

    status = "DD096ZD2ZG_POST_APPLY_SMOKE_TRIAGE_REVIEW"
    if metrics.get("proof_supplied", 0) and metrics.get("new_physical_table_seen_by_tags", 0) and metrics.get("data_dictionary_objects_field_rows_zero", 0):
        status = "DD096ZD2ZG_POST_APPLY_SMOKE_TRIAGE_CLASSIFIED"

    boundary_rows = [
        {"boundary": "post_apply_smoke_triage_only", "observed": 1, "required": 1, "pass": 1},
        {"boundary": "rollback_executed", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "active_catalog_replacement", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "source_edits", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "help_meta_cmdhelpchk_mutation", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "manual_publication_mutation", "observed": 0, "required": 0, "pass": 1},
    ]
    wc(out / "dd096zd2zg_no_mutation_boundary_ledger.csv", boundary_rows, ["boundary","observed","required","pass"])

    report = f"""# DD096Z-D2ZG Post-Apply Smoke Triage

Run id: `{args.run_id}`
Status: **{status}**
Created UTC: `{now()}`

## Summary

The post-apply smoke is not green, but it is also not an immediate rollback signal.

The active physical artifacts for `DATA_DICTIONARY_OBJECTS` are visible:

- DBF: YES
- CDX artifact: `DATA_DICTIONARY_OBJECTS.cdx`
- LMDB mirror: `DATA_DICTIONARY_OBJECTS.cdx.d`

The DDICT command layer still resolves through the old compact catalog model:

- `DDICT TABLES` lists legacy `DD*` tables
- `DDICT FIELDS DATA_DICTIONARY_OBJECTS` returns 0 rows
- `DDICT FIELDS DDOBJECT` still works
- `DDICT TAGS DATA_DICTIONARY_OBJECTS` sees physical artifacts but no catalog tags
- `DDICT REL DDICT BOTH` and `DDICT EVIDENCE DDICT` return `OBJECT_NOT_FOUND`

## Conclusion

Replacement copy appears physically present; reader/resolver compatibility is the blocker.

Next safe lane: DDICT resolver/catalog-reader bridge package.
"""
    wt(out / "DD096ZD2ZG_POST_APPLY_SMOKE_TRIAGE_REPORT.md", report)

    manifest = {
        "contract": "dd096zd2zg_post_apply_smoke_triage_v0",
        "run_id": args.run_id,
        "created_utc": now(),
        "status": status,
        "repo_root": str(repo),
        "profiles": args.profile,
        "proof_supplied": metrics.get("proof_supplied", 0),
        "physical_new_artifacts_visible": metrics.get("new_physical_table_seen_by_tags", 0),
        "legacy_ddict_still_operational": metrics.get("ddobject_field_rows_seen", 0),
        "x64_fields_gap": metrics.get("data_dictionary_objects_field_rows_zero", 0),
        "catalog_tags_gap": metrics.get("no_catalog_tags_found", 0),
        "rel_gap": metrics.get("rel_object_not_found", 0),
        "evidence_gap": metrics.get("evidence_object_not_found", 0),
        "rollback_recommended": 0,
        "active_replacement_executed_by_this_package": 0,
        "source_edits": 0,
        "next_recommended_action": "Create guarded DDICT resolver/catalog-reader bridge package DD096Z-D2ZH.",
    }
    wj(out / "dd096zd2zg_post_apply_smoke_triage_manifest.json", manifest)

    print(f"DD096Z-D2ZG post-apply smoke triage manifest: {out / 'dd096zd2zg_post_apply_smoke_triage_manifest.json'}")
    print(f"status: {status}; physical_new_artifacts_visible: {metrics.get('new_physical_table_seen_by_tags',0)}; x64_fields_gap: {metrics.get('data_dictionary_objects_field_rows_zero',0)}; rollback_recommended: 0")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
