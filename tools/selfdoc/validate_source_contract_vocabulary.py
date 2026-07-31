#!/usr/bin/env python3
"""Build or validate the vocabulary preserved from the historical v1.1 probe."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
from pathlib import Path
from typing import Any


SCHEMA = "source_contract_vocabulary_v1"
CONSTANTS = ("CORE_FIELDS", "RECOMMENDED_FIELDS", "BASE_EXTENSION_FIELDS", "BASE_ALIAS_MAP")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def extract_constants(path: Path) -> dict[str, Any]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    found: dict[str, Any] = {}
    for node in tree.body:
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        target = node.targets[0]
        if isinstance(target, ast.Name) and target.id in CONSTANTS:
            found[target.id] = ast.literal_eval(node.value)
    missing = sorted(set(CONSTANTS) - set(found))
    if missing:
        raise ValueError(f"missing probe constants: {', '.join(missing)}")
    return found


def build_registry(probe: Path, repo_root: Path) -> dict[str, Any]:
    values = extract_constants(probe)
    return {
        "schema_version": SCHEMA,
        "kind": "source_contract_vocabulary_registry",
        "status": "ACTIVE_MIGRATED_VOCABULARY",
        "authority_class": "DESCRIPTIVE_CLASSIFIER_VOCABULARY",
        "contract": "docs/maintenance/lanes/full_stack_documentation/SOURCE_CONTRACT_VOCABULARY_CONTRACT_V1.md",
        "source_probe": {
            "path": probe.relative_to(repo_root).as_posix(),
            "sha256": sha256_file(probe),
            "lifecycle": "HISTORICAL",
            "execution_default_allowed": False,
        },
        "migration_run": "DOCFLUSH-20260716-001",
        "disposition": "VOCABULARY_PRESERVED_PROBE_RETIRED_FROM_DEFAULT_EXECUTION",
        "core_fields": sorted(values["CORE_FIELDS"]),
        "recommended_fields": sorted(values["RECOMMENDED_FIELDS"]),
        "extension_fields": sorted(values["BASE_EXTENSION_FIELDS"]),
        "alias_map": dict(sorted(values["BASE_ALIAS_MAP"].items())),
        "mutation_authorized": False,
        "promotion_authorized": False,
    }


def validate_registry(data: dict[str, Any], repo_root: Path) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []

    def add(code: str, subject: str, detail: str) -> None:
        findings.append({"code": code, "subject": subject, "detail": detail})

    if data.get("schema_version") != SCHEMA:
        add("SCHEMA_VERSION", "registry", f"expected {SCHEMA}")
    if data.get("kind") != "source_contract_vocabulary_registry":
        add("REGISTRY_KIND", "registry", "unexpected kind")
    for gate in ("mutation_authorized", "promotion_authorized"):
        if data.get(gate) is not False:
            add("SAFETY_GATE", gate, "must be false")

    source = data.get("source_probe")
    if not isinstance(source, dict) or not source.get("path"):
        add("SOURCE_PROBE", "registry", "source_probe path is required")
        return findings
    probe = repo_root / str(source["path"])
    if not probe.is_file():
        add("SOURCE_MISSING", str(source["path"]), "probe does not exist")
        return findings
    if source.get("sha256") != sha256_file(probe):
        add("SOURCE_HASH", str(source["path"]), "SHA-256 does not match")
    if source.get("lifecycle") != "HISTORICAL" or source.get("execution_default_allowed") is not False:
        add("SOURCE_LIFECYCLE", str(source["path"]), "probe must remain historical and non-default")

    values = extract_constants(probe)
    expected = {
        "core_fields": sorted(values["CORE_FIELDS"]),
        "recommended_fields": sorted(values["RECOMMENDED_FIELDS"]),
        "extension_fields": sorted(values["BASE_EXTENSION_FIELDS"]),
        "alias_map": dict(sorted(values["BASE_ALIAS_MAP"].items())),
    }
    for key, value in expected.items():
        if data.get(key) != value:
            add("VOCABULARY_DRIFT", key, "registry no longer exactly preserves probe constant")

    known = set(data.get("core_fields", [])) | set(data.get("extension_fields", []))
    aliases = data.get("alias_map", {})
    if isinstance(aliases, dict):
        for alias, target in aliases.items():
            if target not in known:
                add("ALIAS_TARGET", str(alias), f"unknown canonical field: {target}")
    else:
        add("ALIAS_MAP", "registry", "alias_map must be an object")
    return findings


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--registry", type=Path, default=Path("selfdoc/source_contract_vocabulary_v1.json"))
    parser.add_argument("--write", action="store_true", help="write the deterministic migrated registry")
    args = parser.parse_args()
    root = args.repo_root.resolve()
    registry = args.registry if args.registry.is_absolute() else root / args.registry
    probe = root / "selfdoc/probes/source_contract_inventory_probe_v1_1.py"
    if args.write:
        registry.parent.mkdir(parents=True, exist_ok=True)
        registry.write_text(json.dumps(build_registry(probe, root), indent=2) + "\n", encoding="utf-8")
    data = json.loads(registry.read_text(encoding="utf-8"))
    findings = validate_registry(data, root)
    print(json.dumps({"status": "PASS" if not findings else "FAIL", "findings": findings}, indent=2))
    return 0 if not findings else 1


if __name__ == "__main__":
    raise SystemExit(main())
