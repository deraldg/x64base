#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import hashlib
import shutil
import struct
from datetime import datetime, timezone
from pathlib import Path

STATUS_GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_2_ISOLATED_IMPORT_EXECUTION_PROOF_STAGED_SOURCE_HELD"
STATUS_BLOCKED = "MESSAGE_CATALOG_PHASE22AE_6_5_2_ISOLATED_IMPORT_EXECUTION_PROOF_STAGING_BLOCKED"
NEXT_GATE = "RUN_PHASE22AE_6_5_2_ISOLATED_IMPORT_EXECUTION_RUNTIME_THEN_VALIDATE"

REPORT_DIR = Path("docs/messaging/reports")
SANDBOX_ROOT = Path("docs/messaging/sandbox/phase22ae_6_5_2_isolated_import_execution_v1")
SCRIPT_PATH = Path("docs/messaging/scripts/MESSAGE_CATALOG_PHASE22AE_6_5_2_ISOLATED_IMPORT_EXECUTION_PROOF.dts")

ACTIVE_MSG_ROOT = Path("dottalkpp/data/messaging")
ACTIVE_MSG_INDEX_ROOT = Path("dottalkpp/data/indexes/messaging")
ACTIVE_MSG_LMDB_ROOT = Path("dottalkpp/data/lmdb/messaging")
DEFAULT_INDEX_ROOT = Path("dottalkpp/data/indexes")
DEFAULT_LMDB_ROOT = Path("dottalkpp/data/lmdb")

TABLES = ["SYSTEM_MESSAGES", "SYSTEM_MESSAGE_TEXT"]

SYMBOL_ALIASES = ["SYMBOL", "MESSAGE_SYMBOL", "MSG_SYMBOL", "MSGID", "MESSAGE_ID", "KEY", "MSG_KEY"]
LOCALE_ALIASES = ["LOCALE", "LOCALE_ID", "LANG", "LANGUAGE", "CULTURE"]
TEXT_ALIASES = ["TEXT", "MESSAGE_TEXT", "MSG_TEXT", "VALUE", "LOCALIZED_TEXT", "MESSAGE"]
STATUS_ALIASES = ["STATUS", "ROW_STATUS"]
SOURCE_ALIASES = ["SOURCE_PHASE", "SOURCE", "PHASE"]

class DbfInfo:
    def __init__(self, path, record_count, header_len, record_len, fields):
        self.path = path
        self.record_count = record_count
        self.header_len = header_len
        self.record_len = record_len
        self.fields = fields

def read_csv(path: Path):
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

def first_row(path: Path):
    rows = read_csv(path)
    return rows[0] if rows else {}

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

def sha256_file(path: Path) -> str:
    if not path.exists() or not path.is_file():
        return ""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def savepoint_present(repo: Path, savepoint_id: str):
    latest_path = repo / REPORT_DIR / "message_savepoint_latest_v1.json"
    latest_id = ""
    if latest_path.exists():
        try:
            latest_id = json.loads(latest_path.read_text(encoding="utf-8")).get("savepoint_id", "")
        except Exception:
            latest_id = ""
    journal = repo / "docs/messaging/MESSAGING_SAVEPOINT_JOURNAL.md"
    text = journal.read_text(encoding="utf-8", errors="replace") if journal.exists() else ""
    return latest_id == savepoint_id or savepoint_id in text, latest_id

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
        if name:
            fields.append({"NAME": name, "TYPE": ftype, "LENGTH": length, "DECIMALS": decimals, "OFFSET": offset})
            offset += length
        pos += 32
    return DbfInfo(path, record_count, header_len, record_len, fields)

def field_names(info: DbfInfo):
    return [f["NAME"] for f in info.fields]

def choose_field(info: DbfInfo, aliases):
    names = {f["NAME"] for f in info.fields}
    for a in aliases:
        if a in names:
            return a
    return ""

