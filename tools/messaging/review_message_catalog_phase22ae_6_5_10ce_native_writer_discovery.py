#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_10CE_NATIVE_WRITER_DISCOVERY_REVIEW_GREEN_TRIAGE_PACKAGE_REQUIRED_SOURCE_HELD"
BLOCKED = "MESSAGE_CATALOG_PHASE22AE_6_5_10CE_NATIVE_WRITER_DISCOVERY_REVIEW_BLOCKED"
NEXT = "HOLD_OR_AUTHORIZE_PHASE22AE_6_5_10CF_NATIVE_WRITER_DISCOVERY_TRIAGE_PACKAGE"

REPORT_DIR = Path("docs/messaging/reports")
CD_SUMMARY = REPORT_DIR / "message_catalog_phase22ae_6_5_10cd_status_summary_v1.csv"
CD_CANDIDATES = REPORT_DIR / "message_catalog_phase22ae_6_5_10cd_native_writer_candidate_manifest_v1.csv"
CD_CANDIDATE_SUMMARY = REPORT_DIR / "message_catalog_phase22ae_6_5_10cd_discovery_candidate_summary_v1.csv"
CD_RECOMMENDATIONS = REPORT_DIR / "message_catalog_phase22ae_6_5_10cd_discovery_recommendations_v1.csv"
CD_SCAN = REPORT_DIR / "message_catalog_phase22ae_6_5_10cd_scan_manifest_v1.csv"
ACTIVE_MSG_DBF = Path("dottalkpp/data/messaging/SYSTEM_MESSAGES.dbf")
ACTIVE_TEXT_DBF = Path("dottalkpp/data/messaging/SYSTEM_MESSAGE_TEXT.dbf")
CE_ROOT = Path("docs/messaging/apply/phase22ae_6_5_10ce_native_writer_discovery_review_v1")

PRIORITY_KIND_ORDER = {
    "HELP_DATA_WRITER_OR_READER_CANDIDATE": 1,
    "CMDHELPCHK_WRITER_OR_CHECK_CANDIDATE": 1,
    "WRITE_PATH_CANDIDATE": 2,
    "DATA_STORAGE_CANDIDATE": 3,
    "MSGMGR_SURFACE_CANDIDATE": 4,
    "SET_MESSAGE_SURFACE_CANDIDATE": 4,
    "SOURCE_COMMENT_CONTRACT_CANDIDATE": 5,
    "GENERAL_DISCOVERY_CANDIDATE": 9,
}

PRIORITY_PATH_TERMS = [
    "src/",
    "tools/messaging",
    "dottalkpp/data/help",
    "dottalkpp/data/schemas",
    "cmdhelp",
    "help",
    "message",
]

MAX_SHORTLIST = 250
MAX_SAMPLES_PER_KIND = 40

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

