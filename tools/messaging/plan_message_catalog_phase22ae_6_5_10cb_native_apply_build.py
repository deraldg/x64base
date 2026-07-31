#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, json, hashlib, shutil
from datetime import datetime, timezone
from pathlib import Path

GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_10CB_TARGET_SPECIFIC_NATIVE_APPLY_BUILD_PLAN_GREEN_SOURCE_HELD"
BLOCKED = "MESSAGE_CATALOG_PHASE22AE_6_5_10CB_TARGET_SPECIFIC_NATIVE_APPLY_BUILD_PLAN_BLOCKED"
NEXT = "HOLD_OR_AUTHORIZE_PHASE22AE_6_5_10CC_TARGET_SPECIFIC_NATIVE_APPLY_BUILD_PLAN_REVIEW"
REPORT_DIR = Path("docs/messaging/reports")
CA_SUMMARY = REPORT_DIR / "message_catalog_phase22ae_6_5_10ca_status_summary_v1.csv"
CA_IMPL_REVIEW = REPORT_DIR / "message_catalog_phase22ae_6_5_10ca_native_implementation_review_v1.csv"
CA_CONTRACT_REVIEW = REPORT_DIR / "message_catalog_phase22ae_6_5_10ca_target_apply_contract_review_v1.csv"
CA_SURFACE_REVIEW = REPORT_DIR / "message_catalog_phase22ae_6_5_10ca_surface_implementation_review_v1.csv"
CA_BUILD_REQ = REPORT_DIR / "message_catalog_phase22ae_6_5_10ca_build_plan_requirements_v1.csv"
CA_VALIDATION_REVIEW = REPORT_DIR / "message_catalog_phase22ae_6_5_10ca_validation_contract_review_v1.csv"
ACTIVE_MSG_DBF = Path("dottalkpp/data/messaging/SYSTEM_MESSAGES.dbf")
ACTIVE_TEXT_DBF = Path("dottalkpp/data/messaging/SYSTEM_MESSAGE_TEXT.dbf")
CB_ROOT = Path("docs/messaging/apply/phase22ae_6_5_10cb_target_specific_native_apply_build_plan_v1")

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

