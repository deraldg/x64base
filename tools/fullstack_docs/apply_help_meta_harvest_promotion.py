#!/usr/bin/env python3
"""Apply or roll back one authorized, hash-bound HELP/META harvest plan."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Callable


HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from check_help_meta_harvest_freshness import audit_workspace  # noqa: E402


Writer = Callable[[Path, bytes, str], None]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes((json.dumps(value, indent=2) + "\n").encode("utf-8"))


def repo_file(root: Path, value: str | Path) -> Path:
    path = Path(value)
    resolved = path.resolve() if path.is_absolute() else (root / path).resolve()
    try:
        resolved.relative_to(root.resolve())
    except ValueError as exc:
        raise ValueError(f"Path escapes repository root: {value}") from exc
    return resolved


def repo_relative(root: Path, path: Path) -> str:
    return str(path.resolve().relative_to(root.resolve())).replace("\\", "/")


def atomic_write(path: Path, value: bytes, token: str) -> None:
    temporary = path.parent / f".{path.name}.{token}.tmp"
    if temporary.exists():
        temporary.unlink()
    temporary.write_bytes(value)
    os.replace(temporary, path)


def authorization_findings(
    text: str,
    plan: dict[str, object],
    plan_hash: str,
) -> list[str]:
    required = (
        "Decision: authorized for canonical harvest apply.",
        f"Plan run: `{plan['run_id']}`.",
        f"Plan manifest SHA-256: `{plan_hash}`.",
        f"Mutation ledger SHA-256: `{plan['mutation_ledger_sha256']}`.",
        f"Mutation rows authorized: {plan['planned_mutation_rows']}.",
    )
    return [f"AUTHORIZATION_MISSING:{item}" for item in required if item not in text]


def validate_plan(
    root: Path,
    plan_path: Path,
    authorization_path: Path,
    confirm: str,
) -> tuple[dict[str, object], list[dict[str, object]], list[str]]:
    plan = load_json(plan_path)
    findings: list[str] = []
    if confirm != plan.get("run_id"):
        findings.append("CONFIRM_RUN_MISMATCH")
    for field, expected in (
        ("status", "PASS_PLAN_ONLY"),
        ("plan_only", 1),
        ("apply_available", 0),
        ("mutation_authorized", 0),
        ("canonical_files_mutated", 0),
    ):
        if plan.get(field) != expected:
            findings.append(f"PLAN_FIELD:{field}")

    ledger_path = repo_file(root, str(plan.get("mutation_ledger", "")))
    if not ledger_path.is_file():
        findings.append("LEDGER_MISSING")
        rows: list[dict[str, object]] = []
    else:
        if sha256(ledger_path) != plan.get("mutation_ledger_sha256"):
            findings.append("LEDGER_HASH_MISMATCH")
        rows = load_json(ledger_path)
        if not isinstance(rows, list):
            findings.append("LEDGER_NOT_LIST")
            rows = []
    if len(rows) != plan.get("planned_mutation_rows"):
        findings.append("LEDGER_ROW_COUNT_MISMATCH")

    plan_hash = sha256(plan_path)
    authorization_text = authorization_path.read_text(
        encoding="utf-8-sig"
    ) if authorization_path.is_file() else ""
    findings.extend(authorization_findings(authorization_text, plan, plan_hash))
    return plan, rows, findings


def apply_plan(
    repo_root: Path,
    plan_path: Path,
    authorization_path: Path,
    execution_dir: Path,
    record_out: Path,
    confirm: str,
    observed_at_utc: str,
    writer: Writer = atomic_write,
) -> dict[str, object]:
    root = repo_root.resolve()
    plan_path = repo_file(root, plan_path)
    authorization_path = repo_file(root, authorization_path)
    execution_dir = repo_file(root, execution_dir)
    record_out = repo_file(root, record_out)
    plan, rows, findings = validate_plan(
        root, plan_path, authorization_path, confirm
    )
    plan_hash = sha256(plan_path)
    authorization_hash = sha256(authorization_path) if authorization_path.is_file() else ""
    candidate_root = repo_file(root, str(plan.get("candidate_workspace", "")))
    canonical_root = repo_file(root, str(plan.get("canonical_workspace", "")))

    if execution_dir.exists() and any(execution_dir.iterdir()):
        findings.append("EXECUTION_DIR_NOT_EMPTY")
    candidate_audit = audit_workspace(root, candidate_root)
    if candidate_audit["status"] != "PASS":
        findings.append("CANDIDATE_NOT_CURRENT")

    validated: list[dict[str, object]] = []
    seen_targets: set[str] = set()
    for row in rows:
        target = repo_file(root, str(row.get("target", "")))
        candidate = repo_file(root, str(row.get("candidate", "")))
        try:
            relative = target.relative_to(canonical_root)
            candidate.relative_to(candidate_root)
        except ValueError:
            findings.append(f"ROW_SCOPE:{row.get('ordinal')}")
            continue
        target_key = str(target).lower()
        if target_key in seen_targets:
            findings.append(f"DUPLICATE_TARGET:{row.get('ordinal')}")
        seen_targets.add(target_key)
        if row.get("action") != "replace":
            findings.append(f"UNSUPPORTED_ACTION:{row.get('ordinal')}")
        if not target.is_file() or sha256(target) != row.get("before_sha256"):
            findings.append(f"BEFORE_HASH:{row.get('ordinal')}")
        if not candidate.is_file() or sha256(candidate) != row.get("after_sha256"):
            findings.append(f"CANDIDATE_HASH:{row.get('ordinal')}")
        validated.append({
            **row,
            "target_path": target,
            "candidate_path": candidate,
            "relative_path": relative,
        })

    record: dict[str, object] = {
        "schema": "dottalk.fullstack.help_meta_harvest_apply.v1",
        "observed_at_utc": observed_at_utc,
        "run_id": plan.get("run_id"),
        "plan_manifest": repo_relative(root, plan_path),
        "plan_manifest_sha256": plan_hash,
        "mutation_ledger": plan.get("mutation_ledger"),
        "mutation_ledger_sha256": plan.get("mutation_ledger_sha256"),
        "authorization_record": repo_relative(root, authorization_path),
        "authorization_sha256": authorization_hash,
        "status": "FAIL_PREFLIGHT" if findings else "READY",
        "findings": findings,
        "canonical_files_mutated": 0,
        "rollback_performed": 0,
        "backup_retention": "local_ignored",
        "rows": [],
    }
    if findings:
        write_json(record_out, record)
        return record

    before_root = execution_dir / "before"
    staged_root = execution_dir / "staged_after"
    before_root.mkdir(parents=True)
    staged_root.mkdir(parents=True)
    for row in validated:
        relative = row["relative_path"]
        before = before_root / relative
        staged = staged_root / relative
        before.parent.mkdir(parents=True, exist_ok=True)
        staged.parent.mkdir(parents=True, exist_ok=True)
        before.write_bytes(row["target_path"].read_bytes())
        staged.write_bytes(row["candidate_path"].read_bytes())
        if sha256(before) != row["before_sha256"]:
            findings.append(f"BACKUP_HASH:{row['ordinal']}")
        if sha256(staged) != row["after_sha256"]:
            findings.append(f"STAGED_HASH:{row['ordinal']}")
        record["rows"].append({
            "ordinal": row["ordinal"],
            "target": row["target"],
            "before_sha256": row["before_sha256"],
            "after_sha256": row["after_sha256"],
            "backup": repo_relative(root, before),
            "staged_after": repo_relative(root, staged),
        })
    if findings:
        record["status"] = "FAIL_STAGING"
        record["findings"] = findings
        write_json(execution_dir / "execution_manifest.json", record)
        write_json(record_out, record)
        return record

    applied: list[dict[str, object]] = []
    try:
        for row in validated:
            writer(
                row["target_path"],
                (staged_root / row["relative_path"]).read_bytes(),
                f"harvest-{row['ordinal']}",
            )
            applied.append(row)
        after_audit = audit_workspace(root, canonical_root)
        if after_audit["status"] != "PASS":
            raise RuntimeError("CANONICAL_E5_NOT_CURRENT")
        for row in validated:
            if sha256(row["target_path"]) != row["after_sha256"]:
                raise RuntimeError(f"AFTER_HASH:{row['ordinal']}")
        record["status"] = "APPLIED"
        record["canonical_files_mutated"] = len(applied)
        record["canonical_freshness_status"] = after_audit["status"]
    except Exception as exc:  # rollback is the safety boundary
        rollback_findings: list[str] = []
        for row in reversed(validated):
            backup = before_root / row["relative_path"]
            try:
                writer(
                    row["target_path"],
                    backup.read_bytes(),
                    f"harvest-rollback-{row['ordinal']}",
                )
                if sha256(row["target_path"]) != row["before_sha256"]:
                    rollback_findings.append(f"ROLLBACK_HASH:{row['ordinal']}")
            except Exception as rollback_exc:
                rollback_findings.append(
                    f"ROLLBACK_ERROR:{row['ordinal']}:{rollback_exc}"
                )
        record["status"] = (
            "FAILED_ROLLED_BACK" if not rollback_findings else "FAILED_ROLLBACK_INCOMPLETE"
        )
        record["findings"] = [f"APPLY_ERROR:{exc}"] + rollback_findings
        record["canonical_files_mutated"] = len(applied)
        record["rollback_performed"] = 1

    write_json(execution_dir / "execution_manifest.json", record)
    write_json(record_out, record)
    return record


def rollback_execution(
    repo_root: Path,
    execution_record: Path,
    confirm: str,
    observed_at_utc: str,
    record_out: Path,
    writer: Writer = atomic_write,
) -> dict[str, object]:
    root = repo_root.resolve()
    execution_record = repo_file(root, execution_record)
    record_out = repo_file(root, record_out)
    applied = load_json(execution_record)
    findings: list[str] = []
    if applied.get("status") != "APPLIED":
        findings.append("EXECUTION_NOT_APPLIED")
    if confirm != applied.get("run_id"):
        findings.append("CONFIRM_RUN_MISMATCH")
    rows = applied.get("rows", [])
    for row in rows:
        target = repo_file(root, row["target"])
        backup = repo_file(root, row["backup"])
        if not target.is_file() or sha256(target) != row["after_sha256"]:
            findings.append(f"AFTER_HASH:{row['ordinal']}")
        if not backup.is_file() or sha256(backup) != row["before_sha256"]:
            findings.append(f"BACKUP_HASH:{row['ordinal']}")
    result = {
        "schema": "dottalk.fullstack.help_meta_harvest_rollback.v1",
        "observed_at_utc": observed_at_utc,
        "run_id": applied.get("run_id"),
        "status": "FAIL_PREFLIGHT" if findings else "READY",
        "findings": findings,
        "restored_rows": 0,
    }
    if not findings:
        for row in reversed(rows):
            target = repo_file(root, row["target"])
            backup = repo_file(root, row["backup"])
            writer(target, backup.read_bytes(), f"harvest-manual-rollback-{row['ordinal']}")
        for row in rows:
            if sha256(repo_file(root, row["target"])) != row["before_sha256"]:
                findings.append(f"RESTORE_HASH:{row['ordinal']}")
        result["status"] = "ROLLED_BACK" if not findings else "ROLLBACK_INCOMPLETE"
        result["findings"] = findings
        result["restored_rows"] = len(rows) if not findings else 0
    write_json(record_out, result)
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    apply_parser = sub.add_parser("apply")
    apply_parser.add_argument("--repo-root", type=Path, default=Path("."))
    apply_parser.add_argument("--plan", type=Path, required=True)
    apply_parser.add_argument("--authorization", type=Path, required=True)
    apply_parser.add_argument("--execution-dir", type=Path, required=True)
    apply_parser.add_argument("--record-out", type=Path, required=True)
    apply_parser.add_argument("--confirm", required=True)
    apply_parser.add_argument("--observed-at-utc", required=True)
    rollback_parser = sub.add_parser("rollback")
    rollback_parser.add_argument("--repo-root", type=Path, default=Path("."))
    rollback_parser.add_argument("--execution-record", type=Path, required=True)
    rollback_parser.add_argument("--record-out", type=Path, required=True)
    rollback_parser.add_argument("--confirm", required=True)
    rollback_parser.add_argument("--observed-at-utc", required=True)
    args = parser.parse_args(argv)
    if args.command == "apply":
        result = apply_plan(
            args.repo_root,
            args.plan,
            args.authorization,
            args.execution_dir,
            args.record_out,
            args.confirm,
            args.observed_at_utc,
        )
        print(
            "%s: canonical_files_mutated=%d rollback_performed=%d"
            % (
                result["status"],
                result["canonical_files_mutated"],
                result["rollback_performed"],
            )
        )
        return 0 if result["status"] == "APPLIED" else 1
    result = rollback_execution(
        args.repo_root,
        args.execution_record,
        args.confirm,
        args.observed_at_utc,
        args.record_out,
    )
    print("%s: restored_rows=%d" % (result["status"], result["restored_rows"]))
    return 0 if result["status"] == "ROLLED_BACK" else 1


if __name__ == "__main__":
    raise SystemExit(main())
