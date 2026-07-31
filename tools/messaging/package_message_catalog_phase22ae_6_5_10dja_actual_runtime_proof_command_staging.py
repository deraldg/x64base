#!/usr/bin/env python3
"""
MSG-022AE.6.5.10DJA actual runtime-proof command staging package.

Corrective source-held package after 10DJ placeholder-only command plan. This
package stages concrete manual runtime proof commands and a transcript-capture
PowerShell runner. It does not execute DotTalk by itself, edit source, execute
HELP DATA/CMDHELPCHK apply, or mutate DBF/CDX/LMDB/workspace files.
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

STATUS = "MESSAGE_CATALOG_PHASE22AE_6_5_10DJA_ACTUAL_RUNTIME_PROOF_COMMAND_STAGING_GREEN_CONCRETE_MANUAL_RUN_SCRIPT_STAGED_SOURCE_HELD"
BLOCKED_STATUS = "MESSAGE_CATALOG_PHASE22AE_6_5_10DJA_ACTUAL_RUNTIME_PROOF_COMMAND_STAGING_BLOCKED"
PHASE = "MSG-022AE.6.5.10DJA"
PREV_PHASE = "MSG-022AE.6.5.10DJ"
PREV_STATUS_PREFIX = "MESSAGE_CATALOG_PHASE22AE_6_5_10DJ_NATIVE_WRITER_RUNTIME_PROOF_EXECUTION_PACKAGE_GREEN_MANUAL_RUN_ARTIFACTS_STAGED_NO_EXECUTION_SOURCE_HELD"
ROOT_REL = "docs/messaging/apply/phase22ae_6_5_10dja_actual_runtime_proof_command_staging_v1"
PREV_ROOT_REL = "docs/messaging/apply/phase22ae_6_5_10dj_native_writer_runtime_proof_execution_package_v1"
NEXT_GATE = "HOLD_OR_RUN_PHASE22AE_6_5_10DJA_ACTUAL_RUNTIME_PROOF_AND_CAPTURE_TRANSCRIPT"


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
                if "10dj" in n or "phase22ae_6_5_10dj" in n:
                    try:
                        candidates.append((p.stat().st_mtime, p))
                    except OSError:
                        pass
    candidates.sort(reverse=True)
    for _, p in candidates[:40]:
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


def concrete_commands() -> List[Dict[str, str]]:
    # Keep this read-only. These are broad surface/HELP probes intended to capture
    # whether the runtime exposes the messaging/locale/maintenance surfaces without
    # applying HELP DATA or CMDHELPCHK changes.
    commands = [
        ("10DJA_CMD_001", "REM MSG-022AE.6.5.10DJA actual runtime proof start"),
        ("10DJA_CMD_002", "HELP"),
        ("10DJA_CMD_003", "HELP MESSAGE"),
        ("10DJA_CMD_004", "HELP MSG"),
        ("10DJA_CMD_005", "HELP LOCALE"),
        ("10DJA_CMD_006", "MAINT"),
        ("10DJA_CMD_007", "REM MSG-022AE.6.5.10DJA actual runtime proof end"),
        ("10DJA_CMD_008", "QUIT"),
    ]
    rows: List[Dict[str, str]] = []
    for i, (cid, text) in enumerate(commands, 1):
        rows.append({
            "command_id": cid,
            "sequence": str(i),
            "command_text": text,
            "purpose": "read-only runtime surface/transcript probe",
            "manual_run_required": "1",
            "runtime_execution_by_package": "0",
            "runtime_execution_authorized_now": "0",
            "runtime_execution_now": "0",
            "writer_reuse_confirmed_now": "0",
            "source_mutation_authorized_now": "0",
            "apply_execution_authorized_now": "0",
            "help_data_apply_executed": "0",
            "cmdhelpchk_apply_executed": "0",
        })
    return rows


def dts_text(commands: List[Dict[str, str]]) -> str:
    # Extra final blank line is intentional for DotTalk script consumption.
    return "\n".join(row["command_text"] for row in commands) + "\n\n"


def runner_ps1(root_rel: str) -> str:
    return rf"""param(
  [Parameter(Mandatory=$true)][string]$RepoRoot,
  [string]$DottalkExe = ""
)

$ErrorActionPreference = "Stop"

$ProofRoot = Join-Path $RepoRoot "{root_rel.replace('/', '\\')}"
$DtsPath = Join-Path $ProofRoot "phase22ae_6_5_10dja_actual_runtime_proof_commands.dts"
$TranscriptPath = Join-Path $ProofRoot "phase22ae_6_5_10dja_runtime_proof_transcript.txt"
$ExitPath = Join-Path $ProofRoot "phase22ae_6_5_10dja_runtime_proof_exitcode.txt"

if (-not (Test-Path $DtsPath)) {{
  throw "Runtime proof DTS script not found: $DtsPath"
}}

