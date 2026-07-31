#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, datetime as dt, json, re
from pathlib import Path

TABLES = [
    (3, "DATA_DICTIONARY_OBJECTS", 10, ["CATALOG_OBJECT_ID", "CATALOG_OBJECT_NAME"]),
    (2, "DATA_DICTIONARY_OBJECT_ATTRIBUTES", 127, ["CATALOG_OBJECT_ID", "CATALOG_ATTRIBUTE_NAME"]),
    (4, "DATA_DICTIONARY_RELATION_EDGES", 16, ["RELATION_FROM_OBJECT_ID", "RELATION_TO_OBJECT_ID"]),
    (0, "DATA_DICTIONARY_EVIDENCE_RECORDS", 7, ["CATALOG_OBJECT_ID"]),
    (1, "DATA_DICTIONARY_GATE_RECORDS", 3, ["GATE_RECORD_ID"]),
    (5, "DATA_DICTIONARY_RUNS", 2, ["RUN_RECORD_ID"]),
]

LEGACY_NAMES = ["DDBASE", "DDOBJECT", "DDATTR", "DDEDGE", "DDEVID", "DDGATE", "DDARTIF", "DDSRC"]

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

def make_identity(candidate_dbf: Path, candidate_index: Path, candidate_lmdb: Path) -> str:
    lines = []
    lines.append("* DD096Z-D2ZC current-session candidate SELECT identity check")
    lines.append("* No CDX mutation and no BUILDLMDB.")
    lines.append("* Continue only if each selected area shows the expected candidate DATA_DICTIONARY_* table and candidate path.")
    lines.append("")
    lines.append(f"SETPATH DBF {candidate_dbf}")
    lines.append(f"SETPATH INDEXES {candidate_index}")
    lines.append(f"SETPATH LMDB {candidate_lmdb}")
    lines.append("")
    for area, table, expected, tags in TABLES:
        lines.append(f"* CHECK AREA {area}: expected {table}; expected records {expected}")
        lines.append(f"SELECT {area}")
        lines.append("AREA")
        lines.append("STRUCT")
        lines.append("")
    return "\n".join(lines) + "\n\n"

def make_rebuild(candidate_dbf: Path, candidate_index: Path, candidate_lmdb: Path, preset: str) -> str:
    lines = []
    lines.append("* DD096Z-D2ZC current-session SELECT-area candidate CDX/LMDB rebuild")
    lines.append("* Uses proven syntax: BUILDLMDB CLEAN TINY YES.")
    lines.append("* Do not put TINY after CDX CREATE; CDX CREATE TINY creates TINY.cdx.")
    lines.append("* Candidate paths only. Generated listing uses SL/SMARTLIST.")
    lines.append("")
    lines.append(f"SETPATH DBF {candidate_dbf}")
    lines.append(f"SETPATH INDEXES {candidate_index}")
    lines.append(f"SETPATH LMDB {candidate_lmdb}")
    lines.append("")
    for area, table, expected, tags in TABLES:
        lines.append(f"* REBUILD AREA {area}: {table}; expected records {expected}")
        lines.append(f"SELECT {area}")
        lines.append("AREA")
        lines.append("STRUCT")
        lines.append("* Guard: AREA above must show this DATA_DICTIONARY_* table and candidate path.")
        lines.append("CDX CREATE")
        for tag in tags:
            lines.append(f"CDX ADDTAG {tag}")
        lines.append("CDX INFO")
        lines.append(f"BUILDLMDB CLEAN {preset} YES")
        lines.append(f"SET INDEX TO {table}")
        lines.append("CDX INFO")
        for tag in tags:
            lines.append(f"SET ORDER TO TAG {tag}")
            lines.append("TOP")
            lines.append("SL")
        lines.append("")
    return "\n".join(lines) + "\n\n"

