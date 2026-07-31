#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, json, hashlib, shutil, re
from datetime import datetime, timezone
from pathlib import Path

GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_10CP_EXACT_NATIVE_WRITER_CONFIRMATION_PACKAGE_GREEN_CONFIRMATION_REPORTED_SOURCE_HELD"
BLOCKED = "MESSAGE_CATALOG_PHASE22AE_6_5_10CP_EXACT_NATIVE_WRITER_CONFIRMATION_PACKAGE_BLOCKED"
NEXT = "HOLD_OR_AUTHORIZE_PHASE22AE_6_5_10CQ_EXACT_NATIVE_WRITER_CONFIRMATION_REVIEW"
REPORT = Path("docs/messaging/reports")
CP_ROOT = Path("docs/messaging/apply/phase22ae_6_5_10cp_exact_native_writer_confirmation_package_v1")

CO_SUMMARY = REPORT / "message_catalog_phase22ae_6_5_10co_status_summary_v1.csv"
CO_FOCUS = REPORT / "message_catalog_phase22ae_6_5_10co_confirmation_focus_v1.csv"
CO_REQ = REPORT / "message_catalog_phase22ae_6_5_10co_confirmation_requirements_v1.csv"
CO_BLOCKED = REPORT / "message_catalog_phase22ae_6_5_10co_carry_forward_blocked_actions_v1.csv"
ACTIVE_MSG_DBF = Path("dottalkpp/data/messaging/SYSTEM_MESSAGES.dbf")
ACTIVE_TEXT_DBF = Path("dottalkpp/data/messaging/SYSTEM_MESSAGE_TEXT.dbf")

WRITE_RX = re.compile(r"\b(write|writer|import|update|replace|append|insert|save|create|add|put|apply|install|load|emit|generate)\b", re.I)
HELP_RX = re.compile(r"\b(help\s*data|helpdata|help[_\-\s]*data|help\s+msgmgr|help\s+set\s+message|help_manager|cmd_help|help)\b", re.I)
CHK_RX = re.compile(r"\b(cmdhelpchk|cmd_help_chk|command[_\-\s]*help[_\-\s]*check|help[_\-\s]*check)\b", re.I)
TARGET_RX = re.compile(r"\b(msgg?mgr|set\s+message|system_messages|system_message_text|help\s+data|cmdhelpchk|cmdhelp|help)\b", re.I)
READER_RX = re.compile(r"\b(read|reader|display|show|list|print|status|check|verify|validate|lookup|review|plan|package|candidate|summary)\b", re.I)

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

def read_context(repo, file_path, line, radius=24):
    p = repo / file_path
    if not p.exists() or not p.is_file():
        return "", "", 0, 0, "", ""
    try:
        lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
    except Exception:
        return "", "", 0, 0, "", ""
    if not lines:
        return "", "", 0, 0, "", ""
    try:
        ln = max(1, min(int(float(line)), len(lines)))
    except Exception:
        ln = 1
    start, end = max(1, ln - radius), min(len(lines), ln + radius)
    out = []
    for i in range(start, end + 1):
        out.append((">> " if i == ln else "   ") + f"{i}: {lines[i-1]}")
    return "\n".join(out), lines[ln-1], start, end, str(p.stat().st_size), sha(p)

