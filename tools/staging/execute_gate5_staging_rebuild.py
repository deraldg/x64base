from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any


sys.path.insert(0, str(Path(__file__).resolve().parent))
from preserve_staging_worktree import parse_porcelain_z  # noqa: E402


ESCROW_SCHEMA = "dottalk.staging.public_baseline_escrow.v1"
OVERLAY_SCHEMA = "dottalk.staging.gate5_selective_overlay_plan.v1"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def safe_path(root: Path, relative: str, must_exist: bool = False) -> Path:
    posix = PurePosixPath(relative.replace("\\", "/"))
    if posix.is_absolute() or ".." in posix.parts or not posix.parts:
        raise ValueError(f"unsafe relative path: {relative}")
    candidate = (root / Path(*posix.parts)).resolve()
    try:
        candidate.relative_to(root.resolve())
    except ValueError as exc:
        raise ValueError(f"path escapes root: {relative}") from exc
    if must_exist and not candidate.is_file():
        raise FileNotFoundError(candidate)
    return candidate


def git_command(root: Path, *args: str) -> list[str]:
    return ["git", "-c", f"safe.directory={root.resolve().as_posix()}", "-C", str(root), *args]


def git_run(root: Path, *args: str, text: bool = True, check: bool = True) -> str | bytes:
    result = subprocess.run(
        git_command(root, *args),
        check=check,
        capture_output=True,
        text=text,
        encoding="utf-8" if text else None,
        errors="replace" if text else None,
    )
    return result.stdout


def load_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def verify_artifact(base: Path, relative: str, expected_hash: str) -> Path:
    path = safe_path(base, relative, must_exist=True)
    actual = sha256_file(path)
    if actual != expected_hash:
        raise ValueError(f"artifact hash mismatch: {relative}: expected {expected_hash}, found {actual}")
    return path


def load_bound_escrow(escrow_root: Path, expected_manifest_hash: str) -> dict[str, Any]:
    escrow_root = escrow_root.resolve()
    manifest_path = escrow_root / "public_baseline_escrow_manifest.json"
    if sha256_file(manifest_path) != expected_manifest_hash:
        raise ValueError("escrow manifest hash mismatch")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("schema") != ESCROW_SCHEMA:
        raise ValueError("unexpected escrow schema")
    artifacts = manifest["artifacts"]
    for key, hash_key in (
        ("archive", "archive_sha256"),
        ("bundle", "bundle_sha256"),
        ("baseline_ledger", "baseline_ledger_sha256"),
        ("public_only_ledger", "public_only_ledger_sha256"),
        ("dirty_preservation", "dirty_preservation_sha256"),
        ("ignored_preservation", "ignored_preservation_sha256"),
        ("gate5_overlay_plan", "gate5_overlay_plan_sha256"),
    ):
        verify_artifact(escrow_root, artifacts[key], artifacts[hash_key])

    dirty_manifest_path = safe_path(escrow_root, artifacts["dirty_preservation"], must_exist=True)
    dirty_root = dirty_manifest_path.parent
    dirty_manifest = json.loads(dirty_manifest_path.read_text(encoding="utf-8"))
    dirty_ledger_path = verify_artifact(
        dirty_root,
        dirty_manifest["file_manifest"],
        dirty_manifest["file_manifest_sha256"],
    )
    dirty_rows = load_csv(dirty_ledger_path)

    ignored_manifest_path = safe_path(escrow_root, artifacts["ignored_preservation"], must_exist=True)
    ignored_root = ignored_manifest_path.parent
    ignored_manifest = json.loads(ignored_manifest_path.read_text(encoding="utf-8"))
    ignored_ledger_path = verify_artifact(
        ignored_root,
        ignored_manifest["file_manifest"],
        ignored_manifest["file_manifest_sha256"],
    )
    ignored_rows = load_csv(ignored_ledger_path)

    overlay_manifest_path = safe_path(escrow_root, artifacts["gate5_overlay_plan"], must_exist=True)
    overlay_root = overlay_manifest_path.parent
    overlay_manifest = json.loads(overlay_manifest_path.read_text(encoding="utf-8"))
    if overlay_manifest.get("schema") != OVERLAY_SCHEMA:
        raise ValueError("unexpected overlay schema")
    overlay_ledger_path = overlay_root / "gate5_staging_overlay_ledger.csv"
    if sha256_file(overlay_ledger_path) != artifacts["gate5_overlay_ledger_sha256"]:
        raise ValueError("overlay ledger hash mismatch")
    overlay_rows = load_csv(overlay_ledger_path)

    public_only_path = safe_path(escrow_root, artifacts["public_only_ledger"], must_exist=True)
    public_only_rows = load_csv(public_only_path)
    return {
        "root": escrow_root,
        "manifest_path": manifest_path,
        "manifest": manifest,
        "dirty_root": dirty_root,
        "dirty_rows": dirty_rows,
        "ignored_root": ignored_root,
        "ignored_rows": ignored_rows,
        "overlay_manifest": overlay_manifest,
        "overlay_rows": overlay_rows,
        "public_only_rows": public_only_rows,
    }


