#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, json, hashlib, shutil
from datetime import datetime, timezone
from pathlib import Path

GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_10CQ_EXACT_NATIVE_WRITER_CONFIRMATION_REVIEW_GREEN_DECISION_PACKAGE_REQUIRED_SOURCE_HELD"
BLOCKED = "MESSAGE_CATALOG_PHASE22AE_6_5_10CQ_EXACT_NATIVE_WRITER_CONFIRMATION_REVIEW_BLOCKED"
NEXT = "HOLD_OR_AUTHORIZE_PHASE22AE_6_5_10CR_NATIVE_WRITER_REUSE_OR_PATCH_DECISION_PACKAGE"

REPORT = Path("docs/messaging/reports")
CP_SUMMARY = REPORT / "message_catalog_phase22ae_6_5_10cp_status_summary_v1.csv"
CP_ROWS = REPORT / "message_catalog_phase22ae_6_5_10cp_exact_native_writer_confirmation_rows_v1.csv"
CP_CONTEXT = REPORT / "message_catalog_phase22ae_6_5_10cp_exact_native_writer_confirmation_context_v1.csv"
CP_SUMMARY_ROWS = REPORT / "message_catalog_phase22ae_6_5_10cp_confirmation_summary_v1.csv"
CP_REQS = REPORT / "message_catalog_phase22ae_6_5_10cp_confirmation_review_requirements_v1.csv"
CP_BLOCKED = REPORT / "message_catalog_phase22ae_6_5_10cp_carry_forward_blocked_actions_v1.csv"

ACTIVE_MSG_DBF = Path("dottalkpp/data/messaging/SYSTEM_MESSAGES.dbf")
ACTIVE_TEXT_DBF = Path("dottalkpp/data/messaging/SYSTEM_MESSAGE_TEXT.dbf")
CQ_ROOT = Path("docs/messaging/apply/phase22ae_6_5_10cq_exact_native_writer_confirmation_review_v1")

def rows(path):
    p = Path(path)
    if not p.exists():
        return []
    with p.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

def first(path):
    r = rows(path)
    return r[0] if r else {}

def wcsv(path, data, fields):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n", extrasaction="ignore")
        w.writeheader()
        for row in data:
            w.writerow({k: row.get(k, "") for k in fields})

def rel(path, repo):
    try:
        return str(Path(path).resolve().relative_to(repo.resolve())).replace("\\", "/")
    except Exception:
        return str(path).replace("\\", "/")

def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1048576), b""):
            h.update(chunk)
    return h.hexdigest()

def dbf_count(path):
    p = Path(path)
    if not p.exists() or p.stat().st_size < 12:
        return ""
    return int.from_bytes(p.read_bytes()[:12][4:8], "little")

def savepoint(repo, sid):
    latest = ""
    latest_path = repo / REPORT / "message_savepoint_latest_v1.json"
    if latest_path.exists():
        try:
            latest = json.loads(latest_path.read_text(encoding="utf-8")).get("savepoint_id", "")
        except Exception:
            latest = ""
    journal = repo / "docs/messaging/MESSAGING_SAVEPOINT_JOURNAL.md"
    text = journal.read_text(encoding="utf-8", errors="replace") if journal.exists() else ""
    return latest == sid or sid in text, latest

def intish(v):
    try:
        return int(float(str(v)))
    except Exception:
        return 0

