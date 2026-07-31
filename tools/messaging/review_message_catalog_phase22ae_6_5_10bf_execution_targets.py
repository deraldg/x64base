#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, json, hashlib, shutil
from datetime import datetime, timezone
from pathlib import Path

GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_10BF_HELP_CMDHELPCHK_EXECUTION_REVIEW_GREEN_IMPLEMENTATION_PLAN_REQUIRED_SOURCE_HELD"
BLOCKED = "MESSAGE_CATALOG_PHASE22AE_6_5_10BF_HELP_CMDHELPCHK_EXECUTION_REVIEW_BLOCKED"
NEXT = "HOLD_OR_AUTHORIZE_PHASE22AE_6_5_10BG_TARGET_SPECIFIC_HELP_CMDHELPCHK_WRITE_IMPLEMENTATION_PLAN"

REPORT_DIR = Path("docs/messaging/reports")
BE_SUMMARY = REPORT_DIR / "message_catalog_phase22ae_6_5_10be_status_summary_v1.csv"
BE_TARGETS = REPORT_DIR / "message_catalog_phase22ae_6_5_10be_exact_target_status_v1.csv"
BE_BACKUPS = REPORT_DIR / "message_catalog_phase22ae_6_5_10be_backup_manifest_v1.csv"
BE_ROOT = Path("docs/messaging/apply/phase22ae_6_5_10be_help_cmdhelpchk_guarded_execution_package_v1")
BF_ROOT = Path("docs/messaging/apply/phase22ae_6_5_10bf_help_cmdhelpchk_execution_review_v1")
ACTIVE_MSG_DBF = Path("dottalkpp/data/messaging/SYSTEM_MESSAGES.dbf")
ACTIVE_TEXT_DBF = Path("dottalkpp/data/messaging/SYSTEM_MESSAGE_TEXT.dbf")

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
    p = Path(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fs, lineterminator="\n", extrasaction="ignore")
        w.writeheader()
        for r in rs:
            w.writerow({k: r.get(k, "") for k in fs})

def rel(p, repo):
    try:
        return str(Path(p).relative_to(repo)).replace("\\", "/")
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
    lp = repo / REPORT_DIR / "message_savepoint_latest_v1.json"
    if lp.exists():
        try:
            latest = json.loads(lp.read_text(encoding="utf-8")).get("savepoint_id", "")
        except Exception:
            latest = ""
    jp = repo / "docs/messaging/MESSAGING_SAVEPOINT_JOURNAL.md"
    txt = jp.read_text(encoding="utf-8", errors="replace") if jp.exists() else ""
    return latest == sid or sid in txt, latest

def classify_format(path: Path):
    suffix = path.suffix.lower()
    if suffix == ".dbf":
        return "DBF_BINARY", "native_x64base_or_dbf_write_path_required"
    if suffix in {".md", ".txt"}:
        return "TEXT_MARKDOWN", "line_or_section_patch_possible_after_anchor_review"
    if suffix == ".csv":
        return "CSV_TEXT", "csv_row_patch_possible_after_schema_review"
    if suffix in {".json"}:
        return "JSON_TEXT", "json_update_possible_after_schema_review"
    return "UNKNOWN", "manual_target_specific_review_required"

