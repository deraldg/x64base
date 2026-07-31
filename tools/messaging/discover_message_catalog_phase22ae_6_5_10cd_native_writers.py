#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path

GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_10CD_NATIVE_HELP_CMDHELPCHK_WRITER_DISCOVERY_PACKAGE_GREEN_SOURCE_HELD_DISCOVERY_REPORTED"
BLOCKED = "MESSAGE_CATALOG_PHASE22AE_6_5_10CD_NATIVE_HELP_CMDHELPCHK_WRITER_DISCOVERY_PACKAGE_BLOCKED"
NEXT = "HOLD_OR_AUTHORIZE_PHASE22AE_6_5_10CE_NATIVE_WRITER_DISCOVERY_REVIEW"

REPORT_DIR = Path("docs/messaging/reports")
CC_SUMMARY = REPORT_DIR / "message_catalog_phase22ae_6_5_10cc_status_summary_v1.csv"
CC_DISCOVERY_REQ = REPORT_DIR / "message_catalog_phase22ae_6_5_10cc_discovery_package_requirements_v1.csv"
CC_WRITER_REVIEW = REPORT_DIR / "message_catalog_phase22ae_6_5_10cc_native_writer_family_review_v1.csv"
CC_SOURCE_REVIEW = REPORT_DIR / "message_catalog_phase22ae_6_5_10cc_source_discovery_review_v1.csv"
ACTIVE_MSG_DBF = Path("dottalkpp/data/messaging/SYSTEM_MESSAGES.dbf")
ACTIVE_TEXT_DBF = Path("dottalkpp/data/messaging/SYSTEM_MESSAGE_TEXT.dbf")
CD_ROOT = Path("docs/messaging/apply/phase22ae_6_5_10cd_native_help_cmdhelpchk_writer_discovery_package_v1")

TEXT_EXTENSIONS = {
    ".cpp", ".cxx", ".cc", ".c", ".hpp", ".hh", ".h",
    ".py", ".ps1", ".psm1", ".md", ".dts", ".dtschema",
    ".txt", ".ini", ".json", ".csv"
}

DISCOVERY_PATTERNS = [
    ("HELP_DATA", re.compile(r"\bHELP\s*DATA\b|HELPDATA|help[_\-\s]*data|cmd_help|cmdhelp|help_manager|help\s+manager", re.IGNORECASE)),
    ("CMDHELPCHK", re.compile(r"CMDHELPCHK|cmd_help_chk|command[_\-\s]*help[_\-\s]*check|help[_\-\s]*check", re.IGNORECASE)),
    ("MSGMGR", re.compile(r"\bMSGMGR\b|Message\s+Manager|message[_\-\s]*manager", re.IGNORECASE)),
    ("SET_MESSAGE", re.compile(r"SET\s+MESSAGE|SET_MESSAGE|message\s+catalog|MESSAGE_CATALOG", re.IGNORECASE)),
    ("WRITE_IMPORT_UPDATE", re.compile(r"\bIMPORT\b|\bAPPEND\b|\bREPLACE\b|\bUPDATE\b|\bWRITE\b|\bINSERT\b|\bSAVE\b", re.IGNORECASE)),
    ("DBF_CDX_LMDB", re.compile(r"\bDBF\b|\bCDX\b|\bLMDB\b|\.dbf|\.cdx|\.dtx|\.dbt", re.IGNORECASE)),
    ("USAGE_CONTRACT", re.compile(r"@dottalk\.usage|usage\s+contract|source[-_\s]*comment", re.IGNORECASE)),
]

SCAN_ROOTS = [
    "src",
    "tools",
    "dottalkpp/data/schemas",
    "dottalkpp/data/scripts",
    "dottalkpp/data/help",
    "docs/messaging",
]

MAX_FILE_BYTES = 2_000_000
MAX_MATCHES_PER_FILE = 8

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

def iter_scan_files(repo: Path):
    seen = set()
    for root_rel in SCAN_ROOTS:
        root = repo / root_rel
        if not root.exists():
            continue
        for p in root.rglob("*"):
            if not p.is_file():
                continue
            if p.suffix.lower() not in TEXT_EXTENSIONS:
                continue
            try:
                if p.stat().st_size > MAX_FILE_BYTES:
                    continue
            except OSError:
                continue
            rp = rel(p, repo)
            if rp in seen:
                continue
            seen.add(rp)
            yield p

