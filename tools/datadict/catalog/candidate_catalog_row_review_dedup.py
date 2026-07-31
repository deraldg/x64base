#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List, Tuple


EXPECTED_DD096A_STATUS = "DATADICT_CANDIDATE_CATALOG_ROW_DESIGN_READY"
EXPECTED_DD098_STATUS = "DATADICT_BASELINE_CLOSED_AND_REGRESSION_PROVEN"

DEFAULT_CANDIDATE_DIR = "docs/datadict/reports/DD096A-candidate-catalog-row-design-v0/generated_candidate_catalog_rows"

TARGET_TABLES = ["DDOBJECT", "DDATTR", "DDEDGE", "DDEVID", "DDGATE"]

PROTECTED_ARTIFACTS = [
    "dottalkpp/data/datadict",
    "dottalkpp/data/indexes/datadict",
    "dottalkpp/data/lmdb/datadict",
    "dottalkpp/data/workspaces/ddbase.dtschema",
    "src/datadict/ddict_catalog_paths.cpp",
    "src/cli/cmd_ddict.cpp",
    "src/CMakeLists.txt",
]


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def read_text(path: Path) -> str:
    if not path.exists() or path.is_dir():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(read_text(path))
    except Exception as exc:
        return {"_read_error": str(exc)}


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_json(path: Path, obj: Dict[str, Any]) -> None:
    write_text(path, json.dumps(obj, indent=2, sort_keys=True) + "\n")


