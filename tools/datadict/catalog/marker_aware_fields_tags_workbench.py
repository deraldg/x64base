#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, datetime as dt, json
from pathlib import Path

REQUIRED = [
    ("DD096ZD2ZP", "docs/datadict/reports/DD096ZD2ZP-fields-tags-marker-placement-v0/dd096zd2zp_fields_tags_marker_placement_manifest.json", ["DD096ZD2ZP_FIELDS_TAGS_MARKERS_APPLIED_LOGIC_DEFERRED"]),
    ("DD096ZD2ZO", "docs/datadict/reports/DD096ZD2ZO-actual-fields-tags-logic-patch-guard-v0/dd096zd2zo_actual_fields_tags_logic_patch_guard_manifest.json", ["DD096ZD2ZO_ACTUAL_FIELDS_TAGS_LOGIC_PATCH_GUARD_READY"]),
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

def locate_marker(lines, marker):
    for i, line in enumerate(lines, start=1):
        if marker in line:
            return i
    return 0

def window(lines, line_no, radius):
    if not line_no:
        return ""
    start = max(1, line_no - radius)
    end = min(len(lines), line_no + radius)
    return "\n".join(f"{i:5d}: {lines[i-1]}" for i in range(start, end + 1))

def segment_until_failure(lines, marker_line, failure_token, max_scan=80):
    if not marker_line:
        return []
    seg = []
    for i in range(marker_line, min(len(lines), marker_line + max_scan) + 1):
        seg.append((i, lines[i-1]))
        if failure_token.upper() in lines[i-1].upper():
            break
    return seg

def segment_metrics(seg):
    text = "\n".join(line for _, line in seg)
    up = text.upper()
    likely_vars = []
    for token in ["OWNER", "TABLE", "NAME", "TOKEN", "ARG", "REQUEST", "CATALOG", "DBF", "CDX", "LMDB", "TAG"]:
        if token in up:
            likely_vars.append(token.lower())
    return {
        "line_count": len(seg),
        "has_no_fields_found": int("NO_FIELDS_FOUND" in up),
        "has_no_catalog_tags_found": int("NO_CATALOG_TAGS_FOUND" in up),
        "has_cdx": int("CDX" in up),
        "has_lmdb": int("LMDB" in up),
        "has_catalog_tags": int("CATALOG TAGS" in up),
        "has_field_rows": int("FIELD ROWS" in up),
        "likely_local_concepts": ",".join(likely_vars),
    }

def smoke_dts():
    return "\n".join([
        "* DD096Z-D2ZQ marker-aware FIELDS/TAGS workbench smoke",
        "* Real runtime smoke belongs after D2ZR/D2ZS actual source patch and rebuild.",
        "DDICT STATUS",
        "DDICT FIELDS DDOBJECT",
        "DDICT FIELDS DATA_DICTIONARY_OBJECTS",
        "DDICT TAGS DDOBJECT",
        "DDICT TAGS DATA_DICTIONARY_OBJECTS",
        "",
    ])

def workbench_notes(fields_line, tags_line, fields_metrics, tags_metrics):
    return f"""# DD096Z-D2ZQ Marker-Aware FIELDS/TAGS Workbench

D2ZQ confirms the D2ZP markers are present and extracts the exact marker-local code needed for a real source patch.

## Marker lines

- FIELDS marker line: `{fields_line}`
- TAGS marker line: `{tags_line}`

## FIELDS segment metrics

```json
{json.dumps(fields_metrics, indent=2)}
```

## TAGS segment metrics

```json
{json.dumps(tags_metrics, indent=2)}
```

## Decision

This package does not rewrite the logic automatically.

Reason: the patch must connect to local variables and output helpers visible in the extracted marker windows. D2ZR should be the actual source patch after reviewing:

- `DD096ZD2ZQ_FIELDS_MARKER_WINDOW.txt`
- `DD096ZD2ZQ_TAGS_MARKER_WINDOW.txt`
- `DD096ZD2ZQ_FIELDS_SEGMENT.txt`
- `DD096ZD2ZQ_TAGS_SEGMENT.txt`

## D2ZR target

FIELDS:
- Use the bridge helpers to try legacy/x64 owner names before final `NO_FIELDS_FOUND`.

TAGS:
- If physical DBF/CDX/LMDB evidence exists, avoid plain `NO_CATALOG_TAGS_FOUND`.
- Report `PHYSICAL_TAGS_FOUND_NO_CATALOG_ROWS` when catalog rows are absent but physical tag artifacts exist.
"""

def main():
    ap = argparse.ArgumentParser(description="DD096Z-D2ZQ marker-aware FIELDS/TAGS workbench")
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--run-id", default="DD096ZD2ZQ-marker-aware-fields-tags-workbench-v0")
    ap.add_argument("--profile", action="append", default=[])
    ap.add_argument("--radius", type=int, default=28)
    ap.add_argument("--write-review-copy", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    out = Path(args.out_dir).resolve()
    gen = out / "generated_marker_aware_fields_tags_workbench"
    gen.mkdir(parents=True, exist_ok=True)

    blockers = 0
    pre_rows = []
    for lane, rel, expected in REQUIRED:
        p = repo / rel
        observed = read_json(p).get("status", "MISSING")
        passed = int(observed in expected)
        blockers += 0 if passed else 1
        pre_rows.append({"lane": lane, "manifest_path": str(p), "observed_status": observed, "expected_status": "|".join(expected), "pass": passed})
    wc(gen / "dd096zd2zq_precondition_ledger.csv", pre_rows, ["lane","manifest_path","observed_status","expected_status","pass"])

    cmd_path = repo / "src/cli/cmd_ddict.cpp"
    text = read_text(cmd_path)
    lines = text.splitlines()
    fields_line = locate_marker(lines, FIELDS_MARKER)
    tags_line = locate_marker(lines, TAGS_MARKER)

    fields_seg = segment_until_failure(lines, fields_line, "NO_FIELDS_FOUND")
    tags_seg = segment_until_failure(lines, tags_line, "NO_CATALOG_TAGS_FOUND")
    fields_metrics = segment_metrics(fields_seg)
    tags_metrics = segment_metrics(tags_seg)

    marker_rows = [
        {"marker": "FIELDS", "line": fields_line, "present": int(fields_line > 0), **fields_metrics},
        {"marker": "TAGS", "line": tags_line, "present": int(tags_line > 0), **tags_metrics},
    ]
    wc(gen / "dd096zd2zq_marker_segment_metrics.csv", marker_rows, [
        "marker","line","present","line_count","has_no_fields_found","has_no_catalog_tags_found",
        "has_cdx","has_lmdb","has_catalog_tags","has_field_rows","likely_local_concepts"
    ])

    wt(gen / "DD096ZD2ZQ_FIELDS_MARKER_WINDOW.txt", window(lines, fields_line, args.radius) + "\n")
    wt(gen / "DD096ZD2ZQ_TAGS_MARKER_WINDOW.txt", window(lines, tags_line, args.radius) + "\n")
    wt(gen / "DD096ZD2ZQ_FIELDS_SEGMENT.txt", "\n".join(f"{n:5d}: {line}" for n, line in fields_seg) + "\n")
    wt(gen / "DD096ZD2ZQ_TAGS_SEGMENT.txt", "\n".join(f"{n:5d}: {line}" for n, line in tags_seg) + "\n")
    wt(gen / "DD096ZD2ZQ_MARKER_AWARE_WORKBENCH_NOTES.md", workbench_notes(fields_line, tags_line, fields_metrics, tags_metrics))
    wt(gen / "DD096ZD2ZQ_MARKER_AWARE_SMOKE_PLACEHOLDER.dts", smoke_dts())

    review_copy_written = 0
    if args.write_review_copy:
        review = repo / "docs/datadict/reviews/DD096ZD2ZQ"
        wt(review / "DD096ZD2ZQ_FIELDS_MARKER_WINDOW.txt", window(lines, fields_line, args.radius) + "\n")
        wt(review / "DD096ZD2ZQ_TAGS_MARKER_WINDOW.txt", window(lines, tags_line, args.radius) + "\n")
        wt(review / "DD096ZD2ZQ_FIELDS_SEGMENT.txt", "\n".join(f"{n:5d}: {line}" for n, line in fields_seg) + "\n")
        wt(review / "DD096ZD2ZQ_TAGS_SEGMENT.txt", "\n".join(f"{n:5d}: {line}" for n, line in tags_seg) + "\n")
        wt(review / "DD096ZD2ZQ_MARKER_AWARE_WORKBENCH_NOTES.md", workbench_notes(fields_line, tags_line, fields_metrics, tags_metrics))
        wt(repo / "dottalkpp/data/scripts/DD096ZD2ZQ_MARKER_AWARE_SMOKE_PLACEHOLDER.dts", smoke_dts())
        review_copy_written = 1

    required_missing = int(not cmd_path.exists())
    marker_failures = int(fields_line == 0) + int(tags_line == 0)
    failures = blockers + required_missing + marker_failures
    status = "DD096ZD2ZQ_MARKER_AWARE_FIELDS_TAGS_WORKBENCH_READY" if failures == 0 else "DD096ZD2ZQ_MARKER_AWARE_FIELDS_TAGS_WORKBENCH_REVIEW"

    boundary = [
        {"boundary": "marker_aware_fields_tags_workbench_only", "observed": 1, "required": 1, "pass": 1},
        {"boundary": "source_edits", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "actual_fields_tags_logic_rewritten", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "build_file_edits", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "active_catalog_replacement", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "active_dbf_cdx_lmdb_mutation", "observed": 0, "required": 0, "pass": 1},
    ]
    wc(out / "dd096zd2zq_boundary_ledger.csv", boundary, ["boundary","observed","required","pass"])

    report = f"""# DD096Z-D2ZQ Marker-Aware FIELDS/TAGS Workbench

Run id: `{args.run_id}`
Status: **{status}**
Created UTC: `{now()}`

## Purpose

D2ZQ extracts exact marker-local code after D2ZP placed surgical markers.

This package does not rewrite source. It prepares the evidence needed for D2ZR actual source patch.

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

D2ZR should be the actual source patch using the marker windows and segments generated here.
"""
    wt(out / "DD096ZD2ZQ_MARKER_AWARE_FIELDS_TAGS_WORKBENCH_REPORT.md", report)

    manifest = {
        "contract": "dd096zd2zq_marker_aware_fields_tags_workbench_v0",
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
        "next_recommended_action": "Review D2ZQ marker windows and authorize D2ZR actual FIELDS/TAGS source patch.",
    }
    wj(out / "dd096zd2zq_marker_aware_fields_tags_workbench_manifest.json", manifest)

    print(f"DD096Z-D2ZQ marker-aware FIELDS/TAGS workbench manifest: {out / 'dd096zd2zq_marker_aware_fields_tags_workbench_manifest.json'}")
    print(f"status: {status}; precondition_blockers: {blockers}; fields_marker_line: {fields_line}; tags_marker_line: {tags_line}; source_edits: 0; failures: {failures}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
