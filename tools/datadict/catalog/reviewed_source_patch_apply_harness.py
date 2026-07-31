#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, datetime as dt, hashlib, json, shutil
from pathlib import Path

REQUIRED = [
    ("DD096ZD2ZR", "docs/datadict/reports/DD096ZD2ZR-marker-local-patch-readiness-v0/dd096zd2zr_marker_local_patch_readiness_manifest.json", ["DD096ZD2ZR_MARKER_LOCAL_PATCH_READINESS_READY"]),
    ("DD096ZD2ZQ", "docs/datadict/reports/DD096ZD2ZQ-marker-aware-fields-tags-workbench-v0/dd096zd2zq_marker_aware_fields_tags_workbench_manifest.json", ["DD096ZD2ZQ_MARKER_AWARE_FIELDS_TAGS_WORKBENCH_READY"]),
]

FIELDS_MARKER = "DD096Z-D2ZP FIELDS OWNER-LOOKUP PATCH MARKER"
TAGS_MARKER = "DD096Z-D2ZP TAGS PHYSICAL-REPORT PATCH MARKER"
REQUIRED_CANDIDATE_TOKENS = [
    "ddict_callsite_bridge.hpp",
    "ddict_bridge_legacy_owner_token",
    "ddict_bridge_x64_owner_token",
    "PHYSICAL_TAGS_FOUND_NO_CATALOG_ROWS",
]

def now():
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")

def sha256(path: Path) -> str:
    if not path.exists() or not path.is_file():
        return ""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

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

def marker_line(text: str, marker: str) -> int:
    for i, line in enumerate(text.splitlines(), start=1):
        if marker in line:
            return i
    return 0

def window(text: str, line_no: int, radius: int = 22):
    lines = text.splitlines()
    if line_no <= 0:
        return ""
    start = max(1, line_no - radius)
    end = min(len(lines), line_no + radius)
    return "\n".join(f"{i:5d}: {lines[i-1]}" for i in range(start, end + 1)) + "\n"

def strip_cpp_comments_for_validation(text: str) -> str:
    """Remove C/C++ comments before executable-forbidden-term validation."""
    out = []
    i = 0
    n = len(text)
    in_block = False
    in_line = False
    in_str = False
    in_char = False
    escape = False
    while i < n:
        c = text[i]
        nxt = text[i + 1] if i + 1 < n else ""
        if in_block:
            if c == "*" and nxt == "/":
                in_block = False
                i += 2
                continue
            if c == "\n":
                out.append("\n")
            i += 1
            continue
        if in_line:
            if c == "\n":
                in_line = False
                out.append(c)
            i += 1
            continue
        if not in_str and not in_char and c == "/" and nxt == "*":
            in_block = True
            i += 2
            continue
        if not in_str and not in_char and c == "/" and nxt == "/":
            in_line = True
            i += 2
            continue
        out.append(c)
        if escape:
            escape = False
        elif c == "\\" and (in_str or in_char):
            escape = True
        elif c == '"' and not in_char:
            in_str = not in_str
        elif c == "'" and not in_str:
            in_char = not in_char
        i += 1
    return "".join(out)

