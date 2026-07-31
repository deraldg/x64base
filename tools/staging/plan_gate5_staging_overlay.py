from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any


SCHEMA = "dottalk.staging.gate5_selective_overlay_plan.v1"
DENY_RE = re.compile(
    r"(?i)(?:\.cdx\.d[\\/]|[\\/]lmdb[\\/]|[\\/]og[\\/]|\.exe$|"
    r"[\\/]backups?[\\/]|\.bak|\.save|\.before_mdo_|\.mdb$|"
    r"[\\/]zz_|[\\/]table\.cnx$|[\\/]table\.cdx$|mixed\.workspace)"
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _git(root: Path, *args: str, text: bool = True) -> str | bytes:
    result = subprocess.run(
        ["git", "-c", f"safe.directory={root.as_posix()}", "-C", str(root), *args],
        check=True,
        capture_output=True,
        text=text,
    )
    return result.stdout


def parse_delta_candidate(text: str) -> list[str]:
    entries: list[str] = []
    in_block = False
    for raw in text.splitlines():
        line = raw.strip()
        if line == "```text":
            if in_block:
                raise ValueError("nested text code fence")
            in_block = True
            continue
        if line == "```" and in_block:
            in_block = False
            continue
        if in_block and line and not line.startswith("#"):
            entries.append(line.replace("\\", "/"))
    if in_block:
        raise ValueError("unterminated text code fence")
    return entries


def expand_entry(repo_root: Path, entry: str) -> list[Path]:
    pure = PurePosixPath(entry)
    if pure.is_absolute() or ".." in pure.parts:
        raise ValueError(f"unsafe manifest entry: {entry}")
    exact = repo_root / Path(*pure.parts)
    if exact.is_file():
        return [exact]
    if exact.is_dir():
        return sorted(path for path in exact.rglob("*") if path.is_file())
    return sorted(path for path in repo_root.glob(entry) if path.is_file())


def git_blob_oid(value: bytes, object_format: str) -> str:
    header = f"blob {len(value)}\0".encode("ascii")
    if object_format == "sha1":
        return hashlib.sha1(header + value).hexdigest()  # noqa: S324 - Git object identity
    if object_format == "sha256":
        return hashlib.sha256(header + value).hexdigest()
    raise ValueError(f"unsupported Git object format: {object_format}")


def head_tree(staging_root: Path, head: str) -> dict[str, str]:
    raw = _git(staging_root, "ls-tree", "-r", "-z", head, text=False)
    assert isinstance(raw, bytes)
    result: dict[str, str] = {}
    for item in raw.split(b"\0"):
        if not item:
            continue
        metadata, raw_path = item.split(b"\t", 1)
        _mode, kind, oid = metadata.decode("ascii").split(" ")
        if kind == "blob":
            result[raw_path.decode("utf-8", errors="surrogateescape")] = oid
    return result


def read_preserved_paths(preservation_root: Path) -> tuple[dict[str, str], dict[str, Any]]:
    manifest_path = preservation_root / "preservation_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    if manifest.get("schema") != "dottalk.staging.dirty_worktree_preservation.v1":
        raise ValueError("unexpected preservation schema")
    ledger = preservation_root / str(manifest.get("file_manifest", ""))
    if not ledger.is_file() or sha256_file(ledger) != manifest.get("file_manifest_sha256"):
        raise ValueError("preservation file-manifest hash mismatch")
    with ledger.open("r", encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    if len(rows) != manifest.get("dirty_paths"):
        raise ValueError("preservation dirty-path count mismatch")
    return {row["path"]: row["sha256"] for row in rows}, manifest


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]) if rows else ["path", "action"])
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def build_plan(
    repo_root: Path,
    staging_root: Path,
    output_root: Path,
    delta_candidate: Path,
    expected_delta_sha256: str,
    preservation_root: Path,
    expected_head: str,
) -> dict[str, Any]:
    if sys.version_info[:2] != (3, 12):
        raise ValueError("plan_gate5_staging_overlay requires Python 3.12.x")
    repo_root = repo_root.resolve()
    staging_root = staging_root.resolve()
    output_root = output_root.resolve()
    delta_candidate = delta_candidate.resolve()
    preservation_root = preservation_root.resolve()
    try:
        output_root.relative_to(repo_root)
    except ValueError as exc:
        raise ValueError("output root must stay inside authoritative development") from exc
    if output_root.exists():
        raise ValueError(f"output root already exists: {output_root}")
    if sha256_file(delta_candidate) != expected_delta_sha256.upper():
        raise ValueError("delta-candidate hash mismatch")

    entries = parse_delta_candidate(delta_candidate.read_text(encoding="utf-8-sig"))
    if len(entries) != 20 or len(set(entries)) != 20:
        raise ValueError(f"expected 20 unique delta entries, observed {len(entries)}/{len(set(entries))}")
    current_manifest_lines = (repo_root / "PROMOTE.manifest").read_text(encoding="utf-8-sig").splitlines()
    missing_from_manifest = [entry for entry in entries if entry not in current_manifest_lines]
    if missing_from_manifest:
        raise ValueError("accepted delta entries missing from current PROMOTE.manifest")

    head = str(_git(staging_root, "rev-parse", "HEAD")).strip()
    branch = str(_git(staging_root, "branch", "--show-current")).strip()
    if head != expected_head:
        raise ValueError(f"staging HEAD drift: expected {expected_head}, observed {head}")
    preserved_paths, preservation = read_preserved_paths(preservation_root)
    if preservation.get("head") != head:
        raise ValueError("preservation package HEAD differs from overlay baseline")

    path_entries: dict[str, set[str]] = {}
    misses: list[str] = []
    for entry in entries:
        hits = expand_entry(repo_root, entry)
        if not hits:
            misses.append(entry)
            continue
        for path in hits:
            relative = path.relative_to(repo_root).as_posix()
            if DENY_RE.search(relative):
                continue
            path_entries.setdefault(relative, set()).add(entry)
    path_entries.setdefault("PROMOTE.manifest", set()).add("PROMOTE.manifest")
    if misses:
        raise ValueError("delta entries matched nothing: " + ", ".join(misses))
    leaks = [path for path in path_entries if DENY_RE.search(path)]
    if leaks:
        raise ValueError("deny-list leaks: " + ", ".join(leaks))

    object_format = str(_git(staging_root, "rev-parse", "--show-object-format")).strip()
    baseline = head_tree(staging_root, head)
    rows: list[dict[str, Any]] = []
    for relative in sorted(path_entries):
        source = repo_root / Path(*PurePosixPath(relative).parts)
        source_bytes = source.read_bytes()
        source_oid = git_blob_oid(source_bytes, object_format)
        baseline_oid = baseline.get(relative, "ABSENT")
        action = "UNCHANGED" if source_oid == baseline_oid else ("REPLACE" if baseline_oid != "ABSENT" else "CREATE")
        current = staging_root / Path(*PurePosixPath(relative).parts)
        current_hash = sha256_file(current) if current.is_file() else "ABSENT"
        rows.append(
            {
                "path": relative,
                "action_after_fresh": action,
                "bytes": len(source_bytes),
                "source_sha256": hashlib.sha256(source_bytes).hexdigest().upper(),
                "source_git_blob_oid": source_oid,
                "baseline_git_blob_oid": baseline_oid,
                "current_worktree_sha256": current_hash,
                "current_equals_source": int(current_hash == hashlib.sha256(source_bytes).hexdigest().upper()),
                "preserved_dirty_path": int(relative in preserved_paths),
                "manifest_entries": ";".join(sorted(path_entries[relative])),
            }
        )

    dirty_intersections = [row for row in rows if row["preserved_dirty_path"]]
    unrelated_dirty_intersections = [row for row in dirty_intersections if row["path"] != "PROMOTE.manifest"]
    if unrelated_dirty_intersections:
        raise ValueError(
            "selective Gate 5 overlay intersects unrelated preserved dirty paths: "
            + ", ".join(str(row["path"]) for row in unrelated_dirty_intersections)
        )

    output_root.mkdir(parents=True, exist_ok=False)
    ledger_path = output_root / "gate5_staging_overlay_ledger.csv"
    write_csv(ledger_path, rows)
    counts = {
        "planned_files": len(rows),
        "create": sum(row["action_after_fresh"] == "CREATE" for row in rows),
        "replace": sum(row["action_after_fresh"] == "REPLACE" for row in rows),
        "unchanged": sum(row["action_after_fresh"] == "UNCHANGED" for row in rows),
        "planned_bytes": sum(int(row["bytes"]) for row in rows),
        "delta_entries": len(entries),
        "deny_list_leaks": len(leaks),
        "dirty_path_intersections": len(dirty_intersections),
        "unrelated_dirty_path_intersections": len(unrelated_dirty_intersections),
        "findings": 0,
    }
    report_path = output_root / "GATE5_SELECTIVE_STAGING_OVERLAY_PLAN.md"
    report_path.write_text(
        "# Gate 5 Selective Staging Overlay Plan\n\n"
        "- Status: `PASS_PLAN_ONLY`\n"
        f"- Staging baseline: `{branch}` / `{head}`\n"
        f"- Reviewed manifest-delta entries: `{len(entries)}`\n"
        f"- Planned files: `{counts['planned_files']}`\n"
        f"- After-fresh actions: `{counts['create']}` create / `{counts['replace']}` replace / `{counts['unchanged']}` unchanged\n"
        f"- Planned bytes: `{counts['planned_bytes']}`\n"
        f"- Preserved dirty-path intersections: `{counts['dirty_path_intersections']}` (`PROMOTE.manifest` only)\n"
        "- Unrelated dirty-path intersections: `0`\n"
        "- Deny-list leaks/findings: `0` / `0`\n"
        "- `C:\\x64base` mutation: `0`\n\n"
        "## Apply boundary\n\n"
        "This plan is the reviewed Gate 5 delta plus `PROMOTE.manifest`, not the ordinary 559-file full overlay. "
        "Application requires separate authorization for a fresh reset of disposable staging and this exact ledger. "
        "It does not authorize Git staging, commit, push, or website work.\n",
        encoding="utf-8",
    )
    manifest_path = output_root / "gate5_staging_overlay_plan_manifest.json"
    manifest = {
        "schema": SCHEMA,
        "created_utc": utc_now(),
        "status": "PASS_PLAN_ONLY",
        "execute_authorized": 0,
        "repo_root": str(repo_root),
        "staging_root": str(staging_root),
        "branch": branch,
        "head": head,
        "git_object_format": object_format,
        "delta_candidate": delta_candidate.relative_to(repo_root).as_posix(),
        "delta_candidate_sha256": sha256_file(delta_candidate),
        "preservation_root": preservation_root.relative_to(repo_root).as_posix(),
        "preservation_manifest_sha256": sha256_file(preservation_root / "preservation_manifest.json"),
        "counts": counts,
        "findings": [],
        "artifacts": {
            "review": report_path.relative_to(repo_root).as_posix(),
            "review_sha256": sha256_file(report_path),
            "ledger": ledger_path.relative_to(repo_root).as_posix(),
            "ledger_sha256": sha256_file(ledger_path),
        },
        "boundaries": {
            "source_staging_mutated": 0,
            "git_index_mutated": 0,
            "commit_created": 0,
            "website_mutated": 0,
        },
    }
    write_json(manifest_path, manifest)
    return manifest


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build an exact report-only Gate 5 selective staging overlay plan.")
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--staging-root", required=True)
    parser.add_argument("--output-root", required=True)
    parser.add_argument("--delta-candidate", required=True)
    parser.add_argument("--expected-delta-sha256", required=True)
    parser.add_argument("--preservation-root", required=True)
    parser.add_argument("--expected-head", required=True)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    manifest = build_plan(
        Path(args.repo_root),
        Path(args.staging_root),
        Path(args.output_root),
        Path(args.delta_candidate),
        args.expected_delta_sha256,
        Path(args.preservation_root),
        args.expected_head,
    )
    counts = manifest["counts"]
    print(
        "gate5_staging_overlay_plan "
        f"files={counts['planned_files']} create={counts['create']} replace={counts['replace']} "
        f"unchanged={counts['unchanged']} unrelated_dirty_intersections=0 "
        "staging_mutated=0 status=PASS_PLAN_ONLY"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
