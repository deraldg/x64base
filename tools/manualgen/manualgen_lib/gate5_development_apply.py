from __future__ import annotations

import csv
import hashlib
import json
import os
import shutil
import sys
from pathlib import Path
from typing import Any

from .gate5_source_gap import PROMOTE_ADDITIONS
from .runlog import RunLogger, utc_now_iso
from .util import relpath_posix, sha256_file, write_json


PUBLICATION = "docs/manuals/developer/manualgen/published/developer_manual_publication_v1"
PAGE_PREFIX = f"{PUBLICATION}/command_reference_v1/commands/"
INDEX = f"{PUBLICATION}/command_reference_v1/README.md"
NAVIGATION = f"{PUBLICATION}/sections/sections/navigation_browsing_and_search.md"
READER = f"{PUBLICATION}/developer_manual_publication_v1.md"
PRIMARY_RECORD = "docs/manuals/developer/manualgen/accepted_artifacts/primary_reader_artifact_v1.json"
CANONICAL_RECORD = "docs/manuals/developer/manualgen/accepted_manifests/developer_manual_canonical_manifest_v1.json"
COMMAND_RECORD = "docs/manuals/developer/manualgen/accepted_artifacts/command_reference_artifact_v1.json"
FINALIZED_RECORDS = {PRIMARY_RECORD, CANONICAL_RECORD, COMMAND_RECORD}
EXPECTED_PAGE_NAMES = {
    "area.md",
    "bottom.md",
    "browse.md",
    "browser.md",
    "continue.md",
    "ersatz.md",
    "find.md",
    "go.md",
    "goto.md",
    "list.md",
    "locate.md",
    "schemas.md",
    "seek.md",
    "select.md",
    "skip.md",
    "smartlist.md",
    "top.md",
    "use.md",
    "workspace.md",
}
EXPECTED_OTHER_TARGETS = {
    INDEX,
    NAVIGATION,
    "PROMOTE.manifest",
    PRIMARY_RECORD,
    CANONICAL_RECORD,
    COMMAND_RECORD,
}


def _repo_file(repo_root: Path, value: str) -> Path:
    raw = Path(value)
    resolved = (raw if raw.is_absolute() else repo_root / raw).resolve()
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
    temporary = path.parent / f".{path.name}.{token}.tmp"
    if temporary.exists():
        temporary.unlink()
    temporary.write_bytes(value)
    os.replace(temporary, path)


def validate_gate5_authorization(
    payload: dict[str, Any], plan_run: str, manifest_hash: str, ledger_hash: str
) -> list[str]:
    findings: list[str] = []
    expected = {
        "schema": "dottalk.manualgen.gate5_development_apply_authorization.v1",
        "decision": "AUTHORIZED_FOR_DEVELOPMENT_DOCUMENTATION_APPLY",
        "plan_run": plan_run,
        "plan_manifest_sha256": manifest_hash,
        "mutation_ledger_sha256": ledger_hash,
        "mutation_rows_authorized": 25,
        "create_rows_authorized": 19,
        "replace_rows_authorized": 6,
        "required_interpreter": "Python 3.12",
    }
    for key, expected_value in expected.items():
        if payload.get(key) != expected_value:
            findings.append(f"AUTHORIZATION:{key}:{payload.get(key)}")
    if set(payload.get("apply_time_finalization_targets", [])) != FINALIZED_RECORDS:
        findings.append("AUTHORIZATION:apply_time_finalization_targets")
    scope = payload.get("scope", {})
    if scope.get("development_documentation_apply") != "AUTHORIZED":
        findings.append("AUTHORIZATION:development_documentation_apply")
    for boundary in ("source_staging_mutation", "git_index_commit_push", "website_mutation"):
        if scope.get(boundary) != "NOT_AUTHORIZED":
            findings.append(f"AUTHORIZATION:{boundary}")
    return findings


def finalize_gate5_record(
    target: str,
    planned: bytes,
    plan_run: str,
    apply_run: str,
    authorization_record: str,
    accepted_utc: str,
) -> bytes:
    if target not in FINALIZED_RECORDS:
        return planned
    payload = json.loads(planned.decode("utf-8-sig"))
    if payload.get("status") != "GATE5_SUPPLEMENTAL_SOURCE_PLAN_PENDING_APPLY":
        raise ValueError(f"unexpected planned Gate 5 status for {target}: {payload.get('status')}")
    payload["gate5_plan_run"] = plan_run
    payload["gate5_apply_run"] = apply_run
    payload["gate5_acceptance_authorization_record"] = authorization_record
    payload["gate5_accepted_utc"] = accepted_utc
    if target == PRIMARY_RECORD:
        payload["status"] = "PRIMARY_READER_AND_183_PAGE_COMMAND_REFERENCE_ACCEPTED_POINTER_UNCHANGED"
    elif target == CANONICAL_RECORD:
        payload["status"] = "GATE5_SUPPLEMENTAL_SOURCE_AND_PROMOTION_MANIFEST_ACCEPTED"
    else:
        payload["status"] = "ACCEPTED_COMMAND_REFERENCE_183_PAGES"
    return _json_bytes(payload)


