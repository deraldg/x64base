#!/usr/bin/env python3
"""Run the owner-approved AIF-136 M5-B isolated restore drill.

The runner rebuilds from isolated DBF/CDX copies, copies only its generated
MDB files into a new timestamp-suffixed test directory, and opens that restored
directory read-only with LMDBDUMP. It never opens the real reclaim candidate
for write and it never authorizes physical reclaim.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MANIFEST = REPO_ROOT / "labtalk/registries/aif136_m5b_reclaim_manifest_v1.json"
DEFAULT_WORKSPACE = REPO_ROOT / "tmp/aif136_m5b_restore/CODEX-20260915-AIF136-M5B-RESTORE-001"
DEFAULT_PROOF_JSON = REPO_ROOT / "labtalk/proofs/runs/20260915_aif136_m5b_restore_drill.json"
DEFAULT_TRANSCRIPT = REPO_ROOT / "labtalk/proofs/runs/20260915_aif136_m5b_restore_drill.txt"
EXPECTED_ENV_FILES = {"data.mdb", "lock.mdb"}


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


def ascii_text(text: str) -> str:
    normalized = "\n".join(line.rstrip(" \t") for line in text.splitlines()) + "\n"
    return normalized.encode("ascii", errors="backslashreplace").decode("ascii")


def load_and_validate_manifest(path: Path) -> dict[str, Any]:
    manifest = json.loads(path.read_text(encoding="utf-8"))
    required = {
        "schema": "dottalk.portal.m5b-reclaim-manifest.v1",
        "manifest_id": "AIF136-M5B-001",
        "lane_id": "AIF-136",
        "phase": "M5-B",
        "operation": "exact_mdb_payload_reclaim",
        "directory_must_persist": True,
        "expected_record_count": 10,
        "expected_container_tag_count": 3,
        "generated_tag": "CATALOG_OBJECT_ID",
    }
    for field, expected in required.items():
        if manifest.get(field) != expected:
            raise RuntimeError(f"manifest {field} must be {expected!r}")
    if manifest.get("ruling_state") not in {"pending_owner_approval", "approved"}:
        raise RuntimeError("manifest ruling_state is not a recognized lifecycle state")
    if not isinstance(manifest.get("m5b_action_authorized"), bool):
        raise RuntimeError("manifest m5b_action_authorized must be boolean")
    drill = manifest.get("restore_drill", {})
    if drill.get("ruling_state") != "approved":
        raise RuntimeError("restore drill is not owner-approved")
    if drill.get("owner") != "member.derald" or not drill.get("decided_at_utc"):
        raise RuntimeError("restore drill approval is incomplete")
    if drill.get("physical_reclaim_authorized") is not False:
        raise RuntimeError("restore drill must not authorize physical reclaim")
    if len(manifest.get("delete_files", [])) != 2:
        raise RuntimeError("manifest must name exactly two reclaim candidate files")
    if {row.get("path", "").rsplit("/", 1)[-1] for row in manifest["delete_files"]} != EXPECTED_ENV_FILES:
        raise RuntimeError("manifest reclaim candidates must be exactly data.mdb and lock.mdb")
    tags = manifest.get("expected_container_tags", [])
    if len(tags) != manifest["expected_container_tag_count"]:
        raise RuntimeError("expected tag count does not match expected tags")
    if manifest["generated_tag"] not in tags:
        raise RuntimeError("generated tag is absent from expected tags")
    if len(manifest.get("expected_ordered_keys", [])) != manifest["expected_record_count"]:
        raise RuntimeError("expected key count does not match expected record count")
    return manifest


def checked_repo_path(relative: str) -> Path:
    path = (REPO_ROOT / relative).resolve()
    try:
        path.relative_to(REPO_ROOT.resolve())
    except ValueError as exc:
        raise RuntimeError(f"path escapes repository: {relative}") from exc
    return path


def validate_exact_file(path: Path, row: dict[str, Any], label: str) -> None:
    if not path.is_file():
        raise RuntimeError(f"{label} is missing: {row['path']}")
    if path.stat().st_size != row["size_bytes"] or sha256(path) != row["sha256"]:
        raise RuntimeError(f"{label} does not match manifest: {row['path']}")


def protected_snapshot(manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    protection_manifest = checked_repo_path(manifest["protected_population_manifest"])
    protection = json.loads(protection_manifest.read_text(encoding="utf-8"))
    rows = protection.get("protected_files", [])
    if not rows:
        raise RuntimeError("protected population manifest has no protected files")
    snapshot: dict[str, dict[str, Any]] = {}
    for row in rows:
        path = checked_repo_path(row["path"])
        validate_exact_file(path, row, "protected file")
        snapshot[row["path"]] = file_state(path, display_path=row["path"])
    return snapshot


def validate_candidate_boundary(manifest: dict[str, Any]) -> None:
    target = checked_repo_path(manifest["target_directory"])
    if not target.is_dir():
        raise RuntimeError("real candidate directory is missing")
    entries = {path.name for path in target.iterdir()}
    if entries != set(manifest["expected_pre_delete_directory_entries"]):
        raise RuntimeError("real candidate directory contents changed from the manifest")
    for row in manifest["delete_files"]:
        validate_exact_file(checked_repo_path(row["path"]), row, "candidate file")
    for row in manifest["retain_files"]:
        validate_exact_file(checked_repo_path(row["path"]), row, "retained file")


def build_commands(
    *, dbf_dir: Path, index_dir: Path, lmdb_root: Path, cdx_path: Path, capture_path: Path,
    table: str, tag: str,
) -> list[str]:
    return [
        f"SET ALTERNATE TO {capture_path}",
        "SET ALTERNATE ON",
        "ABOUT",
        f"SETPATH DBF {dbf_dir}",
        f"SETPATH INDEXES {index_dir}",
        f"SETPATH LMDB {lmdb_root}",
        "CLOSE ALL",
        f"USE {table}",
        "AREA",
        "STRUCT",
        "COUNT",
        f"SET INDEX TO {cdx_path}",
        f"CDX INFO {cdx_path}",
        "BUILDLMDB CLEAN YES",
        f"SET ORDER TO {tag}",
        "LIST ALL",
        "CLOSE ALL",
        "SET ALTERNATE OFF",
        "QUIT",
    ]


def dump_commands(*, restored_dir: Path, capture_path: Path, tags: list[str]) -> list[str]:
    commands = [
        f"SET ALTERNATE TO {capture_path}",
        "SET ALTERNATE ON",
        "ABOUT",
        f"LMDBDUMP {restored_dir} --trydb --limit 0",
    ]
    commands.extend(f"LMDBDUMP {restored_dir} --db {tag} --limit 20" for tag in tags)
    commands.extend(("SET ALTERNATE OFF", "QUIT"))
    return commands


def run_script(executable: Path, script_path: Path, commands: list[str]) -> subprocess.CompletedProcess[str]:
    script_path.write_text("\n".join(commands) + "\n", encoding="ascii")
    return subprocess.run(
        [str(executable), "--script", str(script_path)],
        cwd=REPO_ROOT / "dottalkpp/data",
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=180,
        check=False,
    )


def combined_capture(capture_path: Path, process: subprocess.CompletedProcess[str]) -> str:
    routed = capture_path.read_text(encoding="utf-8", errors="replace") if capture_path.is_file() else ""
    return ascii_text(
        "--- routed capture ---\n" + routed
        + "--- process stdout ---\n" + process.stdout
        + "--- process stderr ---\n" + process.stderr
    )


def validate_build_capture(text: str, manifest: dict[str, Any]) -> list[str]:
    findings: list[str] = []
    required = (
        f"Opened {manifest['source_table']} (v64) : Record count {manifest['expected_record_count']}",
        f"Tags     : {manifest['expected_container_tag_count']}",
        f"BUILDLMDB: done OK={manifest['expected_container_tag_count']} tags rebuilt.",
        f"SET ORDER: CDX TAG '{manifest['generated_tag']}'",
        f"{manifest['expected_record_count']} cdx(lmdb) indexed record(s)",
    )
    upper = text.upper()
    for token in required:
        if token.upper() not in upper:
            findings.append(f"build capture missing: {token}")
    positions = [text.find(key) for key in manifest["expected_ordered_keys"]]
    if any(position < 0 for position in positions):
        findings.append("build capture does not contain every expected key")
    elif positions != sorted(positions):
        findings.append("build capture keys are not in expected order")
    return findings


def validate_dump_capture(text: str, manifest: dict[str, Any]) -> list[str]:
    findings: list[str] = []
    for tag in manifest["expected_container_tags"]:
        token = f"DB '{tag}' exists (entries={manifest['expected_record_count']})"
        if token.upper() not in text.upper():
            findings.append(f"restored dump missing tag evidence: {token}")
    scanned = f"Scanned: {manifest['expected_record_count']} record(s)"
    if text.upper().count(scanned.upper()) < manifest["expected_container_tag_count"]:
        findings.append("restored dump did not scan the expected record count for every tag")
    positions = [text.find(key) for key in manifest["expected_ordered_keys"]]
    if any(position < 0 for position in positions):
        findings.append("restored dump does not contain every expected ordered key")
    elif positions != sorted(positions):
        findings.append("restored dump keys are not in expected order")
    return findings


def remove_owned_workspace(workspace: Path, allowed_root: Path, run_id: str) -> None:
    try:
        workspace.relative_to(allowed_root)
    except ValueError as exc:
        raise RuntimeError("refusing to clean workspace outside the allowed root") from exc
    marker = workspace / ".aif136_m5b_owned.json"
    if not marker.is_file():
        raise RuntimeError("refusing to clean workspace without ownership marker")
    marker_data = json.loads(marker.read_text(encoding="ascii"))
    if marker_data != {"run_id": run_id}:
        raise RuntimeError("refusing to clean workspace with a foreign ownership marker")
    shutil.rmtree(workspace)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--workspace", type=Path, default=DEFAULT_WORKSPACE)
    parser.add_argument("--proof-json", type=Path, default=DEFAULT_PROOF_JSON)
    parser.add_argument("--transcript", type=Path, default=DEFAULT_TRANSCRIPT)
    parser.add_argument("--executable", type=Path, default=REPO_ROOT / "build/src/Release/dottalkpp.exe")
    parser.add_argument("--cleanup-on-success", action="store_true")
    args = parser.parse_args(argv)

    manifest = load_and_validate_manifest(args.manifest)
    if manifest["restore_drill"].get("status") == "PASS":
        raise RuntimeError("restore drill is already complete")
    run_id = manifest["restore_drill"]["run_id"]
    workspace = args.workspace.resolve()
    allowed_root = (REPO_ROOT / "tmp/aif136_m5b_restore").resolve()
    try:
        workspace.relative_to(allowed_root)
    except ValueError as exc:
        raise RuntimeError(f"workspace must remain under {allowed_root}") from exc
    if workspace.exists():
        raise RuntimeError(f"refusing to reuse existing workspace: {workspace}")
    if not args.executable.is_file():
        raise RuntimeError(f"DotTalk++ executable not found: {args.executable}")

    validate_candidate_boundary(manifest)
    before = protected_snapshot(manifest)
    source_dbf_row = next(row for row in manifest["retain_files"] if row["role"] == "authoritative_dbf_source")
    source_cdx_row = next(row for row in manifest["retain_files"] if row["role"] == "cdx_metadata_index_generator")
    source_dbf = checked_repo_path(source_dbf_row["path"])
    source_cdx = checked_repo_path(source_cdx_row["path"])

    dbf_dir = workspace / "dbf"
    index_dir = workspace / "indexes"
    lmdb_root = workspace / "lmdb_standard"
    standard_env = lmdb_root / f"{manifest['source_table']}.cdx.d"
    restored_root = workspace / "restored"
    restored_dir = restored_root / Path(manifest["target_directory"]).name
    for directory in (dbf_dir, index_dir, standard_env, restored_dir):
        directory.mkdir(parents=True, exist_ok=False)
    (workspace / ".aif136_m5b_owned.json").write_text(
        json.dumps({"run_id": run_id}, sort_keys=True) + "\n", encoding="ascii"
    )

    isolated_dbf = dbf_dir / source_dbf.name
    isolated_cdx = index_dir / source_cdx.name
    shutil.copy2(source_dbf, isolated_dbf)
    shutil.copy2(source_cdx, isolated_cdx)
    if sha256(isolated_dbf) != source_dbf_row["sha256"]:
        raise RuntimeError("isolated DBF copy hash mismatch")
    if sha256(isolated_cdx) != source_cdx_row["sha256"]:
        raise RuntimeError("isolated CDX copy hash mismatch")

    build_capture_path = workspace / "build_capture.txt"
    build_process = run_script(
        args.executable,
        workspace / "build.dts",
        build_commands(
            dbf_dir=dbf_dir,
            index_dir=index_dir,
            lmdb_root=lmdb_root,
            cdx_path=isolated_cdx,
            capture_path=build_capture_path,
            table=manifest["source_table"],
            tag=manifest["generated_tag"],
        ),
    )
    if build_process.returncode != 0:
        raise RuntimeError(f"build process exited {build_process.returncode}: {build_process.stderr}")
    build_text = combined_capture(build_capture_path, build_process)
    build_findings = validate_build_capture(build_text, manifest)
    if build_findings:
        raise RuntimeError("; ".join(build_findings))
    standard_files = {path.name: file_state(path) for path in standard_env.iterdir() if path.is_file()}
    if set(standard_files) != EXPECTED_ENV_FILES:
        raise RuntimeError("standard rebuild did not create exactly data.mdb and lock.mdb")

    for name in sorted(EXPECTED_ENV_FILES):
        shutil.copy2(standard_env / name, restored_dir / name)
    restored_files = {path.name: file_state(path) for path in restored_dir.iterdir() if path.is_file()}
    if set(restored_files) != EXPECTED_ENV_FILES:
        raise RuntimeError("restored directory does not contain exactly data.mdb and lock.mdb")
    for name in EXPECTED_ENV_FILES:
        if standard_files[name]["size_bytes"] != restored_files[name]["size_bytes"]:
            raise RuntimeError(f"restored {name} size mismatch")
        if standard_files[name]["sha256"] != restored_files[name]["sha256"]:
            raise RuntimeError(f"restored {name} hash mismatch")

    dump_capture_path = workspace / "restore_capture.txt"
    dump_process = run_script(
        args.executable,
        workspace / "restore_readback.dts",
        dump_commands(
            restored_dir=restored_dir,
            capture_path=dump_capture_path,
            tags=manifest["expected_container_tags"],
        ),
    )
    if dump_process.returncode != 0:
        raise RuntimeError(f"restore readback exited {dump_process.returncode}: {dump_process.stderr}")
    dump_text = combined_capture(dump_capture_path, dump_process)
    dump_findings = validate_dump_capture(dump_text, manifest)
    if dump_findings:
        raise RuntimeError("; ".join(dump_findings))

    validate_candidate_boundary(manifest)
    after = protected_snapshot(manifest)
    if before != after:
        raise RuntimeError("one or more protected files changed during the restore drill")

    args.transcript.parent.mkdir(parents=True, exist_ok=True)
    args.proof_json.parent.mkdir(parents=True, exist_ok=True)
    transcript = ascii_text(
        "AIF-136 M5-B RESTORE DRILL\n"
        "\n=== STANDARD BUILD ===\n" + build_text
        + "\n=== TIMESTAMPED DIRECTORY READBACK ===\n" + dump_text
    )
    args.transcript.write_text(transcript, encoding="ascii")
    transcript_state = file_state(args.transcript)
    executable_state = file_state(args.executable)

    workspace_removed = False
    if args.cleanup_on_success:
        remove_owned_workspace(workspace, allowed_root, run_id)
        workspace_removed = not workspace.exists()

    proof = {
        "schema": "dottalk.portal.m5b-restore-drill-proof.v1",
        "manifest_id": manifest["manifest_id"],
        "run_id": run_id,
        "created_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "status": "PASS",
        "operation": "isolated_timestamped_directory_restore_proof_only",
        "physical_reclaim_authorized": False,
        "candidate_files_removed": 0,
        "candidate_directories_removed": 0,
        "protected_before": before,
        "protected_after": after,
        "protected_unchanged": before == after,
        "executable": executable_state,
        "workspace": workspace.as_posix(),
        "workspace_removed_after_success": workspace_removed,
        "restored_directory_leaf": restored_dir.name,
        "restored_directory_matched_candidate_leaf": restored_dir.name == Path(manifest["target_directory"]).name,
        "standard_environment_files": standard_files,
        "restored_environment_files": restored_files,
        "restored_files_match_standard_environment": all(
            standard_files[name]["size_bytes"] == restored_files[name]["size_bytes"]
            and standard_files[name]["sha256"] == restored_files[name]["sha256"]
            for name in EXPECTED_ENV_FILES
        ),
        "restored_tag_count": manifest["expected_container_tag_count"],
        "restored_record_count_per_tag": manifest["expected_record_count"],
        "expected_ordered_keys_verified": True,
        "transcript": transcript_state,
        "m5b_action_authorized": False,
    }
    args.proof_json.write_text(json.dumps(proof, indent=2, sort_keys=True) + "\n", encoding="ascii")
    print(f"AIF-136 M5-B restore drill: PASS -- proof {args.proof_json}")
    print("candidate files removed: 0; candidate directories removed: 0")
    print("physical reclaim remains separately authorized")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, ValueError, json.JSONDecodeError) as exc:
        print(f"AIF-136 M5-B restore drill: FAIL -- {exc}", file=sys.stderr)
        raise SystemExit(2)
