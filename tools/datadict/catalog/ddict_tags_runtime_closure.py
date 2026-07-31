#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
from pathlib import Path
from typing import Any, Dict, List


EXPECTED_DD075_STATUS = "DDICT_TAGS_SOURCE_PATCH_APPLIED_BUILD_REQUIRED"
TABLES = ["DDATTR", "DDOBJECT", "DDEDGE"]
EXPECTED_TAG_COUNTS = {"DDATTR": 2, "DDOBJECT": 2, "DDEDGE": 2}
SAMPLE_TAGS = {
    "DDATTR": ["ATTRID", "OBJ_ATTR"],
    "DDOBJECT": ["OBJID", "TYPE_NAME"],
    "DDEDGE": ["EDGEID", "FROMOBJ"],
}


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def read_json(path: Path) -> Dict[str, Any]:
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


def write_json(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: List[Dict[str, Any]], fields: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        w.writeheader()
        for row in rows:
            w.writerow({k: row.get(k, "") for k in fields})


def rel(repo: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(repo.resolve()).as_posix()
    except Exception:
        return path.as_posix()


def count_line_seen(upper: str, table: str) -> int:
    expected = EXPECTED_TAG_COUNTS[table]
    return int(f"CATALOG TAGS  : {expected}" in upper or f"CATALOG TAGS: {expected}" in upper)


def classify_runtime(text: str) -> Dict[str, Any]:
    upper = text.upper()
    result: Dict[str, Any] = {}
    for table in TABLES:
        result[f"has_tags_{table.lower()}"] = int(f"DDICT TAGS {table}" in upper)
        result[f"has_{table.lower()}_count"] = count_line_seen(upper, table)
        result[f"has_{table.lower()}_cdx"] = int(f"{table.lower()}.cdx".upper() in upper or f"{table}.CDX" in upper)
        result[f"has_{table.lower()}_lmdb"] = int(f"{table.lower()}.cdx.d".upper() in upper or f"{table}.CDX.D" in upper)
        result[f"has_{table.lower()}_samples"] = int(all(tag in upper for tag in SAMPLE_TAGS[table]))
    result["has_read_only"] = int("READ-ONLY" in upper)
    result["has_active_catalog"] = int("ACTIVE CATALOG:" in upper and "DATADICT" in upper)
    result["has_table_dbf_yes"] = int("TABLE DBF" in upper and "YES" in upper)
    result["rel_pending_preserved"] = int("DDICT REL" in upper and "PENDING" in upper)
    result["has_unknown_command_for_ddict"] = int("UNKNOWN COMMAND" in upper and "DDICT" in upper)
    result["tags_surface_green"] = int(
        all(result[f"has_tags_{table.lower()}"] for table in TABLES)
        and all(result[f"has_{table.lower()}_count"] for table in TABLES)
        and all(result[f"has_{table.lower()}_cdx"] for table in TABLES)
        and all(result[f"has_{table.lower()}_lmdb"] for table in TABLES)
        and all(result[f"has_{table.lower()}_samples"] for table in TABLES)
        and result["has_read_only"]
        and result["has_active_catalog"]
        and result["has_table_dbf_yes"]
        and result["rel_pending_preserved"]
        and not result["has_unknown_command_for_ddict"]
    )
    return result


def main() -> int:
    ap = argparse.ArgumentParser(description="DD-076 DDICT TAGS runtime closure")
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--run-id", default="DD076-ddict-tags-runtime-closure-v0")
    ap.add_argument("--dd075-dir", default="docs/datadict/reports/DD075-guarded-ddict-tags-implementation-apply-v0")
    ap.add_argument("--runtime-proof", required=True)
    ap.add_argument("--exe-path", default="build/src/Release/dottalkpp.exe")
    ap.add_argument("--write-closure", action="store_true")
    ap.add_argument("--closure-path", default="docs/datadict/runlog/DD-076_DDICT_TAGS_RUNTIME_CLOSURE.md")
    ap.add_argument("--profile", action="append", default=[])
    ap.add_argument("--fail-on-review", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    out = Path(args.out_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)

    dd075_dir = (repo / args.dd075_dir).resolve()
    dd075_manifest = read_json(dd075_dir / "dd075_guarded_ddict_tags_impl_manifest.json")
    proof_path = (repo / args.runtime_proof).resolve()
    exe_path = (repo / args.exe_path).resolve()
    closure_path = (repo / args.closure_path).resolve()

    proof_text = read_text(proof_path)
    classified = classify_runtime(proof_text)
    exe_exists = int(exe_path.exists())
    exe_bytes = exe_path.stat().st_size if exe_path.exists() else 0
    proof_exists = int(proof_path.exists())
    dd075_ok = int(dd075_manifest.get("status") == EXPECTED_DD075_STATUS)

    gate_rows = [
        {"gate": "dd075_source_patch_applied", "expected": EXPECTED_DD075_STATUS, "observed": dd075_manifest.get("status", ""), "pass": dd075_ok},
        {"gate": "dottalkpp_exe_exists", "expected": 1, "observed": exe_exists, "pass": exe_exists},
        {"gate": "dottalkpp_exe_nonempty", "expected": 1, "observed": int(exe_bytes > 0), "pass": int(exe_bytes > 0)},
        {"gate": "runtime_proof_exists", "expected": 1, "observed": proof_exists, "pass": proof_exists},
        {"gate": "active_catalog_seen", "expected": 1, "observed": classified["has_active_catalog"], "pass": classified["has_active_catalog"]},
        {"gate": "read_only_seen", "expected": 1, "observed": classified["has_read_only"], "pass": classified["has_read_only"]},
        {"gate": "table_dbf_yes_seen", "expected": 1, "observed": classified["has_table_dbf_yes"], "pass": classified["has_table_dbf_yes"]},
        {"gate": "rel_pending_preserved", "expected": 1, "observed": classified["rel_pending_preserved"], "pass": classified["rel_pending_preserved"]},
        {"gate": "no_unknown_command_for_ddict", "expected": 0, "observed": classified["has_unknown_command_for_ddict"], "pass": int(classified["has_unknown_command_for_ddict"] == 0)},
    ]

    for table in TABLES:
        tl = table.lower()
        gate_rows.extend([
            {"gate": f"ddict_tags_{tl}_seen", "expected": 1, "observed": classified[f"has_tags_{tl}"], "pass": classified[f"has_tags_{tl}"]},
            {"gate": f"{tl}_catalog_tag_count_2_seen", "expected": 1, "observed": classified[f"has_{tl}_count"], "pass": classified[f"has_{tl}_count"]},
            {"gate": f"{tl}_cdx_artifact_seen", "expected": 1, "observed": classified[f"has_{tl}_cdx"], "pass": classified[f"has_{tl}_cdx"]},
            {"gate": f"{tl}_lmdb_mirror_seen", "expected": 1, "observed": classified[f"has_{tl}_lmdb"], "pass": classified[f"has_{tl}_lmdb"]},
            {"gate": f"{tl}_sample_tags_seen", "expected": 1, "observed": classified[f"has_{tl}_samples"], "pass": classified[f"has_{tl}_samples"]},
        ])

    boundary_rows = [
        {"boundary": "runtime_closure_only", "observed": 1, "required": 1, "pass": 1},
        {"boundary": "cxx_source_edits", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "registry_edits", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "build_file_edits", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "active_catalog_mutation", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "dbf_append_replace_delete_pack_zap", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "cdx_lmdb_create_rebuild", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "help_meta_cmdhelpchk_mutation", "observed": 0, "required": 0, "pass": 1},
    ]

    table_rows = []
    for table in TABLES:
        tl = table.lower()
        table_rows.append({
            "table": table,
            "expected_catalog_tags": EXPECTED_TAG_COUNTS[table],
            "seen_command": classified[f"has_tags_{tl}"],
            "seen_count": classified[f"has_{tl}_count"],
            "seen_cdx": classified[f"has_{tl}_cdx"],
            "seen_lmdb": classified[f"has_{tl}_lmdb"],
            "seen_sample_tags": classified[f"has_{tl}_samples"],
            "sample_tags": ",".join(SAMPLE_TAGS[table]),
        })

    failures = sum(1 for r in gate_rows if int(r["pass"]) != 1)
    status = "DDICT_TAGS_RUNTIME_CLOSURE_GREEN" if failures == 0 else "DDICT_TAGS_RUNTIME_CLOSURE_REVIEW"

    write_csv(out / "dd076_tags_runtime_gate_ledger.csv", gate_rows, ["gate", "expected", "observed", "pass"])
    write_csv(out / "dd076_tags_table_runtime_ledger.csv", table_rows, ["table", "expected_catalog_tags", "seen_command", "seen_count", "seen_cdx", "seen_lmdb", "seen_sample_tags", "sample_tags"])
    write_csv(out / "dd076_tags_no_mutation_boundary_ledger.csv", boundary_rows, ["boundary", "observed", "required", "pass"])

    report = f"""# DD-076 DDICT TAGS Runtime Closure

Run id: `{args.run_id}`
Status: **{status}**
Created UTC: `{utc_now()}`

## Purpose

DD-076 closes the guarded `DDICT TAGS <table>` runtime milestone.

## Evidence

- DD-075 apply status: `{dd075_manifest.get('status', '')}`
- Runtime proof: `{rel(repo, proof_path)}`
- Executable: `{rel(repo, exe_path)}`
- Executable exists: **{exe_exists}**
- Executable bytes: **{exe_bytes}**

## Runtime classification

- DDICT TAGS DDATTR seen: **{classified['has_tags_ddattr']}**
- DDICT TAGS DDOBJECT seen: **{classified['has_tags_ddobject']}**
- DDICT TAGS DDEDGE seen: **{classified['has_tags_ddedge']}**
- READ-ONLY seen: **{classified['has_read_only']}**
- Active catalog seen: **{classified['has_active_catalog']}**
- Table DBF YES seen: **{classified['has_table_dbf_yes']}**
- REL pending preserved: **{classified['rel_pending_preserved']}**

## Boundary

DD-076 closure is readback only. It does not edit C++ source, edit registry/build files,
mutate active catalog data, append/replace/delete/pack/zap DBFs, create/rebuild CDX/LMDB,
or mutate HELP/META/CMDHELPCHK.
"""
    (out / "DD076_DDICT_TAGS_RUNTIME_CLOSURE_REPORT.md").write_text(report, encoding="utf-8")

    closure_written = 0
    if args.write_closure:
        closure_path.parent.mkdir(parents=True, exist_ok=True)
        closure_path.write_text(report, encoding="utf-8")
        closure_written = 1

    manifest = {
        "contract": "dd076_ddict_tags_runtime_closure_v0",
        "run_id": args.run_id,
        "created_utc": utc_now(),
        "status": status,
        "repo_root": str(repo),
        "profiles": args.profile,
        "dd075_status": dd075_manifest.get("status", ""),
        "runtime_proof": rel(repo, proof_path),
        "exe_exists": exe_exists,
        "exe_bytes": exe_bytes,
        "tags_surface_green": classified["tags_surface_green"],
        "closure_written": closure_written,
        "closure_path": str(closure_path) if closure_written else "",
        "failures": failures,
        "cxx_source_edits": 0,
        "registry_edits": 0,
        "build_file_edits": 0,
        "active_catalog_mutation": 0,
        "help_meta_cmdhelpchk_mutation": 0,
        "next_recommended_action": "DD-077 plan for guarded DDICT REL implementation.",
    }
    write_json(out / "dd076_tags_runtime_closure_manifest.json", manifest)

    print(f"DD-076 TAGS runtime closure manifest: {out / 'dd076_tags_runtime_closure_manifest.json'}")
    print(f"status: {status}; failures: {failures}; closure_written: {closure_written}")
    return 2 if (args.fail_on_review and failures) else 0


if __name__ == "__main__":
    raise SystemExit(main())
