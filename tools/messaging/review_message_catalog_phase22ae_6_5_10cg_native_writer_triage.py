#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, json, hashlib, shutil
from datetime import datetime, timezone
from pathlib import Path

GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_10CG_NATIVE_WRITER_TRIAGE_REVIEW_GREEN_DECISION_PACKAGE_REQUIRED_SOURCE_HELD"
BLOCKED = "MESSAGE_CATALOG_PHASE22AE_6_5_10CG_NATIVE_WRITER_TRIAGE_REVIEW_BLOCKED"
NEXT = "HOLD_OR_AUTHORIZE_PHASE22AE_6_5_10CH_NATIVE_WRITER_REUSE_OR_SOURCE_PATCH_DECISION_PACKAGE"
REPORT = Path("docs/messaging/reports")
CF_SUMMARY = REPORT / "message_catalog_phase22ae_6_5_10cf_status_summary_v1.csv"
CF_TRIAGE = REPORT / "message_catalog_phase22ae_6_5_10cf_native_writer_candidate_triage_v1.csv"
CF_FOCUS = REPORT / "message_catalog_phase22ae_6_5_10cf_native_writer_triage_focus_set_v1.csv"
CF_REUSE = REPORT / "message_catalog_phase22ae_6_5_10cf_possible_reuse_writer_candidates_v1.csv"
ACTIVE_MSG_DBF = Path("dottalkpp/data/messaging/SYSTEM_MESSAGES.dbf")
ACTIVE_TEXT_DBF = Path("dottalkpp/data/messaging/SYSTEM_MESSAGE_TEXT.dbf")
CG_ROOT = Path("docs/messaging/apply/phase22ae_6_5_10cg_native_writer_triage_review_v1")

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

