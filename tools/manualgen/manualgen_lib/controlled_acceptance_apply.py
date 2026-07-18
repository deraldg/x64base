from __future__ import annotations

import csv
import json
import os
import shutil
import sys
from pathlib import Path
from typing import Any

from .paths import ManualgenPaths
from .runlog import RunLogger, utc_now_iso
from .util import relpath_posix, sha256_file, write_json


EXPECTED_TARGETS = {
    "docs/manuals/developer/manualgen/published/developer_manual_publication_v1/sections/sections/runtime_evidence_source_verification_and_canary_closure.md": "replace",
    "docs/manuals/developer/manualgen/published/developer_manual_publication_v1/sections/sections/command_surface_dispatch_and_entry_variants.md": "replace",
    "docs/manuals/developer/manualgen/published/developer_manual_publication_v1/appendices/partial_help_reference.md": "create",
    "docs/manuals/developer/manualgen/published/developer_manual_publication_v1/developer_manual_publication_v1_appendices.md": "replace",
    "docs/manuals/developer/manualgen/published/developer_manual_publication_v1/developer_manual_publication_v1.md": "replace",
    "docs/manuals/developer/manualgen/accepted_artifacts/primary_reader_artifact_v1.json": "regenerate_on_apply",
    "docs/manuals/developer/manualgen/accepted_manifests/developer_manual_canonical_manifest_v1.json": "regenerate_on_apply",
    "docs/manuals/developer/manualgen/accepted_manifests/DOCFLUSH-20260716-001_APPENDIX_ACCEPTANCE_RECORD.md": "generate_on_apply",
}


def _repo_file(repo_root: Path, value: str) -> Path:
    path = Path(value)
    path = path if path.is_absolute() else repo_root / path
    resolved = path.resolve()
    try:
        resolved.relative_to(repo_root.resolve())
    except ValueError as exc:
        raise ValueError(f"Path escapes repository root: {value}") from exc
    return resolved


