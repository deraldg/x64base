#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import py_compile
from datetime import datetime, timezone
from pathlib import Path

STATUS_GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_3_1_2_LITERAL_NEWLINE_REPAIR_APPLIED"
STATUS_BLOCKED = "MESSAGE_CATALOG_PHASE22AE_6_5_3_1_2_LITERAL_NEWLINE_REPAIR_BLOCKED"
NEXT_GATE = "RERUN_PHASE22AE_6_5_3_STAGE_WITH_REPLACE_EXISTING_SANDBOX"

REPORT_DIR = Path("docs/messaging/reports")
BACKUP_DIR = Path("docs/messaging/backups/MSG-022AE_6_5_3_1_2_LITERAL_NEWLINE_REPAIR_TOOL_BACKUP")

STAGE_TOOL = Path("tools/messaging/stage_message_catalog_phase22ae_6_5_3_full_candidate_rebuild.py")
VALIDATE_TOOL = Path("tools/messaging/validate_message_catalog_phase22ae_6_5_3_full_candidate_rebuild.py")

PATCHED_PARSE_STAGE = r'''
def valid_dbf_field_name(name: str) -> bool:
    if not name:
        return False
    if not (name[0].isalpha() or name[0] == "_"):
        return False
    return all(ch.isalnum() or ch == "_" for ch in name)

def parse_dbf(path: Path) -> DbfInfo:
    data = path.read_bytes()
    if len(data) < 32:
        raise RuntimeError(f"DBF too small: {path}")
    record_count = struct.unpack("<I", data[4:8])[0]
    header_len = struct.unpack("<H", data[8:10])[0]
    record_len = struct.unpack("<H", data[10:12])[0]
    fields = []
    pos = 32
    offset = 1
    while pos + 32 <= len(data):
        if data[pos] == 0x0D:
            break
        raw = data[pos:pos+11].split(b"\x00", 1)[0]
        name = raw.decode("ascii", errors="ignore").strip().upper()
        ftype = chr(data[pos+11])
        length = data[pos+16]
        decimals = data[pos+17]

        # DotTalk++ v64 DBF headers can include non-field layout markers.
        # Treat only ordinary field identifiers that fit inside the declared
        # record length as actual fields.
        if valid_dbf_field_name(name) and length > 0 and (offset + length) <= record_len:
            fields.append({"NAME": name, "TYPE": ftype, "LENGTH": length, "DECIMALS": decimals, "OFFSET": offset})
            offset += length
        pos += 32
    return DbfInfo(path, record_count, header_len, record_len, fields)
'''

PATCHED_APPEND = r'''
def append_records_to_dbf(path: Path, rows: list[dict]) -> int:
    info = parse_dbf(path)
    raw = bytearray(path.read_bytes())
    if raw and raw[-1] == 0x1A:
        raw = raw[:-1]
    new_count = info.record_count
    for row in rows:
        rec = bytearray(b" " * info.record_len)
        rec[0] = 0x20
        for fld in info.fields:
            start = int(fld["OFFSET"])
            end = start + int(fld["LENGTH"])
            if start < 1 or end > info.record_len:
                continue
            rec[start:end] = encode_field(fld, row.get(fld["NAME"], ""))
        raw.extend(rec)
        new_count += 1
    raw.extend(b"\x1A")
    raw[4:8] = struct.pack("<I", new_count)
    path.write_bytes(bytes(raw))
    return new_count
'''

PATCHED_PARSE_VALIDATE = r'''
def valid_dbf_field_name(name: str) -> bool:
    if not name:
        return False
    if not (name[0].isalpha() or name[0] == "_"):
        return False
    return all(ch.isalnum() or ch == "_" for ch in name)

def parse_dbf(path: Path) -> DbfInfo:
    data = path.read_bytes()
    if len(data) < 32:
        raise RuntimeError(f"DBF too small: {path}")
    record_count = struct.unpack("<I", data[4:8])[0]
    header_len = struct.unpack("<H", data[8:10])[0]
    record_len = struct.unpack("<H", data[10:12])[0]
    fields = []
    pos = 32
    offset = 1
    while pos + 32 <= len(data):
        if data[pos] == 0x0D:
            break
        raw = data[pos:pos+11].split(b"\x00", 1)[0]
        name = raw.decode("ascii", errors="ignore").strip().upper()
        ftype = chr(data[pos+11])
        length = data[pos+16]
        if valid_dbf_field_name(name) and length > 0 and (offset + length) <= record_len:
            fields.append({"NAME": name, "TYPE": ftype, "LENGTH": length, "OFFSET": offset})
            offset += length
        pos += 32
    return DbfInfo(path, record_count, header_len, record_len, fields)
'''

