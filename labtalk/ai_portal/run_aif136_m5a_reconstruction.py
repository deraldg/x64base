#!/usr/bin/env python3
"""Run the owner-approved AIF-136 M5-A isolated reconstruction proof.

This runner may remove only files it created inside its new tmp/aif136_m5a
workspace. Existing DBF, CDX, CNX, LMDB, archive, and directory paths are
hashed before and after and are never opened by DotTalk++.
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
DEFAULT_MANIFEST = REPO_ROOT / "labtalk/registries/aif136_m5a_reconstruction_manifest_v1.json"
DEFAULT_WORKSPACE = REPO_ROOT / "tmp/aif136_m5a/CODEX-20260915-AIF136-M5A-001"
DEFAULT_PROOF_JSON = REPO_ROOT / "labtalk/proofs/runs/20260915_aif136_m5a_protected_hashes.json"
DEFAULT_STAGE1_CAPTURE = REPO_ROOT / "labtalk/proofs/runs/20260915_aif136_m5a_reconstruction_stage1.txt"
DEFAULT_STAGE2_CAPTURE = REPO_ROOT / "labtalk/proofs/runs/20260915_aif136_m5a_reconstruction_stage2.txt"
EXPECTED_ENV_FILES = {"data.mdb", "lock.mdb"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def file_state(path: Path) -> dict[str, Any]:
    return {
        "path": path.as_posix(),
        "size_bytes": path.stat().st_size,
        "sha256": sha256(path),
    }


def normalize_capture(path: Path) -> str:
    """Remove console column padding while preserving every emitted line."""
    raw = path.read_text(encoding="utf-8", errors="replace")
    normalized = "\n".join(line.rstrip(" \t") for line in raw.splitlines()) + "\n"
    path.write_bytes(normalized.encode("ascii"))
    return normalized


def load_and_validate_manifest(path: Path) -> dict[str, Any]:
    manifest = json.loads(path.read_text(encoding="utf-8"))
    required = {
        "schema": "dottalk.portal.m5a-reconstruction-manifest.v1",
        "lane_id": "AIF-136",
        "phase": "M5-A",
        "ruling_state": "approved",
        "operation": "isolated_reconstruction_proof_only",
        "physical_action": "temporary_workspace_only",
        "container_kind": "CDX",
        "container_role": "metadata_index_generator",
        "container_must_persist": True,
        "expected_container_tag_count": 3,
        "mdb_files_reconstructible": True,
        "lmdb_environment_directory_must_persist": True,
        "m5b_action_authorized": False,
    }
    for field, expected in required.items():
        if manifest.get(field) != expected:
            raise RuntimeError(f"manifest {field} must be {expected!r}")
    ruling = manifest.get("owner_ruling", {})
    if ruling.get("owner") != "member.derald" or ruling.get("decision") != "approved":
        raise RuntimeError("manifest lacks the explicit member.derald approval")
    if not ruling.get("decided_at_utc"):
        raise RuntimeError("manifest approval lacks decided_at_utc")
    tags = manifest.get("expected_container_tags")
    if not isinstance(tags, list) or len(tags) != manifest["expected_container_tag_count"]:
        raise RuntimeError("manifest expected_container_tags does not match its count")
    if manifest["generated_tag"] not in tags:
        raise RuntimeError("generated_tag is absent from expected_container_tags")
    return manifest


def protected_snapshot(manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    snapshot: dict[str, dict[str, Any]] = {}
    for row in manifest["protected_files"]:
        rel = row["path"]
        path = (REPO_ROOT / rel).resolve()
        try:
            path.relative_to(REPO_ROOT.resolve())
        except ValueError as exc:
            raise RuntimeError(f"protected path escapes repository: {rel}") from exc
        if not path.is_file():
            raise RuntimeError(f"protected file is missing: {rel}")
        state = file_state(path)
        state["path"] = rel
        if state["size_bytes"] != row["size_bytes"] or state["sha256"] != row["sha256"]:
            raise RuntimeError(f"protected file does not match approved manifest: {rel}")
        snapshot[rel] = state
    return snapshot


def clear_isolated_env_files(env_dir: Path) -> None:
    if not env_dir.is_dir():
        raise RuntimeError("isolated LMDB environment directory does not exist")
    names = {path.name for path in env_dir.iterdir()}
    if names != EXPECTED_ENV_FILES:
        raise RuntimeError(
            "refusing to clear isolated environment with unexpected contents: "
            + ", ".join(sorted(names))
        )
    for name in sorted(EXPECTED_ENV_FILES):
        (env_dir / name).unlink()
    if not env_dir.is_dir() or any(env_dir.iterdir()):
        raise RuntimeError("isolated environment directory was not preserved empty")


def build_commands(
    *,
    stage: int,
    dbf_dir: Path,
    index_dir: Path,
    lmdb_root: Path,
    cdx_path: Path,
    capture_path: Path,
    table: str,
    tag: str,
) -> list[str]:
    commands = [
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
    ]
    commands.append(f"SET INDEX TO {cdx_path}")
    commands.extend(
        (
            f"CDX INFO {cdx_path}",
            "BUILDLMDB CLEAN YES",
            f"SET ORDER TO {tag}",
            "LIST ALL",
            "CLOSE ALL",
            "SET ALTERNATE OFF",
            "QUIT",
        )
    )
    return commands


def run_stage(executable: Path, script_path: Path, commands: list[str]) -> subprocess.CompletedProcess[str]:
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


def validate_capture(text: str, manifest: dict[str, Any], stage: int) -> list[str]:
    findings: list[str] = []
    required = (
        f"Opened {manifest['source_table']} (v64) : Record count {manifest['expected_record_count']}",
        f"Tags     : {manifest['expected_container_tag_count']}",
        f"BUILDLMDB: done OK={manifest['expected_container_tag_count']} tags rebuilt.",
        f"SET ORDER: CDX TAG '{manifest['generated_tag']}'",
        f"{manifest['expected_record_count']} cdx(lmdb) indexed record(s)",
    )
    for token in required:
        if token.upper() not in text.upper():
            findings.append(f"stage {stage} capture missing: {token}")
    for tag in manifest["expected_container_tags"]:
        if tag.upper() not in text.upper():
            findings.append(f"stage {stage} capture does not report retained tag {tag}")
    positions = [text.find(key) for key in manifest["expected_ordered_keys"]]
    if any(position < 0 for position in positions):
        findings.append(f"stage {stage} capture does not contain every expected key")
    elif positions != sorted(positions):
        findings.append(f"stage {stage} keys are not in CATALOG_OBJECT_ID order")
    return findings


def validate_resumable_stage1_workspace(
    workspace: Path,
    manifest: dict[str, Any],
    stage1_capture: Path,
) -> tuple[Path, Path, Path, Path, dict[str, dict[str, Any]]]:
    dbf_dir = workspace / "dbf"
    index_dir = workspace / "indexes"
    lmdb_root = workspace / "lmdb"
    source_dbf = REPO_ROOT / manifest["source_dbf"]
    source_container = REPO_ROOT / manifest["source_container"]
    isolated_dbf = dbf_dir / source_dbf.name
    cdx_path = index_dir / source_container.name
    env_dir = lmdb_root / f"{manifest['source_table']}.cdx.d"

    expected_root_names = {"dbf", "indexes", "lmdb", "stage1.dts"}
    root_names = {path.name for path in workspace.iterdir()}
    if root_names != expected_root_names:
        raise RuntimeError("resume workspace root has unexpected contents")
    if not dbf_dir.is_dir() or {path.name for path in dbf_dir.iterdir()} != {source_dbf.name}:
        raise RuntimeError("resume DBF directory does not contain exactly the isolated DBF")
    allowed_index_names = {source_container.name, source_container.name + ".meta"}
    index_names = {path.name for path in index_dir.iterdir()}
    if not index_names.issubset(allowed_index_names) or source_container.name not in index_names:
        raise RuntimeError("resume index directory has unexpected contents")
    if not lmdb_root.is_dir() or {path.name for path in lmdb_root.iterdir()} != {env_dir.name}:
        raise RuntimeError("resume LMDB root does not contain exactly the isolated environment")
    if sha256(isolated_dbf) != sha256(source_dbf):
        raise RuntimeError("resume DBF copy hash mismatch")
    if sha256(cdx_path) != sha256(source_container):
        raise RuntimeError("resume CDX copy hash mismatch")
    if not stage1_capture.is_file():
        raise RuntimeError("resume stage 1 capture is missing")
    findings = validate_capture(normalize_capture(stage1_capture), manifest, 1)
    if findings:
        raise RuntimeError("; ".join(findings))
    if not env_dir.is_dir():
        raise RuntimeError("resume isolated LMDB environment directory is missing")
    stage1_env = {path.name: file_state(path) for path in env_dir.iterdir() if path.is_file()}
    if set(stage1_env) != EXPECTED_ENV_FILES:
        raise RuntimeError("resume stage 1 environment is not exactly data.mdb and lock.mdb")
    return dbf_dir, index_dir, lmdb_root, cdx_path, stage1_env


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--workspace", type=Path, default=DEFAULT_WORKSPACE)
    parser.add_argument("--proof-json", type=Path, default=DEFAULT_PROOF_JSON)
    parser.add_argument("--stage1-capture", type=Path, default=DEFAULT_STAGE1_CAPTURE)
    parser.add_argument("--stage2-capture", type=Path, default=DEFAULT_STAGE2_CAPTURE)
    parser.add_argument("--executable", type=Path, default=REPO_ROOT / "build/src/Release/dottalkpp.exe")
    parser.add_argument(
        "--resume-after-stage1",
        action="store_true",
        help="resume only an exact, validated isolated stage-1 workspace",
    )
    args = parser.parse_args(argv)

    manifest = load_and_validate_manifest(args.manifest)
    workspace = args.workspace.resolve()
    allowed_root = (REPO_ROOT / "tmp/aif136_m5a").resolve()
    try:
        workspace.relative_to(allowed_root)
    except ValueError as exc:
        raise RuntimeError(f"workspace must remain under {allowed_root}") from exc
    if workspace.exists() and not args.resume_after_stage1:
        raise RuntimeError(f"refusing to reuse existing workspace: {workspace}")
    if not workspace.exists() and args.resume_after_stage1:
        raise RuntimeError(f"resume workspace does not exist: {workspace}")
    if not args.executable.is_file():
        raise RuntimeError(f"DotTalk++ executable not found: {args.executable}")

    before = protected_snapshot(manifest)
    source_dbf = REPO_ROOT / manifest["source_dbf"]
    source_container = REPO_ROOT / manifest["source_container"]
    args.proof_json.parent.mkdir(parents=True, exist_ok=True)
    args.stage1_capture.parent.mkdir(parents=True, exist_ok=True)
    executable_state = file_state(args.executable)

    if args.resume_after_stage1:
        dbf_dir, index_dir, lmdb_root, cdx_path, stage1_env = (
            validate_resumable_stage1_workspace(workspace, manifest, args.stage1_capture)
        )
        env_dir = lmdb_root / f"{manifest['source_table']}.cdx.d"
        isolated_dbf = dbf_dir / source_dbf.name
        env_initially_present_empty = True
    else:
        dbf_dir = workspace / "dbf"
        index_dir = workspace / "indexes"
        lmdb_root = workspace / "lmdb"
        env_dir = lmdb_root / f"{manifest['source_table']}.cdx.d"
        for directory in (dbf_dir, index_dir, env_dir):
            directory.mkdir(parents=True, exist_ok=False)
        env_initially_present_empty = env_dir.is_dir() and not any(env_dir.iterdir())
        isolated_dbf = dbf_dir / source_dbf.name
        cdx_path = index_dir / source_container.name
        shutil.copy2(source_dbf, isolated_dbf)
        shutil.copy2(source_container, cdx_path)
        if sha256(isolated_dbf) != sha256(source_dbf):
            raise RuntimeError("isolated DBF copy hash mismatch")
        if sha256(cdx_path) != sha256(source_container):
            raise RuntimeError("isolated CDX copy hash mismatch")

        stage1 = run_stage(
            args.executable,
            workspace / "stage1.dts",
            build_commands(
                stage=1,
                dbf_dir=dbf_dir,
                index_dir=index_dir,
                lmdb_root=lmdb_root,
                cdx_path=cdx_path,
                capture_path=args.stage1_capture.resolve(),
                table=manifest["source_table"],
                tag=manifest["generated_tag"],
            ),
        )
        if stage1.returncode != 0:
            raise RuntimeError(f"stage 1 process exited {stage1.returncode}: {stage1.stderr}")
        stage1_text = normalize_capture(args.stage1_capture)
        stage1_findings = validate_capture(stage1_text, manifest, 1)
        if stage1_findings:
            raise RuntimeError("; ".join(stage1_findings))
        stage1_env = {path.name: file_state(path) for path in env_dir.iterdir() if path.is_file()}
        if set(stage1_env) != EXPECTED_ENV_FILES:
            raise RuntimeError("stage 1 did not create exactly data.mdb and lock.mdb")

    clear_isolated_env_files(env_dir)
    directory_survived_clear = env_dir.is_dir() and not any(env_dir.iterdir())

    stage2 = run_stage(
        args.executable,
        workspace / "stage2.dts",
        build_commands(
            stage=2,
            dbf_dir=dbf_dir,
            index_dir=index_dir,
            lmdb_root=lmdb_root,
            cdx_path=cdx_path,
            capture_path=args.stage2_capture.resolve(),
            table=manifest["source_table"],
            tag=manifest["generated_tag"],
        ),
    )
    if stage2.returncode != 0:
        raise RuntimeError(f"stage 2 process exited {stage2.returncode}: {stage2.stderr}")
    stage2_text = normalize_capture(args.stage2_capture)
    stage2_findings = validate_capture(stage2_text, manifest, 2)
    if stage2_findings:
        raise RuntimeError("; ".join(stage2_findings))
    stage2_env = {path.name: file_state(path) for path in env_dir.iterdir() if path.is_file()}
    if set(stage2_env) != EXPECTED_ENV_FILES:
        raise RuntimeError("stage 2 did not reconstruct exactly data.mdb and lock.mdb")

    after = protected_snapshot(manifest)
    protected_unchanged = before == after
    if not protected_unchanged:
        raise RuntimeError("one or more protected files changed during M5-A")

    proof = {
        "schema": "dottalk.portal.m5a-reconstruction-proof.v1",
        "manifest_id": manifest["manifest_id"],
        "run_id": manifest["run_id"],
        "created_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "status": "PASS",
        "executable": executable_state,
        "workspace": workspace.as_posix(),
        "resumed_after_validated_stage1": args.resume_after_stage1,
        "source_dbf_copy_sha256": sha256(isolated_dbf),
        "source_container_copy_sha256": sha256(cdx_path),
        "preserved_cdx": file_state(cdx_path),
        "environment_directory_initially_present_empty": env_initially_present_empty,
        "environment_directory_survived_clear": directory_survived_clear,
        "environment_directory_present_after_rebuild": env_dir.is_dir(),
        "stage1_capture": file_state(args.stage1_capture),
        "stage1_environment_files": stage1_env,
        "stage2_capture": file_state(args.stage2_capture),
        "stage2_environment_files": stage2_env,
        "protected_before": before,
        "protected_after": after,
        "protected_unchanged": protected_unchanged,
        "existing_files_removed": 0,
        "existing_directories_removed": 0,
        "m5b_action_authorized": False,
    }
    args.proof_json.write_text(json.dumps(proof, indent=2, sort_keys=True) + "\n", encoding="ascii")
    print(f"AIF-136 M5-A: PASS -- proof {args.proof_json}")
    print("existing files removed: 0; existing directories removed: 0")
    print("M5-B remains separately authorized")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, ValueError, json.JSONDecodeError) as exc:
        print(f"AIF-136 M5-A: FAIL -- {exc}", file=sys.stderr)
        raise SystemExit(2)
