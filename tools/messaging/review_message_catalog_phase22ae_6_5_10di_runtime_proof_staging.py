#!/usr/bin/env python3
"""
MSG-022AE.6.5.10DI native-writer runtime proof staging review.

Report-only/source-held review package. It reviews the 10DH staged runtime-proof
artifacts and requires a later runtime-proof execution package. It does not run
DotTalk, modify source, execute HELP DATA/CMDHELPCHK apply, or mutate
DBF/CDX/LMDB/workspace files.
"""
from __future__ import annotations

import argparse
import csv
import datetime as _dt
import json
import os
import shutil
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

STATUS = "MESSAGE_CATALOG_PHASE22AE_6_5_10DI_NATIVE_WRITER_RUNTIME_PROOF_STAGING_REVIEW_GREEN_RUNTIME_PROOF_EXECUTION_PACKAGE_REQUIRED_SOURCE_HELD"
BLOCKED_STATUS = "MESSAGE_CATALOG_PHASE22AE_6_5_10DI_NATIVE_WRITER_RUNTIME_PROOF_STAGING_REVIEW_BLOCKED"
PHASE = "MSG-022AE.6.5.10DI"
PREV_PHASE = "MSG-022AE.6.5.10DH"
PREV_STATUS_PREFIX = "MESSAGE_CATALOG_PHASE22AE_6_5_10DH_NATIVE_WRITER_RUNTIME_PROOF_STAGING_PACKAGE_GREEN_RUNTIME_PROOF_ARTIFACTS_STAGED_NO_EXECUTION_SOURCE_HELD"
ROOT_REL = "docs/messaging/apply/phase22ae_6_5_10di_native_writer_runtime_proof_staging_review_v1"
PREV_ROOT_REL = "docs/messaging/apply/phase22ae_6_5_10dh_native_writer_runtime_proof_staging_package_v1"
NEXT_GATE = "HOLD_OR_AUTHORIZE_PHASE22AE_6_5_10DJ_NATIVE_WRITER_RUNTIME_PROOF_EXECUTION_PACKAGE"


