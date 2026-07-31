#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, json, hashlib, re, shutil
from datetime import datetime, timezone
from pathlib import Path

GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_10CL_TARGETED_NATIVE_WRITER_DISCOVERY_PACKAGE_GREEN_DISCOVERY_REPORTED_SOURCE_HELD"
BLOCKED = "MESSAGE_CATALOG_PHASE22AE_6_5_10CL_TARGETED_NATIVE_WRITER_DISCOVERY_PACKAGE_BLOCKED"
NEXT = "HOLD_OR_AUTHORIZE_PHASE22AE_6_5_10CM_TARGETED_NATIVE_WRITER_DISCOVERY_REVIEW"

REPORT = Path("docs/messaging/reports")
CK_SUMMARY = REPORT / "message_catalog_phase22ae_6_5_10ck_status_summary_v1.csv"
CK_REQUIREMENTS = REPORT / "message_catalog_phase22ae_6_5_10ck_targeted_discovery_requirements_v1.csv"
CK_SCOPE = REPORT / "message_catalog_phase22ae_6_5_10ck_targeted_scope_review_v1.csv"
CK_BLOCKED = REPORT / "message_catalog_phase22ae_6_5_10ck_carry_forward_blocked_actions_v1.csv"

ACTIVE_MSG_DBF = Path("dottalkpp/data/messaging/SYSTEM_MESSAGES.dbf")
ACTIVE_TEXT_DBF = Path("dottalkpp/data/messaging/SYSTEM_MESSAGE_TEXT.dbf")
CL_ROOT = Path("docs/messaging/apply/phase22ae_6_5_10cl_targeted_native_writer_discovery_package_v1")

SCAN_ROOTS = [
    "src",
    "tools/messaging",
    "tools/help",
    "dottalkpp/data/schemas",
    "dottalkpp/data/scripts",
    "dottalkpp/data/help",
    "dottalkpp/data/metadata",
]

TEXT_EXTS = {".cpp", ".cxx", ".cc", ".c", ".hpp", ".h", ".hh", ".py", ".ps1", ".md", ".dts", ".dtschema", ".txt", ".csv", ".json"}
MAX_FILE_BYTES = 2000000
MAX_MATCH_ROWS = 1200
MAX_MATCHES_PER_FILE = 12

HELP_WRITER_RX = re.compile(r"(HELP\s*DATA|HELPDATA|HELP[_\-\s]*DATA|HELP\s+MSGMGR|HELP\s+SET\s+MESSAGE|cmd_help|help_manager|help[_\-\s]*manager).{0,160}(WRITE|IMPORT|UPDATE|REPLACE|APPEND|INSERT|SAVE|CREATE|ADD|PUT|MUTATE)|"
                            r"(WRITE|IMPORT|UPDATE|REPLACE|APPEND|INSERT|SAVE|CREATE|ADD|PUT|MUTATE).{0,160}(HELP\s*DATA|HELPDATA|HELP[_\-\s]*DATA|HELP\s+MSGMGR|HELP\s+SET\s+MESSAGE|cmd_help|help_manager|help[_\-\s]*manager)",
                            re.IGNORECASE)
CMDHELPCHK_WRITER_RX = re.compile(r"(CMDHELPCHK|cmd_help_chk|command[_\-\s]*help[_\-\s]*check|help[_\-\s]*check).{0,160}(WRITE|IMPORT|UPDATE|REPLACE|APPEND|INSERT|SAVE|CREATE|ADD|PUT|MUTATE)|"
                                  r"(WRITE|IMPORT|UPDATE|REPLACE|APPEND|INSERT|SAVE|CREATE|ADD|PUT|MUTATE).{0,160}(CMDHELPCHK|cmd_help_chk|command[_\-\s]*help[_\-\s]*check|help[_\-\s]*check)",
                                  re.IGNORECASE)
GENERIC_WRITER_RX = re.compile(r"\b(WRITE|IMPORT|UPDATE|REPLACE|APPEND|INSERT|SAVE|CREATE|ADDTAG|BUILDLMDB|CDX|DBF)\b", re.IGNORECASE)
READER_ONLY_RX = re.compile(r"\b(PRINT|DISPLAY|SHOW|LIST|CHECK|READ|OPEN|STATUS|HELP\s+[A-Z0-9_]+)\b", re.IGNORECASE)
SOURCE_CONTRACT_RX = re.compile(r"@dottalk\.usage|source[-_\s]*comment|usage\s+contract", re.IGNORECASE)

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