def make_verify(candidate_dbf: Path, candidate_index: Path, candidate_lmdb: Path) -> str:
    lines = []
    lines.append("* DD096Z-D2ZC current-session SELECT-area candidate verify")
    lines.append("* Uses already-open candidate areas and SL.")
    lines.append("")
    lines.append(f"SETPATH DBF {candidate_dbf}")
    lines.append(f"SETPATH INDEXES {candidate_index}")
    lines.append(f"SETPATH LMDB {candidate_lmdb}")
    lines.append("")
    for area, table, expected, tags in TABLES:
        lines.append(f"* VERIFY AREA {area}: {table}; expected records {expected}")
        lines.append(f"SELECT {area}")
        lines.append("AREA")
        lines.append(f"SET INDEX TO {table}")
        lines.append("CDX INFO")
        for tag in tags:
            lines.append(f"SET ORDER TO TAG {tag}")
            lines.append("TOP")
            lines.append("SL")
        lines.append("")
    return "\n".join(lines) + "\n\n"

def scan_runtime(text: str):
    up = text.upper()
    return {
        "proof_supplied": int(bool(text)),
        "candidate_path_seen": int("DOCS\\DATADICT\\CANDIDATES" in up or "DOCS/DATADICT/CANDIDATES" in up),
        "active_datadict_path_seen": int("DOTTALKPP\\DATA\\DATADICT" in up or "DOTTALKPP/DATA/DATADICT" in up),
        "legacy_name_seen_count": sum(1 for name in LEGACY_NAMES if f"FILE: {name}" in up),
        "buildlmdb_clean_tiny_seen": int("BUILDLMDB CLEAN TINY YES" in up or "MAPSIZE         33,554,432 BYTES (32 MIB)" in up),
        "cdx_create_tiny_bad_seen": int("CDX CREATE TINY" in up or "\\INDEXES\\TINY.CDX" in up),
        "table_cdx_seen": int("\\INDEXES\\TABLE.CDX" in up or "/INDEXES/TABLE.CDX" in up),
        "no_table_open_count": len(re.findall(r"NO TABLE OPEN", up)),
        "buildlmdb_failed_count": len(re.findall(r"BUILDLMDB:\s*FAILED", up)),
        "mdb_env_open_112_count": len(re.findall(r"MDB_ENV_OPEN FAILED:\s*112", up)),
        "not_enough_space_count": len(re.findall(r"NOT ENOUGH SPACE ON THE DISK", up)),
        "buildlmdb_ok_count": len(re.findall(r"BUILDLMDB:\s*DONE\s+OK=", up)),
        "smartlist_output_count": len(re.findall(r"RECORD\(S\) LISTED \(LIMIT", up)),
        "set_order_success_count": len(re.findall(r"SET ORDER:\s*CDX TAG", up)),
    }

