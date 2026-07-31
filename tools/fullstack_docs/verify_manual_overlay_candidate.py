#!/usr/bin/env python3
"""Verify a candidate-only ordered manual overlay manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def resolve(repo_root: Path, value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else repo_root / path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    args = parser.parse_args()

    repo_root = args.repo_root.resolve()
    manifest_path = resolve(repo_root, str(args.manifest)).resolve()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    failures: list[str] = []
    reviews: list[str] = []

    source = resolve(repo_root, manifest["source_artifact"]["path"])
    if not source.is_file():
        failures.append("SOURCE_ARTIFACT_MISSING")
    elif sha256(source) != manifest["source_artifact"]["sha256"].upper():
        failures.append("SOURCE_ARTIFACT_HASH_MISMATCH")

    overlays = manifest.get("ordered_overlays", [])
    orders = [int(row["order"]) for row in overlays]
    if orders != list(range(1, len(overlays) + 1)):
        failures.append("OVERLAY_ORDER_NOT_CONTIGUOUS")

    for row in overlays:
        candidate = resolve(repo_root, row["candidate_path"])
        overlay_id = row["overlay_id"]
        if source.is_file():
            try:
                start_text, end_text = str(row["source_lines"]).split("-", 1)
                start_line, end_line = int(start_text), int(end_text)
                source_lines = source.read_text(encoding="utf-8-sig").splitlines()
                source_content = "\n".join(source_lines[start_line : end_line - 1]).strip() + "\n"
                source_content_hash = hashlib.sha256(source_content.encode("utf-8")).hexdigest().upper()
                if source_content_hash != row["source_content_sha256_lf"].upper():
                    failures.append(f"{overlay_id}:SOURCE_CONTENT_HASH_MISMATCH")
            except (KeyError, TypeError, ValueError):
                failures.append(f"{overlay_id}:SOURCE_LINE_CONTRACT_INVALID")
        if not candidate.is_file():
            failures.append(f"{overlay_id}:CANDIDATE_MISSING")
            continue
        if sha256(candidate) != row["candidate_sha256"].upper():
            failures.append(f"{overlay_id}:CANDIDATE_HASH_MISMATCH")
        text = candidate.read_text(encoding="utf-8-sig")
        fences = sum(line.startswith("```") for line in text.splitlines())
        if fences % 2:
            failures.append(f"{overlay_id}:UNBALANCED_FENCES")
        if not text.startswith("# "):
            failures.append(f"{overlay_id}:MISSING_PRIMARY_HEADING")
        if "eferences/manual_mutation_cycle_reference_v1.md" in text and "references/manual_mutation_cycle_reference_v1.md" not in text:
            failures.append(f"{overlay_id}:TRUNCATED_REFERENCE_PATH")
        if "D:\\code\\ccode\\build\\vcpkg_installed\\x64-windows\\tools\\python3\\python.exe" in text:
            interpreter = repo_root / "build" / "vcpkg_installed" / "x64-windows" / "tools" / "python3" / "python.exe"
            if not interpreter.is_file():
                reviews.append(f"{overlay_id}:DOCUMENTED_INTERPRETER_ABSENT")

    policy = manifest.get("assembly_policy", {})
    for key in (
        "active_reader_mutation_authorized",
        "supporting_publication_mutation_authorized",
        "accepted_manifest_mutation_authorized",
    ):
        if policy.get(key) is not False:
            failures.append(f"BOUNDARY_NOT_CLOSED:{key}")

    result = {
        "schema": "dottalk.fullstack.manual_overlay_candidate_verification.v1",
        "manifest": str(manifest_path),
        "overlay_count": len(overlays),
        "failure_count": len(failures),
        "review_count": len(reviews),
        "failures": failures,
        "reviews": reviews,
        "status": "PASS_WITH_REVIEW" if not failures and reviews else "PASS" if not failures else "FAIL",
    }
    print(json.dumps(result, indent=2))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