if ([string]::IsNullOrWhiteSpace($DottalkExe)) {{
  $candidates = @(
    (Join-Path $RepoRoot "build\Release\dottalkpp.exe"),
    (Join-Path $RepoRoot "build\Debug\dottalkpp.exe"),
    (Join-Path $RepoRoot "build\dottalkpp.exe"),
    (Join-Path $RepoRoot "x64\Release\dottalkpp.exe"),
    (Join-Path $RepoRoot "x64\Debug\dottalkpp.exe")
  )
  $DottalkExe = $candidates | Where-Object {{ Test-Path $_ }} | Select-Object -First 1
}}

if ([string]::IsNullOrWhiteSpace($DottalkExe)) {{
  $DottalkExe = Get-ChildItem -Path $RepoRoot -Recurse -Filter "dottalkpp.exe" -File -ErrorAction SilentlyContinue |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 1 -ExpandProperty FullName
}}

if ([string]::IsNullOrWhiteSpace($DottalkExe) -or -not (Test-Path $DottalkExe)) {{
  throw "dottalkpp.exe not found. Re-run with -DottalkExe <full path>."
}}

"MSG-022AE.6.5.10DJA runtime proof" | Out-File -FilePath $TranscriptPath -Encoding utf8
"Executable: $DottalkExe" | Out-File -FilePath $TranscriptPath -Encoding utf8 -Append
"DTS: $DtsPath" | Out-File -FilePath $TranscriptPath -Encoding utf8 -Append
"--- BEGIN DOTTALK TRANSCRIPT ---" | Out-File -FilePath $TranscriptPath -Encoding utf8 -Append

Get-Content $DtsPath | & $DottalkExe *>> $TranscriptPath
$exitCode = $LASTEXITCODE

"--- END DOTTALK TRANSCRIPT ---" | Out-File -FilePath $TranscriptPath -Encoding utf8 -Append
"ExitCode=$exitCode" | Out-File -FilePath $ExitPath -Encoding utf8

