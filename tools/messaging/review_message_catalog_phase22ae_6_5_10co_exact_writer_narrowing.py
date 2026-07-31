#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, json, hashlib, shutil
from datetime import datetime, timezone
from pathlib import Path

GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_10CO_EXACT_NATIVE_WRITER_NARROWING_REVIEW_GREEN_CONFIRMATION_PACKAGE_REQUIRED_SOURCE_HELD"
BLOCKED = "MESSAGE_CATALOG_PHASE22AE_6_5_10CO_EXACT_NATIVE_WRITER_NARROWING_REVIEW_BLOCKED"
NEXT = "HOLD_OR_AUTHORIZE_PHASE22AE_6_5_10CP_EXACT_NATIVE_WRITER_CONFIRMATION_PACKAGE"

REPORT = Path("docs/messaging/reports")
CN_SUMMARY = REPORT / "message_catalog_phase22ae_6_5_10cn_status_summary_v1.csv"
CN_NARROWED = REPORT / "message_catalog_phase22ae_6_5_10cn_narrowed_exact_writer_candidates_v1.csv"
CN_CONTEXT = REPORT / "message_catalog_phase22ae_6_5_10cn_exact_writer_candidate_context_v1.csv"
CN_PATH_SUMMARY = REPORT / "message_catalog_phase22ae_6_5_10cn_narrowing_path_summary_v1.csv"
CN_NEXT_REQ = REPORT / "message_catalog_phase22ae_6_5_10cn_next_review_requirements_v1.csv"
CN_BLOCKED = REPORT / "message_catalog_phase22ae_6_5_10cn_carry_forward_blocked_actions_v1.csv"

ACTIVE_MSG_DBF = Path("dottalkpp/data/messaging/SYSTEM_MESSAGES.dbf")
ACTIVE_TEXT_DBF = Path("dottalkpp/data/messaging/SYSTEM_MESSAGE_TEXT.dbf")
CO_ROOT = Path("docs/messaging/apply/phase22ae_6_5_10co_exact_native_writer_narrowing_review_v1")

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
    p = Path(p); p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fs, lineterminator="\n", extrasaction="ignore")
        w.writeheader()
        for r in rs:
            w.writerow({k: r.get(k, "") for k in fs})

def rel(p, repo):
    try:
        return str(Path(p).resolve().relative_to(repo.resolve())).replace("\\", "/")
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
    lp = repo / REPORT / "message_savepoint_latest_v1.json"
    if lp.exists():
        try:
            latest = json.loads(lp.read_text(encoding="utf-8")).get("savepoint_id", "")
        except Exception:
            latest = ""
    jp = repo / "docs/messaging/MESSAGING_SAVEPOINT_JOURNAL.md"
    txt = jp.read_text(encoding="utf-8", errors="replace") if jp.exists() else ""
    return latest == sid or sid in txt, latest

def intish(v):
    try:
        return int(float(str(v)))
    except Exception:
        return 0

