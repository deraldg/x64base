#!/usr/bin/env python3
"""Build the bounded AIF-136 history summary from the approved M3 manifest."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


LABTALK_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = LABTALK_ROOT / "registries" / "aif136_memory_pilot_manifest_v1.json"
DEFAULT_OUTPUT = Path(__file__).resolve().parent / "PORTAL_HISTORY_SUMMARY_V1.md"


def render_summary(manifest: dict[str, Any]) -> str:
    if manifest.get("ruling_state") != "approved":
        raise ValueError("history summary requires an approved owner ruling")
    if manifest.get("physical_action") != "none_authorized":
        raise ValueError("history summary refuses a physical-action manifest")
    lines = [
        "# AI Portal Historical Memory Summary V1",
        "",
        "Generated from the owner-approved AIF-136 M3 manifest. Do not hand-edit.",
        "",
        "Use this bounded index when the task asks why current Portal controls exist,",
        "requests prior Portal assessments, or studies the lineage of intent-driven",
        "seed recall. Current behavior remains owned by maintained seeds, source,",
        "contracts, registries, and runtime evidence.",
        "",
        "Trigger: `trigger.portal_history`",
        "",
        "Physical posture: every body remains at its Git-tracked source path. This",
        "summary authorizes no copy, move, deletion, publication, or supersession.",
        "",
        "## Cold bodies",
        "",
    ]
    for item in manifest["items"]:
        lines.extend([
            f"### `{item['memory_id']}`",
            "",
            item["portal_summary"],
            "",
            f"- Body: `{item['source_uri']}`",
            f"- SHA-256: `{item['expected_sha256']}`",
            f"- Bytes: {item['expected_size_bytes']}",
            f"- Authority: `{item['authority_class']}`",
            f"- Sensitivity: `{item['sensitivity']}`",
            f"- Cognitive tier: `C3` (owner-confirmed)",
            f"- Lineage boundary: {item['lineage_note']}",
            "",
        ])
    lines.extend([
        "## Retrieval rule",
        "",
        "Load a full body only when the request matches this history trigger or names",
        "the exact body. Before relying on it, compare the live hash with this summary",
        "and use current authorities for current-state claims.",
        "",
    ])
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    try:
        manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
        text = render_summary(manifest)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f"portal-history-summary: error -- {exc}", file=sys.stderr)
        return 1
    if args.check:
        if not args.output.is_file() or args.output.read_text(encoding="utf-8") != text:
            print(f"portal-history-summary: stale -- {args.output}")
            return 3
        print("portal-history-summary: PASS -- bounded history summary is current")
        return 0
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(text, encoding="utf-8")
    print(f"portal-history-summary: wrote {args.output} ({len(manifest['items'])} cold bodies)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
