#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, datetime as dt, json
from pathlib import Path

REQUIRED = [
    ("DD096ZD2ZQ", "docs/datadict/reports/DD096ZD2ZQ-marker-aware-fields-tags-workbench-v0/dd096zd2zq_marker_aware_fields_tags_workbench_manifest.json", ["DD096ZD2ZQ_MARKER_AWARE_FIELDS_TAGS_WORKBENCH_READY"]),
    ("DD096ZD2ZP", "docs/datadict/reports/DD096ZD2ZP-fields-tags-marker-placement-v0/dd096zd2zp_fields_tags_marker_placement_manifest.json", ["DD096ZD2ZP_FIELDS_TAGS_MARKERS_APPLIED_LOGIC_DEFERRED"]),
]

FIELDS_MARKER = "DD096Z-D2ZP FIELDS OWNER-LOOKUP PATCH MARKER"
TAGS_MARKER = "DD096Z-D2ZP TAGS PHYSICAL-REPORT PATCH MARKER"

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

def marker_line(lines, marker):
    for i, line in enumerate(lines, start=1):
        if marker in line:
            return i
    return 0

def local_window(lines, line_no, before=18, after=45):
    if not line_no:
        return []
    start = max(1, line_no - before)
    end = min(len(lines), line_no + after)
    return [(i, lines[i-1]) for i in range(start, end + 1)]

def metrics_for_window(rows):
    txt = "\n".join(x for _, x in rows)
    up = txt.upper()
    return {
        "line_count": len(rows),
        "has_no_fields_found": int("NO_FIELDS_FOUND" in up),
        "has_no_catalog_tags_found": int("NO_CATALOG_TAGS_FOUND" in up),
        "has_result": int("RESULT" in up),
        "has_note": int("NOTE" in up),
        "has_field_rows": int("FIELD ROWS" in up),
        "has_catalog_tags": int("CATALOG TAGS" in up),
        "has_table_dbf": int("TABLE DBF" in up),
        "has_cdx_artifact": int("CDX ARTIFACT" in up),
        "has_lmdb_mirror": int("LMDB MIRROR" in up),
        "has_bridge_helper_ref": int("DDICT_BRIDGE_" in up),
        "has_return": int("RETURN" in up),
        "has_if": int("IF" in up),
        "has_for": int("FOR" in up),
        "has_lambda": int("[" in txt and "]" in txt),
        "has_print_or_out": int("PRINT" in up or "OUT" in up or "COUT" in up or "EMIT" in up),
    }

def write_window(path: Path, rows):
    wt(path, "\n".join(f"{n:5d}: {line}" for n, line in rows) + "\n")

def patch_plan_text(fields_line, tags_line, fields_metrics, tags_metrics):
    return f'''# DD096Z-D2ZR Marker-Local Patch Readiness

D2ZR has marker-local context and patch intent, but still does not edit source.

## Marker lines

- FIELDS marker: `{fields_line}`
- TAGS marker: `{tags_line}`

## FIELDS local metrics

```json
{json.dumps(fields_metrics, indent=2)}
```

## TAGS local metrics

```json
{json.dumps(tags_metrics, indent=2)}
```

## Readiness decision

A real source patch should only be applied once the local output helper and lookup variables are identified.

D2ZR records the exact work items for D2ZS.

### D2ZS FIELDS work item

At the FIELDS marker, identify:

- requested table/owner token variable
- field row lookup routine or collection
- final `NO_FIELDS_FOUND` emission block

Patch behavior:

1. Try current behavior unchanged.
2. If zero rows and token is bridge-known, retry with `ddict_bridge_legacy_owner_token(token)`.
3. Preserve `DDICT FIELDS DDOBJECT`.
4. Make `DDICT FIELDS DATA_DICTIONARY_OBJECTS` use the same successful metadata path where possible.
5. If still no rows, report an honest bridge status rather than a misleading plain no-fields result.

### D2ZS TAGS work item

At the TAGS marker, identify:

- physical DBF/CDX/LMDB existence booleans or paths
- catalog tag count variable
- final `NO_CATALOG_TAGS_FOUND` emission block

Patch behavior:

1. Preserve physical artifact reporting.
2. If physical artifact exists and catalog tag count is zero, report `PHYSICAL_TAGS_FOUND_NO_CATALOG_ROWS`.
3. Only emit `NO_CATALOG_TAGS_FOUND` when both metadata and physical tag/artifact evidence are absent.
'''

