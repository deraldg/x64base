#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, datetime as dt, json
from pathlib import Path

REQUIRED = [
    ("DD096ZD2ZL", "docs/datadict/reports/DD096ZD2ZL-ddict-fields-tags-source-context-v0/dd096zd2zl_ddict_fields_tags_source_context_manifest.json", ["DD096ZD2ZL_DDICT_FIELDS_TAGS_SOURCE_CONTEXT_READY"]),
    ("DD096ZD2ZK", "docs/datadict/reports/DD096ZD2ZK-guarded-ddict-fields-tags-patch-v0/dd096zd2zk_guarded_ddict_fields_tags_patch_manifest.json", ["DD096ZD2ZK_SAFE_SOURCE_PATCH_APPLIED_CALLSITE_REVIEW_PENDING"]),
]
ALIASES = [
    ("DDRUN", "DATA_DICTIONARY_RUNS"),
    ("DDOBJECT", "DATA_DICTIONARY_OBJECTS"),
    ("DDATTR", "DATA_DICTIONARY_OBJECT_ATTRIBUTES"),
    ("DDEDGE", "DATA_DICTIONARY_RELATION_EDGES"),
    ("DDEVID", "DATA_DICTIONARY_EVIDENCE_RECORDS"),
    ("DDGATE", "DATA_DICTIONARY_GATE_RECORDS"),
]
PATTERNS = [
    "FIELDS", "TAGS", "NO_FIELDS_FOUND", "NO_CATALOG_TAGS_FOUND",
    "FIELD ROWS", "CATALOG TAGS", "CDX ARTIFACT", "LMDB MIRROR",
    "DATA_DICTIONARY_OBJECTS", "DDOBJECT"
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
        "has_ddict_callsite_bridge_include": int("DDICT_CALLSITE_BRIDGE.HPP" in up),
        "has_ddict_catalog_resolver_include": int("DDICT_CATALOG_RESOLVER.HPP" in up),
        "has_bridge_x64_helper": int("DDICT_BRIDGE_X64_OWNER_TOKEN" in up),
        "has_bridge_legacy_helper": int("DDICT_BRIDGE_LEGACY_OWNER_TOKEN" in up),
        "fields_mentions": up.count("FIELDS"),
        "tags_mentions": up.count("TAGS"),
        "no_fields_found_mentions": up.count("NO_FIELDS_FOUND"),
        "no_catalog_tags_found_mentions": up.count("NO_CATALOG_TAGS_FOUND"),
        "data_dictionary_objects_mentions": up.count("DATA_DICTIONARY_OBJECTS"),
        "ddobject_mentions": up.count("DDOBJECT"),
    }

def anchor_lines(text: str):
    rows = []
    for n, line in enumerate(text.splitlines(), start=1):
        up = line.upper()
        hits = [p for p in PATTERNS if p in up]
        if hits:
            cls = "related"
            if "NO_FIELDS_FOUND" in up or "FIELD ROWS" in up:
                cls = "fields_anchor"
            elif "NO_CATALOG_TAGS_FOUND" in up or "CATALOG TAGS" in up or "CDX ARTIFACT" in up or "LMDB MIRROR" in up:
                cls = "tags_anchor"
            rows.append({"line": n, "classification": cls, "patterns": ";".join(hits), "text": line[:260]})
    return rows

def fields_patch_intent():
    return """// DD096Z-D2ZM FIELDS patch intent.
//
// Before DDICT FIELDS owner lookup, bridge the requested token:
//
// const std::string requested = user_token;
// const std::string legacy_owner = dottalk::datadict::ddict_bridge_legacy_owner_token(requested);
// const std::string x64_owner = dottalk::datadict::ddict_bridge_x64_owner_token(requested);
//
// Compatibility target:
//   DDICT FIELDS DDOBJECT
//   DDICT FIELDS DATA_DICTIONARY_OBJECTS
//
// Query order should preserve legacy DDOBJECT behavior, then allow x64 names.
// If field rows are still absent but physical x64 artifacts exist, report a bridge gap
// instead of a plain NO_FIELDS_FOUND.
"""

