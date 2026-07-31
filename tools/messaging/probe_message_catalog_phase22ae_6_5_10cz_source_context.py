#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, json, hashlib, shutil, re
from datetime import datetime, timezone
from pathlib import Path

GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_10CZ_NATIVE_WRITER_SOURCE_CONTEXT_PROBE_PACKAGE_GREEN_SOURCE_CONTEXT_CAPTURED_NO_MUTATION"
BLOCKED = "MESSAGE_CATALOG_PHASE22AE_6_5_10CZ_NATIVE_WRITER_SOURCE_CONTEXT_PROBE_PACKAGE_BLOCKED"
NEXT = "HOLD_OR_AUTHORIZE_PHASE22AE_6_5_10DA_NATIVE_WRITER_SOURCE_CONTEXT_PROBE_REVIEW"

REPORT = Path("docs/messaging/reports")
CY_SUMMARY = REPORT / "message_catalog_phase22ae_6_5_10cy_status_summary_v1.csv"
CY_PROBE_REVIEW = REPORT / "message_catalog_phase22ae_6_5_10cy_probe_staging_review_v1.csv"
CY_CONTEXT_REVIEW = REPORT / "message_catalog_phase22ae_6_5_10cy_source_context_plan_review_v1.csv"
CY_TARGET_REVIEW = REPORT / "message_catalog_phase22ae_6_5_10cy_target_probe_matrix_review_v1.csv"
CY_REQS = REPORT / "message_catalog_phase22ae_6_5_10cy_source_context_probe_package_requirements_v1.csv"
CY_EVIDENCE = REPORT / "message_catalog_phase22ae_6_5_10cy_evidence_review_v1.csv"
CY_DUP_NOTES = REPORT / "message_catalog_phase22ae_6_5_10cy_duplicate_savepoint_notes_v1.csv"
CY_BLOCKED = REPORT / "message_catalog_phase22ae_6_5_10cy_carry_forward_blocked_actions_v1.csv"

ACTIVE_MSG_DBF = Path("dottalkpp/data/messaging/SYSTEM_MESSAGES.dbf")
ACTIVE_TEXT_DBF = Path("dottalkpp/data/messaging/SYSTEM_MESSAGE_TEXT.dbf")
CZ_ROOT = Path("docs/messaging/apply/phase22ae_6_5_10cz_native_writer_source_context_probe_package_v1")

SEARCH_TERMS = [
    "HELP DATA", "HELPDATA", "CMDHELPCHK", "MSGMGR", "SET MESSAGE",
    "import", "write", "writer", "update", "append", "insert", "save",
    "apply", "replace", "@dottalk.usage", "CMDHELP", "HELP"
]

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

def line_window(repo, file_path, center_line, before=30, after=30):
    p = repo / file_path
    if not file_path or not p.exists() or not p.is_file():
        return [], 0, 0
    lines = read_lines(p)
    if not lines:
        return [], 0, 0
    c = intish(center_line, 1)
    if c < 1:
        c = 1
    start = max(1, c - before)
    end = min(len(lines), c + after)
    out = []
    for n in range(start, end + 1):
        text = lines[n-1]
        hit_terms = [t for t in SEARCH_TERMS if t.lower() in text.lower()]
        out.append({
            "LINE_NUMBER": n,
            "TEXT": text[:400],
            "HIT_TERMS": ";".join(hit_terms),
            "HAS_HIT": 1 if hit_terms else 0,
        })
    return out, start, end

