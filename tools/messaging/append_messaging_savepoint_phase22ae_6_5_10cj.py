#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from datetime import datetime
from pathlib import Path

PHASE = "22AE.6.5.10CJ"
SAVEPOINT = "MSG-022AE.6.5.10CJ"
GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_10CJ_NATIVE_WRITER_DECISION_SELECTION_PACKAGE_GREEN_OPTION_B_REUSE_WITH_WRAPPER_CONTRACT_SELECTED_SOURCE_HELD"

def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""

def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")

def read_summary(repo: Path) -> dict:
    path = repo / "docs/messaging/reports/message_catalog_phase22ae_6_5_10cj_status_summary_v1.csv"
    rows = []
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as f:
            rows = list(csv.DictReader(f))
    except Exception:
        return {}
    return rows[0] if rows else {}

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--accept-messaging-savepoint", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    summary = read_summary(repo)
    status = summary.get("STATUS", "")
    if not args.accept_messaging_savepoint:
        print("[MSG-022AE.6.5.10CJ] Refusing savepoint without --accept-messaging-savepoint.")
        return 1
    if status != GREEN:
        print(f"[MSG-022AE.6.5.10CJ] Status is not green: {status}")
        return 1

    journal = repo / "docs/messaging/MESSAGING_SAVEPOINT_JOURNAL.md"
    old = read_text(journal)
    if SAVEPOINT in old:
        print("[MSG-022AE.6.5.10CJ] Messaging savepoint already appears in journal; refusing duplicate append.")
        return 0

    entry = f"""
## {SAVEPOINT} — {status}

- Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- Phase: {PHASE}
- Selected option: {summary.get('SELECTED_OPTION','')}
- Reuse path selected now: {summary.get('REUSE_PATH_SELECTED_NOW','')}
- Reuse path confirmed now: {summary.get('REUSE_PATH_CONFIRMED_NOW','')}
- Source patch needed proven: {summary.get('SOURCE_PATCH_NEEDED_PROVEN','')}
- Source mutation authorized now: {summary.get('SOURCE_MUTATION_AUTHORIZED_NOW','')}
- Apply execution authorized now: {summary.get('APPLY_EXECUTION_AUTHORIZED_NOW','')}
- HELP DATA apply executed: {summary.get('HELP_DATA_APPLY_EXECUTED','')}
- CMDHELPCHK apply executed: {summary.get('CMDHELPCHK_APPLY_EXECUTED','')}
- Source files mutated: {summary.get('SOURCE_FILES_MUTATED','')}
- Active catalog mutation observed by selection: {summary.get('ACTIVE_CATALOG_MUTATION_OBSERVED_BY_SELECTION','')}
- Next gate: {summary.get('NEXT_GATE','')}

"""
    write_text(journal, old.rstrip() + "\n\n" + entry.lstrip())

    latest = repo / "docs/messaging/reports/message_savepoint_latest_v1.json"
    latest_json = {
        "savepoint": SAVEPOINT,
        "phase": PHASE,
        "status": status,
        "selected_option": summary.get("SELECTED_OPTION",""),
        "next_gate": summary.get("NEXT_GATE",""),
    }
    write_text(latest, json_dumps(latest_json))

    print("[MSG-022AE.6.5.10CJ] Messaging savepoint appended.")
    print(f"  journal: {journal}")
    print(f"  latest: {latest}")
    return 0

def json_dumps(obj) -> str:
    import json
    return json.dumps(obj, indent=2) + "\n"

if __name__ == "__main__":
    raise SystemExit(main())