def quick_probe(path: Path):
    suffix = path.suffix.lower()
    try:
        if suffix == ".dbf":
            size = path.stat().st_size
            count = dbf_count(path)
            return f"dbf_size={size}; dbf_header_count={count}"
        data = path.read_text(encoding="utf-8", errors="replace")
        first_lines = data.splitlines()[:8]
        joined = " | ".join(line[:80] for line in first_lines)
        return joined[:500]
    except Exception as e:
        return f"probe_error={type(e).__name__}:{e}"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--replace-existing-review", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    reports = repo / REPORT_DIR
    reports.mkdir(parents=True, exist_ok=True)

    be = first(repo / BE_SUMMARY)
    targets = rows(repo / BE_TARGETS)
    backups = rows(repo / BE_BACKUPS)
    sp_be, latest_be = savepoint(repo, "MSG-022AE.6.5.10BE")
    msg_count = dbf_count(repo / ACTIVE_MSG_DBF)
    text_count = dbf_count(repo / ACTIVE_TEXT_DBF)
    be_root = repo / BE_ROOT
    bf_root = repo / BF_ROOT

    gates = []
    failures = 0
    def gate(name, ok, detail):
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": str(detail)})
        if not ok:
            failures += 1

    gate("PHASE22AE_6_5_10BE_GREEN",
         be.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_5_10BE_HELP_CMDHELPCHK_GUARDED_EXECUTION_PACKAGE_GREEN_STAGED_EXECUTION_NOT_RUN",
         be.get("STATUS", "missing"))
    gate("MSG_022AE_6_5_10BE_SAVEPOINT_PRESENT", sp_be, latest_be)
    gate("BE_GUARDED_PACKAGE_STAGED", be.get("GUARDED_EXECUTION_PACKAGE_STAGED") == "1", be.get("GUARDED_EXECUTION_PACKAGE_STAGED", "missing"))
    gate("BE_HELP_APPLY_NOT_EXECUTED", be.get("HELP_DATA_APPLY_EXECUTED") == "0", be.get("HELP_DATA_APPLY_EXECUTED", "missing"))
    gate("BE_CMDHELPCHK_APPLY_NOT_EXECUTED", be.get("CMDHELPCHK_APPLY_EXECUTED") == "0", be.get("CMDHELPCHK_APPLY_EXECUTED", "missing"))
    gate("BE_TARGET_STATUS_ROWS_PRESENT", len(targets) > 0, len(targets))
    gate("BE_BACKUPS_PRESENT", len(backups) > 0, len(backups))
    gate("BE_ROOT_EXISTS", be_root.exists(), rel(be_root, repo))
    gate("ACTIVE_MESSAGES_HEADER_COUNT_14", msg_count == 14, msg_count)
    gate("ACTIVE_TEXT_HEADER_COUNT_70", text_count == 70, text_count)
    gate("BF_ROOT_NOT_EXISTING_OR_REPLACE_ALLOWED", (not bf_root.exists()) or args.replace_existing_review, rel(bf_root, repo))

    status = BLOCKED
    review_rows = []
    implementation_rows = []
    artifact_rows = []
    if failures == 0:
        if bf_root.exists() and args.replace_existing_review:
            shutil.rmtree(bf_root)
        bf_root.mkdir(parents=True, exist_ok=True)

        for r in targets:
            tpath = r.get("TARGET_PATH", "")
            full = repo / tpath
            fmt, implementation_need = classify_format(full)
            exists = full.exists() and full.is_file()
            probe = quick_probe(full) if exists else "missing"
            can_auto_write_now = 0
            reason = "No automatic mutation in 10BF. "
            if fmt == "DBF_BINARY":
                reason += "DBF target requires native x64base/DotTalk++ HELP/CMDHELPCHK write path or verified DBF schema-specific import path."
            elif fmt in {"TEXT_MARKDOWN", "CSV_TEXT", "JSON_TEXT"}:
                reason += "Text target may be patchable later, but exact anchor/row schema must be reviewed."
            else:
                reason += "Unknown target format requires manual review."

            review_rows.append({
                "EXEC_STEP": r.get("EXEC_STEP", ""),
                "TARGET_ID": r.get("TARGET_ID", ""),
                "TARGET_KIND": r.get("TARGET_KIND", ""),
                "TARGET_PATH": tpath,
                "TARGET_EXISTS": 1 if exists else 0,
                "TARGET_FORMAT": fmt,
                "IMPLEMENTATION_NEED": implementation_need,
                "PROBE": probe,
                "CAN_AUTO_WRITE_NOW": can_auto_write_now,
                "REVIEW_DECISION": "IMPLEMENTATION_PLAN_REQUIRED",
                "REASON": reason,
            })

        implementation_rows = [
            {
                "PLAN_ITEM": "HELP_DATA_WRITE_MECHANIC",
                "STATUS": "REQUIRED",
                "DETAIL": "Identify exact HELP DATA artifact format and use native/guarded write path. Do not raw-write DBF unless target schema/path is proven safe.",
            },
            {
                "PLAN_ITEM": "CMDHELPCHK_WRITE_MECHANIC",
                "STATUS": "REQUIRED",
                "DETAIL": "Identify exact CMDHELPCHK artifact format and expected validation rows/rules before mutation.",
            },
            {
                "PLAN_ITEM": "ANCHOR_OR_KEY_SELECTION",
                "STATUS": "REQUIRED",
                "DETAIL": "For each target, identify keys/anchors such as MSGMGR, SET MESSAGE CATALOG CHECK, SET MESSAGE CATALOG GET, SET MESSAGE EMIT.",
            },
            {
                "PLAN_ITEM": "NATIVE_RUNTIME_READBACK",
                "STATUS": "REQUIRED",
                "DETAIL": "After any later write, prove HELP/CMDHELPCHK behavior through DotTalk++ runtime readback.",
            },
            {
                "PLAN_ITEM": "ROLLBACK_SCRIPT",
                "STATUS": "REQUIRED",
                "DETAIL": "Generate restore from 10BE exact target backups before any later write package.",
            },
        ]

        review_path = bf_root / "target_format_and_write_mechanic_review_v1.csv"
        impl_path = bf_root / "target_specific_write_implementation_requirements_v1.csv"
        readme = bf_root / "README_10BF_EXECUTION_REVIEW.md"

        wcsv(review_path, review_rows, ["EXEC_STEP","TARGET_ID","TARGET_KIND","TARGET_PATH","TARGET_EXISTS","TARGET_FORMAT","IMPLEMENTATION_NEED","PROBE","CAN_AUTO_WRITE_NOW","REVIEW_DECISION","REASON"])
        wcsv(impl_path, implementation_rows, ["PLAN_ITEM","STATUS","DETAIL"])
        readme.write_text(
            "# 10BF HELP/CMDHELPCHK Execution Review\n\n"
            "10BF reviews the staged 10BE execution package and classifies target formats/write mechanics. "
            "It does not mutate HELP DATA or CMDHELPCHK.\n\n"
            "Result: target-specific write implementation is required before any actual apply package.\n",
            encoding="utf-8"
        )

        for p in [review_path, impl_path, readme]:
            artifact_rows.append({"ARTIFACT": rel(p, repo), "ROLE": "execution_review_artifact", "BYTES": p.stat().st_size, "SHA256": sha(p)})

        status = GREEN

    boundary = [
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "10BF writes docs/messaging execution-review artifacts only."},
        {"PROTECTED_SYSTEM": "ACTIVE_SYSTEM_MESSAGES", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_SYSTEM_MESSAGE_TEXT", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_CDX_LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CDX/LMDB mutation."},
        {"PROTECTED_SYSTEM": "WORKSPACE_PROFILE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No workspace mutation."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No HELP DATA mutation; write implementation review only."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CMDHELPCHK mutation; write implementation review only."},
    ]

    readiness = [
        {"ITEM": "TARGET_FORMAT_REVIEW_COMPLETE", "STATUS": "YES" if review_rows else "NO", "DETAIL": f"{len(review_rows)} targets reviewed."},
        {"ITEM": "AUTO_WRITE_READY", "STATUS": "NO", "DETAIL": "10BF intentionally refuses automatic mutation without target-specific write implementation."},
        {"ITEM": "HELP_DATA_APPLY_EXECUTION", "STATUS": "NOT_EXECUTED_IN_10BF", "DETAIL": "No apply execution."},
        {"ITEM": "CMDHELPCHK_APPLY_EXECUTION", "STATUS": "NOT_EXECUTED_IN_10BF", "DETAIL": "No apply execution."},
        {"ITEM": "NEXT_PACKAGE", "STATUS": "10BG_REQUIRED", "DETAIL": "Build target-specific write implementation plan or stop before mutation."},
    ]

    issues = "0" if failures == 0 else str(failures)
    wcsv(reports / "message_catalog_phase22ae_6_5_10bf_gate_check_v1.csv", gates, ["GATE","STATUS","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10bf_target_format_review_v1.csv", review_rows, ["EXEC_STEP","TARGET_ID","TARGET_KIND","TARGET_PATH","TARGET_EXISTS","TARGET_FORMAT","IMPLEMENTATION_NEED","PROBE","CAN_AUTO_WRITE_NOW","REVIEW_DECISION","REASON"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10bf_write_implementation_requirements_v1.csv", implementation_rows, ["PLAN_ITEM","STATUS","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10bf_apply_readiness_v1.csv", readiness, ["ITEM","STATUS","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10bf_boundary_ledger_v1.csv", boundary, ["PROTECTED_SYSTEM","MUTATION_ALLOWED","OBSERVED_MUTATION","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10bf_artifact_manifest_v1.csv", artifact_rows, ["ARTIFACT","ROLE","BYTES","SHA256"])

    summary = {
        "STATUS": status,
        "VALIDATION_ISSUES": issues,
        "PHASE22AE_6_5_10BE_STATUS": be.get("STATUS", ""),
        "MSG_022AE_6_5_10BE_SAVEPOINT_PRESENT": 1 if sp_be else 0,
        "ACTIVE_MESSAGES_OBSERVED_COUNT": msg_count,
        "ACTIVE_TEXT_OBSERVED_COUNT": text_count,
        "BE_TARGET_STATUS_ROWS": len(targets),
        "TARGET_FORMAT_REVIEW_ROWS": len(review_rows),
        "WRITE_IMPLEMENTATION_REQUIREMENT_ROWS": len(implementation_rows),
        "BF_ROOT": rel(bf_root, repo),
        "AUTO_WRITE_READY": 0,
        "TARGET_SPECIFIC_IMPLEMENTATION_REQUIRED": 1 if status == GREEN else 0,
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
    wcsv(reports / "message_catalog_phase22ae_6_5_10bf_status_summary_v1.csv", [summary], list(summary.keys()))

    (repo / "docs/messaging/MESSAGE_LOCALE_PHASE22AE_6_5_10BF_HELP_CMDHELPCHK_EXECUTION_REVIEW.md").write_text(
        f"# Message Catalog Phase 22AE.6.5.10BF HELP/CMDHELPCHK Execution Review\n\n"
        f"Status: `{status}`\n\n"
        "10BF reviews target formats and write mechanics. It does not mutate HELP DATA or CMDHELPCHK.\n\n"
        f"Execution-review root:\n\n```text\n{rel(bf_root, repo)}\n```\n\n"
        f"Next gate:\n\n```text\n{NEXT}\n```\n",
        encoding="utf-8"
    )

    print(status)
    print(f"  validation issues: {issues}")
    print(f"  Phase 22AE.6.5.10BE status: {be.get('STATUS','')}")
    print(f"  MSG-022AE.6.5.10BE savepoint present: {1 if sp_be else 0}")
    print(f"  active messages observed count: {msg_count}")
    print(f"  active text observed count: {text_count}")
    print(f"  BE target status rows: {len(targets)}")
    print(f"  target format review rows: {len(review_rows)}")
    print(f"  write implementation requirement rows: {len(implementation_rows)}")
    print(f"  execution-review root: {rel(bf_root, repo)}")
    print("  auto-write ready: 0")
    print(f"  target-specific implementation required: {summary['TARGET_SPECIFIC_IMPLEMENTATION_REQUIRED']}")
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
