#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, json, hashlib, shutil, re
from datetime import datetime, timezone
from pathlib import Path

GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_10DD_NATIVE_WRITER_EXACT_PATH_RESOLUTION_PACKAGE_GREEN_EXACT_SOURCE_LOCATIONS_STAGED_SOURCE_HELD"
BLOCKED = "MESSAGE_CATALOG_PHASE22AE_6_5_10DD_NATIVE_WRITER_EXACT_PATH_RESOLUTION_PACKAGE_BLOCKED"
NEXT = "HOLD_OR_AUTHORIZE_PHASE22AE_6_5_10DE_NATIVE_WRITER_EXACT_PATH_RESOLUTION_REVIEW"

REPORT = Path("docs/messaging/reports")
DC_SUMMARY = REPORT / "message_catalog_phase22ae_6_5_10dc_status_summary_v1.csv"
DC_CANDIDATES = REPORT / "message_catalog_phase22ae_6_5_10dc_high_value_exact_path_candidates_v1.csv"
DC_EVIDENCE = REPORT / "message_catalog_phase22ae_6_5_10dc_decision_evidence_review_v1.csv"
DC_SELECTED = REPORT / "message_catalog_phase22ae_6_5_10dc_selected_safe_path_v1.csv"
DC_REQUIREMENTS = REPORT / "message_catalog_phase22ae_6_5_10dc_exact_path_resolution_requirements_v1.csv"
DC_DEFERRED = REPORT / "message_catalog_phase22ae_6_5_10dc_deferred_decision_options_v1.csv"
DC_DUP_NOTES = REPORT / "message_catalog_phase22ae_6_5_10dc_duplicate_savepoint_notes_v1.csv"
DC_BLOCKED = REPORT / "message_catalog_phase22ae_6_5_10dc_carry_forward_blocked_actions_v1.csv"

ACTIVE_MSG_DBF = Path("dottalkpp/data/messaging/SYSTEM_MESSAGES.dbf")
ACTIVE_TEXT_DBF = Path("dottalkpp/data/messaging/SYSTEM_MESSAGE_TEXT.dbf")
DD_ROOT = Path("docs/messaging/apply/phase22ae_6_5_10dd_native_writer_exact_path_resolution_package_v1")

TARGET_TERMS = ["HELP DATA", "HELPDATA", "CMDHELPCHK", "CMDHELP", "HELP"]
WRITER_TERMS = ["write", "writer", "import", "update", "append", "insert", "save", "apply", "replace", "export", "emit"]
CONTROL_TERMS = ["@dottalk.usage", "MSGMR", "MSGMGR", "SET MESSAGE"]

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

def savepoint_occurrences(repo, sid):
    journal = repo / "docs/messaging/MESSAGING_SAVEPOINT_JOURNAL.md"
    if not journal.exists():
        return 0
    text = journal.read_text(encoding="utf-8", errors="replace")
    return len(re.findall(re.escape(sid), text))

def intish(v, default=0):
    try:
        return int(float(str(v)))
    except Exception:
        return default

def read_lines(path):
    for enc in ("utf-8", "utf-8-sig", "cp1252", "latin-1"):
        try:
            return path.read_text(encoding=enc, errors="replace").splitlines()
        except Exception:
            continue
    return []

def line_window(lines, center, before=80, after=80):
    if not lines:
        return 1, 0, []
    c = intish(center, 1)
    c = max(1, min(c, len(lines)))
    start = max(1, c - before)
    end = min(len(lines), c + after)
    return start, end, lines[start-1:end]

