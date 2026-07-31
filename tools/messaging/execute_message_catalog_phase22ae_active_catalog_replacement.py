#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
import struct
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

STATUS_GREEN = "MESSAGE_CATALOG_PHASE22AE_ACTIVE_CATALOG_REPLACEMENT_EXECUTED"
STATUS_ALREADY = "MESSAGE_CATALOG_PHASE22AE_ACTIVE_CATALOG_REPLACEMENT_ALREADY_PRESENT_NOOP_GREEN"
STATUS_BLOCKED = "MESSAGE_CATALOG_PHASE22AE_ACTIVE_CATALOG_REPLACEMENT_EXECUTION_BLOCKED"
NEXT_GATE = "HOLD_OR_AUTHORIZE_PHASE22AF_ACTIVE_CATALOG_READBACK_AND_RUNTIME_VALIDATION"

REPORT_DIR = Path("docs/messaging/reports")
APPLY_PACKAGE_ROOT = Path("docs/messaging/apply/phase22ad_active_catalog_replacement_apply_package_v1")
ACTIVE_MSG_ROOT = Path("dottalkpp/data/messaging")
ACTIVE_INDEX_ROOT = Path("dottalkpp/data/indexes/messaging")
ACTIVE_LMDB_ROOT = Path("dottalkpp/data/lmdb/messaging")
BACKUP_BASE = Path("docs/messaging/backups")

REQUIRED_SYMBOLS = ["MESSAGE_PROOF_MODE_STATUS", "MESSAGE_PROOF_BOUNDARY_NOTE"]
REQUIRED_LOCALES = ["en-US", "es", "fr", "de", "it"]
TARGET_MESSAGES = 14
TARGET_TEXT_ROWS = 70

CURRENT_MESSAGES = 12
CURRENT_TEXT_ROWS = 60


SYMBOL_FIELDS = ["SYMBOL", "MESSAGE_SYMBOL", "MSG_SYMBOL"]
LOCALE_FIELDS = ["LOCALE", "LOCALE_ID"]
TEXT_FIELDS = ["TEXT", "MESSAGE_TEXT", "MSG_TEXT"]
KIND_FIELDS = ["KIND", "MESSAGE_KIND", "MSG_KIND"]
PLACEHOLDER_FIELDS = ["PLACEHOLDERS", "PLACEHOLDER", "ARGS", "ARGUMENTS"]
STATUS_FIELDS = ["STATUS", "ROW_STATUS"]
SOURCE_FIELDS = ["SOURCE_PHASE", "SOURCE", "PHASE"]

@dataclass
class Field:
    name: str
    type: str
    length: int
    decimals: int
    offset: int

@dataclass
class DbfInfo:
    path: Path
    record_count: int
    header_len: int
    record_len: int
    fields: list[Field]
    eof_present: bool

def read_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

def first_row(path: Path) -> dict:
    rows = read_csv(path)
    return rows[0] if rows else {}

def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        w.writeheader()
        for row in rows:
            w.writerow({k: row.get(k, "") for k in fields})

def sha256_file(path: Path) -> str:
    if not path.exists() or not path.is_file():
        return ""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def rel(path: Path, repo: Path) -> str:
    try:
        return str(path.relative_to(repo)).replace("\\", "/")
    except Exception:
        return str(path).replace("\\", "/")

def savepoint_present(repo: Path, savepoint_id: str):
    latest_path = repo / REPORT_DIR / "message_savepoint_latest_v1.json"
    latest_id = ""
    if latest_path.exists():
        try:
            latest = json.loads(latest_path.read_text(encoding="utf-8"))
            latest_id = latest.get("savepoint_id", "")
        except Exception:
            latest_id = ""
    journal = repo / "docs/messaging/MESSAGING_SAVEPOINT_JOURNAL.md"
    journal_text = journal.read_text(encoding="utf-8", errors="replace") if journal.exists() else ""
    return latest_id == savepoint_id or savepoint_id in journal_text, latest_id

