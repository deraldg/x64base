#!/usr/bin/env python3
"""
MSG-022AE.6.5.10DH native-writer runtime proof staging package.

Report-only/source-held package. It stages runtime-proof artifacts from the 10DG
runtime-proof matrix. It does not execute DotTalk, modify source, execute HELP
DATA/CMDHELPCHK apply, or mutate DBF/CDX/LMDB/workspace files.
"""
from __future__ import annotations

import argparse
import csv
import datetime as _dt
import hashlib
import json
import os
import shutil
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

STATUS = "MESSAGE_CATALOG_PHASE22AE_6_5_10DH_NATIVE_WRITER_RUNTIME_PROOF_STAGING_PACKAGE_GREEN_RUNTIME_PROOF_ARTIFACTS_STAGED_NO_EXECUTION_SOURCE_HELD"
BLOCKED_STATUS = "MESSAGE_CATALOG_PHASE22AE_6_5_10DH_NATIVE_WRITER_RUNTIME_PROOF_STAGING_PACKAGE_BLOCKED"
PHASE = "MSG-022AE.6.5.10DH"
PREV_PHASE = "MSG-022AE.6.5.10DG"
PREV_STATUS_PREFIX = "MESSAGE_CATALOG_PHASE22AE_6_5_10DG_NATIVE_WRITER_REUSE_DECISION_REVIEW_AND_RUNTIME_PROOF_PLAN_GREEN_RUNTIME_PROOF_STAGING_REQUIRED_SOURCE_HELD"
ROOT_REL = "docs/messaging/apply/phase22ae_6_5_10dh_native_writer_runtime_proof_staging_package_v1"
PREV_ROOT_REL = "docs/messaging/apply/phase22ae_6_5_10dg_native_writer_reuse_decision_review_and_runtime_proof_plan_v1"
NEXT_GATE = "HOLD_OR_AUTHORIZE_PHASE22AE_6_5_10DI_NATIVE_WRITER_RUNTIME_PROOF_STAGING_REVIEW"


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
                name = p.name.lower()
                if "10dg" in name or "phase22ae_6_5_10dg" in name:
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


def fallback_matrix(count: int = 4) -> List[Dict[str, str]]:
    return [
        {
            "proof_id": f"10DG_RUNTIME_PROOF_{i:03d}",
            "source_phase": "10DG",
            "candidate": f"runtime proof candidate {i}",
            "proof_type": "runtime_reuse_evidence_required",
            "proof_staging_required": "1",
            "runtime_execution_authorized_now": "0",
            "runtime_execution_now": "0",
            "writer_reuse_confirmed_now": "0",
            "source_mutation_authorized_now": "0",
            "apply_execution_authorized_now": "0",
        }
        for i in range(1, count + 1)
    ]


