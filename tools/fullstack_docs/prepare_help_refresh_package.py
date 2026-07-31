from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
from pathlib import Path


DEFAULT_RUN = Path("docs/maintenance/lanes/full_stack_documentation/runs/DOCFLUSH-20260716-001")


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Prepare a report-only guarded HELP refresh package.")
    ap.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[2])
    ap.add_argument("--output-dir", type=Path, default=DEFAULT_RUN / "help_refresh_package")
    return ap.parse_args()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def git(repo: Path, *args: str) -> str:
    cp = subprocess.run(["git", "-C", str(repo), *args], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    return cp.stdout.decode("utf-8", errors="replace").strip()


def write_csv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields, quoting=csv.QUOTE_ALL)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    args = parse_args()
    repo = args.repo_root.resolve()
    output = args.output_dir if args.output_dir.is_absolute() else repo / args.output_dir
    help_root = repo / "dottalkpp/data/help"
    input_paths = [
        repo / "include/dotref.hpp",
        repo / "include/foxref.hpp",
        repo / "include/edref.hpp",
        repo / "src/cli/shell_commands.cpp",
        repo / "src/help/helpdata_messages.cpp",
        repo / "src/help/helpdata_messages.hpp",
        repo / "docs/maintenance/lanes/full_stack_documentation/runs/DOCFLUSH-20260716-001/comments_reharvest/post_messaging_20260716/source_comment_reharvest_manifest_v1.json",
        repo / "docs/maintenance/lanes/full_stack_documentation/runs/DOCFLUSH-20260716-001/reference_inventory/fullstack_reference_identity_manifest_v1.json",
        repo / "docs/maintenance/lanes/full_stack_documentation/runs/DOCFLUSH-20260716-001/runtime_baseline/fullstack_pre_refresh_runtime_manifest_v1.json",
    ]
    input_rows = []
    for path in input_paths:
        rel = path.relative_to(repo).as_posix()
        status = git(repo, "status", "--short", "--", rel)
        input_rows.append({
            "path": rel,
            "exists": str(path.exists()),
            "bytes": str(path.stat().st_size if path.exists() else 0),
            "sha256": sha256(path) if path.exists() else "",
            "git_status": status,
        })
    write_csv(output / "help_refresh_input_manifest_v1.csv", input_rows, list(input_rows[0]))

    protected_rows = []
    for path in sorted(p for p in help_root.iterdir() if p.is_file()):
        protected_rows.append({
            "path": path.relative_to(repo).as_posix(),
            "extension": path.suffix.lower(),
            "bytes": str(path.stat().st_size),
            "last_write_ns": str(path.stat().st_mtime_ns),
            "sha256": sha256(path),
            "backup_required_before_build": "True",
        })
    protected_path = output / "pre_refresh_help_file_manifest_v1.csv"
    write_csv(protected_path, protected_rows, list(protected_rows[0]))

    dotref_dirty = bool(git(repo, "status", "--short", "--", "include/dotref.hpp"))
    current_inputs_dirty = any(
        bool(git(repo, "status", "--short", "--", path))
        for path in ("src/cli/shell_commands.cpp", "src/help/helpdata_messages.cpp", "src/help/helpdata_messages.hpp")
    )
    payload = {
        "contract": "guarded-help-refresh-package-v1",
        "mutation_authorized": False,
        "help_root": str(help_root),
        "protected_file_count": len(protected_rows),
        "protected_manifest_sha256": sha256(protected_path),
        "current_help_build_required": current_inputs_dirty,
        "current_help_build_reason": "Messaging/help source inputs are dirty after the 2026-07-07 HELP artifacts and the current usage-contract snapshot has advanced.",
        "legacy_build_trigger": "REVIEW_REQUIRED" if not dotref_dirty else "DOTREF_DIRTY",
        "legacy_build_reason": "DOTREF is not currently dirty; timestamps alone do not prove whether it diverged from the last legacy build.",
        "proposed_current_command": "CMDHELP BUILD . D:\\code\\ccode\\src",
        "proposed_legacy_command_if_trigger_confirmed": "CMDHELP BUILD LEGACY",
        "pre_refresh_runtime_findings": {
            "cmdhelp_topics": 473,
            "cmdhelp_line_rows": 10846,
            "artifact_rows": 6926,
            "orphan_cmdkey_rows": 461,
            "compact_set_canonicalization_errors": 9,
            "reflection_structural_status": "PASS",
        },
        "required_before_execution": [
            "explicit maintainer authorization",
            "copy every pre-refresh HELP file named by the protected manifest into a dated backup directory",
            "hash-verify the backup",
            "resolve the conditional legacy-build trigger",
            "run approved build commands only",
            "capture post-build file and row-count deltas",
            "rerun CMDHELPCHK reflection, artifacts, and legacy checks",
        ],
        "rollback": "Restore the complete dated HELP backup, then rerun the same read-only runtime transcript.",
    }
    output.mkdir(parents=True, exist_ok=True)
    (output / "help_refresh_package_manifest_v1.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    md = [
        "# Guarded HELP Refresh Package v1", "",
        "Status: PROPOSED / MUTATION_NOT_AUTHORIZED", "",
        "## Why a current HELP rebuild is proposed", "",
        "The live HELP family was last written on 2026-07-07. Messaging/help source inputs are currently modified, the post-messaging usage-contract harvest is newer, and the pre-refresh artifact check reports 461 orphan command keys plus nine compact SET canonicalization errors.", "",
        "## Conditional command order", "", "```text",
        "if reviewed evidence confirms include/dotref.hpp changed since the legacy build:",
        "    CMDHELP BUILD LEGACY",
        "CMDHELP BUILD . D:\\code\\ccode\\src", "```", "",
        "DOTREF is not currently dirty, so the legacy trigger remains `REVIEW_REQUIRED`; file timestamps are not sufficient evidence.", "",
        "## Required execution controls", "",
    ]
    md += [f"- {item}" for item in payload["required_before_execution"]]
    md += ["", "No HELP, DBF, DBT, index, LMDB, source, COMMENTS, manual, or publication file was changed while preparing this package."]
    (output / "HELP_REFRESH_MUTATION_PACKAGE_V1.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
