"""Build candidate pages for supported commands added after a HELP baseline."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path


MANUALGEN_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(MANUALGEN_ROOT))

from manualgen_lib.command_reference_candidate import (  # noqa: E402
    _deduplicate_lines,
    _render_page,
)


TRUE_VALUES = {"1", "T", "TRUE", "Y", "YES"}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def slug_for(topic: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", topic.strip().lower()).strip("_")


def supported(path: Path) -> dict[str, dict[str, str]]:
    return {
        row["TOPICKEY"]: row
        for row in read_csv(path)
        if row.get("CATALOG", "").upper() == "DOT"
        and row.get("SUPPORTED", "").upper() in TRUE_VALUES
    }


def build(
    current_topics_path: Path,
    baseline_topics_path: Path,
    help_lines_path: Path,
    accepted_command_dir: Path,
    output_dir: Path,
    expected_keys: set[str],
) -> dict[str, object]:
    current = supported(current_topics_path)
    baseline = supported(baseline_topics_path)
    physical_slugs = {path.stem.lower() for path in accepted_command_dir.glob("*.md")}
    new_gaps = {
        key: row
        for key, row in current.items()
        if key not in baseline and slug_for(row.get("TOPIC", "")) not in physical_slugs
    }
    findings: list[str] = []
    if set(new_gaps) != expected_keys:
        findings.append(
            "EXPECTED_KEY_MISMATCH:"
            f"actual={';'.join(sorted(new_gaps))}:"
            f"expected={';'.join(sorted(expected_keys))}"
        )

    lines_by_topic: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in read_csv(help_lines_path):
        lines_by_topic[row.get("TOPICKEY", "")].append(row)

    commands_dir = output_dir / "commands"
    commands_dir.mkdir(parents=True, exist_ok=True)
    ledger: list[dict[str, object]] = []
    lineage: list[dict[str, object]] = []
    for key in sorted(new_gaps):
        topic = new_gaps[key]
        label = topic.get("TITLE", "").strip() or topic.get("TOPIC", "").strip()
        slug = slug_for(topic.get("TOPIC", ""))
        selected, dispositions = _deduplicate_lines(lines_by_topic.get(key, []))
        page = commands_dir / f"{slug}.md"
        page.write_text(
            _render_page(
                topic,
                label,
                selected,
                "DOCFLUSH-20260722-001/help_meta_export_v5",
                "POSTBASELINE_SUPPORTED_COVERAGE_REPAIR",
            ),
            encoding="utf-8",
        )
        ledger.append(
            {
                "topic_key": key,
                "topic": topic.get("TOPIC", ""),
                "slug": slug,
                "status": topic.get("STATUS", ""),
                "source_help_rows": len(lines_by_topic.get(key, [])),
                "included_help_rows": len(selected),
                "excluded_help_rows": len(lines_by_topic.get(key, [])) - len(selected),
                "candidate_path": str(page),
                "candidate_sha256": sha256(page),
            }
        )
        for source_row in lines_by_topic.get(key, []):
            line_id = source_row.get("LINEID", "")
            disposition = dispositions.get(line_id, "EXCLUDE_UNCLASSIFIED")
            lineage.append(
                {
                    "topic_key": key,
                    "slug": slug,
                    "line_id": line_id,
                    "kind": source_row.get("KIND", ""),
                    "source": source_row.get("SOURCE", ""),
                    "included": int(disposition == "INCLUDE_PUBLIC_HELP_EVIDENCE"),
                    "disposition": disposition,
                    "text_sha256": hashlib.sha256(
                        source_row.get("TEXT", "").encode("utf-8")
                    ).hexdigest().upper(),
                }
            )
        if not selected:
            findings.append(f"NO_INCLUDED_HELP_ROWS:{key}")

    ledger_path = output_dir / "postbaseline_supported_command_pages_v1.csv"
    lineage_path = output_dir / "postbaseline_supported_command_lineage_v1.csv"
    report_path = output_dir / "POSTBASELINE_SUPPORTED_COMMAND_PAGES_REVIEW_V1.md"
    manifest_path = output_dir / "postbaseline_supported_command_pages_manifest_v1.json"
    with ledger_path.open("w", encoding="utf-8", newline="") as handle:
        fields = [
            "topic_key",
            "topic",
            "slug",
            "status",
            "source_help_rows",
            "included_help_rows",
            "excluded_help_rows",
            "candidate_path",
            "candidate_sha256",
        ]
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(ledger)
    with lineage_path.open("w", encoding="utf-8", newline="") as handle:
        fields = [
            "topic_key",
            "slug",
            "line_id",
            "kind",
            "source",
            "included",
            "disposition",
            "text_sha256",
        ]
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(lineage)

    report = [
        "# Post-baseline Supported Command Pages",
        "",
        f"Status: **{'PASS_CANDIDATE_ONLY' if not findings else 'FAIL'}**",
        "",
        "These pages close the supported-command coverage gaps introduced after",
        "the 2026-07-16 HELP baseline. They were rendered from the repaired",
        "isolated HELP candidate; no accepted publication file is changed by",
        "this candidate builder.",
        "",
        f"- Candidate pages: `{len(ledger)}`",
        f"- Lineage rows: `{len(lineage)}`",
        f"- Included HELP rows: `{sum(int(row['included_help_rows']) for row in ledger)}`",
        f"- Findings: `{len(findings)}`",
        "",
        "## Pages",
        "",
    ]
    report.extend(
        f"- [{row['topic']}](commands/{row['slug']}.md) — "
        f"`{row['included_help_rows']}` included HELP rows"
        for row in ledger
    )
    report.extend(["", "## Findings", ""])
    report.extend(f"- `{finding}`" for finding in findings)
    if not findings:
        report.append("- None.")
    report.append("")
    report_path.write_text("\n".join(report), encoding="utf-8")

    manifest = {
        "schema": "dottalk.manualgen.postbaseline_supported_command_pages.v1",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "required_interpreter": "Python 3.12",
        "candidate_only": 1,
        "publication_authority_claimed": 0,
        "status": "PASS_CANDIDATE_ONLY" if not findings else "FAIL",
        "expected_topic_keys": sorted(expected_keys),
        "actual_topic_keys": sorted(new_gaps),
        "counts": {
            "pages": len(ledger),
            "lineage_rows": len(lineage),
            "included_help_rows": sum(int(row["included_help_rows"]) for row in ledger),
            "findings": len(findings),
        },
        "inputs": {
            "current_topics": str(current_topics_path),
            "current_topics_sha256": sha256(current_topics_path),
            "baseline_topics": str(baseline_topics_path),
            "baseline_topics_sha256": sha256(baseline_topics_path),
            "help_lines": str(help_lines_path),
            "help_lines_sha256": sha256(help_lines_path),
            "accepted_command_dir": str(accepted_command_dir),
        },
        "artifacts": {
            "ledger": str(ledger_path),
            "ledger_sha256": sha256(ledger_path),
            "lineage": str(lineage_path),
            "lineage_sha256": sha256(lineage_path),
            "report": str(report_path),
            "report_sha256": sha256(report_path),
        },
        "pages": ledger,
        "findings": findings,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def main() -> int:
    if sys.version_info[:2] != (3, 12):
        raise SystemExit("Python 3.12.x is required")
    parser = argparse.ArgumentParser()
    parser.add_argument("--current-topics", type=Path, required=True)
    parser.add_argument("--baseline-topics", type=Path, required=True)
    parser.add_argument("--help-lines", type=Path, required=True)
    parser.add_argument("--accepted-command-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--expected-topic-key", action="append", default=[])
    args = parser.parse_args()
    manifest = build(
        args.current_topics.resolve(),
        args.baseline_topics.resolve(),
        args.help_lines.resolve(),
        args.accepted_command_dir.resolve(),
        args.output_dir.resolve(),
        set(args.expected_topic_key),
    )
    print(
        "postbaseline_supported_command_pages "
        f"status={manifest['status']} pages={manifest['counts']['pages']} "
        f"lineage={manifest['counts']['lineage_rows']}"
    )
    return 0 if manifest["status"] == "PASS_CANDIDATE_ONLY" else 2


if __name__ == "__main__":
    raise SystemExit(main())
