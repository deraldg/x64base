#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, datetime as dt, json, difflib
from pathlib import Path

REQUIRED = [
    ("DD096ZD2ZN", "docs/datadict/reports/DD096ZD2ZN-surgical-fields-tags-patch-v0/dd096zd2zn_surgical_fields_tags_patch_manifest.json", ["DD096ZD2ZN_SAFE_MARKER_APPLIED_LOGIC_PATCH_DEFERRED"]),
    ("DD096ZD2ZM", "docs/datadict/reports/DD096ZD2ZM-guarded-fields-tags-logic-patch-proposal-v0/dd096zd2zm_guarded_fields_tags_logic_patch_proposal_manifest.json", ["DD096ZD2ZM_GUARDED_FIELDS_TAGS_LOGIC_PATCH_PROPOSAL_READY"]),
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

def read_csv(path: Path):
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))

def cmd_metrics(text: str):
    up = text.upper()
    return {
        "has_bridge_include": int("DDICT_CALLSITE_BRIDGE.HPP" in up),
        "has_d2zn_marker": int("DD096Z-D2ZN BRIDGE HELPER NOTES" in up),
        "has_fields_text": int("FIELDS" in up),
        "has_tags_text": int("TAGS" in up),
        "has_no_fields_found": int("NO_FIELDS_FOUND" in up),
        "has_no_catalog_tags_found": int("NO_CATALOG_TAGS_FOUND" in up),
        "has_cdx_artifact_text": int("CDX ARTIFACT" in up),
        "has_lmdb_mirror_text": int("LMDB MIRROR" in up),
        "has_physical_tags_found_status": int("PHYSICAL_TAGS_FOUND_NO_CATALOG_ROWS" in up),
        "explicit_d2zo_fields_marker": int("DD096Z-D2ZO FIELDS PATCH INSERT HERE" in up),
        "explicit_d2zo_tags_marker": int("DD096Z-D2ZO TAGS PATCH INSERT HERE" in up),
    }

def find_relevant_lines(text: str):
    patterns = [
        "DD096Z-D2ZN", "ddict_callsite_bridge.hpp", "FIELDS", "TAGS",
        "NO_FIELDS_FOUND", "NO_CATALOG_TAGS_FOUND", "CDX artifact", "LMDB mirror",
        "DATA_DICTIONARY_OBJECTS", "DDOBJECT"
    ]
    rows = []
    for n, line in enumerate(text.splitlines(), start=1):
        up = line.upper()
        hits = [p for p in patterns if p.upper() in up]
        if hits:
            rows.append({"line": n, "patterns": ";".join(hits), "text": line[:260]})
    return rows

def source_window(text: str, center: int, radius: int = 10):
    lines = text.splitlines()
    start = max(1, center - radius)
    end = min(len(lines), center + radius)
    return "\n".join(f"{i:5d}: {lines[i-1]}" for i in range(start, end + 1))

def extract_focus_windows(text: str):
    rows = []
    out = {}
    for n, line in enumerate(text.splitlines(), start=1):
        up = line.upper()
        if "NO_FIELDS_FOUND" in up:
            wid = f"FIELDS_NO_FIELDS_FOUND_{n}"
            rows.append({"window_id": wid, "line": n, "kind": "fields_no_fields_found"})
            out[wid] = source_window(text, n, 14)
        if "NO_CATALOG_TAGS_FOUND" in up:
            wid = f"TAGS_NO_CATALOG_TAGS_FOUND_{n}"
            rows.append({"window_id": wid, "line": n, "kind": "tags_no_catalog_tags_found"})
            out[wid] = source_window(text, n, 14)
        if "CDX ARTIFACT" in up or "LMDB MIRROR" in up:
            wid = f"TAGS_PHYSICAL_ARTIFACT_{n}"
            rows.append({"window_id": wid, "line": n, "kind": "tags_physical_artifact"})
            out[wid] = source_window(text, n, 10)
    return rows, out

def fields_patch_template():
    return """// DD096Z-D2ZO FIELDS patch template:
//
// Apply at the point where DDICT FIELDS resolves the requested owner/table token.
//
// const std::string requested_owner = <existing user token variable>;
// const std::string bridge_legacy_owner = dottalk::datadict::ddict_bridge_legacy_owner_token(requested_owner);
// const std::string bridge_x64_owner = dottalk::datadict::ddict_bridge_x64_owner_token(requested_owner);
//
// Existing lookup should try:
//   1. requested_owner
//   2. bridge_legacy_owner if different
//   3. bridge_x64_owner if different and the catalog has x64 rows
//
// Preserve legacy DDOBJECT output as baseline.
// DATA_DICTIONARY_OBJECTS should no longer end as plain NO_FIELDS_FOUND when a bridge owner has field rows.
"""

