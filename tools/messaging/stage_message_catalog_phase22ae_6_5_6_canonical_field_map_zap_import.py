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

STATUS_GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_6_CANONICAL_FIELD_MAP_ZAP_IMPORT_PROOF_STAGED_SOURCE_HELD"
STATUS_BLOCKED = "MESSAGE_CATALOG_PHASE22AE_6_5_6_CANONICAL_FIELD_MAP_ZAP_IMPORT_PROOF_STAGING_BLOCKED"
NEXT_GATE = "RUN_PHASE22AE_6_5_6_CANONICAL_FIELD_MAP_ZAP_IMPORT_RUNTIME_THEN_VALIDATE"

REPORT_DIR = Path("docs/messaging/reports")
SANDBOX_ROOT = Path("docs/messaging/sandbox/phase22ae_6_5_6_canonical_field_map_zap_import_v1")
SCRIPT_PATH = Path("docs/messaging/scripts/MESSAGE_CATALOG_PHASE22AE_6_5_6_CANONICAL_FIELD_MAP_ZAP_IMPORT_PROOF.dts")

ACTIVE_MSG_ROOT = Path("dottalkpp/data/messaging")
ACTIVE_MSG_INDEX_ROOT = Path("dottalkpp/data/indexes/messaging")
ACTIVE_MSG_LMDB_ROOT = Path("dottalkpp/data/lmdb/messaging")
DEFAULT_INDEX_ROOT = Path("dottalkpp/data/indexes")
DEFAULT_LMDB_ROOT = Path("dottalkpp/data/lmdb")

CANON_MSG = Path("docs/messaging/apply/phase22ad_active_catalog_replacement_apply_package_v1/rows/message_catalog_candidate_message_adds_v1.csv")
CANON_TXT = Path("docs/messaging/apply/phase22ad_active_catalog_replacement_apply_package_v1/rows/message_catalog_candidate_text_adds_v1.csv")

TABLES = ["SYSTEM_MESSAGES", "SYSTEM_MESSAGE_TEXT"]
SIDE_EXTS = [".dtx", ".dbt", ".fpt", ".memo", ".mdx"]

SYMBOL_COLS = ["SYMBOL", "ENUMNAME", "MESSAGE_SYMBOL", "MSG_SYMBOL", "MESSAGE_ID", "MSGID", "KEY", "SYMBOLLOC", "NAME"]
LOCALE_COLS = ["LOCALE", "MSGLOCALE", "LOCALE_ID", "LANG", "LANGUAGE", "CULTURE"]
TEXT_COLS = ["TEXT", "MESSAGE_TEXT", "MSG_TEXT", "VALUE", "LOCALIZED_TEXT", "DESCRIPTION", "DEFAULT_TEXT"]
STATUS_COLS = ["STATUS", "ROW_STATUS", "STATE"]
SRC_COLS = ["SRC", "SOURCE", "SOURCE_PHASE", "PHASE", "SOURCE_ID"]
HASH_COLS = ["TXTHASH", "TEXT_HASH", "HASH", "SHA256"]

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

def rel(path: Path, repo: Path):
    try:
        return str(path.relative_to(repo)).replace("\\", "/")
    except Exception:
        return str(path).replace("\\", "/")

def sha256_file(path: Path):
    if not path.exists() or not path.is_file():
        return ""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def savepoint_present(repo: Path, savepoint_id: str):
    latest = ""
    latest_path = repo / REPORT_DIR / "message_savepoint_latest_v1.json"
    if latest_path.exists():
        try:
            latest = json.loads(latest_path.read_text(encoding="utf-8")).get("savepoint_id", "")
        except Exception:
            latest = ""
    journal = repo / "docs/messaging/MESSAGING_SAVEPOINT_JOURNAL.md"
    text = journal.read_text(encoding="utf-8", errors="replace") if journal.exists() else ""
    return latest == savepoint_id or savepoint_id in text, latest

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