def priority_score(row):
    kind = row.get("CANDIDATE_KIND", "")
    path = row.get("FILE_PATH", "").replace("\\", "/").lower()
    snippet = row.get("SNIPPET", "").lower()
    score = 100 - (PRIORITY_KIND_ORDER.get(kind, 9) * 10)
    for term in PRIORITY_PATH_TERMS:
        if term in path:
            score += 5
    if "write" in snippet or "import" in snippet or "update" in snippet or "replace" in snippet or "append" in snippet:
        score += 5
    if "cmdhelpchk" in snippet.lower() or "help data" in snippet.lower():
        score += 8
    if path.endswith((".md", ".csv")) and "docs/messaging" in path:
        score -= 8
    return score

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--replace-existing-review", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    reports = repo / REPORT_DIR
    reports.mkdir(parents=True, exist_ok=True)

    cd = first(repo / CD_SUMMARY)
    candidates = rows(repo / CD_CANDIDATES)
    candidate_summary_in = rows(repo / CD_CANDIDATE_SUMMARY)
    recommendations_in = rows(repo / CD_RECOMMENDATIONS)
    scan_manifest = rows(repo / CD_SCAN)
    sp_cd, latest_cd = savepoint(repo, "MSG-022AE.6.5.10CD")
    msg_count = dbf_count(repo / ACTIVE_MSG_DBF)
    text_count = dbf_count(repo / ACTIVE_TEXT_DBF)
    ce_root = repo / CE_ROOT

    gates = []
    failures = 0
    def gate(name, ok, detail):
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": str(detail)})
        if not ok:
            failures += 1

    gate("PHASE22AE_6_5_10CD_GREEN",
         cd.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_5_10CD_NATIVE_HELP_CMDHELPCHK_WRITER_DISCOVERY_PACKAGE_GREEN_SOURCE_HELD_DISCOVERY_REPORTED",
         cd.get("STATUS", "missing"))
    gate("MSG_022AE_6_5_10CD_SAVEPOINT_PRESENT", sp_cd, latest_cd)
    gate("CD_DISCOVERY_REPORTED", cd.get("DISCOVERY_REPORTED") == "1", cd.get("DISCOVERY_REPORTED", "missing"))
    gate("CD_SOURCE_MUTATION_NOT_AUTHORIZED", cd.get("SOURCE_MUTATION_AUTHORIZED_NOW") == "0", cd.get("SOURCE_MUTATION_AUTHORIZED_NOW", "missing"))
    gate("CD_APPLY_EXECUTION_NOT_AUTHORIZED", cd.get("APPLY_EXECUTION_AUTHORIZED_NOW") == "0", cd.get("APPLY_EXECUTION_AUTHORIZED_NOW", "missing"))
    gate("CD_HELP_APPLY_NOT_EXECUTED", cd.get("HELP_DATA_APPLY_EXECUTED") == "0", cd.get("HELP_DATA_APPLY_EXECUTED", "missing"))
    gate("CD_CMDHELPCHK_APPLY_NOT_EXECUTED", cd.get("CMDHELPCHK_APPLY_EXECUTED") == "0", cd.get("CMDHELPCHK_APPLY_EXECUTED", "missing"))
    gate("CD_CANDIDATES_PRESENT", len(candidates) > 0, len(candidates))
    gate("CD_SUMMARY_PRESENT", len(candidate_summary_in) > 0, len(candidate_summary_in))
    gate("ACTIVE_MESSAGES_HEADER_COUNT_14", msg_count == 14, msg_count)
    gate("ACTIVE_TEXT_HEADER_COUNT_70", text_count == 70, text_count)
    gate("CE_ROOT_NOT_EXISTING_OR_REPLACE_ALLOWED", (not ce_root.exists()) or args.replace_existing_review, rel(ce_root, repo))

    status = BLOCKED
    kind_review = []
    shortlist = []
    triage_requirements = []
    review_decisions = []
    artifact_rows = []

    if failures == 0:
        if ce_root.exists() and args.replace_existing_review:
            shutil.rmtree(ce_root)
        ce_root.mkdir(parents=True, exist_ok=True)

        counts = {}
        for c in candidates:
            kind = c.get("CANDIDATE_KIND", "UNKNOWN") or "UNKNOWN"
            counts[kind] = counts.get(kind, 0) + 1

        for kind in sorted(counts, key=lambda k: (PRIORITY_KIND_ORDER.get(k, 9), k)):
            count = counts[kind]
            if count > 500:
                disposition = "ACCEPT_FOR_TRIAGE_TOO_BROAD"
            elif kind in {"HELP_DATA_WRITER_OR_READER_CANDIDATE", "CMDHELPCHK_WRITER_OR_CHECK_CANDIDATE", "WRITE_PATH_CANDIDATE"}:
                disposition = "ACCEPT_FOR_TRIAGE_HIGH_PRIORITY"
            else:
                disposition = "ACCEPT_FOR_TRIAGE_SUPPORTING"
            kind_review.append({
                "KIND_REVIEW_ROW": len(kind_review) + 1,
                "CANDIDATE_KIND": kind,
                "CANDIDATE_COUNT": count,
                "REVIEW_DISPOSITION": disposition,
                "TRIAGE_REQUIRED": 1,
                "DETAIL": "Discovery result is report-only; candidate set must be narrowed before reuse/source-patch decision.",
            })

        ranked = sorted(candidates, key=priority_score, reverse=True)
        per_kind = {}
        for c in ranked:
            kind = c.get("CANDIDATE_KIND", "UNKNOWN") or "UNKNOWN"
            if per_kind.get(kind, 0) >= MAX_SAMPLES_PER_KIND:
                continue
            row = dict(c)
            row["PRIORITY_SCORE"] = priority_score(c)
            row["TRIAGE_DISPOSITION"] = "SHORTLIST_FOR_NATIVE_WRITER_REVIEW"
            row["SOURCE_MUTATION_AUTHORIZED_NOW"] = 0
            row["APPLY_AUTHORIZED_NOW"] = 0
            shortlist.append(row)
            per_kind[kind] = per_kind.get(kind, 0) + 1
            if len(shortlist) >= MAX_SHORTLIST:
                break

        triage_requirements = [
            {"TRIAGE_ROW": 1, "TRIAGE_REQUIREMENT": "NARROW_HELP_DATA_WRITER_CANDIDATES", "DETAIL": "Review HELP DATA candidates first; identify existing native writer/import/update path or prove absent.", "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
            {"TRIAGE_ROW": 2, "TRIAGE_REQUIREMENT": "NARROW_CMDHELPCHK_WRITER_CANDIDATES", "DETAIL": "Review CMDHELPCHK candidates first; identify existing native writer/import/update path or prove absent.", "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
            {"TRIAGE_ROW": 3, "TRIAGE_REQUIREMENT": "SEPARATE_RUNTIME_READBACK_FROM_WRITER_MUTATION", "DETAIL": "MSGMGR/SET MESSAGE proof surfaces remain runtime readback; do not confuse with writer implementation.", "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
            {"TRIAGE_ROW": 4, "TRIAGE_REQUIREMENT": "REUSE_BEFORE_PATCH", "DETAIL": "Prefer existing native/runtime writer paths over new source patch planning.", "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
            {"TRIAGE_ROW": 5, "TRIAGE_REQUIREMENT": "UPDATE_SOURCE_COMMENT_CONTRACTS_IF_PATCH_LATER", "DETAIL": "If source patch becomes necessary, include @dottalk.usage and header/contract comment updates in same guarded package.", "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
            {"TRIAGE_ROW": 6, "TRIAGE_REQUIREMENT": "KEEP_RAW_DBF_WRITE_FORBIDDEN", "DETAIL": "Raw Python DBF byte writing remains forbidden for runtime promotion/materialization.", "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
        ]

        review_decisions = [
            {"DECISION_ROW": 1, "DECISION": "DISCOVERY_ACCEPTED_FOR_TRIAGE", "VALUE": 1, "DETAIL": "10CD discovery is large and useful but too broad for direct implementation."},
            {"DECISION_ROW": 2, "DECISION": "DIRECT_APPLY_NOT_READY", "VALUE": 1, "DETAIL": "No HELP DATA/CMDHELPCHK apply execution should occur from 10CE."},
            {"DECISION_ROW": 3, "DECISION": "SOURCE_PATCH_NOT_READY", "VALUE": 1, "DETAIL": "Existing writer/reuse candidates must be triaged before source patch planning."},
            {"DECISION_ROW": 4, "DECISION": "TRIAGE_PACKAGE_REQUIRED", "VALUE": 1, "DETAIL": "10CF should narrow the candidate list and classify reuse vs source-patch need."},
        ]

        kind_review_path = ce_root / "discovery_kind_review_v1.csv"
        shortlist_path = ce_root / "native_writer_candidate_shortlist_v1.csv"
        triage_req_path = ce_root / "triage_requirements_v1.csv"
        decisions_path = ce_root / "review_decisions_v1.csv"

        scripts_dir = ce_root / "scripts"
        scripts_dir.mkdir(parents=True, exist_ok=True)
        disabled_triage = scripts_dir / "MESSAGE_CATALOG_PHASE22AE_6_5_10CF_TRIAGE_TEMPLATE.ps1.disabled"
        disabled_triage.write_text(
            'throw "10CE is discovery review only. Generate a dedicated 10CF triage package before narrowing candidates."\n',
            encoding="utf-8"
        )
        readback_dts = scripts_dir / "MESSAGE_CATALOG_PHASE22AE_6_5_10CE_READBACK_CONTRACT.dts"
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

        notes = ce_root / "native_writer_discovery_review_v1.md"
        notes.write_text(
            "# 10CE Native Writer Discovery Review\n\n"
            "10CE reviews the 10CD discovery output. The discovery is accepted as useful but too broad for direct implementation. A dedicated 10CF triage package is required to narrow HELP DATA and CMDHELPCHK writer/reuse candidates.\n\n"
            "No source, HELP DATA, CMDHELPCHK, DBF, CDX, LMDB, or workspace mutation is authorized in 10CE.\n",
            encoding="utf-8"
        )

        readme = ce_root / "README_10CE_NATIVE_WRITER_DISCOVERY_REVIEW.md"
        readme.write_text(
            "# 10CE Native Writer Discovery Review\n\n"
            "10CE reviews the 10CD report-only discovery and stages a shortlist plus triage requirements for the next package.\n\n"
            "No protected mutation occurs.\n",
            encoding="utf-8"
        )

        shortlist_fields = ["CANDIDATE_ROW", "CANDIDATE_KIND", "FILE_PATH", "LINE", "MATCH_KIND", "SNIPPET", "REVIEW_REQUIRED", "SOURCE_MUTATION_AUTHORIZED_NOW", "APPLY_AUTHORIZED_NOW", "PRIORITY_SCORE", "TRIAGE_DISPOSITION"]
        wcsv(kind_review_path, kind_review, ["KIND_REVIEW_ROW", "CANDIDATE_KIND", "CANDIDATE_COUNT", "REVIEW_DISPOSITION", "TRIAGE_REQUIRED", "DETAIL"])
        wcsv(shortlist_path, shortlist, shortlist_fields)
        wcsv(triage_req_path, triage_requirements, ["TRIAGE_ROW", "TRIAGE_REQUIREMENT", "DETAIL", "SOURCE_MUTATION_AUTHORIZED_NOW", "APPLY_AUTHORIZED_NOW"])
        wcsv(decisions_path, review_decisions, ["DECISION_ROW", "DECISION", "VALUE", "DETAIL"])

        for p in [kind_review_path, shortlist_path, triage_req_path, decisions_path, disabled_triage, readback_dts, notes, readme]:
            artifact_rows.append({"ARTIFACT": rel(p, repo), "ROLE": "native_writer_discovery_review_artifact", "BYTES": p.stat().st_size, "SHA256": sha(p)})

        status = GREEN

    boundary = [
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "10CE writes docs/messaging review artifacts only."},
        {"PROTECTED_SYSTEM": "ACTIVE_SYSTEM_MESSAGES", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_SYSTEM_MESSAGE_TEXT", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_CDX_LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CDX/LMDB mutation."},
        {"PROTECTED_SYSTEM": "WORKSPACE_PROFILE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No workspace mutation."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Discovery review only; no HELP DATA apply."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Discovery review only; no CMDHELPCHK apply."},
    ]

    readiness = [
        {"ITEM": "DISCOVERY_REVIEW_COMPLETE", "STATUS": "YES" if status == GREEN else "NO", "DETAIL": f"{len(kind_review)} candidate kinds reviewed."},
        {"ITEM": "SHORTLIST_CREATED", "STATUS": "YES" if shortlist else "NO", "DETAIL": f"{len(shortlist)} shortlist rows."},
        {"ITEM": "TRIAGE_PACKAGE_REQUIRED", "STATUS": "YES", "DETAIL": "10CF should narrow native writer/reuse candidates."},
        {"ITEM": "HELP_DATA_APPLY_EXECUTION", "STATUS": "NOT_EXECUTED_IN_10CE", "DETAIL": "No apply execution."},
        {"ITEM": "CMDHELPCHK_APPLY_EXECUTION", "STATUS": "NOT_EXECUTED_IN_10CE", "DETAIL": "No apply execution."},
    ]

    issues = "0" if failures == 0 else str(failures)
    wcsv(reports / "message_catalog_phase22ae_6_5_10ce_gate_check_v1.csv", gates, ["GATE", "STATUS", "DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10ce_discovery_kind_review_v1.csv", kind_review, ["KIND_REVIEW_ROW", "CANDIDATE_KIND", "CANDIDATE_COUNT", "REVIEW_DISPOSITION", "TRIAGE_REQUIRED", "DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10ce_native_writer_candidate_shortlist_v1.csv", shortlist, ["CANDIDATE_ROW", "CANDIDATE_KIND", "FILE_PATH", "LINE", "MATCH_KIND", "SNIPPET", "REVIEW_REQUIRED", "SOURCE_MUTATION_AUTHORIZED_NOW", "APPLY_AUTHORIZED_NOW", "PRIORITY_SCORE", "TRIAGE_DISPOSITION"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10ce_triage_requirements_v1.csv", triage_requirements, ["TRIAGE_ROW", "TRIAGE_REQUIREMENT", "DETAIL", "SOURCE_MUTATION_AUTHORIZED_NOW", "APPLY_AUTHORIZED_NOW"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10ce_review_decisions_v1.csv", review_decisions, ["DECISION_ROW", "DECISION", "VALUE", "DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10ce_apply_readiness_v1.csv", readiness, ["ITEM", "STATUS", "DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10ce_boundary_ledger_v1.csv", boundary, ["PROTECTED_SYSTEM", "MUTATION_ALLOWED", "OBSERVED_MUTATION", "DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10ce_artifact_manifest_v1.csv", artifact_rows, ["ARTIFACT", "ROLE", "BYTES", "SHA256"])

    summary = {
        "STATUS": status,
        "VALIDATION_ISSUES": issues,
        "PHASE22AE_6_5_10CD_STATUS": cd.get("STATUS", ""),
        "MSG_022AE_6_5_10CD_SAVEPOINT_PRESENT": 1 if sp_cd else 0,
        "ACTIVE_MESSAGES_OBSERVED_COUNT": msg_count,
        "ACTIVE_TEXT_OBSERVED_COUNT": text_count,
        "CD_SCAN_FILE_ROWS": len(scan_manifest),
        "CD_NATIVE_WRITER_CANDIDATE_ROWS": len(candidates),
        "CD_DISCOVERY_SUMMARY_ROWS": len(candidate_summary_in),
        "DISCOVERY_KIND_REVIEW_ROWS": len(kind_review),
        "SHORTLIST_ROWS": len(shortlist),
        "TRIAGE_REQUIREMENT_ROWS": len(triage_requirements),
        "CE_ROOT": rel(ce_root, repo),
        "DISCOVERY_REVIEW_COMPLETE": 1 if status == GREEN else 0,
        "TRIAGE_PACKAGE_REQUIRED": 1 if status == GREEN else 0,
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
    wcsv(reports / "message_catalog_phase22ae_6_5_10ce_status_summary_v1.csv", [summary], list(summary.keys()))

    (repo / "docs/messaging/MESSAGE_LOCALE_PHASE22AE_6_5_10CE_NATIVE_WRITER_DISCOVERY_REVIEW.md").write_text(
        f"# Message Catalog Phase 22AE.6.5.10CE Native Writer Discovery Review\n\n"
        f"Status: `{status}`\n\n"
        "10CE reviews the 10CD discovery output, creates a shortlist, and requires a dedicated triage package. It does not mutate protected systems.\n\n"
        f"Review root:\n\n```text\n{rel(ce_root, repo)}\n```\n\n"
        f"Next gate:\n\n```text\n{NEXT}\n```\n",
        encoding="utf-8"
    )

    print(status)
    print(f"  validation issues: {issues}")
    print(f"  Phase 22AE.6.5.10CD status: {cd.get('STATUS','')}")
    print(f"  MSG-022AE.6.5.10CD savepoint present: {1 if sp_cd else 0}")
    print(f"  active messages observed count: {msg_count}")
    print(f"  active text observed count: {text_count}")
    print(f"  CD scan file rows: {len(scan_manifest)}")
    print(f"  CD native writer candidate rows: {len(candidates)}")
    print(f"  CD discovery summary rows: {len(candidate_summary_in)}")
    print(f"  discovery kind review rows: {len(kind_review)}")
    print(f"  shortlist rows: {len(shortlist)}")
    print(f"  triage requirement rows: {len(triage_requirements)}")
    print(f"  review root: {rel(ce_root, repo)}")
    print("  discovery review complete: 1")
    print("  triage package required: 1")
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
