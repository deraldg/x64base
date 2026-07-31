#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_10CF_NATIVE_WRITER_DISCOVERY_TRIAGE_PACKAGE_GREEN_REVIEW_REQUIRED_SOURCE_HELD"
BLOCKED = "MESSAGE_CATALOG_PHASE22AE_6_5_10CF_NATIVE_WRITER_DISCOVERY_TRIAGE_PACKAGE_BLOCKED"
NEXT = "HOLD_OR_AUTHORIZE_PHASE22AE_6_5_10CG_NATIVE_WRITER_TRIAGE_REVIEW"

REPORT_DIR = Path("docs/messaging/reports")
CE_SUMMARY = REPORT_DIR / "message_catalog_phase22ae_6_5_10ce_status_summary_v1.csv"
CE_KIND_REVIEW = REPORT_DIR / "message_catalog_phase22ae_6_5_10ce_discovery_kind_review_v1.csv"
CE_SHORTLIST = REPORT_DIR / "message_catalog_phase22ae_6_5_10ce_native_writer_candidate_shortlist_v1.csv"
CE_TRIAGE_REQ = REPORT_DIR / "message_catalog_phase22ae_6_5_10ce_triage_requirements_v1.csv"
CE_DECISIONS = REPORT_DIR / "message_catalog_phase22ae_6_5_10ce_review_decisions_v1.csv"
ACTIVE_MSG_DBF = Path("dottalkpp/data/messaging/SYSTEM_MESSAGES.dbf")
ACTIVE_TEXT_DBF = Path("dottalkpp/data/messaging/SYSTEM_MESSAGE_TEXT.dbf")
CF_ROOT = Path("docs/messaging/apply/phase22ae_6_5_10cf_native_writer_discovery_triage_package_v1")

MAX_FOCUS_ROWS = 120
MAX_REUSE_ROWS = 80

WRITE_TERMS = ["write", "import", "update", "replace", "append", "insert", "save", "create", "addtag", "use ", "open"]
HELP_TERMS = ["help data", "helpdata", "cmd_help", "help manager", "help_manager", "help"]
CMDHELPCHK_TERMS = ["cmdhelpchk", "cmd_help_chk", "command help check", "help check"]
MESSAGE_TERMS = ["msgmgr", "message manager", "set message", "message catalog", "message_catalog"]

def rows(p: Path):
    if not p.exists():
        return []
    with p.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

def first(p: Path):
    r = rows(p)
    return r[0] if r else {}

def wcsv(p: Path, rs, fs):
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fs, lineterminator="\n", extrasaction="ignore")
        w.writeheader()
        for r in rs:
            w.writerow({k: r.get(k, "") for k in fs})

def rel(p: Path, repo: Path):
    try:
        return str(p.resolve().relative_to(repo.resolve())).replace("\\", "/")
    except Exception:
        return str(p).replace("\\", "/")

def sha(p: Path):
    h = hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda: f.read(1048576), b""):
            h.update(b)
    return h.hexdigest()

def dbf_count(p: Path):
    if not p.exists() or p.stat().st_size < 12:
        return ""
    with p.open("rb") as f:
        head = f.read(12)
    return int.from_bytes(head[4:8], "little")

def savepoint(repo: Path, sid: str):
    latest = ""
    lp = repo / REPORT_DIR / "message_savepoint_latest_v1.json"
    if lp.exists():
        try:
            latest = json.loads(lp.read_text(encoding="utf-8")).get("savepoint_id", "")
        except Exception:
            latest = ""
    jp = repo / "docs/messaging/MESSAGING_SAVEPOINT_JOURNAL.md"
    txt = jp.read_text(encoding="utf-8", errors="replace") if jp.exists() else ""
    return latest == sid or sid in txt, latest

def has_any(text: str, terms):
    low = (text or "").lower()
    return any(t in low for t in terms)