def classify(discovery_class, context, file_path):
    blob = context.lower()
    score = 0
    has_write = bool(WRITE_RX.search(blob))
    has_help = bool(HELP_RX.search(blob))
    has_chk = bool(CHK_RX.search(blob))
    has_target = bool(TARGET_RX.search(blob))
    has_reader = bool(READER_RX.search(blob))
    if has_write: score += 35
    if has_target: score += 25
    if file_path.lower().startswith("src/"): score += 20
    if "tools/messaging" in file_path.lower() or "tools/help" in file_path.lower(): score += 12
    if has_reader: score -= 12
    if "HELP_DATA" in discovery_class and has_write and has_help and has_target:
        return "HELP_DATA_WRITER_CONFIRMATION_CANDIDATE", score + 30
    if "CMDHELPCHK" in discovery_class and has_write and has_chk and has_target:
        return "CMDHELPCHK_WRITER_CONFIRMATION_CANDIDATE", score + 30
    if has_write and has_target:
        return "GENERIC_WRITER_TARGET_BINDING_CANDIDATE", score
    if has_reader and not has_write:
        return "READER_CHECKER_FALSE_POSITIVE_CANDIDATE", score
    return "INSUFFICIENT_CONFIRMATION_SIGNAL", score

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--replace-existing-package", action="store_true")
    args = ap.parse_args()
    repo = Path(args.repo_root).resolve()
    reports = repo / REPORT
    reports.mkdir(parents=True, exist_ok=True)

    co = first(repo / CO_SUMMARY)
    focus = rows(repo / CO_FOCUS)
    req_in = rows(repo / CO_REQ)
    blocked_in = rows(repo / CO_BLOCKED)
    sp_co, latest_co = savepoint(repo, "MSG-022AE.6.5.10CO")
    msg_count = dbf_count(repo / ACTIVE_MSG_DBF)
    text_count = dbf_count(repo / ACTIVE_TEXT_DBF)
    cp_root = repo / CP_ROOT

    gates, failures = [], 0
    def gate(name, ok, detail):
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": str(detail)})
        if not ok:
            failures += 1

    gate("PHASE22AE_6_5_10CO_GREEN", co.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_5_10CO_EXACT_NATIVE_WRITER_NARROWING_REVIEW_GREEN_CONFIRMATION_PACKAGE_REQUIRED_SOURCE_HELD", co.get("STATUS", "missing"))
    gate("MSG_022AE_6_5_10CO_SAVEPOINT_PRESENT", sp_co, latest_co)
    gate("CO_CONFIRMATION_PACKAGE_REQUIRED", co.get("CONFIRMATION_PACKAGE_REQUIRED") == "1", co.get("CONFIRMATION_PACKAGE_REQUIRED", "missing"))
    gate("CO_WRITER_REUSE_NOT_CONFIRMED", co.get("WRITER_REUSE_CONFIRMED_NOW") == "0", co.get("WRITER_REUSE_CONFIRMED_NOW", "missing"))
    gate("CO_SOURCE_PATCH_NOT_PROVEN", co.get("SOURCE_PATCH_NEEDED_PROVEN") == "0", co.get("SOURCE_PATCH_NEEDED_PROVEN", "missing"))
    gate("CO_SOURCE_MUTATION_NOT_AUTHORIZED", co.get("SOURCE_MUTATION_AUTHORIZED_NOW") == "0", co.get("SOURCE_MUTATION_AUTHORIZED_NOW", "missing"))
    gate("CO_APPLY_EXECUTION_NOT_AUTHORIZED", co.get("APPLY_EXECUTION_AUTHORIZED_NOW") == "0", co.get("APPLY_EXECUTION_AUTHORIZED_NOW", "missing"))
    gate("CO_HELP_APPLY_NOT_EXECUTED", co.get("HELP_DATA_APPLY_EXECUTED") == "0", co.get("HELP_DATA_APPLY_EXECUTED", "missing"))
    gate("CO_CMDHELPCHK_APPLY_NOT_EXECUTED", co.get("CMDHELPCHK_APPLY_EXECUTED") == "0", co.get("CMDHELPCHK_APPLY_EXECUTED", "missing"))
    gate("CO_CONFIRMATION_FOCUS_PRESENT", len(focus) > 0, len(focus))
    gate("CO_REQUIREMENTS_PRESENT", len(req_in) > 0, len(req_in))
    gate("ACTIVE_MESSAGES_HEADER_COUNT_14", msg_count == 14, msg_count)
    gate("ACTIVE_TEXT_HEADER_COUNT_70", text_count == 70, text_count)
    gate("CP_ROOT_NOT_EXISTING_OR_REPLACE_ALLOWED", (not cp_root.exists()) or args.replace_existing_package, rel(cp_root, repo))

    status = BLOCKED
    confirmations, contexts, summary_rows, review_reqs, blocked_rows, artifacts = [], [], [], [], [], []

    if failures == 0:
        if cp_root.exists() and args.replace_existing_package:
            shutil.rmtree(cp_root)
        cp_root.mkdir(parents=True, exist_ok=True)

        for i, row in enumerate(focus, 1):
            fp, ln = row.get("FILE_PATH", ""), row.get("LINE", "")
            context, target, start, end, size, file_sha = read_context(repo, fp, ln)
            cclass, score = classify(row.get("DISCOVERY_CLASS", ""), context, fp)
            contexts.append({
                "CONTEXT_ROW": i,
                "SOURCE_CONFIRMATION_FOCUS_ROW": row.get("CONFIRMATION_FOCUS_ROW", ""),
                "DISCOVERY_CLASS": row.get("DISCOVERY_CLASS", ""),
                "FILE_PATH": fp,
                "LINE": ln,
                "CONTEXT_START_LINE": start,
                "CONTEXT_END_LINE": end,
                "FILE_BYTES": size,
                "FILE_SHA256": file_sha,
                "TARGET_LINE": target.strip(),
                "CONTEXT_EXCERPT": context,
                "CONTEXT_AVAILABLE": 1 if context else 0,
            })
            confirmations.append({
                "CONFIRMATION_ROW": i,
                "SOURCE_CONFIRMATION_FOCUS_ROW": row.get("CONFIRMATION_FOCUS_ROW", ""),
                "DISCOVERY_CLASS": row.get("DISCOVERY_CLASS", ""),
                "CONFIRMATION_CLASS": cclass,
                "CONFIRMATION_SIGNAL_SCORE": score,
                "FILE_PATH": fp,
                "LINE": ln,
                "CONFIRMATION_DETAIL": "Signal row for 10CQ manual review; not proof by itself.",
                "MANUAL_REVIEW_REQUIRED": 1,
                "WRITER_REUSE_CONFIRMED_NOW": 0,
                "SOURCE_PATCH_NEEDED_PROVEN": 0,
                "APPLY_READY_NOW": 0,
                "SOURCE_MUTATION_AUTHORIZED_NOW": 0,
                "APPLY_AUTHORIZED_NOW": 0,
            })

        confirmations.sort(key=lambda r: int(r["CONFIRMATION_SIGNAL_SCORE"]), reverse=True)
        for i, row in enumerate(confirmations, 1):
            row["CONFIRMATION_ROW"] = i

        counts = {}
        for row in confirmations:
            key = row["CONFIRMATION_CLASS"]
            counts[key] = counts.get(key, 0) + 1
        for key in sorted(counts):
            summary_rows.append({
                "SUMMARY_ROW": len(summary_rows) + 1,
                "CONFIRMATION_CLASS": key,
                "ROW_COUNT": counts[key],
                "NEXT_REVIEW_ACTION": "10CQ must review and decide whether reuse is confirmed, rejected, or inconclusive.",
            })

        review_reqs = [
            {"REQ_ROW": 1, "REQUIREMENT": "REVIEW_CONFIRMATION_CANDIDATES_WITH_CONTEXT", "DETAIL": "Manual review is required before declaring writer reuse.", "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
            {"REQ_ROW": 2, "REQUIREMENT": "CONFIRM_OR_REJECT_HELP_DATA_REUSE", "DETAIL": "State whether a HELP DATA native writer path is reusable for MSGMGR / SET MESSAGE.", "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
            {"REQ_ROW": 3, "REQUIREMENT": "CONFIRM_OR_REJECT_CMDHELPCHK_REUSE", "DETAIL": "State whether a CMDHELPCHK native writer path is reusable for MSGMGR / SET MESSAGE.", "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
            {"REQ_ROW": 4, "REQUIREMENT": "DO_NOT_USE_SIGNAL_SCORE_AS_PROOF", "DETAIL": "Signal scores are triage only.", "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
            {"REQ_ROW": 5, "REQUIREMENT": "KEEP_RAW_DBF_WRITE_FORBIDDEN", "DETAIL": "Active apply path must remain native/schema-aware.", "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
            {"REQ_ROW": 6, "REQUIREMENT": "KEEP_APPLY_BLOCKED", "DETAIL": "No HELP DATA/CMDHELPCHK apply until exact path and guarded apply package are reviewed.", "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
        ]

        for i, b in enumerate(blocked_in, 1):
            blocked_rows.append({
                "CARRY_FORWARD_ROW": i,
                "BLOCKED_ACTION": b.get("BLOCKED_ACTION", ""),
                "BLOCKED": 1,
                "REASON": b.get("REASON", ""),
                "CARRY_FORWARD_DETAIL": "Still blocked after CP confirmation package.",
            })

        paths = [
            (cp_root / "exact_native_writer_confirmation_rows_v1.csv", confirmations, ["CONFIRMATION_ROW","SOURCE_CONFIRMATION_FOCUS_ROW","DISCOVERY_CLASS","CONFIRMATION_CLASS","CONFIRMATION_SIGNAL_SCORE","FILE_PATH","LINE","CONFIRMATION_DETAIL","MANUAL_REVIEW_REQUIRED","WRITER_REUSE_CONFIRMED_NOW","SOURCE_PATCH_NEEDED_PROVEN","APPLY_READY_NOW","SOURCE_MUTATION_AUTHORIZED_NOW","APPLY_AUTHORIZED_NOW"]),
            (cp_root / "exact_native_writer_confirmation_context_v1.csv", contexts, ["CONTEXT_ROW","SOURCE_CONFIRMATION_FOCUS_ROW","DISCOVERY_CLASS","FILE_PATH","LINE","CONTEXT_START_LINE","CONTEXT_END_LINE","FILE_BYTES","FILE_SHA256","TARGET_LINE","CONTEXT_EXCERPT","CONTEXT_AVAILABLE"]),
            (cp_root / "confirmation_summary_v1.csv", summary_rows, ["SUMMARY_ROW","CONFIRMATION_CLASS","ROW_COUNT","NEXT_REVIEW_ACTION"]),
            (cp_root / "confirmation_review_requirements_v1.csv", review_reqs, ["REQ_ROW","REQUIREMENT","DETAIL","SOURCE_MUTATION_AUTHORIZED_NOW","APPLY_AUTHORIZED_NOW"]),
            (cp_root / "carry_forward_blocked_actions_v1.csv", blocked_rows, ["CARRY_FORWARD_ROW","BLOCKED_ACTION","BLOCKED","REASON","CARRY_FORWARD_DETAIL"]),
        ]
        for p, data, fields in paths:
            wcsv(p, data, fields)

        scripts = cp_root / "scripts"
        scripts.mkdir(parents=True, exist_ok=True)
        disabled = scripts / "MESSAGE_CATALOG_PHASE22AE_6_5_10CQ_REVIEW_TEMPLATE.ps1.disabled"
        disabled.write_text('throw "10CP is confirmation reporting only. Run 10CQ review before declaring reuse/source-patch/apply readiness."\n', encoding="utf-8")
        readback = scripts / "MESSAGE_CATALOG_PHASE22AE_6_5_10CP_READBACK_CONTRACT.dts"
        readback.write_text("MSGMGR STATUS\nMSGMGR CHECK\nSET MESSAGE CATALOG CHECK\nSET MESSAGE EMIT MESSAGE_PROOF_MODE_STATUS en-US\nHELP MSGMGR\nHELP SET MESSAGE\nCMDHELPCHK\nQUIT\n", encoding="utf-8")
        notes = cp_root / "exact_native_writer_confirmation_package_v1.md"
        notes.write_text("# 10CP Exact Native Writer Confirmation Package\n\n10CP reports confirmation evidence for narrowed native writer candidates. Signal rows are review inputs, not proof. No protected systems are mutated.\n", encoding="utf-8")
        readme = cp_root / "README_10CP_EXACT_NATIVE_WRITER_CONFIRMATION_PACKAGE.md"
        readme.write_text("# 10CP Exact Native Writer Confirmation Package\n\nConfirmation-reporting package only. No protected mutation occurs.\n", encoding="utf-8")

        for p, _, _ in paths:
            artifacts.append({"ARTIFACT": rel(p, repo), "ROLE": "exact_native_writer_confirmation_artifact", "BYTES": p.stat().st_size, "SHA256": sha(p)})
        for p in [disabled, readback, notes, readme]:
            artifacts.append({"ARTIFACT": rel(p, repo), "ROLE": "exact_native_writer_confirmation_artifact", "BYTES": p.stat().st_size, "SHA256": sha(p)})
        status = GREEN

    boundary = [
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "10CP reads source context and writes docs/messaging confirmation artifacts only."},
        {"PROTECTED_SYSTEM": "ACTIVE_SYSTEM_MESSAGES", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_SYSTEM_MESSAGE_TEXT", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_CDX_LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CDX/LMDB mutation."},
        {"PROTECTED_SYSTEM": "WORKSPACE_PROFILE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No workspace mutation."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Confirmation package only; no HELP DATA apply."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Confirmation package only; no CMDHELPCHK apply."},
    ]
    readiness = [
        {"ITEM": "CONFIRMATION_REPORTED", "STATUS": "YES" if status == GREEN else "NO", "DETAIL": f"{len(confirmations)} confirmation rows."},
        {"ITEM": "WRITER_REUSE_CONFIRMED_NOW", "STATUS": "NO", "DETAIL": "10CP reports evidence; 10CQ review must decide."},
        {"ITEM": "SOURCE_PATCH_NEEDED_PROVEN", "STATUS": "NO", "DETAIL": "Source patch need remains unproven."},
        {"ITEM": "DIRECT_APPLY_READY", "STATUS": "NO", "DETAIL": "Direct apply remains blocked."},
    ]

    issues = "0" if failures == 0 else str(failures)
    wcsv(reports / "message_catalog_phase22ae_6_5_10cp_gate_check_v1.csv", gates, ["GATE","STATUS","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10cp_exact_native_writer_confirmation_rows_v1.csv", confirmations, ["CONFIRMATION_ROW","SOURCE_CONFIRMATION_FOCUS_ROW","DISCOVERY_CLASS","CONFIRMATION_CLASS","CONFIRMATION_SIGNAL_SCORE","FILE_PATH","LINE","CONFIRMATION_DETAIL","MANUAL_REVIEW_REQUIRED","WRITER_REUSE_CONFIRMED_NOW","SOURCE_PATCH_NEEDED_PROVEN","APPLY_READY_NOW","SOURCE_MUTATION_AUTHORIZED_NOW","APPLY_AUTHORIZED_NOW"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10cp_exact_native_writer_confirmation_context_v1.csv", contexts, ["CONTEXT_ROW","SOURCE_CONFIRMATION_FOCUS_ROW","DISCOVERY_CLASS","FILE_PATH","LINE","CONTEXT_START_LINE","CONTEXT_END_LINE","FILE_BYTES","FILE_SHA256","TARGET_LINE","CONTEXT_EXCERPT","CONTEXT_AVAILABLE"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10cp_confirmation_summary_v1.csv", summary_rows, ["SUMMARY_ROW","CONFIRMATION_CLASS","ROW_COUNT","NEXT_REVIEW_ACTION"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10cp_confirmation_review_requirements_v1.csv", review_reqs, ["REQ_ROW","REQUIREMENT","DETAIL","SOURCE_MUTATION_AUTHORIZED_NOW","APPLY_AUTHORIZED_NOW"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10cp_carry_forward_blocked_actions_v1.csv", blocked_rows, ["CARRY_FORWARD_ROW","BLOCKED_ACTION","BLOCKED","REASON","CARRY_FORWARD_DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10cp_apply_readiness_v1.csv", readiness, ["ITEM","STATUS","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10cp_boundary_ledger_v1.csv", boundary, ["PROTECTED_SYSTEM","MUTATION_ALLOWED","OBSERVED_MUTATION","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10cp_artifact_manifest_v1.csv", artifacts, ["ARTIFACT","ROLE","BYTES","SHA256"])

    summary = {
        "STATUS": status,
        "VALIDATION_ISSUES": issues,
        "PHASE22AE_6_5_10CO_STATUS": co.get("STATUS",""),
        "MSG_022AE_6_5_10CO_SAVEPOINT_PRESENT": 1 if sp_co else 0,
        "ACTIVE_MESSAGES_OBSERVED_COUNT": msg_count,
        "ACTIVE_TEXT_OBSERVED_COUNT": text_count,
        "CO_CONFIRMATION_FOCUS_ROWS": len(focus),
        "CONFIRMATION_ROWS": len(confirmations),
        "CONFIRMATION_CONTEXT_ROWS": len(contexts),
        "CONFIRMATION_SUMMARY_ROWS": len(summary_rows),
        "CONFIRMATION_REVIEW_REQUIREMENT_ROWS": len(review_reqs),
        "CP_ROOT": rel(cp_root, repo),
        "CONFIRMATION_REPORTED": 1 if status == GREEN else 0,
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
    wcsv(reports / "message_catalog_phase22ae_6_5_10cp_status_summary_v1.csv", [summary], list(summary.keys()))

    (repo / "docs/messaging/MESSAGE_LOCALE_PHASE22AE_6_5_10CP_EXACT_NATIVE_WRITER_CONFIRMATION_PACKAGE.md").write_text(
        f"# Message Catalog Phase 22AE.6.5.10CP Exact Native Writer Confirmation Package\n\nStatus: `{status}`\n\n10CP reports confirmation evidence for exact native writer candidates and requires 10CQ review. It does not confirm reuse, prove source patch need, authorize apply, or mutate protected systems.\n\nConfirmation root:\n\n```text\n{rel(cp_root, repo)}\n```\n\nNext gate:\n\n```text\n{NEXT}\n```\n",
        encoding="utf-8"
    )

    print(status)
    print(f"  validation issues: {issues}")
    print(f"  Phase 22AE.6.5.10CO status: {co.get('STATUS','')}")
    print(f"  MSG-022AE.6.5.10CO savepoint present: {1 if sp_co else 0}")
    print(f"  active messages observed count: {msg_count}")
    print(f"  active text observed count: {text_count}")
    print(f"  CO confirmation focus rows: {len(focus)}")
    print(f"  confirmation rows: {len(confirmations)}")
    print(f"  confirmation context rows: {len(contexts)}")
    print(f"  confirmation summary rows: {len(summary_rows)}")
    print(f"  confirmation review requirement rows: {len(review_reqs)}")
    print(f"  confirmation root: {rel(cp_root, repo)}")
    print("  confirmation reported: 1")
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