def sha256_file(path: Path) -> str:
    if not path.exists() or not path.is_file():
        return ""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def write_csv(path: Path, rows, fields):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n", extrasaction="ignore")
        w.writeheader()
        for row in rows:
            w.writerow({k: row.get(k, "") for k in fields})

def rel(path: Path, repo: Path) -> str:
    try:
        return str(path.relative_to(repo)).replace("\\", "/")
    except Exception:
        return str(path).replace("\\", "/")

def safe_backup_path(repo: Path, backup_root: Path, original: Path) -> Path:
    try:
        rp = original.relative_to(repo)
    except Exception:
        rp = Path(original.name)
    safe_name = "__".join(rp.parts) + ".bak"
    return backup_root / safe_name

def backup_file(original: Path, repo: Path, backup_root: Path) -> Path:
    backup = safe_backup_path(repo, backup_root, original)
    backup.parent.mkdir(parents=True, exist_ok=True)
    backup.write_bytes(original.read_bytes())
    return backup

def replace_between(text: str, start_marker: str, end_marker: str, replacement: str) -> tuple[str, bool]:
    start = text.find(start_marker)
    if start < 0:
        return text, False
    end = text.find(end_marker, start + len(start_marker))
    if end < 0:
        return text, False
    return text[:start] + replacement.rstrip() + "\n\n" + text[end:], True

def patch_stage(text: str) -> tuple[str, dict]:
    info = {"PARSE_PATCHED": 0, "APPEND_PATCHED": 0}
    text, ok = replace_between(text, "def parse_dbf(path: Path) -> DbfInfo:", "def field_names(info: DbfInfo):", PATCHED_PARSE_STAGE)
    info["PARSE_PATCHED"] = 1 if ok else 0
    text, ok = replace_between(text, "def append_records_to_dbf(path: Path, rows: list[dict]) -> int:", "def main():", PATCHED_APPEND)
    info["APPEND_PATCHED"] = 1 if ok else 0
    return text, info

def patch_validate(text: str) -> tuple[str, dict]:
    info = {"PARSE_PATCHED": 0, "APPEND_PATCHED": 1}
    text, ok = replace_between(text, "def parse_dbf(path: Path) -> DbfInfo:", "def read_rows(info: DbfInfo):", PATCHED_PARSE_VALIDATE)
    info["PARSE_PATCHED"] = 1 if ok else 0
    return text, info

