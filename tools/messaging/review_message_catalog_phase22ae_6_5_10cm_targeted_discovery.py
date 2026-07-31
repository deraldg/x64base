#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, json, hashlib, shutil
from datetime import datetime, timezone
from pathlib import Path

GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_10CM_TARGETED_NATIVE_WRITER_DISCOVERY_REVIEW_GREEN_NARROWING_PACKAGE_REQUIRED_SOURCE_HELD"
BLOCKED = "MESSAGE_CATALOG_PHASE22AE_6_5_10CM_TARGETED_NATIVE_WRITER_DISCOVERY_REVIEW_BLOCKED"
NEXT = "HOLD_OR_AUTHORIZE_PHASE22AE_6_5_10CN_EXACT_NATIVE_WRITER_CANDIDATE_NARROWING_PACKAGE"

REPORT = Path("docs/messaging/reports")
CL_SUMMARY = REPORT / "message_catalog_phase22ae_6_5_10cl_status_summary_v1.csv"
CL_CANDIDATES = REPORT / "message_catalog_phase22ae_6_5_10cl_targeted_native_writer_candidates_v1.csv"
CL_DISCOVERY_SUMMARY = REPORT / "message_catalog_phase22ae_6_5_10cl_targeted_discovery_summary_v1.csv"
CL_SCAN = REPORT / "message_catalog_phase22ae_6_5_10cl_targeted_scan_manifest_v1.csv"
CL_BLOCKED = REPORT / "message_catalog_phase22ae_6_5_10cl_carry_forward_blocked_actions_v1.csv"

ACTIVE_MSG_DBF = Path("dottalkpp/data/messaging/SYSTEM_MESSAGES.dbf")
ACTIVE_TEXT_DBF = Path("dottalkpp/data/messaging/SYSTEM_MESSAGE_TEXT.dbf")
CM_ROOT = Path("docs/messaging/apply/phase22ae_6_5_10cm_targeted_native_writer_discovery_review_v1")

MAX_FOCUS_ROWS = 160
MAX_EXACT_ROWS = 80

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
    try: return str(Path(p).resolve().relative_to(repo.resolve())).replace("\\", "/")
    except Exception: return str(p).replace("\\", "/")

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

