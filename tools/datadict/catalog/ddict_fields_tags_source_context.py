#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, datetime as dt, json, re
from pathlib import Path

REQUIRED = [
    ("DD096ZD2ZK", "docs/datadict/reports/DD096ZD2ZK-guarded-ddict-fields-tags-patch-v0/dd096zd2zk_guarded_ddict_fields_tags_patch_manifest.json", ["DD096ZD2ZK_SAFE_SOURCE_PATCH_APPLIED_CALLSITE_REVIEW_PENDING"]),
]

PATTERNS = [
    "FIELDS",
    "TAGS",
    "NO_FIELDS_FOUND",
    "NO_CATALOG_TAGS_FOUND",
    "DATA_DICTIONARY_OBJECTS",
    "DDOBJECT",
    "DDATTR",
    "DDICT TAGS",
    "DDICT FIELDS",
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

def source_windows(text: str, patterns, radius: int):
    lines = text.splitlines()
    hits = []
    for i, line in enumerate(lines, start=1):
        up = line.upper()
        for pat in patterns:
            if pat.upper() in up:
                hits.append((i, pat))
    # Merge overlapping windows.
    raw = []
    for line_no, pat in hits:
        raw.append((max(1, line_no - radius), min(len(lines), line_no + radius), line_no, pat))
    raw.sort()
    merged = []
    for start, end, line_no, pat in raw:
        if not merged or start > merged[-1]["end"] + 2:
            merged.append({"start": start, "end": end, "hits": [(line_no, pat)]})
        else:
            merged[-1]["end"] = max(merged[-1]["end"], end)
            merged[-1]["hits"].append((line_no, pat))
    windows = []
    for idx, w in enumerate(merged, start=1):
        snippet_lines = []
        for n in range(w["start"], w["end"] + 1):
            snippet_lines.append(f"{n:5d}: {lines[n-1]}")
        windows.append({
            "window_id": f"W{idx:03d}",
            "start": w["start"],
            "end": w["end"],
            "hit_summary": "; ".join(f"{ln}:{pat}" for ln, pat in w["hits"][:20]),
            "text": "\n".join(snippet_lines),
        })
    return windows

def classify_window(text: str):
    up = text.upper()
    if "NO_FIELDS_FOUND" in up or "FIELD ROWS" in up:
        return "fields_candidate"
    if "NO_CATALOG_TAGS_FOUND" in up or "CATALOG TAGS" in up or "CDX ARTIFACT" in up:
        return "tags_candidate"
    if "FIELDS" in up:
        return "fields_related"
    if "TAGS" in up:
        return "tags_related"
    return "related"

def plan_text() -> str:
    return """# DD096Z-D2ZL FIELDS/TAGS Patch Planning Notes

D2ZK applied safe scaffolding only. D2ZL extracts the exact local source context needed before a real call-site rewrite.

## Intended D2ZM patch

D2ZM should be the first actual logic patch, and only after reviewing D2ZL source windows.

### FIELDS target

The `DDICT FIELDS <token>` path should normalize `<token>` through the D2ZI/D2ZK bridge before owner lookup.

Required compatibility:

```text
DDICT FIELDS DDOBJECT
DDICT FIELDS DATA_DICTIONARY_OBJECTS
```

Both must produce useful field output or a precise bridge explanation.

### TAGS target

The `DDICT TAGS <token>` path should not report `NO_CATALOG_TAGS_FOUND` when physical DBF/CDX/LMDB artifacts are present.

Required honest result shape:

```text
Table DBF     : YES
CDX artifact  : <path>
LMDB mirror   : <path>
Catalog tags  : 0
Physical tags : <n>
Result        : PHYSICAL_TAGS_FOUND_NO_CATALOG_ROWS
```

## Do not patch blindly

Do not use regex-only replacement inside `cmd_ddict.cpp` until the relevant windows are reviewed.
"""

def smoke_dts() -> str:
    return "\n".join([
        "* DD096Z-D2ZL source-context smoke placeholder",
        "* Actual runtime smoke belongs to D2ZM after call-site patch.",
        "DDICT STATUS",
        "DDICT FIELDS DATA_DICTIONARY_OBJECTS",
        "DDICT FIELDS DDOBJECT",
        "DDICT TAGS DATA_DICTIONARY_OBJECTS",
        "DDICT TAGS DDOBJECT",
        "",
    ])

def main():
    ap = argparse.ArgumentParser(description="DD096Z-D2ZL DDICT FIELDS/TAGS source context extractor")
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--run-id", default="DD096ZD2ZL-ddict-fields-tags-source-context-v0")
    ap.add_argument("--profile", action="append", default=[])
    ap.add_argument("--radius", type=int, default=12)
    ap.add_argument("--write-review-copy", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    out = Path(args.out_dir).resolve()
    gen = out / "generated_ddict_fields_tags_source_context"
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
    wc(gen / "dd096zd2zl_precondition_ledger.csv", pre_rows, ["lane","manifest_path","observed_status","expected_status","pass"])

    cmd_path = repo / "src/cli/cmd_ddict.cpp"
    cmd_text = read_text(cmd_path)
    windows = source_windows(cmd_text, PATTERNS, args.radius)

    window_rows = []
    for w in windows:
        cls = classify_window(w["text"])
        window_rows.append({
            "window_id": w["window_id"],
            "start_line": w["start"],
            "end_line": w["end"],
            "classification": cls,
            "hit_summary": w["hit_summary"],
        })
        wt(gen / f"{w['window_id']}_{cls}_cmd_ddict_context.txt", w["text"] + "\n")
    wc(gen / "dd096zd2zl_source_window_index.csv", window_rows, ["window_id","start_line","end_line","classification","hit_summary"])

    priority_rows = []
    for r in window_rows:
        priority = "review"
        if r["classification"] in ("fields_candidate", "tags_candidate"):
            priority = "high"
        priority_rows.append({**r, "review_priority": priority})
    wc(gen / "dd096zd2zl_patch_review_queue.csv", priority_rows, ["window_id","start_line","end_line","classification","hit_summary","review_priority"])

    wt(gen / "DD096ZD2ZL_FIELDS_TAGS_PATCH_PLANNING_NOTES.md", plan_text())
    wt(gen / "DD096ZD2ZL_REVIEW_SMOKE_PLACEHOLDER.dts", smoke_dts())

    review_copy_written = 0
    if args.write_review_copy:
        review_root = repo / "docs/datadict/reviews/DD096ZD2ZL"
        wt(review_root / "DD096ZD2ZL_FIELDS_TAGS_PATCH_PLANNING_NOTES.md", plan_text())
        for w in windows:
            cls = classify_window(w["text"])
            wt(review_root / f"{w['window_id']}_{cls}_cmd_ddict_context.txt", w["text"] + "\n")
        wt(repo / "dottalkpp/data/scripts/DD096ZD2ZL_REVIEW_SMOKE_PLACEHOLDER.dts", smoke_dts())
        review_copy_written = 1

    required_missing = int(not cmd_path.exists())
    failures = blockers + required_missing
    if failures:
        status = "DD096ZD2ZL_DDICT_FIELDS_TAGS_SOURCE_CONTEXT_REVIEW"
    else:
        status = "DD096ZD2ZL_DDICT_FIELDS_TAGS_SOURCE_CONTEXT_READY"

    boundary = [
        {"boundary": "fields_tags_source_context_only", "observed": 1, "required": 1, "pass": 1},
        {"boundary": "source_edits", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "build_file_edits", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "active_catalog_replacement", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "active_dbf_cdx_lmdb_mutation", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "help_meta_cmdhelpchk_mutation", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "manual_publication_mutation", "observed": 0, "required": 0, "pass": 1},
    ]
    wc(out / "dd096zd2zl_boundary_ledger.csv", boundary, ["boundary","observed","required","pass"])

    report = f"""# DD096Z-D2ZL DDICT FIELDS/TAGS Source Context

Run id: `{args.run_id}`
Status: **{status}**
Created UTC: `{now()}`

## Purpose

D2ZL extracts the actual local source context around DDICT FIELDS/TAGS before the real logic patch.

D2ZK green means scaffolding is present, but the FIELDS/TAGS logic was not rewritten. D2ZL prevents blind patching by producing source windows and a review queue.

## Summary

- Precondition blockers: **{blockers}**
- Required files missing: **{required_missing}**
- Source windows: **{len(windows)}**
- Review copy written: **{review_copy_written}**
- Source edits: **0**
- Build file edits: **0**
- Active catalog mutation: **0**

## Next lane

D2ZM should use the D2ZL review queue to apply the first actual FIELDS/TAGS logic patch.
"""
    wt(out / "DD096ZD2ZL_DDICT_FIELDS_TAGS_SOURCE_CONTEXT_REPORT.md", report)

    manifest = {
        "contract": "dd096zd2zl_ddict_fields_tags_source_context_v0",
        "run_id": args.run_id,
        "created_utc": now(),
        "status": status,
        "repo_root": str(repo),
        "profiles": args.profile,
        "precondition_blockers": blockers,
        "required_files_missing": required_missing,
        "source_windows": len(windows),
        "review_copy_written": review_copy_written,
        "source_edits": 0,
        "build_file_edits": 0,
        "active_catalog_replacement": 0,
        "failures": failures,
        "next_recommended_action": "Review source windows and authorize D2ZM actual FIELDS/TAGS logic patch.",
    }
    wj(out / "dd096zd2zl_ddict_fields_tags_source_context_manifest.json", manifest)

    print(f"DD096Z-D2ZL DDICT FIELDS/TAGS source context manifest: {out / 'dd096zd2zl_ddict_fields_tags_source_context_manifest.json'}")
    print(f"status: {status}; precondition_blockers: {blockers}; source_windows: {len(windows)}; source_edits: 0; failures: {failures}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
