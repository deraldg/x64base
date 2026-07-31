from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
import subprocess
import sys
import tarfile
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath


SCHEMA = "dottalk.staging.public_baseline_escrow.v1"
EXPECTED_PRESERVATION_SCHEMA = "dottalk.staging.dirty_worktree_preservation.v1"
EXPECTED_OVERLAY_SCHEMA = "dottalk.staging.gate5_selective_overlay_plan.v1"


def require_python_312() -> None:
    if sys.version_info[:2] != (3, 12):
        raise RuntimeError(
            f"Python 3.12 is required; running {sys.version_info.major}.{sys.version_info.minor}"
        )


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def normalized_relative(value: str) -> str:
    path = PurePosixPath(value.replace("\\", "/"))
    if path.is_absolute() or ".." in path.parts or not path.parts:
        raise ValueError(f"unsafe relative path: {value}")
    return path.as_posix()


def git_command(staging_root: Path, *args: str) -> list[str]:
    safe = staging_root.resolve().as_posix()
    return ["git", "-c", f"safe.directory={safe}", "-C", str(staging_root), *args]


def git_text(staging_root: Path, *args: str) -> str:
    result = subprocess.run(
        git_command(staging_root, *args),
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return result.stdout.strip()


def git_bytes(staging_root: Path, *args: str) -> bytes:
    result = subprocess.run(
        git_command(staging_root, *args),
        check=True,
        capture_output=True,
    )
    return result.stdout


def write_git_archive(staging_root: Path, head: str, destination: Path) -> None:
    with destination.open("wb") as handle:
        subprocess.run(
            git_command(staging_root, "archive", "--format=tar", head),
            check=True,
            stdout=handle,
        )


def write_git_bundle(staging_root: Path, branch: str, destination: Path) -> str:
    subprocess.run(
        git_command(
            staging_root,
            "bundle",
            "create",
            str(destination),
            f"refs/heads/{branch}",
        ),
        check=True,
    )
    result = subprocess.run(
        git_command(staging_root, "bundle", "verify", str(destination)),
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return (result.stdout + result.stderr).strip()


def classify_relation(baseline_sha256: str, development_path: Path) -> tuple[str, str, int]:
    if not development_path.is_file():
        return "PUBLIC_BASELINE_ONLY", "", 0
    development_sha256 = sha256_file(development_path)
    relation = "EXACT_IN_DEVELOPMENT" if development_sha256 == baseline_sha256 else "DIVERGENT_FROM_DEVELOPMENT"
    return relation, development_sha256, development_path.stat().st_size


def archive_ledger(archive_path: Path, development_root: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    with tarfile.open(archive_path, "r") as archive:
        for member in archive.getmembers():
            if not member.isfile():
                continue
            relative = normalized_relative(member.name)
            extracted = archive.extractfile(member)
            if extracted is None:
                raise RuntimeError(f"unable to read archive member: {relative}")
            digest = hashlib.sha256()
            for block in iter(lambda: extracted.read(1024 * 1024), b""):
                digest.update(block)
            baseline_sha256 = digest.hexdigest().upper()
            relation, development_sha256, development_bytes = classify_relation(
                baseline_sha256, development_root / Path(relative)
            )
            rows.append(
                {
                    "path": relative,
                    "baseline_bytes": member.size,
                    "baseline_sha256": baseline_sha256,
                    "development_relation": relation,
                    "development_bytes": development_bytes,
                    "development_sha256": development_sha256,
                }
            )
    return sorted(rows, key=lambda row: str(row["path"]).casefold())


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def preserve_ignored_files(staging_root: Path, output_dir: Path, head: str) -> dict[str, object]:
    raw = git_bytes(
        staging_root,
        "ls-files",
        "--others",
        "--ignored",
        "--exclude-standard",
        "-z",
    )
    relatives = sorted(
        (normalized_relative(value.decode("utf-8", errors="surrogateescape")) for value in raw.split(b"\0") if value),
        key=str.casefold,
    )
    ignored_root = output_dir / "ignored_worktree_preservation"
    files_root = ignored_root / "files"
    rows: list[dict[str, object]] = []
    for relative in relatives:
        source = (staging_root / Path(relative)).resolve()
        try:
            source.relative_to(staging_root)
        except ValueError as exc:
            raise RuntimeError(f"ignored path escapes staging root: {relative}") from exc
        if not source.is_file():
            raise RuntimeError(f"ignored path is not a file: {relative}")
        destination = files_root / Path(relative)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        source_hash = sha256_file(source)
        copy_hash = sha256_file(destination)
        if source_hash != copy_hash:
            raise RuntimeError(f"ignored-file copy verification failed: {relative}")
        rows.append(
            {
                "path": relative,
                "bytes": source.stat().st_size,
                "sha256": source_hash,
                "backup_path": destination.relative_to(ignored_root).as_posix(),
                "backup_sha256": copy_hash,
            }
        )
    ledger_path = ignored_root / "ignored_files.csv"
    write_csv(
        ledger_path,
        rows,
        ["path", "bytes", "sha256", "backup_path", "backup_sha256"],
    )
    manifest = {
        "schema": "dottalk.staging.ignored_worktree_preservation.v1",
        "created_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "head": head,
        "ignored_files": len(rows),
        "ignored_bytes": sum(int(row["bytes"]) for row in rows),
        "file_manifest": ledger_path.name,
        "file_manifest_sha256": sha256_file(ledger_path),
        "staging_mutated": 0,
    }
    manifest_path = ignored_root / "ignored_preservation_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return {
        "manifest_path": manifest_path,
        "manifest_sha256": sha256_file(manifest_path),
        "file_count": len(rows),
        "bytes": manifest["ignored_bytes"],
    }


def verify_preservation_package(preservation_root: Path, expected_head: str) -> dict[str, object]:
    manifest_path = preservation_root / "preservation_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("schema") != EXPECTED_PRESERVATION_SCHEMA:
        raise RuntimeError("unexpected dirty-worktree preservation schema")
    if manifest.get("head") != expected_head:
        raise RuntimeError("dirty-worktree preservation HEAD does not match escrow HEAD")
    ledger_path = preservation_root / str(manifest["file_manifest"])
    if sha256_file(ledger_path) != manifest.get("file_manifest_sha256"):
        raise RuntimeError("dirty-worktree preservation ledger hash mismatch")
    with ledger_path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if len(rows) != int(manifest.get("dirty_paths", -1)):
        raise RuntimeError("dirty-worktree preservation row count mismatch")
    for row in rows:
        backup_path = preservation_root / Path(normalized_relative(row["backup_path"]))
        if sha256_file(backup_path) != row["backup_sha256"]:
            raise RuntimeError(f"dirty-worktree backup hash mismatch: {row['path']}")
    return {
        "manifest_sha256": sha256_file(manifest_path),
        "file_count": len(rows),
        "preserved_bytes": sum(int(row["bytes"]) for row in rows),
    }


def verify_overlay_plan(overlay_root: Path, expected_head: str) -> dict[str, object]:
    manifest_path = overlay_root / "gate5_staging_overlay_plan_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("schema") != EXPECTED_OVERLAY_SCHEMA:
        raise RuntimeError("unexpected Gate 5 overlay-plan schema")
    if manifest.get("head") != expected_head:
        raise RuntimeError("Gate 5 overlay-plan HEAD does not match escrow HEAD")
    ledger_path = overlay_root / "gate5_staging_overlay_ledger.csv"
    if sha256_file(ledger_path) != manifest["artifacts"]["ledger_sha256"]:
        raise RuntimeError("Gate 5 overlay ledger hash mismatch")
    return {
        "manifest_sha256": sha256_file(manifest_path),
        "ledger_sha256": sha256_file(ledger_path),
        "planned_files": int(manifest["counts"]["planned_files"]),
        "planned_bytes": int(manifest["counts"]["planned_bytes"]),
    }


def create_escrow(
    staging_root: Path,
    development_root: Path,
    output_dir: Path,
    preservation_root: Path,
    overlay_root: Path,
    expected_head: str,
) -> Path:
    staging_root = staging_root.resolve()
    development_root = development_root.resolve()
    preservation_root = preservation_root.resolve()
    overlay_root = overlay_root.resolve()
    output_dir = output_dir.resolve()
    if output_dir.exists():
        raise FileExistsError(f"output directory already exists: {output_dir}")

    head = git_text(staging_root, "rev-parse", "HEAD")
    branch = git_text(staging_root, "branch", "--show-current")
    origin_head = git_text(staging_root, "rev-parse", f"origin/{branch}")
    if head != expected_head:
        raise RuntimeError(f"staging HEAD mismatch: expected {expected_head}, found {head}")
    if origin_head != head:
        raise RuntimeError(f"local origin/{branch} does not match staging HEAD")

    preservation = verify_preservation_package(preservation_root, head)
    overlay = verify_overlay_plan(overlay_root, head)

    output_dir.mkdir(parents=True)
    archive_path = output_dir / f"x64base-public-baseline-{head[:8]}.tar"
    bundle_path = output_dir / f"x64base-public-baseline-{head[:8]}.bundle"
    ledger_path = output_dir / "public_baseline_files.csv"
    public_only_path = output_dir / "public_baseline_only_reconciliation.csv"

    write_git_archive(staging_root, head, archive_path)
    bundle_verification = write_git_bundle(staging_root, branch, bundle_path)
    rows = archive_ledger(archive_path, development_root)
    if not rows:
        raise RuntimeError("public baseline archive contains no files")
    write_csv(
        ledger_path,
        rows,
        [
            "path",
            "baseline_bytes",
            "baseline_sha256",
            "development_relation",
            "development_bytes",
            "development_sha256",
        ],
    )

    public_only_rows = [
        {
            "path": row["path"],
            "baseline_bytes": row["baseline_bytes"],
            "baseline_sha256": row["baseline_sha256"],
            "reset_disposition": "RETAIN_FROM_VERIFIED_PUBLIC_BASELINE",
            "development_disposition": "REVIEW_FOR_ADOPTION_OR_PUBLIC_BASELINE_OWNERSHIP",
        }
        for row in rows
        if row["development_relation"] == "PUBLIC_BASELINE_ONLY"
    ]
    write_csv(
        public_only_path,
        public_only_rows,
        [
            "path",
            "baseline_bytes",
            "baseline_sha256",
            "reset_disposition",
            "development_disposition",
        ],
    )

    preservation_copy = output_dir / "dirty_worktree_preservation"
    overlay_copy = output_dir / "gate5_overlay_plan"
    shutil.copytree(preservation_root, preservation_copy)
    shutil.copytree(overlay_root, overlay_copy)
    ignored = preserve_ignored_files(staging_root, output_dir, head)

    counts = {
        "baseline_files": len(rows),
        "baseline_bytes": sum(int(row["baseline_bytes"]) for row in rows),
        "exact_in_development": sum(row["development_relation"] == "EXACT_IN_DEVELOPMENT" for row in rows),
        "divergent_from_development": sum(
            row["development_relation"] == "DIVERGENT_FROM_DEVELOPMENT" for row in rows
        ),
        "public_baseline_only": len(public_only_rows),
        "preserved_dirty_files": preservation["file_count"],
        "preserved_ignored_files": ignored["file_count"],
        "preserved_ignored_bytes": ignored["bytes"],
        "gate5_overlay_files": overlay["planned_files"],
    }
    manifest = {
        "schema": SCHEMA,
        "created_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "status": "RECOVERY_VERIFIED_RESET_AUTHORIZATION_SEPARATE",
        "staging_root": str(staging_root),
        "development_root": str(development_root),
        "branch": branch,
        "head": head,
        "local_origin_head": origin_head,
        "counts": counts,
        "artifacts": {
            "archive": archive_path.name,
            "archive_sha256": sha256_file(archive_path),
            "bundle": bundle_path.name,
            "bundle_sha256": sha256_file(bundle_path),
            "baseline_ledger": ledger_path.name,
            "baseline_ledger_sha256": sha256_file(ledger_path),
            "public_only_ledger": public_only_path.name,
            "public_only_ledger_sha256": sha256_file(public_only_path),
            "dirty_preservation": "dirty_worktree_preservation/preservation_manifest.json",
            "dirty_preservation_sha256": preservation["manifest_sha256"],
            "ignored_preservation": "ignored_worktree_preservation/ignored_preservation_manifest.json",
            "ignored_preservation_sha256": ignored["manifest_sha256"],
            "gate5_overlay_plan": "gate5_overlay_plan/gate5_staging_overlay_plan_manifest.json",
            "gate5_overlay_plan_sha256": overlay["manifest_sha256"],
            "gate5_overlay_ledger_sha256": overlay["ledger_sha256"],
        },
        "bundle_verification": bundle_verification.splitlines(),
        "reset_contract": {
            "baseline": "restore the exact committed public baseline from bundle, archive, or matching origin/main",
            "dirty_layer": "restore all preserved dirty files exactly before applying a publication overlay",
            "ignored_layer": "restore every ignored file removed by git clean from its exact escrowed byte",
            "gate5_layer": "apply only the hash-bound 316-file Gate 5 overlay; PROMOTE.manifest intentionally supersedes its preserved dirty byte",
            "public_only": "retain all public-baseline-only paths from the verified baseline; upstream adoption remains separately reviewable",
            "git_and_website": "not authorized by this escrow",
        },
    }
    manifest_path = output_dir / "public_baseline_escrow_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    readme = f"""# x64base public-baseline recovery escrow

Status: **recovery verified; destructive reset authorization remains separate**.

This package closes the assumption that `C:\\x64base` can be recovered only
from a live GitHub checkout. It binds public baseline `{head}`, all
{counts['baseline_files']} committed files, the {counts['public_baseline_only']}
paths absent from authoritative development, the complete
{counts['preserved_dirty_files']}-file dirty staging layer, the
{counts['preserved_ignored_files']}-file ignored layer, and the exact
{counts['gate5_overlay_files']}-file Gate 5 plan.

Recovery choices:

```powershell
git clone .\\{bundle_path.name} restored-x64base

# Or restore committed bytes without Git history:
tar -xf .\\{archive_path.name} -C <empty-directory>
```

Neither recovery choice authorizes publication. A correct staging rebuild must
restore the committed baseline, restore the preserved dirty and ignored layers,
then apply the separately authorized Gate 5 overlay. The overlay intentionally replaces
the preserved `PROMOTE.manifest`; it does not erase the other preserved files.
"""
    (output_dir / "README.md").write_text(readme, encoding="utf-8")
    return manifest_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create an offline, hash-bound recovery escrow for the x64base public staging baseline."
    )
    parser.add_argument("--staging-root", required=True, type=Path)
    parser.add_argument("--development-root", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--preservation-root", required=True, type=Path)
    parser.add_argument("--overlay-plan-root", required=True, type=Path)
    parser.add_argument("--expected-head", required=True)
    return parser.parse_args()


def main() -> int:
    require_python_312()
    args = parse_args()
    manifest_path = create_escrow(
        args.staging_root,
        args.development_root,
        args.output_dir,
        args.preservation_root,
        args.overlay_plan_root,
        args.expected_head,
    )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    counts = manifest["counts"]
    print(f"escrow={manifest_path.parent}")
    print(
        "baseline_files={baseline_files} public_only={public_baseline_only} "
        "dirty={preserved_dirty_files} ignored={preserved_ignored_files} "
        "gate5={gate5_overlay_files}".format(**counts)
    )
    print(f"manifest_sha256={sha256_file(manifest_path)}")
    print("staging_mutated=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
