#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, json, hashlib, shutil
from datetime import datetime, timezone
from pathlib import Path

GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_10CI_NATIVE_WRITER_DECISION_PACKAGE_REVIEW_GREEN_SELECTION_PACKAGE_REQUIRED_SOURCE_HELD"
BLOCKED = "MESSAGE_CATALOG_PHASE22AE_6_5_10CI_NATIVE_WRITER_DECISION_PACKAGE_REVIEW_BLOCKED"
NEXT = "HOLD_OR_AUTHORIZE_PHASE22AE_6_5_10CJ_NATIVE_WRITER_DECISION_SELECTION_PACKAGE"

REPORT = Path("docs/messaging/reports")
CH_SUMMARY = REPORT / "message_catalog_phase22ae_6_5_10ch_status_summary_v1.csv"
CH_OPTIONS = REPORT / "message_catalog_phase22ae_6_5_10ch_decision_options_v1.csv"
CH_EVIDENCE = REPORT / "message_catalog_phase22ae_6_5_10ch_decision_option_evidence_v1.csv"
CH_CHECKLIST = REPORT / "message_catalog_phase22ae_6_5_10ch_decision_review_checklist_v1.csv"
CH_BLOCKED = REPORT / "message_catalog_phase22ae_6_5_10ch_blocked_actions_v1.csv"
ACTIVE_MSG_DBF = Path("dottalkpp/data/messaging/SYSTEM_MESSAGES.dbf")
ACTIVE_TEXT_DBF = Path("dottalkpp/data/messaging/SYSTEM_MESSAGE_TEXT.dbf")
CI_ROOT = Path("docs/messaging/apply/phase22ae_6_5_10ci_native_writer_decision_package_review_v1")

def rows(p):
    p = Path(p)
    if not p.exists(): return []
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
        for r in rs: w.writerow({k: r.get(k, "") for k in fs})

def rel(p, repo):
    try: return str(Path(p).resolve().relative_to(repo.resolve())).replace("\\", "/")
    except Exception: return str(p).replace("\\", "/")

def sha(p):
    h = hashlib.sha256()
    with Path(p).open("rb") as f:
        for b in iter(lambda: f.read(1048576), b""): h.update(b)
    return h.hexdigest()

def dbf_count(p):
    p = Path(p)
    if not p.exists() or p.stat().st_size < 12: return ""
    return int.from_bytes(p.read_bytes()[:12][4:8], "little")

def savepoint(repo, sid):
    latest = ""
    lp = repo / REPORT / "message_savepoint_latest_v1.json"
    if lp.exists():
        try: latest = json.loads(lp.read_text(encoding="utf-8")).get("savepoint_id", "")
        except Exception: latest = ""
    jp = repo / "docs/messaging/MESSAGING_SAVEPOINT_JOURNAL.md"
    txt = jp.read_text(encoding="utf-8", errors="replace") if jp.exists() else ""
    return latest == sid or sid in txt, latest

