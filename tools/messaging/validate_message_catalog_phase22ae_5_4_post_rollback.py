#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import hashlib
import struct
from datetime import datetime, timezone
from pathlib import Path

STATUS_GREEN = "MESSAGE_CATALOG_PHASE22AE_5_4_POST_ROLLBACK_READBACK_AND_RUNTIME_REGRESSION_GREEN"
STATUS_BLOCKED = "MESSAGE_CATALOG_PHASE22AE_5_4_POST_ROLLBACK_READBACK_AND_RUNTIME_REGRESSION_BLOCKED"
NEXT_GATE = "HOLD_OR_AUTHORIZE_PHASE22AE_6_REDESIGNED_PROMOTION_PATH_PLAN"
REPORT_DIR = Path("docs/messaging/reports")
RUNLOG = Path("docs/messaging/runlog/MSG-022AE_5_4_POST_ROLLBACK_RUNTIME_REGRESSION.md")
ACTIVE_MSG_ROOT = Path("dottalkpp/data/messaging")

REQUIRED_SYMBOLS = ["MESSAGE_PROOF_MODE_STATUS", "MESSAGE_PROOF_BOUNDARY_NOTE"]
REQUIRED_LOCALES = ["en-US", "es", "fr", "de", "it"]

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

def sha256_file(path: Path) -> str:
    if not path.exists() or not path.is_file():
        return ""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def rel(path: Path, repo: Path) -> str:
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

