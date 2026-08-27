#!/usr/bin/env python3
"""Validate the AIF-136 M3 pilot manifest against the current M1 inventory."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any


LABTALK_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = LABTALK_ROOT.parent
DEFAULT_MANIFEST = LABTALK_ROOT / "registries" / "aif136_memory_pilot_manifest_v1.json"
DEFAULT_SCHEMA = Path(__file__).resolve().parent / "schemas" / "portal_memory_pilot_manifest_v1.schema.json"
DEFAULT_INVENTORY = LABTALK_ROOT / "reports" / "portal" / "memory_storage_inventory_latest.json"
SCHEMA_ID = "dottalk.portal.memory-pilot-manifest.v1"


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def validate_manifest(
    manifest: dict[str, Any],
    inventory: dict[str, Any],
    *,
    repo_root: Path,
    schema_path: Path = DEFAULT_SCHEMA,
) -> list[str]:
    findings: list[str] = []
    try:
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return [f"cannot read manifest schema {schema_path}: {exc}"]
    missing_top = sorted(set(schema["required"]) - set(manifest))
    extra_top = sorted(set(manifest) - set(schema["properties"]))
    if missing_top:
        findings.append(f"manifest missing top-level field(s): {', '.join(missing_top)}")
    if extra_top:
        findings.append(f"manifest has unsupported top-level field(s): {', '.join(extra_top)}")
    for field, expected in (
        ("schema", SCHEMA_ID),
        ("lane_id", "AIF-136"),
        ("phase", "M3"),
        ("operation", "cognitive_demotion_only"),
        ("physical_action", "none_authorized"),
        ("proposed_store", "in_place_git_tracked_cold_body"),
        ("retrieval_trigger", "trigger.portal_history"),
    ):
        if manifest.get(field) != expected:
            findings.append(f"{field} must be {expected}")
    if manifest.get("ruling_state") not in {"awaiting_owner_ruling", "approved", "rejected", "withdrawn"}:
        findings.append("ruling_state is unsupported")

    inventory_rows = inventory.get("records", [])
    by_id = {row.get("memory_id"): row for row in inventory_rows if isinstance(row, dict)}
    items = manifest.get("items")
    if not isinstance(items, list) or not 1 <= len(items) <= 5:
        return findings + ["items must contain one to five exact records"]
    item_schema = schema["properties"]["items"]["items"]
    required_item = set(item_schema["required"])
    item_properties = set(item_schema["properties"])
    seen_ids: set[str] = set()
    seen_paths: set[str] = set()
    for index, item in enumerate(items):
        prefix = f"items[{index}]"
        if not isinstance(item, dict):
            findings.append(f"{prefix} must be an object")
            continue
        missing = sorted(required_item - set(item))
        extra = sorted(set(item) - item_properties)
        if missing:
            findings.append(f"{prefix} missing field(s): {', '.join(missing)}")
        if extra:
            findings.append(f"{prefix} has unsupported field(s): {', '.join(extra)}")
        memory_id = item.get("memory_id")
        source_uri = item.get("source_uri")
        if memory_id in seen_ids:
            findings.append(f"duplicate memory_id: {memory_id}")
        if source_uri in seen_paths:
            findings.append(f"duplicate source_uri: {source_uri}")
        if isinstance(memory_id, str):
            seen_ids.add(memory_id)
        if isinstance(source_uri, str):
            seen_paths.add(source_uri)
        if item.get("stored_uri") != source_uri:
            findings.append(f"{prefix}.stored_uri must equal source_uri for the in-place pilot")
        if item.get("physical_move") is not False or item.get("source_deletion") is not False:
            findings.append(f"{prefix} cannot authorize physical mutation")
        for field, expected in (
            ("current_tier", "W2"), ("proposed_tier", "C3"),
            ("authority_class", "reviewed_derivative"),
            ("sensitivity", "development_only"),
        ):
            if item.get(field) != expected:
                findings.append(f"{prefix}.{field} must be {expected}")
        source_record = by_id.get(memory_id)
        if source_record is None:
            findings.append(f"{prefix} memory_id is absent from the M1 inventory")
            continue
        for field, inventory_field in (
            ("source_uri", "source_uri"),
            ("expected_sha256", "sha256"),
            ("expected_size_bytes", "logical_size_bytes"),
        ):
            if item.get(field) != source_record.get(inventory_field):
                findings.append(f"{prefix}.{field} does not match the M1 inventory")
        if source_record.get("hash_state") != "computed":
            findings.append(f"{prefix} requires an M1-computed hash")
        if isinstance(source_uri, str):
            path = (repo_root / source_uri).resolve(strict=False)
            try:
                path.relative_to(repo_root.resolve())
            except ValueError:
                findings.append(f"{prefix}.source_uri escapes the repository")
                continue
            if not path.is_file():
                findings.append(f"{prefix}.source_uri does not exist")
            else:
                if path.stat().st_size != item.get("expected_size_bytes"):
                    findings.append(f"{prefix} live size does not match the manifest")
                if file_sha256(path) != item.get("expected_sha256"):
                    findings.append(f"{prefix} live hash does not match the manifest")

    ruling = manifest.get("owner_ruling")
    if not isinstance(ruling, dict) or ruling.get("owner") != "member.derald":
        findings.append("owner_ruling must name member.derald")
    elif manifest.get("ruling_state") == "approved":
        if ruling.get("decision") != "approved" or not ruling.get("decided_at_utc"):
            findings.append("approved state requires an explicit owner decision and timestamp")
    elif ruling.get("decision") is not None or ruling.get("decided_at_utc") is not None:
        findings.append("an unapproved manifest cannot carry a decision or decision timestamp")
    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--inventory", type=Path, default=DEFAULT_INVENTORY)
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)
    args = parser.parse_args(argv)
    try:
        manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
        inventory = json.loads(args.inventory.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        print(f"memory-pilot-manifest: error -- {exc}", file=sys.stderr)
        return 1
    findings = validate_manifest(manifest, inventory, repo_root=args.repo_root, schema_path=args.schema)
    if findings:
        print(f"memory-pilot-manifest: FAIL -- {len(findings)} finding(s)", file=sys.stderr)
        for finding in findings:
            print(f"  - {finding}", file=sys.stderr)
        return 2
    print(f"memory-pilot-manifest: PASS -- {len(manifest['items'])} exact item(s), ruling {manifest['ruling_state']}, no physical action")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