def patch_file(path: Path, repo: Path, backup_root: Path, role: str) -> dict:
    before = path.read_text(encoding="utf-8", errors="replace")
    before_sha = sha256_file(path)
    backup = backup_file(path, repo, backup_root)

    if role == "stage":
        after, info = patch_stage(before)
    else:
        after, info = patch_validate(before)

    # Explicitly clean any accidental literal splice tokens introduced by 6.5.3.1.1.
    after = after.replace("\\n\\ndef field_names(info: DbfInfo):", "\n\ndef field_names(info: DbfInfo):")
    after = after.replace("\\n\\ndef main():", "\n\ndef main():")
    after = after.replace('b"\\\\x00"', 'b"\\x00"')
    after = after.replace('b"\\\\x1A"', 'b"\\x1A"')

    changed = after != before
    if changed:
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_text(after, encoding="utf-8")
        tmp.replace(path)

    compile_ok = 0
    compile_error = ""
    try:
        py_compile.compile(str(path), doraise=True)
        compile_ok = 1
    except Exception as exc:
        compile_error = str(exc)

    return {
        "FILE": rel(path, repo),
        "ROLE": role,
        "BACKUP": rel(backup, repo),
        "PARSE_PATCHED": info["PARSE_PATCHED"],
        "APPEND_PATCHED": info["APPEND_PATCHED"],
        "CHANGED": 1 if changed else 0,
        "COMPILE_OK": compile_ok,
        "COMPILE_ERROR": compile_error,
        "BEFORE_SHA256": before_sha,
        "AFTER_SHA256": sha256_file(path),
    }

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--allow-tool-repair", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    reports = repo / REPORT_DIR
    reports.mkdir(parents=True, exist_ok=True)
    backup_root = repo / BACKUP_DIR / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    rows = []
    issues = []

    if not args.allow_tool_repair:
        issues.append("missing --allow-tool-repair")

    targets = [(repo / STAGE_TOOL, "stage"), (repo / VALIDATE_TOOL, "validate")]
    for path, role in targets:
        if not path.exists():
            issues.append(f"missing tool: {path}")

    if not issues:
        for path, role in targets:
            try:
                rows.append(patch_file(path, repo, backup_root, role))
            except Exception as exc:
                issues.append(f"{role}: {exc}")

    failures = len(issues)
    for row in rows:
        if row["PARSE_PATCHED"] != 1:
            failures += 1
        if row["ROLE"] == "stage" and row["APPEND_PATCHED"] != 1:
            failures += 1
        if row["COMPILE_OK"] != 1:
            failures += 1

    status = STATUS_GREEN if failures == 0 else STATUS_BLOCKED

    write_csv(reports / "message_catalog_phase22ae_6_5_3_1_2_tool_repair_rows_v1.csv",
              rows, ["FILE", "ROLE", "BACKUP", "PARSE_PATCHED", "APPEND_PATCHED", "CHANGED", "COMPILE_OK", "COMPILE_ERROR", "BEFORE_SHA256", "AFTER_SHA256"])
    write_csv(reports / "message_catalog_phase22ae_6_5_3_1_2_tool_repair_issues_v1.csv",
              [{"ISSUE": i} for i in issues], ["ISSUE"])

    boundary = [
        {"PROTECTED_SYSTEM": "TOOL_FILES", "MUTATION_ALLOWED": 1 if args.allow_tool_repair else 0, "OBSERVED_MUTATION": sum(int(r.get("CHANGED", 0)) for r in rows), "DETAIL": "Repairs 6.5.3 stage/validate tooling only."},
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No src/include mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_DBF_CATALOG", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active catalog mutation."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No HELP DATA mutation."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CMDHELPCHK mutation."},
    ]
    write_csv(reports / "message_catalog_phase22ae_6_5_3_1_2_boundary_ledger_v1.csv",
              boundary, ["PROTECTED_SYSTEM", "MUTATION_ALLOWED", "OBSERVED_MUTATION", "DETAIL"])

    write_csv(reports / "message_catalog_phase22ae_6_5_3_1_2_status_summary_v1.csv", [{
        "STATUS": status,
        "VALIDATION_ISSUES": failures,
        "TOOL_REPAIR_AUTHORIZED": 1 if args.allow_tool_repair else 0,
        "TOOL_FILES_MUTATED": sum(int(r.get("CHANGED", 0)) for r in rows),
        "TOOL_BACKUP_ROWS": len(rows),
        "TOOL_COMPILE_OK_ROWS": sum(int(r.get("COMPILE_OK", 0)) for r in rows),
        "SOURCE_FILES_MUTATED": 0,
        "ACTIVE_CATALOG_MUTATION_OBSERVED": 0,
        "HELP_DATA_MUTATION_OBSERVED": 0,
        "CMDHELPCHK_MUTATION_OBSERVED": 0,
        "NEXT_GATE": NEXT_GATE,
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }], ["STATUS", "VALIDATION_ISSUES", "TOOL_REPAIR_AUTHORIZED", "TOOL_FILES_MUTATED", "TOOL_BACKUP_ROWS",
         "TOOL_COMPILE_OK_ROWS", "SOURCE_FILES_MUTATED", "ACTIVE_CATALOG_MUTATION_OBSERVED",
         "HELP_DATA_MUTATION_OBSERVED", "CMDHELPCHK_MUTATION_OBSERVED", "NEXT_GATE", "REPORT_TIMESTAMP_UTC"])

    print(status)
    print(f"  validation issues: {failures}")
    print(f"  tool repair authorized: {1 if args.allow_tool_repair else 0}")
    print(f"  tool files mutated: {sum(int(r.get('CHANGED', 0)) for r in rows)}")
    print(f"  tool backup rows: {len(rows)}")
    print(f"  tool compile OK rows: {sum(int(r.get('COMPILE_OK', 0)) for r in rows)}")
    print("  source files mutated: 0")
    print("  active catalog mutation observed: 0")
    print("  HELP DATA mutation observed: 0")
    print("  CMDHELPCHK mutation observed: 0")
    print(f"  next gate: {NEXT_GATE}")
    print(f"  reports: {reports}")
    return 0 if status == STATUS_GREEN else 2

if __name__ == "__main__":
    raise SystemExit(main())
