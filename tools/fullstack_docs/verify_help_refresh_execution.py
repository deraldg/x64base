from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import subprocess
from collections import Counter
from pathlib import Path


DEFAULT_RUN = Path("docs/maintenance/lanes/full_stack_documentation/runs/DOCFLUSH-20260716-001")


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Verify maintainer-executed legacy/current HELP builds.")
    ap.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[2])
    ap.add_argument("--pre-manifest", type=Path, default=DEFAULT_RUN / "help_refresh_package/pre_refresh_help_file_manifest_v1.csv")
    ap.add_argument("--transcript", type=Path, default=DEFAULT_RUN / "help_refresh_execution/maintainer_cmdhelp_build_legacy_then_current_transcript_v1.txt")
    ap.add_argument("--backup-dir", type=Path, default=DEFAULT_RUN / "help_refresh_execution/post_build_backup")
    ap.add_argument("--output-dir", type=Path, default=DEFAULT_RUN / "help_refresh_execution")
    ap.add_argument(
        "--post-runtime-manifest",
        type=Path,
        default=DEFAULT_RUN / "help_refresh_execution/post_runtime/fullstack_post_refresh_runtime_manifest_v1.json",
    )
    return ap.parse_args()


def resolve(repo: Path, path: Path) -> Path:
    return path if path.is_absolute() else repo / path


def sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def sha(path: Path) -> str:
    return sha_bytes(path.read_bytes())


def git_head_bytes(repo: Path, relpath: str) -> bytes | None:
    cp = subprocess.run(["git", "-C", str(repo), "show", f"HEAD:{relpath}"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return cp.stdout if cp.returncode == 0 else None


def write_csv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields, quoting=csv.QUOTE_ALL)
        writer.writeheader()
        writer.writerows(rows)


def num(pattern: str, text: str) -> int:
    match = re.search(pattern, text, re.MULTILINE)
    return int(match.group(1).replace(",", "")) if match else 0


def main() -> int:
    args = parse_args()
    repo = args.repo_root.resolve()
    pre_path = resolve(repo, args.pre_manifest)
    transcript = resolve(repo, args.transcript)
    backup_dir = resolve(repo, args.backup_dir)
    output = resolve(repo, args.output_dir)
    post_runtime_path = resolve(repo, args.post_runtime_manifest)
    with pre_path.open("r", encoding="utf-8-sig", newline="") as fh:
        pre_rows = list(csv.DictReader(fh))
    post_rows: list[dict[str, str]] = []
    for row in pre_rows:
        relpath = row["path"]
        current = repo / relpath
        backup = backup_dir / Path(relpath).name
        head_data = git_head_bytes(repo, relpath)
        current_hash = sha(current) if current.exists() else ""
        backup_hash = sha(backup) if backup.exists() else ""
        head_hash = sha_bytes(head_data) if head_data is not None else ""
        if not current.exists():
            delta = "MISSING_POST_BUILD"
        elif current_hash != row["sha256"]:
            delta = "CHANGED"
        else:
            delta = "UNCHANGED"
        post_rows.append({
            "path": relpath,
            "pre_sha256": row["sha256"],
            "post_sha256": current_hash,
            "post_bytes": str(current.stat().st_size if current.exists() else 0),
            "delta": delta,
            "pre_matches_head": str(head_hash == row["sha256"]),
            "head_sha256": head_hash,
            "post_backup_sha256": backup_hash,
            "post_backup_verified": str(bool(backup_hash) and backup_hash == current_hash),
        })
    manifest_path = output / "post_refresh_help_file_manifest_v1.csv"
    write_csv(manifest_path, post_rows, list(post_rows[0]))
    text = transcript.read_text(encoding="utf-8-sig", errors="replace")
    counts = Counter(row["delta"] for row in post_rows)
    post_runtime = json.loads(post_runtime_path.read_text()) if post_runtime_path.exists() else {}
    post_validated = post_runtime.get("runtime_exit") == 0 and post_runtime.get("reflection_structural_status") == "PASS"
    payload = {
        "contract": "help-refresh-execution-verification-v1",
        "execution_origin": "maintainer-provided transcript",
        "transcript_sha256": sha(transcript),
        "sequence_confirmed": text.find("CMDHELP BUILD LEGACY") < text.find("CMDHELP BUILD . D:\\code\\ccode\\src"),
        "legacy_command_rows": num(r"CMDHELP LEGACY wrote:\s*([\d,]+) command rows", text),
        "legacy_arg_rows": num(r"CMDHELP LEGACY wrote:\s*[\d,]+ command rows,\s*([\d,]+) arg rows", text),
        "current_usage_rows": num(r"Usage contracts mined directly:\s*([\d,]+) row", text),
        "current_usage_files": num(r"Usage contracts mined directly:\s*[\d,]+ row\(s\) from\s*([\d,]+) file", text),
        "current_line_rows": num(r"^\s*line rows\s*:\s*([\d,]+)$", text[text.find("CMDHELP BUILD . D:\\code\\ccode\\src"):]),
        "current_topics": num(r"^\s*topics\s*:\s*([\d,]+)$", text[text.find("CMDHELP BUILD . D:\\code\\ccode\\src"):]),
        "file_delta_counts": dict(sorted(counts.items())),
        "pre_files_recoverable_from_head": sum(row["pre_matches_head"] == "True" for row in post_rows),
        "post_backup_verified_files": sum(row["post_backup_verified"] == "True" for row in post_rows),
        "post_manifest_sha256": sha(manifest_path),
        "post_runtime_validated": post_validated,
        "post_runtime_manifest_sha256": sha(post_runtime_path) if post_runtime_path.exists() else "",
    }
    output.mkdir(parents=True, exist_ok=True)
    (output / "help_refresh_execution_manifest_v1.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    md = [
        "# HELP Refresh Execution Verification v1", "",
        f"Status: BUILDS_EXECUTED_BY_MAINTAINER / {'READBACK_VALIDATED' if post_validated else 'READBACK_PENDING'}", "",
        f"- Sequence legacy then current: `{payload['sequence_confirmed']}`",
        f"- Legacy commands/args: `{payload['legacy_command_rows']}/{payload['legacy_arg_rows']}`",
        f"- Current usage rows/files: `{payload['current_usage_rows']}/{payload['current_usage_files']}`",
        f"- Current line rows/topics: `{payload['current_line_rows']}/{payload['current_topics']}`",
        f"- Changed protected files: `{counts['CHANGED']}`",
        f"- Unchanged protected files: `{counts['UNCHANGED']}`",
        f"- Pre-build files recoverable from HEAD: `{payload['pre_files_recoverable_from_head']}/{len(post_rows)}`",
        f"- Post-build backup verified: `{payload['post_backup_verified_files']}/{len(post_rows)}`",
        f"- Post-build runtime validated: `{post_validated}`",
    ]
    (output / "README.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
