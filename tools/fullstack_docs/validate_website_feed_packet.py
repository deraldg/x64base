#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


MIN_PYTHON = (3, 12)
EXPECTED_ACTIONS = {"CREATE": 2, "UPDATE": 8, "REPLACE": 1}
EXPECTED_PROOF_LABELS = {"manual-reviewed", "generated-reviewed", "help-catalog-evidenced"}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def _git(repo: Path, *args: str) -> str:
    result = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, check=False)
    if result.returncode:
        raise RuntimeError(result.stderr.strip())
    return result.stdout.strip()


def validate_route_rows(rows: list[dict[str, str]], source_commit: str) -> list[str]:
    findings: list[str] = []
    if len(rows) != 11:
        findings.append(f"ROUTE_COUNT:{len(rows)}!=11")
    if len({row.get("site_path", "") for row in rows}) != len(rows):
        findings.append("DUPLICATE_SITE_PATH")
    if len({row.get("route", "") for row in rows}) != len(rows):
        findings.append("DUPLICATE_PUBLIC_ROUTE")
    action_counts = {name: sum(row.get("action") == name for row in rows) for name in EXPECTED_ACTIONS}
    if action_counts != EXPECTED_ACTIONS:
        findings.append(f"ACTION_COUNTS:{action_counts}")
    for index, row in enumerate(rows, start=2):
        prefix = f"ROW_{index}:{row.get('site_path', '')}"
        path = row.get("site_path", "")
        if not path or path.startswith("/") or ":" in path or "\\" in path:
            findings.append(f"{prefix}:SITE_PATH_NOT_REPOSITORY_RELATIVE")
        if not row.get("route", "").startswith("/"):
            findings.append(f"{prefix}:ROUTE_NOT_ABSOLUTE_WEB_PATH")
        if row.get("proof_label") not in EXPECTED_PROOF_LABELS:
            findings.append(f"{prefix}:PROOF_LABEL_INVALID")
        if row.get("gate7_mutation_authorized") != "0":
            findings.append(f"{prefix}:GATE7_AUTHORITY_NOT_ZERO")
        expected_url = f"https://github.com/deraldg/x64base/blob/{source_commit}/"
        if not row.get("public_source_url", "").startswith(expected_url):
            findings.append(f"{prefix}:PUBLIC_SOURCE_URL_NOT_BOUND")
    return findings


def validate(packet_dir: Path, public_repo: Path, site_root: Path) -> list[str]:
    packet_dir = packet_dir.resolve()
    public_repo = public_repo.resolve()
    site_root = site_root.resolve()
    manifest = json.loads((packet_dir / "website_feed_manifest_v1.json").read_text(encoding="utf-8"))
    payload = json.loads((packet_dir / "website_feed_payload_v1.json").read_text(encoding="utf-8"))
    validation = json.loads((packet_dir / "website_feed_validation_v1.json").read_text(encoding="utf-8"))
    with (packet_dir / "website_feed_route_ledger_v1.csv").open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))

    findings = validate_route_rows(rows, manifest.get("public_source_commit", ""))
    if manifest.get("status") != "PASS" or validation.get("status") != "PASS":
        findings.append("UPSTREAM_PACKET_STATUS_NOT_PASS")
    for name, record in manifest.get("artifacts", {}).items():
        path = packet_dir / name
        if not path.exists():
            findings.append(f"ARTIFACT_MISSING:{name}")
        elif _sha256(path) != record.get("sha256"):
            findings.append(f"ARTIFACT_HASH_DRIFT:{name}")
    if payload.get("source", {}).get("commit") != manifest.get("public_source_commit"):
        findings.append("SOURCE_COMMIT_BINDING_MISMATCH")
    if payload.get("boundaries") != manifest.get("boundaries"):
        findings.append("BOUNDARY_BINDING_MISMATCH")
    if any(value != 0 for value in payload.get("boundaries", {}).values()):
        findings.append("MUTATION_BOUNDARY_NONZERO")
    if payload.get("source", {}).get("command_reference_pages") != 183:
        findings.append("COMMAND_PAGE_COUNT_MISMATCH")
    if payload.get("source", {}).get("sections") != 24 or payload.get("source", {}).get("appendices") != 4:
        findings.append("MANUAL_STRUCTURE_COUNT_MISMATCH")

    commit = manifest.get("public_source_commit", "")
    for row in rows:
        target = site_root / row["site_path"]
        if row["action"] == "CREATE":
            if target.exists():
                findings.append(f"CREATE_TARGET_NOW_EXISTS:{row['site_path']}")
        else:
            if not target.exists():
                findings.append(f"UPDATE_TARGET_MISSING:{row['site_path']}")
            elif _sha256(target) != row["current_site_sha256"]:
                findings.append(f"SITE_TARGET_HASH_DRIFT:{row['site_path']}")
        oid = _git(public_repo, "rev-parse", f"{commit}:{row['source_path']}")
        if oid != row["source_git_blob_oid"]:
            findings.append(f"SOURCE_BLOB_DRIFT:{row['source_path']}")

    site_state = validation.get("website_state_after", {})
    if _git(site_root, "rev-parse", "HEAD") != site_state.get("head"):
        findings.append("WEBSITE_HEAD_DRIFT")
    if _git(site_root, "branch", "--show-current") != site_state.get("branch"):
        findings.append("WEBSITE_BRANCH_DRIFT")
    current_status = _git(site_root, "status", "--porcelain=v1", "--untracked-files=all").splitlines()
    if len(current_status) != site_state.get("status_rows"):
        findings.append("WEBSITE_STATUS_DRIFT")
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a Gate 6 website feed/export packet.")
    parser.add_argument("--packet-dir", type=Path, required=True)
    parser.add_argument("--public-repo", type=Path, required=True)
    parser.add_argument("--site-root", type=Path, required=True)
    args = parser.parse_args()
    if sys.version_info < MIN_PYTHON:
        print("website_feed_validation status=FAIL finding=PYTHON_3_12_REQUIRED")
        return 2
    try:
        findings = validate(args.packet_dir, args.public_repo, args.site_root)
    except (OSError, RuntimeError, ValueError, json.JSONDecodeError) as exc:
        print(f"website_feed_validation status=FAIL error={exc}")
        return 2
    print(f"website_feed_validation status={'PASS' if not findings else 'FAIL'} findings={len(findings)}")
    for finding in findings:
        print(f"finding={finding}")
    return 0 if not findings else 2


if __name__ == "__main__":
    raise SystemExit(main())
