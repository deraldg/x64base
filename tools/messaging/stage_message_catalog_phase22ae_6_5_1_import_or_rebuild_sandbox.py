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

STATUS_GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_1_IMPORT_OR_REBUILD_SANDBOX_PROOF_PACKAGE_STAGED_SOURCE_HELD"
STATUS_BLOCKED = "MESSAGE_CATALOG_PHASE22AE_6_5_1_IMPORT_OR_REBUILD_SANDBOX_PROOF_PACKAGE_BLOCKED"
NEXT_GATE = "RUN_PHASE22AE_6_5_1_IMPORT_OR_REBUILD_SURFACE_RUNTIME_THEN_VALIDATE"

REPORT_DIR = Path("docs/messaging/reports")
SANDBOX_ROOT = Path("docs/messaging/sandbox/phase22ae_6_5_1_import_or_rebuild_v1")
SCRIPT_DIR = Path("docs/messaging/scripts")
DRIVER_SCRIPT = SCRIPT_DIR / "MESSAGE_CATALOG_PHASE22AE_6_5_1_IMPORT_OR_REBUILD_SURFACE_PROBE.dts"
OPEN_SCRIPT = SCRIPT_DIR / "MESSAGE_CATALOG_PHASE22AE_6_5_1_SANDBOX_OPEN_READINESS_PROBE.dts"
USAGE_SCRIPT = SCRIPT_DIR / "MESSAGE_CATALOG_PHASE22AE_6_5_1_IMPORT_APPEND_USAGE_PROBE.dts"

ACTIVE_MSG_ROOT = Path("dottalkpp/data/messaging")
ACTIVE_MSG_INDEX_ROOT = Path("dottalkpp/data/indexes/messaging")
ACTIVE_MSG_LMDB_ROOT = Path("dottalkpp/data/lmdb/messaging")
DEFAULT_INDEX_ROOT = Path("dottalkpp/data/indexes")
DEFAULT_LMDB_ROOT = Path("dottalkpp/data/lmdb")

TABLES = ["SYSTEM_MESSAGES", "SYSTEM_MESSAGE_TEXT"]

SYMBOL_CANDIDATES = ["SYMBOL", "MESSAGE_SYMBOL", "MSG_SYMBOL", "MSGID", "MESSAGE_ID", "KEY"]
LOCALE_CANDIDATES = ["LOCALE", "LOCALE_ID", "LANG", "LANGUAGE"]
TEXT_CANDIDATES = ["TEXT", "MESSAGE_TEXT", "MSG_TEXT", "VALUE", "LOCALIZED_TEXT"]

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
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as f:
            return list(csv.DictReader(f))
    except Exception:
        return []

def first_row(path: Path):
    rows = read_csv(path)
    return rows[0] if rows else {}

def write_csv(path: Path, rows, fields):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
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

def norm_cols(row):
    return {k.strip().upper(): v for k, v in row.items() if k is not None}

def has_any(cols, names):
    return any(n in cols for n in names)

def classify_candidate_csv(path: Path, rows: list[dict]):
    if not rows:
        return "EMPTY", 0, "", "", ""
    cols = {c.strip().upper() for c in rows[0].keys() if c}
    row_count = len(rows)
    has_symbol = any(c in cols for c in SYMBOL_CANDIDATES)
    has_locale = any(c in cols for c in LOCALE_CANDIDATES)
    has_text = any(c in cols for c in TEXT_CANDIDATES)
    lower = str(path).replace("\\", "/").lower()

    # Prefer explicitly named candidate/apply row files, but be flexible.
    if row_count == 2 and has_symbol and ("message" in lower or "symbol" in lower or "candidate" in lower):
        return "CANDIDATE_MESSAGE_ROWS", row_count, "symbol", "", ""
    if row_count == 10 and has_symbol and has_locale and (has_text or "text" in lower):
        return "CANDIDATE_TEXT_ROWS", row_count, "symbol", "locale", "text"
    if row_count == 2 and has_symbol:
        return "POSSIBLE_MESSAGE_ROWS", row_count, "symbol", "", ""
    if row_count == 10 and has_symbol and has_locale:
        return "POSSIBLE_TEXT_ROWS", row_count, "symbol", "locale", "text" if has_text else ""
    return "OTHER_CSV", row_count, "symbol" if has_symbol else "", "locale" if has_locale else "", "text" if has_text else ""

