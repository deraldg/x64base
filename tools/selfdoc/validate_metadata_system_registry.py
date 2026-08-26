#!/usr/bin/env python3
"""Validate the cross-domain SelfDoc metadata system registry.

This validator is read-only. It prints findings to stdout and never rewrites
the registry, SelfDoc manifests, source, HELP, DBF, CDX, or LMDB artifacts.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "metadata_system_registry_v1"
SYSTEM_ID_RE = re.compile(r"^META-[0-9]{3}$")
SHA256_RE = re.compile(r"^[0-9A-Fa-f]{64}$")
LIFECYCLES = {"ACTIVE", "SUPPORTING", "PROTOTYPE", "HISTORICAL", "UTILITY"}
MUTATION_CLASSES = {
    "READ_ONLY",
    "REPORT_ONLY",
    "CANDIDATE_WRITER",
    "IN_MEMORY_ONLY",
    "PROJECTION_WRITER",
    "PROTECTED_HELP_MUTATOR",
    "PROTECTED_STORAGE_MUTATOR",
    "HELPER_ONLY",
}
PROTECTED_MUTATORS = {"PROTECTED_HELP_MUTATOR", "PROTECTED_STORAGE_MUTATOR"}
REQUIRED_SYSTEM_FIELDS = {
    "system_id",
    "name",
    "canonical_entrypoints",
    "role",
    "authority_domain",
    "authority_class",
    "mutation_class",
    "protected_targets",
    "lifecycle",
    "owner_lane",
    "inputs",
    "outputs",
    "dependencies",
    "overlaps",
    "source_sha256",
    "last_verified",
    "selfdoc_tool_manifest_entry",
    "execution_default_allowed",
    "promotion_authorized",
}
LIST_FIELDS = {
    "canonical_entrypoints",
    "protected_targets",
    "inputs",
    "outputs",
    "dependencies",
    "overlaps",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def load_registry(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError("registry root must be a JSON object")
    return data


def validate_registry(
    data: dict[str, Any],
    repo_root: Path,
    freshness_system_ids: set[str] | None = None,
) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []

    def add(code: str, subject: str, detail: str) -> None:
        findings.append({"code": code, "subject": subject, "detail": detail})

    if data.get("schema_version") != SCHEMA_VERSION:
        add("SCHEMA_VERSION", "registry", f"expected {SCHEMA_VERSION}")
    if data.get("kind") != "metadata_system_registry":
        add("REGISTRY_KIND", "registry", "kind must be metadata_system_registry")
    if data.get("mutation_authorized") is not False:
        add("MUTATION_GATE", "registry", "mutation_authorized must be false")
    if data.get("promotion_authorized") is not False:
        add("PROMOTION_GATE", "registry", "promotion_authorized must be false")

    inventory = data.get("source_inventory")
    if not isinstance(inventory, dict):
        add("SOURCE_INVENTORY", "registry", "source_inventory object is required")
    else:
        inventory_path = inventory.get("path")
        inventory_hash = inventory.get("sha256")
        if not isinstance(inventory_path, str) or not inventory_path:
            add("SOURCE_INVENTORY_PATH", "registry", "source inventory path is required")
        else:
            resolved = repo_root / inventory_path
            if not resolved.is_file():
                add("SOURCE_INVENTORY_MISSING", inventory_path, "file does not exist")
            elif not isinstance(inventory_hash, str) or sha256_file(resolved) != inventory_hash.upper():
                add("SOURCE_INVENTORY_HASH", inventory_path, "SHA-256 does not match")

    systems = data.get("systems")
    if not isinstance(systems, list):
        add("SYSTEMS_TYPE", "registry", "systems must be a list")
        return findings

    seen: set[str] = set()
    valid_ids: set[str] = set()
    for index, system in enumerate(systems):
        subject = f"systems[{index}]"
        if not isinstance(system, dict):
            add("SYSTEM_TYPE", subject, "system row must be an object")
            continue
        system_id = system.get("system_id")
        if isinstance(system_id, str):
            subject = system_id
            if not SYSTEM_ID_RE.fullmatch(system_id):
                add("SYSTEM_ID_FORMAT", subject, "expected META-NNN")
            if system_id in seen:
                add("SYSTEM_ID_DUPLICATE", subject, "system id is duplicated")
            seen.add(system_id)
            valid_ids.add(system_id)
        else:
            add("SYSTEM_ID_REQUIRED", subject, "system_id must be a string")

        missing = sorted(REQUIRED_SYSTEM_FIELDS - set(system))
        for field in missing:
            add("FIELD_REQUIRED", subject, f"missing field: {field}")

        for field in LIST_FIELDS:
            value = system.get(field)
            if not isinstance(value, list):
                add("FIELD_LIST", subject, f"{field} must be a list")
            elif field in {"canonical_entrypoints", "inputs", "outputs"} and not value:
                add("FIELD_NONEMPTY", subject, f"{field} must not be empty")
            elif any(not isinstance(item, str) or not item for item in value):
                add("FIELD_LIST_VALUE", subject, f"{field} must contain non-empty strings")

        lifecycle = system.get("lifecycle")
        if lifecycle not in LIFECYCLES:
            add("LIFECYCLE", subject, f"unsupported lifecycle: {lifecycle}")
        mutation_class = system.get("mutation_class")
        if mutation_class not in MUTATION_CLASSES:
            add("MUTATION_CLASS", subject, f"unsupported mutation class: {mutation_class}")
        if mutation_class in PROTECTED_MUTATORS and not system.get("protected_targets"):
            add("PROTECTED_TARGETS", subject, "protected mutator must name targets")
        if system.get("execution_default_allowed") is not False:
            add("DEFAULT_EXECUTION", subject, "execution_default_allowed must be false")
        if system.get("promotion_authorized") is not False:
            add("SYSTEM_PROMOTION", subject, "promotion_authorized must be false")

        expected_hash = system.get("source_sha256")
        if not isinstance(expected_hash, str) or not SHA256_RE.fullmatch(expected_hash):
            add("SOURCE_SHA256", subject, "source_sha256 must be 64 hexadecimal characters")

        entrypoints = system.get("canonical_entrypoints")
        if isinstance(entrypoints, list) and entrypoints and isinstance(entrypoints[0], str):
            primary = repo_root / entrypoints[0]
            if not primary.is_file():
                add("ENTRYPOINT_MISSING", subject, entrypoints[0])
            else:
                check_freshness = freshness_system_ids is None or subject in freshness_system_ids
                if (
                    check_freshness
                    and isinstance(expected_hash, str)
                    and SHA256_RE.fullmatch(expected_hash)
                    and sha256_file(primary) != expected_hash.upper()
                ):
                    add("ENTRYPOINT_HASH", subject, f"primary SHA-256 mismatch: {entrypoints[0]}")
            for entrypoint in entrypoints[1:]:
                if isinstance(entrypoint, str) and not (repo_root / entrypoint).is_file():
                    add("ENTRYPOINT_MISSING", subject, entrypoint)

        last_verified = system.get("last_verified")
        if not isinstance(last_verified, dict):
            add("LAST_VERIFIED", subject, "last_verified must be an object")
        else:
            if not last_verified.get("run_id") or not last_verified.get("date"):
                add("LAST_VERIFIED_FIELDS", subject, "run_id and date are required")

    for system in systems:
        if not isinstance(system, dict):
            continue
        subject = str(system.get("system_id", "unknown"))
        for field in ("dependencies", "overlaps"):
            values = system.get(field)
            if not isinstance(values, list):
                continue
            for related in values:
                if isinstance(related, str) and related not in valid_ids:
                    add("RELATED_SYSTEM", subject, f"{field} references unknown id: {related}")
                if related == subject:
                    add("SELF_REFERENCE", subject, f"{field} must not reference itself")

    if freshness_system_ids is not None:
        for requested_id in sorted(freshness_system_ids - valid_ids):
            add("SYSTEM_SELECTION", requested_id, "selected system id is not registered")

    registry_pointer = "selfdoc/metadata_system_registry_v1.json"
    contract_pointer = "docs/maintenance/lanes/full_stack_documentation/METADATA_SYSTEM_REGISTRY_CONTRACT_V1.md"
    manifest_texts: dict[str, str] = {}
    for manifest_name in ("tool_manifest.yaml", "pipeline_manifest.yaml"):
        manifest_path = repo_root / "selfdoc" / manifest_name
        text = manifest_path.read_text(encoding="utf-8") if manifest_path.is_file() else ""
        manifest_texts[manifest_name] = text
        if registry_pointer not in text:
            add("MANIFEST_REGISTRY_POINTER", manifest_name, f"missing {registry_pointer}")
        if contract_pointer not in text:
            add("MANIFEST_CONTRACT_POINTER", manifest_name, f"missing {contract_pointer}")

    tool_manifest_text = manifest_texts["tool_manifest.yaml"]
    for system in systems:
        if not isinstance(system, dict) or system.get("selfdoc_tool_manifest_entry") is not True:
            continue
        subject = str(system.get("system_id", "unknown"))
        tool_id = system.get("selfdoc_tool_id")
        if not isinstance(tool_id, str) or not tool_id:
            add("SELFDOC_TOOL_ID", subject, "mapped system requires selfdoc_tool_id")
        elif tool_id not in tool_manifest_text:
            add("SELFDOC_TOOL_MAPPING", subject, f"tool id not found in tool_manifest.yaml: {tool_id}")

    declared_count = data.get("system_count")
    if declared_count != len(systems):
        add("SYSTEM_COUNT", "registry", f"declared {declared_count}, observed {len(systems)}")
    return findings


def audit(
    registry_path: Path,
    repo_root: Path,
    freshness_system_ids: set[str] | None = None,
) -> dict[str, Any]:
    data = load_registry(registry_path)
    findings = validate_registry(data, repo_root.resolve(), freshness_system_ids)
    result = {
        "schema_version": SCHEMA_VERSION,
        "registry": str(registry_path.resolve()),
        "system_count": len(data.get("systems", [])) if isinstance(data.get("systems"), list) else 0,
        "finding_count": len(findings),
        "status": "PASS" if not findings else "FAIL",
        "findings": findings,
    }
    if freshness_system_ids is not None:
        result["freshness_system_ids"] = sorted(freshness_system_ids)
    return result


def main() -> int:
    repo_default = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=repo_default)
    parser.add_argument("--registry", type=Path)
    parser.add_argument(
        "--system-id",
        action="append",
        dest="system_ids",
        help=(
            "limit source-hash freshness checks to this META-NNN id; may be repeated. "
            "All registry structure, relationship, gate, entrypoint-existence, and manifest checks still run."
        ),
    )
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    repo_root = args.repo_root.resolve()
    registry_path = args.registry or (repo_root / "selfdoc" / "metadata_system_registry_v1.json")
    freshness_system_ids = set(args.system_ids) if args.system_ids else None
    result = audit(registry_path, repo_root, freshness_system_ids)
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(
            "metadata_system_registry "
            f"status={result['status']} systems={result['system_count']} "
            f"findings={result['finding_count']}"
        )
        for finding in result["findings"]:
            print(f"- {finding['code']} {finding['subject']}: {finding['detail']}")
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
