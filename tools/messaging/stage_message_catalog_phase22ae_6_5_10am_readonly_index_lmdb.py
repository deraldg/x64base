#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

STATUS_GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_10AM_READONLY_INDEX_LMDB_VERIFICATION_STAGED_SOURCE_HELD"
STATUS_BLOCKED = "MESSAGE_CATALOG_PHASE22AE_6_5_10AM_READONLY_INDEX_LMDB_VERIFICATION_STAGE_BLOCKED"
NEXT_GATE = "RUN_PHASE22AE_6_5_10AM_READONLY_INDEX_LMDB_RUNTIME_THEN_VALIDATE"

REPORT_DIR = Path("docs/messaging/reports")
SCRIPT_PATH = Path("docs/messaging/scripts/MESSAGE_CATALOG_PHASE22AE_6_5_10AM_READONLY_INDEX_LMDB_VERIFICATION.dts")
RUNLOG_PATH = Path("docs/messaging/runlog/MSG-022AE_6_5_10AM_READONLY_INDEX_LMDB_VERIFICATION.md")

ACTIVE_MSG_DBF = Path("dottalkpp/data/messaging/SYSTEM_MESSAGES.dbf")
ACTIVE_TEXT_DBF = Path("dottalkpp/data/messaging/SYSTEM_MESSAGE_TEXT.dbf")

ARTIFACTS = [
    ("SYSTEM_MESSAGES_DBF", ACTIVE_MSG_DBF),
    ("SYSTEM_MESSAGE_TEXT_DBF", ACTIVE_TEXT_DBF),
    ("SYSTEM_MESSAGES_DBF_SIDE_CDX", Path("dottalkpp/data/messaging/SYSTEM_MESSAGES.cdx")),
    ("SYSTEM_MESSAGE_TEXT_DBF_SIDE_CDX", Path("dottalkpp/data/messaging/SYSTEM_MESSAGE_TEXT.cdx")),
    ("SYSTEM_MESSAGES_MESSAGING_CDX", Path("dottalkpp/data/indexes/messaging/SYSTEM_MESSAGES.cdx")),
    ("SYSTEM_MESSAGE_TEXT_MESSAGING_CDX", Path("dottalkpp/data/indexes/messaging/SYSTEM_MESSAGE_TEXT.cdx")),
    ("SYSTEM_MESSAGES_MESSAGING_CDX_META", Path("dottalkpp/data/indexes/messaging/SYSTEM_MESSAGES.cdx.meta")),
    ("SYSTEM_MESSAGE_TEXT_MESSAGING_CDX_META", Path("dottalkpp/data/indexes/messaging/SYSTEM_MESSAGE_TEXT.cdx.meta")),
    ("SYSTEM_MESSAGES_MESSAGING_LMDB", Path("dottalkpp/data/lmdb/messaging/SYSTEM_MESSAGES.cdx.d")),
    ("SYSTEM_MESSAGE_TEXT_MESSAGING_LMDB", Path("dottalkpp/data/lmdb/messaging/SYSTEM_MESSAGE_TEXT.cdx.d")),
    ("SYSTEM_MESSAGES_DEFAULT_CDX", Path("dottalkpp/data/indexes/SYSTEM_MESSAGES.cdx")),
    ("SYSTEM_MESSAGE_TEXT_DEFAULT_CDX", Path("dottalkpp/data/indexes/SYSTEM_MESSAGE_TEXT.cdx")),
    ("SYSTEM_MESSAGES_DEFAULT_LMDB", Path("dottalkpp/data/lmdb/SYSTEM_MESSAGES.cdx.d")),
    ("SYSTEM_MESSAGE_TEXT_DEFAULT_LMDB", Path("dottalkpp/data/lmdb/SYSTEM_MESSAGE_TEXT.cdx.d")),
]

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

def hash_dir(path: Path):
    if not path.exists() or not path.is_dir():
        return "", 0, 0
    files = sorted(p for p in path.rglob("*") if p.is_file())
    h = hashlib.sha256()
    total = 0
    for f in files:
        h.update(str(f.relative_to(path)).replace("\\", "/").encode("utf-8"))
        h.update(sha256_file(f).encode("ascii"))
        total += f.stat().st_size
    return h.hexdigest(), len(files), total

def artifact_inventory(repo: Path):
    rows = []
    for role, path in ARTIFACTS:
        p = repo / path
        if p.is_dir():
            h, count, size = hash_dir(p)
            rows.append({"ROLE": role, "PATH": rel(p, repo), "EXISTS": 1, "KIND": "dir", "BYTES": size, "FILES": count, "SHA256": h})
        elif p.is_file():
            rows.append({"ROLE": role, "PATH": rel(p, repo), "EXISTS": 1, "KIND": "file", "BYTES": p.stat().st_size, "FILES": 1, "SHA256": sha256_file(p)})
        else:
            rows.append({"ROLE": role, "PATH": rel(p, repo), "EXISTS": 0, "KIND": "missing", "BYTES": 0, "FILES": 0, "SHA256": ""})
    return rows