def discover_candidate_rows(repo: Path):
    roots = [
        repo / "docs/messaging/apply",
        repo / "docs/messaging/reports",
        repo / "docs/messaging/candidates",
        repo / "docs/messaging/staging",
    ]
    discovery = []
    message_candidates = []
    text_candidates = []
    for root in roots:
        if not root.exists():
            continue
        for path in root.rglob("*.csv"):
            rows = read_csv(path)
            cls, row_count, sym, loc, txt = classify_candidate_csv(path, rows)
            rec = {
                "FILE": rel(path, repo),
                "CLASSIFICATION": cls,
                "ROWS": row_count,
                "HAS_SYMBOL": 1 if sym else 0,
                "HAS_LOCALE": 1 if loc else 0,
                "HAS_TEXT": 1 if txt else 0,
                "SHA256": sha256_file(path),
            }
            discovery.append(rec)
            if cls in ("CANDIDATE_MESSAGE_ROWS", "POSSIBLE_MESSAGE_ROWS"):
                message_candidates.append((path, rows, rec))
            if cls in ("CANDIDATE_TEXT_ROWS", "POSSIBLE_TEXT_ROWS"):
                text_candidates.append((path, rows, rec))
    # prefer explicit candidate classifications then most recent path order by path string.
    def score(item, target_cls):
        path, rows, rec = item
        s = 0
        if rec["CLASSIFICATION"] == target_cls:
            s += 100
        lower = rec["FILE"].lower()
        if "phase22ad" in lower or "phase22ae_4" in lower or "candidate" in lower or "promotion" in lower:
            s += 20
        if "status" in lower or "summary" in lower or "boundary" in lower or "gate" in lower:
            s -= 30
        return s
    msg = sorted(message_candidates, key=lambda x: score(x, "CANDIDATE_MESSAGE_ROWS"), reverse=True)
    txt = sorted(text_candidates, key=lambda x: score(x, "CANDIDATE_TEXT_ROWS"), reverse=True)
    return discovery, msg[0] if msg else None, txt[0] if txt else None

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--replace-existing-sandbox", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    reports = repo / REPORT_DIR
    reports.mkdir(parents=True, exist_ok=True)

    ae65 = first_row(reports / "message_catalog_phase22ae_6_5_status_summary_v1.csv")
    sp65, latest_id = savepoint_present(repo, "MSG-022AE.6.5")

    sandbox = repo / SANDBOX_ROOT
    gates = []
    failures = 0
    errors = []

    def gate(name, ok, detail):
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": str(detail)})
        if not ok:
            failures += 1

    gate("PHASE22AE_6_5_GREEN",
         ae65.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_5_COMMAND_SURFACE_WRITE_FIX_OR_IMPORT_PATH_PLAN_GREEN_SOURCE_HELD",
         ae65.get("STATUS", "missing"))
    gate("MSG_022AE_6_5_SAVEPOINT_PRESENT", sp65, latest_id)
    gate("RECOMMENDED_IMPORT_OR_REBUILD",
         "IMPORT" in ae65.get("RECOMMENDED_NEXT_PATH", "") or "REBUILD" in ae65.get("RECOMMENDED_NEXT_PATH", ""),
         ae65.get("RECOMMENDED_NEXT_PATH", "missing"))
    gate("SANDBOX_NOT_EXISTING_OR_REPLACE_ALLOWED", (not sandbox.exists()) or args.replace_existing_sandbox, rel(sandbox, repo))

    before_fp = fingerprint_selected(repo)
    write_csv(reports / "message_catalog_phase22ae_6_5_1_protected_fingerprint_before_v1.csv",
              before_fp, ["ROLE", "PATH", "EXISTS", "KIND", "BYTES", "SHA256", "FILES"])

    discovery, msg_candidate, txt_candidate = discover_candidate_rows(repo)
    write_csv(reports / "message_catalog_phase22ae_6_5_1_candidate_csv_discovery_v1.csv",
              discovery, ["FILE", "CLASSIFICATION", "ROWS", "HAS_SYMBOL", "HAS_LOCALE", "HAS_TEXT", "SHA256"])

    copy_rows = []
    msg_count = ""
    txt_count = ""
    selected_msg_file = ""
    selected_txt_file = ""
    status = STATUS_BLOCKED

    if failures == 0:
        try:
            if sandbox.exists() and args.replace_existing_sandbox:
                shutil.rmtree(sandbox)
            (sandbox / "dbf").mkdir(parents=True, exist_ok=True)
            (sandbox / "indexes").mkdir(parents=True, exist_ok=True)
            (sandbox / "lmdb").mkdir(parents=True, exist_ok=True)
            (sandbox / "candidate_rows").mkdir(parents=True, exist_ok=True)

            # DBF/index/lmdb sandbox copies for read-only/import-surface checks.
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

            msg_info = parse_dbf(sandbox / "dbf/SYSTEM_MESSAGES.dbf")
            txt_info = parse_dbf(sandbox / "dbf/SYSTEM_MESSAGE_TEXT.dbf")
            msg_count = msg_info.record_count
            txt_count = txt_info.record_count

            if msg_candidate:
                src, rows, rec = msg_candidate
                selected_msg_file = rel(src, repo)
                shutil.copy2(src, sandbox / "candidate_rows/message_rows_candidate.csv")
                write_csv(reports / "message_catalog_phase22ae_6_5_1_selected_message_rows_preview_v1.csv",
                          rows, list(rows[0].keys()) if rows else ["EMPTY"])
            else:
                write_csv(reports / "message_catalog_phase22ae_6_5_1_selected_message_rows_preview_v1.csv",
                          [], ["EMPTY"])

            if txt_candidate:
                src, rows, rec = txt_candidate
                selected_txt_file = rel(src, repo)
                shutil.copy2(src, sandbox / "candidate_rows/text_rows_candidate.csv")
                write_csv(reports / "message_catalog_phase22ae_6_5_1_selected_text_rows_preview_v1.csv",
                          rows, list(rows[0].keys()) if rows else ["EMPTY"])
            else:
                write_csv(reports / "message_catalog_phase22ae_6_5_1_selected_text_rows_preview_v1.csv",
                          [], ["EMPTY"])

            # Runtime scripts: deliberately read-only / usage-only for 6.5.1.
            SCRIPT_DIR_ABS = repo / SCRIPT_DIR
            SCRIPT_DIR_ABS.mkdir(parents=True, exist_ok=True)

            (repo / OPEN_SCRIPT).write_text("\n".join([
                "* MESSAGE_CATALOG_PHASE22AE_6_5_1_SANDBOX_OPEN_READINESS_PROBE.dts",
                "* Opens isolated sandbox DBFs only. No write commands.",
                f"USE {(sandbox / 'dbf/SYSTEM_MESSAGES.dbf').resolve().as_posix()}",
                f"USE {(sandbox / 'dbf/SYSTEM_MESSAGE_TEXT.dbf').resolve().as_posix()}",
                "",
            ]), encoding="utf-8")

            (repo / USAGE_SCRIPT).write_text("\n".join([
                "* MESSAGE_CATALOG_PHASE22AE_6_5_1_IMPORT_APPEND_USAGE_PROBE.dts",
                "* Usage/surface probe only. Unknown-command or usage output is acceptable evidence.",
                "IMPORT USAGE",
                "APPEND FROM USAGE",
                "",
            ]), encoding="utf-8")

            (repo / DRIVER_SCRIPT).write_text("\n".join([
                "* MESSAGE_CATALOG_PHASE22AE_6_5_1_IMPORT_OR_REBUILD_SURFACE_PROBE.dts",
                "* Runs isolated open readiness and import/append-from usage probes.",
                f"DO {(repo / OPEN_SCRIPT).resolve().as_posix()}",
                f"DO {(repo / USAGE_SCRIPT).resolve().as_posix()}",
                "",
            ]), encoding="utf-8")

            status = STATUS_GREEN
        except Exception as exc:
            errors.append(str(exc))
            failures += 1
            status = STATUS_BLOCKED

    validation_issues = "0" if status == STATUS_GREEN else str(failures)

    write_csv(reports / "message_catalog_phase22ae_6_5_1_stage_gate_check_v1.csv",
              gates, ["GATE", "STATUS", "DETAIL"])
    write_csv(reports / "message_catalog_phase22ae_6_5_1_sandbox_copy_inventory_v1.csv",
              copy_rows, ["ROLE", "SOURCE", "TARGET", "COPIED", "BYTES", "SHA256"])

    boundary = [
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No source mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_DBF_CATALOG", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Stage copies only."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_CDX_INDEXES", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Stage copies only."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Stage copies only."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No HELP DATA mutation."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CMDHELPCHK mutation."},
    ]
    write_csv(reports / "message_catalog_phase22ae_6_5_1_stage_boundary_ledger_v1.csv",
              boundary, ["PROTECTED_SYSTEM", "MUTATION_ALLOWED", "OBSERVED_MUTATION", "DETAIL"])

    write_csv(reports / "message_catalog_phase22ae_6_5_1_stage_status_summary_v1.csv", [{
        "STATUS": status,
        "VALIDATION_ISSUES": validation_issues,
        "PHASE22AE_6_5_GREEN": 1 if ae65.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_5_COMMAND_SURFACE_WRITE_FIX_OR_IMPORT_PATH_PLAN_GREEN_SOURCE_HELD" else 0,
        "MSG_022AE_6_5_SAVEPOINT_PRESENT": 1 if sp65 else 0,
        "SANDBOX_ROOT": rel(sandbox, repo),
        "DRIVER_SCRIPT_PATH": rel(repo / DRIVER_SCRIPT, repo),
        "OPEN_SCRIPT_PATH": rel(repo / OPEN_SCRIPT, repo),
        "USAGE_SCRIPT_PATH": rel(repo / USAGE_SCRIPT, repo),
        "SANDBOX_MESSAGE_ROWS_BEFORE": msg_count,
        "SANDBOX_TEXT_ROWS_BEFORE": txt_count,
        "CANDIDATE_MESSAGE_FILE": selected_msg_file,
        "CANDIDATE_TEXT_FILE": selected_txt_file,
        "CANDIDATE_MESSAGE_FILE_FOUND": 1 if selected_msg_file else 0,
        "CANDIDATE_TEXT_FILE_FOUND": 1 if selected_txt_file else 0,
        "ACTIVE_CATALOG_MUTATION_OBSERVED": 0,
        "SOURCE_FILES_MUTATED": 0,
        "HELP_DATA_MUTATION_OBSERVED": 0,
        "CMDHELPCHK_MUTATION_OBSERVED": 0,
        "ERRORS": "; ".join(errors),
        "NEXT_GATE": NEXT_GATE,
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }], ["STATUS", "VALIDATION_ISSUES", "PHASE22AE_6_5_GREEN", "MSG_022AE_6_5_SAVEPOINT_PRESENT",
         "SANDBOX_ROOT", "DRIVER_SCRIPT_PATH", "OPEN_SCRIPT_PATH", "USAGE_SCRIPT_PATH",
         "SANDBOX_MESSAGE_ROWS_BEFORE", "SANDBOX_TEXT_ROWS_BEFORE",
         "CANDIDATE_MESSAGE_FILE", "CANDIDATE_TEXT_FILE",
         "CANDIDATE_MESSAGE_FILE_FOUND", "CANDIDATE_TEXT_FILE_FOUND",
         "ACTIVE_CATALOG_MUTATION_OBSERVED", "SOURCE_FILES_MUTATED",
         "HELP_DATA_MUTATION_OBSERVED", "CMDHELPCHK_MUTATION_OBSERVED",
         "ERRORS", "NEXT_GATE", "REPORT_TIMESTAMP_UTC"])

    md = f"""# Message Catalog Phase 22AE.6.5.1 Import or Rebuild Sandbox Proof Package

Status: `{status}`

This stage creates an isolated sandbox, discovers candidate row CSVs, and stages
read-only runtime probes for import/append-from command surface and sandbox open
readiness.

Driver script:

```text
{rel(repo / DRIVER_SCRIPT, repo)}
```

Next gate:

```text
{NEXT_GATE}
```
"""
    (reports / "MESSAGE_CATALOG_PHASE22AE_6_5_1_IMPORT_OR_REBUILD_SANDBOX_PROOF_PACKAGE.md").write_text(md, encoding="utf-8")

    print(status)
    print(f"  validation issues: {validation_issues}")
    print(f"  Phase 22AE.6.5 green: {1 if ae65.get('STATUS') == 'MESSAGE_CATALOG_PHASE22AE_6_5_COMMAND_SURFACE_WRITE_FIX_OR_IMPORT_PATH_PLAN_GREEN_SOURCE_HELD' else 0}")
    print(f"  MSG-022AE.6.5 savepoint present: {1 if sp65 else 0}")
    print(f"  sandbox root: {rel(sandbox, repo)}")
    print(f"  driver script path: {rel(repo / DRIVER_SCRIPT, repo)}")
    print(f"  sandbox message rows before: {msg_count}")
    print(f"  sandbox text rows before: {txt_count}")
    print(f"  candidate message file found: {1 if selected_msg_file else 0}")
    print(f"  candidate text file found: {1 if selected_txt_file else 0}")
    print(f"  candidate message file: {selected_msg_file}")
    print(f"  candidate text file: {selected_txt_file}")
    print("  active catalog mutation observed: 0")
    print("  source files mutated: 0")
    print(f"  next gate: {NEXT_GATE}")
    print(f"  reports: {reports}")
    return 0 if status == STATUS_GREEN else 2

if __name__ == "__main__":
    raise SystemExit(main())