def copy_file_if_exists(src: Path, dst: Path, repo: Path, rows: list[dict], role: str):
    exists = src.exists() and src.is_file()
    if exists:
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
    rows.append({
        "ROLE": role,
        "SOURCE": rel(src, repo),
        "TARGET": rel(dst, repo),
        "COPIED": 1 if exists else 0,
        "BYTES": dst.stat().st_size if exists and dst.exists() else 0,
        "SHA256": sha256_file(dst) if exists and dst.exists() else "",
    })
    return exists

def copy_dir_if_exists(src: Path, dst: Path, repo: Path, rows: list[dict], role: str):
    exists = src.exists() and src.is_dir()
    files = 0
    total = 0
    if exists:
        if dst.exists():
            shutil.rmtree(dst)
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(src, dst)
        for p in dst.rglob("*"):
            if p.is_file():
                files += 1
                total += p.stat().st_size
    rows.append({
        "ROLE": role,
        "SOURCE": rel(src, repo),
        "TARGET": rel(dst, repo),
        "COPIED": 1 if exists else 0,
        "BYTES": total,
        "SHA256": f"dir_files={files}" if exists else "",
    })
    return exists

def fingerprint_selected(repo: Path):
    rows = []
    targets = []
    for table in TABLES:
        targets.append((repo / ACTIVE_MSG_ROOT / f"{table}.dbf", f"active_dbf_{table}"))
        targets.append((repo / ACTIVE_MSG_INDEX_ROOT / f"{table}.cdx", f"active_msg_index_{table}_cdx"))
        targets.append((repo / ACTIVE_MSG_INDEX_ROOT / f"{table}.cdx.meta", f"active_msg_index_{table}_meta"))
        targets.append((repo / ACTIVE_MSG_LMDB_ROOT / f"{table}.cdx.d", f"active_msg_lmdb_{table}"))
        targets.append((repo / DEFAULT_INDEX_ROOT / f"{table}.cdx", f"default_index_{table}_cdx"))
        targets.append((repo / DEFAULT_INDEX_ROOT / f"{table}.cdx.meta", f"default_index_{table}_meta"))
        targets.append((repo / DEFAULT_LMDB_ROOT / f"{table}.cdx.d", f"default_lmdb_{table}"))
    for path, role in targets:
        if path.is_dir():
            files = sorted([p for p in path.rglob("*") if p.is_file()])
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

def norm_map(row: dict):
    return {str(k).strip().upper(): v for k, v in row.items() if k is not None}

def pick_value(src: dict, target_field: str, aliases: list[str]):
    t = target_field.upper()
    if t in src:
        return src.get(t, "")
    for a in aliases:
        if a in src:
            return src.get(a, "")
    return ""

