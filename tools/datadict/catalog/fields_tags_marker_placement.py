#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, datetime as dt, json, shutil
from pathlib import Path

REQUIRED = [
    ("DD096ZD2ZO", "docs/datadict/reports/DD096ZD2ZO-actual-fields-tags-logic-patch-guard-v0/dd096zd2zo_actual_fields_tags_logic_patch_guard_manifest.json", ["DD096ZD2ZO_ACTUAL_FIELDS_TAGS_LOGIC_PATCH_GUARD_READY"]),
    ("DD096ZD2ZN", "docs/datadict/reports/DD096ZD2ZN-surgical-fields-tags-patch-v0/dd096zd2zn_surgical_fields_tags_patch_manifest.json", ["DD096ZD2ZN_SAFE_MARKER_APPLIED_LOGIC_PATCH_DEFERRED"]),
]

FIELDS_MARKER = "// DD096Z-D2ZP FIELDS OWNER-LOOKUP PATCH MARKER"
TAGS_MARKER = "// DD096Z-D2ZP TAGS PHYSICAL-REPORT PATCH MARKER"

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

def find_anchor_lines(text: str):
    lines = text.splitlines()
    anchors = []
    for i, line in enumerate(lines, start=1):
        up = line.upper()
        if "NO_FIELDS_FOUND" in up:
            anchors.append({"kind": "fields_no_fields_found", "line": i, "text": line[:240]})
        if "NO_CATALOG_TAGS_FOUND" in up:
            anchors.append({"kind": "tags_no_catalog_tags_found", "line": i, "text": line[:240]})
        if "FIELD ROWS" in up:
            anchors.append({"kind": "fields_row_count", "line": i, "text": line[:240]})
        if "CATALOG TAGS" in up:
            anchors.append({"kind": "tags_catalog_count", "line": i, "text": line[:240]})
        if "CDX ARTIFACT" in up or "LMDB MIRROR" in up:
            anchors.append({"kind": "tags_physical_artifact", "line": i, "text": line[:240]})
    return anchors

def place_markers(text: str):
    if FIELDS_MARKER in text or TAGS_MARKER in text:
        return text, 0, "markers_already_present_or_partial"
    lines = text.splitlines()
    fields_line = None
    tags_line = None
    for idx, line in enumerate(lines):
        up = line.upper()
        if fields_line is None and "NO_FIELDS_FOUND" in up:
            fields_line = idx
        if tags_line is None and "NO_CATALOG_TAGS_FOUND" in up:
            tags_line = idx
    changes = 0
    plan = []
    # Insert in reverse line order so indices remain valid.
    inserts = []
    if fields_line is not None:
        inserts.append((fields_line, [
            FIELDS_MARKER,
            "// D2ZQ target: normalize requested owner through ddict_bridge_legacy_owner_token / ddict_bridge_x64_owner_token before final NO_FIELDS_FOUND.",
        ]))
    if tags_line is not None:
        inserts.append((tags_line, [
            TAGS_MARKER,
            "// D2ZQ target: if physical DBF/CDX/LMDB exists but catalog rows are absent, report PHYSICAL_TAGS_FOUND_NO_CATALOG_ROWS.",
        ]))
    for index, marker_lines in sorted(inserts, key=lambda x: x[0], reverse=True):
        for m in reversed(marker_lines):
            lines.insert(index, m)
        changes += 1
        plan.append({"insert_before_line": index + 1, "marker": marker_lines[0]})
    if changes == 0:
        return text, 0, "no_no_fields_or_no_catalog_tags_anchors_found"
    return "\n".join(lines) + ("\n" if text.endswith("\n") else ""), changes, "markers_inserted"

def window(text: str, line: int, radius: int = 8):
    lines = text.splitlines()
    start = max(1, line - radius)
    end = min(len(lines), line + radius)
    return "\n".join(f"{i:5d}: {lines[i-1]}" for i in range(start, end + 1))

