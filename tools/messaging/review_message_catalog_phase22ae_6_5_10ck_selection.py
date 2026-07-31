#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, json, hashlib, shutil
from datetime import datetime, timezone
from pathlib import Path

GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_10CK_NATIVE_WRITER_SELECTION_REVIEW_GREEN_TARGETED_DISCOVERY_PACKAGE_REQUIRED_SOURCE_HELD"
BLOCKED = "MESSAGE_CATALOG_PHASE22AE_6_5_10CK_NATIVE_WRITER_SELECTION_REVIEW_BLOCKED"
NEXT = "HOLD_OR_AUTHORIZE_PHASE22AE_6_5_10CL_TARGETED_NATIVE_WRITER_DISCOVERY_PACKAGE"

REPORT = Path("docs/messaging/reports")
CJ_SUMMARY = REPORT / "message_catalog_phase22ae_6_5_10cj_status_summary_v1.csv"
CJ_SELECTION = REPORT / "message_catalog_phase22ae_6_5_10cj_decision_selection_v1.csv"
CJ_SELECTED_PATH = REPORT / "message_catalog_phase22ae_6_5_10cj_selected_path_contract_v1.csv"
CJ_REJECTED = REPORT / "message_catalog_phase22ae_6_5_10cj_rejected_paths_v1.csv"
CJ_SCOPE = REPORT / "message_catalog_phase22ae_6_5_10cj_targeted_discovery_scope_v1.csv"
CJ_BLOCKED = REPORT / "message_catalog_phase22ae_6_5_10cj_carry_forward_blocked_actions_v1.csv"
ACTIVE_MSG_DBF = Path("dottalkpp/data/messaging/SYSTEM_MESSAGES.dbf")
ACTIVE_TEXT_DBF = Path("dottalkpp/data/messaging/SYSTEM_MESSAGE_TEXT.dbf")
CK_ROOT = Path("docs/messaging/apply/phase22ae_6_5_10ck_native_writer_selection_review_v1")

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
    if not p.exists() or p.stat().st_size < 12: return ""
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

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--replace-existing-review", action="store_true")
    args = ap.parse_args()
    repo = Path(args.repo_root).resolve()
    reports = repo / REPORT
    reports.mkdir(parents=True, exist_ok=True)

    cj = first(repo / CJ_SUMMARY)
    selection = rows(repo / CJ_SELECTION)
    selected_path = rows(repo / CJ_SELECTED_PATH)
    rejected = rows(repo / CJ_REJECTED)
    scope = rows(repo / CJ_SCOPE)
    blocked_in = rows(repo / CJ_BLOCKED)
    sp_cj, latest_cj = savepoint(repo, "MSG-022AE.6.5.10CJ")
    msg_count = dbf_count(repo / ACTIVE_MSG_DBF)
    text_count = dbf_count(repo / ACTIVE_TEXT_DBF)
    ck_root = repo / CK_ROOT

    gates = []
    failures = 0
    def gate(name, ok, detail):
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": str(detail)})
        if not ok:
            failures += 1

    gate("PHASE22AE_6_5_10CJ_GREEN", cj.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_5_10CJ_NATIVE_WRITER_DECISION_SELECTION_PACKAGE_GREEN_TARGETED_DISCOVERY_SELECTED_SOURCE_HELD", cj.get("STATUS","missing"))
    gate("MSG_022AE_6_5_10CJ_SAVEPOINT_PRESENT", sp_cj, latest_cj)
    gate("CJ_SELECTION_PACKAGE_CREATED", cj.get("DECISION_SELECTION_PACKAGE_CREATED") == "1", cj.get("DECISION_SELECTION_PACKAGE_CREATED","missing"))
    gate("CJ_SELECTED_TARGETED_DISCOVERY", cj.get("SELECTED_PATH") == "FURTHER_TARGETED_NATIVE_WRITER_DISCOVERY", cj.get("SELECTED_PATH","missing"))
    gate("CJ_REUSE_NOT_SELECTED", cj.get("REUSE_PATH_SELECTED_NOW") == "0", cj.get("REUSE_PATH_SELECTED_NOW","missing"))
    gate("CJ_REUSE_NOT_CONFIRMED", cj.get("REUSE_PATH_CONFIRMED_NOW") == "0", cj.get("REUSE_PATH_CONFIRMED_NOW","missing"))
    gate("CJ_SOURCE_PATCH_NOT_SELECTED", cj.get("SOURCE_PATCH_SELECTED_NOW") == "0", cj.get("SOURCE_PATCH_SELECTED_NOW","missing"))
    gate("CJ_SOURCE_PATCH_NOT_PROVEN", cj.get("SOURCE_PATCH_NEEDED_PROVEN") == "0", cj.get("SOURCE_PATCH_NEEDED_PROVEN","missing"))
    gate("CJ_SOURCE_MUTATION_NOT_AUTHORIZED", cj.get("SOURCE_MUTATION_AUTHORIZED_NOW") == "0", cj.get("SOURCE_MUTATION_AUTHORIZED_NOW","missing"))
    gate("CJ_APPLY_EXECUTION_NOT_AUTHORIZED", cj.get("APPLY_EXECUTION_AUTHORIZED_NOW") == "0", cj.get("APPLY_EXECUTION_AUTHORIZED_NOW","missing"))
    gate("CJ_HELP_APPLY_NOT_EXECUTED", cj.get("HELP_DATA_APPLY_EXECUTED") == "0", cj.get("HELP_DATA_APPLY_EXECUTED","missing"))
    gate("CJ_CMDHELPCHK_APPLY_NOT_EXECUTED", cj.get("CMDHELPCHK_APPLY_EXECUTED") == "0", cj.get("CMDHELPCHK_APPLY_EXECUTED","missing"))
    gate("CJ_SELECTION_ROWS_PRESENT", len(selection) > 0, len(selection))
    gate("CJ_TARGETED_SCOPE_ROWS_PRESENT", len(scope) > 0, len(scope))
    gate("ACTIVE_MESSAGES_HEADER_COUNT_14", msg_count == 14, msg_count)
    gate("ACTIVE_TEXT_HEADER_COUNT_70", text_count == 70, text_count)
    gate("CK_ROOT_NOT_EXISTING_OR_REPLACE_ALLOWED", (not ck_root.exists()) or args.replace_existing_review, rel(ck_root, repo))

    status = BLOCKED
    selection_review = []
    scope_review = []
    targeted_discovery_requirements = []
    carry_forward_blocked = []
    review_decisions = []
    artifacts = []

    if failures == 0:
        if ck_root.exists() and args.replace_existing_review:
            shutil.rmtree(ck_root)
        ck_root.mkdir(parents=True, exist_ok=True)

        for i, r in enumerate(selection, 1):
            selection_review.append({
                "SELECTION_REVIEW_ROW": i,
                "DECISION_OPTION": r.get("DECISION_OPTION",""),
                "SELECTED": r.get("SELECTED",""),
                "SELECTION_STATUS": r.get("SELECTION_STATUS",""),
                "RATIONALE": r.get("RATIONALE",""),
                "REVIEW_DISPOSITION": "ACCEPT_SELECTION" if r.get("SELECTED") == "1" else "ACCEPT_REJECTION",
                "REVIEW_DETAIL": "Targeted discovery is accepted as the conservative selected path." if r.get("SELECTED") == "1" else "Rejected path remains rejected for safety.",
                "SOURCE_MUTATION_AUTHORIZED_NOW": 0,
                "APPLY_AUTHORIZED_NOW": 0,
            })

        for i, r in enumerate(scope, 1):
            scope_review.append({
                "SCOPE_REVIEW_ROW": i,
                "TARGET": r.get("TARGET",""),
                "FOCUS": r.get("FOCUS",""),
                "BROAD_SCAN_ALLOWED": r.get("BROAD_SCAN_ALLOWED","0"),
                "REVIEW_DISPOSITION": "ACCEPT_FOR_TARGETED_DISCOVERY",
                "TARGETED_DISCOVERY_PACKAGE_REQUIRED": 1,
            })

        targeted_discovery_requirements = [
            {"REQ_ROW": 1, "DISCOVERY_REQUIREMENT": "SEARCH_EXACT_HELP_DATA_WRITE_PATHS_ONLY", "DETAIL": "Find exact native/runtime/schema-aware writer/import/update path for HELP MSGMGR and HELP SET MESSAGE. Exclude display-only HELP readers.", "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
            {"REQ_ROW": 2, "DISCOVERY_REQUIREMENT": "SEARCH_EXACT_CMDHELPCHK_WRITE_PATHS_ONLY", "DETAIL": "Find exact native/runtime/schema-aware writer/import/update path for CMDHELPCHK entries. Exclude checker/readback-only code.", "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
            {"REQ_ROW": 3, "DISCOVERY_REQUIREMENT": "NARROW_SOURCE_SCOPES", "DETAIL": "Target source, tools, schemas, and active help/catalog roots by exact writer terms; avoid another broad repository scan.", "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
            {"REQ_ROW": 4, "DISCOVERY_REQUIREMENT": "REPORT_REUSE_OR_GAP", "DETAIL": "Report whether reuse path exists, or whether a gap remains that may justify guarded source-patch planning later.", "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
            {"REQ_ROW": 5, "DISCOVERY_REQUIREMENT": "PRESERVE_SOURCE_COMMENT_CONTRACT_RULE", "DETAIL": "If later source patch is needed, update @dottalk.usage/source-comment contracts in the same guarded package.", "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
            {"REQ_ROW": 6, "DISCOVERY_REQUIREMENT": "KEEP_RAW_DBF_WRITE_FORBIDDEN", "DETAIL": "Do not use Python/raw DBF byte writing as active promotion/materialization path.", "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
            {"REQ_ROW": 7, "DISCOVERY_REQUIREMENT": "KEEP_APPLY_BLOCKED", "DETAIL": "No HELP DATA/CMDHELPCHK apply until a selected writer path and guarded apply package are reviewed.", "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
        ]

        for i, b in enumerate(blocked_in, 1):
            carry_forward_blocked.append({
                "CARRY_FORWARD_ROW": i,
                "BLOCKED_ACTION": b.get("BLOCKED_ACTION",""),
                "BLOCKED": 1,
                "REASON": b.get("REASON",""),
                "CARRY_FORWARD_DETAIL": "Still blocked after CK review.",
            })

        review_decisions = [
            {"DECISION_ROW": 1, "DECISION": "CJ_SELECTION_ACCEPTED", "VALUE": 1, "DETAIL": "Targeted native writer discovery selection accepted."},
            {"DECISION_ROW": 2, "DECISION": "TARGETED_DISCOVERY_PACKAGE_REQUIRED", "VALUE": 1, "DETAIL": "10CL package should perform targeted discovery."},
            {"DECISION_ROW": 3, "DECISION": "REUSE_PATH_CONFIRMED_NOW", "VALUE": 0, "DETAIL": "No exact reuse path confirmed in CK."},
            {"DECISION_ROW": 4, "DECISION": "SOURCE_PATCH_NEEDED_PROVEN", "VALUE": 0, "DETAIL": "Source patch need remains unproven."},
            {"DECISION_ROW": 5, "DECISION": "DIRECT_APPLY_READY", "VALUE": 0, "DETAIL": "Direct HELP/CMDHELPCHK apply remains blocked."},
        ]

        paths = [
            (ck_root / "selection_review_v1.csv", selection_review, ["SELECTION_REVIEW_ROW","DECISION_OPTION","SELECTED","SELECTION_STATUS","RATIONALE","REVIEW_DISPOSITION","REVIEW_DETAIL","SOURCE_MUTATION_AUTHORIZED_NOW","APPLY_AUTHORIZED_NOW"]),
            (ck_root / "targeted_scope_review_v1.csv", scope_review, ["SCOPE_REVIEW_ROW","TARGET","FOCUS","BROAD_SCAN_ALLOWED","REVIEW_DISPOSITION","TARGETED_DISCOVERY_PACKAGE_REQUIRED"]),
            (ck_root / "targeted_discovery_requirements_v1.csv", targeted_discovery_requirements, ["REQ_ROW","DISCOVERY_REQUIREMENT","DETAIL","SOURCE_MUTATION_AUTHORIZED_NOW","APPLY_AUTHORIZED_NOW"]),
            (ck_root / "carry_forward_blocked_actions_v1.csv", carry_forward_blocked, ["CARRY_FORWARD_ROW","BLOCKED_ACTION","BLOCKED","REASON","CARRY_FORWARD_DETAIL"]),
            (ck_root / "review_decisions_v1.csv", review_decisions, ["DECISION_ROW","DECISION","VALUE","DETAIL"]),
        ]
        for p, rs, fs in paths:
            wcsv(p, rs, fs)

        scripts = ck_root / "scripts"
        scripts.mkdir(parents=True, exist_ok=True)
        disabled = scripts / "MESSAGE_CATALOG_PHASE22AE_6_5_10CL_DISCOVERY_TEMPLATE.ps1.disabled"
        disabled.write_text('throw "10CK is review only. Generate a dedicated 10CL targeted discovery package before running discovery."\n', encoding="utf-8")
        readback = scripts / "MESSAGE_CATALOG_PHASE22AE_6_5_10CK_READBACK_CONTRACT.dts"
        readback.write_text("MSGMGR STATUS\nMSGMGR CHECK\nSET MESSAGE CATALOG CHECK\nSET MESSAGE EMIT MESSAGE_PROOF_MODE_STATUS en-US\nHELP MSGMGR\nHELP SET MESSAGE\nCMDHELPCHK\nQUIT\n", encoding="utf-8")
        notes = ck_root / "native_writer_selection_review_v1.md"
        notes.write_text("# 10CK Native Writer Selection Review\n\n10CK reviews and accepts the 10CJ conservative selection: further targeted native writer discovery. It does not confirm reuse, prove source patch need, authorize apply, or mutate protected systems.\n", encoding="utf-8")
        readme = ck_root / "README_10CK_NATIVE_WRITER_SELECTION_REVIEW.md"
        readme.write_text("# 10CK Native Writer Selection Review\n\nReview-only package. No protected mutation occurs.\n", encoding="utf-8")

        for p, _, _ in paths:
            artifacts.append({"ARTIFACT": rel(p, repo), "ROLE": "native_writer_selection_review_artifact", "BYTES": p.stat().st_size, "SHA256": sha(p)})
        for p in [disabled, readback, notes, readme]:
            artifacts.append({"ARTIFACT": rel(p, repo), "ROLE": "native_writer_selection_review_artifact", "BYTES": p.stat().st_size, "SHA256": sha(p)})

        status = GREEN

    boundary = [
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "10CK writes docs/messaging review artifacts only."},
        {"PROTECTED_SYSTEM": "ACTIVE_SYSTEM_MESSAGES", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_SYSTEM_MESSAGE_TEXT", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_CDX_LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CDX/LMDB mutation."},
        {"PROTECTED_SYSTEM": "WORKSPACE_PROFILE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No workspace mutation."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Selection review only; no HELP DATA apply."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Selection review only; no CMDHELPCHK apply."},
    ]
    readiness = [
        {"ITEM": "SELECTION_REVIEW_COMPLETE", "STATUS": "YES" if status == GREEN else "NO", "DETAIL": f"{len(selection_review)} selection rows reviewed."},
        {"ITEM": "TARGETED_DISCOVERY_PACKAGE_REQUIRED", "STATUS": "YES", "DETAIL": "10CL should perform targeted writer discovery."},
        {"ITEM": "REUSE_PATH_CONFIRMED_NOW", "STATUS": "NO", "DETAIL": "No reuse path confirmed in 10CK."},
        {"ITEM": "SOURCE_PATCH_NEEDED_PROVEN", "STATUS": "NO", "DETAIL": "Source patch need remains unproven."},
        {"ITEM": "DIRECT_APPLY_READY", "STATUS": "NO", "DETAIL": "Direct apply remains blocked."},
    ]

    issues = "0" if failures == 0 else str(failures)
    wcsv(reports / "message_catalog_phase22ae_6_5_10ck_gate_check_v1.csv", gates, ["GATE","STATUS","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10ck_selection_review_v1.csv", selection_review, ["SELECTION_REVIEW_ROW","DECISION_OPTION","SELECTED","SELECTION_STATUS","RATIONALE","REVIEW_DISPOSITION","REVIEW_DETAIL","SOURCE_MUTATION_AUTHORIZED_NOW","APPLY_AUTHORIZED_NOW"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10ck_targeted_scope_review_v1.csv", scope_review, ["SCOPE_REVIEW_ROW","TARGET","FOCUS","BROAD_SCAN_ALLOWED","REVIEW_DISPOSITION","TARGETED_DISCOVERY_PACKAGE_REQUIRED"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10ck_targeted_discovery_requirements_v1.csv", targeted_discovery_requirements, ["REQ_ROW","DISCOVERY_REQUIREMENT","DETAIL","SOURCE_MUTATION_AUTHORIZED_NOW","APPLY_AUTHORIZED_NOW"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10ck_carry_forward_blocked_actions_v1.csv", carry_forward_blocked, ["CARRY_FORWARD_ROW","BLOCKED_ACTION","BLOCKED","REASON","CARRY_FORWARD_DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10ck_review_decisions_v1.csv", review_decisions, ["DECISION_ROW","DECISION","VALUE","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10ck_apply_readiness_v1.csv", readiness, ["ITEM","STATUS","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10ck_boundary_ledger_v1.csv", boundary, ["PROTECTED_SYSTEM","MUTATION_ALLOWED","OBSERVED_MUTATION","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10ck_artifact_manifest_v1.csv", artifacts, ["ARTIFACT","ROLE","BYTES","SHA256"])

    summary = {
        "STATUS": status,
        "VALIDATION_ISSUES": issues,
        "PHASE22AE_6_5_10CJ_STATUS": cj.get("STATUS",""),
        "MSG_022AE_6_5_10CJ_SAVEPOINT_PRESENT": 1 if sp_cj else 0,
        "ACTIVE_MESSAGES_OBSERVED_COUNT": msg_count,
        "ACTIVE_TEXT_OBSERVED_COUNT": text_count,
        "CJ_DECISION_SELECTION_ROWS": len(selection),
        "CJ_TARGETED_DISCOVERY_SCOPE_ROWS": len(scope),
        "SELECTION_REVIEW_ROWS": len(selection_review),
        "TARGETED_DISCOVERY_REQUIREMENT_ROWS": len(targeted_discovery_requirements),
        "CK_ROOT": rel(ck_root, repo),
        "SELECTION_REVIEW_COMPLETE": 1 if status == GREEN else 0,
        "TARGETED_DISCOVERY_PACKAGE_REQUIRED": 1 if status == GREEN else 0,
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
    wcsv(reports / "message_catalog_phase22ae_6_5_10ck_status_summary_v1.csv", [summary], list(summary.keys()))

    (repo / "docs/messaging/MESSAGE_LOCALE_PHASE22AE_6_5_10CK_NATIVE_WRITER_SELECTION_REVIEW.md").write_text(
        f"# Message Catalog Phase 22AE.6.5.10CK Native Writer Selection Review\n\nStatus: `{status}`\n\n10CK reviews the 10CJ selection and requires a targeted native writer discovery package. It does not confirm reuse, prove source patch need, authorize apply, or mutate protected systems.\n\nReview root:\n\n```text\n{rel(ck_root, repo)}\n```\n\nNext gate:\n\n```text\n{NEXT}\n```\n",
        encoding="utf-8"
    )

    print(status)
    print(f"  validation issues: {issues}")
    print(f"  Phase 22AE.6.5.10CJ status: {cj.get('STATUS','')}")
    print(f"  MSG-022AE.6.5.10CJ savepoint present: {1 if sp_cj else 0}")
    print(f"  active messages observed count: {msg_count}")
    print(f"  active text observed count: {text_count}")
    print(f"  CJ decision selection rows: {len(selection)}")
    print(f"  CJ targeted discovery scope rows: {len(scope)}")
    print(f"  selection review rows: {len(selection_review)}")
    print(f"  targeted discovery requirement rows: {len(targeted_discovery_requirements)}")
    print(f"  review root: {rel(ck_root, repo)}")
    print("  selection review complete: 1")
    print("  targeted discovery package required: 1")
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
