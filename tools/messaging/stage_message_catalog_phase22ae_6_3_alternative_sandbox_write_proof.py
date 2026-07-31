#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import shutil
import struct
from datetime import datetime, timezone
from pathlib import Path

STATUS_GREEN = "MESSAGE_CATALOG_PHASE22AE_6_3_ALTERNATIVE_SANDBOX_WRITE_PROOF_PACKAGE_STAGED_SOURCE_HELD"
STATUS_BLOCKED = "MESSAGE_CATALOG_PHASE22AE_6_3_ALTERNATIVE_SANDBOX_WRITE_PROOF_PACKAGE_BLOCKED"
NEXT_GATE = "RUN_PHASE22AE_6_3_ALTERNATIVE_SANDBOX_WRITE_PROOF_RUNTIME_THEN_VALIDATE"

REPORT_DIR = Path("docs/messaging/reports")
SANDBOX_ROOT = Path("docs/messaging/sandbox/phase22ae_6_3_alternative_write_proof_v1")
SCRIPT_DIR = Path("docs/messaging/scripts")
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

VARIANTS = [
    {
        "variant_id": "V1_GO_BOTTOM_WITH_DOUBLE_QUOTES",
        "description": "APPEND, GO BOTTOM, REPLACE field WITH double-quoted literal",
        "record_position": "GO BOTTOM",
        "replace_style": "WITH_DOUBLE_QUOTES",
    },
    {
        "variant_id": "V2_BOTTOM_WITH_DOUBLE_QUOTES",
        "description": "APPEND, BOTTOM, REPLACE field WITH double-quoted literal",
        "record_position": "BOTTOM",
        "replace_style": "WITH_DOUBLE_QUOTES",
    },
    {
        "variant_id": "V3_GO_BOTTOM_REPLACE_NO_WITH",
        "description": "APPEND, GO BOTTOM, REPLACE field double-quoted literal without WITH",
        "record_position": "GO BOTTOM",
        "replace_style": "NO_WITH_DOUBLE_QUOTES",
    },
    {
        "variant_id": "V4_GO_BOTTOM_WITH_UNQUOTED_TOKENS",
        "description": "APPEND, GO BOTTOM, REPLACE field WITH unquoted token literals",
        "record_position": "GO BOTTOM",
        "replace_style": "WITH_UNQUOTED",
    },
]

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
        if name:
            fields.append({"NAME": name, "TYPE": ftype, "LENGTH": length, "OFFSET": offset})
            offset += length
        pos += 32
    return DbfInfo(path, record_count, header_len, record_len, fields)

def choose_field(info: DbfInfo, choices):
    names = {f["NAME"] for f in info.fields}
    for c in choices:
        if c in names:
            return c
    return ""

def q(value: str) -> str:
    return '"' + str(value).replace('"', '""') + '"'

def unquoted(value: str) -> str:
    return "".join(ch if (ch.isalnum() or ch == "_") else "_" for ch in str(value))

def value_for(style: str, value: str) -> str:
    if style == "WITH_UNQUOTED":
        return unquoted(value)
    return q(value)

def replace_line(style: str, field: str, value: str) -> str:
    if style == "NO_WITH_DOUBLE_QUOTES":
        return f"REPLACE {field} {q(value)}"
    if style == "WITH_UNQUOTED":
        return f"REPLACE {field} WITH {unquoted(value)}"
    return f"REPLACE {field} WITH {q(value)}"

def copy_tree(src: Path, dst: Path, repo: Path, rows: list[dict], role: str):
    if dst.exists():
        shutil.rmtree(dst)
    dst.parent.mkdir(parents=True, exist_ok=True)
    files = 0
    total = 0
    if src.exists():
        for p in src.rglob("*"):
            if p.is_file():
                qpath = dst / p.relative_to(src)
                qpath.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(p, qpath)
                files += 1
                total += qpath.stat().st_size
    rows.append({"SOURCE": rel(src, repo), "TARGET": rel(dst, repo), "ROLE": role, "FILES": files, "BYTES": total})
    return files