def tags_patch_template():
    return """// DD096Z-D2ZO TAGS patch template:
//
// Apply where DDICT TAGS has already computed physical DBF/CDX/LMDB artifacts and catalog tag row count.
//
// if (catalog_tag_count == 0 && physical_cdx_exists) {
//     print Physical tags / physical artifact status;
//     Result: PHYSICAL_TAGS_FOUND_NO_CATALOG_ROWS
// }
//
// Only print NO_CATALOG_TAGS_FOUND when no catalog rows and no physical tag metadata/artifact evidence exists.
"""

def smoke_dts():
    return "\n".join([
        "* DD096Z-D2ZO actual FIELDS/TAGS logic patch smoke",
        "* Run after a real recognized-anchor patch and rebuild.",
        "DDICT STATUS",
        "DDICT FIELDS DDOBJECT",
        "DDICT FIELDS DATA_DICTIONARY_OBJECTS",
        "DDICT TAGS DDOBJECT",
        "DDICT TAGS DATA_DICTIONARY_OBJECTS",
        "",
    ])

def maybe_apply_explicit_marker_patch(text: str):
    """Only edits if human-placed D2ZO markers exist. Otherwise refuses actual rewrite."""
    changed = 0
    notes = []
    new_text = text
    fields_marker = "// DD096Z-D2ZO FIELDS PATCH INSERT HERE"
    tags_marker = "// DD096Z-D2ZO TAGS PATCH INSERT HERE"
    if fields_marker in new_text:
        insert = "\n".join([
            "// DD096Z-D2ZO FIELDS bridge marker:",
            "// Resolve requested owner with ddict_bridge_legacy_owner_token and ddict_bridge_x64_owner_token here.",
            "// Actual local variables must be wired by the reviewed source patch.",
        ])
        new_text = new_text.replace(fields_marker, fields_marker + "\n" + insert, 1)
        changed += 1
        notes.append("fields_marker_augmented")
    if tags_marker in new_text:
        insert = "\n".join([
            "// DD096Z-D2ZO TAGS bridge marker:",
            "// If physical CDX/LMDB exists and catalog rows are absent, report PHYSICAL_TAGS_FOUND_NO_CATALOG_ROWS here.",
            "// Actual local variables must be wired by the reviewed source patch.",
        ])
        new_text = new_text.replace(tags_marker, tags_marker + "\n" + insert, 1)
        changed += 1
        notes.append("tags_marker_augmented")
    return new_text, changed, ";".join(notes) if notes else "no_explicit_d2zo_markers_refuse_actual_rewrite"

