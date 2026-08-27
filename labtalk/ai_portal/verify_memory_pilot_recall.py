#!/usr/bin/env python3
"""Prove the approved AIF-136 M4 cognitive-demotion recall behavior."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


LABTALK_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = LABTALK_ROOT / "registries" / "aif136_memory_pilot_manifest_v1.json"
DEFAULT_SUMMARY = Path(__file__).resolve().parent / "PORTAL_HISTORY_SUMMARY_V1.md"
RECALL = Path(__file__).resolve().parent / "recall.py"


def verify_outputs(
    manifest: dict[str, Any], summary_text: str, onboard_output: str, history_output: str
) -> list[str]:
    findings: list[str] = []
    if manifest.get("ruling_state") != "approved":
        findings.append("manifest is not owner-approved")
    if "PORTAL_HISTORY_SUMMARY_V1.md" not in history_output:
        findings.append("portal_history recall does not resolve the bounded summary")
    for item in manifest.get("items", []):
        source_uri = item.get("source_uri", "")
        basename = Path(source_uri).name
        if basename and basename in onboard_output:
            findings.append(f"ordinary onboarding loads cold body: {basename}")
        if source_uri not in summary_text:
            findings.append(f"history summary does not resolve source path: {source_uri}")
        digest = item.get("expected_sha256", "")
        if digest not in summary_text:
            findings.append(f"history summary does not resolve expected hash: {source_uri}")
    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY)
    args = parser.parse_args(argv)
    try:
        manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
        summary_text = args.summary.read_text(encoding="utf-8")
        onboard = subprocess.run(
            [sys.executable, str(RECALL), "onboard"], check=True,
            capture_output=True, text=True, encoding="utf-8",
        ).stdout
        history = subprocess.run(
            [sys.executable, str(RECALL), "portal_history"], check=True,
            capture_output=True, text=True, encoding="utf-8",
        ).stdout
    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
        print(f"memory-pilot-recall: error -- {exc}", file=sys.stderr)
        return 1
    findings = verify_outputs(manifest, summary_text, onboard, history)
    if findings:
        print(f"memory-pilot-recall: FAIL -- {len(findings)} finding(s)", file=sys.stderr)
        for finding in findings:
            print(f"  - {finding}", file=sys.stderr)
        return 2
    print(
        f"memory-pilot-recall: PASS -- {len(manifest['items'])} cold bodies excluded from onboard and resolved by portal_history summary"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
