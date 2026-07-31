#!/usr/bin/env python3
"""Validate the reference identity authority map and current DOCFLUSH evidence."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


SCHEMA = "reference_identity_authority_v1"
REQUIRED_ENTITIES = {"COMMAND", "SUBCOMMAND", "FUNCTION", "ARGUMENT", "ENTRY_VARIANT"}
NORMALIZATION = ["trim", "uppercase", "collapse_internal_ascii_whitespace"]


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def normalized(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip().upper())


def sanitized(value: str) -> str:
    return re.sub(r"[^A-Z0-9]+", "_", normalized(value)).strip("_")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def path_exists(repo_root: Path, value: str) -> bool:
    if "*" in value or "?" in value:
        return any(repo_root.glob(value))
    return (repo_root / value).exists()


def validate_map(data: dict[str, Any], repo_root: Path) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []

    def add(code: str, subject: str, detail: str) -> None:
        findings.append({"code": code, "subject": subject, "detail": detail})

    if data.get("schema_version") != SCHEMA:
        add("SCHEMA", "map", f"expected {SCHEMA}")
    if data.get("kind") != "reference_identity_authority_map":
        add("KIND", "map", "unexpected kind")
    if data.get("mutation_authorized") is not False:
        add("MUTATION_GATE", "map", "mutation_authorized must be false")
    if data.get("promotion_authorized") is not False:
        add("PROMOTION_GATE", "map", "promotion_authorized must be false")

    contract = data.get("contract")
    if not isinstance(contract, str) or not (repo_root / contract).is_file():
        add("CONTRACT_PATH", "map", "contract path is missing")

    map_pointer = "selfdoc/reference_identity_authority_v1.json"
    contract_pointer = "docs/maintenance/lanes/full_stack_documentation/REFERENCE_IDENTITY_AUTHORITY_CONTRACT_V1.md"
    for manifest_name in ("tool_manifest.yaml", "pipeline_manifest.yaml"):
        manifest_path = repo_root / "selfdoc" / manifest_name
        text = manifest_path.read_text(encoding="utf-8") if manifest_path.is_file() else ""
        if map_pointer not in text:
            add("MANIFEST_MAP_POINTER", manifest_name, f"missing {map_pointer}")
        if contract_pointer not in text:
            add("MANIFEST_CONTRACT_POINTER", manifest_name, f"missing {contract_pointer}")

    registry_path = repo_root / "selfdoc" / "metadata_system_registry_v1.json"
    registered_systems: set[str] = set()
    if registry_path.is_file():
        registry = json.loads(registry_path.read_text(encoding="utf-8"))
        registered_systems = {row.get("system_id") for row in registry.get("systems", []) if isinstance(row, dict)}
    else:
        add("SYSTEM_REGISTRY", "map", "metadata system registry is missing")

    entity_rows = data.get("entity_types")
    if not isinstance(entity_rows, list):
        add("ENTITY_TYPES", "map", "entity_types must be a list")
        entity_rows = []
    entity_ids: list[str] = []
    for row in entity_rows:
        if not isinstance(row, dict):
            add("ENTITY_ROW", "entity_types", "row must be an object")
            continue
        entity = row.get("entity_type")
        if not isinstance(entity, str):
            add("ENTITY_ID", "entity_types", "entity_type is required")
            continue
        entity_ids.append(entity)
        if not row.get("identity_template") or not row.get("identity_fields"):
            add("ENTITY_IDENTITY", entity, "template and fields are required")
        if row.get("normalization") != NORMALIZATION:
            add("ENTITY_NORMALIZATION", entity, "normalization sequence is not canonical")
        if not row.get("legacy_projection"):
            add("LEGACY_PROJECTION", entity, "legacy projection must be explicit")
    for entity, count in Counter(entity_ids).items():
        if count > 1:
            add("ENTITY_DUPLICATE", entity, "entity type is duplicated")
    missing_entities = REQUIRED_ENTITIES - set(entity_ids)
    for entity in sorted(missing_entities):
        add("ENTITY_MISSING", entity, "required entity type is absent")

    authority_rows = data.get("authority_sources")
    if not isinstance(authority_rows, list):
        add("AUTHORITY_SOURCES", "map", "authority_sources must be a list")
        authority_rows = []
    authority_ids: list[str] = []
    for row in authority_rows:
        if not isinstance(row, dict):
            add("AUTHORITY_ROW", "authority_sources", "row must be an object")
            continue
        authority_id = row.get("authority_id")
        if not isinstance(authority_id, str):
            add("AUTHORITY_ID", "authority_sources", "authority_id is required")
            continue
        authority_ids.append(authority_id)
        if not row.get("authority_role"):
            add("AUTHORITY_ROLE", authority_id, "authority_role is required")
        for system_id in row.get("system_ids", []):
            if system_id not in registered_systems:
                add("SYSTEM_REFERENCE", authority_id, f"unknown metadata system: {system_id}")
        paths = row.get("paths")
        if not isinstance(paths, list) or not paths:
            add("AUTHORITY_PATHS", authority_id, "paths must not be empty")
        else:
            for value in paths:
                if not isinstance(value, str) or not path_exists(repo_root, value):
                    add("AUTHORITY_PATH", authority_id, f"path not found: {value}")
    for authority_id, count in Counter(authority_ids).items():
        if count > 1:
            add("AUTHORITY_DUPLICATE", authority_id, "authority id is duplicated")

    rules = data.get("field_rules")
    if not isinstance(rules, list) or not rules:
        add("FIELD_RULES", "map", "field_rules must not be empty")
        rules = []
    field_groups: list[str] = []
    for row in rules:
        if not isinstance(row, dict):
            add("FIELD_RULE_ROW", "field_rules", "row must be an object")
            continue
        group = row.get("field_group")
        if not isinstance(group, str):
            add("FIELD_GROUP", "field_rules", "field_group is required")
            continue
        field_groups.append(group)
        for entity in row.get("applies_to", []):
            if entity not in set(entity_ids):
                add("FIELD_ENTITY", group, f"unknown entity: {entity}")
        order = row.get("authority_order")
        if not isinstance(order, list) or not order:
            add("FIELD_AUTHORITY", group, "authority_order must not be empty")
        else:
            for authority_id in order:
                if authority_id not in set(authority_ids):
                    add("FIELD_AUTHORITY", group, f"unknown authority: {authority_id}")
        if not row.get("conflict_disposition"):
            add("FIELD_CONFLICT", group, "conflict disposition is required")
    for group, count in Counter(field_groups).items():
        if count > 1:
            add("FIELD_GROUP_DUPLICATE", group, "field group is duplicated")

    evidence_rows = data.get("evidence_inputs")
    if not isinstance(evidence_rows, list) or not evidence_rows:
        add("EVIDENCE_INPUTS", "map", "evidence inputs are required")
    else:
        for row in evidence_rows:
            if not isinstance(row, dict):
                add("EVIDENCE_ROW", "evidence_inputs", "row must be an object")
                continue
            evidence_id = str(row.get("evidence_id", "unknown"))
            path_value = row.get("path")
            if not isinstance(path_value, str) or not (repo_root / path_value).is_file():
                add("EVIDENCE_PATH", evidence_id, f"missing: {path_value}")
            elif sha256_file(repo_root / path_value) != str(row.get("sha256", "")).upper():
                add("EVIDENCE_HASH", evidence_id, "SHA-256 mismatch")

    policy = data.get("conflict_policy")
    if not isinstance(policy, dict) or policy.get("merge_strategy") != "NO_LAST_WRITER_WINS":
        add("CONFLICT_POLICY", "map", "NO_LAST_WRITER_WINS is required")
    return findings


def validate_evidence(data: dict[str, Any], repo_root: Path) -> tuple[dict[str, int], list[dict[str, str]]]:
    paths = {row["evidence_id"]: repo_root / row["path"] for row in data.get("evidence_inputs", [])}
    findings: list[dict[str, str]] = []
    refs = read_csv(paths["joined_reference_inventory"])
    funcs = read_csv(paths["sysfunc_candidate"])
    args = read_csv(paths["sysargs_candidate"])

    def add(code: str, subject: str, detail: str) -> None:
        findings.append({"code": code, "subject": subject, "detail": detail})

    ref_ids = [row.get("identity", "") for row in refs]
    for identity, count in Counter(ref_ids).items():
        if count > 1:
            add("REFERENCE_DUPLICATE", identity, str(count))
        if identity != normalized(identity):
            add("REFERENCE_NORMALIZATION", identity, normalized(identity))

    for field in ("CAN_NAME", "FUNC_ID"):
        for value, count in Counter(row.get(field, "") for row in funcs).items():
            if count > 1:
                add("FUNCTION_DUPLICATE", value, field)
    for row in funcs:
        expected = "FN_" + sanitized(row.get("CAN_NAME", ""))
        if row.get("FUNC_ID") != expected:
            add("FUNCTION_ID_PROJECTION", row.get("FUNC_ID", ""), expected)

    logical_keys: list[str] = []
    legacy_shapes: dict[str, set[str]] = defaultdict(set)
    arg_ids: list[str] = []
    for row in args:
        shape = "|".join(normalized(row.get(field, "")) for field in ("OWNER_KND", "OWNER_NAM", "ARG_KIND", "ARG_NAME"))
        logical_keys.append(shape)
        arg_id = row.get("ARG_ID", "")
        arg_ids.append(arg_id)
        legacy_shapes[arg_id].add(shape)
    for key, count in Counter(logical_keys).items():
        if count > 1:
            add("ARGUMENT_KEY_DUPLICATE", key, str(count))
    for arg_id, count in Counter(arg_ids).items():
        if count > 1:
            add("ARGUMENT_ID_DUPLICATE", arg_id, str(count))
    for arg_id, shapes in legacy_shapes.items():
        if len(shapes) > 1:
            add("ARGUMENT_ID_COLLISION", arg_id, " || ".join(sorted(shapes)))

    metrics = {
        "reference_identities": len(refs),
        "function_candidates": len(funcs),
        "argument_candidates": len(args),
        "reference_duplicates": sum(1 for count in Counter(ref_ids).values() if count > 1),
        "function_name_duplicates": sum(1 for count in Counter(row.get("CAN_NAME", "") for row in funcs).values() if count > 1),
        "function_id_duplicates": sum(1 for count in Counter(row.get("FUNC_ID", "") for row in funcs).values() if count > 1),
        "argument_key_duplicates": sum(1 for count in Counter(logical_keys).values() if count > 1),
        "argument_id_duplicates": sum(1 for count in Counter(arg_ids).values() if count > 1),
        "argument_id_cross_shape_collisions": sum(1 for shapes in legacy_shapes.values() if len(shapes) > 1),
    }
    return metrics, findings


def audit(map_path: Path, repo_root: Path) -> dict[str, Any]:
    data = json.loads(map_path.read_text(encoding="utf-8"))
    findings = validate_map(data, repo_root)
    metrics: dict[str, int] = {}
    if not findings:
        metrics, evidence_findings = validate_evidence(data, repo_root)
        findings.extend(evidence_findings)
    return {"schema_version": SCHEMA, "status": "PASS" if not findings else "FAIL", "finding_count": len(findings), "metrics": metrics, "findings": findings}


def main() -> int:
    default_root = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=default_root)
    parser.add_argument("--map", type=Path)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    repo_root = args.repo_root.resolve()
    map_path = args.map or repo_root / "selfdoc" / "reference_identity_authority_v1.json"
    result = audit(map_path, repo_root)
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        metrics = " ".join(f"{key}={value}" for key, value in result["metrics"].items())
        print(f"reference_identity_authority status={result['status']} findings={result['finding_count']} {metrics}".rstrip())
        for finding in result["findings"]:
            print(f"- {finding['code']} {finding['subject']}: {finding['detail']}")
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