def main():
    ap = argparse.ArgumentParser(description="DD096Z-D2ZO actual FIELDS/TAGS logic patch guard")
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--run-id", default="DD096ZD2ZO-actual-fields-tags-logic-patch-guard-v0")
    ap.add_argument("--profile", action="append", default=[])
    ap.add_argument("--apply-recognized-patch", action="store_true")
    ap.add_argument("--write-smoke-script", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    out = Path(args.out_dir).resolve()
    gen = out / "generated_actual_fields_tags_logic_patch_guard"
    gen.mkdir(parents=True, exist_ok=True)

    blockers = 0
    pre_rows = []
    for lane, rel, expected in REQUIRED:
        p = repo / rel
        observed = read_json(p).get("status", "MISSING")
        passed = int(observed in expected)
        blockers += 0 if passed else 1
        pre_rows.append({"lane": lane, "manifest_path": str(p), "observed_status": observed, "expected_status": "|".join(expected), "pass": passed})
    wc(gen / "dd096zd2zo_precondition_ledger.csv", pre_rows, ["lane","manifest_path","observed_status","expected_status","pass"])

    cmd_path = repo / "src/cli/cmd_ddict.cpp"
    cmd_text = read_text(cmd_path)
    metrics = cmd_metrics(cmd_text)
    wc(gen / "dd096zd2zo_cmd_ddict_metrics.csv", [{"metric": k, "value": v} for k, v in sorted(metrics.items())], ["metric","value"])
    wc(gen / "dd096zd2zo_relevant_lines.csv", find_relevant_lines(cmd_text), ["line","patterns","text"])

    focus_rows, focus_windows = extract_focus_windows(cmd_text)
    wc(gen / "dd096zd2zo_focus_window_index.csv", focus_rows, ["window_id","line","kind"])
    for wid, txt in focus_windows.items():
        wt(gen / f"{wid}.txt", txt + "\n")

    wt(gen / "DD096ZD2ZO_FIELDS_PATCH_TEMPLATE.cpp.txt", fields_patch_template())
    wt(gen / "DD096ZD2ZO_TAGS_PATCH_TEMPLATE.cpp.txt", tags_patch_template())
    wt(gen / "DD096ZD2ZO_FIELDS_TAGS_LOGIC_SMOKE.dts", smoke_dts())

    new_text, patch_changes, patch_status = maybe_apply_explicit_marker_patch(cmd_text)
    diff = "\n".join(difflib.unified_diff(
        cmd_text.splitlines(),
        new_text.splitlines(),
        fromfile="src/cli/cmd_ddict.cpp.before",
        tofile="src/cli/cmd_ddict.cpp.after",
        lineterm=""
    ))
    wt(gen / "dd096zd2zo_candidate_diff.patch", diff + ("\n" if diff else ""))

    source_files_written = 0
    backups_written = 0
    if args.apply_recognized_patch:
        if blockers:
            raise SystemExit("Precondition blockers present; refusing --apply-recognized-patch.")
        if patch_changes == 0:
            raise SystemExit("No explicit D2ZO markers or recognized safe anchors found; refusing actual FIELDS/TAGS rewrite.")
        backup_root = repo / f"docs/datadict/backups/DD096ZD2ZO-source-backup-{dt.datetime.now().strftime('%Y%m%d_%H%M%S')}"
        backup = backup_root / cmd_path.relative_to(repo)
        backup.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(cmd_path, backup)
        backups_written = 1
        wt(cmd_path, new_text)
        source_files_written = 1

    smoke_written = 0
    if args.write_smoke_script:
        wt(repo / "dottalkpp/data/scripts/DD096ZD2ZO_FIELDS_TAGS_LOGIC_SMOKE.dts", smoke_dts())
        smoke_written = 1

    required_missing = int(not cmd_path.exists())
    failures = blockers + required_missing
    if failures:
        status = "DD096ZD2ZO_ACTUAL_FIELDS_TAGS_LOGIC_PATCH_REVIEW"
    elif args.apply_recognized_patch and source_files_written:
        status = "DD096ZD2ZO_RECOGNIZED_FIELDS_TAGS_PATCH_APPLIED_PENDING_BUILD"
    elif args.apply_recognized_patch and patch_changes == 0:
        status = "DD096ZD2ZO_ACTUAL_FIELDS_TAGS_LOGIC_PATCH_REFUSED_UNRECOGNIZED"
    else:
        status = "DD096ZD2ZO_ACTUAL_FIELDS_TAGS_LOGIC_PATCH_GUARD_READY"

    boundary = [
        {"boundary": "actual_fields_tags_logic_patch_guard", "observed": 1, "required": 1, "pass": 1},
        {"boundary": "actual_fields_tags_logic_rewritten", "observed": source_files_written, "required": 1 if args.apply_recognized_patch and patch_changes else 0, "pass": int(source_files_written == (1 if args.apply_recognized_patch and patch_changes else 0))},
        {"boundary": "build_file_edits", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "active_catalog_replacement", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "active_dbf_cdx_lmdb_mutation", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "help_meta_cmdhelpchk_mutation", "observed": 0, "required": 0, "pass": 1},
    ]
    wc(out / "dd096zd2zo_boundary_ledger.csv", boundary, ["boundary","observed","required","pass"])

    recommendation = "Review focus windows; if no explicit markers are present, create D2ZP with exact local source edits or insert human-reviewed D2ZO markers."
    report = f"""# DD096Z-D2ZO Actual FIELDS/TAGS Logic Patch Guard

Run id: `{args.run_id}`
Status: **{status}**
Created UTC: `{now()}`

## Purpose

D2ZO is the first actual FIELDS/TAGS logic patch guard.

It inspects exact local `cmd_ddict.cpp` anchors and refuses blind rewrites. It only applies a patch when explicit D2ZO patch markers or recognized safe anchors are present.

## Summary

- Precondition blockers: **{blockers}**
- Required files missing: **{required_missing}**
- Focus windows: **{len(focus_rows)}**
- Patch status: **{patch_status}**
- Candidate patch changes: **{patch_changes}**
- Source files written: **{source_files_written}**
- Smoke script written: **{smoke_written}**
- Build file edits: **0**

## Recommendation

{recommendation}
"""
    wt(out / "DD096ZD2ZO_ACTUAL_FIELDS_TAGS_LOGIC_PATCH_GUARD_REPORT.md", report)

    manifest = {
        "contract": "dd096zd2zo_actual_fields_tags_logic_patch_guard_v0",
        "run_id": args.run_id,
        "created_utc": now(),
        "status": status,
        "repo_root": str(repo),
        "profiles": args.profile,
        "precondition_blockers": blockers,
        "required_files_missing": required_missing,
        "focus_windows": len(focus_rows),
        "patch_status": patch_status,
        "candidate_patch_changes": patch_changes,
        "apply_recognized_patch": int(args.apply_recognized_patch),
        "source_files_written": source_files_written,
        "backups_written": backups_written,
        "smoke_script_written": smoke_written,
        "build_file_edits": 0,
        "active_catalog_replacement": 0,
        "failures": failures,
        "next_recommended_action": recommendation,
    }
    wj(out / "dd096zd2zo_actual_fields_tags_logic_patch_guard_manifest.json", manifest)

    print(f"DD096Z-D2ZO actual FIELDS/TAGS logic patch guard manifest: {out / 'dd096zd2zo_actual_fields_tags_logic_patch_guard_manifest.json'}")
    print(f"status: {status}; precondition_blockers: {blockers}; focus_windows: {len(focus_rows)}; patch_status: {patch_status}; source_files_written: {source_files_written}; failures: {failures}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