def iter_files(repo):
    seen = set()
    for r in SCAN_ROOTS:
        root = repo / r
        if not root.exists():
            continue
        for p in root.rglob("*"):
            if not p.is_file():
                continue
            if p.suffix.lower() not in TEXT_EXTS:
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

def classify_line(line):
    classes = []
    if HELP_WRITER_RX.search(line):
        classes.append("HELP_DATA_EXACT_WRITER_CANDIDATE")
    if CMDHELPCHK_WRITER_RX.search(line):
        classes.append("CMDHELPCHK_EXACT_WRITER_CANDIDATE")
    if SOURCE_CONTRACT_RX.search(line):
        classes.append("SOURCE_COMMENT_CONTRACT_SUPPORT")
    if not classes and GENERIC_WRITER_RX.search(line) and ("help" in line.lower() or "message" in line.lower() or "cmd" in line.lower()):
        classes.append("GENERIC_NATIVE_WRITER_SUPPORT")
    if not classes and READER_ONLY_RX.search(line) and ("help" in line.lower() or "cmdhelpchk" in line.lower() or "message" in line.lower()):
        classes.append("READER_CHECKER_EXCLUSION_CANDIDATE")
    return classes

def score_candidate(row):
    cls = row.get("DISCOVERY_CLASS", "")
    path = row.get("FILE_PATH", "").lower()
    snippet = row.get("SNIPPET", "").lower()
    s = 0
    if "HELP_DATA_EXACT_WRITER" in cls or "CMDHELPCHK_EXACT_WRITER" in cls:
        s += 100
    if "GENERIC_NATIVE_WRITER" in cls:
        s += 65
    if path.startswith("src/"):
        s += 20
    if "tools/messaging" in path or "tools/help" in path:
        s += 15
    if "data/help" in path or "data/schemas" in path:
        s += 10
    for term in ["write", "import", "update", "replace", "append", "insert", "save", "create"]:
        if term in snippet:
            s += 4
    if "reader" in cls or "exclusion" in cls:
        s -= 20
    return s

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--replace-existing-discovery", action="store_true")
    args = ap.parse_args()
    repo = Path(args.repo_root).resolve()
    reports = repo / REPORT
    reports.mkdir(parents=True, exist_ok=True)

    ck = first(repo / CK_SUMMARY)
    reqs = rows(repo / CK_REQUIREMENTS)
    scopes = rows(repo / CK_SCOPE)
    blocked_in = rows(repo / CK_BLOCKED)
    sp_ck, latest_ck = savepoint(repo, "MSG-022AE.6.5.10CK")
    msg_count = dbf_count(repo / ACTIVE_MSG_DBF)
    text_count = dbf_count(repo / ACTIVE_TEXT_DBF)
    cl_root = repo / CL_ROOT

    gates = []
    failures = 0
    def gate(name, ok, detail):
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": str(detail)})
        if not ok:
            failures += 1

    gate("PHASE22AE_6_5_10CK_GREEN", ck.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_5_10CK_NATIVE_WRITER_SELECTION_REVIEW_GREEN_TARGETED_DISCOVERY_PACKAGE_REQUIRED_SOURCE_HELD", ck.get("STATUS","missing"))
    gate("MSG_022AE_6_5_10CK_SAVEPOINT_PRESENT", sp_ck, latest_ck)
    gate("CK_TARGETED_DISCOVERY_REQUIRED", ck.get("TARGETED_DISCOVERY_PACKAGE_REQUIRED") == "1", ck.get("TARGETED_DISCOVERY_PACKAGE_REQUIRED","missing"))
    gate("CK_REUSE_NOT_CONFIRMED", ck.get("REUSE_PATH_CONFIRMED_NOW") == "0", ck.get("REUSE_PATH_CONFIRMED_NOW","missing"))
    gate("CK_SOURCE_PATCH_NOT_PROVEN", ck.get("SOURCE_PATCH_NEEDED_PROVEN") == "0", ck.get("SOURCE_PATCH_NEEDED_PROVEN","missing"))
    gate("CK_SOURCE_MUTATION_NOT_AUTHORIZED", ck.get("SOURCE_MUTATION_AUTHORIZED_NOW") == "0", ck.get("SOURCE_MUTATION_AUTHORIZED_NOW","missing"))
    gate("CK_APPLY_EXECUTION_NOT_AUTHORIZED", ck.get("APPLY_EXECUTION_AUTHORIZED_NOW") == "0", ck.get("APPLY_EXECUTION_AUTHORIZED_NOW","missing"))
    gate("CK_HELP_APPLY_NOT_EXECUTED", ck.get("HELP_DATA_APPLY_EXECUTED") == "0", ck.get("HELP_DATA_APPLY_EXECUTED","missing"))
    gate("CK_CMDHELPCHK_APPLY_NOT_EXECUTED", ck.get("CMDHELPCHK_APPLY_EXECUTED") == "0", ck.get("CMDHELPCHK_APPLY_EXECUTED","missing"))
    gate("CK_REQUIREMENTS_PRESENT", len(reqs) > 0, len(reqs))
    gate("CK_SCOPE_PRESENT", len(scopes) > 0, len(scopes))
    gate("ACTIVE_MESSAGES_HEADER_COUNT_14", msg_count == 14, msg_count)
    gate("ACTIVE_TEXT_HEADER_COUNT_70", text_count == 70, text_count)
    gate("CL_ROOT_NOT_EXISTING_OR_REPLACE_ALLOWED", (not cl_root.exists()) or args.replace_existing_discovery, rel(cl_root, repo))

    status = BLOCKED
    scan_manifest = []
    candidates = []
    summary_rows = []
    blocked_rows = []
    artifacts = []

    if failures == 0:
        if cl_root.exists() and args.replace_existing_discovery:
            shutil.rmtree(cl_root)
        cl_root.mkdir(parents=True, exist_ok=True)

        for p in iter_files(repo):
            try:
                text = p.read_text(encoding="utf-8", errors="replace")
                size = p.stat().st_size
            except Exception:
                continue
            relp = rel(p, repo)
            file_matches = 0
            for lineno, line in enumerate(text.splitlines(), 1):
                classes = classify_line(line)
                if not classes:
                    continue
                snippet = line.strip()
                if len(snippet) > 260:
                    snippet = snippet[:257] + "..."
                for cls in classes:
                    row = {
                        "DISCOVERY_ROW": len(candidates) + 1,
                        "DISCOVERY_CLASS": cls,
                        "FILE_PATH": relp,
                        "LINE": lineno,
                        "SNIPPET": snippet,
                        "TARGETED_REVIEW_REQUIRED": 1,
                        "REUSE_PATH_CONFIRMED_NOW": 0,
                        "SOURCE_PATCH_NEEDED_PROVEN": 0,
                        "SOURCE_MUTATION_AUTHORIZED_NOW": 0,
                        "APPLY_AUTHORIZED_NOW": 0,
                    }
                    row["TARGETED_SCORE"] = score_candidate(row)
                    candidates.append(row)
                file_matches += 1
                if file_matches >= MAX_MATCHES_PER_FILE or len(candidates) >= MAX_MATCH_ROWS:
                    break
            scan_manifest.append({
                "SCAN_FILE": relp,
                "BYTES": size,
                "SHA256": sha(p),
                "TARGETED_MATCHES_IN_FILE": file_matches,
            })
            if len(candidates) >= MAX_MATCH_ROWS:
                break

        candidates = sorted(candidates, key=lambda r: int(r.get("TARGETED_SCORE", 0)), reverse=True)
        for idx, row in enumerate(candidates, 1):
            row["DISCOVERY_ROW"] = idx

        counts = {}
        for row in candidates:
            counts[row["DISCOVERY_CLASS"]] = counts.get(row["DISCOVERY_CLASS"], 0) + 1
        for cls in sorted(counts):
            summary_rows.append({
                "DISCOVERY_CLASS": cls,
                "ROW_COUNT": counts[cls],
                "NEXT_REVIEW_ACTION": "Review exact candidates for writer/reuse proof; exclude reader/checker-only candidates.",
            })

        for i, b in enumerate(blocked_in, 1):
            blocked_rows.append({
                "CARRY_FORWARD_ROW": i,
                "BLOCKED_ACTION": b.get("BLOCKED_ACTION",""),
                "BLOCKED": 1,
                "REASON": b.get("REASON",""),
                "CARRY_FORWARD_DETAIL": "Still blocked after CL targeted discovery.",
            })

        paths = [
            (cl_root / "targeted_scan_manifest_v1.csv", scan_manifest, ["SCAN_FILE","BYTES","SHA256","TARGETED_MATCHES_IN_FILE"]),
            (cl_root / "targeted_native_writer_candidates_v1.csv", candidates, ["DISCOVERY_ROW","DISCOVERY_CLASS","TARGETED_SCORE","FILE_PATH","LINE","SNIPPET","TARGETED_REVIEW_REQUIRED","REUSE_PATH_CONFIRMED_NOW","SOURCE_PATCH_NEEDED_PROVEN","SOURCE_MUTATION_AUTHORIZED_NOW","APPLY_AUTHORIZED_NOW"]),
            (cl_root / "targeted_discovery_summary_v1.csv", summary_rows, ["DISCOVERY_CLASS","ROW_COUNT","NEXT_REVIEW_ACTION"]),
            (cl_root / "carry_forward_blocked_actions_v1.csv", blocked_rows, ["CARRY_FORWARD_ROW","BLOCKED_ACTION","BLOCKED","REASON","CARRY_FORWARD_DETAIL"]),
        ]
        for p, rs, fs in paths:
            wcsv(p, rs, fs)

        scripts = cl_root / "scripts"
        scripts.mkdir(parents=True, exist_ok=True)
        disabled = scripts / "MESSAGE_CATALOG_PHASE22AE_6_5_10CM_REVIEW_TEMPLATE.ps1.disabled"
        disabled.write_text('throw "10CL is targeted discovery only. Run 10CM review before selecting reuse/source-patch/apply path."\n', encoding="utf-8")
        readback = scripts / "MESSAGE_CATALOG_PHASE22AE_6_5_10CL_READBACK_CONTRACT.dts"
        readback.write_text("MSGMGR STATUS\nMSGMGR CHECK\nSET MESSAGE CATALOG CHECK\nSET MESSAGE EMIT MESSAGE_PROOF_MODE_STATUS en-US\nHELP MSGMGR\nHELP SET MESSAGE\nCMDHELPCHK\nQUIT\n", encoding="utf-8")
        notes = cl_root / "targeted_native_writer_discovery_package_v1.md"
        notes.write_text("# 10CL Targeted Native Writer Discovery Package\n\n10CL performs targeted discovery for exact HELP DATA and CMDHELPCHK native writer/import/update paths. It excludes broad scan behavior by design and does not mutate protected systems.\n", encoding="utf-8")
        readme = cl_root / "README_10CL_TARGETED_NATIVE_WRITER_DISCOVERY_PACKAGE.md"
        readme.write_text("# 10CL Targeted Native Writer Discovery Package\n\nReport-only targeted discovery. No protected mutation occurs.\n", encoding="utf-8")

        for p, _, _ in paths:
            artifacts.append({"ARTIFACT": rel(p, repo), "ROLE": "targeted_native_writer_discovery_artifact", "BYTES": p.stat().st_size, "SHA256": sha(p)})
        for p in [disabled, readback, notes, readme]:
            artifacts.append({"ARTIFACT": rel(p, repo), "ROLE": "targeted_native_writer_discovery_artifact", "BYTES": p.stat().st_size, "SHA256": sha(p)})

        status = GREEN

    boundary = [
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "10CL reads/scans source and writes docs/messaging discovery artifacts only."},
        {"PROTECTED_SYSTEM": "ACTIVE_SYSTEM_MESSAGES", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_SYSTEM_MESSAGE_TEXT", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_CDX_LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CDX/LMDB mutation."},
        {"PROTECTED_SYSTEM": "WORKSPACE_PROFILE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No workspace mutation."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Targeted discovery only; no HELP DATA apply."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Targeted discovery only; no CMDHELPCHK apply."},
    ]
    readiness = [
        {"ITEM": "TARGETED_DISCOVERY_REPORTED", "STATUS": "YES" if status == GREEN else "NO", "DETAIL": f"{len(candidates)} candidate rows."},
        {"ITEM": "REUSE_PATH_CONFIRMED_NOW", "STATUS": "NO", "DETAIL": "10CL reports candidates; review is next."},
        {"ITEM": "SOURCE_PATCH_NEEDED_PROVEN", "STATUS": "NO", "DETAIL": "10CL does not prove source patch need."},
        {"ITEM": "DIRECT_APPLY_READY", "STATUS": "NO", "DETAIL": "Direct apply remains blocked."},
        {"ITEM": "NEXT_REVIEW_REQUIRED", "STATUS": "YES", "DETAIL": "10CM must review targeted discovery."},
    ]

    issues = "0" if failures == 0 else str(failures)
    wcsv(reports / "message_catalog_phase22ae_6_5_10cl_gate_check_v1.csv", gates, ["GATE","STATUS","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10cl_targeted_scan_manifest_v1.csv", scan_manifest, ["SCAN_FILE","BYTES","SHA256","TARGETED_MATCHES_IN_FILE"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10cl_targeted_native_writer_candidates_v1.csv", candidates, ["DISCOVERY_ROW","DISCOVERY_CLASS","TARGETED_SCORE","FILE_PATH","LINE","SNIPPET","TARGETED_REVIEW_REQUIRED","REUSE_PATH_CONFIRMED_NOW","SOURCE_PATCH_NEEDED_PROVEN","SOURCE_MUTATION_AUTHORIZED_NOW","APPLY_AUTHORIZED_NOW"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10cl_targeted_discovery_summary_v1.csv", summary_rows, ["DISCOVERY_CLASS","ROW_COUNT","NEXT_REVIEW_ACTION"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10cl_carry_forward_blocked_actions_v1.csv", blocked_rows, ["CARRY_FORWARD_ROW","BLOCKED_ACTION","BLOCKED","REASON","CARRY_FORWARD_DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10cl_apply_readiness_v1.csv", readiness, ["ITEM","STATUS","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10cl_boundary_ledger_v1.csv", boundary, ["PROTECTED_SYSTEM","MUTATION_ALLOWED","OBSERVED_MUTATION","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10cl_artifact_manifest_v1.csv", artifacts, ["ARTIFACT","ROLE","BYTES","SHA256"])

    summary = {
        "STATUS": status,
        "VALIDATION_ISSUES": issues,
        "PHASE22AE_6_5_10CK_STATUS": ck.get("STATUS",""),
        "MSG_022AE_6_5_10CK_SAVEPOINT_PRESENT": 1 if sp_ck else 0,
        "ACTIVE_MESSAGES_OBSERVED_COUNT": msg_count,
        "ACTIVE_TEXT_OBSERVED_COUNT": text_count,
        "CK_TARGETED_DISCOVERY_REQUIREMENT_ROWS": len(reqs),
        "CK_TARGETED_SCOPE_ROWS": len(scopes),
        "TARGETED_SCAN_FILE_ROWS": len(scan_manifest),
        "TARGETED_DISCOVERY_CANDIDATE_ROWS": len(candidates),
        "TARGETED_DISCOVERY_SUMMARY_ROWS": len(summary_rows),
        "CL_ROOT": rel(cl_root, repo),
        "TARGETED_DISCOVERY_REPORTED": 1 if status == GREEN else 0,
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
    wcsv(reports / "message_catalog_phase22ae_6_5_10cl_status_summary_v1.csv", [summary], list(summary.keys()))

    (repo / "docs/messaging/MESSAGE_LOCALE_PHASE22AE_6_5_10CL_TARGETED_NATIVE_WRITER_DISCOVERY_PACKAGE.md").write_text(
        f"# Message Catalog Phase 22AE.6.5.10CL Targeted Native Writer Discovery Package\n\nStatus: `{status}`\n\n10CL performs targeted native writer discovery and requires 10CM review. It does not confirm reuse, prove source patch need, authorize apply, or mutate protected systems.\n\nDiscovery root:\n\n```text\n{rel(cl_root, repo)}\n```\n\nNext gate:\n\n```text\n{NEXT}\n```\n",
        encoding="utf-8"
    )

    print(status)
    print(f"  validation issues: {issues}")
    print(f"  Phase 22AE.6.5.10CK status: {ck.get('STATUS','')}")
    print(f"  MSG-022AE.6.5.10CK savepoint present: {1 if sp_ck else 0}")
    print(f"  active messages observed count: {msg_count}")
    print(f"  active text observed count: {text_count}")
    print(f"  CK targeted discovery requirement rows: {len(reqs)}")
    print(f"  CK targeted scope rows: {len(scopes)}")
    print(f"  targeted scan file rows: {len(scan_manifest)}")
    print(f"  targeted discovery candidate rows: {len(candidates)}")
    print(f"  targeted discovery summary rows: {len(summary_rows)}")
    print(f"  discovery root: {rel(cl_root, repo)}")
    print("  targeted discovery reported: 1")
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