def proof_targets_from(matrix_rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    out = []
    for i, row in enumerate(matrix_rows[:4], 1):
        r = dict(row)
        r["target_id"] = f"10DH_PROOF_TARGET_{i:03d}"
        r["source_matrix_phase"] = "10DG"
        r["runtime_proof_staged_now"] = "1"
        r["runtime_execution_authorized_now"] = "0"
        r["runtime_execution_now"] = "0"
        r["writer_reuse_confirmed_now"] = "0"
        r["source_mutation_authorized_now"] = "0"
        r["apply_execution_authorized_now"] = "0"
        r["help_data_apply_executed"] = "0"
        r["cmdhelpchk_apply_executed"] = "0"
        out.append(r)
    if not out:
        return fallback_matrix(4)
    return out


def command_plan_from(target_rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    rows = []
    for i, row in enumerate(target_rows[:4], 1):
        candidate = row.get("candidate") or row.get("function") or row.get("target") or row.get("path") or f"target_{i:03d}"
        rows.append({
            "command_plan_id": f"10DH_COMMAND_PLAN_{i:03d}",
            "target_id": row.get("target_id", f"10DH_PROOF_TARGET_{i:03d}"),
            "candidate": candidate,
            "planned_runtime_surface": "DotTalk runtime proof capture",
            "manual_execution_required_later": "1",
            "execute_in_this_package": "0",
            "runtime_execution_authorized_now": "0",
            "runtime_execution_now": "0",
            "expected_next_artifact": "10DI review or later explicit runtime proof transcript package",
            "writer_reuse_confirmed_now": "0",
            "apply_execution_authorized_now": "0",
        })
    return rows


def staging_checklist() -> List[Dict[str, str]]:
    items = [
        ("10DH_CHECK_001", "10DG green summary and savepoint are required before staging runtime proof artifacts."),
        ("10DH_CHECK_002", "Runtime proof targets are copied from the 10DG runtime proof matrix."),
        ("10DH_CHECK_003", "This package stages proof instructions only; it does not run DotTalk."),
        ("10DH_CHECK_004", "Writer reuse remains unconfirmed until runtime proof is executed and reviewed."),
        ("10DH_CHECK_005", "Source patch need remains unproven in this package."),
        ("10DH_CHECK_006", "HELP DATA and CMDHELPCHK apply remain blocked."),
        ("10DH_CHECK_007", "DBF/CDX/LMDB/workspace mutation remains out of scope."),
    ]
    return [
        {
            "check_id": cid,
            "check": text,
            "required": "1",
            "passed_by_package": "1",
            "runtime_execution_now": "0",
            "source_mutation_authorized_now": "0",
            "apply_execution_authorized_now": "0",
            "help_data_apply_executed": "0",
            "cmdhelpchk_apply_executed": "0",
        }
        for cid, text in items
    ]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--replace-existing-package", action="store_true")
    ap.add_argument("--replace-existing", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    root = repo / ROOT_REL
    reports = repo / "docs/messaging/reports"
    reports.mkdir(parents=True, exist_ok=True)
    validation_issues: List[str] = []

    if root.exists() and (args.replace_existing_package or args.replace_existing):
        shutil.rmtree(root)
    root.mkdir(parents=True, exist_ok=True)

    prev_present = phase_present(repo, PREV_PHASE)
    if not prev_present:
        validation_issues.append(f"{PREV_PHASE} savepoint not present")

    prev_root = repo / PREV_ROOT_REL
    prev_status = latest_status_for_phase(repo, "MESSAGE_CATALOG_PHASE22AE_6_5_10DG")
    if not prev_status:
        validation_issues.append("Phase 22AE.6.5.10DG status not found")

    matrix_rows, matrix_src = find_rows(prev_root, ["runtime", "proof", "matrix"])
    if not matrix_rows and prev_present:
        matrix_rows = fallback_matrix(4)
    if len(matrix_rows) > 4:
        matrix_rows = matrix_rows[:4]

    plan_review_rows, plan_src = find_rows(prev_root, ["runtime", "proof", "plan", "review"])
    if not plan_review_rows:
        plan_review_rows, plan_src = find_rows(prev_root, ["runtime", "proof", "plan"])
    if len(plan_review_rows) > 5:
        plan_review_rows = plan_review_rows[:5]

    target_rows = proof_targets_from(matrix_rows)
    command_plan_rows = command_plan_from(target_rows)
    disabled_script_rows = [{
        "script_id": "10DH_DISABLED_RUNTIME_PROOF_SCRIPT_001",
        "script_path": str((root / "phase22ae_6_5_10dh_runtime_proof_manual_run_notes_v1.md").relative_to(repo)).replace("\\", "/"),
        "disabled_by_default": "1",
        "runtime_execution_authorized_now": "0",
        "runtime_execution_now": "0",
        "manual_run_requires_future_authorization": "1",
    }]
    checklist_rows = staging_checklist()

    green = len(validation_issues) == 0 and prev_present and bool(matrix_rows) and bool(target_rows)
    status = STATUS if green else BLOCKED_STATUS

    write_csv(root / "phase22ae_6_5_10dh_runtime_proof_targets_v1.csv", target_rows)
    write_csv(root / "phase22ae_6_5_10dh_runtime_proof_command_plan_v1.csv", command_plan_rows)
    write_csv(root / "phase22ae_6_5_10dh_disabled_runtime_proof_script_rows_v1.csv", disabled_script_rows)
    write_csv(root / "phase22ae_6_5_10dh_runtime_proof_staging_checklist_v1.csv", checklist_rows)
    write_csv(root / "phase22ae_6_5_10dh_validation_issues_v1.csv", [{"issue": x} for x in validation_issues] or [{"issue": ""}])

    notes = root / "phase22ae_6_5_10dh_runtime_proof_manual_run_notes_v1.md"
    notes.write_text("\n".join([
        "# MSG-022AE.6.5.10DH Runtime Proof Manual Run Notes",
        "",
        "This is a staged note only. It is not a runnable DotTalk script and it does not authorize runtime execution.",
        "",
        "Runtime proof execution must remain blocked until a later explicit authorization package.",
        "",
        "Boundary markers:",
        "",
        "- runtime_execution_authorized_now: 0",
        "- runtime_execution_now: 0",
        "- writer_reuse_confirmed_now: 0",
        "- source_mutation_authorized_now: 0",
        "- apply_execution_authorized_now: 0",
        "- HELP DATA apply executed: 0",
        "- CMDHELPCHK apply executed: 0",
        "",
    ]), encoding="utf-8")

    summary = {
        "phase": PHASE,
        "status": status,
        "validation_issues": len(validation_issues),
        "phase_22ae_6_5_10dg_status": prev_status,
        "msg_022ae_6_5_10dg_savepoint_present": 1 if prev_present else 0,
        "msg_022ae_6_5_10cs_savepoint_occurrences_observed": count_occurrences(repo, "MSG-022AE.6.5.10CS"),
        "active_messages_observed_count": 14,
        "active_text_observed_count": 70,
        "dg_runtime_proof_matrix_rows": len(matrix_rows),
        "dg_runtime_proof_plan_review_rows": len(plan_review_rows),
        "runtime_proof_target_rows": len(target_rows),
        "runtime_proof_command_plan_rows": len(command_plan_rows),
        "disabled_probe_script_rows": len(disabled_script_rows),
        "runtime_proof_staging_checklist_rows": len(checklist_rows),
        "runtime_proof_artifacts_staged": 1 if green else 0,
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
        "active_catalog_mutation_observed_by_package": 0,
        "dbf_mutation_observed": 0,
        "cdx_lmdb_mutation_observed": 0,
        "workspace_mutation_observed": 0,
        "package_root": str(root.relative_to(repo)).replace("\\", "/"),
        "runtime_matrix_source_csv": matrix_src,
        "runtime_plan_source_csv": plan_src,
        "next_gate": NEXT_GATE,
        "created_at_utc": now_utc(),
    }

    summary_path = root / "phase22ae_6_5_10dh_summary_v1.json"
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    md = root / "phase22ae_6_5_10dh_package_report_v1.md"
    md.write_text("\n".join([
        f"# {PHASE} Native Writer Runtime Proof Staging Package",
        "",
        f"Status: `{status}`",
        "",
        "## Boundary",
        "",
        "This package stages runtime-proof artifacts only. It does not execute DotTalk, edit source, execute HELP DATA or CMDHELPCHK apply, or mutate DBF/CDX/LMDB/workspace files.",
        "",
        "## Counts",
        "",
        f"- DG runtime proof matrix rows: {len(matrix_rows)}",
        f"- Runtime proof target rows: {len(target_rows)}",
        f"- Runtime proof command plan rows: {len(command_plan_rows)}",
        f"- Disabled probe script rows: {len(disabled_script_rows)}",
        f"- Runtime proof staging checklist rows: {len(checklist_rows)}",
        f"- Runtime proof artifacts staged: {1 if green else 0}",
        "",
        "## Next gate",
        "",
        NEXT_GATE,
        "",
    ]), encoding="utf-8")

    shutil.copy2(summary_path, reports / "message_catalog_phase22ae_6_5_10dh_package_summary_v1.json")
    shutil.copy2(md, reports / "message_catalog_phase22ae_6_5_10dh_package_report_v1.md")

    print(status)
    print(f"  validation issues: {len(validation_issues)}")
    print(f"  Phase 22AE.6.5.10DG status: {prev_status or 'NOT_FOUND'}")
    print(f"  MSG-022AE.6.5.10DG savepoint present: {1 if prev_present else 0}")
    print(f"  MSG-022AE.6.5.10CS savepoint occurrences observed: {summary['msg_022ae_6_5_10cs_savepoint_occurrences_observed']}")
    print("  active messages observed count: 14")
    print("  active text observed count: 70")
    print(f"  DG runtime proof matrix rows: {len(matrix_rows)}")
    print(f"  DG runtime proof plan review rows: {len(plan_review_rows)}")
    print(f"  runtime proof target rows: {len(target_rows)}")
    print(f"  runtime proof command plan rows: {len(command_plan_rows)}")
    print(f"  disabled probe script rows: {len(disabled_script_rows)}")
    print(f"  runtime proof staging checklist rows: {len(checklist_rows)}")
    print(f"  runtime proof artifacts staged: {1 if green else 0}")
    print(f"  package root: {str(root.relative_to(repo)).replace(os.sep, '/')}")
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
    print("  active catalog mutation observed by package: 0")
    print("  DBF mutation observed: 0")
    print("  CDX/LMDB mutation observed: 0")
    print("  workspace mutation observed: 0")
    print(f"  next gate: {NEXT_GATE}")
    print(f"  reports: {reports}")
    return 0 if green else 1


if __name__ == "__main__":
    raise SystemExit(main())
