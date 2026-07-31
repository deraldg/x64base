from __future__ import annotations

import argparse
import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


HELP_FILES = (
    "cmd_args.dbf",
    "cmd_args.dbt",
    "commands.dbf",
    "commands.dbt",
    "help_artifacts.dbf",
    "help_artifacts.dbt",
    "help_line.dbf",
    "help_section.dbf",
    "help_topic.dbf",
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def file_record(path: Path, base: Path, family: str) -> dict[str, object]:
    return {
        "family": family,
        "path": path.relative_to(base).as_posix(),
        "bytes": path.stat().st_size,
        "sha256": sha256(path),
    }


def active_comments_files(repo: Path) -> list[dict[str, object]]:
    roots = (
        ("dbf", repo / "dottalkpp/data/comments"),
        ("index", repo / "dottalkpp/data/indexes/comments"),
    )
    rows: list[dict[str, object]] = []
    for family, root in roots:
        if not root.is_dir():
            raise FileNotFoundError(f"COMMENTS {family} root missing: {root}")
        for path in sorted(p for p in root.rglob("*") if p.is_file()):
            rows.append(file_record(path, root, family))

    lmdb_root = repo / "dottalkpp/data/lmdb/comments"
    if not lmdb_root.is_dir():
        raise FileNotFoundError(f"COMMENTS LMDB root missing: {lmdb_root}")
    active_dirs = sorted(
        path for path in lmdb_root.iterdir()
        if path.is_dir() and path.name.lower().endswith(".cdx.d")
    )
    if not active_dirs:
        raise RuntimeError(f"No active COMMENTS LMDB directories in {lmdb_root}")
    for active in active_dirs:
        for path in sorted(p for p in active.rglob("*") if p.is_file()):
            record = file_record(path, lmdb_root, "lmdb")
            rows.append(record)
    return rows


def help_records(live_root: Path, candidate_root: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for name in HELP_FILES:
        live = live_root / name
        candidate = candidate_root / name
        if not live.is_file():
            raise FileNotFoundError(f"live HELP file missing: {live}")
        if not candidate.is_file():
            raise FileNotFoundError(f"candidate HELP file missing: {candidate}")
        rows.append({
            "file": name,
            "live_bytes": live.stat().st_size,
            "live_sha256": sha256(live),
            "candidate_bytes": candidate.stat().st_size,
            "candidate_sha256": sha256(candidate),
        })
    return rows


def comment_candidate_records(candidate_root: Path, manifest_path: Path) -> list[dict[str, object]]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    rows: list[dict[str, object]] = []
    for name, expected in sorted(manifest["candidate_files"].items()):
        path = candidate_root / name
        if not path.is_file():
            raise FileNotFoundError(f"candidate COMMENTS file missing: {path}")
        actual = sha256(path)
        if actual != expected["sha256"]:
            raise RuntimeError(
                f"candidate COMMENTS hash mismatch for {name}: "
                f"manifest={expected['sha256']} actual={actual}"
            )
        rows.append({
            "file": name,
            "bytes": path.stat().st_size,
            "rows": expected["rows"],
            "sha256": actual,
        })
    return rows


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        raise RuntimeError(f"Refusing to write empty manifest: {path}")
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def build_preflight(repo: Path, run_root: Path, output_dir: Path) -> dict[str, object]:
    comments_package = run_root / "comments_reharvest/fullstack_20260722_contracts_v2"
    comments_candidate = comments_package / "candidate_source_comment_metadata_import_v2"
    comments_manifest = comments_package / "source_comment_reharvest_manifest_v1.json"
    help_candidate = run_root / "help_refresh_candidate/isolated_help_v2"

    comment_candidates = comment_candidate_records(comments_candidate, comments_manifest)
    comment_live = active_comments_files(repo)
    help = help_records(repo / "dottalkpp/data/help", help_candidate)

    output_dir.mkdir(parents=True, exist_ok=True)
    write_csv(output_dir / "comments_candidate_sha256_manifest_v1.csv", comment_candidates)
    write_csv(output_dir / "comments_live_sha256_manifest_v1.csv", comment_live)
    write_csv(output_dir / "help_live_candidate_sha256_manifest_v1.csv", help)

    payload: dict[str, object] = {
        "contract": "comments-help-promotion-preflight-v1",
        "run_id": run_root.name,
        "recorded_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "repo_root": str(repo),
        "comments": {
            "candidate_root": str(comments_candidate),
            "candidate_manifest": str(comments_manifest),
            "candidate_files": len(comment_candidates),
            "live_files": len(comment_live),
            "live_roots": {
                "dbf": str(repo / "dottalkpp/data/comments"),
                "index": str(repo / "dottalkpp/data/indexes/comments"),
                "lmdb": str(repo / "dottalkpp/data/lmdb/comments"),
            },
        },
        "help": {
            "candidate_root": str(help_candidate),
            "live_root": str(repo / "dottalkpp/data/help"),
            "files": len(help),
        },
        "live_mutation_authorized": False,
        "git_mutation_authorized": False,
        "website_mutation_authorized": False,
    }
    (output_dir / "comments_help_promotion_preflight_v1.json").write_text(
        json.dumps(payload, indent=2) + "\n",
        encoding="utf-8",
    )
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Bind current live COMMENTS and HELP state to reviewed candidates."
    )
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    payload = build_preflight(
        args.repo_root.resolve(),
        args.run_root.resolve(),
        args.output_dir.resolve(),
    )
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