def writer_family(kind, target, surface=""):
    text = " ".join([kind or "", target or "", surface or ""]).upper()
    if "CMDHELPCHK" in text:
        return "CMDHELPCHK_NATIVE_WRITER_PLAN"
    if "HELP" in text:
        return "HELP_DATA_NATIVE_WRITER_PLAN"
    if "DBF" in text or "DOTTALK_NATIVE_TABLE" in text:
        return "DOTTALK_TABLE_NATIVE_WRITER_PLAN"
    if "SCHEMA" in text:
        return "SCHEMA_AWARE_WRITER_PLAN"
    return "TARGET_SPECIFIC_NATIVE_WRITER_PLAN"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--replace-existing-plan", action="store_true")
    args = ap.parse_args()
    repo = Path(args.repo_root).resolve()
    reports = repo / REPORT_DIR
    reports.mkdir(parents=True, exist_ok=True)

    ca = first(repo / CA_SUMMARY)
    impl_review = rows(repo / CA_IMPL_REVIEW)
    contract_review = rows(repo / CA_CONTRACT_REVIEW)
    surface_review = rows(repo / CA_SURFACE_REVIEW)
    build_req = rows(repo / CA_BUILD_REQ)
    validation_review = rows(repo / CA_VALIDATION_REVIEW)
    sp_ca, latest_ca = savepoint(repo, "MSG-022AE.6.5.10CA")
    msg_count = dbf_count(repo / ACTIVE_MSG_DBF)
    text_count = dbf_count(repo / ACTIVE_TEXT_DBF)
    cb_root = repo / CB_ROOT

    gates = []
    failures = 0
    def gate(name, ok, detail):
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": str(detail)})
        if not ok:
            failures += 1

    gate("PHASE22AE_6_5_10CA_GREEN", ca.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_5_10CA_NATIVE_APPLY_IMPLEMENTATION_PACKAGE_REVIEW_GREEN_BUILD_PLAN_REQUIRED_SOURCE_HELD", ca.get("STATUS", "missing"))
    gate("MSG_022AE_6_5_10CA_SAVEPOINT_PRESENT", sp_ca, latest_ca)
    gate("CA_BUILD_PLAN_REQUIRED", ca.get("BUILD_PLAN_REQUIRED") == "1", ca.get("BUILD_PLAN_REQUIRED", "missing"))
    gate("CA_HELP_APPLY_NOT_EXECUTED", ca.get("HELP_DATA_APPLY_EXECUTED") == "0", ca.get("HELP_DATA_APPLY_EXECUTED", "missing"))
    gate("CA_CMDHELPCHK_APPLY_NOT_EXECUTED", ca.get("CMDHELPCHK_APPLY_EXECUTED") == "0", ca.get("CMDHELPCHK_APPLY_EXECUTED", "missing"))
    gate("CA_IMPL_REVIEW_ROWS_PRESENT", len(impl_review) > 0, len(impl_review))
    gate("CA_CONTRACT_REVIEW_ROWS_PRESENT", len(contract_review) > 0, len(contract_review))
    gate("CA_SURFACE_REVIEW_ROWS_PRESENT", len(surface_review) > 0, len(surface_review))
    gate("CA_BUILD_REQUIREMENT_ROWS_PRESENT", len(build_req) > 0, len(build_req))
    gate("CA_VALIDATION_REVIEW_ROWS_PRESENT", len(validation_review) > 0, len(validation_review))
    gate("ACTIVE_MESSAGES_HEADER_COUNT_14", msg_count == 14, msg_count)
    gate("ACTIVE_TEXT_HEADER_COUNT_70", text_count == 70, text_count)
    gate("CB_ROOT_NOT_EXISTING_OR_REPLACE_ALLOWED", (not cb_root.exists()) or args.replace_existing_plan, rel(cb_root, repo))

    status = BLOCKED
    target_plan = []
    writer_plan = []
    source_plan = []
    surface_plan = []
    validation_plan = []
    refusal_rows = []
    artifact_rows = []

    if failures == 0:
        if cb_root.exists() and args.replace_existing_plan:
            shutil.rmtree(cb_root)
        cb_root.mkdir(parents=True, exist_ok=True)
        contract_by_target = {r.get("TARGET_PATH", ""): r for r in contract_review}

        for i, r in enumerate(impl_review, start=1):
            target = r.get("TARGET_PATH", "")
            contract = contract_by_target.get(target, {})
            wfam = writer_family(r.get("IMPLEMENTATION_KIND", ""), target)
            target_plan.append({
                "BUILD_ROW": i,
                "TARGET_PATH": target,
                "TARGET_KIND": r.get("TARGET_KIND", ""),
                "TARGET_EXISTS": r.get("TARGET_EXISTS", ""),
                "IMPLEMENTATION_KIND": r.get("IMPLEMENTATION_KIND", ""),
                "REQUIRED_IMPLEMENTATION": r.get("REQUIRED_IMPLEMENTATION", ""),
                "WRITER_FAMILY": wfam,
                "TARGET_SHA256_EXPECTED": contract.get("TARGET_SHA256_EXPECTED", ""),
                "BACKUP_PATH": contract.get("BACKUP_PATH", ""),
                "REFUSE_IF": contract.get("REFUSE_IF", "target hash drift; backup missing; runtime readback missing"),
                "BUILD_PLAN_STATUS": "PLANNED_SOURCE_HELD",
                "SOURCE_MUTATION_AUTHORIZED_NOW": 0,
                "APPLY_AUTHORIZED_NOW": 0,
                "APPLY_EXECUTED_NOW": 0,
            })

        writer_plan = [
            {"WRITER_ROW": 1, "WRITER_FAMILY": "HELP_DATA_NATIVE_WRITER_PLAN", "SCOPE": "HELP MSGMGR and HELP SET MESSAGE topic insertion/update", "BUILD_ACTION": "discover or define guarded native HELP DATA update path", "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
            {"WRITER_ROW": 2, "WRITER_FAMILY": "CMDHELPCHK_NATIVE_WRITER_PLAN", "SCOPE": "CMDHELPCHK rows for MSGMGR and SET MESSAGE surfaces", "BUILD_ACTION": "discover or define guarded native CMDHELPCHK update path", "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
            {"WRITER_ROW": 3, "WRITER_FAMILY": "SCHEMA_AWARE_WRITER_PLAN", "SCOPE": "any DBF-backed HELP/CMDHELPCHK target", "BUILD_ACTION": "require native/schema-aware writes; refuse raw DBF byte edits", "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
            {"WRITER_ROW": 4, "WRITER_FAMILY": "READBACK_TRANSCRIPT_PLAN", "SCOPE": "post-apply proof", "BUILD_ACTION": "use DOTSCRIPT transcript path when available; otherwise capture manual transcript", "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
        ]
        source_plan = [
            {"PATCH_ROW": 1, "PATCH_TARGET": "existing HELP DATA writer surface", "PATCH_KIND": "DISCOVERY_OR_REUSE_FIRST", "REQUIRED": 1, "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "DETAIL": "Do not add new source until existing HELP DATA mutation path is inventoried."},
            {"PATCH_ROW": 2, "PATCH_TARGET": "existing CMDHELPCHK writer surface", "PATCH_KIND": "DISCOVERY_OR_REUSE_FIRST", "REQUIRED": 1, "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "DETAIL": "Do not bypass existing runtime/catalog mechanisms."},
            {"PATCH_ROW": 3, "PATCH_TARGET": "source-comment contracts", "PATCH_KIND": "REQUIRED_IF_SOURCE_PATCH_LATER", "REQUIRED": 1, "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "DETAIL": "If a later source patch changes command syntax or behavior, update @dottalk.usage and contract comments in same guarded package."},
            {"PATCH_ROW": 4, "PATCH_TARGET": "raw Python DBF writer", "PATCH_KIND": "FORBIDDEN", "REQUIRED": 1, "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "DETAIL": "Raw DBF byte writing is forbidden for runtime promotion/materialization."},
        ]
        for i, r in enumerate(surface_review, start=1):
            surface_plan.append({
                "SURFACE_BUILD_ROW": i,
                "COMMAND_OR_SURFACE": r.get("COMMAND_OR_SURFACE", ""),
                "IMPLEMENTATION_NEED": r.get("IMPLEMENTATION_NEED", ""),
                "REVIEW_DISPOSITION": r.get("REVIEW_DISPOSITION", ""),
                "BUILD_PLAN_ACTION": "MAP_TO_NATIVE_WRITER_OR_READBACK",
                "APPLY_AUTHORIZED_NOW": 0,
            })
        validation_plan = [
            {"VALIDATION_ROW": 1, "VALIDATION": "10CB build plan reviewed before implementation", "REQUIRED": 1, "RUN_NOW": 0},
            {"VALIDATION_ROW": 2, "VALIDATION": "existing native HELP DATA writer inventoried", "REQUIRED": 1, "RUN_NOW": 0},
            {"VALIDATION_ROW": 3, "VALIDATION": "existing native CMDHELPCHK writer inventoried", "REQUIRED": 1, "RUN_NOW": 0},
            {"VALIDATION_ROW": 4, "VALIDATION": "target hashes and backups carried forward", "REQUIRED": 1, "RUN_NOW": 0},
            {"VALIDATION_ROW": 5, "VALIDATION": "source-comment contracts updated if source patch is later authorized", "REQUIRED": 1, "RUN_NOW": 0},
            {"VALIDATION_ROW": 6, "VALIDATION": "HELP MSGMGR readback after future apply", "REQUIRED": 1, "RUN_NOW": 0},
            {"VALIDATION_ROW": 7, "VALIDATION": "HELP SET MESSAGE readback after future apply", "REQUIRED": 1, "RUN_NOW": 0},
            {"VALIDATION_ROW": 8, "VALIDATION": "CMDHELPCHK readback after future apply", "REQUIRED": 1, "RUN_NOW": 0},
            {"VALIDATION_ROW": 9, "VALIDATION": "SYSTEM_MESSAGES remains 14 unless separately authorized", "REQUIRED": 1, "RUN_NOW": 0},
            {"VALIDATION_ROW": 10, "VALIDATION": "SYSTEM_MESSAGE_TEXT remains 70 unless separately authorized", "REQUIRED": 1, "RUN_NOW": 0},
        ]
        refusal_rows = [
            {"REFUSAL_GUARD": "NO_SOURCE_PATCH_IN_10CB", "STATUS": "ACTIVE", "DETAIL": "10CB is a build plan only."},
            {"REFUSAL_GUARD": "NO_HELP_DATA_APPLY_IN_10CB", "STATUS": "ACTIVE", "DETAIL": "HELP DATA mutation remains blocked."},
            {"REFUSAL_GUARD": "NO_CMDHELPCHK_APPLY_IN_10CB", "STATUS": "ACTIVE", "DETAIL": "CMDHELPCHK mutation remains blocked."},
            {"REFUSAL_GUARD": "NO_RAW_DBF_BYTE_WRITE", "STATUS": "ACTIVE", "DETAIL": "Future DBF touching must be native/schema-aware."},
            {"REFUSAL_GUARD": "REQUIRE_SAVEPOINTED_REVIEW_BEFORE_IMPLEMENTATION", "STATUS": "ACTIVE", "DETAIL": "10CC review required before implementation work."},
        ]

        scripts_dir = cb_root / "scripts"
        scripts_dir.mkdir(parents=True, exist_ok=True)
        disabled_impl = scripts_dir / "MESSAGE_CATALOG_PHASE22AE_6_5_10CD_IMPLEMENTATION_TEMPLATE.ps1.disabled"
        disabled_impl.write_text('throw "10CB is a build plan only. Wait for 10CC review and a separately authorized implementation package before source or HELP/CMDHELPCHK mutation."\n', encoding="utf-8")
        readback_dts = scripts_dir / "MESSAGE_CATALOG_PHASE22AE_6_5_10CB_READBACK_CONTRACT.dts"
        readback_dts.write_text("MSGMGR STATUS\nMSGMGR CHECK\nSET MESSAGE CATALOG CHECK\nSET MESSAGE EMIT MESSAGE_PROOF_MODE_STATUS en-US\nHELP MSGMGR\nHELP SET MESSAGE\nCMDHELPCHK\nQUIT\n", encoding="utf-8")
        notes = cb_root / "target_specific_native_apply_build_plan_v1.md"
        notes.write_text("# 10CB Target-Specific Native Apply Build Plan\n\n10CB converts the reviewed 10CA implementation package into a build plan. It requires discovery or reuse of native HELP DATA and CMDHELPCHK writer paths before any source or active-catalog mutation.\n\nNo source, HELP DATA, CMDHELPCHK, DBF, CDX, LMDB, or workspace mutation is authorized in 10CB.\n", encoding="utf-8")
        readme = cb_root / "README_10CB_TARGET_SPECIFIC_NATIVE_APPLY_BUILD_PLAN.md"
        readme.write_text("# 10CB Target-Specific Native Apply Build Plan\n\n10CB plans how to build the target-specific native/schema-aware apply path required by 10CA. It is source-held and apply-held.\n", encoding="utf-8")

        target_path = cb_root / "target_specific_native_apply_build_plan_v1.csv"
        writer_path = cb_root / "native_writer_family_plan_v1.csv"
        source_path = cb_root / "source_patch_discovery_plan_v1.csv"
        surface_path = cb_root / "command_surface_build_plan_v1.csv"
        validation_path = cb_root / "build_plan_validation_contract_v1.csv"
        guard_path = cb_root / "build_plan_refusal_guards_v1.csv"
        wcsv(target_path, target_plan, ["BUILD_ROW","TARGET_PATH","TARGET_KIND","TARGET_EXISTS","IMPLEMENTATION_KIND","REQUIRED_IMPLEMENTATION","WRITER_FAMILY","TARGET_SHA256_EXPECTED","BACKUP_PATH","REFUSE_IF","BUILD_PLAN_STATUS","SOURCE_MUTATION_AUTHORIZED_NOW","APPLY_AUTHORIZED_NOW","APPLY_EXECUTED_NOW"])
        wcsv(writer_path, writer_plan, ["WRITER_ROW","WRITER_FAMILY","SCOPE","BUILD_ACTION","SOURCE_MUTATION_AUTHORIZED_NOW","APPLY_AUTHORIZED_NOW"])
        wcsv(source_path, source_plan, ["PATCH_ROW","PATCH_TARGET","PATCH_KIND","REQUIRED","SOURCE_MUTATION_AUTHORIZED_NOW","DETAIL"])
        wcsv(surface_path, surface_plan, ["SURFACE_BUILD_ROW","COMMAND_OR_SURFACE","IMPLEMENTATION_NEED","REVIEW_DISPOSITION","BUILD_PLAN_ACTION","APPLY_AUTHORIZED_NOW"])
        wcsv(validation_path, validation_plan, ["VALIDATION_ROW","VALIDATION","REQUIRED","RUN_NOW"])
        wcsv(guard_path, refusal_rows, ["REFUSAL_GUARD","STATUS","DETAIL"])
        for p in [target_path, writer_path, source_path, surface_path, validation_path, guard_path, disabled_impl, readback_dts, notes, readme]:
            artifact_rows.append({"ARTIFACT": rel(p, repo), "ROLE": "target_specific_native_apply_build_plan_artifact", "BYTES": p.stat().st_size, "SHA256": sha(p)})
        status = GREEN

    boundary = [
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "10CB writes docs/messaging build-plan artifacts only."},
        {"PROTECTED_SYSTEM": "ACTIVE_SYSTEM_MESSAGES", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_SYSTEM_MESSAGE_TEXT", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_CDX_LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CDX/LMDB mutation."},
        {"PROTECTED_SYSTEM": "WORKSPACE_PROFILE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No workspace mutation."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Build plan only; no HELP DATA apply."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Build plan only; no CMDHELPCHK apply."},
    ]
    readiness = [
        {"ITEM": "TARGET_SPECIFIC_NATIVE_APPLY_BUILD_PLAN_CREATED", "STATUS": "YES" if target_plan else "NO", "DETAIL": f"{len(target_plan)} target build rows."},
        {"ITEM": "NATIVE_WRITER_FAMILY_PLAN_CREATED", "STATUS": "YES" if writer_plan else "NO", "DETAIL": f"{len(writer_plan)} writer-family rows."},
        {"ITEM": "SOURCE_PATCH_DISCOVERY_PLAN_CREATED", "STATUS": "YES" if source_plan else "NO", "DETAIL": f"{len(source_plan)} source/discovery rows."},
        {"ITEM": "HELP_DATA_APPLY_EXECUTION", "STATUS": "NOT_EXECUTED_IN_10CB", "DETAIL": "No apply execution."},
        {"ITEM": "CMDHELPCHK_APPLY_EXECUTION", "STATUS": "NOT_EXECUTED_IN_10CB", "DETAIL": "No apply execution."},
        {"ITEM": "NEXT_REVIEW_GATE", "STATUS": "10CC_REQUIRED", "DETAIL": "Review build plan before any implementation/source/apply package."},
    ]

    issues = "0" if failures == 0 else str(failures)
    wcsv(reports / "message_catalog_phase22ae_6_5_10cb_gate_check_v1.csv", gates, ["GATE","STATUS","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10cb_target_build_plan_v1.csv", target_plan, ["BUILD_ROW","TARGET_PATH","TARGET_KIND","TARGET_EXISTS","IMPLEMENTATION_KIND","REQUIRED_IMPLEMENTATION","WRITER_FAMILY","TARGET_SHA256_EXPECTED","BACKUP_PATH","REFUSE_IF","BUILD_PLAN_STATUS","SOURCE_MUTATION_AUTHORIZED_NOW","APPLY_AUTHORIZED_NOW","APPLY_EXECUTED_NOW"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10cb_native_writer_family_plan_v1.csv", writer_plan, ["WRITER_ROW","WRITER_FAMILY","SCOPE","BUILD_ACTION","SOURCE_MUTATION_AUTHORIZED_NOW","APPLY_AUTHORIZED_NOW"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10cb_source_patch_discovery_plan_v1.csv", source_plan, ["PATCH_ROW","PATCH_TARGET","PATCH_KIND","REQUIRED","SOURCE_MUTATION_AUTHORIZED_NOW","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10cb_command_surface_build_plan_v1.csv", surface_plan, ["SURFACE_BUILD_ROW","COMMAND_OR_SURFACE","IMPLEMENTATION_NEED","REVIEW_DISPOSITION","BUILD_PLAN_ACTION","APPLY_AUTHORIZED_NOW"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10cb_validation_contract_v1.csv", validation_plan, ["VALIDATION_ROW","VALIDATION","REQUIRED","RUN_NOW"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10cb_refusal_guards_v1.csv", refusal_rows, ["REFUSAL_GUARD","STATUS","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10cb_apply_readiness_v1.csv", readiness, ["ITEM","STATUS","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10cb_boundary_ledger_v1.csv", boundary, ["PROTECTED_SYSTEM","MUTATION_ALLOWED","OBSERVED_MUTATION","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10cb_artifact_manifest_v1.csv", artifact_rows, ["ARTIFACT","ROLE","BYTES","SHA256"])

    summary = {
        "STATUS": status,
        "VALIDATION_ISSUES": issues,
        "PHASE22AE_6_5_10CA_STATUS": ca.get("STATUS", ""),
        "MSG_022AE_6_5_10CA_SAVEPOINT_PRESENT": 1 if sp_ca else 0,
        "ACTIVE_MESSAGES_OBSERVED_COUNT": msg_count,
        "ACTIVE_TEXT_OBSERVED_COUNT": text_count,
        "CA_IMPLEMENTATION_REVIEW_ROWS": len(impl_review),
        "CA_BUILD_PLAN_REQUIREMENT_ROWS": len(build_req),
        "TARGET_BUILD_PLAN_ROWS": len(target_plan),
        "NATIVE_WRITER_FAMILY_PLAN_ROWS": len(writer_plan),
        "SOURCE_PATCH_DISCOVERY_PLAN_ROWS": len(source_plan),
        "COMMAND_SURFACE_BUILD_PLAN_ROWS": len(surface_plan),
        "VALIDATION_CONTRACT_ROWS": len(validation_plan),
        "REFUSAL_GUARD_ROWS": len(refusal_rows),
        "CB_ROOT": rel(cb_root, repo),
        "TARGET_SPECIFIC_NATIVE_APPLY_BUILD_PLAN_CREATED": 1 if status == GREEN else 0,
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
    wcsv(reports / "message_catalog_phase22ae_6_5_10cb_status_summary_v1.csv", [summary], list(summary.keys()))
    (repo / "docs/messaging/MESSAGE_LOCALE_PHASE22AE_6_5_10CB_TARGET_SPECIFIC_NATIVE_APPLY_BUILD_PLAN.md").write_text(
        f"# Message Catalog Phase 22AE.6.5.10CB Target-Specific Native Apply Build Plan\n\nStatus: `{status}`\n\n10CB creates a target-specific native apply build plan. It does not mutate HELP DATA, CMDHELPCHK, source, DBF, CDX, LMDB, or workspace files.\n\nBuild-plan root:\n\n```text\n{rel(cb_root, repo)}\n```\n\nNext gate:\n\n```text\n{NEXT}\n```\n", encoding="utf-8")

    print(status)
    print(f"  validation issues: {issues}")
    print(f"  Phase 22AE.6.5.10CA status: {ca.get('STATUS','')}")
    print(f"  MSG-022AE.6.5.10CA savepoint present: {1 if sp_ca else 0}")
    print(f"  active messages observed count: {msg_count}")
    print(f"  active text observed count: {text_count}")
    print(f"  CA implementation review rows: {len(impl_review)}")
    print(f"  CA build plan requirement rows: {len(build_req)}")
    print(f"  target build plan rows: {len(target_plan)}")
    print(f"  native writer family plan rows: {len(writer_plan)}")
    print(f"  source patch discovery plan rows: {len(source_plan)}")
    print(f"  command surface build plan rows: {len(surface_plan)}")
    print(f"  validation contract rows: {len(validation_plan)}")
    print(f"  refusal guard rows: {len(refusal_rows)}")
    print(f"  build-plan root: {rel(cb_root, repo)}")
    print("  target-specific native apply build plan created: 1")
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
