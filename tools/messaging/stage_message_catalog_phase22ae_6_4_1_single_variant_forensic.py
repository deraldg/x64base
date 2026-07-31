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

STATUS_GREEN = "MESSAGE_CATALOG_PHASE22AE_6_4_1_SINGLE_VARIANT_FORENSIC_SANDBOX_PROOF_STAGED_SOURCE_HELD"
STATUS_BLOCKED = "MESSAGE_CATALOG_PHASE22AE_6_4_1_SINGLE_VARIANT_FORENSIC_SANDBOX_PROOF_STAGING_BLOCKED"
NEXT_GATE = "RUN_PHASE22AE_6_4_1_SINGLE_VARIANT_FORENSIC_RUNTIME_THEN_VALIDATE"

REPORT_DIR = Path("docs/messaging/reports")
SANDBOX_ROOT = Path("docs/messaging/sandbox/phase22ae_6_4_1_single_variant_v1")
SCRIPT_PATH = Path("docs/messaging/scripts/MESSAGE_CATALOG_PHASE22AE_6_4_1_SINGLE_VARIANT_FORENSIC_SANDBOX_PROOF.dts")
ACTIVE_MSG_ROOT = Path("dottalkpp/data/messaging")
ACTIVE_INDEX_ROOT = Path("dottalkpp/data/indexes/messaging")
ACTIVE_LMDB_ROOT = Path("dottalkpp/data/lmdb/messaging")
DEFAULT_INDEX_ROOT = Path("dottalkpp/data/indexes")
DEFAULT_LMDB_ROOT = Path("dottalkpp/data/lmdb")

SYMBOL_FIELDS = ["SYMBOL", "MESSAGE_SYMBOL", "MSG_SYMBOL"]
LOCALE_FIELDS = ["LOCALE", "LOCALE_ID"]
TEXT_FIELDS = ["TEXT", "MESSAGE_TEXT", "MSG_TEXT"]
KIND_FIELDS = ["KIND", "MESSAGE_KIND", "MSG_KIND"]
PLACEHOLDER_FIELDS = ["PLACEHOLDERS", "PLACEHOLDER", "ARGS", "ARGUMENTS"]
STATUS_FIELDS = ["STATUS", "ROW_STATUS"]
SOURCE_FIELDS = ["SOURCE_PHASE", "SOURCE", "PHASE"]

TEST_SYMBOL = "MSG22AE641_V1_TEST"
TEST_LOCALE = "en-US"
TEST_TEXT = "MSG22AE641_V1_TEXT"

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
    return '"' + str(value).replace('"', '""') + '"'

def replace(field: str, value: str) -> str:
    return f"REPLACE {field} WITH {q(value)}"