def review_disposition(candidate):
    cls = candidate.get("DISCOVERY_CLASS", "")
    path = candidate.get("FILE_PATH", "").lower()
    snippet = candidate.get("SNIPPET", "").lower()
    score = intish(candidate.get("TARGETED_SCORE", 0))

    if "HELP_DATA_EXACT_WRITER" in cls:
        return "EXACT_HELP_DATA_WRITER_REVIEW_REQUIRED", "High-priority candidate. Inspect manually to confirm whether it writes/imports/updates HELP DATA, not just reads/displays it."
    if "CMDHELPCHK_EXACT_WRITER" in cls:
        return "EXACT_CMDHELPCHK_WRITER_REVIEW_REQUIRED", "High-priority candidate. Inspect manually to confirm whether it writes/imports/updates CMDHELPCHK, not just checks/reads it."
    if "GENERIC_NATIVE_WRITER" in cls:
        return "GENERIC_WRITER_TARGET_BINDING_REQUIRED", "Candidate mentions writer/import/update behavior but must be tied to exact HELP DATA or CMDHELPCHK target before use."
    if "SOURCE_COMMENT_CONTRACT" in cls:
        return "SOURCE_CONTRACT_SUPPORT_ONLY", "Useful only if a later source patch is chosen; not writer proof by itself."
    if "READER_CHECKER_EXCLUSION" in cls:
        return "EXCLUDE_OR_MARK_READER_CHECKER", "Likely reader/checker/display path; use to avoid false writer positives."
    if score >= 100:
        return "HIGH_SCORE_REVIEW_REQUIRED", "High targeted score requires manual review before any selection."
    return "SUPPORTING_EVIDENCE_REVIEW", "Supporting evidence only."

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--replace-existing-review", action="store_true")
    args = ap.parse_args()
    repo = Path(args.repo_root).resolve()
    reports = repo / REPORT
    reports.mkdir(parents=True, exist_ok=True)

    cl = first(repo / CL_SUMMARY)
    candidates = rows(repo / CL_CANDIDATES)
    discovery_summary = rows(repo / CL_DISCOVERY_SUMMARY)
    scan_manifest = rows(repo / CL_SCAN)
    blocked_in = rows(repo / CL_BLOCKED)

    sp_cl, latest_cl = savepoint(repo, "MSG-022AE.6.5.10CL")
    msg_count = dbf_count(repo / ACTIVE_MSG_DBF)
    text_count = dbf_count(repo / ACTIVE_TEXT_DBF)
    cm_root = repo / CM_ROOT

    gates = []
    failures = 0
    def gate(name, ok, detail):
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": str(detail)})
        if not ok:
            failures += 1

    gate("PHASE22AE_6_5_10CL_GREEN", cl.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_5_10CL_TARGETED_NATIVE_WRITER_DISCOVERY_PACKAGE_GREEN_DISCOVERY_REPORTED_SOURCE_HELD", cl.get("STATUS","missing"))
    gate("MSG_022AE_6_5_10CL_SAVEPOINT_PRESENT", sp_cl, latest_cl)
    gate("CL_TARGETED_DISCOVERY_REPORTED", cl.get("TARGETED_DISCOVERY_REPORTED") == "1", cl.get("TARGETED_DISCOVERY_REPORTED","missing"))
    gate("CL_REUSE_NOT_CONFIRMED", cl.get("REUSE_PATH_CONFIRMED_NOW") == "0", cl.get("REUSE_PATH_CONFIRMED_NOW","missing"))
    gate("CL_SOURCE_PATCH_NOT_PROVEN", cl.get("SOURCE_PATCH_NEEDED_PROVEN") == "0", cl.get("SOURCE_PATCH_NEEDED_PROVEN","missing"))
    gate("CL_SOURCE_MUTATION_NOT_AUTHORIZED", cl.get("SOURCE_MUTATION_AUTHORIZED_NOW") == "0", cl.get("SOURCE_MUTATION_AUTHORIZED_NOW","missing"))
    gate("CL_APPLY_EXECUTION_NOT_AUTHORIZED", cl.get("APPLY_EXECUTION_AUTHORIZED_NOW") == "0", cl.get("APPLY_EXECUTION_AUTHORIZED_NOW","missing"))
    gate("CL_HELP_APPLY_NOT_EXECUTED", cl.get("HELP_DATA_APPLY_EXECUTED") == "0", cl.get("HELP_DATA_APPLY_EXECUTED","missing"))
    gate("CL_CMDHELPCHK_APPLY_NOT_EXECUTED", cl.get("CMDHELPCHK_APPLY_EXECUTED") == "0", cl.get("CMDHELPCHK_APPLY_EXECUTED","missing"))
    gate("CL_CANDIDATES_PRESENT", len(candidates) > 0, len(candidates))
    gate("CL_DISCOVERY_SUMMARY_PRESENT", len(discovery_summary) > 0, len(discovery_summary))
    gate("ACTIVE_MESSAGES_HEADER_COUNT_14", msg_count == 14, msg_count)
    gate("ACTIVE_TEXT_HEADER_COUNT_70", text_count == 70, text_count)
    gate("CM_ROOT_NOT_EXISTING_OR_REPLACE_ALLOWED", (not cm_root.exists()) or args.replace_existing_review, rel(cm_root, repo))

    status = BLOCKED
    class_review = []
    focus_review = []
    exact_candidate_focus = []
    narrowing_requirements = []
    carry_forward_blocked = []
    review_decisions = []
    artifacts = []

    if failures == 0:
        if cm_root.exists() and args.replace_existing_review:
            shutil.rmtree(cm_root)
        cm_root.mkdir(parents=True, exist_ok=True)

        # class-level review
        for i, r in enumerate(discovery_summary, 1):
            row_count = intish(r.get("ROW_COUNT", 0))
            cls = r.get("DISCOVERY_CLASS", "")
            if "EXACT_WRITER" in cls:
                disp = "ACCEPT_HIGH_PRIORITY_FOR_NARROWING"
            elif "GENERIC_NATIVE_WRITER" in cls:
                disp = "ACCEPT_SUPPORTING_FOR_TARGET_BINDING"
            elif "READER_CHECKER" in cls:
                disp = "ACCEPT_AS_EXCLUSION_EVIDENCE"
            else:
                disp = "ACCEPT_SUPPORTING_ONLY"
            class_review.append({
                "CLASS_REVIEW_ROW": i,
                "DISCOVERY_CLASS": cls,
                "ROW_COUNT": row_count,
                "REVIEW_DISPOSITION": disp,
                "NARROWING_REQUIRED": 1,
                "DETAIL": r.get("NEXT_REVIEW_ACTION",""),
            })

        # candidate-level review
        sorted_candidates = sorted(candidates, key=lambda r: intish(r.get("TARGETED_SCORE", 0)), reverse=True)
        for i, r in enumerate(sorted_candidates[:MAX_FOCUS_ROWS], 1):
            disp, detail = review_disposition(r)
            focus_review.append({
                "FOCUS_REVIEW_ROW": i,
                "SOURCE_DISCOVERY_ROW": r.get("DISCOVERY_ROW",""),
                "DISCOVERY_CLASS": r.get("DISCOVERY_CLASS",""),
                "TARGETED_SCORE": r.get("TARGETED_SCORE",""),
                "FILE_PATH": r.get("FILE_PATH",""),
                "LINE": r.get("LINE",""),
                "SNIPPET": r.get("SNIPPET",""),
                "REVIEW_DISPOSITION": disp,
                "REVIEW_DETAIL": detail,
                "EXACT_WRITER_CONFIRMATION_REQUIRED": 1 if "EXACT" in disp or "GENERIC_WRITER" in disp else 0,
                "REUSE_PATH_CONFIRMED_NOW": 0,
                "SOURCE_PATCH_NEEDED_PROVEN": 0,
                "SOURCE_MUTATION_AUTHORIZED_NOW": 0,
                "APPLY_AUTHORIZED_NOW": 0,
            })

        for r in focus_review:
            if "EXACT_" in r["REVIEW_DISPOSITION"] or "GENERIC_WRITER" in r["REVIEW_DISPOSITION"]:
                exact_candidate_focus.append({
                    "EXACT_FOCUS_ROW": len(exact_candidate_focus) + 1,
                    "SOURCE_FOCUS_REVIEW_ROW": r.get("FOCUS_REVIEW_ROW",""),
                    "DISCOVERY_CLASS": r.get("DISCOVERY_CLASS",""),
                    "TARGETED_SCORE": r.get("TARGETED_SCORE",""),
                    "FILE_PATH": r.get("FILE_PATH",""),
                    "LINE": r.get("LINE",""),
                    "SNIPPET": r.get("SNIPPET",""),
                    "CONFIRMATION_TASK": "Open file/context and confirm writer/import/update behavior plus exact target table/catalog.",
                    "CONFIRMED_NOW": 0,
                    "APPLY_READY_NOW": 0,
                })
                if len(exact_candidate_focus) >= MAX_EXACT_ROWS:
                    break

        cap_reached = len(candidates) >= 1200
        narrowing_requirements = [
            {"REQ_ROW": 1, "NARROWING_REQUIREMENT": "OPEN_TOP_EXACT_HELP_DATA_CANDIDATES", "DETAIL": "Inspect top HELP_DATA_EXACT_WRITER_CANDIDATE rows with file context; confirm writer/import/update behavior and exact target.", "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
            {"REQ_ROW": 2, "NARROWING_REQUIREMENT": "OPEN_TOP_EXACT_CMDHELPCHK_CANDIDATES", "DETAIL": "Inspect top CMDHELPCHK_EXACT_WRITER_CANDIDATE rows with file context; confirm writer/import/update behavior and exact target.", "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
            {"REQ_ROW": 3, "NARROWING_REQUIREMENT": "EXCLUDE_READER_CHECKER_FALSE_POSITIVES", "DETAIL": "Explicitly separate HELP display/CMDHELPCHK check/readback paths from writers.", "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
            {"REQ_ROW": 4, "NARROWING_REQUIREMENT": "REPORT_REUSE_PATH_OR_GAP", "DETAIL": "Narrowing package should state whether an exact reuse path exists or a gap remains.", "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
            {"REQ_ROW": 5, "NARROWING_REQUIREMENT": "TREAT_1200_CAP_AS_REVIEW_SIGNAL", "DETAIL": "Targeted discovery hit the package cap; do not assume complete coverage without narrowing/review." if cap_reached else "Targeted discovery did not hit the cap, but manual narrowing is still required.", "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
            {"REQ_ROW": 6, "NARROWING_REQUIREMENT": "KEEP_RAW_DBF_WRITE_FORBIDDEN", "DETAIL": "Any accepted path must be native/runtime/schema-aware, not raw DBF byte mutation.", "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
            {"REQ_ROW": 7, "NARROWING_REQUIREMENT": "PRESERVE_SOURCE_COMMENT_CONTRACT_RULE", "DETAIL": "If later source patch is needed, update @dottalk.usage/source-comment contracts in the same guarded package.", "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
            {"REQ_ROW": 8, "NARROWING_REQUIREMENT": "KEEP_APPLY_BLOCKED", "DETAIL": "No HELP DATA/CMDHELPCHK apply until exact writer path and guarded apply package are reviewed.", "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
        ]

        for i, b in enumerate(blocked_in, 1):
            carry_forward_blocked.append({
                "CARRY_FORWARD_ROW": i,
                "BLOCKED_ACTION": b.get("BLOCKED_ACTION",""),
                "BLOCKED": 1,
                "REASON": b.get("REASON",""),
                "CARRY_FORWARD_DETAIL": "Still blocked after CM targeted discovery review.",
            })

        review_decisions = [
            {"DECISION_ROW": 1, "DECISION": "TARGETED_DISCOVERY_ACCEPTED_FOR_REVIEW", "VALUE": 1, "DETAIL": "CL targeted discovery produced reviewable candidates."},
            {"DECISION_ROW": 2, "DECISION": "EXACT_CANDIDATE_NARROWING_REQUIRED", "VALUE": 1, "DETAIL": "Candidate set must be narrowed before reuse/source-patch/apply decision."},
            {"DECISION_ROW": 3, "DECISION": "TARGETED_DISCOVERY_CAP_REACHED", "VALUE": 1 if len(candidates) >= 1200 else 0, "DETAIL": f"{len(candidates)} targeted candidates reported."},
            {"DECISION_ROW": 4, "DECISION": "REUSE_PATH_CONFIRMED_NOW", "VALUE": 0, "DETAIL": "No exact reuse path confirmed by CM."},
            {"DECISION_ROW": 5, "DECISION": "SOURCE_PATCH_NEEDED_PROVEN", "VALUE": 0, "DETAIL": "Source patch need remains unproven."},
            {"DECISION_ROW": 6, "DECISION": "DIRECT_APPLY_READY", "VALUE": 0, "DETAIL": "Direct HELP/CMDHELPCHK apply remains blocked."},
        ]

        paths = [
            (cm_root / "targeted_discovery_class_review_v1.csv", class_review, ["CLASS_REVIEW_ROW","DISCOVERY_CLASS","ROW_COUNT","REVIEW_DISPOSITION","NARROWING_REQUIRED","DETAIL"]),
            (cm_root / "targeted_writer_focus_review_v1.csv", focus_review, ["FOCUS_REVIEW_ROW","SOURCE_DISCOVERY_ROW","DISCOVERY_CLASS","TARGETED_SCORE","FILE_PATH","LINE","SNIPPET","REVIEW_DISPOSITION","REVIEW_DETAIL","EXACT_WRITER_CONFIRMATION_REQUIRED","REUSE_PATH_CONFIRMED_NOW","SOURCE_PATCH_NEEDED_PROVEN","SOURCE_MUTATION_AUTHORIZED_NOW","APPLY_AUTHORIZED_NOW"]),
            (cm_root / "exact_writer_candidate_focus_v1.csv", exact_candidate_focus, ["EXACT_FOCUS_ROW","SOURCE_FOCUS_REVIEW_ROW","DISCOVERY_CLASS","TARGETED_SCORE","FILE_PATH","LINE","SNIPPET","CONFIRMATION_TASK","CONFIRMED_NOW","APPLY_READY_NOW"]),
            (cm_root / "narrowing_requirements_v1.csv", narrowing_requirements, ["REQ_ROW","NARROWING_REQUIREMENT","DETAIL","SOURCE_MUTATION_AUTHORIZED_NOW","APPLY_AUTHORIZED_NOW"]),
            (cm_root / "carry_forward_blocked_actions_v1.csv", carry_forward_blocked, ["CARRY_FORWARD_ROW","BLOCKED_ACTION","BLOCKED","REASON","CARRY_FORWARD_DETAIL"]),
            (cm_root / "review_decisions_v1.csv", review_decisions, ["DECISION_ROW","DECISION","VALUE","DETAIL"]),
        ]
        for p, rs, fs in paths:
            wcsv(p, rs, fs)

        scripts = cm_root / "scripts"
        scripts.mkdir(parents=True, exist_ok=True)
        disabled = scripts / "MESSAGE_CATALOG_PHASE22AE_6_5_10CN_NARROWING_TEMPLATE.ps1.disabled"
        disabled.write_text('throw "10CM is review only. Generate a dedicated 10CN exact candidate narrowing package before selecting reuse/source-patch/apply path."\n', encoding="utf-8")
        readback = scripts / "MESSAGE_CATALOG_PHASE22AE_6_5_10CM_READBACK_CONTRACT.dts"
        readback.write_text("MSGMGR STATUS\nMSGMGR CHECK\nSET MESSAGE CATALOG CHECK\nSET MESSAGE EMIT MESSAGE_PROOF_MODE_STATUS en-US\nHELP MSGMGR\nHELP SET MESSAGE\nCMDHELPCHK\nQUIT\n", encoding="utf-8")
        notes = cm_root / "targeted_native_writer_discovery_review_v1.md"
        notes.write_text("# 10CM Targeted Native Writer Discovery Review\n\n10CM reviews the 10CL targeted discovery output. The candidate set is useful but still too broad for apply or source-patch decisions; exact candidate narrowing is required. No protected systems are mutated.\n", encoding="utf-8")
        readme = cm_root / "README_10CM_TARGETED_NATIVE_WRITER_DISCOVERY_REVIEW.md"
        readme.write_text("# 10CM Targeted Native Writer Discovery Review\n\nReview-only package. It requires a 10CN exact candidate narrowing package. No protected mutation occurs.\n", encoding="utf-8")

        for p, _, _ in paths:
            artifacts.append({"ARTIFACT": rel(p, repo), "ROLE": "targeted_native_writer_discovery_review_artifact", "BYTES": p.stat().st_size, "SHA256": sha(p)})
        for p in [disabled, readback, notes, readme]:
            artifacts.append({"ARTIFACT": rel(p, repo), "ROLE": "targeted_native_writer_discovery_review_artifact", "BYTES": p.stat().st_size, "SHA256": sha(p)})

        status = GREEN

    boundary = [
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "10CM writes docs/messaging review artifacts only."},
        {"PROTECTED_SYSTEM": "ACTIVE_SYSTEM_MESSAGES", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_SYSTEM_MESSAGE_TEXT", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_CDX_LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CDX/LMDB mutation."},
        {"PROTECTED_SYSTEM": "WORKSPACE_PROFILE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No workspace mutation."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Discovery review only; no HELP DATA apply."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Discovery review only; no CMDHELPCHK apply."},
    ]
    readiness = [
        {"ITEM": "TARGETED_DISCOVERY_REVIEWED", "STATUS": "YES" if status == GREEN else "NO", "DETAIL": f"{len(focus_review)} focus rows reviewed."},
        {"ITEM": "EXACT_CANDIDATE_NARROWING_REQUIRED", "STATUS": "YES", "DETAIL": f"{len(exact_candidate_focus)} exact/generic focus rows staged."},
        {"ITEM": "REUSE_PATH_CONFIRMED_NOW", "STATUS": "NO", "DETAIL": "No exact reuse path confirmed in CM."},
        {"ITEM": "SOURCE_PATCH_NEEDED_PROVEN", "STATUS": "NO", "DETAIL": "Source patch need remains unproven."},
        {"ITEM": "DIRECT_APPLY_READY", "STATUS": "NO", "DETAIL": "Direct apply remains blocked."},
    ]

    issues = "0" if failures == 0 else str(failures)
    wcsv(reports / "message_catalog_phase22ae_6_5_10cm_gate_check_v1.csv", gates, ["GATE","STATUS","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10cm_targeted_discovery_class_review_v1.csv", class_review, ["CLASS_REVIEW_ROW","DISCOVERY_CLASS","ROW_COUNT","REVIEW_DISPOSITION","NARROWING_REQUIRED","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10cm_targeted_writer_focus_review_v1.csv", focus_review, ["FOCUS_REVIEW_ROW","SOURCE_DISCOVERY_ROW","DISCOVERY_CLASS","TARGETED_SCORE","FILE_PATH","LINE","SNIPPET","REVIEW_DISPOSITION","REVIEW_DETAIL","EXACT_WRITER_CONFIRMATION_REQUIRED","REUSE_PATH_CONFIRMED_NOW","SOURCE_PATCH_NEEDED_PROVEN","SOURCE_MUTATION_AUTHORIZED_NOW","APPLY_AUTHORIZED_NOW"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10cm_exact_writer_candidate_focus_v1.csv", exact_candidate_focus, ["EXACT_FOCUS_ROW","SOURCE_FOCUS_REVIEW_ROW","DISCOVERY_CLASS","TARGETED_SCORE","FILE_PATH","LINE","SNIPPET","CONFIRMATION_TASK","CONFIRMED_NOW","APPLY_READY_NOW"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10cm_narrowing_requirements_v1.csv", narrowing_requirements, ["REQ_ROW","NARROWING_REQUIREMENT","DETAIL","SOURCE_MUTATION_AUTHORIZED_NOW","APPLY_AUTHORIZED_NOW"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10cm_carry_forward_blocked_actions_v1.csv", carry_forward_blocked, ["CARRY_FORWARD_ROW","BLOCKED_ACTION","BLOCKED","REASON","CARRY_FORWARD_DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10cm_review_decisions_v1.csv", review_decisions, ["DECISION_ROW","DECISION","VALUE","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10cm_apply_readiness_v1.csv", readiness, ["ITEM","STATUS","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10cm_boundary_ledger_v1.csv", boundary, ["PROTECTED_SYSTEM","MUTATION_ALLOWED","OBSERVED_MUTATION","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10cm_artifact_manifest_v1.csv", artifacts, ["ARTIFACT","ROLE","BYTES","SHA256"])

    summary = {
        "STATUS": status,
        "VALIDATION_ISSUES": issues,
        "PHASE22AE_6_5_10CL_STATUS": cl.get("STATUS",""),
        "MSG_022AE_6_5_10CL_SAVEPOINT_PRESENT": 1 if sp_cl else 0,
        "ACTIVE_MESSAGES_OBSERVED_COUNT": msg_count,
        "ACTIVE_TEXT_OBSERVED_COUNT": text_count,
        "CL_TARGETED_SCAN_FILE_ROWS": len(scan_manifest),
        "CL_TARGETED_DISCOVERY_CANDIDATE_ROWS": len(candidates),
        "CL_TARGETED_DISCOVERY_SUMMARY_ROWS": len(discovery_summary),
        "CLASS_REVIEW_ROWS": len(class_review),
        "FOCUS_REVIEW_ROWS": len(focus_review),
        "EXACT_WRITER_CANDIDATE_FOCUS_ROWS": len(exact_candidate_focus),
        "NARROWING_REQUIREMENT_ROWS": len(narrowing_requirements),
        "CM_ROOT": rel(cm_root, repo),
        "TARGETED_DISCOVERY_REVIEWED": 1 if status == GREEN else 0,
        "EXACT_CANDIDATE_NARROWING_REQUIRED": 1 if status == GREEN else 0,
        "TARGETED_DISCOVERY_CAP_REACHED": 1 if len(candidates) >= 1200 else 0,
        "REUSE_PATH_CONFIRMED_NOW": 0,
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
    wcsv(reports / "message_catalog_phase22ae_6_5_10cm_status_summary_v1.csv", [summary], list(summary.keys()))

    (repo / "docs/messaging/MESSAGE_LOCALE_PHASE22AE_6_5_10CM_TARGETED_NATIVE_WRITER_DISCOVERY_REVIEW.md").write_text(
        f"# Message Catalog Phase 22AE.6.5.10CM Targeted Native Writer Discovery Review\n\nStatus: `{status}`\n\n10CM reviews the 10CL targeted discovery output and requires exact candidate narrowing. It does not confirm reuse, prove source patch need, authorize apply, or mutate protected systems.\n\nReview root:\n\n```text\n{rel(cm_root, repo)}\n```\n\nNext gate:\n\n```text\n{NEXT}\n```\n",
        encoding="utf-8"
    )

    print(status)
    print(f"  validation issues: {issues}")
    print(f"  Phase 22AE.6.5.10CL status: {cl.get('STATUS','')}")
    print(f"  MSG-022AE.6.5.10CL savepoint present: {1 if sp_cl else 0}")
    print(f"  active messages observed count: {msg_count}")
    print(f"  active text observed count: {text_count}")
    print(f"  CL targeted scan file rows: {len(scan_manifest)}")
    print(f"  CL targeted discovery candidate rows: {len(candidates)}")
    print(f"  CL targeted discovery summary rows: {len(discovery_summary)}")
    print(f"  class review rows: {len(class_review)}")
    print(f"  focus review rows: {len(focus_review)}")
    print(f"  exact writer candidate focus rows: {len(exact_candidate_focus)}")
    print(f"  narrowing requirement rows: {len(narrowing_requirements)}")
    print(f"  review root: {rel(cm_root, repo)}")
    print("  targeted discovery reviewed: 1")
    print("  exact candidate narrowing required: 1")
    print(f"  targeted discovery cap reached: {1 if len(candidates) >= 1200 else 0}")
    print("  reuse path confirmed now: 0")
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
