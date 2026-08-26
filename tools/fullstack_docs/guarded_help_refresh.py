#!/usr/bin/env python3
"""Plan, apply, or roll back a guarded canonical HELP refresh.

The apply path is fail-closed: exact plan authorization, a zero-open-runtime
probe, a byte-preserved complete backup, legacy-then-current execution, and
semantic readback are all required. Any failure restores the complete backup.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
from pathlib import Path
from typing import Any, Callable


PLAN_SCHEMA = "dottalk.fullstack.guarded_help_refresh_plan.v1"
AUTH_SCHEMA = "dottalk.fullstack.guarded_help_refresh_authorization.v1"
EXECUTION_SCHEMA = "dottalk.fullstack.guarded_help_refresh_execution.v1"
ROLLBACK_SCHEMA = "dottalk.fullstack.guarded_help_refresh_rollback.v1"
CONFIRM_APPLY = "APPLY GUARDED HELP REFRESH"
CONFIRM_ROLLBACK = "ROLLBACK GUARDED HELP REFRESH"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"JSON root must be an object: {path}")
    return data


def resolve_under(repo: Path, relative: str) -> Path:
    path = (repo / relative).resolve()
    try:
        path.relative_to(repo.resolve())
    except ValueError as exc:
        raise ValueError(f"path escapes repository: {relative}") from exc
    return path


def resolve_argument(repo: Path, path: Path) -> Path:
    return path.resolve() if path.is_absolute() else (repo / path).resolve()


def inventory(root: Path, repo: Path) -> list[dict[str, Any]]:
    return [
        {
            "path": path.relative_to(repo).as_posix(),
            "bytes": path.stat().st_size,
            "sha256": sha256_file(path),
        }
        for path in sorted(root.rglob("*"))
        if path.is_file()
    ]


def build_plan(
    repo: Path,
    run_id: str,
    observed_at_utc: str,
    command_script: Path,
) -> dict[str, Any]:
    repo = repo.resolve()
    help_root = repo / "dottalkpp" / "data" / "help"
    exe = repo / "build" / "src" / "Release" / "dottalkpp.exe"
    if not help_root.is_dir():
        raise ValueError(f"HELP root missing: {help_root}")
    if not exe.is_file():
        raise ValueError(f"runtime executable missing: {exe}")
    command_script = command_script.resolve()
    command_script.relative_to(repo)
    files = inventory(help_root, repo)
    if not files:
        raise ValueError("HELP root contains no files")
    newest_store_ns = max((repo / row["path"]).stat().st_mtime_ns for row in files)
    return {
        "schema": PLAN_SCHEMA,
        "run_id": run_id,
        "observed_at_utc": observed_at_utc,
        "status": "PLAN_ONLY",
        "mutation_authorized": 0,
        "help_root": "dottalkpp/data/help",
        "runtime_executable": {
            "path": exe.relative_to(repo).as_posix(),
            "bytes": exe.stat().st_size,
            "mtime_ns": exe.stat().st_mtime_ns,
            "sha256": sha256_file(exe),
        },
        "command_script": {
            "path": command_script.relative_to(repo).as_posix(),
            "sha256": sha256_file(command_script),
        },
        "command_order": [
            "CMDHELP BUILD LEGACY",
            "CMDHELP BUILD . D:\\code\\ccode\\src D:\\code\\ccode\\include D:\\code\\ccode\\bindings",
            "CMDHELPCHK",
        ],
        "protected_files": files,
        "protected_file_count": len(files),
        "store_newest_mtime_ns": newest_store_ns,
        "runtime_newer_than_store": exe.stat().st_mtime_ns > newest_store_ns,
        "required_controls": [
            "authorization binds exact plan SHA-256 and protected file count",
            "no dottalkpp.exe process is open before mutation",
            "complete recursive backup is byte-verified before execution",
            "legacy build precedes current build",
            "CMDHELPCHK reports no structural issues",
            "direct HELP table join validation passes",
            "all failures restore the complete before set",
        ],
        "publication_authority_claimed": 0,
    }


def validate_plan(repo: Path, plan: dict[str, Any]) -> None:
    if plan.get("schema") != PLAN_SCHEMA:
        raise ValueError("unsupported plan schema")
    if plan.get("mutation_authorized") != 0:
        raise ValueError("plan must not self-authorize mutation")
    if plan.get("publication_authority_claimed") != 0:
        raise ValueError("plan must not claim publication authority")
    rows = plan.get("protected_files")
    if not isinstance(rows, list) or not rows:
        raise ValueError("plan has no protected files")
    if plan.get("protected_file_count") != len(rows):
        raise ValueError("protected file count mismatch")
    for row in rows:
        path = resolve_under(repo, row["path"])
        if not path.is_file() or sha256_file(path) != row["sha256"]:
            raise ValueError(f"protected file drift: {row['path']}")
    exe = plan["runtime_executable"]
    exe_path = resolve_under(repo, exe["path"])
    if not exe_path.is_file() or sha256_file(exe_path) != exe["sha256"]:
        raise ValueError("runtime executable drift")
    script = plan["command_script"]
    script_path = resolve_under(repo, script["path"])
    if not script_path.is_file() or sha256_file(script_path) != script["sha256"]:
        raise ValueError("command script drift")


def default_process_probe() -> list[str]:
    cp = subprocess.run(
        ["tasklist", "/FI", "IMAGENAME eq dottalkpp.exe", "/FO", "CSV", "/NH"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    if cp.returncode != 0:
        raise RuntimeError(f"process probe failed: {cp.stderr.strip()}")
    return [line for line in cp.stdout.splitlines() if "dottalkpp.exe" in line.lower()]


def default_runner(repo: Path, command_script: Path) -> subprocess.CompletedProcess[str]:
    command = (
        "& { Set-Location -LiteralPath '"
        + str(repo).replace("'", "''")
        + "'; .\\datarun.ps1 -CommandLines (Get-Content -LiteralPath '"
        + str(command_script).replace("'", "''")
        + "') }"
    )
    return subprocess.run(
        ["powershell", "-NoProfile", "-Command", command],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )


def default_semantic_validator(repo: Path) -> tuple[bool, str]:
    cp = subprocess.run(
        ["python", str(repo / "tools" / "coordination" / "help_store_check.py"), "--json"],
        cwd=repo,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    return cp.returncode == 0, cp.stdout


def restore_complete(help_root: Path, backup_dir: Path) -> None:
    expected = help_root.resolve()
    if expected.name.lower() != "help" or expected.parent.name.lower() != "data":
        raise ValueError(f"refusing broad restore target: {expected}")
    if not backup_dir.is_dir():
        raise ValueError(f"backup missing: {backup_dir}")
    shutil.rmtree(help_root)
    shutil.copytree(backup_dir, help_root)


def apply_plan(
    repo: Path,
    plan_path: Path,
    authorization_path: Path,
    backup_dir: Path,
    transcript_path: Path,
    execution_path: Path,
    confirm: str,
    observed_at_utc: str,
    runner: Callable[[Path, Path], subprocess.CompletedProcess[str]] = default_runner,
    semantic_validator: Callable[[Path], tuple[bool, str]] = default_semantic_validator,
    process_probe: Callable[[], list[str]] = default_process_probe,
) -> dict[str, Any]:
    repo = repo.resolve()
    plan_path = resolve_argument(repo, plan_path)
    authorization_path = resolve_argument(repo, authorization_path)
    backup_dir = resolve_argument(repo, backup_dir)
    transcript_path = resolve_argument(repo, transcript_path)
    execution_path = resolve_argument(repo, execution_path)
    plan = load_json(plan_path)
    auth = load_json(authorization_path)
    if confirm != CONFIRM_APPLY:
        raise ValueError("apply confirmation phrase mismatch")
    if auth.get("schema") != AUTH_SCHEMA or auth.get("authorized") is not True:
        raise ValueError("valid owner authorization is required")
    if auth.get("plan_sha256") != sha256_file(plan_path):
        raise ValueError("authorization does not bind this plan")
    if auth.get("run_id") != plan.get("run_id"):
        raise ValueError("authorization run id mismatch")
    if auth.get("protected_file_count") != plan.get("protected_file_count"):
        raise ValueError("authorization protected file count mismatch")
    if auth.get("control_sha256") != sha256_file(Path(__file__).resolve()):
        raise ValueError("authorization does not bind this apply control")
    validate_plan(repo, plan)
    open_processes = process_probe()
    if open_processes:
        raise ValueError(f"dottalkpp.exe is open: {open_processes}")

    help_root = resolve_under(repo, plan["help_root"])
    if backup_dir.exists():
        raise ValueError(f"backup target already exists: {backup_dir}")
    backup_dir.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(help_root, backup_dir)
    before_rows = plan["protected_files"]
    for row in before_rows:
        backup = backup_dir / Path(row["path"]).relative_to(Path(plan["help_root"]))
        if not backup.is_file() or sha256_file(backup) != row["sha256"]:
            raise ValueError(f"backup verification failed: {row['path']}")

    record: dict[str, Any] = {
        "schema": EXECUTION_SCHEMA,
        "run_id": plan["run_id"],
        "observed_at_utc": observed_at_utc,
        "plan_path": plan_path.relative_to(repo).as_posix(),
        "plan_sha256": sha256_file(plan_path),
        "authorization_path": authorization_path.relative_to(repo).as_posix(),
        "authorization_sha256": sha256_file(authorization_path),
        "backup_dir": str(backup_dir.resolve()),
        "protected_file_count": len(before_rows),
        "rollback_performed": 0,
        "publication_authority_claimed": 0,
    }
    transcript_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        result = runner(repo, resolve_under(repo, plan["command_script"]["path"]))
        transcript_path.write_text(result.stdout, encoding="utf-8")
        transcript = result.stdout
        findings = []
        if result.returncode != 0:
            findings.append(f"RUNTIME_EXIT:{result.returncode}")
        required_text = [
            "CMDHELP LEGACY wrote:",
            "Usage contracts mined directly:",
            "OK no structural issues found",
            "DOCFLUSH-E2-REFRESH-END",
        ]
        for marker in required_text:
            if marker not in transcript:
                findings.append(f"TRANSCRIPT_MARKER_MISSING:{marker}")
        if "Unknown command" in transcript:
            findings.append("TRANSCRIPT_UNKNOWN_COMMAND")
        semantic_ok, semantic_output = semantic_validator(repo)
        if not semantic_ok:
            findings.append("SEMANTIC_HELP_STORE_CHECK_FAILED")
        after_rows = inventory(help_root, repo)
        newest_after_ns = max((repo / row["path"]).stat().st_mtime_ns for row in after_rows)
        if newest_after_ns <= plan["runtime_executable"]["mtime_ns"]:
            findings.append("STORE_NOT_NEWER_THAN_RUNTIME")
        if findings:
            raise RuntimeError(";".join(findings))
        record.update(
            {
                "status": "APPLIED",
                "runtime_exit": result.returncode,
                "transcript_path": transcript_path.relative_to(repo).as_posix(),
                "transcript_sha256": sha256_file(transcript_path),
                "semantic_help_store_check": "PASS",
                "semantic_help_store_check_output": semantic_output,
                "after_files": after_rows,
                "after_file_count": len(after_rows),
                "changed_file_count": sum(
                    1
                    for row in after_rows
                    if next((old["sha256"] for old in before_rows if old["path"] == row["path"]), "")
                    != row["sha256"]
                ),
                "findings": [],
            }
        )
    except Exception as exc:
        restore_complete(help_root, backup_dir)
        record.update(
            {
                "status": "FAILED_ROLLED_BACK",
                "rollback_performed": 1,
                "findings": [f"APPLY_ERROR:{exc}"],
            }
        )
        write_json(execution_path, record)
        raise
    write_json(execution_path, record)
    return record


def rollback_execution(
    repo: Path,
    execution_path: Path,
    record_out: Path,
    confirm: str,
    observed_at_utc: str,
) -> dict[str, Any]:
    repo = repo.resolve()
    execution_path = resolve_argument(repo, execution_path)
    record_out = resolve_argument(repo, record_out)
    execution = load_json(execution_path)
    if confirm != CONFIRM_ROLLBACK:
        raise ValueError("rollback confirmation phrase mismatch")
    if execution.get("schema") != EXECUTION_SCHEMA or execution.get("status") != "APPLIED":
        raise ValueError("rollback requires a successful execution record")
    help_root = repo / "dottalkpp" / "data" / "help"
    current = inventory(help_root, repo)
    if current != execution.get("after_files"):
        raise ValueError("current HELP store no longer matches the execution after set")
    backup = Path(execution["backup_dir"])
    restore_complete(help_root, backup)
    payload = {
        "schema": ROLLBACK_SCHEMA,
        "run_id": execution["run_id"],
        "observed_at_utc": observed_at_utc,
        "execution_sha256": sha256_file(execution_path),
        "status": "ROLLED_BACK",
        "restored_file_count": len(inventory(help_root, repo)),
    }
    write_json(record_out, payload)
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    plan_parser = sub.add_parser("plan")
    plan_parser.add_argument("--repo-root", type=Path, default=Path("."))
    plan_parser.add_argument("--run-id", required=True)
    plan_parser.add_argument("--observed-at-utc", required=True)
    plan_parser.add_argument("--command-script", type=Path, required=True)
    plan_parser.add_argument("--plan-out", type=Path, required=True)
    apply_parser = sub.add_parser("apply")
    apply_parser.add_argument("--repo-root", type=Path, default=Path("."))
    apply_parser.add_argument("--plan", type=Path, required=True)
    apply_parser.add_argument("--authorization", type=Path, required=True)
    apply_parser.add_argument("--backup-dir", type=Path, required=True)
    apply_parser.add_argument("--transcript-out", type=Path, required=True)
    apply_parser.add_argument("--execution-out", type=Path, required=True)
    apply_parser.add_argument("--confirm", required=True)
    apply_parser.add_argument("--observed-at-utc", required=True)
    rollback_parser = sub.add_parser("rollback")
    rollback_parser.add_argument("--repo-root", type=Path, default=Path("."))
    rollback_parser.add_argument("--execution", type=Path, required=True)
    rollback_parser.add_argument("--record-out", type=Path, required=True)
    rollback_parser.add_argument("--confirm", required=True)
    rollback_parser.add_argument("--observed-at-utc", required=True)
    args = parser.parse_args()

    repo = args.repo_root.resolve()
    if args.command == "plan":
        plan = build_plan(repo, args.run_id, args.observed_at_utc, args.command_script)
        write_json(args.plan_out, plan)
        print(json.dumps(plan, indent=2, sort_keys=True))
        return 0
    if args.command == "apply":
        result = apply_plan(
            repo,
            args.plan,
            args.authorization,
            args.backup_dir,
            args.transcript_out,
            args.execution_out,
            args.confirm,
            args.observed_at_utc,
        )
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    result = rollback_execution(repo, args.execution, args.record_out, args.confirm, args.observed_at_utc)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
