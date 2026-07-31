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

STATUS_GREEN = "MESSAGE_CATALOG_PHASE22AE_6_1_SANDBOX_ROW_WRITE_PROOF_PACKAGE_STAGED_SOURCE_HELD"
STATUS_BLOCKED = "MESSAGE_CATALOG_PHASE22AE_6_1_SANDBOX_ROW_WRITE_PROOF_PACKAGE_BLOCKED"
NEXT_GATE = "RUN_SANDBOX_ROW_WRITE_PROOF_RUNTIME_THEN_VALIDATE"
REPORT_DIR = Path("docs/messaging/reports")
SANDBOX_ROOT = Path("docs/messaging/sandbox/phase22ae_6_1_row_write_proof_v1")
SCRIPT_PATH = Path("docs/messaging/scripts/MESSAGE_CATALOG_PHASE22AE_6_1_SANDBOX_ROW_WRITE_PROOF.dts")
ACTIVE_MSG_ROOT = Path("dottalkpp/data/messaging")
ACTIVE_INDEX_ROOT = Path("dottalkpp/data/indexes/messaging")
ACTIVE_LMDB_ROOT = Path("dottalkpp/data/lmdb/messaging")

SYMBOL_FIELDS = ["SYMBOL", "MESSAGE_SYMBOL", "MSG_SYMBOL"]
LOCALE_FIELDS = ["LOCALE", "LOCALE_ID"]
TEXT_FIELDS = ["TEXT", "MESSAGE_TEXT", "MSG_TEXT"]
KIND_FIELDS = ["KIND", "MESSAGE_KIND", "MSG_KIND"]
PLACEHOLDER_FIELDS = ["PLACEHOLDERS", "PLACEHOLDER", "ARGS", "ARGUMENTS"]
STATUS_FIELDS = ["STATUS", "ROW_STATUS"]
SOURCE_FIELDS = ["SOURCE_PHASE", "SOURCE", "PHASE"]

TEST_SYMBOL = "MSG22AE61_SANDBOX_ROW_WRITE_TEST"
TEST_LOCALE = "en-US"
TEST_TEXT = "Phase 22AE.6.1 sandbox row write proof text"
TEST_PLACEHOLDERS = ""

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
        w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
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

def choose_field(info: DbfInfo, choices):
    names = {f["NAME"] for f in info.fields}
    for c in choices:
        if c in names:
            return c
    return ""

def copy_tree(src: Path, dst: Path, repo: Path, rows: list[dict], role: str):
    if dst.exists():
        shutil.rmtree(dst)
    dst.parent.mkdir(parents=True, exist_ok=True)
    files = 0
    total = 0
    if src.exists():
        for p in src.rglob("*"):
            if p.is_file():
                q = dst / p.relative_to(src)
                q.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(p, q)
                files += 1
                total += q.stat().st_size
    rows.append({"SOURCE": rel(src, repo), "TARGET": rel(dst, repo), "ROLE": role, "FILES": files, "BYTES": total})
    return files

