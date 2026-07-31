#!/usr/bin/env python3
"""Validate a Gate 7 website integration plan without mutating the website."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


ALLOWED_ACTIONS = {"CREATE", "UPDATE", "REPLACE"}
ALLOWED_PROOF_LABELS = {
    "manual-reviewed",
    "generated-reviewed",
    "help-catalog-evidenced",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def git(site_root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(site_root), *args],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def validate_plan(
    plan: dict[str, Any],
    site_root: Path,
    *,
    observed_branch: str,
    observed_head: str,
    observed_status: str,
) -> list[str]:
    findings: list[str] = []

    if plan.get("schema") != "dottalk.website.integration_plan.v1":
        findings.append("unexpected plan schema")
    if plan.get("status") != "PLAN_READY_MUTATION_NOT_AUTHORIZED":
        findings.append("plan status is not held for authorization")

    website = plan.get("website", {})
    if observed_branch != website.get("branch"):
        findings.append(
            f"website branch drift: expected {website.get('branch')}, observed {observed_branch}"
        )
    if observed_head != website.get("baseline_commit"):
        findings.append(
            f"website HEAD drift: expected {website.get('baseline_commit')}, observed {observed_head}"
        )
    if observed_status:
        findings.append("website working tree is not clean")
    if website.get("build_command") != "npm run build":
        findings.append("unexpected website build command")

    authorization = plan.get("authorization", {})
    if not authorization or any(bool(value) for value in authorization.values()):
        findings.append("one or more Gate 7 authorization flags are enabled")

    operations = plan.get("operations", [])
    if len(operations) != 11:
        findings.append(f"expected 11 operations, found {len(operations)}")

    actions: dict[str, int] = {action: 0 for action in ALLOWED_ACTIONS}
    paths: set[str] = set()
    routes: set[str] = set()
    sequences: set[int] = set()

    for operation in operations:
        action = operation.get("action")
        if action not in ALLOWED_ACTIONS:
            findings.append(f"invalid action: {action}")
            continue
        actions[action] += 1

        path_text = operation.get("site_path", "")
        route = operation.get("route", "")
        sequence = operation.get("sequence")
        if path_text in paths:
            findings.append(f"duplicate site path: {path_text}")
        paths.add(path_text)
        if route in routes:
            findings.append(f"duplicate route: {route}")
        routes.add(route)
        if sequence in sequences:
            findings.append(f"duplicate sequence: {sequence}")
        sequences.add(sequence)

        if Path(path_text).is_absolute() or ".." in Path(path_text).parts:
            findings.append(f"unsafe site path: {path_text}")
            continue
        if operation.get("proof_label") not in ALLOWED_PROOF_LABELS:
            findings.append(f"invalid proof label for {path_text}")
        if not operation.get("content_contract"):
            findings.append(f"missing content contract for {path_text}")

        target = site_root / path_text
        expected_before = operation.get("before_sha256")
        if action == "CREATE":
            if expected_before != "ABSENT":
                findings.append(f"CREATE target lacks ABSENT precondition: {path_text}")
            if target.exists():
                findings.append(f"CREATE target already exists: {path_text}")
        else:
            if not target.is_file():
                findings.append(f"existing target is absent: {path_text}")
            elif sha256_file(target) != expected_before:
                findings.append(f"before hash drift: {path_text}")

    if actions != {"CREATE": 2, "UPDATE": 8, "REPLACE": 1}:
        findings.append(f"unexpected action counts: {actions}")
    if sequences != set(range(1, 12)):
        findings.append("operation sequences are not exactly 1 through 11")

    holds = "\n".join(plan.get("holds", []))
    for required in ("No website commit", "metacollect", "No dependency"):
        if required not in holds:
            findings.append(f"missing required hold: {required}")

    return findings


def _status_paths(observed_status: str) -> set[str]:
    paths: set[str] = set()
    for row in observed_status.splitlines():
        if not row.strip():
            continue
        if len(row) >= 3 and row[2] == " ":
            path_text = row[3:]
        else:
            fields = row.split(maxsplit=1)
            path_text = fields[1] if len(fields) == 2 else ""
        path_text = path_text.strip().strip('"').replace("\\", "/")
        if " -> " in path_text:
            path_text = path_text.split(" -> ", 1)[1]
        paths.add(path_text)
    return paths


def validate_applied_plan(
    plan: dict[str, Any],
    site_root: Path,
    *,
    observed_branch: str,
    observed_head: str,
    observed_status: str,
) -> list[str]:
    """Validate the authorized working-tree transaction after a local build."""

    findings: list[str] = []
    website = plan.get("website", {})
    operations = plan.get("operations", [])

    if observed_branch != website.get("branch"):
        findings.append("website branch drift after apply")
    if observed_head != website.get("baseline_commit"):
        findings.append("website HEAD changed during Gate 7")

    planned_paths = {operation["site_path"] for operation in operations}
    changed_paths = _status_paths(observed_status)
    if changed_paths != planned_paths:
        missing = sorted(planned_paths - changed_paths)
        extra = sorted(changed_paths - planned_paths)
        if missing:
            findings.append(f"planned paths missing from diff: {missing}")
        if extra:
            findings.append(f"paths outside plan changed: {extra}")

    for operation in operations:
        target = site_root / operation["site_path"]
        if not target.is_file():
            findings.append(f"applied target is absent: {operation['site_path']}")

    manual_operation = next(
        operation for operation in operations if operation["action"] == "REPLACE"
    )
    manual_path = site_root / manual_operation["site_path"]
    expected_manual_sha = manual_operation.get("after_sha256_required")
    if manual_path.is_file() and sha256_file(manual_path) != expected_manual_sha:
        findings.append("manual download does not match the required public Git blob")
    if manual_path.is_file():
        manual_text = manual_path.read_text(encoding="utf-8")
        if len(manual_text.splitlines()) != 4118:
            findings.append("manual line count is not 4118")
        heading_count = sum(
            1 for line in manual_text.splitlines() if re.match(r"^#{1,6}\s", line)
        )
        if heading_count != 237:
            findings.append("manual heading count is not 237")

    manifest_path = site_root / "public/downloads/current/DOWNLOAD_MANIFEST.json"
    if manifest_path.is_file():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        snapshot = manifest.get("accepted_documentation_snapshot", {})
        required_manifest_values = {
            "source_commit": plan["source"]["commit"],
            "manual_download_sha256": plan["source"]["manual_blob_sha256"],
            "manual_lines": 4118,
            "manual_headings": 237,
            "command_reference_pages": 183,
            "reader_linked_command_pages": 164,
            "supplemental_command_pages": 19,
            "command_lineage_rows": 3974,
        }
        for key, value in required_manifest_values.items():
            if snapshot.get(key) != value:
                findings.append(f"download manifest mismatch: {key}")

    required_tokens = {
        "app/downloads/page.tsx": ["Accepted documentation snapshot", "be935053", "4,118", "237"],
        "content/docs/dev/developer-handbook.mdx": ["Accepted documentation entrypoints", "be935053"],
        "content/docs/dev/important-documents.mdx": ["Current Manual Publication", "3,974"],
        "content/docs/dev/website-documentation-matrix.mdx": ["2026-07-18 Publication Checkpoint", "Python `3.12.9`"],
        "content/docs/dottalk/command-catalog.mdx": ["Catalog and Accepted Reference", "3,974"],
        "content/docs/dottalk/command-reference.mdx": ["Standalone command pages | 183", "`manual-reviewed`", "3,974"],
        "content/docs/engine/feature-crosswalk.mdx": ["Python `3.12.9`", "Publication-readiness findings: `0`"],
        "content/docs/dev/selfdoc-feed-pipeline.mdx": ["Accepted 2026-07-18 Checkpoint", "Python `3.12.9`"],
        "content/news/announcements/developer-manual-gate5-published.mdx": ["4,118", "3,974", "be935053"],
    }
    for path_text, tokens in required_tokens.items():
        target = site_root / path_text
        if not target.is_file():
            continue
        text = target.read_text(encoding="utf-8")
        for token in tokens:
            if token not in text:
                findings.append(f"required content absent from {path_text}: {token}")

    for path_text in (
        "content/docs/dev/selfdoc-feed-pipeline.mdx",
        "content/docs/engine/feature-crosswalk.mdx",
    ):
        text = (site_root / path_text).read_text(encoding="utf-8")
        if "Python `3.11" in text or "Python 3.11" in text:
            findings.append(f"obsolete Python 3.11 statement remains: {path_text}")

    required_outputs = (
        "out/docs/dottalk/command-reference/index.html",
        "out/news/announcements/developer-manual-gate5-published/index.html",
        "out/downloads/current/developer_manual_publication_v1.md",
        "dist",
    )
    for path_text in required_outputs:
        if not (site_root / path_text).exists():
            findings.append(f"required build output absent: {path_text}")
    built_manual = site_root / "out/downloads/current/developer_manual_publication_v1.md"
    if built_manual.is_file() and sha256_file(built_manual) != expected_manual_sha:
        findings.append("built manual download hash mismatch")

    return findings


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan-json", type=Path, required=True)
    parser.add_argument("--site-root", type=Path, required=True)
    parser.add_argument("--mode", choices=("preflight", "postapply"), default="preflight")
    args = parser.parse_args()

    plan = json.loads(args.plan_json.read_text(encoding="utf-8"))
    branch = git(args.site_root, "branch", "--show-current")
    head = git(args.site_root, "rev-parse", "HEAD")
    status_rows = git(args.site_root, "status", "--short", "--untracked-files=all")
    validator = validate_plan if args.mode == "preflight" else validate_applied_plan
    findings = validator(
        plan,
        args.site_root,
        observed_branch=branch,
        observed_head=head,
        observed_status=status_rows,
    )

    status = "PASS" if not findings else "FAIL"
    print(
        f"website_integration_plan mode={args.mode} status={status} "
        f"findings={len(findings)}"
    )
    for finding in findings:
        print(f"- {finding}")
    return 0 if not findings else 1


if __name__ == "__main__":
    sys.exit(main())