def _validate_target_set(rows: list[dict[str, str]]) -> list[str]:
    findings: list[str] = []
    targets = [row.get("target", "") for row in rows]
    if len(rows) != 25 or len(set(targets)) != 25:
        findings.append(f"LEDGER_ROWS_OR_UNIQUENESS:{len(rows)}:{len(set(targets))}")
    pages = {Path(target).name for target in targets if target.startswith(PAGE_PREFIX)}
    others = {target for target in targets if not target.startswith(PAGE_PREFIX)}
    if pages != EXPECTED_PAGE_NAMES:
        findings.append(f"COMMAND_PAGE_SET:{len(pages)}")
    if others != EXPECTED_OTHER_TARGETS:
        findings.append(f"OTHER_TARGET_SET:{len(others)}")
    creates = sum(row.get("operation") == "CREATE" for row in rows)
    replaces = sum(row.get("operation") == "REPLACE" for row in rows)
    if (creates, replaces) != (19, 6):
        findings.append(f"OPERATION_COUNTS:{creates}:{replaces}")
    return findings


def _priority(target: str) -> tuple[int, str]:
    if target.startswith(PAGE_PREFIX):
        return 0, target
    if target in {INDEX, NAVIGATION, "PROMOTE.manifest"}:
        return 1, target
    return 2, target


def _rollback(
    repo_root: Path, before_root: Path, rows: list[dict[str, Any]], token: str
) -> list[str]:
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


def _write_rollback_script(
    path: Path,
    repo_root: Path,
    before_rows: list[dict[str, Any]],
    after_rows: list[dict[str, Any]],
    plan_run: str,
) -> None:
    before_json = json.dumps(before_rows, separators=(",", ":"))
    after_json = json.dumps(after_rows, separators=(",", ":"))
    script = f'''#!/usr/bin/env python3
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path

PLAN_RUN = {plan_run!r}
REPO_ROOT = Path({str(repo_root)!r})
BACKUP_ROOT = Path(__file__).resolve().parent / "before"
BEFORE_ROWS = json.loads({before_json!r})
AFTER_ROWS = json.loads({after_json!r})

def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()

parser = argparse.ArgumentParser(description="Rollback one authorized Gate 5 development documentation apply.")
parser.add_argument("--confirm", required=True)
args = parser.parse_args()
if args.confirm != PLAN_RUN:
    raise SystemExit("Refusing rollback: --confirm must equal the Gate 5 plan run")

after_by_target = {{row["target"]: row for row in AFTER_ROWS}}
drift = []
for row in BEFORE_ROWS:
    target = REPO_ROOT / row["target"]
    expected = after_by_target[row["target"]]["after_sha256"]
    observed = sha256_file(target) if target.is_file() else "ABSENT"
    if observed != expected:
        drift.append(f"{{row['target']}}: expected {{expected}}, observed {{observed}}")
if drift:
    raise SystemExit("Refusing rollback because applied targets drifted:\n" + "\n".join(drift))

for row in reversed(BEFORE_ROWS):
    target = REPO_ROOT / row["target"]
    if row["before_exists"]:
        source = BACKUP_ROOT / row["target"]
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.parent / ("." + target.name + ".gate5-rollback.tmp")
        temporary.write_bytes(source.read_bytes())
        os.replace(temporary, target)
    elif target.is_file():
        target.unlink()
print("Gate 5 development rollback complete", PLAN_RUN)
'''
    path.write_text(script, encoding="utf-8")


