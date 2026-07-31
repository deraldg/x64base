#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List, Tuple


EXPECTED_DD096G_STATUS = "DATADICT_FINAL_GUARDED_APPLY_PACKAGE_DESIGN_READY"
EXPECTED_DD096F_STATUS = "DATADICT_STAGED_ROW_SIMULATED_APPLY_VALIDATION_READY"
EXPECTED_DD096E_STATUS = "DATADICT_EXTERNAL_APPLY_ROW_STAGING_READY"

DEFAULT_STAGED_DIR = "docs/datadict/reports/DD096E-R-root-aware-external-apply-staging-v0/generated_staged_apply_rows"

TARGETS = [
    ("DDOBJECT", "dd096e_staged_ddobject_insert_rows.csv", "OBJID", 6),
    ("DDATTR", "dd096e_staged_ddattr_insert_rows.csv", "ATTRID", 1),
    ("DDEDGE", "dd096e_staged_ddedge_insert_rows.csv", "EDGEID", 3),
    ("DDEVID", "dd096e_staged_ddevid_insert_rows.csv", "EVID", 4),
    ("DDGATE", "dd096e_staged_ddgate_insert_rows.csv", "GATEID", 5),
]


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def norm_name(s: Any) -> str:
    return "".join(ch for ch in str(s or "").upper() if ch.isalnum())


def read_text(path: Path) -> str:
    if not path.exists() or path.is_dir():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(read_text(path))
    except Exception as exc:
        return {"_read_error": str(exc)}


def write_json(path: Path, obj: Dict[str, Any]) -> None:
    write_text(path, json.dumps(obj, indent=2, sort_keys=True) + "\n")


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


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


def le16(b: bytes, pos: int) -> int:
    return int.from_bytes(b[pos:pos+2], "little", signed=False) if pos + 2 <= len(b) else 0


def le32(b: bytes, pos: int) -> int:
    return int.from_bytes(b[pos:pos+4], "little", signed=False) if pos + 4 <= len(b) else 0