def main():
    ap = argparse.ArgumentParser(description="DD096Z-D2ZC current-session SELECT-area CLEAN TINY candidate rebuild")
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--run-id", default="DD096ZD2ZC-current-session-select-clean-tiny-rebuild-v0")
    ap.add_argument("--preset", default="TINY", choices=["TINY", "SMALL"])
    ap.add_argument("--write-runtime-scripts", action="store_true")
    ap.add_argument("--runtime-proof", default="")
    ap.add_argument("--profile", action="append", default=[])
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    out = Path(args.out_dir).resolve()
    gen = out / "generated_current_session_select_clean_tiny_rebuild"
    gen.mkdir(parents=True, exist_ok=True)

    d2s = read_json(repo / "docs/datadict/reports/DD096ZD2S-single-table-cdx-lmdb-proof-closure-v0/dd096zd2s_single_table_cdx_lmdb_proof_closure_manifest.json")
    d2s_status = d2s.get("status", "MISSING")
    precondition_blockers = 0 if d2s_status == "DD096ZD2S_SINGLE_TABLE_CDX_LMDB_PROOF_GREEN" else 1

    zb = read_json(repo / "docs/datadict/reports/DD096ZB-backup-and-inactive-candidate-staging-v0/dd096zb_backup_and_inactive_candidate_staging_manifest.json")
    candidate_root = Path(zb.get("candidate_root", repo / "docs/datadict/candidates/DD096ZB-backup-and-inactive-candidate-staging-v0"))
    candidate_dbf = Path(zb.get("candidate_dbf_root", candidate_root / "dbf"))
    candidate_index = candidate_root / "indexes"
    candidate_lmdb = candidate_root / "lmdb"

    missing = 0
    table_rows = []
    for area, table, expected, tags in TABLES:
        p = candidate_dbf / f"{table}.dbf"
        exists = int(p.exists())
        missing += 0 if exists else 1
        table_rows.append({
            "area": area,
            "table": table,
            "expected_records": expected,
            "candidate_dbf": str(p),
            "exists": exists,
            "tags": ";".join(tags),
            "access_strategy": f"SELECT {area} after identity check",
            "buildlmdb_command": f"BUILDLMDB CLEAN {args.preset} YES",
        })
    wc(gen / "dd096zd2zc_area_rebuild_plan.csv", table_rows, ["area","table","expected_records","candidate_dbf","exists","tags","access_strategy","buildlmdb_command"])

    policy_rows = [
        {"finding": "CDX CREATE TINY creates TINY.cdx", "policy": "Do not use TINY as a CDX CREATE modifier."},
        {"finding": "BUILDLMDB CLEAN TINY YES mapsize is 32 MiB and succeeds on DATA_DICTIONARY_RUNS", "policy": "Use BUILDLMDB CLEAN TINY YES for proof-sized candidate tables."},
        {"finding": "Candidate tables are already open in areas 0..5", "policy": "Use SELECT after identity check in this current session."},
        {"finding": "Generated display should use SL", "policy": "Do not use LIST in generated proof scripts."},
    ]
    wc(gen / "dd096zd2zc_verified_syntax_policy.csv", policy_rows, ["finding","policy"])

    identity = make_identity(candidate_dbf, candidate_index, candidate_lmdb)
    rebuild = make_rebuild(candidate_dbf, candidate_index, candidate_lmdb, args.preset)
    verify = make_verify(candidate_dbf, candidate_index, candidate_lmdb)

    wt(gen / "DD096ZD2ZC_CURRENT_SESSION_CANDIDATE_AREA_IDENTITY_CHECK.dts", identity)
    wt(gen / "DD096ZD2ZC_CURRENT_SESSION_SELECT_CLEAN_TINY_CANDIDATE_REBUILD.dts", rebuild)
    wt(gen / "DD096ZD2ZC_CURRENT_SESSION_SELECT_CLEAN_TINY_CANDIDATE_VERIFY.dts", verify)

    scripts_written = 0
    if args.write_runtime_scripts:
        wt(repo / "dottalkpp/data/scripts/DD096ZD2ZC_CURRENT_SESSION_CANDIDATE_AREA_IDENTITY_CHECK.dts", identity)
        wt(repo / "dottalkpp/data/scripts/DD096ZD2ZC_CURRENT_SESSION_SELECT_CLEAN_TINY_CANDIDATE_REBUILD.dts", rebuild)
        wt(repo / "dottalkpp/data/scripts/DD096ZD2ZC_CURRENT_SESSION_SELECT_CLEAN_TINY_CANDIDATE_VERIFY.dts", verify)
        scripts_written = 1

    metrics = scan_runtime("")
    proof_supplied = 0
    if args.runtime_proof:
        p = Path(args.runtime_proof)
        if not p.is_absolute():
            p = repo / p
        metrics = scan_runtime(read_text(p))
        proof_supplied = metrics["proof_supplied"]
    wc(gen / "dd096zd2zc_runtime_scan.csv", [{"metric": k, "value": v} for k, v in sorted(metrics.items())], ["metric","value"])

    proof_failures = 0
    if proof_supplied:
        checks = [
            ("candidate_path_seen", 1),
            ("active_datadict_path_seen", 0),
            ("legacy_name_seen_count", 0),
            ("no_table_open_count", 0),
            ("buildlmdb_failed_count", 0),
            ("mdb_env_open_112_count", 0),
            ("not_enough_space_count", 0),
        ]
        for k, expected in checks:
            if metrics.get(k, 0) != expected:
                proof_failures += 1
        if metrics.get("buildlmdb_ok_count", 0) < len(TABLES):
            proof_failures += 1

    failures = precondition_blockers + missing + (proof_failures if proof_supplied else 0)
    if failures:
        status = "DD096ZD2ZC_CURRENT_SESSION_SELECT_CLEAN_TINY_REBUILD_REVIEW"
    elif proof_supplied:
        status = "DD096ZD2ZC_CURRENT_SESSION_SELECT_CLEAN_TINY_REBUILD_GREEN"
    else:
        status = "DD096ZD2ZC_CURRENT_SESSION_SELECT_CLEAN_TINY_REBUILD_READY"

    wc(out / "dd096zd2zc_no_mutation_boundary_ledger.csv", [
        {"boundary": "current_session_select_clean_tiny_rebuild_script_package", "observed": 1, "required": 1, "pass": 1},
        {"boundary": "runtime_scripts_written", "observed": scripts_written, "required": int(args.write_runtime_scripts), "pass": int(scripts_written == int(args.write_runtime_scripts))},
        {"boundary": "active_catalog_replacement", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "active_cdx_lmdb_rebuild", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "source_edits", "observed": 0, "required": 0, "pass": 1},
    ], ["boundary","observed","required","pass"])

    report = f"""# DD096Z-D2ZC Current-Session SELECT CLEAN TINY Rebuild

Run id: `{args.run_id}`
Status: **{status}**
Created UTC: `{now()}`

## Purpose

DD096Z-D2ZC corrects D2ZB using the now-proven syntax:

```text
BUILDLMDB CLEAN TINY YES
```

It also preserves the current-session SELECT-area strategy because the candidate tables are already open in areas 0..5.

## Summary

- Candidate DBF root: `{candidate_dbf}`
- Candidate INDEXES root: `{candidate_index}`
- Candidate LMDB root: `{candidate_lmdb}`
- BUILDLMDB command: **BUILDLMDB CLEAN {args.preset} YES**
- Precondition blockers: **{precondition_blockers}**
- Missing candidate tables: **{missing}**
- Runtime scripts written: **{scripts_written}**
- Runtime proof supplied: **{proof_supplied}**
- Runtime proof failures: **{proof_failures}**
- Active catalog replacement: **0**

## Runtime scripts

1. `DD096ZD2ZC_CURRENT_SESSION_CANDIDATE_AREA_IDENTITY_CHECK`
2. `DD096ZD2ZC_CURRENT_SESSION_SELECT_CLEAN_TINY_CANDIDATE_REBUILD`
3. `DD096ZD2ZC_CURRENT_SESSION_SELECT_CLEAN_TINY_CANDIDATE_VERIFY`

Run identity check first. Only run rebuild if each area shows the expected candidate `DATA_DICTIONARY_*` table and candidate path.
"""
    wt(out / "DD096ZD2ZC_CURRENT_SESSION_SELECT_CLEAN_TINY_REBUILD_REPORT.md", report)

    manifest = {
        "contract": "dd096zd2zc_current_session_select_clean_tiny_rebuild_v0",
        "run_id": args.run_id,
        "created_utc": now(),
        "status": status,
        "preset": args.preset,
        "buildlmdb_command": f"BUILDLMDB CLEAN {args.preset} YES",
        "candidate_dbf_root": str(candidate_dbf),
        "candidate_index_root": str(candidate_index),
        "candidate_lmdb_root": str(candidate_lmdb),
        "precondition_blockers": precondition_blockers,
        "missing_candidate_tables": missing,
        "runtime_scripts_written": scripts_written,
        "runtime_proof_supplied": proof_supplied,
        "runtime_proof_failures": proof_failures,
        "active_catalog_replacement": 0,
        "failures": failures,
    }
    wj(out / "dd096zd2zc_current_session_select_clean_tiny_rebuild_manifest.json", manifest)

    print(f"DD096Z-D2ZC current-session SELECT CLEAN TINY rebuild manifest: {out / 'dd096zd2zc_current_session_select_clean_tiny_rebuild_manifest.json'}")
    print(f"status: {status}; command: BUILDLMDB CLEAN {args.preset} YES; precondition_blockers: {precondition_blockers}; missing_candidate_tables: {missing}; runtime_scripts_written: {scripts_written}; proof_supplied: {proof_supplied}; active_catalog_replacement: 0; failures: {failures}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
