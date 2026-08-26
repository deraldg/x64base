#!/usr/bin/env python3
"""Build a hash-bound, plan-only canonical HELP/META harvest promotion package."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from check_help_meta_harvest_freshness import audit_workspace  # noqa: E402
from compare_help_meta_harvest import REQUIRED_FILES  # noqa: E402


MANIFEST_NAME = "HELP_META_EXPORT_MANIFEST_v0.csv"
PACKAGE_FILES = tuple(REQUIRED_FILES) + (MANIFEST_NAME,)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def repo_relative(root: Path, path: Path) -> str:
    resolved_root = root.resolve()
    resolved = path.resolve()
    try:
        relative = resolved.relative_to(resolved_root)
    except ValueError as exc:
        raise ValueError(f"Path escapes repository root: {path}") from exc
    return str(relative).replace("\\", "/")


def write_ledger(path: Path, rows: list[dict[str, object]]) -> None:
    path.write_bytes((json.dumps(rows, indent=2) + "\n").encode("utf-8"))


def build_plan(
    repo_root: Path,
    candidate: Path,
    canonical: Path,
    output_dir: Path,
    run_id: str,
    observed_at_utc: str,
) -> dict[str, object]:
    root = repo_root.resolve()
    candidate = candidate.resolve()
    canonical = canonical.resolve()
    output_dir = output_dir.resolve()
    candidate_rel = repo_relative(root, candidate)
    canonical_rel = repo_relative(root, canonical)
    output_rel = repo_relative(root, output_dir)

    candidate_audit = audit_workspace(root, candidate)
    canonical_audit = audit_workspace(root, canonical)
    findings: list[str] = []
    if candidate_audit["status"] != "PASS":
        findings.append("CANDIDATE_NOT_CURRENT")

    inventory: list[dict[str, object]] = []
    mutation_rows: list[dict[str, object]] = []
    for name in PACKAGE_FILES:
        source = candidate / name
        target = canonical / name
        if not source.is_file():
            findings.append(f"CANDIDATE_MISSING:{name}")
            continue
        if not target.is_file():
            findings.append(f"CANONICAL_MISSING:{name}")
            continue
        before_hash = sha256(target)
        after_hash = sha256(source)
        changed = before_hash != after_hash
        inventory.append({
            "file_name": name,
            "candidate_sha256": after_hash,
            "canonical_sha256": before_hash,
            "candidate_bytes": source.stat().st_size,
            "canonical_bytes": target.stat().st_size,
            "action": "replace" if changed else "verify_noop",
        })
        if changed:
            mutation_rows.append({
                "ordinal": len(mutation_rows) + 1,
                "action": "replace",
                "target": f"{canonical_rel}/{name}",
                "candidate": f"{candidate_rel}/{name}",
                "before_sha256": before_hash,
                "after_sha256": after_hash,
                "before_bytes": target.stat().st_size,
                "after_bytes": source.stat().st_size,
                "backup_required": 1,
                "rollback_guard_sha256": after_hash,
            })

    if len(inventory) != len(PACKAGE_FILES):
        findings.append(
            f"PACKAGE_INCOMPLETE:{len(inventory)}/{len(PACKAGE_FILES)}"
        )

    status = "PASS_PLAN_ONLY" if not findings else "FAIL_PLAN_ONLY"
    output_dir.mkdir(parents=True, exist_ok=True)
    ledger_path = output_dir / "help_meta_harvest_mutation_ledger.json"
    write_ledger(ledger_path, mutation_rows)
    ledger_hash = sha256(ledger_path)

    backup_root = (
        "docs/manuals/developer/manualgen/backups/"
        f"help_meta_harvest_{run_id}/before"
    )
    plan = {
        "schema": "dottalk.fullstack.help_meta_harvest_promotion_plan.v1",
        "observed_at_utc": observed_at_utc,
        "run_id": run_id,
        "status": status,
        "plan_only": 1,
        "apply_available": 0,
        "mutation_authorized": 0,
        "canonical_files_mutated": 0,
        "publication_authority_claimed": 0,
        "candidate_workspace": candidate_rel,
        "canonical_workspace": canonical_rel,
        "output_workspace": output_rel,
        "proposed_backup_root": backup_root,
        "candidate_freshness_status": candidate_audit["status"],
        "canonical_freshness_status": canonical_audit["status"],
        "package_file_count": len(PACKAGE_FILES),
        "planned_mutation_rows": len(mutation_rows),
        "verified_noop_rows": len(inventory) - len(mutation_rows),
        "mutation_ledger": f"{output_rel}/{ledger_path.name}",
        "mutation_ledger_sha256": ledger_hash,
        "review": f"{output_rel}/HELP_META_HARVEST_PROMOTION_REVIEW.md",
        "authorization_required": 1,
        "findings": findings,
        "inventory": inventory,
        "required_apply_controls": [
            "new owner authorization bound to plan and ledger hashes",
            "recheck every before and candidate hash before writing",
            "copy every target byte-for-byte to the proposed backup root",
            "stage and hash every after byte before the first replacement",
            "use atomic same-directory replacements",
            "rollback every changed target if any apply or readback check fails",
            "rerun E5 freshness against the canonical workspace after apply",
        ],
        "rollback_contract": {
            "scope": "all planned mutation rows",
            "precondition": "each target still matches rollback_guard_sha256",
            "source": backup_root,
            "success_readback": "every restored target matches before_sha256",
        },
    }
    plan_path = output_dir / "help_meta_harvest_promotion_plan.json"
    plan_path.write_bytes((json.dumps(plan, indent=2) + "\n").encode("utf-8"))
    plan_hash = sha256(plan_path)

    review_lines = [
        "# HELP/META Harvest Promotion Review",
        "",
        f"Status: **{status}**. Plan only; canonical files changed: 0.",
        "",
        f"- Run: `{run_id}`",
        f"- Candidate freshness: `{candidate_audit['status']}`",
        f"- Canonical freshness: `{canonical_audit['status']}`",
        f"- Package files: {len(inventory)}/{len(PACKAGE_FILES)}",
        f"- Planned replacements: {len(mutation_rows)}",
        f"- Verified no-ops: {len(inventory) - len(mutation_rows)}",
        f"- Plan manifest SHA-256: `{plan_hash}`",
        f"- Mutation ledger SHA-256: `{ledger_hash}`",
        "- Apply available: no",
        "- Mutation authorized: no",
        "",
        "## Exact disposition",
        "",
        "| File | Action | Canonical SHA-256 | Candidate SHA-256 |",
        "|---|---|---|---|",
    ]
    for row in inventory:
        review_lines.append(
            f"| {row['file_name']} | {row['action']} | "
            f"`{row['canonical_sha256']}` | `{row['candidate_sha256']}` |"
        )
    review_lines.extend([
        "",
        "## Authorization boundary",
        "",
        "This package cannot apply itself. A future apply must be separately",
        "authorized against the final plan-manifest and mutation-ledger hashes,",
        "create the byte-preserved backup first, and roll back the complete",
        "mutation set on any failed after-state check.",
        "",
        "No canonical harvest, manual, reader pointer, website, staging tree,",
        "commit, push, or deployment was changed by this planning run.",
        "",
    ])
    (output_dir / "HELP_META_HARVEST_PROMOTION_REVIEW.md").write_bytes(
        "\n".join(review_lines).encode("utf-8")
    )
    return plan


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--canonical", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--observed-at-utc", required=True)
    args = parser.parse_args(argv)
    plan = build_plan(
        args.repo_root,
        args.candidate,
        args.canonical,
        args.output_dir,
        args.run_id,
        args.observed_at_utc,
    )
    print(
        "%s: mutation_rows=%d noops=%d apply_available=0 "
        "canonical_files_mutated=0"
        % (
            plan["status"],
            plan["planned_mutation_rows"],
            plan["verified_noop_rows"],
        )
    )
    return 0 if plan["status"] == "PASS_PLAN_ONLY" else 1


if __name__ == "__main__":
    raise SystemExit(main())