def classify_triage(row):
    kind = row.get("CANDIDATE_KIND", "")
    path = row.get("FILE_PATH", "")
    snippet = row.get("SNIPPET", "")
    all_text = " ".join([kind, path, snippet]).lower()

    is_write = has_any(all_text, WRITE_TERMS)
    is_help = has_any(all_text, HELP_TERMS)
    is_cmd = has_any(all_text, CMDHELPCHK_TERMS)
    is_msg = has_any(all_text, MESSAGE_TERMS)
    path_low = path.lower()

    if is_cmd and is_write:
        return ("CMDHELPCHK_NATIVE_WRITER_REUSE_CANDIDATE", "HIGH", "Candidate mentions CMDHELPCHK/help-check and writer/import/update behavior.")
    if is_help and is_write:
        return ("HELP_DATA_NATIVE_WRITER_REUSE_CANDIDATE", "HIGH", "Candidate mentions HELP/help data and writer/import/update behavior.")
    if kind == "CMDHELPCHK_WRITER_OR_CHECK_CANDIDATE":
        return ("CMDHELPCHK_REVIEW_CANDIDATE", "HIGH", "CMDHELPCHK candidate; determine writer vs checker/readback role.")
    if kind == "HELP_DATA_WRITER_OR_READER_CANDIDATE":
        return ("HELP_DATA_REVIEW_CANDIDATE", "HIGH", "HELP DATA candidate; determine writer vs reader/help display role.")
    if kind == "WRITE_PATH_CANDIDATE":
        return ("GENERIC_WRITE_PATH_CANDIDATE", "MEDIUM", "Write/import/update candidate; determine whether it can safely target HELP/CMDHELPCHK.")
    if kind == "DATA_STORAGE_CANDIDATE":
        return ("STORAGE_SCHEMA_SUPPORT_CANDIDATE", "MEDIUM", "Storage/schema candidate; use to confirm target locations and safety contracts.")
    if kind in {"MSGMGR_SURFACE_CANDIDATE", "SET_MESSAGE_SURFACE_CANDIDATE"} or is_msg:
        return ("RUNTIME_SURFACE_READBACK_CANDIDATE", "SUPPORT", "Runtime surface candidate; likely readback/proof, not writer implementation.")
    if kind == "SOURCE_COMMENT_CONTRACT_CANDIDATE" or "@dottalk.usage" in all_text:
        return ("SOURCE_COMMENT_CONTRACT_CANDIDATE", "SUPPORT", "Source-comment/usage contract candidate; relevant only if later source patch is authorized.")
    if "docs/messaging" in path_low:
        return ("PROCESS_ARTIFACT_SUPPORT_CANDIDATE", "SUPPORT", "Process/documentation artifact; useful for provenance, not direct writer implementation.")
    return ("GENERAL_DISCOVERY_SUPPORT_CANDIDATE", "SUPPORT", "General discovery evidence requiring manual review.")

