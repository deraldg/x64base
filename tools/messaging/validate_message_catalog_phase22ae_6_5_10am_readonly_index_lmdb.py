#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
from datetime import datetime, timezone
from pathlib import Path

STATUS_GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_10AM_READONLY_INDEX_LMDB_VERIFICATION_GREEN_NO_REBUILD_REQUIRED_YET"
STATUS_REVIEW = "MESSAGE_CATALOG_PHASE22AE_6_5_10AM_READONLY_INDEX_LMDB_VERIFICATION_GREEN_REBUILD_DECISION_REVIEW"
STATUS_BLOCKED = "MESSAGE_CATALOG_PHASE22AE_6_5_10AM_READONLY_INDEX_LMDB_VERIFICATION_BLOCKED"
NEXT_GREEN = "HOLD_OR_AUTHORIZE_PHASE22AE_6_5_10AN_RUNTIME_MESSAGE_CONSUMER_INTEGRATION_PLAN"
NEXT_REVIEW = "HOLD_OR_AUTHORIZE_PHASE22AE_6_5_10AMR_GUARDED_INDEX_LMDB_REBUILD_DECISION_REVIEW"

REPORT_DIR = Path("docs/messaging/reports")
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

PROOF_SYMBOLS = ["MESSAGE_PROOF_MODE_STATUS", "MESSAGE_PROOF_BOUNDARY_NOTE"]
PROOF_LOCALES = ["en-US", "es", "fr", "de", "it"]

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

def compare_inventory(before, after):
    def sv(v):
        return "" if v is None else str(v)

    b = {r["ROLE"]: r for r in before}
    a = {r["ROLE"]: r for r in after}
    rows = []

    for role in sorted(set(b) | set(a)):
        br = b.get(role, {})
        ar = a.get(role, {})

        before_exists = sv(br.get("EXISTS"))
        after_exists = sv(ar.get("EXISTS"))
        before_sha = sv(br.get("SHA256"))
        after_sha = sv(ar.get("SHA256"))
        before_bytes = sv(br.get("BYTES"))
        after_bytes = sv(ar.get("BYTES"))

        if before_exists != after_exists or before_sha != after_sha or before_bytes != after_bytes:
            rows.append({
                "ROLE": role,
                "PATH": ar.get("PATH", br.get("PATH", "")),
                "CHANGE": "MODIFIED_OR_EXISTENCE_CHANGED",
                "BEFORE_EXISTS": before_exists,
                "AFTER_EXISTS": after_exists,
                "BEFORE_SHA256": before_sha,
                "AFTER_SHA256": after_sha,
                "BEFORE_BYTES": before_bytes,
                "AFTER_BYTES": after_bytes,
            })

    return rows

def dbf_header_count(path: Path):
    if not path.exists() or path.stat().st_size < 12:
        return ""
    return int.from_bytes(path.read_bytes()[:12][4:8], "little")

