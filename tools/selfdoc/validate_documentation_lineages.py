#!/usr/bin/env python3
"""Validate documentation tool lineage registries without executing tools."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def validate_lineages(repo_root: Path, source_data: dict[str, Any], messaging_data: dict[str, Any]) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []

    def add(code: str, subject: str, detail: str) -> None:
        findings.append({"code": code, "subject": subject, "detail": detail})

    for name, data, schema in (
        ("source", source_data, "source_contract_probe_lineage_v1"),
        ("messaging", messaging_data, "messaging_exporter_lineage_v1"),
    ):
        if data.get("schema_version") != schema:
            add("SCHEMA_VERSION", name, f"expected {schema}")
        for gate in ("mutation_authorized", "promotion_authorized"):
            if data.get(gate) is not False:
                add("SAFETY_GATE", f"{name}.{gate}", "must be false")

    historical = source_data.get("historical_probe", {})
    _validate_hashed_path(repo_root, historical, "source.historical_probe", add)
    if historical.get("lifecycle") != "HISTORICAL" or historical.get("execution_default_allowed") is not False:
        add("HISTORICAL_GATE", "source.historical_probe", "must be historical and non-default")
    vocabulary = source_data.get("preserved_vocabulary")
    if not isinstance(vocabulary, str) or not (repo_root / vocabulary).is_file():
        add("VOCABULARY_PATH", "source.preserved_vocabulary", "registry does not exist")
    roles = source_data.get("current_role_split")
    if not isinstance(roles, dict) or not roles:
        add("ROLE_SPLIT", "source.current_role_split", "non-empty object required")
    else:
        for role, path_text in roles.items():
            if not isinstance(path_text, str) or not (repo_root / path_text).is_file():
                add("ROLE_PATH", f"source.{role}", f"missing path: {path_text}")

    canonical = messaging_data.get("canonical_exporter", {})
    historical_message = messaging_data.get("historical_exporter", {})
    _validate_hashed_path(repo_root, canonical, "messaging.canonical_exporter", add)
    _validate_hashed_path(repo_root, historical_message, "messaging.historical_exporter", add)
    if canonical.get("lifecycle") != "ACTIVE":
        add("CANONICAL_LIFECYCLE", "messaging.canonical_exporter", "must be active")
    if historical_message.get("lifecycle") != "HISTORICAL" or historical_message.get("execution_default_allowed") is not False:
        add("HISTORICAL_GATE", "messaging.historical_exporter", "must be historical and non-default")
    return findings


def _validate_hashed_path(repo_root: Path, row: Any, subject: str, add: Any) -> None:
    if not isinstance(row, dict) or not isinstance(row.get("path"), str):
        add("PATH_REQUIRED", subject, "path is required")
        return
    path = repo_root / row["path"]
    if not path.is_file():
        add("PATH_MISSING", subject, row["path"])
    elif row.get("sha256") != sha256_file(path):
        add("PATH_HASH", subject, "SHA-256 does not match")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()
    root = args.repo_root.resolve()
    source = json.loads((root / "selfdoc/source_contract_probe_lineage_v1.json").read_text(encoding="utf-8"))
    messaging = json.loads((root / "selfdoc/messaging_exporter_lineage_v1.json").read_text(encoding="utf-8"))
    findings = validate_lineages(root, source, messaging)
    print(json.dumps({"status": "PASS" if not findings else "FAIL", "findings": findings}, indent=2))
    return 0 if not findings else 1


if __name__ == "__main__":
    raise SystemExit(main())