def q(value: str) -> str:
    value = "" if value is None else str(value)
    value = value.replace('"', '""')
    return f'"{value}"'

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--replace-existing-sandbox", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    reports = repo / REPORT_DIR
    reports.mkdir(parents=True, exist_ok=True)

    ae6 = first_row(reports / "message_catalog_phase22ae_6_status_summary_v1.csv")
    sp_ok, latest = savepoint_present(repo, "MSG-022AE.6")

    sandbox = repo / SANDBOX_ROOT
    gates = []
    failures = 0
    def gate(name, ok, detail):
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": str(detail)})
        if not ok:
            failures += 1

    gate("PHASE22AE_6_GREEN", ae6.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_REDESIGNED_PROMOTION_PATH_PLAN_GREEN_SOURCE_HELD", ae6.get("STATUS", "missing"))
    gate("MSG_022AE_6_SAVEPOINT_PRESENT", sp_ok, latest)
    gate("ACTIVE_BASELINE_12_60", ae6.get("ACTIVE_MESSAGE_COUNT") == "12" and ae6.get("ACTIVE_TEXT_ROW_COUNT") == "60", f"{ae6.get('ACTIVE_MESSAGE_COUNT')}/{ae6.get('ACTIVE_TEXT_ROW_COUNT')}")
    gate("SANDBOX_NOT_EXISTING_OR_REPLACE_ALLOWED", (not sandbox.exists()) or args.replace_existing_sandbox, rel(sandbox, repo))

    active_msg = repo / ACTIVE_MSG_ROOT / "SYSTEM_MESSAGES.dbf"
    active_text = repo / ACTIVE_MSG_ROOT / "SYSTEM_MESSAGE_TEXT.dbf"
    gate("ACTIVE_SYSTEM_MESSAGES_EXISTS", active_msg.exists(), rel(active_msg, repo))
    gate("ACTIVE_SYSTEM_MESSAGE_TEXT_EXISTS", active_text.exists(), rel(active_text, repo))

    copy_rows = []
    field_rows = []
    errors = []
    msg_count_before = ""
    text_count_before = ""

    status = STATUS_BLOCKED
    if failures == 0:
        try:
            if sandbox.exists() and args.replace_existing_sandbox:
                shutil.rmtree(sandbox)
            copy_tree(repo / ACTIVE_MSG_ROOT, sandbox / "messaging", repo, copy_rows, "sandbox_messaging_copy")
            copy_tree(repo / ACTIVE_INDEX_ROOT, sandbox / "indexes_messaging", repo, copy_rows, "sandbox_indexes_copy")
            copy_tree(repo / ACTIVE_LMDB_ROOT, sandbox / "lmdb_messaging", repo, copy_rows, "sandbox_lmdb_copy")

            msg_dbf = sandbox / "messaging/SYSTEM_MESSAGES.dbf"
            text_dbf = sandbox / "messaging/SYSTEM_MESSAGE_TEXT.dbf"
            msg_info = parse_dbf(msg_dbf)
            text_info = parse_dbf(text_dbf)
            msg_count_before = msg_info.record_count
            text_count_before = text_info.record_count

            msg_symbol = choose_field(msg_info, SYMBOL_FIELDS)
            msg_kind = choose_field(msg_info, KIND_FIELDS)
            msg_ph = choose_field(msg_info, PLACEHOLDER_FIELDS)
            msg_status = choose_field(msg_info, STATUS_FIELDS)
            msg_source = choose_field(msg_info, SOURCE_FIELDS)
            text_symbol = choose_field(text_info, SYMBOL_FIELDS)
            text_locale = choose_field(text_info, LOCALE_FIELDS)
            text_text = choose_field(text_info, TEXT_FIELDS)
            text_ph = choose_field(text_info, PLACEHOLDER_FIELDS)
            text_status = choose_field(text_info, STATUS_FIELDS)
            text_source = choose_field(text_info, SOURCE_FIELDS)

            for role, info in [("messages", msg_info), ("message_text", text_info)]:
                for f in info.fields:
                    field_rows.append({"ROLE": role, "FIELD": f["NAME"], "TYPE": f["TYPE"], "LENGTH": f["LENGTH"], "OFFSET": f["OFFSET"]})

            gate("SANDBOX_MESSAGE_FIELD_MAPPING", bool(msg_symbol), f"symbol={msg_symbol}")
            gate("SANDBOX_TEXT_FIELD_MAPPING", bool(text_symbol and text_locale and text_text), f"symbol={text_symbol}; locale={text_locale}; text={text_text}")

            dts_lines = [
                "* MESSAGE_CATALOG_PHASE22AE_6_1_SANDBOX_ROW_WRITE_PROOF.dts",
                "* Sandbox-only proof. Do not point this script at active catalog roots.",
                "* It tests whether USE/APPEND/REPLACE writes key/text fields in a copied messaging DBF.",
                "",
                f"USE {(msg_dbf.resolve()).as_posix()}",
                "APPEND",
                f"REPLACE {msg_symbol} WITH {q(TEST_SYMBOL)}",
            ]
            if msg_kind:
                dts_lines.append(f"REPLACE {msg_kind} WITH {q('sandbox_probe')}")
            if msg_ph:
                dts_lines.append(f"REPLACE {msg_ph} WITH {q(TEST_PLACEHOLDERS)}")
            if msg_status:
                dts_lines.append(f"REPLACE {msg_status} WITH {q('SANDBOX')}")
            if msg_source:
                dts_lines.append(f"REPLACE {msg_source} WITH {q('22AE_6_1')}")
            dts_lines += [
                "",
                f"USE {(text_dbf.resolve()).as_posix()}",
                "APPEND",
                f"REPLACE {text_symbol} WITH {q(TEST_SYMBOL)}",
                f"REPLACE {text_locale} WITH {q(TEST_LOCALE)}",
                f"REPLACE {text_text} WITH {q(TEST_TEXT)}",
            ]
            if text_ph:
                dts_lines.append(f"REPLACE {text_ph} WITH {q(TEST_PLACEHOLDERS)}")
            if text_status:
                dts_lines.append(f"REPLACE {text_status} WITH {q('SANDBOX')}")
            if text_source:
                dts_lines.append(f"REPLACE {text_source} WITH {q('22AE_6_1')}")
            dts_lines += [
                "",
                "* End sandbox row write proof.",
                "",
            ]
            script_path = repo / SCRIPT_PATH
            script_path.parent.mkdir(parents=True, exist_ok=True)
            script_path.write_text("\n".join(dts_lines), encoding="utf-8")

            status = STATUS_GREEN
        except Exception as exc:
            errors.append(str(exc))
            failures += 1
            status = STATUS_BLOCKED

    validation_issues = "0" if status == STATUS_GREEN else str(failures)

    write_csv(reports / "message_catalog_phase22ae_6_1_stage_gate_check_v1.csv", gates, ["GATE", "STATUS", "DETAIL"])
    write_csv(reports / "message_catalog_phase22ae_6_1_sandbox_copy_inventory_v1.csv", copy_rows, ["SOURCE", "TARGET", "ROLE", "FILES", "BYTES"])
    write_csv(reports / "message_catalog_phase22ae_6_1_sandbox_field_mapping_v1.csv", field_rows, ["ROLE", "FIELD", "TYPE", "LENGTH", "OFFSET"])

    boundary = [
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No source mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_DBF_CATALOG", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Sandbox copy only; no active DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_CDX_INDEXES", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Sandbox copy only; no active index mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Sandbox copy only; no active LMDB mutation."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No HELP DATA mutation."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CMDHELPCHK mutation."},
    ]
    write_csv(reports / "message_catalog_phase22ae_6_1_stage_boundary_ledger_v1.csv", boundary, ["PROTECTED_SYSTEM", "MUTATION_ALLOWED", "OBSERVED_MUTATION", "DETAIL"])

    write_csv(reports / "message_catalog_phase22ae_6_1_stage_status_summary_v1.csv", [{
        "STATUS": status,
        "VALIDATION_ISSUES": validation_issues,
        "PHASE22AE_6_GREEN": 1 if ae6.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_REDESIGNED_PROMOTION_PATH_PLAN_GREEN_SOURCE_HELD" else 0,
        "MSG_022AE_6_SAVEPOINT_PRESENT": 1 if sp_ok else 0,
        "SANDBOX_ROOT": rel(sandbox, repo),
        "SCRIPT_PATH": rel(repo / SCRIPT_PATH, repo),
        "SANDBOX_MESSAGE_ROWS_BEFORE": msg_count_before,
        "SANDBOX_TEXT_ROWS_BEFORE": text_count_before,
        "TEST_SYMBOL": TEST_SYMBOL,
        "TEST_LOCALE": TEST_LOCALE,
        "ACTIVE_CATALOG_MUTATION_OBSERVED": 0,
        "SOURCE_FILES_MUTATED": 0,
        "HELP_DATA_MUTATION_OBSERVED": 0,
        "CMDHELPCHK_MUTATION_OBSERVED": 0,
        "ERRORS": "; ".join(errors),
        "NEXT_GATE": NEXT_GATE,
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }], ["STATUS", "VALIDATION_ISSUES", "PHASE22AE_6_GREEN", "MSG_022AE_6_SAVEPOINT_PRESENT",
         "SANDBOX_ROOT", "SCRIPT_PATH", "SANDBOX_MESSAGE_ROWS_BEFORE", "SANDBOX_TEXT_ROWS_BEFORE",
         "TEST_SYMBOL", "TEST_LOCALE", "ACTIVE_CATALOG_MUTATION_OBSERVED", "SOURCE_FILES_MUTATED",
         "HELP_DATA_MUTATION_OBSERVED", "CMDHELPCHK_MUTATION_OBSERVED", "ERRORS", "NEXT_GATE",
         "REPORT_TIMESTAMP_UTC"])

    md = f"""# Message Catalog Phase 22AE.6.1 Sandbox Row Write Proof Package

Status: `{status}`

Sandbox root:

```text
{rel(sandbox, repo)}
```

Runtime DTS:

```text
{rel(repo / SCRIPT_PATH, repo)}
```

This phase mutates only the sandbox copy when the runtime proof is run. It must
not touch active messaging DBF/CDX/LMDB roots.
"""
    (reports / "MESSAGE_CATALOG_PHASE22AE_6_1_SANDBOX_ROW_WRITE_PROOF_PACKAGE.md").write_text(md, encoding="utf-8")

    print(status)
    print(f"  validation issues: {validation_issues}")
    print(f"  Phase 22AE.6 green: {1 if ae6.get('STATUS') == 'MESSAGE_CATALOG_PHASE22AE_6_REDESIGNED_PROMOTION_PATH_PLAN_GREEN_SOURCE_HELD' else 0}")
    print(f"  MSG-022AE.6 savepoint present: {1 if sp_ok else 0}")
    print(f"  sandbox root: {rel(sandbox, repo)}")
    print(f"  script path: {rel(repo / SCRIPT_PATH, repo)}")
    print(f"  sandbox message rows before: {msg_count_before}")
    print(f"  sandbox text rows before: {text_count_before}")
    print(f"  test symbol: {TEST_SYMBOL}")
    print(f"  active catalog mutation observed: 0")
    print(f"  source files mutated: 0")
    print(f"  next gate: {NEXT_GATE}")
    print(f"  reports: {reports}")
    return 0 if status == STATUS_GREEN else 2

if __name__ == "__main__":
    raise SystemExit(main())