def observed_status(staging_root: Path) -> list[dict[str, str]]:
    raw = git_run(
        staging_root,
        "status",
        "--porcelain=v1",
        "-z",
        "--untracked-files=all",
        "--no-renames",
        text=False,
    )
    assert isinstance(raw, bytes)
    return parse_porcelain_z(raw)


def observed_ignored(staging_root: Path) -> list[str]:
    raw = git_run(
        staging_root,
        "ls-files",
        "--others",
        "--ignored",
        "--exclude-standard",
        "-z",
        text=False,
    )
    assert isinstance(raw, bytes)
    return sorted(
        value.decode("utf-8", errors="surrogateescape") for value in raw.split(b"\0") if value
    )


def verify_current_layers(staging_root: Path, bound: dict[str, Any]) -> None:
    expected_dirty = {row["path"]: row for row in bound["dirty_rows"]}
    observed = {row["path"]: row for row in observed_status(staging_root)}
    if set(observed) != set(expected_dirty):
        raise ValueError(f"dirty path-set drift: expected {len(expected_dirty)}, found {len(observed)}")
    for relative, expected in expected_dirty.items():
        if observed[relative]["status"] != expected["status"]:
            raise ValueError(f"dirty status drift: {relative}")
        if sha256_file(safe_path(staging_root, relative, must_exist=True)) != expected["sha256"]:
            raise ValueError(f"dirty hash drift: {relative}")

    expected_ignored = {row["path"]: row for row in bound["ignored_rows"]}
    ignored = observed_ignored(staging_root)
    if ignored != sorted(expected_ignored):
        raise ValueError(f"ignored path-set drift: expected {len(expected_ignored)}, found {len(ignored)}")
    for relative, expected in expected_ignored.items():
        if sha256_file(safe_path(staging_root, relative, must_exist=True)) != expected["sha256"]:
            raise ValueError(f"ignored hash drift: {relative}")


def verify_sources(development_root: Path, overlay_rows: list[dict[str, str]]) -> None:
    for row in overlay_rows:
        source = safe_path(development_root, row["path"], must_exist=True)
        if sha256_file(source) != row["source_sha256"]:
            raise ValueError(f"overlay source drift: {row['path']}")


def restore_rows(root: Path, backup_root: Path, rows: list[dict[str, str]]) -> None:
    for row in rows:
        source = safe_path(backup_root, row["backup_path"], must_exist=True)
        if sha256_file(source) != row["backup_sha256"]:
            raise ValueError(f"backup drift: {row['path']}")
        destination = safe_path(root, row["path"])
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        if sha256_file(destination) != row["sha256"]:
            raise OSError(f"restore verification failed: {row['path']}")


def apply_overlay(staging_root: Path, development_root: Path, rows: list[dict[str, str]]) -> None:
    for row in rows:
        source = safe_path(development_root, row["path"], must_exist=True)
        destination = safe_path(staging_root, row["path"])
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        if sha256_file(destination) != row["source_sha256"]:
            raise OSError(f"overlay verification failed: {row['path']}")


def reset_to_baseline(staging_root: Path, branch: str, head: str) -> None:
    git_run(staging_root, "checkout", branch)
    git_run(staging_root, "reset", "--hard", head)
    git_run(staging_root, "clean", "-fdx", "-e", ".git")