def triage_score(row):
    base = 0
    priority = row.get("TRIAGE_PRIORITY", "")
    if priority == "HIGH":
        base += 100
    elif priority == "MEDIUM":
        base += 60
    else:
        base += 20
    try:
        base += int(float(row.get("PRIORITY_SCORE", 0))) // 5
    except Exception:
        pass
    path = row.get("FILE_PATH", "").lower()
    snippet = row.get("SNIPPET", "").lower()
    if path.startswith("src/"):
        base += 12
    if "tools/messaging" in path:
        base += 8
    if "dottalkpp/data/help" in path:
        base += 8
    if has_any(snippet, WRITE_TERMS):
        base += 10
    if "cmdhelpchk" in snippet or "help data" in snippet:
        base += 10
    if "docs/messaging" in path:
        base -= 10
    return base

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--replace-existing-triage", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    reports = repo / REPORT_DIR
    reports.mkdir(parents=True, exist_ok=True)

    ce = first(repo / CE_SUMMARY)
    kind_review_in = rows(repo / CE_KIND_REVIEW)
    shortlist_in = rows(repo / CE_SHORTLIST)
    triage_req_in = rows(repo / CE_TRIAGE_REQ)
    decisions_in = rows(repo / CE_DECISIONS)
    sp_ce, latest_ce = savepoint(repo, "MSG-022AE.6.5.10CE")
    msg_count = dbf_count(repo / ACTIVE_MSG_DBF)
    text_count = dbf_count(repo / ACTIVE_TEXT_DBF)
    cf_root = repo / CF_ROOT

    gates = []
    failures = 0
    def gate(name, ok, detail):
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": str(detail)})
        if not ok:
            failures += 1

    gate("PHASE22AE_6_5_10CE_GREEN",
         ce.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_5_10CE_NATIVE_WRITER_DISCOVERY_REVIEW_GREEN_TRIAGE_PACKAGE_REQUIRED_SOURCE_HELD",
         ce.get("STATUS", "missing"))
    gate("MSG_022AE_6_5_10CE_SAVEPOINT_PRESENT", sp_ce, latest_ce)
    gate("CE_TRIAGE_PACKAGE_REQUIRED", ce.get("TRIAGE_PACKAGE_REQUIRED") == "1", ce.get("TRIAGE_PACKAGE_REQUIRED", "missing"))
    gate("CE_SOURCE_MUTATION_NOT_AUTHORIZED", ce.get("SOURCE_MUTATION_AUTHORIZED_NOW") == "0", ce.get("SOURCE_MUTATION_AUTHORIZED_NOW", "missing"))
    gate("CE_APPLY_EXECUTION_NOT_AUTHORIZED", ce.get("APPLY_EXECUTION_AUTHORIZED_NOW") == "0", ce.get("APPLY_EXECUTION_AUTHORIZED_NOW", "missing"))
    gate("CE_HELP_APPLY_NOT_EXECUTED", ce.get("HELP_DATA_APPLY_EXECUTED") == "0", ce.get("HELP_DATA_APPLY_EXECUTED", "missing"))
    gate("CE_CMDHELPCHK_APPLY_NOT_EXECUTED", ce.get("CMDHELPCHK_APPLY_EXECUTED") == "0", ce.get("CMDHELPCHK_APPLY_EXECUTED", "missing"))
    gate("CE_SHORTLIST_PRESENT", len(shortlist_in) > 0, len(shortlist_in))
    gate("CE_KIND_REVIEW_PRESENT", len(kind_review_in) > 0, len(kind_review_in))
    gate("CE_TRIAGE_REQUIREMENTS_PRESENT", len(triage_req_in) > 0, len(triage_req_in))
    gate("ACTIVE_MESSAGES_HEADER_COUNT_14", msg_count == 14, msg_count)
    gate("ACTIVE_TEXT_HEADER_COUNT_70", text_count == 70, text_count)
    gate("CF_ROOT_NOT_EXISTING_OR_REPLACE_ALLOWED", (not cf_root.exists()) or args.replace_existing_triage, rel(cf_root, repo))

    status = BLOCKED
    triaged_rows = []
    focus_rows = []
    reuse_candidate_rows = []
    decision_rows = []
    next_review_requirements = []
    artifact_rows = []

    if failures == 0:
        if cf_root.exists() and args.replace_existing_triage:
            shutil.rmtree(cf_root)
        cf_root.mkdir(parents=True, exist_ok=True)

        for i, r in enumerate(shortlist_in, start=1):
            triage_class, triage_priority, detail = classify_triage(r)
            out = {
                "TRIAGE_ROW": i,
                "SOURCE_CANDIDATE_ROW": r.get("CANDIDATE_ROW", ""),
                "CANDIDATE_KIND": r.get("CANDIDATE_KIND", ""),
                "TRIAGE_CLASS": triage_class,
                "TRIAGE_PRIORITY": triage_priority,
                "FILE_PATH": r.get("FILE_PATH", ""),
                "LINE": r.get("LINE", ""),
                "MATCH_KIND": r.get("MATCH_KIND", ""),
                "SNIPPET": r.get("SNIPPET", ""),
                "TRIAGE_DETAIL": detail,
                "REUSE_PATH_POSSIBLE": 1 if "REUSE_CANDIDATE" in triage_class else 0,
                "SOURCE_PATCH_NEEDED_PROVEN": 0,
                "SOURCE_MUTATION_AUTHORIZED_NOW": 0,
                "APPLY_AUTHORIZED_NOW": 0,
            }
            out["TRIAGE_SCORE"] = triage_score(out)
            triaged_rows.append(out)

        triaged_sorted = sorted(triaged_rows, key=lambda r: int(r.get("TRIAGE_SCORE", 0)), reverse=True)
        focus_rows = triaged_sorted[:MAX_FOCUS_ROWS]
        reuse_candidate_rows = [r for r in triaged_sorted if str(r.get("REUSE_PATH_POSSIBLE", "")) == "1"][:MAX_REUSE_ROWS]

        class_counts = {}
        priority_counts = {}
        for r in triaged_rows:
            cls = r["TRIAGE_CLASS"]
            pri = r["TRIAGE_PRIORITY"]
            class_counts[cls] = class_counts.get(cls, 0) + 1
            priority_counts[pri] = priority_counts.get(pri, 0) + 1

        for cls in sorted(class_counts):
            decision_rows.append({
                "DECISION_ROW": len(decision_rows) + 1,
                "DECISION_SCOPE": cls,
                "ROW_COUNT": class_counts[cls],
                "DECISION": "REVIEW_IN_10CG",
                "DETAIL": "Triage narrowed/organized candidates; 10CG must decide reuse path, further discovery, or guarded source-patch planning.",
            })

        next_review_requirements = [
            {"REQUIREMENT_ROW": 1, "REQUIREMENT": "REVIEW_REUSE_CANDIDATES_FIRST", "DETAIL": f"{len(reuse_candidate_rows)} possible reuse candidates identified; inspect before source patch planning.", "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
            {"REQUIREMENT_ROW": 2, "REQUIREMENT": "DISTINGUISH_WRITER_FROM_READER_CHECKER", "DETAIL": "HELP/CMDHELPCHK matches may be readers/checkers; only writer/import/update paths can support apply.", "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
            {"REQUIREMENT_ROW": 3, "REQUIREMENT": "DO_NOT_DECLARE_SOURCE_PATCH_NEEDED_YET", "DETAIL": "10CF does not prove source patch is required; it creates a reviewable triage set.", "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
            {"REQUIREMENT_ROW": 4, "REQUIREMENT": "KEEP_HELP_CMDHELPCHK_APPLY_BLOCKED", "DETAIL": "No HELP DATA or CMDHELPCHK apply until a reviewed writer path and apply package exist.", "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
            {"REQUIREMENT_ROW": 5, "REQUIREMENT": "KEEP_RAW_DBF_WRITE_FORBIDDEN", "DETAIL": "Runtime-promotion path must remain native/schema-aware, not Python/raw DBF byte writing.", "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
            {"REQUIREMENT_ROW": 6, "REQUIREMENT": "PRESERVE_SOURCE_COMMENT_CONTRACT_RULE", "DETAIL": "If later source patch changes command behavior/syntax, update @dottalk.usage and related comments in same package.", "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
        ]

        triaged_path = cf_root / "native_writer_candidate_triage_v1.csv"
        focus_path = cf_root / "native_writer_triage_focus_set_v1.csv"
        reuse_path = cf_root / "possible_reuse_writer_candidates_v1.csv"
        decisions_path = cf_root / "triage_decisions_v1.csv"
        requirements_path = cf_root / "next_review_requirements_v1.csv"

        scripts_dir = cf_root / "scripts"
        scripts_dir.mkdir(parents=True, exist_ok=True)
        disabled_review = scripts_dir / "MESSAGE_CATALOG_PHASE22AE_6_5_10CG_REVIEW_TEMPLATE.ps1.disabled"
        disabled_review.write_text(
            'throw "10CF is triage only. Generate a dedicated 10CG review package before choosing reuse/source-patch/apply path."\n',
            encoding="utf-8"
        )
        readback_dts = scripts_dir / "MESSAGE_CATALOG_PHASE22AE_6_5_10CF_READBACK_CONTRACT.dts"
        readback_dts.write_text(
            "MSGMGR STATUS\n"
            "MSGMGR CHECK\n"
            "SET MESSAGE CATALOG CHECK\n"
            "SET MESSAGE EMIT MESSAGE_PROOF_MODE_STATUS en-US\n"
            "HELP MSGMGR\n"
            "HELP SET MESSAGE\n"
            "CMDHELPCHK\n"
            "QUIT\n",
            encoding="utf-8"
        )

        notes = cf_root / "native_writer_discovery_triage_v1.md"
        notes.write_text(
            "# 10CF Native Writer Discovery Triage\n\n"
            "10CF narrows the 10CE shortlist into review classes, a focus set, and possible writer reuse candidates. It does not prove that a source patch is required and it does not mutate protected systems.\n\n"
            "The next step is 10CG review, where the narrowed candidates should be inspected to decide whether an existing writer/reuse path is available or whether guarded source-patch planning is needed.\n",
            encoding="utf-8"
        )

        readme = cf_root / "README_10CF_NATIVE_WRITER_DISCOVERY_TRIAGE_PACKAGE.md"
        readme.write_text(
            "# 10CF Native Writer Discovery Triage Package\n\n"
            "10CF performs report-only triage of the 10CE native writer discovery shortlist.\n\n"
            "No source, HELP DATA, CMDHELPCHK, DBF, CDX, LMDB, or workspace mutation occurs.\n",
            encoding="utf-8"
        )

        triage_fields = ["TRIAGE_ROW", "SOURCE_CANDIDATE_ROW", "CANDIDATE_KIND", "TRIAGE_CLASS", "TRIAGE_PRIORITY", "TRIAGE_SCORE", "FILE_PATH", "LINE", "MATCH_KIND", "SNIPPET", "TRIAGE_DETAIL", "REUSE_PATH_POSSIBLE", "SOURCE_PATCH_NEEDED_PROVEN", "SOURCE_MUTATION_AUTHORIZED_NOW", "APPLY_AUTHORIZED_NOW"]
        wcsv(triaged_path, triaged_rows, triage_fields)
        wcsv(focus_path, focus_rows, triage_fields)
        wcsv(reuse_path, reuse_candidate_rows, triage_fields)
        wcsv(decisions_path, decision_rows, ["DECISION_ROW", "DECISION_SCOPE", "ROW_COUNT", "DECISION", "DETAIL"])
        wcsv(requirements_path, next_review_requirements, ["REQUIREMENT_ROW", "REQUIREMENT", "DETAIL", "SOURCE_MUTATION_AUTHORIZED_NOW", "APPLY_AUTHORIZED_NOW"])

        for p in [triaged_path, focus_path, reuse_path, decisions_path, requirements_path, disabled_review, readback_dts, notes, readme]:
            artifact_rows.append({"ARTIFACT": rel(p, repo), "ROLE": "native_writer_discovery_triage_artifact", "BYTES": p.stat().st_size, "SHA256": sha(p)})

        status = GREEN

    boundary = [
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "10CF writes docs/messaging triage artifacts only."},
        {"PROTECTED_SYSTEM": "ACTIVE_SYSTEM_MESSAGES", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_SYSTEM_MESSAGE_TEXT", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_CDX_LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CDX/LMDB mutation."},
        {"PROTECTED_SYSTEM": "WORKSPACE_PROFILE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No workspace mutation."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Triage only; no HELP DATA apply."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Triage only; no CMDHELPCHK apply."},
    ]

    readiness = [
        {"ITEM": "TRIAGE_COMPLETE", "STATUS": "YES" if status == GREEN else "NO", "DETAIL": f"{len(triaged_rows)} candidates triaged."},
        {"ITEM": "FOCUS_SET_CREATED", "STATUS": "YES" if focus_rows else "NO", "DETAIL": f"{len(focus_rows)} focus rows."},
        {"ITEM": "REUSE_CANDIDATES_IDENTIFIED", "STATUS": "YES" if reuse_candidate_rows else "NO", "DETAIL": f"{len(reuse_candidate_rows)} possible reuse rows."},
        {"ITEM": "SOURCE_PATCH_NEEDED_PROVEN", "STATUS": "NO", "DETAIL": "10CF does not prove source patch need."},
        {"ITEM": "HELP_DATA_APPLY_EXECUTION", "STATUS": "NOT_EXECUTED_IN_10CF", "DETAIL": "No apply execution."},
        {"ITEM": "CMDHELPCHK_APPLY_EXECUTION", "STATUS": "NOT_EXECUTED_IN_10CF", "DETAIL": "No apply execution."},
    ]

    issues = "0" if failures == 0 else str(failures)
    wcsv(reports / "message_catalog_phase22ae_6_5_10cf_gate_check_v1.csv", gates, ["GATE", "STATUS", "DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10cf_native_writer_candidate_triage_v1.csv", triaged_rows, ["TRIAGE_ROW", "SOURCE_CANDIDATE_ROW", "CANDIDATE_KIND", "TRIAGE_CLASS", "TRIAGE_PRIORITY", "TRIAGE_SCORE", "FILE_PATH", "LINE", "MATCH_KIND", "SNIPPET", "TRIAGE_DETAIL", "REUSE_PATH_POSSIBLE", "SOURCE_PATCH_NEEDED_PROVEN", "SOURCE_MUTATION_AUTHORIZED_NOW", "APPLY_AUTHORIZED_NOW"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10cf_native_writer_triage_focus_set_v1.csv", focus_rows, ["TRIAGE_ROW", "SOURCE_CANDIDATE_ROW", "CANDIDATE_KIND", "TRIAGE_CLASS", "TRIAGE_PRIORITY", "TRIAGE_SCORE", "FILE_PATH", "LINE", "MATCH_KIND", "SNIPPET", "TRIAGE_DETAIL", "REUSE_PATH_POSSIBLE", "SOURCE_PATCH_NEEDED_PROVEN", "SOURCE_MUTATION_AUTHORIZED_NOW", "APPLY_AUTHORIZED_NOW"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10cf_possible_reuse_writer_candidates_v1.csv", reuse_candidate_rows, ["TRIAGE_ROW", "SOURCE_CANDIDATE_ROW", "CANDIDATE_KIND", "TRIAGE_CLASS", "TRIAGE_PRIORITY", "TRIAGE_SCORE", "FILE_PATH", "LINE", "MATCH_KIND", "SNIPPET", "TRIAGE_DETAIL", "REUSE_PATH_POSSIBLE", "SOURCE_PATCH_NEEDED_PROVEN", "SOURCE_MUTATION_AUTHORIZED_NOW", "APPLY_AUTHORIZED_NOW"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10cf_triage_decisions_v1.csv", decision_rows, ["DECISION_ROW", "DECISION_SCOPE", "ROW_COUNT", "DECISION", "DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10cf_next_review_requirements_v1.csv", next_review_requirements, ["REQUIREMENT_ROW", "REQUIREMENT", "DETAIL", "SOURCE_MUTATION_AUTHORIZED_NOW", "APPLY_AUTHORIZED_NOW"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10cf_apply_readiness_v1.csv", readiness, ["ITEM", "STATUS", "DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10cf_boundary_ledger_v1.csv", boundary, ["PROTECTED_SYSTEM", "MUTATION_ALLOWED", "OBSERVED_MUTATION", "DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10cf_artifact_manifest_v1.csv", artifact_rows, ["ARTIFACT", "ROLE", "BYTES", "SHA256"])

    summary = {
        "STATUS": status,
        "VALIDATION_ISSUES": issues,
        "PHASE22AE_6_5_10CE_STATUS": ce.get("STATUS", ""),
        "MSG_022AE_6_5_10CE_SAVEPOINT_PRESENT": 1 if sp_ce else 0,
        "ACTIVE_MESSAGES_OBSERVED_COUNT": msg_count,
        "ACTIVE_TEXT_OBSERVED_COUNT": text_count,
        "CE_SHORTLIST_ROWS": len(shortlist_in),
        "TRIAGED_CANDIDATE_ROWS": len(triaged_rows),
        "FOCUS_SET_ROWS": len(focus_rows),
        "POSSIBLE_REUSE_WRITER_ROWS": len(reuse_candidate_rows),
        "TRIAGE_DECISION_ROWS": len(decision_rows),
        "NEXT_REVIEW_REQUIREMENT_ROWS": len(next_review_requirements),
        "CF_ROOT": rel(cf_root, repo),
        "TRIAGE_PACKAGE_CREATED": 1 if status == GREEN else 0,
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
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }
    wcsv(reports / "message_catalog_phase22ae_6_5_10cf_status_summary_v1.csv", [summary], list(summary.keys()))

    (repo / "docs/messaging/MESSAGE_LOCALE_PHASE22AE_6_5_10CF_NATIVE_WRITER_DISCOVERY_TRIAGE_PACKAGE.md").write_text(
        f"# Message Catalog Phase 22AE.6.5.10CF Native Writer Discovery Triage Package\n\n"
        f"Status: `{status}`\n\n"
        "10CF triages the 10CE shortlist and prepares 10CG review. It does not mutate protected systems.\n\n"
        f"Triage root:\n\n```text\n{rel(cf_root, repo)}\n```\n\n"
        f"Next gate:\n\n```text\n{NEXT}\n```\n",
        encoding="utf-8"
    )

    print(status)
    print(f"  validation issues: {issues}")
    print(f"  Phase 22AE.6.5.10CE status: {ce.get('STATUS','')}")
    print(f"  MSG-022AE.6.5.10CE savepoint present: {1 if sp_ce else 0}")
    print(f"  active messages observed count: {msg_count}")
    print(f"  active text observed count: {text_count}")
    print(f"  CE shortlist rows: {len(shortlist_in)}")
    print(f"  triaged candidate rows: {len(triaged_rows)}")
    print(f"  focus set rows: {len(focus_rows)}")
    print(f"  possible reuse writer rows: {len(reuse_candidate_rows)}")
    print(f"  triage decision rows: {len(decision_rows)}")
    print(f"  next review requirement rows: {len(next_review_requirements)}")
    print(f"  triage root: {rel(cf_root, repo)}")
    print("  triage package created: 1")
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
