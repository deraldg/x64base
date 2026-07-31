from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any


SCHEMA = "dottalk.staging.dirty_worktree_preservation.v1"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest().upper()


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _git(root: Path, *args: str, text: bool = True) -> str | bytes:
    command = ["git", "-c", f"safe.directory={root.as_posix()}", "-C", str(root), *args]
    result = subprocess.run(command, check=True, capture_output=True, text=text)
    return result.stdout


def parse_porcelain_z(value: bytes) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for raw in value.split(b"\0"):
        if not raw:
            continue
        text = raw.decode("utf-8", errors="surrogateescape")
        if len(text) < 4 or text[2] != " ":
            raise ValueError(f"unexpected porcelain row: {text!r}")
        status = text[:2]
        if "R" in status or "C" in status:
            raise ValueError("rename/copy status is unsupported; rerun with --no-renames")
        rows.append({"status": status, "path": text[3:]})
    return rows


def safe_file(root: Path, relative: str) -> Path:
    posix = PurePosixPath(relative)
    if posix.is_absolute() or ".." in posix.parts:
        raise ValueError(f"unsafe relative path: {relative}")
    candidate = (root / Path(*posix.parts)).resolve()
    try:
        candidate.relative_to(root.resolve())
    except ValueError as exc:
        raise ValueError(f"path escapes staging root: {relative}") from exc
    if not candidate.is_file():
        raise ValueError(f"dirty path is not a file: {relative}")
    return candidate