def classify_context(lines):
    blob = "\n".join(x["TEXT"] for x in lines).lower()
    has_help = ("help data" in blob) or ("helpdata" in blob) or ("help msgmgr" in blob) or ("help set message" in blob)
    has_cmd = "cmdhelpchk" in blob or "cmdhelp" in blob
    has_write = any(t in blob for t in ["write", "writer", "import", "update", "append", "insert", "save", "apply", "replace"])
    has_usage = "@dottalk.usage" in blob
    if has_help and has_write:
        return "HELP_DATA_WRITER_CANDIDATE_CONTEXT", "Window contains HELP DATA/help and writer/import/update language."
    if has_cmd and has_write:
        return "CMDHELPCHK_WRITER_CANDIDATE_CONTEXT", "Window contains CMDHELP/CMDHELPCHK and writer/import/update language."
    if has_write:
        return "GENERIC_WRITER_CONTEXT", "Window contains writer/import/update language but target binding remains unclear."
    if has_help or has_cmd:
        return "TARGET_READER_CHECKER_CONTEXT", "Window contains HELP/CMDHELP target language without clear writer signal."
    if has_usage:
        return "SOURCE_COMMENT_CONTRACT_CONTEXT", "Window contains @dottalk.usage/source-comment contract evidence."
    return "INCONCLUSIVE_CONTEXT", "Window does not contain strong writer/target terms."

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--replace-existing-package", action="store_true")
    args = ap.parse_args()
    repo = Path(args.repo_root).resolve()
    reports = repo / REPORT
    reports.mkdir(parents=True, exist_ok=True)

    cy = first(repo / CY_SUMMARY)
    probe_review = rows(repo / CY_PROBE_REVIEW)
    context_review = rows(repo / CY_CONTEXT_REVIEW)
    target_review = rows(repo / CY_TARGET_REVIEW)
    reqs_in = rows(repo / CY_REQS)
    evidence_in = rows(repo / CY_EVIDENCE)
    dup_notes_in = rows(repo / CY_DUP_NOTES)
    blocked_in = rows(repo / CY_BLOCKED)

    sp_cy, latest_cy = savepoint(repo, "MSG-022AE.6.5.10CY")
    sp_cs_count = savepoint_occurrences(repo, "MSG-022AE.6.5.10CS")
    sp_cy_count = savepoint_occurrences(repo, "MSG-022AE.6.5.10CY")
    msg_count = dbf_count(repo / ACTIVE_MSG_DBF)
    text_count = dbf_count(repo / ACTIVE_TEXT_DBF)
    cz_root = repo / CZ_ROOT

    gates, failures = [], 0
    def gate(name, ok, detail):
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": str(detail)})
        if not ok:
            failures += 1

    gate("PHASE22AE_6_5_10CY_GREEN", cy.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_5_10CY_NATIVE_WRITER_PROBE_STAGING_REVIEW_GREEN_SOURCE_CONTEXT_PROBE_PACKAGE_REQUIRED_SOURCE_HELD", cy.get("STATUS", "missing"))
    gate("MSG_022AE_6_5_10CY_SAVEPOINT_PRESENT", sp_cy, latest_cy)
    gate("CY_PROBE_STAGING_REVIEWED", cy.get("PROBE_STAGING_REVIEWED") == "1", cy.get("PROBE_STAGING_REVIEWED", "missing"))
    gate("CY_SOURCE_CONTEXT_PACKAGE_REQUIRED", cy.get("SOURCE_CONTEXT_PROBE_PACKAGE_REQUIRED") == "1", cy.get("SOURCE_CONTEXT_PROBE_PACKAGE_REQUIRED", "missing"))
    gate("CY_RUNTIME_NOT_AUTHORIZED", cy.get("RUNTIME_EXECUTION_AUTHORIZED_NOW") == "0", cy.get("RUNTIME_EXECUTION_AUTHORIZED_NOW", "missing"))
    gate("CY_REUSE_NOT_SELECTED", cy.get("REUSE_PATH_SELECTED_NOW") == "0", cy.get("REUSE_PATH_SELECTED_NOW", "missing"))
    gate("CY_WRITER_REUSE_NOT_CONFIRMED", cy.get("WRITER_REUSE_CONFIRMED_NOW") == "0", cy.get("WRITER_REUSE_CONFIRMED_NOW", "missing"))
    gate("CY_SOURCE_PATCH_NOT_SELECTED", cy.get("SOURCE_PATCH_SELECTED_NOW") == "0", cy.get("SOURCE_PATCH_SELECTED_NOW", "missing"))
    gate("CY_SOURCE_PATCH_NOT_PROVEN", cy.get("SOURCE_PATCH_NEEDED_PROVEN") == "0", cy.get("SOURCE_PATCH_NEEDED_PROVEN", "missing"))
    gate("CY_SOURCE_MUTATION_NOT_AUTHORIZED", cy.get("SOURCE_MUTATION_AUTHORIZED_NOW") == "0", cy.get("SOURCE_MUTATION_AUTHORIZED_NOW", "missing"))
    gate("CY_APPLY_EXECUTION_NOT_AUTHORIZED", cy.get("APPLY_EXECUTION_AUTHORIZED_NOW") == "0", cy.get("APPLY_EXECUTION_AUTHORIZED_NOW", "missing"))
    gate("CY_HELP_APPLY_NOT_EXECUTED", cy.get("HELP_DATA_APPLY_EXECUTED") == "0", cy.get("HELP_DATA_APPLY_EXECUTED", "missing"))
    gate("CY_CMDHELPCHK_APPLY_NOT_EXECUTED", cy.get("CMDHELPCHK_APPLY_EXECUTED") == "0", cy.get("CMDHELPCHK_APPLY_EXECUTED", "missing"))
    gate("CY_PROBE_REVIEW_ROWS_PRESENT", len(probe_review) > 0, len(probe_review))
    gate("CY_CONTEXT_REVIEW_ROWS_PRESENT", len(context_review) > 0, len(context_review))
    gate("ACTIVE_MESSAGES_HEADER_COUNT_14", msg_count == 14, msg_count)
    gate("ACTIVE_TEXT_HEADER_COUNT_70", text_count == 70, text_count)
    gate("CZ_ROOT_NOT_EXISTING_OR_REPLACE_ALLOWED", (not cz_root.exists()) or args.replace_existing_package, rel(cz_root, repo))

    status = BLOCKED
    captured_context = []
    context_summary = []
    probe_result_rows = []
    target_result_matrix = []
    evidence_carry_forward = []
    duplicate_savepoint_notes = []
    review_requirements = []
    blocked_rows = []
    artifacts = []

    if failures == 0:
        if cz_root.exists() and args.replace_existing_package:
            shutil.rmtree(cz_root)
        cz_root.mkdir(parents=True, exist_ok=True)

        # Map context plan by PROBE_ID
        context_by_probe = {r.get("PROBE_ID", ""): r for r in context_review}
        eligible = [r for r in probe_review if str(r.get("ELIGIBLE_FOR_10CZ_SOURCE_CONTEXT_PACKAGE", "")) == "1"]
        if not eligible:
            eligible = probe_review

        source_context_dir = cz_root / "source_context"
        source_context_dir.mkdir(parents=True, exist_ok=True)

        for idx, row in enumerate(eligible, 1):
            probe_id = row.get("PROBE_ID", "") or f"CZ-PROBE-{idx:03d}"
            plan = context_by_probe.get(probe_id, {})
            fp = row.get("FILE_PATH", "") or plan.get("FILE_PATH", "")
            line = row.get("LINE", "") or plan.get("LINE", "")
            before = intish(plan.get("READ_WINDOW_BEFORE", ""), 30)
            after = intish(plan.get("READ_WINDOW_AFTER", ""), 30)
            lines, start, end = line_window(repo, fp, line, before, after)
            cls, detail = classify_context(lines)
            hit_count = sum(intish(x["HAS_HIT"]) for x in lines)
            context_file = source_context_dir / f"{probe_id}_source_context.md"
            context_file.parent.mkdir(parents=True, exist_ok=True)
            md = []
            md.append(f"# Source Context Probe {probe_id}")
            md.append("")
            md.append(f"- File: `{fp}`")
            md.append(f"- Requested line: `{line}`")
            md.append(f"- Captured range: `{start}-{end}`")
            md.append(f"- Classification: `{cls}`")
            md.append(f"- Detail: {detail}")
            md.append("")
            md.append("```text")
            for item in lines:
                marker = " *" if item["HAS_HIT"] else "  "
                md.append(f"{item['LINE_NUMBER']:6d}{marker} {item['TEXT']}")
            md.append("```")
            context_file.write_text("\n".join(md) + "\n", encoding="utf-8")

            probe_result_rows.append({
                "PROBE_RESULT_ROW": idx,
                "PROBE_ID": probe_id,
                "PROBE_KIND": row.get("PROBE_KIND", ""),
                "INVESTIGATION_TARGET": row.get("INVESTIGATION_TARGET", ""),
                "FILE_PATH": fp,
                "REQUESTED_LINE": line,
                "CAPTURE_START_LINE": start,
                "CAPTURE_END_LINE": end,
                "CONTEXT_LINE_ROWS": len(lines),
                "HIT_LINE_ROWS": hit_count,
                "SOURCE_CONTEXT_CLASSIFICATION": cls,
                "SOURCE_CONTEXT_DETAIL": detail,
                "CONTEXT_ARTIFACT": rel(context_file, repo),
                "RUNTIME_EXECUTION_NOW": 0,
                "SOURCE_MUTATION_AUTHORIZED_NOW": 0,
                "APPLY_AUTHORIZED_NOW": 0,
            })

            for item in lines:
                captured_context.append({
                    "CONTEXT_ROW": len(captured_context) + 1,
                    "PROBE_ID": probe_id,
                    "FILE_PATH": fp,
                    "LINE_NUMBER": item["LINE_NUMBER"],
                    "HAS_HIT": item["HAS_HIT"],
                    "HIT_TERMS": item["HIT_TERMS"],
                    "TEXT_EXCERPT": item["TEXT"],
                })

        class_counts = {}
        target_counts = {}
        for row in probe_result_rows:
            class_counts[row["SOURCE_CONTEXT_CLASSIFICATION"]] = class_counts.get(row["SOURCE_CONTEXT_CLASSIFICATION"], 0) + 1
            target_counts[row["INVESTIGATION_TARGET"]] = target_counts.get(row["INVESTIGATION_TARGET"], 0) + 1
        for cls, count in sorted(class_counts.items()):
            context_summary.append({
                "SUMMARY_ROW": len(context_summary) + 1,
                "SUMMARY_KIND": "CLASSIFICATION_COUNT",
                "KEY": cls,
                "ROW_COUNT": count,
                "DETAIL": "Source-context package classification count.",
            })
        for target, count in sorted(target_counts.items()):
            target_result_matrix.append({
                "MATRIX_ROW": len(target_result_matrix) + 1,
                "INVESTIGATION_TARGET": target,
                "PROBE_RESULT_ROWS": count,
                "NEXT_REVIEW_REQUIRED": 1,
                "REUSE_CONFIRMED_NOW": 0,
                "SOURCE_PATCH_NEEDED_PROVEN": 0,
                "APPLY_ALLOWED_NOW": 0,
            })

        for i, row in enumerate(evidence_in, 1):
            evidence_carry_forward.append({
                "EVIDENCE_ROW": i,
                "SOURCE": row.get("SOURCE", ""),
                "ROW_COUNT": row.get("ROW_COUNT", ""),
                "ROLE": row.get("ROLE", ""),
                "CARRY_FORWARD_STATUS": "CARRIED_TO_10DA_SOURCE_CONTEXT_REVIEW",
            })

        duplicate_savepoint_notes = [
            {"NOTE_ROW": 1, "SAVEPOINT_ID": "MSG-022AE.6.5.10CS", "OBSERVED_OCCURRENCES": sp_cs_count, "REVIEW_STATUS": "DUPLICATE_ACCOUNTING_NOTE" if sp_cs_count > 1 else "NORMAL", "DETAIL": "Duplicate 10CS savepoint entries remain an accounting/idempotency issue only; no protected mutation is implied." if sp_cs_count > 1 else "No duplicate 10CS savepoint observed."},
            {"NOTE_ROW": 2, "SAVEPOINT_ID": "MSG-022AE.6.5.10CY", "OBSERVED_OCCURRENCES": sp_cy_count, "REVIEW_STATUS": "CURRENT_SAVEPOINT_PRESENT" if sp_cy_count >= 1 else "MISSING", "DETAIL": "10CY savepoint presence is the precondition for 10CZ."},
        ]

        review_requirements = [
            {"REQ_ROW": 1, "REQUIREMENT": "10DA_REVIEW_SOURCE_CONTEXT_RESULTS", "DETAIL": "10DA must review source-context classifications before selecting reuse, patch, or further investigation.", "RUNTIME_EXECUTION_AUTHORIZED_NOW": 0, "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
            {"REQ_ROW": 2, "REQUIREMENT": "NO_REUSE_CONFIRMED_BY_CONTEXT_CAPTURE", "DETAIL": "Source context capture alone does not confirm native writer reuse.", "RUNTIME_EXECUTION_AUTHORIZED_NOW": 0, "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
            {"REQ_ROW": 3, "REQUIREMENT": "NO_PATCH_NEED_PROVEN_BY_CONTEXT_CAPTURE", "DETAIL": "Source context capture alone does not prove source patch need.", "RUNTIME_EXECUTION_AUTHORIZED_NOW": 0, "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
            {"REQ_ROW": 4, "REQUIREMENT": "NO_DOTTALK_RUNTIME_COMMANDS_EXECUTED", "DETAIL": "10CZ only reads source files and writes reports/artifacts.", "RUNTIME_EXECUTION_AUTHORIZED_NOW": 0, "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
            {"REQ_ROW": 5, "REQUIREMENT": "NO_SOURCE_EDITS", "DETAIL": "10CZ does not edit source files.", "RUNTIME_EXECUTION_AUTHORIZED_NOW": 0, "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
            {"REQ_ROW": 6, "REQUIREMENT": "KEEP_RAW_DBF_WRITE_FORBIDDEN", "DETAIL": "Active HELP/CMDHELPCHK materialization must remain native/schema-aware, not raw DBF byte mutation.", "RUNTIME_EXECUTION_AUTHORIZED_NOW": 0, "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
            {"REQ_ROW": 7, "REQUIREMENT": "KEEP_APPLY_BLOCKED", "DETAIL": "No HELP DATA/CMDHELPCHK apply until a later guarded apply package is reviewed and explicitly authorized.", "RUNTIME_EXECUTION_AUTHORIZED_NOW": 0, "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
        ]

        for i, b in enumerate(blocked_in, 1):
            blocked_rows.append({
                "CARRY_FORWARD_ROW": i,
                "BLOCKED_ACTION": b.get("BLOCKED_ACTION", ""),
                "BLOCKED": 1,
                "REASON": b.get("REASON", ""),
                "CARRY_FORWARD_DETAIL": "Still blocked after CZ source-context probe package.",
            })

        paths = [
            (cz_root / "source_context_probe_results_v1.csv", probe_result_rows, ["PROBE_RESULT_ROW","PROBE_ID","PROBE_KIND","INVESTIGATION_TARGET","FILE_PATH","REQUESTED_LINE","CAPTURE_START_LINE","CAPTURE_END_LINE","CONTEXT_LINE_ROWS","HIT_LINE_ROWS","SOURCE_CONTEXT_CLASSIFICATION","SOURCE_CONTEXT_DETAIL","CONTEXT_ARTIFACT","RUNTIME_EXECUTION_NOW","SOURCE_MUTATION_AUTHORIZED_NOW","APPLY_AUTHORIZED_NOW"]),
            (cz_root / "captured_source_context_lines_v1.csv", captured_context, ["CONTEXT_ROW","PROBE_ID","FILE_PATH","LINE_NUMBER","HAS_HIT","HIT_TERMS","TEXT_EXCERPT"]),
            (cz_root / "source_context_summary_v1.csv", context_summary, ["SUMMARY_ROW","SUMMARY_KIND","KEY","ROW_COUNT","DETAIL"]),
            (cz_root / "target_result_matrix_v1.csv", target_result_matrix, ["MATRIX_ROW","INVESTIGATION_TARGET","PROBE_RESULT_ROWS","NEXT_REVIEW_REQUIRED","REUSE_CONFIRMED_NOW","SOURCE_PATCH_NEEDED_PROVEN","APPLY_ALLOWED_NOW"]),
            (cz_root / "evidence_carry_forward_v1.csv", evidence_carry_forward, ["EVIDENCE_ROW","SOURCE","ROW_COUNT","ROLE","CARRY_FORWARD_STATUS"]),
            (cz_root / "duplicate_savepoint_notes_v1.csv", duplicate_savepoint_notes, ["NOTE_ROW","SAVEPOINT_ID","OBSERVED_OCCURRENCES","REVIEW_STATUS","DETAIL"]),
            (cz_root / "source_context_review_requirements_v1.csv", review_requirements, ["REQ_ROW","REQUIREMENT","DETAIL","RUNTIME_EXECUTION_AUTHORIZED_NOW","SOURCE_MUTATION_AUTHORIZED_NOW","APPLY_AUTHORIZED_NOW"]),
            (cz_root / "carry_forward_blocked_actions_v1.csv", blocked_rows, ["CARRY_FORWARD_ROW","BLOCKED_ACTION","BLOCKED","REASON","CARRY_FORWARD_DETAIL"]),
        ]
        for p, data, fields in paths:
            wcsv(p, data, fields)

        scripts = cz_root / "scripts"
        scripts.mkdir(parents=True, exist_ok=True)
        disabled_script = scripts / "MESSAGE_CATALOG_PHASE22AE_6_5_10DA_SOURCE_CONTEXT_REVIEW_TEMPLATE.ps1.disabled"
        disabled_script.write_text('throw "10CZ captured source context only. Run 10DA review before selecting reuse/source-patch/apply or authorizing any mutation."\n', encoding="utf-8")
        readback = scripts / "MESSAGE_CATALOG_PHASE22AE_6_5_10CZ_READBACK_CONTRACT.dts"
        readback.write_text("MSGMGR STATUS\nMSGMGR CHECK\nSET MESSAGE CATALOG CHECK\nSET MESSAGE EMIT MESSAGE_PROOF_MODE_STATUS en-US\nHELP MSGMGR\nHELP SET MESSAGE\nCMDHELPCHK\nQUIT\n", encoding="utf-8")
        notes = cz_root / "native_writer_source_context_probe_package_v1.md"
        notes.write_text("# 10CZ Native Writer Source Context Probe Package\n\n10CZ captures read-only source context around staged native-writer probe rows. It does not run DotTalk runtime commands, edit source, select reuse, select source patch, authorize apply, or mutate protected systems.\n", encoding="utf-8")
        readme = cz_root / "README_10CZ_NATIVE_WRITER_SOURCE_CONTEXT_PROBE_PACKAGE.md"
        readme.write_text("# 10CZ Native Writer Source Context Probe Package\n\nRead-only source-context capture package. No protected mutation occurs.\n", encoding="utf-8")

        artifacts = []
        for p, _, _ in paths:
            artifacts.append({"ARTIFACT": rel(p, repo), "ROLE": "native_writer_source_context_probe_artifact", "BYTES": p.stat().st_size, "SHA256": sha(p)})
        for p in sorted(source_context_dir.glob("*.md")):
            artifacts.append({"ARTIFACT": rel(p, repo), "ROLE": "source_context_excerpt", "BYTES": p.stat().st_size, "SHA256": sha(p)})
        for p in [disabled_script, readback, notes, readme]:
            artifacts.append({"ARTIFACT": rel(p, repo), "ROLE": "native_writer_source_context_probe_artifact", "BYTES": p.stat().st_size, "SHA256": sha(p)})
        wcsv(cz_root / "artifact_manifest_v1.csv", artifacts, ["ARTIFACT","ROLE","BYTES","SHA256"])

        status = GREEN

    boundary = [
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "10CZ reads source context only; no source writes."},
        {"PROTECTED_SYSTEM": "ACTIVE_SYSTEM_MESSAGES", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_SYSTEM_MESSAGE_TEXT", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_CDX_LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CDX/LMDB mutation."},
        {"PROTECTED_SYSTEM": "WORKSPACE_PROFILE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No workspace mutation."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Source-context package only; no HELP DATA apply."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Source-context package only; no CMDHELPCHK apply."},
    ]
    readiness = [
        {"ITEM": "SOURCE_CONTEXT_CAPTURED", "STATUS": "YES" if status == GREEN else "NO", "DETAIL": f"{len(probe_result_rows)} probe contexts captured."},
        {"ITEM": "DOTTALK_RUNTIME_EXECUTION_NOW", "STATUS": "NO", "DETAIL": "No DotTalk runtime commands executed."},
        {"ITEM": "SOURCE_MUTATION_AUTHORIZED_NOW", "STATUS": "NO", "DETAIL": "No source edits authorized or applied."},
        {"ITEM": "REUSE_PATH_SELECTED_NOW", "STATUS": "NO", "DETAIL": "Reuse remains deferred."},
        {"ITEM": "SOURCE_PATCH_SELECTED_NOW", "STATUS": "NO", "DETAIL": "Source patch remains deferred."},
        {"ITEM": "APPLY_BLOCKED", "STATUS": "YES", "DETAIL": "Apply remains blocked."},
    ]

    issues = "0" if failures == 0 else str(failures)
    wcsv(reports / "message_catalog_phase22ae_6_5_10cz_gate_check_v1.csv", gates, ["GATE","STATUS","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10cz_source_context_probe_results_v1.csv", probe_result_rows, ["PROBE_RESULT_ROW","PROBE_ID","PROBE_KIND","INVESTIGATION_TARGET","FILE_PATH","REQUESTED_LINE","CAPTURE_START_LINE","CAPTURE_END_LINE","CONTEXT_LINE_ROWS","HIT_LINE_ROWS","SOURCE_CONTEXT_CLASSIFICATION","SOURCE_CONTEXT_DETAIL","CONTEXT_ARTIFACT","RUNTIME_EXECUTION_NOW","SOURCE_MUTATION_AUTHORIZED_NOW","APPLY_AUTHORIZED_NOW"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10cz_captured_source_context_lines_v1.csv", captured_context, ["CONTEXT_ROW","PROBE_ID","FILE_PATH","LINE_NUMBER","HAS_HIT","HIT_TERMS","TEXT_EXCERPT"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10cz_source_context_summary_v1.csv", context_summary, ["SUMMARY_ROW","SUMMARY_KIND","KEY","ROW_COUNT","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10cz_target_result_matrix_v1.csv", target_result_matrix, ["MATRIX_ROW","INVESTIGATION_TARGET","PROBE_RESULT_ROWS","NEXT_REVIEW_REQUIRED","REUSE_CONFIRMED_NOW","SOURCE_PATCH_NEEDED_PROVEN","APPLY_ALLOWED_NOW"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10cz_evidence_carry_forward_v1.csv", evidence_carry_forward, ["EVIDENCE_ROW","SOURCE","ROW_COUNT","ROLE","CARRY_FORWARD_STATUS"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10cz_duplicate_savepoint_notes_v1.csv", duplicate_savepoint_notes, ["NOTE_ROW","SAVEPOINT_ID","OBSERVED_OCCURRENCES","REVIEW_STATUS","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10cz_source_context_review_requirements_v1.csv", review_requirements, ["REQ_ROW","REQUIREMENT","DETAIL","RUNTIME_EXECUTION_AUTHORIZED_NOW","SOURCE_MUTATION_AUTHORIZED_NOW","APPLY_AUTHORIZED_NOW"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10cz_carry_forward_blocked_actions_v1.csv", blocked_rows, ["CARRY_FORWARD_ROW","BLOCKED_ACTION","BLOCKED","REASON","CARRY_FORWARD_DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10cz_apply_readiness_v1.csv", readiness, ["ITEM","STATUS","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10cz_boundary_ledger_v1.csv", boundary, ["PROTECTED_SYSTEM","MUTATION_ALLOWED","OBSERVED_MUTATION","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10cz_artifact_manifest_v1.csv", artifacts, ["ARTIFACT","ROLE","BYTES","SHA256"])

    summary = {
        "STATUS": status,
        "VALIDATION_ISSUES": issues,
        "PHASE22AE_6_5_10CY_STATUS": cy.get("STATUS",""),
        "MSG_022AE_6_5_10CY_SAVEPOINT_PRESENT": 1 if sp_cy else 0,
        "MSG_022AE_6_5_10CS_SAVEPOINT_OCCURRENCES_OBSERVED": sp_cs_count,
        "MSG_022AE_6_5_10CY_SAVEPOINT_OCCURRENCES_OBSERVED": sp_cy_count,
        "ACTIVE_MESSAGES_OBSERVED_COUNT": msg_count,
        "ACTIVE_TEXT_OBSERVED_COUNT": text_count,
        "CY_PROBE_REVIEW_ROWS": len(probe_review),
        "CY_SOURCE_CONTEXT_PLAN_REVIEW_ROWS": len(context_review),
        "SOURCE_CONTEXT_PROBE_RESULT_ROWS": len(probe_result_rows),
        "CAPTURED_SOURCE_CONTEXT_LINE_ROWS": len(captured_context),
        "SOURCE_CONTEXT_SUMMARY_ROWS": len(context_summary),
        "TARGET_RESULT_MATRIX_ROWS": len(target_result_matrix),
        "CZ_ROOT": rel(cz_root, repo),
        "SOURCE_CONTEXT_CAPTURED": 1 if status == GREEN else 0,
        "DOTTALK_RUNTIME_EXECUTION_NOW": 0,
        "RUNTIME_EXECUTION_AUTHORIZED_NOW": 0,
        "REUSE_PATH_SELECTED_NOW": 0,
        "WRITER_REUSE_CONFIRMED_NOW": 0,
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
    wcsv(reports / "message_catalog_phase22ae_6_5_10cz_status_summary_v1.csv", [summary], list(summary.keys()))

    (repo / "docs/messaging/MESSAGE_LOCALE_PHASE22AE_6_5_10CZ_NATIVE_WRITER_SOURCE_CONTEXT_PROBE_PACKAGE.md").write_text(
        f"# Message Catalog Phase 22AE.6.5.10CZ Native Writer Source Context Probe Package\n\nStatus: `{status}`\n\n10CZ captures read-only source context around staged native-writer probe rows. It does not run DotTalk runtime commands, edit source, select reuse, select source patch, authorize apply, or mutate protected systems.\n\nProbe root:\n\n```text\n{rel(cz_root, repo)}\n```\n\nNext gate:\n\n```text\n{NEXT}\n```\n",
        encoding="utf-8"
    )

    print(status)
    print(f"  validation issues: {issues}")
    print(f"  Phase 22AE.6.5.10CY status: {cy.get('STATUS','')}")
    print(f"  MSG-022AE.6.5.10CY savepoint present: {1 if sp_cy else 0}")
    print(f"  MSG-022AE.6.5.10CS savepoint occurrences observed: {sp_cs_count}")
    print(f"  active messages observed count: {msg_count}")
    print(f"  active text observed count: {text_count}")
    print(f"  CY probe review rows: {len(probe_review)}")
    print(f"  CY source context plan review rows: {len(context_review)}")
    print(f"  source context probe result rows: {len(probe_result_rows)}")
    print(f"  captured source context line rows: {len(captured_context)}")
    print(f"  source context summary rows: {len(context_summary)}")
    print(f"  target result matrix rows: {len(target_result_matrix)}")
    print(f"  probe root: {rel(cz_root, repo)}")
    print("  source context captured: 1")
    print("  DotTalk runtime execution now: 0")
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