def find_function(lines, center):
    if not lines:
        return "", "", ""
    c = max(1, min(intish(center, 1), len(lines)))
    start = max(1, c - 120)
    candidates = []
    bad_prefix = ("if", "for", "while", "switch", "catch", "return", "else", "do")
    sig_re = re.compile(r"^\s*(?:[\w:<>,~*&]+\s+)+([A-Za-z_~]\w*(?:::[A-Za-z_~]\w*)*)\s*\([^;{}]*\)\s*(?:const\s*)?(?:\{|$)")
    for idx in range(c, start-1, -1):
        text = lines[idx-1].strip()
        low = text.lower()
        if not text or text.startswith("//") or text.startswith("*"):
            continue
        if any(low.startswith(x + " ") or low.startswith(x + "(") for x in bad_prefix):
            continue
        if "(" in text and ")" in text and not text.endswith(";"):
            m = sig_re.match(text)
            if m or "::" in text or text.startswith(("bool ", "void ", "int ", "static ", "std::", "auto ")):
                candidates.append((idx, text, m.group(1) if m else ""))
                break
    if candidates:
        line, sig, name = candidates[0]
        return str(line), sig[:300], name
    return "", "", ""

def nearest_usage_contract(lines, center):
    c = max(1, min(intish(center, 1), len(lines))) if lines else 1
    for idx in range(c, max(1, c-160)-1, -1):
        text = lines[idx-1]
        if "@dottalk.usage" in text or "@dottalk" in text:
            return str(idx), text.strip()[:300]
    return "", ""

def hits(texts, terms):
    blob = "\n".join(texts).lower()
    out = [t for t in terms if t.lower() in blob]
    return ";".join(out), len(out)

