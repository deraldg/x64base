#!/usr/bin/env python3
from __future__ import annotations
import argparse
import csv
import datetime as dt
import json
from pathlib import Path
from typing import Dict, List

TERMS = [
    "DDICT",
    "DDOBJECT",
    "DDATTR",
    "DDEDGE",
    "DDEVID",
    "DDGATE",
    "DDRUN",
    "DATA_DICTIONARY_OBJECTS",
    "DATA_DICTIONARY_OBJECT_ATTRIBUTES",
    "DATA_DICTIONARY_RELATION_EDGES",
    "DATA_DICTIONARY_EVIDENCE_RECORDS",
    "DATA_DICTIONARY_GATE_RECORDS",
    "DATA_DICTIONARY_RUNS",
    "CATALOG_OBJECT_ID",
    "CATALOG_ATTRIBUTE_NAME",
]

SOURCE_EXTS = {
    ".cpp", ".cxx", ".cc", ".c", ".hpp", ".h", ".hh", ".hxx",
    ".dts", ".dtschema", ".md", ".csv", ".json", ".ps1", ".py"
}

SKIP_PARTS = {
    ".git", ".vs", "build", "out", "__pycache__", ".venv", "node_modules"
}

def now():
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")

def wt(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")

def wj(path: Path, obj):
    wt(path, json.dumps(obj, indent=2, sort_keys=True) + "\n")

def wc(path: Path, rows: List[Dict], fields: List[str]):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        w.writeheader()
        for row in rows:
            w.writerow({k: row.get(k, "") for k in fields})

def safe_read(path: Path, max_bytes: int = 2_000_000) -> str:
    try:
        if path.stat().st_size > max_bytes:
            return ""
        return path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return ""

def should_skip(path: Path) -> bool:
    parts = {p.lower() for p in path.parts}
    return bool(parts.intersection(SKIP_PARTS))

def score_file(text: str) -> Dict[str, int]:
    upper = text.upper()
    return {term: upper.count(term.upper()) for term in TERMS}

def classify(path: Path, counts: Dict[str, int]) -> str:
    name = path.name.lower()
    rel = str(path).lower()
    if counts.get("DDICT", 0) and path.suffix.lower() in {".cpp", ".hpp", ".h", ".cxx", ".cc"}:
        return "DDICT_SOURCE_CANDIDATE"
    if any(counts.get(t, 0) for t in ["DDOBJECT", "DDATTR", "DDEDGE", "DDEVID", "DDGATE", "DDRUN"]) and path.suffix.lower() in {".cpp", ".hpp", ".h", ".cxx", ".cc"}:
        return "LEGACY_DD_SOURCE_CANDIDATE"
    if any(counts.get(t, 0) for t in ["DATA_DICTIONARY_OBJECTS", "CATALOG_OBJECT_ID"]) and path.suffix.lower() in {".cpp", ".hpp", ".h", ".cxx", ".cc"}:
        return "X64_DATADICT_SOURCE_CANDIDATE"
    if "datadict" in rel or "data_dictionary" in rel:
        return "DATADICT_ARTIFACT"
    if "help" in name or "cmdhelp" in name:
        return "HELP_BOUNDARY_CANDIDATE"
    return "TERM_MATCH"

def main():
    ap = argparse.ArgumentParser(description="DD096ZF-R source touchpoint discovery/correction")
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--run-id", default="DD096ZFR-source-touchpoint-discovery-v0")
    ap.add_argument("--max-results", type=int, default=500)
    ap.add_argument("--profile", action="append", default=[])
    ap.add_argument("--fail-on-review", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    out = Path(args.out_dir).resolve()
    gen = out / "generated_source_touchpoint_discovery"
    gen.mkdir(parents=True, exist_ok=True)

    candidates = []
    scanned = 0
    skipped_large = 0

    for path in sorted(repo.rglob("*")):
        if should_skip(path):
            continue
        if not path.is_file():
            continue
        if path.suffix.lower() not in SOURCE_EXTS:
            continue
        scanned += 1
        if path.stat().st_size > 2_000_000:
            skipped_large += 1
            continue
        text = safe_read(path)
        if not text:
            continue
        counts = score_file(text)
        total = sum(counts.values())
        if total <= 0:
            continue
        rel = str(path.relative_to(repo))
        cls = classify(path.relative_to(repo), counts)
        candidates.append({
            "path": rel,
            "suffix": path.suffix.lower(),
            "class": cls,
            "total_hits": total,
            **{f"count_{term.lower()}": counts[term] for term in TERMS},
            "source_edits_in_this_package": 0,
        })

    candidates.sort(key=lambda r: (r["class"] != "DDICT_SOURCE_CANDIDATE", -int(r["total_hits"]), r["path"]))
    limited = candidates[: args.max_results]

    fields = ["path", "suffix", "class", "total_hits"] + [f"count_{term.lower()}" for term in TERMS] + ["source_edits_in_this_package"]
    wc(gen / "dd096zfr_source_touchpoint_candidates.csv", limited, fields)

    class_counts: Dict[str, int] = {}
    for row in candidates:
        class_counts[row["class"]] = class_counts.get(row["class"], 0) + 1
    wc(gen / "dd096zfr_source_touchpoint_class_summary.csv",
       [{"class": k, "count": v} for k, v in sorted(class_counts.items())],
       ["class", "count"])

    source_candidates = [r for r in candidates if "SOURCE_CANDIDATE" in r["class"]]
    prioritized = source_candidates[:50]
    wc(gen / "dd096zfr_prioritized_source_patch_candidates.csv", prioritized, fields)

    old_guess_rows = [
        {"old_guess_path": "dottalkpp/src/cmd_ddict.cpp", "observed_exists_in_dd096zf": 0, "replacement_policy": "Use discovery candidates, not guessed paths."},
        {"old_guess_path": "dottalkpp/src/cmd_datadict.cpp", "observed_exists_in_dd096zf": 0, "replacement_policy": "Use discovery candidates, not guessed paths."},
        {"old_guess_path": "dottalkpp/src/cmd_help.cpp", "observed_exists_in_dd096zf": 0, "replacement_policy": "Use discovery candidates, not guessed paths."},
        {"old_guess_path": "dottalkpp/include/xbase_cli.hpp", "observed_exists_in_dd096zf": 0, "replacement_policy": "Use discovery candidates, not guessed paths."},
        {"old_guess_path": "dottalkpp/include/xbase_64.hpp", "observed_exists_in_dd096zf": 0, "replacement_policy": "Use discovery candidates, not guessed paths."},
        {"old_guess_path": "dottalkpp/include/xbase.hpp", "observed_exists_in_dd096zf": 0, "replacement_policy": "Use discovery candidates, not guessed paths."},
    ]
    wc(gen / "dd096zfr_old_guess_path_correction.csv", old_guess_rows,
       ["old_guess_path", "observed_exists_in_dd096zf", "replacement_policy"])

    boundary = [
        ("source_touchpoint_discovery_only", 1, 1, 1),
        ("source_edits", 0, 0, 1),
        ("build_file_edits", 0, 0, 1),
        ("active_catalog_replacement", 0, 0, 1),
        ("active_catalog_dbf_copy_or_write", 0, 0, 1),
        ("candidate_cdx_lmdb_rebuild", 0, 0, 1),
        ("active_cdx_lmdb_rebuild", 0, 0, 1),
        ("workspace_schema_mutation", 0, 0, 1),
        ("help_meta_cmdhelpchk_mutation", 0, 0, 1),
        ("manual_publication_mutation", 0, 0, 1),
    ]
    wc(out / "dd096zfr_no_mutation_boundary_ledger.csv",
       [{"boundary": a, "observed": b, "required": c, "pass": d} for a,b,c,d in boundary],
       ["boundary", "observed", "required", "pass"])

    gates = [
        {"gate": "repo_scanned", "expected": ">0", "observed": scanned, "pass": int(scanned > 0)},
        {"gate": "term_candidates_found", "expected": ">0", "observed": len(candidates), "pass": int(len(candidates) > 0)},
        {"gate": "source_candidates_found", "expected": "review", "observed": len(source_candidates), "pass": 1},
        {"gate": "source_edits_performed", "expected": 0, "observed": 0, "pass": 1},
    ]
    failures = sum(1 for g in gates if int(g["pass"]) != 1)
    wc(out / "dd096zfr_gate_ledger.csv", gates, ["gate", "expected", "observed", "pass"])

    status = "DD096ZFR_SOURCE_TOUCHPOINT_DISCOVERY_READY" if failures == 0 else "DD096ZFR_SOURCE_TOUCHPOINT_DISCOVERY_REVIEW"

    report = f"""# DD096ZF-R Source Touchpoint Discovery / Correction

Run id: `{args.run_id}`
Status: **{status}**
Created UTC: `{now()}`

## Purpose

DD096ZF-R corrects the DD096Z-F source-touchpoint assumption problem.

DD096Z-F correctly designed the resolver bridge, but its guessed source paths all reported `exists = 0`. This package performs repo-wide term discovery so a future source patch proposal is grounded in actual files.

## Summary

- Files scanned: **{scanned}**
- Large files skipped: **{skipped_large}**
- Term-match candidates found: **{len(candidates)}**
- Source-code candidates found: **{len(source_candidates)}**
- Source edits: **0**
- Active catalog replacement: **0**

## Next lane

If prioritized source candidates are meaningful, DD096Z-F2 should be a guarded source patch proposal only. If source candidates are still weak, run a focused file-layout inventory first.
"""
    wt(out / "DD096ZFR_SOURCE_TOUCHPOINT_DISCOVERY_REPORT.md", report)

    manifest = {
        "contract": "dd096zfr_source_touchpoint_discovery_v0",
        "run_id": args.run_id,
        "created_utc": now(),
        "status": status,
        "repo_root": str(repo),
        "profiles": args.profile,
        "files_scanned": scanned,
        "large_files_skipped": skipped_large,
        "term_candidates_found": len(candidates),
        "source_candidates_found": len(source_candidates),
        "source_edits": 0,
        "active_catalog_replacement": 0,
        "failures": failures,
        "next_recommended_action": "Inspect prioritized source candidates; then DD096Z-F2 guarded source patch proposal or focused file-layout inventory.",
    }
    wj(out / "dd096zfr_source_touchpoint_discovery_manifest.json", manifest)

    print(f"DD096ZF-R source touchpoint discovery manifest: {out / 'dd096zfr_source_touchpoint_discovery_manifest.json'}")
    print(f"status: {status}; files_scanned: {scanned}; candidates: {len(candidates)}; source_candidates: {len(source_candidates)}; source_edits: 0; active_catalog_replacement: 0; failures: {failures}")
    return 2 if (args.fail_on_review and failures) else 0

if __name__ == "__main__":
    raise SystemExit(main())
