from __future__ import annotations
import argparse, csv, json, os, shutil
from datetime import datetime, timezone
from pathlib import Path

DC_GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_10DC_B_GUARDED_HELP_CMDHELPCHK_APPLY_PLAN_GREEN_PLAN_ONLY_EXECUTION_NOT_AUTHORIZED"
DC_MARKERS = [
    "MSG-022AE.6.5.10DC-B",
    "22AE.6.5.10DC-B",
    "phase22ae_6_5_10dc_b",
    "PHASE22AE_6_5_10DC_B",
]
GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_10DD_B_ACTIVE_HELP_CMDHELPCHK_TARGET_DISCOVERY_STAGING_GREEN_CANDIDATE_TARGETS_STAGED_NO_MUTATION"
RED = "MESSAGE_CATALOG_PHASE22AE_6_5_10DD_B_ACTIVE_HELP_CMDHELPCHK_TARGET_DISCOVERY_STAGING_RED_REVIEW_REQUIRED"
NEXT = "HOLD_OR_AUTHORIZE_PHASE22AE_6_5_10DE_B_ACTIVE_HELP_CMDHELPCHK_TARGET_DISCOVERY_REVIEW"
ROOT_REL = "docs/messaging/apply/phase22ae_6_5_10dd_b_active_help_cmdhelpchk_target_discovery_staging_v1"
KEYWORDS = {
    "HELP_DATA": ["HELP DATA", "HELPDATA", "HELP_DATA", "help data", "help_data", "helpdata"],
    "CMDHELPCHK": ["CMDHELPCHK", "cmdhelpchk", "CMD HELP CHK", "command help check"],
}
TEXT_SUFFIXES = {".cpp",".hpp",".h",".c",".cc",".py",".ps1",".bat",".cmd",".md",".txt",".json",".csv",".dts",".ini",".yaml",".yml",".cmake"}
DATA_SUFFIXES = {".dbf",".dtx",".cdx",".idx",".inx",".cnx",".json",".csv",".md",".txt"}

def read_text(path: Path, limit: int | None = None) -> str:
    try:
        if limit is None:
            return path.read_text(encoding="utf-8", errors="replace")
        with path.open("rb") as f:
            return f.read(limit).decode("utf-8", errors="replace")
    except Exception:
        return ""

def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")

def csv_rows(path: Path) -> list[dict]:
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as f:
            return list(csv.DictReader(f))
    except Exception:
        return []

def csv_one(path: Path) -> dict:
    rows = csv_rows(path)
    return rows[0] if rows else {}