def verify_final(
    staging_root: Path,
    development_root: Path,
    bound: dict[str, Any],
) -> dict[str, Any]:
    manifest = bound["manifest"]
    head = str(git_run(staging_root, "rev-parse", "HEAD")).strip()
    if head != manifest["head"]:
        raise ValueError("final HEAD drift")
    baseline_tree = str(git_run(staging_root, "rev-parse", f"{head}^{{tree}}")).strip()
    index_tree = str(git_run(staging_root, "write-tree")).strip()
    if index_tree != baseline_tree:
        raise ValueError("Git index tree differs from baseline tree")

    overlay = {row["path"]: row for row in bound["overlay_rows"]}
    dirty = {row["path"]: row for row in bound["dirty_rows"]}
    for relative, row in dirty.items():
        expected = overlay.get(relative, {}).get("source_sha256", row["sha256"])
        if sha256_file(safe_path(staging_root, relative, must_exist=True)) != expected:
            raise ValueError(f"final dirty-layer drift: {relative}")
    for relative, row in overlay.items():
        if sha256_file(safe_path(staging_root, relative, must_exist=True)) != row["source_sha256"]:
            raise ValueError(f"final overlay drift: {relative}")
        if sha256_file(safe_path(development_root, relative, must_exist=True)) != row["source_sha256"]:
            raise ValueError(f"development source changed during apply: {relative}")
    for row in bound["ignored_rows"]:
        if sha256_file(safe_path(staging_root, row["path"], must_exist=True)) != row["sha256"]:
            raise ValueError(f"final ignored-layer drift: {row['path']}")
    for row in bound["public_only_rows"]:
        relative = row["path"]
        safe_path(staging_root, relative, must_exist=True)
        expected_oid = str(git_run(staging_root, "rev-parse", f"{head}:{relative}")).strip()
        actual_oid = str(
            git_run(staging_root, "hash-object", f"--path={relative}", relative)
        ).strip()
        if actual_oid != expected_oid:
            raise ValueError(
                f"final public-only Git-blob drift: {relative}: expected {expected_oid}, found {actual_oid}"
            )

    expected_status_paths = set(dirty) | set(overlay)
    status = observed_status(staging_root)
    if {row["path"] for row in status} != expected_status_paths:
        raise ValueError(
            f"final status path-set mismatch: expected {len(expected_status_paths)}, found {len(status)}"
        )
    if observed_ignored(staging_root) != sorted(row["path"] for row in bound["ignored_rows"]):
        raise ValueError("final ignored path-set mismatch")
    cached = subprocess.run(git_command(staging_root, "diff", "--cached", "--quiet"))
    if cached.returncode != 0:
        raise ValueError("Git index contains staged changes")
    return {
        "head": head,
        "baseline_tree": baseline_tree,
        "index_tree": index_tree,
        "status_files": len(status),
        "tracked_modified": sum(row["status"] != "??" for row in status),
        "untracked": sum(row["status"] == "??" for row in status),
        "ignored": len(bound["ignored_rows"]),
        "public_only_verified": len(bound["public_only_rows"]),
        "dirty_verified": len(bound["dirty_rows"]),
        "overlay_verified": len(bound["overlay_rows"]),
    }


def write_execution_record(output_root: Path, value: dict[str, Any]) -> None:
    output_root.mkdir(parents=True, exist_ok=False)
    (output_root / "gate5_staging_execution_manifest.json").write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (output_root / "README.md").write_text(
        "# Gate 5 recovery-bound staging execution\n\n"
        f"- Status: `{value['status']}`\n"
        f"- Baseline: `{value['head']}`\n"
        f"- Dirty / ignored / overlay: `{value['final']['dirty_verified']}` / "
        f"`{value['final']['ignored']}` / `{value['final']['overlay_verified']}`\n"
        "- Git staging, commit, push, and website mutation: `0`\n",
        encoding="utf-8",
    )


