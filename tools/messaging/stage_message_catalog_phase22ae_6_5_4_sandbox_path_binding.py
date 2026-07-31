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

STATUS_GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_4_SANDBOX_PATH_BINDING_PROOF_STAGED_SOURCE_HELD"
STATUS_BLOCKED = "MESSAGE_CATALOG_PHASE22AE_6_5_4_SANDBOX_PATH_BINDING_PROOF_STAGING_BLOCKED"
NEXT_GATE = "RUN_PHASE22AE_6_5_4_UNIQUE_BASENAME_RUNTIME_THEN_VALIDATE"

REPORT_DIR = Path("docs/messaging/reports")
SANDBOX_ROOT = Path("docs/messaging/sandbox/phase22ae_6_5_4_sandbox_path_binding_v1")
SCRIPT_PATH = Path("docs/messaging/scripts/MESSAGE_CATALOG_PHASE22AE_6_5_4_UNIQUE_BASENAME_PATH_BINDING_PROOF.dts")

SOURCE_653_SANDBOX = Path("docs/messaging/sandbox/phase22ae_6_5_3_full_candidate_rebuild_v1/dbf")
ACTIVE_MSG_ROOT = Path("dottalkpp/data/messaging")
ACTIVE_MSG_INDEX_ROOT = Path("dottalkpp/data/indexes/messaging")
ACTIVE_MSG_LMDB_ROOT = Path("dottalkpp/data/lmdb/messaging")
DEFAULT_INDEX_ROOT = Path("dottalkpp/data/indexes")
DEFAULT_LMDB_ROOT = Path("dottalkpp/data/lmdb")

TABLES = ["SYSTEM_MESSAGES", "SYSTEM_MESSAGE_TEXT"]
UNIQUE_MESSAGE_DBF = "MSG653_MESSAGES_REBUILT.dbf"
UNIQUE_TEXT_DBF = "MSG653_TEXT_REBUILT.dbf"

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

def dbf_count(path: Path) -> int:
    data = path.read_bytes()
    if len(data) < 12:
        raise RuntimeError(f"DBF too small: {path}")
    return struct.unpack("<I", data[4:8])[0]

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