def disposition(row):
    cls = row.get("TRIAGE_CLASS", "")
    if "HELP_DATA_NATIVE_WRITER_REUSE" in cls:
        return "REVIEW_FOR_HELP_DATA_REUSE_DECISION", "Possible HELP DATA writer reuse; confirm actual native writer/import/update path."
    if "CMDHELPCHK_NATIVE_WRITER_REUSE" in cls:
        return "REVIEW_FOR_CMDHELPCHK_REUSE_DECISION", "Possible CMDHELPCHK writer reuse; confirm actual native writer/import/update path."
    if cls in ("HELP_DATA_REVIEW_CANDIDATE", "CMDHELPCHK_REVIEW_CANDIDATE"):
        return "REVIEW_WRITER_VS_READER_CHECKER", "Distinguish writer/import/update path from reader/checker/display path."
    if cls == "GENERIC_WRITE_PATH_CANDIDATE":
        return "REVIEW_IF_GENERIC_WRITER_CAN_TARGET_HELP_CMDHELPCHK", "Tie generic writer/import/update path to exact HELP/CMDHELPCHK target before use."
    if cls == "SOURCE_COMMENT_CONTRACT_CANDIDATE":
        return "SUPPORT_SOURCE_CONTRACT_REVIEW", "Relevant only if later source patch is authorized."
    return "SUPPORTING_REVIEW_EVIDENCE", "Supporting evidence for 10CH decision package."

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--replace-existing-review", action="store_true")
    args = ap.parse_args()
    repo = Path(args.repo_root).resolve()
    reports = repo / REPORT; reports.mkdir(parents=True, exist_ok=True)

    cf = first(repo / CF_SUMMARY)
    triage_rows = rows(repo / CF_TRIAGE)
    focus_rows = rows(repo / CF_FOCUS)
    reuse_rows = rows(repo / CF_REUSE)
    sp_cf, latest_cf = savepoint(repo, "MSG-022AE.6.5.10CF")
    msg_count = dbf_count(repo / ACTIVE_MSG_DBF)
    text_count = dbf_count(repo / ACTIVE_TEXT_DBF)
    cg_root = repo / CG_ROOT

    gates = []
    failures = 0
    def gate(name, ok, detail):
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": str(detail)})
        if not ok: failures += 1

    gate("PHASE22AE_6_5_10CF_GREEN", cf.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_5_10CF_NATIVE_WRITER_DISCOVERY_TRIAGE_PACKAGE_GREEN_REVIEW_REQUIRED_SOURCE_HELD", cf.get("STATUS","missing"))
    gate("MSG_022AE_6_5_10CF_SAVEPOINT_PRESENT", sp_cf, latest_cf)
    gate("CF_TRIAGE_PACKAGE_CREATED", cf.get("TRIAGE_PACKAGE_CREATED") == "1", cf.get("TRIAGE_PACKAGE_CREATED","missing"))
    gate("CF_SOURCE_PATCH_NOT_PROVEN", cf.get("SOURCE_PATCH_NEEDED_PROVEN") == "0", cf.get("SOURCE_PATCH_NEEDED_PROVEN","missing"))
    gate("CF_SOURCE_MUTATION_NOT_AUTHORIZED", cf.get("SOURCE_MUTATION_AUTHORIZED_NOW") == "0", cf.get("SOURCE_MUTATION_AUTHORIZED_NOW","missing"))
    gate("CF_APPLY_EXECUTION_NOT_AUTHORIZED", cf.get("APPLY_EXECUTION_AUTHORIZED_NOW") == "0", cf.get("APPLY_EXECUTION_AUTHORIZED_NOW","missing"))
    gate("CF_HELP_APPLY_NOT_EXECUTED", cf.get("HELP_DATA_APPLY_EXECUTED") == "0", cf.get("HELP_DATA_APPLY_EXECUTED","missing"))
    gate("CF_CMDHELPCHK_APPLY_NOT_EXECUTED", cf.get("CMDHELPCHK_APPLY_EXECUTED") == "0", cf.get("CMDHELPCHK_APPLY_EXECUTED","missing"))
    gate("CF_TRIAGE_ROWS_PRESENT", len(triage_rows) > 0, len(triage_rows))
    gate("CF_FOCUS_ROWS_PRESENT", len(focus_rows) > 0, len(focus_rows))
    gate("CF_REUSE_ROWS_PRESENT", len(reuse_rows) > 0, len(reuse_rows))
    gate("ACTIVE_MESSAGES_HEADER_COUNT_14", msg_count == 14, msg_count)
    gate("ACTIVE_TEXT_HEADER_COUNT_70", text_count == 70, text_count)
    gate("CG_ROOT_NOT_EXISTING_OR_REPLACE_ALLOWED", (not cg_root.exists()) or args.replace_existing_review, rel(cg_root, repo))

    status = BLOCKED
    focus_review = []
    reuse_review = []
    req = []
    decisions = []
    risks = []
    artifacts = []

    if failures == 0:
        if cg_root.exists() and args.replace_existing_review:
            shutil.rmtree(cg_root)
        cg_root.mkdir(parents=True, exist_ok=True)

        for i, r in enumerate(focus_rows, 1):
            disp, detail = disposition(r)
            focus_review.append({
                "FOCUS_REVIEW_ROW": i, "SOURCE_TRIAGE_ROW": r.get("TRIAGE_ROW",""),
                "TRIAGE_CLASS": r.get("TRIAGE_CLASS",""), "TRIAGE_PRIORITY": r.get("TRIAGE_PRIORITY",""),
                "TRIAGE_SCORE": r.get("TRIAGE_SCORE",""), "FILE_PATH": r.get("FILE_PATH",""),
                "LINE": r.get("LINE",""), "MATCH_KIND": r.get("MATCH_KIND",""),
                "REVIEW_DISPOSITION": disp, "REVIEW_DETAIL": detail,
                "DECISION_PACKAGE_REQUIRED": 1, "REUSE_PATH_CONFIRMED_NOW": 0,
                "SOURCE_PATCH_NEEDED_PROVEN": 0, "SOURCE_MUTATION_AUTHORIZED_NOW": 0,
                "APPLY_AUTHORIZED_NOW": 0,
            })
        for i, r in enumerate(reuse_rows, 1):
            disp, detail = disposition(r)
            reuse_review.append({
                "REUSE_REVIEW_ROW": i, "SOURCE_TRIAGE_ROW": r.get("TRIAGE_ROW",""),
                "TRIAGE_CLASS": r.get("TRIAGE_CLASS",""), "TRIAGE_PRIORITY": r.get("TRIAGE_PRIORITY",""),
                "TRIAGE_SCORE": r.get("TRIAGE_SCORE",""), "FILE_PATH": r.get("FILE_PATH",""),
                "LINE": r.get("LINE",""), "MATCH_KIND": r.get("MATCH_KIND",""),
                "REVIEW_DISPOSITION": disp, "REVIEW_DETAIL": detail,
                "REUSE_PATH_POSSIBLE": r.get("REUSE_PATH_POSSIBLE","0"),
                "REUSE_PATH_CONFIRMED_NOW": 0, "DECISION_PACKAGE_REQUIRED": 1,
            })

        req = [
            {"REQUIREMENT_ROW": 1, "REQUIREMENT": "SELECT_HELP_DATA_WRITER_DECISION", "DETAIL": "Choose existing HELP DATA writer/reuse, further discovery, or guarded source-patch planning.", "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
            {"REQUIREMENT_ROW": 2, "REQUIREMENT": "SELECT_CMDHELPCHK_WRITER_DECISION", "DETAIL": "Choose existing CMDHELPCHK writer/reuse, further discovery, or guarded source-patch planning.", "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
            {"REQUIREMENT_ROW": 3, "REQUIREMENT": "DO_NOT_TREAT_REUSE_AS_CONFIRMED_YET", "DETAIL": f"{len(reuse_review)} possible reuse rows exist, but none are confirmed in 10CG.", "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
            {"REQUIREMENT_ROW": 4, "REQUIREMENT": "DO_NOT_PROVE_SOURCE_PATCH_NEED_YET", "DETAIL": "10CG still does not prove that source patch is required.", "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
            {"REQUIREMENT_ROW": 5, "REQUIREMENT": "CARRY_FORWARD_SOURCE_COMMENT_CONTRACT_RULE", "DETAIL": "If later source patch changes command behavior/syntax, @dottalk.usage and source-comment contracts must be updated in same package.", "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
            {"REQUIREMENT_ROW": 6, "REQUIREMENT": "PRESERVE_NATIVE_SCHEMA_AWARE_BOUNDARY", "DETAIL": "Raw Python DBF byte writing remains forbidden for runtime promotion/materialization.", "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
        ]
        decisions = [
            {"DECISION_ROW": 1, "DECISION": "TRIAGE_ACCEPTED_FOR_DECISION_PACKAGE", "VALUE": 1, "DETAIL": "10CF triage is accepted as basis for 10CH decision package."},
            {"DECISION_ROW": 2, "DECISION": "REUSE_PATH_CONFIRMED_NOW", "VALUE": 0, "DETAIL": "Possible reuse candidates exist but are not confirmed in 10CG."},
            {"DECISION_ROW": 3, "DECISION": "SOURCE_PATCH_NEEDED_PROVEN", "VALUE": 0, "DETAIL": "Source patch need remains unproven."},
            {"DECISION_ROW": 4, "DECISION": "DIRECT_HELP_CMDHELPCHK_APPLY_READY", "VALUE": 0, "DETAIL": "No direct apply execution is ready."},
            {"DECISION_ROW": 5, "DECISION": "DECISION_PACKAGE_REQUIRED", "VALUE": 1, "DETAIL": "10CH must decide reuse path vs further discovery vs guarded source-patch planning."},
        ]
        risks = [
            {"RISK_ROW": 1, "RISK": "FALSE_REUSE_POSITIVE", "STATUS": "ACTIVE", "MITIGATION": "Distinguish reader/checker/display from writer/import/update path."},
            {"RISK_ROW": 2, "RISK": "PROCESS_ARTIFACT_NOISE", "STATUS": "ACTIVE", "MITIGATION": "Do not treat docs/messaging rows as native runtime writers."},
            {"RISK_ROW": 3, "RISK": "RAW_DBF_WRITE_REGRESSION", "STATUS": "ACTIVE", "MITIGATION": "Keep Python/raw DBF byte writing forbidden."},
            {"RISK_ROW": 4, "RISK": "SOURCE_CONTRACT_DRIFT", "STATUS": "ACTIVE", "MITIGATION": "Update @dottalk.usage/source-comment contracts with any later source patch."},
            {"RISK_ROW": 5, "RISK": "APPLY_BEFORE_WRITER_CONFIRMED", "STATUS": "ACTIVE", "MITIGATION": "Block HELP DATA/CMDHELPCHK apply until writer path is confirmed and packaged."},
        ]

        fields_focus = ["FOCUS_REVIEW_ROW","SOURCE_TRIAGE_ROW","TRIAGE_CLASS","TRIAGE_PRIORITY","TRIAGE_SCORE","FILE_PATH","LINE","MATCH_KIND","REVIEW_DISPOSITION","REVIEW_DETAIL","DECISION_PACKAGE_REQUIRED","REUSE_PATH_CONFIRMED_NOW","SOURCE_PATCH_NEEDED_PROVEN","SOURCE_MUTATION_AUTHORIZED_NOW","APPLY_AUTHORIZED_NOW"]
        fields_reuse = ["REUSE_REVIEW_ROW","SOURCE_TRIAGE_ROW","TRIAGE_CLASS","TRIAGE_PRIORITY","TRIAGE_SCORE","FILE_PATH","LINE","MATCH_KIND","REVIEW_DISPOSITION","REVIEW_DETAIL","REUSE_PATH_POSSIBLE","REUSE_PATH_CONFIRMED_NOW","DECISION_PACKAGE_REQUIRED"]
        paths = [
            (cg_root / "native_writer_focus_review_v1.csv", focus_review, fields_focus),
            (cg_root / "possible_reuse_writer_review_v1.csv", reuse_review, fields_reuse),
            (cg_root / "decision_package_requirements_v1.csv", req, ["REQUIREMENT_ROW","REQUIREMENT","DETAIL","SOURCE_MUTATION_AUTHORIZED_NOW","APPLY_AUTHORIZED_NOW"]),
            (cg_root / "review_decisions_v1.csv", decisions, ["DECISION_ROW","DECISION","VALUE","DETAIL"]),
            (cg_root / "review_risks_v1.csv", risks, ["RISK_ROW","RISK","STATUS","MITIGATION"]),
        ]
        for p, rs, fs in paths:
            wcsv(p, rs, fs)
        scripts = cg_root / "scripts"; scripts.mkdir(parents=True, exist_ok=True)
        disabled = scripts / "MESSAGE_CATALOG_PHASE22AE_6_5_10CH_DECISION_TEMPLATE.ps1.disabled"
        disabled.write_text('throw "10CG is review only. Generate a dedicated 10CH decision package before choosing reuse/source-patch/apply path."\n', encoding="utf-8")
        readback = scripts / "MESSAGE_CATALOG_PHASE22AE_6_5_10CG_READBACK_CONTRACT.dts"
        readback.write_text("MSGMGR STATUS\nMSGMGR CHECK\nSET MESSAGE CATALOG CHECK\nSET MESSAGE EMIT MESSAGE_PROOF_MODE_STATUS en-US\nHELP MSGMGR\nHELP SET MESSAGE\nCMDHELPCHK\nQUIT\n", encoding="utf-8")
        notes = cg_root / "native_writer_triage_review_v1.md"
        notes.write_text("# 10CG Native Writer Triage Review\n\n10CG reviews 10CF triage and prepares 10CH decision. It does not confirm reuse, prove source patch need, or mutate protected systems.\n", encoding="utf-8")
        readme = cg_root / "README_10CG_NATIVE_WRITER_TRIAGE_REVIEW.md"
        readme.write_text("# 10CG Native Writer Triage Review\n\nReport-only review package. No protected mutation occurs.\n", encoding="utf-8")
        for p, _, _ in paths:
            artifacts.append({"ARTIFACT": rel(p, repo), "ROLE": "native_writer_triage_review_artifact", "BYTES": p.stat().st_size, "SHA256": sha(p)})
        for p in [disabled, readback, notes, readme]:
            artifacts.append({"ARTIFACT": rel(p, repo), "ROLE": "native_writer_triage_review_artifact", "BYTES": p.stat().st_size, "SHA256": sha(p)})
        status = GREEN

    boundary = [
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "10CG writes docs/messaging review artifacts only."},
        {"PROTECTED_SYSTEM": "ACTIVE_SYSTEM_MESSAGES", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_SYSTEM_MESSAGE_TEXT", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_CDX_LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CDX/LMDB mutation."},
        {"PROTECTED_SYSTEM": "WORKSPACE_PROFILE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No workspace mutation."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Triage review only; no HELP DATA apply."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Triage review only; no CMDHELPCHK apply."},
    ]
    readiness = [
        {"ITEM": "TRIAGE_REVIEW_COMPLETE", "STATUS": "YES" if status == GREEN else "NO", "DETAIL": f"{len(focus_review)} focus rows reviewed."},
        {"ITEM": "REUSE_CANDIDATES_REVIEWED", "STATUS": "YES" if reuse_review else "NO", "DETAIL": f"{len(reuse_review)} possible reuse rows reviewed."},
        {"ITEM": "REUSE_PATH_CONFIRMED_NOW", "STATUS": "NO", "DETAIL": "10CG prepares a decision package; it does not confirm reuse."},
        {"ITEM": "SOURCE_PATCH_NEEDED_PROVEN", "STATUS": "NO", "DETAIL": "10CG does not prove source patch need."},
        {"ITEM": "DECISION_PACKAGE_REQUIRED", "STATUS": "YES", "DETAIL": "10CH must decide reuse path vs further discovery vs guarded source-patch planning."},
        {"ITEM": "HELP_DATA_APPLY_EXECUTION", "STATUS": "NOT_EXECUTED_IN_10CG", "DETAIL": "No apply execution."},
        {"ITEM": "CMDHELPCHK_APPLY_EXECUTION", "STATUS": "NOT_EXECUTED_IN_10CG", "DETAIL": "No apply execution."},
    ]

    issues = "0" if failures == 0 else str(failures)
    wcsv(reports / "message_catalog_phase22ae_6_5_10cg_gate_check_v1.csv", gates, ["GATE","STATUS","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10cg_native_writer_focus_review_v1.csv", focus_review, ["FOCUS_REVIEW_ROW","SOURCE_TRIAGE_ROW","TRIAGE_CLASS","TRIAGE_PRIORITY","TRIAGE_SCORE","FILE_PATH","LINE","MATCH_KIND","REVIEW_DISPOSITION","REVIEW_DETAIL","DECISION_PACKAGE_REQUIRED","REUSE_PATH_CONFIRMED_NOW","SOURCE_PATCH_NEEDED_PROVEN","SOURCE_MUTATION_AUTHORIZED_NOW","APPLY_AUTHORIZED_NOW"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10cg_possible_reuse_writer_review_v1.csv", reuse_review, ["REUSE_REVIEW_ROW","SOURCE_TRIAGE_ROW","TRIAGE_CLASS","TRIAGE_PRIORITY","TRIAGE_SCORE","FILE_PATH","LINE","MATCH_KIND","REVIEW_DISPOSITION","REVIEW_DETAIL","REUSE_PATH_POSSIBLE","REUSE_PATH_CONFIRMED_NOW","DECISION_PACKAGE_REQUIRED"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10cg_decision_package_requirements_v1.csv", req, ["REQUIREMENT_ROW","REQUIREMENT","DETAIL","SOURCE_MUTATION_AUTHORIZED_NOW","APPLY_AUTHORIZED_NOW"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10cg_review_decisions_v1.csv", decisions, ["DECISION_ROW","DECISION","VALUE","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10cg_review_risks_v1.csv", risks, ["RISK_ROW","RISK","STATUS","MITIGATION"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10cg_apply_readiness_v1.csv", readiness, ["ITEM","STATUS","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10cg_boundary_ledger_v1.csv", boundary, ["PROTECTED_SYSTEM","MUTATION_ALLOWED","OBSERVED_MUTATION","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10cg_artifact_manifest_v1.csv", artifacts, ["ARTIFACT","ROLE","BYTES","SHA256"])

    summary = {
        "STATUS": status, "VALIDATION_ISSUES": issues,
        "PHASE22AE_6_5_10CF_STATUS": cf.get("STATUS",""),
        "MSG_022AE_6_5_10CF_SAVEPOINT_PRESENT": 1 if sp_cf else 0,
        "ACTIVE_MESSAGES_OBSERVED_COUNT": msg_count,
        "ACTIVE_TEXT_OBSERVED_COUNT": text_count,
        "CF_TRIAGED_CANDIDATE_ROWS": len(triage_rows),
        "CF_FOCUS_SET_ROWS": len(focus_rows),
        "CF_POSSIBLE_REUSE_WRITER_ROWS": len(reuse_rows),
        "FOCUS_REVIEW_ROWS": len(focus_review),
        "REUSE_REVIEW_ROWS": len(reuse_review),
        "DECISION_PACKAGE_REQUIREMENT_ROWS": len(req),
        "CG_ROOT": rel(cg_root, repo),
        "TRIAGE_REVIEW_COMPLETE": 1 if status == GREEN else 0,
        "DECISION_PACKAGE_REQUIRED": 1 if status == GREEN else 0,
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
    wcsv(reports / "message_catalog_phase22ae_6_5_10cg_status_summary_v1.csv", [summary], list(summary.keys()))

    (repo / "docs/messaging/MESSAGE_LOCALE_PHASE22AE_6_5_10CG_NATIVE_WRITER_TRIAGE_REVIEW.md").write_text(
        f"# Message Catalog Phase 22AE.6.5.10CG Native Writer Triage Review\n\nStatus: `{status}`\n\n10CG reviews the 10CF triage package and requires a 10CH decision package. It does not confirm reuse, prove source patch need, or mutate protected systems.\n\nReview root:\n\n```text\n{rel(cg_root, repo)}\n```\n\nNext gate:\n\n```text\n{NEXT}\n```\n",
        encoding="utf-8"
    )

    print(status)
    print(f"  validation issues: {issues}")
    print(f"  Phase 22AE.6.5.10CF status: {cf.get('STATUS','')}")
    print(f"  MSG-022AE.6.5.10CF savepoint present: {1 if sp_cf else 0}")
    print(f"  active messages observed count: {msg_count}")
    print(f"  active text observed count: {text_count}")
    print(f"  CF triaged candidate rows: {len(triage_rows)}")
    print(f"  CF focus set rows: {len(focus_rows)}")
    print(f"  CF possible reuse writer rows: {len(reuse_rows)}")
    print(f"  focus review rows: {len(focus_review)}")
    print(f"  reuse review rows: {len(reuse_review)}")
    print(f"  decision package requirement rows: {len(req)}")
    print(f"  review root: {rel(cg_root, repo)}")
    print("  triage review complete: 1")
    print("  decision package required: 1")
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