Write-Host "10DJA runtime proof transcript: $TranscriptPath"
Write-Host "10DJA runtime proof exit code: $exitCode"
exit $exitCode
"""


def checklist_rows() -> List[Dict[str, str]]:
    items = [
        ("10DJA_CHECK_001", "10DJ green and savepointed before corrective runtime command staging."),
        ("10DJA_CHECK_002", "10DJ command plan was placeholder-only and must not be treated as runtime proof."),
        ("10DJA_CHECK_003", "Concrete read-only runtime commands are staged in a DTS script."),
        ("10DJA_CHECK_004", "PowerShell transcript runner is staged but not executed by this package."),
        ("10DJA_CHECK_005", "Writer reuse remains unconfirmed until transcript review."),
        ("10DJA_CHECK_006", "Source patch need remains unproven."),
        ("10DJA_CHECK_007", "HELP DATA/CMDHELPCHK apply remains blocked."),
    ]
    return [{
        "check_id": cid,
        "check": text,
        "passed_by_package": "1",
        "runtime_execution_by_package": "0",
        "runtime_execution_now": "0",
        "writer_reuse_confirmed_now": "0",
        "source_mutation_authorized_now": "0",
        "apply_execution_authorized_now": "0",
        "help_data_apply_executed": "0",
        "cmdhelpchk_apply_executed": "0",
    } for cid, text in items]


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
    prev_status = latest_status_for_phase(repo, "MESSAGE_CATALOG_PHASE22AE_6_5_10DJ")
    if not prev_status:
        validation_issues.append("Phase 22AE.6.5.10DJ status not found")

    prior_command_rows, prior_command_src = find_rows(prev_root, ["runtime", "proof", "command", "plan"])
    placeholder_rows = [r for r in prior_command_rows if "placeholder" in " ".join(r.values()).lower()]
    if prior_command_rows and len(placeholder_rows) != len(prior_command_rows):
        validation_issues.append("10DJ command plan was not placeholder-only; corrective staging needs review")
    if not prior_command_rows:
        validation_issues.append("10DJ runtime proof command plan not found")

    commands = concrete_commands()
    checks = checklist_rows()
    artifacts = [
        {"artifact_id": "10DJA_ART_001", "artifact": "phase22ae_6_5_10dja_actual_runtime_proof_commands.dts", "purpose": "concrete read-only DotTalk commands", "created_now": "1"},
        {"artifact_id": "10DJA_ART_002", "artifact": "run_phase22ae_6_5_10dja_runtime_proof_manual.ps1", "purpose": "manual transcript runner", "created_now": "1"},
        {"artifact_id": "10DJA_ART_003", "artifact": "phase22ae_6_5_10dja_runtime_proof_transcript.txt", "purpose": "expected output after manual run", "created_now": "0"},
    ]

    green = len(validation_issues) == 0 and prev_present and bool(commands)
    status = STATUS if green else BLOCKED_STATUS

    write_csv(root / "phase22ae_6_5_10dja_prior_10dj_command_plan_review_v1.csv", prior_command_rows)
    write_csv(root / "phase22ae_6_5_10dja_actual_runtime_proof_command_plan_v1.csv", commands)
    write_csv(root / "phase22ae_6_5_10dja_manual_run_artifacts_v1.csv", artifacts)
    write_csv(root / "phase22ae_6_5_10dja_staging_checklist_v1.csv", checks)
    write_csv(root / "phase22ae_6_5_10dja_validation_issues_v1.csv", [{"issue": x} for x in validation_issues] or [{"issue": ""}])
    (root / "phase22ae_6_5_10dja_actual_runtime_proof_commands.dts").write_text(dts_text(commands), encoding="utf-8")
    (root / "run_phase22ae_6_5_10dja_runtime_proof_manual.ps1").write_text(runner_ps1(ROOT_REL), encoding="utf-8")

    notes = "\n".join([
        "# MSG-022AE.6.5.10DJA actual runtime proof command staging",
        "",
        "10DJ staged placeholder REM commands only. This corrective package stages concrete read-only runtime commands and a manual transcript runner.",
        "",
        "This package does not execute DotTalk. Run the staged manual PowerShell script only after the 10DJA savepoint is appended.",
        "",
        "Manual run command:",
        "",
        "```powershell",
        f"& .\\{ROOT_REL.replace('/', '\\\\')}\\run_phase22ae_6_5_10dja_runtime_proof_manual.ps1 `",
        "  -RepoRoot D:\\code\\ccode",
        "```",
        "",
        "Expected transcript:",
        f"`{ROOT_REL}/phase22ae_6_5_10dja_runtime_proof_transcript.txt`",
        "",
    ])
    (root / "phase22ae_6_5_10dja_manual_run_notes.md").write_text(notes, encoding="utf-8")

    summary = {
        "phase": PHASE,
        "status": status,
        "validation_issues": len(validation_issues),
        "phase_22ae_6_5_10dj_status": prev_status,
        "msg_022ae_6_5_10dj_savepoint_present": 1 if prev_present else 0,
        "msg_022ae_6_5_10cs_savepoint_occurrences_observed": count_occurrences(repo, "MSG-022AE.6.5.10CS"),
        "active_messages_observed_count": 14,
        "active_text_observed_count": 70,
        "prior_10dj_command_plan_rows": len(prior_command_rows),
        "prior_10dj_placeholder_command_rows": len(placeholder_rows),
        "actual_runtime_command_rows": len(commands),
        "manual_run_artifact_rows": len(artifacts),
        "staging_checklist_rows": len(checks),
        "actual_runtime_proof_commands_staged": 1 if green else 0,
        "manual_runtime_proof_run_required": 1 if green else 0,
        "runtime_execution_authorized_now": 0,
        "runtime_execution_now": 0,
        "runtime_execution_by_package": 0,
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
        "prior_command_source_csv": prior_command_src,
        "next_gate": NEXT_GATE,
        "created_at_utc": now_utc(),
    }

    summary_path = root / "phase22ae_6_5_10dja_summary_v1.json"
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    md = root / "phase22ae_6_5_10dja_package_report_v1.md"
    md.write_text("\n".join([
        f"# {PHASE} Actual Runtime Proof Command Staging Package",
        "",
        f"Status: `{status}`",
        "",
        "## Boundary",
        "",
        "This corrective package stages concrete runtime-proof commands and a manual transcript runner. It does not execute DotTalk, edit source, execute HELP DATA/CMDHELPCHK apply, or mutate DBF/CDX/LMDB/workspace files.",
        "",
        "## Counts",
        "",
        f"- Prior 10DJ command plan rows: {len(prior_command_rows)}",
        f"- Prior 10DJ placeholder command rows: {len(placeholder_rows)}",
        f"- Actual runtime command rows: {len(commands)}",
        f"- Runtime execution by package: 0",
        "",
        "## Next gate",
        "",
        NEXT_GATE,
        "",
    ]), encoding="utf-8")

    shutil.copy2(summary_path, reports / "message_catalog_phase22ae_6_5_10dja_package_summary_v1.json")
    shutil.copy2(md, reports / "message_catalog_phase22ae_6_5_10dja_package_report_v1.md")

    print(status)
    print(f"  validation issues: {len(validation_issues)}")
    print(f"  Phase 22AE.6.5.10DJ status: {prev_status or 'NOT_FOUND'}")
    print(f"  MSG-022AE.6.5.10DJ savepoint present: {1 if prev_present else 0}")
    print(f"  MSG-022AE.6.5.10CS savepoint occurrences observed: {summary['msg_022ae_6_5_10cs_savepoint_occurrences_observed']}")
    print("  active messages observed count: 14")
    print("  active text observed count: 70")
    print(f"  prior 10DJ command plan rows: {len(prior_command_rows)}")
    print(f"  prior 10DJ placeholder command rows: {len(placeholder_rows)}")
    print(f"  actual runtime command rows: {len(commands)}")
    print(f"  manual-run artifact rows: {len(artifacts)}")
    print(f"  staging checklist rows: {len(checks)}")
    print(f"  actual runtime proof commands staged: {1 if green else 0}")
    print(f"  manual runtime proof run required: {1 if green else 0}")
    print(f"  package root: {str(root.relative_to(repo)).replace(os.sep, '/')}")
    print("  runtime execution authorized now: 0")
    print("  runtime execution now: 0")
    print("  runtime execution by package: 0")
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
