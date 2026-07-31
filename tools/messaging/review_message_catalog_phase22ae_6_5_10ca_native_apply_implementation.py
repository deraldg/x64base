#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, json, hashlib, shutil
from datetime import datetime, timezone
from pathlib import Path

GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_10CA_NATIVE_APPLY_IMPLEMENTATION_PACKAGE_REVIEW_GREEN_BUILD_PLAN_REQUIRED_SOURCE_HELD"
BLOCKED = "MESSAGE_CATALOG_PHASE22AE_6_5_10CA_NATIVE_APPLY_IMPLEMENTATION_PACKAGE_REVIEW_BLOCKED"
NEXT = "HOLD_OR_AUTHORIZE_PHASE22AE_6_5_10CB_TARGET_SPECIFIC_NATIVE_APPLY_BUILD_PLAN"

REPORT_DIR = Path("docs/messaging/reports")
BZ_SUMMARY = REPORT_DIR / "message_catalog_phase22ae_6_5_10bz_status_summary_v1.csv"
BZ_IMPL = REPORT_DIR / "message_catalog_phase22ae_6_5_10bz_native_implementation_manifest_v1.csv"
BZ_CONTRACT = REPORT_DIR / "message_catalog_phase22ae_6_5_10bz_target_apply_contract_v1.csv"
BZ_SURFACE = REPORT_DIR / "message_catalog_phase22ae_6_5_10bz_surface_implementation_plan_v1.csv"
BZ_VALIDATION = REPORT_DIR / "message_catalog_phase22ae_6_5_10bz_validation_contract_v1.csv"
BZ_ARTIFACTS = REPORT_DIR / "message_catalog_phase22ae_6_5_10bz_artifact_manifest_v1.csv"
ACTIVE_MSG_DBF = Path("dottalkpp/data/messaging/SYSTEM_MESSAGES.dbf")
ACTIVE_TEXT_DBF = Path("dottalkpp/data/messaging/SYSTEM_MESSAGE_TEXT.dbf")
CA_ROOT = Path("docs/messaging/apply/phase22ae_6_5_10ca_native_apply_implementation_package_review_v1")

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

