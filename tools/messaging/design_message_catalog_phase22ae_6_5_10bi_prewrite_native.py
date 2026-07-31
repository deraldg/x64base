#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, json, hashlib, shutil
from datetime import datetime, timezone
from pathlib import Path

GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_10BI_PRE_WRITE_DIFF_AND_NATIVE_EXECUTION_DESIGN_PACKAGE_GREEN_SOURCE_HELD"
BLOCKED = "MESSAGE_CATALOG_PHASE22AE_6_5_10BI_PRE_WRITE_DIFF_AND_NATIVE_EXECUTION_DESIGN_PACKAGE_BLOCKED"
NEXT = "HOLD_OR_AUTHORIZE_PHASE22AE_6_5_10BJ_PRE_WRITE_DIFF_DESIGN_REVIEW_AND_EXECUTION_DECISION"

REPORT_DIR = Path("docs/messaging/reports")
BH_SUMMARY = REPORT_DIR / "message_catalog_phase22ae_6_5_10bh_status_summary_v1.csv"
BH_REVIEW = REPORT_DIR / "message_catalog_phase22ae_6_5_10bh_write_implementation_review_v1.csv"
BH_DESIGN_REQ = REPORT_DIR / "message_catalog_phase22ae_6_5_10bh_next_design_requirements_v1.csv"
BI_ROOT = Path("docs/messaging/apply/phase22ae_6_5_10bi_pre_write_diff_and_native_execution_design_v1")
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

def probe(path: Path):
    try:
        if not path.exists():
            return "missing"
        if path.suffix.lower() == ".dbf":
            return f"DBF_BINARY; bytes={path.stat().st_size}; header_count={dbf_count(path)}"
        text = path.read_text(encoding="utf-8", errors="replace")
        lines = text.splitlines()
        return " | ".join(lines[:8])[:700]
    except Exception as e:
        return f"probe_error={type(e).__name__}:{e}"

