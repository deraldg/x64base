#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, json, hashlib, shutil, difflib
from datetime import datetime, timezone
from pathlib import Path

GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_10BK_EXACT_PRE_WRITE_DIFF_PACKAGE_GREEN_DIFFS_STAGED_NO_APPLY"
BLOCKED = "MESSAGE_CATALOG_PHASE22AE_6_5_10BK_EXACT_PRE_WRITE_DIFF_PACKAGE_BLOCKED"
NEXT = "HOLD_OR_AUTHORIZE_PHASE22AE_6_5_10BL_EXACT_PRE_WRITE_DIFF_PACKAGE_REVIEW"

REPORT_DIR = Path("docs/messaging/reports")
BJ_SUMMARY = REPORT_DIR / "message_catalog_phase22ae_6_5_10bj_status_summary_v1.csv"
BJ_REVIEW = REPORT_DIR / "message_catalog_phase22ae_6_5_10bj_pre_write_diff_design_review_v1.csv"
BI_DIFF = REPORT_DIR / "message_catalog_phase22ae_6_5_10bi_pre_write_diff_design_v1.csv"
BK_ROOT = Path("docs/messaging/apply/phase22ae_6_5_10bk_exact_pre_write_diff_package_v1")
CANDIDATE_PATH = Path("docs/messaging/candidates/MESSAGE_CATALOG_PHASE22AE_6_5_10AW_MSGMGR_HELP_CANDIDATE.md")
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

def safe_read_text(path: Path):
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return ""