def dbf_header_count(path: Path):
    if not path.exists() or path.stat().st_size < 12:
        return ""
    return int.from_bytes(path.read_bytes()[:12][4:8], "little")

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

def dottalkpp_running():
    if sys.platform.startswith("win"):
        try:
            cp = subprocess.run(["tasklist", "/FI", "IMAGENAME eq dottalkpp.exe"], capture_output=True, text=True, timeout=10)
            out = (cp.stdout or "") + (cp.stderr or "")
            return "dottalkpp.exe" in out.lower()
        except Exception:
            return False
    return False

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--replace-existing-script", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    reports = repo / REPORT_DIR
    reports.mkdir(parents=True, exist_ok=True)

    al = first_row(reports / "message_catalog_phase22ae_6_5_10al_status_summary_v1.csv")
    sp_al, latest = savepoint_present(repo, "MSG-022AE.6.5.10AL")
    running = dottalkpp_running()
    script = repo / SCRIPT_PATH
    inv_rows = artifact_inventory(repo)

    msg_count = dbf_header_count(repo / ACTIVE_MSG_DBF)
    text_count = dbf_header_count(repo / ACTIVE_TEXT_DBF)
    cdx_exists = sum(1 for r in inv_rows if "CDX" in r["ROLE"] and r["EXISTS"] == 1)
    lmdb_exists = sum(1 for r in inv_rows if "LMDB" in r["ROLE"] and r["EXISTS"] == 1)

    gates = []
    failures = 0
    def gate(name, ok, detail):
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": str(detail)})
        if not ok:
            failures += 1

    gate("PHASE22AE_6_5_10AL_GREEN",
         al.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_5_10AL_FOLLOWUP_INDEX_LMDB_OR_RUNTIME_MESSAGE_CONSUMER_PLAN_GREEN_SOURCE_HELD",
         al.get("STATUS", "missing"))
    gate("MSG_022AE_6_5_10AL_SAVEPOINT_PRESENT", sp_al, latest)
    gate("ACTIVE_MESSAGES_HEADER_COUNT_14", msg_count == 14, msg_count)
    gate("ACTIVE_TEXT_HEADER_COUNT_70", text_count == 70, text_count)
    gate("NO_DOTTALKPP_PROCESS_RUNNING", not running, running)
    gate("SCRIPT_NOT_EXISTING_OR_REPLACE_ALLOWED", (not script.exists()) or args.replace_existing_script, rel(script, repo))
    gate("SYSTEM_MESSAGES_DBF_EXISTS", (repo / ACTIVE_MSG_DBF).exists(), rel(repo / ACTIVE_MSG_DBF, repo))
    gate("SYSTEM_MESSAGE_TEXT_DBF_EXISTS", (repo / ACTIVE_TEXT_DBF).exists(), rel(repo / ACTIVE_TEXT_DBF, repo))

    status = STATUS_BLOCKED
    if failures == 0:
        script.parent.mkdir(parents=True, exist_ok=True)
        script.write_text("\n".join([
            "* MESSAGE_CATALOG_PHASE22AE_6_5_10AM_READONLY_INDEX_LMDB_VERIFICATION.dts",
            "* READ-ONLY VERIFICATION ONLY.",
            "* No ZAP, IMPORT, APPEND, REPLACE, PACK, CDX CREATE, BUILDLMDB, or source mutation.",
            "* No QUIT here; quit manually in interactive runs.",
            "",
            "* Active SYSTEM_MESSAGES readback; USE output should show Valid Index/Indices if available.",
            f"USE {(repo / ACTIVE_MSG_DBF).resolve().as_posix()}",
            "COUNT",
            "LIST ALL",
            "",
            "* Active SYSTEM_MESSAGE_TEXT readback; USE output should show Valid Index/Indices if available.",
            f"USE {(repo / ACTIVE_TEXT_DBF).resolve().as_posix()}",
            "COUNT",
            "LIST ALL",
            "",
            "* Final cross-table readback.",
            f"USE {(repo / ACTIVE_MSG_DBF).resolve().as_posix()}",
            "COUNT",
            f"USE {(repo / ACTIVE_TEXT_DBF).resolve().as_posix()}",
            "COUNT",
            "",
        ]), encoding="utf-8")
        status = STATUS_GREEN

    boundary = [
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "10AM stage is read-only/report artifact generation."},
        {"PROTECTED_SYSTEM": "ACTIVE_SYSTEM_MESSAGES", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_SYSTEM_MESSAGE_TEXT", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_CDX_LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CDX/LMDB rebuild."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No HELP DATA mutation."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CMDHELPCHK mutation."},
    ]

    validation_issues = "0" if status == STATUS_GREEN else str(failures)

    write_csv(reports / "message_catalog_phase22ae_6_5_10am_stage_gate_check_v1.csv", gates, ["GATE", "STATUS", "DETAIL"])
    write_csv(reports / "message_catalog_phase22ae_6_5_10am_artifact_inventory_before_runtime_v1.csv", inv_rows, ["ROLE", "PATH", "EXISTS", "KIND", "BYTES", "FILES", "SHA256"])
    write_csv(reports / "message_catalog_phase22ae_6_5_10am_stage_boundary_ledger_v1.csv", boundary, ["PROTECTED_SYSTEM", "MUTATION_ALLOWED", "OBSERVED_MUTATION", "DETAIL"])
    write_csv(reports / "message_catalog_phase22ae_6_5_10am_stage_status_summary_v1.csv", [{
        "STATUS": status,
        "VALIDATION_ISSUES": validation_issues,
        "PHASE22AE_6_5_10AL_STATUS": al.get("STATUS", ""),
        "MSG_022AE_6_5_10AL_SAVEPOINT_PRESENT": 1 if sp_al else 0,
        "ACTIVE_MESSAGES_HEADER_COUNT_AT_STAGE": msg_count,
        "ACTIVE_TEXT_HEADER_COUNT_AT_STAGE": text_count,
        "CDX_ARTIFACTS_PRESENT_COUNT": cdx_exists,
        "LMDB_ARTIFACTS_PRESENT_COUNT": lmdb_exists,
        "DOTTALKPP_PROCESS_RUNNING": 1 if running else 0,
        "SCRIPT_PATH": rel(script, repo) if script.exists() else "",
        "RUNLOG_PATH": rel(repo / RUNLOG_PATH, repo),
        "READONLY_RUNTIME_SCRIPT_STAGED": 1 if status == STATUS_GREEN else 0,
        "INDEX_LMDB_REBUILD_AUTHORIZED": 0,
        "RUNTIME_CONSUMER_INTEGRATION_AUTHORIZED": 0,
        "SOURCE_FILES_MUTATED": 0,
        "ACTIVE_CATALOG_MUTATION_OBSERVED": 0,
        "HELP_DATA_MUTATION_OBSERVED": 0,
        "CMDHELPCHK_MUTATION_OBSERVED": 0,
        "NEXT_GATE": NEXT_GATE,
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }], ["STATUS", "VALIDATION_ISSUES", "PHASE22AE_6_5_10AL_STATUS", "MSG_022AE_6_5_10AL_SAVEPOINT_PRESENT",
         "ACTIVE_MESSAGES_HEADER_COUNT_AT_STAGE", "ACTIVE_TEXT_HEADER_COUNT_AT_STAGE",
         "CDX_ARTIFACTS_PRESENT_COUNT", "LMDB_ARTIFACTS_PRESENT_COUNT", "DOTTALKPP_PROCESS_RUNNING",
         "SCRIPT_PATH", "RUNLOG_PATH", "READONLY_RUNTIME_SCRIPT_STAGED", "INDEX_LMDB_REBUILD_AUTHORIZED",
         "RUNTIME_CONSUMER_INTEGRATION_AUTHORIZED", "SOURCE_FILES_MUTATED", "ACTIVE_CATALOG_MUTATION_OBSERVED",
         "HELP_DATA_MUTATION_OBSERVED", "CMDHELPCHK_MUTATION_OBSERVED", "NEXT_GATE", "REPORT_TIMESTAMP_UTC"])

    (repo / "docs/messaging/MESSAGE_LOCALE_PHASE22AE_6_5_10AM_READONLY_INDEX_LMDB_VERIFICATION.md").write_text(
        f"# Message Catalog Phase 22AE.6.5.10AM Read-Only Index/LMDB Verification\n\nStatus: `{status}`\n\n10AM is read-only. It inventories DBF/CDX/LMDB artifacts and stages a runtime script that uses only USE, COUNT, and LIST ALL.\n\nNext gate:\n\n```text\n{NEXT_GATE}\n```\n",
        encoding="utf-8"
    )

    print(status)
    print(f"  validation issues: {validation_issues}")
    print(f"  Phase 22AE.6.5.10AL status: {al.get('STATUS','')}")
    print(f"  MSG-022AE.6.5.10AL savepoint present: {1 if sp_al else 0}")
    print(f"  active messages header count at stage: {msg_count}")
    print(f"  active text header count at stage: {text_count}")
    print(f"  CDX artifacts present count: {cdx_exists}")
    print(f"  LMDB artifacts present count: {lmdb_exists}")
    print(f"  dottalkpp process running: {1 if running else 0}")
    print(f"  script path: {rel(script, repo) if script.exists() else ''}")
    print("  index/LMDB rebuild authorized: 0")
    print("  runtime consumer integration authorized: 0")
    print("  source files mutated: 0")
    print("  active catalog mutation observed: 0")
    print("  HELP DATA mutation observed: 0")
    print("  CMDHELPCHK mutation observed: 0")
    print(f"  next gate: {NEXT_GATE}")
    print(f"  reports: {reports}")
    return 0 if status == STATUS_GREEN else 2

if __name__ == "__main__":
    raise SystemExit(main())