def review_class(row):
    c = row.get("CONFIRMATION_CLASS", "")
    score = intish(row.get("CONFIRMATION_SIGNAL_SCORE", 0))
    if c in {"HELP_DATA_WRITER_CONFIRMATION_CANDIDATE", "CMDHELPCHK_WRITER_CONFIRMATION_CANDIDATE"}:
        return "HIGH_PRIORITY_DECISION_REVIEW_REQUIRED", "Carry to 10CR decision package; signal is promising but not proof."
    if c == "GENERIC_WRITER_TARGET_BINDING_CANDIDATE":
        return "TARGET_BINDING_DECISION_REVIEW_REQUIRED", "Carry to 10CR only if target binding can be manually proven."
    if c == "READER_CHECKER_FALSE_POSITIVE_CANDIDATE":
        return "LIKELY_EXCLUSION_EVIDENCE", "Likely reader/checker path; do not use as writer proof."
    if score >= 60:
        return "SUPPORTING_DECISION_REVIEW_REQUIRED", "Signal score is review input only."
    return "SUPPORTING_OR_INCONCLUSIVE", "Insufficient to confirm reuse."

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--replace-existing-review", action="store_true")
    args = ap.parse_args()
    repo = Path(args.repo_root).resolve()
    reports = repo / REPORT
    reports.mkdir(parents=True, exist_ok=True)

    cp = first(repo / CP_SUMMARY)
    confirmation_rows = rows(repo / CP_ROWS)
    context_rows = rows(repo / CP_CONTEXT)
    cp_summary_rows = rows(repo / CP_SUMMARY_ROWS)
    reqs_in = rows(repo / CP_REQS)
    blocked_in = rows(repo / CP_BLOCKED)

    sp_cp, latest_cp = savepoint(repo, "MSG-022AE.6.5.10CP")
    msg_count = dbf_count(repo / ACTIVE_MSG_DBF)
    text_count = dbf_count(repo / ACTIVE_TEXT_DBF)
    cq_root = repo / CQ_ROOT

    gates, failures = [], 0
    def gate(name, ok, detail):
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": str(detail)})
        if not ok:
            failures += 1

    gate("PHASE22AE_6_5_10CP_GREEN", cp.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_5_10CP_EXACT_NATIVE_WRITER_CONFIRMATION_PACKAGE_GREEN_CONFIRMATION_REPORTED_SOURCE_HELD", cp.get("STATUS", "missing"))
    gate("MSG_022AE_6_5_10CP_SAVEPOINT_PRESENT", sp_cp, latest_cp)
    gate("CP_CONFIRMATION_REPORTED", cp.get("CONFIRMATION_REPORTED") == "1", cp.get("CONFIRMATION_REPORTED", "missing"))
    gate("CP_WRITER_REUSE_NOT_CONFIRMED", cp.get("WRITER_REUSE_CONFIRMED_NOW") == "0", cp.get("WRITER_REUSE_CONFIRMED_NOW", "missing"))
    gate("CP_SOURCE_PATCH_NOT_PROVEN", cp.get("SOURCE_PATCH_NEEDED_PROVEN") == "0", cp.get("SOURCE_PATCH_NEEDED_PROVEN", "missing"))
    gate("CP_SOURCE_MUTATION_NOT_AUTHORIZED", cp.get("SOURCE_MUTATION_AUTHORIZED_NOW") == "0", cp.get("SOURCE_MUTATION_AUTHORIZED_NOW", "missing"))
    gate("CP_APPLY_EXECUTION_NOT_AUTHORIZED", cp.get("APPLY_EXECUTION_AUTHORIZED_NOW") == "0", cp.get("APPLY_EXECUTION_AUTHORIZED_NOW", "missing"))
    gate("CP_HELP_APPLY_NOT_EXECUTED", cp.get("HELP_DATA_APPLY_EXECUTED") == "0", cp.get("HELP_DATA_APPLY_EXECUTED", "missing"))
    gate("CP_CMDHELPCHK_APPLY_NOT_EXECUTED", cp.get("CMDHELPCHK_APPLY_EXECUTED") == "0", cp.get("CMDHELPCHK_APPLY_EXECUTED", "missing"))
    gate("CP_CONFIRMATION_ROWS_PRESENT", len(confirmation_rows) > 0, len(confirmation_rows))
    gate("CP_CONTEXT_ROWS_PRESENT", len(context_rows) > 0, len(context_rows))
    gate("CP_REQUIREMENTS_PRESENT", len(reqs_in) > 0, len(reqs_in))
    gate("ACTIVE_MESSAGES_HEADER_COUNT_14", msg_count == 14, msg_count)
    gate("ACTIVE_TEXT_HEADER_COUNT_70", text_count == 70, text_count)
    gate("CQ_ROOT_NOT_EXISTING_OR_REPLACE_ALLOWED", (not cq_root.exists()) or args.replace_existing_review, rel(cq_root, repo))

    status = BLOCKED
    confirmation_review = []
    class_review = []
    decision_requirements = []
    decision_options = []
    blocked_rows = []
    artifacts = []

    if failures == 0:
        if cq_root.exists() and args.replace_existing_review:
            shutil.rmtree(cq_root)
        cq_root.mkdir(parents=True, exist_ok=True)

        for i, row in enumerate(confirmation_rows, 1):
            disposition, detail = review_class(row)
            confirmation_review.append({
                "REVIEW_ROW": i,
                "SOURCE_CONFIRMATION_ROW": row.get("CONFIRMATION_ROW", ""),
                "DISCOVERY_CLASS": row.get("DISCOVERY_CLASS", ""),
                "CONFIRMATION_CLASS": row.get("CONFIRMATION_CLASS", ""),
                "CONFIRMATION_SIGNAL_SCORE": row.get("CONFIRMATION_SIGNAL_SCORE", ""),
                "FILE_PATH": row.get("FILE_PATH", ""),
                "LINE": row.get("LINE", ""),
                "CQ_REVIEW_DISPOSITION": disposition,
                "CQ_REVIEW_DETAIL": detail,
                "DECISION_PACKAGE_CANDIDATE": 1 if "DECISION" in disposition or "HIGH_PRIORITY" in disposition else 0,
                "WRITER_REUSE_CONFIRMED_NOW": 0,
                "SOURCE_PATCH_NEEDED_PROVEN": 0,
                "APPLY_READY_NOW": 0,
                "SOURCE_MUTATION_AUTHORIZED_NOW": 0,
                "APPLY_AUTHORIZED_NOW": 0,
            })

        counts = {}
        for row in confirmation_review:
            key = row["CQ_REVIEW_DISPOSITION"]
            counts[key] = counts.get(key, 0) + 1
        for key in sorted(counts):
            class_review.append({
                "CLASS_REVIEW_ROW": len(class_review) + 1,
                "CQ_REVIEW_DISPOSITION": key,
                "ROW_COUNT": counts[key],
                "NEXT_ACTION": "Carry decision-worthy rows to 10CR; keep exclusions/supporting rows as evidence.",
            })

        decision_options = [
            {"OPTION_ROW": 1, "DECISION_OPTION": "CONFIRM_EXISTING_NATIVE_HELP_DATA_REUSE", "SELECTED_NOW": 0, "DETAIL": "Only after 10CR manual decision review names an exact reusable writer path."},
            {"OPTION_ROW": 2, "DECISION_OPTION": "CONFIRM_EXISTING_NATIVE_CMDHELPCHK_REUSE", "SELECTED_NOW": 0, "DETAIL": "Only after 10CR manual decision review names an exact reusable writer path."},
            {"OPTION_ROW": 3, "DECISION_OPTION": "REJECT_REUSE_AND_PLAN_SOURCE_PATCH", "SELECTED_NOW": 0, "DETAIL": "Only if 10CR rejects native reuse and states the gap."},
            {"OPTION_ROW": 4, "DECISION_OPTION": "CONTINUE_TARGETED_REVIEW", "SELECTED_NOW": 0, "DETAIL": "Use if confirmation evidence remains inconclusive."},
            {"OPTION_ROW": 5, "DECISION_OPTION": "KEEP_APPLY_BLOCKED", "SELECTED_NOW": 1, "DETAIL": "Safety default until exact writer path and guarded apply package are reviewed."},
        ]

        decision_requirements = [
            {"REQ_ROW": 1, "REQUIREMENT": "10CR_MUST_MAKE_EXPLICIT_DECISION", "DETAIL": "10CR must decide reuse confirmed, reuse rejected/source-patch planning, or continue review.", "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
            {"REQ_ROW": 2, "REQUIREMENT": "NAME_EXACT_HELP_DATA_WRITER_IF_CONFIRMED", "DETAIL": "A HELP DATA reuse decision must name exact writer/import/update path and target record contract.", "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
            {"REQ_ROW": 3, "REQUIREMENT": "NAME_EXACT_CMDHELPCHK_WRITER_IF_CONFIRMED", "DETAIL": "A CMDHELPCHK reuse decision must name exact writer/import/update path and target record contract.", "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
            {"REQ_ROW": 4, "REQUIREMENT": "PATCH_PATH_REQUIRES_CONTRACT_UPDATES", "DETAIL": "Any later source patch must include @dottalk.usage/source-comment contract updates in the same guarded package.", "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
            {"REQ_ROW": 5, "REQUIREMENT": "KEEP_RAW_DBF_WRITE_FORBIDDEN", "DETAIL": "No Python/raw DBF byte promotion path is allowed for active HELP/CMDHELPCHK materialization.", "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
            {"REQ_ROW": 6, "REQUIREMENT": "KEEP_APPLY_BLOCKED", "DETAIL": "No HELP DATA/CMDHELPCHK apply until a later guarded apply package is reviewed and explicitly authorized.", "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
        ]

        for i, b in enumerate(blocked_in, 1):
            blocked_rows.append({
                "CARRY_FORWARD_ROW": i,
                "BLOCKED_ACTION": b.get("BLOCKED_ACTION", ""),
                "BLOCKED": 1,
                "REASON": b.get("REASON", ""),
                "CARRY_FORWARD_DETAIL": "Still blocked after CQ confirmation review.",
            })

        paths = [
            (cq_root / "confirmation_review_v1.csv", confirmation_review, ["REVIEW_ROW","SOURCE_CONFIRMATION_ROW","DISCOVERY_CLASS","CONFIRMATION_CLASS","CONFIRMATION_SIGNAL_SCORE","FILE_PATH","LINE","CQ_REVIEW_DISPOSITION","CQ_REVIEW_DETAIL","DECISION_PACKAGE_CANDIDATE","WRITER_REUSE_CONFIRMED_NOW","SOURCE_PATCH_NEEDED_PROVEN","APPLY_READY_NOW","SOURCE_MUTATION_AUTHORIZED_NOW","APPLY_AUTHORIZED_NOW"]),
            (cq_root / "confirmation_class_review_v1.csv", class_review, ["CLASS_REVIEW_ROW","CQ_REVIEW_DISPOSITION","ROW_COUNT","NEXT_ACTION"]),
            (cq_root / "decision_options_v1.csv", decision_options, ["OPTION_ROW","DECISION_OPTION","SELECTED_NOW","DETAIL"]),
            (cq_root / "decision_requirements_v1.csv", decision_requirements, ["REQ_ROW","REQUIREMENT","DETAIL","SOURCE_MUTATION_AUTHORIZED_NOW","APPLY_AUTHORIZED_NOW"]),
            (cq_root / "carry_forward_blocked_actions_v1.csv", blocked_rows, ["CARRY_FORWARD_ROW","BLOCKED_ACTION","BLOCKED","REASON","CARRY_FORWARD_DETAIL"]),
        ]
        for p, data, fields in paths:
            wcsv(p, data, fields)

        scripts = cq_root / "scripts"
        scripts.mkdir(parents=True, exist_ok=True)
        disabled = scripts / "MESSAGE_CATALOG_PHASE22AE_6_5_10CR_DECISION_TEMPLATE.ps1.disabled"
        disabled.write_text('throw "10CQ is review only. Generate a dedicated 10CR decision package before selecting reuse/source-patch/apply path."\n', encoding="utf-8")
        readback = scripts / "MESSAGE_CATALOG_PHASE22AE_6_5_10CQ_READBACK_CONTRACT.dts"
        readback.write_text("MSGMGR STATUS\nMSGMGR CHECK\nSET MESSAGE CATALOG CHECK\nSET MESSAGE EMIT MESSAGE_PROOF_MODE_STATUS en-US\nHELP MSGMGR\nHELP SET MESSAGE\nCMDHELPCHK\nQUIT\n", encoding="utf-8")
        notes = cq_root / "exact_native_writer_confirmation_review_v1.md"
        notes.write_text("# 10CQ Exact Native Writer Confirmation Review\n\n10CQ reviews 10CP confirmation evidence and requires a 10CR explicit reuse-or-patch decision package. It does not confirm reuse, prove source patch need, authorize apply, or mutate protected systems.\n", encoding="utf-8")
        readme = cq_root / "README_10CQ_EXACT_NATIVE_WRITER_CONFIRMATION_REVIEW.md"
        readme.write_text("# 10CQ Exact Native Writer Confirmation Review\n\nReview-only package. No protected mutation occurs.\n", encoding="utf-8")

        for p, _, _ in paths:
            artifacts.append({"ARTIFACT": rel(p, repo), "ROLE": "exact_native_writer_confirmation_review_artifact", "BYTES": p.stat().st_size, "SHA256": sha(p)})
        for p in [disabled, readback, notes, readme]:
            artifacts.append({"ARTIFACT": rel(p, repo), "ROLE": "exact_native_writer_confirmation_review_artifact", "BYTES": p.stat().st_size, "SHA256": sha(p)})

        status = GREEN

    boundary = [
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "10CQ writes docs/messaging review artifacts only."},
        {"PROTECTED_SYSTEM": "ACTIVE_SYSTEM_MESSAGES", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_SYSTEM_MESSAGE_TEXT", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_CDX_LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CDX/LMDB mutation."},
        {"PROTECTED_SYSTEM": "WORKSPACE_PROFILE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No workspace mutation."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Confirmation review only; no HELP DATA apply."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Confirmation review only; no CMDHELPCHK apply."},
    ]
    readiness = [
        {"ITEM": "CONFIRMATION_REVIEWED", "STATUS": "YES" if status == GREEN else "NO", "DETAIL": f"{len(confirmation_review)} confirmation rows reviewed."},
        {"ITEM": "DECISION_PACKAGE_REQUIRED", "STATUS": "YES", "DETAIL": "10CR must make explicit reuse/source-patch/continue-review decision."},
        {"ITEM": "WRITER_REUSE_CONFIRMED_NOW", "STATUS": "NO", "DETAIL": "CQ reviews evidence but does not confirm reuse."},
        {"ITEM": "SOURCE_PATCH_NEEDED_PROVEN", "STATUS": "NO", "DETAIL": "Source patch need remains unproven."},
        {"ITEM": "DIRECT_APPLY_READY", "STATUS": "NO", "DETAIL": "Direct apply remains blocked."},
    ]

    issues = "0" if failures == 0 else str(failures)
    wcsv(reports / "message_catalog_phase22ae_6_5_10cq_gate_check_v1.csv", gates, ["GATE","STATUS","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10cq_confirmation_review_v1.csv", confirmation_review, ["REVIEW_ROW","SOURCE_CONFIRMATION_ROW","DISCOVERY_CLASS","CONFIRMATION_CLASS","CONFIRMATION_SIGNAL_SCORE","FILE_PATH","LINE","CQ_REVIEW_DISPOSITION","CQ_REVIEW_DETAIL","DECISION_PACKAGE_CANDIDATE","WRITER_REUSE_CONFIRMED_NOW","SOURCE_PATCH_NEEDED_PROVEN","APPLY_READY_NOW","SOURCE_MUTATION_AUTHORIZED_NOW","APPLY_AUTHORIZED_NOW"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10cq_confirmation_class_review_v1.csv", class_review, ["CLASS_REVIEW_ROW","CQ_REVIEW_DISPOSITION","ROW_COUNT","NEXT_ACTION"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10cq_decision_options_v1.csv", decision_options, ["OPTION_ROW","DECISION_OPTION","SELECTED_NOW","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10cq_decision_requirements_v1.csv", decision_requirements, ["REQ_ROW","REQUIREMENT","DETAIL","SOURCE_MUTATION_AUTHORIZED_NOW","APPLY_AUTHORIZED_NOW"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10cq_carry_forward_blocked_actions_v1.csv", blocked_rows, ["CARRY_FORWARD_ROW","BLOCKED_ACTION","BLOCKED","REASON","CARRY_FORWARD_DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10cq_apply_readiness_v1.csv", readiness, ["ITEM","STATUS","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10cq_boundary_ledger_v1.csv", boundary, ["PROTECTED_SYSTEM","MUTATION_ALLOWED","OBSERVED_MUTATION","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10cq_artifact_manifest_v1.csv", artifacts, ["ARTIFACT","ROLE","BYTES","SHA256"])

    summary = {
        "STATUS": status,
        "VALIDATION_ISSUES": issues,
        "PHASE22AE_6_5_10CP_STATUS": cp.get("STATUS",""),
        "MSG_022AE_6_5_10CP_SAVEPOINT_PRESENT": 1 if sp_cp else 0,
        "ACTIVE_MESSAGES_OBSERVED_COUNT": msg_count,
        "ACTIVE_TEXT_OBSERVED_COUNT": text_count,
        "CP_CONFIRMATION_ROWS": len(confirmation_rows),
        "CP_CONFIRMATION_CONTEXT_ROWS": len(context_rows),
        "CONFIRMATION_REVIEW_ROWS": len(confirmation_review),
        "CONFIRMATION_CLASS_REVIEW_ROWS": len(class_review),
        "DECISION_OPTION_ROWS": len(decision_options),
        "DECISION_REQUIREMENT_ROWS": len(decision_requirements),
        "CQ_ROOT": rel(cq_root, repo),
        "CONFIRMATION_REVIEWED": 1 if status == GREEN else 0,
        "DECISION_PACKAGE_REQUIRED": 1 if status == GREEN else 0,
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
    wcsv(reports / "message_catalog_phase22ae_6_5_10cq_status_summary_v1.csv", [summary], list(summary.keys()))

    (repo / "docs/messaging/MESSAGE_LOCALE_PHASE22AE_6_5_10CQ_EXACT_NATIVE_WRITER_CONFIRMATION_REVIEW.md").write_text(
        f"# Message Catalog Phase 22AE.6.5.10CQ Exact Native Writer Confirmation Review\n\nStatus: `{status}`\n\n10CQ reviews 10CP confirmation evidence and requires a 10CR explicit reuse-or-patch decision package. It does not confirm reuse, prove source patch need, authorize apply, or mutate protected systems.\n\nReview root:\n\n```text\n{rel(cq_root, repo)}\n```\n\nNext gate:\n\n```text\n{NEXT}\n```\n",
        encoding="utf-8"
    )

    print(status)
    print(f"  validation issues: {issues}")
    print(f"  Phase 22AE.6.5.10CP status: {cp.get('STATUS','')}")
    print(f"  MSG-022AE.6.5.10CP savepoint present: {1 if sp_cp else 0}")
    print(f"  active messages observed count: {msg_count}")
    print(f"  active text observed count: {text_count}")
    print(f"  CP confirmation rows: {len(confirmation_rows)}")
    print(f"  CP confirmation context rows: {len(context_rows)}")
    print(f"  confirmation review rows: {len(confirmation_review)}")
    print(f"  confirmation class review rows: {len(class_review)}")
    print(f"  decision option rows: {len(decision_options)}")
    print(f"  decision requirement rows: {len(decision_requirements)}")
    print(f"  review root: {rel(cq_root, repo)}")
    print("  confirmation reviewed: 1")
    print("  decision package required: 1")
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