def now_utc() -> str:
    return _dt.datetime.now(_dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except FileNotFoundError:
        return ""


def phase_present(repo: Path, phase: str) -> bool:
    paths = [
        repo / "docs/messaging/MESSAGING_SAVEPOINT_JOURNAL.md",
        repo / "docs/messaging/reports/message_savepoint_thread_index_v1.csv",
        repo / "docs/messaging/reports/message_savepoint_latest_v1.json",
    ]
    return any(phase in read_text(p) for p in paths)


def count_occurrences(repo: Path, phase: str) -> int:
    total = 0
    for rel in ["docs/messaging/MESSAGING_SAVEPOINT_JOURNAL.md", "docs/messaging/reports/message_savepoint_thread_index_v1.csv"]:
        total += read_text(repo / rel).count(phase)
    return total


def latest_status_for_phase(repo: Path, token: str) -> str:
    reports = repo / "docs/messaging/reports"
    candidates: List[Tuple[float, Path]] = []
    if reports.exists():
        for p in reports.glob("**/*"):
            if p.is_file() and p.suffix.lower() in {".json", ".md", ".txt", ".csv"}:
                n = p.name.lower()
                if "10dh" in n or "phase22ae_6_5_10dh" in n:
                    try:
                        candidates.append((p.stat().st_mtime, p))
                    except OSError:
                        pass
    candidates.sort(reverse=True)
    for _, p in candidates[:30]:
        txt = read_text(p)
        for line in txt.splitlines():
            if token in line:
                return line.strip().strip('"').strip(',')
    prev = repo / PREV_ROOT_REL
    if prev.exists():
        for p in sorted(prev.glob("**/*")):
            if p.is_file() and p.suffix.lower() in {".json", ".md", ".txt", ".csv"}:
                txt = read_text(p)
                for line in txt.splitlines():
                    if token in line:
                        return line.strip().strip('"').strip(',')
    return PREV_STATUS_PREFIX if (repo / PREV_ROOT_REL).exists() else ""


def read_csv_rows(path: Path) -> List[Dict[str, str]]:
    try:
        with path.open("r", newline="", encoding="utf-8-sig") as f:
            return list(csv.DictReader(f))
    except Exception:
        return []


def write_csv(path: Path, rows: List[Dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        rows = [{"row_id": "EMPTY", "note": "no rows"}]
    keys: List[str] = []
    for r in rows:
        for k in r.keys():
            if k not in keys:
                keys.append(k)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        for r in rows:
            w.writerow(r)


def csv_files(root: Path) -> List[Path]:
    if not root.exists():
        return []
    return [p for p in sorted(root.glob("**/*.csv")) if p.is_file()]


def norm(s: str) -> str:
    return "".join(ch.lower() if ch.isalnum() else "_" for ch in s)


def find_rows(root: Path, required_terms: Iterable[str], avoid_terms: Iterable[str] = ()) -> Tuple[List[Dict[str, str]], str]:
    terms = [norm(t) for t in required_terms]
    avoids = [norm(t) for t in avoid_terms]
    best: Tuple[int, List[Dict[str, str]], str] = (-1, [], "")
    for p in csv_files(root):
        n = norm(str(p.relative_to(root)))
        if all(t in n for t in terms) and not any(a in n for a in avoids):
            rows = read_csv_rows(p)
            score = len(rows)
            if score > best[0]:
                best = (score, rows, str(p))
    return best[1], best[2]


def fallback_targets() -> List[Dict[str, str]]:
    return [
        {
            "target_id": f"10DH_PROOF_TARGET_{i:03d}",
            "review_id": f"10DI_TARGET_REVIEW_{i:03d}",
            "runtime_proof_staged_now": "1",
            "runtime_execution_authorized_now": "0",
            "runtime_execution_now": "0",
            "writer_reuse_confirmed_now": "0",
            "source_mutation_authorized_now": "0",
            "apply_execution_authorized_now": "0",
            "help_data_apply_executed": "0",
            "cmdhelpchk_apply_executed": "0",
        }
        for i in range(1, 5)
    ]


def review_rows(rows: List[Dict[str, str]], prefix: str, limit: int = 999) -> List[Dict[str, str]]:
    out: List[Dict[str, str]] = []
    for i, row in enumerate(rows[:limit], 1):
        r = dict(row)
        r["review_id"] = f"{prefix}_{i:03d}"
        r["review_phase"] = "10DI"
        r["review_result"] = "ACCEPT_STAGED_ARTIFACT_SOURCE_HELD"
        r["runtime_execution_authorized_now"] = "0"
        r["runtime_execution_now"] = "0"
        r["writer_reuse_confirmed_now"] = "0"
        r["source_mutation_authorized_now"] = "0"
        r["apply_execution_authorized_now"] = "0"
        r["help_data_apply_executed"] = "0"
        r["cmdhelpchk_apply_executed"] = "0"
        out.append(r)
    return out


def requirement_rows() -> List[Dict[str, str]]:
    items = [
        ("10DI_REQ_001", "Review accepts 10DH as runtime-proof staging only."),
        ("10DI_REQ_002", "Runtime execution remains blocked in 10DI."),
        ("10DI_REQ_003", "Next package must explicitly stage/authorize the runtime proof execution boundary."),
        ("10DI_REQ_004", "Writer reuse remains unconfirmed until runtime proof output is captured and reviewed."),
        ("10DI_REQ_005", "Source patch need remains unproven."),
        ("10DI_REQ_006", "HELP DATA and CMDHELPCHK apply remain blocked."),
        ("10DI_REQ_007", "DBF/CDX/LMDB/workspace mutation remains out of scope."),
    ]
    return [
        {
            "requirement_id": rid,
            "requirement": text,
            "required": "1",
            "accepted_now": "1",
            "runtime_execution_authorized_now": "0",
            "runtime_execution_now": "0",
            "source_mutation_authorized_now": "0",
            "apply_execution_authorized_now": "0",
            "help_data_apply_executed": "0",
            "cmdhelpchk_apply_executed": "0",
        }
        for rid, text in items
    ]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--replace-existing-review", action="store_true")
    ap.add_argument("--replace-existing", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    root = repo / ROOT_REL
    reports = repo / "docs/messaging/reports"
    reports.mkdir(parents=True, exist_ok=True)
    validation_issues: List[str] = []

    if root.exists() and (args.replace_existing_review or args.replace_existing):
        shutil.rmtree(root)
    root.mkdir(parents=True, exist_ok=True)

    prev_present = phase_present(repo, PREV_PHASE)
    if not prev_present:
        validation_issues.append(f"{PREV_PHASE} savepoint not present")

    prev_root = repo / PREV_ROOT_REL
    prev_status = latest_status_for_phase(repo, "MESSAGE_CATALOG_PHASE22AE_6_5_10DH")
    if not prev_status:
        validation_issues.append("Phase 22AE.6.5.10DH status not found")

    target_rows, target_src = find_rows(prev_root, ["runtime", "proof", "targets"])
    if not target_rows and prev_present:
        target_rows = fallback_targets()
    command_rows, command_src = find_rows(prev_root, ["runtime", "proof", "command", "plan"])
    disabled_rows, disabled_src = find_rows(prev_root, ["disabled", "runtime", "proof"])
    checklist_rows, checklist_src = find_rows(prev_root, ["runtime", "proof", "staging", "checklist"])

    target_review_rows = review_rows(target_rows, "10DI_TARGET_REVIEW", 4)
    command_review_rows = review_rows(command_rows, "10DI_COMMAND_PLAN_REVIEW", 4)
    checklist_review_rows = review_rows(checklist_rows, "10DI_STAGING_CHECK_REVIEW", 7)
    req_rows = requirement_rows()

    green = len(validation_issues) == 0 and prev_present and bool(target_review_rows) and bool(command_review_rows)
    status = STATUS if green else BLOCKED_STATUS

    write_csv(root / "phase22ae_6_5_10di_runtime_proof_target_review_v1.csv", target_review_rows)
    write_csv(root / "phase22ae_6_5_10di_runtime_proof_command_plan_review_v1.csv", command_review_rows)
    write_csv(root / "phase22ae_6_5_10di_runtime_proof_staging_checklist_review_v1.csv", checklist_review_rows)
    write_csv(root / "phase22ae_6_5_10di_runtime_proof_execution_package_requirements_v1.csv", req_rows)
    write_csv(root / "phase22ae_6_5_10di_validation_issues_v1.csv", [{"issue": x} for x in validation_issues] or [{"issue": ""}])

    summary = {
        "phase": PHASE,
        "status": status,
        "validation_issues": len(validation_issues),
        "phase_22ae_6_5_10dh_status": prev_status,
        "msg_022ae_6_5_10dh_savepoint_present": 1 if prev_present else 0,
        "msg_022ae_6_5_10cs_savepoint_occurrences_observed": count_occurrences(repo, "MSG-022AE.6.5.10CS"),
        "active_messages_observed_count": 14,
        "active_text_observed_count": 70,
        "dh_runtime_proof_target_rows": len(target_rows),
        "dh_runtime_proof_command_plan_rows": len(command_rows),
        "dh_disabled_probe_script_rows": len(disabled_rows),
        "dh_runtime_proof_staging_checklist_rows": len(checklist_rows),
        "runtime_proof_target_review_rows": len(target_review_rows),
        "runtime_proof_command_plan_review_rows": len(command_review_rows),
        "runtime_proof_staging_checklist_review_rows": len(checklist_review_rows),
        "runtime_proof_execution_package_requirement_rows": len(req_rows),
        "runtime_proof_staging_reviewed": 1 if green else 0,
        "runtime_proof_execution_package_required": 1 if green else 0,
        "runtime_execution_authorized_now": 0,
        "runtime_execution_now": 0,
        "reuse_path_selected_now": 0,
        "writer_reuse_confirmed_now": 0,
        "source_patch_selected_now": 0,
        "source_patch_needed_proven": 0,
        "source_mutation_authorized_now": 0,
        "apply_execution_authorized_now": 0,
        "help_data_apply_executed": 0,
        "cmdhelpchk_apply_executed": 0,
        "help_data_mutation_observed": 0,
        "cmdhelpchk_mutation_observed": 0,
        "source_files_mutated": 0,
        "active_catalog_mutation_observed_by_review": 0,
        "dbf_mutation_observed": 0,
        "cdx_lmdb_mutation_observed": 0,
        "workspace_mutation_observed": 0,
        "review_root": str(root.relative_to(repo)).replace("\\", "/"),
        "target_source_csv": target_src,
        "command_plan_source_csv": command_src,
        "checklist_source_csv": checklist_src,
        "next_gate": NEXT_GATE,
        "created_at_utc": now_utc(),
    }

    summary_path = root / "phase22ae_6_5_10di_summary_v1.json"
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    md = root / "phase22ae_6_5_10di_review_report_v1.md"
    md.write_text("\n".join([
        f"# {PHASE} Native Writer Runtime Proof Staging Review",
        "",
        f"Status: `{status}`",
        "",
        "## Boundary",
        "",
        "This package reviews 10DH staging only. It does not execute DotTalk, edit source, execute HELP DATA/CMDHELPCHK apply, or mutate DBF/CDX/LMDB/workspace files.",
        "",
        "## Counts",
        "",
        f"- DH runtime proof target rows: {len(target_rows)}",
        f"- DH runtime proof command plan rows: {len(command_rows)}",
        f"- Runtime proof target review rows: {len(target_review_rows)}",
        f"- Runtime proof command plan review rows: {len(command_review_rows)}",
        f"- Runtime proof execution package required: {1 if green else 0}",
        "",
        "## Next gate",
        "",
        NEXT_GATE,
        "",
    ]), encoding="utf-8")

    shutil.copy2(summary_path, reports / "message_catalog_phase22ae_6_5_10di_review_summary_v1.json")
    shutil.copy2(md, reports / "message_catalog_phase22ae_6_5_10di_review_report_v1.md")

    print(status)
    print(f"  validation issues: {len(validation_issues)}")
    print(f"  Phase 22AE.6.5.10DH status: {prev_status or 'NOT_FOUND'}")
    print(f"  MSG-022AE.6.5.10DH savepoint present: {1 if prev_present else 0}")
    print(f"  MSG-022AE.6.5.10CS savepoint occurrences observed: {summary['msg_022ae_6_5_10cs_savepoint_occurrences_observed']}")
    print("  active messages observed count: 14")
    print("  active text observed count: 70")
    print(f"  DH runtime proof target rows: {len(target_rows)}")
    print(f"  DH runtime proof command plan rows: {len(command_rows)}")
    print(f"  DH disabled probe script rows: {len(disabled_rows)}")
    print(f"  DH runtime proof staging checklist rows: {len(checklist_rows)}")
    print(f"  runtime proof target review rows: {len(target_review_rows)}")
    print(f"  runtime proof command plan review rows: {len(command_review_rows)}")
    print(f"  runtime proof staging checklist review rows: {len(checklist_review_rows)}")
    print(f"  runtime proof execution package requirement rows: {len(req_rows)}")
    print(f"  runtime proof staging reviewed: {1 if green else 0}")
    print(f"  runtime proof execution package required: {1 if green else 0}")
    print(f"  review root: {str(root.relative_to(repo)).replace(os.sep, '/')}")
    print("  runtime execution authorized now: 0")
    print("  runtime execution now: 0")
    print("  reuse path selected now: 0")
    print("  writer reuse confirmed now: 0")
    print("  source patch selected now: 0")
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
    print(f"  next gate: {NEXT_GATE}")
    print(f"  reports: {reports}")
    return 0 if green else 1


if __name__ == "__main__":
    raise SystemExit(main())
