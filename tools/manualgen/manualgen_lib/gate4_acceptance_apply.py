from __future__ import annotations

import csv
import hashlib
import json
import os
import shutil
import sys
from pathlib import Path
from typing import Any

from .runlog import RunLogger, utc_now_iso
from .util import relpath_posix, sha256_file, write_json


PUBLICATION = "docs/manuals/developer/manualgen/published/developer_manual_publication_v1"
READER = f"{PUBLICATION}/developer_manual_publication_v1.md"
PRIMARY_RECORD = "docs/manuals/developer/manualgen/accepted_artifacts/primary_reader_artifact_v1.json"
CANONICAL_RECORD = "docs/manuals/developer/manualgen/accepted_manifests/developer_manual_canonical_manifest_v1.json"
COMMAND_RECORD = "docs/manuals/developer/manualgen/accepted_artifacts/command_reference_artifact_v1.json"
FINALIZED_RECORDS = {PRIMARY_RECORD, CANONICAL_RECORD, COMMAND_RECORD}
EXPECTED_SECTIONS = {
    "documentation_modeling_and_project_notes.md",
    "educational_and_demo_commands.md",
    "functions_and_expression_helpers.md",
    "getting_started_and_session_basics.md",
    "help_metadata_and_selfdoc.md",
    "import_export_and_storage_bridges.md",
    "indexing_order_and_relations.md",
    "legacy_and_compatibility_surfaces.md",
    "relations_and_tuple_views.md",
    "scripting_and_control_flow.md",
    "system_shell_and_files.md",
    "tables_records_and_data_editing.md",
    "transactions_locking_and_buffering.md",
    "workspaces_areas_and_session_state.md",
}