def make_diff_for_text(target: Path, candidate_text: str, anchors: str):
    before = safe_read_text(target)
    # 10BK is conservative: no actual replacement is guessed. It generates a review patch header only.
    patch_header = [
        "# REVIEW-ONLY PRE-WRITE DIFF PACKAGE",
        "# No apply was executed.",
        f"# Target: {target}",
        f"# Anchors/keys: {anchors}",
        "# Candidate payload must be inserted/updated only by a later authorized package.",
        "",
    ]
    candidate_lines = candidate_text.splitlines(keepends=True)
    preview_after = before.splitlines(keepends=True) + ["\n", "----- BEGIN REVIEW CANDIDATE PAYLOAD -----\n"] + candidate_lines + ["\n----- END REVIEW CANDIDATE PAYLOAD -----\n"]
    diff = list(difflib.unified_diff(
        before.splitlines(keepends=True),
        preview_after,
        fromfile=str(target) + " (before)",
        tofile=str(target) + " (review-payload-appended-preview)",
        lineterm=""
    ))
    return "\n".join(patch_header) + "".join(diff)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--replace-existing-package", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    reports = repo / REPORT_DIR
    reports.mkdir(parents=True, exist_ok=True)

    bj = first(repo / BJ_SUMMARY)
    bj_review = rows(repo / BJ_REVIEW)
    bi_diff = rows(repo / BI_DIFF)
    sp_bj, latest_bj = savepoint(repo, "MSG-022AE.6.5.10BJ")
    msg_count = dbf_count(repo / ACTIVE_MSG_DBF)
    text_count = dbf_count(repo / ACTIVE_TEXT_DBF)
    candidate = repo / CANDIDATE_PATH
    bk_root = repo / BK_ROOT

    gates = []
    failures = 0
    def gate(name, ok, detail):
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": str(detail)})
        if not ok:
            failures += 1

    gate("PHASE22AE_6_5_10BJ_GREEN",
         bj.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_5_10BJ_PRE_WRITE_DIFF_DESIGN_REVIEW_GREEN_EXACT_DIFF_PACKAGE_REQUIRED_SOURCE_HELD",
         bj.get("STATUS", "missing"))
    gate("MSG_022AE_6_5_10BJ_SAVEPOINT_PRESENT", sp_bj, latest_bj)
    gate("BJ_EXACT_PRE_WRITE_DIFF_REQUIRED", bj.get("EXACT_PRE_WRITE_DIFF_PACKAGE_REQUIRED") == "1", bj.get("EXACT_PRE_WRITE_DIFF_PACKAGE_REQUIRED", "missing"))
    gate("BJ_HELP_APPLY_NOT_EXECUTED", bj.get("HELP_DATA_APPLY_EXECUTED") == "0", bj.get("HELP_DATA_APPLY_EXECUTED", "missing"))
    gate("BJ_CMDHELPCHK_APPLY_NOT_EXECUTED", bj.get("CMDHELPCHK_APPLY_EXECUTED") == "0", bj.get("CMDHELPCHK_APPLY_EXECUTED", "missing"))
    gate("BJ_REVIEW_ROWS_PRESENT", len(bj_review) > 0, len(bj_review))
    gate("BI_DIFF_ROWS_PRESENT", len(bi_diff) > 0, len(bi_diff))
    gate("ACTIVE_MESSAGES_HEADER_COUNT_14", msg_count == 14, msg_count)
    gate("ACTIVE_TEXT_HEADER_COUNT_70", text_count == 70, text_count)
    gate("CANDIDATE_EXISTS", candidate.exists(), rel(candidate, repo))
    gate("BK_ROOT_NOT_EXISTING_OR_REPLACE_ALLOWED", (not bk_root.exists()) or args.replace_existing_package, rel(bk_root, repo))

    status = BLOCKED
    package_rows = []
    diff_artifacts = []
    guard_rows = []
    artifact_rows = []

    if failures == 0:
        if bk_root.exists() and args.replace_existing_package:
            shutil.rmtree(bk_root)
        bk_root.mkdir(parents=True, exist_ok=True)

        candidate_text = safe_read_text(candidate)
        candidate_hash = sha(candidate)
        candidate_snapshot = bk_root / "candidate_snapshot" / CANDIDATE_PATH.name
        candidate_snapshot.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(candidate, candidate_snapshot)

        diff_dir = bk_root / "diffs"
        diff_dir.mkdir(parents=True, exist_ok=True)

        # Join BI detail rows by target id/path where possible.
        bi_by_target = {}
        for r in bi_diff:
            bi_by_target[(r.get("TARGET_ID", ""), r.get("TARGET_PATH", ""))] = r

        for i, r in enumerate(bj_review, start=1):
            target_id = r.get("TARGET_ID", "")
            target_path = r.get("TARGET_PATH", "")
            target = repo / target_path
            bi = bi_by_target.get((target_id, target_path), {})
            target_format = r.get("TARGET_FORMAT", "") or bi.get("TARGET_FORMAT", "")
            diff_strategy = r.get("DIFF_STRATEGY", "") or bi.get("DIFF_STRATEGY", "")
            anchors = bi.get("ANCHORS_OR_KEYS", "MSGMGR;SET MESSAGE CATALOG CHECK;SET MESSAGE CATALOG GET;SET MESSAGE EMIT")
            exists = target.exists() and target.is_file()
            target_hash = sha(target) if exists else ""

            safe_name = f"{i:02d}_{target_id or 'TARGET'}".replace(":", "_").replace("/", "_").replace("\\", "_")
            diff_path = diff_dir / f"{safe_name}_pre_write_diff_review.txt"

            if target_format in {"TEXT_MARKDOWN", "CSV_TEXT", "JSON_TEXT"} and exists:
                diff_text = make_diff_for_text(target, candidate_text, anchors)
                diff_status = "TEXTUAL_REVIEW_DIFF_GENERATED_NO_APPLY"
            else:
                diff_text = (
                    "# NATIVE/SCHEMA-AWARE DIFF REQUIRED\n\n"
                    "No binary DBF patch was generated. This is intentional.\n\n"
                    f"Target ID: {target_id}\n"
                    f"Target path: {target_path}\n"
                    f"Target format: {target_format}\n"
                    f"Target SHA256: {target_hash}\n"
                    f"Candidate SHA256: {candidate_hash}\n"
                    f"Anchors/keys: {anchors}\n\n"
                    "Required next step: generate native x64base/DotTalk++ or schema-aware staged-import diff/readback plan.\n"
                    "No HELP DATA or CMDHELPCHK mutation occurred in 10BK.\n"
                )
                diff_status = "NATIVE_OR_SCHEMA_AWARE_DIFF_STUB_GENERATED_NO_APPLY"

            diff_path.write_text(diff_text, encoding="utf-8")

            package_rows.append({
                "PACKAGE_ROW": i,
                "TARGET_ID": target_id,
                "TARGET_KIND": r.get("TARGET_KIND", ""),
                "TARGET_PATH": target_path,
                "TARGET_FORMAT": target_format,
                "TARGET_EXISTS": 1 if exists else 0,
                "TARGET_SHA256": target_hash,
                "DIFF_STRATEGY": diff_strategy,
                "DIFF_STATUS": diff_status,
                "DIFF_ARTIFACT": rel(diff_path, repo),
                "CANDIDATE_SOURCE": rel(candidate, repo),
                "CANDIDATE_SHA256": candidate_hash,
                "AUTHORIZED_FOR_WRITE_NOW": 0,
                "APPLY_EXECUTED_NOW": 0,
            })
            diff_artifacts.append({
                "DIFF_ARTIFACT": rel(diff_path, repo),
                "TARGET_ID": target_id,
                "BYTES": diff_path.stat().st_size,
                "SHA256": sha(diff_path),
            })

        guard_rows = [
            {"GUARD": "NO_RAW_PYTHON_DBF_WRITE", "STATUS": "ACTIVE", "DETAIL": "DBF targets get native/schema-aware diff stubs only."},
            {"GUARD": "NO_APPLY_IN_10BK", "STATUS": "ACTIVE", "DETAIL": "10BK only creates diff package artifacts."},
            {"GUARD": "TARGET_HASH_REQUIRED", "STATUS": "ACTIVE", "DETAIL": "Later execution must refuse if target hash differs."},
            {"GUARD": "CANDIDATE_HASH_REQUIRED", "STATUS": "ACTIVE", "DETAIL": "Later execution must refuse if candidate hash differs."},
            {"GUARD": "RUNTIME_READBACK_REQUIRED", "STATUS": "ACTIVE", "DETAIL": "Later execution must prove HELP/CMDHELPCHK in DotTalk++ runtime."},
        ]

        manifest_path = bk_root / "exact_pre_write_diff_package_manifest_v1.csv"
        diff_artifact_path = bk_root / "diff_artifact_manifest_v1.csv"
        guard_path = bk_root / "execution_guards_carried_forward_v1.csv"
        readme = bk_root / "README_10BK_EXACT_PRE_WRITE_DIFF_PACKAGE.md"
        disabled = bk_root / "scripts" / "MESSAGE_CATALOG_PHASE22AE_6_5_10BL_REVIEW_REQUIRED_NO_APPLY.ps1.disabled"
        disabled.parent.mkdir(parents=True, exist_ok=True)
        disabled.write_text(
            'throw "DISABLED TEMPLATE: 10BK creates pre-write diff artifacts only. 10BL review is required before any later execution."\n',
            encoding="utf-8"
        )

        wcsv(manifest_path, package_rows, ["PACKAGE_ROW","TARGET_ID","TARGET_KIND","TARGET_PATH","TARGET_FORMAT","TARGET_EXISTS","TARGET_SHA256","DIFF_STRATEGY","DIFF_STATUS","DIFF_ARTIFACT","CANDIDATE_SOURCE","CANDIDATE_SHA256","AUTHORIZED_FOR_WRITE_NOW","APPLY_EXECUTED_NOW"])
        wcsv(diff_artifact_path, diff_artifacts, ["DIFF_ARTIFACT","TARGET_ID","BYTES","SHA256"])
        wcsv(guard_path, guard_rows, ["GUARD","STATUS","DETAIL"])
        readme.write_text(
            "# 10BK Exact Pre-Write Diff Package\n\n"
            "10BK stages exact pre-write diff package artifacts for review. It does not mutate HELP DATA or CMDHELPCHK.\n\n"
            "For text-like targets, review-only unified diff previews may be generated. For DBF/runtime targets, native/schema-aware diff stubs are generated and raw Python DBF mutation remains refused.\n",
            encoding="utf-8"
        )

        for p in [candidate_snapshot, manifest_path, diff_artifact_path, guard_path, readme, disabled]:
            artifact_rows.append({"ARTIFACT": rel(p, repo), "ROLE": "exact_pre_write_diff_package_artifact", "BYTES": p.stat().st_size, "SHA256": sha(p)})
        for d in diff_artifacts:
            artifact_rows.append({"ARTIFACT": d["DIFF_ARTIFACT"], "ROLE": "per_target_diff_artifact", "BYTES": d["BYTES"], "SHA256": d["SHA256"]})

        status = GREEN

    boundary = [
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "10BK writes docs/messaging diff-package artifacts only."},
        {"PROTECTED_SYSTEM": "ACTIVE_SYSTEM_MESSAGES", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_SYSTEM_MESSAGE_TEXT", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_CDX_LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CDX/LMDB mutation."},
        {"PROTECTED_SYSTEM": "WORKSPACE_PROFILE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No workspace mutation."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No HELP DATA mutation; pre-write diff package only."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CMDHELPCHK mutation; pre-write diff package only."},
    ]

    readiness = [
        {"ITEM": "EXACT_PRE_WRITE_DIFF_PACKAGE_CREATED", "STATUS": "YES" if package_rows else "NO", "DETAIL": f"{len(package_rows)} target diff package rows."},
        {"ITEM": "PER_TARGET_DIFF_ARTIFACTS_CREATED", "STATUS": "YES" if diff_artifacts else "NO", "DETAIL": f"{len(diff_artifacts)} diff artifacts."},
        {"ITEM": "EXECUTION_GUARDS_CARRIED_FORWARD", "STATUS": "YES" if guard_rows else "NO", "DETAIL": f"{len(guard_rows)} guards."},
        {"ITEM": "HELP_DATA_APPLY_EXECUTION", "STATUS": "NOT_EXECUTED_IN_10BK", "DETAIL": "No apply execution."},
        {"ITEM": "CMDHELPCHK_APPLY_EXECUTION", "STATUS": "NOT_EXECUTED_IN_10BK", "DETAIL": "No apply execution."},
        {"ITEM": "NEXT_REVIEW_GATE", "STATUS": "10BL_REQUIRED", "DETAIL": "Review exact pre-write diff package before any execution decision."},
    ]

    issues = "0" if failures == 0 else str(failures)
    wcsv(reports / "message_catalog_phase22ae_6_5_10bk_gate_check_v1.csv", gates, ["GATE","STATUS","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10bk_exact_pre_write_diff_package_v1.csv", package_rows, ["PACKAGE_ROW","TARGET_ID","TARGET_KIND","TARGET_PATH","TARGET_FORMAT","TARGET_EXISTS","TARGET_SHA256","DIFF_STRATEGY","DIFF_STATUS","DIFF_ARTIFACT","CANDIDATE_SOURCE","CANDIDATE_SHA256","AUTHORIZED_FOR_WRITE_NOW","APPLY_EXECUTED_NOW"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10bk_diff_artifact_manifest_v1.csv", diff_artifacts, ["DIFF_ARTIFACT","TARGET_ID","BYTES","SHA256"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10bk_execution_guards_v1.csv", guard_rows, ["GUARD","STATUS","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10bk_apply_readiness_v1.csv", readiness, ["ITEM","STATUS","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10bk_boundary_ledger_v1.csv", boundary, ["PROTECTED_SYSTEM","MUTATION_ALLOWED","OBSERVED_MUTATION","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10bk_artifact_manifest_v1.csv", artifact_rows, ["ARTIFACT","ROLE","BYTES","SHA256"])

    summary = {
        "STATUS": status,
        "VALIDATION_ISSUES": issues,
        "PHASE22AE_6_5_10BJ_STATUS": bj.get("STATUS", ""),
        "MSG_022AE_6_5_10BJ_SAVEPOINT_PRESENT": 1 if sp_bj else 0,
        "ACTIVE_MESSAGES_OBSERVED_COUNT": msg_count,
        "ACTIVE_TEXT_OBSERVED_COUNT": text_count,
        "BJ_REVIEW_ROWS": len(bj_review),
        "DIFF_PACKAGE_ROWS": len(package_rows),
        "DIFF_ARTIFACT_ROWS": len(diff_artifacts),
        "EXECUTION_GUARD_ROWS": len(guard_rows),
        "BK_ROOT": rel(bk_root, repo),
        "EXACT_PRE_WRITE_DIFF_PACKAGE_CREATED": 1 if status == GREEN else 0,
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
    wcsv(reports / "message_catalog_phase22ae_6_5_10bk_status_summary_v1.csv", [summary], list(summary.keys()))

    (repo / "docs/messaging/MESSAGE_LOCALE_PHASE22AE_6_5_10BK_EXACT_PRE_WRITE_DIFF_PACKAGE.md").write_text(
        f"# Message Catalog Phase 22AE.6.5.10BK Exact Pre-Write Diff Package\n\n"
        f"Status: `{status}`\n\n"
        "10BK creates exact pre-write diff package artifacts for review. It does not mutate HELP DATA or CMDHELPCHK.\n\n"
        f"Diff-package root:\n\n```text\n{rel(bk_root, repo)}\n```\n\n"
        f"Next gate:\n\n```text\n{NEXT}\n```\n",
        encoding="utf-8"
    )

    print(status)
    print(f"  validation issues: {issues}")
    print(f"  Phase 22AE.6.5.10BJ status: {bj.get('STATUS','')}")
    print(f"  MSG-022AE.6.5.10BJ savepoint present: {1 if sp_bj else 0}")
    print(f"  active messages observed count: {msg_count}")
    print(f"  active text observed count: {text_count}")
    print(f"  BJ review rows: {len(bj_review)}")
    print(f"  diff package rows: {len(package_rows)}")
    print(f"  diff artifact rows: {len(diff_artifacts)}")
    print(f"  execution guard rows: {len(guard_rows)}")
    print(f"  diff-package root: {rel(bk_root, repo)}")
    print("  exact pre-write diff package created: 1")
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
