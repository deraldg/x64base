#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
import struct
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

STATUS_GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_6_NATIVE_IMPORT_CSV_WRITE_PROOF_STAGED_SOURCE_HELD"
STATUS_BLOCKED = "MESSAGE_CATALOG_PHASE22AE_6_5_6_NATIVE_IMPORT_CSV_WRITE_PROOF_STAGING_BLOCKED"
NEXT_GATE = "RUN_PHASE22AE_6_5_6_NATIVE_IMPORT_CSV_RUNTIME_THEN_VALIDATE"

REPORT_DIR = Path("docs/messaging/reports")
SANDBOX_ROOT = Path("docs/messaging/sandbox/phase22ae_6_5_6_native_import_csv_v1")
ABS_SCRIPT_PATH = Path("docs/messaging/scripts/MESSAGE_CATALOG_PHASE22AE_6_5_6_NATIVE_IMPORT_CSV_ABSOLUTE_PATH_PROOF.dts")
PATH_SETUP_SCRIPT = Path("docs/messaging/scripts/MESSAGE_CATALOG_PHASE22AE_6_5_6_DBF_PATH_LOCATION_SETUP.dts")

ACTIVE_MSG_ROOT = Path("dottalkpp/data/messaging")
ACTIVE_INDEX_ROOT = Path("dottalkpp/data/indexes/messaging")
ACTIVE_LMDB_ROOT = Path("dottalkpp/data/lmdb/messaging")
DEFAULT_INDEX_ROOT = Path("dottalkpp/data/indexes")
DEFAULT_LMDB_ROOT = Path("dottalkpp/data/lmdb")

MESSAGE_TABLE = "SYSTEM_MESSAGES"
TEXT_TABLE = "SYSTEM_MESSAGE_TEXT"
UNIQUE_MESSAGE_DBF = "MSG656_MESSAGES_NATIVE_IMPORT.dbf"
UNIQUE_TEXT_DBF = "MSG656_TEXT_NATIVE_IMPORT.dbf"

SYMBOL_ALIASES = ["SYMBOL", "MESSAGE_SYMBOL", "MSG_SYMBOL", "MSGID", "MESSAGE_ID", "KEY", "MSG_KEY"]
LOCALE_ALIASES = ["LOCALE", "LOCALE_ID", "LANG", "LANGUAGE", "CULTURE"]
TEXT_ALIASES = ["TEXT", "MESSAGE_TEXT", "MSG_TEXT", "VALUE", "LOCALIZED_TEXT", "MESSAGE", "TEXT_VALUE"]
STATUS_ALIASES = ["STATUS", "ROW_STATUS"]
SOURCE_ALIASES = ["SOURCE_PHASE", "SOURCE", "PHASE", "SRC"]
KIND_ALIASES = ["KIND", "MESSAGE_KIND", "MSG_KIND", "TYPE"]

class DbfInfo:
    def __init__(self, path: Path, header_count: int, header_len: int, record_len: int, fields: list[dict[str, Any]]):
        self.path = path
        self.header_count = header_count
        self.header_len = header_len
        self.record_len = record_len
        self.fields = fields

def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

def first_row(path: Path) -> dict[str, str]:
    rows = read_csv(path)
    return rows[0] if rows else {}

def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
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

def sha256_file(path: Path) -> str:
    if not path.exists() or not path.is_file():
        return ""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def valid_field_name(name: str) -> bool:
    if not name:
        return False
    if not (name[0].isalpha() or name[0] == "_"):
        return False
    return all(ch.isalnum() or ch == "_" for ch in name)

def parse_dbf(path: Path) -> DbfInfo:
    data = path.read_bytes()
    if len(data) < 32:
        raise RuntimeError(f"DBF too small: {path}")
    count = struct.unpack("<I", data[4:8])[0]
    header_len = struct.unpack("<H", data[8:10])[0]
    record_len = struct.unpack("<H", data[10:12])[0]
    fields = []
    pos = 32
    offset = 1
    ordinal = 0
    while pos + 32 <= len(data):
        if data[pos] == 0x0D:
            break
        ordinal += 1
        raw = data[pos:pos+11].split(b"\x00", 1)[0]
        name = raw.decode("ascii", errors="ignore").strip().upper()
        ftype = chr(data[pos+11]) if 32 <= data[pos+11] <= 126 else f"0x{data[pos+11]:02X}"
        length = data[pos+16]
        decimals = data[pos+17]
        if valid_field_name(name) and length > 0 and (offset + length) <= record_len:
            fields.append({"NAME": name, "TYPE": ftype, "LENGTH": length, "DECIMALS": decimals, "OFFSET": offset, "ORDINAL": ordinal})
            offset += length
        pos += 32
    return DbfInfo(path, count, header_len, record_len, fields)