def candidate_validation(candidate_text: str, base_text: str):
    rows = []
    up = candidate_text.upper()
    base_up = base_text.upper()
    def add(check, observed, required, passed, note):
        rows.append({"check": check, "observed": observed, "required": required, "pass": int(passed), "note": note})
    add("candidate_nonempty", int(bool(candidate_text)), 1, bool(candidate_text), "candidate source must be readable")
    add("fields_marker_present", int(FIELDS_MARKER in candidate_text), 1, FIELDS_MARKER in candidate_text, "FIELDS marker should be preserved")
    add("tags_marker_present", int(TAGS_MARKER in candidate_text), 1, TAGS_MARKER in candidate_text, "TAGS marker should be preserved")
    add("bridge_include_present", int("DDICT_CALLSITE_BRIDGE.HPP" in up), 1, "DDICT_CALLSITE_BRIDGE.HPP" in up, "bridge include required")
    add("legacy_bridge_helper_present", int("DDICT_BRIDGE_LEGACY_OWNER_TOKEN" in up), 1, "DDICT_BRIDGE_LEGACY_OWNER_TOKEN" in up, "FIELDS bridge helper should be used")
    add("x64_bridge_helper_present", int("DDICT_BRIDGE_X64_OWNER_TOKEN" in up), 1, "DDICT_BRIDGE_X64_OWNER_TOKEN" in up, "x64 bridge helper should be used")
    add("physical_status_present", int("PHYSICAL_TAGS_FOUND_NO_CATALOG_ROWS" in up), 1, "PHYSICAL_TAGS_FOUND_NO_CATALOG_ROWS" in up, "TAGS physical bridge result required")
    add("legacy_ddobject_preserved", int("DDOBJECT" in up), 1, "DDOBJECT" in up, "legacy DDOBJECT surface must remain present")
    code_for_forbidden_scan = strip_cpp_comments_for_validation(candidate_text).upper()
    add("no_forbidden_active_mutation_terms", int(not any(x in code_for_forbidden_scan for x in ["PACK", "ZAP", "DELETE FILE", "REMOVE("])), 1, not any(x in code_for_forbidden_scan for x in ["PACK", "ZAP", "DELETE FILE", "REMOVE("]), "executable source patch should not introduce destructive active mutations; comments are ignored")
    add("candidate_differs_from_base", int(candidate_text != base_text), 1, candidate_text != base_text, "candidate must actually differ from current source")
    return rows

def smoke_dts():
    return "\n".join([
        "* DD096Z-D2ZS reviewed source patch smoke",
        "* Run after reviewed source patch is applied and binary is rebuilt.",
        "DDICT STATUS",
        "DDICT FIELDS DDOBJECT",
        "DDICT FIELDS DATA_DICTIONARY_OBJECTS",
        "DDICT TAGS DDOBJECT",
        "DDICT TAGS DATA_DICTIONARY_OBJECTS",
        "",
    ])

def reviewer_instructions(base_hash: str):
    return f"""# DD096Z-D2ZS Reviewed Source Patch Instructions

D2ZS is a human-reviewed apply harness. It does not synthesize the C++ logic patch automatically.

## Base source hash

`{base_hash}`

## Edit target

Copy or edit this staged file:

```text
docs/datadict/reviews/DD096ZD2ZS/cmd_ddict.cpp.review_candidate
```

The reviewed candidate must preserve:

- `DDICT FIELDS DDOBJECT`
- `DDICT TAGS DDOBJECT`
- D2ZP marker comments
- D2ZN bridge helper notes
- `ddict_callsite_bridge.hpp` include

## Required behavior in candidate source

FIELDS:

- Use `ddict_bridge_legacy_owner_token(...)`
- Use `ddict_bridge_x64_owner_token(...)`
- Keep legacy field lookup working
- Avoid plain final `NO_FIELDS_FOUND` for `DATA_DICTIONARY_OBJECTS` when bridged metadata is available through the legacy owner path

TAGS:

- Preserve physical DBF/CDX/LMDB reporting
- Use result/status text `PHYSICAL_TAGS_FOUND_NO_CATALOG_ROWS` when physical artifacts exist but catalog tag rows are absent
- Avoid plain `NO_CATALOG_TAGS_FOUND` in that physical-artifact case

## Apply command shape

```powershell
$py12 = "D:\\code\\ccode\\build\\vcpkg_installed\\x64-windows\\tools\\python3\\python.exe"

& $py12 .\\tools\\datadict\\catalog\\reviewed_source_patch_apply_harness.py `
  --repo-root D:\\code\\ccode `
  --out-dir D:\\code\\ccode\\docs\\datadict\\reports\\DD096ZD2ZS-reviewed-source-patch-apply-harness-v0 `
  --run-id DD096ZD2ZS-reviewed-source-patch-apply-harness-v0 `
  --profile ENGINE `
  --profile PROFESSIONAL `
  --candidate-source docs\\datadict\\reviews\\DD096ZD2ZS\\cmd_ddict.cpp.review_candidate `
  --apply-reviewed-source `
  --write-smoke-script
```
"""