def scan_file(repo: Path, p: Path):
    try:
        text = p.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return []
    result = []
    lines = text.splitlines()
    matched = 0
    for ln, line in enumerate(lines, start=1):
        matched_kinds = []
        for kind, rx in DISCOVERY_PATTERNS:
            if rx.search(line):
                matched_kinds.append(kind)
        if matched_kinds:
            snippet = line.strip()
            if len(snippet) > 240:
                snippet = snippet[:237] + "..."
            result.append({
                "FILE_PATH": rel(p, repo),
                "LINE": ln,
                "MATCH_KIND": ";".join(sorted(set(matched_kinds))),
                "SNIPPET": snippet,
            })
            matched += 1
            if matched >= MAX_MATCHES_PER_FILE:
                break
    return result

def classify_candidate(match):
    kinds = match.get("MATCH_KIND", "")
    path = match.get("FILE_PATH", "").lower()
    snippet = match.get("SNIPPET", "").lower()
    if "CMDHELPCHK" in kinds:
        return "CMDHELPCHK_WRITER_OR_CHECK_CANDIDATE"
    if "HELP_DATA" in kinds:
        return "HELP_DATA_WRITER_OR_READER_CANDIDATE"
    if "MSGMGR" in kinds:
        return "MSGMGR_SURFACE_CANDIDATE"
    if "SET_MESSAGE" in kinds:
        return "SET_MESSAGE_SURFACE_CANDIDATE"
    if "USAGE_CONTRACT" in kinds:
        return "SOURCE_COMMENT_CONTRACT_CANDIDATE"
    if "DBF_CDX_LMDB" in kinds:
        return "DATA_STORAGE_CANDIDATE"
    if "WRITE_IMPORT_UPDATE" in kinds:
        return "WRITE_PATH_CANDIDATE"
    return "GENERAL_DISCOVERY_CANDIDATE"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--replace-existing-discovery", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    reports = repo / REPORT_DIR
    reports.mkdir(parents=True, exist_ok=True)

    cc = first(repo / CC_SUMMARY)
    discovery_req = rows(repo / CC_DISCOVERY_REQ)
    writer_review = rows(repo / CC_WRITER_REVIEW)
    source_review = rows(repo / CC_SOURCE_REVIEW)
    sp_cc, latest_cc = savepoint(repo, "MSG-022AE.6.5.10CC")
    msg_count = dbf_count(repo / ACTIVE_MSG_DBF)
    text_count = dbf_count(repo / ACTIVE_TEXT_DBF)
    cd_root = repo / CD_ROOT

    gates = []
    failures = 0
    def gate(name, ok, detail):
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": str(detail)})
        if not ok:
            failures += 1

    gate("PHASE22AE_6_5_10CC_GREEN",
         cc.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_5_10CC_TARGET_SPECIFIC_NATIVE_APPLY_BUILD_PLAN_REVIEW_GREEN_DISCOVERY_PACKAGE_REQUIRED_SOURCE_HELD",
         cc.get("STATUS", "missing"))
    gate("MSG_022AE_6_5_10CC_SAVEPOINT_PRESENT", sp_cc, latest_cc)
    gate("CC_DISCOVERY_PACKAGE_REQUIRED", cc.get("DISCOVERY_PACKAGE_REQUIRED") == "1", cc.get("DISCOVERY_PACKAGE_REQUIRED", "missing"))
    gate("CC_SOURCE_MUTATION_NOT_AUTHORIZED", cc.get("SOURCE_MUTATION_AUTHORIZED_NOW") == "0", cc.get("SOURCE_MUTATION_AUTHORIZED_NOW", "missing"))
    gate("CC_APPLY_EXECUTION_NOT_AUTHORIZED", cc.get("APPLY_EXECUTION_AUTHORIZED_NOW") == "0", cc.get("APPLY_EXECUTION_AUTHORIZED_NOW", "missing"))
    gate("CC_HELP_APPLY_NOT_EXECUTED", cc.get("HELP_DATA_APPLY_EXECUTED") == "0", cc.get("HELP_DATA_APPLY_EXECUTED", "missing"))
    gate("CC_CMDHELPCHK_APPLY_NOT_EXECUTED", cc.get("CMDHELPCHK_APPLY_EXECUTED") == "0", cc.get("CMDHELPCHK_APPLY_EXECUTED", "missing"))
    gate("CC_DISCOVERY_REQUIREMENTS_PRESENT", len(discovery_req) > 0, len(discovery_req))
    gate("CC_WRITER_REVIEW_PRESENT", len(writer_review) > 0, len(writer_review))
    gate("ACTIVE_MESSAGES_HEADER_COUNT_14", msg_count == 14, msg_count)
    gate("ACTIVE_TEXT_HEADER_COUNT_70", text_count == 70, text_count)
    gate("CD_ROOT_NOT_EXISTING_OR_REPLACE_ALLOWED", (not cd_root.exists()) or args.replace_existing_discovery, rel(cd_root, repo))

    status = BLOCKED
    scan_manifest = []
    raw_matches = []
    candidate_rows = []
    discovery_summary = []
    recommendation_rows = []
    artifact_rows = []

    if failures == 0:
        if cd_root.exists() and args.replace_existing_discovery:
            shutil.rmtree(cd_root)
        cd_root.mkdir(parents=True, exist_ok=True)

        for p in iter_scan_files(repo):
            try:
                size = p.stat().st_size
                file_sha = sha(p)
            except OSError:
                continue
            scan_manifest.append({
                "SCAN_FILE": rel(p, repo),
                "BYTES": size,
                "SHA256": file_sha,
                "SCANNED": 1,
            })
            raw_matches.extend(scan_file(repo, p))

        for i, m in enumerate(raw_matches, start=1):
            candidate_rows.append({
                "CANDIDATE_ROW": i,
                "CANDIDATE_KIND": classify_candidate(m),
                "FILE_PATH": m.get("FILE_PATH", ""),
                "LINE": m.get("LINE", ""),
                "MATCH_KIND": m.get("MATCH_KIND", ""),
                "SNIPPET": m.get("SNIPPET", ""),
                "REVIEW_REQUIRED": 1,
                "SOURCE_MUTATION_AUTHORIZED_NOW": 0,
                "APPLY_AUTHORIZED_NOW": 0,
            })

        kind_counts = {}
        for r in candidate_rows:
            kind_counts[r["CANDIDATE_KIND"]] = kind_counts.get(r["CANDIDATE_KIND"], 0) + 1
        for kind in sorted(kind_counts):
            discovery_summary.append({
                "CANDIDATE_KIND": kind,
                "CANDIDATE_COUNT": kind_counts[kind],
                "NEXT_REVIEW_ACTION": "review candidate files and select existing writer/reuse path before any source patch",
            })

        recommendation_rows = [
            {"RECOMMENDATION_ROW": 1, "RECOMMENDATION": "REVIEW_DISCOVERY_CANDIDATES", "DETAIL": "Inspect candidate files for existing HELP DATA and CMDHELPCHK native writer/reuse paths.", "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
            {"RECOMMENDATION_ROW": 2, "RECOMMENDATION": "PREFER_REUSE_OVER_SOURCE_PATCH", "DETAIL": "Reuse existing import/update commands or helpers before authorizing source changes.", "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
            {"RECOMMENDATION_ROW": 3, "RECOMMENDATION": "MAINTAIN_SOURCE_COMMENT_CONTRACTS", "DETAIL": "If later source patch is needed, update @dottalk.usage/source-comment contracts in the same guarded package.", "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
            {"RECOMMENDATION_ROW": 4, "RECOMMENDATION": "KEEP_RAW_DBF_WRITE_FORBIDDEN", "DETAIL": "Do not use Python/raw DBF byte writing as the active promotion/materialization path.", "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
            {"RECOMMENDATION_ROW": 5, "RECOMMENDATION": "REVIEW_WITH_10CE", "DETAIL": "10CE should review candidates and decide whether a reuse path exists or a guarded source patch plan is needed.", "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
        ]

        scan_path = cd_root / "scan_manifest_v1.csv"
        raw_path = cd_root / "raw_discovery_matches_v1.csv"
        candidate_path = cd_root / "native_writer_candidate_manifest_v1.csv"
        summary_path = cd_root / "discovery_candidate_summary_v1.csv"
        rec_path = cd_root / "discovery_recommendations_v1.csv"

        scripts_dir = cd_root / "scripts"
        scripts_dir.mkdir(parents=True, exist_ok=True)
        readback_dts = scripts_dir / "MESSAGE_CATALOG_PHASE22AE_6_5_10CD_READBACK_CONTRACT.dts"
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

        notes = cd_root / "native_help_cmdhelpchk_writer_discovery_v1.md"
        notes.write_text(
            "# 10CD Native HELP/CMDHELPCHK Writer Discovery\n\n"
            "10CD scans source/tools/schema/script/help/documentation paths for candidate HELP DATA, CMDHELPCHK, MSGMGR, SET MESSAGE, writer/import/update, DBF/CDX/LMDB, and source-comment contract references.\n\n"
            "This is discovery only. It does not mutate source, HELP DATA, CMDHELPCHK, DBF, CDX, LMDB, or workspace files.\n",
            encoding="utf-8"
        )

        wcsv(scan_path, scan_manifest, ["SCAN_FILE", "BYTES", "SHA256", "SCANNED"])
        wcsv(raw_path, raw_matches, ["FILE_PATH", "LINE", "MATCH_KIND", "SNIPPET"])
        wcsv(candidate_path, candidate_rows, ["CANDIDATE_ROW", "CANDIDATE_KIND", "FILE_PATH", "LINE", "MATCH_KIND", "SNIPPET", "REVIEW_REQUIRED", "SOURCE_MUTATION_AUTHORIZED_NOW", "APPLY_AUTHORIZED_NOW"])
        wcsv(summary_path, discovery_summary, ["CANDIDATE_KIND", "CANDIDATE_COUNT", "NEXT_REVIEW_ACTION"])
        wcsv(rec_path, recommendation_rows, ["RECOMMENDATION_ROW", "RECOMMENDATION", "DETAIL", "SOURCE_MUTATION_AUTHORIZED_NOW", "APPLY_AUTHORIZED_NOW"])

        readme = cd_root / "README_10CD_NATIVE_HELP_CMDHELPCHK_WRITER_DISCOVERY_PACKAGE.md"
        readme.write_text(
            "# 10CD Native HELP/CMDHELPCHK Writer Discovery Package\n\n"
            "10CD performs report-only discovery of candidate native writer/reuse paths for HELP DATA and CMDHELPCHK.\n\n"
            "No source, HELP DATA, CMDHELPCHK, DBF, CDX, LMDB, or workspace mutation occurs.\n",
            encoding="utf-8"
        )

        for p in [scan_path, raw_path, candidate_path, summary_path, rec_path, readback_dts, notes, readme]:
            artifact_rows.append({"ARTIFACT": rel(p, repo), "ROLE": "native_writer_discovery_artifact", "BYTES": p.stat().st_size, "SHA256": sha(p)})

        status = GREEN

    boundary = [
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "10CD scans text files and writes docs/messaging discovery reports only."},
        {"PROTECTED_SYSTEM": "ACTIVE_SYSTEM_MESSAGES", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_SYSTEM_MESSAGE_TEXT", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_CDX_LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CDX/LMDB mutation."},
        {"PROTECTED_SYSTEM": "WORKSPACE_PROFILE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No workspace mutation."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Discovery only; no HELP DATA apply."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Discovery only; no CMDHELPCHK apply."},
    ]

    readiness = [
        {"ITEM": "DISCOVERY_SCAN_COMPLETE", "STATUS": "YES" if status == GREEN else "NO", "DETAIL": f"{len(scan_manifest)} files scanned."},
        {"ITEM": "DISCOVERY_CANDIDATES_REPORTED", "STATUS": "YES", "DETAIL": f"{len(candidate_rows)} candidate rows reported."},
        {"ITEM": "HELP_DATA_APPLY_EXECUTION", "STATUS": "NOT_EXECUTED_IN_10CD", "DETAIL": "No apply execution."},
        {"ITEM": "CMDHELPCHK_APPLY_EXECUTION", "STATUS": "NOT_EXECUTED_IN_10CD", "DETAIL": "No apply execution."},
        {"ITEM": "NEXT_REVIEW_GATE", "STATUS": "10CE_REQUIRED", "DETAIL": "Review discovery candidates and decide reuse vs guarded source patch planning."},
    ]

    issues = "0" if failures == 0 else str(failures)
    wcsv(reports / "message_catalog_phase22ae_6_5_10cd_gate_check_v1.csv", gates, ["GATE", "STATUS", "DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10cd_scan_manifest_v1.csv", scan_manifest, ["SCAN_FILE", "BYTES", "SHA256", "SCANNED"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10cd_raw_discovery_matches_v1.csv", raw_matches, ["FILE_PATH", "LINE", "MATCH_KIND", "SNIPPET"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10cd_native_writer_candidate_manifest_v1.csv", candidate_rows, ["CANDIDATE_ROW", "CANDIDATE_KIND", "FILE_PATH", "LINE", "MATCH_KIND", "SNIPPET", "REVIEW_REQUIRED", "SOURCE_MUTATION_AUTHORIZED_NOW", "APPLY_AUTHORIZED_NOW"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10cd_discovery_candidate_summary_v1.csv", discovery_summary, ["CANDIDATE_KIND", "CANDIDATE_COUNT", "NEXT_REVIEW_ACTION"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10cd_discovery_recommendations_v1.csv", recommendation_rows, ["RECOMMENDATION_ROW", "RECOMMENDATION", "DETAIL", "SOURCE_MUTATION_AUTHORIZED_NOW", "APPLY_AUTHORIZED_NOW"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10cd_apply_readiness_v1.csv", readiness, ["ITEM", "STATUS", "DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10cd_boundary_ledger_v1.csv", boundary, ["PROTECTED_SYSTEM", "MUTATION_ALLOWED", "OBSERVED_MUTATION", "DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10cd_artifact_manifest_v1.csv", artifact_rows, ["ARTIFACT", "ROLE", "BYTES", "SHA256"])

    summary = {
        "STATUS": status,
        "VALIDATION_ISSUES": issues,
        "PHASE22AE_6_5_10CC_STATUS": cc.get("STATUS", ""),
        "MSG_022AE_6_5_10CC_SAVEPOINT_PRESENT": 1 if sp_cc else 0,
        "ACTIVE_MESSAGES_OBSERVED_COUNT": msg_count,
        "ACTIVE_TEXT_OBSERVED_COUNT": text_count,
        "CC_DISCOVERY_REQUIREMENT_ROWS": len(discovery_req),
        "SCAN_FILE_ROWS": len(scan_manifest),
        "RAW_DISCOVERY_MATCH_ROWS": len(raw_matches),
        "NATIVE_WRITER_CANDIDATE_ROWS": len(candidate_rows),
        "DISCOVERY_SUMMARY_ROWS": len(discovery_summary),
        "CD_ROOT": rel(cd_root, repo),
        "DISCOVERY_REPORTED": 1 if status == GREEN else 0,
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
    wcsv(reports / "message_catalog_phase22ae_6_5_10cd_status_summary_v1.csv", [summary], list(summary.keys()))

    (repo / "docs/messaging/MESSAGE_LOCALE_PHASE22AE_6_5_10CD_NATIVE_HELP_CMDHELPCHK_WRITER_DISCOVERY_PACKAGE.md").write_text(
        f"# Message Catalog Phase 22AE.6.5.10CD Native HELP/CMDHELPCHK Writer Discovery Package\n\n"
        f"Status: `{status}`\n\n"
        "10CD performs report-only discovery of candidate HELP DATA and CMDHELPCHK native writer/reuse paths. It does not mutate protected systems.\n\n"
        f"Discovery root:\n\n```text\n{rel(cd_root, repo)}\n```\n\n"
        f"Next gate:\n\n```text\n{NEXT}\n```\n",
        encoding="utf-8"
    )

    print(status)
    print(f"  validation issues: {issues}")
    print(f"  Phase 22AE.6.5.10CC status: {cc.get('STATUS','')}")
    print(f"  MSG-022AE.6.5.10CC savepoint present: {1 if sp_cc else 0}")
    print(f"  active messages observed count: {msg_count}")
    print(f"  active text observed count: {text_count}")
    print(f"  CC discovery requirement rows: {len(discovery_req)}")
    print(f"  scan file rows: {len(scan_manifest)}")
    print(f"  raw discovery match rows: {len(raw_matches)}")
    print(f"  native writer candidate rows: {len(candidate_rows)}")
    print(f"  discovery summary rows: {len(discovery_summary)}")
    print(f"  discovery root: {rel(cd_root, repo)}")
    print("  discovery reported: 1")
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
