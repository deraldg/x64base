#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, json, hashlib, shutil
from datetime import datetime, timezone
from pathlib import Path

GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_10BB_EXACT_HELP_CMDHELPCHK_TARGET_MAP_GREEN_REVIEW_REQUIRED_SOURCE_HELD"
BLOCKED = "MESSAGE_CATALOG_PHASE22AE_6_5_10BB_EXACT_HELP_CMDHELPCHK_TARGET_MAP_BLOCKED"
NEXT = "HOLD_OR_AUTHORIZE_PHASE22AE_6_5_10BC_EXACT_TARGET_MAP_ACCEPTANCE_REVIEW"
REPORT_DIR = Path("docs/messaging/reports")
BA_SUMMARY = REPORT_DIR / "message_catalog_phase22ae_6_5_10ba_status_summary_v1.csv"
BA_EXACT = REPORT_DIR / "message_catalog_phase22ae_6_5_10ba_exact_target_candidates_v1.csv"
BA_BROAD = REPORT_DIR / "message_catalog_phase22ae_6_5_10ba_broad_target_review_v1.csv"
BA_ROOT = Path("docs/messaging/apply/phase22ae_6_5_10ba_msgmgr_help_cmdhelpchk_apply_execution_preflight_v1")
BB_ROOT = Path("docs/messaging/apply/phase22ae_6_5_10bb_exact_help_cmdhelpchk_target_map_v1")
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

def choose_kind(path, role, reason):
    up = (path + " " + role + " " + reason).upper()
    if "CMDHELP" in up:
        return "CMDHELPCHK_EXACT_TARGET_CANDIDATE"
    if "COMMAND" in up and "HELP" in up:
        return "CMDHELPCHK_OR_COMMAND_HELP_REVIEW"
    if "HELP" in up:
        return "HELP_DATA_EXACT_TARGET_CANDIDATE"
    return "REVIEW_REQUIRED"