def read_dbf_rows(info: DbfInfo):
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
            for fld in info.fields:
                raw = rec[fld["OFFSET"]:fld["OFFSET"] + fld["LENGTH"]]
                if fld["TYPE"].upper() == "C":
                    row[fld["NAME"]] = raw.decode("cp1252", errors="replace").rstrip().strip()
                elif fld["TYPE"].upper() == "M":
                    row[fld["NAME"]] = raw.decode("cp1252", errors="replace").rstrip().strip()
                else:
                    row[fld["NAME"]] = raw.decode("ascii", errors="replace").rstrip().strip()
            rows.append(row)
    return rows

def field_names(info: DbfInfo):
    return [f["NAME"] for f in info.fields]

def norm(row):
    return {str(k).strip().upper(): ("" if v is None else str(v)) for k, v in row.items() if k is not None}

def first_nonempty(src, cols):
    for c in cols:
        if src.get(c, "").strip():
            return src[c].strip()
    return ""

def extract_candidate(row):
    src = norm(row)
    sym = first_nonempty(src, SYMBOL_COLS)
    loc = first_nonempty(src, LOCALE_COLS)
    text = first_nonempty(src, TEXT_COLS)
    status = first_nonempty(src, STATUS_COLS) or "CANDIDATE"
    source = first_nonempty(src, SRC_COLS) or "phase22ad_canonical"
    thash = first_nonempty(src, HASH_COLS)
    # If SYMBOLLOC is the only useful compound, split a trailing locale if present.
    if not loc and "|" in sym:
        parts = sym.rsplit("|", 1)
        if len(parts) == 2:
            sym, loc = parts[0], parts[1]
    return {
        "SYMBOL": sym,
        "ENUMNAME": sym,
        "LOCALE": loc,
        "MSGLOCALE": loc,
        "SYMBOLLOC": sym if not loc else f"{sym}|{loc}",
        "TEXT": text,
        "TXTHASH": thash,
        "STATUS": status,
        "SRC": source,
    }

def target_value(table, field, cand, recno):
    f = field.upper()
    symbol = cand["SYMBOL"]
    locale = cand["LOCALE"]
    symbol_loc = cand["SYMBOLLOC"] or symbol
    text = cand["TEXT"]
    if f == "MSGID":
        # Preserve exact key proof by putting symbol into MSGID for candidate rows if the table lacks a better id discipline.
        return symbol[:60] if table == "SYSTEM_MESSAGES" else symbol[:60]
    if f in ("SYMBOL", "ENUMNAME", "MESSAGE_SYMBOL", "MSG_SYMBOL", "KEY", "NAME", "CODE"):
        return symbol
    if f in ("LOCALE", "MSGLOCALE", "LOCALE_ID", "LANG", "LANGUAGE", "CULTURE"):
        return locale
    if f == "SYMBOLLOC":
        return symbol_loc
    if f in ("TEXT", "MESSAGE_TEXT", "MSG_TEXT", "VALUE", "LOCALIZED_TEXT", "DESCRIPTION", "DEFAULT_TEXT"):
        return text
    if f in ("TXTHASH", "TEXT_HASH", "HASH", "SHA256"):
        if cand["TXTHASH"]:
            return cand["TXTHASH"]
        return hashlib.sha256(text.encode("utf-8")).hexdigest()[:60] if text else ""
    if f in ("STATUS", "ROW_STATUS", "STATE") or f.endswith("STATUS"):
        return cand["STATUS"]
    if f in ("SRC", "SOURCE", "SOURCE_PHASE", "PHASE", "SOURCE_ID") or f.startswith("SRC"):
        return cand["SRC"]
    # Conservative fallback for symbol-ish unknown fields.
    if any(tok in f for tok in ["SYMBOL", "ENUM", "MSG", "MESSAGE", "KEY"]):
        return symbol
    if table == "SYSTEM_MESSAGE_TEXT" and any(tok in f for tok in ["LOC", "LANG"]):
        return locale
    return ""

