from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
from collections import Counter
from pathlib import Path

from upsert_source_comment_contract import parse_header_contract, read_csv_rows, write_csv_rows


DEFAULT_RUN = Path("docs/maintenance/lanes/full_stack_documentation/runs/DOCFLUSH-20260716-001")


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Build an isolated candidate source-comment metadata package.")
    ap.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[2])
    ap.add_argument("--queue", type=Path, default=DEFAULT_RUN / "comments_audit/source_comment_escrow_review_queue_v1.csv")
    ap.add_argument(
        "--input-dir",
        type=Path,
        default=Path("dottalkpp/docs/generated/staging/source_comment_metadata_import_v1"),
    )
    ap.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_RUN / "comments_audit/candidate_source_comment_metadata_import_v1",
    )
    ap.add_argument("--updated", default="20260716")
    return ap.parse_args()


def resolve(repo: Path, path: Path) -> Path:
    return path if path.is_absolute() else repo / path


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def file_record(path: Path) -> dict[str, object]:
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        count = sum(1 for _ in csv.DictReader(fh))
    return {"bytes": path.stat().st_size, "rows": count, "sha256": sha256(path)}


def main() -> int:
    args = parse_args()
    repo = args.repo_root.resolve()
    queue_path = resolve(repo, args.queue)
    input_dir = resolve(repo, args.input_dir)
    output_dir = resolve(repo, args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    input_files = sorted(input_dir.glob("*.csv"))
    if not input_files:
        raise RuntimeError(f"No source import CSVs found in {input_dir}")
    input_manifest = {path.name: file_record(path) for path in input_files}
    for path in input_files:
        shutil.copy2(path, output_dir / path.name)

    with queue_path.open("r", encoding="utf-8-sig", newline="") as fh:
        p1 = [row for row in csv.DictReader(fh) if row["priority"] == "P1"]

    input_srcfile_rows, _ = read_csv_rows(input_dir / "SRCFILE_IMPORT.csv")
    known_paths = {row["RELPATH"] for row in input_srcfile_rows}
    reviews: list[dict[str, str]] = []
    contract_deltas: list[dict[str, str]] = []
    for row in p1:
        rel = row["path"]
        source = repo / rel
        usage = row["current_usage_present"] == "1"
        selected = row["status"] in {"FILE_DRIFT_COMMENT_CHANGED", "NEW_CURRENT"}
        action = "HASH_REFRESH_ONLY"
        reason = "Existing metadata contract retained; current whole-file hash refreshed when present."
        if not source.exists():
            action = "DEFER_MISSING_CURRENT"
            reason = "Candidate does not delete or restore a missing path without review."
        elif selected and not usage:
            action = "DEFER_NON_USAGE_CONTRACT"
            reason = "Contract markers exist, but the established upsert schema requires @dottalk.usage v1."
        elif selected and usage:
            try:
                parse_header_contract(repo, source)
            except (OSError, UnicodeError, RuntimeError) as exc:
                action = "DEFER_PARSE_ERROR"
                reason = str(exc)
            else:
                contract = parse_header_contract(repo, source)
                contract_deltas.append({
                    "path": contract.relpath,
                    "source_sha256": contract.file_sha256,
                    "owner": contract.owner,
                    "command": contract.command,
                    "header_lines": str(len(contract.header_lines)),
                    "usage_start_ord": str(contract.usage_start_ord),
                    "first_code_line": str(contract.first_code_line),
                    "existing_srcfile_row": "1" if rel in known_paths else "0",
                })
                if rel in known_paths:
                    action = "DEFER_FULL_COMMENT_REHARVEST"
                    reason = "Header delta captured; existing metadata is preserved until a full-comment harvester can replace the whole file slice safely."
                else:
                    action = "DEFER_NEW_FILE_FULL_COMMENT_HARVEST"
                    reason = "Header delta captured; new SRC* rows require a full-comment harvester, not a header-only insertion."
        reviews.append({
            "priority": "P1",
            "path": rel,
            "drift_status": row["status"],
            "candidate_action": action,
            "reason": reason,
        })

    srcfile_path = output_dir / "SRCFILE_IMPORT.csv"
    srcfile_rows, srcfile_fields = read_csv_rows(srcfile_path)
    hashes_populated = 0
    hashes_unresolved = 0
    for row in srcfile_rows:
        source = repo / row["RELPATH"]
        if source.is_file():
            row["HASH"] = sha256(source)
            hashes_populated += 1
        else:
            row["HASH"] = ""
            hashes_unresolved += 1
    write_csv_rows(srcfile_path, srcfile_fields, srcfile_rows)

    delta_path = output_dir / "source_comment_usage_contract_delta_v1.csv"
    delta_fields = list(contract_deltas[0]) if contract_deltas else [
        "path", "source_sha256", "owner", "command", "header_lines", "usage_start_ord", "first_code_line", "existing_srcfile_row"
    ]
    with delta_path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=delta_fields, quoting=csv.QUOTE_ALL)
        writer.writeheader()
        writer.writerows(contract_deltas)

    review_path = output_dir / "source_comment_candidate_review_v1.csv"
    review_fields = list(reviews[0]) if reviews else []
    with review_path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=review_fields, quoting=csv.QUOTE_ALL)
        writer.writeheader()
        writer.writerows(reviews)

    output_manifest = {
        path.name: file_record(path)
        for path in sorted(output_dir.glob("*.csv"))
        if path.name not in {review_path.name, delta_path.name}
    }
    action_counts = Counter(row["candidate_action"] for row in reviews)
    unchanged_policy = {}
    for name in ("SRCALIAS_IMPORT.csv", "SRCDISP_IMPORT.csv"):
        unchanged_policy[name] = {
            "input_sha256": input_manifest[name]["sha256"],
            "candidate_sha256": output_manifest[name]["sha256"],
            "unchanged": input_manifest[name]["sha256"] == output_manifest[name]["sha256"],
        }
    preserved_tables = {
        name: input_manifest[name]["sha256"] == output_manifest[name]["sha256"]
        for name in input_manifest
        if name != "SRCFILE_IMPORT.csv"
    }
    payload = {
        "contract": "source-comment-refresh-candidate-v1",
        "candidate_only": True,
        "live_dbf_mutation": False,
        "help_mutation": False,
        "source_mutation": False,
        "queue_sha256": sha256(queue_path),
        "updated_stamp": args.updated,
        "p1_rows": len(p1),
        "usage_contracts_upserted": 0,
        "usage_contract_deltas_captured": len(contract_deltas),
        "action_counts": dict(sorted(action_counts.items())),
        "srcfile_hashes_populated": hashes_populated,
        "srcfile_hashes_unresolved": hashes_unresolved,
        "input_files": input_manifest,
        "candidate_files": output_manifest,
        "policy_tables": unchanged_policy,
        "non_srcfile_tables_preserved": preserved_tables,
        "usage_contract_delta_sha256": sha256(delta_path),
        "metadata_preservation_policy": "All non-SRCFILE import tables are copied byte-for-byte; SRCFILE changes are limited to HASH population.",
    }
    manifest_path = output_dir / "source_comment_refresh_candidate_manifest_v1.json"
    manifest_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    summary = [
        "# Source Comment Refresh Candidate v1",
        "",
        "This directory is an isolated import candidate. It has not been loaded into live COMMENTS DBFs.",
        "",
        f"- P1 rows assessed: `{len(p1)}`",
        "- Usage contracts upserted: `0`",
        f"- Usage contract deltas captured: `{len(contract_deltas)}`",
        f"- SRCFILE hashes populated: `{hashes_populated}`",
        f"- SRCFILE hashes unresolved: `{hashes_unresolved}`",
        f"- SRCALIAS unchanged: `{unchanged_policy['SRCALIAS_IMPORT.csv']['unchanged']}`",
        f"- SRCDISP unchanged: `{unchanged_policy['SRCDISP_IMPORT.csv']['unchanged']}`",
        "",
        "## Candidate actions",
        "",
    ]
    summary += [f"- `{key}`: {value}" for key, value in sorted(action_counts.items())]
    (output_dir / "README.md").write_text("\n".join(summary) + "\n", encoding="utf-8")
    print(json.dumps({
        "p1_rows": len(p1),
        "usage_contracts_upserted": 0,
        "usage_contract_deltas_captured": len(contract_deltas),
        "actions": dict(sorted(action_counts.items())),
        "srcfile_hashes_populated": hashes_populated,
        "srcfile_hashes_unresolved": hashes_unresolved,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
