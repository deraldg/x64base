"""Fail closed when newly supported HELP commands lack publication coverage.

This gate intentionally separates inherited documentation debt from new drift:

* a supported DOT topic has coverage when a same-slug command page exists;
* an explicit disposition may merge, defer, or hold a topic with a rationale;
* a gap already present in the selected baseline is reported as backlog;
* a supported topic added after the baseline is a blocking failure until it has
  a page or an explicit reviewed disposition.

Run with the project Python 3.12 environment.
"""

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


TRUE_VALUES = {"1", "T", "TRUE", "Y", "YES"}
DISPOSITION_VALUES = {"PAGE", "MERGE", "DEFER", "HOLD"}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def slug_for(topic: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", topic.strip().lower()).strip("_")


def supported_dot_topics(path: Path) -> dict[str, dict[str, str]]:
    rows: dict[str, dict[str, str]] = {}
    for row in read_csv(path):
        key = row.get("TOPICKEY", "").strip()
        if row.get("CATALOG", "").strip().upper() != "DOT":
            continue
        if row.get("SUPPORTED", "").strip().upper() not in TRUE_VALUES:
            continue
        if key:
            rows[key] = row
    return rows


def dispositions(path: Path | None) -> dict[str, dict[str, str]]:
    if path is None or not path.is_file():
        return {}
    rows: dict[str, dict[str, str]] = {}
    for row in read_csv(path):
        key = row.get("topic_key", "").strip()
        action = row.get("disposition", "").strip().upper()
        rationale = row.get("rationale", "").strip()
        if not key:
            continue
        if action not in DISPOSITION_VALUES:
            raise ValueError(f"invalid disposition for {key}: {action}")
        if action != "PAGE" and not rationale:
            raise ValueError(f"non-page disposition requires rationale: {key}")
        rows[key] = row
    return rows


def audit(
    current_topics: Path,
    baseline_topics: Path,
    command_dir: Path,
    disposition_path: Path | None,
    output_dir: Path,
) -> dict[str, object]:
    current = supported_dot_topics(current_topics)
    baseline = supported_dot_topics(baseline_topics)
    disposition_rows = dispositions(disposition_path)
    pages = {path.stem.lower(): path for path in command_dir.glob("*.md")}

    slug_topics: dict[str, list[str]] = defaultdict(list)
    for key, row in current.items():
        slug_topics[slug_for(row.get("TOPIC", ""))].append(key)

    ledger: list[dict[str, object]] = []
    blocking = 0
    historical = 0
    covered = 0
    disposed = 0
    for key in sorted(current):
        row = current[key]
        topic = row.get("TOPIC", "").strip()
        slug = slug_for(topic)
        page = pages.get(slug)
        disposition = disposition_rows.get(key, {})
        action = disposition.get("disposition", "").strip().upper()
        rationale = disposition.get("rationale", "").strip()
        is_new = key not in baseline

        if page is not None:
            result = "COVERED_PAGE"
            covered += 1
        elif action:
            result = f"DISPOSITION_{action}"
            disposed += 1
        elif is_new:
            result = "BLOCK_NEW_SUPPORTED_GAP"
            blocking += 1
        else:
            result = "HISTORICAL_BACKLOG"
            historical += 1

        ledger.append(
            {
                "topic_key": key,
                "topic": topic,
                "status": row.get("STATUS", ""),
                "slug": slug,
                "baseline_supported": int(not is_new),
                "page_present": int(page is not None),
                "page_path": page.as_posix() if page else "",
                "slug_collision_count": len(slug_topics[slug]),
                "disposition": action,
                "rationale": rationale,
                "result": result,
            }
        )

    stale_dispositions = sorted(set(disposition_rows) - set(current))
    collisions = {slug: keys for slug, keys in slug_topics.items() if len(keys) > 1}
    status = "PASS" if blocking == 0 else "FAIL"
    output_dir.mkdir(parents=True, exist_ok=True)
    ledger_path = output_dir / "supported_command_publication_coverage_v1.csv"
    report_path = output_dir / "SUPPORTED_COMMAND_PUBLICATION_COVERAGE_V1.md"
    manifest_path = output_dir / "supported_command_publication_coverage_manifest_v1.json"
    fields = [
        "topic_key",
        "topic",
        "status",
        "slug",
        "baseline_supported",
        "page_present",
        "page_path",
        "slug_collision_count",
        "disposition",
        "rationale",
        "result",
    ]
    write_csv(ledger_path, ledger, fields)

    blocking_rows = [row for row in ledger if row["result"] == "BLOCK_NEW_SUPPORTED_GAP"]
    report = [
        "# Supported Command Publication Coverage",
        "",
        f"Status: **{status}**",
        "",
        "This anti-regression gate distinguishes inherited command-reference debt",
        "from supported commands added after the selected HELP baseline. New",
        "supported commands fail closed until they have a page or reviewed",
        "disposition.",
        "",
        f"- Current supported DOT topics: `{len(current)}`",
        f"- Baseline supported DOT topics: `{len(baseline)}`",
        f"- Covered by physical page: `{covered}`",
        f"- Covered by explicit disposition: `{disposed}`",
        f"- Historical backlog: `{historical}`",
        f"- Blocking new supported gaps: `{blocking}`",
        f"- Slug collisions: `{len(collisions)}`",
        f"- Stale dispositions: `{len(stale_dispositions)}`",
        "",
        "## Blocking gaps",
        "",
    ]
    if blocking_rows:
        report.extend(
            f"- `{row['topic_key']}` -> expected `{row['slug']}.md`"
            for row in blocking_rows
        )
    else:
        report.append("- None.")
    report.extend(
        [
            "",
            "## Boundary",
            "",
            "Historical backlog remains visible and countable; this gate does not",
            "silently relabel it as complete. It prevents the backlog from growing.",
            "",
        ]
    )
    report_path.write_text("\n".join(report), encoding="utf-8")

    manifest = {
        "schema": "x64base.supported_command_publication_coverage.v1",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "required_interpreter": "Python 3.12",
        "status": status,
        "counts": {
            "current_supported_dot_topics": len(current),
            "baseline_supported_dot_topics": len(baseline),
            "covered_by_page": covered,
            "covered_by_disposition": disposed,
            "historical_backlog": historical,
            "blocking_new_supported_gaps": blocking,
            "slug_collisions": len(collisions),
            "stale_dispositions": len(stale_dispositions),
        },
        "inputs": {
            "current_topics": str(current_topics),
            "current_topics_sha256": sha256(current_topics),
            "baseline_topics": str(baseline_topics),
            "baseline_topics_sha256": sha256(baseline_topics),
            "command_dir": str(command_dir),
            "dispositions": str(disposition_path) if disposition_path else "",
        },
        "artifacts": {
            "ledger": str(ledger_path),
            "ledger_sha256": sha256(ledger_path),
            "report": str(report_path),
            "report_sha256": sha256(report_path),
        },
        "blocking_topic_keys": [row["topic_key"] for row in blocking_rows],
        "slug_collisions": collisions,
        "stale_disposition_topic_keys": stale_dispositions,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def main() -> int:
    if sys.version_info[:2] != (3, 12):
        raise SystemExit("Python 3.12.x is required")
    parser = argparse.ArgumentParser()
    parser.add_argument("--current-topics", type=Path, required=True)
    parser.add_argument("--baseline-topics", type=Path, required=True)
    parser.add_argument("--command-dir", type=Path, required=True)
    parser.add_argument("--dispositions", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    manifest = audit(
        args.current_topics.resolve(),
        args.baseline_topics.resolve(),
        args.command_dir.resolve(),
        args.dispositions.resolve() if args.dispositions else None,
        args.output_dir.resolve(),
    )
    print(
        "supported_command_publication_coverage "
        f"status={manifest['status']} "
        f"blocking={manifest['counts']['blocking_new_supported_gaps']} "
        f"historical={manifest['counts']['historical_backlog']}"
    )
    return 0 if manifest["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