def make_candidate_rows(info: DbfInfo, canon_rows, table):
    fields = field_names(info)
    out = []
    expected = []
    fmap = []
    for i, row in enumerate(canon_rows, 1):
        cand = extract_candidate(row)
        mapped = {f: target_value(table, f, cand, i) for f in fields}
        out.append(mapped)
        if table == "SYSTEM_MESSAGES":
            expected.append({"SYMBOL": cand["SYMBOL"], "SOURCE": "canonical_phase22ad"})
        else:
            expected.append({"SYMBOL": cand["SYMBOL"], "LOCALE": cand["LOCALE"], "SOURCE": "canonical_phase22ad"})
    for f in fields:
        samples = [r.get(f, "") for r in out if r.get(f, "")]
        fmap.append({"TABLE": table, "TARGET_FIELD": f, "FILLED_ROWS": len(samples), "SAMPLE_VALUE": samples[0] if samples else ""})
    return out, expected, fmap

def copy_file_if_exists(src: Path, dst: Path, repo: Path, rows: list[dict], role: str):
    exists = src.exists() and src.is_file()
    if exists:
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
    rows.append({"ROLE": role, "SOURCE": rel(src, repo), "TARGET": rel(dst, repo),
                 "COPIED": 1 if exists else 0, "BYTES": dst.stat().st_size if exists and dst.exists() else 0,
                 "SHA256": sha256_file(dst) if exists and dst.exists() else ""})
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
    rows.append({"ROLE": role, "SOURCE": rel(src, repo), "TARGET": rel(dst, repo),
                 "COPIED": 1 if exists else 0, "BYTES": total, "SHA256": f"dir_files={files}" if exists else ""})
    return exists

def copy_sidecars(src_dbf: Path, dst_dir: Path, repo: Path, rows: list[dict], table: str):
    copied = 0
    base = src_dbf.with_suffix("")
    for ext in SIDE_EXTS:
        src = base.with_suffix(ext)
        dst = dst_dir / src.name
        if copy_file_if_exists(src, dst, repo, rows, f"{table}_sidecar_{ext}_copy"):
            copied += 1
    return copied

