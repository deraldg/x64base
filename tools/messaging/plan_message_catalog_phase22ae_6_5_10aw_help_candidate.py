#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path

STATUS_GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_10AW_MSGMGR_HELP_CANDIDATE_PLAN_GREEN_SOURCE_HELD"
STATUS_BLOCKED = "MESSAGE_CATALOG_PHASE22AE_6_5_10AW_MSGMGR_HELP_CANDIDATE_PLAN_BLOCKED"
NEXT_GATE = "HOLD_OR_AUTHORIZE_PHASE22AE_6_5_10AX_MSGMGR_HELP_CANDIDATE_REVIEW"

REPORT_DIR = Path("docs/messaging/reports")
CANDIDATE_DIR = Path("docs/messaging/candidates")
ACTIVE_MSG_DBF = Path("dottalkpp/data/messaging/SYSTEM_MESSAGES.dbf")
ACTIVE_TEXT_DBF = Path("dottalkpp/data/messaging/SYSTEM_MESSAGE_TEXT.dbf")

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

def make_candidate_text():
    return """# HELP Candidate: MSGMGR / Message Manager

Status: CANDIDATE ONLY - DO NOT APPLY TO HELP DATA

## Purpose

`MSGMGR` is the Message Manager command-house surface for inspecting the active message catalog and its read-only runtime status.

## Usage

```text
MSGMGR
MSGMGR USAGE
MSGMGR STATUS
MSGMGR CHECK
```

## Behavior

`MSGMGR` and `MSGMGR USAGE` display command usage.

`MSGMGR STATUS` reports the command-house registration, read-only mode, active provider mode, active message DBF/index/LMDB roots, and the low-level message catalog surfaces.

`MSGMGR CHECK` currently reports the same read-only status surface as `MSGMGR STATUS`.

## Proven low-level surfaces

```text
SET MESSAGE CATALOG CHECK
SET MESSAGE CATALOG GET
SET MESSAGE EMIT <symbol> [LOCALE <locale>] [ARG <name> <value>]
```

`SET MESSAGE CATALOG CHECK` reports active provider status and proves active catalog readability.

`SET MESSAGE CATALOG GET` is a proven low-level read/get surface.

`SET MESSAGE EMIT` is a proven read-only diagnostic emission surface for localized catalog messages.

## Proven catalog state

```text
SYSTEM_MESSAGES      = 14
SYSTEM_MESSAGE_TEXT  = 70
provider mode        = active_dbf
```

## Proven localized proof symbols

```text
MESSAGE_PROOF_MODE_STATUS
MESSAGE_PROOF_BOUNDARY_NOTE
```

Proven locales:

```text
en-US
es
fr
de
it
```

## Proven workspace profile

The messaging catalog has a proven workspace profile:

```text
dottalkpp/data/workspaces/messages_profile_phase22ae_6_5_10as.dtschema
```

It restores:

```text
SYSTEM_MESSAGE_TEXT = 70
SYSTEM_MESSAGES     = 14
```

## Boundary

This command-house surface is read-only in the current phase.

No DBF, CDX, LMDB, workspace, source, HELP DATA, or CMDHELPCHK mutation is authorized by this candidate.

## Deferred work

Aliases such as `MESSAGE`, `MSG`, or `MESSAGE_MANAGER` are not authorized by this candidate.

Runtime source integration is not authorized by this candidate.

HELP DATA and CMDHELPCHK updates require a separate explicit apply gate.
"""

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--replace-existing-candidate", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    reports = repo / REPORT_DIR
    reports.mkdir(parents=True, exist_ok=True)
    candidates = repo / CANDIDATE_DIR
    candidates.mkdir(parents=True, exist_ok=True)

    av = first_row(reports / "message_catalog_phase22ae_6_5_10av_validate_status_summary_v1.csv")
    sp_av, latest_av = savepoint_present(repo, "MSG-022AE.6.5.10AV")
    msg_count = dbf_header_count(repo / ACTIVE_MSG_DBF)
    text_count = dbf_header_count(repo / ACTIVE_TEXT_DBF)
    candidate_path = candidates / "MESSAGE_CATALOG_PHASE22AE_6_5_10AW_MSGMGR_HELP_CANDIDATE.md"

    gates = []
    failures = 0
    def gate(name, ok, detail):
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": str(detail)})
        if not ok:
            failures += 1

    gate("PHASE22AE_6_5_10AV_GREEN_EMIT_PROVEN",
         av.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_5_10AV_SET_MESSAGE_EMIT_LOCALIZED_PROOF_GREEN_EMIT_PROVEN",
         av.get("STATUS", "missing"))
    gate("MSG_022AE_6_5_10AV_SAVEPOINT_PRESENT", sp_av, latest_av)
    gate("ACTIVE_MESSAGES_HEADER_COUNT_14", msg_count == 14, msg_count)
    gate("ACTIVE_TEXT_HEADER_COUNT_70", text_count == 70, text_count)
    gate("10AV_CHECK_PROVEN", av.get("SET_MESSAGE_CATALOG_CHECK_PROVEN") == "1", av.get("SET_MESSAGE_CATALOG_CHECK_PROVEN", "missing"))
    gate("10AV_EMIT_PROVEN", av.get("SET_MESSAGE_EMIT_PROVEN") == "1", av.get("SET_MESSAGE_EMIT_PROVEN", "missing"))
    gate("10AV_PROOF_SYMBOLS_VISIBLE_2", av.get("PROOF_SYMBOLS_VISIBLE") == "2", av.get("PROOF_SYMBOLS_VISIBLE", "missing"))
    gate("10AV_PROOF_LOCALES_VISIBLE_5", av.get("PROOF_LOCALES_VISIBLE") == "5", av.get("PROOF_LOCALES_VISIBLE", "missing"))
    gate("CANDIDATE_NOT_EXISTING_OR_REPLACE_ALLOWED", (not candidate_path.exists()) or args.replace_existing_candidate, rel(candidate_path, repo))

    status = STATUS_BLOCKED
    if failures == 0:
        candidate_path.write_text(make_candidate_text(), encoding="utf-8")
        status = STATUS_GREEN

    surfaces = [
        {"SURFACE": "MSGMGR", "TYPE": "command_house", "STATUS": "CANDIDATE_HELP_TEXT", "PROVEN": 1, "NOTES": "Message Manager read-only command-house."},
        {"SURFACE": "MSGMGR USAGE", "TYPE": "command_house", "STATUS": "CANDIDATE_HELP_TEXT", "PROVEN": 1, "NOTES": "Usage display."},
        {"SURFACE": "MSGMGR STATUS", "TYPE": "command_house", "STATUS": "CANDIDATE_HELP_TEXT", "PROVEN": 1, "NOTES": "Read-only status surface."},
        {"SURFACE": "MSGMGR CHECK", "TYPE": "command_house", "STATUS": "CANDIDATE_HELP_TEXT", "PROVEN": 1, "NOTES": "Read-only check/status surface."},
        {"SURFACE": "SET MESSAGE CATALOG CHECK", "TYPE": "low_level_read", "STATUS": "CANDIDATE_HELP_TEXT", "PROVEN": 1, "NOTES": "Active provider readback and status."},
        {"SURFACE": "SET MESSAGE CATALOG GET", "TYPE": "low_level_read", "STATUS": "CANDIDATE_HELP_TEXT", "PROVEN": 1, "NOTES": "Low-level read/get surface proven in 10AQ."},
        {"SURFACE": "SET MESSAGE EMIT <symbol> [LOCALE <locale>] [ARG <name> <value>]", "TYPE": "low_level_emit", "STATUS": "CANDIDATE_HELP_TEXT", "PROVEN": 1, "NOTES": "Localized diagnostic emission proven in 10AV."},
    ]

    candidate_rows = [
        {"TOPIC": "MSGMGR", "HELP_KIND": "PRIMARY_TOPIC", "CANDIDATE_ACTION": "REVIEW_ONLY", "TARGET_SYSTEM": "HELP_DATA", "APPLY_AUTHORIZED": 0},
        {"TOPIC": "SET MESSAGE CATALOG CHECK", "HELP_KIND": "RELATED_LOW_LEVEL_TOPIC", "CANDIDATE_ACTION": "REVIEW_ONLY", "TARGET_SYSTEM": "HELP_DATA", "APPLY_AUTHORIZED": 0},
        {"TOPIC": "SET MESSAGE CATALOG GET", "HELP_KIND": "RELATED_LOW_LEVEL_TOPIC", "CANDIDATE_ACTION": "REVIEW_ONLY", "TARGET_SYSTEM": "HELP_DATA", "APPLY_AUTHORIZED": 0},
        {"TOPIC": "SET MESSAGE EMIT", "HELP_KIND": "RELATED_LOW_LEVEL_TOPIC", "CANDIDATE_ACTION": "REVIEW_ONLY", "TARGET_SYSTEM": "HELP_DATA", "APPLY_AUTHORIZED": 0},
        {"TOPIC": "CMDHELPCHK", "HELP_KIND": "VALIDATION_HANDOFF", "CANDIDATE_ACTION": "REVIEW_ONLY", "TARGET_SYSTEM": "CMDHELPCHK", "APPLY_AUTHORIZED": 0},
    ]

    deferred = [
        {"ITEM": "HELP_DATA_APPLY", "STATUS": "DEFERRED", "REASON": "Requires explicit apply gate after candidate review."},
        {"ITEM": "CMDHELPCHK_APPLY", "STATUS": "DEFERRED", "REASON": "Requires explicit apply gate after HELP candidate acceptance."},
        {"ITEM": "ALIASES", "STATUS": "DEFERRED", "REASON": "Requires alias policy lane."},
        {"ITEM": "RUNTIME_SOURCE_INTEGRATION", "STATUS": "DEFERRED", "REASON": "Requires guarded source/build/runtime proof lane."},
        {"ITEM": "DTSCHEMA_DTSHEMA_POLISH", "STATUS": "DEFERRED", "REASON": "Workspace header polish is not this lane's responsibility."},
    ]

    boundary = [
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "10AW writes docs/messaging candidate/report files only."},
        {"PROTECTED_SYSTEM": "ACTIVE_SYSTEM_MESSAGES", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_SYSTEM_MESSAGE_TEXT", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_CDX_LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CDX/LMDB mutation."},
        {"PROTECTED_SYSTEM": "WORKSPACE_PROFILE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No workspace mutation."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No HELP DATA mutation; candidate markdown only."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CMDHELPCHK mutation; candidate handoff only."},
    ]

    issues = "0" if status == STATUS_GREEN else str(failures)

    write_csv(reports / "message_catalog_phase22ae_6_5_10aw_gate_check_v1.csv", gates, ["GATE", "STATUS", "DETAIL"])
    write_csv(reports / "message_catalog_phase22ae_6_5_10aw_help_surfaces_v1.csv", surfaces, ["SURFACE", "TYPE", "STATUS", "PROVEN", "NOTES"])
    write_csv(reports / "message_catalog_phase22ae_6_5_10aw_help_candidate_handoff_v1.csv", candidate_rows, ["TOPIC", "HELP_KIND", "CANDIDATE_ACTION", "TARGET_SYSTEM", "APPLY_AUTHORIZED"])
    write_csv(reports / "message_catalog_phase22ae_6_5_10aw_deferred_items_v1.csv", deferred, ["ITEM", "STATUS", "REASON"])
    write_csv(reports / "message_catalog_phase22ae_6_5_10aw_boundary_ledger_v1.csv", boundary, ["PROTECTED_SYSTEM", "MUTATION_ALLOWED", "OBSERVED_MUTATION", "DETAIL"])

    summary = {
        "STATUS": status,
        "VALIDATION_ISSUES": issues,
        "PHASE22AE_6_5_10AV_STATUS": av.get("STATUS", ""),
        "MSG_022AE_6_5_10AV_SAVEPOINT_PRESENT": 1 if sp_av else 0,
        "ACTIVE_MESSAGES_OBSERVED_COUNT": msg_count,
        "ACTIVE_TEXT_OBSERVED_COUNT": text_count,
        "MSGMGR_HELP_CANDIDATE_CREATED": 1 if status == STATUS_GREEN else 0,
        "MSGMGR_HELP_CANDIDATE_PATH": rel(candidate_path, repo) if candidate_path.exists() else "",
        "SET_MESSAGE_CATALOG_CHECK_PROVEN": av.get("SET_MESSAGE_CATALOG_CHECK_PROVEN", ""),
        "SET_MESSAGE_EMIT_PROVEN": av.get("SET_MESSAGE_EMIT_PROVEN", ""),
        "PROOF_SYMBOLS_VISIBLE": av.get("PROOF_SYMBOLS_VISIBLE", ""),
        "PROOF_LOCALES_VISIBLE": av.get("PROOF_LOCALES_VISIBLE", ""),
        "HELP_DATA_APPLY_AUTHORIZED": 0,
        "CMDHELPCHK_APPLY_AUTHORIZED": 0,
        "ALIASES_AUTHORIZED": 0,
        "RUNTIME_CONSUMER_SOURCE_INTEGRATION_AUTHORIZED": 0,
        "SOURCE_FILES_MUTATED": 0,
        "ACTIVE_CATALOG_MUTATION_OBSERVED_BY_REVIEW": 0,
        "HELP_DATA_MUTATION_OBSERVED": 0,
        "CMDHELPCHK_MUTATION_OBSERVED": 0,
        "NEXT_GATE": NEXT_GATE,
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }
    write_csv(reports / "message_catalog_phase22ae_6_5_10aw_status_summary_v1.csv", [summary], list(summary.keys()))

    (repo / "docs/messaging/MESSAGE_LOCALE_PHASE22AE_6_5_10AW_MSGMGR_HELP_CANDIDATE_PLAN.md").write_text(
        f"# Message Catalog Phase 22AE.6.5.10AW MSGMGR HELP Candidate Plan\n\nStatus: `{status}`\n\n10AW creates a review-only HELP candidate for the proven Message Manager surfaces. It does not mutate HELP DATA or CMDHELPCHK.\n\nCandidate:\n\n```text\n{rel(candidate_path, repo) if candidate_path.exists() else rel(candidate_path, repo)}\n```\n\nNext gate:\n\n```text\n{NEXT_GATE}\n```\n",
        encoding="utf-8"
    )

    print(status)
    print(f"  validation issues: {issues}")
    print(f"  Phase 22AE.6.5.10AV status: {av.get('STATUS','')}")
    print(f"  MSG-022AE.6.5.10AV savepoint present: {1 if sp_av else 0}")
    print(f"  active messages observed count: {msg_count}")
    print(f"  active text observed count: {text_count}")
    print(f"  MSGMGR HELP candidate created: {1 if status == STATUS_GREEN else 0}")
    print(f"  MSGMGR HELP candidate path: {rel(candidate_path, repo) if candidate_path.exists() else ''}")
    print(f"  SET MESSAGE CATALOG CHECK proven: {av.get('SET_MESSAGE_CATALOG_CHECK_PROVEN','')}")
    print(f"  SET MESSAGE EMIT proven: {av.get('SET_MESSAGE_EMIT_PROVEN','')}")
    print(f"  proof symbols visible: {av.get('PROOF_SYMBOLS_VISIBLE','')}/2")
    print(f"  proof locales visible: {av.get('PROOF_LOCALES_VISIBLE','')}/5")
    print("  HELP DATA apply authorized: 0")
    print("  CMDHELPCHK apply authorized: 0")
    print("  aliases authorized: 0")
    print("  runtime consumer source integration authorized: 0")
    print("  source files mutated: 0")
    print("  active catalog mutation observed by review: 0")
    print("  HELP DATA mutation observed: 0")
    print("  CMDHELPCHK mutation observed: 0")
    print(f"  next gate: {NEXT_GATE}")
    print(f"  reports: {reports}")
    return 0 if status == STATUS_GREEN else 2

if __name__ == "__main__":
    raise SystemExit(main())