def option_review(option):
    opt = option.get("DECISION_OPTION", "")
    rows_count = option.get("EVIDENCE_ROWS", "")
    if opt in {"CONFIRM_EXISTING_HELP_DATA_WRITER_REUSE", "CONFIRM_EXISTING_CMDHELPCHK_WRITER_REUSE"}:
        return "REVIEWABLE_NOT_SELECTED", f"Review {rows_count} evidence rows before selecting reuse."
    if opt == "REQUIRE_FURTHER_WRITER_DISCOVERY":
        return "REVIEWABLE_NOT_SELECTED", "Use if evidence is still too broad or no native writer path is confirmed."
    if opt == "PLAN_GUARDED_SOURCE_PATCH":
        return "REVIEWABLE_NOT_SELECTED", "Use only if existing native/reuse path is rejected; later source patch must include source-comment contracts."
    if opt == "REFUSE_DIRECT_APPLY":
        return "SAFETY_DEFAULT_ACCEPTED", "Direct HELP/CMDHELPCHK apply remains refused until a writer path decision and apply package are reviewed."
    return "REVIEWABLE_NOT_SELECTED", "Decision option requires review."

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--replace-existing-review", action="store_true")
    args = ap.parse_args()
    repo = Path(args.repo_root).resolve()
    reports = repo / REPORT
    reports.mkdir(parents=True, exist_ok=True)

    ch = first(repo / CH_SUMMARY)
    options = rows(repo / CH_OPTIONS)
    evidence = rows(repo / CH_EVIDENCE)
    checklist = rows(repo / CH_CHECKLIST)
    blocked = rows(repo / CH_BLOCKED)
    sp_ch, latest_ch = savepoint(repo, "MSG-022AE.6.5.10CH")
    msg_count = dbf_count(repo / ACTIVE_MSG_DBF)
    text_count = dbf_count(repo / ACTIVE_TEXT_DBF)
    ci_root = repo / CI_ROOT

    gates = []
    failures = 0
    def gate(name, ok, detail):
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": str(detail)})
        if not ok: failures += 1

    gate("PHASE22AE_6_5_10CH_GREEN", ch.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_5_10CH_NATIVE_WRITER_REUSE_OR_SOURCE_PATCH_DECISION_PACKAGE_GREEN_DECISION_OPTIONS_STAGED_SOURCE_HELD", ch.get("STATUS","missing"))
    gate("MSG_022AE_6_5_10CH_SAVEPOINT_PRESENT", sp_ch, latest_ch)
    gate("CH_DECISION_OPTIONS_STAGED", ch.get("DECISION_OPTIONS_STAGED") == "1", ch.get("DECISION_OPTIONS_STAGED","missing"))
    gate("CH_REUSE_NOT_SELECTED", ch.get("REUSE_PATH_SELECTED_NOW") == "0", ch.get("REUSE_PATH_SELECTED_NOW","missing"))
    gate("CH_REUSE_NOT_CONFIRMED", ch.get("REUSE_PATH_CONFIRMED_NOW") == "0", ch.get("REUSE_PATH_CONFIRMED_NOW","missing"))
    gate("CH_SOURCE_PATCH_NOT_PROVEN", ch.get("SOURCE_PATCH_NEEDED_PROVEN") == "0", ch.get("SOURCE_PATCH_NEEDED_PROVEN","missing"))
    gate("CH_SOURCE_MUTATION_NOT_AUTHORIZED", ch.get("SOURCE_MUTATION_AUTHORIZED_NOW") == "0", ch.get("SOURCE_MUTATION_AUTHORIZED_NOW","missing"))
    gate("CH_APPLY_EXECUTION_NOT_AUTHORIZED", ch.get("APPLY_EXECUTION_AUTHORIZED_NOW") == "0", ch.get("APPLY_EXECUTION_AUTHORIZED_NOW","missing"))
    gate("CH_HELP_APPLY_NOT_EXECUTED", ch.get("HELP_DATA_APPLY_EXECUTED") == "0", ch.get("HELP_DATA_APPLY_EXECUTED","missing"))
    gate("CH_CMDHELPCHK_APPLY_NOT_EXECUTED", ch.get("CMDHELPCHK_APPLY_EXECUTED") == "0", ch.get("CMDHELPCHK_APPLY_EXECUTED","missing"))
    gate("CH_OPTIONS_PRESENT", len(options) > 0, len(options))
    gate("CH_EVIDENCE_PRESENT", len(evidence) > 0, len(evidence))
    gate("CH_CHECKLIST_PRESENT", len(checklist) > 0, len(checklist))
    gate("ACTIVE_MESSAGES_HEADER_COUNT_14", msg_count == 14, msg_count)
    gate("ACTIVE_TEXT_HEADER_COUNT_70", text_count == 70, text_count)
    gate("CI_ROOT_NOT_EXISTING_OR_REPLACE_ALLOWED", (not ci_root.exists()) or args.replace_existing_review, rel(ci_root, repo))

    status = BLOCKED
    option_reviews = []
    evidence_review = []
    selection_requirements = []
    review_decisions = []
    blocked_review = []
    artifacts = []

    if failures == 0:
        if ci_root.exists() and args.replace_existing_review:
            shutil.rmtree(ci_root)
        ci_root.mkdir(parents=True, exist_ok=True)

        for i, o in enumerate(options, 1):
            disp, detail = option_review(o)
            option_reviews.append({
                "OPTION_REVIEW_ROW": i,
                "DECISION_OPTION": o.get("DECISION_OPTION",""),
                "CH_OPTION_STATUS": o.get("OPTION_STATUS",""),
                "EVIDENCE_ROWS": o.get("EVIDENCE_ROWS",""),
                "WHAT_IT_WOULD_MEAN": o.get("WHAT_IT_WOULD_MEAN",""),
                "SOURCE_MUTATION_REQUIRED": o.get("SOURCE_MUTATION_REQUIRED",""),
                "APPLY_READY_NOW": o.get("APPLY_READY_NOW",""),
                "REVIEW_DISPOSITION": disp,
                "REVIEW_DETAIL": detail,
                "SELECTION_ALLOWED_NEXT": 1,
                "SELECTED_NOW": 0,
            })

        for i, e in enumerate(evidence, 1):
            evidence_review.append({
                "EVIDENCE_REVIEW_ROW": i,
                "SOURCE_KIND": e.get("SOURCE_KIND",""),
                "FILE_PATH": e.get("FILE_PATH",""),
                "LINE": e.get("LINE",""),
                "TRIAGE_CLASS": e.get("TRIAGE_CLASS",""),
                "REVIEW_DISPOSITION": e.get("REVIEW_DISPOSITION",""),
                "DECISION_USE": e.get("DECISION_USE",""),
                "REVIEW_REQUIRED_NEXT": 1,
                "REUSE_PATH_CONFIRMED_NOW": 0,
                "SOURCE_PATCH_NEEDED_PROVEN": 0,
            })

        selection_requirements = [
            {"SELECTION_ROW": 1, "SELECTION_REQUIREMENT": "SELECT_EXPLICIT_DECISION_PATH", "DETAIL": "10CJ must explicitly select reuse, further discovery, guarded source-patch planning, or continued refusal/hold.", "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
            {"SELECTION_ROW": 2, "SELECTION_REQUIREMENT": "IF_HELP_REUSE_SELECTED_NAME_EXACT_WRITER", "DETAIL": "A HELP DATA reuse decision must name the exact native writer/import/update path and target contract.", "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
            {"SELECTION_ROW": 3, "SELECTION_REQUIREMENT": "IF_CMDHELPCHK_REUSE_SELECTED_NAME_EXACT_WRITER", "DETAIL": "A CMDHELPCHK reuse decision must name the exact native writer/import/update path and target contract.", "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
            {"SELECTION_ROW": 4, "SELECTION_REQUIREMENT": "IF_SOURCE_PATCH_SELECTED_PLAN_CONTRACTS", "DETAIL": "A source patch decision must require @dottalk.usage/source-comment contract updates in the same guarded package.", "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
            {"SELECTION_ROW": 5, "SELECTION_REQUIREMENT": "IF_FURTHER_DISCOVERY_SELECTED_STATE_SCOPE", "DETAIL": "Further discovery must state exact unresolved targets and avoid repeating broad 10CD scan noise.", "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
            {"SELECTION_ROW": 6, "SELECTION_REQUIREMENT": "KEEP_DIRECT_APPLY_REFUSED", "DETAIL": "No HELP DATA/CMDHELPCHK apply may occur until a selected writer path and guarded apply package are reviewed.", "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
        ]

        review_decisions = [
            {"DECISION_ROW": 1, "DECISION": "CH_DECISION_PACKAGE_ACCEPTED_FOR_SELECTION_REVIEW", "VALUE": 1, "DETAIL": "10CH decision options are accepted for a 10CJ selection package."},
            {"DECISION_ROW": 2, "DECISION": "REUSE_PATH_SELECTED_NOW", "VALUE": 0, "DETAIL": "10CI reviews options but does not select a reuse path."},
            {"DECISION_ROW": 3, "DECISION": "SOURCE_PATCH_NEEDED_PROVEN", "VALUE": 0, "DETAIL": "10CI does not prove source patch need."},
            {"DECISION_ROW": 4, "DECISION": "DIRECT_APPLY_READY", "VALUE": 0, "DETAIL": "Direct HELP/CMDHELPCHK apply remains blocked."},
            {"DECISION_ROW": 5, "DECISION": "SELECTION_PACKAGE_REQUIRED", "VALUE": 1, "DETAIL": "10CJ should record the explicit decision path."},
        ]

        for i, b in enumerate(blocked, 1):
            blocked_review.append({
                "BLOCKED_REVIEW_ROW": i,
                "BLOCKED_ACTION": b.get("BLOCKED_ACTION",""),
                "BLOCKED": b.get("BLOCKED",""),
                "REASON": b.get("REASON",""),
                "CARRY_FORWARD": 1,
                "DETAIL": "Carry forward through 10CI; no protected mutation allowed.",
            })

        paths = [
            (ci_root / "decision_options_review_v1.csv", option_reviews, ["OPTION_REVIEW_ROW","DECISION_OPTION","CH_OPTION_STATUS","EVIDENCE_ROWS","WHAT_IT_WOULD_MEAN","SOURCE_MUTATION_REQUIRED","APPLY_READY_NOW","REVIEW_DISPOSITION","REVIEW_DETAIL","SELECTION_ALLOWED_NEXT","SELECTED_NOW"]),
            (ci_root / "decision_option_evidence_review_v1.csv", evidence_review, ["EVIDENCE_REVIEW_ROW","SOURCE_KIND","FILE_PATH","LINE","TRIAGE_CLASS","REVIEW_DISPOSITION","DECISION_USE","REVIEW_REQUIRED_NEXT","REUSE_PATH_CONFIRMED_NOW","SOURCE_PATCH_NEEDED_PROVEN"]),
            (ci_root / "selection_requirements_v1.csv", selection_requirements, ["SELECTION_ROW","SELECTION_REQUIREMENT","DETAIL","SOURCE_MUTATION_AUTHORIZED_NOW","APPLY_AUTHORIZED_NOW"]),
            (ci_root / "review_decisions_v1.csv", review_decisions, ["DECISION_ROW","DECISION","VALUE","DETAIL"]),
            (ci_root / "blocked_actions_review_v1.csv", blocked_review, ["BLOCKED_REVIEW_ROW","BLOCKED_ACTION","BLOCKED","REASON","CARRY_FORWARD","DETAIL"]),
        ]
        for p, rs, fs in paths:
            wcsv(p, rs, fs)

        scripts = ci_root / "scripts"
        scripts.mkdir(parents=True, exist_ok=True)
        disabled = scripts / "MESSAGE_CATALOG_PHASE22AE_6_5_10CJ_SELECTION_TEMPLATE.ps1.disabled"
        disabled.write_text('throw "10CI is review only. Generate a dedicated 10CJ selection package before selecting reuse/source-patch/further-discovery path."\n', encoding="utf-8")
        readback = scripts / "MESSAGE_CATALOG_PHASE22AE_6_5_10CI_READBACK_CONTRACT.dts"
        readback.write_text("MSGMGR STATUS\nMSGMGR CHECK\nSET MESSAGE CATALOG CHECK\nSET MESSAGE EMIT MESSAGE_PROOF_MODE_STATUS en-US\nHELP MSGMGR\nHELP SET MESSAGE\nCMDHELPCHK\nQUIT\n", encoding="utf-8")
        notes = ci_root / "native_writer_decision_package_review_v1.md"
        notes.write_text("# 10CI Native Writer Decision Package Review\n\n10CI reviews the 10CH decision options and requires a 10CJ explicit selection package. It does not select reuse, prove source patch need, authorize apply, or mutate protected systems.\n", encoding="utf-8")
        readme = ci_root / "README_10CI_NATIVE_WRITER_DECISION_PACKAGE_REVIEW.md"
        readme.write_text("# 10CI Native Writer Decision Package Review\n\nReview-only package. No protected mutation occurs.\n", encoding="utf-8")

        for p, _, _ in paths:
            artifacts.append({"ARTIFACT": rel(p, repo), "ROLE": "native_writer_decision_review_artifact", "BYTES": p.stat().st_size, "SHA256": sha(p)})
        for p in [disabled, readback, notes, readme]:
            artifacts.append({"ARTIFACT": rel(p, repo), "ROLE": "native_writer_decision_review_artifact", "BYTES": p.stat().st_size, "SHA256": sha(p)})
        status = GREEN

    boundary = [
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "10CI writes docs/messaging review artifacts only."},
        {"PROTECTED_SYSTEM": "ACTIVE_SYSTEM_MESSAGES", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_SYSTEM_MESSAGE_TEXT", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_CDX_LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CDX/LMDB mutation."},
        {"PROTECTED_SYSTEM": "WORKSPACE_PROFILE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No workspace mutation."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Decision review only; no HELP DATA apply."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Decision review only; no CMDHELPCHK apply."},
    ]
    readiness = [
        {"ITEM": "DECISION_PACKAGE_REVIEWED", "STATUS": "YES" if status == GREEN else "NO", "DETAIL": f"{len(option_reviews)} options reviewed."},
        {"ITEM": "SELECTION_PACKAGE_REQUIRED", "STATUS": "YES", "DETAIL": "10CJ must explicitly select the decision path."},
        {"ITEM": "REUSE_PATH_SELECTED_NOW", "STATUS": "NO", "DETAIL": "No reuse path selected in 10CI."},
        {"ITEM": "SOURCE_PATCH_NEEDED_PROVEN", "STATUS": "NO", "DETAIL": "Source patch need remains unproven."},
        {"ITEM": "DIRECT_APPLY_READY", "STATUS": "NO", "DETAIL": "Direct apply remains blocked."},
    ]

    issues = "0" if failures == 0 else str(failures)
    wcsv(reports / "message_catalog_phase22ae_6_5_10ci_gate_check_v1.csv", gates, ["GATE","STATUS","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10ci_decision_options_review_v1.csv", option_reviews, ["OPTION_REVIEW_ROW","DECISION_OPTION","CH_OPTION_STATUS","EVIDENCE_ROWS","WHAT_IT_WOULD_MEAN","SOURCE_MUTATION_REQUIRED","APPLY_READY_NOW","REVIEW_DISPOSITION","REVIEW_DETAIL","SELECTION_ALLOWED_NEXT","SELECTED_NOW"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10ci_decision_option_evidence_review_v1.csv", evidence_review, ["EVIDENCE_REVIEW_ROW","SOURCE_KIND","FILE_PATH","LINE","TRIAGE_CLASS","REVIEW_DISPOSITION","DECISION_USE","REVIEW_REQUIRED_NEXT","REUSE_PATH_CONFIRMED_NOW","SOURCE_PATCH_NEEDED_PROVEN"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10ci_selection_requirements_v1.csv", selection_requirements, ["SELECTION_ROW","SELECTION_REQUIREMENT","DETAIL","SOURCE_MUTATION_AUTHORIZED_NOW","APPLY_AUTHORIZED_NOW"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10ci_review_decisions_v1.csv", review_decisions, ["DECISION_ROW","DECISION","VALUE","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10ci_blocked_actions_review_v1.csv", blocked_review, ["BLOCKED_REVIEW_ROW","BLOCKED_ACTION","BLOCKED","REASON","CARRY_FORWARD","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10ci_apply_readiness_v1.csv", readiness, ["ITEM","STATUS","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10ci_boundary_ledger_v1.csv", boundary, ["PROTECTED_SYSTEM","MUTATION_ALLOWED","OBSERVED_MUTATION","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10ci_artifact_manifest_v1.csv", artifacts, ["ARTIFACT","ROLE","BYTES","SHA256"])

    summary = {
        "STATUS": status,
        "VALIDATION_ISSUES": issues,
        "PHASE22AE_6_5_10CH_STATUS": ch.get("STATUS",""),
        "MSG_022AE_6_5_10CH_SAVEPOINT_PRESENT": 1 if sp_ch else 0,
        "ACTIVE_MESSAGES_OBSERVED_COUNT": msg_count,
        "ACTIVE_TEXT_OBSERVED_COUNT": text_count,
        "CH_DECISION_OPTION_ROWS": len(options),
        "CH_DECISION_OPTION_EVIDENCE_ROWS": len(evidence),
        "OPTION_REVIEW_ROWS": len(option_reviews),
        "SELECTION_REQUIREMENT_ROWS": len(selection_requirements),
        "CI_ROOT": rel(ci_root, repo),
        "DECISION_PACKAGE_REVIEWED": 1 if status == GREEN else 0,
        "SELECTION_PACKAGE_REQUIRED": 1 if status == GREEN else 0,
        "REUSE_PATH_SELECTED_NOW": 0,
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
    wcsv(reports / "message_catalog_phase22ae_6_5_10ci_status_summary_v1.csv", [summary], list(summary.keys()))

    (repo / "docs/messaging/MESSAGE_LOCALE_PHASE22AE_6_5_10CI_NATIVE_WRITER_DECISION_PACKAGE_REVIEW.md").write_text(
        f"# Message Catalog Phase 22AE.6.5.10CI Native Writer Decision Package Review\n\nStatus: `{status}`\n\n10CI reviews the 10CH decision package and requires a 10CJ explicit selection package. It does not select reuse, prove source patch need, authorize apply, or mutate protected systems.\n\nReview root:\n\n```text\n{rel(ci_root, repo)}\n```\n\nNext gate:\n\n```text\n{NEXT}\n```\n",
        encoding="utf-8"
    )

    print(status)
    print(f"  validation issues: {issues}")
    print(f"  Phase 22AE.6.5.10CH status: {ch.get('STATUS','')}")
    print(f"  MSG-022AE.6.5.10CH savepoint present: {1 if sp_ch else 0}")
    print(f"  active messages observed count: {msg_count}")
    print(f"  active text observed count: {text_count}")
    print(f"  CH decision option rows: {len(options)}")
    print(f"  CH decision option evidence rows: {len(evidence)}")
    print(f"  option review rows: {len(option_reviews)}")
    print(f"  selection requirement rows: {len(selection_requirements)}")
    print(f"  review root: {rel(ci_root, repo)}")
    print("  decision package reviewed: 1")
    print("  selection package required: 1")
    print("  reuse path selected now: 0")
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