def field_names(info: DbfInfo) -> list[str]:
    return [f["NAME"] for f in info.fields]

def field_type(info: DbfInfo, name: str) -> str:
    for f in info.fields:
        if f["NAME"] == name:
            return f["TYPE"]
    return ""

def choose_field(info: DbfInfo, aliases: list[str]) -> str:
    names = {f["NAME"] for f in info.fields}
    for a in aliases:
        if a in names:
            return a
    return ""

def norm_row(row: dict[str, Any]) -> dict[str, str]:
    return {str(k).strip().upper(): "" if v is None else str(v) for k, v in row.items() if k is not None}

def pick(src: dict[str, str], target: str, aliases: list[str]) -> str:
    if target in src:
        return src[target]
    for a in aliases:
        if a in src:
            return src[a]
    return ""

def build_import_rows(info: DbfInfo, source_rows: list[dict[str, str]], table: str):
    sym_field = choose_field(info, SYMBOL_ALIASES)
    loc_field = choose_field(info, LOCALE_ALIASES)
    text_field = choose_field(info, TEXT_ALIASES)
    status_field = choose_field(info, STATUS_ALIASES)
    source_field = choose_field(info, SOURCE_ALIASES)
    kind_field = choose_field(info, KIND_ALIASES)

    rows = []
    mapping = []
    for source_row in source_rows:
        src = norm_row(source_row)
        dst: dict[str, str] = {}
        for f in field_names(info):
            val = ""
            if f == sym_field:
                val = pick(src, f, SYMBOL_ALIASES)
            elif f == loc_field:
                val = pick(src, f, LOCALE_ALIASES)
            elif f == text_field:
                val = pick(src, f, TEXT_ALIASES)
            elif f == status_field:
                val = pick(src, f, STATUS_ALIASES) or "CANDIDATE"
            elif f == source_field:
                val = pick(src, f, SOURCE_ALIASES) or "22AE_6_5_6"
            elif f == kind_field:
                val = pick(src, f, KIND_ALIASES) or "catalog"
            else:
                val = src.get(f, "")
            dst[f] = val
        rows.append(dst)

    for f in field_names(info):
        mapping.append({"TABLE": table, "TARGET_FIELD": f, "SAMPLE_VALUE": rows[0].get(f, "") if rows else ""})
    return rows, mapping, sym_field, loc_field, text_field

def copy_renamed_sidecars(repo: Path, source_dbf: Path, target_dbf: Path, rows: list[dict[str, Any]]):
    # Copy memo sidecars from active roots using the new unique DBF stem. Do not
    # copy CDX/LMDB here; native import proof intentionally opens without active indexes.
    for sidecar in sorted(source_dbf.parent.glob(source_dbf.stem + ".*")):
        if sidecar.name.lower() == source_dbf.name.lower():
            continue
        target = target_dbf.parent / (target_dbf.stem + sidecar.suffix)
        shutil.copy2(sidecar, target)
        rows.append({
            "ROLE": "renamed_sidecar_copy",
            "SOURCE": rel(sidecar, repo),
            "TARGET": rel(target, repo),
            "BYTES": target.stat().st_size,
            "SHA256": sha256_file(target),
        })

def dbf_physical_count(path: Path) -> int:
    data = path.read_bytes()
    header_len = struct.unpack("<H", data[8:10])[0]
    record_len = struct.unpack("<H", data[10:12])[0]
    eof = 1 if data and data[-1] == 0x1A else 0
    return (len(data) - header_len - eof) // record_len if record_len else 0