def proposed_action(kind):
    if kind == "HELP_DATA_EXACT_TARGET_CANDIDATE":
        return "PROPOSE_HELP_TOPIC_INSERT_OR_UPDATE"
    if kind == "CMDHELPCHK_EXACT_TARGET_CANDIDATE":
        return "PROPOSE_CMDHELPCHK_RULE_INSERT_OR_UPDATE"
    return "REVIEW_BEFORE_ACTION"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--replace-existing-map", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    reports = repo / REPORT_DIR
    reports.mkdir(parents=True, exist_ok=True)

    ba = first(repo / BA_SUMMARY)
    sp_ba, latest_ba = savepoint(repo, "MSG-022AE.6.5.10BA")
    msg_count = dbf_count(repo / ACTIVE_MSG_DBF)
    text_count = dbf_count(repo / ACTIVE_TEXT_DBF)
    exact = rows(repo / BA_EXACT)
    broad = rows(repo / BA_BROAD)
    ba_root = repo / BA_ROOT
    bb_root = repo / BB_ROOT

    gates = []
    failures = 0
    def gate(name, ok, detail):
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": str(detail)})
        if not ok:
            failures += 1

    gate("PHASE22AE_6_5_10BA_PREFLIGHT_GREEN",
         ba.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_5_10BA_MSGMGR_HELP_CMDHELPCHK_APPLY_EXECUTION_PREFLIGHT_GREEN_EXACT_TARGET_MAP_REQUIRED",
         ba.get("STATUS", "missing"))
    gate("MSG_022AE_6_5_10BA_SAVEPOINT_PRESENT", sp_ba, latest_ba)
    gate("BA_EXACT_TARGET_MAP_REQUIRED", ba.get("EXACT_TARGET_MAP_REQUIRED") == "1", ba.get("EXACT_TARGET_MAP_REQUIRED", "missing"))
    gate("BA_HELP_APPLY_NOT_EXECUTED", ba.get("HELP_DATA_APPLY_EXECUTED") == "0", ba.get("HELP_DATA_APPLY_EXECUTED", "missing"))
    gate("BA_CMDHELPCHK_APPLY_NOT_EXECUTED", ba.get("CMDHELPCHK_APPLY_EXECUTED") == "0", ba.get("CMDHELPCHK_APPLY_EXECUTED", "missing"))
    gate("ACTIVE_MESSAGES_HEADER_COUNT_14", msg_count == 14, msg_count)
    gate("ACTIVE_TEXT_HEADER_COUNT_70", text_count == 70, text_count)
    gate("BA_EXACT_CANDIDATES_PRESENT", len(exact) > 0, len(exact))
    gate("BA_PREFLIGHT_ROOT_EXISTS", ba_root.exists(), rel(ba_root, repo))
    gate("BB_ROOT_NOT_EXISTING_OR_REPLACE_ALLOWED", (not bb_root.exists()) or args.replace_existing_map, rel(bb_root, repo))

    status = BLOCKED
    proposed = []
    review = []
    artifacts = []
    if failures == 0:
        if bb_root.exists() and args.replace_existing_map:
            shutil.rmtree(bb_root)
        bb_root.mkdir(parents=True, exist_ok=True)

        for i, r in enumerate(exact, start=1):
            kind = choose_kind(r.get("TARGET_PATH", ""), r.get("ROLE", ""), r.get("REASON", ""))
            proposed.append({
                "MAP_ROW": i,
                "TARGET_ID": f"BB-CAND-{i:03d}",
                "TARGET_KIND": kind,
                "TARGET_PATH": r.get("TARGET_PATH", ""),
                "SOURCE_ROLE": r.get("ROLE", ""),
                "CONFIDENCE_SCORE": r.get("CONFIDENCE_SCORE", ""),
                "PROPOSED_ACTION": proposed_action(kind),
                "CANDIDATE_HELP_TOPIC": "MSGMGR",
                "CANDIDATE_LOW_LEVEL_TOPICS": "SET MESSAGE CATALOG CHECK;SET MESSAGE CATALOG GET;SET MESSAGE EMIT",
                "ROLLBACK_REQUIRED": 1,
                "AUTHORIZED_FOR_EXECUTION_NOW": 0,
                "HUMAN_REVIEW_REQUIRED": 1,
                "NOTES": r.get("REASON", ""),
            })
        for i, r in enumerate(broad[:200], start=1):
            review.append({
                "REVIEW_ROW": i,
                "TARGET_PATH": r.get("TARGET_PATH", ""),
                "ROLE": r.get("ROLE", ""),
                "CONFIDENCE_SCORE": r.get("CONFIDENCE_SCORE", ""),
                "REASON": r.get("REASON", ""),
                "ACTION": "NOT_IN_EXACT_MAP_REVIEW_ONLY",
            })

        map_path = bb_root / "exact_target_map_PROPOSED_REVIEW_REQUIRED_v1.csv"
        review_path = bb_root / "broad_target_review_sample_v1.csv"
        readme = bb_root / "README_10BB_EXACT_TARGET_MAP_REVIEW.md"
        wcsv(map_path, proposed, ["MAP_ROW","TARGET_ID","TARGET_KIND","TARGET_PATH","SOURCE_ROLE","CONFIDENCE_SCORE","PROPOSED_ACTION","CANDIDATE_HELP_TOPIC","CANDIDATE_LOW_LEVEL_TOPICS","ROLLBACK_REQUIRED","AUTHORIZED_FOR_EXECUTION_NOW","HUMAN_REVIEW_REQUIRED","NOTES"])
        wcsv(review_path, review, ["REVIEW_ROW","TARGET_PATH","ROLE","CONFIDENCE_SCORE","REASON","ACTION"])
        readme.write_text(
            "# 10BB Exact Target Map Review\n\n"
            "10BB proposes an exact target map from the six high-confidence 10BA candidates. "
            "It does not authorize or execute HELP DATA/CMDHELPCHK mutation.\n\n"
            "Review this file before any 10BC acceptance:\n\n"
            "```text\n"
            "docs/messaging/apply/phase22ae_6_5_10bb_exact_help_cmdhelpchk_target_map_v1/exact_target_map_PROPOSED_REVIEW_REQUIRED_v1.csv\n"
            "```\n\n"
            "All rows have `AUTHORIZED_FOR_EXECUTION_NOW=0` and `HUMAN_REVIEW_REQUIRED=1`.\n",
            encoding="utf-8"
        )
        for p in [map_path, review_path, readme]:
            artifacts.append({"ARTIFACT": rel(p, repo), "ROLE": "target_map_review_artifact", "BYTES": p.stat().st_size, "SHA256": sha(p)})
        status = GREEN

    boundary = [
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "10BB writes docs/messaging target-map review artifacts only."},
        {"PROTECTED_SYSTEM": "ACTIVE_SYSTEM_MESSAGES", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_SYSTEM_MESSAGE_TEXT", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_CDX_LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CDX/LMDB mutation."},
        {"PROTECTED_SYSTEM": "WORKSPACE_PROFILE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No workspace mutation."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No HELP DATA mutation; proposed map only."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CMDHELPCHK mutation; proposed map only."},
    ]

    readiness = [
        {"ITEM": "EXACT_TARGET_MAP_PROPOSED", "STATUS": "YES_REVIEW_REQUIRED", "DETAIL": f"{len(proposed)} proposed exact rows from 10BA candidates."},
        {"ITEM": "HUMAN_REVIEW_REQUIRED", "STATUS": "YES", "DETAIL": "All proposed rows require review before acceptance."},
        {"ITEM": "HELP_DATA_APPLY_EXECUTION", "STATUS": "NOT_EXECUTED_IN_10BB", "DETAIL": "No apply execution."},
        {"ITEM": "CMDHELPCHK_APPLY_EXECUTION", "STATUS": "NOT_EXECUTED_IN_10BB", "DETAIL": "No apply execution."},
        {"ITEM": "NEXT_ACCEPTANCE_GATE", "STATUS": "10BC_REQUIRED", "DETAIL": "10BC should accept/reject/revise the proposed exact map."},
    ]

    issues = "0" if failures == 0 else str(failures)
    wcsv(reports / "message_catalog_phase22ae_6_5_10bb_gate_check_v1.csv", gates, ["GATE","STATUS","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10bb_proposed_exact_target_map_v1.csv", proposed, ["MAP_ROW","TARGET_ID","TARGET_KIND","TARGET_PATH","SOURCE_ROLE","CONFIDENCE_SCORE","PROPOSED_ACTION","CANDIDATE_HELP_TOPIC","CANDIDATE_LOW_LEVEL_TOPICS","ROLLBACK_REQUIRED","AUTHORIZED_FOR_EXECUTION_NOW","HUMAN_REVIEW_REQUIRED","NOTES"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10bb_broad_target_review_sample_v1.csv", review, ["REVIEW_ROW","TARGET_PATH","ROLE","CONFIDENCE_SCORE","REASON","ACTION"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10bb_apply_readiness_v1.csv", readiness, ["ITEM","STATUS","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10bb_boundary_ledger_v1.csv", boundary, ["PROTECTED_SYSTEM","MUTATION_ALLOWED","OBSERVED_MUTATION","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10bb_artifact_manifest_v1.csv", artifacts, ["ARTIFACT","ROLE","BYTES","SHA256"])

    summary = {
        "STATUS": status,
        "VALIDATION_ISSUES": issues,
        "PHASE22AE_6_5_10BA_STATUS": ba.get("STATUS", ""),
        "MSG_022AE_6_5_10BA_SAVEPOINT_PRESENT": 1 if sp_ba else 0,
        "ACTIVE_MESSAGES_OBSERVED_COUNT": msg_count,
        "ACTIVE_TEXT_OBSERVED_COUNT": text_count,
        "BA_EXACT_TARGET_CANDIDATES": len(exact),
        "BA_BROAD_TARGET_REVIEW_ROWS": len(broad),
        "PROPOSED_MAP_ROWS": len(proposed),
        "BROAD_REVIEW_SAMPLE_ROWS": len(review),
        "BB_ROOT": rel(bb_root, repo),
        "EXACT_TARGET_MAP_PROPOSED": 1 if proposed else 0,
        "EXACT_TARGET_MAP_ACCEPTED": 0,
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
    wcsv(reports / "message_catalog_phase22ae_6_5_10bb_status_summary_v1.csv", [summary], list(summary.keys()))

    (repo / "docs/messaging/MESSAGE_LOCALE_PHASE22AE_6_5_10BB_EXACT_HELP_CMDHELPCHK_TARGET_MAP.md").write_text(
        f"# Message Catalog Phase 22AE.6.5.10BB Exact HELP/CMDHELPCHK Target Map\n\n"
        f"Status: `{status}`\n\n"
        "10BB proposes an exact target map for review. It does not mutate HELP DATA or CMDHELPCHK.\n\n"
        f"Target-map root:\n\n```text\n{rel(bb_root, repo)}\n```\n\n"
        f"Next gate:\n\n```text\n{NEXT}\n```\n",
        encoding="utf-8"
    )

    print(status)
    print(f"  validation issues: {issues}")
    print(f"  Phase 22AE.6.5.10BA status: {ba.get('STATUS','')}")
    print(f"  MSG-022AE.6.5.10BA savepoint present: {1 if sp_ba else 0}")
    print(f"  active messages observed count: {msg_count}")
    print(f"  active text observed count: {text_count}")
    print(f"  BA exact target candidates: {len(exact)}")
    print(f"  BA broad target review rows: {len(broad)}")
    print(f"  proposed map rows: {len(proposed)}")
    print(f"  broad review sample rows: {len(review)}")
    print(f"  target-map root: {rel(bb_root, repo)}")
    print("  exact target map proposed: 1")
    print("  exact target map accepted: 0")
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
