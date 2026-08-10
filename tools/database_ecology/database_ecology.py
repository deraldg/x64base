#!/usr/bin/env python3
"""Read-only database ecology census and reversible sidecar intake planning.

The scanner identifies database carriers by content or well-known companion
names. It never opens DBF or LMDB data and opens no SQLite connection. Sidecar
planning hashes candidate files but never moves or deletes them.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Iterable


SQLITE_HEADER = b"SQLite format 3\x00"
SIDECAR_SUFFIXES = (".ddl.json", ".indexes.json", ".load.json", ".schema.copy.json")
DEFINITION_SUFFIXES = {
    "dtschema_files": ".dtschema",
    "schema_json_files": ".schema.json",
    "ddl_json_files": ".ddl.json",
    "index_sidecar_json_files": ".indexes.json",
    "load_receipt_json_files": ".load.json",
    "sql_files": ".sql",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def normalized(path: Path) -> str:
    return path.as_posix()


def relative_to_or_absolute(path: Path, root: Path) -> str:
    try:
        return normalized(path.resolve().relative_to(root.resolve()))
    except ValueError:
        return normalized(path.resolve())


def iter_files(root: Path) -> Iterable[Path]:
    if not root.exists():
        return
    for current, directories, names in os.walk(root):
        directories[:] = sorted(name for name in directories if name != ".git")
        base = Path(current)
        for name in sorted(names):
            yield base / name


def git_tracked_paths(repo_root: Path) -> set[str]:
    if not (repo_root / ".git").exists():
        return set()
    result = subprocess.run(
        ["git", "-C", str(repo_root), "ls-files", "-z"],
        check=True,
        capture_output=True,
    )
    return {
        item.decode("utf-8", errors="surrogateescape").replace("\\", "/").lower()
        for item in result.stdout.split(b"\0")
        if item
    }


def git_ignored_paths(repo_root: Path, paths: list[str]) -> set[str]:
    if not paths or not (repo_root / ".git").exists():
        return set()
    payload = b"\0".join(path.encode("utf-8") for path in paths) + b"\0"
    result = subprocess.run(
        ["git", "-C", str(repo_root), "check-ignore", "-z", "--stdin"],
        input=payload,
        capture_output=True,
        check=False,
    )
    if result.returncode not in {0, 1}:
        raise RuntimeError(result.stderr.decode("utf-8", errors="replace"))
    return {
        item.decode("utf-8", errors="surrogateescape").replace("\\", "/").lower()
        for item in result.stdout.split(b"\0")
        if item
    }


def is_sqlite(path: Path) -> bool:
    try:
        with path.open("rb") as handle:
            return handle.read(len(SQLITE_HEADER)) == SQLITE_HEADER
    except OSError:
        return False


def colocated_dbf_exists(path: Path, stem: str) -> bool:
    expected = f"{stem}.dbf".lower()
    try:
        return any(child.is_file() and child.name.lower() == expected for child in path.parent.iterdir())
    except OSError:
        return False


def sidecar_stem(name: str) -> str | None:
    lower = name.lower()
    for suffix in SIDECAR_SUFFIXES:
        if lower.endswith(suffix):
            return name[: -len(suffix)]
    return None


def cascade_duplicate_state(repo_root: Path) -> dict[str, Any]:
    dbf_root = repo_root / "dottalkpp" / "data" / "dbf"
    # System-bundle layout (owner ruling 2026-08-10): the canonical mirror is
    # split -- DBFs under systems/cascade_erp/dbf, generated JSON sidecars
    # under systems/cascade_erp/meta. A legacy stray is paired against
    # whichever half owns its suffix.
    system_root = repo_root / "dottalkpp" / "data" / "systems" / "cascade_erp"
    legacy = sorted(path for path in dbf_root.glob("CASCADE_*") if path.is_file())
    state: dict[str, Any] = {
        "legacy_root_artifacts": len(legacy),
        "paired_with_canonical": 0,
        "byte_equal": 0,
        "load_timestamp_equivalent": 0,
        "divergent": [],
        "missing_canonical": [],
    }
    for source in legacy:
        half = "meta" if source.name.lower().endswith(".json") else "dbf"
        target = system_root / half / source.name
        if not target.exists():
            state["missing_canonical"].append(relative_to_or_absolute(source, repo_root))
            continue
        state["paired_with_canonical"] += 1
        if sha256(source) == sha256(target):
            state["byte_equal"] += 1
            continue
        if source.name.lower().endswith(".load.json"):
            try:
                left = json.loads(source.read_text(encoding="utf-8"))
                right = json.loads(target.read_text(encoding="utf-8"))
                for document in (left, right):
                    for key in ("finished", "finished_utc", "completed", "completed_at"):
                        document.pop(key, None)
                if left == right:
                    state["load_timestamp_equivalent"] += 1
                    continue
            except (OSError, ValueError, AttributeError):
                pass
        state["divergent"].append(relative_to_or_absolute(source, repo_root))
    return state


def scan_roots(repo_root: Path, roots: list[Path]) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    tracked = git_tracked_paths(repo_root)
    extension_counts: Counter[str] = Counter()
    definition_counts: Counter[str] = Counter()
    files_by_kind: dict[str, list[Path]] = {
        "dbf": [], "cdx": [], "cnx": [], "dbt": [], "fpt": [], "sqlite": [], "lmdb": []
    }
    root_rows: list[dict[str, Any]] = []
    unreadable: list[str] = []

    for root in roots:
        root = root.resolve()
        count = 0
        for path in iter_files(root):
            count += 1
            lower = path.name.lower()
            suffix = path.suffix.lower()
            extension_counts[suffix] += 1
            for key, ending in DEFINITION_SUFFIXES.items():
                if lower.endswith(ending):
                    definition_counts[key] += 1
            if suffix in {".dbf", ".cdx", ".cnx", ".dbt", ".fpt"}:
                files_by_kind[suffix[1:]].append(path)
            if lower == "data.mdb" and (path.parent / "lock.mdb").exists():
                files_by_kind["lmdb"].append(path.parent)
            try:
                if is_sqlite(path):
                    files_by_kind["sqlite"].append(path)
            except OSError:
                unreadable.append(normalized(path))
        root_rows.append({"path": normalized(root), "files_scanned": count})

    def tracked_count(paths: list[Path]) -> int:
        return sum(
            1
            for path in paths
            if relative_to_or_absolute(path, repo_root).lower() in tracked
        )

    sqlite_incidental = [
        path for path in files_by_kind["sqlite"]
        if relative_to_or_absolute(path, repo_root).lower().startswith(".tmp/edge-manual-render/")
    ]
    dbf_hashes = {sha256(path) for path in files_by_kind["dbf"]}
    memo_orphans = [
        relative_to_or_absolute(path, repo_root)
        for kind in ("dbt", "fpt")
        for path in files_by_kind[kind]
        if not colocated_dbf_exists(path, path.stem)
    ]
    sidecar_orphans = []
    for root in roots:
        for path in iter_files(root.resolve()):
            stem = sidecar_stem(path.name)
            if stem is not None and not colocated_dbf_exists(path, stem):
                sidecar_orphans.append(relative_to_or_absolute(path, repo_root))
    lmdb_data_without_lock = []
    lmdb_lock_without_data = []
    for root in roots:
        for path in iter_files(root.resolve()):
            if path.name.lower() == "data.mdb" and not (path.parent / "lock.mdb").exists():
                lmdb_data_without_lock.append(relative_to_or_absolute(path, repo_root))
            if path.name.lower() == "lock.mdb" and not (path.parent / "data.mdb").exists():
                lmdb_lock_without_data.append(relative_to_or_absolute(path, repo_root))

    primary = {
        "dbf_tables": len(files_by_kind["dbf"]),
        "dbf_content_distinct_sha256": len(dbf_hashes),
        "lmdb_environments": len(files_by_kind["lmdb"]),
        "sqlite_files_by_signature": len(files_by_kind["sqlite"]),
        "sqlite_ecology_files": len(files_by_kind["sqlite"]) - len(sqlite_incidental),
        "sqlite_incidental_browser_profile_files": len(sqlite_incidental),
    }
    companions = {
        "lmdb_lock_files": len(files_by_kind["lmdb"]),
        "cdx_containers": len(files_by_kind["cdx"]),
        "cnx_containers": len(files_by_kind["cnx"]),
        "dbt_memo_files": len(files_by_kind["dbt"]),
        "fpt_memo_files": len(files_by_kind["fpt"]),
    }
    visibility = {}
    for kind in ("dbf", "sqlite", "lmdb"):
        visible = tracked_count(files_by_kind[kind])
        label = "lmdb_environments" if kind == "lmdb" else kind
        visibility[f"{label}_tracked"] = visible
        visibility[f"{label}_untracked"] = len(files_by_kind[kind]) - visible

    return {
        "schema": "dottalk-database-ecology-scan-v1",
        "roots": root_rows,
        "unreadable": sorted(unreadable),
        "physical_census": {
            "primary_stores": primary,
            "companions": companions,
            "definitions_and_rebuild_inputs": dict(sorted(definition_counts.items())),
            "git_visibility": visibility,
        },
        "integrity_findings": {
            "memo_companions_without_colocated_dbf": sorted(memo_orphans),
            "generated_sidecars_without_colocated_dbf": sorted(sidecar_orphans),
            "lmdb_data_without_lock_peer": sorted(lmdb_data_without_lock),
            "lmdb_lock_without_data_peer": sorted(lmdb_lock_without_data),
        },
        "cascade_legacy_root": cascade_duplicate_state(repo_root),
    }


def load_yaml(path: Path) -> dict[str, Any]:
    try:
        import yaml
    except ImportError as exc:
        raise RuntimeError("PyYAML is required for registry and sidecar-plan commands") from exc
    loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(loaded, dict):
        raise ValueError(f"registry root must be a mapping: {path}")
    return loaded


def compare_registry(scan: dict[str, Any], registry_path: Path) -> list[str]:
    registry = load_yaml(registry_path)["database_ecology"]["physical_census"]
    findings: list[str] = []
    for section in (
        "primary_stores", "companions", "definitions_and_rebuild_inputs", "git_visibility"
    ):
        expected = registry.get(section, {})
        observed = scan["physical_census"].get(section, {})
        for key, value in expected.items():
            if key in observed and observed[key] != value:
                findings.append(f"{section}.{key}: registry={value} observed={observed[key]}")
    integrity_expected = load_yaml(registry_path)["database_ecology"].get("integrity_findings", {})
    for key, expected in integrity_expected.items():
        observed = len(scan["integrity_findings"].get(key, []))
        if observed != expected:
            findings.append(f"integrity_findings.{key}: registry={expected} observed={observed}")
    return findings


def expand_candidate(repo_root: Path, candidate: dict[str, Any]) -> list[Path]:
    paths: list[Path] = []
    if "path" in candidate:
        paths.append(repo_root / str(candidate["path"]))
    for item in candidate.get("paths", []):
        paths.append(repo_root / str(item))
    files: list[Path] = []
    for path in paths:
        if path.is_dir():
            files.extend(iter_files(path))
        elif path.is_file():
            files.append(path)
    if "path_glob" in candidate:
        # A glob denotes artifact files. On case-insensitive filesystems the
        # CASCADE_* pattern also matches the canonical cascade_erp directory;
        # never recurse into a directory reached only through a file glob.
        files.extend(path for path in repo_root.glob(str(candidate["path_glob"])) if path.is_file())
    return sorted(set(path.resolve() for path in files))


def sidecar_rows(
    repo_root: Path, registry_path: Path, batch_id: str, sidecar_root: Path
) -> list[dict[str, Any]]:
    registry = load_yaml(registry_path)["database_ecology"]
    tracked = git_tracked_paths(repo_root)
    candidates = [
        item for item in registry.get("orphan_review_queue", [])
        if str(item.get("id", "")).startswith("orphan.") and item.get("orphan", True)
    ]
    expanded = [(candidate, expand_candidate(repo_root, candidate)) for candidate in candidates]
    relative_paths = [
        relative_to_or_absolute(path, repo_root)
        for _, paths in expanded
        for path in paths
    ]
    ignored = git_ignored_paths(repo_root, relative_paths)
    rows: list[dict[str, Any]] = []
    for candidate, paths in expanded:
        for path in paths:
            relative = relative_to_or_absolute(path, repo_root)
            is_tracked = relative.lower() in tracked
            rows.append(
                {
                    "BATCH_ID": batch_id,
                    "ORPHAN_ID": candidate["id"],
                    "CLASSIFICATION": candidate.get("classification", "review-needed"),
                    "REVIEW_STATE": "candidate_not_approved",
                    "SOURCE_RELATIVE": relative,
                    "SOURCE_BYTES": path.stat().st_size,
                    "SOURCE_SHA256": sha256(path),
                    "GIT_TRACKED": int(is_tracked),
                    "GIT_IGNORED": int(relative.lower() in ignored),
                    "ORDINARY_INTAKE_ELIGIBLE": int(not is_tracked),
                    "PROPOSED_DESTINATION": normalized(
                        sidecar_root / "holding" / batch_id / Path(relative)
                    ),
                    "DISPOSITION": candidate.get("disposition", "review_before_intake"),
                }
            )
    return rows


def write_csv(rows: list[dict[str, Any]], output: Path | None) -> None:
    fields = [
        "BATCH_ID", "ORPHAN_ID", "CLASSIFICATION", "REVIEW_STATE",
        "SOURCE_RELATIVE", "SOURCE_BYTES", "SOURCE_SHA256", "GIT_TRACKED",
        "GIT_IGNORED", "ORDINARY_INTAKE_ELIGIBLE", "PROPOSED_DESTINATION", "DISPOSITION",
    ]
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    if output is None:
        sys.stdout.write(buffer.getvalue())
    else:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(buffer.getvalue(), encoding="utf-8", newline="")


def verify_sidecar_plan(repo_root: Path, plan_path: Path) -> list[str]:
    findings: list[str] = []
    tracked = git_tracked_paths(repo_root)
    seen: set[str] = set()
    with plan_path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    for number, row in enumerate(rows, start=2):
        relative = row.get("SOURCE_RELATIVE", "").replace("\\", "/")
        if not relative or relative in seen:
            findings.append(f"row {number}: empty or duplicate source path {relative!r}")
            continue
        seen.add(relative)
        source = (repo_root / Path(relative)).resolve()
        try:
            source.relative_to(repo_root.resolve())
        except ValueError:
            findings.append(f"row {number}: source escapes repository: {relative}")
            continue
        if not source.is_file():
            findings.append(f"row {number}: source is missing: {relative}")
            continue
        actual_hash = sha256(source)
        if actual_hash != row.get("SOURCE_SHA256"):
            findings.append(f"row {number}: source hash drift: {relative}")
        if str(source.stat().st_size) != row.get("SOURCE_BYTES"):
            findings.append(f"row {number}: source size drift: {relative}")
        actually_tracked = relative.lower() in tracked
        if actually_tracked != (row.get("GIT_TRACKED") == "1"):
            findings.append(f"row {number}: Git tracking state drift: {relative}")
        if row.get("REVIEW_STATE") != "candidate_not_approved":
            findings.append(f"row {number}: plan is not review-gated: {relative}")
        destination = Path(row.get("PROPOSED_DESTINATION", ""))
        if destination.exists():
            findings.append(f"row {number}: proposed destination already exists: {destination}")
    return findings


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("scan", "check-registry", "cascade-preflight"):
        command = sub.add_parser(name)
        command.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[2])
        command.add_argument("--extra-root", type=Path, action="append", default=[])
        if name == "check-registry":
            command.add_argument(
                "--registry", type=Path,
                default=Path(__file__).resolve().parents[2] / "labtalk/registries/database_ecology.yaml",
            )
    plan = sub.add_parser("sidecar-plan")
    plan.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[2])
    plan.add_argument(
        "--registry", type=Path,
        default=Path(__file__).resolve().parents[2] / "labtalk/registries/database_ecology.yaml",
    )
    plan.add_argument("--batch-id", required=True)
    plan.add_argument("--sidecar-root", type=Path, required=True)
    plan.add_argument("--output", type=Path)
    verify = sub.add_parser("verify-sidecar-plan")
    verify.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[2])
    verify.add_argument("--plan", type=Path, required=True)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.command == "verify-sidecar-plan":
        findings = verify_sidecar_plan(args.repo_root.resolve(), args.plan)
        if findings:
            print("SIDECAR PLAN: FAILED")
            for finding in findings:
                print(f"  {finding}")
            return 1
        with args.plan.open(encoding="utf-8", newline="") as handle:
            count = sum(1 for _ in csv.DictReader(handle))
        print(f"SIDECAR PLAN: PASS -- {count} hash-bound candidate file(s), 0 moved")
        return 0
    if args.command == "sidecar-plan":
        rows = sidecar_rows(args.repo_root.resolve(), args.registry, args.batch_id, args.sidecar_root)
        write_csv(rows, args.output)
        print(f"sidecar-plan: {len(rows)} file row(s), 0 moved", file=sys.stderr)
        return 0
    if args.command == "cascade-preflight":
        state = cascade_duplicate_state(args.repo_root.resolve())
        if state["legacy_root_artifacts"]:
            print(
                "CASCADE PREFLIGHT: BLOCKED -- "
                f"{state['legacy_root_artifacts']} legacy root artifact(s); "
                "review the database ecology sidecar plan before another mirror run",
                file=sys.stderr,
            )
            return 2
        print("CASCADE PREFLIGHT: PASS -- no legacy root artifacts")
        return 0
    roots = [args.repo_root, *args.extra_root]
    scan = scan_roots(args.repo_root, roots)
    if args.command == "check-registry":
        findings = compare_registry(scan, args.registry)
        if findings:
            print("DATABASE ECOLOGY REGISTRY: DRIFT")
            for finding in findings:
                print(f"  {finding}")
            return 1
        print("DATABASE ECOLOGY REGISTRY: PASS")
        return 0
    print(json.dumps(scan, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
