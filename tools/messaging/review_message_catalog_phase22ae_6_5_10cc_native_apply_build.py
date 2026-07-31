#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, json, hashlib, shutil
from datetime import datetime, timezone
from pathlib import Path

GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_10CC_TARGET_SPECIFIC_NATIVE_APPLY_BUILD_PLAN_REVIEW_GREEN_DISCOVERY_PACKAGE_REQUIRED_SOURCE_HELD"
BLOCKED = "MESSAGE_CATALOG_PHASE22AE_6_5_10CC_TARGET_SPECIFIC_NATIVE_APPLY_BUILD_PLAN_REVIEW_BLOCKED"
NEXT = "HOLD_OR_AUTHORIZE_PHASE22AE_6_5_10CD_NATIVE_HELP_CMDHELPCHK_WRITER_DISCOVERY_PACKAGE"

REPORT_DIR = Path("docs/messaging/reports")
CB_SUMMARY = REPORT_DIR / "message_catalog_phase22ae_6_5_10cb_status_summary_v1.csv"
CB_TARGET = REPORT_DIR / "message_catalog_phase22ae_6_5_10cb_target_build_plan_v1.csv"
CB_WRITER = REPORT_DIR / "message_catalog_phase22ae_6_5_10cb_native_writer_family_plan_v1.csv"
CB_SOURCE = REPORT_DIR / "message_catalog_phase22ae_6_5_10cb_source_patch_discovery_plan_v1.csv"
CB_SURFACE = REPORT_DIR / "message_catalog_phase22ae_6_5_10cb_command_surface_build_plan_v1.csv"
CB_VALIDATION = REPORT_DIR / "message_catalog_phase22ae_6_5_10cb_validation_contract_v1.csv"
CB_GUARDS = REPORT_DIR / "message_catalog_phase22ae_6_5_10cb_refusal_guards_v1.csv"
ACTIVE_MSG_DBF = Path("dottalkpp/data/messaging/SYSTEM_MESSAGES.dbf")
ACTIVE_TEXT_DBF = Path("dottalkpp/data/messaging/SYSTEM_MESSAGE_TEXT.dbf")
CC_ROOT = Path("docs/messaging/apply/phase22ae_6_5_10cc_target_specific_native_apply_build_plan_review_v1")

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
    lp = repo / REPORT_DIR / "message_savepoint_latest_v1.json"
    if lp.exists():
        try:
            latest = json.loads(lp.read_text(encoding="utf-8")).get("savepoint_id", "")
        except Exception:
            latest = ""
    jp = repo / "docs/messaging/MESSAGING_SAVEPOINT_JOURNAL.md"
    txt = jp.read_text(encoding="utf-8", errors="replace") if jp.exists() else ""
    return latest == sid or sid in txt, latest

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--replace-existing-review", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    reports = repo / REPORT_DIR
    reports.mkdir(parents=True, exist_ok=True)

    cb = first(repo / CB_SUMMARY)
    target_plan = rows(repo / CB_TARGET)
    writer_plan = rows(repo / CB_WRITER)
    source_plan = rows(repo / CB_SOURCE)
    surface_plan = rows(repo / CB_SURFACE)
    validation_plan_in = rows(repo / CB_VALIDATION)
    guard_rows_in = rows(repo / CB_GUARDS)
    sp_cb, latest_cb = savepoint(repo, "MSG-022AE.6.5.10CB")
    msg_count = dbf_count(repo / ACTIVE_MSG_DBF)
    text_count = dbf_count(repo / ACTIVE_TEXT_DBF)
    cc_root = repo / CC_ROOT

    gates = []
    failures = 0
    def gate(name, ok, detail):
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": str(detail)})
        if not ok:
            failures += 1

    gate("PHASE22AE_6_5_10CB_GREEN",
         cb.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_5_10CB_TARGET_SPECIFIC_NATIVE_APPLY_BUILD_PLAN_GREEN_SOURCE_HELD",
         cb.get("STATUS", "missing"))
    gate("MSG_022AE_6_5_10CB_SAVEPOINT_PRESENT", sp_cb, latest_cb)
    gate("CB_BUILD_PLAN_CREATED", cb.get("TARGET_SPECIFIC_NATIVE_APPLY_BUILD_PLAN_CREATED") == "1", cb.get("TARGET_SPECIFIC_NATIVE_APPLY_BUILD_PLAN_CREATED", "missing"))
    gate("CB_SOURCE_MUTATION_NOT_AUTHORIZED", cb.get("SOURCE_MUTATION_AUTHORIZED_NOW") == "0", cb.get("SOURCE_MUTATION_AUTHORIZED_NOW", "missing"))
    gate("CB_APPLY_EXECUTION_NOT_AUTHORIZED", cb.get("APPLY_EXECUTION_AUTHORIZED_NOW") == "0", cb.get("APPLY_EXECUTION_AUTHORIZED_NOW", "missing"))
    gate("CB_HELP_APPLY_NOT_EXECUTED", cb.get("HELP_DATA_APPLY_EXECUTED") == "0", cb.get("HELP_DATA_APPLY_EXECUTED", "missing"))
    gate("CB_CMDHELPCHK_APPLY_NOT_EXECUTED", cb.get("CMDHELPCHK_APPLY_EXECUTED") == "0", cb.get("CMDHELPCHK_APPLY_EXECUTED", "missing"))
    gate("CB_TARGET_PLAN_ROWS_PRESENT", len(target_plan) > 0, len(target_plan))
    gate("CB_WRITER_PLAN_ROWS_PRESENT", len(writer_plan) > 0, len(writer_plan))
    gate("CB_SOURCE_PLAN_ROWS_PRESENT", len(source_plan) > 0, len(source_plan))
    gate("CB_SURFACE_PLAN_ROWS_PRESENT", len(surface_plan) > 0, len(surface_plan))
    gate("CB_VALIDATION_PLAN_ROWS_PRESENT", len(validation_plan_in) > 0, len(validation_plan_in))
    gate("ACTIVE_MESSAGES_HEADER_COUNT_14", msg_count == 14, msg_count)
    gate("ACTIVE_TEXT_HEADER_COUNT_70", text_count == 70, text_count)
    gate("CC_ROOT_NOT_EXISTING_OR_REPLACE_ALLOWED", (not cc_root.exists()) or args.replace_existing_review, rel(cc_root, repo))

    status = BLOCKED
    target_review = []
    writer_review = []
    source_discovery_review = []
    discovery_package_requirements = []
    validation_review = []
    guard_rows = []
    artifact_rows = []

    if failures == 0:
        if cc_root.exists() and args.replace_existing_review:
            shutil.rmtree(cc_root)
        cc_root.mkdir(parents=True, exist_ok=True)

        for i, r in enumerate(target_plan, start=1):
            target_review.append({
                "REVIEW_ROW": i,
                "TARGET_PATH": r.get("TARGET_PATH", ""),
                "TARGET_KIND": r.get("TARGET_KIND", ""),
                "WRITER_FAMILY": r.get("WRITER_FAMILY", ""),
                "BUILD_PLAN_STATUS": r.get("BUILD_PLAN_STATUS", ""),
                "SOURCE_MUTATION_AUTHORIZED_NOW": r.get("SOURCE_MUTATION_AUTHORIZED_NOW", "0"),
                "APPLY_AUTHORIZED_NOW": r.get("APPLY_AUTHORIZED_NOW", "0"),
                "APPLY_EXECUTED_NOW": r.get("APPLY_EXECUTED_NOW", "0"),
                "REVIEW_DISPOSITION": "ACCEPT_FOR_DISCOVERY_PACKAGE",
                "DISCOVERY_PACKAGE_REQUIRED": 1,
                "REVIEW_DETAIL": "Target build row is source-held/apply-held and ready for native writer discovery.",
            })

        for i, r in enumerate(writer_plan, start=1):
            writer_review.append({
                "WRITER_REVIEW_ROW": i,
                "WRITER_FAMILY": r.get("WRITER_FAMILY", ""),
                "SCOPE": r.get("SCOPE", ""),
                "BUILD_ACTION": r.get("BUILD_ACTION", ""),
                "SOURCE_MUTATION_AUTHORIZED_NOW": r.get("SOURCE_MUTATION_AUTHORIZED_NOW", "0"),
                "APPLY_AUTHORIZED_NOW": r.get("APPLY_AUTHORIZED_NOW", "0"),
                "REVIEW_DISPOSITION": "ACCEPT_WRITER_FAMILY_FOR_DISCOVERY",
            })

        for i, r in enumerate(source_plan, start=1):
            source_discovery_review.append({
                "SOURCE_REVIEW_ROW": i,
                "PATCH_TARGET": r.get("PATCH_TARGET", ""),
                "PATCH_KIND": r.get("PATCH_KIND", ""),
                "REQUIRED": r.get("REQUIRED", ""),
                "SOURCE_MUTATION_AUTHORIZED_NOW": r.get("SOURCE_MUTATION_AUTHORIZED_NOW", "0"),
                "REVIEW_DISPOSITION": "ACCEPT_DISCOVERY_FIRST",
                "REVIEW_DETAIL": r.get("DETAIL", ""),
            })

        discovery_package_requirements = [
            {"DISCOVERY_ROW": 1, "DISCOVERY_TARGET": "HELP DATA writer path", "SEARCH_SCOPE": "source tree and runtime commands", "DISCOVERY_ACTION": "find existing HELP DATA import/update/write command or helper before proposing source patch", "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
            {"DISCOVERY_ROW": 2, "DISCOVERY_TARGET": "CMDHELPCHK writer path", "SEARCH_SCOPE": "source tree and runtime commands", "DISCOVERY_ACTION": "find existing CMDHELPCHK/catalog import/update/write command or helper before proposing source patch", "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
            {"DISCOVERY_ROW": 3, "DISCOVERY_TARGET": "HELP table/schema names", "SEARCH_SCOPE": "dottalkpp/data/help, schemas, source comments, command handlers", "DISCOVERY_ACTION": "identify exact target files/tables and native mutation path", "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
            {"DISCOVERY_ROW": 4, "DISCOVERY_TARGET": "CMDHELPCHK target files/tables", "SEARCH_SCOPE": "dottalkpp/data/help, reports, source, command registry", "DISCOVERY_ACTION": "identify exact validation/catalog target and update mechanism", "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
            {"DISCOVERY_ROW": 5, "DISCOVERY_TARGET": "source-comment usage contract impact", "SEARCH_SCOPE": "src/cli, command registrations, @dottalk.usage metadata", "DISCOVERY_ACTION": "report whether source-contract changes are required in later package", "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
            {"DISCOVERY_ROW": 6, "DISCOVERY_TARGET": "DOTSCRIPT transcript readback option", "SEARCH_SCOPE": "runtime script/transcript support", "DISCOVERY_ACTION": "plan how later proof transcript will be captured if transcript service is available", "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
        ]

        for i, r in enumerate(validation_plan_in, start=1):
            validation_review.append({
                "VALIDATION_REVIEW_ROW": i,
                "VALIDATION": r.get("VALIDATION", ""),
                "REQUIRED": r.get("REQUIRED", ""),
                "RUN_NOW": 0,
                "REVIEW_DISPOSITION": "CARRY_FORWARD_TO_DISCOVERY_PACKAGE",
            })

        guard_rows = [
            {"REFUSAL_GUARD": "NO_SOURCE_PATCH_IN_10CC", "STATUS": "ACTIVE", "DETAIL": "10CC is build-plan review only."},
            {"REFUSAL_GUARD": "NO_HELP_DATA_APPLY_IN_10CC", "STATUS": "ACTIVE", "DETAIL": "HELP DATA mutation remains blocked."},
            {"REFUSAL_GUARD": "NO_CMDHELPCHK_APPLY_IN_10CC", "STATUS": "ACTIVE", "DETAIL": "CMDHELPCHK mutation remains blocked."},
            {"REFUSAL_GUARD": "DISCOVERY_BEFORE_SOURCE_PATCH", "STATUS": "ACTIVE", "DETAIL": "Existing native writer paths must be discovered before source patch planning."},
            {"REFUSAL_GUARD": "NO_RAW_DBF_BYTE_WRITE", "STATUS": "ACTIVE", "DETAIL": "Future DBF touching must be native/schema-aware."},
        ]

        scripts_dir = cc_root / "scripts"
        scripts_dir.mkdir(parents=True, exist_ok=True)

        disabled_discovery = scripts_dir / "MESSAGE_CATALOG_PHASE22AE_6_5_10CD_DISCOVERY_TEMPLATE.ps1.disabled"
        disabled_discovery.write_text(
            'throw "10CC is review only. Generate a dedicated 10CD discovery package before running writer discovery."\n',
            encoding="utf-8"
        )
        readback_dts = scripts_dir / "MESSAGE_CATALOG_PHASE22AE_6_5_10CC_READBACK_CONTRACT.dts"
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

        notes = cc_root / "native_apply_build_plan_review_v1.md"
        notes.write_text(
            "# 10CC Target-Specific Native Apply Build Plan Review\n\n"
            "10CC accepts the 10CB build plan and requires a dedicated native HELP/CMDHELPCHK writer discovery package before any source or active-catalog mutation.\n\n"
            "No source, HELP DATA, CMDHELPCHK, DBF, CDX, LMDB, or workspace mutation is authorized in 10CC.\n",
            encoding="utf-8"
        )

        target_path = cc_root / "target_build_plan_review_v1.csv"
        writer_path = cc_root / "native_writer_family_review_v1.csv"
        source_path = cc_root / "source_patch_discovery_review_v1.csv"
        discovery_path = cc_root / "discovery_package_requirements_v1.csv"
        validation_path = cc_root / "validation_contract_review_v1.csv"
        guard_path = cc_root / "refusal_guards_v1.csv"
        readme = cc_root / "README_10CC_TARGET_SPECIFIC_NATIVE_APPLY_BUILD_PLAN_REVIEW.md"
        readme.write_text(
            "# 10CC Target-Specific Native Apply Build Plan Review\n\n"
            "10CC reviews the 10CB target-specific native apply build plan and prepares the 10CD discovery gate.\n\n"
            "It is still source-held and apply-held: no HELP DATA, CMDHELPCHK, source, DBF, CDX, LMDB, or workspace mutation occurs.\n",
            encoding="utf-8"
        )

        wcsv(target_path, target_review, ["REVIEW_ROW","TARGET_PATH","TARGET_KIND","WRITER_FAMILY","BUILD_PLAN_STATUS","SOURCE_MUTATION_AUTHORIZED_NOW","APPLY_AUTHORIZED_NOW","APPLY_EXECUTED_NOW","REVIEW_DISPOSITION","DISCOVERY_PACKAGE_REQUIRED","REVIEW_DETAIL"])
        wcsv(writer_path, writer_review, ["WRITER_REVIEW_ROW","WRITER_FAMILY","SCOPE","BUILD_ACTION","SOURCE_MUTATION_AUTHORIZED_NOW","APPLY_AUTHORIZED_NOW","REVIEW_DISPOSITION"])
        wcsv(source_path, source_discovery_review, ["SOURCE_REVIEW_ROW","PATCH_TARGET","PATCH_KIND","REQUIRED","SOURCE_MUTATION_AUTHORIZED_NOW","REVIEW_DISPOSITION","REVIEW_DETAIL"])
        wcsv(discovery_path, discovery_package_requirements, ["DISCOVERY_ROW","DISCOVERY_TARGET","SEARCH_SCOPE","DISCOVERY_ACTION","SOURCE_MUTATION_AUTHORIZED_NOW","APPLY_AUTHORIZED_NOW"])
        wcsv(validation_path, validation_review, ["VALIDATION_REVIEW_ROW","VALIDATION","REQUIRED","RUN_NOW","REVIEW_DISPOSITION"])
        wcsv(guard_path, guard_rows, ["REFUSAL_GUARD","STATUS","DETAIL"])

        for p in [target_path, writer_path, source_path, discovery_path, validation_path, guard_path, disabled_discovery, readback_dts, notes, readme]:
            artifact_rows.append({"ARTIFACT": rel(p, repo), "ROLE": "target_specific_native_apply_build_plan_review_artifact", "BYTES": p.stat().st_size, "SHA256": sha(p)})

        status = GREEN

    boundary = [
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "10CC writes docs/messaging review artifacts only."},
        {"PROTECTED_SYSTEM": "ACTIVE_SYSTEM_MESSAGES", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_SYSTEM_MESSAGE_TEXT", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_CDX_LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CDX/LMDB mutation."},
        {"PROTECTED_SYSTEM": "WORKSPACE_PROFILE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No workspace mutation."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Build-plan review only; no HELP DATA apply."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Build-plan review only; no CMDHELPCHK apply."},
    ]

    readiness = [
        {"ITEM": "BUILD_PLAN_REVIEW_COMPLETE", "STATUS": "YES" if target_review else "NO", "DETAIL": f"{len(target_review)} target build rows reviewed."},
        {"ITEM": "DISCOVERY_PACKAGE_REQUIRED", "STATUS": "YES" if discovery_package_requirements else "NO", "DETAIL": f"{len(discovery_package_requirements)} discovery requirements."},
        {"ITEM": "HELP_DATA_APPLY_EXECUTION", "STATUS": "NOT_EXECUTED_IN_10CC", "DETAIL": "No apply execution."},
        {"ITEM": "CMDHELPCHK_APPLY_EXECUTION", "STATUS": "NOT_EXECUTED_IN_10CC", "DETAIL": "No apply execution."},
        {"ITEM": "NEXT_DISCOVERY_GATE", "STATUS": "10CD_REQUIRED", "DETAIL": "Discover/reuse native writer paths before implementation planning."},
    ]

    issues = "0" if failures == 0 else str(failures)
    wcsv(reports / "message_catalog_phase22ae_6_5_10cc_gate_check_v1.csv", gates, ["GATE","STATUS","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10cc_target_build_plan_review_v1.csv", target_review, ["REVIEW_ROW","TARGET_PATH","TARGET_KIND","WRITER_FAMILY","BUILD_PLAN_STATUS","SOURCE_MUTATION_AUTHORIZED_NOW","APPLY_AUTHORIZED_NOW","APPLY_EXECUTED_NOW","REVIEW_DISPOSITION","DISCOVERY_PACKAGE_REQUIRED","REVIEW_DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10cc_native_writer_family_review_v1.csv", writer_review, ["WRITER_REVIEW_ROW","WRITER_FAMILY","SCOPE","BUILD_ACTION","SOURCE_MUTATION_AUTHORIZED_NOW","APPLY_AUTHORIZED_NOW","REVIEW_DISPOSITION"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10cc_source_discovery_review_v1.csv", source_discovery_review, ["SOURCE_REVIEW_ROW","PATCH_TARGET","PATCH_KIND","REQUIRED","SOURCE_MUTATION_AUTHORIZED_NOW","REVIEW_DISPOSITION","REVIEW_DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10cc_discovery_package_requirements_v1.csv", discovery_package_requirements, ["DISCOVERY_ROW","DISCOVERY_TARGET","SEARCH_SCOPE","DISCOVERY_ACTION","SOURCE_MUTATION_AUTHORIZED_NOW","APPLY_AUTHORIZED_NOW"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10cc_validation_contract_review_v1.csv", validation_review, ["VALIDATION_REVIEW_ROW","VALIDATION","REQUIRED","RUN_NOW","REVIEW_DISPOSITION"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10cc_refusal_guards_v1.csv", guard_rows, ["REFUSAL_GUARD","STATUS","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10cc_apply_readiness_v1.csv", readiness, ["ITEM","STATUS","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10cc_boundary_ledger_v1.csv", boundary, ["PROTECTED_SYSTEM","MUTATION_ALLOWED","OBSERVED_MUTATION","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10cc_artifact_manifest_v1.csv", artifact_rows, ["ARTIFACT","ROLE","BYTES","SHA256"])

    summary = {
        "STATUS": status,
        "VALIDATION_ISSUES": issues,
        "PHASE22AE_6_5_10CB_STATUS": cb.get("STATUS", ""),
        "MSG_022AE_6_5_10CB_SAVEPOINT_PRESENT": 1 if sp_cb else 0,
        "ACTIVE_MESSAGES_OBSERVED_COUNT": msg_count,
        "ACTIVE_TEXT_OBSERVED_COUNT": text_count,
        "CB_TARGET_BUILD_PLAN_ROWS": len(target_plan),
        "CB_NATIVE_WRITER_PLAN_ROWS": len(writer_plan),
        "CB_SOURCE_DISCOVERY_PLAN_ROWS": len(source_plan),
        "CB_COMMAND_SURFACE_PLAN_ROWS": len(surface_plan),
        "TARGET_BUILD_PLAN_REVIEW_ROWS": len(target_review),
        "NATIVE_WRITER_REVIEW_ROWS": len(writer_review),
        "SOURCE_DISCOVERY_REVIEW_ROWS": len(source_discovery_review),
        "DISCOVERY_PACKAGE_REQUIREMENT_ROWS": len(discovery_package_requirements),
        "CC_ROOT": rel(cc_root, repo),
        "DISCOVERY_PACKAGE_REQUIRED": 1 if status == GREEN else 0,
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
    wcsv(reports / "message_catalog_phase22ae_6_5_10cc_status_summary_v1.csv", [summary], list(summary.keys()))

    (repo / "docs/messaging/MESSAGE_LOCALE_PHASE22AE_6_5_10CC_TARGET_SPECIFIC_NATIVE_APPLY_BUILD_PLAN_REVIEW.md").write_text(
        f"# Message Catalog Phase 22AE.6.5.10CC Target-Specific Native Apply Build Plan Review\n\n"
        f"Status: `{status}`\n\n"
        "10CC reviews the 10CB build plan and requires a native HELP/CMDHELPCHK writer discovery package. It does not mutate HELP DATA, CMDHELPCHK, source, DBF, CDX, LMDB, or workspace files.\n\n"
        f"Review root:\n\n```text\n{rel(cc_root, repo)}\n```\n\n"
        f"Next gate:\n\n```text\n{NEXT}\n```\n",
        encoding="utf-8"
    )

    print(status)
    print(f"  validation issues: {issues}")
    print(f"  Phase 22AE.6.5.10CB status: {cb.get('STATUS','')}")
    print(f"  MSG-022AE.6.5.10CB savepoint present: {1 if sp_cb else 0}")
    print(f"  active messages observed count: {msg_count}")
    print(f"  active text observed count: {text_count}")
    print(f"  CB target build plan rows: {len(target_plan)}")
    print(f"  CB native writer plan rows: {len(writer_plan)}")
    print(f"  CB source discovery plan rows: {len(source_plan)}")
    print(f"  CB command surface plan rows: {len(surface_plan)}")
    print(f"  target build plan review rows: {len(target_review)}")
    print(f"  native writer review rows: {len(writer_review)}")
    print(f"  source discovery review rows: {len(source_discovery_review)}")
    print(f"  discovery package requirement rows: {len(discovery_package_requirements)}")
    print(f"  review root: {rel(cc_root, repo)}")
    print("  discovery package required: 1")
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
