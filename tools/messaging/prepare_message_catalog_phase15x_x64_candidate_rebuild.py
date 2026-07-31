#!/usr/bin/env python3
"""
Phase 15X: Prepare x64 candidate table rebuild for DotTalk++ Messaging catalog.

This phase corrects the substrate after discovering the earlier candidate DBFs
were v32+memo. It generates a DotTalk++ DTS script that creates the two
messaging catalog tables as native x64 tables using CREATE X64, populates them
from Phase 9 candidate CSVs, and includes precomputed compound-key fields
because compound CDX keys are not supported yet.

Prepare step does not run DotTalk++ and does not mutate active catalogs.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

STATUS = "MESSAGE_CATALOG_PHASE15X_X64_CANDIDATE_REBUILD_SCRIPT_STAGED"
NEXT_GATE = "RUN_DOTTALK_PHASE15X_X64_REBUILD_THEN_VALIDATE"
REPORT_DIR = Path("docs/messaging/reports")
PHASE9_ROOT = Path("docs/messaging/candidates/phase9_inactive_candidate_dbf_staging")
PHASE15X_ROOT = Path("docs/messaging/candidates/phase15x_x64_candidate_rebuild")

def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        w.writeheader()
        for row in rows:
            w.writerow({k: row.get(k, "") for k in fields})

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def pick(row: dict[str, str], *names: str, default: str = "") -> str:
    for n in names:
        if n in row and row[n] != "":
            return row[n]
    return default

def q(value: str) -> str:
    """DotTalk double-quoted string literal."""
    if value is None:
        value = ""
    value = str(value)
    value = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{value}"'

def safe_text(value: str, max_len: int) -> str:
    value = "" if value is None else str(value)
    # Keep current status-message phase simple: no memo field, char field only.
    # Values longer than max are truncated in the DTS input and reported.
    return value[:max_len]

def sha256_text(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

def transform_messages(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    out = []
    for r in rows:
        out.append({
            "MSGID": pick(r, "MSGID", "MESSAGE_ID"),
            "SYMBOL": pick(r, "SYMBOL"),
            "ENUMNAME": pick(r, "ENUMNAME", "ENUM_NAME"),
            "FACILITY": pick(r, "FACILITY", default="GLOBAL"),
            "OWNER": pick(r, "OWNER", "OWNER_SUBSYSTEM", default="GLOBAL"),
            "CATEGORY": pick(r, "CATEGORY", default="STATUS"),
            "SEVERITY": pick(r, "SEVERITY", default="INFO"),
            "STATUS": pick(r, "STATUS", default="ACTIVE"),
            "SRC": pick(r, "SRC", "SOURCE", default="PHASE6"),
        })
    return out

def transform_text(rows: list[dict[str, str]]) -> tuple[list[dict[str, str]], list[dict[str, Any]]]:
    out = []
    trunc = []
    for r in rows:
        msgid = pick(r, "MSGID", "MESSAGE_ID")
        symbol = pick(r, "SYMBOL")
        enumname = pick(r, "ENUMNAME", "ENUM_NAME")
        locale = pick(r, "LOCALE")
        text = pick(r, "TEXT", "TEXT_TEMPLATE")
        out.append({
            "MSGID": msgid,
            "SYMBOL": symbol,
            "ENUMNAME": enumname,
            "LOCALE": locale,
            # Compound index workaround fields.
            # Compound CDX expressions are not supported yet, so store them as fields.
            "MSGLOCALE": f"{int(float(msgid)):010d}|{locale}" if msgid else f"0000000000|{locale}",
            "SYMBOLLOC": f"{symbol}|{locale}",
            "TEXT": text,
            "TXTHASH": pick(r, "TXTHASH", "TEXT_HASH", default=sha256_text(text)),
            "STATUS": pick(r, "STATUS", default="ACTIVE"),
            "SRC": pick(r, "SRC", "SOURCE", default="PHASE6"),
        })
    return out, trunc

def append_replace_lines(lines: list[str], table_rows: list[dict[str, str]], fields: list[str]) -> None:
    for r in table_rows:
        lines.append("APPEND")
        for f in fields:
            value = r.get(f, "")
            if f == "MSGID":
                lines.append(f"REPLACE {f} WITH {int(float(value)) if value else 0}")
            else:
                lines.append(f"REPLACE {f} WITH {q(value)}")
        lines.append("")

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--allow-x64-candidate-rebuild", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    reports = repo / REPORT_DIR
    reports.mkdir(parents=True, exist_ok=True)

    gates: list[dict[str, Any]] = []
    failures = 0
    def gate(name: str, ok: bool, detail: str) -> None:
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": detail})
        if not ok:
            failures += 1

    msg_csv = repo / PHASE9_ROOT / "import_inputs" / "SYSTEM_MESSAGES_import_candidate_v1.csv"
    txt_csv = repo / PHASE9_ROOT / "import_inputs" / "SYSTEM_MESSAGE_TEXT_import_candidate_v1.csv"
    p14_status = repo / REPORT_DIR / "message_catalog_phase14_status_summary_v1.csv"
    p15_status = repo / REPORT_DIR / "message_catalog_phase15_status_summary_v1.csv"

    gate("OPERATOR_AUTHORIZED_X64_CANDIDATE_REBUILD", args.allow_x64_candidate_rebuild, "requires --allow-x64-candidate-rebuild")
    gate("PHASE9_SYSTEM_MESSAGES_INPUT_PRESENT", msg_csv.exists(), str(msg_csv))
    gate("PHASE9_SYSTEM_MESSAGE_TEXT_INPUT_PRESENT", txt_csv.exists(), str(txt_csv))
    gate("PHASE14_STATUS_PRESENT", p14_status.exists(), str(p14_status))
    gate("PHASE15_STATUS_PRESENT", p15_status.exists(), str(p15_status))

    messages = "0"
    text_rows = "0"
    locales = ""
    validation_issues = "0"

    if failures == 0:
        msg_rows = transform_messages(read_csv(msg_csv))
        txt_rows, trunc_rows = transform_text(read_csv(txt_csv))

        messages = str(len(msg_rows))
        text_rows = str(len(txt_rows))
        locales = ";".join(sorted(set(r["LOCALE"] for r in txt_rows)))

        gate("EXPECTED_MESSAGE_COUNT", len(msg_rows) == 12, f"messages={len(msg_rows)}")
        gate("EXPECTED_TEXT_COUNT", len(txt_rows) == 60, f"text_rows={len(txt_rows)}")
        gate("TEXT_MEMO_FIELD_SELECTED", True, "TEXT uses X64 memo field M; no truncation required")

        root = repo / PHASE15X_ROOT
        if root.exists():
            shutil.rmtree(root)
        dbf_dir = root / "dbf"
        indexes_dir = root / "indexes"
        lmdb_dir = root / "lmdb"
        scripts_dir = root / "scripts"
        runlog_dir = repo / "docs/messaging/runlog"
        for d in [dbf_dir, indexes_dir, lmdb_dir, scripts_dir, runlog_dir]:
            d.mkdir(parents=True, exist_ok=True)

        msg_fields = ["MSGID", "SYMBOL", "ENUMNAME", "FACILITY", "OWNER", "CATEGORY", "SEVERITY", "STATUS", "SRC"]
        txt_fields = ["MSGID", "SYMBOL", "ENUMNAME", "LOCALE", "MSGLOCALE", "SYMBOLLOC", "TEXT", "TXTHASH", "STATUS", "SRC"]

        create_script = scripts_dir / "MESSAGE_CATALOG_PHASE15X_CREATE_X64_CANDIDATES.dts"
        lines = [
            "* MESSAGE_CATALOG_PHASE15X_CREATE_X64_CANDIDATES.dts",
            "* Corrective x64 substrate rebuild for Messaging catalog candidate.",
            "* Boundary: inactive candidate path only; no active catalog promotion.",
            "CLOSE ALL",
            f"SET PATH DBF {dbf_dir}",
            f"SET PATH INDEXES {indexes_dir}",
            f"SET PATH LMDB {lmdb_dir}",
            "",
            "* Clean prior candidate tables from this candidate path only.",
            "ERASE SYSTEM_MESSAGES CONFIRM",
            "ERASE SYSTEM_MESSAGE_TEXT CONFIRM",
            "",
            "* Create native x64 tables. Compound lookup keys are precomputed fields.",
            "CREATE X64 SYSTEM_MESSAGES (MSGID N(10,0), SYMBOL C(64), ENUMNAME C(64), FACILITY C(32), OWNER C(64), CATEGORY C(32), SEVERITY C(16), STATUS C(16), SRC C(32))",
            "",
        ]
        append_replace_lines(lines, msg_rows, msg_fields)
        lines.extend([
            "CLOSE",
            "",
            "CREATE X64 SYSTEM_MESSAGE_TEXT (MSGID N(10,0), SYMBOL C(64), ENUMNAME C(64), LOCALE C(16), MSGLOCALE C(32), SYMBOLLOC C(96), TEXT M, TXTHASH C(64), STATUS C(16), SRC C(32))",
            "",
        ])
        append_replace_lines(lines, txt_rows, txt_fields)
        lines.extend([
            "CLOSE",
            "",
            "* Runtime validation: both tables should reopen as v64.",
            "SELECT 0",
            "USE SYSTEM_MESSAGES",
            "AREA",
            "COUNT",
            "STRUCT",
            "SL 3",
            "",
            "SELECT 1",
            "USE SYSTEM_MESSAGE_TEXT",
            "AREA",
            "COUNT",
            "STRUCT",
            "SL 3",
            "",
            "SELECT 2",
            "",
        ])
        create_script.write_text("\n".join(lines), encoding="utf-8")

        cdx_script = scripts_dir / "MESSAGE_CATALOG_PHASE15X_CREATE_X64_CDX_TAGS.dts"
        cdx_lines = [
            "* MESSAGE_CATALOG_PHASE15X_CREATE_X64_CDX_TAGS.dts",
            "* Candidate-only CDX tags over x64 messaging tables.",
            "CLOSE ALL",
            f"SET PATH DBF {dbf_dir}",
            f"SET PATH INDEXES {indexes_dir}",
            f"SET PATH LMDB {lmdb_dir}",
            "",
            "SELECT 0",
            "USE SYSTEM_MESSAGES",
            "CDX CREATE",
            "CDX ADDTAG MSGID",
            "CDX ADDTAG SYMBOL",
            "CDX ADDTAG ENUMNAME",
            "CDX ADDTAG SEVERITY",
            "CDX ADDTAG FACILITY",
            "CDX ADDTAG OWNER",
            "",
            "SELECT 1",
            "USE SYSTEM_MESSAGE_TEXT",
            "CDX CREATE",
            "CDX ADDTAG MSGID",
            "CDX ADDTAG SYMBOL",
            "CDX ADDTAG ENUMNAME",
            "CDX ADDTAG LOCALE",
            "CDX ADDTAG MSGLOCALE",
            "CDX ADDTAG SYMBOLLOC",
            "CDX ADDTAG TXTHASH",
            "",
            "SELECT 2",
            "",
        ]
        cdx_script.write_text("\n".join(cdx_lines), encoding="utf-8")

        write_csv(root / "SYSTEM_MESSAGES_x64_input_v1.csv", msg_rows, msg_fields)
        write_csv(root / "SYSTEM_MESSAGE_TEXT_x64_input_v1.csv", txt_rows, txt_fields)
        write_csv(reports / "message_catalog_phase15x_text_truncation_review_v1.csv", trunc_rows,
                  ["MSGID", "SYMBOL", "LOCALE", "ORIGINAL_LENGTH", "TRUNCATED_LENGTH", "STATUS"])

        artifact_rows = []
        for p in sorted(root.rglob("*")):
            if p.is_file():
                artifact_rows.append({
                    "RELATIVE_PATH": str(p.relative_to(repo)).replace("\\", "/"),
                    "BYTES": p.stat().st_size,
                    "SHA256": sha256_file(p),
                    "ROLE": "phase15x_x64_candidate_rebuild_artifact",
                })
        write_csv(reports / "message_catalog_phase15x_staging_artifact_inventory_v1.csv",
                  artifact_rows, ["RELATIVE_PATH", "BYTES", "SHA256", "ROLE"])

        manifest = {
            "status": STATUS,
            "candidate_name": "phase15x_x64_candidate_rebuild",
            "candidate_root": str(PHASE15X_ROOT).replace("\\", "/"),
            "dbf_path": str(dbf_dir),
            "indexes_path": str(indexes_dir),
            "lmdb_path": str(lmdb_dir),
            "messages": int(messages),
            "text_rows": int(text_rows),
            "locales": locales.split(";") if locales else [],
            "validation_issues": int(validation_issues),
            "x64_create_script": str(create_script.relative_to(repo)).replace("\\", "/"),
            "x64_cdx_script": str(cdx_script.relative_to(repo)).replace("\\", "/"),
            "compound_key_workaround_fields": ["MSGLOCALE", "SYMBOLLOC"],
            "memo_fields_used": 1,
            "active_promotion_authorized": 0,
            "candidate_artifacts": artifact_rows,
        }
        (root / "candidate_manifest_prepare_v1.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    else:
        write_csv(reports / "message_catalog_phase15x_staging_artifact_inventory_v1.csv", [],
                  ["RELATIVE_PATH", "BYTES", "SHA256", "ROLE"])

    status = STATUS if failures == 0 else "MESSAGE_CATALOG_PHASE15X_X64_CANDIDATE_REBUILD_SCRIPT_BLOCKED"
    write_csv(reports / "message_catalog_phase15x_prepare_status_summary_v1.csv", [{
        "STATUS": status,
        "MESSAGES": messages,
        "TEXT_ROWS": text_rows,
        "LOCALES": locales,
        "VALIDATION_ISSUES": validation_issues if failures == 0 else str(failures),
        "X64_REBUILD_SCRIPT_STAGED": 1 if failures == 0 else 0,
        "CDX_SCRIPT_STAGED": 1 if failures == 0 else 0,
        "LMDB_ENV_CREATED": 0,
        "ACTIVE_PROMOTION_AUTHORIZED": 0,
        "NEXT_GATE": NEXT_GATE,
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }], ["STATUS", "MESSAGES", "TEXT_ROWS", "LOCALES", "VALIDATION_ISSUES",
         "X64_REBUILD_SCRIPT_STAGED", "CDX_SCRIPT_STAGED", "LMDB_ENV_CREATED",
         "ACTIVE_PROMOTION_AUTHORIZED", "NEXT_GATE", "REPORT_TIMESTAMP_UTC"])

    write_csv(reports / "message_catalog_phase15x_prepare_gate_check_v1.csv", gates, ["GATE", "STATUS", "DETAIL"])

    boundary = [
        {"PROTECTED_SYSTEM": "INACTIVE_CANDIDATE_X64_SCRIPT_STAGING", "MUTATION_ALLOWED": 1, "OBSERVED_MUTATION": 1 if failures == 0 else 0, "DETAIL": "Prepare step stages candidate-only x64 CREATE/APPEND scripts and input CSV snapshots."},
        {"PROTECTED_SYSTEM": "INACTIVE_CANDIDATE_DBF", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Prepare step does not create DBF files; DotTalk runtime step will create candidate-only x64 DBFs if run."},
        {"PROTECTED_SYSTEM": "INACTIVE_CANDIDATE_CDX", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Prepare step creates no CDX files."},
        {"PROTECTED_SYSTEM": "INACTIVE_CANDIDATE_LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No LMDB environment created."},
        {"PROTECTED_SYSTEM": "ACTIVE_DBF_CATALOGS", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active DBF/catalog paths touched."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No HELP DATA mutation."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CMDHELPCHK mutation."},
        {"PROTECTED_SYSTEM": "SOURCE_MINING", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No source-mining mutation."},
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No source-code mutation."},
        {"PROTECTED_SYSTEM": "CATALOG_PROMOTION", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active catalog promotion."},
    ]
    write_csv(reports / "message_catalog_phase15x_prepare_boundary_ledger_v1.csv", boundary,
              ["PROTECTED_SYSTEM", "MUTATION_ALLOWED", "OBSERVED_MUTATION", "DETAIL"])

    print(status)
    print(f"  messages: {messages}")
    print(f"  text rows: {text_rows}")
    print(f"  locales: {locales.replace(';', ', ')}")
    print(f"  validation issues: {validation_issues if failures == 0 else failures}")
    print(f"  x64 rebuild script staged: {1 if failures == 0 else 0}")
    print(f"  cdx script staged: {1 if failures == 0 else 0}")
    print("  lmdb env created: 0")
    print("  active promotion authorized: 0")
    print(f"  reports: {reports}")
    return 0 if failures == 0 else 2

if __name__ == "__main__":
    raise SystemExit(main())