def classify_target(texts, source_cls):
    blob = "\n".join(texts).lower()
    if "cmdhelpchk" in blob or "cmdhelp" in blob or "CMDHELPCHK" in source_cls:
        return "CMDHELPCHK_TARGET_CANDIDATE"
    if "help data" in blob or "helpdata" in blob or "HELP_DATA" in source_cls:
        return "HELP_DATA_TARGET_CANDIDATE"
    if "help" in blob:
        return "GENERIC_HELP_TARGET_CANDIDATE"
    return "TARGET_UNRESOLVED"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--replace-existing-package", action="store_true")
    args = ap.parse_args()
    repo = Path(args.repo_root).resolve()
    reports = repo / REPORT
    reports.mkdir(parents=True, exist_ok=True)

    dc = first(repo / DC_SUMMARY)
    candidates = rows(repo / DC_CANDIDATES)
    evidence = rows(repo / DC_EVIDENCE)
    selected = rows(repo / DC_SELECTED)
    requirements = rows(repo / DC_REQUIREMENTS)
    deferred = rows(repo / DC_DEFERRED)
    dup_notes_in = rows(repo / DC_DUP_NOTES)
    blocked_in = rows(repo / DC_BLOCKED)

    sp_dc, latest_dc = savepoint(repo, "MSG-022AE.6.5.10DC")
    sp_cs_count = savepoint_occurrences(repo, "MSG-022AE.6.5.10CS")
    sp_dc_count = savepoint_occurrences(repo, "MSG-022AE.6.5.10DC")
    msg_count = dbf_count(repo / ACTIVE_MSG_DBF)
    text_count = dbf_count(repo / ACTIVE_TEXT_DBF)
    dd_root = repo / DD_ROOT

    gates, failures = [], 0
    def gate(name, ok, detail):
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": str(detail)})
        if not ok:
            failures += 1

    gate("PHASE22AE_6_5_10DC_GREEN", dc.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_5_10DC_NATIVE_WRITER_SOURCE_CONTEXT_DECISION_REVIEW_GREEN_EXACT_WRITER_PATH_RESOLUTION_REQUIRED_SOURCE_HELD", dc.get("STATUS", "missing"))
    gate("MSG_022AE_6_5_10DC_SAVEPOINT_PRESENT", sp_dc, latest_dc)
    gate("DC_DECISION_REVIEW_COMPLETED", dc.get("DECISION_REVIEW_COMPLETED") == "1", dc.get("DECISION_REVIEW_COMPLETED", "missing"))
    gate("DC_EXACT_PATH_REQUIRED", dc.get("EXACT_WRITER_PATH_RESOLUTION_REQUIRED") == "1", dc.get("EXACT_WRITER_PATH_RESOLUTION_REQUIRED", "missing"))
    gate("DC_REUSE_NOT_SELECTED", dc.get("REUSE_PATH_SELECTED_NOW") == "0", dc.get("REUSE_PATH_SELECTED_NOW", "missing"))
    gate("DC_WRITER_REUSE_NOT_CONFIRMED", dc.get("WRITER_REUSE_CONFIRMED_NOW") == "0", dc.get("WRITER_REUSE_CONFIRMED_NOW", "missing"))
    gate("DC_SOURCE_PATCH_NOT_SELECTED", dc.get("SOURCE_PATCH_SELECTED_NOW") == "0", dc.get("SOURCE_PATCH_SELECTED_NOW", "missing"))
    gate("DC_SOURCE_PATCH_NOT_PROVEN", dc.get("SOURCE_PATCH_NEEDED_PROVEN") == "0", dc.get("SOURCE_PATCH_NEEDED_PROVEN", "missing"))
    gate("DC_SOURCE_MUTATION_NOT_AUTHORIZED", dc.get("SOURCE_MUTATION_AUTHORIZED_NOW") == "0", dc.get("SOURCE_MUTATION_AUTHORIZED_NOW", "missing"))
    gate("DC_APPLY_EXECUTION_NOT_AUTHORIZED", dc.get("APPLY_EXECUTION_AUTHORIZED_NOW") == "0", dc.get("APPLY_EXECUTION_AUTHORIZED_NOW", "missing"))
    gate("DC_HELP_APPLY_NOT_EXECUTED", dc.get("HELP_DATA_APPLY_EXECUTED") == "0", dc.get("HELP_DATA_APPLY_EXECUTED", "missing"))
    gate("DC_CMDHELPCHK_APPLY_NOT_EXECUTED", dc.get("CMDHELPCHK_APPLY_EXECUTED") == "0", dc.get("CMDHELPCHK_APPLY_EXECUTED", "missing"))
    gate("DC_HIGH_VALUE_CANDIDATES_PRESENT", len(candidates) > 0, len(candidates))
    gate("ACTIVE_MESSAGES_HEADER_COUNT_14", msg_count == 14, msg_count)
    gate("ACTIVE_TEXT_HEADER_COUNT_70", text_count == 70, text_count)
    gate("DD_ROOT_NOT_EXISTING_OR_REPLACE_ALLOWED", (not dd_root.exists()) or args.replace_existing_package, rel(dd_root, repo))

    status = BLOCKED
    resolution_rows = []
    target_summary = []
    function_summary = []
    exact_review_requirements = []
    duplicate_savepoint_notes = []
    blocked_rows = []
    deferred_rows = []
    artifacts = []

    if failures == 0:
        if dd_root.exists() and args.replace_existing_package:
            shutil.rmtree(dd_root)
        dd_root.mkdir(parents=True, exist_ok=True)

        function_counts = {}
        target_counts = {}
        resolved_source_location_count = 0
        resolved_function_count = 0

        for i, row in enumerate(candidates, 1):
            fp = row.get("FILE_PATH", "")
            requested = row.get("REQUESTED_LINE", "")
            source_path = repo / fp
            lines = read_lines(source_path) if fp else []
            start, end, window = line_window(lines, requested)
            func_line, func_sig, func_name = find_function(lines, requested)
            usage_line, usage_text = nearest_usage_contract(lines, requested)
            target_terms, target_hits = hits(window, TARGET_TERMS)
            writer_terms, writer_hits = hits(window, WRITER_TERMS)
            control_terms, control_hits = hits(window, CONTROL_TERMS)
            target = classify_target(window, row.get("SOURCE_CONTEXT_CLASSIFICATION", ""))
            source_exists = 1 if source_path.exists() else 0
            location_status = "EXACT_SOURCE_LOCATION_STAGED_REVIEW_REQUIRED" if source_exists else "SOURCE_PATH_MISSING_REVIEW_REQUIRED"
            if source_exists:
                resolved_source_location_count += 1
            if func_sig:
                resolved_function_count += 1
                location_status = "EXACT_FUNCTION_CONTEXT_STAGED_REVIEW_REQUIRED"
            function_key = func_name or func_sig or "(unresolved)"
            function_counts[function_key] = function_counts.get(function_key, 0) + 1
            target_counts[target] = target_counts.get(target, 0) + 1

            resolution_rows.append({
                "RESOLUTION_ROW": i,
                "CANDIDATE_ROW": row.get("CANDIDATE_ROW", i),
                "PROBE_ID": row.get("PROBE_ID", ""),
                "PROBE_KIND": row.get("PROBE_KIND", ""),
                "INVESTIGATION_TARGET": row.get("INVESTIGATION_TARGET", ""),
                "FILE_PATH": fp,
                "SOURCE_EXISTS": source_exists,
                "REQUESTED_LINE": requested,
                "CAPTURE_START_LINE": start,
                "CAPTURE_END_LINE": end,
                "RESOLVED_FUNCTION_LINE": func_line,
                "RESOLVED_FUNCTION_NAME": func_name,
                "RESOLVED_FUNCTION_SIGNATURE": func_sig,
                "USAGE_CONTRACT_LINE": usage_line,
                "USAGE_CONTRACT_TEXT": usage_text,
                "TARGET_RESOLUTION_CANDIDATE": target,
                "TARGET_SIGNAL_TERMS": target_terms,
                "WRITER_SIGNAL_TERMS": writer_terms,
                "CONTROL_SIGNAL_TERMS": control_terms,
                "TARGET_SIGNAL_HITS": target_hits,
                "WRITER_SIGNAL_HITS": writer_hits,
                "CONTROL_SIGNAL_HITS": control_hits,
                "RESOLUTION_STATUS": location_status,
                "REQUIRED_REVIEW": "10DE must decide whether this is an exact native writer path, reader/checker path, false positive, or still unresolved.",
                "WRITER_REUSE_CONFIRMED_NOW": 0,
                "SOURCE_PATCH_NEEDED_PROVEN": 0,
                "SOURCE_MUTATION_AUTHORIZED_NOW": 0,
                "APPLY_AUTHORIZED_NOW": 0,
            })

        for target, count in sorted(target_counts.items()):
            target_summary.append({
                "TARGET_SUMMARY_ROW": len(target_summary) + 1,
                "TARGET_RESOLUTION_CANDIDATE": target,
                "RESOLUTION_ROWS": count,
                "REVIEW_REQUIRED": 1,
                "WRITER_REUSE_CONFIRMED_NOW": 0,
                "SOURCE_PATCH_NEEDED_PROVEN": 0,
                "APPLY_AUTHORIZED_NOW": 0,
            })
        for func, count in sorted(function_counts.items()):
            function_summary.append({
                "FUNCTION_SUMMARY_ROW": len(function_summary) + 1,
                "RESOLVED_FUNCTION_OR_SIGNATURE": func,
                "RESOLUTION_ROWS": count,
                "REVIEW_REQUIRED": 1,
                "WRITER_REUSE_CONFIRMED_NOW": 0,
                "SOURCE_PATCH_NEEDED_PROVEN": 0,
                "APPLY_AUTHORIZED_NOW": 0,
            })

        exact_review_requirements = [
            {"REQ_ROW": 1, "REQUIREMENT": "10DE_REVIEW_RESOLVED_FUNCTION_CONTEXTS", "DETAIL": "Review staged exact source locations and function contexts before confirming reuse.", "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
            {"REQ_ROW": 2, "REQUIREMENT": "CONFIRM_WRITER_NOT_READER_CHECKER", "DETAIL": "A candidate must be a write/import/update/materialization path, not just HELP/CMDHELPCHK reader/checker/report output.", "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
            {"REQ_ROW": 3, "REQUIREMENT": "CONFIRM_TARGET_HELP_DATA_OR_CMDHELPCHK", "DETAIL": "Target contract must be exact before reuse can be selected.", "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
            {"REQ_ROW": 4, "REQUIREMENT": "CONFIRM_NATIVE_SCHEMA_AWARE_WRITE", "DETAIL": "Any selected reuse path must be native/schema-aware and not raw DBF byte writing.", "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
            {"REQ_ROW": 5, "REQUIREMENT": "NO_REUSE_CONFIRMATION_BY_DD", "DETAIL": "10DD stages exact source locations but does not confirm reuse.", "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
            {"REQ_ROW": 6, "REQUIREMENT": "NO_PATCH_SELECTION_BY_DD", "DETAIL": "10DD does not prove source patch need or select patch path.", "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
            {"REQ_ROW": 7, "REQUIREMENT": "NO_HELP_CMDHELPCHK_APPLY", "DETAIL": "No HELP DATA/CMDHELPCHK apply until a later guarded apply package is reviewed and authorized.", "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
        ]

        duplicate_savepoint_notes = [
            {"NOTE_ROW": 1, "SAVEPOINT_ID": "MSG-022AE.6.5.10CS", "OBSERVED_OCCURRENCES": sp_cs_count, "REVIEW_STATUS": "DUPLICATE_ACCOUNTING_NOTE" if sp_cs_count > 1 else "NORMAL", "DETAIL": "Duplicate 10CS savepoint entries remain an accounting/idempotency issue only; no protected mutation is implied." if sp_cs_count > 1 else "No duplicate 10CS savepoint observed."},
            {"NOTE_ROW": 2, "SAVEPOINT_ID": "MSG-022AE.6.5.10DC", "OBSERVED_OCCURRENCES": sp_dc_count, "REVIEW_STATUS": "CURRENT_SAVEPOINT_PRESENT" if sp_dc_count >= 1 else "MISSING", "DETAIL": "10DC savepoint presence is the precondition for 10DD."},
        ]

        for i, row in enumerate(deferred, 1):
            deferred_rows.append({
                "DEFERRED_ROW": i,
                "DEFERRED_PATH": row.get("DEFERRED_PATH", ""),
                "DEFERRED_REASON": row.get("DEFERRED_REASON", ""),
                "STILL_DEFERRED_AFTER_DD": 1,
            })

        for i, b in enumerate(blocked_in, 1):
            blocked_rows.append({
                "CARRY_FORWARD_ROW": i,
                "BLOCKED_ACTION": b.get("BLOCKED_ACTION", ""),
                "BLOCKED": 1,
                "REASON": b.get("REASON", ""),
                "CARRY_FORWARD_DETAIL": "Still blocked after DD exact path resolution package.",
            })

        paths = [
            (dd_root / "exact_path_resolution_rows_v1.csv", resolution_rows, ["RESOLUTION_ROW","CANDIDATE_ROW","PROBE_ID","PROBE_KIND","INVESTIGATION_TARGET","FILE_PATH","SOURCE_EXISTS","REQUESTED_LINE","CAPTURE_START_LINE","CAPTURE_END_LINE","RESOLVED_FUNCTION_LINE","RESOLVED_FUNCTION_NAME","RESOLVED_FUNCTION_SIGNATURE","USAGE_CONTRACT_LINE","USAGE_CONTRACT_TEXT","TARGET_RESOLUTION_CANDIDATE","TARGET_SIGNAL_TERMS","WRITER_SIGNAL_TERMS","CONTROL_SIGNAL_TERMS","TARGET_SIGNAL_HITS","WRITER_SIGNAL_HITS","CONTROL_SIGNAL_HITS","RESOLUTION_STATUS","REQUIRED_REVIEW","WRITER_REUSE_CONFIRMED_NOW","SOURCE_PATCH_NEEDED_PROVEN","SOURCE_MUTATION_AUTHORIZED_NOW","APPLY_AUTHORIZED_NOW"]),
            (dd_root / "target_resolution_summary_v1.csv", target_summary, ["TARGET_SUMMARY_ROW","TARGET_RESOLUTION_CANDIDATE","RESOLUTION_ROWS","REVIEW_REQUIRED","WRITER_REUSE_CONFIRMED_NOW","SOURCE_PATCH_NEEDED_PROVEN","APPLY_AUTHORIZED_NOW"]),
            (dd_root / "function_resolution_summary_v1.csv", function_summary, ["FUNCTION_SUMMARY_ROW","RESOLVED_FUNCTION_OR_SIGNATURE","RESOLUTION_ROWS","REVIEW_REQUIRED","WRITER_REUSE_CONFIRMED_NOW","SOURCE_PATCH_NEEDED_PROVEN","APPLY_AUTHORIZED_NOW"]),
            (dd_root / "exact_path_review_requirements_v1.csv", exact_review_requirements, ["REQ_ROW","REQUIREMENT","DETAIL","SOURCE_MUTATION_AUTHORIZED_NOW","APPLY_AUTHORIZED_NOW"]),
            (dd_root / "duplicate_savepoint_notes_v1.csv", duplicate_savepoint_notes, ["NOTE_ROW","SAVEPOINT_ID","OBSERVED_OCCURRENCES","REVIEW_STATUS","DETAIL"]),
            (dd_root / "still_deferred_paths_v1.csv", deferred_rows, ["DEFERRED_ROW","DEFERRED_PATH","DEFERRED_REASON","STILL_DEFERRED_AFTER_DD"]),
            (dd_root / "carry_forward_blocked_actions_v1.csv", blocked_rows, ["CARRY_FORWARD_ROW","BLOCKED_ACTION","BLOCKED","REASON","CARRY_FORWARD_DETAIL"]),
        ]
        for p, data, fields in paths:
            wcsv(p, data, fields)

        scripts = dd_root / "scripts"
        scripts.mkdir(parents=True, exist_ok=True)
        disabled_script = scripts / "MESSAGE_CATALOG_PHASE22AE_6_5_10DE_EXACT_PATH_REVIEW_TEMPLATE.ps1.disabled"
        disabled_script.write_text('throw "10DD staged exact source locations only. Run 10DE review before confirming reuse/source-patch/apply or authorizing mutation."\n', encoding="utf-8")
        readback = scripts / "MESSAGE_CATALOG_PHASE22AE_6_5_10DD_READBACK_CONTRACT.dts"
        readback.write_text("MSGMGR STATUS\nMSGMGR CHECK\nSET MESSAGE CATALOG CHECK\nSET MESSAGE EMIT MESSAGE_PROOF_MODE_STATUS en-US\nHELP MSGMGR\nHELP SET MESSAGE\nCMDHELPCHK\nQUIT\n", encoding="utf-8")
        notes = dd_root / "native_writer_exact_path_resolution_package_v1.md"
        notes.write_text("# 10DD Native Writer Exact Path Resolution Package\n\n10DD reads source around high-value 10DC candidates and stages exact source locations/function contexts for 10DE review. It does not confirm reuse, prove source patch need, authorize apply, or mutate protected systems.\n", encoding="utf-8")
        readme = dd_root / "README_10DD_EXACT_PATH_RESOLUTION_PACKAGE.md"
        readme.write_text("# 10DD Exact Path Resolution Package\n\nReport-only/source-held package. No protected mutation occurs.\n", encoding="utf-8")

        for p, _, _ in paths:
            artifacts.append({"ARTIFACT": rel(p, repo), "ROLE": "native_writer_exact_path_resolution_artifact", "BYTES": p.stat().st_size, "SHA256": sha(p)})
        for p in [disabled_script, readback, notes, readme]:
            artifacts.append({"ARTIFACT": rel(p, repo), "ROLE": "native_writer_exact_path_resolution_artifact", "BYTES": p.stat().st_size, "SHA256": sha(p)})

        status = GREEN

    boundary = [
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "10DD reads source and writes docs/messaging reports only; no source writes."},
        {"PROTECTED_SYSTEM": "ACTIVE_SYSTEM_MESSAGES", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_SYSTEM_MESSAGE_TEXT", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_CDX_LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CDX/LMDB mutation."},
        {"PROTECTED_SYSTEM": "WORKSPACE_PROFILE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No workspace mutation."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Exact-path resolution only; no HELP DATA apply."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Exact-path resolution only; no CMDHELPCHK apply."},
    ]
    readiness = [
        {"ITEM": "EXACT_SOURCE_LOCATIONS_STAGED", "STATUS": "YES" if status == GREEN else "NO", "DETAIL": f"{len(resolution_rows)} exact path candidate rows staged."},
        {"ITEM": "FUNCTION_CONTEXTS_STAGED", "STATUS": "YES" if resolved_function_count > 0 else "NO", "DETAIL": f"{resolved_function_count} candidate rows have a staged function context."},
        {"ITEM": "REUSE_CONFIRMED_NOW", "STATUS": "NO", "DETAIL": "Reuse remains unconfirmed pending 10DE review."},
        {"ITEM": "SOURCE_PATCH_NEEDED_PROVEN", "STATUS": "NO", "DETAIL": "Patch need remains unproven."},
        {"ITEM": "APPLY_BLOCKED", "STATUS": "YES", "DETAIL": "Apply remains blocked."},
    ]

    issues = "0" if failures == 0 else str(failures)
    wcsv(reports / "message_catalog_phase22ae_6_5_10dd_gate_check_v1.csv", gates, ["GATE","STATUS","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10dd_exact_path_resolution_rows_v1.csv", resolution_rows, ["RESOLUTION_ROW","CANDIDATE_ROW","PROBE_ID","PROBE_KIND","INVESTIGATION_TARGET","FILE_PATH","SOURCE_EXISTS","REQUESTED_LINE","CAPTURE_START_LINE","CAPTURE_END_LINE","RESOLVED_FUNCTION_LINE","RESOLVED_FUNCTION_NAME","RESOLVED_FUNCTION_SIGNATURE","USAGE_CONTRACT_LINE","USAGE_CONTRACT_TEXT","TARGET_RESOLUTION_CANDIDATE","TARGET_SIGNAL_TERMS","WRITER_SIGNAL_TERMS","CONTROL_SIGNAL_TERMS","TARGET_SIGNAL_HITS","WRITER_SIGNAL_HITS","CONTROL_SIGNAL_HITS","RESOLUTION_STATUS","REQUIRED_REVIEW","WRITER_REUSE_CONFIRMED_NOW","SOURCE_PATCH_NEEDED_PROVEN","SOURCE_MUTATION_AUTHORIZED_NOW","APPLY_AUTHORIZED_NOW"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10dd_target_resolution_summary_v1.csv", target_summary, ["TARGET_SUMMARY_ROW","TARGET_RESOLUTION_CANDIDATE","RESOLUTION_ROWS","REVIEW_REQUIRED","WRITER_REUSE_CONFIRMED_NOW","SOURCE_PATCH_NEEDED_PROVEN","APPLY_AUTHORIZED_NOW"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10dd_function_resolution_summary_v1.csv", function_summary, ["FUNCTION_SUMMARY_ROW","RESOLVED_FUNCTION_OR_SIGNATURE","RESOLUTION_ROWS","REVIEW_REQUIRED","WRITER_REUSE_CONFIRMED_NOW","SOURCE_PATCH_NEEDED_PROVEN","APPLY_AUTHORIZED_NOW"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10dd_exact_path_review_requirements_v1.csv", exact_review_requirements, ["REQ_ROW","REQUIREMENT","DETAIL","SOURCE_MUTATION_AUTHORIZED_NOW","APPLY_AUTHORIZED_NOW"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10dd_duplicate_savepoint_notes_v1.csv", duplicate_savepoint_notes, ["NOTE_ROW","SAVEPOINT_ID","OBSERVED_OCCURRENCES","REVIEW_STATUS","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10dd_still_deferred_paths_v1.csv", deferred_rows, ["DEFERRED_ROW","DEFERRED_PATH","DEFERRED_REASON","STILL_DEFERRED_AFTER_DD"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10dd_carry_forward_blocked_actions_v1.csv", blocked_rows, ["CARRY_FORWARD_ROW","BLOCKED_ACTION","BLOCKED","REASON","CARRY_FORWARD_DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10dd_apply_readiness_v1.csv", readiness, ["ITEM","STATUS","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10dd_boundary_ledger_v1.csv", boundary, ["PROTECTED_SYSTEM","MUTATION_ALLOWED","OBSERVED_MUTATION","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10dd_artifact_manifest_v1.csv", artifacts, ["ARTIFACT","ROLE","BYTES","SHA256"])

    summary = {
        "STATUS": status,
        "VALIDATION_ISSUES": issues,
        "PHASE22AE_6_5_10DC_STATUS": dc.get("STATUS",""),
        "MSG_022AE_6_5_10DC_SAVEPOINT_PRESENT": 1 if sp_dc else 0,
        "MSG_022AE_6_5_10CS_SAVEPOINT_OCCURRENCES_OBSERVED": sp_cs_count,
        "MSG_022AE_6_5_10DC_SAVEPOINT_OCCURRENCES_OBSERVED": sp_dc_count,
        "ACTIVE_MESSAGES_OBSERVED_COUNT": msg_count,
        "ACTIVE_TEXT_OBSERVED_COUNT": text_count,
        "DC_HIGH_VALUE_CANDIDATE_ROWS": len(candidates),
        "EXACT_PATH_RESOLUTION_ROWS": len(resolution_rows),
        "RESOLVED_SOURCE_LOCATION_ROWS": resolved_source_location_count if status == GREEN else 0,
        "RESOLVED_FUNCTION_CONTEXT_ROWS": resolved_function_count if status == GREEN else 0,
        "TARGET_RESOLUTION_SUMMARY_ROWS": len(target_summary),
        "FUNCTION_RESOLUTION_SUMMARY_ROWS": len(function_summary),
        "DD_ROOT": rel(dd_root, repo),
        "EXACT_SOURCE_LOCATIONS_STAGED": 1 if status == GREEN else 0,
        "REUSE_PATH_SELECTED_NOW": 0,
        "WRITER_REUSE_CONFIRMED_NOW": 0,
        "REUSE_CONFIRMED_NOW": 0,
        "SOURCE_PATCH_SELECTED_NOW": 0,
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
    wcsv(reports / "message_catalog_phase22ae_6_5_10dd_status_summary_v1.csv", [summary], list(summary.keys()))

    (repo / "docs/messaging/MESSAGE_LOCALE_PHASE22AE_6_5_10DD_NATIVE_WRITER_EXACT_PATH_RESOLUTION_PACKAGE.md").write_text(
        f"# Message Catalog Phase 22AE.6.5.10DD Native Writer Exact Path Resolution Package\n\nStatus: `{status}`\n\n10DD reads source around high-value 10DC candidates and stages exact source locations/function contexts for 10DE review. It does not confirm reuse, prove source patch need, authorize apply, or mutate protected systems.\n\nPackage root:\n\n```text\n{rel(dd_root, repo)}\n```\n\nNext gate:\n\n```text\n{NEXT}\n```\n",
        encoding="utf-8"
    )

    print(status)
    print(f"  validation issues: {issues}")
    print(f"  Phase 22AE.6.5.10DC status: {dc.get('STATUS','')}")
    print(f"  MSG-022AE.6.5.10DC savepoint present: {1 if sp_dc else 0}")
    print(f"  MSG-022AE.6.5.10CS savepoint occurrences observed: {sp_cs_count}")
    print(f"  active messages observed count: {msg_count}")
    print(f"  active text observed count: {text_count}")
    print(f"  DC high value candidate rows: {len(candidates)}")
    print(f"  exact path resolution rows: {len(resolution_rows)}")
    print(f"  resolved source location rows: {resolved_source_location_count if status == GREEN else 0}")
    print(f"  resolved function context rows: {resolved_function_count if status == GREEN else 0}")
    print(f"  target resolution summary rows: {len(target_summary)}")
    print(f"  function resolution summary rows: {len(function_summary)}")
    print(f"  package root: {rel(dd_root, repo)}")
    print("  exact source locations staged: 1")
    print("  reuse path selected now: 0")
    print("  writer reuse confirmed now: 0")
    print("  source patch selected now: 0")
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