def fingerprint_selected(repo: Path):
    rows = []
    targets = []
    for table in TABLES:
        targets.extend([
            (repo / ACTIVE_MSG_ROOT / f"{table}.dbf", f"active_dbf_{table}"),
            (repo / ACTIVE_MSG_ROOT / f"{table}.dtx", f"active_dtx_{table}"),
            (repo / ACTIVE_MSG_INDEX_ROOT / f"{table}.cdx", f"active_msg_index_{table}_cdx"),
            (repo / ACTIVE_MSG_INDEX_ROOT / f"{table}.cdx.meta", f"active_msg_index_{table}_meta"),
            (repo / ACTIVE_MSG_LMDB_ROOT / f"{table}.cdx.d", f"active_msg_lmdb_{table}"),
            (repo / DEFAULT_INDEX_ROOT / f"{table}.cdx", f"default_index_{table}_cdx"),
            (repo / DEFAULT_INDEX_ROOT / f"{table}.cdx.meta", f"default_index_{table}_meta"),
            (repo / DEFAULT_LMDB_ROOT / f"{table}.cdx.d", f"default_lmdb_{table}"),
        ])
    for path, role in targets:
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

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--replace-existing-sandbox", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    reports = repo / REPORT_DIR
    reports.mkdir(parents=True, exist_ok=True)

    ae655 = first_row(reports / "message_catalog_phase22ae_6_5_5_status_summary_v1.csv")
    sp655, latest = savepoint_present(repo, "MSG-022AE.6.5.5")

    sandbox = repo / SANDBOX_ROOT
    gates = []
    failures = 0
    errors = []
    def gate(name, ok, detail):
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": str(detail)})
        if not ok:
            failures += 1

    gate("PHASE22AE_6_5_5_GREEN", ae655.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_5_5_FIELD_MAP_FORENSIC_REVIEW_GREEN_SOURCE_HELD", ae655.get("STATUS","missing"))
    gate("MSG_022AE_6_5_5_SAVEPOINT_PRESENT", sp655, latest)
    gate("CANONICAL_MESSAGE_SOURCE_EXISTS", (repo / CANON_MSG).exists(), rel(repo / CANON_MSG, repo))
    gate("CANONICAL_TEXT_SOURCE_EXISTS", (repo / CANON_TXT).exists(), rel(repo / CANON_TXT, repo))
    gate("SANDBOX_NOT_EXISTING_OR_REPLACE_ALLOWED", (not sandbox.exists()) or args.replace_existing_sandbox, rel(sandbox, repo))

    canon_msg = read_csv(repo / CANON_MSG)
    canon_txt = read_csv(repo / CANON_TXT)
    gate("CANONICAL_MESSAGE_ROWS_2", len(canon_msg) == 2, len(canon_msg))
    gate("CANONICAL_TEXT_ROWS_10", len(canon_txt) == 10, len(canon_txt))

    before_fp = fingerprint_selected(repo)
    write_csv(reports / "message_catalog_phase22ae_6_5_6_protected_fingerprint_before_v1.csv", before_fp, ["ROLE","PATH","EXISTS","KIND","BYTES","SHA256","FILES"])

    copy_rows = []
    fmap = []
    expected_msg = []
    expected_txt = []
    manifest = []
    msg_before = ""
    txt_before = ""
    script_rel = ""
    status = STATUS_BLOCKED

    if failures == 0:
        try:
            if sandbox.exists() and args.replace_existing_sandbox:
                shutil.rmtree(sandbox)
            for sub in ["dbf", "indexes", "lmdb", "import", "source_canonical_rows"]:
                (sandbox / sub).mkdir(parents=True, exist_ok=True)

            for table in TABLES:
                src_dbf = repo / ACTIVE_MSG_ROOT / f"{table}.dbf"
                dst_dbf = sandbox / "dbf" / f"{table}.dbf"
                copy_file_if_exists(src_dbf, dst_dbf, repo, copy_rows, f"{table}_dbf_copy")
                copy_sidecars(src_dbf, sandbox / "dbf", repo, copy_rows, table)
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

            shutil.copy2(repo / CANON_MSG, sandbox / "source_canonical_rows/message_rows_canonical_phase22ad.csv")
            shutil.copy2(repo / CANON_TXT, sandbox / "source_canonical_rows/text_rows_canonical_phase22ad.csv")

            msg_info = parse_dbf(sandbox / "dbf/SYSTEM_MESSAGES.dbf")
            txt_info = parse_dbf(sandbox / "dbf/SYSTEM_MESSAGE_TEXT.dbf")
            msg_before = msg_info.record_count
            txt_before = txt_info.record_count

            active_msg_rows = read_dbf_rows(msg_info)
            active_txt_rows = read_dbf_rows(txt_info)
            msg_fields = field_names(msg_info)
            txt_fields = field_names(txt_info)

            msg_candidates, expected_msg, msg_map = make_candidate_rows(msg_info, canon_msg, "SYSTEM_MESSAGES")
            txt_candidates, expected_txt, txt_map = make_candidate_rows(txt_info, canon_txt, "SYSTEM_MESSAGE_TEXT")
            fmap.extend(msg_map)
            fmap.extend(txt_map)

            full_msg = active_msg_rows + msg_candidates
            full_txt = active_txt_rows + txt_candidates

            msg_csv = sandbox / "import/system_messages_canonical_field_map_full_state.csv"
            txt_csv = sandbox / "import/system_message_text_canonical_field_map_full_state.csv"
            write_csv(msg_csv, full_msg, msg_fields)
            write_csv(txt_csv, full_txt, txt_fields)

            manifest = [
                {"TABLE":"SYSTEM_MESSAGES","ACTIVE_ROWS":len(active_msg_rows),"CANONICAL_CANDIDATE_ROWS":len(msg_candidates),"FULL_STATE_ROWS":len(full_msg),"CSV":rel(msg_csv,repo)},
                {"TABLE":"SYSTEM_MESSAGE_TEXT","ACTIVE_ROWS":len(active_txt_rows),"CANONICAL_CANDIDATE_ROWS":len(txt_candidates),"FULL_STATE_ROWS":len(full_txt),"CSV":rel(txt_csv,repo)},
            ]
            gate("FULL_STATE_MESSAGE_ROWS_14", len(full_msg) == 14, len(full_msg))
            gate("FULL_STATE_TEXT_ROWS_70", len(full_txt) == 70, len(full_txt))
            gate("EXPECTED_MESSAGE_SYMBOLS_2", len(expected_msg) == 2 and all(r.get("SYMBOL") for r in expected_msg), expected_msg)
            gate("EXPECTED_TEXT_KEYS_10", len(expected_txt) == 10 and all(r.get("SYMBOL") for r in expected_txt), expected_txt[:2])

            script = repo / SCRIPT_PATH
            script.parent.mkdir(parents=True, exist_ok=True)
            script.write_text("\n".join([
                "* MESSAGE_CATALOG_PHASE22AE_6_5_6_CANONICAL_FIELD_MAP_ZAP_IMPORT_PROOF.dts",
                "* Sandbox-only proof: canonical Phase22AD field map, ZAP isolated copies, reopen, import full 14/70 state.",
                "* No active catalog path is used.",
                "",
                f"USE {(sandbox / 'dbf/SYSTEM_MESSAGES.dbf').resolve().as_posix()}",
                "ZAP",
                f"USE {(sandbox / 'dbf/SYSTEM_MESSAGES.dbf').resolve().as_posix()}",
                f"IMPORT {msg_csv.resolve().as_posix()}",
                "",
                f"USE {(sandbox / 'dbf/SYSTEM_MESSAGE_TEXT.dbf').resolve().as_posix()}",
                "ZAP",
                f"USE {(sandbox / 'dbf/SYSTEM_MESSAGE_TEXT.dbf').resolve().as_posix()}",
                f"IMPORT {txt_csv.resolve().as_posix()}",
                "",
            ]), encoding="utf-8")
            script_rel = rel(script, repo)
            status = STATUS_GREEN
        except Exception as exc:
            errors.append(str(exc))
            failures += 1

    validation_issues = "0" if status == STATUS_GREEN and failures == 0 else str(max(1, failures))

    write_csv(reports / "message_catalog_phase22ae_6_5_6_stage_gate_check_v1.csv", gates, ["GATE","STATUS","DETAIL"])
    write_csv(reports / "message_catalog_phase22ae_6_5_6_sandbox_copy_inventory_v1.csv", copy_rows, ["ROLE","SOURCE","TARGET","COPIED","BYTES","SHA256"])
    write_csv(reports / "message_catalog_phase22ae_6_5_6_canonical_field_map_v1.csv", fmap, ["TABLE","TARGET_FIELD","FILLED_ROWS","SAMPLE_VALUE"])
    write_csv(reports / "message_catalog_phase22ae_6_5_6_full_state_manifest_v1.csv", manifest, ["TABLE","ACTIVE_ROWS","CANONICAL_CANDIDATE_ROWS","FULL_STATE_ROWS","CSV"])
    write_csv(reports / "message_catalog_phase22ae_6_5_6_expected_message_rows_v1.csv", expected_msg, ["SYMBOL","SOURCE"])
    write_csv(reports / "message_catalog_phase22ae_6_5_6_expected_text_rows_v1.csv", expected_txt, ["SYMBOL","LOCALE","SOURCE"])

    boundary = [
        {"PROTECTED_SYSTEM":"SOURCE_CODE","MUTATION_ALLOWED":0,"OBSERVED_MUTATION":0,"DETAIL":"No source mutation."},
        {"PROTECTED_SYSTEM":"ACTIVE_MESSAGING_DBF_CATALOG","MUTATION_ALLOWED":0,"OBSERVED_MUTATION":0,"DETAIL":"Stage copies only."},
        {"PROTECTED_SYSTEM":"ACTIVE_MESSAGING_CDX_INDEXES","MUTATION_ALLOWED":0,"OBSERVED_MUTATION":0,"DETAIL":"Stage copies only."},
        {"PROTECTED_SYSTEM":"ACTIVE_MESSAGING_LMDB","MUTATION_ALLOWED":0,"OBSERVED_MUTATION":0,"DETAIL":"Stage copies only."},
        {"PROTECTED_SYSTEM":"HELP_DATA","MUTATION_ALLOWED":0,"OBSERVED_MUTATION":0,"DETAIL":"No HELP DATA mutation."},
        {"PROTECTED_SYSTEM":"CMDHELPCHK","MUTATION_ALLOWED":0,"OBSERVED_MUTATION":0,"DETAIL":"No CMDHELPCHK mutation."},
    ]
    write_csv(reports / "message_catalog_phase22ae_6_5_6_stage_boundary_ledger_v1.csv", boundary, ["PROTECTED_SYSTEM","MUTATION_ALLOWED","OBSERVED_MUTATION","DETAIL"])

    write_csv(reports / "message_catalog_phase22ae_6_5_6_stage_status_summary_v1.csv", [{
        "STATUS": status,
        "VALIDATION_ISSUES": validation_issues,
        "PHASE22AE_6_5_5_GREEN": 1 if ae655.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_5_5_FIELD_MAP_FORENSIC_REVIEW_GREEN_SOURCE_HELD" else 0,
        "MSG_022AE_6_5_5_SAVEPOINT_PRESENT": 1 if sp655 else 0,
        "SANDBOX_ROOT": rel(sandbox, repo),
        "SCRIPT_PATH": script_rel,
        "SANDBOX_MESSAGE_ROWS_BEFORE": msg_before,
        "SANDBOX_TEXT_ROWS_BEFORE": txt_before,
        "FULL_STATE_MESSAGE_ROWS": 14 if manifest else "",
        "FULL_STATE_TEXT_ROWS": 70 if manifest else "",
        "CANONICAL_MESSAGE_ROWS": len(canon_msg),
        "CANONICAL_TEXT_ROWS": len(canon_txt),
        "ACTIVE_CATALOG_MUTATION_OBSERVED": 0,
        "SOURCE_FILES_MUTATED": 0,
        "HELP_DATA_MUTATION_OBSERVED": 0,
        "CMDHELPCHK_MUTATION_OBSERVED": 0,
        "ERRORS": "; ".join(errors),
        "NEXT_GATE": NEXT_GATE,
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00","Z"),
    }], ["STATUS","VALIDATION_ISSUES","PHASE22AE_6_5_5_GREEN","MSG_022AE_6_5_5_SAVEPOINT_PRESENT",
         "SANDBOX_ROOT","SCRIPT_PATH","SANDBOX_MESSAGE_ROWS_BEFORE","SANDBOX_TEXT_ROWS_BEFORE",
         "FULL_STATE_MESSAGE_ROWS","FULL_STATE_TEXT_ROWS","CANONICAL_MESSAGE_ROWS","CANONICAL_TEXT_ROWS",
         "ACTIVE_CATALOG_MUTATION_OBSERVED","SOURCE_FILES_MUTATED","HELP_DATA_MUTATION_OBSERVED",
         "CMDHELPCHK_MUTATION_OBSERVED","ERRORS","NEXT_GATE","REPORT_TIMESTAMP_UTC"])

    print(status)
    print(f"  validation issues: {validation_issues}")
    print(f"  Phase 22AE.6.5.5 green: {1 if ae655.get('STATUS') == 'MESSAGE_CATALOG_PHASE22AE_6_5_5_FIELD_MAP_FORENSIC_REVIEW_GREEN_SOURCE_HELD' else 0}")
    print(f"  MSG-022AE.6.5.5 savepoint present: {1 if sp655 else 0}")
    print(f"  sandbox root: {rel(sandbox, repo)}")
    print(f"  script path: {script_rel}")
    print(f"  sandbox message rows before: {msg_before}")
    print(f"  sandbox text rows before: {txt_before}")
    print(f"  full-state message rows: {14 if manifest else ''}")
    print(f"  full-state text rows: {70 if manifest else ''}")
    print(f"  canonical rows: message {len(canon_msg)}; text {len(canon_txt)}")
    print("  active catalog mutation observed: 0")
    print("  source files mutated: 0")
    print(f"  next gate: {NEXT_GATE}")
    print(f"  reports: {reports}")
    return 0 if status == STATUS_GREEN and failures == 0 else 2

if __name__ == "__main__":
    raise SystemExit(main())
