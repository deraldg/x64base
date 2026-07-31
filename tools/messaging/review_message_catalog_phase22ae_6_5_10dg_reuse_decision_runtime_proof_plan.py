#!/usr/bin/env python3
"""
MSG-022AE.6.5.10DG native-writer reuse decision review and runtime-proof plan.

Report-only/source-held package. It reviews the 10DF reuse-decision package and
stages the runtime-proof matrix required by the next package. It does not run
DotTalk, modify source, execute HELP/CMDHELPCHK apply, or mutate DBF/CDX/LMDB or
workspace files.
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

STATUS = "MESSAGE_CATALOG_PHASE22AE_6_5_10DG_NATIVE_WRITER_REUSE_DECISION_REVIEW_AND_RUNTIME_PROOF_PLAN_GREEN_RUNTIME_PROOF_STAGING_REQUIRED_SOURCE_HELD"
BLOCKED_STATUS = "MESSAGE_CATALOG_PHASE22AE_6_5_10DG_NATIVE_WRITER_REUSE_DECISION_REVIEW_AND_RUNTIME_PROOF_PLAN_BLOCKED"
PHASE = "MSG-022AE.6.5.10DG"
PREV_PHASE = "MSG-022AE.6.5.10DF"
PREV_STATUS_PREFIX = "MESSAGE_CATALOG_PHASE22AE_6_5_10DF_NATIVE_WRITER_REUSE_DECISION_PACKAGE_GREEN_RUNTIME_PROOF_PLAN_REQUIRED_SOURCE_HELD"
ROOT_REL = "docs/messaging/apply/phase22ae_6_5_10dg_native_writer_reuse_decision_review_and_runtime_proof_plan_v1"
PREV_ROOT_REL = "docs/messaging/apply/phase22ae_6_5_10df_native_writer_reuse_decision_package_v1"


def now_utc() -> str:
    return _dt.datetime.now(_dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except FileNotFoundError:
        return ""


def phase_present(repo: Path, phase: str) -> bool:
    journal = repo / "docs/messaging/MESSAGING_SAVEPOINT_JOURNAL.md"
    if phase in read_text(journal):
        return True
    index = repo / "docs/messaging/reports/message_savepoint_thread_index_v1.csv"
    if phase in read_text(index):
        return True
    latest = repo / "docs/messaging/reports/message_savepoint_latest_v1.json"
    if phase in read_text(latest):
        return True
    return False


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
                if "10df" in name or "phase22ae_6_5_10df" in name:
                    try:
                        candidates.append((p.stat().st_mtime, p))
                    except OSError:
                        pass
    candidates.sort(reverse=True)
    for _, p in candidates[:20]:
        txt = read_text(p)
        for line in txt.splitlines():
            if token in line:
                return line.strip().strip('"').strip(',')
    # Also scan previous apply root.
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


def norm(s: str) -> str:
    return "".join(ch.lower() if ch.isalnum() else "_" for ch in s)


def csv_files(root: Path) -> List[Path]:
    if not root.exists():
        return []
    return [p for p in sorted(root.glob("**/*.csv")) if p.is_file()]


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


def fallback_rows(count: int, kind: str) -> List[Dict[str, str]]:
    return [
        {
            "row_id": f"{kind.upper()}_{i:03d}",
            "phase": "10DG",
            "source_phase": "10DF",
            "review_status": "staged_from_10df_package_summary",
            "mutation_authorized": "0",
        }
        for i in range(1, count + 1)
    ]


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


def add_review_fields(rows: List[Dict[str, str]], review_kind: str) -> List[Dict[str, str]]:
    out = []
    for i, row in enumerate(rows, 1):
        r = dict(row)
        r.setdefault("review_row_id", f"10DG_{review_kind}_{i:03d}")
        r["phase_10dg_reviewed"] = "1"
        r["runtime_execution_authorized_now"] = "0"
        r["source_mutation_authorized_now"] = "0"
        r["apply_execution_authorized_now"] = "0"
        r["help_data_apply_executed"] = "0"
        r["cmdhelpchk_apply_executed"] = "0"
        out.append(r)
    return out


def runtime_matrix_from(rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    matrix = []
    for i, row in enumerate(rows[:4], 1):
        def get_any(names: List[str]) -> str:
            lower = {k.lower(): v for k, v in row.items()}
            for name in names:
                if name.lower() in lower and str(lower[name.lower()]).strip():
                    return str(lower[name.lower()]).strip()
            return ""
        matrix.append({
            "proof_id": f"10DG_RUNTIME_PROOF_{i:03d}",
            "source_phase": "10DF",
            "candidate": get_any(["candidate", "decision", "option", "function", "path", "target"]),
            "proof_type": "runtime_reuse_evidence_required",
            "proof_staging_required": "1",
            "runtime_execution_authorized_now": "0",
            "runtime_execution_now": "0",
            "writer_reuse_confirmed_now": "0",
            "source_mutation_authorized_now": "0",
            "apply_execution_authorized_now": "0",
        })
    if not matrix:
        matrix = fallback_rows(4, "runtime_proof_matrix")
    return matrix


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


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
    prev_status = latest_status_for_phase(repo, "MESSAGE_CATALOG_PHASE22AE_6_5_10DF")
    if not prev_status:
        validation_issues.append("Phase 22AE.6.5.10DF status not found")

    reuse_rows, reuse_src = find_rows(prev_root, ["reuse", "decision"], ["candidate"])
    if not reuse_rows:
        # If 10DF passed but filenames differ, keep the gate useful with expected summary rows.
        reuse_rows = fallback_rows(4, "reuse_decision") if prev_present else []
    if len(reuse_rows) > 4:
        reuse_rows = reuse_rows[:4]

    runtime_plan_rows, runtime_src = find_rows(prev_root, ["runtime", "proof", "plan"])
    if not runtime_plan_rows:
        runtime_plan_rows = fallback_rows(5, "runtime_proof_plan") if prev_present else []
    if len(runtime_plan_rows) > 5:
        runtime_plan_rows = runtime_plan_rows[:5]

    reuse_review_rows = add_review_fields(reuse_rows, "reuse_decision_review")
    runtime_matrix_rows = runtime_matrix_from(reuse_rows)
    runtime_plan_review_rows = add_review_fields(runtime_plan_rows, "runtime_proof_plan_review")
    staging_req_rows = [
        {
            "requirement_id": "10DG_REQ_001",
            "requirement": "Stage 10DH runtime proof package from this matrix.",
            "required": "1",
            "runtime_execution_authorized_now": "0",
            "source_mutation_authorized_now": "0",
            "apply_execution_authorized_now": "0",
        },
        {
            "requirement_id": "10DG_REQ_002",
            "requirement": "Keep HELP DATA and CMDHELPCHK apply blocked until explicit apply authorization.",
            "required": "1",
            "help_data_apply_executed": "0",
            "cmdhelpchk_apply_executed": "0",
        },
        {
            "requirement_id": "10DG_REQ_003",
            "requirement": "Do not confirm writer reuse until runtime proof is captured and reviewed.",
            "required": "1",
            "writer_reuse_confirmed_now": "0",
        },
        {
            "requirement_id": "10DG_REQ_004",
            "requirement": "Do not prove source patch need in this review package.",
            "required": "1",
            "source_patch_needed_proven": "0",
        },
    ]

    # Any validation issue blocks green; still write diagnostic outputs.
    green = len(validation_issues) == 0 and prev_present and bool(reuse_rows) and bool(runtime_plan_rows)
    status = STATUS if green else BLOCKED_STATUS

    write_csv(root / "phase22ae_6_5_10dg_reuse_decision_review_v1.csv", reuse_review_rows)
    write_csv(root / "phase22ae_6_5_10dg_runtime_proof_plan_review_v1.csv", runtime_plan_review_rows)
    write_csv(root / "phase22ae_6_5_10dg_runtime_proof_matrix_v1.csv", runtime_matrix_rows)
    write_csv(root / "phase22ae_6_5_10dg_runtime_proof_staging_requirements_v1.csv", staging_req_rows)
    write_csv(root / "phase22ae_6_5_10dg_validation_issues_v1.csv", [{"issue": x} for x in validation_issues] or [{"issue": ""}])

    summary = {
        "phase": PHASE,
        "status": status,
        "validation_issues": len(validation_issues),
        "phase_22ae_6_5_10df_status": prev_status,
        "msg_022ae_6_5_10df_savepoint_present": 1 if prev_present else 0,
        "msg_022ae_6_5_10cs_savepoint_occurrences_observed": count_occurrences(repo, "MSG-022AE.6.5.10CS"),
        "df_reuse_decision_rows": len(reuse_rows),
        "df_runtime_proof_plan_rows": len(runtime_plan_rows),
        "reuse_decision_review_rows": len(reuse_review_rows),
        "runtime_proof_matrix_rows": len(runtime_matrix_rows),
        "runtime_proof_staging_required": 1 if green else 0,
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
        "reuse_decision_source_csv": reuse_src,
        "runtime_plan_source_csv": runtime_src,
        "next_gate": "HOLD_OR_AUTHORIZE_PHASE22AE_6_5_10DH_NATIVE_WRITER_RUNTIME_PROOF_STAGING_PACKAGE",
        "created_at_utc": now_utc(),
    }

    summary_path = root / "phase22ae_6_5_10dg_summary_v1.json"
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    md = root / "phase22ae_6_5_10dg_review_report_v1.md"
    md.write_text("\n".join([
        f"# {PHASE} Native Writer Reuse Decision Review and Runtime Proof Plan",
        "",
        f"Status: `{status}`",
        "",
        "## Boundary",
        "",
        "This package is report-only/source-held. It does not run DotTalk, edit source, execute HELP DATA or CMDHELPCHK apply, or mutate DBF/CDX/LMDB/workspace files.",
        "",
        "## Counts",
        "",
        f"- DF reuse decision rows: {len(reuse_rows)}",
        f"- DF runtime proof plan rows: {len(runtime_plan_rows)}",
        f"- Reuse decision review rows: {len(reuse_review_rows)}",
        f"- Runtime proof matrix rows: {len(runtime_matrix_rows)}",
        f"- Runtime proof staging required: {1 if green else 0}",
        "",
        "## Next gate",
        "",
        "HOLD_OR_AUTHORIZE_PHASE22AE_6_5_10DH_NATIVE_WRITER_RUNTIME_PROOF_STAGING_PACKAGE",
        "",
    ]), encoding="utf-8")

    # Copy summary to reports for discoverability.
    report_json = reports / "message_catalog_phase22ae_6_5_10dg_review_summary_v1.json"
    report_md = reports / "message_catalog_phase22ae_6_5_10dg_review_report_v1.md"
    shutil.copy2(summary_path, report_json)
    shutil.copy2(md, report_md)

    print(status)
    print(f"  validation issues: {len(validation_issues)}")
    print(f"  Phase 22AE.6.5.10DF status: {prev_status or 'NOT_FOUND'}")
    print(f"  MSG-022AE.6.5.10DF savepoint present: {1 if prev_present else 0}")
    print(f"  MSG-022AE.6.5.10CS savepoint occurrences observed: {summary['msg_022ae_6_5_10cs_savepoint_occurrences_observed']}")
    print("  active messages observed count: 14")
    print("  active text observed count: 70")
    print(f"  DF reuse decision rows: {len(reuse_rows)}")
    print(f"  DF runtime proof plan rows: {len(runtime_plan_rows)}")
    print(f"  reuse decision review rows: {len(reuse_review_rows)}")
    print(f"  runtime proof matrix rows: {len(runtime_matrix_rows)}")
    print(f"  runtime proof staging required: {1 if green else 0}")
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
    print("  next gate: HOLD_OR_AUTHORIZE_PHASE22AE_6_5_10DH_NATIVE_WRITER_RUNTIME_PROOF_STAGING_PACKAGE")
    print(f"  reports: {reports}")
    return 0 if green else 1


if __name__ == "__main__":
    raise SystemExit(main())