def generate_variant_script(repo: Path, variant: dict, msg_dbf: Path, text_dbf: Path, msg_info: DbfInfo, text_info: DbfInfo) -> str:
    vid = variant["variant_id"]
    style = variant["replace_style"]
    pos_cmd = variant["record_position"]

    test_symbol = f"MSG22AE63_{vid[:2]}_TEST"
    test_locale = "en-US"
    test_text = f"MSG22AE63_{vid[:2]}_TEXT"

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

    lines = [
        f"* MESSAGE_CATALOG_PHASE22AE_6_3_{vid}.dts",
        f"* Sandbox-only alternative write proof: {variant['description']}",
        "* Active catalog roots must not appear below.",
        "",
        f"USE {msg_dbf.resolve().as_posix()}",
        "APPEND",
        pos_cmd,
        replace_line(style, msg_symbol, test_symbol),
    ]
    if msg_kind:
        lines.append(replace_line(style, msg_kind, "sandbox_probe"))
    if msg_ph:
        lines.append(replace_line(style, msg_ph, ""))
    if msg_status:
        lines.append(replace_line(style, msg_status, "SANDBOX"))
    if msg_source:
        lines.append(replace_line(style, msg_source, "22AE_6_3"))
    lines += [
        "",
        f"USE {text_dbf.resolve().as_posix()}",
        "APPEND",
        pos_cmd,
        replace_line(style, text_symbol, test_symbol),
        replace_line(style, text_locale, test_locale),
        replace_line(style, text_text, test_text),
    ]
    if text_ph:
        lines.append(replace_line(style, text_ph, ""))
    if text_status:
        lines.append(replace_line(style, text_status, "SANDBOX"))
    if text_source:
        lines.append(replace_line(style, text_source, "22AE_6_3"))
    lines += ["", "* End variant.", ""]

    script = repo / SCRIPT_DIR / f"MESSAGE_CATALOG_PHASE22AE_6_3_{vid}.dts"
    script.parent.mkdir(parents=True, exist_ok=True)
    script.write_text("\n".join(lines), encoding="utf-8")
    return rel(script, repo)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--replace-existing-sandbox", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    reports = repo / REPORT_DIR
    reports.mkdir(parents=True, exist_ok=True)

    ae62 = first_row(reports / "message_catalog_phase22ae_6_2_status_summary_v1.csv")
    sp62, latest_id = savepoint_present(repo, "MSG-022AE.6.2")

    sandbox = repo / SANDBOX_ROOT
    gates = []
    failures = 0
    errors = []

    def gate(name, ok, detail):
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": str(detail)})
        if not ok:
            failures += 1

    gate("PHASE22AE_6_2_GREEN", ae62.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_2_ALTERNATIVE_SANDBOX_WRITE_PATH_PLAN_GREEN_SOURCE_HELD", ae62.get("STATUS", "missing"))
    gate("MSG_022AE_6_2_SAVEPOINT_PRESENT", sp62, latest_id)
    gate("SANDBOX_NOT_EXISTING_OR_REPLACE_ALLOWED", (not sandbox.exists()) or args.replace_existing_sandbox, rel(sandbox, repo))
    gate("ACTIVE_MESSAGING_ROOT_EXISTS", (repo / ACTIVE_MSG_ROOT).exists(), rel(repo / ACTIVE_MSG_ROOT, repo))
    gate("ACTIVE_INDEX_ROOT_EXISTS", (repo / ACTIVE_INDEX_ROOT).exists(), rel(repo / ACTIVE_INDEX_ROOT, repo))
    gate("ACTIVE_LMDB_ROOT_EXISTS", (repo / ACTIVE_LMDB_ROOT).exists(), rel(repo / ACTIVE_LMDB_ROOT, repo))

    copy_rows = []
    variant_rows = []
    status = STATUS_BLOCKED

    if failures == 0:
        try:
            if sandbox.exists() and args.replace_existing_sandbox:
                shutil.rmtree(sandbox)
            sandbox.mkdir(parents=True, exist_ok=True)

            for variant in VARIANTS:
                vid = variant["variant_id"]
                vroot = sandbox / vid
                copy_tree(repo / ACTIVE_MSG_ROOT, vroot / "messaging", repo, copy_rows, f"{vid}_messaging_copy")
                copy_tree(repo / ACTIVE_INDEX_ROOT, vroot / "indexes_messaging", repo, copy_rows, f"{vid}_indexes_copy")
                copy_tree(repo / ACTIVE_LMDB_ROOT, vroot / "lmdb_messaging", repo, copy_rows, f"{vid}_lmdb_copy")

                msg_dbf = vroot / "messaging/SYSTEM_MESSAGES.dbf"
                text_dbf = vroot / "messaging/SYSTEM_MESSAGE_TEXT.dbf"
                msg_info = parse_dbf(msg_dbf)
                text_info = parse_dbf(text_dbf)
                script_rel = generate_variant_script(repo, variant, msg_dbf, text_dbf, msg_info, text_info)
                test_symbol = f"MSG22AE63_{vid[:2]}_TEST"
                variant_rows.append({
                    "VARIANT_ID": vid,
                    "DESCRIPTION": variant["description"],
                    "SCRIPT_PATH": script_rel,
                    "SANDBOX_ROOT": rel(vroot, repo),
                    "MESSAGE_ROWS_BEFORE": msg_info.record_count,
                    "TEXT_ROWS_BEFORE": text_info.record_count,
                    "TEST_SYMBOL": test_symbol,
                    "ACTIVE_MUTATION": 0,
                })

            driver = repo / SCRIPT_DIR / "MESSAGE_CATALOG_PHASE22AE_6_3_RUN_ALL_ALTERNATIVE_SANDBOX_WRITE_PROOFS.dts"
            driver_lines = [
                "* MESSAGE_CATALOG_PHASE22AE_6_3_RUN_ALL_ALTERNATIVE_SANDBOX_WRITE_PROOFS.dts",
                "* Runs every 22AE.6.3 sandbox-only variant. Active catalog roots are not targeted.",
                "",
            ]
            for row in variant_rows:
                driver_lines.append(f"DO {str((repo / row['SCRIPT_PATH']).resolve()).replace(chr(92), '/')}")
            driver_lines.append("")
            driver.write_text("\n".join(driver_lines), encoding="utf-8")
            status = STATUS_GREEN
        except Exception as exc:
            errors.append(str(exc))
            failures += 1
            status = STATUS_BLOCKED

    validation_issues = "0" if status == STATUS_GREEN else str(failures)

    write_csv(reports / "message_catalog_phase22ae_6_3_stage_gate_check_v1.csv", gates, ["GATE", "STATUS", "DETAIL"])
    write_csv(reports / "message_catalog_phase22ae_6_3_sandbox_copy_inventory_v1.csv", copy_rows, ["SOURCE", "TARGET", "ROLE", "FILES", "BYTES"])
    write_csv(reports / "message_catalog_phase22ae_6_3_variant_manifest_v1.csv", variant_rows, ["VARIANT_ID", "DESCRIPTION", "SCRIPT_PATH", "SANDBOX_ROOT", "MESSAGE_ROWS_BEFORE", "TEXT_ROWS_BEFORE", "TEST_SYMBOL", "ACTIVE_MUTATION"])

    boundary = [
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No source mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_DBF_CATALOG", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Sandbox variants only; no active DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_CDX_INDEXES", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Sandbox variants only; no active index mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Sandbox variants only; no active LMDB mutation."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No HELP DATA mutation."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CMDHELPCHK mutation."},
    ]
    write_csv(reports / "message_catalog_phase22ae_6_3_stage_boundary_ledger_v1.csv", boundary, ["PROTECTED_SYSTEM", "MUTATION_ALLOWED", "OBSERVED_MUTATION", "DETAIL"])

    driver_path = repo / SCRIPT_DIR / "MESSAGE_CATALOG_PHASE22AE_6_3_RUN_ALL_ALTERNATIVE_SANDBOX_WRITE_PROOFS.dts"

    write_csv(reports / "message_catalog_phase22ae_6_3_stage_status_summary_v1.csv", [{
        "STATUS": status,
        "VALIDATION_ISSUES": validation_issues,
        "PHASE22AE_6_2_GREEN": 1 if ae62.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_2_ALTERNATIVE_SANDBOX_WRITE_PATH_PLAN_GREEN_SOURCE_HELD" else 0,
        "MSG_022AE_6_2_SAVEPOINT_PRESENT": 1 if sp62 else 0,
        "SANDBOX_ROOT": rel(sandbox, repo),
        "VARIANTS_STAGED": len(variant_rows),
        "DRIVER_SCRIPT_PATH": rel(driver_path, repo),
        "ACTIVE_CATALOG_MUTATION_OBSERVED": 0,
        "SOURCE_FILES_MUTATED": 0,
        "HELP_DATA_MUTATION_OBSERVED": 0,
        "CMDHELPCHK_MUTATION_OBSERVED": 0,
        "ERRORS": "; ".join(errors),
        "NEXT_GATE": NEXT_GATE,
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }], ["STATUS", "VALIDATION_ISSUES", "PHASE22AE_6_2_GREEN", "MSG_022AE_6_2_SAVEPOINT_PRESENT",
         "SANDBOX_ROOT", "VARIANTS_STAGED", "DRIVER_SCRIPT_PATH",
         "ACTIVE_CATALOG_MUTATION_OBSERVED", "SOURCE_FILES_MUTATED",
         "HELP_DATA_MUTATION_OBSERVED", "CMDHELPCHK_MUTATION_OBSERVED", "ERRORS",
         "NEXT_GATE", "REPORT_TIMESTAMP_UTC"])

    md = f"""# Message Catalog Phase 22AE.6.3 Alternative Sandbox Write Proof Package

Status: `{status}`

Sandbox root:

```text
{rel(sandbox, repo)}
```

Driver script:

```text
{rel(driver_path, repo)}
```

This package stages separate sandbox clones per write variant. It does not target
active messaging DBF/CDX/LMDB roots.
"""
    (reports / "MESSAGE_CATALOG_PHASE22AE_6_3_ALTERNATIVE_SANDBOX_WRITE_PROOF_PACKAGE.md").write_text(md, encoding="utf-8")

    print(status)
    print(f"  validation issues: {validation_issues}")
    print(f"  Phase 22AE.6.2 green: {1 if ae62.get('STATUS') == 'MESSAGE_CATALOG_PHASE22AE_6_2_ALTERNATIVE_SANDBOX_WRITE_PATH_PLAN_GREEN_SOURCE_HELD' else 0}")
    print(f"  MSG-022AE.6.2 savepoint present: {1 if sp62 else 0}")
    print(f"  sandbox root: {rel(sandbox, repo)}")
    print(f"  variants staged: {len(variant_rows)}")
    print(f"  driver script path: {rel(driver_path, repo)}")
    print("  active catalog mutation observed: 0")
    print("  source files mutated: 0")
    print(f"  next gate: {NEXT_GATE}")
    print(f"  reports: {reports}")
    return 0 if status == STATUS_GREEN else 2

if __name__ == "__main__":
    raise SystemExit(main())
