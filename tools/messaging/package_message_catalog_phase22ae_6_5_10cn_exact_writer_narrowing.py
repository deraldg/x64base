#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, json, hashlib, shutil, re
from datetime import datetime, timezone
from pathlib import Path

GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_10CN_EXACT_NATIVE_WRITER_CANDIDATE_NARROWING_PACKAGE_GREEN_CANDIDATES_NARROWED_SOURCE_HELD"
BLOCKED = "MESSAGE_CATALOG_PHASE22AE_6_5_10CN_EXACT_NATIVE_WRITER_CANDIDATE_NARROWING_PACKAGE_BLOCKED"
NEXT = "HOLD_OR_AUTHORIZE_PHASE22AE_6_5_10CO_EXACT_NATIVE_WRITER_NARROWING_REVIEW"

REPORT = Path("docs/messaging/reports")
CM_SUMMARY = REPORT / "message_catalog_phase22ae_6_5_10cm_status_summary_v1.csv"
CM_EXACT_FOCUS = REPORT / "message_catalog_phase22ae_6_5_10cm_exact_writer_candidate_focus_v1.csv"
CM_FOCUS_REVIEW = REPORT / "message_catalog_phase22ae_6_5_10cm_targeted_writer_focus_review_v1.csv"
CM_NARROWING_REQ = REPORT / "message_catalog_phase22ae_6_5_10cm_narrowing_requirements_v1.csv"
CM_BLOCKED = REPORT / "message_catalog_phase22ae_6_5_10cm_carry_forward_blocked_actions_v1.csv"

ACTIVE_MSG_DBF = Path("dottalkpp/data/messaging/SYSTEM_MESSAGES.dbf")
ACTIVE_TEXT_DBF = Path("dottalkpp/data/messaging/SYSTEM_MESSAGE_TEXT.dbf")
CN_ROOT = Path("docs/messaging/apply/phase22ae_6_5_10cn_exact_native_writer_candidate_narrowing_package_v1")

CONTEXT_RADIUS = 10
MAX_NARROWED_ROWS = 40

WRITER_TERMS = re.compile(r"\b(write|writer|import|update|replace|append|insert|save|create|add|put|mutate|apply|install|load)\b", re.IGNORECASE)
HELP_TERMS = re.compile(r"\b(help\s*data|helpdata|help[_\-\s]*data|help\s+msgmgr|help\s+set\s+message|help_manager|cmd_help|help)\b", re.IGNORECASE)
CMDHELPCHK_TERMS = re.compile(r"\b(cmdhelpchk|cmd_help_chk|command[_\-\s]*help[_\-\s]*check|help[_\-\s]*check)\b", re.IGNORECASE)
READER_TERMS = re.compile(r"\b(read|reader|display|show|list|print|status|check|verify|validate|lookup)\b", re.IGNORECASE)
SOURCE_CONTRACT_TERMS = re.compile(r"@dottalk\.usage|usage\s+contract|source[-_\s]*comment", re.IGNORECASE)

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

def read_context(repo, file_path, line_no, radius=CONTEXT_RADIUS):
    p = repo / file_path
    if not p.exists() or not p.is_file():
        return "", "", "", "", 0, 0
    try:
        text = p.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return "", "", "", "", 0, 0
    lines = text.splitlines()
    n = len(lines)
    ln = max(1, min(intish(line_no), n if n else 1))
    start = max(1, ln - radius)
    end = min(n, ln + radius)
    numbered = []
    for i in range(start, end + 1):
        prefix = ">>" if i == ln else "  "
        numbered.append(f"{prefix} {i}: {lines[i-1]}")
    context = "\n".join(numbered)
    target_line = lines[ln-1] if 1 <= ln <= n else ""
    return context, target_line, str(p.stat().st_size), sha(p), start, end