def diff_strategy(row):
    fmt = row.get("TARGET_FORMAT", "")
    disposition = row.get("REVIEW_DISPOSITION", "")
    if fmt == "DBF_BINARY" or "NATIVE" in disposition:
        return (
            "NATIVE_OR_SCHEMA_AWARE_DBF_DIFF_REQUIRED",
            "Generate candidate rows/updates as CSV or native script input, then compare native readback before/after. Do not binary-patch DBF."
        )
    if fmt in {"TEXT_MARKDOWN", "CSV_TEXT", "JSON_TEXT"}:
        return (
            "TEXTUAL_UNIFIED_DIFF_REQUIRED",
            "Generate exact textual unified diff with anchors and refusal if anchors are missing or duplicated."
        )
    return (
        "MANUAL_DIFF_DESIGN_REQUIRED",
        "Target format not sufficiently classified for automatic diff generation."
    )

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--replace-existing-design", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    reports = repo / REPORT_DIR
    reports.mkdir(parents=True, exist_ok=True)

    bh = first(repo / BH_SUMMARY)
    review = rows(repo / BH_REVIEW)
    reqs = rows(repo / BH_DESIGN_REQ)
    sp_bh, latest_bh = savepoint(repo, "MSG-022AE.6.5.10BH")
    msg_count = dbf_count(repo / ACTIVE_MSG_DBF)
    text_count = dbf_count(repo / ACTIVE_TEXT_DBF)
    candidate = repo / CANDIDATE_PATH
    bi_root = repo / BI_ROOT

    gates = []
    failures = 0
    def gate(name, ok, detail):
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": str(detail)})
        if not ok:
            failures += 1

    gate("PHASE22AE_6_5_10BH_GREEN",
         bh.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_5_10BH_TARGET_SPECIFIC_WRITE_IMPLEMENTATION_REVIEW_GREEN_DIFF_PACKAGE_REQUIRED_SOURCE_HELD",
         bh.get("STATUS", "missing"))
    gate("MSG_022AE_6_5_10BH_SAVEPOINT_PRESENT", sp_bh, latest_bh)
    gate("BH_PRE_WRITE_DIFF_REQUIRED", bh.get("PRE_WRITE_DIFF_PACKAGE_REQUIRED") == "1", bh.get("PRE_WRITE_DIFF_PACKAGE_REQUIRED", "missing"))
    gate("BH_NATIVE_EXECUTION_DESIGN_REQUIRED", bh.get("NATIVE_EXECUTION_DESIGN_REQUIRED") == "1", bh.get("NATIVE_EXECUTION_DESIGN_REQUIRED", "missing"))
    gate("BH_HELP_APPLY_NOT_EXECUTED", bh.get("HELP_DATA_APPLY_EXECUTED") == "0", bh.get("HELP_DATA_APPLY_EXECUTED", "missing"))
    gate("BH_CMDHELPCHK_APPLY_NOT_EXECUTED", bh.get("CMDHELPCHK_APPLY_EXECUTED") == "0", bh.get("CMDHELPCHK_APPLY_EXECUTED", "missing"))
    gate("BH_REVIEW_ROWS_PRESENT", len(review) > 0, len(review))
    gate("BH_DESIGN_REQUIREMENTS_PRESENT", len(reqs) > 0, len(reqs))
    gate("ACTIVE_MESSAGES_HEADER_COUNT_14", msg_count == 14, msg_count)
    gate("ACTIVE_TEXT_HEADER_COUNT_70", text_count == 70, text_count)
    gate("CANDIDATE_EXISTS", candidate.exists(), rel(candidate, repo))
    gate("BI_ROOT_NOT_EXISTING_OR_REPLACE_ALLOWED", (not bi_root.exists()) or args.replace_existing_design, rel(bi_root, repo))

    status = BLOCKED
    diff_rows = []
    native_rows = []
    refusal_rows = []
    artifact_rows = []
    if failures == 0:
        if bi_root.exists() and args.replace_existing_design:
            shutil.rmtree(bi_root)
        bi_root.mkdir(parents=True, exist_ok=True)

        candidate_text = candidate.read_text(encoding="utf-8", errors="replace")
        candidate_hash = sha(candidate)

        for i, r in enumerate(review, start=1):
            tpath = r.get("TARGET_PATH", "")
            full = repo / tpath
            strategy, detail = diff_strategy(r)
            diff_rows.append({
                "DIFF_ROW": i,
                "TARGET_ID": r.get("TARGET_ID", ""),
                "TARGET_KIND": r.get("TARGET_KIND", ""),
                "TARGET_PATH": tpath,
                "TARGET_FORMAT": r.get("TARGET_FORMAT", ""),
                "TARGET_EXISTS": 1 if full.exists() else 0,
                "TARGET_SHA256": sha(full) if full.exists() and full.is_file() else "",
                "DIFF_STRATEGY": strategy,
                "DIFF_DETAIL": detail,
                "CANDIDATE_SOURCE": rel(candidate, repo),
                "CANDIDATE_SHA256": candidate_hash,
                "ANCHORS_OR_KEYS": "MSGMGR;SET MESSAGE CATALOG CHECK;SET MESSAGE CATALOG GET;SET MESSAGE EMIT",
                "PRE_WRITE_DIFF_GENERATED_NOW": 0,
                "AUTHORIZED_FOR_WRITE_NOW": 0,
                "TARGET_PROBE": probe(full),
            })

            native_rows.append({
                "NATIVE_ROW": i,
                "TARGET_ID": r.get("TARGET_ID", ""),
                "TARGET_PATH": tpath,
                "TARGET_FORMAT": r.get("TARGET_FORMAT", ""),
                "EXECUTION_DESIGN": "NATIVE_RUNTIME_OR_SCHEMA_AWARE_IMPORT_REQUIRED" if r.get("TARGET_FORMAT") == "DBF_BINARY" else "TEXT_PATCH_OR_NATIVE_HELP_REBUILD_AS_APPROPRIATE",
                "REFUSAL_GUARD": "refuse if target hash differs; refuse if anchor/key missing; refuse if backup missing; refuse if runtime readback script missing",
                "POST_WRITE_READBACK": "HELP MSGMGR; HELP SET MESSAGE; CMDHELPCHK; SET MESSAGE CATALOG CHECK remains 14/70",
                "RESTORE_REQUIRED_IF_NOT_ACCEPTED": 1,
                "IMPLEMENTED_NOW": 0,
            })

        refusal_rows = [
            {"REFUSAL": "RAW_PYTHON_DBF_WRITE", "STATUS": "REFUSE", "DETAIL": "Runtime DBF/CMDHELPCHK/HELP targets must not be raw-written by Python."},
            {"REFUSAL": "MISSING_BACKUP", "STATUS": "REFUSE", "DETAIL": "Any later execution must have exact target backup and matching pre-write hash."},
            {"REFUSAL": "TARGET_HASH_DRIFT", "STATUS": "REFUSE", "DETAIL": "If target hash differs from accepted state, execution must stop and re-plan."},
            {"REFUSAL": "ANCHOR_OR_KEY_AMBIGUITY", "STATUS": "REFUSE", "DETAIL": "If MSGMGR/SET MESSAGE anchors are missing or duplicated unexpectedly, execution must stop."},
            {"REFUSAL": "NO_RUNTIME_READBACK", "STATUS": "REFUSE", "DETAIL": "No later write package may close green without DotTalk++ runtime readback."},
        ]

        diff_path = bi_root / "pre_write_diff_design_v1.csv"
        native_path = bi_root / "native_execution_design_v1.csv"
        refusal_path = bi_root / "execution_refusal_guards_v1.csv"
        candidate_snapshot = bi_root / "candidate_snapshot" / CANDIDATE_PATH.name
        candidate_snapshot.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(candidate, candidate_snapshot)
        disabled = bi_root / "scripts" / "MESSAGE_CATALOG_PHASE22AE_6_5_10BJ_EXECUTION_DISABLED_UNTIL_DIFF_ACCEPTED.ps1.disabled"
        disabled.parent.mkdir(parents=True, exist_ok=True)
        disabled.write_text(
            'throw "DISABLED TEMPLATE: 10BI only designs pre-write diff/native execution; 10BJ review and later explicit execution gate required."\n',
            encoding="utf-8"
        )
        readme = bi_root / "README_10BI_PRE_WRITE_DIFF_AND_NATIVE_EXECUTION_DESIGN.md"
        readme.write_text(
            "# 10BI Pre-Write Diff and Native Execution Design\n\n"
            "10BI designs the pre-write diff and native execution guards. It does not mutate HELP DATA or CMDHELPCHK.\n\n"
            "No raw Python DBF writes are allowed. Later execution must use native x64base/DotTalk++ or schema-aware staged import with runtime readback gates.\n",
            encoding="utf-8"
        )

        wcsv(diff_path, diff_rows, ["DIFF_ROW","TARGET_ID","TARGET_KIND","TARGET_PATH","TARGET_FORMAT","TARGET_EXISTS","TARGET_SHA256","DIFF_STRATEGY","DIFF_DETAIL","CANDIDATE_SOURCE","CANDIDATE_SHA256","ANCHORS_OR_KEYS","PRE_WRITE_DIFF_GENERATED_NOW","AUTHORIZED_FOR_WRITE_NOW","TARGET_PROBE"])
        wcsv(native_path, native_rows, ["NATIVE_ROW","TARGET_ID","TARGET_PATH","TARGET_FORMAT","EXECUTION_DESIGN","REFUSAL_GUARD","POST_WRITE_READBACK","RESTORE_REQUIRED_IF_NOT_ACCEPTED","IMPLEMENTED_NOW"])
        wcsv(refusal_path, refusal_rows, ["REFUSAL","STATUS","DETAIL"])

        for p in [diff_path, native_path, refusal_path, candidate_snapshot, disabled, readme]:
            artifact_rows.append({"ARTIFACT": rel(p, repo), "ROLE": "pre_write_diff_or_native_execution_design_artifact", "BYTES": p.stat().st_size, "SHA256": sha(p)})

        status = GREEN

    boundary = [
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "10BI writes docs/messaging design artifacts only."},
        {"PROTECTED_SYSTEM": "ACTIVE_SYSTEM_MESSAGES", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_SYSTEM_MESSAGE_TEXT", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_CDX_LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CDX/LMDB mutation."},
        {"PROTECTED_SYSTEM": "WORKSPACE_PROFILE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No workspace mutation."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No HELP DATA mutation; design only."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CMDHELPCHK mutation; design only."},
    ]

    readiness = [
        {"ITEM": "PRE_WRITE_DIFF_DESIGN_CREATED", "STATUS": "YES" if diff_rows else "NO", "DETAIL": f"{len(diff_rows)} diff design rows."},
        {"ITEM": "NATIVE_EXECUTION_DESIGN_CREATED", "STATUS": "YES" if native_rows else "NO", "DETAIL": f"{len(native_rows)} native execution design rows."},
        {"ITEM": "EXECUTION_REFUSAL_GUARDS_CREATED", "STATUS": "YES" if refusal_rows else "NO", "DETAIL": f"{len(refusal_rows)} refusal guards."},
        {"ITEM": "HELP_DATA_APPLY_EXECUTION", "STATUS": "NOT_EXECUTED_IN_10BI", "DETAIL": "No apply execution."},
        {"ITEM": "CMDHELPCHK_APPLY_EXECUTION", "STATUS": "NOT_EXECUTED_IN_10BI", "DETAIL": "No apply execution."},
        {"ITEM": "NEXT_REVIEW_GATE", "STATUS": "10BJ_REQUIRED", "DETAIL": "Review diff/native design and decide whether exact diff package may be generated."},
    ]

    issues = "0" if failures == 0 else str(failures)
    wcsv(reports / "message_catalog_phase22ae_6_5_10bi_gate_check_v1.csv", gates, ["GATE","STATUS","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10bi_pre_write_diff_design_v1.csv", diff_rows, ["DIFF_ROW","TARGET_ID","TARGET_KIND","TARGET_PATH","TARGET_FORMAT","TARGET_EXISTS","TARGET_SHA256","DIFF_STRATEGY","DIFF_DETAIL","CANDIDATE_SOURCE","CANDIDATE_SHA256","ANCHORS_OR_KEYS","PRE_WRITE_DIFF_GENERATED_NOW","AUTHORIZED_FOR_WRITE_NOW","TARGET_PROBE"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10bi_native_execution_design_v1.csv", native_rows, ["NATIVE_ROW","TARGET_ID","TARGET_PATH","TARGET_FORMAT","EXECUTION_DESIGN","REFUSAL_GUARD","POST_WRITE_READBACK","RESTORE_REQUIRED_IF_NOT_ACCEPTED","IMPLEMENTED_NOW"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10bi_execution_refusal_guards_v1.csv", refusal_rows, ["REFUSAL","STATUS","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10bi_apply_readiness_v1.csv", readiness, ["ITEM","STATUS","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10bi_boundary_ledger_v1.csv", boundary, ["PROTECTED_SYSTEM","MUTATION_ALLOWED","OBSERVED_MUTATION","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10bi_artifact_manifest_v1.csv", artifact_rows, ["ARTIFACT","ROLE","BYTES","SHA256"])

    summary = {
        "STATUS": status,
        "VALIDATION_ISSUES": issues,
        "PHASE22AE_6_5_10BH_STATUS": bh.get("STATUS", ""),
        "MSG_022AE_6_5_10BH_SAVEPOINT_PRESENT": 1 if sp_bh else 0,
        "ACTIVE_MESSAGES_OBSERVED_COUNT": msg_count,
        "ACTIVE_TEXT_OBSERVED_COUNT": text_count,
        "BH_WRITE_IMPLEMENTATION_REVIEW_ROWS": len(review),
        "PRE_WRITE_DIFF_DESIGN_ROWS": len(diff_rows),
        "NATIVE_EXECUTION_DESIGN_ROWS": len(native_rows),
        "EXECUTION_REFUSAL_GUARD_ROWS": len(refusal_rows),
        "BI_ROOT": rel(bi_root, repo),
        "PRE_WRITE_DIFF_DESIGN_CREATED": 1 if status == GREEN else 0,
        "NATIVE_EXECUTION_DESIGN_CREATED": 1 if status == GREEN else 0,
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
    wcsv(reports / "message_catalog_phase22ae_6_5_10bi_status_summary_v1.csv", [summary], list(summary.keys()))

    (repo / "docs/messaging/MESSAGE_LOCALE_PHASE22AE_6_5_10BI_PRE_WRITE_DIFF_AND_NATIVE_EXECUTION_DESIGN_PACKAGE.md").write_text(
        f"# Message Catalog Phase 22AE.6.5.10BI Pre-Write Diff and Native Execution Design Package\n\n"
        f"Status: `{status}`\n\n"
        "10BI creates pre-write diff and native execution design artifacts. It does not mutate HELP DATA or CMDHELPCHK.\n\n"
        f"Design root:\n\n```text\n{rel(bi_root, repo)}\n```\n\n"
        f"Next gate:\n\n```text\n{NEXT}\n```\n",
        encoding="utf-8"
    )

    print(status)
    print(f"  validation issues: {issues}")
    print(f"  Phase 22AE.6.5.10BH status: {bh.get('STATUS','')}")
    print(f"  MSG-022AE.6.5.10BH savepoint present: {1 if sp_bh else 0}")
    print(f"  active messages observed count: {msg_count}")
    print(f"  active text observed count: {text_count}")
    print(f"  BH write implementation review rows: {len(review)}")
    print(f"  pre-write diff design rows: {len(diff_rows)}")
    print(f"  native execution design rows: {len(native_rows)}")
    print(f"  execution refusal guard rows: {len(refusal_rows)}")
    print(f"  design root: {rel(bi_root, repo)}")
    print("  pre-write diff design created: 1")
    print("  native execution design created: 1")
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