def _json_bytes(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _sha_bytes(value: bytes) -> str:
    import hashlib

    return hashlib.sha256(value).hexdigest().upper()


def _atomic_write(path: Path, value: bytes, token: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.parent / f".{path.name}.{token}.tmp"
    if temp.exists():
        temp.unlink()
    temp.write_bytes(value)
    os.replace(temp, path)


def _read_ledger(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def _validate_authorization(
    text: str,
    plan_run: str,
    plan_hash: str,
    ledger_hash: str,
) -> list[str]:
    findings: list[str] = []
    required = (
        "Decision: authorized for canonical apply.",
        f"Plan run: `{plan_run}`.",
        f"Plan manifest SHA-256: `{plan_hash}`.",
        f"Mutation ledger SHA-256: `{ledger_hash}`.",
        "Mutation rows authorized: 8.",
        "Required interpreter: Python 3.12.",
    )
    for item in required:
        if item not in text:
            findings.append(f"AUTHORIZATION_REQUIRED_TEXT:{item}")
    return findings


def _final_after_bytes(
    row: dict[str, str],
    planned: bytes,
    plan_run: str,
    authorization_record: str,
    accepted_utc: str,
) -> bytes:
    action = row["action"]
    target = row["target"]
    if action in {"replace", "create"}:
        return planned
    if action == "regenerate_on_apply":
        payload = json.loads(planned.decode("utf-8-sig"))
        if target.endswith("primary_reader_artifact_v1.json"):
            expected = "PRIMARY_READER_CONTENT_ACCEPTANCE_PLANNED_POINTER_UNCHANGED"
            if payload.get("status") != expected:
                raise ValueError(f"Unexpected planned reader status: {payload.get('status')}")
            payload["status"] = "PRIMARY_READER_CONTENT_ACCEPTED_POINTER_UNCHANGED"
        elif target.endswith("developer_manual_canonical_manifest_v1.json"):
            expected = "CONTROLLED_SELECTIVE_MERGE_ACCEPTANCE_PLANNED_POINTER_UNCHANGED"
            if payload.get("status") != expected:
                raise ValueError(f"Unexpected planned canonical status: {payload.get('status')}")
            payload["status"] = "CONTROLLED_SELECTIVE_MERGE_ACCEPTED_POINTER_UNCHANGED"
        else:
            raise ValueError(f"Unexpected regenerate target: {target}")
        payload["acceptance_plan_run"] = plan_run
        payload["acceptance_authorization_record"] = authorization_record
        payload["accepted_utc"] = accepted_utc
        return _json_bytes(payload)
    if action == "generate_on_apply":
        text = planned.decode("utf-8")
        expected = "Status: PLANNED_NOT_APPLIED"
        if expected not in text:
            raise ValueError("Appendix acceptance preview status missing")
        text = text.replace(expected, "Status: ACCEPTED_BY_AUTHORIZED_APPLY", 1).rstrip()
        text = text.replace(
            "\n\nApply mode must replace this status with an execution result and retain the prior MDO-215 manifest as history.",
            "",
            1,
        )
        text += (
            f"\n\nApplied plan: `{plan_run}`  "
            f"\nAuthorization: `{authorization_record}`  "
            f"\nAccepted UTC: `{accepted_utc}`\n"
        )
        return text.encode("utf-8")
    raise ValueError(f"Unsupported action: {action}")


def _rollback(
    repo_root: Path,
    before_root: Path,
    before_rows: list[dict[str, Any]],
    token: str,
) -> list[str]:
    findings: list[str] = []
    for row in reversed(before_rows):
        target = repo_root / row["target"]
        try:
            if row["before_exists"]:
                backup = before_root / row["target"]
                _atomic_write(target, backup.read_bytes(), f"rollback-{token}")
            elif target.exists():
                target.unlink()
        except OSError as exc:
            findings.append(f"ROLLBACK:{row['target']}:{exc}")
    return findings


def _write_rollback_script(
    path: Path,
    repo_root: Path,
    before_rows: list[dict[str, Any]],
    plan_run: str,
) -> None:
    rows_json = json.dumps(before_rows, indent=2)
    script = f'''#!/usr/bin/env python3
from __future__ import annotations
import argparse
import os
import json
from pathlib import Path

PLAN_RUN = {plan_run!r}
REPO_ROOT = Path({str(repo_root)!r})
BACKUP_ROOT = Path(__file__).resolve().parent / "before"
ROWS = json.loads({rows_json!r})

parser = argparse.ArgumentParser(description="Rollback one authorized Manualgen acceptance apply.")
parser.add_argument("--confirm", required=True)
args = parser.parse_args()
if args.confirm != PLAN_RUN:
    raise SystemExit("Refusing rollback: --confirm must equal the accepted plan run")

for row in reversed(ROWS):
    target = REPO_ROOT / row["target"]
    if row["before_exists"]:
        source = BACKUP_ROOT / row["target"]
        target.parent.mkdir(parents=True, exist_ok=True)
        temp = target.parent / ("." + target.name + ".rollback.tmp")
        temp.write_bytes(source.read_bytes())
        os.replace(temp, target)
    elif target.exists():
        target.unlink()
print("rollback complete", PLAN_RUN)
'''
    path.write_text(script, encoding="utf-8")


def apply_controlled_acceptance(
    paths: ManualgenPaths,
    plan_run: str,
    authorization_record_value: str,
    logger: RunLogger | None = None,
) -> tuple[dict[str, Any], dict[str, int]]:
    findings: list[str] = []
    if sys.version_info[:2] != (3, 12):
        findings.append(
            f"PYTHON_VERSION_REQUIRED:3.12:observed={sys.version_info.major}.{sys.version_info.minor}"
        )

    plan_dir = (
        paths.manualgen_root
        / "generated"
        / "manualgen_controlled_acceptance_plans"
        / plan_run
    )
    manifest_path = plan_dir / "controlled_acceptance_plan_manifest.json"
    ledger_path = plan_dir / "controlled_acceptance_mutation_ledger.csv"
    if not manifest_path.is_file():
        findings.append("PLAN_MANIFEST_MISSING")
    if not ledger_path.is_file():
        findings.append("PLAN_LEDGER_MISSING")
    if findings:
        return {"status": "FAIL_PREFLIGHT", "findings": findings}, {
            "applied_rows": 0,
            "validation_findings": len(findings),
            "rollback_findings": 0,
        }

    manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    rows = _read_ledger(ledger_path)
    plan_hash = sha256_file(manifest_path)
    ledger_hash = sha256_file(ledger_path)
    if manifest.get("status") != "PASS_PLAN_ONLY":
        findings.append("PLAN_STATUS")
    if manifest.get("run_id") != plan_run:
        findings.append("PLAN_RUN")
    if manifest.get("apply_available") != 0 or manifest.get("canonical_files_mutated") != 0:
        findings.append("PLAN_BOUNDARY")
    if manifest.get("counts") != {
        "planned_mutation_rows": 8,
        "reviewed_topics": 8,
        "validation_findings": 0,
    }:
        findings.append("PLAN_COUNTS")
    if len(rows) != 8:
        findings.append(f"LEDGER_ROWS:{len(rows)}")
    row_map = {row.get("target", ""): row for row in rows}
    if set(row_map) != set(EXPECTED_TARGETS):
        findings.append("LEDGER_TARGET_SET")
    for target, action in EXPECTED_TARGETS.items():
        if row_map.get(target, {}).get("action") != action:
            findings.append(f"LEDGER_ACTION:{target}")
        if row_map.get(target, {}).get("apply_authorized") != "0":
            findings.append(f"PLAN_SELF_AUTHORIZED:{target}")

    try:
        authorization_path = _repo_file(paths.repo_root, authorization_record_value)
    except ValueError as exc:
        findings.append(f"AUTHORIZATION_PATH:{exc}")
        authorization_path = paths.repo_root / "__invalid__"
    authorization_text = (
        authorization_path.read_text(encoding="utf-8-sig", errors="replace")
        if authorization_path.is_file()
        else ""
    )
    if not authorization_text:
        findings.append("AUTHORIZATION_RECORD_MISSING")
    findings.extend(
        _validate_authorization(authorization_text, plan_run, plan_hash, ledger_hash)
        if authorization_text
        else []
    )

    planned_bytes: dict[str, bytes] = {}
    before_rows: list[dict[str, Any]] = []
    for row in rows:
        target_rel = row["target"]
        target = paths.repo_root / target_rel
        expected_exists = row["before_exists"] == "1"
        observed_exists = target.is_file()
        if observed_exists != expected_exists:
            findings.append(f"BEFORE_EXISTS:{target_rel}:{observed_exists}")
        observed_hash = sha256_file(target) if observed_exists else ""
        if observed_hash != row["before_sha256"]:
            findings.append(f"BEFORE_HASH:{target_rel}:{observed_hash}")
        planned_path = _repo_file(paths.repo_root, row["planned_candidate"])
        if not planned_path.is_file():
            findings.append(f"PLANNED_MISSING:{target_rel}")
            continue
        if sha256_file(planned_path) != row["planned_sha256"]:
            findings.append(f"PLANNED_HASH:{target_rel}")
        planned_bytes[target_rel] = planned_path.read_bytes()
        before_rows.append(
            {
                "target": target_rel,
                "before_exists": 1 if observed_exists else 0,
                "before_sha256": observed_hash,
                "before_size": target.stat().st_size if observed_exists else 0,
            }
        )

    if findings:
        return {"status": "FAIL_PREFLIGHT", "findings": findings}, {
            "applied_rows": 0,
            "validation_findings": len(findings),
            "rollback_findings": 0,
        }

    accepted_utc = utc_now_iso()
    auth_rel = relpath_posix(authorization_path, paths.repo_root)
    after_bytes: dict[str, bytes] = {}
    for row in rows:
        after_bytes[row["target"]] = _final_after_bytes(
            row,
            planned_bytes[row["target"]],
            plan_run,
            auth_rel,
            accepted_utc,
        )

    reader_target = "docs/manuals/developer/manualgen/published/developer_manual_publication_v1/developer_manual_publication_v1.md"
    reader_sha = _sha_bytes(after_bytes[reader_target])
    reader_record = json.loads(
        after_bytes[
            "docs/manuals/developer/manualgen/accepted_artifacts/primary_reader_artifact_v1.json"
        ].decode("utf-8")
    )
    canonical_record = json.loads(
        after_bytes[
            "docs/manuals/developer/manualgen/accepted_manifests/developer_manual_canonical_manifest_v1.json"
        ].decode("utf-8")
    )
    if str(reader_record.get("artifact_sha256", "")).upper() != reader_sha:
        findings.append("AFTER_READER_RECORD_HASH")
    if str(canonical_record.get("current_reference_sha256", "")).upper() != reader_sha:
        findings.append("AFTER_CANONICAL_RECORD_HASH")
    if findings:
        return {"status": "FAIL_STAGING", "findings": findings}, {
            "applied_rows": 0,
            "validation_findings": len(findings),
            "rollback_findings": 0,
        }

    token = logger.run_id if logger else plan_run
    backup_root = paths.manualgen_root / "backups" / f"docflush_controlled_acceptance_{token}"
    before_root = backup_root / "before"
    staged_root = backup_root / "staged_after"
    evidence_root = backup_root / "evidence"
    before_root.mkdir(parents=True, exist_ok=False)
    staged_root.mkdir(parents=True, exist_ok=False)
    evidence_root.mkdir(parents=True, exist_ok=False)

    for row in before_rows:
        if row["before_exists"]:
            source = paths.repo_root / row["target"]
            destination = before_root / row["target"]
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
    write_json(backup_root / "before_manifest.json", {"plan_run": plan_run, "rows": before_rows})
    shutil.copy2(manifest_path, evidence_root / manifest_path.name)
    shutil.copy2(ledger_path, evidence_root / ledger_path.name)
    shutil.copy2(authorization_path, evidence_root / authorization_path.name)

    staged_rows: list[dict[str, Any]] = []
    for target_rel, value in after_bytes.items():
        staged = staged_root / target_rel
        staged.parent.mkdir(parents=True, exist_ok=True)
        staged.write_bytes(value)
        staged_rows.append(
            {
                "target": target_rel,
                "after_sha256": sha256_file(staged),
                "after_size": len(value),
            }
        )
    write_json(
        backup_root / "staged_after_manifest.json",
        {"plan_run": plan_run, "accepted_utc": accepted_utc, "rows": staged_rows},
    )
    _write_rollback_script(
        backup_root / "rollback_controlled_acceptance.py",
        paths.repo_root,
        before_rows,
        plan_run,
    )
    (backup_root / "ROLLBACK_COMMAND.md").write_text(
        "# Rollback command\n\n"
        "Use the required Python 3.12 interpreter:\n\n"
        "```powershell\n"
        "$py12 = 'C:\\Users\\deral\\vcpkg\\installed\\x64-windows\\tools\\python3\\python.exe'\n"
        f"& $py12 '{backup_root / 'rollback_controlled_acceptance.py'}' --confirm {plan_run}\n"
        "```\n",
        encoding="utf-8",
    )

    applied = 0
    rollback_findings: list[str] = []
    try:
        for row in rows:
            target = paths.repo_root / row["target"]
            _atomic_write(target, after_bytes[row["target"]], token)
            applied += 1
        for staged in staged_rows:
            target = paths.repo_root / staged["target"]
            observed = sha256_file(target) if target.is_file() else ""
            if observed != staged["after_sha256"]:
                raise OSError(
                    f"After hash mismatch for {staged['target']}: {observed}"
                )
    except Exception as exc:  # noqa: BLE001 - must roll back every partial apply
        findings.append(f"APPLY:{exc}")
        rollback_findings = _rollback(paths.repo_root, before_root, before_rows, token)
        findings.extend(rollback_findings)

    status = "PASS_APPLIED" if not findings else "FAIL_ROLLED_BACK"
    execution = {
        "schema": "dottalk.manualgen.controlled_acceptance_execution.v1",
        "status": status,
        "plan_run": plan_run,
        "apply_run": token,
        "accepted_utc": accepted_utc,
        "authorization_record": auth_rel,
        "authorization_sha256": sha256_file(authorization_path),
        "plan_manifest_sha256": plan_hash,
        "mutation_ledger_sha256": ledger_hash,
        "applied_rows": applied,
        "findings": findings,
        "reader_pointer_mutated": 0,
        "publication_authority_claimed": 0,
        "after_rows": staged_rows,
    }
    execution_path = backup_root / "controlled_acceptance_execution_manifest.json"
    write_json(execution_path, execution)
    (backup_root / "CONTROLLED_ACCEPTANCE_EXECUTION_RECORD.md").write_text(
        "# Controlled Acceptance Execution Record\n\n"
        f"- Plan: `{plan_run}`\n"
        f"- Apply run: `{token}`\n"
        f"- Status: `{status}`\n"
        f"- Applied rows: {applied}\n"
        f"- Findings: {len(findings)}\n"
        "- Reader pointer mutated: 0\n"
        "- Website/publication mutation: 0\n",
        encoding="utf-8",
    )

    if logger:
        logger.artifact("controlled_acceptance_execution_manifest", execution_path, "Authorized eight-row apply result.")
        logger.artifact("controlled_acceptance_before_manifest", backup_root / "before_manifest.json", "Byte-preserved pre-apply state.")
        logger.artifact("controlled_acceptance_rollback", backup_root / "rollback_controlled_acceptance.py", "Python 3.12 rollback command.")
        logger.boundary("reader_pointer_mutated", 0, "PASS", "Pointer target path is unchanged.")
        logger.boundary("man_catalog_mutated", 0, "PASS", "MAN* catalogs excluded.")
        logger.boundary("help_meta_mutated", 0, "PASS", "HELP/META excluded.")
        logger.boundary("website_mutated", 0, "PASS", "Website publication is a later gate.")

    return {
        "status": status,
        "backup_root": relpath_posix(backup_root, paths.repo_root),
        "execution_manifest": relpath_posix(execution_path, paths.repo_root),
        "findings": findings,
    }, {
        "applied_rows": applied,
        "validation_findings": len(findings),
        "rollback_findings": len(rollback_findings),
    }