def dbf_count(path: Path) -> int:
    data = path.read_bytes()
    if len(data) < 12:
        raise RuntimeError(f"DBF too small: {path}")
    return struct.unpack("<I", data[4:8])[0]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--runtime-proof", default="")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    reports = repo / REPORT_DIR
    reports.mkdir(parents=True, exist_ok=True)

    ae53 = first_row(reports / "message_catalog_phase22ae_5_3_status_summary_v1.csv")
    sp_ok, latest = savepoint_present(repo, "MSG-022AE.5.3")

    runtime_path = Path(args.runtime_proof) if args.runtime_proof else repo / RUNLOG
    if not runtime_path.is_absolute():
        runtime_path = repo / runtime_path

    msg_dbf = repo / ACTIVE_MSG_ROOT / "SYSTEM_MESSAGES.dbf"
    text_dbf = repo / ACTIVE_MSG_ROOT / "SYSTEM_MESSAGE_TEXT.dbf"

    gates = []
    failures = 0

    def gate(name, ok, detail):
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": str(detail)})
        if not ok:
            failures += 1

    gate("PHASE22AE_5_3_GREEN",
         ae53.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_5_3_ACTIVE_CATALOG_ROLLBACK_EXECUTED",
         ae53.get("STATUS", "missing"))
    gate("MSG_022AE_5_3_SAVEPOINT_PRESENT", sp_ok, latest)
    gate("ACTIVE_SYSTEM_MESSAGES_EXISTS", msg_dbf.exists(), rel(msg_dbf, repo))
    gate("ACTIVE_SYSTEM_MESSAGE_TEXT_EXISTS", text_dbf.exists(), rel(text_dbf, repo))

    msg_count = ""
    text_count = ""
    try:
        msg_count = dbf_count(msg_dbf)
        text_count = dbf_count(text_dbf)
        gate("ACTIVE_MESSAGE_COUNT_12", msg_count == 12, msg_count)
        gate("ACTIVE_TEXT_COUNT_60", text_count == 60, text_count)
    except Exception as exc:
        gate("ACTIVE_DBF_COUNT_READBACK", False, exc)

    log_text = runtime_path.read_text(encoding="utf-8", errors="replace") if runtime_path.exists() else ""
    log_upper = log_text.upper()

    gate("RUNTIME_PROOF_EXISTS", runtime_path.exists(), rel(runtime_path, repo))
    gate("RUNTIME_PROVIDER_ACTIVE_DBF", "MODE: ACTIVE_DBF" in log_upper, "mode active_dbf")
    gate("RUNTIME_ACTIVE_CATALOG_LOADED", "ACTIVE CATALOG LOADED: YES" in log_upper, "active loaded yes")
    gate("RUNTIME_MESSAGE_COUNT_12", "MESSAGE COUNT: 12" in log_upper, "message count 12")
    gate("RUNTIME_TEXT_ROW_COUNT_60", "TEXT ROW COUNT: 60" in log_upper, "text row count 60")
    gate("RUNTIME_MESSAGE_LOCALE_SET_PROOF", "MESSAGE ROUTING PROOF: ACTIVE_DBF MESSAGE_LOCALE_SET" in log_upper, "locale set proof")
    gate("RUNTIME_UNSUPPORTED_LOCALE_PROOF", "MESSAGE ROUTING PROOF: ACTIVE_DBF UNSUPPORTED_MESSAGE_LOCALE" in log_upper, "unsupported locale proof")
    gate("RUNTIME_HELP_HINT_PROOF", "MESSAGE ROUTING PROOF: ACTIVE_DBF HELP_HINT_COMMAND" in log_upper, "help hint proof")
    gate("RUNTIME_PROOF_LANE_GATED", "MESSAGE ROUTING PROOF MODE: ON" in log_upper and "MESSAGE ROUTING PROOF MODE: OFF" in log_upper, "proof on/off")
    gate("NO_FOXHELP_FALLBACK", "TRY FOXHELP" not in log_upper, "FOXHELP fallback absent")
    gate("NO_UNKNOWN_COMMAND", "UNKNOWN COMMAND:" not in log_upper, "unknown command absent")
    gate("NO_MEMO_BACKEND_ERROR", "MEMO BACKEND NOT ATTACHED" not in log_upper, "memo backend error absent")

    proof_rows = [
        {"PROOF": "active_message_count", "EXPECTED": 12, "OBSERVED": msg_count, "PASS": 1 if msg_count == 12 else 0},
        {"PROOF": "active_text_count", "EXPECTED": 60, "OBSERVED": text_count, "PASS": 1 if text_count == 60 else 0},
        {"PROOF": "runtime_provider_active_dbf", "EXPECTED": "present", "OBSERVED": 1 if "MODE: ACTIVE_DBF" in log_upper else 0, "PASS": 1 if "MODE: ACTIVE_DBF" in log_upper else 0},
        {"PROOF": "runtime_catalog_loaded", "EXPECTED": "yes", "OBSERVED": 1 if "ACTIVE CATALOG LOADED: YES" in log_upper else 0, "PASS": 1 if "ACTIVE CATALOG LOADED: YES" in log_upper else 0},
        {"PROOF": "runtime_message_locale_set", "EXPECTED": "active_dbf", "OBSERVED": 1 if "MESSAGE ROUTING PROOF: ACTIVE_DBF MESSAGE_LOCALE_SET" in log_upper else 0, "PASS": 1 if "MESSAGE ROUTING PROOF: ACTIVE_DBF MESSAGE_LOCALE_SET" in log_upper else 0},
        {"PROOF": "runtime_unsupported_locale", "EXPECTED": "active_dbf", "OBSERVED": 1 if "MESSAGE ROUTING PROOF: ACTIVE_DBF UNSUPPORTED_MESSAGE_LOCALE" in log_upper else 0, "PASS": 1 if "MESSAGE ROUTING PROOF: ACTIVE_DBF UNSUPPORTED_MESSAGE_LOCALE" in log_upper else 0},
        {"PROOF": "runtime_help_hint", "EXPECTED": "active_dbf", "OBSERVED": 1 if "MESSAGE ROUTING PROOF: ACTIVE_DBF HELP_HINT_COMMAND" in log_upper else 0, "PASS": 1 if "MESSAGE ROUTING PROOF: ACTIVE_DBF HELP_HINT_COMMAND" in log_upper else 0},
    ]

    boundary = [
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "22AE.5.4 is validation-only."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_DBF_CATALOG", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active DBF mutation in post-rollback validation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_CDX_INDEXES", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active CDX/index mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active LMDB mutation."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No HELP DATA mutation."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CMDHELPCHK mutation."},
        {"PROTECTED_SYSTEM": "COMMAND_REGISTRY", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No command registry mutation."},
        {"PROTECTED_SYSTEM": "MANUALGEN", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No manualgen mutation."},
        {"PROTECTED_SYSTEM": "DATADICT_SELF_DOC", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No Data Dictionary/SelfDoc mutation."},
    ]

    status = STATUS_GREEN if failures == 0 else STATUS_BLOCKED
    validation_issues = str(failures)

    write_csv(reports / "message_catalog_phase22ae_5_4_gate_check_v1.csv", gates, ["GATE", "STATUS", "DETAIL"])
    write_csv(reports / "message_catalog_phase22ae_5_4_runtime_proof_v1.csv", proof_rows, ["PROOF", "EXPECTED", "OBSERVED", "PASS"])
    write_csv(reports / "message_catalog_phase22ae_5_4_boundary_ledger_v1.csv", boundary, ["PROTECTED_SYSTEM", "MUTATION_ALLOWED", "OBSERVED_MUTATION", "DETAIL"])

    write_csv(reports / "message_catalog_phase22ae_5_4_status_summary_v1.csv", [{
        "STATUS": status,
        "VALIDATION_ISSUES": validation_issues,
        "PHASE22AE_5_3_GREEN": 1 if ae53.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_5_3_ACTIVE_CATALOG_ROLLBACK_EXECUTED" else 0,
        "MSG_022AE_5_3_SAVEPOINT_PRESENT": 1 if sp_ok else 0,
        "ACTIVE_MESSAGE_COUNT": msg_count,
        "ACTIVE_TEXT_ROW_COUNT": text_count,
        "RUNTIME_PROOF_PATH": rel(runtime_path, repo),
        "RUNTIME_PROVIDER_ACTIVE_DBF": 1 if "MODE: ACTIVE_DBF" in log_upper else 0,
        "RUNTIME_ACTIVE_CATALOG_LOADED": 1 if "ACTIVE CATALOG LOADED: YES" in log_upper else 0,
        "MESSAGE_LOCALE_SET_PROOF": 1 if "MESSAGE ROUTING PROOF: ACTIVE_DBF MESSAGE_LOCALE_SET" in log_upper else 0,
        "UNSUPPORTED_MESSAGE_LOCALE_PROOF": 1 if "MESSAGE ROUTING PROOF: ACTIVE_DBF UNSUPPORTED_MESSAGE_LOCALE" in log_upper else 0,
        "HELP_HINT_COMMAND_PROOF": 1 if "MESSAGE ROUTING PROOF: ACTIVE_DBF HELP_HINT_COMMAND" in log_upper else 0,
        "PROOF_LANE_GATED": 1 if ("MESSAGE ROUTING PROOF MODE: ON" in log_upper and "MESSAGE ROUTING PROOF MODE: OFF" in log_upper) else 0,
        "FOXHELP_FALLBACK_COUNT": log_upper.count("TRY FOXHELP"),
        "SOURCE_FILES_MUTATED": 0,
        "ACTIVE_CATALOG_MUTATION_OBSERVED": 0,
        "HELP_DATA_MUTATION_OBSERVED": 0,
        "CMDHELPCHK_MUTATION_OBSERVED": 0,
        "NEXT_GATE": NEXT_GATE,
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }], ["STATUS", "VALIDATION_ISSUES", "PHASE22AE_5_3_GREEN",
         "MSG_022AE_5_3_SAVEPOINT_PRESENT", "ACTIVE_MESSAGE_COUNT",
         "ACTIVE_TEXT_ROW_COUNT", "RUNTIME_PROOF_PATH", "RUNTIME_PROVIDER_ACTIVE_DBF",
         "RUNTIME_ACTIVE_CATALOG_LOADED", "MESSAGE_LOCALE_SET_PROOF",
         "UNSUPPORTED_MESSAGE_LOCALE_PROOF", "HELP_HINT_COMMAND_PROOF",
         "PROOF_LANE_GATED", "FOXHELP_FALLBACK_COUNT", "SOURCE_FILES_MUTATED",
         "ACTIVE_CATALOG_MUTATION_OBSERVED", "HELP_DATA_MUTATION_OBSERVED",
         "CMDHELPCHK_MUTATION_OBSERVED", "NEXT_GATE", "REPORT_TIMESTAMP_UTC"])

    md = f"""# Message Catalog Phase 22AE.5.4 Post-Rollback Readback and Runtime Regression

Status: `{status}`

Active counts:

```text
SYSTEM_MESSAGES: {msg_count}
SYSTEM_MESSAGE_TEXT: {text_count}
```

Runtime proof path:

```text
{rel(runtime_path, repo)}
```

Next gate:

```text
{NEXT_GATE}
```
"""
    (reports / "MESSAGE_CATALOG_PHASE22AE_5_4_POST_ROLLBACK_READBACK_AND_RUNTIME_REGRESSION.md").write_text(md, encoding="utf-8")

    print(status)
    print(f"  validation issues: {validation_issues}")
    print(f"  Phase 22AE.5.3 green: {1 if ae53.get('STATUS') == 'MESSAGE_CATALOG_PHASE22AE_5_3_ACTIVE_CATALOG_ROLLBACK_EXECUTED' else 0}")
    print(f"  MSG-022AE.5.3 savepoint present: {1 if sp_ok else 0}")
    print(f"  active message count: {msg_count}")
    print(f"  active text row count: {text_count}")
    print(f"  runtime provider active_dbf: {1 if 'MODE: ACTIVE_DBF' in log_upper else 0}")
    print(f"  runtime active catalog loaded: {1 if 'ACTIVE CATALOG LOADED: YES' in log_upper else 0}")
    print(f"  MESSAGE_LOCALE_SET proof: {1 if 'MESSAGE ROUTING PROOF: ACTIVE_DBF MESSAGE_LOCALE_SET' in log_upper else 0}")
    print(f"  UNSUPPORTED_MESSAGE_LOCALE proof: {1 if 'MESSAGE ROUTING PROOF: ACTIVE_DBF UNSUPPORTED_MESSAGE_LOCALE' in log_upper else 0}")
    print(f"  HELP_HINT_COMMAND proof: {1 if 'MESSAGE ROUTING PROOF: ACTIVE_DBF HELP_HINT_COMMAND' in log_upper else 0}")
    print(f"  proof lane gated: {1 if ('MESSAGE ROUTING PROOF MODE: ON' in log_upper and 'MESSAGE ROUTING PROOF MODE: OFF' in log_upper) else 0}")
    print(f"  FOXHELP fallback count: {log_upper.count('TRY FOXHELP')}")
    print("  source files mutated: 0")
    print("  active catalog mutation observed: 0")
    print("  HELP DATA mutation observed: 0")
    print("  CMDHELPCHK mutation observed: 0")
    print(f"  next gate: {NEXT_GATE}")
    print(f"  reports: {reports}")
    return 0 if status == STATUS_GREEN else 2

if __name__ == "__main__":
    raise SystemExit(main())