def tags_patch_intent():
    return """// DD096Z-D2ZM TAGS patch intent.
//
// DDICT TAGS should distinguish physical artifacts from catalog tag metadata.
//
// Desired when physical DBF/CDX/LMDB exist but catalog tag rows are absent:
//
// Table DBF     : YES
// CDX artifact  : <path>
// LMDB mirror   : <path>
// Catalog tags  : 0
// Physical tags : <n>
// Result        : PHYSICAL_TAGS_FOUND_NO_CATALOG_ROWS
//
// Only return NO_CATALOG_TAGS_FOUND when neither catalog rows nor physical tag
// metadata can be found.
"""

def smoke_dts():
    return "\n".join([
        "* DD096Z-D2ZM proposed FIELDS/TAGS logic smoke",
        "* Run after a later real source patch and rebuild.",
        "DDICT STATUS",
        "DDICT FIELDS DDOBJECT",
        "DDICT FIELDS DATA_DICTIONARY_OBJECTS",
        "DDICT TAGS DDOBJECT",
        "DDICT TAGS DATA_DICTIONARY_OBJECTS",
        "",
    ])

def main():
    ap = argparse.ArgumentParser(description="DD096Z-D2ZM guarded FIELDS/TAGS logic patch proposal")
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--run-id", default="DD096ZD2ZM-guarded-fields-tags-logic-patch-proposal-v0")
    ap.add_argument("--profile", action="append", default=[])
    ap.add_argument("--write-review-files", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    out = Path(args.out_dir).resolve()
    gen = out / "generated_fields_tags_logic_patch_proposal"
    gen.mkdir(parents=True, exist_ok=True)

    blockers = 0
    pre_rows = []
    for lane, rel, expected in REQUIRED:
        p = repo / rel
        observed = read_json(p).get("status", "MISSING")
        passed = int(observed in expected)
        blockers += 0 if passed else 1
        pre_rows.append({"lane": lane, "manifest_path": str(p), "observed_status": observed, "expected_status": "|".join(expected), "pass": passed})
    wc(gen / "dd096zd2zm_precondition_ledger.csv", pre_rows, ["lane","manifest_path","observed_status","expected_status","pass"])

    cmd_path = repo / "src/cli/cmd_ddict.cpp"
    cmd_text = read_text(cmd_path)
    metrics = cmd_metrics(cmd_text)
    wc(gen / "dd096zd2zm_cmd_ddict_metrics.csv", [{"metric": k, "value": v} for k, v in sorted(metrics.items())], ["metric","value"])
    anchors = anchor_lines(cmd_text)
    wc(gen / "dd096zd2zm_anchor_lines.csv", anchors, ["line","classification","patterns","text"])

    d2zl_index = repo / "docs/datadict/reports/DD096ZD2ZL-ddict-fields-tags-source-context-v0/generated_ddict_fields_tags_source_context/dd096zd2zl_source_window_index.csv"
    windows = read_csv(d2zl_index)
    wc(gen / "dd096zd2zm_d2zl_window_summary.csv", windows, ["window_id","start_line","end_line","classification","hit_summary"])

    proposals = [
        {"area": "FIELDS", "proposal_file": "DD096ZD2ZM_FIELDS_PATCH_INTENT.cpp.txt", "auto_patch_safe": 0, "reason": "source-window review required"},
        {"area": "TAGS", "proposal_file": "DD096ZD2ZM_TAGS_PATCH_INTENT.cpp.txt", "auto_patch_safe": 0, "reason": "source-window review required"},
    ]
    wc(gen / "dd096zd2zm_patch_proposal_index.csv", proposals, ["area","proposal_file","auto_patch_safe","reason"])

    wt(gen / "DD096ZD2ZM_FIELDS_PATCH_INTENT.cpp.txt", fields_patch_intent())
    wt(gen / "DD096ZD2ZM_TAGS_PATCH_INTENT.cpp.txt", tags_patch_intent())
    wt(gen / "DD096ZD2ZM_FIELDS_TAGS_LOGIC_SMOKE.dts", smoke_dts())
    decision = """# DD096Z-D2ZM Patch Decision

D2ZM does not auto-rewrite `cmd_ddict.cpp`.

It provides anchors and intended patch behavior for a later D2ZN surgical patch.

Review:
- `dd096zd2zm_anchor_lines.csv`
- `dd096zd2zm_d2zl_window_summary.csv`
- `DD096ZD2ZM_FIELDS_PATCH_INTENT.cpp.txt`
- `DD096ZD2ZM_TAGS_PATCH_INTENT.cpp.txt`

D2ZN should patch only:
1. DDICT FIELDS token normalization / fallback owner lookup
2. DDICT TAGS physical-tag reporting when catalog rows are absent

Do not patch REL/EVIDENCE yet.
"""
    wt(gen / "DD096ZD2ZM_PATCH_DECISION.md", decision)

    review_written = 0
    if args.write_review_files:
        review = repo / "docs/datadict/reviews/DD096ZD2ZM"
        wt(review / "DD096ZD2ZM_PATCH_DECISION.md", decision)
        wt(review / "DD096ZD2ZM_FIELDS_PATCH_INTENT.cpp.txt", fields_patch_intent())
        wt(review / "DD096ZD2ZM_TAGS_PATCH_INTENT.cpp.txt", tags_patch_intent())
        wt(repo / "dottalkpp/data/scripts/DD096ZD2ZM_FIELDS_TAGS_LOGIC_SMOKE.dts", smoke_dts())
        review_written = 1

    required_missing = int(not cmd_path.exists())
    failures = blockers + required_missing
    status = "DD096ZD2ZM_GUARDED_FIELDS_TAGS_LOGIC_PATCH_PROPOSAL_READY" if failures == 0 else "DD096ZD2ZM_GUARDED_FIELDS_TAGS_LOGIC_PATCH_PROPOSAL_REVIEW"

    boundary = [
        {"boundary": "fields_tags_logic_patch_proposal_only", "observed": 1, "required": 1, "pass": 1},
        {"boundary": "source_edits", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "build_file_edits", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "active_catalog_replacement", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "active_dbf_cdx_lmdb_mutation", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "help_meta_cmdhelpchk_mutation", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "manual_publication_mutation", "observed": 0, "required": 0, "pass": 1},
    ]
    wc(out / "dd096zd2zm_boundary_ledger.csv", boundary, ["boundary","observed","required","pass"])

    report = f"""# DD096Z-D2ZM Guarded FIELDS/TAGS Logic Patch Proposal

Run id: `{args.run_id}`
Status: **{status}**
Created UTC: `{now()}`

## Purpose

D2ZM converts D2ZL source windows into a concrete FIELDS/TAGS patch proposal without editing source.

## Summary

- Precondition blockers: **{blockers}**
- Required files missing: **{required_missing}**
- Anchor lines found: **{len(anchors)}**
- D2ZL windows: **{len(windows)}**
- Review files written: **{review_written}**
- Source edits: **0**
- Auto patch safe: **0**

## Next lane

D2ZN should apply the surgical FIELDS/TAGS logic patch after this proposal is reviewed.
"""
    wt(out / "DD096ZD2ZM_GUARDED_FIELDS_TAGS_LOGIC_PATCH_PROPOSAL_REPORT.md", report)

    manifest = {
        "contract": "dd096zd2zm_guarded_fields_tags_logic_patch_proposal_v0",
        "run_id": args.run_id,
        "created_utc": now(),
        "status": status,
        "repo_root": str(repo),
        "profiles": args.profile,
        "precondition_blockers": blockers,
        "required_files_missing": required_missing,
        "anchor_lines_found": len(anchors),
        "d2zl_windows": len(windows),
        "review_files_written": review_written,
        "auto_patch_safe": 0,
        "source_edits": 0,
        "build_file_edits": 0,
        "active_catalog_replacement": 0,
        "failures": failures,
        "next_recommended_action": "Review D2ZM outputs and authorize D2ZN surgical FIELDS/TAGS logic patch.",
    }
    wj(out / "dd096zd2zm_guarded_fields_tags_logic_patch_proposal_manifest.json", manifest)

    print(f"DD096Z-D2ZM guarded FIELDS/TAGS logic patch proposal manifest: {out / 'dd096zd2zm_guarded_fields_tags_logic_patch_proposal_manifest.json'}")
    print(f"status: {status}; precondition_blockers: {blockers}; anchor_lines_found: {len(anchors)}; auto_patch_safe: 0; source_edits: 0; failures: {failures}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