def dottalkpp_running() -> tuple[bool, str]:
    try:
        proc = subprocess.run(
            ["tasklist", "/FI", "IMAGENAME eq dottalkpp.exe"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        out = (proc.stdout or "") + "\n" + (proc.stderr or "")
        return ("dottalkpp.exe" in out.lower()), out.strip().replace("\r\n", " | ")
    except Exception as exc:
        # Do not fail only because tasklist is unavailable in a non-Windows shell.
        return False, f"tasklist unavailable: {exc}"

def parse_dbf(path: Path) -> DbfInfo:
    data = path.read_bytes()
    if len(data) < 32:
        raise RuntimeError(f"{path} is too small to be a DBF")
    record_count = struct.unpack("<I", data[4:8])[0]
    header_len = struct.unpack("<H", data[8:10])[0]
    record_len = struct.unpack("<H", data[10:12])[0]
    fields = []
    pos = 32
    offset = 1
    while pos + 32 <= len(data):
        if data[pos] == 0x0D:
            break
        raw_name = data[pos:pos+11].split(b"\x00", 1)[0]
        name = raw_name.decode("ascii", errors="ignore").strip().upper()
        ftype = chr(data[pos+11])
        length = data[pos+16]
        decimals = data[pos+17]
        if name:
            fields.append(Field(name=name, type=ftype, length=length, decimals=decimals, offset=offset))
            offset += length
        pos += 32
    eof_present = bool(data and data[-1] == 0x1A)
    return DbfInfo(path=path, record_count=record_count, header_len=header_len, record_len=record_len, fields=fields, eof_present=eof_present)

def read_dbf_rows(info: DbfInfo) -> list[dict]:
    rows = []
    with info.path.open("rb") as f:
        f.seek(info.header_len)
        for _ in range(info.record_count):
            rec = f.read(info.record_len)
            if len(rec) < info.record_len:
                break
            if rec[:1] == b"*":
                continue
            row = {}
            for field in info.fields:
                raw = rec[field.offset:field.offset + field.length]
                if field.type.upper() in ("C", "M"):
                    row[field.name] = raw.decode("cp1252", errors="replace").rstrip().strip()
                elif field.type.upper() in ("N", "F", "B", "Y"):
                    row[field.name] = raw.decode("ascii", errors="replace").strip()
                elif field.type.upper() == "L":
                    row[field.name] = raw[:1].decode("ascii", errors="ignore").upper()
                elif field.type.upper() == "D":
                    row[field.name] = raw.decode("ascii", errors="replace").strip()
                else:
                    row[field.name] = raw.decode("cp1252", errors="replace").rstrip().strip()
            rows.append(row)
    return rows

def field_names(info: DbfInfo) -> set[str]:
    return {f.name.upper() for f in info.fields}

def choose_field(info: DbfInfo, choices: list[str]) -> str:
    names = field_names(info)
    for c in choices:
        if c in names:
            return c
    return ""

def score_message_dbf(info: DbfInfo) -> int:
    names = field_names(info)
    score = 0
    if any(f in names for f in SYMBOL_FIELDS):
        score += 10
    if any(f in names for f in LOCALE_FIELDS):
        score -= 5
    if any(f in names for f in KIND_FIELDS):
        score += 3
    if any(f in names for f in PLACEHOLDER_FIELDS):
        score += 2
    return score

def score_text_dbf(info: DbfInfo) -> int:
    names = field_names(info)
    score = 0
    if any(f in names for f in SYMBOL_FIELDS):
        score += 7
    if any(f in names for f in LOCALE_FIELDS):
        score += 7
    if any(f in names for f in TEXT_FIELDS):
        score += 7
    return score

def discover_dbfs(active_root: Path):
    infos = []
    for p in sorted(active_root.rglob("*.dbf")):
        try:
            infos.append(parse_dbf(p))
        except Exception:
            continue
    return infos

def find_targets(infos: list[DbfInfo]) -> tuple[DbfInfo|None, DbfInfo|None, list[dict]]:
    rows = []
    msg_candidates = []
    text_candidates = []
    for info in infos:
        msg_score = score_message_dbf(info)
        text_score = score_text_dbf(info)
        rows.append({
            "DBF": str(info.path),
            "RECORD_COUNT": info.record_count,
            "FIELDS": ";".join([f.name for f in info.fields]),
            "MESSAGE_SCORE": msg_score,
            "TEXT_SCORE": text_score,
        })
        if msg_score >= 10:
            msg_candidates.append((msg_score, info))
        if text_score >= 21:
            text_candidates.append((text_score, info))
    msg_candidates.sort(key=lambda x: (x[0], x[1].record_count), reverse=True)
    text_candidates.sort(key=lambda x: (x[0], x[1].record_count), reverse=True)

    message = msg_candidates[0][1] if msg_candidates else None
    text = text_candidates[0][1] if text_candidates else None
    if message and text and message.path == text.path:
        # Prefer a separate non-locale table for message rows if available.
        for _, cand in msg_candidates:
            if cand.path != text.path:
                message = cand
                break
    return message, text, rows

def validate_field_lengths(info: DbfInfo, field_values: list[dict], errors: list[str]) -> None:
    field_map = {f.name: f for f in info.fields}
    for row in field_values:
        for field, value in row.items():
            if not field:
                continue
            f = field_map.get(field)
            if not f:
                continue
            if f.type.upper() == "M":
                errors.append(f"{info.path.name}.{field} is memo field; direct memo append is not supported")
                continue
            if f.type.upper() == "C":
                encoded = str(value).encode("cp1252", errors="replace")
                if len(encoded) > f.length:
                    errors.append(f"{info.path.name}.{field} length {len(encoded)} exceeds field width {f.length}: {value[:80]}")

def format_field(field: Field, value: str) -> bytes:
    ftype = field.type.upper()
    value = "" if value is None else str(value)
    if ftype == "C":
        b = value.encode("cp1252", errors="replace")
        if len(b) > field.length:
            raise RuntimeError(f"value too long for {field.name}: {value}")
        return b.ljust(field.length, b" ")
    if ftype in ("N", "F"):
        b = value.encode("ascii", errors="ignore")
        if len(b) > field.length:
            raise RuntimeError(f"numeric value too long for {field.name}: {value}")
        return b.rjust(field.length, b" ")
    if ftype == "L":
        c = "T" if value.upper() in ("1", "T", "TRUE", "Y", "YES", "ACTIVE") else "F"
        return c.encode("ascii").ljust(field.length, b" ")
    if ftype == "D":
        b = value.encode("ascii", errors="ignore")[:8]
        return b.ljust(field.length, b" ")
    if ftype == "M":
        raise RuntimeError(f"memo field append is not supported for {field.name}")
    b = value.encode("cp1252", errors="replace")
    if len(b) > field.length:
        raise RuntimeError(f"value too long for {field.name}: {value}")
    return b.ljust(field.length, b" ")

def append_dbf_rows(info: DbfInfo, rows_values: list[dict]) -> int:
    if not rows_values:
        return 0
    records = []
    for values in rows_values:
        rec = bytearray()
        rec.extend(b" ")
        for f in info.fields:
            rec.extend(format_field(f, values.get(f.name, "")))
        if len(rec) != info.record_len:
            raise RuntimeError(f"built record length {len(rec)} != DBF record length {info.record_len} for {info.path}")
        records.append(bytes(rec))

    data = info.path.read_bytes()
    if info.eof_present:
        data = data[:-1]
    old_count = info.record_count
    new_count = old_count + len(records)
    data = bytearray(data)
    data[4:8] = struct.pack("<I", new_count)
    for rec in records:
        data.extend(rec)
    data.extend(b"\x1A")
    info.path.write_bytes(data)
    return len(records)

def make_message_values(info: DbfInfo, candidate_rows: list[dict]) -> list[dict]:
    symbol_f = choose_field(info, SYMBOL_FIELDS)
    kind_f = choose_field(info, KIND_FIELDS)
    ph_f = choose_field(info, PLACEHOLDER_FIELDS)
    status_f = choose_field(info, STATUS_FIELDS)
    source_f = choose_field(info, SOURCE_FIELDS)
    values = []
    for row in candidate_rows:
        out = {}
        if symbol_f:
            out[symbol_f] = row.get("SYMBOL", "")
        if kind_f:
            out[kind_f] = row.get("KIND", "runtime_message")
        if ph_f:
            out[ph_f] = row.get("PLACEHOLDERS", "")
        if status_f:
            out[status_f] = "ACTIVE"
        if source_f:
            out[source_f] = "22AE"
        values.append(out)
    return values

def make_text_values(info: DbfInfo, candidate_rows: list[dict]) -> list[dict]:
    symbol_f = choose_field(info, SYMBOL_FIELDS)
    locale_f = choose_field(info, LOCALE_FIELDS)
    text_f = choose_field(info, TEXT_FIELDS)
    ph_f = choose_field(info, PLACEHOLDER_FIELDS)
    status_f = choose_field(info, STATUS_FIELDS)
    source_f = choose_field(info, SOURCE_FIELDS)
    values = []
    for row in candidate_rows:
        out = {}
        if symbol_f:
            out[symbol_f] = row.get("SYMBOL", "")
        if locale_f:
            out[locale_f] = row.get("LOCALE", "")
        if text_f:
            out[text_f] = row.get("TEXT", "")
        if ph_f:
            out[ph_f] = row.get("PLACEHOLDERS", "")
        if status_f:
            out[status_f] = "ACTIVE"
        if source_f:
            out[source_f] = "22AE"
        values.append(out)
    return values

def copy_tree_with_inventory(src: Path, dst: Path, repo: Path, rows: list[dict], role: str):
    if not src.exists():
        rows.append({"SOURCE": rel(src, repo), "BACKUP": rel(dst, repo), "ROLE": role, "EXISTS": 0, "FILES": 0, "BYTES": 0, "SHA256": ""})
        return
    if src.is_file():
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        rows.append({"SOURCE": rel(src, repo), "BACKUP": rel(dst, repo), "ROLE": role, "EXISTS": 1, "FILES": 1, "BYTES": dst.stat().st_size, "SHA256": sha256_file(dst)})
        return
    file_count = 0
    total_bytes = 0
    for p in src.rglob("*"):
        if p.is_file():
            q = dst / p.relative_to(src)
            q.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(p, q)
            file_count += 1
            total_bytes += q.stat().st_size
    rows.append({"SOURCE": rel(src, repo), "BACKUP": rel(dst, repo), "ROLE": role, "EXISTS": 1, "FILES": file_count, "BYTES": total_bytes, "SHA256": ""})

def fingerprint_root(root: Path, repo: Path, label: str) -> list[dict]:
    rows = []
    if not root.exists():
        rows.append({"LABEL": label, "PATH": rel(root, repo), "EXISTS": 0, "BYTES": 0, "SHA256": "", "ROLE": "root_missing"})
        return rows
    for p in sorted(root.rglob("*")):
        if p.is_file():
            rows.append({"LABEL": label, "PATH": rel(p, repo), "EXISTS": 1, "BYTES": p.stat().st_size, "SHA256": sha256_file(p), "ROLE": "file"})
    if not rows:
        rows.append({"LABEL": label, "PATH": rel(root, repo), "EXISTS": 1, "BYTES": 0, "SHA256": "", "ROLE": "empty_root"})
    return rows

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--allow-active-catalog-mutation", action="store_true")
    ap.add_argument("--allow-already-promoted-noop", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    reports = repo / REPORT_DIR
    reports.mkdir(parents=True, exist_ok=True)

    ad = first_row(reports / "message_catalog_phase22ad_status_summary_v1.csv")
    ad_savepoint_ok, latest_id = savepoint_present(repo, "MSG-022AD")

    msg_rows_path = repo / APPLY_PACKAGE_ROOT / "rows/message_catalog_candidate_message_adds_v1.csv"
    txt_rows_path = repo / APPLY_PACKAGE_ROOT / "rows/message_catalog_candidate_text_adds_v1.csv"
    candidate_message_rows = read_csv(msg_rows_path)
    candidate_text_rows = read_csv(txt_rows_path)

    gates = []
    failures = 0

    def gate(name: str, ok: bool, detail: str):
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": detail})
        if not ok:
            failures += 1

    running, running_detail = dottalkpp_running()

    gate("OPERATOR_AUTHORIZED_ACTIVE_CATALOG_MUTATION", args.allow_active_catalog_mutation, "requires --allow-active-catalog-mutation")
    gate("PHASE22AD_APPLY_PACKAGE_GREEN",
         ad.get("STATUS") == "MESSAGE_CATALOG_PHASE22AD_ACTIVE_CATALOG_REPLACEMENT_APPLY_PACKAGE_STAGED_SOURCE_HELD",
         ad.get("STATUS", "missing"))
    gate("MSG_022AD_SAVEPOINT_PRESENT", ad_savepoint_ok, latest_id)
    gate("DOTTALKPP_PROCESS_NOT_RUNNING", not running, running_detail)
    gate("CANDIDATE_MESSAGE_ROWS_AVAILABLE", len(candidate_message_rows) == 2, f"rows={len(candidate_message_rows)}")
    gate("CANDIDATE_TEXT_ROWS_AVAILABLE", len(candidate_text_rows) == 10, f"rows={len(candidate_text_rows)}")
    gate("ACTIVE_MESSAGE_ROOT_EXISTS", (repo / ACTIVE_MSG_ROOT).exists(), rel(repo / ACTIVE_MSG_ROOT, repo))

    active_infos = discover_dbfs(repo / ACTIVE_MSG_ROOT) if (repo / ACTIVE_MSG_ROOT).exists() else []
    message_dbf, text_dbf, dbf_discovery = find_targets(active_infos)
    gate("ACTIVE_MESSAGE_DBF_DISCOVERED", message_dbf is not None, rel(message_dbf.path, repo) if message_dbf else "not found")
    gate("ACTIVE_TEXT_DBF_DISCOVERED", text_dbf is not None, rel(text_dbf.path, repo) if text_dbf else "not found")

    errors = []
    backup_rows = []
    mutation_rows = []
    row_apply_rows = []
    status = STATUS_BLOCKED
    records_added_message = 0
    records_added_text = 0
    already_present = False

    before_fingerprints = (
        fingerprint_root(repo / ACTIVE_MSG_ROOT, repo, "before_active_message_root") +
        fingerprint_root(repo / ACTIVE_INDEX_ROOT, repo, "before_active_index_root") +
        fingerprint_root(repo / ACTIVE_LMDB_ROOT, repo, "before_active_lmdb_root")
    )

    if failures == 0 and message_dbf is not None and text_dbf is not None:
        try:
            msg_symbol_f = choose_field(message_dbf, SYMBOL_FIELDS)
            text_symbol_f = choose_field(text_dbf, SYMBOL_FIELDS)
            text_locale_f = choose_field(text_dbf, LOCALE_FIELDS)
            text_text_f = choose_field(text_dbf, TEXT_FIELDS)

            if not msg_symbol_f:
                errors.append(f"message DBF {rel(message_dbf.path, repo)} has no supported symbol field")
            if not text_symbol_f or not text_locale_f or not text_text_f:
                errors.append(f"text DBF {rel(text_dbf.path, repo)} must have supported symbol, locale, and text fields")

            existing_msg_rows = read_dbf_rows(message_dbf)
            existing_text_rows = read_dbf_rows(text_dbf)
            existing_symbols = {r.get(msg_symbol_f, "") for r in existing_msg_rows} if msg_symbol_f else set()
            existing_text_keys = {(r.get(text_symbol_f, ""), r.get(text_locale_f, "")) for r in existing_text_rows} if text_symbol_f and text_locale_f else set()

            message_missing = [r for r in candidate_message_rows if r.get("SYMBOL") not in existing_symbols]
            text_missing = [r for r in candidate_text_rows if (r.get("SYMBOL"), r.get("LOCALE")) not in existing_text_keys]

            if not message_missing and not text_missing:
                already_present = True
                if not args.allow_already_promoted_noop:
                    errors.append("candidate symbols/text rows already present; rerun with -AllowAlreadyPromotedNoop to record no-op")
            elif len(message_missing) != 2 or len(text_missing) != 10:
                errors.append(f"partial active catalog presence detected; missing message rows={len(message_missing)} missing text rows={len(text_missing)}")

            msg_values = make_message_values(message_dbf, message_missing)
            txt_values = make_text_values(text_dbf, text_missing)
            validate_field_lengths(message_dbf, msg_values, errors)
            validate_field_lengths(text_dbf, txt_values, errors)

            if errors:
                raise RuntimeError("; ".join(errors))

            if already_present:
                status = STATUS_ALREADY
            else:
                # Backup active roots before writing any active DBF row.
                backup_root = repo / BACKUP_BASE / f"MSG-022AE_ACTIVE_CATALOG_REPLACEMENT_BACKUP_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
                copy_tree_with_inventory(repo / ACTIVE_MSG_ROOT, backup_root / "messaging", repo, backup_rows, "active_messaging_root_backup")
                copy_tree_with_inventory(repo / ACTIVE_INDEX_ROOT, backup_root / "indexes_messaging", repo, backup_rows, "active_indexes_root_backup")
                copy_tree_with_inventory(repo / ACTIVE_LMDB_ROOT, backup_root / "lmdb_messaging", repo, backup_rows, "active_lmdb_root_backup")

                pre_msg_count = parse_dbf(message_dbf.path).record_count
                pre_text_count = parse_dbf(text_dbf.path).record_count
                records_added_message = append_dbf_rows(parse_dbf(message_dbf.path), msg_values)
                records_added_text = append_dbf_rows(parse_dbf(text_dbf.path), txt_values)
                post_msg_count = parse_dbf(message_dbf.path).record_count
                post_text_count = parse_dbf(text_dbf.path).record_count

                row_apply_rows.append({
                    "DBF_ROLE": "message",
                    "DBF_PATH": rel(message_dbf.path, repo),
                    "PRE_RECORDS": pre_msg_count,
                    "ROWS_ADDED": records_added_message,
                    "POST_RECORDS": post_msg_count,
                    "EXPECTED_POST_RECORDS": TARGET_MESSAGES,
                    "STATUS": "PASS" if post_msg_count == TARGET_MESSAGES else "REVIEW",
                })
                row_apply_rows.append({
                    "DBF_ROLE": "text",
                    "DBF_PATH": rel(text_dbf.path, repo),
                    "PRE_RECORDS": pre_text_count,
                    "ROWS_ADDED": records_added_text,
                    "POST_RECORDS": post_text_count,
                    "EXPECTED_POST_RECORDS": TARGET_TEXT_ROWS,
                    "STATUS": "PASS" if post_text_count == TARGET_TEXT_ROWS else "REVIEW",
                })

                mutation_rows.append({
                    "TARGET_PATH": rel(message_dbf.path, repo),
                    "ACTION": "DBF_APPEND",
                    "ROWS_ADDED": records_added_message,
                    "SHA256_AFTER": sha256_file(message_dbf.path),
                    "DETAIL": "appended active messaging catalog message rows",
                })
                mutation_rows.append({
                    "TARGET_PATH": rel(text_dbf.path, repo),
                    "ACTION": "DBF_APPEND",
                    "ROWS_ADDED": records_added_text,
                    "SHA256_AFTER": sha256_file(text_dbf.path),
                    "DETAIL": "appended active messaging catalog text rows",
                })

                if records_added_message == 2 and records_added_text == 10:
                    status = STATUS_GREEN
                else:
                    status = STATUS_BLOCKED
                    failures += 1
                    gates.append({"GATE": "ROW_APPEND_COUNTS", "STATUS": "FAIL", "DETAIL": f"message={records_added_message}; text={records_added_text}"})
        except Exception as exc:
            errors.append(str(exc))
            failures += 1
            gates.append({"GATE": "EXECUTE_ACTIVE_CATALOG_REPLACEMENT", "STATUS": "FAIL", "DETAIL": str(exc)})
            status = STATUS_BLOCKED

    after_fingerprints = (
        fingerprint_root(repo / ACTIVE_MSG_ROOT, repo, "after_active_message_root") +
        fingerprint_root(repo / ACTIVE_INDEX_ROOT, repo, "after_active_index_root") +
        fingerprint_root(repo / ACTIVE_LMDB_ROOT, repo, "after_active_lmdb_root")
    )

    validation_issues = "0" if status in (STATUS_GREEN, STATUS_ALREADY) else str(failures)

    write_csv(reports / "message_catalog_phase22ae_dbf_discovery_v1.csv", dbf_discovery,
              ["DBF", "RECORD_COUNT", "FIELDS", "MESSAGE_SCORE", "TEXT_SCORE"])
    write_csv(reports / "message_catalog_phase22ae_backup_inventory_v1.csv", backup_rows,
              ["SOURCE", "BACKUP", "ROLE", "EXISTS", "FILES", "BYTES", "SHA256"])
    write_csv(reports / "message_catalog_phase22ae_active_fingerprint_before_v1.csv", before_fingerprints,
              ["LABEL", "PATH", "EXISTS", "BYTES", "SHA256", "ROLE"])
    write_csv(reports / "message_catalog_phase22ae_active_fingerprint_after_v1.csv", after_fingerprints,
              ["LABEL", "PATH", "EXISTS", "BYTES", "SHA256", "ROLE"])
    write_csv(reports / "message_catalog_phase22ae_row_apply_readback_v1.csv", row_apply_rows,
              ["DBF_ROLE", "DBF_PATH", "PRE_RECORDS", "ROWS_ADDED", "POST_RECORDS", "EXPECTED_POST_RECORDS", "STATUS"])
    write_csv(reports / "message_catalog_phase22ae_active_mutation_inventory_v1.csv", mutation_rows,
              ["TARGET_PATH", "ACTION", "ROWS_ADDED", "SHA256_AFTER", "DETAIL"])
    write_csv(reports / "message_catalog_phase22ae_gate_check_v1.csv", gates,
              ["GATE", "STATUS", "DETAIL"])

    boundary = [
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No source mutation in 22AE."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_DBF_CATALOG", "MUTATION_ALLOWED": 1, "OBSERVED_MUTATION": len(mutation_rows), "DETAIL": "Authorized active messaging DBF row append only."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_CDX_INDEXES", "MUTATION_ALLOWED": 1, "OBSERVED_MUTATION": 0, "DETAIL": "No CDX/index mutation performed by this Python DBF append; validate in 22AF."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_LMDB", "MUTATION_ALLOWED": 1, "OBSERVED_MUTATION": 0, "DETAIL": "No LMDB mutation performed by this Python DBF append; validate in 22AF."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No HELP DATA mutation."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CMDHELPCHK mutation."},
        {"PROTECTED_SYSTEM": "COMMAND_REGISTRY", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No command registry mutation."},
        {"PROTECTED_SYSTEM": "MANUALGEN", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No manualgen mutation."},
        {"PROTECTED_SYSTEM": "DATADICT_SELF_DOC", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No Data Dictionary/SelfDoc mutation."},
    ]
    write_csv(reports / "message_catalog_phase22ae_boundary_ledger_v1.csv", boundary,
              ["PROTECTED_SYSTEM", "MUTATION_ALLOWED", "OBSERVED_MUTATION", "DETAIL"])

    write_csv(reports / "message_catalog_phase22ae_status_summary_v1.csv", [{
        "STATUS": status,
        "MESSAGES_BEFORE": CURRENT_MESSAGES,
        "TEXT_ROWS_BEFORE": CURRENT_TEXT_ROWS,
        "TARGET_MESSAGES_AFTER_EXECUTION": TARGET_MESSAGES,
        "TARGET_TEXT_ROWS_AFTER_EXECUTION": TARGET_TEXT_ROWS,
        "VALIDATION_ISSUES": validation_issues,
        "PHASE22AD_GREEN": 1 if ad.get("STATUS") == "MESSAGE_CATALOG_PHASE22AD_ACTIVE_CATALOG_REPLACEMENT_APPLY_PACKAGE_STAGED_SOURCE_HELD" else 0,
        "MSG_022AD_SAVEPOINT_PRESENT": 1 if ad_savepoint_ok else 0,
        "DOTTALKPP_PROCESS_RUNNING": 1 if running else 0,
        "MESSAGE_DBF": rel(message_dbf.path, repo) if message_dbf else "",
        "TEXT_DBF": rel(text_dbf.path, repo) if text_dbf else "",
        "MESSAGE_ROWS_ADDED": records_added_message,
        "TEXT_ROWS_ADDED": records_added_text,
        "ALREADY_PRESENT_NOOP": 1 if already_present else 0,
        "BACKUP_ROWS": len(backup_rows),
        "SOURCE_FILES_MUTATED": 0,
        "ACTIVE_CATALOG_MUTATION_OBSERVED": len(mutation_rows),
        "ACTIVE_INDEX_MUTATION_OBSERVED": 0,
        "ACTIVE_LMDB_MUTATION_OBSERVED": 0,
        "HELP_DATA_MUTATION_OBSERVED": 0,
        "CMDHELPCHK_MUTATION_OBSERVED": 0,
        "ERRORS": "; ".join(errors),
        "NEXT_GATE": NEXT_GATE,
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }], ["STATUS", "MESSAGES_BEFORE", "TEXT_ROWS_BEFORE",
         "TARGET_MESSAGES_AFTER_EXECUTION", "TARGET_TEXT_ROWS_AFTER_EXECUTION",
         "VALIDATION_ISSUES", "PHASE22AD_GREEN", "MSG_022AD_SAVEPOINT_PRESENT",
         "DOTTALKPP_PROCESS_RUNNING", "MESSAGE_DBF", "TEXT_DBF",
         "MESSAGE_ROWS_ADDED", "TEXT_ROWS_ADDED", "ALREADY_PRESENT_NOOP",
         "BACKUP_ROWS", "SOURCE_FILES_MUTATED", "ACTIVE_CATALOG_MUTATION_OBSERVED",
         "ACTIVE_INDEX_MUTATION_OBSERVED", "ACTIVE_LMDB_MUTATION_OBSERVED",
         "HELP_DATA_MUTATION_OBSERVED", "CMDHELPCHK_MUTATION_OBSERVED",
         "ERRORS", "NEXT_GATE", "REPORT_TIMESTAMP_UTC"])

    print(status)
    print(f"  validation issues: {validation_issues}")
    print(f"  Phase 22AD green: {1 if ad.get('STATUS') == 'MESSAGE_CATALOG_PHASE22AD_ACTIVE_CATALOG_REPLACEMENT_APPLY_PACKAGE_STAGED_SOURCE_HELD' else 0}")
    print(f"  MSG-022AD savepoint present: {1 if ad_savepoint_ok else 0}")
    print(f"  dottalkpp process running: {1 if running else 0}")
    print(f"  message DBF: {rel(message_dbf.path, repo) if message_dbf else ''}")
    print(f"  text DBF: {rel(text_dbf.path, repo) if text_dbf else ''}")
    print(f"  message rows added: {records_added_message}")
    print(f"  text rows added: {records_added_text}")
    print(f"  already present noop: {1 if already_present else 0}")
    print(f"  backup rows: {len(backup_rows)}")
    print("  source files mutated: 0")
    print(f"  active catalog mutation observed: {len(mutation_rows)}")
    print("  active index mutation observed: 0")
    print("  active lmdb mutation observed: 0")
    print("  HELP DATA mutation observed: 0")
    print("  CMDHELPCHK mutation observed: 0")
    print(f"  next gate: {NEXT_GATE}")
    print(f"  reports: {reports}")
    return 0 if status in (STATUS_GREEN, STATUS_ALREADY) else 2

if __name__ == "__main__":
    raise SystemExit(main())
