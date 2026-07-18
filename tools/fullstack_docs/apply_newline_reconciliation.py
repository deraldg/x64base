#!/usr/bin/env python3
"""Guarded CRLF-byte restoration for explicitly authorized documentation files."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def to_crlf(data: bytes) -> bytes:
    return data.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")


def normalized_lf(data: bytes) -> bytes:
    return data.replace(b"\r\n", b"\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--authorization", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    if sys.version_info[:2] != (3, 12):
        raise SystemExit("Python 3.12.x is required")
    repo = args.repo_root.resolve()
    authorization_path = args.authorization if args.authorization.is_absolute() else repo / args.authorization
    output_dir = args.output_dir if args.output_dir.is_absolute() else repo / args.output_dir
    authorization = json.loads(authorization_path.read_text(encoding="utf-8-sig"))
    if authorization.get("schema") != "dottalk.documentation.newline_reconciliation_authorization.v1":
        raise SystemExit("authorization schema mismatch")
    if authorization.get("decision") != "RESTORE_RECORDED_CRLF_BYTES":
        raise SystemExit("authorization decision mismatch")
    if authorization.get("approved_by") != "maintainer" or not authorization.get("approval_text"):
        raise SystemExit("maintainer approval missing")
    boundaries = authorization.get("boundaries", {})
    if any(int(boundaries.get(name, 1)) != 0 for name in ("content_change_allowed", "accepted_evidence_update_allowed", "pointer_update_allowed", "website_update_allowed")):
        raise SystemExit("authorization boundary mismatch")
    targets = authorization.get("targets", [])
    expected_target_count = int(authorization.get("expected_target_count", 4))
    if expected_target_count < 1 or expected_target_count > 16 or len(targets) != expected_target_count:
        raise SystemExit(f"exactly {expected_target_count} authorized targets are required")

    prepared = []
    for row in targets:
        path = (repo / row["path"]).resolve()
        try:
            path.relative_to(repo)
        except ValueError as exc:
            raise SystemExit(f"target escapes repository: {path}") from exc
        if not path.is_file():
            raise SystemExit(f"missing target: {path}")
        before = path.read_bytes()
        if sha256_bytes(before) != row["before_sha256"]:
            raise SystemExit(f"before hash mismatch: {row['path']}")
        after = to_crlf(before)
        if normalized_lf(before) != normalized_lf(after):
            raise SystemExit(f"content changed during newline conversion: {row['path']}")
        if sha256_bytes(after) != row["after_sha256"]:
            raise SystemExit(f"derived after hash mismatch: {row['path']}")
        prepared.append((row, path, before, after))

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup_root = repo / "docs/manuals/developer/manualgen/backups" / f"docflush_newline_reconciliation_{stamp}"
    staged_root = output_dir / "staged_after"
    for row, path, before, after in prepared:
        relative = path.relative_to(repo)
        backup = backup_root / relative
        staged = staged_root / relative
        backup.parent.mkdir(parents=True, exist_ok=True)
        staged.parent.mkdir(parents=True, exist_ok=True)
        backup.write_bytes(before)
        staged.write_bytes(after)

    applied = []
    for row, path, before, after in prepared:
        temporary = path.with_name(path.name + ".newline-reconcile.tmp")
        temporary.write_bytes(after)
        os.replace(temporary, path)
        actual = sha256_file(path)
        if actual != row["after_sha256"]:
            raise SystemExit(f"post-apply hash mismatch: {row['path']}")
        applied.append({
            "role": row["role"],
            "path": row["path"],
            "before_sha256": row["before_sha256"],
            "after_sha256": actual,
            "normalized_content_equal": 1,
            "status": "PASS",
        })

    output_dir.mkdir(parents=True, exist_ok=True)
    manifest = {
        "schema": "dottalk.documentation.newline_reconciliation_result.v1",
        "created_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "authorization": str(authorization_path.relative_to(repo)).replace("\\", "/"),
        "authorization_sha256": sha256_file(authorization_path),
        "backup_root": str(backup_root.relative_to(repo)).replace("\\", "/"),
        "status": "PASS_APPLIED",
        "targets": applied,
        "boundaries": {
            "normalized_content_changes": 0,
            "accepted_evidence_mutated": 0,
            "pointer_mutated": 0,
            "website_mutated": 0,
        },
    }
    (output_dir / "newline_reconciliation_result_v1.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"newline_reconciliation status=PASS_APPLIED targets={len(applied)} backup={manifest['backup_root']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