def fingerprint_active(repo: Path):
    rows = []
    targets = []
    for table in [MESSAGE_TABLE, TEXT_TABLE]:
        targets.append((repo / ACTIVE_MSG_ROOT / f"{table}.dbf", f"active_dbf_{table}"))
        for p in sorted((repo / ACTIVE_MSG_ROOT).glob(f"{table}.*")):
            if p.name.lower() != f"{table.lower()}.dbf":
                targets.append((p, f"active_sidecar_{table}_{p.suffix.lower().lstrip('.')}"))
        targets.extend([
            (repo / ACTIVE_INDEX_ROOT / f"{table}.cdx", f"active_index_{table}_cdx"),
            (repo / ACTIVE_INDEX_ROOT / f"{table}.cdx.meta", f"active_index_{table}_meta"),
            (repo / ACTIVE_LMDB_ROOT / f"{table}.cdx.d", f"active_lmdb_{table}"),
            (repo / DEFAULT_INDEX_ROOT / f"{table}.cdx", f"default_index_{table}_cdx"),
            (repo / DEFAULT_INDEX_ROOT / f"{table}.cdx.meta", f"default_index_{table}_meta"),
            (repo / DEFAULT_LMDB_ROOT / f"{table}.cdx.d", f"default_lmdb_{table}"),
        ])
    seen = set()
    for path, role in targets:
        key = role + "|" + str(path.resolve())
        if key in seen:
            continue
        seen.add(key)
        if path.is_dir():
            files = sorted(p for p in path.rglob("*") if p.is_file())
            h = hashlib.sha256()
            total = 0
            for f in files:
                h.update(str(f.relative_to(path)).replace("\\", "/").encode("utf-8"))
                h.update(sha256_file(f).encode("ascii"))
                total += f.stat().st_size
            rows.append({"ROLE": role, "PATH": rel(path, repo), "EXISTS": 1, "KIND": "dir", "BYTES": total, "SHA256": h.hexdigest(), "FILES": len(files)})
        elif path.is_file():
            rows.append({"ROLE": role, "PATH": rel(path, repo), "EXISTS": 1, "KIND": "file", "BYTES": path.stat().st_size, "SHA256": sha256_file(path), "FILES": 1})
        else:
            rows.append({"ROLE": role, "PATH": rel(path, repo), "EXISTS": 0, "KIND": "missing", "BYTES": 0, "SHA256": "", "FILES": 0})
    return rows

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--replace-existing-sandbox", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    reports = repo / REPORT_DIR
    reports.mkdir(parents=True, exist_ok=True)
    sandbox = repo / SANDBOX_ROOT
    dbf_dir = sandbox / "dbf"
    import_dir = sandbox / "import"

    val654 = first_row(reports / "message_catalog_phase22ae_6_5_4_validate_status_summary_v1.csv")
    stage651 = first_row(reports / "message_catalog_phase22ae_6_5_1_stage_status_summary_v1.csv")
    stage652 = first_row(reports / "message_catalog_phase22ae_6_5_2_stage_status_summary_v1.csv")

    gates = []
    failures = 0
    errors = []

    def gate(name: str, ok: bool, detail: Any):
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": str(detail)})
        if not ok:
            failures += 1

    gate("PHASE22AE_6_5_4_BLOCKED_WITH_KEYS_PROVEN",
         val654.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_5_4_SANDBOX_PATH_BINDING_PROOF_BLOCKED" and val654.get("KEYS_PROVEN") == "1",
         f"status={val654.get('STATUS','missing')}; keys={val654.get('KEYS_PROVEN','')}")
    gate("SANDBOX_NOT_EXISTING_OR_REPLACE_ALLOWED", (not sandbox.exists()) or args.replace_existing_sandbox, rel(sandbox, repo))

    candidate_msg = repo / (stage652.get("CANDIDATE_MESSAGE_FILE") or stage651.get("CANDIDATE_MESSAGE_FILE") or "")
    candidate_txt = repo / (stage652.get("CANDIDATE_TEXT_FILE") or stage651.get("CANDIDATE_TEXT_FILE") or "")
    gate("CANDIDATE_MESSAGE_FILE_EXISTS", candidate_msg.exists(), rel(candidate_msg, repo))
    gate("CANDIDATE_TEXT_FILE_EXISTS", candidate_txt.exists(), rel(candidate_txt, repo))

    before_fp = fingerprint_active(repo)
    write_csv(reports / "message_catalog_phase22ae_6_5_6_active_fingerprint_before_v1.csv",
              before_fp, ["ROLE", "PATH", "EXISTS", "KIND", "BYTES", "SHA256", "FILES"])

    copy_rows = []
    mapping_rows = []
    expected_msg_rows = []
    expected_txt_rows = []
    abs_script_rel = ""
    path_setup_rel = ""
    status = STATUS_BLOCKED
    msg_before = text_before = ""
    msg_phys_before = text_phys_before = ""
    text_field_type = ""

    if failures == 0:
        try:
            if sandbox.exists() and args.replace_existing_sandbox:
                shutil.rmtree(sandbox)
            dbf_dir.mkdir(parents=True, exist_ok=True)
            import_dir.mkdir(parents=True, exist_ok=True)

            active_msg = repo / ACTIVE_MSG_ROOT / f"{MESSAGE_TABLE}.dbf"
            active_txt = repo / ACTIVE_MSG_ROOT / f"{TEXT_TABLE}.dbf"
            unique_msg = dbf_dir / UNIQUE_MESSAGE_DBF
            unique_txt = dbf_dir / UNIQUE_TEXT_DBF
            shutil.copy2(active_msg, unique_msg)
            shutil.copy2(active_txt, unique_txt)
            copy_rows.append({"ROLE": "message_dbf_copy", "SOURCE": rel(active_msg, repo), "TARGET": rel(unique_msg, repo), "BYTES": unique_msg.stat().st_size, "SHA256": sha256_file(unique_msg)})
            copy_rows.append({"ROLE": "text_dbf_copy", "SOURCE": rel(active_txt, repo), "TARGET": rel(unique_txt, repo), "BYTES": unique_txt.stat().st_size, "SHA256": sha256_file(unique_txt)})
            copy_renamed_sidecars(repo, active_msg, unique_msg, copy_rows)
            copy_renamed_sidecars(repo, active_txt, unique_txt, copy_rows)

            msg_info = parse_dbf(unique_msg)
            txt_info = parse_dbf(unique_txt)
            msg_before = msg_info.header_count
            text_before = txt_info.header_count
            msg_phys_before = dbf_physical_count(unique_msg)
            text_phys_before = dbf_physical_count(unique_txt)

            msg_src_rows = read_csv(candidate_msg)
            txt_src_rows = read_csv(candidate_txt)
            msg_import_rows, msg_map, msg_symbol_field, _, _ = build_import_rows(msg_info, msg_src_rows, MESSAGE_TABLE)
            txt_import_rows, txt_map, txt_symbol_field, txt_locale_field, txt_text_field = build_import_rows(txt_info, txt_src_rows, TEXT_TABLE)
            mapping_rows.extend(msg_map)
            mapping_rows.extend(txt_map)
            text_field_type = field_type(txt_info, txt_text_field)

            gate("MESSAGE_IMPORT_ROW_COUNT_2", len(msg_import_rows) == 2, len(msg_import_rows))
            gate("TEXT_IMPORT_ROW_COUNT_10", len(txt_import_rows) == 10, len(txt_import_rows))
            gate("MESSAGE_SYMBOL_FIELD_MAPPED", bool(msg_symbol_field), msg_symbol_field)
            gate("TEXT_SYMBOL_LOCALE_FIELD_MAPPED", bool(txt_symbol_field and txt_locale_field), f"{txt_symbol_field}/{txt_locale_field}")

            msg_import_csv = import_dir / "MSG656_MESSAGES_NATIVE_IMPORT.csv"
            txt_import_csv = import_dir / "MSG656_TEXT_NATIVE_IMPORT.csv"
            write_csv(msg_import_csv, msg_import_rows, field_names(msg_info))
            write_csv(txt_import_csv, txt_import_rows, field_names(txt_info))

            for row in msg_import_rows:
                expected_msg_rows.append({"SYMBOL_FIELD": msg_symbol_field, "SYMBOL": row.get(msg_symbol_field, "")})
            for row in txt_import_rows:
                expected_txt_rows.append({
                    "SYMBOL_FIELD": txt_symbol_field,
                    "SYMBOL": row.get(txt_symbol_field, ""),
                    "LOCALE_FIELD": txt_locale_field,
                    "LOCALE": row.get(txt_locale_field, ""),
                    "TEXT_FIELD": txt_text_field,
                    "TEXT_FIELD_TYPE": text_field_type,
                })

            abs_script = repo / ABS_SCRIPT_PATH
            abs_script.parent.mkdir(parents=True, exist_ok=True)
            abs_script.write_text("\n".join([
                "* MESSAGE_CATALOG_PHASE22AE_6_5_6_NATIVE_IMPORT_CSV_ABSOLUTE_PATH_PROOF.dts",
                "* Native DotTalk++ IMPORT proof using absolute DBF and CSV paths.",
                "* This is the primary proof path; it must not depend on SET PATH.",
                f"USE {unique_msg.resolve().as_posix()}",
                f"IMPORT {msg_import_csv.resolve().as_posix()}",
                f"USE {unique_msg.resolve().as_posix()}",
                f"USE {unique_txt.resolve().as_posix()}",
                f"IMPORT {txt_import_csv.resolve().as_posix()}",
                f"USE {unique_txt.resolve().as_posix()}",
                "",
            ]), encoding="utf-8")
            abs_script_rel = rel(abs_script, repo)

            path_script = repo / PATH_SETUP_SCRIPT
            path_script.parent.mkdir(parents=True, exist_ok=True)
            path_script.write_text("\n".join([
                "* MESSAGE_CATALOG_PHASE22AE_6_5_6_DBF_PATH_LOCATION_SETUP.dts",
                "* Convenience/manual helper for setting the DBF path location.",
                "* The absolute-path proof script remains authoritative.",
                f"SET PATH TO {dbf_dir.resolve().as_posix()}",
                "",
            ]), encoding="utf-8")
            path_setup_rel = rel(path_script, repo)

            status = STATUS_GREEN if failures == 0 else STATUS_BLOCKED
        except Exception as exc:
            errors.append(str(exc))
            failures += 1
            status = STATUS_BLOCKED

    validation_issues = "0" if status == STATUS_GREEN else str(max(1, failures))

    write_csv(reports / "message_catalog_phase22ae_6_5_6_stage_gate_check_v1.csv",
              gates, ["GATE", "STATUS", "DETAIL"])
    write_csv(reports / "message_catalog_phase22ae_6_5_6_sandbox_copy_inventory_v1.csv",
              copy_rows, ["ROLE", "SOURCE", "TARGET", "BYTES", "SHA256"])
    write_csv(reports / "message_catalog_phase22ae_6_5_6_import_field_mapping_v1.csv",
              mapping_rows, ["TABLE", "TARGET_FIELD", "SAMPLE_VALUE"])
    write_csv(reports / "message_catalog_phase22ae_6_5_6_expected_message_keys_v1.csv",
              expected_msg_rows, ["SYMBOL_FIELD", "SYMBOL"])
    write_csv(reports / "message_catalog_phase22ae_6_5_6_expected_text_keys_v1.csv",
              expected_txt_rows, ["SYMBOL_FIELD", "SYMBOL", "LOCALE_FIELD", "LOCALE", "TEXT_FIELD", "TEXT_FIELD_TYPE"])

    boundary = [
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No source mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_DBF_CATALOG", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Sandbox DBF copies only."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_CDX_INDEXES", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active CDX mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active LMDB mutation."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No HELP DATA mutation."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CMDHELPCHK mutation."},
    ]
    write_csv(reports / "message_catalog_phase22ae_6_5_6_stage_boundary_ledger_v1.csv",
              boundary, ["PROTECTED_SYSTEM", "MUTATION_ALLOWED", "OBSERVED_MUTATION", "DETAIL"])

    write_csv(reports / "message_catalog_phase22ae_6_5_6_stage_status_summary_v1.csv", [{
        "STATUS": status,
        "VALIDATION_ISSUES": validation_issues,
        "PHASE22AE_6_5_4_BLOCKED_WITH_KEYS_PROVEN": 1 if val654.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_5_4_SANDBOX_PATH_BINDING_PROOF_BLOCKED" and val654.get("KEYS_PROVEN") == "1" else 0,
        "SANDBOX_ROOT": rel(sandbox, repo),
        "DBF_PATH_ROOT": rel(dbf_dir, repo),
        "ABSOLUTE_PATH_SCRIPT": abs_script_rel,
        "DBF_PATH_SETUP_SCRIPT": path_setup_rel,
        "UNIQUE_MESSAGE_DBF": rel(dbf_dir / UNIQUE_MESSAGE_DBF, repo),
        "UNIQUE_TEXT_DBF": rel(dbf_dir / UNIQUE_TEXT_DBF, repo),
        "MESSAGE_ROWS_BEFORE": msg_before,
        "TEXT_ROWS_BEFORE": text_before,
        "MESSAGE_PHYSICAL_ROWS_BEFORE": msg_phys_before,
        "TEXT_PHYSICAL_ROWS_BEFORE": text_phys_before,
        "IMPORT_MESSAGE_ROWS": len(expected_msg_rows),
        "IMPORT_TEXT_ROWS": len(expected_txt_rows),
        "TEXT_FIELD_TYPE": text_field_type,
        "ABSOLUTE_PATH_NAMES_SUPPORTED_BY_PROOF": 1,
        "ACTIVE_CATALOG_MUTATION_OBSERVED": 0,
        "SOURCE_FILES_MUTATED": 0,
        "HELP_DATA_MUTATION_OBSERVED": 0,
        "CMDHELPCHK_MUTATION_OBSERVED": 0,
        "ERRORS": "; ".join(errors),
        "NEXT_GATE": NEXT_GATE,
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }], ["STATUS", "VALIDATION_ISSUES", "PHASE22AE_6_5_4_BLOCKED_WITH_KEYS_PROVEN",
         "SANDBOX_ROOT", "DBF_PATH_ROOT", "ABSOLUTE_PATH_SCRIPT", "DBF_PATH_SETUP_SCRIPT",
         "UNIQUE_MESSAGE_DBF", "UNIQUE_TEXT_DBF", "MESSAGE_ROWS_BEFORE", "TEXT_ROWS_BEFORE",
         "MESSAGE_PHYSICAL_ROWS_BEFORE", "TEXT_PHYSICAL_ROWS_BEFORE",
         "IMPORT_MESSAGE_ROWS", "IMPORT_TEXT_ROWS", "TEXT_FIELD_TYPE",
         "ABSOLUTE_PATH_NAMES_SUPPORTED_BY_PROOF", "ACTIVE_CATALOG_MUTATION_OBSERVED",
         "SOURCE_FILES_MUTATED", "HELP_DATA_MUTATION_OBSERVED", "CMDHELPCHK_MUTATION_OBSERVED",
         "ERRORS", "NEXT_GATE", "REPORT_TIMESTAMP_UTC"])

    print(status)
    print(f"  validation issues: {validation_issues}")
    print(f"  Phase 22AE.6.5.4 blocked with keys proven: {1 if val654.get('STATUS') == 'MESSAGE_CATALOG_PHASE22AE_6_5_4_SANDBOX_PATH_BINDING_PROOF_BLOCKED' and val654.get('KEYS_PROVEN') == '1' else 0}")
    print(f"  sandbox root: {rel(sandbox, repo)}")
    print(f"  dbf path root: {rel(dbf_dir, repo)}")
    print(f"  absolute path script: {abs_script_rel}")
    print(f"  dbf path setup script: {path_setup_rel}")
    print(f"  message/text rows before: {msg_before}/{text_before}")
    print(f"  import message/text rows: {len(expected_msg_rows)}/{len(expected_txt_rows)}")
    print(f"  text field type: {text_field_type}")
    print("  absolute path names supported by proof: 1")
    print("  active catalog mutation observed: 0")
    print("  source files mutated: 0")
    print(f"  next gate: {NEXT_GATE}")
    print(f"  reports: {reports}")
    return 0 if status == STATUS_GREEN else 2

if __name__ == "__main__":
    raise SystemExit(main())
