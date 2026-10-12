#!/usr/bin/env python3
"""Execute the owner-approved AIF136-M5B-001 exact reclaim.

The executor validates the approved manifest and restore proof, remeasures the
full protected population, moves exactly two approved MDB files into an owned
quarantine, validates the preserved empty directory, then unlinks only those
quarantined payloads. Any failure before final unlink rolls the files back.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MANIFEST = REPO_ROOT / "labtalk/registries/aif136_m5b_reclaim_manifest_v1.json"
DEFAULT_WORKSPACE = REPO_ROOT / "tmp/aif136_m5b_reclaim/CODEX-20260915-AIF136-M5B-RECLAIM-001"
DEFAULT_PROOF_JSON = REPO_ROOT / "labtalk/proofs/runs/20260915_aif136_m5b_reclaim.json"
EXPECTED_FILES = {"data.mdb", "lock.mdb"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def file_state(path: Path, *, display_path: str | None = None) -> dict[str, Any]:
    return {
        "path": display_path if display_path is not None else path.as_posix(),
        "size_bytes": path.stat().st_size,
        "sha256": sha256(path),
    }


def checked_repo_path(relative: str) -> Path:
    path = (REPO_ROOT / relative).resolve()
    try:
        path.relative_to(REPO_ROOT.resolve())
    except ValueError as exc:
        raise RuntimeError(f"path escapes repository: {relative}") from exc
    return path


def load_and_validate_manifest(path: Path) -> dict[str, Any]:
    manifest = json.loads(path.read_text(encoding="utf-8"))
    required = {
        "schema": "dottalk.portal.m5b-reclaim-manifest.v1",
        "manifest_id": "AIF136-M5B-001",
        "lane_id": "AIF-136",
        "phase": "M5-B",
        "ruling_state": "approved",
        "operation": "exact_mdb_payload_reclaim",
        "m5b_action_authorized": True,
        "directory_must_persist": True,
        "expected_reclaim_logical_bytes": 16384,
    }
    for field, expected in required.items():
        if manifest.get(field) != expected:
            raise RuntimeError(f"manifest {field} must be {expected!r}")
    ruling = manifest.get("owner_ruling", {})
    if ruling.get("owner") != "member.derald" or ruling.get("decision") != "approved":
        raise RuntimeError("manifest lacks explicit owner approval")
    if not ruling.get("decided_at_utc") or ruling.get("response") != "go":
        raise RuntimeError("owner approval record is incomplete")
    execution = manifest.get("execution", {})
    if execution.get("run_id") != "CODEX-20260915-AIF136-M5B-RECLAIM-001":
        raise RuntimeError("execution run ID is not the approved run")
    if execution.get("status") not in {"pending", "PASS"}:
        raise RuntimeError("execution state must be pending or PASS")
    drill = manifest.get("restore_drill", {})
    if drill.get("status") != "PASS" or drill.get("physical_reclaim_authorized") is not False:
        raise RuntimeError("restore drill proof boundary is not satisfied")
    reconstruction = manifest.get("reconstruction", {})
    if reconstruction.get("direct_timestamped_directory_restore_proven") is not True:
        raise RuntimeError("timestamped-directory restore is not proven")
    rows = manifest.get("delete_files", [])
    if len(rows) != 2 or {Path(row.get("path", "")).name for row in rows} != EXPECTED_FILES:
        raise RuntimeError("delete scope must be exactly data.mdb and lock.mdb")
    if sum(row["size_bytes"] for row in rows) != manifest["expected_reclaim_logical_bytes"]:
        raise RuntimeError("delete-file sizes do not match expected reclaim")
    return manifest


def validate_exact_file(path: Path, row: dict[str, Any], label: str) -> None:
    if not path.is_file():
        raise RuntimeError(f"{label} is missing: {row['path']}")
    if path.stat().st_size != row["size_bytes"] or sha256(path) != row["sha256"]:
        raise RuntimeError(f"{label} does not match manifest: {row['path']}")


def load_protected_rows(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    protection_path = checked_repo_path(manifest["protected_population_manifest"])
    protection = json.loads(protection_path.read_text(encoding="utf-8"))
    rows = protection.get("protected_files", [])
    if not rows:
        raise RuntimeError("protected population manifest has no protected files")
    return rows


def protected_snapshot(rows: list[dict[str, Any]], *, exclude: set[str] | None = None) -> dict[str, dict[str, Any]]:
    excluded = exclude or set()
    snapshot: dict[str, dict[str, Any]] = {}
    for row in rows:
        relative = row["path"]
        if relative in excluded:
            continue
        path = checked_repo_path(relative)
        validate_exact_file(path, row, "protected file")
        snapshot[relative] = file_state(path, display_path=relative)
    return snapshot


def validate_restore_proof(manifest: dict[str, Any]) -> dict[str, Any]:
    path = checked_repo_path(manifest["restore_drill"]["proof_json"])
    proof = json.loads(path.read_text(encoding="utf-8"))
    required = {
        "schema": "dottalk.portal.m5b-restore-drill-proof.v1",
        "manifest_id": manifest["manifest_id"],
        "status": "PASS",
        "physical_reclaim_authorized": False,
        "protected_unchanged": True,
        "restored_files_match_standard_environment": True,
        "restored_directory_matched_candidate_leaf": True,
        "restored_tag_count": manifest["expected_container_tag_count"],
        "restored_record_count_per_tag": manifest["expected_record_count"],
        "expected_ordered_keys_verified": True,
        "workspace_removed_after_success": True,
    }
    for field, expected in required.items():
        if proof.get(field) != expected:
            raise RuntimeError(f"restore proof {field} must be {expected!r}")
    transcript = checked_repo_path(manifest["restore_drill"]["transcript"])
    if not transcript.is_file() or sha256(transcript) != proof["transcript"]["sha256"]:
        raise RuntimeError("restore proof transcript hash mismatch")
    return proof


def validate_candidate_before(manifest: dict[str, Any]) -> Path:
    target = checked_repo_path(manifest["target_directory"])
    if not target.is_dir():
        raise RuntimeError("target directory is missing")
    names = {path.name for path in target.iterdir()}
    if names != set(manifest["expected_pre_delete_directory_entries"]):
        raise RuntimeError("target directory contents changed from approved manifest")
    for row in manifest["delete_files"]:
        path = checked_repo_path(row["path"])
        if path.parent != target:
            raise RuntimeError("delete path is not a direct child of target directory")
        validate_exact_file(path, row, "approved reclaim file")
    for row in manifest["retain_files"]:
        validate_exact_file(checked_repo_path(row["path"]), row, "retained reconstruction input")
    return target


def rollback_moves(moved: list[tuple[Path, Path]]) -> None:
    errors: list[str] = []
    for source, destination in reversed(moved):
        try:
            if destination.exists() and not source.exists():
                destination.replace(source)
        except OSError as exc:
            errors.append(f"{destination} -> {source}: {exc}")
    if errors:
        raise RuntimeError("rollback failed: " + "; ".join(errors))


def finalize_quarantine(workspace: Path, payload: Path, run_id: str) -> None:
    allowed_root = (REPO_ROOT / "tmp/aif136_m5b_reclaim").resolve()
    try:
        workspace.relative_to(allowed_root)
    except ValueError as exc:
        raise RuntimeError("refusing to finalize quarantine outside allowed root") from exc
    marker = workspace / ".aif136_m5b_owned.json"
    if json.loads(marker.read_text(encoding="ascii")) != {"run_id": run_id}:
        raise RuntimeError("refusing to finalize quarantine with foreign marker")
    names = {path.name for path in payload.iterdir()}
    if names != EXPECTED_FILES:
        raise RuntimeError("refusing to finalize quarantine with unexpected contents")
    for name in sorted(EXPECTED_FILES):
        (payload / name).unlink()
    payload.rmdir()
    marker.unlink()
    workspace.rmdir()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--workspace", type=Path, default=DEFAULT_WORKSPACE)
    parser.add_argument("--proof-json", type=Path, default=DEFAULT_PROOF_JSON)
    args = parser.parse_args(argv)

    manifest = load_and_validate_manifest(args.manifest)
    run_id = manifest["execution"]["run_id"]
    if manifest["execution"]["status"] != "pending":
        raise RuntimeError("execution is not in pending state")
    workspace = args.workspace.resolve()
    allowed_root = (REPO_ROOT / "tmp/aif136_m5b_reclaim").resolve()
    try:
        workspace.relative_to(allowed_root)
    except ValueError as exc:
        raise RuntimeError(f"workspace must remain under {allowed_root}") from exc
    if workspace.exists():
        raise RuntimeError(f"refusing to reuse existing workspace: {workspace}")

    restore_proof = validate_restore_proof(manifest)
    target = validate_candidate_before(manifest)
    protected_rows = load_protected_rows(manifest)
    before_all = protected_snapshot(protected_rows)
    delete_paths = {row["path"] for row in manifest["delete_files"]}
    before_retained = {key: value for key, value in before_all.items() if key not in delete_paths}

    payload = workspace / "payload"
    payload.mkdir(parents=True, exist_ok=False)
    (workspace / ".aif136_m5b_owned.json").write_text(
        json.dumps({"run_id": run_id}, sort_keys=True) + "\n", encoding="ascii"
    )

    moved: list[tuple[Path, Path]] = []
    quarantine_states: dict[str, dict[str, Any]] = {}
    try:
        for row in manifest["delete_files"]:
            source = checked_repo_path(row["path"])
            destination = payload / source.name
            source.replace(destination)
            moved.append((source, destination))
            validate_exact_file(destination, row, "quarantined reclaim file")
            quarantine_states[source.name] = file_state(destination, display_path=row["path"])

        if not target.is_dir() or any(target.iterdir()):
            raise RuntimeError("target directory was not preserved empty after quarantine")
        after_retained = protected_snapshot(protected_rows, exclude=delete_paths)
        if before_retained != after_retained:
            raise RuntimeError("a protected retained file changed during quarantine")
        for row in manifest["retain_files"]:
            validate_exact_file(checked_repo_path(row["path"]), row, "retained reconstruction input")
    except Exception:
        rollback_moves(moved)
        raise

    finalize_quarantine(workspace, payload, run_id)
    if workspace.exists():
        raise RuntimeError("owned quarantine workspace survived finalization")
    if not target.is_dir() or any(target.iterdir()):
        raise RuntimeError("target directory was not preserved empty after finalization")
    for relative in delete_paths:
        if checked_repo_path(relative).exists():
            raise RuntimeError(f"approved reclaim file still exists: {relative}")
    after_retained = protected_snapshot(protected_rows, exclude=delete_paths)
    if before_retained != after_retained:
        raise RuntimeError("a protected retained file changed after finalization")

    args.proof_json.parent.mkdir(parents=True, exist_ok=True)
    proof = {
        "schema": "dottalk.portal.m5b-reclaim-execution-proof.v1",
        "manifest_id": manifest["manifest_id"],
        "run_id": run_id,
        "created_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "status": "PASS",
        "owner_ruling": manifest["owner_ruling"],
        "restore_proof": {
            "path": manifest["restore_drill"]["proof_json"],
            "status": restore_proof["status"],
            "protected_unchanged": restore_proof["protected_unchanged"],
        },
        "target_directory": manifest["target_directory"],
        "target_directory_present": target.is_dir(),
        "target_directory_entries_after": [],
        "removed_files": manifest["delete_files"],
        "removed_file_count": len(manifest["delete_files"]),
        "reclaimed_logical_bytes": sum(row["size_bytes"] for row in manifest["delete_files"]),
        "quarantine_verified_before_final_unlink": quarantine_states,
        "quarantine_workspace_removed": not workspace.exists(),
        "protected_retained_before": before_retained,
        "protected_retained_after": after_retained,
        "protected_retained_unchanged": before_retained == after_retained,
        "retained_dbf_cdx_unchanged": all(
            before_retained[row["path"]] == after_retained[row["path"]]
            for row in manifest["retain_files"]
        ),
        "other_lmdb_environments_changed": 0,
        "rollback": manifest["reconstruction"]["rollback_after_delete"],
    }
    args.proof_json.write_text(json.dumps(proof, indent=2, sort_keys=True) + "\n", encoding="ascii")
    print(f"AIF-136 M5-B reclaim: PASS -- proof {args.proof_json}")
    print(f"removed files: {proof['removed_file_count']}; reclaimed logical bytes: {proof['reclaimed_logical_bytes']}")
    print("target directory preserved empty; retained DBF/CDX and other LMDB environments unchanged")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, ValueError, json.JSONDecodeError) as exc:
        print(f"AIF-136 M5-B reclaim: FAIL -- {exc}", file=sys.stderr)
        raise SystemExit(2)
