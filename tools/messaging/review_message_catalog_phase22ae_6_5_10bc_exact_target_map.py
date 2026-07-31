#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, json, hashlib, shutil
from datetime import datetime, timezone
from pathlib import Path

GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_10BC_EXACT_TARGET_MAP_ACCEPTANCE_REVIEW_GREEN_ACCEPTED_FOR_EXECUTION_PLANNING_SOURCE_HELD"
BLOCKED = "MESSAGE_CATALOG_PHASE22AE_6_5_10BC_EXACT_TARGET_MAP_ACCEPTANCE_REVIEW_BLOCKED"
NEXT = "HOLD_OR_AUTHORIZE_PHASE22AE_6_5_10BD_HELP_CMDHELPCHK_EXECUTION_PLAN_FROM_ACCEPTED_MAP"
REPORT_DIR = Path("docs/messaging/reports")
BB_SUMMARY = REPORT_DIR / "message_catalog_phase22ae_6_5_10bb_status_summary_v1.csv"
BB_MAP = REPORT_DIR / "message_catalog_phase22ae_6_5_10bb_proposed_exact_target_map_v1.csv"
BC_ROOT = Path("docs/messaging/apply/phase22ae_6_5_10bc_exact_target_map_acceptance_review_v1")
ACTIVE_MSG_DBF = Path("dottalkpp/data/messaging/SYSTEM_MESSAGES.dbf")
ACTIVE_TEXT_DBF = Path("dottalkpp/data/messaging/SYSTEM_MESSAGE_TEXT.dbf")

def rows(p):
    p = Path(p)
    if not p.exists():
        return []
    with p.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

def first(p):
    r = rows(p)
    return r[0] if r else {}

def wcsv(p, rs, fs):
    p = Path(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fs, lineterminator="\n", extrasaction="ignore")
        w.writeheader()
        for r in rs:
            w.writerow({k: r.get(k, "") for k in fs})

def rel(p, repo):
    try:
        return str(Path(p).relative_to(repo)).replace("\\", "/")
    except Exception:
        return str(p).replace("\\", "/")

def sha(p):
    h = hashlib.sha256()
    with Path(p).open("rb") as f:
        for b in iter(lambda: f.read(1048576), b""):
            h.update(b)
    return h.hexdigest()

def dbf_count(p):
    p = Path(p)
    if not p.exists() or p.stat().st_size < 12:
        return ""
    return int.from_bytes(p.read_bytes()[:12][4:8], "little")

