"""Verify that supported source-contract lines survive into HELP_LINE."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path


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


def normal(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip()).casefold()


def expected_lines(row: dict[str, str]) -> list[tuple[str, str]]:
    lines: list[tuple[str, str]] = []
    for field in ("USAGE", "EXAMPLES", "NOTES"):
        for value in row.get(field, "").replace("\r\n", "\n").split("\n"):
            if value.strip():
                lines.append((field, value.strip()))
    for value in row.get("RELATED", "").split(";"):
        if value.strip():
            lines.append(("RELATED", value.strip()))
    return lines


def audit(
    srcusage_path: Path,
    help_topics_path: Path,
    help_lines_path: Path,
    output_dir: Path,
) -> dict[str, object]:
    supported = {
        row.get("TOPICKEY", "")
        for row in read_csv(help_topics_path)
        if row.get("SUPPORTED", "").strip().upper() in TRUE_VALUES
    }
    actual: dict[str, set[str]] = {}
    for row in read_csv(help_lines_path):
        if row.get("SOURCE", "").strip().upper() != "USAGE_CONTRACT":
            continue
        actual.setdefault(row.get("TOPICKEY", ""), set()).add(normal(row.get("TEXT", "")))

    findings: list[dict[str, object]] = []
    contracts_checked = 0
    expected_count = 0
    for row in read_csv(srcusage_path):
        topic_key = row.get("OWNER", "").strip().upper()
        if topic_key not in supported:
            continue
        contracts_checked += 1
        actual_lines = actual.get(topic_key, set())
        for field, text in expected_lines(row):
            expected_count += 1
            if normal(text) not in actual_lines:
                findings.append(
                    {
                        "topic_key": topic_key,
                        "command": row.get("COMMAND", ""),
                        "field": field,
                        "expected_text": text,
                        "result": "MISSING_FROM_HELP",
                    }
                )

    output_dir.mkdir(parents=True, exist_ok=True)
    ledger_path = output_dir / "help_contract_continuation_findings_v1.csv"
    report_path = output_dir / "HELP_CONTRACT_CONTINUATION_AUDIT_V1.md"
    manifest_path = output_dir / "help_contract_continuation_manifest_v1.json"
    with ledger_path.open("w", encoding="utf-8", newline="") as handle:
        fields = ["topic_key", "command", "field", "expected_text", "result"]
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(findings)

    by_topic = sorted({row["topic_key"] for row in findings})
    status = "PASS" if not findings else "FAIL"
    report = [
        "# HELP Contract Continuation Audit",
        "",
        f"Status: **{status}**",
        "",
        "This audit compares every line in the USAGE, EXAMPLES, NOTES, and",
        "RELATED fields of supported `SRCUSAGE` contracts with authoritative",
        "`USAGE_CONTRACT` rows in the isolated HELP candidate.",
        "",
        f"- Supported contracts checked: `{contracts_checked}`",
        f"- Contract lines checked: `{expected_count}`",
        f"- Missing continuation lines: `{len(findings)}`",
        f"- Topics with missing lines: `{len(by_topic)}`",
        "",
        "## Topics with findings",
        "",
    ]
    report.extend(f"- `{topic}`" for topic in by_topic)
    if not by_topic:
        report.append("- None.")
    report.append("")
    report_path.write_text("\n".join(report), encoding="utf-8")
    manifest = {
        "schema": "x64base.help_contract_continuation_audit.v1",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "required_interpreter": "Python 3.12",
        "status": status,
        "counts": {
            "supported_contracts_checked": contracts_checked,
            "contract_lines_checked": expected_count,
            "missing_lines": len(findings),
            "topics_with_findings": len(by_topic),
        },
        "inputs": {
            "srcusage": str(srcusage_path),
            "srcusage_sha256": sha256(srcusage_path),
            "help_topics": str(help_topics_path),
            "help_topics_sha256": sha256(help_topics_path),
            "help_lines": str(help_lines_path),
            "help_lines_sha256": sha256(help_lines_path),
        },
        "artifacts": {
            "ledger": str(ledger_path),
            "ledger_sha256": sha256(ledger_path),
            "report": str(report_path),
            "report_sha256": sha256(report_path),
        },
        "finding_topic_keys": by_topic,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def main() -> int:
    if sys.version_info[:2] != (3, 12):
        raise SystemExit("Python 3.12.x is required")
    parser = argparse.ArgumentParser()
    parser.add_argument("--srcusage", type=Path, required=True)
    parser.add_argument("--help-topics", type=Path, required=True)
    parser.add_argument("--help-lines", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    manifest = audit(
        args.srcusage.resolve(),
        args.help_topics.resolve(),
        args.help_lines.resolve(),
        args.output_dir.resolve(),
    )
    print(
        "help_contract_continuation "
        f"status={manifest['status']} "
        f"checked={manifest['counts']['contract_lines_checked']} "
        f"missing={manifest['counts']['missing_lines']}"
    )
    return 0 if manifest["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