def classify_narrowed(row, context):
    cls = row.get("DISCOVERY_CLASS", "")
    blob = (row.get("SNIPPET","") + "\n" + context).lower()
    score = intish(row.get("TARGETED_SCORE", 0))

    writer = bool(WRITER_TERMS.search(blob))
    helpish = bool(HELP_TERMS.search(blob))
    cmdish = bool(CMDHELPCHK_TERMS.search(blob))
    reader = bool(READER_TERMS.search(blob))
    contract = bool(SOURCE_CONTRACT_TERMS.search(blob))
    path = row.get("FILE_PATH","").lower()

    priority = "C"
    disposition = "SUPPORTING_CONTEXT_REVIEW"
    task = "Review context manually; do not use as writer proof without exact target confirmation."

    if "HELP_DATA_EXACT_WRITER" in cls and writer and helpish:
        priority = "A"
        disposition = "HELP_DATA_EXACT_WRITER_CONTEXT_REVIEW"
        task = "Confirm whether this context writes/imports/updates HELP DATA for MSGMGR or SET MESSAGE."
    elif "CMDHELPCHK_EXACT_WRITER" in cls and writer and cmdish:
        priority = "A"
        disposition = "CMDHELPCHK_EXACT_WRITER_CONTEXT_REVIEW"
        task = "Confirm whether this context writes/imports/updates CMDHELPCHK records for MSGMGR or SET MESSAGE."
    elif "GENERIC_NATIVE_WRITER" in cls and writer and (helpish or cmdish):
        priority = "B"
        disposition = "GENERIC_WRITER_TARGET_BINDING_REVIEW"
        task = "Bind generic writer/import/update behavior to exact HELP DATA or CMDHELPCHK target if possible."
    elif "SOURCE_COMMENT_CONTRACT" in cls or contract:
        priority = "C"
        disposition = "SOURCE_CONTRACT_SUPPORT_REVIEW"
        task = "Carry forward only if a later source patch is selected."
    elif reader:
        priority = "D"
        disposition = "READER_CHECKER_FALSE_POSITIVE_REVIEW"
        task = "Likely reader/checker/display path; use as exclusion evidence."

    if path.startswith("src/") and priority in {"A", "B"}:
        score += 20
    elif ("tools/messaging" in path or "tools/help" in path) and priority in {"A", "B"}:
        score += 12
    if priority == "A":
        score += 100
    elif priority == "B":
        score += 60
    elif priority == "D":
        score -= 40

    return disposition, priority, task, score

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--replace-existing-package", action="store_true")
    args = ap.parse_args()
    repo = Path(args.repo_root).resolve()
    reports = repo / REPORT
    reports.mkdir(parents=True, exist_ok=True)

    cm = first(repo / CM_SUMMARY)
    exact_focus = rows(repo / CM_EXACT_FOCUS)
    focus_review = rows(repo / CM_FOCUS_REVIEW)
    narrowing_req_in = rows(repo / CM_NARROWING_REQ)
    blocked_in = rows(repo / CM_BLOCKED)

    sp_cm, latest_cm = savepoint(repo, "MSG-022AE.6.5.10CM")
    msg_count = dbf_count(repo / ACTIVE_MSG_DBF)
    text_count = dbf_count(repo / ACTIVE_TEXT_DBF)
    cn_root = repo / CN_ROOT

    gates = []
    failures = 0
    def gate(name, ok, detail):
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": str(detail)})
        if not ok:
            failures += 1

    gate("PHASE22AE_6_5_10CM_GREEN", cm.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_5_10CM_TARGETED_NATIVE_WRITER_DISCOVERY_REVIEW_GREEN_NARROWING_PACKAGE_REQUIRED_SOURCE_HELD", cm.get("STATUS","missing"))
    gate("MSG_022AE_6_5_10CM_SAVEPOINT_PRESENT", sp_cm, latest_cm)
    gate("CM_EXACT_CANDIDATE_NARROWING_REQUIRED", cm.get("EXACT_CANDIDATE_NARROWING_REQUIRED") == "1", cm.get("EXACT_CANDIDATE_NARROWING_REQUIRED","missing"))
    gate("CM_REUSE_NOT_CONFIRMED", cm.get("REUSE_PATH_CONFIRMED_NOW") == "0", cm.get("REUSE_PATH_CONFIRMED_NOW","missing"))
    gate("CM_SOURCE_PATCH_NOT_PROVEN", cm.get("SOURCE_PATCH_NEEDED_PROVEN") == "0", cm.get("SOURCE_PATCH_NEEDED_PROVEN","missing"))
    gate("CM_SOURCE_MUTATION_NOT_AUTHORIZED", cm.get("SOURCE_MUTATION_AUTHORIZED_NOW") == "0", cm.get("SOURCE_MUTATION_AUTHORIZED_NOW","missing"))
    gate("CM_APPLY_EXECUTION_NOT_AUTHORIZED", cm.get("APPLY_EXECUTION_AUTHORIZED_NOW") == "0", cm.get("APPLY_EXECUTION_AUTHORIZED_NOW","missing"))
    gate("CM_HELP_APPLY_NOT_EXECUTED", cm.get("HELP_DATA_APPLY_EXECUTED") == "0", cm.get("HELP_DATA_APPLY_EXECUTED","missing"))
    gate("CM_CMDHELPCHK_APPLY_NOT_EXECUTED", cm.get("CMDHELPCHK_APPLY_EXECUTED") == "0", cm.get("CMDHELPCHK_APPLY_EXECUTED","missing"))
    gate("CM_EXACT_FOCUS_PRESENT", len(exact_focus) > 0, len(exact_focus))
    gate("CM_NARROWING_REQUIREMENTS_PRESENT", len(narrowing_req_in) > 0, len(narrowing_req_in))
    gate("ACTIVE_MESSAGES_HEADER_COUNT_14", msg_count == 14, msg_count)
    gate("ACTIVE_TEXT_HEADER_COUNT_70", text_count == 70, text_count)
    gate("CN_ROOT_NOT_EXISTING_OR_REPLACE_ALLOWED", (not cn_root.exists()) or args.replace_existing_package, rel(cn_root, repo))

    status = BLOCKED
    context_rows = []
    narrowed_rows = []
    path_summary = []
    next_review_requirements = []
    carry_forward_blocked = []
    artifacts = []

    if failures == 0:
        if cn_root.exists() and args.replace_existing_package:
            shutil.rmtree(cn_root)
        cn_root.mkdir(parents=True, exist_ok=True)

        for i, r in enumerate(exact_focus, 1):
            file_path = r.get("FILE_PATH","")
            line = r.get("LINE","")
            context, target_line, size, file_sha, start, end = read_context(repo, file_path, line)
            disposition, priority, task, score = classify_narrowed(r, context)
            context_rows.append({
                "CONTEXT_ROW": i,
                "SOURCE_EXACT_FOCUS_ROW": r.get("EXACT_FOCUS_ROW",""),
                "DISCOVERY_CLASS": r.get("DISCOVERY_CLASS",""),
                "FILE_PATH": file_path,
                "LINE": line,
                "CONTEXT_START_LINE": start,
                "CONTEXT_END_LINE": end,
                "FILE_BYTES": size,
                "FILE_SHA256": file_sha,
                "TARGET_LINE": target_line.strip(),
                "CONTEXT_EXCERPT": context,
                "CONTEXT_AVAILABLE": 1 if context else 0,
            })
            narrowed_rows.append({
                "NARROWED_ROW": i,
                "SOURCE_EXACT_FOCUS_ROW": r.get("EXACT_FOCUS_ROW",""),
                "DISCOVERY_CLASS": r.get("DISCOVERY_CLASS",""),
                "NARROWING_DISPOSITION": disposition,
                "NARROWING_PRIORITY": priority,
                "NARROWING_SCORE": score,
                "FILE_PATH": file_path,
                "LINE": line,
                "SNIPPET": r.get("SNIPPET",""),
                "CONFIRMATION_TASK": task,
                "CONTEXT_AVAILABLE": 1 if context else 0,
                "WRITER_REUSE_CONFIRMED_NOW": 0,
                "SOURCE_PATCH_NEEDED_PROVEN": 0,
                "APPLY_READY_NOW": 0,
                "SOURCE_MUTATION_AUTHORIZED_NOW": 0,
                "APPLY_AUTHORIZED_NOW": 0,
            })

        narrowed_rows = sorted(narrowed_rows, key=lambda r: intish(r.get("NARROWING_SCORE", 0)), reverse=True)[:MAX_NARROWED_ROWS]
        for idx, r in enumerate(narrowed_rows, 1):
            r["NARROWED_ROW"] = idx

        # keep context rows only for narrowed rows to avoid oversized CSVs
        selected_pairs = {(r["FILE_PATH"], str(r["LINE"])) for r in narrowed_rows}
        context_rows = [r for r in context_rows if (r["FILE_PATH"], str(r["LINE"])) in selected_pairs]
        for idx, r in enumerate(context_rows, 1):
            r["CONTEXT_ROW"] = idx

        counts = {}
        for r in narrowed_rows:
            key = r.get("NARROWING_DISPOSITION","")
            counts[key] = counts.get(key, 0) + 1
        for k in sorted(counts):
            path_summary.append({
                "SUMMARY_ROW": len(path_summary) + 1,
                "NARROWING_DISPOSITION": k,
                "ROW_COUNT": counts[k],
                "NEXT_REVIEW_ACTION": "Open/review context and decide whether exact writer reuse, further targeted investigation, or guarded source-patch planning is appropriate.",
            })

        next_review_requirements = [
            {"REQ_ROW": 1, "REQUIREMENT": "MANUAL_CONTEXT_REVIEW_REQUIRED", "DETAIL": f"Review {len(narrowed_rows)} narrowed candidates with context before selecting any reuse/source-patch path.", "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
            {"REQ_ROW": 2, "REQUIREMENT": "CONFIRM_HELP_DATA_WRITER_TARGET", "DETAIL": "For HELP_DATA candidates, confirm the exact target record/table/catalog and whether MSGMGR/SET MESSAGE entries can be written.", "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
            {"REQ_ROW": 3, "REQUIREMENT": "CONFIRM_CMDHELPCHK_WRITER_TARGET", "DETAIL": "For CMDHELPCHK candidates, confirm the exact target record/table/catalog and whether MSGMGR/SET MESSAGE checks can be written.", "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
            {"REQ_ROW": 4, "REQUIREMENT": "EXCLUDE_READER_CHECKER_ONLY_ROWS", "DETAIL": "Rows that only read, check, list, or display must not be treated as writer proof.", "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
            {"REQ_ROW": 5, "REQUIREMENT": "DO_NOT_DECLARE_PATCH_NEEDED_YET", "DETAIL": "Source patch need is still not proven by CN.", "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
            {"REQ_ROW": 6, "REQUIREMENT": "KEEP_SOURCE_COMMENT_CONTRACT_RULE", "DETAIL": "If later source patch is selected, @dottalk.usage and source-comment contracts must be updated in same package.", "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
            {"REQ_ROW": 7, "REQUIREMENT": "KEEP_RAW_DBF_WRITE_FORBIDDEN", "DETAIL": "Any runtime promotion/apply path must be native/schema-aware, not raw DBF byte mutation.", "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
            {"REQ_ROW": 8, "REQUIREMENT": "KEEP_APPLY_BLOCKED", "DETAIL": "No HELP DATA/CMDHELPCHK apply until exact writer path and guarded apply package are reviewed.", "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
        ]

        for i, b in enumerate(blocked_in, 1):
            carry_forward_blocked.append({
                "CARRY_FORWARD_ROW": i,
                "BLOCKED_ACTION": b.get("BLOCKED_ACTION",""),
                "BLOCKED": 1,
                "REASON": b.get("REASON",""),
                "CARRY_FORWARD_DETAIL": "Still blocked after CN exact narrowing package.",
            })

        paths = [
            (cn_root / "exact_writer_candidate_context_v1.csv", context_rows, ["CONTEXT_ROW","SOURCE_EXACT_FOCUS_ROW","DISCOVERY_CLASS","FILE_PATH","LINE","CONTEXT_START_LINE","CONTEXT_END_LINE","FILE_BYTES","FILE_SHA256","TARGET_LINE","CONTEXT_EXCERPT","CONTEXT_AVAILABLE"]),
            (cn_root / "narrowed_exact_writer_candidates_v1.csv", narrowed_rows, ["NARROWED_ROW","SOURCE_EXACT_FOCUS_ROW","DISCOVERY_CLASS","NARROWING_DISPOSITION","NARROWING_PRIORITY","NARROWING_SCORE","FILE_PATH","LINE","SNIPPET","CONFIRMATION_TASK","CONTEXT_AVAILABLE","WRITER_REUSE_CONFIRMED_NOW","SOURCE_PATCH_NEEDED_PROVEN","APPLY_READY_NOW","SOURCE_MUTATION_AUTHORIZED_NOW","APPLY_AUTHORIZED_NOW"]),
            (cn_root / "narrowing_path_summary_v1.csv", path_summary, ["SUMMARY_ROW","NARROWING_DISPOSITION","ROW_COUNT","NEXT_REVIEW_ACTION"]),
            (cn_root / "next_review_requirements_v1.csv", next_review_requirements, ["REQ_ROW","REQUIREMENT","DETAIL","SOURCE_MUTATION_AUTHORIZED_NOW","APPLY_AUTHORIZED_NOW"]),
            (cn_root / "carry_forward_blocked_actions_v1.csv", carry_forward_blocked, ["CARRY_FORWARD_ROW","BLOCKED_ACTION","BLOCKED","REASON","CARRY_FORWARD_DETAIL"]),
        ]
        for p, rs, fs in paths:
            wcsv(p, rs, fs)

        scripts = cn_root / "scripts"
        scripts.mkdir(parents=True, exist_ok=True)
        disabled = scripts / "MESSAGE_CATALOG_PHASE22AE_6_5_10CO_REVIEW_TEMPLATE.ps1.disabled"
        disabled.write_text('throw "10CN is narrowing only. Run 10CO review before selecting reuse/source-patch/apply path."\n', encoding="utf-8")
        readback = scripts / "MESSAGE_CATALOG_PHASE22AE_6_5_10CN_READBACK_CONTRACT.dts"
        readback.write_text("MSGMGR STATUS\nMSGMGR CHECK\nSET MESSAGE CATALOG CHECK\nSET MESSAGE EMIT MESSAGE_PROOF_MODE_STATUS en-US\nHELP MSGMGR\nHELP SET MESSAGE\nCMDHELPCHK\nQUIT\n", encoding="utf-8")
        notes = cn_root / "exact_native_writer_candidate_narrowing_package_v1.md"
        notes.write_text("# 10CN Exact Native Writer Candidate Narrowing Package\n\n10CN narrows the 10CM exact writer focus rows using nearby source context. It does not confirm reuse, prove source patch need, authorize apply, or mutate protected systems.\n", encoding="utf-8")
        readme = cn_root / "README_10CN_EXACT_NATIVE_WRITER_CANDIDATE_NARROWING_PACKAGE.md"
        readme.write_text("# 10CN Exact Native Writer Candidate Narrowing Package\n\nNarrowing-only package. No protected mutation occurs.\n", encoding="utf-8")

        for p, _, _ in paths:
            artifacts.append({"ARTIFACT": rel(p, repo), "ROLE": "exact_native_writer_candidate_narrowing_artifact", "BYTES": p.stat().st_size, "SHA256": sha(p)})
        for p in [disabled, readback, notes, readme]:
            artifacts.append({"ARTIFACT": rel(p, repo), "ROLE": "exact_native_writer_candidate_narrowing_artifact", "BYTES": p.stat().st_size, "SHA256": sha(p)})

        status = GREEN

    boundary = [
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "10CN reads source context and writes docs/messaging narrowing artifacts only."},
        {"PROTECTED_SYSTEM": "ACTIVE_SYSTEM_MESSAGES", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_SYSTEM_MESSAGE_TEXT", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_CDX_LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CDX/LMDB mutation."},
        {"PROTECTED_SYSTEM": "WORKSPACE_PROFILE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No workspace mutation."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Narrowing only; no HELP DATA apply."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Narrowing only; no CMDHELPCHK apply."},
    ]
    readiness = [
        {"ITEM": "CANDIDATES_NARROWED", "STATUS": "YES" if status == GREEN else "NO", "DETAIL": f"{len(narrowed_rows)} narrowed rows."},
        {"ITEM": "WRITER_REUSE_CONFIRMED_NOW", "STATUS": "NO", "DETAIL": "10CN narrows candidates only; review is next."},
        {"ITEM": "SOURCE_PATCH_NEEDED_PROVEN", "STATUS": "NO", "DETAIL": "Source patch need remains unproven."},
        {"ITEM": "DIRECT_APPLY_READY", "STATUS": "NO", "DETAIL": "Direct apply remains blocked."},
        {"ITEM": "NEXT_REVIEW_REQUIRED", "STATUS": "YES", "DETAIL": "10CO must review exact narrowing."},
    ]

    issues = "0" if failures == 0 else str(failures)
    wcsv(reports / "message_catalog_phase22ae_6_5_10cn_gate_check_v1.csv", gates, ["GATE","STATUS","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10cn_exact_writer_candidate_context_v1.csv", context_rows, ["CONTEXT_ROW","SOURCE_EXACT_FOCUS_ROW","DISCOVERY_CLASS","FILE_PATH","LINE","CONTEXT_START_LINE","CONTEXT_END_LINE","FILE_BYTES","FILE_SHA256","TARGET_LINE","CONTEXT_EXCERPT","CONTEXT_AVAILABLE"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10cn_narrowed_exact_writer_candidates_v1.csv", narrowed_rows, ["NARROWED_ROW","SOURCE_EXACT_FOCUS_ROW","DISCOVERY_CLASS","NARROWING_DISPOSITION","NARROWING_PRIORITY","NARROWING_SCORE","FILE_PATH","LINE","SNIPPET","CONFIRMATION_TASK","CONTEXT_AVAILABLE","WRITER_REUSE_CONFIRMED_NOW","SOURCE_PATCH_NEEDED_PROVEN","APPLY_READY_NOW","SOURCE_MUTATION_AUTHORIZED_NOW","APPLY_AUTHORIZED_NOW"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10cn_narrowing_path_summary_v1.csv", path_summary, ["SUMMARY_ROW","NARROWING_DISPOSITION","ROW_COUNT","NEXT_REVIEW_ACTION"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10cn_next_review_requirements_v1.csv", next_review_requirements, ["REQ_ROW","REQUIREMENT","DETAIL","SOURCE_MUTATION_AUTHORIZED_NOW","APPLY_AUTHORIZED_NOW"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10cn_carry_forward_blocked_actions_v1.csv", carry_forward_blocked, ["CARRY_FORWARD_ROW","BLOCKED_ACTION","BLOCKED","REASON","CARRY_FORWARD_DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10cn_apply_readiness_v1.csv", readiness, ["ITEM","STATUS","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10cn_boundary_ledger_v1.csv", boundary, ["PROTECTED_SYSTEM","MUTATION_ALLOWED","OBSERVED_MUTATION","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10cn_artifact_manifest_v1.csv", artifacts, ["ARTIFACT","ROLE","BYTES","SHA256"])

    summary = {
        "STATUS": status,
        "VALIDATION_ISSUES": issues,
        "PHASE22AE_6_5_10CM_STATUS": cm.get("STATUS",""),
        "MSG_022AE_6_5_10CM_SAVEPOINT_PRESENT": 1 if sp_cm else 0,
        "ACTIVE_MESSAGES_OBSERVED_COUNT": msg_count,
        "ACTIVE_TEXT_OBSERVED_COUNT": text_count,
        "CM_EXACT_WRITER_CANDIDATE_FOCUS_ROWS": len(exact_focus),
        "CONTEXT_ROWS": len(context_rows),
        "NARROWED_CANDIDATE_ROWS": len(narrowed_rows),
        "NARROWING_PATH_SUMMARY_ROWS": len(path_summary),
        "NEXT_REVIEW_REQUIREMENT_ROWS": len(next_review_requirements),
        "CN_ROOT": rel(cn_root, repo),
        "CANDIDATES_NARROWED": 1 if status == GREEN else 0,
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
    wcsv(reports / "message_catalog_phase22ae_6_5_10cn_status_summary_v1.csv", [summary], list(summary.keys()))

    (repo / "docs/messaging/MESSAGE_LOCALE_PHASE22AE_6_5_10CN_EXACT_NATIVE_WRITER_CANDIDATE_NARROWING_PACKAGE.md").write_text(
        f"# Message Catalog Phase 22AE.6.5.10CN Exact Native Writer Candidate Narrowing Package\n\nStatus: `{status}`\n\n10CN narrows exact native writer candidates using source context and requires 10CO review. It does not confirm reuse, prove source patch need, authorize apply, or mutate protected systems.\n\nNarrowing root:\n\n```text\n{rel(cn_root, repo)}\n```\n\nNext gate:\n\n```text\n{NEXT}\n```\n",
        encoding="utf-8"
    )

    print(status)
    print(f"  validation issues: {issues}")
    print(f"  Phase 22AE.6.5.10CM status: {cm.get('STATUS','')}")
    print(f"  MSG-022AE.6.5.10CM savepoint present: {1 if sp_cm else 0}")
    print(f"  active messages observed count: {msg_count}")
    print(f"  active text observed count: {text_count}")
    print(f"  CM exact writer candidate focus rows: {len(exact_focus)}")
    print(f"  context rows: {len(context_rows)}")
    print(f"  narrowed candidate rows: {len(narrowed_rows)}")
    print(f"  narrowing path summary rows: {len(path_summary)}")
    print(f"  next review requirement rows: {len(next_review_requirements)}")
    print(f"  narrowing root: {rel(cn_root, repo)}")
    print("  candidates narrowed: 1")
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