def main():
    ap = argparse.ArgumentParser(description="DD096Z-D2ZS reviewed source patch apply harness")
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--run-id", default="DD096ZD2ZS-reviewed-source-patch-apply-harness-v0")
    ap.add_argument("--profile", action="append", default=[])
    ap.add_argument("--stage-review-copy", action="store_true")
    ap.add_argument("--candidate-source", default="")
    ap.add_argument("--apply-reviewed-source", action="store_true")
    ap.add_argument("--write-smoke-script", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    out = Path(args.out_dir).resolve()
    gen = out / "generated_reviewed_source_patch_apply_harness"
    gen.mkdir(parents=True, exist_ok=True)

    blockers = 0
    pre_rows = []
    for lane, rel, expected in REQUIRED:
        p = repo / rel
        observed = read_json(p).get("status", "MISSING")
        passed = int(observed in expected)
        blockers += 0 if passed else 1
        pre_rows.append({"lane": lane, "manifest_path": str(p), "observed_status": observed, "expected_status": "|".join(expected), "pass": passed})
    wc(gen / "dd096zd2zs_precondition_ledger.csv", pre_rows, ["lane","manifest_path","observed_status","expected_status","pass"])

    cmd_path = repo / "src/cli/cmd_ddict.cpp"
    base_text = read_text(cmd_path)
    base_hash = sha256(cmd_path)
    fields_line = marker_line(base_text, FIELDS_MARKER)
    tags_line = marker_line(base_text, TAGS_MARKER)
    required_missing = int(not cmd_path.exists()) + int(fields_line == 0) + int(tags_line == 0)

    wt(gen / "DD096ZD2ZS_FIELDS_BASE_WINDOW.txt", window(base_text, fields_line))
    wt(gen / "DD096ZD2ZS_TAGS_BASE_WINDOW.txt", window(base_text, tags_line))
    wt(gen / "DD096ZD2ZS_REVIEWED_PATCH_INSTRUCTIONS.md", reviewer_instructions(base_hash))
    wt(gen / "DD096ZD2ZS_REVIEWED_SOURCE_PATCH_SMOKE.dts", smoke_dts())

    stage_copy_written = 0
    review_root = repo / "docs/datadict/reviews/DD096ZD2ZS"
    if args.stage_review_copy:
        wt(review_root / "cmd_ddict.cpp.review_candidate", base_text)
        wt(review_root / "DD096ZD2ZS_REVIEWED_PATCH_INSTRUCTIONS.md", reviewer_instructions(base_hash))
        wt(review_root / "DD096ZD2ZS_FIELDS_BASE_WINDOW.txt", window(base_text, fields_line))
        wt(review_root / "DD096ZD2ZS_TAGS_BASE_WINDOW.txt", window(base_text, tags_line))
        stage_copy_written = 1

    candidate_rows = []
    candidate_valid = 0
    candidate_source = ""
    candidate_path = None
    if args.candidate_source:
        candidate_path = Path(args.candidate_source)
        if not candidate_path.is_absolute():
            candidate_path = repo / candidate_path
        candidate_source = read_text(candidate_path)
        candidate_rows = candidate_validation(candidate_source, base_text)
        candidate_valid = int(candidate_rows and all(int(r["pass"]) == 1 for r in candidate_rows))
        wc(gen / "dd096zd2zs_candidate_validation.csv", candidate_rows, ["check","observed","required","pass","note"])
    else:
        wc(gen / "dd096zd2zs_candidate_validation.csv", [], ["check","observed","required","pass","note"])

    source_files_written = 0
    backups_written = 0
    backup_root = repo / f"docs/datadict/backups/DD096ZD2ZS-source-backup-{dt.datetime.now().strftime('%Y%m%d_%H%M%S')}"
    if args.apply_reviewed_source:
        if blockers or required_missing:
            raise SystemExit("Precondition or required-source blockers present; refusing --apply-reviewed-source.")
        if not args.candidate_source:
            raise SystemExit("--candidate-source is required with --apply-reviewed-source.")
        if not candidate_valid:
            raise SystemExit("Candidate validation failed; refusing --apply-reviewed-source.")
        backup = backup_root / cmd_path.relative_to(repo)
        backup.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(cmd_path, backup)
        backups_written = 1
        wt(cmd_path, candidate_source)
        source_files_written = 1

    smoke_written = 0
    if args.write_smoke_script:
        wt(repo / "dottalkpp/data/scripts/DD096ZD2ZS_REVIEWED_SOURCE_PATCH_SMOKE.dts", smoke_dts())
        smoke_written = 1

    failures = blockers + required_missing
    if failures:
        status = "DD096ZD2ZS_REVIEWED_SOURCE_PATCH_APPLY_HARNESS_REVIEW"
    elif args.apply_reviewed_source and source_files_written:
        status = "DD096ZD2ZS_REVIEWED_SOURCE_PATCH_APPLIED_PENDING_BUILD"
    elif args.candidate_source and candidate_valid:
        status = "DD096ZD2ZS_REVIEWED_SOURCE_PATCH_CANDIDATE_VALIDATED"
    else:
        status = "DD096ZD2ZS_REVIEWED_SOURCE_PATCH_APPLY_HARNESS_READY"

    boundary = [
        {"boundary": "reviewed_source_patch_apply_harness", "observed": 1, "required": 1, "pass": 1},
        {"boundary": "source_files_written", "observed": source_files_written, "required": 1 if args.apply_reviewed_source else 0, "pass": int(source_files_written == (1 if args.apply_reviewed_source else 0))},
        {"boundary": "build_file_edits", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "active_catalog_replacement", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "active_dbf_cdx_lmdb_mutation", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "help_meta_cmdhelpchk_mutation", "observed": 0, "required": 0, "pass": 1},
    ]
    wc(out / "dd096zd2zs_boundary_ledger.csv", boundary, ["boundary","observed","required","pass"])

    report = f"""# DD096Z-D2ZS Reviewed Source Patch Apply Harness

Run id: `{args.run_id}`
Status: **{status}**
Created UTC: `{now()}`

## Purpose

D2ZS stages and validates a human-reviewed `cmd_ddict.cpp` patch for the actual FIELDS/TAGS logic.

It does not generate a blind logic rewrite. It applies source only when a candidate source file is supplied and passes validation.

## Summary

- Precondition blockers: **{blockers}**
- Required source/marker missing count: **{required_missing}**
- Base hash: `{base_hash}`
- FIELDS marker line: **{fields_line}**
- TAGS marker line: **{tags_line}**
- Review copy staged: **{stage_copy_written}**
- Candidate supplied: **{int(bool(args.candidate_source))}**
- Candidate valid: **{candidate_valid}**
- Source files written: **{source_files_written}**
- Backups written: **{backups_written}**
- Smoke script written: **{smoke_written}**

## Next

Edit the staged review candidate, rerun with `--candidate-source`, and only then apply reviewed source.
"""
    wt(out / "DD096ZD2ZS_REVIEWED_SOURCE_PATCH_APPLY_HARNESS_REPORT.md", report)

    manifest = {
        "contract": "dd096zd2zs_reviewed_source_patch_apply_harness_v0",
        "run_id": args.run_id,
        "created_utc": now(),
        "status": status,
        "repo_root": str(repo),
        "profiles": args.profile,
        "precondition_blockers": blockers,
        "required_source_marker_missing": required_missing,
        "base_hash": base_hash,
        "fields_marker_line": fields_line,
        "tags_marker_line": tags_line,
        "stage_review_copy": int(args.stage_review_copy),
        "stage_copy_written": stage_copy_written,
        "candidate_source": str(candidate_path) if candidate_path else "",
        "candidate_valid": candidate_valid,
        "apply_reviewed_source": int(args.apply_reviewed_source),
        "source_files_written": source_files_written,
        "backups_written": backups_written,
        "smoke_script_written": smoke_written,
        "build_file_edits": 0,
        "active_catalog_replacement": 0,
        "failures": failures,
        "next_recommended_action": "Edit staged review candidate, validate candidate, then apply reviewed source and rebuild.",
    }
    wj(out / "dd096zd2zs_reviewed_source_patch_apply_harness_manifest.json", manifest)

    print(f"DD096Z-D2ZS reviewed source patch apply harness manifest: {out / 'dd096zd2zs_reviewed_source_patch_apply_harness_manifest.json'}")
    print(f"status: {status}; precondition_blockers: {blockers}; required_source_marker_missing: {required_missing}; stage_copy_written: {stage_copy_written}; candidate_valid: {candidate_valid}; source_files_written: {source_files_written}; failures: {failures}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