def manual_patch_stub():
    return "\n".join([
        "// DD096Z-D2ZS MANUAL PATCH STUB - DO NOT APPLY BLINDLY",
        "//",
        "// FIELDS marker target:",
        "//   // DD096Z-D2ZP FIELDS OWNER-LOOKUP PATCH MARKER",
        "//",
        "// Insert logic near the final NO_FIELDS_FOUND branch, after identifying:",
        "//   - requested owner/table token variable",
        "//   - existing field-row lookup routine",
        "//   - output/message helper",
        "//",
        "// Pseudocode:",
        "//   if (field_rows.empty() && dottalk::datadict::ddict_bridge_token_is_catalog_surface(requested_token)) {",
        "//       auto legacy_owner = dottalk::datadict::ddict_bridge_legacy_owner_token(requested_token);",
        "//       if (legacy_owner != requested_token) {",
        "//           field_rows = lookup_fields_for_owner(legacy_owner);",
        "//       }",
        "//   }",
        "//",
        "// TAGS marker target:",
        "//   // DD096Z-D2ZP TAGS PHYSICAL-REPORT PATCH MARKER",
        "//",
        "// Insert logic near final NO_CATALOG_TAGS_FOUND branch, after identifying:",
        "//   - catalog tag count",
        "//   - CDX/LMDB physical existence/path variables",
        "//   - output/message helper",
        "//",
        "// Pseudocode:",
        "//   if (catalog_tags.empty() && physical_cdx_exists_or_lmdb_exists) {",
        "//       print(\"Physical tags : <available/inspectable>\");",
        "//       print(\"Result        : PHYSICAL_TAGS_FOUND_NO_CATALOG_ROWS\");",
        "//       return;",
        "//   }",
        "",
    ])

def smoke_dts():
    return "\n".join([
        "* DD096Z-D2ZR marker-local readiness smoke placeholder",
        "* Real runtime smoke belongs after D2ZS actual source patch and rebuild.",
        "DDICT STATUS",
        "DDICT FIELDS DDOBJECT",
        "DDICT FIELDS DATA_DICTIONARY_OBJECTS",
        "DDICT TAGS DDOBJECT",
        "DDICT TAGS DATA_DICTIONARY_OBJECTS",
        "",
    ])