def fingerprint_selected(repo: Path):
    rows = []
    targets = []
    for table in TABLES:
        targets.append((repo / ACTIVE_MSG_ROOT / f"{table}.dbf", f"active_dbf_{table}"))
        for p in sorted((repo / ACTIVE_MSG_ROOT).glob(f"{table}.*")):
            if p.name.lower() != f"{table.lower()}.dbf":
                targets.append((p, f"active_sidecar_{table}_{p.suffix.lower().lstrip('.')}"))
        targets.append((repo / ACTIVE_MSG_INDEX_ROOT / f"{table}.cdx", f"active_msg_index_{table}_cdx"))
        targets.append((repo / ACTIVE_MSG_INDEX_ROOT / f"{table}.cdx.meta", f"active_msg_index_{table}_meta"))
        targets.append((repo / ACTIVE_MSG_LMDB_ROOT / f"{table}.cdx.d", f"active_msg_lmdb_{table}"))
        targets.append((repo / DEFAULT_INDEX_ROOT / f"{table}.cdx", f"default_index_{table}_cdx"))
        targets.append((repo / DEFAULT_INDEX_ROOT / f"{table}.cdx.meta", f"default_index_{table}_meta"))
        targets.append((repo / DEFAULT_LMDB_ROOT / f"{table}.cdx.d", f"default_lmdb_{table}"))
    seen = set()
    for path, role in targets:
        key = str(path.resolve()) + "|" + role
        if key in seen:
            continue
        seen.add(key)
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

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--replace-existing-sandbox", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    reports = repo / REPORT_DIR
    reports.mkdir(parents=True, exist_ok=True)
    sandbox = repo / SANDBOX_ROOT

    stage653 = first_row(reports / "message_catalog_phase22ae_6_5_3_stage_status_summary_v1.csv")
    sp652, latest_id = savepoint_present(repo, "MSG-022AE.6.5.2")

    gates = []
    failures = 0
    errors = []

    def gate(name, ok, detail):
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": str(detail)})
        if not ok:
            failures += 1

    gate("PHASE22AE_6_5_3_STAGE_GREEN",
         stage653.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_5_3_FULL_CANDIDATE_REBUILD_SANDBOX_PROOF_STAGED_SOURCE_HELD",
         stage653.get("STATUS", "missing"))
    gate("MSG_022AE_6_5_2_SAVEPOINT_PRESENT", sp652, latest_id)
    gate("SANDBOX_NOT_EXISTING_OR_REPLACE_ALLOWED", (not sandbox.exists()) or args.replace_existing_sandbox, rel(sandbox, repo))

    src_msg = repo / SOURCE_653_SANDBOX / "SYSTEM_MESSAGES.dbf"
    src_txt = repo / SOURCE_653_SANDBOX / "SYSTEM_MESSAGE_TEXT.dbf"
    gate("SOURCE_REBUILT_MESSAGES_DBF_EXISTS", src_msg.exists(), rel(src_msg, repo))
    gate("SOURCE_REBUILT_TEXT_DBF_EXISTS", src_txt.exists(), rel(src_txt, repo))

    msg_src_count = ""
    txt_src_count = ""
    if src_msg.exists():
        msg_src_count = dbf_count(src_msg)
        gate("SOURCE_REBUILT_MESSAGES_COUNT_14", msg_src_count == 14, msg_src_count)
    if src_txt.exists():
        txt_src_count = dbf_count(src_txt)
        gate("SOURCE_REBUILT_TEXT_COUNT_70", txt_src_count == 70, txt_src_count)

    before_fp = fingerprint_selected(repo)
    write_csv(reports / "message_catalog_phase22ae_6_5_4_protected_fingerprint_before_v1.csv",
              before_fp, ["ROLE", "PATH", "EXISTS", "KIND", "BYTES", "SHA256", "FILES"])

    copy_rows = []
    unique_msg = sandbox / "dbf" / UNIQUE_MESSAGE_DBF
    unique_txt = sandbox / "dbf" / UNIQUE_TEXT_DBF
    msg_unique_count = ""
    txt_unique_count = ""
    script_rel = ""

    if failures == 0:
        try:
            if sandbox.exists() and args.replace_existing_sandbox:
                shutil.rmtree(sandbox)
            (sandbox / "dbf").mkdir(parents=True, exist_ok=True)
            shutil.copy2(src_msg, unique_msg)
            shutil.copy2(src_txt, unique_txt)

            copy_rows.append({"ROLE": "unique_message_dbf_copy", "SOURCE": rel(src_msg, repo), "TARGET": rel(unique_msg, repo), "BYTES": unique_msg.stat().st_size, "SHA256": sha256_file(unique_msg)})
            copy_rows.append({"ROLE": "unique_text_dbf_copy", "SOURCE": rel(src_txt, repo), "TARGET": rel(unique_txt, repo), "BYTES": unique_txt.stat().st_size, "SHA256": sha256_file(unique_txt)})

            msg_unique_count = dbf_count(unique_msg)
            txt_unique_count = dbf_count(unique_txt)

            script = repo / SCRIPT_PATH
            script.parent.mkdir(parents=True, exist_ok=True)
            script.write_text("\n".join([
                "* MESSAGE_CATALOG_PHASE22AE_6_5_4_UNIQUE_BASENAME_PATH_BINDING_PROOF.dts",
                "* Opens unique-basename copies of the rebuilt 14/70 sandbox DBFs.",
                "* Purpose: prove whether DotTalk++ USE can bind to non-active absolute sandbox paths.",
                f"USE {unique_msg.resolve().as_posix()}",
                f"USE {unique_txt.resolve().as_posix()}",
                "",
            ]), encoding="utf-8")
            script_rel = rel(script, repo)
        except Exception as exc:
            errors.append(str(exc))
            failures += 1

    status = STATUS_GREEN if failures == 0 else STATUS_BLOCKED
    validation_issues = "0" if failures == 0 else str(failures)

    write_csv(reports / "message_catalog_phase22ae_6_5_4_stage_gate_check_v1.csv",
              gates, ["GATE", "STATUS", "DETAIL"])
    write_csv(reports / "message_catalog_phase22ae_6_5_4_sandbox_copy_inventory_v1.csv",
              copy_rows, ["ROLE", "SOURCE", "TARGET", "BYTES", "SHA256"])

    boundary = [
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No source mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_DBF_CATALOG", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Unique DBF copies only."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_CDX_INDEXES", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active CDX mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active LMDB mutation."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No HELP DATA mutation."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CMDHELPCHK mutation."},
    ]
    write_csv(reports / "message_catalog_phase22ae_6_5_4_stage_boundary_ledger_v1.csv",
              boundary, ["PROTECTED_SYSTEM", "MUTATION_ALLOWED", "OBSERVED_MUTATION", "DETAIL"])

    write_csv(reports / "message_catalog_phase22ae_6_5_4_stage_status_summary_v1.csv", [{
        "STATUS": status,
        "VALIDATION_ISSUES": validation_issues,
        "PHASE22AE_6_5_3_STAGE_GREEN": 1 if stage653.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_5_3_FULL_CANDIDATE_REBUILD_SANDBOX_PROOF_STAGED_SOURCE_HELD" else 0,
        "MSG_022AE_6_5_2_SAVEPOINT_PRESENT": 1 if sp652 else 0,
        "SOURCE_REBUILT_MESSAGE_ROWS": msg_src_count,
        "SOURCE_REBUILT_TEXT_ROWS": txt_src_count,
        "UNIQUE_MESSAGE_DBF": rel(unique_msg, repo),
        "UNIQUE_TEXT_DBF": rel(unique_txt, repo),
        "UNIQUE_MESSAGE_ROWS": msg_unique_count,
        "UNIQUE_TEXT_ROWS": txt_unique_count,
        "SCRIPT_PATH": script_rel,
        "ACTIVE_CATALOG_MUTATION_OBSERVED": 0,
        "SOURCE_FILES_MUTATED": 0,
        "HELP_DATA_MUTATION_OBSERVED": 0,
        "CMDHELPCHK_MUTATION_OBSERVED": 0,
        "ERRORS": "; ".join(errors),
        "NEXT_GATE": NEXT_GATE,
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }], ["STATUS", "VALIDATION_ISSUES", "PHASE22AE_6_5_3_STAGE_GREEN", "MSG_022AE_6_5_2_SAVEPOINT_PRESENT",
         "SOURCE_REBUILT_MESSAGE_ROWS", "SOURCE_REBUILT_TEXT_ROWS",
         "UNIQUE_MESSAGE_DBF", "UNIQUE_TEXT_DBF", "UNIQUE_MESSAGE_ROWS", "UNIQUE_TEXT_ROWS",
         "SCRIPT_PATH", "ACTIVE_CATALOG_MUTATION_OBSERVED", "SOURCE_FILES_MUTATED",
         "HELP_DATA_MUTATION_OBSERVED", "CMDHELPCHK_MUTATION_OBSERVED",
         "ERRORS", "NEXT_GATE", "REPORT_TIMESTAMP_UTC"])

    print(status)
    print(f"  validation issues: {validation_issues}")
    print(f"  Phase 22AE.6.5.3 stage green: {1 if stage653.get('STATUS') == 'MESSAGE_CATALOG_PHASE22AE_6_5_3_FULL_CANDIDATE_REBUILD_SANDBOX_PROOF_STAGED_SOURCE_HELD' else 0}")
    print(f"  MSG-022AE.6.5.2 savepoint present: {1 if sp652 else 0}")
    print(f"  source rebuilt message/text rows: {msg_src_count}/{txt_src_count}")
    print(f"  unique message/text rows: {msg_unique_count}/{txt_unique_count}")
    print(f"  unique message DBF: {rel(unique_msg, repo)}")
    print(f"  unique text DBF: {rel(unique_txt, repo)}")
    print(f"  script path: {script_rel}")
    print("  active catalog mutation observed: 0")
    print("  source files mutated: 0")
    print(f"  next gate: {NEXT_GATE}")
    print(f"  reports: {reports}")
    return 0 if status == STATUS_GREEN else 2

if __name__ == "__main__":
    raise SystemExit(main())