def _repo_file(repo_root: Path, value: str) -> Path:
    path = Path(value)
    resolved = (path if path.is_absolute() else repo_root / path).resolve()
    try:
        resolved.relative_to(repo_root.resolve())
    except ValueError as exc:
        raise ValueError(f"path escapes repository: {value}") from exc
    return resolved


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def _json_bytes(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _sha_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest().upper()


def _atomic_write(path: Path, value: bytes, token: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.parent / f".{path.name}.{token}.tmp"
    if temp.exists():
        temp.unlink()
    temp.write_bytes(value)
    os.replace(temp, path)


def validate_gate4_authorization(
    payload: dict[str, Any], plan_run: str, manifest_hash: str, ledger_hash: str
) -> list[str]:
    findings: list[str] = []
    expected = {
        "schema": "dottalk.manualgen.gate4_apply_authorization.v1",
        "decision": "AUTHORIZED_FOR_CANONICAL_APPLY",
        "plan_run": plan_run,
        "plan_manifest_sha256": manifest_hash,
        "mutation_ledger_sha256": ledger_hash,
        "mutation_rows_authorized": 183,
        "required_interpreter": "Python 3.12",
    }
    for key, value in expected.items():
        if payload.get(key) != value:
            findings.append(f"AUTHORIZATION:{key}:{payload.get(key)}")
    if set(payload.get("apply_time_finalization_targets", [])) != FINALIZED_RECORDS:
        findings.append("AUTHORIZATION:apply_time_finalization_targets")
    return findings


def finalize_gate4_record(
    target: str,
    planned: bytes,
    plan_run: str,
    authorization_record: str,
    accepted_utc: str,
) -> bytes:
    if target not in FINALIZED_RECORDS:
        return planned
    payload = json.loads(planned.decode("utf-8-sig"))
    payload["acceptance_plan_run"] = plan_run
    payload["acceptance_authorization_record"] = authorization_record
    payload["authorization_record"] = authorization_record
    payload["accepted_utc"] = accepted_utc
    if target == PRIMARY_RECORD:
        payload["status"] = "PRIMARY_READER_AND_COMMAND_REFERENCE_ACCEPTED_POINTER_UNCHANGED"
    elif target == CANONICAL_RECORD:
        payload["status"] = "GATE4_CANONICAL_READER_AND_COMMAND_REFERENCE_ACCEPTED"
    else:
        if payload.get("status") != "ACCEPTED_PENDING_EXACT_GATE4_APPLY":
            raise ValueError(f"unexpected planned command-reference status: {payload.get('status')}")
        payload["status"] = "ACCEPTED_COMMAND_REFERENCE"
    return _json_bytes(payload)


def _validate_target_set(rows: list[dict[str, str]]) -> list[str]:
    findings: list[str] = []
    targets = [row.get("target", "") for row in rows]
    if len(rows) != 183 or len(set(targets)) != 183:
        findings.append(f"LEDGER_ROWS_OR_UNIQUENESS:{len(rows)}:{len(set(targets))}")
    page_prefix = f"{PUBLICATION}/command_reference_v1/commands/"
    section_prefix = f"{PUBLICATION}/sections/sections/"
    pages = {Path(target).name for target in targets if target.startswith(page_prefix)}
    sections = {Path(target).name for target in targets if target.startswith(section_prefix)}
    expected_other = {
        f"{PUBLICATION}/command_reference_v1/README.md",
        READER,
        PRIMARY_RECORD,
        CANONICAL_RECORD,
        COMMAND_RECORD,
    }
    observed_other = {
        target
        for target in targets
        if not target.startswith(page_prefix) and not target.startswith(section_prefix)
    }
    if len(pages) != 164 or any(not name.endswith(".md") for name in pages):
        findings.append(f"COMMAND_PAGE_SET:{len(pages)}")
    if sections != EXPECTED_SECTIONS:
        findings.append(f"SECTION_SET:{len(sections)}")
    if observed_other != expected_other:
        findings.append("OTHER_TARGET_SET")
    creates = sum(row.get("operation") == "CREATE" for row in rows)
    replaces = sum(row.get("operation") == "REPLACE" for row in rows)
    if (creates, replaces) != (166, 17):
        findings.append(f"OPERATION_COUNTS:{creates}:{replaces}")
    return findings


def _priority(target: str) -> tuple[int, str]:
    if "/command_reference_v1/" in target:
        return 0, target
    if "/sections/sections/" in target:
        return 1, target
    if target == READER:
        return 2, target
    return 3, target


def _rollback(repo_root: Path, before_root: Path, rows: list[dict[str, Any]], token: str) -> list[str]:
    findings: list[str] = []
    for row in reversed(rows):
        target = repo_root / row["target"]
        try:
            if row["before_exists"]:
                backup = before_root / row["target"]
                _atomic_write(target, backup.read_bytes(), f"rollback-{token}")
            elif target.is_file():
                target.unlink()
        except OSError as exc:
            findings.append(f"ROLLBACK:{row['target']}:{exc}")
    return findings


def _write_rollback_script(path: Path, repo_root: Path, rows: list[dict[str, Any]], plan_run: str) -> None:
    rows_json = json.dumps(rows, separators=(",", ":"))
    script = f'''#!/usr/bin/env python3
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path

PLAN_RUN = {plan_run!r}
REPO_ROOT = Path({str(repo_root)!r})
BACKUP_ROOT = Path(__file__).resolve().parent / "before"
ROWS = json.loads({rows_json!r})

parser = argparse.ArgumentParser(description="Rollback one authorized Gate 4 documentation apply.")
parser.add_argument("--confirm", required=True)
args = parser.parse_args()
if args.confirm != PLAN_RUN:
    raise SystemExit("Refusing rollback: --confirm must equal the Gate 4 plan run")

for row in reversed(ROWS):
    target = REPO_ROOT / row["target"]
    if row["before_exists"]:
        source = BACKUP_ROOT / row["target"]
        target.parent.mkdir(parents=True, exist_ok=True)
        temp = target.parent / ("." + target.name + ".gate4-rollback.tmp")
        temp.write_bytes(source.read_bytes())
        os.replace(temp, target)
    elif target.is_file():
        target.unlink()
print("Gate 4 rollback complete", PLAN_RUN)
'''
    path.write_text(script, encoding="utf-8")


def apply_gate4_acceptance(
    paths,
    plan_run: str,
    authorization_record_value: str,
    logger: RunLogger | None = None,
) -> tuple[dict[str, Any], dict[str, int]]:
    findings: list[str] = []
    if sys.version_info[:2] != (3, 12):
        findings.append(f"PYTHON_VERSION_REQUIRED:3.12:observed={sys.version_info.major}.{sys.version_info.minor}")
    plan_dir = paths.manualgen_root / "generated" / "manualgen_gate4_acceptance_plans" / plan_run
    manifest_path = plan_dir / "gate4_acceptance_plan_manifest.json"
    ledger_path = plan_dir / "gate4_planned_mutations.csv"
    if not manifest_path.is_file():
        findings.append("PLAN_MANIFEST_MISSING")
    if not ledger_path.is_file():
        findings.append("PLAN_LEDGER_MISSING")
    if findings:
        return {"status": "FAIL_PREFLIGHT", "findings": findings}, {"applied_rows": 0, "validation_findings": len(findings), "rollback_findings": 0}

    manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    rows = _read_csv(ledger_path)
    manifest_hash = sha256_file(manifest_path)
    ledger_hash = sha256_file(ledger_path)
    if manifest.get("schema") != "dottalk.manualgen.gate4_acceptance_plan.v1":
        findings.append("PLAN_SCHEMA")
    if manifest.get("run_id") != plan_run or manifest.get("status") != "PASS_PLAN_ONLY":
        findings.append("PLAN_STATUS_OR_RUN")
    if manifest.get("plan_only") != 1 or manifest.get("apply_available") != 0:
        findings.append("PLAN_BOUNDARY")
    expected_counts = {
        "planned_mutation_rows": 183,
        "planned_create_rows": 166,
        "planned_replace_rows": 17,
        "command_pages": 164,
        "command_indexes": 1,
        "section_status_files": 14,
        "reader_link_rewrites": 164,
        "reader_begin_markers": 24,
        "reader_end_markers": 24,
        "reader_historical_statuses": 14,
        "reader_review_statuses": 0,
        "reader_command_destinations": 164,
        "findings": 0,
    }
    for key, expected in expected_counts.items():
        if manifest.get("counts", {}).get(key) != expected:
            findings.append(f"PLAN_COUNT:{key}:{manifest.get('counts', {}).get(key)}")
    findings.extend(_validate_target_set(rows))

    try:
        authorization_path = _repo_file(paths.repo_root, authorization_record_value)
    except ValueError as exc:
        findings.append(f"AUTHORIZATION_PATH:{exc}")
        authorization_path = paths.repo_root / "__invalid__"
    try:
        authorization = json.loads(authorization_path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        findings.append(f"AUTHORIZATION_INVALID:{exc}")
        authorization = {}
    findings.extend(validate_gate4_authorization(authorization, plan_run, manifest_hash, ledger_hash))

    planned_bytes: dict[str, bytes] = {}
    before_rows: list[dict[str, Any]] = []
    staged_prefix = relpath_posix(plan_dir / "staged_after", paths.repo_root) + "/"
    for row in rows:
        target_rel = row.get("target", "")
        target = paths.repo_root / target_rel
        expected_exists = row.get("before_exists") == "1"
        observed_exists = target.is_file()
        if observed_exists != expected_exists:
            findings.append(f"BEFORE_EXISTS:{target_rel}:{int(observed_exists)}")
        observed_hash = sha256_file(target) if observed_exists else "ABSENT"
        if observed_hash != row.get("before_sha256"):
            findings.append(f"BEFORE_HASH:{target_rel}:{observed_hash}")
        staged_rel = row.get("staged_path", "")
        if not staged_rel.startswith(staged_prefix):
            findings.append(f"STAGED_PATH_BOUNDARY:{target_rel}")
            continue
        try:
            staged = _repo_file(paths.repo_root, staged_rel)
        except ValueError as exc:
            findings.append(f"STAGED_PATH:{target_rel}:{exc}")
            continue
        if not staged.is_file() or sha256_file(staged) != row.get("staged_sha256"):
            findings.append(f"STAGED_HASH:{target_rel}")
            continue
        planned_bytes[target_rel] = staged.read_bytes()
        before_rows.append({
            "target": target_rel,
            "before_exists": int(observed_exists),
            "before_sha256": observed_hash,
            "before_size": target.stat().st_size if observed_exists else 0,
        })
    if findings:
        return {"status": "FAIL_PREFLIGHT", "findings": findings}, {"applied_rows": 0, "validation_findings": len(findings), "rollback_findings": 0}

    accepted_utc = utc_now_iso()
    authorization_rel = relpath_posix(authorization_path, paths.repo_root)
    after_bytes = {
        row["target"]: finalize_gate4_record(
            row["target"], planned_bytes[row["target"]], plan_run, authorization_rel, accepted_utc
        )
        for row in rows
    }
    reader_sha = _sha_bytes(after_bytes[READER])
    primary = json.loads(after_bytes[PRIMARY_RECORD].decode("utf-8"))
    canonical = json.loads(after_bytes[CANONICAL_RECORD].decode("utf-8"))
    command = json.loads(after_bytes[COMMAND_RECORD].decode("utf-8"))
    if str(primary.get("artifact_sha256", "")).upper() != reader_sha:
        findings.append("FINAL_PRIMARY_READER_HASH")
    if str(canonical.get("current_reference_sha256", "")).upper() != reader_sha:
        findings.append("FINAL_CANONICAL_READER_HASH")
    if str(command.get("reader_sha256", "")).upper() != reader_sha:
        findings.append("FINAL_COMMAND_READER_HASH")
    if findings:
        return {"status": "FAIL_STAGING", "findings": findings}, {"applied_rows": 0, "validation_findings": len(findings), "rollback_findings": 0}

    token = logger.run_id if logger else plan_run
    backup_root = paths.manualgen_root / "backups" / f"docflush_gate4_acceptance_{token}"
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

    after_rows: list[dict[str, Any]] = []
    for target_rel, value in after_bytes.items():
        staged = staged_root / target_rel
        staged.parent.mkdir(parents=True, exist_ok=True)
        staged.write_bytes(value)
        after_rows.append({"target": target_rel, "after_sha256": sha256_file(staged), "after_size": len(value)})
    after_rows.sort(key=lambda row: row["target"])
    write_json(backup_root / "staged_after_manifest.json", {"plan_run": plan_run, "accepted_utc": accepted_utc, "rows": after_rows})
    rollback_path = backup_root / "rollback_gate4_acceptance.py"
    _write_rollback_script(rollback_path, paths.repo_root, before_rows, plan_run)
    (backup_root / "ROLLBACK_COMMAND.md").write_text(
        "# Gate 4 rollback command\n\n```powershell\n"
        "$py12 = 'D:\\code\\ccode\\.venv312\\Scripts\\python.exe'\n"
        f"& $py12 '{rollback_path}' --confirm {plan_run}\n```\n",
        encoding="utf-8",
    )

    applied = 0
    rollback_findings: list[str] = []
    try:
        for row in sorted(rows, key=lambda item: _priority(item["target"])):
            _atomic_write(paths.repo_root / row["target"], after_bytes[row["target"]], token)
            applied += 1
        after_by_target = {row["target"]: row for row in after_rows}
        for target_rel, row in after_by_target.items():
            target = paths.repo_root / target_rel
            if not target.is_file() or sha256_file(target) != row["after_sha256"]:
                raise OSError(f"after hash mismatch: {target_rel}")
    except Exception as exc:  # noqa: BLE001 - partial apply must always roll back
        findings.append(f"APPLY:{exc}")
        rollback_findings = _rollback(paths.repo_root, before_root, before_rows, token)
        findings.extend(rollback_findings)

    status = "PASS_APPLIED" if not findings else "FAIL_ROLLED_BACK"
    execution = {
        "schema": "dottalk.manualgen.gate4_acceptance_execution.v1",
        "status": status,
        "plan_run": plan_run,
        "apply_run": token,
        "accepted_utc": accepted_utc,
        "authorization_record": authorization_rel,
        "authorization_sha256": sha256_file(authorization_path),
        "plan_manifest_sha256": manifest_hash,
        "mutation_ledger_sha256": ledger_hash,
        "planned_rows": len(rows),
        "applied_rows": applied,
        "findings": findings,
        "reader_sha256": reader_sha,
        "reader_pointer_mutated": 0,
        "website_mutated": 0,
        "after_rows": after_rows,
    }
    execution_path = backup_root / "gate4_acceptance_execution_manifest.json"
    write_json(execution_path, execution)
    (backup_root / "GATE4_ACCEPTANCE_EXECUTION_RECORD.md").write_text(
        "# Gate 4 Acceptance Execution Record\n\n"
        f"- Plan: `{plan_run}`\n- Apply run: `{token}`\n- Status: `{status}`\n"
        f"- Applied rows: `{applied}`\n- Findings: `{len(findings)}`\n"
        f"- Reader SHA-256: `{reader_sha}`\n- Reader pointer mutated: `0`\n- Website mutated: `0`\n",
        encoding="utf-8",
    )
    if logger:
        logger.artifact("gate4_acceptance_execution", execution_path, "Authorized 183-target Gate 4 apply result.")
        logger.artifact("gate4_acceptance_before_manifest", backup_root / "before_manifest.json", "Byte-preserved pre-apply state.")
        logger.artifact("gate4_acceptance_rollback", rollback_path, "Guarded Python 3.12 rollback command.")
        logger.boundary("reader_pointer_mutated", 0, "PASS", "Pointer file is outside the allow-list.")
        logger.boundary("help_meta_mutated", 0, "PASS", "HELP/META are outside the allow-list.")
        logger.boundary("product_source_mutated", 0, "PASS", "Product source is outside the allow-list.")
        logger.boundary("website_mutated", 0, "PASS", "Website publication remains a later gate.")
    return {
        "status": status,
        "backup_root": relpath_posix(backup_root, paths.repo_root),
        "execution_manifest": relpath_posix(execution_path, paths.repo_root),
        "findings": findings,
    }, {"applied_rows": applied, "validation_findings": len(findings), "rollback_findings": len(rollback_findings)}