def main():
    ap = argparse.ArgumentParser(description="DD096Z-D2ZR marker-local patch readiness")
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--run-id", default="DD096ZD2ZR-marker-local-patch-readiness-v0")
    ap.add_argument("--profile", action="append", default=[])
    ap.add_argument("--write-review-copy", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    out = Path(args.out_dir).resolve()
    gen = out / "generated_marker_local_patch_readiness"
    gen.mkdir(parents=True, exist_ok=True)

    blockers = 0
    pre_rows = []
    for lane, rel, expected in REQUIRED:
        p = repo / rel
        observed = read_json(p).get("status", "MISSING")
        passed = int(observed in expected)
        blockers += 0 if passed else 1
        pre_rows.append({"lane": lane, "manifest_path": str(p), "observed_status": observed, "expected_status": "|".join(expected), "pass": passed})
    wc(gen / "dd096zd2zr_precondition_ledger.csv", pre_rows, ["lane","manifest_path","observed_status","expected_status","pass"])

    cmd_path = repo / "src/cli/cmd_ddict.cpp"
    text = read_text(cmd_path)
    lines = text.splitlines()
    fields_line = marker_line(lines, FIELDS_MARKER)
    tags_line = marker_line(lines, TAGS_MARKER)

    fields_win = local_window(lines, fields_line)
    tags_win = local_window(lines, tags_line)
    fields_metrics = metrics_for_window(fields_win)
    tags_metrics = metrics_for_window(tags_win)

    write_window(gen / "DD096ZD2ZR_FIELDS_MARKER_LOCAL_WINDOW.txt", fields_win)
    write_window(gen / "DD096ZD2ZR_TAGS_MARKER_LOCAL_WINDOW.txt", tags_win)
    wt(gen / "DD096ZD2ZR_PATCH_PLAN.md", patch_plan_text(fields_line, tags_line, fields_metrics, tags_metrics))
    wt(gen / "DD096ZD2ZR_MANUAL_PATCH_STUB.cpp.txt", manual_patch_stub())
    wt(gen / "DD096ZD2ZR_READINESS_SMOKE_PLACEHOLDER.dts", smoke_dts())

    readiness_rows = [
        {"area": "FIELDS", "marker_line": fields_line, "present": int(fields_line > 0), **fields_metrics},
        {"area": "TAGS", "marker_line": tags_line, "present": int(tags_line > 0), **tags_metrics},
    ]
    wc(gen / "dd096zd2zr_readiness_matrix.csv", readiness_rows, [
        "area","marker_line","present","line_count","has_no_fields_found","has_no_catalog_tags_found",
        "has_result","has_note","has_field_rows","has_catalog_tags","has_table_dbf","has_cdx_artifact",
        "has_lmdb_mirror","has_bridge_helper_ref","has_return","has_if","has_for","has_lambda","has_print_or_out"
    ])

    review_copy_written = 0
    if args.write_review_copy:
        review = repo / "docs/datadict/reviews/DD096ZD2ZR"
        write_window(review / "DD096ZD2ZR_FIELDS_MARKER_LOCAL_WINDOW.txt", fields_win)
        write_window(review / "DD096ZD2ZR_TAGS_MARKER_LOCAL_WINDOW.txt", tags_win)
        wt(review / "DD096ZD2ZR_PATCH_PLAN.md", patch_plan_text(fields_line, tags_line, fields_metrics, tags_metrics))
        wt(review / "DD096ZD2ZR_MANUAL_PATCH_STUB.cpp.txt", manual_patch_stub())
        wt(repo / "dottalkpp/data/scripts/DD096ZD2ZR_READINESS_SMOKE_PLACEHOLDER.dts", smoke_dts())
        review_copy_written = 1

    required_missing = int(not cmd_path.exists())
    marker_failures = int(fields_line == 0) + int(tags_line == 0)
    failures = blockers + required_missing + marker_failures

    status = "DD096ZD2ZR_MARKER_LOCAL_PATCH_READINESS_READY" if failures == 0 else "DD096ZD2ZR_MARKER_LOCAL_PATCH_READINESS_REVIEW"

    boundary = [
        {"boundary": "marker_local_patch_readiness_only", "observed": 1, "required": 1, "pass": 1},
        {"boundary": "source_edits", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "actual_fields_tags_logic_rewritten", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "build_file_edits", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "active_catalog_replacement", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "active_dbf_cdx_lmdb_mutation", "observed": 0, "required": 0, "pass": 1},
    ]
    wc(out / "dd096zd2zr_boundary_ledger.csv", boundary, ["boundary","observed","required","pass"])

    report = f'''# DD096Z-D2ZR Marker-Local Patch Readiness

Run id: `{args.run_id}`
Status: **{status}**
Created UTC: `{now()}`

## Purpose

D2ZR turns the D2ZQ marker-local workbench into concrete patch readiness evidence.

It still does not rewrite source. It produces local source windows, readiness metrics, and a manual patch stub for the next package.

## Summary

- Precondition blockers: **{blockers}**
- Required files missing: **{required_missing}**
- Marker failures: **{marker_failures}**
- FIELDS marker line: **{fields_line}**
- TAGS marker line: **{tags_line}**
- Review copy written: **{review_copy_written}**
- Source edits: **0**
- Actual FIELDS/TAGS logic rewritten: **0**

## Next lane

D2ZS should be the actual source patch or a human-reviewed patch apply package using the D2ZR local windows.
'''
    wt(out / "DD096ZD2ZR_MARKER_LOCAL_PATCH_READINESS_REPORT.md", report)

    manifest = {
        "contract": "dd096zd2zr_marker_local_patch_readiness_v0",
        "run_id": args.run_id,
        "created_utc": now(),
        "status": status,
        "repo_root": str(repo),
        "profiles": args.profile,
        "precondition_blockers": blockers,
        "required_files_missing": required_missing,
        "marker_failures": marker_failures,
        "fields_marker_line": fields_line,
        "tags_marker_line": tags_line,
        "review_copy_written": review_copy_written,
        "source_edits": 0,
        "actual_fields_tags_logic_rewritten": 0,
        "build_file_edits": 0,
        "active_catalog_replacement": 0,
        "failures": failures,
        "next_recommended_action": "Review D2ZR local windows and authorize D2ZS actual source patch.",
    }
    wj(out / "dd096zd2zr_marker_local_patch_readiness_manifest.json", manifest)

    print(f"DD096Z-D2ZR marker-local patch readiness manifest: {out / 'dd096zd2zr_marker_local_patch_readiness_manifest.json'}")
    print(f"status: {status}; precondition_blockers: {blockers}; fields_marker_line: {fields_line}; tags_marker_line: {tags_line}; source_edits: 0; failures: {failures}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
