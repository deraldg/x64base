#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, datetime as dt, json, shutil
from pathlib import Path

REQUIRED = [
    ("DD096ZD2ZM", "docs/datadict/reports/DD096ZD2ZM-guarded-fields-tags-logic-patch-proposal-v0/dd096zd2zm_guarded_fields_tags_logic_patch_proposal_manifest.json", ["DD096ZD2ZM_GUARDED_FIELDS_TAGS_LOGIC_PATCH_PROPOSAL_READY"]),
    ("DD096ZD2ZK", "docs/datadict/reports/DD096ZD2ZK-guarded-ddict-fields-tags-patch-v0/dd096zd2zk_guarded_ddict_fields_tags_patch_manifest.json", ["DD096ZD2ZK_SAFE_SOURCE_PATCH_APPLIED_CALLSITE_REVIEW_PENDING"]),
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

def smoke_dts() -> str:
    return "\n".join([
        "* DD096Z-D2ZN surgical FIELDS/TAGS patch smoke",
        "* Read-only smoke after source patch and rebuild.",
        "DDICT STATUS",
        "DDICT FIELDS DDOBJECT",
        "DDICT FIELDS DATA_DICTIONARY_OBJECTS",
        "DDICT TAGS DDOBJECT",
        "DDICT TAGS DATA_DICTIONARY_OBJECTS",
        "",
    ])

def source_helpers_block() -> str:
    return "\n".join([
        "// DD096Z-D2ZN bridge helper notes:",
        "// The resolver bridge is intentionally available to DDICT call sites through:",
        "//   dottalk::datadict::ddict_bridge_legacy_owner_token(token)",
        "//   dottalk::datadict::ddict_bridge_x64_owner_token(token)",
        "// The actual call-site logic should use these helpers only at owner/table lookup boundaries.",
    ])

def cmd_metrics(text: str):
    up = text.upper()
    return {
        "has_callsite_bridge_include": int("DDICT_CALLSITE_BRIDGE.HPP" in up),
        "has_catalog_resolver_include": int("DDICT_CATALOG_RESOLVER.HPP" in up),
        "has_d2zn_marker": int("DD096Z-D2ZN" in up),
        "fields_mentions": up.count("FIELDS"),
        "tags_mentions": up.count("TAGS"),
        "no_fields_found_mentions": up.count("NO_FIELDS_FOUND"),
        "no_catalog_tags_found_mentions": up.count("NO_CATALOG_TAGS_FOUND"),
    }

def make_patch_notes(metrics: dict, anchor_count: int) -> str:
    return f'''# DD096Z-D2ZN Surgical Patch Notes

D2ZN is intentionally conservative.

## Current source facts

- Anchor lines from D2ZM: {anchor_count}
- `ddict_callsite_bridge.hpp` include present: {metrics.get("has_callsite_bridge_include", 0)}
- `ddict_catalog_resolver.hpp` include present: {metrics.get("has_catalog_resolver_include", 0)}
- FIELDS mentions: {metrics.get("fields_mentions", 0)}
- TAGS mentions: {metrics.get("tags_mentions", 0)}
- NO_FIELDS_FOUND mentions: {metrics.get("no_fields_found_mentions", 0)}
- NO_CATALOG_TAGS_FOUND mentions: {metrics.get("no_catalog_tags_found_mentions", 0)}

## D2ZN rule

This package does not blind-rewrite `cmd_ddict.cpp`.

It applies only a sentinel/source-comment marker and smoke script unless a later tool version has exact recognized anchors. The real logic patch should be D2ZO once the D2ZM/D2ZN anchor evidence is reviewed.

## Required actual behavior for D2ZO

FIELDS:
- Normalize requested token through the bridge.
- Keep `DDICT FIELDS DDOBJECT` green.
- Make `DDICT FIELDS DATA_DICTIONARY_OBJECTS` return compatible fields or an honest bridge status.

TAGS:
- Preserve physical artifact detection.
- If DBF/CDX/LMDB exists but catalog tag rows are absent, report `PHYSICAL_TAGS_FOUND_NO_CATALOG_ROWS`.
- Do not return plain `NO_CATALOG_TAGS_FOUND` when physical tags are available.
'''

def add_marker_if_safe(text: str):
    if "DD096Z-D2ZN bridge helper notes" in text:
        return text, 0, "marker_already_present"
    if "ddict_callsite_bridge.hpp" not in text:
        return text, 0, "bridge_include_missing_refuse_marker"
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if "ddict_callsite_bridge.hpp" in line:
            lines.insert(i + 1, source_helpers_block())
            return "\n".join(lines) + ("\n" if text.endswith("\n") else ""), 1, "marker_inserted"
    return text, 0, "include_anchor_not_found"

def build_review_matrix(anchor_rows):
    matrix = []
    for r in anchor_rows:
        cls = r.get("classification", "")
        area = "related"
        if "fields" in cls:
            area = "FIELDS"
        elif "tags" in cls:
            area = "TAGS"
        matrix.append({
            "area": area,
            "line": r.get("line", ""),
            "classification": cls,
            "patterns": r.get("patterns", ""),
            "text": r.get("text", ""),
            "d2zo_action": "review_for_exact_logic_patch",
        })
    return matrix

def main():
    ap = argparse.ArgumentParser(description="DD096Z-D2ZN surgical FIELDS/TAGS patch guard")
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--run-id", default="DD096ZD2ZN-surgical-fields-tags-patch-v0")
    ap.add_argument("--profile", action="append", default=[])
    ap.add_argument("--apply-safe-marker", action="store_true")
    ap.add_argument("--write-smoke-script", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    out = Path(args.out_dir).resolve()
    gen = out / "generated_surgical_fields_tags_patch"
    gen.mkdir(parents=True, exist_ok=True)

    blockers = 0
    pre_rows = []
    for lane, rel, expected in REQUIRED:
        p = repo / rel
        observed = read_json(p).get("status", "MISSING")
        passed = int(observed in expected)
        blockers += 0 if passed else 1
        pre_rows.append({"lane": lane, "manifest_path": str(p), "observed_status": observed, "expected_status": "|".join(expected), "pass": passed})
    wc(gen / "dd096zd2zn_precondition_ledger.csv", pre_rows, ["lane","manifest_path","observed_status","expected_status","pass"])

    cmd_path = repo / "src/cli/cmd_ddict.cpp"
    cmd_text = read_text(cmd_path)
    metrics = cmd_metrics(cmd_text)
    wc(gen / "dd096zd2zn_cmd_ddict_metrics.csv", [{"metric": k, "value": v} for k, v in sorted(metrics.items())], ["metric", "value"])

    anchors_path = repo / "docs/datadict/reports/DD096ZD2ZM-guarded-fields-tags-logic-patch-proposal-v0/generated_fields_tags_logic_patch_proposal/dd096zd2zm_anchor_lines.csv"
    anchors = read_csv(anchors_path)
    wc(gen / "dd096zd2zn_review_matrix.csv", build_review_matrix(anchors), ["area","line","classification","patterns","text","d2zo_action"])

    patched_cmd, marker_changed, marker_status = add_marker_if_safe(cmd_text)
    wt(gen / "cmd_ddict.cpp.d2zn_marker_preview", patched_cmd if patched_cmd else "")

    source_files_written = 0
    backups_written = 0
    backup_root = repo / f"docs/datadict/backups/DD096ZD2ZN-source-backup-{dt.datetime.now().strftime('%Y%m%d_%H%M%S')}"
    if args.apply_safe_marker:
        if blockers:
            raise SystemExit("Precondition blockers present; refusing --apply-safe-marker.")
        if marker_changed:
            backup = backup_root / cmd_path.relative_to(repo)
            backup.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(cmd_path, backup)
            backups_written += 1
            wt(cmd_path, patched_cmd)
            source_files_written += 1

    smoke_written = 0
    smoke = smoke_dts()
    wt(gen / "DD096ZD2ZN_SURGICAL_FIELDS_TAGS_SMOKE.dts", smoke)
    if args.write_smoke_script:
        wt(repo / "dottalkpp/data/scripts/DD096ZD2ZN_SURGICAL_FIELDS_TAGS_SMOKE.dts", smoke)
        smoke_written = 1

    notes = make_patch_notes(metrics, len(anchors))
    wt(gen / "DD096ZD2ZN_SURGICAL_PATCH_NOTES.md", notes)

    required_missing = int(not cmd_path.exists())
    failures = blockers + required_missing
    if failures:
        status = "DD096ZD2ZN_SURGICAL_FIELDS_TAGS_PATCH_REVIEW"
    elif args.apply_safe_marker:
        status = "DD096ZD2ZN_SAFE_MARKER_APPLIED_LOGIC_PATCH_DEFERRED"
    else:
        status = "DD096ZD2ZN_SURGICAL_FIELDS_TAGS_PATCH_READY"

    boundary = [
        {"boundary": "surgical_fields_tags_patch_guard", "observed": 1, "required": 1, "pass": 1},
        {"boundary": "actual_fields_tags_logic_rewritten", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "safe_marker_written", "observed": source_files_written, "required": 1 if args.apply_safe_marker and marker_changed else 0, "pass": int(source_files_written == (1 if args.apply_safe_marker and marker_changed else 0))},
        {"boundary": "build_file_edits", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "active_catalog_replacement", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "active_dbf_cdx_lmdb_mutation", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "help_meta_cmdhelpchk_mutation", "observed": 0, "required": 0, "pass": 1},
    ]
    wc(out / "dd096zd2zn_boundary_ledger.csv", boundary, ["boundary","observed","required","pass"])

    report = f'''# DD096Z-D2ZN Surgical FIELDS/TAGS Patch Guard

Run id: `{args.run_id}`
Status: **{status}**
Created UTC: `{now()}`

## Purpose

D2ZN is the guard immediately before the actual FIELDS/TAGS logic rewrite.

It validates that D2ZM proposal evidence is present, creates a review matrix from anchor lines, and optionally applies only a safe source marker near the bridge include.

## Summary

- Precondition blockers: **{blockers}**
- Required files missing: **{required_missing}**
- D2ZM anchor lines: **{len(anchors)}**
- Marker status: **{marker_status}**
- Safe marker/source files written: **{source_files_written}**
- Smoke script written: **{smoke_written}**
- Actual FIELDS/TAGS logic rewritten: **0**
- Build file edits: **0**

## Next lane

D2ZO should be the real surgical source patch, using `dd096zd2zn_review_matrix.csv` and local code review.
'''
    wt(out / "DD096ZD2ZN_SURGICAL_FIELDS_TAGS_PATCH_REPORT.md", report)

    manifest = {
        "contract": "dd096zd2zn_surgical_fields_tags_patch_v0",
        "run_id": args.run_id,
        "created_utc": now(),
        "status": status,
        "repo_root": str(repo),
        "profiles": args.profile,
        "precondition_blockers": blockers,
        "required_files_missing": required_missing,
        "d2zm_anchor_lines": len(anchors),
        "marker_status": marker_status,
        "apply_safe_marker": int(args.apply_safe_marker),
        "source_files_written": source_files_written,
        "backups_written": backups_written,
        "smoke_script_written": smoke_written,
        "actual_fields_tags_logic_rewritten": 0,
        "build_file_edits": 0,
        "active_catalog_replacement": 0,
        "failures": failures,
        "next_recommended_action": "Review D2ZN matrix and authorize D2ZO actual FIELDS/TAGS logic rewrite.",
    }
    wj(out / "dd096zd2zn_surgical_fields_tags_patch_manifest.json", manifest)

    print(f"DD096Z-D2ZN surgical FIELDS/TAGS patch manifest: {out / 'dd096zd2zn_surgical_fields_tags_patch_manifest.json'}")
    print(f"status: {status}; precondition_blockers: {blockers}; d2zm_anchor_lines: {len(anchors)}; marker_status: {marker_status}; actual_fields_tags_logic_rewritten: 0; failures: {failures}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