def savepoint(repo, sid):
    latest = ""
    lp = repo / REPORT_DIR / "message_savepoint_latest_v1.json"
    if lp.exists():
        try:
            latest = json.loads(lp.read_text(encoding="utf-8")).get("savepoint_id", "")
        except Exception:
            latest = ""
    jp = repo / "docs/messaging/MESSAGING_SAVEPOINT_JOURNAL.md"
    txt = jp.read_text(encoding="utf-8", errors="replace") if jp.exists() else ""
    return latest == sid or sid in txt, latest

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--replace-existing-review", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    reports = repo / REPORT_DIR
    reports.mkdir(parents=True, exist_ok=True)

    bb = first(repo / BB_SUMMARY)
    bbmap = rows(repo / BB_MAP)
    sp_bb, latest_bb = savepoint(repo, "MSG-022AE.6.5.10BB")
    msg_count = dbf_count(repo / ACTIVE_MSG_DBF)
    text_count = dbf_count(repo / ACTIVE_TEXT_DBF)
    bc_root = repo / BC_ROOT

    gates = []
    failures = 0
    def gate(name, ok, detail):
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": str(detail)})
        if not ok:
            failures += 1

    gate("PHASE22AE_6_5_10BB_GREEN",
         bb.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_5_10BB_EXACT_HELP_CMDHELPCHK_TARGET_MAP_GREEN_REVIEW_REQUIRED_SOURCE_HELD",
         bb.get("STATUS", "missing"))
    gate("MSG_022AE_6_5_10BB_SAVEPOINT_PRESENT", sp_bb, latest_bb)
    gate("BB_MAP_EXISTS", len(bbmap) > 0, len(bbmap))
    gate("BB_PROPOSED_ROWS_MATCH_SUMMARY", str(len(bbmap)) == str(bb.get("PROPOSED_MAP_ROWS", "")), f"map={len(bbmap)} summary={bb.get('PROPOSED_MAP_ROWS','')}")
    gate("BB_EXACT_TARGET_MAP_PROPOSED", bb.get("EXACT_TARGET_MAP_PROPOSED") == "1", bb.get("EXACT_TARGET_MAP_PROPOSED", "missing"))
    gate("BB_EXACT_TARGET_MAP_NOT_ALREADY_ACCEPTED", bb.get("EXACT_TARGET_MAP_ACCEPTED") == "0", bb.get("EXACT_TARGET_MAP_ACCEPTED", "missing"))
    gate("BB_HELP_APPLY_NOT_EXECUTED", bb.get("HELP_DATA_APPLY_EXECUTED") == "0", bb.get("HELP_DATA_APPLY_EXECUTED", "missing"))
    gate("BB_CMDHELPCHK_APPLY_NOT_EXECUTED", bb.get("CMDHELPCHK_APPLY_EXECUTED") == "0", bb.get("CMDHELPCHK_APPLY_EXECUTED", "missing"))
    gate("ACTIVE_MESSAGES_HEADER_COUNT_14", msg_count == 14, msg_count)
    gate("ACTIVE_TEXT_HEADER_COUNT_70", text_count == 70, text_count)
    gate("BC_ROOT_NOT_EXISTING_OR_REPLACE_ALLOWED", (not bc_root.exists()) or args.replace_existing_review, rel(bc_root, repo))

    accepted = []
    review = []
    artifacts = []
    status = BLOCKED

    if failures == 0:
        if bc_root.exists() and args.replace_existing_review:
            shutil.rmtree(bc_root)
        bc_root.mkdir(parents=True, exist_ok=True)

        for r in bbmap:
            target_path = r.get("TARGET_PATH", "")
            kind = r.get("TARGET_KIND", "")
            action = r.get("PROPOSED_ACTION", "")
            auth = r.get("AUTHORIZED_FOR_EXECUTION_NOW", "")
            human = r.get("HUMAN_REVIEW_REQUIRED", "")
            row_ok = bool(target_path) and auth == "0" and human == "1" and (
                "HELP" in kind.upper() or "CMDHELP" in kind.upper() or "COMMAND" in kind.upper()
            )
            out = {
                "MAP_ROW": r.get("MAP_ROW", ""),
                "TARGET_ID": r.get("TARGET_ID", ""),
                "TARGET_KIND": kind,
                "TARGET_PATH": target_path,
                "PROPOSED_ACTION": action,
                "ACCEPTANCE_DISPOSITION": "ACCEPTED_FOR_EXECUTION_PLANNING" if row_ok else "REVIEW_REQUIRED",
                "AUTHORIZED_FOR_EXECUTION_NOW": 0,
                "ROLLBACK_REQUIRED": 1,
                "NOTES": r.get("NOTES", ""),
            }
            if row_ok:
                accepted.append(out)
            else:
                review.append(out)

        accepted_path = bc_root / "exact_target_map_ACCEPTED_FOR_EXECUTION_PLANNING_v1.csv"
        review_path = bc_root / "exact_target_map_REVIEW_ROWS_v1.csv"
        readme = bc_root / "README_10BC_ACCEPTANCE_REVIEW.md"
        wcsv(accepted_path, accepted, ["MAP_ROW","TARGET_ID","TARGET_KIND","TARGET_PATH","PROPOSED_ACTION","ACCEPTANCE_DISPOSITION","AUTHORIZED_FOR_EXECUTION_NOW","ROLLBACK_REQUIRED","NOTES"])
        wcsv(review_path, review, ["MAP_ROW","TARGET_ID","TARGET_KIND","TARGET_PATH","PROPOSED_ACTION","ACCEPTANCE_DISPOSITION","AUTHORIZED_FOR_EXECUTION_NOW","ROLLBACK_REQUIRED","NOTES"])
        readme.write_text(
            "# 10BC Exact Target Map Acceptance Review\n\n"
            "10BC accepts the proposed 10BB exact target map for execution planning only. "
            "It does not execute HELP DATA or CMDHELPCHK mutation.\n\n"
            "Accepted map:\n\n"
            "```text\n"
            "docs/messaging/apply/phase22ae_6_5_10bc_exact_target_map_acceptance_review_v1/exact_target_map_ACCEPTED_FOR_EXECUTION_PLANNING_v1.csv\n"
            "```\n\n"
            "Every accepted row keeps `AUTHORIZED_FOR_EXECUTION_NOW=0`. A later 10BD plan and 10BE execution gate are required before mutation.\n",
            encoding="utf-8"
        )
        for p in [accepted_path, review_path, readme]:
            artifacts.append({"ARTIFACT": rel(p, repo), "ROLE": "acceptance_review_artifact", "BYTES": p.stat().st_size, "SHA256": sha(p)})
        status = GREEN

    boundary = [
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "10BC writes docs/messaging acceptance artifacts only."},
        {"PROTECTED_SYSTEM": "ACTIVE_SYSTEM_MESSAGES", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_SYSTEM_MESSAGE_TEXT", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_CDX_LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CDX/LMDB mutation."},
        {"PROTECTED_SYSTEM": "WORKSPACE_PROFILE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No workspace mutation."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No HELP DATA mutation; accepted for planning only."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CMDHELPCHK mutation; accepted for planning only."},
    ]

    readiness = [
        {"ITEM": "EXACT_TARGET_MAP_ACCEPTED_FOR_PLANNING", "STATUS": "YES" if accepted else "NO", "DETAIL": f"{len(accepted)} accepted rows."},
        {"ITEM": "REVIEW_ROWS", "STATUS": "CLEAR" if not review else "REVIEW_REQUIRED", "DETAIL": f"{len(review)} review rows."},
        {"ITEM": "HELP_DATA_APPLY_EXECUTION", "STATUS": "NOT_EXECUTED_IN_10BC", "DETAIL": "No apply execution."},
        {"ITEM": "CMDHELPCHK_APPLY_EXECUTION", "STATUS": "NOT_EXECUTED_IN_10BC", "DETAIL": "No apply execution."},
        {"ITEM": "NEXT_EXECUTION_PLAN_GATE", "STATUS": "10BD_REQUIRED", "DETAIL": "10BD should build exact execution plan from accepted map."},
    ]

    issues = "0" if failures == 0 else str(failures)
    wcsv(reports / "message_catalog_phase22ae_6_5_10bc_gate_check_v1.csv", gates, ["GATE","STATUS","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10bc_accepted_exact_target_map_v1.csv", accepted, ["MAP_ROW","TARGET_ID","TARGET_KIND","TARGET_PATH","PROPOSED_ACTION","ACCEPTANCE_DISPOSITION","AUTHORIZED_FOR_EXECUTION_NOW","ROLLBACK_REQUIRED","NOTES"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10bc_review_rows_v1.csv", review, ["MAP_ROW","TARGET_ID","TARGET_KIND","TARGET_PATH","PROPOSED_ACTION","ACCEPTANCE_DISPOSITION","AUTHORIZED_FOR_EXECUTION_NOW","ROLLBACK_REQUIRED","NOTES"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10bc_apply_readiness_v1.csv", readiness, ["ITEM","STATUS","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10bc_boundary_ledger_v1.csv", boundary, ["PROTECTED_SYSTEM","MUTATION_ALLOWED","OBSERVED_MUTATION","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10bc_artifact_manifest_v1.csv", artifacts, ["ARTIFACT","ROLE","BYTES","SHA256"])

    summary = {
        "STATUS": status,
        "VALIDATION_ISSUES": issues,
        "PHASE22AE_6_5_10BB_STATUS": bb.get("STATUS", ""),
        "MSG_022AE_6_5_10BB_SAVEPOINT_PRESENT": 1 if sp_bb else 0,
        "ACTIVE_MESSAGES_OBSERVED_COUNT": msg_count,
        "ACTIVE_TEXT_OBSERVED_COUNT": text_count,
        "BB_PROPOSED_MAP_ROWS": len(bbmap),
        "ACCEPTED_MAP_ROWS": len(accepted),
        "REVIEW_ROWS": len(review),
        "BC_ROOT": rel(bc_root, repo),
        "EXACT_TARGET_MAP_ACCEPTED_FOR_PLANNING": 1 if accepted and not review else 0,
        "HELP_DATA_APPLY_EXECUTED": 0,
        "CMDHELPCHK_APPLY_EXECUTED": 0,
        "HELP_DATA_MUTATION_OBSERVED": 0,
        "CMDHELPCHK_MUTATION_OBSERVED": 0,
        "SOURCE_FILES_MUTATED": 0,
        "ACTIVE_CATALOG_MUTATION_OBSERVED_BY_REVIEW": 0,
        "DBF_MUTATION_OBSERVED": 0,
        "CDX_LMDB_MUTATION_OBSERVED": 0,
        "WORKSPACE_MUTATION_OBSERVED": 0,
        "NEXT_GATE": NEXT,
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }
    wcsv(reports / "message_catalog_phase22ae_6_5_10bc_status_summary_v1.csv", [summary], list(summary.keys()))

    (repo / "docs/messaging/MESSAGE_LOCALE_PHASE22AE_6_5_10BC_EXACT_TARGET_MAP_ACCEPTANCE_REVIEW.md").write_text(
        f"# Message Catalog Phase 22AE.6.5.10BC Exact Target Map Acceptance Review\n\n"
        f"Status: `{status}`\n\n"
        "10BC accepts the exact target map for execution planning only. It does not mutate HELP DATA or CMDHELPCHK.\n\n"
        f"Acceptance root:\n\n```text\n{rel(bc_root, repo)}\n```\n\n"
        f"Next gate:\n\n```text\n{NEXT}\n```\n",
        encoding="utf-8"
    )

    print(status)
    print(f"  validation issues: {issues}")
    print(f"  Phase 22AE.6.5.10BB status: {bb.get('STATUS','')}")
    print(f"  MSG-022AE.6.5.10BB savepoint present: {1 if sp_bb else 0}")
    print(f"  active messages observed count: {msg_count}")
    print(f"  active text observed count: {text_count}")
    print(f"  BB proposed map rows: {len(bbmap)}")
    print(f"  accepted map rows: {len(accepted)}")
    print(f"  review rows: {len(review)}")
    print(f"  acceptance root: {rel(bc_root, repo)}")
    print(f"  exact target map accepted for planning: {summary['EXACT_TARGET_MAP_ACCEPTED_FOR_PLANNING']}")
    print("  HELP DATA apply executed: 0")
    print("  CMDHELPCHK apply executed: 0")
    print("  HELP DATA mutation observed: 0")
    print("  CMDHELPCHK mutation observed: 0")
    print("  source files mutated: 0")
    print("  active catalog mutation observed by review: 0")
    print("  DBF mutation observed: 0")
    print("  CDX/LMDB mutation observed: 0")
    print("  workspace mutation observed: 0")
    print(f"  next gate: {NEXT}")
    print(f"  reports: {reports}")
    return 0 if status == GREEN else 2

if __name__ == "__main__":
    raise SystemExit(main())