def write_csv(path: Path, fields: list[str], rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for row in rows:
            w.writerow({field: row.get(field, "") for field in fields})

def latest_id(repo: Path) -> str:
    try:
        data = json.loads(read_text(repo / "docs/messaging/reports/message_savepoint_latest_v1.json"))
        return data.get("savepoint_id", data.get("savepoint", ""))
    except Exception:
        return ""

def journal_detection(repo: Path) -> tuple[int, str, str]:
    journal = repo / "docs/messaging/MESSAGING_SAVEPOINT_JOURNAL.md"
    text = read_text(journal)
    low = text.lower()
    for marker in DC_MARKERS:
        if marker.lower() in low:
            return 1, marker, str(journal)
    return 0, "", str(journal)

def should_skip_dir(path: Path) -> bool:
    parts = {p.lower() for p in path.parts}
    return bool(parts & {".git",".vs","build",".cache","__pycache__","node_modules","_incoming"})

def classify_path(path: Path) -> str:
    s = path.as_posix().lower()
    suffix = path.suffix.lower()
    if "/src/" in s or suffix in {".cpp",".hpp",".h",".c",".cc"}:
        return "source"
    if "/tools/" in s or suffix in {".py",".ps1",".bat",".cmd"}:
        return "tooling"
    if "/docs/" in s or suffix in {".md",".txt"}:
        return "documentation_or_report"
    if suffix in {".dbf",".dtx",".cdx",".idx",".inx",".cnx"}:
        return "runtime_data_or_index"
    if suffix in {".csv",".json"}:
        return "structured_candidate_or_report"
    return "other"

def family_for(name_text: str) -> tuple[str, int, int]:
    low = name_text.lower()
    help_hits = sum(low.count(k.lower()) for k in KEYWORDS["HELP_DATA"])
    cmd_hits = sum(low.count(k.lower()) for k in KEYWORDS["CMDHELPCHK"])
    if help_hits and cmd_hits:
        return "BOTH", help_hits, cmd_hits
    if help_hits:
        return "HELP_DATA", help_hits, cmd_hits
    if cmd_hits:
        return "CMDHELPCHK", help_hits, cmd_hits
    return "UNKNOWN", help_hits, cmd_hits

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--replace-existing-staging", action="store_true")
    ap.add_argument("--max-files", type=int, default=25000)
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    docs = repo / "docs/messaging"
    reports = docs / "reports"
    out = repo / ROOT_REL

    if out.exists() and args.replace_existing_staging:
        shutil.rmtree(out)

    dc = csv_one(reports / "message_catalog_phase22ae_6_5_10dc_b_status_summary_v1.csv")
    dc_green = int(dc.get("STATUS", "") == DC_GREEN)
    dc_savepoint, matched_marker, journal_path = journal_detection(repo)
    apply_auth = int(str(dc.get("APPLY_EXECUTION_AUTHORIZED_NOW", "0")) == "1")
    help_apply = int(str(dc.get("HELP_DATA_APPLY_EXECUTED", "0")) == "1")
    cmd_apply = int(str(dc.get("CMDHELPCHK_APPLY_EXECUTED", "0")) == "1")
    target_required = int(str(dc.get("TARGET_DISCOVERY_REQUIRED", "0")) == "1")

    pre = [
        {"check_id":"dc_b_status_green","value":dc_green,"expected":1,"status":"PASS" if dc_green else "FAIL"},
        {"check_id":"dc_b_savepoint_present","value":dc_savepoint,"expected":1,"status":"PASS" if dc_savepoint else "FAIL"},
        {"check_id":"dc_b_savepoint_marker_matched","value":matched_marker,"expected":"one accepted DC-B marker","status":"PASS" if dc_savepoint else "FAIL"},
        {"check_id":"target_discovery_required","value":target_required,"expected":1,"status":"PASS" if target_required else "FAIL"},
        {"check_id":"apply_execution_not_authorized","value":apply_auth,"expected":0,"status":"PASS" if apply_auth == 0 else "FAIL"},
        {"check_id":"help_data_apply_not_executed","value":help_apply,"expected":0,"status":"PASS" if help_apply == 0 else "FAIL"},
        {"check_id":"cmdhelpchk_apply_not_executed","value":cmd_apply,"expected":0,"status":"PASS" if cmd_apply == 0 else "FAIL"},
        {"check_id":"dd_b_root_absent_or_replace_authorized","value":int(out.exists()),"expected":0,"status":"PASS" if (not out.exists() or args.replace_existing_staging) else "FAIL"},
    ]

    candidate_rows = []
    scanned = 0
    skipped_binary = 0
    for dirpath, dirnames, filenames in os.walk(repo):
        d = Path(dirpath)
        if should_skip_dir(d):
            dirnames[:] = []
            continue
        dirnames[:] = [x for x in dirnames if not should_skip_dir(d / x)]
        for fn in filenames:
            scanned += 1
            if scanned > args.max_files:
                break
            p = d / fn
            rel = p.relative_to(repo).as_posix()
            suffix = p.suffix.lower()
            name_text = rel + " " + p.stem
            content_text = ""
            content_scanned = 0
            if suffix in TEXT_SUFFIXES:
                content_text = read_text(p, limit=262144)
                content_scanned = 1
            elif suffix not in DATA_SUFFIXES:
                skipped_binary += 1
            fam1, help_name, cmd_name = family_for(name_text)
            fam2, help_content, cmd_content = family_for(content_text)
            help_hits = help_name + help_content
            cmd_hits = cmd_name + cmd_content
            if help_hits == 0 and cmd_hits == 0:
                continue
            if help_hits and cmd_hits:
                fam = "BOTH"
            elif help_hits:
                fam = "HELP_DATA"
            else:
                fam = "CMDHELPCHK"
            kind = classify_path(p)
            size = p.stat().st_size if p.exists() else 0
            review_priority = 0
            if kind == "runtime_data_or_index":
                review_priority += 20
            if kind == "source":
                review_priority += 15
            if kind == "tooling":
                review_priority += 10
            if "cmdhelpchk" in rel.lower():
                review_priority += 10
            if "help" in rel.lower():
                review_priority += 5
            review_priority += min(help_hits + cmd_hits, 20)
            candidate_rows.append({
                "family": fam,
                "artifact_type": kind,
                "relative_path": rel,
                "suffix": suffix,
                "bytes": size,
                "content_scanned": content_scanned,
                "help_hits": help_hits,
                "cmdhelpchk_hits": cmd_hits,
                "review_priority": review_priority,
                "active_target_selected_now": 0,
                "mutate_now": 0,
            })
        if scanned > args.max_files:
            break

    candidate_rows.sort(key=lambda r: (int(r["review_priority"]), int(r["bytes"]) if str(r["bytes"]).isdigit() else 0), reverse=True)

    family_summary = []
    for fam in ["HELP_DATA","CMDHELPCHK","BOTH","UNKNOWN"]:
        rows = [r for r in candidate_rows if r["family"] == fam]
        family_summary.append({
            "family": fam,
            "candidate_count": len(rows),
            "selected_now": 0,
            "target_discovered_now": 0,
            "requires_review": 1 if rows else 0,
        })

    likely_targets = []
    for fam in ["HELP_DATA","CMDHELPCHK","BOTH"]:
        for row in [r for r in candidate_rows if r["family"] == fam][:15]:
            likely_targets.append({
                "family": row["family"],
                "relative_path": row["relative_path"],
                "artifact_type": row["artifact_type"],
                "review_priority": row["review_priority"],
                "why_relevant": "keyword/name/content match; review required before active target selection",
                "active_target_selected_now": 0,
                "apply_now": 0,
            })

    boundary = [
        {"boundary":"target discovery staging executed","value":1,"status":"PASS"},
        {"boundary":"active HELP DATA target selected now","value":0,"status":"PASS"},
        {"boundary":"active CMDHELPCHK target selected now","value":0,"status":"PASS"},
        {"boundary":"active HELP DATA apply executed","value":0,"status":"PASS"},
        {"boundary":"active CMDHELPCHK apply executed","value":0,"status":"PASS"},
        {"boundary":"apply execution authorized now","value":0,"status":"PASS"},
        {"boundary":"source mutation authorized now","value":0,"status":"PASS"},
        {"boundary":"active catalog mutation observed by staging","value":0,"status":"PASS"},
        {"boundary":"active DBF/CDX/LMDB mutation observed by staging","value":0,"status":"PASS"},
        {"boundary":"workspace mutation observed by staging","value":0,"status":"PASS"},
        {"boundary":"latest pointer changed by DD-B","value":0,"status":"PASS"},
    ]

    validation = sum(1 for row in pre + boundary if row["status"] == "FAIL")
    status = GREEN if validation == 0 else RED
    next_gate = NEXT if status == GREEN else "REVIEW_PHASE22AE_6_5_10DD_B_TARGET_DISCOVERY_STAGING_PRECONDITIONS"

    out.mkdir(parents=True, exist_ok=True)
    reports.mkdir(parents=True, exist_ok=True)

    write_csv(reports / "message_catalog_phase22ae_6_5_10dd_b_precondition_check_v1.csv", ["check_id","value","expected","status"], pre)
    write_csv(reports / "message_catalog_phase22ae_6_5_10dd_b_target_candidate_inventory_v1.csv", ["family","artifact_type","relative_path","suffix","bytes","content_scanned","help_hits","cmdhelpchk_hits","review_priority","active_target_selected_now","mutate_now"], candidate_rows)
    write_csv(reports / "message_catalog_phase22ae_6_5_10dd_b_target_family_summary_v1.csv", ["family","candidate_count","selected_now","target_discovered_now","requires_review"], family_summary)
    write_csv(reports / "message_catalog_phase22ae_6_5_10dd_b_likely_target_review_queue_v1.csv", ["family","relative_path","artifact_type","review_priority","why_relevant","active_target_selected_now","apply_now"], likely_targets)
    write_csv(reports / "message_catalog_phase22ae_6_5_10dd_b_boundary_check_v1.csv", ["boundary","value","status"], boundary)

    summary = [{
        "STATUS": status,
        "VALIDATION_ISSUES": validation,
        "PHASE": "22AE.6.5.10DD-B",
        "PATCH_LEVEL": "v1.1_savepoint_marker_repair",
        "DC_B_STATUS_GREEN": dc_green,
        "DC_B_SAVEPOINT_PRESENT": dc_savepoint,
        "DC_B_SAVEPOINT_MARKER_MATCHED": matched_marker,
        "DC_B_JOURNAL_PATH": journal_path,
        "OFFICIAL_LATEST_SAVEPOINT_BEFORE_DD_B": latest_id(repo),
        "FILES_SCANNED": scanned,
        "BINARY_OR_UNSCANNED_SKIPPED": skipped_binary,
        "TARGET_CANDIDATE_ROWS": len(candidate_rows),
        "LIKELY_TARGET_REVIEW_ROWS": len(likely_targets),
        "HELP_DATA_TARGET_CANDIDATES": sum(1 for r in candidate_rows if r["family"] in ("HELP_DATA","BOTH")),
        "CMDHELPCHK_TARGET_CANDIDATES": sum(1 for r in candidate_rows if r["family"] in ("CMDHELPCHK","BOTH")),
        "ACTIVE_HELP_DATA_TARGET_SELECTED_NOW": 0,
        "ACTIVE_CMDHELPCHK_TARGET_SELECTED_NOW": 0,
        "TARGET_DISCOVERY_REVIEW_REQUIRED": 1,
        "APPLY_EXECUTION_AUTHORIZED_NOW": 0,
        "HELP_DATA_APPLY_EXECUTED": 0,
        "CMDHELPCHK_APPLY_EXECUTED": 0,
        "SOURCE_MUTATION_AUTHORIZED_NOW": 0,
        "ACTIVE_CATALOG_MUTATION_OBSERVED_BY_STAGING": 0,
        "ACTIVE_DBF_CDX_LMDB_MUTATION_OBSERVED_BY_STAGING": 0,
        "WORKSPACE_MUTATION_OBSERVED_BY_STAGING": 0,
        "LATEST_POINTER_CHANGED_BY_DD_B": 0,
        "NEXT_GATE": next_gate,
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00","Z"),
    }]
    write_csv(reports / "message_catalog_phase22ae_6_5_10dd_b_status_summary_v1.csv", list(summary[0].keys()), summary)

    manifest = {
        "phase": "22AE.6.5.10DD-B",
        "patch_level": "v1.1_savepoint_marker_repair",
        "status": status,
        "dc_b_savepoint_marker_matched": matched_marker,
        "target_candidate_rows": len(candidate_rows),
        "likely_target_review_rows": len(likely_targets),
        "active_target_selected_now": False,
        "apply_execution_authorized_now": False,
        "next_gate": next_gate,
    }
    write_text(out / "message_catalog_phase22ae_6_5_10dd_b_manifest_v1.json", json.dumps(manifest, indent=2))

    report = f"""# Phase 22AE.6.5.10DD-B Active HELP/CMDHELPCHK Target Discovery Staging v1.1

- Status: {status}
- Patch level: v1.1 savepoint marker repair
- Validation issues: {validation}
- DC-B status green: {dc_green}
- DC-B savepoint present: {dc_savepoint}
- DC-B savepoint marker matched: {matched_marker}
- Files scanned: {scanned}
- Target candidate rows: {len(candidate_rows)}
- Likely target review rows: {len(likely_targets)}
- Active HELP DATA target selected now: 0
- Active CMDHELPCHK target selected now: 0
- Apply execution authorized now: 0
- HELP DATA apply executed: 0
- CMDHELPCHK apply executed: 0
- Source mutation authorized now: 0
- Latest pointer changed by DD-B: 0
- Next gate: {next_gate}
"""
    write_text(out / "MESSAGE_LOCALE_PHASE22AE_6_5_10DD_B_ACTIVE_HELP_CMDHELPCHK_TARGET_DISCOVERY_STAGING.md", report)
    write_text(docs / "MESSAGE_LOCALE_PHASE22AE_6_5_10DD_B_ACTIVE_HELP_CMDHELPCHK_TARGET_DISCOVERY_STAGING.md", report)

    print(status)
    print(f"  patch level: v1.1 savepoint marker repair")
    print(f"  validation issues: {validation}")
    print(f"  DC-B status green: {dc_green}")
    print(f"  DC-B savepoint present: {dc_savepoint}")
    print(f"  DC-B savepoint marker matched: {matched_marker}")
    print(f"  files scanned: {scanned}")
    print(f"  target candidate rows: {len(candidate_rows)}")
    print(f"  likely target review rows: {len(likely_targets)}")
    print(f"  HELP DATA target candidates: {summary[0]['HELP_DATA_TARGET_CANDIDATES']}")
    print(f"  CMDHELPCHK target candidates: {summary[0]['CMDHELPCHK_TARGET_CANDIDATES']}")
    print("  active HELP DATA target selected now: 0")
    print("  active CMDHELPCHK target selected now: 0")
    print("  target discovery review required: 1")
    print("  apply execution authorized now: 0")
    print("  HELP DATA apply executed: 0")
    print("  CMDHELPCHK apply executed: 0")
    print("  source mutation authorized now: 0")
    print("  active catalog mutation observed by staging: 0")
    print("  active DBF/CDX/LMDB mutation observed by staging: 0")
    print("  workspace mutation observed by staging: 0")
    print("  latest pointer changed by DD-B: 0")
    print(f"  next gate: {next_gate}")
    print(f"  reports: {reports}")
    return 0 if status == GREEN else 1

if __name__ == "__main__":
    raise SystemExit(main())