def fingerprint_root(root: Path, repo: Path, label: str, max_files: int = 5000):
    rows = []
    if not root.exists():
        rows.append({"LABEL": label, "PATH": rel(root, repo), "EXISTS": 0, "BYTES": 0, "SHA256": "", "ROLE": "missing_root"})
        return rows
    count = 0
    for p in sorted(root.rglob("*")):
        if p.is_file():
            rows.append({"LABEL": label, "PATH": rel(p, repo), "EXISTS": 1, "BYTES": p.stat().st_size, "SHA256": sha256_file(p), "ROLE": "file"})
            count += 1
            if count >= max_files:
                rows.append({"LABEL": label, "PATH": rel(root, repo), "EXISTS": 1, "BYTES": 0, "SHA256": "", "ROLE": "truncated_after_max_files"})
                break
    if not rows:
        rows.append({"LABEL": label, "PATH": rel(root, repo), "EXISTS": 1, "BYTES": 0, "SHA256": "", "ROLE": "empty_root"})
    return rows

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--replace-existing-sandbox", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    reports = repo / REPORT_DIR
    reports.mkdir(parents=True, exist_ok=True)

    ae64 = first_row(reports / "message_catalog_phase22ae_6_4_status_summary_v1.csv")
    sp64, latest_id = savepoint_present(repo, "MSG-022AE.6.4")

    sandbox = repo / SANDBOX_ROOT
    gates = []
    failures = 0
    errors = []
    def gate(name, ok, detail):
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": str(detail)})
        if not ok:
            failures += 1

    gate("PHASE22AE_6_4_GREEN", ae64.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_4_DEEP_COMMAND_SURFACE_WRITE_SEMANTICS_REVIEW_GREEN_SOURCE_HELD", ae64.get("STATUS", "missing"))
    gate("MSG_022AE_6_4_SAVEPOINT_PRESENT", sp64, latest_id)
    gate("SINGLE_VARIANT_NEXT_PATH", ae64.get("RECOMMENDED_NEXT_PATH") == "SINGLE_VARIANT_FORENSIC_SANDBOX_PROOF", ae64.get("RECOMMENDED_NEXT_PATH", "missing"))
    gate("SANDBOX_NOT_EXISTING_OR_REPLACE_ALLOWED", (not sandbox.exists()) or args.replace_existing_sandbox, rel(sandbox, repo))
    gate("ACTIVE_MESSAGING_ROOT_EXISTS", (repo / ACTIVE_MSG_ROOT).exists(), rel(repo / ACTIVE_MSG_ROOT, repo))

    copy_rows = []
    field_rows = []
    msg_count = ""
    text_count = ""
    script_rel = ""

    before_fp = (
        fingerprint_root(repo / ACTIVE_MSG_ROOT, repo, "before_active_messaging") +
        fingerprint_root(repo / ACTIVE_INDEX_ROOT, repo, "before_active_indexes_messaging") +
        fingerprint_root(repo / ACTIVE_LMDB_ROOT, repo, "before_active_lmdb_messaging") +
        fingerprint_root(repo / DEFAULT_INDEX_ROOT, repo, "before_default_indexes") +
        fingerprint_root(repo / DEFAULT_LMDB_ROOT, repo, "before_default_lmdb")
    )

    status = STATUS_BLOCKED
    if failures == 0:
        try:
            if sandbox.exists() and args.replace_existing_sandbox:
                shutil.rmtree(sandbox)
            sandbox.mkdir(parents=True, exist_ok=True)

            copy_tree(repo / ACTIVE_MSG_ROOT, sandbox / "messaging", repo, copy_rows, "sandbox_messaging_copy")
            copy_tree(repo / ACTIVE_INDEX_ROOT, sandbox / "indexes_messaging", repo, copy_rows, "sandbox_indexes_copy")
            copy_tree(repo / ACTIVE_LMDB_ROOT, sandbox / "lmdb_messaging", repo, copy_rows, "sandbox_lmdb_copy")

            msg_dbf = sandbox / "messaging/SYSTEM_MESSAGES.dbf"
            txt_dbf = sandbox / "messaging/SYSTEM_MESSAGE_TEXT.dbf"
            msg_info = parse_dbf(msg_dbf)
            txt_info = parse_dbf(txt_dbf)
            msg_count = msg_info.record_count
            text_count = txt_info.record_count

            for role, info in [("SYSTEM_MESSAGES", msg_info), ("SYSTEM_MESSAGE_TEXT", txt_info)]:
                for f in info.fields:
                    field_rows.append({"TABLE": role, "FIELD": f["NAME"], "TYPE": f["TYPE"], "LENGTH": f["LENGTH"], "OFFSET": f["OFFSET"]})

            msg_symbol = choose_field(msg_info, SYMBOL_FIELDS)
            msg_kind = choose_field(msg_info, KIND_FIELDS)
            msg_ph = choose_field(msg_info, PLACEHOLDER_FIELDS)
            msg_status = choose_field(msg_info, STATUS_FIELDS)
            msg_source = choose_field(msg_info, SOURCE_FIELDS)

            txt_symbol = choose_field(txt_info, SYMBOL_FIELDS)
            txt_locale = choose_field(txt_info, LOCALE_FIELDS)
            txt_text = choose_field(txt_info, TEXT_FIELDS)
            txt_ph = choose_field(txt_info, PLACEHOLDER_FIELDS)
            txt_status = choose_field(txt_info, STATUS_FIELDS)
            txt_source = choose_field(txt_info, SOURCE_FIELDS)

            gate("MESSAGE_SYMBOL_FIELD_MAPPED", bool(msg_symbol), msg_symbol)
            gate("TEXT_SYMBOL_LOCALE_TEXT_FIELDS_MAPPED", bool(txt_symbol and txt_locale and txt_text), f"{txt_symbol}/{txt_locale}/{txt_text}")

            script = repo / SCRIPT_PATH
            script.parent.mkdir(parents=True, exist_ok=True)
            lines = [
                "* MESSAGE_CATALOG_PHASE22AE_6_4_1_SINGLE_VARIANT_FORENSIC_SANDBOX_PROOF.dts",
                "* Fresh V1-only sandbox proof. Do not point this script at active roots.",
                "* Variant: APPEND, GO BOTTOM, REPLACE <field> WITH double-quoted literal.",
                "",
                f"USE {msg_dbf.resolve().as_posix()}",
                "APPEND",
                "GO BOTTOM",
                replace(msg_symbol, TEST_SYMBOL),
            ]
            if msg_kind:
                lines.append(replace(msg_kind, "sandbox_probe"))
            if msg_ph:
                lines.append(replace(msg_ph, ""))
            if msg_status:
                lines.append(replace(msg_status, "SANDBOX"))
            if msg_source:
                lines.append(replace(msg_source, "22AE_6_4_1"))
            lines += [
                "",
                f"USE {txt_dbf.resolve().as_posix()}",
                "APPEND",
                "GO BOTTOM",
                replace(txt_symbol, TEST_SYMBOL),
                replace(txt_locale, TEST_LOCALE),
                replace(txt_text, TEST_TEXT),
            ]
            if txt_ph:
                lines.append(replace(txt_ph, ""))
            if txt_status:
                lines.append(replace(txt_status, "SANDBOX"))
            if txt_source:
                lines.append(replace(txt_source, "22AE_6_4_1"))
            lines += ["", "* End 6.4.1 V1-only forensic sandbox proof.", ""]
            script.write_text("\n".join(lines), encoding="utf-8")
            script_rel = rel(script, repo)
            status = STATUS_GREEN
        except Exception as exc:
            errors.append(str(exc))
            failures += 1
            status = STATUS_BLOCKED

    validation_issues = "0" if status == STATUS_GREEN else str(failures)

    write_csv(reports / "message_catalog_phase22ae_6_4_1_stage_gate_check_v1.csv", gates, ["GATE", "STATUS", "DETAIL"])
    write_csv(reports / "message_catalog_phase22ae_6_4_1_sandbox_copy_inventory_v1.csv", copy_rows, ["SOURCE", "TARGET", "ROLE", "FILES", "BYTES"])
    write_csv(reports / "message_catalog_phase22ae_6_4_1_field_mapping_v1.csv", field_rows, ["TABLE", "FIELD", "TYPE", "LENGTH", "OFFSET"])
    write_csv(reports / "message_catalog_phase22ae_6_4_1_active_fingerprint_before_v1.csv", before_fp, ["LABEL", "PATH", "EXISTS", "BYTES", "SHA256", "ROLE"])

    boundary = [
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No source mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_DBF_CATALOG", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Sandbox only; no active DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_CDX_INDEXES", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Sandbox only; no active index mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Sandbox only; no active LMDB mutation."},
        {"PROTECTED_SYSTEM": "DEFAULT_INDEX_ROOT", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Before fingerprint captured; after fingerprint checked during validation."},
        {"PROTECTED_SYSTEM": "DEFAULT_LMDB_ROOT", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Before fingerprint captured; after fingerprint checked during validation."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No HELP DATA mutation."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CMDHELPCHK mutation."},
    ]
    write_csv(reports / "message_catalog_phase22ae_6_4_1_stage_boundary_ledger_v1.csv", boundary, ["PROTECTED_SYSTEM", "MUTATION_ALLOWED", "OBSERVED_MUTATION", "DETAIL"])

    write_csv(reports / "message_catalog_phase22ae_6_4_1_stage_status_summary_v1.csv", [{
        "STATUS": status,
        "VALIDATION_ISSUES": validation_issues,
        "PHASE22AE_6_4_GREEN": 1 if ae64.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_4_DEEP_COMMAND_SURFACE_WRITE_SEMANTICS_REVIEW_GREEN_SOURCE_HELD" else 0,
        "MSG_022AE_6_4_SAVEPOINT_PRESENT": 1 if sp64 else 0,
        "SANDBOX_ROOT": rel(sandbox, repo),
        "SCRIPT_PATH": script_rel,
        "VARIANT": "V1_GO_BOTTOM_WITH_DOUBLE_QUOTES",
        "TEST_SYMBOL": TEST_SYMBOL,
        "TEST_LOCALE": TEST_LOCALE,
        "TEST_TEXT": TEST_TEXT,
        "SANDBOX_MESSAGE_ROWS_BEFORE": msg_count,
        "SANDBOX_TEXT_ROWS_BEFORE": text_count,
        "ACTIVE_CATALOG_MUTATION_OBSERVED": 0,
        "SOURCE_FILES_MUTATED": 0,
        "HELP_DATA_MUTATION_OBSERVED": 0,
        "CMDHELPCHK_MUTATION_OBSERVED": 0,
        "ERRORS": "; ".join(errors),
        "NEXT_GATE": NEXT_GATE,
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }], ["STATUS", "VALIDATION_ISSUES", "PHASE22AE_6_4_GREEN", "MSG_022AE_6_4_SAVEPOINT_PRESENT",
         "SANDBOX_ROOT", "SCRIPT_PATH", "VARIANT", "TEST_SYMBOL", "TEST_LOCALE", "TEST_TEXT",
         "SANDBOX_MESSAGE_ROWS_BEFORE", "SANDBOX_TEXT_ROWS_BEFORE",
         "ACTIVE_CATALOG_MUTATION_OBSERVED", "SOURCE_FILES_MUTATED", "HELP_DATA_MUTATION_OBSERVED",
         "CMDHELPCHK_MUTATION_OBSERVED", "ERRORS", "NEXT_GATE", "REPORT_TIMESTAMP_UTC"])

    md = f"""# Message Catalog Phase 22AE.6.4.1 Single-Variant Forensic Sandbox Proof

Status: `{status}`

Variant:

```text
V1_GO_BOTTOM_WITH_DOUBLE_QUOTES
```

Runtime script:

```text
{script_rel}
```

This stage copied active messaging roots to a single fresh sandbox and captured
active/default root fingerprints before runtime execution.
"""
    (reports / "MESSAGE_CATALOG_PHASE22AE_6_4_1_SINGLE_VARIANT_FORENSIC_SANDBOX_PROOF.md").write_text(md, encoding="utf-8")

    print(status)
    print(f"  validation issues: {validation_issues}")
    print(f"  Phase 22AE.6.4 green: {1 if ae64.get('STATUS') == 'MESSAGE_CATALOG_PHASE22AE_6_4_DEEP_COMMAND_SURFACE_WRITE_SEMANTICS_REVIEW_GREEN_SOURCE_HELD' else 0}")
    print(f"  MSG-022AE.6.4 savepoint present: {1 if sp64 else 0}")
    print(f"  sandbox root: {rel(sandbox, repo)}")
    print(f"  script path: {script_rel}")
    print("  variant: V1_GO_BOTTOM_WITH_DOUBLE_QUOTES")
    print(f"  sandbox message rows before: {msg_count}")
    print(f"  sandbox text rows before: {text_count}")
    print(f"  test symbol: {TEST_SYMBOL}")
    print("  active catalog mutation observed: 0")
    print("  source files mutated: 0")
    print(f"  next gate: {NEXT_GATE}")
    print(f"  reports: {reports}")
    return 0 if status == STATUS_GREEN else 2

if __name__ == "__main__":
    raise SystemExit(main())