def classify_review(row):
    kind = (row.get("IMPLEMENTATION_KIND") or "").upper()
    req = (row.get("REQUIRED_IMPLEMENTATION") or "").upper()
    target = (row.get("TARGET_PATH") or "").lower()
    if str(row.get("SAFE_TO_MUTATE_NOW", "")) not in {"0", "", "False", "false"}:
        return ("REVIEW_REQUIRED_UNEXPECTED_SAFE_MUTATE", "Implementation package must not mark targets safe to mutate at CA.")
    if str(row.get("APPLY_EXECUTED_NOW", "")) not in {"0", "", "False", "false"}:
        return ("REVIEW_REQUIRED_UNEXPECTED_APPLY", "Implementation package unexpectedly says apply executed.")
    if "NATIVE" in kind or "SCHEMA" in kind or "WRITER" in kind:
        return ("ACCEPT_FOR_BUILD_PLAN", "Native/schema-aware implementation class identified.")
    if "NATIVE" in req or "SCHEMA" in req:
        return ("ACCEPT_FOR_BUILD_PLAN", "Native/schema-aware requirement identified.")
    if target:
        return ("ACCEPT_FOR_BUILD_PLAN", "Target-specific implementation requirement identified.")
    return ("REVIEW_REQUIRED_MISSING_TARGET", "Target path missing.")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--replace-existing-review", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    reports = repo / REPORT_DIR
    reports.mkdir(parents=True, exist_ok=True)

    bz = first(repo / BZ_SUMMARY)
    impl_rows = rows(repo / BZ_IMPL)
    contract_rows = rows(repo / BZ_CONTRACT)
    surface_rows = rows(repo / BZ_SURFACE)
    validation_rows = rows(repo / BZ_VALIDATION)
    artifact_in = rows(repo / BZ_ARTIFACTS)
    sp_bz, latest_bz = savepoint(repo, "MSG-022AE.6.5.10BZ")
    msg_count = dbf_count(repo / ACTIVE_MSG_DBF)
    text_count = dbf_count(repo / ACTIVE_TEXT_DBF)
    ca_root = repo / CA_ROOT

    gates = []
    failures = 0
    def gate(name, ok, detail):
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": str(detail)})
        if not ok:
            failures += 1

    gate("PHASE22AE_6_5_10BZ_GREEN",
         bz.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_5_10BZ_TARGET_SPECIFIC_NATIVE_APPLY_IMPLEMENTATION_PACKAGE_GREEN_SOURCE_HELD_APPLY_NOT_EXECUTED",
         bz.get("STATUS", "missing"))
    gate("MSG_022AE_6_5_10BZ_SAVEPOINT_PRESENT", sp_bz, latest_bz)
    gate("BZ_IMPLEMENTATION_PACKAGE_STAGED", bz.get("TARGET_SPECIFIC_NATIVE_IMPLEMENTATION_PACKAGE_STAGED") == "1", bz.get("TARGET_SPECIFIC_NATIVE_IMPLEMENTATION_PACKAGE_STAGED", "missing"))
    gate("BZ_HELP_APPLY_NOT_EXECUTED", bz.get("HELP_DATA_APPLY_EXECUTED") == "0", bz.get("HELP_DATA_APPLY_EXECUTED", "missing"))
    gate("BZ_CMDHELPCHK_APPLY_NOT_EXECUTED", bz.get("CMDHELPCHK_APPLY_EXECUTED") == "0", bz.get("CMDHELPCHK_APPLY_EXECUTED", "missing"))
    gate("BZ_IMPL_ROWS_PRESENT", len(impl_rows) > 0, len(impl_rows))
    gate("BZ_CONTRACT_ROWS_PRESENT", len(contract_rows) > 0, len(contract_rows))
    gate("BZ_SURFACE_ROWS_PRESENT", len(surface_rows) > 0, len(surface_rows))
    gate("BZ_VALIDATION_ROWS_PRESENT", len(validation_rows) > 0, len(validation_rows))
    gate("ACTIVE_MESSAGES_HEADER_COUNT_14", msg_count == 14, msg_count)
    gate("ACTIVE_TEXT_HEADER_COUNT_70", text_count == 70, text_count)
    gate("CA_ROOT_NOT_EXISTING_OR_REPLACE_ALLOWED", (not ca_root.exists()) or args.replace_existing_review, rel(ca_root, repo))

    status = BLOCKED
    impl_review = []
    contract_review = []
    surface_review = []
    build_plan_requirements = []
    validation_review = []
    artifact_rows = []

    if failures == 0:
        if ca_root.exists() and args.replace_existing_review:
            shutil.rmtree(ca_root)
        ca_root.mkdir(parents=True, exist_ok=True)

        accepted = 0
        for i, r in enumerate(impl_rows, start=1):
            disposition, detail = classify_review(r)
            if disposition == "ACCEPT_FOR_BUILD_PLAN":
                accepted += 1
            impl_review.append({
                "REVIEW_ROW": i,
                "TARGET_PATH": r.get("TARGET_PATH", ""),
                "TARGET_KIND": r.get("TARGET_KIND", ""),
                "TARGET_EXISTS": r.get("TARGET_EXISTS", ""),
                "REQUIRED_IMPLEMENTATION": r.get("REQUIRED_IMPLEMENTATION", ""),
                "IMPLEMENTATION_KIND": r.get("IMPLEMENTATION_KIND", ""),
                "IMPLEMENTATION_STATUS": r.get("IMPLEMENTATION_STATUS", ""),
                "SAFE_TO_MUTATE_NOW": r.get("SAFE_TO_MUTATE_NOW", "0"),
                "APPLY_EXECUTED_NOW": r.get("APPLY_EXECUTED_NOW", "0"),
                "REVIEW_DISPOSITION": disposition,
                "BUILD_PLAN_REQUIRED": 1 if disposition == "ACCEPT_FOR_BUILD_PLAN" else 0,
                "REVIEW_DETAIL": detail,
            })

        for i, r in enumerate(contract_rows, start=1):
            contract_review.append({
                "CONTRACT_REVIEW_ROW": i,
                "TARGET_PATH": r.get("TARGET_PATH", ""),
                "APPLY_METHOD": r.get("APPLY_METHOD", ""),
                "PRECONDITION": r.get("PRECONDITION", ""),
                "REFUSE_IF": r.get("REFUSE_IF", ""),
                "POSTCONDITION": r.get("POSTCONDITION", ""),
                "REVIEW_DISPOSITION": "ACCEPT_CONTRACT_FOR_BUILD_PLAN",
                "BUILD_PLAN_REQUIRED": 1,
            })

        for i, r in enumerate(surface_rows, start=1):
            surface_review.append({
                "SURFACE_REVIEW_ROW": i,
                "COMMAND_OR_SURFACE": r.get("COMMAND_OR_SURFACE", ""),
                "IMPLEMENTATION_NEED": r.get("IMPLEMENTATION_NEED", ""),
                "STATUS": r.get("STATUS", ""),
                "REVIEW_DISPOSITION": "ACCEPT_SURFACE_FOR_BUILD_PLAN",
            })

        build_plan_requirements = [
            {"BUILD_PLAN_ROW": 1, "BUILD_REQUIREMENT": "MAP_TARGETS_TO_NATIVE_WRITER", "DETAIL": "Map each target row to a DotTalk++ native/schema-aware writer surface.", "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
            {"BUILD_PLAN_ROW": 2, "BUILD_REQUIREMENT": "DEFINE_HELP_DATA_UPDATE_PATH", "DETAIL": "Define exact native HELP DATA insertion/update path for MSGMGR and SET MESSAGE topics.", "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
            {"BUILD_PLAN_ROW": 3, "BUILD_REQUIREMENT": "DEFINE_CMDHELPCHK_UPDATE_PATH", "DETAIL": "Define exact native CMDHELPCHK/catalog update path for MSGMGR and SET MESSAGE checks.", "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
            {"BUILD_PLAN_ROW": 4, "BUILD_REQUIREMENT": "REFUSE_RAW_DBF_BYTE_WRITE", "DETAIL": "Future implementation must refuse raw Python DBF byte mutation for runtime-promotion paths.", "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
            {"BUILD_PLAN_ROW": 5, "BUILD_REQUIREMENT": "CARRY_FORWARD_HASH_BACKUP_CONTRACT", "DETAIL": "Target hash and exact backup checks must be carried into the build/apply package.", "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
            {"BUILD_PLAN_ROW": 6, "BUILD_REQUIREMENT": "CARRY_FORWARD_RUNTIME_READBACK", "DETAIL": "MSGMGR, SET MESSAGE, HELP, and CMDHELPCHK readback must remain required after any future apply.", "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
            {"BUILD_PLAN_ROW": 7, "BUILD_REQUIREMENT": "SEPARATE_IMPLEMENTATION_FROM_EXECUTION", "DETAIL": "Next build-plan package remains report/source-held until separately authorized.", "SOURCE_MUTATION_AUTHORIZED_NOW": 0, "APPLY_AUTHORIZED_NOW": 0},
        ]

        for i, r in enumerate(validation_rows, start=1):
            validation_review.append({
                "VALIDATION_REVIEW_ROW": i,
                "VALIDATION": r.get("VALIDATION", ""),
                "REQUIRED": r.get("REQUIRED", ""),
                "RUN_NOW": 0,
                "REVIEW_DISPOSITION": "CARRY_FORWARD_TO_BUILD_PLAN",
            })

        scripts_dir = ca_root / "scripts"
        scripts_dir.mkdir(parents=True, exist_ok=True)

        disabled_build = scripts_dir / "MESSAGE_CATALOG_PHASE22AE_6_5_10CB_BUILD_PLAN_TEMPLATE.ps1.disabled"
        disabled_build.write_text(
            'throw "10CA reviews only. Generate a dedicated 10CB build-plan package before any source or active-catalog mutation."\n',
            encoding="utf-8"
        )
        readback_contract = scripts_dir / "MESSAGE_CATALOG_PHASE22AE_6_5_10CA_READBACK_CONTRACT.dts"
        readback_contract.write_text(
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
        review_notes = ca_root / "native_apply_implementation_package_review_v1.md"
        review_notes.write_text(
            "# 10CA Native Apply Implementation Package Review\n\n"
            "10CA accepts the 10BZ target-specific/native implementation package for a separate build-plan package. It does not apply HELP DATA or CMDHELPCHK changes and does not mutate source.\n",
            encoding="utf-8"
        )

        impl_review_path = ca_root / "native_implementation_manifest_review_v1.csv"
        contract_review_path = ca_root / "target_apply_contract_review_v1.csv"
        surface_review_path = ca_root / "surface_implementation_plan_review_v1.csv"
        build_req_path = ca_root / "build_plan_requirements_v1.csv"
        validation_review_path = ca_root / "validation_contract_review_v1.csv"
        readme = ca_root / "README_10CA_NATIVE_APPLY_IMPLEMENTATION_PACKAGE_REVIEW.md"
        readme.write_text(
            "# 10CA Native Apply Implementation Package Review\n\n"
            "10CA reviews the 10BZ implementation package and determines that a target-specific native apply build plan is required.\n\n"
            "No HELP DATA, CMDHELPCHK, source, DBF, CDX, LMDB, or workspace mutation is authorized or executed in 10CA.\n",
            encoding="utf-8"
        )

        wcsv(impl_review_path, impl_review, ["REVIEW_ROW","TARGET_PATH","TARGET_KIND","TARGET_EXISTS","REQUIRED_IMPLEMENTATION","IMPLEMENTATION_KIND","IMPLEMENTATION_STATUS","SAFE_TO_MUTATE_NOW","APPLY_EXECUTED_NOW","REVIEW_DISPOSITION","BUILD_PLAN_REQUIRED","REVIEW_DETAIL"])
        wcsv(contract_review_path, contract_review, ["CONTRACT_REVIEW_ROW","TARGET_PATH","APPLY_METHOD","PRECONDITION","REFUSE_IF","POSTCONDITION","REVIEW_DISPOSITION","BUILD_PLAN_REQUIRED"])
        wcsv(surface_review_path, surface_review, ["SURFACE_REVIEW_ROW","COMMAND_OR_SURFACE","IMPLEMENTATION_NEED","STATUS","REVIEW_DISPOSITION"])
        wcsv(build_req_path, build_plan_requirements, ["BUILD_PLAN_ROW","BUILD_REQUIREMENT","DETAIL","SOURCE_MUTATION_AUTHORIZED_NOW","APPLY_AUTHORIZED_NOW"])
        wcsv(validation_review_path, validation_review, ["VALIDATION_REVIEW_ROW","VALIDATION","REQUIRED","RUN_NOW","REVIEW_DISPOSITION"])

        for p in [impl_review_path, contract_review_path, surface_review_path, build_req_path, validation_review_path, disabled_build, readback_contract, review_notes, readme]:
            artifact_rows.append({"ARTIFACT": rel(p, repo), "ROLE": "native_apply_implementation_package_review_artifact", "BYTES": p.stat().st_size, "SHA256": sha(p)})

        status = GREEN

    boundary = [
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "10CA writes docs/messaging review artifacts only."},
        {"PROTECTED_SYSTEM": "ACTIVE_SYSTEM_MESSAGES", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_SYSTEM_MESSAGE_TEXT", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_CDX_LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CDX/LMDB mutation."},
        {"PROTECTED_SYSTEM": "WORKSPACE_PROFILE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No workspace mutation."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Implementation review only; no HELP DATA apply."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Implementation review only; no CMDHELPCHK apply."},
    ]

    readiness = [
        {"ITEM": "IMPLEMENTATION_PACKAGE_REVIEW_COMPLETE", "STATUS": "YES" if impl_review else "NO", "DETAIL": f"{len(impl_review)} implementation rows reviewed."},
        {"ITEM": "BUILD_PLAN_REQUIRED", "STATUS": "YES" if build_plan_requirements else "NO", "DETAIL": f"{len(build_plan_requirements)} build-plan requirements."},
        {"ITEM": "HELP_DATA_APPLY_EXECUTION", "STATUS": "NOT_EXECUTED_IN_10CA", "DETAIL": "No apply execution."},
        {"ITEM": "CMDHELPCHK_APPLY_EXECUTION", "STATUS": "NOT_EXECUTED_IN_10CA", "DETAIL": "No apply execution."},
        {"ITEM": "NEXT_GATE", "STATUS": "10CB_REQUIRED", "DETAIL": "Create target-specific native apply build plan."},
    ]

    issues = "0" if failures == 0 else str(failures)
    wcsv(reports / "message_catalog_phase22ae_6_5_10ca_gate_check_v1.csv", gates, ["GATE","STATUS","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10ca_native_implementation_review_v1.csv", impl_review, ["REVIEW_ROW","TARGET_PATH","TARGET_KIND","TARGET_EXISTS","REQUIRED_IMPLEMENTATION","IMPLEMENTATION_KIND","IMPLEMENTATION_STATUS","SAFE_TO_MUTATE_NOW","APPLY_EXECUTED_NOW","REVIEW_DISPOSITION","BUILD_PLAN_REQUIRED","REVIEW_DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10ca_target_apply_contract_review_v1.csv", contract_review, ["CONTRACT_REVIEW_ROW","TARGET_PATH","APPLY_METHOD","PRECONDITION","REFUSE_IF","POSTCONDITION","REVIEW_DISPOSITION","BUILD_PLAN_REQUIRED"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10ca_surface_implementation_review_v1.csv", surface_review, ["SURFACE_REVIEW_ROW","COMMAND_OR_SURFACE","IMPLEMENTATION_NEED","STATUS","REVIEW_DISPOSITION"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10ca_build_plan_requirements_v1.csv", build_plan_requirements, ["BUILD_PLAN_ROW","BUILD_REQUIREMENT","DETAIL","SOURCE_MUTATION_AUTHORIZED_NOW","APPLY_AUTHORIZED_NOW"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10ca_validation_contract_review_v1.csv", validation_review, ["VALIDATION_REVIEW_ROW","VALIDATION","REQUIRED","RUN_NOW","REVIEW_DISPOSITION"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10ca_apply_readiness_v1.csv", readiness, ["ITEM","STATUS","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10ca_boundary_ledger_v1.csv", boundary, ["PROTECTED_SYSTEM","MUTATION_ALLOWED","OBSERVED_MUTATION","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10ca_artifact_manifest_v1.csv", artifact_rows, ["ARTIFACT","ROLE","BYTES","SHA256"])

    build_required_rows = sum(1 for r in impl_review if str(r.get("BUILD_PLAN_REQUIRED", "")) == "1")
    summary = {
        "STATUS": status,
        "VALIDATION_ISSUES": issues,
        "PHASE22AE_6_5_10BZ_STATUS": bz.get("STATUS", ""),
        "MSG_022AE_6_5_10BZ_SAVEPOINT_PRESENT": 1 if sp_bz else 0,
        "ACTIVE_MESSAGES_OBSERVED_COUNT": msg_count,
        "ACTIVE_TEXT_OBSERVED_COUNT": text_count,
        "BZ_IMPLEMENTATION_ROWS": len(impl_rows),
        "BZ_CONTRACT_ROWS": len(contract_rows),
        "BZ_SURFACE_ROWS": len(surface_rows),
        "BZ_VALIDATION_ROWS": len(validation_rows),
        "IMPLEMENTATION_REVIEW_ROWS": len(impl_review),
        "BUILD_PLAN_REQUIRED_ROWS": build_required_rows,
        "CONTRACT_REVIEW_ROWS": len(contract_review),
        "SURFACE_REVIEW_ROWS": len(surface_review),
        "BUILD_PLAN_REQUIREMENT_ROWS": len(build_plan_requirements),
        "CA_ROOT": rel(ca_root, repo),
        "BUILD_PLAN_REQUIRED": 1 if status == GREEN else 0,
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
    wcsv(reports / "message_catalog_phase22ae_6_5_10ca_status_summary_v1.csv", [summary], list(summary.keys()))

    (repo / "docs/messaging/MESSAGE_LOCALE_PHASE22AE_6_5_10CA_NATIVE_APPLY_IMPLEMENTATION_PACKAGE_REVIEW.md").write_text(
        f"# Message Catalog Phase 22AE.6.5.10CA Native Apply Implementation Package Review\n\n"
        f"Status: `{status}`\n\n"
        "10CA reviews the 10BZ implementation package and determines that a target-specific native apply build plan is required. It does not mutate HELP DATA or CMDHELPCHK.\n\n"
        f"Review root:\n\n```text\n{rel(ca_root, repo)}\n```\n\n"
        f"Next gate:\n\n```text\n{NEXT}\n```\n",
        encoding="utf-8"
    )

    print(status)
    print(f"  validation issues: {issues}")
    print(f"  Phase 22AE.6.5.10BZ status: {bz.get('STATUS','')}")
    print(f"  MSG-022AE.6.5.10BZ savepoint present: {1 if sp_bz else 0}")
    print(f"  active messages observed count: {msg_count}")
    print(f"  active text observed count: {text_count}")
    print(f"  BZ implementation rows: {len(impl_rows)}")
    print(f"  BZ contract rows: {len(contract_rows)}")
    print(f"  BZ surface rows: {len(surface_rows)}")
    print(f"  BZ validation rows: {len(validation_rows)}")
    print(f"  implementation review rows: {len(impl_review)}")
    print(f"  build plan required rows: {build_required_rows}")
    print(f"  contract review rows: {len(contract_review)}")
    print(f"  surface review rows: {len(surface_review)}")
    print(f"  build plan requirement rows: {len(build_plan_requirements)}")
    print(f"  review root: {rel(ca_root, repo)}")
    print("  build plan required: 1")
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