def load_baseline(path: Path) -> dict[str, dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    return {row["path"]: row for row in rows}


def validate_baseline(
    observed: list[dict[str, str]],
    baseline: dict[str, dict[str, str]],
    staging_root: Path,
) -> list[str]:
    findings: list[str] = []
    observed_paths = {row["path"] for row in observed}
    if observed_paths != set(baseline):
        findings.append(
            f"PATH_SET:observed={len(observed_paths)}:baseline={len(baseline)}"
        )
    for row in observed:
        relative = row["path"]
        expected = baseline.get(relative, {})
        if row["status"] != expected.get("status"):
            findings.append(f"STATUS:{relative}:{row['status']}:{expected.get('status', '')}")
        try:
            source = safe_file(staging_root, relative)
        except ValueError as exc:
            findings.append(f"SOURCE:{exc}")
            continue
        observed_hash = sha256_file(source)
        if observed_hash != expected.get("c_sha256"):
            findings.append(f"HASH:{relative}:{observed_hash}:{expected.get('c_sha256', '')}")
    return findings


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]) if rows else ["status", "path"])
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def preserve(
    staging_root: Path,
    repo_root: Path,
    output_root: Path,
    baseline_csv: Path,
    expected_head: str,
) -> dict[str, Any]:
    if sys.version_info[:2] != (3, 12):
        raise ValueError("preserve_staging_worktree requires Python 3.12.x")
    staging_root = staging_root.resolve()
    repo_root = repo_root.resolve()
    output_root = output_root.resolve()
    baseline_csv = baseline_csv.resolve()
    try:
        output_root.relative_to(repo_root)
    except ValueError as exc:
        raise ValueError("output root must stay inside authoritative development") from exc
    if output_root.exists():
        raise ValueError(f"output root already exists: {output_root}")
    if not (staging_root / ".git").exists():
        raise ValueError(f"staging root is not a Git worktree: {staging_root}")

    head = str(_git(staging_root, "rev-parse", "HEAD")).strip()
    branch = str(_git(staging_root, "branch", "--show-current")).strip()
    if head != expected_head:
        raise ValueError(f"staging HEAD drift: expected {expected_head}, observed {head}")
    raw_status = _git(
        staging_root,
        "status",
        "--porcelain=v1",
        "-z",
        "--untracked-files=all",
        "--no-renames",
        text=False,
    )
    assert isinstance(raw_status, bytes)
    observed = parse_porcelain_z(raw_status)
    baseline = load_baseline(baseline_csv)
    findings = validate_baseline(observed, baseline, staging_root)
    if findings:
        raise ValueError("preservation preflight failed: " + "; ".join(findings))

    files_root = output_root / "files"
    output_root.mkdir(parents=True, exist_ok=False)
    copied_rows: list[dict[str, Any]] = []
    for row in observed:
        relative = row["path"]
        source = safe_file(staging_root, relative)
        destination = files_root / Path(*PurePosixPath(relative).parts)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        source_hash = sha256_file(source)
        copied_hash = sha256_file(destination)
        if copied_hash != source_hash:
            raise OSError(f"copy verification failed: {relative}")
        copied_rows.append(
            {
                "status": row["status"],
                "path": relative,
                "bytes": source.stat().st_size,
                "sha256": source_hash,
                "backup_path": destination.relative_to(output_root).as_posix(),
                "backup_sha256": copied_hash,
            }
        )

    status_text = _git(
        staging_root,
        "status",
        "--porcelain=v1",
        "--untracked-files=all",
        "--no-renames",
    )
    tracked_patch = _git(staging_root, "diff", "--binary", "--no-ext-diff", text=False)
    cached_patch = _git(staging_root, "diff", "--cached", "--binary", "--no-ext-diff", text=False)
    assert isinstance(tracked_patch, bytes) and isinstance(cached_patch, bytes)
    (output_root / "status_before.txt").write_text(str(status_text), encoding="utf-8")
    (output_root / "tracked_worktree.patch").write_bytes(tracked_patch)
    (output_root / "cached_index.patch").write_bytes(cached_patch)
    write_csv(output_root / "preserved_files.csv", copied_rows)

    manifest = {
        "schema": SCHEMA,
        "created_utc": utc_now(),
        "staging_root": str(staging_root),
        "development_root": str(repo_root),
        "branch": branch,
        "head": head,
        "baseline_csv": baseline_csv.relative_to(repo_root).as_posix(),
        "baseline_csv_sha256": sha256_file(baseline_csv),
        "dirty_paths": len(copied_rows),
        "tracked_modified": sum(row["status"] != "??" for row in copied_rows),
        "untracked": sum(row["status"] == "??" for row in copied_rows),
        "preserved_bytes": sum(int(row["bytes"]) for row in copied_rows),
        "status_sha256": sha256_bytes(str(status_text).encode("utf-8")),
        "tracked_patch_sha256": sha256_file(output_root / "tracked_worktree.patch"),
        "cached_patch_sha256": sha256_file(output_root / "cached_index.patch"),
        "file_manifest": "preserved_files.csv",
        "file_manifest_sha256": sha256_file(output_root / "preserved_files.csv"),
        "findings": [],
        "source_staging_mutated": 0,
    }
    write_json(output_root / "preservation_manifest.json", manifest)
    (output_root / "README.md").write_text(
        "# C:\\x64base dirty-worktree preservation\n\n"
        f"- Branch / HEAD: `{branch}` / `{head}`\n"
        f"- Preserved files: `{len(copied_rows)}`\n"
        f"- Preserved bytes: `{manifest['preserved_bytes']}`\n"
        "- Staging mutation: `0`\n\n"
        "This package preserves exact bytes before any future fresh staging rebuild. "
        "It is safety evidence, not publication authority and not an instruction to restore all adjacent work into the documentation lane.\n",
        encoding="utf-8",
    )
    return manifest


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Byte-preserve one exact dirty x64base staging worktree into authoritative development.")
    parser.add_argument("--staging-root", required=True)
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--output-root", required=True)
    parser.add_argument("--baseline-csv", required=True)
    parser.add_argument("--expected-head", required=True)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    manifest = preserve(
        Path(args.staging_root),
        Path(args.repo_root),
        Path(args.output_root),
        Path(args.baseline_csv),
        args.expected_head,
    )
    print(
        "staging_preservation "
        f"files={manifest['dirty_paths']} tracked={manifest['tracked_modified']} "
        f"untracked={manifest['untracked']} bytes={manifest['preserved_bytes']} "
        "staging_mutated=0 status=PASS"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