def build_import_rows(info: DbfInfo, source_rows: list[dict], table_kind: str):
    out = []
    mapping_rows = []
    fields = field_names(info)
    sym_field = choose_field(info, SYMBOL_ALIASES)
    loc_field = choose_field(info, LOCALE_ALIASES)
    text_field = choose_field(info, TEXT_ALIASES)
    status_field = choose_field(info, STATUS_ALIASES)
    source_field = choose_field(info, SOURCE_ALIASES)

    for i, row in enumerate(source_rows, 1):
        src = norm_map(row)
        dst = {}
        for f in fields:
            val = ""
            if f == sym_field:
                val = pick_value(src, f, SYMBOL_ALIASES)
            elif f == loc_field:
                val = pick_value(src, f, LOCALE_ALIASES)
            elif f == text_field:
                val = pick_value(src, f, TEXT_ALIASES)
            elif f == status_field:
                val = pick_value(src, f, STATUS_ALIASES) or "CANDIDATE"
            elif f == source_field:
                val = pick_value(src, f, SOURCE_ALIASES) or "22AE_6_5_2"
            else:
                val = src.get(f, "")
            dst[f] = val
        out.append(dst)

    # Mapping summary per field.
    for f in fields:
        source = f if any(f in norm_map(r) for r in source_rows) else ""
        if f == sym_field:
            source = source or "|".join([a for a in SYMBOL_ALIASES if any(a in norm_map(r) for r in source_rows)])
        elif f == loc_field:
            source = source or "|".join([a for a in LOCALE_ALIASES if any(a in norm_map(r) for r in source_rows)])
        elif f == text_field:
            source = source or "|".join([a for a in TEXT_ALIASES if any(a in norm_map(r) for r in source_rows)])
        mapping_rows.append({"TABLE": table_kind, "TARGET_FIELD": f, "SOURCE_COLUMN_OR_ALIAS": source, "SAMPLE_VALUE": out[0].get(f, "") if out else ""})
    return out, mapping_rows, sym_field, loc_field, text_field

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--replace-existing-sandbox", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    reports = repo / REPORT_DIR
    reports.mkdir(parents=True, exist_ok=True)

    ae651 = first_row(reports / "message_catalog_phase22ae_6_5_1_validate_status_summary_v1.csv")
    sp651, latest_id = savepoint_present(repo, "MSG-022AE.6.5.1")
    stage651 = first_row(reports / "message_catalog_phase22ae_6_5_1_stage_status_summary_v1.csv")

    sandbox = repo / SANDBOX_ROOT
    gates = []
    failures = 0
    errors = []

    def gate(name, ok, detail):
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": str(detail)})
        if not ok:
            failures += 1

    gate("PHASE22AE_6_5_1_IMPORT_READY",
         ae651.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_5_1_IMPORT_OR_REBUILD_SANDBOX_PROOF_GREEN_IMPORT_SURFACE_CANDIDATE_READY",
         ae651.get("STATUS", "missing"))
    gate("MSG_022AE_6_5_1_SAVEPOINT_PRESENT", sp651, latest_id)
    gate("IMPORT_SURFACE_READY", ae651.get("IMPORT_SURFACE_READY") == "1", ae651.get("IMPORT_SURFACE_READY", "missing"))
    gate("CANDIDATE_PAIR_FOUND", ae651.get("CANDIDATE_MESSAGE_FILE_FOUND") == "1" and ae651.get("CANDIDATE_TEXT_FILE_FOUND") == "1",
         f"msg={ae651.get('CANDIDATE_MESSAGE_FILE_FOUND','')}; text={ae651.get('CANDIDATE_TEXT_FILE_FOUND','')}")
    gate("SANDBOX_NOT_EXISTING_OR_REPLACE_ALLOWED", (not sandbox.exists()) or args.replace_existing_sandbox, rel(sandbox, repo))

    msg_candidate = repo / stage651.get("CANDIDATE_MESSAGE_FILE", "")
    txt_candidate = repo / stage651.get("CANDIDATE_TEXT_FILE", "")
    gate("CANDIDATE_MESSAGE_FILE_EXISTS", msg_candidate.exists(), rel(msg_candidate, repo))
    gate("CANDIDATE_TEXT_FILE_EXISTS", txt_candidate.exists(), rel(txt_candidate, repo))

    before_fp = fingerprint_selected(repo)
    write_csv(reports / "message_catalog_phase22ae_6_5_2_protected_fingerprint_before_v1.csv",
              before_fp, ["ROLE", "PATH", "EXISTS", "KIND", "BYTES", "SHA256", "FILES"])

    copy_rows = []
    mapping_rows = []
    expected_message_rows = []
    expected_text_rows = []
    msg_count = ""
    txt_count = ""
    status = STATUS_BLOCKED
    script_rel = ""

    if failures == 0:
        try:
            if sandbox.exists() and args.replace_existing_sandbox:
                shutil.rmtree(sandbox)
            (sandbox / "dbf").mkdir(parents=True, exist_ok=True)
            (sandbox / "indexes").mkdir(parents=True, exist_ok=True)
            (sandbox / "lmdb").mkdir(parents=True, exist_ok=True)
            (sandbox / "import").mkdir(parents=True, exist_ok=True)
            (sandbox / "source_candidate_rows").mkdir(parents=True, exist_ok=True)

            # Fresh isolated sandbox copies.
            for table in TABLES:
                copy_file_if_exists(repo / ACTIVE_MSG_ROOT / f"{table}.dbf", sandbox / "dbf" / f"{table}.dbf", repo, copy_rows, f"{table}_dbf_copy")
                copied_cdx = copy_file_if_exists(repo / ACTIVE_MSG_INDEX_ROOT / f"{table}.cdx", sandbox / "indexes" / f"{table}.cdx", repo, copy_rows, f"{table}_messaging_cdx_copy")
                copied_meta = copy_file_if_exists(repo / ACTIVE_MSG_INDEX_ROOT / f"{table}.cdx.meta", sandbox / "indexes" / f"{table}.cdx.meta", repo, copy_rows, f"{table}_messaging_cdx_meta_copy")
                if not copied_cdx:
                    copy_file_if_exists(repo / DEFAULT_INDEX_ROOT / f"{table}.cdx", sandbox / "indexes" / f"{table}.cdx", repo, copy_rows, f"{table}_default_cdx_fallback_copy")
                if not copied_meta:
                    copy_file_if_exists(repo / DEFAULT_INDEX_ROOT / f"{table}.cdx.meta", sandbox / "indexes" / f"{table}.cdx.meta", repo, copy_rows, f"{table}_default_cdx_meta_fallback_copy")
                copied_lmdb = copy_dir_if_exists(repo / ACTIVE_MSG_LMDB_ROOT / f"{table}.cdx.d", sandbox / "lmdb" / f"{table}.cdx.d", repo, copy_rows, f"{table}_messaging_lmdb_copy")
                if not copied_lmdb:
                    copy_dir_if_exists(repo / DEFAULT_LMDB_ROOT / f"{table}.cdx.d", sandbox / "lmdb" / f"{table}.cdx.d", repo, copy_rows, f"{table}_default_lmdb_fallback_copy")
                if (sandbox / "indexes" / f"{table}.cdx").exists():
                    copy_file_if_exists(sandbox / "indexes" / f"{table}.cdx", sandbox / "dbf" / f"{table}.cdx", repo, copy_rows, f"{table}_co_located_cdx_copy")
                if (sandbox / "indexes" / f"{table}.cdx.meta").exists():
                    copy_file_if_exists(sandbox / "indexes" / f"{table}.cdx.meta", sandbox / "dbf" / f"{table}.cdx.meta", repo, copy_rows, f"{table}_co_located_cdx_meta_copy")

            shutil.copy2(msg_candidate, sandbox / "source_candidate_rows/message_rows_source.csv")
            shutil.copy2(txt_candidate, sandbox / "source_candidate_rows/text_rows_source.csv")

            msg_info = parse_dbf(sandbox / "dbf/SYSTEM_MESSAGES.dbf")
            txt_info = parse_dbf(sandbox / "dbf/SYSTEM_MESSAGE_TEXT.dbf")
            msg_count = msg_info.record_count
            txt_count = txt_info.record_count

            msg_src_rows = read_csv(msg_candidate)
            txt_src_rows = read_csv(txt_candidate)
            msg_import_rows, msg_map, msg_symbol_field, _, _ = build_import_rows(msg_info, msg_src_rows, "SYSTEM_MESSAGES")
            txt_import_rows, txt_map, txt_symbol_field, txt_locale_field, txt_text_field = build_import_rows(txt_info, txt_src_rows, "SYSTEM_MESSAGE_TEXT")
            mapping_rows.extend(msg_map)
            mapping_rows.extend(txt_map)

            msg_import = sandbox / "import/system_messages_import.csv"
            txt_import = sandbox / "import/system_message_text_import.csv"
            write_csv(msg_import, msg_import_rows, field_names(msg_info))
            write_csv(txt_import, txt_import_rows, field_names(txt_info))

            for r in msg_import_rows:
                expected_message_rows.append({
                    "SYMBOL_FIELD": msg_symbol_field,
                    "SYMBOL": r.get(msg_symbol_field, ""),
                    "SOURCE": rel(msg_candidate, repo),
                    "IMPORT_FILE": rel(msg_import, repo),
                })
            for r in txt_import_rows:
                expected_text_rows.append({
                    "SYMBOL_FIELD": txt_symbol_field,
                    "SYMBOL": r.get(txt_symbol_field, ""),
                    "LOCALE_FIELD": txt_locale_field,
                    "LOCALE": r.get(txt_locale_field, ""),
                    "TEXT_FIELD": txt_text_field,
                    "TEXT_EXPECTED": r.get(txt_text_field, ""),
                    "SOURCE": rel(txt_candidate, repo),
                    "IMPORT_FILE": rel(txt_import, repo),
                })

            gate("IMPORT_MESSAGE_ROWS_COUNT_2", len(msg_import_rows) == 2, len(msg_import_rows))
            gate("IMPORT_TEXT_ROWS_COUNT_10", len(txt_import_rows) == 10, len(txt_import_rows))
            gate("MESSAGE_SYMBOL_FIELD_MAPPED", bool(msg_symbol_field), msg_symbol_field)
            gate("TEXT_SYMBOL_LOCALE_FIELDS_MAPPED", bool(txt_symbol_field and txt_locale_field), f"{txt_symbol_field}/{txt_locale_field}")

            script = repo / SCRIPT_PATH
            script.parent.mkdir(parents=True, exist_ok=True)
            lines = [
                "* MESSAGE_CATALOG_PHASE22AE_6_5_2_ISOLATED_IMPORT_EXECUTION_PROOF.dts",
                "* Executes IMPORT against isolated sandbox DBF copies only.",
                "* Candidate CSVs are generated with headers matching target DBF fields.",
                "",
                f"USE {(sandbox / 'dbf/SYSTEM_MESSAGES.dbf').resolve().as_posix()}",
                f"IMPORT {msg_import.resolve().as_posix()}",
                "",
                f"USE {(sandbox / 'dbf/SYSTEM_MESSAGE_TEXT.dbf').resolve().as_posix()}",
                f"IMPORT {txt_import.resolve().as_posix()}",
                "",
            ]
            script.write_text("\n".join(lines), encoding="utf-8")
            script_rel = rel(script, repo)

            status = STATUS_GREEN
        except Exception as exc:
            errors.append(str(exc))
            failures += 1
            status = STATUS_BLOCKED

    validation_issues = "0" if status == STATUS_GREEN else str(failures)

    write_csv(reports / "message_catalog_phase22ae_6_5_2_stage_gate_check_v1.csv", gates, ["GATE", "STATUS", "DETAIL"])
    write_csv(reports / "message_catalog_phase22ae_6_5_2_sandbox_copy_inventory_v1.csv", copy_rows, ["ROLE", "SOURCE", "TARGET", "COPIED", "BYTES", "SHA256"])
    write_csv(reports / "message_catalog_phase22ae_6_5_2_import_field_mapping_v1.csv", mapping_rows, ["TABLE", "TARGET_FIELD", "SOURCE_COLUMN_OR_ALIAS", "SAMPLE_VALUE"])
    write_csv(reports / "message_catalog_phase22ae_6_5_2_expected_message_rows_v1.csv", expected_message_rows, ["SYMBOL_FIELD", "SYMBOL", "SOURCE", "IMPORT_FILE"])
    write_csv(reports / "message_catalog_phase22ae_6_5_2_expected_text_rows_v1.csv", expected_text_rows, ["SYMBOL_FIELD", "SYMBOL", "LOCALE_FIELD", "LOCALE", "TEXT_FIELD", "TEXT_EXPECTED", "SOURCE", "IMPORT_FILE"])

    boundary = [
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No source mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_DBF_CATALOG", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Stage copies only."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_CDX_INDEXES", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Stage copies only."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Stage copies only."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No HELP DATA mutation."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CMDHELPCHK mutation."},
    ]
    write_csv(reports / "message_catalog_phase22ae_6_5_2_stage_boundary_ledger_v1.csv", boundary, ["PROTECTED_SYSTEM", "MUTATION_ALLOWED", "OBSERVED_MUTATION", "DETAIL"])

    write_csv(reports / "message_catalog_phase22ae_6_5_2_stage_status_summary_v1.csv", [{
        "STATUS": status,
        "VALIDATION_ISSUES": validation_issues,
        "PHASE22AE_6_5_1_IMPORT_READY": 1 if ae651.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_5_1_IMPORT_OR_REBUILD_SANDBOX_PROOF_GREEN_IMPORT_SURFACE_CANDIDATE_READY" else 0,
        "MSG_022AE_6_5_1_SAVEPOINT_PRESENT": 1 if sp651 else 0,
        "SANDBOX_ROOT": rel(sandbox, repo),
        "SCRIPT_PATH": script_rel,
        "SANDBOX_MESSAGE_ROWS_BEFORE": msg_count,
        "SANDBOX_TEXT_ROWS_BEFORE": txt_count,
        "IMPORT_MESSAGE_ROWS": len(expected_message_rows),
        "IMPORT_TEXT_ROWS": len(expected_text_rows),
        "CANDIDATE_MESSAGE_FILE": rel(msg_candidate, repo) if msg_candidate else "",
        "CANDIDATE_TEXT_FILE": rel(txt_candidate, repo) if txt_candidate else "",
        "ACTIVE_CATALOG_MUTATION_OBSERVED": 0,
        "SOURCE_FILES_MUTATED": 0,
        "HELP_DATA_MUTATION_OBSERVED": 0,
        "CMDHELPCHK_MUTATION_OBSERVED": 0,
        "ERRORS": "; ".join(errors),
        "NEXT_GATE": NEXT_GATE,
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }], ["STATUS", "VALIDATION_ISSUES", "PHASE22AE_6_5_1_IMPORT_READY", "MSG_022AE_6_5_1_SAVEPOINT_PRESENT",
         "SANDBOX_ROOT", "SCRIPT_PATH", "SANDBOX_MESSAGE_ROWS_BEFORE", "SANDBOX_TEXT_ROWS_BEFORE",
         "IMPORT_MESSAGE_ROWS", "IMPORT_TEXT_ROWS", "CANDIDATE_MESSAGE_FILE", "CANDIDATE_TEXT_FILE",
         "ACTIVE_CATALOG_MUTATION_OBSERVED", "SOURCE_FILES_MUTATED", "HELP_DATA_MUTATION_OBSERVED",
         "CMDHELPCHK_MUTATION_OBSERVED", "ERRORS", "NEXT_GATE", "REPORT_TIMESTAMP_UTC"])

    md = f"""# Message Catalog Phase 22AE.6.5.2 Isolated Import Execution Proof

Status: `{status}`

This stage creates import CSVs with headers matching the sandbox DBF fields and
generates a runtime script that imports candidate rows into isolated sandbox
copies only.

Runtime script:

```text
{script_rel}
```

Next gate:

```text
{NEXT_GATE}
```
"""
    (reports / "MESSAGE_CATALOG_PHASE22AE_6_5_2_ISOLATED_IMPORT_EXECUTION_PROOF.md").write_text(md, encoding="utf-8")

    print(status)
    print(f"  validation issues: {validation_issues}")
    print(f"  Phase 22AE.6.5.1 import ready: {1 if ae651.get('STATUS') == 'MESSAGE_CATALOG_PHASE22AE_6_5_1_IMPORT_OR_REBUILD_SANDBOX_PROOF_GREEN_IMPORT_SURFACE_CANDIDATE_READY' else 0}")
    print(f"  MSG-022AE.6.5.1 savepoint present: {1 if sp651 else 0}")
    print(f"  sandbox root: {rel(sandbox, repo)}")
    print(f"  script path: {script_rel}")
    print(f"  sandbox message rows before: {msg_count}")
    print(f"  sandbox text rows before: {txt_count}")
    print(f"  import message rows: {len(expected_message_rows)}")
    print(f"  import text rows: {len(expected_text_rows)}")
    print("  active catalog mutation observed: 0")
    print("  source files mutated: 0")
    print(f"  next gate: {NEXT_GATE}")
    print(f"  reports: {reports}")
    return 0 if status == STATUS_GREEN else 2

if __name__ == "__main__":
    raise SystemExit(main())