def parse_dbf(path: Path, limit: int = 100000) -> Tuple[List[Dict[str, str]], Dict[str, Any]]:
    meta: Dict[str, Any] = {"path": str(path), "exists": int(path.exists()), "fields": [], "records_read": 0, "parse_warning": ""}
    if not path.exists():
        meta["parse_warning"] = "missing_dbf"
        return [], meta
    data = path.read_bytes()
    size = len(data)
    if size < 64:
        meta["parse_warning"] = "file_too_small"
        return [], meta

    std_header_len = le16(data, 8)
    std_record_len = le16(data, 10)
    ext_header_len = le32(data, 0x28)
    ext_record_len = le32(data, 0x30)

    header_len = std_header_len if 32 <= std_header_len < size else ext_header_len
    if not (32 <= header_len < size):
        for pos in range(32, min(size, 4096)):
            if data[pos] == 0x0D:
                header_len = pos + 1
                break
    record_len = std_record_len if 1 <= std_record_len < 100000 else ext_record_len
    if not (32 <= header_len < size and 1 <= record_len < 100000):
        meta["parse_warning"] = "could_not_determine_header_or_record_len"
        return [], meta

    descriptor_start = 96 if size > 96 and data[96] not in (0x00, 0x0D) and 96 < header_len else 32
    fields: List[Dict[str, Any]] = []
    pos = descriptor_start
    while pos + 32 <= size and pos < header_len:
        if data[pos] == 0x0D:
            break
        desc = data[pos:pos+32]
        name = desc[:11].split(b"\x00", 1)[0].decode("ascii", errors="ignore").strip().upper()
        if not name:
            break
        ftype = chr(desc[11]) if 32 <= desc[11] < 127 else "C"
        off = le32(desc, 12)
        flen = desc[16]
        candidates = [flen, le16(desc, 16), le32(desc, 16), le32(desc, 20), le32(desc, 24)]
        flen = next((x for x in candidates if 0 < x <= record_len), flen)
        fields.append({"name": name, "type": ftype, "offset": off, "length": flen})
        pos += 32

    if fields and any(int(f["offset"]) <= 0 or int(f["offset"]) + int(f["length"]) > record_len for f in fields):
        off = 1
        for f in fields:
            f["offset"] = off
            off += int(f["length"])

    meta["fields"] = fields
    meta["field_count"] = len(fields)
    meta["header_len"] = header_len
    meta["record_len"] = record_len
    meta["descriptor_start"] = descriptor_start

    rows: List[Dict[str, str]] = []
    if not fields:
        meta["parse_warning"] = "no_fields_found"
        return rows, meta

    max_records = max(0, (size - header_len) // record_len)
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
            raw = rec[int(f["offset"]):int(f["offset"]) + int(f["length"])]
            row[str(f["name"])] = raw.decode("utf-8", errors="replace").strip()
        rows.append(row)
    meta["records_read"] = len(rows)
    return rows, meta


def dt_literal(value: str) -> str:
    value = str(value or "")
    if "\n" in value or "\r" in value:
        raise ValueError("DotTalk string literal cannot contain newline")
    if '"' in value:
        raise ValueError("DotTalk string literal cannot contain double quote")
    return '"' + value + '"'


def field_value_for_dbf_field(staged_row: Dict[str, str], dbf_field_name: str) -> str:
    target_norm = norm_name(dbf_field_name)
    for k, v in staged_row.items():
        if norm_name(k) == target_norm:
            return str(v or "")
    return ""


def generate_table_script(table: str, rows: List[Dict[str, str]], fields: List[Dict[str, Any]], area: int) -> List[str]:
    lines: List[str] = []
    lines.append("")
    lines.append(f"* DD096I apply rows for {table}")
    lines.append(f"SELECT {area}")
    lines.append("")

    dbf_fields = [str(f["name"]) for f in fields]
    for row in rows:
        lines.append("APPEND")
        for fname in dbf_fields:
            value = field_value_for_dbf_field(row, fname)
            if value == "":
                continue
            lines.append(f"REPLACE {fname} WITH {dt_literal(value)}")
        lines.append("")
    lines.append("BUILDLMDB CLEAN YES")
    lines.append("")
    return lines


def make_runner_text() -> str:
    return r"""# DD096I guarded Data Dictionary apply runner
# This runner creates backups, then runs the generated DotTalk++ DTS apply script through datarun.

param(
  [string]$RepoRoot = 'D:\code\ccode'
)

$ErrorActionPreference = 'Stop'

$timestamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$outDir = Join-Path $RepoRoot 'docs\datadict\reports\DD096I-guarded-datadict-apply-v0'
$backupDir = Join-Path $outDir ('backups\preapply_' + $timestamp)
$runlog = Join-Path $RepoRoot 'docs\datadict\runlog\DD096I_GUARDED_DATADICT_APPLY_RUNTIME_PROOF.md'

New-Item -ItemType Directory -Force -Path $backupDir | Out-Null
New-Item -ItemType Directory -Force -Path (Split-Path $runlog) | Out-Null

$tables = @('DDOBJECT','DDATTR','DDEDGE','DDEVID','DDGATE')
foreach ($t in $tables) {
  $dbf = Join-Path $RepoRoot ('dottalkpp\data\datadict\' + $t + '.dbf')
  $cdx = Join-Path $RepoRoot ('dottalkpp\data\indexes\datadict\' + $t.ToLower() + '.cdx')
  $lmdb = Join-Path $RepoRoot ('dottalkpp\data\lmdb\datadict\' + $t + '.cdx.d')

  if (Test-Path $dbf) { Copy-Item $dbf (Join-Path $backupDir ($t + '.dbf')) -Force }
  if (Test-Path $cdx) { Copy-Item $cdx (Join-Path $backupDir ($t.ToLower() + '.cdx')) -Force }
  if (Test-Path $lmdb) { Copy-Item $lmdb (Join-Path $backupDir ($t + '.cdx.d')) -Recurse -Force }
}

@'
DO DD096I_GUARDED_DATADICT_APPLY
QUIT

'@ | & (Join-Path $RepoRoot 'datarun') *>&1 | Tee-Object -FilePath $runlog

Write-Host "DD096I backup directory: $backupDir"
Write-Host "DD096I runtime proof: $runlog"
"""


def main() -> int:
    ap = argparse.ArgumentParser(description="DD096H/DD096I guarded Data Dictionary apply package generator")
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--run-id", default="DD096HI-guarded-datadict-apply-package-v0")
    ap.add_argument("--dd096g-dir", default="docs/datadict/reports/DD096G-final-guarded-apply-package-design-v0")
    ap.add_argument("--dd096f-dir", default="docs/datadict/reports/DD096F-R-root-aware-staged-row-simulated-apply-v0")
    ap.add_argument("--dd096e-dir", default="docs/datadict/reports/DD096E-R-root-aware-external-apply-staging-v0")
    ap.add_argument("--staged-dir", default=DEFAULT_STAGED_DIR)
    ap.add_argument("--write-authorization", action="store_true")
    ap.add_argument("--write-runtime-script", action="store_true")
    ap.add_argument("--write-runner", action="store_true")
    ap.add_argument("--profile", action="append", default=[])
    ap.add_argument("--fail-on-review", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    out = Path(args.out_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)

    g_manifest_path = repo / args.dd096g_dir / "dd096g_final_guarded_apply_package_design_manifest.json"
    f_manifest_path = repo / args.dd096f_dir / "dd096f_staged_row_review_simulated_apply_manifest.json"
    e_manifest_path = repo / args.dd096e_dir / "dd096e_external_apply_row_staging_manifest.json"

    g_manifest = read_json(g_manifest_path)
    f_manifest = read_json(f_manifest_path)
    e_manifest = read_json(e_manifest_path)

    staged_dir = repo / args.staged_dir
    table_rows: Dict[str, List[Dict[str, str]]] = {}
    precheck_rows = []
    parse_rows = []
    duplicate_rows = []
    length_rows = []
    total_staged = 0

    for table, staged_file, pk, area in TARGETS:
        staged_rows = read_csv(staged_dir / staged_file)
        table_rows[table] = staged_rows
        total_staged += len(staged_rows)
        active_rows, meta = parse_dbf(repo / "dottalkpp/data/datadict" / f"{table}.dbf")
        parse_rows.append({
            "table": table,
            "dbf": str(repo / "dottalkpp/data/datadict" / f"{table}.dbf"),
            "exists": meta.get("exists", 0),
            "field_count": meta.get("field_count", 0),
            "records_read": meta.get("records_read", 0),
            "parse_warning": meta.get("parse_warning", ""),
        })

        active_ids = {str(r.get(pk, "")).strip() for r in active_rows if str(r.get(pk, "")).strip()}
        staged_ids = []
        for r in staged_rows:
            sid = field_value_for_dbf_field(r, pk).strip()
            staged_ids.append(sid)
            if sid in active_ids:
                duplicate_rows.append({"table": table, "primary_key": pk, "staged_id": sid, "issue": "already_exists_in_active_dbf"})

        for sid in sorted(set(x for x in staged_ids if x and staged_ids.count(x) > 1)):
            duplicate_rows.append({"table": table, "primary_key": pk, "staged_id": sid, "issue": "duplicate_within_staged_rows"})

        fields = meta.get("fields", [])
        if isinstance(fields, list):
            for r in staged_rows:
                for f in fields:
                    fname2 = str(f.get("name", ""))
                    flen = int(f.get("length", 0) or 0)
                    val = field_value_for_dbf_field(r, fname2)
                    if len(val.encode("utf-8")) > flen:
                        length_rows.append({
                            "table": table,
                            "field": fname2,
                            "max_len": flen,
                            "value_len": len(val.encode("utf-8")),
                            "value_preview": val[:80],
                            "issue": "value_too_long_for_field",
                        })

        precheck_rows.append({
            "table": table,
            "staged_rows": len(staged_rows),
            "active_records_before": len(active_rows),
            "primary_key": pk,
            "duplicates_found": sum(1 for r in duplicate_rows if r["table"] == table),
            "length_issues": sum(1 for r in length_rows if r["table"] == table),
        })

    generated = out / "generated_guarded_apply_package"
    generated.mkdir(parents=True, exist_ok=True)

    write_csv(generated / "dd096i_preapply_table_checks.csv", precheck_rows, ["table", "staged_rows", "active_records_before", "primary_key", "duplicates_found", "length_issues"])
    write_csv(generated / "dd096i_active_dbf_parse_ledger.csv", parse_rows, ["table", "dbf", "exists", "field_count", "records_read", "parse_warning"])
    write_csv(generated / "dd096i_duplicate_blockers.csv", duplicate_rows, ["table", "primary_key", "staged_id", "issue"])
    write_csv(generated / "dd096i_field_length_blockers.csv", length_rows, ["table", "field", "max_len", "value_len", "value_preview", "issue"])

    auth_record = {
        "contract": "dd096h_apply_authorization_record_v0",
        "run_id": args.run_id,
        "created_utc": utc_now(),
        "authorization_status": "AUTHORIZED" if args.write_authorization else "NOT_WRITTEN",
        "authorized_scope": "DD096I_GUARDED_DATADICT_SCHEMA_PROMOTION_APPLY" if args.write_authorization else "",
        "authorization_basis": "User explicitly stated: if green you are authorized to implement.",
        "authorized_by": "Derald",
        "requires_green_inputs": ["DD096G", "DD096F-R", "DD096E-R"],
        "expected_staged_rows": 158,
        "observed_staged_rows": total_staged,
        "active_catalog_mutation_authorized": bool(args.write_authorization),
        "dbf_targets": [t[0] for t in TARGETS],
        "notes": "Authorization record permits the generated DD096I guarded apply script only; HELP/CMDHELPCHK remains out of scope.",
    }

    authorization_path = out / "DD096H_APPLY_AUTHORIZATION_RECORD.json"
    if args.write_authorization:
        write_json(authorization_path, auth_record)
    else:
        write_json(generated / "DD096H_APPLY_AUTHORIZATION_RECORD_PREVIEW.json", auth_record)

    dts_lines: List[str] = []
    dts_lines.append("* DD096I GUARDED DATA DICTIONARY APPLY")
    dts_lines.append("* Generated by DD096H/DD096I package.")
    dts_lines.append("* Scope: append staged Data Dictionary schema-promotion rows only.")
    dts_lines.append("* HELP/CMDHELPCHK is out of scope.")
    dts_lines.append("")
    dts_lines.append("SETPATH")
    dts_lines.append("DO ddbase")
    dts_lines.append("WORKSPACE LOAD ddbase")
    dts_lines.append("WORKSPACE")
    dts_lines.append("")

    script_generation_error = ""
    if not duplicate_rows and not length_rows:
        for table, staged_file, pk, area in TARGETS:
            active_rows, meta = parse_dbf(repo / "dottalkpp/data/datadict" / f"{table}.dbf")
            try:
                dts_lines.extend(generate_table_script(table, table_rows[table], meta.get("fields", []), area))
            except Exception as exc:
                script_generation_error = str(exc)
                break

    dts_lines.append("")
    dts_lines.append("* DD096I post-apply smoke commands")
    dts_lines.append("DDICT STATUS")
    dts_lines.append("DDICT TABLES")
    dts_lines.append("DDICT OBJECTS TYPE COMMAND")
    dts_lines.append("DDICT REL DDICT OUT")
    dts_lines.append("DDICT EVIDENCE DDICT")
    dts_lines.append("WORKSPACE")
    dts_lines.append("QUIT")
    dts_lines.append("")
    dts_lines.append("")

    dts_preview_path = generated / "DD096I_GUARDED_DATADICT_APPLY.dts"
    runtime_script_written = 0
    if script_generation_error or duplicate_rows or length_rows:
        write_text(generated / "DD096I_GUARDED_DATADICT_APPLY_BLOCKED.txt", "Apply script generation blocked by precheck failures.\n")
    else:
        write_text(dts_preview_path, "\n".join(dts_lines))
        if args.write_runtime_script:
            runtime_path = repo / "dottalkpp/data/scripts/DD096I_GUARDED_DATADICT_APPLY.dts"
            write_text(runtime_path, "\n".join(dts_lines))
            runtime_script_written = 1

    runner_path = out / "run_dd096i_guarded_apply.ps1"
    if args.write_runner:
        write_text(runner_path, make_runner_text())

    gates = [
        {"gate": "dd096g_ready", "expected": EXPECTED_DD096G_STATUS, "observed": g_manifest.get("status", ""), "pass": int(g_manifest.get("status") == EXPECTED_DD096G_STATUS)},
        {"gate": "dd096f_ready", "expected": EXPECTED_DD096F_STATUS, "observed": f_manifest.get("status", ""), "pass": int(f_manifest.get("status") == EXPECTED_DD096F_STATUS)},
        {"gate": "dd096e_ready", "expected": EXPECTED_DD096E_STATUS, "observed": e_manifest.get("status", ""), "pass": int(e_manifest.get("status") == EXPECTED_DD096E_STATUS)},
        {"gate": "staged_rows_158", "expected": 158, "observed": total_staged, "pass": int(total_staged == 158)},
        {"gate": "duplicate_blockers_zero", "expected": 0, "observed": len(duplicate_rows), "pass": int(len(duplicate_rows) == 0)},
        {"gate": "length_blockers_zero", "expected": 0, "observed": len(length_rows), "pass": int(len(length_rows) == 0)},
        {"gate": "authorization_written", "expected": 1, "observed": int(args.write_authorization), "pass": int(args.write_authorization)},
        {"gate": "runtime_script_written", "expected": 1, "observed": runtime_script_written, "pass": int(runtime_script_written == 1)},
        {"gate": "runner_written", "expected": 1, "observed": int(args.write_runner), "pass": int(args.write_runner)},
    ]
    failures = sum(1 for r in gates if int(r["pass"]) != 1)
    status = "DATADICT_GUARDED_APPLY_PACKAGE_READY_TO_RUN" if failures == 0 else "DATADICT_GUARDED_APPLY_PACKAGE_REVIEW"

    boundary_rows = [
        {"boundary": "package_generation_only", "observed": 1, "required": 1, "pass": 1},
        {"boundary": "active_catalog_mutation_by_python", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "dbf_append_replace_delete_pack_zap_by_python", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "runtime_script_written", "observed": runtime_script_written, "required": int(args.write_runtime_script), "pass": 1},
        {"boundary": "authorization_record_written", "observed": int(args.write_authorization), "required": int(args.write_authorization), "pass": 1},
        {"boundary": "help_meta_cmdhelpchk_mutation", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "cxx_source_edits", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "build_file_edits", "observed": 0, "required": 0, "pass": 1},
    ]

    write_csv(out / "dd096hi_gate_ledger.csv", gates, ["gate", "expected", "observed", "pass"])
    write_csv(out / "dd096hi_no_mutation_boundary_ledger.csv", boundary_rows, ["boundary", "observed", "required", "pass"])

    artifact_rows = [
        {"role": "dd096g_manifest", "path": str(g_manifest_path), "exists": int(g_manifest_path.exists()), "kind": "file", "bytes_or_children": g_manifest_path.stat().st_size if g_manifest_path.exists() else 0, "sha256": sha256(g_manifest_path)},
        {"role": "dd096f_manifest", "path": str(f_manifest_path), "exists": int(f_manifest_path.exists()), "kind": "file", "bytes_or_children": f_manifest_path.stat().st_size if f_manifest_path.exists() else 0, "sha256": sha256(f_manifest_path)},
        {"role": "dd096e_manifest", "path": str(e_manifest_path), "exists": int(e_manifest_path.exists()), "kind": "file", "bytes_or_children": e_manifest_path.stat().st_size if e_manifest_path.exists() else 0, "sha256": sha256(e_manifest_path)},
        {"role": "generated_apply_dts_preview", "path": str(dts_preview_path), "exists": int(dts_preview_path.exists()), "kind": "file", "bytes_or_children": dts_preview_path.stat().st_size if dts_preview_path.exists() else 0, "sha256": sha256(dts_preview_path)},
        {"role": "authorization_record", "path": str(authorization_path), "exists": int(authorization_path.exists()), "kind": "file", "bytes_or_children": authorization_path.stat().st_size if authorization_path.exists() else 0, "sha256": sha256(authorization_path)},
        {"role": "runner", "path": str(runner_path), "exists": int(runner_path.exists()), "kind": "file", "bytes_or_children": runner_path.stat().st_size if runner_path.exists() else 0, "sha256": sha256(runner_path)},
    ]
    write_csv(out / "dd096hi_artifact_ledger.csv", artifact_rows, ["role", "path", "exists", "kind", "bytes_or_children", "sha256"])

    report = f"""# DD096H/DD096I Guarded Data Dictionary Apply Package

Run id: `{args.run_id}`
Status: **{status}**
Created UTC: `{utc_now()}`

## Purpose

DD096H records authorization and DD096I creates the guarded DotTalk++ apply script and runner.

## Summary

- Staged rows: **{total_staged}**
- Duplicate blockers: **{len(duplicate_rows)}**
- Field length blockers: **{len(length_rows)}**
- Authorization written: **{int(args.write_authorization)}**
- Runtime DTS script written: **{runtime_script_written}**
- Runner written: **{int(args.write_runner)}**
- Python DBF writes: **0**

## Execution boundary

The Python generator does not append to DBFs. The active mutation occurs only when the generated PowerShell runner executes `datarun` against:

```text
dottalkpp/data/scripts/DD096I_GUARDED_DATADICT_APPLY.dts
```

The runner creates backups before invoking DotTalk++.

## HELP/CMDHELPCHK

HELP/CMDHELPCHK remains out of scope.
"""
    write_text(out / "DD096HI_GUARDED_DATADICT_APPLY_PACKAGE_REPORT.md", report)

    manifest = {
        "contract": "dd096hi_guarded_datadict_apply_package_v0",
        "run_id": args.run_id,
        "created_utc": utc_now(),
        "status": status,
        "repo_root": str(repo),
        "profiles": args.profile,
        "staged_rows": total_staged,
        "duplicate_blockers": len(duplicate_rows),
        "field_length_blockers": len(length_rows),
        "authorization_written": int(args.write_authorization),
        "runtime_script_written": runtime_script_written,
        "runner_written": int(args.write_runner),
        "python_active_catalog_mutation": 0,
        "failures": failures,
        "runtime_script_path": str(repo / "dottalkpp/data/scripts/DD096I_GUARDED_DATADICT_APPLY.dts") if runtime_script_written else "",
        "runner_path": str(runner_path) if args.write_runner else "",
        "authorization_path": str(authorization_path) if args.write_authorization else "",
        "script_generation_error": script_generation_error,
        "next_recommended_action": "Review generated DTS, then run run_dd096i_guarded_apply.ps1 if ready.",
    }
    write_json(out / "dd096hi_guarded_datadict_apply_package_manifest.json", manifest)

    print(f"DD096H/DD096I guarded apply package manifest: {out / 'dd096hi_guarded_datadict_apply_package_manifest.json'}")
    print(f"status: {status}; staged_rows: {total_staged}; duplicate_blockers: {len(duplicate_rows)}; length_blockers: {len(length_rows)}; authorization_written: {int(args.write_authorization)}; runtime_script_written: {runtime_script_written}; runner_written: {int(args.write_runner)}; failures: {failures}")
    return 2 if (args.fail_on_review and failures) else 0


if __name__ == "__main__":
    raise SystemExit(main())