def apply_gate5_development_plan(
    paths,
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
        / "manualgen_gate5_development_plans"
        / plan_run
    )
    manifest_path = plan_dir / "gate5_development_plan_manifest.json"
    ledger_path = plan_dir / "gate5_planned_mutations.csv"
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
    rows = _read_csv(ledger_path)
    manifest_hash = sha256_file(manifest_path)
    ledger_hash = sha256_file(ledger_path)
    if manifest.get("schema") != "dottalk.manualgen.gate5_development_plan.v1":
        findings.append("PLAN_SCHEMA")
    if manifest.get("run_id") != plan_run or manifest.get("status") != "PASS_PLAN_ONLY":
        findings.append("PLAN_STATUS_OR_RUN")
    if manifest.get("plan_only") != 1 or manifest.get("apply_available") != 0:
        findings.append("PLAN_BOUNDARY")
    expected_counts = {
        "planned_mutation_rows": 25,
        "planned_create_rows": 19,
        "planned_replace_rows": 6,
        "supplemental_pages": 19,
        "accepted_index_links": 183,
        "unresolved_index_links": 0,
        "navigation_status_files": 1,
        "acceptance_records": 3,
        "promote_manifest_additions": 20,
        "held_appendix_statuses": 3,
        "findings": 0,
    }
    for key, expected in expected_counts.items():
        observed = manifest.get("counts", {}).get(key)
        if observed != expected:
            findings.append(f"PLAN_COUNT:{key}:{observed}")
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
    findings.extend(
        validate_gate5_authorization(authorization, plan_run, manifest_hash, ledger_hash)
    )

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
        before_rows.append(
            {
                "target": target_rel,
                "before_exists": int(observed_exists),
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
    token = logger.run_id if logger else plan_run
    authorization_rel = relpath_posix(authorization_path, paths.repo_root)
    after_bytes = {
        row["target"]: finalize_gate5_record(
            row["target"],
            planned_bytes[row["target"]],
            plan_run,
            token,
            authorization_rel,
            accepted_utc,
        )
        for row in rows
    }

    reader = paths.repo_root / READER
    expected_reader_hash = manifest.get("bindings", {}).get("accepted_reader_sha256", "")
    if not reader.is_file() or sha256_file(reader) != expected_reader_hash:
        findings.append("ACCEPTED_READER_DRIFT")
    index_text = after_bytes[INDEX].decode("utf-8-sig")
    if index_text.count("](commands/") != 183:
        findings.append("FINAL_INDEX_LINK_COUNT")
    if "Status: REVIEWED_FOR_PUBLICATION" not in after_bytes[NAVIGATION].decode("utf-8-sig"):
        findings.append("FINAL_NAVIGATION_STATUS")
    manifest_lines = after_bytes["PROMOTE.manifest"].decode("utf-8-sig").splitlines()
    if any(manifest_lines.count(entry) != 1 for entry in PROMOTE_ADDITIONS):
        findings.append("FINAL_PROMOTE_MANIFEST_ENTRIES")
    command_record = json.loads(after_bytes[COMMAND_RECORD].decode("utf-8-sig"))
    if command_record.get("page_count") != 183 or command_record.get("lineage_rows") != 3974:
        findings.append("FINAL_COMMAND_RECORD_COUNTS")
    if findings:
        return {"status": "FAIL_STAGING", "findings": findings}, {
            "applied_rows": 0,
            "validation_findings": len(findings),
            "rollback_findings": 0,
        }

    backup_root = (
        paths.manualgen_root / "backups" / f"docflush_gate5_development_{token}"
    )
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
        after_rows.append(
            {
                "target": target_rel,
                "after_sha256": sha256_file(staged),
                "after_size": len(value),
            }
        )
    after_rows.sort(key=lambda row: row["target"])
    write_json(
        backup_root / "staged_after_manifest.json",
        {"plan_run": plan_run, "accepted_utc": accepted_utc, "rows": after_rows},
    )
    rollback_path = backup_root / "rollback_gate5_development.py"
    _write_rollback_script(rollback_path, paths.repo_root, before_rows, after_rows, plan_run)
    (backup_root / "ROLLBACK_COMMAND.md").write_text(
        "# Gate 5 development rollback command\n\n```powershell\n"
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
        if sha256_file(reader) != expected_reader_hash:
            raise OSError("accepted reader changed during Gate 5 apply")
    except Exception as exc:  # noqa: BLE001 - partial apply must always roll back
        findings.append(f"APPLY:{exc}")
        rollback_findings = _rollback(paths.repo_root, before_root, before_rows, token)
        findings.extend(rollback_findings)

    status = "PASS_APPLIED" if not findings else "FAIL_ROLLED_BACK"
    execution = {
        "schema": "dottalk.manualgen.gate5_development_execution.v1",
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
        "accepted_reader_sha256": sha256_file(reader),
        "source_staging_mutated": 0,
        "git_mutated": 0,
        "website_mutated": 0,
        "after_rows": after_rows,
    }
    execution_path = backup_root / "gate5_development_execution_manifest.json"
    write_json(execution_path, execution)
    (backup_root / "GATE5_DEVELOPMENT_EXECUTION_RECORD.md").write_text(
        "# Gate 5 Development Execution Record\n\n"
        f"- Plan: `{plan_run}`\n- Apply run: `{token}`\n- Status: `{status}`\n"
        f"- Applied rows: `{applied}`\n- Findings: `{len(findings)}`\n"
        f"- Accepted reader SHA-256: `{sha256_file(reader)}`\n"
        "- Source staging mutated: `0`\n- Git mutated: `0`\n- Website mutated: `0`\n",
        encoding="utf-8",
    )
    if logger:
        logger.artifact("gate5_development_execution", execution_path, "Authorized 25-target Gate 5 development apply result.")
        logger.artifact("gate5_development_before_manifest", backup_root / "before_manifest.json", "Byte-preserved pre-apply state.")
        logger.artifact("gate5_development_rollback", rollback_path, "After-hash-guarded Python 3.12 rollback command.")
        logger.boundary("accepted_reader_mutated", 0, "PASS", "The reader is outside the allow-list and its hash was rechecked.")
        logger.boundary("help_meta_mutated", 0, "PASS", "HELP and metadata are outside the allow-list.")
        logger.boundary("product_source_mutated", 0, "PASS", "Runtime product source is outside the allow-list.")
        logger.boundary("source_staging_mutated", 0, "PASS", "C:\\x64base remains a later gate.")
        logger.boundary("website_mutated", 0, "PASS", "Website publication remains a later gate.")
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