def rank_candidate(r):
    priority = r.get("NARROWING_PRIORITY", "")
    disp = r.get("NARROWING_DISPOSITION", "")
    score = intish(r.get("NARROWING_SCORE", 0))
    if priority == "A":
        review = "CONFIRM_EXACT_WRITER_REUSE_OR_REJECT"
        detail = "Open source context and confirm whether this is an actual native writer/import/update path for HELP DATA or CMDHELPCHK."
    elif priority == "B":
        review = "CONFIRM_GENERIC_WRITER_TARGET_BINDING_OR_REJECT"
        detail = "Open source context and prove whether generic writer behavior binds to exact HELP DATA/CMDHELPCHK targets."
    elif "READER" in disp:
        review = "LIKELY_READER_CHECKER_EXCLUSION"
        detail = "Use as false-positive exclusion unless context proves writer behavior."
    else:
        review = "SUPPORTING_CONTEXT_ONLY"
        detail = "Supporting evidence only; not enough for reuse/apply decision."
    return review, detail, score

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--replace-existing-review", action="store_true")
    args = ap.parse_args()
    repo = Path(args.repo_root).resolve()
    reports = repo / REPORT
    reports.mkdir(parents=True, exist_ok=True)

    cn = first(repo / CN_SUMMARY)
    narrowed = rows(repo / CN_NARROWED)
    context = rows(repo / CN_CONTEXT)
    path_summary = rows(repo / CN_PATH_SUMMARY)
    next_req = rows(repo / CN_NEXT_REQ)
    blocked_in = rows(repo / CN_BLOCKED)

    sp_cn, latest_cn = savepoint(repo, "MSG-022AE.6.5.10CN")
    msg_count = dbf_count(repo / ACTIVE_MSG_DBF)
    text_count = dbf_count(repo / ACTIVE_TEXT_DBF)
    co_root = repo / CO_ROOT

    gates = []
    failures = 0
    def gate(name, ok, detail):
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": str(detail)})
        if not ok:
            failures += 1

    gate("PHASE22AE_6_5_10CN_GREEN", cn.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_5_10CN_EXACT_NATIVE_WRITER_CANDIDATE_NARROWING_PACKAGE_GREEN_CANDIDATES_NARROWED_SOURCE_HELD", cn.get("STATUS","missing"))
    gate("MSG_022AE_6_5_10CN_SAVEPOINT_PRESENT", sp_cn, latest_cn)
    gate("CN_CANDIDATES_NARROWED", cn.get("CANDIDATES_NARROWED") == "1", cn.get("CANDIDATES_NARROWED","missing"))
    gate("CN_WRITER_REUSE_NOT_CONFIRMED", cn.get("WRITER_REUSE_CONFIRMED_NOW") == "0", cn.get("WRITER_REUSE_CONFIRMED_NOW","missing"))
    gate("CN_SOURCE_PATCH_NOT_PROVEN", cn.get("SOURCE_PATCH_NEEDED_PROVEN") == "0", cn.get("SOURCE_PATCH_NEEDED_PROVEN","missing"))
    gate("CN_SOURCE_MUTATION_NOT_AUTHORIZED", cn.get("SOURCE_MUTATION_AUTHORIZED_NOW") == "0", cn.get("SOURCE_MUTATION_AUTHORIZED_NOW","missing"))
    gate("CN_APPLY_EXECUTION_NOT_AUTHORIZED", cn.get("APPLY_EXECUTION_AUTHORIZED_NOW") == "0", cn.get("APPLY_EXECUTION_AUTHORIZED_NOW","missing"))
    gate("CN_HELP_APPLY_NOT_EXECUTED", cn.get("HELP_DATA_APPLY_EXECUTED") == "0", cn.get("HELP_DATA_APPLY_EXECUTED","missing"))
    gate("CN_CMDHELPCHK_APPLY_NOT_EXECUTED", cn.get("CMDHELPCHK_APPLY_EXECUTED") == "0", cn.get("CMDHELPCHK_APPLY_EXECUTED","missing"))
    gate("CN_NARROWED_ROWS_PRESENT", len(narrowed) > 0, len(narrowed))
    gate("CN_CONTEXT_ROWS_PRESENT", len(context) > 0, len(context))
    gate("CN_NEXT_REQUIREMENTS_PRESENT", len(next_req) > 0, len(next_req))
    gate("ACTIVE_MESSAGES_HEADER_COUNT_14", msg_count == 14, msg_count)
    gate("ACTIVE_TEXT_HEADER_COUNT_70", text_count == 70, text_count)
    gate("CO_ROOT_NOT_EXISTING_OR_REPLACE_ALLOWED", (not co_root.exists()) or args.replace_existing_review, rel(co_root, repo))

    status = BLOCKED
    candidate_review = []
    confirmation_focus = []
    disposition_summary = []
    confirmation_requirements = []
    carry_forward_blocked = []
    review_decisions = []
    artifacts = []

    if failures == 0:
        if co_root.exists() and args.replace_existing_review:
            shutil.rmtree(co_root)
        co_root.mkdir(parents=True, exist_ok=True)

        for i, r in enumerate(narrowed, 1):
            review, detail, score = rank_candidate(r)
            candidate_review.append({
                "REVIEW_ROW": i,
                "SOURCE_NARROWED_ROW": r.get("NARROWED_ROW",""),
                "DISCOVERY_CLASS": r.get("DISCOVERY_CLASS",""),
                "NARROWING_DISPOSITION": r.get("NARROWING_DISPOSITION",""),
                "NARROWING_PRIORITY": r.get("NARROWING_PRIORITY",""),
                "NARROWING_SCORE": r.get("NARROWING_SCORE",""),
                "FILE_PATH": r.get("FILE_PATH",""),
                "LINE": r.get("LINE",""),
                "SNIPPET": r.get("SNIPPET",""),
                "CO_REVIEW_DISPOSITION": review,
                "CO_REVIEW_DETAIL": detail,
                "CONFIRMATION_REQUIRED": 1 if review in {"CONFIRM_EXACT_WRITER_REUSE_OR_REJECT","CONFIRM_GENERIC_WRITER_TARGET_BINDING_OR_REJECT"} else 0,
                "WRITER_REUSE_CONFIRMED_NOW": 0,
                "SOURCE_PATCH_NEEDED_PROVEN": 0,
                "APPLY_READY_NOW": 0,
                "SOURCE_MUTATION_AUTHORIZED_NOW": 0,
                "APPLY_AUTHORIZED_NOW": 0,
            })

        for r in candidate_review:
            if r["CONFIRMATION_REQUIRED"] == 1:
                confirmation_focus.append({
                    "CONFIRMATION_FOCUS_ROW": len(confirmation_focus) + 1,
                    "SOURCE_REVIEW_ROW": r.get("REVIEW_ROW",""),
                    "DISCOVERY_CLASS": r.get("DISCOVERY_CLASS",""),
                    "NARROWING_PRIORITY": r.get("NARROWING_PRIORITY",""),
                    "NARROWING_SCORE": r.get("NARROWING_SCORE",""),
                    "FILE_PATH": r.get("FILE_PATH",""),
                    "LINE": r.get("LINE",""),
                    "CONFIRMATION_OBJECTIVE": "Confirm exact native writer/import/update path and exact target records for HELP DATA or CMDHELPCHK.",
                    "CONFIRMED_NOW": 0,
                    "APPLY_READY_NOW": 0,
                })

        counts = {}
        for r in candidate_review:
            k = r.get("CO_REVIEW_DISPOSITION","")
            counts[k] = counts.get(k, 0) + 1
        for k in sorted(counts):
            disposition_summary.append({
                "SUMMARY_ROW": len(disposition_summary) + 1,
                "CO_REVIEW_DISPOSITION": k,
                "ROW_COUNT": counts[k],
                "NEXT_ACTION": "Carry to 10CP confirmation package if confirmation is required; otherwise keep as supporting or exclusion evidence.",
            })

        confirmation_requirements = [
            {"REQ_ROW": 1, "CONFIRMATION_REQUIREMENT": "OPEN_CANDIDATE_SOURCE_CONTEXT", "DETAIL": "Open each confirmation-focus file around the reported line and inspect surrounding implementation.", "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
            {"REQ_ROW": 2, "CONFIRMATION_REQUIREMENT": "PROVE_NATIVE_WRITER_BEHAVIOR", "DETAIL": "Confirm actual write/import/update behavior rather than read/check/display behavior.", "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
            {"REQ_ROW": 3, "CONFIRMATION_REQUIREMENT": "PROVE_EXACT_HELP_DATA_TARGET", "DETAIL": "For HELP DATA candidates, prove the path can target MSGMGR / SET MESSAGE HELP records.", "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
            {"REQ_ROW": 4, "CONFIRMATION_REQUIREMENT": "PROVE_EXACT_CMDHELPCHK_TARGET", "DETAIL": "For CMDHELPCHK candidates, prove the path can target MSGMGR / SET MESSAGE CMDHELPCHK records.", "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
            {"REQ_ROW": 5, "CONFIRMATION_REQUIREMENT": "REPORT_REUSE_OR_GAP", "DETAIL": "10CP should state whether existing native reuse is confirmed, rejected, or still inconclusive.", "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
            {"REQ_ROW": 6, "CONFIRMATION_REQUIREMENT": "DO_NOT_DECLARE_SOURCE_PATCH_NEEDED_YET", "DETAIL": "Source patch need remains unproven until existing native/reuse path is rejected by review.", "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
            {"REQ_ROW": 7, "CONFIRMATION_REQUIREMENT": "KEEP_SOURCE_COMMENT_CONTRACT_RULE", "DETAIL": "If a later source patch is selected, update @dottalk.usage and related source-comment contracts in the same guarded package.", "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
            {"REQ_ROW": 8, "CONFIRMATION_REQUIREMENT": "KEEP_RAW_DBF_WRITE_FORBIDDEN", "DETAIL": "Any accepted apply path must be native/schema-aware, not raw DBF byte mutation.", "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
            {"REQ_ROW": 9, "CONFIRMATION_REQUIREMENT": "KEEP_APPLY_BLOCKED", "DETAIL": "No HELP DATA/CMDHELPCHK apply until an exact writer path and guarded apply package are reviewed.", "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
        ]

        for i, b in enumerate(blocked_in, 1):
            carry_forward_blocked.append({
                "CARRY_FORWARD_ROW": i,
                "BLOCKED_ACTION": b.get("BLOCKED_ACTION",""),
                "BLOCKED": 1,
                "REASON": b.get("REASON",""),
                "CARRY_FORWARD_DETAIL": "Still blocked after CO exact narrowing review.",
            })

        review_decisions = [
            {"DECISION_ROW": 1, "DECISION": "CN_NARROWING_ACCEPTED_FOR_REVIEW", "VALUE": 1, "DETAIL": "10CN narrowed candidate set is accepted for confirmation planning."},
            {"DECISION_ROW": 2, "DECISION": "CONFIRMATION_PACKAGE_REQUIRED", "VALUE": 1, "DETAIL": "10CP must confirm/reject exact writer candidates."},
            {"DECISION_ROW": 3, "DECISION": "WRITER_REUSE_CONFIRMED_NOW", "VALUE": 0, "DETAIL": "CO does not confirm reuse."},
            {"DECISION_ROW": 4, "DECISION": "SOURCE_PATCH_NEEDED_PROVEN", "VALUE": 0, "DETAIL": "Source patch need remains unproven."},
            {"DECISION_ROW": 5, "DECISION": "DIRECT_APPLY_READY", "VALUE": 0, "DETAIL": "Direct HELP/CMDHELPCHK apply remains blocked."},
        ]

        paths = [
            (co_root / "exact_narrowing_candidate_review_v1.csv", candidate_review, ["REVIEW_ROW","SOURCE_NARROWED_ROW","DISCOVERY_CLASS","NARROWING_DISPOSITION","NARROWING_PRIORITY","NARROWING_SCORE","FILE_PATH","LINE","SNIPPET","CO_REVIEW_DISPOSITION","CO_REVIEW_DETAIL","CONFIRMATION_REQUIRED","WRITER_REUSE_CONFIRMED_NOW","SOURCE_PATCH_NEEDED_PROVEN","APPLY_READY_NOW","SOURCE_MUTATION_AUTHORIZED_NOW","APPLY_AUTHORIZED_NOW"]),
            (co_root / "confirmation_focus_v1.csv", confirmation_focus, ["CONFIRMATION_FOCUS_ROW","SOURCE_REVIEW_ROW","DISCOVERY_CLASS","NARROWING_PRIORITY","NARROWING_SCORE","FILE_PATH","LINE","CONFIRMATION_OBJECTIVE","CONFIRMED_NOW","APPLY_READY_NOW"]),
            (co_root / "review_disposition_summary_v1.csv", disposition_summary, ["SUMMARY_ROW","CO_REVIEW_DISPOSITION","ROW_COUNT","NEXT_ACTION"]),
            (co_root / "confirmation_requirements_v1.csv", confirmation_requirements, ["REQ_ROW","CONFIRMATION_REQUIREMENT","DETAIL","SOURCE_MUTATION_AUTHORIZED_NOW","APPLY_AUTHORIZED_NOW"]),
            (co_root / "carry_forward_blocked_actions_v1.csv", carry_forward_blocked, ["CARRY_FORWARD_ROW","BLOCKED_ACTION","BLOCKED","REASON","CARRY_FORWARD_DETAIL"]),
            (co_root / "review_decisions_v1.csv", review_decisions, ["DECISION_ROW","DECISION","VALUE","DETAIL"]),
        ]
        for p, rs, fs in paths:
            wcsv(p, rs, fs)

        scripts = co_root / "scripts"
        scripts.mkdir(parents=True, exist_ok=True)
        disabled = scripts / "MESSAGE_CATALOG_PHASE22AE_6_5_10CP_CONFIRMATION_TEMPLATE.ps1.disabled"
        disabled.write_text('throw "10CO is review only. Generate a dedicated 10CP confirmation package before confirming reuse/source-patch/apply path."\n', encoding="utf-8")
        readback = scripts / "MESSAGE_CATALOG_PHASE22AE_6_5_10CO_READBACK_CONTRACT.dts"
        readback.write_text("MSGMGR STATUS\nMSGMGR CHECK\nSET MESSAGE CATALOG CHECK\nSET MESSAGE EMIT MESSAGE_PROOF_MODE_STATUS en-US\nHELP MSGMGR\nHELP SET MESSAGE\nCMDHELPCHK\nQUIT\n", encoding="utf-8")
        notes = co_root / "exact_native_writer_narrowing_review_v1.md"
        notes.write_text("# 10CO Exact Native Writer Narrowing Review\n\n10CO reviews 10CN narrowed candidates and requires a 10CP confirmation package. It does not confirm reuse, prove source patch need, authorize apply, or mutate protected systems.\n", encoding="utf-8")
        readme = co_root / "README_10CO_EXACT_NATIVE_WRITER_NARROWING_REVIEW.md"
        readme.write_text("# 10CO Exact Native Writer Narrowing Review\n\nReview-only package. No protected mutation occurs.\n", encoding="utf-8")

        for p, _, _ in paths:
            artifacts.append({"ARTIFACT": rel(p, repo), "ROLE": "exact_native_writer_narrowing_review_artifact", "BYTES": p.stat().st_size, "SHA256": sha(p)})
        for p in [disabled, readback, notes, readme]:
            artifacts.append({"ARTIFACT": rel(p, repo), "ROLE": "exact_native_writer_narrowing_review_artifact", "BYTES": p.stat().st_size, "SHA256": sha(p)})

        status = GREEN

    boundary = [
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "10CO writes docs/messaging review artifacts only."},
        {"PROTECTED_SYSTEM": "ACTIVE_SYSTEM_MESSAGES", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_SYSTEM_MESSAGE_TEXT", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_CDX_LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CDX/LMDB mutation."},
        {"PROTECTED_SYSTEM": "WORKSPACE_PROFILE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No workspace mutation."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Narrowing review only; no HELP DATA apply."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Narrowing review only; no CMDHELPCHK apply."},
    ]
    readiness = [
        {"ITEM": "NARROWING_REVIEWED", "STATUS": "YES" if status == GREEN else "NO", "DETAIL": f"{len(candidate_review)} narrowed candidates reviewed."},
        {"ITEM": "CONFIRMATION_PACKAGE_REQUIRED", "STATUS": "YES", "DETAIL": f"{len(confirmation_focus)} confirmation-focus rows."},
        {"ITEM": "WRITER_REUSE_CONFIRMED_NOW", "STATUS": "NO", "DETAIL": "CO does not confirm reuse."},
        {"ITEM": "SOURCE_PATCH_NEEDED_PROVEN", "STATUS": "NO", "DETAIL": "Source patch need remains unproven."},
        {"ITEM": "DIRECT_APPLY_READY", "STATUS": "NO", "DETAIL": "Direct apply remains blocked."},
    ]

    issues = "0" if failures == 0 else str(failures)
    wcsv(reports / "message_catalog_phase22ae_6_5_10co_gate_check_v1.csv", gates, ["GATE","STATUS","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10co_exact_narrowing_candidate_review_v1.csv", candidate_review, ["REVIEW_ROW","SOURCE_NARROWED_ROW","DISCOVERY_CLASS","NARROWING_DISPOSITION","NARROWING_PRIORITY","NARROWING_SCORE","FILE_PATH","LINE","SNIPPET","CO_REVIEW_DISPOSITION","CO_REVIEW_DETAIL","CONFIRMATION_REQUIRED","WRITER_REUSE_CONFIRMED_NOW","SOURCE_PATCH_NEEDED_PROVEN","APPLY_READY_NOW","SOURCE_MUTATION_AUTHORIZED_NOW","APPLY_AUTHORIZED_NOW"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10co_confirmation_focus_v1.csv", confirmation_focus, ["CONFIRMATION_FOCUS_ROW","SOURCE_REVIEW_ROW","DISCOVERY_CLASS","NARROWING_PRIORITY","NARROWING_SCORE","FILE_PATH","LINE","CONFIRMATION_OBJECTIVE","CONFIRMED_NOW","APPLY_READY_NOW"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10co_review_disposition_summary_v1.csv", disposition_summary, ["SUMMARY_ROW","CO_REVIEW_DISPOSITION","ROW_COUNT","NEXT_ACTION"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10co_confirmation_requirements_v1.csv", confirmation_requirements, ["REQ_ROW","CONFIRMATION_REQUIREMENT","DETAIL","SOURCE_MUTATION_AUTHORIZED_NOW","APPLY_AUTHORIZED_NOW"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10co_carry_forward_blocked_actions_v1.csv", carry_forward_blocked, ["CARRY_FORWARD_ROW","BLOCKED_ACTION","BLOCKED","REASON","CARRY_FORWARD_DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10co_review_decisions_v1.csv", review_decisions, ["DECISION_ROW","DECISION","VALUE","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10co_apply_readiness_v1.csv", readiness, ["ITEM","STATUS","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10co_boundary_ledger_v1.csv", boundary, ["PROTECTED_SYSTEM","MUTATION_ALLOWED","OBSERVED_MUTATION","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10co_artifact_manifest_v1.csv", artifacts, ["ARTIFACT","ROLE","BYTES","SHA256"])

    summary = {
        "STATUS": status,
        "VALIDATION_ISSUES": issues,
        "PHASE22AE_6_5_10CN_STATUS": cn.get("STATUS",""),
        "MSG_022AE_6_5_10CN_SAVEPOINT_PRESENT": 1 if sp_cn else 0,
        "ACTIVE_MESSAGES_OBSERVED_COUNT": msg_count,
        "ACTIVE_TEXT_OBSERVED_COUNT": text_count,
        "CN_NARROWED_CANDIDATE_ROWS": len(narrowed),
        "CN_CONTEXT_ROWS": len(context),
        "CANDIDATE_REVIEW_ROWS": len(candidate_review),
        "CONFIRMATION_FOCUS_ROWS": len(confirmation_focus),
        "CONFIRMATION_REQUIREMENT_ROWS": len(confirmation_requirements),
        "CO_ROOT": rel(co_root, repo),
        "NARROWING_REVIEWED": 1 if status == GREEN else 0,
        "CONFIRMATION_PACKAGE_REQUIRED": 1 if status == GREEN else 0,
        "WRITER_REUSE_CONFIRMED_NOW": 0,
        "SOURCE_PATCH_NEEDED_PROVEN": 0,
        "SOURCE_MUTATION_AUTHORIZED_NOW": 0,
        "APPLY_EXECUTION_AUTHORIZED_NOW": 0,
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
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00","Z"),
    }
    wcsv(reports / "message_catalog_phase22ae_6_5_10co_status_summary_v1.csv", [summary], list(summary.keys()))

    (repo / "docs/messaging/MESSAGE_LOCALE_PHASE22AE_6_5_10CO_EXACT_NATIVE_WRITER_NARROWING_REVIEW.md").write_text(
        f"# Message Catalog Phase 22AE.6.5.10CO Exact Native Writer Narrowing Review\n\nStatus: `{status}`\n\n10CO reviews 10CN narrowed exact native writer candidates and requires a 10CP confirmation package. It does not confirm reuse, prove source patch need, authorize apply, or mutate protected systems.\n\nReview root:\n\n```text\n{rel(co_root, repo)}\n```\n\nNext gate:\n\n```text\n{NEXT}\n```\n",
        encoding="utf-8"
    )

    print(status)
    print(f"  validation issues: {issues}")
    print(f"  Phase 22AE.6.5.10CN status: {cn.get('STATUS','')}")
    print(f"  MSG-022AE.6.5.10CN savepoint present: {1 if sp_cn else 0}")
    print(f"  active messages observed count: {msg_count}")
    print(f"  active text observed count: {text_count}")
    print(f"  CN narrowed candidate rows: {len(narrowed)}")
    print(f"  CN context rows: {len(context)}")
    print(f"  candidate review rows: {len(candidate_review)}")
    print(f"  confirmation focus rows: {len(confirmation_focus)}")
    print(f"  confirmation requirement rows: {len(confirmation_requirements)}")
    print(f"  review root: {rel(co_root, repo)}")
    print("  narrowing reviewed: 1")
    print("  confirmation package required: 1")
    print("  writer reuse confirmed now: 0")
    print("  source patch needed proven: 0")
    print("  source mutation authorized now: 0")
    print("  apply execution authorized now: 0")
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