def write_csv(path: Path, rows: List[Dict[str, Any]], fields: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        w.writeheader()
        for row in rows:
            w.writerow({k: row.get(k, "") for k in fields})


def sha256(path: Path) -> str:
    if not path.exists() or path.is_dir():
        return ""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def artifact_row(repo: Path, rel_path: str, role: str) -> Dict[str, Any]:
    p = repo / rel_path
    return {
        "role": role,
        "path": rel_path,
        "exists": int(p.exists()),
        "kind": "dir" if p.exists() and p.is_dir() else "file" if p.exists() and p.is_file() else "",
        "bytes_or_children": p.stat().st_size if p.exists() and p.is_file() else sum(1 for _ in p.iterdir()) if p.exists() and p.is_dir() else 0,
        "sha256": sha256(p),
    }


def le16(b: bytes, pos: int) -> int:
    return int.from_bytes(b[pos:pos+2], "little", signed=False) if pos + 2 <= len(b) else 0


def le32(b: bytes, pos: int) -> int:
    return int.from_bytes(b[pos:pos+4], "little", signed=False) if pos + 4 <= len(b) else 0


def plausible_header_len(n: int, size: int) -> bool:
    return 32 <= n < min(size, 20000) and n % 1 == 0


def plausible_record_len(n: int) -> bool:
    return 1 <= n < 100000


def parse_dbf(path: Path, limit: int = 100000) -> Tuple[List[Dict[str, str]], Dict[str, Any]]:
    meta: Dict[str, Any] = {
        "path": str(path),
        "exists": int(path.exists()),
        "fields": [],
        "records_read": 0,
        "parse_warning": "",
    }
    if not path.exists():
        meta["parse_warning"] = "missing_dbf"
        return [], meta

    data = path.read_bytes()
    size = len(data)
    if size < 64:
        meta["parse_warning"] = "file_too_small"
        return [], meta

    # Header length and record length support both standard DBF and x64base extended header patterns.
    std_header_len = le16(data, 8)
    std_record_len = le16(data, 10)
    ext_header_len = le32(data, 0x28)
    ext_record_len = le32(data, 0x30)

    header_len = std_header_len if plausible_header_len(std_header_len, size) else ext_header_len
    if not plausible_header_len(header_len, size):
        header_len = 0
        for pos in range(32, min(size, 4096)):
            if data[pos] == 0x0D:
                header_len = pos + 1
                break
    if not plausible_header_len(header_len, size):
        meta["parse_warning"] = "could_not_determine_header_len"
        return [], meta

    record_len = std_record_len if plausible_record_len(std_record_len) else ext_record_len
    if not plausible_record_len(record_len):
        meta["parse_warning"] = "could_not_determine_record_len"
        return [], meta

    descriptor_start = 96 if size > 96 and data[96] not in (0x00, 0x0D) and 96 < header_len else 32
    fields: List[Dict[str, Any]] = []
    pos = descriptor_start
    while pos + 32 <= size and pos < header_len:
        if data[pos] == 0x0D:
            break
        desc = data[pos:pos+32]
        raw_name = desc[:11].split(b"\x00", 1)[0].decode("ascii", errors="ignore").strip()
        if not raw_name:
            break
        ftype = chr(desc[11]) if 32 <= desc[11] < 127 else "C"
        std_off = le32(desc, 12)
        std_len = desc[16]
        # x64base variants may carry widened length. Prefer standard byte when plausible.
        len_candidates = [std_len, le16(desc, 16), le32(desc, 16), le32(desc, 20), le32(desc, 24)]
        flen = next((x for x in len_candidates if 0 < x <= record_len), std_len)
        fields.append({"name": raw_name.upper(), "type": ftype, "offset": std_off, "length": flen})
        pos += 32

    # If stored offsets are invalid, compute sequential offsets from the deletion flag.
    if fields:
        invalid_offsets = any(f["offset"] <= 0 or f["offset"] + f["length"] > record_len for f in fields)
        if invalid_offsets:
            off = 1
            for f in fields:
                f["offset"] = off
                off += int(f["length"])

    meta["fields"] = [dict(f) for f in fields]
    meta["field_count"] = len(fields)
    meta["header_len"] = header_len
    meta["record_len"] = record_len
    meta["descriptor_start"] = descriptor_start

    if not fields:
        meta["parse_warning"] = "no_fields_found"
        return [], meta

    max_records = max(0, (size - header_len) // record_len)
    rows: List[Dict[str, str]] = []
    for i in range(min(max_records, limit)):
        start = header_len + i * record_len
        rec = data[start:start+record_len]
        if len(rec) < record_len:
            continue
        if rec[0:1] == b"*":
            continue
        if rec[0:1] == b"\x1A":
            break
        row: Dict[str, str] = {}
        for f in fields:
            off = int(f["offset"])
            flen = int(f["length"])
            raw = rec[off:off+flen]
            val = raw.decode("utf-8", errors="replace").strip()
            row[f["name"]] = val
        rows.append(row)
    meta["records_read"] = len(rows)
    return rows, meta


def norm(s: Any) -> str:
    return str(s or "").strip().upper()


def load_active_catalog(repo: Path) -> Tuple[Dict[str, List[Dict[str, str]]], List[Dict[str, Any]]]:
    active: Dict[str, List[Dict[str, str]]] = {}
    metas: List[Dict[str, Any]] = []
    root = repo / "dottalkpp/data/datadict"
    for table in TARGET_TABLES:
        rows, meta = parse_dbf(root / f"{table}.dbf")
        active[table] = rows
        meta["table"] = table
        metas.append(meta)
    return active, metas


def compare_ddobject(candidate_rows: List[Dict[str, str]], active_rows: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    active_by_key = {}
    for r in active_rows:
        key = (norm(r.get("OBJTYPE")), norm(r.get("OWNER")), norm(r.get("NAME")))
        active_by_key.setdefault(key, []).append(r)

    out = []
    for c in candidate_rows:
        key = (norm(c.get("objtype")), norm(c.get("owner")), norm(c.get("name")))
        matches = active_by_key.get(key, [])
        out.append({
            "family": "DDOBJECT",
            "candidate_row_id": c.get("candidate_row_id", ""),
            "candidate_key": "|".join(key),
            "candidate_name": c.get("name", ""),
            "candidate_type": c.get("objtype", ""),
            "active_match_count": len(matches),
            "review_status": "DUPLICATE_REVIEW" if matches else "NEW_CANDIDATE_REVIEW",
            "active_objids": ";".join(r.get("OBJID", "") for r in matches[:5]),
            "apply_now": c.get("apply_now", "0"),
        })
    return out


def compare_ddattr(candidate_rows: List[Dict[str, str]], active_rows: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    # Active DDATTR may use ATTRNAME/ATTRVAL/OBJID.
    active_keys = {}
    for r in active_rows:
        key = (norm(r.get("OBJID")), norm(r.get("ATTRNAME")), norm(r.get("ATTRVAL")))
        active_keys.setdefault(key, []).append(r)

    out = []
    for c in candidate_rows:
        key = (norm(c.get("objid")), norm(c.get("attrname")), norm(c.get("attrval")))
        matches = active_keys.get(key, [])
        # Candidate objids are stable DD096A ids and may not match active ids. Also detect same attr/value.
        attr_value_matches = [
            r for r in active_rows
            if norm(r.get("ATTRNAME")) == norm(c.get("attrname")) and norm(r.get("ATTRVAL")) == norm(c.get("attrval"))
        ]
        out.append({
            "family": "DDATTR",
            "candidate_row_id": c.get("candidate_row_id", ""),
            "candidate_key": "|".join(key),
            "candidate_attrname": c.get("attrname", ""),
            "active_exact_match_count": len(matches),
            "active_attr_value_match_count": len(attr_value_matches),
            "review_status": "DUPLICATE_REVIEW" if matches else "POSSIBLE_DUPLICATE_REVIEW" if attr_value_matches else "NEW_CANDIDATE_REVIEW",
            "active_attrids": ";".join(r.get("ATTRID", "") for r in (matches or attr_value_matches)[:5]),
            "apply_now": c.get("apply_now", "0"),
        })
    return out


def compare_generic(candidate_rows: List[Dict[str, str]], active_rows: List[Dict[str, str]], family: str, candidate_name_fields: List[str], active_name_fields: List[str]) -> List[Dict[str, Any]]:
    active_keys = {}
    for r in active_rows:
        key = tuple(norm(r.get(f)) for f in active_name_fields)
        active_keys.setdefault(key, []).append(r)

    out = []
    for c in candidate_rows:
        key = tuple(norm(c.get(f)) for f in candidate_name_fields)
        matches = active_keys.get(key, [])
        out.append({
            "family": family,
            "candidate_row_id": c.get("candidate_row_id", ""),
            "candidate_key": "|".join(key),
            "active_match_count": len(matches),
            "review_status": "DUPLICATE_REVIEW" if matches else "NEW_CANDIDATE_REVIEW",
            "apply_now": c.get("apply_now", "0"),
        })
    return out


def make_report(run_id: str, status: str, counts: Dict[str, int]) -> str:
    return f"""# DD096B Candidate Catalog-Row Review / Deduplication

Run id: `{run_id}`
Created UTC: `{utc_now()}`
Status: **{status}**

## Purpose

DD096B performs a read-only comparison between DD096A candidate catalog rows and the active Data Dictionary catalog DBFs.

It does not write DBFs, mutate indexes, rebuild LMDB, edit HELP/CMDHELPCHK, edit source, or apply schema promotion.

## Review counts

- Candidates reviewed: **{counts['candidate_total']}**
- Duplicate/review rows: **{counts['duplicate_or_possible']}**
- New candidate review rows: **{counts['new_candidate']}**
- Active catalog tables parsed: **{counts['active_tables_parsed']} / 5**
- Apply-now total: **{counts['apply_now_total']}**

## Interpretation

DD096B is not an apply stage. It sorts candidates into review buckets so a later design/apply lane can avoid duplicate catalog entries and preserve provenance.

## Boundary

DD096B is read-only review/deduplication. It does not edit C++ source, edit build files, edit command registration,
mutate active catalog DBFs, append/replace/delete/pack/zap DBFs, create/rebuild CDX/LMDB,
mutate HELP/META/CMDHELPCHK, regenerate catalog content, or repair manual rows.
"""


def main() -> int:
    ap = argparse.ArgumentParser(description="DD096B read-only candidate catalog-row review/deduplication")
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--run-id", default="DD096B-candidate-catalog-row-review-dedup-v0")
    ap.add_argument("--dd096a-dir", default="docs/datadict/reports/DD096A-candidate-catalog-row-design-v0")
    ap.add_argument("--dd098-dir", default="docs/datadict/reports/DD098-datadict-baseline-closeout-v0")
    ap.add_argument("--candidate-dir", default=DEFAULT_CANDIDATE_DIR)
    ap.add_argument("--profile", action="append", default=[])
    ap.add_argument("--fail-on-review", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    out = Path(args.out_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)

    dd096a_manifest_path = repo / args.dd096a_dir / "dd096a_candidate_catalog_row_design_manifest.json"
    dd098_manifest_path = repo / args.dd098_dir / "dd098_datadict_baseline_closeout_manifest.json"
    dd096a = read_json(dd096a_manifest_path)
    dd098 = read_json(dd098_manifest_path)

    cdir = repo / args.candidate_dir
    cand_ddobject = read_csv(cdir / "dd096a_candidate_ddobject_rows.csv")
    cand_ddattr = read_csv(cdir / "dd096a_candidate_ddattr_rows.csv")
    cand_ddedge = read_csv(cdir / "dd096a_candidate_ddedge_rows.csv")
    cand_ddevid = read_csv(cdir / "dd096a_candidate_ddevid_rows.csv")
    cand_ddgate = read_csv(cdir / "dd096a_candidate_ddgate_rows.csv")

    active, active_metas = load_active_catalog(repo)

    review_rows = []
    review_rows.extend(compare_ddobject(cand_ddobject, active.get("DDOBJECT", [])))
    review_rows.extend(compare_ddattr(cand_ddattr, active.get("DDATTR", [])))
    review_rows.extend(compare_generic(cand_ddedge, active.get("DDEDGE", []), "DDEDGE", ["from_name", "to_name", "edge_type", "key"], ["FROMNAME", "TONAME", "EDGETYPE", "KEY"]))
    review_rows.extend(compare_generic(cand_ddevid, active.get("DDEVID", []), "DDEVID", ["source", "kind"], ["SOURCE", "KIND"]))
    review_rows.extend(compare_generic(cand_ddgate, active.get("DDGATE", []), "DDGATE", ["gate_id", "gate_type"], ["GATEID", "GATETYPE"]))

    generated = out / "generated_candidate_review"
    generated.mkdir(parents=True, exist_ok=True)

    write_csv(generated / "dd096b_candidate_review_all.csv", review_rows, ["family", "candidate_row_id", "candidate_key", "candidate_name", "candidate_type", "candidate_attrname", "active_match_count", "active_exact_match_count", "active_attr_value_match_count", "review_status", "active_objids", "active_attrids", "apply_now"])
    duplicate_rows = [r for r in review_rows if r.get("review_status") in {"DUPLICATE_REVIEW", "POSSIBLE_DUPLICATE_REVIEW"}]
    new_rows = [r for r in review_rows if r.get("review_status") == "NEW_CANDIDATE_REVIEW"]
    write_csv(generated / "dd096b_duplicate_review_rows.csv", duplicate_rows, ["family", "candidate_row_id", "candidate_key", "review_status", "active_match_count", "active_exact_match_count", "active_attr_value_match_count", "active_objids", "active_attrids"])
    write_csv(generated / "dd096b_new_candidate_review_rows.csv", new_rows, ["family", "candidate_row_id", "candidate_key", "review_status", "apply_now"])
    write_json(generated / "dd096b_candidate_review_summary.json", {
        "run_id": args.run_id,
        "created_utc": utc_now(),
        "review_rows": len(review_rows),
        "duplicate_or_possible": len(duplicate_rows),
        "new_candidate": len(new_rows),
        "active_dbf_meta": active_metas,
    })

    candidate_total = len(cand_ddobject) + len(cand_ddattr) + len(cand_ddedge) + len(cand_ddevid) + len(cand_ddgate)
    apply_now_total = 0
    for rows in [cand_ddobject, cand_ddattr, cand_ddedge, cand_ddevid, cand_ddgate]:
        for r in rows:
            try:
                apply_now_total += int(str(r.get("apply_now", "0")).strip() or "0")
            except ValueError:
                apply_now_total += 1

    active_tables_parsed = sum(1 for m in active_metas if int(m.get("records_read", 0)) >= 0 and not m.get("parse_warning"))
    counts = {
        "candidate_total": candidate_total,
        "duplicate_or_possible": len(duplicate_rows),
        "new_candidate": len(new_rows),
        "active_tables_parsed": active_tables_parsed,
        "apply_now_total": apply_now_total,
    }

    status = "DATADICT_CANDIDATE_ROW_REVIEW_DEDUP_READY"
    gate_rows = [
        {"gate": "dd096a_ready", "expected": EXPECTED_DD096A_STATUS, "observed": dd096a.get("status", ""), "pass": int(dd096a.get("status") == EXPECTED_DD096A_STATUS)},
        {"gate": "dd098_closed", "expected": EXPECTED_DD098_STATUS, "observed": dd098.get("status", ""), "pass": int(dd098.get("status") == EXPECTED_DD098_STATUS)},
        {"gate": "candidate_total_matches_manifest", "expected": dd096a.get("candidate_counts", {}).get("all", ""), "observed": candidate_total, "pass": int(str(dd096a.get("candidate_counts", {}).get("all", "")) == str(candidate_total))},
        {"gate": "review_rows_match_candidates", "expected": candidate_total, "observed": len(review_rows), "pass": int(candidate_total == len(review_rows))},
        {"gate": "active_dbfs_parsed", "expected": 5, "observed": active_tables_parsed, "pass": int(active_tables_parsed == 5)},
        {"gate": "apply_now_zero", "expected": 0, "observed": apply_now_total, "pass": int(apply_now_total == 0)},
    ]
    failures = sum(1 for r in gate_rows if int(r["pass"]) != 1)
    if failures:
        status = "DATADICT_CANDIDATE_ROW_REVIEW_DEDUP_REVIEW"

    boundary_rows = [
        {"boundary": "candidate_row_review_read_only", "observed": 1, "required": 1, "pass": 1},
        {"boundary": "apply_now_total", "observed": apply_now_total, "required": 0, "pass": int(apply_now_total == 0)},
        {"boundary": "cxx_source_edits", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "build_file_edits", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "registry_edits", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "active_catalog_mutation", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "dbf_append_replace_delete_pack_zap", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "cdx_lmdb_create_rebuild", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "help_meta_cmdhelpchk_mutation", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "catalog_regeneration", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "manual_row_repair", "observed": 0, "required": 0, "pass": 1},
    ]

    artifact_rows = [
        artifact_row(repo, str(dd096a_manifest_path.relative_to(repo)), "dd096a_manifest"),
        artifact_row(repo, str(dd098_manifest_path.relative_to(repo)), "dd098_manifest"),
        artifact_row(repo, args.candidate_dir, "candidate_dir"),
    ]
    for p in PROTECTED_ARTIFACTS:
        artifact_rows.append(artifact_row(repo, p, "protected_observed"))
    for f in sorted(generated.iterdir()):
        if f.is_file():
            artifact_rows.append({"role": "generated_review", "path": str(f), "exists": 1, "kind": "file", "bytes_or_children": f.stat().st_size, "sha256": sha256(f)})

    next_rows = [
        {"next_id": "DD096C", "title": "candidate row acceptance plan", "allowed_scope": "plan only; no DBF writes"},
        {"next_id": "DD092D", "title": "guarded HELP/CMDHELPCHK apply planning", "allowed_scope": "only after explicit authorization"},
        {"next_id": "DD099", "title": "baseline-to-manual integration report", "allowed_scope": "documentation/explanation only"},
    ]

    write_csv(out / "dd096b_active_dbf_parse_ledger.csv", active_metas, ["table", "path", "exists", "field_count", "records_read", "header_len", "record_len", "descriptor_start", "parse_warning"])
    write_csv(out / "dd096b_gate_ledger.csv", gate_rows, ["gate", "expected", "observed", "pass"])
    write_csv(out / "dd096b_no_mutation_boundary_ledger.csv", boundary_rows, ["boundary", "observed", "required", "pass"])
    write_csv(out / "dd096b_artifact_ledger.csv", artifact_rows, ["role", "path", "exists", "kind", "bytes_or_children", "sha256"])
    write_csv(out / "dd096b_next_lane_recommendations.csv", next_rows, ["next_id", "title", "allowed_scope"])
    write_text(out / "DD096B_CANDIDATE_ROW_REVIEW_DEDUP_REPORT.md", make_report(args.run_id, status, counts))

    manifest = {
        "contract": "dd096b_candidate_catalog_row_review_dedup_v0",
        "run_id": args.run_id,
        "created_utc": utc_now(),
        "status": status,
        "repo_root": str(repo),
        "profiles": args.profile,
        "candidate_total": candidate_total,
        "review_rows": len(review_rows),
        "duplicate_or_possible_review_rows": len(duplicate_rows),
        "new_candidate_review_rows": len(new_rows),
        "active_tables_parsed": active_tables_parsed,
        "apply_now_total": apply_now_total,
        "failures": failures,
        "cxx_source_edits": 0,
        "build_file_edits": 0,
        "registry_edits": 0,
        "active_catalog_mutation": 0,
        "dbf_append_replace_delete_pack_zap": 0,
        "cdx_lmdb_create_rebuild": 0,
        "help_meta_cmdhelpchk_mutation": 0,
        "catalog_regeneration": 0,
        "manual_row_repair": 0,
        "next_recommended_action": "DD096C candidate row acceptance plan, still no DBF writes.",
    }
    write_json(out / "dd096b_candidate_catalog_row_review_dedup_manifest.json", manifest)

    print(f"DD096B candidate row review/dedup manifest: {out / 'dd096b_candidate_catalog_row_review_dedup_manifest.json'}")
    print(f"status: {status}; candidates: {candidate_total}; duplicate_or_possible: {len(duplicate_rows)}; new_candidate: {len(new_rows)}; active_tables_parsed: {active_tables_parsed}/5; apply_now: {apply_now_total}; failures: {failures}")
    return 2 if (args.fail_on_review and failures) else 0


if __name__ == "__main__":
    raise SystemExit(main())