def smoke_dts():
    return "\n".join([
        "* DD096Z-D2ZP marker-placement smoke placeholder",
        "* Real runtime smoke belongs after D2ZQ actual logic patch.",
        "DDICT STATUS",
        "DDICT FIELDS DDOBJECT",
        "DDICT FIELDS DATA_DICTIONARY_OBJECTS",
        "DDICT TAGS DDOBJECT",
        "DDICT TAGS DATA_DICTIONARY_OBJECTS",
        "",
    ])

def main():
    ap = argparse.ArgumentParser(description="DD096Z-D2ZP FIELDS/TAGS marker placement")
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--run-id", default="DD096ZD2ZP-fields-tags-marker-placement-v0")
    ap.add_argument("--profile", action="append", default=[])
    ap.add_argument("--apply-marker-placement", action="store_true")
    ap.add_argument("--write-smoke-script", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    out = Path(args.out_dir).resolve()
    gen = out / "generated_fields_tags_marker_placement"
    gen.mkdir(parents=True, exist_ok=True)

    blockers = 0
    pre_rows = []
    for lane, rel, expected in REQUIRED:
        p = repo / rel
        observed = read_json(p).get("status", "MISSING")
        passed = int(observed in expected)
        blockers += 0 if passed else 1
        pre_rows.append({"lane": lane, "manifest_path": str(p), "observed_status": observed, "expected_status": "|".join(expected), "pass": passed})
    wc(gen / "dd096zd2zp_precondition_ledger.csv", pre_rows, ["lane","manifest_path","observed_status","expected_status","pass"])

    cmd_path = repo / "src/cli/cmd_ddict.cpp"
    cmd_text = read_text(cmd_path)
    anchors = find_anchor_lines(cmd_text)
    wc(gen / "dd096zd2zp_anchor_inventory.csv", anchors, ["kind","line","text"])

    for a in anchors:
        wt(gen / f"{a['kind']}_{a['line']}_context.txt", window(cmd_text, int(a["line"])) + "\n")

    patched, marker_changes, marker_status = place_markers(cmd_text)
    wt(gen / "cmd_ddict.cpp.marker_preview", patched if patched else "")

    source_files_written = 0
    backups_written = 0
    backup_root = repo / f"docs/datadict/backups/DD096ZD2ZP-source-backup-{dt.datetime.now().strftime('%Y%m%d_%H%M%S')}"
    required_missing = int(not cmd_path.exists())

    if args.apply_marker_placement:
        if blockers:
            raise SystemExit("Precondition blockers present; refusing --apply-marker-placement.")
        if required_missing:
            raise SystemExit("cmd_ddict.cpp missing; refusing --apply-marker-placement.")
        if marker_changes == 0:
            raise SystemExit(f"No marker changes available: {marker_status}")
        backup = backup_root / cmd_path.relative_to(repo)
        backup.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(cmd_path, backup)
        backups_written = 1
        wt(cmd_path, patched)
        source_files_written = 1

    smoke_written = 0
    if args.write_smoke_script:
        wt(repo / "dottalkpp/data/scripts/DD096ZD2ZP_MARKER_PLACEMENT_SMOKE_PLACEHOLDER.dts", smoke_dts())
        smoke_written = 1
    wt(gen / "DD096ZD2ZP_MARKER_PLACEMENT_SMOKE_PLACEHOLDER.dts", smoke_dts())

    notes = f"""# DD096Z-D2ZP Marker Placement Notes

D2ZO refused actual rewrite because no explicit markers were present.

D2ZP places comment-only patch markers at the two final-result anchors:

- `NO_FIELDS_FOUND`
- `NO_CATALOG_TAGS_FOUND`

These markers are not runtime logic. They are surgical landmarks for D2ZQ.

## Marker status

`{marker_status}`

## Markers

```cpp
{FIELDS_MARKER}
{TAGS_MARKER}
```

## D2ZQ must do real logic

D2ZQ should patch code at these markers to:

1. Bridge `DDICT FIELDS DATA_DICTIONARY_OBJECTS` to the same field metadata path that keeps `DDICT FIELDS DDOBJECT` green.
2. Bridge `DDICT TAGS DATA_DICTIONARY_OBJECTS` so physical CDX/LMDB artifacts do not end as plain `NO_CATALOG_TAGS_FOUND`.
"""
    wt(gen / "DD096ZD2ZP_MARKER_PLACEMENT_NOTES.md", notes)

    failures = blockers + required_missing
    if failures:
        status = "DD096ZD2ZP_FIELDS_TAGS_MARKER_PLACEMENT_REVIEW"
    elif args.apply_marker_placement:
        status = "DD096ZD2ZP_FIELDS_TAGS_MARKERS_APPLIED_LOGIC_DEFERRED"
    else:
        status = "DD096ZD2ZP_FIELDS_TAGS_MARKER_PLACEMENT_READY"

    boundary = [
        {"boundary": "fields_tags_marker_placement_only", "observed": 1, "required": 1, "pass": 1},
        {"boundary": "marker_comments_written", "observed": source_files_written, "required": 1 if args.apply_marker_placement else 0, "pass": int(source_files_written == (1 if args.apply_marker_placement else 0))},
        {"boundary": "actual_fields_tags_logic_rewritten", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "build_file_edits", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "active_catalog_replacement", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "active_dbf_cdx_lmdb_mutation", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "help_meta_cmdhelpchk_mutation", "observed": 0, "required": 0, "pass": 1},
    ]
    wc(out / "dd096zd2zp_boundary_ledger.csv", boundary, ["boundary","observed","required","pass"])

    report = f"""# DD096Z-D2ZP FIELDS/TAGS Marker Placement

Run id: `{args.run_id}`
Status: **{status}**
Created UTC: `{now()}`

## Purpose

D2ZP responds to D2ZO's safe refusal: `no_explicit_d2zo_markers_refuse_actual_rewrite`.

It places comment-only surgical markers near the final FIELDS/TAGS failure-result anchors. This does not change runtime behavior.

## Summary

- Precondition blockers: **{blockers}**
- Required files missing: **{required_missing}**
- Anchor rows found: **{len(anchors)}**
- Marker status: **{marker_status}**
- Marker changes available: **{marker_changes}**
- Source files written: **{source_files_written}**
- Actual FIELDS/TAGS logic rewritten: **0**
- Smoke script written: **{smoke_written}**

## Next lane

D2ZQ should apply the actual FIELDS/TAGS logic at these markers.
"""
    wt(out / "DD096ZD2ZP_FIELDS_TAGS_MARKER_PLACEMENT_REPORT.md", report)

    manifest = {
        "contract": "dd096zd2zp_fields_tags_marker_placement_v0",
        "run_id": args.run_id,
        "created_utc": now(),
        "status": status,
        "repo_root": str(repo),
        "profiles": args.profile,
        "precondition_blockers": blockers,
        "required_files_missing": required_missing,
        "anchor_rows_found": len(anchors),
        "marker_status": marker_status,
        "marker_changes_available": marker_changes,
        "apply_marker_placement": int(args.apply_marker_placement),
        "source_files_written": source_files_written,
        "backups_written": backups_written,
        "smoke_script_written": smoke_written,
        "actual_fields_tags_logic_rewritten": 0,
        "build_file_edits": 0,
        "active_catalog_replacement": 0,
        "failures": failures,
        "next_recommended_action": "After marker placement green, authorize D2ZQ actual FIELDS/TAGS logic at markers.",
    }
    wj(out / "dd096zd2zp_fields_tags_marker_placement_manifest.json", manifest)

    print(f"DD096Z-D2ZP FIELDS/TAGS marker placement manifest: {out / 'dd096zd2zp_fields_tags_marker_placement_manifest.json'}")
    print(f"status: {status}; precondition_blockers: {blockers}; marker_status: {marker_status}; source_files_written: {source_files_written}; actual_fields_tags_logic_rewritten: 0; failures: {failures}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