def run(args: argparse.Namespace) -> dict[str, Any]:
    if sys.version_info[:2] != (3, 12):
        raise RuntimeError("Python 3.12 is required")
    staging_root = Path(args.staging_root).resolve()
    development_root = Path(args.development_root).resolve()
    escrow_root = Path(args.escrow_root).resolve()
    output_root = Path(args.output_root).resolve()
    if output_root.exists():
        raise FileExistsError(output_root)
    if not (staging_root / ".git").exists():
        raise ValueError("staging root is not a Git worktree")
    if (staging_root / ".git" / "index.lock").exists():
        raise RuntimeError("staging .git/index.lock exists; inspect the owning Git process before proceeding")

    bound = load_bound_escrow(escrow_root, args.expected_escrow_manifest_sha256)
    manifest = bound["manifest"]
    head = str(git_run(staging_root, "rev-parse", "HEAD")).strip()
    branch = str(git_run(staging_root, "branch", "--show-current")).strip()
    origin_head = str(git_run(staging_root, "rev-parse", f"origin/{branch}")).strip()
    if head != manifest["head"] or branch != manifest["branch"] or origin_head != head:
        raise ValueError("staging HEAD/branch/local-origin binding mismatch")
    if bound["overlay_manifest"]["head"] != head:
        raise ValueError("overlay plan baseline mismatch")
    verify_current_layers(staging_root, bound)
    verify_sources(development_root, bound["overlay_rows"])

    if not args.execute:
        value = {
            "schema": "dottalk.staging.gate5_execution_preflight.v1",
            "created_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "status": "PASS_REPORT_ONLY",
            "head": head,
            "escrow_manifest_sha256": args.expected_escrow_manifest_sha256,
            "dirty_files": len(bound["dirty_rows"]),
            "ignored_files": len(bound["ignored_rows"]),
            "overlay_files": len(bound["overlay_rows"]),
            "public_only_files": len(bound["public_only_rows"]),
            "staging_mutated": 0,
        }
        output_root.mkdir(parents=True, exist_ok=False)
        (output_root / "gate5_staging_preflight_manifest.json").write_text(
            json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        return value

    mutation_started = False
    try:
        git_run(staging_root, "fetch", "origin", branch)
        fetched_head = str(git_run(staging_root, "rev-parse", f"origin/{branch}")).strip()
        if fetched_head != head:
            raise ValueError(f"origin/{branch} moved: expected {head}, found {fetched_head}")
        mutation_started = True
        reset_to_baseline(staging_root, branch, head)
        restore_rows(staging_root, bound["dirty_root"], bound["dirty_rows"])
        restore_rows(staging_root, bound["ignored_root"], bound["ignored_rows"])
        apply_overlay(staging_root, development_root, bound["overlay_rows"])
        final = verify_final(staging_root, development_root, bound)
    except Exception:
        if mutation_started:
            reset_to_baseline(staging_root, branch, head)
            restore_rows(staging_root, bound["dirty_root"], bound["dirty_rows"])
            restore_rows(staging_root, bound["ignored_root"], bound["ignored_rows"])
            verify_current_layers(staging_root, bound)
        raise

    value = {
        "schema": "dottalk.staging.gate5_recovery_bound_execution.v1",
        "created_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "status": "PASS_APPLIED_STAGING_ONLY",
        "head": head,
        "branch": branch,
        "escrow_manifest_sha256": args.expected_escrow_manifest_sha256,
        "overlay_plan_manifest_sha256": sha256_file(
            safe_path(escrow_root, manifest["artifacts"]["gate5_overlay_plan"], must_exist=True)
        ),
        "overlay_ledger_sha256": manifest["artifacts"]["gate5_overlay_ledger_sha256"],
        "final": final,
        "boundaries": {
            "git_staged_changes": 0,
            "commit_created": 0,
            "push_performed": 0,
            "website_mutated": 0,
        },
    }
    write_execution_record(output_root, value)
    return value


def parser() -> argparse.ArgumentParser:
    value = argparse.ArgumentParser(description="Recovery-bound exact Gate 5 staging rebuild; report-only unless --execute is supplied.")
    value.add_argument("--staging-root", required=True)
    value.add_argument("--development-root", required=True)
    value.add_argument("--escrow-root", required=True)
    value.add_argument("--expected-escrow-manifest-sha256", required=True)
    value.add_argument("--output-root", required=True)
    value.add_argument("--execute", action="store_true")
    return value


def main() -> int:
    value = run(parser().parse_args())
    final = value.get("final", {})
    print(
        f"status={value['status']} head={value['head']} "
        f"dirty={final.get('dirty_verified', value.get('dirty_files'))} "
        f"ignored={final.get('ignored', value.get('ignored_files'))} "
        f"overlay={final.get('overlay_verified', value.get('overlay_files'))} "
        f"staged={value.get('boundaries', {}).get('git_staged_changes', 0)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
