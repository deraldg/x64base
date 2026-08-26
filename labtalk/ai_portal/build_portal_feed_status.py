#!/usr/bin/env python3
"""Generate the Portal feed/assertion status projection from typed registries."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

try:
    from .validate_portal_assertions import load_yaml, validate_assertions
    from .validate_portal_feeds import load_registry, validate_registry
except ImportError:  # Direct script execution from labtalk/ai_portal.
    from validate_portal_assertions import load_yaml, validate_assertions
    from validate_portal_feeds import load_registry, validate_registry


LABTALK_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = LABTALK_ROOT.parent
DEFAULT_FEEDS = LABTALK_ROOT / "registries" / "portal_feeds.yaml"
DEFAULT_ASSERTIONS = LABTALK_ROOT / "registries" / "portal_assertions.yaml"
DEFAULT_CURRENT = LABTALK_ROOT / "registries" / "current_fullstack_doc_push.yaml"
DEFAULT_JSON = LABTALK_ROOT / "reports" / "portal" / "portal_feed_status_latest.json"
DEFAULT_MARKDOWN = LABTALK_ROOT / "reports" / "portal" / "portal_feed_status_latest.md"


def json_scalar(value: Any) -> Any:
    if isinstance(value, datetime):
        normalized = value.astimezone(timezone.utc) if value.tzinfo else value.replace(tzinfo=timezone.utc)
        return normalized.isoformat().replace("+00:00", "Z")
    return value


def build_status(
    *,
    repo_root: Path,
    feed_data: dict[str, Any],
    assertion_data: dict[str, Any],
    current_data: dict[str, Any],
) -> dict[str, Any]:
    feed_findings, feed_observations = validate_registry(feed_data, repo_root)
    assertion_findings, assertion_observations = validate_assertions(assertion_data, repo_root)
    feed_findings_by_id = Counter(item["feed_id"] for item in feed_findings)
    assertion_findings_by_id = Counter(item["claim_id"] for item in assertion_findings)
    assertion_observation_by_id = {item["claim_id"]: item for item in assertion_observations}

    feeds = []
    for feed in feed_data.get("feeds", []):
        feed_id = feed.get("feed_id", "<unknown>")
        feeds.append(
            {
                "feed_id": feed_id,
                "subject_class": feed.get("subject_class"),
                "status": feed.get("status"),
                "phase": (feed.get("phase") or {}).get("canonical"),
                "evidence_state": (feed.get("evidence") or {}).get("state"),
                "sensitivity": feed.get("sensitivity"),
                "outputs": len(feed.get("outputs", [])),
                "consumers": len(feed.get("consumers", [])),
                "findings": feed_findings_by_id[feed_id],
            }
        )

    assertions = []
    for assertion in assertion_data.get("assertions", []):
        claim_id = assertion.get("claim_id", "<unknown>")
        observation = assertion_observation_by_id.get(claim_id, {})
        assertions.append(
            {
                "claim_id": claim_id,
                "subject": assertion.get("subject"),
                "predicate": assertion.get("predicate"),
                "validity": assertion.get("validity"),
                "expected": assertion.get("expected"),
                "actual": observation.get("actual"),
                "passed": observation.get("passed", False),
                "findings": assertion_findings_by_id[claim_id],
            }
        )

    evidence_counts = Counter(item["evidence_state"] for item in feeds)
    feed_status_counts = Counter(item["status"] for item in feeds)
    return {
        "schema": "dottalk.portal.status.v1",
        "generated_at_utc": json_scalar(current_data.get("observed_at_utc")),
        "mode": "development_advisory",
        "current_documentation_push": current_data.get("current", {}),
        "summary": {
            "feeds": len(feeds),
            "feed_findings": len(feed_findings),
            "feed_artifact_observations": len(feed_observations),
            "assertions": len(assertions),
            "assertion_findings": len(assertion_findings),
            "assertions_passing": sum(bool(item["passed"]) and item["findings"] == 0 for item in assertions),
            "feed_statuses": dict(sorted(feed_status_counts.items())),
            "evidence_states": dict(sorted(evidence_counts.items())),
        },
        "feeds": feeds,
        "assertions": assertions,
        "findings": {"feeds": feed_findings, "assertions": assertion_findings},
    }


def cell(value: Any) -> str:
    if isinstance(value, (dict, list)):
        value = json.dumps(value, sort_keys=True)
    return str(value).replace("|", "\\|").replace("\n", " ")


def render_markdown(status: dict[str, Any]) -> str:
    current = status["current_documentation_push"]
    summary = status["summary"]
    lines = [
        "# AI Portal Feed Status",
        "",
        "Generated from the typed feed, assertion, and current-run registries. Do not hand-edit.",
        "",
        "## Current documentation push",
        "",
        "| Field | Value |",
        "| --- | --- |",
    ]
    for key in (
        "run_id",
        "canonical_process",
        "state",
        "publication_state",
        "next_process",
        "next_entry_state",
        "first_open_entry",
    ):
        lines.append(f"| {key} | `{cell(current.get(key, ''))}` |")
    lines.extend(
        [
            "",
            "## Summary",
            "",
            f"- Feeds: {summary['feeds']} ({summary['feed_findings']} advisory findings)",
            f"- Artifact observations: {summary['feed_artifact_observations']}",
            f"- Structured assertions: {summary['assertions']} ({summary['assertions_passing']} passing, {summary['assertion_findings']} advisory findings)",
            "",
            "## Feeds",
            "",
            "| Feed | Class | Status | Phase | Evidence | Outputs | Consumers | Findings |",
            "| --- | --- | --- | --- | --- | ---: | ---: | ---: |",
        ]
    )
    for feed in status["feeds"]:
        lines.append(
            "| `{feed_id}` | {subject_class} | `{status}` | `{phase}` | `{evidence_state}` | {outputs} | {consumers} | {findings} |".format(
                **{key: cell(value) for key, value in feed.items()}
            )
        )
    lines.extend(
        [
            "",
            "## Structured assertions",
            "",
            "| Claim | Validity | Expected | Observed | Pass | Findings |",
            "| --- | --- | --- | --- | --- | ---: |",
        ]
    )
    for assertion in status["assertions"]:
        lines.append(
            f"| `{cell(assertion['claim_id'])}` | `{cell(assertion['validity'])}` | `{cell(assertion['expected'])}` | `{cell(assertion['actual'])}` | {str(bool(assertion['passed'])).lower()} | {assertion['findings']} |"
        )
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "This is development-tree status. It is not a promotion, deployment, or public publication receipt.",
            "",
        ]
    )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    parser.add_argument("--feeds", type=Path, default=DEFAULT_FEEDS)
    parser.add_argument("--assertions", type=Path, default=DEFAULT_ASSERTIONS)
    parser.add_argument("--current", type=Path, default=DEFAULT_CURRENT)
    parser.add_argument("--out-json", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--out-markdown", type=Path, default=DEFAULT_MARKDOWN)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    try:
        status = build_status(
            repo_root=args.repo_root.resolve(),
            feed_data=load_registry(args.feeds),
            assertion_data=load_yaml(args.assertions),
            current_data=load_yaml(args.current),
        )
    except (OSError, ValueError, yaml.YAMLError) as exc:
        print(f"portal-feed-status: error -- {exc}", file=sys.stderr)
        return 1
    json_text = json.dumps(status, indent=2) + "\n"
    markdown_text = render_markdown(status)
    if args.check:
        stale = []
        if not args.out_json.is_file() or args.out_json.read_text(encoding="utf-8") != json_text:
            stale.append(str(args.out_json))
        if not args.out_markdown.is_file() or args.out_markdown.read_text(encoding="utf-8") != markdown_text:
            stale.append(str(args.out_markdown))
        if stale:
            print(f"portal-feed-status: stale -- {', '.join(stale)}")
            return 3
        print("portal-feed-status: PASS -- generated reports are current")
        return 0
    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_markdown.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(json_text, encoding="utf-8")
    args.out_markdown.write_text(markdown_text, encoding="utf-8")
    print(
        f"portal-feed-status: wrote {args.out_json} and {args.out_markdown} "
        f"({status['summary']['feeds']} feeds, {status['summary']['assertions']} assertions)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