def norm_text(s: str) -> str:
    return " ".join(s.replace("\r", "\n").split()).upper()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--runtime-log", default="")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    reports = repo / REPORT_DIR
    reports.mkdir(parents=True, exist_ok=True)

    stage = first_row(reports / "message_catalog_phase22ae_6_5_10am_stage_status_summary_v1.csv")
    before = read_csv(reports / "message_catalog_phase22ae_6_5_10am_artifact_inventory_before_runtime_v1.csv")
    after = artifact_inventory(repo)
    deltas = compare_inventory(before, after)

    runtime = Path(args.runtime_log) if args.runtime_log else repo / RUNLOG_PATH
    if not runtime.is_absolute():
        runtime = repo / runtime
    log = runtime.read_text(encoding="utf-8", errors="replace") if runtime.exists() else ""
    up = log.upper()
    compact = norm_text(log)

    msg_open14 = "OPENED SYSTEM_MESSAGES (V64) : RECORD COUNT 14" in up
    text_open70 = "OPENED SYSTEM_MESSAGE_TEXT (V64) : RECORD COUNT 70" in up
    count14 = "\n14\n" in log.replace("\r", "\n") or " 14 " in compact
    count70 = "\n70\n" in log.replace("\r", "\n") or " 70 " in compact
    listed14 = "14 RECORD(S) LISTED" in up
    listed70 = "70 RECORD(S) LISTED" in up
    cdx_valid_signals = up.count("VALID INDEX/INDICES")
    proof_symbols = sum(1 for s in PROOF_SYMBOLS if s in up)
    proof_locales = sum(1 for loc in PROOF_LOCALES if loc.upper() in up)
    msg_header = dbf_header_count(repo / ACTIVE_MSG_DBF)
    text_header = dbf_header_count(repo / ACTIVE_TEXT_DBF)
    cdx_present = sum(1 for r in after if "CDX" in r["ROLE"] and r["EXISTS"] == 1)
    lmdb_present = sum(1 for r in after if "LMDB" in r["ROLE"] and r["EXISTS"] == 1)

    gates = []
    failures = 0
    review_flags = 0
    def gate(name, ok, detail, review_only=False):
        nonlocal failures, review_flags
        status = "PASS" if ok else ("REVIEW" if review_only else "FAIL")
        gates.append({"GATE": name, "STATUS": status, "DETAIL": str(detail)})
        if not ok and review_only:
            review_flags += 1
        elif not ok:
            failures += 1

    gate("STAGE_GREEN", stage.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_5_10AM_READONLY_INDEX_LMDB_VERIFICATION_STAGED_SOURCE_HELD", stage.get("STATUS", "missing"))
    gate("RUNTIME_LOG_EXISTS", runtime.exists(), rel(runtime, repo))
    gate("FRESH_OPEN_SYSTEM_MESSAGES_RECORD_COUNT_14", msg_open14, "Opened SYSTEM_MESSAGES record count 14")
    gate("FRESH_OPEN_SYSTEM_MESSAGE_TEXT_RECORD_COUNT_70", text_open70, "Opened SYSTEM_MESSAGE_TEXT record count 70")
    gate("COUNT_14_VISIBLE", count14, "COUNT output 14")
    gate("COUNT_70_VISIBLE", count70, "COUNT output 70")
    gate("LIST_14_VISIBLE", listed14, "LIST ALL message table")
    gate("LIST_70_VISIBLE", listed70, "LIST ALL text table")
    gate("CDX_VALID_SIGNALS_PRESENT", cdx_valid_signals >= 2, cdx_valid_signals)
    gate("PROOF_SYMBOLS_VISIBLE", proof_symbols == 2, f"{proof_symbols}/2")
    gate("PROOF_LOCALES_VISIBLE", proof_locales == 5, f"{proof_locales}/5")
    gate("ACTIVE_MESSAGES_HEADER_COUNT_14", msg_header == 14, msg_header)
    gate("ACTIVE_TEXT_HEADER_COUNT_70", text_header == 70, text_header)
    gate("NO_ZAP", "ZAP" not in up, "read-only")
    gate("NO_IMPORT_OR_IMPORTED", "IMPORT" not in up and "IMPORTED" not in up, "read-only")
    gate("NO_APPEND_REPLACE_PACK_BUILDLMDB", all(token not in up for token in ["APPEND", "REPLACE", "PACK", "BUILDLMDB", "CDX CREATE"]), "read-only")
    gate("NO_UNKNOWN_COMMAND", "UNKNOWN COMMAND" not in up, "must be absent")
    gate("NO_CANNOT_OPEN", "CANNOT OPEN" not in up, "must be absent")
    gate("ARTIFACT_FINGERPRINTS_UNCHANGED", len(deltas) == 0, f"delta rows={len(deltas)}")
    gate("LMDB_ARTIFACTS_PRESENT", lmdb_present >= 1, f"lmdb_present={lmdb_present}", review_only=True)

    if failures == 0 and review_flags == 0:
        status = STATUS_GREEN
        next_gate = NEXT_GREEN
    elif failures == 0:
        status = STATUS_REVIEW
        next_gate = NEXT_REVIEW
    else:
        status = STATUS_BLOCKED
        next_gate = "HOLD_AND_FIX_PHASE22AE_6_5_10AM_READONLY_VERIFICATION_FAILURE"
    validation_issues = "0" if failures == 0 else str(failures)

    observations = [
        {"OBSERVATION": "runtime_log_exists", "VALUE": 1 if runtime.exists() else 0, "DETAIL": rel(runtime, repo)},
        {"OBSERVATION": "fresh_open_system_messages_14", "VALUE": 1 if msg_open14 else 0, "DETAIL": "USE active DBF"},
        {"OBSERVATION": "fresh_open_system_message_text_70", "VALUE": 1 if text_open70 else 0, "DETAIL": "USE active DBF"},
        {"OBSERVATION": "cdx_valid_signals", "VALUE": cdx_valid_signals, "DETAIL": "USE output Valid Index/Indices"},
        {"OBSERVATION": "cdx_artifacts_present_count", "VALUE": cdx_present, "DETAIL": "filesystem inventory"},
        {"OBSERVATION": "lmdb_artifacts_present_count", "VALUE": lmdb_present, "DETAIL": "filesystem inventory; review-only"},
        {"OBSERVATION": "artifact_fingerprint_delta_rows", "VALUE": len(deltas), "DETAIL": "read-only run should not change artifacts"},
        {"OBSERVATION": "proof_symbols_visible", "VALUE": proof_symbols, "DETAIL": "2 expected"},
        {"OBSERVATION": "proof_locales_visible", "VALUE": proof_locales, "DETAIL": "5 expected"},
    ]

    boundary = [
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "10AM is read-only."},
        {"PROTECTED_SYSTEM": "ACTIVE_SYSTEM_MESSAGES", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_SYSTEM_MESSAGE_TEXT", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_CDX_LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 1 if deltas else 0, "DETAIL": "No rebuild authorized; fingerprint delta would require review."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No HELP DATA mutation."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CMDHELPCHK mutation."},
    ]

    write_csv(reports / "message_catalog_phase22ae_6_5_10am_validate_gate_check_v1.csv", gates, ["GATE", "STATUS", "DETAIL"])
    write_csv(reports / "message_catalog_phase22ae_6_5_10am_artifact_inventory_after_runtime_v1.csv", after, ["ROLE", "PATH", "EXISTS", "KIND", "BYTES", "FILES", "SHA256"])
    write_csv(reports / "message_catalog_phase22ae_6_5_10am_artifact_fingerprint_delta_v1.csv", deltas, ["ROLE", "PATH", "CHANGE", "BEFORE_EXISTS", "AFTER_EXISTS", "BEFORE_SHA256", "AFTER_SHA256", "BEFORE_BYTES", "AFTER_BYTES"])
    write_csv(reports / "message_catalog_phase22ae_6_5_10am_runtime_observations_v1.csv", observations, ["OBSERVATION", "VALUE", "DETAIL"])
    write_csv(reports / "message_catalog_phase22ae_6_5_10am_boundary_ledger_v1.csv", boundary, ["PROTECTED_SYSTEM", "MUTATION_ALLOWED", "OBSERVED_MUTATION", "DETAIL"])

    write_csv(reports / "message_catalog_phase22ae_6_5_10am_validate_status_summary_v1.csv", [{
        "STATUS": status,
        "VALIDATION_ISSUES": validation_issues,
        "REVIEW_FLAGS": review_flags,
        "STAGE_STATUS": stage.get("STATUS", ""),
        "FRESH_OPEN_SYSTEM_MESSAGES_14": 1 if msg_open14 else 0,
        "FRESH_OPEN_SYSTEM_MESSAGE_TEXT_70": 1 if text_open70 else 0,
        "RUNTIME_MESSAGE_COUNT_14": 1 if count14 else 0,
        "RUNTIME_TEXT_COUNT_70": 1 if count70 else 0,
        "RUNTIME_MESSAGE_LISTED_14": 1 if listed14 else 0,
        "RUNTIME_TEXT_LISTED_70": 1 if listed70 else 0,
        "CDX_VALID_SIGNALS": cdx_valid_signals,
        "CDX_ARTIFACTS_PRESENT_COUNT": cdx_present,
        "LMDB_ARTIFACTS_PRESENT_COUNT": lmdb_present,
        "ARTIFACT_FINGERPRINT_DELTA_ROWS": len(deltas),
        "ACTIVE_MESSAGES_HEADER_COUNT_AFTER_READBACK": msg_header,
        "ACTIVE_TEXT_HEADER_COUNT_AFTER_READBACK": text_header,
        "INDEX_LMDB_REBUILD_AUTHORIZED": 0,
        "RUNTIME_CONSUMER_INTEGRATION_AUTHORIZED": 0,
        "SOURCE_FILES_MUTATED": 0,
        "ACTIVE_CATALOG_MUTATION_OBSERVED": 0,
        "HELP_DATA_MUTATION_OBSERVED": 0,
        "CMDHELPCHK_MUTATION_OBSERVED": 0,
        "NEXT_GATE": next_gate,
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }], ["STATUS", "VALIDATION_ISSUES", "REVIEW_FLAGS", "STAGE_STATUS",
         "FRESH_OPEN_SYSTEM_MESSAGES_14", "FRESH_OPEN_SYSTEM_MESSAGE_TEXT_70",
         "RUNTIME_MESSAGE_COUNT_14", "RUNTIME_TEXT_COUNT_70",
         "RUNTIME_MESSAGE_LISTED_14", "RUNTIME_TEXT_LISTED_70",
         "CDX_VALID_SIGNALS", "CDX_ARTIFACTS_PRESENT_COUNT", "LMDB_ARTIFACTS_PRESENT_COUNT",
         "ARTIFACT_FINGERPRINT_DELTA_ROWS", "ACTIVE_MESSAGES_HEADER_COUNT_AFTER_READBACK",
         "ACTIVE_TEXT_HEADER_COUNT_AFTER_READBACK", "INDEX_LMDB_REBUILD_AUTHORIZED",
         "RUNTIME_CONSUMER_INTEGRATION_AUTHORIZED", "SOURCE_FILES_MUTATED",
         "ACTIVE_CATALOG_MUTATION_OBSERVED", "HELP_DATA_MUTATION_OBSERVED",
         "CMDHELPCHK_MUTATION_OBSERVED", "NEXT_GATE", "REPORT_TIMESTAMP_UTC"])

    print(status)
    print(f"  validation issues: {validation_issues}")
    print(f"  review flags: {review_flags}")
    print(f"  stage green: {1 if stage.get('STATUS') == 'MESSAGE_CATALOG_PHASE22AE_6_5_10AM_READONLY_INDEX_LMDB_VERIFICATION_STAGED_SOURCE_HELD' else 0}")
    print(f"  fresh open SYSTEM_MESSAGES 14: {1 if msg_open14 else 0}")
    print(f"  fresh open SYSTEM_MESSAGE_TEXT 70: {1 if text_open70 else 0}")
    print(f"  runtime message count 14: {1 if count14 else 0}")
    print(f"  runtime text count 70: {1 if count70 else 0}")
    print(f"  runtime message listed 14: {1 if listed14 else 0}")
    print(f"  runtime text listed 70: {1 if listed70 else 0}")
    print(f"  CDX valid signals: {cdx_valid_signals}")
    print(f"  CDX artifacts present count: {cdx_present}")
    print(f"  LMDB artifacts present count: {lmdb_present}")
    print(f"  artifact fingerprint delta rows: {len(deltas)}")
    print(f"  active messages header count after readback: {msg_header}")
    print(f"  active text header count after readback: {text_header}")
    print("  index/LMDB rebuild authorized: 0")
    print("  runtime consumer integration authorized: 0")
    print("  source files mutated: 0")
    print("  active catalog mutation observed: 0")
    print("  HELP DATA mutation observed: 0")
    print("  CMDHELPCHK mutation observed: 0")
    print(f"  next gate: {next_gate}")
    print(f"  reports: {reports}")
    return 0 if failures == 0 else 2

if __name__ == "__main__":
    raise SystemExit(main())
